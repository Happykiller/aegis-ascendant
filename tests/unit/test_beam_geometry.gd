extends "res://tests/test_case.gd"
## Portée du faisceau du canon (`Beam.hits`).
##
## POURQUOI CE TEST — le faisceau ne tire aucune balle : ses dégâts ne passent donc
## par AUCUN chemin déjà couvert par `test_bullet_collision.gd`. Sans ce test, la
## seule façon de savoir où il touche serait de se placer devant le canon en jeu et
## d'espérer que le tir parte au bon moment.
##
## Fonction statique et pure : ni nœud, ni rendu, ni arbre.

const HALF_WIDTH := 0.55
const PROBE := 0.25

func test_a_point_on_the_axis_is_hit() -> void:
	assert_true(Beam.hits(Vector2.ZERO, Vector2(0.0, -10.0), HALF_WIDTH,
		Vector2(0.0, -5.0), PROBE), "dead centre of the beam")

func test_a_point_just_inside_the_edge_is_hit() -> void:
	# Le bord effectif est `demi-largeur + rayon du joueur` = 0,80.
	assert_true(Beam.hits(Vector2.ZERO, Vector2(0.0, -10.0), HALF_WIDTH,
		Vector2(0.78, -5.0), PROBE), "grazed, but grazed is hit")

func test_a_point_just_outside_the_edge_is_spared() -> void:
	assert_false(Beam.hits(Vector2.ZERO, Vector2(0.0, -10.0), HALF_WIDTH,
		Vector2(0.85, -5.0), PROBE), "a hair outside is a dodge")

## ⚠️ LE PIÈGE. Sans borner le paramètre de projection à [0, 1], le calcul porte sur
## la DROITE INFINIE : un joueur placé derrière la bouche du canon serait touché par
## un tir qui part dans l'autre sens.
func test_a_point_behind_the_muzzle_is_never_hit() -> void:
	assert_false(Beam.hits(Vector2.ZERO, Vector2(0.0, -10.0), HALF_WIDTH,
		Vector2(0.0, 3.0), PROBE), "the beam does not fire backwards")

func test_a_point_beyond_the_far_end_is_never_hit() -> void:
	assert_false(Beam.hits(Vector2.ZERO, Vector2(0.0, -10.0), HALF_WIDTH,
		Vector2(0.0, -12.0), PROBE), "the beam has a length, not an infinite reach")

func test_the_beam_works_at_any_angle() -> void:
	var from := Vector2(-3.0, 5.0)
	var to := Vector2(6.0, -4.0)
	var mid := (from + to) * 0.5
	assert_true(Beam.hits(from, to, HALF_WIDTH, mid, PROBE), "hit on a diagonal beam")
	# Décalé perpendiculairement de bien plus que la portée.
	var normal := (to - from).orthogonal().normalized()
	assert_false(Beam.hits(from, to, HALF_WIDTH, mid + normal * 3.0, PROBE),
		"spared beside a diagonal beam")

## Un faisceau de longueur nulle ne doit ni planter ni toucher tout l'écran : c'est
## l'état d'une image où la bouche et la cible coïncident.
func test_a_degenerate_beam_does_not_reach_the_whole_screen() -> void:
	assert_true(Beam.hits(Vector2.ZERO, Vector2.ZERO, HALF_WIDTH, Vector2(0.1, 0.0), PROBE),
		"a point-blank beam still touches what sits on it")
	assert_false(Beam.hits(Vector2.ZERO, Vector2.ZERO, HALF_WIDTH, Vector2(9.0, 0.0), PROBE),
		"but it does not reach across the field")
