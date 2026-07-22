class_name CodexDatasheet
extends CanvasLayer
## Fiche technique du bestiaire — tout l'habillage 2D de l'écran des coques.
##
## Construite EN CODE, comme `fighter_hud.gd` : les valeurs, les libellés et jusqu'à
## la couleur d'accent changent à chaque coque, et une `.tscn` de 400 lignes qu'il
## faut de toute façon réécrire au complet à chaque bascule ne serait qu'un décor à
## maintenir en double. La `.tscn` du bestiaire ne porte donc que la scène 3D.
##
## Vocabulaire imposé par ADR-0012 : thème et Control, mobilier de l'accueil reconduit
## aux mêmes ancres (identité en haut à gauche, rappel de touches en bas au centre,
## devise en bas à droite), filet de 2 px, angles vifs, Press Start 2P.
##
## Ce calque ne LIT rien tout seul : `codex_screen.gd` lui pousse une fiche. Il ne
## connaît ni la 3D, ni les autoloads, ni l'input.

# --- Palette ------------------------------------------------------------------
# L'accent suit le CAMP : la fiche entière vire au magenta sur une coque du Null
# Choir. C'est le signal le plus rapide qu'on a changé de bord — plus rapide qu'un
# libellé, qu'il faut lire.
const HELIOS_ACCENT := Color("29e6ff")
const CHOIR_ACCENT := Color("d93d9c")
const GOLD := Color("e4b54a")
const TEXT_LIGHT := Color("dff6ff")
const TEXT_DIM := Color(0.875, 0.965, 1.0, 0.55)
const PANEL_BG := Color(0.024, 0.039, 0.078, 0.82)   # #060A14 @ 82 %
const BAR_TRACK := Color("02131a")

const _LABEL_FONT := preload("res://assets/fonts/PressStart2P.ttf")
const _VALUE_FONT := preload("res://assets/fonts/VT323.ttf")

# --- Mise en page (viewport de référence 1920 x 1080) -------------------------
const MARGIN := 52.0
const FRAME_INSET := 22.0
const LEFT_WIDTH := 660.0
const RIGHT_WIDTH := 560.0

## ⚠️ Les DEUX panneaux de la colonne droite sont ancrés EN HAUT, et le second se
## place sous le premier par le calcul. Ancrer les profils de vol en bas les faisait
## se recouvrir dès que la hauteur du viewport passait sous 1068 px : le panneau des
## variantes, opaque à 82 %, passait par-dessus la dernière ligne d'instruments —
## celle-là même qu'on venait d'agrandir le panneau pour ne pas perdre. Le projet ne
## pose aucun `window/stretch/mode`, et la fenêtre est redimensionnable : une fenêtre
## maximisée sur un écran 1080p a déjà une zone client d'environ 1040 px.
const READOUTS_TOP := 150.0
const READOUTS_HEIGHT := 476.0
const VARIANTS_GAP := 12.0
const VARIANTS_HEIGHT := 306.0

## Maxima de RÉFÉRENCE des jauges. Ce ne sont pas des valeurs de gameplay : ce sont
## les bornes d'un instrument, choisies juste au-dessus du plus gros de la flotte
## (Leviathan 950 PV, joueur 14 u/s et 8,3 tirs/s) pour qu'aucune barre ne sature.
const HULL_REFERENCE := 1000.0
const SPEED_REFERENCE := 15.0
const RATE_REFERENCE := 10.0

## Durée du décompte des chiffres à chaque bascule de coque. Au-delà, on attend
## l'instrument au lieu de lire la fiche.
const ROLL_TIME := 0.45
## Le balayage de scan descend sur la zone 3D quand une fiche s'ouvre.
const SCAN_TIME := 0.7

signal back_requested

# --- Nœuds construits ---------------------------------------------------------
var _accent: Color = HELIOS_ACCENT
var _accent_applied: bool = false
var _frame_style: StyleBoxFlat
var _roster_labels: Array[Label] = []
var _panel_styles: Array[StyleBoxFlat] = []
var _accent_labels: Array[Label] = []
var _rules: Array[ColorRect] = []
## Tweens en cours, tués avant d'en lancer un autre sur la même propriété : deux
## bascules de fiche à moins de ROLL_TIME d'intervalle laissaient deux tweens écrire
## la même largeur de barre, chacun depuis sa propre valeur de départ.
var _bar_tweens: Dictionary[StringName, Tween] = {}
var _scan_tween: Tween

