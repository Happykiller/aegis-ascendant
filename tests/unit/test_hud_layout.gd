extends "res://tests/test_case.gd"
## Placement des panneaux du HUD de combat.
##
## POURQUOI CE TEST EXISTE — le bandeau de vie du boss chevauchait la jauge de
## bouclier, et le défaut a survécu à toutes les captures : il n'apparaît qu'une fois
## le **mini-boss atteint**, c'est-à-dire après plusieurs minutes de jeu réel. Aucune
## capture automatisée ne va là-bas. C'est le cas type de
## `.claude/resources/pratique-verifier-par-test.md` : quand l'événement à observer
## demande de la chance ou du temps, la capture est le mauvais outil.
##
## La cause était une erreur de géométrie dans `_panel`, dont la condition portait sur
## « ancre différente de 0 » au lieu de « ancre égale à 1 » : l'ancre CENTRALE tombait
## dans la branche « bord droit », et le bandeau de boss s'étalait de centre-1200 à
## centre-400 au lieu de centre-400 à centre+400.
##
## Le runner tourne en mode `--script` : le HUD est instancié à la main, jamais ajouté
## à l'arbre. On lit donc les ancres et les offsets, et on refait le calcul de Godot —
## `bord = ancre * taille_viewport + offset` — plutôt que d'interroger `get_rect()`,
## qui n'a pas de parent pour se résoudre.

const FighterHudScript := preload("res://scripts/ui/fighter_hud.gd")

func _viewport() -> Vector2:
	return Vector2(
		float(ProjectSettings.get_setting("display/window/size/viewport_width", 1920)),
		float(ProjectSettings.get_setting("display/window/size/viewport_height", 1080)))

## Rectangle effectif d'un Control ancré, tel que Godot le résoudrait.
func _rect_of(control: Control) -> Rect2:
	var size := _viewport()
	var left := control.anchor_left * size.x + control.offset_left
	var right := control.anchor_right * size.x + control.offset_right
	var top := control.anchor_top * size.y + control.offset_top
	var bottom := control.anchor_bottom * size.y + control.offset_bottom
	return Rect2(left, top, right - left, bottom - top)

## HUD construit, hors arbre. `_ready()` ne fait que bâtir des nœuds et appeler
## `set_process` — rien qui réclame un arbre, un autoload ou un rendu.
func _hud() -> CanvasLayer:
	var hud: CanvasLayer = FighterHudScript.new()
	hud._ready()
	return hud

func _panels(hud: CanvasLayer) -> Array[Panel]:
	var found: Array[Panel] = []
	for child in hud.get_children():
		var panel := child as Panel
		if panel != null:
			found.append(panel)
	return found

func test_the_hud_builds_its_four_panels() -> void:
	var hud := _hud()
	assert_eq(_panels(hud).size(), 4, "shield, score, lives and boss panels are built")
	hud.free()

## LE test. Le bandeau de boss est le seul panneau ancré au centre : c'est lui que
## l'erreur de géométrie envoyait sur la jauge de bouclier.
func test_the_boss_banner_never_overlaps_another_panel() -> void:
	var hud := _hud()
	var boss := _rect_of(hud._boss_panel)
	for panel in _panels(hud):
		if panel == hud._boss_panel:
			continue
		assert_false(boss.intersects(_rect_of(panel)),
			"the boss banner (%s) clears the panel at %s" % [boss, _rect_of(panel)])
	hud.free()

func test_the_boss_banner_is_centred() -> void:
	var hud := _hud()
	var boss := _rect_of(hud._boss_panel)
	var centre := _viewport().x * 0.5
	assert_almost_eq(boss.position.x + boss.size.x * 0.5, centre, 0.5,
		"the boss banner is centred on the screen")
	hud.free()

## Un panneau qui sort du cadre est toujours un défaut de placement, jamais un choix :
## le HUD n'a aucune raison de déborder.
func test_no_panel_leaves_the_screen() -> void:
	var hud := _hud()
	var size := _viewport()
	for panel in _panels(hud):
		var rect := _rect_of(panel)
		assert_true(rect.position.x >= 0.0 and rect.position.y >= 0.0
				and rect.end.x <= size.x and rect.end.y <= size.y,
			"panel %s stays inside %s" % [rect, size])
	hud.free()

## L'ancre 1,0 doit bien accrocher le bord opposé — c'est la moitié du contrat de
## `_panel`, et la corriger pour le centre ne doit pas l'avoir cassée.
func test_right_and_bottom_anchored_panels_hang_off_their_edge() -> void:
	var hud := _hud()
	var size := _viewport()
	var score := _rect_of(_panels(hud)[1])
	var lives := _rect_of(_panels(hud)[2])
	assert_almost_eq(score.end.x, size.x - 28.0, 0.5, "the score panel hugs the right margin")
	assert_almost_eq(lives.end.y, size.y - 28.0, 0.5, "the lives panel hugs the bottom margin")
	hud.free()
