extends "res://tests/test_case.gd"
## Le gel d'impact (LOI-EXP-03).
##
## Un seul mode d'échec compte ici, et il n'est pas esthétique : **le jeu qui reste au
## ralenti**. Une erreur de comptage ne se verrait pas à la relecture — elle se verrait
## en jouant, une fois, chez quelqu'un d'autre.
##
## La logique testée est PURE : `request()` accumule, `advance()` consomme du temps RÉEL
## et rend l'échelle à appliquer. Le nœud n'est qu'un applicateur, et `Engine.time_scale`
## n'est jamais touché ici — un test qui le poserait le laisserait aux suivants.

const HitStopScript := preload("res://scripts/fx/hit_stop.gd")

func _fresh() -> HitStop:
	return track(HitStopScript.new()) as HitStop

func test_it_always_gives_time_back() -> void:
	var stop := _fresh()
	stop.request(HitStop.PLATE)
	assert_true(stop.is_frozen(), "le gel est armé")
	# Une seule image longue suffit à tout consommer : le gel ne doit jamais survivre à
	# sa durée, quelle que soit la cadence.
	assert_almost_eq(stop.advance(1.0), 1.0, 0.0001, "le temps revient à l'échelle 1")
	assert_false(stop.is_frozen(), "et le gel est retombé")

func test_it_holds_for_its_whole_duration() -> void:
	var stop := _fresh()
	stop.request(0.06)
	var elapsed := 0.0
	var steps := 0
	while stop.is_frozen() and steps < 1000:
		stop.advance(0.01)
		elapsed += 0.01
		steps += 1
	assert_almost_eq(elapsed, 0.06, 0.011, "il a tenu ~60 ms de temps réel (%.3f)" % elapsed)

## Trois plaques qui cèdent dans la même salve ne doivent pas immobiliser le jeu 180 ms.
func test_overlapping_requests_take_the_longest_not_the_sum() -> void:
	var stop := _fresh()
	stop.request(0.06)
	stop.advance(0.02)
	stop.request(0.06)
	var elapsed := 0.0
	while stop.is_frozen() and elapsed < 1.0:
		stop.advance(0.01)
		elapsed += 0.01
	assert_true(elapsed <= 0.07,
		"la seconde demande relance sans s'ajouter (%.3f s restants)" % elapsed)

func test_an_absurd_duration_is_capped() -> void:
	var stop := _fresh()
	stop.request(30.0)
	stop.advance(HitStop.MAX_DURATION)
	assert_false(stop.is_frozen(), "plafonné à %.2f s" % HitStop.MAX_DURATION)

func test_a_zero_request_freezes_nothing() -> void:
	var stop := _fresh()
	stop.request(0.0)
	assert_false(stop.is_frozen(), "zéro ne gèle pas")
	stop.request(-1.0)
	assert_false(stop.is_frozen(), "une durée négative non plus")

## Le repère du genre : 60 à 80 ms sur une frappe décisive. Les deux durées du jeu
## doivent y rester — c'est une CONTRAINTE de la bible, pas un goût.
func test_both_shipped_durations_sit_in_the_documented_window() -> void:
	for duration in [HitStop.PLATE, HitStop.BOSS]:
		assert_true(duration >= 0.06 and duration <= 0.08,
			"%.3f s est dans la fenêtre 60-80 ms" % duration)
