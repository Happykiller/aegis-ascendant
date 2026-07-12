extends "res://tests/test_case.gd"
## The nine tracks the director can ask for must actually exist and be loadable.
## Catches a renamed OGG or a state added to the enum without a track behind it.

const MUSIC_BANK_PATH := "res://resources/audio/music_bank.tres"

func _bank() -> AudioCueBank:
	return load(MUSIC_BANK_PATH) as AudioCueBank

func test_bank_loads_and_validates() -> void:
	var bank := _bank()
	assert_true(bank != null, "music_bank.tres loads as an AudioCueBank")
	var errors := bank.validate()
	assert_true(errors.is_empty(), "bank is valid (got: %s)" % ", ".join(errors))

func test_every_state_the_director_can_pick_has_a_track() -> void:
	var index := _bank().build_index()
	for state in MusicDirector.State.values():
		if state == MusicDirector.State.SILENT:
			continue
		var cue := MusicDirector.cue(state)
		assert_true(index.has(cue), "state %d has a track in the bank (%s)" % [state, cue])
		if index.has(cue):
			var data: AudioCueData = index[cue]
			assert_true(data.stream != null, "%s has a stream" % cue)

func test_music_plays_on_the_music_bus_and_loops() -> void:
	# A bed that does not loop leaves the fight in silence after thirty seconds; one that
	# plays on the SFX bus cannot be mixed down separately (spec §13).
	for cue in _bank().cues:
		assert_eq(cue.bus, "Music", "%s is on the Music bus" % cue.id)
		assert_true(cue.looping, "%s loops" % cue.id)
