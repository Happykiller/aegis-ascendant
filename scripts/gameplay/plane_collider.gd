class_name PlaneCollider

## La collision du plan de jeu : un corps rond contre un jeu de [PlaneShapes].
##
## ⚠️ IL REMPLACE UN RATTRAPAGE. La version d'avant vivait dans `ReactorRings`, ne
## connaissait qu'une forme — le secteur d'anneau — et poussait toujours RADIALEMENT. D'où
## trois plaintes du playtest qui n'en faisaient qu'une : « le vaisseau rentre en partie
## dans les murs », « le bord des murs est franchissable », « je fonce tout droit et mon
## vaisseau est bloqué, il avance pas ». La dernière était la plus parlante : poussé vers
## l'intérieur par le seul axe qu'il connaissait, le chasseur atterrissait dans un couloir
## dont il ne pouvait plus sortir, alors que l'ouverture était à un demi-mètre de côté.
##
## Ici un corps coincé sort par le chemin LE PLUS COURT — vers l'intérieur, vers
## l'extérieur, ou **par le bout de l'arc**, c'est-à-dire par l'ouverture. C'est ce que
## « crédible » veut dire pour un joueur : il n'est jamais retenu par une géométrie qu'il
## ne voit pas.
##
## Tout est statique et pur : aucune scène, aucun autoload, aucun nœud. Les tests
## l'instancient à la main (règle du projet : les unités se testent sans le moteur).

## Rendu par [method first_hit] quand le segment est libre. Un `Vector2` fini est toujours
## un point de contact — d'où l'infini pour dire « rien ».
const NO_HIT := Vector2.INF

## ⚠️ UN CHEVEU AU-DELÀ DE LA FACE, ET C'EST NÉCESSAIRE. Reposer PILE sur la face laisse le
## point dans la forme au sens de la comparaison large, la passe suivante le repousse encore,
## et le chasseur reste collé en vibrant. Vécu, corrigé, gardé.
const EDGE_EPSILON := 0.01

## Nombre de passes de dégagement. Sortir d'une forme peut faire entrer dans sa voisine ;
## deux suffisent tant que les formes ne s'empilent pas à plus de deux d'épaisseur.
const RESOLVE_PASSES := 2

## Un corps allongé sort en plusieurs fois : chaque passe ne dégage que le point le plus
## enfoncé, et un vaisseau enfoncé sur toute sa longueur en demande plusieurs.
const CAPSULE_PASSES := 6

# --- Interrogation ------------------------------------------------------------

## Le point est-il dans la forme `index`, corps de rayon `body` compris ?
static func shape_blocks(shapes: PlaneShapes, index: int, point: Vector2,
		body: float) -> bool:
	match shapes.kind_at(index):
		PlaneShapes.Kind.DISC:
			return point.distance_to(shapes.centre_of(index)) \
				<= shapes.param(index, 2) + body
		PlaneShapes.Kind.RING_ARC:
			return _arc_blocks(shapes, index, point, body)
		PlaneShapes.Kind.CAPSULE:
			var a := shapes.centre_of(index)
			var b := Vector2(shapes.param(index, 2), shapes.param(index, 3))
			return _distance_to_segment(point, a, b) <= shapes.param(index, 4) + body
	return false

## Le point touche-t-il QUELQUE forme ?
static func blocks(shapes: PlaneShapes, point: Vector2, body: float = 0.0) -> bool:
	for i in shapes.size():
		if shape_blocks(shapes, i, point, body):
			return true
	return false

# --- Dégagement ---------------------------------------------------------------

## Ramène `point` hors de toute forme, par le chemin le plus court. Rend le point inchangé
## s'il était déjà libre — les appelants s'en servent pour ne pas écrire une position pour
## rien.
static func resolve(shapes: PlaneShapes, point: Vector2, body: float = 0.0) -> Vector2:
	var out := point
	for _pass in RESOLVE_PASSES:
		var moved := false
		for i in shapes.size():
			if not shape_blocks(shapes, i, out, body):
				continue
			out = _escape(shapes, i, out, body)
			moved = true
		if not moved:
			break
	return out

# --- Ligne de tir -------------------------------------------------------------

