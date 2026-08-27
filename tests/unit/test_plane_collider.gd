extends "res://tests/test_case.gd"
## Le module de collision du plan de jeu ([PlaneCollider] + [PlaneShapes]).
##
## ⚠️ LE MODE D'ÉCHEC QUE CE FICHIER EXISTE POUR EMPÊCHER : un corps que la géométrie
## RETIENT. Pas « traverse un mur » — ça se voit et ça se dit —, mais l'inverse, qui ne se
## dit pas : un chasseur coincé dans un endroit dont il ne peut plus sortir, sans erreur,
## sans test rouge, et sans qu'aucune image ne montre pourquoi. C'est ce que l'opérateur a
## vécu le 2026-08-27 : « je fonce tout droit et à l'apparition de la phase interne mon
## vaisseau est bloqué, il avance pas ».
##
## La cause n'était pas la détection, elle était juste : c'était le DÉGAGEMENT, qui ne
## connaissait qu'une direction — radiale. Poussé vers l'intérieur, le chasseur atterrissait
## dans un couloir de 0,9 u alors que l'ouverture était à un demi-mètre de côté.

const SHIPPED := "res://resources/bosses/pale_leviathan_tuning.tres"

func _tuning() -> LeviathanTuning:
	return load(SHIPPED) as LeviathanTuning

func _one_arc(start_deg: float, span_deg: float) -> PlaneShapes:
	var shapes := PlaneShapes.new()
	shapes.reserve(1)
	shapes.add_ring_arc(Vector2.ZERO, 5.0, 1.0, start_deg, span_deg)
	return shapes

func _at(bearing_deg: float, distance: float) -> Vector2:
	return Vector2(cos(deg_to_rad(bearing_deg)), sin(deg_to_rad(bearing_deg))) * distance

# --- Ce qu'un obstacle doit garantir ----------------------------------------

## LA garde. Quelle que soit la forme et quel que soit l'endroit d'où l'on part, le point
## rendu par `resolve()` est LIBRE. Sans elle, un dégagement peut « réussir » en laissant le
## corps dans une autre forme — et le joueur vibre ou se retrouve enfermé.
func test_what_resolve_returns_is_always_free() -> void:
	var shapes := PlaneShapes.new()
	shapes.reserve(6)
	# ⚠️ UNE GEOMETRIE QUI LAISSE DE LA PLACE, et c'est une condition, pas une commodite :
	# des formes qui se chevauchent ne laissent AUCUN point libre entre elles, et aucun
	# algorithme ne peut en sortir un corps. C'est precisement ce que
	# `test_no_wall_lives_inside_the_core` impose a la geometrie livree.
	shapes.add_ring_arc(Vector2.ZERO, 5.0, 1.0, 0.0, 90.0)
	shapes.add_ring_arc(Vector2.ZERO, 3.0, 0.8, 40.0, 120.0)
	shapes.add_disc(Vector2.ZERO, 1.5)
	var stuck := 0
	var worst := ""
	for i in 360:
		for r in [0.4, 1.2, 2.0, 2.4, 3.0, 3.9, 4.6, 5.0, 5.4, 6.0]:
			var start := _at(float(i), r)
			var freed := PlaneCollider.resolve(shapes, start, 0.35)
			if PlaneCollider.blocks(shapes, freed, 0.35):
				stuck += 1
				if worst.is_empty():
					worst = " (premier : azimut %d, rayon %.1f)" % [i, r]
	assert_eq(stuck, 0, "aucun point degage ne reste dans une forme%s" % worst)

## Un point déjà libre ne bouge pas. Sinon l'appelant réécrit une position à chaque image et
## le pilotage devient poisseux sans que rien ne le montre.
func test_a_free_point_is_left_exactly_where_it_was() -> void:
	var shapes := _one_arc(0.0, 90.0)
	var free := _at(200.0, 5.0)
	assert_true(PlaneCollider.resolve(shapes, free, 0.35).is_equal_approx(free),
		"hors de l'arc, rien ne bouge")

