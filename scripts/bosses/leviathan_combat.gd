class_name LeviathanCombat
extends Node
## Le combat du Pale Leviathan : quatre phases, quatre verbes
## (`docs/design/BOSS_PALE_LEVIATHAN.md`, acté par `ADR-0018`).
##
## COMPOSITION — `BossController` garde tout le générique (entrée, déplacement, roulis,
## PV, signaux HUD, mort, prise de main sur le déplacement) et sert toujours le Choir
## Harvester. Ce module ne lui prend que deux choses, exactement comme `HarvesterCombat` :
## l'armement (`external_attacks`) et la vulnérabilité du corps.
##
## LE PILIER — le Harvester est un **verrou** (trois clés ouvrent une fenêtre, en boucle,
## tout repousse). Le Leviathan est un **démontage** : chaque phase lui arrache une
## partie du corps, **rien ne repousse**, et la pièce arrachée devient la mécanique de
## la phase suivante.
##
## ⚠️ LES PHASES N'AVANCENT PAS AUX SEUILS DE POINTS DE VIE. C'est ce que faisait le
## `BossController` générique, et c'est précisément ce qui rendait le boss final
## illisible : la « phase » changeait sans que rien à l'écran ne l'explique. Ici chaque
## transition a une **condition matérielle** — les quatre plaques à terre, les trois
## nœuds abattus, les quatre épines détruites, le cœur mort. Le joueur voit ce qu'il a
## cassé, et c'est ce qui fait avancer le combat.

## Le contrat de noms de la coque (BRIEF-0040, vérifié dans le `.glb`).
const PLATE_COUNT := 4
const NODE_COUNT := 3
const SPIKE_COUNT := 4

enum Phase { ARMOR_CHOIR, GRAVITIC_MAW, BOARDING_SWARM, INTO_THE_MAW, DEFEATED }

## Le HUD et le niveau écoutent ; le module ne connaît ni l'un ni l'autre.
signal phase_entered(phase: int)
## Progression globale : dégâts cumulés sur TOUTES les structures. ⚠️ Une jauge qui ne
## montrerait que le corps resterait figée pendant une phase entière et dirait au
## joueur qu'il ne fait rien.
signal structure_changed(ratio: float)
signal piece_gauge_changed(index: int, ratio: float, alive: bool)
signal piece_destroyed(phase: int, index: int, world_position: Vector3)
## Force d'aspiration à appliquer au chasseur, en unités par seconde. Le niveau la
## relaie ; le module ne touche jamais au joueur directement.
signal pull_changed(speed_max: float, radius: float, centre: Vector2)

@export var tuning: LeviathanTuning
@export var projectile: ProjectileData

var _boss: BossController
var _hull: Node3D
var _bullet_manager: BulletManager
var _player: PlayerFighterController

var _phase: Phase = Phase.ARMOR_CHOIR
var _phase_age: float = 0.0
var _age: float = 0.0
## Répit entre deux phases : la coque se réorganise et le boss ne tire pas. C'est là
## que le joueur respire, voit ce qu'il a cassé, et lit la nouvelle règle.
var _interlude: float = 0.0

var _plates: Array[LeviathanPlate] = []
var _nodes: Array[BulletTarget] = []
var _node_health: PackedFloat32Array = PackedFloat32Array()
var _spikes: Array[LeviathanSpike] = []
var _core_target: BulletTarget
var _core_health: float = 0.0
var _heart_target: BulletTarget
var _heart_health: float = 0.0
var _missiles: Array[TargetableProjectile] = []

## Rotation courante de la coquille, en radians. C'est elle qui fabrique la fenêtre de
## tir de la phase 1.
var _shell_rotation: float = 0.0
var _fan_timer: float = 0.0
var _missile_timer: float = 0.0
var _pulse_timer: float = 0.0
## Dégâts cumulés sur toutes les structures — le numérateur de la jauge.
var _damage_taken: float = 0.0
## Compte à rebours de la gueule en phase 4.
var _maw_open: float = 0.0
var _maw_closed_for: float = 0.0

# --- Montage ------------------------------------------------------------------

