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

## Plafonds MÉCANIQUES de la coque, mesurés par la forge et remesurés à chaque build
## (BRIEF-0035-report). Ce ne sont PAS les réglages de `ShipFlight` : ce sont les
## limites au-delà desquelles la géométrie se traverse elle-même.
const HARD_LIMIT_DEG := 18.5        # volets — échancrure d'aile
const HARD_SWEEP_DEG := 32.25       # ailes — peau de nacelle

## Les volets sont des ENFANTS des ailes depuis BRIEF-0035 : le banc d'essai doit
## reproduire cette imbrication, sinon il valide une structure qui n'existe plus.
func _rig() -> Array:
	var hull := Node3D.new()
	for side in ["L", "R"]:
		var wing := Node3D.new()
		wing.name = "Wing_" + side
		hull.add_child(wing)
		var flap := Node3D.new()
		flap.name = "Flap_" + side
		wing.add_child(flap)
	for part_name in ["Nozzle_L", "Nozzle_R"]:
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
	var l: float = (rig[0].get_node("Wing_L/Flap_L") as Node3D).rotation.x
	var r: float = (rig[0].get_node("Wing_R/Flap_R") as Node3D).rotation.x
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
			peak = maxf(peak, absf(rad_to_deg((rig[0].get_node("Wing_L/Flap_L") as Node3D).rotation.x)))
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
	var deg: float = absf(rad_to_deg((rig[0].get_node("Wing_L/Flap_L") as Node3D).rotation.x))
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

# --- Fleche des ailes ----------------------------------------------------

func test_wings_sweep_back_in_mirror() -> void:
	# Meme piege que les volets, avec une consequence pire : une rotation de meme
	# signe des deux cotes enverrait l'aile tribord vers le NEZ au lieu de la poupe.
	var rig := _rig()
	rig[1].call("set_thrust", 1.0)
	_settle(rig[1])
	var l: float = (rig[0].get_node("Wing_L") as Node3D).rotation.y
	var r: float = (rig[0].get_node("Wing_R") as Node3D).rotation.y
	assert_true(absf(l) > 0.1, "l'aile babord se replie (%.3f rad)" % l)
	assert_true(absf(l + r) < 1e-5, "les deux ailes sont en miroir (%.3f / %.3f)" % [l, r])
	rig[0].free()

func test_wing_sweep_never_passes_the_mechanical_ceiling() -> void:
	# 32,25 deg mesures : au-dela l'aile traverse la peau de nacelle.
	var rig := _rig()
	var peak: float = 0.0
	for phase in [1.0, 0.0, 1.0]:
		rig[1].call("set_thrust", phase)
		for i in 300:
			rig[1].call("_process", 0.05)
			peak = maxf(peak, absf(rad_to_deg((rig[0].get_node("Wing_L") as Node3D).rotation.y)))
	assert_true(peak <= HARD_SWEEP_DEG,
		"la fleche reste sous le plafond mecanique (%.2f deg <= %.2f)" % [peak, HARD_SWEEP_DEG])
	assert_true(peak > 20.0, "la fleche est franchement visible (%.2f deg)" % peak)
	rig[0].free()

func test_wings_are_deployed_at_rest() -> void:
	# Position de repos = DEPLOYEE : c'est l'etat que le .glb montre et que le
	# contrat de bbox mesure. Des ailes repliees au repos feraient mentir les deux.
	var rig := _rig()
	rig[1].call("set_thrust", 0.0)
	_settle(rig[1])
	assert_true(absf((rig[0].get_node("Wing_L") as Node3D).rotation.y) < 0.02,
		"au ralenti, les ailes sont ouvertes")
	rig[0].free()

func test_a_hull_without_moving_parts_degrades_quietly() -> void:
	# Les cinq autres coques du jeu n'ont pas de pieces mobiles. Elles doivent
	# continuer de voler, pas planter.
	var bare := Node3D.new()
	assert_true(ShipFlightScript.apply(bare) == null, "coque sans volet : aucune animation, aucune erreur")
	bare.free()

