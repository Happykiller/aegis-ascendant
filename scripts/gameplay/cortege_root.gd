extends Node3D
## Le niveau 2 : le survol du Long Cortège, de la proue vers l'arrière.
##
## ⚠️ CE SCRIPT NE COPIE PAS `graybox_root.gd`, ET C'EST DÉLIBÉRÉ. Celui-ci fait 1 470 lignes,
## précharge ses deux boss et pilote un arc de six phases en dur : le dupliquer aurait donné
## deux fichiers qui divergent au premier réglage. Le niveau 2 n'a pas de phases, il a une
## traversée — c'est un autre jeu, donc un autre script. Ce qui est GÉNÉRIQUE est réutilisé tel
## quel : `BulletManager`, `FighterHUD`, `GameplayPlane`, `PhaseTransition`, `PickupManager`.
##
## Autoloads résolus par chemin (convention projet) : garde le script compilable en mode
## `--script`, où les globales d'autoload n'existent pas.

const GameStateScript := preload("res://scripts/core/game_state.gd")
const SettingsManagerScript := preload("res://scripts/core/settings_manager.gd")
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const MissionReportScene := preload("res://scenes/ui/mission_report.tscn")
const TUNING := preload("res://resources/levels/long_cortege_tuning.tres")
const LYRA_LINES := preload("res://resources/dialogue/lyra_cortege.tres")
const BRIEFINGS := preload("res://resources/dialogue/cortege_briefings.tres")

## Ce que Lyra dit en entrant dans un troncon. ⚠️ PAR TRONÇON ET NON PAR ÉVÉNEMENT, parce que ce
## niveau n'a pas d'événements : rien ne change pendant trois minutes et demie, sauf ce que le
## joueur comprend. La progression du RÉCIT est donc la seule progression qu'il ait, et elle est
## portée par la seule chose qui avance — la coque sous lui.
const SECTION_LINES: Array[StringName] = [
	&"survey_start", &"hull_guns", &"bay_first", &"spine_seen", &"ambry",
]

## Combien de temps le rapport attend après la dernière réplique.
##
## ⚠️ IL ATTEND PARCE QUE LA DERNIÈRE RÉPLIQUE EST LA SEULE QUI COMPTE. C'est là que Lyra avoue
## avoir lu le dossier avant le décollage — la fracture de tout l'acte I. Enchaîner le rapport
## par-dessus la couperait au milieu, et le joueur ne saurait jamais ce qu'il vient de manquer.
## Mesuré, pas estimé : la voix dure 5,45 s et la réplique tient 6,5 s à l'écran.
const REPORT_DELAY := 7.5

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _settings: SettingsManagerScript = get_node_or_null("/root/SettingsManager")
@onready var _audio: AudioManagerScript = get_node("/root/AudioManager")
@onready var _flyby: CortegeFlyby = $CortegeFlyby
@onready var _hud: CanvasLayer = get_node_or_null("FighterHUD") as CanvasLayer
@onready var _player: Node3D = get_node_or_null("PlayerFighter") as Node3D
@onready var _backdrop: Node3D = get_node_or_null("SpaceBackdrop") as Node3D
@onready var _bullets: BulletManager = get_node("BulletManager")
@onready var _vfx: VFXManager = get_node("VFXManager")
@onready var _hardpoints: CortegeHardpoints = $Hardpoints

var _pause: PauseScreen = null
var _finished: bool = false
var _defeated: bool = false
## ⚠️ « PREMIÈRE FOIS » ET NON « À CHAQUE FOIS ». Sept ponts et cinq nœuds tombent dans une
## partie : répéter la même réplique à chacun la userait jusqu'au bruit de fond, et couvrirait
## la réplique de tronçon qui, elle, porte le récit.
var _said_bay_down: bool = false
var _said_node_down: bool = false

