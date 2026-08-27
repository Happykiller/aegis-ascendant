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


## Un reglage LIVRE, mais avec les verrous rallumes. Ils sont eteints en jeu depuis le
## playtest du 2026-08-27 (« les boules vertes, c'est pas logique ») ; le mecanisme reste
## code et teste, la spec lui prevoyant deux autres roles. Ces gardes portent donc sur LE
## MECANISME, jamais sur la configuration livree — qui a sa propre garde ailleurs.
func _tuning_with_locks() -> LeviathanTuning:
	var t: LeviathanTuning = load("res://resources/bosses/pale_leviathan_tuning.tres").duplicate(true)
	t.node_count = 4
	return t

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

## ⚠️ CE TEST GARDAIT LE DEFAUT. Il affirmait `base_angle == TAU*i/4` — « reparties
## regulierement » — c'est-a-dire exactement ce que le code faisait, et non ce qu'il
## devait faire. La coque porte ses quatre plaques sur un CROISSANT de 198 deg
## (`Shell_Crescent`, silhouette validee par BRIEF-0041), pas sur un tour complet. Le
## test etait donc vert pendant que la hitbox se posait jusqu'a 5,05 m du maillage.
##
## Sans coque montee, le repli regulier reste la bonne reponse : c'est le seul cas ou il
## n'y a rien a mesurer. C'est ce que ce test garde desormais — le repli, et rien de plus.
func test_without_a_hull_the_plates_fall_back_to_an_even_spread() -> void:
	var combat := _make()
	for i in combat.plates().size():
		var expected := wrapf(TAU * i / 4.0, -PI, PI)
		var actual: float = combat.plates()[i].base_angle
		assert_almost_eq(wrapf(actual - expected, -PI, PI), 0.0, 0.001,
			"repli regulier a defaut de coque")
		assert_almost_eq(combat.plates()[i].radius, 2.6, 0.001, "rayon de repli")

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

func test_the_flux_follows_the_dive_anchor_not_the_boss_body() -> void:
	# ⚠️ LE DEFAUT QUE CETTE GARDE EMPECHE. Depuis que la plongee bascule vers une zone
	# dediee, le boss reste DEHORS : sa coque n'est plus la ou se trouve le joueur. Laisser
	# le flux au centre du corps du boss le posait hors de l'arene interieure — on tirerait
	# dans le vide, sans erreur, sans test rouge, et sans que rien a l'ecran le dise.
	var combat := _make()
	var anchor := Vector2(3.0, -5.0)
	combat.dive_anchor = anchor
	_kill_armour(combat)
	combat.tick(0.016)                                    # bascule armure -> plongee
	combat.tick(combat.tuning.dive_enter_time + 0.02)     # entree consommee
	# ⚠️ L'ENVELOPPE DE DERIVE N'EST PAS UN CERCLE, et elle n'est plus recopiee ici : la
	# figure de base est une Lissajous dont le coin atteint sqrt(2) x rayon, et la derive
	# organique (ADR-0029) s'y ajoute. Le code l'expose, le test la LIT — deux formules
	# separees n'auraient pu que diverger.
	var drift: float = combat.flux_drift_envelope()
	var to_anchor := combat._flux_target.position - anchor
	assert_true(to_anchor.length() <= drift + 0.01,
		"le flux vit sur l'ancre de plongee, a sa derive pres : %.2f m" % to_anchor.length())
	assert_true(combat._flux_target.position.length() > drift + 0.01,
		"et surtout PAS sur le corps du boss, reste dehors")

func test_without_an_anchor_the_flux_stays_on_the_boss() -> void:
	# La valeur au repos (`Vector2.INF`) doit rendre EXACTEMENT le comportement d'avant :
	# c'est ce qui permet aux tests, qui ne montent aucune zone, de rester comparables.
	var combat := _make()
	_kill_armour(combat)
	combat.tick(0.016)
	combat.tick(combat.tuning.dive_enter_time + 0.02)
	var drift: float = combat.flux_drift_envelope()
	assert_true(combat._flux_target.position.length() <= drift + 0.01,
		"sans ancre, le flux reste au corps du boss")

