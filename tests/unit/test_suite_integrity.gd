extends "res://tests/test_case.gd"
## La suite se surveille elle-même.
##
## ⚠️ ÉCRIT APRÈS UN ACCIDENT, LE 2026-08-27. Une suppression par expression régulière a vidé
## `test_reactor_rings.gd` de ses DIX-SEPT gardes au lieu des cinq visées — et la porte de
## qualité est restée VERTE, parce qu'un fichier sans test ne peut pas échouer. Le compte de
## méthodes avait baissé de 582 à 565 dans une ligne de résumé que personne ne compare.
##
## C'est le pire mode de panne du dépôt : la couverture disparaît sans bruit, et le premier
## à s'en apercevoir est celui que le défaut atteint en jouant. Un fichier de tests vide est
## désormais une ERREUR.

const UNIT_DIR := "res://tests/unit"

func _unit_files() -> PackedStringArray:
	var found := PackedStringArray()
	var dir := DirAccess.open(UNIT_DIR)
	assert_true(dir != null, "le dossier des tests unitaires est lisible")
	if dir == null:
		return found
	for name in dir.get_files():
		if name.ends_with(".gd"):
			found.append(name)
	return found

func test_the_unit_folder_is_not_empty() -> void:
	assert_true(_unit_files().size() >= 40,
		"la suite compte %d fichiers unitaires" % _unit_files().size())

## LA garde. Un fichier qui ne déclare plus rien a perdu sa couverture, et rien d'autre ne
## le dira.
func test_every_test_file_still_declares_at_least_one_test() -> void:
	var empty := PackedStringArray()
	for name in _unit_files():
		var text := FileAccess.get_file_as_string("%s/%s" % [UNIT_DIR, name])
		if not text.contains("func test_"):
			empty.append(name)
	assert_eq(empty.size(), 0,
		"fichiers de tests SANS AUCUN TEST : %s" % ", ".join(empty))
