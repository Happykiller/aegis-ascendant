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

## Les arcs d'un berceau vide (spec §16 et §17).
const ARC_COUNT := 4
const ARC_SEGMENTS := 3
const ARC_REACH := 1.9
const ARC_HZ := 9.0

## Ce que la boîte grise garde de la boîte englobante du moteur livré : le fût, pas les carénages.
const BODY_FIT := Vector3(0.78, 0.92, 0.86)

## Les binaires réduits (`BRIEF-0105`). ⚠️ 60 020 TRIANGLES POUR LA POUPE ENTIÈRE, contre les
## 3,17 millions livrés : la géométrie et les cent repères sont ceux de l'auteur, seul le poids
## a changé. Les matériaux portent déjà les noms du kit — c'était un critère du brief, parce que
## `CortegeSkin` reconnaît son émissif PAR SON NOM et que sans lui rien ne peut s'éteindre.
const CRADLE_KIT := "res://assets/imported/models/backgrounds/stern_cradle.glb"
const ENGINE_KIT := "res://assets/imported/models/backgrounds/stern_engine.glb"
## Le préfixe des repères de l'auteur. Le jeu les adresse par leur nom, jamais par leur rang.
const SOCKET_PREFIX := "CTRL | Socket ancrage"
## ⚠️ L'AUTEUR AVAIT LIVRÉ LE REPÈRE, ET LE CODE NE LE LISAIT PAS. `CTRL | Socket VFX flamme` est
## dans le binaire depuis le premier jour (z = −5,980, la bouche de la tuyère) ; `_mount_thrust`
## calculait à la place `−engine_size.z × k × 0,5` à partir de la boîte englobante. Les deux
## tombaient à un centimètre l'un de l'autre, ce qui a fait passer l'approximation — mais elle
## était fausse par principe, et elle plaçait le panache À LA LÈVRE au lieu de le mettre DEDANS.
## Même défaut que les tourelles de coque, même parade : la cote se lit sur l'asset.
const FLAME_SOCKET := "CTRL | Socket VFX flamme"

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
var _nacelle: Node3D = null
## La charge de la poupe, posée par elle avant `build()`. ⚠️ ELLE NE SE LIT NI DANS UN AUTOLOAD NI
## DANS LA POUPE : le moteur est pilotable sans scène, et c'est ce qui le rend testable.
var charge: float = 1.0
var _surge_clock: float = 0.0
var _surge: Surge = Surge.CALM
## Le central ouvre son extinction quand les deux latéraux sont partis, jamais avant.
var _has_vent: bool = false
var _arc_mesh: ImmediateMesh = null
var _arc_timer: float = 0.0
var _arc_rng := RandomNumberGenerator.new()
var _cradle_anim: AnimationPlayer = null
var _engine_anim: AnimationPlayer = null
## Les matériaux émissifs propres à CE groupe : ceux du berceau, ceux de la nacelle.
var _hull_glow: Array[StandardMaterial3D] = []
var _thrust_glow: Array[StandardMaterial3D] = []
var _clip_engine: String = ""
var _clip_cradle: String = ""

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
## ⚠️ SON PREMIER GAIN S'APPELAIT `charge`, ET LA CLASSE PORTE MAINTENANT UN MEMBRE DU MEME NOM.
## Les deux n'ont rien à voir : ici c'est la MONTÉE d'une surintensité, là-bas ce que l'artère a
## laissé au vaisseau. Le paramètre gagnait, le membre était invisible — et un lecteur pressé
## aurait branché l'un sur l'autre en croyant corriger un oubli.
static func surge_gain(phase: Surge, rise: float, blast: float) -> float:
	match phase:
		Surge.CHARGE: return rise
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
## Monte le groupe : les pièces réduites si elles sont là, les boîtes grises sinon.
##
## ⚠️ LA DOUBLURE RESTE, ET CE N'EST PAS DE LA PRUDENCE DE FAÇADE. Les tests montent la poupe
## sans arbre et sans import ; un banc qui exigerait les `.glb` ne pourrait plus vérifier une
## seule règle de la phase. Même contrat que `CortegeFlyby.is_stand_in()`.
func build() -> void:
	var cradle := _load_kit(CRADLE_KIT)
	if cradle == null:
		build_greybox()
		return
	var k := tuning.scale_of(is_central)
	cradle.name = "Cradle"
	cradle.scale = Vector3.ONE * k
	add_child(cradle)
	_claim_emissive(cradle, _hull_glow)
	_cradle_anim = _player_of(cradle)

	_body = Node3D.new()
	_body.name = "Body"
	# Le contrat de mariage de l'auteur, converti en Y-up. ⚠️ LE MOTEUR S'ENCASTRE, il ne
	# s'empile pas : c'est la correction du LOT 5, et elle vaut un mètre de hauteur.
	_rest = tuning.engine_seat * k
	_body.position = _rest
	add_child(_body)
	var engine := _load_kit(ENGINE_KIT)
	_nacelle = engine
	if engine != null:
		engine.name = "Nacelle"
		engine.scale = Vector3.ONE * k
		_body.add_child(engine)
		_claim_emissive(engine, _thrust_glow)
		_engine_anim = _player_of(engine)

	# ⚠️ LES SIÈGES SE LISENT DANS LE BINAIRE, PAS DANS UNE TABLE. Quatre repères
	# `CTRL | Socket ancrage AV/AR D/G` portent les places exactes ; les recopier ici, c'est
	# rouvrir l'écart entre la table et le marqueur que le dépôt a déjà payé sur les tourelles
	# de coque — jusqu'à 2,30 m.
	var sieges := _sockets_of(cradle)
	var total := tuning.anchors_of(is_central)
	for i in mini(total, sieges.size()):
		var anchor := _make_anchor(i)
		anchor.position = sieges[i]
		# ⚠️ LA RANGÉE ARRIÈRE FAIT DEMI-TOUR. La mâchoire de l'ancrage regarde son +Z local
		# (`CTRL | Contact moteur` y siège) : il doit donc présenter cette face au MOTEUR, qui
		# est en amont pour la rangée avant et en aval pour l'arrière. Sans ce yaw, la moitié
		# des verrous mordent le vide.
		if sieges[i].z > 0.0:
			anchor.rotation.y = PI
		# ⚠️ ENFANT DU BERCEAU, DONC À SON ÉCHELLE. Le poser en frère obligerait à multiplier
		# chaque cote par `k` à la main, et c'est exactement le genre de multiplication qu'on
		# oublie une fois sur deux.
		cradle.add_child(anchor)
		_anchors.append(anchor)
	if _anchors.size() < total:
		push_error("[Poupe] %s : %d sièges d'ancrage pour %d verrous attendus"
			% [name, sieges.size(), total])
	_mount_thrust(k)
	_play_clips()