## ⚠️ LE DEFAUT VECU, ET LA RAISON D'ETRE DU MODULE. Un corps pris tout PRES DU BOUT d'un mur
## doit sortir PAR LE BOUT — par l'ouverture, qui est a quelques centimetres — et non se
## faire pousser radialement a travers toute l'epaisseur.
func test_a_body_near_the_end_of_a_wall_escapes_through_the_opening() -> void:
	var shapes := _one_arc(0.0, 90.0)
	# A 2 degres du bout, sur le rayon median : le bout est a ~0,17 u, les faces a 0,85.
	var stuck := _at(2.0, 5.0)
	var freed := PlaneCollider.resolve(shapes, stuck, 0.0)
	assert_false(PlaneCollider.blocks(shapes, freed, 0.0), "il est sorti")
	assert_almost_eq(freed.length(), 5.0, 0.15,
		"et il est sorti PAR LE COTE : son rayon n'a pas change, il a contourne le bout")
	assert_true(freed.distance_to(stuck) < 0.5,
		"par le chemin le plus court (%.2f u)" % freed.distance_to(stuck))

## Le symétrique : au MILIEU d'un long mur, aucun bout n'est proche et la sortie est bien
## radiale. Sans cette garde, un dégagement qui contournerait toujours passerait pour bon.
func test_a_body_in_the_middle_of_a_long_wall_escapes_radially() -> void:
	var shapes := _one_arc(0.0, 180.0)
	var freed := PlaneCollider.resolve(shapes, _at(90.0, 5.0), 0.0)
	assert_false(PlaneCollider.blocks(shapes, freed, 0.0), "il est sorti")
	assert_almost_eq(rad_to_deg(freed.angle()), 90.0, 1.0, "sans changer d'azimut")
	assert_true(absf(freed.length() - 5.0) > 0.4, "en franchissant une face")

## Le corps a une LARGEUR. Une aile ne passe pas par un bord que le centre franchit.
func test_a_wide_body_does_not_slip_past_an_edge_its_centre_clears() -> void:
	var shapes := _one_arc(0.0, 90.0)
	var just_past := _at(-3.0, 5.0)
	assert_false(PlaneCollider.blocks(shapes, just_past, 0.0),
		"le centre est hors de l'arc")
	assert_true(PlaneCollider.blocks(shapes, just_past, 0.6),
		"mais un corps de 0,6 y touche encore")

## Un disque arrête, et il pousse vers l'extérieur.
func test_a_disc_stops_a_body_and_pushes_it_out() -> void:
	var shapes := PlaneShapes.new()
	shapes.reserve(1)
	shapes.add_disc(Vector2(3.0, 0.0), 2.0)
	assert_true(PlaneCollider.blocks(shapes, Vector2(3.5, 0.0), 0.0), "dedans")
	var freed := PlaneCollider.resolve(shapes, Vector2(4.0, 0.0), 0.5)
	assert_true(freed.x > 3.0 + 2.0 + 0.5, "repousse au-dela de la surface, corps compris")
	assert_almost_eq(freed.y, 0.0, 0.001, "en ligne droite depuis le centre")

func test_a_capsule_stops_a_body_along_its_whole_length() -> void:
	var shapes := PlaneShapes.new()
	shapes.reserve(1)
	shapes.add_capsule(Vector2(-4.0, 0.0), Vector2(4.0, 0.0), 0.5)
	assert_true(PlaneCollider.blocks(shapes, Vector2(0.0, 0.3), 0.0), "au milieu")
	assert_true(PlaneCollider.blocks(shapes, Vector2(4.2, 0.0), 0.0), "au bout arrondi")
	assert_false(PlaneCollider.blocks(shapes, Vector2(6.0, 0.0), 0.0), "au-dela, non")

# --- La ligne de tir ---------------------------------------------------------

func test_a_clear_line_reports_no_hit_at_all() -> void:
	var shapes := _one_arc(0.0, 90.0)
	assert_eq(PlaneCollider.first_hit(shapes, _at(200.0, 9.0), Vector2.ZERO, 0.35),
		PlaneCollider.NO_HIT, "rien sur le chemin")

## Une ligne bloquée doit dire OÙ. Sans le point, le repère d'arrêt se pose au jugé — et les
## bolts le manquaient en traversant le mur (« les tirs aussi peuvent passer »).
func test_a_blocked_line_always_names_where_it_is_blocked() -> void:
	var shapes := _one_arc(0.0, 90.0)
	var from := _at(45.0, 9.0)
	var hit := PlaneCollider.first_hit(shapes, from, Vector2.ZERO, 0.35)
	assert_true(hit != PlaneCollider.NO_HIT, "le mur est bien en travers")
	assert_true(PlaneCollider.blocks(shapes, hit, 0.35), "et le point nomme touche du plein")
	assert_true(hit.length() > 5.0, "c'est le PREMIER contact : la face externe, pas l'autre")

