extends "res://tests/test_case.gd"
## LeviathanTuning : les invariants qui empechent un reglage sensé pièce par pièce de
## produire un combat injouable. Chaque test correspond a une panne SILENCIEUSE —
## celles ou aucune valeur prise separement n'a l'air fausse.
##
## REFONTE ADR-0020 — le combat est passé de quatre phases a deux. Les tests qui
## gardaient les nœuds gravitiques, l'essaim d'abordage et la plongee dans la gueule ont
## disparu avec eux ; deux invariants NEUFS les remplacent, et ils gardent precisement ce
## qui avait echappe a tous les autres : la duree totale du combat, et le fait qu'une
## phase pese assez pour exister.

func _tuning() -> LeviathanTuning:
	return LeviathanTuning.new()   # les valeurs par defaut sont les valeurs retenues

func test_the_shipped_values_validate() -> void:
	var errors := _tuning().validate()
	assert_eq(errors.size(), 0, "reglages par defaut valides, sinon : %s" % ", ".join(errors))

# --- Invariant 1 : la phase 1 offre toujours une cible --------------------

func test_the_arc_always_covers_the_gap_between_plates() -> void:
	var t := _tuning()
	# Une seule plaque encaisse a la fois. Si l'arc est plus etroit que l'ecart entre
	# deux plaques, il existe des instants ou AUCUNE n'est atteignable : le joueur tire
	# dans le vide sans qu'on lui dise pourquoi.
	assert_almost_eq(t.plate_spacing_deg(), 90.0, 0.001, "quatre plaques : 90 deg d'ecart")
	assert_true(t.plate_arc_deg >= t.plate_spacing_deg(),
		"l'arc de %.0f deg couvre les %.0f deg d'ecart" % [t.plate_arc_deg, t.plate_spacing_deg()])

func test_an_arc_narrower_than_the_gap_is_refused() -> void:
	# Le piege : 9 s et 70 deg sont deux nombres parfaitement sensés isolement, et
	# l'ancien invariant de « fenetre » les acceptait — il mesurait combien de temps une
	# plaque restait atteignable, jamais s'il y en avait une.
	var t := _tuning()
	t.plate_arc_deg = 70.0
	var errors := t.validate()
	assert_true(errors.size() > 0, "sous 90 deg, il existe des instants sans aucune cible")
	assert_true(errors[0].contains("no target at all"), "et l'erreur le nomme : %s" % errors[0])

func test_the_window_stays_long_enough_to_place_a_burst() -> void:
	var t := _tuning()
	# 9 s de tour x 100 deg / 360 = 2,5 s d'atteignabilite par passage.
	assert_almost_eq(t.plate_window(), 9.0 * 100.0 / 360.0, 0.001,
		"la fenetre est un arc parcouru, pas un minuteur")
	assert_true(t.plate_window() >= t.min_window, "et elle est exploitable")

func test_an_orbit_too_fast_for_the_window_is_refused() -> void:
	var t := _tuning()
	t.shell_orbit_period = 3.0   # 0,83 s par passage
	var errors := t.validate()
	assert_true(errors.size() > 0, "la plaque defile trop vite pour etre traitee")
	assert_true(errors[0].contains("window"), "erreur explicite : %s" % errors[0])

# --- Invariant 2 : l'aspiration de la phase 2 laisse jouer ----------------

func test_the_pull_must_leave_the_player_able_to_flee() -> void:
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

func test_a_pull_that_never_stops_is_not_intermittent() -> void:
	# L'aspiration a cesse d'etre une phase pour devenir une pression par vagues. Une
	# vague qui dure autant que son intervalle est une aspiration permanente : le
	# reglage dirait « intermittent » et le jeu ferait autre chose.
	var t := _tuning()
	t.pull_time = t.pull_interval
	var errors := t.validate()
	assert_true(errors.size() > 0, "sans repit entre deux vagues, ce n'est plus une vague")
	assert_true(errors[0].contains("intermittent"), "erreur explicite : %s" % errors[0])

func test_the_player_can_always_outrun_the_pull() -> void:
	var t := _tuning()
	assert_true(t.pull_speed_max < t.reference_player_max_speed,
		"on resiste a l'aspiration : elle presse, elle ne prend pas les commandes")

# --- Invariant 3 : le combat tient sa duree -------------------------------

func test_the_whole_fight_lands_on_its_promise() -> void:
	var t := _tuning()
	# ~40 s, « nerveux » : le playtest a rejete les ~67 s d'ADR-0019 comme il avait
	# rejete les ~3 min d'avant. Le boss final reste au-dessus du mini-boss (~30 s)
	# sans devenir une epreuve d'endurance.
	assert_almost_eq(t.total_duration(), 40.0, 1.0,
		"~40 s de combat net ; obtenu %.1f s" % t.total_duration())
	assert_eq(t.validate().size(), 0, "et le jeu de valeurs livre passe son propre garde-fou")

