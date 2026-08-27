extends Node3D
## Level director: sequences the level's phases (spec §5, §6, §37) and wires the
## player, HUD, VFX, camera, pickups and encounters together.
##   FIGHTER_WAVES -> MINI_BOSS -> ASTEROID_FIELD -> FINAL_BOSS -> DOCKING -> VICTORY
## Le joueur reste le chasseur de bout en bout (ADR-0010) : plus de transformation en
## forteresse ; le docking clot le niveau apres la defaite du boss final.

const GameStateScript := preload("res://scripts/core/game_state.gd")
const AudioManagerScript := preload("res://scripts/core/audio_manager.gd")
const MiniBossScene := preload("res://scenes/bosses/choir_harvester.tscn")
const FinalBossScene := preload("res://scenes/bosses/pale_leviathan.tscn")
const CitadelScene := preload("res://scenes/fortress/aegis_citadel.tscn")
const MissionReportScene := preload("res://scenes/ui/mission_report.tscn")

const _FINAL_BOSS_SCALE := 0.75

const _COLOR_ALLY := Color(0.247, 0.851, 0.91)
const _COLOR_GOLD := Color(0.894, 0.71, 0.29)

## Bannières du Pale Leviathan — les couleurs exactes du design (`docs/design/
## BOSS_PALE_LEVIATHAN.md`) : ivoire pour la structure qui cède, magenta pour la gueule.
const _BANNER_IVORY := Color("e8e2cf")
const _BANNER_MAGENTA := Color("d93d9c")

## Libellés des pastilles de sous-cibles, par phase. Numérotés parce que les pièces sont
## identiques (contrairement aux appendices nommés du Harvester) et abrégés pour tenir
## dans la jauge : P = plaque, N = nœud gravitique, E = épine. Le bandeau de phase donne
## le contexte, le numéro distingue la cible.
## Les quatre plaques de la phase 1. ⚠️ Il n'y a plus de rangée pour les nœuds ni pour
## les épines : ADR-0020 les a retirés du combat, ils ne sont plus que des pièces qui
## tombent. Une pastille sans cible derrière est un mensonge de HUD.
const _LEVIATHAN_PLATE_LABELS: PackedStringArray = ["P 1", "P 2", "P 3", "P 4"]

## Impact tints: the palette's cold impact flash when we strike an enemy hull, the
## shield's own cyan when something strikes us.
const _HULL_IMPACT_TINT := Color(0.851, 0.902, 0.949)
const _SHIELD_IMPACT_TINT := Color(0.247, 0.851, 0.91)

## Shield alarm thresholds (spec §8.3: audible warning under 25%). The alarm re-arms
## only above 35% so a shield hovering around the threshold does not stutter.
const _ALARM_TRIGGER_RATIO := 0.25
const _ALARM_REARM_RATIO := 0.35

## ⚠️ `MusicContext.LevelPhase` REFLÈTE cet enum PAR VALEUR, et `test_music_director.gd`
## le vérifie : les deux se modifient ensemble ou la musique se décale en silence.
## `ASTEROID_FIELD` s'insère entre les deux boss (ADR-0027) — la traversée qui sépare
## le Harvester du Leviathan.
enum Phase { FIGHTER_WAVES, MINI_BOSS, ASTEROID_FIELD, FINAL_BOSS, DOCKING, VICTORY }

## Temps laissé à la mort du dernier chasseur avant que le rapport ne se lève. L'explosion
## dure ~0,7 s (VfxExplosion.HEAVY) et la secousse doit retomber : couper plus tôt
## escamoterait la seule chose que le joueur attend de voir à cet instant.
const DEFEAT_HOLD := 1.6

## Une partie ne se perd qu'une fois. Sans ce verrou, une seconde émission de
## `game_over` empilerait un deuxième rapport par-dessus le premier.
var _defeated: bool = false

@onready var _game_state: GameStateScript = get_node("/root/GameState")
@onready var _wave_spawner: WaveSpawner = get_node_or_null("WaveSpawner")
## La vague du champ d'astéroïdes (ADR-0027) : montée et peuplée au même instant que
## la première, mais endormie. C'est `_start_asteroid_field()` qui la réveille.
@onready var _field_spawner: WaveSpawner = get_node_or_null("AsteroidFieldSpawner")
@onready var _vfx: VFXManager = get_node_or_null("VFXManager") as VFXManager
@onready var _camera_director: CameraDirector = get_node_or_null("CameraDirector") as CameraDirector
var _hit_stop: HitStop
## Âge du battement du repère de cible. Repart de zéro à chaque plongée : le battement doit
## commencer plein, pas au milieu d'un cycle hérité de la plongée précédente.
var _core_marker_age: float = 0.0
## Nombre de plaques déjà annoncées par la rangée de reconstruction. Évite de redresser la
## rangée à chaque image : `set_boss_limbs` repositionne toute la ligne.
var _regen_plates: int = 0

## Libellés de la rangée quand elle porte les VERROUS et non les plaques. Quatre lettres :
## la colonne est étroite, et « VERROU 1 » y déborderait.
## ⚠️ `var` et non `const` : un `PackedStringArray(...)` n'est pas une expression constante
## en GDScript, et le script entier refuse alors de se charger.
static var _LEVIATHAN_LOCK_LABELS := PackedStringArray(["V1", "V2", "V3", "V4", "V5", "V6"])
@onready var _player: PlayerFighterController = get_node_or_null("PlayerFighter") as PlayerFighterController
@onready var _hud: CanvasLayer = get_node_or_null("FighterHUD") as CanvasLayer
@onready var _pickups: PickupManager = get_node_or_null("PickupManager") as PickupManager
@onready var _bullets: BulletManager = get_node_or_null("BulletManager") as BulletManager
@onready var _bullet_manager: BulletManager = get_node_or_null("BulletManager") as BulletManager
@onready var _audio: AudioManagerScript = get_node_or_null("/root/AudioManager") as AudioManagerScript

var _phase: int = Phase.FIGHTER_WAVES
var _boss: BossController
var _citadel: AegisCitadel
var _final_boss: BossController
## Le module du boss final, gardé pour lire sa progression de combat (la musique la suit).
var _leviathan: LeviathanCombat

## Tout ce qui est solide dans le niveau, à cet instant. Rempli à chaque image par les boss
## en place, lu par le chasseur qui s'y conforme.
##
## ⚠️ UN SEUL JEU DE FORMES POUR TOUT LE NIVEAU, et il est REFAIT à chaque image sans jamais
## être réalloué (spec §26.1). Le niveau ne sait pas ce qu'il contient — ni plaques, ni bras,
## ni anneaux : chaque boss DÉCLARE ses formes par `fill_solids()`. C'est ce qui rend la loi
## « les corps ne se chevauchent pas » applicable au boss suivant sans toucher à ce fichier.
var _solids := PlaneShapes.new()

## Sonde de plongée (`--dive-probe`) : voir `_probe_dive()`.
var _dive_probe: bool = false
var _probe_clock: float = 0.0
## Enregistrement de partie (`--dive-trace`) : voir `_trace_dive()`. Accumulé en mémoire et
## écrit à la sortie — écrire 60 lignes par seconde sur le disque fausserait ce qu'on mesure.
var _dive_trace: bool = false
## Superposition des formes de collision (`--show-solids`).
var _solids_overlay: SolidsOverlay = null
var _trace_lines := PackedStringArray()
var _trace_age: float = 0.0

## Le module de combat du mini-boss, gardé pour ses formes solides. ⚠️ Testé par
## `is_instance_valid()` à chaque image et non vidé à sa mort : le Harvester est libéré par
## le niveau, et une référence morte lue une fois de trop planterait la partie sur la
## transition la plus chargée de l'arc.
var _harvester: HarvesterCombat
var _alarm_armed: bool = true
## `--no-wave` : aucune vague ne se joue, ni celle des chasseurs ni celle du champ.
var _waves_disabled: bool = false
## Le décor du champ d'astéroïdes (ADR-0027). Bâti au MONTAGE et caché, contrairement à
## `CoreInterior` qui se construit à la plongée : un survol se monte une fois pour toutes,
## et la spec §26.1 n'aime pas plus les décors alloués en jeu que les ennemis.
var _moon_flyby: MoonFlyby
## `--no-flyby` : la phase se joue sous le fond spatial habituel. Bissection de perf — le
## témoin d'un différentiel, c'est la même chose sans le réglage.
var _flyby_disabled: bool = false
## `--no-surface-maps` : le survol garde sa géométrie mais perd sa matière. Second témoin
## de bissection — `--no-flyby` isole le décor entier, celui-ci isole ses seules textures.
var _surface_maps_disabled: bool = false
## Le voile de raccord entre deux décors (lot 5 du plan inter-boss). Monté au MONTAGE et
## caché, comme le survol : un raccord alloué au moment où il sert arriverait en retard.
var _transition: PhaseTransition
## L'approche du boss final : le dernier puits gravitique qui monte (`BossApproach`).
## Pas une phase de l'enum — `MusicContext.LevelPhase` le reflète PAR VALEUR et
## `test_music_director.gd` le vérifie, donc y insérer une entrée décalerait la musique
## en silence. L'approche se joue DANS `ASTEROID_FIELD`, sur son propre lit musical.
var _approach_active: bool = false
var _approach_time: float = 0.0
## One instance for the whole run: resolving the musical state must not allocate.
var _music: MusicContext = MusicContext.new()
var _engine_running: bool = false

