class_name CortegeEngine
extends Node3D
## Un des trois groupes propulsifs de la poupe, et sa machine à états.
##
## ⚠️ SON ÉTAT NE SE DÉCIDE PAS, IL SE DÉDUIT — du nombre d'ancrages tombés, et de rien d'autre.
## `state_for()` est une fonction pure : c'est ce qui rend la séquence vérifiable sans monter la
## scène, sans jouer quatre minutes de survol, et sans rendu. Toute la spec §8 tient dedans.
##
## ⚠️ ET LE MOTEUR NE PREND AUCUN DÉGÂT. Pas « peu » : aucun. Il n'a pas de `BulletTarget`, donc
## il n'existe pas pour le gestionnaire de balles — la règle n'est pas gardée par une condition
## qu'on pourrait oublier, elle est gardée par une absence. C'est le critère d'acceptation n°3
## de la spec, et c'est ce qui distingue cette phase d'un boss.
##
## ⚠️ ET SON DÉPART EST UNE TRAJECTOIRE ÉCRITE, JAMAIS UNE SIMULATION (spec §11). Un moteur qui
## part « physiquement » est un moteur qui peut, un jour sur cent, percuter le joueur ou rester
## coincé dans la coque. Ici la position est une fonction du temps écoulé : elle sort toujours
## du bon côté, et elle est testable au point près.

enum State { ACTIVE, DAMAGED_1, DAMAGED_2, DETACHING, DETACHED }

## Le cycle de poussée (spec §6). `VENT` n'appartient qu'au central, et seulement après la perte
## des deux latéraux (spec §15).
enum Surge { CALM, CHARGE, BLAST, VENT }

## La lueur de tuyère d'un moteur qui pousse, et celle d'une conduite alimentée.
const THRUST_GLOW := 2.20
const CONDUIT_GLOW := 1.10
## Ce qu'il reste d'une conduite rompue : une gaine noire. Elle ne disparaît PAS — c'est elle qui
## dit, sur un berceau vide, que quelque chose a été arraché là.
const CONDUIT_DEAD := 0.03

## Il vient de perdre un ancrage : le niveau le raconte, la flamme s'abîme.
signal weakened(engine: CortegeEngine, lost: int)
## Le dernier ancrage a cédé : la séquence d'arrachement commence.
signal detaching(engine: CortegeEngine)
## Il a quitté son berceau et n'appartient plus au jeu.
signal detached(engine: CortegeEngine)

## −1 bâbord, 0 central, +1 tribord. C'est aussi le sens de la dérive (spec §10).
var side: float = 0.0
var is_central: bool = false
var tuning: CortegeSternTuning = null
## Voir `--no-flames`.
var show_flame: bool = true

var _anchors: Array[CortegeAnchor] = []
var _lost: int = 0
var _state: State = State.ACTIVE
var _detach_clock: float = -1.0
var _body: Node3D = null
var _rest: Vector3 = Vector3.ZERO
var _vfx: VFXManager = null
var _nozzle: MeshInstance3D = null
var _thrust_mat: StandardMaterial3D = null
var _conduits: Array[MeshInstance3D] = []
var _conduit_veins: Array[StandardMaterial3D] = []
var _burst_done: bool = false
var _flame: CortegeFlame = null
var _surge_clock: float = 0.0
var _surge: Surge = Surge.CALM
## Le central ouvre son extinction quand les deux latéraux sont partis, jamais avant.
var _has_vent: bool = false

static func make(p_tuning: CortegeSternTuning, p_side: float) -> CortegeEngine:
	var engine := CortegeEngine.new()
	engine.tuning = p_tuning
	engine.side = p_side
	engine.is_central = is_zero_approx(p_side)
	return engine

# --- La règle, pure et testable sans arbre -------------------------------------

## L'état d'un moteur, déduit de ses seules attaches.
##
## ⚠️ ELLE PREND `total` ET NON TROIS, parce que le central en porte quatre. Écrire la règle en
## dur pour trois aurait donné un moteur central qui passe `DAMAGED_2` au deuxième ancrage puis
## reste là jusqu'au quatrième — une progression muette au milieu, et rien pour le dire.
static func state_for(lost: int, total: int, leaving: bool) -> State:
	if leaving:
		return State.DETACHING
	if total <= 0 or lost >= total:
		return State.DETACHED
	if lost <= 0:
		return State.ACTIVE
	# Les états intermédiaires se répartissent sur ce qui reste : le premier ancrage perdu ouvre
	# `DAMAGED_1`, et la seconde moitié du chemin ouvre `DAMAGED_2`.
	return State.DAMAGED_1 if lost * 2 < total else State.DAMAGED_2

