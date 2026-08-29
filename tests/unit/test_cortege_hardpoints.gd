extends "res://tests/test_case.gd"
## Les trois mecaniques de coque du niveau 2, pilotees SANS arbre de scene.
##
## ⚠️ CE QU'ELLES GARDENT, ET POURQUOI CHACUNE. Un survol ne revient jamais en arriere : tout
## ce que ces pieces font, elles le font une seule fois, dans une fenetre qui se referme. Trois
## defauts sont donc invisibles a l'oeil et fatals a la partie, et chacun a son test ici :
##
##   1. une tourelle qui TIRE SANS PREAVIS — le telegraphe est ce qui distingue une difficulte
##      d'une taxe (spec §11.2), et il ne se voit pas sur une capture ;
##   2. un pont qui NE TOMBE PAS dans sa fenetre — il serait indestructible en pratique, et le
##      joueur croirait mal jouer (le defaut qu'ADR-0024 a paye sur le flux du Leviathan) ;
##   3. un noeud qui n'eteint RIEN — la troisieme mecanique n'existerait alors pas du tout, et
##      rien a l'ecran ne le dirait, puisque sa recompense arrive quarante secondes plus tard.
##
## Les pieces recoivent leur position en parametre (`tick(delta, world)`) : c'est ce qui les
## rend pilotables ici, sans coque livree, sans BulletManager et sans joueur.

const TurretScript := preload("res://scripts/gameplay/cortege_turret.gd")
const BayScript := preload("res://scripts/gameplay/cortege_bay.gd")
const NodeScript := preload("res://scripts/gameplay/cortege_spine_node.gd")
const TUNING := preload("res://resources/levels/long_cortege_tuning.tres")

## Le monde d'un point de la coque a cette hauteur du plan de jeu. La coque est trois unites et
## demie sous le plan ; ce qui compte pour les fenetres est l'axe Z.
func _world_at(plane_y: float) -> Vector3:
	return Vector3(0.0, -3.5, -plane_y)

func _turret() -> CortegeTurret:
	var turret := track(TurretScript.make(TUNING, 0)) as CortegeTurret
	turret.setup(null, null, null)
	return turret

# --- 1. Le telegraphe ---------------------------------------------------------

func test_a_turret_always_telegraphs_before_it_burns() -> void:
	var turret := _turret()
	# Elle entre dans sa fenetre et on la fait vivre par petits pas, en relevant l'instant du
	# premier tir et celui du premier preavis.
	var first_windup := -1.0
	var first_firing := -1.0
	var t := 0.0
	for i in 400:
		turret.tick(0.02, _world_at(0.0))
		t += 0.02
		if first_windup < 0.0 and turret.fire_state() == TurretScript.Fire.WINDUP:
			first_windup = t
		if first_firing < 0.0 and turret.fire_state() == TurretScript.Fire.FIRING:
			first_firing = t
		if first_firing > 0.0:
			break
	assert_true(first_windup > 0.0, "la tourelle passe par un preavis")
	assert_true(first_firing > 0.0, "la tourelle finit par tirer")
	assert_true(first_firing > first_windup,
		"le preavis PRECEDE le tir — sinon ce n'est pas un telegraphe")
	assert_almost_eq(first_firing - first_windup, TUNING.turret_windup_time, 0.03,
		"le preavis dure ce que le reglage promet")

func test_a_turret_never_fires_outside_its_window() -> void:
	var turret := _turret()
	# Loin devant, tres au-dela de la fenetre : elle ne doit rien armer du tout.
	for i in 400:
		turret.tick(0.02, _world_at(TUNING.turret_visible_span))
	assert_eq(turret.fire_state(), TurretScript.Fire.READY,
		"une tourelle hors fenetre ne prepare rien — sinon son premier tir part des l'entree, sans preavis visible")

