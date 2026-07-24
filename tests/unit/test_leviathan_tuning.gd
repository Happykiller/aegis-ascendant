extends "res://tests/test_case.gd"
## LeviathanTuning : les invariants qui empechent un reglage sensé pièce par pièce de
## produire un combat injouable. Chaque test correspond a une panne SILENCIEUSE —
## celles ou aucune valeur prise separement n'a l'air fausse.

func _tuning() -> LeviathanTuning:
	return LeviathanTuning.new()   # les valeurs par defaut sont les valeurs retenues

func test_the_shipped_values_validate() -> void:
	var errors := _tuning().validate()
	assert_eq(errors.size(), 0, "reglages par defaut valides, sinon : %s" % ", ".join(errors))

# --- Invariant 1 : la fenetre de la phase 1 -------------------------------

func test_the_phase_one_window_comes_from_the_geometry() -> void:
	var t := _tuning()
	# 12 s de tour x 100 deg / 360 = 3,33 s d'atteignabilite par passage.
	assert_almost_eq(t.plate_window(), 12.0 * 100.0 / 360.0, 0.001,
		"la fenetre est un arc parcouru, pas un minuteur")
	assert_true(t.plate_window() >= t.min_window, "et elle est exploitable")

func test_too_narrow_an_arc_is_refused() -> void:
	# Le piege : 12 s et 20 deg sont deux nombres parfaitement sensés isolement.
	var t := _tuning()
	t.plate_arc_deg = 20.0
	var errors := t.validate()
	assert_true(errors.size() > 0, "0,67 s d'atteignabilite : le joueur regarde passer")
	assert_true(errors[0].contains("window"), "et l'erreur nomme la fenetre : %s" % errors[0])

func test_a_slower_orbit_widens_the_window() -> void:
	var t := _tuning()
	t.plate_arc_deg = 20.0
	t.shell_orbit_period = 60.0   # 3,33 s a nouveau
	assert_eq(t.validate().size(), 0, "l'arc etroit passe si l'orbite ralentit d'autant")

# --- Invariants 2 et 3 : l'aspiration -------------------------------------

func test_phase_two_must_leave_the_player_able_to_flee() -> void:
	var t := _tuning()
	t.pull_speed_max = 15.0   # au-dela des 14 du chasseur
	var errors := t.validate()
	assert_true(errors.size() > 0, "aspire quoi qu'il fasse : la phase devient une cinematique")
	assert_true(errors[0].contains("phase 2"), "erreur explicite : %s" % errors[0])

func test_escapable_but_unplayable_is_also_refused() -> void:
	# 13,9 contre 14,0 : fuyable sur le papier, on avance a un dixieme d'unite par
	# seconde. C'est le reglage qui passe une revue et rate en jeu.
	var t := _tuning()
	t.pull_speed_max = 13.9
	var errors := t.validate()
	assert_true(errors.size() > 0, "il faut de la mobilite, pas seulement une echappatoire")
	assert_true(errors[0].contains("unplayable"), "erreur explicite : %s" % errors[0])

func test_phase_four_must_NOT_be_resistible() -> void:
	# C'est le sujet de la phase : on n'y resiste plus, on entre.
	var t := _tuning()
	t.pull_speed_max_final = 10.0
	var errors := t.validate()
	assert_true(errors.size() > 0, "une phase 4 fuyable n'a plus de course")
	assert_true(errors[0].contains("phase 4"), "erreur explicite : %s" % errors[0])

func test_the_two_pull_settings_pull_in_opposite_directions() -> void:
	var t := _tuning()
	assert_true(t.pull_speed_max < t.reference_player_max_speed, "phase 2 : on resiste")
	assert_true(t.pull_speed_max_final > t.reference_player_max_speed, "phase 4 : on n'y resiste plus")

# --- Invariant 4 : le coeur est abattable avec de la marge ----------------

func test_the_heart_falls_well_inside_the_countdown() -> void:
	var t := _tuning()
	var kill := t.heart_health / t.reference_dps
	assert_true(kill <= t.maw_open_time * 0.7,
		"%.1f s de tir utile dans une fenetre de %.1f s : il reste de la marge" % [kill, t.maw_open_time])

func test_a_heart_that_needs_a_perfect_dive_is_refused() -> void:
	var t := _tuning()
	t.heart_health = 4800.0   # 11,4 s pour une fenetre de 12
	var errors := t.validate()
	assert_true(errors.size() > 0, "sans marge d'erreur, la phase 4 devient aleatoire")
	assert_true(errors[0].contains("heart"), "erreur explicite : %s" % errors[0])

func test_the_exit_window_cannot_swallow_the_dive() -> void:
	var t := _tuning()
	t.eject_window = 15.0
	assert_true(t.validate().size() > 0, "la sortie s'ouvrirait avant meme la descente")

