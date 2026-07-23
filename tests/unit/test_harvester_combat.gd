extends "res://tests/test_case.gd"
## Le combat du Choir Harvester : appendices destructibles, iris, noyau.
##
## POURQUOI TOUT EST TESTÉ ICI — la boucle demande **trois cycles** et une repousse de
## neuf secondes par appendice : la voir en entier réclame plusieurs minutes de jeu
## réel. Aucune capture d'écran n'ira là-bas, et une partie manuelle ne prouve rien
## sur la synchronisation de l'iris. C'est le cas type de
## `.claude/resources/pratique-verifier-par-test.md`.
##
## On passe par les VRAIS chemins : un vrai `BulletManager`, les vraies `BulletTarget`
## enregistrées par le module, le vrai `BossController`. Le seul raccourci est
## l'absence de coque 3D — `setup()` l'accepte, et un appendice sans nœud à poser
## reste un appendice qui vit, meurt et repousse.

const BossScript := preload("res://scripts/bosses/boss_controller.gd")
const TUNING_PATH := "res://resources/bosses/choir_harvester_tuning.tres"

var _deflections: int = 0

func _on_deflected(_world_position: Vector3) -> void:
	_deflections += 1

## Boss + module montés à la main, sortis de leur phase d'entrée, prêts à encaisser.
## Retourne `[boss, combat, bullet_manager]`.
func _rig() -> Array:
	var tuning := load(TUNING_PATH) as HarvesterTuning
	var bm := BulletManager.new()
	var boss: BossController = BossScript.new()
	boss.max_health = 420.0
	boss.hitbox_radius = 2.0
	boss.entry_plane_position = Vector2(0.0, 4.0)
	var combat := HarvesterCombat.new()
	combat.tuning = tuning
	boss.add_child(combat)
	boss._ready()
	combat._ready()
	boss.begin(bm, null)
	# Sortir de l'entrée : tant qu'elle dure le boss est invulnérable par construction,
	# ce qui masquerait la porte qu'on veut justement éprouver.
	boss.plane_position = boss.entry_plane_position
	boss._physics_process(1.0 / 60.0)
	return [boss, combat, bm]

func _kill_limb(combat: HarvesterCombat, kind: StringName) -> void:
	for limb in combat.limbs():
		if limb.kind == kind:
			limb.target.hit_callback.call(limb.max_health)
			return
	assert_true(false, "limb %s exists" % kind)

func _kill_all_limbs(combat: HarvesterCombat) -> void:
	for kind in [HarvesterCombat.KIND_SCYTHE, HarvesterCombat.KIND_CLAW,
			HarvesterCombat.KIND_CANNON]:
		_kill_limb(combat, kind)

## Fait avancer le module de `seconds`, par pas d'image.
func _advance(combat: HarvesterCombat, seconds: float) -> void:
	var step := 1.0 / 60.0
	var elapsed := 0.0
	while elapsed < seconds:
		combat.tick(step)
		elapsed += step

func _free(rig: Array) -> void:
	(rig[2] as BulletManager).free()
	(rig[0] as BossController).free()

# --- Montage ------------------------------------------------------------------

func test_the_boss_starts_with_three_limbs_and_a_closed_iris() -> void:
	var rig := _rig()
	var combat: HarvesterCombat = rig[1]
	assert_eq(combat.limbs().size(), 3, "three limbs are built")
	assert_eq(combat.limbs_up(), 3, "all three start in service")
	assert_false(combat.is_iris_open(), "the iris starts closed")
	assert_false((rig[0] as BossController).vulnerable, "the body starts invulnerable")
	_free(rig)

func test_the_generic_attack_pattern_is_handed_over() -> void:
	var rig := _rig()
	# Sans cela, le boss tirerait SES motifs par-dessus ceux du module : deux
	# armements sur la même coque, et un rideau de balles double.
	assert_true((rig[0] as BossController).external_attacks, "the module took over the armament")
	_free(rig)

# --- L'iris -------------------------------------------------------------------

func test_destroying_all_three_limbs_opens_the_iris() -> void:
	var rig := _rig()
	var combat: HarvesterCombat = rig[1]
	_kill_limb(combat, HarvesterCombat.KIND_SCYTHE)
	combat.tick(1.0 / 60.0)
	assert_false(combat.is_iris_open(), "one limb down is not enough")
	_kill_limb(combat, HarvesterCombat.KIND_CLAW)
	combat.tick(1.0 / 60.0)
	assert_false(combat.is_iris_open(), "two limbs down is not enough")
	_kill_limb(combat, HarvesterCombat.KIND_CANNON)
	combat.tick(1.0 / 60.0)
	assert_true(combat.is_iris_open(), "the third one opens the iris")
	assert_true((rig[0] as BossController).vulnerable, "and the core becomes reachable")
	_free(rig)

