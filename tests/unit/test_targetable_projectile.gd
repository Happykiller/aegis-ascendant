extends "res://tests/test_case.gd"
## TargetableProjectile : le missile que le joueur peut abattre (phase 1 du Leviathan).
## Instanciable a la main — aucun arbre, aucun BulletManager, aucun boss.

var _hits: int = 0

func _on_hit(_damage: float) -> void:
	_hits += 1

func _make(velocity: Vector2 = Vector2(0.0, -4.0), turn_rate: float = 0.0) -> TargetableProjectile:
	_hits = 0
	return TargetableProjectile.make(Vector2(0.0, 4.0), velocity, 40.0, 0.3,
		turn_rate, 22.0, Callable(self, "_on_hit"))

func test_it_registers_on_the_enemy_team() -> void:
	# C'est CE detail qui le rend touchable par les tirs joueur sans toucher au
	# BulletManager : _resolve_target ignore les balles de la meme equipe que la cible.
	var m := _make()
	assert_eq(m.target.team, BulletManager.Team.ENEMY,
		"equipe ENEMY : seules les balles du joueur peuvent le toucher")
	assert_true(m.target.enabled, "et sa cible est active tant qu'il vit")

func test_it_travels_along_its_velocity() -> void:
	var m := _make(Vector2(0.0, -4.0))
	m.tick(0.5, Vector2(0.0, -6.0))
	assert_almost_eq(m.plane_position.y, 2.0, 0.001, "quatre unites par seconde vers le bas")
	assert_almost_eq(m.plane_position.x, 0.0, 0.001, "et pas de derive laterale")

func test_the_bullet_target_follows_the_projectile() -> void:
	# Une cible qui ne suit pas est une cible qu'on ne peut pas viser.
	var m := _make()
	m.tick(0.5, Vector2.ZERO)
	assert_eq(m.target.position, m.plane_position, "la zone de touche suit la position")

func test_homing_turns_toward_the_target_without_gaining_speed() -> void:
	var m := _make(Vector2(0.0, -4.0), 1.4)
	var speed_before := m.velocity.length()
	m.tick(0.2, Vector2(10.0, 0.0))   # cible franchement a tribord
	assert_true(m.velocity.x > 0.0, "la vitesse s'incline vers la cible")
	assert_almost_eq(m.velocity.length(), speed_before, 0.001,
		"virer ne fait pas accelerer : on tourne la vitesse, on ne la remplace pas")

func test_the_turn_is_capped_which_is_what_makes_it_dodgeable() -> void:
	# Un missile qui vire instantanement est un missile qui touche toujours.
	var m := _make(Vector2(0.0, -4.0), 1.0)
	var before := m.velocity.angle()
	m.tick(0.1, Vector2(0.0, 100.0))  # demi-tour complet demande
	var turned := absf(wrapf(m.velocity.angle() - before, -PI, PI))
	assert_true(turned <= 1.0 * 0.1 + 0.001, "au plus turn_rate x delta en un pas")

func test_a_straight_projectile_never_steers() -> void:
	var m := _make(Vector2(0.0, -4.0), 0.0)
	m.tick(0.3, Vector2(10.0, 10.0))
	assert_almost_eq(m.velocity.x, 0.0, 0.001, "turn_rate nul = trajectoire rectiligne")

func test_shooting_it_down_reports_the_kill_exactly_once() -> void:
	# Sinon une salve de quatre traits joue quatre explosions sur le meme missile.
	var m := _make()
	assert_false(m.apply_damage(20.0), "encore debout a mi-vie")
	assert_true(m.apply_damage(20.0), "le frame ou il tombe, et celui-la seulement")
	assert_false(m.apply_damage(20.0), "un projectile mort ne retombe pas")

func test_a_dead_projectile_disables_its_target() -> void:
	# Une cible active sur un projectile eteint est un mur invisible qui mange les
	# balles du joueur.
	var m := _make()
	m.apply_damage(999.0)
	assert_false(m.alive, "abattu")
	assert_false(m.target.enabled, "et sa zone de touche est retiree")

func test_a_dead_projectile_stops_moving() -> void:
	var m := _make()
	m.apply_damage(999.0)
	var resting := m.plane_position
	m.tick(1.0, Vector2.ZERO)
	assert_eq(m.plane_position, resting, "il ne court plus apres sa mort")

func test_it_retires_when_it_leaves_the_plane() -> void:
	var m := _make(Vector2(0.0, -40.0))
	m.tick(1.0, Vector2.ZERO)   # bien au-dela du bord bas
	assert_false(m.alive, "sorti du plan, il est retire")
	assert_false(m.target.enabled, "cible retiree avec lui")

func test_it_survives_a_frame_spent_near_the_edge() -> void:
	# La marge evite qu'un missile ne au bord ne meure a l'image de sa creation.
	var m := TargetableProjectile.make(Vector2(0.0, 7.9), Vector2(0.0, 0.5), 40.0, 0.3,
		0.0, 22.0, Callable(self, "_on_hit"))
	m.tick(0.1, Vector2.ZERO)
	assert_true(m.alive, "juste au bord haut, il vit encore")

func test_reach_uses_both_radii() -> void:
	var m := _make()
	assert_true(m.reaches(Vector2(0.0, 4.4), 0.25), "0,4 d'ecart pour 0,3 + 0,25 de portee")
	assert_false(m.reaches(Vector2(0.0, 5.0), 0.25), "une unite plus loin, il ne touche pas")

func test_a_consumed_projectile_no_longer_reaches_anything() -> void:
	var m := _make()
	m.consume()
	assert_false(m.reaches(m.plane_position, 1.0), "depense, il ne peut plus frapper deux fois")

func test_health_ratio_is_safe_on_a_zero_health_projectile() -> void:
	var m := TargetableProjectile.make(Vector2.ZERO, Vector2.ZERO, 0.0, 0.3, 0.0, 1.0,
		Callable(self, "_on_hit"))
	assert_almost_eq(m.health_ratio(), 0.0, 0.001, "aucune division par zero")
