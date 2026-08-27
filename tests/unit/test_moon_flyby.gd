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
	# ⚠️ `_decor` ET NON `get_child(0)`. Lire un nœud par sa POSITION casse dès qu'un frère
	# apparaît devant lui — et l'échec ment alors sur sa cause : le 2026-08-26, sortir le
	# ciel de la doublure a fait annoncer « 0 rocher » par ce test sur un décor qui en
	# portait trois. On cherche un défaut de décor pendant que le défaut est dans la lecture.
	for child in flyby._decor.get_children():
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

# --- Les impacts (lot 3) ----------------------------------------------------

func test_every_impact_lands_on_the_moon() -> void:
	# Un point demandé hors du disque de la lune donnerait un flash dans le vide. La
	# hauteur n'est pas un réglage : elle se déduit du rayon, et doit le vérifier.
	for i in FlybyScript.IMPACT_SPOTS.size():
		var spot: Vector2 = FlybyScript.IMPACT_SPOTS[i]
		var at := FlybyScript.surface_point(spot.x, spot.y)
		assert_true(at != Vector3.INF, "impact %d hors de la lune" % i)
		assert_almost_eq(at.distance_to(FlybyScript.MOON_CENTER), FlybyScript.MOON_RADIUS,
			0.001, "impact %d posé sur la surface" % i)

func test_no_impact_ever_reaches_into_the_play_field() -> void:
	# ⚠️ L'INVARIANT PORTE SUR LA TRAJECTOIRE, PAS SUR LA POSE DE REPOS. Un bolide part
	# d'en haut : c'est le seul morceau du décor qui MONTE, et rien à l'écran ne dirait
	# qu'il traverse la zone de combat — on le lirait comme un ennemi qu'on ne peut pas
	# toucher. Première écriture : chute de 26 unités depuis un point à −23,3, donc un
	# départ à +2,7. Trouvé ici.
	for i in FlybyScript.IMPACT_SPOTS.size():
		var spot: Vector2 = FlybyScript.IMPACT_SPOTS[i]
		var at := FlybyScript.surface_point(spot.x, spot.y)
		var up := (at - FlybyScript.MOON_CENTER).normalized()
		for step in 25:
			var t := FlybyScript.BOLIDE_FALL * float(step) / 24.0
			var bolide := FlybyScript.bolide_position(at, up, t)
			assert_true(bolide.y <= FlybyScript.CEILING_Y,
				"bolide %d à %.1f (t = %.2f s)" % [i, bolide.y, t])

func test_the_shards_fly_up_then_fall_back() -> void:
	# Une gerbe qui monte sans retomber laisse des éclats plantés dans le ciel jusqu'à la
	# fin de la phase ; une gerbe qui ne monte pas n'est pas une gerbe.
	var at := FlybyScript.surface_point(
		FlybyScript.IMPACT_SPOTS[0].x, FlybyScript.IMPACT_SPOTS[0].y)
	var up := (at - FlybyScript.MOON_CENTER).normalized()
	var velocity := up * FlybyScript.SHARD_SPEED
	var peak := FlybyScript.shard_position(at, velocity, up, 1.6)
	var landing := FlybyScript.shard_position(at, velocity, up, FlybyScript.SHARD_LIFE)
	assert_true(peak.distance_to(FlybyScript.MOON_CENTER) > FlybyScript.MOON_RADIUS + 3.0,
		"la gerbe s'élève (%.1f au-dessus)" % (peak.distance_to(FlybyScript.MOON_CENTER) - FlybyScript.MOON_RADIUS))
	assert_true(landing.distance_to(FlybyScript.MOON_CENTER) < peak.distance_to(FlybyScript.MOON_CENTER),
		"et elle redescend avant de s'éteindre")
	# Et jamais dans le champ, elle non plus.
	for step in 20:
		var t := FlybyScript.SHARD_LIFE * float(step) / 19.0
		assert_true(FlybyScript.shard_position(at, velocity, up, t).y <= FlybyScript.CEILING_Y,
			"éclat à t = %.2f s" % t)

func test_the_impacts_are_scheduled_inside_the_phase() -> void:
	# Un jalon posé après la fin de la traversée ne se joue jamais : le décor se cache
	# avant. Bornes : la phase va de ~42 s (tout nettoyé) à ~54 s.
	var previous := 0.0
	for i in FlybyScript.IMPACT_TIMES.size():
		var at: float = FlybyScript.IMPACT_TIMES[i]
		assert_true(at > previous, "les jalons montent (%d : %.1f s)" % [i, at])
		assert_true(at <= 42.0, "jalon %d à %.1f s, avant la fin la plus courte" % [i, at])
		previous = at

