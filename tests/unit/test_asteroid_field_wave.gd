extends "res://tests/test_case.gd"
## La vague du champ d'astéroïdes (ADR-0027) — la traversée entre les deux boss.
##
## Ce que ce fichier garde n'est PAS un goût de level design : ce sont les trois
## choses qu'une retouche de timeline peut casser en silence.
##   1. la phase tient dans la fenêtre de durée décidée (45-60 s) ;
##   2. les trois unités du bestiaire y sont VRAIMENT — c'est la raison d'être
##      de la phase, et une entrée supprimée par mégarde ne se verrait nulle part ;
##   3. rien n'apparaît DANS le champ de jeu, sous le nez du joueur.

const FieldWave: WaveData = preload("res://resources/encounters/wave_asteroid_field_01.tres")

const MineScene := "res://scenes/enemies/choir_mine.tscn"
const MawScene := "res://scenes/enemies/null_maw.tscn"
const LeechScene := "res://scenes/enemies/leech_drone.tscn"
const CarrierScene := "res://scenes/enemies/shield_carrier.tscn"

## Durée décidée avec l'opérateur le 2026-08-25 : la traversée fait respirer entre
## deux boss sans creuser un ventre mou. Le boss final dure ~40 s.
const PHASE_MIN_SECONDS := 45.0
const PHASE_MAX_SECONDS := 60.0

## Ce qu'une unité qui dérive met à traverser le champ sans être touchée : de son
## point d'entrée jusqu'à la ligne de despawn, à sa propre vitesse. C'est ce trajet,
## et non le dernier spawn, qui décide de la durée réelle de la phase.
func _drift_crossing_seconds(spawn_y: float, speed: float) -> float:
	var exit_y := GameplayPlane.BOUNDS.position.y - EnemyController.DESPAWN_MARGIN
	return (spawn_y - exit_y) / speed

func _scene_paths() -> Dictionary:
	var counts := {}
	for entry in FieldWave.entries:
		var path := entry.enemy_scene.resource_path
		counts[path] = int(counts.get(path, 0)) + entry.count
	return counts

func test_the_wave_is_valid() -> void:
	var errors := FieldWave.validate()
	assert_true(errors.is_empty(), "vague valide (%s)" % ", ".join(errors))

func test_it_plays_the_three_units_the_bestiary_had_left_unused() -> void:
	# Choir Mine, Null Maw et Leech Drone étaient livrées, testées et au codex — et
	# n'apparaissaient dans AUCUNE rencontre. C'est la moitié de la raison d'être de
	# cette phase (plan du 2026-08-25, point 3.1 du plan bestiaire).
	var counts := _scene_paths()
	assert_true(int(counts.get(MineScene, 0)) > 0, "la Choir Mine entre en jeu")
	assert_true(int(counts.get(MawScene, 0)) > 0, "la Null Maw entre en jeu")
	assert_true(int(counts.get(LeechScene, 0)) > 0, "la Leech Drone entre en jeu")
	assert_eq(counts.size(), 4, "et rien d'autre : la phase est celle du nouveau bestiaire")

func test_the_shield_carrier_teaches_before_it_is_exploited() -> void:
	# ⚠️ PREMIÈRE APPARITION DANS TOUT LE JEU. Le genre est explicite : un mécanisme
	# s'installe SEUL avant d'être combiné. Deux porteurs, pas plus — le premier pour
	# comprendre, le second pour payer le détour — et le premier arrive bien avant le
	# rideau de mines, sinon la leçon se donne au pire moment.
	var counts := _scene_paths()
	assert_eq(int(counts.get(CarrierScene, 0)), 2, "deux porteurs, pas un essaim")
	var times: Array[float] = []
	for entry in FieldWave.entries:
		if entry.enemy_scene.resource_path == CarrierScene:
			times.append(entry.time_offset)
	times.sort()
	assert_true(times[0] < 20.0, "le premier enseigne tôt (%.1f s)" % times[0])
	assert_true(times[1] - times[0] >= 10.0,
		"et le second est loin derrière (%.1f s d'écart)" % (times[1] - times[0]))

func test_the_phase_lasts_as_long_as_it_was_decided_to() -> void:
	# Borne HAUTE : le pire cas, celui du joueur qui ne détruit rien. La vague ne se
	# clôt qu'une fois le dernier ennemi sorti du champ, pas au dernier spawn.
	var mine: EnemyData = load("res://resources/enemies/choir_mine.tres")
	var maw: EnemyData = load("res://resources/enemies/null_maw.tres")
	var worst := 0.0
	var last_spawn := 0.0
	for entry in FieldWave.entries:
		var end_of_entry := entry.time_offset + (entry.count - 1) * entry.spacing
		last_spawn = maxf(last_spawn, end_of_entry)
		var path := entry.enemy_scene.resource_path
		if path == MineScene or path == MawScene:
			var speed := mine.move_speed if path == MineScene else maw.move_speed
			worst = maxf(worst, end_of_entry
				+ _drift_crossing_seconds(entry.spawn_plane_position.y, speed))
	assert_true(worst <= PHASE_MAX_SECONDS,
		"pire cas %.1f s <= %.0f s" % [worst, PHASE_MAX_SECONDS])
	assert_true(worst >= PHASE_MIN_SECONDS,
		"pire cas %.1f s >= %.0f s" % [worst, PHASE_MIN_SECONDS])
	# Et la borne BASSE, celle du joueur qui nettoie tout : elle ne doit pas non plus
	# expédier la traversée en vingt secondes.
	assert_true(last_spawn >= 35.0, "dernier spawn à %.1f s" % last_spawn)

func test_nothing_spawns_inside_the_play_area() -> void:
	# Une unité qui apparaît sous le nez du joueur n'est pas une menace, c'est une
	# injustice : il n'a rien pu lire venir.
	for entry in FieldWave.entries:
		var spawn := entry.spawn_plane_position
		assert_true(spawn.y > GameplayPlane.BOUNDS.end.y,
			"entrée par le haut (y = %.1f)" % spawn.y)
		assert_true(absf(spawn.x) <= GameplayPlane.BOUNDS.end.x,
			"colonne dans le champ (x = %.1f)" % spawn.x)

func test_the_schedule_is_what_the_spawner_will_preallocate() -> void:
	# Le pool est construit au montage, une fois, depuis ce planning : sa taille est
	# donc une donnée de perf autant que de rythme.
	var schedule := WaveSpawner.build_schedule(FieldWave)
	var times: PackedFloat32Array = schedule["times"]
	assert_eq(times.size(), FieldWave.total_enemy_count(), "un spawn par ennemi")
	for i in times.size() - 1:
		assert_true(times[i] <= times[i + 1], "planning trié (index %d)" % i)
