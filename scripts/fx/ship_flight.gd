class_name ShipFlight
extends Node
## Anime les pièces mobiles d'une coque de chasseur : volets de bord de fuite et
## pétales de tuyère (BRIEF-0033), puis — depuis `ADR-0044` — tout ce qu'une coque
## plus riche expose : pétales articulés, aérofreins, rampes d'entrée d'air,
## gouvernes de dérive, grappins d'appontage, verrière, lacet vectoriel des tuyères.
##
## POURQUOI UNE FABRIQUE — le joueur instancie sa coque sous un contrôleur, l'écran
## d'accueil l'instancie NUE (`boot.tscn`) et les escortes aussi. Une animation
## écrite dans `player_fighter_controller.gd` serait absente des quatre vaisseaux de
## l'accueil, c'est-à-dire de tous les gros plans du jeu. Même leçon, même parade que
## `CitadelLife` : une fonction statique appelable de partout.
##
## Elle ne lit RIEN : ni input, ni vitesse, ni autoload. Ce sont ses appelants qui
## lui poussent quatre ratios. Un vaisseau de décor peut donc s'en servir sans embarquer
## le moindre gameplay.
##
## ⚠️ TOUTES LES FAMILLES SONT OPTIONNELLES. `ADR-0044` §3 : on anime ce qu'on trouve
## par son nom exact, et on ignore ce qu'on ne trouve pas. Les deux coques d'avant (six
## pièces mobiles, ou aucune) volent sans une ligne de plus — et sans une erreur.

## Débattement des volets. ⚠️ Le plafond MÉCANIQUE mesuré sur la coque est de ±13° :
## au-delà, le volet mord la cloison de l'échancrure d'aile (BRIEF-0033-report §4,
## marge relevée à +1,94 mm à −12°). On reste à 11° — la marge est là pour absorber
## le lissage, qui dépasse légèrement la cible avant de s'y poser.
const FLAP_DEG := 11.0

## Flèche des ailes à pleine poussée. Le plafond MÉCANIQUE mesuré par la forge est de
## **32,25°** — au-delà l'aile traverse la peau de nacelle — et il est remesuré à chaque
## build, le build échouant en dessous de la cible. On reste à 26 : la marge absorbe le
## lissage, qui dépasse légèrement sa cible avant de s'y poser.
##
## Sens : l'aile se REPLIE quand la poussée monte, elle s'ouvre au ralenti.
const SWEEP_DEG := 26.0

## Ouverture des pétales à pleine poussée, POUR UNE COQUE SANS PÉTALES ARTICULÉS.
## Modélisés FERMÉS au repos : on ne fait que grandir. 1,45 est la valeur que la forge
## a utilisée pour son rendu de contrôle. Dès qu'une tuyère porte des `Petal_*`,
## l'échelle ne bouge plus : ce sont les pétales qui s'ouvrent, sur leur charnière.
const NOZZLE_OPEN := 1.45

## Les familles d'`ADR-0044`. Chaque valeur est UN CRAN SOUS le plafond mécanique
## MESURÉ par le build de `specter_9_c` (balayage BVH au pas de 1°, jeu minimal 2,5 mm,
## `build-hull.sh specter_9_c` du 2026-09-04) : la marge absorbe le lissage.
##
## | Famille   | plafond mesuré                    | réglage |
## |-----------|-----------------------------------|---------|
## | pétales   | 30° (Petal_R_07 touche son voisin) | 24°     |
## | lacet     | 7° (douille de nacelle)            | 5°      |
## | aérofrein | 94° (baie, arête, dérives)         | 60°     |
## | rampe     | aucune butée                       | 15°     |
## | gouverne  | 32° (dérive, nacelle)              | 24°     |
## | grappin   | aucune butée                       | 90°     |
## | verrière  | aucune butée                       | 40°     |
##
## « Aucune butée » ne veut pas dire « n'importe quoi » : au-delà, la pièce ne traverse
## rien mais raconte autre chose (un grappin à 150° rentre dans le fuselage par l'arrière).
const PETAL_DEG := 24.0
const NOZZLE_YAW_DEG := 5.0
const AIRBRAKE_DEG := 60.0
const INTAKE_DEG := 15.0
const RUDDER_DEG := 24.0
const GRAPPLE_DEG := 90.0
const CANOPY_DEG := 40.0

