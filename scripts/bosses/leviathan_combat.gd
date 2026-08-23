class_name LeviathanCombat
extends Node
## Le combat du Pale Leviathan : **deux phases, deux gestes**
## (`docs/design/BOSS_PALE_LEVIATHAN.md`, refondu par `ADR-0020`).
##
##     PHASE 1 — BRISER L'ARMURE : quatre plaques, une seule vulnérable à la fois.
##     PHASE 2 — LE CŒUR : la coquille s'écarte, le cœur est à nu jusqu'à la fin.
##
## COMPOSITION — `BossController` garde tout le générique (entrée, déplacement, roulis,
## PV, signaux HUD, mort, prise de main sur le déplacement) et sert toujours le Choir
## Harvester. Ce module ne lui prend que deux choses, exactement comme `HarvesterCombat` :
## l'armement (`external_attacks`) et la vulnérabilité du corps.
##
## ⚠️ CE QUE LA REFONTE A RETIRÉ, ET POURQUOI (ADR-0020). Le combat comptait quatre
## phases : armure, nœuds gravitiques, essaim d'abordage, plongée dans la gueule. Le
## playtest a rendu un verdict sans appel — « mal équilibré, on ne voit pas les phases,
## je n'aime pas le combat » — et la partie s'est arrêtée **pendant la phase 1**, sans
## que le joueur voie jamais les trois autres. Trois défauts, tous vérifiés dans ce
## fichier avant d'y toucher :
##
##   1. **La jauge mentait.** Elle divisait par les PV des quatre phases : briser toute
##      l'armure ne valait que 30 % de barre. Le joueur travaillait vingt secondes et
##      lisait « 70 % ». Elle montre désormais **la phase en cours**, et se remplit à
##      nouveau à la bascule — l'idiome de shmup que tout le monde sait lire.
##   2. **La fenêtre de tir n'existait pas.** Quatre plaques espacées de 90°, arc de
##      100° : il y avait toujours une plaque exposée, souvent deux. « Lire la rotation
##      pour choisir son moment » ne contraignait donc jamais rien.
##   3. **Les dégâts s'étalaient.** Comme toutes les plaques exposées encaissaient, elles
##      descendaient ensemble et tombaient toutes à la fin. Une seule est désormais
##      vulnérable — celle qui brille : le feu se concentre, une plaque cède toutes les
##      ~5,5 s, et le démontage devient visible.
##
## Nœuds, épines et noyau intermédiaire ont disparu **comme cibles**. Ils restent à
## l'écran et se détachent quand une plaque cède : le boss se démonte à vue sans qu'aucune
## règle nouvelle n'ait à s'apprendre.
##
## ⚠️ LES PHASES N'AVANCENT PAS AUX SEUILS DE POINTS DE VIE. C'est ce que faisait le
## `BossController` générique, et c'est ce qui rendait le boss illisible : la « phase »
## changeait sans que rien à l'écran ne l'explique. Ici chaque transition a une
## **condition matérielle** — les quatre plaques à terre, puis le cœur mort.

## Le contrat de noms de la coque (BRIEF-0040, vérifié dans le `.glb`).
const PLATE_COUNT := 4
## Épines et nœuds : décor qui se détache, plus aucune cible.
const SPIKE_COUNT := 4
const NODE_COUNT := 3
## Durée de chute d'une pièce détachée, en secondes.
const DEBRIS_FALL_TIME := 1.6

enum Phase { ARMOR, HEART, DEFEATED }

## Le HUD et le niveau écoutent ; le module ne connaît ni l'un ni l'autre.
signal phase_entered(phase: int)
## Santé restante **de la phase en cours**, entre 1 et 0. ⚠️ Ce n'était pas le cas avant :
## le signal portait les dégâts cumulés sur les quatre phases, et c'est précisément ce qui
## faisait dire au joueur « je ne fais rien » alors qu'il venait de briser toute l'armure.
signal structure_changed(ratio: float)
signal piece_gauge_changed(index: int, ratio: float, alive: bool)
## Sous-cible que le joueur doit viser MAINTENANT (`-1` = aucune). En phase 1 une seule
## plaque encaisse à la fois, celle qui est surlignée. Émis SEULEMENT au changement.
signal piece_active_changed(index: int)
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

