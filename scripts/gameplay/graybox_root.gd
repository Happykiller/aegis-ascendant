extends Node3D
## Level director: sequences the level's phases (spec §5, §6, §37) and wires the
## player, HUD, VFX, camera, pickups and encounters together.
##   FIGHTER_WAVES -> MINI_BOSS -> FINAL_BOSS -> DOCKING -> VICTORY
## Le joueur reste le chasseur de bout en bout (ADR-0010) : plus de transformation en
## forteresse ; le docking clot le niveau apres la defaite du boss final.

const GameStateScript := preload("res://scripts/core/game_state.gd")
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const MiniBossScene := preload("res://scenes/bosses/choir_harvester.tscn")
const FinalBossScene := preload("res://scenes/bosses/pale_leviathan.tscn")
const CitadelScene := preload("res://scenes/fortress/aegis_citadel.tscn")
const MissionReportScene := preload("res://scenes/ui/mission_report.tscn")

const _FINAL_BOSS_SCALE := 0.75

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

enum Phase { FIGHTER_WAVES, MINI_BOSS, FINAL_BOSS, DOCKING, VICTORY }

## Temps laissé à la mort du dernier chasseur avant que le rapport ne se lève. L'explosion
## dure ~0,7 s (VfxExplosion.HEAVY) et la secousse doit retomber : couper plus tôt
## escamoterait la seule chose que le joueur attend de voir à cet instant.
const DEFEAT_HOLD := 1.6

## Une partie ne se perd qu'une fois. Sans ce verrou, une seconde émission de
## `game_over` empilerait un deuxième rapport par-dessus le premier.
var _defeated: bool = false

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
	# L'écran de pause reprend l'interface entière (bloc d'identité en haut à gauche,
	# COMMS en bas à gauche, comme l'accueil) : ces places sont celles du HUD, et deux
	# blocs de texte superposés ne se lisent ni l'un ni l'autre. Le HUD s'efface donc
	# le temps de la pause. Il n'en sait rien — c'est le niveau qui les raccorde.
	var pause := get_node_or_null("PauseScreen") as PauseScreen
	if pause != null and _hud != null:
		pause.pause_toggled.connect(_on_pause_toggled)
	if _pickups != null:
		_pickups.picked_up.connect(_on_pickup)
	var args := OS.get_cmdline_user_args()
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
	# L'écran de victoire ne s'atteignait qu'en jouant l'arc entier — donc en pratique
	# il ne se REGARDAIT jamais, et il a vécu longtemps avec la police par défaut sans
	# que personne le voie (ADR-0006). Le score est semé pour que le rapport s'affiche
	# avec des chiffres plausibles plutôt qu'un 00000000 de rang C.
	if "--victory-demo" in args:
		_game_state.add_score(31500)
		_start_victory.call_deferred()
	# Même raison exactement que `--victory-demo` : un écran qu'on n'atteint qu'en
	# perdant trois vies ne se REGARDE jamais pendant le développement (ADR-0006), et
	# c'est ainsi qu'il a pu ne pas exister du tout pendant tout ce temps. Le drapeau
	# encaisse un coup mortel toutes les 3,5 s — l'espacement n'est pas décoratif :
	# mourir coûte 1,2 s de renaissance PUIS 2 s d'invulnérabilité, soit 3,2 s pendant
	# lesquelles un second coup ne porte pas. À 2,5 s, une fois sur deux le coup tombait
	# dans cette fenêtre et la défaite arrivait à un moment imprévisible.
	if "--defeat-demo" in args and _player != null:
		_game_state.add_score(9400)
		var killer := Timer.new()
		killer.wait_time = 3.5
		killer.autostart = true
		killer.timeout.connect(func() -> void: _player.take_contact_damage(9999.0))
		add_child(killer)
	if "--pickup-demo" in args and _pickups != null:
		_pickups.spawn(Pickup.Kind.POWER, Vector2(-3.0, 0.0))
		_pickups.spawn(Pickup.Kind.SHIELD, Vector2(0.0, 0.0))
		_pickups.spawn(Pickup.Kind.SCORE, Vector2(3.0, 0.0))
	if "--skip-to-boss" in args:
		_start_mini_boss()
	elif "--skip-to-final" in args:
		if _wave_spawner != null:
			_wave_spawner.set_physics_process(false)
		_start_final_boss()
	elif "--skip-to-dock" in args:
		if _wave_spawner != null:
			_wave_spawner.set_physics_process(false)
		_start_docking()
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

