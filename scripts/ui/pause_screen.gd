class_name PauseScreen
extends CanvasLayer
## Écran de pause — même interface Helios que l'accueil, rabattue sur un champ de
## bataille figé (mise en scène : scenes/ui/pause_screen.tscn).
##
## Le calque traite TOUJOURS (process_mode = ALWAYS) : sans ça, Échap et les boutons
## deviendraient inertes à l'instant même où l'arbre se met en pause.
##
## Autoloads résolus par chemin (convention projet) : garde le script compilable en
## mode --script, où les globales d'autoload n'existent pas.

const GameStateScript := preload("res://scripts/core/game_state.gd")
const SceneRouterScript := preload("res://scripts/core/scene_router.gd")
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const OptionsMenuScene := preload("res://scenes/ui/options_menu.tscn")
const BOOT_SCENE := "res://scenes/boot/boot.tscn"

## Émis à chaque bascule. Le niveau s'en sert pour effacer le HUD, dont les coins
## sont ceux que l'interface de pause vient occuper. La pause ne connaît pas le HUD :
## c'est le niveau qui les raccorde (graybox_root.gd).
signal pause_toggled(is_paused: bool)

## Ouverture sèche, fermeture plus sèche encore : une pause qui met une demi-seconde
## à se lever se paie à CHAQUE pression d'Échap. L'accueil peut prendre son temps
## (0.8 s), pas elle.
const OPEN_TIME := 0.16
const CLOSE_TIME := 0.10
const RISE := 18.0        # le bloc central monte de 18 px en se posant
const FADE_TIME := 0.45   # sortie vers le titre, calée sur title_menu.gd

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _scene_router: SceneRouterScript = get_node("/root/SceneRouter")
@onready var _audio: AudioManagerScript = get_node("/root/AudioManager")
@onready var _scrim: ColorRect = %Scrim
@onready var _overlay: Control = %Overlay
@onready var _center: Control = %Center
@onready var _menu: VBoxContainer = %Menu
@onready var _fade: ColorRect = %Fade
@onready var _build_label: Label = %Build

var _options: Control
var _is_open: bool = false
var _leaving: bool = false
## Le focus repris à l'ouverture déclencherait son tic par-dessus le son de pause :
## deux sons sur la même image se brouillent au lieu de s'additionner.
var _muting_focus: bool = false
var _scrim_alpha: float = 0.0
var _center_rest_y: float = 0.0
var _tween: Tween
var _lyra: LyraPortrait
var _brief_panel: PanelContainer
var _brief_kicker: Label
var _brief_title: Label
var _brief_desc: Label
var _brief_objectives: VBoxContainer

func _ready() -> void:
	visible = false
	# Opacité de repos relevée depuis la scène : l'animation est un facteur de
	# celle-ci, jamais une valeur en dur qui divergerait au premier réglage.
	_scrim_alpha = _scrim.color.a
	_center_rest_y = _center.position.y
	_build_label.text = GameVersion.label()
	_build_briefing()
	for button in _buttons():
		button.focus_entered.connect(_on_focus_changed)
	var args := OS.get_cmdline_user_args()
	if "--pause-demo" in args:
		_open.call_deferred()
	# L'écran d'options ne s'atteint qu'au clavier, donc il n'était vérifiable que par
	# l'opérateur. Ce drapeau le rend capturable depuis WSL comme le reste du jeu.
	if "--options-demo" in args:
		_open.call_deferred()
		_open_options.call_deferred()

# --- Le briefing de secteur (ADR-0035, pas 3) --------------------------------

const LyraPortraitScript := preload("res://scripts/ui/lyra_portrait.gd")

