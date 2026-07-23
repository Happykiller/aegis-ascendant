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
const PETAL_COUNT := 5

const KIND_SCYTHE := &"scythe"
const KIND_CLAW := &"claw"
const KIND_CANNON := &"cannon"

## L'ordre d'affichage des jauges, et la seule source de l'indice porté par
## `limb_gauge_changed`. Il vaut aussi l'ordre de construction : les deux se lisent au
## même endroit, donc ils ne peuvent pas diverger en silence.
const LIMB_ORDER: Array[StringName] = [KIND_SCYTHE, KIND_CLAW, KIND_CANNON]

## Phases d'une attaque télégraphiée. `WINDUP` est le télégraphe : c'est lui qui rend
## le coup esquivable, et le supprimer rendrait l'attaque imparable.
enum Attack { READY, WINDUP, ACTIVE, RECOVER }

signal iris_opened
signal iris_closed
signal limb_destroyed(kind: StringName)
signal limb_restored(kind: StringName)
## Jauge d'un appendice : son indice dans `LIMB_ORDER`, sa part de structure et s'il
## est encore en service.
##
## ÉVÉNEMENTIEL, PAS SONDÉ. Le HUD n'a besoin de la valeur qu'aux trois moments où elle
## change — un impact, une chute, un retour en service. Le temps de repousse, lui, se lit
## sur le modèle : l'appendice se redéploie à vue (cf. `FighterHud._build_limb_pips`).
signal limb_gauge_changed(index: int, ratio: float, alive: bool)

@export var tuning: HarvesterTuning
## Projectile de la griffe. Les deux autres appendices ne tirent pas de balle.
@export var projectile: ProjectileData

var _boss: BossController
var _hull: Node3D
var _bullet_manager: BulletManager
var _player: PlayerFighterController
var _limbs: Array[HarvesterLimb] = []
var _beam: Beam
## Télégraphe de l'estoc : le MÊME objet que le faisceau du canon, en régime « ligne de
## visée ». Deux instances et non deux classes — la faux et le canon annoncent tous deux
## un point, et `Beam` porte déjà les deux régimes (`beam.gd:5-7`).
var _scythe_trace: Beam

## Pétales de l'iris et leur axe de charnière, calculé une fois au montage.
var _petals: Array[Node3D] = []
var _petal_rest: Array[Basis] = []
var _petal_axes: Array[Vector3] = []
var _iris_open: bool = false
var _iris_ratio: float = 0.0

## Bouche du canon, résolue UNE fois. `NodePath(String)` alloue et reparse à chaque
## appel : le faire par image pour un nœud qui ne change jamais coûtait 60 recherches
## d'arbre par seconde. `BossController._read_muzzles()` résout les siennes dans
## `_ready` — c'est le même précédent, dans le fichier voisin.
var _cannon_muzzle: Node3D

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
		# ⚠️ On REND l'armement au boss générique. Sans cela le module ne monte pas,
		# `external_attacks` reste à `true` (il est déclaré dans la scène), le boss ne
		# tire donc rien du tout, et `vulnerable` garde son défaut `true` : le
		# mini-boss devient un disque inoffensif tuable en une passe, avec trois
		# pastilles éteintes au HUD pour parachever le mensonge. Dégrader vers
		# l'ancien comportement vaut mieux que dégrader vers l'absence de combat.
		push_error("[Harvester] aucun HarvesterTuning : retour aux motifs generiques")
		_boss.external_attacks = false
		set_physics_process(false)
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
	_bind_muzzles()
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
	# Un remontage laissait les cibles du tour précédent dans le gestionnaire, encore
	# actives, callback vivant, position figée : le « mur invisible » exact contre
	# lequel `release()` a été écrit. La protection existait d'un côté du montage,
	# pas de l'autre.
	release()
	_limbs.clear()
	# ⚠️ Trois appels explicites, et non une boucle sur un tableau de paires. La
	# version précédente passait des `Variant` à des paramètres `StringName` et
	# `PackedStringArray` : intervertir les deux colonnes, ou coller `CANNON_NODES`
	# sous `KIND_CLAW`, compilait sans un mot et ne se manifestait qu'à l'exécution
	# sous forme de bras inertes — exactement le mode de panne qu'un brief entier
	# vient de débusquer.
	_limbs.append(_make_limb(KIND_SCYTHE, SCYTHE_NODES))
	_limbs.append(_make_limb(KIND_CLAW, CLAW_NODES))
	_limbs.append(_make_limb(KIND_CANNON, CANNON_NODES))
	assert(_limbs.size() == LIMB_ORDER.size(), "LIMB_ORDER doit couvrir tous les appendices")
	# ⚠️ ORDRE D'ENREGISTREMENT CRITIQUE. `BulletManager._resolve_hits` parcourt les
	# cibles dans l'ordre où elles ont été enregistrées et CONSOMME la balle sur la
	# première qui la réclame. Les appendices doivent donc passer AVANT la cible de
	# corps du boss : dans l'autre sens, un tir ajusté sur un bras serait absorbé par
	# le corps — et pendant l'iris ouvert, il soignerait le noyau à sa place.
	# `BossController.begin()` émet `began` avant d'enregistrer la sienne, exprès.
	if _bullet_manager != null:
		for limb in _limbs:
			_bullet_manager.register_target(limb.target)

