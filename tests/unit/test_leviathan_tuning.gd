extends "res://tests/test_case.gd"
## LeviathanTuning : les invariants qui empechent un reglage sensé pièce par pièce de
## produire un combat injouable. Chaque test correspond a une panne SILENCIEUSE — celles
## ou aucune valeur prise separement n'a l'air fausse.
##
## REFONTE ADR-0021 — le combat est devenu CYCLIQUE : trois tours d'armure, trois
## plongees dans le noyau, une plaque de moins a chaque fois. Deux invariants neufs
## gardent ce que le playtest a du decouvrir a la main : que le flux tombe au dernier
## passage (ni avant, ni jamais), et que l'arc d'exposition suive la perte des plaques.

func _tuning() -> LeviathanTuning:
	return LeviathanTuning.new()   # les valeurs par defaut sont les valeurs retenues

func test_the_shipped_values_validate() -> void:
	var errors := _tuning().validate()
	assert_eq(errors.size(), 0, "reglages par defaut valides, sinon : %s" % ", ".join(errors))

# --- La structure en cycles -----------------------------------------------

func test_each_cycle_costs_the_boss_one_plate() -> void:
	var t := _tuning()
	assert_eq(t.plates_for_cycle(0), 4, "cycle 1 : l'armure complete")
	assert_eq(t.plates_for_cycle(1), 3, "cycle 2 : elle se reforme moins bien")
	assert_eq(t.plates_for_cycle(2), 2, "cycle 3 : le boss ne couvre presque plus rien")

func test_the_armour_never_falls_below_its_floor() -> void:
	# Sans plancher, un cycle de trop laisserait zero plaque : la phase d'armure durerait
	# zero seconde et le combat deviendrait une suite de plongees.
	var t := _tuning()
	assert_eq(t.plates_for_cycle(9), t.plate_count_min, "le plancher tient, meme hors cycles prevus")
	assert_true(t.plate_count_min >= 1, "il reste toujours quelque chose a briser")

func test_each_cycle_is_shorter_than_the_one_before() -> void:
	# C'est ce qui fait SENTIR qu'on gagne, sans qu'aucun texte ne l'explique.
	var t := _tuning()
	for cycle in range(1, t.cycle_count):
		assert_true(t.armor_duration(cycle) < t.armor_duration(cycle - 1),
			"cycle %d (%.1f s) plus court que le precedent (%.1f s)"
				% [cycle + 1, t.armor_duration(cycle), t.armor_duration(cycle - 1)])

# --- INVARIANT 1 : le temps 1 offre toujours une cible --------------------

func test_the_arc_widens_as_plates_are_lost() -> void:
	# ⚠️ LE PIEGE QUE CET INVARIANT GARDE. Quatre plaques sont espacees de 90 deg, trois de
	# 120, deux de 180. Un arc fixe de 100 deg marche au premier cycle et laisse, des le
	# deuxieme, des instants ou AUCUNE plaque n'est atteignable — le joueur tire dans le
	# vide sans qu'aucune erreur ni aucun test ne le signale.
	var t := _tuning()
	assert_almost_eq(t.effective_arc_deg(4), 100.0, 0.001, "quatre plaques : l'arc de base suffit")
	assert_almost_eq(t.effective_arc_deg(3), 120.0, 0.001, "trois plaques : il s'elargit")
	assert_almost_eq(t.effective_arc_deg(2), 180.0, 0.001, "deux plaques : la moitie du tour")

func test_every_cycle_keeps_a_reachable_plate() -> void:
	var t := _tuning()
	for cycle in t.cycle_count:
		var alive := t.plates_for_cycle(cycle)
		assert_true(t.effective_arc_deg(alive) >= 360.0 / float(alive),
			"cycle %d : %d plaques, arc %.0f deg" % [cycle + 1, alive, t.effective_arc_deg(alive)])

func test_an_orbit_too_fast_for_the_window_is_refused() -> void:
	var t := _tuning()
	t.shell_orbit_period = 3.0   # 0,83 s par passage
	var errors := t.validate()
	assert_true(errors.size() > 0, "la plaque defile trop vite pour etre traitee")
	assert_true(errors[0].contains("window"), "erreur explicite : %s" % errors[0])

# --- INVARIANT 2 : l'aspiration accompagne, elle ne pilote pas ------------

func test_the_pull_must_leave_the_player_able_to_flee() -> void:
	var t := _tuning()
	t.pull_speed_max = 15.0   # au-dela des 14 du chasseur
	var errors := t.validate()
	assert_true(errors.size() > 0, "aspire quoi qu'il fasse : l'entree devient une cinematique")
	assert_true(errors[0].contains("dive pull"), "erreur explicite : %s" % errors[0])

func test_escapable_but_unplayable_is_also_refused() -> void:
	# 13,9 contre 14,0 : fuyable sur le papier, on avance a un dixieme d'unite par
	# seconde. C'est le reglage qui passe une revue et rate en jeu.
	var t := _tuning()
	t.pull_speed_max = 13.9
	var errors := t.validate()
	assert_true(errors.size() > 0, "il faut de la mobilite, pas seulement une echappatoire")
	assert_true(errors[0].contains("unplayable"), "erreur explicite : %s" % errors[0])

# --- INVARIANT 3 : le combat tient sa duree -------------------------------

func test_the_whole_fight_lands_on_its_promise() -> void:
	var t := _tuning()
	assert_almost_eq(t.total_duration(), 40.0, 2.0,
		"~40 s de combat net ; obtenu %.1f s" % t.total_duration())

