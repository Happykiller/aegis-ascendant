extends "res://tests/test_case.gd"
## Le jeu porte une version, et une seule.
##
## ⚠️ CE FICHIER GARDE UN LIEN QUI NE PEUT PAS S'ÉCRIRE DANS LE CODE. La version vit dans
## `project.godot` ; trois consommateurs la lisent — l'écran-titre, l'écran de pause, et
## `scripts/release.sh`, qui en dérive le tag GitHub `vX.Y.Z`. Rien dans GDScript ne peut
## empêcher quelqu'un d'y écrire « 0.2 », « v0.2.0 » ou « 0.2.0-rc1 » : le jeu se lancerait
## sans un mot, l'écran afficherait la chaîne telle quelle, et la publication produirait un
## tag qu'on ne pourrait plus corriger — un tag déjà téléchargé ne se reprend pas.

func test_the_project_declares_a_semver() -> void:
	var version := GameVersion.current()
	assert_true(GameVersion.is_semver(version),
		"config/version = « %s » : il faut MAJEUR.MINEUR.CORRECTIF" % version)

func test_semver_rejects_what_a_tag_could_not_carry() -> void:
	for bad in ["", "0.2", "v0.2.0", "0.2.0-rc1", "0.2.0.1", "0.02.0", "a.b.c", "0..0"]:
		assert_false(GameVersion.is_semver(bad), "« %s » n'est pas une version" % bad)
	for good in ["0.0.0", "0.2.0", "1.0.0", "10.20.30"]:
		assert_true(GameVersion.is_semver(good), "« %s » en est une" % good)

## Le libellé affiché contient la version, sans la réécrire : c'est ce qu'un testeur va
## nous citer quand il rapportera un défaut.
func test_the_label_shows_the_version() -> void:
	var label := GameVersion.label()
	assert_true(label.contains(GameVersion.current()),
		"« %s » doit contenir la version du projet" % label)
	assert_true(label.begins_with("v"), "« %s » commence par v" % label)
