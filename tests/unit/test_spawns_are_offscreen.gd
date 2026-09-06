extends "res://tests/test_case.gd"
## AUCUNE COQUE N'APPARAIT DANS LE CADRE.
##
## ⚠️ LE DEFAUT, RAPPORTE EN JOUANT LE 2026-09-06 : « les vagues d'ennemis apparaissent aussi
## dans le champ de vision ; ils devraient apparaitre en dehors et rentrer dedans ». Mesure du
## jour : les CENT QUINZE points de naissance du jeu etaient tous a l'interieur du cadre — 108
## a y = +9,5 pour un bord haut a +12,28, et sept passes de mitraillage a |x| = 16 pour un bord
## lateral a 20,37. Aucun ne naissait dehors.
##
## ⚠️ ET CE N'ETAIT PAS UNE NEGLIGENCE D'AUTEUR : NAITRE DEHORS ETAIT IMPOSSIBLE. Le couperet
## de `EnemyController` tombait a y = +11 (`BOUNDS.end.y + ESCAPE_MARGIN`), c'est-a-dire SOUS
## le bord haut de l'ecran. Une coque posee hors cadre mourait a sa premiere trame, sans une
## erreur ni une ligne de journal. Les deux se corrigent ensemble ou pas du tout — et ce test
## garde les deux moities.
##
## ⚠️ LE CADRE EST RELU DANS LA SCENE, JAMAIS RECOPIE. Un nombre grave dans un commentaire meurt
## au premier deplacement de camera, en silence, et rouvre exactement ce defaut.

const SCENES := ["res://scenes/gameplay/graybox.tscn", "res://scenes/gameplay/cortege.tscn"]
const WAVES_DIR := "res://resources/encounters/"

func _camera_of(scene: String) -> Array:
	var packed: PackedScene = load(scene)
	if packed == null:
		return []
	var etat := packed.get_state()
	for i in etat.get_node_count():
		if String(etat.get_node_name(i)) != "Camera3D":
			continue
		var camera := Transform3D.IDENTITY
		var fov := 0.0
		for j in etat.get_node_property_count(i):
			var nom := String(etat.get_node_property_name(i, j))
			if nom == "transform":
				camera = etat.get_node_property_value(i, j)
			elif nom == "fov":
				fov = etat.get_node_property_value(i, j)
		if fov > 0.0:
			return [camera, fov]
	return []

## Le cadre le PLUS LARGE de toutes les scenes de jeu : une naissance doit etre dehors partout,
## et une vague n'appartient pas a une scene en particulier.
func _widest_frame() -> Rect2:
	var union := Rect2()
	var trouve := false
	for scene in SCENES:
		var cam := _camera_of(scene)
		assert_eq(cam.size(), 2, "la camera de %s se lit" % scene.get_file())
		if cam.size() != 2:
			continue
		var f: Rect2 = GameplayPlane.visible_frame(cam[0], cam[1])
		union = f if not trouve else union.merge(f)
		trouve = true
	assert_true(trouve, "au moins une camera de jeu a ete trouvee")
	return union

func _waves() -> Array[String]:
	var out: Array[String] = []
	for nom in DirAccess.get_files_at(WAVES_DIR):
		if nom.begins_with("wave_") and nom.ends_with(".tres"):
			out.append(WAVES_DIR + nom)
	return out

func test_no_enemy_is_born_inside_the_frame() -> void:
	var cadre := _widest_frame()
	var vagues := _waves()
	assert_true(vagues.size() >= 4, "les vagues du jeu ont ete trouvees (%d)" % vagues.size())
	var comptees := 0
	for chemin in vagues:
		var wave: WaveData = load(chemin)
		if wave == null:
			continue
		for entry in wave.entries:
			comptees += 1
			var p: Vector2 = entry.spawn_plane_position
			assert_false(cadre.has_point(p),
				"%s : une coque nait en (%.1f, %.1f), DANS un cadre qui va de y=%.2f a y=%.2f et jusqu'a |x|=%.2f — elle apparaitrait sous les yeux du joueur au lieu d'y entrer"
					% [chemin.get_file(), p.x, p.y, cadre.position.y, cadre.end.y, cadre.end.x])
	assert_true(comptees > 100, "toutes les entrees ont ete examinees (%d)" % comptees)

## ⚠️ L'AUTRE MOITIE : une naissance hors cadre ne sert a rien si le couperet la fauche.
func test_the_despawn_box_lets_an_offscreen_birth_live() -> void:
	var cadre := _widest_frame()
	var haut := GameplayPlane.BOUNDS.end.y + EnemyController.ESCAPE_MARGIN
	var cote := GameplayPlane.BOUNDS.end.x + EnemyController.SIDE_MARGIN
	var bas := GameplayPlane.BOUNDS.position.y - EnemyController.DESPAWN_MARGIN
	assert_true(haut > cadre.end.y,
		"le couperet du haut est a y=%.2f pour un cadre qui monte a %.2f : une coque nee hors champ mourrait a sa premiere trame"
			% [haut, cadre.end.y])
	assert_true(cote > cadre.end.x,
		"le couperet lateral est a |x|=%.2f pour un cadre large de %.2f : une passe de mitraillage mourrait avant d'entrer"
			% [cote, cadre.end.x])
	# Le bas, lui, doit rester SERRE : c'est la sortie, pas l'entree. Une marge large y ferait
	# vivre des coques mortes pour le joueur, sous l'ecran, dans le pool.
	assert_true(bas <= cadre.position.y,
		"le couperet du bas est a y=%.2f alors que l'ecran s'arrete a %.2f : une coque survivrait hors champ pour rien"
			% [bas, cadre.position.y])
	for chemin in _waves():
		var wave: WaveData = load(chemin)
		if wave == null:
			continue
		for entry in wave.entries:
			var p: Vector2 = entry.spawn_plane_position
			assert_true(p.y < haut and absf(p.x) < cote,
				"%s : la coque nee en (%.1f, %.1f) est HORS de la boite de despawn — elle mourrait a l'image de sa creation, sans une erreur"
					% [chemin.get_file(), p.x, p.y])
