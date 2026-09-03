extends "res://tests/test_case.gd"
## Le rapport de mission — l'ecran qui dit au joueur comment sa partie s'est terminee.
##
## ⚠️ POURQUOI CE TEST EXISTE, ET POURQUOI IL ARRIVE SI TARD. Cet ecran decide du
## denouement des DEUX niveaux, porte trois embranchements (REJOUER / CONTINUER /
## REESSAYER) et manipule `Campaign`, `SceneRouter` et `GameState` — et il n'avait pas
## une seule assertion. L'audit du backlog du 2026-09-03 l'a trouve en cherchant tout
## autre chose : le backlog le declarait ABSENT alors qu'il etait livre depuis six
## semaines. Un ecran qu'on croit inexistant n'est teste par personne.
##
## CE QUE CES TESTS GARDENT, ET QUI NE SE VOIT PAS AUTREMENT —
##
##   1. UN ACCENT. La police d'interface (Press Start 2P) n'en porte aucun : un « É »
##      rend un carre vide. Le fichier le dit en commentaire depuis le premier jour,
##      et un commentaire n'a jamais arrete personne. Le defaut ne se verrait qu'en
##      PERDANT une partie, et seulement sur la ligne fautive ;
##   2. LE RAPPEL DE TOUCHES QUI NOMME UNE AUTRE ACTION QUE SON BOUTON. Deja survenu :
##      « REJOUER » s'affichait sous un bouton « REESSAYER » — deux mots pour une
##      touche, sur l'ecran dont c'est la seule instruction ;
##   3. UNE TABLE QUI OUBLIE UNE ISSUE. Six dictionnaires sont indexes par `Outcome` ;
##      une entree manquante leve a l'execution, au pire moment — la fin de partie ;
##   4. UN SEUIL DE RANG DEPLACE. `_rank()` est la seule logique de cet ecran, et elle
##      n'a aucun garde-fou : ses quatre paliers se relisent ici, aux BORNES.
##
## ⚠️ CE QUI EST INSTANCIABLE ICI, ET CE QUI NE L'EST PAS. Le runner tourne en mode
## `--script` : pas d'autoloads. `_ready()` resout `/root/GameState`, `/root/SceneRouter`
## et `/root/AudioManager` — il est donc HORS d'atteinte, et la scene n'est jamais ajoutee
## a l'arbre. Mais `setup()` est ecrit pour tourner entre `instantiate()` et `add_child()` :
## il n'adresse QUE des nœuds `%`, resolus des l'instanciation. C'est exactement ce que ces
## tests exploitent — ils habillent l'ecran pour de vrai, et relisent ce qui s'affiche.

const ReportScript := preload("res://scripts/ui/mission_report.gd")
const REPORT_SCENE := "res://scenes/ui/mission_report.tscn"

## Les lettres que Press Start 2P ne sait pas dessiner. Le point median « · », lui, est
## utilise partout dans cet ecran et n'est pas en cause.
const ACCENTED := "ÀÁÂÄÃÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÖÕÙÚÛÜÝàáâäãåæçèéêëìíîïñòóôöõùúûüýÿŒœ"

func _tables() -> Array:
	return [
		["_TITLE", ReportScript._TITLE],
		["_TAGLINE", ReportScript._TAGLINE],
		["_RELAY", ReportScript._RELAY],
		["_REPLAY_LABEL", ReportScript._REPLAY_LABEL],
		["_CHANNEL", ReportScript._CHANNEL],
		["_CONTROLS", ReportScript._CONTROLS],
	]

## L'ecran habille pour une issue, hors arbre. `setup()` ne touche aucun autoload.
func _dressed(score: int, outcome: int) -> CanvasLayer:
	var packed: PackedScene = load(REPORT_SCENE)
	assert_true(packed != null, "la scene du rapport se charge")
	var report := track(packed.instantiate()) as CanvasLayer
	report.setup(score, outcome)
	return report

func _label(report: CanvasLayer, unique_name: String) -> Label:
	return report.get_node("%" + unique_name) as Label


