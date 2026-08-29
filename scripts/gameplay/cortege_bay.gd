class_name CortegeBay
extends Node3D
## Un pont d'envol du Long Cortège : tant qu'il vit, il produit.
##
## ⚠️ IL COÛTE CHER À FAIRE TOMBER, C'EST SA RAISON D'ÊTRE. Un pont laissé debout lâche des
## coques en continu ; l'abattre est une DÉCISION, pas un réflexe. Mais le prix a une borne, et
## c'est l'invariant 2 de `CortegeTuning` qui la tient : au-dessus de ce qu'une fenêtre de survol
## permet de placer, le pont est indestructible EN PRATIQUE et le joueur croira mal jouer.
##
## ⚠️ `WaveSpawner` NE SAIT PAS ANCRER UN LÂCHER À UN OBJET QUI BOUGE, et c'est pour ça que ce
## fichier existe. Ses positions d'apparition sont figées dans un `PackedVector2Array` au
## `_ready()` : elles décrivent un ciel, pas une coque qui défile. Le point d'entrée qui existe
## déjà, lui, accepte n'importe quelle position — `EnemyController.activate(position, seed)`. Le
## pont pilote donc son propre pool et appelle `activate()` à SA position du moment. Aucune
## modification de `WaveSpawner`, donc aucune régression possible sur le niveau 1.
##
## ⚠️ ET LES COQUES LÂCHÉES NE SONT PAS SES ENFANTS. Le pont est enfant d'un marqueur qui défile ;
## un `EnemyController` pose sa coque avec `position = GameplayPlane.to_world(plane_position)`,
## c'est-à-dire en LOCAL. Une coque parentée au pont serait donc décalée de tout ce que le décor
## a parcouru, et dériverait un peu plus à chaque seconde. Elles vivent sous un nœud immobile,
## fourni par le gestionnaire.

enum Pass { AHEAD, LIVE, PASSED }

## Ce qui sort d'un pont. ⚠️ CE SONT LES COQUES DU BESTIAIRE EXISTANT, sur demande explicite de
## l'opérateur : le niveau 2 ne présente pas d'ennemis neufs, il montre d'où venaient ceux du
## niveau 1. Le plongeur descend droit sur la coque, l'intercepteur coupe en travers — deux
## lectures différentes du même pont, ce qui suffit à ce qu'un lâcher ne se joue pas toujours
## pareil.
const RELEASE_SCENES: Array[String] = [
	"res://scenes/enemies/needle_scout_diver.tscn",
	"res://scenes/enemies/crescent_interceptor.tscn",
]

## Le fond du puits : le volume émissif qui dit si le pont produit encore.
##
## ⚠️ IL RECOUVRE LE FOND DE LA FORGE, IL NE S'AJOUTE PAS À CÔTÉ. La coque livrée porte déjà un
## cœur émissif magenta au fond de chaque puits — mais il est CUIT dans le maillage du tronçon et
## partage son matériau avec les six autres baies : éteindre un pont abattu en touchant à la
## coque éteindrait les sept. Le fond de la forge est donc masqué par celui-ci, qui lui appartient
## en propre. Une première version posait un carré rose PAR-DESSUS l'hexagone sans le couvrir :
## on voyait les deux, et ça ne ressemblait à rien. Vu en capture, pas déduit.
##
## Cotes prises sur `build_long_cortege.py` : le cœur émissif est un hexagone allongé de ±1,95 en
## X et ±2,11 en Z, posé à −4,20. Un hexagone régulier de rayon 2,4 tourné d'un quart de tour
## couvre les deux (2,08 de plat en X, 2,40 de pointe en Z) avec quatre centimètres de marge
## au-dessus du fond — assez pour qu'aucun conflit de profondeur ne scintille au défilement.
const WELL_RADIUS := 2.4
const WELL_THICKNESS := 0.06
const WELL_DEPTH := -0.71
const HATCH_TINT := Color("d93d9c")

signal destroyed(bay: CortegeBay)
signal released(enemy: EnemyController)

