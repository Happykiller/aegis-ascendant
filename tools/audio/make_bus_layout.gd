extends SceneTree
## One-shot generator for res://resources/audio/default_bus_layout.tres (spec §18.5).
## The bus layout is written through the engine API rather than by hand: the .tres
## serialisation of AudioBusLayout is an editor format we must not guess at.
## Run: godot4 --headless --path . --script res://tools/audio/make_bus_layout.gd
## Re-run after any change to the mix topology, then commit the .tres.

const OUTPUT := "res://resources/audio/default_bus_layout.tres"

func _init() -> void:
	# Master keeps a gentle compressor then a hard limiter: no clipping, ever.
	AudioServer.set_bus_count(4)

	AudioServer.set_bus_name(0, "Master")
	AudioServer.set_bus_volume_db(0, 0.0)
	for i in range(AudioServer.get_bus_effect_count(0) - 1, -1, -1):
		AudioServer.remove_bus_effect(0, i)
	var compressor := AudioEffectCompressor.new()
	compressor.threshold = -18.0
	compressor.ratio = 3.0
	compressor.attack_us = 20.0
	compressor.release_ms = 250.0
	AudioServer.add_bus_effect(0, compressor)
	var limiter := AudioEffectHardLimiter.new()
	limiter.ceiling_db = -0.5
	AudioServer.add_bus_effect(0, limiter)

	_make_bus(1, "Music", -4.0)
	_make_bus(2, "SFX", 0.0)
	_make_bus(3, "Voice", 0.0)

	var layout := AudioServer.generate_bus_layout()
	var error := ResourceSaver.save(layout, OUTPUT)
	if error != OK:
		printerr("[bus] save failed: %d" % error)
		quit(1)
		return
	print("[bus] wrote %s (%d buses)" % [OUTPUT, AudioServer.bus_count])
	quit(0)

func _make_bus(index: int, bus_name: String, volume_db: float) -> void:
	AudioServer.set_bus_name(index, bus_name)
	AudioServer.set_bus_volume_db(index, volume_db)
	AudioServer.set_bus_send(index, "Master")
	for i in range(AudioServer.get_bus_effect_count(index) - 1, -1, -1):
		AudioServer.remove_bus_effect(index, i)
