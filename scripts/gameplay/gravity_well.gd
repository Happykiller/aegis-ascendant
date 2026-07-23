class_name GravityWell
## Champ d'aspiration radial — la primitive de la phase 2 du Pale Leviathan
## (`docs/design/BOSS_PALE_LEVIATHAN.md` §4 et §8.2).
##
## Fonctions **pures et statiques**, sur le modèle de `BossMovement` : aucun nœud,
## aucun état, aucune allocation. C'est ce qui rend une mécanique qu'on n'atteint
## qu'après trois minutes de jeu vérifiable en headless.
##
## CE QUE LE CHAMP FAIT AU JOUEUR — il ajoute une vitesse vers le centre. La menace
## n'est PAS le contact avec la gueule : c'est de ne plus pouvoir esquiver. Le rideau
## de balles n'a pas changé, mais la marge de manœuvre a fondu.
##
## ⚠️ L'INVARIANT QUI REND LA PHASE JOUABLE — `speed_max` doit rester **strictement
## inférieure** à `PlayerStats.max_speed`. Au-delà, le chasseur est aspiré quoi qu'il
## fasse et la phase devient une cinématique. C'est le genre de réglage qui a l'air
## parfaitement sensé isolément : d'où `leaves_room()`, appelé par `validate()`.
##
## La phase 4 casse volontairement cet invariant (on n'y résiste plus, on **entre**) :
## c'est le sujet de la phase, et `escapes()` dit dans quel régime on se trouve.

## Part de mobilité que le joueur doit conserver au pire de l'aspiration. À 0,4, il
## garde 40 % de sa vitesse : assez pour replacer son chasseur, pas assez pour ignorer
## le champ. En deçà, l'esquive devient une loterie.
const MIN_MOBILITY := 0.4

## Vitesse d'aspiration à une distance donnée, en unités par seconde.
##
## Le profil est linéaire et **borné** : maximal au centre, nul au-delà de `radius`.
## Pas d'inverse du carré — une vraie loi de gravité diverge près du centre et rend le
## réglage impossible à borner, alors que le joueur doit pouvoir traverser la zone.
static func speed_at(distance: float, radius: float, speed_max: float) -> float:
	if radius <= 0.0:
		return 0.0
	return speed_max * clampf(1.0 - distance / radius, 0.0, 1.0)

## Contribution de vitesse à ajouter à celle du joueur, en coordonnées du plan.
##
## ⚠️ Retourne `ZERO` pile au centre : la direction y est indéfinie, et normaliser un
## vecteur nul rendrait `NaN` — qui se propagerait silencieusement dans la position du
## joueur jusqu'à le faire disparaître de l'écran sans une seule erreur au journal.
static func pull_at(position: Vector2, center: Vector2, radius: float,
		speed_max: float) -> Vector2:
	var offset := center - position
	var distance := offset.length()
	if distance <= 0.0001:
		return Vector2.ZERO
	return offset / distance * speed_at(distance, radius, speed_max)

## Vitesse maximale du champ une fois `nodes_down` nœuds gravitiques abattus.
##
## Le soulagement est **fractionnaire, pas tout-ou-rien** : le joueur récupère sa
## mobilité morceau par morceau et le sent dans les doigts. Chaque victoire partielle
## paie, ce qui est exactement ce qu'on veut d'une phase de résistance.
static func speed_max_after(base_speed_max: float, nodes_down: int,
		node_count: int) -> float:
	if node_count <= 0:
		return base_speed_max
	var remaining := clampi(node_count - nodes_down, 0, node_count)
	return base_speed_max * float(remaining) / float(node_count)

## Le joueur peut-il encore fuir le champ ? Faux = il est aspiré quoi qu'il fasse.
static func escapes(speed_max: float, player_max_speed: float) -> bool:
	return speed_max < player_max_speed

## Le joueur garde-t-il assez de mobilité pour jouer ? C'est la question que pose
## `validate()` : `escapes()` seul autorise un champ à 13,9 u/s contre 14,0, où l'on
## avance à un dixième d'unité par seconde — techniquement libre, injouable en fait.
static func leaves_room(speed_max: float, player_max_speed: float) -> bool:
	if player_max_speed <= 0.0:
		return false
	return speed_max <= player_max_speed * (1.0 - MIN_MOBILITY)
