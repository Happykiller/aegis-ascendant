extends "res://tests/test_case.gd"
## Integrity of the shipped audio assets (spec §18.3, §22.1). Loads the real bank and
## bus layout: catches a renamed WAV, a typo'd cue id or a missing bus at test time
## rather than in a silent build. No AudioServer, no device — headless safe.

const SFX_BANK_PATH := "res://resources/audio/sfx_bank.tres"
const BUS_LAYOUT_PATH := "res://resources/audio/default_bus_layout.tres"

## Every cue graybox_root.gd triggers. Keep in sync when a call site is added.
const EXPECTED_CUES: Array[StringName] = [
	&"player_pulse", &"enemy_pulse", &"hull_impact", &"shield_impact",
	&"small_explosion", &"medium_explosion", &"heavy_explosion",
	&"pickup_power", &"pickup_shield", &"pickup_score",
	&"danger_alarm", &"docking_lock", &"rail_battery", &"helios_lance",
	&"player_death", &"boss_phase_shift", &"ui_banner", &"engine_loop",
]

func _bank() -> AudioCueBank:
	return load(SFX_BANK_PATH) as AudioCueBank

func test_bank_loads() -> void:
	assert_true(_bank() != null, "sfx_bank.tres loads as an AudioCueBank")

func test_bank_validates() -> void:
	var errors := _bank().validate()
	assert_true(errors.is_empty(), "bank is valid (got: %s)" % ", ".join(errors))

func test_every_expected_cue_is_present_with_a_stream() -> void:
	var index := _bank().build_index()
	for cue in EXPECTED_CUES:
		assert_true(index.has(cue), "cue %s is declared" % cue)
		if index.has(cue):
			var data: AudioCueData = index[cue]
			assert_true(data.stream != null, "cue %s has a stream" % cue)

func test_cues_target_a_declared_bus() -> void:
	var layout := load(BUS_LAYOUT_PATH)
	assert_true(layout != null, "default_bus_layout.tres loads")
	var buses := PackedStringArray()
	for i in 8: # names are stored as bus/<i>/name; index 0 (Master) is implicit
		var value: Variant = layout.get("bus/%d/name" % i)
		if value != null:
			buses.append(String(value))
	assert_true(buses.has("Music"), "Music bus exists")
	assert_true(buses.has("SFX"), "SFX bus exists")
	assert_true(buses.has("Voice"), "Voice bus exists")
	for cue in _bank().cues:
		assert_true(cue.bus == "Master" or buses.has(cue.bus),
			"cue %s targets an existing bus (%s)" % [cue.id, cue.bus])

func test_engine_bed_is_the_only_looping_cue() -> void:
	# Any other looping one-shot would never stop: it would jam a pool voice forever.
	var looping := PackedStringArray()
	for cue in _bank().cues:
		if cue.looping:
			looping.append(String(cue.id))
	assert_eq(looping, PackedStringArray(["engine_loop"]), "only the engine bed loops")

func test_rate_limited_cues_have_a_pitch_range() -> void:
	# A cue that can fire many times a second and always at the same pitch is what
	# makes a shmup sound like a machine gun jam (spec §18.3).
	for cue in _bank().cues:
		if cue.min_interval > 0.0 and cue.min_interval <= 0.1:
			assert_true(cue.pitch_max > cue.pitch_min,
				"fast cue %s varies its pitch" % cue.id)
