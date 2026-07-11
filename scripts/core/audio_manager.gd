extends Node
## Sound effects (autoload "AudioManager"). Preloads the prototype SFX and plays
## them through a small round-robin pool of AudioStreamPlayers (spec §18.3, §18.5).
## Non-positional (shmup): every cue plays at a consistent level.

const _POOL_SIZE := 12
const _SFX_DIR := "res://assets/imported/audio/sfx/"

const _CUES: Dictionary = {
	"player_pulse": preload(_SFX_DIR + "player_pulse.wav"),
	"enemy_pulse": preload(_SFX_DIR + "enemy_pulse.wav"),
	"hull_impact": preload(_SFX_DIR + "hull_impact.wav"),
	"shield_impact": preload(_SFX_DIR + "shield_impact.wav"),
	"small_explosion": preload(_SFX_DIR + "small_explosion.wav"),
	"pickup_collect": preload(_SFX_DIR + "pickup_collect.wav"),
	"danger_alarm": preload(_SFX_DIR + "danger_alarm.wav"),
	"docking_lock": preload(_SFX_DIR + "docking_lock.wav"),
	"rail_battery": preload(_SFX_DIR + "rail_battery.wav"),
	"helios_lance": preload(_SFX_DIR + "helios_lance.wav"),
}

var _players: Array[AudioStreamPlayer] = []
var _next: int = 0

func _ready() -> void:
	for i in _POOL_SIZE:
		var p := AudioStreamPlayer.new()
		p.bus = "Master"
		add_child(p)
		_players.append(p)

func play(cue: String, volume_db: float = 0.0) -> void:
	var stream: AudioStream = _CUES.get(cue)
	if stream == null:
		return
	var p := _players[_next]
	_next = (_next + 1) % _POOL_SIZE
	p.stream = stream
	p.volume_db = volume_db
	p.play()