var _phase: Phase = Phase.ARMOR
var _phase_age: float = 0.0
var _age: float = 0.0
## Répit entre les deux phases : la coque s'ouvre et le boss ne tire pas. C'est là que le
## joueur respire, voit ce qu'il a cassé, et lit la nouvelle règle.
var _interlude: float = 0.0

var _plates: Array[LeviathanPlate] = []
var _heart_target: BulletTarget
var _heart_health: float = 0.0
var _missiles: Array[TargetableProjectile] = []

## Rotation courante de la coquille, en radians. C'est elle qui donne le tempo de la phase 1.
var _shell_rotation: float = 0.0
## Plaque vulnérable (`-1` = aucune). Mémorisée pour n'émettre `piece_active_changed` qu'au
## changement : la boucle tourne à chaque image pendant vingt secondes.
var _active_piece: int = -1
## La coque visible : `Shell_Ring` porte l'orbite (contrat BRIEF-0040).
var _shell_ring: Node3D
var _shell_ring_rest: Transform3D = Transform3D.IDENTITY
## Le cœur (`Heart`), révélé en phase 2.
var _heart_node: Node3D
## Surbrillance additive de la pièce à viser, partagée par tous ses maillages. Créée une
## fois : la moduler par image ne réalloue rien. Posée en `material_overlay` pour ne PAS
## remplacer la texture, seulement ajouter un halo par-dessus.
var _highlight: StandardMaterial3D
## Ouverture de la coquille en phase 2, de 0 (fermée) à 1 (le cœur est à nu). C'est le
## seul « texte » de la transition : le corps s'ouvre, la cible apparaît.
var _shell_open: float = 0.0

## Pièces décoratives qui se détachent quand l'armure cède. Trois tableaux parallèles,
## dimensionnés une fois au montage : aucune allocation pendant le combat.
var _debris: Array[Node3D] = []
var _debris_rest: Array[Transform3D] = []
## Progression de chute, par pièce : `-1` = encore en place, sinon 0 → 1.
var _debris_fall: PackedFloat32Array = PackedFloat32Array()

var _fan_timer: float = 0.0
var _missile_timer: float = 0.0
var _pulse_timer: float = 0.0
## Aspiration intermittente de la phase 2 : `_pull_left > 0` pendant la vague.
var _pull_timer: float = 0.0
var _pull_left: float = 0.0
## Dégâts encaissés **dans la phase en cours** — le numérateur de la jauge du HUD.
var _phase_damage: float = 0.0
## Dégâts encaissés depuis le début du combat — la progression réelle. ⚠️ Les deux sont
## nécessaires et ne disent pas la même chose : la jauge se remplit à nouveau à chaque
## phase, la progression du combat, elle, ne remonte jamais.
var _fight_damage: float = 0.0

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
	_build_heart()
	_bind_shell_visual()
	_collect_debris()
	_register_targets()
	_enter_phase(Phase.ARMOR)
	# Hook de vérification : la phase 2 arrive après vingt secondes de jeu, donc personne
	# ne la REGARDE jamais (ADR-0006). `++ --leviathan-phase=2` y saute.
	_apply_phase_hook()

func _build_plates() -> void:
	_plates.clear()
	for i in PLATE_COUNT:
		# Réparties régulièrement. ⚠️ L'écart entre deux plaques (360/N) doit rester
		# inférieur ou égal à `plate_arc_deg`, sans quoi il existe des instants où aucune
		# plaque n'est atteignable — `LeviathanTuning.validate()` refuse ce réglage.
		var plate := LeviathanPlate.make(i, TAU * i / PLATE_COUNT, tuning.plate_health,
			tuning.plate_hitbox_radius, Callable(self, "_on_plate_hit").bind(i))
		if _hull != null:
			plate.node = _hull.find_child("Plate_%02d" % (i + 1), true, false) as Node3D
			if plate.node == null:
				push_error("[Leviathan] coque sans 'Plate_%02d' (contrat BRIEF-0040)" % (i + 1))
			else:
				plate.rest_basis = plate.node.transform.basis
				_collect_meshes(plate.node, plate.meshes)
		_plates.append(plate)

