extends Control
## Audio options overlay (spec §19.2, §13: separate music / SFX / voice volumes).
## Autoloads are resolved by path, per project convention.

const SettingsManagerScript := preload("res://scripts/core/settings_manager.gd")
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")

## Slider node name -> bus. The scene names each row after its bus.
const _ROWS: Array[StringName] = [&"Master", &"Music", &"SFX", &"Voice"]

signal closed

@onready var _settings: SettingsManagerScript = get_node_or_null("/root/SettingsManager")
@onready var _audio: AudioManagerScript = get_node_or_null("/root/AudioManager")
@onready var _rows: VBoxContainer = %Rows
@onready var _graphics: VBoxContainer = %Graphics
@onready var _debug: VBoxContainer = %Debug

var _sliders: Dictionary = {}
var _pixelation: CheckButton
var _shake: HSlider
var _shake_value: Label
## Nom de rangee -> couche de `SettingsData`. Chaque interrupteur porte sa phrase
## d'explication dans la scene (but pedagogique).
const _DEBUG_ROWS: Dictionary = {&"Bodies": &"bodies", &"Targets": &"targets", &"Screens": &"screens"}
var _debug_toggles: Dictionary = {}

func _ready() -> void:
	for bus in _ROWS:
		var slider := _rows.get_node_or_null("%s/Slider" % bus) as HSlider
		var value_label := _rows.get_node_or_null("%s/Value" % bus) as Label
		if slider == null:
			continue
		_sliders[bus] = slider
		slider.value_changed.connect(_on_slider_changed.bind(bus, value_label))
	_pixelation = _graphics.get_node_or_null("Pixelation/Toggle") as CheckButton
	if _pixelation != null:
		_pixelation.toggled.connect(_on_pixelation_toggled)
	_shake = _graphics.get_node_or_null("Shake/Slider") as HSlider
	_shake_value = _graphics.get_node_or_null("Shake/Value") as Label
	if _shake != null:
		_shake.value_changed.connect(_on_shake_changed)
	if _debug != null:
		for row: StringName in _DEBUG_ROWS:
			var toggle := _debug.get_node_or_null("%s/Toggle" % row) as CheckButton
			if toggle == null:
				continue
			_debug_toggles[row] = toggle
			toggle.toggled.connect(_on_debug_toggled.bind(_DEBUG_ROWS[row]))
	open()

## Show the overlay with the values that are actually in force.
func open() -> void:
	for bus: StringName in _sliders:
		var slider: HSlider = _sliders[bus]
		if _settings != null:
			slider.set_value_no_signal(_settings.get_audio().get_linear(bus) * 100.0)
		var value_label := _rows.get_node_or_null("%s/Value" % bus) as Label
		if value_label != null:
			value_label.text = "%d" % roundi(slider.value)
	if _pixelation != null and _settings != null:
		# `set_pressed_no_signal` : sans lui, ouvrir l'écran rejouerait le réglage —
		# et son clic de confirmation — comme si le joueur venait de le basculer.
		_pixelation.set_pressed_no_signal(_settings.get_graphics().pixelation)
	if _shake != null and _settings != null:
		_shake.set_value_no_signal(_settings.get_graphics().shake * 100.0)
		if _shake_value != null:
			_shake_value.text = "%d" % roundi(_shake.value)
	if _settings != null:
		for row: StringName in _debug_toggles:
			(_debug_toggles[row] as CheckButton).set_pressed_no_signal(
				_settings.get_debug().get_debug_layer(_DEBUG_ROWS[row]))
	show()
	# Keyboard/pad users land on the first slider.
	var first := _sliders.get(_ROWS[0]) as HSlider
	if first != null:
		first.grab_focus()

func _on_slider_changed(value: float, bus: StringName, value_label: Label) -> void:
	if value_label != null:
		value_label.text = "%d" % roundi(value)
	if _settings != null:
		_settings.set_bus_linear(bus, value / 100.0)
	# Audible confirmation on the bus you are actually moving — a muted SFX slider that
	# still ticks would be lying to you.
	if _audio != null and bus != &"Music":
		_audio.play(&"ui_select")

## L'effet est IMMÉDIAT : la couche de post-process est derrière l'écran d'options, le
## joueur voit donc son réglage sur l'image qu'il est en train de regarder. C'est ce qui
## rend l'option jugeable sans quitter le menu.
func _on_pixelation_toggled(enabled: bool) -> void:
	if _settings != null:
		_settings.set_pixelation(enabled)
	if _audio != null:
		_audio.play(&"ui_select")

## Comme la pixelisation, le réglage s'applique TOUT DE SUITE — et il se sent : le
## `CameraDirector` répond au signal par une brève secousse à la nouvelle intensité.
## Sans cet aperçu, le curseur serait le seul réglage du menu dont on ne peut rien
## juger sans quitter l'écran.
func _on_shake_changed(value: float) -> void:
	if _shake_value != null:
		_shake_value.text = "%d" % roundi(value)
	if _settings != null:
		_settings.set_shake(value / 100.0)
	if _audio != null:
		_audio.play(&"ui_select")

## Immediat, comme les autres : le niveau redessine ses couches a l'image suivante, et le
## joueur voit apparaitre ou disparaitre la representation qu'il vient de nommer.
func _on_debug_toggled(enabled: bool, layer: StringName) -> void:
	if _settings != null:
		_settings.set_debug_layer(layer, enabled)
	if _audio != null:
		_audio.play(&"ui_select")

func _on_test_pressed() -> void:
	if _audio != null:
		_audio.play(&"ui_confirm")

func _on_back_pressed() -> void:
	close()

func close() -> void:
	if _settings != null:
		_settings.save_settings()
	hide()
	closed.emit()

func _unhandled_input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		close()
