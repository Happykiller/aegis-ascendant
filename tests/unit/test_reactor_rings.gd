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
## puzzle, ce serait une décoration. La garde tient les deux bouts.
func test_the_shield_actually_shields() -> void:
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
	assert_true(ratio < 0.35,
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