var _designation: Label
var _name: Label
var _class: Label
var _builder: Label
var _status_pip: ColorRect
var _status_text: Label
var _notice: Label

var _readouts: Dictionary[StringName, Label] = {}
var _bars: Dictionary[StringName, ColorRect] = {}
var _bar_tracks: Dictionary[StringName, ColorRect] = {}
var _bar_widths: Dictionary[StringName, float] = {}

var _variant_panel: Panel
var _variant_title: Label
var _variant_rows: Array[Label] = []
var _scan_line: ColorRect
var _fade: ColorRect

## Nombre de lignes de variantes pré-construites. Le Needle Scout en a huit ; on en
## prévoit dix pour absorber une famille qui grandirait sans toucher au calque.
const VARIANT_ROWS := 10
## Gabarit de colonne du tableau des variantes, partagé par l'en-tête et les lignes.
## Une seule constante : c'est ce qui garantit que les colonnes restent alignées quand
## on en élargit une.
const VARIANT_FORMAT := "%-14s %4s %6s %5s"

func _ready() -> void:
	layer = 2
	_build_frame()
	_build_identity()
	_build_roster()
	_build_subject()
	_build_readouts()
	_build_variants()
	_build_notice()
	_build_furniture()
	_build_scan()
	_build_fade()

# --- Fabriques élémentaires ---------------------------------------------------

func _root() -> Control:
	# Un Control racine plein cadre : tous les blocs s'ancrent dessus, ce qui rend la
	# fiche indépendante de la résolution sans recalculer une seule position.
	var existing := get_node_or_null("Root") as Control
	if existing != null:
		return existing
	var root := Control.new()
	root.name = "Root"
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	return root

func _panel(anchor: Vector2, offset: Vector2, size: Vector2) -> Panel:
	var panel := Panel.new()
	panel.anchor_left = anchor.x
	panel.anchor_right = anchor.x
	panel.anchor_top = anchor.y
	panel.anchor_bottom = anchor.y
	# Un offset négatif ancre depuis le bord opposé — même convention que le HUD.
	panel.offset_left = offset.x if anchor.x == 0.0 else offset.x - size.x
	panel.offset_right = offset.x + size.x if anchor.x == 0.0 else offset.x
	panel.offset_top = offset.y if anchor.y == 0.0 else offset.y - size.y
	panel.offset_bottom = offset.y + size.y if anchor.y == 0.0 else offset.y
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var style := StyleBoxFlat.new()
	style.bg_color = PANEL_BG
	style.border_color = _accent
	style.set_border_width_all(3)
	style.set_corner_radius_all(0)
	style.shadow_color = Color(_accent.r, _accent.g, _accent.b, 0.25)
	style.shadow_size = 0
	style.shadow_offset = Vector2(4, 4)
	panel.add_theme_stylebox_override("panel", style)
	_root().add_child(panel)
	_panel_styles.append(style)
	return panel

## `accent` : le libellé suivra la couleur du camp à chaque bascule de coque.
func _label(parent: Node, text: String, font: FontFile, size: int, color: Color,
		pos: Vector2, width: float = 400.0,
		align: int = HORIZONTAL_ALIGNMENT_LEFT, accent: bool = false) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_override("font", font)
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
	label.horizontal_alignment = align
	label.position = pos
	label.size = Vector2(width, float(size) + 10.0)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(label)
	if accent:
		_accent_labels.append(label)
	return label

# --- Blocs --------------------------------------------------------------------