## Abat les trois appendices en les espaçant de `gap`, puis MESURE la fenêtre : le
## temps pendant lequel l'iris reste ouvert.
##
## L'espacement compte. Une première version tuait les trois sur la même image — les
## trois repoussaient donc ensemble, et le test affirmait « un seul appendice est
## revenu » sur un état où il y en avait trois. En jeu, on n'abat jamais trois bras
## dans la même image : c'est l'échelonnement qui fait la mécanique.
func _window_after_chaining(gap: float) -> float:
	var rig := _rig()
	var combat: HarvesterCombat = rig[1]
	var step := 1.0 / 60.0
	_kill_limb(combat, HarvesterCombat.KIND_SCYTHE)
	_advance(combat, gap)
	_kill_limb(combat, HarvesterCombat.KIND_CLAW)
	_advance(combat, gap)
	_kill_limb(combat, HarvesterCombat.KIND_CANNON)
	combat.tick(step)
	assert_true(combat.is_iris_open(), "the third kill opened the window (gap %.2f)" % gap)
	var open_for := 0.0
	# Borne de sécurité : un iris qui ne se referme jamais est un défaut, pas une
	# boucle infinie qu'on laisse bloquer la porte de qualité.
	while combat.is_iris_open() and open_for < 30.0:
		combat.tick(step)
		open_for += step
	assert_true(open_for < 30.0, "the iris does close again (gap %.2f)" % gap)
	_free(rig)
	return open_for

## « Quand un des appendices s'est reformé, il se referme. » REFORMÉ, donc au bout du
## redéploiement — pas à la fin du minuteur d'attente.
func test_the_first_limb_back_in_service_closes_the_iris() -> void:
	var tuning := load(TUNING_PATH) as HarvesterTuning
	var window := _window_after_chaining(2.0)
	assert_true(window > 0.5, "the window is worth something (got %.2f s)" % window)
	# Le premier abattu revient `limb_rebuild_time` après SA mort, soit 2 x gap avant
	# les autres : la fenêtre est donc forcément plus courte que le délai de repousse.
	assert_true(window < tuning.limb_rebuild_time,
		"the window is shorter than the rebuild delay (got %.2f s)" % window)

## LA propriété émergente du combat : la fenêtre vaut « délai de repousse moins le
## temps mis à enchaîner ». Enchaîner vite est donc récompensé sans qu'aucune règle
## ne le dise — et c'est le genre d'affirmation de conception qui doit être mesurée,
## pas seulement écrite dans un commentaire.
func test_chaining_the_kills_faster_buys_a_longer_window() -> void:
	var patient := _window_after_chaining(2.0)
	var brisk := _window_after_chaining(0.5)
	assert_true(brisk > patient + 2.0,
		"chaining in 1 s instead of 4 s buys a longer window (%.2f s vs %.2f s)" % [brisk, patient])

func test_a_limb_returns_exactly_after_its_rebuild_delay() -> void:
	var rig := _rig()
	var combat: HarvesterCombat = rig[1]
	var tuning := combat.tuning
	_kill_limb(combat, HarvesterCombat.KIND_CLAW)
	_advance(combat, tuning.limb_rebuild_time - 0.15)
	assert_eq(combat.limbs_up(), 2, "still down just before the delay")
	_advance(combat, 0.3)
	assert_eq(combat.limbs_up(), 3, "back in service just after it")
	_free(rig)

func test_a_rebuilt_limb_comes_back_at_full_health() -> void:
	var rig := _rig()
	var combat: HarvesterCombat = rig[1]
	_kill_limb(combat, HarvesterCombat.KIND_CANNON)
	_advance(combat, combat.tuning.limb_rebuild_time + 0.2)
	for limb in combat.limbs():
		if limb.kind == HarvesterCombat.KIND_CANNON:
			assert_almost_eq(limb.health, limb.max_health, 0.001,
				"a rebuilt limb is not a wreck at 0 HP that dies to one bullet")
	_free(rig)

# --- La carapace --------------------------------------------------------------

