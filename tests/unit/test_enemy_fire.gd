extends "res://tests/test_case.gd"
## Schémas de tir (EnemyFire) — géométrie pure, testée sans scène ni projectile.
##
## Le pendant de test_enemy_path.gd : là-bas on vérifie où va la coque, ici où part
## le coup. Et la même règle dure — deux schémas doivent différer par leur FORME.

const FROM := Vector2(0.0, 4.0)
const PLAYER := Vector2(3.0, -2.0)
const ALL_FIRES: Array[int] = [
	EnemyData.Fire.SINGLE, EnemyData.Fire.FAN, EnemyData.Fire.AIMED, EnemyData.Fire.RADIAL,
]

func _data(fire: int, burst: int = 5) -> EnemyData:
	var data := EnemyData.new()
	data.fire = fire
	data.burst_count = burst
	return data

## Non-régression : les neuf familles écrites avant cet axe n'ont pas de champ
## `fire` dans leur .tres, donc elles héritent de l'indice 0. Ce test dit que
## l'indice 0 n'a pas bougé d'un iota — un coup, droit vers le bas, un seul.
func test_single_still_shoots_exactly_one_bolt_straight_down() -> void:
	var data := _data(EnemyData.Fire.SINGLE)
	assert_eq(EnemyFire.shot_count(data), 1, "SINGLE tire un coup")
	var dir := EnemyFire.direction(data, 0, 0, FROM, PLAYER)
	assert_true(dir.distance_to(EnemyFire.DIR_DOWN) < 0.0001,
		"et il part droit vers le bas (obtenu %s)" % dir)

## Une unité peut menacer sans tirer : aura, aspiration, contact. Zéro coup est une
## réponse valide, pas un cas d'erreur.
func test_none_fires_nothing_at_all() -> void:
	assert_eq(EnemyFire.shot_count(_data(EnemyData.Fire.NONE)), 0, "NONE ne tire pas")

# --- La différence qui compte : voir, ou ne pas voir -------------------------
#
# FAN et AIMED ne se distinguent PAS par leur ouverture. On peut élargir l'un et
# resserrer l'autre autant qu'on veut : ils resteront deux choses différentes,
# parce que l'un regarde le joueur et l'autre pas. C'est ça qu'on teste.

func test_aimed_follows_the_player_wherever_he_goes() -> void:
	var data := _data(EnemyData.Fire.AIMED)
	var left := EnemyFire.direction(data, 0, 2, FROM, Vector2(-8.0, -2.0))
	var right := EnemyFire.direction(data, 0, 2, FROM, Vector2(8.0, -2.0))
	assert_true(left.x < -0.4, "visé à gauche, le coup part à gauche (%s)" % left)
	assert_true(right.x > 0.4, "visé à droite, il part à droite (%s)" % right)

func test_fan_never_looks_at_the_player() -> void:
	var data := _data(EnemyData.Fire.FAN)
	for i in EnemyFire.shot_count(data):
		var here := EnemyFire.direction(data, 0, i, FROM, Vector2(-8.0, -2.0))
		var there := EnemyFire.direction(data, 0, i, FROM, Vector2(8.0, -2.0))
		assert_true(here.distance_to(there) < 0.0001,
			"le coup %d est le même où que soit le joueur" % i)

## L'éventail couvre un couloir : symétrique autour de la verticale, et large.
func test_fan_opens_symmetrically_around_straight_down() -> void:
	var data := _data(EnemyData.Fire.FAN)
	var count := EnemyFire.shot_count(data)
	var first := EnemyFire.direction(data, 0, 0, FROM, PLAYER)
	var last := EnemyFire.direction(data, 0, count - 1, FROM, PLAYER)
	assert_almost_eq(first.x, -last.x, 0.0001, "les deux bords sont symétriques")
	assert_true(absf(first.angle_to(last)) > deg_to_rad(40.0),
		"et l'éventail est large (%f°)" % rad_to_deg(absf(first.angle_to(last))))

