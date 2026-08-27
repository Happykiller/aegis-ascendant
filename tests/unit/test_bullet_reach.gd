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

## Marge exigée AU-DESSUS du plus haut point d'apparition. En dessous, la coupe se voit.
const SLACK_ABOVE_SPAWNS := 2.5

func _highest_spawn() -> float:
	var highest := -1e9
	for path in WAVES:
		var wave: WaveData = load(path)
		for entry in wave.entries:
			highest = maxf(highest, entry.spawn_plane_position.y)
	return highest

func test_a_bolt_outlives_the_line_the_enemies_come_from() -> void:
	var cull := GameplayPlane.BOUNDS.end.y + BulletManager.CULL_MARGIN
	var spawn := _highest_spawn()
	assert_true(cull >= spawn + SLACK_ABOVE_SPAWNS,
		"coupe à y=%.1f pour des apparitions à y=%.1f — il faut %.1f d'écart"
			% [cull, spawn, SLACK_ABOVE_SPAWNS])

## ⚠️ ET CE N'ÉTAIT PAS LA PORTÉE. Le `ttl` autorise bien plus de trajet que le terrain n'en
## demande : allonger la durée de vie n'aurait rien corrigé, et cette garde empêche qu'on
## croie l'inverse la prochaine fois.
func test_the_lifetime_was_never_the_limit() -> void:
	var travel := PULSE.speed * PULSE.ttl
	var needed := GameplayPlane.BOUNDS.size.y + BulletManager.CULL_MARGIN
	assert_true(travel > needed,
		"un bolt peut parcourir %.1f u pour un besoin de %.1f — le ttl n'a jamais borné"
			% [travel, needed])
