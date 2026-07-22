class_name Beam
extends MeshInstance3D
## Faisceau tendu entre deux points du plan de jeu — et sa ligne de télégraphe.
##
## UN SEUL OBJET, DEUX RÉGIMES : la ligne de visée qui annonce le tir et le faisceau
## qui frappe sont le même nœud, à largeur et énergie différentes. Deux nœuds
## auraient divergé au premier réglage (cf. `comms_trace.gd`).
##
## Le projet n'avait AUCUN rendu de faisceau : la « Lance Helios » n'est qu'une salve
## d'explosions et une secousse (`graybox_root.gd:303`). C'est la première.
##
## Zéro allocation par image : `aim()` ne touche qu'à `transform` (type valeur) et à
## trois uniformes scalaires.

const BeamShader := preload("res://shaders/beam.gdshader")

## Hauteur au-dessus du plan de jeu. Les coques vivent à Y = 0 ; le faisceau est
## additif et n'écrit pas la profondeur, mais le décoller évite qu'il disparaisse
## sous une coque à l'instant où elle le traverse.
const PLANE_LIFT := 0.18

var _material: ShaderMaterial

static func make() -> Beam:
	var beam := Beam.new()
	beam.name = "Beam"
	# Quad unitaire dans le plan XZ : X porte la largeur, Z la longueur. Une taille
	# de 1 rend la mise à l'échelle directe — `scale.x` EST la largeur.
	var quad := PlaneMesh.new()
	quad.size = Vector2.ONE
	quad.orientation = PlaneMesh.FACE_Y
	beam.mesh = quad
	beam._material = ShaderMaterial.new()
	beam._material.shader = BeamShader
	beam.material_override = beam._material
	beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# Un faisceau traverse tout l'écran : sa boîte englobante calculée est celle du
	# quad unitaire, et Godot le culle dès qu'il s'allonge (même piège que les coques
	# de boss, cf. `BossController._pad_cull_margin`).
	beam.extra_cull_margin = 40.0
	beam.visible = false
	return beam

## Tend le faisceau de `from` à `to` (coordonnées du plan de jeu) avec une demi-largeur.
func aim(from: Vector2, to: Vector2, half_width: float) -> void:
	var delta := to - from
	var length := delta.length()
	if length < 0.001:
		visible = false
		return
	var mid := (from + to) * 0.5
	var world_dir := Vector3(delta.x, 0.0, -delta.y) / length
	position = GameplayPlane.to_world(mid) + Vector3(0.0, PLANE_LIFT, 0.0)
	# Rotation autour de Y qui aligne le +Z local sur la direction : une base tournée
	# de θ envoie +Z sur (sin θ, 0, cos θ).
	rotation = Vector3(0.0, atan2(world_dir.x, world_dir.z), 0.0)
	scale = Vector3(half_width * 2.0, 1.0, length)

## `pulse` à 1 fait battre la ligne de télégraphe ; à 0 le faisceau est plein.
func set_regime(energy: float, pulse: float) -> void:
	visible = energy > 0.0
	if _material == null:
		return
	# `&"…"` et non `"…"` : la conversion String -> StringName se referait à chaque
	# image de charge et de tir, pour deux uniformes qui ne changent jamais de nom.
	_material.set_shader_parameter(&"energy", energy)
	_material.set_shader_parameter(&"pulse", pulse)

func extinguish() -> void:
	visible = false

# --- Géométrie ----------------------------------------------------------------

## Le point `probe` (de rayon `probe_radius`) touche-t-il le segment `from`→`to`
## épaissi de `half_width` ?
##
## STATIQUE ET PURE, à dessein : les dégâts du faisceau ne passent par aucune balle,
## donc par aucun test déjà couvert. Sans cette fonction isolée, la seule façon de
## vérifier la portée serait de se placer devant le canon en jeu et d'espérer —
## exactement ce que `pratique-verifier-par-test.md` proscrit.
##
## ⚠️ Le paramètre `t` est BORNÉ à [0, 1] : sans cela, la droite infinie porterait le
## faisceau derrière le canon, et un joueur placé dans le dos de la bouche serait
## touché par un tir qui part dans l'autre sens.
static func hits(from: Vector2, to: Vector2, half_width: float,
		probe: Vector2, probe_radius: float) -> bool:
	var axis := to - from
	var length_squared := axis.length_squared()
	var closest := from
	if length_squared > 0.0001:
		var t := clampf((probe - from).dot(axis) / length_squared, 0.0, 1.0)
		closest = from + axis * t
	var reach := half_width + probe_radius
	return probe.distance_squared_to(closest) <= reach * reach
