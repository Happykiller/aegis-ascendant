class_name CodexScreen
extends Node3D
## Bestiaire — une coque à la fois, en 3D, manipulable.
##
## L'écran monte la coque sur un PLATEAU TOURNANT et laisse le joueur la retourner :
## rotation à la souris ou au clavier, zoom à la molette, recadrage d'une touche. Les
## pièces mobiles sont pilotées en démonstration (flèche des ailes, volets, pétales de
## tuyère) — un vaisseau figé ne dit pas ce qu'il fait.
##
## ON TOURNE LE MODÈLE, PAS LA CAMÉRA. Une caméra en orbite garde les lumières fixes
## par rapport à la coque : le relief ne bouge plus, et une coque sombre le reste. En
## tournant le modèle sous des lumières fixes, les arêtes s'allument l'une après
## l'autre — c'est tout l'intérêt d'un présentoir.
##
## Les DIMENSIONS ne sont pas saisies : elles se mesurent sur la boîte englobante de
## la coque réellement affichée, et le recadrage automatique s'en déduit aussi. Un
## `.glb` reforgé met donc la fiche à jour tout seul.
##
## Autoloads résolus par chemin (convention projet) : garde le script compilable en
## mode `--script`, où les globales d'autoload n'existent pas.

const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const GameStateScript := preload("res://scripts/core/game_state.gd")
const SceneRouterScript := preload("res://scripts/core/scene_router.gd")
const BOOT_SCENE := "res://scenes/boot/boot.tscn"

## Plumes d'échappement du présentoir (ADR-0017), une par camp.
const HELIOS_PLUME := preload("res://resources/vfx/plume_helios.tres")
const NULL_CHOIR_PLUME := preload("res://resources/vfx/plume_null_choir.tres")
## Régime de présentation : au-dessus du seuil des disques de Mach. Une fiche technique
## montre le moteur ouvert — au ralenti, la moitié de ce qu'il y a à voir est absente.
const PLUME_THROTTLE := 0.85

## L'ordre est celui de la rencontre : le vaisseau du joueur, puis la menace par
## gravité croissante. Ce n'est pas l'ordre alphabétique, c'est une progression.
##
## PUBLIQUE ET TYPÉE, à dessein. Publique : les tests énuméraient les mêmes cinq
## `.tres` de leur côté, et prétendaient dans leur propre docstring porter « sur les
## fichiers réellement embarqués » — c'était faux, ils portaient sur leur copie. Une
## sixième fiche ajoutée ici serait partie en production sans `validate()`, sans
## contrôle ASCII, sans contrôle de source de stats. C'est exactement la deuxième
## source de vérité que `CodexEntry` s'interdit.
## Typée : sans le type d'élément, glisser une `EnemyData` dans la liste compile et
## passe le parse-check ; l'erreur ne tombe qu'à l'ouverture de l'écran.
const ROSTER: Array[CodexEntry] = [
	preload("res://resources/codex/specter_9.tres"),
	preload("res://resources/codex/aegis_citadel.tres"),
	preload("res://resources/codex/needle_scout.tres"),
	preload("res://resources/codex/crescent_interceptor.tres"),
	preload("res://resources/codex/choir_harvester.tres"),
	preload("res://resources/codex/pale_leviathan.tres"),
]

## Pièces mobiles de la citadelle. Elles sont des scènes SÉPARÉES et non des nœuds du
## `.glb` (le kit Blender n'exporte qu'un objet maillé) : `CitadelLife` les instancie
## sur les marqueurs de la coque. Sans elles, le vaisseau mère serait la seule fiche
## du bestiaire présentée figée.
const CitadelTurretScene := preload("res://scenes/fortress/citadel_turret.tscn")
const CitadelBeaconScene := preload("res://scenes/fortress/citadel_beacon.tscn")

## Préfixes des marqueurs comptés sur la coque pour la fiche d'une forteresse.
## COMPTÉS, jamais saisis : ajouter une septième tourelle au `.glb` met la fiche à
## jour toute seule, exactement comme les dimensions.
const FITTINGS: Dictionary[StringName, String] = {
	&"turrets": "Turret_",
	&"beacons": "Beacon_",
	&"batteries": "Muzzle_Battery",
}

