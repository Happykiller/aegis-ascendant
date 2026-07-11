extends "res://tests/test_case.gd"
## PlayerShield: damage, invulnerability, regen, depletion (spec §8.3).

func _make() -> PlayerShield:
	var s := PlayerShield.new()
	s.configure(100.0, 3.0, 12.0, 1.2)
	return s

func test_hit_reduces_shield() -> void:
	var s := _make()
	assert_true(s.take_hit(25.0), "hit lands")
	assert_almost_eq(s.current, 75.0, 0.001, "shield reduced")

func test_invulnerability_blocks_second_hit() -> void:
	var s := _make()
	s.take_hit(25.0)
	assert_true(s.is_invulnerable(), "invuln granted after hit")
	assert_false(s.take_hit(25.0), "second hit blocked by invuln")
	assert_almost_eq(s.current, 75.0, 0.001, "shield unchanged during invuln")

func test_invulnerability_expires() -> void:
	var s := _make()
	s.take_hit(25.0)
	s.tick(1.3) # past the 1.2s invuln window
	assert_false(s.is_invulnerable(), "invuln expired")
	assert_true(s.take_hit(10.0), "hit lands again")

func test_no_regen_before_delay() -> void:
	var s := _make()
	s.take_hit(40.0)
	s.tick(2.0) # under the 3s regen delay
	assert_almost_eq(s.current, 60.0, 0.001, "no regen yet")

func test_regen_after_delay() -> void:
	var s := _make()
	s.take_hit(40.0)
	s.tick(3.0) # reach the delay (no regen this tick, boundary)
	s.tick(1.0) # +12 units
	assert_true(s.current > 60.0, "shield regenerated (got %f)" % s.current)
	assert_true(s.current <= 100.0, "never exceeds max")

func test_depletion() -> void:
	var s := _make()
	s.take_hit(100.0)
	assert_true(s.is_depleted(), "depleted at 0")
	assert_false(s.take_hit(10.0), "no hit when depleted")

func test_reset_and_restore() -> void:
	var s := _make()
	s.take_hit(80.0)
	s.restore(30.0)
	assert_almost_eq(s.current, 50.0, 0.001, "restore adds")
	s.reset()
	assert_almost_eq(s.current, 100.0, 0.001, "reset to max")
	assert_false(s.is_invulnerable(), "reset clears invuln")
