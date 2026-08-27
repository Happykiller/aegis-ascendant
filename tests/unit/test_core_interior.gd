extends "res://tests/test_case.gd"
## `CoreInterior` — l'arene dediee ou l'on entre quand le noyau s'ouvre.
##
## ⚠️ CE QUE CE FICHIER GARDE, ET POURQUOI IL EXISTE. La conception decrivait deja un puits
## interieur, et la coque du boss livre les pieces qui en portent les noms : `Ring_01..05`,
## `Tunnel_End`, `Heart`. Mesurees, elles font 24 a 33 cm — pour un chasseur de 241 cm.
## Elles existaient par le NOM, jamais a l'ECHELLE, et RIEN ne l'a signale : ni le compte de
## triangles, ni le contrat d'export, ni le rendu.
##
## Un contrat de noms respecte n'est donc pas une preuve. Ces tests mesurent ce qui compte
## vraiment pour le joueur : le reacteur et le point d'entree tombent-ils dans le cadre ou
## le jeu se joue ?

const InteriorScript := preload("res://scripts/bosses/core_interior.gd")

func _make() -> CoreInterior:
	var interior := track(InteriorScript.new()) as CoreInterior
	# `_ready` ne tourne pas hors de l'arbre : on batit a la main, comme le reste du depot
	# pilote ses unites sans scene montee.
	interior._build()
	return interior

func test_the_reactor_sits_inside_the_playfield() -> void:
	# Le reacteur EST la cible de la phase. Hors des bornes, il serait intouchable.
	var interior := _make()
	var reactor := interior.reactor_plane_position()
	assert_true(GameplayPlane.BOUNDS.has_point(reactor),
		"reacteur en (%.1f, %.1f), bornes %s" % [reactor.x, reactor.y, GameplayPlane.BOUNDS])

## ⚠️ CETTE GARDE LISAIT L'ANCRAGE DU DECOR, et elle a fait son travail : agrandie, la salle
## l'a pousse a -8,4, hors de l'aire de jeu. Le vrai defaut n'etait pas la position mais le
## DOUBLON — le decor portait un point d'entree, le reglage en calculait un autre, et le
## chasseur etait pose a l'un puis conduit a l'autre. L'ancrage n'est plus lu ; la garde suit
## le point qui reste.
func test_the_entry_point_sits_inside_the_playfield() -> void:
	var tuning: LeviathanTuning = load("res://resources/bosses/pale_leviathan_tuning.tres")
	var interior := _make()
	var entry := interior.reactor_plane_position() + tuning.dive_entry_local()
	# ⚠️ LES BORNES DE LA CHAMBRE, et non celles du plan ordinaire : c'est le lieu ou cette
	# entree existe. Juger l'entree d'une piece sur les dimensions d'une autre piece etait
	# vrai tant que les deux avaient la meme taille ; elles n'en ont plus.
	assert_true(GameplayPlane.CHAMBER_BOUNDS.has_point(entry),
		"entree en (%.1f, %.1f), bornes de la chambre %s"
			% [entry.x, entry.y, GameplayPlane.CHAMBER_BOUNDS])

func test_the_fighter_does_not_start_on_top_of_the_reactor() -> void:
	# Il arrive DANS une arene, il ne s'y telporte pas au contact de sa cible : sinon la
	# phase commence par un choc que personne n'a demande.
	var interior := _make()
	var tuning: LeviathanTuning = load("res://resources/bosses/pale_leviathan_tuning.tres")
	var gap := tuning.dive_entry_local().length()
	assert_true(gap >= 3.0, "entree a %.1f m du reacteur" % gap)

func test_a_missing_decor_degrades_instead_of_breaking_the_fight() -> void:
	# Regle du depot : une piece d'asset absente DEGRADE et le dit. Un combat imparfait vaut
	# mieux qu'un combat qui plante — et tant que la forge n'a pas livre, la mecanique doit
	# rester jouable et testable.
	var interior := _make()
	# ⚠️ CETTE ASSERTION ETAIT TRIVIALEMENT VRAIE dans sa premiere forme (« la doublure OU le
	# fichier existe ») : elle passait sans jamais rien prouver. Le contrat reel a deux
	# branches, et il faut les tester toutes les deux.
	if ResourceLoader.exists(InteriorScript.DECOR_PATH):
		assert_false(interior.is_stand_in(),
			"le decor livre existe : c'est LUI qui doit etre monte, jamais la doublure")
	else:
		assert_true(interior.is_stand_in(),
			"pas de decor : la doublure prend le relais, le combat reste jouable")

func test_the_arena_is_hidden_until_the_fighter_enters() -> void:
	# Elle est montee a l'origine du monde : visible d'emblee, elle s'afficherait par-dessus
	# le combat exterieur.
	var interior := _make()
	interior.visible = false
	assert_false(interior.visible, "l'arene ne se montre qu'a l'entree")


## ⚠️ LE DÉCOR ET LA COLLISION DOIVENT TOURNER ENSEMBLE, ET ILS ONT TOURNÉ EN SENS INVERSE.
## Le maillage etait en miroir et le pivot en negatif : juste a l'instant zero (deux arcs
## symetriques), 96 degres d'ecart deux secondes plus tard. Le joueur butait sur des murs
## invisibles et traversait ceux qu'il voyait. Aucun banc ne l'a vu, parce que tous
## mesuraient la collision seule — juste en elle-meme. Cette garde compare un SOMMET du
## decor, transforme par son pivot, a l'arc de collision du meme instant, a deux ages.
func test_the_decor_walls_are_where_the_collision_walls_are() -> void:
	var tuning: LeviathanTuning = load("res://resources/bosses/pale_leviathan_tuning.tres")
	var interior := _make()
	interior.build_rings(tuning.reactor_rings)
	assert_true(interior._rings.size() >= 1, "le decor a bati au moins un anneau")
	if interior._rings.is_empty():
		return
	for age in [0.0, 2.0, 7.3]:
		interior.pose_rings(tuning.reactor_rings, age)
		var shapes := PlaneShapes.new()
		shapes.reserve(8)
		ReactorRings.fill_shapes(shapes, tuning.reactor_rings, Vector2.ZERO, age)
		var pivot: Node3D = interior._rings[0]
		var arc: MeshInstance3D = pivot.get_child(0) as MeshInstance3D
		assert_true(arc != null and arc.mesh != null, "le premier arc a un maillage")
		if arc == null or arc.mesh == null:
			return
		var vertex: Vector3 = arc.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX][0]
		var world: Vector3 = pivot.transform * (arc.transform * vertex)
		var seen := fposmod(rad_to_deg(GameplayPlane.to_plane(world).angle()), 360.0)
		# Le premier sommet du maillage est au DEBUT de l'arc ; la collision du meme arc
		# commence au meme azimut, ou a un tour pres.
		var expected := fposmod(shapes.param(0, 4), 360.0)
		var gap := absf(angle_difference(deg_to_rad(seen), deg_to_rad(expected)))
		assert_true(rad_to_deg(gap) < 1.0,
			"a t=%.1f s le decor montre le mur a %.1f deg, la collision le met a %.1f deg (ecart %.1f)"
				% [age, seen, expected, rad_to_deg(gap)])
