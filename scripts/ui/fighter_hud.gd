extends CanvasLayer
## Fighter HUD (spec §19.1): shield, power level, score, lives.
## Bound by the gameplay root to the player and GameState via signals.

const COLOR_FULL := Color(0.247, 0.851, 0.91)   # cyan
const COLOR_MID := Color(0.894, 0.71, 0.29)     # gold
const COLOR_LOW := Color(0.79, 0.23, 0.19)      # red

@onready var _shield_fill: ColorRect = %ShieldFill
@onready var _shield_value: Label = %ShieldValue
@onready var _score_value: Label = %ScoreValue
@onready var _lives_value: Label = %LivesValue
@onready var _power_value: Label = %PowerValue
@onready var _boss_panel: Control = %BossPanel
@onready var _boss_name: Label = %BossName
@onready var _boss_fill: ColorRect = %BossBarFill

var _shield_full_width: float = 0.0
var _boss_full_width: float = 0.0

func _ready() -> void:
	_shield_full_width = _shield_fill.size.x
	_boss_full_width = _boss_fill.size.x

func show_boss(display_name: String) -> void:
	_boss_name.text = display_name.to_upper()
	_boss_fill.size.x = _boss_full_width
	_boss_panel.visible = true

func hide_boss() -> void:
	_boss_panel.visible = false

func set_boss_health(ratio: float) -> void:
	_boss_fill.size.x = _boss_full_width * clampf(ratio, 0.0, 1.0)

func bind_player(player: PlayerFighterController) -> void:
	player.shield_changed.connect(_on_shield_changed)
	player.lives_changed.connect(_on_lives_changed)
	player.power_changed.connect(_on_power_changed)

func bind_score(gs: Object) -> void:
	gs.score_changed.connect(_on_score_changed)
	_on_score_changed(gs.score)

func _on_shield_changed(ratio: float, current: float, _maximum: float) -> void:
	_shield_fill.size.x = _shield_full_width * clampf(ratio, 0.0, 1.0)
	var col := COLOR_FULL if ratio > 0.5 else (COLOR_MID if ratio > 0.25 else COLOR_LOW)
	_shield_fill.color = col
	_shield_value.text = "%d" % roundi(current)

func _on_score_changed(total: int) -> void:
	_score_value.text = "%08d" % total

func _on_lives_changed(lives: int) -> void:
	_lives_value.text = "x%d" % maxi(lives, 0)

func _on_power_changed(level: int) -> void:
	_power_value.text = "LV.%d" % level
