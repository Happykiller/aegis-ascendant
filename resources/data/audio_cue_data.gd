class_name AudioCueData
extends Resource
## A single playable sound cue (spec §22.1). Units: decibels, seconds, pitch ratio.

## Lookup key used by AudioManager.play().
@export var id: StringName = &""
@export var stream: AudioStream
## Target bus; must exist in resources/audio/default_bus_layout.tres.
@export_enum("SFX", "Music", "Voice") var bus: String = "SFX"
## Base level. Per-call offsets are added on top of this.
@export_range(-40.0, 12.0) var volume_db: float = 0.0
## Random pitch range, to keep repeated cues from sounding machine-gunned.
@export_range(0.5, 2.0) var pitch_min: float = 1.0
@export_range(0.5, 2.0) var pitch_max: float = 1.0
## Minimum delay between two triggers of this cue; 0 = no limit (spec §9.2:
## the fire cadence must not spam the mix).
@export_range(0.0, 2.0) var min_interval: float = 0.0
## Loop the stream instead of playing it once (engine hum, music beds).
@export var looping: bool = false

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if id.is_empty():
		errors.append("id must not be empty")
	if stream == null:
		errors.append("stream must not be null")
	if pitch_min <= 0.0:
		errors.append("pitch_min must be > 0")
	if pitch_max < pitch_min:
		errors.append("pitch_max must be >= pitch_min")
	if min_interval < 0.0:
		errors.append("min_interval must be >= 0")
	return errors