## ⚠️ LE PIÈGE D'ORDRE. `BulletManager` consomme une balle sur la PREMIÈRE cible qui
## la réclame, dans l'ordre d'enregistrement. Les appendices doivent passer avant la
## cible de corps — sinon un tir ajusté sur un bras serait absorbé par la carapace, et
## pendant l'iris ouvert il soignerait le noyau à sa place.
##
## Sans coque, les trois appendices sont exactement au centre du boss, donc superposés
## à la cible de corps : la configuration la plus défavorable, et c'est voulu.
func test_a_bullet_reaches_a_limb_before_the_body() -> void:
	var rig := _rig()
	var combat: HarvesterCombat = rig[1]
	var bm: BulletManager = rig[2]
	var boss: BossController = rig[0]
	combat.tick(1.0 / 60.0)
	var before := boss.health_ratio()
	bm.spawn_bullet(BulletManager.Team.PLAYER, boss.plane_position, Vector2(0.0, 1.0),
		0.1, 30.0, 5.0)
	bm.step(1.0 / 60.0)
	var damaged := 0
	for limb in combat.limbs():
		if limb.health < limb.max_health or not limb.is_up():
			damaged += 1
	assert_eq(damaged, 1, "exactly one limb absorbed the shot")
	assert_almost_eq(boss.health_ratio(), before, 0.0001, "the body took nothing")
	_free(rig)

func test_the_core_takes_no_damage_while_the_iris_is_closed() -> void:
	var rig := _rig()
	var combat: HarvesterCombat = rig[1]
	var boss: BossController = rig[0]
	_deflections = 0
	boss.deflected.connect(_on_deflected)
	# Les appendices d'abord hors circuit, pour que la balle atteigne bien le corps.
	for limb in combat.limbs():
		limb.target.enabled = false
	var before := boss.health_ratio()
	boss._take_hit(50.0)
	assert_almost_eq(boss.health_ratio(), before, 0.0001, "a closed carapace takes nothing")
	assert_eq(_deflections, 1, "but it reports a deflection — silence would read as a bug")
	_free(rig)

func test_the_core_takes_damage_once_the_iris_is_open() -> void:
	var rig := _rig()
	var combat: HarvesterCombat = rig[1]
	var boss: BossController = rig[0]
	_kill_all_limbs(combat)
	combat.tick(1.0 / 60.0)
	var before := boss.health_ratio()
	boss._take_hit(50.0)
	assert_true(boss.health_ratio() < before, "an open iris exposes the core")
	_free(rig)

func test_a_destroyed_limb_stops_absorbing_bullets() -> void:
	var rig := _rig()
	var combat: HarvesterCombat = rig[1]
	_kill_limb(combat, HarvesterCombat.KIND_SCYTHE)
	for limb in combat.limbs():
		if limb.kind == HarvesterCombat.KIND_SCYTHE:
			assert_false(limb.target.enabled,
				"a fallen limb is not a ghost hitbox floating in front of the core")
	_free(rig)

# --- La boucle complete -------------------------------------------------------

## Trois cycles tuent le boss — la promesse du combat, bout en bout.
func test_three_windows_bring_the_boss_down() -> void:
	var rig := _rig()
	var combat: HarvesterCombat = rig[1]
	var boss: BossController = rig[0]
	var per_window: float = boss.max_health / 3.0
	for cycle in 3:
		_kill_all_limbs(combat)
		combat.tick(1.0 / 60.0)
		assert_true(combat.is_iris_open(), "cycle %d opened its window" % (cycle + 1))
		boss._take_hit(per_window)
		if cycle < 2:
			# On laisse tout repousser avant le cycle suivant, comme en jeu.
			_advance(combat, combat.tuning.limb_rebuild_time + 0.5)
			assert_eq(combat.limbs_up(), 3, "everything is back up for cycle %d" % (cycle + 2))
			assert_false(combat.is_iris_open(), "and the iris closed again")
	assert_almost_eq(boss.health_ratio(), 0.0, 0.001, "three windows are enough")
	_free(rig)

# --- Reglages -----------------------------------------------------------------

func test_the_shipped_tuning_is_valid() -> void:
	var tuning := load(TUNING_PATH) as HarvesterTuning
	assert_true(tuning != null, "the tuning resource loads")
	var errors := tuning.validate()
	assert_true(errors.is_empty(), "tuning is valid (got: %s)" % ", ".join(errors))

## Le réarme EST la règle du duel : un estoc sans télégraphe est imparable.
func test_validate_refuses_an_untelegraphed_lunge() -> void:
	var tuning := (load(TUNING_PATH) as HarvesterTuning).duplicate() as HarvesterTuning
	tuning.scythe_windup_time = 0.0
	assert_true(not tuning.validate().is_empty(), "a zero wind-up is rejected")

## Un redéploiement qui déborde du délai de repousse déclarerait l'appendice vivant
## avant la fin de sa sortie, et l'iris se refermerait sur un bras encore rentré.
func test_validate_refuses_an_animation_longer_than_the_rebuild() -> void:
	var tuning := (load(TUNING_PATH) as HarvesterTuning).duplicate() as HarvesterTuning
	tuning.limb_deploy_time = tuning.limb_rebuild_time
	tuning.limb_retract_time = 1.0
	assert_true(not tuning.validate().is_empty(), "retract + deploy must fit inside the rebuild")

