extends "res://tests/test_case.gd"
## Les invariants du survol du Long Cortege (niveau 2).
##
## ⚠️ UN SURVOL NE REVIENT JAMAIS EN ARRIERE. Chaque cible n'est tirable que pendant la fenetre
## ou elle est a l'ecran ; des points de vie choisis au-dessus de cette fenetre rendent la cible
## indestructible EN PRATIQUE, et le joueur croira mal jouer. C'est le defaut qu'ADR-0024 a paye
## sur le flux du Leviathan, et ce fichier existe pour qu'il ne se reproduise pas.

const TuningScript := preload("res://resources/data/cortege_tuning.gd")
## ⚠️ LA RESOURCE LIVREE, pas une neuve. Un test qui valide autre chose que la donnee du jeu ne
## valide rien : le reglage du Leviathan avait diverge de son script, et le boss tournait sur une
## Resource invalide pendant que la porte de qualite restait verte.
const SHIPPED := "res://resources/levels/long_cortege_tuning.tres"

func _sound() -> CortegeTuning:
	return load(SHIPPED).duplicate()

func test_the_shipped_resource_validates() -> void:
	var tuning: CortegeTuning = load(SHIPPED)
	var errors := tuning.validate()
	assert_eq(errors.size(), 0, "le reglage livre est valide : %s" % str(errors))

## La fenetre de tir se DEDUIT de la vitesse, elle ne se saisit pas.
func test_the_window_shrinks_when_the_hull_scrolls_faster() -> void:
	var tuning := _sound()
	tuning.scroll_speed = 2.0
	var lent := tuning.window_for(20.0)
	tuning.scroll_speed = 4.0
	var rapide := tuning.window_for(20.0)
	assert_almost_eq(lent, 10.0, 0.001, "20 unites a 2 u/s : dix secondes")
	assert_true(rapide < lent, "deux fois plus vite, deux fois moins de temps (%.1f contre %.1f)" % [rapide, lent])

func test_a_stopped_hull_offers_no_window_instead_of_dividing_by_zero() -> void:
	var tuning := _sound()
	tuning.scroll_speed = 0.0
	assert_almost_eq(tuning.window_for(20.0), 0.0, 0.001, "aucune fenetre, et aucune division par zero")
	assert_true(tuning.validate().size() > 0, "et le reglage est refuse")

## ⚠️ LE CŒUR DU FICHIER. Une cible qui demande plus que ce que sa fenetre permet ne peut pas
## tomber — et rien a l'ecran ne le dit au joueur.
func test_a_bay_that_cannot_fall_in_its_window_is_refused() -> void:
	var tuning := _sound()
	tuning.bay_health = tuning.bay_reachable() * 1.2
	var errors := tuning.validate()
	assert_true(errors.size() > 0, "un pont intenable est refuse")
	assert_true(str(errors[0]).contains("ne peut PAS tomber"),
		"et l'erreur DIT pourquoi : %s" % errors[0])

func test_a_node_that_cannot_fall_in_its_window_is_refused() -> void:
	var tuning := _sound()
	tuning.node_health = tuning.node_reachable() * 1.5
	assert_true(tuning.validate().size() > 0, "un noeud intenable est refuse")

## L'autre bord : une decision qui tombe en passant n'est plus une decision.
func test_a_bay_that_falls_on_the_way_past_is_refused() -> void:
	var tuning := _sound()
	tuning.bay_health = tuning.bay_reachable() * 0.2
	var errors := tuning.validate()
	assert_true(errors.size() > 0, "un pont trop fragile est refuse")
	assert_true(str(errors[0]).contains("tombe en passant"), "et l'erreur le dit : %s" % errors[0])

## ⚠️ ET LA TOURELLE SUIT LA REGLE INVERSE. Elle est une cible d'OPPORTUNITE, pas une decision :
## il y en a une douzaine, souvent plusieurs a l'ecran. Elle a besoin d'un PLAFOND. La premiere
## ecriture de l'invariant leur appliquait a toutes la meme regle, et exigeait donc d'une
## tourelle qu'elle coute aussi cher qu'un pont.
func test_a_turret_that_monopolises_the_window_is_refused() -> void:
	var tuning := _sound()
	tuning.turret_health = tuning.turret_reachable() * 0.6
	var errors := tuning.validate()
	assert_true(errors.size() > 0, "une tourelle qui monopolise la fenetre est refusee")
	assert_true(str(errors[0]).contains("file d'attente"), "et l'erreur le dit : %s" % errors[0])

func test_a_cheap_turret_is_accepted_where_a_cheap_bay_is_not() -> void:
	var tuning := _sound()
	tuning.turret_health = tuning.turret_reachable() * 0.1
	assert_eq(tuning.validate().size(), 0,
		"une tourelle bon marche passe — elle n'a pas a etre une decision")

## La duree se DEDUIT de la geometrie et de la vitesse, elle ne se declare pas.
func test_the_level_lasts_what_the_geometry_and_the_speed_say() -> void:
	var tuning := _sound()
	tuning.section_count = 5
	tuning.section_length = 100.0
	tuning.scroll_speed = 2.5
	assert_almost_eq(tuning.level_duration(), 200.0, 0.001, "500 unites a 2,5 u/s")
	assert_almost_eq(tuning.section_duration(), 40.0, 0.001, "et 40 s par section")

func test_a_survey_that_drags_beyond_the_promise_is_refused() -> void:
	var tuning := _sound()
	tuning.scroll_speed = 0.6
	var errors := tuning.validate()
	assert_true(errors.size() > 0, "un survol interminable est refuse")

## Reprise de l'invariant 6 du Leviathan : un tir sans preavis est une taxe, pas une difficulte.
func test_a_turret_always_telegraphs_before_it_fires() -> void:
	var tuning := _sound()
	tuning.turret_windup_time = tuning.turret_beam_time * 0.2
	var errors := tuning.validate()
	assert_true(errors.size() > 0, "un telegraphe trop court est refuse")
	assert_true(str(errors[0]).contains("telegraphe") or str(errors[0]).contains("préavis"),
		"et l'erreur le nomme : %s" % errors[0])

## Un pont qui ne produit pas assez pendant sa fenetre ne pese pas sur la decision de l'abattre.
func test_a_bay_that_barely_releases_anything_is_refused() -> void:
	var tuning := _sound()
	tuning.bay_release_interval = tuning.window_for(tuning.bay_visible_span) * 0.9
	var errors := tuning.validate()
	assert_true(errors.size() > 0, "un pont qui lache une seule fois est refuse")

## ⚠️ DEUX CADENCES DE REFERENCE, ET C'EST LA LEÇON D'ADR-0024. Se comparer a une seule revient
## a se donner raison : sur une baie de plusieurs metres les canons d'aile portent, sur un noeud
## ils partent a cote.
func test_a_node_is_sized_against_the_nose_guns_not_the_wing_guns() -> void:
	var tuning := _sound()
	assert_true(tuning.node_reference_dps < tuning.reference_dps,
		"la cadence sur un noeud (%.0f) est plus basse que sur une cible large (%.0f)"
			% [tuning.node_reference_dps, tuning.reference_dps])
	assert_true(tuning.node_reachable() < tuning.bay_reachable(),
		"donc un noeud offre moins de degats atteignables qu'un pont, a fenetre comparable")