func _build_frame() -> void:
	var frame := Panel.new()
	frame.set_anchors_preset(Control.PRESET_FULL_RECT)
	frame.offset_left = FRAME_INSET
	frame.offset_top = FRAME_INSET
	frame.offset_right = -FRAME_INSET
	frame.offset_bottom = -FRAME_INSET
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_frame_style = StyleBoxFlat.new()
	_frame_style.bg_color = Color(0, 0, 0, 0)
	_frame_style.set_border_width_all(2)
	_frame_style.border_color = Color(_accent.r, _accent.g, _accent.b, 0.3)
	frame.add_theme_stylebox_override("panel", _frame_style)
	_root().add_child(frame)

## Bloc d'identité de l'accueil, reconduit à la même ancre (ADR-0012 §1).
func _build_identity() -> void:
	var root := _root()
	_label(root, "HELIOS VANGUARD", _LABEL_FONT, 13, GOLD, Vector2(MARGIN, 48.0))
	_label(root, "ARCHIVE TECHNIQUE", _LABEL_FONT, 10, TEXT_DIM, Vector2(MARGIN, 74.0))
	_label(root, "BESTIAIRE  //  COQUES CONNUES", _LABEL_FONT, 10, _accent,
		Vector2(MARGIN, 94.0), 480.0, HORIZONTAL_ALIGNMENT_LEFT, true)

## Bandeau des coques, en haut au centre. La coque courante est vive, les autres
## sourdes : le joueur voit d'un coup où il est ET ce qui reste à voir.
func _build_roster() -> void:
	var strip := HBoxContainer.new()
	strip.name = "Roster"
	strip.anchor_left = 0.5
	strip.anchor_right = 0.5
	strip.offset_left = -880.0
	strip.offset_right = 880.0
	strip.offset_top = 62.0
	strip.offset_bottom = 92.0
	strip.alignment = BoxContainer.ALIGNMENT_CENTER
	strip.add_theme_constant_override("separation", 22)
	strip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root().add_child(strip)

func set_roster(names: PackedStringArray) -> void:
	var strip := _root().get_node_or_null("Roster") as HBoxContainer
	if strip == null:
		return
	for child in strip.get_children():
		child.queue_free()
	_roster_labels.clear()
	for i in names.size():
		if i > 0:
			var sep := Label.new()
			sep.text = "/"
			sep.add_theme_font_override("font", _LABEL_FONT)
			sep.add_theme_font_size_override("font_size", 11)
			sep.add_theme_color_override("font_color", Color(1, 1, 1, 0.2))
			strip.add_child(sep)
		var label := Label.new()
		label.text = names[i].to_upper()
		label.add_theme_font_override("font", _LABEL_FONT)
		label.add_theme_font_size_override("font_size", 11)
		label.add_theme_color_override("font_color", TEXT_DIM)
		strip.add_child(label)
		_roster_labels.append(label)

## Le sujet : matricule, nom, classe, constructeur, statut.
func _build_subject() -> void:
	var root := _root()
	var y := 268.0
	_designation = _label(root, "", _LABEL_FONT, 13, GOLD, Vector2(MARGIN, y), LEFT_WIDTH)
	_name = _label(root, "", _LABEL_FONT, 34, Color("f2fbff"), Vector2(MARGIN, y + 30.0), LEFT_WIDTH)
	# Halo cyan sous le nom, comme le titre de l'accueil : c'est la même famille
	# typographique, au même rang hiérarchique.
	_name.add_theme_color_override("font_shadow_color", Color(_accent.r, _accent.g, _accent.b, 0.45))
	_name.add_theme_constant_override("shadow_offset_x", 0)
	_name.add_theme_constant_override("shadow_offset_y", 0)
	_name.add_theme_constant_override("shadow_outline_size", 10)
	_class = _label(root, "", _LABEL_FONT, 12, _accent, Vector2(MARGIN, y + 84.0),
		LEFT_WIDTH, HORIZONTAL_ALIGNMENT_LEFT, true)
	_builder = _label(root, "", _LABEL_FONT, 10, TEXT_DIM, Vector2(MARGIN, y + 110.0), LEFT_WIDTH)
	# Pastille d'état en ColorRect : Press Start 2P n'a ni `●` ni `■` (ADR-0012).
	_status_pip = ColorRect.new()
	_status_pip.position = Vector2(MARGIN, y + 142.0)
	_status_pip.size = Vector2(9, 9)
	_status_pip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_status_pip)
	_status_text = _label(root, "", _LABEL_FONT, 10, GOLD, Vector2(MARGIN + 18.0, y + 138.0), LEFT_WIDTH)

