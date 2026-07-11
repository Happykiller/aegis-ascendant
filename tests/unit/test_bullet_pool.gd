extends "res://tests/test_case.gd"
## BulletManager pool behaviour (spec §21.3 budgets, §28.2 object pool).

func _spawn_n(bm: BulletManager, team: int, n: int) -> int:
	var spawned := 0
	for i in n:
		if bm.spawn_bullet(team, Vector2.ZERO, Vector2(0.0, 1.0), 0.1, 1.0, 10.0) != -1:
			spawned += 1
	return spawned

func test_player_budget_is_150() -> void:
	var bm := BulletManager.new()
	assert_eq(_spawn_n(bm, BulletManager.Team.PLAYER, 200), 150, "player budget capped")
	assert_eq(bm.team_count(BulletManager.Team.PLAYER), 150, "player count")
	bm.free()

func test_enemy_budget_is_450() -> void:
	var bm := BulletManager.new()
	assert_eq(_spawn_n(bm, BulletManager.Team.ENEMY, 500), 450, "enemy budget capped")
	bm.free()

func test_total_pool_is_600() -> void:
	var bm := BulletManager.new()
	_spawn_n(bm, BulletManager.Team.PLAYER, 150)
	_spawn_n(bm, BulletManager.Team.ENEMY, 450)
	assert_eq(bm.active_count(), 600, "pool full")
	assert_eq(bm.spawn_bullet(BulletManager.Team.PLAYER, Vector2.ZERO, Vector2.ZERO, 0.1, 1.0, 1.0),
		-1, "601st spawn refused")
	bm.free()

func test_released_index_is_reused() -> void:
	var bm := BulletManager.new()
	var first := bm.spawn_bullet(BulletManager.Team.PLAYER, Vector2.ZERO, Vector2.ZERO, 0.1, 1.0, 10.0)
	bm.despawn(first)
	assert_eq(bm.active_count(), 0, "pool empty after despawn")
	var second := bm.spawn_bullet(BulletManager.Team.PLAYER, Vector2.ZERO, Vector2.ZERO, 0.1, 1.0, 10.0)
	assert_eq(second, first, "freed index reused")
	bm.free()

func test_despawn_frees_team_budget() -> void:
	var bm := BulletManager.new()
	_spawn_n(bm, BulletManager.Team.PLAYER, 150)
	bm.despawn(0)
	assert_eq(_spawn_n(bm, BulletManager.Team.PLAYER, 5), 1, "one slot reopened")
	bm.free()
