extends "res://tests/test_case.gd"
## LeviathanCombat : la machine CYCLIQUE du boss final (ADR-0021).
##
##     BRISER L'ARMURE  →  PLONGER DANS LE NOYAU  →  ejecte  →  l'armure revient, amoindrie
##
## Le module est pilote SANS arbre, sans coque et sans BulletManager — `tick()` est
## publique exactement pour ca. C'est ce qui rend verifiable un enchainement qu'aucune
## capture ne pourrait couvrir : trois cycles demandent quarante secondes de jeu.
##
## ⚠️ CE QUE CES TESTS GARDENT, ET POURQUOI. Trois defauts ont survecu a toutes les
## versions precedentes des tests parce que ceux-ci verifiaient la MECANIQUE et jamais
## son EFFET : la jauge qui cumulait les phases, les degats qui s'etalaient sur quatre
## plaques, et une duree que personne ne mesurait. Chacun a desormais son test — ici pour
## les deux premiers, dans `test_leviathan_tuning.gd` pour le troisieme.

const CombatScript := preload("res://scripts/bosses/leviathan_combat.gd")
const BossScript := preload("res://scripts/bosses/boss_controller.gd")

var _phases: Array[int] = []
var _pull: Array = []
var _active: Array[int] = []
var _dives: Array[int] = []
var _reformed: Array = []

func _make() -> LeviathanCombat:
	var combat := track(CombatScript.new()) as LeviathanCombat
	combat.tuning = LeviathanTuning.new()
	_phases = []
	_pull = []
	_active = []
	_dives = []
	_reformed = []
	combat.phase_entered.connect(func(p: int) -> void: _phases.append(p))
	combat.pull_changed.connect(func(s: float, _r: float, _c: Vector2) -> void: _pull.append(s))
	combat.piece_active_changed.connect(func(i: int) -> void: _active.append(i))
	combat.dive_started.connect(func(c: int, _centre: Vector2) -> void: _dives.append(c))
	combat.armour_reformed.connect(func(c: int, p: int) -> void: _reformed.append([c, p]))
	combat.setup(null, null, null)
	return combat

func _kill_armour(combat: LeviathanCombat) -> void:
	for plate in combat.plates():
		combat._on_plate_hit(plate.max_health, plate.index)

## Traverse une plongee entiere : entree, sejour, ejection.
##
## ⚠️ LE PREMIER TICK NE PLONGE PAS, IL BASCULE. `_run_armor` constate que l'armure est a
## terre et ouvre la plongee ; celle-ci ne tourne qu'au tick suivant. A 60 images par
## seconde ce decalage vaut 16 ms et ne se voit pas — mais un test qui l'ignore mesure la
## phase precedente et echoue en accusant le mauvais coupable.
func _ride_dive(combat: LeviathanCombat, damage: float = 0.0) -> void:
	var t := combat.tuning
	combat.tick(0.016)                         # bascule armure -> plongee
	combat.tick(t.dive_enter_time + 0.01)      # entree consommee
	if damage > 0.0:
		combat._on_flux_hit(damage)
	combat.tick(t.dive_time + 0.01)            # sejour consomme
	combat.tick(t.dive_eject_time + 0.01)      # ejection consommee
	combat.tick(2.0)                           # repit d'ouverture du cycle suivant

# --- Montage --------------------------------------------------------------

func test_it_starts_on_the_full_armour() -> void:
	var combat := _make()
	assert_eq(combat.phase(), CombatScript.Phase.ARMOR, "on commence par BRISER L'ARMURE")
	assert_eq(combat.cycle(), 0, "premier cycle")
	assert_eq(combat.plates().size(), 4, "quatre plaques")
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001, "armure intacte")

func test_the_plates_are_spread_evenly_for_the_cycle() -> void:
	var combat := _make()
	for i in combat.plates().size():
		assert_almost_eq(combat.plates()[i].base_angle, TAU * i / 4.0, 0.001,
			"reparties regulierement")

func test_the_shell_turns_and_swaps_which_plate_is_exposed() -> void:
	var combat := _make()
	var at_start := combat.plates()[0].is_exposed(combat.shell_rotation(), 100.0)
	combat.tick(combat.tuning.shell_orbit_period * 0.5)
	var later := combat.plates()[0].is_exposed(combat.shell_rotation(), 100.0)
	assert_true(at_start != later, "un demi-tour change la face exposee")

# --- LE DEFAUT CORRIGE : une seule plaque encaisse ------------------------

