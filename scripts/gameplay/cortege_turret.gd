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

# --- L'affût, assemblé depuis le kit de la forge -------------------------------
#
## ⚠️ HUIT PIÈCES, ET UN NŒUD INTERMÉDIAIRE QUI TOURNE. Le socle et l'appareillage sont FIXES,
## posés sur le marqueur ; la couronne, le bloc et les deux tubes tournent EN BLOC autour de
## l'axe du marqueur. C'est ce qui distingue la partie ancrée de la partie mobile — et donc ce
## qui rend l'orientation lisible d'un coup d'œil, ce que la version précédente (une barre noire
## et une boule rose) ne faisait pas.
const KIT_PATH := "res://assets/imported/models/backgrounds/turret_kit.glb"

## Positions d'assemblage, mesurées sur le binaire livré (BRIEF-0093) — pas recopiées d'un brief.
const RING_LIFT := 0.02
const BODY_LIFT := 0.37
const BARREL_LIFT := 0.90
## ⚠️ LA CULASSE EST AU FOND DU MASQUE, PAS SUR LA FACE AVANT. C'est la différence entre un tube
## « logé » et un tube « collé devant » — 12 cm qui font toute la lecture du blindage.
const BARREL_SEAT_Z := 0.60
## Où l'appareillage se pose autour du socle.
const SERVICE_RADIUS := 1.46
const SERVICE_LIFT := 0.14

## Les trois familles du kit, telles que la forge les a réglées. ⚠️ LA VARIÉTÉ EST UN LIVRABLE :
## dix-sept tourelles identiques se liraient comme dix-sept fois la même. Aucune géométrie neuve
## n'est nécessaire — jupe ou non, tube long ou court, écartement, angles de l'appareillage.
const FAMILIES: Array = [
	# jupe, tube,                  écartement, coffrets,        conduite
	[false, "turret_barrel_short", 0.72, [128.0],          -1.0],
	[true,  "turret_barrel",       0.86, [118.0, -118.0],  180.0],
	[true,  "turret_barrel",       0.98, [96.0, -142.0],   205.0],
]

## L'œil de la tourelle. ⚠️ IL EXISTE PARCE QUE LA GÉOMÉTRIE LIVRÉE EST CUITE DANS LE TRONÇON :
## les coupoles font partie du maillage de la section et partagent leurs matériaux avec elle. On
## ne peut donc PAS éteindre une tourelle en touchant à la coque — il faudrait éteindre les dix-
## sept. L'état de la pièce est porté par un volume à nous, ajouté au marqueur : il s'allume au
## télégraphe, il s'éteint à la mort. C'est la seule chose que le joueur ait à lire.
## D'où sort la balle : le bout des tubes, mesuré — culasse à +0,60 plus 2,90 m de tube.
## ⚠️ Une balle née au centre de la coupole se verrait sortir du décor, ce qui est exactement ce
## qu'on reproche à un tir qu'on ne comprend pas.
## ⚠️ CE QUE LE JOUEUR VISE N'EST PAS OÙ LA PIÈCE EST POSÉE. La caméra plonge à 70° : la masse
## qu'on voit — le tambour à +0,37..+1,70 et les tubes à +0,90 — se projette sur le plan de jeu
## à une vingtaine de centimètres de son assise. La zone de touche se cale donc sur les tubes,
## pas sur le socle. Voir le même constant sur `CortegeSpineNode`, où l'écart coûtait plus cher.
const HIT_LIFT := 0.90

const MUZZLE_REACH := 3.50

