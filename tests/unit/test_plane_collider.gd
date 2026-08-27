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
	# ⚠️ LES BORNES DE LA CHAMBRE. L'entree se DEDUIT du rayon du mur exterieur : agrandir le
	# blindage la fait descendre avec lui, et c'est elle — plus que le poste de tir — qui
	# commande la profondeur du plan de vol de ce lieu.
	var chamber := GameplayPlane.CHAMBER_BOUNDS
	assert_true(chamber.has_point(entry),
		"l'entree (y = %.2f) est dans la chambre (bas %.2f)" % [entry.y, chamber.position.y])
	# ⚠️ SON CORPS ENTIER, et non sa demi-largeur. Le test exigeait `body_radius` : il aurait
	# valide un point d'apparition ou le chasseur nait le nez dans le mur et la queue hors du
	# plan. Ce qui doit tenir sous lui, c'est ce que la collision teste — la capsule.
	var room := entry.y - chamber.position.y
	var demi_corps: float = stats.body_half_length + stats.body_radius
	assert_true(room >= demi_corps,
		"il reste %.2f u sous l'entree, pour un corps qui en occupe %.2f depuis son centre"
			% [room, demi_corps])

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
	# Le haut de la CHAMBRE — et le corps entier, pour la meme raison que l'entree : ce qui
	# doit passer au-dessus du blindage, c'est la capsule, pas un rayon.
	var reach := GameplayPlane.CHAMBER_BOUNDS.end.y - CoreInterior.PLANE_OFFSET.y
	var demi_corps: float = stats.body_half_length + stats.body_radius
	assert_true(reach > outermost + demi_corps,
		("le haut de la chambre est a %.2f du noyau, le blindage va jusqu'a %.2f corps compris"
			% [reach, outermost + demi_corps]))

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

## ⚠️ LE DÉGAGEMENT ET LE BORNAGE PEUVENT SE DISPUTER. Le premier peut sortir le chasseur de
## l'arène, le second peut l'y rentrer — dans un obstacle. Un joueur poussé contre le bord
## doit finir QUELQUE PART, pas vibrer entre les deux. Le comportement était affirmé dans un
## commentaire ; il est mesuré ici.
func test_a_fighter_pushed_against_the_arena_edge_settles() -> void:
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	var shapes := PlaneShapes.new()
	shapes.reserve(1)
	# Un gros corps juste au-dessus du bord bas : le seul dégagement possible est vers le bas,
	# et le bas est justement la limite du plan.
	var bottom := GameplayPlane.BOUNDS.position.y
	shapes.add_disc(Vector2(0.0, bottom + 2.0), 3.0)
	var here := Vector2(0.0, bottom + 0.5)
	var seen := PackedVector2Array()
	for step in 40:
		here = GameplayPlane.clamp_to_bounds(PlaneCollider.resolve_capsule(shapes, here,
			Vector2(0.0, 1.0), stats.body_half_length, stats.body_radius))
		seen.append(here)
	var last := seen[seen.size() - 1]
	assert_true(last.distance_to(seen[seen.size() - 2]) < 0.001,
		"il s'est immobilise (dernier pas %.4f u)"
			% last.distance_to(seen[seen.size() - 2]))
	assert_true(GameplayPlane.is_inside(last, 0.001),
		"et il est reste dans l'arene (y = %.2f)" % last.y)

# --- Le déplacement : on glisse, on ne corrige pas -----------------------------
## ⚠️ Le mode d'echec vise ici a un NOM, donne par l'operateur le 2026-08-27 : « j'ai pu
## rentrer dans les murs, et quand on est repousse c'est comme un aimant ou avec des
## ressorts ». Les deux moities sont le meme defaut — corriger APRES coup fait entrer pour
## de bon, puis ressortir par un saut, et le saut rejoue contre la commande du joueur donne
## un ressort. Ces gardes tiennent l'ordre des operations, pas la detection.

func _wall() -> PlaneShapes:
	var shapes := PlaneShapes.new()
	shapes.reserve(1)
	# Un mur horizontal en y = 4, tres large : on ne peut pas le contourner par les bouts.
	shapes.add_capsule(Vector2(-40.0, 4.0), Vector2(40.0, 4.0), 0.6)
	return shapes

func test_a_move_into_a_wall_never_ends_inside_it() -> void:
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	var shapes := _wall()
	var from := Vector2(0.0, 0.0)
	for i in 60:
		var to := Vector2(0.0, float(i) * 0.15)
		var landed := PlaneCollider.slide_capsule(shapes, from, to, Vector2(0.0, 1.0),
			stats.body_half_length, stats.body_radius)
		assert_false(PlaneCollider.capsule_blocks(shapes, landed, Vector2(0.0, 1.0),
				stats.body_half_length, stats.body_radius),
			"pas d'entree dans le mur, meme en visant %.2f" % to.y)

