class_name CameraDirector
extends Node3D
## Owns the gameplay Camera3D and applies centralized trauma-based screen shake
## (spec §16.3). The camera keeps a fixed rest pose; shake is an additive offset
## so gameplay dodging is never disturbed. Trauma accumulates (capped) and decays.

@export var max_translation: float = 0.35
@export var max_roll_deg: float = 2.2
@export var trauma_decay: float = 1.6
@export var noise_speed: float = 28.0
## Accessibility multiplier (spec §16.3): 0 disables shake entirely.
@export var shake_multiplier: float = 1.0

var _camera: Camera3D
var _rest_transform: Transform3D
var _trauma: float = 0.0
var _noise: FastNoiseLite
var _noise_time: float = 0.0

func _ready() -> void:
	_camera = get_node_or_null("Camera3D") as Camera3D
	if _camera == null:
		push_error("[CameraDirector] expects a child Camera3D")
		return
	_rest_transform = _camera.transform
	_noise = FastNoiseLite.new()
	_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	_noise.frequency = 0.08

## Add trauma in [0,1]; shake intensity scales with trauma squared.
func add_trauma(amount: float) -> void:
	_trauma = clampf(_trauma + amount, 0.0, 1.0)

func _process(delta: float) -> void:
	if _camera == null:
		return
	if _trauma <= 0.0:
		_camera.transform = _rest_transform
		return
	_trauma = maxf(_trauma - trauma_decay * delta, 0.0)
	_noise_time += delta * noise_speed
	var shake := _trauma * _trauma * shake_multiplier
	var ox := _noise.get_noise_2d(_noise_time, 0.0)
	var oy := _noise.get_noise_2d(0.0, _noise_time)
	var oz := _noise.get_noise_2d(_noise_time, _noise_time)
	var offset := Vector3(ox, oy, 0.0) * max_translation * shake
	var roll := deg_to_rad(max_roll_deg) * oz * shake
	var shaken := _rest_transform
	shaken.origin += offset
	shaken.basis = _rest_transform.basis * Basis(Vector3(0.0, 0.0, 1.0), roll)
	_camera.transform = shaken
