extends Node3D
## Bac à sable du bestiaire — une unité, un joueur, rien d'autre.
##
## Régler un comportement d'ennemi dans l'arc complet coûte trois minutes de jeu
## par itération, et ce qu'on observe est noyé dans une vague de cent coques. Ici
## une seule famille tourne en boucle, dans le même éclairage et sous le même
## post-traitement rétro que le jeu — parce qu'un télégraphe jugé sans les
## scanlines est un télégraphe jugé sur une image que le joueur ne verra jamais
## (ADR-0016 : le rendu studio flatte).
##
## Le choix se fait au drapeau, APRÈS le séparateur `++` :
##   ./scripts/play.sh -- --goto-lab=mine
##
## ⚠️ ASSET TEMPORAIRE, SIGNALÉ (spec §0.2). Les unités de ce banc empruntent la
## coque du Needle Scout : les coques de mines n'existent pas encore (lot 1, briefs
## BRIEF-0042/0043). On règle ici un COMPORTEMENT, jamais une silhouette. Le banc
## le répète à chaque lancement dans son en-tête de journal.

const NEEDLE_SCOUT := preload("res://scenes/enemies/needle_scout.tscn")
const BASE_DATA := preload("res://resources/enemies/needle_scout.tres")
const CHOIR_MINE := preload("res://scenes/enemies/choir_mine.tscn")
const NULL_MAW := preload("res://scenes/enemies/null_maw.tscn")
const LEECH_DRONE := preload("res://scenes/enemies/leech_drone.tscn")

## Combien d'exemplaires tournent en même temps. Assez pour lire une interaction
## (deux puits qui s'additionnent, un éveil isolé dans une rangée), pas assez pour
## que le banc devienne une vague.
const UNIT_COUNT := 5
## Colonnes de largage, réparties sur le champ (`GameplayPlane.BOUNDS` : ±14).
const COLUMN_SPACING := 4.2
const SPAWN_Y := 9.5
## Délai avant qu'une unité sortie du champ (ou vidée) ne revienne.
const RESPAWN_DELAY := 2.5

const STATE_NAMES := ["DORMANT", "ALERT", "WINDUP", "ACTIVE", "SPENT"]

@onready var _bullets: BulletManager = $BulletManager
@onready var _player: PlayerFighterController = $PlayerFighter

var _slug: String = "mine"
var _units: Array[EnemyController] = []
var _respawn_at: PackedFloat32Array = PackedFloat32Array()
var _clock: float = 0.0
## Cadence du relevé de vitesse du chasseur. Il existe pour une raison précise :
## un effet qui agit SUR LE JOUEUR ne se lit dans aucun journal d'ennemi. Le
## contrôleur peut appeler `add_drag()` correctement pendant que le joueur ne le
## consomme jamais, et rien ne le dirait — c'est exactement le genre de trou de
## câblage qui a déjà coûté deux fois sur ce projet.
const SPEED_LOG_EVERY := 0.5
var _speed_log_at: float = 0.0
var _last_player_position: Vector2 = Vector2.ZERO


## Familles réellement livrées : coque, Resource et réglages sont ceux du jeu.
## Le banc les ouvre telles quelles — s'il en montait une version à lui, il
## règlerait quelque chose que personne ne joue.
const SHIPPED := {
	"mine": CHOIR_MINE,
	"maw": NULL_MAW,
	"leech": LEECH_DRONE,
}

func _ready() -> void:
	_slug = _read_slug()
	var shipped: PackedScene = SHIPPED.get(_slug)
	if shipped != null:
		print("[Lab] unite='%s' LIVREE : coque et reglages du jeu" % _slug)
		_apply_backdrop_flag()
		_build_pool_from(shipped, null)
		print("[Lab] %s" % _describe(_slug))
		return
	print("[Lab] COQUE PROVISOIRE : needle_scout.glb sert de silhouette")
	var data := _build(_slug)
	var errors := data.validate()
	for error in errors:
		# Le banc valide ses propres montages : une donnée fautive ici serait un
		# comportement qu'on réglerait pendant des heures sans qu'il soit jouable.
		push_error("[Lab] montage '%s' invalide : %s" % [_slug, error])
	print("[Lab] unite='%s' exemplaires=%d" % [_slug, UNIT_COUNT])
	print("[Lab] %s" % _describe(_slug))
	_apply_backdrop_flag()
	_build_pool(data)


