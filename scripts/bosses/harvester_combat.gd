class_name HarvesterCombat
extends Node
## Le combat du Choir Harvester : trois appendices destructibles, un iris, un noyau.
##
## LA BOUCLE — les trois appendices attaquent et protègent le corps. Détruits, ils
## cessent d'attaquer et repoussent. Les trois à terre en même temps ouvrent l'iris et
## exposent le noyau ; le premier qui se reforme le referme. Trois fenêtres tuent le
## boss.
##
## COMPOSITION, PAS HÉRITAGE — `BossController` reste le boss générique (entrée,
## déplacement, roulis, PV, signaux HUD, mort) et sert toujours le Pale Leviathan. Ce
## module est un nœud enfant de la scène du Harvester : il lui prend la main sur les
## attaques (`external_attacks`) et sur la vulnérabilité, rien d'autre.
##
## SEUL ÉCRIVAIN DES POSES — un appendice est tour à tour plié par sa destruction et
## braqué par sa visée. Les deux rotations sont composées ICI, en un seul endroit ;
## `HarvesterLimb` ne pose rien, il ne fait que dire où il en est.
##
## Testable sans arbre ni rendu : `tick()` est public et `setup()` accepte une coque
## nulle. `_physics_process` ne fait que déléguer.

## Contrat de noms de la coque (BRIEF-0039). Racine d'abord, puis articulations.
const SCYTHE_NODES: PackedStringArray = ["Arm_Scythe", "Scythe_Mid", "Scythe_Blade"]
const CLAW_NODES: PackedStringArray = ["Arm_Claw", "Claw_Head_1", "Claw_Head_2", "Claw_Head_3"]
const CANNON_NODES: PackedStringArray = ["Arm_Cannon", "Cannon_Barrel"]
const CLAW_MUZZLES: PackedStringArray = ["Muzzle_Claw_1", "Muzzle_Claw_2", "Muzzle_Claw_3"]
const PETAL_COUNT := 5

const KIND_SCYTHE := &"scythe"
const KIND_CLAW := &"claw"
const KIND_CANNON := &"cannon"

## Phases d'une attaque télégraphiée. `WINDUP` est le télégraphe : c'est lui qui rend
## le coup esquivable, et le supprimer rendrait l'attaque imparable.
enum Attack { READY, WINDUP, ACTIVE, RECOVER }

signal iris_opened
signal iris_closed
signal limb_destroyed(kind: StringName)
signal limb_restored(kind: StringName)

@export var tuning: HarvesterTuning
## Projectile de la griffe. Les deux autres appendices ne tirent pas de balle.
@export var projectile: ProjectileData

var _boss: BossController
var _hull: Node3D
var _bullet_manager: BulletManager
var _player: PlayerFighterController
var _limbs: Array[HarvesterLimb] = []
var _beam: Beam

## Pétales de l'iris et leur axe de charnière, calculé une fois au montage.
var _petals: Array[Node3D] = []
var _petal_rest: Array[Basis] = []
var _petal_axes: Array[Vector3] = []
var _iris_open: bool = false
var _iris_ratio: float = 0.0

var _claw_timer: float = 0.0
var _claw_sweep: float = 0.0
var _scythe_phase: Attack = Attack.READY
var _scythe_elapsed: float = 0.0
var _scythe_lock: Vector2 = Vector2.ZERO
var _cannon_phase: Attack = Attack.READY
var _cannon_elapsed: float = 0.0
var _cannon_lock: Vector2 = Vector2.ZERO
var _age: float = 0.0

func _ready() -> void:
	_boss = get_parent() as BossController
	if _boss == null:
		push_error("[Harvester] le module doit etre enfant d'un BossController")
		return
	if tuning == null:
		push_error("[Harvester] aucun HarvesterTuning : le combat n'a aucun reglage")
		return
	_boss.external_attacks = true
	_boss.began.connect(_on_boss_began)
	# Une cible d'appendice laissée dans le gestionnaire continuerait d'absorber les
	# balles sur un cadavre — le boss vaincu resterait un mur invisible.
	_boss.defeated.connect(_on_boss_defeated)
	set_physics_process(false)

func _on_boss_defeated(_world_position: Vector3) -> void:
	set_physics_process(false)
	release()

func _on_boss_began(bullet_manager: BulletManager, player: PlayerFighterController) -> void:
	setup(_boss.hull(), bullet_manager, player)
	set_physics_process(true)