# --- Présentoir ---------------------------------------------------------------
## Pose de présentation : trois quarts avant, légèrement plongeant. Le 180° vient de
## ce que les coques sont modelées nez vers -Z (cf. EngineTrail) : sans lui, le
## bestiaire ouvrirait sur des tuyères.
const DEFAULT_YAW_DEG := 205.0
const DEFAULT_PITCH_DEG := 16.0
## Au-delà, on regarde la coque par le pôle et la silhouette disparaît.
const PITCH_LIMIT_DEG := 78.0

## Part de la DEMI-LARGEUR du cadre que la coque occupe. 0,62 la pose franchement au
## centre : elle déborde sur les zones vides à gauche et à droite sans jamais mordre
## la colonne d'instruments. Un premier essai calé sur la demi-diagonale complète et
## une marge de 1,55 rendait un Specter-9 à 19 % de la largeur — un catalogue dont on
## ne voit pas l'objet.
const FILL_WIDTH := 0.62
## Idem en hauteur. Plus bas, parce que le bandeau des coques et le rappel de touches
## mangent le haut et le bas du cadre.
const FILL_HEIGHT := 0.52
## Décentrage du sujet vers la gauche, en fraction de la distance caméra. La colonne
## d'instruments occupe le tiers droit du cadre : une coque centrée sur l'écran passe
## dessous par la queue. On décale la CAMÉRA, pas la coque — le plateau doit tourner
## autour de son propre centre, sinon la rotation devient une orbite.
const SUBJECT_SHIFT := 0.11
const ZOOM_MIN := 0.40
const ZOOM_MAX := 2.60
const ZOOM_WHEEL_STEP := 0.11
const ZOOM_KEY_RATE := 0.9

const DRAG_SENSITIVITY := 0.006      # rad/pixel
const KEY_TURN_RATE := 1.6           # rad/s
## Rotation d'attente. Elle reprend `AUTO_RESUME` secondes après la dernière action :
## un présentoir doit vivre, mais pas repartir sous les doigts de qui l'examine.
const AUTO_YAW_RATE := 0.25          # rad/s
const AUTO_RESUME := 3.5

## Périodes de la démonstration des pièces mobiles. Non harmoniques, comme la
## chorégraphie de l'accueil : les ailes et les volets ne doivent jamais retomber
## ensemble sur la même pose, sinon le mouvement lit comme une boucle.
const DEMO_THRUST_PERIOD := 7.0
const DEMO_BANK_PERIOD := 4.3

const FADE_IN := 0.6
const FADE_OUT := 0.4
## Le modèle se pose en grandissant à chaque bascule — le raccord sec entre deux
## coques lisait comme un défaut d'affichage.
const SWAP_POP := 0.28

@onready var _audio: AudioManagerScript = get_node("/root/AudioManager")
@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _scene_router: SceneRouterScript = get_node("/root/SceneRouter")
@onready var _tilt: Node3D = $Tilt
@onready var _yaw: Node3D = $Tilt/Yaw
@onready var _camera: Camera3D = $CameraRig/Camera3D
@onready var _datasheet: CodexDatasheet = $Datasheet

var _index: int = 0
var _hull: Node3D
var _flight: ShipFlight
var _yaw_angle: float = deg_to_rad(DEFAULT_YAW_DEG)
var _pitch_angle: float = deg_to_rad(DEFAULT_PITCH_DEG)
var _base_distance: float = 6.0
var _zoom: float = 1.0
var _dragging: bool = false
var _idle: float = 0.0
var _age: float = 0.0
var _leaving: bool = false

func _ready() -> void:
	_audio.set_music_state(MusicDirector.State.TITLE)
	_tune_backdrop()
	_datasheet.back_requested.connect(_leave)
	# La distance de cadrage dépend du RAPPORT D'IMAGE : calculée une seule fois au
	# montage, la coque restait cadrée pour l'ancienne fenêtre après un
	# redimensionnement, jusqu'à ce qu'on change de fiche.
	get_viewport().size_changed.connect(_reframe)
	var names := PackedStringArray()
	for entry: CodexEntry in ROSTER:
		names.append(entry.display_name)
	_datasheet.set_roster(names)
	_show(_requested_index())
	_datasheet.fade_in(FADE_IN)
	print("[Codex] ready — %d coques" % ROSTER.size())

