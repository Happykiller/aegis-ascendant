class_name ProjectileData
extends Resource
## Projectile tuning values (spec §22.1). Units: world units, seconds.

## Travel speed (units/s). Spec §5.3: moderate speeds, readability first.
@export var speed: float = 22.0
## Collision radius on the logical plane; must match the visual size (spec §17.3).
@export var radius: float = 0.12
## Damage applied on hit.
@export var damage: float = 10.0
## Lifetime in seconds (safety net on top of out-of-bounds culling).
@export var ttl: float = 2.0

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if speed <= 0.0:
		errors.append("speed must be > 0")
	if radius <= 0.0:
		errors.append("radius must be > 0")
	if damage < 0.0:
		errors.append("damage must be >= 0")
	if ttl <= 0.0:
		errors.append("ttl must be > 0")
	return errors
