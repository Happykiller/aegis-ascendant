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
