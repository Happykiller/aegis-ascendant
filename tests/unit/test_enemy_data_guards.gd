extends "res://tests/test_case.gd"
## Les gardes de EnemyData.validate() — vérifiées NON VACANTES.
##
## Une règle de validation qu'on n'a jamais mise en échec ne prouve rien : elle
## peut être fausse, inatteignable, ou porter sur un champ qui n'existe plus, et
## tous les tests resteraient verts. Chaque garde est donc éprouvée deux fois —
## une donnée fautive qui DOIT être refusée, une donnée saine qui DOIT passer.

const SHOT := preload("res://resources/weapons/needle_shot.tres")

func _sane() -> EnemyData:
	var data := EnemyData.new()
	data.projectile = SHOT
	return data

## Une mine réactive valide, dont on ira casser un champ à la fois.
func _mine() -> EnemyData:
	var data := _sane()
	data.path = EnemyData.Path.DRIFT
	data.fire = EnemyData.Fire.RADIAL
	data.burst_count = 14
	data.alert_radius = 4.0
	data.trigger_radius = 2.0
	data.windup_time = 0.6
	data.active_time = 0.4
	return data

func _refuses(data: EnemyData, fragment: String, message: String) -> void:
	var errors := data.validate()
	var found := false
	for error in errors:
		if error.contains(fragment):
			found = true
			break
	assert_true(found, "%s (erreurs obtenues : %s)" % [message, ", ".join(errors)])

func test_the_reference_units_are_accepted() -> void:
	assert_true(_sane().validate().is_empty(), "un ennemi ordinaire passe")
	assert_true(_mine().validate().is_empty(), "une mine bien réglée passe")

# --- Tir ----------------------------------------------------------------------

## Une unité qui ne tire pas n'a pas besoin de munition. C'est ce qui rend possible
## une menace sans projectile : aura, aspiration, contact.
func test_a_silent_unit_needs_no_projectile() -> void:
	var data := EnemyData.new()
	data.fire = EnemyData.Fire.NONE
	assert_true(data.validate().is_empty(), "NONE se passe de projectile")

func test_a_shooting_unit_without_ammunition_is_refused() -> void:
	var data := EnemyData.new()
	_refuses(data, "projectile is required", "un tireur sans projectile est refusé")

## Un éventail d'un seul coup n'est pas un éventail : c'est un SINGLE qui se ment,
## et la règle de variété tomberait sans que rien ne le dise.
func test_a_fan_of_one_is_refused() -> void:
	var data := _sane()
	data.fire = EnemyData.Fire.FAN
	data.burst_count = 1
	_refuses(data, "burst_count", "un éventail d'un coup est refusé")

func test_a_ring_of_two_is_refused() -> void:
	var data := _sane()
	data.fire = EnemyData.Fire.RADIAL
	data.burst_count = 2
	_refuses(data, "RADIAL", "une couronne de deux balles est refusée")

# --- Menace de proximité ------------------------------------------------------

## Sans marge d'éveil, l'unité passe de l'inertie à l'engagement dans la même
## image : le joueur n'a rien vu venir, et le télégraphe ne sert plus à rien.
func test_a_trigger_wider_than_the_alert_is_refused() -> void:
	var data := _mine()
	data.alert_radius = 1.0
	_refuses(data, "alert_radius", "un déclenchement plus large que l'éveil est refusé")

## Spec §11.2 : 300 à 800 ms. Ce n'est pas un goût, c'est un contrat de lisibilité —
## en deçà le joueur n'a pas le temps de lire, au-delà la menace cesse d'en être une.
func test_a_telegraph_outside_the_spec_window_is_refused() -> void:
	var quick := _mine()
	quick.windup_time = 0.2
	_refuses(quick, "windup_time", "un télégraphe trop court est refusé")
	var slow := _mine()
	slow.windup_time = 1.2
	_refuses(slow, "windup_time", "un télégraphe trop long est refusé")

func test_a_charge_of_zero_duration_is_refused() -> void:
	var data := _mine()
	data.active_time = 0.0
	_refuses(data, "active_time", "une charge de durée nulle est refusée")

# --- Puits gravitationnel -----------------------------------------------------

func _well() -> EnemyData:
	var data := _mine()
	data.fire = EnemyData.Fire.NONE
	data.effect = EnemyData.Effect.GRAVITY_WELL
	data.pull_radius = 3.5
	data.pull_speed_max = 5.0
	return data

func test_a_well_that_is_properly_bounded_is_accepted() -> void:
	assert_true(_well().validate().is_empty(), "un puits mesuré passe")

func test_a_well_without_reach_is_refused() -> void:
	var data := _well()
	data.pull_radius = 0.0
	_refuses(data, "pull_radius", "un puits sans portée est refusé")

## ⚠️ L'invariant qui rend la mécanique jouable. Une aspiration à laquelle le
## chasseur ne peut rien opposer n'est plus un danger, c'est une cinématique — et
## sur une MINE c'est pire encore, puisque le joueur a CHOISI de s'approcher : il
## doit pouvoir choisir de repartir. Même garde que la phase gravitique du boss.
func test_a_well_that_pins_the_fighter_is_refused() -> void:
	var data := _well()
	data.pull_speed_max = EnemyData.PLAYER_STATS.max_speed - 0.1
	_refuses(data, "no room to manoeuvre", "un puits qui cloue le chasseur est refusé")

## Le puits est une RÉACTION, pas un champ permanent : sans rayon de déclenchement
## il aspirerait du début à la fin de la vague, sans que rien ne l'annonce.
func test_a_well_without_a_trigger_is_refused() -> void:
	var data := _well()
	data.alert_radius = 0.0
	data.trigger_radius = 0.0
	_refuses(data, "requires a trigger_radius", "un puits sans déclenchement est refusé")