## L'énergie de l'œil selon l'état. ⚠️ AFFAIBLIE N'EST PAS MORTE, ET ÇA DOIT SE VOIR : une pièce
## abîmée garde une braise, une pièce abattue est noire. Sans cet écart, le joueur n'a aucun
## moyen de savoir laquelle des deux il regarde — et donc aucune raison de tirer sur l'une.
## L'épave. ⚠️ ELLE EXISTE PARCE QUE RIEN NE MOURAIT À L'ÉCRAN. Une tourelle abattue perdait son
## œil et c'est tout : le socle, la couronne, le tambour et les deux tubes restaient debout,
## intacts, pour toujours. Vivante, abîmée et morte se ressemblaient — « pas d'animation de
## destruction des canons » (opérateur, 2026-08-30, en jouant).
##
## ⚠️ ET C'EST LA SILHOUETTE QUI PORTE L'INFORMATION, PAS LA COULEUR. La caméra plonge à 70° et
## le rendu sort à 23 px/m : un noircissement de 1,5 m se perd, deux tubes qui PIQUENT DU NEZ et
## partent de travers se voient d'un coup d'œil, et se voient encore mieux à côté d'une tourelle
## intacte. C'est aussi la seule mise en scène qui ne coûte aucune géométrie neuve et aucun
## matériau dupliqué — dix-sept tourelles qui s'offriraient chacune sa copie du bordé casseraient
## le regroupement des dessins pour un effet qu'on ne verrait pas.
const WRECK_TIME := 0.8
const WRECK_PITCH_DEG := -34.0
const WRECK_ROLL_DEG := 17.0
const WRECK_SINK := 0.14
## De combien la tête part de travers en mourant. ⚠️ TIRÉE DU RANG DE MONTAGE, PAS DU HASARD :
## un tirage aléatoire donnerait un champ de ruines différent à chaque lancement, donc deux
## captures qu'on ne peut pas comparer — et l'équilibrage d'un survol se lit en comparant deux
## passages.
const WRECK_YAW_DEG := 63.0

const EYE_SHOT := 3.0
const EYE_WEAK := 0.55
const EYE_DEAD := 0.0

signal destroyed(turret: CortegeTurret)

var tuning: CortegeTuning
## Le tronçon d'appartenance, pour que le nœud d'épine du tronçon précédent sache qui éteindre.
var section: int = 0

var _bullet_manager: BulletManager
var _player: PlayerFighterController
var _vfx: VFXManager
var _target: BulletTarget
## Les matériaux émissifs PROPRES à cette tourelle — l'œil, au fond du masque.
var _glow: Array[StandardMaterial3D] = []
## Son rang de montage, pour que la famille se tire de la position et non du hasard.
var serial: int = 0

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
var _weakened: bool = false
## Où le canon pointe À CET INSTANT. ⚠️ IL SUIT LE JOUEUR, MAIS IL A DU RETARD, et ce retard EST
## la difficulté : la tourelle ne rate pas parce qu'elle vise mal, elle rate parce qu'elle
## n'arrive pas à suivre. C'est une règle qu'on comprend en une seconde de jeu, sans qu'aucun
## texte n'ait à l'expliquer.
var _aim: Vector2 = Vector2.DOWN
## La dernière position connue, en monde — pour poser l'explosion sur la COQUE et non sur le
## plan de vol, qui est trois unités et demie plus haut.
var _world: Vector3 = Vector3.ZERO
## L'avancement de l'effondrement, de 0 à 1. Négatif tant que la pièce est debout.
var _wreck: float = -1.0
## La pose de la tête au moment où elle meurt — l'effondrement part de LÀ, et non d'un zéro qui
## ferait sauter le canon avant de le faire tomber.
var _wreck_from: Vector3 = Vector3.ZERO

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