func _make_limb(kind: StringName, nodes: PackedStringArray) -> HarvesterLimb:
	return HarvesterLimb.make(kind, _hull, nodes, tuning.limb_health,
		tuning.limb_hitbox_radius, Callable(self, "_on_limb_hit").bind(kind))

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
func _bind_muzzles() -> void:
	_cannon_muzzle = null
	if _hull == null:
		return
	_cannon_muzzle = _hull.get_node_or_null(NodePath("Muzzle_Cannon")) as Node3D
	if _cannon_muzzle == null:
		push_error("[Harvester] coque sans 'Muzzle_Cannon' (contrat BRIEF-0039)")

func _build_beam() -> void:
	if _beam != null or not is_inside_tree():
		return
	_beam = Beam.make()
	add_child(_beam)
	_scythe_trace = Beam.make()
	_scythe_trace.name = "ScytheTrace"
	add_child(_scythe_trace)

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
			_emit_gauge(limb)
		limb.target.position = _limb_plane_position(limb, origin)

	_update_iris(delta)
	_run_claw(delta, origin)
	_run_scythe(delta, origin)
	_run_cannon(delta, origin)
	_pose_limbs()

## Où se trouve la zone de touche d'un appendice : sur son CENTRE VISUEL.
##
## ⚠️ Pas sur son pivot — l'épaule d'un bras est noyée dans la carapace, la lame de la
## faux vit à 2,9 m de là, et le joueur tire sur ce qu'il voit. Pas sur la moyenne des
## articulations non plus : elle retombait sur le pivot pour le canon, dont l'unique
## articulation partage la position de son parent.
##
## Hors de l'arbre — donc en test — on retombe sur le centre du boss : c'est
## exactement la configuration défavorable que
## `test_a_bullet_reaches_a_limb_before_the_body` veut éprouver.
func _limb_plane_position(limb: HarvesterLimb, origin: Vector2) -> Vector2:
	if not limb.has_visual():
		return origin
	return GameplayPlane.to_plane(limb.visual_center())

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
	var next := move_toward(_iris_ratio, goal, speed * delta)
	# ⚠️ On ne repose l'iris QUE s'il a bougé. Il est immobile pendant l'essentiel du
	# combat, et chaque passe coûtait cinq `Basis` et cinq lire-modifier-réécrire sur
	# `.transform` — des types de 36 et 48 octets, qui débordent le tampon inline d'un
	# Variant et allouent dans son pool. Soixante fois par seconde, pour rien.
	if is_equal_approx(next, _iris_ratio):
		return
	_iris_ratio = next
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
	#
	# ⚠️ Les balles partent des TÊTES, pas des marqueurs `Muzzle_Claw_*`. Ceux-ci sont
	# des nœuds racines du `.glb`, frères du bras et non ses enfants : ils sont donc
	# immobiles, alors que le bras balaie ±32° en continu. À fond de balayage, les
	# traits sortaient d'un point situé à côté des têtes qui les crachent.
	for i in limb.joints.size():
		var head := limb.joints[i]
		var muzzle := GameplayPlane.to_plane(head.global_position) if head.is_inside_tree() \
			else origin
		var spread := deg_to_rad(9.0 * (i - 1))
		_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, muzzle,
			aim.rotated(spread), projectile)

