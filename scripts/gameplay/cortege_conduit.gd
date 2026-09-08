class_name CortegeConduit
extends Node3D
## Une conduite de l'artère — la cible qui relie le survol à sa propre fin.
##
## ⚠️ ELLE EXISTE PARCE QUE LE SURVOL N'AVAIT AUCUNE CONSÉQUENCE. Raser dix-sept tourelles, sept
## ponts et cinq nœuds, ou traverser en ligne droite : la poupe était exactement la même dans les
## deux cas. Le niveau se jouait en deux moitiés qui ne se parlent pas
## (`docs/plans/2026-09-08-couper-l-artere.md`).
##
## ⚠️ ET SON EFFET N'EST PAS LOCAL, C'EST TOUT LE POINT. La première idée — « couper une conduite
## éteint son tronçon d'artère » — a été écartée : le NŒUD D'ÉPINE fait déjà exactement ça sur son
## tronçon, et c'est la mécanique centrale du corridor. Deux cibles pour un effet de même forme,
## c'est une cible de trop. Ce qu'une conduite coupée retire, c'est de la CHARGE à la poupe.
##
## ⚠️ LA PIÈCE NE DÉCIDE PAS DE CET EFFET, ELLE LE SIGNALE. Elle émet `severed` et rien d'autre :
## qui compte, ce qu'on en fait et quand la charge est figée appartiennent au niveau. Une pièce qui
## irait toucher le réglage de la poupe rendrait la mécanique intestable sans quatre minutes de
## survol.

signal severed(conduit: CortegeConduit)

## Les quatre états, et ils sont ceux des quatre clips livrés.
##
## ⚠️ `SEVERING` EST UNE TRANSITION, PAS UN ÉTAT DE REPOS. Le clip `Rupture` est le geste de la
## coupure ; sa pose finale EST le début de `Rompu`. Les confondre ferait sauter la pièce d'une
## pose à l'autre à l'instant précis où le joueur regarde ce qu'il vient de faire.
enum State { ACTIVE, DAMAGED, SEVERING, SEVERED }

const KIT := "res://assets/imported/models/backgrounds/artery_conduit.glb"
const KIT_BEND := "res://assets/imported/models/backgrounds/artery_conduit_bend.glb"
## Le flexible : ⚠️ DÉCOR, PAS CIBLE. Il habille la liaison et se rompt avec elle. Lui donner une
## hitbox doublerait le nombre de choses à viser pour un seul effet — et c'est exactement ce
## qu'on a refusé en écartant l'effet local.
const HOSE := "res://assets/imported/models/backgrounds/artery_hose.glb"

## Le repère de l'auteur où naît la fuite.
const LEAK_SOCKET := "CTRL | VFX fuite principale"

const TINT := Color("d93d9c")
## La lueur de l'artère selon l'état. ⚠️ ELLE MONTE AVANT DE S'ÉTEINDRE : une conduite entamée
## fuit, donc elle brille PLUS. Baisser dès le premier coup se lirait comme une pièce qui s'éteint
## proprement — c'est-à-dire comme rien.
const GLOW_ACTIVE := 2.20
const GLOW_DAMAGED := 4.60
const GLOW_SEVERED := 0.04
const DAMAGED_PULSE_HZ := 4.2
const DAMAGED_PULSE_DEPTH := 0.38
const HIT_FLASH_TIME := 0.10
const HIT_FLASH_GAIN := 2.4

var score: int = 0
var serial: int = 0
var section: int = 0
## Sous cette part de vie, la conduite fuit.
var damaged_at: float = 0.50
## Entre deux gerbes d'une conduite qui fuit.
var leak_interval: float = 0.70
## Ce que dure le geste de rupture avant la pose de repos.
var sever_time: float = 0.80

var _health: float = 0.0
var _health_max: float = 0.0
var _alive: bool = true
var _target: BulletTarget = null
var _bullets: BulletManager = null
var _vfx: VFXManager = null
var _world: Vector3 = Vector3.ZERO
var _leak: Vector3 = Vector3.ZERO
var _glows: Array[StandardMaterial3D] = []
var _anim: AnimationPlayer = null
var _hose_anim: AnimationPlayer = null
var _clip: String = ""
var _registered: bool = false
var _state: State = State.ACTIVE
var _pulse: float = 0.0
var _flash: float = 0.0
var _leak_clock: float = 0.0
var _sever_clock: float = 0.0

