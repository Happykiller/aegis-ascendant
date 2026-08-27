extends "res://tests/test_case.gd"
## L'écrasement sur des unités RÉELLES : le pool, les coques livrées, la mort qui compte.
##
## ⚠️ CE QUE L'ARITHMÉTIQUE SEULE NE PEUT PAS ATTRAPER (et `test_mass_rules.gd` s'arrête là).
## Trois façons de casser la mécanique sans qu'une seule règle de masse soit fausse :
##
## 1. **Verser quand même la coque** dans les obstacles : l'unité est écrasée ET reste un
##    mur. Le chasseur la tue en la percutant, puis reste bloqué sur un cadavre.
## 2. **Écraser sans passer par la mort normale** : l'unité disparaît sans score, sans
##    explosion et sans bruit. En jeu ça ne ressemble pas à une collision, ça ressemble à
##    un bug de pop — c'est le défaut que `EnemyController.crush()` existe pour éviter.
## 3. **Écraser à côté** : une portée mal composée (rayon de l'unité oublié, demi-longueur
##    du chasseur ignorée) broie les unités qu'on frôle ou laisse passer celles qu'on
##    percute. Aucune erreur, juste un jeu qui ment.

const SpawnerScript := preload("res://scripts/gameplay/wave_spawner.gd")
const SCOUT := preload("res://scenes/enemies/needle_scout.tscn")
const CARRIER := preload("res://scenes/enemies/shield_carrier.tscn")
const PLAYER_STATS := preload("res://resources/player/specter9_stats.tres")

## Le chasseur, tel qu'il est réglé : c'est lui qui décide de ce qui est traversable.
func _mass() -> float:
	return PLAYER_STATS.mass

func _ratio() -> float:
	return PLAYER_STATS.crush_mass_ratio

## Un semeur NON monté dans l'arbre — donc sans `_ready()`, sans vague et sans pool — dont
## on remplit la réserve à la main. C'est la seule façon d'exercer `fill_solids()` et
## `crush_contacts()` sur de vraies coques sans monter un niveau entier.
func _spawner() -> WaveSpawner:
	return track(SpawnerScript.new()) as WaveSpawner

## Une unité vivante, posée où on la veut, MONTÉE À LA MAIN.
##
## ⚠️ IL N'Y A PAS D'ARBRE ICI, et c'est ce qui rend ces trois lignes nécessaires. Le runner
## exécute tout dans son `_init()` : `Engine.get_main_loop()` est encore nul, donc aucun
## `add_child()` ne peut déclencher le `_ready()` d'une coque — et sans `_ready()`, ses
## `@onready` (dont sa santé) restent nuls et l'unité ne peut pas mourir.
##
## On notifie donc soi-même, ENFANTS D'ABORD puis le nœud : `propagate_notification()`
## verrouille la fratrie pendant sa descente, et une coque qui monte sa plume dans son
## `_ready()` se voit refuser son `add_child()` — une erreur bruyante pour un test vert.
##
## Le chemin du gestionnaire de balles est effacé avant : il désigne un frère (`PlayerBullets`)
## qui n'existe que dans le niveau.
func _unit(spawner: WaveSpawner, scene: PackedScene, at: Vector2) -> EnemyController:
	var enemy := track(scene.instantiate()) as EnemyController
	enemy.bullet_manager_path = NodePath()
	_notify_ready(enemy)
	enemy.activate(at)
	spawner._pool.append(enemy)
	return enemy

func _notify_ready(node: Node) -> void:
	for child in node.get_children():
		_notify_ready(child)
	node.notification(Node.NOTIFICATION_READY)

# --- Ce qui est versé comme obstacle, et ce qui ne l'est pas ------------------

func test_a_scout_is_no_longer_a_wall() -> void:
	var spawner := _spawner()
	_unit(spawner, SCOUT, Vector2(0.0, 0.0))
	var shapes := PlaneShapes.new()
	spawner.fill_solids(shapes, _mass(), _ratio())
	assert_eq(shapes.size(), 0,
		"un eclaireur ne doit plus etre verse dans les obstacles du niveau")

func test_the_carrier_is_still_a_wall() -> void:
	var spawner := _spawner()
	_unit(spawner, CARRIER, Vector2(0.0, 0.0))
	var shapes := PlaneShapes.new()
	spawner.fill_solids(shapes, _mass(), _ratio())
	assert_eq(shapes.size(), 1, "le porteur de bouclier reste un corps")

