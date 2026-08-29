class_name CombatRuntime
extends Node
## Les LOIS d'un combat — celles qui valent dans tout le jeu, quel que soit le niveau.
##
## ⚠️ IL EXISTE PARCE QUE CES LOIS VIVAIENT DANS UN NIVEAU, ET QU'UN SECOND NIVEAU N'AVAIT
## AUCUN MOYEN D'EN HÉRITER. Le constat est de l'opérateur, en jouant le niveau 2 :
## « je ne devrais pas avoir à signaler des bugs de gameplay qu'on a déjà couverts dans le
## niveau 1 ». Il avait raison, et le défaut n'était pas une série d'oublis : c'était une
## FRONTIÈRE MANQUANTE. `graybox_root.gd` fait 1 469 lignes et tient à la fois le runtime
## commun, le level design du niveau 1 et deux boss en dur. Écrire un second niveau sans le
## copier — ce qui était juste — revenait donc à perdre le runtime avec le reste.
##
## Ce qui se perdait, mesuré sur le niveau 2 avant ce fichier : **les ennemis n'explosaient
## plus, ne faisaient plus de bruit et ne lâchaient plus de bonus ; les percuter ne les
## écrasait plus ; et Lyra parlait sans voix** — parce que la ligne qui joue la cue était,
## elle aussi, dans le script du niveau 1 (`graybox_root.gd:1459`).
##
## ⚠️ CE QUI EST ICI, ET CE QUI N'Y EST PAS. Ici : ce qui est vrai de TOUT combat — mourir,
## toucher, percuter, parler. Pas ici : ce qui appartient à un niveau — quelles vagues, quels
## boss, quel décor, quel enchaînement. La règle de partage tient en une question : « est-ce
## que le niveau 3 en aura besoin sans rien y changer ? » Si oui, c'est une loi.
##
## Suit la recommandation d'organisation de Godot : injection de dépendances plutôt que
## chemins en dur, signaux vers le haut pour RENDRE COMPTE, appels vers le bas pour agir.

## Teintes d'impact. Le blanc pour une coque, le cyan pour un bouclier — c'est la seule chose
## qui distingue « j'ai touché » de « il a encaissé », et elle vaut dans tout le jeu.
const HULL_IMPACT_TINT := Color(0.851, 0.902, 0.949)
const SHIELD_IMPACT_TINT := Color(0.247, 0.851, 0.91)

## Secousse d'une mort d'unité ordinaire.
const ENEMY_DEATH_TRAUMA := 0.35

## Rendre compte au niveau, sans que la loi ait à savoir ce qu'il en fera. C'est le sens du
## signal : il RÉPOND à un événement, il n'en déclenche pas un (recommandation Godot).
signal enemy_destroyed(enemy: EnemyController)
signal player_crushed(mass_crushed: float, shield_cost: float)

var _game_state: Object = null
var _bullets: BulletManager = null
var _vfx: VFXManager = null
var _audio: Object = null
var _camera: Node = null
var _hud: CanvasLayer = null
var _pickups: Node = null
var _player: PlayerFighterController = null

## Toutes les unités de la partie, collectées UNE FOIS.
##
## ⚠️ UNE FOIS, ET C'EST UNE CONTRAINTE DE MOTEUR, PAS UNE OPTIMISATION. Le pooling est
## obligatoire (spec §26.1) : aucune unité n'est instanciée en cours de partie, donc la liste
## ne change jamais. La reconstruire à chaque image — par `get_nodes_in_group()`, qui alloue un
## `Array` neuf à chaque appel — serait l'allocation par trame que la spec §26 interdit, sur la
## boucle la plus chaude du jeu.
var _units: Array[EnemyController] = []