# --- Les zones de debug -------------------------------------------------------
#
# ⚠️ ELLES MANQUAIENT ICI, ET NULLE PART AILLEURS. `SolidsOverlay` existe depuis le
# 2026-08-28 et le niveau 1 le monte ; le niveau 2 ne le montait pas, donc ses dix-sept
# tourelles, ses sept ponts et ses cinq nœuds n'avaient AUCUNE représentation visible de leur
# volume de collision. Or c'est le seul niveau du jeu où l'on tire sur des pièces posées sur
# un décor qui défile : quand un tir ne fait rien, la question « ai-je visé à côté, ou la
# cible n'est-elle pas encore armée ? » ne se tranche pas à l'œil.
#
# Les réglages valent déjà `OS.is_debug_build()` par défaut (`settings_data.gd`) : en build de
# développement, tout est allumé sans rien demander.
var _solids: PlaneShapes = PlaneShapes.new()
var _solids_overlay: SolidsOverlay = null
var _survey_zones: SurveyZones = null
## +1 : tout forcé (`--show-solids`) ; -1 : tout coupé (`--hide-solids`) ; 0 : le réglage.
var _overlay_force: int = 0

func _ready() -> void:
	for error in TUNING.validate():
		push_error("[Cortege] réglage invalide : %s" % error)
	# Le survol lit ses paramètres du réglage : la vitesse commande la durée, donc les fenêtres
	# de tir, donc tout l'équilibrage. Rien n'est saisi deux fois.
	_flyby.scroll_speed = TUNING.scroll_speed
	_flyby.section_length = TUNING.section_length
	_flyby.section_count = TUNING.section_count
	_flyby.section_entered.connect(_on_section_entered)
	_flyby.survey_finished.connect(_on_survey_finished)
	# ⚠️ LE FOND CÈDE LA PLACE, il ne se superpose pas (`ADR-0027`).
	if _backdrop != null:
		_backdrop.visible = false
	_pause = get_node_or_null("PauseScreen") as PauseScreen
	if _pause != null:
		_pause.pause_toggled.connect(_on_pause_toggled)
	_flyby.reveal(true)
	# ⚠️ APRÈS `reveal`, parce que `reveal` repose le décor : les points d'ancrage lisent leur
	# position dans le monde, et les monter avant reviendrait à les créer sur une coque qui n'est
	# pas encore là où elle sera.
	_hardpoints.build(_flyby.sections(), TUNING, _bullets, _player as PlayerFighterController, _vfx)
	_hardpoints.turret_destroyed.connect(_on_turret_destroyed)
	_hardpoints.bay_destroyed.connect(_on_bay_destroyed)
	_hardpoints.node_destroyed.connect(_on_node_destroyed)
	_hardpoints.section_silenced.connect(_on_section_silenced)
	# ⚠️ TOUS LES ENNEMIS, D'OÙ QU'ILS VIENNENT, ET APRÈS `build()`. Ce niveau en met en scène
	# de deux façons — la réception de proue par un `WaveSpawner`, les coques de pont par le
	# pool de leur baie — et un ennemi ne vaut des points qu'à UN seul endroit. Les brancher par
	# le groupe, comme le niveau 1, plutôt que source par source : deux chemins de score
	# finissent par diverger, et la première divergence est un double comptage que personne ne
	# remarque. Après `build()`, parce que c'est lui qui monte les pools des ponts.
	for node in get_tree().get_nodes_in_group("enemies"):
		var enemy := node as EnemyController
		if enemy != null:
			enemy.destroyed.connect(_on_enemy_destroyed)
	if _player != null and _player.has_signal("game_over"):
		_player.game_over.connect(_on_game_over)
	# ⚠️ OUTIL DE VÉRIFICATION, PAS UN RACCOURCI DE JEU. `--cortege-from=<n>` démarre le survol
	# au tronçon n : sans lui, juger la section 3 demande d'attendre deux minutes de défilement,
	# et une capture automatisée n'y arrive pas du tout. Même esprit que `--skip-to-*` du
	# niveau 1 et que `--leviathan-phase=2`, dont l'absence avait coûté trois lancements.
	var args := OS.get_cmdline_user_args()
	_solids_overlay = SolidsOverlay.new()
	_solids_overlay.name = "SolidsOverlay"
	add_child(_solids_overlay)
	_survey_zones = SurveyZones.new()
	_survey_zones.name = "SurveyZones"
	add_child(_survey_zones)
	if "--show-solids" in args:
		_overlay_force = 1
	elif "--hide-solids" in args:
		_overlay_force = -1
	for arg in args:
		if arg.begins_with("--cortege-from="):
			var section := maxi(arg.substr(15).to_int() - 1, 0)
			_flyby.skip_to_section(section)
			print("[Cortege] saut au tronçon %d" % (section + 1))
	# ⚠️ L'INDICATEUR EST DEMANDÉ PAR LE NIVEAU, PAS POSÉ PAR LE HUD. Le niveau 1 traverse six
	# lieux et n'a rien à jauger : une barre qui ne bouge pas y serait pire qu'aucune barre.
	if _hud != null and _hud.has_method("show_survey"):
		_hud.show_survey(TUNING.section_count)
	if _flyby.is_stand_in():
		print("[Cortege] coque DOUBLÉE — %s absent" % CortegeFlyby.DECOR_PATH.get_file())
	print("[Cortege] survol — %d sections, %.1f u/s, %.0f s attendues"
		% [TUNING.section_count, TUNING.scroll_speed, TUNING.level_duration()])

