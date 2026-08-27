extends "res://tests/test_case.gd"
## La dérive organique — ce qui casse la boucle sans casser la lecture.
##
## Deux risques, opposés, et ce fichier garde les deux :
##   1. qu'elle ne serve à rien — deux unités continueraient d'onduler à l'unisson ;
##   2. qu'elle serve TROP — une trajectoire cesserait d'être reconnaissable, et la règle
##      de variété d'`enemy_path.gd` (« deux schémas diffèrent par leur FORME ») tomberait
##      sans qu'aucun test ne le dise.

const PathScript := preload("res://scripts/enemies/enemy_path.gd")

func _scout() -> EnemyData:
	var data := EnemyData.new()
	data.path = EnemyData.Path.WEAVE
	data.move_speed = 3.0
	data.weave_amplitude = 1.4
	data.weave_frequency = 0.5
	return data

# --- Le contrat de pureté, qui ne doit RIEN perdre --------------------------

## ⚠️ LA GARDE LA PLUS IMPORTANTE. Une unité doit apparaître EXACTEMENT à son point de
## spawn : c'est ce qui rend le pooling observable. Une dérive à pleine amplitude dès
## l'âge zéro téléporterait chaque réapparition d'un demi-mètre — sans erreur, sans test
## rouge, et invisible autrement qu'en jouant.
func test_a_drifting_unit_still_appears_exactly_on_its_spawn() -> void:
	for seed in [0.0, 0.37, 0.61, 0.99]:
		var offset := OrganicDrift.offset(0.0, seed, 1.0)
		assert_true(offset.length() < 0.0001,
			"graine %.2f : décalage nul à l'âge zéro (%.4f)" % [seed, offset.length()])

## Elle reste une FONCTION du temps, pas une accumulation : même âge, même décalage.
## C'est ce qui garde la trajectoire indépendante du pas de temps.
func test_the_same_seed_always_traces_the_same_path() -> void:
	var a := OrganicDrift.offset(3.7, 0.42, 0.55)
	var b := OrganicDrift.offset(3.7, 0.42, 0.55)
	assert_true(a.distance_to(b) < 0.00001, "déterministe à graine égale")

# --- Ce pour quoi elle existe ----------------------------------------------

## Le défaut nommé au playtest : quatre coques nées à 0,7 s d'intervalle ondulaient à
## l'unisson. Deux rangs successifs doivent recevoir des dérives franchement différentes.
func test_two_neighbours_in_a_flight_do_not_move_as_one() -> void:
	var worst := 0.0
	for step in 40:
		var age := 0.8 + step * 0.1
		var a := OrganicDrift.offset(age, OrganicDrift.seed_for(7), 0.55)
		var b := OrganicDrift.offset(age, OrganicDrift.seed_for(8), 0.55)
		worst = maxf(worst, a.distance_to(b))
	assert_true(worst > 0.4,
		"deux ennemis successifs s'écartent de %.2f u — sinon ils volent en miroir" % worst)

## ⚠️ LE CŒUR DU SUJET : les périodes doivent rester NON HARMONIQUES. Dans un rapport
## simple (×2, ×3, ÷2), la somme redeviendrait périodique et l'œil retrouverait la boucle
## qu'on vient de casser. La garde mesure le rapport, pas les valeurs — libre de bouger,
## pas libre de retomber sur un compte rond.
func test_the_two_periods_never_fall_into_step() -> void:
	var ratio: float = OrganicDrift.PERIOD_B / OrganicDrift.PERIOD_A
	for harmonic in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
		assert_true(absf(ratio - harmonic) > 0.05,
			"rapport de périodes %.3f — trop proche de l'harmonique %.1f" % [ratio, harmonic])

## Et la conséquence qu'on achète avec : le mouvement ne se répète pas dans la vie d'une
## unité. On compare la dérive à elle-même, décalée, et on cherche le pire décalage.
##
## ⚠️ LE DÉCALAGE EST BORNÉ PAR LA DURÉE DE VIE, et ce n'est pas une commodité. Une unité
## traverse le champ (9,5 → −8) à ~3 u/s, soit **environ six secondes**. Pour que l'œil
## voie une répétition, il faut qu'elle se produise DEUX FOIS pendant ce temps — donc à un
## décalage d'au plus ~4 s. Une quasi-répétition à 13 s d'écart existe toujours dans un
## signal quasi périodique, et personne ne la verra jamais : la mesurer ferait rougir le
## test pour une propriété qui n'intéresse aucun joueur.
##
## Mesuré le 2026-08-27 : pire cas **0,41 u** au décalage 0,4 s, soit les trois quarts de
## l'amplitude. Le seuil garde une marge d'un quart.
const LIFETIME_LAG_MAX := 4.0

func test_the_drift_does_not_repeat_within_a_lifetime() -> void:
	var closest := 1e9
	for lag_step in range(4, int(LIFETIME_LAG_MAX * 10) + 1):
		var lag := lag_step * 0.1
		var worst := 0.0
		for step in 50:
			var age := 1.0 + step * 0.1
			worst = maxf(worst, OrganicDrift.offset(age, 0.42, 0.55)
				.distance_to(OrganicDrift.offset(age + lag, 0.42, 0.55)))
		closest = minf(closest, worst)
	assert_true(closest > 0.30,
		"la dérive revient sur elle-même à %.2f u près — l'œil y retrouverait la boucle" % closest)

# --- Ce qu'elle ne doit PAS abîmer -----------------------------------------

## La règle de variété d'`enemy_path.gd` : deux trajectoires doivent différer par leur
## forme. La dérive ne doit pas les rapprocher au point de les confondre — c'est le risque
## exact d'un bruit ajouté à tout le monde.
func test_drift_never_makes_two_paths_look_alike() -> void:
	var paths := EnemyData.Path.values()
	for i in paths.size():
		for j in range(i + 1, paths.size()):
			var a := _scout(); a.path = paths[i]
			var b := _scout(); b.path = paths[j]
			var worst := 0.0
			for step in 30:
				var age := step * 0.15
				worst = maxf(worst, PathScript.position_at(a, age, Vector2(-6.0, 9.0), 0.31)
					.distance_to(PathScript.position_at(b, age, Vector2(-6.0, 9.0), 0.62)))
			assert_true(worst > 0.5,
				"trajectoires %d et %d restent distinguables sous la dérive (%.2f u)"
					% [paths[i], paths[j], worst])

## Celle qui « ne manœuvre pas » ne doit pas se mettre à manœuvrer : la dérive la fait
## respirer, elle ne lui donne pas une trajectoire.
func test_the_straight_one_stays_straight() -> void:
	var data := _scout()
	data.path = EnemyData.Path.DRIFT
	var worst := 0.0
	for step in 40:
		var age := step * 0.15
		var nue := PathScript.position_at(data, age, Vector2(2.0, 9.0))
		var derivee := PathScript.position_at(data, age, Vector2(2.0, 9.0), 0.42)
		worst = maxf(worst, absf(derivee.x - nue.x))
	assert_true(worst < 0.25,
		"elle s'écarte de %.2f u de sa colonne — au-delà, elle manœuvre" % worst)