## Câble les services partagés. Tous facultatifs : une loi qui n'a pas son service se tait
## plutôt que de faire tomber le niveau — un banc de test n'a ni caméra ni audio.
func bind(game_state: Object, bullets: BulletManager, vfx: VFXManager, audio: Object,
		camera: Node, hud: CanvasLayer, pickups: Node,
		player: PlayerFighterController) -> void:
	_game_state = game_state
	_bullets = bullets
	_vfx = vfx
	_audio = audio
	_camera = camera
	_hud = hud
	_pickups = pickups
	_player = player
	if _bullets != null:
		if not _bullets.target_hit.is_connected(_on_bullet_hit):
			_bullets.target_hit.connect(_on_bullet_hit)
		if not _bullets.bullet_screened.is_connected(_on_bullet_screened):
			_bullets.bullet_screened.connect(_on_bullet_screened)

## Place TOUTES les unités de l'arbre sous la loi commune, d'où qu'elles viennent.
##
## ⚠️ PAR LE GROUPE, ET NON SOURCE PAR SOURCE. Le niveau 1 peuple deux `WaveSpawner`, le
## niveau 2 en peuple un plus sept pools de ponts d'envol, et le niveau 3 fera autre chose.
## Brancher les unités source par source, c'est se garantir qu'un jour l'une des sources sera
## oubliée — et un ennemi qui ne rapporte rien, ne fait pas de bruit et n'explose pas ne
## ressemble pas à un bug, il ressemble à un ennemi.
func adopt(tree: SceneTree) -> void:
	_units.clear()
	for node in tree.get_nodes_in_group("enemies"):
		var unit := node as EnemyController
		if unit == null:
			continue
		_units.append(unit)
		if not unit.destroyed.is_connected(_on_unit_destroyed):
			unit.destroyed.connect(_on_unit_destroyed)
		if not unit.fired.is_connected(_on_unit_fired):
			unit.fired.connect(_on_unit_fired)
		if not unit.hit.is_connected(_on_unit_hit):
			unit.hit.connect(_on_unit_hit)

func units() -> Array[EnemyController]:
	return _units

# ==========================================================================
# Les lois
# ==========================================================================

## MOURIR. ⚠️ Quatre choses, et aucune n'est décorative : le score dit que ça comptait,
## l'explosion et le son disent que c'est arrivé, le bonus dit que ça valait la peine. En
## retirer une seule fait un ennemi qui « disparaît », et c'est ce que le niveau 2 faisait.
func _on_unit_destroyed(unit: EnemyController) -> void:
	if _game_state != null and unit.data != null:
		_game_state.add_score(unit.data.score_value)
	boom(unit.global_position, VfxExplosion.Category.MEDIUM, ENEMY_DEATH_TRAUMA)
	sfx(&"medium_explosion")
	if _pickups != null and _pickups.has_method("roll_drop"):
		_pickups.roll_drop(unit.global_position)
	enemy_destroyed.emit(unit)

func _on_unit_fired() -> void:
	sfx(&"enemy_pulse")

func _on_unit_hit() -> void:
	sfx(&"hull_impact")

## TOUCHER. La teinte dit ce qui a encaissé, pas qui a tiré.
func _on_bullet_hit(plane_position: Vector2, victim_team: int) -> void:
	if _vfx == null:
		return
	var tint := SHIELD_IMPACT_TINT if victim_team == BulletManager.Team.PLAYER \
		else HULL_IMPACT_TINT
	_vfx.spawn_explosion(GameplayPlane.to_world(plane_position),
		VfxExplosion.Category.IMPACT, tint)

func _on_bullet_screened(plane_position: Vector2, _team: int) -> void:
	boom(GameplayPlane.to_world(plane_position), VfxExplosion.Category.IMPACT, 0.0)
	sfx(&"shield_impact")