func _build_heart() -> void:
	_heart_health = tuning.heart_health
	_heart_target = BulletTarget.make(BulletManager.Team.ENEMY, tuning.heart_hitbox_radius,
		Callable(self, "_on_heart_hit"))
	_heart_target.enabled = false   # l'armure le protège tant qu'elle tient

## Résout la coquille tournante, le cœur et le halo. Nuls en test (coque absente) : la
## boucle tourne sans 3D, seule la géométrie des hitbox compte.
func _bind_shell_visual() -> void:
	_shell_ring = null
	_heart_node = null
	if _hull != null:
		_shell_ring = _hull.find_child("Shell_Ring", true, false) as Node3D
		if _shell_ring == null:
			push_error("[Leviathan] coque sans 'Shell_Ring' (contrat BRIEF-0040)")
		else:
			_shell_ring_rest = _shell_ring.transform
		_heart_node = _hull.find_child("Heart", true, false) as Node3D
	if _highlight == null:
		# Additif, non éclairé : un halo qui s'AJOUTE à la texture au lieu de la remplacer.
		# Posé en `material_overlay`, il laisse la pièce lisible et signale « ici, maintenant ».
		_highlight = StandardMaterial3D.new()
		_highlight.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_highlight.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		_highlight.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_highlight.albedo_color = Color(0.90, 0.35, 0.70, 1.0)

## Les pièces qui tombent avec l'armure : épines et nœuds. Elles n'ont plus de vie, plus
## de zone de touche et plus de comportement — elles ne servent qu'à montrer le démontage.
## Un boss qui perd des morceaux se lit sans bannière.
func _collect_debris() -> void:
	_debris.clear()
	_debris_rest.clear()
	_debris_fall.resize(0)
	if _hull == null:
		return
	for i in SPIKE_COUNT:
		_push_debris(_hull.find_child("Spike_%02d" % (i + 1), true, false) as Node3D)
	for i in NODE_COUNT:
		_push_debris(_hull.find_child("Node_%02d" % (i + 1), true, false) as Node3D)

func _push_debris(node: Node3D) -> void:
	if node == null:
		return
	_debris.append(node)
	_debris_rest.append(node.transform)
	_debris_fall.append(-1.0)

## Tous les `MeshInstance3D` sous un nœud, racine comprise. Mirror de `HarvesterLimb`.
static func _collect_meshes(node: Node, into: Array[MeshInstance3D]) -> void:
	var mesh := node as MeshInstance3D
	if mesh != null and mesh.mesh != null:
		into.append(mesh)
	for child in node.get_children():
		_collect_meshes(child, into)

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
	_bullet_manager.register_target(_heart_target)

func _apply_phase_hook() -> void:
	for arg in OS.get_cmdline_user_args():
		if not arg.begins_with("--leviathan-phase"):
			continue
		var wanted := arg.get_slice("=", 1).to_int() if "=" in arg else 0
		for _step in clampi(wanted - 1, 0, 1):
			_force_next_phase()
		return

## Abat tout ce que la phase courante demande, et bascule. Réservé au hook de debug :
## le combat, lui, avance sur des conditions matérielles.
## ⚠️ Passe par `_on_plate_hit`, pas par `plate.apply_damage` : c'est le chemin réel des
## dégâts, celui qui détache les pièces et publie les jauges. Le raccourci laissait le hook
## sauter en phase 2 avec une coque intacte — on vérifiait alors un état que le jeu ne
## produit jamais.
func _force_next_phase() -> void:
	if _phase != Phase.ARMOR:
		return
	for plate in _plates:
		_on_plate_hit(plate.max_health, plate.index)
	_advance_phase()

