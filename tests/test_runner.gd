extends SceneTree
## Headless test runner (spec §28.1). Run with:
##   godot4 --headless --path . --script res://tests/test_runner.gd
## 1) Parse-checks every .gd under the source roots (load() == null -> failure).
## 2) Discovers tests/unit/test_*.gd, runs every test_* method, accumulates
##    assertion failures, prints a summary and exits non-zero on any failure.
## NOTE: autoloads are NOT mounted in --script mode; tests must instantiate
## their units by hand.

const SOURCE_ROOTS: PackedStringArray = ["res://scripts", "res://resources", "res://tests"]
const UNIT_DIR := "res://tests/unit"

func _init() -> void:
	var parse_failures := _parse_check_all()
	var result := _run_unit_tests()
	var total_failures: int = parse_failures + result.failures
	print("")
	print("=== %d test method(s), %d assertion(s), %d failure(s), %d parse error(s) ===" %
		[result.methods, result.asserts, result.failures, parse_failures])
	quit(1 if total_failures > 0 else 0)

func _parse_check_all() -> int:
	var failures := 0
	for root in SOURCE_ROOTS:
		for path in _collect_gd_files(root):
			var script: Variant = load(path)
			if script == null or not (script as GDScript).can_instantiate():
				printerr("[parse] FAILED to load: %s" % path)
				failures += 1
	return failures

func _collect_gd_files(root: String) -> PackedStringArray:
	var found := PackedStringArray()
	if not DirAccess.dir_exists_absolute(root):
		return found
	for file in DirAccess.get_files_at(root):
		if file.ends_with(".gd"):
			found.append(root.path_join(file))
	for dir in DirAccess.get_directories_at(root):
		found.append_array(_collect_gd_files(root.path_join(dir)))
	return found

func _run_unit_tests() -> Dictionary:
	var methods := 0
	var asserts := 0
	var failures := 0
	if not DirAccess.dir_exists_absolute(UNIT_DIR):
		return {"methods": 0, "asserts": 0, "failures": 0}
	var files := DirAccess.get_files_at(UNIT_DIR)
	for file in files:
		if not (file.begins_with("test_") and file.ends_with(".gd")):
			continue
		var script: Variant = load(UNIT_DIR.path_join(file))
		if script == null:
			printerr("[test] FAILED to load: %s" % file)
			failures += 1
			continue
		for method in (script as GDScript).get_script_method_list():
			var name: String = method["name"]
			if not name.begins_with("test_"):
				continue
			var case: RefCounted = (script as GDScript).new()
			case.call(name)
			methods += 1
			asserts += case.assert_count
			if case.failures.is_empty():
				print("[PASS] %s :: %s" % [file, name])
			else:
				failures += case.failures.size()
				for failure_message: String in case.failures:
					printerr("[FAIL] %s :: %s — %s" % [file, name, failure_message])
	return {"methods": methods, "asserts": asserts, "failures": failures}
