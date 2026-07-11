extends Node3D
## Level director: sequences the level's phases (spec §5, §6, §37) and wires the
## player, HUD, VFX, camera, pickups and encounters together.
##   FIGHTER_WAVES -> MINI_BOSS -> DOCKING -> COMMAND_TRANSFER -> FORTRESS_BOSS -> VICTORY

const GameStateScript := preload("res://scripts/core/game_state.gd")
const MiniBossScene := preload("res://scenes/bosses/choir_harvester.tscn")

enum Phase { FIGHTER_WAVES, MINI_BOSS, DOCKING, COMMAND_TRANSFER, FORTRESS_BOSS, VICTORY }

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _wave_spawner: WaveSpawner = get_node_or_null("WaveSpawner")
@onready var _vfx: VFXManager = get_node_or_null("VFXManager") as VFXManager
@onready var _camera_director: CameraDirector = get_node_or_null("CameraDirector") as CameraDirector
@onready var _player: PlayerFighterController = get_node_or_null("PlayerFighter") as PlayerFighterController
@onready var _hud: CanvasLayer = get_node_or_null("FighterHUD") as CanvasLayer
@onready var _pickups: PickupManager = get_node_or_null("PickupManager") as PickupManager
@onready var _bullet_manager: BulletManager = get_node_or_null("BulletManager") as BulletManager

var _phase: int = Phase.FIGHTER_WAVES
var _boss: BossController

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
	var args := OS.get_cmdline_user_args()
	if "--no-wave" in args and _wave_spawner != null:
		_wave_spawner.set_physics_process(false)
	if "--pickup-demo" in args and _pickups != null:
		_pickups.spawn(Pickup.Kind.POWER, Vector2(-3.0, 0.0))
		_pickups.spawn(Pickup.Kind.SHIELD, Vector2(0.0, 0.0))
		_pickups.spawn(Pickup.Kind.SCORE, Vector2(3.0, 0.0))
	if "--skip-to-boss" in args:
		_start_mini_boss()
	print("[Level] ready — phase FIGHTER_WAVES")

# --- Fighter waves -----------------------------------------------------------

func _on_wave_cleared() -> void:
	if _phase != Phase.FIGHTER_WAVES:
		return
	print("[Level] waves cleared — mini-boss incoming")
	_start_mini_boss()

func _on_enemy_destroyed(enemy: EnemyController) -> void:
	_game_state.add_score(enemy.data.score_value)
	_boom(enemy.global_position, VfxExplosion.Category.MEDIUM, 0.35)
	if _pickups != null:
		_pickups.roll_drop(enemy.global_position)

# --- Mini-boss ---------------------------------------------------------------

func _start_mini_boss() -> void:
	_phase = Phase.MINI_BOSS
	_boss = MiniBossScene.instantiate() as BossController
	add_child(_boss)
	_boss.health_changed.connect(_on_boss_health)
	_boss.defeated.connect(_on_mini_boss_defeated)
	_boss.begin(_bullet_manager, _player)
	if _hud != null:
		_hud.show_boss(_boss.display_name)

func _on_boss_health(ratio: float) -> void:
	if _hud != null:
		_hud.set_boss_health(ratio)

func _on_mini_boss_defeated(world_position: Vector3) -> void:
	_boom(world_position, VfxExplosion.Category.HEAVY, 1.0)
	if _hud != null:
		_hud.hide_boss()
	if _boss != null:
		_boss.queue_free()
		_boss = null
	print("[Level] mini-boss defeated — score %d" % _game_state.score)
	_start_docking()

# --- Docking (placeholder until G-F) ----------------------------------------

func _start_docking() -> void:
	_phase = Phase.DOCKING
	print("[Level] DOCKING (to be implemented)")

# --- Player feedback ---------------------------------------------------------

func _on_player_hit(_world_position: Vector3) -> void:
	if _camera_director != null:
		_camera_director.add_trauma(0.45)

func _on_player_destroyed(world_position: Vector3) -> void:
	_boom(world_position, VfxExplosion.Category.HEAVY, 0.9)

func _on_game_over() -> void:
	print("[Level] all fighters lost — continue")
	if _player != null:
		_player.continue_run()

# --- Helpers -----------------------------------------------------------------

func _boom(world_position: Vector3, category: VfxExplosion.Category, trauma: float) -> void:
	if _vfx != null:
		_vfx.spawn_explosion(world_position, category)
	if _camera_director != null:
		_camera_director.add_trauma(trauma)
