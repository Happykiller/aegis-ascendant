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
