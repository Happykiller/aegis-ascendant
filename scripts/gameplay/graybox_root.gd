extends LevelRoot
## Level director: sequences the level's phases (spec §5, §6, §37) and wires the
## player, HUD, VFX, camera, pickups and encounters together.
##   FIGHTER_WAVES -> MINI_BOSS -> ASTEROID_FIELD -> FINAL_BOSS -> DOCKING -> VICTORY
## Le joueur reste le chasseur de bout en bout (ADR-0010) : plus de transformation en
## forteresse ; le docking clot le niveau apres la defaite du boss final.

const MiniBossScene := preload("res://scenes/bosses/choir_harvester.tscn")
const FinalBossScene := preload("res://scenes/bosses/pale_leviathan.tscn")
const CitadelScene := preload("res://scenes/fortress/aegis_citadel.tscn")

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

## Ce que Lyra dit pendant le combat (`ADR-0035`). Le texte vit dans une Resource : c'est la
## règle du projet pour tout contenu, et c'est ce qui rendra la traduction possible.
const LYRA_LINES := preload("res://resources/dialogue/lyra_ingame.tres")
## Ce que l'écran de pause rappelle : le lieu et les objectifs de la phase en cours.
const ARC := preload("res://resources/levels/ossane_arc.tres")
const BRIEFINGS := preload("res://resources/dialogue/sector_briefings.tres")

## L'écran de pause, gardé pour lui pousser le briefing de la phase courante.

@onready var _wave_spawner: WaveSpawner = get_node_or_null("WaveSpawner")
## La vague du champ d'astéroïdes (ADR-0027) : montée et peuplée au même instant que
## la première, mais endormie. C'est `_start_asteroid_field()` qui la réveille.
@onready var _field_spawner: WaveSpawner = get_node_or_null("AsteroidFieldSpawner")
## Les deux semeurs, dans UN tableau alloué une fois. Les parcourir est un geste de chaque
## image physique (obstacles, puis écrasements) : le littéral qui servait avant allouait un
## `Array` à chaque passage, pour deux références figées au montage.
@onready var _spawners: Array[WaveSpawner] = [_wave_spawner, _field_spawner]
var _camera_director: CameraDirector = null
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
## ⚠️ DEUX NOMS POUR LA MÊME CHOSE, ET C'EST ASSUMÉ LE TEMPS DE LA REFONTE. Le socle expose
## `_bullets` ; ce fichier écrivait `_bullet_manager` à dix-sept endroits. Renommer aurait
## mélangé un déplacement de responsabilité avec dix-sept réécritures, et la recette de ce
## chantier est « le niveau 1 se joue à l'identique ».
var _bullet_manager: BulletManager = null

var _phase: int = Phase.FIGHTER_WAVES
var _boss: BossController
var _citadel: AegisCitadel
var _final_boss: BossController
## Le module du boss final, gardé pour lire sa progression de combat (la musique la suit).
var _leviathan: LeviathanCombat
var _final_stage: LeviathanStage = null
var _backdrop_hidden: bool = false
var _backdrop_was_visible: bool = true

## Tout ce qui est solide dans le niveau, à cet instant. Rempli à chaque image par les boss
## en place, lu par le chasseur qui s'y conforme.
##
## ⚠️ UN SEUL JEU DE FORMES POUR TOUT LE NIVEAU, et il est REFAIT à chaque image sans jamais
## être réalloué (spec §26.1). Le niveau ne sait pas ce qu'il contient — ni plaques, ni bras,
## ni anneaux : chaque boss DÉCLARE ses formes par `fill_solids()`. C'est ce qui rend la loi
## « les corps ne se chevauchent pas » applicable au boss suivant sans toucher à ce fichier.