func test_the_impact_kit_is_preallocated_and_asleep() -> void:
	# Spec §26.1 : rien ne s'alloue en jeu. Et au repos tout dort AU CENTRE DE LA LUNE —
	# invisible ne suffit pas, un kit posé à l'origine se tiendrait en plein plan de jeu.
	var flyby := _make()
	assert_eq(flyby._shards.size(), FlybyScript.SHARD_COUNT, "les éclats sont montés")
	assert_eq(flyby._shard_velocities.size(), FlybyScript.SHARD_COUNT, "une vitesse chacun")
	assert_true(flyby._bolide != null and flyby._flash != null, "bolide et flash montés")
	assert_false(flyby._bolide.visible, "le bolide dort")
	assert_false(flyby._flash.visible, "le flash dort")
	for shard in flyby._shards:
		assert_false(shard.visible, "%s dort" % shard.name)

# --- Les impacts vus d'en haut (2026-08-26) ----------------------------------
#
# ⚠️ CES TESTS EXISTENT PARCE QUE LA CAMÉRA REGARDE D'EN HAUT, et que ce fait invalide
# l'intuition. Relevé de l'opérateur en jouant : « les astéroïdes qui se crashent sur la
# lune sont un simple cercle jaune ». La cause n'était pas le manque de géométrie mais
# l'ORIENTATION : un bolide qui tombe le long de la verticale locale est vu en enfilade, et
# une gerbe conique verticale se projette exactement en un disque. Ce qui se lit en plongée
# est ce qui s'étale dans le plan qu'on voit.

func test_the_bolide_comes_in_at_an_angle_or_the_trail_is_invisible() -> void:
	var at := FlybyScript.surface_point(-6.0, 10.0)
	var up := (at - FlybyScript.MOON_CENTER).normalized()
	var heading := FlybyScript.bolide_heading(at, up)
	# La composante HORIZONTALE de la course est ce qui la rend visible d'au-dessus.
	var flat := Vector2(heading.x, heading.z).length()
	assert_true(flat > 0.45,
		"la course est franchement oblique (part horizontale %.2f) — verticale, elle serait vue en enfilade" % flat)

## ⚠️ LA GARDE DU PLAFOND NE DOIT PAS AVOIR BOUGÉ. L'écart latéral est horizontal : si
## quelqu'un lui donne un jour une composante Y, le bolide repasserait au-dessus du plan de
## jeu — le défaut que `test_the_bolide_never_crosses_the_play_field` avait déjà attrapé.
func test_the_slant_is_horizontal_and_does_not_lift_the_bolide() -> void:
	assert_almost_eq(FlybyScript.BOLIDE_FROM.y, 0.0, 0.0001,
		"l'écart latéral n'a aucune composante verticale")
	var at := FlybyScript.surface_point(-6.0, 10.0)
	var up := (at - FlybyScript.MOON_CENTER).normalized()
	assert_almost_eq(FlybyScript.bolide_start(at, up).y,
		at.y + up.y * FlybyScript.BOLIDE_DROP, 0.001,
		"le départ est à la même hauteur qu'avant l'oblique")

func test_the_trail_grows_instead_of_appearing_whole() -> void:
	assert_almost_eq(FlybyScript.trail_length(0.0), 0.0, 0.0001,
		"aucune traînée à la première image")
	var early := FlybyScript.trail_length(FlybyScript.BOLIDE_FALL * 0.3)
	var late := FlybyScript.trail_length(FlybyScript.BOLIDE_FALL * 0.9)
	assert_true(early < late, "elle s'allonge")
	assert_true(late <= FlybyScript.TRAIL_LENGTH + 0.001, "et plafonne")

## L'onde s'ÉTALE : son rayon doit croître bien plus que sa hauteur, sinon elle redevient
## la colonne verticale qu'on ne voit pas d'en haut.
func test_the_shockwave_spreads_more_than_it_rises() -> void:
	assert_true(FlybyScript.PLUME_RADIUS > FlybyScript.PLUME_HEIGHT * 3.0,
		"l'anneau est bien plus large (%.1f) que haut (%.1f)"
			% [FlybyScript.PLUME_RADIUS, FlybyScript.PLUME_HEIGHT])
	var early := FlybyScript.plume_shape(0.2)
	var late := FlybyScript.plume_shape(1.0)
	assert_true(late.x > early.x, "le rayon grandit")
	assert_almost_eq(late.x, FlybyScript.PLUME_RADIUS, 0.001, "jusqu'à sa pleine largeur")