# --- Faux : estoc telegraphie -------------------------------------------------

## L'ESTOC DÉPLACE LE CORPS. La première version agitait la lame en haut de l'écran et
## comparait la position du joueur à un point abstrait verrouillé une seconde plus tôt :
## rien à l'écran ne reliait le geste au dégât, et l'attaque passait pour inexistante.
## Le boss se fend maintenant sur le point verrouillé, et ce sont les allées et venues
## de la LAME qui blessent.
func _run_scythe(delta: float, origin: Vector2) -> void:
	var limb := _limb(KIND_SCYTHE)
	if limb == null or not limb.is_up():
		# Bras à terre en pleine charge : on rend la main au boss, sinon il resterait
		# figé sur sa destination pour toujours — un boss immobile et sans faux.
		if _scythe_phase == Attack.ACTIVE:
			_release_lunge()
		_scythe_phase = Attack.READY
		_scythe_elapsed = 0.0
		return
	_scythe_elapsed += delta
	match _scythe_phase:
		Attack.READY:
			# ⚠️ La cible est VERROUILLÉE au début du réarme. Suivre le joueur pendant
			# la seconde de télégraphe ferait un coup imparable : le télégraphe ne
			# vaut que s'il annonce un point fixe.
			_scythe_lock = _lunge_target(origin)
			_enter_scythe(Attack.WINDUP)
		Attack.WINDUP:
			# Le télégraphe : une ligne fine et battante, du corps au point visé. C'est
			# elle qui rend l'estoc esquivable — sans elle, une masse de dix mètres
			# tombe sur le joueur sans préavis.
			_trace_scythe(origin)
			if _scythe_elapsed >= tuning.scythe_windup_time:
				_enter_scythe(Attack.ACTIVE)
				# ⚠️ La charge part DANS L'IMAGE de la bascule, pas à la suivante.
				# Déclenchée depuis le corps de la branche `ACTIVE`, elle perdait une
				# image — invisible à l'œil, mais elle rendait l'état « en train de
				# charger » et « le corps bouge » désaccordés pendant une frame, ce
				# qu'un test lit comme une contradiction et un joueur comme un à-coup.
				_begin_lunge()
		Attack.ACTIVE:
			_strike_scythe(origin)
			if _scythe_elapsed >= tuning.scythe_strike_time:
				_release_lunge()
				_enter_scythe(Attack.RECOVER)
		Attack.RECOVER:
			if _scythe_elapsed >= tuning.scythe_recover_time:
				_enter_scythe(Attack.READY)

## Où le corps consent à se fendre : la position du joueur, mais jamais plus bas que
## `scythe_lunge_reach` sous sa position de croisière. Sans ce plafond, le boss finit
## collé au bord bas, sur le joueur, qui n'a plus d'espace pour esquiver la suivante.
func _lunge_target(origin: Vector2) -> Vector2:
	var goal := _player.plane_position if _player != null else origin + Vector2(0.0, -4.0)
	goal.y = maxf(goal.y, origin.y - tuning.scythe_lunge_reach)
	return goal