## Les deux instruments du combat final (`--dive-probe`, `--dive-trace`), ou `null` si aucun
## drapeau ne les appelle — auquel cas le niveau ne paie même pas un appel. Ils vivaient ici,
## en cent dix lignes de formatage de CSV : voir `DiveInstruments`.
var _dive_instruments: DiveInstruments = null
## Superposition des couches invisibles (corps, cibles, écrans de tir). Voir `SettingsData`.
## Le module de combat du mini-boss, gardé pour ses formes solides. ⚠️ Testé par
## `is_instance_valid()` à chaque image et non vidé à sa mort : le Harvester est libéré par
## le niveau, et une référence morte lue une fois de trop planterait la partie sur la
## transition la plus chargée de l'arc.
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
	# ⚠️ LE SOCLE D'ABORD. Il trouve les services, monte le runtime de combat, adopte les unités,
	# branche le HUD, ouvre la pause et pose les calques de debug — tout ce que ce fichier
	# faisait à la main, et que le niveau 2 a oublié de refaire.
	setup_level()
	_bullet_manager = _bullets
	_camera_director = _camera as CameraDirector
	_game_state.reset_session()
	# ⚠️ LES LOIS DU COMBAT NE SONT PLUS ÉCRITES ICI. Mourir, toucher, percuter, parler valent
	# dans tout le jeu : elles vivent dans `CombatRuntime`, et ce niveau ne fait que les
	# convoquer. Elles étaient dans ce fichier, et un second niveau n'avait donc aucun moyen
	# d'en hériter — c'est ce que l'opérateur a constaté en jouant le niveau 2 muet, sans
	# explosions et sans écrasement.
	# ⚠️ SEULE LA PROGRESSION RESTE ICI : elle alimente la musique, qui appartient au niveau. La
	# FIN d'une vague, elle, ferme un temps de l'arc — c'est le directeur qui l'écoute.
	if _wave_spawner != null:
		_wave_spawner.progress_changed.connect(_on_wave_progress)
	# Deux vagues, deux fins distinctes : celle des chasseurs ouvre sur le mini-boss,
	# celle du champ sur le boss final. La progression, elle, alimente la MÊME jauge
	# musicale — c'est toujours « où en est la vague en cours ».
	if _field_spawner != null:
		_field_spawner.progress_changed.connect(_on_wave_progress)
	if _player != null:
		_player.hit_taken.connect(_on_player_hit)
		_player.destroyed_at.connect(_on_player_destroyed)
		_player.game_over.connect(_on_game_over)
		_player.fired.connect(_on_player_fired)
		_player.shield_changed.connect(_on_player_shield_changed)
	# L'écran de pause reprend l'interface entière (bloc d'identité en haut à gauche,
	# COMMS en bas à gauche, comme l'accueil) : ces places sont celles du HUD, et deux
	# blocs de texte superposés ne se lisent ni l'un ni l'autre. Le HUD s'efface donc
	# le temps de la pause. Il n'en sait rien — c'est le niveau qui les raccorde.
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
	# Le gel d'impact. Monté en code : il n'a ni transform ni enfant, et l'ajouter aux
	# trois scènes qui portent un CameraDirector n'apporterait rien de plus.
	# ⚠️ ON EMPRUNTE CEUX DU RUNTIME, on n'en crée pas. L'arrêt sur image et l'état musical
	# sont demandés par des ÉVÉNEMENTS DE COMBAT — une plaque qui cède, un boss qui tombe — et
	# un boss n'a pas à connaître le script du niveau qui l'héberge pour figer une image. Les
	# références locales restent : elles sont lues à quarante endroits, et les remplacer aurait
	# mélangé un déplacement de responsabilité avec une réécriture.
	_hit_stop = _runtime.hit_stop
	_music = _runtime.music
	# ⚠️ SONDE DE PLONGÉE (`--dive-probe`). Elle existe parce qu'une simulation headless a
	# affirmé que le convoyeur de la chambre avait disparu, pendant que l'opérateur le vivait
	# encore : « toujours le même syndrome, j'ai comme un mur qui me pousse ». Quand le banc
	# et le jeu se contredisent, c'est le JEU qui a raison — et il faut l'instrumenter, pas
	# raffiner le banc. Elle imprime, quatre fois par seconde et seulement pendant la
	# plongée, ce que le chasseur subit VRAIMENT : sa position, son contact, ce qui est versé.
	# ⚠️ L'ENREGISTREMENT DE PARTIE (`--dive-trace`), demandé par l'opérateur après trois
	# diagnostics qui se contredisaient : « enregistre le déplacement du vaisseau en même
	# temps que la position des murs ». C'est la seule preuve qui ne dépende d'aucune
	# hypothèse — ni la mienne, ni celle d'un banc. On écrit la COMMANDE en plus de la
	# position : sans elle, une trace ne distingue pas « il va à droite » de « il est poussé
	# à droite », et c'est exactement la question posée.
	_dive_instruments = DiveInstruments.from_args(args)
	ReactorRings.disabled = "--no-rings" in args
	# ⚠️ LA REPRÉSENTATION PHYSIQUE, VISIBLE (`--show-solids`). Demandée par l'opérateur après
	# quatre correctifs à l'aveugle : « faire apparaître la représentation dans l'espace des
	# points de collision, pour qu'on voie visuellement la différence ». Quand l'image et la
	# collision sont deux objets, la superposition est la seule preuve qui ne discute pas.
	# ⚠️ TOUJOURS MONTÉ ; ce sont les COUCHES qui s'allument — depuis le menu des options
	# (« Débogage »), allumées par défaut en build de développement, éteintes en release. « Dès
	# qu'on est en développement, on doit toujours les afficher » (opérateur, 2026-08-28) —
	# c'est cet outil, et lui seul, qui a montré que le décor et la collision tournaient en
	# sens inverse, après quatre correctifs à l'aveugle. `--show-solids` force tout,
	# `--hide-solids` coupe tout (capture propre) ; sinon le réglage du joueur fait foi.
	if ReactorRings.disabled:
		print("[Level] ISOLATION : aucun mur dans la chambre (--no-rings)")
	if "--density-probe" in args and _bullets != null:
		add_child(DensityProbe.make(_bullets, phase_label))
	# Aucun de ces sauts n'éteint le semeur lui-même : `_set_phase()` le fait pour tout le
	# monde, dès qu'on quitte `FIGHTER_WAVES`.
	# ⚠️ LES SAUTS PASSENT PAR L'ARC, PLUS PAR DES APPELS DIRECTS. Un saut qui monterait le temps
	# « à la main » finirait par diverger de l'enchaînement normal — et l'on découvrirait avec
	# un raccourci ce qui est cassé sans lui. `jump_to` emprunte exactement le même chemin
	# d'entrée : musique, bornes, décor, bannière.
	_director = setup_arc(ARC)
	_director.beat_entering.connect(_on_beat_entering)
	_director.beat_revealed.connect(_on_beat_revealed)
	_director.beat_scripted.connect(_on_beat_scripted)
	if "--skip-to-boss" in args:
		_director.jump_to(&"MINI_BOSS")
	elif "--skip-to-field" in args:
		_director.jump_to(&"ASTEROID_FIELD")
	elif "--skip-to-final" in args:
		_director.jump_to(&"FINAL_BOSS")
	elif "--skip-to-dock" in args:
		_director.jump_to(&"DOCKING")
	elif "--skip-to-victory" in args:
		_game_state.add_score(28450)
		_director.jump_to(&"VICTORY")
	else:
		_director.begin()
	# Start the score. Runs after the --skip-to-* flags, so a skipped run opens on the
	# state it actually jumped to instead of fading out of Launch.
	_update_music()
	# Lyra ouvre la mission. ⚠️ SEULEMENT SI ON PART DU DÉBUT : les `--skip-to-*` ci-dessus ont
	# déjà changé de phase, et l'entendre annoncer un secteur qu'on vient de survoler serait
	# pire que le silence. Le test est sur `_phase`, pas sur les arguments — un futur drapeau
	# de saut serait couvert sans qu'on y pense.
	if _phase == Phase.FIGHTER_WAVES:
		say(&"mission_start")
	# ⚠️ LA PHASE, PAS UNE CONSTANTE. Cette ligne annonçait `FIGHTER_WAVES` quoi qu'il arrive,
	# donc un `--skip-to-dock` la faisait paraître APRÈS `[Level] DOCKING` : un journal qui
	# ment sur la phase envoie la lecture suivante dans le mur, et c'est le journal qui sert
	# de preuve ici (relevé en jouant, 2026-08-28).
	print("[Level] ready — phase %s" % Phase.keys()[_phase])

