class_name LeviathanCombat
extends Node
## Le combat du Pale Leviathan : **trois cycles, deux temps par cycle** (`ADR-0021`).
##
##     BRISER L'ARMURE  →  PLONGER DANS LE NOYAU  →  éjecté  →  l'armure revient, amoindrie
##
## Cycle 1 : 4 plaques et 4 tourelles-épines. Cycle 2 : 3. Cycle 3 : 2. Le boss se
## dégrade à vue et chaque cycle est plus court que le précédent.
##
## COMPOSITION — `BossController` garde tout le générique (entrée, déplacement, roulis,
## PV, signaux HUD, mort, prise de main sur le déplacement) et sert toujours le Choir
## Harvester. Ce module ne lui prend que deux choses, exactement comme `HarvesterCombat` :
## l'armement (`external_attacks`) et la vulnérabilité du corps.
##
## ⚠️ CE QUE LE PLAYTEST A DEMANDÉ, ET CE QUE CHAQUE PIÈCE DE CE FICHIER Y RÉPOND.
## Verdict : « extrêmement lancinant — le boss va de gauche à droite, on arrose les
## plaques sans faire gaffe en attendant qu'elles disparaissent ; les antennes, je ne
## vois pas à quoi elles servent ; et qu'il faille tirer le noyau, on ne le comprend pas ».
##
##   1. **Les épines tirent** (`_run_spines`). Ce sont des tourelles laser télégraphiées,
##      et **chaque plaque brisée en fait tomber une**. Casser une plaque retire une
##      menace qu'on peut nommer — le rideau s'allège d'un laser, pas d'un septième
##      d'éventail que personne ne compte.
##   2. **On entre dans le noyau** (`_run_dive`). La cible ne se devine plus : le corps
##      s'ouvre, le chasseur y est aspiré, et le flux d'énergie remplit l'écran. La mise
##      en scène (caméra, autopilote, paroi) est au niveau ; le module publie les temps.
##   3. **Les plaques tombent vite** (460 PV au lieu de 1270). Le grief est le temps passé
##      sans décision : la première salve d'armure passe de ~22 s à ~8 s.
##
## ⚠️ « RIEN NE REPOUSSE » N'EST PLUS VRAI, et c'est délibéré (ADR-0021 amende ADR-0018).
## L'armure revient entre deux plongées, avec une plaque de moins à chaque fois. Le boss
## ne se répare pas : il se répare **de plus en plus mal**, et ça se lit sur sa silhouette.
##
## ⚠️ LES PHASES N'AVANCENT PAS AUX SEUILS DE POINTS DE VIE. Chaque bascule a une
## condition matérielle : toutes les plaques du cycle à terre, ou le compte à rebours du
## noyau épuisé. Un boss qui avancerait sur ses PV changerait d'état sans que rien à
## l'écran ne l'explique — c'est ce que faisait le `BossController` générique.

const PLATE_SLOTS := 4
const SPINE_SLOTS := 4
const NODE_COUNT := 3
## Durée de chute d'une pièce détachée, en secondes.
const DEBRIS_FALL_TIME := 1.2

enum Phase { ARMOR, DIVE, DEFEATED }
## Les trois temps d'une plongée. Le module les traverse ; le niveau les met en scène.
enum Dive { ENTER, INSIDE, EJECT }
## Les états d'une tourelle-épine. Mêmes noms que le canon du Harvester, même grammaire :
## un télégraphe, un tir, une récupération.
enum Spine { DOWN, READY, WINDUP, FIRING, RECOVER }

