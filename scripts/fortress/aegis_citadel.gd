class_name AegisCitadel
extends Node3D
## The friendly mobile fortress (spec §3.3, §15.4). Appears for the docking
## sequence (spec §6.5) and becomes the player-controlled body in the fortress
## phase (spec §12). A 3D hull (ADR-0008) sitting on the play plane.

signal arrived

@export var hull_scene: PackedScene
## Pièces mobiles, instanciées sur les marqueurs de la coque (BRIEF-0032). Elles
## sont des modèles SÉPARÉS et non des nœuds du `.glb` : le kit Blender n'exporte
## qu'un seul objet maillé, et le rendre multi-parties toucherait la validation de
## contrat et les six scripts de coque existants. Les marqueurs, eux, existaient
## déjà. Laisser ces champs vides dégrade proprement : la citadelle reste figée.
## L'animation elle-même vit dans `CitadelLife` — l'écran d'accueil instancie le
## `.glb` nu et n'a pas de contrôleur, il lui faut la même fabrique.
@export var turret_scene: PackedScene
@export var beacon_scene: PackedScene

var plane_position: Vector2 = Vector2(0.0, 20.0)
var _slide_target: Vector2 = Vector2(0.0, 20.0)
var _slide_speed: float = 0.0
var _sliding: bool = false
var _hull: Node3D
## Mouth of the docking bay, in plane coordinates relative to the hull's origin.
var _bay_offset: Vector2 = Vector2(0.0, -3.0)
## Plane-space offset (model units) of each heavy rail battery, read from the hull.
var _battery_offsets: Array[Vector2] = []

func _ready() -> void:
	if hull_scene != null:
		_hull = hull_scene.instantiate() as Node3D
		add_child(_hull)
		var entry := _hull.get_node_or_null("Dock_Entry") as Node3D
		if entry != null:
			_bay_offset = Vector2(entry.position.x, -entry.position.z)
		else:
			push_error("[AegisCitadel] hull has no 'Dock_Entry' attach point")
		for battery_name in ["Muzzle_Battery_L", "Muzzle_Battery_R"]:
			var node := _hull.get_node_or_null(battery_name) as Node3D
			if node != null:
				_battery_offsets.append(Vector2(node.position.x, -node.position.z))
			else:
				push_error("[AegisCitadel] hull has no '%s' attach point" % battery_name)
		CitadelLife.apply(_hull, turret_scene, beacon_scene)
	position = GameplayPlane.to_world(plane_position)
	set_physics_process(false)

## Docking bay mouth in plane coordinates, taken from the hull's own attach point.
func bay_position() -> Vector2:
	return plane_position + _bay_offset

## Firing point of a heavy rail battery (0 = port, 1 = starboard), in plane
## coordinates, taken from the hull's own muzzle and scaled with the fortress
## (it shrinks for the fortress phase). Falls back to the origin if unbaked.
func battery_origin(index: int) -> Vector2:
	if _battery_offsets.is_empty():
		return plane_position
	return plane_position + _battery_offsets[index % _battery_offsets.size()] * scale.x

func slide_to(target: Vector2, speed: float) -> void:
	_slide_target = target
	_slide_speed = speed
	_sliding = true
	set_physics_process(true)

func _physics_process(delta: float) -> void:
	if not _sliding:
		return
	plane_position = plane_position.move_toward(_slide_target, _slide_speed * delta)
	position = GameplayPlane.to_world(plane_position)
	if plane_position.distance_to(_slide_target) < 0.05:
		_sliding = false
		set_physics_process(false)
		arrived.emit()