func test_the_anchor_is_ignored_outside_the_dive() -> void:
	# Une ancre posee trop tot ne doit pas deplacer une cible qui n'existe pas encore dans
	# l'arene : hors plongee, la seule verite est le corps du boss.
	var combat := _make()
	combat.dive_anchor = Vector2(9.0, 9.0)
	combat.tick(0.5)
	var drift: float = combat.flux_drift_envelope()
	assert_true(combat._flux_target.position.length() <= drift + 0.01,
		"pendant l'armure, l'ancre ne dit rien")

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
	#
	# ⚠️ CE TEST TUAIT LE FLUX EN UNE SEULE PLONGEE. Le plafond par passage (ADR-0026) le
	# rend impossible — et c'est tout son objet : trois cycles sont desormais le meilleur
	# cas, garanti par construction. On draine donc les deux premiers passages avant de
	# verifier ce qui est reellement en jeu ici, l'ejection du DERNIER.
	var combat := _make()
	for _cycle in 2:
		_kill_armour(combat)
		combat.tick(0.016)
		combat.tick(combat.tuning.dive_enter_time + 0.01)
		combat._on_flux_hit(combat.tuning.flux_health)   # sature le passage
		combat.tick(combat.tuning.dive_time + 0.01)
		combat.tick(combat.tuning.dive_eject_time + 0.01)
		combat.tick(2.0)
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


# --- LE DEFAUT CORRIGE : la hitbox etait ailleurs que le maillage ---------

## Une coque synthetique aux cotes REELLES de `pale_leviathan.glb`, mesurees dans le
## fichier : `Shell_Ring` a (0, 0,4, 0), `Shell_Crescent` a (0, 0,54, 3,86), et les quatre
## plaques a leurs translations locales. Le `BossController` fait tourner la coque de
## `FACING_PLAYER = (0, PI, 0)` : on le reproduit, sans quoi on mesure le repere du
## FICHIER en croyant mesurer celui du JEU — l'erreur qui a coute BRIEF-0045.
func _fake_hull() -> Node3D:
	var hull := Node3D.new()
	hull.rotation = Vector3(0.0, PI, 0.0)
	var ring := Node3D.new()
	ring.name = "Shell_Ring"
	ring.position = Vector3(0.0, 0.4, 0.0)
	hull.add_child(ring)
	var crescent := Node3D.new()
	crescent.name = "Shell_Crescent"
	crescent.position = Vector3(0.0, 0.54, 3.86)
	ring.add_child(crescent)
	var local := [
		Vector3(-2.737, 0.16, -5.315), Vector3(-2.786, 0.16, -2.501),
		Vector3(-0.538, 0.16, -0.807), Vector3(2.153, 0.16, -1.63),
	]
	for i in 4:
		var plate := Node3D.new()
		plate.name = "Plate_%02d" % (i + 1)
		plate.position = local[i]
		crescent.add_child(plate)
	# Les quatre epines et leurs bouches. Sans elles le module remplit le journal de
	# « coque sans 'Spike_NN' » : du bruit qu'on finit par ne plus lire, et c'est ce
	# bruit-la qui noie la prochaine vraie erreur.
	var roots := [
		Vector3(3.60, 0.30, 2.10), Vector3(-3.60, 0.30, 2.10),
		Vector3(-3.60, 0.30, -2.10), Vector3(3.60, 0.30, -2.10),
	]
	var tips := [
		Vector3(4.70, 0.30, -1.60), Vector3(-4.70, 0.30, -1.60),
		Vector3(-4.20, 0.30, -4.90), Vector3(4.20, 0.30, -4.90),
	]
	for i in 4:
		var spike := Node3D.new()
		spike.name = "Spike_%02d" % (i + 1)
		spike.position = roots[i]
		hull.add_child(spike)
		var muzzle := Node3D.new()
		muzzle.name = "Muzzle_Spike_%02d" % (i + 1)
		muzzle.position = tips[i] - roots[i]
		spike.add_child(muzzle)
	return hull

