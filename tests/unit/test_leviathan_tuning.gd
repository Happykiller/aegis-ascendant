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
	# ⚠️ CE TEST MESURAIT LE PIRE CAS, ET SA PRECISION ETAIT UN ACCIDENT. Il comparait
	# `total_duration()` — un joueur qui consomme chaque plongee jusqu'au bout — a 40 s a
	# deux secondes pres, et ca tombait juste par coincidence. Le rythme se juge sur ce qu'un
	# joueur de REFERENCE vit : il sort des son quota rempli, bien avant le plafond.
	#
	# La bande vient de `target_duration` / `duration_tolerance`, que `validate()` applique
	# deja : une seule source, plus deux chiffres sur le meme fait.
	assert_almost_eq(t.reference_duration(), t.target_duration, t.duration_tolerance,
		"combat de reference : %.1f s pour une cible de %.0f +/- %.0f"
			% [t.reference_duration(), t.target_duration, t.duration_tolerance])
	assert_true(t.total_duration() < 70.0,
		"et meme le pire cas reste borne : %.1f s" % t.total_duration())

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
	# Trop mou, le boss meurt au premier passage et les cycles ne servent a rien ; trop dur,
	# le joueur repart pour un tour de plus a chaque fois sans comprendre pourquoi.
	var t := _tuning()
	# ⚠️ On LIT la portee au reglage, on ne la recalcule pas : la formule a change deux
	# fois (blindage, puis verrous) et une copie locale serait restee sur l'ancienne.
	var reachable := t.flux_reachable_per_dive()
	assert_true(t.flux_damage_per_dive() <= reachable,
		"%.0f PV a placer par plongee, %.0f atteignables" % [t.flux_damage_per_dive(), reachable])
	assert_true(t.flux_damage_per_dive() > reachable * 0.55,
		"et il ne tombe pas au premier passage : %.0f contre %.0f" % [t.flux_damage_per_dive(), reachable])

func test_the_flux_is_NOT_sized_against_the_armour_cadence() -> void:
	# ⚠️ LE DEFAUT QUE CE TEST GARDE, ET IL A COUTE UN PLAYTEST ENTIER. L'invariant 5 se
	# comparait a `reference_dps` — la cadence sur une cible LARGE, ou toutes les balles
	# portent. Le flux fait 1,80 m et derive : seuls les canons de nez le touchent. Se
	# mesurer a la mauvaise hypothese, c'est se donner raison : le reglage tombait a 99 %
	# du plafond autorise, et le playtest du 2026-08-25 a demande SIX plongees a puissance
	# maximale au lieu de trois.
	var t := _tuning()
	assert_true(t.flux_reference_dps < t.reference_dps,
		"une petite cible mobile ne se frappe pas comme une plaque : %.0f contre %.0f"
			% [t.flux_reference_dps, t.reference_dps])
	# Le reglage livre doit garder de la MARGE, pas froler le plafond comme avant.
	# ⚠️ On LIT la portee au reglage, on ne la recalcule pas : la formule a change deux
	# fois (blindage, puis verrous) et une copie locale serait restee sur l'ancienne.
	var reachable := t.flux_reachable_per_dive()
	assert_true(t.flux_damage_per_dive() < reachable * 0.95,
		"le flux ne doit plus etre calibre au millimetre du plafond : %.0f %% de %.0f PV"
			% [100.0 * t.flux_damage_per_dive() / reachable, reachable])

func test_an_ancient_flux_sized_on_the_armour_cadence_is_now_refused() -> void:
	# La valeur exacte d'avant le 2026-08-25. Elle validait ; elle ne doit plus.
	var t := _tuning()
	t.flux_health = 5300.0
	assert_true(t.validate().size() > 0,
		"5300 PV, c'etait le flux dimensionne sur la mauvaise cadence")

## Le flux doit encaisser DEUX plongees et ceder pendant la TROISIEME — toute la promesse
## des cycles.
##
## ⚠️ CETTE GARDE TENAIT UN NOMBRE MESURE, ET IL EST DEVENU FAUX. Elle comparait la sante a
## « ~883 PV places par plongee a puissance maximale », releve au playtest du 2026-08-25 —
## sur une plongee SANS blindage ni verrous. Depuis, le noyau n'est atteignable qu'une
## fraction du temps : la mesure ne decrit plus le jeu.
##
## Et surtout, ce n'est plus elle qui garantit les cycles. `ADR-0026` a plafonne les degats
## a UN TIERS par passage : trois cycles sont vrais PAR CONSTRUCTION, pas par calibrage.
## La garde porte donc desormais sur le mecanisme, pas sur un releve qui vieillit.
func test_the_flux_survives_a_second_dive_so_the_cycles_happen() -> void:
	var t := _tuning()
	var per_dive := t.flux_damage_per_dive()
	assert_almost_eq(per_dive * float(t.cycle_count), t.flux_health, 0.01,
		"les %d passages plafonnes couvrent exactement la sante du flux" % t.cycle_count)
	assert_true(per_dive * 2.0 < t.flux_health,
		"deux passages n'y suffisent pas : %.0f contre %.0f PV" % [per_dive * 2.0, t.flux_health])
	# Et le plafond doit rester ATTEIGNABLE, sinon il ne plafonne rien : c'est ce que
	# `validate()` verifie, on s'assure seulement que la marge existe.
	assert_true(per_dive <= t.flux_reachable_per_dive(),
		"un joueur de reference remplit son quota : %.0f a placer, %.0f atteignables"
			% [per_dive, t.flux_reachable_per_dive()])

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

func test_a_flux_without_its_own_cadence_is_refused() -> void:
	# Sans hypothese propre, l'invariant 5 n'a rien a quoi se comparer — et le silence
	# ressemblerait a un accord.
	var t := _tuning()
	t.flux_reference_dps = 0.0
	assert_true(t.validate().size() > 0, "une cadence de reference nulle ne dimensionne rien")

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

## ⚠️ CETTE GARDE PLAFONNAIT `dive_time` A 6 s, en citant « on n'aurait pas enormement de
## temps pour tirer dessus ». Elle confondait le PLAFOND et la DUREE. La plongee s'arrete au
## premier de DEUX criteres — quota d'un tiers rempli, ou temps ecoule — et l'operateur a
## demande le 2026-08-27 de rallonger le second. Ca ne rallonge la plongee de personne qui
## tire correctement : il sort avant.
##
## Ce qui doit rester court, c'est la plongee du joueur de REFERENCE. C'est elle qu'on garde.
func test_the_dive_is_short_for_whoever_shoots_straight() -> void:
	var t := _tuning()
	assert_true(t.reference_dive_time() <= 6.0,
		"%.2f s pour remplir le quota, contre %.1f s de plafond"
			% [t.reference_dive_time(), t.dive_time])
	assert_true(t.reference_dive_time() < t.dive_time,
		"et le plafond laisse une marge a celui qui rate")
	assert_true(t.dive_duration() > t.dive_time, "entree et ejection comptent aussi")

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
