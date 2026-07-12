class_name BulletManager
extends Node3D
## Data-oriented projectile system (spec §21).
## All buffers are preallocated in _init(); nothing allocates during gameplay.
## Logic lives in step(delta) — separate from _physics_process so headless
## tests can drive it directly (no MultiMesh needed: rendering is skipped when
## the node is not inside a scene with its MultiMeshInstance3D children).

enum Team { PLAYER = 0, ENEMY = 1 }

## A bullet connected. `victim_team` is the team that was *hit*, so a listener can
## colour the impact by side. The hit callback only carries damage, which is all
## the victim needs — but nothing else knew where the hit landed, so there was no
## way to draw it.
signal target_hit(plane_position: Vector2, victim_team: int)

const MAX_BULLETS := 600                       # spec §21.3 hard budget
const TEAM_BUDGETS: PackedInt32Array = [150, 450]  # player / enemy sub-budgets
const CULL_MARGIN := 2.0                       # units beyond BOUNDS before culling

## Fixed-capacity flat spatial grid over BOUNDS.grow(CULL_MARGIN).
const GRID_COLS := 12
const GRID_ROWS := 8
const CELL_CAP := 32

var _positions: PackedVector2Array
var _velocities: PackedVector2Array
var _radii: PackedFloat32Array
var _damages: PackedFloat32Array
var _ttls: PackedFloat32Array
var _teams: PackedInt32Array
var _alive: PackedByteArray
var _free_stack: PackedInt32Array
var _free_top: int = 0
var _team_counts: PackedInt32Array
var _visible_counts: PackedInt32Array
var _grid_counts: PackedInt32Array
var _grid_data: PackedInt32Array
var _grid_overflows: int = 0
var _grid_origin: Vector2
var _cell_size: Vector2
var _targets: Array[BulletTarget] = []
## Set while walking _targets, so a hit callback that unregisters its own target
## defers the erase instead of mutating the array under the loop.
var _resolving: bool = false
var _pending_unregister: Array[BulletTarget] = []
var _multimeshes: Array[MultiMesh] = []
var _buffers: Array[PackedFloat32Array] = []

func _init() -> void:
	_positions.resize(MAX_BULLETS)
	_velocities.resize(MAX_BULLETS)
	_radii.resize(MAX_BULLETS)
	_damages.resize(MAX_BULLETS)
	_ttls.resize(MAX_BULLETS)
	_teams.resize(MAX_BULLETS)
	_alive.resize(MAX_BULLETS)
	_free_stack.resize(MAX_BULLETS)
	for i in MAX_BULLETS:
		_free_stack[i] = MAX_BULLETS - 1 - i   # pop order: 0, 1, 2, ...
	_free_top = MAX_BULLETS
	_team_counts.resize(2)
	_visible_counts.resize(2)
	_grid_counts.resize(GRID_COLS * GRID_ROWS)
	_grid_data.resize(GRID_COLS * GRID_ROWS * CELL_CAP)
	var grid_bounds := GameplayPlane.BOUNDS.grow(CULL_MARGIN)
	_grid_origin = grid_bounds.position
	_cell_size = grid_bounds.size / Vector2(GRID_COLS, GRID_ROWS)

func _ready() -> void:
	for child_name: String in ["PlayerBullets", "EnemyBullets"]:
		var instance := get_node(child_name) as MultiMeshInstance3D
		var multimesh := instance.multimesh
		multimesh.instance_count = MAX_BULLETS   # once only: reallocates GPU buffers
		multimesh.visible_instance_count = 0
		_multimeshes.append(multimesh)
		# Bulk transform buffer (12 floats/instance): far cheaper than one
		# set_instance_transform() call per bullet each frame. Pre-fill the
		# identity basis once; per frame only the origin (x,z) is rewritten.
		var buffer := PackedFloat32Array()
		buffer.resize(MAX_BULLETS * 12)
		for s in MAX_BULLETS:
			var base := s * 12
			buffer[base] = 1.0       # basis x.x
			buffer[base + 5] = 1.0   # basis y.y
			buffer[base + 10] = 1.0  # basis z.z
		_buffers.append(buffer)

func _physics_process(delta: float) -> void:
	step(delta)

## Spawns a bullet; returns its index, or -1 when the pool or team budget is full.
func spawn_bullet(team: int, pos: Vector2, vel: Vector2, radius: float,
		damage: float, ttl: float) -> int:
	if _free_top == 0 or _team_counts[team] >= TEAM_BUDGETS[team]:
		return -1
	_free_top -= 1
	var i := _free_stack[_free_top]
	_positions[i] = pos
	_velocities[i] = vel
	_radii[i] = radius
	_damages[i] = damage
	_ttls[i] = ttl
	_teams[i] = team
	_alive[i] = 1
	_team_counts[team] += 1
	return i

func spawn_from_data(team: int, pos: Vector2, direction: Vector2, data: ProjectileData) -> int:
	return spawn_bullet(team, pos, direction.normalized() * data.speed,
		data.radius, data.damage, data.ttl)

