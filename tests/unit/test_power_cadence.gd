extends "res://tests/test_case.gd"
## La cadence de montée en puissance (spec §10.3).
##
## ⚠️ ELLE N'EST PAS ALÉATOIRE, malgré le nom de `roll_drop()` : un bonus tous les
## `_DROP_EVERY` ennemis, et un bonus sur `_POWER_EVERY` est un Power Core. C'est donc une
## fonction du **nombre d'ennemis abattus**, jamais du temps — conséquence à connaître avant
## de toucher au bestiaire : ajouter du popcorn ACCÉLÈRE la montée en puissance, ajouter des
## unités coriaces la ralentit, à durée de phase identique.
##
## Ce fichier garde le rapport entre cette cadence et la TAILLE de la vague d'ouverture.
## C'est ce rapport, et lui seul, qui décide de la puissance à laquelle on entre en phase 2 —
## et il peut être cassé des deux côtés, sans qu'aucun autre test ne bouge.

const OpeningWave: WaveData = preload("res://resources/encounters/wave_graybox_01.tres")
## Le contrat, en un nombre : combien d'ennemis pour un niveau de puissance.
const KILLS_PER_CORE := 24

## Niveau maximal jugé acceptable à l'entrée de la phase 2 (retour opérateur du
## 2026-08-27 : « max 4/5 en arrivant en phase 2 »).
const MAX_LEVEL_AT_PHASE_2 := 4

func test_a_power_core_costs_what_it_was_balanced_to_cost() -> void:
	assert_eq(PickupManager.KILLS_PER_POWER, KILLS_PER_CORE,
		"un Power Core tous les %d ennemis" % KILLS_PER_CORE)

## LA garde. Le niveau 5 demande 4 Cores ; s'il tombe dans la première moitié de la vague,
## on repart pour une phase 1 entière à pleine puissance — ce que le playtest a nommé.
func test_full_power_is_not_reached_in_the_middle_of_the_opening_wave() -> void:
	var units := 0
	for entry in OpeningWave.entries:
		units += entry.count
	var kills_for_max := 4 * PickupManager.KILLS_PER_POWER
	assert_true(kills_for_max > units * 0.80,
		"le niveau 5 demande %d kills sur une vague de %d (%.0f %%) — mesuré le 2026-08-27 : une partie jouée en tue ~74, le seuil doit rester au-dessus"
			% [kills_for_max, units, 100.0 * kills_for_max / float(units)])

## Le revers : une cadence trop lente rendrait la montée en puissance invisible, et le
## genre en fait « la moitié du plaisir » (`LOI-PUI-01`). La borne se DÉDUIT de la vague —
## le premier Core doit tomber dans son premier quart — plutôt que d'être un nombre posé.
func test_the_first_core_still_arrives_early() -> void:
	var units := 0
	for entry in OpeningWave.entries:
		units += entry.count
	assert_true(PickupManager.KILLS_PER_POWER <= units / 4,
		"le premier Power Core tombe au %dᵉ ennemi d'une vague de %d — au-delà du premier quart, la montée ne se sent plus"
			% [PickupManager.KILLS_PER_POWER, units])