# --- Boucle -------------------------------------------------------------------

func _physics_process(delta: float) -> void:
	tick(delta)

## Toute la logique du combat. Publique et sans dépendance à l'arbre : les tests la
## pilotent directement, ce qui rend vérifiable un enchaînement qu'aucune capture ne
## pourrait couvrir — il faut une quarantaine de secondes de jeu pour voir les deux phases.
func tick(delta: float) -> void:
	if tuning == null:
		return
	_age += delta
	_phase_age += delta
	var origin := _origin()
	_tick_missiles(delta)
	_tick_debris(delta)
	if _interlude > 0.0:
		# Le répit : la coque s'ouvre, le boss ne tire pas.
		_interlude = maxf(_interlude - delta, 0.0)
		_open_shell(delta)
		_pose_shell()
		return
	match _phase:
		Phase.ARMOR: _run_armor(delta, origin)
		Phase.HEART: _run_heart(delta, origin)
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
	if _heart_target != null:
		_heart_target.position = origin

# --- Phase 1 — BRISER L'ARMURE ------------------------------------------------

func _run_armor(delta: float, origin: Vector2) -> void:
	# La coquille tourne : c'est elle qui fait défiler la plaque à viser.
	if tuning.shell_orbit_period > 0.0:
		_shell_rotation = wrapf(_shell_rotation + TAU * delta / tuning.shell_orbit_period, -PI, PI)
	# La plaque vulnérable : la plus proche du centre de l'arc face au joueur.
	var active := -1
	var best := INF
	for plate in _plates:
		plate.tick(delta, tuning.shell_break_time)
		if not plate.is_exposed(_shell_rotation, tuning.plate_arc_deg):
			continue
		var offset := absf(plate.angle_at(_shell_rotation))
		if offset < best:
			best = offset
			active = plate.index
	# ⚠️ UNE SEULE plaque encaisse, et c'est celle qui brille. Avant, toutes les plaques
	# exposées encaissaient : les dégâts se répartissaient sur quatre barres qui
	# descendaient ensemble, donc rien ne tombait avant la toute fin de la phase. Le
	# joueur tirait vingt secondes sans voir une seule pièce céder.
	for plate in _plates:
		plate.target.enabled = plate.index == active and plate.is_up()
	_set_active_piece(active)
	_pose_shell()
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

# --- Phase 2 — LE CŒUR --------------------------------------------------------

func _run_heart(delta: float, origin: Vector2) -> void:
	_open_shell(delta)
	# La coquille vidée continue de tourner, deux fois plus lentement : le boss reste
	# vivant à l'écran sans reprendre le tempo de la phase précédente.
	if tuning.shell_orbit_period > 0.0:
		_shell_rotation = wrapf(_shell_rotation + TAU * delta / (tuning.shell_orbit_period * 2.0), -PI, PI)
	_pose_shell()
	_pulse_timer -= delta
	if _pulse_timer <= 0.0:
		_pulse_timer = tuning.pulse_interval
		_fire_pulse(origin)
	_missile_timer -= delta
	if _missile_timer <= 0.0:
		_missile_timer = tuning.missile_salvo_interval
		_launch_missiles(origin)
	_tick_pull(delta, origin)

## Aspiration par vagues. ⚠️ Elle était une phase entière (« RÉSISTER ») ; elle est
## devenue une pression intermittente. La différence tient en une phrase : une phase
## impose d'apprendre une règle, une pression se sent sans qu'on l'explique.
func _tick_pull(delta: float, origin: Vector2) -> void:
	if _pull_left > 0.0:
		_pull_left = maxf(_pull_left - delta, 0.0)
		pull_changed.emit(tuning.pull_speed_max, tuning.pull_radius, origin)
		if _pull_left <= 0.0:
			pull_changed.emit(0.0, tuning.pull_radius, origin)
		return
	_pull_timer -= delta
	if _pull_timer <= 0.0:
		_pull_timer = tuning.pull_interval
		_pull_left = tuning.pull_time