## La colonne de gauche : Lyra et ce qu'il faut savoir. ⚠️ ELLE EST À GAUCHE ICI, ET À DROITE
## EN JEU, et ce n'est pas une incohérence : en pause, c'est ELLE qu'on vient lire, donc elle
## prend le bord que l'œil balaie en premier. En jeu, elle ne doit pas disputer sa place au
## champ de tir — d'où le coin libre.
const BRIEF_COLUMN := 0.42
## ⚠️ LE CENTRE RESTE DÉGAGÉ. Le jeu est toujours là derrière, figé sous le voile : c'est ce
## que l'opérateur a retenu de la maquette (« la fenêtre du jeu visible figé »). Le remplir
## d'interface reviendrait à le cacher, et la pause perdrait ce qu'elle a de mieux — on voit
## ce qu'on a laissé en plan.
func _build_briefing() -> void:
	_lyra = LyraPortraitScript.new()
	_lyra.name = "Lyra"
	_lyra.layer_dir = "res://assets/imported/ui/characters/lyra"
	_lyra.rig = preload("res://resources/dialogue/lyra_rig.tres")
	# Elle se tient sur un socle : pied-en-cap, sans lui, elle flotte.
	_lyra.pedestal = true
	_lyra.anchor_right = 0.20
	_lyra.anchor_bottom = 1.0
	_lyra.offset_left = 44.0
	_lyra.offset_top = 168.0
	_lyra.offset_bottom = -150.0
	_overlay.add_child(_lyra)

	_brief_panel = PanelContainer.new()
	_brief_panel.name = "Briefing"
	_brief_panel.anchor_left = 0.20
	_brief_panel.anchor_right = BRIEF_COLUMN
	_brief_panel.anchor_top = 0.0
	_brief_panel.offset_left = 24.0
	_brief_panel.offset_top = 200.0
	_brief_panel.offset_right = 300.0
	_brief_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_brief_panel.add_theme_stylebox_override("panel", _brief_frame())
	_brief_panel.visible = false
	_overlay.add_child(_brief_panel)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	_brief_panel.add_child(column)

	_brief_kicker = _brief_label(column, 11, Color(0.161, 0.902, 1.0, 0.85))
	_brief_title = _brief_label(column, 30, Color(0.95, 0.98, 1.0))
	_brief_desc = _brief_label(column, 18, Color(0.875, 0.965, 1.0, 0.85), true)

	var rule := ColorRect.new()
	rule.color = Color(0.161, 0.902, 1.0, 0.35)
	rule.custom_minimum_size = Vector2(0, 1)
	column.add_child(rule)

	_brief_label(column, 11, Color(0.894, 0.71, 0.29, 0.9)).text = "OBJECTIFS DE MISSION"
	_brief_objectives = VBoxContainer.new()
	_brief_objectives.add_theme_constant_override("separation", 6)
	column.add_child(_brief_objectives)

func _brief_frame() -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = Color(0.02, 0.05, 0.10, 0.88)
	box.border_color = Color(0.161, 0.902, 1.0, 0.7)
	box.set_border_width_all(2)
	box.corner_radius_top_left = 14
	box.corner_radius_bottom_right = 14
	box.set_content_margin_all(20)
	return box

func _brief_label(parent: Control, size: int, colour: Color, wrap: bool = false) -> Label:
	var label := Label.new()
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", colour)
	if wrap:
		label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	parent.add_child(label)
	return label

## Le niveau pousse le briefing de la phase courante. ⚠️ C'EST LUI QUI SAIT, PAS L'ÉCRAN : la
## pause ne connaît ni les phases, ni le boss, ni le champ d'astéroïdes — et elle n'a aucune
## raison de l'apprendre. `null` la laisse muette plutôt que fautive.
func show_briefing(briefing: SectorBriefing) -> void:
	if _brief_panel == null:
		return
	if briefing == null:
		_brief_panel.visible = false
		return
	_brief_kicker.text = briefing.kicker
	_brief_title.text = briefing.title
	_brief_desc.text = briefing.description
	for child in _brief_objectives.get_children():
		child.queue_free()
	for objective in briefing.objectives:
		var line := _brief_label(_brief_objectives, 16, Color(0.95, 0.98, 1.0, 0.92))
		# Le losange d'Helios, le même que sur les bonus : la puce dit la faction avant que
		# le texte ne dise la consigne.
		line.text = "◆  %s" % objective
	_brief_panel.visible = true

func _buttons() -> Array[Button]:
	var found: Array[Button] = []
	for child in _menu.get_children():
		var button := child as Button
		if button != null:
			found.append(button)
	return found

func _on_focus_changed() -> void:
	if _muting_focus:
		return
	_audio.play(&"ui_select")

func _unhandled_input(event: InputEvent) -> void:
	if _leaving:
		return
	if _options != null and _options.visible:
		return # l'overlay d'options possède l'input tant qu'il est levé
	if event.is_action_pressed("ui_cancel"):
		if _is_open:
			_resume()
		else:
			_open()
		get_viewport().set_input_as_handled()
	elif _is_open and event.is_action_pressed("ui_options"):
		_open_options()
		get_viewport().set_input_as_handled()

