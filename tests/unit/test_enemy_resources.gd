extends "res://tests/test_case.gd"
## Les .tres d'ennemis livrés — validés en chargeant les VRAIS fichiers.
##
## Les autres tests d'ennemis construisent leurs EnemyData à la main : ils prouvent
## que les trajectoires sont justes, jamais que les données EXPÉDIÉES le sont. Une
## Resource incohérente (hook_delay à zéro, projectile absent, trajectoire réglée
## sur un indice devenu invalide) passait donc toute la porte de qualité, pour ne
## se manifester qu'à l'exécution, en push_error depuis EnemyController._ready().
##
## Ce fichier ferme ce trou, et sert de garde-fou à la sérialisation par INDICE de
## l'enum Path : réordonner l'enum réaffecterait silencieusement les trajectoires,
## et les signatures vérifiées ici ne correspondraient plus.

const ENEMY_DIR := "res://resources/enemies"

func _enemy_paths() -> PackedStringArray:
	var found := PackedStringArray()
	var dir := DirAccess.open(ENEMY_DIR)
	if dir == null:
		return found
	for file in dir.get_files():
		# L'export ajoute un .remap aux ressources ; en source on lit le .tres.
		if file.ends_with(".tres"):
			found.append("%s/%s" % [ENEMY_DIR, file])
	return found

func test_the_shipped_enemy_resources_are_all_valid() -> void:
	var files := _enemy_paths()
	assert_true(files.size() > 0, "on a bien trouvé des ennemis dans %s" % ENEMY_DIR)
	for file in files:
		var data: EnemyData = load(file)
		if data == null:
			fail("%s ne se charge pas comme EnemyData" % file)
			continue
		var errors := data.validate()
		assert_true(errors.is_empty(), "%s est valide (%s)" % [file, ", ".join(errors)])

## Chaque Resource doit désigner une trajectoire qui EXISTE. Un indice hors enum
## retomberait silencieusement sur le WEAVE par défaut du match — un ennemi qui ne
## fait pas ce que sa donnée annonce, sans la moindre erreur.
func test_every_enemy_resource_points_at_a_real_path() -> void:
	var known := EnemyData.Path.values()
	for file in _enemy_paths():
		var data: EnemyData = load(file)
		if data == null:
			continue
		assert_true(known.has(data.path),
			"%s utilise une trajectoire connue (indice %d)" % [file, data.path])

## Le crochet est la seule trajectoire qui divise par hook_delay. Un zéro y produit
## une position NaN, que rien n'attrape ensuite : l'ennemi disparaît du plan de jeu
## sans erreur. La règle de validate() est donc vérifiée sur la donnée réelle.
func test_crescent_hook_resources_declare_a_usable_hook_delay() -> void:
	for file in _enemy_paths():
		var data: EnemyData = load(file)
		if data == null or data.path != EnemyData.Path.CRESCENT_HOOK:
			continue
		assert_true(data.hook_delay > 0.0,
			"%s déclare un hook_delay exploitable (%f)" % [file, data.hook_delay])
		var late := EnemyPath.position_at(data, 3.0, Vector2(-4.0, 9.0))
		assert_true(is_finite(late.x) and is_finite(late.y),
			"%s produit une position finie (obtenu %s)" % [file, late])
