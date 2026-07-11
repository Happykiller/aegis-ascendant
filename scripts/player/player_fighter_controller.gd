class_name PlayerFighterController
extends Node3D
## Player fighter: arcade movement on the logical 2D plane (spec §7.3, §16.2).
## The logical position is authoritative; the 3D node only projects it.
## Visual banking lives on VisualRoot and never affects the hitbox.

## Logical "up the screen" direction (+y logical = -Z world).
const DIR_UP := Vector2(0.0, 1.0)
const MUZZLE_OFFSET := Vector2(0.0, 0.9)

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

var _engine_trail: GPUParticles3D
var _muzzle_flash: MeshInstance3D
var _muzzle_material: StandardMaterial3D
var _muzzle_timer: float = 0.0

@onready var _visual_root: Node3D = $VisualRoot
@onready var _bullet_manager: BulletManager = get_node_or_null(bullet_manager_path) as BulletManager

func _ready() -> void:
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

func _physics_process(delta: float) -> void:
	var input: Vector2
	if _demo:
		_demo_time += delta
		input = Vector2(sin(_demo_time * 0.9) * 0.85, 0.0) # horizontal sweep only
	else:
		input = Input.get_vector("move_left", "move_right", "move_up", "move_down")
	_velocity = integrate_velocity(_velocity, input, stats.max_speed, stats.accel_time, delta)
	plane_position = GameplayPlane.clamp_to_bounds(plane_position + _velocity * delta)
	position = GameplayPlane.to_world(plane_position)
	_apply_visual_bank(delta)
	_update_fire(delta)

func _update_fire(delta: float) -> void:
	_fire_timer = maxf(_fire_timer - delta, 0.0)
	if _muzzle_timer > 0.0:
		_muzzle_timer = maxf(_muzzle_timer - delta, 0.0)
		_muzzle_material.emission_energy_multiplier = 6.0 * (_muzzle_timer / 0.05)
		_muzzle_flash.visible = _muzzle_timer > 0.0
	if _bullet_manager == null or primary_projectile == null:
		return
	if (_demo or Input.is_action_pressed("fire_primary")) and _fire_timer == 0.0:
		_fire_timer = stats.fire_interval
		_bullet_manager.spawn_from_data(BulletManager.Team.PLAYER,
			plane_position + MUZZLE_OFFSET, DIR_UP, primary_projectile)
		_muzzle_timer = 0.05

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
