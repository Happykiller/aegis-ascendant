extends "res://tests/test_case.gd"
## `BossApproach` — le dernier puits qui monte avant le Leviathan (lot 5, option D).
##
## ⚠️ CE QUE CE FICHIER GARDE. Cette mécanique s'atteint après DEUX MINUTES de jeu, à la
## toute fin du champ d'astéroïdes : la vérifier à la main coûte une partie entière à
## chaque retouche. Et son défaut le plus probable est muet — une aspiration mal bornée ne
## lève aucune erreur, elle transforme une respiration en cinématique où le joueur regarde
## son chasseur partir sans lui.

const Approach := preload("res://scripts/gameplay/boss_approach.gd")
const PLAYER_STATS: PlayerStats = preload("res://resources/player/specter9_stats.tres")

const D := Approach.DURATION

## LE test du fichier. `GravityWell.leaves_room()` existe parce qu'un champ à 13,9 u/s
## contre 14,0 est « techniquement libre » et injouable en fait : on y avance à un dixième
## d'unité par seconde. La même garde s'applique ici, sinon la respiration devient un piège.
func test_the_well_never_traps_the_player() -> void:
	assert_true(Approach.leaves_room(PLAYER_STATS.max_speed),
		"le puits d'approche (%.1f u/s) laisse jouer un chasseur à %.1f u/s"
			% [Approach.MAX_PULL_SPEED, PLAYER_STATS.max_speed])

## Il ne doit pas être plus dur que ce que la phase vient d'enseigner : le Null Maw du
## champ tire à 7,0 u/s. Un dernier puits PLUS fort que la leçon ne serait pas une
## respiration, ce serait une vague de plus.
func test_the_approach_is_gentler_than_the_wave_it_follows() -> void:
	var maw: EnemyData = load("res://resources/enemies/null_maw.tres")
	assert_true(Approach.MAX_PULL_SPEED < maw.pull_speed_max,
		"l'approche (%.1f) aspire moins que le Null Maw (%.1f)"
			% [Approach.MAX_PULL_SPEED, maw.pull_speed_max])

## ⚠️ Le défaut que cette courbe évite : une aspiration à pleine vitesse dès la première
## image ARRACHE le chasseur des mains du joueur à l'instant où la vague vient de se vider.
## Il lit ça comme un bug, pas comme un puits.
func test_the_pull_is_born_at_zero_and_grows() -> void:
	assert_almost_eq(Approach.speed_at(0.0, D), 0.0, 0.0001,
		"à la première image, aucune aspiration")
	var quarter := Approach.speed_at(D * 0.25, D)
	var half := Approach.speed_at(D * 0.5, D)
	assert_true(quarter < half, "elle monte")
	assert_true(quarter < Approach.MAX_PULL_SPEED * 0.25,
		"et elle monte LENTEMENT d'abord (%.2f u/s au quart)" % quarter)
	assert_almost_eq(Approach.speed_at(D, D), Approach.MAX_PULL_SPEED, 0.0001,
		"pour atteindre son maximum pile à la fin")

## Le puits monte vers l'endroit d'où le boss descend — `plane_position = (0, 12)`. C'est
## ce qui fait qu'on suit le puits des yeux et qu'on trouve le boss au bout du regard.
func test_the_well_rises_towards_where_the_boss_enters() -> void:
	var start := Approach.centre_at(0.0, D)
	var mid := Approach.centre_at(D * 0.5, D)
	var end := Approach.centre_at(D, D)
	assert_true(mid.y > start.y and end.y > mid.y, "il monte, sans reculer")
	assert_true(end.y >= 10.0,
		"il finit en haut du cadre (y=%.1f), là où le Leviathan apparaît" % end.y)
	assert_almost_eq(end.x, 0.0, 0.0001, "et au centre, comme le boss")

## Il s'élargit en montant : il ne devient pas plus fort de près, il devient plus large de
## loin. C'est ce qui le fait sentir alors que sa vitesse reste modeste.
func test_the_well_widens_as_it_rises() -> void:
	assert_true(Approach.radius_at(D, D) > Approach.radius_at(0.0, D) * 2.0,
		"le rayon plus que double sur l'approche")

func test_the_approach_ends_and_nothing_runs_past_it() -> void:
	assert_false(Approach.is_over(D * 0.99, D), "pas encore finie juste avant")
	assert_true(Approach.is_over(D, D), "finie à l'échéance")
	assert_almost_eq(Approach.ratio(D * 3.0, D), 1.0, 0.0001,
		"et l'avancement ne dépasse jamais 1")
	assert_almost_eq(Approach.speed_at(D * 3.0, D), Approach.MAX_PULL_SPEED, 0.0001,
		"ni la vitesse son maximum")

## La bible pose la garde en même temps que le manque : l'arc est déjà à sa cible de
## 2-3 min. Une respiration qui s'étirerait repaierait une phase entière.
func test_the_breath_stays_short() -> void:
	assert_true(D >= 2.0, "assez longue pour se lire comme une respiration (%.1f s)" % D)
	assert_true(D <= 5.0, "assez courte pour ne pas repayer une phase (%.1f s)" % D)

## Une durée nulle ne divise pas par zéro : elle vaut « déjà fini ».
func test_a_zero_duration_is_already_over() -> void:
	assert_almost_eq(Approach.ratio(0.0, 0.0), 1.0, 0.0001, "avancement plein")
	assert_true(Approach.is_over(0.0, 0.0), "et l'approche est finie")
