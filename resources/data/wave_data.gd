class_name WaveData
extends Resource
## Data-driven wave timeline (spec §11.3) — the seed of the future
## EncounterDirector: waves are described by data, never by scattered timers.

@export var entries: Array[WaveEntry] = []

## Silence d'ouverture, en secondes, AVANT le premier spawn de la vague.
##
## Ce n'est pas un décalage technique : c'est l'espace où le joueur apprend à se déplacer
## avant qu'on lui tire dessus (spec §5.2, « prise en main calme » — premier point de la
## courbe d'intensité).
##
## ⚠️ Il vit ICI et non dans les `time_offset` des entrées, pour deux raisons. D'abord
## parce que le décaler reviendrait à retoucher une trentaine de valeurs, et que le
## prochain diff de la vague en deviendrait illisible. Ensuite parce que l'ordre relatif
## des entrées est du design déjà réglé : il ne doit pas bouger quand on change la durée
## du silence.
@export var lead_in: float = 0.0

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if entries.is_empty():
		errors.append("wave has no entries")
	if lead_in < 0.0:
		errors.append("lead_in must be >= 0")
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