var tuning: CortegeTuning
var section: int = 0

var _bullet_manager: BulletManager
var _vfx: VFXManager
var _target: BulletTarget
var _pool: Array[EnemyController] = []
var _next: int = 0
var _hatch: MeshInstance3D
var _hatch_material: StandardMaterial3D

var _pass: Pass = Pass.AHEAD
var _timer: float = 0.0
var _health: float = 0.0
var _alive: bool = true
var _world: Vector3 = Vector3.ZERO

static func make(p_tuning: CortegeTuning, p_section: int) -> CortegeBay:
	var bay := CortegeBay.new()
	bay.tuning = p_tuning
	bay.section = p_section
	bay._health = p_tuning.bay_health
	bay._timer = p_tuning.bay_release_interval
	# La cible nait avec la piece — meme raison que pour la tourelle.
	bay._target = BulletTarget.make(BulletManager.Team.ENEMY, 1.9, bay._take_damage)
	bay._target.enabled = false
	return bay

## ⚠️ TOUT LE POOL EST ALLOUÉ ICI, au montage du niveau, et plus jamais ensuite (spec §26.1).
## Sa taille couvre le pire cas — un pont qui vit jusqu'au bout de sa fenêtre — et c'est
## `CortegeTuning.validate()` qui le vérifie, pas une supposition écrite ici.
func build(bullet_manager: BulletManager, player: PlayerFighterController, vfx: VFXManager,
		release_parent: Node) -> void:
	_bullet_manager = bullet_manager
	_vfx = vfx
	for i in tuning.bay_pool_size:
		var path: String = RELEASE_SCENES[i % RELEASE_SCENES.size()]
		var packed: PackedScene = load(path) as PackedScene
		if packed == null:
			continue
		var enemy := packed.instantiate() as EnemyController
		if enemy == null:
			continue
		release_parent.add_child(enemy)
		enemy.setup(bullet_manager, player)
		_pool.append(enemy)

func is_alive() -> bool:
	return _alive

func has_passed() -> bool:
	return _pass == Pass.PASSED

func pool() -> Array[EnemyController]:
	return _pool

## La cible que le gestionnaire de balles connait. ⚠️ EXPOSEE PARCE QUE C'EST LE VRAI CHEMIN DES
## DEGATS : un test qui appellerait une methode ecrite pour lui ne verifierait pas le chemin que
## le jeu emprunte. Ici il n'y a qu'une porte, et tout le monde passe par elle.
func target() -> BulletTarget:
	return _target

## Dans sa fenetre, ni encore devant ni deja derriere.
func is_engaged() -> bool:
	return _pass == Pass.LIVE

func _ready() -> void:
	_hatch_material = StandardMaterial3D.new()
	_hatch_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_hatch_material.albedo_color = HATCH_TINT
	_hatch_material.emission_enabled = true
	_hatch_material.emission = HATCH_TINT
	_hatch_material.emission_energy_multiplier = 1.4
	var mesh := CylinderMesh.new()
	mesh.top_radius = WELL_RADIUS
	mesh.bottom_radius = WELL_RADIUS
	mesh.height = WELL_THICKNESS
	# Six pans, comme le puits. Le défaut par défaut en compterait soixante-quatre, sept fois
	# dans le niveau, pour un couvercle qu'on regarde toujours de face.
	mesh.radial_segments = 6
	mesh.rings = 0
	_hatch = MeshInstance3D.new()
	_hatch.name = "Well"
	_hatch.mesh = mesh
	_hatch.material_override = _hatch_material
	_hatch.position.y = WELL_DEPTH
	# ⚠️ Le quart de tour n'est pas un détail : sans lui l'hexagone pose ses pointes en X et ses
	# plats en Z, exactement l'inverse du puits, et deux coins du fond de la forge dépassent.
	_hatch.rotation.y = PI * 0.5
	_hatch.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_hatch)