func _ready() -> void:
	_game_state.reset_session()
	for node in get_tree().get_nodes_in_group("enemies"):
		var enemy := node as EnemyController
		enemy.destroyed.connect(_on_enemy_destroyed)
		enemy.fired.connect(_on_enemy_fired)
		enemy.hit.connect(_on_enemy_hit)
	if _bullets != null:
		_bullets.target_hit.connect(_on_bullet_hit)
	if _wave_spawner != null:
		_wave_spawner.wave_cleared.connect(_on_wave_cleared)
		_wave_spawner.progress_changed.connect(_on_wave_progress)
	# Deux vagues, deux fins distinctes : celle des chasseurs ouvre sur le mini-boss,
	# celle du champ sur le boss final. La progression, elle, alimente la MÊME jauge
	# musicale — c'est toujours « où en est la vague en cours ».
	if _field_spawner != null:
		_field_spawner.wave_cleared.connect(_on_asteroid_field_cleared)
		_field_spawner.progress_changed.connect(_on_wave_progress)
	if _player != null:
		_player.hit_taken.connect(_on_player_hit)
		_player.destroyed_at.connect(_on_player_destroyed)
		_player.game_over.connect(_on_game_over)
		_player.fired.connect(_on_player_fired)
		_player.shield_changed.connect(_on_player_shield_changed)
	if _hud != null and _player != null:
		_hud.bind_player(_player)
		_hud.bind_score(_game_state)
	# L'écran de pause reprend l'interface entière (bloc d'identité en haut à gauche,
	# COMMS en bas à gauche, comme l'accueil) : ces places sont celles du HUD, et deux
	# blocs de texte superposés ne se lisent ni l'un ni l'autre. Le HUD s'efface donc
	# le temps de la pause. Il n'en sait rien — c'est le niveau qui les raccorde.
	var pause := get_node_or_null("PauseScreen") as PauseScreen
	if pause != null and _hud != null:
		pause.pause_toggled.connect(_on_pause_toggled)
	if _pickups != null:
		_pickups.picked_up.connect(_on_pickup)
	var args := OS.get_cmdline_user_args()
	# Perf bisection flags.
	if "--no-backdrop" in args:
		var bd := get_node_or_null("SpaceBackdrop") as Node3D
		if bd != null:
			bd.visible = false
	if "--no-flyby" in args:
		_flyby_disabled = true
	if "--no-surface-maps" in args:
		_surface_maps_disabled = true
	if "--no-glow" in args:
		var we := get_node_or_null("WorldEnvironment") as WorldEnvironment
		if we != null and we.environment != null:
			we.environment.glow_enabled = false
	if "--no-wave" in args:
		# Coupe les DEUX vagues : le champ d'astéroïdes enchaînerait sinon sur le boss
		# final au premier `begin()`, et la bissection perf mesurerait autre chose que
		# ce qu'elle croit.
		_waves_disabled = true
		if _wave_spawner != null:
			_wave_spawner.set_physics_process(false)
	# L'écran de victoire ne s'atteignait qu'en jouant l'arc entier — donc en pratique
	# il ne se REGARDAIT jamais, et il a vécu longtemps avec la police par défaut sans
	# que personne le voie (ADR-0006). Le score est semé pour que le rapport s'affiche
	# avec des chiffres plausibles plutôt qu'un 00000000 de rang C.
	if "--victory-demo" in args:
		_game_state.add_score(31500)
		_start_victory.call_deferred()
	# Même raison exactement que `--victory-demo` : un écran qu'on n'atteint qu'en
	# perdant trois vies ne se REGARDE jamais pendant le développement (ADR-0006), et
	# c'est ainsi qu'il a pu ne pas exister du tout pendant tout ce temps. Le drapeau
	# encaisse un coup mortel toutes les 3,5 s — l'espacement n'est pas décoratif :
	# mourir coûte 1,2 s de renaissance PUIS 2 s d'invulnérabilité, soit 3,2 s pendant
	# lesquelles un second coup ne porte pas. À 2,5 s, une fois sur deux le coup tombait
	# dans cette fenêtre et la défaite arrivait à un moment imprévisible.
	if "--defeat-demo" in args and _player != null:
		_game_state.add_score(9400)
		var killer := Timer.new()
		killer.wait_time = 3.5
		killer.autostart = true
		killer.timeout.connect(func() -> void: _player.take_contact_damage(9999.0))
		add_child(killer)
	if "--pickup-demo" in args and _pickups != null:
		_pickups.spawn(Pickup.Kind.POWER, Vector2(-3.0, 0.0))
		_pickups.spawn(Pickup.Kind.SHIELD, Vector2(0.0, 0.0))
		_pickups.spawn(Pickup.Kind.SCORE, Vector2(3.0, 0.0))
	# ⚠️ AVANT les sauts de phase : `--skip-to-field` entre dans le champ depuis ce même
	# bloc, et il lui faut son décor déjà monté.
	_build_moon_flyby()
	_build_transition()
	# Le gel d'impact. Monté en code : il n'a ni transform ni enfant, et l'ajouter aux
	# trois scènes qui portent un CameraDirector n'apporterait rien de plus.
	_hit_stop = HitStop.new()
	_hit_stop.name = "HitStop"
	add_child(_hit_stop)
	# ⚠️ SONDE DE PLONGÉE (`--dive-probe`). Elle existe parce qu'une simulation headless a
	# affirmé que le convoyeur de la chambre avait disparu, pendant que l'opérateur le vivait
	# encore : « toujours le même syndrome, j'ai comme un mur qui me pousse ». Quand le banc
	# et le jeu se contredisent, c'est le JEU qui a raison — et il faut l'instrumenter, pas
	# raffiner le banc. Elle imprime, quatre fois par seconde et seulement pendant la
	# plongée, ce que le chasseur subit VRAIMENT : sa position, son contact, ce qui est versé.
	_dive_probe = "--dive-probe" in args
	# ⚠️ L'ENREGISTREMENT DE PARTIE (`--dive-trace`), demandé par l'opérateur après trois
	# diagnostics qui se contredisaient : « enregistre le déplacement du vaisseau en même
	# temps que la position des murs ». C'est la seule preuve qui ne dépende d'aucune
	# hypothèse — ni la mienne, ni celle d'un banc. On écrit la COMMANDE en plus de la
	# position : sans elle, une trace ne distingue pas « il va à droite » de « il est poussé
	# à droite », et c'est exactement la question posée.
	_dive_trace = "--dive-trace" in args
	ReactorRings.disabled = "--no-rings" in args
	# ⚠️ LA REPRÉSENTATION PHYSIQUE, VISIBLE (`--show-solids`). Demandée par l'opérateur après
	# quatre correctifs à l'aveugle : « faire apparaître la représentation dans l'espace des
	# points de collision, pour qu'on voie visuellement la différence ». Quand l'image et la
	# collision sont deux objets, la superposition est la seule preuve qui ne discute pas.
	# ⚠️ ACTIF PAR DÉFAUT EN BUILD DE DÉVELOPPEMENT, coupé en release. « Dès qu'on est en
	# développement, on doit toujours les afficher » (opérateur, 2026-08-28) — c'est cet
	# outil, et lui seul, qui a montré que le décor et la collision tournaient en sens
	# inverse, après quatre correctifs a l'aveugle. `--hide-solids` pour une capture propre.
	if "--show-solids" in args \
			or (OS.is_debug_build() and not "--hide-solids" in args):
		_solids_overlay = SolidsOverlay.new()
		_solids_overlay.name = "SolidsOverlay"
		add_child(_solids_overlay)
	if ReactorRings.disabled:
		print("[Level] ISOLATION : aucun mur dans la chambre (--no-rings)")
	if "--density-probe" in args and _bullets != null:
		add_child(DensityProbe.make(_bullets, phase_label))
	# Aucun de ces sauts n'éteint le semeur lui-même : `_set_phase()` le fait pour tout le
	# monde, dès qu'on quitte `FIGHTER_WAVES`.
	if "--skip-to-boss" in args:
		_start_mini_boss()
	elif "--skip-to-field" in args:
		_start_asteroid_field()
	elif "--skip-to-final" in args:
		_start_final_boss()
	elif "--skip-to-dock" in args:
		_start_docking()
	elif "--skip-to-victory" in args:
		_game_state.add_score(28450)
		_start_victory()
	# Start the score. Runs after the --skip-to-* flags, so a skipped run opens on the
	# state it actually jumped to instead of fading out of Launch.
	_update_music()
	print("[Level] ready — phase FIGHTER_WAVES")

# --- Adaptive music (spec §18.2) ---------------------------------------------
# The level is the only thing that knows how the fight is going; MusicDirector turns
# that into a state and AudioManager plays it. Nothing here picks a track by name.

## ⚠️ ET IL ARRÊTE LE SEMEUR DE VAGUES, PARCE QUE C'EST LE SEUL POINT PAR LEQUEL TOUTES LES
## PHASES PASSENT. L'extinction était répétée dans chaque branche de `--skip-to-*` — et
## `--skip-to-boss`, la seule qui l'avait oubliée, faisait jouer le mini-boss AVEC la vague
## d'éclaireurs par-dessus (playtest du 2026-08-27 : « avec le raccourci direct sur le mini
## boss, il y avait les vagues d'ennemis »). Une règle recopiée cinq fois finit toujours par
## manquer à la sixième ; posée ici, elle est vraie par construction : quitter
## `FIGHTER_WAVES` ARRÊTE de semer, quel que soit le chemin — vague nettoyée, drapeau de
## debug, ou tout ce qu'on ajoutera ensuite.
##
## Le champ d'astéroïdes a son PROPRE semeur (`_field_spawner`), que ceci ne touche pas.
func _set_phase(phase: int) -> void:
	_phase = phase
	if phase != Phase.FIGHTER_WAVES and _wave_spawner != null:
		_wave_spawner.set_physics_process(false)
	# ⚠️ MÊME RAISON QUE LE SEMEUR, ET MÊME ENDROIT. La chambre du réacteur élargit le plan
	# de vol le temps d'une plongée ; le boss peut tomber pendant celle-ci, et l'arc enchaîne
	# alors sur l'appontage. Rendre les bornes ici couvre ce chemin comme tous les autres —
	# une phase qui n'est pas le boss final se joue TOUJOURS sur le plan ordinaire.
	if phase != Phase.FINAL_BOSS:
		GameplayPlane.reset_bounds()
	_music.level_phase = phase
	_update_music()

func _on_wave_progress(ratio: float) -> void:
	_music.wave_progress = ratio
	_update_music()

func _update_music() -> void:
	if _audio != null:
		_audio.set_music_state(MusicDirector.resolve(_music))

