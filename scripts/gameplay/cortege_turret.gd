class_name CortegeTurret
extends Node3D
## Une tourelle de coque du Long Cortège : elle télégraphie, elle brûle, puis elle passe.
##
## ⚠️ ELLE EST ENFANT DE SON MARQUEUR, ET C'EST TOUT LE MÉCANISME DE POSITION. La forge a livré
## `Turret_NN` comme enfant de son tronçon : le défilement déplace le décor, le décor emmène le
## tronçon, le tronçon emmène le marqueur, le marqueur emmène la tourelle. Il n'y a donc AUCUNE
## arithmétique de position à tenir à jour ici — donc aucune façon de la désynchroniser de la
## coque qu'on voit. C'est ce qui a coûté le plus cher sur les épines du Léviathan, où la pose
## se recalculait à partir d'un angle et finissait par désigner autre chose que la pièce.
##
## ⚠️ ELLE TIRE EN CONTINU ET ELLE PIVOTE LENTEMENT — ET C'EST UNE CORRECTION, PAS UN CHOIX DE
## DÉPART. Sa première version reprenait les trois temps de la tourelle-épine du Léviathan
## (`READY → WINDUP → FIRING → RECOVER`), avec un préavis qui annonçait le coup. Ce modèle marche
## sur un boss, qu'on regarde. Il ne marche pas ici : « je ne vois pas les tourelles qui me
## tirent dessus » (opérateur, en jouant le 2026-08-29). Sur un décor qui défile, avec dix-sept
## pièces réparties sur deux flancs, un préavis de 0,8 s passe inaperçu — le joueur regarde
## ailleurs, il esquive.
##
## Un tir CONTINU résout le problème par construction : la menace est visible tout le temps, sa
## direction se lit d'un coup d'œil, et l'on sait toujours quelle pièce est vivante. Ce qui
## remplace le télégraphe, c'est la LENTEUR — la tourelle pivote à 42 °/s, le joueur en contourne
## une à 100 °/s. L'invariant 3 de `CortegeTuning` tient cet écart : une menace qu'on ne peut pas
## semer serait une taxe, exactement ce que la spec §11.2 interdit.
##
## ⚠️ ET ELLE TIRE DES BALLES, PLUS UN FAISCEAU. Un rayon permanent était lisible mais laid, et
## surtout il ne se joue pas : on ne peut ni le voir venir, ni passer entre deux tirs. Des
## projectiles lents donnent au joueur les deux — « je préfère qu'elles tirent en continu des
## bullets » (opérateur, 2026-08-29). Ils traversent aussi le gestionnaire de balles commun,
## donc ils sont freinés par les mêmes écrans et comptés par la même densité que tout le reste.
##
## ⚠️ ELLE PIVOTE DÈS QU'ELLE VOUS VOIT, PAS SEULEMENT QUAND ELLE PEUT TIRER. Sa fenêtre de tir
## fait 20 unités ; elle commence à chercher son axe sur le DOUBLE. Le joueur voit donc le canon
## se tourner vers lui avant que ça ne compte — c'est ce qui remplace le télégraphe, et c'est
## demandé : « dès qu'on rentre dans leur champ de vision elles devraient tourner pour chercher
## à nous mettre dans leur axe de tir ».
##
## ⚠️ CE QUI CHANGE ICI : LE SURVOL NE REVIENT JAMAIS EN ARRIÈRE. Une tourelle a donc un AVANT,
## un PENDANT et un APRÈS. Passée, elle se tait pour de bon et REND SA CIBLE au gestionnaire de
## balles : dix-sept tourelles qui resteraient inscrites feraient payer à chaque balle du niveau
## le coût de cibles hors de portée à jamais.

## Le cycle de vie sur la coque. Une seule fois, dans un seul sens.
enum Pass { AHEAD, LIVE, PASSED }

## Teinte du faisceau : celle des lasers ennemis du jeu (`leviathan_combat.gd:563`), pas une
## nouvelle. Un second rouge apprendrait au joueur qu'il existe deux dangers là où il n'y en a
## qu'un.
const BEAM_CORE := Color(1.0, 0.90, 0.86)
const BEAM_EDGE := Color("c93a31")

