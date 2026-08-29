class_name LevelArc
extends Resource
## L'ORDRE des temps d'un niveau — la seule liste qui fasse foi.
##
## ⚠️ ELLE SE LIT D'UN SEUL TENANT, et c'est tout ce qu'on lui demande. Avant elle, l'arc du
## niveau 1 ne se lisait qu'en suivant six appels de fonction à travers 1 469 lignes, chacun
## déclenché par un événement différent. Personne ne pouvait dire « voici l'arc » sans lire le
## fichier entier.

@export var beats: Array[LevelBeat] = []

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if beats.is_empty():
		errors.append("aucun temps — un niveau sans arc ne commence jamais")
	var seen := {}
	for i in beats.size():
		var beat := beats[i]
		if beat == null:
			errors.append("beats[%d] est nul" % i)
			continue
		for error in beat.validate():
			errors.append("beats[%d] : %s" % [i, error])
		# ⚠️ DEUX TEMPS DE MÊME NOM, ET LE BRIEFING DE PAUSE DEVIENT FAUX pour l'un des deux :
		# `BriefingBook.find()` rend le premier, en silence.
		if beat.id != &"":
			if seen.has(beat.id):
				errors.append("beats[%d] : le nom `%s` est déjà pris par beats[%d]"
					% [i, beat.id, seen[beat.id]])
			seen[beat.id] = i
	return errors

func size() -> int:
	return beats.size()

func at(index: int) -> LevelBeat:
	return beats[index] if index >= 0 and index < beats.size() else null

## Le rang d'un temps, ou -1. ⚠️ ON CHERCHE PAR NOM, on ne compte pas : un rang dans une liste
## qu'on réordonne n'est pas une identité (`ADR-0034`).
func index_of(id: StringName) -> int:
	for i in beats.size():
		if beats[i] != null and beats[i].id == id:
			return i
	return -1