## Écarte la coquille pour découvrir le cœur. C'est le seul « texte » de la transition.
func _open_shell(delta: float) -> void:
	if _phase == Phase.ARMOR or tuning.shell_open_time <= 0.0:
		return
	_shell_open = minf(_shell_open + delta / tuning.shell_open_time, 1.0)

# --- Rendu de la coque --------------------------------------------------------

## Fait tourner la coquille visible, l'écarte en phase 2, pulse le halo de la pièce à
## viser et couche les plaques abattues. Un seul écrivain sur la pose (le module), comme
## le Harvester : deux auteurs sur une même rotation finissent par se marcher dessus.
## `.transform =` réassigne un type valeur — aucune allocation par image.
func _pose_shell() -> void:
	if _shell_ring != null:
		var basis := _shell_ring_rest.basis * Basis(Vector3.UP, _shell_rotation)
		# L'ouverture recule la coquille et l'élargit : le cœur se dégage sans que la
		# silhouette se disloque.
		var opened := _shell_ring_rest.origin + Vector3(0.0, 0.0, tuning.shell_open_offset * _shell_open)
		_shell_ring.transform = Transform3D(basis.scaled(Vector3.ONE * (1.0 + 0.12 * _shell_open)), opened)
	# Les plaques abattues se couchent et s'effacent : `fall_ratio` était calculé depuis
	# le premier jour et n'était appliqué à AUCUN maillage — la plaque mourait donc sans
	# que rien ne bouge à l'écran.
	for plate in _plates:
		if plate.node == null:
			continue
		var fall := plate.fall_ratio(tuning.shell_break_time)
		if fall <= 0.0:
			continue
		plate.node.transform.basis = plate.rest_basis.rotated(plate.fall_axis, fall * PI * 0.55) \
			.scaled(Vector3.ONE * maxf(1.0 - fall, 0.05))
		if fall >= 1.0 and plate.node.visible:
			plate.node.visible = false
	if _heart_node != null:
		# ⚠️ Le cœur ne bat QU'UNE FOIS À NU. Vu en capture : un cœur qui palpite au centre
		# pendant la phase 1 attire l'œil autant que le halo de la plaque à viser, et les
		# deux sont roses. On désignait deux cibles à la fois, dont une intouchable.
		var beat := 1.0 + 0.09 * _shell_open * sin(_age * 6.0)
		_heart_node.scale = Vector3.ONE * beat
	if _highlight != null:
		# Le halo doit trancher sur une coque qui est DÉJÀ rose et ivoire. Il monte donc
		# vers le blanc chaud au sommet de son battement au lieu de rester dans la teinte
		# de la coque, où il se lisait comme un reflet.
		var pulse := 0.5 + 0.5 * sin(_age * 4.0)
		_highlight.albedo_color = Color(0.95, 0.35 + 0.45 * pulse, 0.72 + 0.24 * pulse,
			0.55 + 0.45 * pulse)

## Fait tomber les pièces détachées. Aucune allocation : `Vector3` et `Transform3D` sont
## des types valeur, et les trois tableaux sont dimensionnés au montage.
func _tick_debris(delta: float) -> void:
	for i in _debris.size():
		var fall := _debris_fall[i]
		if fall < 0.0 or fall >= 1.0:
			continue
		fall = minf(fall + delta / DEBRIS_FALL_TIME, 1.0)
		_debris_fall[i] = fall
		var node := _debris[i]
		if node == null:
			continue
		var rest := _debris_rest[i]
		# Elle part vers l'extérieur et vers le bas, en tournant : une pièce arrachée,
		# pas un objet qu'on éteint.
		var drift := Vector3(rest.origin.x * 1.4, -6.0 * fall * fall, rest.origin.z * 1.4) * fall
		node.transform = Transform3D(
			rest.basis.rotated(Vector3.FORWARD, fall * PI * 1.2).scaled(Vector3.ONE * maxf(1.0 - fall * 0.9, 0.05)),
			rest.origin + drift)
		if fall >= 1.0:
			node.visible = false