## Les places d'ancrage, lues sur les repères de l'auteur et triées : d'abord la paire AVANT
## (haute à l'écran), puis l'ARRIÈRE. ⚠️ L'ORDRE COMPTE : un moteur latéral n'en prend que trois,
## et ce sont les deux hautes plus une basse — le triangle de la spec §7.
## La bouche de la tuyère, telle que l'auteur l'a posée. Vecteur nul si le repère manque.
static func _flame_socket_of(root: Node) -> Vector3:
	if root == null:
		return Vector3.ZERO
	for node in _descendants(root):
		var n3 := node as Node3D
		if n3 != null and String(node.name) == FLAME_SOCKET:
			return n3.position
	return Vector3.ZERO

static func _sockets_of(root: Node) -> Array[Vector3]:
	var avant: Array[Vector3] = []
	var arriere: Array[Vector3] = []
	for node in _descendants(root):
		var n3 := node as Node3D
		if n3 == null or not String(node.name).begins_with(SOCKET_PREFIX):
			continue
		if n3.position.z < 0.0:
			avant.append(n3.position)
		else:
			arriere.append(n3.position)
	avant.sort_custom(func(a: Vector3, b: Vector3) -> bool: return a.x < b.x)
	arriere.sort_custom(func(a: Vector3, b: Vector3) -> bool: return a.x < b.x)
	var out: Array[Vector3] = []
	out.append_array(avant)
	out.append_array(arriere)
	return out

static func _descendants(node: Node, out: Array[Node] = []) -> Array[Node]:
	for child in node.get_children():
		out.append(child)
		_descendants(child, out)
	return out

func _load_kit(path: String) -> Node3D:
	var packed: PackedScene = load(path) as PackedScene
	if packed == null:
		return null
	return packed.instantiate() as Node3D

static func _player_of(root: Node) -> AnimationPlayer:
	for node in _descendants(root):
		var player := node as AnimationPlayer
		if player != null:
			return player
	return null

