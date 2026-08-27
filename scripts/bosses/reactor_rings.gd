class_name ReactorRings
## Les anneaux du réacteur — géométrie PURE : (anneaux, azimut, âge) -> ouvert ou non.
##
## Aucun nœud, aucun état, aucune allocation : testable en headless
## (tests/unit/test_reactor_rings.gd). Le combat n'en tire qu'un booléen, le décor n'en tire
## qu'une pose. Les deux lisent la MÊME fonction — c'est ce qui garantit qu'on tire là où
## l'on voit une ouverture, et le contraire serait le pire défaut possible pour cette phase.
##
## ⚠️ IL NE FAIT PLUS DE COLLISION. Il en a fait — `blocks()`, `blocks_body()`, `push_out()`,
## `first_hit_along()` — et c'était un moteur de collision écrit pour UNE forme, qui ne
## savait pousser que radialement. [PlaneCollider] l'a remplacé, et ces fonctions ont été
## retirées plutôt que laissées à dormir : plus personne ne les appelait, seuls leurs propres
## tests les maintenaient en vie. Deux implémentations de la même chose finissent toujours
## par diverger, et c'est ce fichier qui aurait gagné en silence.
##
## Ce qui reste ici est la CONVENTION : où sont les ouvertures, et dans quel sens ça tourne.
## `fill_shapes()` la traduit en formes pour le module de collision.
##
## ⚠️ C'est `ADR-0029` à l'envers. Là, il fallait des périodes qui ne retombent JAMAIS en
## rythme, pour que l'œil ne repère pas la boucle. Ici il faut qu'elles se croisent SOUVENT,
## pour que le joueur ne reste jamais enfermé. Deux problèmes opposés, deux réglages opposés.

## ⚠️ INTERRUPTEUR D'ISOLATION (`--no-rings`) : plus AUCUN mur, ni en collision ni au décor.
## « La méthode de la sphère indienne : vire les murs, on teste sans » (opérateur,
## 2026-08-28). Quand un symptôme survit à quatre correctifs, on retire l'élément suspect
## et on regarde si le symptôme part avec lui. Si le chasseur pousse encore à droite sans
## un seul mur, les murs sont hors de cause — et on aura cessé de les accuser pour de bon.
static var disabled: bool = false

## Azimut d'ouverture le plus proche, à défaut d'en trouver un : rend une valeur hors du
## cercle pour qu'aucun appelant ne la prenne pour une direction valide.
const NO_OPENING := INF



## Cet anneau laisse-t-il passer à `bearing_deg`, à l'instant `age` ?
static func ring_open(ring: ReactorRing, bearing_deg: float, age: float) -> bool:
	if disabled or ring == null or ring.apertures < 1:
		return true
	var step := 360.0 / float(ring.apertures)
	# Repli du tour sur UN secteur : les ouvertures étant régulières, il suffit de comparer
	# l'écart au centre de l'ouverture la plus proche.
	var centre := fposmod(ring.phase_deg + ring.speed_deg * age, step)
	var offset := fposmod(bearing_deg - centre, step)
	return minf(offset, step - offset) <= ring.aperture_deg * 0.5


## Le corridor est-il ouvert à `bearing_deg` ? Il faut que TOUS les anneaux le soient.
static func is_open(rings: Array[ReactorRing], bearing_deg: float, age: float) -> bool:
	for ring in rings:
		if not ring_open(ring, bearing_deg, age):
			return false
	return true


## Un azimut où le corridor est ouvert, à l'instant `age` — celui le plus PROCHE de
## `from_deg`, pour que le repère désigne l'ouverture vers laquelle il faut aller et non une
## autre à l'opposé. Rend `NO_OPENING` si le blindage est intégralement fermé.
##
## Balayage par pas fixe : la fonction est appelée une fois par image au plus, et un pas de
## deux degrés suffit à désigner une ouverture qui en fait quarante-huit.
static func nearest_opening(rings: Array[ReactorRing], from_deg: float, age: float,
		step_deg: float = 2.0) -> float:
	if rings.is_empty():
		return from_deg
	var best := NO_OPENING
	var best_gap := INF
	var samples := int(360.0 / maxf(step_deg, 0.5))
	for i in samples:
		var bearing := float(i) * step_deg
		if not is_open(rings, bearing, age):
			continue
		var gap := absf(angle_difference(deg_to_rad(bearing), deg_to_rad(from_deg)))
		if gap < best_gap:
			best_gap = gap
			best = bearing
	return best


## Verse les murs de CET instant dans un jeu de formes, prêt pour [PlaneCollider].
##
## ⚠️ C'EST ICI, ET NULLE PART AILLEURS, QUE VIT LA CONVENTION DE ROTATION. Le décor
## (`CoreInterior.build_rings`) dessine un arc plein de `start = k x pas + ouverture/2` puis
## fait tourner son pivot de `-(phase + vitesse x age)` — le signe est inversé parce que la
## rotation d'un `Node3D` autour de Y va à l'envers de l'azimut du plan. Dans le plan, ça
## revient donc à AJOUTER cet angle. Se tromper de signe ici ferait bloquer le tir là où
## l'on voit une ouverture : le pire défaut possible pour cette phase, et le seul que le
## joueur ne pourrait pas apprendre.
##
## `shapes` est vidé puis rempli — il appartient à l'appelant, qui l'a dimensionné une fois.
static func fill_shapes(shapes: PlaneShapes, rings: Array[ReactorRing],
		centre: Vector2, age: float) -> void:
	if disabled:
		return
	for ring in rings:
		if ring == null or ring.apertures < 1:
			continue
		var step := 360.0 / float(ring.apertures)
		var span := step - ring.aperture_deg
		if span <= 0.0:
			continue
		var turn := ring.phase_deg + ring.speed_deg * age
		for k in ring.apertures:
			shapes.add_ring_arc(centre, ring.radius, ring.thickness,
				float(k) * step + ring.aperture_deg * 0.5 + turn, span, ring.speed_deg)

## Combien de formes `fill_shapes()` produira — pour dimensionner UNE fois.
static func shape_count(rings: Array[ReactorRing]) -> int:
	var total := 0
	for ring in rings:
		if ring != null and ring.apertures >= 1 and ring.aperture_deg < 360.0 / float(ring.apertures):
			total += ring.apertures
	return total
