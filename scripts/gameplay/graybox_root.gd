extends Node3D
## Level director: sequences the level's phases (spec §5, §6, §37) and wires the
## player, HUD, VFX, camera, pickups and encounters together.
##   FIGHTER_WAVES -> MINI_BOSS -> DOCKING -> COMMAND_TRANSFER -> FORTRESS_BOSS -> VICTORY

const GameStateScript := preload("res://scripts/core/game_state.gd")
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const MiniBossScene := preload("res://scenes/bosses/choir_harvester.tscn")
const FinalBossScene := preload("res://scenes/bosses/pale_leviathan.tscn")
const CitadelScene := preload("res://scenes/fortress/aegis_citadel.tscn")
const FortressBattery := preload("res://resources/weapons/fortress_battery.tres")
const VictoryScene := preload("res://scenes/ui/victory_screen.tscn")

const _FORTRESS_SPEED := 9.0
const _FORTRESS_INTEGRITY_MAX := 200.0
const _FORTRESS_FIRE_INTERVAL := 0.16
const _FORTRESS_X_LIMIT := 8.5
const _FORTRESS_Y := -3.8
const _FORTRESS_SCALE := 0.38
const _FINAL_BOSS_SCALE := 0.75
const _FORTRESS_HITBOX_RADIUS := 1.5

const _COLOR_ALLY := Color(0.247, 0.851, 0.91)
const _COLOR_GOLD := Color(0.894, 0.71, 0.29)

## Impact tints: the palette's cold impact flash when we strike an enemy hull, the
## shield's own cyan when something strikes us.
const _HULL_IMPACT_TINT := Color(0.851, 0.902, 0.949)
const _SHIELD_IMPACT_TINT := Color(0.247, 0.851, 0.91)

## Shield alarm thresholds (spec §8.3: audible warning under 25%). The alarm re-arms
## only above 35% so a shield hovering around the threshold does not stutter.
const _ALARM_TRIGGER_RATIO := 0.25
const _ALARM_REARM_RATIO := 0.35

enum Phase { FIGHTER_WAVES, MINI_BOSS, DOCKING, COMMAND_TRANSFER, FORTRESS_BOSS, VICTORY }

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _wave_spawner: WaveSpawner = get_node_or_null("WaveSpawner")
@onready var _vfx: VFXManager = get_node_or_null("VFXManager") as VFXManager
@onready var _camera_director: CameraDirector = get_node_or_null("CameraDirector") as CameraDirector
@onready var _player: PlayerFighterController = get_node_or_null("PlayerFighter") as PlayerFighterController
@onready var _hud: CanvasLayer = get_node_or_null("FighterHUD") as CanvasLayer
@onready var _pickups: PickupManager = get_node_or_null("PickupManager") as PickupManager
@onready var _bullets: BulletManager = get_node_or_null("BulletManager") as BulletManager
@onready var _bullet_manager: BulletManager = get_node_or_null("BulletManager") as BulletManager
@onready var _audio: AudioManagerScript = get_node_or_null("/root/AudioManager") as AudioManagerScript

var _phase: int = Phase.FIGHTER_WAVES
var _boss: BossController
var _citadel: AegisCitadel
var _final_boss: BossController
var _fortress_control: bool = false
var _fortress_target: BulletTarget
var _fortress_integrity: float = _FORTRESS_INTEGRITY_MAX
var _fortress_fire_timer: float = 0.0
var _fortress_side: int = 1
var _demo: bool = false
var _demo_time: float = 0.0
var _alarm_armed: bool = true
## One instance for the whole run: resolving the musical state must not allocate.
var _music: MusicContext = MusicContext.new()
var _engine_running: bool = false

