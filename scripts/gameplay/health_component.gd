class_name HealthComponent
extends Node
## Composable health (spec §20.1: composition, signals for events).
## Pure logic — instantiable by hand in headless tests.

signal damaged(amount: float, remaining: float)
signal died

@export var max_health: float = 30.0

var health: float

func _init() -> void:
	health = max_health

func _ready() -> void:
	health = max_health

func apply_damage(amount: float) -> void:
	if health <= 0.0:
		return
	var applied := minf(amount, health)
	health -= applied
	damaged.emit(applied, health)
	if health <= 0.0:
		died.emit()

func revive() -> void:
	health = max_health