## La caméra prend le recul qu'exige la chambre.
##
## ⚠️ ELLE REVENAIT AU CADRAGE ORDINAIRE, ET C'ÉTAIT JUSTE TANT QUE L'ARÈNE FAISAIT LA MÊME
## TAILLE QUE LE PLAN DE VOL. La chambre est désormais plus grande (23,8 contre 16) : au
## cadrage d'origine, le blindage déborderait de l'écran et le joueur piloterait vers des
## murs qu'il ne voit pas. Le facteur se DÉDUIT des deux terrains — changer l'un déplace la
## caméra avec lui, sans qu'aucun chiffre ne soit à reprendre ici.
##
## Coupe franche (durée nulle) : on arrive du zoom d'entrée, qui vient de remplir l'écran.
## Un glissement, lui, se verrait — c'est la même raison qui fait entrer sec dans le lieu.
func _frame_chamber() -> void:
	var director := get_node_or_null("CameraDirector") as CameraDirector
	if director == null:
		return
	var chamber := GameplayPlane.CHAMBER_BOUNDS
	director.frame_scaled(chamber.size.y / GameplayPlane.BOUNDS.size.y,
		GameplayPlane.to_world(chamber.get_center()), 0.0)

## Le HUD s'efface pendant la pause et revient à la reprise. Coupure franche
## assumée : elle se produit sous un voile qui monte en 0.16 s, donc invisible.
func _on_pause_toggled(is_paused: bool) -> void:
	if _hud != null:
		_hud.visible = not is_paused

# --- Fighter waves -----------------------------------------------------------

func _on_wave_cleared() -> void:
	if _phase != Phase.FIGHTER_WAVES:
		return
	print("[Level] waves cleared — mini-boss incoming")
	_start_mini_boss()

func _on_enemy_destroyed(enemy: EnemyController) -> void:
	_game_state.add_score(enemy.data.score_value)
	_boom(enemy.global_position, VfxExplosion.Category.MEDIUM, 0.35)
	_sfx(&"medium_explosion")
	if _pickups != null:
		_pickups.roll_drop(enemy.global_position)

## One cue per kind: a bonus has to be identifiable without looking straight at it
## (docs/forge/CHARTE_CREATIVE.md — never colour alone).
func _on_pickup(kind: int, _world_position: Vector3) -> void:
	if _hud != null:
		_hud.pulse_pickup(kind)
	match kind:
		Pickup.Kind.POWER:
			_sfx(&"pickup_power")
		Pickup.Kind.SHIELD:
			_sfx(&"pickup_shield")
		Pickup.Kind.SCORE:
			_sfx(&"pickup_score")

# --- Combat chatter (rate-limited by the cue bank) ---------------------------

func _on_player_fired() -> void:
	_sfx(&"player_pulse")

func _on_enemy_fired() -> void:
	_sfx(&"enemy_pulse")

func _on_enemy_hit() -> void:
	_sfx(&"hull_impact")

## Every connecting bullet, from either side. Coloured by who was hit, so a glance
## tells you whether you landed a shot or took one: cold white on an enemy hull,
## shield cyan on ours (docs/forge/output/graybox_palette.md).
func _on_bullet_hit(plane_position: Vector2, victim_team: int) -> void:
	if _vfx == null:
		return
	var tint := _SHIELD_IMPACT_TINT if victim_team == BulletManager.Team.PLAYER \
		else _HULL_IMPACT_TINT
	_vfx.spawn_explosion(GameplayPlane.to_world(plane_position),
		VfxExplosion.Category.IMPACT, tint)

## Audible warning when the shield drops under 25% (spec §8.3).
func _on_player_shield_changed(ratio: float, _current: float, _maximum: float) -> void:
	if _alarm_armed and ratio <= _ALARM_TRIGGER_RATIO:
		_alarm_armed = false
		_sfx(&"danger_alarm")
	elif not _alarm_armed and ratio >= _ALARM_REARM_RATIO:
		_alarm_armed = true

# --- Mini-boss ---------------------------------------------------------------

func _start_mini_boss() -> void:
	_set_phase(Phase.MINI_BOSS)
	_boss = MiniBossScene.instantiate() as BossController
	add_child(_boss)
	_boss.health_changed.connect(_on_boss_health)
	_boss.defeated.connect(_on_mini_boss_defeated)
	# Le corps du Harvester est blindé tant que son iris est fermé : sans ce retour,
	# tirer dessus ne produit RIEN à l'écran et se lit comme un défaut, pas comme une
	# armure. Le signal existe sur tout boss ; seul le Harvester le déclenche.
	_boss.deflected.connect(_on_boss_deflected)
	_bind_harvester(_boss)
	_boss.begin(_bullet_manager, _player)
	_sfx(&"danger_alarm")
	if _hud != null:
		_hud.show_boss(_boss.display_name)
		# APRÈS `begin()` : c'est lui qui monte le module, donc qui crée les appendices.
		# Interroger avant rendrait zéro et afficherait trois pastilles éteintes sur un
		# boss intact.
		var combat := _boss.get_node_or_null("Combat") as HarvesterCombat
		if combat != null:
			combat.publish_gauges()

## Raccorde le retour propre au Harvester, s'il porte son module de combat. Câblé
## AVANT `begin()` : c'est lui qui déclenche le montage du module.
func _bind_harvester(boss: BossController) -> void:
	var combat := boss.get_node_or_null("Combat") as HarvesterCombat
	_harvester = combat
	if combat == null:
		return
	combat.limb_destroyed.connect(_on_harvester_limb_destroyed.bind(boss))
	combat.limb_gauge_changed.connect(_on_harvester_limb_gauge)
	combat.limb_rebuild_changed.connect(_on_harvester_limb_rebuild)
	combat.iris_opened.connect(_on_harvester_iris_opened.bind(boss))
	combat.iris_closed.connect(_on_harvester_iris_closed)

func _on_boss_deflected(world_position: Vector3) -> void:
	# Étincelle blanche et son de bouclier : la carapace RENVOIE le tir.
	_boom(world_position, VfxExplosion.Category.IMPACT, 0.0)
	_sfx(&"shield_impact")

func _on_harvester_limb_destroyed(_kind: StringName, boss: BossController) -> void:
	# `_boom` porte déjà la secousse : la redemander ici la doublerait.
	_boom(boss.global_position, VfxExplosion.Category.MEDIUM, 0.5)
	_sfx(&"medium_explosion")

## Une jauge d'appendice a bougé. Le niveau ne fait que relayer : le HUD ne connaît pas
## le Harvester, le module ne connaît pas le HUD.
## Un appendice REPOUSSE : le HUD le montre, au lieu d'une barre immobile pendant les
## quatorze secondes de `limb_rebuild_time`.
func _on_harvester_limb_rebuild(index: int, ratio: float) -> void:
	if _hud != null:
		_hud.set_boss_limb_regen(index, ratio)

func _on_harvester_limb_gauge(index: int, ratio: float, alive: bool) -> void:
	if _hud != null:
		_hud.set_boss_limb(index, ratio, alive)

## Le moment du combat : la carapace s'ouvre. Il doit s'entendre, se sentir et se
## lire — c'est la seule fenêtre où le joueur peut faire des dégâts.
func _on_harvester_iris_opened(boss: BossController) -> void:
	_boom(boss.global_position, VfxExplosion.Category.MEDIUM, 0.9)
	_sfx(&"boss_phase_shift")
	if _hud != null:
		_hud.show_banner("NOYAU EXPOSE", Color("d93d9c"), 1.4)

func _on_harvester_iris_closed() -> void:
	_sfx(&"docking_lock")
	if _hud != null:
		_hud.show_banner("CARAPACE REFERMEE", Color("e4b54a"), 1.0)

func _on_boss_health(ratio: float) -> void:
	if _hud != null:
		_hud.set_boss_health(ratio)
	# Only the final boss drives the boss music: the mini-boss shares Fleet Battle.
	if _phase == Phase.FINAL_BOSS:
		_music.boss_health_ratio = ratio
		_update_music()

func _on_mini_boss_defeated(world_position: Vector3) -> void:
	_game_state.add_score(5000)
	_boom(world_position, VfxExplosion.Category.HEAVY, 1.0)
	_sfx(&"heavy_explosion")
	if _hit_stop != null:
		_hit_stop.freeze(HitStop.BOSS)
	if _hud != null:
		_hud.hide_boss()
	if _boss != null:
		_boss.queue_free()
		_boss = null
	print("[Level] mini-boss defeated — score %d" % _game_state.score)
	_start_asteroid_field()

# --- Champ d'astéroïdes (ADR-0027) -------------------------------------------
#
# La traversée qui sépare les deux boss. Aucun boss, aucun décor dédié à ce stade :
# une seconde vague, jouée avec les trois unités que le bestiaire avait livrées sans
# qu'aucune rencontre ne les emploie. Le décor viendra par-dessus (lot 2 du plan),
# sans rien changer à cet enchaînement.

func _start_asteroid_field() -> void:
	# AVANT `_set_phase` : celui-ci résout déjà la musique, et il la résoudrait sur la
	# progression de la vague PRÉCÉDENTE — donc sur Fleet Battle, à 1,0, alors que la
	# traversée est censée s'ouvrir sur son propre lit.
	_music.wave_progress = 0.0
	_set_phase(Phase.ASTEROID_FIELD)
	print("[Level] ASTEROID FIELD")
	if _field_spawner == null or _waves_disabled:
		# Rien à traverser. On le DIT et on enchaîne : un arc qui s'arrête sur un nœud
		# absent se lit comme un boss qui ne vient pas, et se cherche au mauvais endroit.
		if _field_spawner == null:
			push_error("[Level] AsteroidFieldSpawner missing — straight to the final boss")
		_show_moon_flyby(true)
		_start_final_boss()
		return
	# Le décor ne commute plus : il change SOUS un voile fermé (lot 5). La bannière est
	# posée au même instant — elle vit sur le HUD, au-dessus du voile, et s'inscrit donc
	# sur l'écran éteint avant que le survol n'apparaisse dessous.
	_veil(_reveal_asteroid_field, _begin_asteroid_field)

## Le décor bascule ici, et nulle part ailleurs : appelé quand le voile est plein.
func _reveal_asteroid_field() -> void:
	_show_moon_flyby(true)
	_banner("CHAMP D'ASTEROIDES", _COLOR_GOLD, 1.6)

