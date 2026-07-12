extends "res://tests/test_case.gd"
## GameplayPlane projections and bounds (spec §28.2).

# GameplayPlane is a global class (class_name), resolved via the class cache.

func test_round_trip_projection() -> void:
	var p := Vector2(3.5, -2.25)
	assert_eq(GameplayPlane.to_plane(GameplayPlane.to_world(p)), p, "to_plane(to_world(p)) == p")

func test_axis_convention() -> void:
	# Logical "up" (+y) must be world -Z; logical +x stays world +X.
	var w := GameplayPlane.to_world(Vector2(2.0, 5.0))
	assert_almost_eq(w.x, 2.0, 0.0001, "logical +x -> world +X")
	assert_almost_eq(w.y, 0.0, 0.0001, "plane lives at Y=0")
	assert_almost_eq(w.z, -5.0, 0.0001, "logical +y -> world -Z")

func test_up_input_moves_up_the_screen() -> void:
	# Input.get_vector reports a held "move_up" as y = -1 (screen space is down-positive).
	var plane := GameplayPlane.from_input(Vector2(0.0, -1.0))
	assert_true(plane.y > 0.0, "pressing up yields a positive (upward) plane y")
	assert_true(GameplayPlane.to_world(plane).z < 0.0, "and maps to world -Z, up the screen")

func test_down_input_moves_down_the_screen() -> void:
	var plane := GameplayPlane.from_input(Vector2(0.0, 1.0))
	assert_true(plane.y < 0.0, "pressing down yields a negative (downward) plane y")
	assert_true(GameplayPlane.to_world(plane).z > 0.0, "and maps to world +Z, down the screen")

func test_input_horizontal_axis_is_untouched() -> void:
	assert_almost_eq(GameplayPlane.from_input(Vector2(1.0, 0.0)).x, 1.0, 0.0001, "right stays right")
	assert_almost_eq(GameplayPlane.from_input(Vector2(-1.0, 0.0)).x, -1.0, 0.0001, "left stays left")

func test_input_magnitude_is_preserved() -> void:
	var raw := Vector2(0.6, -0.8) # already deadzoned/normalized by Input.get_vector
	assert_almost_eq(GameplayPlane.from_input(raw).length(), raw.length(), 0.0001,
		"flipping the axis never changes the requested speed")

func test_clamp_inside_is_identity() -> void:
	var p := Vector2(1.0, 1.0)
	assert_eq(GameplayPlane.clamp_to_bounds(p), p, "inside point unchanged")

func test_clamp_outside_lands_on_edge() -> void:
	var clamped := GameplayPlane.clamp_to_bounds(Vector2(100.0, -100.0))
	assert_almost_eq(clamped.x, GameplayPlane.BOUNDS.end.x, 0.0001, "x clamped to right edge")
	assert_almost_eq(clamped.y, GameplayPlane.BOUNDS.position.y, 0.0001, "y clamped to bottom edge")

func test_is_inside_with_margin() -> void:
	var outside := Vector2(GameplayPlane.BOUNDS.end.x + 1.0, 0.0)
	assert_false(GameplayPlane.is_inside(outside), "1 unit out is outside")
	assert_true(GameplayPlane.is_inside(outside, 2.0), "but inside with margin 2")
