class_name DialogueBox
extends PanelContainer
## La bulle par laquelle Lyra parle : son nom, son rôle, ce qu'elle dit, l'oscillogramme du
## canal et la pastille « MESSAGE n/N ».
##
## ⚠️ ELLE REMPLACE UNE BANNIÈRE, ET C'EST TOUT LE SUJET. Le jeu disait déjà des choses —
## « DANS LE NOYAU », « CHAMP D'ASTÉROÏDES » — mais du **mobilier** les disait. Ici quelqu'un
## les dit (`ADR-0035`). La différence n'est pas cosmétique : une information qui vient d'une
## personne se retient, et le joueur apprend à qui faire confiance.
##
## ## Ce qu'elle ne fait pas
##
## Elle ne compte pas ses pages. `DialogueScript.page_label()` le fait, parce que le compte
## appartient à la DONNÉE : laisser l'affichage le calculer, c'est le voir diverger le jour
## où une réplique s'ajoute.
##
## ⚠️ **ZÉRO ALLOCATION EN BOUCLE** (spec §31) : la frappe avance un compteur de caractères
## et écrit `visible_ratio_characters` — elle ne reconstruit jamais la chaîne.

## Un tir de comms par ligne, pas par caractère : le bip par caractère est charmant deux
## secondes et fatigant à la troisième réplique.
signal line_started(line: DialogueLine)
## La réplique a fini de s'écrire ET de tenir : l'appelant peut enchaîner.
signal line_finished
## Le joueur a demandé la suite (clic, Entrée, Espace) — ou à voir la ligne d'un coup.
signal advance_requested
## Elle a une réplique à dire à voix haute. L'écran qui la monte la joue — la bulle ne
## connaît pas l'`AudioManager` (règle du projet : aucun identifiant d'autoload dans un
## script, sinon le mode `--script` ne compile plus et TOUTE la suite tombe).
signal voice_requested(cue: StringName)

## Vitesse de frappe, en caractères par seconde. ⚠️ Réglée sur la LECTURE, pas sur l'effet :
## à 45 c/s une phrase de la maquette s'écrit en une seconde et demie, ce qui laisse le temps
## de la lire sans donner l'impression d'attendre.
const TYPE_SPEED := 45.0
## Ce que la frappe vaut comme « niveau de voix » tant qu'aucun audio ne joue. Elle donne son
## amplitude à l'oscillogramme et sa bouche au portrait : sans voix, elle parle quand même.
const TYPING_LEVEL := 0.55
## Largeur allouée à l'oscillogramme dans la bulle. `CommsTrace` trace sur 232 px fixes :
## c'est un facteur d'échelle, pas un recadrage.
const TRACE_WIDTH := 96.0
## En dessous de ce niveau, le bus Voice est considéré silencieux. ⚠️ −42 dB et non −80 :
## le plancher de bruit d'un `.ogg` encodé n'est jamais un vrai silence, et un seuil trop bas
## ferait bavarder la bouche du portrait entre deux répliques.
const VOICE_SILENCE_DB := -42.0

var _name_label: Label
var _role_label: Label
var _text_label: Label
var _page_label: Label
var _trace: CommsTrace
var _line: DialogueLine = null
var _typed: float = 0.0
var _hold_left: float = 0.0
var _finished: bool = false
## L'index du bus `Voice`, résolu UNE fois. ⚠️ `get_bus_index()` fait une recherche par NOM
## dans la table des bus : appelée depuis `_process`, elle payait ce parcours soixante fois
## par seconde pour une valeur qui ne bouge jamais. -2 = pas encore cherché.
var _voice_bus: int = -2

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	add_theme_stylebox_override("panel", _frame())
	_build()

## Le cadre biseauté de l'interface Helios. ⚠️ Sans lui, la bulle est une bande sombre qui
## flotte : la capture du 2026-08-28 l'a montrée posée sur la nébuleuse, sans bord, illisible
## là où le fond est clair. Un panneau se lit à son BORD, pas à son fond.
func _frame() -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = Color(0.02, 0.05, 0.10, 0.86)
	box.border_color = Color(0.161, 0.902, 1.0, 0.75)
	box.set_border_width_all(2)
	box.set_corner_radius_all(0)
	# Coins coupés en haut à gauche et en bas à droite : c'est la signature des cadres de
	# l'écran de pause et du HUD — trois écrans, une seule interface.
	box.corner_radius_top_left = 14
	box.corner_radius_bottom_right = 14
	box.set_content_margin_all(16)
	box.content_margin_left = 22.0
	return box