func test_a_turret_that_has_passed_is_gone_for_good() -> void:
	var turret := _turret()
	turret.tick(0.02, _world_at(0.0))
	assert_false(turret.has_passed(), "elle est vivante dans sa fenetre")
	turret.tick(0.02, _world_at(-TUNING.turret_visible_span))
	assert_true(turret.has_passed(), "passee, elle se retire")
	# ⚠️ Et elle ne revient pas : c'est la loi du survol. Une piece qui se reveillerait en
	# arriere du joueur tirerait hors du cadre, sans que rien ne le montre.
	turret.tick(0.02, _world_at(0.0))
	assert_true(turret.has_passed(), "elle ne se rallume pas quand la position repasse dans la fenetre")

func test_a_silenced_turret_stays_shootable() -> void:
	var turret := _turret()
	turret.silence()
	assert_true(turret.is_silenced(), "elle est eteinte")
	# ⚠️ VIVANTE, DONC ENCORE UNE CIBLE. Faire disparaitre les tourelles qu'un noeud eteint
	# couterait au joueur le score de ce qu'il vient de neutraliser : il apprendrait a ne plus
	# abattre les noeuds.
	assert_true(turret.is_alive(), "eteinte n'est pas detruite")
	for i in 400:
		turret.tick(0.02, _world_at(0.0))
	assert_eq(turret.fire_state(), TurretScript.Fire.READY, "elle ne tire plus jamais")

# --- 2. Le pont tombe dans sa fenetre -----------------------------------------

func test_a_bay_falls_within_the_window_a_reference_player_gets() -> void:
	# C'est l'invariant 2 du reglage, verifie ici sur la PIECE et non sur la Resource : le
	# reglage promet que les degats sont atteignables, ce test verifie que les encaisser tue.
	var bay := track(BayScript.make(TUNING, 0)) as CortegeBay
	var down := [false]
	bay.destroyed.connect(func(_b: CortegeBay) -> void: down[0] = true)
	bay.tick(0.02, _world_at(0.0))
	# On lui verse exactement ce que la fenetre permet, par salves de la taille d'un tir.
	var dealt := 0.0
	var reachable: float = TUNING.bay_reachable()
	while dealt < reachable and not down[0]:
		bay.target().hit_callback.call(20.0)
		dealt += 20.0
	assert_true(down[0],
		"le pont tombe dans les %.0f degats que sa fenetre permet — au-dessus il serait indestructible en pratique" % reachable)

func test_a_bay_only_releases_over_the_playfield() -> void:
	var bay := track(BayScript.make(TUNING, 0)) as CortegeBay
	var launched := [0]
	bay.released.connect(func(_e: EnemyController) -> void: launched[0] += 1)
	# Dans sa fenetre de TIR, mais au-dessus de la borne haute du plan de vol.
	var above := GameplayPlane.BOUNDS.end.y + 1.5
	for i in 600:
		bay.tick(0.02, _world_at(above))
	assert_eq(launched[0], 0,
		"un pont ne lache pas au-dessus du terrain — la coque naitrait hors des bornes et serait detruite a sa premiere trame")

func test_a_dead_bay_stops_producing() -> void:
	var bay := track(BayScript.make(TUNING, 0)) as CortegeBay
	bay.tick(0.02, _world_at(0.0))
	bay.target().hit_callback.call(TUNING.bay_health)
	assert_false(bay.is_alive(), "il est tombe")
	var launched := [0]
	bay.released.connect(func(_e: EnemyController) -> void: launched[0] += 1)
	for i in 600:
		bay.tick(0.02, _world_at(0.0))
	assert_eq(launched[0], 0, "abattu, il ne produit plus — c'est toute la valeur de la decision")

func test_a_bay_releases_enough_times_to_be_worth_killing() -> void:
	# ⚠️ La FENETRE DE TIR deborde le plan de vol : c'est le temps passe AU-DESSUS DU TERRAIN
	# qui dit la pression reelle, et c'est lui qu'il faut compter.
	var over_field := float(GameplayPlane.BOUNDS.size.y)
	var releases := BayScript.releases_over(over_field, TUNING.scroll_speed,
		TUNING.bay_release_interval)
	assert_true(releases >= 2,
		"un pont lache %d fois au-dessus du terrain — moins de deux ne pese pas sur la decision de l'abattre" % releases)

