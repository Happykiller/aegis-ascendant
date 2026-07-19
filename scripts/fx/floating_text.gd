class_name FloatingText
extends Label3D
## A short word that pops at a world position, drifts up-screen and fades — used
## to say what a pickup was (spec §10 feedback). Pooled: never freed in gameplay,
## returned to its owner via `finished`.

signal finished(label: FloatingText)

## World units risen (up-screen = world -Z) over the life.
const _RISE := 1.7
const _LIFE := 0.85

var _age: float = 0.0
var _base_z: float = 0.0
var _active: bool = false

func _ready() -> void:
	billboard = BaseMaterial3D.BILLBOARD_ENABLED
	shaded = false
	double_sided = true
	no_depth_test = true
	pixel_size = 0.006
	font_size = 64
	outline_size = 18
	outline_modulate = Color(0.0, 0.0, 0.0, 0.85)
	visible = false
	set_process(false)

## Show `content` in `color` at `world_position`, then animate and recycle.
func pop(content: String, color: Color, world_position: Vector3) -> void:
	text = content
	modulate = Color(color.r, color.g, color.b, 1.0)
	position = world_position
	_base_z = world_position.z
	_age = 0.0
	_active = true
	visible = true
	set_process(true)

func _process(delta: float) -> void:
	if not _active:
		return
	_age += delta
	var t := _age / _LIFE
	if t >= 1.0:
		_active = false
		visible = false
		set_process(false)
		finished.emit(self)
		return
	position.z = _base_z - _RISE * t   # drift up-screen
	modulate.a = 1.0 - t * t           # ease-out fade
