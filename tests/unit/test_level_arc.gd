extends "res://tests/test_case.gd"
## L'ARC D'UN NIVEAU, devenu une donnee (ADR-0039, derniere couche).
##
## ⚠️ CE QU'IL REMPLACE. Les six temps du niveau 1 s'enchainaient a la main, chacun appelant le
## suivant depuis son propre evenement de fin : `_on_wave_cleared` -> `_start_mini_boss` ->
## `_on_mini_boss_defeated` -> `_start_asteroid_field` -> ... a travers 1 469 lignes. Personne ne
## pouvait dire « voici l'arc » sans lire le fichier entier, et le reordonner demandait de
## relire les six.

const ArcScript := preload("res://resources/data/level_arc.gd")
const BeatScript := preload("res://resources/data/level_beat.gd")
const OSSANE := "res://resources/levels/ossane_arc.tres"

func _beat(id: StringName, kind: int) -> LevelBeat:
	var beat := BeatScript.new() as LevelBeat
	beat.id = id
	beat.kind = kind
	return beat

func test_the_shipped_arc_validates() -> void:
	var arc: LevelArc = load(OSSANE)
	var errors := arc.validate()
	assert_eq(errors.size(), 0, "l'arc du couloir d'Ossane est valide : %s" % str(errors))

## ⚠️ L'ARC SE LIT D'UN SEUL TENANT, et c'est tout ce qu'on lui demande. Ce test EST cette
## lecture : si l'ordre change, il faut le dire ici.
func test_the_ossane_arc_reads_as_seven_beats_in_order() -> void:
	var arc: LevelArc = load(OSSANE)
	var attendu := ["FIGHTER_WAVES", "MINI_BOSS", "ASTEROID_FIELD", "BOSS_APPROACH",
		"FINAL_BOSS", "DOCKING", "VICTORY"]
	assert_eq(arc.size(), attendu.size(), "sept temps")
	for i in attendu.size():
		assert_eq(String(arc.at(i).id), attendu[i], "temps %d" % (i + 1))
	# ⚠️ LES DEUX BOSS PORTENT LEUR SCORE ET LEUR MISE EN SCENE EN DONNEES : c'etait 5000 et
	# 20000 ecrits en dur dans deux fonctions differentes du script du niveau.
	assert_eq(arc.at(arc.index_of(&"MINI_BOSS")).boss_score, 5000, "le mini-boss vaut 5000")
	assert_eq(String(arc.at(arc.index_of(&"MINI_BOSS")).boss_stage), "harvester",
		"et il a sa mise en scene")
	# ⚠️ L'ORDRE DU BANDEAU DU BOSS FINAL EST UNE DONNEE, et c'est le piege le plus couteux de
	# tout le fichier : `show_boss` ETEINT la rangee de pastilles, `begin()` les rallume.
	assert_true(arc.at(arc.index_of(&"FINAL_BOSS")).boss_banner_first,
		"le boss final annonce AVANT de commencer, sinon ses quatre pastilles sortent eteintes")

## ⚠️ ON CHERCHE PAR NOM, ON NE COMPTE PAS. Un rang dans une liste qu'on reordonne n'est pas une
## identite (ADR-0034) — et c'est exactement ce qu'un arc est fait pour permettre : reordonner.
func test_a_beat_is_found_by_name_never_by_rank() -> void:
	var arc: LevelArc = load(OSSANE)
	assert_eq(arc.index_of(&"FINAL_BOSS"), 4, "le boss final est le cinquieme AUJOURD'HUI")
	assert_eq(arc.index_of(&"NEXISTE_PAS"), -1, "un nom inconnu rend -1, il ne plante pas")

func test_two_beats_of_the_same_name_are_refused() -> void:
	var arc := ArcScript.new() as LevelArc
	arc.beats = [_beat(&"A", BeatScript.Kind.SCRIPTED), _beat(&"A", BeatScript.Kind.SCRIPTED)]
	# ⚠️ SANS CETTE GARDE, LE BRIEFING DE PAUSE DEVIENT FAUX pour l'un des deux : la recherche
	# rend le premier, en silence.
	assert_true(arc.validate().size() > 0, "deux temps de meme nom sont refuses")

func test_a_wave_beat_without_a_spawner_is_refused() -> void:
	var beat := _beat(&"VAGUE", BeatScript.Kind.WAVE)
	assert_true(beat.validate().size() > 0,
		"un temps de type VAGUE sans semeur : le directeur ne saurait pas quoi demarrer")
	beat.spawner_name = &"WaveSpawner"
	assert_eq(beat.validate().size(), 0, "avec son semeur, il est valide")

func test_a_boss_beat_without_a_scene_is_refused() -> void:
	var beat := _beat(&"BOSS", BeatScript.Kind.BOSS)
	assert_true(beat.validate().size() > 0, "un temps de type BOSS sans scene n'a rien a monter")

func test_a_beat_with_no_name_is_refused() -> void:
	# ⚠️ Le nom est AUSSI la cle du briefing de pause : sans lui, l'ecran de pause reste muet
	# sans qu'aucune erreur ne soit levee.
	var beat := _beat(&"", BeatScript.Kind.SCRIPTED)
	assert_true(beat.validate().size() > 0, "un temps sans nom est refuse")