## Le HUD et le niveau écoutent ; le module ne connaît ni l'un ni l'autre.
signal phase_entered(phase: int)
## Santé restante de ce qu'on peut casser MAINTENANT — l'armure du cycle, ou le flux
## pendant la plongée. ⚠️ Ce n'est pas la progression du combat : voir `fight_ratio()`.
signal structure_changed(ratio: float)
signal piece_gauge_changed(index: int, ratio: float, alive: bool)
## Plaque à viser (`-1` = aucune). Émis SEULEMENT au changement.
signal piece_active_changed(index: int)
signal piece_destroyed(phase: int, index: int, world_position: Vector3)
## Aspiration à appliquer au chasseur. Le niveau la relaie ; le module ne touche jamais
## au joueur directement.
signal pull_changed(speed_max: float, radius: float, centre: Vector2)
## La plongée s'ouvre : le niveau prend la main sur la caméra et l'autopilote.
signal dive_started(cycle: int, centre: Vector2)
## Le chasseur est dedans, le tir commence.
signal dive_entered(cycle: int)
## Éjection. `flux_down` dit si le flux est mort — auquel cas le boss meurt juste après.
signal dive_ended(cycle: int, flux_down: bool)
## L'armure s'est reformée, avec `plates` plaques. Le niveau l'annonce au joueur : sans
## cela, une armure qui revient se lit comme un bug, pas comme une mécanique.
signal armour_reformed(cycle: int, plates: int)

@export var tuning: LeviathanTuning
@export var projectile: ProjectileData

var _boss: BossController
var _hull: Node3D
var _bullet_manager: BulletManager
var _player: PlayerFighterController

var _phase: Phase = Phase.ARMOR
var _dive: Dive = Dive.ENTER
var _dive_elapsed: float = 0.0
## Cycle courant, 0-indexé.
var _cycle: int = 0
var _age: float = 0.0
## Répit entre deux temps : le boss ne tire pas, le joueur voit ce qu'il a cassé.
var _interlude: float = 0.0

var _plates: Array[LeviathanPlate] = []
var _flux_target: BulletTarget
var _flux_health: float = 0.0
var _missiles: Array[TargetableProjectile] = []

## Rotation de la coquille, en radians — le tempo du temps 1.
var _shell_rotation: float = 0.0
var _active_piece: int = -1
var _shell_ring: Node3D
var _shell_ring_rest: Transform3D = Transform3D.IDENTITY
var _heart_node: Node3D
var _highlight: StandardMaterial3D
## Ouverture de la coquille, de 0 (close) à 1 (le noyau est béant).
var _shell_open: float = 0.0

## Les tourelles-épines. Tableaux parallèles, dimensionnés une fois : aucune allocation
## pendant le combat.
var _spine_nodes: Array[Node3D] = []
var _spine_rest: Array[Transform3D] = []
var _spine_beams: Array[Beam] = []
var _spine_state: PackedInt32Array = PackedInt32Array()
var _spine_timer: PackedFloat32Array = PackedFloat32Array()

## Les nœuds décoratifs, qui tombent avec la première armure.
var _debris: Array[Node3D] = []
var _debris_rest: Array[Transform3D] = []
var _debris_fall: PackedFloat32Array = PackedFloat32Array()
## Chute des plaques abattues, par emplacement.
var _plate_fall: PackedFloat32Array = PackedFloat32Array()

var _fan_timer: float = 0.0
var _missile_timer: float = 0.0
## Dégâts encaissés par la cible courante — le numérateur de la jauge.
var _local_damage: float = 0.0
## Dégâts encaissés depuis le début du combat — la progression, qui ne remonte jamais.
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
		# rien, et `vulnerable` garde son défaut : le boss final devient un sac à PV
		# inoffensif. Dégrader vers l'ancien comportement vaut mieux que dégrader vers
		# l'absence de combat.
		push_error("[Leviathan] aucun LeviathanTuning : retour aux motifs generiques")
		_boss.external_attacks = false
		set_physics_process(false)
		return
	var errors := tuning.validate()
	if not errors.is_empty():
		# Le réglage est refusé AVANT le combat, pas découvert au milieu.
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
	_cycle = 0
	_flux_health = tuning.flux_health
	_fight_damage = 0.0
	_plate_fall.resize(PLATE_SLOTS)
	_plate_fall.fill(-1.0)
	_build_flux()
	_bind_shell_visual()
	_build_spines()
	_collect_debris()
	_arm_cycle(0)
	_enter_phase(Phase.ARMOR)
	# Hook de vérification : la plongée arrive après huit secondes de jeu, donc personne
	# ne la REGARDE jamais (ADR-0006). `++ --leviathan-phase=2` y saute.
	_apply_phase_hook()

