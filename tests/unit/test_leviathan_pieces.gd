extends "res://tests/test_case.gd"
## LeviathanPlate et LeviathanSpike : les deux mecaniques neuves du boss final.
## Instanciables a la main — aucun arbre, aucune coque, aucun boss.

var _hits: int = 0

func _on_hit(_damage: float) -> void:
	_hits += 1

func _plate(index: int = 0) -> LeviathanPlate:
	# Quatre plaques a 90 deg : index 0 face camera, les autres derriere.
	return LeviathanPlate.make(index, TAU * index / 4.0, 3200.0, 1.30, Callable(self, "_on_hit"))

func _spike(role: int = LeviathanSpike.Role.CHARGER) -> LeviathanSpike:
	return LeviathanSpike.make(0, role, 0.0, 1500.0, 0.90, Callable(self, "_on_hit"))

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

# --- LeviathanSpike : quatre roles, un dilemme ----------------------------

func test_the_four_spikes_take_four_distinct_roles() -> void:
	# Deux fonceuses feraient perdre a la phase son dilemme.
	var roles := {}
	for i in 4:
		roles[LeviathanSpike.role_for(i)] = true
	assert_eq(roles.size(), 4, "quatre roles distincts sur quatre epines")

func test_a_spike_starts_attached_and_is_not_a_target_yet() -> void:
	var spike := _spike()
	assert_eq(spike.state, LeviathanSpike.State.ATTACHED, "sur le corps au depart")
	assert_false(spike.is_free(), "et pas encore autonome")

func test_detaching_opens_a_transition_before_autonomy() -> void:
	var spike := _spike()
	spike.detach(Vector2(3.0, 5.0))
	assert_eq(spike.state, LeviathanSpike.State.DETACHING, "elle s'arrache")
	assert_false(spike.is_free(), "pas encore autonome pendant l'arrachement")
	assert_true(spike.target.enabled, "mais deja touchable")
	spike.tick(1.0, 0.6)
	assert_true(spike.is_free(), "puis elle vole seule")

func test_a_spike_cannot_detach_twice() -> void:
	var spike := _spike()
	spike.detach(Vector2(1.0, 1.0))
	spike.tick(1.0, 0.6)
	spike.detach(Vector2(9.0, 9.0))
	assert_true(spike.is_free(), "un second detachement ne la renvoie pas en arrachement")
	assert_eq(spike.plane_position, Vector2(1.0, 1.0), "et ne la teleporte pas")

func test_the_blocker_places_itself_between_the_player_and_the_core() -> void:
	# C'est elle qui cree le dilemme de la phase : frapper ou nettoyer.
	var spike := _spike(LeviathanSpike.Role.BLOCKER)
	var core := Vector2(0.0, 5.0)
	var player := Vector2(0.0, -3.0)
	var want := spike.desired_position(core, player, 2.5, 3.0, 0.0)
	assert_almost_eq(want.x, 0.0, 0.001, "alignee sur l'axe joueur-noyau")
	assert_almost_eq(want.y, 2.5, 0.001, "a blocker_offset du noyau, du cote du joueur")

func test_the_blocker_does_not_divide_by_zero_on_top_of_the_core() -> void:
	var spike := _spike(LeviathanSpike.Role.BLOCKER)
	var core := Vector2(0.0, 5.0)
	var want := spike.desired_position(core, core, 2.5, 3.0, 0.0)
	assert_eq(want, core, "joueur pile sur le noyau : pas de direction, pas de NaN")
	assert_false(is_nan(want.x) or is_nan(want.y), "et surtout pas un NaN")

func test_the_escort_orbits_the_core_at_its_radius() -> void:
	var spike := _spike(LeviathanSpike.Role.ESCORT)
	var core := Vector2(0.0, 5.0)
	for age in [0.0, 1.3, 4.7]:
		var want := spike.desired_position(core, Vector2.ZERO, 2.5, 3.0, age)
		assert_almost_eq(want.distance_to(core), 3.0, 0.001, "toujours a escort_radius du noyau")

func test_the_charger_locks_its_point_at_the_start_of_the_wind_up() -> void:
	# Une fonceuse qui suit sa cible pendant le telegraphe est imparable.
	var spike := _spike(LeviathanSpike.Role.CHARGER)
	var core := Vector2(0.0, 5.0)
	spike.begin_charge(Vector2(6.0, -2.0))
	var want := spike.desired_position(core, Vector2(-9.0, -7.0), 2.5, 3.0, 0.0)
	assert_eq(want, Vector2(6.0, -2.0), "elle fonce sur le point VERROUILLE, pas sur le joueur")

func test_a_charger_at_rest_returns_to_the_core() -> void:
	var spike := _spike(LeviathanSpike.Role.CHARGER)
	var core := Vector2(0.0, 5.0)
	spike.begin_charge(Vector2(6.0, -2.0))
	spike.end_charge()
	assert_eq(spike.desired_position(core, Vector2(-9.0, -7.0), 2.5, 3.0, 0.0), core,
		"charge terminee, elle revient sur le noyau")

func test_killing_a_spike_reports_once_and_releases_its_target() -> void:
	var spike := _spike()
	assert_false(spike.apply_damage(750.0), "encore debout a mi-vie")
	assert_true(spike.apply_damage(750.0), "le frame ou elle tombe")
	assert_false(spike.apply_damage(750.0), "et pas une fois de plus")
	assert_false(spike.is_alive(), "morte")
	assert_false(spike.target.enabled, "cible retiree avec elle")

func test_health_ratios_are_safe_at_zero_max() -> void:
	var plate := LeviathanPlate.make(0, 0.0, 0.0, 1.0, Callable(self, "_on_hit"))
	var spike := LeviathanSpike.make(0, LeviathanSpike.Role.GUNNER, 0.0, 0.0, 1.0, Callable(self, "_on_hit"))
	assert_almost_eq(plate.health_ratio(), 0.0, 0.001, "aucune division par zero")
	assert_almost_eq(spike.health_ratio(), 0.0, 0.001, "aucune division par zero")
