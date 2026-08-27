extends "res://tests/test_case.gd"
## La loi « les corps ne se chevauchent pas » appliquée aux ennemis (lot 3).
##
## ⚠️ LE MODE D'ÉCHEC QUE CE FICHIER EXISTE POUR EMPÊCHER, ET IL EST DOUBLE.
##
## 1. **Une répulsion effacée.** Une unité sur trajectoire recalcule sa position ENTIÈREMENT
##    à chaque image : `EnemyPath.position_at` est une fonction pure de l'âge. Une poussée
##    écrite dans `plane_position` disparaît donc à l'image suivante, et l'empilement qu'on
##    croyait corrigé se reforme aussitôt. À l'écran ça ne se lit pas comme « ça ne marche
##    pas » mais comme un frémissement — le pire signal, parce qu'il ressemble à du vivant.
##
## 2. **Un kamikaze désamorcé par sa propre collision.** Une mine qui rebondit sur le
##    chasseur au lieu d'exploser n'attaque plus, et rien ne le dit : elle a l'air de
##    fonctionner, elle tourne autour de sa cible. La règle est « le contact EST-il son
##    attaque ? », et elle se vérifie sur les fichiers LIVRÉS, pas sur une intention.

const ENEMY_DIR := "res://resources/enemies"

## Le contact de ces trois-là EST leur attaque : les rendre solides les désarmerait.
const MUST_TRAVERSE := ["choir_mine", "leech_drone", "null_maw"]

func _enemy(name: String) -> EnemyData:
	return load("%s/%s.tres" % [ENEMY_DIR, name]) as EnemyData

func _all() -> Array:
	var found := []
	var dir := DirAccess.open(ENEMY_DIR)
	if dir == null:
		return found
	for file in dir.get_files():
		var clean := file.trim_suffix(".remap")
		if clean.ends_with(".tres"):
			found.append([clean.get_basename(), load("%s/%s" % [ENEMY_DIR, clean])])
	return found

# --- Qui est un corps, qui n'en est pas un -----------------------------------

func test_the_kamikazes_still_go_through() -> void:
	for name in MUST_TRAVERSE:
		var data := _enemy(name)
		assert_true(data != null, "%s se charge" % name)
		if data == null:
			continue
		assert_false(data.solid,
			"%s traverse : son contact EST son attaque, l'arreter la desamorcerait" % name)

func test_every_other_hull_is_a_body() -> void:
	var soft := PackedStringArray()
	for pair in _all():
		var data: EnemyData = pair[1]
		if data != null and not data.solid and not (pair[0] in MUST_TRAVERSE):
			soft.append(pair[0])
	assert_eq(soft.size(), 0,
		"coques traversables non justifiees : %s" % ", ".join(soft))

# --- La répulsion ------------------------------------------------------------

func _unit(data: EnemyData, at: Vector2) -> EnemyController:
	var enemy := track(EnemyController.new()) as EnemyController
	enemy.data = data
	enemy.plane_position = at
	return enemy

func test_two_overlapping_units_push_each_other_apart_by_halves() -> void:
	var data := _enemy("needle_scout")
	var left := _unit(data, Vector2(0.0, 0.0))
	var right := _unit(data, Vector2(0.2, 0.0))
	var wanted := left.body_radius() + right.body_radius()
	var offset := right.plane_position - left.plane_position
	var push := offset.normalized() * ((wanted - offset.length()) * 0.5 * 0.5)
	left.nudge(-push)
	right.nudge(push)
	assert_almost_eq(left._separation.length(), right._separation.length(), 0.0001,
		"chacune prend la MOITIE : entre pairs, aucune des deux n'a raison")
	assert_true(left._separation.x < 0.0 and right._separation.x > 0.0,
		"et elles s'ecartent, elles ne se suivent pas")

## ⚠️ LA GARDE DU DÉFAUT ANTICIPÉ. Une unité sur trajectoire voit sa position réécrite à
## chaque image ; si l'écart n'est pas RÉAPPLIQUÉ après, il n'existe qu'une image.
func test_the_push_survives_a_frame_of_path_recomputation() -> void:
	var data := _enemy("needle_scout")
	assert_eq(data.motion, EnemyData.Motion.PATH, "pre-requis : elle suit une trajectoire")
	var enemy := _unit(data, Vector2(0.0, 5.0))
	enemy.nudge(Vector2(0.8, 0.0))
	var pure := EnemyPath.position_at(data, 0.0, Vector2(0.0, 5.0), EnemyPath.NO_DRIFT)
	enemy._spawn = Vector2(0.0, 5.0)
	enemy._age = 0.0
	# Le VRAI pas d'image, pas une copie de ses quatre lignes : une garde qui reproduit le
	# code reste verte le jour ou le code change.
	enemy.step_position(0.0)
	assert_true(enemy.plane_position.distance_to(pure) > 0.5,
		"l'ecart a survecu au recalcul de la trajectoire (%.2f u)"
			% enemy.plane_position.distance_to(pure))

## Et il s'amortit : l'unité REVIENT sur sa figure dès qu'elle est libre. Une répulsion
## permanente déformerait la nuée jusqu'à ce qu'elle ne dessine plus rien.
func test_the_push_fades_so_the_written_figure_survives() -> void:
	var enemy := _unit(_enemy("needle_scout"), Vector2.ZERO)
	enemy.nudge(Vector2(1.0, 0.0))
	var start := enemy._separation.length()
	for step in 60:
		enemy._separation = enemy._separation.move_toward(Vector2.ZERO,
			EnemyController.SEPARATION_RECOVER * 0.016)
	assert_true(enemy._separation.length() < start * 0.05,
		"l'ecart est retombe (%.3f u apres une seconde)" % enemy._separation.length())

## Un empilement ne peut pas éjecter. Dix poussées dans le même sens restent bornées.
func test_a_pile_up_cannot_fling_a_unit_off_the_screen() -> void:
	var enemy := _unit(_enemy("needle_scout"), Vector2.ZERO)
	for i in 20:
		enemy.nudge(Vector2(1.0, 0.0))
	assert_true(enemy._separation.length() <= EnemyController.SEPARATION_MAX + 0.001,
		"borne a %.2f u malgre vingt poussees" % enemy._separation.length())