# --- 3. Le noeud eteint le troncon SUIVANT ------------------------------------

func test_a_node_silences_the_next_section_not_its_own() -> void:
	assert_eq(NodeScript.silenced_section(0, 5), 1,
		"le noeud du troncon 1 eteint le troncon 2")
	assert_eq(NodeScript.silenced_section(2, 5), 3, "et ainsi de suite")
	# ⚠️ Eteindre son propre troncon recompenserait apres coup un joueur qui a deja traverse le
	# danger : la mecanique n'aurait aucun effet sur sa partie.
	assert_true(NodeScript.silenced_section(1, 5) != 1, "jamais le sien")

func test_the_last_node_of_the_survey_relieves_nothing() -> void:
	# Ce n'est pas une erreur : le vaisseau continue, le niveau s'arrete. Le dernier noeud n'a
	# pas de troncon d'apres DANS CE NIVEAU.
	assert_eq(NodeScript.silenced_section(4, 5), -1,
		"le dernier noeud ne designe aucun troncon — le code appelant doit le lire, pas planter")

func test_a_node_only_becomes_a_target_inside_its_window() -> void:
	var node := track(NodeScript.make(TUNING, 0)) as CortegeSpineNode
	node.setup(null, null)
	node.tick(0.02, _world_at(TUNING.node_visible_span))
	assert_false(node.is_engaged(), "loin devant, il n'est pas encore une cible")
	node.tick(0.02, _world_at(0.0))
	assert_true(node.is_engaged(), "dans sa fenetre, il l'est")
	node.tick(0.02, _world_at(-TUNING.node_visible_span))
	assert_true(node.has_passed(), "derriere, il ne l'est plus jamais")

func test_a_node_falls_within_the_window_the_nose_guns_allow() -> void:
	var node := track(NodeScript.make(TUNING, 0)) as CortegeSpineNode
	node.setup(null, null)
	var down := [-1]
	node.destroyed.connect(func(n: CortegeSpineNode) -> void: down[0] = n.section)
	node.tick(0.02, _world_at(0.0))
	var dealt := 0.0
	var reachable: float = TUNING.node_reachable()
	while dealt < reachable and down[0] < 0:
		node.target().hit_callback.call(20.0)
		dealt += 20.0
	assert_eq(down[0], 0,
		"le noeud tombe dans les %.0f degats que les seuls canons de nez placent — se dimensionner contre la cadence d'une cible large reviendrait a se donner raison" % reachable)

# --- La chaine complete : un noeud abattu eteint le troncon suivant -----------
#
# ⚠️ AUCUNE PARTIE NE PROUVE CETTE CHAINE. Sa recompense arrive quarante secondes apres sa
# cause, sur un troncon que le joueur n'a pas encore vu ; et le pilote de demonstration, qui
# esquive et tire droit devant, n'abat pratiquement aucune cible de coque — une partie complete
# de 208 s en a detruit UNE. La seule verification possible est ici.

const HardpointsScript := preload("res://scripts/gameplay/cortege_hardpoints.gd")

## Deux troncons montes a la main, avec les noms de marqueurs du contrat de forge.
func _two_sections() -> Array[Node3D]:
	var sections: Array[Node3D] = []
	for i in 2:
		var section := track(Node3D.new()) as Node3D
		section.name = "Section_%02d" % (i + 1)
		var spine := Node3D.new()
		spine.name = "Spine_%02d" % (i + 1)
		section.add_child(spine)
		for t in 2:
			var turret := Node3D.new()
			turret.name = "Turret_%02d" % (i * 2 + t + 1)
			section.add_child(turret)
		sections.append(section)
	return sections

