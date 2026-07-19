class_name PickupManager
extends Node3D
## Pools pickups and rolls semi-deterministic drops (spec §10.3): guarantees a
## Power Core cadence so the player reliably powers up, with occasional shields
## and score prisms. Applies effects on collection.

const _POOL_SIZE := 16
## Drop on roughly every Nth kill. Raised with the denser waves so bonuses stay
## rare (operator feedback) rather than flooding the field.
const _DROP_EVERY := 4
## Guarantee a Power Core every Nth drop until max power (spec §10.3 guarantee).
const _POWER_EVERY := 3

signal picked_up(kind: Pickup.Kind, world_position: Vector3)

@export var player_path: NodePath

var _player: PlayerFighterController
var _game_state: Node
var _pool: Array[Pickup] = []
var _free: Array[Pickup] = []
var _drop_count: int = 0
var _rng_index: int = 0
var _text_pool: Array[FloatingText] = []
var _text_free: Array[FloatingText] = []
# Fixed, deterministic non-power drop cycle (no Math.random dependency).
const _CYCLE: Array = [Pickup.Kind.SHIELD, Pickup.Kind.SCORE, Pickup.Kind.SHIELD]

## Floating word popped at the pickup on collect (operator feedback).
const _TEXT_POOL_SIZE := 8
const _WORD: Dictionary = {
	Pickup.Kind.POWER: "POWER UP",
	Pickup.Kind.SHIELD: "SHIELD +",
	Pickup.Kind.SCORE: "+500",
}
const _WORD_COLOR: Dictionary = {
	Pickup.Kind.POWER: Color(0.894, 0.71, 0.29),
	Pickup.Kind.SHIELD: Color(0.247, 0.851, 0.91),
	Pickup.Kind.SCORE: Color(0.93, 0.93, 0.88),
}

func _ready() -> void:
	_player = get_node_or_null(player_path) as PlayerFighterController
	_game_state = get_node_or_null("/root/GameState")
	for i in _POOL_SIZE:
		var p := Pickup.new()
		add_child(p)
		p.setup(_player)
		p.collected.connect(_on_collected)
		_pool.append(p)
		_free.append(p)
	for i in _TEXT_POOL_SIZE:
		var label := FloatingText.new()
		add_child(label)
		label.finished.connect(_on_text_finished)
		_text_pool.append(label)
		_text_free.append(label)

## Roll a drop at a world position (called on enemy death). Not every kill drops.
func roll_drop(world_position: Vector3) -> void:
	_drop_count += 1
	if _drop_count % _DROP_EVERY != 0:
		return
	var kind: Pickup.Kind
	if (_drop_count / _DROP_EVERY) % _POWER_EVERY == 0:
		kind = Pickup.Kind.POWER
	else:
		kind = _CYCLE[_rng_index % _CYCLE.size()]
		_rng_index += 1
	spawn(kind, GameplayPlane.to_plane(world_position))

func spawn(kind: Pickup.Kind, plane_position: Vector2) -> void:
	if _free.is_empty():
		return
	var p: Pickup = _free.pop_back()
	p.activate(kind, plane_position)

func _on_collected(pickup: Pickup) -> void:
	match pickup.kind:
		Pickup.Kind.POWER:
			if _player != null:
				_player.add_power()
		Pickup.Kind.SHIELD:
			if _player != null:
				_player.restore_shield(35.0)
		Pickup.Kind.SCORE:
			if _game_state != null:
				_game_state.add_score(500)
	picked_up.emit(pickup.kind, pickup.global_position)
	_pop_word(pickup.kind, pickup.global_position)
	if not _free.has(pickup):
		_free.append(pickup)

func _pop_word(kind: Pickup.Kind, world_position: Vector3) -> void:
	if _text_free.is_empty():
		return
	var label: FloatingText = _text_free.pop_back()
	label.pop(_WORD[kind], _WORD_COLOR[kind], world_position)

func _on_text_finished(label: FloatingText) -> void:
	if not _text_free.has(label):
		_text_free.append(label)