## Montage. `hull` peut être nul : les tests font tourner toute la boucle sans coque,
## et un appendice sans nœud à poser reste un appendice qui vit, meurt et repousse.
func setup(hull: Node3D, bullet_manager: BulletManager, player: PlayerFighterController) -> void:
	_hull = hull
	_bullet_manager = bullet_manager
	_player = player
	_build_limbs()
	_bind_iris()
	_build_beam()
	_close_iris(true)
	# Hook de verification : `++ --harvester-window` abat les trois appendices d'entree
	# de jeu, pour que la fenetre — le moment du combat — soit capturable sans jouer
	# plusieurs minutes. Meme raison que `--victory-demo` : un ecran qu'on n'atteint
	# qu'en fin d'arc ne se REGARDE jamais (ADR-0006).
	if "--harvester-window" in OS.get_cmdline_user_args():
		for limb in _limbs:
			limb.apply_damage(limb.max_health)

func _build_limbs() -> void:
	_limbs.clear()
	for entry: Array in [[KIND_SCYTHE, SCYTHE_NODES], [KIND_CLAW, CLAW_NODES],
			[KIND_CANNON, CANNON_NODES]]:
		var limb := HarvesterLimb.make(entry[0], _hull, entry[1],
			tuning.limb_health, tuning.limb_hitbox_radius, Callable(self, "_on_limb_hit").bind(entry[0]))
		_limbs.append(limb)
	# ⚠️ ORDRE D'ENREGISTREMENT CRITIQUE. `BulletManager._resolve_hits` parcourt les
	# cibles dans l'ordre où elles ont été enregistrées et CONSOMME la balle sur la
	# première qui la réclame. Les appendices doivent donc passer AVANT la cible de
	# corps du boss : dans l'autre sens, un tir ajusté sur un bras serait absorbé par
	# le corps — et pendant l'iris ouvert, il soignerait le noyau à sa place.
	# `BossController.begin()` émet `began` avant d'enregistrer la sienne, exprès.
	if _bullet_manager != null:
		for limb in _limbs:
			_bullet_manager.register_target(limb.target)

## L'axe de charnière de chaque pétale se DÉDUIT de sa position, il n'est pas saisi :
## `ak.moving_part()` pose l'origine sur la charnière sans réorienter les axes locaux,
## si bien qu'un simple `rotation.x` ferait tourner les cinq pétales autour du même
## axe au lieu de leur propre bord. L'axe d'un pétale est la tangente du cercle en son
## point de charnière.
func _bind_iris() -> void:
	_petals.clear()
	_petal_rest.clear()
	_petal_axes.clear()
	if _hull == null:
		return
	for i in PETAL_COUNT:
		var petal := _hull.get_node_or_null(NodePath("Petal_%02d" % (i + 1))) as Node3D
		if petal == null:
			push_error("[Harvester] coque sans 'Petal_%02d'" % (i + 1))
			continue
		_petals.append(petal)
		_petal_rest.append(petal.transform.basis)
		var radial := Vector3(petal.position.x, 0.0, petal.position.z)
		if radial.length_squared() < 0.0001:
			# Un pétale pile sur l'axe n'a pas de direction radiale : on lui donne un
			# axe arbitraire plutôt que de propager un NaN dans sa base.
			radial = Vector3.FORWARD
		_petal_axes.append(Vector3.UP.cross(radial.normalized()).normalized())

## Le faisceau est un nœud de RENDU : il n'existe pas hors de l'arbre. Les tests
## pilotent toute la boucle du canon sans lui — `_show_beam` et `_burn` le
## null-gardent, et la portée est éprouvée à part par `test_beam_geometry.gd`, sur la
## fonction statique. Le construire quand même laisserait des RID de maillage à la
## sortie du runner.
func _build_beam() -> void:
	if _beam != null or not is_inside_tree():
		return
	_beam = Beam.make()
	add_child(_beam)

# --- Boucle -------------------------------------------------------------------

func _physics_process(delta: float) -> void:
	tick(delta)

