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
	# ⚠️ ET UNE PIECE N'EST UN MUR QUE SI LE JOUEUR NE PEUT PAS PASSER DEVANT ELLE. Les balles
	# montent : une tourelle plus BASSE que le chasseur n'intercepte rien, il lui suffit
	# d'avancer. Le plan de vol descend a -8 ; une piece a `plan_y = -5,8` se contourne en
	# montant de deux unites, et c'est un piquet avant, pas un barrage. La regle ne vaut donc
	# que pour ce qui siege dans la moitie haute de l'arene, la ou l'on tire vers les verrous.
	var plancher := GameplayPlane.BOUNDS.position.y + 3.0
	var barre := 0
	for post in Garrison.posts():
		if post.w <= STERN.socket_z_rear * k:
			continue
		var echelle: CortegeTuning.TurretScale = int(post.x) as CortegeTuning.TurretScale
		var plan := Garrison.plane_post(post, _lift_of(echelle), z, eye)
		if plan.y < plancher:
			continue
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

# =============================================================================
# 5. L'escalade — ce que le vaisseau fait de ce qu'on lui prend
# =============================================================================

## ⚠️ DEUX TABLEAUX PARALLELES SE DESYNCHRONISENT. `posts()` et `tiers()` sont produits par la
## meme boucle et doivent avoir la meme taille : une entree qui gagnerait un miroir dans l'une
## sans l'autre poserait le palier d'une piece sur sa voisine, en silence.
func test_the_tier_table_matches_the_post_table() -> void:
	assert_eq(Garrison.tiers().size(), Garrison.posts().size(),
		"un palier par poste developpe")

## Le palier 0 est une GARNISON, pas un echantillon : la poupe doit se defendre des l'arrivee.
func test_the_ship_already_fights_on_arrival() -> void:
	var eveilles := 0
	for palier in Garrison.tiers():
		if palier == 0:
			eveilles += 1
	assert_true(eveilles >= 4,
		"%d pieces tirent des l'arrivee — la poupe n'attend pas d'etre entamee" % eveilles)

## ⚠️ ET CHAQUE PALIER DOIT APPORTER QUELQUE CHOSE. Un palier vide serait une escalade
## silencieuse : la cadence monterait sans qu'aucune piece ne s'allume, et le joueur ne saurait
## pas que le vaisseau vient de reagir.
func test_every_tier_wakes_something() -> void:
	var paliers := Garrison.tiers()
	for tier in range(1, 4):
		var compte := 0
		for palier in paliers:
			if palier == tier:
				compte += 1
		assert_true(compte > 0, "le palier %d reveille au moins une piece" % tier)

## ⚠️ LES LOURDES SONT LE DERNIER MOT. 520 PV et une fenetre de tir de 26 : les eveiller tot
## ferait de l'arrivee le pic de la phase, et le central — le moment ou tout converge — serait
## joue en descente.
func test_the_heaviest_pieces_are_the_last_word() -> void:
	var paliers := Garrison.tiers()
	var postes := Garrison.posts()
	for i in postes.size():
		if int(postes[i].x) != CortegeTuning.TurretScale.HEAVY:
			continue
		assert_eq(paliers[i], 3,
			"la lourde (%.2f ; %.2f ; %.2f) attend l'exposition du central" 
				% [postes[i].y, postes[i].z, postes[i].w])

## L'echelle de pression, telle que la Resource la livre.
func test_the_pressure_ladder_only_climbs() -> void:
	assert_eq(STERN.tier_pressure.size(), 4, "quatre paliers")
	assert_true(is_equal_approx(STERN.pressure_of(0), 1.0),
		"le palier 0 est la reference (%.2f)" % STERN.pressure_of(0))
	for tier in range(1, 4):
		assert_true(STERN.pressure_of(tier) > STERN.pressure_of(tier - 1),
			"le palier %d (%.2f) est plus dur que le %d (%.2f)"
				% [tier, STERN.pressure_of(tier), tier - 1, STERN.pressure_of(tier - 1)])
	# ⚠️ ET UN PALIER HORS TABLE NE PLANTE PAS : `force_tier` vient d'un drapeau de banc.
	assert_true(is_equal_approx(STERN.pressure_of(99), STERN.pressure_of(3)),
		"un palier hors table se rabat sur le dernier")

