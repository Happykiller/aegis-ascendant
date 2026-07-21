extends Node3D
## Écran d'accueil — diorama 3D animé (maquette : assets/reference/inspiration/ref_home.png).
##
## Remplace l'ancien écran titre, qui était un Control 2D : un SVG plat, des labels en
## police Godot par défaut, et pour toute animation un sin() sur l'alpha du hint. Le jeu
## étant en vraie 3D, la rupture d'ambiance avec le combat était totale.
##
## Ce script ne fait QUE la mise en scène. L'interface, le menu et l'input vivent dans
## title_menu.gd, sur le CanvasLayer au-dessus.
##
## Autoloads résolus par chemin (convention projet) : garde le script compilable en mode
## --script, où les globales d'autoload n'existent pas.

const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")

@onready var _audio: AudioManagerScript = get_node("/root/AudioManager")
@onready var _camera_rig: Node3D = $CameraDirector
@onready var _hero: Node3D = $Hero
@onready var _citadel: Node3D = $Citadel
@onready var _escorts: Node3D = $Escorts

## Pose de repos de la caméra, relevée au départ : toute l'animation est un DÉCALAGE
## par rapport à elle, jamais une position absolue accumulée.
var _camera_rest: Vector3
var _hero_rest: Vector3
var _age: float = 0.0

# --- Chorégraphie -------------------------------------------------------------
# Des périodes volontairement non harmoniques (11.0 / 7.3 / 17.0 s) : la scène ne
# doit jamais se retrouver deux fois dans la même pose, sinon l'œil repère la boucle
# et l'accueil redevient un décor.
const CAMERA_SWAY_PERIOD := 17.0
const CAMERA_SWAY := Vector3(0.85, 0.35, 0.0)
const CAMERA_PUSH_PERIOD := 23.0
const CAMERA_PUSH := 1.1
const HERO_BOB_PERIOD := 7.3
const HERO_BOB := 0.14
const HERO_ROLL_PERIOD := 11.0
const HERO_ROLL_DEG := 4.5
const CITADEL_YAW_RATE := 0.035    # rad/s — à peine perceptible, mais jamais figé
const ESCORT_SPAN := 34.0          # largeur du couloir traversé avant rebouclage
const ESCORT_SPEED := 2.6

func _ready() -> void:
	_camera_rest = _camera_rig.position
	_hero_rest = _hero.position
	_audio.set_music_state(MusicDirector.State.TITLE)
	_tune_backdrop()
	_detail_hulls()
	_animate_citadel()
	_attach_engine_trails()
	_apply_bisect_flags()
	print("[TitleStage] ready")

## Réglages de fond propres au titre, sur une COPIE du matériau.
##
## Le ShaderMaterial vit sur le PlaneMesh à l'intérieur de space_backdrop.tscn, et les
## sous-ressources d'une scène packée sont PARTAGÉES entre toutes ses instances : le
## modifier en place changerait aussi le fond du combat. On duplique, puis on pose la
## copie en material_override.
##
## center_calm assombrit volontairement le tiers central pour que le combat s'y lise
## (space_background.gdshader). Sur un écran titre, le sujet EST au centre — garder le
## réglage de jeu creuserait un trou en plein milieu de la composition.
func _tune_backdrop() -> void:
	var backdrop := get_node_or_null("SpaceBackdrop") as MeshInstance3D
	if backdrop == null or backdrop.mesh == null:
		return
	var source := backdrop.mesh.surface_get_material(0) as ShaderMaterial
	if source == null:
		push_error("[TitleStage] fond spatial sans ShaderMaterial")
		return
	var tuned: ShaderMaterial = source.duplicate()
	tuned.set_shader_parameter("center_calm", 0.0)
	# Défilement ralenti : on contemple, on ne fuit pas vers l'avant.
	tuned.set_shader_parameter("scroll_speed", -0.12)
	backdrop.material_override = tuned

## Drapeaux de bissection perf, sur le modèle de graybox_root.gd:77-83. Sans eux le
## coût du fond et du glow n'est pas isolable, et « c'est lent » reste une opinion.
func _apply_bisect_flags() -> void:
	var args := OS.get_cmdline_user_args()
	if "--no-backdrop" in args:
		var backdrop := get_node_or_null("SpaceBackdrop") as Node3D
		if backdrop != null:
			backdrop.visible = false
	if "--no-glow" in args:
		var we := get_node_or_null("WorldEnvironment") as WorldEnvironment
		if we != null and we.environment != null:
			we.environment.glow_enabled = false

## Les points d'attache sont de vrais Node3D enfants du .glb (ADR-0008), adressables
## par nom. Une coque à laquelle il en manque un est un bug d'asset : le signaler et
## dégrader, pas planter l'écran d'accueil.
## Le héros est à 3 m de la caméra, les escortes à une quinzaine : à réglage égal,
## les plumes du héros écrasent l'image pendant que celles des escortes disparaissent.
## D'où deux calibrages distincts — c'est une question de cadrage, pas de physique.
const HERO_TRAIL_SCALE := 0.42
const HERO_TRAIL_ENERGY := 1.5
const ESCORT_TRAIL_SCALE := 0.8
const ESCORT_TRAIL_ENERGY := 2.4

