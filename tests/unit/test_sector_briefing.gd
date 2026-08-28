extends "res://tests/test_case.gd"
## Ce que l'ecran de pause rappelle : ou l'on est, et ce qu'on a a y faire (`ADR-0035`).
##
## ⚠️ CE CONTENU N'EXISTAIT NULLE PART DANS LE JEU. Les bannieres annoncent une phase 1,6
## seconde, au moment precis ou le joueur regarde ailleurs — il esquive. Apres quoi plus rien
## ne rappelle l'objectif, a aucun moment de la partie.

const BriefingScript := preload("res://resources/data/sector_briefing.gd")
const BookScript := preload("res://resources/data/briefing_book.gd")
const SHIPPED := "res://resources/dialogue/sector_briefings.tres"
## ⚠️ Prechargé et non nomme : `graybox_root.gd` ne declare pas de `class_name`, et lui en
## donner un pour un test serait laisser le test dicter au jeu.
const GrayboxScript := preload("res://scripts/gameplay/graybox_root.gd")

func _brief(phase: StringName, objectives: PackedStringArray) -> SectorBriefing:
	var b: SectorBriefing = BriefingScript.new()
	b.phase = phase
	b.title = "TITRE"
	b.objectives = objectives
	return b

func test_a_briefing_needs_a_place_and_something_to_do() -> void:
	var vide: SectorBriefing = BriefingScript.new()
	assert_true(vide.validate().size() >= 3, "sans phase, sans titre, sans objectif : trois reproches")
	assert_eq(_brief(&"X", PackedStringArray(["faire ceci"])).validate().size(), 0,
		"avec les trois, il passe")

## ⚠️ TROIS OBJECTIFS AU PLUS. Au-dela ce n'est plus une consigne qu'on relit en pause, c'est
## une liste qu'on parcourt — et le joueur qui met en pause veut se SOUVENIR, pas etudier.
func test_a_briefing_refuses_a_fourth_objective() -> void:
	var trois := _brief(&"X", PackedStringArray(["a", "b", "c"]))
	assert_eq(trois.validate().size(), 0, "trois passent")
	var quatre := _brief(&"X", PackedStringArray(["a", "b", "c", "d"]))
	assert_true(quatre.validate().size() > 0, "le quatrieme est refuse")

func test_an_empty_objective_is_refused() -> void:
	var b := _brief(&"X", PackedStringArray(["a", "   "]))
	assert_true(b.validate().size() > 0, "une puce vide se verrait a l'ecran")

## ⚠️ PAR NOM, JAMAIS PAR RANG — meme regle que les repliques, et pour la meme raison deja
## payee sur les missiles du Leviathan : inserer une phase au milieu de l'enumeration
## suffirait a afficher le mauvais briefing, en silence.
func test_the_book_finds_by_name_and_never_by_rank() -> void:
	var book: BriefingBook = BookScript.new()
	book.briefings = [_brief(&"UN", PackedStringArray(["a"])), _brief(&"DEUX", PackedStringArray(["b"]))]
	assert_true(book.find(&"DEUX") != null, "la seconde se trouve par son nom")
	assert_eq(book.find(&"DEUX").objectives[0], "b", "et c'est bien la sienne")
	assert_true(book.find(&"TROIS") == null,
		"une phase sans briefing rend null — muet plutot que fautif")

func test_the_book_refuses_two_briefings_for_the_same_phase() -> void:
	var book: BriefingBook = BookScript.new()
	book.briefings = [_brief(&"UN", PackedStringArray(["a"])), _brief(&"UN", PackedStringArray(["b"]))]
	var errors := book.validate()
	assert_true(errors.size() > 0, "deux briefings pour une phase : `find` en rendrait un au hasard")

## ⚠️ LES CLES DOIVENT ETRE DE VRAIES PHASES. Une faute de frappe dans un `.tres` ne se voit
## nulle part : l'ecran de pause resterait simplement muet, et personne ne saurait pourquoi.
func test_every_shipped_briefing_names_a_real_phase() -> void:
	var book: BriefingBook = load(SHIPPED)
	assert_true(book != null, "le recueil livre se charge")
	assert_eq(book.validate().size(), 0, "et il est valide : %s" % str(book.validate()))
	var phases := PackedStringArray()
	for key in GrayboxScript.Phase.keys():
		phases.append(String(key))
	for entry in book.briefings:
		assert_true(String(entry.phase) in phases,
			"`%s` n'est pas une phase du niveau (%s)" % [entry.phase, str(phases)])

## Les deux phases que le joueur traverse le plus longtemps doivent etre couvertes : ce sont
## celles ou il met en pause.
func test_the_long_phases_have_a_briefing() -> void:
	var book: BriefingBook = load(SHIPPED)
	for phase in [&"FIGHTER_WAVES", &"ASTEROID_FIELD", &"FINAL_BOSS"]:
		assert_true(book.find(phase) != null, "la phase %s a son briefing" % phase)
