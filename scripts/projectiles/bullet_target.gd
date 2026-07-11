class_name BulletTarget
extends RefCounted
## Lightweight collision proxy registered with the BulletManager (spec §21).
## The owning entity updates `position` every physics frame and receives
## damage through `hit_callback` (func(damage: float) -> void).

var position: Vector2 = Vector2.ZERO
var radius: float = 0.5
var team: int = 0
var enabled: bool = true
var hit_callback: Callable

static func make(p_team: int, p_radius: float, p_hit_callback: Callable) -> BulletTarget:
	var target := BulletTarget.new()
	target.team = p_team
	target.radius = p_radius
	target.hit_callback = p_hit_callback
	return target