func test_killing_a_node_silences_the_next_sections_turrets() -> void:
	var manager := track(HardpointsScript.new()) as CortegeHardpoints
	manager.build(_two_sections(), TUNING, null, null, null)
	assert_eq(manager.turret_count(), 4, "quatre tourelles montees")
	assert_eq(manager.node_count(), 2, "deux noeuds montes")
	var announced := [-1, -1]
	manager.section_silenced.connect(func(section: int, count: int) -> void:
		announced[0] = section
		announced[1] = count)
	# Le noeud du PREMIER troncon tombe.
	var node := manager.nodes()[0]
	node.tick(0.02, Vector3.ZERO)
	node.target().hit_callback.call(TUNING.node_health)
	assert_false(node.is_alive(), "le noeud est tombe")
	assert_eq(manager.turrets_alive_in(1), 0,
		"les deux tourelles du troncon SUIVANT sont eteintes")
	assert_eq(manager.turrets_alive_in(0), 2,
		"celles de son propre troncon ne le sont pas — la recompense serait arrivee apres le danger")
	# ⚠️ ET ELLE EST ANNONCEE. Rien a l'ecran ne relie une cause a un effet separes de quarante
	# secondes : sans le signal, la troisieme mecanique n'existe pas pour le joueur.
	assert_eq(announced[0], 1, "le troncon eteint est annonce")
	assert_eq(announced[1], 2, "avec le nombre de tourelles qu'il vient de perdre")

func test_the_last_node_silences_nothing_and_says_nothing() -> void:
	var manager := track(HardpointsScript.new()) as CortegeHardpoints
	manager.build(_two_sections(), TUNING, null, null, null)
	var heard := [0]
	manager.section_silenced.connect(func(_s: int, _c: int) -> void: heard[0] += 1)
	# ⚠️ Le reglage livre declare CINQ troncons ; le banc n'en monte que deux. Le dernier noeud
	# du BANC (rang 1) designe donc le troncon 2, qui n'existe pas ici — et le gestionnaire ne
	# doit ni planter ni annoncer une extinction vide.
	var node := manager.nodes()[1]
	node.tick(0.02, Vector3.ZERO)
	node.target().hit_callback.call(TUNING.node_health)
	assert_false(node.is_alive(), "le second noeud est tombe")
	assert_eq(heard[0], 0, "aucune extinction annoncee — il n'y a rien a eteindre")

# --- L'habillage de la coque : facultatif, jamais fatal ------------------------

const SkinScript := preload("res://scripts/fx/cortege_skin.gd")

func test_the_skin_is_harmless_when_the_operator_has_not_supplied_the_maps() -> void:
	# ⚠️ C'EST L'ETAT NORMAL DU DEPOT, PAS UN CAS D'ERREUR. Les cartes viennent de l'operateur
	# (ADR-0028, demandes TEX-0010 a TEX-0014) et le niveau doit se jouer sans elles. Le piege
	# evite ici est un `preload` sur un fichier absent : en GDScript c'est une erreur de
	# COMPILATION, donc le niveau entier cesserait de se monter — pour un habillage facultatif.
	var mesh := track(MeshInstance3D.new()) as MeshInstance3D
	mesh.mesh = BoxMesh.new()
	var material := StandardMaterial3D.new()
	material.resource_name = "AA_Hull"
	mesh.set_surface_override_material(0, material)
	var dressed := SkinScript.apply(mesh)
	assert_eq(dressed, 0, "sans carte, rien n'est habille — et rien ne casse")
	assert_eq(mesh.get_active_material(0), material,
		"le materiau importe est laisse INTACT : on ne remplace pas par une copie vide")

func test_the_skin_leaves_materials_it_does_not_know_alone() -> void:
	var mesh := track(MeshInstance3D.new()) as MeshInstance3D
	mesh.mesh = BoxMesh.new()
	var material := StandardMaterial3D.new()
	material.resource_name = "AA_Marking_Red"
	mesh.set_surface_override_material(0, material)
	assert_eq(SkinScript.apply(mesh), 0,
		"un materiau hors contrat n'est pas touche — le contrat de nommage vient de la forge")
