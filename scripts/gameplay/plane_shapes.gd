class_name PlaneShapes
extends RefCounted

## Un jeu de formes de collision dans le PLAN DE JEU, stocké à plat.
##
## ⚠️ ZÉRO ALLOCATION EN COURS DE PARTIE (spec §26.1), et c'est la raison de cette forme
## bizarre. Les formes changent à CHAQUE IMAGE — les murs tournent, le noyau dérive — donc
## en faire des objets reviendrait à en allouer soixante fois par seconde, et à laisser le
## ramasse-miettes décider du rythme du combat. Les tableaux sont dimensionnés une fois par
## `reserve()` ; `clear()` remet un compteur à zéro et ne libère rien.
##
## Voir [`PlaneCollider`] pour ce qui les lit. La séparation est délibérée : ce fichier ne
## sait que RANGER des formes, l'autre ne sait que les RÉSOUDRE, et aucun des deux ne
## connaît le jeu.

enum Kind {
	## Un disque plein. `centre`, `rayon`.
	DISC,
	## Un secteur d'anneau — un mur courbe. `centre`, `rayon` médian, `épaisseur`,
	## `début` et `étendue` en degrés.
	RING_ARC,
	## Un segment épais. `a`, `b`, `rayon`.
	CAPSULE,
}

## Nombre de flottants réservés par forme. Six couvre la plus gourmande (RING_ARC).
const STRIDE := 6

var _kind := PackedInt32Array()
var _data := PackedFloat32Array()
var _count: int = 0

## Dimensionne pour `capacity` formes. À appeler UNE FOIS, au montage.
func reserve(capacity: int) -> void:
	if _kind.size() >= capacity:
		return
	# Croissance géométrique : un appelant qui aurait oublié de réserver ne paie pas une
	# réallocation par forme ajoutée.
	var target := maxi(capacity, _kind.size() * 2)
	_kind.resize(target)
	_data.resize(target * STRIDE)

## Vide sans libérer. C'est l'appel de début d'image.
func clear() -> void:
	_count = 0

func size() -> int:
	return _count

func kind_at(index: int) -> Kind:
	return _kind[index] as Kind

func param(index: int, slot: int) -> float:
	return _data[index * STRIDE + slot]

func centre_of(index: int) -> Vector2:
	var base := index * STRIDE
	return Vector2(_data[base], _data[base + 1])

func add_disc(centre: Vector2, radius: float) -> void:
	_push(Kind.DISC, centre.x, centre.y, radius, 0.0, 0.0, 0.0)

func add_ring_arc(centre: Vector2, radius: float, thickness: float,
		start_deg: float, span_deg: float) -> void:
	_push(Kind.RING_ARC, centre.x, centre.y, radius, thickness, start_deg, span_deg)

func add_capsule(a: Vector2, b: Vector2, radius: float) -> void:
	_push(Kind.CAPSULE, a.x, a.y, b.x, b.y, radius, 0.0)

func _push(kind: Kind, p0: float, p1: float, p2: float, p3: float,
		p4: float, p5: float) -> void:
	reserve(_count + 1)
	_kind[_count] = kind
	var base := _count * STRIDE
	_data[base] = p0
	_data[base + 1] = p1
	_data[base + 2] = p2
	_data[base + 3] = p3
	_data[base + 4] = p4
	_data[base + 5] = p5
	_count += 1