## Et on GLISSE : un mouvement oblique contre un mur garde sa composante le long du mur.
## Sans ca le vaisseau se colle et s'arrete net, ce qui se joue comme un accrochage.
func test_a_diagonal_move_keeps_travelling_along_the_wall() -> void:
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	var shapes := _wall()
	var from := Vector2(0.0, 1.0)
	var to := from + Vector2(1.5, 1.5)
	var landed := PlaneCollider.slide_capsule(shapes, from, to, Vector2(0.0, 1.0),
		stats.body_half_length, stats.body_radius)
	assert_false(PlaneCollider.capsule_blocks(shapes, landed, Vector2(0.0, 1.0),
			stats.body_half_length, stats.body_radius), "il est dehors")
	assert_true(landed.x > from.x + 0.5,
		"il a bien avance LE LONG du mur (%.2f u de cote)" % (landed.x - from.x))

## ⚠️ LA GARDE DU RESSORT. Le joueur pousse contre le mur pendant deux secondes : sa position
## doit SE POSER, pas osciller. Un aller-retour d'une image sur l'autre est exactement ce que
## l'operateur a decrit, et c'est invisible sur une capture fixe.
func test_holding_against_a_wall_settles_instead_of_bouncing() -> void:
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	var shapes := _wall()
	var here := Vector2(0.0, 0.0)
	var reversals := 0
	var previous := 0.0
	for frame in 120:
		var wanted := here + Vector2(0.0, 6.0) * (1.0 / 60.0)
		var next := PlaneCollider.slide_capsule(shapes, here, wanted, Vector2(0.0, 1.0),
			stats.body_half_length, stats.body_radius)
		var step := next.y - here.y
		if absf(step) > 0.0005 and absf(previous) > 0.0005 and signf(step) != signf(previous):
			reversals += 1
		previous = step
		here = next
	assert_eq(reversals, 0,
		"aucun aller-retour en deux secondes de poussee (%d releves)" % reversals)
	assert_true(absf(previous) < 0.001,
		"et il s'est pose (dernier pas %.5f u)" % absf(previous))

## Un mur qui TOURNE peut rattraper un vaisseau immobile : il faut bien l'en sortir. Mais le
## degagement doit etre BORNE — instantane, c'est le saut qui fait le ressort.
func test_a_wall_that_catches_you_pushes_you_out_at_a_readable_speed() -> void:
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	var shapes := _wall()
	var inside := Vector2(0.0, 4.0)
	assert_true(PlaneCollider.capsule_blocks(shapes, inside, Vector2(0.0, 1.0),
			stats.body_half_length, stats.body_radius), "pre-requis : il est dedans")
	var freed := PlaneCollider.resolve_capsule(shapes, inside, Vector2(0.0, 1.0),
		stats.body_half_length, stats.body_radius)
	var step := inside.move_toward(freed, PlayerFighterController.DEPENETRATION_SPEED / 60.0)
	assert_true(step.distance_to(inside) < freed.distance_to(inside),
		"il sort en plusieurs images, pas d'un bond")
	assert_true(step.distance_to(inside) > 0.05,
		"mais franchement : %.3f u en une image" % step.distance_to(inside))