# =============================================================================
# 1. Les tables couvrent les deux issues, et rien de ce qu'elles portent n'est illisible
# =============================================================================

## ⚠️ UNE ENTREE MANQUANTE LEVERAIT A LA FIN DE LA PARTIE, jamais avant : `setup()` indexe
## les six tables par l'issue, et l'issue qui manque est par construction celle qu'on teste
## le moins — la defaite.
func test_every_outcome_table_covers_both_outcomes() -> void:
	for entry in _tables():
		var name := String(entry[0])
		var table: Dictionary = entry[1]
		assert_true(table.has(ReportScript.Outcome.VICTORY),
			"%s porte une entree pour la VICTOIRE" % name)
		assert_true(table.has(ReportScript.Outcome.DEFEAT),
			"%s porte une entree pour la DEFAITE" % name)
		assert_eq(table.size(), 2,
			"%s ne porte que les deux issues (une entree de plus est une issue muette)" % name)

## ⚠️ LE COMMENTAIRE NE SUFFISAIT PAS. `mission_report.gd` porte « SANS ACCENTS » en tete
## de ces tables depuis le premier jour ; rien ne l'a jamais verifie. Un « É » rend un carre
## vide dans Press Start 2P, et cela ne se voit qu'a l'ecran, sur la seule ligne fautive.
func test_no_screen_text_carries_an_accent() -> void:
	var texts: Array[String] = [ReportScript._CONTINUE_LABEL]
	for entry in _tables():
		for key in (entry[1] as Dictionary):
			texts.append(String((entry[1] as Dictionary)[key]))
	for text in texts:
		for i in text.length():
			var glyph := text[i]
			assert_false(ACCENTED.contains(glyph),
				"« %s » porte « %s » : Press Start 2P n'a pas cette lettre, elle rendrait un carre vide"
					% [text, glyph])

## ⚠️ DEJA SURVENU UNE FOIS. Le rappel de touches etait FIXE : il annoncait « REJOUER » sous
## un bouton « REESSAYER ». Deux mots pour une touche, sur l'ecran dont c'est la seule
## instruction — et le seul moment ou le joueur cherche quoi faire.
func test_the_controls_hint_names_the_same_action_as_its_button() -> void:
	for outcome in [ReportScript.Outcome.VICTORY, ReportScript.Outcome.DEFEAT]:
		var button := String(ReportScript._REPLAY_LABEL[outcome])
		var hint := String(ReportScript._CONTROLS[outcome])
		assert_true(hint.contains(button),
			"le rappel « %s » doit nommer le bouton « %s »" % [hint, button])
		assert_true(hint.contains("TITRE"),
			"le rappel « %s » doit aussi nommer la sortie vers le titre" % hint)

## Les deux issues ne se ressemblent pas : c'est tout ce que cet ecran a pour dire au
## joueur ce qui vient de se passer.
func test_the_two_outcomes_never_share_a_wording() -> void:
	for entry in _tables():
		var table: Dictionary = entry[1]
		assert_true(table[ReportScript.Outcome.VICTORY] != table[ReportScript.Outcome.DEFEAT],
			"%s dit deux choses differentes selon l'issue" % String(entry[0]))


# =============================================================================
# 2. Le rang — la seule logique de cet ecran, et elle n'avait aucun garde-fou
# =============================================================================

## ⚠️ TESTE AUX BORNES, ET NON AU MILIEU DES PALIERS. Un seuil deplace d'une unite passe
## toutes les valeurs rondes et ne se voit que sur le score qui tombe pile dessus.
func test_the_rank_thresholds_hold_at_their_boundaries() -> void:
	var cases := [
		[40000, "S"], [39999, "A"],
		[25000, "A"], [24999, "B"],
		[12000, "B"], [11999, "C"],
		[0, "C"],
	]
	for case in cases:
		assert_eq(ReportScript._rank(int(case[0])), String(case[1]),
			"un score de %d vaut le rang %s" % [int(case[0]), String(case[1])])

