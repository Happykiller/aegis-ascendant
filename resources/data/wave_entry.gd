class_name WaveEntry
extends Resource
## One timed group of identical enemies inside a wave (spec §11.3).

## Seconds after wave start when the first enemy of this entry spawns.
@export var time_offset: float = 0.0
@export var enemy_scene: PackedScene
## Spawn point on the logical plane (usually just above the top edge).
@export var spawn_plane_position: Vector2 = Vector2(0.0, 8.5)
## Number of enemies, spawned `spacing` seconds apart.
@export var count: int = 1
@export var spacing: float = 0.7

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if enemy_scene == null:
		errors.append("enemy_scene is required")
	if count < 1:
		errors.append("count must be >= 1")
	if spacing < 0.0:
		errors.append("spacing must be >= 0")
	if time_offset < 0.0:
		errors.append("time_offset must be >= 0")
	return errors