## Où se trouve un moteur qui s'en va, en écart depuis son berceau, à `t` secondes du dernier
## ancrage abattu.
##
## ⚠️ RIEN NE BOUGE AVANT `detach_leave_at`, ET C'EST LA MOITIÉ DE LA LECTURE. Entre le dernier
## verrou et le départ, le moteur TREMBLE et ses conduites éclatent — s'il glissait déjà, le
## joueur lirait « il tombe » au lieu de « il s'arrache ».
static func drift_offset(t: float, leave_at: float, speed: float, side: float) -> Vector3:
	if t <= leave_at:
		return Vector3.ZERO
	var age := t - leave_at
	# Vers le HAUT de l'écran d'abord, et de côté ensuite : les trois partent par où sortent
	# leurs flammes, ce qui est la seule direction que le joueur peut anticiper.
	var up := speed * age
	var out := speed * 0.45 * age * side
	return Vector3(out, 0.0, -up)

## De combien le moteur tremble, à `t` secondes. ⚠️ DÉTERMINISTE, ET C'EST CE QUI LE REND
## TESTABLE. Un tremblement tiré au hasard donnerait une capture différente à chaque lancement —
## or un arrachement se juge en comparant deux passages. Deux sinusoïdes incommensurables
## suffisent à ne pas se lire comme un balancier.
static func shake_at(t: float, from_s: float, to_s: float, amplitude: float,
		hz: float) -> Vector3:
	if t <= from_s or t >= to_s:
		return Vector3.ZERO
	# ⚠️ IL MONTE, IL N'EST PAS CONSTANT. Une vibration d'intensité fixe se lit comme un moteur
	# qui ronronne ; ce qu'il faut lire, c'est une pièce dont la tenue se dégrade seconde après
	# seconde jusqu'à lâcher.
	var montee := clampf((t - from_s) / maxf(to_s - from_s, 0.001), 0.0, 1.0)
	var a := amplitude * montee
	return Vector3(a * sin(t * hz * TAU), a * 0.6 * sin(t * hz * TAU * 1.37), 0.0)

## Ce qu'il reste de la propulsion d'un moteur arraché, de 1 à 0.
##
## ⚠️ ELLE NE S'ÉTEINT PAS AU DÉPART, ELLE S'ÉTEINT EN DÉRIVANT (spec §9 : « il dérive tout en
## continuant à cracher une poussée instable », §16 : « la propulsion s'éteint progressivement »).
## Couper au moment du départ ferait lire une panne ; ce qu'il faut lire, c'est une machine qui
## fonctionne encore et que plus rien ne retient.
static func thrust_at(t: float, leave_at: float, gone_at: float) -> float:
	if t <= leave_at:
		return 1.0
	var span := maxf(gone_at - leave_at, 0.001)
	return clampf(1.0 - (t - leave_at) / span, 0.0, 1.0)

## Où en est le cycle de poussée à `t` secondes (spec §6 et §15).
##
## ⚠️ L'ORDRE EST CALME → CHARGE → SOUFFLE, ET LA CHARGE EST DEVANT. Un préavis qui suivrait le
## souffle ne préviendrait rien ; c'est évident écrit ainsi, et c'est pourtant l'inversion la
## plus facile à commettre en calculant des restes de modulo.
##
## ⚠️ ET L'EXTINCTION N'APPARTIENT QU'AU CENTRAL, une fois les deux latéraux partis (spec §15).
## Elle donne au joueur « une fenêtre très confortable pour attaquer » — c'est ce qui empêche la
## dernière étape de la phase de devenir une attente.
static func surge_at(t: float, period: float, warning: float, blast: float,
		vent: float, has_vent: bool) -> Surge:
	var cycle := period + (vent if has_vent else 0.0)
	if cycle <= 0.0:
		return Surge.CALM
	var u := fposmod(t, cycle)
	if u < period - warning - blast:
		return Surge.CALM
	if u < period - blast:
		return Surge.CHARGE
	if u < period:
		return Surge.BLAST
	return Surge.VENT

## De combien la flamme enfle selon la phase.
static func surge_gain(phase: Surge, charge: float, blast: float) -> float:
	match phase:
		Surge.CHARGE: return charge
		Surge.BLAST: return blast
		Surge.VENT: return 0.0
	return 1.0

## L'angle de bascule, en radians, à `t` secondes.
static func tilt_at(t: float, tilt_at_s: float, leave_at: float, degrees: float) -> float:
	if t <= tilt_at_s:
		return 0.0
	# Il bascule pendant la fenêtre qui sépare la bascule du départ, puis garde son angle.
	var span := maxf(leave_at - tilt_at_s, 0.001)
	return deg_to_rad(degrees) * clampf((t - tilt_at_s) / span, 0.0, 1.0)