## Donne à CE groupe sa propre copie des matériaux émissifs.
##
## ⚠️ SANS CETTE COPIE, ÉTEINDRE UN MOTEUR LES ÉTEINDRAIT TOUS LES TROIS. Les trois nacelles
## sont trois instances du MÊME `.glb` : elles partagent leurs matériaux. C'est le piège déjà
## payé sur les deux relais de la Citadelle, sur les puits, et sur les cinq bulbes d'épine.
static func _claim_emissive(root: Node, out: Array[StandardMaterial3D]) -> void:
	for node in _descendants(root):
		var mesh := node as MeshInstance3D
		if mesh == null:
			continue
		for i in mesh.get_surface_override_material_count():
			var base := mesh.get_active_material(i) as StandardMaterial3D
			if base == null or not base.emission_enabled:
				continue
			var mine: StandardMaterial3D = base.duplicate()
			mesh.set_surface_override_material(i, mine)
			out.append(mine)

func _make_anchor(i: int) -> CortegeAnchor:
	var anchor := CortegeAnchor.make(tuning.anchor_health * charge, tuning.anchor_radius,
		tuning.anchor_score)
	anchor.name = "Anchor_%02d" % (i + 1)
	anchor.serial = i
	anchor.damaged_at = tuning.anchor_damaged_at
	anchor.spark_interval = tuning.anchor_spark_interval
	anchor.build(tuning.anchor_size)
	anchor.destroyed.connect(_on_anchor_destroyed)
	return anchor

## La tuyère et la flamme. ⚠️ LA FLAMME EST FILLE DU CORPS : elle part avec lui.
func _mount_thrust(k: float) -> void:
	if not show_flame or _body == null:
		return
	_flame = CortegeFlame.make(tuning.flame_length, tuning.flame_width, side * 1.7 + 0.4)
	_flame.name = "Flame"
	# ⚠️ LE SIÈGE EST LU, PUIS ON MORD DEDANS. `+z` va vers l'intérieur du moteur : ajouter
	# `THROAT_BITE` recule le départ du panache dans la gorge, ce qui l'éclaire au lieu de la
	# laisser noire. Sans repère dans le binaire, on retombe sur l'estimation d'avant — mais on
	# le DIT, au lieu de laisser croire que la cote vient du modèle.
	var siege := _flame_socket_of(_nacelle)
	if is_zero_approx(siege.z):
		siege = Vector3(0.0, 0.0, -tuning.engine_size.z * 0.5)
		push_warning("[Poupe] %s : pas de « %s » dans la nacelle — flamme estimée"
			% [name, FLAME_SOCKET])
	_flame.position = (siege + Vector3(0.0, 0.0, tuning.throat_bite)) * k
	_flame.build()
	_body.add_child(_flame)
	_surge_clock = (side + 1.0) * tuning.surge_period / 3.0