## Colonne d'instruments, à droite. Trois blocs : gabarit, structure, armement.
func _build_readouts() -> void:
	# 476 et non 430 : la dernière ligne du bloc tombait SOUS le bord du cadre, et
	# comme elle est la seule à changer de libellé selon la coque, c'est justement
	# celle qu'on ne peut pas se permettre de perdre.
	var panel := _panel(Vector2(1, 0), Vector2(-MARGIN, READOUTS_TOP),
		Vector2(RIGHT_WIDTH, READOUTS_HEIGHT))
	_label(panel, "FICHE TECHNIQUE", _LABEL_FONT, 11, _accent, Vector2(18, 16),
		RIGHT_WIDTH - 36.0, HORIZONTAL_ALIGNMENT_LEFT, true)

	var y := 54.0
	_row(panel, &"length", "LONGUEUR", y)
	_row(panel, &"span", "ENVERGURE", y + 30.0)
	_row(panel, &"height", "HAUTEUR", y + 60.0)
	_rule(panel, y + 92.0)
	_row(panel, &"mass", "MASSE", y + 104.0)
	_row(panel, &"crew", "EQUIPAGE", y + 134.0)
	_row(panel, &"polys", "POLYGONES", y + 164.0)
	_rule(panel, y + 196.0)
	_gauge(panel, &"hull", "STRUCTURE", y + 208.0)
	_gauge(panel, &"speed", "VITESSE", y + 258.0)
	_gauge(panel, &"rate", "CADENCE", y + 308.0)
	_row(panel, &"extra", "TOUCHE", y + 352.0)

## Ligne « libellé ..... valeur ». Les libellés sont en police de titrage, les
## valeurs en VT323 : c'est la convention du HUD de combat, on ne l'invente pas ici.
func _row(panel: Panel, key: StringName, caption: String, y: float) -> void:
	_label(panel, caption, _LABEL_FONT, 11, TEXT_DIM, Vector2(18, y + 6.0), 300.0)
	_readouts[key] = _label(panel, "-", _VALUE_FONT, 28, TEXT_LIGHT,
		Vector2(RIGHT_WIDTH - 258.0, y - 2.0), 240.0, HORIZONTAL_ALIGNMENT_RIGHT)

## Ligne avec jauge : le chiffre reste la vérité, la barre donne l'ordre de grandeur
## dans la flotte. Les deux, jamais la barre seule.
func _gauge(panel: Panel, key: StringName, caption: String, y: float) -> void:
	_row(panel, key, caption, y)
	var width := RIGHT_WIDTH - 36.0
	var track := ColorRect.new()
	track.color = BAR_TRACK
	track.position = Vector2(18, y + 30.0)
	track.size = Vector2(width, 10.0)
	track.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(track)
	_bar_tracks[key] = track
	var fill := ColorRect.new()
	fill.color = _accent
	fill.position = Vector2(18, y + 30.0)
	fill.size = Vector2(0.0, 10.0)
	fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(fill)
	_bars[key] = fill
	_bar_widths[key] = width

## Les filets sont ENREGISTRÉS, pas seulement dessinés : construits une fois avec
## l'accent Helios, ils restaient cyan au milieu d'un panneau devenu magenta sur les
## quatre fiches du Null Choir — deux traits qui trahissaient le camp précédent.
func _rule(panel: Panel, y: float) -> void:
	var rule := ColorRect.new()
	rule.color = Color(_accent.r, _accent.g, _accent.b, 0.22)
	_rules.append(rule)
	rule.position = Vector2(18, y)
	rule.size = Vector2(RIGHT_WIDTH - 36.0, 1.0)
	rule.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(rule)

