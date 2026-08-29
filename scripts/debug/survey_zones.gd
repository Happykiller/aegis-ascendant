class_name SurveyZones
extends MeshInstance3D
## Les zones du survol que `SolidsOverlay` ne peut pas connaître : les FENÊTRES DE TIR.
##
## ⚠️ IL EXISTE PARCE QUE LA MOITIÉ DES RÈGLES DE CE NIVEAU SONT INVISIBLES. `SolidsOverlay`
## montre bien les cibles enregistrées — un cercle par tourelle, par pont, par nœud —, mais il
## ne montre que celles qui sont DÉJÀ armées. Or tout l'équilibrage du survol tient dans un
## seuil qu'on ne voit nulle part : une pièce n'est tirable que pendant la fenêtre où elle est
## à l'écran, et cette fenêtre n'est pas la même pour les trois. Sans ces bandes, la seule
## façon de savoir pourquoi un tir n'a rien fait est de relire `cortege_tuning.gd`.
##
## ⚠️ ET DEUX SEUILS DE CE NIVEAU SE CONTREDISENT EN APPARENCE, ce qui est exactement ce qu'un
## instrument doit rendre lisible : un pont est TIRABLE bien avant d'être au-dessus du terrain,
## mais il ne LÂCHE qu'une fois dessus — une coque née plus haut serait détruite à sa première
## trame par le despawn de `EnemyController`. Deux bandes différentes, donc, et c'est voulu.
##
## Tout est redessiné à chaque image dans un `ImmediateMesh`, comme `SolidsOverlay` : c'est un
## instrument de debug, pas un rendu de jeu, et il ne tourne que quand on l'allume.

## Au-dessus du plan de vol, pour passer devant les coques sans se battre avec elles.
const LIFT := 0.40

## Une bande par famille de cible, avec sa couleur.
##
## ⚠️ LES COULEURS SONT CELLES DES PIÈCES, pas des couleurs de debug arbitraires. La tourelle
## est rouge comme son faisceau, le pont magenta comme son puits, le nœud violet comme son
## bulbe. Un instrument qui invente ses propres codes oblige à traduire, et on se trompe.
const TURRET_TINT := Color(0.90, 0.28, 0.24)
const BAY_TINT := Color(0.85, 0.24, 0.61)
const NODE_TINT := Color(0.48, 0.30, 0.91)
## La bande de LÂCHER d'un pont — celle du plan de vol. Plus pâle : c'est une borne du terrain,
## pas une propriété de la pièce.
const RELEASE_TINT := Color(0.95, 0.72, 0.35)

## Longueur d'un tiret et de son vide. ⚠️ EN TIRETS ET NON EN TRAIT PLEIN : une ligne pleine en
## travers du plan de jeu se lit comme un mur ou comme un tir, et sur un niveau où le joueur
## cherche justement des faisceaux, c'est le pire malentendu possible.
const DASH := 0.9
const GAP := 0.6

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
	# Un instrument ne doit jamais être coupé par le culling : ses lignes traversent tout le
	# plan de jeu alors que sa boîte englobante est calculée sur un maillage vide au montage.
	extra_cull_margin = 60.0

## Ce qu'une pièce PAS ENCORE ARMÉE vaut à l'écran, et ce qu'une pièce morte y vaut.
##
## ⚠️ ELLES N'APPARAISSENT NULLE PART AILLEURS, ET C'EST LE TROU QUE CET INSTRUMENT COMBLE.
## `SolidsOverlay` dessine les cibles enregistrées auprès du gestionnaire de balles — donc
## uniquement celles qui sont DÉJÀ dans leur fenêtre. Une tourelle qui approche n'est pas
## enregistrée, une tourelle passée s'est désenregistrée : dans les deux cas, rien à l'écran, et
## la question « pourquoi mon tir ne fait-il rien ? » n'a pas de réponse visible. C'est
## exactement celle qu'on se pose sur ce niveau.
const PENDING_ALPHA := 0.45

