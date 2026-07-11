class_name BossController
extends Node3D
## Reusable boss (spec §12): sprite body, health, multi-phase attack patterns.
## Used for the Choir Harvester mini-boss (1 phase) and the Pale Leviathan final
## boss (several phases). Patterns intensify per phase. Fires through the shared
## BulletManager; killed via its registered BulletTarget.

signal phase_changed(index: int, total: int)
signal health_changed(ratio: float)
signal defeated(world_position: Vector3)

enum Pattern { RADIAL, AIMED_SPREAD, FAN }

@export var display_name: String = "boss"
@export var sprite_texture: Texture2D
@export var sprite_pixel_size: float = 0.008
@export var max_health: float = 600.0
@export var hitbox_radius: float = 2.2
@export var phase_count: int = 1
@export var entry_plane_position: Vector2 = Vector2(0.0, 4.0)
@export var drift_amplitude: float = 6.0
@export var drift_frequency: float = 0.25
@export var fire_interval: float = 1.4
@export var projectile: ProjectileData
@export var bullet_manager_path: NodePath

var plane_position: Vector2 = Vector2(0.0, 10.0)
var _bullet_manager: BulletManager
var _player: PlayerFighterController
var _target: BulletTarget
var _health: float
var _phase: int = 0
var _entering: bool = true
var _age: float = 0.0
var _fire_timer: float = 0.0
var _sprite: Sprite3D
var _base_x: float = 0.0

func _ready() -> void:
	_health = max_health
	_sprite = Sprite3D.new()
	_sprite.texture = sprite_texture
	_sprite.pixel_size = sprite_pixel_size
	_sprite.shaded = false
	_sprite.double_sided = true
	_sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	_sprite.rotation = Vector3(deg_to_rad(-90.0), 0.0, 0.0)
	add_child(_sprite)
	position = GameplayPlane.to_world(plane_position)
	set_physics_process(false) # activated on begin()

func begin(bullet_manager: BulletManager, player: PlayerFighterController) -> void:
	_bullet_manager = bullet_manager
	_player = player
	_target = BulletTarget.make(BulletManager.Team.ENEMY, hitbox_radius, Callable(self, "_take_hit"))
	_target.position = plane_position
	_target.enabled = false # invulnerable during entry
	_bullet_manager.register_target(_target)
	_fire_timer = 1.0
	set_physics_process(true)
	phase_changed.emit(_phase, phase_count)
	health_changed.emit(1.0)

func _take_hit(damage: float) -> void:
	if _entering:
		return
	_health = maxf(_health - damage, 0.0)
	health_changed.emit(_health / max_health)
	# Advance phase at even health thresholds.
	var next_phase := int((1.0 - _health / max_health) * phase_count)
	if next_phase > _phase and next_phase < phase_count:
		_phase = next_phase
		phase_changed.emit(_phase, phase_count)
	if _health <= 0.0:
		_defeat()

func _defeat() -> void:
	set_physics_process(false)
	if _target != null:
		_target.enabled = false
		_bullet_manager.unregister_target(_target)
	defeated.emit(global_position)

func _physics_process(delta: float) -> void:
	_age += delta
	if _entering:
		plane_position = plane_position.move_toward(entry_plane_position, 5.0 * delta)
		position = GameplayPlane.to_world(plane_position)
		if plane_position.distance_to(entry_plane_position) < 0.05:
			_entering = false
			_base_x = entry_plane_position.x
			if _target != null:
				_target.enabled = true
		if _target != null:
			_target.position = plane_position
		return
	# Horizontal drift.
	plane_position.x = _base_x + sin(_age * drift_frequency * TAU) * drift_amplitude
	position = GameplayPlane.to_world(plane_position)
	if _target != null:
		_target.position = plane_position
	# Attacks intensify per phase.
	_fire_timer -= delta
	if _fire_timer <= 0.0:
		_fire_timer = fire_interval * (1.0 - 0.12 * _phase)
		_attack()

func _attack() -> void:
	if _bullet_manager == null or projectile == null:
		return
	var muzzle := plane_position + Vector2(0.0, -1.0)
	match (_age_pattern()):
		Pattern.RADIAL:
			var count := 10 + _phase * 4
			for i in count:
				var a := TAU * i / count
				_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, muzzle,
					Vector2(cos(a), sin(a)), projectile)
		Pattern.AIMED_SPREAD:
			var dir := (_player.plane_position - muzzle).normalized() if _player != null else Vector2(0.0, -1.0)
			var count := 3 + _phase
			for i in count:
				var spread := deg_to_rad(14.0 * (i - (count - 1) * 0.5))
				_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, muzzle,
					dir.rotated(spread), projectile)
		Pattern.FAN:
			var count := 7 + _phase * 2
			for i in count:
				var t := float(i) / (count - 1) - 0.5
				_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, muzzle,
					Vector2(t * 1.4, -1.0).normalized(), projectile)

func _age_pattern() -> Pattern:
	# Cycle patterns over time; more variety at higher phases.
	var patterns := [Pattern.FAN, Pattern.AIMED_SPREAD, Pattern.RADIAL]
	return patterns[int(_age / 2.0) % patterns.size()]

func health_ratio() -> float:
	return _health / max_health
