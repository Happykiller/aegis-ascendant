class_name PlayerFighterController
extends Node3D
## Player fighter: arcade movement on the logical 2D plane (spec §7.3, §16.2).
## The logical position is authoritative; the 3D node only projects it.
## Visual banking lives on VisualRoot and never affects the hitbox.

## Logical "up the screen" direction (+y logical = -Z world).
const DIR_UP := Vector2(0.0, 1.0)
const MUZZLE_OFFSET := Vector2(0.0, 0.9)

## Emitted whenever the shield value changes (HUD).
signal shield_changed(ratio: float, current: float, maximum: float)
## Emitted when a life is lost; `lives` is the remaining count.
signal lives_changed(lives: int)
## Emitted when the player is hit (feedback: shake / sfx), with the world position.
signal hit_taken(world_position: Vector3)
## Emitted when a life is lost (explosion at position).
signal destroyed_at(world_position: Vector3)
## Emitted when the last life is gone (game over).
signal game_over
## Emitted when the fire power level changes (HUD / feedback).
signal power_changed(level: int)
## Emitted once per salvo, whatever the power level (audio cue).
signal fired

const MAX_POWER := 5

@export var stats: PlayerStats
@export var primary_projectile: ProjectileData
@export var bullet_manager_path: NodePath

var plane_position: Vector2 = Vector2(0.0, -5.0)
var _velocity: Vector2 = Vector2.ZERO
var _fire_timer: float = 0.0
## Demo/attract mode (cmdline `--demo`): auto-fire + gentle strafe, for captures
## and hands-off showcase. Never active in a normal run.
var _demo: bool = false
var _demo_time: float = 0.0
## Autopilot (docking, spec §6.5): control is taken over and the ship flies to a
## target on the plane; firing is suspended. Emits `autopilot_reached` on arrival.
var _autopilot: bool = false
var _autopilot_target: Vector2 = Vector2.ZERO
signal autopilot_reached

var _shield: PlayerShield = PlayerShield.new()
var _lives: int = 3
var _power_level: int = 1
var _alive: bool = true
var _respawn_timer: float = 0.0
var _target: BulletTarget
var _blink_time: float = 0.0

var _engine_trail: GPUParticles3D
var _muzzle_flash: MeshInstance3D
var _muzzle_material: StandardMaterial3D
var _muzzle_timer: float = 0.0

@onready var _visual_root: Node3D = $VisualRoot
@onready var _hull: Node3D = $VisualRoot/Hull
@onready var _bullet_manager: BulletManager = get_node_or_null(bullet_manager_path) as BulletManager

func _ready() -> void:
	# Lay the top-down ship sprite flat on the play plane, nose toward screen-up
	# (local +Y -> world -Z), facing the camera (local +Z -> world +Y).
	_hull.rotation = Vector3(deg_to_rad(-90.0), 0.0, 0.0)
	assert(stats != null, "PlayerFighterController requires a PlayerStats resource")
	for error in stats.validate():
		push_error("[PlayerFighter] invalid stats: %s" % error)
	if primary_projectile != null:
		for error in primary_projectile.validate():
			push_error("[PlayerFighter] invalid projectile: %s" % error)
	position = GameplayPlane.to_world(plane_position)
	_build_engine_trail()
	_build_muzzle_flash()
	_demo = "--demo" in OS.get_cmdline_user_args()
	_shield.configure(stats.shield_max, stats.shield_regen_delay,
		stats.shield_regen_rate, stats.invuln_time)
	_lives = stats.lives
	if _bullet_manager != null:
		_target = BulletTarget.make(BulletManager.Team.PLAYER, stats.hitbox_radius,
			Callable(self, "_take_hit"))
		_target.position = plane_position
		_bullet_manager.register_target(_target)
	# Publish initial HUD state on the next idle frame (listeners connect after _ready).
	call_deferred("_emit_initial_state")

func _emit_initial_state() -> void:
	shield_changed.emit(_shield.ratio(), _shield.current, _shield.maximum)
	lives_changed.emit(_lives)
	power_changed.emit(_power_level)

