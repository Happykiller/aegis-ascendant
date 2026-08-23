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


func _ready() -> void:
	_slug = _read_slug()
	var data := _build(_slug)
	var errors := data.validate()
	for error in errors:
		# Le banc valide ses propres montages : une donnée fautive ici serait un
		# comportement qu'on réglerait pendant des heures sans qu'il soit jouable.
		push_error("[Lab] montage '%s' invalide : %s" % [_slug, error])
	print("[Lab] unite='%s' exemplaires=%d" % [_slug, UNIT_COUNT])
	print("[Lab] COQUE PROVISOIRE : needle_scout.glb sert de silhouette (lot 1 a venir)")
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
		_:
			push_error("[Lab] unite inconnue '%s' (connues : fan, aimed, mine, maw)" % slug)
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
		_:
			return "unite inconnue"


func _build_pool(data: EnemyData) -> void:
	_respawn_at.resize(UNIT_COUNT)
	for i in UNIT_COUNT:
		var unit := NEEDLE_SCOUT.instantiate() as EnemyController
		# La donnée est posée AVANT l'entrée dans l'arbre : `_ready()` la valide et
		# en déduit si l'unité est réactive.
		unit.data = data
		add_child(unit)
		unit.setup(_bullets, _player)
		unit.reaction_changed.connect(_on_reaction_changed.bind(i))
		unit.destroyed.connect(_on_destroyed)
		_units.append(unit)
		_respawn_at[i] = float(i) * 0.6


func _physics_process(delta: float) -> void:
	_clock += delta
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


## Colonnes centrées : l'unité du milieu tombe sur l'axe, les autres de part et
## d'autre. Le joueur démarre au centre, donc il choisit celle qu'il va toucher.
func _column(index: int) -> float:
	return (float(index) - float(UNIT_COUNT - 1) * 0.5) * COLUMN_SPACING


func _on_reaction_changed(state: int, index: int) -> void:
	print("[Lab] t=%.2f unite=%d -> %s" % [_clock, index, STATE_NAMES[state]])


func _on_destroyed(unit: EnemyController) -> void:
	print("[Lab] t=%.2f abattue (%s)" % [_clock, unit.data.display_name])
