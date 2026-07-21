class_name ShipFlight
extends Node
## Anime les pièces mobiles d'une coque de chasseur : volets de bord de fuite et
## pétales de tuyère (BRIEF-0033).
##
## POURQUOI UNE FABRIQUE — le joueur instancie sa coque sous un contrôleur, l'écran
## d'accueil l'instancie NUE (`boot.tscn`) et les escortes aussi. Une animation
## écrite dans `player_fighter_controller.gd` serait absente des quatre vaisseaux de
## l'accueil, c'est-à-dire de tous les gros plans du jeu. Même leçon, même parade que
## `CitadelLife` : une fonction statique appelable de partout.
##
## Elle ne lit RIEN : ni input, ni vitesse, ni autoload. Ce sont ses appelants qui
## lui poussent deux ratios. Un vaisseau de décor peut donc s'en servir sans embarquer
## le moindre gameplay.

## Débattement des volets. ⚠️ Le plafond MÉCANIQUE mesuré sur la coque est de ±13° :
## au-delà, le volet mord la cloison de l'échancrure d'aile (BRIEF-0033-report §4,
## marge relevée à +1,94 mm à −12°). On reste à 11° — la marge est là pour absorber
## le lissage, qui dépasse légèrement la cible avant de s'y poser.
const FLAP_DEG := 11.0

## Ouverture des pétales à pleine poussée. Modélisés FERMÉS au repos : on ne fait que
## grandir. 1,45 est la valeur que la forge a utilisée pour son rendu de contrôle.
const NOZZLE_OPEN := 1.45

## Vitesses de réponse. Les volets sont vifs — ce sont des gouvernes, elles réagissent
## avec le pilote. Les tuyères sont lentes : une tuyère qui claque à chaque pression de
## touche lit comme un défaut, pas comme de la mécanique.
const FLAP_RESPONSE := 9.0
const NOZZLE_RESPONSE := 3.0

var _flap_l: Node3D
var _flap_r: Node3D
var _nozzles: Array[Node3D] = []

var _bank_target: float = 0.0
var _thrust_target: float = 0.0
var _bank: float = 0.0
var _thrust: float = 0.0

## `hull` : le Node3D instancié du `.glb`. Retourne `null` si la coque n'a aucune
## pièce mobile — une coque d'avant BRIEF-0033 continue de fonctionner, immobile.
static func apply(hull: Node3D) -> ShipFlight:
	if hull == null or hull.get_node_or_null("Flap_L") == null:
		return null
	var flight := ShipFlight.new()
	flight.name = "ShipFlight"
	hull.add_child(flight)
	return flight

func _ready() -> void:
	var hull := get_parent() as Node3D
	_flap_l = hull.get_node_or_null("Flap_L") as Node3D
	_flap_r = hull.get_node_or_null("Flap_R") as Node3D
	for side in ["Nozzle_L", "Nozzle_R"]:
		var nozzle := hull.get_node_or_null(side) as Node3D
		if nozzle != null:
			_nozzles.append(nozzle)

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

func _process(delta: float) -> void:
	# Lissage exponentiel encadré : `minf(1.0, ...)` empêche le dépassement quand une
	# image très longue (chargement, alt-tab) rendrait le facteur supérieur à 1 — la
	# pièce partirait alors au-delà de sa cible, donc au-delà de son plafond mécanique.
	_bank = lerpf(_bank, _bank_target, minf(1.0, delta * FLAP_RESPONSE))
	_thrust = lerpf(_thrust, _thrust_target, minf(1.0, delta * NOZZLE_RESPONSE))

	var deflection := deg_to_rad(FLAP_DEG * _bank)
	if _flap_l != null:
		_flap_l.rotation.x = deflection
	if _flap_r != null:
		_flap_r.rotation.x = -deflection

	var open := 1.0 + (NOZZLE_OPEN - 1.0) * _thrust
	for nozzle in _nozzles:
		nozzle.scale = Vector3(open, open, 1.0)
