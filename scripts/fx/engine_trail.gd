class_name EngineTrail
## Fabrique de traînée de réacteur — pas un nœud, une fonction qui en construit un.
##
## Le code existait déjà, mais enfermé dans PlayerFighterController._make_engine_trail()
## (scripts/player/player_fighter_controller.gd:293-334). Le réutiliser hors du gameplay
## imposait d'instancier player_fighter.tscn, donc d'embarquer tout le contrôleur de vol
## et son input — pour un vaisseau qui ne fait que poser sur un écran titre.
##
## Sur le modèle de SoftDot et FlameStreak : classe sans état, `static func`, appelable
## de partout sans rien instancier.
##
## Le contrôleur du joueur pourra l'adopter plus tard ; on ne le touche pas ici, c'est
## du code de gameplay et ce n'est pas le sujet.

## Bleu Helios : cœur presque blanc, queue qui vire au bleu profond en s'effaçant.
const HELIOS_HOT := Color(0.6, 0.95, 1.0, 1.0)
const HELIOS_COLD := Color(0.15, 0.5, 0.9, 0.0)

## La poussée part vers +Z, l'arrière d'une coque modelée nez vers -Z.
##
## `scale_factor` et `energy` sont paramétrables parce que les valeurs du gameplay
## (1.0 / 2.5) sont calées sur un vaisseau vu de loin, presque au zénith. Reprises
## telles quelles sur un héros d'écran titre à 3 m de la caméra, les plumes mangeaient
## le quart bas de l'image et bavaient dans le bloom.
static func make(scale_factor: float = 1.0, amount: int = 24, energy: float = 2.5,
		hot: Color = HELIOS_HOT, cold: Color = HELIOS_COLD) -> GPUParticles3D:
	var trail := GPUParticles3D.new()
	trail.amount = amount
	trail.lifetime = 0.32
	# local_coords = false : les particules restent dans le monde, donc la traînée
	# s'étire derrière un vaisseau qui bouge au lieu de le suivre en bloc.
	trail.local_coords = false
	trail.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var mat := ParticleProcessMaterial.new()
	mat.direction = Vector3(0.0, 0.0, 1.0)
	mat.spread = 6.0
	mat.gravity = Vector3.ZERO
	mat.initial_velocity_min = 6.0 * scale_factor
	mat.initial_velocity_max = 9.0 * scale_factor
	mat.scale_min = 0.5 * scale_factor
	mat.scale_max = 1.0 * scale_factor
	var curve := Curve.new()
	curve.add_point(Vector2(0.0, 1.0))
	curve.add_point(Vector2(1.0, 0.0))
	var scale_tex := CurveTexture.new()
	scale_tex.curve = curve
	mat.scale_curve = scale_tex
	var ramp := Gradient.new()
	ramp.set_color(0, hot)
	ramp.set_color(1, cold)
	var ramp_tex := GradientTexture1D.new()
	ramp_tex.gradient = ramp
	mat.color_ramp = ramp_tex
	trail.process_material = mat
	var quad := QuadMesh.new()
	quad.size = Vector2(0.19, 0.42) * scale_factor
	var qmat := StandardMaterial3D.new()
	qmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	qmat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	qmat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	qmat.vertex_color_use_as_albedo = true
	qmat.emission_enabled = true
	qmat.emission_energy_multiplier = energy
	# Sans ce ramp la particule est un quad nu : un carré blanc additif à bord dur.
	qmat.albedo_texture = FlameStreak.texture()
	quad.material = qmat
	trail.draw_pass_1 = quad
	trail.emitting = true
	return trail
