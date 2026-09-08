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
		assert_almost_eq(a - b, length, 0.001,
			"le troncon %d precede le %d d'exactement une longueur — ni trou, ni recouvrement" % [i, i + 1])

## ⚠️ Le troncon 1 est SOUS le joueur au depart, le 5 est loin devant. C'est le sens de la
## traversee : on remonte le vaisseau de la proue vers l'arriere.
func test_the_first_section_is_under_the_player_and_the_last_is_far_ahead() -> void:
	assert_almost_eq(FlybyScript.section_z_at(0, 100.0, 0.0), -FlybyScript.LEAD_IN, 0.001,
		"au depart le premier troncon est DEVANT le joueur, pas sous lui — il faut le voir venir")
	assert_true(FlybyScript.section_z_at(4, 100.0, 0.0) < -300.0, "le dernier, loin devant")

## ⚠️ LE SURVOL NE S'ARRETE PLUS A 500 M, IL FREINE JUSQU'A LA POUPE — et le test disait
## l'ancienne regle. Avant le 2026-09-06 il se terminait sec une fois le lead-in et les cinq
## troncons parcourus ; la phase finale montait alors sa PROPRE plateforme, qui glissait dans le
## cadre et venait se ranger. « Il y a une espece de plateforme qui amene les moteurs a la fin,
## alors que les moteurs doivent etre rattaches au vaisseau » (operateur, en regardant). Les
## groupes sont boulonnes a la carene depuis toujours : ce qui doit s'arreter, c'est le
## DEFILEMENT.
func test_the_survey_brakes_to_the_stern_instead_of_stopping_at_the_last_section() -> void:
	var f := _flyby()
	f.reveal(true)
	var cinq := f.section_length * float(f.section_count) + FlybyScript.LEAD_IN
	assert_true(f.stop_at() > cinq,
		"il continue au-dela des cinq troncons (%.1f contre %.1f) — la poupe est plus loin"
			% [f.stop_at(), cinq])
	f._travelled = cinq
	f._process(0.0)
	assert_false(f._finished, "au bout du cinquieme troncon, la traversee n'est pas finie")
	# ⚠️ ET IL RALENTIT AVANT DE S'ARRETER : un arret net se lit comme un accrochage.
	# ⚠️ LE TEMOIN DE CROISIERE SE PREND LOIN DE LA FIN. Pris au bout du cinquieme troncon, il
	# est DEJA dans la zone de freinage — le vaisseau y ralentit depuis vingt-quatre unites — et
	# la comparaison rendait un rapport de 0,875, c'est-a-dire rien.
	f._travelled = f.stop_at() - 2.0
	var avant := f._travelled
	f._process(1.0)
	var pas_freine := f._travelled - avant
	f._travelled = f.stop_at() - FlybyScript.STERN_BRAKE - 40.0
	avant = f._travelled
	f._process(1.0)
	var pas_plein := f._travelled - avant
	assert_true(pas_freine < pas_plein * 0.6,
		"a deux unites de l'arret il avance %.2f contre %.2f en croisiere"
			% [pas_freine, pas_plein])
	f._travelled = f.stop_at()
	f._process(0.0)
	assert_true(f._finished, "et il se termine a la station de la poupe")
	f.free()

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

# =============================================================================
# La derive de fin — le Cortege n'est pas detruit, on le LAISSE
# =============================================================================

const STERN_T: CortegeSternTuning = preload("res://resources/levels/long_cortege_stern.tres")
const LEVEL_SCENE_FOR_DRIFT := "res://scenes/gameplay/cortege.tscn"

func _drift_camera() -> Array:
	var packed: PackedScene = load(LEVEL_SCENE_FOR_DRIFT)
	assert_true(packed != null, "la scene du niveau 2 se charge")
	var etat := packed.get_state()
	for i in etat.get_node_count():
		if String(etat.get_node_name(i)) != "Camera3D":
			continue
		var camera := Transform3D.IDENTITY
		var fov := 0.0
		for j in etat.get_node_property_count(i):
			var nom := String(etat.get_node_property_name(i, j))
			if nom == "transform":
				camera = etat.get_node_property_value(i, j)
			elif nom == "fov":
				fov = etat.get_node_property_value(i, j)
		if fov > 0.0:
			return [camera, fov]
	return []

## ⚠️ LA DERIVE DOIT SORTIR LA POUPE, PAS SEULEMENT LA DEPLACER. L'Aurora Spear entre par le haut
## quand `wreck_gone` tombe : si la carene est encore a l'ecran a cet instant, le porte-chasseur
## se pose PAR-DESSUS quarante metres de coque, et ca se lit comme une collision.
##
## Le cadre est LU dans la scene, jamais recopie : une camera reculee d'une unite rendrait ce
## test faux en silence, et la faute ne se verrait qu'en jouant la fin du niveau.
func test_the_drift_takes_the_wreck_out_of_the_frame() -> void:
	var cam := _drift_camera()
	assert_eq(cam.size(), 2, "la camera du niveau se lit")
	if cam.size() != 2:
		return
	var oeil: Vector3 = (cam[0] as Transform3D).origin
	var cadre: Rect2 = GameplayPlane.visible_frame(cam[0], cam[1])
	# Le point le plus ARRIERE de la poupe : le massif, a `z_local = -12` (BRIEF-0106 §2).
	var arriere_local := -12.0
	var apres := CortegeFlyby.DRIFT_RUN
	var monde := Vector3(0.0, STERN_T.deck_y,
		-STERN_T.hold_plane_y + apres + arriere_local)
	var plan := GameplayPlane.aim_point_of(monde, oeil)
	assert_true(plan.y < cadre.position.y,
		"apres %.1f u de derive, l'arriere de la poupe est a plan_y = %.2f, sous le bord bas du cadre (%.2f)"
			% [apres, plan.y, cadre.position.y])

## ⚠️ ET ELLE NE REPART PAS A LA VITESSE DU SURVOL. Un vaisseau dont on vient de couper les trois
## moteurs qui reprendrait sa vitesse de croisiere en une image demenrait la phrase qu'on vient
## de lui appliquer. La rampe existe, et elle dure.
func test_the_wreck_takes_its_time_to_move_again() -> void:
	assert_true(CortegeFlyby.DRIFT_RAMP > 1.0,
		"la derive s'installe en %.1f s, elle ne demarre pas d'un coup" % CortegeFlyby.DRIFT_RAMP)
	assert_true(CortegeFlyby.DRIFT_SPEED > 0.0, "et elle avance vraiment")