## ⚠️ LA GARDE DE L'AIMANT, et elle rejoue le blindage LIVRE parce que le defaut ne se
## reproduit pas sur un mur droit. « Quand on est repousse c'est comme un aimant ou avec des
## ressorts » (playtest du 2026-08-27) : au moindre CONTACT le chasseur perdait sa commande
## et n'etait plus que repousse. Or le contact est l'etat NORMAL de cette phase — mesure :
## un joueur qui pousse vers le noyau touche un mur 77 % du temps. Il perdait donc la main
## trois images sur quatre. Le remede tient en un ordre : GLISSER d'abord, ne corriger que ce
## qui depasse.
##
## ⚠️ ET LE CHASSEUR DOIT RESTER AU CONTACT. Premiere version de cette garde : elle le
## poussait vers le cote, il s'eloignait du blindage en quelques images et ne longeait plus
## rien — verte, et aveugle (la mutation qui remettait le defaut passait). Ici il TOURNE
## autour du reacteur, a distance rasante, donc chaque arc solide qui passe le touche.
func _graze(input_is_tangential: bool) -> Array:
	var tuning: LeviathanTuning = load(SHIPPED)
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	var shapes := PlaneShapes.new()
	shapes.reserve(ReactorRings.shape_count(tuning.reactor_rings) + 2)
	var outermost := 0.0
	for ring in tuning.reactor_rings:
		if ring != null:
			outermost = maxf(outermost, ring.radius + ring.thickness * 0.5)
	# Juste assez pres pour que la coque morde le mur quand un arc passe devant.
	var grazing := outermost + stats.body_radius - 0.06
	var up := Vector2(0.0, 1.0)
	var here := Vector2(0.0, -grazing)
	var last_free := here
	var shoved := 0
	var touched := 0
	var travelled := 0.0
	var closest := 999.0
	for i in 600:
		var age := float(i) / 60.0
		shapes.clear()
		ReactorRings.fill_shapes(shapes, tuning.reactor_rings, Vector2.ZERO, age)
		shapes.add_disc(Vector2.ZERO, tuning.flux_hitbox_radius)
		# Tangentiel : il longe, en restant a distance rasante. Radial : il pousse dedans.
		var radial := here.normalized()
		var input := Vector2(-radial.y, radial.x) * 4.0 if input_is_tangential else -radial * 4.0
		var wanted := here + input / 60.0
		if input_is_tangential:
			wanted = wanted.normalized() * grazing
		# ⚠️ ON COMPTE LE MUR QUI SE MET EN TRAVERS, pas le corps enfonce dedans. Avec le
		# glissement le chasseur n'est JAMAIS dedans — il est contre — donc compter les
		# penetrations rendait zero par construction, et la garde ne prouvait plus rien.
		if PlaneCollider.capsule_blocks(shapes, wanted, up, stats.body_half_length,
				stats.body_radius):
			touched += 1
		var next := PlaneCollider.slide_capsule(shapes, here, wanted, up,
			stats.body_half_length, stats.body_radius)
		if PlaneCollider.capsule_blocks(shapes, next, up, stats.body_half_length,
				stats.body_radius):
			var freed := PlaneCollider.resolve_capsule(shapes, next, up,
				stats.body_half_length, stats.body_radius, 5, last_free - next)
			if freed.distance_to(next) > PlayerFighterController.CONTACT_TOLERANCE:
				next = next.move_toward(freed,
					PlayerFighterController.DEPENETRATION_SPEED / 60.0)
				shoved += 1
		else:
			last_free = next
		travelled += next.distance_to(here)
		here = next
		closest = minf(closest, here.length())
	return [shoved, touched, travelled, closest]

func test_a_fighter_grazing_the_shield_keeps_full_control() -> void:
	var run := _graze(true)
	var shoved: int = run[0]
	var touched: int = run[1]
	var travelled: float = run[2]
	# ⚠️ SEUIL DE CALIBRATION, RECALE APRES L'AGRANDISSEMENT DU BLINDAGE (8,05). Ce n'est pas
	# la garde — celles-ci sont `shoved` et `travelled` — c'est le controle qui dit que la
	# simulation frotte vraiment quelque chose. Le mur ayant grandi a angles d'ouverture
	# constants, la meme trajectoire rasante passe de 82 images de contact au lieu de plus de
	# cent. Abaisser ce chiffre n'affaiblit rien tant que les deux assertions qui suivent
	# restent inchangees ; le supprimer, si.
	assert_true(touched > 60,
		"pre-requis : il RASE vraiment le blindage (%d images de contact sur 600)" % touched)
	assert_true(shoved < 30,
		"il longe sans etre manipule (%d images bousculees sur 600)" % shoved)
	assert_true(travelled > 25.0,
		"et il avance vraiment : %.1f u parcourues en dix secondes" % travelled)

