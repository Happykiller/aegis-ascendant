extends "res://tests/test_case.gd"
## Les quatre salves de poupe : evenementielles, endormies, et sans lendemain.
##
## ⚠️ CE QUE CE BANC GARDE N'EST PAS LEUR CONTENU — il s'equilibre en jouant — MAIS LEUR
## CABLAGE. Une salve dont le semeur manque dans la scene, ou qui demarrerait toute seule, ne
## produit AUCUNE erreur : elle ne se voit qu'en jouant quatre minutes de survol, et seulement
## si l'on regarde au bon moment.

const SCENE := "res://scenes/gameplay/cortege.tscn"
const SALVOS := ["SternSalvoA", "SternSalvoB", "SternSalvoC", "SternSalvoD"]
const WAVES := {
	"SternSalvoA": "res://resources/encounters/wave_cortege_stern_a.tres",
	"SternSalvoB": "res://resources/encounters/wave_cortege_stern_b.tres",
	"SternSalvoC": "res://resources/encounters/wave_cortege_stern_c.tres",
	"SternSalvoD": "res://resources/encounters/wave_cortege_stern_d.tres",
}

## Les proprietes d'un noeud de la scene, lues sans monter la scene.
func _node_props(nom: String) -> Dictionary:
	var packed: PackedScene = load(SCENE)
	assert_true(packed != null, "la scene du niveau 2 se charge")
	if packed == null:
		return {}
	var etat := packed.get_state()
	for i in etat.get_node_count():
		if String(etat.get_node_name(i)) != nom:
			continue
		var out := {}
		for j in etat.get_node_property_count(i):
			out[String(etat.get_node_property_name(i, j))] = etat.get_node_property_value(i, j)
		return out
	return {}

## ⚠️ QUATRE SEMEURS, UN PAR EVENEMENT. Un seul deroulerait une ligne de temps : la salve du
## second moteur tomberait a la trente-huitieme seconde, que le joueur l'ait arrache ou non.
func test_the_scene_carries_one_spawner_per_salvo() -> void:
	for nom in SALVOS:
		var props := _node_props(nom)
		assert_true(not props.is_empty(), "la scene porte %s" % nom)
		assert_true(props.has("wave") and props["wave"] != null,
			"%s a sa vague" % nom)

## ⚠️ ET ILS DORMENT. `autostart` au defaut (vrai) ferait cracher les quatre salves des la
## PREMIERE seconde du niveau — a quatre cents metres de la poupe, pendant la reception de
## proue. Aucune erreur, aucun test rouge : juste un niveau 2 devenu injouable au tronçon 01.
func test_no_salvo_starts_on_its_own() -> void:
	for nom in SALVOS:
		var props := _node_props(nom)
		assert_true(props.has("autostart"),
			"%s declare `autostart` explicitement — le defaut est VRAI" % nom)
		assert_false(bool(props.get("autostart", true)),
			"%s attend son evenement" % nom)

## ⚠️ « DES VAGUES D'ENNEMIS DE PLUSIEURS TYPES » (operateur, 2026-09-07). Une salve d'une seule
## coque se lit comme une repetition ; c'est la variete qui fait qu'on change de facon de jouer
## d'une salve a l'autre.
func test_each_salvo_mixes_at_least_two_hulls() -> void:
	for nom in SALVOS:
		var wave: WaveData = load(WAVES[nom])
		assert_true(wave != null, "%s : la vague se charge" % nom)
		if wave == null:
			continue
		var coques := {}
		for entry in wave.entries:
			if entry.enemy_scene != null:
				coques[entry.enemy_scene.resource_path] = true
		assert_true(coques.size() >= 2,
			"%s melange %d coques differentes" % [nom, coques.size()])

## Et le jeu de salves couvre plusieurs familles du bestiaire, pas la meme deux fois.
func test_the_four_salvos_do_not_repeat_themselves() -> void:
	var vues := {}
	for nom in SALVOS:
		var wave: WaveData = load(WAVES[nom])
		if wave == null:
			continue
		for entry in wave.entries:
			if entry.enemy_scene != null:
				vues[entry.enemy_scene.resource_path] = true
	assert_true(vues.size() >= 6,
		"les quatre salves piochent dans %d coques du bestiaire" % vues.size())

## Chaque vague passe ses propres invariants.
func test_every_salvo_validates() -> void:
	for nom in SALVOS:
		var wave: WaveData = load(WAVES[nom])
		if wave == null:
			continue
		var errors := wave.validate()
		assert_eq(errors.size(), 0, "%s : %s" % [nom, ", ".join(errors)])

## ⚠️ ET AUCUNE N'EST DEMESUREE. La spec §19 reste vraie sur le fond — « les moteurs sont les
## protagonistes ». Une salve de trente coques ferait de la phase finale un combat de vagues
## avec des verrous en decor.
func test_no_salvo_drowns_the_engines() -> void:
	for nom in SALVOS:
		var wave: WaveData = load(WAVES[nom])
		if wave == null:
			continue
		var total := wave.total_enemy_count()
		assert_true(total >= 4 and total <= 16,
			"%s lache %d coques — assez pour peser, pas assez pour voler la scene" % [nom, total])