## SENS D'OUVERTURE, MESURÉS sur le `.glb` par la forge (rotation de +5° et lecture du
## déplacement d'un sommet) — jamais déduits. Aérofreins et rampes : rotation POSITIVE
## autour de +X = le bord arrière DESCEND, donc s'ouvrir, c'est tourner en négatif.
## Grappins : positif = la pointe descend (déployé). Verrière : positif = l'avant monte.
const AIRBRAKE_OPEN_SIGN := -1.0
const INTAKE_OPEN_SIGN := -1.0
const GRAPPLE_OPEN_SIGN := 1.0
const CANOPY_OPEN_SIGN := 1.0

## L'axe des gouvernes : celui de LEUR dérive, mesuré sur le `.glb` — inclinée de 30°
## vers l'extérieur ET couchée vers l'arrière (composante +Z). Une gouverne qui
## pivoterait sur +Y traverserait sa dérive. Rotation positive : le bord de fuite va vers
## +X (tribord) des deux côtés — c'est un lacet, pas une paire de volets.
const RUDDER_AXIS_L := Vector3(-0.4810, 0.8331, 0.2731)
const RUDDER_AXIS_R := Vector3(0.4810, 0.8331, 0.2731)

## Vitesses de réponse. Les volets sont vifs — ce sont des gouvernes, elles réagissent
## avec le pilote. Les tuyères sont lentes : une tuyère qui claque à chaque pression de
## touche lit comme un défaut, pas comme de la mécanique. Les aérofreins sont entre les
## deux, et l'appontage est lent : un grappin qui sort d'un coup n'est pas un mécanisme,
## c'est une bascule.
const FLAP_RESPONSE := 9.0
const NOZZLE_RESPONSE := 3.0
const BRAKE_RESPONSE := 5.0
const DOCK_RESPONSE := 1.5

var _wing_l: Node3D
var _wing_r: Node3D
var _flap_l: Node3D
var _flap_r: Node3D
var _nozzles: Array[Node3D] = []
## Pétales, à plat : tous ceux de toutes les tuyères. L'axe de charnière de chacun est
## dérivé UNE FOIS de sa position dans le repère de sa tuyère (voir `_bind_petals`).
var _petals: Array[Node3D] = []
var _petal_axes: PackedVector3Array = PackedVector3Array()
var _airbrakes: Array[Node3D] = []
var _intakes: Array[Node3D] = []
var _rudder_l: Node3D
var _rudder_r: Node3D
var _grapples: Array[Node3D] = []
var _canopy: Node3D

var _bank_target: float = 0.0
var _thrust_target: float = 0.0
var _brake_target: float = 0.0
var _dock_target: float = 0.0
var _bank: float = 0.0
var _thrust: float = 0.0
var _brake: float = 0.0
var _dock: float = 0.0

## `hull` : le Node3D instancié du `.glb`. Retourne `null` si la coque n'a aucune
## pièce mobile — une coque d'avant BRIEF-0033 continue de fonctionner, immobile.
static func apply(hull: Node3D) -> ShipFlight:
	if hull == null or hull.get_node_or_null("Wing_L") == null:
		return null
	var flight := ShipFlight.new()
	flight.name = "ShipFlight"
	hull.add_child(flight)
	return flight

