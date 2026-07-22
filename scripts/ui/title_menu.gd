extends CanvasLayer
## Interface de l'écran d'accueil : identité et menu navigable.
## Le diorama 3D sous-jacent est piloté par title_stage.gd et l'oscillogramme COMMS
## s'anime seul (scripts/ui/comms_trace.gd, partagé avec l'écran de pause) — ce
## script ne touche ni à la mise en scène ni à la télémétrie.
##
## Autoloads résolus par chemin (convention projet) : garde le script compilable en
## mode --script, où les globales d'autoload n'existent pas.

const GameStateScript := preload("res://scripts/core/game_state.gd")
const SceneRouterScript := preload("res://scripts/core/scene_router.gd")
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const OptionsMenuScene := preload("res://scenes/ui/options_menu.tscn")
const GRAYBOX_SCENE := "res://scenes/gameplay/graybox.tscn"
const CODEX_SCENE := "res://scenes/ui/codex.tscn"

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _scene_router: SceneRouterScript = get_node("/root/SceneRouter")
@onready var _audio: AudioManagerScript = get_node("/root/AudioManager")
@onready var _version_label: Label = %VersionLabel
@onready var _menu: VBoxContainer = %Menu
@onready var _fade: ColorRect = %Fade

var _options: Control
var _leaving: bool = false

func _ready() -> void:
	var version: String = ProjectSettings.get_setting("application/config/version", "0.0.0")
	_version_label.text = "v%s — prototype" % version
	_build_menu_focus()
	_fade.color.a = 1.0
	# Ouverture en fondu : l'accueil se lève du noir au lieu d'apparaître d'un coup.
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", 0.0, 0.8)
	print("[TitleMenu] ready (v%s)" % version)
	# Hooks de test (args après le séparateur `++`) : sauter droit à un écran.
	var args := OS.get_cmdline_user_args()
	if "--goto-graybox" in args:
		_start_game.call_deferred()
	elif "--goto-codex" in args:
		_open_codex.call_deferred()

func _build_menu_focus() -> void:
	var buttons := _buttons()
	if buttons.is_empty():
		return
	for button in buttons:
		button.focus_entered.connect(_on_focus_changed)
	buttons[0].grab_focus()

func _buttons() -> Array[Button]:
	var found: Array[Button] = []
	for child in _menu.get_children():
		var button := child as Button
		if button != null:
			found.append(button)
	return found

func _on_focus_changed() -> void:
	_audio.play(&"ui_select")

func _unhandled_input(event: InputEvent) -> void:
	if _leaving:
		return
	if _options != null and _options.visible:
		return # l'overlay possède l'input tant qu'il est levé
	if event.is_action_pressed("ui_options"):
		_open_options()
		get_viewport().set_input_as_handled()

# --- Actions du menu ----------------------------------------------------------

func _on_play_pressed() -> void:
	_audio.play(&"ui_confirm")
	_start_game()

func _on_codex_pressed() -> void:
	_audio.play(&"ui_confirm")
	_open_codex()

func _on_options_pressed() -> void:
	_audio.play(&"ui_confirm")
	_open_options()

func _on_quit_pressed() -> void:
	_audio.play(&"ui_confirm")
	# Jusqu'ici le jeu n'avait AUCUN moyen de se fermer, nulle part.
	get_tree().quit()

func _start_game() -> void:
	if _leaving:
		return
	if not ResourceLoader.exists(GRAYBOX_SCENE, "PackedScene"):
		push_error("[TitleMenu] scène de jeu introuvable : %s" % GRAYBOX_SCENE)
		return
	if not _game_state.transition_to(GameStateScript.State.FIGHTER_COMBAT):
		return
	_leaving = true
	# SceneRouter fait une coupe sèche ; on fond au noir d'abord, sinon l'accueil
	# disparaît d'une image à l'autre. La musique, elle, ne s'arrête PAS : le
	# niveau réclame Launch dans son propre _ready() et AudioManager enchaîne les
	# deux — couper au silence ici ne ferait qu'un trou dans le relais.
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", 1.0, 0.45)
	tween.tween_callback(func() -> void: _scene_router.goto_scene(GRAYBOX_SCENE))

## Le bestiaire est une SCÈNE, pas un overlay : il monte son propre présentoir 3D,
## sa caméra et ses lumières. Le poser au-dessus du diorama de l'accueil obligerait
## à masquer ce dernier et à se battre contre sa chorégraphie — pour un résultat que
## SceneRouter obtient d'une ligne.
func _open_codex() -> void:
	if _leaving:
		return
	if not ResourceLoader.exists(CODEX_SCENE, "PackedScene"):
		push_error("[TitleMenu] bestiaire introuvable : %s" % CODEX_SCENE)
		return
	if not _game_state.transition_to(GameStateScript.State.CODEX):
		return
	_leaving = true
	# Même fondu au noir que le lancement de partie : SceneRouter fait une coupe
	# sèche, et l'accueil disparaîtrait d'une image à l'autre.
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", 1.0, 0.45)
	tween.tween_callback(func() -> void: _scene_router.goto_scene(CODEX_SCENE))

func _open_options() -> void:
	if _options == null:
		_options = OptionsMenuScene.instantiate()
		# Le signal `closed` existait déjà et n'était écouté par personne : en
		# sortant des options, le focus restait nulle part et le menu ne
		# répondait plus au clavier.
		_options.closed.connect(_on_options_closed)
		add_child(_options)  # son _ready() l'ouvre
	else:
		_options.open()

## Le focus revient sur le bouton PAR SON NOM, pas par son rang : il valait `[1]`
## quand OPTIONS était le deuxième item, et l'insertion du bestiaire l'aurait
## silencieusement renvoyé sur ce dernier.
func _on_options_closed() -> void:
	var options_button := _menu.get_node_or_null("OptionsButton") as Button
	if options_button != null:
		options_button.grab_focus()
