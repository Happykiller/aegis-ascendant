extends Node
## Sound effects (autoload "AudioManager"). Plays the cues declared in
## resources/audio/sfx_bank.tres through a round-robin pool of AudioStreamPlayers
## (spec §18.3, §18.5). Non-positional (shmup): every cue plays at a consistent level.
## Cue tuning (level, pitch range, rate limit) lives in the bank, never here.

const SfxThrottleScript := preload("res://scripts/audio/sfx_throttle.gd")
const SFX_BANK := preload("res://resources/audio/sfx_bank.tres")
const MUSIC_BANK := preload("res://resources/audio/music_bank.tres")

const _POOL_SIZE := 16
const _FALLBACK_BUS := "Master"
const _ENGINE_CUE := &"engine_loop"
## The hum is a bed, not an event: it never rises above the cues it sits under.
const _ENGINE_IDLE_DB := -8.0
const _ENGINE_PITCH_RANGE := 0.18
## Level a music deck sits at when it is the active one, and when it is faded out.
const _MUSIC_ON_DB := -3.0
const _MUSIC_OFF_DB := -60.0

var _index: Dictionary = {}
var _music_index: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []
var _next: int = 0
var _throttle: SfxThrottle = SfxThrottleScript.new()
var _rng := RandomNumberGenerator.new()
var _engine: AudioStreamPlayer
var _engine_base_db: float = 0.0

## Two decks: one plays, the other is faded in under it, then they swap. That is the whole
## crossfade (spec §18.2 — a state change is never a hard cut).
var _music_decks: Array[AudioStreamPlayer] = []
var _active_deck: int = 0
var _music_state: int = MusicDirector.State.SILENT
var _music_tween: Tween

func _ready() -> void:
	for error in SFX_BANK.validate():
		push_error("[Audio] invalid sfx bank: %s" % error)
	for error in MUSIC_BANK.validate():
		push_error("[Audio] invalid music bank: %s" % error)
	_index = SFX_BANK.build_index()
	_music_index = MUSIC_BANK.build_index()
	_enable_loops(SFX_BANK)
	_enable_loops(MUSIC_BANK)
	for i in _POOL_SIZE:
		var player := AudioStreamPlayer.new()
		player.bus = _resolve_bus("SFX")
		add_child(player)
		_players.append(player)
	_engine = AudioStreamPlayer.new()
	_engine.bus = _resolve_bus("SFX")
	add_child(_engine)
	for i in 2:
		var deck := AudioStreamPlayer.new()
		deck.bus = _resolve_bus("Music")
		deck.volume_db = _MUSIC_OFF_DB
		add_child(deck)
		_music_decks.append(deck)

## Looping belongs to the imported stream, not to the .import file: forcing it here means
## the flag survives every regeneration of the assets.
func _enable_loops(bank: AudioCueBank) -> void:
	for cue: AudioCueData in bank.cues:
		if not cue.looping:
			continue
		var wav := cue.stream as AudioStreamWAV
		if wav != null:
			wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
			wav.loop_begin = 0
			wav.loop_end = 0
			continue
		var vorbis := cue.stream as AudioStreamOggVorbis
		if vorbis != null:
			vorbis.loop = true

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

## Engine bed under the fighter. `intensity` is 0 (drifting) to 1 (full throttle) and
## drives both level and pitch, so the ship sounds like it is working. Called every
## frame: no allocation, no cue lookup beyond the first.
func set_engine_intensity(intensity: float) -> void:
	if _engine == null:
		return
	var value := clampf(intensity, 0.0, 1.0)
	if not _engine.playing:
		var data: AudioCueData = _index.get(_ENGINE_CUE)
		if data == null:
			return
		_engine.stream = data.stream
		_engine.bus = _resolve_bus(data.bus)
		_engine_base_db = data.volume_db
		_engine.play()
	_engine.volume_db = _engine_base_db + _ENGINE_IDLE_DB * (1.0 - value)
	_engine.pitch_scale = 1.0 - _ENGINE_PITCH_RANGE * 0.5 + _ENGINE_PITCH_RANGE * value

func stop_engine() -> void:
	if _engine != null:
		_engine.stop()

# --- Adaptive music (spec §18.2) ---------------------------------------------

func current_music_state() -> int:
	return _music_state

## Fade into a state's track. Idempotent: asking for the state already playing does
## nothing, so the level director can call this on every event without checking.
func set_music_state(state: int, immediate: bool = false) -> void:
	if state == _music_state:
		return
	var fade := 0.0 if immediate else MusicDirector.crossfade_seconds(_music_state, state)
	var from_state := _music_state
	_music_state = state

	var outgoing := _music_decks[_active_deck]
	var incoming := _music_decks[1 - _active_deck]
	_active_deck = 1 - _active_deck

	if _music_tween != null and _music_tween.is_valid():
		_music_tween.kill()

	var cue: StringName = MusicDirector.cue(state)
	if cue.is_empty():
		_fade_out(outgoing, fade)  # SILENT: nothing to bring in
		return
	var data: AudioCueData = _music_index.get(cue)
	if data == null:
		push_warning("[Audio] unknown music cue: %s" % cue)
		return

	incoming.stream = data.stream
	incoming.bus = _resolve_bus(data.bus)
	incoming.volume_db = _MUSIC_OFF_DB if fade > 0.0 else _MUSIC_ON_DB + data.volume_db
	incoming.play()

	if fade <= 0.0:
		outgoing.stop()
		return
	_music_tween = create_tween().set_parallel(true)
	_music_tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_music_tween.tween_property(incoming, "volume_db", _MUSIC_ON_DB + data.volume_db, fade)
	_music_tween.tween_property(outgoing, "volume_db", _MUSIC_OFF_DB, fade)
	# Only silence the old deck once it is actually inaudible.
	_music_tween.chain().tween_callback(outgoing.stop)
	print("[Audio] music %d -> %d (%.1fs)" % [from_state, state, fade])

func stop_music(fade: float = 1.5) -> void:
	if _music_tween != null and _music_tween.is_valid():
		_music_tween.kill()
	_music_state = MusicDirector.State.SILENT
	_fade_out(_music_decks[_active_deck], fade)

func _fade_out(deck: AudioStreamPlayer, fade: float) -> void:
	if not deck.playing:
		return
	if fade <= 0.0:
		deck.stop()
		return
	_music_tween = create_tween()
	_music_tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_music_tween.tween_property(deck, "volume_db", _MUSIC_OFF_DB, fade)
	_music_tween.tween_callback(deck.stop)

## Buses come from resources/audio/default_bus_layout.tres. If the layout failed to
## load, fall back to Master rather than dropping the sound entirely.
func _resolve_bus(bus: String) -> String:
	if AudioServer.get_bus_index(bus) < 0:
		push_warning("[Audio] missing bus '%s', falling back to %s" % [bus, _FALLBACK_BUS])
		return _FALLBACK_BUS
	return bus
