class_name EnemyData
extends Resource
## Enemy tuning values (spec §11, §22). Units: world units, seconds.

## Trajectoire suivie. Le mouvement est DATA-DRIVEN : le contrôleur échantillonne
## EnemyPath, il ne décide de rien. Ajouter une famille, c'est choisir ici.
enum Path { WEAVE, DIVE, ARC_SWEEP, HOVER_STRAFE }
@export var path: Path = Path.WEAVE

@export var display_name: String = "enemy"
@export var max_health: float = 20.0
## Downward travel speed (units/s).
@export var move_speed: float = 3.5
## Lateral sine weave: amplitude (units) and frequency (cycles/s).
@export var weave_amplitude: float = 1.5
@export var weave_frequency: float = 0.4
## Seconds between shots; enemies only fire while inside the play area.
@export var fire_interval: float = 1.9
@export var projectile: ProjectileData
## Logical hitbox radius (generous on enemies, spec §5.3 accessibility).
@export var hitbox_radius: float = 0.45
@export var score_value: int = 100

## DIVE : secondes d'approche lente avant que l'ennemi ne fonde.
@export var dive_delay: float = 1.2
## HOVER_STRAFE : ligne où l'ennemi se stabilise, et durée du vol stationnaire.
@export var hold_y: float = 3.0
@export var hold_time: float = 2.2

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if max_health <= 0.0:
		errors.append("max_health must be > 0")
	if move_speed <= 0.0:
		errors.append("move_speed must be > 0")
	if fire_interval <= 0.0:
		errors.append("fire_interval must be > 0")
	if hitbox_radius <= 0.0:
		errors.append("hitbox_radius must be > 0")
	if score_value < 0:
		errors.append("score_value must be >= 0")
	if path == Path.DIVE and dive_delay < 0.0:
		errors.append("dive_delay must be >= 0")
	if path == Path.HOVER_STRAFE and hold_time <= 0.0:
		errors.append("hold_time must be > 0 for HOVER_STRAFE")
	if projectile == null:
		errors.append("projectile is required")
	else:
		errors.append_array(projectile.validate())
	return errors
