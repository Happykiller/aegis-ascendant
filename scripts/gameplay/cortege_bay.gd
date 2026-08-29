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

# --- Le hangar, assemblé depuis le kit de la forge -----------------------------
#
## ⚠️ IL EST ASSEMBLÉ ICI, PIÈCE PAR PIÈCE, ET C'EST TOUT L'INTÉRÊT DU KIT. La forge livre sept
## volumes modélisés chacun dans son repère, origine au point d'assemblage ; c'est le moteur qui
## en fait sept hangars — et qui pourra en faire de différents, par rotation, écartement ou
## présence des blocs, sans qu'aucun modèle ne soit refait.
##
## ⚠️ ET C'EST OBLIGATOIRE, PAS UN CONFORT : les portes s'ouvrent, un appareil se pose au fond,
## un pont abattu doit rester fermé. Une cavité cuite dans la coque ne ferait aucune des trois.
const KIT_PATH := "res://assets/imported/models/backgrounds/bay_kit.glb"

## Cotes mesurées sur le binaire livré (BRIEF-0091), pas recopiées d'un brief : l'ouverture fait
## 6,00 × 8,50, le puits descend à −1,80 sous la bouche, le coaming monte à +0,60.
const OPENING_HALF_X := 3.00
const OPENING_HALF_Z := 4.25
const WELL_FLOOR := -1.80
const RAIL_GAP := 1.15
const RAIL_HALF_LEN := 3.30

## La teinte d'état. ⚠️ Le kit porte son émissif sur trois bandes — liseré de coaming, pied de
## paroi, filets de rail — et ces bandes partagent leur matériau avec les six autres hangars.
## Éteindre un pont abattu en touchant au matériau du kit éteindrait les sept. Chaque hangar
## reçoit donc sa PROPRE copie du matériau émissif à l'assemblage.
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
# ⚠️ QUATRE TEMPS, ET C'EST LA PLANCHE DE L'OPÉRATEUR QUI LES NOMME :
#
#   1. APPAREIL AU REPOS   — il est là, moteurs éteints, on le voit
#   2. ALLUMAGE            — les moteurs s'allument, il ne bouge pas encore
#   3. DÉCOLLAGE           — il monte, franchit la bouche, et entre en jeu
#   4. PUITS VIDE          — refroidissement, la porte se referme
#
## ⚠️ LE PREMIER TEMPS EST LE PLUS IMPORTANT, ET C'EST LE MOINS SPECTACULAIRE. C'est lui qui
## dit au joueur que la structure PRODUIT : un vaisseau immobile dans une cavité se comprend
## sans un mot. Les trois autres ne font que confirmer.
const REST_TIME := 0.75
const IGNITION_TIME := 0.45
const LAUNCH_TIME := 0.85
## Le temps où le puits reste ouvert et vide après le départ. Sans lui, la porte se referme sur
## la queue du vaisseau et la séquence n'a pas de fin — elle a une coupure.
const COOLDOWN_TIME := 0.5
## La silhouette part du fond du puits et sort par la bouche, en avançant vers le joueur.
## Le repos : au fond du puits, sur les rails. Le décollage : sorti de la bouche, en avant.
##
## ⚠️ IL SE POSE AU FOND, ET C'EST MAINTENANT VRAI. Cette valeur était provisoire à −0,70 tant
## que le puits n'était qu'un coaming de 0,78 m posé sur le bordé : y descendre l'appareil de
## 1,55 m l'aurait enterré dans la tôle. `BRIEF-0091` a livré la cavité de 1,80 m, et le
## commentaire d'alors prescrivait exactement ce passage.
const LAUNCH_FROM := Vector3(0.0, -1.55, -0.3)
const LAUNCH_TO := Vector3(0.0, 0.45, 2.1)
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
const DOOR_SLIDE := 3.00
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
## Les matériaux émissifs PROPRES à ce hangar. ⚠️ Un par surface du kit qui en porte : c'est
## eux, et eux seuls, qui disent si le pont vit, encaisse ou est mort.
var _glow: Array[StandardMaterial3D] = []

var _pass: Pass = Pass.AHEAD
var _timer: float = 0.0
var _health: float = 0.0
var _alive: bool = true
var _world: Vector3 = Vector3.ZERO

## Les décollages en cours. ⚠️ UN TABLEAU PRÉALLOUÉ ET NON UNE FILE QUI GRANDIT : deux coques
## par lâcher, et le lâcher suivant ne peut pas commencer avant la fin de celui-ci (l'intervalle
## est plus long que l'animation). Rien ne s'alloue pendant la partie (spec §26.1).
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
	_build_hangar()
	_build_doors()
	_build_risers()