## La vague ne part qu'une fois le voile rouvert. Peupler l'écran derrière un voile
## fermé offrirait au joueur des mines déjà à mi-course quand il retrouve la vue.
func _begin_asteroid_field() -> void:
	if _field_spawner != null:
		_field_spawner.begin()

## Monte le survol, caché. ⚠️ La doublure procédurale s'annonce dans le journal : un décor
## en doublure ne doit jamais passer pour l'asset final (ADR-0006, et la leçon d'`ADR-0025`
## où un contrat de noms respecté cachait des anneaux de 30 cm).
func _build_moon_flyby() -> void:
	if _flyby_disabled:
		return
	_moon_flyby = MoonFlyby.new()
	_moon_flyby.name = "MoonFlyby"
	# ⚠️ AVANT `add_child` : c'est `_ready()` qui bâtit le décor et pose la matière.
	_moon_flyby.maps_enabled = not _surface_maps_disabled
	add_child(_moon_flyby)
	if _moon_flyby.is_stand_in():
		print("[Level] moon flyby: DOUBLURE procedurale (decor de survol non livre)")
	# ⚠️ La géométrie et la MATIÈRE sont deux livraisons distinctes (`ADR-0028`) : la forge
	# livre l'une, l'opérateur l'autre. Une doublure texturée n'est plus tout à fait une
	# doublure, et un journal qui ne le dirait pas laisserait croire à l'une ou à l'autre.
	print("[Level] moon flyby: surface %s, impacts %s"
		% ["texturee (TEX-0001/0002)" if _moon_flyby.has_surface_maps() else "en aplat",
		   "peints (TEX-0005/0006)" if _moon_flyby.has_painted_impacts() else "en repli geometrique"])

## Monte le voile de raccord, caché. Bâti par code et non posé dans `graybox.tscn` : la
## scène est éditée par une autre session, et un `.tscn` se fusionne très mal à deux —
## même raison que pour `CoreInterior`.
func _build_transition() -> void:
	_transition = PhaseTransition.new()
	_transition.name = "PhaseTransition"
	add_child(_transition)

## Joue un raccord : `on_midpoint` est appelé voile fermé (c'est là qu'on change le
## décor), `on_finished` voile rouvert (c'est là qu'on rend la main à l'arc).
##
## ⚠️ SANS VOILE, LES DEUX APPELS PARTENT QUAND MÊME, dans l'ordre. Une mise en scène doit
## tolérer d'être absente : `--skip-to-*` et les tests montent le niveau sans passer par
## les chemins qui la construisent, et un arc qui s'arrêterait là se lirait comme un boss
## qui ne vient pas — exactement le défaut que `_start_asteroid_field()` évite déjà.
func _veil(on_midpoint: Callable, on_finished: Callable) -> void:
	if _transition == null:
		on_midpoint.call()
		on_finished.call()
		return
	_transition.midpoint.connect(on_midpoint, CONNECT_ONE_SHOT)
	_transition.finished.connect(on_finished, CONNECT_ONE_SHOT)
	_transition.play()

## Bascule le décor de la phase. Le fond spatial CÈDE LA PLACE au lieu de s'y ajouter :
## c'est la décision d'`ADR-0027`, et elle vient autant du budget GPU que de la demande
## (« qu'on n'ait pas le même décor qu'avant le premier boss »).
func _show_moon_flyby(on: bool) -> void:
	if _moon_flyby == null:
		return
	_moon_flyby.reveal(on)
	_set_backdrop_hidden(on)

func _on_asteroid_field_cleared() -> void:
	if _phase != Phase.ASTEROID_FIELD:
		return
	print("[Level] asteroid field cleared — final boss incoming")
	_start_boss_approach()

# --- L'approche du Leviathan : le dernier puits monte (lot 5, option D) -------
#
# Le champ nettoyé, l'arc NE RELANCE PAS immédiatement. Un dernier puits gravitique reste,
# grossit et dérive vers le haut du cadre — là d'où le boss descendra. C'est la
# respiration que la bible réclame (« ralentir avant la fin », ❌ non tenu au 2026-08-25)
# et, du même geste, la seule mécanique du Leviathan que la phase 2 enseignait déjà sans
# que rien ne le dise : `GravityWell.pull_at()` est appelée par le Null Maw ET par le boss.

func _start_boss_approach() -> void:
	# Sans joueur à aspirer, l'approche n'a aucun sujet : elle serait trois secondes
	# d'écran vide. `--no-wave` saute aussi, pour la même raison qu'il saute la vague.
	if _player == null or _waves_disabled:
		_veil(_leave_asteroid_field, _start_final_boss)
		return
	_approach_active = true
	_approach_time = 0.0
	print("[Level] BOSS APPROACH — le dernier puits monte")

## Fait monter le puits, image par image, et rend la main au voile quand il a fini.
##
## ⚠️ Aucune allocation ici : `BossApproach` et `GravityWell` sont des bibliothèques de
## fonctions pures, et `add_pull` s'ajoute à ce que les autres puits ont déjà posé cette
## image — une affectation les effacerait en silence.
func _advance_boss_approach(delta: float) -> void:
	_approach_time += delta
	if _player != null:
		_player.add_pull(GravityWell.pull_at(
			_player.plane_position,
			BossApproach.centre_at(_approach_time, BossApproach.DURATION),
			BossApproach.radius_at(_approach_time, BossApproach.DURATION),
			BossApproach.speed_at(_approach_time, BossApproach.DURATION)))
	if not BossApproach.is_over(_approach_time, BossApproach.DURATION):
		return
	_approach_active = false
	_veil(_leave_asteroid_field, _start_final_boss)

## Le survol s'éteint sous le voile fermé. ⚠️ `_start_final_boss()` garde SA propre
## extinction : c'est le seul point par lequel tous les chemins passent, `--skip-to-final`
## compris, et un décor qui survivrait à sa phase se retrouverait sous le boss.
func _leave_asteroid_field() -> void:
	_show_moon_flyby(false)

# --- Final boss + docking close (ADR-0010; docking was the mid-level §6.5) ----

func _start_docking() -> void:
	_set_phase(Phase.DOCKING)
	print("[Level] DOCKING")
	_citadel = CitadelScene.instantiate() as AegisCitadel
	_citadel.plane_position = Vector2(0.0, 22.0) # off-screen above
	add_child(_citadel)
	_citadel.arrived.connect(_on_citadel_arrived, CONNECT_ONE_SHOT)
	_citadel.slide_to(Vector2(0.0, 11.0), 9.0)

func _on_citadel_arrived() -> void:
	if _player != null:
		_player.autopilot_reached.connect(_on_player_docked, CONNECT_ONE_SHOT)
		_player.begin_autopilot(Vector2(0.0, 6.3))

func _on_player_docked() -> void:
	_boom(GameplayPlane.to_world(Vector2(0.0, 6.6)), VfxExplosion.Category.MEDIUM, 0.5)
	_sfx(&"docking_lock")
	if _player != null:
		_player.stow()
	_start_victory()

func _start_final_boss() -> void:
	# Le survol s'éteint ici et pas dans `_on_asteroid_field_cleared` : c'est le SEUL
	# point par lequel tous les chemins passent — la vague nettoyée, mais aussi
	# `--skip-to-final` et l'échappement de `--no-wave`. Un décor qui survivrait à sa
	# phase se retrouverait sous le boss final.
	_show_moon_flyby(false)
	_set_phase(Phase.FINAL_BOSS)
	print("[Level] FINAL BOSS")
	_final_boss = FinalBossScene.instantiate() as BossController
	_final_boss.plane_position = Vector2(0.0, 12.0)
	_final_boss.scale = Vector3.ONE * _FINAL_BOSS_SCALE
	add_child(_final_boss)
	# Le Pale Leviathan pilote TOUT par son module composé : phases matérielles, jauge de
	# structure, aspiration, sous-cibles, et sa propre mort quand le cœur tombe. Le corps
	# générique reste clos (aucune phase par seuil de PV) — on ne branche donc ni
	# `phase_changed` ni `health_changed`, seulement la défaite, que le module déclenche.
	_final_boss.defeated.connect(_on_final_boss_defeated)
	if _hud != null:
		_hud.show_boss(_final_boss.display_name)
	_bind_leviathan(_final_boss)
	# APRÈS `show_boss` (qui éteint les pastilles) et AVEC le module déjà branché : `begin`
	# monte le module, qui émet `phase_entered(ARMOR_CHOIR)` — c'est lui qui rallume et
	# nomme les quatre pastilles de plaques.
	_final_boss.begin(_bullet_manager, _player)
	_sfx(&"danger_alarm")
	# APRÈS `begin()` : le module a créé les sous-cibles, publier avant afficherait des
	# pastilles éteintes sur un boss intact.
	var combat := _final_boss.get_node_or_null("Combat") as LeviathanCombat
	if combat != null:
		combat.publish_gauges()
	_banner(_final_boss.display_name, _COLOR_GOLD, 1.6)

## Raccorde le module du Pale Leviathan au reste du niveau. Câblé AVANT `begin()` : c'est
## `begin` qui déclenche le montage du module et la première émission de phase.
func _bind_leviathan(boss: BossController) -> void:
	var combat := boss.get_node_or_null("Combat") as LeviathanCombat
	if combat == null:
		return
	_leviathan = combat
	combat.phase_entered.connect(_on_leviathan_phase)
	combat.structure_changed.connect(_on_leviathan_structure)
	combat.piece_gauge_changed.connect(_on_leviathan_piece_gauge)
	combat.piece_active_changed.connect(_on_leviathan_piece_active)
	combat.piece_destroyed.connect(_on_leviathan_piece_destroyed)
	combat.pull_changed.connect(_on_leviathan_pull)
	combat.dive_started.connect(_on_leviathan_dive_started)
	combat.dive_entered.connect(_on_leviathan_dive_entered)
	combat.dive_ended.connect(_on_leviathan_dive_ended)
	combat.armour_reformed.connect(_on_leviathan_armour_reformed)
	combat.armour_regen.connect(_on_leviathan_armour_regen)
	combat.dive_time_left.connect(_on_leviathan_dive_time_left)
	combat.shield_deflected.connect(_on_boss_deflected)
	combat.node_gauge_changed.connect(_on_leviathan_node_gauge)
	combat.node_destroyed.connect(_on_leviathan_node_destroyed)

