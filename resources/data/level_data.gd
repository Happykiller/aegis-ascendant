class_name LevelData
extends Resource
## Un niveau de la campagne : ce qu'on monte, ce qu'on annonce, ce que Lyra y dit.
##
## ⚠️ ELLE EXISTE PARCE QUE LE JEU NE SAVAIT PAS CE QU'ÉTAIT UN NIVEAU. Jusqu'ici, la scène de
## jeu était codée en dur dans l'écran-titre, `GameState` n'avait qu'un état de combat, et
## REJOUER faisait `reload_current_scene()` : on savait recommencer, jamais continuer. Le
## deuxième niveau (`docs/plans/2026-08-29-niveau-2-execution.md`) rend ce trou bloquant.
##
## Paramètre de contenu, donc Resource typée avec son `validate()` — c'est la règle du projet
## (spec §31), et `scripts/lint-regles.sh` la fait respecter.

## Le nom par lequel le reste du jeu le demande. ⚠️ ON NOMME, ON NE COMPTE PAS : un rang dans
## une liste qu'on réordonne n'est pas une identité (la leçon des missiles du Léviathan,
## `ADR-0034`, et celle des répliques de Lyra).
@export var id: StringName = &""

## Ce que le joueur lit — sur le rapport de mission, et un jour sur un écran de sélection.
@export var display_name: String = ""

## La scène à monter. ⚠️ PackedScene et non un chemin : un chemin qui ne résout plus se
## découvre au lancement, une référence cassée se découvre à l'import.
@export var scene: PackedScene

## Les briefings de pause de ce niveau, et ce que Lyra y dit. Vides tant qu'ils ne sont pas
## écrits : un niveau sans dialogue se joue, il est seulement muet.
@export var briefings: Resource
@export var dialogue: Resource

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if id == &"":
		errors.append("id est vide — le jeu désigne un niveau par son nom, jamais par son rang")
	if display_name.strip_edges().is_empty():
		errors.append("display_name est vide — le rapport de mission a un titre à afficher")
	if scene == null:
		errors.append("scene est vide — un niveau sans scène ne se monte pas")
	return errors