static func make(health: float, radius: float, p_score: int) -> CortegeConduit:
	var conduit := CortegeConduit.new()
	conduit.score = p_score
	conduit._health = health
	conduit._health_max = health
	# La cible naît avec la pièce — même contrat que la tourelle, le nœud et l'ancrage : il n'y a
	# qu'une porte pour les dégâts, et les tests passent par elle.
	conduit._target = BulletTarget.make(BulletManager.Team.ENEMY, radius, conduit._take_damage)
	conduit._target.enabled = false
	return conduit

func setup(bullets: BulletManager, vfx: VFXManager) -> void:
	_bullets = bullets
	_vfx = vfx

# --- La règle, pure et testable sans arbre -------------------------------------

## L'état de repos d'une conduite, déduit de sa vie et de rien d'autre.
##
## ⚠️ ELLE NE REND JAMAIS `SEVERING`. La rupture est un instant, pas une lecture de santé : elle
## se déclenche au passage à zéro et s'écoule sur une horloge. Une fonction d'état qui la rendrait
## la ferait rejouer à chaque image de la trame où la vie vaut zéro.
static func state_for(alive: bool, ratio: float, seuil: float) -> State:
	if not alive:
		return State.SEVERED
	return State.DAMAGED if ratio <= seuil else State.ACTIVE

## Le nom du clip d'un état. ⚠️ LES QUATRE SONT UTILISÉS : livrer quatre animations et n'en jouer
## que deux, c'est payer une pièce animée pour un décor.
static func clip_of(state: State) -> String:
	match state:
		State.DAMAGED: return "Endommage"
		State.SEVERING: return "Rupture"
		State.SEVERED: return "Rompu"
	return "Actif"

func health_ratio() -> float:
	return 0.0 if _health_max <= 0.0 else clampf(_health / _health_max, 0.0, 1.0)

func is_alive() -> bool:
	return _alive

func state() -> State:
	return _state

func target() -> BulletTarget:
	return _target

# --- La pièce ------------------------------------------------------------------

## Monte la conduite et son flexible. `bend` prend la pièce coudée.
func build(bend: bool = false) -> void:
	var packed: PackedScene = load(KIT_BEND if bend else KIT) as PackedScene
	if packed == null:
		return
	var piece := packed.instantiate() as Node3D
	if piece == null:
		return
	piece.name = "Conduit"
	add_child(piece)
	_claim_glow(piece)
	_anim = _player_of(piece)
	_leak = _socket_of(piece, LEAK_SOCKET)
	_mount_hose()
	_apply_state()

## ⚠️ LE FLEXIBLE EST UN FRÈRE, PAS UN ENFANT DE LA CONDUITE. Il a ses propres clips et sa propre
## `AnimationPlayer` : parenté sous la conduite, sa piste serait écrasée par celle de l'hôte au
## premier `play()` — les deux joueurs ne se voient pas, mais leurs pistes visent les mêmes noms.
func _mount_hose() -> void:
	var packed: PackedScene = load(HOSE) as PackedScene
	if packed == null:
		return
	var brin := packed.instantiate() as Node3D
	if brin == null:
		return
	brin.name = "Hose"
	add_child(brin)
	_claim_glow(brin)
	_hose_anim = _player_of(brin)

## ⚠️ CHAQUE CONDUITE SA COPIE. Dix conduites sont dix instances du MÊME `.glb` : elles partagent
## leurs matériaux, et en éteindre une les éteindrait toutes. Piège déjà payé sur les deux relais
## de la Citadelle, les cinq bulbes d'épine et les dix verrous de poupe.
func _claim_glow(root: Node) -> void:
	for node in _descendants(root):
		var mesh := node as MeshInstance3D
		if mesh == null or mesh.mesh == null:
			continue
		for i in mesh.mesh.get_surface_count():
			var base := mesh.mesh.surface_get_material(i) as StandardMaterial3D
			if base == null:
				continue
			if not base.emission_enabled:
				mesh.set_surface_override_material(i, CortegeSkin.tamed(base))
				continue
			var mine: StandardMaterial3D = base.duplicate()
			mesh.set_surface_override_material(i, mine)
			_glows.append(mine)

static func _player_of(root: Node) -> AnimationPlayer:
	for node in _descendants(root):
		var player := node as AnimationPlayer
		if player != null:
			return player
	return null

