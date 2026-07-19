class_name BossController
extends Node3D
## Reusable boss (spec §12): 3D hull, health, multi-phase attack patterns.
## Used for the Choir Harvester mini-boss (1 phase) and the Pale Leviathan final
## boss (several phases). Patterns intensify per phase. Fires through the shared
## BulletManager; killed via its registered BulletTarget.

signal phase_changed(index: int, total: int)
signal health_changed(ratio: float)
signal defeated(world_position: Vector3)

enum Pattern { RADIAL, AIMED_SPREAD, FAN }

@export var display_name: String = "boss"
@export var hull_scene: PackedScene
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
## A boss dies once. Two bullets landing on the same frame both used to reach
## _take_hit with health already at zero, so _defeat() ran twice: the reward was
## paid twice and the docking sequence started twice.
var _defeated: bool = false
var _age: float = 0.0
var _fire_timer: float = 0.0
var _hull: Node3D
var _base_position: Vector2 = Vector2.ZERO
var _combat_age: float = 0.0
## Smoothed roll/pitch of the 3D hull, kept as members. They must NOT be read back
## from `_hull.rotation` each frame: near the 180° facing yaw the euler decomposition
## is ambiguous and the read-back flips, which made the boss blink out for a frame.
var _bank: float = 0.0
var _pitch: float = 0.0
## Where the boss's shots leave its body: one plane-space offset per gun the hull
## carries (Leviathan: central + two pods; Harvester: its two claws). A volley is
## dealt round-robin across them, so it visibly sprays from the guns, not the core.
var _muzzles: Array[Vector2] = [Vector2(0.0, -1.0)]

## Hulls are modelled nose-forward like every unit (ADR-0008); a boss faces the
## player, so the scene turns it around rather than the mesh being built backwards.
const FACING_PLAYER := Vector3(0.0, PI, 0.0)

## Vertical amplitude of the movement shapes, and the band the boss keeps to (it
## never dives onto the player, never leaves the top).
const _AMP_Y := 1.8
const _MIN_Y := 2.5
const _MAX_Y := 9.0
## The 3D hull banks into its turns and pitches into its dives — where depth reads.
const _MAX_BANK_DEG := 30.0
const _MAX_PITCH_DEG := 20.0
const _BANK_REFERENCE := 6.0
const _PITCH_REFERENCE := 5.0

func _ready() -> void:
	_health = max_health
	if hull_scene != null:
		_hull = hull_scene.instantiate() as Node3D
		_hull.rotation = FACING_PLAYER
		add_child(_hull)
		_pad_cull_margin(_hull)
		_muzzles = _read_muzzles()
	position = GameplayPlane.to_world(plane_position)
	set_physics_process(false) # activated on begin()

## A large boss hull can be frustum-culled for a frame while it banks and drifts near
## the top of the view: its computed AABB is tighter than the rotated/animated
## silhouette, so Godot decides it is off-screen and it blinks out. Padding the cull
## margin on every mesh keeps it drawn. (The space backdrop uses the same trick.)
func _pad_cull_margin(node: Node) -> void:
	if node is GeometryInstance3D:
		(node as GeometryInstance3D).extra_cull_margin = 12.0
	for child in node.get_children():
		_pad_cull_margin(child)

## The plane-space offset of every muzzle the hull carries (the Leviathan has a
## central one plus two pods, the Harvester its two claws). Falls back to a single
## nose offset so a hull without muzzles still fires.
func _read_muzzles() -> Array[Vector2]:
	var out: Array[Vector2] = []
	for point_name in ["Muzzle_C", "Muzzle_L", "Muzzle_R"]:
		var node := _hull.get_node_or_null(NodePath(point_name)) as Node3D
		if node != null:
			var world: Vector3 = _hull.transform * node.position
			out.append(Vector2(world.x, -world.z))
	if out.is_empty():
		push_error("[Boss:%s] hull carries no muzzle attach point" % display_name)
		out.append(Vector2(0.0, -1.0))
	return out

