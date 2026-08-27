class_name PlayerFighterController
extends Node3D
## Player fighter: arcade movement on the logical 2D plane (spec §7.3, §16.2).
## The logical position is authoritative; the 3D node only projects it.
## Visual banking lives on VisualRoot and never affects the hitbox.

## Logical "up the screen" direction (+y logical = -Z world).
const DIR_UP := Vector2(0.0, 1.0)

## Le cap du chasseur dans le plan. Il ne pivote JAMAIS — c'est la grammaire du genre
## (`LOI-SYS-07` : on vise en se déplaçant) — donc c'est toujours `DIR_UP`. Exposé plutôt
## qu'écrit en dur chez les appelants pour qu'un jour où une coque banquerait, un seul
## endroit change.
func plane_forward() -> Vector2:
	return DIR_UP

## Emitted whenever the shield value changes (HUD).
signal shield_changed(ratio: float, current: float, maximum: float)
## Emitted when a life is lost; `lives` is the remaining count.
signal lives_changed(lives: int)
## Emitted when the player is hit (feedback: shake / sfx), with the world position.
signal hit_taken(world_position: Vector3)
## Emitted when a life is lost (explosion at position).
signal destroyed_at(world_position: Vector3)
## Emitted when the last life is gone (game over).
signal game_over
## Emitted when the fire power level changes (HUD / feedback).
signal power_changed(level: int)
## Emitted once per salvo, whatever the power level (audio cue).
signal fired

const MAX_POWER := 5

## Avance du point de naissance d'un bolt par rapport au centre du chasseur, en unités
## du plan. **Zéro, et c'est une décision** : voir `_shoot()`. Le porter à la position
## réelle du canon rouvrirait l'angle mort du tir rapproché, que `test_point_blank.gd`
## garde fermé.
const BOLT_FORWARD_OFFSET := 0.0

@export var stats: PlayerStats
@export var primary_projectile: ProjectileData
## Réglages de la plume d'échappement (ADR-0017). Nul = pas de plume : la coque vole
## quand même, moteur éteint — un écran de debug ne doit pas planter faute de VFX.
@export var plume: PlumeTuning
@export var bullet_manager_path: NodePath

var plane_position: Vector2 = Vector2(0.0, -5.0)
var _velocity: Vector2 = Vector2.ZERO
## Vitesse d'aspiration imposée de l'extérieur (le champ gravitique du Pale Leviathan,
## `GravityWell`). Le niveau la repose à chaque image tant qu'une phase l'exige ; on la
## CONSOMME dans `_physics_process` (remise à zéro), pour qu'une phase sans champ ne
## traîne pas la dernière valeur. Ce n'est pas un déplacement piloté : la commande du
## joueur reste pleine, l'aspiration s'y AJOUTE — c'est le sujet des phases 2 et 4.
var _external_pull: Vector2 = Vector2.ZERO
## Part de vitesse volée par ce qui s'accroche à la coque (`Leech Drone`). Même
## cycle de vie que l'aspiration : posée par les agresseurs, consommée en tête de
## `_physics_process`, quel que soit l'état du chasseur.
var _external_drag: float = 0.0
## Le freinage de l'image précédente, gardé pour l'AFFICHER. `consume_drag()` le remet à
## zéro par contrat ; sans cette copie, la plume ne saurait jamais qu'on freine.
var _shown_drag: float = 0.0
var _fire_timer: float = 0.0
## Demo/attract mode (cmdline `--demo`): auto-fire + gentle strafe, for captures
## and hands-off showcase. Never active in a normal run.
var _demo: bool = false
var _demo_time: float = 0.0
## Autopilot (docking, spec §6.5): control is taken over and the ship flies to a
## target on the plane; firing is suspended. Emits `autopilot_reached` on arrival.
var _autopilot: bool = false
var _autopilot_target: Vector2 = Vector2.ZERO
signal autopilot_reached

