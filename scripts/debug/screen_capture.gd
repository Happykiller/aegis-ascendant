class_name ScreenCapture
extends Node
## Debug screenshot helper for the WSL→Windows verification loop.
## Enabled only when `--capture` is present in the user cmdline args
## (after the `++` separator). Waits, saves a PNG next to the executable
## (readable from WSL under /mnt/c/...), then quits. Never active in a normal run.
##
##   --capture-after=N   attend N IMAGES (défaut 150) — cadrage rapide
##   --capture-at=S      attend S SECONDES de jeu — pour viser un évènement de
##                       la vague, dont l'instant est connu en secondes et non
##                       en images (`--capture-at` gagne si les deux sont donnés)

var _frames_left: int = -1
## Alternative en SECONDES de temps de jeu. Compter des images ne permet pas de
## viser un évènement de la vague : le nombre d'images qui s'écoule avant la
## 39e seconde dépend du framerate, donc de la machine et du throttle de
## présentation de Windows. Chercher la bonne valeur coûtait un cycle de
## déploiement complet par essai.
var _seconds_left: float = -1.0
var _path: String = ""

func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if not ("--capture" in args):
		set_process(false)
		return
	_seconds_left = _float_arg(args, "--capture-at", -1.0)
	if _seconds_left < 0.0:
		_frames_left = _int_arg(args, "--capture-after", 150)
	_path = OS.get_executable_path().get_base_dir().path_join("capture.png")
	# GPU render time, not FPS: an unattended Windows session throttles
	# presentation (see the vsync note in docs/BACKLOG.md), which makes frame
	# rate meaningless here. GPU time per frame is measured on the device and
	# stays honest whether or not the window is actually being displayed.
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)
	if _seconds_left >= 0.0:
		print("[ScreenCapture] armed: %.1f s -> %s" % [_seconds_left, _path])
	else:
		print("[ScreenCapture] armed: %d frames -> %s" % [_frames_left, _path])

func _process(delta: float) -> void:
	if _seconds_left >= 0.0:
		_seconds_left -= delta
		if _seconds_left > 0.0:
			return
	elif _frames_left >= 0:
		_frames_left -= 1
		if _frames_left > 0:
			return
	else:
		return
	var image := get_viewport().get_texture().get_image()
	var err := image.save_png(_path)
	var gpu_ms := RenderingServer.viewport_get_measured_render_time_gpu(
		get_viewport().get_viewport_rid())
	print("[ScreenCapture] saved (%d) — GPU %.3f ms/frame: %s" % [err, gpu_ms, _path])
	get_tree().quit(0)

static func _int_arg(args: PackedStringArray, key: String, fallback: int) -> int:
	for arg in args:
		if arg.begins_with(key + "="):
			return int(arg.get_slice("=", 1))
	return fallback

static func _float_arg(args: PackedStringArray, key: String, fallback: float) -> float:
	for arg in args:
		if arg.begins_with(key + "="):
			return float(arg.get_slice("=", 1))
	return fallback