func begin(bullet_manager: BulletManager, player: PlayerFighterController) -> void:
	_bullet_manager = bullet_manager
	_player = player
	_defeated = false
	_target = BulletTarget.make(BulletManager.Team.ENEMY, hitbox_radius, Callable(self, "_take_hit"))
	_target.position = plane_position
	_target.enabled = false # invulnerable during entry
	_bullet_manager.register_target(_target)
	_fire_timer = 1.0
	set_physics_process(true)
	phase_changed.emit(_phase, phase_count)
	health_changed.emit(1.0)

func _take_hit(damage: float) -> void:
	if _entering or _defeated:
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
	_defeated = true
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
			_base_position = entry_plane_position
			_combat_age = 0.0
			if _target != null:
				_target.enabled = true
		if _target != null:
			_target.position = plane_position
		return
	# Move in an escalating shape (BossMovement) and bank the 3D hull into it.
	_combat_age += delta
	var previous := plane_position
	var pattern := BossMovement.pattern_for_phase(_phase, phase_count)
	plane_position = BossMovement.position_at(pattern, _combat_age, _base_position,
		drift_amplitude, _AMP_Y, drift_frequency)
	plane_position.y = clampf(plane_position.y, _MIN_Y, _MAX_Y)
	position = GameplayPlane.to_world(plane_position)
	if _target != null:
		_target.position = plane_position
	_apply_bank(previous, delta)
	# Attacks intensify per phase.
	_fire_timer -= delta
	if _fire_timer <= 0.0:
		_fire_timer = fire_interval * (1.0 - 0.12 * _phase)
		_attack()

## Roll from lateral speed, pitch from vertical speed: the hull leans into turns and
## tips into dives, so a boss that used to slide flat now reads in three dimensions.
func _apply_bank(previous: Vector2, delta: float) -> void:
	if _hull == null:
		return
	var velocity := (plane_position - previous) / maxf(delta, 0.0001)
	var target_bank := clampf(-velocity.x / _BANK_REFERENCE, -1.0, 1.0) * deg_to_rad(_MAX_BANK_DEG)
	# Diving toward the player (down, -y) tips the nose down toward them.
	var target_pitch := clampf(-velocity.y / _PITCH_REFERENCE, -1.0, 1.0) * deg_to_rad(_MAX_PITCH_DEG)
	var blend := minf(1.0, delta * 8.0)
	_bank = lerp_angle(_bank, target_bank, blend)
	_pitch = lerp_angle(_pitch, target_pitch, blend)
	_hull.rotation = Vector3(_pitch, PI, _bank)

func _attack() -> void:
	if _bullet_manager == null or projectile == null:
		return
	# Each shot leaves one of the hull's guns (round-robin): same shot counts as
	# before, but the volley visibly sprays from the muzzles rather than the centre.
	var guns := _muzzles.size()
	match (_age_pattern()):
		Pattern.RADIAL:
			var count := 10 + _phase * 4
			for i in count:
				var a := TAU * i / count
				var origin: Vector2 = plane_position + _muzzles[i % guns]
				_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, origin,
					Vector2(cos(a), sin(a)), projectile)
		Pattern.AIMED_SPREAD:
			var count := 3 + _phase
			for i in count:
				var origin: Vector2 = plane_position + _muzzles[i % guns]
				var dir := (_player.plane_position - origin).normalized() if _player != null else Vector2(0.0, -1.0)
				var spread := deg_to_rad(14.0 * (i - (count - 1) * 0.5))
				_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, origin,
					dir.rotated(spread), projectile)
		Pattern.FAN:
			var count := 7 + _phase * 2
			for i in count:
				var origin: Vector2 = plane_position + _muzzles[i % guns]
				var t := float(i) / (count - 1) - 0.5
				_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, origin,
					Vector2(t * 1.4, -1.0).normalized(), projectile)

func _age_pattern() -> Pattern:
	# Cycle patterns over time; more variety at higher phases.
	var patterns := [Pattern.FAN, Pattern.AIMED_SPREAD, Pattern.RADIAL]
	return patterns[int(_age / 2.0) % patterns.size()]

func health_ratio() -> float:
	return _health / max_health
