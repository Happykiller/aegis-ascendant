extends CanvasLayer
## Fighter HUD (spec §19.1), arcade retro-pixel refonte. Built in code: four
## corner panels (cyan sharp borders + offset shadow), a segmented shield bar,
## pixel fonts (Press Start 2P labels / VT323 values), ship-icon lives, and a
## low-shield alert blink. Bound by the level to the player and GameState via
## signals. Game logic is untouched — this only draws state.

# --- Palette ------------------------------------------------------------------
const ACCENT := Color("29e6ff")        # cyan
const TEXT_LIGHT := Color("dff6ff")
const SCORE_WHITE := Color("ffffff")
const POWER_ORANGE := Color("ffd23f")
const ALERT_RED := Color("ff3b3b")
const BAR_TRACK := Color("02131a")
const BLOCK_EMPTY := Color("0a2a33")

const MARGIN := 28.0
const SHIELD_BLOCKS := 10
const ALERT_AT := 30.0                 # shield value at/under which the alert blinks
const MAX_LIVES_ICONS := 5

const _LABEL_FONT := preload("res://assets/fonts/PressStart2P.ttf")
const _VALUE_FONT := preload("res://assets/fonts/VT323.ttf")

# --- Runtime nodes ------------------------------------------------------------
var _shield_style: StyleBoxFlat
var _blocks: Array[ColorRect] = []
var _shield_value: Label
var _power_value: Label
var _score_value: Label
var _life_icons: Array[Polygon2D] = []
var _lives_count: Label
var _pickup_targets: Dictionary[int, Label] = {}

var _shield_ratio: float = 1.0
var _shield_current: float = 100.0
var _alert: bool = false
var _alert_time: float = 0.0

# Boss bar + banner (kept from the old HUD, restyled).
var _boss_panel: Panel
var _boss_name: Label
var _boss_fill: ColorRect
var _boss_full_width: float = 0.0
var _banner: Label

func _ready() -> void:
	_build_shield_power_panel()
	_build_score_panel()
	_build_lives_panel()
	_build_boss_panel()
	_build_banner()
	set_process(true)

# --- Builders -----------------------------------------------------------------

func _panel(anchor: Vector2, offset: Vector2, size: Vector2, border: Color = ACCENT) -> Panel:
	var panel := Panel.new()
	panel.anchor_left = anchor.x
	panel.anchor_right = anchor.x
	panel.anchor_top = anchor.y
	panel.anchor_bottom = anchor.y
	# offset.x < 0 anchors from the right edge, offset.y < 0 from the bottom.
	panel.offset_left = offset.x if anchor.x == 0.0 else offset.x - size.x
	panel.offset_right = offset.x + size.x if anchor.x == 0.0 else offset.x
	panel.offset_top = offset.y if anchor.y == 0.0 else offset.y - size.y
	panel.offset_bottom = offset.y + size.y if anchor.y == 0.0 else offset.y
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.024, 0.039, 0.078, 0.82) # #060A14 @ 82%
	style.border_color = border
	style.set_border_width_all(3)
	style.set_corner_radius_all(0)
	style.shadow_color = Color(border.r, border.g, border.b, 0.25)
	style.shadow_size = 0
	style.shadow_offset = Vector2(4, 4)
	panel.add_theme_stylebox_override("panel", style)
	add_child(panel)
	panel.set_meta("style", style)
	return panel

func _label(parent: Node, text: String, font: FontFile, size: int, color: Color,
		pos: Vector2, width: float = 400.0, align: int = HORIZONTAL_ALIGNMENT_LEFT) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_override("font", font)
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
	label.horizontal_alignment = align
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.position = pos
	label.size = Vector2(width, size + 8)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(label)
	return label

## Small pixel diamond (the pickup-guide marker for a stat: cyan = shield/score,
## orange = power). Drawn, so its size is exact — the SVG pickup icons rendered
## far too large in the panel.
func _diamond(parent: Node, color: Color, center: Vector2, r: float) -> Polygon2D:
	var d := Polygon2D.new()
	d.polygon = PackedVector2Array([Vector2(0, -r), Vector2(r * 0.7, 0), Vector2(0, r), Vector2(-r * 0.7, 0)])
	d.color = color
	d.position = center
	parent.add_child(d)
	return d

