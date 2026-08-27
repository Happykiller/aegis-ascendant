extends "res://tests/test_case.gd"
## Le blindage rotatif du réacteur (plan « Reactor Chamber », lot 1).
##
## ⚠️ LE MODE D'ÉCHEC QUE CE FICHIER EXISTE POUR EMPÊCHER : un blindage dont les ouvertures
## ne se croisent JAMAIS enfermerait le joueur devant une cible intouchable, sans erreur,
## sans test rouge, et sans qu'il puisse rien y faire. Ce serait le défaut nommé au playtest
## — « une cible quasiment fixe » — en pire, puisqu'elle deviendrait inatteignable.
##
## C'est `ADR-0029` À L'ENVERS. Là, il fallait des périodes qui ne retombent jamais en
## rythme pour que l'œil ne repère pas la boucle. Ici il faut qu'elles se croisent souvent.
## Deux problèmes opposés, deux réglages opposés — et deux gardes opposées.

const SHIPPED := "res://resources/bosses/pale_leviathan_tuning.tres"

func _shipped_rings() -> Array[ReactorRing]:
	var tuning: LeviathanTuning = load(SHIPPED)
	return tuning.reactor_rings

func _any_opening(rings: Array[ReactorRing], age: float) -> bool:
	for i in 180:
		if ReactorRings.is_open(rings, float(i) * 2.0, age):
			return true
	return false

# --- Ce que le blindage doit garantir --------------------------------------

## LA garde. Sur toute la durée d'une plongée — et bien au-delà — un corridor doit exister
## quelque part sur le cercle. Le joueur n'attend pas : il se DÉPLACE.
func test_the_player_is_never_locked_out() -> void:
	var rings := _shipped_rings()
	assert_true(rings.size() >= 2, "le blindage livré a bien ses anneaux")
	var longest_lock := 0.0
	var lock := 0.0
	var step := 0.05
	for i in int(60.0 / step):
		if _any_opening(rings, float(i) * step):
			longest_lock = maxf(longest_lock, lock)
			lock = 0.0
		else:
			lock += step
	longest_lock = maxf(longest_lock, lock)
	assert_true(longest_lock <= 0.5,
		"blindage intégralement fermé pendant %.2f s d'affilée — le joueur y serait enfermé"
			% longest_lock)

## Et il doit VRAIMENT protéger : un blindage ouvert partout tout le temps ne serait pas un
## puzzle, ce serait une décoration.
##
## ⚠️ CETTE GARDE TENAIT UNE BORNE INVENTÉE (« < 35 % ») PENDANT QUE L'ÉQUILIBRAGE CALCULAIT
## AVEC 45 %. Elle était verte, et le combat n'en finissait pas : douze plongées à puissance
## maximale au playtest du 2026-08-27, parce que la géométrie livrée n'ouvrait que 13 % du
## temps. Deux chiffres sur le même fait, qui ne se parlaient pas — la panne exacte
## qu'`ADR-0024` a déjà coûtée au projet.
##
## Elle compare donc désormais la couverture RÉELLEMENT SIMULÉE à `ring_occupancy`, qui est
## la valeur dont `flux_reachable_per_dive()` déduit la santé du flux. Changer les ouvertures
## sans corriger l'estimation — ou l'inverse — rougit ici.
func test_the_shield_opens_as_often_as_the_balance_assumes() -> void:
	var rings := _shipped_rings()
	var open := 0
	var total := 0
	for i in 200:
		var age := float(i) * 0.13
		for k in 72:
			total += 1
			if ReactorRings.is_open(rings, float(k) * 5.0, age):
				open += 1
	var ratio := float(open) / float(total)
	var tuning: LeviathanTuning = load(SHIPPED)
	assert_true(absf(ratio - tuning.ring_occupancy) <= 0.06,
		("le blindage livré laisse tirer %.0f %% du temps, mais l'équilibrage dimensionne "
			+ "le flux comme s'il en laissait %.0f %%") % [ratio * 100.0, tuning.ring_occupancy * 100.0])
	assert_true(ratio < 0.70,
		"le corridor couvre %.0f %% du cercle — au-delà, il n'y a plus rien à chercher"
			% (ratio * 100.0))
	assert_true(ratio > 0.03,
		"le corridor ne couvre que %.1f %% du cercle — trop peu pour être trouvé"
			% (ratio * 100.0))