## Une couronne doit être une couronne : des directions réparties sur tout le tour.
## La somme de vecteurs unitaires régulièrement espacés vaut zéro — c'est la mesure
## la plus courte de « aucune direction n'est privilégiée ».
func test_radial_covers_the_whole_circle_evenly() -> void:
	var data := _data(EnemyData.Fire.RADIAL, 12)
	var sum := Vector2.ZERO
	for i in EnemyFire.shot_count(data):
		sum += EnemyFire.direction(data, 0, i, FROM, PLAYER)
	assert_true(sum.length() < 0.0001,
		"la couronne ne privilégie aucune direction (résidu %f)" % sum.length())

## Deux couronnes de suite ne doivent pas superposer leurs trous, sinon rester
## immobile dans un interstice serait une stratégie gagnante.
func test_consecutive_rings_interleave_their_gaps() -> void:
	var data := _data(EnemyData.Fire.RADIAL, 8)
	var step := TAU / 8.0
	var first := EnemyFire.direction(data, 0, 0, FROM, PLAYER)
	var second := EnemyFire.direction(data, 1, 0, FROM, PLAYER)
	assert_almost_eq(absf(first.angle_to(second)), step * EnemyFire.RADIAL_PHASE, 0.0001,
		"la seconde couronne est décalée d'un demi-intervalle")

# --- La règle de variété ------------------------------------------------------

## Deux schémas distincts doivent produire des salves distinctes. Si deux d'entre
## eux rendent les mêmes directions, ce ne sont pas deux comportements : c'est un
## seul, réglé deux fois — exactement le piège qu'on a déjà évité aux trajectoires.
func test_no_two_fire_patterns_produce_the_same_salvo() -> void:
	var shapes: Dictionary = {}
	for fire in ALL_FIRES:
		var data := _data(fire, 5)
		var dirs: Array[Vector2] = []
		for i in EnemyFire.shot_count(data):
			dirs.append(EnemyFire.direction(data, 0, i, FROM, PLAYER))
		shapes[fire] = dirs
	for a in ALL_FIRES:
		for b in ALL_FIRES:
			if a >= b:
				continue
			var different: bool = shapes[a].size() != shapes[b].size()
			if not different:
				for i in shapes[a].size():
					if shapes[a][i].distance_to(shapes[b][i]) > 0.2:
						different = true
						break
			assert_true(different, "les schémas %d et %d sont la même salve" % [a, b])

# --- Les gardes ---------------------------------------------------------------

## Un coup unique dans un éventail part au CENTRE, pas sur un bord. Sans ce cas,
## `count - 1` vaudrait zéro et l'ouverture se diviserait par elle-même.
func test_a_lone_shot_leaves_from_the_centre_of_its_fan() -> void:
	var dir := EnemyFire.direction(_data(EnemyData.Fire.FAN, 1), 0, 0, FROM, PLAYER)
	assert_true(dir.distance_to(EnemyFire.DIR_DOWN) < 0.0001,
		"un éventail d'un seul coup part droit (obtenu %s)" % dir)

## Viser un point où l'on se trouve déjà : normaliser un vecteur nul rend ZERO, et
## une balle de vitesse nulle resterait vissée sur la coque jusqu'à son TTL, sans
## une seule erreur au journal. On retombe sur le tir droit.
func test_aiming_at_your_own_position_falls_back_to_straight_down() -> void:
	var dir := EnemyFire.direction(_data(EnemyData.Fire.AIMED, 1), 0, 0, FROM, FROM)
	assert_true(dir.distance_to(EnemyFire.DIR_DOWN) < 0.0001,
		"la visée dégénérée retombe sur le bas (obtenu %s)" % dir)

## Toute direction rendue est unitaire : la vitesse d'une balle vient de son
## ProjectileData, jamais de la longueur du vecteur qu'on lui passe.
func test_every_direction_is_a_unit_vector() -> void:
	for fire in ALL_FIRES:
		var data := _data(fire, 7)
		for i in EnemyFire.shot_count(data):
			var dir := EnemyFire.direction(data, 3, i, FROM, PLAYER)
			assert_almost_eq(dir.length(), 1.0, 0.0001,
				"schéma %d, coup %d : direction unitaire" % [fire, i])