# --- Ce que valent les trois mécaniques ---------------------------------------
#
# ⚠️ LE SCORE EST DANS LE RÉGLAGE, PAS ICI. Ce sont des paramètres d'équilibrage : ils se
# recalent en jouant, et un chiffre écrit dans le script du niveau échapperait à `validate()`
# comme aux tests (spec §31).

func _on_turret_destroyed(_turret: CortegeTurret) -> void:
	_game_state.add_score(TUNING.turret_score)

## ⚠️ UN PONT ABATTU S'ANNONCE. Il coûte quinze cents points de vie, soit les deux tiers de ce
## qu'un joueur de référence peut placer dans sa fenêtre : sans un retour franc, l'effort le plus
## cher du niveau se solderait par un silence.
func _on_bay_destroyed(bay: CortegeBay) -> void:
	_game_state.add_score(TUNING.bay_score)
	print("[Cortege] pont d'envol détruit — tronçon %02d" % (bay.section + 1))
	if _hud != null and _hud.has_method("show_banner"):
		_hud.show_banner("PONT D'ENVOL DÉTRUIT", Color("d93d9c"), 1.8)
	if not _said_bay_down:
		_said_bay_down = true
		_lyra(&"bay_down")

func _on_node_destroyed(node: CortegeSpineNode) -> void:
	_game_state.add_score(TUNING.node_score)
	print("[Cortege] nœud d'épine %02d abattu" % (node.section + 1))
	if not _said_node_down:
		_said_node_down = true
		_lyra(&"node_down")

## ⚠️ C'EST ICI QUE LA TROISIÈME MÉCANIQUE DEVIENT COMPRÉHENSIBLE, ou nulle part. La récompense
## d'un nœud arrive quarante secondes plus tard, sur un tronçon que le joueur n'a pas encore vu :
## rien à l'écran ne relie la cause à l'effet. Le niveau doit donc DIRE ce qui vient de se passer,
## au moment où ça se passe, et nommer sa conséquence.
func _on_section_silenced(section: int, turrets: int) -> void:
	print("[Cortege] tronçon %02d éteint — %d tourelles" % [section + 1, turrets])
	if turrets <= 0:
		return
	if _hud != null and _hud.has_method("show_banner"):
		_hud.show_banner("TRONÇON %02d ÉTEINT · %d TOURELLES" % [section + 1, turrets],
			Color("7a4de8"), 2.0)

func _on_enemy_destroyed(enemy: EnemyController) -> void:
	_game_state.add_score(enemy.data.score_value)

## ⚠️ LA JAUGE SE MET À JOUR ICI ET NON DANS LE HUD. Le HUD ne connaît aucun niveau en
## particulier — c'est ce qui lui permet de servir les deux —, et le survol est la seule chose
## qui sache où l'on en est. Même partage que `show_boss` / `set_boss_health`.
func _process(_delta: float) -> void:
	if _hud != null and not (_finished or _defeated):
		_hud.set_survey(_flyby.progress(), _flyby.current_section())
	_draw_debug_zones()