var _shield: PlayerShield = PlayerShield.new()
var _lives: int = 3
var _power_level: int = 1
var _alive: bool = true
var _respawn_timer: float = 0.0
var _target: BulletTarget
var _blink_time: float = 0.0

## Guns baked into the hull (ADR-0008), one per fire stream; the power level
## decides which of them fire. Every bolt leaves one of these — never a hard-coded
## offset (spec §9.1 ; cf. la référence, où le chasseur crache plusieurs flux
## parallèles depuis le nez, les ailes et les bouts d'aile).
const MUZZLE_NAMES: Array[String] = [
	"Muzzle_L", "Muzzle_R", "Muzzle_Wing_L", "Muzzle_Wing_R",
	"Muzzle_C", "Muzzle_Tip_L", "Muzzle_Tip_R",
]

## Plumes and muzzle flashes sit on the hull's attach points (ADR-0008),
## one per nozzle / per gun — never on hard-coded offsets.
##
## Les plumes d'échappement, une par tuyère. Tableau TYPÉ et préalloué : il est
## parcouru à chaque image de vol.
var _engine_plumes: Array[EnginePlume] = []
## Plane-space offset of each gun from the ship origin, read once from the hull.
var _muzzles: Dictionary[String, Vector2] = {}
## One flash quad per gun, shown only for the guns that fired this salvo.
var _muzzle_flashes: Dictionary[String, MeshInstance3D] = {}
var _muzzle_material: StandardMaterial3D
var _muzzle_timer: float = 0.0

@onready var _visual_root: Node3D = $VisualRoot
@onready var _hull: Node3D = $VisualRoot/Hull
## Volets et petales de tuyere (BRIEF-0033). Nul si la coque n'en a pas : une
## coque d'avant la reforge continue de voler, immobile.
var _flight: ShipFlight
@onready var _bullet_manager: BulletManager = get_node_or_null(bullet_manager_path) as BulletManager

func _ready() -> void:
	assert(stats != null, "PlayerFighterController requires a PlayerStats resource")
	for error in stats.validate():
		push_error("[PlayerFighter] invalid stats: %s" % error)
	if primary_projectile != null:
		for error in primary_projectile.validate():
			push_error("[PlayerFighter] invalid projectile: %s" % error)
	position = GameplayPlane.to_world(plane_position) + Vector3(0.0, plane_lift, 0.0)
	# Same detail sheet the title screen puts on its hulls: the .glb ships with no
	# texture (ADR-0008), so without this the fighter reads as smooth plastic in
	# combat while looking panelled on the menu. Safe on a shared imported material —
	# HullDetail duplicates before retexturing.
	HullDetail.apply(_hull)
	_cache_muzzles()
	_build_engine_plumes()
	_flight = ShipFlight.apply(_hull)
	_build_muzzle_flashes()
	_demo = "--demo" in OS.get_cmdline_user_args()
	# Debug/capture only: `++ --power=N` starts at power N to inspect the fuller
	# fire pattern (wing and wingtip guns) without collecting pickups first.
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--power="):
			_power_level = clampi(int(arg.trim_prefix("--power=")), 1, MAX_POWER)
	_shield.configure(stats.shield_max, stats.shield_regen_delay,
		stats.shield_regen_rate, stats.invuln_time)
	_lives = stats.lives
	if _bullet_manager != null:
		_target = BulletTarget.make(BulletManager.Team.PLAYER, stats.hitbox_radius,
			Callable(self, "_take_hit"))
		_target.position = plane_position
		_bullet_manager.register_target(_target)
	# Publish initial HUD state on the next idle frame (listeners connect after _ready).
	call_deferred("_emit_initial_state")

func _emit_initial_state() -> void:
	shield_changed.emit(_shield.ratio(), _shield.current, _shield.maximum)
	lives_changed.emit(_lives)
	power_changed.emit(_power_level)

