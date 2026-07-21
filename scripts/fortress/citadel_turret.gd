class_name CitadelTurret
extends Node3D
## Tourelle de la citadelle — pièce mobile instanciée sur un marqueur `Turret_NN`
## de la coque (BRIEF-0032).
##
## Elle ne connaît **pas** le gameplay : elle balaie en veille, en permanence. C'est
## ce qui lui permet de vivre à l'écran d'accueil comme en combat, sans dépendre d'un
## spawner d'ennemis ni d'une liste de cibles — et donc de ne jamais se figer là où
## on la regarde le plus.
##
## Le monde a Y en haut et le plan de jeu en XZ (`GameplayPlane`) : le gisement d'une
## tourelle est donc une rotation autour de **Y**.

## Amplitude du balayage, en gisement. Au-delà d'une cinquantaine de degrés la
## tourelle a l'air de chercher quelque chose qu'elle ne trouve pas ; en dessous de
## vingt, elle a l'air en panne.
const SWEEP_DEG := 42.0

## Période de base. Lente : une forteresse en veille surveille, elle ne s'agite pas.
const SWEEP_PERIOD := 13.0

## Débattement en site, appliqué au mantelet s'il existe (voir `_mantlet`).
const PITCH_DEG := 5.0
const PITCH_PERIOD := 8.5

## Angle d'or. Six tourelles qui partagent une phase lisent comme un métronome —
## le mouvement devient mécanique et trahit qu'un seul script les pilote toutes.
## L'angle d'or est le pire diviseur possible : aucune paire d'indices ne retombe
## en phase, quel que soit leur nombre.
const GOLDEN_ANGLE := 2.399963229728653  # rad

## Décalage de période par index. Sans lui, des tourelles simplement déphasées
## reviennent toutes en phase à chaque période : le métronome revient, en retard.
const PERIOD_SPREAD := 1.7

var _yaw_phase: float = 0.0
var _pitch_phase: float = 0.0
var _yaw_period: float = SWEEP_PERIOD
var _pitch_period: float = PITCH_PERIOD
var _rest_yaw: float = 0.0
var _age: float = 0.0

## Mantelet portant les tubes, si la coque en expose un : le site s'y applique seul,
## sinon la tourelle entière basculerait, socle compris. Absent = pas de site, et
## c'est un dégradé acceptable, pas une erreur.
var _mantlet: Node3D

## Appelé par la citadelle juste après l'instanciation. `index` est le rang du
## marqueur (`Turret_01` -> 0) : c'est lui, et lui seul, qui désynchronise.
func setup(index: int) -> void:
	_yaw_phase = float(index) * GOLDEN_ANGLE
	_pitch_phase = float(index) * GOLDEN_ANGLE * 0.5
	_yaw_period = SWEEP_PERIOD + float(index) * PERIOD_SPREAD
	_pitch_period = PITCH_PERIOD + float(index) * PERIOD_SPREAD * 0.6

func _ready() -> void:
	_rest_yaw = rotation.y
	_mantlet = get_node_or_null("Mantlet") as Node3D
	# Départ à un instant quelconque du cycle : sans ça, toutes les tourelles
	# partent de la même pose au chargement de la scène, et la première seconde
	# les montre alignées — précisément ce qu'on cherche à éviter.
	_age = _yaw_phase * _yaw_period / TAU

func _process(delta: float) -> void:
	_age += delta
	rotation.y = _rest_yaw + deg_to_rad(
		SWEEP_DEG * sin(_age * TAU / _yaw_period + _yaw_phase))
	if _mantlet != null:
		_mantlet.rotation.x = deg_to_rad(
			PITCH_DEG * sin(_age * TAU / _pitch_period + _pitch_phase))
