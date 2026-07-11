extends Node
## Global game state machine (autoload "GameState").
## Subset of the states defined in the spec §20.4; grows with the project.
## All transitions are centralized, validated and logged (spec §20.4).

enum State { BOOT, LOADING, FIGHTER_COMBAT, GAME_OVER, VICTORY }

signal state_changed(previous: State, next: State)
signal score_changed(total: int)

## Allowed transitions; a state absent from this table cannot transition at all.
const _ALLOWED: Dictionary = {
	State.BOOT: [State.LOADING, State.FIGHTER_COMBAT],
	State.LOADING: [State.FIGHTER_COMBAT],
	State.FIGHTER_COMBAT: [State.GAME_OVER, State.VICTORY],
	State.GAME_OVER: [State.FIGHTER_COMBAT, State.BOOT],
	State.VICTORY: [State.BOOT],
}

var current: State = State.BOOT
var score: int = 0

func _ready() -> void:
	InputBootstrap.register_actions()
	if "--novsync" in OS.get_cmdline_user_args():
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	print("[GameState] %s" % State.keys()[current])

func transition_to(next: State) -> bool:
	if not _ALLOWED.has(current) or not (next in _ALLOWED[current]):
		push_error("[GameState] invalid transition %s -> %s" %
			[State.keys()[current], State.keys()[next]])
		return false
	var previous := current
	current = next
	print("[GameState] %s -> %s" % [State.keys()[previous], State.keys()[next]])
	state_changed.emit(previous, next)
	return true

func add_score(points: int) -> void:
	score += points
	score_changed.emit(score)

func reset_session() -> void:
	score = 0
	score_changed.emit(score)