## La jauge du boss montre la PROGRESSION DU COMBAT — `fight_ratio()`, qui ne remonte
## jamais — et non la santé de la cible courante.
##
## ⚠️ ELLE A MONTRÉ `structure_ratio()`, et c'était le défaut le plus coûteux du combat.
## Cette mesure vaut « ce qu'on peut casser MAINTENANT » : elle se remplit à nouveau à
## chaque bascule. Le joueur voyait donc armure 100→0, noyau 100→0, armure 100→0, noyau
## 100→0… Playtest du 2026-08-25, sur un combat pourtant jugé mieux équilibré : « phase 1
## phase 2 phase 1 phase 2, j'ai l'impression que c'était en boucle ». Il ne se trompait
## pas — il décrivait exactement ce que le HUD lui affichait.
## La mesure qui prouvait l'avancement existait déjà, juste et testée ; son UNIQUE
## consommateur était la musique. L'oreille savait que le combat montait, l'œil n'avait
## rien. L'état de la cible courante n'est pas perdu pour autant : il vit sur la rangée de
## pastilles, qui suit les plaques du cycle.
func _on_leviathan_structure(ratio: float) -> void:
	var progress := _leviathan.fight_ratio() if _leviathan != null else ratio
	if _hud != null:
		_hud.set_boss_health(progress)
	_music.boss_health_ratio = progress
	_update_music()

## Une sous-cible a bougé. Le niveau relaie : le HUD ne connaît pas le Leviathan, le
## module ne connaît pas le HUD.
func _on_leviathan_piece_gauge(index: int, ratio: float, alive: bool) -> void:
	if _hud != null:
		_hud.set_boss_limb(index, ratio, alive)

## La plaque à viser a changé (phase 1) ou s'est éteinte (`-1`, autres phases). Le niveau
## relaie au HUD, qui surligne la pastille active — le joueur voit enfin laquelle traiter.
func _on_leviathan_piece_active(index: int) -> void:
	if _hud != null:
		_hud.set_boss_limb_active(index)

## L'armure se reconstruit : la RANGÉE DE PLAQUES le montre, cuve par cuve, au lieu de
## laisser une seconde de vide.
##
## ⚠️ La rangée est éteinte pendant la plongée (« plus de plaques »). On la redresse ici,
## pour le cycle QUI VIENT — c'est ce qui permet de voir arriver l'armure, et combien il en
## reste. Même vocabulaire que la repousse des appendices du mini-boss : une barre qui se
## Le sablier de la plongée. Le niveau relaie : le module ne connaît pas le HUD, le HUD ne
## connaît pas le Leviathan.
func _on_leviathan_dive_time_left(ratio: float) -> void:
	if _hud != null:
		_hud.set_dive_time_left(ratio)

## remplit en vert.
func _on_leviathan_armour_regen(ratio: float, plates: int) -> void:
	if _hud == null:
		return
	if ratio <= 0.0:
		_regen_plates = 0
		return
	if _regen_plates != plates:
		_regen_plates = plates
		_hud.set_boss_limbs(_LEVIATHAN_PLATE_LABELS.slice(0, plates))
		for i in plates:
			_hud.set_boss_limb(i, 0.0, false)   # à terre : la barre sombre dit « pas encore »
	for i in plates:
		_hud.set_boss_limb_regen(i, ratio)

## L'état d'un verrou : la rangée de pastilles le porte, comme elle porte les plaques
## pendant l'armure. ⚠️ La rangée est ÉTEINTE pendant la plongée depuis `ADR-0025` (« plus de
## plaques ») : c'est le premier verrou annoncé qui la redresse.
func _on_leviathan_node_gauge(index: int, ratio: float, alive: bool) -> void:
	if _hud == null or _leviathan == null:
		return
	if _regen_plates != -1:
		_regen_plates = -1
		_hud.set_boss_limbs(_LEVIATHAN_LOCK_LABELS.slice(0, _leviathan.tuning.node_count))
	_hud.set_boss_limb(index, ratio, alive)

func _on_leviathan_node_destroyed(_index: int, world_position: Vector3) -> void:
	_boom(world_position, VfxExplosion.Category.MEDIUM, 0.35)
	_sfx(&"medium_explosion")

func _on_leviathan_piece_destroyed(_phase: int, _index: int, world_position: Vector3) -> void:
	_boom(world_position, VfxExplosion.Category.MEDIUM, 0.4)
	_sfx(&"medium_explosion")
	# Une plaque qui cède est le seul retour que le joueur ait sur sa progression dans
	# l'armure : elle mérite qu'on tienne l'image (LOI-EXP-03).
	if _hit_stop != null:
		_hit_stop.freeze(HitStop.PLATE)

## Le champ gravitique (vagues d'aspiration de la phase 2) s'ajoute à la vitesse du joueur. Le module publie
## à chaque image tant que la phase l'exige ; on la recalcule ici depuis la position
## COURANTE du joueur (il bouge) et on la lui impose — il la consomme et la remet à zéro,
## si bien qu'une phase sans champ ne traîne aucune aspiration résiduelle.
func _on_leviathan_pull(speed_max: float, radius: float, centre: Vector2) -> void:
	if _player == null:
		return
	# `add_pull` et non `apply_pull` : l'aspiration s'AJOUTE à celles déjà posées cette
	# image. Le boss est seul aujourd'hui, mais un champ de mines et lui peuvent se
	# retrouver dans la même rencontre — et une affectation effacerait silencieusement les
	# puits des autres, sans erreur ni test rouge.
	_player.add_pull(GravityWell.pull_at(_player.plane_position, centre, radius, speed_max))

# --- La plongée dans le noyau (ADR-0021) --------------------------------------
## Le playtest disait : « on ne voit pas, on ne comprend pas qu'il faut aller dans le
## noyau pour tirer ». La cible ne se DÉSIGNE donc plus, elle se REMPLIT l'écran : le
## corps s'ouvre, le chasseur y est tiré, la caméra plonge derrière lui. C'est la même
## grammaire que l'appontage — un autopilote et un cadrage — parce que le joueur l'a
## déjà apprise à la fin du niveau.

## Distance de la caméra à la gueule au bout du zoom, en mètres. Déduite du champ de
## vision (62° verticaux) et du passage libre mesuré de l'iris (4,378 m) : 3,64 m serait le
## minimum pour qu'il remplisse l'écran, 4,5 lui en laisse 81 % et garde la lèvre visible.
const DIVE_FRAME_DISTANCE := 4.5
## Hauteur de la gueule au-dessus du plan, dans la coque du boss.
const DIVE_MAW_HEIGHT := 1.5

## L'intérieur du noyau : une **zone dédiée**, montée à l'origine du monde et à l'échelle
## du plan de jeu. Bâtie par code et non posée dans `graybox.tscn` — la scène est éditée
## par une autre session, et un `.tscn` se fusionne très mal à deux.
var _core_interior: CoreInterior
## Où était le chasseur juste avant d'entrer : on l'y repose en ressortant, sans quoi il
## réapparaît dehors à la place qu'il occupait DANS l'arène intérieure — deux repères qui
## n'ont rien à voir.
var _outside_plane: Vector2 = Vector2.ZERO
## Etat du fond spatial avant qu'on le masque, pour le rendre tel quel et non « allume ».
var _backdrop_was_visible: bool = true
## Le fond est-il masqué en ce moment ? Sans ce drapeau, un second masquage relèverait
## `false` comme « état d'avant » et le fond ne reviendrait jamais.
var _backdrop_hidden: bool = false

## Masque le fond spatial, ou le RESTAURE tel qu'il était.
##
## ⚠️ ON RESTAURE CE QU'IL Y AVAIT, pas « visible ». `--no-backdrop` éteint le fond pour
## juger une silhouette ; un `visible = true` au sortir rallumerait le fond au milieu d'une
## mesure, et l'on conclurait sur deux images qui ne se comparent pas.
##
## Deux décors s'en servent désormais — l'arène du noyau (`ADR-0025`) et le survol de lune
## (`ADR-0027`) : la précaution vit ici, en un seul endroit, plutôt qu'en deux copies.
func _set_backdrop_hidden(hidden: bool) -> void:
	var backdrop := get_node_or_null("SpaceBackdrop") as Node3D
	if backdrop == null:
		return
	if hidden:
		if not _backdrop_hidden:
			_backdrop_was_visible = backdrop.visible
			_backdrop_hidden = true
		backdrop.visible = false
		return
	backdrop.visible = _backdrop_was_visible
	_backdrop_hidden = false

func _on_leviathan_dive_started(cycle: int, centre: Vector2) -> void:
	_sfx(&"boss_phase_shift")
	# ⚠️ CETTE BANNIÈRE A DIT « ENCORE » à chaque plongée sauf la première — le mot nomme
	# la répétition, dans le seul moment du combat qui pouvait nommer l'avancement. Elle
	# compte désormais les passages : deux, trois, quatre. Un nombre qui monte se lit comme
	# du terrain gagné ; « encore » se lit comme du surplace.
	_banner("DANS LE NOYAU" if cycle == 0 else "NOYAU — PASSAGE %d" % (cycle + 1),
		_BANNER_MAGENTA, 1.2)
	if _hud != null:
		_hud.set_boss_limbs(PackedStringArray())   # plus de plaques : la rangée s'éteint
	_build_core_interior()
	if _player != null:
		# ⚠️ AVANT `begin_autopilot`, pas apres. L'autopilote emmene le chasseur a la gueule :
		# relever sa position une fois dedans memoriserait le point d'aspiration, pas
		# l'endroit d'ou le joueur est parti — et il ressortirait ailleurs qu'il n'est entre.
		_outside_plane = _player.plane_position
		# ⚠️ Pendant l'autopilote le chasseur est GUIDÉ, invulnérable et il ne tire pas
		# (`player_fighter_controller.gd:133`). C'est acceptable — et voulu — pour les
		# 1,4 s de l'entrée : le joueur regarde le corps s'ouvrir. Mais il faut lui rendre
		# la main à l'instant exact où le tir s'ouvre, d'où `end_autopilot()` juste après.
		# ⚠️ PAS AU CENTRE EXACT : le flux y est, et le chasseur disparaissait DERRIÈRE lui —
		# vu en capture, un noyau splendide et pas un vaisseau à l'écran. On le pose en
		# dessous, à portée de tir : c'est la position d'un shooter vertical, celle où le
		# joueur sait déjà ce qu'il a à faire.
		#
		# ⚠️ ET LA DISTANCE NE S'ÉCRIT PLUS ICI. Elle valait `-5.0`, une constante posée avant
		# que les murs n'existent — et qui tombait EN PLEIN DEDANS. Le chasseur naissait dans
		# le blindage, se faisait repousser vers l'intérieur et se retrouvait encagé : « je
		# fonce tout droit et mon vaisseau est bloqué, il avance pas ». `dive_entry_local()`
		# la déduit des anneaux livrés, et une garde refuse ce qui enfermerait.
		_player.begin_autopilot(centre + _leviathan.tuning.dive_entry_local())
		# Il vole DANS le noyau, au-dessus de son plancher : sans cette hauteur il passe
		# derrière la coque et on ne le voit plus.
		_player.plane_lift = CoreInterior.FLIGHT_LIFT
	_dive_camera(true)

