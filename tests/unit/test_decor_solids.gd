extends "res://tests/test_case.gd"
## Le décor de la chambre du réacteur, arbitré pièce par pièce (loi « les corps ne se
## chevauchent pas », lot 4).
##
## ⚠️ LE MODE D'ÉCHEC QUE CE FICHIER EXISTE POUR EMPÊCHER : un mur qu'on traverse parce qu'il
## est SOMBRE et qu'on le longe rarement. Mesuré le 2026-08-27, la face interne des bordures
## était à |x| = 13,45 quand l'aire de jeu va jusqu'à 14 : le chasseur entrait dans la pierre
## de 1,43 unité, coque comprise, et personne ne l'avait vu en six semaines de playtests.
##
## L'arbitrage tient en une question : **la pièce monte-t-elle jusqu'à la hauteur de vol ?**
##
## | Pièce | Monte à | Verdict |
## |---|---|---|
## | `Floor` | 0,45 | sol — on vole à 2,2, on ne le touche jamais |
## | `Catwalk_01..04` | −0,06 | sol — les rendre solides poserait des murs invisibles AU-DESSUS de passerelles qu'on se voit survoler, le pire cas |
## | `Reactor` | 2,05 | **corps** — il frôle le plan de vol, et c'est la machine centrale |
## | `Rim_01..06` | 3,22 | mur — mais on l'écarte hors de l'aire de jeu plutôt que de le rendre solide |
##
## Le choix d'AGRANDIR la salle plutôt que de rendre ses murs solides n'est pas un
## contournement : rendre les bordures solides rétrécirait l'aire utile en dessous de ce que
## le blindage rotatif exige, et l'entrée de plongée tomberait dans le mur. La salle était
## simplement sous-dimensionnée face à l'aire de jeu.

const DECOR_PATH := "res://assets/imported/models/bosses/core_interior.glb"

func _decor_pieces() -> Dictionary:
	## Nom de pièce -> AABB dans le plan de jeu, échelle et décalage de chambre appliqués.
	var packed := load(DECOR_PATH) as PackedScene
	if packed == null:
		return {}
	var root := track(packed.instantiate()) as Node3D
	var found := {}
	# ⚠️ ON PART DES ENFANTS DE LA RACINE, pas de la racine. Partir d'elle nommait TOUTES les
	# pièces « core_interior » : la garde voyait un seul bloc de 32 unités et n'arbitrait
	# plus rien. Ce sont les enfants directs qui portent les noms du contrat de forge.
	for child in root.get_children():
		_walk(child, root.transform, "", found)
	return found

func _walk(node: Node, parent: Transform3D, top: String, into: Dictionary) -> void:
	var as_3d := node as Node3D
	var here := parent * as_3d.transform if as_3d != null else parent
	var piece := top if not top.is_empty() else String(node.name)
	var mesh := node as MeshInstance3D
	if mesh != null and mesh.mesh != null:
		# ⚠️ Le carter est CONTRE-ÉCHELONNÉ au montage : la salle grandit, la machine non.
		# Le reproduire ici, sinon la garde mesurerait une pièce que le jeu ne montre pas.
		var factor := 1.0 if piece == CoreInterior.ANCHOR_HOUSING else CoreInterior.DECOR_SCALE
		var box := mesh.mesh.get_aabb()
		for i in 8:
			var corner := here * (box.position + box.size * Vector3(
				float(i & 1), float((i >> 1) & 1), float((i >> 2) & 1))) * factor
			var plane := GameplayPlane.to_plane(corner) + CoreInterior.PLANE_OFFSET
			var entry: Array = into.get(piece, [
				Vector3(INF, INF, INF), Vector3(-INF, -INF, -INF)])
			entry[0] = Vector3(minf(entry[0].x, plane.x), minf(entry[0].y, corner.y),
				minf(entry[0].z, plane.y))
			entry[1] = Vector3(maxf(entry[1].x, plane.x), maxf(entry[1].y, corner.y),
				maxf(entry[1].z, plane.y))
			into[piece] = entry
	for child in node.get_children():
		_walk(child, here, piece, into)

func test_the_decor_actually_loads() -> void:
	assert_true(_decor_pieces().size() >= 10,
		"le décor livré expose ses pièces (%d)" % _decor_pieces().size())