## PERCUTER. Le chasseur broie ce qui est trop léger pour l'arrêter, et le paie en bouclier.
##
## ⚠️ LE CONTRAT EST ASYMÉTRIQUE, ET C'EST VOULU : l'unité n'a pas de fenêtre d'invulnérabilité
## — dix éclaireurs traversés sont dix morts — tandis que le chasseur passe par
## `take_contact_damage()`, donc par la sienne. Sans ça, traverser une vague serrée viderait le
## bouclier en une image.
func crush() -> void:
	if _player == null or _player.stats == null:
		return
	var mass: float = _player.stats.mass
	var ratio: float = _player.stats.crush_mass_ratio
	var centre := _player.plane_position
	var axis := _player.plane_forward()
	var half_length: float = _player.stats.body_half_length
	var radius: float = _player.stats.body_radius
	var crushed := 0.0
	for unit in _units:
		if not unit.active or unit.data == null or not unit.data.solid:
			continue
		if not MassRules.crushes(mass, unit.data.mass, ratio):
			continue
		var reach: float = unit.data.hitbox_radius + radius
		if PlaneCollider.distance_to_segment(unit.plane_position,
				centre - axis * half_length, centre + axis * half_length) > reach:
			continue
		# ⚠️ `crush()` ET PAS `deactivate()` : elle passe par `_receive_damage()`, donc par la
		# chaîne de la mort ordinaire — `died` → `destroyed` → score, explosion, bonus. Une
		# unité écrasée qu'on désactiverait disparaîtrait sans rien, et le joueur y lirait un
		# bug de pop. Et `crush()` rend FAUX quand une aura protège l'unité : le porteur la
		# protège aussi du choc, mais le chasseur paie quand même sa collision.
		if unit.crush():
			crushed += unit.data.mass
	if crushed <= 0.0:
		return
	var cost := MassRules.crush_damage(crushed, _player.stats.crush_damage_per_mass)
	_player.take_contact_damage(cost)
	player_crushed.emit(crushed, cost)
	# Une trace d'ÉVÉNEMENT, pas de boucle : quelques fois par partie. C'est le seul endroit
	# d'où l'on voit la mécanique tourner — un écrasement ne laisse rien à l'écran une fois
	# l'explosion passée, et l'équilibrage se lit au journal.
	print("[Combat] ecrase %.1f t — %.0f de bouclier" % [crushed, cost])

## Verse les unités qui sont des OBSTACLES — celles qu'on ne peut pas écraser.
func fill_solids(shapes: PlaneShapes) -> void:
	if _player == null or _player.stats == null:
		return
	var mass: float = _player.stats.mass
	var ratio: float = _player.stats.crush_mass_ratio
	shapes.reserve(shapes.size() + _units.size())
	for unit in _units:
		if not unit.active or unit.data == null or not unit.data.solid:
			continue
		if MassRules.crushes(mass, unit.data.mass, ratio):
			continue
		shapes.add_disc(unit.plane_position, unit.data.hitbox_radius)

## PARLER. ⚠️ UNE RÉPLIQUE A UNE VOIX, et c'est une loi parce que l'oublier ne se voit nulle
## part : le panneau s'affiche, le texte défile, et le silence passe pour un choix. Le niveau 2
## a été joué muet pour cette seule raison — la ligne qui joue la cue était dans le script du
## niveau 1.
func say(script: DialogueScript, key: StringName) -> void:
	if script == null:
		return
	var line := script.find(key)
	if line == null:
		# Une réplique qui ne part pas ne se voit nulle part : sept d'entre elles sont restées
		# muettes une soirée entière, fichiers en place, sans une ligne au journal.
		print("[Lyra] cle inconnue : %s" % key)
	else:
		print("[Lyra] %s" % key)
	if _hud != null and _hud.has_method("say"):
		_hud.say(line)
	if line != null and line.voice_cue != &"":
		sfx(line.voice_cue)

# ==========================================================================
# Les deux gestes de base
# ==========================================================================

func boom(world_position: Vector3, category: VfxExplosion.Category, trauma: float) -> void:
	if _vfx != null:
		_vfx.spawn_explosion(world_position, category)
	if _camera != null and _camera.has_method("add_trauma"):
		_camera.add_trauma(trauma)

func sfx(cue: StringName, volume_db: float = 0.0) -> void:
	if _audio != null and _audio.has_method("play"):
		_audio.play(cue, volume_db)
