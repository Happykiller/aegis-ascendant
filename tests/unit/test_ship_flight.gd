extends "res://tests/test_case.gd"
## Pièces mobiles du Specter-9 (BRIEF-0033) — vérifiées par calcul.
##
## L'enjeu n'est pas cosmétique : la forge a **mesuré** le dégagement des volets dans
## l'échancrure d'aile et relevé un plafond mécanique de **±13°** (rapport §4, marge
## de 1,94 mm à −12°). Au-delà, le volet traverse la cloison. Un test est le seul
## endroit où cette limite peut survivre à un réglage distrait.
##
## `ShipFlight` ne lit ni input ni autoload : on lui pousse deux ratios. Elle est donc
## instanciable à la main, avec une fausse coque faite de Node3D nommés.

const ShipFlightScript := preload("res://scripts/fx/ship_flight.gd")

## Plafond mécanique de la coque. Ce n'est PAS le réglage de `ShipFlight` : c'est la
## limite au-delà de laquelle la géométrie se traverse.
const HARD_LIMIT_DEG := 13.0

func _rig() -> Array:
	var hull := Node3D.new()
	for part_name in ["Flap_L", "Flap_R", "Nozzle_L", "Nozzle_R"]:
		var part := Node3D.new()
		part.name = part_name
		hull.add_child(part)
	var flight: Node = ShipFlightScript.new()
	hull.add_child(flight)
	flight.call("_ready")
	return [hull, flight]

func _settle(flight: Node, steps: int = 400, step: float = 0.05) -> void:
	for i in steps:
		flight.call("_process", step)

# --- Volets --------------------------------------------------------------

func test_flaps_deflect_in_opposition() -> void:
	# De vrais ailerons : l'un descend quand l'autre monte. Les faire battre
	# ensemble raconterait un freinage, pas un virage.
	var rig := _rig()
	rig[1].call("set_bank", 1.0)
	_settle(rig[1])
	var l: float = (rig[0].get_node("Flap_L") as Node3D).rotation.x
	var r: float = (rig[0].get_node("Flap_R") as Node3D).rotation.x
	assert_true(absf(l) > 0.01, "le volet babord se deporte (%.3f rad)" % l)
	assert_true(absf(l + r) < 1e-5, "les deux volets sont en opposition (%.3f / %.3f)" % [l, r])
	rig[0].free()

func test_flaps_never_pass_the_mechanical_ceiling() -> void:
	# LE test de ce lot. On pousse la commande a fond dans les deux sens, longtemps.
	var rig := _rig()
	var peak: float = 0.0
	for pass_index in 2:
		rig[1].call("set_bank", 1.0 if pass_index == 0 else -1.0)
		for i in 400:
			rig[1].call("_process", 0.05)
			peak = maxf(peak, absf(rad_to_deg((rig[0].get_node("Flap_L") as Node3D).rotation.x)))
	assert_true(peak <= HARD_LIMIT_DEG,
		"le volet reste sous le plafond mecanique (%.2f deg <= %.1f)" % [peak, HARD_LIMIT_DEG])
	assert_true(peak > 8.0, "le debattement reste visible (%.2f deg)" % peak)
	rig[0].free()

func test_a_long_frame_does_not_overshoot() -> void:
	# Le piege du lissage : `lerp(a, b, delta * k)` avec un delta d'une seconde donne
	# un facteur de 9 — la piece DEPASSE sa cible, donc son plafond mecanique. Un
	# chargement, un alt-tab, et le volet traverse l'aile.
	var rig := _rig()
	rig[1].call("set_bank", 1.0)
	rig[1].call("_process", 1.0)   # image d'une seconde
	var deg: float = absf(rad_to_deg((rig[0].get_node("Flap_L") as Node3D).rotation.x))
	assert_true(deg <= HARD_LIMIT_DEG,
		"pas de depassement sur une image longue (%.2f deg)" % deg)
	rig[0].free()

# --- Tuyeres -------------------------------------------------------------

func test_nozzles_only_ever_open() -> void:
	# Elles sont modelees FERMEES au repos : une echelle sous 1 les ferait imploser
	# dans la nacelle.
	var rig := _rig()
	var floor_scale: float = 9.0
	for ratio in [0.0, 1.0, 0.0]:
		rig[1].call("set_thrust", ratio)
		for i in 200:
			rig[1].call("_process", 0.05)
			floor_scale = minf(floor_scale, (rig[0].get_node("Nozzle_L") as Node3D).scale.x)
	assert_true(floor_scale >= 0.999, "l'echelle ne descend jamais sous 1 (%.4f)" % floor_scale)
	rig[0].free()

func test_thrust_opens_the_nozzles() -> void:
	var rig := _rig()
	rig[1].call("set_thrust", 1.0)
	_settle(rig[1])
	var open: float = (rig[0].get_node("Nozzle_L") as Node3D).scale.x
	assert_true(open > 1.3, "pleine poussee ouvre les petales (x%.2f)" % open)
	# La profondeur ne bouge pas : seuls les petales s'ecartent, la tuyere ne
	# s'allonge pas.
	assert_true(absf((rig[0].get_node("Nozzle_L") as Node3D).scale.z - 1.0) < 1e-5,
		"la tuyere ne s'allonge pas")
	rig[0].free()

func test_a_hull_without_moving_parts_degrades_quietly() -> void:
	# Les cinq autres coques du jeu n'ont pas de pieces mobiles. Elles doivent
	# continuer de voler, pas planter.
	var bare := Node3D.new()
	assert_true(ShipFlightScript.apply(bare) == null, "coque sans volet : aucune animation, aucune erreur")
	bare.free()
