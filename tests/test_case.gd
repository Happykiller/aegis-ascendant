extends RefCounted
## Minimal unit-test base class (spec §28.1: no third-party framework).
## Tests extend this by path: `extends "res://tests/test_case.gd"`.
## Assertions accumulate failures instead of aborting (native `assert` is
## debug-only and stops the whole run).

var failures: PackedStringArray = PackedStringArray()
var assert_count: int = 0

func assert_true(condition: bool, message: String) -> void:
	assert_count += 1
	if not condition:
		failures.append("assert_true failed: %s" % message)

func assert_false(condition: bool, message: String) -> void:
	assert_count += 1
	if condition:
		failures.append("assert_false failed: %s" % message)

func assert_eq(actual: Variant, expected: Variant, message: String) -> void:
	assert_count += 1
	if actual != expected:
		failures.append("assert_eq failed: %s (actual=%s expected=%s)" %
			[message, str(actual), str(expected)])

func assert_almost_eq(actual: float, expected: float, epsilon: float, message: String) -> void:
	assert_count += 1
	if absf(actual - expected) > epsilon:
		failures.append("assert_almost_eq failed: %s (actual=%f expected=%f eps=%f)" %
			[message, actual, expected, epsilon])

func fail(message: String) -> void:
	assert_count += 1
	failures.append("fail: %s" % message)
