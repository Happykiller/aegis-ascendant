class_name EnemyPath
## Trajectoires ennemies — mathématiques PURES : (temps, paramètres) -> position.
##
## Aucune dépendance à la scène, aucun état : instanciable et testable en headless
## (tests/unit/test_enemy_path.gd). Le contrôleur ne fait qu'échantillonner ces
## fonctions ; il ne décide de rien.
##
## Chaque trajectoire rend une position ABSOLUE, fonction du seul âge. Deux
## conséquences qu'on ne paie pas :
##   - la forme est identique quel que soit le pas de temps (rien ne s'accumule) ;
##   - un ennemi poolé qu'on réactive repart proprement de son spawn, sans traîner
##     l'état du précédent.
##
## RÈGLE DE VARIÉTÉ. Deux trajectoires doivent différer par leur *forme*, pas par
## leurs constantes. Une sinusoïde large et lente n'est pas un arc : c'est la même
## courbe avec d'autres nombres, et le joueur le voit. Chaque entrée ci-dessous a
## une signature de mouvement qu'aucune autre ne peut imiter :
##
##   WEAVE       oscillation douce      — la ligne de base, lisible
##   SERPENTINE  oscillation ANGULEUSE  — onde triangulaire : cassures nettes, lecture mécanique
##   ARC_CROSS   arc de cercle          — part vers le bas, s'incurve, TRAVERSE le champ
##   SPIRAL      cercle + descente      — orbite en descendant, occupe la profondeur
##   DIVE        accélération           — approche lente, puis il fond
##   HOVER_STRAFE  arrêt + strafe       — tient sa ligne et arrose : attaque télégraphiée
##   BOOMERANG   entrée puis RETRAITE   — repart vers le haut : à tuer avant qu'il file

## Vitesse latérale (unités/s) à laquelle le roulis visuel est à fond.
const BANK_REFERENCE_SPEED := 6.0

const DIVE_APPROACH_FACTOR := 0.35
const DIVE_ACCELERATION := 1.9
const STRAFE_RATE := 1.5
const STRAFE_WIDTH := 1.8
const DEPARTURE_FACTOR := 1.6
const RETREAT_FACTOR := 1.35


