class_name EngineTrail
## Fabrique de BRAISES RÉSIDUELLES — pas un nœud, une fonction qui en construit un.
##
## ⚠️ CE N'EST PLUS LE MOTEUR. Depuis ADR-0017, le réacteur est rendu par `EnginePlume`
## (un cône de gaz solidaire de la coque, avec ses disques de Mach). Ces particules-ci
## ne racontent plus qu'UNE chose, et la racontent bien : les braises laissées DANS LE
## MONDE par une coque qui se déplace. C'est tout ce que la plume, rigide, ne peut pas
## dire — sans elles, une embardée latérale ne laisse aucune trace de vitesse.
##
## D'où le réglage réduit : peu de particules, courtes, fines. Remontées à leurs valeurs
## d'avant (24 particules, quads de 0,19 × 0,42), elles reprennent le dessus sur la
## plume et on retrouve le chapelet de petits nuages qu'ADR-0017 a écarté.
##
## Sur le modèle de SoftDot et FlameStreak : classe sans état, `static func`, appelable
## de partout sans rien instancier.

## Bleu Helios : cœur presque blanc, queue qui vire au bleu profond en s'effaçant.
const HELIOS_HOT := Color(0.6, 0.95, 1.0, 1.0)
const HELIOS_COLD := Color(0.15, 0.5, 0.9, 0.0)

## La poussée part vers +Z, l'arrière d'une coque modelée nez vers -Z.
##
## `scale_factor` et `energy` sont paramétrables parce que les valeurs du gameplay
## (1.0 / 2.5) sont calées sur un vaisseau vu de loin, presque au zénith. Reprises
## telles quelles sur un héros d'écran titre à 3 m de la caméra, les plumes mangeaient
## le quart bas de l'image et bavaient dans le bloom.
static func make(scale_factor: float = 1.0, amount: int = 8, energy: float = 1.6,
		hot: Color = HELIOS_HOT, cold: Color = HELIOS_COLD) -> GPUParticles3D:
	var trail := GPUParticles3D.new()
	trail.amount = amount
	trail.lifetime = 0.22
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
	mat.scale_min = 0.25 * scale_factor
	mat.scale_max = 0.55 * scale_factor
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
	quad.size = Vector2(0.10, 0.24) * scale_factor
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