# --- L'arc, temps par temps --------------------------------------------------
#
# ⚠️ CE QUI RESTE ICI EST CE QUI N'APPARTIENT QU'AU COULOIR D'OSSANE. La séquence, les noms,
# les bannières, les répliques, les vagues et les boss sont dans `ossane_arc.tres`. Ce fichier
# ne garde que ses décors sur mesure : le survol de lune, le puits qui monte, l'appontage.

## Le temps commence, rien n'est encore affiché. ⚠️ LA MUSIQUE ET LES BORNES D'ABORD : un temps
## qui les réglerait après son décor ferait entendre la phase précédente sous la nouvelle.
func _on_beat_entering(beat: LevelBeat) -> void:
	# ⚠️ Le nom du temps N'EST PAS forcément une phase. `BOSS_APPROACH` n'en est pas une : le
	# puits monte pendant qu'on est encore dans le champ d'astéroïdes, et c'est bien ce
	# briefing-là que l'écran de pause doit montrer.
	var phase: Variant = Phase.get(String(beat.id))
	if phase != null:
		if beat.id == &"ASTEROID_FIELD":
			# AVANT `_set_phase` : celui-ci résout la musique, et il la résoudrait sur la
			# progression de la vague PRÉCÉDENTE — donc sur Fleet Battle à 1,0, alors que la
			# traversée est censée s'ouvrir sur son propre lit.
			_music.wave_progress = 0.0
		_set_phase(phase)

