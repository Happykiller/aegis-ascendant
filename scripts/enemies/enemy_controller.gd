class_name EnemyController
extends Node3D
## Composition base for enemies (spec §11, §20.3). Graybox behaviour:
## descend + lateral sine weave, slow forward fire (Needle Scout family).
## Instances are pooled: spawners preinstantiate then activate/deactivate;
## death never queue_free()s during gameplay (spec §26.1).

## Réglages de la plume Null Choir (ADR-0017). Chargé ici et non dans `EnemyData` :
## c'est une couleur de CAMP, pas une caractéristique d'espèce — la répliquer dans les
## neuf `.tres` d'ennemis garantirait qu'un jour ils ne s'accorderaient plus.
const PLUME_TUNING := preload("res://resources/vfx/plume_null_choir.tres")
## Un ennemi plonge vers le joueur à régime établi : il n'a ni manche ni ralenti. On lui
## pose une poussée haute et fixe — assez pour que ses disques de Mach s'allument, ce qui
## distingue à l'œil une coque en approche d'une épave qui dérive.
const PLUME_THROTTLE := 0.9

const MUZZLE_OFFSET := Vector2(0.0, -0.6)
const DESPAWN_MARGIN := 1.5
## Marge de sortie par le HAUT : au-delà, un ennemi qui bat en retraite est perdu.
const ESCAPE_MARGIN := 3.0

signal destroyed(enemy: EnemyController)
## Emitted on each shot (audio cue).
signal fired
## Emitted when the enemy takes a hit without dying (audio cue).
signal hit
## Changement d'état de la menace de proximité (`EnemyReaction.State`).
##
## Ce qu'une mine fait ne se voit pas dans sa position : elle dérive pareil qu'elle
## dorme ou qu'elle s'apprête à éclater. Sans ce signal, son comportement n'est
## observable qu'à l'œil, sur une capture — c'est-à-dire mal.
signal reaction_changed(state: int)

@export var data: EnemyData
## Optional wiring for enemies placed directly in a scene (spawners inject
## through setup() instead).
@export var bullet_manager_path: NodePath
@export var auto_activate: bool = false

var active: bool = false
var plane_position: Vector2 = Vector2.ZERO

## Seconds the hull stays lit after taking a hit (spec §17: feedback under 120 ms).
const HIT_FLASH_TIME := 0.09
## Peak opacity of the additive white wash laid over the hull on impact.
const FLASH_STRENGTH := 0.85
## How hard the hull banks into its weave, in degrees at full lateral speed.
const MAX_BANK_DEG := 26.0

## Teinte de l'éclat quand un coup est ABSORBÉ par un bouclier d'aura. Le blanc dit
## « touché », celle-ci dit « touché et sans effet » — deux informations, deux
## couleurs, sinon le joueur croit à un défaut de collision.
const SHIELD_FLASH_TINT := Color(0.42, 0.85, 1.0)

## Durée d'une couverture d'aura, renouvelée à chaque image par le porteur. Assez
## longue pour tenir entre deux images même à cadence dégradée, assez courte pour
## que la mort du porteur se voie tout de suite.
const AURA_GRACE := 0.12

## Période de respiration d'une coque articulée SANS télégraphe (porteur de
## bouclier). Lente : c'est un signe de vie, pas une annonce.
const PASSIVE_POSE_PERIOD := 5.3

var _bullet_manager: BulletManager
var _target: BulletTarget
## Point de spawn : les trajectoires sont des fonctions de l'âge ET de ce point.
var _spawn: Vector2 = Vector2.ZERO
var _age: float = 0.0
## Graine de dérive organique, posée à chaque activation (`OrganicDrift`). C'est elle qui
## fait que deux coques de la même nuée n'ondulent pas à l'unisson. `NO_DRIFT` par défaut :
## une unité montée à la main dans un test garde sa courbe nue.
var _drift_seed: float = EnemyPath.NO_DRIFT
var _fire_timer: float = 0.0
var _hit_flash: float = 0.0
var _plume: EnginePlume
## Additive wash laid over the hull mesh on impact. A mesh has no `modulate`, so
## the flash is an overlay pass rather than a tint.
var _flash_material: StandardMaterial3D
## Couleur du prochain éclat : blanche si le coup porte, bleue s'il est absorbé.
var _flash_tint: Color = Color.WHITE
## Distance from the enemy's origin to its gun, read from the hull.
var _muzzle_offset: Vector2 = MUZZLE_OFFSET
## Le joueur, injecté par le spawner. `null` est un cas normal : une unité qui ne
## réagit à rien n'a aucune raison de le connaître, et les tests n'en ont pas.
var _player: PlayerFighterController
## Menace de proximité (`EnemyReaction`). Une unité non réactive reste DORMANT.
var _state: int = EnemyReaction.State.DORMANT
var _state_time: float = 0.0
var _threat: float = 0.0
var _reactive: bool = false
## Numéro de salve : c'est lui qui fait tourner les couronnes de `Fire.RADIAL`
## d'un tir au suivant, pour qu'un trou ne reste jamais au même endroit.
var _salvo: int = 0
var _vitals: EnemyVitals
## Poursuite (`Motion.HOMING`) : la vitesse courante, seule chose que le contrôleur
## accumule. Les unités `PATH` ne s'en servent pas — leur position reste une
## fonction de leur âge.
var _velocity: Vector2 = Vector2.ZERO
## Décalage figé à l'instant de l'accrochage : la sangsue se pose LÀ où elle a
## touché, et y reste. Sans ça elle se téléporterait au centre du chasseur, où le
## moindre tir vers l'avant la détruirait aussitôt.
var _attach_offset: Vector2 = Vector2.ZERO
## Pièces articulées de la coque, s'il y en a (mines, corolles, berceaux).
var _pose: EnemyPose
## Secondes d'invulnérabilité restantes, accordées par un porteur de bouclier.
##
## Un COMPTE À REBOURS et non un drapeau : le porteur repose la couverture à chaque
## image, et l'unité la consomme. Aucun ordre d'exécution à garantir entre eux, et
## rien à nettoyer quand le porteur meurt — la couverture s'éteint d'elle-même.
var _shield_grace: float = 0.0
## Ouverture LISSÉE de la coque : la cible vient d'`EnemyReaction`, celle-ci la suit à
## vitesse bornée pour que le geste existe.
var _open: float = 0.0
## Voisins couverts par l'aura, résolus UNE fois. Le pool est préinstancié avant la
## première activation, donc le groupe ne bouge plus : rappeler `get_nodes_in_group`
## à chaque image allouerait un tableau par porteur et par frame.
var _neighbours: Array[EnemyController] = []

