class_name CitadelDetail
## Jeu de textures DÉDIÉ à l'Aegis Citadel (ADR-0013).
##
## `HullDetail` pose UNE carte de multiplication partagée par toutes les coques,
## calée sur un chasseur de 2 m. Sur une forteresse de 19,6 m, la même feuille lit
## comme du bruit rayé. Et surtout, elle ne porte aucun relief : une multiplication
## d'albedo peint des rainures, elle n'en creuse pas — la lumière ne les voit pas.
##
## Ici chaque matériau reçoit **le jeu qui le concerne** : blindage sur les coques,
## encombrement mécanique sur les greebles, facettes sur le cristal. Les cartes de
## relief sont DÉRIVÉES des hauteurs par `tools/derive-maps.py` — jamais générées
## (un générateur d'images rend une normal map aux gradients faux, cf. ADR-0013).
##
## Volontairement une classe statique, comme `HullDetail` et `CitadelLife`.

const _DIR := "res://assets/imported/textures/citadel/"

const PANELS_ALBEDO := preload(_DIR + "citadel_panels_mul.png")
const PANELS_NRM := preload(_DIR + "citadel_panels_nrm.png")
const PANELS_ROUGH := preload(_DIR + "citadel_panels_rough.png")
const PANELS_AO := preload(_DIR + "citadel_panels_ao.png")

const GREEBLE_NRM := preload(_DIR + "citadel_greebles_nrm.png")
const GREEBLE_ROUGH := preload(_DIR + "citadel_greebles_rough.png")
const GREEBLE_AO := preload(_DIR + "citadel_greebles_ao.png")

const CRYSTAL_EMISSION := preload(_DIR + "crystal_facets_mul.png")
const CRYSTAL_NRM := preload(_DIR + "crystal_facets_nrm.png")

## Les UV sont dépliées à 0,12 tuile/m côté Blender, soit **une tuile pour 8,33 m**
## (`build_aegis_citadel.py`). À ce tuilage, une plaque de blindage mesure ~1,4 m sur
## la coque — l'échelle que la planche de concept montre.
const TILING_PANELS := 1.0

## Les greebles, eux, doivent être DEUX FOIS plus gros. Mesuré au rendu : à la même
## densité que le blindage, chaque élément fait 28 cm, soit deux pixels une fois passé
## le post-process rétro (960x540) — les ponts se couvraient d'un moucheté qui lisait
## comme de la saleté, pas comme de la machinerie. À 0,5, l'élément fait 55 cm et
## redevient une pièce. C'est la leçon d'ADR-0011 : « le détail fin se noie ».
const TILING_GREEBLE := 0.5

## Le cristal ne montre qu'une demi-tuile sur ses 7 m : trois ou quatre facettes,
## comme la planche.
const TILING_CRYSTAL := 1.0

## Le relief est fort sur la mécanique, discret sur le blindage : une plaque de coque
## est plane, un faisceau de tuyaux ne l'est pas.
const NRM_PANELS := 0.9
const NRM_GREEBLE := 1.4
const NRM_CRYSTAL := 0.6

## `hull` : le Node3D instancié du `.glb` de la citadelle.
static func apply(hull: Node) -> void:
	for mesh in _meshes(hull):
		for i in mesh.get_surface_override_material_count():
			var base := mesh.get_active_material(i) as StandardMaterial3D
			if base == null:
				continue
			# On DUPLIQUE : le matériau importé est partagé par toutes les instances
			# du `.glb`, et ses noms (`AA_Hull`…) sont communs à TOUTES les coques du
			# jeu. Le muter en place texturerait le chasseur du joueur avec les
			# plaques d'une forteresse. Même parade que `HullDetail.apply()`.
			var tuned: StandardMaterial3D = base.duplicate()
			var tiling := _dress(tuned, base.resource_name)
			if tiling <= 0.0:
				continue
			tuned.uv1_scale = Vector3(tiling, tiling, tiling)
			mesh.set_surface_override_material(i, tuned)

## Retourne le tuilage à appliquer, ou 0 si le matériau ne reçoit rien (le verre
## reste lisse : une carte de plaques n'a aucun sens sur une verrière).
static func _dress(m: StandardMaterial3D, role: String) -> float:
	match role:
		"AA_Hull", "AA_Panel", "AA_Trim", "AA_Marking_Red":
			m.albedo_texture = PANELS_ALBEDO
			_set_normal(m, PANELS_NRM, NRM_PANELS)
			_set_rough(m, PANELS_ROUGH)
			_set_ao(m, PANELS_AO)
			return TILING_PANELS
		"AA_Greeble":
			# Pas d'albedo : l'anthracite est déjà sombre, le multiplier le noierait.
			# Tout le détail passe par le relief et la rugosité.
			_set_normal(m, GREEBLE_NRM, NRM_GREEBLE)
			_set_rough(m, GREEBLE_ROUGH)
			_set_ao(m, GREEBLE_AO)
			return TILING_GREEBLE
		"AA_Emissive_Engine":
			# ⚠️ Sur un émissif, la carte va sur l'ÉMISSION, pas sur l'albedo : la
			# couleur visible vient de `emission * energy` (2,5), qui écrase
			# complètement l'albedo. C'est exactement pour ça que le noyau se rendait
			# en goutte blanche uniforme — un émissif ne reçoit pas la lumière, donc
			# ses facettes n'existent ni par l'ombre ni par l'albedo.
			# ⚠️⚠️ L'OPÉRATEUR D'ABORD. Godot compose l'émission en **ADD** par défaut :
			# `EMISSION = (couleur + texture) * energie`. Une carte grise à 0,85 ne
			# module alors rien du tout, elle AJOUTE 0,85 de blanc au cyan — le noyau
			# vire au pâté blanc surexposé qui déborde sur toute la proue. Mesuré au
			# rendu, pas déduit. En MULTIPLY on obtient ce qu'on voulait : les creux
			# d'arête assombrissent, les facettes ressortent.
			m.emission_operator = BaseMaterial3D.EMISSION_OP_MULTIPLY
			m.emission_texture = CRYSTAL_EMISSION
			_set_normal(m, CRYSTAL_NRM, NRM_CRYSTAL)
			return TILING_CRYSTAL
		_:
			return 0.0  # AA_Glass : une verrière n'a ni plaques ni rainures
	return 0.0

static func _set_normal(m: StandardMaterial3D, tex: Texture2D, scale: float) -> void:
	m.normal_enabled = true
	m.normal_texture = tex
	m.normal_scale = scale

static func _set_rough(m: StandardMaterial3D, tex: Texture2D) -> void:
	m.roughness_texture = tex
	m.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED

static func _set_ao(m: StandardMaterial3D, tex: Texture2D) -> void:
	m.ao_enabled = true
	m.ao_texture = tex
	m.ao_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	# 0 = l'AO n'assombrit que l'ambiante. Au-delà, elle mange aussi la lumière
	# directe et la coque vire au gris sale sous la clé.
	m.ao_light_affect = 0.0

static func _meshes(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	var mesh := node as MeshInstance3D
	if mesh != null:
		out.append(mesh)
	for child in node.get_children():
		_meshes(child, out)
	return out
