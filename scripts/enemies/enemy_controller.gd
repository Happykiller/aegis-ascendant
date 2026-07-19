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
## Marge de sortie par le HAUT : au-delà, un ennemi qui bat en retraite est perdu.
const ESCAPE_MARGIN := 3.0

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
## Peak opacity of the additive white wash laid over the hull on impact.
const FLASH_STRENGTH := 0.85
## How hard the hull banks into its weave, in degrees at full lateral speed.
const MAX_BANK_DEG := 26.0

var _bullet_manager: BulletManager
var _target: BulletTarget
## Point de spawn : les trajectoires sont des fonctions de l'âge ET de ce point.
var _spawn: Vector2 = Vector2.ZERO
var _age: float = 0.0
var _fire_timer: float = 0.0
var _hit_flash: float = 0.0
var _thruster: GPUParticles3D
## Additive wash laid over the hull mesh on impact. A mesh has no `modulate`, so
## the flash is an overlay pass rather than a tint.
var _flash_material: StandardMaterial3D
## Distance from the enemy's origin to its gun, read from the hull.
var _muzzle_offset: Vector2 = MUZZLE_OFFSET

@onready var _health: HealthComponent = $HealthComponent
@onready var _visual_root: Node3D = $VisualRoot
## Enemies that carry a hull can flash and bank; ones that don't just skip it.
@onready var _hull: Node3D = get_node_or_null("VisualRoot/Hull") as Node3D

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
		var muzzle := _attach_point("Muzzle_C")
		_muzzle_offset = Vector2(muzzle.x, -muzzle.z)
		_build_flash_overlay()
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
	_spawn = spawn_plane_position
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
	if value and _flash_material != null:
		_hit_flash = 0.0
		_flash_material.albedo_color.a = 0.0

func _physics_process(delta: float) -> void:
	_age += delta
	var previous_x := plane_position.x
	# La trajectoire est une fonction pure de l'âge (EnemyPath) : le contrôleur
	# l'échantillonne, il ne décide de rien. Ajouter un comportement, c'est ajouter
	# une trajectoire là-bas et la choisir dans la Resource — pas toucher ici.
	plane_position = EnemyPath.position_at(data, _age, _spawn)
	position = GameplayPlane.to_world(plane_position)
	_target.position = plane_position
	# Sortie par le bas OU par le haut : le BOOMERANG s'échappe en remontant, et sans
	# cette seconde borne il resterait vivant à jamais, hors du champ, à consommer une
	# entrée du pool.
	if plane_position.y < GameplayPlane.BOUNDS.position.y - DESPAWN_MARGIN \
			or plane_position.y > GameplayPlane.BOUNDS.end.y + ESCAPE_MARGIN \
			or absf(plane_position.x) > GameplayPlane.BOUNDS.end.x + DESPAWN_MARGIN:
		deactivate()
		return
	# Le roulis se déduit du déplacement latéral RÉELLEMENT parcouru, pas de la
	# dérivée d'une sinusoïde : il vaut donc pour toutes les trajectoires, y compris
	# celles qu'on ajoutera.
	var lateral_speed := (plane_position.x - previous_x) / maxf(delta, 0.0001)
	var bank := clampf(lateral_speed / EnemyPath.BANK_REFERENCE_SPEED, -1.0, 1.0)
	_visual_root.rotation.z = deg_to_rad(-MAX_BANK_DEG) * bank
	_update_hit_flash(delta)
	_update_fire(delta)

## Local position of an attach point baked into the hull mesh (ADR-0008),
## expressed in VisualRoot space so the hull's own yaw is accounted for.
func _attach_point(point_name: String) -> Vector3:
	if _hull == null:
		return Vector3.ZERO
	var node := _hull.get_node_or_null(NodePath(point_name)) as Node3D
	if node == null:
		push_error("[Enemy:%s] hull has no attach point '%s'" % [data.display_name, point_name])
		return Vector3.ZERO
	return _hull.transform * node.position

## A mesh has no `modulate`, so the impact flash is an additive overlay pass over
## the whole hull rather than a tint on a sprite.
func _build_flash_overlay() -> void:
	var mesh := _find_mesh(_hull)
	if mesh == null:
		return
	_flash_material = StandardMaterial3D.new()
	_flash_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_flash_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_flash_material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_flash_material.albedo_color = Color(1.0, 1.0, 1.0, 0.0)
	mesh.material_overlay = _flash_material

static func _find_mesh(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D:
		return node as MeshInstance3D
	for child in node.get_children():
		var found := _find_mesh(child)
		if found != null:
			return found
	return null

## Light the hull for a beat when it is struck. Without this a hit only registers
## in the audio and the health bar — the hull itself never reacts.
func _update_hit_flash(delta: float) -> void:
	if _flash_material == null or _hit_flash <= 0.0:
		return
	_hit_flash = maxf(_hit_flash - delta, 0.0)
	_flash_material.albedo_color.a = FLASH_STRENGTH * (_hit_flash / HIT_FLASH_TIME)

func _update_fire(delta: float) -> void:
	if _bullet_manager == null or not GameplayPlane.is_inside(plane_position):
		return
	_fire_timer -= delta
	if _fire_timer <= 0.0:
		_fire_timer = data.fire_interval
		fired.emit()
		_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY,
			plane_position + _muzzle_offset, DIR_DOWN, data.projectile)

## Exhaust plume, so the hull reads as a thing under power rather than a decal
## sliding down the screen. Built in code, like the player's own trail.
func _build_thruster() -> void:
	_thruster = GPUParticles3D.new()
	_thruster.amount = 14
	_thruster.lifetime = 0.24
	_thruster.local_coords = false
	_thruster.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# The scout dives toward the player (world +Z), so its exhaust trails behind
	# it, up the screen — from the nozzle the hull actually carries.
	_thruster.position = _attach_point("Engine_C")
	var mat := ParticleProcessMaterial.new()
	mat.direction = Vector3(0.0, 0.0, -1.0)
	mat.spread = 7.0
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
	quad.size = Vector2(0.16, 0.36)
	var qmat := StandardMaterial3D.new()
	qmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	qmat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	qmat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	qmat.vertex_color_use_as_albedo = true
	qmat.emission_enabled = true
	qmat.emission_energy_multiplier = 2.0
	qmat.albedo_texture = FlameStreak.texture()
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
