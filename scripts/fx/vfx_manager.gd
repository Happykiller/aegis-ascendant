class_name VFXManager
extends Node3D
## Pooled visual effects (spec §26.1: pooling mandatory). Explosions are
## preallocated and reused; nothing is instantiated during gameplay.
## Injected into gameplay nodes; call spawn_explosion() on enemy/structure death.

## Impacts fire far more often than deaths (one per connecting bullet), so the
## pool has to cover a full burst landing on a cluster of enemies.
const _POOL_SIZE := 48

var _explosions: Array[VfxExplosion] = []
var _free: Array[VfxExplosion] = []

func _ready() -> void:
	for i in _POOL_SIZE:
		var fx := VfxExplosion.new()
		add_child(fx)
		fx.finished.connect(_on_finished)
		_explosions.append(fx)
		_free.append(fx)

func spawn_explosion(world_position: Vector3, category: VfxExplosion.Category,
		tint: Color = Color.TRANSPARENT) -> void:
	if _free.is_empty():
		return # pool exhausted: drop the effect rather than allocate (spec §26.2)
	var fx: VfxExplosion = _free.pop_back()
	fx.global_position = world_position
	fx.play(category, tint)

func _on_finished(effect: VfxExplosion) -> void:
	if not _free.has(effect):
		_free.append(effect)