## Assemble l'affût. Le socle et l'appareillage restent sur le marqueur ; tout le reste va sous
## un nœud qui tourne.
##
## ⚠️ LA FAMILLE SE TIRE DE LA POSITION, PAS DU HASARD. Un tirage aléatoire donnerait une
## répartition différente à chaque lancement, donc une capture qu'on ne peut pas comparer à la
## précédente — et l'équilibrage d'un survol se lit en comparant deux passages.
func _build_head() -> void:
	var packed: PackedScene = load(KIT_PATH) as PackedScene
	if packed == null:
		push_error("[Cortege] kit de tourelle introuvable : %s" % KIT_PATH)
		return
	var kit := packed.instantiate()
	var family: Array = FAMILIES[(serial + section) % FAMILIES.size()]
	_place(kit, "turret_pad", Vector3.ZERO, 0.0, self)
	if bool(family[0]):
		_place(kit, "turret_anchor_skirt", Vector3.ZERO, 0.0, self)
	for angle in family[3]:
		_place_around(kit, "turret_service_box", float(angle), self)
	if float(family[4]) >= 0.0:
		_place_around(kit, "turret_pipe", float(family[4]), self)
	# ⚠️ LE ROTATEUR EST À L'ORIGINE DU MARQUEUR, SUR L'AXE. Si son origine s'en écartait d'un
	# centimètre, la tourelle balaierait en décrivant un cercle au lieu de pivoter sur place —
	# et ça ne se verrait qu'en jeu, en mouvement.
	_barrel = Node3D.new()
	_barrel.name = "Rotator"
	add_child(_barrel)
	_place(kit, "turret_ring", Vector3(0.0, RING_LIFT, 0.0), 0.0, _barrel)
	_place(kit, "turret_body", Vector3(0.0, BODY_LIFT, 0.0), 0.0, _barrel)
	var gauge := float(family[2])
	for side in [-1.0, 1.0]:
		_place(kit, String(family[1]),
			Vector3(side * gauge * 0.5, BARREL_LIFT, BARREL_SEAT_Z), 0.0, _barrel)
	kit.queue_free()

func _place(kit: Node, part: String, offset: Vector3, yaw: float, parent: Node) -> void:
	var source := kit.get_node_or_null(part) as MeshInstance3D
	if source == null:
		push_error("[Cortege] pièce de kit manquante : %s" % part)
		return
	var piece := MeshInstance3D.new()
	piece.name = part
	piece.mesh = source.mesh
	piece.position = offset
	piece.rotation.y = yaw
	piece.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_claim_glow(piece, source)
	parent.add_child(piece)

## Pose une pièce d'appareillage autour du socle, à l'angle voulu.
func _place_around(kit: Node, part: String, degrees: float, parent: Node) -> void:
	var a := deg_to_rad(degrees)
	_place(kit, part, Vector3(cos(a) * SERVICE_RADIUS, SERVICE_LIFT, sin(a) * SERVICE_RADIUS),
		-a, parent)

## Donne à CETTE tourelle sa propre copie du matériau émissif — l'œil.
##
## ⚠️ SANS CETTE COPIE, ÉTEINDRE UNE TOURELLE ABATTUE LES ÉTEINDRAIT TOUTES LES DIX-SEPT. Même
## piège que sur les puits, et il a déjà été payé deux fois : un état par pièce demande un
## matériau par pièce.
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

## Affaiblie par le nœud d'épine du tronçon précédent. ⚠️ ELLE RESTE TIRABLE : la récompense du
## nœud est de réduire la MENACE, pas de faire disparaître la cible. Sans quoi abattre un nœud
## coûterait aussi le score des tourelles qu'il touche, et le joueur apprendrait à ne plus le
## faire.
##
## ⚠️ ELLE AFFAIBLIT, ELLE N'ÉTEINT PAS — ET C'EST UNE CORRECTION, PAS UN CHOIX DE DÉPART. La
## première version faisait taire toute la pièce : plus de rotation, plus de tir. Mesuré en jeu
## le 2026-08-30, ça vidait le niveau — **quinze tourelles sur dix-sept** neutralisées avant même
## d'être à portée, parce que les cinq nœuds tombent et que la chaîne se referme. Le joueur ne
## lisait pas une récompense, il lisait une panne : « certaines tours canon ne sont pas actives,
## ne bougent pas, ne tirent pas » (opérateur). Une pièce immobile ne dit RIEN de ce qui l'a
## rendue inoffensive.
##
## Une tourelle affaiblie continue donc de pivoter et de tirer — plus lentement, et son œil
## reste bas. C'est ce qui rend la récompense LISIBLE : on voit la même pièce, on la voit
## traîner, et on comprend d'un coup d'œil que quelque chose l'a abîmée.
func weaken() -> void:
	if _weakened:
		return
	_weakened = true
	_set_eye(EYE_WEAK)

