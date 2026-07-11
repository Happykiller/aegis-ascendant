class_name PlayerShield
extends RefCounted
## Player shield model (spec §8.3): depletes on hit, brief invulnerability after
## impact, slow regeneration after a quiet delay. Pure logic — testable headless.
## Lives/respawn are handled by the controller; this owns one shield instance.

var maximum: float = 100.0
var current: float = 100.0
var regen_delay: float = 3.0
var regen_rate: float = 12.0      # units per second once regen starts
var invuln_time: float = 1.2

var _time_since_hit: float = 0.0
var _invuln_timer: float = 0.0

func configure(p_max: float, p_regen_delay: float, p_regen_rate: float, p_invuln: float) -> void:
	maximum = p_max
	regen_delay = p_regen_delay
	regen_rate = p_regen_rate
	invuln_time = p_invuln
	reset()

func reset() -> void:
	current = maximum
	_time_since_hit = regen_delay # allow immediate regen readiness after respawn
	_invuln_timer = 0.0

## Grant temporary invulnerability (e.g. right after a respawn).
func grant_invulnerability(duration: float) -> void:
	_invuln_timer = maxf(_invuln_timer, duration)

func is_invulnerable() -> bool:
	return _invuln_timer > 0.0

func is_depleted() -> bool:
	return current <= 0.0

func ratio() -> float:
	return current / maximum if maximum > 0.0 else 0.0

## Apply a hit. Returns true if damage landed (i.e. shield went down / depleted),
## false if blocked by invulnerability or already depleted.
func take_hit(damage: float) -> bool:
	if _invuln_timer > 0.0 or current <= 0.0:
		return false
	current = maxf(current - damage, 0.0)
	_time_since_hit = 0.0
	if current > 0.0:
		_invuln_timer = invuln_time
	return true

func tick(delta: float) -> void:
	if _invuln_timer > 0.0:
		_invuln_timer = maxf(_invuln_timer - delta, 0.0)
	if current <= 0.0:
		return
	_time_since_hit += delta
	if _time_since_hit >= regen_delay and current < maximum:
		current = minf(current + regen_rate * delta, maximum)

## Immediate top-up (Shield Cell pickup, spec §10.1).
func restore(amount: float) -> void:
	current = minf(current + amount, maximum)
