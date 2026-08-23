extends "res://tests/test_case.gd"
## LeviathanPlate : l'armure du boss final, et la geometrie qui decide de sa vulnerabilite.
##
## ⚠️ `LeviathanSpike` a disparu avec la refonte (ADR-0020) : les epines ne sont plus des
## cibles autonomes avec des roles, seulement des pieces qui se detachent quand l'armure
## cede. Ses treize tests sont partis avec elle — garder des tests verts sur du code que
## plus rien n'appelle donne l'illusion d'une couverture.
## Instanciables a la main — aucun arbre, aucune coque, aucun boss.

var _hits: int = 0

func _on_hit(_damage: float) -> void:
	_hits += 1

func _plate(index: int = 0) -> LeviathanPlate:
	# Quatre plaques a 90 deg : index 0 face camera, les autres derriere.
	return LeviathanPlate.make(index, TAU * index / 4.0, 3200.0, 1.30, Callable(self, "_on_hit"))


# --- LeviathanPlate : la fenetre nait d'une geometrie ----------------------

func test_only_the_plate_facing_the_player_can_be_hit() -> void:
	var front := _plate(0)
	var back := _plate(2)   # a 180 deg
	assert_true(front.is_exposed(0.0, 100.0), "la plaque face camera encaisse")
	assert_false(back.is_exposed(0.0, 100.0), "celle qui est derriere est masquee par le corps")

func test_the_orbit_brings_each_plate_into_the_arc_in_turn() -> void:
	var plate := _plate(2)   # commence derriere
	assert_false(plate.is_exposed(0.0, 100.0), "derriere au depart")
	assert_true(plate.is_exposed(PI, 100.0), "un demi-tour de coquille plus tard, elle est devant")

func test_the_arc_is_a_total_width_not_a_half_width() -> void:
	# Se tromper la-dessus doublerait silencieusement la fenetre de tir de la phase.
	var plate := _plate(0)
	# Arc de 100 deg = +/- 50 deg.
	assert_true(plate.is_exposed(deg_to_rad(49.0), 100.0), "a 49 deg du centre, encore dans l'arc")
	assert_false(plate.is_exposed(deg_to_rad(51.0), 100.0), "a 51 deg, dehors")

func test_the_arc_wraps_around_the_circle() -> void:
	# Un arc qui ne gere pas le passage par PI cree un angle mort qui ne se voit
	# qu'apres plusieurs tours de coquille.
	var plate := _plate(0)
	assert_true(plate.is_exposed(TAU, 100.0), "un tour complet ramene la plaque au meme endroit")
	assert_true(plate.is_exposed(-TAU, 100.0), "et dans l'autre sens aussi")

func test_a_fallen_plate_is_never_exposed_again() -> void:
	# Rien ne repousse : c'est le pilier du combat.
	var plate := _plate(0)
	plate.apply_damage(9999.0)
	assert_false(plate.is_exposed(0.0, 100.0), "abattue, elle ne revient pas dans l'arc")
	assert_false(plate.is_up(), "et elle ne protege plus le corps")

func test_destroying_a_plate_reports_the_kill_exactly_once() -> void:
	var plate := _plate(0)
	assert_false(plate.apply_damage(1600.0), "encore debout a mi-vie")
	assert_true(plate.apply_damage(1600.0), "le frame ou elle tombe")
	assert_false(plate.apply_damage(1600.0), "et pas une fois de plus par balle de la salve")

func test_a_fallen_plate_releases_its_bullet_target() -> void:
	var plate := _plate(0)
	plate.apply_damage(9999.0)
	assert_false(plate.target.enabled, "sinon c'est un mur invisible qui mange les balles")

func test_the_fall_runs_to_completion_then_rests() -> void:
	var plate := _plate(0)
	plate.apply_damage(9999.0)
	assert_almost_eq(plate.fall_ratio(1.0), 0.0, 0.001, "la chute part de zero")
	plate.tick(0.5, 1.0)
	assert_almost_eq(plate.fall_ratio(1.0), 0.5, 0.001, "a mi-chute")
	plate.tick(0.6, 1.0)
	assert_eq(plate.state, LeviathanPlate.State.DOWN, "puis elle pend")
	assert_almost_eq(plate.fall_ratio(1.0), 1.0, 0.001, "et y reste")

func test_an_intact_plate_has_not_begun_to_fall() -> void:
	assert_almost_eq(_plate(0).fall_ratio(1.0), 0.0, 0.001, "aucune chute tant qu'elle vit")
