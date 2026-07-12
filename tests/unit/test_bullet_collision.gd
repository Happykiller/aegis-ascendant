extends "res://tests/test_case.gd"
## BulletManager collision, TTL and culling on the logical plane (spec §21.2).

var _hits: Array[float] = []
var _impacts: Array[Array] = []

func _on_hit(damage: float) -> void:
	_hits.append(damage)

func _on_target_hit(plane_position: Vector2, victim_team: int) -> void:
	_impacts.append([plane_position, victim_team])

func _make_target(team: int, pos: Vector2, radius: float) -> BulletTarget:
	var target := BulletTarget.make(team, radius, Callable(self, "_on_hit"))
	target.position = pos
	return target

func test_enemy_bullet_hits_player_target() -> void:
	var bm := BulletManager.new()
	bm.register_target(_make_target(BulletManager.Team.PLAYER, Vector2.ZERO, 0.3))
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2(0.0, -0.2), Vector2(0.0, 1.0), 0.1, 15.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(_hits.size(), 1, "hit callback fired once")
	assert_almost_eq(_hits[0], 15.0, 0.0001, "damage forwarded")
	assert_eq(bm.active_count(), 0, "bullet released on hit")
	bm.free()

func test_same_team_never_hits() -> void:
	var bm := BulletManager.new()
	bm.register_target(_make_target(BulletManager.Team.PLAYER, Vector2.ZERO, 0.5))
	bm.spawn_bullet(BulletManager.Team.PLAYER, Vector2.ZERO, Vector2.ZERO, 0.2, 10.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(_hits.size(), 0, "no friendly fire")
	assert_eq(bm.active_count(), 1, "bullet still alive")
	bm.free()

func test_disabled_target_ignored() -> void:
	var bm := BulletManager.new()
	var target := _make_target(BulletManager.Team.PLAYER, Vector2.ZERO, 0.5)
	target.enabled = false
	bm.register_target(target)
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2.ZERO, Vector2.ZERO, 0.2, 10.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(_hits.size(), 0, "disabled target not hit")
	bm.free()

func test_far_bullet_does_not_hit() -> void:
	var bm := BulletManager.new()
	bm.register_target(_make_target(BulletManager.Team.PLAYER, Vector2(-10.0, -6.0), 0.3))
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2(10.0, 6.0), Vector2.ZERO, 0.1, 10.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(_hits.size(), 0, "distant bullet misses")
	assert_eq(bm.active_count(), 1, "distant bullet alive")
	bm.free()

## The hit callback only carries damage, so the impact VFX has no other way to
## learn where the hit landed or whose hull took it.
func test_hit_reports_impact_position_and_victim() -> void:
	var bm := BulletManager.new()
	bm.target_hit.connect(_on_target_hit)
	bm.register_target(_make_target(BulletManager.Team.PLAYER, Vector2(2.0, -3.0), 0.4))
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2(2.0, -3.2), Vector2.ZERO, 0.1, 10.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(_impacts.size(), 1, "impact reported once")
	var where: Vector2 = _impacts[0][0]
	assert_true(where.distance_to(Vector2(2.0, -3.2)) < 0.05,
		"impact carries the bullet's position, not the target's (got %s)" % where)
	assert_eq(_impacts[0][1], BulletManager.Team.PLAYER, "victim team is the side that was hit")
	bm.free()

func test_miss_reports_no_impact() -> void:
	var bm := BulletManager.new()
	bm.target_hit.connect(_on_target_hit)
	bm.register_target(_make_target(BulletManager.Team.PLAYER, Vector2(-10.0, -6.0), 0.3))
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2(10.0, 6.0), Vector2.ZERO, 0.1, 10.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(_impacts.size(), 0, "a miss draws nothing")
	bm.free()

## Regression: a boss died twice. Two bullets landing on the same frame both
## reached the hit callback — the first killed it, the second found health already
## at zero and ran the defeat path again, paying the reward and starting the
## docking sequence twice. A target that goes cold mid-pass must stop absorbing.
var _lethal_target: BulletTarget
var _lethal_hits: int = 0
var _lethal_bm: BulletManager

func _on_lethal_hit(_damage: float) -> void:
	_lethal_hits += 1
	# What a dying entity does: disable, then unregister from inside the callback.
	_lethal_target.enabled = false
	_lethal_bm.unregister_target(_lethal_target)

func test_dead_target_absorbs_no_further_bullets_this_frame() -> void:
	_lethal_bm = BulletManager.new()
	_lethal_target = BulletTarget.make(BulletManager.Team.ENEMY, 0.8, Callable(self, "_on_lethal_hit"))
	_lethal_target.position = Vector2.ZERO
	_lethal_bm.register_target(_lethal_target)
	for i in 4: # a whole salvo arriving together
		_lethal_bm.spawn_bullet(BulletManager.Team.PLAYER,
			Vector2(-0.3 + 0.2 * i, 0.0), Vector2.ZERO, 0.1, 10.0, 5.0)
	_lethal_bm.step(1.0 / 60.0)
	assert_eq(_lethal_hits, 1, "the killing blow lands once, not once per bullet")
	assert_eq(_lethal_bm.active_count(), 3, "the rest of the salvo flies on through")
	_lethal_bm.free()

func test_ttl_expiry_releases_bullet() -> void:
	var bm := BulletManager.new()
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2.ZERO, Vector2.ZERO, 0.1, 10.0, 0.05)
	bm.step(0.1)
	assert_eq(bm.active_count(), 0, "expired bullet released")
	bm.free()

func test_out_of_bounds_releases_bullet() -> void:
	var bm := BulletManager.new()
	bm.spawn_bullet(BulletManager.Team.PLAYER, Vector2(0.0, 6.9), Vector2(0.0, 50.0), 0.1, 10.0, 10.0)
	bm.step(0.25) # -> y = 19.4, far beyond BOUNDS.end.y + CULL_MARGIN
	assert_eq(bm.active_count(), 0, "out-of-bounds bullet culled")
	bm.free()
