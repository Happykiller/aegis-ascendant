class_name AegisCitadel
extends Node3D
## The friendly mobile fortress (spec §3.3, §15.4). Appears for the docking
## sequence (spec §6.5) and becomes the player-controlled body in the fortress
## phase (spec §12). A 3D hull (ADR-0008) sitting on the play plane.

signal arrived

@export var hull_scene: PackedScene

var plane_position: Vector2 = Vector2(0.0, 20.0)
var _slide_target: Vector2 = Vector2(0.0, 20.0)
var _slide_speed: float = 0.0
var _sliding: bool = false
var _hull: Node3D
## Mouth of the docking bay, in plane coordinates relative to the hull's origin.
var _bay_offset: Vector2 = Vector2(0.0, -3.0)

func _ready() -> void:
	if hull_scene != null:
		_hull = hull_scene.instantiate() as Node3D
		add_child(_hull)
		var entry := _hull.get_node_or_null("Dock_Entry") as Node3D
		if entry != null:
			_bay_offset = Vector2(entry.position.x, -entry.position.z)
		else:
			push_error("[AegisCitadel] hull has no 'Dock_Entry' attach point")
	position = GameplayPlane.to_world(plane_position)
	set_physics_process(false)

## Docking bay mouth in plane coordinates, taken from the hull's own attach point.
func bay_position() -> Vector2:
	return plane_position + _bay_offset

func slide_to(target: Vector2, speed: float) -> void:
	_slide_target = target
	_slide_speed = speed
	_sliding = true
	set_physics_process(true)

func _physics_process(delta: float) -> void:
	if not _sliding:
		return
	plane_position = plane_position.move_toward(_slide_target, _slide_speed * delta)
	position = GameplayPlane.to_world(plane_position)
	if plane_position.distance_to(_slide_target) < 0.05:
		_sliding = false
		set_physics_process(false)
		arrived.emit()
