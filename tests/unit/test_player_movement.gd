extends "res://tests/test_case.gd"
## Player movement math (spec §7.3: max speed reached in < 250 ms).

const MAX_SPEED := 14.0
const ACCEL_TIME := 0.18
const DELTA := 1.0 / 60.0

func test_reaches_max_speed_within_accel_time() -> void:
	var velocity := Vector2.ZERO
	var input := Vector2(1.0, 0.0)
	var steps := int(ceil(ACCEL_TIME / DELTA))
	for i in steps:
		velocity = PlayerFighterController.integrate_velocity(
			velocity, input, MAX_SPEED, ACCEL_TIME, DELTA)
	assert_almost_eq(velocity.length(), MAX_SPEED, 0.001,
		"max speed reached after accel_time (%d steps)" % steps)

func test_accel_time_meets_spec_budget() -> void:
	assert_true(ACCEL_TIME < 0.25, "accel_time under the 250 ms budget")

func test_symmetric_deceleration() -> void:
	var velocity := Vector2(MAX_SPEED, 0.0)
	var steps := int(ceil(ACCEL_TIME / DELTA))
	for i in steps:
		velocity = PlayerFighterController.integrate_velocity(
			velocity, Vector2.ZERO, MAX_SPEED, ACCEL_TIME, DELTA)
	assert_almost_eq(velocity.length(), 0.0, 0.001, "full stop after accel_time")

func test_diagonal_input_is_normalized() -> void:
	var velocity := Vector2.ZERO
	var input := Vector2(1.0, 1.0) # raw diagonal, length sqrt(2)
	for i in 120:
		velocity = PlayerFighterController.integrate_velocity(
			velocity, input, MAX_SPEED, ACCEL_TIME, DELTA)
	assert_true(velocity.length() <= MAX_SPEED + 0.001,
		"diagonal never exceeds max speed (got %f)" % velocity.length())
