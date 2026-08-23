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

var _bullet_manager: BulletManager
var _target: BulletTarget
## Point de spawn : les trajectoires sont des fonctions de l'âge ET de ce point.
var _spawn: Vector2 = Vector2.ZERO
var _age: float = 0.0
var _fire_timer: float = 0.0
var _hit_flash: float = 0.0
var _plume: EnginePlume
## Additive wash laid over the hull mesh on impact. A mesh has no `modulate`, so
## the flash is an overlay pass rather than a tint.
var _flash_material: StandardMaterial3D
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
## Pièces articulées de la coque, s'il y en a (mines, corolles).
var _pose: EnemyPose

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
	_target = BulletTarget.make(BulletManager.Team.ENEMY, data.hitbox_radius,
		Callable(_health, "apply_damage"))
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

func activate(spawn_plane_position: Vector2) -> void:
	plane_position = spawn_plane_position
	_spawn = spawn_plane_position
	_age = 0.0
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
	_update_reaction(delta)
	_update_fire(delta)
	if _vitals != null:
		_vitals.update(delta, _threat)

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
	plane_position = EnemyPath.position_at(data, _age, _spawn)


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
	_flash_material.albedo_color.a = FLASH_STRENGTH * (_hit_flash / HIT_FLASH_TIME)

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
	_threat = EnemyReaction.threat_ratio(_state, _state_time, distance, data)
	if _pose != null:
		_pose.pose(EnemyReaction.open_ratio(_state, _state_time, data))
	if _state != EnemyReaction.State.ACTIVE or _player == null:
		return
	match data.effect:
		EnemyData.Effect.GRAVITY_WELL:
			_pull_player()
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

## A non-lethal hit: the killing blow is reported by `destroyed` instead.
func _on_damaged(_amount: float, remaining: float) -> void:
	_hit_flash = HIT_FLASH_TIME
	if remaining > 0.0:
		hit.emit()

func _on_died() -> void:
	deactivate()
	destroyed.emit(self)
