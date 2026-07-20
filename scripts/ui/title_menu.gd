extends CanvasLayer
## Interface de l'écran d'accueil : identité, menu navigable, oscillogramme COMMS.
## Le diorama 3D sous-jacent est piloté par title_stage.gd — ce script ne touche
## à rien de la mise en scène.
##
## Autoloads résolus par chemin (convention projet) : garde le script compilable en
## mode --script, où les globales d'autoload n'existent pas.

const GameStateScript := preload("res://scripts/core/game_state.gd")
const SceneRouterScript := preload("res://scripts/core/scene_router.gd")
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const OptionsMenuScene := preload("res://scenes/ui/options_menu.tscn")
const GRAYBOX_SCENE := "res://scenes/gameplay/graybox.tscn"

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _scene_router: SceneRouterScript = get_node("/root/SceneRouter")
@onready var _audio: AudioManagerScript = get_node("/root/AudioManager")
@onready var _version_label: Label = %VersionLabel
@onready var _menu: VBoxContainer = %Menu
@onready var _fade: ColorRect = %Fade
@onready var _comms_trace: Line2D = %CommsTrace

var _options: Control
var _leaving: bool = false
var _age: float = 0.0

## Points de l'oscillogramme, PRÉALLOUÉS une fois : la courbe est réécrite en place
## à chaque image, jamais reconstruite (spec §31, zéro allocation en boucle).
const TRACE_POINTS := 48
const TRACE_WIDTH := 232.0
const TRACE_HEIGHT := 26.0
var _trace: PackedVector2Array = PackedVector2Array()

func _ready() -> void:
	var version: String = ProjectSettings.get_setting("application/config/version", "0.0.0")
	_version_label.text = "v%s — prototype" % version
	_trace.resize(TRACE_POINTS)
	_build_menu_focus()
	_fade.color.a = 1.0
	# Ouverture en fondu : l'accueil se lève du noir au lieu d'apparaître d'un coup.
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", 0.0, 0.8)
	print("[TitleMenu] ready (v%s)" % version)
	# Hook de test (args après le séparateur `++`) : sauter droit au gameplay.
	if "--goto-graybox" in OS.get_cmdline_user_args():
		_start_game.call_deferred()

## Le menu pause du jeu n'appelle jamais grab_focus() : au clavier comme au pad, il
## faut d'abord cliquer pour que la navigation réponde. On ne reproduit pas ça ici.
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

func _process(delta: float) -> void:
	_age += delta
	_update_comms_trace()

## Fausse télémétrie animée du bloc COMMS. Trois sinusoïdes de périodes premières
## entre elles, plus une dent de scie : assez irrégulier pour lire comme un signal,
## assez bon marché pour être gratuit.
func _update_comms_trace() -> void:
	for i in TRACE_POINTS:
		var t := float(i) / float(TRACE_POINTS - 1)
		var phase := _age * 2.1 + t * 9.0
		var value := sin(phase) * 0.5 + sin(phase * 2.7) * 0.28 + sin(phase * 6.1) * 0.12
		_trace[i] = Vector2(t * TRACE_WIDTH, -value * TRACE_HEIGHT * 0.5)
	_comms_trace.points = _trace

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

func _on_options_closed() -> void:
	var buttons := _buttons()
	if buttons.size() > 1:
		buttons[1].grab_focus()
