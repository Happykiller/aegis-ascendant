class_name EnemyHoming
## Poursuite ennemie — la seule chose du jeu qui vise le joueur en se déplaçant.
##
## ⚠️ CE FICHIER EXISTE PARCE QU'UNE POURSUITE NE PEUT PAS ÊTRE UNE `EnemyPath`.
## Les trajectoires sont des fonctions pures `(âge, spawn) → position` : c'est ce
## qui rend le pooling sûr et les tests possibles sans joueur (ADR-0022). Une
## poursuite, elle, accumule — sa position dépend de tout son passé. Elle est donc
## sortie de `EnemyPath` plutôt que de la corrompre.
##
## Ce qu'on y gagne quand même : la fonction ci-dessous reste **pure**. Elle prend
## un état et rend le suivant, sans rien retenir. Un test lui injecte une suite
## scriptée de positions joueur et obtient un résultat déterministe, image par
## image, sans arbre de scène (tests/unit/test_enemy_homing.gd).
##
## Le virage est **borné**, et c'est ce qui rend la sangsue esquivable. C'est
## exactement la raison pour laquelle `TargetableProjectile` borne le sien : un
## poursuivant qui vire instantanément est un poursuivant qui touche toujours, et
## le joueur n'a plus de réponse à lui opposer que le tir.

## En dessous, la direction de la vitesse n'a plus de sens : la faire tourner ferait
## partir la coque dans un cap arbitraire. Même garde que `TargetableProjectile`.
const MIN_STEERING_SPEED := 0.05


## Nouvelle vitesse après `delta` secondes de poursuite.
##
## On tourne la vitesse, on ne la remplace pas : sa norme est conservée, donc une
## sangsue ne peut pas accélérer en virant — elle prend juste plus de temps à se
## réaligner. C'est ce qui laisse au joueur une chance de la semer par un crochet.
static func steer(velocity: Vector2, from: Vector2, target: Vector2,
		turn_rate: float, delta: float) -> Vector2:
	var speed := velocity.length()
	if turn_rate <= 0.0 or speed <= MIN_STEERING_SPEED:
		return velocity
	var desired := target - from
	# ⚠️ Cible atteinte pile : `angle_to` sur un vecteur nul rend zéro, mais autant
	# le dire ici — une sangsue posée sur le joueur n'a plus de cap à corriger.
	if desired.length_squared() < 0.000001:
		return velocity
	var turn := clampf(velocity.angle_to(desired), -turn_rate * delta, turn_rate * delta)
	return velocity.rotated(turn)


## Vitesse de départ d'une unité qui apparaît en haut du champ : elle plonge vers le
## joueur, à son régime de croisière. Sans cap initial, `steer` n'aurait rien à
## faire tourner (norme nulle) et la sangsue resterait plantée à son point d'entrée.
static func initial_velocity(spawn: Vector2, target: Vector2, speed: float) -> Vector2:
	var toward := target - spawn
	if toward.length_squared() < 0.000001:
		return Vector2(0.0, -speed)
	return toward.normalized() * speed


## Le poursuivant a-t-il rattrapé sa proie ? Une distance, rien de plus — mais elle
## est ici pour que la règle vive au même endroit que la poursuite.
static func has_caught(from: Vector2, target: Vector2, reach: float) -> bool:
	return from.distance_squared_to(target) <= reach * reach
