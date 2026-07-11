extends Node3D
## Graybox scene root: first playable segment sandbox (spec §37 items 12-19).
## Wires enemy destruction to score, explosions and screen shake.

const GameStateScript := preload("res://scripts/core/game_state.gd")

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _wave_spawner: WaveSpawner = get_node_or_null("WaveSpawner")
@onready var _vfx: VFXManager = get_node_or_null("VFXManager") as VFXManager
@onready var _camera_director: CameraDirector = get_node_or_null("CameraDirector") as CameraDirector

func _ready() -> void:
	# Children _ready() ran first: every pooled/placed enemy already exists.
	for enemy in get_tree().get_nodes_in_group("enemies"):
		(enemy as EnemyController).destroyed.connect(_on_enemy_destroyed)
	if _wave_spawner != null:
		_wave_spawner.wave_cleared.connect(_on_wave_cleared)
	print("[Graybox] ready")

func _on_wave_cleared() -> void:
	print("[Graybox] wave cleared — session score %d" % _game_state.score)

func _on_enemy_destroyed(enemy: EnemyController) -> void:
	_game_state.add_score(enemy.data.score_value)
	if _vfx != null:
		_vfx.spawn_explosion(enemy.global_position, VfxExplosion.Category.MEDIUM)
	if _camera_director != null:
		_camera_director.add_trauma(0.35)
