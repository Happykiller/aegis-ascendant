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

# --- Le décollage -------------------------------------------------------------
#
## ⚠️ LES COQUES APPARAISSAIENT PAR MAGIE, ET C'EST TOUT CE QUE LE JOUEUR EN VOYAIT :
## « aucune animation de pont d'envol, les ennemis apparaissent par magie » (opérateur, en
## jouant le 2026-08-29). Un pont qu'on abat pour tarir sa production doit d'abord se lire
## COMME une production — sinon abattre le pont ne se relie à rien.
##
## Ce qui manquait n'est pas un effet, c'est une CAUSE VISIBLE : quelque chose qui monte du
## puits, franchit la bouche, et part. Le joueur voit alors d'où ça vient, une seconde avant
## que ça ne le concerne.
##
## ⚠️ ET C'EST UN VOLUME À NOUS, PAS LA COQUE POOLÉE. `EnemyController` pose sa position en
## coordonnées du PLAN de jeu, à hauteur nulle : il ne sait pas monter d'un puits creusé trois
## mètres et demi plus bas. Le faire descendre pour l'occasion aurait demandé un état de plus
## dans la classe la plus chaude du jeu, pour une animation qui ne dure pas une seconde. La
## silhouette qui monte est donc décorative ; la vraie coque s'active à l'instant où elle
## atteint la bouche, exactement là où elle était.
const LAUNCH_TIME := 0.85
## La silhouette part du fond du puits et sort par la bouche, en avançant vers le joueur.
const LAUNCH_FROM := Vector3(0.0, -0.66, 0.0)
const LAUNCH_TO := Vector3(0.0, 0.35, 1.9)
## ⚠️ SOMBRE SUR FOND CLAIR, ET C'EST L'INVERSE DE MON PREMIER ESSAI. Une silhouette pâle et
## légèrement émissive se noyait dans le magenta du puits — vu en capture : on devinait deux
## formes, on ne lisait pas un décollage. Le fond de la baie est ce qu'il y a de plus lumineux
## sur toute la coque ; ce qui s'en détache est ce qui est SOMBRE.
const RISER_LENGTH := 1.55
const RISER_WIDTH := 0.86

# --- Les portes ----------------------------------------------------------------
#
## ⚠️ IL MANQUAIT LA PORTE, ET C'EST CE QUI FAISAIT « DES FORMES CARRÉES ». La première version
## montrait une nappe magenta permanente et deux silhouettes qui en sortaient : un pont d'envol
## toujours ouvert n'est pas un pont d'envol, c'est un trou. « Les ponts d'envol ne sont pas
## animés, c'est moche, on dirait des jeux faits avec des formes carrées » (opérateur,
## 2026-08-29) — et le mot juste est *animés* : ce qui manque n'est pas de la géométrie, c'est
## un ÉTAT qui change.
##
## Deux battants se retirent sur les côtés, la lueur du puits apparaît, les coques montent, les
## battants se referment. Le puits ne brille donc que quand il produit — et un pont abattu reste
## FERMÉ, ce qui se lit sans un mot.
const DOOR_TIME := 0.4
const DOOR_SLIDE := 2.05
const DOOR_TINT := Color(0.15, 0.13, 0.17)

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

## Les décollages en cours. ⚠️ UN TABLEAU PRÉALLOUÉ ET NON UNE FILE QUI GRANDIT : deux coques
## par lâcher, et le lâcher suivant ne peut pas commencer avant la fin de celui-ci (l'intervalle
## est plus long que l'animation). Rien ne s'alloue pendant la partie (spec §26.1).
var _risers: Array[MeshInstance3D] = []
var _riser_age: PackedFloat32Array = PackedFloat32Array()
var _riser_enemy: Array[EnemyController] = []

## Les deux battants, et leur ouverture — 0 fermé, 1 ouvert.
var _doors: Array[MeshInstance3D] = []
var _door_open: float = 0.0
## La porte reste ouverte tant qu'un décollage est en cours, plus un souffle.
var _door_hold: float = 0.0

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
	# dans le niveau, pour un fond qu'on regarde toujours de face.
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
	_build_doors()
	_build_risers()

