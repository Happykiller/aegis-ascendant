class_name CitadelLife
extends Node
## Donne vie à une coque de citadelle : pièces mobiles sur ses marqueurs, et
## respiration de ses émissifs.
##
## POURQUOI UNE FABRIQUE, ET PAS DU CODE DANS `aegis_citadel.gd` — l'écran d'accueil
## instancie le `.glb` **nu** (`boot.tscn:87`), pas la scène de gameplay. Une
## animation écrite dans le contrôleur serait donc absente de l'endroit même où la
## forteresse est mise en vedette. Sur le modèle de `HullDetail` et `EngineTrail` :
## une fonction statique appelable de partout, sans instancier de gameplay.
##
## C'est un `Node` — et pas une classe purement statique — parce que la respiration
## a besoin d'un `_process`. Les tourelles et les balises, elles, s'animent seules.

## Amplitude et période de la respiration des émissifs (noyau, chevrons, feux).
## ±10 % : au-delà, une forteresse en veille se met à clignoter comme une alarme.
const BREATH_AMPLITUDE := 0.10
const BREATH_PERIOD := 6.5

const TURRET_COUNT := 6
const BEACON_COUNT := 3

var _turret_scene: PackedScene
var _beacon_scene: PackedScene
var _breath_material: StandardMaterial3D
var _breath_energy: float = 0.0
var _age: float = 0.0

## `hull` : le Node3D instancié du `.glb`, celui qui porte les marqueurs.
## Des scènes nulles dégradent proprement — la citadelle reste figée, elle ne casse pas.
static func apply(hull: Node3D, turret_scene: PackedScene, beacon_scene: PackedScene) -> void:
	if hull == null:
		return
	var life := CitadelLife.new()
	life.name = "CitadelLife"
	life._turret_scene = turret_scene
	life._beacon_scene = beacon_scene
	hull.add_child(life)

func _ready() -> void:
	var hull := get_parent() as Node3D
	if hull == null:
		return
	_populate(hull, "Turret_%02d", TURRET_COUNT, _turret_scene)
	_populate(hull, "Beacon_%02d", BEACON_COUNT, _beacon_scene)
	_bind_breath(hull)
	set_process(_breath_material != null)

## Instancie une pièce mobile sur chaque marqueur `<pattern>` de la coque.
##
## Les marqueurs sont numérotés à partir de 1 côté Blender (`Turret_01`) ; l'index
## passé aux pièces part de 0. C'est lui, et lui seul, qui les désynchronise.
##
## Un marqueur manquant n'est PAS une erreur silencieuse : la coque et le code
## partagent un contrat de noms, et une faute de frappe côté Blender doit se voir.
func _populate(hull: Node3D, pattern: String, count: int, scene: PackedScene) -> void:
	if scene == null:
		return
	for i in count:
		var marker := hull.get_node_or_null(pattern % (i + 1)) as Node3D
		if marker == null:
			push_error("[CitadelLife] coque sans marqueur '%s'" % (pattern % (i + 1)))
			continue
		var piece := scene.instantiate() as Node3D
		marker.add_child(piece)
		if piece.has_method("setup"):
			piece.call("setup", i)

## Prépare la respiration des émissifs.
##
## ⚠️ On DUPLIQUE le matériau. Celui importé du `.glb` est partagé par toutes les
## instances de la scène — et `AA_Emissive_Engine` porte le même nom sur **toutes**
## les coques du jeu. Le muter en place ferait respirer les tuyères du joueur et des
## ennemis au rythme de la forteresse. Même piège, même parade que `HullDetail.apply()`
## et `title_stage._tune_backdrop()`.
func _bind_breath(hull: Node3D) -> void:
	for mesh in _meshes(hull):
		for i in mesh.get_surface_override_material_count():
			var base := mesh.get_active_material(i) as StandardMaterial3D
			if base == null or base.resource_name != "AA_Emissive_Engine":
				continue
			if _breath_material == null:
				_breath_material = base.duplicate()
				_breath_energy = _breath_material.emission_energy_multiplier
			mesh.set_surface_override_material(i, _breath_material)

func _meshes(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	var mesh := node as MeshInstance3D
	if mesh != null:
		out.append(mesh)
	for child in node.get_children():
		_meshes(child, out)
	return out

## Respiration lente. Zéro allocation : on écrit un flottant (spec §31).
func _process(delta: float) -> void:
	_age += delta
	_breath_material.emission_energy_multiplier = _breath_energy * (
		1.0 + BREATH_AMPLITUDE * sin(_age * TAU / BREATH_PERIOD))
