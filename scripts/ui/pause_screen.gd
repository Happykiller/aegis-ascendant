class_name PauseScreen
extends CanvasLayer
## Pause overlay. It always processes so Escape and its buttons remain usable
## while the gameplay tree is paused.

const GameStateScript := preload("res://scripts/core/game_state.gd")
const SceneRouterScript := preload("res://scripts/core/scene_router.gd")
const BOOT_SCENE := "res://scenes/boot/boot.tscn"

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _scene_router: SceneRouterScript = get_node("/root/SceneRouter")

func _ready() -> void:
	visible = false
	if "--pause-demo" in OS.get_cmdline_user_args():
		_open.call_deferred()

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if visible:
			_resume()
		else:
			_open()
		get_viewport().set_input_as_handled()

func _open() -> void:
	visible = true
	get_tree().paused = true

func _resume() -> void:
	get_tree().paused = false
	visible = false

func _return_to_title() -> void:
	get_tree().paused = false
	# Repasser l'état AVANT de router : sans ça, `current` restait sur
	# FIGHTER_COMBAT alors qu'on affiche le titre, et le lancement suivant
	# était refusé sans que rien ne le montre à l'écran.
	_game_state.transition_to(GameStateScript.State.BOOT)
	_scene_router.goto_scene(BOOT_SCENE)