func _build_shield_power_panel() -> void:
	var panel := _panel(Vector2(0, 0), Vector2(MARGIN, MARGIN), Vector2(430, 150))
	_shield_style = panel.get_meta("style") as StyleBoxFlat
	# SHIELD row
	_diamond(panel, ACCENT, Vector2(24, 24), 9)
	_label(panel, "SHIELD", _LABEL_FONT, 16, ACCENT, Vector2(44, 14))
	# segmented bar
	var bar_x := 16.0
	var bar_y := 48.0
	var bar_w := 300.0
	var gap := 3.0
	var block_w := (bar_w - gap * float(SHIELD_BLOCKS - 1)) / float(SHIELD_BLOCKS)
	var track := ColorRect.new()
	track.color = BAR_TRACK
	track.position = Vector2(bar_x - 2, bar_y - 2)
	track.size = Vector2(bar_w + 4, 24)
	track.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(track)
	for i in SHIELD_BLOCKS:
		var block := ColorRect.new()
		block.color = ACCENT
		block.position = Vector2(bar_x + float(i) * (block_w + gap), bar_y)
		block.size = Vector2(block_w, 20)
		block.mouse_filter = Control.MOUSE_FILTER_IGNORE
		panel.add_child(block)
		_blocks.append(block)
	_shield_value = _label(panel, "100", _VALUE_FONT, 30, ACCENT, Vector2(bar_x + bar_w + 12, bar_y - 8), 90)
	# POWER row
	_diamond(panel, POWER_ORANGE, Vector2(24, 112), 9)
	_label(panel, "POWER", _LABEL_FONT, 15, POWER_ORANGE, Vector2(44, 102))
	_power_value = _label(panel, "LV.1", _VALUE_FONT, 26, POWER_ORANGE, Vector2(190, 98), 120)
	_pickup_targets[Pickup.Kind.SHIELD] = _shield_value
	_pickup_targets[Pickup.Kind.POWER] = _power_value

func _build_score_panel() -> void:
	var panel := _panel(Vector2(1, 0), Vector2(-MARGIN, MARGIN), Vector2(430, 130))
	_label(panel, "SCORE", _LABEL_FONT, 15, TEXT_LIGHT, Vector2(16, 18), 398, HORIZONTAL_ALIGNMENT_RIGHT)
	_score_value = _label(panel, "00000000", _VALUE_FONT, 58, SCORE_WHITE, Vector2(16, 48), 398,
		HORIZONTAL_ALIGNMENT_RIGHT)
	_score_value.add_theme_constant_override("outline_size", 0)
	_score_value.add_theme_color_override("font_shadow_color", Color(ACCENT.r, ACCENT.g, ACCENT.b, 0.55))
	_score_value.add_theme_constant_override("shadow_offset_x", 0)
	_score_value.add_theme_constant_override("shadow_offset_y", 0)
	_score_value.add_theme_constant_override("shadow_outline_size", 6)
	_pickup_targets[Pickup.Kind.SCORE] = _score_value

func _build_lives_panel() -> void:
	var panel := _panel(Vector2(0, 1), Vector2(MARGIN, -MARGIN), Vector2(360, 72))
	_label(panel, "FIGHTERS", _LABEL_FONT, 15, ACCENT, Vector2(16, 26))
	var ix := 200.0
	for i in MAX_LIVES_ICONS:
		var ship := Polygon2D.new()
		ship.polygon = PackedVector2Array([Vector2(9, 2), Vector2(17, 22), Vector2(9, 17), Vector2(1, 22)])
		ship.color = ACCENT
		ship.position = Vector2(ix + float(i) * 24.0, 22)
		panel.add_child(ship)
		_life_icons.append(ship)
	_lives_count = _label(panel, "x3", _VALUE_FONT, 26, ACCENT, Vector2(ix + MAX_LIVES_ICONS * 24.0 + 6, 22), 80)

func _build_boss_panel() -> void:
	_boss_panel = _panel(Vector2(0.5, 0), Vector2(-400, MARGIN), Vector2(800, 58),
		Color("d93d9c"))
	_boss_panel.visible = false
	_boss_name = _label(_boss_panel, "BOSS", _LABEL_FONT, 18, Color("f16bc0"), Vector2(0, 8), 800,
		HORIZONTAL_ALIGNMENT_CENTER)
	var bg := ColorRect.new()
	bg.color = Color(0.09, 0.03, 0.07, 0.7)
	bg.position = Vector2(12, 36)
	bg.size = Vector2(776, 12)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_boss_panel.add_child(bg)
	_boss_fill = ColorRect.new()
	_boss_fill.color = Color("d93d9c")
	_boss_fill.position = Vector2(14, 38)
	_boss_fill.size = Vector2(772, 8)
	_boss_fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_boss_panel.add_child(_boss_fill)
	_boss_full_width = 772.0

