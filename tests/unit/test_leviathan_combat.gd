extends "res://tests/test_case.gd"
## LeviathanCombat : la machine a DEUX phases du boss final (ADR-0020).
##
## Le module est pilote SANS arbre, sans coque et sans BulletManager — `tick()` est
## publique exactement pour ca. C'est ce qui rend verifiable un enchainement qu'aucune
## capture d'ecran ne pourrait couvrir : il faut une quarantaine de secondes de jeu pour
## voir les deux phases.
##
## ⚠️ CE QUE CES TESTS GARDENT DEPUIS LA REFONTE. Trois defauts avaient survecu a tous les
## tests precedents parce que ceux-ci verifiaient la MECANIQUE et jamais son EFFET :
##   1. la jauge cumulait les quatre phases, donc briser l'armure ne se voyait pas ;
##   2. toutes les plaques exposees encaissaient, donc aucune ne tombait avant la fin ;
##   3. rien ne verifiait la duree du combat.
## Les trois ont maintenant leur test. Le premier et le deuxieme ici, le troisieme dans
## `test_leviathan_tuning.gd`.

const CombatScript := preload("res://scripts/bosses/leviathan_combat.gd")
const BossScript := preload("res://scripts/bosses/boss_controller.gd")

var _phases: Array[int] = []
var _pull: Array = []
var _active: Array[int] = []

func _make() -> LeviathanCombat:
	var combat := track(CombatScript.new()) as LeviathanCombat
	combat.tuning = LeviathanTuning.new()
	_phases = []
	_pull = []
	_active = []
	combat.phase_entered.connect(func(p: int) -> void: _phases.append(p))
	combat.pull_changed.connect(func(s: float, _r: float, _c: Vector2) -> void: _pull.append(s))
	combat.piece_active_changed.connect(func(i: int) -> void: _active.append(i))
	combat.setup(null, null, null)
	return combat

func _kill_plates(combat: LeviathanCombat) -> void:
	for plate in combat.plates():
		combat._on_plate_hit(plate.max_health, plate.index)

## Amene le module a l'etat « phase suivante, prete a tourner ».
##
## Trois appels, et chacun a sa raison — `tick()` consomme un repit et rend la main
## SANS executer la phase, ce qui est voulu (c'est le repit ou le joueur voit ce qu'il
## a casse) :
##   1. epuise le repit de la phase courante ;
##   2. fait tourner la phase, qui constate sa condition et bascule ;
##   3. epuise le repit de la phase nouvellement entree.
func _settle(combat: LeviathanCombat) -> void:
	combat.tick(2.0)
	combat.tick(0.016)
	combat.tick(2.0)

# --- Montage --------------------------------------------------------------

func test_it_starts_in_the_first_phase_with_everything_intact() -> void:
	var combat := _make()
	assert_eq(combat.phase(), CombatScript.Phase.ARMOR, "on commence par BRISER L'ARMURE")
	assert_eq(combat.plates().size(), 4, "quatre plaques")
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001, "armure intacte")

func test_the_four_plates_are_spread_around_the_shell() -> void:
	var combat := _make()
	var seen: Array[float] = []
	for plate in combat.plates():
		seen.append(plate.base_angle)
	assert_eq(seen.size(), 4, "quatre angles")
	for i in 4:
		assert_almost_eq(seen[i], TAU * i / 4.0, 0.001, "reparties regulierement")

func test_the_shell_turns_and_swaps_which_plate_is_exposed() -> void:
	var combat := _make()
	var exposed_at_start := combat.plates()[0].is_exposed(combat.shell_rotation(), 100.0)
	combat.tick(combat.tuning.shell_orbit_period * 0.5)
	var exposed_later := combat.plates()[0].is_exposed(combat.shell_rotation(), 100.0)
	assert_true(exposed_at_start != exposed_later, "un demi-tour change la face exposee")

# --- LE DEFAUT CORRIGE : une seule plaque encaisse ------------------------

func test_only_the_highlighted_plate_can_be_damaged() -> void:
	# ⚠️ LE COEUR DE LA REFONTE. Avant, toute plaque dans l'arc encaissait : les degats du
	# joueur se repartissaient sur les quatre, elles descendaient ensemble et AUCUNE ne
	# tombait avant la fin de la phase. Vingt secondes de tir sans qu'une piece cede.
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

func test_a_plate_out_of_the_arc_cannot_be_damaged_through_the_target() -> void:
	var combat := _make()
	combat.tick(0.016)
	var idle: LeviathanPlate = null
	for plate in combat.plates():
		if not plate.target.enabled:
			idle = plate
			break
	assert_true(idle != null, "trois plaques sur quatre sont protegees")
	assert_false(idle.target.enabled, "le corps les masque : le tir ricoche")

