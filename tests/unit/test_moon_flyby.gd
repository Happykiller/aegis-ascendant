extends "res://tests/test_case.gd"
## `MoonFlyby` — le décor de la phase `ASTEROID_FIELD` (ADR-0027).
##
## ⚠️ CE QUE CE FICHIER GARDE. Un décor de fond ne casse rien quand il est faux : il
## s'affiche, et personne ne sait qu'il est au mauvais endroit. `ADR-0025` a payé
## exactement ça — des « anneaux qu'on franchit » de 30 cm, un contrat de noms respecté,
## aucun test rouge. On mesure donc les deux choses qu'un survol peut rater sans bruit :
##   1. rien ne monte DANS le plan de jeu (au lot 2 le décor est pur : sans hitbox, un
##      volume qui traverse le champ masque le combat sans jamais pouvoir être touché) ;
##   2. la dérive reboucle vraiment, sinon les rochers partent une fois et ne reviennent
##      jamais — un survol qui se vide en trente secondes.

const FlybyScript := preload("res://scripts/vfx/moon_flyby.gd")

func _make() -> MoonFlyby:
	var flyby := track(FlybyScript.new()) as MoonFlyby
	# `_ready` ne tourne pas hors de l'arbre : on bâtit à la main, comme `CoreInterior`.
	flyby._build()
	return flyby

## Le point le plus haut de tout le décor, en composant les transformations jusqu'à la
## racine et en transformant l'AABB de chaque mesh.
##
## ⚠️ TROIS PIÈGES, tous payés ailleurs dans ce dépôt. On ne lit pas `position.y` seule :
## elle est LOCALE, et un cratère porté par le pivot de la lune rendrait une hauteur
## fausse, plausible et silencieuse (`CoreInterior._plane_of`). On ne mesure que les
## nœuds qui portent un MESH : un pivot vide posé à l'origine ferait conclure « le décor
## monte à 0 » alors qu'il ne dessine rien. Et on transforme l'AABB au lieu d'ajouter le
## rayon : un rocher écrasé PUIS tourné monte plus haut que sa demi-hauteur.
func _highest_point(node: Node3D, parent: Transform3D) -> float:
	var world := parent * node.transform
	var top := -INF
	var mesh := node as MeshInstance3D
	if mesh != null and mesh.mesh != null:
		top = (world * mesh.mesh.get_aabb()).end.y
	for child in node.get_children():
		var as_3d := child as Node3D
		if as_3d != null:
			top = maxf(top, _highest_point(as_3d, world))
	return top

func test_nothing_rises_into_the_play_field() -> void:
	var flyby := _make()
	var top := _highest_point(flyby, Transform3D.IDENTITY)
	assert_true(top <= FlybyScript.CEILING_Y,
		"sommet du décor à %.1f, plafond %.1f" % [top, FlybyScript.CEILING_Y])

func test_the_moon_sits_between_the_sky_and_the_play_field() -> void:
	# Les deux seules bornes qu'un test peut tenir sans caméra — le cadrage, lui, se juge
	# en capture (ADR-0006). Trop haut, la lune emplit le cadre et le combat se joue sur
	# un mur gris ; sous le ciel, elle passe derrière le fond et on ne survole plus rien.
	var summit := FlybyScript.MOON_CENTER.y + FlybyScript.MOON_RADIUS
	assert_true(summit <= FlybyScript.CEILING_Y,
		"sommet de la lune à %.1f, plafond %.1f" % [summit, FlybyScript.CEILING_Y])
	assert_true(summit > FlybyScript.SKY_Y,
		"lune derrière le ciel : sommet %.1f, ciel %.1f" % [summit, FlybyScript.SKY_Y])

func test_every_rock_flies_between_the_sky_and_the_play_field() -> void:
	# Même raison, corps par corps : un rocher sous le ciel ne se voit jamais, et personne
	# ne s'en apercevrait — il dériverait consciencieusement derrière le décor.
	var flyby := _make()
	for body in flyby._drifters:
		assert_true(body.position.y > FlybyScript.SKY_Y,
			"%s sous le ciel (y = %.1f)" % [body.name, body.position.y])

