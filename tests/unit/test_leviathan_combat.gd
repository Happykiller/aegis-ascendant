extends "res://tests/test_case.gd"
## LeviathanCombat : la machine a quatre phases du boss final.
##
## Le module est pilote SANS arbre, sans coque et sans BulletManager — `tick()` est
## publique exactement pour ca. C'est ce qui rend verifiable un enchainement qu'aucune
## capture d'ecran ne pourrait couvrir : il faut plus de trois minutes de jeu pour voir
## les quatre phases.

const CombatScript := preload("res://scripts/bosses/leviathan_combat.gd")

var _phases: Array[int] = []
var _pull: Array = []

func _make() -> LeviathanCombat:
	var combat: LeviathanCombat = CombatScript.new()
	combat.tuning = LeviathanTuning.new()
	_phases = []
	_pull = []
	combat.phase_entered.connect(func(p: int) -> void: _phases.append(p))
	combat.pull_changed.connect(func(s: float, _r: float, _c: Vector2) -> void: _pull.append(s))
	combat.setup(null, null, null)
	return combat

func _kill_plates(combat: LeviathanCombat) -> void:
	for plate in combat.plates():
		combat._on_plate_hit(plate.max_health, plate.index)

func _kill_nodes(combat: LeviathanCombat) -> void:
	for i in CombatScript.NODE_COUNT:
		combat._on_node_hit(combat.tuning.node_health, i)

func _kill_spikes(combat: LeviathanCombat) -> void:
	for spike in combat.spikes():
		combat._on_spike_hit(spike.max_health, spike.index)

## Amene le module a l'etat « phase suivante, prete a tourner ».
##
## Trois appels, et chacun a sa raison — `tick()` consomme un repit et rend la main
## SANS executer la phase, ce qui est voulu (c'est le repit ou le joueur voit ce qu'il
## a casse) :
##   1. epuise le repit de la phase courante ;
##   2. fait tourner la phase, qui constate sa condition et bascule ;
##   3. epuise le repit de la phase nouvellement entree.
##
## En jeu, a 1/60 s, la nuance ne se voit pas. Ici elle compte, et un helper qui la
## masquerait rendrait les tests menteurs sur la mecanique reelle.
func _settle(combat: LeviathanCombat) -> void:
	combat.tick(2.0)
	combat.tick(0.016)
	combat.tick(2.0)

# --- Montage --------------------------------------------------------------

func test_it_starts_in_the_first_phase_with_everything_intact() -> void:
	var combat := _make()
	assert_eq(combat.phase(), CombatScript.Phase.ARMOR_CHOIR, "on commence par BRISER")
	assert_eq(combat.plates().size(), 4, "quatre plaques")
	assert_eq(combat.spikes().size(), 4, "quatre epines")
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001, "structure intacte")

func test_the_four_plates_are_spread_around_the_shell() -> void:
	# C'est cet ecart qui garantit qu'il y a presque toujours une cible dans l'arc,
	# donc aucun temps mort dans la phase.
	var combat := _make()
	var angles: Array[float] = []
	for plate in combat.plates():
		angles.append(plate.base_angle)
	for i in 4:
		assert_almost_eq(angles[i], TAU * i / 4.0, 0.001, "plaque %d a sa place" % i)

# --- Phase 1 : la fenetre nait de l'orbite --------------------------------

func test_the_shell_turns_and_swaps_which_plate_is_exposed() -> void:
	var combat := _make()
	var exposed_at_start := combat.plates()[0].is_exposed(combat.shell_rotation(), 100.0)
	combat.tick(combat.tuning.shell_orbit_period * 0.5)   # un demi-tour
	var exposed_later := combat.plates()[0].is_exposed(combat.shell_rotation(), 100.0)
	assert_true(exposed_at_start, "la plaque 0 commence face camera")
	assert_false(exposed_later, "un demi-tour plus tard, elle est masquee")

func test_exposure_drives_the_bullet_target() -> void:
	# Hors de l'arc, la cible doit etre eteinte : sinon le joueur touche une plaque
	# que le corps est cense masquer.
	var combat := _make()
	combat.tick(0.016)
	assert_true(combat.plates()[0].target.enabled, "la plaque exposee encaisse")
	assert_false(combat.plates()[2].target.enabled, "celle d'en face, non")