## Le corridor doit BOUGER : figé, le joueur s'y poste une fois et la phase redevient ce
## qu'elle était.
func test_the_corridor_moves() -> void:
	var rings := _shipped_rings()
	var moved := false
	for k in 72:
		var bearing := float(k) * 5.0
		if ReactorRings.is_open(rings, bearing, 0.0) != ReactorRings.is_open(rings, bearing, 2.0):
			moved = true
			break
	assert_true(moved, "le corridor s'est déplacé en deux secondes")

# --- La géométrie elle-même ------------------------------------------------

func test_an_aperture_is_open_at_its_own_centre() -> void:
	var ring := ReactorRing.new()
	ring.apertures = 3
	ring.aperture_deg = 40.0
	ring.speed_deg = 10.0
	ring.phase_deg = 0.0
	assert_true(ReactorRings.ring_open(ring, 0.0, 0.0), "au centre de l'ouverture")
	assert_true(ReactorRings.ring_open(ring, 120.0, 0.0), "et de la suivante, 120° plus loin")
	assert_false(ReactorRings.ring_open(ring, 60.0, 0.0), "mais pas entre les deux")

func test_an_aperture_travels_with_the_ring() -> void:
	var ring := ReactorRing.new()
	ring.apertures = 2
	ring.aperture_deg = 30.0
	ring.speed_deg = 90.0
	assert_true(ReactorRings.ring_open(ring, 0.0, 0.0), "ouverte ici à t=0")
	assert_false(ReactorRings.ring_open(ring, 0.0, 0.5), "et fermée un demi-tour de plus tard")
	assert_true(ReactorRings.ring_open(ring, 45.0, 0.5), "l'ouverture a suivi la rotation")

## `nearest_opening` désigne l'ouverture vers laquelle ALLER : la plus proche, pas une autre
## à l'opposé du cercle. Un repère qui pointe le mauvais côté est pire que pas de repère.
func test_the_nearest_opening_is_the_one_you_should_fly_to() -> void:
	var rings := _shipped_rings()
	var from := 90.0
	var found := ReactorRings.nearest_opening(rings, from, 3.7)
	assert_true(found != ReactorRings.NO_OPENING, "il y a bien une ouverture")
	assert_true(ReactorRings.is_open(rings, found, 3.7), "et elle est ouverte")
	var gap := absf(rad_to_deg(angle_difference(deg_to_rad(found), deg_to_rad(from))))
	for k in 72:
		var other := float(k) * 5.0
		if not ReactorRings.is_open(rings, other, 3.7):
			continue
		var other_gap := absf(rad_to_deg(angle_difference(deg_to_rad(other), deg_to_rad(from))))
		assert_true(gap <= other_gap + 2.5,
			"aucune ouverture plus proche que celle désignée (%.0f° contre %.0f°)" % [gap, other_gap])

## Une Resource sans anneau doit rendre le comportement d'AVANT : le flux atteignable en
## permanence. C'est ce qui permet de désarmer le puzzle si le playtest le condamne.
func test_no_rings_means_no_shield() -> void:
	var none: Array[ReactorRing] = []
	assert_true(ReactorRings.is_open(none, 123.0, 4.5), "sans anneau, tout est ouvert")

# --- Le laser balayant (lot 2) ----------------------------------------------

## ⚠️ LA GARDE QUI COMPTE POUR LE LASER. Il met la pression, il ne CONDAMNE jamais : il doit
## toujours exister un corridor à la fois OUVERT et HORS du faisceau. Un laser qui se poserait
## sur la seule ouverture enfermerait le joueur — le même mode d'échec que le blindage, par un
## autre chemin, et tout aussi silencieux.
const LASER_BLOCK_DEG := 14.0

func _laser_bearing(tuning: LeviathanTuning, age: float) -> float:
	return fposmod(tuning.sweep_speed_deg * age, 360.0)

