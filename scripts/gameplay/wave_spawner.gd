class_name WaveSpawner
extends Node
## Executes a WaveData timeline (spec §11.3). All enemies are preinstantiated
## in _ready() as a deactivated pool — zero instantiation during gameplay
## (spec §26.1). Emits wave_cleared when every spawn has been consumed and no
## enemy remains active (killed or flown out).

signal wave_cleared
## How far through the wave's spawn schedule we are, 0 to 1 (drives the music).
signal progress_changed(ratio: float)

@export var wave: WaveData
@export var bullet_manager_path: NodePath
## Le joueur, transmis aux unités qui le REGARDENT (mines, salves visées, puits
## gravitationnels — ADR-0022). Facultatif : laissé vide, la vague se comporte
## exactement comme avant, les trajectoires restant des fonctions du seul âge.
@export var player_path: NodePath
## Une vague qui démarre au montage, ou une vague qui attend son tour. Les deux
## préallouent leur pool dans `_ready()` — c'est la seule chose que la spec §26.1
## exige, et c'est ce qui permet à une SECONDE vague d'exister sans qu'un seul
## `instantiate()` ne tombe pendant la partie (ADR-0027). `false` : le spawner est
## monté, peuplé, et dort jusqu'à `begin()`.
@export var autostart: bool = true

var _clock: float = 0.0
var _next_spawn: int = 0
var _spawn_times: PackedFloat32Array
var _spawn_positions: PackedVector2Array
var _pool: Array[EnemyController] = []

## Indices des unités vivantes, réutilisés d'une image à l'autre. ⚠️ Sans cette liste, la
## passe de séparation parcourrait les 107 entrées du pool à chaque image pour en trouver
## quinze : 5 600 paires au lieu de 105, dans une boucle critique (spec §26.1).
var _live := PackedInt32Array()

## Douceur de la répulsion. À 1,0 deux unités se décollent en une image — ça se voit comme
## un choc. À 0,5 elles glissent l'une contre l'autre, ce qui lit comme une nuée.
const SEPARATION_STRENGTH := 0.5
var _cleared: bool = false

func _ready() -> void:
	# Safe fallback on invalid data (spec §22.2, §31.2): report every problem,
	# then disable the spawner instead of crashing on a null enemy_scene.
	var errors := wave.validate() if wave != null else PackedStringArray(["wave resource is null"])
	if not errors.is_empty():
		for error in errors:
			push_error("[WaveSpawner] invalid wave: %s" % error)
		set_physics_process(false)
		return
	var bullet_manager := get_node(bullet_manager_path) as BulletManager
	var player := get_node_or_null(player_path) as PlayerFighterController
	var schedule := build_schedule(wave)
	_spawn_times = schedule["times"]
	_spawn_positions = schedule["positions"]
	var entry_indices: PackedInt32Array = schedule["entries"]
	for k in _spawn_times.size():
		var entry := wave.entries[entry_indices[k]]
		var enemy := entry.enemy_scene.instantiate() as EnemyController
		add_child(enemy)               # _ready runs now: enemy starts deactivated
		enemy.setup(bullet_manager, player)
		_pool.append(enemy)
	print("[WaveSpawner] pool ready: %d enemies (%s)" % [_pool.size(), name])
	if not autostart:
		set_physics_process(false)

## Démarre une vague montée en veille (`autostart = false`). L'horloge part de zéro
## ici et pas au montage : les `time_offset` de la WaveData se comptent depuis
## l'entrée en phase, pas depuis le début du niveau.
func begin() -> void:
	if _pool.is_empty():
		# La vague n'a pas passé sa validation : l'erreur est déjà remontée dans
		# `_ready()`. On ne bloque pas l'arc dessus — un niveau qui ne s'enchaîne
		# plus cacherait la panne derrière un symptôme sans rapport.
		push_error("[WaveSpawner] begin() on an empty pool: %s" % name)
		wave_cleared.emit()
		return
	set_physics_process(true)

