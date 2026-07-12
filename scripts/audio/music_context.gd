class_name MusicContext
extends RefCounted
## What the level director knows about the fight, in the terms the music cares about.
## The level owns exactly one of these and mutates it in place — resolving the musical
## state must never allocate (spec §26.2).

## Mirrors graybox_root.Phase; kept aligned by test_music_director.gd.
enum LevelPhase { FIGHTER_WAVES, MINI_BOSS, DOCKING, COMMAND_TRANSFER, FORTRESS_BOSS, VICTORY }

var level_phase: int = LevelPhase.FIGHTER_WAVES
## How far into the fighter waves we are, 0 to 1. Drives Launch -> Skirmish -> Fleet Battle.
var wave_progress: float = 0.0
var boss_phase: int = 0
var boss_phase_count: int = 0
var boss_health_ratio: float = 1.0
## Victory only starts once nothing dangerous is still in flight (music structure §mix).
var hostiles_clear: bool = false
