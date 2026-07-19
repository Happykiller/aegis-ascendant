class_name VfxExplosion
extends Node3D
## Pooled explosion effect (spec §17.2): a bright flash sphere that expands and
## fades + GPU spark burst. Built in code for robustness. Three size categories.
## Emits `finished` so the VFXManager can return it to the pool.

signal finished(effect: VfxExplosion)

## IMPACT is the bullet-on-hull hit, not a death: tiny, brief, and tinted by the
## caller (cold white on an enemy hull, shield cyan on ours) so the player can
## tell "I connected" from "I got hit" without reading the HUD.
enum Category { IMPACT, SMALL, MEDIUM, HEAVY }

const _SIZE: Dictionary = {
	Category.IMPACT: 0.5,
	Category.SMALL: 0.9,
	Category.MEDIUM: 1.8,
	Category.HEAVY: 3.6,
}
# Warm, saturated orange bursts (ADR-0009 target: la référence explose en orange
# chaud). IMPACT stays cold — it is the allied hit marker, not a death.
const _TINT: Dictionary = {
	Category.IMPACT: Color(0.85, 0.90, 0.95),
	Category.SMALL: Color(1.0, 0.70, 0.30),
	Category.MEDIUM: Color(1.0, 0.56, 0.22),
	Category.HEAVY: Color(1.0, 0.46, 0.16),
}
const _SPARKS: Dictionary = {
	Category.IMPACT: 8,
	Category.SMALL: 20,
	Category.MEDIUM: 38,
	Category.HEAVY: 54,
}
const _FLASH_DURATION: Dictionary = {
	Category.IMPACT: 0.10,
	Category.SMALL: 0.28,
	Category.MEDIUM: 0.28,
	Category.HEAVY: 0.34,
}
const _SPARK_LIFE: Dictionary = {
	Category.IMPACT: 0.26,
	Category.SMALL: 0.55,
	Category.MEDIUM: 0.55,
	Category.HEAVY: 0.70,
}
## Tumbling hull chunks on a ship death (the reference's "debris burst") — a mere
## bullet IMPACT gets none, so hits and deaths stay distinct.
const _DEBRIS: Dictionary = {
	Category.IMPACT: 0,
	Category.SMALL: 7,
	Category.MEDIUM: 13,
	Category.HEAVY: 22,
}

var _flash: MeshInstance3D
var _flash_material: StandardMaterial3D
var _sparks: GPUParticles3D
var _spark_material: ParticleProcessMaterial
var _debris: GPUParticles3D
var _active: bool = false
var _elapsed: float = 0.0
var _size: float = 1.0
var _flash_time: float = 0.28

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
	_spark_material = _make_spark_process_material()
	_sparks.process_material = _spark_material
	_sparks.draw_pass_1 = _make_spark_mesh()
	add_child(_sparks)

	_debris = GPUParticles3D.new()
	_debris.one_shot = true
	_debris.explosiveness = 1.0
	_debris.amount = 12
	_debris.lifetime = 0.7
	_debris.local_coords = false
	_debris.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_debris.process_material = _make_debris_process_material()
	_debris.draw_pass_1 = _make_debris_mesh()
	add_child(_debris)

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
	# The ramp only shapes brightness and fade; the hue comes from mat.color, set
	# per play(). That keeps a tinted burst allocation-free in the hot path — the
	# alternative, rebuilding the gradient on every hit, would allocate per bullet.
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1.0, 1.0, 1.0, 1.0))
	ramp.set_color(1, Color(0.75, 0.75, 0.75, 0.0))
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
	mat.emission_energy_multiplier = 3.5
	mat.albedo_texture = SoftDot.texture()
	quad.material = mat
	return quad

func _make_debris_process_material() -> ParticleProcessMaterial:
	var mat := ParticleProcessMaterial.new()
	mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	mat.emission_sphere_radius = 0.2
	mat.spread = 180.0
	mat.gravity = Vector3.ZERO
	mat.initial_velocity_min = 3.5
	mat.initial_velocity_max = 9.0
	mat.damping_min = 3.0
	mat.damping_max = 7.0
	mat.angular_velocity_min = -540.0
	mat.angular_velocity_max = 540.0
	mat.scale_min = 0.6
	mat.scale_max = 1.3
	var curve := Curve.new()
	curve.add_point(Vector2(0.0, 1.0))
	curve.add_point(Vector2(0.8, 0.9))
	curve.add_point(Vector2(1.0, 0.0))
	var scale_tex := CurveTexture.new()
	scale_tex.curve = curve
	mat.scale_curve = scale_tex
	# A hot fragment cooling to dark hull metal, then fading out.
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1.0, 0.62, 0.28, 1.0))
	ramp.set_color(1, Color(0.12, 0.12, 0.16, 0.0))
	ramp.add_point(0.35, Color(0.35, 0.30, 0.30, 1.0))
	var ramp_tex := GradientTexture1D.new()
	ramp_tex.gradient = ramp
	mat.color_ramp = ramp_tex
	return mat

func _make_debris_mesh() -> QuadMesh:
	var quad := QuadMesh.new()
	quad.size = Vector2(0.16, 0.16)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.vertex_color_use_as_albedo = true
	quad.material = mat
	return quad

## `tint` overrides the category default (used for impacts, which are coloured by
## whose hull was hit). Leave it transparent to keep the category's own tint.
func play(category: Category, tint: Color = Color.TRANSPARENT) -> void:
	_size = _SIZE[category]
	_flash_time = _FLASH_DURATION[category]
	var colour: Color = tint if tint.a > 0.0 else _TINT[category]
	_flash_material.albedo_color = Color(colour.r, colour.g, colour.b, 1.0)
	_flash_material.emission = colour
	_flash_material.emission_energy_multiplier = 5.0
	_spark_material.color = colour
	_sparks.amount = _SPARKS[category]
	_sparks.lifetime = _SPARK_LIFE[category]
	_sparks.restart()
	_sparks.emitting = true
	var debris_count: int = _DEBRIS[category]
	if debris_count > 0:
		_debris.amount = debris_count
		_debris.lifetime = _SPARK_LIFE[category]
		_debris.restart()
		_debris.emitting = true
	else:
		_debris.emitting = false
	_elapsed = 0.0
	_active = true
	visible = true
	set_process(true)

func _process(delta: float) -> void:
	if not _active:
		return
	_elapsed += delta
	var t := _elapsed / _flash_time
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
	_flash_material.emission_energy_multiplier = 5.0 * (1.0 - t)
