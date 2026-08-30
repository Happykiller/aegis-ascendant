extends "res://tests/test_case.gd"
## Ce qui PEUPLE le niveau 2 — et le trou qu'aucune porte de qualite n'a vu.
##
## ⚠️ CE BANC EXISTE A CAUSE D'UNE MESURE, PAS D'UNE INTUITION. Partie complete du 2026-08-30 :
## 208 secondes de survol, QUATORZE ennemis au total (la reception de proue, nettoyee des le
## troncon 01), plus les lachers des sept ponts — qui piochaient dans DEUX coques sur les treize
## du bestiaire. Le niveau 1, lui, en alloue 107 plus 62. Rien de tout cela n'etait faux : la
## coque etait la, les pieces marchaient, les tests etaient verts. Le niveau etait simplement
## VIDE, et c'est le genre de defaut qu'aucun test unitaire ne trouve tout seul.
##
## Ce qui suit garde les deux moities de la reponse : le bestiaire est employe EN ENTIER, et ce
## qu'un pont lache MONTE d'un troncon a l'autre.

const BayScript := preload("res://scripts/gameplay/cortege_bay.gd")
const PATROL := preload("res://resources/encounters/wave_cortege_patrol.tres")
const APPROACH := preload("res://resources/encounters/wave_cortege_approach.tres")
const HULL_DIR := "res://scenes/enemies"

## Toutes les coques que le niveau 2 emploie, par chemin : patrouille, reception, ponts.
func _employed() -> Dictionary:
	var seen := {}
	for wave in [PATROL, APPROACH]:
		for entry in wave.entries:
			if entry != null and entry.enemy_scene != null:
				seen[entry.enemy_scene.resource_path] = true
	for section in BayScript.RELEASE_BY_SECTION.size():
		for path in BayScript.releases_for(section):
			seen[String(path)] = true
	return seen

## ⚠️ CE TEST CASSE QUAND ON AJOUTE UNE COQUE AU BESTIAIRE, ET C'EST VOULU. Une coque neuve qui
## n'apparaitrait nulle part serait exactement ce qui vient d'etre paye : onze coques modelisees,
## reglees, fichees au bestiaire — et jamais rencontrees dans le niveau 2. Le rouge demande une
## DECISION : ou bien elle entre dans le survol, ou bien on ecrit pourquoi elle n'y entre pas.
func test_the_flyby_employs_the_whole_bestiary() -> void:
	var employed := _employed()
	var manquantes := PackedStringArray()
	for file in DirAccess.get_files_at(HULL_DIR):
		if not file.ends_with(".tscn"):
			continue
		var path := "%s/%s" % [HULL_DIR, file]
		if not employed.has(path):
			manquantes.append(file)
	assert_eq(manquantes.size(), 0,
		"le niveau 2 n'emploie pas ces coques : %s — le bestiaire entier doit s'y rencontrer" % str(manquantes))

## Ce qu'un pont lache monte d'un troncon a l'autre. ⚠️ SUR LA TABLE, PAS SUR UN HANGAR MONTE :
## la question est de design, pas de montage, et un pont demande un BulletManager pour exister.
func test_what_a_bay_releases_climbs_from_section_to_section() -> void:
	var scores := []
	for section in BayScript.RELEASE_BY_SECTION.size():
		var total := 0.0
		for path in BayScript.releases_for(section):
			var scene: PackedScene = load(String(path))
			assert_true(scene != null, "la coque %s se charge" % path)
			total += _weight(String(path))
		scores.append(total / float(BayScript.releases_for(section).size()))
	# Le premier troncon accueille, le dernier presse. On ne demande pas une croissance stricte
	# — un palier est du rythme —, on demande que la FIN pese plus lourd que le DEBUT.
	assert_true(scores[scores.size() - 1] > scores[0] * 1.4,
		"le dernier troncon lache du %.0f pour %.0f au premier : sans ecart, sept ponts se valent tous"
			% [scores[scores.size() - 1], scores[0]])

## Le poids d'une coque, lu dans sa Resource de reglage. ⚠️ ON LIT LE SCORE ET NON LES PV : le
## score est ce que le jeu declare comme la valeur d'une coque, PV et menace confondus, et c'est
## la seule mesure que le bestiaire tienne a jour pour les treize.
func _weight(path: String) -> float:
	var slug := path.get_file().get_basename()
	var data: Resource = load("res://resources/enemies/%s.tres" % slug)
	assert_true(data != null, "le reglage de %s existe" % slug)
	return float(data.score_value)

## ⚠️ ET LA PATROUILLE NE DOIT PAS OUVRIR AVANT QUE LA RECEPTION AIT FINI. Les deux se
## superposeraient, le niveau ouvrirait sur son pic de densite au lieu d'y monter — et le seul
## repere de rythme du debut (`wave_cleared` de l'approche) disparaitrait dans le bruit.
func test_the_patrol_opens_after_the_prow_reception_has_cleared() -> void:
	var derniere_reception := 0.0
	for entry in APPROACH.entries:
		derniere_reception = maxf(derniere_reception, entry.time_offset)
	var premiere_patrouille := INF
	for entry in PATROL.entries:
		premiere_patrouille = minf(premiere_patrouille, entry.time_offset)
	assert_true(premiere_patrouille > derniere_reception + 6.0,
		"la patrouille ouvre a %.0f s pour une reception qui pond jusqu'a %.0f s : il faut laisser le plan se vider"
			% [premiere_patrouille, derniere_reception])

## La vague se valide comme n'importe quelle autre — sinon `WaveSpawner` la refuse au montage,
## en une ligne d'erreur qu'un lancement automatise ne lit pas.
func test_the_patrol_wave_validates() -> void:
	var errors := PATROL.validate()
	assert_eq(errors.size(), 0, "la patrouille est valide : %s" % str(errors))