func build_greybox() -> void:
	var k := tuning.scale_of(is_central)
	# ⚠️ LE BERCEAU EST UN CADRE OUVERT, PAS UN BLOC — et le LOT 1 en faisait un bloc. L'auteur
	# le décrit ainsi : « cadre ouvert, quatre pylônes blindés, rails, logements d'ancrage,
	# cavité centrale 8 m ». La différence n'est pas esthétique : ses quatre sockets d'ancrage
	# sont À MI-HAUTEUR, donc DANS le volume d'un bloc plein. Posés sur une boîte, les verrous
	# disparaissaient dedans — le défaut du LOT 1, reproduit à l'identique par une autre cause.
	var socle := _box("Deck", Vector3(tuning.cradle_size.x, 0.9, tuning.cradle_size.z) * k,
		Color(0.10, 0.10, 0.13))
	socle.position.y = 0.45 * k
	add_child(socle)
	for cote in [-1.0, 1.0]:
		for prof in [tuning.socket_z_front, tuning.socket_z_rear]:
			var pylone := _box("Pylon", Vector3(1.5, tuning.socket_y, 1.7) * k,
				Color(0.13, 0.13, 0.17))
			pylone.position = Vector3(cote * tuning.socket_x * k,
				tuning.socket_y * k * 0.5, prof * k)
			add_child(pylone)

	_body = Node3D.new()
	_body.name = "Body"
	# Le contrat de mariage du berceau, converti en Y-up : le moteur s'ENCASTRE, il ne s'empile pas.
	_rest = tuning.engine_seat * k
	_body.position = _rest
	add_child(_body)
	# ⚠️ LA BOÎTE EST PLUS ÉTROITE QUE LA BOÎTE ENGLOBANTE, ET C'EST DÉLIBÉRÉ. Le moteur livré est
	# une nacelle : ses 9,10 m de large sont ceux de ses carénages, pas ceux du fût que le
	# berceau enserre. Une boîte à la cote pleine avale les quatre sockets d'ancrage — qui sont à
	# |x| = 3,70 pour une demi-largeur de 3,96 — et les verrous redeviennent invisibles, ce qui
	# est le défaut du LOT 1 par une autre cause. `BODY_FIT` approche le fût ; il disparaîtra
	# avec la boîte grise, quand le vrai maillage entrera.
	_body.add_child(_box("Engine", tuning.engine_size * k * BODY_FIT, Color(0.14, 0.14, 0.18)))

	# ⚠️ LA TUYÈRE EST DANS LE CORPS, PAS DANS LE BERCEAU. C'est elle qui s'éteint en dérivant,
	# et c'est le seul signal qui dise « cette masse est encore une machine ». Le LOT 4 la
	# remplacera par une vraie flamme ; ce disque n'est là que pour que l'extinction existe.
	_nozzle = _box("Nozzle", Vector3(tuning.engine_size.x * k * BODY_FIT.x * 0.66, 0.30,
		tuning.engine_size.z * k * 0.09), Color(0.16, 0.05, 0.12))
	_nozzle.position.z = -tuning.engine_size.z * k * BODY_FIT.z * 0.5
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
			tuning.socket_y * k * 1.15,
			tuning.socket_z_front * k - 0.6)
		add_child(conduit)
		_conduits.append(conduit)
		_conduit_veins.append(vein)

	# Les ancrages ceinturent le berceau, au niveau où le joueur les voit : jamais dessous.
	var total := tuning.anchors_of(is_central)
	var largeur := tuning.cradle_size.x * k
	for i in total:
		var anchor := CortegeAnchor.make(tuning.anchor_health * charge, tuning.anchor_radius,
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

## Où siège le `i`-ème ancrage — SUR LES SOCKETS DU BINAIRE, plus sur des cotes inventées.
##
## ⚠️ `berceau_moteur.glb` porte quatre repères `CTRL | Socket ancrage AV/AR D/G`, et c'est le
## contrat. La pose du LOT 1 était une approximation en deux rangées arbitraires : elle donnait
## la bonne LECTURE — la spec dessine bien un triangle — mais pas les bonnes places, et le jour
## où la vraie géométrie entrera, les verrous auraient flotté à côté de leurs logements.
##
## ⚠️ ET UN LATÉRAL N'EN PORTE QUE TROIS pour quatre sockets. Le moteur, lui, en déclare
## exactement trois (`CTRL | Socket ancrage arriere / droit / gauche`) : c'est donc la paire
## AVANT plus UN arrière centré — le triangle de la spec §7, et cette fois il vient des pièces.
func _anchor_seat(i: int, total: int, _largeur: float, k: float) -> Vector3:
	var y := (tuning.socket_y + tuning.anchor_size.y * 0.5) * k
	# La paire avant (haute à l'écran), puis l'arrière : centré à trois, dédoublé à quatre.
	if i < 2:
		var cote := -1.0 if i == 0 else 1.0
		return Vector3(cote * tuning.socket_x * k, y, tuning.socket_z_front * k)
	if total <= 3:
		return Vector3(0.0, y, tuning.socket_z_rear * k)
	var cote_ar := -1.0 if i == 2 else 1.0
	return Vector3(cote_ar * tuning.socket_x * k, y, tuning.socket_z_rear * k)

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
	if _arc_mesh != null and _state == State.DETACHED:
		_arc_timer -= delta
		if _arc_timer <= 0.0:
			_arc_timer = 1.0 / ARC_HZ
			_redraw_arcs()
	if _state == State.DETACHING and _detach_clock >= tuning.detach_gone_at:
		_state = State.DETACHED
		_play_clips()
		_open_arcs()
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

## ⚠️ LES CLIPS SUIVENT L'ÉTAT, ET ILS NE SE RELANCENT PAS À CHAQUE IMAGE. `play()` appelé
## soixante fois par seconde remet l'animation à zéro : la libération du berceau tremblerait sur
## place au lieu de s'ouvrir. Et la continuité `Liberation` → `Berceau_vide` — que la forge a
## vérifiée à 0,000000 — ne vaut que si les deux se jouent dans cet ordre, une fois chacun.
func _play_clips() -> void:
	var moteur := "Fonctionnement"
	var berceau := "Intact"
	match _state:
		State.DAMAGED_1:
			moteur = "Endommage"
		State.DAMAGED_2:
			moteur = "Endommage"
			berceau = "Sous_contrainte"
		State.DETACHING:
			moteur = "Detachement"
			berceau = "Liberation"
		State.DETACHED:
			moteur = "Detachement"
			berceau = "Berceau_vide"
	_play(_engine_anim, moteur, "_clip_engine")
	_play(_cradle_anim, berceau, "_clip_cradle")

func _play(player: AnimationPlayer, clip: String, champ: String) -> void:
	if player == null or get(champ) == clip or not player.has_animation(clip):
		return
	set(champ, clip)
	player.play(clip)

func _on_anchor_destroyed(anchor: CortegeAnchor) -> void:
	_lost += 1
	var total := tuning.anchors_of(is_central)
	print("[Poupe] ancrage %d/%d du moteur %s abattu" % [_lost, total, _slot_name()])
	if _lost < total:
		_state = state_for(_lost, total, false)
		_play_clips()
		weakened.emit(self, _lost)
		return
	_state = State.DETACHING
	_play_clips()
	_detach_clock = 0.0
	set_locked(true)
	print("[Poupe] moteur %s : dernier ancrage rompu — arrachement" % _slot_name())
	detaching.emit(self)

## ⚠️ UN BERCEAU VIDE DOIT CRÉPITER, SINON C'EST UN TROU. La spec le demande deux fois — « arcs
## électriques » au §16 et au §17 — et la raison est de lecture : sans rien qui bouge, la place
## laissée par un moteur se lit comme une pièce qu'on aurait oublié de poser, pas comme une
## pièce qu'on a arrachée. C'est le seul mouvement qui reste dans le silence final.
func _open_arcs() -> void:
	_arc_mesh = ImmediateMesh.new()
	var arcs := MeshInstance3D.new()
	arcs.name = "Arcs"
	arcs.mesh = _arc_mesh
	arcs.position.y = tuning.socket_y * tuning.scale_of(is_central)
	arcs.position.z = (tuning.socket_z_front + tuning.socket_z_rear) * 0.5 \
		* tuning.scale_of(is_central)
	arcs.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# Sans marge, l'arc disparaît dès que le centre du berceau sort du cadre : la boîte
	# englobante d'un `ImmediateMesh` vide est nulle au montage. Même piège que le nœud d'épine.
	arcs.extra_cull_margin = 6.0
	var spark := StandardMaterial3D.new()
	spark.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	spark.vertex_color_use_as_albedo = true
	spark.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	spark.no_depth_test = true
	spark.render_priority = 6
	arcs.material_override = spark
	add_child(arcs)
	_arc_rng.seed = hash(name) * 7919
	_arc_timer = 0.0

## ⚠️ REDESSINÉS, PAS ANIMÉS. Un arc électrique n'a pas de trajectoire : il RECOMMENCE. Même
## règle que les arcs du nœud d'épine, et pour la même raison — une interpolation lisse se lit
## comme un tentacule.
func _redraw_arcs() -> void:
	if _arc_mesh == null:
		return
	var largeur := tuning.cradle_size.x * tuning.scale_of(is_central) * 0.34
	_arc_mesh.clear_surfaces()
	_arc_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
	for i in ARC_COUNT:
		var base := Vector3(_arc_rng.randf_range(-largeur, largeur), 0.0,
			_arc_rng.randf_range(-1.2, 1.2))
		var precedent := base
		for step in range(1, ARC_SEGMENTS + 1):
			var t := float(step) / float(ARC_SEGMENTS)
			var point := base + Vector3(
				_arc_rng.randf_range(-0.6, 0.6), ARC_REACH * t,
				_arc_rng.randf_range(-0.5, 0.5))
			_arc_mesh.surface_set_color(Color(1.0, 0.9, 1.0, 1.0) * (1.0 - t * 0.4))
			_arc_mesh.surface_add_vertex(precedent)
			_arc_mesh.surface_set_color(CortegeAnchor.TINT * (1.0 - t * 0.7))
			_arc_mesh.surface_add_vertex(point)
			precedent = point
	_arc_mesh.surface_end()

func _slot_name() -> String:
	if is_central:
		return "central"
	return "tribord" if side > 0.0 else "bâbord"
