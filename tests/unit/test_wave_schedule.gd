extends "res://tests/test_case.gd"
## WaveSpawner scheduling math (pure, headless).

func _make_entry(time_offset: float, count: int, spacing: float, x: float) -> WaveEntry:
	var entry := WaveEntry.new()
	entry.time_offset = time_offset
	entry.count = count
	entry.spacing = spacing
	entry.spawn_plane_position = Vector2(x, 8.5)
	return entry

func test_schedule_flattens_and_sorts() -> void:
	var wave := WaveData.new()
	# Deliberately out of order: second entry fires first.
	wave.entries = [_make_entry(5.0, 2, 1.0, -3.0), _make_entry(0.5, 3, 0.5, 3.0)]
	var schedule := WaveSpawner.build_schedule(wave)
	var times: PackedFloat32Array = schedule["times"]
	assert_eq(times.size(), 5, "one event per enemy")
	for i in times.size() - 1:
		assert_true(times[i] <= times[i + 1], "times sorted (index %d)" % i)
	assert_almost_eq(times[0], 0.5, 0.0001, "earliest event first")
	assert_almost_eq(times[times.size() - 1], 6.0, 0.0001, "latest = 5.0 + 1*1.0")

func test_schedule_positions_follow_entries() -> void:
	var wave := WaveData.new()
	wave.entries = [_make_entry(0.0, 2, 1.0, -7.0)]
	var schedule := WaveSpawner.build_schedule(wave)
	var positions: PackedVector2Array = schedule["positions"]
	assert_eq(positions.size(), 2, "two spawns")
	assert_almost_eq(positions[0].x, -7.0, 0.0001, "entry position used")

func test_wave_data_validation() -> void:
	var wave := WaveData.new()
	assert_false(wave.validate().is_empty(), "empty wave rejected")
	wave.entries = [_make_entry(0.0, 3, 0.5, 0.0)]
	assert_true(wave.validate().size() == 1, "only missing enemy_scene remains")
	assert_eq(wave.total_enemy_count(), 3, "total count")
