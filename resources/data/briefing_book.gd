class_name BriefingBook
extends Resource
## Tous les briefings du niveau, cherchés par NOM de phase.
##
## ⚠️ PAR NOM, JAMAIS PAR RANG — même règle que les répliques de Lyra, et pour la même raison
## déjà payée sur les missiles du Léviathan (`ADR-0034`) : un rang dans une liste qu'on
## réordonne n'est pas une identité. Insérer une phase au milieu de l'énumération suffirait à
## afficher le mauvais briefing, en silence.

@export var briefings: Array[SectorBriefing] = []

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if briefings.is_empty():
		errors.append("aucun briefing")
	var seen := {}
	for i in briefings.size():
		var entry := briefings[i]
		if entry == null:
			errors.append("briefings[%d] est nul" % i)
			continue
		for error in entry.validate():
			errors.append("briefings[%d] : %s" % [i, error])
		if entry.phase != &"":
			if seen.has(entry.phase):
				errors.append("briefings[%d] : la phase `%s` est déjà décrite par briefings[%d]"
					% [i, entry.phase, seen[entry.phase]])
			seen[entry.phase] = i
	return errors

## Le briefing de cette phase, ou `null`. Muet plutôt que fautif : une phase sans briefing est
## une phase sans briefing, pas une erreur — l'écran de pause s'en passe.
func find(phase: StringName) -> SectorBriefing:
	for entry in briefings:
		if entry != null and entry.phase == phase:
			return entry
	return null
