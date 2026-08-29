class_name LevelRoot
extends Node3D
## Le SOCLE d'un niveau — ce que tout niveau monte, quel que soit ce qu'on y joue.
##
## ⚠️ IL EXISTE PARCE QUE DEUX NIVEAUX SUFFISENT À MONTRER LA DUPLICATION, ET QU'UN TROISIÈME
## LA RENDRAIT IRRATTRAPABLE. `graybox_root.gd` et `cortege_root.gd` montaient déjà chacun,
## séparément : les mêmes sept services, le runtime de combat, les mêmes calques de debug, le
## même écran de pause avec son briefing, le même rapport de mission, le même raccourci de
## réplique. Rien de tout cela n'appartient au couloir d'Ossane ni au Long Cortège.
##
## ⚠️ ET LA DUPLICATION N'EST PAS UN DÉFAUT DE PROPRETÉ, C'EST UN GÉNÉRATEUR DE BUGS SILENCIEUX.
## Chaque chose montée deux fois est une chose qu'on peut oublier une fois : le niveau 2 a été
## joué SANS voix, SANS explosions d'ennemi, SANS écrasement et SANS zones de debug — quatre
## défauts, quatre oublis, aucun message d'erreur. Un socle ne s'oublie pas : on en hérite.
##
## ## Le partage, en une phrase
##
##     Le socle monte et câble. Le NIVEAU décide de ce qui se passe.
##
## Ici : trouver les services, créer le runtime, adopter les unités, brancher le joueur et le
## HUD, ouvrir la pause, dessiner les zones de debug, afficher le rapport. Pas ici : quelles
## vagues, quels boss, quel décor, quel enchaînement — et c'est pour ça que les deux méthodes
## que le socle appelle sans les connaître, `phase_label()` et `dialogue()`, sont laissées aux
## niveaux.

# --- Les services, par NOM DE NŒUD ---------------------------------------------
#
# ⚠️ PAR NOM ET NON PAR CHEMIN ABSOLU : ce sont des enfants du niveau, pas des autoloads. Un
# `get_node_or_null` tolère leur absence — un banc de test monte le socle sans scène, et une
# scène de niveau peut légitimement se passer de ramassage ou d'écran de pause.

const GameStateScript := preload("res://scripts/core/game_state.gd")
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const SettingsManagerScript := preload("res://scripts/core/settings_manager.gd")
const MissionReportScene := preload("res://scenes/ui/mission_report.tscn")

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _audio: AudioManagerScript = get_node("/root/AudioManager")
@onready var _settings: SettingsManagerScript = get_node_or_null("/root/SettingsManager")

var _bullets: BulletManager = null
var _vfx: VFXManager = null
var _hud: CanvasLayer = null
var _player: PlayerFighterController = null
var _pickups: Node = null
var _pause: PauseScreen = null
var _camera: Node = null

## Les lois du combat. ⚠️ CRÉÉES ICI, UNE FOIS : c'est ce qui garantit qu'aucun niveau ne peut
## les oublier, et `scripts/lint-regles.sh` refuse un script racine qui ne les convoque pas.
var _runtime: CombatRuntime = null

## Le voile de transition. ⚠️ AU SOCLE PARCE QU'IL SERT À L'ARC : un temps qui change le décor
## le fait à l'écran éteint, et c'est le directeur qui le demande — pas le niveau.
var _transition: PhaseTransition = null

## L'arc, et celui qui le joue. Un niveau sans arc n'en monte pas : le survol du Long Cortège
## n'a qu'un seul temps, et le déclarer serait plus de cérémonie que de structure.
var _director: EncounterDirector = null

## Les obstacles du plan, reconstruits à chaque image physique par le niveau.
var _solids: PlaneShapes = PlaneShapes.new()
var _solids_overlay: SolidsOverlay = null
## +1 : tout forcé (`--show-solids`) ; -1 : tout coupé (`--hide-solids`) ; 0 : le réglage.
var _overlay_force: int = 0

# ==========================================================================
# Le montage
# ==========================================================================