## Hook de vérification : `++ --codex-entry=3` ouvre directement une coque donnée.
## Sans lui, toute capture d'écran du bestiaire montre la première fiche, et les
## quatre autres ne seraient jamais regardées (ADR-0006 : un asset non regardé n'est
## pas un asset validé).
func _requested_index() -> int:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--codex-entry="):
			return arg.trim_prefix("--codex-entry=").to_int()
	return 0

## Réglages de fond propres au bestiaire, sur une COPIE du matériau.
##
## Le ShaderMaterial vit sur le PlaneMesh à l'intérieur de `space_backdrop.tscn`, et
## les sous-ressources d'une scène packée sont PARTAGÉES entre toutes ses instances :
## le modifier en place changerait aussi le fond du combat (title_stage.gd est tombé
## dans ce piège avant nous).
##
## `center_calm` assombrit le tiers central pour que le combat s'y lise. Ici le sujet
## EST au centre, et garder le réglage de jeu creuserait un trou pile derrière la
## coque qu'on présente.
func _tune_backdrop() -> void:
	var backdrop := get_node_or_null("SpaceBackdrop") as MeshInstance3D
	if backdrop == null or backdrop.mesh == null:
		return
	var source := backdrop.mesh.surface_get_material(0) as ShaderMaterial
	if source == null:
		push_error("[Codex] fond spatial sans ShaderMaterial")
		return
	var tuned: ShaderMaterial = source.duplicate()
	tuned.set_shader_parameter("center_calm", 0.0)
	# Presque immobile : le fond d'un catalogue ne doit pas concurrencer le sujet.
	tuned.set_shader_parameter("scroll_speed", -0.05)
	backdrop.material_override = tuned

# --- Mise en scène de la coque courante ---------------------------------------

func _show(index: int) -> void:
	_index = wrapi(index, 0, ROSTER.size())
	var entry: CodexEntry = ROSTER[_index]
	_mount(entry)
	_reset_view()

func _mount(entry: CodexEntry) -> void:
	if _hull != null:
		# `free()` et non `queue_free()` : la coque suivante est montée dans la
		# foulée, et deux coques présentes le temps d'une image se superposeraient
		# dans le cadre.
		_hull.free()
		_hull = null
	_flight = null
	if entry.hull_scene == null:
		push_error("[Codex] %s : fiche sans coque" % entry.display_name)
		return
	_hull = entry.hull_scene.instantiate() as Node3D
	_yaw.add_child(_hull)

	# Mesuré AVANT la feuille de détail et les traînées : la fiche annonce les
	# dimensions de la COQUE, pas celles de ses effets.
	var bounds := _hull_bounds(_hull)
	var triangles := _count_triangles(_hull)
	var fittings := _count_fittings(_hull)
	# Le plateau doit tourner autour du centre du volume, pas autour de l'origine du
	# `.glb` — qui est le nez sur certaines coques, et le ferait balayer le cadre.
	_hull.position = -bounds.get_center()

	# ⚠️ Deux feuilles de détail, jamais les deux à la fois. La feuille commune est
	# calée sur un chasseur de 2 m et lit comme du bruit rayé sur une pièce de 19,6 m
	# — c'est le constat de `title_stage.gd`, on ne le refait pas.
	if entry.family == CodexEntry.Family.FORTRESS:
		CitadelDetail.apply(_hull)
		# Tourelles, balises et respiration des émissifs. Sans cet appel, la citadelle
		# serait la seule fiche présentée figée, alors qu'elle est la plus animée du
		# jeu — et l'opérateur a demandé « animé pour voir ce qui bouge ».
		CitadelLife.apply(_hull, CitadelTurretScene, CitadelBeaconScene)
	else:
		HullDetail.apply(_hull)
		_flight = ShipFlight.apply(_hull)
	_attach_trails(bounds, entry.camp)

	_base_distance = entry.frame_distance if entry.frame_distance > 0.0 else _framing_distance(bounds)
	_datasheet.show_entry(entry, _index, bounds, triangles, fittings)
	_pop()

## Compte les marqueurs d'équipement de la coque, par préfixe.
##
## ⚠️ Appelé AVANT `CitadelLife`, qui instancie de vraies tourelles EN ENFANTS de ces
## mêmes marqueurs : compter après aurait mélangé marqueurs et pièces montées.
func _count_fittings(hull: Node3D) -> Dictionary[StringName, int]:
	var counts: Dictionary[StringName, int] = {}
	for key: StringName in FITTINGS:
		var prefix: String = FITTINGS[key]
		var total := 0
		for child in hull.get_children():
			if String(child.name).begins_with(prefix):
				total += 1
		counts[key] = total
	return counts