func _rig_with_hull() -> Array:
	var rig := _rig()
	var boss: BossController = rig[0]
	var combat: LeviathanCombat = rig[1]
	var hull := _fake_hull()
	boss.add_child(hull)
	combat.setup(hull, null, null)
	return [boss, combat, hull]

func test_the_plate_angles_come_from_the_hull_not_from_a_convention() -> void:
	var rig := _rig_with_hull()
	var combat: LeviathanCombat = rig[1]
	# Azimuts du plan de jeu, mesures dans le .glb puis convertis (angle_plan = 180 - a_fichier).
	# Ils tombent sur les `PLATES` du script Blender, ce qui les confirme deux fois.
	var expected := [-28.0, 26.0, 80.0, 134.0]
	for i in combat.plates().size():
		var got: float = rad_to_deg(combat.plates()[i].base_angle)
		assert_almost_eq(wrapf(got - expected[i], -180.0, 180.0), 0.0, 0.5,
			"Plate_%02d lue sur la coque" % [i + 1])
		assert_almost_eq(combat.plates()[i].radius, 3.10, 0.01,
			"Plate_%02d est a 3,10 m de l'axe" % [i + 1])

## ⚠️ LE TEST QUI MANQUAIT, ET AUCUN AUTRE NE POUVAIT LE REMPLACER. Une hitbox ne se
## dessine pas : ni une capture, ni un rendu, ni un test de mecanique ne montrent qu'elle
## a glisse. Elle se posait a `TAU*i/alive` pendant que le maillage restait a sa place
## sculptee — jusqu'a 5,05 m d'ecart sur une coque de 11 m. La plaque qui BRILLE n'etait
## pas celle qu'on pouvait TOUCHER, et le joueur n'avait aucun moyen de le savoir.
func test_the_hitbox_sits_under_the_mesh_it_highlights() -> void:
	var rig := _rig_with_hull()
	var boss: BossController = rig[0]
	var combat: LeviathanCombat = rig[1]
	# Plusieurs poses d'orbite : un seul instant pourrait coincider par hasard.
	for step in 6:
		combat.tick(combat.tuning.shell_orbit_period / 6.0)
		for plate in combat.plates():
			if plate.node == null:
				continue
			var mesh_at := boss.plane_position + GameplayPlane.to_plane(
				CombatScript._relative_to(plate.node, boss).origin)
			var gap := plate.target.position.distance_to(mesh_at)
			assert_true(gap < 0.25,
				"pose %d, Plate_%02d : hitbox a %.2f m du maillage" % [step, plate.index + 1, gap])


# --- LE DEFAUT CORRIGE : le vide du croissant passait devant le joueur ----

## ⚠️ CE QUE CE TEST GARDE, ET QU'AUCUN AUTRE NE PEUT GARDER. L'armure ne couvre pas le
## tour du boss : c'est un CROISSANT de 198 deg. En rotation continue, son vide se
## presentait au joueur 27 % du temps au premier cycle et 37 % au deuxieme — deux a trois
## secondes par tour sans AUCUNE cible. Aucun test ne pouvait le voir tant que les angles
## de plaque etaient fictifs : sur une repartition reguliere de 360 deg, le trou n'existe
## pas. Le defaut ne s'est revele qu'une fois la geometrie mesuree.
##
## Il se garde ici et pas dans `validate()` : le tuning ne connait pas les azimuts de la
## coque, et le seuil `arc >= 360/alive` qui y vit compare l'arc a une repartition que la
## coque n'a jamais portee.
func test_the_crescent_never_shows_its_gap_to_the_player() -> void:
	var rig := _rig_with_hull()
	var combat: LeviathanCombat = rig[1]
	var t := combat.tuning
	# Deux allers-retours complets, echantillonnes finement : un pas grossier pourrait
	# enjamber le creux au lieu de le trouver.
	var steps := 240
	var blind := 0
	for k in steps:
		combat.tick(2.0 * t.shell_orbit_period / float(steps))
		var armed := 0
		for plate in combat.plates():
			if plate.target != null and plate.target.enabled:
				armed += 1
		if armed == 0:
			blind += 1
		assert_true(armed <= 1, "jamais plus d'une plaque vulnerable a la fois")
	assert_eq(blind, 0, "%d/%d instants sans aucune cible" % [blind, steps])