## ⚠️ LA PRESSION DIVISE L'INTERVALLE, ELLE NE REMPLACE PAS L'AFFAIBLISSEMENT. Une tourelle
## eteinte par son noeud d'epine doit rester molle au dernier palier de la poupe — sinon abattre
## un noeud cesserait de vouloir dire quelque chose la ou ca compte le plus.
func test_pressure_and_weakening_compose() -> void:
	var turret := CortegeTurret.make(CORRIDOR, 0, CortegeTuning.TurretScale.STANDARD)
	var repos := turret.fire_slack()
	turret.pressure = STERN.pressure_of(3)
	var sous_pression := turret.fire_slack()
	assert_true(sous_pression < repos,
		"sous pression elle tire plus vite : %.3f contre %.3f" % [sous_pression, repos])
	turret.weaken()
	assert_true(turret.fire_slack() > sous_pression,
		"et un noeud abattu la ralentit MEME au dernier palier : %.3f contre %.3f"
			% [turret.fire_slack(), sous_pression])
	turret.free()

## ⚠️ UNE PIECE ENDORMIE NE VISE PAS. Ce n'est pas « pression zero » : un canon qui suit le
## joueur annonce un tir. S'il ne vient jamais, le joueur apprend a ignorer le geste qui,
## partout ailleurs dans ce niveau, precede un tir — et le telegraphe meurt pour tout le jeu.
func test_a_sleeping_piece_is_a_target_but_not_a_threat() -> void:
	var turret := CortegeTurret.make(CORRIDOR, 0, CortegeTuning.TurretScale.HEAVY)
	turret.sleep_now()
	assert_true(turret.asleep, "elle dort")
	assert_true(turret.is_alive(), "et elle reste une cible : le joueur peut la nettoyer avant")
	turret.wake()
	assert_true(not turret.asleep, "le reveil la rend au jeu")
	turret.free()

# =============================================================================
# 6. ⚠️ LE CHEVAUCHEMENT — « on a beaucoup de chevauchement » (operateur)
# =============================================================================

## ⚠️ DEUX PIECES QUI NE SE TOUCHENT PAS SUR LA COQUE PEUVENT SE TOUCHER A L'ECRAN. C'est le
## defaut rapporte le 2026-09-07, capture a l'appui : six legeres alignees sur la levre avant du
## bassin, distantes de 3,4 m — donc parfaitement disjointes en 3D — et jointives une fois
## projetees, parce que la projection RAPPROCHE (facteur 0,55 sur le pont). Chaque cote passait
## ses invariants ; c'est leur ENSEMBLE qui ne passait pas, et rien ne le testait.
##
## Le rayon projete d'une piece vaut son rayon d'assise fois SON facteur de projection : deux
## pieces a des hauteurs differentes ne se compriment pas pareil, et prendre un facteur commun
## laisserait passer exactement les paires qui posent probleme.
func test_no_two_pieces_overlap_on_screen() -> void:
	var eye := _camera_eye()
	var z := _stern_z()
	var postes := Garrison.posts()
	for i in postes.size():
		for j in range(i + 1, postes.size()):
			var a := postes[i]
			var b := postes[j]
			var ea: CortegeTuning.TurretScale = int(a.x) as CortegeTuning.TurretScale
			var eb: CortegeTuning.TurretScale = int(b.x) as CortegeTuning.TurretScale
			var pa := Garrison.plane_post(a, _lift_of(ea), z, eye)
			var pb := Garrison.plane_post(b, _lift_of(eb), z, eye)
			var ra := Garrison.footprint_of(ea) * _shrink(a.z + _lift_of(ea), eye)
			var rb := Garrison.footprint_of(eb) * _shrink(b.z + _lift_of(eb), eye)
			assert_true(pa.distance_to(pb) >= ra + rb,
				"(%.2f ; %.2f ; %.2f) et (%.2f ; %.2f ; %.2f) ne se chevauchent pas a l'ecran : %.2f d'ecart pour %.2f de rayons cumules"
					% [a.y, a.z, a.w, b.y, b.z, b.w, pa.distance_to(pb), ra + rb])

