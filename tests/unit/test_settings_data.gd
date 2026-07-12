extends "res://tests/test_case.gd"
## SettingsData: pure volume state (spec §13). SettingsManager is an autoload and
## touches AudioServer; the values it holds do neither, so they are tested here.

const SettingsDataScript := preload("res://scripts/core/settings_data.gd")

func test_defaults_are_sane() -> void:
	var data: SettingsData = SettingsDataScript.new()
	for bus in SettingsData.BUSES:
		var value := data.get_linear(bus)
		assert_true(value > 0.0 and value <= 1.0, "%s defaults to something audible" % bus)

func test_set_clamps_to_range() -> void:
	var data: SettingsData = SettingsDataScript.new()
	data.set_linear(&"Music", 2.5)
	assert_almost_eq(data.get_linear(&"Music"), 1.0, 0.001, "clamped to 1")
	data.set_linear(&"Music", -3.0)
	assert_almost_eq(data.get_linear(&"Music"), 0.0, 0.001, "clamped to 0")

func test_round_trip_through_dict() -> void:
	var data: SettingsData = SettingsDataScript.new()
	data.set_linear(&"Master", 0.42)
	data.set_linear(&"SFX", 0.13)
	var restored: SettingsData = SettingsDataScript.new()
	restored.from_dict(data.to_dict())
	assert_almost_eq(restored.get_linear(&"Master"), 0.42, 0.001, "Master survives a save/load")
	assert_almost_eq(restored.get_linear(&"SFX"), 0.13, 0.001, "SFX survives a save/load")

func test_a_corrupt_settings_file_falls_back_to_defaults() -> void:
	# A hand-edited or stale user://settings.cfg must not brick the mix.
	var data: SettingsData = SettingsDataScript.new()
	data.from_dict({&"Master": "loud", &"Music": 99.0, &"Nonsense": 0.5})
	assert_almost_eq(data.get_linear(&"Master"),
		SettingsData.DEFAULTS[&"Master"], 0.001, "garbage value ignored")
	assert_almost_eq(data.get_linear(&"Music"), 1.0, 0.001, "out-of-range value clamped")
	assert_almost_eq(data.get_linear(&"SFX"),
		SettingsData.DEFAULTS[&"SFX"], 0.001, "missing key keeps its default")

func test_zero_is_true_silence() -> void:
	assert_almost_eq(SettingsData.to_db(0.0), SettingsData.SILENCE_DB, 0.001,
		"a slider at zero is silent, not just quiet")
	assert_almost_eq(SettingsData.to_db(1.0), 0.0, 0.001, "full slider is unity gain")
	assert_true(SettingsData.to_db(0.5) < 0.0, "half a slider attenuates")

func test_unknown_bus_is_refused() -> void:
	var data: SettingsData = SettingsDataScript.new()
	print("[test] expected warning below (unknown bus):")
	data.set_linear(&"Reverb", 0.5)
	assert_false(data.to_dict().has(&"Reverb"), "unknown bus does not enter the settings")