## (Re)dresse l'armure du cycle : `plates_for_cycle` plaques et autant de tourelles.
##
## ⚠️ Les plaques sont REDISTRIBUÉES à chaque cycle, pas simplement éteintes. Trois
## plaques laissées à leurs anciennes places laisseraient un trou de 180° dans l'armure ;
## réparties à 120°, elles couvrent encore le corps. C'est aussi ce qui rend
## `effective_arc_deg()` nécessaire : moins de plaques, arc plus large.
func _arm_cycle(cycle: int) -> void:
	var alive := tuning.plates_for_cycle(cycle)
	_release_plates()
	_plates.clear()
	for i in alive:
		var plate := LeviathanPlate.make(i, TAU * i / float(alive), tuning.plate_health,
			tuning.plate_hitbox_radius, Callable(self, "_on_plate_hit").bind(i))
		if _hull != null:
			plate.node = _hull.find_child("Plate_%02d" % (i + 1), true, false) as Node3D
			if plate.node == null:
				push_error("[Leviathan] coque sans 'Plate_%02d' (contrat BRIEF-0040)" % (i + 1))
			else:
				plate.rest_basis = plate.node.transform.basis
				plate.node.visible = true
				_collect_meshes(plate.node, plate.meshes)
		_plates.append(plate)
		if _bullet_manager != null:
			_bullet_manager.register_target(plate.target)
		_plate_fall[i] = -1.0
	# Les emplacements au-delà du compte restent à terre, invisibles.
	for i in range(alive, PLATE_SLOTS):
		_plate_fall[i] = 1.0
		if _hull != null:
			var node := _hull.find_child("Plate_%02d" % (i + 1), true, false) as Node3D
			if node != null:
				node.visible = false
	for i in _spine_state.size():
		var up := i < alive
		_spine_state[i] = Spine.READY if up else Spine.DOWN
		# Les épines se relaient au lieu de tirer ensemble : quatre lasers simultanés
		# sont un mur, quatre lasers déphasés sont une danse.
		_spine_timer[i] = tuning.spine_interval * float(i) / float(maxi(alive, 1))
		if i < _spine_nodes.size() and _spine_nodes[i] != null:
			_spine_nodes[i].visible = up
			_spine_nodes[i].transform = _spine_rest[i]
		if i < _spine_beams.size() and _spine_beams[i] != null:
			_spine_beams[i].extinguish()
	_local_damage = 0.0
	_active_piece = -1
	_shell_open = 0.0

func _build_flux() -> void:
	_flux_target = BulletTarget.make(BulletManager.Team.ENEMY, tuning.flux_hitbox_radius,
		Callable(self, "_on_flux_hit"))
	_flux_target.enabled = false   # il n'existe que dans le noyau, pendant la plongée
	if _bullet_manager != null:
		_bullet_manager.register_target(_flux_target)

## Résout la coquille, le cœur et le halo. Nuls en test (coque absente) : la boucle
## tourne sans 3D, seule la géométrie des hitbox compte.
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
		# Additif, non éclairé : un halo qui s'AJOUTE à la texture au lieu de la
		# remplacer. Il monte vers le blanc chaud au sommet de son battement, sans quoi
		# il se lit comme un reflet sur une coque déjà rose.
		_highlight = StandardMaterial3D.new()
		_highlight.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_highlight.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		_highlight.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_highlight.albedo_color = Color(0.95, 0.35, 0.72, 1.0)

## Les épines deviennent des tourelles. Leur faisceau n'est construit que dans l'arbre :
## en test il reste nul, et `_fire_spine` le null-garde — la portée est éprouvée à part
## par `test_beam_geometry.gd`, sur la fonction statique.
func _build_spines() -> void:
	_spine_nodes.clear()
	_spine_rest.clear()
	_spine_beams.clear()
	_spine_state.resize(SPINE_SLOTS)
	_spine_timer.resize(SPINE_SLOTS)
	for i in SPINE_SLOTS:
		var node: Node3D = null
		if _hull != null:
			node = _hull.find_child("Spike_%02d" % (i + 1), true, false) as Node3D
			if node == null:
				push_error("[Leviathan] coque sans 'Spike_%02d' (contrat BRIEF-0040)" % (i + 1))
		_spine_nodes.append(node)
		_spine_rest.append(node.transform if node != null else Transform3D.IDENTITY)
		var beam: Beam = null
		if is_inside_tree():
			beam = Beam.make()
			# ⚠️ `top_level` OBLIGATOIRE. `Beam.aim()` pose le faisceau en coordonnées
			# MONDE ; ce module est un `Node` enfant du `BossController`, et Godot remonte
			# l'arbre jusqu'au premier ancêtre `Node3D` pour composer les transformations —
			# le faisceau subirait donc la position du boss DEUX fois et partirait hors du
			# cadre. Symptôme : aucun laser à l'écran, et rien au journal.
			beam.top_level = true
			add_child(beam)
		_spine_beams.append(beam)
		_spine_state[i] = Spine.DOWN
		_spine_timer[i] = 0.0

