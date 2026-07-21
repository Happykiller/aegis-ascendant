extends "res://tests/test_case.gd"
## Animation de la citadelle (BRIEF-0032) — vérifiée par CALCUL, pas par capture.
##
## Une capture d'écran ne peut rien dire ici : la citadelle porte aussi un lacet
## global et la caméra tangue, si bien qu'une carte de différence entre deux images
## montre 51 % de pixels changés sans rien prouver sur l'indépendance des tourelles.
## C'est le cas d'école de `pratique-verifier-par-test.md` : l'événement à observer
## est temporel, la capture est le mauvais outil.
##
## Les deux classes n'utilisent aucun autoload et ne lisent pas l'arbre : elles
## s'instancient à la main, `_ready()` s'appelle explicitement, et `_process()` est
## piloté par un pas de temps injecté.

const TurretScript := preload("res://scripts/fortress/citadel_turret.gd")
const BeaconScript := preload("res://scripts/fortress/citadel_beacon.gd")

const STEP := 0.05
const SAMPLES := 2400   # 120 s simulées — deux fois la plus longue période en jeu

## Fait tourner une pièce et retourne l'échantillonnage demandé.
func _run(piece: Node3D, sample: Callable) -> Array:
	var out: Array = []
	for i in SAMPLES:
		piece.call("_process", STEP)
		out.append(sample.call(piece))
	return out

func _turret(index: int) -> Node3D:
	var t: Node3D = TurretScript.new()
	t.call("setup", index)
	t.call("_ready")
	return t

# --- Tourelles ---------------------------------------------------------------

func test_turret_sweep_stays_within_its_amplitude() -> void:
	# Une tourelle qui dépasse son secteur pointerait à travers la coque.
	var turret := _turret(0)
	var yaws: Array = _run(turret, func(p: Node3D) -> float: return rad_to_deg(p.rotation.y))
	var peak: float = 0.0
	for y: float in yaws:
		peak = maxf(peak, absf(y))
	assert_true(peak <= TurretScript.SWEEP_DEG + 0.01,
		"amplitude tenue (%.1f deg <= %.1f)" % [peak, TurretScript.SWEEP_DEG])
	assert_true(peak > TurretScript.SWEEP_DEG * 0.9,
		"le secteur est reellement balaye (%.1f deg)" % peak)
	turret.free()

func test_no_two_turrets_march_in_lockstep() -> void:
	# LE test de ce lot. Six tourelles synchrones lisent comme un metronome et
	# trahissent qu'un seul script les pilote — c'est precisement ce que l'angle
	# d'or et le decalage de periode existent pour empecher.
	var series: Array = []
	for i in 6:
		var turret := _turret(i)
		series.append(_run(turret, func(p: Node3D) -> float: return rad_to_deg(p.rotation.y)))
		turret.free()
	var worst: float = 0.0
	var worst_pair: String = ""
	for a in 6:
		for b in range(a + 1, 6):
			var together: int = 0
			for k in SAMPLES:
				if absf(series[a][k] - series[b][k]) < 1.0:
					together += 1
			var ratio: float = float(together) / float(SAMPLES)
			if ratio > worst:
				worst = ratio
				worst_pair = "%d/%d" % [a, b]
	# Deux sinusoides dephasees se croisent forcement : on n'exige pas zero, on
	# exige qu'aucune paire ne passe l'essentiel du temps ensemble.
	assert_true(worst < 0.10,
		"aucune paire en phase (pire : %s a %.1f %% du temps)" % [worst_pair, worst * 100.0])

func test_turrets_do_not_all_start_at_the_same_pose() -> void:
	# Sans avance de phase a l'initialisation, la premiere seconde montre six
	# tourelles alignees — le defaut le plus visible, et le plus court.
	var poses: Array[float] = []
	for i in 6:
		var turret := _turret(i)
		poses.append(rad_to_deg(turret.rotation.y))
		turret.free()
	var spread: float = poses.max() - poses.min()
	assert_true(spread > 20.0, "poses initiales dispersees (%.1f deg d'ecart)" % spread)

# --- Balises -----------------------------------------------------------------

func test_beacon_never_drifts_away_from_its_anchor() -> void:
	# Le piege classique : `position += ...` accumule, et la balise s'en va pour de
	# bon au bout de quelques minutes. L'animation doit etre un DECALAGE par rapport
	# a une pose de repos relevee une fois.
	var beacon: Node3D = BeaconScript.new()
	beacon.position = Vector3(3.0, 1.0, -2.0)
	beacon.call("setup", 1)
	beacon.call("_ready")
	var rest := Vector3(3.0, 1.0, -2.0)
	var peak: float = 0.0
	var last := Vector3.ZERO
	for i in SAMPLES:
		beacon.call("_process", STEP)
		peak = maxf(peak, (beacon.position - rest).length())
		last = beacon.position
	var bound: float = Vector3(
		BeaconScript.ORBIT_RADIUS, BeaconScript.RISE, BeaconScript.ORBIT_RADIUS).length()
	assert_true(peak <= bound + 0.001,
		"reste dans son enveloppe (%.3f m <= %.3f)" % [peak, bound])
	assert_true((last - rest).length() <= bound + 0.001,
		"toujours pres de l'ancrage apres 120 s (%.3f m)" % (last - rest).length())
	beacon.free()

func test_beacons_are_not_synchronised() -> void:
	var positions: Array[Vector3] = []
	for i in 3:
		var beacon: Node3D = BeaconScript.new()
		beacon.call("setup", i)
		beacon.call("_ready")
		for k in 200:
			beacon.call("_process", STEP)
		positions.append(beacon.position)
		beacon.free()
	for a in 3:
		for b in range(a + 1, 3):
			assert_true(positions[a].distance_to(positions[b]) > 0.05,
				"balises %d et %d dissociees" % [a, b])
