extends "res://tests/test_case.gd"
## Les liaisons d'entrée (spec §7.1, §7.2).
##
## Ce que ce fichier garde n'est pas la disposition — c'est un goût, elle bougera. Ce sont
## les deux choses qu'un ajout d'action peut casser sans qu'aucun test ne rougisse :
##   1. une action de jeu livrée MANCHOTE, jouable au clavier et pas à la manette. C'est
##      exactement l'état dans lequel le jeu a vécu jusqu'au 2026-08-27 ;
##   2. l'axe vertical REPRIS À L'ENVERS. Il l'a déjà été une fois (backlog du 12/07), et
##      l'axe Y d'une manette est négatif vers le haut — l'occasion se représente ici.

const GAMEPLAY_ACTIONS: Array[StringName] = [
	&"move_left", &"move_right", &"move_up", &"move_down", &"fire_primary",
]

const CODEX_ACTIONS: Array[StringName] = [
	&"codex_prev", &"codex_next", &"codex_yaw_left", &"codex_yaw_right",
	&"codex_pitch_up", &"codex_pitch_down", &"codex_zoom_in", &"codex_zoom_out",
	&"codex_reset",
]

func _kinds(action: StringName) -> Dictionary:
	var keys := 0
	var pads := 0
	for event in InputMap.action_get_events(action):
		if event is InputEventKey:
			keys += 1
		elif event is InputEventJoypadButton or event is InputEventJoypadMotion:
			pads += 1
	return {"keys": keys, "pads": pads}

func test_every_gameplay_action_answers_to_both_devices() -> void:
	InputBootstrap.register_actions()
	for action in GAMEPLAY_ACTIONS:
		assert_true(InputMap.has_action(action), "%s est déclarée" % action)
		var kinds := _kinds(action)
		assert_true(int(kinds["keys"]) > 0, "%s a une touche" % action)
		assert_true(int(kinds["pads"]) > 0, "%s a une liaison manette" % action)

func test_the_bestiary_is_reachable_without_a_keyboard() -> void:
	# Le codex n'écoute AUCUNE action `ui_*` : sans liaisons propres, il restait le seul
	# écran du jeu qu'une manette ne pouvait pas piloter.
	InputBootstrap.register_actions()
	for action in CODEX_ACTIONS:
		var kinds := _kinds(action)
		assert_true(int(kinds["pads"]) > 0, "%s a une liaison manette" % action)

## LA garde d'orientation. Sur une manette, l'axe Y est NÉGATIF vers le haut : monter à
## l'écran, c'est `axis_value < 0`. Une inversion ici ne casse aucun autre test.
func test_pushing_the_stick_up_moves_up() -> void:
	InputBootstrap.register_actions()
	var up := _axis_value(&"move_up", JOY_AXIS_LEFT_Y)
	var down := _axis_value(&"move_down", JOY_AXIS_LEFT_Y)
	assert_true(up < 0.0, "stick vers le haut (%.1f) = monter" % up)
	assert_true(down > 0.0, "stick vers le bas (%.1f) = descendre" % down)
	var left := _axis_value(&"move_left", JOY_AXIS_LEFT_X)
	var right := _axis_value(&"move_right", JOY_AXIS_LEFT_X)
	assert_true(left < 0.0, "stick à gauche (%.1f) = aller à gauche" % left)
	assert_true(right > 0.0, "stick à droite (%.1f) = aller à droite" % right)

func _axis_value(action: StringName, axis: JoyAxis) -> float:
	for event in InputMap.action_get_events(action):
		var motion := event as InputEventJoypadMotion
		if motion != null and motion.axis == axis:
			return motion.axis_value
	fail("%s n'est liée à aucun mouvement de l'axe %d" % [action, axis])
	return 0.0

## `register_actions()` s'annonce idempotente en tête de fichier. Elle est appelée au
## démarrage, et le sera à chaque rechargement d'un futur écran de remappage.
func test_registering_twice_does_not_double_the_bindings() -> void:
	InputBootstrap.register_actions()
	var before := _kinds(&"fire_primary")
	InputBootstrap.register_actions()
	var after := _kinds(&"fire_primary")
	assert_eq(after["keys"], before["keys"], "aucune touche en double")
	assert_eq(after["pads"], before["pads"], "aucune liaison manette en double")