## Profils de vol — huit ennemis partagent la coque du Needle Scout. Les faire
## défiler comme huit fiches montrerait huit fois le même modèle ; ils sont donc
## listés DANS la fiche de leur coque, avec ce qui les distingue vraiment.
func _build_variants() -> void:
	_variant_panel = _panel(Vector2(1, 0),
		Vector2(-MARGIN, READOUTS_TOP + READOUTS_HEIGHT + VARIANTS_GAP),
		Vector2(RIGHT_WIDTH, VARIANTS_HEIGHT))
	_variant_title = _label(_variant_panel, "PROFILS DE VOL", _LABEL_FONT, 11, _accent,
		Vector2(18, 16), RIGHT_WIDTH - 36.0, HORIZONTAL_ALIGNMENT_LEFT, true)
	# L'en-tête est composé DANS LA MÊME POLICE ET LE MÊME GABARIT que les lignes de
	# données. Posé en Press Start 2P, il ne pouvait pas tomber sur les colonnes : deux
	# polices de métriques différentes n'alignent jamais un tableau, quelle que soit la
	# position qu'on leur donne.
	_label(_variant_panel, VARIANT_FORMAT % ["TRAJECTOIRE", "PV", "U/S", "PTS"],
		_VALUE_FONT, 20, TEXT_DIM, Vector2(18, 40), RIGHT_WIDTH - 36.0)
	for i in VARIANT_ROWS:
		var row := _label(_variant_panel, "", _VALUE_FONT, 22, TEXT_LIGHT,
			Vector2(18, 66.0 + float(i) * 23.0), RIGHT_WIDTH - 36.0)
		_variant_rows.append(row)
	_variant_panel.visible = false

func _build_notice() -> void:
	var panel := _panel(Vector2(0, 1), Vector2(MARGIN, -136.0), Vector2(LEFT_WIDTH, 186.0))
	_label(panel, "NOTICE", _LABEL_FONT, 11, _accent, Vector2(18, 16),
		LEFT_WIDTH - 36.0, HORIZONTAL_ALIGNMENT_LEFT, true)
	_notice = Label.new()
	_notice.add_theme_font_override("font", _LABEL_FONT)
	_notice.add_theme_font_size_override("font_size", 10)
	_notice.add_theme_color_override("font_color", TEXT_LIGHT)
	_notice.add_theme_constant_override("line_spacing", 9)
	_notice.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_notice.position = Vector2(18, 46)
	_notice.size = Vector2(LEFT_WIDTH - 36.0, 128.0)
	_notice.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(_notice)

## Mobilier bas de l'accueil : rappel de touches au centre, devise à droite.
func _build_furniture() -> void:
	var root := _root()
	var controls := _label(root,
		"COQUE  ← →     ·     ROTATION  SOURIS / A D W S     ·     ZOOM  MOLETTE     ·     RECADRER  R     ·     RETOUR  ECHAP",
		_LABEL_FONT, 10, Color(GOLD.r, GOLD.g, GOLD.b, 0.7), Vector2(0, 0), 0.0,
		HORIZONTAL_ALIGNMENT_CENTER)
	controls.anchor_top = 1.0
	controls.anchor_right = 1.0
	controls.anchor_bottom = 1.0
	controls.offset_top = -78.0
	controls.offset_bottom = -54.0
	controls.offset_left = 0.0
	controls.offset_right = 0.0
	# Contour obligatoire : cette ligne traverse la scène 3D (ADR-0012).
	controls.add_theme_color_override("font_outline_color", Color(0.008, 0.012, 0.027, 0.9))
	controls.add_theme_constant_override("outline_size", 6)

	var creed := _label(root, "FORGE THE SKY.  DEFEND THE LIGHT.", _LABEL_FONT, 9, TEXT_DIM,
		Vector2(0, 0), 0.0, HORIZONTAL_ALIGNMENT_RIGHT)
	creed.anchor_left = 1.0
	creed.anchor_top = 1.0
	creed.anchor_right = 1.0
	creed.anchor_bottom = 1.0
	creed.offset_left = -520.0
	creed.offset_right = -MARGIN
	creed.offset_top = -46.0
	creed.offset_bottom = -26.0
	# La devise tombe sur la nébuleuse du fond, pas sur un panneau : sans contour
	# elle disparaît dans le violet (ADR-0012 — aucun texte essentiel ne repose sur
	# une image chargée sans fond ni contour de séparation).
	creed.add_theme_color_override("font_outline_color", Color(0.008, 0.012, 0.027, 0.9))
	creed.add_theme_constant_override("outline_size", 6)

