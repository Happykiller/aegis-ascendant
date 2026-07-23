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

var _sliders: Dictionary = {}
var _pixelation: CheckButton

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
