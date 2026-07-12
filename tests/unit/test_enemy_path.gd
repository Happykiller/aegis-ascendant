extends "res://tests/test_case.gd"
## Trajectoires ennemies (EnemyPath) — mathématiques pures, testées sans scène.

const SPAWN := Vector2(3.0, 8.0)

func _data(path: int) -> EnemyData:
	var data := EnemyData.new()
	data.path = path
	data.move_speed = 4.0
	data.weave_amplitude = 1.5
	data.weave_frequency = 0.4
	data.hold_y = 3.0
	data.hold_time = 2.0
	data.dive_delay = 1.0
	return data

## Le contrat commun : quelle que soit la trajectoire, on part du point de spawn.
## C'est ce qui rend le pooling sûr — un ennemi réactivé ne traîne pas l'état du
## précédent, puisque sa position ne dépend que de son âge et de son spawn.
func test_every_path_starts_at_the_spawn_point() -> void:
	for path in [EnemyData.Path.WEAVE, EnemyData.Path.DIVE,
			EnemyData.Path.ARC_SWEEP, EnemyData.Path.HOVER_STRAFE]:
		var start := EnemyPath.position_at(_data(path), 0.0, SPAWN)
		assert_true(start.distance_to(SPAWN) < 0.001,
			"trajectoire %d démarre au spawn (obtenu %s)" % [path, start])

func test_every_path_travels_down_the_screen() -> void:
	for path in [EnemyData.Path.WEAVE, EnemyData.Path.DIVE,
			EnemyData.Path.ARC_SWEEP, EnemyData.Path.HOVER_STRAFE]:
		var later := EnemyPath.position_at(_data(path), 6.0, SPAWN)
		assert_true(later.y < SPAWN.y,
			"trajectoire %d descend (y=%f vs spawn %f)" % [path, later.y, SPAWN.y])

func test_weave_oscillates_around_its_spawn_column() -> void:
	var data := _data(EnemyData.Path.WEAVE)
	var quarter := 0.25 / data.weave_frequency # premier sommet de la sinusoïde
	var peak := EnemyPath.position_at(data, quarter, SPAWN)
	assert_almost_eq(peak.x - SPAWN.x, data.weave_amplitude, 0.01,
		"le zigzag atteint son amplitude")

## Le piqué doit ACCÉLÉRER : c'est toute sa raison d'être. Sans ça, ce n'est qu'une
## descente lente de plus.
func test_dive_accelerates_after_its_approach() -> void:
	var data := _data(EnemyData.Path.DIVE)
	var approach := SPAWN.y - EnemyPath.position_at(data, data.dive_delay, SPAWN).y
	var first := EnemyPath.position_at(data, data.dive_delay + 1.0, SPAWN).y
	var second := EnemyPath.position_at(data, data.dive_delay + 2.0, SPAWN).y
	var step_one := EnemyPath.position_at(data, data.dive_delay, SPAWN).y - first
	var step_two := first - second
	assert_true(approach < data.move_speed * data.dive_delay,
		"l'approche est plus lente que la vitesse nominale")
	assert_true(step_two > step_one * 1.2,
		"la seconde seconde de piqué couvre bien plus que la première (%f vs %f)"
			% [step_two, step_one])

func test_arc_sweep_crosses_further_than_a_weave() -> void:
	var arc := _data(EnemyData.Path.ARC_SWEEP)
	var widest := 0.0
	for i in 200:
		var offset: float = absf(EnemyPath.position_at(arc, i * 0.05, SPAWN).x - SPAWN.x)
		widest = maxf(widest, offset)
	assert_true(widest > arc.weave_amplitude * 2.0,
		"l'arc balaie bien plus large que le zigzag (%f)" % widest)

## Le vol stationnaire est la fenêtre où l'ennemi tire : elle doit exister, et tenir.
func test_hover_holds_its_line_then_leaves() -> void:
	var data := _data(EnemyData.Path.HOVER_STRAFE)
	var descent := (SPAWN.y - data.hold_y) / data.move_speed
	var early := EnemyPath.position_at(data, descent + 0.2, SPAWN)
	var late := EnemyPath.position_at(data, descent + data.hold_time - 0.2, SPAWN)
	assert_almost_eq(early.y, data.hold_y, 0.001, "il se stabilise sur sa ligne")
	assert_almost_eq(late.y, data.hold_y, 0.001, "et la tient toute la durée du hold")
	var after := EnemyPath.position_at(data, descent + data.hold_time + 1.0, SPAWN)
	assert_true(after.y < data.hold_y - 1.0, "puis il décroche vers le bas")

func test_hover_strafes_sideways_while_holding() -> void:
	var data := _data(EnemyData.Path.HOVER_STRAFE)
	var descent := (SPAWN.y - data.hold_y) / data.move_speed
	var widest := 0.0
	for i in 40:
		var t: float = descent + i * (data.hold_time / 40.0)
		widest = maxf(widest, absf(EnemyPath.position_at(data, t, SPAWN).x - SPAWN.x))
	assert_true(widest > 0.5, "il strafe pendant le hold au lieu de rester figé (%f)" % widest)

## Une trajectoire est une FONCTION du temps, pas une accumulation : deux échantillons
## au même âge doivent coïncider, quel que soit le chemin parcouru pour y arriver.
## C'est ce qui la rend indépendante du pas de temps.
func test_paths_are_deterministic_in_time() -> void:
	for path in [EnemyData.Path.WEAVE, EnemyData.Path.DIVE,
			EnemyData.Path.ARC_SWEEP, EnemyData.Path.HOVER_STRAFE]:
		var data := _data(path)
		var a := EnemyPath.position_at(data, 3.7, SPAWN)
		var b := EnemyPath.position_at(data, 3.7, SPAWN)
		assert_true(a.distance_to(b) < 0.0001, "trajectoire %d est déterministe" % path)