## La position d'un repère de l'auteur, en local. Zéro s'il manque.
static func _socket_of(root: Node, nom: String) -> Vector3:
	for node in _descendants(root):
		var n3 := node as Node3D
		if n3 != null and String(node.name) == nom:
			return n3.position
	return Vector3.ZERO

static func _descendants(node: Node, out: Array[Node] = []) -> Array[Node]:
	for child in node.get_children():
		out.append(child)
		_descendants(child, out)
	return out

## Ouvre la conduite aux dégâts. ⚠️ APPELÉ PAR LE NIVEAU quand elle entre dans la fenêtre, comme
## toute pièce de coque : une cible inscrite en permanence encaisserait à cinq cents mètres.
func engage(on: bool) -> void:
	if _target == null or _bullets == null:
		return
	if on and not _registered and _alive:
		_bullets.register_target(_target)
		_target.enabled = true
		_registered = true
	elif not on and _registered:
		_target.enabled = false
		_registered = false

## Un pas. `world` est la position de la pièce, `here` son point de visée dans le plan.
func tick(delta: float, world: Vector3, here: Vector2) -> void:
	_world = world
	if _target != null:
		_target.position = here
	if _flash > 0.0:
		_flash = maxf(_flash - delta, 0.0)
	if _state == State.SEVERING:
		_sever_clock -= delta
		if _sever_clock <= 0.0:
			_state = State.SEVERED
			_apply_state()
	elif _state == State.DAMAGED:
		_pulse = fmod(_pulse + delta * DAMAGED_PULSE_HZ, TAU)
		# ⚠️ LA FUITE EST LE SEUL SIGNAL QUI PORTE À DISTANCE. Le battement se voit quand on
		# regarde la pièce ; la gerbe se voit du coin de l'œil, et c'est elle qui ramène le joueur
		# sur une conduite qu'il a laissée à moitié.
		_leak_clock -= delta
		if _leak_clock <= 0.0 and _vfx != null:
			_leak_clock = leak_interval
			_vfx.spawn_explosion(_world + _leak, VfxExplosion.Category.IMPACT, TINT)
	_apply_glow()

func _take_damage(damage: float) -> void:
	if not _alive:
		return
	_health -= damage
	_flash = HIT_FLASH_TIME
	if _health > 0.0:
		var avant := _state
		_state = state_for(true, health_ratio(), damaged_at)
		if _state != avant:
			_pulse = 0.0
			_leak_clock = 0.0
			_apply_state()
		return
	_alive = false
	engage(false)
	# ⚠️ LA RUPTURE SE JOUE, PUIS LA CARCASSE RESTE. Une conduite qui disparaîtrait laisserait le
	# joueur compter ce qui manque au lieu de voir ce qu'il a fait — même règle que le berceau
	# vide, le cœur de nœud et le verrou rompu.
	_state = State.SEVERING
	_sever_clock = sever_time
	_apply_state()
	if _vfx != null:
		_vfx.spawn_explosion(_world + _leak, VfxExplosion.Category.MEDIUM, TINT)
	severed.emit(self)

func _apply_state() -> void:
	_play_clip()
	_apply_glow()

func _apply_glow() -> void:
	var energie := GLOW_ACTIVE
	match _state:
		State.DAMAGED:
			energie = GLOW_DAMAGED * (1.0 + DAMAGED_PULSE_DEPTH * sin(_pulse))
		State.SEVERING:
			energie = GLOW_DAMAGED
		State.SEVERED:
			energie = GLOW_SEVERED
	if _flash > 0.0:
		energie += HIT_FLASH_GAIN * (_flash / HIT_FLASH_TIME)
	for mat in _glows:
		mat.emission_energy_multiplier = energie

## ⚠️ LES DEUX JOUEURS AVANCENT ENSEMBLE. Le flexible porte les mêmes quatre clips, à un nom près
## (`Intact` au lieu d'`Actif`) : le laisser sur sa pose de départ pendant que la conduite se rompt
## donnerait une gaine intacte sur un tuyau arraché.
func _play_clip() -> void:
	var voulu := clip_of(_state)
	if voulu == _clip:
		return
	_clip = voulu
	if _anim != null and _anim.has_animation(voulu):
		_anim.play(voulu)
	if _hose_anim == null:
		return
	var pour_le_brin := "Intact" if voulu == "Actif" else voulu
	if _hose_anim.has_animation(pour_le_brin):
		_hose_anim.play(pour_le_brin)
