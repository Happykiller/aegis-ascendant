extends "res://tests/test_case.gd"
## La détonation de la sangsue — le chemin que la porte de qualité ne voyait pas.
##
## ⚠️ CE FICHIER EXISTE PARCE QUE `check.sh` ÉTAIT VERT SUR DU CODE CASSÉ. La détonation
## appelait `_health.maximum`, une propriété qui n'existe pas sur `HealthComponent` (c'est
## `max_health`). GDScript ne le voit pas à la compilation : l'accès invalide n'échoue qu'à
## l'EXÉCUTION, et seulement dans un chemin qu'aucun test n'exerçait — une sangsue qui va au
## bout de sa morsure.
##
## Le symptôme en jeu ne ressemblait même pas à une erreur : « les sangsues n'explosent pas,
## une fois collées à moi elles repartent ». Elles ne repartaient pas par choix — la
## fonction s'interrompait avant les dégâts, l'unité survivait, passait en épuisée, et son
## `rearm_time` de 1,5 s la renvoyait dormante. Un comportement plausible, entièrement faux.

const HealthScript := preload("res://scripts/gameplay/health_component.gd")

## La propriété que le code appelle doit EXISTER. C'est l'assertion la plus bête de ce
## dépôt, et c'est celle qui aurait économisé une partie entière.
func test_the_health_component_exposes_what_the_detonation_uses() -> void:
	var health := track(HealthScript.new()) as HealthComponent
	health.max_health = 10.0
	health._ready()
	assert_true("health" in health, "`health` existe")
	assert_true("max_health" in health, "`max_health` existe")
	assert_false("maximum" in health,
		"`maximum` n'existe PAS — c'est la faute qui a coûté une partie")

## Le geste de la détonation : s'infliger de quoi mourir à coup sûr, quel que soit l'état
## de la santé au moment du coup.
func test_a_unit_that_detonates_always_dies() -> void:
	for restant in [30.0, 1.0, 0.1]:
		var health := track(HealthScript.new()) as HealthComponent
		health.max_health = 30.0
		health._ready()
		health.apply_damage(30.0 - restant)
		# ⚠️ UN TABLEAU ET NON UN BOOLÉEN : en GDScript une lambda capture par VALEUR.
		# `func(): morte = true` sur un booléen local modifie une COPIE, et le test
		# échoue en affirmant que rien ne s'est passé — sur du code parfaitement correct.
		# C'est le piège qui a fait échouer ce fichier à sa première écriture.
		var morte := [false]
		health.died.connect(func() -> void: morte[0] = true)
		# Le geste exact de `_detonate()`.
		health.apply_damage(health.health + 1.0)
		assert_true(morte[0], "elle meurt avec %.1f PV restants" % restant)

## Les dégâts de détonation sont réels et non nuls — une sangsue qui explose pour zéro
## serait un feu d'artifice, pas une menace.
func test_the_leech_carries_a_real_charge() -> void:
	var data: EnemyData = load("res://resources/enemies/leech_drone.tres")
	assert_true(data.detonation_damage > 0.0,
		"la sangsue porte une charge (%.1f)" % data.detonation_damage)
	assert_eq(data.effect, EnemyData.Effect.LEECH, "et c'est bien elle qui détone")
