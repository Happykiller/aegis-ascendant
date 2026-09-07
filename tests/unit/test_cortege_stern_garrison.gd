extends "res://tests/test_case.gd"
## La garnison de poupe : ou une tourelle posee sur la coque est TOUCHABLE, et ou elle TIRE.
##
## ⚠️ CE BANC EST LA PORTE DE CE LOT, et il existe parce que le meme defaut a ete rapporte deux
## fois en jouant. Une piece posee sur la coque n'est pas touchable la ou elle se voit : la
## hitbox passe par `GameplayPlane.aim_point_of`, dont le facteur depend de la HAUTEUR de la
## piece. Une cote ecrite a vue donne une tourelle visible et intouchable, ou — pire, parce que
## rien ne le signale — une tourelle qui vise le joueur sans jamais tirer.

const LEVEL_SCENE := "res://scenes/gameplay/cortege.tscn"
const STERN: CortegeSternTuning = preload("res://resources/levels/long_cortege_stern.tres")
const CORRIDOR: CortegeTuning = preload("res://resources/levels/long_cortege_tuning.tres")
const Garrison := preload("res://scripts/gameplay/cortege_stern_garrison.gd")

# =============================================================================
# 0. Outillage — la camera est LUE, la poupe est PLACEE par le survol
# =============================================================================

## ⚠️ LUE DANS LA SCENE, JAMAIS RECOPIEE. Recopier « (0, 14, 5) » ferait passer tout ce fichier
## au vert le jour ou l'on recule la camera, pendant qu'en jeu la garnison sortirait du plan.
func _camera_eye() -> Vector3:
	var packed: PackedScene = load(LEVEL_SCENE)
	assert_true(packed != null, "la scene du niveau 2 se charge")
	var level := track(packed.instantiate()) as Node3D
	var cam := level.get_node_or_null("CameraDirector/Camera3D") as Node3D
	assert_true(cam != null, "la scene porte bien CameraDirector/Camera3D")
	if cam == null:
		return Vector3(0.0, 14.0, 5.0)
	var eye := _composed_origin(cam)
	# ⚠️ LE GARDE-FOU QUI VAUT TOUS LES AUTRES. `aim_point_of` a un cas degenere : une camera
	# POSEE DANS LE PLAN fait « marcher » le calcul et rend la position de la camera — toutes les
	# cibles au meme endroit, sans une erreur. Hors de l'arbre, `global_position` rend Y = 0.
	assert_true(absf(eye.y) > 1.0,
		"l'oeil est au-dessus du plan (%.2f) — sinon la projection est degeneree et ce fichier ment"
			% eye.y)
	return eye

func _composed_origin(node: Node3D) -> Vector3:
	var t := Transform3D.IDENTITY
	var current: Node = node
	while current is Node3D:
		t = (current as Node3D).transform * t
		current = current.get_parent()
	return t.origin

## Le z monde de la poupe une fois le survol immobilise.
##
## ⚠️ IL SE DEDUIT, IL NE SE SUPPOSE PAS. `CortegeFlyby` arrete le decor a
## `LEAD_IN + station - hold` et pose `_decor.position.z = _travelled - LEAD_IN` ; la poupe est
## a `-station` sous le decor. Le `LEAD_IN` s'annule, et il reste `-hold`.
func _stern_z() -> float:
	return -STERN.hold_plane_y

## La hauteur de masse d'une echelle, telle que `CortegeHardpoints` l'applique.
func _lift_of(echelle: CortegeTuning.TurretScale) -> float:
	var turret := CortegeTurret.make(CORRIDOR, 0, echelle)
	var lift := turret.hit_lift()
	turret.free()
	return lift

# =============================================================================
# 1. Ce que la table place
# =============================================================================