## À appeler EN PREMIER depuis le `_ready()` du niveau.
##
## ⚠️ IL NE S'APPELLE PAS TOUT SEUL. `_ready()` est virtuel en GDScript : un niveau qui
## surcharge `_ready()` sans appeler celui-ci ne monterait rien, en silence. Une méthode nommée
## se voit manquer à la lecture ; un `super._ready()` oublié, non.
func setup_level() -> void:
	_bullets = get_node_or_null("BulletManager") as BulletManager
	_vfx = get_node_or_null("VFXManager") as VFXManager
	_hud = get_node_or_null("FighterHUD") as CanvasLayer
	_player = get_node_or_null("PlayerFighter") as PlayerFighterController
	_pickups = get_node_or_null("PickupManager")
	_pause = get_node_or_null("PauseScreen") as PauseScreen
	_camera = get_node_or_null("CameraDirector")
	_setup_runtime()
	_setup_hud()
	_setup_pause()
	_setup_debug()
	_transition = PhaseTransition.new()
	_transition.name = "PhaseTransition"
	add_child(_transition)

## ⚠️ APRÈS que le niveau ait monté SES sources d'unités. Le runtime adopte par le groupe : les
## unités doivent être dans l'arbre. Le niveau 2 monte sept pools de ponts d'envol dans son
## propre `_ready()`, donc il rappelle `adopt_units()` ensuite.
func _setup_runtime() -> void:
	_runtime = CombatRuntime.new()
	_runtime.name = "CombatRuntime"
	add_child(_runtime)
	_runtime.bind(_game_state, _bullets, _vfx, _audio, _camera, _hud, _pickups, _player)
	adopt_units()

func adopt_units() -> void:
	if _runtime != null:
		_runtime.adopt(get_tree())

func _setup_hud() -> void:
	if _hud != null and _player != null:
		_hud.bind_player(_player)
		_hud.bind_score(_game_state)

## ⚠️ LE HUD S'EFFACE PENDANT LA PAUSE. L'écran de pause reprend l'interface entière — bloc
## d'identité en haut à gauche, COMMS en bas à gauche — et ces places sont celles du HUD : deux
## blocs de texte superposés ne se lisent ni l'un ni l'autre.
func _setup_pause() -> void:
	if _pause != null:
		_pause.pause_toggled.connect(_on_pause_toggled)

## ⚠️ LES CALQUES DE DEBUG SONT UN SOCLE, PAS UN LUXE DE NIVEAU. Le niveau 2 s'est joué sans
## eux parce qu'il ne les montait pas : ses dix-sept tourelles, ses sept ponts et ses cinq nœuds
## n'avaient aucune représentation visible de leur volume de collision, sur le seul niveau du
## jeu où l'on tire sur des pièces posées sur un décor qui défile.
func _setup_debug() -> void:
	_solids_overlay = SolidsOverlay.new()
	_solids_overlay.name = "SolidsOverlay"
	add_child(_solids_overlay)
	var args := OS.get_cmdline_user_args()
	if "--show-solids" in args:
		_overlay_force = 1
	elif "--hide-solids" in args:
		_overlay_force = -1

# ==========================================================================
# Ce que le socle rend au niveau
# ==========================================================================

## Les calques allumés à cet instant : forcés par drapeau, sinon lus dans les réglages — dont
## les défauts valent `OS.is_debug_build()`, donc tout est allumé en développement.
func debug_layers() -> Vector3i:
	if _overlay_force != 0:
		var on := 1 if _overlay_force > 0 else 0
		return Vector3i(on, on, on)
	if _settings == null:
		return Vector3i.ZERO
	var debug: SettingsData = _settings.get_debug()
	return Vector3i(1 if debug.debug_bodies else 0, 1 if debug.debug_targets else 0,
		1 if debug.debug_screens else 0)

## Dessine la représentation physique. `screens` est propre au niveau — un boss peut poser des
## murs qui arrêtent une balle, un survol n'en a aucun.
func draw_debug_zones(screens: PlaneShapes = null) -> void:
	if _solids_overlay == null or _player == null or _player.stats == null:
		return
	var layers := debug_layers()
	_solids_overlay.draw(_solids, _player.plane_lift, _player.plane_position,
		_player.plane_forward(), _player.stats.body_half_length, _player.stats.body_radius,
		_bullets.targets() if _bullets != null else [], screens,
		layers.x == 1, layers.y == 1, layers.z == 1)

## L'écran de fin. Le niveau dit l'issue ; le socle sait comment on la présente.
func show_report(outcome: MissionReport.Outcome) -> void:
	var screen := MissionReportScene.instantiate()
	screen.setup(_game_state.score, outcome)
	add_child(screen)
	if _hud != null:
		_hud.visible = false

