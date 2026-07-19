class_name BossMovement
## Boss movement — pure functions (pattern, age, base, amplitudes, freq) -> plane
## position. No node, no state: testable headless (tests/unit/test_boss_movement.gd).
##
## A boss must not slide left-right on a flat line (that reads as a 2D cutout). It
## repositions in shapes that escalate with the fight (standard of the genre), and
## the controller derives roll/pitch from the resulting velocity so the 3D hull
## banks into its turns and pitches into its dives — that is where the depth reads.
##
##   SWAY            gentle horizontal + slow vertical bob — the calm opening
##   FIGURE_EIGHT    Lissajous 8: constant banking, never still
##   ORBIT           circles its anchor: strong, continuous roll
##   CHARGE_RETREAT  lunges toward the player then climbs back — the aggressive late phase
##
## Convention: plane +y is up-screen, so "toward the player" (down) is a DECREASE in y.

enum Pattern { SWAY, FIGURE_EIGHT, ORBIT, CHARGE_RETREAT }

## Which pattern a phase uses: more mobile as the fight escalates. A one-phase boss
## (the mini-boss) still gets a lively figure-eight rather than a flat sway.
static func pattern_for_phase(phase: int, phase_count: int) -> int:
	if phase_count <= 1:
		return Pattern.FIGURE_EIGHT
	var frac := float(phase) / float(maxi(phase_count - 1, 1))
	if frac < 0.25:
		return Pattern.SWAY
	if frac < 0.5:
		return Pattern.FIGURE_EIGHT
	if frac < 0.75:
		return Pattern.ORBIT
	return Pattern.CHARGE_RETREAT

static func position_at(pattern: int, age: float, base: Vector2,
		amp_x: float, amp_y: float, freq: float) -> Vector2:
	var w := age * freq * TAU
	match pattern:
		Pattern.FIGURE_EIGHT:
			# x at the base rate, y at twice it: the classic figure-eight.
			return Vector2(base.x + sin(w) * amp_x, base.y + sin(w * 2.0) * amp_y * 0.6)
		Pattern.ORBIT:
			return Vector2(base.x + cos(w) * amp_x, base.y + sin(w) * amp_y)
		Pattern.CHARGE_RETREAT:
			# One cycle: a quick lunge toward the player, then a slower climb back.
			var cycle := fposmod(age * freq, 1.0)
			var lunge: float
			if cycle < 0.35:
				var t := cycle / 0.35
				lunge = 1.0 - (1.0 - t) * (1.0 - t)   # ease-out dive
			else:
				lunge = 1.0 - (cycle - 0.35) / 0.65    # linear climb back
			return Vector2(base.x + sin(w * 0.5) * amp_x * 0.6,
				base.y - lunge * amp_y * 2.2)          # dive down = -y
		_: # SWAY
			return Vector2(base.x + sin(w) * amp_x, base.y + sin(w * 0.5) * amp_y * 0.4)