func test_without_a_crusher_everything_is_a_wall_again() -> void:
	# Le mode sans joueur et les tests d'avant la masse doivent retrouver la règle d'avant.
	var spawner := _spawner()
	_unit(spawner, SCOUT, Vector2(0.0, 0.0))
	var shapes := PlaneShapes.new()
	spawner.fill_solids(shapes)
	assert_eq(shapes.size(), 1, "sans ecraseur, l'eclaireur redevient un obstacle")

# --- L'écrasement lui-même ---------------------------------------------------

func test_a_touched_scout_dies_and_is_billed() -> void:
	var spawner := _spawner()
	var scout := _unit(spawner, SCOUT, Vector2(0.0, 0.3))
	var killed := [null]
	scout.destroyed.connect(func(unit: EnemyController) -> void: killed[0] = unit)
	var crushed := spawner.crush_contacts(Vector2.ZERO, Vector2(0.0, 1.0),
		PLAYER_STATS.body_half_length, PLAYER_STATS.body_radius, _mass(), _ratio())
	assert_almost_eq(crushed, scout.data.mass, 0.001,
		"la masse broyee est facturee au chasseur")
	assert_false(scout.active, "l'eclaireur percute est mort")
	# ⚠️ LE POINT 2 : il meurt par le chemin normal, donc le niveau apprend sa mort et lui
	# donne son score et son explosion. Une disparition muette serait un bug de pop.
	assert_true(killed[0] == scout, "`destroyed` a bien ete emis — score et explosion")

func test_a_distant_scout_is_left_alone() -> void:
	var spawner := _spawner()
	var scout := _unit(spawner, SCOUT, Vector2(6.0, 0.0))
	var crushed := spawner.crush_contacts(Vector2.ZERO, Vector2(0.0, 1.0),
		PLAYER_STATS.body_half_length, PLAYER_STATS.body_radius, _mass(), _ratio())
	assert_almost_eq(crushed, 0.0, 0.001, "rien n'est broye a six unites de distance")
	assert_true(scout.active, "et l'eclaireur est toujours en vie")

## La portée exacte, mesurée sur les valeurs livrées : une unité juste au contact du nez du
## chasseur est écrasée ; la même, un demi-mètre plus loin, ne l'est pas.
func test_the_reach_is_the_hull_and_nothing_more() -> void:
	var half: float = PLAYER_STATS.body_half_length
	var radius: float = PLAYER_STATS.body_radius
	var scout_radius: float = load("res://resources/enemies/needle_scout.tres").hitbox_radius
	var contact := half + radius + scout_radius
	var spawner := _spawner()
	var touching := _unit(spawner, SCOUT, Vector2(0.0, contact - 0.05))
	var clear := _unit(spawner, SCOUT, Vector2(0.0, contact + 0.5))
	spawner.crush_contacts(Vector2.ZERO, Vector2(0.0, 1.0), half, radius,
		_mass(), _ratio())
	assert_false(touching.active, "l'unite au contact du nez est ecrasee")
	assert_true(clear.active, "celle qui est au-dela ne l'est pas")

func test_the_carrier_survives_being_rammed() -> void:
	# La contrepartie du blocage : ce qui arrête le chasseur ne doit pas mourir du choc.
	var spawner := _spawner()
	var carrier := _unit(spawner, CARRIER, Vector2(0.0, 0.5))
	var crushed := spawner.crush_contacts(Vector2.ZERO, Vector2(0.0, 1.0),
		PLAYER_STATS.body_half_length, PLAYER_STATS.body_radius, _mass(), _ratio())
	assert_almost_eq(crushed, 0.0, 0.001, "on ne broie pas ce qui nous arrete")
	assert_true(carrier.active, "le porteur de bouclier encaisse le choc")

## ⚠️ LE POINT 1, ET C'EST L'INVARIANT CENTRAL : aucune unité ne peut être à la fois un
## obstacle et une proie. Une seule qui le serait rendrait le chasseur prisonnier d'un
## cadavre — exactement la plainte qu'on prétend corriger.
func test_no_unit_is_both_a_wall_and_a_prey() -> void:
	var spawner := _spawner()
	var scout := _unit(spawner, SCOUT, Vector2(0.0, 0.3))
	var carrier := _unit(spawner, CARRIER, Vector2(3.0, 0.3))
	var shapes := PlaneShapes.new()
	spawner.fill_solids(shapes, _mass(), _ratio())
	var walls := shapes.size()
	var crushed := spawner.crush_contacts(Vector2.ZERO, Vector2(0.0, 1.0),
		PLAYER_STATS.body_half_length, PLAYER_STATS.body_radius, _mass(), _ratio())
	assert_eq(walls, 1, "seul le porteur est un mur")
	assert_almost_eq(crushed, scout.data.mass, 0.001, "seul l'eclaireur est une proie")
	assert_true(carrier.active, "et le mur est intact")
