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
## Un faisceau PERMANENT résout le problème par construction : la menace est visible tout le
## temps, sa direction se lit d'un coup d'œil, et l'on sait toujours quelle pièce est vivante.
## Ce qui remplace le télégraphe, c'est la LENTEUR — la tourelle pivote à 42 °/s, le joueur en
## contourne une à 100 °/s. L'invariant 3 de `CortegeTuning` tient cet écart : un faisceau qu'on
## ne peut pas semer serait une taxe, exactement ce que la spec §11.2 interdit.
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

## Le CANON. ⚠️ IL EXISTE PARCE QU'UNE TOURELLE DOIT SE VOIR AVANT DE TIRER. La coupole est
## cuite dans le tronçon et ne bouge pas ; sans une pièce mobile, rien à l'écran ne dit où
## regarde la tourelle — et un faisceau qui sort d'un décor immobile se lit comme un piège, pas
## comme une machine. Le canon tourne, donc on lit son intention une seconde avant qu'elle ne
## compte.
const BARREL_LENGTH := 1.35
const BARREL_WIDTH := 0.26
const BARREL_LIFT := 0.42

## L'œil de la tourelle. ⚠️ IL EXISTE PARCE QUE LA GÉOMÉTRIE LIVRÉE EST CUITE DANS LE TRONÇON :
## les coupoles font partie du maillage de la section et partagent leurs matériaux avec elle. On
## ne peut donc PAS éteindre une tourelle en touchant à la coque — il faudrait éteindre les dix-
## sept. L'état de la pièce est porté par un volume à nous, ajouté au marqueur : il s'allume au
## télégraphe, il s'éteint à la mort. C'est la seule chose que le joueur ait à lire.
const EYE_RADIUS := 0.42
const EYE_LIFT := 0.55

signal destroyed(turret: CortegeTurret)

var tuning: CortegeTuning
## Le tronçon d'appartenance, pour que le nœud d'épine du tronçon précédent sache qui éteindre.
var section: int = 0

var _bullet_manager: BulletManager
var _player: PlayerFighterController
var _vfx: VFXManager
var _target: BulletTarget
var _beam: Beam
var _eye: MeshInstance3D
var _eye_material: StandardMaterial3D

var _pass: Pass = Pass.AHEAD
var _barrel: MeshInstance3D
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
	_eye_material = StandardMaterial3D.new()
	_eye_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_eye_material.albedo_color = BEAM_EDGE
	_eye_material.emission_enabled = true
	_eye_material.emission = BEAM_EDGE
	_eye_material.emission_energy_multiplier = 0.6
	var mesh := SphereMesh.new()
	mesh.radius = EYE_RADIUS
	mesh.height = EYE_RADIUS * 2.0
	# Une coque de dix-sept œils : la sphère par défaut en coûterait 1 472 à elle seule, pour
	# un volume de quarante centimètres qu'on ne voit jamais de près.
	mesh.radial_segments = 8
	mesh.rings = 4
	_eye = MeshInstance3D.new()
	_eye.name = "Eye"
	_eye.mesh = mesh
	_eye.material_override = _eye_material
	_eye.position.y = EYE_LIFT
	_eye.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_eye)
	# Le canon : une barre posée à plat qui pointe où le faisceau part. ⚠️ SON PIVOT EST À SA
	# BASE, pas en son milieu — une `BoxMesh` est centrée sur son origine, donc on la décale de
	# la moitié de sa longueur dans un nœud intermédiaire. Sans ça elle tourne autour de son
	# centre et sort de la coupole par l'arrière à chaque quart de tour.
	_barrel = MeshInstance3D.new()
	_barrel.name = "Barrel"
	_barrel.position.y = BARREL_LIFT
	_barrel.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var tube := MeshInstance3D.new()
	var bar := BoxMesh.new()
	bar.size = Vector3(BARREL_WIDTH, BARREL_WIDTH, BARREL_LENGTH)
	tube.mesh = bar
	tube.position.z = -BARREL_LENGTH * 0.5
	var steel := StandardMaterial3D.new()
	steel.albedo_color = Color(0.16, 0.14, 0.18)
	steel.metallic = 0.7
	steel.roughness = 0.35
	tube.material_override = steel
	tube.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_barrel.add_child(tube)
	add_child(_barrel)
	_beam = Beam.make()
	# ⚠️ `top_level` OBLIGATOIRE, exactement pour la raison qui a coûté un après-midi sur le
	# Léviathan : `Beam.aim()` pose le faisceau en coordonnées MONDE, et cette tourelle est
	# enfant d'un marqueur qui est lui-même à trois cents unités de l'origine. Sans lui, le
	# faisceau subit la position du décor DEUX fois et part hors du cadre — sans une ligne au
	# journal.
	_beam.top_level = true
	_beam.tint(BEAM_CORE, BEAM_EDGE)
	add_child(_beam)

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
	if _beam != null:
		_beam.extinguish()
	_set_eye(0.25)

