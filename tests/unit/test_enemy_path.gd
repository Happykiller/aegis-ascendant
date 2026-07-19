extends "res://tests/test_case.gd"
## Trajectoires ennemies (EnemyPath) — mathématiques pures, testées sans scène.

const SPAWN := Vector2(-4.0, 9.0)
const ALL_PATHS: Array[int] = [
	EnemyData.Path.WEAVE, EnemyData.Path.DIVE, EnemyData.Path.ARC_CROSS,
	EnemyData.Path.HOVER_STRAFE, EnemyData.Path.SERPENTINE, EnemyData.Path.SPIRAL,
	EnemyData.Path.BOOMERANG, EnemyData.Path.STRAFE_RUN,
]

func _data(path: int) -> EnemyData:
	var data := EnemyData.new()
	data.path = path
	data.move_speed = 4.0
	data.weave_amplitude = 1.5
	data.weave_frequency = 0.4
	data.hold_y = 3.0
	data.hold_time = 2.0
	data.dive_delay = 1.0
	data.arc_radius = 7.0
	return data

## Contrat commun : quelle que soit la trajectoire, on part du point de spawn.
## C'est ce qui rend le pooling sûr — un ennemi réactivé ne traîne pas l'état du
## précédent, puisque sa position ne dépend que de son âge et de son spawn.
func test_every_path_starts_at_the_spawn_point() -> void:
	for path in ALL_PATHS:
		var start := EnemyPath.position_at(_data(path), 0.0, SPAWN)
		assert_true(start.distance_to(SPAWN) < 0.001,
			"trajectoire %d démarre au spawn (obtenu %s)" % [path, start])

## Une trajectoire est une FONCTION du temps, pas une accumulation : même âge,
## même position. C'est ce qui la rend indépendante du pas de temps.
func test_every_path_is_deterministic_in_time() -> void:
	for path in ALL_PATHS:
		var data := _data(path)
		var a := EnemyPath.position_at(data, 3.7, SPAWN)
		var b := EnemyPath.position_at(data, 3.7, SPAWN)
		assert_true(a.distance_to(b) < 0.0001, "trajectoire %d est déterministe" % path)

## Tout le monde entre dans le champ. Le BOOMERANG est le seul à en ressortir par
## le haut : il est traité à part, plus bas.
func test_every_path_enters_the_field() -> void:
	for path in ALL_PATHS:
		var descended := false
		for i in 60:
			if EnemyPath.position_at(_data(path), i * 0.1, SPAWN).y < SPAWN.y - 1.0:
				descended = true
				break
		assert_true(descended, "trajectoire %d entre bien dans le champ" % path)

# --- La règle de variété -----------------------------------------------------
#
# Le vrai piège de ce fichier : une sinusoïde large et lente N'EST PAS un arc.
# C'est la même courbe avec d'autres constantes, et le joueur le voit. Un premier
# jet avait exactement ce défaut — quatre « trajectoires » dont deux étaient la
# même fonction. Ce test l'aurait attrapé.

## Deux trajectoires distinctes doivent produire des CHEMINS distincts, échantillon
## par échantillon. Si deux d'entre elles se ressemblent à moins d'une demi-unité
## sur toute leur durée, ce ne sont pas deux comportements : c'est un seul, réglé
## deux fois.
func test_no_two_paths_trace_the_same_shape() -> void:
	var samples: Dictionary = {}
	for path in ALL_PATHS:
		var points: Array[Vector2] = []
		for i in 40:
			points.append(EnemyPath.position_at(_data(path), i * 0.15, SPAWN))
		samples[path] = points
	for a in ALL_PATHS:
		for b in ALL_PATHS:
			if a >= b:
				continue
			var worst := 0.0
			for i in 40:
				worst = maxf(worst, samples[a][i].distance_to(samples[b][i]))
			assert_true(worst > 0.5,
				"trajectoires %d et %d sont la même forme (écart max %f)" % [a, b, worst])

## Le weave ondule, le serpentin CASSE. La différence se mesure : sur une onde
## triangulaire, la vitesse latérale est constante par morceaux — donc son
## accélération est nulle partout, sauf aux sommets. Sur une sinusoïde, elle ne
## l'est jamais.
func test_serpentine_is_angular_where_weave_is_smooth() -> void:
	var serp := _data(EnemyData.Path.SERPENTINE)
	var wv := _data(EnemyData.Path.WEAVE)
	var serp_curvature := 0.0
	var weave_curvature := 0.0
	for i in 60:
		var t := 0.8 + i * 0.01 # loin des sommets du triangle
		serp_curvature += absf(_second_difference(serp, t))
		weave_curvature += absf(_second_difference(wv, t))
	assert_true(serp_curvature < weave_curvature * 0.5,
		"le serpentin est droit entre ses cassures, la sinusoïde courbe partout (%f vs %f)"
			% [serp_curvature, weave_curvature])

