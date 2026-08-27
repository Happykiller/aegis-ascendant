extends "res://tests/test_case.gd"
## La vague d'ouverture — ce qu'une retouche peut casser en silence.
##
## Elle a longtemps été la seule rencontre du jeu, et pendant tout ce temps ses dix
## unités ont tiré LA MÊME CHOSE : une balle droite. `EnemyFire` connaissait pourtant
## `FAN` et `AIMED` depuis ADR-0022 — écrits, testés, documentés, et employés nulle
## part, parce que `fire` vaut `SINGLE` par défaut et qu'aucune Resource ne le disait.
##
## Ce fichier garde deux choses, et aucune n'est un goût de level design :
##   1. les deux schémas restent EN JEU — un `fire` retiré d'un `.tres` ne se verrait
##      nulle part ailleurs, et le jeu retomberait à la balle droite sans une alerte ;
##   2. la PARITÉ d'une salve visée reste un choix — c'est la loi, pas un réglage.

const OpeningWave: WaveData = preload("res://resources/encounters/wave_graybox_01.tres")

const LancerScene := "res://scenes/enemies/needle_scout_lancer.tscn"
const StrafeScene := "res://scenes/enemies/needle_scout_strafe.tscn"
const LancerData := "res://resources/enemies/needle_scout_lancer.tres"
const StrafeData := "res://resources/enemies/needle_scout_strafe.tres"

const ENEMY_DIR := "res://resources/enemies"

func _scene_paths() -> Dictionary:
	var counts := {}
	for entry in OpeningWave.entries:
		var path := entry.enemy_scene.resource_path
		counts[path] = int(counts.get(path, 0)) + entry.count
	return counts

func _enemy_paths() -> PackedStringArray:
	var found := PackedStringArray()
	var dir := DirAccess.open(ENEMY_DIR)
	if dir == null:
		return found
	for file in dir.get_files():
		if file.ends_with(".tres"):
			found.append("%s/%s" % [ENEMY_DIR, file])
	return found

func test_the_wave_is_valid() -> void:
	var errors := OpeningWave.validate()
	assert_true(errors.is_empty(), "vague valide (%s)" % ", ".join(errors))

## Le seul schéma qui PUNIT L'IMMOBILITÉ doit rester joué. Sans lui, aucune unité de
## vague ne demande au joueur de bouger : elles se contournent toutes.
func test_a_wave_unit_actually_aims_at_the_player() -> void:
	var counts := _scene_paths()
	assert_true(int(counts.get(LancerScene, 0)) > 0, "le lancier est bien dans la vague")
	var lancer: EnemyData = load(LancerData)
	assert_eq(lancer.fire, EnemyData.Fire.AIMED,
		"le lancier vise — c'est la seule unité de vague qui s'immobilise pour tirer")

func test_a_wave_unit_actually_closes_a_corridor() -> void:
	var counts := _scene_paths()
	assert_true(int(counts.get(StrafeScene, 0)) > 0, "le strafe est bien dans la vague")
	var strafe: EnemyData = load(StrafeData)
	assert_eq(strafe.fire, EnemyData.Fire.FAN,
		"le strafe ferme un couloir — il traverse, viser n'aurait aucun sens")

## LA garde de parité. Un éventail VISÉ à nombre IMPAIR met une balle sur l'axe : rester
## immobile tue. À nombre PAIR, l'axe est vide et le pattern ne fait plus que contraindre
## la position. Ce sont deux intentions OPPOSÉES, et elles se décident par un nombre —
## que `burst_count = 5` par défaut choisirait tout seul si personne ne l'écrit.
func test_an_aimed_salvo_never_chooses_its_own_parity() -> void:
	var aimed := 0
	for file in _enemy_paths():
		var data: EnemyData = load(file)
		if data == null or data.fire != EnemyData.Fire.AIMED:
			continue
		aimed += 1
		assert_eq(data.burst_count % 2, 1,
			"%s vise en nombre impair (%d) : une balle sur l'axe" % [file, data.burst_count])
	assert_true(aimed > 0, "au moins une Resource emploie la salve visée")

## Les schémas se distinguent par leur FORME (enemy_fire.gd) : deux unités qui tirent
## pareil ne sont qu'une unité. La vague doit employer au moins trois schémas distincts,
## sinon la variété de tir retombe à ce qu'elle était — un seul.
func test_the_wave_speaks_more_than_one_language() -> void:
	var schemes := {}
	for path: String in _scene_paths():
		var file := path.replace("res://scenes/enemies/", ENEMY_DIR + "/").replace(".tscn", ".tres")
		var data: EnemyData = load(file)
		if data == null:
			continue
		schemes[data.fire] = true
	assert_true(schemes.size() >= 3,
		"la vague emploie %d schémas de tir distincts, il en faut au moins 3" % schemes.size())

## Le silence d'ouverture (spec §5.2, `LOI-EXP-07`). Le joueur découvrait qu'il se déplace
## en se faisant tirer dessus : le premier chasseur tombait à 0,3 s.
##
## ⚠️ La garde porte sur l'HORAIRE CALCULÉ, pas sur `lead_in`. Vérifier le champ ne
## prouverait rien — c'est `build_schedule()` qui décide de la date d'un spawn, et c'est
## lui qui pourrait cesser d'en tenir compte sans qu'aucun autre test ne bouge.
const CALM_SECONDS := 1.5

func test_the_player_gets_the_sky_to_himself_first() -> void:
	var schedule := WaveSpawner.build_schedule(OpeningWave)
	var times: PackedFloat32Array = schedule["times"]
	assert_true(times.size() > 0, "la vague a des spawns")
	var first := times[0]
	for t in times:
		first = minf(first, t)
	assert_true(first >= CALM_SECONDS,
		"le premier ennemi arrive à %.2f s, il en faut au moins %.1f" % [first, CALM_SECONDS])

## Le silence décale TOUT le bloc : il ne doit pas écraser le rythme déjà réglé entre les
## entrées. Une implémentation qui ne retarderait que la première entrée passerait le test
## ci-dessus et casserait la vague en silence.
func test_the_calm_does_not_rewrite_the_rhythm() -> void:
	var schedule := WaveSpawner.build_schedule(OpeningWave)
	var times: PackedFloat32Array = schedule["times"]
	var span := times[times.size() - 1] - times[0]
	var raw_first := INF
	var raw_last := -INF
	for entry in OpeningWave.entries:
		raw_first = minf(raw_first, entry.time_offset)
		raw_last = maxf(raw_last, entry.time_offset + (entry.count - 1) * entry.spacing)
	assert_almost_eq(span, raw_last - raw_first, 0.01,
		"la vague garde exactement sa durée, elle est seulement décalée")