## Assemble le hangar depuis le kit. Sept volumes, posés d'après leurs emprises mesurées : le
## montant gauche a son origine sur sa face INTERNE, le fond sur sa face SUPÉRIEURE, le rail à
## son extrémité arrière. C'est la convention de la forge — « origine au point d'assemblage » —
## et elle se vérifie sur le binaire plutôt que de se supposer.
func _build_hangar() -> void:
	var packed: PackedScene = load(KIT_PATH) as PackedScene
	if packed == null:
		push_error("[Cortege] kit de hangar introuvable : %s" % KIT_PATH)
		return
	var kit := packed.instantiate()
	# ⚠️ LE MONTANT AVANT EST POSÉ DEUX FOIS, la seconde d'un demi-tour. La forge ne livre qu'une
	# traverse : la symétrie appartient à l'assemblage, pas au modèle — c'est ce qui permet de
	# faire varier la longueur d'un hangar sans reforger quoi que ce soit.
	var poses: Array = [
		["bay_frame_left", Vector3(-OPENING_HALF_X, 0.0, 0.0), 0.0],
		["bay_frame_right", Vector3(OPENING_HALF_X, 0.0, 0.0), 0.0],
		["bay_frame_top", Vector3(0.0, 0.0, OPENING_HALF_Z), 0.0],
		["bay_frame_top", Vector3(0.0, 0.0, -OPENING_HALF_Z), PI],
		["bay_inner_wall", Vector3.ZERO, 0.0],
		["bay_floor", Vector3(0.0, WELL_FLOOR, 0.0), 0.0],
		["bay_launch_rail", Vector3(-RAIL_GAP, WELL_FLOOR, -RAIL_HALF_LEN), 0.0],
		["bay_launch_rail", Vector3(RAIL_GAP, WELL_FLOOR, -RAIL_HALF_LEN), 0.0],
	]
	for pose in poses:
		var source := kit.get_node_or_null(String(pose[0])) as MeshInstance3D
		if source == null:
			push_error("[Cortege] pièce de kit manquante : %s" % pose[0])
			continue
		var piece := MeshInstance3D.new()
		piece.name = String(pose[0])
		piece.mesh = source.mesh
		piece.position = pose[1]
		piece.rotation.y = pose[2]
		piece.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_claim_glow(piece, source)
		add_child(piece)
	kit.queue_free()

## Donne à CE hangar sa propre copie des matériaux émissifs, et laisse les autres partagés.
##
## ⚠️ SANS CETTE COPIE, ÉTEINDRE UN PONT ABATTU LES ÉTEINDRAIT TOUS LES SEPT. C'est exactement le
## piège qu'on a déjà payé sur la coque : les cœurs émissifs des puits y étaient cuits dans le
## tronçon et partageaient leur matériau. Un état par pièce demande un matériau par pièce.
func _claim_glow(piece: MeshInstance3D, source: MeshInstance3D) -> void:
	for i in source.mesh.get_surface_count():
		var base := source.mesh.surface_get_material(i) as StandardMaterial3D
		if base == null:
			continue
		if not base.emission_enabled:
			piece.set_surface_override_material(i, base)
			continue
		var mine: StandardMaterial3D = base.duplicate()
		piece.set_surface_override_material(i, mine)
		_glow.append(mine)

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
		slab.size = Vector3(OPENING_HALF_X, 0.14, OPENING_HALF_Z * 2.0)
		door.mesh = slab
		door.material_override = plate
		# Juste au-dessus de la peau, sous la lèvre du coaming : fermés, ils masquent la lueur.
		door.position = Vector3(side * OPENING_HALF_X * 0.5, 0.1, 0.0)
		door.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(door)
		_doors.append(door)

## Les silhouettes qui montent du puits. Une par coque d'un lâcher, montées au démarrage et
## réutilisées — comme tout le reste.
## ⚠️ IL N'Y A PLUS DE SILHOUETTE DÉCORATIVE. Les places de décollage ne portent plus que des
## références vers de VRAIES coques du pool : c'est la même que celle qui va tirer sur le joueur
## une seconde plus tard, et c'est ce qui rend la production compréhensible. Une maquette en
## boîtes disait « quelque chose sort » ; la coque dit « CELLE-CI sort ».
func _build_risers() -> void:
	for i in maxi(tuning.bay_release_count, 1):
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
	for slot in _riser_enemy.size():
		if launched >= tuning.bay_release_count:
			break
		if _riser_age[slot] >= 0.0:
			continue          # cette place décolle déjà
		var enemy := _take_from_pool()
		if enemy == null:
			break
		_riser_enemy[slot] = enemy
		_riser_age[slot] = 0.0
		launched += 1
	if launched > 0:
		# ⚠️ LA PORTE S'OUVRE AVANT QUE LA COQUE NE MONTE : c'est l'ordre qui rend la séquence
		# lisible. Ouvrir pendant la montée donnerait un vaisseau qui traverse un battant.
		# La porte reste ouverte le temps des quatre temps, refroidissement compris.
		_door_hold = DOOR_TIME + REST_TIME + IGNITION_TIME + LAUNCH_TIME + COOLDOWN_TIME
		_pulse_hatch()

func _take_from_pool() -> EnemyController:
	for i in _pool.size():
		var enemy := _pool[_next]
		_next = (_next + 1) % _pool.size()
		if not enemy.active and not _riser_enemy.has(enemy):
			return enemy
	return null