func _physics_process(delta: float) -> void:
	# L'aspiration se CONSOMME ici, en tête et inconditionnellement, avant toute
	# sortie anticipée.
	#
	# ⚠️ Elle était consommée au milieu du déplacement libre, donc jamais pendant
	# l'appontage ni pendant la mort — deux chemins qui rendent la main plus haut.
	# Tant qu'un seul champ AFFECTAIT la valeur, la traîner était sans conséquence :
	# elle était écrasée à l'image suivante. Depuis que plusieurs puits s'AJOUTENT,
	# une aspiration posée pendant un état pilote s'accumulerait sans borne, et le
	# chasseur serait catapulté dans un coin du champ à la première image rendue —
	# sans erreur, sans test rouge, et seulement dans une partie qui va jusqu'à
	# l'appontage.
	var pull := consume_pull()
	var drag := consume_drag()
	# ⚠️ RETENU POUR L'AFFICHAGE, et c'est le sujet du correctif. Le freinage changeait la
	# vitesse sans qu'AUCUN signal ne le dise : l'opérateur a joué au milieu des sangsues
	# sans comprendre qu'elles agissaient — « elles viennent se mettre autour de moi sans
	# rien faire ? ». Un effet qui modifie l'état du jeu et ne se montre pas se lit comme
	# des commandes molles, donc comme un défaut du jeu et non comme une menace.
	_shown_drag = drag
	if not _alive:
		_respawn_timer -= delta
		if _respawn_timer <= 0.0:
			_respawn()
		return
	if _autopilot:
		_shield.grant_invulnerability(0.3) # safe during the guided approach
		plane_position = plane_position.move_toward(_autopilot_target, stats.max_speed * 0.6 * delta)
		position = GameplayPlane.to_world(plane_position) + Vector3(0.0, plane_lift, 0.0)
		# L'approche d'appontage est pilotée : la commande du joueur ne dit plus rien,
		# mais le moteur pousse — sans cette ligne la plume s'éteindrait pendant le
		# seul plan du jeu où le vaisseau est filmé en approche lente.
		_update_plumes(Vector2(0.0, 0.5))
		if _target != null:
			_target.position = plane_position
		if plane_position.distance_to(_autopilot_target) < 0.1:
			_autopilot = false
			autopilot_reached.emit()
		return
	_shield.tick(delta)
	shield_changed.emit(_shield.ratio(), _shield.current, _shield.maximum)
	_update_invuln_blink(delta)
	var input: Vector2
	if _demo:
		_demo_time += delta
		input = Vector2(sin(_demo_time * 0.9) * 0.85, 0.0) # horizontal sweep only
	else:
		input = GameplayPlane.from_input(
			Input.get_vector("move_left", "move_right", "move_up", "move_down"))
	_velocity = integrate_velocity(_velocity, input, stats.max_speed, stats.accel_time, delta)
	# Le frein s'applique à la COMMANDE du joueur, l'aspiration s'y ajoute. Une
	# sangsue vole de la vitesse ; elle ne pousse pas le chasseur quelque part.
	plane_position = GameplayPlane.clamp_to_bounds(
		plane_position + (_velocity * (1.0 - drag) + pull) * delta)
	position = GameplayPlane.to_world(plane_position) + Vector3(0.0, plane_lift, 0.0)
	if _target != null:
		_target.position = plane_position
	_apply_visual_bank(delta)
	_update_plumes(input)
	_update_fire(delta)

