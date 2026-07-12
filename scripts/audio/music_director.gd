class_name MusicDirector
extends RefCounted
## Which of the nine musical states the fight is currently in, and how long the crossfade
## into it should take (spec §18.2, docs/forge/output/adaptive_music_structure.md).
##
## Pure logic: no node, no AudioServer, no scene access. That is what makes the whole
## adaptive layer testable headless — AudioManager only executes what this decides.

enum State {
	SILENT,
	## The title theme. Not a state of the fight: nothing resolves into it, the boot screen
	## claims it directly. It is the piece the nine others are derived from — same signature
	## cell, same D minor (docs/forge/output/main_theme_spec.md).
	TITLE,
	LAUNCH,
	SKIRMISH,
	FLEET_BATTLE,
	DOCKING,
	FORTRESS_AWAKENING,
	BOSS_PHASE_1,
	BOSS_PHASE_2,
	FINAL_CHARGE,
	VICTORY,
}

## Cue ids in resources/audio/music_bank.tres.
const CUES: Dictionary = {
	State.TITLE: &"main_theme",
	State.LAUNCH: &"launch",
	State.SKIRMISH: &"skirmish",
	State.FLEET_BATTLE: &"fleet_battle",
	State.DOCKING: &"docking",
	State.FORTRESS_AWAKENING: &"fortress_awakening",
	State.BOSS_PHASE_1: &"boss_phase_1",
	State.BOSS_PHASE_2: &"boss_phase_2",
	State.FINAL_CHARGE: &"final_charge",
	State.VICTORY: &"victory",
}

## Wave progress at which the fighter section escalates.
const _SKIRMISH_AT := 0.25
const _FLEET_BATTLE_AT := 0.70
## Boss health under which the fight tips into its second half, then into the finale.
const _BOSS_PHASE_2_AT := 0.50
const _FINAL_CHARGE_AT := 0.15

## Transitions must be musical, never a hard cut (spec §18.2). Default is a long fade;
## the exceptions come from the structure's own transition column.
const _DEFAULT_CROSSFADE := 6.0
const _CROSSFADE_INTO: Dictionary = {
	State.TITLE: 1.2,           # the theme rises out of silence; it does not hit on launch
	State.BOSS_PHASE_2: 1.2,    # "coupe contrôlée puis impact"
	State.FINAL_CHARGE: 2.5,    # "crescendo verrouillé sur la charge"
	State.VICTORY: 3.5,         # "résolution après le tir final"
	State.SILENT: 1.5,
}

static func cue(state: int) -> StringName:
	return CUES.get(state, &"")

static func crossfade_seconds(_from_state: int, to_state: int) -> float:
	return _CROSSFADE_INTO.get(to_state, _DEFAULT_CROSSFADE)

## The only place that decides what plays **during a fight**. Pure function of the context.
## Never returns TITLE: the title is not a phase of the level, it is what plays before there
## is a level at all. The boot screen sets it directly.
static func resolve(ctx: MusicContext) -> int:
	match ctx.level_phase:
		MusicContext.LevelPhase.FIGHTER_WAVES:
			if ctx.wave_progress < _SKIRMISH_AT:
				return State.LAUNCH
			if ctx.wave_progress < _FLEET_BATTLE_AT:
				return State.SKIRMISH
			return State.FLEET_BATTLE
		MusicContext.LevelPhase.MINI_BOSS:
			return State.FLEET_BATTLE
		MusicContext.LevelPhase.DOCKING:
			return State.DOCKING
		MusicContext.LevelPhase.COMMAND_TRANSFER:
			return State.FORTRESS_AWAKENING
		MusicContext.LevelPhase.FORTRESS_BOSS:
			if ctx.boss_health_ratio <= _FINAL_CHARGE_AT:
				return State.FINAL_CHARGE
			# Either the boss announced its later phase, or it is simply hurt enough.
			var late_phase := ctx.boss_phase_count > 0 \
				and ctx.boss_phase * 2 >= ctx.boss_phase_count
			if late_phase or ctx.boss_health_ratio <= _BOSS_PHASE_2_AT:
				return State.BOSS_PHASE_2
			return State.BOSS_PHASE_1
		MusicContext.LevelPhase.VICTORY:
			# Hold the previous cue until the screen is clear, then resolve.
			return State.VICTORY if ctx.hostiles_clear else State.FINAL_CHARGE
	return State.SILENT