func _ready() -> void:
	_game_state.reset_session()
	for node in get_tree().get_nodes_in_group("enemies"):
		var enemy := node as EnemyController
		enemy.destroyed.connect(_on_enemy_destroyed)
		enemy.fired.connect(_on_enemy_fired)
		enemy.hit.connect(_on_enemy_hit)
	if _bullets != null:
		_bullets.target_hit.connect(_on_bullet_hit)
	if _wave_spawner != null:
		_wave_spawner.wave_cleared.connect(_on_wave_cleared)
		_wave_spawner.progress_changed.connect(_on_wave_progress)
	if _player != null:
		_player.hit_taken.connect(_on_player_hit)
		_player.destroyed_at.connect(_on_player_destroyed)
		_player.game_over.connect(_on_game_over)
		_player.fired.connect(_on_player_fired)
		_player.shield_changed.connect(_on_player_shield_changed)
	if _hud != null and _player != null:
		_hud.bind_player(_player)
		_hud.bind_score(_game_state)
	if _pickups != null:
		_pickups.picked_up.connect(_on_pickup)
	var args := OS.get_cmdline_user_args()
	_demo = "--demo" in args
	# Perf bisection flags.
	if "--no-backdrop" in args:
		var bd := get_node_or_null("SpaceBackdrop") as Node3D
		if bd != null:
			bd.visible = false
	if "--no-glow" in args:
		var we := get_node_or_null("WorldEnvironment") as WorldEnvironment
		if we != null and we.environment != null:
			we.environment.glow_enabled = false
	if "--no-wave" in args and _wave_spawner != null:
		_wave_spawner.set_physics_process(false)
	if "--pickup-demo" in args and _pickups != null:
		_pickups.spawn(Pickup.Kind.POWER, Vector2(-3.0, 0.0))
		_pickups.spawn(Pickup.Kind.SHIELD, Vector2(0.0, 0.0))
		_pickups.spawn(Pickup.Kind.SCORE, Vector2(3.0, 0.0))
	if "--skip-to-boss" in args:
		_start_mini_boss()
	elif "--skip-to-dock" in args:
		if _wave_spawner != null:
			_wave_spawner.set_physics_process(false)
		_start_docking()
	elif "--skip-to-fortress" in args:
		if _wave_spawner != null:
			_wave_spawner.set_physics_process(false)
		if _player != null:
			_player.stow()
		_start_fortress_boss()
	elif "--skip-to-victory" in args:
		if _wave_spawner != null:
			_wave_spawner.set_physics_process(false)
		_game_state.add_score(28450)
		_start_victory()
	# Start the score. Runs after the --skip-to-* flags, so a skipped run opens on the
	# state it actually jumped to instead of fading out of Launch.
	_update_music()
	print("[Level] ready — phase FIGHTER_WAVES")

# --- Adaptive music (spec §18.2) ---------------------------------------------
# The level is the only thing that knows how the fight is going; MusicDirector turns
# that into a state and AudioManager plays it. Nothing here picks a track by name.

func _set_phase(phase: int) -> void:
	_phase = phase
	_music.level_phase = phase
	_update_music()

func _on_wave_progress(ratio: float) -> void:
	_music.wave_progress = ratio
	_update_music()

func _update_music() -> void:
	if _audio != null:
		_audio.set_music_state(MusicDirector.resolve(_music))

# --- Fighter waves -----------------------------------------------------------

func _on_wave_cleared() -> void:
	if _phase != Phase.FIGHTER_WAVES:
		return
	print("[Level] waves cleared — mini-boss incoming")
	_start_mini_boss()

func _on_enemy_destroyed(enemy: EnemyController) -> void:
	_game_state.add_score(enemy.data.score_value)
	_boom(enemy.global_position, VfxExplosion.Category.MEDIUM, 0.35)
	_sfx(&"medium_explosion")
	if _pickups != null:
		_pickups.roll_drop(enemy.global_position)

## One cue per kind: a bonus has to be identifiable without looking straight at it
## (docs/forge/CHARTE_CREATIVE.md — never colour alone).
func _on_pickup(kind: int, _world_position: Vector3) -> void:
	match kind:
		Pickup.Kind.POWER:
			_sfx(&"pickup_power")
		Pickup.Kind.SHIELD:
			_sfx(&"pickup_shield")
		Pickup.Kind.SCORE:
			_sfx(&"pickup_score")