## Le voile est plein : c'est ici, et nulle part ailleurs, que le décor bascule.
func _on_beat_revealed(beat: LevelBeat) -> void:
	match beat.id:
		&"ASTEROID_FIELD":
			_show_moon_flyby(true)
		&"FINAL_BOSS":
			# ⚠️ ICI ET PAS À LA FIN DU CHAMP : c'est le seul point par lequel TOUS les chemins
			# passent, `--skip-to-final` compris. Un décor qui survivrait à sa phase se
			# retrouverait sous le boss final.
			_show_moon_flyby(false)

## Les temps que le directeur ne sait pas jouer : ceux qui sont du sur-mesure.
func _on_beat_scripted(beat: LevelBeat) -> void:
	match beat.id:
		&"BOSS_APPROACH":
			_start_boss_approach()
		&"DOCKING":
			_start_docking()
		&"VICTORY":
			_start_victory()

## ⚠️ `--no-wave` SUPPRIME LES DEUX VAGUES, et l'approche avec elles — sans joueur à aspirer,
## elle serait trois secondes d'écran vide. Sans ce crochet, l'arc s'arrêterait sur un semeur
## qui ne se videra jamais.
func should_skip_beat(beat: LevelBeat) -> bool:
	if beat.kind == LevelBeat.Kind.WAVE:
		return _waves_disabled
	if beat.id == &"BOSS_APPROACH":
		return _waves_disabled or _player == null
	return false

## La mise en scène du boss reçoit les services du niveau, et le boss final est retenu : le
## HUD, les obstacles et les écrans de tir le consultent à chaque image.
func dress_boss_stage(stage: BossStage, beat: LevelBeat) -> void:
	super.dress_boss_stage(stage, beat)
	var leviathan := stage as LeviathanStage
	if leviathan == null:
		return
	# ⚠️ LE FOND EST AU NIVEAU, LA PLONGÉE LE DEMANDE. Il s'en sert aussi pour le survol de
	# lune : deux propriétaires du même état finiraient par se contredire.
	leviathan.backdrop_gate = _set_backdrop_hidden
	_final_stage = leviathan

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
	if _runtime != null:
		_runtime.push_music()

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
	# ⚠️ AU MOMENT DE LA PAUSE, PAS AU MONTAGE. Le briefing suit la phase, et la phase change
	# six fois dans une partie : le poser une fois pour toutes afficherait « patrouille
	# avancée » au milieu du boss final. C'est le NIVEAU qui sait où l'on en est — l'écran de
	# pause ne connaît ni les phases, ni le boss, et n'a aucune raison de l'apprendre.
	if is_paused and _pause != null:
		_pause.show_briefing(BRIEFINGS.find(StringName(phase_label())))