# --- L'estoc : le corps se fend --------------------------------------------------

## LE DÉFAUT QUE CE TEST GARDE — la première version de la faux comparait la position
## du joueur à un point ABSTRAIT verrouillé une seconde plus tôt, pendant que le corps
## du boss restait en haut de l'écran. L'attaque « fonctionnait » au sens où elle
## infligeait parfois des dégâts, et ne se voyait jamais : rien ne reliait le geste au
## résultat. Ce qu'on vérifie ici, c'est donc que le CORPS bouge.
##
## Aucune capture n'irait là-bas : il faut atteindre le mini-boss, survivre au réarme,
## et se trouver au bon endroit à l'image près.
func _advance_to_lunge(combat: HarvesterCombat) -> void:
	var step := 1.0 / 60.0
	var guard := 0.0
	while not combat.is_lunging() and guard < 20.0:
		combat.tick(step)
		guard += step
	assert_true(combat.is_lunging(), "the scythe reaches its lunge")

func test_the_scythe_drives_the_body_toward_the_player() -> void:
	var rig := _rig()
	var boss: BossController = rig[0]
	var combat: HarvesterCombat = rig[1]
	_advance_to_lunge(combat)
	assert_true(boss.is_driven(), "the module has taken the wheel")
	var before := boss.plane_position
	# Le contrôleur ne bouge que dans SON pas de simulation, pas dans celui du module.
	boss._physics_process(0.2)
	assert_true(boss.plane_position.y < before.y,
		"the body dives toward the player (%.2f -> %.2f)" % [before.y, boss.plane_position.y])
	_free(rig)

## Sans cette remise, le boss resterait accroché à sa destination pour toujours : un
## boss immobile, collé au bord bas, qui ne remonte jamais.
func test_the_body_is_handed_back_after_the_strike() -> void:
	var rig := _rig()
	var boss: BossController = rig[0]
	var combat: HarvesterCombat = rig[1]
	_advance_to_lunge(combat)
	_advance(combat, combat.tuning.scythe_strike_time + 0.1)
	assert_false(boss.is_driven(), "the trajectory has the wheel back")
	_free(rig)

## Un appendice abattu EN PLEIN ESTOC ne doit pas emporter le déplacement du boss avec
## lui : c'est l'ordre exact où le joueur détruit la faux pendant qu'elle charge.
func test_killing_the_scythe_mid_lunge_hands_the_body_back() -> void:
	var rig := _rig()
	var boss: BossController = rig[0]
	var combat: HarvesterCombat = rig[1]
	_advance_to_lunge(combat)
	_kill_limb(combat, HarvesterCombat.KIND_SCYTHE)
	combat.tick(1.0 / 60.0)
	assert_false(boss.is_driven(), "a severed arm releases the body")
	_free(rig)

## La destination est bornée au plan de jeu : un verrou posé sur un joueur collé au
## bord enverrait sinon le boss hors champ, sa zone de touche avec lui.
func test_a_lunge_never_leaves_the_playfield() -> void:
	var rig := _rig()
	var boss: BossController = rig[0]
	boss.drive_toward(Vector2(999.0, -999.0), 100.0)
	for i in 120:
		boss._physics_process(1.0 / 60.0)
	assert_true(GameplayPlane.is_inside(boss.plane_position, 0.1),
		"the boss stays on the plane (got %s)" % boss.plane_position)
	_free(rig)

# --- Fenêtre de tir : la règle qui rend le boss tuable ---------------------------

## ⚠️ LE RÉGLAGE QUI REND LE COMBAT INJOUABLE SANS UN MOT. Chaque valeur prise
## séparément est sensée : des appendices coriaces, une repousse rapide. Ensemble, elles
## font que le premier bras revient avant que le troisième ne tombe — l'iris ne s'ouvre
## jamais, et le boss est invincible.
func test_validate_refuses_a_tuning_with_no_window() -> void:
	var tuning := (load(TUNING_PATH) as HarvesterTuning).duplicate() as HarvesterTuning
	tuning.limb_health = tuning.reference_dps * tuning.limb_rebuild_time
	assert_true(not tuning.validate().is_empty(),
		"a limb nobody can chain down in time is rejected")

func test_the_shipped_tuning_leaves_a_usable_window() -> void:
	var tuning := load(TUNING_PATH) as HarvesterTuning
	var kill_time := tuning.limb_health / tuning.reference_dps
	var window := tuning.limb_rebuild_time - 2.0 * kill_time
	assert_true(window >= HarvesterTuning.MIN_WINDOW,
		"shipped tuning: %.1f s kill, %.1f s window" % [kill_time, window])
