class_name PlayerStats
extends Resource
## Player fighter tuning values (spec §8.1: no gameplay value hard-coded).
## Units: distances in world units, times in seconds, angles in degrees.

## Maximum planar speed (units/s).
@export var max_speed: float = 14.0
## Time to reach max_speed from rest; spec §7.3 requires < 0.25 s.
@export var accel_time: float = 0.18
## Logical hitbox radius; deliberately smaller than the visual model (spec §8.2).
@export var hitbox_radius: float = 0.25
## Seconds between primary shots.
@export var fire_interval: float = 0.12
## Maximum visual roll when strafing; never affects the hitbox (spec §7.3).
@export var max_bank_deg: float = 35.0

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if max_speed <= 0.0:
		errors.append("max_speed must be > 0")
	if accel_time <= 0.0 or accel_time > 0.25:
		errors.append("accel_time must be in (0, 0.25] (spec §7.3)")
	if hitbox_radius <= 0.0:
		errors.append("hitbox_radius must be > 0")
	if fire_interval <= 0.0:
		errors.append("fire_interval must be > 0")
	return errors