func test_a_plate_out_of_the_arc_cannot_be_damaged_through_the_target() -> void:
	var combat := _make()
	combat.tick(0.016)
	var back := combat.plates()[2]
	assert_false(back.is_exposed(combat.shell_rotation(), combat.tuning.plate_arc_deg),
		"hors de l'arc")

# --- Les transitions sont MATERIELLES, pas des seuils de PV ---------------

func test_breaking_the_four_plates_opens_the_maw() -> void:
	var combat := _make()
	_kill_plates(combat)
	combat.tick(0.016)
	assert_eq(combat.phase(), CombatScript.Phase.GRAVITIC_MAW, "les quatre plaques a terre : la gueule s'ouvre")

func test_three_plates_are_not_enough() -> void:
	# La transition a une condition materielle : le joueur voit ce qu'il a casse.
	var combat := _make()
	for i in 3:
		combat._on_plate_hit(combat.plates()[i].max_health, i)
	combat.tick(0.016)
	assert_eq(combat.phase(), CombatScript.Phase.ARMOR_CHOIR, "il en reste une : on ne bascule pas")

func test_damage_alone_never_advances_a_phase() -> void:
	# C'est ce que faisait le BossController generique, et c'est ce qui rendait le
	# boss illisible : la phase changeait sans que rien a l'ecran ne l'explique.
	var combat := _make()
	for i in 40:
		combat._on_core_hit(500.0)
	combat.tick(0.016)
	assert_eq(combat.phase(), CombatScript.Phase.ARMOR_CHOIR,
		"20 000 degats encaisses ne font pas avancer d'une phase")

func test_the_full_arc_runs_through_the_four_phases_in_order() -> void:
	var combat := _make()
	_kill_plates(combat); _settle(combat)
	_kill_nodes(combat); _settle(combat)
	_kill_spikes(combat); _settle(combat)
	combat._on_heart_hit(combat.tuning.heart_health)
	assert_eq(_phases, [
		CombatScript.Phase.ARMOR_CHOIR, CombatScript.Phase.GRAVITIC_MAW,
		CombatScript.Phase.BOARDING_SWARM, CombatScript.Phase.INTO_THE_MAW,
		CombatScript.Phase.DEFEATED,
	], "les quatre verbes s'enchainent dans l'ordre, puis la defaite")

# --- Les cibles s'ouvrent et se ferment avec les phases -------------------

func test_the_nodes_are_sealed_until_the_shell_breaks() -> void:
	var combat := _make()
	for node in combat._nodes:
		assert_false(node.enabled, "la levre est fermee pendant la phase 1")
	_kill_plates(combat); _settle(combat)
	for node in combat._nodes:
		assert_true(node.enabled, "la coquille eclatee, les noeuds deviennent la cible")

func test_the_core_only_becomes_targetable_in_phase_three() -> void:
	var combat := _make()
	assert_false(combat._core_target.enabled, "blinde en phase 1")
	_kill_plates(combat); _settle(combat)
	assert_false(combat._core_target.enabled, "toujours blinde en phase 2")
	_kill_nodes(combat); _settle(combat)
	assert_true(combat._core_target.enabled, "enfin touchable quand les epines s'arrachent")

func test_the_spikes_detach_when_phase_three_opens() -> void:
	var combat := _make()
	_kill_plates(combat); _settle(combat)
	_kill_nodes(combat); _settle(combat)
	for spike in combat.spikes():
		assert_true(spike.state != LeviathanSpike.State.ATTACHED, "elle s'est arrachee du corps")
		assert_true(spike.target.enabled, "et elle est devenue une cible")

# --- Phase 2 : l'aspiration, et son soulagement par tiers -----------------

func test_the_pull_starts_at_full_strength_and_eases_with_each_node() -> void:
	var combat := _make()
	_kill_plates(combat); _settle(combat)
	_pull = []
	combat.tick(0.016)
	assert_almost_eq(_pull[0], combat.tuning.pull_speed_max, 0.001, "aspiration entiere")
	combat._on_node_hit(combat.tuning.node_health, 0)
	_pull = []
	combat.tick(0.016)
	assert_almost_eq(_pull[0], combat.tuning.pull_speed_max * 2.0 / 3.0, 0.001,
		"un noeud abattu retire un tiers — le joueur le sent dans les doigts")