## ⚠️ C'EST ICI QUE L'ON CHANGE DE LIEU, et c'est tout l'objet de la refonte. Le zoom de
## `dive_started` a fini sa course : l'écran est rempli par l'ouverture, donc la bascule
## passe inaperçue. On masque l'extérieur, on montre l'arène, on y pose le chasseur — et
## **la caméra revient à son cadrage normal**, parce que l'arène est bâtie à l'échelle du
## plan de jeu. C'est ce dernier point qui règle « on perd de vue le vaisseau » : dans le
## noyau, le jeu se lit exactement comme partout ailleurs.
func _on_leviathan_dive_entered(_cycle: int) -> void:
	if _player != null:
		_player.end_autopilot()
	# ⚠️ LE LIEU PREND SES BORNES AVANT QU'ON Y POSE LE CHASSEUR. La chambre est plus grande
	# que l'arène ouverte (`GameplayPlane.CHAMBER_BOUNDS`) : le blindage y occupe 16,6 unités
	# de diamètre, et sous le plan de vol ordinaire le chasseur n'avait la place ni de tenir
	# entre les murs ni de se poster dessous — il était convoyé le long des arcs et éjecté.
	# L'ordre compte : poser sa position d'abord la ferait borner par l'ancien plan.
	GameplayPlane.use_bounds(GameplayPlane.CHAMBER_BOUNDS)
	_show_core_interior(true)
	if _player != null and _core_interior != null:
		# ⚠️ LE MÊME POINT QUE L'AUTOPILOTE, et il n'y en a plus qu'un. Ici on lisait
		# l'ancrage `Entry_Point` du décor — sculpté avant que les murs n'existent — pendant
		# que l'autopilote visait `dive_entry_local()`, déduit des anneaux. Deux points
		# d'entrée pour le même fait : le chasseur était posé à un endroit puis conduit à un
		# autre, et le premier a fini hors de l'aire de jeu sans que rien ne s'en aperçoive.
		_player.plane_position = _core_interior.reactor_plane_position() \
			+ _leviathan.tuning.dive_entry_local()
		# Dedans, le chasseur revole DANS le plan : plus besoin de le soulever pour qu'il
		# cesse de disparaître derrière la cible, il n'y a plus de sphère devant lui.
		_player.plane_lift = 0.0
	# La cible suit le lieu : le flux vit désormais sur le réacteur de l'arène et non au
	# centre du corps du boss, resté dehors.
	if _leviathan != null and _core_interior != null:
		_leviathan.dive_anchor = _core_interior.reactor_plane_position()
		# ⚠️ ET ON DIT OÙ ELLE EST. La cible dérive de plusieurs unités autour de l'ancre ;
		# sans repère, le joueur tire sur le réacteur du décor pendant qu'elle est ailleurs.
		_core_marker_age = 0.0
		_core_interior.set_target_marker(_leviathan.flux_plane_position(), true)
		# Le blindage se dresse avec l'arène : ses arcs se déduisent des MÊMES Resources
		# que la mécanique, jamais d'une copie.
		_core_interior.build_rings(_leviathan.tuning.reactor_rings)
		_core_interior.build_nodes(_leviathan.tuning.node_count)
		_regen_plates = 0   # la rangée se redressera au premier verrou annoncé
	_frame_chamber()

func _on_leviathan_dive_ended(_cycle: int, flux_down: bool) -> void:
	# On quitte le lieu : il rend le plan de vol. Voir `_leave_chamber()` pour les AUTRES
	# chemins de sortie — celui-ci n'est que le plus heureux.
	GameplayPlane.reset_bounds()
	# L'éjection est une secousse, pas un fondu : on est recraché.
	_boom(_final_boss.global_position if _final_boss != null else Vector3.ZERO,
		VfxExplosion.Category.HEAVY, 0.85)
	_sfx(&"boss_phase_shift")
	if _player != null:
		_player.end_autopilot()
		_player.plane_lift = 0.0   # on ressort, le chasseur redescend dans le plan
		_player.plane_position = _outside_plane
	if _leviathan != null:
		_leviathan.dive_anchor = Vector2.INF   # le flux redevient une affaire de boss
	if _core_interior != null:
		_core_interior.set_target_marker(Vector2.ZERO, false)
	_show_core_interior(false)
	_dive_camera(false)
	_clear_core_interior()
	if not flux_down:
		_banner("EJECTE", _BANNER_IVORY, 1.0)

## L'armure revient — avec une plaque de moins. ⚠️ À ANNONCER : une armure qui repousse
## sans un mot se lit comme un bug, pas comme une mécanique. Le compte dans la bannière
## dit que le boss se répare de plus en plus mal.
func _on_leviathan_armour_reformed(_cycle: int, plates: int) -> void:
	_sfx(&"danger_alarm")
	_banner("ARMURE REFORMEE — %d PLAQUES" % plates, _BANNER_IVORY, 1.4)
	if _hud != null:
		_hud.set_boss_limbs(_LEVIATHAN_PLATE_LABELS.slice(0, plates))

## Glisse la caméra vers le noyau, ou la ramène. ⚠️ Passe par la POSE DE REPOS du
## `CameraDirector` : écrire `Camera3D.transform` directement serait écrasé par le shake
## à l'image suivante.
## Le zoom d'entrée : on plonge dans l'ouverture jusqu'à ce qu'elle remplisse l'écran.
##
## ⚠️ IL NE CADRE PLUS LA PHASE, IL LA COUVRE. Il glissait à mi-chemin du boss et y restait
## pendant toute la plongée — d'où « on perd de vue le vaisseau qui est dans la sphère » :
## un cadrage bâtard, ni le plan de jeu ni un gros plan. Il sert maintenant de RIDEAU : il
## va jusqu'au bout, la bascule de lieu se fait derrière, et le cadrage normal reprend une
## fois dedans (`dive_entered` appelle `_dive_camera(false)`).
func _dive_camera(inside: bool, snap: bool = false) -> void:
	var director := get_node_or_null("CameraDirector") as CameraDirector
	if director == null:
		return
	if not inside:
		# ⚠️ COUPE FRANCHE A L'ENTREE, GLISSEMENT A LA SORTIE. En glissant à l'entrée, la
		# caméra revenait de la gueule — à une douzaine d'unités de là — vers l'origine où
		# l'arène est montée, pendant une demi-seconde. Or à cet instant le fond spatial et
		# le corps du boss sont déjà masqués : elle traversait donc un monde vide et la
		# capture ne montrait QUE le HUD sur du noir. La coupe est invisible parce que le
		# zoom vient de remplir l'écran ; le glissement, lui, ne l'était pas du tout.
		director.restore_rest(0.0 if snap else 0.5)
		return
	var home := director.home_transform()
	var focus := _final_boss.global_position if _final_boss != null else Vector3.ZERO
	# ⚠️ ON SE POSE A UNE DISTANCE CALCULEE, PAS A UNE FRACTION DE LA HAUTEUR D'ORIGINE.
	# Premier essai : `home.origin.y * 0.22`, soit Y = 3,08 pour une caméra d'origine à 14.
	# La coque du boss fait 3,162 m de haut : la caméra finissait DANS la coque, et la
	# capture ne montrait qu'un amas de plaques — ni gueule, ni ouverture, ni plongée.
	# Une fraction d'une hauteur ne dit rien de ce qu'on cadre.
	#
	# Le cadrage se déduit du champ de vision : à 62° verticaux, encadrer un puits de
	# 4,378 m demande 3,64 m au minimum. On se pose à `DIVE_FRAME_DISTANCE`, ce qui lui
	# laisse ~81 % de la hauteur d'écran — assez pour qu'il déborde presque, assez peu
	# pour qu'on voie encore la lèvre s'écarter autour.
	# On recule le long de l'axe ARRIERE de la caméra d'origine, donc l'orientation et la
	# lecture du plan de jeu sont conservées, et le cadrage suit si la caméra est retouchée.
	var backward := home.basis.z.normalized()
	var maw := focus + Vector3(0.0, DIVE_MAW_HEIGHT, 0.0)
	var enter := _leviathan.tuning.dive_enter_time if _leviathan != null and _leviathan.tuning != null else 1.4
	director.push_rest(Transform3D(home.basis, maw + backward * DIVE_FRAME_DISTANCE),
		maxf(enter - 0.15, 0.2))

func _build_core_interior() -> void:
	if _core_interior != null:
		return
	_core_interior = CoreInterior.new()
	_core_interior.name = "CoreInterior"
	add_child(_core_interior)
	if _core_interior.is_stand_in():
		# ⚠️ À DIRE, TOUJOURS. Une doublure procédurale qui passerait pour l'asset livré
		# ferait juger le décor de la forge sur autre chose que la forge.
		print("[Level] core interior: DOUBLURE procedurale (decor BRIEF-0082 absent)")

