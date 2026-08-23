extends "res://tests/test_case.gd"
## L'aspiration extérieure du chasseur (GravityWell) — composition et consommation.
##
## Ce fichier existe à cause d'un défaut qui n'aurait produit ni erreur, ni test
## rouge, ni ligne au journal, et qui ne se serait manifesté que dans une partie
## menée jusqu'à l'appontage : l'aspiration était consommée au MILIEU du
## déplacement libre, donc jamais pendant l'autopilote ni pendant la mort — deux
## chemins qui rendent la main plus haut. Tant qu'un seul champ AFFECTAIT la
## valeur, la traîner était sans conséquence. Depuis que plusieurs puits
## s'AJOUTENT, elle aurait grossi sans borne.

func _fighter() -> PlayerFighterController:
	# Hors de l'arbre : `_ready` ne tourne pas, mais l'accumulateur et sa
	# consommation ne dépendent d'aucun enfant. C'est tout l'intérêt de les avoir
	# sortis de la boucle physique.
	return track(PlayerFighterController.new()) as PlayerFighterController

## Deux puits ouverts en même temps doivent tirer chacun leur part. Sinon le
## dernier appelé gagne, et le joueur traverse tranquillement un nid qui devrait
## l'écraser.
func test_two_wells_pull_together_instead_of_overwriting_each_other() -> void:
	var fighter := _fighter()
	fighter.add_pull(Vector2(3.0, 0.0))
	fighter.add_pull(Vector2(0.0, 4.0))
	var pull := fighter.consume_pull()
	assert_almost_eq(pull.x, 3.0, 0.0001, "le premier puits tire encore")
	assert_almost_eq(pull.y, 4.0, 0.0001, "et le second s'y ajoute")

## ⚠️ LA PORTE QUI RESTE FERMÉE. Il a existé un `apply_pull()` qui AFFECTAIT la
## valeur, et tant qu'il n'y avait qu'un champ dans le jeu, rien ne pouvait le
## révéler : le défaut était masqué par le NOMBRE D'APPELANTS, pas par le code. Le
## boss et les mines ont désormais la même porte, et ce test échouera si quelqu'un
## en rouvre une qui écrase — un appelant qui affecte annulerait en silence tous
## les autres de la même image.
func test_there_is_no_second_door_that_overwrites() -> void:
	var fighter := _fighter()
	assert_false(fighter.has_method("apply_pull"),
		"aucune voie d'affectation n'est offerte a cote de add_pull()")

## Le scénario que le boss et les mines partageront le jour où une rencontre les
## fera cohabiter : chacun pose sa part, l'ordre d'appel n'y change rien.
func test_a_boss_field_and_a_minefield_compose_in_any_order() -> void:
	var first := _fighter()
	first.add_pull(Vector2(2.0, 0.0))
	first.add_pull(Vector2(0.0, 5.0))
	var second := _fighter()
	second.add_pull(Vector2(0.0, 5.0))
	second.add_pull(Vector2(2.0, 0.0))
	assert_true(first.consume_pull().is_equal_approx(second.consume_pull()),
		"le resultat ne depend pas de qui a parle en premier")

## Consommer, c'est prendre ET effacer. Un chemin qui lirait sans effacer
## rejouerait la même aspiration à chaque image.
func test_consuming_leaves_nothing_behind() -> void:
	var fighter := _fighter()
	fighter.add_pull(Vector2(6.0, -2.0))
	fighter.consume_pull()
	var second := fighter.consume_pull()
	assert_almost_eq(second.length(), 0.0, 0.0001,
		"la deuxième lecture ne rend plus rien (obtenu %s)" % second)

## Le cas qui aurait explosé : un puits qui pousse pendant que le chasseur ne
## consomme pas (appontage, mort). L'accumulateur monte — c'est attendu — mais une
## seule consommation doit tout solder, pas en laisser une part pour l'image
## suivante.
func test_a_long_unconsumed_pull_is_settled_in_one_go() -> void:
	var fighter := _fighter()
	for i in 120:
		fighter.add_pull(Vector2(0.5, 0.0))
	assert_almost_eq(fighter.consume_pull().x, 60.0, 0.0001, "tout est rendu d'un coup")
	assert_almost_eq(fighter.consume_pull().x, 0.0, 0.0001, "et rien ne reste pour la suite")

func test_no_pull_at_all_is_a_zero_not_a_surprise() -> void:
	assert_almost_eq(_fighter().consume_pull().length(), 0.0, 0.0001,
		"sans champ, l'aspiration est nulle")
