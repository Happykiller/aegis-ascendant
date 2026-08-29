extends CanvasLayer
## Interface de l'écran d'accueil : identité et menu navigable.
## Le diorama 3D sous-jacent est piloté par title_stage.gd et l'oscillogramme COMMS
## s'anime seul (scripts/ui/comms_trace.gd, partagé avec l'écran de pause) — ce
## script ne touche ni à la mise en scène ni à la télémétrie.
##
## Autoloads résolus par chemin (convention projet) : garde le script compilable en
## mode --script, où les globales d'autoload n'existent pas.

const GameStateScript := preload("res://scripts/core/game_state.gd")
const SceneRouterScript := preload("res://scripts/core/scene_router.gd")
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const OptionsMenuScene := preload("res://scenes/ui/options_menu.tscn")
## ⚠️ REPLI, PAS SOURCE DE VÉRITÉ. La scène à monter vient désormais du livre de campagne
## (`/root/Campaign`) ; cette constante ne sert que si l'autoload manque — un écran-titre qui
## ne lance rien serait pire qu'un écran-titre qui lance le premier niveau.
const GRAYBOX_SCENE := "res://scenes/gameplay/graybox.tscn"

## La scène du niveau courant, ou le repli ci-dessus.
func _level_scene_path() -> String:
	var campaign := get_node_or_null("/root/Campaign")
	if campaign == null:
		return GRAYBOX_SCENE
	var level: LevelData = campaign.current()
	if level == null or level.scene == null:
		return GRAYBOX_SCENE
	return level.scene.resource_path
const CODEX_SCENE := "res://scenes/ui/codex.tscn"
## Banc d'essai du bestiaire : une famille d'ennemis seule, en boucle. Jamais
## atteignable au menu — c'est un outil de réglage, pas un mode de jeu.
const BESTIARY_LAB_SCENE := "res://scenes/dev/bestiary_lab.tscn"

## Ce que Lyra dit à l'accueil (`ADR-0035`). Le texte vit dans une Resource, pas ici : c'est
## la règle du projet pour tout contenu, et c'est ce qui rendra la traduction possible.
const TITLE_DIALOGUE := preload("res://resources/dialogue/lyra_title.tres")
const LyraPortraitScript := preload("res://scripts/ui/lyra_portrait.gd")
const DialogueBoxScript := preload("res://scripts/ui/dialogue_box.gd")
const LYRA_RIG := preload("res://resources/dialogue/lyra_rig.tres")

## La colonne de droite qu'occupe Lyra, en fraction de largeur. Le menu et la bulle tiennent
## dans ce qui reste.
const LYRA_COLUMN := 0.34

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _scene_router: SceneRouterScript = get_node("/root/SceneRouter")
@onready var _audio: AudioManagerScript = get_node("/root/AudioManager")
@onready var _version_label: Label = %VersionLabel
@onready var _menu: VBoxContainer = %Menu
@onready var _fade: ColorRect = %Fade

var _options: Control
var _leaving: bool = false
var _lyra: LyraPortrait
var _dialogue: DialogueBox
var _line_index: int = 0

func _ready() -> void:
	var version := GameVersion.current()
	_version_label.text = GameVersion.label()
	_build_menu_focus()
	_dress_menu()
	_build_lyra()
	_fade.color.a = 1.0
	# Ouverture en fondu : l'accueil se lève du noir au lieu d'apparaître d'un coup.
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", 0.0, 0.8)
	print("[TitleMenu] ready (v%s)" % version)
	# Hooks de test (args après le séparateur `++`) : sauter droit à un écran.
	var args := OS.get_cmdline_user_args()
	if "--goto-graybox" in args:
		_start_game.call_deferred()
	elif "--goto-codex" in args:
		_open_codex.call_deferred()
	elif _has_prefix(args, "--goto-lab"):
		# `--goto-lab` ou `--goto-lab=<unite>` : le banc lit lui-même l'unité.
		_scene_router.goto_scene.call_deferred(BESTIARY_LAB_SCENE)


# --- Lyra Vantella, la voix du jeu (ADR-0035) --------------------------------

## Le sous-titre de chaque entrée, comme sur la maquette. ⚠️ Il ne DÉCORE pas : « NOUVELLE
## PARTIE » et « CONTINUER » se ressemblent trop pour un joueur qui découvre l'écran, et la
## seconde n'existe pas encore — dire ce que fait chaque entrée évite qu'on cherche l'autre.
const MENU_SUBTITLES: Dictionary[String, String] = {
	"PlayButton": "COMMENCER UNE NOUVELLE CAMPAGNE",
	"CodexButton": "CONSULTER LES DONNÉES ENNEMIES",
	"OptionsButton": "PARAMÈTRES ET ACCESSIBILITÉ",
	"QuitButton": "FERMER LE JEU",
}

