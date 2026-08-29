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
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const MissionReportScene := preload("res://scenes/ui/mission_report.tscn")
const TUNING := preload("res://resources/levels/long_cortege_tuning.tres")

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _audio: AudioManagerScript = get_node("/root/AudioManager")
@onready var _flyby: CortegeFlyby = $CortegeFlyby
@onready var _hud: CanvasLayer = get_node_or_null("FighterHUD") as CanvasLayer
@onready var _player: Node3D = get_node_or_null("PlayerFighter") as Node3D
@onready var _backdrop: Node3D = get_node_or_null("SpaceBackdrop") as Node3D
@onready var _bullets: BulletManager = get_node("BulletManager")
@onready var _vfx: VFXManager = get_node("VFXManager")
@onready var _hardpoints: CortegeHardpoints = $Hardpoints

var _finished: bool = false
var _defeated: bool = false

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
	_flyby.reveal(true)
	# ⚠️ APRÈS `reveal`, parce que `reveal` repose le décor : les points d'ancrage lisent leur
	# position dans le monde, et les monter avant reviendrait à les créer sur une coque qui n'est
	# pas encore là où elle sera.
	_hardpoints.build(_flyby, TUNING, _bullets, _player as PlayerFighterController, _vfx)
	_hardpoints.turret_destroyed.connect(_on_turret_destroyed)
	_hardpoints.bay_destroyed.connect(_on_bay_destroyed)
	_hardpoints.node_destroyed.connect(_on_node_destroyed)
	_hardpoints.enemy_destroyed.connect(_on_enemy_destroyed)
	_hardpoints.section_silenced.connect(_on_section_silenced)
	if _player != null and _player.has_signal("game_over"):
		_player.game_over.connect(_on_game_over)
	# ⚠️ OUTIL DE VÉRIFICATION, PAS UN RACCOURCI DE JEU. `--cortege-from=<n>` démarre le survol
	# au tronçon n : sans lui, juger la section 3 demande d'attendre deux minutes de défilement,
	# et une capture automatisée n'y arrive pas du tout. Même esprit que `--skip-to-*` du
	# niveau 1 et que `--leviathan-phase=2`, dont l'absence avait coûté trois lancements.
	var args := OS.get_cmdline_user_args()
	for arg in args:
		if arg.begins_with("--cortege-from="):
			var section := maxi(arg.substr(15).to_int() - 1, 0)
			_flyby.skip_to_section(section)
			print("[Cortege] saut au tronçon %d" % (section + 1))
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

func _on_node_destroyed(node: CortegeSpineNode) -> void:
	_game_state.add_score(TUNING.node_score)
	print("[Cortege] nœud d'épine %02d abattu" % (node.section + 1))

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

func _on_section_entered(index: int) -> void:
	print("[Cortege] SECTION %02d / %02d" % [index + 1, TUNING.section_count])
	if _hud != null and _hud.has_method("show_banner"):
		_hud.show_banner("SECTION %02d" % (index + 1), Color("d93d9c"), 1.4)

## ⚠️ LE CORTÈGE N'EST PAS ABATTU, IL CONTINUE SA ROUTE. C'est le premier adversaire du jeu que
## le joueur ne peut pas détruire, et c'est ce qui doit rester de lui (`docs/lore/NULL_CHOIR.md`).
## Ce qui se termine ici, c'est la traversée — pas lui.
func _on_survey_finished() -> void:
	if _finished or _defeated:
		return
	_finished = true
	print("[Cortege] VICTORY — score %d" % _game_state.score)
	_game_state.transition_to(GameStateScript.State.VICTORY)
	_show_report(MissionReport.Outcome.VICTORY)

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