## Les nœuds : décor pur depuis ADR-0020, ils tombent avec la première armure.
func _collect_debris() -> void:
	_debris.clear()
	_debris_rest.clear()
	_debris_fall.resize(0)
	if _hull == null:
		return
	for i in NODE_COUNT:
		var node := _hull.find_child("Node_%02d" % (i + 1), true, false) as Node3D
		if node == null:
			continue
		node.visible = true
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

func _apply_phase_hook() -> void:
	for arg in OS.get_cmdline_user_args():
		if not arg.begins_with("--leviathan-phase"):
			continue
		var wanted := arg.get_slice("=", 1).to_int() if "=" in arg else 0
		if wanted >= 2:
			_force_dive()
		return

## Abat toute l'armure du cycle et ouvre la plongée. Réservé au hook de debug.
##
## ⚠️ Passe par `_on_plate_hit`, pas par `plate.apply_damage` : c'est le chemin réel des
## dégâts, celui qui fait tomber les épines et publie les jauges. Le raccourci menait à
## un état que le jeu ne produit jamais.
func _force_dive() -> void:
	if _phase != Phase.ARMOR:
		return
	for plate in _plates:
		_on_plate_hit(plate.max_health, plate.index)

# --- Boucle -------------------------------------------------------------------

func _physics_process(delta: float) -> void:
	tick(delta)

## Toute la logique du combat. Publique et sans dépendance à l'arbre : les tests la
## pilotent directement, ce qui rend vérifiable un enchaînement qu'aucune capture ne
## pourrait couvrir — trois cycles demandent quarante secondes de jeu.
func tick(delta: float) -> void:
	if tuning == null:
		return
	_age += delta
	var origin := _origin()
	_tick_missiles(delta)
	_tick_debris(delta)
	_tick_plate_falls(delta)
	if _interlude > 0.0:
		_interlude = maxf(_interlude - delta, 0.0)
		_pose_shell()
		return
	match _phase:
		Phase.ARMOR: _run_armor(delta, origin)
		Phase.DIVE: _run_dive(delta, origin)
		Phase.DEFEATED: return
	_sync_targets(origin)

## Position du boss dans le plan. Le plan est la vérité des collisions : il ne dépend ni
## de l'arbre ni du roulis, et reste lisible en test où rien n'est monté.
func _origin() -> Vector2:
	return _boss.plane_position if _boss != null else Vector2.ZERO

func _sync_targets(origin: Vector2) -> void:
	for plate in _plates:
		var a := plate.angle_at(_shell_rotation)
		plate.target.position = origin + Vector2(cos(a), sin(a)) * 2.6
	if _flux_target != null:
		_flux_target.position = origin + _flux_offset()

## Dérive du flux dans le noyau : assez pour qu'on suive, pas assez pour qu'on cherche.
func _flux_offset() -> Vector2:
	if _phase != Phase.DIVE or tuning.flux_drift_period <= 0.0:
		return Vector2.ZERO
	var t := TAU * _age / tuning.flux_drift_period
	return Vector2(cos(t), sin(t * 0.7)) * tuning.flux_drift_radius

# --- Temps 1 — BRISER L'ARMURE ------------------------------------------------