func _build_banner() -> void:
	_banner = Label.new()
	_banner.add_theme_font_override("font", _LABEL_FONT)
	_banner.add_theme_font_size_override("font_size", 56)
	_banner.add_theme_color_override("font_color", ACCENT)
	_banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_banner.anchor_left = 0.0
	_banner.anchor_right = 1.0
	_banner.anchor_top = 0.5
	_banner.anchor_bottom = 0.5
	_banner.offset_top = -60
	_banner.offset_bottom = 60
	_banner.modulate = Color(1, 1, 1, 0)
	_banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_banner)

# --- Public API (unchanged for the level director) ----------------------------

func bind_player(player: PlayerFighterController) -> void:
	player.shield_changed.connect(_on_shield_changed)
	player.lives_changed.connect(_on_lives_changed)
	player.power_changed.connect(_on_power_changed)

func bind_score(gs: Object) -> void:
	gs.score_changed.connect(_on_score_changed)
	_on_score_changed(gs.score)

func show_boss(display_name: String) -> void:
	_boss_name.text = display_name.to_upper()
	_boss_fill.size.x = _boss_full_width
	_boss_panel.visible = true

func hide_boss() -> void:
	_boss_panel.visible = false

func set_boss_health(ratio: float) -> void:
	_boss_fill.size.x = _boss_full_width * clampf(ratio, 0.0, 1.0)

func show_banner(text: String, color: Color = ACCENT, hold: float = 1.6) -> void:
	_banner.text = text
	_banner.add_theme_color_override("font_color", color)
	var tween := create_tween()
	tween.tween_property(_banner, "modulate:a", 1.0, 0.35)
	tween.tween_interval(hold)
	tween.tween_property(_banner, "modulate:a", 0.0, 0.5)

## Briefly punch the value a pickup just changed, so the gain is noticed.
func pulse_pickup(kind: int) -> void:
	var label: Label = _pickup_targets.get(kind)
	if label == null:
		return
	label.pivot_offset = label.size * 0.5
	label.scale = Vector2(1.4, 1.4)
	var tween := create_tween()
	tween.set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	tween.tween_property(label, "scale", Vector2.ONE, 0.35)

# --- Signal handlers ----------------------------------------------------------

func _on_shield_changed(ratio: float, current: float, _maximum: float) -> void:
	_shield_ratio = ratio
	_shield_current = current
	_shield_value.text = "%d" % roundi(current)
	var filled := roundi(current / 10.0)
	var alert := current <= ALERT_AT
	for i in _blocks.size():
		if i < filled:
			_blocks[i].color = ALERT_RED if alert else ACCENT
		else:
			_blocks[i].color = BLOCK_EMPTY
	if alert != _alert:
		_alert = alert
		_alert_time = 0.0
		if not alert:
			_shield_value.add_theme_color_override("font_color", ACCENT)
			_shield_style.border_color = ACCENT

func _on_power_changed(level: int) -> void:
	_power_value.text = "LV.%d" % level

func _on_score_changed(total: int) -> void:
	_score_value.text = "%08d" % total

func _on_lives_changed(lives: int) -> void:
	_lives_count.text = "x%d" % maxi(lives, 0)
	for i in _life_icons.size():
		_life_icons[i].visible = i < lives

# --- Alert blink --------------------------------------------------------------

func _process(delta: float) -> void:
	if not _alert:
		return
	_alert_time += delta
	# ~1s blink: on for the first half, off for the second.
	var on := fmod(_alert_time, 1.0) < 0.5
	var col := ALERT_RED if on else Color(ALERT_RED.r, ALERT_RED.g, ALERT_RED.b, 0.25)
	_shield_style.border_color = col
	_shield_value.add_theme_color_override("font_color", ALERT_RED if on else BAR_TRACK)
	var filled := roundi(_shield_current / 10.0)
	for i in _blocks.size():
		if i < filled:
			_blocks[i].color = ALERT_RED if on else Color(ALERT_RED.r, ALERT_RED.g, ALERT_RED.b, 0.35)