## --- Le champ de protection, rendu VISIBLE -----------------------------------
##
## ⚠️ SANS LUI, LA MÉCANIQUE EST INJOUABLE. Le porteur couvre bien ses voisins et une
## unité couverte montre qu'elle encaisse sans rien perdre — mais tant que la PORTÉE ne
## se voit pas, le joueur constate que ses tirs ne portent pas sans pouvoir savoir **où**
## la bulle s'arrête. Il ne peut donc pas jouer contre : il subit.
## `BRIEF-0046` l'avait écrit et mis hors du périmètre de la forge, précisément pour ça :
## « le dôme est généré par le code, à partir du rayon d'aura — il doit montrer la portée
## RÉELLE, qui est une valeur de gameplay et non une dimension de maillage. Si tu le
## sculptais, il mentirait au premier réglage. »
##
## D'où l'anneau au ras du plan de jeu : le combat se joue en 2D logique, et la frontière
## qui compte est un CERCLE, pas une surface. Le dôme, lui, dit seulement qu'il y a un
## volume — c'est l'anneau qu'on lit.

## Demi-épaisseur de l'anneau, en unités monde.
## Vitesse d'ouverture et de refermeture de la coque, en fraction par seconde. À 2,2 une
## coque met ~0,3 s à se rabattre depuis le sursis : assez pour qu'on VOIE le geste, assez
## vite pour que la mine soit prête au prochain passage.
const OPEN_RATE := 2.2

## Portée de la détonation d'une sangsue, en plus de son propre rayon. Courte, et c'est le
## sujet : elle punit celui qui l'a laissée mordre, pas celui qui est parti.
const DETONATION_REACH := 1.6

## Le rayon tracteur du puits gravitique. ⚠️ Plus LARGE que les liens du porteur (0,55) :
## il ne désigne pas une unité lointaine, il dit une force qui s'exerce sur TOI, et c'est
## le seul lien de l'écran qui te concerne directement.
const TRACTOR_WIDTH := 0.9
## Violet profond du Null Choir. ⛔ Ni cyan ni corail : ils appartiennent au tir allié et
## au tir ennemi, et un rayon de cette taille dans l'une de ces teintes se lirait comme un
## projectile qu'on peut esquiver — alors qu'il n'y a rien à esquiver, seulement à fuir.
const TRACTOR_TINT := Color(0.62, 0.28, 0.86)

const AURA_RING_THICKNESS := 0.09

## Le champ peint (`TEX-0008`). Chargé à l'exécution : sans lui, le tore procédural reprend
## la main — le bestiaire doit rester jouable sans ses images.
const AURA_SPRITE := "res://assets/imported/vfx/champ_porteur.png"
## Violet du Chœur Nul. ⚠️ Ni cyan ni corail : ces deux teintes appartiennent au tir
## allié et au tir ennemi, et un champ qui les emprunterait leur volerait leur lisibilité.
const AURA_TINT := Color(0.78, 0.32, 0.98)
## Respiration du champ, en secondes. La même que celle des pièces d'une unité passive :
## le porteur n'a pas de télégraphe, il ne fait que tourner.
const AURA_PULSE_PERIOD := 5.3

var _aura_visual: Node3D
var _aura_edge_material: StandardMaterial3D
## Les liens tendus du porteur vers les unités qu'il couvre. Préalloués : voir `_draw_link`.
var _links: Array[MeshInstance3D] = []
## L'horloge du défilement. Une seule pour tous les liens d'un porteur : ils battent
## ensemble, ce qui les lit comme UN champ et non comme des câbles indépendants.
var _link_age: float = 0.0
## Le rayon tracteur, pour un puits gravitique. `null` pour toutes les autres familles.
var _tractor: MeshInstance3D

@onready var _health: HealthComponent = $HealthComponent
@onready var _visual_root: Node3D = $VisualRoot
## Enemies that carry a hull can flash and bank; ones that don't just skip it.
@onready var _hull: Node3D = get_node_or_null("VisualRoot/Hull") as Node3D