func test_the_drift_wraps_instead_of_emptying_the_sky() -> void:
	var speed := FlybyScript.drift_speed_at(-6.0)
	var body := Vector3(0.0, -6.0, FlybyScript.WRAP_MAX_Z - 0.1)
	var next := FlybyScript.drifted(body, Vector3(0.0, 0.0, speed), 1.0)
	assert_true(next.z <= FlybyScript.WRAP_MIN_Z + 0.001,
		"rebouclé à %.1f, bande [%.1f, %.1f]"
			% [next.z, FlybyScript.WRAP_MIN_Z, FlybyScript.WRAP_MAX_Z])
	# Et entre deux rebouclages, elle avance bel et bien.
	var mid := FlybyScript.drifted(Vector3.ZERO, Vector3(0.0, 0.0, speed), 1.0)
	assert_almost_eq(mid.z, speed, 0.001, "un pas de dérive vaut la vitesse")

func test_a_closer_rock_crosses_faster_than_a_distant_one() -> void:
	# C'est la parallaxe qui dit l'échelle, pas le nombre de triangles : deux rochers qui
	# filent à la même vitesse se lisent comme un décor plat, quelle que soit leur taille.
	# ⚠️ Mesuré sur les rochers RÉELS du décor, pas sur deux hauteurs choisies pour la
	# démonstration : la première écriture comparait −5 et −28, deux valeurs qu'aucun
	# rocher n'occupait, et elle a survécu au déplacement de tout le décor.
	var flyby := _make()
	var fastest := 0.0
	var slowest := INF
	for i in flyby._drifters.size():
		var speed: float = flyby._drift_velocities[i].z
		fastest = maxf(fastest, speed)
		slowest = minf(slowest, speed)
	assert_true(fastest > slowest * 2.0,
		"le plus proche %.2f u/s contre le plus lointain %.2f u/s" % [fastest, slowest])

func test_every_rock_drifts_and_the_moon_is_found() -> void:
	# Le décor livré comme la doublure exposent le même contrat de noms. Un rocher que
	# `_collect_bodies` ne voit pas resterait planté, sans que rien ne le dise.
	var flyby := _make()
	var rocks := 0
	for child in flyby.get_child(0).get_children():
		if (child as Node3D) != null and child.name.begins_with("Asteroid"):
			rocks += 1
	assert_true(rocks >= 3, "au moins trois rochers (%d)" % rocks)
	assert_eq(flyby._drifters.size(), rocks, "tous les rochers dérivent")
	assert_eq(flyby._drift_velocities.size(), rocks, "une vitesse par rocher")
	assert_true(flyby._moon != null, "la lune est relevée par son nom")

func test_a_missing_decor_degrades_instead_of_breaking_the_phase() -> void:
	# Même règle que `CoreInterior` : une pièce d'asset absente DÉGRADE et le dit. Les
	# deux branches sont testées — une assertion « la doublure OU le fichier » serait
	# trivialement vraie et ne prouverait rien.
	var flyby := _make()
	if ResourceLoader.exists(FlybyScript.DECOR_PATH):
		assert_false(flyby.is_stand_in(),
			"le décor livré existe : c'est LUI qui doit être monté")
	else:
		assert_true(flyby.is_stand_in(),
			"pas de décor : la doublure prend le relais, la phase reste jouable")

func test_hiding_the_flyby_also_stops_its_clock() -> void:
	# Un décor invisible qui continue de faire dériver ses rochers dépense pour rien
	# pendant les trois quarts de la partie.
	var flyby := _make()
	flyby.reveal(true)
	assert_true(flyby.visible and flyby.is_processing(), "révélé : visible et animé")
	flyby.reveal(false)
	assert_false(flyby.visible, "caché")
	assert_false(flyby.is_processing(), "et sa dérive s'arrête")