## ⚠️ AU MOMENT DE LA PAUSE, PAS AU MONTAGE. Le briefing suit l'endroit où l'on est, et cet
## endroit change plusieurs fois par partie : le poser une fois pour toutes afficherait le
## premier secteur au milieu du dernier. C'est le NIVEAU qui sait où l'on en est — l'écran de
## pause ne connaît ni les phases, ni les tronçons, et n'a aucune raison de l'apprendre.
func _on_pause_toggled(is_paused: bool) -> void:
	if _hud != null:
		_hud.visible = not is_paused
	if is_paused and _pause != null:
		var book := briefings()
		if book != null:
			_pause.show_briefing(book.find(StringName(phase_label())))

## Fait parler la navigatrice. ⚠️ LA VOIX PART AVEC — c'est une loi, elle est dans le runtime,
## et l'oublier ne se voit nulle part : le panneau s'affiche, le texte défile, et le silence
## passe pour un choix. Le niveau 2 a été joué muet pour cette seule raison.
func say(key: StringName) -> void:
	if _runtime != null:
		_runtime.say(dialogue(), key)

## Monte le directeur et lui donne l'arc. À appeler après `setup_level()`, quand la scène est
## prête à jouer son premier temps.
func setup_arc(arc: LevelArc) -> EncounterDirector:
	_director = EncounterDirector.new()
	_director.name = "EncounterDirector"
	add_child(_director)
	_director.bind(self, arc)
	return _director

## Ferme l'écran, appelle `on_midpoint` quand il est plein, `on_finished` quand il rouvre.
##
## ⚠️ SANS VOILE, LES DEUX RAPPELS PARTENT QUAND MÊME, dans l'ordre. Un niveau monté sans nœud de
## transition — un banc, un mode dégradé — doit jouer son arc jusqu'au bout : un décor qui
## commute sèchement est un défaut visuel, un arc qui s'arrête est un jeu cassé.
func veil(on_midpoint: Callable, on_finished: Callable) -> void:
	if _transition == null:
		on_midpoint.call()
		on_finished.call()
		return
	_transition.midpoint.connect(on_midpoint, CONNECT_ONE_SHOT)
	_transition.finished.connect(on_finished, CONNECT_ONE_SHOT)
	_transition.play()

## Annonce. ⚠️ Bandeau ET son : un bandeau muet apparaît au moment où le joueur regarde
## ailleurs — il esquive — et il est déjà parti quand il revient.
func banner(text: String, colour: Color, hold: float) -> void:
	if _runtime != null:
		_runtime.banner(text, colour, hold)

# ==========================================================================
# Ce que le NIVEAU doit dire — le socle ne peut pas le savoir
# ==========================================================================

## Câble une mise en scène de boss avec les services de CE niveau. ⚠️ Le socle ne peut pas le
## faire : il ne connaît ni les répliques du niveau, ni son fond spatial, ni les réglages propres
## à tel boss.
func dress_boss_stage(stage: BossStage, _beat: LevelBeat) -> void:
	stage.bind(_runtime, _hud, _game_state, _bullets, _player, dialogue(), _camera)

## Ce que la mort d'un boss OUVRE. ⚠️ REND `true` QUAND LE NIVEAU PREND LA MAIN sur la suite :
## la finale Helios du niveau 1 dure 1,8 s, et enchaîner l'appontage par-dessus l'escamoterait.
## Rendre `false` laisse le directeur avancer tout de suite.
func on_boss_defeated(_beat: LevelBeat, _stage: BossStage, _world_position: Vector3) -> bool:
	return false

## ⚠️ UN TEMPS PEUT ÊTRE SAUTÉ, ET C'EST LE NIVEAU QUI LE SAIT. `--no-wave` supprime les deux
## vagues ; sans ce crochet, l'arc s'arrêterait sur un semeur qui ne se videra jamais.
func should_skip_beat(_beat: LevelBeat) -> bool:
	return false

## Où l'on en est, sous la forme que le livre de briefings emploie comme clé.
func phase_label() -> String:
	return ""

## Les répliques de ce niveau.
func dialogue() -> DialogueScript:
	return null

## Le livre de briefings de ce niveau.
func briefings() -> BriefingBook:
	return null