## Le projectile. ⚠️ Une Resource partagée : tous les tirs de tourelle du niveau sont le même
## objet, comme partout ailleurs dans le jeu (spec §31).
const SHOT := preload("res://resources/weapons/cortege_turret_shot.tres")

## ⚠️ ELLE CHERCHE SON AXE SUR LE DOUBLE DE SA PORTÉE DE TIR. Voir le canon se tourner vers soi
## AVANT d'être à portée est ce qui remplace le télégraphe : la menace s'annonce par un geste,
## pas par un clignotement.
const SEEK_SPAN_FACTOR := 2.0

## Le CANON. ⚠️ IL EXISTE PARCE QU'UNE TOURELLE DOIT SE VOIR AVANT DE TIRER. La coupole est
## cuite dans le tronçon et ne bouge pas ; sans une pièce mobile, rien à l'écran ne dit où
## regarde la tourelle — et un faisceau qui sort d'un décor immobile se lit comme un piège, pas
## comme une machine. Le canon tourne, donc on lit son intention une seconde avant qu'elle ne
## compte.
const BARREL_LENGTH := 1.15
const BARREL_WIDTH := 0.19
const BARREL_GAP := 0.22
const HEAD_LIFT := 0.34
const HEAD_RADIUS := 0.58
const HEAD_HEIGHT := 0.34

## L'œil de la tourelle. ⚠️ IL EXISTE PARCE QUE LA GÉOMÉTRIE LIVRÉE EST CUITE DANS LE TRONÇON :
## les coupoles font partie du maillage de la section et partagent leurs matériaux avec elle. On
## ne peut donc PAS éteindre une tourelle en touchant à la coque — il faudrait éteindre les dix-
## sept. L'état de la pièce est porté par un volume à nous, ajouté au marqueur : il s'allume au
## télégraphe, il s'éteint à la mort. C'est la seule chose que le joueur ait à lire.
const EYE_RADIUS := 0.24
## D'où sort la balle : le bout des canons. ⚠️ Une balle née au centre de la coupole se verrait
## sortir du décor, ce qui est exactement ce qu'on reproche à un tir qu'on ne comprend pas.
const MUZZLE_REACH := 1.45

signal destroyed(turret: CortegeTurret)

var tuning: CortegeTuning
## Le tronçon d'appartenance, pour que le nœud d'épine du tronçon précédent sache qui éteindre.
var section: int = 0

var _bullet_manager: BulletManager
var _player: PlayerFighterController
var _vfx: VFXManager
var _target: BulletTarget
var _eye: MeshInstance3D
var _eye_material: StandardMaterial3D

var _pass: Pass = Pass.AHEAD
## ⚠️ `Node3D` ET NON `MeshInstance3D` : la tête est un ASSEMBLAGE — un dôme, deux canons, une
## bouche — et non un maillage. Le typer en `MeshInstance3D` a coûté une soirée : l'affectation
## échoue À L'EXÉCUTION, dans `_ready()`, donc la tête n'était jamais construite. La tourelle
## tirait quand même — la logique ne dépend pas du canon — et la porte de qualité restait VERTE,
## parce qu'un contrôle de type d'affectation ne se voit pas à l'analyse syntaxique. Une pièce
## invisible dont le comportement fonctionne est le pire des deux mondes.
var _barrel: Node3D
## Le temps qui reste avant la prochaine morsure du faisceau.
var _burn_timer: float = 0.0
var _health: float = 0.0
var _alive: bool = true
var _silenced: bool = false
## Où le canon pointe À CET INSTANT. ⚠️ IL SUIT LE JOUEUR, MAIS IL A DU RETARD, et ce retard EST
## la difficulté : la tourelle ne rate pas parce qu'elle vise mal, elle rate parce qu'elle
## n'arrive pas à suivre. C'est une règle qu'on comprend en une seconde de jeu, sans qu'aucun
## texte n'ait à l'expliquer.
var _aim: Vector2 = Vector2.DOWN
## La dernière position connue, en monde — pour poser l'explosion sur la COQUE et non sur le
## plan de vol, qui est trois unités et demie plus haut.
var _world: Vector3 = Vector3.ZERO