func _ready() -> void:
	_boss = get_parent() as BossController
	if _boss == null:
		push_error("[Leviathan] le module doit etre enfant d'un BossController")
		return
	if tuning == null:
		# ⚠️ On REND l'armement au boss générique. Sans cela le module ne monte pas,
		# `external_attacks` reste à `true` (déclaré dans la scène), le boss ne tire
		# donc rien, et `vulnerable` garde son défaut `true` : le boss final devient
		# un sac à PV inoffensif. Dégrader vers l'ancien comportement vaut mieux que
		# dégrader vers l'absence de combat. Même raisonnement que le Harvester.
		push_error("[Leviathan] aucun LeviathanTuning : retour aux motifs generiques")
		_boss.external_attacks = false
		set_physics_process(false)
		return
	var errors := tuning.validate()
	if not errors.is_empty():
		# Le réglage est refusé AVANT le combat, pas découvert au milieu : les
		# invariants de `LeviathanTuning` décrivent des pannes qui ne se voient pas.
		push_error("[Leviathan] tuning invalide : %s" % ", ".join(errors))
	_boss.external_attacks = true
	_boss.began.connect(_on_boss_began)
	_boss.defeated.connect(_on_boss_defeated)
	set_physics_process(false)

func _on_boss_began(bullet_manager: BulletManager, player: PlayerFighterController) -> void:
	setup(_boss.hull(), bullet_manager, player)
	set_physics_process(true)

func _on_boss_defeated(_world_position: Vector3) -> void:
	set_physics_process(false)
	release()

## Montage. `hull` peut être nul : les tests font tourner toute la boucle sans coque,
## et une plaque sans nœud à poser reste une plaque qui vit, encaisse et tombe.
func setup(hull: Node3D, bullet_manager: BulletManager, player: PlayerFighterController) -> void:
	_hull = hull
	_bullet_manager = bullet_manager
	_player = player
	release()
	_build_plates()
	_build_nodes()
	_build_spikes()
	_build_core_and_heart()
	_register_targets()
	_enter_phase(Phase.ARMOR_CHOIR)
	# Hook de vérification : atteindre la phase 3 demande deux minutes de jeu, donc
	# personne ne la REGARDE jamais (ADR-0006). `++ --leviathan-phase 3` y saute.
	_apply_phase_hook()

func _build_plates() -> void:
	_plates.clear()
	for i in PLATE_COUNT:
		# Réparties régulièrement : c'est cet écart qui garantit qu'il y a presque
		# toujours une cible dans l'arc, donc aucun temps mort dans la phase.
		var plate := LeviathanPlate.make(i, TAU * i / PLATE_COUNT, tuning.plate_health,
			tuning.plate_hitbox_radius, Callable(self, "_on_plate_hit").bind(i))
		if _hull != null:
			plate.node = _hull.find_child("Plate_%02d" % (i + 1), true, false) as Node3D
			if plate.node == null:
				push_error("[Leviathan] coque sans 'Plate_%02d' (contrat BRIEF-0040)" % (i + 1))
			else:
				plate.rest_basis = plate.node.transform.basis
		_plates.append(plate)

func _build_nodes() -> void:
	_nodes.clear()
	_node_health.resize(NODE_COUNT)
	for i in NODE_COUNT:
		_node_health[i] = tuning.node_health
		var target := BulletTarget.make(BulletManager.Team.ENEMY, tuning.node_hitbox_radius,
			Callable(self, "_on_node_hit").bind(i))
		target.enabled = false   # la lèvre est fermée tant que la phase 1 dure
		_nodes.append(target)

func _build_spikes() -> void:
	_spikes.clear()
	for i in SPIKE_COUNT:
		var spike := LeviathanSpike.make(i, LeviathanSpike.role_for(i), TAU * i / SPIKE_COUNT,
			tuning.spike_health, tuning.spike_hitbox_radius, Callable(self, "_on_spike_hit").bind(i))
		spike.target.enabled = false   # attachée : le corps la protège
		if _hull != null:
			spike.node = _hull.find_child("Spike_%02d" % (i + 1), true, false) as Node3D
			if spike.node == null:
				push_error("[Leviathan] coque sans 'Spike_%02d' (contrat BRIEF-0040)" % (i + 1))
			else:
				spike.rest_transform = spike.node.transform
		_spikes.append(spike)