func test_the_table_places_all_three_calibres() -> void:
	var par_echelle := {}
	for post in Garrison.posts():
		var echelle := int(post.x)
		par_echelle[echelle] = int(par_echelle.get(echelle, 0)) + 1
	for echelle: int in [CortegeTuning.TurretScale.LIGHT, CortegeTuning.TurretScale.STANDARD,
			CortegeTuning.TurretScale.HEAVY]:
		assert_true(int(par_echelle.get(echelle, 0)) > 0,
			"l'echelle %d est representee dans la garnison" % echelle)

## ⚠️ UNE ENTREE HORS AXE VAUT DEUX PIECES. Le miroir est dans la lecture de la table et non
## dans la table : ecrire les deux bords a la main a coute une desymetrisation silencieuse sur
## les batteries du corridor, ou un signe oublie posait la grappe du mauvais cote de son hote.
func test_every_off_axis_post_is_mirrored() -> void:
	for post in Garrison.posts():
		if is_zero_approx(post.y):
			continue
		var jumeau := Vector4(post.x, -post.y, post.z, post.w)
		assert_true(Garrison.posts().has(jumeau),
			"le poste (%.2f ; %.2f ; %.2f) a son jumeau de babord" % [post.y, post.z, post.w])

# =============================================================================
# 2. ⚠️ LA PROJECTION — ce que ce fichier existe pour garder
# =============================================================================

## Toute piece doit etre TOUCHABLE : sa hitbox projetee tient dans le plan de vol.
##
## ⚠️ « ELLE EST VISIBLE, POURTANT JE NE LA TOUCHE PAS » (operateur, 2026-09-06). Le defaut
## avait ete corrige sur les fenetres de ciblage du corridor ; il se represente ici par un autre
## chemin — une cote de placement trop au large. Le rayon de la cible compte : c'est son BORD
## qu'une balle rencontre, pas son centre.
func test_every_post_is_reachable_by_the_player() -> void:
	var eye := _camera_eye()
	var z := _stern_z()
	for post in Garrison.posts():
		var echelle: CortegeTuning.TurretScale = int(post.x) as CortegeTuning.TurretScale
		var plan := Garrison.plane_post(post, _lift_of(echelle), z, eye)
		var rayon := CortegeTurret.target_radius_of(echelle)
		assert_true(absf(plan.x) - rayon <= GameplayPlane.BOUNDS.end.x,
			"le poste (%.2f ; %.2f ; %.2f) est atteignable : bord a |x| = %.2f pour un plan de vol de %.2f"
				% [post.y, post.z, post.w, absf(plan.x) - rayon, GameplayPlane.BOUNDS.end.x])

## Toute piece doit etre CIBLABLE : elle entre dans la fenetre ou le joueur peut l'inscrire.
func test_every_post_enters_the_target_window() -> void:
	var eye := _camera_eye()
	var z := _stern_z()
	var demi := CORRIDOR.target_span * 0.5
	for post in Garrison.posts():
		var echelle: CortegeTuning.TurretScale = int(post.x) as CortegeTuning.TurretScale
		var plan := Garrison.plane_post(post, _lift_of(echelle), z, eye)
		assert_true(absf(plan.y) <= demi,
			"le poste (%.2f ; %.2f ; %.2f) est ciblable : plan_y = %.2f pour une demi-fenetre de %.2f"
				% [post.y, post.z, post.w, plan.y, demi])

## ⚠️ ET ELLE DOIT TIRER. C'est le defaut SYMETRIQUE, et il ne se voit sur aucun journal : une
## legere posee sur le massif arriere tombe a `plan_y = 9,2` quand sa fenetre de tir en fait 7.
## Elle serait la, visible, tournee vers le joueur — et muette pour toujours. Aucune erreur,
## aucun test rouge, et en jouant on conclurait que la piece est « passive ».
func test_every_post_can_actually_fire() -> void:
	var eye := _camera_eye()
	var z := _stern_z()
	for post in Garrison.posts():
		var echelle: CortegeTuning.TurretScale = int(post.x) as CortegeTuning.TurretScale
		var plan := Garrison.plane_post(post, _lift_of(echelle), z, eye)
		var demi := Garrison.fire_half_of(CORRIDOR, echelle)
		assert_true(absf(plan.y) <= demi,
			"le poste (%.2f ; %.2f ; %.2f), echelle %d, TIRE : plan_y = %.2f pour une demi-fenetre de %.2f"
				% [post.y, post.z, post.w, echelle, plan.y, demi])