static func make(p_tuning: CortegeTuning, p_section: int) -> CortegeTurret:
	var turret := CortegeTurret.new()
	turret.tuning = p_tuning
	turret.section = p_section
	turret._health = p_tuning.turret_health
	# ⚠️ LA CIBLE NAIT AVEC LA PIECE, pas avec son cablage. Une tourelle sans BulletManager reste
	# une tourelle : elle a des points de vie et une facon de les perdre. Les creer dans `setup`
	# rendait la piece intestable sans gestionnaire de balles — et donc intestee.
	turret._target = BulletTarget.make(BulletManager.Team.ENEMY, 1.05, turret._take_damage)
	turret._target.enabled = false
	return turret

func setup(bullet_manager: BulletManager, player: PlayerFighterController,
		vfx: VFXManager) -> void:
	_bullet_manager = bullet_manager
	_player = player
	_vfx = vfx

func _ready() -> void:
	_build_head()

## La tourelle : une TÊTE qui pivote, deux canons, et une bouche qui s'allume au tir.
##
## ⚠️ ELLE ÉTAIT « HIDEUSE », ET LE MOT EST DE L'OPÉRATEUR. La première version posait une barre
## noire et une boule rose sur la coupole cuite dans la coque : deux primitives sans rapport,
## qui ne se lisaient ni comme une machine ni comme une menace. Ce qui manquait n'est pas du
## détail — à 23 px/m il n'en survivrait aucun — c'est une SILHOUETTE : un volume qui tourne,
## des canons qu'on voit pointer, une bouche qui dit quand ça part.
##
## ⚠️ ET ELLE EST BÂTIE SUR LE SOCLE DE LA FORGE, PAS À CÔTÉ. La coupole est cuite dans le
## tronçon et ne bouge pas ; la tête se pose dessus et tourne. C'est ce qui distingue la partie
## fixe de la partie mobile, et donc ce qui rend l'orientation lisible.
func _build_head() -> void:
	var steel := StandardMaterial3D.new()
	steel.albedo_color = Color(0.13, 0.12, 0.16)
	steel.metallic = 0.72
	steel.roughness = 0.34
	_barrel = Node3D.new()
	_barrel.name = "Head"
	_barrel.position.y = HEAD_LIFT
	add_child(_barrel)
	# La tête : un cylindre bas. Douze pans — on la voit toujours de dessus, et dix-sept
	# tourelles à soixante-quatre pans coûteraient mille triangles pour un contour identique.
	var dome := MeshInstance3D.new()
	var dome_mesh := CylinderMesh.new()
	dome_mesh.top_radius = HEAD_RADIUS * 0.82
	dome_mesh.bottom_radius = HEAD_RADIUS
	dome_mesh.height = HEAD_HEIGHT
	dome_mesh.radial_segments = 12
	dome_mesh.rings = 0
	dome.mesh = dome_mesh
	dome.material_override = steel
	dome.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_barrel.add_child(dome)
	# Les deux canons, cote à cote. ⚠️ LEUR PIVOT EST À LA TÊTE, pas en leur milieu : une
	# `BoxMesh` est centrée sur son origine, donc on les décale de la moitié de leur longueur.
	# Sans ça ils tournent autour de leur centre et sortent par l'arrière à chaque quart de tour.
	for side in [-1.0, 1.0]:
		var tube := MeshInstance3D.new()
		var bar := BoxMesh.new()
		bar.size = Vector3(BARREL_WIDTH, BARREL_WIDTH, BARREL_LENGTH)
		tube.mesh = bar
		tube.position = Vector3(side * BARREL_GAP, 0.0, -BARREL_LENGTH * 0.5 - HEAD_RADIUS * 0.4)
		tube.material_override = steel
		tube.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_barrel.add_child(tube)
	# La bouche : le seul volume émissif, et il porte TOUT l'état de la pièce — vivante, en
	# train de tirer, éteinte, morte. Un joueur doit pouvoir compter les tourelles encore
	# dangereuses d'un coup d'œil.
	_eye_material = StandardMaterial3D.new()
	_eye_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_eye_material.albedo_color = BEAM_EDGE
	_eye_material.emission_enabled = true
	_eye_material.emission = BEAM_EDGE
	_eye_material.emission_energy_multiplier = 1.4
	_eye = MeshInstance3D.new()
	_eye.name = "Muzzle"
	var glow := SphereMesh.new()
	glow.radius = EYE_RADIUS
	glow.height = EYE_RADIUS * 2.0
	glow.radial_segments = 8
	glow.rings = 4
	_eye.mesh = glow
	_eye.material_override = _eye_material
	_eye.position.z = -MUZZLE_REACH
	_eye.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_barrel.add_child(_eye)


