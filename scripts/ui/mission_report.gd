class_name MissionReport
extends CanvasLayer
## Rapport de mission (spec §14.3) — même interface Helios que l'accueil et la pause
## (ADR-0012 ; mise en scène : scenes/ui/mission_report.tscn).
##
## UN SEUL ÉCRAN, DEUX ISSUES. La victoire et la défaite affichent le même rapport :
## même cadre, même bloc d'identité, même trace de comms, même score. Ne changent que
## le titre, sa couleur, la ligne de contexte, l'état du canal et le libellé du premier
## bouton. Deux scènes auraient divergé au premier réglage — ce dépôt a déjà payé cette
## facture (cf. la traînée de réacteur dupliquée dans le contrôleur du joueur).
##
## Il ne met PAS l'arbre en pause : le niveau continue de tourner derrière (la musique
## de victoire attend que le dernier tir ennemi ait quitté l'écran, graybox_root.gd).
## L'écran se lève par-dessus, en fondu.
##
## Autoloads résolus par chemin (convention projet) : garde le script compilable en
## mode --script, où les globales d'autoload n'existent pas.

const GameStateScript := preload("res://scripts/core/game_state.gd")
const SceneRouterScript := preload("res://scripts/core/scene_router.gd")
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const BOOT_SCENE := "res://scenes/boot/boot.tscn"

enum Outcome { VICTORY, DEFEAT }

const RAISE_TIME := 0.7   # le rapport se lève, il ne surgit pas
const FADE_TIME := 0.45

## Or pour la victoire (la DA réserve l'or au commandement et aux faits d'exception,
## §5.1), rouge d'alerte pour la défaite. La grammaire ne change pas, la teinte si.
const VICTORY_GOLD := Color(0.988, 0.902, 0.71)
const VICTORY_GLOW := Color(0.894, 0.71, 0.29, 0.5)
const DEFEAT_RED := Color(1.0, 0.72, 0.68)
const DEFEAT_GLOW := Color(0.788, 0.227, 0.192, 0.55)
const CHANNEL_CLEAR := Color(0.35, 0.85, 0.6, 0.9)
const CHANNEL_LOST := Color(0.86, 0.32, 0.28, 0.95)

## ⚠️ SANS ACCENTS. La police d'interface (Press Start 2P) n'en porte pas : un « É »
## rendrait un carré vide. Tout l'écran suit déjà cette règle — « PALE LEVIATHAN
## DETRUIT », « RETOUR AU TITRE », « CANAL DEGAGE ».
const _TITLE: Dictionary = {
	Outcome.VICTORY: "VICTOIRE",
	Outcome.DEFEAT: "DEFAITE",
}
const _TAGLINE: Dictionary = {
	Outcome.VICTORY: "PALE LEVIATHAN DETRUIT  ·  SECTEUR SECURISE",
	Outcome.DEFEAT: "SPECTER-9 PERDU  ·  MISSION INTERROMPUE",
}
const _REPLAY_LABEL: Dictionary = {
	Outcome.VICTORY: "REJOUER",
	Outcome.DEFEAT: "REESSAYER",
}
const _CHANNEL: Dictionary = {
	Outcome.VICTORY: "CANAL DEGAGE",
	Outcome.DEFEAT: "SIGNAL PERDU",
}
## Le rappel de touches nomme la MÊME action que le bouton. Laissé fixe, il annonçait
## « REJOUER » sous un bouton « REESSAYER » : deux mots pour une touche, sur un écran
## dont c'est la seule instruction.
const _CONTROLS: Dictionary = {
	Outcome.VICTORY: "REJOUER  ENTREE     ·     TITRE  ECHAP",
	Outcome.DEFEAT: "REESSAYER  ENTREE     ·     TITRE  ECHAP",
}

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _scene_router: SceneRouterScript = get_node("/root/SceneRouter")
@onready var _audio: AudioManagerScript = get_node("/root/AudioManager")
@onready var _scrim: ColorRect = %Scrim
@onready var _overlay: Control = %Overlay
@onready var _menu: VBoxContainer = %Menu
@onready var _fade: ColorRect = %Fade

