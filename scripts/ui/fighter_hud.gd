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

const BOSS_MAGENTA := Color("d93d9c")
## Jauges d'appendice du Choir Harvester. Trois, comme la planche.
const LIMB_PIPS := 3
## Le Pale Leviathan en montre jusqu'à QUATRE (plaques, épines). On construit ce maximum
## et `set_boss_limbs` recentre la rangée sur le nombre réellement utilisé — sinon les
## trois du Harvester, centrées pour trois, se décaleraient sous un bandeau centré.
const MAX_LIMB_PIPS := 4
## Couleur d'une jauge à terre : sombre mais pas noire, sinon elle disparaît du panneau
## et l'on ne compte plus que ce qui reste, pas ce qui manque.
const LIMB_PIP_DOWN := Color(0.25, 0.08, 0.18, 0.85)
## Noms des appendices, dans l'ordre de `HarvesterCombat.LIMB_ORDER`.
##
## ⚠️ Écrits ici et non lus du module : le HUD ne connaît AUCUN boss en particulier
## (`show_boss` sert aussi le Pale Leviathan). Le couplage se fait par l'indice, que le
## niveau relaie — pas par un `preload` du combat dans l'interface.
const LIMB_LABELS: PackedStringArray = ["FAUX", "GRIFFE", "CANON"]
const LIMB_GAUGE_WIDTH := 92.0
const LIMB_GAUGE_HEIGHT := 7.0
const LIMB_LABEL_WIDTH := 58.0
const LIMB_GAUGE_GAP := 44.0

const MARGIN := 28.0
const SHIELD_BLOCKS := 10
const ALERT_AT := 30.0                 # shield value at/under which the alert blinks
const MAX_LIVES_ICONS := 5

const _LABEL_FONT := preload("res://assets/fonts/PressStart2P.ttf")
const _VALUE_FONT := preload("res://assets/fonts/VT323.ttf")
const _PICKUP_POWER := preload("res://assets/imported/sprites/pickups/power_core.svg")
const _PICKUP_SHIELD := preload("res://assets/imported/sprites/pickups/shield_cell.svg")
const _PICKUP_SCORE := preload("res://assets/imported/sprites/pickups/score_prism.svg")

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
var _limb_pips: Array[ColorRect] = []
var _limb_tracks: Array[ColorRect] = []
var _limb_labels: Array[Label] = []
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
	# `offset` is measured FROM the anchor: at anchor 1 it grows leftwards/upwards
	# (the panel hangs off the far edge), everywhere else it grows the natural way.
	#
	# ⚠️ La condition portait sur `anchor.x == 0.0`, donc l'ancre CENTRALE tombait dans
	# la branche « bord droit ». Le bandeau de boss, seul panneau ancré à 0,5 avec un
	# offset de -400 pour se centrer sur 800 px de large, s'étalait en fait de
	# centre-1200 à centre-400 : il sortait du cadre par la gauche et venait se poser
	# sur la jauge de bouclier. Le défaut ne se voyait qu'une fois le mini-boss atteint,
	# c'est-à-dire jamais pendant le développement.
	var from_right := is_equal_approx(anchor.x, 1.0)
	var from_bottom := is_equal_approx(anchor.y, 1.0)
	panel.offset_left = offset.x - size.x if from_right else offset.x
	panel.offset_right = offset.x if from_right else offset.x + size.x
	panel.offset_top = offset.y - size.y if from_bottom else offset.y
	panel.offset_bottom = offset.y if from_bottom else offset.y + size.y
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

## The actual pickup icon, placed in front of the stat it fills — the guide/reminder
## the player recalls at a glance. Offset-based sizing so the SVG renders at the
## intended size in the panel (setting .size directly rendered it far too large).
func _pickup_icon(parent: Node, tex: Texture2D, pos: Vector2, side: float) -> TextureRect:
	var rect := TextureRect.new()
	rect.texture = tex
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	rect.offset_left = pos.x
	rect.offset_top = pos.y
	rect.offset_right = pos.x + side
	rect.offset_bottom = pos.y + side
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(rect)
	return rect