# --- La pièce ------------------------------------------------------------------

func setup(bullets: BulletManager, vfx: VFXManager) -> void:
	_vfx = vfx
	for anchor in _anchors:
		anchor.setup(bullets, vfx)

## Monte les boîtes grises du LOT 1 : un berceau, un corps moteur, et ses ancrages.
##
## ⚠️ LE BERCEAU N'EST PAS ENFANT DU MOTEUR, et c'est toute la mise en scène de la phase. Ce qui
## reste quand le moteur part est la PREUVE qu'on est passé par là (spec §21, critère 7) : un
## berceau emporté avec son moteur ferait disparaître la récompense en même temps qu'elle
## arrive.
func build_greybox() -> void:
	var k := tuning.scale_of(is_central)
	var cradle := _box("Cradle", tuning.cradle_size * k, Color(0.11, 0.11, 0.14))
	cradle.position.y = tuning.cradle_size.y * k * 0.5
	add_child(cradle)

	_body = Node3D.new()
	_body.name = "Body"
	_rest = Vector3(0.0, tuning.cradle_size.y * k + tuning.engine_size.y * k * 0.5, 0.0)
	_body.position = _rest
	add_child(_body)
	_body.add_child(_box("Engine", tuning.engine_size * k, Color(0.14, 0.14, 0.18)))

	# ⚠️ LA TUYÈRE EST DANS LE CORPS, PAS DANS LE BERCEAU. C'est elle qui s'éteint en dérivant,
	# et c'est le seul signal qui dise « cette masse est encore une machine ». Le LOT 4 la
	# remplacera par une vraie flamme ; ce disque n'est là que pour que l'extinction existe.
	_nozzle = _box("Nozzle", Vector3(tuning.engine_size.x * k * 0.62, 0.30,
		tuning.engine_size.z * k * 0.10), Color(0.16, 0.05, 0.12))
	_nozzle.position.z = -tuning.engine_size.z * k * 0.46
	_thrust_mat = StandardMaterial3D.new()
	_thrust_mat.albedo_color = Color(0.20, 0.04, 0.14)
	_thrust_mat.emission_enabled = true
	_thrust_mat.emission = CortegeAnchor.TINT
	_thrust_mat.emission_energy_multiplier = THRUST_GLOW
	_nozzle.material_override = _thrust_mat
	_body.add_child(_nozzle)

	# ⚠️ LA FLAMME EST FILLE DU CORPS, PAS DU BERCEAU. Elle part avec lui : un moteur arraché
	# qui laisserait son panache accroché au vaisseau serait la pire image de la séquence.
	# Le déphasage vient de la place du moteur — sans lui, les trois respirent à l'unisson et
	# la poupe se met à battre comme un seul objet.
	if show_flame:
		_mount_flame()
	# ⚠️ DÉPHASAGE DU CYCLE AUSSI, et pour une raison de jeu cette fois : trois souffles
	# simultanés fermeraient toute la poupe d'un coup, sans couloir nulle part. Décalés, il y a
	# toujours au moins un moteur qu'on peut travailler.
	_surge_clock = (side + 1.0) * tuning.surge_period / 3.0

	# ⚠️ LES CONDUITES RENDENT L'ARRACHEMENT LISIBLE AVANT QUE RIEN NE BOUGE. Entre le dernier
	# verrou et le départ il s'écoule 1,2 s : sans une rupture visible à 0,5 s, cette seconde est
	# un temps mort où le joueur croit que rien ne s'est passé.
	var haut := tuning.cradle_size.y * k
	for i in tuning.conduit_count:
		var u := (float(i) + 0.5) / float(tuning.conduit_count)
		var conduit := _box("Conduit_%02d" % (i + 1),
			Vector3(tuning.conduit_width * k, tuning.engine_size.y * k * 0.34,
				tuning.conduit_width * k), Color(0.09, 0.09, 0.11))
		var vein := StandardMaterial3D.new()
		vein.albedo_color = Color(0.18, 0.04, 0.13)
		vein.metallic = 0.3
		vein.roughness = 0.5
		vein.emission_enabled = true
		vein.emission = CortegeAnchor.TINT
		vein.emission_energy_multiplier = CONDUIT_GLOW
		conduit.material_override = vein
		conduit.position = Vector3(
			lerpf(-tuning.cradle_size.x * k * 0.30, tuning.cradle_size.x * k * 0.30, u),
			haut + tuning.engine_size.y * k * 0.17,
			tuning.anchor_offset_z - 1.4)
		add_child(conduit)
		_conduits.append(conduit)
		_conduit_veins.append(vein)

	# Les ancrages ceinturent le berceau, au niveau où le joueur les voit : jamais dessous.
	var total := tuning.anchors_of(is_central)
	var largeur := tuning.cradle_size.x * k
	for i in total:
		var anchor := CortegeAnchor.make(tuning.anchor_health, tuning.anchor_radius,
			tuning.anchor_score)
		anchor.name = "Anchor_%02d" % (i + 1)
		anchor.serial = i
		anchor.damaged_at = tuning.anchor_damaged_at
		anchor.spark_interval = tuning.anchor_spark_interval
		anchor.build_greybox(tuning.anchor_size * k)
		# ⚠️ SUR LE BERCEAU, PAS DEDANS, ET DU CÔTÉ DU JOUEUR. La première pose les enfonçait à
		# 72 % de la hauteur du berceau et au tiers ARRIÈRE de sa profondeur : ils étaient
		# invisibles, et surtout à `y` de plan 9,6 quand le joueur ne monte qu'à 8. Ils se
		# voyaient à peine et ne pouvaient pas être touchés — sur la seule cible de la phase.
		anchor.position = _anchor_seat(i, total, largeur, k)
		anchor.destroyed.connect(_on_anchor_destroyed)
		add_child(anchor)
		_anchors.append(anchor)