# --- ADR-0044 : les familles optionnelles -----------------------------------

## Plafonds MECANIQUES de la cellule-temoin, MESURES par le build de `specter_9_c`
## (balayage BVH, pas 1 deg, jeu 2,5 mm — log du 2026-09-04). Les pieces sans butee
## (rampe, grappin, verriere) recoivent la borne au-dela de laquelle elles racontent
## autre chose (planche des mecanismes : 30 / 150 / 70).
const HARD_PETAL_DEG := 30.0
const HARD_YAW_DEG := 7.0
const HARD_AIRBRAKE_DEG := 94.0
const HARD_INTAKE_DEG := 30.0
const HARD_RUDDER_DEG := 32.0
const HARD_GRAPPLE_DEG := 150.0
const HARD_CANOPY_DEG := 70.0

## La coque de la cellule-temoin, en Node3D nommes : les six pieces d'avant, plus
## douze petales par tuyere posés sur un cercle de rayon 0,1 dans le repere de la
## tuyere (pivot sur l'axe, plan des charnieres — la contrainte du brief), et les
## familles d'ADR-0044.
func _rich_rig() -> Array:
	var rig := _rig()
	var hull: Node3D = rig[0]
	for side in ["L", "R"]:
		var nozzle := hull.get_node("Nozzle_" + side) as Node3D
		for k in 12:
			var petal := Node3D.new()
			petal.name = "Petal_%s_%02d" % [side, k]
			var phi := TAU * k / 12.0
			petal.position = Vector3(0.1 * cos(phi), 0.1 * sin(phi), 0.0)
			nozzle.add_child(petal)
		for family in ["Airbrake_", "Intake_", "Rudder_", "Grapple_"]:
			var part := Node3D.new()
			part.name = family + side
			hull.add_child(part)
	var canopy := Node3D.new()
	canopy.name = "Canopy"
	hull.add_child(canopy)
	# `_ready` a deja tourne sur le rig nu : on rebranche sur la coque riche.
	rig[1].call("_ready")
	return rig

## Le point d'un petale a 10 cm en arriere de sa charniere (+Z Godot = vers la poupe),
## dans le repere de la tuyere : c'est sa POINTE, et c'est elle qui doit s'ecarter.
static func _petal_tip(petal: Node3D) -> Vector3:
	return petal.position + petal.quaternion * Vector3(0.0, 0.0, 0.1)

func test_petals_open_outward_at_full_thrust() -> void:
	# LE test du lot : l'axe de charniere est DERIVE de la position radiale du petale.
	# Un signe faux fermerait les douze petales vers l'axe, les uns dans les autres.
	var rig := _rich_rig()
	var nozzle := rig[0].get_node("Nozzle_L") as Node3D
	var closed: Array[float] = []
	for k in 12:
		var petal := nozzle.get_node("Petal_L_%02d" % k) as Node3D
		closed.append(Vector2(_petal_tip(petal).x, _petal_tip(petal).y).length())
	rig[1].call("set_thrust", 1.0)
	_settle(rig[1])
	for k in 12:
		var petal := nozzle.get_node("Petal_L_%02d" % k) as Node3D
		var radius := Vector2(_petal_tip(petal).x, _petal_tip(petal).y).length()
		assert_true(radius > closed[k] + 0.02,
			"petale %d : la pointe s'ecarte de l'axe (%.3f -> %.3f)" % [k, closed[k], radius])
	assert_true(absf(nozzle.scale.x - 1.0) < 1e-6, "avec des petales, la tuyere ne change plus d'echelle")
	rig[0].free()

func test_petals_are_closed_at_rest_and_under_the_ceiling() -> void:
	var rig := _rich_rig()
	var petal := (rig[0].get_node("Nozzle_R") as Node3D).get_node("Petal_R_03") as Node3D
	_settle(rig[1])
	assert_true(petal.quaternion.get_angle() < 1e-4, "au repos, les petales sont fermes")
	var peak := 0.0
	for phase in [1.0, 0.0, 1.0]:
		rig[1].call("set_thrust", phase)
		for i in 300:
			rig[1].call("_process", 0.05)
			peak = maxf(peak, rad_to_deg(petal.quaternion.get_angle()))
	assert_true(peak <= HARD_PETAL_DEG, "les petales restent sous le plafond (%.2f <= %.1f)" % [peak, HARD_PETAL_DEG])
	assert_true(peak > 10.0, "l'ouverture se voit (%.2f deg)" % peak)
	rig[0].free()

