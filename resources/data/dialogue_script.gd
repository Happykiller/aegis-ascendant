class_name DialogueScript
extends Resource
## Une suite de répliques, jouée dans l'ordre — l'accueil, l'entrée dans un secteur, la
## plongée. C'est l'unité que le jeu monte : un écran ne connaît jamais une réplique isolée.
##
## ⚠️ LA PAGINATION EST UNE PROPRIÉTÉ DU SCRIPT, PAS DE L'AFFICHAGE. La maquette de l'accueil
## écrit « Message 1/4 » : ce compte vient d'ici. Le laisser calculer par l'interface, c'est
## le voir diverger le jour où une réplique est ajoutée sans que la pastille suive.

@export var id: StringName = &""
@export var lines: Array[DialogueLine] = []

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if id == &"":
		errors.append("id est vide — un script se désigne")
	if lines.is_empty():
		errors.append("aucune réplique — un script vide ne se joue pas")
	var seen := {}
	for i in lines.size():
		var line := lines[i]
		if line == null:
			errors.append("lines[%d] est nul" % i)
			continue
		for error in line.validate():
			errors.append("lines[%d] : %s" % [i, error])
		# ⚠️ DEUX RÉPLIQUES DU MÊME NOM, ET `find()` EN RENDRAIT UNE AU HASARD — celle qui
		# vient en premier. Le jeu jouerait la mauvaise sans que rien ne le dise.
		if line.key != &"":
			if seen.has(line.key):
				errors.append("lines[%d] : la clé `%s` sert déjà à lines[%d]"
					% [i, line.key, seen[line.key]])
			seen[line.key] = i
	return errors

## La réplique nommée `key`, ou `null`. C'est par là que le JEU demande — jamais par un rang.
func find(key: StringName) -> DialogueLine:
	for line in lines:
		if line != null and line.key == key:
			return line
	return null

func size() -> int:
	return lines.size()

## La réplique `index`, ou `null` hors bornes. Rendre `null` plutôt que planter : ce chemin
## est piloté par l'entrée du joueur, qui peut avancer plus vite que l'état.
func line_at(index: int) -> DialogueLine:
	return lines[index] if index >= 0 and index < lines.size() else null

## Ce que la bulle affiche : « Message 2/4 ». Une seule source pour le compte et pour son
## rendu.
func page_label(index: int) -> String:
	return "MESSAGE %d/%d" % [clampi(index + 1, 1, maxi(lines.size(), 1)), lines.size()]
