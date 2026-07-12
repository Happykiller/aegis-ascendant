extends "res://tests/test_case.gd"
## MusicDirector state resolution and crossfade table (spec §18.2).
## Pure logic: no autoload, no AudioServer, no scene — the whole adaptive layer is
## decided here, so this is where it can be checked.

const GrayboxRoot := preload("res://scripts/gameplay/graybox_root.gd")

func _ctx(phase: int) -> MusicContext:
	var ctx := MusicContext.new()
	ctx.level_phase = phase
	return ctx

func test_level_phases_stay_aligned_with_the_director() -> void:
	# MusicContext mirrors graybox_root.Phase by value. If someone reorders one enum,
	# every state resolution silently shifts — catch it here instead of in the mix.
	assert_eq(MusicContext.LevelPhase.FIGHTER_WAVES, GrayboxRoot.Phase.FIGHTER_WAVES, "FIGHTER_WAVES")
	assert_eq(MusicContext.LevelPhase.MINI_BOSS, GrayboxRoot.Phase.MINI_BOSS, "MINI_BOSS")
	assert_eq(MusicContext.LevelPhase.DOCKING, GrayboxRoot.Phase.DOCKING, "DOCKING")
	assert_eq(MusicContext.LevelPhase.COMMAND_TRANSFER, GrayboxRoot.Phase.COMMAND_TRANSFER, "COMMAND_TRANSFER")
	assert_eq(MusicContext.LevelPhase.FORTRESS_BOSS, GrayboxRoot.Phase.FORTRESS_BOSS, "FORTRESS_BOSS")
	assert_eq(MusicContext.LevelPhase.VICTORY, GrayboxRoot.Phase.VICTORY, "VICTORY")

func test_fighter_waves_escalate_with_progress() -> void:
	var ctx := _ctx(MusicContext.LevelPhase.FIGHTER_WAVES)
	ctx.wave_progress = 0.0
	assert_eq(MusicDirector.resolve(ctx), MusicDirector.State.LAUNCH, "opening = Launch")
	ctx.wave_progress = 0.4
	assert_eq(MusicDirector.resolve(ctx), MusicDirector.State.SKIRMISH, "mid wave = Skirmish")
	ctx.wave_progress = 0.9
	assert_eq(MusicDirector.resolve(ctx), MusicDirector.State.FLEET_BATTLE, "late wave = Fleet Battle")

func test_mini_boss_keeps_fleet_battle() -> void:
	assert_eq(MusicDirector.resolve(_ctx(MusicContext.LevelPhase.MINI_BOSS)),
		MusicDirector.State.FLEET_BATTLE, "mini-boss shares the Fleet Battle bed")

func test_docking_and_command_transfer() -> void:
	assert_eq(MusicDirector.resolve(_ctx(MusicContext.LevelPhase.DOCKING)),
		MusicDirector.State.DOCKING, "docking")
	assert_eq(MusicDirector.resolve(_ctx(MusicContext.LevelPhase.COMMAND_TRANSFER)),
		MusicDirector.State.FORTRESS_AWAKENING, "command transfer wakes the fortress")

func test_fortress_boss_follows_health() -> void:
	var ctx := _ctx(MusicContext.LevelPhase.FORTRESS_BOSS)
	ctx.boss_health_ratio = 1.0
	assert_eq(MusicDirector.resolve(ctx), MusicDirector.State.BOSS_PHASE_1, "healthy = phase 1")
	ctx.boss_health_ratio = 0.4
	assert_eq(MusicDirector.resolve(ctx), MusicDirector.State.BOSS_PHASE_2, "hurt = phase 2")
	ctx.boss_health_ratio = 0.1
	assert_eq(MusicDirector.resolve(ctx), MusicDirector.State.FINAL_CHARGE, "nearly dead = final charge")

func test_boss_phase_announcement_also_escalates() -> void:
	# The boss can declare its later phase before its health says so.
	var ctx := _ctx(MusicContext.LevelPhase.FORTRESS_BOSS)
	ctx.boss_health_ratio = 0.9
	ctx.boss_phase = 1
	ctx.boss_phase_count = 2
	assert_eq(MusicDirector.resolve(ctx), MusicDirector.State.BOSS_PHASE_2, "second half = phase 2")

func test_escalation_never_goes_backwards_as_the_boss_dies() -> void:
	var ctx := _ctx(MusicContext.LevelPhase.FORTRESS_BOSS)
	var seen: Array[int] = []
	for step in 21:
		ctx.boss_health_ratio = 1.0 - float(step) / 20.0
		var state := MusicDirector.resolve(ctx)
		if seen.is_empty() or seen[-1] != state:
			seen.append(state)
	assert_eq(seen, [MusicDirector.State.BOSS_PHASE_1, MusicDirector.State.BOSS_PHASE_2,
		MusicDirector.State.FINAL_CHARGE] as Array[int], "phase 1 -> phase 2 -> final charge, once each")

func test_victory_waits_for_the_screen_to_clear() -> void:
	var ctx := _ctx(MusicContext.LevelPhase.VICTORY)
	ctx.hostiles_clear = false
	assert_eq(MusicDirector.resolve(ctx), MusicDirector.State.FINAL_CHARGE,
		"enemy fire still in flight: hold the charge")
	ctx.hostiles_clear = true
	assert_eq(MusicDirector.resolve(ctx), MusicDirector.State.VICTORY, "screen clear: resolve")

func test_every_playable_state_has_a_cue() -> void:
	for state in MusicDirector.State.values():
		if state == MusicDirector.State.SILENT:
			assert_true(MusicDirector.cue(state).is_empty(), "SILENT has no cue")
		else:
			assert_false(MusicDirector.cue(state).is_empty(), "state %d has a cue" % state)

func test_crossfade_table() -> void:
	assert_almost_eq(MusicDirector.crossfade_seconds(
		MusicDirector.State.LAUNCH, MusicDirector.State.SKIRMISH), 6.0, 0.001, "default is a long fade")
	assert_almost_eq(MusicDirector.crossfade_seconds(
		MusicDirector.State.BOSS_PHASE_1, MusicDirector.State.BOSS_PHASE_2), 1.2, 0.001,
		"into phase 2: controlled cut then impact")
	assert_almost_eq(MusicDirector.crossfade_seconds(
		MusicDirector.State.BOSS_PHASE_2, MusicDirector.State.FINAL_CHARGE), 2.5, 0.001,
		"into the final charge")
	assert_true(MusicDirector.crossfade_seconds(
		MusicDirector.State.FINAL_CHARGE, MusicDirector.State.VICTORY) > 0.0,
		"a state change is never a hard cut (spec §18.2)")

func test_the_title_is_never_resolved_from_a_fight() -> void:
	# TITLE is claimed by the boot screen, not derived from a level phase. If resolve() ever
	# returned it, the title theme would cut into the middle of a fight.
	for phase in MusicContext.LevelPhase.values():
		var ctx := _ctx(phase)
		for progress in [0.0, 0.5, 1.0]:
			ctx.wave_progress = progress
			ctx.boss_health_ratio = progress
			assert_false(MusicDirector.resolve(ctx) == MusicDirector.State.TITLE,
				"phase %d never resolves to TITLE" % phase)

func test_the_title_theme_rises_out_of_silence() -> void:
	# A 140 BPM theme slammed in at full level on launch is a jump-scare, not an opening.
	assert_almost_eq(MusicDirector.crossfade_seconds(
		MusicDirector.State.SILENT, MusicDirector.State.TITLE), 1.2, 0.001, "title fades in")
	assert_eq(MusicDirector.cue(MusicDirector.State.TITLE), &"main_theme", "title cue")