# --- Fighter waves -----------------------------------------------------------


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

## Every connecting bullet, from either side. Coloured by who was hit, so a glance
## tells you whether you landed a shot or took one: cold white on an enemy hull,
## shield cyan on ours (docs/forge/output/graybox_palette.md).
## Audible warning when the shield drops under 25% (spec §8.3).
func _on_player_shield_changed(ratio: float, _current: float, _maximum: float) -> void:
	if _alarm_armed and ratio <= _ALARM_TRIGGER_RATIO:
		_alarm_armed = false
		_sfx(&"danger_alarm")
	elif not _alarm_armed and ratio >= _ALARM_REARM_RATIO:
		_alarm_armed = true


func _on_boss_health(ratio: float) -> void:
	if _hud != null:
		_hud.set_boss_health(ratio)
	# Only the final boss drives the boss music: the mini-boss shares Fleet Battle.
	if _phase == Phase.FINAL_BOSS:
		_music.boss_health_ratio = ratio
		_update_music()


# --- Champ d'astéroïdes (ADR-0027) -------------------------------------------
#
# La traversée qui sépare les deux boss. Aucun boss, aucun décor dédié à ce stade :
# une seconde vague, jouée avec les trois unités que le bestiaire avait livrées sans
# qu'aucune rencontre ne les emploie. Le décor viendra par-dessus (lot 2 du plan),
# sans rien changer à cet enchaînement.




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

## Joue un raccord : `on_midpoint` est appelé voile fermé (c'est là qu'on change le
## décor), `on_finished` voile rouvert (c'est là qu'on rend la main à l'arc).
##
## ⚠️ SANS VOILE, LES DEUX APPELS PARTENT QUAND MÊME, dans l'ordre. Une mise en scène doit
## tolérer d'être absente : `--skip-to-*` et les tests montent le niveau sans passer par
## les chemins qui la construisent, et un arc qui s'arrêterait là se lirait comme un boss
## qui ne vient pas — exactement le défaut que `_start_asteroid_field()` évite déjà.

## Bascule le décor de la phase. Le fond spatial CÈDE LA PLACE au lieu de s'y ajouter :
## c'est la décision d'`ADR-0027`, et elle vient autant du budget GPU que de la demande
## (« qu'on n'ait pas le même décor qu'avant le premier boss »).
func _show_moon_flyby(on: bool) -> void:
	if _moon_flyby == null:
		return
	_moon_flyby.reveal(on)
	_set_backdrop_hidden(on)


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
		veil(_leave_asteroid_field, _director.advance)
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
	veil(_leave_asteroid_field, _director.advance)

## Le survol s'éteint sous le voile fermé. ⚠️ `_start_final_boss()` garde SA propre
## extinction : c'est le seul point par lequel tous les chemins passent, `--skip-to-final`
## compris, et un décor qui survivrait à sa phase se retrouverait sous le boss.
func _leave_asteroid_field() -> void:
	_show_moon_flyby(false)

# --- Final boss + docking close (ADR-0010; docking was the mid-level §6.5) ----

func _start_docking() -> void:
	_set_phase(Phase.DOCKING)
	say(&"docking")
	print("[Level] DOCKING")
	_citadel = CitadelScene.instantiate() as AegisCitadel
	_citadel.plane_position = Vector2(0.0, 22.0) # off-screen above
	add_child(_citadel)
	_citadel.arrived.connect(_on_citadel_arrived, CONNECT_ONE_SHOT)
	_citadel.slide_to(Vector2(0.0, 11.0), 9.0)

func _on_citadel_arrived() -> void:
	if _player != null:
		_player.autopilot_reached.connect(_on_player_docked, CONNECT_ONE_SHOT)
		_player.begin_docking(Vector2(0.0, 6.3))

func _on_player_docked() -> void:
	_boom(GameplayPlane.to_world(Vector2(0.0, 6.6)), VfxExplosion.Category.MEDIUM, 0.5)
	_sfx(&"docking_lock")
	if _player != null:
		_player.stow()
	_director.advance()


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