## Dégâts qui ne viennent PAS d'un projectile : la lame de la faux du Harvester, son
## faisceau. Ils passent par le même bouclier, donc par la même invulnérabilité de
## 1,2 s après impact — c'est elle, et non un plafond côté attaquant, qui empêche un
## faisceau continu de vider l'écu en une image.
## Impose une aspiration pour l'image en cours (`GravityWell`), qui S'AJOUTE à celles
## déjà posées. À reposer chaque image : elle est consommée en tête de
## `_physics_process`, quel que soit l'état du chasseur.
##
## Deux puits ouverts en même temps doivent tirer chacun leur part — sans quoi le
## dernier appelé gagne et le joueur traverse tranquillement un nid qui devrait
## l'écraser.
##
## ⚠️ C'EST LA SEULE PORTE. Il a existé un `apply_pull()` qui AFFECTAIT la valeur,
## et tant qu'il n'y avait qu'un champ dans le jeu, personne ne pouvait le voir :
## le défaut était masqué par le nombre d'appelants, pas par le code. Ne pas
## rouvrir de voie qui écrase — un appelant qui affecte annule en silence tous les
## autres de la même image.
func add_pull(velocity: Vector2) -> void:
	_external_pull += velocity

## Retire l'aspiration accumulée et remet le compteur à zéro, en un seul geste.
##
## Une méthode plutôt que deux lignes en tête de `_physics_process` pour une seule
## raison : ainsi la règle « on consomme, donc on remet à zéro » est vérifiable sans
## arbre de scène (tests/unit/test_player_pull.gd). Séparer la lecture de la remise
## à zéro, c'est autoriser un chemin qui lit sans effacer — et c'est exactement le
## défaut qu'on vient de corriger.
func consume_pull() -> Vector2:
	var pull := _external_pull
	_external_pull = Vector2.ZERO
	return pull

## Part maximale de vitesse qu'on peut voler au chasseur, toutes sangsues confondues.
##
## ⚠️ MÊME INVARIANT QUE `GravityWell.MIN_MOBILITY`, ET POUR LA MÊME RAISON : le
## pilote doit conserver 40 % de sa mobilité quoi qu'il arrive. En deçà, l'esquive
## devient une loterie et la menace cesse d'être une menace pour devenir une panne.
## Deux sangsues freinent plus qu'une, trois ne freinent pas plus que deux.
const MAX_EXTERNAL_DRAG := 0.6

## Vole une part de la vitesse pour l'image en cours. Cumulatif et plafonné : à
## reposer chaque image, comme l'aspiration.
func add_drag(factor: float) -> void:
	_external_drag = clampf(_external_drag + maxf(factor, 0.0), 0.0, MAX_EXTERNAL_DRAG)

## Retire le frein accumulé et remet le compteur à zéro, en un seul geste — même
## forme que `consume_pull()`, et pour la même raison : séparer la lecture de la
## remise à zéro autoriserait un chemin qui lit sans effacer.
func consume_drag() -> float:
	var drag := _external_drag
	_external_drag = 0.0
	return drag

func take_contact_damage(amount: float) -> void:
	_take_hit(amount)

## Bullet hit callback (registered with the BulletManager).
func _take_hit(damage: float) -> void:
	if not _alive:
		return
	if _shield.take_hit(damage):
		hit_taken.emit(global_position)
		shield_changed.emit(_shield.ratio(), _shield.current, _shield.maximum)
		if _shield.is_depleted():
			_destroy()

func _destroy() -> void:
	_alive = false
	_visual_root.visible = false
	if _target != null:
		_target.enabled = false
	destroyed_at.emit(global_position)
	_lives -= 1
	lives_changed.emit(_lives)
	if _lives <= 0:
		game_over.emit()
	else:
		_respawn_timer = 1.2 # brief pause before respawn (spec §5.3: forgiving)

func _respawn() -> void:
	_alive = true
	plane_position = Vector2(0.0, -5.0)
	_velocity = Vector2.ZERO
	position = GameplayPlane.to_world(plane_position) + Vector3(0.0, plane_lift, 0.0)
	_visual_root.visible = true
	_shield.reset()
	_shield.grant_invulnerability(2.0)
	if _target != null:
		_target.position = plane_position
		_target.enabled = true
	shield_changed.emit(_shield.ratio(), _shield.current, _shield.maximum)