func _build_core_and_heart() -> void:
	_core_health = tuning.core_health
	_heart_health = tuning.heart_health
	_core_target = BulletTarget.make(BulletManager.Team.ENEMY, tuning.core_hitbox_radius,
		Callable(self, "_on_core_hit"))
	_core_target.enabled = false
	_heart_target = BulletTarget.make(BulletManager.Team.ENEMY, tuning.heart_hitbox_radius,
		Callable(self, "_on_heart_hit"))
	_heart_target.enabled = false

## ⚠️ ORDRE D'ENREGISTREMENT CRITIQUE. `BulletManager._resolve_hits` parcourt les cibles
## dans l'ordre d'enregistrement et CONSOMME la balle sur la première qui la réclame.
## Les sous-cibles doivent donc passer AVANT la cible de corps du boss : dans l'autre
## sens, un tir ajusté sur une plaque serait absorbé par le corps.
## `BossController.begin()` émet `began` avant d'enregistrer la sienne, exprès.
func _register_targets() -> void:
	if _bullet_manager == null:
		return
	for plate in _plates:
		_bullet_manager.register_target(plate.target)
	for node in _nodes:
		_bullet_manager.register_target(node)
	for spike in _spikes:
		_bullet_manager.register_target(spike.target)
	_bullet_manager.register_target(_core_target)
	_bullet_manager.register_target(_heart_target)

func _apply_phase_hook() -> void:
	for arg in OS.get_cmdline_user_args():
		if not arg.begins_with("--leviathan-phase"):
			continue
		var wanted := arg.get_slice("=", 1).to_int() if "=" in arg else 0
		for _step in clampi(wanted - 1, 0, 3):
			_force_next_phase()
		return

## Abat tout ce que la phase courante demande, et bascule. Réservé au hook de debug :
## le combat, lui, avance sur des conditions matérielles.
func _force_next_phase() -> void:
	match _phase:
		Phase.ARMOR_CHOIR:
			for plate in _plates:
				plate.apply_damage(plate.max_health)
		Phase.GRAVITIC_MAW:
			for i in _nodes.size():
				_on_node_hit(tuning.node_health, i)
		Phase.BOARDING_SWARM:
			for spike in _spikes:
				spike.detach(_origin())
				spike.apply_damage(spike.max_health)
		_:
			return
	_advance_phase()

# --- Boucle -------------------------------------------------------------------

func _physics_process(delta: float) -> void:
	tick(delta)

## Toute la logique du combat. Publique et sans dépendance à l'arbre : les tests la
## pilotent directement, ce qui rend vérifiable un enchaînement qu'aucune capture ne
## pourrait couvrir — il faut plus de trois minutes de jeu pour voir les quatre phases.
func tick(delta: float) -> void:
	if tuning == null:
		return
	_age += delta
	_phase_age += delta
	var origin := _origin()
	_tick_missiles(delta)
	if _interlude > 0.0:
		# Le répit : la coque se réorganise, le boss ne tire pas.
		_interlude = maxf(_interlude - delta, 0.0)
		return
	match _phase:
		Phase.ARMOR_CHOIR: _run_armor_choir(delta, origin)
		Phase.GRAVITIC_MAW: _run_gravitic_maw(delta, origin)
		Phase.BOARDING_SWARM: _run_boarding_swarm(delta, origin)
		Phase.INTO_THE_MAW: _run_into_the_maw(delta, origin)
		Phase.DEFEATED: return
	_sync_targets(origin)

## Position du boss dans le plan. Le plan est la vérité des collisions : il ne dépend
## ni de l'arbre ni du roulis, et reste lisible en test où rien n'est monté.
func _origin() -> Vector2:
	return _boss.plane_position if _boss != null else Vector2.ZERO

func _sync_targets(origin: Vector2) -> void:
	for plate in _plates:
		# La plaque tourne avec la coquille : sa zone de touche suit son angle réel.
		var a := plate.angle_at(_shell_rotation)
		plate.target.position = origin + Vector2(cos(a), sin(a)) * 2.6
	for i in _nodes.size():
		var a := TAU * i / float(maxi(_nodes.size(), 1)) + _age * 0.2
		_nodes[i].position = origin + Vector2(cos(a), sin(a)) * 1.8
	if _core_target != null:
		_core_target.position = origin
	if _heart_target != null:
		_heart_target.position = origin
	for spike in _spikes:
		if spike.is_free() or spike.state == LeviathanSpike.State.DETACHING:
			spike.target.position = spike.plane_position

