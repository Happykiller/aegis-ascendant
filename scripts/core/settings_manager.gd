extends Node
## Player settings (autoload "SettingsManager", allowed by spec §20.2). Owns the volume
## of each audio bus and persists it to user://settings.cfg.
##
## Applying settings is the *only* thing here that touches AudioServer: the values
## themselves live in SettingsData, which is pure and tested on its own.

const SettingsDataScript := preload("res://scripts/core/settings_data.gd")
const SETTINGS_PATH := "user://settings.cfg"
const _SECTION := "audio"
## Dragging a slider fires continuously; writing the file on every frame would hammer
## the disk for nothing.
const _SAVE_DEBOUNCE := 0.5

signal audio_changed(data: SettingsData)

var _data: SettingsData = SettingsDataScript.new()
var _save_timer: SceneTreeTimer

func _ready() -> void:
	load_settings()
	apply_all()

func get_audio() -> SettingsData:
	return _data

func set_bus_linear(bus: StringName, value: float) -> void:
	_data.set_linear(bus, value)
	_apply_bus(bus)
	audio_changed.emit(_data)
	_schedule_save()

func apply_all() -> void:
	for bus in SettingsData.BUSES:
		_apply_bus(bus)

func _apply_bus(bus: StringName) -> void:
	var index := AudioServer.get_bus_index(bus)
	if index < 0:
		push_warning("[Settings] missing bus '%s' — is the layout loaded?" % bus)
		return
	AudioServer.set_bus_volume_db(index, SettingsData.to_db(_data.get_linear(bus)))

func load_settings() -> void:
	var config := ConfigFile.new()
	if config.load(SETTINGS_PATH) != OK:
		return # first run, or an unreadable file: the defaults stand
	var stored := {}
	for key in config.get_section_keys(_SECTION) if config.has_section(_SECTION) else []:
		stored[key] = config.get_value(_SECTION, key)
	_data.from_dict(stored)

func save_settings() -> void:
	var config := ConfigFile.new()
	for bus in SettingsData.BUSES:
		config.set_value(_SECTION, String(bus), _data.get_linear(bus))
	var error := config.save(SETTINGS_PATH)
	if error != OK:
		push_warning("[Settings] could not save %s (error %d)" % [SETTINGS_PATH, error])

func _schedule_save() -> void:
	if _save_timer != null and _save_timer.time_left > 0.0:
		return
	_save_timer = get_tree().create_timer(_SAVE_DEBOUNCE)
	_save_timer.timeout.connect(save_settings)