func _build_shield_power_panel() -> void:
	var panel := _panel(Vector2(0, 0), Vector2(MARGIN, MARGIN), Vector2(430, 150))
	_shield_style = panel.get_meta("style") as StyleBoxFlat
	# SHIELD row — the shield pickup icon leads the indicator (guide).
	_pickup_icon(panel, _PICKUP_SHIELD, Vector2(12, 10), 28)
	_label(panel, "SHIELD", _LABEL_FONT, 16, ACCENT, Vector2(48, 14))
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
	# POWER row — the power pickup icon leads the indicator.
	_pickup_icon(panel, _PICKUP_POWER, Vector2(12, 96), 28)
	_label(panel, "POWER", _LABEL_FONT, 15, POWER_ORANGE, Vector2(48, 102))
	_power_value = _label(panel, "LV.1", _VALUE_FONT, 26, POWER_ORANGE, Vector2(190, 98), 120)
	_pickup_targets[Pickup.Kind.SHIELD] = _shield_value
	_pickup_targets[Pickup.Kind.POWER] = _power_value

func _build_score_panel() -> void:
	var panel := _panel(Vector2(1, 0), Vector2(-MARGIN, MARGIN), Vector2(430, 130))
	_label(panel, "SCORE", _LABEL_FONT, 15, TEXT_LIGHT, Vector2(16, 18), 398, HORIZONTAL_ALIGNMENT_RIGHT)
	# The score pickup icon sits to the left of the score value (guide).
	_pickup_icon(panel, _PICKUP_SCORE, Vector2(16, 50), 40)
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
	# 76 px et non 58 : les trois jauges d'appendice vivent sous la barre du noyau.
	_boss_panel = _panel(Vector2(0.5, 0), Vector2(-400, MARGIN), Vector2(800, 76),
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
	_build_limb_pips()

## Trois jauges d'appendice nommées, sous la barre du boss.
##
## POURQUOI — le Choir Harvester n'est vulnérable QUE lorsque ses trois appendices sont
## à terre EN MÊME TEMPS. Trois pastilles allumée/éteinte disaient combien il en restait,
## jamais combien il restait à chacun : le joueur ne pouvait pas savoir s'il valait mieux
## finir le bras entamé ou changer de cible, alors que c'est exactement l'arbitrage du
## combat (la fenêtre vaut le délai de repousse moins le temps d'enchaîner les deux
## autres). Le temps de repousse, lui, se lit toujours sur le modèle : l'appendice se
## redéploie à vue, et n'a donc pas besoin de jauge.
##
## ⚠️ Pas un caractère de remplissage : Press Start 2P n'a ni `●` ni `■` (ADR-0012).
## Ce sont des `ColorRect`, comme la pastille COMMS de l'accueil.
func _build_limb_pips() -> void:
	_limb_pips.clear()
	_limb_tracks.clear()
	_limb_labels.clear()
	# Centrage de la RANGÉE, pas de chaque colonne : un pas de « largeur + marge » posé
	# depuis le milieu décale l'ensemble d'une demi-marge vers la gauche, et la rangée
	# se retrouve visiblement décentrée sous un titre, lui, centré. On compose donc la
	# largeur réelle (libellé + jauge, trois fois, deux intervalles) et on la centre.
	var unit := LIMB_LABEL_WIDTH + LIMB_GAUGE_WIDTH
	var span := unit + LIMB_GAUGE_GAP
	var left := 400.0 - (unit * LIMB_PIPS + LIMB_GAUGE_GAP * (LIMB_PIPS - 1)) * 0.5
	# On bâtit MAX_LIMB_PIPS pastilles, centrées ICI pour les trois du Harvester (défaut) :
	# la quatrième est posée à droite et reste cachée jusqu'à ce que `set_boss_limbs`
	# recentre la rangée pour un boss qui l'utilise.
	for i in MAX_LIMB_PIPS:
		var x := left + float(i) * span
		var text := LIMB_LABELS[i] if i < LIMB_LABELS.size() else ""
		# Le libellé est centré verticalement sur SA hauteur (`size + 8`), pas sur la
		# barre : on le remonte de la moitié de l'écart pour que les deux s'alignent.
		_limb_labels.append(_label(_boss_panel, text, _LABEL_FONT, 9,
			Color("f16bc0"), Vector2(x, 49), LIMB_LABEL_WIDTH))
		var track := ColorRect.new()
		track.color = BAR_TRACK
		track.position = Vector2(x + LIMB_LABEL_WIDTH, 50.0)
		track.size = Vector2(LIMB_GAUGE_WIDTH, LIMB_GAUGE_HEIGHT)
		track.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_boss_panel.add_child(track)
		_limb_tracks.append(track)
		var fill := ColorRect.new()
		fill.color = BOSS_MAGENTA
		fill.position = Vector2(x + LIMB_LABEL_WIDTH, 50.0)
		fill.size = Vector2(LIMB_GAUGE_WIDTH, LIMB_GAUGE_HEIGHT)
		fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_boss_panel.add_child(fill)
		_limb_pips.append(fill)

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

## ⚠️ Cache les jauges d'appendice : `show_boss` sert TOUS les boss, et seul le
## Harvester en a. C'est son module qui les rallume, après son montage.
func show_boss(display_name: String) -> void:
	for pip in _limb_pips:
		pip.visible = false
	for label in _limb_labels:
		label.visible = false
	for track in _limb_tracks:
		track.visible = false
	_boss_name.text = display_name.to_upper()
	_boss_fill.size.x = _boss_full_width
	_boss_panel.visible = true

func hide_boss() -> void:
	_boss_panel.visible = false

## Pose la jauge d'UN appendice, et la REND VISIBLE : les trois sont cachées par défaut,
## parce qu'un boss générique — le Pale Leviathan — n'a pas d'appendices et afficherait
## sinon trois barres mortes qui ne veulent rien dire.
##
## `alive` n'est pas déductible de `ratio` : un appendice qui vient de tomber et un
## appendice en train de repousser sont tous deux à zéro, mais seul le second reviendra.
## La couleur les sépare.
func set_boss_limb(index: int, ratio: float, alive: bool) -> void:
	if index < 0 or index >= _limb_pips.size():
		return
	if index < _limb_labels.size():
		_limb_labels[index].visible = true
	if index < _limb_tracks.size():
		_limb_tracks[index].visible = true
	var fill := _limb_pips[index]
	fill.visible = true
	fill.color = BOSS_MAGENTA if alive else LIMB_PIP_DOWN
	# ⚠️ Un appendice à terre garde une barre PLEINE, en sombre. Le laisser à sa part de
	# structure (zéro) le ferait disparaître : la jauge dirait « rien ici » là où il faut
	# lire « celui-ci est tombé, il revient ».
	fill.size.x = LIMB_GAUGE_WIDTH * (clampf(ratio, 0.0, 1.0) if alive else 1.0)

## Reconfigure la rangée de pastilles pour les sous-cibles d'un boss : un libellé chacune,
## la rangée RECENTRÉE sur leur nombre (trois pour le Harvester, quatre ou trois pour le
## Leviathan selon la phase). Les pastilles au-delà du compte sont cachées.
##
## À appeler après `show_boss`, puis à chaque changement de phase du Leviathan quand la
## nature des sous-cibles change (plaques → nœuds → épines). Une liste vide éteint la
## rangée — la phase finale du Leviathan n'a plus de sous-cible extérieure.
func set_boss_limbs(labels: PackedStringArray) -> void:
	var count := mini(labels.size(), _limb_pips.size())
	var unit := LIMB_LABEL_WIDTH + LIMB_GAUGE_WIDTH
	var span := unit + LIMB_GAUGE_GAP
	var left := 400.0 - (unit * count + LIMB_GAUGE_GAP * maxi(count - 1, 0)) * 0.5
	for i in _limb_pips.size():
		var used := i < count
		_limb_labels[i].visible = used
		_limb_tracks[i].visible = used
		_limb_pips[i].visible = used
		if not used:
			continue
		var x := left + float(i) * span
		_limb_labels[i].text = labels[i]
		_limb_labels[i].position = Vector2(x, 49)
		_limb_tracks[i].position = Vector2(x + LIMB_LABEL_WIDTH, 50.0)
		_limb_pips[i].position = Vector2(x + LIMB_LABEL_WIDTH, 50.0)
		# Chaque sous-cible repart pleine et vive : la rangée décrit un boss neuf de phase.
		_limb_pips[i].color = BOSS_MAGENTA
		_limb_pips[i].size.x = LIMB_GAUGE_WIDTH

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
