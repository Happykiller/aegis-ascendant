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

const ENTRY_PATHS: Array[String] = [
	"res://resources/codex/specter_9.tres",
	"res://resources/codex/needle_scout.tres",
	"res://resources/codex/crescent_interceptor.tres",
	"res://resources/codex/choir_harvester.tres",
	"res://resources/codex/pale_leviathan.tres",
]

func _entries() -> Array[CodexEntry]:
	var found: Array[CodexEntry] = []
	for path in ENTRY_PATHS:
		var entry := load(path) as CodexEntry
		if entry != null:
			found.append(entry)
	return found

func test_every_entry_loads() -> void:
	for path in ENTRY_PATHS:
		assert_true(load(path) as CodexEntry != null, "%s loads as a CodexEntry" % path)

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

## Lecture d'un `@export` de scène SANS instancier : c'est ce qui évite de faire
## tourner `boss_controller._ready()`, donc du gameplay, dans un écran de menu.
func test_boss_values_are_read_from_the_scene() -> void:
	var leviathan := load("res://resources/codex/pale_leviathan.tres") as CodexEntry
	assert_true(leviathan.boss_scene != null, "the Leviathan entry points at its boss scene")
	assert_eq(leviathan.hull_points(), 950.0, "hull points come from pale_leviathan.tscn")
	assert_eq(leviathan.phase_count(), 4, "phase count comes from pale_leviathan.tscn")

## Le bestiaire annonce huit profils de vol pour une seule coque de Needle Scout.
## Si une variante disparaît des Resources, la fiche doit le dire, pas l'ignorer.
func test_needle_scout_lists_every_flight_profile() -> void:
	var scout := load("res://resources/codex/needle_scout.tres") as CodexEntry
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
	entry.hull_scene = (load("res://resources/codex/specter_9.tres") as CodexEntry).hull_scene
	entry.player_stats = load("res://resources/player/specter9_stats.tres") as PlayerStats
	entry.enemy_data = load("res://resources/enemies/needle_scout.tres") as EnemyData
	var errors := entry.validate()
	assert_true(not errors.is_empty(), "two stats sources are rejected")
