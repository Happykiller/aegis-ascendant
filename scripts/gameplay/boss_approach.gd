class_name BossApproach
extends RefCounted
## L'approche du Pale Leviathan — le dernier puits gravitique ne meurt pas, il monte
## (`ADR-0027`, lot 5 du plan inter-boss, option D).
##
## POURQUOI ELLE EXISTE. La bible de design relève deux manques qui se répondent :
##
##   « Ralentir avant la fin — ❌ NON TENU. Le boss final arrive après le champ
##     d'astéroïdes, sans respiration. »   (docs/design/bible/03-niveau-et-rythme.md)
##   « Le boss final n'enseigne rien avant de l'exiger. »   (04-boss.md)
##
## Or la phase 2 enseigne DÉJÀ l'aspiration, et personne ne l'avait relevé : le Null Maw
## et le boss appellent la MÊME fonction — `GravityWell.pull_at()`. `gravity_well.gd` le
## dit de lui-même, « la primitive de la phase 2 du Pale Leviathan », et
## `enemy_controller.gd` en écho, « gravitique du boss, mais posée par une unité de vague ».
## Quatre puits traversent le champ ; la leçon du boss y est donnée par accident.
##
## Cette approche la RÉCOLTE. Le champ nettoyé, un dernier puits reste, grossit et dérive
## vers le haut du cadre — là où le Leviathan entrera. La leçon et l'examen se touchent.
##
## Fonctions **pures et statiques**, sur le modèle de `GravityWell` et d'`EnemyReaction` :
## aucun nœud, aucun état, aucune allocation. Une mécanique qu'on n'atteint qu'après deux
## minutes de jeu doit rester vérifiable en headless.
##
## ⚠️ CE PUITS NE BLESSE PAS ET NE PIÈGE PAS. C'est une respiration, pas une menace de
## plus : il n'a ni coque, ni PV, ni salve, et son aspiration reste sous l'invariant de
## `GravityWell.leaves_room()`. Un temps mort qui tue n'est pas un temps mort.

## Durée de l'approche. La bible pose la garde en même temps que le manque : « la durée de
## l'arc est déjà à sa cible (2-3 min), ajouter du temps mort peut coûter plus que ça ne
## rapporte ». Trois secondes tiennent la respiration sans repayer une phase — et le boss
## met encore ~1,6 s à descendre de y = 12 à son poste, qui s'y ajoutent à l'écran.
const DURATION := 3.0

## D'où le puits part, et où il va. Il monte vers `(0, 11)` parce que c'est de LÀ que le
## Leviathan descend (`plane_position = (0, 12)` puis glissement vers `(0, 4)`) : le
## joueur suit le puits des yeux et trouve le boss au bout du regard.
const START_CENTRE := Vector2(0.0, 4.0)
const END_CENTRE := Vector2(0.0, 11.0)

## Le puits s'ÉLARGIT en montant. Il ne devient pas plus fort de près, il devient plus
## large de loin — c'est ce qui fait qu'on le subit sans pouvoir le fuir, alors même que
## sa vitesse reste modeste.
const START_RADIUS := 3.0
const END_RADIUS := 9.0

## ⚠️ Vitesse maximale d'aspiration, et elle est VOLONTAIREMENT basse. Le Null Maw du champ
## tire à 7,0 u/s ; celui-ci plafonne à 5,0. Il doit se SENTIR, pas se subir : c'est le
## dernier moment où le joueur replace son chasseur avant le boss.
const MAX_PULL_SPEED := 5.0


## Avancement de l'approche, de 0 à 1.
static func ratio(elapsed: float, duration: float) -> float:
	if duration <= 0.0:
		return 1.0
	return clampf(elapsed / duration, 0.0, 1.0)

## Où est le centre du puits à cet instant.
static func centre_at(elapsed: float, duration: float) -> Vector2:
	return START_CENTRE.lerp(END_CENTRE, ratio(elapsed, duration))

## Rayon du puits à cet instant.
static func radius_at(elapsed: float, duration: float) -> float:
	return lerpf(START_RADIUS, END_RADIUS, ratio(elapsed, duration))

## Vitesse d'aspiration à cet instant.
##
## ⚠️ ELLE PART DE ZÉRO, et c'est la seule courbe des trois qui ne soit pas linéaire. Une
## aspiration qui vaut déjà 5 u/s à la première image ARRACHE le chasseur des mains du
## joueur à l'instant précis où la vague vient de se vider — il lit ça comme un bug, pas
## comme un puits. Le carré de l'avancement la fait naître doucement puis monter.
static func speed_at(elapsed: float, duration: float) -> float:
	var t := ratio(elapsed, duration)
	return MAX_PULL_SPEED * t * t

## L'approche est-elle terminée ?
static func is_over(elapsed: float, duration: float) -> bool:
	return elapsed >= duration

## Le puits laisse-t-il jouer ? Même invariant que `GravityWell`, posé ici pour qu'un
## réglage de `MAX_PULL_SPEED` ne puisse pas le franchir sans qu'un test le dise.
static func leaves_room(player_max_speed: float) -> bool:
	return GravityWell.leaves_room(MAX_PULL_SPEED, player_max_speed)