## ⚠️ ET ELLES NE S'INTERPENETRENT PAS NON PLUS DANS LE MONDE. Le test d'ecran ne suffit pas : deux
## pieces exactement l'une au-dessus de l'autre auraient la meme projection et passeraient au
## vert en etant encastrees.
func test_no_two_pieces_share_the_same_metal() -> void:
	var postes := Garrison.posts()
	for i in postes.size():
		for j in range(i + 1, postes.size()):
			var a := postes[i]
			var b := postes[j]
			var ea: CortegeTuning.TurretScale = int(a.x) as CortegeTuning.TurretScale
			var eb: CortegeTuning.TurretScale = int(b.x) as CortegeTuning.TurretScale
			var ecart := Vector3(a.y, a.z, a.w).distance_to(Vector3(b.y, b.z, b.w))
			var rayons := Garrison.footprint_of(ea) + Garrison.footprint_of(eb)
			assert_true(ecart >= rayons,
				"(%.2f ; %.2f ; %.2f) et (%.2f ; %.2f ; %.2f) ne s'encastrent pas : %.2f m pour %.2f d'assises"
					% [a.y, a.z, a.w, b.y, b.z, b.w, ecart, rayons])

## Le facteur de compression de la projection a la hauteur `y`. Meme formule que `aim_point_of`.
func _shrink(y: float, eye: Vector3) -> float:
	return absf(-eye.y / (y - eye.y))

# =============================================================================
# 7. Les plates-formes volantes
# =============================================================================

## ⚠️ FLOTTER NE DISPENSE DE RIEN. Une plate-forme au-dessus du bassin masquerait un verrou
## exactement comme un pylone : le test d'emprise vaut pour elles aussi, et il est ici pour que
## ce soit dit a l'endroit ou l'on serait tente de croire le contraire.
func test_a_flying_platform_still_respects_the_cradle_footprint() -> void:
	var postes := Garrison.posts()
	var volantes := Garrison.flying()
	assert_eq(volantes.size(), postes.size(), "un drapeau de vol par poste")
	var comptees := 0
	for i in postes.size():
		if not volantes[i]:
			continue
		comptees += 1
		var post := postes[i]
		var dedans := absf(post.y) <= EMPRISE_HALF_X and absf(post.w) <= EMPRISE_HALF_Z
		assert_false(dedans,
			"la plate-forme (%.2f ; %.2f ; %.2f) est hors de l'emprise des berceaux"
				% [post.y, post.z, post.w])
	assert_true(comptees > 0, "la garnison a bien des pieces volantes")

## ⚠️ ET ELLE FLOTTE AU-DESSUS DU PONT, PAS DEDANS. Une dalle posee sous le niveau de la coque
## se lirait comme un morceau de coque mal place — c'est-a-dire le defaut qu'elle corrige.
func test_a_flying_platform_hovers_clear_of_the_deck() -> void:
	var postes := Garrison.posts()
	var volantes := Garrison.flying()
	for i in postes.size():
		if not volantes[i]:
			continue
		assert_true(postes[i].z > STERN.deck_y + 2.0,
			"la plate-forme (%.2f ; %.2f ; %.2f) est franchement au-dessus du pont (%.2f)"
				% [postes[i].y, postes[i].z, postes[i].w, STERN.deck_y])
