class_name PlayerFighterController
extends Node3D
## Player fighter: arcade movement on the logical 2D plane (spec §7.3, §16.2).
## The logical position is authoritative; the 3D node only projects it.
## Visual banking lives on VisualRoot and never affects the hitbox.

@export var stats: PlayerStats

var plane_position: Vector2 = Vector2(0.0, -5.0)
var _velocity: Vector2 = Vector2.ZERO

@onready var _visual_root: Node3D = $VisualRoot

func _ready() -> void:
	assert(stats != null, "PlayerFighterController requires a PlayerStats resource")
	var errors := stats.validate()
	for error in errors:
		push_error("[PlayerFighter] invalid stats: %s" % error)
	position = GameplayPlane.to_world(plane_position)

func _physics_process(delta: float) -> void:
	var input := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	_velocity = integrate_velocity(_velocity, input, stats.max_speed, stats.accel_time, delta)
	plane_position = GameplayPlane.clamp_to_bounds(plane_position + _velocity * delta)
	position = GameplayPlane.to_world(plane_position)
	_apply_visual_bank(delta)

## Pure movement math, testable headless: accelerate toward input * max_speed,
## reaching it in accel_time seconds (spec §7.3: max speed in < 250 ms).
static func integrate_velocity(current: Vector2, input: Vector2, max_speed: float,
		accel_time: float, delta: float) -> Vector2:
	var target := input.limit_length(1.0) * max_speed
	var accel := max_speed / accel_time
	return current.move_toward(target, accel * delta)

func _apply_visual_bank(delta: float) -> void:
	var bank_target := -_velocity.x / stats.max_speed * deg_to_rad(stats.max_bank_deg)
	_visual_root.rotation.z = lerp_angle(_visual_root.rotation.z, bank_target,
		minf(1.0, delta * 12.0))