## ⚠️ LE RANG NOTE LE SCORE, PAS L'ISSUE, et c'est une decision : une defaite tardive vaut
## mieux qu'une defaite immediate, et le rapport doit le dire plutot qu'un tiret punitif.
func test_the_rank_reads_the_score_and_not_the_outcome() -> void:
	var won := _dressed(41000, ReportScript.Outcome.VICTORY)
	var lost := _dressed(41000, ReportScript.Outcome.DEFEAT)
	assert_eq(_label(lost, "RankValue").text, _label(won, "RankValue").text,
		"le meme score donne le meme rang, gagne ou perdu")
	assert_eq(_label(lost, "RankValue").text, "S", "et c'est bien le rang du score")


# =============================================================================
# 3. L'ecran habille — ce que le joueur lit vraiment
# =============================================================================

## ⚠️ C'EST LE CHEMIN QUE PERSONNE NE JOUE. On gagne pour verifier, on perd par accident :
## la defaite est l'issue la moins vue du developpement, et celle que le backlog a crue
## inexistante pendant six semaines.
func test_a_defeat_dresses_the_whole_screen() -> void:
	var report := _dressed(7777, ReportScript.Outcome.DEFEAT)
	assert_eq(_label(report, "Title").text, "DEFAITE", "le titre annonce la defaite")
	assert_eq(_label(report, "Tagline").text, ReportScript._TAGLINE[ReportScript.Outcome.DEFEAT],
		"la ligne de contexte est celle de la defaite")
	assert_eq(_label(report, "RelayValue").text, ReportScript._RELAY[ReportScript.Outcome.DEFEAT],
		"le releve porte l'etat de la defaite")
	assert_eq(_label(report, "CommsText").text, "SIGNAL PERDU", "le canal est perdu")
	assert_eq((report.get_node("%ReplayButton") as Button).text, "REESSAYER",
		"le bouton propose de reessayer")
	assert_eq(_label(report, "Controls").text, ReportScript._CONTROLS[ReportScript.Outcome.DEFEAT],
		"et le rappel de touches suit l'issue")

func test_a_victory_dresses_the_whole_screen() -> void:
	var report := _dressed(7777, ReportScript.Outcome.VICTORY)
	assert_eq(_label(report, "Title").text, "VICTOIRE", "le titre annonce la victoire")
	assert_eq(_label(report, "CommsText").text, "CANAL DEGAGE", "le canal est degage")
	assert_eq((report.get_node("%ReplayButton") as Button).text, "REJOUER",
		"le bouton propose de rejouer")

## ⚠️ LES DEUX ISSUES NE SE DISTINGUENT PAS QUE PAR LES MOTS. L'or est reserve au
## commandement et aux faits d'exception (DA §5.1) ; la defaite prend le rouge d'alerte.
## Une couleur oubliee laisserait un titre « DEFAITE » en or, ce qu'aucun test de texte
## ne verrait.
func test_the_defeat_never_wears_the_colour_of_the_victory() -> void:
	var won := _dressed(100, ReportScript.Outcome.VICTORY)
	var lost := _dressed(100, ReportScript.Outcome.DEFEAT)
	assert_eq(_label(won, "Title").get_theme_color("font_color"), ReportScript.VICTORY_GOLD,
		"la victoire porte l'or")
	assert_eq(_label(lost, "Title").get_theme_color("font_color"), ReportScript.DEFEAT_RED,
		"la defaite porte le rouge")
	assert_eq((lost.get_node("%Pip") as ColorRect).color, ReportScript.CHANNEL_LOST,
		"et la pastille du canal suit l'issue, pas seulement le texte")

## ⚠️ HUIT CHIFFRES, TOUJOURS. Le score est cadre par `%08d` : un format relache ferait
## danser le bloc d'un ecran a l'autre, sur le seul nombre que le joueur compare.
func test_the_score_is_always_padded_to_eight_digits() -> void:
	for score in [0, 7, 77130, 99999999]:
		var report := _dressed(score, ReportScript.Outcome.VICTORY)
		var shown := _label(report, "ScoreValue").text
		assert_eq(shown.length(), 8, "un score de %d s'affiche sur huit chiffres (%s)" % [score, shown])
		assert_eq(shown, "%08d" % score, "et il vaut bien le score")