func _ready() -> void:
	assert(data != null, "EnemyController requires an EnemyData resource")
	for error in data.validate():
		push_error("[Enemy:%s] invalid data: %s" % [data.display_name, error])
	add_to_group("enemies")
	_health.died.connect(_on_died)
	_health.damaged.connect(_on_damaged)
	# ⚠️ Les dégâts passent par NOUS et non plus directement par la santé : c'est ici
	# qu'une unité couverte par un porteur de bouclier les absorbe. Brancher
	# `HealthComponent.apply_damage` en direct ne laissait aucun endroit pour le dire.
	_target = BulletTarget.make(BulletManager.Team.ENEMY, data.hitbox_radius,
		Callable(self, "_receive_damage"))
	_target.enabled = false
	_reactive = EnemyReaction.is_reactive(data)
	if _hull != null:
		var muzzle := _attach_point("Muzzle_C")
		_muzzle_offset = Vector2(muzzle.x, -muzzle.z)
		_build_flash_overlay()
		if _hull.find_child("Engine_C", true, false) != null:
			_build_plume()
		_vitals = EnemyVitals.bind(_hull)
		_pose = EnemyPose.bind(_hull, data.moving_part_prefix, data.open_angle_deg,
			data.open_spread)
	# ⚠️ HORS du bloc de la coque, et volontairement : le champ est une valeur de gameplay,
	# pas une pièce d'asset. Une unité dont le `.glb` manquerait doit quand même montrer sa
	# portée — sinon le jour où un asset tombe, c'est la MÉCANIQUE qui disparaît avec lui.
	if data.effect == EnemyData.Effect.SHIELD_AURA and data.aura_radius > 0.0:
		_build_aura_visual()
	if data.effect == EnemyData.Effect.GRAVITY_WELL and data.pull_radius > 0.0:
		_tractor = FlowLink.build(TRACTOR_TINT, TRACTOR_WIDTH, 2.6)
		_tractor.name = "Tractor"
		add_child(_tractor)
	if _bullet_manager == null and not bullet_manager_path.is_empty():
		setup(get_node(bullet_manager_path) as BulletManager)
	_set_active(false)
	if auto_activate:
		activate(GameplayPlane.to_plane(position))

## One-time wiring done by the owner (spawner or scene).
##
## Le joueur est OPTIONNEL et ne sert qu'aux unités qui le regardent : menace de
## proximité, salve visée, puits gravitationnel. Les neuf familles écrites avant
## cet axe ne le lisent jamais — leur trajectoire reste une fonction pure de leur
## âge, et c'est ce qui garde le pooling et les tests headless valables (ADR-0022).
func setup(bullet_manager: BulletManager, player: PlayerFighterController = null) -> void:
	_bullet_manager = bullet_manager
	_bullet_manager.register_target(_target)
	_player = player

## `drift_seed` : la phase de dérive de CETTE apparition. Réassignée à chaque activation —
## c'est ce qui garde le pooling sûr tout en donnant à une coque réutilisée un mouvement
## qui n'est pas celui de la précédente.
func activate(spawn_plane_position: Vector2, drift_seed: float = EnemyPath.NO_DRIFT) -> void:
	plane_position = spawn_plane_position
	_spawn = spawn_plane_position
	_age = 0.0
	_drift_seed = drift_seed
	_fire_timer = data.fire_interval
	if data.motion == EnemyData.Motion.HOMING:
		_velocity = EnemyHoming.initial_velocity(spawn_plane_position, _player_position(),
			data.move_speed)
	_health.max_health = data.max_health
	_health.revive()
	position = GameplayPlane.to_world(plane_position)
	_set_active(true)

func deactivate() -> void:
	_set_active(false)

func _set_active(value: bool) -> void:
	active = value
	visible = value
	set_physics_process(value)
	if _target != null:
		_target.enabled = value
	if _plume != null:
		# Pooled instances are reused: a dormant hull must not keep burning.
		# `snap_throttle` et non `set_throttle` : une instance recyclée qui revient en
		# scène doit déjà pousser, pas allumer son moteur devant le joueur.
		_plume.snap_throttle(PLUME_THROTTLE if value else 0.0)
	# Toute pose et tout régime se rejouent à zéro : une mine recyclée qui revient
	# en scène déjà éveillée désignerait une menace qui n'existe pas, et sa salve
	# serait déjà partie.
	_state = EnemyReaction.State.DORMANT
	_state_time = 0.0
	_threat = 0.0
	_salvo = 0
	_shield_grace = 0.0
	_open = 0.0
	if _vitals != null:
		_vitals.reset()
	if _pose != null:
		_pose.reset()
	if value and _flash_material != null:
		_hit_flash = 0.0
		_flash_material.albedo_color.a = 0.0

func _physics_process(delta: float) -> void:
	_age += delta
	var previous_x := plane_position.x
	_advance(delta)
	position = GameplayPlane.to_world(plane_position)
	_target.position = plane_position
	# Sortie par le bas OU par le haut : le BOOMERANG s'échappe en remontant, et sans
	# cette seconde borne il resterait vivant à jamais, hors du champ, à consommer une
	# entrée du pool.
	if plane_position.y < GameplayPlane.BOUNDS.position.y - DESPAWN_MARGIN \
			or plane_position.y > GameplayPlane.BOUNDS.end.y + ESCAPE_MARGIN \
			or absf(plane_position.x) > GameplayPlane.BOUNDS.end.x + DESPAWN_MARGIN:
		deactivate()
		return
	# Le roulis se déduit du déplacement latéral RÉELLEMENT parcouru, pas de la
	# dérivée d'une sinusoïde : il vaut donc pour toutes les trajectoires, y compris
	# celles qu'on ajoutera.
	var lateral_speed := (plane_position.x - previous_x) / maxf(delta, 0.0001)
	var bank := clampf(lateral_speed / EnemyPath.BANK_REFERENCE_SPEED, -1.0, 1.0)
	_visual_root.rotation.z = deg_to_rad(-MAX_BANK_DEG) * bank
	_update_hit_flash(delta)
	tick_cover(delta)
	_update_reaction(delta)
	if data.effect == EnemyData.Effect.SHIELD_AURA:
		_project_aura()
		_pulse_aura()
	_update_fire(delta)
	if _pose != null:
		_pose.pose(_pose_ratio())
	if _vitals != null:
		# La cadence du sursis passe à part : elle ne peut pas voyager DANS la menace, dont
		# les signes vitaux dérivent déjà leur propre période.
		_vitals.update(delta, _threat,
			EnemyReaction.arming_beats(_state, _state_time, data))

