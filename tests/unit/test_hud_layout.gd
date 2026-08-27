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

# --- La repousse d'une sous-cible ------------------------------------------

## ⚠️ LE DÉFAUT NOMMÉ AU SECOND PLAYTEST DU 2026-08-27 : « quand l'une d'elles est 100 %
## rechargée, TOUTES passent à 100 % ». La cause n'était pas dans la logique du boss — les
## appendices repoussent bel et bien chacun sur son minuteur — mais **dans la jauge** : une
## sous-cible à terre affiche une barre PLEINE, seulement plus sombre. Rien n'y lit « vide »,
## donc la rangée entière se lit comme opérationnelle dès qu'une seule redevient vive.
##
## La repousse est désormais une VRAIE barre, par-dessus la sombre. Ce test garde qu'elle
## dise la vérité : une sous-cible à mi-repousse doit occuper la MOITIÉ de sa jauge, pas la
## totalité.
func test_a_regrowing_target_shows_how_far_it_has_come_not_a_full_bar() -> void:
	var hud: Control = track(FighterHudScript.new()) as Control
	hud._ready()
	hud.show_boss("TEST")
	hud.set_boss_limbs(PackedStringArray(["A", "B", "C"]))
	hud.set_boss_limb(0, 0.0, false)
	hud.set_boss_limb_regen(0, 0.5)
	var regen: ColorRect = hud._limb_regens[0]
	assert_true(regen.visible, "la repousse se voit")
	assert_almost_eq(regen.size.x, FighterHudScript.LIMB_GAUGE_WIDTH * 0.5, 0.5,
		"à mi-repousse, la barre fait la moitié de la jauge")
	assert_almost_eq(regen.size.y, FighterHudScript.LIMB_GAUGE_HEIGHT, 0.01,
		"et toute la hauteur : un filet de deux pixels ne se voyait pas")

## Elle s'efface dès que la sous-cible est revenue — sinon elle resterait en travers d'une
## jauge de santé qui, elle, redevient la vérité.
func test_the_regrowth_bar_clears_the_moment_the_target_is_back() -> void:
	var hud: Control = track(FighterHudScript.new()) as Control
	hud._ready()
	hud.show_boss("TEST")
	hud.set_boss_limbs(PackedStringArray(["A", "B", "C"]))
	hud.set_boss_limb(1, 0.0, false)
	hud.set_boss_limb_regen(1, 0.9)
	assert_true(hud._limb_regens[1].visible, "elle monte")
	hud.set_boss_limb(1, 1.0, true)
	assert_false(hud._limb_regens[1].visible, "et disparaît au retour")

## La couleur doit être FRANCHE. Le vert « limité » de la charte a été jugé « trop subtil,
## d'une couleur foncée pas visible » en jouant : la garde porte sur la luminosité, pas sur
## la teinte, qui reste libre de bouger.
func test_the_regrowth_colour_is_bright_enough_to_be_seen() -> void:
	var green: Color = FighterHudScript.REGEN_GREEN
	assert_true(green.get_luminance() > 0.45,
		"luminance %.2f — en dessous, on doit chercher le signal au lieu de le voir"
			% green.get_luminance())
	assert_true(green.g > green.r and green.g > green.b, "et c'est bien un vert")