## Le balancement doit faire DEFILER les plaques, pas en designer une seule a vie : sinon
## on a supprime le temps mort en supprimant le mouvement, et les trois autres plaques ne
## servent plus a rien.
func test_the_sway_brings_every_plate_to_the_front_in_turn() -> void:
	var rig := _rig_with_hull()
	var combat: LeviathanCombat = rig[1]
	var t := combat.tuning
	var seen := {}
	for k in 240:
		combat.tick(2.0 * t.shell_orbit_period / 240.0)
		for plate in combat.plates():
			if plate.target != null and plate.target.enabled:
				seen[plate.index] = true
	assert_eq(seen.size(), 4, "les quatre plaques passent en tete, pas seulement une")


# --- LE GRIEF D'ORIGINE : « les lasers, ca sort d'un peu n'importe ou » ---

## ⚠️ CE QUE CE TEST GARDE. Le faisceau partait de la pointe de l'epine mais visait le
## JOUEUR : la piece montrait une direction, le tir en prenait une autre. C'etait une
## dette assumee — deux epines sur quatre pointaient vers l'arriere, et prolonger leur axe
## aurait tire a l'oppose de la cible. BRIEF-0081 a reforge la coque (les quatre visent le
## joueur), donc l'axe est enfin une direction de tir defendable.
##
## La direction se MESURE, base vers pointe, au lieu de se deduire d'un angle : elle ne
## depend alors d'aucune convention de repere. C'est ce qui a coute BRIEF-0045, ou des
## angles releves dans le `.glb` avaient ete pris pour ceux du jeu, a 180 degres pres.
func test_the_beam_extends_the_spine_instead_of_tracking_the_player() -> void:
	var rig := _rig_with_hull()
	var boss: BossController = rig[0]
	var combat: LeviathanCombat = rig[1]
	var origin: Vector2 = boss.plane_position
	for i in 4:
		combat._aim_spine(i, origin)
		# Le faisceau lui-meme n'est monte que dans l'arbre de scene, donc jamais ici :
		# c'est `_spine_aim` qui porte la direction, releve a chaque pointage.
		var fired: Vector2 = combat._spine_aim[i]
		var node: Node3D = combat._spine_nodes[i]
		var here := CombatScript._relative_to(node, boss)
		var base := GameplayPlane.to_plane(here.origin)
		var tip := GameplayPlane.to_plane(here * combat._spine_tip[i])
		var axis := (tip - base).normalized()
		assert_almost_eq(fired.dot(axis), 1.0, 0.01,
			"epine %d : le faisceau prolonge l'axe (ecart %.1f deg)"
				% [i, rad_to_deg(fired.angle_to(axis))])

# --- Le plafond de degats par plongee (ADR-0026) ---------------------------

func test_one_dive_can_never_kill_more_than_its_share() -> void:
	# ⚠️ LE DEFAUT QUE CE PLAFOND SUPPRIME. Trois playtests ont donne 6, 4 puis 2 plongees
	# pour le meme joueur : les degats places par passage vont de 600 a plus de 1200, et
	# aucune valeur de flux_health ne peut satisfaire « survit a 2 » ET « tombe au 3e ».
	# Le boss est mort en DEUX cycles, la panne exacte que l'invariant 5 nommait.
	var combat := _make()
	_kill_armour(combat)
	combat.tick(0.016)
	combat.tick(combat.tuning.dive_enter_time + 0.02)
	# Un tir absurde, tres au-dela de ce qu'un joueur peut placer.
	combat._on_flux_hit(999999.0)
	var share: float = combat.tuning.flux_damage_per_dive()
	assert_true(combat.fight_ratio() > 0.0, "une seule plongee ne peut pas tuer le boss")
	assert_almost_eq(combat.tuning.flux_health - share, _flux_left(combat), 0.5,
		"une plongee retire AU PLUS un tiers de la reserve")