## Toute la logique du combat. Publique et sans dépendance à l'arbre : les tests la
## pilotent directement, ce qui rend vérifiable une boucle qu'aucune capture d'écran
## ne pourrait couvrir (il faut plusieurs minutes de jeu pour voir trois cycles).
func tick(delta: float) -> void:
	if tuning == null:
		return
	_age += delta
	var origin := _boss.plane_position if _boss != null else Vector2.ZERO

	for limb in _limbs:
		# Le retour en service se DÉTECTE ici plutôt que d'être annoncé par
		# `HarvesterLimb` : la pièce ne connaît que son propre minuteur, et lui faire
		# porter un signal l'obligerait à hériter de Node pour rien.
		var was_up := limb.is_up()
		limb.tick(delta, tuning)
		if not was_up and limb.is_up():
			limb_restored.emit(limb.kind)
		limb.target.position = _limb_plane_position(limb, origin)

	_update_iris(delta)
	_run_claw(delta, origin)
	_run_scythe(delta, origin)
	_run_cannon(delta, origin)
	_pose_limbs()

## Où se trouve la zone de touche d'un appendice.
##
## ⚠️ SUR SES ARTICULATIONS, PAS SUR SON PIVOT. Le pivot d'un bras est son épaule,
## posée dans la carapace ; la lame de la faux vit à 2,9 m de là. Une zone de touche
## centrée sur l'épaule aurait mis le joueur dans la pire des situations : il tire sur
## ce qu'il voit — la lame, les têtes, le fût — et ne touche rien, sans que rien ne le
## lui dise. Signalé par la forge au §6 de son rapport (BRIEF-0039).
##
## On prend la MOYENNE des articulations : elle suit l'animation gratuitement (les
## positions sont globales) et couvre le corps utile du bras plutôt qu'un seul point.
##
## Hors de l'arbre — donc en test — on retombe sur le centre du boss : c'est
## exactement la configuration défavorable que `test_a_bullet_reaches_a_limb_before_the_body`
## veut éprouver.
func _limb_plane_position(limb: HarvesterLimb, origin: Vector2) -> Vector2:
	if limb.joints.is_empty():
		if limb.root == null or not limb.root.is_inside_tree():
			return origin
		return GameplayPlane.to_plane(limb.root.global_position)
	var sum := Vector3.ZERO
	var counted := 0
	for joint in limb.joints:
		if not joint.is_inside_tree():
			continue
		sum += joint.global_position
		counted += 1
	if counted == 0:
		return origin
	return GameplayPlane.to_plane(sum / float(counted))

# --- Iris ---------------------------------------------------------------------

func _update_iris(delta: float) -> void:
	var all_down := true
	for limb in _limbs:
		if limb.is_up():
			all_down = false
			break
	if all_down and not _iris_open:
		_open_iris()
	elif not all_down and _iris_open:
		_close_iris(false)

	var speed := 1.0 / (tuning.iris_open_time if _iris_open else tuning.iris_close_time)
	var goal := 1.0 if _iris_open else 0.0
	_iris_ratio = move_toward(_iris_ratio, goal, speed * delta)
	_pose_iris()

func _open_iris() -> void:
	_iris_open = true
	if _boss != null:
		_boss.vulnerable = true
	iris_opened.emit()

func _close_iris(silent: bool) -> void:
	_iris_open = false
	if _boss != null:
		_boss.vulnerable = false
	if not silent:
		iris_closed.emit()

func _pose_iris() -> void:
	var angle := deg_to_rad(tuning.iris_open_deg) * _iris_ratio
	for i in _petals.size():
		_petals[i].transform.basis = _petal_rest[i] * Basis(_petal_axes[i], angle)

func is_iris_open() -> bool:
	return _iris_open

# --- Griffe a trois tetes : la pression de fond -------------------------------

func _run_claw(delta: float, origin: Vector2) -> void:
	var limb := _limb(KIND_CLAW)
	if limb == null or not limb.is_up():
		return
	# Balayage de visée continu : le bras vit même entre deux salves.
	_claw_sweep = sin(_age * 1.7)
	_claw_timer -= delta
	if _claw_timer > 0.0:
		return
	_claw_timer = tuning.claw_fire_interval
	if _bullet_manager == null or projectile == null:
		return
	var aim := _aim_from(origin)
	# Une salve par tête : trois traits qui convergent, pas une gerbe qui sort du
	# centre. C'est ce que la planche montre — trois yeux, trois bouches.
	for i in CLAW_MUZZLES.size():
		var muzzle := origin + _muzzle_offset(CLAW_MUZZLES[i])
		var spread := deg_to_rad(9.0 * (i - 1))
		_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, muzzle,
			aim.rotated(spread), projectile)

# --- Faux : estoc telegraphie -------------------------------------------------

