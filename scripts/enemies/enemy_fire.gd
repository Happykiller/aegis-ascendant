class_name EnemyFire
## Schémas de tir ennemis — géométrie PURE : (données, salve, index) -> direction.
##
## `EnemyPath` répond « où va cette coque » ; celui-ci répond « où part le coup ».
## Même forme, mêmes garanties : aucune dépendance à la scène, aucun état, aucune
## allocation — on rend UNE direction à la fois plutôt qu'un tableau, pour qu'une
## salve de vingt balles ne fabrique pas un tableau par tir. Testable en headless
## (tests/unit/test_enemy_fire.gd).
##
## RÈGLE DE VARIÉTÉ, la même qu'aux trajectoires : deux schémas doivent différer
## par leur FORME, pas par leurs constantes. Un éventail de trois balles n'est pas
## un éventail de cinq — c'est le même geste, et le joueur le voit. Chaque entrée
## ci-dessous a une signature qu'aucune autre ne peut imiter :
##
##   SINGLE  un coup droit vers le bas   — la ligne de base, celle qu'on apprend
##   NONE    aucun coup                  — l'unité menace autrement (aura, aspiration, contact)
##   FAN     éventail large vers le bas  — ferme un couloir, IGNORE le joueur : on le contourne
##   AIMED   salve resserrée VERS le joueur — le seul qui SUIT : punit l'immobilité
##   RADIAL  couronne complète           — aucune direction sûre, seule la DISTANCE sauve
##
## ⚠️ FAN et AIMED ne diffèrent pas par leur ouverture : ils diffèrent parce que
## l'un est aveugle et l'autre voit. Élargir l'un ou resserrer l'autre ne les
## rapprocherait pas — c'est ce que vérifie le test de variété.

## Vers le joueur, en coordonnées du plan (le même bas que `EnemyController`).
const DIR_DOWN := Vector2(0.0, -1.0)

## Ouverture de l'éventail aveugle, en degrés. Large : c'est un mur de couloir,
## et il doit se lire comme tel dès la première salve.
const FAN_SPREAD_DEG := 62.0
## Ouverture de la salve visée. Serrée : la menace est la VISÉE, pas la couverture.
const AIMED_SPREAD_DEG := 12.0
## Rotation d'une couronne à la suivante, en fraction d'intervalle entre deux
## balles. À 0,5 les couronnes s'entrelacent : les trous de la première sont
## bouchés par la seconde, donc rester immobile ne paie jamais.
const RADIAL_PHASE := 0.5


## Nombre de coups dans une salve. Zéro est une réponse valide (`NONE`).
static func shot_count(data: EnemyData) -> int:
	match data.fire:
		EnemyData.Fire.NONE:
			return 0
		EnemyData.Fire.SINGLE:
			return 1
		_:
			return maxi(data.burst_count, 1)


## Direction du `index`-ième coup de la `salvo`-ième salve.
##
## `from` et `player` sont en coordonnées du plan. Une unité qui ne voit pas le
## joueur (aucun joueur injecté) passe `from` pour les deux : `AIMED` retombe
## alors sur le tir droit plutôt que de rendre une direction nulle.
static func direction(data: EnemyData, salvo: int, index: int, from: Vector2,
		player: Vector2) -> Vector2:
	var count := shot_count(data)
	if count <= 0:
		return DIR_DOWN
	match data.fire:
		EnemyData.Fire.FAN:
			return DIR_DOWN.rotated(deg_to_rad(FAN_SPREAD_DEG) * _spread_ratio(index, count))
		EnemyData.Fire.AIMED:
			return _aim(from, player).rotated(
				deg_to_rad(AIMED_SPREAD_DEG) * _spread_ratio(index, count))
		EnemyData.Fire.RADIAL:
			var step := TAU / float(count)
			return DIR_DOWN.rotated(step * (float(index) + float(salvo) * RADIAL_PHASE))
		_:
			return DIR_DOWN


## Position du coup dans son éventail, de -0,5 (bord gauche) à +0,5 (bord droit).
## Un coup unique part au centre plutôt que sur un bord : sans ce cas, `count - 1`
## vaudrait zéro et l'éventail se diviserait par lui.
static func _spread_ratio(index: int, count: int) -> float:
	if count <= 1:
		return 0.0
	return float(index) / float(count - 1) - 0.5


## Direction du tireur vers le joueur, normalisée.
##
## ⚠️ Retourne le tir droit si les deux points coïncident : normaliser un vecteur
## nul rend `ZERO`, et une balle de vitesse nulle resterait vissée sur la coque
## jusqu'à l'expiration de son TTL, sans une seule erreur au journal.
static func _aim(from: Vector2, player: Vector2) -> Vector2:
	var offset := player - from
	if offset.length_squared() < 0.000001:
		return DIR_DOWN
	return offset.normalized()
