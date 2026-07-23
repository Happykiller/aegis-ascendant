extends "res://tests/test_case.gd"
## GravityWell : le champ d'aspiration de la phase 2 du Pale Leviathan.
## Fonctions pures — le comportement se vérifie sans arbre, sans coque et sans boss.

const PLAYER_MAX_SPEED := 14.0   # resources/data/player_stats.gd
const RADIUS := 16.0
const SPEED_MAX := 7.0           # le réglage retenu (§7.4 du document de conception)

func test_pull_is_maximal_at_the_centre_and_null_at_the_edge() -> void:
	assert_almost_eq(GravityWell.speed_at(0.0, RADIUS, SPEED_MAX), SPEED_MAX, 0.001,
		"au centre, le champ tire a pleine vitesse")
	assert_almost_eq(GravityWell.speed_at(RADIUS, RADIUS, SPEED_MAX), 0.0, 0.001,
		"au bord, le champ ne tire plus")
	assert_almost_eq(GravityWell.speed_at(RADIUS * 0.5, RADIUS, SPEED_MAX), SPEED_MAX * 0.5, 0.001,
		"le profil est lineaire entre les deux")

func test_pull_never_exceeds_its_maximum_outside_the_radius() -> void:
	# Un champ non borne au-dela de sa portee aspirerait le joueur depuis le bord de
	# l'ecran, ou rien ne l'annonce.
	for distance in [RADIUS + 0.1, RADIUS * 2.0, 100.0]:
		assert_almost_eq(GravityWell.speed_at(distance, RADIUS, SPEED_MAX), 0.0, 0.001,
			"hors de portee, aucune aspiration")

func test_pull_points_toward_the_centre() -> void:
	var centre := Vector2(0.0, 5.0)
	var pull := GravityWell.pull_at(Vector2(4.0, 5.0), centre, RADIUS, SPEED_MAX)
	assert_true(pull.x < 0.0, "un joueur a tribord est tire vers babord")
	assert_almost_eq(pull.y, 0.0, 0.001, "et pas devie verticalement")
	var up := GravityWell.pull_at(Vector2(0.0, 1.0), centre, RADIUS, SPEED_MAX)
	assert_true(up.y > 0.0, "un joueur en dessous est tire vers le haut")

func test_the_centre_itself_does_not_produce_a_nan() -> void:
	# Normaliser un vecteur nul rend NaN, qui se propagerait dans la position du joueur
	# jusqu'a le faire disparaitre — sans une seule erreur au journal.
	var pull := GravityWell.pull_at(Vector2(2.0, 3.0), Vector2(2.0, 3.0), RADIUS, SPEED_MAX)
	assert_eq(pull, Vector2.ZERO, "pile au centre, aucune direction : vecteur nul")
	assert_false(is_nan(pull.x) or is_nan(pull.y), "et surtout pas un NaN")

func test_a_null_radius_is_inert_rather_than_a_division_by_zero() -> void:
	assert_almost_eq(GravityWell.speed_at(1.0, 0.0, SPEED_MAX), 0.0, 0.001,
		"portee nulle = champ eteint, pas une division par zero")

func test_each_node_gives_back_a_share_of_the_mobility() -> void:
	assert_almost_eq(GravityWell.speed_max_after(SPEED_MAX, 0, 3), SPEED_MAX, 0.001,
		"trois noeuds debout : le champ est entier")
	assert_almost_eq(GravityWell.speed_max_after(SPEED_MAX, 1, 3), SPEED_MAX * 2.0 / 3.0, 0.001,
		"un noeud abattu retire un tiers")
	assert_almost_eq(GravityWell.speed_max_after(SPEED_MAX, 3, 3), 0.0, 0.001,
		"les trois abattus : l'aspiration tombe a zero")

func test_relief_is_clamped_rather_than_going_negative() -> void:
	# Un compteur qui derape ne doit pas produire une aspiration REPULSIVE.
	assert_almost_eq(GravityWell.speed_max_after(SPEED_MAX, 9, 3), 0.0, 0.001,
		"plus de noeuds abattus que de noeuds : zero, jamais un signe inverse")

func test_phase_two_leaves_the_player_room_to_dodge() -> void:
	# L'invariant central : sans lui la phase 2 devient une cinematique.
	assert_true(GravityWell.escapes(SPEED_MAX, PLAYER_MAX_SPEED),
		"a 7 u/s contre 14, le joueur peut encore fuir")
	assert_true(GravityWell.leaves_room(SPEED_MAX, PLAYER_MAX_SPEED),
		"et il lui reste assez de mobilite pour jouer")

func test_a_field_faster_than_the_player_is_rejected() -> void:
	assert_false(GravityWell.escapes(PLAYER_MAX_SPEED, PLAYER_MAX_SPEED),
		"a egalite, le joueur ne fuit deja plus")
	assert_false(GravityWell.escapes(16.0, PLAYER_MAX_SPEED),
		"le reglage de la phase 4 n'est pas fuyable — c'est son sujet")

func test_a_field_that_is_escapable_can_still_be_unplayable() -> void:
	# 13,9 contre 14,0 : techniquement fuyable, on avance a un dixieme d'unite par
	# seconde. C'est exactement le reglage qui passe une revue et rate en jeu.
	assert_true(GravityWell.escapes(13.9, PLAYER_MAX_SPEED), "fuyable sur le papier")
	assert_false(GravityWell.leaves_room(13.9, PLAYER_MAX_SPEED), "mais injouable en fait")

func test_pure_and_deterministic() -> void:
	var a := GravityWell.pull_at(Vector2(3.0, 1.0), Vector2(0.0, 5.0), RADIUS, SPEED_MAX)
	var b := GravityWell.pull_at(Vector2(3.0, 1.0), Vector2(0.0, 5.0), RADIUS, SPEED_MAX)
	assert_eq(a, b, "memes entrees -> meme sortie")