# =============================================================================
# 3. L'emprise des berceaux — les moteurs restent les protagonistes
# =============================================================================

## L'union des trois emprises, mesuree sur le binaire par la forge (`BRIEF-0106-report.md` §1).
const EMPRISE_HALF_X := 15.78
const EMPRISE_HALF_Z := 8.00

## ⚠️ RIEN AU-DESSUS DU PONT DANS L'EMPRISE. Une piece qui y monte masque un verrou, c'est-a-dire
## la seule cible de la phase. Les deux bandes de la dalle sont tolerees parce qu'elles sont AU
## NIVEAU du pont : elles se lisent sous les verrous, jamais devant.
func test_nothing_stands_above_the_deck_inside_the_cradle_footprint() -> void:
	for post in Garrison.posts():
		var dedans := absf(post.y) <= EMPRISE_HALF_X and absf(post.w) <= EMPRISE_HALF_Z
		if not dedans:
			continue
		assert_true(is_equal_approx(post.z, STERN.deck_y),
			"le poste (%.2f ; %.2f ; %.2f) est dans l'emprise : il est donc SUR le pont (%.2f attendu)"
				% [post.y, post.z, post.w, STERN.deck_y])

## ⚠️ CE QUI PEUT MASQUER UN VERROU N'EST PAS CE QUI EST « AU-DESSUS », c'est ce qui est PLUS
## PRES DE LA CAMERA. Elle regarde depuis `z = +5` : une piece a `z` plus grand que la rangee
## arriere des ancrages peut passer devant eux ; une piece derriere eux ne le peut pas, c'est
## l'ancrage qui l'occulte. Une premiere version de ce test refusait les deux — et la bande
## arriere du bassin, qui ne masque rien, echouait.
func test_no_forward_deck_piece_is_drawn_over_an_anchor() -> void:
	var eye := _camera_eye()
	var z := _stern_z()
	var k := STERN.scale_of(false)
	var basse := _anchor_plane_y(STERN.socket_z_rear)
	for post in Garrison.posts():
		var dedans := absf(post.y) <= EMPRISE_HALF_X and absf(post.w) <= EMPRISE_HALF_Z
		# `w` est le z LOCAL de la piece, `socket_z_rear * k` celui de la rangee la plus proche
		# de la camera. Au-dela, la piece est devant, et c'est la qu'il faut regarder.
		if not dedans or post.w <= STERN.socket_z_rear * k:
			continue
		var echelle: CortegeTuning.TurretScale = int(post.x) as CortegeTuning.TurretScale
		var plan := Garrison.plane_post(post, _lift_of(echelle), z, eye)
		assert_true(plan.y < basse - 0.8,
			"le poste avant (%.2f ; %.2f ; %.2f) se lit SOUS les verrous : plan_y = %.2f contre %.2f pour la rangee basse"
				% [post.y, post.z, post.w, plan.y, basse])