func _physics_process(delta: float) -> void:
	if not _alive:
		_respawn_timer -= delta
		if _respawn_timer <= 0.0:
			_respawn()
		return
	if _autopilot:
		_shield.grant_invulnerability(0.3) # safe during the guided approach
		plane_position = plane_position.move_toward(_autopilot_target, stats.max_speed * 0.6 * delta)
		position = GameplayPlane.to_world(plane_position)
		if _target != null:
			_target.position = plane_position
		if plane_position.distance_to(_autopilot_target) < 0.1:
			_autopilot = false
			autopilot_reached.emit()
		return
	_shield.tick(delta)
	shield_changed.emit(_shield.ratio(), _shield.current, _shield.maximum)
	_update_invuln_blink(delta)
	var input: Vector2
	if _demo:
		_demo_time += delta
		input = Vector2(sin(_demo_time * 0.9) * 0.85, 0.0) # horizontal sweep only
	else:
		input = GameplayPlane.from_input(
			Input.get_vector("move_left", "move_right", "move_up", "move_down"))
	_velocity = integrate_velocity(_velocity, input, stats.max_speed, stats.accel_time, delta)
	plane_position = GameplayPlane.clamp_to_bounds(plane_position + _velocity * delta)
	position = GameplayPlane.to_world(plane_position)
	if _target != null:
		_target.position = plane_position
	_apply_visual_bank(delta)
	_update_fire(delta)

## Bullet hit callback (registered with the BulletManager).
func _take_hit(damage: float) -> void:
	if not _alive:
		return
	if _shield.take_hit(damage):
		hit_taken.emit(global_position)
		shield_changed.emit(_shield.ratio(), _shield.current, _shield.maximum)
		if _shield.is_depleted():
			_destroy()

func _destroy() -> void:
	_alive = false
	_visual_root.visible = false
	if _target != null:
		_target.enabled = false
	destroyed_at.emit(global_position)
	_lives -= 1
	lives_changed.emit(_lives)
	if _lives <= 0:
		game_over.emit()
	else:
		_respawn_timer = 1.2 # brief pause before respawn (spec §5.3: forgiving)

func _respawn() -> void:
	_alive = true
	plane_position = Vector2(0.0, -5.0)
	_velocity = Vector2.ZERO
	position = GameplayPlane.to_world(plane_position)
	_visual_root.visible = true
	_shield.reset()
	_shield.grant_invulnerability(2.0)
	if _target != null:
		_target.position = plane_position
		_target.enabled = true
	shield_changed.emit(_shield.ratio(), _shield.current, _shield.maximum)

func _update_invuln_blink(delta: float) -> void:
	if _shield.is_invulnerable():
		_blink_time += delta * 18.0
		_visual_root.visible = fmod(_blink_time, 1.0) < 0.55
	elif not _visual_root.visible:
		_visual_root.visible = true

## Raise the primary fire power level (Power Core pickup, spec §9.1).
func add_power() -> void:
	if _power_level < MAX_POWER:
		_power_level += 1
		power_changed.emit(_power_level)

func restore_shield(amount: float) -> void:
	_shield.restore(amount)
	shield_changed.emit(_shield.ratio(), _shield.current, _shield.maximum)

## Take over control and fly to a target on the plane (docking, spec §6.5).
func begin_autopilot(target: Vector2) -> void:
	_autopilot = true
	_autopilot_target = target
	_visual_root.visible = true

## Hide the fighter (after docking, when the player becomes the fortress).
func stow() -> void:
	_autopilot = false
	visible = false
	set_physics_process(false)
	if _target != null:
		_target.enabled = false

## Unlimited continues for the demo (spec §8.4): restore lives and respawn.
func continue_run() -> void:
	_lives = stats.lives
	lives_changed.emit(_lives)
	_respawn()

func _update_fire(delta: float) -> void:
	_fire_timer = maxf(_fire_timer - delta, 0.0)
	if _muzzle_timer > 0.0:
		_muzzle_timer = maxf(_muzzle_timer - delta, 0.0)
		_muzzle_material.emission_energy_multiplier = 6.0 * (_muzzle_timer / 0.05)
		_muzzle_flash.visible = _muzzle_timer > 0.0
	if _bullet_manager == null or primary_projectile == null:
		return
	if (_demo or Input.is_action_pressed("fire_primary")) and _fire_timer == 0.0:
		# Higher power tightens cadence (spec §9.1 level 2 = increased rate).
		var cadence := stats.fire_interval * (1.0 if _power_level < 2 else 0.8)
		_fire_timer = cadence
		_fire_pattern()
		_muzzle_timer = 0.05