func is_silenced() -> bool:
	return _silenced

## Un pas de la tourelle. ⚠️ APPELÉE PAR LE GESTIONNAIRE, pas par `_process`. Vingt-neuf points
## d'ancrage qui traitent chacun leur propre image, c'est vingt-neuf appels de script par trame
## pour un travail que rien n'oblige à disperser — et un ordre de passage dont on ne sait plus
## rien le jour où un nœud doit éteindre une tourelle avant qu'elle ait tiré.
##
## ⚠️ SA POSITION LUI EST DONNÉE, ELLE NE LA LIT PAS DANS L'ARBRE. Elle est
## pourtant enfant d'un marqueur qui défile, et `global_position` répondrait — mais seulement
## DANS un arbre monté. La passer en paramètre rend la pièce pilotable sans scène, donc
## vérifiable : c'est exactement ce qui a rendu `LeviathanCombat` testable là où trois cycles
## demandent quarante secondes de jeu. Le gestionnaire, lui, sait lire l'arbre.
func tick(delta: float, world: Vector3) -> void:
	if _pass == Pass.PASSED:
		return
	_world = world
	var here := GameplayPlane.to_plane(world)
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
	if not _alive or _silenced or _pass != Pass.LIVE:
		return
	_run_fire(delta, here)

## Le tir continu. Trois gestes seulement : tourner vers le joueur, tendre le faisceau, mordre
## à cadence fixe ce qu'il touche.
##
## ⚠️ LA MORSURE EST CADENCÉE, PAS PROPORTIONNELLE AU TEMPS. Verser `dps × delta` au bouclier à
## chaque image ferait perdre presque tout dans les images gelées par un arrêt sur image, et
## rendrait les dégâts dépendants de la cadence d'affichage. Une morsure toutes les 0,4 s se
## règle, se teste, et se sent.
func _run_fire(delta: float, here: Vector2) -> void:
	_turn_toward(delta, here)
	_project(here)
	_burn_timer -= delta
	if _burn_timer > 0.0 or _player == null:
		return
	var reach := here + _aim * tuning.turret_range
	# ⚠️ `Beam.hits` s'applique au SEGMENT, pas au bout : la tourelle brûle ce qui traverse, et
	# c'est ce qui rend le faisceau lisible — on voit exactement où il ne faut pas passer.
	if Beam.hits(here, reach, tuning.turret_beam_half_width, _player.plane_position, 0.25):
		_burn_timer = tuning.turret_burn_interval
		_player.take_contact_damage(tuning.turret_burn_damage)

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
	if _barrel != null:
		# ⚠️ Le canon est un enfant du marqueur, qui défile : on lui donne un angle LOCAL. Le
		# plan de jeu a +y vers l'écran, le monde -z : d'où le signe.
		_barrel.rotation.y = -_aim.angle() + PI * 0.5


## Tend le faisceau. ⚠️ IL EST TOUJOURS ARMÉ TANT QUE LA TOURELLE VIT : c'est lui, et lui seul,
## qui dit au joueur quelles pièces sont encore dangereuses.
func _project(here: Vector2) -> void:
	var reach := here + _aim * tuning.turret_range
	if _beam != null:
		_beam.aim(here, reach, tuning.turret_beam_half_width)
		_beam.set_regime(2.2, 0.0)
	_set_eye(2.2)


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
	if _beam != null:
		_beam.extinguish()
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
	if _beam != null:
		_beam.extinguish()

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
