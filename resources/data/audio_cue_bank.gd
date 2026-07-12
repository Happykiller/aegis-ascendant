class_name AudioCueBank
extends Resource
## An indexed collection of AudioCueData (spec §22.1). AudioManager loads one bank
## for SFX and one for music, so no cue path is ever hard-coded in gameplay code.

@export var cues: Array[AudioCueData] = []

## StringName -> AudioCueData. Built once at startup; never called per frame.
func build_index() -> Dictionary:
	var index := {}
	for cue in cues:
		if cue != null and not cue.id.is_empty():
			index[cue.id] = cue
	return index

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	var seen := {}
	for cue in cues:
		if cue == null:
			errors.append("bank contains a null cue")
			continue
		for error in cue.validate():
			errors.append("%s: %s" % [cue.id, error])
		if seen.has(cue.id):
			errors.append("%s: duplicate id" % cue.id)
		seen[cue.id] = true
	return errors
