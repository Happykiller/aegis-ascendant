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

## ⚠️ Le piège que ce test ferme : `apply_pull()` AFFECTAIT la valeur. Le jour où
## le boss final et un champ de mines coexisteront — un EncounterDirector est au
## backlog — l'ordre d'appel aurait décidé du résultat en silence : un appel du
## boss arrivant après les puits des mines les aurait tous effacés.
func test_the_bosss_call_site_no_longer_erases_the_mines() -> void:
	var fighter := _fighter()
	fighter.add_pull(Vector2(2.0, 0.0))
	fighter.apply_pull(Vector2(0.0, 5.0))
	var pull := fighter.consume_pull()
	assert_almost_eq(pull.x, 2.0, 0.0001, "le puits de la mine a survécu à l'appel du boss")
	assert_almost_eq(pull.y, 5.0, 0.0001, "et le champ du boss est bien là")

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