func test_only_the_highlighted_plate_can_be_damaged() -> void:
	# ⚠️ Avant, toute plaque dans l'arc encaissait : les degats se repartissaient sur les
	# quatre, elles descendaient ensemble et AUCUNE ne tombait avant la fin de la phase.
	var combat := _make()
	combat.tick(0.016)
	var enabled := 0
	for plate in combat.plates():
		if plate.target.enabled:
			enabled += 1
	assert_eq(enabled, 1, "une seule plaque encaisse a la fois, celle qui brille")

func test_the_vulnerable_plate_is_the_one_announced_to_the_hud() -> void:
	var combat := _make()
	combat.tick(0.016)
	assert_true(_active.size() > 0, "le module annonce la plaque a viser")
	var announced: int = _active[_active.size() - 1]
	for plate in combat.plates():
		assert_eq(plate.target.enabled, plate.index == announced,
			"la plaque annoncee est exactement celle qui encaisse")

func test_a_fallen_plate_never_becomes_the_target_again() -> void:
	var combat := _make()
	combat.tick(0.016)
	var first: int = _active[_active.size() - 1]
	combat._on_plate_hit(combat.plates()[first].max_health, first)
	combat.tick(0.016)
	assert_false(combat.plates()[first].target.enabled, "une plaque abattue n'encaisse plus")

# --- LES EPINES : le sens rendu a la destruction d'une plaque -------------

func test_every_plate_carries_a_spine() -> void:
	# « Les tentacules, je ne vois pas a quoi elles servent » : elles tirent, et casser
	# une plaque en eteint une. La recompense est une menace en moins.
	var combat := _make()
	assert_eq(combat.spines_up(), 4, "quatre tourelles au premier cycle")

func test_breaking_a_plate_drops_a_spine() -> void:
	var combat := _make()
	combat.tick(0.016)
	combat._on_plate_hit(combat.plates()[0].max_health, 0)
	assert_eq(combat.spines_up(), 3, "une plaque brisee, un laser en moins")

func test_the_armour_comes_back_with_one_spine_fewer() -> void:
	var combat := _make()
	_kill_armour(combat)
	assert_eq(combat.spines_up(), 0, "toutes les tourelles sont tombees avec l'armure")
	_ride_dive(combat)
	assert_eq(combat.plates().size(), 3, "l'armure se reforme moins bien")
	assert_eq(combat.spines_up(), 3, "et elle ramene autant de tourelles que de plaques")

# --- Les cycles -----------------------------------------------------------

func test_breaking_the_armour_opens_the_dive() -> void:
	var combat := _make()
	_kill_armour(combat)
	combat.tick(0.016)
	assert_eq(combat.phase(), CombatScript.Phase.DIVE, "l'armure tombee, le noyau s'ouvre")
	assert_eq(_dives, [0] as Array[int], "et le niveau est prevenu, avec le numero du cycle")

func test_one_plate_left_is_not_enough() -> void:
	var combat := _make()
	for i in 3:
		combat._on_plate_hit(combat.plates()[i].max_health, i)
	combat.tick(0.016)
	assert_eq(combat.phase(), CombatScript.Phase.ARMOR,
		"la condition est MATERIELLE : toutes les plaques du cycle")

func test_damage_alone_never_advances_a_phase() -> void:
	# C'est ce que faisait le BossController generique, et c'est ce qui rendait le boss
	# illisible : la phase changeait sans que rien a l'ecran ne l'explique.
	var combat := _make()
	for i in 40:
		combat._on_plate_hit(10.0, 0)
	combat.tick(0.016)
	assert_eq(combat.phase(), CombatScript.Phase.ARMOR, "des degats ne font pas une phase")

func test_the_armour_reforms_between_two_dives() -> void:
	var combat := _make()
	_kill_armour(combat)
	_ride_dive(combat)
	assert_eq(combat.phase(), CombatScript.Phase.ARMOR, "on ressort dans une armure neuve")
	assert_eq(combat.cycle(), 1, "deuxieme cycle")
	assert_eq(_reformed.size(), 1, "et le joueur en est averti — sans annonce, ca se lit comme un bug")
	assert_eq(_reformed[0][1], 3, "trois plaques cette fois")

func test_three_cycles_of_honest_damage_kill_the_boss() -> void:
	var combat := _make()
	var per_dive := combat.tuning.flux_damage_per_dive()
	for cycle in 3:
		_kill_armour(combat)
		_ride_dive(combat, per_dive)
	assert_eq(combat.phase(), CombatScript.Phase.DEFEATED,
		"trois plongees bien tirees suffisent — c'est le dimensionnement du flux")