func test_brake_closes_the_petals_and_raises_the_airbrakes() -> void:
	# Le freinage subi se lit DEUX fois sur la coque : petales qui se referment (comme
	# la plume s'etrangle) et aerofreins qui se levent.
	var rig := _rich_rig()
	rig[1].call("set_thrust", 1.0)
	_settle(rig[1])
	var petal := (rig[0].get_node("Nozzle_L") as Node3D).get_node("Petal_L_00") as Node3D
	var open_deg := rad_to_deg(petal.quaternion.get_angle())
	rig[1].call("set_brake", 1.0)
	_settle(rig[1])
	assert_true(rad_to_deg(petal.quaternion.get_angle()) < open_deg * 0.1,
		"a plein freinage les petales se referment (%.2f -> %.2f)" % [open_deg, rad_to_deg(petal.quaternion.get_angle())])
	var brake_rot := (rig[0].get_node("Airbrake_L") as Node3D).rotation.x
	var brake_deg := rad_to_deg(absf(brake_rot))
	assert_true(brake_deg > 30.0 and brake_deg <= HARD_AIRBRAKE_DEG,
		"les aerofreins se levent sous le plafond (%.2f deg)" % brake_deg)
	# Mesure de la forge : rotation + autour de +X = le bord arriere DESCEND. S'ouvrir,
	# c'est donc tourner en negatif — un signe faux enfoncerait l'aerofrein dans sa baie.
	assert_true(brake_rot < 0.0, "l'aerofrein tourne dans le sens qui le LEVE (%.3f rad)" % brake_rot)
	rig[0].free()

func test_intakes_follow_thrust_under_the_ceiling() -> void:
	var rig := _rich_rig()
	rig[1].call("set_thrust", 1.0)
	_settle(rig[1])
	var rot := (rig[0].get_node("Intake_R") as Node3D).rotation.x
	var deg := rad_to_deg(absf(rot))
	assert_true(deg > 5.0 and deg <= HARD_INTAKE_DEG, "la rampe s'ouvre sous le plafond (%.2f deg)" % deg)
	assert_true(rot < 0.0, "la rampe tourne dans le sens qui la LEVE (mesure forge : + = descend)")
	rig[0].free()

func test_rudders_yaw_together_on_their_canted_axis() -> void:
	# Les gouvernes vont du MEME cote (un lacet), a la difference des volets qui
	# s'opposent — et chacune tourne autour de l'axe de SA derive, pas de la verticale.
	var rig := _rich_rig()
	rig[1].call("set_bank", 1.0)
	_settle(rig[1])
	var l := rig[0].get_node("Rudder_L") as Node3D
	var r := rig[0].get_node("Rudder_R") as Node3D
	var angle_l := rad_to_deg(l.quaternion.get_angle())
	assert_true(angle_l > 8.0 and angle_l <= HARD_RUDDER_DEG, "la gouverne braque sous le plafond (%.2f deg)" % angle_l)
	assert_almost_eq(rad_to_deg(r.quaternion.get_angle()), angle_l, 0.01, "les deux gouvernes braquent du meme angle")
	assert_almost_eq(l.quaternion.get_axis().angle_to(ShipFlightScript.RUDDER_AXIS_L), 0.0, 1e-3,
		"la gouverne babord tourne autour de l'axe MESURE de sa derive")
	assert_almost_eq(r.quaternion.get_axis().angle_to(ShipFlightScript.RUDDER_AXIS_R), 0.0, 1e-3,
		"la gouverne tribord aussi")
	assert_true(l.quaternion.get_axis().x * r.quaternion.get_axis().x < 0.0,
		"les deux axes penchent vers l'exterieur, en miroir")
	assert_true(l.quaternion.get_axis().z > 0.0 and r.quaternion.get_axis().z > 0.0,
		"et sont couches vers l'arriere, comme les derives")
	rig[0].free()

