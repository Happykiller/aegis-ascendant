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

## Passée comme graine, elle éteint la dérive : c'est le défaut, et c'est ce qui garde les
## figures testables pour elles-mêmes.
const NO_DRIFT := -1.0

## Amplitude de la dérive organique d'un boss, en unités du plan. Plus large que celle des
## unités : une coque de onze mètres qui bougerait de la même demi-unité ne bougerait pas.
##
## ⚠️ `ORGANIC_REACH` et non `DRIFT` : le contrôleur porte déjà un `drift_amplitude` qui
## désigne l'ampleur de la FIGURE. Deux sens sur un même mot finiraient par se croiser.
const ORGANIC_REACH := 1.1


## Position d'un boss à un âge donné.
##
## ⚠️ LES QUATRE FIGURES SONT HARMONIQUES — `w`, `w × 2`, `w × 0,5` — donc elles BOUCLENT
## exactement. C'est ce que le playtest du 2026-08-27 a nommé « figé, fête foraine » : à
## la troisième répétition l'œil a la figure entière, et le boss cesse d'être un adversaire
## pour redevenir un mobile. `drift_seed` ajoute une dérive sur des périodes NON
## harmoniques (`OrganicDrift`) : la figure reste lisible, sa répétition ne l'est plus.
static func position_at(pattern: int, age: float, base: Vector2,
		amp_x: float, amp_y: float, freq: float,
		drift_seed: float = NO_DRIFT) -> Vector2:
	var pose := _figure(pattern, age, base, amp_x, amp_y, freq)
	if drift_seed < 0.0:
		return pose
	return pose + OrganicDrift.offset(age, drift_seed, ORGANIC_REACH)


static func _figure(pattern: int, age: float, base: Vector2,
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
