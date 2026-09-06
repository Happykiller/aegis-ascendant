extends "res://tests/test_case.gd"
## Jusqu'où va un projectile — et ce n'est pas une question de portée.
##
## ⚠️ LE DÉFAUT NOMMÉ AU PLAYTEST DU 2026-08-27 : « mes tirs ne vont pas jusqu'au bout de
## l'écran, cela fait étrange ». Ils ne s'arrêtaient pas : ils **disparaissaient** dans le
## cadre, à environ 170 px du haut. `BOUNDS` est le terrain de JEU, le champ VISIBLE en
## montre davantage — et la coupe se faisait sur le premier.
##
## Ce fichier garde le rapport entre la ligne de coupe et la ligne d'APPARITION des ennemis :
## un bolt doit pouvoir dépasser franchement l'endroit d'où sortent les coques, sinon il
## s'éteint là où le joueur regarde encore.

const WAVES := ["res://resources/encounters/wave_graybox_01.tres",
	"res://resources/encounters/wave_asteroid_field_01.tres"]
const PULSE: ProjectileData = preload("res://resources/weapons/pulse_shot.tres")

## Marge exigée AU-DESSUS du bord haut de l'ÉCRAN. En dessous, la coupe se voit.
##
## ⚠️ LA RÈGLE A CHANGÉ DE RÉFÉRENCE LE 2026-09-06, ET ELLE S'EST RAPPROCHÉE DU DÉFAUT. Elle
## se calait sur la ligne d'APPARITION des ennemis, qui servait de mesure indirecte du haut de
## l'écran tant que les coques naissaient dans le cadre. Elles n'y naissent plus : la ligne
## d'apparition est passée à y = 15, au-dessus du bord haut, et exiger 2,5 de plus qu'elle
## aurait demandé une coupe à 17,5 — pour un défaut qui se juge à 12,28.
##
## On mesure donc le cadre. C'est aussi ce que l'opérateur décrivait mot pour mot : « mes tirs
## ne vont pas jusqu'au bout de l'écran ».
const SLACK_ABOVE_SCREEN := 2.5
const CORTEGE_SCENE := "res://scenes/gameplay/graybox.tscn"

## Le haut du cadre, relu dans la scène — jamais recopié.
func _screen_top() -> float:
	var packed: PackedScene = load(CORTEGE_SCENE)
	assert_true(packed != null, "la scene de jeu se charge")
	var etat := packed.get_state()
	var camera := Transform3D.IDENTITY
	var fov := 0.0
	for i in etat.get_node_count():
		if String(etat.get_node_name(i)) != "Camera3D":
			continue
		for j in etat.get_node_property_count(i):
			var nom := String(etat.get_node_property_name(i, j))
			if nom == "transform":
				camera = etat.get_node_property_value(i, j)
			elif nom == "fov":
				fov = etat.get_node_property_value(i, j)
	assert_true(fov > 0.0, "le fov de la camera se lit")
	return GameplayPlane.visible_frame(camera, fov).end.y

func _highest_spawn() -> float:
	var highest := -1e9
	for path in WAVES:
		var wave: WaveData = load(path)
		for entry in wave.entries:
			highest = maxf(highest, entry.spawn_plane_position.y)
	return highest

func test_a_bolt_outlives_the_screen_and_reaches_what_appears_on_it() -> void:
	var cull := GameplayPlane.BOUNDS.end.y + BulletManager.CULL_MARGIN
	var haut := _screen_top()
	assert_true(cull >= haut + SLACK_ABOVE_SCREEN,
		"coupe à y=%.2f pour un ecran qui monte a y=%.2f — il faut %.1f d'ecart, sinon le bolt s'eteint la ou le joueur regarde encore"
			% [cull, haut, SLACK_ABOVE_SCREEN])
	# ⚠️ ET IL DOIT ATTEINDRE CE QUI ENTRE. Une coque nait desormais HORS du cadre : si la coupe
	# tombait sous sa ligne de naissance, le joueur ne pourrait pas la toucher a l'instant ou
	# elle devient visible — le defaut des tourelles, repris par les balles.
	var spawn := _highest_spawn()
	assert_true(cull >= spawn,
		"coupe à y=%.2f pour des apparitions a y=%.2f : une coque serait intouchable en entrant"
			% [cull, spawn])

## ⚠️ ET CE N'ÉTAIT PAS LA PORTÉE. Le `ttl` autorise bien plus de trajet que le terrain n'en
## demande : allonger la durée de vie n'aurait rien corrigé, et cette garde empêche qu'on
## croie l'inverse la prochaine fois.
func test_the_lifetime_was_never_the_limit() -> void:
	var travel := PULSE.speed * PULSE.ttl
	var needed := GameplayPlane.BOUNDS.size.y + BulletManager.CULL_MARGIN
	assert_true(travel > needed,
		"un bolt peut parcourir %.1f u pour un besoin de %.1f — le ttl n'a jamais borné"
			% [travel, needed])