func despawn(index: int) -> void:
	if _alive[index] == 1:
		_release(index)

func register_target(target: BulletTarget) -> void:
	if not _targets.has(target):
		_targets.append(target)

## Safe to call from a hit callback: the erase is deferred to the end of the pass
## rather than mutating the array mid-iteration. Bosses unregister exactly this
## way, from inside their own hit handler.
func unregister_target(target: BulletTarget) -> void:
	if _resolving:
		if not _pending_unregister.has(target):
			_pending_unregister.append(target)
		return
	_targets.erase(target)

func active_count() -> int:
	return MAX_BULLETS - _free_top

func team_count(team: int) -> int:
	return _team_counts[team]

## Advances every bullet, rebuilds the spatial grid, feeds the MultiMeshes
## (compacted 0..n-1) and resolves circle-circle hits on the logical plane.
func step(delta: float) -> void:
	_grid_counts.fill(0)
	_visible_counts[Team.PLAYER] = 0
	_visible_counts[Team.ENEMY] = 0
	var render := not _multimeshes.is_empty()
	for i in MAX_BULLETS:
		if _alive[i] == 0:
			continue
		_ttls[i] -= delta
		var p := _positions[i] + _velocities[i] * delta
		if _ttls[i] <= 0.0 or not GameplayPlane.is_inside(p, CULL_MARGIN):
			_release(i)
			continue
		_positions[i] = p
		_grid_insert(i, p)
		var team := _teams[i]
		if render:
			# Write only the origin (world x,z) into this team's transform buffer;
			# the identity basis floats were set once in _ready.
			var base := _visible_counts[team] * 12
			_buffers[team][base + 3] = p.x    # origin.x
			_buffers[team][base + 11] = -p.y  # origin.z (world -Z = screen up)
		_visible_counts[team] += 1
	if render:
		for team in 2:
			_multimeshes[team].buffer = _buffers[team]
			_multimeshes[team].visible_instance_count = _visible_counts[team]
	_resolve_hits()

func _release(i: int) -> void:
	_alive[i] = 0
	_team_counts[_teams[i]] -= 1
	_free_stack[_free_top] = i
	_free_top += 1

func _grid_insert(bullet_index: int, p: Vector2) -> void:
	var cell := _cell_of(p)
	var count := _grid_counts[cell]
	if count >= CELL_CAP:
		# Never crash on overflow: the bullet keeps flying but skips hit tests
		# this frame; throttled warning for tuning (spec §21.2).
		_grid_overflows += 1
		if _grid_overflows % 300 == 1:
			push_warning("[BulletManager] grid cell overflow (total: %d)" % _grid_overflows)
		return
	_grid_data[cell * CELL_CAP + count] = bullet_index
	_grid_counts[cell] = count + 1

func _cell_of(p: Vector2) -> int:
	var col := clampi(int((p.x - _grid_origin.x) / _cell_size.x), 0, GRID_COLS - 1)
	var row := clampi(int((p.y - _grid_origin.y) / _cell_size.y), 0, GRID_ROWS - 1)
	return row * GRID_COLS + col

func _resolve_hits() -> void:
	_resolving = true
	for target in _targets:
		if target.enabled:
			_resolve_target(target)
	_resolving = false
	# Unregistrations requested by a hit callback were held back so the loop above
	# never mutated the array it was walking.
	if not _pending_unregister.is_empty():
		for target in _pending_unregister:
			_targets.erase(target)
		_pending_unregister.clear()

## Scan the 3x3 cells around one target.
##
## A hit callback can kill its owner, and a dead entity disables its target. We
## stop the moment that happens: otherwise the rest of the salvo already sitting
## in these cells keeps landing on a corpse, and an entity that reports its death
## from the hit path (the bosses do) reports it once per bullet — which paid the
## boss reward twice and started the docking sequence twice.
func _resolve_target(target: BulletTarget) -> void:
	var col := clampi(int((target.position.x - _grid_origin.x) / _cell_size.x), 0, GRID_COLS - 1)
	var row := clampi(int((target.position.y - _grid_origin.y) / _cell_size.y), 0, GRID_ROWS - 1)
	for dc in 3:
		var c := col + dc - 1
		if c < 0 or c >= GRID_COLS:
			continue
		for dr in 3:
			var r := row + dr - 1
			if r < 0 or r >= GRID_ROWS:
				continue
			var cell := r * GRID_COLS + c
			var count := _grid_counts[cell]
			for k in count:
				var i := _grid_data[cell * CELL_CAP + k]
				if _alive[i] == 0 or _teams[i] == target.team:
					continue
				var reach := _radii[i] + target.radius
				if _positions[i].distance_squared_to(target.position) <= reach * reach:
					target.hit_callback.call(_damages[i])
					target_hit.emit(_positions[i], target.team)
					_release(i)
					if not target.enabled:
						return