## Balayage de scan : une ligne qui descend sur la zone 3D à chaque nouvelle fiche.
## C'est le seul mouvement de l'habillage — il dit « analyse en cours » sans un mot.
func _build_scan() -> void:
	_scan_line = ColorRect.new()
	_scan_line.color = Color(_accent.r, _accent.g, _accent.b, 0.0)
	_scan_line.anchor_right = 1.0
	_scan_line.offset_left = FRAME_INSET
	_scan_line.offset_right = -FRAME_INSET
	_scan_line.offset_top = 0.0
	_scan_line.offset_bottom = 2.0
	_scan_line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root().add_child(_scan_line)

func _build_fade() -> void:
	_fade = ColorRect.new()
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.color = Color(0, 0, 0, 1)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root().add_child(_fade)

# --- Remplissage --------------------------------------------------------------

## Ouvre le calque en fondu, comme l'accueil.
func fade_in(duration: float) -> void:
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", 0.0, duration)

## Ferme au noir, puis appelle `done`.
func fade_out(duration: float, done: Callable) -> void:
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", 1.0, duration)
	tween.tween_callback(done)

## Pose une fiche complète. `bounds` vient de la coque réellement affichée et
## `triangles` de ses maillages : ces deux-là ne sont jamais saisis à la main.
func show_entry(entry: CodexEntry, index: int, bounds: AABB, triangles: int,
		fittings: Dictionary[StringName, int]) -> void:
	_apply_accent(HELIOS_ACCENT if entry.camp == CodexEntry.Camp.HELIOS else CHOIR_ACCENT)
	_highlight_roster(index)

	_designation.text = entry.designation.to_upper() if not entry.designation.is_empty() else "MATRICULE INCONNU"
	_name.text = entry.display_name.to_upper()
	_class.text = entry.hull_class.to_upper() if not entry.hull_class.is_empty() else "CLASSIFICATION EN ATTENTE"
	_builder.text = entry.builder.to_upper() if not entry.builder.is_empty() else "ORIGINE NON ETABLIE"
	_status_text.text = entry.status.to_upper() if not entry.status.is_empty() else "DOSSIER INCOMPLET"
	_notice.text = entry.notice if not entry.notice.is_empty() else \
		"Notice non versee au dossier. Les releves de structure et de vol ci-contre sont mesures sur la coque."

	# Longueur = axe de vol (z), envergure = x, hauteur = y. L'ordre d'affichage suit
	# la façon dont on décrit un vaisseau, pas l'ordre des axes de Godot.
	_set_value(&"length", "%.2f m" % bounds.size.z)
	_set_value(&"span", "%.2f m" % bounds.size.x)
	_set_value(&"height", "%.2f m" % bounds.size.y)
	# Deux décimales sous 10 t : à une seule, le Crescent Interceptor (0,16 t) et le
	# Needle Scout (0,19 t) affichaient tous deux « 0.2 t » et cessaient de se
	# distinguer. Au-dessus, la deuxième décimale est du bruit.
	_set_value(&"mass", ("%.2f t" if entry.mass_t < 10.0 else "%.1f t") % entry.mass_t \
		if entry.mass_t > 0.0 else "-")
	_set_value(&"crew", str(entry.crew) if entry.crew > 0 else "AUCUN")
	_set_value(&"polys", _thousands(triangles))

	if entry.family == CodexEntry.Family.FORTRESS:
		_fill_fortress_rows(fittings)
	else:
		_fill_combat_rows(entry)

	_fill_variants(entry)
	_play_scan()