func _update_invuln_blink(delta: float) -> void:
	if _shield.is_invulnerable():
		_blink_time += delta * 18.0
		_visual_root.visible = fmod(_blink_time, 1.0) < 0.55
	elif not _visual_root.visible:
		_visual_root.visible = true

## Raise the primary fire power level (Power Core pickup, spec §9.1).
func add_power() -> void:
	if _power_level < MAX_POWER:
		_power_level += 1
		power_changed.emit(_power_level)

func restore_shield(amount: float) -> void:
	_shield.restore(amount)
	shield_changed.emit(_shield.ratio(), _shield.current, _shield.maximum)

## Current speed as a fraction of the ship's maximum (0 = drifting, 1 = full tilt).
## Drives the engine hum; also true while the autopilot is flying the docking approach.
func speed_ratio() -> float:
	return clampf(_velocity.length() / stats.max_speed, 0.0, 1.0)

## Take over control and fly to a target on the plane (docking, spec §6.5).
## Hauteur du chasseur au-dessus du plan de jeu, en unités monde.
##
## ⚠️ PUREMENT VISUEL : `plane_position` ne bouge pas, donc ni les collisions, ni les
## tirs, ni les bornes de terrain ne changent. Sert la plongée dans le noyau du boss
## final (ADR-0021) : à hauteur nulle, le chasseur se retrouve À L'INTÉRIEUR de la coque
## et disparaît derrière elle — vu en capture, un noyau splendide et pas un vaisseau à
## l'écran. Le monter le fait passer devant, sans rien changer au jeu.
var plane_lift: float = 0.0

func begin_autopilot(target: Vector2) -> void:
	_autopilot = true
	_autopilot_target = target
	_visual_root.visible = true

## Rend la main au joueur avant l'arrivée. L'autopilote d'appontage s'arrête tout seul
## au contact de sa cible ; la plongée dans le noyau du boss (ADR-0021), elle, doit la
## rendre à un instant PRÉCIS — celui où le tir s'ouvre. Sans ça le chasseur resterait
## guidé, invulnérable et muet pendant les cinq secondes qui comptent.
func end_autopilot() -> void:
	_autopilot = false

## Hide the fighter (after docking, when the player becomes the fortress).
func stow() -> void:
	_autopilot = false
	visible = false
	set_physics_process(false)
	if _target != null:
		_target.enabled = false

## Unlimited continues for the demo (spec §8.4): restore lives and respawn.
func continue_run() -> void:
	_lives = stats.lives
	lives_changed.emit(_lives)
	_respawn()

func _update_fire(delta: float) -> void:
	_fire_timer = maxf(_fire_timer - delta, 0.0)
	if _muzzle_timer > 0.0:
		_muzzle_timer = maxf(_muzzle_timer - delta, 0.0)
		_muzzle_material.emission_energy_multiplier = 6.0 * (_muzzle_timer / 0.05)
		if _muzzle_timer == 0.0:
			# Iterate the constant name list, not `.values()` — the latter allocates
			# a fresh Array every salvo, in a per-frame loop (godot-reviewer).
			for muzzle_name in MUZZLE_NAMES:
				_muzzle_flashes[muzzle_name].visible = false
	if _bullet_manager == null or primary_projectile == null:
		return
	if (_demo or Input.is_action_pressed("fire_primary")) and _fire_timer == 0.0:
		# Higher power tightens cadence (spec §9.1 level 2 = increased rate).
		var cadence := stats.fire_interval * (1.0 if _power_level < 2 else 0.8)
		_fire_timer = cadence
		_fire_pattern()
		_muzzle_timer = 0.05

