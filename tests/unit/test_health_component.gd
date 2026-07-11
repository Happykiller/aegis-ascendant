extends "res://tests/test_case.gd"
## HealthComponent damage/death behaviour (spec §28.2).

var _died_count := 0
var _damage_events: Array[float] = []

func _on_died() -> void:
	_died_count += 1

func _on_damaged(amount: float, _remaining: float) -> void:
	_damage_events.append(amount)

func _make_health(max_health: float) -> HealthComponent:
	var health := HealthComponent.new()
	health.max_health = max_health
	health.revive()
	health.died.connect(_on_died)
	health.damaged.connect(_on_damaged)
	return health

func test_damage_accumulates() -> void:
	var health := _make_health(30.0)
	health.apply_damage(10.0)
	health.apply_damage(5.0)
	assert_almost_eq(health.health, 15.0, 0.0001, "30 - 10 - 5 = 15")
	assert_eq(_died_count, 0, "still alive")
	health.free()

func test_died_emitted_once_at_zero() -> void:
	var health := _make_health(20.0)
	health.apply_damage(20.0)
	assert_eq(_died_count, 1, "died emitted at exactly 0")
	health.apply_damage(10.0)
	assert_eq(_died_count, 1, "no double death")
	health.free()

func test_health_never_negative() -> void:
	var health := _make_health(10.0)
	health.apply_damage(999.0)
	assert_almost_eq(health.health, 0.0, 0.0001, "clamped at 0")
	assert_almost_eq(_damage_events[0], 10.0, 0.0001, "applied damage capped at remaining health")
	health.free()

func test_revive_restores_max() -> void:
	var health := _make_health(25.0)
	health.apply_damage(25.0)
	health.revive()
	assert_almost_eq(health.health, 25.0, 0.0001, "revived to max")
	health.free()
