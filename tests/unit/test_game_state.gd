extends "res://tests/test_case.gd"
## GameState transitions (spec §28.2: state machine transitions).
## GameState is an autoload, absent in --script mode: instantiate by hand.

const GameStateScript := preload("res://scripts/core/game_state.gd")

func _make_state() -> Node:
	# Not added to a tree: _ready() never runs, no InputMap side effects.
	return GameStateScript.new()

func test_initial_state_is_boot() -> void:
	var gs := _make_state()
	assert_eq(gs.current, GameStateScript.State.BOOT, "initial state")
	gs.free()

func test_valid_transition_boot_to_combat() -> void:
	var gs := _make_state()
	assert_true(gs.transition_to(GameStateScript.State.FIGHTER_COMBAT), "BOOT -> FIGHTER_COMBAT allowed")
	assert_eq(gs.current, GameStateScript.State.FIGHTER_COMBAT, "state updated")
	gs.free()

func test_invalid_transition_is_refused() -> void:
	var gs := _make_state()
	print("[test] expected error below (invalid transition):")
	assert_false(gs.transition_to(GameStateScript.State.VICTORY), "BOOT -> VICTORY refused")
	assert_eq(gs.current, GameStateScript.State.BOOT, "state unchanged after refusal")
	gs.free()

func test_full_run_path() -> void:
	var gs := _make_state()
	assert_true(gs.transition_to(GameStateScript.State.LOADING), "BOOT -> LOADING")
	assert_true(gs.transition_to(GameStateScript.State.FIGHTER_COMBAT), "LOADING -> FIGHTER_COMBAT")
	assert_true(gs.transition_to(GameStateScript.State.VICTORY), "FIGHTER_COMBAT -> VICTORY")
	assert_true(gs.transition_to(GameStateScript.State.BOOT), "VICTORY -> BOOT")
	gs.free()

## Abandonner une partie pour revenir au titre, puis EN RELANCER UNE. C'est le
## second pas qui comptait : le retour au titre laissait `current` sur
## FIGHTER_COMBAT, et le lancement suivant était refusé — sans rien à l'écran,
## puisque personne ne teste le retour de transition_to.
func test_abandoning_a_run_lets_the_next_one_start() -> void:
	var gs := _make_state()
	assert_true(gs.transition_to(GameStateScript.State.FIGHTER_COMBAT), "BOOT -> FIGHTER_COMBAT")
	assert_true(gs.transition_to(GameStateScript.State.BOOT), "pause -> titre en pleine partie")
	assert_true(gs.transition_to(GameStateScript.State.FIGHTER_COMBAT),
		"et on peut relancer une partie derrière")
	gs.free()

func test_score_accumulates() -> void:
	var gs := _make_state()
	gs.add_score(100)
	gs.add_score(250)
	assert_eq(gs.score, 350, "score accumulates")
	gs.reset_session()
	assert_eq(gs.score, 0, "score resets")
	gs.free()