func _second_difference(data: EnemyData, t: float) -> float:
	var h := 0.02
	var a := EnemyPath.position_at(data, t - h, SPAWN).x
	var b := EnemyPath.position_at(data, t, SPAWN).x
	var c := EnemyPath.position_at(data, t + h, SPAWN).x
	return (a - 2.0 * b + c) / (h * h)

# --- Signature propre à chaque trajectoire -----------------------------------

func test_weave_oscillates_around_its_spawn_column() -> void:
	var data := _data(EnemyData.Path.WEAVE)
	var peak := EnemyPath.position_at(data, 0.25 / data.weave_frequency, SPAWN)
	assert_almost_eq(peak.x - SPAWN.x, data.weave_amplitude, 0.01,
		"le zigzag atteint son amplitude")

## Le piqué doit ACCÉLÉRER : c'est toute sa raison d'être.
func test_dive_accelerates_after_its_approach() -> void:
	var data := _data(EnemyData.Path.DIVE)
	var at_delay := EnemyPath.position_at(data, data.dive_delay, SPAWN).y
	var first := EnemyPath.position_at(data, data.dive_delay + 1.0, SPAWN).y
	var second := EnemyPath.position_at(data, data.dive_delay + 2.0, SPAWN).y
	assert_true(SPAWN.y - at_delay < data.move_speed * data.dive_delay,
		"l'approche est plus lente que la vitesse nominale")
	assert_true((first - second) > (at_delay - first) * 1.2,
		"la seconde seconde de piqué couvre bien plus que la première")

## L'arc doit TRAVERSER : il finit sa course loin de sa colonne de départ, et il
## s'incurve vers le centre (un ennemi né à gauche part vers la droite).
func test_arc_cross_actually_crosses_the_field() -> void:
	var data := _data(EnemyData.Path.ARC_CROSS)
	var quarter_turn := data.arc_radius * (PI * 0.5) / data.move_speed
	var landed := EnemyPath.position_at(data, quarter_turn, SPAWN)
	assert_true(landed.x - SPAWN.x > data.arc_radius * 0.8,
		"après un quart de tour il a traversé vers le centre (dx=%f)" % (landed.x - SPAWN.x))
	assert_true(absf(landed.y - (SPAWN.y - data.arc_radius)) < 0.5,
		"et il est descendu d'un rayon")

func test_arc_turns_toward_the_centre_from_either_side() -> void:
	var data := _data(EnemyData.Path.ARC_CROSS)
	assert_true(EnemyPath.turn_direction(Vector2(-6.0, 9.0)) > 0.0, "né à gauche -> vire à droite")
	assert_true(EnemyPath.turn_direction(Vector2(6.0, 9.0)) < 0.0, "né à droite -> vire à gauche")

func test_spiral_orbits_while_it_descends() -> void:
	var data := _data(EnemyData.Path.SPIRAL)
	var swings := 0
	var previous := 0.0
	for i in 80:
		var offset := EnemyPath.position_at(data, i * 0.15, SPAWN).x - SPAWN.x
		if signf(offset) != signf(previous) and absf(offset) > 0.2:
			swings += 1
		previous = offset
	assert_true(swings >= 2, "il orbite (traverse sa colonne plusieurs fois)")
	assert_true(EnemyPath.position_at(data, 6.0, SPAWN).y < SPAWN.y - 10.0,
		"tout en descendant pour de bon")

## Le vol stationnaire est la fenêtre où l'ennemi tire : elle doit exister, et tenir.
func test_hover_holds_its_line_then_leaves() -> void:
	var data := _data(EnemyData.Path.HOVER_STRAFE)
	var descent := (SPAWN.y - data.hold_y) / data.move_speed
	assert_almost_eq(EnemyPath.position_at(data, descent + 0.2, SPAWN).y, data.hold_y, 0.001,
		"il se stabilise sur sa ligne")
	assert_almost_eq(EnemyPath.position_at(data, descent + data.hold_time - 0.2, SPAWN).y,
		data.hold_y, 0.001, "et la tient toute la durée du hold")
	assert_true(EnemyPath.position_at(data, descent + data.hold_time + 1.0, SPAWN).y
		< data.hold_y - 1.0, "puis il décroche vers le bas")

## Le boomerang est le seul à s'échapper : il doit repasser AU-DESSUS de son entrée,
## sinon il ne s'échappe pas et le contrôleur ne le désactivera jamais.
func test_boomerang_retreats_back_off_the_top() -> void:
	var data := _data(EnemyData.Path.BOOMERANG)
	var descent := (SPAWN.y - data.hold_y) / data.move_speed
	assert_almost_eq(EnemyPath.position_at(data, descent, SPAWN).y, data.hold_y, 0.01,
		"il descend jusqu'à sa ligne de demi-tour")
	var far := EnemyPath.position_at(data, descent + 6.0, SPAWN).y
	assert_true(far > SPAWN.y,
		"puis il remonte au-delà de son point d'entrée (y=%f vs spawn %f)" % [far, SPAWN.y])