func test_a_saturated_dive_stops_counting_but_the_fight_goes_on() -> void:
	var combat := _make()
	_kill_armour(combat)
	combat.tick(0.016)
	combat.tick(combat.tuning.dive_enter_time + 0.02)
	combat._on_flux_hit(999999.0)
	var after_first := _flux_left(combat)
	combat._on_flux_hit(999999.0)   # on continue de tirer : ca ne compte plus
	assert_almost_eq(_flux_left(combat), after_first, 0.001,
		"le flux sature ne perd plus rien pendant CE passage")

## ⚠️ LE DEFAUT NOMME AU PLAYTEST DU 2026-08-27. Le quota rempli, les tirs portaient encore
## mais ne comptaient plus, la jauge se figeait, et le joueur attendait les 5 s de
## `dive_time` sans rien pouvoir faire. `ADR-0026` demandait pourtant l'inverse en toutes
## lettres : « mieux jouer RACCOURCIT chaque plongee sans jamais en supprimer une ».
##
## La garde porte sur l'INSTANT de la sortie, pas sur son existence : sans elle, une
## regression rendrait simplement la plongee plus longue — et rien ne serait rouge.
func test_filling_the_quota_ejects_at_once_instead_of_waiting_out_the_clock() -> void:
	var combat := _make()
	var ended: Array = []
	combat.dive_ended.connect(func(c: int, _down: bool) -> void: ended.append(c))
	_kill_armour(combat)
	combat.tick(0.016)
	combat.tick(combat.tuning.dive_enter_time + 0.02)
	assert_eq(ended.size(), 0, "on est bien dans le noyau, la plongee court encore")
	combat._on_flux_hit(combat.tuning.flux_damage_per_dive())
	assert_eq(ended.size(), 1,
		"le quota rempli EJECTE — sans une seule seconde de dive_time consommee")

## Et le revers, qui est la raison d'etre du minuteur : rater sa plongee doit couter du
## TEMPS. Supprimer `dive_time` en meme temps que l'attente aurait rendu la phase gratuite.
func test_a_missed_dive_still_waits_out_its_clock() -> void:
	var combat := _make()
	var ended: Array = []
	combat.dive_ended.connect(func(c: int, _down: bool) -> void: ended.append(c))
	_kill_armour(combat)
	combat.tick(0.016)
	combat.tick(combat.tuning.dive_enter_time + 0.02)
	combat._on_flux_hit(1.0)   # trois fois rien
	assert_eq(ended.size(), 0, "un coup isole ne libere pas la plongee")
	combat.tick(combat.tuning.dive_time + 0.01)
	assert_eq(ended.size(), 1, "c'est le minuteur qui la termine, comme avant")

## ⚠️ LA GARDE DU REPERE DE CIBLE. Le flux derive de plusieurs unites autour de son ancre,
## et rien ne le dessinait dans l'arene : le halo du flux se pose sur le coeur du boss,
## RESTE DEHORS pendant la plongee. Le joueur tirait sur le reacteur du decor pendant que la
## cible etait ailleurs — « le noyau semble juste un point du decor » (playtest 2026-08-27).
##
## Ce que le test garde, c'est que la position PUBLIEE — celle que le niveau pose sous le
## repere — est bien celle de la CIBLE, et non celle de l'ancre. Les deux se ressemblent une
## fraction de seconde apres l'entree ; c'est ce qui rend l'erreur invisible autrement.
func test_the_published_flux_position_is_the_target_not_the_anchor() -> void:
	var combat := _make()
	var anchor := Vector2(3.0, -5.0)
	combat.dive_anchor = anchor
	_kill_armour(combat)
	combat.tick(0.016)
	combat.tick(combat.tuning.dive_enter_time + 0.02)
	combat.tick(1.1)   # le temps que la derive s'ecarte
	var published := combat.flux_plane_position()
	assert_true(published.distance_to(combat._flux_target.position) < 0.001,
		"le niveau lit la cible reelle (%.2f m d'ecart)"
			% published.distance_to(combat._flux_target.position))
	assert_true(published.distance_to(anchor) > 0.3,
		"et elle a bien QUITTE l'ancre (%.2f m) — sinon le repere serait inutile"
			% published.distance_to(anchor))