## Joue les quatre temps, place par place, et met la coque en jeu à la fin du troisième.
func _advance_risers(delta: float, here: Vector2) -> void:
	# ⚠️ RIEN NE COMMENCE TANT QUE LA PORTE N'EST PAS OUVERTE. Sans ce verrou, l'appareil est
	# posé sous un battant fermé : on ne le voit pas, et le premier temps — le seul qui compte —
	# est perdu.
	if _door_open < 0.85:
		return
	for slot in _riser_enemy.size():
		if _riser_age[slot] < 0.0:
			continue
		var enemy: EnemyController = _riser_enemy[slot]
		if enemy == null:
			_riser_age[slot] = -1.0
			continue
		_riser_age[slot] += delta
		var t: float = _riser_age[slot]
		var spread := 1.15 * (float(slot) - float(_riser_enemy.size() - 1) * 0.5)
		if t < REST_TIME:
			# 1. AU REPOS — posé sur les rails, moteurs éteints.
			enemy.park(_well_point(spread, 0.0), 0.0)
			continue
		if t < REST_TIME + IGNITION_TIME:
			# 2. ALLUMAGE — il ne bouge toujours pas, mais son moteur monte. C'est le seul
			# instant où le joueur peut encore décider de tirer sur le pont plutôt que sur lui.
			var heat := (t - REST_TIME) / IGNITION_TIME
			enemy.park(_well_point(spread, 0.0), heat)
			continue
		var climb := (t - REST_TIME - IGNITION_TIME) / LAUNCH_TIME
		if climb < 1.0:
			# 3. DÉCOLLAGE — il accélère. ⚠️ Une montée linéaire se lit comme un ascenseur ; un
			# décollage commence lentement et part.
			enemy.park(_well_point(spread, climb * climb), 1.0)
			continue
		# 4. Il entre en jeu, là où la montée l'a laissé — jamais au centre du puits, sinon il
		# ferait un saut en arrière à l'instant précis où le joueur le regarde.
		_riser_age[slot] = -1.0
		_riser_enemy[slot] = null
		enemy.activate(here + Vector2(spread, -LAUNCH_TO.z), randf() * TAU)
		released.emit(enemy)

## Où en est la coque dans son puits, en coordonnées MONDE. `climb` va de 0 (au fond) à 1 (sortie).
func _well_point(spread: float, climb: float) -> Vector3:
	var local := LAUNCH_FROM.lerp(LAUNCH_TO, climb) + Vector3(spread, 0.0, 0.0)
	return to_global(local)


## Fait coulisser les battants. ⚠️ LE FOND N'EST VISIBLE QUE QUAND ILS SONT OUVERTS : la lueur
## du puits est masquée à la fermeture, ce qui fait qu'un pont au repos — ou abattu — est un
## rectangle sombre sur la coque, et non une nappe magenta permanente.
func _advance_doors(delta: float) -> void:
	_door_hold = maxf(_door_hold - delta, 0.0)
	var wanted := 1.0 if _door_hold > 0.0 else 0.0
	_door_open = move_toward(_door_open, wanted, delta / DOOR_TIME)
	for i in _doors.size():
		var side := -1.0 if i == 0 else 1.0
		_doors[i].position.x = side * (OPENING_HALF_X * 0.5 + DOOR_SLIDE * _door_open)

## L'éclat d'un lâcher : les bandes montent d'un coup, puis retombent au premier dégât reçu.
func _pulse_hatch() -> void:
	_set_glow(3.0)

## Règle l'énergie de toutes les bandes de CE hangar.
func _set_glow(energy: float) -> void:
	for material in _glow:
		material.emission_energy_multiplier = energy

func _take_damage(damage: float) -> void:
	if not _alive:
		return
	_health -= damage
	# Les bandes pâlissent avec ce qui lui reste : le joueur doit voir qu'il PROGRESSE, sinon
	# mille cinq cents points de vie se lisent comme une cible indestructible.
	_set_glow(0.3 + 1.5 * clampf(_health / tuning.bay_health, 0.0, 1.0))
	if _health > 0.0:
		return
	_alive = false
	# ⚠️ TOUT S'ÉTEINT, ET SEULEMENT ICI. Un pont abattu dont les bandes brilleraient encore
	# dirait au joueur qu'il produit toujours.
	_set_glow(0.0)
	if _vfx != null:
		_vfx.spawn_explosion(_world, VfxExplosion.Category.HEAVY)
	# ⚠️ CE QUI DÉCOLLAIT MEURT AVEC LE PONT. Une silhouette figée à mi-hauteur dans un puits
	# éteint se lirait comme un bug — et surtout, la coque qu'elle réservait ne serait jamais
	# rendue au pool : le pont resterait « plein » alors qu'il est mort.
	for slot in _riser_enemy.size():
		var waiting: EnemyController = _riser_enemy[slot]
		if waiting != null:
			# ⚠️ ELLE RENTRE, ELLE NE MEURT PAS. Un pont abattu pendant qu'il chargeait ne doit
			# pas offrir une coque gratuite au score : ce qui est détruit, c'est le pont.
			waiting.unpark()
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
