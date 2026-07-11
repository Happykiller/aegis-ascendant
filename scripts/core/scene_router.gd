extends Node
## Scene navigation (autoload "SceneRouter"). Central, logged, error-checked.

func goto_scene(path: String) -> void:
	if not ResourceLoader.exists(path, "PackedScene"):
		push_error("[SceneRouter] scene not found: %s" % path)
		return
	print("[SceneRouter] -> %s" % path)
	var err := get_tree().change_scene_to_file(path)
	if err != OK:
		push_error("[SceneRouter] change_scene_to_file failed (%d): %s" % [err, path])