func test_the_active_plate_is_announced_only_when_it_changes() -> void:
	var combat := _make()
	for i in 30:
		combat.tick(0.016)   # une demi-seconde : la plaque ne change pas
	assert_true(_active.size() <= 2, "un signal au changement, pas a chaque image (%d)" % _active.size())

func test_a_fallen_plate_never_becomes_the_target_again() -> void:
	var combat := _make()
	combat.tick(0.016)
	var first: int = _active[_active.size() - 1]
	combat._on_plate_hit(combat.plates()[first].max_health, first)
	combat.tick(0.016)
	assert_false(combat.plates()[first].target.enabled, "une plaque abattue n'encaisse plus")

# --- Les transitions ------------------------------------------------------

func test_breaking_the_four_plates_bares_the_heart() -> void:
	var combat := _make()
	_kill_plates(combat)
	_settle(combat)
	assert_eq(combat.phase(), CombatScript.Phase.HEART, "l'armure tombee, le coeur est a nu")

func test_three_plates_are_not_enough() -> void:
	var combat := _make()
	for i in 3:
		combat._on_plate_hit(combat.plates()[i].max_health, i)
	_settle(combat)
	assert_eq(combat.phase(), CombatScript.Phase.ARMOR, "la condition est MATERIELLE : quatre sur quatre")

func test_damage_alone_never_advances_a_phase() -> void:
	# C'est ce que faisait le BossController generique, et c'est ce qui rendait le boss
	# illisible : la phase changeait sans que rien a l'ecran ne l'explique.
	var combat := _make()
	for i in 40:
		combat._on_plate_hit(30.0, 0)
	_settle(combat)
	assert_eq(combat.phase(), CombatScript.Phase.ARMOR, "des degats ne font pas une phase")

func test_leaving_phase_one_clears_the_active_plate() -> void:
	var combat := _make()
	combat.tick(0.016)
	_kill_plates(combat)
	_settle(combat)
	assert_eq(_active[_active.size() - 1], -1, "plus de plaque a viser : le telegraphe s'eteint")

func test_the_heart_is_sealed_until_the_armour_breaks() -> void:
	var combat := _make()
	combat.tick(0.016)
	combat._on_heart_hit(9999.0)
	assert_eq(combat.phase(), CombatScript.Phase.ARMOR, "le coeur ne s'entame pas a travers l'armure")

func test_killing_the_heart_ends_the_fight() -> void:
	var combat := _make()
	_kill_plates(combat)
	_settle(combat)
	combat._on_heart_hit(combat.tuning.heart_health)
	assert_eq(combat.phase(), CombatScript.Phase.DEFEATED, "le coeur tombe, le boss meurt")

func test_the_whole_arc_runs_through_two_phases_in_order() -> void:
	var combat := _make()
	_kill_plates(combat); _settle(combat)
	combat._on_heart_hit(combat.tuning.heart_health)
	assert_eq(_phases, [CombatScript.Phase.ARMOR, CombatScript.Phase.HEART,
		CombatScript.Phase.DEFEATED] as Array[int], "deux phases, puis la mort")

# --- La coquille et l'aspiration ------------------------------------------

func test_the_shell_opens_only_once_the_heart_is_bared() -> void:
	var combat := _make()
	combat.tick(1.0)
	assert_almost_eq(combat.shell_open_ratio(), 0.0, 0.001, "phase 1 : la coque reste close")
	_kill_plates(combat); _settle(combat)
	assert_true(combat.shell_open_ratio() > 0.0, "phase 2 : elle s'ecarte, et c'est ca qui dit la phase")

func test_the_pull_comes_in_waves_and_lets_go() -> void:
	# L'aspiration etait une phase entiere (« RESISTER ») ; elle est devenue une pression
	# intermittente. Une pression qui ne relache jamais est une phase deguisee.
	var combat := _make()
	_kill_plates(combat); _settle(combat)
	var pulling := false
	var released := false
	for i in 900:   # 15 s a 1/60
		combat.tick(1.0 / 60.0)
		if _pull.size() > 0:
			var last: float = _pull[_pull.size() - 1]
			if last > 0.0:
				pulling = true
			elif pulling:
				released = true
	assert_true(pulling, "l'aspiration arrive")
	assert_true(released, "et elle relache : le joueur respire entre deux vagues")