## Bascule extérieur / intérieur. Le fond spatial et le corps du boss disparaissent : on
## n'est plus dans l'espace, on est DANS quelque chose. C'est la moitié de la sensation.
func _show_core_interior(inside: bool) -> void:
	if _core_interior != null:
		_core_interior.visible = inside
	_set_backdrop_hidden(inside)
	if _final_boss != null:
		_final_boss.visible = not inside

## Démonte la chambre — et lui reprend ses bornes.
##
## ⚠️ LE FILET, ET IL EST NÉCESSAIRE. La sortie heureuse (`_on_leviathan_dive_ended`) rend
## déjà le plan de vol ; ce n'est pas le seul chemin qui quitte le lieu. Mourir dedans,
## abandonner la partie depuis la pause, ou voir le boss tomber pendant une plongée passent
## tous par ici. Une borne oubliée laisserait le joueur voler jusqu'à −10,7 dans la phase
## SUIVANTE, hors du cadre de la caméra — et rien ne le signalerait.
func _clear_core_interior() -> void:
	GameplayPlane.reset_bounds()
	if _core_interior == null:
		return
	_core_interior.queue_free()
	_core_interior = null

## ⚠️ ET LE FILET DU FILET : quitter la scène rend TOUJOURS le plan ordinaire. `bounds` est
## le seul état global du jeu ; il ne doit pas pouvoir survivre au niveau qui l'a changé —
## un retour au titre en pleine plongée, et l'écran-titre hériterait des bornes de la
## chambre.
func _exit_tree() -> void:
	_flush_dive_trace()
	GameplayPlane.reset_bounds()

## Chaque transition du Leviathan, donnée à voir : bannière (les mots exacts du design),
## secousse, bascule musicale, et la rangée de pastilles reconfigurée pour les sous-cibles
## de la phase qui s'ouvre. Les phases avancent sur une condition MATÉRIELLE — le module
## en est seul juge, le niveau ne fait que l'annoncer.
## Chaque bascule du Leviathan. ⚠️ Les phases avancent sur une condition MATÉRIELLE —
## l'armure du cycle à terre, ou le compte à rebours du noyau épuisé. Le module en est
## seul juge ; le niveau ne fait que l'annoncer et régler la musique.
func _on_leviathan_phase(phase: int) -> void:
	match phase:
		LeviathanCombat.Phase.ARMOR:
			# La rangée de pastilles suit le nombre de plaques du cycle : au cycle 2 il
			# n'y en a plus que trois, et une quatrième pastille mentirait.
			if _hud != null and _leviathan != null:
				_hud.set_boss_limbs(_LEVIATHAN_PLATE_LABELS.slice(0, _leviathan.plates().size()))
			_leviathan_cycle_beat()
		LeviathanCombat.Phase.DIVE:
			# La mise en scène est portée par `dive_started` : ici, seulement la musique.
			_leviathan_cycle_beat()
		LeviathanCombat.Phase.DEFEATED:
			# La mort est portée par `defeated` → `_on_final_boss_defeated` (finale Helios).
			# Seul le compteur est éteint ici : le panneau, lui, survit à la phase.
			if _hud != null:
				_hud.set_boss_cycle("")

## Règle la musique sur l'avancement du combat. `boss_phase` porte le CYCLE : la
## partition monte à chaque tour, et le dernier cycle sonne comme le dernier.
func _leviathan_cycle_beat() -> void:
	if _leviathan == null:
		return
	var cycles: int = _leviathan.tuning.cycle_count if _leviathan.tuning != null else 1
	var cycle := _leviathan.cycle()
	_music.boss_phase = mini(cycle, maxi(cycles - 1, 0))
	_music.boss_phase_count = cycles
	_update_music()
	var label := _leviathan_cycle_label(cycle, cycles)
	if _hud != null:
		_hud.set_boss_cycle(label)
	print("[Level] leviathan %s — %s" % [label,
		"noyau" if _leviathan.phase() == LeviathanCombat.Phase.DIVE else "armure"])

## Le cycle courant, tel que le joueur doit le lire.
##
## ⚠️ AU-DELÀ DE `cycle_count`, NE JAMAIS AFFICHER « 4 / 3 ». Le combat n'est pas borné à
## trois tours et ne l'a jamais été : `plates_for_cycle()` rend le plancher de plaques
## indéfiniment, et le boss ne meurt qu'une fois le flux assez frappé. L'invariant 5 de
## `LeviathanTuning` garantit seulement que trois tours SUFFIRAIENT à un joueur tirant
## 85 % du temps dans le noyau à la cadence de référence — c'est une hypothèse de
## dimensionnement, pas une fin de combat. Le playtest du 2026-08-25 a produit un quatrième
## tour, et le journal a affiché « cycle 4/3 » : un compteur qui dépasse son total dit au
## joueur que le jeu s'est trompé. On nomme le dépassement au lieu de le compter.
## Le nom de la phase courante, pour qui mesure plutôt que pour qui joue : la sonde de
## densité s'en sert pour situer un chiffre. Public, parce qu'un outil de mesure n'a pas à
## connaître l'`enum` privé du director.
func phase_label() -> String:
	return str(Phase.keys()[_phase]) if _phase >= 0 and _phase < Phase.size() else "?"

func _leviathan_cycle_label(cycle: int, cycles: int) -> String:
	return "DERNIER ASSAUT" if cycle >= cycles else "CYCLE %d / %d" % [cycle + 1, cycles]

func _physics_process(delta: float) -> void:
	_rebuild_solids()
	_probe_dive(delta)
	_trace_dive(delta)
	if _solids_overlay != null and _player != null and _player.stats != null:
		_solids_overlay.draw(_solids, _player.plane_lift, _player.plane_position,
			_player.plane_forward(), _player.stats.body_half_length, _player.stats.body_radius)
	_crush_light_bodies()
	_update_engine_hum()
	if _approach_active:
		_advance_boss_approach(delta)
	_track_core_target(delta)

## Refait les corps solides du niveau et les donne au chasseur.
##
## Le chasseur s'en dégage CHEZ LUI, après son propre déplacement — l'ordre compte, sinon on
## le corrige puis le pilotage le renfonce dans l'obstacle à l'image suivante.
func _rebuild_solids() -> void:
	_solids.clear()
	if is_instance_valid(_leviathan):
		_solids.reserve(_leviathan.solid_capacity())
		_leviathan.fill_solids(_solids)
	if is_instance_valid(_harvester):
		_solids.reserve(_harvester.solid_capacity())
		_harvester.fill_solids(_solids)
	# ⚠️ LE CARTER DU RÉACTEUR, et c'est le NIVEAU qui le verse parce qu'il est le seul à
	# connaître à la fois la chambre et le boss. Le module de combat ne sait rien du décor ;
	# le décor ne sait rien du combat. Le carter est plus large que le flux (2,27 contre
	# 1,80) : rendre le flux solide ne suffisait pas — « le réacteur central ne devrait pas
	# être franchissable » vaut pour la machine, pas seulement pour la boule qu'elle porte.
	#
	# `visible` fait foi : la chambre n'existe que pendant la plongée, et le carter avec elle.
	if is_instance_valid(_core_interior) and _core_interior.visible:
		_solids.reserve(_solids.size() + 1)
		_solids.add_disc(_core_interior.reactor_plane_position(),
			_core_interior.housing_radius())
	# ⚠️ LES DEUX SEMEURS, et ils ne tournent jamais ensemble (ADR-0027 : la vague, puis le
	# champ d'astéroïdes). Les interroger tous les deux coûte deux tests et évite d'avoir à
	# savoir lequel est actif — ce que ce fichier n'a pas à connaître.
	for spawner in [_wave_spawner, _field_spawner]:
		if is_instance_valid(spawner):
			_solids.reserve(spawner.solid_capacity())
			spawner.fill_solids(_solids, _crusher_mass(), _crush_ratio())
	if _player != null and _player.solids != _solids:
		_player.solids = _solids

## Ce que le chasseur subit dans la chambre, mesuré dans le JEU et non dans un banc.
##
## Silencieuse sans `--dive-probe`, et muette hors de la plongée : c'est un instrument, pas
## une trace de tous les jours.
## Enregistre une image de plongée : le temps, la commande, la position, le contact, et
## TOUTES les formes solides telles que la collision les voit — murs compris, avec leur
## rotation du moment.
func _trace_dive(delta: float) -> void:
	if not _dive_trace or _player == null or _player.stats == null:
		return
	# ⚠️ TOUT LE COMBAT, ET PLUS SEULEMENT LA PLONGÉE. La première version ne s'armait que
	# dans le noyau : si le défaut se produit dehors — pendant l'armure, l'approche — elle
	# n'en garde aucune trace, et il faut refaire une partie pour rien. Un instrument qui ne
	# regarde qu'où l'on croit que le problème est ne sert qu'à confirmer ce qu'on croit.
	if _phase != Phase.FINAL_BOSS:
		return
	_trace_age += delta
	var here := _player.plane_position
	var forward := _player.plane_forward()
	var half := _player.stats.body_half_length
	var radius := _player.stats.body_radius
	var touching := PlaneCollider.capsule_blocks(_solids, here, forward, half, radius)
	var dive := 1 if _leviathan != null \
		and _leviathan.phase() == LeviathanCombat.Phase.DIVE else 0
	var line := "%.4f;%.3f;%.3f;%.3f;%.3f;%d;%d" % [_trace_age,
		_player.last_input.x, _player.last_input.y, here.x, here.y,
		1 if touching else 0, dive]
	for i in _solids.size():
		var c := _solids.centre_of(i)
		line += "|%d,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f" % [_solids.kind_at(i), c.x, c.y,
			_solids.param(i, 2), _solids.param(i, 3), _solids.param(i, 4), _solids.param(i, 5)]
	_trace_lines.append(line)

## Écrit l'enregistrement à côté de l'exécutable, comme la capture d'écran — c'est le seul
## dossier que WSL peut relire après un lancement Windows.
func _flush_dive_trace() -> void:
	if not _dive_trace or _trace_lines.is_empty():
		return
	var path := OS.get_executable_path().get_base_dir().path_join("dive-trace.csv")
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("[DiveTrace] ecriture impossible : %s" % path)
		return
	file.store_line("t;input_x;input_y;pos_x;pos_y;contact;dive|formes(kind,p0..p5)")
	for line in _trace_lines:
		file.store_line(line)
	file.close()
	print("[DiveTrace] %d images -> %s" % [_trace_lines.size(), path])

