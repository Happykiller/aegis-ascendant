extends CanvasLayer
## Victory / results overlay (spec §14.3). Shows the final score and a rank,
## then replays on accept.

func setup(score: int) -> void:
	%ScoreValue.text = "%08d" % score
	%RankValue.text = _rank(score)

func _ready() -> void:
	pass

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		get_node("/root/GameState").reset_session()
		get_tree().reload_current_scene()

static func _rank(score: int) -> String:
	if score >= 40000:
		return "S"
	if score >= 25000:
		return "A"
	if score >= 12000:
		return "B"
	return "C"