func test_the_pull_always_leaves_the_player_able_to_flee() -> void:
	var combat := _make()
	assert_true(combat.tuning.pull_speed_max < combat.tuning.reference_player_max_speed,
		"elle presse, elle ne prend jamais les commandes")

# --- LE DEFAUT CORRIGE : la jauge ne ment plus ----------------------------

func test_the_gauge_shows_the_current_phase_not_the_whole_fight() -> void:
	# ⚠️ LE DEFAUT QUE L'OPERATEUR A SIGNALE DEUX FOIS. La jauge divisait par les PV des
	# quatre phases : briser toute l'armure ne valait que 30 % de barre, et le joueur
	# lisait « 70 % » apres vingt secondes d'effort. Il en concluait qu'il ne servait a
	# rien — et il avait raison de le croire, c'est ce que la barre lui disait.
	var combat := _make()
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001, "barre pleine au debut")
	_kill_plates(combat)
	assert_almost_eq(combat.structure_ratio(), 0.0, 0.001,
		"l'armure brisee VIDE la barre — elle n'en grignotait qu'un tiers")

func test_the_gauge_refills_when_the_next_phase_opens() -> void:
	# L'idiome de shmup : « il lui reste une deuxieme barre ». Preferable a une barre
	# unique qui n'avance que d'un tiers pour vingt secondes de jeu.
	var combat := _make()
	_kill_plates(combat); _settle(combat)
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001, "phase 2 : la barre est pleine a nouveau")
	combat._on_heart_hit(combat.tuning.heart_health * 0.5)
	assert_almost_eq(combat.structure_ratio(), 0.5, 0.01, "et elle descend quand on frappe le coeur")

func test_the_gauge_never_goes_below_zero() -> void:
	var combat := _make()
	for i in 200:
		combat._on_plate_hit(1000.0, 0)
	assert_true(combat.structure_ratio() >= 0.0, "jamais negative, meme surdosee")

# --- Montage sur un VRAI BossController : le corps clos et la mort ---------
## Les tests ci-dessus pilotent le module seul. Ici on monte le module sous un vrai
## `BossController`, comme la scène, pour éprouver les deux points de câblage que le
## module seul ne couvre pas : le corps reste CLOS tout le combat (rien ne le tue
## directement), et c'est le module qui fait mourir le boss quand le cœur tombe — sans
## quoi le corps clos ne mourrait jamais et la finale du niveau ne partirait pas.

func _rig() -> Array:
	var bm := track(BulletManager.new()) as BulletManager
	# `combat` n'est pas suivi : il devient enfant de `boss`, qui le libere avec lui.
	var boss := track(BossScript.new()) as BossController
	boss.max_health = 20000.0
	boss.hitbox_radius = 2.7
	boss.entry_plane_position = Vector2(0.0, 5.5)
	# Comme la scène : le module prend l'armement, le boss ne lit pas de bouches
	# génériques (sans quoi `_ready` chercherait un `Muzzle_C` sur une coque nulle).
	boss.external_attacks = true
	var combat: LeviathanCombat = CombatScript.new()
	combat.tuning = LeviathanTuning.new()
	boss.add_child(combat)
	boss._ready()
	combat._ready()   # connecte began/defeated AVANT begin, qui monte le module
	boss.begin(bm, null)
	# Sortir de la phase d'entrée : tant qu'elle dure le corps est invulnérable par
	# construction, ce qui masquerait la fermeture qu'on veut justement éprouver.
	boss.plane_position = boss.entry_plane_position
	boss._physics_process(1.0 / 60.0)
	return [boss, combat]

func test_the_body_stays_closed_and_only_the_heart_kills_the_boss() -> void:
	var rig := _rig()
	var boss: BossController = rig[0]
	var combat: LeviathanCombat = rig[1]
	var died: Array[bool] = [false]
	boss.defeated.connect(func(_world: Vector3) -> void: died[0] = true)
	assert_false(boss.vulnerable, "phase 1 : le corps est clos, aucun tir ne l'entame")
	_kill_plates(combat); _settle(combat)
	assert_false(boss.vulnerable, "phase 2 : le corps reste clos, seul le coeur compte")
	assert_false(died[0], "tant que le coeur tient, le boss vit")
	combat._on_heart_hit(combat.tuning.heart_health)
	assert_eq(combat.phase(), CombatScript.Phase.DEFEATED, "le coeur tombe")
	assert_true(died[0], "et le module fait mourir le BossController : `defeated` est emis")

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

func test_a_dead_piece_cannot_be_damaged_twice() -> void:
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
	var combat := track(CombatScript.new()) as LeviathanCombat
	combat.tick(0.5)
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001, "degrade proprement, sans planter")
