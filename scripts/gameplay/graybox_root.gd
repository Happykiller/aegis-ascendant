extends Node3D
## Graybox scene root: first playable segment sandbox (spec §37 items 12-19).
## Wires enemy destruction to the score and logs session events.

const GameStateScript := preload("res://scripts/core/game_state.gd")

@onready var _game_state: GameStateScript = get_node("/root/GameState")

func _ready() -> void:
	# Children _ready() ran first: every pooled/placed enemy already exists.
	for enemy in get_tree().get_nodes_in_group("enemies"):
		(enemy as EnemyController).destroyed.connect(_on_enemy_destroyed)
	print("[Graybox] ready")

func _on_enemy_destroyed(enemy: EnemyController) -> void:
	_game_state.add_score(enemy.data.score_value)
	print("[Graybox] %s destroyed (+%d) — score %d" %
		[enemy.data.display_name, enemy.data.score_value, _game_state.score])