# --- Combat chatter (rate-limited by the cue bank) ---------------------------

func _on_player_fired() -> void:
	_sfx(&"player_pulse")

func _on_enemy_fired() -> void:
	_sfx(&"enemy_pulse")

func _on_enemy_hit() -> void:
	_sfx(&"hull_impact")

## Every connecting bullet, from either side. Coloured by who was hit, so a glance
## tells you whether you landed a shot or took one: cold white on an enemy hull,
## shield cyan on ours (docs/forge/output/graybox_palette.md).
func _on_bullet_hit(plane_position: Vector2, victim_team: int) -> void:
	if _vfx == null:
		return
	var tint := _SHIELD_IMPACT_TINT if victim_team == BulletManager.Team.PLAYER \
		else _HULL_IMPACT_TINT
	_vfx.spawn_explosion(GameplayPlane.to_world(plane_position),
		VfxExplosion.Category.IMPACT, tint)

## Audible warning when the shield drops under 25% (spec §8.3).
func _on_player_shield_changed(ratio: float, _current: float, _maximum: float) -> void:
	if _alarm_armed and ratio <= _ALARM_TRIGGER_RATIO:
		_alarm_armed = false
		_sfx(&"danger_alarm")
	elif not _alarm_armed and ratio >= _ALARM_REARM_RATIO:
		_alarm_armed = true

# --- Mini-boss ---------------------------------------------------------------

func _start_mini_boss() -> void:
	_set_phase(Phase.MINI_BOSS)
	_boss = MiniBossScene.instantiate() as BossController
	add_child(_boss)
	_boss.health_changed.connect(_on_boss_health)
	_boss.defeated.connect(_on_mini_boss_defeated)
	_boss.begin(_bullet_manager, _player)
	_sfx(&"danger_alarm")
	if _hud != null:
		_hud.show_boss(_boss.display_name)

func _on_boss_health(ratio: float) -> void:
	if _hud != null:
		_hud.set_boss_health(ratio)
	# Only the fortress boss drives the music: the mini-boss shares Fleet Battle.
	if _phase == Phase.FORTRESS_BOSS:
		_music.boss_health_ratio = ratio
		_update_music()

func _on_mini_boss_defeated(world_position: Vector3) -> void:
	_game_state.add_score(5000)
	_boom(world_position, VfxExplosion.Category.HEAVY, 1.0)
	_sfx(&"heavy_explosion")
	if _hud != null:
		_hud.hide_boss()
	if _boss != null:
		_boss.queue_free()
		_boss = null
	print("[Level] mini-boss defeated — score %d" % _game_state.score)
	_start_docking()

# --- Docking (spec §6.5) -----------------------------------------------------

func _start_docking() -> void:
	_set_phase(Phase.DOCKING)
	print("[Level] DOCKING")
	_citadel = CitadelScene.instantiate() as AegisCitadel
	_citadel.plane_position = Vector2(0.0, 22.0) # off-screen above
	add_child(_citadel)
	_citadel.arrived.connect(_on_citadel_arrived, CONNECT_ONE_SHOT)
	_citadel.slide_to(Vector2(0.0, 11.0), 9.0)
	_banner("DOCKING", _COLOR_ALLY, 1.4)

func _on_citadel_arrived() -> void:
	if _player != null:
		_player.autopilot_reached.connect(_on_player_docked, CONNECT_ONE_SHOT)
		_player.begin_autopilot(Vector2(0.0, 6.3))

func _on_player_docked() -> void:
	_boom(GameplayPlane.to_world(Vector2(0.0, 6.6)), VfxExplosion.Category.MEDIUM, 0.5)
	_sfx(&"docking_lock")
	if _player != null:
		_player.stow()
	_start_command_transfer()

# --- Command transfer (spec §6.6) -------------------------------------------

