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

# --- Le sursis de la mine (ARMING, 2026-08-26) -------------------------------
#
# ⚠️ CES TESTS GARDENT UN INVARIANT ÉCRIT ET LA DEMANDE QUI SEMBLAIT LE CONTREDIRE.
# L'opérateur voulait qu'une mine « se referme si on ressort en moins d'1 s ». Le fichier
# posait pourtant, noir sur blanc : « WINDUP NE REVIENT PAS EN ARRIÈRE ». Les deux tiennent
# ensemble parce que le sursis est une étape AVANT le télégraphe, pas dedans — et c'est
# exactement ce qu'un test doit empêcher quelqu'un de « simplifier » plus tard.

func _mine_with_grace() -> EnemyData:
	var data := EnemyData.new()
	data.alert_radius = 8.0
	data.trigger_radius = 5.5
	data.arm_grace = 1.0
	data.windup_time = 0.7
	data.active_time = 0.15
	return data

func test_entering_the_zone_arms_without_engaging() -> void:
	var data := _mine_with_grace()
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.ALERT, 0.0, 5.0, data),
		EnemyReaction.State.ARMING, "elle mord, mais ne s'engage pas encore")

func test_leaving_in_time_closes_the_mine_again() -> void:
	var data := _mine_with_grace()
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.ARMING, 0.6, 9.0, data),
		EnemyReaction.State.ALERT, "sortie avant l'échéance : elle se referme")

func test_staying_past_the_grace_commits() -> void:
	var data := _mine_with_grace()
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.ARMING, 1.0, 5.0, data),
		EnemyReaction.State.WINDUP, "à l'échéance, l'engagement part")

## ⚠️ L'INVARIANT LUI-MÊME : une fois le télégraphe lancé, s'éloigner ne sauve plus.
func test_the_telegraph_still_never_reverses() -> void:
	var data := _mine_with_grace()
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.WINDUP, 0.1, 999.0, data),
		EnemyReaction.State.WINDUP, "fuir pendant le télégraphe ne l'annule pas")

## ⚠️ RÈGLE RÉVISÉE LE 2026-08-26. Première version : la coque restait FERMÉE pendant le
## sursis, pour préserver « une mine qui bâillerait dès qu'on l'approche aurait déjà tout
## dit ». L'opérateur a tranché autrement — « le sursis les ouvre comme si elles étaient
## armées, et se referme si on part à temps » — et la crainte d'origine reste satisfaite,
## mais autrement : le sursis n'ouvre qu'AUX DEUX TIERS, le télégraphe ouvre EN GRAND.
## Il reste donc quelque chose à lire au moment qui décide.
func test_the_reprieve_opens_the_shell_partway() -> void:
	var data := _mine_with_grace()
	assert_almost_eq(EnemyReaction.open_ratio(EnemyReaction.State.ARMING, 0.0, data), 0.0, 0.001,
		"fermée à l'entrée")
	assert_almost_eq(EnemyReaction.open_ratio(EnemyReaction.State.ARMING, 1.0, data),
		EnemyReaction.ARMING_OPEN, 0.001, "aux deux tiers à l'échéance")
	assert_true(EnemyReaction.ARMING_OPEN < 0.8,
		"et PAS en grand : le télégraphe doit garder de quoi s'annoncer")

## Le télégraphe REPREND où le sursis s'est arrêté. Repartir de zéro ferait claquer la coque
## fermée à l'instant précis de l'engagement — le contraire de ce qu'elle doit annoncer.
func test_the_telegraph_finishes_what_the_reprieve_started() -> void:
	var data := _mine_with_grace()
	assert_almost_eq(EnemyReaction.open_ratio(EnemyReaction.State.WINDUP, 0.0, data),
		EnemyReaction.ARMING_OPEN, 0.001, "l'engagement part de l'ouverture du sursis")
	assert_almost_eq(EnemyReaction.open_ratio(EnemyReaction.State.WINDUP, data.windup_time, data),
		1.0, 0.001, "et finit grande ouverte")

## ⚠️ Les huit autres familles n'ont pas de sursis : leur coque s'ouvre de 0 à 1 comme avant.
func test_a_unit_without_grace_opens_from_shut() -> void:
	var data := _mine_with_grace()
	data.arm_grace = 0.0
	assert_almost_eq(EnemyReaction.open_ratio(EnemyReaction.State.WINDUP, 0.0, data), 0.0, 0.001,
		"sans sursis, le telegraphe part de la coque fermee")

## Le joueur doit distinguer « elle m'a senti » de « c'est parti ».
func test_the_reprieve_reads_between_alert_and_commitment() -> void:
	var data := _mine_with_grace()
	var arming := EnemyReaction.threat_ratio(EnemyReaction.State.ARMING, 0.9, 5.0, data)
	var alert := EnemyReaction.threat_ratio(EnemyReaction.State.ALERT, 0.0, 5.6, data)
	assert_true(arming > alert, "le sursis monte au-dessus du simple éveil")
	assert_true(arming < 1.0, "sans atteindre le régime de l'engagement")

## ⚠️ Toute unité SANS sursis garde le comportement d'avant, bit pour bit. C'est ce qui
## rend ce changement sûr pour les huit autres familles du bestiaire.
func test_a_unit_without_grace_engages_on_contact_as_before() -> void:
	var data := _mine_with_grace()
	data.arm_grace = 0.0
	assert_eq(EnemyReaction.next_state(EnemyReaction.State.ALERT, 0.0, 5.0, data),
		EnemyReaction.State.WINDUP, "sans sursis, le contact engage immediatement")