func _dress_menu() -> void:
	for button in _buttons():
		var subtitle: String = MENU_SUBTITLES.get(button.name, "")
		if subtitle.is_empty():
			continue
		# ⚠️ ENFANT DU BOUTON, ET IGNORÉ PAR LA SOURIS : posé à côté, il casserait la
		# navigation au clavier que `_build_menu_focus()` vient d'établir.
		# ⚠️ LE BOUTON PASSE A GAUCHE. Centré, son libellé flottait au milieu de la colonne
		# pendant que son sous-titre restait collé au bord : deux textes de la même entrée,
		# à trente centimètres l'un de l'autre, ne se lisent plus comme une paire.
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		var label := Label.new()
		label.name = "Subtitle"
		label.text = subtitle
		label.add_theme_font_size_override("font_size", 9)
		label.add_theme_color_override("font_color", Color(0.875, 0.965, 1.0, 0.5))
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		# ⚠️ DES ANCRES ET DES MARGES, JAMAIS `position` SUR UN NŒUD SANS TAILLE. Écrire
		# `position` juste après un préréglage d'ancres fixe `offset_top`, mais laisse
		# `offset_bottom` calé sur une hauteur ENCORE NULLE — le rectangle est dégénéré, et le
		# texte déborde du bouton. Vu en jeu : le cadre de sélection coupait le sous-titre en
		# deux (opérateur, 2026-08-28).
		label.anchor_left = 0.0
		label.anchor_right = 1.0
		label.anchor_top = 1.0
		label.anchor_bottom = 1.0
		# ⚠️ LA MÊME MARGE QUE LE LIBELLÉ, ET ELLE EST DÉSORMAIS DÉCLARÉE. Le thème pose
		# `content_margin_left = 18` sur les trois états du bouton ; le sous-titre s'y aligne
		# au pixel. Avant, le libellé partait de la bordure (3 px) et le sous-titre de 10 : un
		# écart de sept pixels que le cadre de sélection rendait visible.
		label.offset_left = 18.0
		label.offset_right = -18.0
		label.offset_top = -24.0
		label.offset_bottom = -7.0
		label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		button.add_child(label)
		# La hauteur laisse la place aux DEUX lignes dans le cadre : le libellé se centre dans
		# le bouton, le sous-titre tient sous lui, et la bordure les entoure tous les deux.
		button.custom_minimum_size.y = maxf(button.custom_minimum_size.y, 72.0)

## Monte le portrait à droite et la bulle en bas, puis lance la première réplique.
##
## ⚠️ BÂTIS PAR CODE ET NON POSÉS DANS `boot.tscn`. La scène est éditée par une autre session
## (`pratique-ecrivain-unique.md`) et un `.tscn` se fusionne très mal à deux — le décor du
## noyau a été bâti par code pour la même raison.
func _build_lyra() -> void:
	# ⚠️ `--no-lyra` : LE TÉMOIN DE SA MESURE, dans la même famille que `--no-backdrop` et
	# `--no-glow`. Un coût ne s'attribue qu'en mesurant AVEC puis SANS — et le jour où la
	# planche livrée pèsera treize calques pleine hauteur, c'est ce drapeau qui dira ce
	# qu'elle coûte, sur la T1000 qui contraint le budget.
	if "--no-lyra" in OS.get_cmdline_user_args():
		print("[TitleMenu] ISOLATION : pas de portrait (--no-lyra)")
		return
	_lyra = LyraPortraitScript.new()
	_lyra.name = "Lyra"
	# ⚠️ LE GRÉEMENT EST OBLIGATOIRE ICI. Les calques pied-en-cap ne sont pas co-enregistrés
	# entre groupes : sans lui, la tête ferait les deux tiers du corps (`ADR-0035`).
	_lyra.rig = LYRA_RIG
	# Elle se tient sur un socle : pied-en-cap, sans lui, elle flotte.
	_lyra.pedestal = true
	_lyra.anchor_left = 1.0 - LYRA_COLUMN
	_lyra.anchor_right = 1.0
	_lyra.anchor_top = 0.0
	_lyra.anchor_bottom = 1.0
	_lyra.offset_top = 40.0
	_lyra.offset_bottom = -20.0
	_lyra.offset_right = -40.0
	add_child(_lyra)

	_dialogue = DialogueBoxScript.new()
	_dialogue.name = "Dialogue"
	_dialogue.anchor_left = 0.0
	_dialogue.anchor_right = 1.0 - LYRA_COLUMN
	_dialogue.anchor_top = 1.0
	_dialogue.anchor_bottom = 1.0
	# ⚠️ AU-DESSUS DU BLOC COMMS. Il occupe le coin bas-gauche depuis toujours (canal 09 et
	# son oscillogramme) : la première pose du 2026-08-28 lui passait dessus.
	_dialogue.offset_left = 56.0
	_dialogue.offset_right = -232.0
	_dialogue.offset_top = -272.0
	_dialogue.offset_bottom = -148.0
	_dialogue.voice_requested.connect(_speak)
	_dialogue.advance_requested.connect(_next_line)
	_dialogue.line_finished.connect(_next_line)
	add_child(_dialogue)

	_line_index = 0
	_play_line()

## L'écran joue la voix, la bulle ne fait que la demander. ⚠️ C'est l'`AudioManager` qui
## connaît le bus et la banque ; la bulle, elle, doit rester montable en test.
func _speak(cue: StringName) -> void:
	if _audio != null:
		_audio.play(cue)