## Le HUD s'efface pendant la pause et revient à la reprise. Coupure franche
## assumée : elle se produit sous un voile qui monte en 0.16 s, donc invisible.
func _on_pause_toggled(is_paused: bool) -> void:
	if _hud != null:
		_hud.visible = not is_paused

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
	if _hud != null:
		_hud.pulse_pickup(kind)
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
	# Le corps du Harvester est blindé tant que son iris est fermé : sans ce retour,
	# tirer dessus ne produit RIEN à l'écran et se lit comme un défaut, pas comme une
	# armure. Le signal existe sur tout boss ; seul le Harvester le déclenche.
	_boss.deflected.connect(_on_boss_deflected)
	_bind_harvester(_boss)
	_boss.begin(_bullet_manager, _player)
	_sfx(&"danger_alarm")
	if _hud != null:
		_hud.show_boss(_boss.display_name)
		# APRÈS `begin()` : c'est lui qui monte le module, donc qui crée les appendices.
		# Interroger avant rendrait zéro et afficherait trois pastilles éteintes sur un
		# boss intact.
		var combat := _boss.get_node_or_null("Combat") as HarvesterCombat
		if combat != null:
			combat.publish_gauges()

## Raccorde le retour propre au Harvester, s'il porte son module de combat. Câblé
## AVANT `begin()` : c'est lui qui déclenche le montage du module.
func _bind_harvester(boss: BossController) -> void:
	var combat := boss.get_node_or_null("Combat") as HarvesterCombat
	if combat == null:
		return
	combat.limb_destroyed.connect(_on_harvester_limb_destroyed.bind(boss))
	combat.limb_gauge_changed.connect(_on_harvester_limb_gauge)
	combat.iris_opened.connect(_on_harvester_iris_opened.bind(boss))
	combat.iris_closed.connect(_on_harvester_iris_closed)

func _on_boss_deflected(world_position: Vector3) -> void:
	# Étincelle blanche et son de bouclier : la carapace RENVOIE le tir.
	_boom(world_position, VfxExplosion.Category.IMPACT, 0.0)
	_sfx(&"shield_impact")

func _on_harvester_limb_destroyed(_kind: StringName, boss: BossController) -> void:
	# `_boom` porte déjà la secousse : la redemander ici la doublerait.
	_boom(boss.global_position, VfxExplosion.Category.MEDIUM, 0.5)
	_sfx(&"medium_explosion")

## Une jauge d'appendice a bougé. Le niveau ne fait que relayer : le HUD ne connaît pas
## le Harvester, le module ne connaît pas le HUD.
func _on_harvester_limb_gauge(index: int, ratio: float, alive: bool) -> void:
	if _hud != null:
		_hud.set_boss_limb(index, ratio, alive)

## Le moment du combat : la carapace s'ouvre. Il doit s'entendre, se sentir et se
## lire — c'est la seule fenêtre où le joueur peut faire des dégâts.
func _on_harvester_iris_opened(boss: BossController) -> void:
	_boom(boss.global_position, VfxExplosion.Category.MEDIUM, 0.9)
	_sfx(&"boss_phase_shift")
	if _hud != null:
		_hud.show_banner("NOYAU EXPOSE", Color("d93d9c"), 1.4)

func _on_harvester_iris_closed() -> void:
	_sfx(&"docking_lock")
	if _hud != null:
		_hud.show_banner("CARAPACE REFERMEE", Color("e4b54a"), 1.0)

func _on_boss_health(ratio: float) -> void:
	if _hud != null:
		_hud.set_boss_health(ratio)
	# Only the final boss drives the boss music: the mini-boss shares Fleet Battle.
	if _phase == Phase.FINAL_BOSS:
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
	_start_final_boss()

# --- Final boss + docking close (ADR-0010; docking was the mid-level §6.5) ----