func _run_scythe(delta: float, origin: Vector2) -> void:
	var limb := _limb(KIND_SCYTHE)
	if limb == null or not limb.is_up():
		_scythe_phase = Attack.READY
		_scythe_elapsed = 0.0
		return
	_scythe_elapsed += delta
	match _scythe_phase:
		Attack.READY:
			# ⚠️ La cible est VERROUILLÉE au début du réarme. Suivre le joueur pendant
			# la seconde de télégraphe ferait un coup imparable : le télégraphe ne
			# vaut que s'il annonce un point fixe.
			_scythe_lock = _player.plane_position if _player != null else origin + Vector2(0.0, -4.0)
			_enter_scythe(Attack.WINDUP)
		Attack.WINDUP:
			if _scythe_elapsed >= tuning.scythe_windup_time:
				_enter_scythe(Attack.ACTIVE)
		Attack.ACTIVE:
			_strike_scythe()
			if _scythe_elapsed >= tuning.scythe_strike_time:
				_enter_scythe(Attack.RECOVER)
		Attack.RECOVER:
			if _scythe_elapsed >= tuning.scythe_recover_time:
				_enter_scythe(Attack.READY)

func _enter_scythe(phase: Attack) -> void:
	_scythe_phase = phase
	_scythe_elapsed = 0.0

func _strike_scythe() -> void:
	if _player == null:
		return
	if _player.plane_position.distance_to(_scythe_lock) <= tuning.scythe_reach_radius:
		_player.take_contact_damage(tuning.scythe_damage)

## Part d'avancement du réarme, de 0 à 1. Sert la pose et, plus tard, le télégraphe
## visuel (traînée de lame de la planche).
func scythe_windup_ratio() -> float:
	if _scythe_phase != Attack.WINDUP:
		return 1.0 if _scythe_phase == Attack.ACTIVE else 0.0
	return clampf(_scythe_elapsed / maxf(tuning.scythe_windup_time, 0.0001), 0.0, 1.0)

# --- Canon : charge puis faisceau ---------------------------------------------

func _run_cannon(delta: float, origin: Vector2) -> void:
	var limb := _limb(KIND_CANNON)
	if limb == null or not limb.is_up():
		_cannon_phase = Attack.READY
		_cannon_elapsed = 0.0
		if _beam != null:
			_beam.extinguish()
		return
	_cannon_elapsed += delta
	var muzzle := origin + _muzzle_offset("Muzzle_Cannon")
	match _cannon_phase:
		Attack.READY:
			_cannon_lock = _player.plane_position if _player != null else origin + Vector2(0.0, -6.0)
			_enter_cannon(Attack.WINDUP)
		Attack.WINDUP:
			# Le télégraphe est le MÊME nœud que le faisceau, en fin et en sourdine.
			_show_beam(muzzle, 0.14, 0.35, 1.0)
			if _cannon_elapsed >= tuning.cannon_charge_time:
				_enter_cannon(Attack.ACTIVE)
		Attack.ACTIVE:
			_show_beam(muzzle, tuning.beam_half_width, 2.4, 0.0)
			_burn(muzzle)
			if _cannon_elapsed >= tuning.cannon_beam_time:
				_enter_cannon(Attack.RECOVER)
		Attack.RECOVER:
			if _beam != null:
				_beam.extinguish()
			if _cannon_elapsed >= tuning.cannon_recover_time:
				_enter_cannon(Attack.READY)

func _enter_cannon(phase: Attack) -> void:
	_cannon_phase = phase
	_cannon_elapsed = 0.0

## Le faisceau part de la bouche et file jusqu'au BORD du terrain, dans la direction
## verrouillée : il traverse, il ne s'arrête pas au joueur.
func _beam_end(muzzle: Vector2) -> Vector2:
	var direction := (_cannon_lock - muzzle)
	if direction.length_squared() < 0.0001:
		direction = Vector2(0.0, -1.0)
	return muzzle + direction.normalized() * 34.0

func _show_beam(muzzle: Vector2, half_width: float, energy: float, pulse: float) -> void:
	if _beam == null:
		return
	_beam.aim(muzzle, _beam_end(muzzle), half_width)
	_beam.set_regime(energy, pulse)

func _burn(muzzle: Vector2) -> void:
	if _player == null:
		return
	if Beam.hits(muzzle, _beam_end(muzzle), tuning.beam_half_width,
			_player.plane_position, 0.25):
		_player.take_contact_damage(tuning.beam_damage)

func cannon_charge_ratio() -> float:
	if _cannon_phase != Attack.WINDUP:
		return 1.0 if _cannon_phase == Attack.ACTIVE else 0.0
	return clampf(_cannon_elapsed / maxf(tuning.cannon_charge_time, 0.0001), 0.0, 1.0)