func test_the_shockwave_lights_up_then_dies() -> void:
	assert_almost_eq(FlybyScript.plume_fade(0.0), 0.0, 0.0001, "elle naît éteinte")
	assert_almost_eq(FlybyScript.plume_fade(0.15), 1.0, 0.01, "s'allume vite")
	assert_almost_eq(FlybyScript.plume_fade(1.0), 0.0, 0.01, "et s'éteint à la fin")

## ⚠️ Le produit vectoriel rend ZÉRO si l'axe de référence est colinéaire à `up` — la base
## deviendrait invalide en silence, et l'effet pointerait n'importe où. Les impacts sont
## près du sommet de la lune, donc `up` y est presque exactement +Y : le cas dégénéré n'est
## pas théorique, c'est le cas NOMINAL.
func test_the_orientation_survives_a_vertical_up() -> void:
	for up in [Vector3.UP, Vector3.DOWN, Vector3(0.001, 1.0, 0.0).normalized()]:
		var basis := FlybyScript.basis_from_up(up)
		assert_almost_eq(basis.y.dot(up), 1.0, 0.001, "l'axe Y suit bien `up`")
		assert_almost_eq(basis.x.length(), 1.0, 0.001, "et la base reste normée")
		assert_true(absf(basis.x.dot(basis.y)) < 0.001, "et orthogonale")

# --- Les impacts peints (TEX-0005 / TEX-0006, 2026-08-26) --------------------
#
# ⚠️ CES TESTS GARDENT CE QUE CINQ ITÉRATIONS ONT COÛTÉ. L'impact a été refait cinq fois —
# sphère incandescente, traînée verticale, cône additif, coque agrandie, émission
# procédurale — avant qu'une mesure ne dise pourquoi : la tête rend à 130 px, et à cette
# taille une image autorisée à la taille d'affichage bat toute dérivation. Ce qui suit tient
# les deux invariants géométriques qu'aucune capture ne vérifierait toute seule.

func test_a_panel_lies_in_the_camera_plane() -> void:
	var view := Basis.IDENTITY
	var basis := FlybyScript.billboard_basis(view, Vector3(0.3, 0.8, -0.5), 0.0, 3.0, 2.0)
	# Le panneau fait face à la caméra : son axe Z est celui qui pointe vers elle.
	assert_almost_eq(basis.z.normalized().dot(view.z.normalized()), 1.0, 0.001,
		"le panneau fait face à la caméra")
	assert_true(absf(basis.x.dot(basis.y)) < 0.001, "et sa base reste orthogonale")

## Sans rotation, l'axe long doit suivre la PROJECTION de la course dans le plan caméra —
## c'est tout l'intérêt : un effet aligné sur une direction du monde est vu en enfilade dès
## que la caméra plonge, et s'écrase en tache. C'était le défaut de l'itération n°2.
func test_the_long_axis_follows_the_projected_course() -> void:
	var view := Basis.IDENTITY
	var course := Vector3(0.6, 0.8, -0.9)     # la composante Z est la profondeur
	var basis := FlybyScript.billboard_basis(view, course, 0.0, 1.0, 1.0)
	var attendu := Vector2(course.x, course.y).normalized()
	var obtenu := Vector2(basis.y.x, basis.y.y).normalized()
	assert_almost_eq(obtenu.dot(attendu), 1.0, 0.001,
		"l'axe long suit la course une fois sa profondeur retirée")

## ⚠️ LE CAS DÉGÉNÉRÉ N'EST PAS THÉORIQUE : une course parallèle à l'axe de vue se projette
## en un POINT, et normaliser un vecteur nul rend `NaN` — qui se propage jusqu'à faire
## disparaître le panneau sans une seule erreur au journal. Même piège que `basis_from_up`.
func test_a_course_along_the_view_axis_does_not_produce_nan() -> void:
	var view := Basis.IDENTITY
	for course in [view.z, -view.z, view.z * 3.0]:
		var basis := FlybyScript.billboard_basis(view, course, 0.0, 2.0, 2.0)
		for axe in [basis.x, basis.y, basis.z]:
			assert_true(axe.is_finite(), "aucun NaN dans la base")
			assert_true(axe.length() > 0.001, "aucun axe effondré")