# --- Le contrat d'allocation --------------------------------------------------

## ⚠️ ZÉRO ALLOCATION EN BOUCLE CRITIQUE (spec §26.1). Les murs tournent et le noyau dérive :
## les formes sont refaites SOIXANTE FOIS PAR SECONDE. Cette garde vérifie que remplir et
## vider ne fait pas grossir les tableaux — c'est-à-dire qu'aucune image n'alloue.
func test_refilling_the_shapes_never_grows_the_arrays() -> void:
	var shapes := PlaneShapes.new()
	shapes.reserve(8)
	for frame in 500:
		shapes.clear()
		for i in 8:
			shapes.add_ring_arc(Vector2.ZERO, 5.0, 1.0, float(frame + i), 30.0)
		assert_eq(shapes.size(), 8, "huit formes, toujours")
	assert_eq(shapes.size(), 8, "et rien ne s'est accumule")

# --- Le blindage livré --------------------------------------------------------

## ⚠️ LA GARDE DU DÉFAUT VÉCU. Le point d'apparition dans le noyau valait `Vector2(0, -5)`,
## une constante écrite avant que les murs n'existent — et qui tombait EN PLEIN DEDANS.
## Il se déduit désormais des anneaux : cette garde refuse toute géométrie qui l'enfermerait.
func test_the_dive_entry_is_never_inside_a_wall() -> void:
	var tuning := _tuning()
	var entry := tuning.dive_entry_local()
	var shapes := PlaneShapes.new()
	shapes.reserve(ReactorRings.shape_count(tuning.reactor_rings) + 1)
	var worst := 0.0
	for i in 600:
		var age := float(i) * 0.07
		shapes.clear()
		ReactorRings.fill_shapes(shapes, tuning.reactor_rings, Vector2.ZERO, age)
		shapes.add_disc(Vector2.ZERO, tuning.flux_hitbox_radius + tuning.flux_drift_radius)
		var freed := PlaneCollider.resolve(shapes, entry, tuning.wall_clearance)
		worst = maxf(worst, freed.distance_to(entry))
	assert_almost_eq(worst, 0.0, 0.001,
		"le chasseur apparait TOUJOURS au large (deplacement maximal %.2f u)" % worst)

## Et il doit pouvoir voler. Une entrée libre mais collée au bord de l'arène serait un piège
## d'un autre genre : il ne pourrait ni avancer ni reculer.
##
## ⚠️ EN COORDONNÉES DU MONDE, ET LA PREMIÈRE VERSION S'EST TROMPÉE LÀ-DESSUS. Elle comparait
## `dive_entry_local()` — relatif au CENTRE DU RÉACTEUR — aux limites du plan, qui sont
## absolues. Tant que la chambre était centrée en (0,0), les deux coïncidaient et l'erreur
## était invisible ; elle est apparue le jour où la chambre a été remontée.
func test_the_dive_entry_leaves_room_to_fly() -> void:
	var tuning := _tuning()
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	var entry := CoreInterior.PLANE_OFFSET + tuning.dive_entry_local()
	assert_true(GameplayPlane.is_inside(entry),
		"l'entree est dans les limites du plan (y = %.2f)" % entry.y)
	var room := entry.y - GameplayPlane.BOUNDS.position.y
	assert_true(room >= stats.body_radius,
		"il reste %.2f u sous elle pour manoeuvrer, pour un chasseur large de %.2f"
			% [room, stats.body_radius * 2.0])

## Et le chasseur doit pouvoir atteindre le HAUT de l'arène sans se retrouver dans le mur.
## Sinon le dégagement le repousse, les limites du plan le ramènent, et il vibre entre les
## deux — un blocage de plus, et celui-là n'a aucune image pour l'expliquer.
func test_the_top_of_the_arena_is_not_inside_the_shield() -> void:
	var tuning := _tuning()
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	var outermost := 0.0
	for ring in tuning.reactor_rings:
		if ring != null:
			outermost = maxf(outermost, ring.radius + ring.thickness * 0.5)
	var reach := GameplayPlane.BOUNDS.end.y - CoreInterior.PLANE_OFFSET.y
	assert_true(reach > outermost + stats.body_radius,
		("le haut de l'arene est a %.2f du noyau, le blindage va jusqu'a %.2f corps compris"
			% [reach, outermost + stats.body_radius]))