## Où va la coque cette image. Trois régimes, et un seul par unité.
##
## `PATH` reste ce qu'il a toujours été : une fonction PURE de l'âge, échantillonnée
## et non décidée. C'est ce qui garde le pooling sûr et les tests headless valables
## pour les neuf familles historiques — ajouter un comportement de ce type, c'est
## ajouter une trajectoire dans `EnemyPath` et la choisir dans la Resource, pas
## toucher ici.
func _advance(delta: float) -> void:
	if _is_attached():
		# Accrochée : elle ne se déplace plus, elle est PORTÉE. Le décalage a été
		# figé au contact, donc elle reste posée là où elle a mordu.
		plane_position = _player.plane_position + _attach_offset
		return
	if data.motion == EnemyData.Motion.HOMING:
		# ⚠️ Passé `chase_time` elle cesse de virer, donc elle finit par sortir par un
		# bord. Sans cette rupture, un poursuivant qui rate sa proie tournerait à
		# l'intérieur des bornes indéfiniment et gèlerait son entrée de pool à vie.
		if _age <= data.chase_time:
			_velocity = EnemyHoming.steer(_velocity, plane_position, _player_position(),
				data.homing_turn_rate, delta)
		plane_position += _velocity * delta
		return
	plane_position = EnemyPath.position_at(data, _age, _spawn, _drift_seed)


## Publique : le banc d'essai s'en sert pour corréler la vitesse du chasseur au
## nombre d'unités réellement accrochées. Sans cette corrélation, on ne saurait pas
## distinguer « le frein n'est pas appliqué » de « rien n'est accroché ».
func is_attached() -> bool:
	return _is_attached()


func _is_attached() -> bool:
	return _player != null and data.effect == EnemyData.Effect.LEECH \
		and _state == EnemyReaction.State.ACTIVE


## Position du joueur, ou le point de spawn s'il n'y en a pas (tests, banc d'essai
## sans chasseur). Jamais `ZERO` : une poursuite vers l'origine du plan enverrait
## la coque au centre de l'écran comme si elle y avait un objectif.
func _player_position() -> Vector2:
	return _player.plane_position if _player != null else _spawn


## Local position of an attach point baked into the hull mesh (ADR-0008),
## expressed in VisualRoot space so the hull's own yaw is accounted for.
func _attach_point(point_name: String) -> Vector3:
	if _hull == null:
		return Vector3.ZERO
	var node := _hull.get_node_or_null(NodePath(point_name)) as Node3D
	if node == null:
		push_error("[Enemy:%s] hull has no attach point '%s'" % [data.display_name, point_name])
		return Vector3.ZERO
	return _hull.transform * node.position

## A mesh has no `modulate`, so the impact flash is an additive overlay pass over
## the whole hull rather than a tint on a sprite.
func _build_flash_overlay() -> void:
	var mesh := _find_mesh(_hull)
	if mesh == null:
		return
	_flash_material = StandardMaterial3D.new()
	_flash_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_flash_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_flash_material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_flash_material.albedo_color = Color(1.0, 1.0, 1.0, 0.0)
	mesh.material_overlay = _flash_material

static func _find_mesh(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D:
		return node as MeshInstance3D
	for child in node.get_children():
		var found := _find_mesh(child)
		if found != null:
			return found
	return null

## Light the hull for a beat when it is struck. Without this a hit only registers
## in the audio and the health bar — the hull itself never reacts.
func _update_hit_flash(delta: float) -> void:
	if _flash_material == null or _hit_flash <= 0.0:
		return
	_hit_flash = maxf(_hit_flash - delta, 0.0)
	_flash_material.albedo_color = Color(_flash_tint.r, _flash_tint.g, _flash_tint.b,
		FLASH_STRENGTH * (_hit_flash / HIT_FLASH_TIME))

func _update_fire(delta: float) -> void:
	# Une unité réactive ne tire pas à l'horloge : elle tire quand ON s'approche.
	# Son unique salve part à l'entrée en ACTIVE, dans `_update_reaction`.
	if _reactive or _bullet_manager == null or not GameplayPlane.is_inside(plane_position):
		return
	_fire_timer -= delta
	if _fire_timer <= 0.0:
		_fire_timer = data.fire_interval
		_fire_salvo()

## Une salve, quel que soit son schéma (`EnemyFire`). Zéro allocation : on demande
## les directions une par une plutôt qu'un tableau par tir.
func _fire_salvo() -> void:
	var count := EnemyFire.shot_count(data)
	if _bullet_manager == null or count <= 0:
		return
	# Une couronne part du NOYAU, pas de la bouche : un anneau décentré se lit
	# comme une gerbe et le joueur cherche un angle sûr qui n'existe pas.
	var origin := plane_position if data.fire == EnemyData.Fire.RADIAL \
		else plane_position + _muzzle_offset
	var target := _player.plane_position if _player != null else origin
	for i in count:
		_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, origin,
			EnemyFire.direction(data, _salvo, i, origin, target), data.projectile)
	_salvo += 1
	fired.emit()

