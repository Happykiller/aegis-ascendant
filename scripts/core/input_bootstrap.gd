class_name InputBootstrap
## Registers gameplay input actions in code (idempotent).
## Rationale: keeps project.godot free of hand-written [input] serialization;
## remapping UI will build on top of these actions later (spec §7.1).

const MOVE_DEADZONE := 0.2

static func register_actions() -> void:
	_add_key_action("move_left", [KEY_A, KEY_LEFT], MOVE_DEADZONE)
	_add_key_action("move_right", [KEY_D, KEY_RIGHT], MOVE_DEADZONE)
	_add_key_action("move_up", [KEY_W, KEY_UP], MOVE_DEADZONE)
	_add_key_action("move_down", [KEY_S, KEY_DOWN], MOVE_DEADZONE)
	_add_key_action("fire_primary", [KEY_SPACE], 0.5)
	_add_key_action("ui_options", [KEY_O], 0.5)

static func _add_key_action(action: StringName, physical_keys: Array, deadzone: float) -> void:
	if InputMap.has_action(action):
		return
	InputMap.add_action(action, deadzone)
	for key: Key in physical_keys:
		var event := InputEventKey.new()
		event.physical_keycode = key
		InputMap.action_add_event(action, event)