func is_alive() -> bool:
	return _alive

func has_passed() -> bool:
	return _pass == Pass.PASSED

## Où pointe le canon. Lu par les tests : une rotation trop rapide ne se voit sur aucune capture,
## et c'est précisément ce que l'invariant 3 borne.
func aim() -> Vector2:
	return _aim

## La cible que le gestionnaire de balles connait. ⚠️ EXPOSEE PARCE QUE C'EST LE VRAI CHEMIN DES
## DEGATS : un test qui appellerait une methode ecrite pour lui ne verifierait pas le chemin que
## le jeu emprunte. Ici il n'y a qu'une porte, et tout le monde passe par elle.
func target() -> BulletTarget:
	return _target

## Dans sa fenetre, ni encore devant ni deja derriere.
func is_engaged() -> bool:
	return _pass == Pass.LIVE

## Éteinte par le nœud d'épine du tronçon précédent. ⚠️ ELLE RESTE TIRABLE : la récompense du
## nœud est de supprimer la MENACE, pas de faire disparaître la cible. Sans quoi abattre un nœud
## coûterait aussi le score des tourelles qu'il éteint, et le joueur apprendrait à ne plus le
## faire.
func silence() -> void:
	if _silenced:
		return
	_silenced = true
	_set_eye(0.25)

func is_silenced() -> bool:
	return _silenced

## Un pas de la tourelle. ⚠️ APPELÉE PAR LE GESTIONNAIRE, pas par `_process`. Vingt-neuf points
## d'ancrage qui traitent chacun leur propre image, c'est vingt-neuf appels de script par trame
## pour un travail que rien n'oblige à disperser — et un ordre de passage dont on ne sait plus
## rien le jour où un nœud doit éteindre une tourelle avant qu'elle ait tiré.
##
## ⚠️ ET SON POINT DE VISÉE LUI EST DONNÉ, IL NE SE DÉDUIT PAS DE SA POSITION. La pièce est
## vissée sur une coque à Y = −3,5, hors du plan de jeu ; la caméra plonge à 70°, donc elle
## n'apparaît PAS où sa projection verticale la met. Le gestionnaire calcule le point du plan
## qui se projette au même pixel (`GameplayPlane.aim_point_of`), et c'est LUI la hitbox. Sans
## cette correction, la tourelle se voyait à deux mètres de sa propre cible — le joueur visait
## juste et tirait à côté, signalé par l'opérateur, capture à l'appui.
##
## ⚠️ SA POSITION LUI EST DONNÉE, ELLE NE LA LIT PAS DANS L'ARBRE. Elle est
## pourtant enfant d'un marqueur qui défile, et `global_position` répondrait — mais seulement
## DANS un arbre monté. La passer en paramètre rend la pièce pilotable sans scène, donc
## vérifiable : c'est exactement ce qui a rendu `LeviathanCombat` testable là où trois cycles
## demandent quarante secondes de jeu. Le gestionnaire, lui, sait lire l'arbre.
func tick(delta: float, world: Vector3, here: Vector2) -> void:
	if _pass == Pass.PASSED:
		return
	_world = world
	var half := tuning.turret_visible_span * 0.5
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
	if not _alive or _silenced:
		return
	# ⚠️ ELLE CHERCHE SON AXE AVANT DE POUVOIR TIRER, et c'est ce qui remplace le télégraphe. Sa
	# fenêtre de tir fait 20 unités ; elle commence à se tourner vers le joueur sur le DOUBLE.
	# On voit donc le canon venir bien avant que ça ne compte — une menace qui s'annonce par un
	# geste, pas par un clignotement. Demandé en jouant : « dès qu'on rentre dans leur champ de
	# vision elles devraient tourner pour chercher à nous mettre dans leur axe de tir ».
	if absf(here.y) > half * SEEK_SPAN_FACTOR:
		return
	_run_fire(delta, here)

