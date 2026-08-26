extends "res://tests/test_case.gd"
## `FlowLink` — le lien fait de points qui défilent.
##
## ⚠️ CE FICHIER GARDE UN INVARIANT MINUSCULE ET DÉCISIF. Le chapelet se répète le long du
## lien : son nombre de points vient de la longueur. Sans plancher, un lien court tombe à
## ZÉRO répétition — donc à un point étiré sur rien, donc invisible. Un lien qui disparaît
## quand il devrait seulement raccourcir ne désigne plus rien, et c'est exactement ce que
## deux corrections successives ont déjà coûté sur ce même lien (orientation vue par la
## tranche, puis largeur sous le pixel).

const Link := preload("res://scripts/fx/flow_link.gd")

func test_a_short_link_never_falls_to_zero_dots() -> void:
	for span in [0.0, 0.1, 0.5, 1.0]:
		assert_true(Link.dot_count(span) >= 1.0,
			"un lien de %.1f garde au moins un point" % span)

func test_a_long_link_carries_more_dots() -> void:
	assert_true(Link.dot_count(12.0) > Link.dot_count(4.0),
		"le chapelet s'allonge avec la portée")
	assert_almost_eq(Link.dot_count(10.0), 10.0 * Link.DOTS_PER_UNIT, 0.001,
		"et il suit la densité annoncée")

## ⚠️ LE SENS DU DÉFILEMENT EST LA MÉCANIQUE, pas un détail. L'opérateur a lu un trait plein
## comme « on me ralentit » alors que le porteur PROTÈGE les siens : un signe qui enseigne
## une règle fausse est pire qu'un signe absent. La vitesse est négative parce que le
## décalage d'UV fait remonter la texture — l'inverser dirait le contraire.
func test_the_flow_runs_in_the_declared_direction() -> void:
	assert_true(Link.FLOW_SPEED < 0.0,
		"le défilement remonte vers la cible passée en second")