func _run_armor(delta: float, origin: Vector2) -> void:
	if tuning.shell_orbit_period > 0.0:
		_shell_rotation = wrapf(_shell_rotation + TAU * delta / tuning.shell_orbit_period, -PI, PI)
	var arc := tuning.effective_arc_deg(_plates_up())
	var active := -1
	var best := INF
	for plate in _plates:
		plate.tick(delta, tuning.shell_break_time)
		if not plate.is_exposed(_shell_rotation, arc):
			continue
		var offset := absf(plate.angle_at(_shell_rotation))
		if offset < best:
			best = offset
			active = plate.index
	# ⚠️ UNE SEULE plaque encaisse, et c'est celle qui brille. Quand toutes les plaques
	# exposées encaissaient, les dégâts se répartissaient sur quatre barres qui
	# descendaient ensemble : rien ne tombait avant la fin de la phase.
	for plate in _plates:
		plate.target.enabled = plate.index == active and plate.is_up()
	_set_active_piece(active)
	_pose_shell()
	_run_spines(delta, origin)
	_fan_timer -= delta
	if _fan_timer <= 0.0:
		_fan_timer = tuning.fan_interval
		_fire_fans(origin)
	_missile_timer -= delta
	if _missile_timer <= 0.0:
		_missile_timer = tuning.missile_salvo_interval
		_launch_missiles(origin)
	if _plates_up() == 0:
		_begin_dive()

## Les tourelles-épines. Trois temps, comme le canon du Harvester : le télégraphe fin qui
## annonce, le faisceau qui frappe, la récupération. ⚠️ C'est le télégraphe qui fait le
## duel — un laser sans réarme est un impôt, pas une attaque.
func _run_spines(delta: float, origin: Vector2) -> void:
	for i in _spine_state.size():
		if _spine_state[i] == Spine.DOWN:
			continue
		_spine_timer[i] -= delta
		if _spine_timer[i] > 0.0:
			if _spine_state[i] == Spine.WINDUP or _spine_state[i] == Spine.FIRING:
				_aim_spine(i, origin)
			continue
		match _spine_state[i]:
			Spine.READY:
				_spine_state[i] = Spine.WINDUP
				_spine_timer[i] = tuning.spine_windup_time
			Spine.WINDUP:
				_spine_state[i] = Spine.FIRING
				_spine_timer[i] = tuning.spine_beam_time
			Spine.FIRING:
				_spine_state[i] = Spine.RECOVER
				_spine_timer[i] = tuning.spine_recover_time
				if i < _spine_beams.size() and _spine_beams[i] != null:
					_spine_beams[i].extinguish()
			Spine.RECOVER:
				_spine_state[i] = Spine.READY
				_spine_timer[i] = tuning.spine_interval

## Tend le faisceau d'une épine et, s'il est armé, brûle ce qu'il touche.
##
## ⚠️ La bouche est la POINTE de l'épine quand la coque est là, pas un point calculé sur
## un cercle. Un laser qui sort du corps pendant que l'épine pointe ailleurs rend la
## menace illisible sur la silhouette — et c'est précisément ce qu'on reproche à ces
## pièces depuis le début : qu'on ne voie pas à quoi elles servent.
func _aim_spine(index: int, origin: Vector2) -> void:
	var direction := _spine_direction(index)
	var muzzle := origin + direction * 3.2
	var node: Node3D = _spine_nodes[index] if index < _spine_nodes.size() else null
	if node != null and node.is_inside_tree():
		muzzle = GameplayPlane.to_plane(node.global_position)
		var away := muzzle - origin
		if away.length_squared() > 0.01:
			direction = away.normalized()
	var reach := muzzle + direction * tuning.spine_range
	var firing := _spine_state[index] == Spine.FIRING
	if index < _spine_beams.size() and _spine_beams[index] != null:
		var beam := _spine_beams[index]
		beam.aim(muzzle, reach, tuning.spine_half_width if firing else tuning.spine_half_width * 0.35)
		beam.set_regime(2.4 if firing else 0.35, 0.0 if firing else 1.0)
	if not firing or _player == null:
		return
	if Beam.hits(muzzle, reach, tuning.spine_half_width, _player.plane_position, 0.25):
		_player.take_contact_damage(tuning.spine_damage)

## Direction d'une épine : sa place autour du corps, entraînée par la coquille. Le
## faisceau part donc là où l'épine POINTE — sinon le joueur ne peut pas lire la menace
## sur la silhouette, et le laser semble sortir de nulle part.
func _spine_direction(index: int) -> Vector2:
	var a := wrapf(TAU * float(index) / float(SPINE_SLOTS) + _shell_rotation * 0.5, -PI, PI)
	return Vector2(cos(a), sin(a))