## Pulse Array fire pattern, escalating with power level (spec §9.1). Every stream
## leaves a real gun baked into the hull (ADR-0008): the nose twin, then the wings,
## the central axis, and finally the wingtips.
func _fire_pattern() -> void:
	fired.emit()
	# Level 1+: twin frontal shots from the nose cannon.
	_shoot("Muzzle_L", DIR_UP)
	_shoot("Muzzle_R", DIR_UP)
	if _power_level >= 3:
		# Level 3+: angled side shots from the wing guns.
		_shoot("Muzzle_Wing_L", Vector2(-0.28, 1.0))
		_shoot("Muzzle_Wing_R", Vector2(0.28, 1.0))
	if _power_level >= 4:
		# Level 4+: reinforced central axis.
		_shoot("Muzzle_C", DIR_UP)
	if _power_level >= 5:
		# Level 5: full lateral spread from the wingtip pods.
		_shoot("Muzzle_Tip_L", Vector2(-0.6, 1.0))
		_shoot("Muzzle_Tip_R", Vector2(0.6, 1.0))

## Fire one bolt from the named gun and light that gun's muzzle flash. A gun the
## hull does not carry (old asset) degrades to the ship centre (cached as zero).
##
## ⚠️ LE BOLT PART DE L'AXE DU CHASSEUR, PAS DU BOUT DU CANON. On garde l'écart LATÉRAL
## de l'arme — un tir d'aile sort bien de l'aile — et on annule son AVANCE.
##
## Mesuré le 2026-08-27 : les canons de nez sont modélisés à **+1,070 u** devant le centre,
## et la balle avance encore de 0,40 u avant le premier test de collision. Une cible dont
## le centre était à moins de **0,90 u** devant le chasseur ne pouvait donc pas être
## touchée — et rien ne chassait le joueur de là, un chasseur ordinaire n'infligeant aucun
## dégât de contact. L'unité y était **inoffensive et invulnérable** (`LOI-ENN-04`).
##
## C'est le même découplage que la hitbox, « délibérément plus petite que le modèle
## visuel » (spec §8.2) : l'éclair de bouche reste sur l'arme, la balle naît sur l'axe.
func _shoot(muzzle_name: String, direction: Vector2) -> void:
	var gun: Vector2 = _muzzles.get(muzzle_name, Vector2.ZERO)
	var origin: Vector2 = plane_position + Vector2(gun.x, BOLT_FORWARD_OFFSET)
	_bullet_manager.spawn_from_data(BulletManager.Team.PLAYER, origin, direction, primary_projectile)
	var flash: MeshInstance3D = _muzzle_flashes.get(muzzle_name)
	if flash != null:
		flash.visible = true

## Local position of an attach point baked into the hull mesh (ADR-0008).
## A hull missing one is an asset bug: report it and degrade to the origin
## rather than crash the run.
func _attach_point(point_name: String) -> Vector3:
	var node := _hull.get_node_or_null(NodePath(point_name)) as Node3D
	if node == null:
		push_error("[PlayerFighter] hull has no attach point '%s'" % point_name)
		return Vector3.ZERO
	return node.position

## Read each gun's plane-space offset from the ship origin, once. The hull is
## modelled nose-forward (-Z, no yaw on the player instance) so we project through
## its transform for good measure; a missing gun falls back to the centre.
func _cache_muzzles() -> void:
	for muzzle_name in MUZZLE_NAMES:
		var world: Vector3 = _hull.transform * _attach_point(muzzle_name)
		_muzzles[muzzle_name] = Vector2(world.x, -world.z)

## Une plume d'échappement par tuyère (ADR-0017).
##
## La traînée de particules a disparu, et pas seulement sa fabrication locale : gardée
## en braises résiduelles derrière la plume, elle lisait comme des DÉBRIS qui tombent
## du vaisseau. Le moteur se raconte entièrement dans la plume.
func _build_engine_plumes() -> void:
	if plume == null:
		return
	for point_name in ["Engine_L", "Engine_R"]:
		var jet := EnginePlume.make(plume)
		jet.position = _attach_point(point_name)
		_visual_root.add_child(jet)
		_engine_plumes.append(jet)

