extends "res://tests/test_case.gd"
## Intégrité des fiches du bestiaire (`resources/codex/*.tres`).
##
## Ces tests portent sur les fichiers RÉELLEMENT embarqués, pas sur des fiches
## fabriquées à la main : le bestiaire n'affiche presque aucune valeur propre, il
## pointe vers les Resources de gameplay et vers les `.glb`. Un pointeur qui casse ne
## se voit nulle part ailleurs — la fiche afficherait simplement des tirets, en
## silence, sur un écran que personne n'ouvre pendant les tests.
##
## Le runner tourne en mode `--script` : pas d'autoload, pas de rendu. Tout ici se
## limite à charger des Resources et à lire dedans.

## ⚠️ On lit la liste QUE L'ÉCRAN EMBARQUE, pas une copie. Une première version
## énumérait les cinq chemins ici, en annonçant porter « sur les fichiers réellement
## embarqués » — c'était faux : une sixième fiche ajoutée au seul écran serait partie
## en production sans jamais passer par `validate()`, et une fiche retirée de l'écran
## aurait continué d'être validée ici. C'est la deuxième source de vérité que
## `CodexEntry` s'interdit, reproduite dans son propre test.
func _entries() -> Array[CodexEntry]:
	return CodexScreen.ROSTER

func test_the_screen_carries_a_roster() -> void:
	assert_true(not CodexScreen.ROSTER.is_empty(), "the codex screen embeds at least one entry")

func test_no_entry_is_null() -> void:
	for entry in _entries():
		assert_true(entry != null, "no null entry in the embedded roster")

func test_every_entry_validates() -> void:
	for entry in _entries():
		var errors := entry.validate()
		assert_true(errors.is_empty(), "%s is valid (got: %s)" % [entry.display_name, ", ".join(errors)])

func test_every_entry_has_a_hull_scene() -> void:
	for entry in _entries():
		assert_true(entry.hull_scene != null, "%s carries a hull scene" % entry.display_name)

## Les points de structure viennent de trois sources différentes selon la coque
## (PlayerStats, EnemyData, scène de boss). C'est le câblage le plus fragile de la
## fiche : s'il lâche, tout le monde affiche zéro.
func test_hull_points_resolve_for_every_entry() -> void:
	for entry in _entries():
		assert_true(entry.hull_points() > 0.0,
			"%s resolves hull points (got %s)" % [entry.display_name, entry.hull_points()])

## Retrouve une fiche DANS la liste embarquée. La charger par son chemin la
## validerait même après son retrait de l'écran — précisément ce qu'on veut éviter.
func _named(display_name: String) -> CodexEntry:
	for entry in _entries():
		if entry.display_name == display_name:
			return entry
	return null

## Lecture d'un `@export` de scène SANS instancier : c'est ce qui évite de faire
## tourner `boss_controller._ready()`, donc du gameplay, dans un écran de menu.
func test_boss_values_are_read_from_the_scene() -> void:
	var leviathan := _named("The Pale Leviathan")
	assert_true(leviathan != null, "the Leviathan is on the roster")
	assert_true(leviathan.boss_scene != null, "the Leviathan entry points at its boss scene")
	assert_eq(leviathan.hull_points(), 950.0, "hull points come from pale_leviathan.tscn")
	assert_eq(leviathan.phase_count(), 4, "phase count comes from pale_leviathan.tscn")

## ⚠️ LE PIÈGE QUE CE TEST GARDE — un `.tscn` ne sérialise que les propriétés
## SURCHARGÉES. `choir_harvester.tscn` écrit `phase_count = 1`, mais le défaut du
## script vaut 1 lui aussi : une simple sauvegarde depuis l'éditeur ferait disparaître
## la ligne, et la lecture par `SceneState` seule rendrait 0. La fiche basculerait
## alors de « PHASES 1 » à « TOUCHE 2.00 m », en silence. Le Leviathan, lui, ne le
## verrait pas — ses quatre phases diffèrent du défaut.
func test_a_value_left_at_its_default_is_still_read() -> void:
	var script := load("res://scripts/bosses/boss_controller.gd") as Script
	assert_eq(CodexEntry._script_default(script, &"max_health"), 600.0,
		"the script default is recovered when the scene is silent about it")
	assert_eq(CodexEntry._script_default(script, &"phase_count"), 1.0,
		"same for an int export")
	assert_eq(CodexEntry._script_default(script, &"nonexistent_property"), 0.0,
		"an unknown property stays at zero instead of erroring")
	var harvester := _named("Choir Harvester")
	assert_eq(harvester.phase_count(), 1, "the Harvester reports its single phase")

## Le bestiaire annonce huit profils de vol pour une seule coque de Needle Scout.
## Si une variante disparaît des Resources, la fiche doit le dire, pas l'ignorer.
func test_needle_scout_lists_every_flight_profile() -> void:
	var scout := _named("Needle Scout")
	assert_true(scout != null, "the Needle Scout is on the roster")
	assert_eq(scout.variants.size(), 8, "the Needle Scout entry lists its 8 flight profiles")
	for variant in scout.variants:
		assert_true(variant != null, "no null variant in the Needle Scout roster")

## Press Start 2P dessine les capitales accentuées en hauteur de bas-de-casse
## (ADR-0012) : un accent dans un champ affiché en capitales troue le mot. La règle
## ne tient que si elle est testée — à l'œil, sur une capture, le défaut passe.
func test_uppercase_fields_are_pure_ascii() -> void:
	for entry in _entries():
		for value in [entry.designation, entry.hull_class, entry.builder, entry.status]:
			assert_true(not CodexEntry._has_non_ascii(value),
				"%s: uppercase field is pure ASCII (%s)" % [entry.display_name, value])

## La notice, elle, s'affiche en casse normale : les minuscules accentuées y sont
## correctes. On vérifie seulement qu'elle est renseignée — une fiche muette est un
## oubli d'intégration, pas un cas dégradé.
func test_every_entry_has_a_notice() -> void:
	for entry in _entries():
		assert_true(not entry.notice.strip_edges().is_empty(),
			"%s carries a notice" % entry.display_name)

func test_every_entry_has_a_mass() -> void:
	for entry in _entries():
		assert_true(entry.mass_t > 0.0, "%s carries a mass" % entry.display_name)

## Une fiche câblée sur deux sources de valeurs afficherait l'une en ignorant
## l'autre, sans que rien ne le signale. `validate()` doit refuser.
func test_validate_rejects_two_stats_sources() -> void:
	var entry := CodexEntry.new()
	entry.display_name = "Test"
	entry.hull_scene = _named("Specter-9").hull_scene
	entry.player_stats = load("res://resources/player/specter9_stats.tres") as PlayerStats
	entry.enemy_data = load("res://resources/enemies/needle_scout.tres") as EnemyData
	var errors := entry.validate()
	assert_true(not errors.is_empty(), "two stats sources are rejected")