func _start_docking() -> void:
	_set_phase(Phase.DOCKING)
	print("[Level] DOCKING")
	_citadel = CitadelScene.instantiate() as AegisCitadel
	_citadel.plane_position = Vector2(0.0, 22.0) # off-screen above
	add_child(_citadel)
	_citadel.arrived.connect(_on_citadel_arrived, CONNECT_ONE_SHOT)
	_citadel.slide_to(Vector2(0.0, 11.0), 9.0)

func _on_citadel_arrived() -> void:
	if _player != null:
		_player.autopilot_reached.connect(_on_player_docked, CONNECT_ONE_SHOT)
		_player.begin_autopilot(Vector2(0.0, 6.3))

func _on_player_docked() -> void:
	_boom(GameplayPlane.to_world(Vector2(0.0, 6.6)), VfxExplosion.Category.MEDIUM, 0.5)
	_sfx(&"docking_lock")
	if _player != null:
		_player.stow()
	_start_victory()

func _start_final_boss() -> void:
	_set_phase(Phase.FINAL_BOSS)
	print("[Level] FINAL BOSS")
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
	_banner(_final_boss.display_name, _COLOR_GOLD, 1.6)

func _on_final_boss_phase(index: int, total: int) -> void:
	if _camera_director != null:
		_camera_director.add_trauma(0.5)
	_sfx(&"boss_phase_shift")
	_music.boss_phase = index
	_music.boss_phase_count = total
	_update_music()
	print("[Level] boss phase %d/%d" % [index + 1, total])

func _physics_process(_delta: float) -> void:
	_update_engine_hum()

# --- Helios Lance finale + victory (spec §12.7) -----------------------------

func _on_final_boss_defeated(world_position: Vector3) -> void:
	_game_state.add_score(20000)
	if _hud != null:
		_hud.hide_boss()
	# The boss is destroyed: remove its hull so it does not linger through the
	# finale and the docking close (it was staying visible before — ADR-0010).
	if _final_boss != null:
		_final_boss.queue_free()
		_final_boss = null
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
	get_tree().create_timer(1.8).timeout.connect(_start_docking)

func _start_victory() -> void:
	_set_phase(Phase.VICTORY)
	print("[Level] VICTORY — score %d" % _game_state.score)
	_show_report(MissionReport.Outcome.VICTORY)

## Le rapport de mission, dans l'une ou l'autre de ses issues.
##
## Même raison qu'à la pause de cacher le HUD : le rapport reprend les coins de l'écran,
## et le score qu'il affiche ferait doublon avec celui du HUD, à deux tailles différentes.
func _show_report(outcome: MissionReport.Outcome) -> void:
	var screen := MissionReportScene.instantiate()
	screen.setup(_game_state.score, outcome)
	add_child(screen)
	if _hud != null:
		_hud.visible = false

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

## Le dernier chasseur est perdu.
##
## ⚠️ CE CHEMIN NE MENAIT NULLE PART. Il relançait le joueur en silence (`continue_run`,
## continues illimités, spec §8.4) : l'état `GAME_OVER` de la machine globale était
## déclaré, transitions comprises, et n'était JAMAIS atteint. Une partie perdue se
## confondait donc avec une vie perdue, et le seul indice était une ligne de journal
## que le joueur ne lit pas.
##
## Les continues ne disparaissent pas pour autant : ils passent par le bouton
## « REESSAYER » du rapport, qui relance le niveau. Ce qui change, c'est qu'on le DIT.
func _on_game_over() -> void:
	if _phase == Phase.VICTORY or _defeated:
		return
	_defeated = true
	print("[Level] all fighters lost — DEFEAT, score %d" % _game_state.score)
	_game_state.transition_to(GameStateScript.State.GAME_OVER)
	# Le rapport se lève APRÈS l'explosion du dernier chasseur : le poser dans la même
	# image escamoterait la mort, qui est précisément ce que le joueur doit voir.
	get_tree().create_timer(DEFEAT_HOLD).timeout.connect(
		_show_report.bind(MissionReport.Outcome.DEFEAT))

# --- Helpers -----------------------------------------------------------------

## The fighter's engine bed follows its speed. Once the fighter is stowed at the
## closing docking sequence, the hum has no source: it stops for good.
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