## Le régime que le pilote demande, poussé aux plumes. Appelé avec la commande brute :
## c'est elle qui porte l'INTENTION (le geste précède la vitesse), la vitesse acquise
## n'entretenant ensuite le jet que le temps que le vaisseau file encore.
func _update_plumes(input: Vector2) -> void:
	if plume == null:
		return
	var ratio := EnginePlume.throttle_from(input, speed_ratio(), plume)
	# LE SIGNAL DU FREINAGE : les tuyères s'étranglent. C'est le bon endroit pour le dire —
	# c'est le JOUEUR qui subit, donc c'est sur SON vaisseau que ça doit se lire, pas sur la
	# sangsue qui est ailleurs à l'écran.
	#
	# ⚠️ Et c'est la plume et non une teinte : le cyan appartient à la propulsion alliée
	# (`space_background.gdshader`, DA §6). Le colorer pour dire « on te freine » volerait
	# une couleur qui signifie déjà autre chose.
	ratio *= drag_throttle(_shown_drag)
	for jet in _engine_plumes:
		jet.set_throttle(ratio)

## Ce qu'il reste de poussée visible sous un freinage donné.
##
## Pure et statique : le rapport entre ce que le joueur subit et ce qu'il voit est une règle
## de lisibilité, pas un détail d'affichage — elle se vérifie sans arbre de scène.
##
## ⚠️ ELLE EXAGÈRE VOLONTAIREMENT. Un frein de 0,35 (une sangsue) coupe 35 % de la vitesse
## mais n'étranglerait la plume que d'autant, ce qui ne se voit pas. On l'amplifie pour que
## la première sangsue soit déjà lisible — le signal doit apparaître AVANT que le joueur ne
## se demande si ses commandes répondent mal.
static func drag_throttle(drag: float) -> float:
	return clampf(1.0 - clampf(drag, 0.0, 1.0) * 1.6, 0.12, 1.0)

func _build_muzzle_flashes() -> void:
	var quad := QuadMesh.new()
	quad.size = Vector2(0.5, 0.5)
	_muzzle_material = StandardMaterial3D.new()
	_muzzle_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_muzzle_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_muzzle_material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_muzzle_material.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	_muzzle_material.emission_enabled = true
	_muzzle_material.albedo_color = Color(0.6, 0.95, 1.0, 1.0)
	_muzzle_material.emission = Color(0.5, 0.9, 1.0)
	_muzzle_material.albedo_texture = SoftDot.texture()
	for muzzle_name in MUZZLE_NAMES:
		var flash := MeshInstance3D.new()
		flash.mesh = quad
		flash.position = _attach_point(muzzle_name)
		flash.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		flash.material_override = _muzzle_material
		flash.visible = false
		_visual_root.add_child(flash)
		_muzzle_flashes[muzzle_name] = flash

## Pure movement math, testable headless: accelerate toward input * max_speed,
## reaching it in accel_time seconds (spec §7.3: max speed in < 250 ms).
static func integrate_velocity(current: Vector2, input: Vector2, max_speed: float,
		accel_time: float, delta: float) -> Vector2:
	var target := input.limit_length(1.0) * max_speed
	var accel := max_speed / accel_time
	return current.move_toward(target, accel * delta)

func _apply_visual_bank(delta: float) -> void:
	var lateral := -_velocity.x / stats.max_speed
	var bank_target := lateral * deg_to_rad(stats.max_bank_deg)
	_visual_root.rotation.z = lerp_angle(_visual_root.rotation.z, bank_target,
		minf(1.0, delta * 12.0))
	if _flight != null:
		# Les gouvernes suivent l'inclinaison, les tuyeres suivent la vitesse : ce
		# sont deux informations distinctes, et les confondre ferait s'ouvrir les
		# tuyeres en virage a l'arret.
		_flight.set_bank(lateral)
		_flight.set_thrust(speed_ratio())
