class_name SettingsData
extends RefCounted
## Player settings, as pure data (spec §13, §19.2). Volumes are linear 0..1 — that is what
## a slider is — and only become decibels at the AudioServer boundary.
## No node, no file, no AudioServer: instantiable and testable by hand.

## Bus name -> linear volume. Keys match resources/audio/default_bus_layout.tres.
const BUSES: Array[StringName] = [&"Master", &"Music", &"SFX", &"Voice"]
const DEFAULTS: Dictionary = {
	&"Master": 0.8,
	&"Music": 0.7,
	&"SFX": 0.9,
	&"Voice": 1.0,
}

## Below this, the slider means "off" and we mute outright rather than fade to a
## barely-audible -60 dB.
const SILENCE_THRESHOLD := 0.001
const SILENCE_DB := -80.0

var volumes: Dictionary = DEFAULTS.duplicate()

func get_linear(bus: StringName) -> float:
	return volumes.get(bus, DEFAULTS.get(bus, 1.0))

func set_linear(bus: StringName, value: float) -> void:
	if not DEFAULTS.has(bus):
		push_warning("[Settings] unknown bus: %s" % bus)
		return
	volumes[bus] = clampf(value, 0.0, 1.0)

func to_dict() -> Dictionary:
	return volumes.duplicate()

## Tolerant on purpose: a settings file from an older build, or one a player has edited by
## hand, must not brick the game. Unknown keys are dropped, bad values clamped.
func from_dict(source: Dictionary) -> void:
	volumes = DEFAULTS.duplicate()
	for bus in BUSES:
		var value: Variant = source.get(bus, source.get(String(bus)))
		if value is float or value is int:
			volumes[bus] = clampf(float(value), 0.0, 1.0)

## A slider is linear in loudness-ish terms; the mixer wants decibels.
static func to_db(linear: float) -> float:
	if linear <= SILENCE_THRESHOLD:
		return SILENCE_DB
	return linear_to_db(clampf(linear, 0.0, 1.0))
