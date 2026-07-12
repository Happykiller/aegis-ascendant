class_name SfxThrottle
extends RefCounted
## Rate-limits a cue so a fast trigger (player fire, bullet impacts) cannot flood
## the mix (spec §9.2). The clock is injected rather than read from the engine, so
## the logic is testable headless.

var _last_played: Dictionary = {}

## True when `id` may play at `now_s`; records the trigger as a side effect.
## `min_interval` <= 0 always allows the cue.
func should_play(id: StringName, min_interval: float, now_s: float) -> bool:
	if min_interval <= 0.0:
		return true
	var last: float = _last_played.get(id, -INF)
	if now_s - last < min_interval:
		return false
	_last_played[id] = now_s
	return true

func reset() -> void:
	_last_played.clear()
