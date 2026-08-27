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
	_register_joypad()


## Manette — disposition Xbox de référence (spec §7.2).
##
## ⚠️ CE QUI MARCHAIT DÉJÀ, et qu'il ne faut pas refaire : `project.godot` ne porte
## AUCUNE section `[input]`, donc les actions intégrées `ui_accept`, `ui_cancel` et les
## quatre `ui_*` directionnelles gardent les liaisons par défaut du moteur — croix
## directionnelle, stick gauche, A et B. Les menus, la pause et le rapport de mission se
## naviguaient donc à la manette avant ce code. Ce qui manquait, c'est **le jeu lui-même**
## et **le bestiaire**, qui n'emploient que des actions maison.
static func _register_joypad() -> void:
	# Déplacement — stick gauche. Rien à changer côté joueur : le contrôleur lit
	# `Input.get_vector(...)`, qui rend l'analogique et applique le deadzone de l'action.
	_add_axis("move_left", JOY_AXIS_LEFT_X, -1.0)
	_add_axis("move_right", JOY_AXIS_LEFT_X, 1.0)
	# ⚠️ L'axe Y d'une manette est NÉGATIF vers le haut. L'axe vertical du jeu a déjà été
	# inversé une fois par erreur (backlog du 12/07) ; c'est ici qu'on le paierait deux fois.
	_add_axis("move_up", JOY_AXIS_LEFT_Y, -1.0)
	_add_axis("move_down", JOY_AXIS_LEFT_Y, 1.0)
	# Tir — A ET gâchette droite, les deux que la spec nomme.
	_add_button("fire_primary", JOY_BUTTON_A)
	_add_axis("fire_primary", JOY_AXIS_TRIGGER_RIGHT, 1.0)
	# Pause — le bouton Menu, comme le demande la spec. Elle est portée par `ui_cancel`
	# dans ce jeu (pause_screen.gd), donc c'est cette action qu'on complète.
	# ⚠️ Effet de bord assumé : Menu devient aussi un « retour » dans les écrans, à côté de B.
	_add_button("ui_cancel", JOY_BUTTON_START)
	# Options : aucune ligne dans la spec côté manette, et le bouton OPTIONS du menu de
	# pause est déjà atteignable au stick. Ce raccourci est un confort — sur View, et NON
	# sur Y, que la spec réserve à l'Overdrive.
	_add_button("ui_options", JOY_BUTTON_BACK)
	# Bestiaire — stick DROIT pour la coque, gâchettes pour le zoom, tranches pour changer
	# de fiche. Le stick gauche est laissé libre : la croix et lui pilotent déjà `ui_*`.
	# ⚠️ Le zoom partage la gâchette droite avec le tir. Sans conséquence — les deux écrans
	# ne coexistent jamais — mais c'est à savoir avant d'ajouter une arme sur LT.
	_add_axis("codex_yaw_left", JOY_AXIS_RIGHT_X, -1.0)
	_add_axis("codex_yaw_right", JOY_AXIS_RIGHT_X, 1.0)
	_add_axis("codex_pitch_up", JOY_AXIS_RIGHT_Y, -1.0)
	_add_axis("codex_pitch_down", JOY_AXIS_RIGHT_Y, 1.0)
	_add_axis("codex_zoom_in", JOY_AXIS_TRIGGER_RIGHT, 1.0)
	_add_axis("codex_zoom_out", JOY_AXIS_TRIGGER_LEFT, 1.0)
	_add_button("codex_prev", JOY_BUTTON_LEFT_SHOULDER)
	_add_button("codex_next", JOY_BUTTON_RIGHT_SHOULDER)
	_add_button("codex_reset", JOY_BUTTON_RIGHT_STICK)

static func _add_key_action(action: StringName, physical_keys: Array, deadzone: float) -> void:
	if InputMap.has_action(action):
		return
	InputMap.add_action(action, deadzone)
	for key: Key in physical_keys:
		var event := InputEventKey.new()
		event.physical_keycode = key
		InputMap.action_add_event(action, event)


## Une direction d'axe. `value` vaut -1 ou +1 : c'est le SIGNE qui distingue les deux
## moitiés d'un même axe, et Godot rend la magnitude analogique par-dessus.
static func _add_axis(action: StringName, axis: JoyAxis, value: float) -> void:
	if not InputMap.has_action(action):
		push_warning("[Input] action inconnue: %s" % action)
		return
	for existing in InputMap.action_get_events(action):
		var motion := existing as InputEventJoypadMotion
		if motion != null and motion.axis == axis and signf(motion.axis_value) == signf(value):
			return # déjà liée : `register_actions()` reste idempotent
	var event := InputEventJoypadMotion.new()
	event.axis = axis
	event.axis_value = value
	InputMap.action_add_event(action, event)


static func _add_button(action: StringName, button: JoyButton) -> void:
	if not InputMap.has_action(action):
		push_warning("[Input] action inconnue: %s" % action)
		return
	for existing in InputMap.action_get_events(action):
		var pressed := existing as InputEventJoypadButton
		if pressed != null and pressed.button_index == button:
			return
	var event := InputEventJoypadButton.new()
	event.button_index = button
	InputMap.action_add_event(action, event)
