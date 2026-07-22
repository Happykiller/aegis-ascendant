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
	# Bestiaire. Actions DÉDIÉES et non un recyclage de `move_*` : les flèches y
	# changent de coque pendant que A/D/W/S font tourner le présentoir, alors que
	# `move_left` porte déjà A ET Flèche gauche. Réutiliser aurait lié les deux
	# gestes à la même touche, sans moyen de les séparer plus tard.
	_add_key_action("codex_prev", [KEY_LEFT], 0.5)
	_add_key_action("codex_next", [KEY_RIGHT], 0.5)
	_add_key_action("codex_yaw_left", [KEY_A], MOVE_DEADZONE)
	_add_key_action("codex_yaw_right", [KEY_D], MOVE_DEADZONE)
	_add_key_action("codex_pitch_up", [KEY_W], MOVE_DEADZONE)
	_add_key_action("codex_pitch_down", [KEY_S], MOVE_DEADZONE)
	_add_key_action("codex_zoom_in", [KEY_EQUAL, KEY_KP_ADD], MOVE_DEADZONE)
	_add_key_action("codex_zoom_out", [KEY_MINUS, KEY_KP_SUBTRACT], MOVE_DEADZONE)
	_add_key_action("codex_reset", [KEY_R], 0.5)

static func _add_key_action(action: StringName, physical_keys: Array, deadzone: float) -> void:
	if InputMap.has_action(action):
		return
	InputMap.add_action(action, deadzone)
	for key: Key in physical_keys:
		var event := InputEventKey.new()
		event.physical_keycode = key
		InputMap.action_add_event(action, event)