## Les deux battants qui ferment le puits. ⚠️ ILS SONT AU NIVEAU DE LA BOUCHE, pas au fond :
## fermés, ils cachent la lueur ; ouverts, ils la découvrent. C'est ce contraste — noir puis
## magenta — qui fait lire l'ouverture, bien plus que le mouvement lui-même.
func _build_doors() -> void:
	var plate := StandardMaterial3D.new()
	plate.albedo_color = DOOR_TINT
	plate.metallic = 0.65
	plate.roughness = 0.4
	for side in [-1.0, 1.0]:
		var door := MeshInstance3D.new()
		door.name = "Door%s" % ("L" if side < 0.0 else "R")
		var slab := BoxMesh.new()
		slab.size = Vector3(WELL_RADIUS * 1.02, 0.12, WELL_RADIUS * 2.05)
		door.mesh = slab
		door.material_override = plate
		door.position = Vector3(side * WELL_RADIUS * 0.51, WELL_DEPTH + 0.5, 0.0)
		door.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(door)
		_doors.append(door)

## Les silhouettes qui montent du puits. Une par coque d'un lâcher, montées au démarrage et
## réutilisées — comme tout le reste.
func _build_risers() -> void:
	var skin := StandardMaterial3D.new()
	skin.albedo_color = Color(0.09, 0.08, 0.11)
	skin.metallic = 0.6
	skin.roughness = 0.38
	var burn := StandardMaterial3D.new()
	burn.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	burn.albedo_color = Color(1.0, 0.55, 0.30)
	burn.emission_enabled = true
	burn.emission = Color(1.0, 0.55, 0.30)
	burn.emission_energy_multiplier = 2.2
	for i in maxi(tuning.bay_release_count, 1):
		var riser := MeshInstance3D.new()
		riser.name = "Riser%d" % i
		# ⚠️ UNE COQUE, PAS UN PRISME. Un prisme se lit comme une flèche de menu ; ce qui doit
		# sortir d'un pont d'envol, c'est un vaisseau. Trois boîtes suffisent à cette taille —
		# un fuselage et deux ailes en flèche — et c'est la SILHOUETTE qui porte la lecture,
		# pas le détail, dont rien ne survit à 23 px/m.
		var body := BoxMesh.new()
		body.size = Vector3(RISER_WIDTH * 0.34, 0.16, RISER_LENGTH)
		riser.mesh = body
		riser.material_override = skin
		riser.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		for side in [-1.0, 1.0]:
			var wing := MeshInstance3D.new()
			var pane := BoxMesh.new()
			pane.size = Vector3(RISER_WIDTH * 0.46, 0.09, RISER_LENGTH * 0.42)
			wing.mesh = pane
			wing.material_override = skin
			wing.position = Vector3(side * RISER_WIDTH * 0.38, -0.02, RISER_LENGTH * 0.18)
			wing.rotation.y = side * 0.22
			wing.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			riser.add_child(wing)
		# La lueur de propulsion, à l'ARRIÈRE : c'est elle qui dit que la chose décolle au lieu
		# d'être posée sur un monte-charge.
		var flame := MeshInstance3D.new()
		var jet := BoxMesh.new()
		jet.size = Vector3(RISER_WIDTH * 0.22, 0.1, 0.26)
		flame.mesh = jet
		flame.material_override = burn
		flame.position.z = RISER_LENGTH * 0.5
		flame.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		riser.add_child(flame)
		riser.visible = false
		add_child(riser)
		_risers.append(riser)
		_riser_age.append(-1.0)
		_riser_enemy.append(null)


## Un pas de la pièce. ⚠️ SA POSITION LUI EST DONNÉE, ELLE NE LA LIT PAS DANS L'ARBRE. Elle est
## pourtant enfant d'un marqueur qui défile, et `global_position` répondrait — mais seulement
## DANS un arbre monté. La passer en paramètre rend la pièce pilotable sans scène, donc
## vérifiable : c'est exactement ce qui a rendu `LeviathanCombat` testable là où trois cycles
## demandent quarante secondes de jeu. Le gestionnaire, lui, sait lire l'arbre.
func tick(delta: float, world: Vector3, here: Vector2) -> void:
	if _pass == Pass.PASSED:
		return
	_world = world
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
	_advance_doors(delta)
	_advance_risers(delta, here)
	_timer -= delta
	if _timer > 0.0:
		return
	_timer = tuning.bay_release_interval
	_release(here)

