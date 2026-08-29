extends Node
## Player settings (autoload "SettingsManager", allowed by spec §20.2). Owns the volume
## of each audio bus and persists it to user://settings.cfg.
##
## Applying settings is the *only* thing here that touches AudioServer: the values
## themselves live in SettingsData, which is pure and tested on its own.

const SettingsDataScript := preload("res://scripts/core/settings_data.gd")
const SETTINGS_PATH := "user://settings.cfg"
const _SECTION := "audio"
const _SECTION_GRAPHICS := "graphics"
const _SECTION_DEBUG := "debug"
const _SECTION_LOADOUT := "loadout"
## Dragging a slider fires continuously; writing the file on every frame would hammer
## the disk for nothing.
const _SAVE_DEBOUNCE := 0.5

signal audio_changed(data: SettingsData)
## Émis quand un réglage d'image change. Les post-process s'y abonnent — ils vivent
## dans les scènes, pas ici : cet autoload ne connaît aucun nœud de rendu.
signal graphics_changed(data: SettingsData)
## Émis quand une couche de débogage est allumée ou éteinte (voir `SettingsData`).
signal debug_changed(data: SettingsData)

var _data: SettingsData = SettingsDataScript.new()
var _save_timer: SceneTreeTimer

func _ready() -> void:
	load_settings()
	apply_all()

func get_audio() -> SettingsData:
	return _data

## Même objet que `get_audio()` : une seule Resource de réglages, deux vues. Deux
## accesseurs plutôt qu'un `get_settings()` fourre-tout, pour que l'appelant dise ce
## qu'il vient chercher.
func get_graphics() -> SettingsData:
	return _data

## Même objet, troisième vue : les couches de débogage.
## L'équipement du joueur — aujourd'hui sa coque, et rien d'autre.
func get_loadout() -> SettingsData:
	return _data

func get_debug() -> SettingsData:
	return _data

func set_debug_layer(layer: StringName, enabled: bool) -> void:
	if _data.get_debug_layer(layer) == enabled:
		return
	_data.set_debug_layer(layer, enabled)
	debug_changed.emit(_data)
	_schedule_save()

## La coque choisie au bestiaire. Persistée aussitôt : le joueur qui la choisit
## quitte souvent l'écran dans la foulée, et un réglage qui attend la fermeture
## propre du jeu est un réglage qu'on perd.
func set_hull(scene_path: String) -> void:
	_data.hull = scene_path
	save_settings()

func set_pixelation(enabled: bool) -> void:
	if _data.pixelation == enabled:
		return
	_data.pixelation = enabled
	graphics_changed.emit(_data)
	_schedule_save()

## Secousse d'écran, de 0 (éteinte) à 1 (pleine). Même chemin que la pixelisation :
## la valeur vit dans la donnée pure, le signal prévient les nœuds de scène, et
## l'écriture disque est différée.
func set_shake(value: float) -> void:
	var clamped := clampf(value, 0.0, 1.0)
	if is_equal_approx(_data.shake, clamped):
		return
	_data.shake = clamped
	graphics_changed.emit(_data)
	_schedule_save()

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
	_data.audio_from_dict(stored)
	var graphics := {}
	for key in config.get_section_keys(_SECTION_GRAPHICS) if config.has_section(_SECTION_GRAPHICS) else []:
		graphics[key] = config.get_value(_SECTION_GRAPHICS, key)
	_data.graphics_from_dict(graphics)
	var debug := {}
	if config.has_section_key(_SECTION_LOADOUT, "hull"):
		_data.hull = str(config.get_value(_SECTION_LOADOUT, "hull", ""))
	for key in config.get_section_keys(_SECTION_DEBUG) if config.has_section(_SECTION_DEBUG) else []:
		debug[key] = config.get_value(_SECTION_DEBUG, key)
	_data.debug_from_dict(debug)

func save_settings() -> void:
	var config := ConfigFile.new()
	for bus in SettingsData.BUSES:
		config.set_value(_SECTION, String(bus), _data.get_linear(bus))
	config.set_value(_SECTION_LOADOUT, "hull", _data.hull)
	config.set_value(_SECTION_GRAPHICS, "pixelation", _data.pixelation)
	config.set_value(_SECTION_GRAPHICS, "shake", _data.shake)
	for layer in SettingsData.DEBUG_LAYERS:
		config.set_value(_SECTION_DEBUG, String(layer), _data.get_debug_layer(layer))
	var error := config.save(SETTINGS_PATH)
	if error != OK:
		push_warning("[Settings] could not save %s (error %d)" % [SETTINGS_PATH, error])

func _schedule_save() -> void:
	if _save_timer != null and _save_timer.time_left > 0.0:
		return
	_save_timer = get_tree().create_timer(_SAVE_DEBOUNCE)
	_save_timer.timeout.connect(save_settings)