func _start_command_transfer() -> void:
	_set_phase(Phase.COMMAND_TRANSFER)
	print("[Level] COMMAND TRANSFER")
	_banner("COMMAND TRANSFER", _COLOR_GOLD, 1.8)
	get_tree().create_timer(2.6).timeout.connect(_start_fortress_boss)

# --- Fortress boss (spec §12) -----------------------------------------------

func _start_fortress_boss() -> void:
	_set_phase(Phase.FORTRESS_BOSS)
	print("[Level] FORTRESS BOSS")
	# Ensure the fortress exists (direct skip may bypass docking).
	if _citadel == null:
		_citadel = CitadelScene.instantiate() as AegisCitadel
		add_child(_citadel)
	_citadel.scale = Vector3.ONE * _FORTRESS_SCALE
	_citadel.slide_to(Vector2(0.0, _FORTRESS_Y), 12.0)
	_citadel.arrived.connect(_begin_fortress_control, CONNECT_ONE_SHOT)

func _begin_fortress_control() -> void:
	_fortress_target = BulletTarget.make(BulletManager.Team.PLAYER, _FORTRESS_HITBOX_RADIUS,
		Callable(self, "_on_fortress_hit"))
	_fortress_target.position = _citadel.plane_position
	_bullet_manager.register_target(_fortress_target)
	_fortress_integrity = _FORTRESS_INTEGRITY_MAX
	_fortress_control = true
	if _hud != null:
		_hud.set_integrity(1.0, _fortress_integrity)
	# Summon the final boss.
	_final_boss = FinalBossScene.instantiate() as BossController
	_final_boss.plane_position = Vector2(0.0, 12.0)
	_final_boss.scale = Vector3.ONE * _FINAL_BOSS_SCALE
	add_child(_final_boss)
	_final_boss.health_changed.connect(_on_boss_health)
	_final_boss.phase_changed.connect(_on_final_boss_phase)
	_final_boss.defeated.connect(_on_final_boss_defeated)
	_final_boss.begin(_bullet_manager, _player)
	_sfx(&"danger_alarm")
	if _hud != null:
		_hud.show_boss(_final_boss.display_name)
	_banner("DEFEND THE CORE", _COLOR_GOLD, 1.6)

func _on_final_boss_phase(index: int, total: int) -> void:
	if _camera_director != null:
		_camera_director.add_trauma(0.5)
	_sfx(&"boss_phase_shift")
	_music.boss_phase = index
	_music.boss_phase_count = total
	_update_music()
	print("[Level] boss phase %d/%d" % [index + 1, total])

func _physics_process(delta: float) -> void:
	_update_engine_hum()
	if not _fortress_control:
		return
	var move_x: float
	if _demo:
		_demo_time += delta
		move_x = sin(_demo_time * 0.8)
	else:
		move_x = Input.get_axis("move_left", "move_right")
	_citadel.plane_position.x = clampf(_citadel.plane_position.x + move_x * _FORTRESS_SPEED * delta,
		-_FORTRESS_X_LIMIT, _FORTRESS_X_LIMIT)
	_citadel.position = GameplayPlane.to_world(_citadel.plane_position)
	_fortress_target.position = _citadel.plane_position
	_fortress_fire_timer -= delta
	if (_demo or Input.is_action_pressed("fire_primary")) and _fortress_fire_timer <= 0.0:
		_fortress_fire_timer = _FORTRESS_FIRE_INTERVAL
		_fire_battery()

func _fire_battery() -> void:
	# Twin rail batteries, alternating left/right (spec §12.3), each leaving its own
	# muzzle baked into the citadel hull (ADR-0008) rather than a hard-coded offset.
	_fortress_side = -_fortress_side
	var origin := _citadel.battery_origin(0 if _fortress_side > 0 else 1)
	_bullet_manager.spawn_from_data(BulletManager.Team.PLAYER, origin, Vector2(0.0, 1.0), FortressBattery)
	if _fortress_side > 0: # twin battery: one cue per pair
		_sfx(&"rail_battery")
	if _camera_director != null:
		_camera_director.add_trauma(0.12)