## La derive doit rester DANS son enveloppe : le repere suit, mais le joueur ne doit pas
## avoir a chercher la cible a l'autre bout de l'arene.
func test_the_flux_never_leaves_its_declared_envelope() -> void:
	var combat := _make()
	var anchor := Vector2(1.0, 2.0)
	combat.dive_anchor = anchor
	_kill_armour(combat)
	combat.tick(0.016)
	combat.tick(combat.tuning.dive_enter_time + 0.02)
	var envelope := combat.flux_drift_envelope()
	var worst := 0.0
	for step in 60:
		combat.tick(0.05)
		worst = maxf(worst, combat.flux_plane_position().distance_to(anchor))
	assert_true(worst <= envelope + 0.01,
		"ecart max %.2f m pour une enveloppe declaree de %.2f m" % [worst, envelope])

## ⚠️ LA REGEN NE SE MONTRE QUE SI ELLE A LIEU. Au dernier cycle le flux tombe et l'armure
## ne revient pas : une jauge verte qui monterait la promettrait pour rien — un signal faux,
## que la loi des signaux tient pour pire qu'un signal absent.
## ⚠️ ET LE PIEGE DU TEST LUI-MEME : on NE PEUT PAS abattre le flux en une plongee, les
## degats sont plafonnes a un tiers par passage (ADR-0026). Une premiere version de cette
## garde croyait tuer le boss du premier coup et accusait le code de promettre une armure —
## alors qu'elle revenait bel et bien. Il faut donc aller jusqu'au TROISIEME cycle.
func test_the_regen_gauge_never_promises_an_armour_that_is_not_coming() -> void:
	var combat := _make()
	var per_dive := combat.tuning.flux_damage_per_dive()
	var seen: Array[float] = []
	combat.armour_regen.connect(func(r: float, _p: int) -> void: seen.append(r))
	for cycle in 2:
		_kill_armour(combat)
		_ride_dive(combat, per_dive)
	seen.clear()                       # les deux premieres reconstructions ont bien eu lieu
	_kill_armour(combat)
	_ride_dive(combat, per_dive)       # la derniere : le flux tombe, rien ne revient
	assert_eq(combat.phase(), CombatScript.Phase.DEFEATED, "le boss est bien mort")
	for value in seen:
		assert_true(value <= 0.0,
			"aucune promesse de reconstruction quand le boss meurt (%.2f)" % value)

func test_the_regen_gauge_fills_while_the_armour_comes_back() -> void:
	var combat := _make()
	var seen: Array[float] = []
	combat.armour_regen.connect(func(r: float, _p: int) -> void: seen.append(r))
	_kill_armour(combat)
	_ride_dive(combat, 10.0)   # on rate : l'armure va revenir
	assert_true(seen.size() >= 2, "la reconstruction s'annonce pendant l'ejection")
	assert_true(seen.max() > 0.0, "et la jauge monte")
	assert_almost_eq(seen[seen.size() - 1], 0.0, 0.001,
		"puis s'efface quand l'armure est la — sinon elle resterait en travers du combat")

