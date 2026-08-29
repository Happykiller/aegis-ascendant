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

# ==========================================================================
# L'épilogue — ce que le rapport de mission dit de CE niveau
# ==========================================================================
#
# ⚠️ IL EST ICI PARCE QU'IL ETAIT EN DUR DANS L'ÉCRAN, ET DONC FAUX AU DEUXIÈME NIVEAU. Le
# rapport annonçait « PALE LEVIATHAN DETRUIT · COULOIR REOUVERT » et un relais « REMIS A
# L'HEURE » — le dénouement du niveau 1, écrit quand il n'y en avait qu'un. Au terme du survol
# du Long Cortège, qui ne détruit rien et ne rouvre aucun couloir, ces deux lignes auraient
# raconté une autre mission que celle qu'on vient de jouer.
#
# ⚠️ ET LE RELEVÉ N'EST PAS UN DÉCOR : c'est la seule chose de cet écran qui n'explique rien et
# dit tout. Au niveau 1 c'est l'horloge du relais 07, en avance de 40 ms, remise à l'heure ou
# radiée. Au niveau 2 c'est Ambry. Chaque niveau apporte donc SON relevé, son intitulé compris.

## L'intitulé de la ligne de relevé : « RELAIS 07 », « AMBRY »…
@export var report_readout_label: String = "RELAIS 07"
## Sa valeur, selon l'issue.
@export var report_readout_victory: String = ""
@export var report_readout_defeat: String = ""
## La ligne sous le titre : ce que la mission a changé.
@export var report_tagline_victory: String = ""
@export var report_tagline_defeat: String = ""

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if id == &"":
		errors.append("id est vide — le jeu désigne un niveau par son nom, jamais par son rang")
	if display_name.strip_edges().is_empty():
		errors.append("display_name est vide — le rapport de mission a un titre à afficher")
	if scene == null:
		errors.append("scene est vide — un niveau sans scène ne se monte pas")
	# ⚠️ LES QUATRE LIGNES DU RAPPORT SONT OBLIGATOIRES, et c'est délibérément strict. Vides,
	# elles ne laisseraient pas un écran incomplet : elles laisseraient l'ÉPILOGUE DU NIVEAU 1
	# s'afficher au bout d'un autre niveau, ce qui est pire qu'un blanc — le joueur lirait un
	# dénouement qu'il n'a pas vécu, et rien à l'écran ne le contredirait.
	for pair in [["report_readout_label", report_readout_label],
			["report_readout_victory", report_readout_victory],
			["report_readout_defeat", report_readout_defeat],
			["report_tagline_victory", report_tagline_victory],
			["report_tagline_defeat", report_tagline_defeat]]:
		if String(pair[1]).strip_edges().is_empty():
			errors.append("%s est vide — sans lui, le rapport afficherait l'épilogue d'un AUTRE niveau" % pair[0])
	return errors
