extends "res://tests/test_case.gd"
## La couverture de bouclier — ce qu'une unité protégée par un porteur encaisse.
##
## La PROJECTION de l'aura demande un arbre de scène (le porteur interroge le
## groupe `enemies`), donc elle se vérifie au banc d'essai, en headless, comme le
## frein de la sangsue. Ce qui se teste ici est le contrat de la couverture
## elle-même : c'est lui qui décide si un coup compte.

const ControllerScript := preload("res://scripts/enemies/enemy_controller.gd")

func _unit() -> EnemyController:
	# Hors de l'arbre : `_ready()` ne tourne pas, mais le compte à rebours de
	# couverture ne dépend d'aucun enfant. C'est ce qui le rend vérifiable.
	return track(ControllerScript.new()) as EnemyController

func test_a_unit_starts_uncovered() -> void:
	assert_false(_unit().is_covered(), "sans porteur, rien ne protège")

func test_a_carrier_covers_it() -> void:
	var unit := _unit()
	unit.cover(EnemyController.AURA_GRACE)
	assert_true(unit.is_covered(), "couverte")

## ⚠️ `maxf` ET NON UNE AFFECTATION. Deux porteurs dont les bulles se recouvrent ne
## doivent pas se voler la couverture : celui qui passe en second écraserait celle
## du premier avec une valeur plus courte, et l'unité clignoterait entre protégée et
## vulnérable selon l'ordre d'exécution — invisible, et différent à chaque partie.
func test_two_overlapping_carriers_never_shorten_each_other() -> void:
	var unit := _unit()
	unit.cover(0.5)
	unit.cover(0.1)
	unit.tick_cover(0.2) # plus que la courte, moins que la longue
	assert_true(unit.is_covered(), "la couverture la plus généreuse a survécu")

## La couverture est un COMPTE À REBOURS, pas un drapeau : elle s'éteint d'elle-même
## quand le porteur cesse de la reposer. C'est ce qui dispense de nettoyer quoi que
## ce soit à la mort du porteur — et de se demander qui, de lui ou de sa victime,
## meurt en premier.
func test_the_cover_expires_on_its_own() -> void:
	var unit := _unit()
	unit.cover(EnemyController.AURA_GRACE)
	# Une image plus longue que la grâce suffit à la vider.
	unit.tick_cover(EnemyController.AURA_GRACE + 0.01)
	assert_false(unit.is_covered(), "sans porteur pour la reposer, elle tombe")

## Et elle NE tombe pas tant que le porteur la repose : sinon l'escadron protégé
## clignoterait au rythme des images.
func test_the_cover_holds_while_the_carrier_keeps_renewing_it() -> void:
	var unit := _unit()
	for i in 60:
		unit.cover(EnemyController.AURA_GRACE)
		unit.tick_cover(1.0 / 60.0)
		assert_true(unit.is_covered(), "toujours couverte à l'image %d" % i)

## La grâce doit survivre à une image longue : sinon un pic de charge ferait
## clignoter tout un escadron protégé, une image sur deux.
func test_the_grace_outlasts_a_slow_frame() -> void:
	assert_true(EnemyController.AURA_GRACE > 1.0 / 30.0,
		"la couverture tient plus qu'une image à 30 Hz (%f s)" % EnemyController.AURA_GRACE)
