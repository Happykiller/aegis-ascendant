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

var _clock: float = 0.0
var _next_spawn: int = 0
var _spawn_times: PackedFloat32Array
var _spawn_positions: PackedVector2Array
var _pool: Array[EnemyController] = []
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
	var schedule := build_schedule(wave)
	_spawn_times = schedule["times"]
	_spawn_positions = schedule["positions"]
	var entry_indices: PackedInt32Array = schedule["entries"]
	for k in _spawn_times.size():
		var entry := wave.entries[entry_indices[k]]
		var enemy := entry.enemy_scene.instantiate() as EnemyController
		add_child(enemy)               # _ready runs now: enemy starts deactivated
		enemy.setup(bullet_manager)
		_pool.append(enemy)
	print("[WaveSpawner] pool ready: %d enemies" % _pool.size())

## Pure scheduling, testable headless: flattens entries into per-enemy spawn
## times/positions, sorted by time. Returns {times, positions, entries}.
static func build_schedule(wave_data: WaveData) -> Dictionary:
	var events: Array = []
	for entry_index in wave_data.entries.size():
		var entry := wave_data.entries[entry_index]
		for n in entry.count:
			events.append([entry.time_offset + n * entry.spacing, entry_index])
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
	var spawned := _next_spawn
	while _next_spawn < _spawn_times.size() and _clock >= _spawn_times[_next_spawn]:
		_pool[_next_spawn].activate(_spawn_positions[_next_spawn])
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
	print("[WaveSpawner] wave_cleared")
	wave_cleared.emit()