func test_a_missed_dive_costs_a_cycle_but_never_the_fight() -> void:
	# Le boss n'avance pas sur un compteur : s'il reste du flux, un cycle de plus s'ouvre.
	var combat := _make()
	for cycle in 3:
		_kill_armour(combat)
		_ride_dive(combat, 10.0)   # on rate presque tout
	assert_eq(combat.phase(), CombatScript.Phase.ARMOR, "le flux tient, le combat continue")
	assert_eq(combat.plates().size(), combat.tuning.plate_count_min,
		"et l'armure ne descend pas sous son plancher")

# --- La plongee -----------------------------------------------------------

func test_the_flux_is_only_a_target_inside_the_core() -> void:
	var combat := _make()
	combat._on_flux_hit(9999.0)
	assert_almost_eq(combat.fight_ratio(), 1.0, 0.001,
		"hors du noyau, le flux ne s'entame pas — le joueur n'a aucune raison de le croire atteignable")

func test_the_pull_only_runs_during_the_entry() -> void:
	var combat := _make()
	_kill_armour(combat)
	combat.tick(0.016)                                   # bascule
	combat.tick(0.016)                                   # entree
	assert_true(_pull.size() > 0 and _pull[_pull.size() - 1] > 0.0, "l'aspiration accompagne l'entree")
	combat.tick(combat.tuning.dive_enter_time + 0.01)    # derniere image d'entree
	combat.tick(0.016)                                   # premiere image dedans
	assert_almost_eq(_pull[_pull.size() - 1], 0.0, 0.001, "dedans, elle relache : on tire, on ne lutte pas")

func test_the_shell_opens_for_the_dive_and_closes_after() -> void:
	var combat := _make()
	combat.tick(1.0)
	assert_almost_eq(combat.shell_open_ratio(), 0.0, 0.001, "temps 1 : la coque reste close")
	_kill_armour(combat)
	combat.tick(0.016)                                   # bascule
	combat.tick(combat.tuning.shell_open_time + 0.1)
	assert_true(combat.shell_open_ratio() > 0.9, "la plongee l'ouvre en grand")
	_ride_dive(combat)
	assert_almost_eq(combat.shell_open_ratio(), 0.0, 0.001, "et le cycle suivant la referme")

func test_killing_the_flux_still_plays_the_ejection() -> void:
	# On ne coupe pas la plongee en deux : le joueur voit sa victoire, il n'est pas
	# telepote dans l'ecran suivant.
	var combat := _make()
	_kill_armour(combat)
	combat.tick(0.016)                                   # bascule
	combat.tick(combat.tuning.dive_enter_time + 0.01)
	combat._on_flux_hit(combat.tuning.flux_health)
	assert_eq(combat.phase(), CombatScript.Phase.DIVE, "toujours dans le noyau")
	assert_eq(combat.dive_step(), CombatScript.Dive.EJECT, "mais en ejection")
	combat.tick(combat.tuning.dive_eject_time + 0.01)
	assert_eq(combat.phase(), CombatScript.Phase.DEFEATED, "et le boss tombe a la sortie")

# --- LE DEFAUT CORRIGE : la jauge ne ment plus ----------------------------

func test_the_gauge_shows_the_current_target_not_the_whole_fight() -> void:
	# ⚠️ LE DEFAUT SIGNALE DEUX FOIS PAR L'OPERATEUR. La jauge divisait par les PV des
	# quatre phases : briser toute l'armure ne valait que 30 % de barre, et le joueur
	# lisait « 70 % » apres vingt secondes d'effort.
	var combat := _make()
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001, "barre pleine au debut")
	_kill_armour(combat)
	assert_almost_eq(combat.structure_ratio(), 0.0, 0.001, "l'armure brisee VIDE la barre")

func test_the_gauge_refills_for_the_flux_then_for_the_next_armour() -> void:
	var combat := _make()
	_kill_armour(combat)
	combat.tick(combat.tuning.dive_enter_time + 0.02)
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001, "dans le noyau : la barre du flux, pleine")
	_ride_dive(combat)
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001, "puis celle de l'armure reformee")