func _play_line() -> void:
	var line := TITLE_DIALOGUE.line_at(_line_index)
	if line == null:
		return
	_dialogue.play(line, TITLE_DIALOGUE.page_label(_line_index))
	if _lyra != null:
		_lyra.set_mood(line.mood_colour())

## ⚠️ ELLE BOUCLE, ELLE NE SE TAIT PAS. Un accueil laissé sur sa dernière réplique se fige :
## le joueur qui revient au menu après une partie retrouverait un écran mort. Elle repart au
## début — c'est une hôtesse, pas un générique.
func _next_line() -> void:
	if _leaving or _dialogue == null:
		return
	_line_index = (_line_index + 1) % maxi(TITLE_DIALOGUE.size(), 1)
	_play_line()

func _process(_delta: float) -> void:
	if _lyra != null and _dialogue != null:
		_lyra.set_speech_level(_dialogue.speech_level())

static func _has_prefix(args: PackedStringArray, prefix: String) -> bool:
	for arg in args:
		if arg == prefix or arg.begins_with(prefix + "="):
			return true
	return false

func _build_menu_focus() -> void:
	var buttons := _buttons()
	if buttons.is_empty():
		return
	for button in buttons:
		button.focus_entered.connect(_on_focus_changed)
	buttons[0].grab_focus()

func _buttons() -> Array[Button]:
	var found: Array[Button] = []
	for child in _menu.get_children():
		var button := child as Button
		if button != null:
			found.append(button)
	return found

func _on_focus_changed() -> void:
	_audio.play(&"ui_select")

func _unhandled_input(event: InputEvent) -> void:
	if _leaving:
		return
	if _options != null and _options.visible:
		return # l'overlay possède l'input tant qu'il est levé
	if event.is_action_pressed("ui_options"):
		_open_options()
		get_viewport().set_input_as_handled()

# --- Actions du menu ----------------------------------------------------------

func _on_play_pressed() -> void:
	_audio.play(&"ui_confirm")
	_start_game()

func _on_codex_pressed() -> void:
	_audio.play(&"ui_confirm")
	_open_codex()

func _on_options_pressed() -> void:
	_audio.play(&"ui_confirm")
	_open_options()

func _on_quit_pressed() -> void:
	_audio.play(&"ui_confirm")
	# Jusqu'ici le jeu n'avait AUCUN moyen de se fermer, nulle part.
	get_tree().quit()

func _start_game() -> void:
	if _leaving:
		return
	var chemin := _level_scene_path()
	if not ResourceLoader.exists(chemin, "PackedScene"):
		push_error("[TitleMenu] scène de jeu introuvable : %s" % chemin)
		return
	if not _game_state.transition_to(GameStateScript.State.FIGHTER_COMBAT):
		return
	_leaving = true
	# SceneRouter fait une coupe sèche ; on fond au noir d'abord, sinon l'accueil
	# disparaît d'une image à l'autre. La musique, elle, ne s'arrête PAS : le
	# niveau réclame Launch dans son propre _ready() et AudioManager enchaîne les
	# deux — couper au silence ici ne ferait qu'un trou dans le relais.
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", 1.0, 0.45)
	tween.tween_callback(func() -> void: _scene_router.goto_scene(chemin))

## Le bestiaire est une SCÈNE, pas un overlay : il monte son propre présentoir 3D,
## sa caméra et ses lumières. Le poser au-dessus du diorama de l'accueil obligerait
## à masquer ce dernier et à se battre contre sa chorégraphie — pour un résultat que
## SceneRouter obtient d'une ligne.
func _open_codex() -> void:
	if _leaving:
		return
	if not ResourceLoader.exists(CODEX_SCENE, "PackedScene"):
		push_error("[TitleMenu] bestiaire introuvable : %s" % CODEX_SCENE)
		return
	if not _game_state.transition_to(GameStateScript.State.CODEX):
		return
	_leaving = true
	# Même fondu au noir que le lancement de partie : SceneRouter fait une coupe
	# sèche, et l'accueil disparaîtrait d'une image à l'autre.
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", 1.0, 0.45)
	tween.tween_callback(func() -> void: _scene_router.goto_scene(CODEX_SCENE))

func _open_options() -> void:
	if _options == null:
		_options = OptionsMenuScene.instantiate()
		# Le signal `closed` existait déjà et n'était écouté par personne : en
		# sortant des options, le focus restait nulle part et le menu ne
		# répondait plus au clavier.
		_options.closed.connect(_on_options_closed)
		add_child(_options)  # son _ready() l'ouvre
	else:
		_options.open()

## Le focus revient sur le bouton PAR SON NOM, pas par son rang : il valait `[1]`
## quand OPTIONS était le deuxième item, et l'insertion du bestiaire l'aurait
## silencieusement renvoyé sur ce dernier.
func _on_options_closed() -> void:
	var options_button := _menu.get_node_or_null("OptionsButton") as Button
	if options_button != null:
		options_button.grab_focus()