## Détache une pièce décorative encore en place. Appelée quand une plaque cède : le
## joueur casse une plaque, le boss perd un morceau de plus que ce qu'il visait.
func _shed_debris() -> void:
	for i in _debris.size():
		if _debris_fall[i] < 0.0:
			_debris_fall[i] = 0.0
			return

## Bascule la pièce à viser et n'émet qu'au changement — sinon `piece_active_changed`
## partirait à chaque image pendant toute la phase 1.
func _set_active_piece(index: int) -> void:
	if index == _active_piece:
		return
	_active_piece = index
	_apply_highlight(index)
	piece_active_changed.emit(index)

## Pose le halo sur les maillages de la plaque active, le retire des autres. Appelé
## seulement au changement : réassigner un `material_overlay` par image serait gratuit en
## pure perte. Une plaque tombée ne brille jamais (`is_up()`).
func _apply_highlight(index: int) -> void:
	for plate in _plates:
		var lit: Material = _highlight if (plate.index == index and plate.is_up()) else null
		for mesh in plate.meshes:
			mesh.material_overlay = lit

# --- Armement -----------------------------------------------------------------

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

## La salve circulaire de la phase 2 : le corps à nu se défend dans toutes les directions.
func _fire_pulse(origin: Vector2) -> void:
	if _bullet_manager == null or projectile == null:
		return
	for i in tuning.pulse_bullets:
		var a := TAU * i / float(maxi(tuning.pulse_bullets, 1))
		_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, origin,
			Vector2(cos(a), sin(a)), projectile)

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
	# boucle tourne à chaque image pendant toute la durée du combat.
	if _missiles.size() > 24:
		var kept: Array[TargetableProjectile] = []
		for missile in _missiles:
			if missile.alive:
				kept.append(missile)
			elif _bullet_manager != null:
				_bullet_manager.unregister_target(missile.target)
		_missiles = kept

# --- Transitions --------------------------------------------------------------

func _advance_phase() -> void:
	match _phase:
		Phase.ARMOR: _enter_phase(Phase.HEART)
		Phase.HEART: _enter_phase(Phase.DEFEATED)

func _enter_phase(next: Phase) -> void:
	_phase = next
	_phase_age = 0.0
	# ⚠️ Les dégâts de la phase précédente ne comptent plus : la jauge repart à plein.
	# C'est l'idiome de shmup — « il lui reste une deuxième barre » — et c'est ce qui
	# remplace une barre unique qui n'avançait que d'un tiers pour vingt secondes de jeu.
	_phase_damage = 0.0
	_interlude = 0.0 if next == Phase.ARMOR else 1.5
	if next != Phase.ARMOR:
		# Plus de « plaque à viser » : on éteint le télégraphe. C'est ce qui émet enfin
		# `-1`, la boucle de brisure ne le ferait plus.
		_set_active_piece(-1)
	match next:
		Phase.ARMOR:
			# Le corps reste CLOS tout le combat : rien ne le tue directement, seul le
			# cœur le fait tomber. Les tirs qui ratent une sous-cible ricochent
			# (`deflected`) au lieu d'entamer une barre de 20 000 PV qui ferait avancer
			# les phases par les dégâts — ce que le module refuse.
			if _boss != null:
				_boss.vulnerable = false
		Phase.HEART:
			# L'armure est tombée : le cœur est la seule cible, et il le reste.
			for plate in _plates:
				plate.target.enabled = false
			_heart_target.enabled = true
		Phase.DEFEATED:
			release()
			# Le cœur est tombé : c'est LA condition de mort. On la traduit en mort du
			# BossController, qui émet `defeated` et déclenche la finale du niveau — le
			# corps clos ne serait jamais mort de lui-même.
			if _boss != null:
				_boss.defeat()
	phase_entered.emit(next)
	_publish_structure()