## LA garde. Une pièce qui atteint la hauteur de vol est un OBSTACLE : si elle empiète sur
## l'aire de jeu sans être déclarée solide, le chasseur la traverse.
func test_no_decor_wall_reaches_into_the_play_area() -> void:
	var offenders := PackedStringArray()
	var pieces := _decor_pieces()
	for piece_name in pieces:
		var box: Array = pieces[piece_name]
		if box[1].y < CoreInterior.FLIGHT_LIFT:
			continue   # sol : on vole au-dessus
		if piece_name == CoreInterior.ANCHOR_HOUSING:
			continue   # déclaré solide, versé par le niveau
		var footprint := Rect2(Vector2(box[0].x, box[0].z),
			Vector2(box[1].x - box[0].x, box[1].z - box[0].z))
		# ⚠️ LES BORNES DE LA CHAMBRE. Le décor de ce lieu doit se tenir au-delà du terrain de
		# CE lieu — et il est plus grand que l'arène ouverte depuis que le blindage a été
		# agrandi. Juger contre `BOUNDS` laissait la salle déborder dans le plan de vol sans
		# qu'aucune garde ne s'en aperçoive.
		if footprint.intersects(GameplayPlane.CHAMBER_BOUNDS):
			offenders.append("%s (empiète de %.2f u)" % [piece_name,
				footprint.intersection(GameplayPlane.CHAMBER_BOUNDS).size.length()])
	assert_eq(offenders.size(), 0,
		"pièces de décor traversables dans l'aire de jeu : %s" % ", ".join(offenders))

## Et le carter est bien un corps, lui. Il frôle le plan de vol : le traverser se verrait.
func test_the_reactor_housing_is_declared_solid() -> void:
	var pieces := _decor_pieces()
	assert_true(pieces.has(CoreInterior.ANCHOR_HOUSING),
		"le décor porte bien son carter '%s'" % CoreInterior.ANCHOR_HOUSING)
	if not pieces.has(CoreInterior.ANCHOR_HOUSING):
		return
	var box: Array = pieces[CoreInterior.ANCHOR_HOUSING]
	var half := maxf(box[1].x - box[0].x, box[1].z - box[0].z) * 0.5
	# ⚠️ LE CARTER EST SCULPTÉ À 2,10 ET JOUÉ À 1,80 : le nœud est contre-échelonné au
	# montage pour que l'obstacle ait la taille du noyau qu'on vise. La garde tient donc les
	# DEUX bouts — la constante qui décrit le `.glb`, et le rapport qui décrit ce qu'on en
	# fait — sans quoi rétrécir la collision seule laisserait un mur plus petit que la pièce
	# qu'on voit, exactement le défaut inverse de celui qu'on corrige.
	assert_almost_eq(CoreInterior.REACTOR_HOUSING_SCULPTED, half, 0.2,
		"la constante du sculpté (%.2f) suit la pièce du décor (%.2f)"
			% [CoreInterior.REACTOR_HOUSING_SCULPTED, half])
	var affiche := half * (CoreInterior.REACTOR_HOUSING_RADIUS
		/ CoreInterior.REACTOR_HOUSING_SCULPTED)
	assert_almost_eq(CoreInterior.REACTOR_HOUSING_RADIUS, affiche, 0.05,
		"une fois mis à l'échelle, la piece qu'on voit (%.2f) est l'obstacle qu'on heurte (%.2f)"
			% [affiche, CoreInterior.REACTOR_HOUSING_RADIUS])
	# Et il ne doit plus etre plus large que la cible : c'est cette difference de trente
	# centimetres qui plaquait le chasseur contre un mur invisible plus grand que le noyau.
	var tuning: LeviathanTuning = load("res://resources/bosses/pale_leviathan_tuning.tres")
	assert_true(CoreInterior.REACTOR_HOUSING_RADIUS <= tuning.flux_hitbox_radius + 0.01,
		"le carter (%.2f) ne deborde plus le noyau qu'on vise (%.2f)"
			% [CoreInterior.REACTOR_HOUSING_RADIUS, tuning.flux_hitbox_radius])

## Le sol reste un sol. Une garde à l'envers : elle refuse qu'on rende solide par excès de
## zèle une passerelle qu'on se voit survoler.
func test_the_floor_and_catwalks_stay_walkable_scenery() -> void:
	var pieces := _decor_pieces()
	for piece_name in pieces:
		var label := str(piece_name)
		if not (label == "Floor" or label.begins_with("Catwalk")):
			continue
		var box: Array = pieces[piece_name]
		assert_true(box[1].y < CoreInterior.FLIGHT_LIFT,
			"%s plafonne a %.2f, sous le plan de vol (%.2f) : c'est un sol"
				% [label, box[1].y, CoreInterior.FLIGHT_LIFT])