func _build() -> void:
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 6)
	add_child(column)

	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 12)
	column.add_child(header)

	_name_label = Label.new()
	_name_label.add_theme_font_size_override("font_size", 16)
	_name_label.add_theme_color_override("font_color", Color("3fd9e8"))
	header.add_child(_name_label)

	_role_label = Label.new()
	_role_label.add_theme_font_size_override("font_size", 9)
	_role_label.add_theme_color_override("font_color", Color(0.875, 0.965, 1.0, 0.6))
	_role_label.size_flags_vertical = Control.SIZE_SHRINK_END
	header.add_child(_role_label)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	header.add_child(spacer)

	_page_label = Label.new()
	_page_label.add_theme_font_size_override("font_size", 10)
	_page_label.add_theme_color_override("font_color", Color(0.875, 0.965, 1.0, 0.55))
	_page_label.size_flags_vertical = Control.SIZE_SHRINK_END
	header.add_child(_page_label)

	var body := HBoxContainer.new()
	body.add_theme_constant_override("separation", 14)
	column.add_child(body)

	# ⚠️ LE MÊME APPAREIL QUE L'ACCUEIL ET LA PAUSE. `CommsTrace` porte déjà l'oscillogramme du
	# bloc COMMS, points préalloués et régimes LIVE/HOLD. En réécrire un second ferait deux
	# oscillogrammes qui dérivent — et c'est justement ce qui fait que les écrans du jeu se
	# lisent comme une seule interface.
	# ⚠️ IL TRACE SUR `SPAN` = 232 px FIXES, depuis sa propre origine et centré sur y = 0.
	# Posé tel quel dans un hôte de 88 px, il débordait et traversait le texte — vu à la
	# capture. On le met à l'échelle plutôt que de toucher à `CommsTrace`, que l'accueil et
	# la pause partagent : le corriger « pour la bulle » le casserait ailleurs.
	var trace_host := Control.new()
	trace_host.name = "TraceHost"
	trace_host.custom_minimum_size = Vector2(TRACE_WIDTH, 40.0)
	trace_host.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	trace_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	trace_host.clip_contents = true
	body.add_child(trace_host)
	_trace = CommsTrace.new()
	_trace.width = 2.0
	_trace.default_color = Color("3fd9e8")
	_trace.scale = Vector2(TRACE_WIDTH / CommsTrace.SPAN, 0.62)
	_trace.position = Vector2(0.0, 20.0)
	trace_host.add_child(_trace)

	_text_label = Label.new()
	_text_label.add_theme_font_size_override("font_size", 17)
	_text_label.add_theme_color_override("font_color", Color(0.95, 0.98, 1.0))
	_text_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(_text_label)

## Affiche une réplique et la fait s'écrire. `page` vient du script, jamais d'ici.
func play(line: DialogueLine, page: String) -> void:
	_line = line
	_typed = 0.0
	_finished = false
	_hold_left = line.hold
	_name_label.text = String(line.speaker)
	_role_label.text = line.role
	_page_label.text = page
	_text_label.text = line.text
	_text_label.visible_ratio = 0.0
	var colour := line.mood_colour()
	_name_label.add_theme_color_override("font_color", colour)
	if _trace != null:
		_trace.default_color = colour
		_trace.mode = CommsTrace.Mode.LIVE
	if line.voice_cue != &"":
		voice_requested.emit(line.voice_cue)
	line_started.emit(line)

## Le texte entier, tout de suite. Le premier appui saute la frappe, le second enchaîne —
## c'est la convention du genre, et un joueur pressé ne doit jamais être puni.
func reveal_all() -> void:
	if _line == null:
		return
	_typed = float(_line.text.length())
	_text_label.visible_ratio = 1.0

func is_typing() -> bool:
	return _line != null and _typed < float(_line.text.length())

## L'amplitude de sa voix à cet instant : elle nourrit l'oscillogramme et la bouche du
## portrait.
##
## ⚠️ C'EST LE BUS QUI DIT LA VÉRITÉ, PAS UN DRAPEAU. On lit le crête-mètre du bus `Voice` :
## s'il parle, la bouche suit le son réel ; s'il se tait, la frappe en tient lieu et elle
## parle quand même. Aucun état à tenir, donc aucun état à désynchroniser — et le jour où la
## voix est livrée, rien ne change ici.
func speech_level() -> float:
	if _voice_bus == -2:
		_voice_bus = AudioServer.get_bus_index("Voice")
	if _voice_bus >= 0:
		var level := level_from_db(AudioServer.get_bus_peak_volume_left_db(_voice_bus, 0))
		if level > 0.0:
			return level
	return TYPING_LEVEL if is_typing() else 0.0

## Le crête-mètre, en niveau utilisable. Pur, donc mesurable sans monter une scène ni jouer
## un son — c'est le seul moyen de garder les bornes honnêtes.
static func level_from_db(peak_db: float) -> float:
	if peak_db <= VOICE_SILENCE_DB or is_inf(peak_db) or is_nan(peak_db):
		return 0.0
	return clampf(inverse_lerp(VOICE_SILENCE_DB, 0.0, peak_db), 0.0, 1.0)

func _process(delta: float) -> void:
	if _line == null:
		return
	if is_typing():
		_typed += TYPE_SPEED * delta
		_text_label.visible_ratio = clampf(_typed / maxf(float(_line.text.length()), 1.0), 0.0, 1.0)
		return
	if _trace != null:
		_trace.mode = CommsTrace.Mode.HOLD
	if _finished:
		return
	if _hold_left > 0.0:
		_hold_left -= delta
		return
	_finished = true
	line_finished.emit()

## ⚠️ ELLE ÉCOUTE, MAIS N'AVALE PAS. Le menu de l'accueil garde son clavier : la bulle ne
## consomme que ce qui la concerne, et seulement quand une réplique est à l'écran.
func _gui_input(event: InputEvent) -> void:
	if _line == null:
		return
	var pressed: bool = event is InputEventMouseButton and event.pressed
	if pressed:
		accept_event()
		_advance()

func handle_key(event: InputEvent) -> bool:
	if _line == null:
		return false
	if event.is_action_pressed(&"ui_accept"):
		_advance()
		return true
	return false

func _advance() -> void:
	if is_typing():
		reveal_all()
		return
	advance_requested.emit()