var _leaving: bool = false
var _muting_focus: bool = false

## Appelé par le niveau entre instantiate() et add_child() : _ready() n'a pas encore
## tourné, donc on n'adresse ici QUE des nœuds (les %-noms sont résolus dès
## l'instanciation), jamais un @onready.
func setup(score: int, outcome: Outcome = Outcome.VICTORY) -> void:
	(%ScoreValue as Label).text = "%08d" % score
	# Le rang note le SCORE, pas l'issue : une défaite tardive vaut mieux qu'une défaite
	# immédiate, et le rapport doit le dire plutôt que d'afficher un tiret punitif.
	(%RankValue as Label).text = _rank(score)
	var title := %Title as Label
	title.text = _TITLE[outcome]
	var won := outcome == Outcome.VICTORY
	title.add_theme_color_override("font_color", VICTORY_GOLD if won else DEFEAT_RED)
	title.add_theme_color_override("font_shadow_color", VICTORY_GLOW if won else DEFEAT_GLOW)
	(%Tagline as Label).text = _TAGLINE[outcome]
	(%ReplayButton as Button).text = _REPLAY_LABEL[outcome]
	# Le canal : dégagé quand la mission est remplie, perdu quand le chasseur l'est.
	var comms := %CommsText as Label
	comms.text = _CHANNEL[outcome]
	comms.add_theme_color_override("font_color", CHANNEL_CLEAR if won else CHANNEL_LOST)
	(%Pip as ColorRect).color = CHANNEL_CLEAR if won else CHANNEL_LOST
	(%Controls as Label).text = _CONTROLS[outcome]

func _ready() -> void:
	var target_alpha := _scrim.color.a
	_scrim.color.a = 0.0
	_overlay.modulate.a = 0.0
	var buttons := _buttons()
	for button in buttons:
		button.focus_entered.connect(_on_focus_changed)
	if not buttons.is_empty():
		# Le focus est pris ici, comme sur la pause : sans lui, il fallait cliquer
		# avant que le clavier réponde. Son tic est étouffé — le fanfare de victoire
		# occupe déjà la bande son à cet instant.
		_muting_focus = true
		buttons[0].grab_focus()
		_muting_focus = false
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(_scrim, "color:a", target_alpha, RAISE_TIME)
	tween.tween_property(_overlay, "modulate:a", 1.0, RAISE_TIME)

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

## ui_cancel est consommé ici même si l'écran n'en faisait rien : sinon Échap
## ouvrirait le menu de pause DERRIÈRE le rapport (le calque de pause vit toujours
## dans l'arbre, au layer 20), et le joueur se retrouverait avec deux menus empilés
## dont un invisible.
func _unhandled_input(event: InputEvent) -> void:
	if _leaving:
		return
	if event.is_action_pressed("ui_accept"):
		_on_replay_pressed()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_cancel"):
		_on_title_pressed()
		get_viewport().set_input_as_handled()

# --- Actions ------------------------------------------------------------------

func _on_replay_pressed() -> void:
	_audio.play(&"ui_confirm")
	_leave(func() -> void:
		_game_state.reset_session()
		get_tree().reload_current_scene())

func _on_title_pressed() -> void:
	_audio.play(&"ui_confirm")
	_leave(func() -> void:
		_game_state.reset_session()
		# Repasser l'état AVANT de router : sans ça, `current` reste sur la phase de
		# combat alors qu'on affiche le titre, et le lancement suivant est refusé
		# sans que rien ne le montre à l'écran.
		_game_state.transition_to(GameStateScript.State.BOOT)
		_scene_router.goto_scene(BOOT_SCENE))

## Fondu au noir avant de changer de scène. SceneRouter comme reload_current_scene
## font une coupe sèche : sans ça, on passait du rapport au jeu d'une image à l'autre.
func _leave(action: Callable) -> void:
	if _leaving:
		return
	_leaving = true
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", 1.0, FADE_TIME)
	tween.tween_callback(action)

static func _rank(score: int) -> String:
	if score >= 40000:
		return "S"
	if score >= 25000:
		return "A"
	if score >= 12000:
		return "B"
	return "C"