## Ouvre la porte : les silhouettes commencent à monter. ⚠️ LA COQUE N'EST PAS ENCORE EN JEU —
## elle est réservée maintenant et activée à la fin de la montée, pour que le joueur ait vu d'où
## elle vient avant qu'elle ne le concerne.
func _release(_here: Vector2) -> void:
	var launched := 0
	for slot in _risers.size():
		if launched >= tuning.bay_release_count:
			break
		if _riser_age[slot] >= 0.0:
			continue          # cette place décolle déjà
		var enemy := _take_from_pool()
		if enemy == null:
			break
		_riser_enemy[slot] = enemy
		_riser_age[slot] = 0.0
		_risers[slot].visible = true
		launched += 1
	if launched > 0:
		# ⚠️ LA PORTE S'OUVRE AVANT QUE LA COQUE NE MONTE : c'est l'ordre qui rend la séquence
		# lisible. Ouvrir pendant la montée donnerait un vaisseau qui traverse un battant.
		_door_hold = DOOR_TIME + LAUNCH_TIME + DOOR_TIME
		_pulse_hatch()

func _take_from_pool() -> EnemyController:
	for i in _pool.size():
		var enemy := _pool[_next]
		_next = (_next + 1) % _pool.size()
		if not enemy.active and not _riser_enemy.has(enemy):
			return enemy
	return null

## Fait monter les silhouettes, et met la vraie coque en jeu à l'arrivée.
func _advance_risers(delta: float, here: Vector2) -> void:
	# ⚠️ RIEN NE MONTE TANT QUE LA PORTE N'EST PAS OUVERTE. Sans ce verrou, la coque traverse le
	# battant pendant qu'il coulisse — et une séquence qui se chevauche ne se lit pas comme une
	# séquence, elle se lit comme un défaut.
	if _door_open < 0.85:
		return
	for slot in _risers.size():
		if _riser_age[slot] < 0.0:
			continue
		_riser_age[slot] += delta
		var t := clampf(_riser_age[slot] / LAUNCH_TIME, 0.0, 1.0)
		# ⚠️ ELLE ACCÉLÈRE. Une montée linéaire se lit comme un ascenseur ; un décollage
		# commence lentement et part — c'est la seule chose qui distingue les deux.
		var eased := t * t
		var spread := 1.1 * (float(slot) - float(_risers.size() - 1) * 0.5)
		_risers[slot].position = LAUNCH_FROM.lerp(LAUNCH_TO, eased) + Vector3(spread, 0.0, 0.0)
		if t < 1.0:
			continue
		_risers[slot].visible = false
		_riser_age[slot] = -1.0
		var enemy: EnemyController = _riser_enemy[slot]
		_riser_enemy[slot] = null
		if enemy == null:
			continue
		# ⚠️ LA COQUE NAÎT LÀ OÙ LA SILHOUETTE EST ARRIVÉE, pas au centre du puits : sinon elle
		# ferait un saut en arrière au moment précis où le joueur la regarde.
		var mouth := here + Vector2(spread, -LAUNCH_TO.z)
		enemy.activate(mouth, randf() * TAU)
		released.emit(enemy)

## Fait coulisser les battants. ⚠️ LE FOND N'EST VISIBLE QUE QUAND ILS SONT OUVERTS : la lueur
## du puits est masquée à la fermeture, ce qui fait qu'un pont au repos — ou abattu — est un
## rectangle sombre sur la coque, et non une nappe magenta permanente.
func _advance_doors(delta: float) -> void:
	_door_hold = maxf(_door_hold - delta, 0.0)
	var wanted := 1.0 if _door_hold > 0.0 else 0.0
	_door_open = move_toward(_door_open, wanted, delta / DOOR_TIME)
	for i in _doors.size():
		var side := -1.0 if i == 0 else 1.0
		_doors[i].position.x = side * (WELL_RADIUS * 0.51 + DOOR_SLIDE * _door_open)
	if _hatch != null:
		_hatch.visible = _door_open > 0.02

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
	# ⚠️ CE QUI DÉCOLLAIT MEURT AVEC LE PONT. Une silhouette figée à mi-hauteur dans un puits
	# éteint se lirait comme un bug — et surtout, la coque qu'elle réservait ne serait jamais
	# rendue au pool : le pont resterait « plein » alors qu'il est mort.
	for slot in _risers.size():
		_risers[slot].visible = false
		_riser_age[slot] = -1.0
		_riser_enemy[slot] = null
	# ⚠️ ET LES PORTES SE REFERMENT POUR DE BON. Un pont abattu qui resterait ouvert sur sa lueur
	# dirait au joueur qu'il produit encore.
	_door_hold = 0.0
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