const CitadelTurretScene := preload("res://scenes/fortress/citadel_turret.tscn")
const CitadelBeaconScene := preload("res://scenes/fortress/citadel_beacon.tscn")

## Feuille de detail sur toutes les coques de la scene (accueil = gros plan, c'est
## la que ca compte le plus). Le joueur en combat sera traite separement, une fois
## la methode validee ici.
##
## La citadelle a le SIEN (`CitadelDetail`) et non la feuille partagee : la feuille
## commune est calee sur un chasseur de 2 m et lit comme du bruit raye sur une piece
## de 19,6 m. Les deux ne se cumulent pas — le dernier applique gagnerait.
func _detail_hulls() -> void:
	HullDetail.apply(_hero)
	for escort in _escorts.get_children():
		HullDetail.apply(escort)
	CitadelDetail.apply(_citadel)

## Tourelles, balises et respiration des emissifs.
##
## L'accueil instancie le `.glb` NU, pas `aegis_citadel.tscn` : sans cet appel, la
## forteresse resterait figee precisement la ou on la met en vedette. C'est pour ce
## cas que l'animation vit dans une fabrique statique (`CitadelLife`) et non dans le
## controleur de gameplay.
func _animate_citadel() -> void:
	var hull := _citadel.get_node_or_null("Hull") as Node3D
	if hull == null:
		push_error("[TitleStage] Citadel sans nœud 'Hull'")
		return
	CitadelLife.apply(hull, CitadelTurretScene, CitadelBeaconScene)

func _attach_engine_trails() -> void:
	_attach_trail_to(_hero, HERO_TRAIL_SCALE, 18, HERO_TRAIL_ENERGY)
	for escort in _escorts.get_children():
		_attach_trail_to(escort as Node3D, ESCORT_TRAIL_SCALE, 14, ESCORT_TRAIL_ENERGY)

func _attach_trail_to(ship: Node3D, trail_scale: float, amount: int, energy: float) -> void:
	var hull := ship.get_node_or_null("Hull")
	if hull == null:
		return
	for point_name in ["Engine_L", "Engine_R"]:
		var point := hull.get_node_or_null(NodePath(point_name)) as Node3D
		if point == null:
			push_error("[TitleStage] %s : coque sans point d'attache '%s'" % [ship.name, point_name])
			continue
		# Tous les vaisseaux restent à l'échelle 1 : le cadrage se fait par la
		# distance caméra. Mettre le NŒUD à l'échelle multiplierait deux fois — une
		# par la transformation du parent, une par la taille des particules.
		var trail := EngineTrail.make(trail_scale, amount, energy)
		trail.position = point.position
		ship.add_child(trail)

func _process(delta: float) -> void:
	_age += delta
	_animate_camera()
	_animate_hero()
	_citadel.rotation.y += CITADEL_YAW_RATE * delta
	_animate_escorts(delta)

## ⚠️ On anime le RIG, pas la Camera3D fille. CameraDirector réécrit
## `_camera.transform` à chaque image, y compris au repos (camera_director.gd:37-39) :
## toute animation posée sur la caméra elle-même serait écrasée à la frame suivante.
## En animant le parent, le shake du directeur reste additif par-dessus.
func _animate_camera() -> void:
	var sway := _age * TAU / CAMERA_SWAY_PERIOD
	var push := _age * TAU / CAMERA_PUSH_PERIOD
	_camera_rig.position = _camera_rest + Vector3(
		sin(sway) * CAMERA_SWAY.x,
		cos(sway * 0.7) * CAMERA_SWAY.y,
		sin(push) * CAMERA_PUSH)

func _animate_hero() -> void:
	var bob := _age * TAU / HERO_BOB_PERIOD
	var roll := _age * TAU / HERO_ROLL_PERIOD
	_hero.position = _hero_rest + Vector3(0.0, sin(bob) * HERO_BOB, 0.0)
	_hero.rotation.z = deg_to_rad(sin(roll) * HERO_ROLL_DEG)
	# Le nez suit le roulis, très légèrement : un vaisseau qui s'incline vire.
	_hero.rotation.y = deg_to_rad(sin(roll) * HERO_ROLL_DEG * 0.35)

## Traversée en boucle, sur le modèle de BackdropLandmark : position absolue dérivée
## d'un compteur, rebouclage par wrap. Zéro allocation par image (spec §31).
func _animate_escorts(delta: float) -> void:
	for escort in _escorts.get_children():
		var node := escort as Node3D
		node.position.x += ESCORT_SPEED * delta
		if node.position.x > ESCORT_SPAN * 0.5:
			node.position.x -= ESCORT_SPAN