func _begin_lunge() -> void:
	if _scythe_trace != null:
		_scythe_trace.extinguish()
	if _boss != null:
		_boss.drive_toward(_scythe_lock, tuning.scythe_lunge_speed)

func _release_lunge() -> void:
	if _boss != null:
		_boss.release_drive()

func _trace_scythe(origin: Vector2) -> void:
	if _scythe_trace == null:
		return
	_scythe_trace.aim(origin, _scythe_lock, 0.12)
	_scythe_trace.set_regime(0.5, 1.0)

func _enter_scythe(phase: Attack) -> void:
	_scythe_phase = phase
	_scythe_elapsed = 0.0

## ⚠️ LES DÉGÂTS PARTENT DE LA LAME, pas du point verrouillé. Le verrou dit où le boss
## VA ; ce qui tranche, c'est `Scythe_Blade` là où il se trouve réellement, roulis et
## plongeon compris. Hors de l'arbre — donc en test, où le module tourne sans coque — on
## retombe sur le corps du boss, qui est bien l'objet qui se déplace.
func _strike_scythe(origin: Vector2) -> void:
	if _player == null:
		return
	var blade := origin
	var limb := _limb(KIND_SCYTHE)
	if limb != null and not limb.joints.is_empty():
		var tip: Node3D = limb.joints[limb.joints.size() - 1]
		if tip.is_inside_tree():
			blade = GameplayPlane.to_plane(tip.global_position)
	if _player.plane_position.distance_to(blade) <= tuning.scythe_reach_radius:
		_player.take_contact_damage(tuning.scythe_damage)

## Le corps est-il en train de se fendre ? Sert au test, et au HUD s'il veut un jour
## annoncer la charge autrement que par la ligne de télégraphe.
func is_lunging() -> bool:
	return _scythe_phase == Attack.ACTIVE

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
	var muzzle := origin
	if _cannon_muzzle != null and _cannon_muzzle.is_inside_tree():
		muzzle = GameplayPlane.to_plane(_cannon_muzzle.global_position)
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
	var fell := limb.apply_damage(damage)
	# La jauge d'abord : le HUD doit montrer la barre vidée AVANT que le niveau ne joue
	# l'explosion sur `limb_destroyed`, sinon la barre se vide après le boum.
	_emit_gauge(limb)
	if fell:
		limb_destroyed.emit(kind)

## Pousse la jauge d'un appendice. Trois scalaires, aucune allocation — c'est appelé sur
## chaque balle qui touche un bras, soit dix fois par seconde en salve soutenue.
func _emit_gauge(limb: HarvesterLimb) -> void:
	var index := LIMB_ORDER.find(limb.kind)
	if index < 0:
		return
	limb_gauge_changed.emit(index, limb.health_ratio(), limb.is_up())

## Publie les trois jauges d'un coup. Appelé au montage : sans lui, le bandeau
## afficherait trois barres vides sur un boss intact jusqu'au premier impact.
func publish_gauges() -> void:
	for limb in _limbs:
		_emit_gauge(limb)

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

func _aim_from(origin: Vector2) -> Vector2:
	if _player == null:
		return Vector2(0.0, -1.0)
	var direction := _player.plane_position - origin
	return direction.normalized() if direction.length_squared() > 0.0001 else Vector2(0.0, -1.0)

## Libère les cibles enregistrées. Appelé à la mort du boss : une cible d'appendice
## laissée dans le gestionnaire continuerait d'absorber des balles sur un cadavre.
func release() -> void:
	# ⚠️ AVANT la sortie anticipée sur `_bullet_manager` : un boss tué en plein estoc
	# garderait sinon la main sur son déplacement et sa ligne de télégraphe tendue par
	# dessus l'explosion.
	_release_lunge()
	if _scythe_trace != null:
		_scythe_trace.extinguish()
	if _beam != null:
		_beam.extinguish()
	if _bullet_manager == null:
		return
	for limb in _limbs:
		limb.target.enabled = false
		_bullet_manager.unregister_target(limb.target)