## Premier point du segment `from` -> `to` qui touche une forme, ou [constant NO_HIT].
##
## ⚠️ ÉCHANTILLONNÉ, PAS RÉSOLU ANALYTIQUEMENT, et c'est un choix : un secteur d'anneau
## n'a pas d'intersection segment/forme close simple, et l'échantillonnage suffit largement
## à l'échelle du jeu (un pas vaut quelques centimètres). Il est donné en paramètre pour
## qu'un appelant qui aurait besoin de finesse puisse la payer.
static func first_hit(shapes: PlaneShapes, from: Vector2, to: Vector2,
		body: float = 0.0, steps: int = 32) -> Vector2:
	if shapes.size() == 0:
		return NO_HIT
	var count := maxi(steps, 1)
	for s in count + 1:
		var point := from.lerp(to, float(s) / float(count))
		if blocks(shapes, point, body):
			return point
	return NO_HIT

## Le tir passe-t-il ?
static func segment_blocked(shapes: PlaneShapes, from: Vector2, to: Vector2,
		body: float = 0.0, steps: int = 32) -> bool:
	return first_hit(shapes, from, to, body, steps) != NO_HIT

# --- Interne ------------------------------------------------------------------

static func _arc_blocks(shapes: PlaneShapes, index: int, point: Vector2,
		body: float) -> bool:
	var centre := shapes.centre_of(index)
	var radius := shapes.param(index, 2)
	var half := shapes.param(index, 3) * 0.5 + body
	var offset := point - centre
	var distance := offset.length()
	if absf(distance - radius) > half:
		return false
	# ⚠️ L'ÉTENDUE ANGULAIRE DU CORPS, et son absence était un bug à part entière : une aile
	# passait à travers un bord que le CENTRE du vaisseau franchissait proprement.
	var extent := 0.0
	if body > 0.0 and distance > 0.0001:
		extent = rad_to_deg(asin(clampf(body / distance, -1.0, 1.0)))
	return _within_span(rad_to_deg(offset.angle()), shapes.param(index, 4),
		shapes.param(index, 5), extent)

static func _escape(shapes: PlaneShapes, index: int, point: Vector2,
		body: float) -> Vector2:
	match shapes.kind_at(index):
		PlaneShapes.Kind.DISC:
			var centre := shapes.centre_of(index)
			return _push_from(centre, point, shapes.param(index, 2) + body)
		PlaneShapes.Kind.RING_ARC:
			return _escape_arc(shapes, index, point, body)
		PlaneShapes.Kind.CAPSULE:
			var a := shapes.centre_of(index)
			var b := Vector2(shapes.param(index, 2), shapes.param(index, 3))
			return _push_from(_closest_on_segment(point, a, b), point,
				shapes.param(index, 4) + body)
	return point

## Le cœur du module : quatre sorties possibles d'un mur courbe, on prend la plus courte.
## Les deux dernières — par un bout de l'arc — sont exactement ce qui manquait, et ce qui
## enfermait le chasseur alors que l'ouverture était à côté de lui.
static func _escape_arc(shapes: PlaneShapes, index: int, point: Vector2,
		body: float) -> Vector2:
	var centre := shapes.centre_of(index)
	var radius := shapes.param(index, 2)
	var half := shapes.param(index, 3) * 0.5 + body
	var start_deg := shapes.param(index, 4)
	var span_deg := shapes.param(index, 5)
	var offset := point - centre
	var distance := offset.length()
	if distance < 0.0001:
		# Au centre exact, aucune direction n'est « dehors ». Convention du projet : le bas.
		return centre + Vector2(0.0, -(radius + half + EDGE_EPSILON))
	var bearing := rad_to_deg(offset.angle())
	var extent := 0.0
	if body > 0.0:
		extent = rad_to_deg(asin(clampf(body / distance, -1.0, 1.0)))
	var inward := radius - half - EDGE_EPSILON
	var outward := radius + half + EDGE_EPSILON
	var best := absf(distance - inward)
	var target := offset.normalized() * inward
	var cost := absf(outward - distance)
	if cost < best:
		best = cost
		target = offset.normalized() * outward
	# Les bouts. Le coût est une LONGUEUR D'ARC (rayon x angle), pas un angle : sinon un
	# mur lointain paraîtrait plus proche par le bout qu'un mur voisin par la face.
	var before := start_deg - extent - EDGE_EPSILON
	var after := start_deg + span_deg + extent + EDGE_EPSILON
	for edge in [before, after]:
		var delta := absf(_wrap_deg(bearing - edge))
		cost = distance * deg_to_rad(delta)
		if cost < best:
			best = cost
			target = Vector2(cos(deg_to_rad(edge)), sin(deg_to_rad(edge))) * distance
	return centre + target

static func _push_from(centre: Vector2, point: Vector2, distance: float) -> Vector2:
	var offset := point - centre
	if offset.length() < 0.0001:
		return centre + Vector2(0.0, -(distance + EDGE_EPSILON))
	return centre + offset.normalized() * (distance + EDGE_EPSILON)

