extends "res://tests/test_case.gd"
## Le survol du Long Cortege (niveau 2).
##
## ⚠️ UN DECOR NE CASSE RIEN QUAND IL EST FAUX : il s'affiche, et personne ne sait qu'il est au
## mauvais endroit. `ADR-0025` a paye exactement ca — des anneaux de 30 cm, un contrat de noms
## respecte, aucun test rouge. Ce fichier mesure ce que l'oeil ne verifie pas.

const FlybyScript := preload("res://scripts/vfx/cortege_flyby.gd")

func _flyby() -> CortegeFlyby:
	var f: CortegeFlyby = FlybyScript.new()
	f.section_count = 5
	f.section_length = 100.0
	f.scroll_speed = 2.4
	# `_ready` ne tourne pas hors de l'arbre : on batit a la main, comme test_moon_flyby.
	f._build()
	return f

## ⚠️ LE PLAFOND EST LA GARDE LA PLUS IMPORTANTE. Un volume qui monterait dans le plan de jeu
## masquerait le combat sans jamais pouvoir etre touche.
func test_nothing_of_the_hull_rises_into_the_play_field() -> void:
	var f := _flyby()
	var plus_haut := -1000.0
	for mesh in f._all_meshes(f):
		if mesh.name == "CortegeSky":
			continue
		var aabb := mesh.get_aabb()
		# La transformation jusqu'a la racine, pas la position locale : un tronçon porte la
		# sienne, et lire `position.y` seul mentirait.
		var local := f.get_transform().affine_inverse() * mesh.get_global_transform() \
			if mesh.is_inside_tree() else mesh.transform
		var sommet := local.origin.y + aabb.position.y + aabb.size.y
		if mesh.get_parent() is Node3D:
			sommet += (mesh.get_parent() as Node3D).position.y
		plus_haut = maxf(plus_haut, sommet)
	assert_true(plus_haut <= FlybyScript.CEILING_Y,
		"le point le plus haut de la coque est a %.2f, le plafond du plan de jeu est a %.2f"
			% [plus_haut, FlybyScript.CEILING_Y])
	f.free()

func test_the_hull_sits_between_the_sky_and_the_play_field() -> void:
	assert_true(FlybyScript.HULL_Y < FlybyScript.CEILING_Y,
		"la coque est sous le plafond du plan de jeu")
	assert_true(FlybyScript.HULL_Y > FlybyScript.SKY_Y,
		"et au-dessus de son propre ciel, sinon elle serait derriere lui")

## ⚠️ LA DIFFERENCE AVEC LA LUNE. Elle tourne, on ne la parcourt jamais. Ici on avance, dans un
## seul sens, et c'est ce qui rend une cible ratee definitivement ratee.
func test_the_hull_moves_forward_and_never_comes_back() -> void:
	var avant := FlybyScript.section_z_at(0, 100.0, 0.0)
	var apres := FlybyScript.section_z_at(0, 100.0, 24.0)
	assert_true(apres > avant, "le troncon remonte vers le joueur (%.1f -> %.1f)" % [avant, apres])
	var plus_tard := FlybyScript.section_z_at(0, 100.0, 48.0)
	assert_true(plus_tard > apres, "et continue, sans jamais rebrousser chemin")

func test_the_sections_are_laid_end_to_end_without_a_gap() -> void:
	var length := 100.0
	for i in 4:
		var a := FlybyScript.section_z_at(i, length, 0.0)
		var b := FlybyScript.section_z_at(i + 1, length, 0.0)
		assert_almost_eq(b - a, length, 0.001,
			"le troncon %d suit le %d a exactement une longueur — ni trou, ni recouvrement" % [i + 1, i])

func test_the_section_under_the_player_follows_the_distance_travelled() -> void:
	assert_eq(FlybyScript.section_at(0.0, 100.0, 5), 0, "au depart, le premier")
	assert_eq(FlybyScript.section_at(150.0, 100.0, 5), 1, "a 150 unites, le deuxieme")
	assert_eq(FlybyScript.section_at(420.0, 100.0, 5), 4, "a 420, le cinquieme")
	assert_eq(FlybyScript.section_at(9999.0, 100.0, 5), 4,
		"et au-dela on reste sur le dernier — le survol s'arrete, il ne deborde pas")

func test_a_stopped_survey_reports_no_window_instead_of_dividing_by_zero() -> void:
	assert_almost_eq(FlybyScript.window_for(20.0, 0.0), 0.0, 0.001, "vitesse nulle : aucune fenetre")
	assert_almost_eq(FlybyScript.window_for(24.0, 2.4), 10.0, 0.001, "24 unites a 2,4 u/s : dix secondes")

## Le decor doit exister AVANT la forge, sinon le niveau n'est ni jouable ni mesurable.
func test_a_missing_hull_degrades_into_a_stand_in_instead_of_an_empty_level() -> void:
	var f := _flyby()
	assert_eq(f._sections.size(), 5, "cinq troncons, livres ou doubles")
	if not ResourceLoader.exists(FlybyScript.DECOR_PATH):
		assert_true(f.is_stand_in(), "sans le .glb, la doublure prend le relais")
	f.free()

## ⚠️ Un decor cache qui continue de defiler se retrouve ailleurs qu'ou on l'a laisse.
func test_hiding_the_survey_also_stops_its_clock() -> void:
	var f := _flyby()
	f.reveal(true)
	assert_true(f.is_processing(), "revele : il defile")
	f.reveal(false)
	assert_false(f.visible, "cache")
	assert_false(f.is_processing(), "et son horloge est coupee")
	f.free()

func test_the_progress_runs_from_zero_to_one() -> void:
	var f := _flyby()
	assert_almost_eq(f.progress(), 0.0, 0.001, "au depart, rien de parcouru")
	f._travelled = 250.0
	assert_almost_eq(f.progress(), 0.5, 0.001, "a mi-course, la moitie")
	f._travelled = 9999.0
	assert_almost_eq(f.progress(), 1.0, 0.001, "et jamais plus de un")
	f.free()

## Le ciel du survol prend le CHEMIN `deep_sky`, il ne baisse pas un reglage : un uniforme a
## zero ferait calculer les cinq champs de bruit pour rien.
func test_the_survey_carries_its_own_deep_sky() -> void:
	var f := _flyby()
	assert_true(f._sky != null, "le survol porte son propre ciel")
	var mat := f._sky.material_override as ShaderMaterial
	if mat != null:
		assert_true(bool(mat.get_shader_parameter(&"deep_sky")),
			"et il est sur le chemin deep_sky, pas sur une nebuleuse attenuee")
	f.free()