func test_a_fight_that_drifts_long_is_refused() -> void:
	# LE GARDE-FOU QUI MANQUAIT. Chaque valeur peut rester sensee pendant que le combat
	# derive vers trois minutes : c'est arrive deux fois, et il a fallu un playtest pour
	# le voir. Un test le voit maintenant.
	var t := _tuning()
	t.heart_health = 20000.0
	var errors := t.validate()
	assert_true(errors.size() > 0, "un coeur de 20 000 PV allonge le combat sans qu'aucune valeur n'ait l'air fausse")
	var named := false
	for error in errors:
		if error.contains("fight lasts"):
			named = true
	assert_true(named, "et l'erreur nomme la duree : %s" % ", ".join(errors))

func test_a_fight_that_drifts_short_is_refused_too() -> void:
	var t := _tuning()
	t.plate_health = 100.0
	t.heart_health = 200.0
	assert_true(t.validate().size() > 0, "un boss final expedie en cinq secondes n'est pas un final")

# --- Invariant 4 : chaque phase pese dans le combat -----------------------

func test_each_phase_carries_a_real_share_of_the_fight() -> void:
	var t := _tuning()
	for phase in LeviathanTuning.PHASE_COUNT:
		var share := t.phase_duration(phase) / t.target_duration
		assert_true(share >= 0.25 and share <= 0.75,
			"phase %d : %.0f%% du combat" % [phase + 1, share * 100.0])

func test_a_decorative_phase_is_refused() -> void:
	# Une phase de trois secondes n'est pas une phase, c'est une transition — et c'est
	# exactement ce qu'etait devenue la phase 4 avant la refonte (8 s sur 67).
	var t := _tuning()
	t.plate_health = 3800.0   # la phase 1 avale presque tout le combat
	t.heart_health = 400.0
	var errors := t.validate()
	assert_true(errors.size() > 0, "une phase qui ne pese rien ne se joue pas, elle se traverse")

# --- Invariant 5 : les telegraphes ----------------------------------------

func test_the_lance_keeps_its_wind_up() -> void:
	var t := _tuning()
	t.lance_windup_time = 0.0
	assert_true(t.validate().size() > 0, "sans rearme, le rayon devient imparable")

func test_a_missile_that_turns_too_fast_is_refused() -> void:
	# Un projectile qui vire plus vite qu'un demi-tour par seconde touche toujours.
	var t := _tuning()
	t.missile_turn_rate = 4.0
	assert_true(t.validate().size() > 0, "au-dela de PI rad/s, il n'est plus esquivable")

# --- Invariant 6 : occupation ---------------------------------------------

func test_an_impossible_occupancy_is_refused() -> void:
	var t := _tuning()
	t.occupancy_phase_2 = 0.0
	assert_true(t.validate().size() > 0, "une occupation nulle rend la duree infinie")
	var u := _tuning()
	u.occupancy_phase_1 = 1.4
	assert_true(u.validate().size() > 0, "et au-dela de 1 elle n'a plus de sens")

# --- Lectures derivees ----------------------------------------------------

func test_phase_health_covers_exactly_the_two_phases() -> void:
	var t := _tuning()
	assert_almost_eq(t.phase_health(0), t.plate_health * float(t.plate_count), 0.001,
		"phase 1 : les quatre plaques")
	assert_almost_eq(t.phase_health(1), t.heart_health, 0.001, "phase 2 : le coeur seul")
	assert_almost_eq(t.total_structure(), t.phase_health(0) + t.phase_health(1), 0.001,
		"et le total est bien leur somme")

func test_the_gauge_no_longer_spans_the_whole_fight() -> void:
	# ⚠️ CE TEST GARDE UN CHANGEMENT DE SENS, pas une valeur. `total_structure()` etait le
	# denominateur de la jauge du HUD : briser toute l'armure ne valait que 30 % de barre,
	# et le joueur concluait qu'il ne servait a rien. La jauge montre desormais la phase en
	# cours — donc briser l'armure vide une barre entiere.
	var t := _tuning()
	var armour_share := t.phase_health(0) / t.total_structure()
	assert_true(armour_share > 0.4,
		"l'armure pese %.0f%% du total : sur une barre cumulee, vingt secondes de jeu ne se verraient pas"
			% (armour_share * 100.0))

func test_the_final_boss_still_outlasts_the_mini_boss() -> void:
	# Le boss final n'est pas « plus gros » en PV bruts : il l'est par sa duree et par le
	# fait qu'il demande DEUX gestes au lieu d'un cycle repete.
	var t := _tuning()
	assert_true(t.total_duration() > 30.0,
		"au-dessus du mini-boss (~30 s) : %.0f s" % t.total_duration())

# --- Garde-fous de base ---------------------------------------------------

func test_a_zeroed_health_pool_is_refused() -> void:
	var t := _tuning()
	t.heart_health = 0.0
	assert_true(t.validate().size() > 0, "une cible a zero PV tombe avant d'exister")

func test_a_zeroed_cadence_is_refused() -> void:
	var t := _tuning()
	t.fan_interval = 0.0
	assert_true(t.validate().size() > 0, "une cadence nulle tire une infinite de balles par image")
