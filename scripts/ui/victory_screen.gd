class_name VictoryScreen
extends CanvasLayer
## Écran de victoire / rapport de mission (spec §14.3) — même interface Helios que
## l'accueil et la pause (ADR-0012 ; mise en scène : scenes/ui/victory_screen.tscn).
##
## Il ne met PAS l'arbre en pause : le niveau continue de tourner derrière (la musique
## de victoire attend que le dernier tir ennemi ait quitté l'écran, graybox_root.gd).
## L'écran se lève par-dessus, en fondu.
##
## Autoloads résolus par chemin (convention projet) : garde le script compilable en
## mode --script, où les globales d'autoload n'existent pas.

const GameStateScript := preload("res://scripts/core/game_state.gd")
const SceneRouterScript := preload("res://scripts/core/scene_router.gd")
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const BOOT_SCENE := "res://scenes/boot/boot.tscn"

const RAISE_TIME := 0.7   # le rapport se lève, il ne surgit pas
const FADE_TIME := 0.45

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _scene_router: SceneRouterScript = get_node("/root/SceneRouter")
@onready var _audio: AudioManagerScript = get_node("/root/AudioManager")
@onready var _scrim: ColorRect = %Scrim
@onready var _overlay: Control = %Overlay
@onready var _menu: VBoxContainer = %Menu
@onready var _fade: ColorRect = %Fade

var _leaving: bool = false
var _muting_focus: bool = false

## Appelé par le niveau entre instantiate() et add_child() : _ready() n'a pas encore
## tourné, donc on n'adresse ici QUE des nœuds (les %-noms sont résolus dès
## l'instanciation), jamais un @onready.
func setup(score: int) -> void:
	(%ScoreValue as Label).text = "%08d" % score
	(%RankValue as Label).text = _rank(score)

func _ready() -> void:
	var target_alpha := _scrim.color.a
	_scrim.color.a = 0.0
	_overlay.modulate.a = 0.0
	var buttons := _buttons()
	for button in buttons:
		button.focus_entered.connect(_on_focus_changed)
	if not buttons.is_empty():
		# Le focus est pris ici, comme sur la pause : sans lui, il fallait cliquer
		# avant que le clavier réponde. Son tic est étouffé — le fanfare de victoire
		# occupe déjà la bande son à cet instant.
		_muting_focus = true
		buttons[0].grab_focus()
		_muting_focus = false
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(_scrim, "color:a", target_alpha, RAISE_TIME)
	tween.tween_property(_overlay, "modulate:a", 1.0, RAISE_TIME)

func _buttons() -> Array[Button]:
	var found: Array[Button] = []
	for child in _menu.get_children():
		var button := child as Button
		if button != null:
			found.append(button)
	return found

func _on_focus_changed() -> void:
	if _muting_focus:
		return
	_audio.play(&"ui_select")

## ui_cancel est consommé ici même si l'écran n'en faisait rien : sinon Échap
## ouvrirait le menu de pause DERRIÈRE le rapport (le calque de pause vit toujours
## dans l'arbre, au layer 20), et le joueur se retrouverait avec deux menus empilés
## dont un invisible.
func _unhandled_input(event: InputEvent) -> void:
	if _leaving:
		return
	if event.is_action_pressed("ui_accept"):
		_on_replay_pressed()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_cancel"):
		_on_title_pressed()
		get_viewport().set_input_as_handled()

# --- Actions ------------------------------------------------------------------

func _on_replay_pressed() -> void:
	_audio.play(&"ui_confirm")
	_leave(func() -> void:
		_game_state.reset_session()
		get_tree().reload_current_scene())

func _on_title_pressed() -> void:
	_audio.play(&"ui_confirm")
	_leave(func() -> void:
		_game_state.reset_session()
		# Repasser l'état AVANT de router : sans ça, `current` reste sur la phase de
		# combat alors qu'on affiche le titre, et le lancement suivant est refusé
		# sans que rien ne le montre à l'écran.
		_game_state.transition_to(GameStateScript.State.BOOT)
		_scene_router.goto_scene(BOOT_SCENE))

## Fondu au noir avant de changer de scène. SceneRouter comme reload_current_scene
## font une coupe sèche : sans ça, on passait du rapport au jeu d'une image à l'autre.
func _leave(action: Callable) -> void:
	if _leaving:
		return
	_leaving = true
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", 1.0, FADE_TIME)
	tween.tween_callback(action)

static func _rank(score: int) -> String:
	if score >= 40000:
		return "S"
	if score >= 25000:
		return "A"
	if score >= 12000:
		return "B"
	return "C"
