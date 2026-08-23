extends "res://tests/test_case.gd"
## Menace de proximité (EnemyReaction) — machine à états pure, testée sans joueur.
##
## C'est le premier comportement du jeu qui dépend d'AUTRE CHOSE que du temps. On
## le teste quand même en headless, sans arbre de scène : la bibliothèque ne reçoit
## qu'une distance, et c'est le test qui joue le rôle du joueur qui s'approche.

func _mine() -> EnemyData:
	var data := EnemyData.new()
	data.alert_radius = 4.0
	data.trigger_radius = 2.0
	data.windup_time = 0.6
	data.active_time = 0.4
	data.rearm_time = 0.0
	return data

## Une unité sans rayon de déclenchement est un ennemi ordinaire : elle suit sa
## courbe et n'attend personne. C'est ce qui dispense d'un enum de plus.
func test_an_enemy_without_a_trigger_radius_never_reacts() -> void:
	var data := EnemyData.new()
	assert_false(EnemyReaction.is_reactive(data), "sans rayon, pas de réaction")
	assert_true(EnemyReaction.is_reactive(_mine()), "avec rayon, elle réagit")

func test_it_sleeps_until_the_player_enters_its_alert_radius() -> void:
	var data := _mine()
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.DORMANT, 9.0, 12.0, data),
		EnemyReaction.State.DORMANT, "loin, elle dort")
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.DORMANT, 9.0, 3.5, data),
		EnemyReaction.State.ALERT, "dans le rayon d'alerte, elle s'éveille")

## L'éveil est un AVERTISSEMENT, pas un engagement : entre les deux rayons, le
## joueur peut encore faire demi-tour, et c'est toute la décision qu'on lui vend.
func test_alert_alone_never_commits_to_the_charge() -> void:
	var data := _mine()
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.ALERT, 5.0, 3.0, data),
		EnemyReaction.State.ALERT, "éveillée mais pas déclenchée, elle attend")
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.ALERT, 0.1, 1.5, data),
		EnemyReaction.State.WINDUP, "au rayon de déclenchement, elle s'engage")

## Hystérésis : un joueur posé pile sur le rayon ferait clignoter la coque à chaque
## image. Sortir demande plus que d'entrer.
func test_leaving_the_alert_radius_takes_a_margin() -> void:
	var data := _mine()
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.ALERT, 1.0, 4.2, data),
		EnemyReaction.State.ALERT, "juste au-delà du rayon, elle reste éveillée")
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.ALERT, 1.0,
		4.0 * EnemyReaction.RELEASE_FACTOR + 0.1, data),
		EnemyReaction.State.DORMANT, "franchement partie, elle se rendort")

## ⚠️ LE CONTRAT DU TÉLÉGRAPHE. Une fois engagée, elle part — même si le joueur
## recule à l'autre bout du champ. Un télégraphe annulable apprend au joueur à
## ignorer les télégraphes, et c'est toute la lisibilité du jeu qui s'écroule.
func test_a_started_windup_always_goes_off_even_if_the_player_flees() -> void:
	var data := _mine()
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.WINDUP, 0.2, 999.0, data),
		EnemyReaction.State.WINDUP, "il s'éloigne, elle continue quand même")
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.WINDUP, 0.7, 999.0, data),
		EnemyReaction.State.ACTIVE, "et au bout du compte elle part")

func test_the_windup_lasts_exactly_what_the_data_says() -> void:
	var data := _mine()
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.WINDUP, 0.59, 1.0, data),
		EnemyReaction.State.WINDUP, "avant l'échéance, elle charge encore")
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.WINDUP, 0.60, 1.0, data),
		EnemyReaction.State.ACTIVE, "à l'échéance, elle décharge")

func test_the_charge_ends_and_leaves_her_spent() -> void:
	var data := _mine()
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.ACTIVE, 0.3, 1.0, data),
		EnemyReaction.State.ACTIVE, "la charge tient sa durée")
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.ACTIVE, 0.5, 1.0, data),
		EnemyReaction.State.SPENT, "puis elle est vidée")

## Deux règles du jeu différentes, tenues par une seule valeur : une mine à usage
## unique est un obstacle qu'on peut DÉPENSER, une mine qui se réarme est une zone
## interdite. Le zéro n'est pas un défaut de réglage, c'est un choix de design.
func test_a_single_use_mine_stays_spent_forever() -> void:
	var data := _mine()
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.SPENT, 60.0, 1.0, data),
		EnemyReaction.State.SPENT, "sans temps de réarmement, elle reste vidée")

func test_a_rearming_mine_comes_back_to_life() -> void:
	var data := _mine()
	data.rearm_time = 3.0
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.SPENT, 2.0, 1.0, data),
		EnemyReaction.State.SPENT, "pendant le temps mort, elle est inerte")
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.SPENT, 3.0, 1.0, data),
		EnemyReaction.State.DORMANT, "puis elle se réarme")

# --- Ce que la coque MONTRE ---------------------------------------------------

## Le télégraphe doit être lisible comme une jauge : 0 au départ, 1 à l'échéance.
## C'est ce que consomment l'animation et les signes vitaux.
func test_the_windup_ratio_reads_like_a_gauge() -> void:
	var data := _mine()
	assert_almost_eq(EnemyReaction.windup_ratio(EnemyReaction.State.WINDUP, 0.0, data), 0.0,
		0.0001, "au départ, rien n'est chargé")
	assert_almost_eq(EnemyReaction.windup_ratio(EnemyReaction.State.WINDUP, 0.3, data), 0.5,
		0.0001, "à mi-course, la moitié")
	assert_almost_eq(EnemyReaction.windup_ratio(EnemyReaction.State.WINDUP, 5.0, data), 1.0,
		0.0001, "et ça ne dépasse jamais 1")

## Une division par zéro sur un télégraphe instantané rendrait NaN, qui se
## propagerait dans l'énergie d'un matériau — une coque invisible, sans erreur.
func test_an_instant_windup_does_not_divide_by_zero() -> void:
	var data := _mine()
	data.windup_time = 0.0
	var ratio := EnemyReaction.windup_ratio(EnemyReaction.State.WINDUP, 0.0, data)
	assert_true(is_finite(ratio), "le ratio reste fini (obtenu %f)" % ratio)

## Le régime monte à mesure qu'on s'approche, et il est à fond pendant la charge.
## Une coque endormie, elle, ne montre rien du tout : c'est ce qui rend l'éveil
## d'une seule mine dans un champ immédiatement visible.
func test_the_threat_rises_as_the_player_closes_in() -> void:
	var data := _mine()
	var far := EnemyReaction.threat_ratio(EnemyReaction.State.ALERT, 0.0, 3.9, data)
	var near := EnemyReaction.threat_ratio(EnemyReaction.State.ALERT, 0.0, 2.1, data)
	assert_true(far < near, "plus il approche, plus elle monte (%f puis %f)" % [far, near])
	assert_true(near < EnemyReaction.threat_ratio(EnemyReaction.State.WINDUP, 0.3, 1.0, data),
		"et l'engagement dépasse le simple éveil")
	assert_eq(EnemyReaction.threat_ratio(EnemyReaction.State.DORMANT, 0.0, 12.0, data), 0.0,
		"endormie, elle ne montre rien")
	assert_eq(EnemyReaction.threat_ratio(EnemyReaction.State.ACTIVE, 0.1, 1.0, data), 1.0,
		"en charge, elle est à fond")