func _probe_dive(delta: float) -> void:
	if not _dive_probe or _player == null or _player.stats == null:
		return
	if _leviathan == null or _leviathan.phase() != LeviathanCombat.Phase.DIVE:
		_probe_clock = 0.0
		return
	_probe_clock -= delta
	if _probe_clock > 0.0:
		return
	_probe_clock = 0.25
	var here := _player.plane_position
	var forward := _player.plane_forward()
	var half := _player.stats.body_half_length
	var radius := _player.stats.body_radius
	var touching := PlaneCollider.capsule_blocks(_solids, here, forward, half, radius)
	var freed := PlaneCollider.resolve_capsule(_solids, here, forward, half, radius)
	var centre := _core_interior.reactor_plane_position() if _core_interior != null \
		else Vector2.ZERO
	print("[Dive] pos (%+.2f, %+.2f) | r=%.2f du centre | %s | poussee (%+.2f, %+.2f) | %d formes | bornes %.1f..%.1f"
		% [here.x, here.y, here.distance_to(centre),
			"CONTACT" if touching else "libre  ",
			freed.x - here.x, freed.y - here.y, _solids.size(),
			GameplayPlane.bounds.position.y, GameplayPlane.bounds.end.y])

## Le poids du chasseur, et le rapport à partir duquel il passe à travers. Zéro quand il n'y
## a pas de chasseur : personne n'écrase, tout est un mur — la règle d'avant la masse.
func _crusher_mass() -> float:
	return _player.stats.mass if _player != null and _player.stats != null else 0.0

func _crush_ratio() -> float:
	return _player.stats.crush_mass_ratio if _player != null and _player.stats != null else 0.0

## Broie les coques trop légères que le chasseur traverse, et lui en fait payer le prix.
##
## ⚠️ APRÈS `_rebuild_solids()`, ET DANS CET ORDRE. Ce que la reconstruction vient d'écarter
## des obstacles est exactement ce qui doit être écrasé ici : deux listes tirées du même
## test, à la même image. Les séparer les ferait diverger d'une image — assez pour qu'une
## unité soit à la fois traversable et vivante, ce que le joueur lirait comme un fantôme.
func _crush_light_bodies() -> void:
	if _player == null or _player.stats == null:
		return
	var mass := _crusher_mass()
	var ratio := _crush_ratio()
	var crushed := 0.0
	for spawner in [_wave_spawner, _field_spawner]:
		if is_instance_valid(spawner):
			crushed += spawner.crush_contacts(_player.plane_position,
				_player.plane_forward(), _player.stats.body_half_length,
				_player.stats.body_radius, mass, ratio)
	if crushed > 0.0:
		var cost := MassRules.crush_damage(crushed, _player.stats.crush_damage_per_mass)
		_player.take_contact_damage(cost)
		# ⚠️ UNE TRACE D'ÉVÉNEMENT, PAS UNE TRACE DE BOUCLE : elle ne s'écrit que sur une
		# collision réelle, quelques fois par partie. C'est le seul endroit d'où l'on peut
		# voir la mécanique tourner — un écrasement ne laisse aucune marque à l'écran une
		# fois l'explosion passée, et l'équilibrage se fait sur le journal (balance-prober).
		print("[Level] ecrase %.1f t — %.0f de bouclier" % [crushed, cost])

## Le repère de cible SUIT le flux, à l'image, et il BAT.
##
## ⚠️ Le suivi n'est pas un luxe : c'est tout l'intérêt. Un repère posé une fois à l'entrée
## se retrouverait à plusieurs unités de la cible dès la première seconde de dérive — il
## deviendrait le second signal faux, après le réacteur du décor.
##
## Sondage plutôt que signal : c'est une valeur CONTINUE, et un signal par image ne dirait
## rien de plus qu'une lecture par image.
func _track_core_target(delta: float) -> void:
	if _core_interior == null or _leviathan == null:
		return
	if not _core_interior.visible:
		return
	_core_marker_age += delta
	_core_interior.set_target_marker(_leviathan.flux_plane_position(), true)
	# ⚠️ Le battement dit si le tir COMPTE. Un repère qui bat pareil ouvert et fermé
	# laisserait le joueur tirer dans un blindage plein sans rien pour l'en avertir.
	_core_interior.pulse_target_marker(_core_marker_age, _leviathan.reactor_open())
	_core_interior.pose_rings(_leviathan.tuning.reactor_rings, _leviathan.combat_age())
	for i in _leviathan.tuning.node_count:
		_core_interior.pose_node(i, _leviathan.node_plane_position(i),
			_leviathan.node_alive(i), _core_marker_age)

# --- Helios Lance finale + victory (spec §12.7) -----------------------------

func _on_final_boss_defeated(world_position: Vector3) -> void:
	_game_state.add_score(20000)
	if _hit_stop != null:
		_hit_stop.freeze(HitStop.BOSS)
	if _hud != null:
		_hud.hide_boss()
	# The boss is destroyed: remove its hull so it does not linger through the
	# finale and the docking close (it was staying visible before — ADR-0010).
	if _final_boss != null:
		_final_boss.queue_free()
		_final_boss = null
	_fire_helios_lance(world_position)

func _fire_helios_lance(target: Vector3) -> void:
	# Spectacular finish: heavy explosions along the boss + strong shake, then victory.
	_sfx(&"helios_lance")
	if _camera_director != null:
		_camera_director.add_trauma(1.0)
	for i in 8:
		var offset := Vector3(randf_range(-4.0, 4.0), 0.0, randf_range(-3.0, 3.0))
		get_tree().create_timer(0.12 * i).timeout.connect(
			_boom.bind(target + offset, VfxExplosion.Category.HEAVY, 0.7))
	get_tree().create_timer(1.8).timeout.connect(_start_docking)

func _start_victory() -> void:
	_set_phase(Phase.VICTORY)
	print("[Level] VICTORY — score %d" % _game_state.score)
	_show_report(MissionReport.Outcome.VICTORY)

## Le rapport de mission, dans l'une ou l'autre de ses issues.
##
## Même raison qu'à la pause de cacher le HUD : le rapport reprend les coins de l'écran,
## et le score qu'il affiche ferait doublon avec celui du HUD, à deux tailles différentes.
func _show_report(outcome: MissionReport.Outcome) -> void:
	var screen := MissionReportScene.instantiate()
	screen.setup(_game_state.score, outcome)
	add_child(screen)
	if _hud != null:
		_hud.visible = false

## The victory theme waits for the last enemy shot to leave the screen, so the resolution
## does not land over incoming fire (adaptive_music_structure.md §mix). Until then the
## music stays on Final Charge.
func _process(_delta: float) -> void:
	if _phase != Phase.VICTORY or _music.hostiles_clear:
		return
	if _bullet_manager == null or _bullet_manager.team_count(BulletManager.Team.ENEMY) == 0:
		_music.hostiles_clear = true
		_update_music()

# --- Player feedback ---------------------------------------------------------

func _on_player_hit(_world_position: Vector3) -> void:
	_sfx(&"shield_impact")
	if _camera_director != null:
		_camera_director.add_trauma(0.45)

func _on_player_destroyed(world_position: Vector3) -> void:
	_boom(world_position, VfxExplosion.Category.HEAVY, 0.9)
	_sfx(&"player_death")
	# ⚠️ L'ÉCRAN SE VIDE DE CE QUI VENAIT DE TUER. Sans ça, le chasseur renaît 1,2 s plus
	# tard au centre bas dans le rideau qui l'a eu, et ses 2 s d'invulnérabilité expirent
	# au milieu — c'est la mort en chaîne que tous les jeux du genre neutralisent ainsi.
	# Les tirs du JOUEUR survivent : ils n'ont jamais tué personne.
	if _bullets != null:
		_bullets.clear_team(BulletManager.Team.ENEMY)

## Le dernier chasseur est perdu.
##
## ⚠️ CE CHEMIN NE MENAIT NULLE PART. Il relançait le joueur en silence (`continue_run`,
## continues illimités, spec §8.4) : l'état `GAME_OVER` de la machine globale était
## déclaré, transitions comprises, et n'était JAMAIS atteint. Une partie perdue se
## confondait donc avec une vie perdue, et le seul indice était une ligne de journal
## que le joueur ne lit pas.
##
## Les continues ne disparaissent pas pour autant : ils passent par le bouton
## « REESSAYER » du rapport, qui relance le niveau. Ce qui change, c'est qu'on le DIT.
func _on_game_over() -> void:
	if _phase == Phase.VICTORY or _defeated:
		return
	_defeated = true
	print("[Level] all fighters lost — DEFEAT, score %d" % _game_state.score)
	_game_state.transition_to(GameStateScript.State.GAME_OVER)
	# Le rapport se lève APRÈS l'explosion du dernier chasseur : le poser dans la même
	# image escamoterait la mort, qui est précisément ce que le joueur doit voir.
	get_tree().create_timer(DEFEAT_HOLD).timeout.connect(
		_show_report.bind(MissionReport.Outcome.DEFEAT))

# --- Helpers -----------------------------------------------------------------

## The fighter's engine bed follows its speed. Once the fighter is stowed at the
## closing docking sequence, the hum has no source: it stops for good.
func _update_engine_hum() -> void:
	if _audio == null:
		return
	var flying := _player != null and _player.visible
	if flying:
		_audio.set_engine_intensity(_player.speed_ratio())
		_engine_running = true
	elif _engine_running:
		_engine_running = false
		_audio.stop_engine()

## A banner is a beat, not just a label: it gets a swell so it reads without being read.
func _banner(text: String, color: Color, duration: float) -> void:
	if _hud != null:
		_hud.show_banner(text, color, duration)
	_sfx(&"ui_banner")

func _boom(world_position: Vector3, category: VfxExplosion.Category, trauma: float) -> void:
	if _vfx != null:
		_vfx.spawn_explosion(world_position, category)
	if _camera_director != null:
		_camera_director.add_trauma(trauma)

func _sfx(cue: StringName, volume_db: float = 0.0) -> void:
	if _audio != null:
		_audio.play(cue, volume_db)
