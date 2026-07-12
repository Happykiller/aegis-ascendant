class_name EnemyPath
## Trajectoires ennemies — mathématiques PURES : (temps, paramètres) -> position.
##
## Aucune dépendance à la scène, aucun état : instanciable et testable en headless
## (tests/unit/test_enemy_path.gd). Le contrôleur ne fait qu'échantillonner ces
## fonctions ; il ne décide de rien.
##
## Avant, tout ennemi descendait à vitesse constante avec une sinusoïde en x — et
## c'était tout ce qu'il savait faire. D'où l'impression de linéarité : elle était
## littérale. Chaque trajectoire ci-dessous est choisie par la Resource EnemyData,
## jamais codée en dur dans un contrôleur.
##
## Toutes rendent une position ABSOLUE sur le plan, fonction du seul âge : un
## ennemi poolé qu'on réactive repart donc proprement de son point de spawn, sans
## traîner l'état du précédent.

## Vitesse latérale (unités/s) à laquelle le roulis visuel est à fond.
const BANK_REFERENCE_SPEED := 6.0


static func position_at(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	match data.path:
		EnemyData.Path.DIVE:
			return _dive(data, age, spawn)
		EnemyData.Path.ARC_SWEEP:
			return _arc_sweep(data, age, spawn)
		EnemyData.Path.HOVER_STRAFE:
			return _hover_strafe(data, age, spawn)
		_:
			return _weave(data, age, spawn)


## Descente régulière, zigzag sinusoïdal. La trajectoire historique du Needle
## Scout : conservée telle quelle, elle reste la ligne de base lisible.
static func _weave(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	return Vector2(
		spawn.x + sin(age * data.weave_frequency * TAU) * data.weave_amplitude,
		spawn.y - data.move_speed * age)


## Approche lente, puis accélération franche : l'ennemi « pique ». Le joueur a le
## temps de le voir venir avant qu'il ne fonde — c'est une menace lisible, pas un
## coup de traître.
##
## La position est l'intégrale exacte de la vitesse, pas une accumulation frame par
## frame : la trajectoire est donc identique quel que soit le pas de temps.
static func _dive(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	var approach := data.move_speed * DIVE_APPROACH_FACTOR
	var y: float
	if age <= data.dive_delay:
		y = spawn.y - approach * age
	else:
		var t := age - data.dive_delay
		# v(t) = approach + accel * t  ->  distance = approach*t + accel*t^2/2
		var accel := data.move_speed * DIVE_ACCELERATION
		y = spawn.y - approach * data.dive_delay - (approach * t + 0.5 * accel * t * t)
	# Une inclinaison latérale constante : le piqué n'est pas vertical, il glisse.
	var lean := data.weave_amplitude * DIVE_LEAN * minf(age, data.dive_delay + 1.0)
	return Vector2(spawn.x + lean, y)

const DIVE_APPROACH_FACTOR := 0.35
const DIVE_ACCELERATION := 1.7
const DIVE_LEAN := 0.35


## Descente lente et large balayage horizontal : l'ennemi traverse le champ au lieu
## de tomber dans son couloir. Casse les colonnes verticales que le weave produit.
static func _arc_sweep(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	return Vector2(
		spawn.x + sin(age * data.weave_frequency * TAU * ARC_RATE) * data.weave_amplitude * ARC_WIDTH,
		spawn.y - data.move_speed * ARC_DESCENT * age)

const ARC_RATE := 0.35
const ARC_WIDTH := 3.0
const ARC_DESCENT := 0.55


## Trois temps : l'ennemi descend, se STABILISE (c'est là qu'il tire — l'attaque est
## télégraphiée, le joueur peut la lire), strafe latéralement, puis décroche.
static func _hover_strafe(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	var descent_time := maxf((spawn.y - data.hold_y) / data.move_speed, 0.0)
	var strafe := sin(maxf(age - descent_time, 0.0) * data.weave_frequency * TAU * STRAFE_RATE) \
		* data.weave_amplitude * STRAFE_WIDTH
	var y: float
	if age <= descent_time:
		y = spawn.y - data.move_speed * age
	elif age <= descent_time + data.hold_time:
		y = data.hold_y # en vol stationnaire : il tient sa ligne et tire
	else:
		y = data.hold_y - data.move_speed * DEPARTURE_FACTOR * (age - descent_time - data.hold_time)
	return Vector2(spawn.x + strafe, y)

const STRAFE_RATE := 1.5
const STRAFE_WIDTH := 1.8
const DEPARTURE_FACTOR := 1.6