## La rotation redresse les images, dont le sujet court sur la DIAGONALE et non sur l'axe
## vertical. Sans elle, le sillage part de travers par rapport à la course.
func test_the_roll_turns_the_panel_without_breaking_it() -> void:
	var view := Basis.IDENTITY
	var course := Vector3(0.0, 1.0, -0.2)
	var droit := FlybyScript.billboard_basis(view, course, 0.0, 1.0, 1.0)
	var tourne := FlybyScript.billboard_basis(view, course, FlybyScript.SPRITE_DIAGONAL, 1.0, 1.0)
	assert_true(droit.y.dot(tourne.y) < 0.95, "la rotation change bien l'orientation")
	assert_almost_eq(tourne.y.length(), 1.0, 0.001, "et la base reste normée")
	assert_true(absf(tourne.x.dot(tourne.y)) < 0.001, "et orthogonale")

# --- Le bolide doit VIVRE (playtest du 2026-08-27) --------------------------

## ⚠️ « On dirait juste un sprite qui se déplace latéralement, aucune rotation. » Le panneau
## était posé au MÊME roulis à chaque image. `billboard_basis` prend pourtant le roulis en
## degrés depuis toujours — le mécanisme était là, rien ne s'en servait.
##
## La garde porte sur le fait qu'il TOURNE, pas sur sa vitesse : celle-ci est un goût.
func test_the_bolide_actually_spins_as_it_falls() -> void:
	var view := Basis.IDENTITY
	var course := Vector3(0.2, -1.0, 0.1).normalized()
	var first := MoonFlyby.billboard_basis(view, course, MoonFlyby.SPRITE_DIAGONAL, 1.0, 1.0)
	var later := MoonFlyby.billboard_basis(view, course,
		MoonFlyby.SPRITE_DIAGONAL + 0.5 * MoonFlyby.BOLIDE_SPIN_DEG, 1.0, 1.0)
	assert_true(first.x.angle_to(later.x) > 0.3,
		"un demi-seconde de chute fait tourner le panneau de %.0f°"
			% rad_to_deg(first.x.angle_to(later.x)))

## Et il tourne dans le PLAN DE L'ÉCRAN : le panneau doit rester face caméra, sinon il
## s'aplatit en tournant et disparaît une fois sur deux.
func test_spinning_never_turns_the_panel_away_from_the_camera() -> void:
	var view := Basis.IDENTITY
	var course := Vector3(0.2, -1.0, 0.1).normalized()
	for step in 12:
		var basis := MoonFlyby.billboard_basis(view, course,
			MoonFlyby.SPRITE_DIAGONAL + step * 30.0, 1.0, 1.0)
		assert_almost_eq(basis.z.normalized().dot(view.z.normalized()), 1.0, 0.001,
			"le panneau reste face caméra au roulis %d°" % (step * 30))

## ⚠️ « La traînée est statique. » Elle était posée à échelle 1 en permanence. Elle suit
## désormais `trail_length()` — LA MÊME formule que le cône de repli, pour que les deux
## rendus racontent la même chute.
func test_the_trail_stretches_with_the_fall() -> void:
	var early := maxf(MoonFlyby.trail_length(0.2) / MoonFlyby.TRAIL_LENGTH,
		MoonFlyby.TRAIL_STRETCH_MIN)
	var late := maxf(MoonFlyby.trail_length(MoonFlyby.BOLIDE_FALL) / MoonFlyby.TRAIL_LENGTH,
		MoonFlyby.TRAIL_STRETCH_MIN)
	assert_true(late > early * 1.5,
		"la traînée passe de %.2f à %.2f de sa longueur pendant la chute" % [early, late])
	assert_true(early >= MoonFlyby.TRAIL_STRETCH_MIN,
		"et elle ne naît jamais d'un point : %.2f" % early)

## Le battement est sur la LARGEUR. Sur la longueur, il brouillerait la seule information
## que la traînée transporte — la vitesse de chute.
func test_the_flicker_never_touches_the_length() -> void:
	var view := Basis.IDENTITY
	var course := Vector3(0.0, -1.0, 0.0)
	var span := 0.0
	for step in 20:
		var flicker := 1.0 + MoonFlyby.TRAIL_FLICKER \
			* sin(step * 0.05 * TAU * MoonFlyby.TRAIL_FLICKER_HZ)
		var basis := MoonFlyby.billboard_basis(view, course, MoonFlyby.SPRITE_DIAGONAL,
			0.6, flicker)
		if step == 0:
			span = basis.y.length()
		assert_almost_eq(basis.y.length(), span, 0.001,
			"la longueur ne vibre pas (%.3f)" % basis.y.length())