func test_the_sweep_never_seals_the_last_corridor() -> void:
	var tuning: LeviathanTuning = load(SHIPPED)
	var rings := tuning.reactor_rings
	var longest := 0.0
	var sealed := 0.0
	var step := 0.05
	for i in int(90.0 / step):
		var age := float(i) * step
		var laser := _laser_bearing(tuning, age)
		var free := false
		for k in 180:
			var bearing := float(k) * 2.0
			if not ReactorRings.is_open(rings, bearing, age):
				continue
			if absf(rad_to_deg(angle_difference(deg_to_rad(bearing), deg_to_rad(laser)))) > LASER_BLOCK_DEG:
				free = true
				break
		if free:
			longest = maxf(longest, sealed)
			sealed = 0.0
		else:
			sealed += step
	longest = maxf(longest, sealed)
	assert_true(longest <= 0.4,
		"aucun corridor libre pendant %.2f s d'affilée — le joueur y serait enfermé" % longest)

## Le faisceau doit tourner à contresens de l'anneau extérieur : dans le même sens, ils
## dériveraient ensemble et la pression deviendrait un décor.
func test_the_sweep_turns_against_the_outer_ring() -> void:
	var tuning: LeviathanTuning = load(SHIPPED)
	assert_true(tuning.reactor_rings.size() > 0, "il y a bien un anneau extérieur")
	var outer: ReactorRing = tuning.reactor_rings[0]
	assert_true(signf(tuning.sweep_speed_deg) != signf(outer.speed_deg),
		"laser %.0f °/s contre anneau %.0f °/s — mêmes sens, ils dériveraient ensemble"
			% [tuning.sweep_speed_deg, outer.speed_deg])

## ⚠️ ET IL S'ARME APRÈS COUP. Le joueur qui vient d'entrer doit voir d'où part le faisceau
## et dans quel sens il tourne AVANT de pouvoir en mourir. Une mort qu'on ne pouvait pas lire
## venir n'est pas une difficulté, c'est une injustice — la loi que ce projet applique déjà
## à toute attaque lourde.
func test_the_sweep_is_harmless_when_the_player_arrives() -> void:
	var tuning: LeviathanTuning = load(SHIPPED)
	assert_true(tuning.sweep_arm_delay > 0.5,
		"délai d'armement de %.2f s — en dessous, on meurt avant d'avoir vu le faisceau"
			% tuning.sweep_arm_delay)
	assert_true(tuning.sweep_arm_delay < tuning.dive_time * 0.35,
		"mais il ne mange pas la plongée : %.2f s sur %.1f s" % [tuning.sweep_arm_delay, tuning.dive_time])

# --- Les murs sont des CORPS (playtest du 2026-08-27) -----------------------

## ⚠️ « Faut leur donner un corps, pas qu'un halo de couleur, et faut integrer au jeu un
## moteur de collision : on ne doit pas pouvoir franchir les murs. » La collision est
## analytique — un anneau est un anneau — donc elle se teste en headless comme le reste.
func test_a_wall_blocks_where_it_is_solid_and_lets_through_where_it_opens() -> void:
	var ring := ReactorRing.new()
	ring.apertures = 2
	ring.aperture_deg = 60.0
	ring.speed_deg = 10.0
	ring.phase_deg = 0.0
	ring.radius = 4.0
	ring.thickness = 1.0
	# Au centre d'une ouverture : on passe.
	assert_false(ReactorRings.blocks(ring, Vector2(4.0, 0.0), 0.0), "l'ouverture laisse passer")
	# Entre deux ouvertures : c'est un mur.
	assert_true(ReactorRings.blocks(ring, Vector2(4.0, 0.0).rotated(deg_to_rad(90.0)), 0.0),
		"le plein bloque")
	# Loin du rayon : rien a bloquer.
	assert_false(ReactorRings.blocks(ring, Vector2(9.0, 0.0).rotated(deg_to_rad(90.0)), 0.0),
		"au-dela du mur, il n'y a plus de mur")

## Repoussé, le joueur doit se retrouver DEHORS — et du cote d'ou il venait.
func test_being_pushed_out_never_leaves_you_inside_a_wall() -> void:
	var rings := _shipped_rings()
	for step in 240:
		var age := float(step) * 0.11
		# Un point tire un peu partout dans l'arene.
		var probe := Vector2(cos(age * 2.3), sin(age * 1.7)) * (1.0 + fmod(age, 5.5))
		var pushed := ReactorRings.push_out(rings, probe, age)
		for ring in rings:
			assert_false(ReactorRings.blocks(ring, pushed, age),
				"apres poussee, on n'est plus dans le mur (r=%.2f)" % pushed.length())