func test_the_phase_two_pull_always_leaves_the_player_able_to_flee() -> void:
	var combat := _make()
	_kill_plates(combat); _settle(combat)
	combat.tick(0.016)
	assert_true(GravityWell.escapes(_pull[0], combat.tuning.reference_player_max_speed),
		"sinon la phase 2 devient une cinematique")

func test_the_final_pull_is_stronger_than_the_player() -> void:
	# C'est le sujet de la phase 4 : on n'y resiste plus, on entre.
	var combat := _make()
	_kill_plates(combat); _settle(combat)
	_kill_nodes(combat); _settle(combat)
	_kill_spikes(combat); _settle(combat)
	_pull = []
	combat.tick(0.016)
	assert_true(_pull.size() > 0, "la phase 4 publie une aspiration")
	assert_false(GravityWell.escapes(_pull[0], combat.tuning.reference_player_max_speed),
		"on ne resiste plus")

# --- Phase 4 : le compte a rebours ----------------------------------------

func test_the_maw_closes_on_a_heart_that_holds_then_reopens() -> void:
	var combat := _make()
	_kill_plates(combat); _settle(combat)
	_kill_nodes(combat); _settle(combat)
	_kill_spikes(combat); _settle(combat)
	assert_true(combat._heart_target.enabled, "le coeur est expose des l'ouverture")
	combat.tick(combat.tuning.maw_open_time + 0.1)
	assert_false(combat._heart_target.enabled, "le coeur a tenu : la gueule se referme")
	assert_eq(combat.phase(), CombatScript.Phase.INTO_THE_MAW, "on reste en phase 4")
	combat.tick(combat.tuning.maw_reopen_delay + 0.1)
	assert_true(combat._heart_target.enabled, "puis elle rouvre, et on recommence")

func test_killing_the_heart_ends_the_fight() -> void:
	var combat := _make()
	_kill_plates(combat); _settle(combat)
	_kill_nodes(combat); _settle(combat)
	_kill_spikes(combat); _settle(combat)
	combat._on_heart_hit(combat.tuning.heart_health)
	assert_eq(combat.phase(), CombatScript.Phase.DEFEATED, "le coeur tombe, le boss meurt")

# --- La jauge du HUD ------------------------------------------------------

func test_the_gauge_falls_continuously_across_every_phase() -> void:
	# Une jauge qui ne montrerait que le corps resterait figee pendant une phase
	# entiere et dirait au joueur qu'il ne fait rien.
	var combat := _make()
	var readings: Array[float] = [combat.structure_ratio()]
	_kill_plates(combat); readings.append(combat.structure_ratio()); _settle(combat)
	_kill_nodes(combat); readings.append(combat.structure_ratio()); _settle(combat)
	_kill_spikes(combat); readings.append(combat.structure_ratio()); _settle(combat)
	for i in range(1, readings.size()):
		assert_true(readings[i] < readings[i - 1],
			"la jauge descend a chaque phase (%.3f -> %.3f)" % [readings[i - 1], readings[i]])

func test_the_gauge_never_goes_below_zero() -> void:
	var combat := _make()
	for i in 200:
		combat._on_core_hit(1000.0)
	assert_true(combat.structure_ratio() >= 0.0, "jamais negative, meme surdosee")

# --- Robustesse -----------------------------------------------------------

func test_a_dead_piece_cannot_be_damaged_twice() -> void:
	# Sinon la jauge globale descend deux fois pour la meme plaque.
	var combat := _make()
	combat._on_plate_hit(combat.plates()[0].max_health, 0)
	var after := combat.structure_ratio()
	combat._on_plate_hit(9999.0, 0)
	assert_almost_eq(combat.structure_ratio(), after, 0.001, "les degats sur un mort ne comptent pas")

func test_the_interlude_holds_the_boss_silent_between_phases() -> void:
	var combat := _make()
	_kill_plates(combat)
	combat.tick(0.016)
	assert_true(combat._interlude > 0.0, "un repit s'ouvre : le joueur voit ce qu'il a casse")

func test_a_module_without_tuning_ticks_without_crashing() -> void:
	var combat: LeviathanCombat = CombatScript.new()
	combat.tick(0.5)
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001, "degrade proprement, sans planter")