static func position_at(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	match data.path:
		EnemyData.Path.SERPENTINE:
			return _serpentine(data, age, spawn)
		EnemyData.Path.ARC_CROSS:
			return _arc_cross(data, age, spawn)
		EnemyData.Path.SPIRAL:
			return _spiral(data, age, spawn)
		EnemyData.Path.DIVE:
			return _dive(data, age, spawn)
		EnemyData.Path.HOVER_STRAFE:
			return _hover_strafe(data, age, spawn)
		EnemyData.Path.BOOMERANG:
			return _boomerang(data, age, spawn)
		_:
			return _weave(data, age, spawn)


## Le sens de virage se DÉDUIT du spawn : un ennemi apparu à gauche s'incurve vers
## la droite, donc vers le joueur et vers le centre du champ. Pas de paramètre à
## régler, pas d'erreur possible dans la donnée.
static func turn_direction(spawn: Vector2) -> float:
	return -1.0 if spawn.x > 0.0 else 1.0


## Descente régulière, oscillation sinusoïdale. La ligne de base : c'est elle qui
## apprend au joueur à lire un ennemi.
static func _weave(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	return Vector2(
		spawn.x + sin(age * data.weave_frequency * TAU) * data.weave_amplitude,
		spawn.y - data.move_speed * age)


## Même descente, mais l'oscillation est une onde TRIANGULAIRE : la trajectoire
## change de sens d'un coup, sans arrondi. Là où le weave ondule, celui-ci
## zigzague — et ça se lit immédiatement comme une autre machine.
static func _serpentine(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	var phase := age * data.weave_frequency
	# Onde triangulaire sur [-1, 1] : 4*|frac(u + 1/4) - 1/2| - 1
	var wave := 4.0 * absf(fposmod(phase + 0.25, 1.0) - 0.5) - 1.0
	return Vector2(
		spawn.x + wave * data.weave_amplitude,
		spawn.y - data.move_speed * age)


## Un VRAI arc de cercle, pas une sinusoïde déguisée. L'ennemi part droit vers le
## bas, puis sa vitesse tourne continûment : il finit par traverser le champ à
## l'horizontale. Le centre du cercle est posé sur le côté ; l'ennemi le parcourt à
## vitesse constante.
static func _arc_cross(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	var turn := turn_direction(spawn)
	var radius := maxf(data.arc_radius, 0.5)
	var angle := data.move_speed * age / radius
	var center := Vector2(spawn.x + turn * radius, spawn.y)
	return Vector2(
		center.x - turn * radius * cos(angle),
		center.y - radius * sin(angle))


## Le même cercle, mais l'ennemi continue de descendre pendant qu'il l'orbite :
## il vrille. Il occupe la profondeur au lieu de tomber dans un couloir.
static func _spiral(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	var turn := turn_direction(spawn)
	var radius := maxf(data.arc_radius, 0.5)
	var angle := age * data.weave_frequency * TAU
	return Vector2(
		spawn.x + turn * radius * sin(angle),
		spawn.y - radius * (1.0 - cos(angle)) * 0.35 - data.move_speed * age)


## Approche lente, puis accélération franche : l'ennemi « pique ». Le joueur a le
## temps de le voir venir avant qu'il ne fonde — menace lisible, pas coup de traître.
## La position est l'intégrale EXACTE de la vitesse, pas une accumulation par frame.
static func _dive(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	var approach := data.move_speed * DIVE_APPROACH_FACTOR
	var y: float
	var t := 0.0
	if age <= data.dive_delay:
		y = spawn.y - approach * age
	else:
		t = age - data.dive_delay
		var accel := data.move_speed * DIVE_ACCELERATION
		# v(t) = approach + accel*t  ->  distance = approach*t + accel*t^2/2
		y = spawn.y - approach * data.dive_delay - (approach * t + 0.5 * accel * t * t)
	# Le piqué n'est pas vertical : il glisse vers le centre, d'autant plus qu'il
	# accélère. Le déport suit la même parabole que la chute, donc la courbe est
	# lisse — pas un coude au moment du déclenchement.
	var lean := turn_direction(spawn) * data.weave_amplitude * (t * t) * 0.12
	return Vector2(spawn.x + lean, y)


## Trois temps : il descend, se STABILISE (c'est là qu'il tire — l'attaque est
## télégraphiée, le joueur peut la lire), strafe latéralement, puis décroche.
static func _hover_strafe(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	var descent_time := maxf((spawn.y - data.hold_y) / data.move_speed, 0.0)
	var strafe := sin(maxf(age - descent_time, 0.0) * data.weave_frequency * TAU * STRAFE_RATE) \
		* data.weave_amplitude * STRAFE_WIDTH
	var y: float
	if age <= descent_time:
		y = spawn.y - data.move_speed * age
	elif age <= descent_time + data.hold_time:
		y = data.hold_y # vol stationnaire : il tient sa ligne et tire
	else:
		y = data.hold_y - data.move_speed * DEPARTURE_FACTOR * (age - descent_time - data.hold_time)
	return Vector2(spawn.x + strafe, y)


## Il plonge, puis REPART par où il est venu. C'est le seul ennemi qui s'échappe :
## il faut le descendre pendant sa fenêtre basse, sinon il est perdu — et son score
## avec. Une pression de tempo, pas de danger.
static func _boomerang(data: EnemyData, age: float, spawn: Vector2) -> Vector2:
	var descent_time := maxf((spawn.y - data.hold_y) / data.move_speed, 0.0)
	var lateral := sin(age * data.weave_frequency * TAU) * data.weave_amplitude * 0.6
	var y: float
	if age <= descent_time:
		y = spawn.y - data.move_speed * age
	else:
		# Retraite : il remonte, et il repassera au-dessus de son point d'entrée.
		y = data.hold_y + data.move_speed * RETREAT_FACTOR * (age - descent_time)
	return Vector2(spawn.x + lateral, y)