## ⚠️ LES DEUX CIBLES SONT EXACTEMENT COMPLEMENTAIRES, et c'est ce qui rend le blindage
## honnete. Jamais les deux (on toucherait le noyau ET le blindage), jamais aucune (les tirs
## traverseraient sans rien produire — le defaut nomme sur le Harvester : « tirer dessus sans
## rien produire a l'ecran se lit comme un defaut, pas comme une armure »).
func test_the_shield_and_the_core_are_never_both_open_nor_both_shut() -> void:
	var combat := _make()
	combat.tuning = _tuning_with_locks()
	combat.dive_anchor = Vector2.ZERO
	_kill_armour(combat)
	combat.tick(0.016)
	combat.tick(combat.tuning.dive_enter_time + 0.02)
	# ⚠️ LES VERROUS D'ABORD. Tant qu'un node tient, le corridor ne s'ouvre JAMAIS — c'est
	# la seconde porte, et l'oublier ici ferait accuser le blindage.
	for i in combat.tuning.node_count:
		combat._on_node_hit(combat.tuning.node_health, i)
	assert_eq(combat.nodes_alive(), 0, "les verrous sont a terre")
	var seen_open := false
	var seen_shut := false
	for step in 200:
		combat.tick(0.05)
		if combat.phase() != CombatScript.Phase.DIVE:
			break
		# ⚠️ SEULEMENT DANS LE NOYAU. Pendant l'entree et l'ejection, les DEUX cibles sont
		# eteintes a juste titre : la complementarite ne vaut que la ou l'on tire.
		if combat._dive != CombatScript.Dive.INSIDE:
			continue
		var core: bool = combat._flux_target.enabled
		var shield: bool = combat._shield_target.enabled
		assert_true(core != shield,
			"noyau=%s blindage=%s — il en faut exactement UN" % [core, shield])
		seen_open = seen_open or core
		seen_shut = seen_shut or shield
	assert_true(seen_open, "le corridor s'ouvre au moins une fois")
	assert_true(seen_shut, "et il se ferme au moins une fois — sinon le blindage ne sert a rien")

## ⚠️ LES VERROUS SONT LA PREMIERE PORTE, ET ELLE EST ABSOLUE. Corridor ouvert ou non, tant
## qu'un node tient, le flux est intouchable. Sans cette garde, un reglage qui les
## desactiverait par megarde rendrait le noyau atteignable des l'entree, et la phase
## reviendrait a ce qu'elle etait.
func test_a_single_surviving_lock_keeps_the_core_shut() -> void:
	var combat := _make()
	combat.tuning = _tuning_with_locks()
	combat.dive_anchor = Vector2.ZERO
	_kill_armour(combat)
	combat.tick(0.016)
	combat.tick(combat.tuning.dive_enter_time + 0.02)
	# On en abat tous SAUF un.
	for i in combat.tuning.node_count - 1:
		combat._on_node_hit(combat.tuning.node_health, i)
	assert_eq(combat.nodes_alive(), 1, "il en reste un")
	for step in 120:
		combat.tick(0.05)
		if combat._dive != CombatScript.Dive.INSIDE:
			break
		assert_false(combat._flux_target.enabled,
			"le dernier verrou tient : le noyau reste ferme")

## ⚠️ CETTE GARDE AFFIRMAIT LE CONTRAIRE, ET ELLE AVAIT TORT. Ecrite le matin meme, elle
## disait « ils reviennent ENTIERS : les cycles ne sont pas cumulatifs ». Le playtest a
## montre ou menait cette regle : un joueur qui ne peut pas abattre quatre verrous en cinq
## secondes ne touche JAMAIS le flux, et le combat ne se termine pas. Un mur remis a neuf a
## chaque tentative n'est pas une difficulte.
##
## La regle est desormais celle de l'armure (`ADR-0021`, « le boss se repare de plus en plus
## mal ») : ils reviennent AMOINDRIS. Un joueur qui en abat deux par passage progresse.
func test_the_locks_come_back_diminished_like_the_armour() -> void:
	var combat := _make()
	combat.tuning = _tuning_with_locks()
	_kill_armour(combat)
	combat.tick(0.016)
	combat.tick(combat.tuning.dive_enter_time + 0.02)
	for i in combat.tuning.node_count:
		combat._on_node_hit(combat.tuning.node_health, i)
	assert_eq(combat.nodes_alive(), 0, "abattus au premier passage")
	_ride_dive(combat, 10.0)
	_kill_armour(combat)
	combat.tick(0.016)
	combat.tick(combat.tuning.dive_enter_time + 0.02)
	assert_eq(combat.nodes_alive(), combat.tuning.node_count - 1,
		"et un de moins au suivant : le boss se repare de plus en plus mal")