func is_weakened() -> bool:
	return _weakened

## L'avancement de l'effondrement, de 0 à 1 ; négatif tant que la pièce est debout. ⚠️ EXPOSÉ
## PARCE QUE C'EST LA SEULE FAÇON DE GARDER UNE MISE EN SCÈNE. Une épave ne se voit sur aucune
## capture automatisée — elle dure huit dixièmes de seconde, quelque part sur dix-sept pièces —
## et c'est précisément le genre d'effet qui disparaît sans bruit à la première refonte.
func wreck_progress() -> float:
	return _wreck


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
	# ⚠️ AVANT LA SORTIE SUR `PASSED`. Une tourelle abattue se retire dans la même trame ; si
	# l'effondrement attendait la logique de fenêtre, il ne commencerait jamais.
	if _wreck >= 0.0 and _wreck < 1.0:
		_advance_wreck(delta)
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
	if not _alive:
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
	_burn_timer = tuning.turret_burn_interval * fire_slack()
	# ⚠️ LA BALLE PART DE LA BOUCHE, pas du centre de la coupole : sinon elle naît dans le socle
	# et le joueur voit un tir sortir du décor.
	_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY,
		here + _aim * MUZZLE_REACH, _aim, SHOT)
	_set_eye(EYE_SHOT)


## Fait pivoter le canon vers le joueur, sans jamais dépasser sa vitesse de rotation.
##
## ⚠️ `rotate_toward` ET PAS UNE INTERPOLATION : une interpolation de type `lerp_angle` va vite
## quand l'écart est grand et ralentit en approchant, donc elle colle au joueur dès qu'il est
## presque en face — précisément le cas où il essaie de s'échapper. Une vitesse ANGULAIRE
## CONSTANTE est ce que l'invariant 3 sait borner, et ce que le joueur peut apprendre.
func _turn_toward(delta: float, here: Vector2) -> void:
	var wanted := _direction_to_player(here).angle()
	_aim = Vector2.from_angle(turn_step(_aim.angle(), wanted,
		tuning.turret_turn_rate_deg * turn_slack(), delta))

## Ce que l'affaiblissement retire à la rotation. ⚠️ IL NE PEUT PAS ALLER À ZÉRO : c'est la
## rotation qui dit au joueur que la pièce est vivante mais diminuée. `CortegeTuning.validate()`
## borne le facteur des deux côtés, pour cette raison exactement.
##
## ⚠️ PUBLIQUE PARCE QUE C'EST LA SEULE PORTE OÙ L'ÉTAT SE LIT SANS JOUEUR. Vérifier la rotation
## sur la pièce montée demanderait un `PlayerFighterController` — sans lui la tourelle vise
## `Vector2.DOWN` et ne bouge pas, donc un test « elle pivote encore » passerait au vert pour la
## mauvaise raison. Ici il n'y a que l'état et deux nombres.
func turn_slack() -> float:
	return tuning.turret_weakened_turn_factor if _weakened else 1.0

## Ce que l'affaiblissement ajoute au délai entre deux tirs. Un multiplicateur ≥ 1 : la tourelle
## tire toujours, elle tire moins.
func fire_slack() -> float:
	return tuning.turret_weakened_interval_factor if _weakened else 1.0


## Oriente le canon sur l'axe visé. ⚠️ Le canon est enfant du marqueur, qui défile : on lui
## donne un angle LOCAL. Le plan de jeu a +y vers le haut de l'écran, le monde −z : d'où le
## signe et le quart de tour.
func _aim_barrel() -> void:
	if _barrel != null:
		_barrel.rotation.y = barrel_yaw(_aim)

