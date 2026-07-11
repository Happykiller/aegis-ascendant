class_name VfxExplosion
extends Node3D
## Pooled explosion effect (spec §17.2): a bright flash sphere that expands and
## fades + GPU spark burst. Built in code for robustness. Three size categories.
## Emits `finished` so the VFXManager can return it to the pool.

signal finished(effect: VfxExplosion)

enum Category { SMALL, MEDIUM, HEAVY }

const _FLASH_DURATION := 0.28
const _SIZE: Dictionary = {
	Category.SMALL: 0.9,
	Category.MEDIUM: 1.8,
	Category.HEAVY: 3.6,
}
const _TINT: Dictionary = {
	Category.SMALL: Color(1.0, 0.75, 0.45),
	Category.MEDIUM: Color(1.0, 0.6, 0.35),
	Category.HEAVY: Color(1.0, 0.5, 0.3),
}

var _flash: MeshInstance3D
var _flash_material: StandardMaterial3D
var _sparks: GPUParticles3D
var _active: bool = false
var _elapsed: float = 0.0
var _size: float = 1.0

func _ready() -> void:
	_flash = MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.5
	sphere.height = 1.0
	sphere.radial_segments = 12
	sphere.rings = 6
	_flash.mesh = sphere
	_flash.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_flash_material = StandardMaterial3D.new()
	_flash_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_flash_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_flash_material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_flash_material.emission_enabled = true
	_flash.material_override = _flash_material
	add_child(_flash)

	_sparks = GPUParticles3D.new()
	_sparks.one_shot = true
	_sparks.explosiveness = 1.0
	_sparks.amount = 24
	_sparks.lifetime = 0.55
	_sparks.local_coords = false
	_sparks.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_sparks.process_material = _make_spark_process_material()
	_sparks.draw_pass_1 = _make_spark_mesh()
	add_child(_sparks)

	visible = false
	set_process(false)

func _make_spark_process_material() -> ParticleProcessMaterial:
	var mat := ParticleProcessMaterial.new()
	mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	mat.emission_sphere_radius = 0.15
	mat.direction = Vector3(0.0, 0.0, 0.0)
	mat.spread = 180.0
	mat.gravity = Vector3.ZERO
	mat.initial_velocity_min = 5.0
	mat.initial_velocity_max = 12.0
	mat.damping_min = 6.0
	mat.damping_max = 10.0
	mat.scale_min = 0.6
	mat.scale_max = 1.4
	var curve := Curve.new()
	curve.add_point(Vector2(0.0, 1.0))
	curve.add_point(Vector2(1.0, 0.0))
	var scale_tex := CurveTexture.new()
	scale_tex.curve = curve
	mat.scale_curve = scale_tex
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1.0, 0.9, 0.6, 1.0))
	ramp.set_color(1, Color(1.0, 0.35, 0.2, 0.0))
	var ramp_tex := GradientTexture1D.new()
	ramp_tex.gradient = ramp
	mat.color_ramp = ramp_tex
	return mat

func _make_spark_mesh() -> QuadMesh:
	var quad := QuadMesh.new()
	quad.size = Vector2(0.22, 0.22)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	mat.vertex_color_use_as_albedo = true
	mat.emission_enabled = true
	mat.emission_energy_multiplier = 3.0
	quad.material = mat
	return quad

func play(category: Category) -> void:
	_size = _SIZE[category]
	var tint: Color = _TINT[category]
	_flash_material.albedo_color = Color(tint.r, tint.g, tint.b, 1.0)
	_flash_material.emission = tint
	_flash_material.emission_energy_multiplier = 4.0
	_sparks.amount = 16 + int(category) * 14
	_sparks.restart()
	_sparks.emitting = true
	_elapsed = 0.0
	_active = true
	visible = true
	set_process(true)

func _process(delta: float) -> void:
	if not _active:
		return
	_elapsed += delta
	var t := _elapsed / _FLASH_DURATION
	if t >= 1.0:
		_flash.visible = false
		if _elapsed >= _sparks.lifetime:
			_active = false
			visible = false
			set_process(false)
			finished.emit(self)
		return
	_flash.visible = true
	var eased := 1.0 - pow(1.0 - t, 3.0)
	var s := lerpf(0.2, _size, eased)
	_flash.scale = Vector3(s, s, s)
	_flash_material.albedo_color.a = 1.0 - t
	_flash_material.emission_energy_multiplier = 4.0 * (1.0 - t)
