class_name SolidsOverlay
extends MeshInstance3D
## Dessine la REPRÉSENTATION PHYSIQUE par-dessus l'image : chaque forme de collision du
## plan, et la capsule du chasseur. Drapeau `--show-solids`.
##
## ⚠️ IL EXISTE PARCE QU'ON A RAISONNÉ TROP LONGTEMPS SANS LE VOIR. « Est-ce que tu peux
## faire apparaître la représentation dans l'espace des points de collision, pour qu'on
## puisse voir visuellement pourquoi il y a cette différence » (opérateur, 2026-08-28).
## Un décor et sa collision sont deux objets distincts dans ce projet ; quand ils
## divergent, aucun chiffre ne le dit aussi vite qu'une superposition.
##
## Vert : ce qui arrête. Cyan : le corps du chasseur tel que la collision le voit.
## Tout est redessiné à chaque image dans un `ImmediateMesh` — c'est un instrument de
## debug, pas un rendu de jeu, et il ne tourne que sous drapeau.

const LIFT := 0.35
const SEGMENTS_PER_ARC := 24

var _mesh: ImmediateMesh

func _ready() -> void:
	_mesh = ImmediateMesh.new()
	mesh = _mesh
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.vertex_color_use_as_albedo = true
	material.no_depth_test = true
	material.render_priority = 100
	material_override = material

func draw(shapes: PlaneShapes, lift: float, player: Vector2, forward: Vector2,
		half_length: float, radius: float) -> void:
	_mesh.clear_surfaces()
	_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
	var green := Color(0.2, 1.0, 0.3)
	for i in shapes.size():
		match shapes.kind_at(i):
			PlaneShapes.Kind.DISC:
				_circle(shapes.centre_of(i), shapes.param(i, 2), lift, green)
			PlaneShapes.Kind.RING_ARC:
				var c := shapes.centre_of(i)
				var r := shapes.param(i, 2)
				var th := shapes.param(i, 3)
				var a0 := shapes.param(i, 4)
				var span := shapes.param(i, 5)
				_arc(c, r - th * 0.5, a0, span, lift, green)
				_arc(c, r + th * 0.5, a0, span, lift, green)
				for edge in [a0, a0 + span]:
					var d := Vector2(cos(deg_to_rad(edge)), sin(deg_to_rad(edge)))
					_line(c + d * (r - th * 0.5), c + d * (r + th * 0.5), lift, green)
			PlaneShapes.Kind.CAPSULE:
				var a := shapes.centre_of(i)
				var b := Vector2(shapes.param(i, 2), shapes.param(i, 3))
				_capsule(a, b, shapes.param(i, 4), lift, green)
	var axis := forward.normalized() * half_length
	_capsule(player - axis, player + axis, radius, lift, Color(0.3, 0.95, 1.0))
	_mesh.surface_end()

func _line(a: Vector2, b: Vector2, lift: float, colour: Color) -> void:
	_mesh.surface_set_color(colour)
	_mesh.surface_add_vertex(GameplayPlane.to_world(a) + Vector3(0.0, lift + LIFT, 0.0))
	_mesh.surface_set_color(colour)
	_mesh.surface_add_vertex(GameplayPlane.to_world(b) + Vector3(0.0, lift + LIFT, 0.0))

func _arc(c: Vector2, r: float, a0: float, span: float, lift: float, colour: Color) -> void:
	var prev := c + Vector2(cos(deg_to_rad(a0)), sin(deg_to_rad(a0))) * r
	for k in range(1, SEGMENTS_PER_ARC + 1):
		var a := deg_to_rad(a0 + span * float(k) / float(SEGMENTS_PER_ARC))
		var p := c + Vector2(cos(a), sin(a)) * r
		_line(prev, p, lift, colour)
		prev = p

func _circle(c: Vector2, r: float, lift: float, colour: Color) -> void:
	_arc(c, r, 0.0, 360.0, lift, colour)

func _capsule(a: Vector2, b: Vector2, r: float, lift: float, colour: Color) -> void:
	var d := (b - a).normalized() if a.distance_to(b) > 0.0001 else Vector2(0.0, 1.0)
	var n := Vector2(-d.y, d.x) * r
	_line(a + n, b + n, lift, colour)
	_line(a - n, b - n, lift, colour)
	var base := rad_to_deg(d.angle())
	_arc(b, r, base - 90.0, 180.0, lift, colour)
	_arc(a, r, base + 90.0, 180.0, lift, colour)
