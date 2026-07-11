class_name ScreenCapture
extends Node
## Debug screenshot helper for the WSL→Windows verification loop.
## Enabled only when `--capture` is present in the user cmdline args
## (after the `++` separator). Waits N frames, saves a PNG next to the
## executable (readable from WSL under /mnt/c/...), then quits.
## Never active in a normal run.

var _frames_left: int = -1
var _path: String = ""

func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if not ("--capture" in args):
		set_process(false)
		return
	_frames_left = _int_arg(args, "--capture-after", 150)
	_path = OS.get_executable_path().get_base_dir().path_join("capture.png")
	print("[ScreenCapture] armed: %d frames -> %s" % [_frames_left, _path])

func _process(_delta: float) -> void:
	if _frames_left < 0:
		return
	_frames_left -= 1
	if _frames_left > 0:
		return
	var image := get_viewport().get_texture().get_image()
	var err := image.save_png(_path)
	print("[ScreenCapture] saved (%d): %s" % [err, _path])
	get_tree().quit(0)

static func _int_arg(args: PackedStringArray, key: String, fallback: int) -> int:
	for arg in args:
		if arg.begins_with(key + "="):
			return int(arg.get_slice("=", 1))
	return fallback
