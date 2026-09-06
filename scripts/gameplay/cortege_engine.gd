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

var _anchors: Array[CortegeAnchor] = []
var _lost: int = 0
var _state: State = State.ACTIVE
var _detach_clock: float = -1.0
var _body: Node3D = null
var _rest: Vector3 = Vector3.ZERO
var _vfx: VFXManager = null

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

	# Les ancrages ceinturent le berceau, au niveau où le joueur les voit : jamais dessous.
	var total := tuning.anchors_of(is_central)
	var largeur := tuning.cradle_size.x * k
	for i in total:
		var anchor := CortegeAnchor.make(tuning.anchor_health, tuning.anchor_radius,
			tuning.anchor_score)
		anchor.name = "Anchor_%02d" % (i + 1)
		anchor.serial = i
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
		anchor.tick(w, GameplayPlane.aim_point_of(w, eye))
	if _detach_clock < 0.0:
		return
	_detach_clock += delta
	if _body != null:
		_body.position = _rest + drift_offset(_detach_clock, tuning.detach_leave_at,
			tuning.drift_speed, side if not is_central else 0.0)
		_body.rotation.z = tilt_at(_detach_clock, tuning.detach_tilt_at,
			tuning.detach_leave_at, tuning.detach_tilt_degrees) * (side if side != 0.0 else 1.0)
	if _state == State.DETACHING and _detach_clock >= tuning.detach_gone_at:
		_state = State.DETACHED
		detached.emit(self)

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
