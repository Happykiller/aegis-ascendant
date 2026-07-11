class_name EnemyData
extends Resource
## Enemy tuning values (spec §11, §22). Units: world units, seconds.

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
	if projectile == null:
		errors.append("projectile is required")
	else:
		errors.append_array(projectile.validate())
	return errors
