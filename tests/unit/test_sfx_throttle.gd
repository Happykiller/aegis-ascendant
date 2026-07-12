extends "res://tests/test_case.gd"
## SfxThrottle rate limiting (spec §9.2: firing must not spam the mix).
## The clock is injected, so no engine time and no audio device are involved.

const SfxThrottleScript := preload("res://scripts/audio/sfx_throttle.gd")

func test_first_trigger_always_plays() -> void:
	var throttle: SfxThrottle = SfxThrottleScript.new()
	assert_true(throttle.should_play(&"player_pulse", 0.05, 0.0), "first trigger plays")

func test_second_trigger_within_interval_is_dropped() -> void:
	var throttle: SfxThrottle = SfxThrottleScript.new()
	throttle.should_play(&"player_pulse", 0.05, 1.00)
	assert_false(throttle.should_play(&"player_pulse", 0.05, 1.04), "too soon: dropped")

func test_trigger_after_interval_plays_again() -> void:
	var throttle: SfxThrottle = SfxThrottleScript.new()
	throttle.should_play(&"player_pulse", 0.05, 1.00)
	assert_true(throttle.should_play(&"player_pulse", 0.05, 1.05), "interval elapsed: plays")

func test_dropped_trigger_does_not_extend_the_window() -> void:
	# A rejected call must not count as a play, or a held fire button would silence
	# the cue forever.
	var throttle: SfxThrottle = SfxThrottleScript.new()
	throttle.should_play(&"player_pulse", 0.05, 1.00)
	throttle.should_play(&"player_pulse", 0.05, 1.04) # dropped
	assert_true(throttle.should_play(&"player_pulse", 0.05, 1.05), "window runs from the last play")

func test_cues_are_throttled_independently() -> void:
	var throttle: SfxThrottle = SfxThrottleScript.new()
	throttle.should_play(&"player_pulse", 0.05, 1.00)
	assert_true(throttle.should_play(&"enemy_pulse", 0.05, 1.00), "other cue unaffected")

func test_zero_interval_never_throttles() -> void:
	var throttle: SfxThrottle = SfxThrottleScript.new()
	assert_true(throttle.should_play(&"helios_lance", 0.0, 5.0), "first")
	assert_true(throttle.should_play(&"helios_lance", 0.0, 5.0), "same instant, still plays")

func test_reset_clears_history() -> void:
	var throttle: SfxThrottle = SfxThrottleScript.new()
	throttle.should_play(&"player_pulse", 0.05, 1.00)
	throttle.reset()
	assert_true(throttle.should_play(&"player_pulse", 0.05, 1.00), "history cleared")