# --- Temps 2 — PLONGER DANS LE NOYAU ------------------------------------------

func _begin_dive() -> void:
	_enter_phase(Phase.DIVE)

func _run_dive(delta: float, origin: Vector2) -> void:
	_dive_elapsed += delta
	_shell_open = minf(_shell_open + delta / tuning.shell_open_time, 1.0)
	_pose_shell()
	match _dive:
		Dive.ENTER:
			# L'aspiration accompagne le chasseur vers l'ouverture. Elle reste sous sa
			# vitesse : il entre parce qu'il le veut, pas parce qu'on le lui impose.
			pull_changed.emit(tuning.pull_speed_max, tuning.pull_radius, origin)
			if _dive_elapsed >= tuning.dive_enter_time:
				_set_dive(Dive.INSIDE)
		Dive.INSIDE:
			pull_changed.emit(0.0, tuning.pull_radius, origin)
			if _dive_elapsed >= tuning.dive_time:
				_set_dive(Dive.EJECT)
		Dive.EJECT:
			if _dive_elapsed >= tuning.dive_eject_time:
				_leave_dive()

func _set_dive(next: Dive) -> void:
	_dive = next
	_dive_elapsed = 0.0
	match next:
		Dive.INSIDE:
			# Le flux n'est une cible QUE dans le noyau : dehors, il n'est pas atteignable
			# et le joueur n'a aucune raison de croire qu'il l'est.
			_flux_target.enabled = true
			_local_damage = 0.0
			_publish_structure()
			dive_entered.emit(_cycle)
		Dive.EJECT:
			_flux_target.enabled = false
			dive_ended.emit(_cycle, _flux_health <= 0.0)

## Fin de plongée : le boss meurt si le flux est tombé, sinon l'armure se reforme.
func _leave_dive() -> void:
	# Le corps reprend sa dérive : le combat redevient mobile en même temps que l'armure
	# revient. Relâcher AVANT la mort aussi, sinon un boss vaincu resterait figé pendant
	# la finale.
	if _boss != null:
		_boss.release_drive()
	if _flux_health <= 0.0:
		_enter_phase(Phase.DEFEATED)
		return
	_cycle += 1
	_arm_cycle(_cycle)
	_enter_phase(Phase.ARMOR)
	armour_reformed.emit(_cycle, _plates.size())

# --- Rendu de la coque --------------------------------------------------------

## Fait tourner la coquille, l'écarte pendant la plongée, pulse le halo de la plaque à
## viser et couche les pièces abattues. Un seul écrivain sur la pose (le module), comme
## le Harvester : deux auteurs sur une même rotation finissent par se marcher dessus.
## `.transform =` réassigne un type valeur — aucune allocation par image.
func _pose_shell() -> void:
	if _shell_ring != null:
		var basis := _shell_ring_rest.basis * Basis(Vector3.UP, _shell_rotation)
		var opened := _shell_ring_rest.origin + Vector3(0.0, 0.0, tuning.shell_open_offset * _shell_open)
		_shell_ring.transform = Transform3D(basis.scaled(Vector3.ONE * (1.0 + 0.18 * _shell_open)), opened)
	if _heart_node != null:
		# ⚠️ Le cœur ne bat QUE dans le noyau ouvert. Un cœur qui palpite au centre
		# pendant le temps 1 attire l'œil autant que le halo de la plaque à viser, et les
		# deux sont roses : on désignait deux cibles à la fois, dont une intouchable.
		_heart_node.scale = Vector3.ONE * (1.0 + 0.12 * _shell_open * sin(_age * 6.0))
	if _highlight != null:
		var pulse := 0.5 + 0.5 * sin(_age * 4.0)
		_highlight.albedo_color = Color(0.95, 0.35 + 0.45 * pulse, 0.72 + 0.24 * pulse,
			0.55 + 0.45 * pulse)