# --- Phase 1 — ARMOR CHOIR (BRISER) -------------------------------------------

func _run_armor_choir(delta: float, origin: Vector2) -> void:
	# La coquille tourne : c'est elle qui fabrique la fenêtre de tir.
	if tuning.shell_orbit_period > 0.0:
		_shell_rotation = wrapf(_shell_rotation + TAU * delta / tuning.shell_orbit_period, -PI, PI)
	for plate in _plates:
		plate.tick(delta, tuning.shell_break_time)
		# Une plaque n'encaisse que dans l'arc face au joueur. Hors de l'arc le corps
		# la masque, et le tir part en `deflected` plutôt que dans le vide.
		plate.target.enabled = plate.is_exposed(_shell_rotation, tuning.plate_arc_deg)
	_fan_timer -= delta
	if _fan_timer <= 0.0:
		_fan_timer = tuning.fan_interval
		_fire_fans(origin)
	_missile_timer -= delta
	if _missile_timer <= 0.0:
		_missile_timer = tuning.missile_salvo_interval
		_launch_missiles(origin)
	if _plates_up() == 0:
		_advance_phase()

## Un éventail par plaque **encore debout** : moins de plaques = moins de rideau. Le
## retour de la destruction est immédiat et physique, sans qu'aucun texte ne l'explique.
func _fire_fans(origin: Vector2) -> void:
	if _bullet_manager == null or projectile == null:
		return
	for plate in _plates:
		if not plate.is_up():
			continue
		var a := plate.angle_at(_shell_rotation)
		var muzzle := origin + Vector2(cos(a), sin(a)) * 2.6
		for i in tuning.fan_bullets:
			var t := float(i) / float(maxi(tuning.fan_bullets - 1, 1)) - 0.5
			var spread := deg_to_rad(tuning.fan_spread_deg) * t
			_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, muzzle,
				Vector2(0.0, -1.0).rotated(spread), projectile)

func _launch_missiles(origin: Vector2) -> void:
	var aim := _player.plane_position if _player != null else origin + Vector2(0.0, -6.0)
	for i in tuning.missile_count:
		var spread := deg_to_rad(20.0 * (i - (tuning.missile_count - 1) * 0.5))
		var direction := (aim - origin).normalized().rotated(spread)
		var missile := TargetableProjectile.make(origin, direction * tuning.missile_speed,
			tuning.missile_health, tuning.missile_hitbox_radius, tuning.missile_turn_rate,
			tuning.missile_damage, Callable(self, "_on_missile_hit").bind(_missiles.size()))
		_missiles.append(missile)
		if _bullet_manager != null:
			_bullet_manager.register_target(missile.target)

func _tick_missiles(delta: float) -> void:
	var chase := _player.plane_position if _player != null else Vector2.ZERO
	for missile in _missiles:
		if not missile.alive:
			continue
		missile.tick(delta, chase)
		if _player != null and missile.reaches(_player.plane_position, 0.25):
			_player.take_contact_damage(missile.damage)
			missile.consume()
	# ⚠️ On ne compacte le tableau que lorsqu'il grossit : `filter()` alloue, et cette
	# boucle tourne à chaque image pendant soixante secondes.
	if _missiles.size() > 24:
		var kept: Array[TargetableProjectile] = []
		for missile in _missiles:
			if missile.alive:
				kept.append(missile)
			elif _bullet_manager != null:
				_bullet_manager.unregister_target(missile.target)
		_missiles = kept

# --- Phase 2 — GRAVITIC MAW (RÉSISTER) ----------------------------------------

func _run_gravitic_maw(delta: float, origin: Vector2) -> void:
	_pulse_timer -= delta
	if _pulse_timer <= 0.0:
		_pulse_timer = tuning.maw_pulse_interval
		_fire_pulse(origin)
	_publish_pull(origin)
	if _nodes_up() == 0:
		_advance_phase()

func _fire_pulse(origin: Vector2) -> void:
	if _bullet_manager == null or projectile == null:
		return
	for i in tuning.maw_pulse_bullets:
		var a := TAU * i / float(maxi(tuning.maw_pulse_bullets, 1))
		_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, origin,
			Vector2(cos(a), sin(a)), projectile)