## Pulse Array fire pattern, escalating with power level (spec §9.1).
func _fire_pattern() -> void:
	fired.emit()
	var muzzle := plane_position + MUZZLE_OFFSET
	# Level 1+: twin frontal shots.
	_shoot(muzzle + Vector2(-0.18, 0.0), DIR_UP)
	_shoot(muzzle + Vector2(0.18, 0.0), DIR_UP)
	if _power_level >= 3:
		# Level 3+: weak angled side shots.
		_shoot(muzzle + Vector2(-0.5, 0.0), Vector2(-0.28, 1.0))
		_shoot(muzzle + Vector2(0.5, 0.0), Vector2(0.28, 1.0))
	if _power_level >= 4:
		# Level 4+: reinforced central axis.
		_shoot(muzzle, DIR_UP)
	if _power_level >= 5:
		# Level 5: full lateral spread.
		_shoot(muzzle + Vector2(-0.7, 0.0), Vector2(-0.6, 1.0))
		_shoot(muzzle + Vector2(0.7, 0.0), Vector2(0.6, 1.0))

func _shoot(origin: Vector2, direction: Vector2) -> void:
	_bullet_manager.spawn_from_data(BulletManager.Team.PLAYER, origin, direction, primary_projectile)

func _build_engine_trail() -> void:
	_engine_trail = GPUParticles3D.new()
	_engine_trail.amount = 40
	_engine_trail.lifetime = 0.45
	_engine_trail.local_coords = false
	_engine_trail.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_engine_trail.position = Vector3(0.0, 0.0, 0.9) # behind the ship (world +Z)
	var mat := ParticleProcessMaterial.new()
	mat.direction = Vector3(0.0, 0.0, 1.0)
	mat.spread = 8.0
	mat.gravity = Vector3.ZERO
	mat.initial_velocity_min = 6.0
	mat.initial_velocity_max = 9.0
	mat.scale_min = 0.5
	mat.scale_max = 1.0
	var curve := Curve.new()
	curve.add_point(Vector2(0.0, 1.0))
	curve.add_point(Vector2(1.0, 0.0))
	var scale_tex := CurveTexture.new()
	scale_tex.curve = curve
	mat.scale_curve = scale_tex
	var ramp := Gradient.new()
	ramp.set_color(0, Color(0.6, 0.95, 1.0, 1.0))
	ramp.set_color(1, Color(0.15, 0.5, 0.9, 0.0))
	var ramp_tex := GradientTexture1D.new()
	ramp_tex.gradient = ramp
	mat.color_ramp = ramp_tex
	_engine_trail.process_material = mat
	var quad := QuadMesh.new()
	quad.size = Vector2(0.35, 0.35)
	var qmat := StandardMaterial3D.new()
	qmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	qmat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	qmat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	qmat.vertex_color_use_as_albedo = true
	qmat.emission_enabled = true
	qmat.emission_energy_multiplier = 2.5
	qmat.albedo_texture = SoftDot.texture()
	quad.material = qmat
	_engine_trail.draw_pass_1 = quad
	_engine_trail.emitting = true
	add_child(_engine_trail)

func _build_muzzle_flash() -> void:
	_muzzle_flash = MeshInstance3D.new()
	var quad := QuadMesh.new()
	quad.size = Vector2(0.7, 0.7)
	_muzzle_flash.mesh = quad
	_muzzle_flash.position = Vector3(0.0, 0.0, -0.9) # nose (world -Z = up screen)
	_muzzle_flash.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_muzzle_material = StandardMaterial3D.new()
	_muzzle_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_muzzle_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_muzzle_material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_muzzle_material.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	_muzzle_material.emission_enabled = true
	_muzzle_material.albedo_color = Color(0.6, 0.95, 1.0, 1.0)
	_muzzle_material.emission = Color(0.5, 0.9, 1.0)
	_muzzle_material.albedo_texture = SoftDot.texture()
	_muzzle_flash.material_override = _muzzle_material
	_muzzle_flash.visible = false
	add_child(_muzzle_flash)

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
