extends "res://tests/test_case.gd"
## BossMovement: pure shape functions that escalate per phase (spec §12). No node,
## no state — the boss's motion is decided here and can be checked headless.

func _base() -> Vector2:
	return Vector2(0.0, 7.0)

func test_pattern_escalates_with_phase() -> void:
	assert_eq(BossMovement.pattern_for_phase(0, 1), BossMovement.Pattern.FIGURE_EIGHT,
		"a one-phase boss still moves lively, not a flat sway")
	assert_eq(BossMovement.pattern_for_phase(0, 4), BossMovement.Pattern.SWAY, "phase 0 = sway")
	assert_eq(BossMovement.pattern_for_phase(1, 4), BossMovement.Pattern.FIGURE_EIGHT, "phase 1 = figure eight")
	assert_eq(BossMovement.pattern_for_phase(2, 4), BossMovement.Pattern.ORBIT, "phase 2 = orbit")
	assert_eq(BossMovement.pattern_for_phase(3, 4), BossMovement.Pattern.CHARGE_RETREAT, "final phase charges")

func test_shapes_start_at_the_anchor() -> void:
	var b := _base()
	for pattern in [BossMovement.Pattern.SWAY, BossMovement.Pattern.FIGURE_EIGHT,
			BossMovement.Pattern.CHARGE_RETREAT]:
		var p := BossMovement.position_at(pattern, 0.0, b, 5.0, 1.8, 0.22)
		assert_almost_eq(p.x, b.x, 0.001, "x starts at the anchor")
		assert_almost_eq(p.y, b.y, 0.001, "y starts at the anchor")

func test_shapes_stay_within_amplitude() -> void:
	var b := _base()
	var amp_x := 5.0
	var amp_y := 1.8
	for pattern in [BossMovement.Pattern.SWAY, BossMovement.Pattern.FIGURE_EIGHT,
			BossMovement.Pattern.ORBIT, BossMovement.Pattern.CHARGE_RETREAT]:
		for step in 40:
			var p := BossMovement.position_at(pattern, step * 0.25, b, amp_x, amp_y, 0.22)
			assert_true(absf(p.x - b.x) <= amp_x + 0.001, "x within lateral amplitude")
			assert_true(p.y <= b.y + amp_y + 0.001 and p.y >= b.y - amp_y * 2.2 - 0.001,
				"y within its vertical range")

func test_pure_and_deterministic() -> void:
	var b := _base()
	var a := BossMovement.position_at(BossMovement.Pattern.ORBIT, 1.3, b, 5.0, 1.8, 0.22)
	var c := BossMovement.position_at(BossMovement.Pattern.ORBIT, 1.3, b, 5.0, 1.8, 0.22)
	assert_eq(a, c, "same inputs -> same output")

func test_patterns_are_distinct_shapes() -> void:
	var b := _base()
	var sway := BossMovement.position_at(BossMovement.Pattern.SWAY, 1.0, b, 5.0, 1.8, 0.22)
	var orbit := BossMovement.position_at(BossMovement.Pattern.ORBIT, 1.0, b, 5.0, 1.8, 0.22)
	assert_true(sway.distance_to(orbit) > 0.5, "sway and orbit trace different shapes")