## Les points d'attache sont de vrais Node3D du `.glb` (ADR-0008). Toutes les coques
## n'en ont pas les mêmes — le Leviathan n'en a aucun — et une coque sans réacteur
## nommé n'est pas une erreur ici : c'est une coque qui ne pousse pas.
func _attach_trails(bounds: AABB, camp: CodexEntry.Camp) -> void:
	# Proportionnel à la coque, borné aux deux bouts : à réglage fixe, la plume d'un
	# Needle Scout de 1,9 m et celle d'un Leviathan de 8,8 m ne peuvent pas être la
	# même. Le halo blanc au centre du Choir Harvester n'est PAS cette plume — c'est
	# son noyau émissif, vérifié en baissant l'échelle sans que l'image bouge.
	var trail_scale := clampf(bounds.size.length() * 0.10, 0.10, 0.55)
	# La plume porte la couleur du CAMP : une fiche du Null Choir ne crache pas du cyan
	# Helios. `camp` est déclaré sur l'entrée, on ne le devine pas de la coque.
	var tuning: PlumeTuning = HELIOS_PLUME if camp == CodexEntry.Camp.HELIOS else NULL_CHOIR_PLUME
	# ⚠️ Le catalogue mélange les orientations (ADR-0015) : une coque Helios est modelée
	# nez vers -Z, une coque ennemie nez vers le bas de l'écran. L'échappement part donc
	# dans des sens opposés selon le camp — pris à l'envers, le jet sort du nez.
	var aft := Vector3.BACK if camp == CodexEntry.Camp.HELIOS else Vector3.FORWARD
	# Échelle PROPRE à la plume, et non `trail_scale` : celui-ci est calibré sur des
	# particules (0,10 par unité de coque) et rendait un jet de 39 cm derrière un
	# chasseur de 2,46 m — mesuré, pas supposé. 0,35 pose le Specter-9 du présentoir à
	# la taille qu'il a en jeu, et suit les coques plus grandes.
	var plume_scale := clampf(bounds.size.length() * 0.35, 0.3, 2.0)
	for point_name in ["Engine_C", "Engine_L", "Engine_R"]:
		var point := _hull.get_node_or_null(NodePath(point_name)) as Node3D
		if point == null:
			continue
		# Régime de présentation : assez haut pour que les disques de Mach soient
		# allumés — le bestiaire est une fiche technique, il montre le moteur ouvert.
		var jet := EnginePlume.make(tuning, plume_scale, aft)
		jet.position = point.position
		jet.snap_throttle(PLUME_THROTTLE)
		_hull.add_child(jet)
		var trail := EngineTrail.make(trail_scale, 8, 1.6)
		# `local_coords` vrai, contrairement au jeu : le plateau tourne, et des
		# particules laissées dans le monde décriraient un arc de cercle derrière la
		# coque au lieu d'une plume.
		trail.local_coords = true
		trail.position = point.position
		_hull.add_child(trail)

func _pop() -> void:
	_yaw.scale = Vector3.ONE * 0.86
	var tween := create_tween()
	tween.tween_property(_yaw, "scale", Vector3.ONE, SWAP_POP).set_trans(Tween.TRANS_BACK) \
		.set_ease(Tween.EASE_OUT)

## Recalcule le cadrage sans remonter la coque : le zoom et l'orientation choisis par
## le joueur survivent au redimensionnement — c'est le cadre qui a bougé, pas lui.
func _reframe() -> void:
	if _hull == null:
		return
	var entry: CodexEntry = ROSTER[_index]
	if entry.frame_distance > 0.0:
		return
	_base_distance = _framing_distance(_hull_bounds(_hull))

func _reset_view() -> void:
	_yaw_angle = deg_to_rad(DEFAULT_YAW_DEG)
	_pitch_angle = deg_to_rad(DEFAULT_PITCH_DEG)
	_zoom = 1.0
	_idle = 0.0