## Chaque nœud abattu retire un tiers de l'aspiration. Le soulagement est fractionnaire
## et se **sent dans les doigts** : chaque victoire partielle paie.
func _publish_pull(origin: Vector2) -> void:
	var down := NODE_COUNT - _nodes_up()
	var speed := GravityWell.speed_max_after(tuning.pull_speed_max, down, NODE_COUNT)
	pull_changed.emit(speed, tuning.pull_radius, origin)

# --- Phase 3 — BOARDING SWARM (PRIORISER) -------------------------------------

func _run_boarding_swarm(delta: float, origin: Vector2) -> void:
	var player := _player.plane_position if _player != null else origin + Vector2(0.0, -6.0)
	for spike in _spikes:
		if not spike.is_alive():
			continue
		spike.tick(delta, 0.6)
		if spike.state == LeviathanSpike.State.ATTACHED:
			continue
		var want := spike.desired_position(origin, player, tuning.blocker_offset,
			tuning.escort_orbit_radius, _age)
		var speed := tuning.charger_speed if spike.charging else 8.0
		spike.plane_position = spike.plane_position.move_toward(want, speed * delta)
		spike.plane_position = GameplayPlane.clamp_to_bounds(spike.plane_position)
	if _spikes_alive() == 0:
		_advance_phase()

# --- Phase 4 — INTO THE MAW (OSER) --------------------------------------------

func _run_into_the_maw(delta: float, origin: Vector2) -> void:
	if _maw_closed_for > 0.0:
		_maw_closed_for = maxf(_maw_closed_for - delta, 0.0)
		if _maw_closed_for <= 0.0:
			_maw_open = tuning.maw_open_time
			_heart_target.enabled = true
		pull_changed.emit(0.0, tuning.pull_radius, origin)
		return
	_maw_open = maxf(_maw_open - delta, 0.0)
	# ⚠️ L'aspiration DÉPASSE ici la vitesse du joueur, et c'est le sujet de la phase :
	# on ne résiste plus, on entre. `LeviathanTuning.validate()` vérifie ce sens-là.
	pull_changed.emit(tuning.pull_speed_max_final, tuning.pull_radius, origin)
	if _maw_open <= 0.0:
		# Le cœur a tenu : la gueule se referme, le boss recharge, on recommence.
		_heart_target.enabled = false
		_maw_closed_for = tuning.maw_reopen_delay

## Part restante du compte à rebours, pour le HUD.
func maw_open_ratio() -> float:
	if tuning == null or tuning.maw_open_time <= 0.0:
		return 0.0
	return _maw_open / tuning.maw_open_time

# --- Transitions --------------------------------------------------------------

func _advance_phase() -> void:
	match _phase:
		Phase.ARMOR_CHOIR: _enter_phase(Phase.GRAVITIC_MAW)
		Phase.GRAVITIC_MAW: _enter_phase(Phase.BOARDING_SWARM)
		Phase.BOARDING_SWARM: _enter_phase(Phase.INTO_THE_MAW)
		Phase.INTO_THE_MAW: _enter_phase(Phase.DEFEATED)

func _enter_phase(next: Phase) -> void:
	_phase = next
	_phase_age = 0.0
	_interlude = 0.0 if next == Phase.ARMOR_CHOIR else 1.5
	match next:
		Phase.GRAVITIC_MAW:
			# La coquille a éclaté : la lèvre et ses nœuds deviennent la cible.
			for node in _nodes:
				node.enabled = true
		Phase.BOARDING_SWARM:
			# Les épines s'arrachent, et le noyau devient enfin touchable.
			for spike in _spikes:
				spike.detach(_origin())
			_core_target.enabled = true
			if _boss != null:
				_boss.vulnerable = true
		Phase.INTO_THE_MAW:
			_maw_open = tuning.maw_open_time if tuning != null else 0.0
			_heart_target.enabled = true
			_core_target.enabled = false
		Phase.DEFEATED:
			release()
			if _boss != null:
				_boss.vulnerable = true
	phase_entered.emit(next)
	_publish_structure()

# --- Dégâts -------------------------------------------------------------------

func _on_plate_hit(damage: float, index: int) -> void:
	var plate := _plates[index]
	if not plate.is_up():
		return
	_account(damage)
	if plate.apply_damage(damage):
		piece_destroyed.emit(Phase.ARMOR_CHOIR, index, _piece_world(plate.target.position))
	piece_gauge_changed.emit(index, plate.health_ratio(), plate.is_up())

