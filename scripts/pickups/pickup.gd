class_name Pickup
extends Node3D
## Collectible bonus (spec §10). Pooled: floats and spins, is magnetically drawn
## to the player at short range, and is collected on contact. Logic runs on the
## logical plane; a billboarded Sprite3D shows the forge-authored icon.

enum Kind { POWER, SHIELD, SCORE }

signal collected(pickup: Pickup)

const _ATTRACT_RADIUS := 2.6
const _COLLECT_RADIUS := 0.7
const _ATTRACT_SPEED := 16.0
const _DRIFT_SPEED := 2.2       # gentle downward drift (toward the player, -y)
const _LIFETIME := 9.0

const _TEXTURE: Dictionary = {
	Kind.POWER: preload("res://assets/imported/sprites/pickups/power_core.svg"),
	Kind.SHIELD: preload("res://assets/imported/sprites/pickups/shield_cell.svg"),
	Kind.SCORE: preload("res://assets/imported/sprites/pickups/score_prism.svg"),
}

var kind: Kind = Kind.POWER
var plane_position: Vector2 = Vector2.ZERO
var active: bool = false

var _player: PlayerFighterController
var _sprite: Sprite3D
var _age: float = 0.0
var _spin: float = 0.0

func _ready() -> void:
	_sprite = Sprite3D.new()
	_sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_sprite.shaded = false
	_sprite.pixel_size = 0.012
	_sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	add_child(_sprite)
	_set_active(false)

func setup(player: PlayerFighterController) -> void:
	_player = player

func activate(p_kind: Kind, p_plane_position: Vector2) -> void:
	kind = p_kind
	plane_position = p_plane_position
	_sprite.texture = _TEXTURE[p_kind]
	_age = 0.0
	position = GameplayPlane.to_world(plane_position)
	_set_active(true)

func deactivate() -> void:
	_set_active(false)

func _set_active(value: bool) -> void:
	active = value
	visible = value
	set_physics_process(value)

func _physics_process(delta: float) -> void:
	_age += delta
	if _age >= _LIFETIME:
		deactivate()
		return
	_spin += delta * 2.5
	_sprite.rotation.z = sin(_spin) * 0.35
	_sprite.position.y = sin(_age * 3.0) * 0.15 # bob

	var to_player := Vector2.ZERO
	var dist := INF
	if _player != null:
		to_player = _player.plane_position - plane_position
		dist = to_player.length()

	if dist <= _COLLECT_RADIUS:
		deactivate()
		collected.emit(self)
		return
	if dist <= _ATTRACT_RADIUS:
		plane_position = plane_position.move_toward(_player.plane_position, _ATTRACT_SPEED * delta)
	else:
		plane_position.y -= _DRIFT_SPEED * delta
		if plane_position.y < GameplayPlane.BOUNDS.position.y - 1.0:
			deactivate()
			return
	position = GameplayPlane.to_world(plane_position)
