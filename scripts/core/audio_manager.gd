extends Node
## Sound effects (autoload "AudioManager"). Plays the cues declared in
## resources/audio/sfx_bank.tres through a round-robin pool of AudioStreamPlayers
## (spec §18.3, §18.5). Non-positional (shmup): every cue plays at a consistent level.
## Cue tuning (level, pitch range, rate limit) lives in the bank, never here.

const SfxThrottleScript := preload("res://scripts/audio/sfx_throttle.gd")
const SFX_BANK := preload("res://resources/audio/sfx_bank.tres")

const _POOL_SIZE := 16
const _FALLBACK_BUS := "Master"

var _index: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []
var _next: int = 0
var _throttle: SfxThrottle = SfxThrottleScript.new()
var _rng := RandomNumberGenerator.new()

func _ready() -> void:
	for error in SFX_BANK.validate():
		push_error("[Audio] invalid sfx bank: %s" % error)
	_index = SFX_BANK.build_index()
	for i in _POOL_SIZE:
		var player := AudioStreamPlayer.new()
		player.bus = _resolve_bus("SFX")
		add_child(player)
		_players.append(player)

## Play a cue by id. `volume_db` is an offset applied on top of the cue's own level,
## for context (a boss explosion is the same cue, louder).
func play(cue: StringName, volume_db: float = 0.0) -> void:
	var data: AudioCueData = _index.get(cue)
	if data == null:
		push_warning("[Audio] unknown cue: %s" % cue)
		return
	var now := float(Time.get_ticks_msec()) / 1000.0
	if not _throttle.should_play(cue, data.min_interval, now):
		return
	var player := _players[_next]
	_next = (_next + 1) % _POOL_SIZE
	player.stream = data.stream
	player.bus = _resolve_bus(data.bus)
	player.volume_db = data.volume_db + volume_db
	player.pitch_scale = _rng.randf_range(data.pitch_min, data.pitch_max)
	player.play()

func stop_all_sfx() -> void:
	for player in _players:
		player.stop()
	_throttle.reset()

## Buses come from resources/audio/default_bus_layout.tres. If the layout failed to
## load, fall back to Master rather than dropping the sound entirely.
func _resolve_bus(bus: String) -> String:
	if AudioServer.get_bus_index(bus) < 0:
		push_warning("[Audio] missing bus '%s', falling back to %s" % [bus, _FALLBACK_BUS])
		return _FALLBACK_BUS
	return bus
