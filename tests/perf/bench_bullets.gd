extends SceneTree
## BulletManager benchmark (spec §25.3: gameplay CPU < 2.0 ms/frame).
## Full pool (150 player + 450 enemy bullets) + 20 registered targets,
## 3600 simulated steps (60 s at 60 Hz). Bullets are laid out so no hit or
## cull ever fires: the load stays at 600 for the whole run.
## Run: godot4 --headless --path . --script res://tests/perf/bench_bullets.gd

const STEPS := 3600
const DELTA := 1.0 / 60.0
const BUDGET_MS := 2.0

func _init() -> void:
	var bm := BulletManager.new()
	_fill_pool(bm)
	_register_targets(bm)
	if bm.active_count() != BulletManager.MAX_BULLETS:
		printerr("[bench] setup failed: %d bullets active" % bm.active_count())
		quit(1)
		return

	var total_usec := 0
	var max_usec := 0
	for i in STEPS:
		var t0 := Time.get_ticks_usec()
		bm.step(DELTA)
		var dt := Time.get_ticks_usec() - t0
		total_usec += dt
		max_usec = maxi(max_usec, dt)

	var stable := bm.active_count() == BulletManager.MAX_BULLETS
	var avg_ms := total_usec / float(STEPS) / 1000.0
	var max_ms := max_usec / 1000.0
	print("[bench] %d steps, %d bullets, 20 targets" % [STEPS, bm.active_count()])
	print("[bench] step avg: %.3f ms — max: %.3f ms — budget: %.1f ms" % [avg_ms, max_ms, BUDGET_MS])
	if not stable:
		printerr("[bench] load not stable (bullets were lost during the run)")
	bm.free()
	quit(0 if avg_ms < BUDGET_MS and stable else 1)

## 600 motionless bullets on a 30x20 grid inside the bounds (integration and
## grid insertion costs are identical to moving bullets).
func _fill_pool(bm: BulletManager) -> void:
	var spawned := 0
	for row in 20:
		for col in 30:
			var team := BulletManager.Team.PLAYER if spawned < 150 else BulletManager.Team.ENEMY
			var pos := Vector2(-11.0 + col * (22.0 / 29.0), -6.0 + row * (12.0 / 19.0))
			bm.spawn_bullet(team, pos, Vector2.ZERO, 0.1, 10.0, 999999.0)
			spawned += 1

## 20 targets along the top margin, far enough from every bullet row that no
## hit triggers, but inside the grid so neighborhood scans run for real.
func _register_targets(bm: BulletManager) -> void:
	for i in 20:
		var target := BulletTarget.make(BulletManager.Team.PLAYER, 0.3, func(_damage: float) -> void: pass)
		target.position = Vector2(-11.0 + i * (22.0 / 19.0), 6.8)
		bm.register_target(target)