# --- Invariant 5 : les telegraphes ----------------------------------------

func test_every_heavy_attack_keeps_its_wind_up() -> void:
	var t := _tuning()
	for field in ["lance_windup_time", "charger_windup", "spike_sweep_windup"]:
		var fresh := _tuning()
		fresh.set(field, 0.0)
		var errors := fresh.validate()
		assert_true(errors.size() > 0, "%s a zero rend l'attaque imparable" % field)

func test_a_missile_that_turns_too_fast_is_refused() -> void:
	# Un projectile qui vire plus vite qu'un demi-tour par seconde touche toujours.
	var t := _tuning()
	t.missile_turn_rate = 4.0
	assert_true(t.validate().size() > 0, "au-dela de PI rad/s, il n'est plus esquivable")

# --- Invariant 6 : occupation et durees -----------------------------------

func test_phase_durations_land_in_the_intended_range() -> void:
	var t := _tuning()
	# Coupe de playtest (ADR-0019) : ~20 s par phase de brisure, phase 4 tres courte.
	# L'ancien 65-75 / 55-65 / 50-60 s etait injouable — l'operateur abandonnait avant la fin.
	assert_true(t.phase_duration(0) > 15.0 and t.phase_duration(0) < 25.0,
		"phase 1 : %.1f s" % t.phase_duration(0))
	assert_true(t.phase_duration(1) > 15.0 and t.phase_duration(1) < 25.0,
		"phase 2 : %.1f s" % t.phase_duration(1))
	assert_true(t.phase_duration(2) > 15.0 and t.phase_duration(2) < 25.0,
		"phase 3 : %.1f s" % t.phase_duration(2))
	assert_true(t.phase_duration(3) < 10.0, "phase 4 : %.1f s de tir utile" % t.phase_duration(3))

func test_the_whole_fight_lands_around_a_minute_and_a_bit() -> void:
	var t := _tuning()
	var total := 0.0
	for phase in 4:
		total += t.phase_duration(phase)
	# ADR-0019 acte ~67 s, ce qui CONTREDIT la spec §7 (« 3 a 4 min ») : decision de
	# playtest, un ADR prime sur la spec. L'ancien ~3 min etait injouable.
	assert_true(total > 55.0 and total < 85.0,
		"ADR-0019 vise ~67 s de combat net ; obtenu %.0f s" % total)

func test_an_impossible_occupancy_is_refused() -> void:
	var t := _tuning()
	t.occupancy_phase_2 = 0.0
	assert_true(t.validate().size() > 0, "une occupation nulle rend la duree infinie")
	var u := _tuning()
	u.occupancy_phase_3 = 1.4
	assert_true(u.validate().size() > 0, "et au-dela de 1 elle n'a plus de sens")

func test_total_structure_is_the_sum_of_the_phases() -> void:
	# C'est ce que la jauge du HUD divise : elle doit couvrir TOUT le combat, sinon
	# elle se fige pendant une phase entiere et dit au joueur qu'il ne fait rien.
	var t := _tuning()
	var sum := 0.0
	for phase in 4:
		sum += t.phase_health(phase)
	assert_almost_eq(t.total_structure(), sum, 0.001, "la jauge couvre les quatre phases")
	# Coupe de playtest (ADR-0019) : ~12 650 PV, contre ~33 000 avant. La jauge doit
	# quand meme couvrir de quoi ne pas se figer sur une phase entiere.
	assert_true(t.total_structure() > 12000.0, "environ 12 650 PV de structures au total")

func test_the_final_boss_demands_more_than_the_mini_boss_in_time_and_rules() -> void:
	# RECADRE apres la coupe de playtest (ADR-0019). Le boss final n'est plus « plus gros »
	# en PV bruts (~12 650, soit ~1,1x le Harvester) : il l'est par sa DUREE et sa VARIETE.
	# Le Harvester est un cycle unique repete ; le Leviathan enchaine quatre regles
	# distinctes (BRISER / RESISTER / PRIORISER / OSER) sur ~67 s.
	var t := _tuning()
	var total := 0.0
	for phase in 4:
		total += t.phase_duration(phase)
	assert_true(total > 60.0, "au moins une minute de combat net, sur quatre regles : %.0f s" % total)

# --- Garde-fous de base ---------------------------------------------------

func test_a_zeroed_health_pool_is_refused() -> void:
	var t := _tuning()
	t.node_health = 0.0
	assert_true(t.validate().size() > 0, "une cible a zero PV tombe avant d'exister")

func test_a_zeroed_cadence_is_refused() -> void:
	var t := _tuning()
	t.fan_interval = 0.0
	assert_true(t.validate().size() > 0, "une cadence nulle tire une infinite de balles par image")
