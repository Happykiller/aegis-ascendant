class_name DialogueLine
extends Resource
## Une réplique de Lyra Vantella — la voix du jeu, incarnée (`ADR-0035`).
##
## ⚠️ CE N'EST PAS UNE CHAÎNE DE CARACTÈRES, ET C'EST DÉLIBÉRÉ. Une réplique porte son TON,
## et le ton pilote deux choses à l'écran : l'expression du portrait et la couleur de son
## cadre. Les écrire en dur dans le niveau, comme les bannières l'ont longtemps été, rendrait
## impossible de relire d'un coup d'œil ce que le jeu dit au joueur — et de le traduire.
##
## Paramètre de contenu, donc Resource typée avec son `validate()` : c'est la règle du projet
## (spec §31), et `scripts/lint-regles.sh` la fait respecter depuis le 2026-08-28.

## Le régime de la réplique. Il porte l'expression du portrait ET la couleur de son cadre —
## deux signaux, parce qu'à la taille où le portrait s'affiche en jeu, une expression seule ne
## se lit pas (`docs/KB/DAF/signaux.md`, loi n° 2).
enum Mood {
	## Accueil, information, progression. Cadre cyan, sourire.
	CALM,
	## Danger immédiat, point faible ouvert. Cadre rouge, urgence.
	ALERT,
}

## Le nom par lequel le jeu la demande. ⚠️ EN JEU ON NE COMPTE PAS, ON NOMME : les répliques
## de l'accueil s'enchaînent dans l'ordre, mais celles du combat se déclenchent sur des
## événements — un champ d'astéroïdes, une plongée. Les désigner par leur RANG dans le
## tableau, c'est le piège des missiles du Léviathan (`ADR-0034`) : un rang dans une liste
## qu'on réordonne n'est pas une identité. Vide pour une réplique jouée en séquence.
@export var key: StringName = &""

## Qui parle. Un seul personnage aujourd'hui ; le champ existe pour que le jour où un second
## prend la parole, il n'y ait pas à rouvrir chaque `.tres`.
@export var speaker: StringName = &"LYRA VANTELLA"
## Le rôle affiché sous le nom, dans la bulle.
@export var role: String = "NAVIGATRICE // IA GUIDE"
## Ce qu'elle dit. Les sauts de ligne sont RESPECTÉS : la maquette casse ses phrases à la main,
## et c'est ce qui donne son rythme à la lecture.
@export_multiline var text: String = ""
@export var mood: Mood = Mood.CALM

## La cue audio de sa voix, dans la banque. Vide tant que la voix n'est pas produite — la
## bulle et l'oscillogramme fonctionnent sans elle, et se brancheront dessus sans rien changer
## d'autre (`ADR-0035`, décision 5).
@export var voice_cue: StringName = &""

## Combien de temps la réplique tient à l'écran avant de céder la place, en secondes. Zéro =
## elle attend le joueur.
##
## ⚠️ ELLE NE REMPLACE PAS LA DURÉE DE LA VOIX. Quand `voice_cue` existe, c'est l'audio qui
## commande et cette valeur devient un plancher : une réplique ne doit jamais disparaître
## pendant qu'on l'entend encore.
@export var hold: float = 0.0

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if text.strip_edges().is_empty():
		errors.append("text est vide — une réplique muette n'est pas une réplique")
	if hold < 0.0:
		errors.append("hold (%.2f) doit être >= 0" % hold)
	if speaker == &"":
		errors.append("speaker est vide — la bulle a un nom à afficher")
	return errors

## Le régime, en couleur. Le cadre du portrait et le liseré de la bulle la lisent tous les
## deux : une seule source, donc ils ne peuvent pas diverger.
func mood_colour() -> Color:
	return Color("c93a31") if mood == Mood.ALERT else Color("3fd9e8")