## `--no-backdrop` : éteindre la nébuleuse. Même drapeau que le niveau, même nom.
##
## Ce n'est pas un réglage de perf ici, c'est un INSTRUMENT. Une silhouette et un
## point d'ancrage se jugent sur fond noir — sur la nébuleuse, une coque claire sur
## fond clair ne dit rien, et on tourne en rond à corriger ce qu'on ne voit pas.
## Une COULEUR, elle, se juge sur le fond réel : le télégraphe d'une mine a
## justement échoué parce que son magenta se noyait dans une nébuleuse magenta.
## Ce sont deux captures différentes, jamais la même.
func _apply_backdrop_flag() -> void:
	if not ("--no-backdrop" in OS.get_cmdline_user_args()):
		return
	var backdrop := get_node_or_null("SpaceBackdrop") as Node3D
	if backdrop != null:
		backdrop.visible = false
	print("[Lab] fond eteint : on juge une silhouette, pas une couleur")


## Le drapeau, lu après le séparateur `++` : `--goto-lab=<unite>`. Sans valeur, on
## ouvre la mine — c'est l'unité qui a motivé tout le socle.
func _read_slug() -> String:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--goto-lab="):
			var value := arg.split("=", true, 1)[1].strip_edges()
			if not value.is_empty():
				return value
	return "mine"


## Les montages du banc. Chacun DUPLIQUE la Resource du Needle Scout et n'écrase
## que ce qui fait sa signature : ce qui n'est pas écrit ici est, littéralement,
## le réglage d'un ennemi ordinaire.
func _build(slug: String) -> EnemyData:
	var data := BASE_DATA.duplicate() as EnemyData
	data.display_name = "lab_%s" % slug
	match slug:
		"fan":
			# Le tir aveugle : il ferme un couloir, on le contourne.
			data.fire = EnemyData.Fire.FAN
			data.burst_count = 7
			data.fire_interval = 1.6
		"aimed":
			# Le tir qui suit : il punit l'immobilité, on ne l'attend pas de face.
			data.path = EnemyData.Path.HOVER_STRAFE
			data.fire = EnemyData.Fire.AIMED
			data.burst_count = 3
			data.fire_interval = 1.1
		"mine":
			# Elle ne manœuvre pas, elle attend. Le danger naît de la DISTANCE.
			data.path = EnemyData.Path.DRIFT
			data.move_speed = 1.1
			data.fire = EnemyData.Fire.RADIAL
			data.burst_count = 14
			data.alert_radius = 4.5
			data.trigger_radius = 2.2
			data.windup_time = 0.7
			data.active_time = 0.15
			data.rearm_time = 0.0 # usage unique : on peut la dépenser
			data.max_health = 12.0
			data.hitbox_radius = 0.55
			data.score_value = 90
		"maw":
			# Zéro dégât : elle mange l'esquive, et se réarme. Une zone interdite.
			data.path = EnemyData.Path.DRIFT
			data.move_speed = 1.1
			data.fire = EnemyData.Fire.NONE
			data.effect = EnemyData.Effect.GRAVITY_WELL
			data.pull_radius = 4.5
			data.pull_speed_max = 7.0
			data.alert_radius = 5.5
			data.trigger_radius = 3.0
			data.windup_time = 0.5
			data.active_time = 1.6
			data.rearm_time = 2.5
			data.max_health = 26.0
			data.hitbox_radius = 0.55
			data.score_value = 140
		"leech":
			# Elle POURSUIT : premier ennemi du jeu dont la position accumule.
			data.motion = EnemyData.Motion.HOMING
			data.homing_turn_rate = 2.2
			data.chase_time = 8.0
			data.move_speed = 9.0
			data.fire = EnemyData.Fire.NONE
			data.effect = EnemyData.Effect.LEECH
			data.drag_factor = 0.35
			data.drain_per_second = 6.0
			data.alert_radius = 3.0
			data.trigger_radius = 0.9
			data.windup_time = 0.35
			data.active_time = 2.5
			data.rearm_time = 1.5
			data.max_health = 10.0
			data.hitbox_radius = 0.4
			data.score_value = 160
		_:
			push_error("[Lab] unite inconnue '%s' (connues : fan, aimed, mine, maw, leech)" % slug)
	return data