func _ready() -> void:
	var hull := get_parent() as Node3D
	_wing_l = hull.get_node_or_null("Wing_L") as Node3D
	_wing_r = hull.get_node_or_null("Wing_R") as Node3D
	# Les volets sont des ENFANTS des ailes (le kit sait imbriquer depuis BRIEF-0035) :
	# ils suivent donc la fleche sans qu'on ait a la leur repercuter.
	if _wing_l != null:
		_flap_l = _wing_l.get_node_or_null("Flap_L") as Node3D
	if _wing_r != null:
		_flap_r = _wing_r.get_node_or_null("Flap_R") as Node3D
	for side in ["Nozzle_L", "Nozzle_R"]:
		var nozzle := hull.get_node_or_null(side) as Node3D
		if nozzle != null:
			_nozzles.append(nozzle)
			_bind_petals(nozzle)
	for side in ["L", "R"]:
		_collect(hull, "Airbrake_" + side, _airbrakes)
		_collect(hull, "Intake_" + side, _intakes)
		_collect(hull, "Grapple_" + side, _grapples)
	_rudder_l = hull.get_node_or_null("Rudder_L") as Node3D
	_rudder_r = hull.get_node_or_null("Rudder_R") as Node3D
	_canopy = hull.get_node_or_null("Canopy") as Node3D

static func _collect(hull: Node3D, part_name: String, into: Array[Node3D]) -> void:
	var part := hull.get_node_or_null(part_name) as Node3D
	if part != null:
		into.append(part)

## Les pétales d'une tuyère, et l'axe de charnière de chacun.
##
## Le `.glb` livre chaque nœud à l'identité, origine sur sa charnière : un pétale n'a
## donc AUCUN repère propre qui dirait dans quel sens il s'ouvre. Ce qui le dit, c'est
## sa POSITION dans le repère de la tuyère — BRIEF-0098 impose que le pivot de
## `Nozzle_*` soit sur l'axe, dans le plan des charnières, si bien que la position d'un
## pétale EST son vecteur radial. La charnière est la tangente au cercle des charnières :
## `axe = poussée × radial`. Un pétale s'étend vers l'arrière (+Z en repère Godot) depuis
## sa charnière ; tourner +Z autour de cette tangente d'un angle positif envoie sa pointe
## vers +radial, c'est-à-dire vers L'EXTÉRIEUR — ce qu'on vérifie par le test, pas par
## le raisonnement (`test_ship_flight.gd`).
func _bind_petals(nozzle: Node3D) -> void:
	for child in nozzle.get_children():
		var petal := child as Node3D
		if petal == null or not petal.name.begins_with("Petal_"):
			continue
		var radial := Vector3(petal.position.x, petal.position.y, 0.0)
		if radial.length_squared() < 1e-8:
			push_error("[ShipFlight] %s : petale sur l'axe de sa tuyere, aucune charniere derivable" % petal.name)
			continue
		_petals.append(petal)
		_petal_axes.append(Vector3.BACK.cross(radial.normalized()).normalized())

## Inclinaison demandée, de -1 (bâbord) à +1 (tribord).
##
## Les volets se déportent en OPPOSITION, comme de vrais ailerons : l'un descend
## quand l'autre monte. Les faire battre ensemble donnerait des aérofreins, ce qui
## raconte le freinage et non le virage.
func set_bank(ratio: float) -> void:
	_bank_target = clampf(ratio, -1.0, 1.0)

## Poussée, de 0 (dérive) à 1 (plein régime).
func set_thrust(ratio: float) -> void:
	_thrust_target = clampf(ratio, 0.0, 1.0)

## Freinage, de 0 à 1 : les aérofreins se lèvent. C'est le second signal du freinage
## subi (le premier est la plume qui s'étrangle, `drag_throttle`) — sur la coque du
## joueur, donc là où le joueur regarde quand ses commandes répondent mal.
func set_brake(ratio: float) -> void:
	_brake_target = clampf(ratio, 0.0, 1.0)

## Appontage, de 0 à 1 : les grappins sortent, puis la verrière s'ouvre. Poussé par la
## phase `DOCKING` ; une coque sans grappin n'en fait rien.
func set_docking(ratio: float) -> void:
	_dock_target = clampf(ratio, 0.0, 1.0)