func _on_node_hit(damage: float, index: int) -> void:
	if _node_health[index] <= 0.0:
		return
	_account(damage)
	_node_health[index] = maxf(_node_health[index] - damage, 0.0)
	if _node_health[index] <= 0.0:
		_nodes[index].enabled = false
		piece_destroyed.emit(Phase.GRAVITIC_MAW, index, _piece_world(_nodes[index].position))
	piece_gauge_changed.emit(index, _node_health[index] / tuning.node_health, _node_health[index] > 0.0)

func _on_spike_hit(damage: float, index: int) -> void:
	var spike := _spikes[index]
	if not spike.is_alive():
		return
	_account(damage)
	if spike.apply_damage(damage):
		piece_destroyed.emit(Phase.BOARDING_SWARM, index, _piece_world(spike.plane_position))
	piece_gauge_changed.emit(index, spike.health_ratio(), spike.is_alive())

func _on_core_hit(damage: float) -> void:
	if _core_health <= 0.0:
		return
	_account(damage)
	_core_health = maxf(_core_health - damage, 0.0)
	if _core_health <= 0.0:
		_core_target.enabled = false

func _on_heart_hit(damage: float) -> void:
	if _heart_health <= 0.0:
		return
	_account(damage)
	_heart_health = maxf(_heart_health - damage, 0.0)
	if _heart_health <= 0.0:
		_heart_target.enabled = false
		_advance_phase()

func _on_missile_hit(damage: float, index: int) -> void:
	if index < 0 or index >= _missiles.size():
		return
	_missiles[index].apply_damage(damage)

## Comptabilise les dégâts pour la jauge globale. ⚠️ Tout y passe — plaques, nœuds,
## épines, noyau, cœur — sinon la jauge se fige pendant une phase entière.
func _account(damage: float) -> void:
	_damage_taken += damage
	_publish_structure()

func _publish_structure() -> void:
	if tuning == null:
		return
	var total := tuning.total_structure()
	if total <= 0.0:
		return
	structure_changed.emit(clampf(1.0 - _damage_taken / total, 0.0, 1.0))

func _piece_world(plane: Vector2) -> Vector3:
	return GameplayPlane.to_world(plane)

# --- Lectures -----------------------------------------------------------------

func phase() -> int:
	return _phase

func shell_rotation() -> float:
	return _shell_rotation

func plates() -> Array[LeviathanPlate]:
	return _plates

func spikes() -> Array[LeviathanSpike]:
	return _spikes

func _plates_up() -> int:
	var up := 0
	for plate in _plates:
		if plate.is_up():
			up += 1
	return up

func _nodes_up() -> int:
	var up := 0
	for value in _node_health:
		if value > 0.0:
			up += 1
	return up

func _spikes_alive() -> int:
	var alive := 0
	for spike in _spikes:
		if spike.is_alive():
			alive += 1
	return alive

func structure_ratio() -> float:
	if tuning == null:
		return 1.0
	var total := tuning.total_structure()
	return clampf(1.0 - _damage_taken / total, 0.0, 1.0) if total > 0.0 else 1.0

## Publie l'état de toutes les jauges. Le niveau l'appelle après `begin()`, quand le
## HUD est prêt : interroger avant afficherait des pastilles éteintes sur un boss intact.
func publish_gauges() -> void:
	for plate in _plates:
		piece_gauge_changed.emit(plate.index, plate.health_ratio(), plate.is_up())
	_publish_structure()

## Retire TOUTES les cibles du gestionnaire. Sans cela, un boss vaincu ou un remontage
## laisse des cibles actives, callback vivant, position figée : un mur invisible qui
## mange les balles du joueur.
func release() -> void:
	if _bullet_manager == null:
		return
	for plate in _plates:
		plate.target.enabled = false
		_bullet_manager.unregister_target(plate.target)
	for node in _nodes:
		node.enabled = false
		_bullet_manager.unregister_target(node)
	for spike in _spikes:
		spike.target.enabled = false
		_bullet_manager.unregister_target(spike.target)
	for missile in _missiles:
		missile.target.enabled = false
		_bullet_manager.unregister_target(missile.target)
	_missiles.clear()
	for target in [_core_target, _heart_target]:
		if target != null:
			target.enabled = false
			_bullet_manager.unregister_target(target)