## La menace de proximité : le seul endroit du contrôleur qui regarde le joueur.
##
## Tout le reste — trajectoire, roulis, despawn — reste une fonction du seul âge,
## donc reste vrai pour une instance poolée et vérifiable sans arbre de scène.
func _update_reaction(delta: float) -> void:
	if not _reactive:
		return
	_state_time += delta
	var distance := _distance_to_player()
	var next := EnemyReaction.next_state(_state, _state_time, distance, data)
	if next != _state:
		var previous := _state
		_state = next
		_state_time = 0.0
		reaction_changed.emit(_state)
		if _state == EnemyReaction.State.ACTIVE:
			_attach_offset = plane_position - _player_position()
			_fire_salvo()
		elif previous == EnemyReaction.State.ACTIVE:
			_on_discharged()
			# ⚠️ LA SANGSUE SE FAIT SAUTER AU BOUT DE SA MORSURE. Demande de l'opérateur —
			# « elles mordent puis explosent ». Elle s'accroche, freine et draine ; si le
			# joueur ne l'abat pas avant la fin de sa charge, elle détone.
			#
			# Ce que ça ajoute au rôle de l'unité, et pourquoi ce n'est pas redondant avec
			# la mine : la mine PUNIT LE PASSAGE, la sangsue PUNIT L'ATTENTE. L'une se
			# contourne, l'autre se tue — et c'est le joueur qui choisit s'il tire ou s'il
			# fuit, pas la rencontre.
			if data.effect == EnemyData.Effect.LEECH:
				_detonate()
			if _tractor != null:
				_tractor.visible = false
	_threat = EnemyReaction.threat_ratio(_state, _state_time, distance, data)
	if _state != EnemyReaction.State.ACTIVE or _player == null:
		return
	match data.effect:
		EnemyData.Effect.GRAVITY_WELL:
			_pull_player()
			_aim_tractor()
		EnemyData.Effect.LEECH:
			_leech_player(delta)

## Distance au joueur, ou l'infini s'il n'y en a pas (tests, scène de debug).
## L'infini est la bonne réponse : sans joueur, aucune menace ne se déclenche.
func _distance_to_player() -> float:
	if _player == null:
		return INF
	return plane_position.distance_to(_player.plane_position)

## Le champ d'aspiration, tant que la charge dure. La même primitive que la phase
## gravitique du boss (`GravityWell`), mais posée par une unité de vague.
##
## ⚠️ Deux mines ouvertes en même temps ADDITIONNENT leurs champs. C'est pour ça
## que `add_pull` est la seule porte du chasseur : une affectation ferait gagner la
## dernière appelée, et le joueur traverserait tranquillement un nid qui devrait
## l'écraser.
## Combien la coque doit être ouverte, cette image.
##
## Une unité qui DÉCLENCHE s'ouvre au rythme de son télégraphe. Une unité passive —
## le porteur de bouclier — n'a rien à annoncer : ses bras respirent, lentement, et
## c'est ce qui la fait lire comme une machine en fonctionnement plutôt que comme
## une épave qui plane. Ni télégraphe ni état : un signe de vie.
func _pose_ratio() -> float:
	if _reactive:
		var target := EnemyReaction.open_ratio(_state, _state_time, data)
		# ⚠️ LA COQUE NE TÉLÉPORTE PAS. Sans cette limite, sortir du sursis ferait passer
		# l'ouverture de 0,65 à 0 EN UNE IMAGE : la coque claquerait, et un claquement se
		# lit comme un clignotement de bug, pas comme une machine qui se rabat. C'est aussi
		# ce qui rend la refermeture LISIBLE — c'est le mouvement qui dit le pardon.
		_open = move_toward(_open, target, OPEN_RATE * get_physics_process_delta_time())
		return _open
	return 0.5 + 0.5 * sin(_age * TAU / PASSIVE_POSE_PERIOD)


## Les dégâts entrants, avant la santé.
##
## ⚠️ UNE UNITÉ COUVERTE NE PERD RIEN, ET DOIT LE MONTRER. Sans retour visuel, le
## joueur tire dans le vide et croit à un bug de collision : il faut qu'il voie que
## le coup PORTE et qu'il ne compte pas. D'où un éclat de couleur distincte plutôt
## que l'absence de réaction.
func _receive_damage(amount: float) -> void:
	if _shield_grace > 0.0:
		_hit_flash = HIT_FLASH_TIME
		_flash_tint = SHIELD_FLASH_TINT
		return
	_flash_tint = Color.WHITE
	_health.apply_damage(amount)


## Accorde une invulnérabilité, renouvelée à chaque image par le porteur.
## `maxf` et non une affectation : deux porteurs qui se recouvrent ne doivent pas
## se voler la couverture — le plus généreux gagne.
func cover(duration: float) -> void:
	_shield_grace = maxf(_shield_grace, duration)


func is_covered() -> bool:
	return _shield_grace > 0.0


