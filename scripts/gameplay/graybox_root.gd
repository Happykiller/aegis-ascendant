extends Node3D
## Graybox scene root: wires the player, HUD, VFX, camera and score together.

const GameStateScript := preload("res://scripts/core/game_state.gd")

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _wave_spawner: WaveSpawner = get_node_or_null("WaveSpawner")
@onready var _vfx: VFXManager = get_node_or_null("VFXManager") as VFXManager
@onready var _camera_director: CameraDirector = get_node_or_null("CameraDirector") as CameraDirector
@onready var _player: PlayerFighterController = get_node_or_null("PlayerFighter") as PlayerFighterController
@onready var _hud: CanvasLayer = get_node_or_null("FighterHUD") as CanvasLayer

func _ready() -> void:
	for enemy in get_tree().get_nodes_in_group("enemies"):
		(enemy as EnemyController).destroyed.connect(_on_enemy_destroyed)
	if _wave_spawner != null:
		_wave_spawner.wave_cleared.connect(_on_wave_cleared)
	if _player != null:
		_player.hit_taken.connect(_on_player_hit)
		_player.destroyed_at.connect(_on_player_destroyed)
		_player.game_over.connect(_on_game_over)
	if _hud != null and _player != null:
		_hud.bind_player(_player)
		_hud.bind_score(_game_state)
	print("[Graybox] ready")

func _on_wave_cleared() -> void:
	print("[Graybox] wave cleared — session score %d" % _game_state.score)

func _on_enemy_destroyed(enemy: EnemyController) -> void:
	_game_state.add_score(enemy.data.score_value)
	if _vfx != null:
		_vfx.spawn_explosion(enemy.global_position, VfxExplosion.Category.MEDIUM)
	if _camera_director != null:
		_camera_director.add_trauma(0.35)

func _on_player_hit(_world_position: Vector3) -> void:
	if _camera_director != null:
		_camera_director.add_trauma(0.45)

func _on_player_destroyed(world_position: Vector3) -> void:
	if _vfx != null:
		_vfx.spawn_explosion(world_position, VfxExplosion.Category.HEAVY)
	if _camera_director != null:
		_camera_director.add_trauma(0.9)

func _on_game_over() -> void:
	# Unlimited continues for the demo (spec §8.4): keep the run going.
	print("[Graybox] all fighters lost — continue")
	if _player != null:
		_player.continue_run()
