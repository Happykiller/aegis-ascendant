class_name EnemyController
extends Node3D
## Composition base for enemies (spec §11, §20.3). Graybox behaviour:
## descend + lateral sine weave, slow forward fire (Needle Scout family).
## Instances are pooled: spawners preinstantiate then activate/deactivate;
## death never queue_free()s during gameplay (spec §26.1).

## Logical "down the screen" (toward the player).
const DIR_DOWN := Vector2(0.0, -1.0)
const MUZZLE_OFFSET := Vector2(0.0, -0.6)
const DESPAWN_MARGIN := 1.5

signal destroyed(enemy: EnemyController)

@export var data: EnemyData
## Optional wiring for enemies placed directly in a scene (spawners inject
## through setup() instead).
@export var bullet_manager_path: NodePath
@export var auto_activate: bool = false

var active: bool = false
var plane_position: Vector2 = Vector2.ZERO

var _bullet_manager: BulletManager
var _target: BulletTarget
var _base_x: float = 0.0
var _age: float = 0.0
var _fire_timer: float = 0.0

@onready var _health: HealthComponent = $HealthComponent

func _ready() -> void:
	assert(data != null, "EnemyController requires an EnemyData resource")
	for error in data.validate():
		push_error("[Enemy:%s] invalid data: %s" % [data.display_name, error])
	add_to_group("enemies")
	_health.died.connect(_on_died)
	_target = BulletTarget.make(BulletManager.Team.ENEMY, data.hitbox_radius,
		Callable(_health, "apply_damage"))
	_target.enabled = false
	if _bullet_manager == null and not bullet_manager_path.is_empty():
		setup(get_node(bullet_manager_path) as BulletManager)
	_set_active(false)
	if auto_activate:
		activate(GameplayPlane.to_plane(position))

## One-time wiring done by the owner (spawner or scene).
func setup(bullet_manager: BulletManager) -> void:
	_bullet_manager = bullet_manager
	_bullet_manager.register_target(_target)

func activate(spawn_plane_position: Vector2) -> void:
	plane_position = spawn_plane_position
	_base_x = spawn_plane_position.x
	_age = 0.0
	_fire_timer = data.fire_interval
	_health.max_health = data.max_health
	_health.revive()
	position = GameplayPlane.to_world(plane_position)
	_set_active(true)

func deactivate() -> void:
	_set_active(false)

func _set_active(value: bool) -> void:
	active = value
	visible = value
	set_physics_process(value)
	if _target != null:
		_target.enabled = value

func _physics_process(delta: float) -> void:
	_age += delta
	plane_position.y -= data.move_speed * delta
	plane_position.x = _base_x + sin(_age * data.weave_frequency * TAU) * data.weave_amplitude
	position = GameplayPlane.to_world(plane_position)
	_target.position = plane_position
	if plane_position.y < GameplayPlane.BOUNDS.position.y - DESPAWN_MARGIN:
		deactivate()
		return
	_update_fire(delta)

func _update_fire(delta: float) -> void:
	if _bullet_manager == null or not GameplayPlane.is_inside(plane_position):
		return
	_fire_timer -= delta
	if _fire_timer <= 0.0:
		_fire_timer = data.fire_interval
		_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY,
			plane_position + MUZZLE_OFFSET, DIR_DOWN, data.projectile)

func _on_died() -> void:
	deactivate()
	destroyed.emit(self)
