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

## Ce que COÛTE une sortie par le bout de l'arc, en multiple de sa longueur réelle.
##
## ⚠️ UN MUR QUI TOURNE NE DOIT PAS VOUS EMPORTER AVEC LUI, et sans cette pénalité il le
## faisait. Sortir « par le bout » est un déplacement TANGENTIEL : rejoué à chaque image
## contre un arc en rotation, il devient un convoyeur. Mesuré sur la géométrie livrée, un
## chasseur qui pousse vers le noyau en montant dérivait de **9,2 unités** latéralement, en
## contact 279 images sur 540 — « j'ai comme un mur qui me pousse sur la droite, ça ne marche
## pas du tout » (playtest du 2026-08-27, troisième retour sur le même symptôme).
##
## ⚠️ ET CE N'EST PAS UNE QUESTION DE PLACE. On a d'abord cru que le couloir trop étroit
## expliquait tout, et on l'a élargi : la dérive persistait, parce qu'elle ne vient pas de
## l'étroitesse mais du CHOIX DE SORTIE. La simulation qui avait conclu le contraire posait
## le chasseur immobile au milieu du couloir — là où aucun bord d'arc ne vient le chercher.
## Un banc qui ne reproduit pas le geste du joueur ne prouve rien.
##
## À 2, la sortie par le bout reste possible quand elle est franchement la plus courte —
## c'est elle qui libère un corps coincé à quelques centimètres d'une ouverture, et
## `test_a_body_near_the_end_of_a_wall_escapes_through_the_opening` l'exige — mais elle cesse
## de gagner sur une sortie radiale à peine plus longue. Le mur repousse, il ne transporte
## plus. Valeur mesurée : à 1 la dérive vaut 9,2 u, à 2 elle tombe à zéro.
const EDGE_EXIT_COST := 2.0

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
			return distance_to_segment(point, a, b) <= shapes.param(index, 4) + body
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
		cost = distance * deg_to_rad(delta) * EDGE_EXIT_COST
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

## Distance d'un point au segment `a`-`b`. Publique parce qu'un corps allongé n'est pas
## toujours un obstacle : la passe d'écrasement (`WaveSpawner.crush_contacts`) a besoin de
## la même mesure que la collision pour dire « la coque du chasseur touche cette unité »,
## et il n'existe qu'UNE définition de cette distance dans le jeu.
static func distance_to_segment(point: Vector2, a: Vector2, b: Vector2) -> float:
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
## `prefer` — une direction vers laquelle on AIMERAIT sortir, typiquement « d'où l'on vient ».
## ⚠️ SANS ELLE, LE CORPS SE FAIT TRANSPORTER. Mesuré le 2026-08-27 sur le blindage livré :
## un chasseur immobile sous le noyau, poussé par les anneaux qui tournent, partait de
## y = −6,3 et finissait à y = +6,85 — de l'autre côté du réacteur. La sortie la plus courte
## est parfois VERS L'INTÉRIEUR ; elle le déposait dans le couloir entre les deux murs, d'où
## il ne ressortait plus, et le blindage l'emmenait avec lui. C'est ce que l'opérateur a
## appelé « un aimant ». En préférant repartir d'où il vient, il est repoussé, pas emporté.
static func resolve_capsule(shapes: PlaneShapes, centre: Vector2, axis: Vector2,
		half_length: float, radius: float, samples: int = 5,
		prefer: Vector2 = Vector2.ZERO) -> Vector2:
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
			# À nombre de points dégagés égal, on classe par ce que ça COÛTE : la longueur
			# du déplacement, moins ce qu'il gagne dans la direction préférée. Une sortie
			# légèrement plus longue mais « vers d'où l'on vient » l'emporte donc sur une
			# sortie plus courte qui enfoncerait le corps plus loin dans le décor.
			var cost := shift.length()
			if prefer != Vector2.ZERO:
				cost -= shift.dot(prefer.normalized())
			if stuck < best_stuck or (stuck == best_stuck and cost < best_length):
				best_stuck = stuck
				best_length = cost
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

# --- Le déplacement, pas la correction ----------------------------------------

## Déplace un corps allongé de `from` vers `to` en GLISSANT sur ce qu'il rencontre.
##
## ⚠️ C'EST L'INVERSE DE `resolve_capsule()`, ET C'EST TOUT LE SUJET. Corriger APRÈS coup
## — laisser entrer puis repousser — produit exactement ce que le playtest du 2026-08-27 a
## nommé : « j'ai pu rentrer dans les murs, et quand on est repoussé c'est comme un aimant
## ou avec des ressorts ». Les deux plaintes sont le même défaut :
##
## - **on entre**, parce que la pénétration a lieu pour de bon avant d'être annulée ;
## - **ça ressort tout seul**, parce que l'annulation est un saut, et qu'elle se rejoue
##   contre la commande du joueur à chaque image. Le joueur pousse, le mur rend : un ressort.
##
## Ici, on ne pénètre jamais. On cherche le dernier point libre du trajet, puis on projette
## ce qui restait du mouvement SUR la surface. Le vaisseau longe le mur au lieu d'être
## avalé puis recraché — et un joueur qui longe comprend où est le mur.
static func slide_capsule(shapes: PlaneShapes, from: Vector2, to: Vector2, axis: Vector2,
		half_length: float, radius: float) -> Vector2:
	if shapes.size() == 0:
		return to
	if not capsule_blocks(shapes, to, axis, half_length, radius):
		return to
	var contact := _last_free(shapes, from, to, axis, half_length, radius)
	# La normale, c'est la direction dans laquelle le corps VOUDRAIT sortir à l'arrivée.
	# On la lit du dégagement plutôt que de la recalculer : une seule définition du « dehors ».
	var escape := resolve_capsule(shapes, to, axis, half_length, radius) - to
	if escape.length() < 0.0001:
		return contact
	var normal := escape.normalized()
	var remaining := to - contact
	var tangent := remaining - normal * remaining.dot(normal)
	var slid := contact + tangent
	if not capsule_blocks(shapes, slid, axis, half_length, radius):
		return slid
	return contact

## Le dernier point du segment où le corps tient encore. Recherche dichotomique : douze pas
## suffisent à descendre sous le millimètre sur un déplacement d'une image.
static func _last_free(shapes: PlaneShapes, from: Vector2, to: Vector2, axis: Vector2,
		half_length: float, radius: float) -> Vector2:
	if capsule_blocks(shapes, from, axis, half_length, radius):
		# Le départ est DÉJÀ pris — un mur a tourné dans le corps. Ce n'est pas au glissement
		# de régler ça : `PlayerFighterController` s'en dégage à vitesse bornée, ce qui se lit
		# comme une poussée et non comme un saut.
		return from
	var low := 0.0
	var high := 1.0
	for i in 12:
		var mid := (low + high) * 0.5
		if capsule_blocks(shapes, from.lerp(to, mid), axis, half_length, radius):
			high = mid
		else:
			low = mid
	return from.lerp(to, low)