## ⚠️ TOUT CE QUI EXISTE DANS LE PLAN, ET DANS UNE SEULE PASSE. Les cibles viennent du
## gestionnaire de balles — donc tourelles, ponts, nœuds, coques lâchées et chasseur, sans que
## ce niveau ait à les énumérer —, et les fenêtres de tir viennent du réglage. Les deux couches
## sont distinctes parce qu'elles répondent à deux questions différentes : « où est la
## hitbox ? » et « à partir de quand puis-je la toucher ? ».
func _draw_debug_zones() -> void:
	if _solids_overlay == null:
		return
	var bodies := _overlay_force > 0
	var targets := _overlay_force > 0
	var screens := _overlay_force > 0
	if _overlay_force == 0 and _settings != null:
		var debug: SettingsData = _settings.get_debug()
		bodies = debug.debug_bodies
		targets = debug.debug_targets
		screens = debug.debug_screens
	var fighter := _player as PlayerFighterController
	if fighter != null and fighter.stats != null:
		_solids_overlay.draw(_solids, fighter.plane_lift, fighter.plane_position,
			fighter.plane_forward(), fighter.stats.body_half_length, fighter.stats.body_radius,
			_bullets.targets() if _bullets != null else [], null, bodies, targets, screens)
	# Les fenêtres suivent la couche des CIBLES : elles décrivent quand une cible devient une
	# cible, pas où se trouve un corps.
	if _survey_zones != null:
		_survey_zones.draw(TUNING, targets, _hardpoints)

func _on_section_entered(index: int) -> void:
	print("[Cortege] SECTION %02d / %02d" % [index + 1, TUNING.section_count])
	if _hud != null and _hud.has_method("show_banner"):
		_hud.show_banner("SECTION %02d" % (index + 1), Color("d93d9c"), 1.4)
	if index >= 0 and index < SECTION_LINES.size():
		_lyra(SECTION_LINES[index])

## Le nom de la « phase » courante, pour l'écran de pause. ⚠️ CE NIVEAU N'A PAS DE PHASES : ses
## briefings sont indexés par TRONÇON, et le nom se fabrique. Le contrat de `BriefingBook` reste
## le même — on cherche par NOM, jamais par rang (`ADR-0034`).
func phase_label() -> String:
	return "SECTION_%02d" % (_flyby.current_section() + 1)

## ⚠️ C'EST LE SEUL ÉCRAN OÙ LE JOUEUR A LE TEMPS DE LIRE, et ce niveau en a plus besoin que
## l'autre : il traverse UN SEUL objet pendant trois minutes et demie, et rien d'autre ne lui dit
## où il en est de la coque.
func _on_pause_toggled(is_paused: bool) -> void:
	if _hud != null:
		_hud.visible = not is_paused
	if is_paused and _pause != null:
		_pause.show_briefing(BRIEFINGS.find(StringName(phase_label())))

func _lyra(key: StringName) -> void:
	if _hud == null:
		return
	var line := LYRA_LINES.find(key)
	# Même garde qu'au niveau 1 : une réplique qui ne part pas ne se voit nulle part, et sept
	# d'entre elles y sont restées muettes une soirée entière, fichiers en place.
	if line == null:
		print("[Lyra] clé inconnue : %s" % key)
	else:
		print("[Lyra] %s" % key)
	_hud.say(line)

## ⚠️ LE CORTÈGE N'EST PAS ABATTU, IL CONTINUE SA ROUTE. C'est le premier adversaire du jeu que
## le joueur ne peut pas détruire, et c'est ce qui doit rester de lui (`docs/lore/NULL_CHOIR.md`).
## Ce qui se termine ici, c'est la traversée — pas lui.
func _on_survey_finished() -> void:
	if _finished or _defeated:
		return
	_finished = true
	print("[Cortege] VICTORY — score %d" % _game_state.score)
	_lyra(&"survey_end")
	_game_state.transition_to(GameStateScript.State.VICTORY)
	get_tree().create_timer(REPORT_DELAY).timeout.connect(
		_show_report.bind(MissionReport.Outcome.VICTORY))

func _on_game_over() -> void:
	if _finished or _defeated:
		return
	_defeated = true
	print("[Cortege] all fighters lost — DEFEAT, score %d" % _game_state.score)
	_game_state.transition_to(GameStateScript.State.GAME_OVER)
	get_tree().create_timer(1.6).timeout.connect(
		_show_report.bind(MissionReport.Outcome.DEFEAT))

func _show_report(outcome: MissionReport.Outcome) -> void:
	var screen := MissionReportScene.instantiate()
	screen.setup(_game_state.score, outcome)
	add_child(screen)
	if _hud != null:
		_hud.visible = false
