extends Control
## Boot / title screen. Phase 0 milestone: the exported .exe shows this screen.
## Pressing accept routes to the graybox scene once it exists (Phase 1).
## Autoloads are resolved by path (project convention: keeps every script
## compilable in --script mode, where autoload globals do not exist).

const GameStateScript := preload("res://scripts/core/game_state.gd")
const SceneRouterScript := preload("res://scripts/core/scene_router.gd")
const GRAYBOX_SCENE := "res://scenes/gameplay/graybox.tscn"

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _scene_router: SceneRouterScript = get_node("/root/SceneRouter")
@onready var _version_label: Label = %VersionLabel

func _ready() -> void:
	var version: String = ProjectSettings.get_setting("application/config/version", "0.0.0")
	_version_label.text = "v%s — prototype" % version
	print("[BootScreen] ready (v%s)" % version)
	# Test hook (args after the `--`/`++` separator): jump straight into gameplay.
	if "--goto-graybox" in OS.get_cmdline_user_args():
		_start_graybox.call_deferred()

func _start_graybox() -> void:
	if ResourceLoader.exists(GRAYBOX_SCENE, "PackedScene"):
		if _game_state.transition_to(GameStateScript.State.FIGHTER_COMBAT):
			_scene_router.goto_scene(GRAYBOX_SCENE)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		_start_graybox()