## Les trois jauges du combat, plus la ligne qui dit ce que la coque a de spécifique :
## des phases pour un boss, un score pour un ennemi, le rayon de touche pour le joueur.
func _fill_combat_rows(entry: CodexEntry) -> void:
	var hull_points := entry.hull_points()
	_set_row_caption(&"hull", "STRUCTURE", "")
	_set_gauge(&"hull", "%d" % roundi(hull_points), hull_points / HULL_REFERENCE)
	var speed := entry.speed()
	_set_row_caption(&"speed", "VITESSE", "")
	_set_gauge(&"speed", "%.2f u/s" % speed if speed > 0.0 else "DERIVE", speed / SPEED_REFERENCE)
	var interval := entry.fire_interval()
	var rate := 1.0 / interval if interval > 0.0 else 0.0
	_set_row_caption(&"rate", "CADENCE", "")
	_set_gauge(&"rate", "%.2f /s" % rate if rate > 0.0 else "-", rate / RATE_REFERENCE)

	var phases := entry.phase_count()
	var score := entry.score_value()
	if phases > 0:
		_set_row_caption(&"extra", "PHASES", str(phases))
	elif score > 0:
		_set_row_caption(&"extra", "SCORE", _thousands(score))
	else:
		_set_row_caption(&"extra", "TOUCHE", "%.2f m" % entry.hitbox_radius())

## Une forteresse n'a ni structure, ni vitesse, ni cadence — elle n'est pas un objet
## de combat dans le code. Les trois emplacements de jauge servent donc ses
## ÉQUIPEMENTS, comptés sur la coque, et sans barre : six tourelles ne se lisent pas
## sur une échelle.
func _fill_fortress_rows(fittings: Dictionary[StringName, int]) -> void:
	_set_row_caption(&"hull", "TOURELLES", "")
	_set_gauge(&"hull", str(fittings.get(&"turrets", 0)), -1.0)
	_set_row_caption(&"speed", "BALISES", "")
	_set_gauge(&"speed", str(fittings.get(&"beacons", 0)), -1.0)
	_set_row_caption(&"rate", "BATTERIES", "")
	_set_gauge(&"rate", str(fittings.get(&"batteries", 0)), -1.0)
	_set_row_caption(&"extra", "APPONTAGE", "1 BAIE")

func _set_value(key: StringName, text: String) -> void:
	var label := _readouts.get(key) as Label
	if label != null:
		label.text = text

## Change AUSSI le libellé de la ligne : la dernière ligne du bloc n'a pas le même
## sens selon la coque, et garder « TOUCHE » au-dessus d'un nombre de phases
## afficherait un mensonge bien aligné.
func _set_row_caption(key: StringName, caption: String, text: String) -> void:
	var label := _readouts.get(key) as Label
	if label == null:
		return
	label.text = text
	var caption_label := label.get_parent().get_child(label.get_index() - 1) as Label
	if caption_label != null:
		caption_label.text = caption

## `ratio` négatif : la ligne n'a pas de jauge du tout — piste comprise. Une forteresse
## a six tourelles, pas « six sur un maximum de » : une barre sous un décompte
## inventerait une échelle qui n'existe pas.
func _set_gauge(key: StringName, text: String, ratio: float) -> void:
	_set_value(key, text)
	var fill := _bars.get(key) as ColorRect
	var track := _bar_tracks.get(key) as ColorRect
	var gauged := ratio >= 0.0
	if track != null:
		track.visible = gauged
	if fill != null:
		fill.visible = gauged
	if not gauged or fill == null:
		return
	var width: float = _bar_widths.get(key, 0.0) * clampf(ratio, 0.0, 1.0)
	# La barre se remplit en glissant : une barre qui saute à sa valeur ne se lit pas
	# comme un instrument, elle se lit comme un rafraîchissement d'affichage.
	var previous := _bar_tweens.get(key) as Tween
	if previous != null and previous.is_valid():
		previous.kill()
	var tween := create_tween()
	tween.tween_property(fill, "size:x", width, ROLL_TIME).set_trans(Tween.TRANS_CUBIC)
	_bar_tweens[key] = tween