## Le tir continu : tourner vers le joueur, puis lâcher une balle à cadence fixe.
##
## ⚠️ LA CADENCE EST FIXE ET NON PROPORTIONNELLE AU TEMPS. Une tourelle qui tirerait « n balles
## par seconde » à coups de `delta` en perdrait presque toutes dans les images gelées par un
## arrêt sur image, et sa dangerosité dépendrait de la cadence d'affichage.
func _run_fire(delta: float, here: Vector2) -> void:
	_turn_toward(delta, here)
	_aim_barrel()
	if not _in_window(here):
		return
	_burn_timer -= delta
	if _burn_timer > 0.0 or _bullet_manager == null:
		return
	_burn_timer = tuning.turret_burn_interval
	# ⚠️ LA BALLE PART DE LA BOUCHE, pas du centre de la coupole : sinon elle naît dans le socle
	# et le joueur voit un tir sortir du décor.
	_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY,
		here + _aim * MUZZLE_REACH, _aim, SHOT)
	_set_eye(3.0)


## Fait pivoter le canon vers le joueur, sans jamais dépasser sa vitesse de rotation.
##
## ⚠️ `rotate_toward` ET PAS UNE INTERPOLATION : une interpolation de type `lerp_angle` va vite
## quand l'écart est grand et ralentit en approchant, donc elle colle au joueur dès qu'il est
## presque en face — précisément le cas où il essaie de s'échapper. Une vitesse ANGULAIRE
## CONSTANTE est ce que l'invariant 3 sait borner, et ce que le joueur peut apprendre.
func _turn_toward(delta: float, here: Vector2) -> void:
	var wanted := _direction_to_player(here).angle()
	_aim = Vector2.from_angle(turn_step(_aim.angle(), wanted,
		tuning.turret_turn_rate_deg, delta))


## Oriente le canon sur l'axe visé. ⚠️ Le canon est enfant du marqueur, qui défile : on lui
## donne un angle LOCAL. Le plan de jeu a +y vers le haut de l'écran, le monde −z : d'où le
## signe et le quart de tour.
func _aim_barrel() -> void:
	if _barrel != null:
		_barrel.rotation.y = -_aim.angle() + PI * 0.5

## Dans sa fenêtre de TIR — plus étroite que sa fenêtre de recherche.
func _in_window(here: Vector2) -> bool:
	return absf(here.y) <= tuning.turret_visible_span * 0.5


func _direction_to_player(here: Vector2) -> Vector2:
	if _player == null:
		return Vector2.DOWN
	var offset := _player.plane_position - here
	return offset.normalized() if offset.length_squared() > 0.0001 else Vector2.DOWN

func _set_eye(energy: float) -> void:
	if _eye_material != null:
		_eye_material.emission_energy_multiplier = energy

func _take_damage(damage: float) -> void:
	if not _alive:
		return
	_health -= damage
	if _health > 0.0:
		return
	_alive = false
	_set_eye(0.0)
	if _eye_material != null:
		_eye_material.albedo_color = Color(0.06, 0.05, 0.07)
	if _vfx != null:
		_vfx.spawn_explosion(_world, VfxExplosion.Category.MEDIUM)
	_retire()
	destroyed.emit(self)

## Rend la cible et cesse de compter. ⚠️ `unregister_target` est SÛRE depuis un rappel de
## dégâts — le gestionnaire diffère la suppression jusqu'à la fin de la passe.
func _retire() -> void:
	_pass = Pass.PASSED
	if _target != null:
		_target.enabled = false
		if _bullet_manager != null:
			_bullet_manager.unregister_target(_target)

# --- Fonction pure, testable sans arbre de scène ------------------------------

## Le pas de rotation d'une image. ⚠️ STATIQUE ET PURE, parce que c'est la SEULE chose de cette
## pièce qui doit être vérifiée au chiffre près : une tourelle qui pivote trop vite colle au
## joueur quoi qu'il fasse, et ça ne se voit sur aucune capture. La monter sur un banc
## demanderait un vrai `PlayerFighterController` ; ici il n'y a que trois nombres.
static func turn_step(current: float, wanted: float, rate_deg: float, delta: float) -> float:
	return rotate_toward(current, wanted, deg_to_rad(rate_deg) * delta)

## La tourelle est-elle dans sa fenêtre de tir, à cette position du plan ? ⚠️ STATIQUE ET PURE :
## c'est ce qui permet de tester la fenêtre sans monter le niveau, et donc de la tester du tout.
static func engaged_at(plane_y: float, visible_span: float) -> bool:
	return absf(plane_y) <= visible_span * 0.5