## ⚠️ ET SUR LA BANDE AVANT, TOUTE PIECE EST FORCEMENT DANS LA COLONNE DE TIR D'UN VERROU. C'est
## arithmetique, et ca vaut la peine de l'ecrire : les trois colonnes d'ancrages d'un bord
## occupent `plan_x` 2,03, 4,18 et 8,00, chacune large de 1,10 ; avec le rayon d'une legere il ne
## reste pas deux centimetres de passage entre 0,2 et 9,9. Et la dalle s'arrete a 15,95, soit
## `plan_x` 8,8. Il n'existe donc AUCUN emplacement de bande avant qui ne garde pas un verrou.
##
## Ce n'est pas un defaut : c'est la decision D2 de l'operateur, « les legeres gardent les
## berceaux, il faut nettoyer avant de pouvoir viser tranquillement ». Ce que ce test garde,
## c'est sa BORNE : seul le calibre le moins cher a le droit de barrer une colonne. Une moyenne
## (180 PV) ou une lourde (520 PV) y deviendrait un mur devant la seule cible de la phase.
func test_only_the_cheapest_calibre_may_stand_in_an_anchor_column() -> void:
	var eye := _camera_eye()
	var z := _stern_z()
	var k := STERN.scale_of(false)
	# ⚠️ LA COLONNE NE DEPEND PAS DU `z` DE LA RANGEE. `aim_point_of` projette `x` par un facteur
	# qui ne tient qu'a la HAUTEUR : les deux rangees d'un meme berceau partagent leurs colonnes.
	var colonnes: Array[float] = []
	for dx: float in [STERN.socket_x, -STERN.socket_x]:
		colonnes.append(_anchor_plane_x(STERN.slot_x(1.0) + dx * k, k))
	var kc := STERN.scale_of(true)
	for dx: float in [STERN.socket_x, -STERN.socket_x]:
		colonnes.append(_anchor_plane_x(dx * kc, kc))
	var barre := 0
	for post in Garrison.posts():
		if post.w <= STERN.socket_z_rear * k:
			continue
		var echelle: CortegeTuning.TurretScale = int(post.x) as CortegeTuning.TurretScale
		var plan := Garrison.plane_post(post, _lift_of(echelle), z, eye)
		var rayon := CortegeTurret.target_radius_of(echelle) + STERN.anchor_radius
		for colonne in colonnes:
			if absf(absf(plan.x) - colonne) > rayon:
				continue
			barre += 1
			assert_eq(echelle, CortegeTuning.TurretScale.LIGHT,
				"la piece qui barre la colonne %.2f est une LEGERE (55 PV), pas un mur : poste (%.2f ; %.2f ; %.2f)"
					% [colonne, post.y, post.z, post.w])
			break
	assert_true(barre > 0,
		"au moins une piece garde bien une colonne de verrou — sinon la decision D2 n'est pas rendue")

## Le `plan_y` d'une rangee d'ancrages, projete comme le jeu le projette.
func _anchor_plane_y(socket_z: float) -> float:
	var k := STERN.scale_of(false)
	var monde := Vector3(STERN.slot_x(1.0) + STERN.socket_x * k,
		STERN.deck_y + STERN.socket_y * k, _stern_z() + socket_z * k)
	return GameplayPlane.aim_point_of(monde, _camera_eye()).y

## Le `plan_x` d'une colonne d'ancrages, projete comme le jeu le projette.
func _anchor_plane_x(monde_x: float, k: float) -> float:
	var monde := Vector3(monde_x, STERN.deck_y + STERN.socket_y * k, _stern_z())
	return absf(GameplayPlane.aim_point_of(monde, _camera_eye()).x)

# =============================================================================
# 4. Ce que la spec §19 garde
# =============================================================================

## ⚠️ PAS DE RESPAWN, ET C'EST LE MORCEAU DE LA SPEC §19 QUE CE CHANTIER NE LEVE PAS. La table
## est une liste FIXE : rien dans la garnison ne repeuple. Ce test garde la propriete a
## l'endroit ou elle pourrait se perdre — une table qui deviendrait une regle de generation.
func test_the_garrison_is_a_fixed_list() -> void:
	var un := Garrison.posts()
	var deux := Garrison.posts()
	assert_eq(un.size(), deux.size(), "deux lectures de la table donnent le meme compte")
	for i in un.size():
		assert_true(un[i].is_equal_approx(deux[i]),
			"le poste %d est le meme d'une lecture a l'autre" % i)