func _process(delta: float) -> void:
	# Lissage exponentiel encadré : `minf(1.0, ...)` empêche le dépassement quand une
	# image très longue (chargement, alt-tab) rendrait le facteur supérieur à 1 — la
	# pièce partirait alors au-delà de sa cible, donc au-delà de son plafond mécanique.
	_bank = lerpf(_bank, _bank_target, minf(1.0, delta * FLAP_RESPONSE))
	_thrust = lerpf(_thrust, _thrust_target, minf(1.0, delta * NOZZLE_RESPONSE))
	_brake = lerpf(_brake, _brake_target, minf(1.0, delta * BRAKE_RESPONSE))
	_dock = lerpf(_dock, _dock_target, minf(1.0, delta * DOCK_RESPONSE))

	var deflection := deg_to_rad(FLAP_DEG * _bank)
	if _flap_l != null:
		_flap_l.rotation.x = deflection
	if _flap_r != null:
		_flap_r.rotation.x = -deflection

	# Fleche : babord et tribord en MIROIR. Une rotation de meme signe des deux cotes
	# enverrait l'aile tribord vers le NEZ — Godot tourne autour de +Y, et les deux
	# ailes sont de part et d'autre de l'axe.
	var sweep := deg_to_rad(SWEEP_DEG * _thrust)
	if _wing_l != null:
		_wing_l.rotation.y = sweep
	if _wing_r != null:
		_wing_r.rotation.y = -sweep

	# Tuyeres : sans petales articules, on grandit (BRIEF-0033) ; avec, on tourne les
	# petales et la tuyere garde son echelle. Dans les deux cas, un lacet vectoriel
	# suit l'inclinaison — les deux tuyeres du MEME cote, c'est un vecteur de poussee,
	# pas une paire de gouvernes.
	var open := 1.0 + (NOZZLE_OPEN - 1.0) * _thrust
	var yaw := deg_to_rad(NOZZLE_YAW_DEG * _bank)
	for nozzle in _nozzles:
		if _petals.is_empty():
			nozzle.scale = Vector3(open, open, 1.0)
		nozzle.rotation.y = yaw
	# Le freinage referme les petales que la poussee ouvrait : une tuyere qui s'etrangle,
	# c'est aussi ce que la plume raconte (`drag_throttle`), et les deux doivent le dire
	# ensemble.
	var petal := deg_to_rad(PETAL_DEG * _thrust * (1.0 - _brake))
	for i in _petals.size():
		_petals[i].quaternion = Quaternion(_petal_axes[i], petal)

	var brake := AIRBRAKE_OPEN_SIGN * deg_to_rad(AIRBRAKE_DEG * _brake)
	for airbrake in _airbrakes:
		airbrake.rotation.x = brake

	var intake := INTAKE_OPEN_SIGN * deg_to_rad(INTAKE_DEG * _thrust)
	for ramp in _intakes:
		ramp.rotation.x = intake

	# Gouvernes : les deux du MEME cote, comme un lacet dans le virage — c'est ce qui
	# les distingue des volets, qui sont en opposition. Chacune tourne autour de l'axe
	# de SA derive.
	var rudder := deg_to_rad(RUDDER_DEG * _bank)
	if _rudder_l != null:
		_rudder_l.quaternion = Quaternion(RUDDER_AXIS_L.normalized(), rudder)
	if _rudder_r != null:
		_rudder_r.quaternion = Quaternion(RUDDER_AXIS_R.normalized(), rudder)

	# Appontage : les grappins sortent sur la premiere moitie de la course, la verriere
	# s'ouvre sur la seconde — un mecanisme apres l'autre, pas tout en meme temps.
	var grapple := GRAPPLE_OPEN_SIGN * deg_to_rad(GRAPPLE_DEG * clampf(_dock * 2.0, 0.0, 1.0))
	for hook in _grapples:
		hook.rotation.x = grapple
	if _canopy != null:
		_canopy.rotation.x = CANOPY_OPEN_SIGN * deg_to_rad(CANOPY_DEG * clampf(_dock * 2.0 - 1.0, 0.0, 1.0))