## Et quand il POUSSE dans les murs, il est repousse — c'est juste, les anneaux tournent sur
## lui. Ce qui ne doit pas arriver, c'est que ce soit permanent.
## Et quand il POUSSE dans les murs ? Il ne passe pas — et ce n'est PAS un defaut de
## collision, c'est un fait de geometrie que personne n'avait calcule.
##
## ⚠️ LE COULOIR ENTRE LES DEUX MURS EST DEVENU UN LIEU — ET CETTE GARDE A CHANGE DE SENS.
##
## Elle affirmait le contraire, et elle avait raison de le faire : le chasseur est toujours
## aligne sur l'axe vertical (`LOI-SYS-07` : on vise en se deplacant, on ne pivote pas), donc
## radialement c'est son encombrement de capsule — 4,22 — qui doit tenir dans le couloir, et
## celui-ci en faisait 2,60. Elle constatait donc un fait de geometrie, en attendant qu'il
## soit tranche.
##
## Il l'a ete : « la physique ne marche pas du tout, c'est comme si tout le cercle etait un
## mur pour moi » (playtest du 2026-08-27). Un decor dans lequel on est convoye et ejecte
## n'est pas un decor, c'est un piege. Le mur exterieur passe donc a 8,05 — valeur MESUREE,
## la derive tombant a zero des que le couloir depasse 4,22 — et le plan de vol de la chambre
## s'elargit pour le loger.
##
## La garde tient desormais l'autre bout : le couloir doit rester UN LIEU. Si quelqu'un
## retrecit le mur ou allonge le chasseur, elle retombe.
func test_the_corridor_between_the_walls_is_a_place() -> void:
	var tuning: LeviathanTuning = load(SHIPPED)
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	var rings := tuning.reactor_rings
	assert_eq(rings.size(), 2, "deux murs")
	var inner: ReactorRing = rings[1] if rings[1].radius < rings[0].radius else rings[0]
	var outer: ReactorRing = rings[0] if rings[1].radius < rings[0].radius else rings[1]
	var corridor := (outer.radius - outer.thickness * 0.5) \
		- (inner.radius + inner.thickness * 0.5)
	var lengthwise := (stats.body_half_length + stats.body_radius) * 2.0
	assert_true(corridor >= lengthwise,
		"couloir de %.2f u pour un chasseur qui en occupe %.2f dans l'axe" % [corridor, lengthwise])

## ET IL Y RESTE. Le test precedent mesure ; celui-ci EPROUVE — c'est la difference entre
## « ca rentre sur le papier » et « on peut y voler ». Un chasseur pose immobile au milieu du
## couloir, les murs tournant pendant toute la plongee, ne doit pas bouger. Avec l'ancienne
## geometrie il derivait de 6,6 u vers la droite et finissait ejecte au plafond, sans qu'une
## seule commande soit donnee : les murs le CONVOYAIENT le long de leurs arcs.
func test_a_fighter_left_alone_in_the_corridor_stays_there() -> void:
	var tuning: LeviathanTuning = load(SHIPPED)
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	var rings := tuning.reactor_rings
	var inner: ReactorRing = rings[1] if rings[1].radius < rings[0].radius else rings[0]
	var outer: ReactorRing = rings[0] if rings[1].radius < rings[0].radius else rings[1]
	var milieu := ((outer.radius - outer.thickness * 0.5)
		+ (inner.radius + inner.thickness * 0.5)) * 0.5
	var up := Vector2(0.0, 1.0)
	var here := Vector2(0.0, -milieu)
	var depart := here
	var last_free := here
	var shapes := PlaneShapes.new()
	for i in int(tuning.dive_time * 60.0):
		shapes.clear()
		shapes.reserve(ReactorRings.shape_count(rings) + 1)
		ReactorRings.fill_shapes(shapes, rings, Vector2.ZERO, float(i) / 60.0)
		shapes.add_disc(Vector2.ZERO, tuning.flux_hitbox_radius)
		var next := PlaneCollider.slide_capsule(shapes, here, here, up,
			stats.body_half_length, stats.body_radius)
		if not PlaneCollider.capsule_blocks(shapes, next, up,
				stats.body_half_length, stats.body_radius):
			last_free = next
		else:
			var freed := PlaneCollider.resolve_capsule(shapes, next, up,
				stats.body_half_length, stats.body_radius, 5, last_free - next)
			if freed.distance_to(next) > 0.03:
				next = next.move_toward(freed, 9.0 / 60.0)
		here = next
	assert_true(here.distance_to(depart) < 0.5,
		"pose immobile dans le couloir, il a derive de %.2f u en %.0f s (arrivee %.2f, %.2f)"
			% [here.distance_to(depart), tuning.dive_time, here.x, here.y])

## Ce qui compte vraiment : il n'est ni pris au piege, ni EMPORTE. Le blindage tourne ; il ne
## doit pas emmener le chasseur avec lui.
func test_pushing_into_the_shield_never_carries_you_off() -> void:
	var run := _graze(false)
	var closest: float = run[3]
	var travelled: float = run[2]
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	assert_true(closest > stats.body_radius,
		"il n'est jamais aspire jusqu'au noyau (approche a %.2f)" % closest)
	assert_true(travelled < 60.0,
		("il est repousse, pas emporte : %.1f u parcourues en dix secondes alors qu'il "
			+ "poussait contre un mur") % travelled)