func _describe(slug: String) -> String:
	match slug:
		"fan":
			return "FAN — eventail aveugle vers le bas : il ne vous regarde jamais"
		"aimed":
			return "AIMED — salve resserree qui SUIT : ne restez pas en face"
		"mine":
			return "MINE — dort, s'eveille a 4.5, s'engage a 2.2, couronne apres 0.7 s"
		"maw":
			return "MAW — puits d'aspiration a 3.0, 1.6 s, se rearme apres 2.5 s"
		"leech":
			return "LEECH — poursuit, s'accroche a 0.9, vole 35 pct de vitesse pendant 2.5 s"
		_:
			return "unite inconnue"


func _build_pool(data: EnemyData) -> void:
	_build_pool_from(NEEDLE_SCOUT, data)


## `data` nul = on garde celle que la scène livrée porte déjà.
func _build_pool_from(scene: PackedScene, data: EnemyData) -> void:
	_respawn_at.resize(UNIT_COUNT)
	for i in UNIT_COUNT:
		var unit := scene.instantiate() as EnemyController
		# La donnée est posée AVANT l'entrée dans l'arbre : `_ready()` la valide et
		# en déduit si l'unité est réactive.
		if data != null:
			unit.data = data
		add_child(unit)
		unit.setup(_bullets, _player)
		unit.reaction_changed.connect(_on_reaction_changed.bind(i))
		unit.destroyed.connect(_on_destroyed)
		_units.append(unit)
		_respawn_at[i] = float(i) * 0.6


func _physics_process(delta: float) -> void:
	_clock += delta
	_log_player_speed()
	for i in _units.size():
		var unit := _units[i]
		if unit.active:
			continue
		if _respawn_at[i] < 0.0:
			# Vient de disparaître : on programme son retour.
			_respawn_at[i] = _clock + RESPAWN_DELAY
			continue
		if _clock >= _respawn_at[i]:
			unit.activate(Vector2(_column(i), SPAWN_Y))
			_respawn_at[i] = -1.0


## Relève la vitesse réelle du chasseur, et combien d'unités sont accrochées.
##
## À lire avec `--demo` : sans commande, le chasseur est immobile et un frein sur
## une vitesse nulle ne se voit pas. Avec, il balaie l'horizontale à régime
## constant, et toute prise se lit immédiatement sur le ratio.
func _log_player_speed() -> void:
	if _clock < _speed_log_at:
		return
	_speed_log_at = _clock + SPEED_LOG_EVERY
	var accrochees := 0
	for unit in _units:
		if unit.active and unit.is_attached():
			accrochees += 1
	# ⚠️ ON MESURE LE DÉPLACEMENT RÉEL, PAS `speed_ratio()`. Ce dernier lit la
	# vitesse COMMANDÉE, et le frein d'une sangsue s'applique au déplacement : le
	# ratio reste à 0,85 pendant que le chasseur avance à 40 %. Premier relevé fait
	# avec la mauvaise grandeur, et il annonçait « aucun effet ».
	var parcouru := _player.plane_position.distance_to(_last_player_position) / SPEED_LOG_EVERY
	_last_player_position = _player.plane_position
	print("[Lab] t=%.2f parcouru %.2f u/s (commande %.3f)   accrochees=%d"
		% [_clock, parcouru, _player.speed_ratio(), accrochees])


## Colonnes centrées : l'unité du milieu tombe sur l'axe, les autres de part et
## d'autre. Le joueur démarre au centre, donc il choisit celle qu'il va toucher.
func _column(index: int) -> float:
	return (float(index) - float(UNIT_COUNT - 1) * 0.5) * COLUMN_SPACING


func _on_reaction_changed(state: int, index: int) -> void:
	print("[Lab] t=%.2f unite=%d -> %s" % [_clock, index, STATE_NAMES[state]])


func _on_destroyed(unit: EnemyController) -> void:
	print("[Lab] t=%.2f abattue (%s)" % [_clock, unit.data.display_name])