## Où siège le `i`-ème ancrage, sur DEUX rangées.
##
## ⚠️ LA SPEC LES DESSINE EN TRIANGLE — deux en haut, un en bas — et ce n'est pas décoratif.
## Alignés, les quatre verrous du central se touchent et se lisent comme une seule barre : le
## joueur ne voit plus « des attaches », il voit une pièce. Vu en capture le 2026-09-06.
func _anchor_seat(i: int, total: int, largeur: float, k: float) -> Vector3:
	var hauts := 2
	var bas := total - hauts
	var y := tuning.cradle_size.y * k + tuning.anchor_size.y * k * 0.5
	if i < hauts:
		var t := 0.0 if i == 0 else 1.0
		return Vector3(lerpf(-largeur * 0.34, largeur * 0.34, t), y, tuning.anchor_offset_z)
	var j := i - hauts
	var x := 0.0
	if bas > 1:
		x = lerpf(-largeur * 0.18, largeur * 0.18, float(j) / float(bas - 1))
	return Vector3(x, y, tuning.anchor_offset_z + tuning.anchor_row_gap)

func _mount_flame() -> void:
	_flame = CortegeFlame.make(tuning.flame_length, tuning.flame_width, side * 1.7 + 0.4)
	_flame.name = "Flame"
	_flame.position = _nozzle.position + Vector3(0.0, 0.0, -0.15)
	_flame.build()
	_body.add_child(_flame)

func _box(nom: String, size: Vector3, teinte: Color) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	mesh.name = nom
	var box := BoxMesh.new()
	box.size = size
	mesh.mesh = box
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var mat := StandardMaterial3D.new()
	mat.albedo_color = teinte
	mat.metallic = 0.45
	mat.roughness = 0.55
	mesh.material_override = mat
	return mesh

func anchors() -> Array[CortegeAnchor]:
	return _anchors

func state() -> State:
	return _state

func lost_anchors() -> int:
	return _lost

func is_gone() -> bool:
	return _state == State.DETACHED

## Ouvre ou ferme TOUS ses verrous d'un coup — c'est ainsi que le central reste protégé.
func set_locked(locked: bool) -> void:
	for anchor in _anchors:
		if anchor.is_alive():
			anchor.set_vulnerable(not locked)

func tick(delta: float, world_origin: Vector3, eye: Vector3) -> void:
	for anchor in _anchors:
		var w := anchor.global_position if anchor.is_inside_tree() \
			else world_origin + anchor.position
		anchor.tick(delta, w, GameplayPlane.aim_point_of(w, eye))
	_advance_thrust(delta)
	if _detach_clock < 0.0:
		return
	_detach_clock += delta
	_advance_detach(_detach_clock)
	if _state == State.DETACHING and _detach_clock >= tuning.detach_gone_at:
		_state = State.DETACHED
		detached.emit(self)

