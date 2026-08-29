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
## ⚠️ LE MODÈLE EST LA TOURELLE-ÉPINE DU LÉVIATHAN, PAS `CitadelTurret`. Cette dernière est
## décorative : elle ne tire ni n'encaisse. Les trois temps repris ici — `READY → WINDUP →
## FIRING → RECOVER` — sont ceux de `leviathan_combat.gd`, et l'invariant 3 de `CortegeTuning`
## les tient : un tir qui part sans préavis n'est pas une difficulté, c'est une taxe (spec §11.2).
##
## ⚠️ CE QUI CHANGE ICI : LE SURVOL NE REVIENT JAMAIS EN ARRIÈRE. Une tourelle a donc un AVANT,
## un PENDANT et un APRÈS. Passée, elle se tait pour de bon et REND SA CIBLE au gestionnaire de
## balles : dix-sept tourelles qui resteraient inscrites feraient payer à chaque balle du niveau
## le coût de cibles hors de portée à jamais.

## Le cycle de vie sur la coque. Une seule fois, dans un seul sens.
enum Pass { AHEAD, LIVE, PASSED }

## Les trois temps du tir, plus le repos.
enum Fire { READY, WINDUP, FIRING, RECOVER }

## Teinte du faisceau : celle des lasers ennemis du jeu (`leviathan_combat.gd:563`), pas une
## nouvelle. Un second rouge apprendrait au joueur qu'il existe deux dangers là où il n'y en a
## qu'un.
const BEAM_CORE := Color(1.0, 0.90, 0.86)
const BEAM_EDGE := Color("c93a31")

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
var _fire: Fire = Fire.READY
var _timer: float = 0.0
var _health: float = 0.0
var _alive: bool = true
var _silenced: bool = false
## La direction VERROUILLÉE au début du télégraphe.
##
## ⚠️ ELLE EST VERROUILLÉE, ET C'EST TOUT L'INTÉRÊT DU TÉLÉGRAPHE. Une ligne de visée qui suit
## le joueur pendant le préavis ne lui annonce rien : elle le désigne. Ce qui rend l'esquive
## possible, c'est que la tourelle s'engage sur un point AVANT de tirer, et qu'elle y tire même
## si le joueur n'y est plus.
var _aim: Vector2 = Vector2.DOWN
## La dernière position connue, en monde — pour poser l'explosion sur la COQUE et non sur le
## plan de vol, qui est trois unités et demie plus haut.
var _world: Vector3 = Vector3.ZERO

static func make(p_tuning: CortegeTuning, p_section: int) -> CortegeTurret:
	var turret := CortegeTurret.new()
	turret.tuning = p_tuning
	turret.section = p_section
	turret._health = p_tuning.turret_health
	turret._timer = p_tuning.turret_interval
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

## Le temps du tir ou elle en est. Lu par les tests : le telegraphe ne se voit sur aucune capture.
func fire_state() -> Fire:
	return _fire

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
	_fire = Fire.READY
	_timer = tuning.turret_interval
	if _beam != null:
		_beam.extinguish()

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

## Les trois temps. Le télégraphe fin qui annonce, le faisceau qui frappe, la récupération.
func _run_fire(delta: float, here: Vector2) -> void:
	_timer -= delta
	if _timer > 0.0:
		if _fire == Fire.WINDUP or _fire == Fire.FIRING:
			_project(here)
		return
	match _fire:
		Fire.READY:
			_fire = Fire.WINDUP
			_timer = tuning.turret_windup_time
			# Le verrouillage. Le joueur a `turret_windup_time` pour ne plus être là.
			_aim = _direction_to_player(here)
			_project(here)
		Fire.WINDUP:
			_fire = Fire.FIRING
			_timer = tuning.turret_beam_time
		Fire.FIRING:
			_fire = Fire.RECOVER
			_timer = tuning.turret_recover_time
			if _beam != null:
				_beam.extinguish()
			_set_eye(0.6)
		Fire.RECOVER:
			_fire = Fire.READY
			_timer = tuning.turret_interval

## Tend le faisceau et, s'il est armé, brûle ce qu'il touche.
func _project(here: Vector2) -> void:
	var reach := here + _aim * tuning.turret_range
	var firing := _fire == Fire.FIRING
	var half_width := tuning.turret_beam_half_width if firing else tuning.turret_beam_half_width * 0.35
	if _beam != null:
		_beam.aim(here, reach, half_width)
		_beam.set_regime(2.4 if firing else 0.35, 0.0 if firing else 1.0)
	_set_eye(2.6 if firing else 1.6)
	if not firing or _player == null:
		return
	# ⚠️ `Beam.hits` s'applique au SEGMENT, pas au bout : la tourelle brûle ce qui traverse, et
	# c'est ce qui rend le verrouillage lisible — on voit où il ne faut pas passer.
	if Beam.hits(here, reach, tuning.turret_beam_half_width, _player.plane_position, 0.25):
		_player.take_contact_damage(tuning.turret_damage)

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

## La tourelle est-elle dans sa fenêtre de tir, à cette position du plan ? ⚠️ STATIQUE ET PURE :
## c'est ce qui permet de tester la fenêtre sans monter le niveau, et donc de la tester du tout.
static func engaged_at(plane_y: float, visible_span: float) -> bool:
	return absf(plane_y) <= visible_span * 0.5