## Distance de caméra qui inscrit la coque dans le cadre, largeur ET hauteur.
##
## Le rayon horizontal est la demi-diagonale du plan X/Z — donc l'encombrement de la
## coque VUE DE DESSUS, quel que soit son lacet. C'est ce qui garantit qu'elle ne
## grandit pas en tournant : mesurer la seule largeur ferait respirer le cadrage à
## chaque quart de tour, et mesurer la diagonale 3D complète compterait une hauteur
## qui, elle, ne tourne jamais dans le plan horizontal.
##
## `fov` est le champ VERTICAL : le champ horizontal s'en déduit par le rapport
## d'image réel, pas par un 16/9 supposé — le jeu peut tourner en fenêtré.
func _framing_distance(bounds: AABB) -> float:
	var half_v := deg_to_rad(_camera.fov * 0.5)
	var viewport := get_viewport().get_visible_rect().size
	var aspect := viewport.x / viewport.y if viewport.y > 0.0 else 16.0 / 9.0
	var half_h := atan(tan(half_v) * aspect)
	var radius_h := maxf(Vector2(bounds.size.x, bounds.size.z).length() * 0.5, 0.1)
	var radius_v := maxf(bounds.size.y * 0.5, 0.1)
	# On garde la plus GRANDE des deux distances : celle qui satisfait la contrainte
	# la plus serrée. Prendre la plus petite ferait sortir la coque du cadre.
	return maxf(radius_h / (tan(half_h) * FILL_WIDTH), radius_v / (tan(half_v) * FILL_HEIGHT))

# --- Mesures sur la coque -----------------------------------------------------

## Boîte englobante de toutes les surfaces, exprimée dans le repère de `root`.
##
## On n'utilise PAS `global_transform` : la coque vient d'être ajoutée à l'arbre et
## on veut une mesure qui ne dépende ni de l'état du plateau ni de l'ordre des mises
## à jour. Le produit des transformations locales jusqu'à la racine est exact et
## disponible immédiatement.
static func _hull_bounds(root: Node3D) -> AABB:
	var bounds := AABB()
	var first := true
	for mesh in _meshes(root):
		var local := _relative_transform(mesh, root) * mesh.get_aabb()
		if first:
			bounds = local
			first = false
		else:
			bounds = bounds.merge(local)
	return bounds

static func _count_triangles(root: Node3D) -> int:
	var total := 0
	for mesh in _meshes(root):
		var array_mesh := mesh.mesh as ArrayMesh
		if array_mesh == null:
			continue
		for surface in array_mesh.get_surface_count():
			# Une surface indexée compte ses indices ; sans index, ce sont les
			# sommets qui font foi. Diviser le mauvais des deux par trois donnerait
			# un chiffre plausible et faux.
			var indices := array_mesh.surface_get_array_index_len(surface)
			var count := indices if indices > 0 else array_mesh.surface_get_array_len(surface)
			total += count / 3
	return total

static func _meshes(root: Node) -> Array[MeshInstance3D]:
	var found: Array[MeshInstance3D] = []
	_collect_meshes(root, found)
	return found

## Tableau passé en paramètre plutôt qu'un défaut `= []` : un défaut de paramètre est
## une expression, et faire reposer l'accumulation sur le moment où GDScript la
## réévalue serait un pari — un tableau partagé entre deux appels ferait grossir la
## boîte englobante d'une coque avec les maillages de la précédente.
static func _collect_meshes(node: Node, into: Array[MeshInstance3D]) -> void:
	var mesh := node as MeshInstance3D
	if mesh != null and mesh.mesh != null:
		into.append(mesh)
	for child in node.get_children():
		_collect_meshes(child, into)

static func _relative_transform(node: Node3D, root: Node3D) -> Transform3D:
	var result := Transform3D.IDENTITY
	var current := node
	while current != null and current != root:
		result = current.transform * result
		current = current.get_parent() as Node3D
	return result

# --- Boucle -------------------------------------------------------------------

func _process(delta: float) -> void:
	_age += delta
	_idle += delta
	_poll_keys(delta)
	if _idle > AUTO_RESUME and not _dragging:
		_yaw_angle += AUTO_YAW_RATE * delta
	_apply_view()
	_demo_moving_parts()