## La séquence de la spec §9, dans l'ordre : tremblement, rupture des conduites, bascule, départ,
## dérive. ⚠️ ELLE SE LIT DANS LE TEMPS ÉCOULÉ, JAMAIS DANS UN ÉTAT ACCUMULÉ — sauf la rupture,
## qui est un événement et porte donc son drapeau. Tout le reste est une fonction de `t` : la
## pièce peut être avancée d'un bond dans un banc, et elle sera exactement où elle doit être.
func _advance_detach(t: float) -> void:
	if _body == null:
		return
	var vers := side if not is_central else 0.0
	_body.position = _rest \
		+ drift_offset(t, tuning.detach_leave_at, tuning.drift_speed, vers) \
		+ shake_at(t, tuning.detach_shake_at, tuning.detach_leave_at,
			tuning.detach_shake_amplitude, tuning.detach_shake_hz)
	_body.rotation.z = tilt_at(t, tuning.detach_tilt_at, tuning.detach_leave_at,
		tuning.detach_tilt_degrees) * (side if side != 0.0 else 1.0)
	# ⚠️ LA ROTATION PROPRE N'APPARTIENT QU'AU CENTRAL (spec §10). Les deux latéraux se
	# distinguent par leur direction ; le central part droit, et sans elle son départ serait le
	# seul à ne rien raconter — alors que c'est celui qui clôt la séquence.
	if is_central and t > tuning.detach_leave_at:
		_body.rotation.y = deg_to_rad(tuning.central_spin_deg) * (t - tuning.detach_leave_at)
	# La rupture : un événement, une fois.
	if not _burst_done and t >= tuning.detach_burst_at:
		_burst_done = true
		_break_conduits()
	if _thrust_mat != null:
		_thrust_mat.emission_energy_multiplier = THRUST_GLOW \
			* thrust_at(t, tuning.detach_leave_at, tuning.detach_gone_at)

## Les conduites éclatent : elles s'éteignent, et une gerbe part de chacune.
##
## ⚠️ ELLES NE DISPARAISSENT PAS. Une gaine noire sur un berceau vide est ce qui dit, dix
## secondes plus tard, que quelque chose a été arraché là — c'est la même règle que la carcasse
## d'un verrou rompu et que le cœur retiré d'un nœud d'épine.
func _break_conduits() -> void:
	for vein in _conduit_veins:
		vein.emission_energy_multiplier = CONDUIT_DEAD
		vein.albedo_color = Color(0.05, 0.05, 0.06)
	if _vfx == null:
		return
	for conduit in _conduits:
		var w := conduit.global_position if conduit.is_inside_tree() else global_position
		_vfx.spawn_explosion(w, VfxExplosion.Category.SMALL, CortegeAnchor.TINT)

## Le cycle de poussée et la flamme qui le rend. ⚠️ IL S'ARRÊTE DÈS L'ARRACHEMENT : un moteur
## qui s'en va ne « souffle » plus au sens du jeu — sa flamme devient instable et s'éteint, mais
## elle ne blesse plus personne. Une colonne dangereuse accrochée à une pièce qui dérive
## frapperait le joueur depuis un endroit qu'il ne peut plus prévoir.
func _advance_thrust(delta: float) -> void:
	if _flame == null:
		return
	var leaving := _state == State.DETACHING or _state == State.DETACHED
	if not leaving:
		_surge_clock += delta
		_surge = surge_at(_surge_clock, tuning.surge_period, tuning.surge_warning,
			tuning.surge_blast, tuning.surge_vent, _has_vent)
	else:
		_surge = Surge.CALM
	var puissance := 1.0
	if _detach_clock >= 0.0:
		puissance = thrust_at(_detach_clock, tuning.detach_leave_at, tuning.detach_gone_at)
	_flame.tick(_surge_clock, CortegeFlame.regime_for(_state, leaving), puissance,
		surge_gain(_surge, tuning.surge_charge_gain, tuning.surge_blast_gain))

func surge() -> Surge:
	return _surge

## Le souffle blesse-t-il en ce moment ?
func is_blasting() -> bool:
	return _surge == Surge.BLAST

## Ouvre l'extinction du central (spec §15). Sans appel, il n'en a pas.
func open_vent() -> void:
	_has_vent = true

func _on_anchor_destroyed(anchor: CortegeAnchor) -> void:
	_lost += 1
	var total := tuning.anchors_of(is_central)
	print("[Poupe] ancrage %d/%d du moteur %s abattu" % [_lost, total, _slot_name()])
	if _lost < total:
		_state = state_for(_lost, total, false)
		weakened.emit(self, _lost)
		return
	_state = State.DETACHING
	_detach_clock = 0.0
	set_locked(true)
	print("[Poupe] moteur %s : dernier ancrage rompu — arrachement" % _slot_name())
	detaching.emit(self)

func _slot_name() -> String:
	if is_central:
		return "central"
	return "tribord" if side > 0.0 else "bâbord"