## Couche les plaques abattues. `fall_ratio` était calculé depuis le premier jour et
## n'était appliqué à AUCUN maillage — la plaque mourait sans que rien ne bouge.
func _tick_plate_falls(delta: float) -> void:
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
	# Les épines tombées suivent le même mouvement, une seconde après la plaque qui les
	# a emportées : on voit la cause, puis l'effet.
	for i in _spine_state.size():
		if _spine_state[i] != Spine.DOWN or i >= _spine_nodes.size():
			continue
		var node := _spine_nodes[i]
		if node == null or not node.visible:
			continue
		var rest := _spine_rest[i]
		node.transform = Transform3D(rest.basis.scaled(Vector3.ONE * 0.92), rest.origin)
		node.visible = false

## Fait tomber les pièces décoratives. Aucune allocation : `Vector3` et `Transform3D`
## sont des types valeur, et les tableaux sont dimensionnés au montage.
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
		var drift := Vector3(rest.origin.x * 1.4, -6.0 * fall * fall, rest.origin.z * 1.4) * fall
		node.transform = Transform3D(
			rest.basis.rotated(Vector3.FORWARD, fall * PI * 1.2).scaled(Vector3.ONE * maxf(1.0 - fall * 0.9, 0.05)),
			rest.origin + drift)
		if fall >= 1.0:
			node.visible = false

func _shed_debris() -> void:
	for i in _debris.size():
		if _debris_fall[i] < 0.0:
			_debris_fall[i] = 0.0
			return

func _set_active_piece(index: int) -> void:
	if index == _active_piece:
		return
	_active_piece = index
	_apply_highlight(index)
	piece_active_changed.emit(index)

## Pose le halo sur les maillages de la plaque active, le retire des autres. Appelé
## seulement au changement : réassigner un `material_overlay` par image serait gratuit
## en pure perte.
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

func _enter_phase(next: Phase) -> void:
	_phase = next
	# ⚠️ Les dégâts de ce qui vient d'être détruit ne comptent plus : la jauge repart à
	# plein pour la cible suivante. C'est l'idiome de shmup — « il lui reste une barre » —
	# et c'est ce qui remplace une barre unique qui n'avançait que d'un tiers pour vingt
	# secondes de jeu.
	_local_damage = 0.0
	match next:
		Phase.ARMOR:
			_interlude = 0.0 if _cycle == 0 else 1.2
			# Le corps reste CLOS tout le combat : seul le flux le tue. Les tirs qui
			# ratent une sous-cible ricochent au lieu d'entamer une barre de 20 000 PV
			# qui ferait avancer les phases par les dégâts.
			if _boss != null:
				_boss.vulnerable = false
		Phase.DIVE:
			_dive = Dive.ENTER
			_dive_elapsed = 0.0
			_interlude = 0.0
			_set_active_piece(-1)
			# ⚠️ LE BOSS S'IMMOBILISE. Il dérive de gauche à droite en permanence ; un
			# noyau qui glisse pendant que le chasseur est dedans emporterait le joueur
			# hors du cadre sans qu'il ait rien fait. `drive_toward` à vitesse nulle est
			# la prise de main prévue pour ça (`BossController.drive_toward`).
			if _boss != null:
				_boss.drive_toward(_origin(), 0.0)
			dive_started.emit(_cycle, _origin())
		Phase.DEFEATED:
			release()
			# Le flux est tombé : c'est LA condition de mort. On la traduit en mort du
			# BossController, qui émet `defeated` et déclenche la finale du niveau — le
			# corps clos ne serait jamais mort de lui-même.
			if _boss != null:
				_boss.defeat()
	phase_entered.emit(next)
	_publish_structure()

# --- Dégâts -------------------------------------------------------------------

func _on_plate_hit(damage: float, index: int) -> void:
	if index < 0 or index >= _plates.size():
		return
	var plate := _plates[index]
	if not plate.is_up():
		return
	_account(damage)
	if plate.apply_damage(damage):
		# ⚠️ LA PLAQUE EMPORTE SON ÉPINE. C'est la réponse au « je ne vois pas à quoi
		# servent les antennes » : elles tirent, et casser une plaque en éteint une.
		# La récompense est une menace en moins, pas un septième d'éventail.
		_drop_spine(index)
		_shed_debris()
		piece_destroyed.emit(Phase.ARMOR, index, _piece_world(plate.target.position))
	piece_gauge_changed.emit(index, plate.health_ratio(), plate.is_up())

