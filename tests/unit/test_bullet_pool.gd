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

# --- Vidage à la mort du joueur ---------------------------------------------

func test_clearing_a_team_frees_only_that_team() -> void:
	# ⚠️ LE GARDE-FOU CONTRE LA MORT EN CHAÎNE. Le chasseur renaît 1,2 s après sa mort, au
	# centre bas, avec 2 s d'invulnérabilité — mais tout ce qui volait vole encore. On vide
	# donc l'écran des tirs ENNEMIS à sa mort, et d'eux seuls : ses propres balles n'ont
	# jamais tué personne, et les faire disparaître ne protégerait de rien.
	var bm := BulletManager.new()
	_spawn_n(bm, BulletManager.Team.ENEMY, 5)
	_spawn_n(bm, BulletManager.Team.PLAYER, 3)
	assert_eq(bm.active_count(), 8, "huit balles en vol")
	assert_eq(bm.clear_team(BulletManager.Team.ENEMY), 5, "cinq balles ennemies tombent")
	assert_eq(bm.active_count(), 3, "les tirs du joueur restent")
	assert_eq(bm.team_count(BulletManager.Team.PLAYER), 3, "et ils restent comptés")
	assert_eq(bm.clear_team(BulletManager.Team.ENEMY), 0, "vider deux fois ne rend rien")
	bm.free()

func test_a_cleared_slot_goes_back_to_the_pool() -> void:
	# Le vidage passe par la même pile de libération que l'expiration normale. Si elle
	# était corrompue, le pool se tarirait au bout de quelques morts — et le symptôme
	# n'apparaîtrait qu'après plusieurs parties.
	var bm := BulletManager.new()
	_spawn_n(bm, BulletManager.Team.ENEMY, 450)
	assert_eq(bm.clear_team(BulletManager.Team.ENEMY), 450, "le budget entier tombe")
	assert_eq(_spawn_n(bm, BulletManager.Team.ENEMY, 450), 450,
		"et le budget entier se réattribue")
	bm.free()
