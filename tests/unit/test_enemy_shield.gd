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

# --- Le champ RENDU VISIBLE --------------------------------------------------
#
# ⚠️ POURQUOI CES TESTS EXISTENT. La mécanique du porteur a vécu deux jours en étant
# complète et injouable : les voisins étaient bien couverts, mais la PORTÉE ne se voyait
# nulle part. Le joueur constatait que ses tirs ne portaient pas sans pouvoir savoir où
# la bulle s'arrêtait — il subissait au lieu de jouer contre.
# `BRIEF-0046` avait mis le dôme hors du périmètre de la forge pour cette raison exacte :
# « il doit montrer la portée RÉELLE, qui est une valeur de gameplay et non une dimension
# de maillage. Si tu le sculptais, il mentirait au premier réglage. »
# C'est ce mensonge-là que ces tests interdisent.

func test_the_ring_straddles_the_real_reach() -> void:
	for reach in [1.0, 4.5, 5.0, 12.0]:
		var radii := EnemyController.aura_ring_radii(reach)
		assert_true(radii.x < reach and radii.y > reach,
			"l'anneau encadre la portée %.1f (%.2f .. %.2f)" % [reach, radii.x, radii.y])
		assert_almost_eq((radii.x + radii.y) * 0.5, reach, 0.001,
			"et il est CENTRÉ dessus : c'est le milieu du trait qui est la frontière")

func test_the_ring_never_collapses_on_a_tiny_reach() -> void:
	# Une portée plus petite que l'épaisseur du trait donnerait un rayon intérieur négatif,
	# donc un tore retourné. Le garde-fou est muet mais il tient.
	var radii := EnemyController.aura_ring_radii(0.05)
	assert_true(radii.x > 0.0, "rayon intérieur positif (%.3f)" % radii.x)
	assert_true(radii.y > radii.x, "et l'anneau garde une épaisseur")

func test_the_shipped_carrier_shows_the_reach_it_actually_has() -> void:
	# Le lien qui compte : la Resource et le visuel doivent dire le MÊME nombre. Le jour où
	# quelqu'un règle `aura_radius` pour l'équilibrage, ce test dit si l'anneau a suivi.
	var data: EnemyData = load("res://resources/enemies/shield_carrier.tres")
	assert_true(data.aura_radius > 0.0, "le porteur livré a bien une portée")
	var radii := EnemyController.aura_ring_radii(data.aura_radius)
	assert_almost_eq((radii.x + radii.y) * 0.5, data.aura_radius, 0.001,
		"l'anneau montre les %.1f unités de la Resource" % data.aura_radius)