# --- Ouverture / fermeture ----------------------------------------------------

func _open() -> void:
	if _is_open:
		return
	_is_open = true
	visible = true
	get_tree().paused = true
	pause_toggled.emit(true)
	_audio.play(&"ui_banner")
	# Le menu de pause n'a JAMAIS pris le focus : au clavier comme au pad, il fallait
	# d'abord cliquer pour que la navigation réponde (défaut relevé dans
	# title_menu.gd:48). On le prend ici, dès l'ouverture.
	var buttons := _buttons()
	if not buttons.is_empty():
		_muting_focus = true
		buttons[0].grab_focus()
		_muting_focus = false
	_scrim.color.a = 0.0
	_overlay.modulate.a = 0.0
	_center.position.y = _center_rest_y + RISE
	_retween()
	_tween.set_parallel(true)
	_tween.tween_property(_scrim, "color:a", _scrim_alpha, OPEN_TIME)
	_tween.tween_property(_overlay, "modulate:a", 1.0, OPEN_TIME)
	_tween.tween_property(_center, "position:y", _center_rest_y, OPEN_TIME * 1.4) \
		.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)

func _resume() -> void:
	if not _is_open:
		return
	_is_open = false
	# Le son vit ici, pas dans le gestionnaire du bouton : Échap et « REPRENDRE »
	# sont la même action et doivent sonner pareil.
	_audio.play(&"ui_confirm")
	# close() et non hide() : la fermeture sauvegarde les réglages audio. Chemin
	# défensif — l'overlay d'options garde l'input et bloque les clics tant qu'il est
	# levé — mais un hide() nu perdrait silencieusement un réglage le jour où il
	# deviendrait atteignable.
	if _options != null and _options.visible:
		_options.close()
	# Le jeu repart TOUT DE SUITE, l'écran s'efface par-dessus : rendre la main après
	# le fondu ferait payer 100 ms de latence à chaque reprise.
	get_tree().paused = false
	pause_toggled.emit(false)
	_retween()
	_tween.set_parallel(true)
	_tween.tween_property(_scrim, "color:a", 0.0, CLOSE_TIME)
	_tween.tween_property(_overlay, "modulate:a", 0.0, CLOSE_TIME)
	_tween.chain().tween_callback(func() -> void: visible = false)

## Un seul tween à la fois. Sans ça, Échap pressé pendant un fondu laisse deux tweens
## se disputer la même propriété, et l'écran se fige à mi-opacité.
func _retween() -> void:
	if _tween != null and _tween.is_valid():
		_tween.kill()
	_tween = create_tween()

# --- Actions du menu ----------------------------------------------------------

func _on_resume_pressed() -> void:
	_resume()

func _on_options_pressed() -> void:
	_audio.play(&"ui_confirm")
	_open_options()

func _on_title_pressed() -> void:
	_audio.play(&"ui_confirm")
	_return_to_title()

func _open_options() -> void:
	if _options == null:
		_options = OptionsMenuScene.instantiate()
		_options.closed.connect(_on_options_closed)
		add_child(_options)  # son _ready() l'ouvre
	else:
		_options.open()

func _on_options_closed() -> void:
	var buttons := _buttons()
	if buttons.size() > 1:
		buttons[1].grab_focus()

func _return_to_title() -> void:
	if _leaving:
		return
	_leaving = true
	# L'arbre reste EN PAUSE pendant le fondu : le dépauser d'abord relancerait une
	# demi-seconde de combat sous un écran qui s'assombrit — tirs et morts inclus.
	_retween()
	_tween.tween_property(_fade, "color:a", 1.0, FADE_TIME)
	_tween.tween_callback(_goto_title)

func _goto_title() -> void:
	get_tree().paused = false
	# Repasser l'état AVANT de router : sans ça, `current` restait sur
	# FIGHTER_COMBAT alors qu'on affiche le titre, et le lancement suivant
	# était refusé sans que rien ne le montre à l'écran.
	_game_state.transition_to(GameStateScript.State.BOOT)
	_scene_router.goto_scene(BOOT_SCENE)