func test_docking_deploys_grapples_then_opens_the_canopy() -> void:
	var rig := _rich_rig()
	var hook := rig[0].get_node("Grapple_L") as Node3D
	var canopy := rig[0].get_node("Canopy") as Node3D
	rig[1].call("set_docking", 1.0)
	# A mi-course, les grappins sont sortis et la verriere encore fermee : un mecanisme
	# apres l'autre.
	var canopy_moved_before_hooks := false
	for i in 400:
		rig[1].call("_process", 0.05)
		if canopy.rotation.x > 0.01 and absf(hook.rotation.x) < deg_to_rad(ShipFlightScript.GRAPPLE_DEG * 0.9):
			canopy_moved_before_hooks = true
	assert_false(canopy_moved_before_hooks, "la verriere n'ouvre qu'une fois les grappins sortis")
	var hook_deg := rad_to_deg(absf(hook.rotation.x))
	var canopy_deg := rad_to_deg(absf(canopy.rotation.x))
	assert_true(hook_deg > 60.0 and hook_deg <= HARD_GRAPPLE_DEG, "le grappin pend sous le plafond (%.2f deg)" % hook_deg)
	assert_true(canopy_deg > 15.0 and canopy_deg <= HARD_CANOPY_DEG, "la verriere ouvre sous le plafond (%.2f deg)" % canopy_deg)
	rig[0].free()

func test_nozzle_yaw_follows_bank_under_the_ceiling() -> void:
	var rig := _rich_rig()
	rig[1].call("set_bank", -1.0)
	_settle(rig[1])
	var l := rad_to_deg((rig[0].get_node("Nozzle_L") as Node3D).rotation.y)
	var r := rad_to_deg((rig[0].get_node("Nozzle_R") as Node3D).rotation.y)
	assert_true(absf(l) > 2.0 and absf(l) <= HARD_YAW_DEG, "la tuyere vectorise sous le plafond (%.2f deg)" % l)
	assert_almost_eq(l, r, 1e-6, "les deux tuyeres vectorisent du meme cote")
	rig[0].free()

func test_a_long_frame_never_overshoots_the_new_families() -> void:
	# Le piege du lissage, rejoue sur chaque famille neuve : une image d'une seconde ne
	# doit envoyer aucune piece au-dela de son plafond.
	var rig := _rich_rig()
	rig[1].call("set_thrust", 1.0)
	rig[1].call("set_brake", 1.0)
	rig[1].call("set_docking", 1.0)
	rig[1].call("set_bank", 1.0)
	rig[1].call("_process", 1.0)
	rig[1].call("_process", 1.0)
	var checks := {
		"Airbrake_L": HARD_AIRBRAKE_DEG, "Intake_L": HARD_INTAKE_DEG,
		"Grapple_L": HARD_GRAPPLE_DEG, "Canopy": HARD_CANOPY_DEG,
	}
	for part_name: String in checks:
		var deg := rad_to_deg(absf((rig[0].get_node(part_name) as Node3D).rotation.x))
		assert_true(deg <= checks[part_name], "%s ne depasse pas son plafond sur une image longue (%.2f)" % [part_name, deg])
	rig[0].free()

func test_the_six_part_hull_ignores_the_new_families() -> void:
	# La coque en service n'a ni petale, ni aerofrein, ni grappin : pousser les quatre
	# ratios ne doit rien casser, et la tuyere doit CONTINUER de grandir (BRIEF-0033).
	var rig := _rig()
	rig[1].call("set_brake", 1.0)
	rig[1].call("set_docking", 1.0)
	rig[1].call("set_thrust", 1.0)
	_settle(rig[1])
	assert_true((rig[0].get_node("Nozzle_L") as Node3D).scale.x > 1.3, "sans petales, l'echelle ouvre encore la tuyere")
	rig[0].free()