func test_the_fight_progress_never_climbs_back_up() -> void:
	# ⚠️ DEUX MESURES, DEUX USAGES. La jauge du HUD remonte a chaque bascule ; la
	# progression du combat, jamais. Les confondre a coute un sommet musical : la
	# partition culminait a mi-combat puis retombait (`music 9 -> 8 -> 9` au journal).
	var combat := _make()
	assert_almost_eq(combat.fight_ratio(), 1.0, 0.001, "combat intact")
	_kill_armour(combat)
	var after := combat.fight_ratio()
	assert_true(after < 1.0, "l'armure brisee compte dans la progression")
	_ride_dive(combat)
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001, "la JAUGE se remplit")
	assert_true(combat.fight_ratio() <= after, "mais la PROGRESSION ne remonte pas")

func test_the_gauge_never_goes_below_zero() -> void:
	var combat := _make()
	for i in 200:
		combat._on_plate_hit(1000.0, 0)
	assert_true(combat.structure_ratio() >= 0.0, "jamais negative, meme surdosee")

# --- Montage sur un VRAI BossController ------------------------------------
## Les tests ci-dessus pilotent le module seul. Ici on le monte sous un vrai
## `BossController`, comme la scène, pour éprouver les points de câblage que le module
## seul ne couvre pas : le corps reste CLOS, il s'immobilise pendant la plongée, et c'est
## le module qui le fait mourir quand le flux tombe.

func _rig() -> Array:
	var bm := track(BulletManager.new()) as BulletManager
	# `combat` n'est pas suivi : il devient enfant de `boss`, qui le libere avec lui.
	var boss := track(BossScript.new()) as BossController
	boss.max_health = 20000.0
	boss.hitbox_radius = 2.7
	boss.entry_plane_position = Vector2(0.0, 5.5)
	boss.external_attacks = true
	var combat: LeviathanCombat = CombatScript.new()
	combat.tuning = LeviathanTuning.new()
	boss.add_child(combat)
	boss._ready()
	combat._ready()   # connecte began/defeated AVANT begin, qui monte le module
	boss.begin(bm, null)
	boss.plane_position = boss.entry_plane_position
	boss._physics_process(1.0 / 60.0)
	return [boss, combat]

func test_the_body_stays_closed_and_only_the_flux_kills_the_boss() -> void:
	var rig := _rig()
	var boss: BossController = rig[0]
	var combat: LeviathanCombat = rig[1]
	var died: Array[bool] = [false]
	boss.defeated.connect(func(_world: Vector3) -> void: died[0] = true)
	assert_false(boss.vulnerable, "le corps est clos, aucun tir ne l'entame")
	var per_dive := combat.tuning.flux_damage_per_dive()
	for cycle in 3:
		_kill_armour(combat)
		_ride_dive(combat, per_dive)
	assert_true(died[0], "le flux tombe, et le module fait mourir le BossController")

func test_the_boss_holds_still_while_the_player_is_inside() -> void:
	# ⚠️ Il derive de gauche a droite en permanence. Un noyau qui glisse pendant que le
	# chasseur est dedans emporterait le joueur hors du cadre sans qu'il ait rien fait.
	var rig := _rig()
	var boss: BossController = rig[0]
	var combat: LeviathanCombat = rig[1]
	assert_false(boss.is_driven(), "il derive librement pendant l'armure")
	_kill_armour(combat)
	combat.tick(0.016)
	assert_true(boss.is_driven(), "il s'immobilise pour la plongee")
	_ride_dive(combat)
	assert_false(boss.is_driven(), "et repart quand l'armure se reforme")

func test_defeat_is_idempotent() -> void:
	# Deux balles sur la meme image ne doivent pas payer la mort deux fois.
	var rig := _rig()
	var boss: BossController = rig[0]
	var count: Array[int] = [0]
	boss.defeated.connect(func(_world: Vector3) -> void: count[0] += 1)
	boss.defeat()
	boss.defeat()
	assert_eq(count[0], 1, "un boss ne meurt qu'une fois")

# --- Robustesse -----------------------------------------------------------

func test_a_dead_plate_cannot_be_damaged_twice() -> void:
	var combat := _make()
	combat._on_plate_hit(combat.plates()[0].max_health, 0)
	var after := combat.fight_ratio()
	combat._on_plate_hit(9999.0, 0)
	assert_almost_eq(combat.fight_ratio(), after, 0.001, "les degats sur un mort ne comptent pas")

func test_a_module_without_tuning_ticks_without_crashing() -> void:
	var combat := track(CombatScript.new()) as LeviathanCombat
	combat.tick(0.5)
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001, "degrade proprement, sans planter")
