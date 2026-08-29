class_name CortegeFlyby
extends Node3D
## La coque du Long Cortège qui défile sous le joueur pendant tout le niveau 2.
##
## ⚠️ IL REMPLACE LE FOND, IL NE S'Y AJOUTE PAS. Même arbitrage que le survol de lune
## (`ADR-0027`) et pour la même raison mesurée : sur la machine qui contraint, le fond spatial
## complet coûte 13,05 ms sur les 16,67 disponibles à 60 Hz. Une coque pleine page PAR-DESSUS
## lui ne tiendrait pas. Le décor porte donc son propre ciel, en `deep_sky`.
##
## ⚠️ ET LA DIFFÉRENCE AVEC LA LUNE EST LE MÉCANISME MÊME. La lune défile par ROTATION : sa
## surface tourne, on ne la parcourt jamais. Ici on va d'un bout à l'autre d'un objet fini, dans
## un seul sens, sans jamais revenir en arrière — c'est une TRANSLATION, et c'est ce qui rend
## chaque cible ratée définitivement ratée.
##
## Le `.glb` est chargé au RUNTIME et non `preload` : le niveau doit être jouable et mesurable
## avant que la forge ait livré (`BRIEF-0089`). Sans lui, une doublure procédurale prend sa
## place et le journal le dit — une doublure qui se croit livrée est le genre de défaut muet que
## ce dépôt collectionne.

const DECOR_PATH := "res://assets/imported/models/backgrounds/long_cortege.glb"

## Le plafond du plan de jeu. ⚠️ RIEN DE LA COQUE NE MONTE AU-DESSUS : un volume qui traverserait
## le plan masquerait le combat sans jamais pouvoir être touché. Repris de `MoonFlyby`, où c'est
## un test qui l'a attrapé la première fois.
const CEILING_Y := -3.0

## Le ciel propre au survol, sous la coque. Plus bas que le fond habituel (-5) pour loger la
## coque entre lui et le plan de jeu.
const SKY_Y := -38.0
const SKY_SIZE := Vector2(320.0, 260.0)

## La coque vit à cette hauteur : assez bas pour passer sous le plafond, assez haut pour emplir
## le cadre à FOV 62°.
const HULL_Y := -12.0

## Largeur de la coque, en unités. Le plan de jeu fait 28 de large : elle l'emplit.
const HULL_WIDTH := 28.0

## Où un tronçon entre et où il sort, le long de l'axe de vol (monde -Z = haut de l'écran).
## ⚠️ Le tronçon apparaît LOIN devant et sort LOIN derrière : à FOV 62° et caméra plongeante,
## un objet visible à l'écran couvre bien plus que les 16 unités du plan de jeu.
const SPAWN_Z := -70.0
const RETIRE_Z := 46.0

signal section_entered(index: int)
signal survey_finished()

## Vitesse de défilement, en unités/seconde. Posée par le niveau depuis `CortegeTuning` : elle
## commande la durée, donc les fenêtres de tir, donc tout l'équilibrage.
var scroll_speed: float = 2.4
var section_length: float = 100.0
var section_count: int = 5

var _sections: Array[Node3D] = []
var _sky: MeshInstance3D
var _is_stand_in: bool = false
var _travelled: float = 0.0
var _entered: int = -1
var _finished: bool = false

func _ready() -> void:
	reveal(false)
	_build()

## Allume ou éteint le survol. ⚠️ `set_process` AUSSI : un décor caché qui continue de calculer
## son défilement dépense pour rien, et se retrouve ailleurs qu'où on l'a laissé.
func reveal(on: bool) -> void:
	visible = on
	set_process(on)
	if not on:
		return
	_travelled = 0.0
	_entered = -1
	_finished = false
	_place_sections()

func is_stand_in() -> bool:
	return _is_stand_in

## Ce qui a été parcouru, en part du survol entier — pour l'indicateur de progression.
func progress() -> float:
	var total := section_length * float(section_count)
	return clampf(_travelled / total, 0.0, 1.0) if total > 0.001 else 0.0

func current_section() -> int:
	return clampi(int(_travelled / maxf(section_length, 0.001)), 0, section_count - 1)

func _build() -> void:
	add_child(_make_sky())
	var decor: Node3D = null
	if ResourceLoader.exists(DECOR_PATH):
		var packed: PackedScene = load(DECOR_PATH) as PackedScene
		if packed != null:
			decor = packed.instantiate() as Node3D
	if decor != null:
		add_child(decor)
		_collect_sections(decor)
	if _sections.is_empty():
		_is_stand_in = true
		_build_stand_in()
	_silence_shadows()
	_place_sections()

## Résout les tronçons par CONTRAT DE NOMS, comme `MoonFlyby` le fait pour ses rochers :
## `Section_01` … `Section_NN`, enfants directs du décor.
func _collect_sections(decor: Node3D) -> void:
	for child in decor.get_children():
		var node := child as Node3D
		if node != null and node.name.begins_with("Section_"):
			_sections.append(node)
	_sections.sort_custom(func(a: Node3D, b: Node3D) -> bool: return a.name < b.name)