# --- Poses --------------------------------------------------------------------

## Un seul endroit compose repli et visée. Les angles restent sous les plafonds
## mécaniques mesurés par la forge (BRIEF-0039).
func _pose_limbs() -> void:
	for limb in _limbs:
		if limb.root == null:
			continue
		var deploy := limb.deploy_ratio(tuning)
		# Replié : le bras se couche contre la coque. C'est la lecture « il est
		# tombé » — un appendice détruit qui resterait tendu ne dirait rien.
		var fold := (1.0 - deploy) * deg_to_rad(-70.0)
		match limb.kind:
			KIND_CLAW:
				limb.root.rotation = Vector3(fold,
					deg_to_rad(tuning.claw_sweep_deg) * _claw_sweep * deploy, 0.0)
				var converge := deg_to_rad(tuning.claw_head_converge_deg) * deploy
				for i in limb.joints.size():
					limb.joints[i].rotation.y = converge * (i - 1)
			KIND_SCYTHE:
				_pose_scythe(limb, deploy, fold)
			KIND_CANNON:
				limb.root.rotation = Vector3(fold, 0.0, 0.0)
				if not limb.joints.is_empty():
					# Recul au tir : le fût rentre pendant le faisceau, pas pendant
					# la charge — c'est le départ du coup qui doit se sentir.
					var recoil := tuning.cannon_recoil if _cannon_phase == Attack.ACTIVE else 0.0
					limb.joints[0].position.z = recoil

## La faux se lève pendant le réarme (la pose exacte de la planche : lame haute,
## arquée au-dessus du corps) puis fend d'un coup.
func _pose_scythe(limb: HarvesterLimb, deploy: float, fold: float) -> void:
	var raise := 0.0
	match _scythe_phase:
		Attack.WINDUP:
			raise = scythe_windup_ratio()
		Attack.ACTIVE:
			# De haut levé à abattu, en une fraction de seconde.
			raise = 1.0 - clampf(_scythe_elapsed / maxf(tuning.scythe_strike_time, 0.0001), 0.0, 1.0)
			raise = raise * 2.0 - 1.0
		Attack.RECOVER:
			raise = lerpf(-1.0, 0.0,
				clampf(_scythe_elapsed / maxf(tuning.scythe_recover_time, 0.0001), 0.0, 1.0))
	var swing := deg_to_rad(55.0) * raise * deploy
	limb.root.rotation = Vector3(fold + swing * 0.45, 0.0, 0.0)
	if limb.joints.size() > 0:
		limb.joints[0].rotation.x = swing * 0.35
	if limb.joints.size() > 1:
		limb.joints[1].rotation.x = swing * 0.20

# --- Dégâts et accès ----------------------------------------------------------

func _on_limb_hit(damage: float, kind: StringName) -> void:
	var limb := _limb(kind)
	if limb == null:
		return
	if limb.apply_damage(damage):
		limb_destroyed.emit(kind)

func _limb(kind: StringName) -> HarvesterLimb:
	for limb in _limbs:
		if limb.kind == kind:
			return limb
	return null

func limbs() -> Array[HarvesterLimb]:
	return _limbs

## Nombre d'appendices encore en service — ce que le HUD affiche.
func limbs_up() -> int:
	var count := 0
	for limb in _limbs:
		if limb.is_up():
			count += 1
	return count

func _muzzle_offset(point_name: String) -> Vector2:
	if _hull == null:
		return Vector2.ZERO
	var node := _hull.get_node_or_null(NodePath(point_name)) as Node3D
	if node == null:
		return Vector2.ZERO
	var local: Vector3 = _hull.transform * node.position
	return Vector2(local.x, -local.z)

func _aim_from(origin: Vector2) -> Vector2:
	if _player == null:
		return Vector2(0.0, -1.0)
	var direction := _player.plane_position - origin
	return direction.normalized() if direction.length_squared() > 0.0001 else Vector2(0.0, -1.0)

## Libère les cibles enregistrées. Appelé à la mort du boss : une cible d'appendice
## laissée dans le gestionnaire continuerait d'absorber des balles sur un cadavre.
func release() -> void:
	if _bullet_manager == null:
		return
	for limb in _limbs:
		limb.target.enabled = false
		_bullet_manager.unregister_target(limb.target)
	if _beam != null:
		_beam.extinguish()
