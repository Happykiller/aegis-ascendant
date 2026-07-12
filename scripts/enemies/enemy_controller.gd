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
## Emitted on each shot (audio cue).
signal fired
## Emitted when the enemy takes a hit without dying (audio cue).
signal hit

@export var data: EnemyData
## Optional wiring for enemies placed directly in a scene (spawners inject
## through setup() instead).
@export var bullet_manager_path: NodePath
@export var auto_activate: bool = false

var active: bool = false
var plane_position: Vector2 = Vector2.ZERO

## Seconds the hull stays lit after taking a hit (spec §17: feedback under 120 ms).
const HIT_FLASH_TIME := 0.09
## Brightness the hull is driven to on impact, before easing back to its rest value.
const FLASH_MODULATE := 4.0
## How hard the hull banks into its weave, in degrees at full lateral speed.
const MAX_BANK_DEG := 26.0

var _bullet_manager: BulletManager
var _target: BulletTarget
var _base_x: float = 0.0
var _age: float = 0.0
var _fire_timer: float = 0.0
var _hit_flash: float = 0.0
## The sprite's rest brightness, read from the scene so the flash eases back to
## whatever the artist set rather than to a hardcoded 1.0.
var _rest_modulate: float = 1.0
var _thruster: GPUParticles3D

@onready var _health: HealthComponent = $HealthComponent
@onready var _visual_root: Node3D = $VisualRoot
## Enemies that draw a sprite can flash and bank; ones that don't just skip it.
@onready var _hull: SpriteBase3D = get_node_or_null("VisualRoot/Hull") as SpriteBase3D

func _ready() -> void:
	assert(data != null, "EnemyController requires an EnemyData resource")
	for error in data.validate():
		push_error("[Enemy:%s] invalid data: %s" % [data.display_name, error])
	add_to_group("enemies")
	_health.died.connect(_on_died)
	_health.damaged.connect(_on_damaged)
	_target = BulletTarget.make(BulletManager.Team.ENEMY, data.hitbox_radius,
		Callable(_health, "apply_damage"))
	_target.enabled = false
	if _hull != null:
		_rest_modulate = _hull.modulate.r
		_build_thruster()
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
	if _thruster != null:
		# Pooled instances are reused: a dormant hull must not keep burning.
		_thruster.emitting = value
	if value and _hull != null:
		_hit_flash = 0.0
		_hull.modulate = Color(_rest_modulate, _rest_modulate, _rest_modulate, 1.0)

func _physics_process(delta: float) -> void:
	_age += delta
	plane_position.y -= data.move_speed * delta
	var weave := _age * data.weave_frequency * TAU
	plane_position.x = _base_x + sin(weave) * data.weave_amplitude
	position = GameplayPlane.to_world(plane_position)
	_target.position = plane_position
	if plane_position.y < GameplayPlane.BOUNDS.position.y - DESPAWN_MARGIN:
		deactivate()
		return
	# Bank into the weave. Lateral speed is the analytic derivative of the sine
	# above, normalised by its own peak, so the roll is exact rather than sampled.
	var lateral := cos(weave) # d/dt sin(weave), normalised: peaks at 1
	_visual_root.rotation.z = deg_to_rad(-MAX_BANK_DEG) * lateral
	_update_hit_flash(delta)
	_update_fire(delta)

## Light the hull for a beat when it is struck. Without this a hit only registers
## in the audio and the health bar — the sprite itself never reacts.
func _update_hit_flash(delta: float) -> void:
	if _hull == null or _hit_flash <= 0.0:
		return
	_hit_flash = maxf(_hit_flash - delta, 0.0)
	var t := _hit_flash / HIT_FLASH_TIME
	var level := lerpf(_rest_modulate, FLASH_MODULATE, t)
	_hull.modulate = Color(level, level, level, 1.0)

func _update_fire(delta: float) -> void:
	if _bullet_manager == null or not GameplayPlane.is_inside(plane_position):
		return
	_fire_timer -= delta
	if _fire_timer <= 0.0:
		_fire_timer = data.fire_interval
		fired.emit()
		_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY,
			plane_position + MUZZLE_OFFSET, DIR_DOWN, data.projectile)

## Exhaust plume, so the hull reads as a thing under power rather than a decal
## sliding down the screen. Built in code, like the player's own trail.
func _build_thruster() -> void:
	_thruster = GPUParticles3D.new()
	_thruster.amount = 14
	_thruster.lifetime = 0.32
	_thruster.local_coords = false
	_thruster.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# The scout dives toward the player (world +Z), so its exhaust trails behind
	# it, up the screen.
	_thruster.position = Vector3(0.0, 0.0, -0.55)
	var mat := ParticleProcessMaterial.new()
	mat.direction = Vector3(0.0, 0.0, -1.0)
	mat.spread = 10.0
	mat.gravity = Vector3.ZERO
	mat.initial_velocity_min = 3.0
	mat.initial_velocity_max = 5.0
	mat.scale_min = 0.35
	mat.scale_max = 0.7
	var curve := Curve.new()
	curve.add_point(Vector2(0.0, 1.0))
	curve.add_point(Vector2(1.0, 0.0))
	var scale_tex := CurveTexture.new()
	scale_tex.curve = curve
	mat.scale_curve = scale_tex
	# Null Choir magenta (palette): the enemy's own signature, never the coral
	# reserved for its bullets nor the cyan reserved for ours.
	var ramp := Gradient.new()
	ramp.set_color(0, Color(0.95, 0.45, 0.85, 1.0))
	ramp.set_color(1, Color(0.55, 0.15, 0.55, 0.0))
	var ramp_tex := GradientTexture1D.new()
	ramp_tex.gradient = ramp
	mat.color_ramp = ramp_tex
	_thruster.process_material = mat
	var quad := QuadMesh.new()
	quad.size = Vector2(0.26, 0.26)
	var qmat := StandardMaterial3D.new()
	qmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	qmat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	qmat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	qmat.vertex_color_use_as_albedo = true
	qmat.emission_enabled = true
	qmat.emission_energy_multiplier = 2.0
	qmat.albedo_texture = SoftDot.texture()
	quad.material = qmat
	_thruster.draw_pass_1 = quad
	add_child(_thruster)

## A non-lethal hit: the killing blow is reported by `destroyed` instead.
func _on_damaged(_amount: float, remaining: float) -> void:
	_hit_flash = HIT_FLASH_TIME
	if remaining > 0.0:
		hit.emit()

func _on_died() -> void:
	deactivate()
	destroyed.emit(self)
