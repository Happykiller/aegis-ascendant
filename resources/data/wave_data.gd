class_name WaveData
extends Resource
## Data-driven wave timeline (spec §11.3) — the seed of the future
## EncounterDirector: waves are described by data, never by scattered timers.

@export var entries: Array[WaveEntry] = []

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if entries.is_empty():
		errors.append("wave has no entries")
	for i in entries.size():
		if entries[i] == null:
			errors.append("entry %d is null" % i)
		else:
			errors.append_array(entries[i].validate())
	return errors

func total_enemy_count() -> int:
	var total := 0
	for entry in entries:
		total += entry.count
	return total
