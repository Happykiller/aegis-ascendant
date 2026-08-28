class_name SectorBriefing
extends Resource
## Ce que le joueur relit quand il met le jeu en pause : où il est, et ce qu'il a à y faire.
##
## ⚠️ ELLE EXISTE PARCE QUE LE JEU NE LE DISAIT NULLE PART. Les bannières annoncent une phase
## pendant 1,6 seconde, au moment précis où le joueur regarde ailleurs — il esquive. Après
## quoi rien, à aucun moment, ne rappelle l'objectif. La maquette de briefing l'a nommé avant
## nous : « OBJECTIFS DE MISSION », en toutes lettres, à côté du jeu figé.
##
## Le contenu vit dans une Resource et non dans l'écran de pause, pour la même raison que les
## répliques de Lyra : c'est du contenu, donc c'est de la donnée — traduisible, relisible d'un
## coup d'œil, et modifiable sans toucher à une interface.

## La phase du niveau que ce briefing décrit. ⚠️ C'est le NOM de la valeur d'énumération
## (`Graybox.Phase`), pas son rang : un rang change à la première phase insérée au milieu.
@export var phase: StringName = &""

## Le sur-titre : « NOUVEAU SECTEUR », « COMBAT EN COURS »… Il situe, le titre nomme.
@export var kicker: String = "SECTEUR"
@export var title: String = ""
## Deux ou trois phrases. Elles décrivent le LIEU et sa menace, pas la manœuvre — la manœuvre
## est dans les objectifs, et mélanger les deux fait une bouillie qu'on ne relit pas.
@export_multiline var description: String = ""

## Ce que le joueur a à faire, une ligne par objectif. ⚠️ TROIS AU PLUS : au-delà, ce n'est
## plus une consigne qu'on relit en pause, c'est une liste qu'on parcourt — et le joueur qui
## a mis en pause veut se souvenir, pas étudier.
@export var objectives: PackedStringArray = PackedStringArray()

const MAX_OBJECTIVES := 3

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if phase == &"":
		errors.append("phase est vide — un briefing décrit une phase précise")
	if title.strip_edges().is_empty():
		errors.append("title est vide — le joueur doit savoir où il est")
	if objectives.is_empty():
		errors.append("aucun objectif — un briefing sans consigne ne sert à rien")
	elif objectives.size() > MAX_OBJECTIVES:
		errors.append("%d objectifs pour %d au plus — au-delà on ne relit plus, on étudie"
			% [objectives.size(), MAX_OBJECTIVES])
	for i in objectives.size():
		if String(objectives[i]).strip_edges().is_empty():
			errors.append("objectives[%d] est vide" % i)
	return errors