func _exit_tree() -> void:
	if _dive_instruments != null:
		_dive_instruments.flush()
	GameplayPlane.reset_bounds()

func phase_label() -> String:
	return str(Phase.keys()[_phase]) if _phase >= 0 and _phase < Phase.size() else "?"

func dialogue() -> DialogueScript:
	return LYRA_LINES

func briefings() -> BriefingBook:
	return BRIEFINGS

func _physics_process(delta: float) -> void:
	_rebuild_solids()
	if _dive_instruments != null:
		_dive_instruments.tick(delta, _player, _solids, _phase == Phase.FINAL_BOSS,
			_final_stage != null and _final_stage.is_diving(),
			_final_stage.core_plane_position() if _final_stage != null \
				else Vector2.ZERO)
	# ⚠️ LES ÉCRANS SE VERSENT ICI, ET NON DANS LE MODULE DE COMBAT. Le boss connaît la
	# géométrie de son blindage ; il ne connaît pas le gestionnaire de projectiles, et c'est
	# le niveau qui tient les deux. Hors plongée, `fire_screens()` rend un jeu vide : les
	# balles ne paient alors aucun test.
	if _bullets != null:
		_bullets.screens = _director.fire_screens() if _director != null else null
	# Les calques de debug : le socle sait les dessiner, ce niveau lui donne ses écrans — les
	# murs du boss final, que lui seul connaît.
	draw_debug_zones(_director.fire_screens() if _director != null else null)
	_crush_light_bodies()
	_update_engine_hum()
	if _approach_active:
		_advance_boss_approach(delta)
	if _final_stage != null:
		_final_stage.advance(delta)

## Refait les corps solides du niveau et les donne au chasseur.
##
## Le chasseur s'en dégage CHEZ LUI, après son propre déplacement — l'ordre compte, sinon on
## le corrige puis le pilotage le renfonce dans l'obstacle à l'image suivante.
func _rebuild_solids() -> void:
	_solids.clear()
	if _final_stage != null:
		_final_stage.fill_solids(_solids)
	# ⚠️ LE DIRECTEUR VERSE LES BOSS, PAS LE NIVEAU. Deux fois de suite, une référence tenue par
	# le niveau a été perdue lors d'un déplacement de responsabilité, et le boss est devenu
	# TRAVERSABLE sans qu'aucun test ne rougisse. Le niveau n'a plus rien à retenir.
	if _director != null:
		_director.fill_solids(_solids)
	# ⚠️ LE CARTER DU RÉACTEUR, et c'est le NIVEAU qui le verse parce qu'il est le seul à
	# connaître à la fois la chambre et le boss. Le module de combat ne sait rien du décor ;
	# le décor ne sait rien du combat. Le carter est plus large que le flux (2,27 contre
	# 1,80) : rendre le flux solide ne suffisait pas — « le réacteur central ne devrait pas
	# être franchissable » vaut pour la machine, pas seulement pour la boule qu'elle porte.
	#
	# `visible` fait foi : la chambre n'existe que pendant la plongée, et le carter avec elle.
	# ⚠️ LES UNITÉS SONT VERSÉES PAR LA LOI COMMUNE, plus par les semeurs. Interroger les
	# sources — deux ici, huit au niveau 2 — c'est se garantir qu'un jour l'une sera oubliée,
	# et une unité absente de cette liste devient TRAVERSABLE sans que rien ne le dise. Le
	# runtime tient la liste des unités une fois pour toutes, quelle que soit leur provenance.
	if _runtime != null:
		_runtime.fill_solids(_solids)
	if _player != null and _player.solids != _solids:
		_player.solids = _solids

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
	if _runtime != null:
		_runtime.crush()


## ⚠️ LE NIVEAU PREND LA MAIN, ET C'EST TOUT L'OBJET DU `true`. La finale Helios dure 1,8 s ;
## laisser le directeur enchaîner l'appontage par-dessus l'escamoterait, et c'est le seul moment
## spectaculaire du niveau. Le score, l'arrêt sur image, le bandeau et la libération de la coque
## sont déjà faits par `BossStage` — il ne reste ici que ce qui n'appartient qu'à Ossane.
func on_boss_defeated(beat: LevelBeat, _stage: BossStage, world_position: Vector3) -> bool:
	if beat == null or beat.id != &"FINAL_BOSS":
		return false
	_final_boss = null
	_fire_helios_lance(world_position)
	return true