## Consomme une image de couverture. Une méthode plutôt que deux mots dans la boucle
## physique, pour la même raison que `PlayerFighterController.consume_pull()` : la
## règle « la couverture s'éteint si personne ne la repose » devient vérifiable sans
## arbre de scène, donc elle est vérifiée.
func tick_cover(delta: float) -> void:
	_shield_grace = maxf(_shield_grace - delta, 0.0)


## L'aura du porteur de bouclier : elle couvre les VOISINS, jamais lui.
##
## ⚠️ C'est toute la mécanique de l'unité. S'il se couvrait lui-même il serait
## immortel, et la « cible prioritaire » deviendrait une cible impossible. Le joueur
## doit pouvoir l'abattre — c'est même la seule chose qu'il puisse faire.
func _project_aura() -> void:
	if _neighbours.is_empty():
		_resolve_neighbours()
	var reach := data.aura_radius * data.aura_radius
	_link_age += get_physics_process_delta_time()
	var linked := 0
	for other in _neighbours:
		if other.active and other.plane_position.distance_squared_to(plane_position) <= reach:
			other.cover(AURA_GRACE)
			linked = _draw_link(linked, other.plane_position)
	_hide_links_from(linked)


## Préalloue les liens. Leur nombre borne combien d'unités le porteur peut DÉSIGNER à la
## fois — pas combien il en couvre : la couverture, elle, reste sans limite.
##
## ⚠️ Huit suffisent, et c'est mesuré sur la vague : `wave_asteroid_field_01.tres` ne pose
## jamais plus de six unités à portée d'un porteur. Au-delà, l'écran serait un buisson de
## traits et le message — « tue le porteur » — se perdrait dans sa propre insistance.
const LINK_COUNT := 8
## ⚠️ 0,22 ET NON 0,055 — MESURÉ, PAS ESTIMÉ. Le porteur dérive dans le plan de jeu, à
## ~30 px par mètre : à 0,055 m le lien faisait **1,7 pixel**, donc un trait sous le pixel
## qui disparaissait par morceaux à l'anticrénelage. Il était là, il ne se voyait pas — ce
## qui, pour un signe dont le seul rôle est de DÉSIGNER, revient à ne pas exister.
## À 0,22 il pèse ~7 px : fin, mais continu.
const LINK_WIDTH := 0.55

func _build_links() -> void:
	for i in LINK_COUNT:
		var link := FlowLink.build(AURA_TINT, LINK_WIDTH, 2.1)
		link.name = "Link_%02d" % i
		_aura_visual.add_child(link)
		_links.append(link)

## Tend un lien entre le porteur et une unité qu'il couvre, et rend l'indice suivant.
##
## ⚠️ POURQUOI CES LIENS EXISTENT. L'opérateur, en jouant : « le champ de force ne me choque
## pas, mais à part quand je rentre dedans et voir mon vaisseau qui clignote et mes PV qui
## ne diminuent pas, je ne comprends pas ce que ça fait ». Il avait raison de ne pas
## comprendre — le champ ne lui fait RIEN. Il couvre les unités VOISINES, et rien ne le
## disait : un grand cercle lumineux dans lequel on vole PROMET une conséquence, et n'en
## délivrait aucune.
##
## C'est la règle de la bible appliquée à un élément de jeu — rien ne doit ressembler à un
## obstacle s'il n'en est pas un. Le lien dit « tue le PORTEUR » sans un mot, et transforme
## un cercle décoratif en information.
##
## ⚠️ AUCUNE ALLOCATION : les liens sont préalloués au montage, et on ne fait que les
## repositionner. Un lien créé par image couverte allouerait dans la boucle physique.
func _draw_link(index: int, target: Vector2) -> int:
	if index >= _links.size():
		return index
	var link := _links[index]
	var from := GameplayPlane.to_world(plane_position)
	var to := GameplayPlane.to_world(target)
	# ⚠️ LE SENS DU DÉFILEMENT EST L'ESSENTIEL, et c'est pour ça que `to` vient EN PREMIER.
	# Les points remontent du protégé VERS le porteur : « c'est lui qui les tient », donc
	# « tue-le ». L'opérateur avait lu le trait plein dans l'autre sens — « on me ralentit »
	# — et un signe qui enseigne une règle fausse est pire qu'un signe absent.
	FlowLink.aim(link, to, from, _camera_basis(), LINK_WIDTH, _link_age)
	return index + 1

## La base de la caméra active, ou une base valide hors arbre de scène (tests, banc).
func _camera_basis() -> Basis:
	if is_inside_tree():
		var cam := get_viewport().get_camera_3d()
		if cam != null:
			return cam.global_transform.basis
	return Basis.IDENTITY

## Éteint les liens qui n'ont pas servi cette image — sinon un lien resterait tendu vers
## une unité morte, ce qui désignerait une protection qui n'existe plus.
func _hide_links_from(index: int) -> void:
	for i in range(index, _links.size()):
		_links[i].visible = false

## Voisins résolus une fois pour toutes : le pool est préinstancié avant la première
## activation, donc le groupe ne change plus en cours de partie.
func _resolve_neighbours() -> void:
	for node in get_tree().get_nodes_in_group("enemies"):
		var other := node as EnemyController
		if other != null and other != self:
			_neighbours.append(other)


## Ce que fait une sangsue accrochée : elle VOLE de la vitesse, et elle grignote.
##
## ⚠️ La menace réelle est le frein, pas les dégâts. Le drain passe par le même
## bouclier que tout le reste, donc par la même invulnérabilité de 1,2 s après
## impact : un drain « par seconde » est écrêté par elle et ne peut pas vider l'écu
## en continu. C'est elle qui cadence, pas une valeur d'ici — et c'est voulu.
func _leech_player(delta: float) -> void:
	_player.add_drag(data.drag_factor)
	if data.drain_per_second > 0.0:
		_player.take_contact_damage(data.drain_per_second * delta)