func _poll_keys(delta: float) -> void:
	var turn := Input.get_axis("codex_yaw_left", "codex_yaw_right")
	var tilt := Input.get_axis("codex_pitch_up", "codex_pitch_down")
	var zoom := Input.get_axis("codex_zoom_out", "codex_zoom_in")
	if not is_zero_approx(turn) or not is_zero_approx(tilt):
		_yaw_angle += turn * KEY_TURN_RATE * delta
		_pitch_angle = clampf(_pitch_angle + tilt * KEY_TURN_RATE * delta,
			-deg_to_rad(PITCH_LIMIT_DEG), deg_to_rad(PITCH_LIMIT_DEG))
		_idle = 0.0
	if not is_zero_approx(zoom):
		_zoom = clampf(_zoom - zoom * ZOOM_KEY_RATE * delta, ZOOM_MIN, ZOOM_MAX)
		_idle = 0.0

func _apply_view() -> void:
	# Le tangage est PORTÉ PAR LE PARENT et le lacet par l'enfant : la coque bascule
	# alors autour de l'axe horizontal de l'écran quel que soit son lacet. L'ordre
	# inverse ferait basculer la coque autour de son propre axe, et le geste
	# « je la penche vers moi » cesserait de marcher dès qu'elle est de profil.
	_tilt.rotation.x = _pitch_angle
	_yaw.rotation.y = _yaw_angle
	var distance := _base_distance * _zoom
	_camera.position.z = distance
	_camera.position.x = distance * SUBJECT_SHIFT

## Démonstration des pièces mobiles. Le bestiaire n'a ni pilote ni vitesse : il
## pousse deux ratios à la coque, exactement comme les escortes de l'accueil.
func _demo_moving_parts() -> void:
	if _flight == null:
		return
	_flight.set_thrust(0.5 - 0.5 * cos(_age * TAU / DEMO_THRUST_PERIOD))
	_flight.set_bank(sin(_age * TAU / DEMO_BANK_PERIOD))

# --- Entrées ------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if _leaving:
		return
	var button := event as InputEventMouseButton
	if button != null:
		_on_mouse_button(button)
		return
	var motion := event as InputEventMouseMotion
	if motion != null and _dragging:
		_yaw_angle += motion.relative.x * DRAG_SENSITIVITY
		_pitch_angle = clampf(_pitch_angle + motion.relative.y * DRAG_SENSITIVITY,
			-deg_to_rad(PITCH_LIMIT_DEG), deg_to_rad(PITCH_LIMIT_DEG))
		_idle = 0.0
		return
	if event.is_action_pressed("codex_next"):
		_step(1)
	elif event.is_action_pressed("codex_prev"):
		_step(-1)
	elif event.is_action_pressed("codex_reset"):
		_reset_view()
		_audio.play(&"ui_select")

func _on_mouse_button(button: InputEventMouseButton) -> void:
	match button.button_index:
		MOUSE_BUTTON_LEFT:
			_dragging = button.pressed
			_idle = 0.0
		MOUSE_BUTTON_WHEEL_UP:
			if button.pressed:
				_zoom = clampf(_zoom - ZOOM_WHEEL_STEP, ZOOM_MIN, ZOOM_MAX)
				_idle = 0.0
		MOUSE_BUTTON_WHEEL_DOWN:
			if button.pressed:
				_zoom = clampf(_zoom + ZOOM_WHEEL_STEP, ZOOM_MIN, ZOOM_MAX)
				_idle = 0.0

func _step(direction: int) -> void:
	_audio.play(&"ui_select")
	_show(_index + direction)

func _leave() -> void:
	if _leaving:
		return
	_leaving = true
	_audio.play(&"ui_confirm")
	if not _game_state.transition_to(GameStateScript.State.BOOT):
		# On rentre quand même — un écran sans issue est pire qu'un état incohérent.
		# ⚠️ Mais PERSONNE ne rattrape cet état : `title_menu._ready()` ne touche pas à
		# `GameState.current`, et NOUVELLE PARTIE deviendrait inerte, en silence, sur le
		# `return` de `_start_game`. Le chemin est aujourd'hui inatteignable — CODEX ->
		# BOOT est autorisé, et `test_game_state.gd` le garde. Si un jour il ne l'est
		# plus, c'est la table de transitions qu'il faut corriger, pas cette ligne.
		push_error("[Codex] retour au titre refuse par GameState")
	_datasheet.fade_out(FADE_OUT, func() -> void: _scene_router.goto_scene(BOOT_SCENE))
