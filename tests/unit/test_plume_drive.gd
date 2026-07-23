extends "res://tests/test_case.gd"
## Commande de la plume d'échappement (`EnginePlume.throttle_from` / `advance` /
## `shock_depth_at`).
##
## POURQUOI CE TEST — ce que la plume raconte du mouvement ne se vérifie pas sur une
## capture : l'écart entre « accélère » et « ralentit » est une DIFFÉRENCE entre deux
## instants, et une image fixe n'en montre qu'un (cf. `pratique-verifier-par-test.md`).
## Ces trois fonctions sont statiques et pures : ni nœud, ni rendu, ni arbre.

const TuningScript := preload("res://resources/data/plume_tuning.gd")
const HELIOS := preload("res://resources/vfx/plume_helios.tres")

const UP := Vector2(0.0, 1.0)
const DOWN := Vector2(0.0, -1.0)
const SIDE := Vector2(1.0, 0.0)

func _tuning() -> PlumeTuning:
	return HELIOS

func test_the_shipped_tuning_is_valid() -> void:
	# Le réglage embarqué doit passer sa propre validation : c'est lui qui vole.
	var errors := HELIOS.validate()
	assert_eq(errors.size(), 0, "plume_helios.tres: %s" % ", ".join(errors))

func test_a_released_stick_still_burns() -> void:
	# ⚠️ Un moteur éteint lit comme une panne, pas comme un vol plané.
	var idle := EnginePlume.throttle_from(Vector2.ZERO, 0.0, _tuning())
	assert_true(idle > 0.0, "the engine never dies")
	assert_almost_eq(idle, _tuning().idle_throttle, 0.001, "released stick sits at idle")

func test_pushing_up_the_screen_opens_the_throttle() -> void:
	var idle := EnginePlume.throttle_from(Vector2.ZERO, 0.0, _tuning())
	var accel := EnginePlume.throttle_from(UP, 0.0, _tuning())
	assert_true(accel > idle, "acceleration reads brighter than drift")

func test_holding_back_collapses_the_plume() -> void:
	var idle := EnginePlume.throttle_from(Vector2.ZERO, 0.0, _tuning())
	var brake := EnginePlume.throttle_from(DOWN, 0.0, _tuning())
	assert_true(brake < idle, "pulling back drops below idle — that IS the deceleration")

func test_speed_sustains_the_plume_after_the_stick_is_released() -> void:
	# Le cas exact du shooter : le joueur lâche la touche, le vaisseau file encore.
	var coasting := EnginePlume.throttle_from(Vector2.ZERO, 1.0, _tuning())
	var stopped := EnginePlume.throttle_from(Vector2.ZERO, 0.0, _tuning())
	assert_true(coasting > stopped, "acquired speed keeps the nozzle open")

func test_a_lateral_dash_counts_less_than_a_forward_burn() -> void:
	var side := EnginePlume.throttle_from(SIDE, 0.0, _tuning())
	var forward := EnginePlume.throttle_from(UP, 0.0, _tuning())
	assert_true(side > EnginePlume.throttle_from(Vector2.ZERO, 0.0, _tuning()),
		"a dash does light the engine")
	assert_true(side < forward, "but a swerve is not an acceleration")

func test_the_throttle_never_leaves_zero_one() -> void:
	# Le shader borne ses uniformes ; la commande, elle, additionne quatre gains et
	# pourrait déborder — un `plume_length` extrapolé ferait pousser un jet de 4 m.
	var full := EnginePlume.throttle_from(Vector2(1.0, 1.0), 1.0, _tuning())
	assert_true(full <= 1.0, "saturates at full throttle (got %f)" % full)
	var reverse := EnginePlume.throttle_from(Vector2(-1.0, -1.0), 0.0, _tuning())
	assert_true(reverse >= 0.0, "never goes negative (got %f)" % reverse)

# --- Lissage ------------------------------------------------------------------

func test_the_plume_lights_faster_than_it_dies() -> void:
	# L'ASYMÉTRIE EST L'EFFET : montée vive (le geste se voit), extinction molle (une
	# tuyère garde son inertie). Symétrique, la plume claque à chaque touche relâchée.
	var tuning := _tuning()
	var lit := EnginePlume.advance(0.0, 1.0, 0.1, tuning.attack_rate, tuning.decay_rate)
	var died := EnginePlume.advance(1.0, 0.0, 0.1, tuning.attack_rate, tuning.decay_rate)
	assert_true(lit > 1.0 - died, "attack must outrun decay (lit=%f, died=%f)" % [lit, died])

## ⚠️ LE PIÈGE. Une image très longue (chargement, alt-tab) donne un facteur de lissage
## supérieur à 1 : sans le borner, la poussée DÉPASSE sa cible et la plume pompe au
## retour du focus. Même piège que `ship_flight.gd:89`, déjà payé sur les volets.
func test_a_monstrous_frame_never_overshoots() -> void:
	var settled := EnginePlume.advance(0.0, 1.0, 0.5, 10.0, 3.5)
	assert_true(settled <= 1.0, "overshoot on a 500 ms frame (got %f)" % settled)
	var cut := EnginePlume.advance(1.0, 0.0, 0.5, 10.0, 3.5)
	assert_true(cut >= 0.0, "undershoot on a 500 ms frame (got %f)" % cut)

func test_smoothing_converges_toward_the_target() -> void:
	var value := 0.0
	for i in 60:
		value = EnginePlume.advance(value, 1.0, 1.0 / 60.0, 10.0, 3.5)
	assert_true(value > 0.9, "a second of full throttle gets there (got %f)" % value)

# --- Disques de Mach ----------------------------------------------------------

func test_no_shock_diamonds_at_low_throttle() -> void:
	# Les disques ne sont pas un ornement permanent : ils SONT le signal « plein gaz ».
	assert_almost_eq(EnginePlume.shock_depth_at(0.0, _tuning()), 0.0, 0.0001,
		"a drifting engine shows no diamonds")
	assert_almost_eq(EnginePlume.shock_depth_at(_tuning().shock_threshold, _tuning()), 0.0,
		0.0001, "nothing at the threshold itself")

func test_shock_diamonds_open_at_full_throttle() -> void:
	assert_almost_eq(EnginePlume.shock_depth_at(1.0, _tuning()), _tuning().shock_depth,
		0.0001, "full throttle shows the full pattern")

func test_shock_depth_grows_with_throttle() -> void:
	var mid := EnginePlume.shock_depth_at(0.8, _tuning())
	var high := EnginePlume.shock_depth_at(0.95, _tuning())
	assert_true(mid > 0.0 and high > mid, "the pattern opens progressively")

# --- Garde-fous de la Resource ------------------------------------------------

func test_a_tuning_without_range_is_rejected() -> void:
	# Le défaut qui rend l'effet entier muet : plein régime aussi court que la dérive.
	var flat: PlumeTuning = TuningScript.new()
	flat.length_idle = 1.0
	flat.length_full = 1.0
	assert_true(flat.validate().size() > 0, "a plume that never grows must be rejected")

func test_a_symmetric_response_is_rejected() -> void:
	var snappy: PlumeTuning = TuningScript.new()
	snappy.attack_rate = 5.0
	snappy.decay_rate = 5.0
	assert_true(snappy.validate().size() > 0, "a nozzle does not snap shut")

func test_an_unreadable_shock_count_is_rejected() -> void:
	# 960×540 + scanlines : au-delà de 3 disques le motif devient une bouillie grise.
	var busy: PlumeTuning = TuningScript.new()
	busy.shock_count = 6.0
	assert_true(busy.validate().size() > 0, "readability ceiling is enforced, not hoped for")
