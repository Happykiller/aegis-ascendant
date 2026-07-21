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

## Pas de débattement en site : `citadel_turret.glb` est **un seul maillage**
## (`export_hull()` n'exporte qu'un objet — limite du kit signalée par la forge,
## BRIEF-0032-report §9). Sans mantelet séparé, un site basculerait le socle avec
## les tubes. Le gisement seul suffit d'ailleurs à faire vivre la pièce ; on
## n'écrit pas un code qui cherche un nœud dont on sait qu'il n'existe pas.

var _yaw_phase: float = 0.0
var _yaw_period: float = SWEEP_PERIOD
var _rest_yaw: float = 0.0
var _age: float = 0.0

## Angle d'or. Six tourelles qui partagent une phase lisent comme un métronome —
## le mouvement devient mécanique et trahit qu'un seul script les pilote toutes.
## L'angle d'or est le pire diviseur possible : aucune paire d'indices ne retombe
## en phase, quel que soit leur nombre.
const GOLDEN_ANGLE := 2.399963229728653  # rad

## Décalage de période par index. Sans lui, des tourelles simplement déphasées
## reviennent toutes en phase à chaque période : le métronome revient, en retard.
const PERIOD_SPREAD := 1.7

## Appelé par la citadelle juste après l'instanciation. `index` est le rang du
## marqueur (`Turret_01` -> 0) : c'est lui, et lui seul, qui désynchronise.
func setup(index: int) -> void:
	_yaw_phase = float(index) * GOLDEN_ANGLE
	_yaw_period = SWEEP_PERIOD + float(index) * PERIOD_SPREAD

func _ready() -> void:
	_rest_yaw = rotation.y
	# Départ à un instant quelconque du cycle, ET pose appliquée TOUT DE SUITE.
	# Avancer `_age` sans écrire la rotation ne suffit pas : `rotation.y` n'est
	# posé que dans `_process`, donc à la première image les six tourelles seraient
	# toutes à leur pose de repos — alignées, précisément le défaut visé.
	# (Défaut réel, attrapé par test_citadel_animation.gd, pas par relecture.)
	_age = _yaw_phase * _yaw_period / TAU
	_apply()

func _process(delta: float) -> void:
	_age += delta
	_apply()

func _apply() -> void:
	rotation.y = _rest_yaw + deg_to_rad(
		SWEEP_DEG * sin(_age * TAU / _yaw_period + _yaw_phase))