## Dessine les fenêtres, et les pièces que le gestionnaire de balles ne montre pas.
## `on` à faux vide le maillage et ne coûte plus rien.
func draw(tuning: CortegeTuning, on: bool,
		hardpoints: CortegeHardpoints = null) -> void:
	_mesh.clear_surfaces()
	if not on or tuning == null:
		return
	_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
	if hardpoints != null:
		for turret in hardpoints.turrets():
			_piece(turret.target(), turret.has_passed(), TURRET_TINT)
		for bay in hardpoints.bays():
			_piece(bay.target(), bay.has_passed(), BAY_TINT)
		for node in hardpoints.nodes():
			_piece(node.target(), node.has_passed(), NODE_TINT)
	# Les trois fenêtres de tir, entrée en haut et sortie en bas. ⚠️ Ce sont bien DEUX lignes
	# par famille : ce que le joueur perd en laissant passer une cible, c'est la distance entre
	# les deux, et elle se voit ici en une fois.
	_band(tuning.turret_visible_span * 0.5, TURRET_TINT)
	_band(tuning.bay_visible_span * 0.5, BAY_TINT)
	_band(tuning.node_visible_span * 0.5, NODE_TINT)
	# La borne de lâcher d'un pont : la limite HAUTE du plan de vol, et elle seule.
	_dashed(Vector2(GameplayPlane.bounds.position.x, GameplayPlane.bounds.end.y),
		Vector2(GameplayPlane.bounds.end.x, GameplayPlane.bounds.end.y), RELEASE_TINT)
	_mesh.surface_end()

## Une pièce QUI APPROCHE, en pâle. Rien pour celles qui sont armées, rien pour celles qui sont
## passées.
##
## ⚠️ RIEN POUR LES ARMÉES : `SolidsOverlay` les trace déjà en orange, et deux cercles superposés
## de couleurs différentes se lisent comme deux cibles.
##
## ⚠️ ET RIEN POUR LES PASSÉES, alors que ce serait tentant. Une pièce retirée cesse d'être
## suivie : sa dernière position reste FIGÉE dans le monde pendant que le décor continue de
## défiler. Le cercle dériverait donc tout seul en travers de l'écran — ce qui se lit comme un
## bug de l'instrument, pas comme une information.
func _piece(target: BulletTarget, passed: bool, tint: Color) -> void:
	if target == null or target.enabled or passed:
		return
	_circle(target.position, target.radius, Color(tint.r, tint.g, tint.b, PENDING_ALPHA))

## Les deux bords d'une fenêtre, symétriques autour du joueur.
func _band(half: float, colour: Color) -> void:
	for y in [half, -half]:
		_dashed(Vector2(GameplayPlane.bounds.position.x, y),
			Vector2(GameplayPlane.bounds.end.x, y), colour)

func _dashed(from: Vector2, to: Vector2, colour: Color) -> void:
	var span := from.distance_to(to)
	if span <= 0.001:
		return
	var step := (to - from) / span
	var travelled := 0.0
	while travelled < span:
		var stop := minf(travelled + DASH, span)
		_line(from + step * travelled, from + step * stop, colour)
		travelled = stop + GAP

func _circle(centre: Vector2, radius: float, colour: Color) -> void:
	const SEGMENTS := 16
	var prev := centre + Vector2(radius, 0.0)
	for k in range(1, SEGMENTS + 1):
		var a := TAU * float(k) / float(SEGMENTS)
		var p := centre + Vector2(cos(a), sin(a)) * radius
		_line(prev, p, colour)
		prev = p

func _line(a: Vector2, b: Vector2, colour: Color) -> void:
	_mesh.surface_set_color(colour)
	_mesh.surface_add_vertex(GameplayPlane.to_world(a) + Vector3(0.0, LIFT, 0.0))
	_mesh.surface_set_color(colour)
	_mesh.surface_add_vertex(GameplayPlane.to_world(b) + Vector3(0.0, LIFT, 0.0))

# --- Fonction pure, testable sans arbre de scène ------------------------------

## Combien de tirets une bande de cette longueur produit. ⚠️ Testable pour une seule raison :
## une boucle `while` qui n'avance pas fige le jeu, et c'est le genre de faute qu'un instrument
## de debug — allumé par défaut en build de développement — ferait passer pour un plantage du
## niveau.
static func dash_count(span: float) -> int:
	if span <= 0.001 or DASH + GAP <= 0.0:
		return 0
	return int(ceil(span / (DASH + GAP)))
