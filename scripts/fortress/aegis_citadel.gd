class_name AegisCitadel
extends Node3D
## The friendly mobile fortress (spec §3.3, §15.4). Appears for the docking
## sequence (spec §6.5) and becomes the player-controlled body in the fortress
## phase (spec §12). A large concept sprite laid flat on the play plane.

signal arrived

@export var sprite_texture: Texture2D
@export var sprite_pixel_size: float = 0.024

var plane_position: Vector2 = Vector2(0.0, 20.0)
var _slide_target: Vector2 = Vector2(0.0, 20.0)
var _slide_speed: float = 0.0
var _sliding: bool = false
var _sprite: Sprite3D

func _ready() -> void:
	_sprite = Sprite3D.new()
	_sprite.texture = sprite_texture
	_sprite.pixel_size = sprite_pixel_size
	_sprite.shaded = false
	_sprite.double_sided = true
	_sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	_sprite.rotation = Vector3(deg_to_rad(-90.0), 0.0, 0.0)
	add_child(_sprite)
	position = GameplayPlane.to_world(plane_position)
	set_physics_process(false)

## Docking bay mouth in plane coordinates (bottom-center of the sprite).
func bay_position() -> Vector2:
	return plane_position + Vector2(0.0, -3.0)

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