static func _within_span(bearing_deg: float, start_deg: float, span_deg: float,
		extent_deg: float) -> bool:
	var from_start := _wrap_positive(bearing_deg - start_deg + extent_deg)
	return from_start <= span_deg + extent_deg * 2.0

static func _wrap_positive(degrees: float) -> float:
	return fposmod(degrees, 360.0)

static func _wrap_deg(degrees: float) -> float:
	var wrapped := fposmod(degrees + 180.0, 360.0) - 180.0
	return wrapped

static func _closest_on_segment(point: Vector2, a: Vector2, b: Vector2) -> Vector2:
	var ab := b - a
	var length_squared := ab.length_squared()
	if length_squared < 0.000001:
		return a
	return a + ab * clampf((point - a).dot(ab) / length_squared, 0.0, 1.0)

static func _distance_to_segment(point: Vector2, a: Vector2, b: Vector2) -> float:
	return point.distance_to(_closest_on_segment(point, a, b))

# --- Les corps allongés --------------------------------------------------------

## Dégage une CAPSULE — un corps plus long que large, comme un vaisseau.
##
## ⚠️ UN VAISSEAU N'EST PAS UN DISQUE, et le croire a laissé passer son nez à travers les
## murs. `specter_9.glb` mesure 1,30 de large pour 2,41 de long : décrit par un cercle de
## 0,85 — sa demi-envergure — il couvrait ses ailes et débordait de 0,38 devant. Le joueur
## voyait sa pointe entrer dans le blindage, et il avait raison.
##
## On échantillonne l'axe, on regarde quel point est le plus enfoncé, et on translate TOUT
## le corps de ce que ce point exige. Translater et non pivoter : dans un shoot vertical, le
## vaisseau garde son cap (`LOI-SYS-07`), donc son axe ne tourne pas.
static func resolve_capsule(shapes: PlaneShapes, centre: Vector2, axis: Vector2,
		half_length: float, radius: float, samples: int = 5) -> Vector2:
	if shapes.size() == 0:
		return centre
	var direction := axis.normalized() if axis.length() > 0.0001 else Vector2(0.0, 1.0)
	var count := maxi(samples, 2)
	var out := centre
	for _pass in CAPSULE_PASSES:
		if not capsule_blocks(shapes, out, direction, half_length, radius, count):
			break
		# ⚠️ ON NE PREND PAS LA PLUS GRANDE CORRECTION, ET C'ÉTAIT LE PREMIER RÉFLEXE. Chaque
		# point de l'axe veut sortir par le côté LE PLUS PROCHE DE LUI : quand le nez a déjà
		# dépassé le plan médian d'un mur mince, sa sortie la plus courte est EN AVANT — et
		# suivre la plus grande correction pousse alors tout le vaisseau À TRAVERS le mur.
		# Vu en test, et c'est exactement le défaut qu'on prétendait corriger.
		#
		# On juge donc chaque candidate à ce qu'elle DONNE : celle qui laisse le moins de
		# points enfoncés gagne, et à égalité la plus courte. Le corps recule ou avance d'un
		# bloc, mais il ne traverse plus.
		var best := Vector2.ZERO
		var best_stuck := count + 1
		var best_length := INF
		for s in count:
			var t := lerpf(-half_length, half_length, float(s) / float(count - 1))
			var probe := out + direction * t
			var shift := resolve(shapes, probe, radius) - probe
			if shift.length() <= 0.0:
				continue
			var stuck := _stuck_count(shapes, out + shift, direction, half_length,
				radius, count)
			if stuck < best_stuck or (stuck == best_stuck and shift.length() < best_length):
				best_stuck = stuck
				best_length = shift.length()
				best = shift
		if best == Vector2.ZERO:
			break
		out += best
	return out

static func _stuck_count(shapes: PlaneShapes, centre: Vector2, direction: Vector2,
		half_length: float, radius: float, count: int) -> int:
	var stuck := 0
	for s in count:
		var t := lerpf(-half_length, half_length, float(s) / float(count - 1))
		if blocks(shapes, centre + direction * t, radius):
			stuck += 1
	return stuck

## La capsule touche-t-elle quelque chose ?
static func capsule_blocks(shapes: PlaneShapes, centre: Vector2, axis: Vector2,
		half_length: float, radius: float, samples: int = 5) -> bool:
	var direction := axis.normalized() if axis.length() > 0.0001 else Vector2(0.0, 1.0)
	var count := maxi(samples, 2)
	for s in count:
		var t := lerpf(-half_length, half_length, float(s) / float(count - 1))
		if blocks(shapes, centre + direction * t, radius):
			return true
	return false