func _on_fortress_hit(damage: float) -> void:
	_fortress_integrity = maxf(_fortress_integrity - damage, 0.0)
	if _hud != null:
		_hud.set_integrity(_fortress_integrity / _FORTRESS_INTEGRITY_MAX, _fortress_integrity)
	_sfx(&"hull_impact")
	if _camera_director != null:
		_camera_director.add_trauma(0.3)
	if _fortress_integrity <= 0.0:
		# Forgiving demo (spec §12.8): reset integrity instead of a hard fail.
		_fortress_integrity = _FORTRESS_INTEGRITY_MAX
		if _hud != null:
			_hud.set_integrity(1.0, _fortress_integrity)

# --- Helios Lance finale + victory (spec §12.7) -----------------------------

func _on_final_boss_defeated(world_position: Vector3) -> void:
	_game_state.add_score(20000)
	_fortress_control = false
	if _hud != null:
		_hud.hide_boss()
	_banner("HELIOS LANCE", _COLOR_ALLY, 1.4)
	_fire_helios_lance(world_position)

func _fire_helios_lance(target: Vector3) -> void:
	# Spectacular finish: heavy explosions along the boss + strong shake, then victory.
	_sfx(&"helios_lance")
	if _camera_director != null:
		_camera_director.add_trauma(1.0)
	for i in 8:
		var offset := Vector3(randf_range(-4.0, 4.0), 0.0, randf_range(-3.0, 3.0))
		get_tree().create_timer(0.12 * i).timeout.connect(
			_boom.bind(target + offset, VfxExplosion.Category.HEAVY, 0.7))
	get_tree().create_timer(1.8).timeout.connect(_start_victory)

func _start_victory() -> void:
	_set_phase(Phase.VICTORY)
	print("[Level] VICTORY — score %d" % _game_state.score)
	var screen := VictoryScene.instantiate()
	screen.setup(_game_state.score)
	add_child(screen)

## The victory theme waits for the last enemy shot to leave the screen, so the resolution
## does not land over incoming fire (adaptive_music_structure.md §mix). Until then the
## music stays on Final Charge.
func _process(_delta: float) -> void:
	if _phase != Phase.VICTORY or _music.hostiles_clear:
		return
	if _bullet_manager == null or _bullet_manager.team_count(BulletManager.Team.ENEMY) == 0:
		_music.hostiles_clear = true
		_update_music()

# --- Player feedback ---------------------------------------------------------

func _on_player_hit(_world_position: Vector3) -> void:
	_sfx(&"shield_impact")
	if _camera_director != null:
		_camera_director.add_trauma(0.45)

func _on_player_destroyed(world_position: Vector3) -> void:
	_boom(world_position, VfxExplosion.Category.HEAVY, 0.9)
	_sfx(&"player_death")

func _on_game_over() -> void:
	print("[Level] all fighters lost — continue")
	if _player != null:
		_player.continue_run()

# --- Helpers -----------------------------------------------------------------

## The fighter's engine bed follows its speed. Once the fighter is stowed (docking),
## the player *is* the fortress and the hum has no source: it stops for good.
func _update_engine_hum() -> void:
	if _audio == null:
		return
	var flying := _player != null and _player.visible
	if flying:
		_audio.set_engine_intensity(_player.speed_ratio())
		_engine_running = true
	elif _engine_running:
		_engine_running = false
		_audio.stop_engine()

## A banner is a beat, not just a label: it gets a swell so it reads without being read.
func _banner(text: String, color: Color, duration: float) -> void:
	if _hud != null:
		_hud.show_banner(text, color, duration)
	_sfx(&"ui_banner")

func _boom(world_position: Vector3, category: VfxExplosion.Category, trauma: float) -> void:
	if _vfx != null:
		_vfx.spawn_explosion(world_position, category)
	if _camera_director != null:
		_camera_director.add_trauma(trauma)

func _sfx(cue: StringName, volume_db: float = 0.0) -> void:
	if _audio != null:
		_audio.play(cue, volume_db)