## Pure scheduling, testable headless: flattens entries into per-enemy spawn
## times/positions, sorted by time. Returns {times, positions, entries}.
##
## `lead_in` s'ajoute à TOUTES les dates : c'est un silence d'ouverture, pas un retard
## sur la première entrée. Le reste de la vague garde son rythme intact.
static func build_schedule(wave_data: WaveData) -> Dictionary:
	var events: Array = []
	for entry_index in wave_data.entries.size():
		var entry := wave_data.entries[entry_index]
		for n in entry.count:
			events.append([wave_data.lead_in + entry.time_offset + n * entry.spacing, entry_index])
	events.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	var times := PackedFloat32Array()
	var positions := PackedVector2Array()
	var entries := PackedInt32Array()
	for event: Array in events:
		times.append(event[0])
		positions.append(wave_data.entries[event[1]].spawn_plane_position)
		entries.append(event[1])
	return {"times": times, "positions": positions, "entries": entries}

func _physics_process(delta: float) -> void:
	_clock += delta
	_separate()
	var spawned := _next_spawn
	while _next_spawn < _spawn_times.size() and _clock >= _spawn_times[_next_spawn]:
		# La graine de dérive suit le RANG d'apparition : deux ennemis successifs d'une
		# même nuée reçoivent les phases les plus éloignées possible (`OrganicDrift`).
		_pool[_next_spawn].activate(_spawn_positions[_next_spawn],
			OrganicDrift.seed_for(_next_spawn))
		_next_spawn += 1
	if _next_spawn != spawned:
		progress_changed.emit(float(_next_spawn) / float(_spawn_times.size()))
	if _cleared or _next_spawn < _spawn_times.size():
		return
	for enemy in _pool:
		if enemy.active:
			return
	_cleared = true
	set_physics_process(false)
	# Le niveau porte DEUX vagues (ADR-0027) : sans le nom du nœud, le journal ne dit
	# pas laquelle vient de se clore.
	print("[WaveSpawner] wave_cleared (%s)" % name)
	wave_cleared.emit()


# --- Loi « les corps ne se chevauchent pas » (lot 3) ---------------------------

## Écarte les unités qui se chevauchent, doucement et RÉCIPROQUEMENT.
##
## ⚠️ CHACUNE PREND LA MOITIÉ, contrairement au chasseur contre un boss, où seul le chasseur
## cède. Entre pairs, faire céder une seule des deux ferait passer la nuée pour un tas de
## billes poussées par la dernière arrivée ; à parts égales, elle se dénoue.
##
## La répulsion est SOUPLE et amortie (voir `EnemyController._separation`) : les figures
## écrites survivent, les unités y reviennent dès qu'elles sont libres. Un empilement de
## trois unités au même pixel était le défaut le plus visible du jeu, et le moins cher à
## corriger — il ne demandait pas une collision dure.
func _separate() -> void:
	_live.clear()
	for i in _pool.size():
		if _pool[i].active:
			_live.append(i)
	for a in _live.size():
		var first := _pool[_live[a]]
		for b in range(a + 1, _live.size()):
			var second := _pool[_live[b]]
			var offset := second.plane_position - first.plane_position
			var distance := offset.length()
			var wanted := first.body_radius() + second.body_radius()
			if distance >= wanted:
				continue
			# Deux unités exactement superposées n'ont aucune direction : on les sépare
			# le long d'un axe arbitraire mais STABLE, sinon elles frémiraient sur place.
			var away := offset / distance if distance > 0.0001 else Vector2(1.0, 0.0)
			var push := away * ((wanted - distance) * 0.5 * SEPARATION_STRENGTH)
			first.nudge(-push)
			second.nudge(push)

## Verse les coques qui sont des CORPS. Une unité dont le contact EST l'attaque — mine,
## sangsue, gueule — n'en est pas une : l'arrêter la désamorcerait (voir `EnemyData.solid`).
func fill_solids(shapes: PlaneShapes) -> void:
	for enemy in _pool:
		if enemy.active and enemy.data != null and enemy.data.solid:
			shapes.add_disc(enemy.plane_position, enemy.data.hitbox_radius)

## Majorant du nombre de formes versées — pour dimensionner UNE fois.
func solid_capacity() -> int:
	return _pool.size()