## Un pas de la pièce. ⚠️ SA POSITION LUI EST DONNÉE, ELLE NE LA LIT PAS DANS L'ARBRE. Elle est
## pourtant enfant d'un marqueur qui défile, et `global_position` répondrait — mais seulement
## DANS un arbre monté. La passer en paramètre rend la pièce pilotable sans scène, donc
## vérifiable : c'est exactement ce qui a rendu `LeviathanCombat` testable là où trois cycles
## demandent quarante secondes de jeu. Le gestionnaire, lui, sait lire l'arbre.
func tick(delta: float, world: Vector3) -> void:
	if _pass == Pass.PASSED:
		return
	_world = world
	var here := GameplayPlane.to_plane(world)
	var half := tuning.bay_visible_span * 0.5
	match _pass:
		Pass.AHEAD:
			if here.y <= half:
				_pass = Pass.LIVE
				if _alive and _bullet_manager != null:
					_bullet_manager.register_target(_target)
					_target.enabled = true
		Pass.LIVE:
			if here.y < -half:
				_retire()
				return
	if _target != null:
		_target.position = here
	if not _alive or _pass != Pass.LIVE:
		return
	# ⚠️ IL NE LÂCHE QUE QUAND IL EST AU-DESSUS DU TERRAIN. Sa fenêtre de TIR déborde le plan de
	# vol — la caméra voit loin devant —, mais une coque née au-delà de la borne haute est
	# détruite à sa première trame par le despawn de `EnemyController` : le pont paraîtrait
	# lâcher dans le vide.
	if here.y > GameplayPlane.bounds.end.y:
		return
	_timer -= delta
	if _timer > 0.0:
		return
	_timer = tuning.bay_release_interval
	_release(here)

func _release(here: Vector2) -> void:
	var launched := 0
	for i in _pool.size():
		if launched >= tuning.bay_release_count:
			break
		var enemy := _pool[_next]
		_next = (_next + 1) % _pool.size()
		if enemy.active:
			continue
		# Les coques sortent l'une à côté de l'autre, pas l'une DANS l'autre : la loi de
		# séparation des vagues n'existe pas ici, et deux unités au même point resteraient
		# empilées tout le temps de leur trajectoire.
		var spread := Vector2(1.1 * (float(launched) - float(tuning.bay_release_count - 1) * 0.5), 0.0)
		enemy.activate(here + spread, randf() * TAU)
		launched += 1
		released.emit(enemy)
	if launched > 0:
		_pulse_hatch()

func _pulse_hatch() -> void:
	if _hatch_material != null:
		_hatch_material.emission_energy_multiplier = 3.4

func _take_damage(damage: float) -> void:
	if not _alive:
		return
	_health -= damage
	if _hatch_material != null:
		# L'écoutille pâlit avec ce qui lui reste : le joueur doit voir qu'il PROGRESSE, sinon
		# mille cinq cents points de vie se lisent comme une cible indestructible.
		_hatch_material.emission_energy_multiplier = 0.4 + 1.6 * clampf(_health / tuning.bay_health, 0.0, 1.0)
	if _health > 0.0:
		return
	_alive = false
	if _hatch_material != null:
		_hatch_material.emission_energy_multiplier = 0.0
		_hatch_material.albedo_color = Color(0.07, 0.03, 0.06)
	if _vfx != null:
		_vfx.spawn_explosion(_world, VfxExplosion.Category.HEAVY)
	_retire()
	destroyed.emit(self)

func _retire() -> void:
	_pass = Pass.PASSED
	if _target != null:
		_target.enabled = false
		if _bullet_manager != null:
			_bullet_manager.unregister_target(_target)

# --- Fonction pure, testable sans arbre de scène ------------------------------

## Combien de fois ce pont lâchera pendant qu'il survole le terrain. ⚠️ C'est CE nombre, et non
## la fenêtre de tir, qui dit la pression qu'il exerce : la fenêtre de tir déborde le plan de vol.
static func releases_over(span: float, speed: float, interval: float) -> int:
	if speed <= 0.001 or interval <= 0.001:
		return 0
	return int(span / speed / interval)