## Dans sa fenêtre de TIR — plus étroite que sa fenêtre de recherche.
func _in_window(here: Vector2) -> bool:
	return absf(here.y) <= tuning.turret_visible_span * 0.5


func _direction_to_player(here: Vector2) -> Vector2:
	if _player == null:
		return Vector2.DOWN
	var offset := _player.plane_position - here
	return offset.normalized() if offset.length_squared() > 0.0001 else Vector2.DOWN

func _set_eye(energy: float) -> void:
	for material in _glow:
		material.emission_energy_multiplier = energy

func _take_damage(damage: float) -> void:
	if not _alive:
		return
	_health -= damage
	if _health > 0.0:
		return
	_alive = false
	_set_eye(EYE_DEAD)
	if _vfx != null:
		_vfx.spawn_explosion(_world, VfxExplosion.Category.MEDIUM)
	_begin_wreck()
	_retire()
	destroyed.emit(self)

## Ouvre l'effondrement. ⚠️ IL PART DE LA POSE COURANTE. La tête est là où le dernier tir l'a
## laissée ; repartir d'une pose neutre ferait sauter le canon d'un quart de tour à l'instant
## exact où le joueur regarde l'explosion — le seul moment où il ne peut pas le manquer.
func _begin_wreck() -> void:
	_wreck = 0.0
	if _barrel != null:
		_wreck_from = _barrel.rotation

## Un pas de l'effondrement. ⚠️ APPELÉ MÊME QUAND LA PIÈCE EST `PASSED` : elle meurt souvent au
## bord de sa fenêtre, et une épave qui se figerait à mi-chute serait pire que pas d'épave du
## tout — le joueur verrait le canon s'arrêter en l'air.
func _advance_wreck(delta: float) -> void:
	_wreck = minf(_wreck + delta / WRECK_TIME, 1.0)
	if _barrel == null:
		return
	# Une chute qui décélère : la tête part vite, puis s'affaisse. `ease_out` par un carré, sans
	# courbe à charger ni Tween à allouer.
	var k := 1.0 - (1.0 - _wreck) * (1.0 - _wreck)
	var yaw := deg_to_rad(WRECK_YAW_DEG) * (1.0 if serial % 2 == 0 else -1.0)
	_barrel.rotation = Vector3(
		_wreck_from.x + deg_to_rad(WRECK_PITCH_DEG) * k,
		_wreck_from.y + yaw * k,
		_wreck_from.z + deg_to_rad(WRECK_ROLL_DEG) * k * (1.0 if serial % 2 == 0 else -1.0))
	_barrel.position.y = -WRECK_SINK * k

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

## L'angle du rotateur pour viser cette direction du plan de jeu.
##
## ⚠️ ELLE A ÉTÉ FAUSSE, ET JE NE POUVAIS PAS LE VOIR. La formule était `-angle + π/2`, juste sur
## l'axe X et fausse partout ailleurs — de 180° vers le haut de l'écran. Elle n'a jamais été
## prise en défaut parce que la tête n'était **jamais construite** : un mauvais type l'avait fait
## échouer à l'exécution, et la tourelle tirait quand même. Deux défauts qui se cachaient l'un
## l'autre.
##
## Le calcul, posé : le tube pointe vers son `+z` local ; une rotation de θ autour de Y l'emmène
## sur `(sin θ, 0, cos θ)`. Le plan de jeu envoie `(x, y)` sur le monde `(x, 0, −y)`. Donc
## `sin θ = aim.x` et `cos θ = −aim.y`, soit `θ = atan2(aim.x, −aim.y)`.
static func barrel_yaw(aim: Vector2) -> float:
	return atan2(aim.x, -aim.y)

## La tourelle est-elle dans sa fenêtre de tir, à cette position du plan ? ⚠️ STATIQUE ET PURE :
## c'est ce qui permet de tester la fenêtre sans monter le niveau, et donc de la tester du tout.
static func engaged_at(plane_y: float, visible_span: float) -> bool:
	return absf(plane_y) <= visible_span * 0.5