func test_a_fight_that_drifts_long_is_refused() -> void:
	# LE GARDE-FOU QUI MANQUAIT. Chaque valeur peut rester sensee pendant que le combat
	# derive vers trois minutes : c'est arrive deux fois, et il a fallu un playtest a
	# chaque fois pour le voir.
	var t := _tuning()
	t.cycle_count = 12
	var errors := t.validate()
	assert_true(errors.size() > 0, "douze cycles allongent le combat sans qu'une valeur ait l'air fausse")
	var named := false
	for error in errors:
		if error.contains("fight lasts"):
			named = true
	assert_true(named, "et l'erreur nomme la duree : %s" % ", ".join(errors))

func test_a_fight_that_drifts_short_is_refused_too() -> void:
	var t := _tuning()
	t.cycle_count = 1
	t.plate_health = 50.0
	assert_true(t.validate().size() > 0, "un boss final expedie en dix secondes n'est pas un final")

# --- INVARIANT 4 : les deux temps se partagent le combat ------------------

func test_neither_beat_swallows_the_fight() -> void:
	var t := _tuning()
	var share := t.armor_share()
	assert_true(share >= 0.25 and share <= 0.75,
		"briser l'armure occupe %.0f%% du combat" % (share * 100.0))

func test_an_armour_that_swallows_the_fight_is_refused() -> void:
	# Une plongee anecdotique au bout d'une armure interminable, c'est exactement le
	# combat que le playtest a rejete comme « lancinant ».
	var t := _tuning()
	t.plate_health = 4000.0
	var errors := t.validate()
	assert_true(errors.size() > 0, "l'armure ne peut pas devenir tout le combat")

# --- INVARIANT 5 : le flux tombe au dernier passage -----------------------

func test_the_flux_falls_on_the_last_dive_not_before() -> void:
	# Serre exprès : le dernier plongeon doit se jouer. Trop mou, le boss meurt au premier
	# passage et les cycles ne servent a rien ; trop dur, le joueur repart pour un tour de
	# plus a chaque fois sans comprendre pourquoi.
	var t := _tuning()
	var reachable := t.reference_dps * t.occupancy_dive * t.dive_time
	assert_true(t.flux_damage_per_dive() <= reachable,
		"%.0f PV a placer par plongee, %.0f atteignables" % [t.flux_damage_per_dive(), reachable])
	assert_true(t.flux_damage_per_dive() > reachable * 0.55,
		"et il ne tombe pas au premier passage : %.0f contre %.0f" % [t.flux_damage_per_dive(), reachable])

func test_a_flux_too_tough_for_its_dives_is_refused() -> void:
	var t := _tuning()
	t.flux_health = 40000.0
	var errors := t.validate()
	assert_true(errors.size() > 0, "un flux increvable rend les cycles infinis")

func test_a_flux_that_dies_on_the_first_dive_is_refused() -> void:
	var t := _tuning()
	t.flux_health = 300.0
	var errors := t.validate()
	assert_true(errors.size() > 0, "un flux de verre supprime les cycles qu'on vient d'ecrire")

# --- INVARIANT 6 : les telegraphes ----------------------------------------

func test_the_spine_beam_keeps_its_wind_up() -> void:
	var t := _tuning()
	t.spine_windup_time = 0.0
	assert_true(t.validate().size() > 0, "sans rearme, le laser devient un impot")

func test_a_wind_up_shorter_than_the_beam_is_refused() -> void:
	# Un telegraphe deux fois plus court que le tir se lit comme un clignotement, pas
	# comme un avertissement.
	var t := _tuning()
	t.spine_windup_time = 0.2
	t.spine_beam_time = 1.2
	var errors := t.validate()
	assert_true(errors.size() > 0, "le telegraphe doit etre lisible, pas une formalite")

func test_a_missile_that_turns_too_fast_is_refused() -> void:
	var t := _tuning()
	t.missile_turn_rate = 4.0
	assert_true(t.validate().size() > 0, "au-dela de PI rad/s, il n'est plus esquivable")

# --- Lectures derivees ----------------------------------------------------

func test_the_dive_is_short_on_purpose() -> void:
	# « On n'aurait pas enormement de temps pour tirer dessus avant d'etre a nouveau
	# ejecte » : le sejour dans le noyau est la recompense, pas le combat.
	var t := _tuning()
	assert_true(t.dive_time <= 6.0, "%.1f s de tir dans le noyau" % t.dive_time)
	assert_true(t.dive_duration() > t.dive_time, "entree et ejection comptent aussi")

func test_total_structure_covers_every_cycle_and_the_flux() -> void:
	var t := _tuning()
	var sum := t.flux_health
	for cycle in t.cycle_count:
		sum += t.plate_health * float(t.plates_for_cycle(cycle))
	assert_almost_eq(t.total_structure(), sum, 0.001, "toutes les armures, plus le flux")

func test_the_final_boss_still_outlasts_the_mini_boss() -> void:
	var t := _tuning()
	assert_true(t.total_duration() > 30.0,
		"au-dessus du mini-boss (~30 s) : %.0f s" % t.total_duration())

# --- Garde-fous de base ---------------------------------------------------

func test_a_zeroed_health_pool_is_refused() -> void:
	var t := _tuning()
	t.flux_health = 0.0
	assert_true(t.validate().size() > 0, "une cible a zero PV tombe avant d'exister")

func test_a_zeroed_cadence_is_refused() -> void:
	var t := _tuning()
	t.fan_interval = 0.0
	assert_true(t.validate().size() > 0, "une cadence nulle tire une infinite de balles par image")