func _fill_variants(entry: CodexEntry) -> void:
	var count := mini(entry.variants.size(), VARIANT_ROWS)
	_variant_panel.visible = count > 0
	if count == 0:
		return
	_variant_title.text = "PROFILS DE VOL  (%d)" % entry.variants.size()
	for i in VARIANT_ROWS:
		var row := _variant_rows[i]
		if i >= count:
			row.text = ""
			continue
		var data: EnemyData = entry.variants[i]
		# Le nom de la trajectoire est ce qui distingue vraiment deux variantes :
		# c'est lui qu'on lit, pas le nom de fichier de la Resource.
		var path_name: String = EnemyData.Path.keys()[data.path]
		row.text = VARIANT_FORMAT % [path_name, roundi(data.max_health),
			"%.2f" % data.move_speed, data.score_value]

func _highlight_roster(index: int) -> void:
	for i in _roster_labels.size():
		var label := _roster_labels[i]
		if i == index:
			label.add_theme_color_override("font_color", Color("f2fbff"))
			label.add_theme_font_size_override("font_size", 12)
		else:
			label.add_theme_color_override("font_color", TEXT_DIM)
			label.add_theme_font_size_override("font_size", 11)

## Repeint tout ce qui porte l'accent du camp. Les couleurs sont posées à la
## construction ET ici : un bloc construit avant la première fiche doit déjà être
## de la bonne couleur, et changer de camp doit tout suivre.
func _apply_accent(accent: Color) -> void:
	# ⚠️ Le drapeau, et PAS une comparaison de couleurs. Les blocs sont construits avec
	# l'accent Helios par défaut ; sur la première fiche — qui est justement le
	# Specter-9 — une comparaison trouvait « rien à changer » et sortait avant d'avoir
	# posé la pastille d'état, qui restait blanche. Le défaut ne se voyait que sur
	# cette fiche-là, et disparaissait dès qu'on changeait de coque.
	if _accent_applied and accent.is_equal_approx(_accent):
		return
	_accent_applied = true
	_accent = accent
	_frame_style.border_color = Color(accent.r, accent.g, accent.b, 0.3)
	for style in _panel_styles:
		style.border_color = accent
		style.shadow_color = Color(accent.r, accent.g, accent.b, 0.25)
	for label in _accent_labels:
		label.add_theme_color_override("font_color", accent)
	for key: StringName in _bars:
		(_bars[key] as ColorRect).color = accent
	for rule in _rules:
		rule.color = Color(accent.r, accent.g, accent.b, 0.22)
	_name.add_theme_color_override("font_shadow_color", Color(accent.r, accent.g, accent.b, 0.45))
	_status_pip.color = Color(accent.r, accent.g, accent.b, 0.9)

func _play_scan() -> void:
	if _scan_tween != null and _scan_tween.is_valid():
		# Sans ce kill, une bascule rapide remet la ligne en haut pendant que le tween
		# précédent continue de l'interpoler vers le bas : le balayage saute.
		_scan_tween.kill()
	_scan_line.offset_top = FRAME_INSET
	_scan_line.offset_bottom = FRAME_INSET + 2.0
	_scan_line.color = Color(_accent.r, _accent.g, _accent.b, 0.55)
	# Course lue sur le viewport réel, jamais écrite en dur : à 1058 px la ligne
	# sortait par le bas d'une fenêtre plus haute et s'arrêtait en plein milieu d'une
	# fenêtre plus courte — le seul endroit du fichier qui trahissait ses propres ancres.
	var bottom := get_viewport().get_visible_rect().size.y - FRAME_INSET
	_scan_tween = create_tween()
	_scan_tween.set_parallel(true)
	_scan_tween.tween_property(_scan_line, "offset_top", bottom, SCAN_TIME)
	_scan_tween.tween_property(_scan_line, "offset_bottom", bottom + 2.0, SCAN_TIME)
	_scan_tween.tween_property(_scan_line, "color:a", 0.0, SCAN_TIME).set_delay(SCAN_TIME * 0.5)

## Séparateur de milliers. `String.num` n'en pose pas, et un compte de polygones à
## six chiffres sans séparateur ne se lit pas d'un coup d'œil.
static func _thousands(value: int) -> String:
	var digits := str(absi(value))
	var out := ""
	for i in digits.length():
		if i > 0 and (digits.length() - i) % 3 == 0:
			out += " "
		out += digits[i]
	return ("-" if value < 0 else "") + out

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		back_requested.emit()
