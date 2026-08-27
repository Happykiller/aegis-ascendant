class_name ReactorRings
## Les anneaux du réacteur — géométrie PURE : (anneaux, azimut, âge) -> ouvert ou non.
##
## Aucun nœud, aucun état, aucune allocation : testable en headless
## (tests/unit/test_reactor_rings.gd). Le combat n'en tire qu'un booléen, le décor n'en tire
## qu'une pose. Les deux lisent la MÊME fonction — c'est ce qui garantit qu'on tire là où
## l'on voit une ouverture, et le contraire serait le pire défaut possible pour cette phase.
##
## ⚠️ C'est `ADR-0029` à l'envers. Là, il fallait des périodes qui ne retombent JAMAIS en
## rythme, pour que l'œil ne repère pas la boucle. Ici il faut qu'elles se croisent SOUVENT,
## pour que le joueur ne reste jamais enfermé. Deux problèmes opposés, deux réglages opposés.

## Azimut d'ouverture le plus proche, à défaut d'en trouver un : rend une valeur hors du
## cercle pour qu'aucun appelant ne la prenne pour une direction valide.
const NO_OPENING := INF

## Marge de sortie d'un mur, en unités. Voir `push_out()`.
const EDGE_EPSILON := 0.01


## Cet anneau laisse-t-il passer à `bearing_deg`, à l'instant `age` ?
static func ring_open(ring: ReactorRing, bearing_deg: float, age: float) -> bool:
	if ring == null or ring.apertures < 1:
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


## Ce point est-il DANS le mur de cet anneau ? `local` est relatif au centre du réacteur.
##
## ⚠️ LE MUR EST UN CORPS, pas un halo. Playtest du 2026-08-27 : « faut leur donner un corps,
## pas qu'un halo de couleur, et faut intégrer au jeu un moteur de collision : on ne doit
## pas pouvoir franchir les murs. »
static func blocks(ring: ReactorRing, local: Vector2, age: float) -> bool:
	if ring == null:
		return false
	var distance := local.length()
	var half := ring.thickness * 0.5
	if distance < ring.radius - half or distance > ring.radius + half:
		return false
	return not ring_open(ring, rad_to_deg(local.angle()), age)


## Repousse un point hors des murs, radialement, vers le bord le plus proche.
##
## ⚠️ RADIALEMENT ET NON LATÉRALEMENT : glisser le long du mur ferait franchir l'ouverture
## voisine à un joueur qui pousse contre la paroi, et l'anneau cesserait de fermer quoi que
## ce soit. On le repousse donc du côté d'où il vient.
##
## Fonction PURE : aucun nœud, aucun état — la collision se teste en headless comme le
## reste, et c'est ce qui la rend vérifiable sans jouer.
static func push_out(rings: Array[ReactorRing], local: Vector2, age: float,
		clearance: float = 0.0) -> Vector2:
	var point := local
	# Deux passes : repousser hors d'un anneau peut faire entrer dans l'autre quand ils
	# sont proches. Deux suffisent — ils ne se chevauchent jamais (`validate()` l'impose).
	for pass_index in 2:
		for ring in rings:
			if not blocks(ring, point, age):
				continue
			var half := ring.thickness * 0.5 + clearance
			var distance := point.length()
			if distance < 0.0001:
				# Au centre exact : aucune direction n'est « dehors ». On sort vers le bas,
				# la convention du projet quand un vecteur nul rendrait NaN.
				point = Vector2(0.0, -(ring.radius + half))
				continue
			# ⚠️ UN CHEVEU AU-DELA DU BORD, ET C'EST NECESSAIRE. Repousser PILE sur la face
			# laisse le point dans le mur au sens de `blocks()` (comparaison large), et la
			# passe suivante le repousse a nouveau : le joueur reste collé, vibrant.
			var inward := ring.radius - half - EDGE_EPSILON
			var outward := ring.radius + half + EDGE_EPSILON
			var to_in := absf(distance - inward)
			var to_out := absf(outward - distance)
			point = point.normalized() * (inward if to_in <= to_out else outward)
	return point


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