## La doublure : un tronçon = une dalle nervurée. Elle ne cherche pas à être belle, elle cherche
## à rendre le niveau JOUABLE et MESURABLE avant la livraison de la forge.
func _build_stand_in() -> void:
	for i in section_count:
		var section := Node3D.new()
		section.name = "Section_%02d" % (i + 1)
		var plate := MeshInstance3D.new()
		var mesh := BoxMesh.new()
		mesh.size = Vector3(HULL_WIDTH, 2.0, section_length)
		plate.mesh = mesh
		var mat := StandardMaterial3D.new()
		# Anthracite de l'Unisson (charte §3), plus clair d'un tronçon à l'autre pour que la
		# jonction se voie pendant la mise au point.
		var teinte := 0.10 + 0.015 * float(i)
		mat.albedo_color = Color(teinte, teinte, teinte * 1.08)
		mat.roughness = 0.55
		plate.material_override = mat
		section.add_child(plate)
		add_child(section)
		_sections.append(section)

## Les tronçons sont posés bout à bout le long de l'axe de vol, décalés de ce qui a déjà défilé.
func _place_sections() -> void:
	for i in _sections.size():
		_sections[i].position = Vector3(0.0, HULL_Y, _section_z(i))

func _section_z(index: int) -> float:
	# Le tronçon 0 entre en premier : il part loin devant et remonte vers le joueur.
	return SPAWN_Z + float(index) * section_length + _travelled

func _process(delta: float) -> void:
	if _finished:
		return
	_travelled += scroll_speed * delta
	for i in _sections.size():
		var z := _section_z(i)
		_sections[i].position.z = z
		_sections[i].visible = z < RETIRE_Z + section_length
	var section := current_section()
	if section != _entered:
		_entered = section
		section_entered.emit(section)
	if _travelled >= section_length * float(section_count):
		_finished = true
		survey_finished.emit()

## Le ciel du survol : même shader que le fond spatial, mais sur son chemin `deep_sky`.
## ⚠️ CE N'EST PAS UN RÉGLAGE, C'EST UN CHEMIN. Baisser l'intensité de la nébuleuse à zéro
## n'économiserait rien — le shader calcule ses cinq champs de bruit quoi qu'il arrive.
func _make_sky() -> MeshInstance3D:
	_sky = MeshInstance3D.new()
	_sky.name = "CortegeSky"
	var mesh := PlaneMesh.new()
	mesh.size = SKY_SIZE
	_sky.mesh = mesh
	_sky.position = Vector3(0.0, SKY_Y, -4.0)
	_sky.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# Le ciel est un plan immense vu de très près : sans marge, il disparaît dès que son centre
	# sort du frustum. Même valeur que les deux autres ciels du jeu.
	_sky.extra_cull_margin = 100.0
	var backdrop: Resource = load("res://shaders/space_background.gdshader")
	if backdrop != null:
		var mat := ShaderMaterial.new()
		mat.shader = backdrop
		mat.set_shader_parameter(&"deep_sky", true)
		mat.set_shader_parameter(&"scroll_speed", -0.5)
		_sky.material_override = mat
		_sky.material_override.render_priority = -1
	return _sky

## ⚠️ La carte d'ombres directionnelle s'arrête à 40 unités : une coque de 500 se retrouverait à
## moitié dedans, à moitié dehors, et la couture se verrait défiler. Aucune ombre portée.
func _silence_shadows() -> void:
	for node in _all_meshes(self):
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

func _all_meshes(root: Node) -> Array[MeshInstance3D]:
	var found: Array[MeshInstance3D] = []
	for child in root.get_children():
		var mesh := child as MeshInstance3D
		if mesh != null:
			found.append(mesh)
		found.append_array(_all_meshes(child))
	return found

# --- Fonctions pures, testables sans arbre de scène ---------------------------

## Où se trouve un tronçon après une distance parcourue. ⚠️ STATIQUE ET PURE, comme
## `MoonFlyby.drifted()` : c'est ce qui permet de tester le défilement sans monter la scène.
static func section_z_at(index: int, length: float, travelled: float) -> float:
	return SPAWN_Z + float(index) * length + travelled

## Le tronçon sous le joueur après cette distance.
static func section_at(travelled: float, length: float, count: int) -> int:
	if length <= 0.001 or count <= 0:
		return 0
	return clampi(int(travelled / length), 0, count - 1)

## Combien de temps une cible reste tirable, à cette vitesse. Le survol ne revient jamais en
## arrière : c'est cette fenêtre, et elle seule, qui borne ce qu'on peut abattre.
static func window_for(visible_span: float, speed: float) -> float:
	return visible_span / speed if speed > 0.001 else 0.0
