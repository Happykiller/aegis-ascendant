class_name CampaignBook
extends Resource
## L'ordre des niveaux. Une seule liste, et c'est elle qui fait foi.
##
## ⚠️ LE NIVEAU 1 Y ENTRE SANS CHANGER D'UN OCTET. C'est la recette de ce lot : rendre la
## campagne possible ne doit rien changer à ce qui se joue déjà.

@export var levels: Array[LevelData] = []

func size() -> int:
	return levels.size()

## Le niveau portant cette clé, ou `null`. ⚠️ Par NOM, jamais par rang.
func find(level_id: StringName) -> LevelData:
	for level in levels:
		if level != null and level.id == level_id:
			return level
	return null

func index_of(level_id: StringName) -> int:
	for i in levels.size():
		if levels[i] != null and levels[i].id == level_id:
			return i
	return -1

## Celui d'après, ou `null` si c'est le dernier — c'est ce qui décide entre CONTINUER et
## REJOUER sur le rapport de mission.
func after(level_id: StringName) -> LevelData:
	var i := index_of(level_id)
	if i < 0 or i + 1 >= levels.size():
		return null
	return levels[i + 1]

func first() -> LevelData:
	return levels[0] if not levels.is_empty() else null

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if levels.is_empty():
		errors.append("aucun niveau — une campagne vide ne se lance pas")
	var seen := {}
	for i in levels.size():
		var level := levels[i]
		if level == null:
			errors.append("levels[%d] est vide" % i)
			continue
		for error in level.validate():
			errors.append("levels[%d]: %s" % [i, error])
		if seen.has(level.id):
			errors.append("l'id `%s` apparaît deux fois — le jeu ne saurait plus lequel monter" % level.id)
		seen[level.id] = true
	return errors