func _pull_player() -> void:
	_player.add_pull(GravityWell.pull_at(_player.plane_position, plane_position,
		data.pull_radius, data.pull_speed_max))

## La charge est finie. Une unité à usage unique s'est CONSOMMÉE : elle quitte le
## champ sans émettre `destroyed`, donc sans score ni explosion de mise à mort.
##
## C'est le choix de design qui rend la prudence payante : abattre une mine à
## distance rapporte ses points, la laisser se vider n'en rapporte aucun. Si les
## deux payaient, il n'y aurait plus de décision à prendre.
func _on_discharged() -> void:
	if data.rearm_time <= 0.0:
		deactivate()

## La plume d'échappement, pour que la coque lise comme une chose sous puissance et
## non comme une décalcomanie qui glisse vers le bas de l'écran.
##
## ⚠️ POSÉE SEULEMENT SI LA COQUE A UN MOTEUR. Une mine dérive avec le décor : lui
## allumer une tuyère la ferait lire comme un vaisseau en approche, c'est-à-dire
## comme la seule chose qu'elle n'est pas. Le contrat d'attaches n'est pas perdu
## pour autant — il est tenu à l'EXPORT, par `ak.HullContract.required_attach_points`,
## qui échoue à la construction plutôt qu'en vol.
##
## ⚠️ L'ennemi plonge vers le joueur (+Z monde) : son échappement part donc vers -Z,
## à l'INVERSE de celui du joueur. C'est ce que dit `Vector3.FORWARD` à la fabrique.
func _build_plume() -> void:
	_plume = EnginePlume.make(PLUME_TUNING, 1.0, Vector3.FORWARD)
	_plume.position = _attach_point("Engine_C")
	_plume.snap_throttle(PLUME_THROTTLE)
	add_child(_plume)

## Le rayon tracteur du Null Maw, tendu du joueur VERS le puits.
##
## ⚠️ IL MANQUAIT TOTALEMENT. Relevé par l'opérateur : « les mines attractives et
## immobilisantes, il leur manque du visuel ». Il avait raison — `pull_radius` n'avait
## AUCUN rendu : le puits aspirait le chasseur sans qu'aucun signe ne le dise, et le joueur
## sentait ses commandes lui échapper sans savoir pourquoi. Le même défaut de famille que
## le freinage des sangsues, à un autre endroit.
##
## ⚠️ LE SENS DU DÉFILEMENT DIT LA MÉCANIQUE : les points vont du JOUEUR vers le PUITS,
## donc « tu es tiré là-dedans ». L'inverse aurait dit « il te repousse » — la faute exacte
## qui a fait mal lire le lien du porteur.
func _aim_tractor() -> void:
	if _tractor == null or _player == null:
		return
	var reach := data.pull_radius
	if plane_position.distance_to(_player.plane_position) > reach:
		_tractor.visible = false
		return
	_link_age += get_physics_process_delta_time()
	FlowLink.aim(_tractor, GameplayPlane.to_world(_player.plane_position),
		GameplayPlane.to_world(plane_position), _camera_basis(), TRACTOR_WIDTH, _link_age)

## La détonation de la sangsue, à la fin de sa morsure.
##
## ⚠️ ELLE NE FRAPPE QUE SI LE JOUEUR EST ENCORE LÀ. Une explosion qui touche à travers tout
## l'écran serait une punition qu'on ne peut ni voir venir ni éviter — et le joueur qui vient
## de s'arracher à la morsure a précisément mérité de s'en sortir.
##
## Elle passe par `_on_died()` et non par une destruction directe : c'est ce chemin qui
## prévient la vague, rend le score et joue l'explosion. Une unité qui disparaît par un
## autre chemin laisserait la vague l'attendre indéfiniment.
func _detonate() -> void:
	if _player != null:
		var reach := data.hitbox_radius + DETONATION_REACH
		if plane_position.distance_to(_player.plane_position) <= reach:
			_player.take_contact_damage(data.detonation_damage)
	# ⚠️ `health` ET NON `maximum` — cette propriété N'EXISTE PAS sur `HealthComponent`, et
	# la faute était MUETTE pour la porte de qualité : `check.sh` restait vert, l'erreur ne
	# sortait qu'en jeu, dans un chemin qu'aucun test n'exerçait. Symptôme relevé par
	# l'opérateur : « les sangsues n'explosent pas, une fois collées à moi elles repartent ».
	# Elles ne repartaient pas par choix — l'accès invalide interrompait la fonction AVANT
	# les dégâts, l'unité survivait, passait en épuisée, et son `rearm_time` de 1,5 s la
	# renvoyait dormante. Un test couvre désormais la détonation.
	_health.apply_damage(_health.health + 1.0)

## A non-lethal hit: the killing blow is reported by `destroyed` instead.
func _on_damaged(_amount: float, remaining: float) -> void:
	_hit_flash = HIT_FLASH_TIME
	if remaining > 0.0:
		hit.emit()

func _on_died() -> void:
	deactivate()
	destroyed.emit(self)


# --- Le champ visible --------------------------------------------------------