func _drop_spine(index: int) -> void:
	if index < 0 or index >= _spine_state.size():
		return
	_spine_state[index] = Spine.DOWN
	if index < _spine_beams.size() and _spine_beams[index] != null:
		_spine_beams[index].extinguish()

func _on_flux_hit(damage: float) -> void:
	if _phase != Phase.DIVE or _dive != Dive.INSIDE or _flux_health <= 0.0:
		return
	_account(damage)
	_flux_health = maxf(_flux_health - damage, 0.0)
	if _flux_health <= 0.0:
		# Le flux tombe : on ne coupe pas la plongée en deux, l'éjection reste jouée.
		_set_dive(Dive.EJECT)

func _on_missile_hit(damage: float, index: int) -> void:
	if index < 0 or index >= _missiles.size():
		return
	_missiles[index].apply_damage(damage)

func _account(damage: float) -> void:
	_local_damage += damage
	_fight_damage += damage
	_publish_structure()

func _publish_structure() -> void:
	structure_changed.emit(structure_ratio())

func _piece_world(plane: Vector2) -> Vector3:
	return GameplayPlane.to_world(plane)

# --- Lectures -----------------------------------------------------------------

func phase() -> int:
	return _phase

func dive_step() -> int:
	return _dive

func cycle() -> int:
	return _cycle

func shell_rotation() -> float:
	return _shell_rotation

func plates() -> Array[LeviathanPlate]:
	return _plates

func shell_open_ratio() -> float:
	return _shell_open

## Nombre de tourelles-épines encore debout — ce que le joueur voit diminuer.
func spines_up() -> int:
	var up := 0
	for state in _spine_state:
		if state != Spine.DOWN:
			up += 1
	return up

func _plates_up() -> int:
	var up := 0
	for plate in _plates:
		if plate.is_up():
			up += 1
	return up

## Santé de ce qu'on peut casser MAINTENANT, entre 1 et 0.
func structure_ratio() -> float:
	if tuning == null:
		return 1.0
	var total := tuning.flux_health if _phase == Phase.DIVE \
		else tuning.plate_health * float(maxi(_plates.size(), 1))
	if total <= 0.0:
		return 0.0
	return clampf(1.0 - _local_damage / total, 0.0, 1.0)

## Part du combat qui reste, toutes phases confondues.
##
## ⚠️ À NE PAS CONFONDRE avec `structure_ratio()`. Le HUD montre la cible courante — elle
## se remplit à nouveau à chaque bascule. La musique, elle, doit suivre le combat : lui
## donner le ratio local faisait culminer la partition à mi-combat puis redescendre d'un
## cran. Entendu au playtest, lisible au journal (`music 9 -> 8 -> 9`).
func fight_ratio() -> float:
	if tuning == null:
		return 1.0
	var total := tuning.total_structure()
	return clampf(1.0 - _fight_damage / total, 0.0, 1.0) if total > 0.0 else 1.0

## Publie l'état de toutes les jauges. Le niveau l'appelle après `begin()`, quand le HUD
## est prêt : interroger avant afficherait des pastilles éteintes sur un boss intact.
##
## ⚠️ Seulement pendant le temps 1. Les publier dans le noyau RALLUME une rangée que le
## niveau vient d'éteindre : `set_boss_limb()` rend visible la pastille qu'il met à jour.
func publish_gauges() -> void:
	if _phase == Phase.ARMOR:
		for plate in _plates:
			piece_gauge_changed.emit(plate.index, plate.health_ratio(), plate.is_up())
	_publish_structure()

func _release_plates() -> void:
	if _bullet_manager == null:
		return
	for plate in _plates:
		plate.target.enabled = false
		_bullet_manager.unregister_target(plate.target)

## Retire TOUTES les cibles du gestionnaire. Sans cela, un boss vaincu ou un remontage
## laisse des cibles actives, callback vivant, position figée : un mur invisible qui
## mange les balles du joueur.
func release() -> void:
	for beam in _spine_beams:
		if beam != null:
			beam.extinguish()
	if _bullet_manager == null:
		return
	_release_plates()
	for missile in _missiles:
		missile.target.enabled = false
		_bullet_manager.unregister_target(missile.target)
	_missiles.clear()
	if _flux_target != null:
		_flux_target.enabled = false
		_bullet_manager.unregister_target(_flux_target)
