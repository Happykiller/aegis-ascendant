class_name CitadelBeacon
extends Node3D
## Balise flottante de la citadelle — instanciée sur un marqueur `Beacon_NN`
## (BRIEF-0032, d'après la planche : trois drones tenus dans un champ hexagonal).
##
## Elle ne se pose sur rien : elle dérive autour de son point d'ancrage. C'est le
## seul élément de la forteresse qui n'est pas rigidement lié à la coque, et c'est
## ce qui donne l'échelle — une masse immobile de 20 m paraît plus grande quand
## quelque chose de petit bouge devant elle.

## Rayon d'orbite dans le plan de jeu, et amplitude de la dérive verticale.
## Volontairement faibles : une balise qui parcourt trois mètres cesse d'être un
## satellite et devient un objet à la dérive.
const ORBIT_RADIUS := 0.55
const RISE := 0.30

## Périodes délibérément NON HARMONIQUES entre elles (17,3 / 11,9 / 7,1 s) —
## même parti pris que la chorégraphie de l'écran d'accueil (`title_stage.gd`) :
## la balise ne doit jamais repasser deux fois par la même pose, sinon l'œil
## repère la boucle et l'objet redevient un décor.
const ORBIT_PERIOD := 17.3
const RISE_PERIOD := 11.9
## Rotation propre de la balise. `citadel_beacon.glb` est UN SEUL maillage — le
## kit n'exporte qu'un objet (BRIEF-0032-report §9), l'anneau ne peut donc pas
## tourner seul. La balise tourne donc en entier autour de son axe, que le modèle
## désigne par `Ring_Axis` : (0, +0,30, 0), c'est-à-dire son Y local.
const SPIN_PERIOD := 7.1

const GOLDEN_ANGLE := 2.399963229728653  # rad — voir CitadelTurret

var _phase: float = 0.0
var _rest: Vector3 = Vector3.ZERO
var _age: float = 0.0

func setup(index: int) -> void:
	_phase = float(index) * GOLDEN_ANGLE

func _ready() -> void:
	# Pose de repos relevée UNE fois : toute l'animation est un décalage par
	# rapport à elle, jamais une position absolue accumulée — sinon la balise
	# dérive pour de bon au fil des minutes.
	_rest = position
	_age = _phase * ORBIT_PERIOD / TAU

func _process(delta: float) -> void:
	_age += delta
	var orbit := _age * TAU / ORBIT_PERIOD + _phase
	position = _rest + Vector3(
		cos(orbit) * ORBIT_RADIUS,
		sin(_age * TAU / RISE_PERIOD + _phase) * RISE,
		sin(orbit) * ORBIT_RADIUS)
	rotation.y = _age * TAU / SPIN_PERIOD