## Rayons intérieur et extérieur de l'anneau, pour un rayon d'aura donné. Statique et
## pure : c'est ce qui permet de VÉRIFIER que le visuel montre la portée réelle, sans
## monter la moindre scène.
static func aura_ring_radii(aura_radius: float) -> Vector2:
	return Vector2(maxf(aura_radius - AURA_RING_THICKNESS, 0.01),
		aura_radius + AURA_RING_THICKNESS)

## Le champ, monté UNE fois. Rien ne s'alloue ensuite : la respiration ne touche qu'à des
## facteurs de matériau (spec §26.2).
func _build_aura_visual() -> void:
	_aura_visual = Node3D.new()
	_aura_visual.name = "AuraField"

	# L'anneau : la seule chose que le joueur doit vraiment lire. Il est posé dans le plan
	# de jeu, là où sa position a un sens pour l'esquive.
	_aura_edge_material = _aura_material(0.85, 1.6)
	var edge := MeshInstance3D.new()
	edge.name = "Edge"
	# ⚠️ UN PANNEAU PEINT S'IL EXISTE, LE TORE SINON. Le tore rendait un anneau magenta
	# parfait, tracé au compas — « je veux un rendu plus crédible » (opérateur, 2026-08-26).
	# `TEX-0008` lui donne un liseré irrégulier et une trame hexagonale.
	#
	# ⚠️ ET C'EST L'UN DES RARES CAS OÙ UN PANNEAU EST LE BON OUTIL. La règle posée le même
	# jour — « une surface se texture, un VOLUME se peuple » — ne s'applique pas ici : ce
	# champ n'est pas un volume, c'est une FRONTIÈRE. Son bord porte une règle de jeu (les
	# unités couvertes sont invulnérables), et un système de particules le rendrait flou.
	if ResourceLoader.exists(AURA_SPRITE):
		var quad := QuadMesh.new()
		quad.size = Vector2(data.aura_radius * 2.0, data.aura_radius * 2.0)
		quad.orientation = PlaneMesh.FACE_Y   # à plat dans le plan de jeu, comme le tore
		edge.mesh = quad
		_aura_edge_material.albedo_texture = load(AURA_SPRITE) as Texture2D
		_aura_edge_material.albedo_color = Color(1.0, 1.0, 1.0, 0.95)
		_aura_edge_material.emission_texture = _aura_edge_material.albedo_texture
		_aura_edge_material.emission = Color.WHITE
	else:
		var radii := aura_ring_radii(data.aura_radius)
		var ring := TorusMesh.new()
		ring.inner_radius = radii.x
		ring.outer_radius = radii.y
		ring.rings = 40
		ring.ring_segments = 6
		edge.mesh = ring
	edge.material_override = _aura_edge_material
	edge.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_aura_visual.add_child(edge)
	_build_links()

	# ⚠️ IL N'Y A PAS DE DÔME, ET C'EST UNE DÉCISION, PAS UN OUBLI. Trois essais l'ont
	# condamné, tous regardés en capture : additif à 0,09 d'alpha, puis hémisphère à
	# énergie divisée par dix, puis mélange normal SANS émission à 0,11. Les trois ont
	# rendu le même aplat magenta qui recouvrait le porteur, les unités couvertes et les
	# étoiles.
	#
	# La cause n'est pas le réglage, c'est la SURFACE. Deux étages du rendu la reprennent :
	# le bloom du `WorldEnvironment`, qui sature toute surface émissive un peu large, et
	# surtout le `lift` de 1,25 du post-traitement rétro, qui remonte les noirs — un violet
	# à 11 % d'opacité en ressort vif. Une grande surface teintée ne peut pas être discrète
	# dans cette chaîne de rendu.
	#
	# L'anneau, lui, dit exactement ce qu'on avait besoin de dire : OÙ la bulle s'arrête.
	# C'est la seule information dont le joueur ait l'usage, et un cercle fin la porte
	# mieux qu'un volume — sans rien cacher.

	# ⚠️ Enfant du CONTRÔLEUR, pas de `VisualRoot` : celui-ci prend le roulis de la coque,
	# et un champ de force qui s'incline avec le vaisseau qui le porte se lirait comme une
	# pièce de la coque — donc comme quelque chose qu'on peut casser.
	add_child(_aura_visual)

## Additif et non éclairé : un champ est une SOURCE, et l'additif garantit qu'il éclaircit
## toujours ce qu'il recouvre au lieu de l'assombrir — donc qu'il ne peut jamais cacher un
## projectile.
func _aura_material(alpha: float, energy: float) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.albedo_color = Color(AURA_TINT.r, AURA_TINT.g, AURA_TINT.b, alpha)
	# L'additif n'est réservé qu'à ce qui BRILLE — l'anneau. Il garantit qu'une surface
	# lumineuse éclaircit toujours ce qu'elle recouvre au lieu de l'assombrir, donc
	# qu'elle ne peut jamais effacer un projectile. Appliqué à une grande surface, il
	# fait exactement l'inverse : il la remplit.
	if energy > 0.0:
		material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		material.emission_enabled = true
		material.emission = AURA_TINT
		material.emission_energy_multiplier = energy
	return material

## La respiration. Elle ne change RIEN à la portée — seulement l'intensité : un champ dont
## le rayon pulserait mentirait une fois sur deux.
func _pulse_aura() -> void:
	if _aura_edge_material == null:
		return
	var breath := 0.78 + 0.22 * sin(_age * TAU / AURA_PULSE_PERIOD)
	_aura_edge_material.emission_energy_multiplier = 1.6 * breath