## Et il ne doit pas etre TELEPORTE : la poussee est radiale et courte, elle ne traverse
## jamais l'anneau de part en part.
func test_the_push_is_short_and_radial() -> void:
	var rings := _shipped_rings()
	for step in 200:
		var age := float(step) * 0.13
		var probe := Vector2(cos(age * 1.9), sin(age * 2.7)) * (1.5 + fmod(age, 4.0))
		var pushed := ReactorRings.push_out(rings, probe, age)
		if pushed.is_equal_approx(probe):
			continue
		assert_true(absf(pushed.angle() - probe.angle()) < 0.001,
			"la poussee garde l'azimut : elle est radiale")
		assert_true(pushed.distance_to(probe) < 2.0,
			"et elle est courte (%.2f u) — pas une teleportation" % pushed.distance_to(probe))

## ⚠️ ET LE REGLAGE LIVRE N'A PLUS DE VERROUS. Decision de playtest, gardee ici pour qu'un
## `node_count` remis a quatre par megarde se signale.
func test_the_shipped_fight_has_no_orbital_locks() -> void:
	var tuning: LeviathanTuning = load(SHIPPED)
	assert_eq(tuning.node_count, 0,
		"les verrous sont eteints : « les boules vertes, c'est pas logique »")

## Les deux murs laissent le passage d'un chasseur et demi entre eux.
func test_the_two_walls_leave_room_to_fly_between_them() -> void:
	var rings := _shipped_rings()
	assert_eq(rings.size(), 2, "deux murs")
	var inner: ReactorRing = rings[1] if rings[1].radius < rings[0].radius else rings[0]
	var outer: ReactorRing = rings[0] if rings[1].radius < rings[0].radius else rings[1]
	var gap := (outer.radius - outer.thickness * 0.5) - (inner.radius + inner.thickness * 0.5)
	assert_true(gap > 1.5 * SHIP_WIDTH * 0.8 and gap < 1.5 * SHIP_WIDTH * 1.35,
		"%.2f u entre les deux murs, pour ~%.2f attendus (1,5 largeur de chasseur)"
			% [gap, 1.5 * SHIP_WIDTH])

## Largeur du chasseur, relevee sur la coque livree : les canons de bout d'aile sont a
## x = ±0,853, soit ~1,7 u d'envergure utile.
const SHIP_WIDTH := 1.75

## ⚠️ L'INVARIANT QUI COMPTE MAINTENANT : la ligne de tir est soit coupee — et il existe UN
## premier point de contact — soit degagee, et il n'y en a aucun. Jamais les deux, jamais
## aucun des deux. C'est ce qui garantit qu'une gerbe de deviation nait la ou le bolt
## s'arrete, et non ailleurs.
func test_a_blocked_line_always_names_where_it_is_blocked() -> void:
	var rings := _shipped_rings()
	for step in 300:
		var age := float(step) * 0.09
		var from := Vector2(-3.0 + fmod(age, 6.0), -8.0)
		var hit := ReactorRings.first_hit_along(rings, from, Vector2.ZERO, age, 0.35)
		var blocked := ReactorRings.line_blocked(rings, from, Vector2.ZERO, age, 0.35)
		assert_eq(hit.is_finite(), blocked,
			"coupee <=> un point de contact nomme (age %.2f)" % age)
		if hit.is_finite():
			assert_true(hit.distance_to(from) <= from.length() + 0.01,
				"et ce point est SUR le trajet, entre le tireur et le noyau")

## Le corps du chasseur ne franchit pas le bord d'une ouverture par lequel son centre passe.
func test_a_wide_body_does_not_slip_through_an_edge_its_centre_clears() -> void:
	var ring := ReactorRing.new()
	ring.apertures = 2
	ring.aperture_deg = 40.0
	ring.speed_deg = 10.0
	ring.phase_deg = 0.0
	ring.radius = 4.0
	ring.thickness = 1.0
	# Juste au bord de l'ouverture : le centre passe (19° < 20°), le corps non.
	var edge := Vector2(4.0, 0.0).rotated(deg_to_rad(19.0))
	assert_false(ReactorRings.blocks(ring, edge, 0.0), "le CENTRE passe au bord")
	assert_true(ReactorRings.blocks_body(ring, edge, 0.85, 0.0),
		"mais le corps, large de 0,85, touche encore le plein")