# --- Dégâts -------------------------------------------------------------------

func _on_plate_hit(damage: float, index: int) -> void:
	var plate := _plates[index]
	if not plate.is_up():
		return
	_account(damage)
	if plate.apply_damage(damage):
		# Une plaque cède : une épine ou un nœud part avec elle. Le boss se démonte plus
		# vite que ce que le joueur a visé, et ça se voit.
		_shed_debris()
		piece_destroyed.emit(Phase.ARMOR, index, _piece_world(plate.target.position))
	piece_gauge_changed.emit(index, plate.health_ratio(), plate.is_up())

func _on_heart_hit(damage: float) -> void:
	if _phase != Phase.HEART or _heart_health <= 0.0:
		return
	_account(damage)
	_heart_health = maxf(_heart_health - damage, 0.0)
	if _heart_health <= 0.0:
		_advance_phase()

func _on_missile_hit(damage: float, index: int) -> void:
	if index < 0 or index >= _missiles.size():
		return
	_missiles[index].apply_damage(damage)

## Comptabilise les dégâts : pour la jauge (phase) et pour la progression (combat entier).
func _account(damage: float) -> void:
	_phase_damage += damage
	_fight_damage += damage
	_publish_structure()

func _publish_structure() -> void:
	structure_changed.emit(structure_ratio())

func _piece_world(plane: Vector2) -> Vector3:
	return GameplayPlane.to_world(plane)

# --- Lectures -----------------------------------------------------------------

func phase() -> int:
	return _phase

func shell_rotation() -> float:
	return _shell_rotation

func plates() -> Array[LeviathanPlate]:
	return _plates

## Ouverture de la coquille, de 0 à 1. Sert au niveau pour caler ses effets sur la
## révélation du cœur.
func shell_open_ratio() -> float:
	return _shell_open

func _plates_up() -> int:
	var up := 0
	for plate in _plates:
		if plate.is_up():
			up += 1
	return up

## Santé restante de la PHASE en cours, entre 1 et 0.
func structure_ratio() -> float:
	if tuning == null:
		return 1.0
	var total := tuning.phase_health(_phase) if _phase < LeviathanTuning.PHASE_COUNT else 0.0
	if total <= 0.0:
		return 0.0
	return clampf(1.0 - _phase_damage / total, 0.0, 1.0)

## Part du combat qui reste à faire, entre 1 et 0, toutes phases confondues.
##
## ⚠️ À NE PAS CONFONDRE avec `structure_ratio()`. Le HUD montre la phase — elle se remplit
## à nouveau à la bascule. La musique, elle, doit suivre le combat : lui donner le ratio de
## phase faisait culminer la partition à MI-COMBAT (fin de l'armure) puis redescendre d'un
## cran au début de la phase 2. Entendu au playtest, dans le journal : `music 9 -> 8 -> 9`.
func fight_ratio() -> float:
	if tuning == null:
		return 1.0
	var total := tuning.total_structure()
	return clampf(1.0 - _fight_damage / total, 0.0, 1.0) if total > 0.0 else 1.0

## Publie l'état de toutes les jauges. Le niveau l'appelle après `begin()`, quand le
## HUD est prêt : interroger avant afficherait des pastilles éteintes sur un boss intact.
func publish_gauges() -> void:
	# ⚠️ Les pastilles n'existent qu'en phase 1. Les publier en phase 2 RALLUME une rangée
	# que le niveau vient d'éteindre : vu en capture, quatre pastilles de plaques pleines
	# pendant que le cœur était la seule cible du combat. `set_boss_limb()` rend visible
	# la pastille qu'il met à jour — publier, c'est afficher.
	if _phase == Phase.ARMOR:
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
	for missile in _missiles:
		missile.target.enabled = false
		_bullet_manager.unregister_target(missile.target)
	_missiles.clear()
	if _heart_target != null:
		_heart_target.enabled = false
		_bullet_manager.unregister_target(_heart_target)