## ⚠️ « Le réacteur central ne devrait pas être franchissable » (playtest du 2026-08-27). Il
## l'était : on lui traversait le ventre, parce que la collision ne connaissait que les murs.
func test_the_core_itself_is_solid() -> void:
	var tuning := _tuning()
	var shapes := PlaneShapes.new()
	shapes.reserve(1)
	shapes.add_disc(Vector2.ZERO, tuning.flux_hitbox_radius)
	assert_true(PlaneCollider.blocks(shapes, Vector2.ZERO, 0.0), "on ne passe pas au centre")
	var freed := PlaneCollider.resolve(shapes, Vector2(0.5, 0.2), tuning.wall_clearance)
	assert_true(freed.length() >= tuning.flux_hitbox_radius + tuning.wall_clearance,
		"et le chasseur est repousse hors de sa surface")

## Le mur intérieur doit être DEHORS. Il a longtemps été à l'intérieur du flux — visible sur
## toutes les captures, deux arcs violets à cheval sur la sphère — et personne ne le testait.
func test_no_wall_lives_inside_the_core() -> void:
	var tuning := _tuning()
	var envelope := tuning.flux_hitbox_radius + tuning.flux_drift_radius
	for ring in tuning.reactor_rings:
		if ring == null:
			continue
		assert_true(ring.radius - ring.thickness * 0.5 >= envelope - 0.001,
			("mur de rayon %.2f : sa face interne (%.2f) est dans l'enveloppe du flux (%.2f)"
				% [ring.radius, ring.radius - ring.thickness * 0.5, envelope]))

## ⚠️ DEUX CHIFFRES SUR LE MÊME FAIT, et ce dépôt sait ce que ça coûte. `wall_clearance` sert
## à placer l'entrée dans la chambre ; il doit valoir l'encombrement RÉEL du chasseur devant
## lui. Le laisser dériver du corps replacerait l'entrée dans le mur — le défaut d'origine.
func test_the_wall_clearance_matches_the_real_fighter() -> void:
	var tuning := _tuning()
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	var reach := stats.body_half_length + stats.body_radius
	assert_almost_eq(tuning.wall_clearance, reach, 0.05,
		("wall_clearance vaut %.2f, l'encombrement du chasseur %.2f "
			+ "(demi-longueur %.2f + demi-largeur %.2f)")
			% [tuning.wall_clearance, reach, stats.body_half_length, stats.body_radius])

## Le nez, précisément. C'est LUI qu'on a vu traverser, et un disque ne le décrit pas.
func test_the_nose_is_stopped_where_a_disc_would_have_let_it_through() -> void:
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	var shapes := PlaneShapes.new()
	shapes.reserve(1)
	# Un mur droit devant, a portee du nez mais hors de portee d'un disque de demi-largeur.
	var wall_y := stats.body_radius + (stats.body_half_length - stats.body_radius) * 0.5
	shapes.add_capsule(Vector2(-6.0, wall_y), Vector2(6.0, wall_y), 0.1)
	assert_false(PlaneCollider.blocks(shapes, Vector2.ZERO, stats.body_radius),
		"un DISQUE de sa demi-largeur ne verrait rien : c'est ainsi qu'il traversait")
	assert_true(PlaneCollider.capsule_blocks(shapes, Vector2.ZERO, Vector2(0.0, 1.0),
			stats.body_half_length, stats.body_radius),
		"la CAPSULE, elle, touche : le nez est devant")
	var freed := PlaneCollider.resolve_capsule(shapes, Vector2.ZERO, Vector2(0.0, 1.0),
		stats.body_half_length, stats.body_radius)
	assert_true(freed.y < 0.0, "et le chasseur est repousse en arriere, pas laisse dedans")
	assert_false(PlaneCollider.capsule_blocks(shapes, freed, Vector2(0.0, 1.0),
			stats.body_half_length, stats.body_radius),
		"jusqu'a etre franchement dehors")