func _fire_helios_lance(target: Vector3) -> void:
	# Spectacular finish: heavy explosions along the boss + strong shake, then victory.
	_sfx(&"helios_lance")
	if _camera_director != null:
		_camera_director.add_trauma(1.0)
	for i in 8:
		var offset := Vector3(randf_range(-4.0, 4.0), 0.0, randf_range(-3.0, 3.0))
		get_tree().create_timer(0.12 * i).timeout.connect(
			_boom.bind(target + offset, VfxExplosion.Category.HEAVY, 0.7))
	# ⚠️ C'est ce minuteur qui rend la main à l'arc : la finale finie, le temps suivant s'ouvre.
	get_tree().create_timer(1.8).timeout.connect(_director.advance)

func _start_victory() -> void:
	_set_phase(Phase.VICTORY)
	# ⚠️ CELLE-CI S'ENTEND SANS SE LIRE, et l'ordre des lignes n'y change rien : `show_report()`
	# cache le HUD, donc le panneau de Lyra avec lui. La voix, elle, passe par l'`AudioManager`
	# et survit. Assumé pour l'instant — si le texte doit être lu sur le rapport, c'est au
	# rapport de le porter, pas au HUD de rester ouvert sous lui.
	say(&"mission_complete")
	print("[Level] VICTORY — score %d" % _game_state.score)
	show_report(MissionReport.Outcome.VICTORY)

## Le rapport de mission, dans l'une ou l'autre de ses issues.
##
## Même raison qu'à la pause de cacher le HUD : le rapport reprend les coins de l'écran,
## et le score qu'il affiche ferait doublon avec celui du HUD, à deux tailles différentes.

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
	# ⚠️ LE SEUL DÉNOUEMENT DU JEU QUI N'AVAIT PAS UN MOT. On perdait, un écran rouge se levait,
	# et la navigatrice qui venait de parler pendant toute la mission se taisait. Elle rapporte
	# maintenant — froidement, parce que c'est sa fonction et qu'il n'y a plus personne pour
	# l'entendre (`docs/lore/EXPLOITATION.md` §4). Comme `mission_complete`, elle s'entend sans
	# se lire : le rapport cache le HUD.
	say(&"mission_failed")
	print("[Level] all fighters lost — DEFEAT, score %d" % _game_state.score)
	_game_state.transition_to(GameStateScript.State.GAME_OVER)
	# Le rapport se lève APRÈS l'explosion du dernier chasseur : le poser dans la même
	# image escamoterait la mort, qui est précisément ce que le joueur doit voir.
	get_tree().create_timer(DEFEAT_HOLD).timeout.connect(
		show_report.bind(MissionReport.Outcome.DEFEAT))

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

## Lyra commente ce qui vient d'arriver. ⚠️ ELLE DOUBLE LA BANNIÈRE, ELLE NE LA REMPLACE
## PAS : le titre en deux mots se lit d'un coup d'œil au milieu d'un combat, sa phrase
## demande une seconde qu'on n'a pas toujours (`ADR-0035`). La maquette porte les deux.
##
## Muette si la clé n'existe pas — un moment sans réplique est un moment sans réplique, pas
## une erreur : le combat ne doit pas s'arrêter parce qu'on n'a rien écrit pour lui.

## Délègue à la loi commune. ⚠️ Le raccourci reste parce qu'il est appelé quatorze fois dans
## ce fichier : le remplacer partout aurait mélangé un déplacement de responsabilité avec une
## réécriture de quatorze lignes, et la recette de ce lot est « le niveau 1 se joue à
## l'identique ».
func _boom(world_position: Vector3, category: VfxExplosion.Category, trauma: float) -> void:
	if _runtime != null:
		_runtime.boom(world_position, category, trauma)

func _sfx(cue: StringName, volume_db: float = 0.0) -> void:
	if _runtime != null:
		_runtime.sfx(cue, volume_db)