func test_three_perfect_dives_are_exactly_enough() -> void:
	# Trois cycles deviennent le MEILLEUR cas, vrai par construction et non par calibrage.
	var combat := _make()
	for cycle in 3:
		_kill_armour(combat)
		combat.tick(0.016)
		combat.tick(combat.tuning.dive_enter_time + 0.02)
		combat._on_flux_hit(999999.0)
		combat.tick(combat.tuning.dive_time + 0.01)
		combat.tick(combat.tuning.dive_eject_time + 0.01)
		combat.tick(2.0)
	assert_eq(combat.phase(), LeviathanCombat.Phase.DEFEATED,
		"trois passages parfaits suffisent, et pas deux")

## Reserve restante du flux — lue sur le module, pas recalculee.
func _flux_left(combat: LeviathanCombat) -> float:
	return combat._flux_health

## ⚠️ LE DEFAUT LE PLUS GRAVE DE LA JOURNEE, ET IL EST SORTI D'UN PLAYTEST. Rien ne bornait
## le nombre de cycles : le plafond d'ADR-0026 s'appliquait a TOUS les passages, si bien
## qu'un joueur qui ne remplit jamais son quota voyait « DERNIER ASSAUT » se repeter sans
## fin. Onze fois, avant que l'operateur ne ferme le jeu.
##
## Le plafond existe pour empecher de finir TROP TOT, pas pour empecher de finir. Cette
## garde verifie qu'un joueur MEDIOCRE — un tiers du quota par plongee — voit quand meme la
## fin, et qu'un joueur PARFAIT ne la voit toujours pas avant le troisieme cycle.
## ⚠️ ET C'EST BIEN LES VERROUS QU'IL FAUT EPROUVER, PAS LE PLAFOND. Une premiere version
## de cette garde nourrissait `_on_flux_hit` directement : elle passait MEME SANS la
## correction, parce qu'elle ne reproduisait pas la panne. Le vrai scenario est un joueur
## qui n'abat qu'UNE PARTIE des verrous par plongee — il ne touche alors jamais le flux, et
## si les verrous se relevent entiers, il ne le touchera JAMAIS.
func test_a_player_who_cannot_clear_the_locks_in_one_dive_still_progresses() -> void:
	var combat := _make()
	combat.tuning = _tuning_with_locks()
	combat.dive_anchor = Vector2.ZERO
	var reached := false
	for attempt in 12:
		if combat.phase() == CombatScript.Phase.DEFEATED:
			break
		_kill_armour(combat)
		combat.tick(0.016)
		combat.tick(combat.tuning.dive_enter_time + 0.02)
		# Il n'en abat que DEUX par passage : c'est tout ce que cinq secondes lui laissent.
		var killed := 0
		for i in combat.tuning.node_count:
			if killed >= 2:
				break
			if combat.node_alive(i):
				combat._on_node_hit(combat.tuning.node_health, i)
				killed += 1
		if combat.nodes_alive() == 0:
			reached = true
			combat._on_flux_hit(combat.tuning.flux_damage_per_dive())
		combat.tick(combat.tuning.dive_time + 0.01)
		combat.tick(combat.tuning.dive_eject_time + 0.01)
		combat.tick(2.0)
	assert_true(reached,
		"il finit par atteindre le flux : sans quoi le combat est INFINI (%d cycles)" % combat.cycle())
	assert_eq(combat.phase(), CombatScript.Phase.DEFEATED,
		"et le combat se termine — il a tenu %d cycles" % combat.cycle())

func test_a_perfect_player_still_never_finishes_before_the_third_cycle() -> void:
	var combat := _make()
	var per_dive := combat.tuning.flux_damage_per_dive()
	_kill_armour(combat)
	_ride_dive(combat, per_dive * 10.0)   # il place tout ce qu'il peut
	assert_true(combat.phase() != CombatScript.Phase.DEFEATED, "pas au premier passage")
	_kill_armour(combat)
	_ride_dive(combat, per_dive * 10.0)
	assert_true(combat.phase() != CombatScript.Phase.DEFEATED, "ni au deuxieme")
