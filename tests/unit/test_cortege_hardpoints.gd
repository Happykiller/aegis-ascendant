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

# --- 1. La tourelle se distance ----------------------------------------------

func test_a_turret_can_always_be_outrun() -> void:
	# ⚠️ CE TEST REMPLACE CELUI DU TELEGRAPHE, ET IL GARDE LA MEME LOI. La spec §11.2 dit qu'un
	# tir sans preavis est une taxe et non une difficulte. Le premier modele la tenait par un
	# preavis de 0,8 s ; il ne marchait pas — « je ne vois pas les tourelles qui me tirent
	# dessus » (operateur, en jouant). Le faisceau est desormais PERMANENT, donc visible tout le
	# temps, et ce qui le rend jouable est qu'on peut le SEMER.
	#
	# Le seuil se calcule : un joueur a 14 u/s qui contourne une tourelle a 8 unites tourne
	# autour d'elle a 100 deg/s. La tourelle doit rester nettement en dessous.
	var escapable := rad_to_deg(14.0 / 8.0)
	assert_true(TUNING.turret_turn_rate_deg < escapable * 0.6,
		"une tourelle pivote a %.0f deg/s pour %.0f deg/s de contournement — au-dela elle colle au joueur"
			% [TUNING.turret_turn_rate_deg, escapable])

func test_a_turret_turns_at_a_constant_rate_never_faster() -> void:
	# ⚠️ SUR LA FONCTION PURE, PAS SUR LA PIECE MONTEE. La rotation demande un joueur a viser,
	# et un `PlayerFighterController` ne se fabrique pas au banc. Ce qui doit etre garde au
	# chiffre pres, ce sont ces trois nombres : une tourelle qui pivote trop vite colle au
	# joueur quoi qu'il fasse, et ca ne se voit sur AUCUNE capture.
	const RATE := 42.0
	var angle := 0.0
	for i in 10:
		angle = TurretScript.turn_step(angle, PI, RATE, 0.1)
	var permis := deg_to_rad(RATE) * 1.0 + 0.0001
	assert_true(absf(angle) <= permis,
		"en 1 s elle a tourne de %.1f deg pour %.1f permis" % [rad_to_deg(angle), RATE])
	assert_true(absf(angle) > 0.0, "elle pivote bel et bien vers sa cible")
	# ⚠️ ET ELLE S'ARRETE EN ARRIVANT : `rotate_toward` ne depasse pas. Une interpolation le
	# ferait osciller autour du joueur, ce qui se lirait comme un tremblement.
	var pose := TurretScript.turn_step(PI - 0.01, PI, RATE, 10.0)
	assert_almost_eq(pose, PI, 0.0001, "arrivee sur la cible, elle ne la depasse pas")


func test_a_turret_never_burns_outside_its_window() -> void:
	var turret := _turret()
	for i in 400:
		turret.tick(0.02, _world_at(TUNING.turret_visible_span), GameplayPlane.to_plane(_world_at(TUNING.turret_visible_span)))
	assert_false(turret.is_engaged(),
		"loin devant, elle n'est pas armee — son faisceau ne peut donc mordre personne")

func test_a_turret_that_has_passed_is_gone_for_good() -> void:
	var turret := _turret()
	turret.tick(0.02, _world_at(0.0), GameplayPlane.to_plane(_world_at(0.0)))
	assert_false(turret.has_passed(), "elle est vivante dans sa fenetre")
	turret.tick(0.02, _world_at(-TUNING.turret_visible_span), GameplayPlane.to_plane(_world_at(-TUNING.turret_visible_span)))
	assert_true(turret.has_passed(), "passee, elle se retire")
	# ⚠️ Et elle ne revient pas : c'est la loi du survol. Une piece qui se reveillerait en
	# arriere du joueur tirerait hors du cadre, sans que rien ne le montre.
	turret.tick(0.02, _world_at(0.0), GameplayPlane.to_plane(_world_at(0.0)))
	assert_true(turret.has_passed(), "elle ne se rallume pas quand la position repasse dans la fenetre")

func test_a_silenced_turret_stays_shootable() -> void:
	var turret := _turret()
	turret.silence()
	assert_true(turret.is_silenced(), "elle est eteinte")
	# ⚠️ VIVANTE, DONC ENCORE UNE CIBLE. Faire disparaitre les tourelles qu'un nœud eteint
	# couterait au joueur le score de ce qu'il vient de neutraliser : il apprendrait a ne plus
	# abattre les nœuds.
	assert_true(turret.is_alive(), "eteinte n'est pas detruite")
	var avant := turret.aim()
	for i in 400:
		turret.tick(0.02, _world_at(0.0), GameplayPlane.to_plane(_world_at(0.0)))
	assert_eq(turret.aim(), avant, "elle ne pivote meme plus : sa tete est morte")

# --- 2. Le pont tombe dans sa fenetre -----------------------------------------

func test_a_bay_falls_within_the_window_a_reference_player_gets() -> void:
	# C'est l'invariant 2 du reglage, verifie ici sur la PIECE et non sur la Resource : le
	# reglage promet que les degats sont atteignables, ce test verifie que les encaisser tue.
	var bay := track(BayScript.make(TUNING, 0)) as CortegeBay
	var down := [false]
	bay.destroyed.connect(func(_b: CortegeBay) -> void: down[0] = true)
	bay.tick(0.02, _world_at(0.0), GameplayPlane.to_plane(_world_at(0.0)))
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
		bay.tick(0.02, _world_at(above), GameplayPlane.to_plane(_world_at(above)))
	assert_eq(launched[0], 0,
		"un pont ne lache pas au-dessus du terrain — la coque naitrait hors des bornes et serait detruite a sa premiere trame")

func test_a_dead_bay_stops_producing() -> void:
	var bay := track(BayScript.make(TUNING, 0)) as CortegeBay
	bay.tick(0.02, _world_at(0.0), GameplayPlane.to_plane(_world_at(0.0)))
	bay.target().hit_callback.call(TUNING.bay_health)
	assert_false(bay.is_alive(), "il est tombe")
	var launched := [0]
	bay.released.connect(func(_e: EnemyController) -> void: launched[0] += 1)
	for i in 600:
		bay.tick(0.02, _world_at(0.0), GameplayPlane.to_plane(_world_at(0.0)))
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
	node.tick(0.02, _world_at(TUNING.node_visible_span), GameplayPlane.to_plane(_world_at(TUNING.node_visible_span)))
	assert_false(node.is_engaged(), "loin devant, il n'est pas encore une cible")
	node.tick(0.02, _world_at(0.0), GameplayPlane.to_plane(_world_at(0.0)))
	assert_true(node.is_engaged(), "dans sa fenetre, il l'est")
	node.tick(0.02, _world_at(-TUNING.node_visible_span), GameplayPlane.to_plane(_world_at(-TUNING.node_visible_span)))
	assert_true(node.has_passed(), "derriere, il ne l'est plus jamais")

func test_a_node_falls_within_the_window_the_nose_guns_allow() -> void:
	var node := track(NodeScript.make(TUNING, 0)) as CortegeSpineNode
	node.setup(null, null)
	var down := [-1]
	node.destroyed.connect(func(n: CortegeSpineNode) -> void: down[0] = n.section)
	node.tick(0.02, _world_at(0.0), GameplayPlane.to_plane(_world_at(0.0)))
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
	node.tick(0.02, Vector3.ZERO, GameplayPlane.to_plane(Vector3.ZERO))
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
	node.tick(0.02, Vector3.ZERO, GameplayPlane.to_plane(Vector3.ZERO))
	node.target().hit_callback.call(TUNING.node_health)
	assert_false(node.is_alive(), "le second noeud est tombe")
	assert_eq(heard[0], 0, "aucune extinction annoncee — il n'y a rien a eteindre")

# --- L'habillage de la coque : facultatif, jamais fatal ------------------------

const SkinScript := preload("res://scripts/fx/cortege_skin.gd")

## ⚠️ CE TEST EN REMPLACE UN AUTRE, ET LE PREMIER A FAIT SON TRAVAIL EN TOMBANT. Il verifiait
## que sans cartes rien ne casse — l'etat du depot tant que l'operateur n'avait pas livre ses
## images (ADR-0028). Elles sont arrivees le 2026-08-29 : la propriete gardee change, et c'est
## normal. Ce qui peut mal tourner desormais n'est plus l'absence, c'est le NOM.
func test_the_skin_dresses_the_hull_now_that_the_maps_are_there() -> void:
	var mesh := track(MeshInstance3D.new()) as MeshInstance3D
	mesh.mesh = BoxMesh.new()
	var material := StandardMaterial3D.new()
	material.resource_name = "AA_Hull"
	mesh.set_surface_override_material(0, material)
	assert_eq(SkinScript.apply(mesh), 1, "le borde est habille")
	var tuned := mesh.get_active_material(0) as StandardMaterial3D
	assert_true(tuned != material,
		"le materiau importe n'est PAS mute en place : il appartient au .glb et rien ne le remettrait en etat")
	# ⚠️ TOUT OU RIEN. Poser la multiplication sans la normale donnerait des rainures PEINTES
	# que la lumiere ne voit pas — la coque resterait un aplat, et l'on conclurait que la
	# texture ne sert a rien. C'est la leçon d'ADR-0013, ecrite en tete de `hull_detail.gd`.
	assert_true(tuned.albedo_texture != null, "l'albedo porte la carte de multiplication")
	assert_true(tuned.normal_enabled and tuned.normal_texture != null,
		"et le RELIEF est la : sans lui la carte ne fait que peindre des rainures plates")

## ⚠️ LA GARDE QUI COMPTE MAINTENANT : chaque entree de `SKINS` trouve ses fichiers. Un nom
## change d'un cote sans l'autre ne casse rien — la piece est simplement sautee, et la coque
## sort NUE a cet endroit-la, sans une ligne au journal pour le dire.
func test_every_declared_skin_finds_its_maps_on_disk() -> void:
	for materiau in SkinScript.SKINS:
		var stem: String = SkinScript.SKINS[materiau]
		for suffixe in ["nrm", "mul", "rough", "ao"]:
			var chemin := "%s%s_%s.png" % [SkinScript.MAPS_DIR, stem, suffixe]
			assert_true(ResourceLoader.exists(chemin),
				"`%s` declare la carte %s, absente du depot" % [materiau, chemin])
	var emissif := "%s%s.png" % [SkinScript.MAPS_DIR, SkinScript.EMISSIVE_MAP]
	assert_true(ResourceLoader.exists(emissif), "l'emissif de l'artere est la : %s" % emissif)

func test_the_skin_leaves_materials_it_does_not_know_alone() -> void:
	var mesh := track(MeshInstance3D.new()) as MeshInstance3D
	mesh.mesh = BoxMesh.new()
	var material := StandardMaterial3D.new()
	material.resource_name = "AA_Marking_Red"
	mesh.set_surface_override_material(0, material)
	assert_eq(SkinScript.apply(mesh), 0,
		"un materiau hors contrat n'est pas touche — le contrat de nommage vient de la forge")

# --- L'ouverture du survol n'est pas un temps mort ----------------------------

const FlybyScript := preload("res://scripts/vfx/cortege_flyby.gd")
const APPROACH := preload("res://resources/encounters/wave_cortege_approach.tres")

## Le premier instant ou une piece de coque devient tirable, en secondes de jeu.
##
## ⚠️ CALCULE SUR LA COQUE LIVREE, pas sur une constante recopiee. C'est la geometrie qui
## decide, et elle peut changer a la prochaine forge : un test qui reciterait 30 s ne
## verifierait que lui-meme.
func _first_hardpoint_second() -> float:
	var packed: PackedScene = load(FlybyScript.DECOR_PATH)
	assert_true(packed != null, "la coque livree se charge")
	var hull := track(packed.instantiate()) as Node3D
	var spans := {
		"Turret_": TUNING.turret_visible_span,
		"Bay_": TUNING.bay_visible_span,
		"Spine_": TUNING.node_visible_span,
	}
	var earliest := INF
	for section in hull.get_children():
		var s := section as Node3D
		if s == null or not s.name.begins_with("Section_"):
			continue
		for child in s.get_children():
			var marker := child as Node3D
			if marker == null:
				continue
			for prefix in spans:
				if not marker.name.begins_with(prefix):
					continue
				var z: float = s.position.z + marker.position.z
				# La piece entre dans sa fenetre quand son plane_y descend a span/2.
				var travelled: float = -z + FlybyScript.LEAD_IN - float(spans[prefix]) * 0.5
				earliest = minf(earliest, maxf(travelled, 0.0) / TUNING.scroll_speed)
	return earliest

func test_the_survey_does_not_open_on_dead_air() -> void:
	var first := _first_hardpoint_second()
	assert_true(first < 1000.0, "une premiere piece a bien ete trouvee")
	# ⚠️ CE CHIFFRE EST MESURE, PAS SUPPOSE. La proue de la coque livree est NUE sur 65 unites :
	# rien n'y est tirable avant 30 s de jeu. Aucune vitesse ne referme ce trou — cherche entre
	# 2,4 et 2,9 u/s et entre 8 et 22 unites d'entree en scene, l'ouverture ne descend jamais
	# sous 17,6 s. C'est un probleme de CONTENU, et la reception de proue est sa reponse.
	var dernier_spawn := 0.0
	for entry in APPROACH.entries:
		dernier_spawn = maxf(dernier_spawn,
			entry.time_offset + float(maxi(entry.count - 1, 0)) * entry.spacing)
	assert_true(dernier_spawn > 0.0, "la reception de proue porte des apparitions")
	# ⚠️ LA RECEPTION DOIT PASSER LE RELAIS A LA COQUE, PAS S'Y AJOUTER. Si elle se terminait
	# bien avant la premiere piece, le trou reviendrait ; si elle debordait dessus, le niveau
	# ouvrirait sur son pic de densite au lieu d'y monter. On lui accorde la duree de vie d'une
	# coque lachee — le temps qu'elle traverse le plan de jeu.
	const TRAVERSEE := 8.0
	assert_true(dernier_spawn + TRAVERSEE >= first,
		"la reception (dernier depart %.1f s) tient jusqu'a la premiere piece de coque (%.1f s)"
			% [dernier_spawn, first])
	assert_true(dernier_spawn <= first,
		"et elle ne deborde pas dessus : le niveau monte en densite, il n'ouvre pas dessus")

func test_the_survey_starts_shooting_within_seconds() -> void:
	# La toute premiere chose a faire. Un survol qui commence par regarder n'engage personne.
	var premier := INF
	for entry in APPROACH.entries:
		premier = minf(premier, entry.time_offset)
	assert_true(premier <= 5.0,
		"la premiere cible du niveau apparait a %.1f s — au-dela, le joueur regarde defiler" % premier)

# --- L'instrument de debug ----------------------------------------------------

const ZonesScript := preload("res://scripts/debug/survey_zones.gd")

func test_the_debug_bands_never_loop_forever() -> void:
	# ⚠️ CE TEST GARDE UN FIGEAGE, PAS UN DESSIN. Les bandes sont tracees en tirets par une
	# boucle `while` qui avance de `DASH + GAP` : une valeur nulle ou negative la ferait tourner
	# sans fin. L'instrument est ALLUME PAR DEFAUT en build de developpement (`settings_data.gd`
	# pose `OS.is_debug_build()`), donc le jeu se figerait au montage du niveau — et ca se lirait
	# comme un plantage du niveau, pas comme un defaut de l'outil de debug.
	assert_true(ZonesScript.DASH > 0.0 and ZonesScript.GAP > 0.0,
		"un tiret et son vide sont strictement positifs")
	var largeur := GameplayPlane.BOUNDS.size.x
	var tirets := ZonesScript.dash_count(largeur)
	assert_true(tirets > 0, "une bande en travers du plan porte des tirets (%d)" % tirets)
	assert_true(tirets < 200,
		"et pas des milliers : %d tirets par bande, sept bandes, a chaque image" % tirets)
	assert_eq(ZonesScript.dash_count(0.0), 0, "une bande de longueur nulle n'en porte aucun")

# --- L'ordre des troncons -----------------------------------------------------

## ⚠️ CE TEST EXISTE PARCE QUE LE TRI MENTAIT, ET QUE RIEN NE LE MONTRAIT. `Node.name` est un
## `StringName`, et `<` sur un `StringName` compare des POINTEURS internes, pas des lettres :
## `sections.sort_custom(a.name < b.name)` rendait `[05, 04, 03, 01, 02]`, et cet ordre change
## d'un lancement a l'autre. Le defilement n'en depend pas, le numero affiche non plus — seul
## le numero porte par CHAQUE PIECE etait faux. Un nœud du troncon 1 eteignait donc les
## tourelles du 5, et le journal annoncait « nœud d'epine 04 abattu » pendant qu'on survolait le
## premier. Trouve en JOUANT, par l'operateur.
func test_the_sections_come_back_from_prow_to_stern() -> void:
	var packed: PackedScene = load(FlybyScript.DECOR_PATH)
	var hull := track(packed.instantiate()) as Node3D
	var sections: Array[Node3D] = []
	for child in hull.get_children():
		var s := child as Node3D
		if s != null and s.name.begins_with("Section_"):
			sections.append(s)
	assert_true(sections.size() >= 2, "la coque livree porte plusieurs troncons")
	# Le tri REEL du jeu, pas une copie : on appelle celui du survol.
	var flyby := track(FlybyScript.new()) as CortegeFlyby
	sections.sort_custom(func(a: Node3D, b: Node3D) -> bool:
		return String(a.name) < String(b.name))
	# ⚠️ DEUX VERITES CONFRONTEES : le nom dit l'ordre, la GEOMETRIE aussi. Le contrat de la
	# forge est le nom ; la physique est le z. S'ils divergent, c'est l'un des deux qui a bouge,
	# et il faut le savoir — pas choisir en silence.
	for i in sections.size():
		assert_eq(String(sections[i].name), "Section_%02d" % (i + 1),
			"le troncon de rang %d s'appelle bien Section_%02d" % [i, i + 1])
		if i > 0:
			assert_true(sections[i].position.z < sections[i - 1].position.z,
				"et il est PLUS LOIN vers la poupe que le precedent (%.0f apres %.0f)"
					% [sections[i].position.z, sections[i - 1].position.z])
	assert_true(flyby != null, "le survol se monte")

# --- Le decollage -------------------------------------------------------------

## ⚠️ CE QUI EST GARDE ICI EST UN DELAI, ET IL EST TOUT L'INTERET. Les coques apparaissaient
## instantanement au centre du puits : « les ennemis apparaissent par magie » (operateur, en
## jouant). Un pont qu'on abat pour tarir sa production doit d'abord se LIRE comme une
## production — sinon abattre le pont ne se relie a rien. La silhouette monte, franchit la
## bouche, et c'est SEULEMENT la que la coque entre en jeu.
func test_a_bay_shows_the_launch_before_the_hull_is_in_play() -> void:
	var bay := track(BayScript.make(TUNING, 0)) as CortegeBay
	var lancees := [0]
	bay.released.connect(func(_e: EnemyController) -> void: lancees[0] += 1)
	# Au-dessus du terrain, la ou un pont lache.
	var pas := 0.02
	var ecoule := 0.0
	while ecoule < TUNING.bay_release_interval + 0.01:
		bay.tick(pas, _world_at(0.0), GameplayPlane.to_plane(_world_at(0.0)))
		ecoule += pas
	assert_eq(lancees[0], 0,
		"a l'instant du lacher, RIEN n'est encore en jeu — la porte vient de s'ouvrir")
	# Puis la duree de la montee.
	ecoule = 0.0
	while ecoule < BayScript.LAUNCH_TIME + 0.05:
		bay.tick(pas, _world_at(0.0), GameplayPlane.to_plane(_world_at(0.0)))
		ecoule += pas
	# ⚠️ Sans pool cable (`build()` n'a pas ete appele), aucune coque n'est reservee : ce que ce
	# test garde est le DELAI, pas le nombre. Le nombre est garde par l'invariant du reglage.
	# ⚠️ QUATRE TEMPS, ET C'EST LE PREMIER QUI COMPTE. « Appareil au repos » est le seul qui
	# explique la mecanique : un vrai vaisseau immobile dans une cavite dit que la structure
	# PRODUIT, sans un mot. Les trois autres ne font que confirmer.
	assert_true(BayScript.REST_TIME >= 0.5,
		"l'appareil reste pose assez longtemps pour etre vu (%.2f s)" % BayScript.REST_TIME)
	assert_true(BayScript.IGNITION_TIME > 0.2,
		"l'allumage se voit avant que ça ne bouge (%.2f s)" % BayScript.IGNITION_TIME)
	var sequence := BayScript.REST_TIME + BayScript.IGNITION_TIME + BayScript.LAUNCH_TIME
	assert_true(sequence < TUNING.bay_release_interval + BayScript.LAUNCH_TIME,
		"la sequence (%.2f s) tient dans la cadence du pont, sinon les places s'epuisent" % sequence)

## ⚠️ CE TEST GARDE UNE FORMULE QUI A ETE FAUSSE, ET QUI NE POUVAIT PAS ETRE PRISE EN DEFAUT.
## L'orientation du rotateur valait `-angle + PI/2` : juste sur l'axe X, fausse de 180 deg vers
## le haut de l'ecran. Elle n'a jamais rougi parce que la tete n'etait JAMAIS construite — un
## mauvais type la faisait echouer a l'execution, et la tourelle tirait quand meme. Deux defauts
## qui se cachaient l'un l'autre, et une porte de qualite verte par-dessus.
func test_the_barrel_points_where_the_turret_aims() -> void:
	# Le tube pointe vers son +z local ; une rotation de theta autour de Y l'emmene sur
	# (sin theta, 0, cos theta). Le plan de jeu envoie (x, y) sur le monde (x, 0, -y).
	for aim in [Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0), Vector2(0, -1),
			Vector2(0.6, 0.8), Vector2(-0.6, -0.8)]:
		var yaw := TurretScript.barrel_yaw(aim)
		var pointe := Vector3(sin(yaw), 0.0, cos(yaw))
		var voulu := Vector3(aim.x, 0.0, -aim.y).normalized()
		assert_true(pointe.distance_to(voulu) < 0.0001,
			"vise %s -> le tube pointe %s, il devrait pointer %s" % [aim, pointe, voulu])

# --- Le plafond des pieces de gameplay ---------------------------------------

## ⚠️ CE TEST TIENT UN ARBITRAGE, PAS UNE COTE. La hauteur de 1,70 m demandee par la planche ne
## tient pas sous le plafond du DECOR (-3,00) a dix emplacements sur dix-sept : la chine du borde
## n'y laisse que 1,28 m. Trois issues existaient — ecarter dix marqueurs, rabaisser les tourelles
## a 1,25 m et redevenir le jeton qu'on vient de remplacer, ou lire la regle pour ce qu'elle dit.
##
## Ce que le plafond protege tient en une phrase : « masquerait le combat SANS JAMAIS POUVOIR
## ETRE TOUCHE ». Une tourelle se tire dessus. A -2,40 elle reste 2,40 unites SOUS le plan de
## vol : elle ne peut ni masquer le chasseur ni le heurter. C'est cette lecture qui est actee, et
## c'est ce test qui l'empeche de deriver en « on verra bien ».
func test_no_turret_ever_reaches_the_flight_plane() -> void:
	var kit: PackedScene = load(TurretScript.KIT_PATH)
	assert_true(kit != null, "le kit de tourelle se charge")
	var assembled := track(kit.instantiate()) as Node3D
	# La piece la plus haute de l'affut, offset d'assemblage compris.
	var offsets := {
		"turret_pad": 0.0, "turret_anchor_skirt": 0.0,
		"turret_ring": TurretScript.RING_LIFT, "turret_body": TurretScript.BODY_LIFT,
		"turret_barrel": TurretScript.BARREL_LIFT,
		"turret_barrel_short": TurretScript.BARREL_LIFT,
		"turret_service_box": TurretScript.SERVICE_LIFT,
		"turret_pipe": TurretScript.SERVICE_LIFT,
	}
	var tallest := -100.0
	for child in assembled.get_children():
		var piece := child as MeshInstance3D
		if piece == null or not offsets.has(piece.name):
			continue
		var top: float = float(offsets[piece.name]) + piece.get_aabb().end.y
		tallest = maxf(tallest, top)
	assert_true(tallest > 1.0, "l'affut a bien une hauteur mesurable (%.2f m)" % tallest)

	# Et le pire marqueur de la coque livree : c'est lui qui decide.
	var hull := track((load(FlybyScript.DECOR_PATH) as PackedScene).instantiate()) as Node3D
	var worst := -100.0
	for section in hull.get_children():
		var s := section as Node3D
		if s == null or not s.name.begins_with("Section_"):
			continue
		for child in s.get_children():
			var marker := child as Node3D
			if marker != null and marker.name.begins_with("Turret_"):
				worst = maxf(worst, s.position.y + marker.position.y)
	assert_true(worst > -10.0, "des marqueurs de tourelle ont bien ete trouves")
	var summit := worst + tallest
	assert_true(summit <= FlybyScript.GAMEPLAY_CEILING_Y,
		"la tourelle la plus haute culmine a %.3f, au-dessus du plafond de gameplay %.2f"
			% [summit, FlybyScript.GAMEPLAY_CEILING_Y])
	# ⚠️ ET ELLE RESTE LOIN DU PLAN DE VOL. C'est la moitie de l'arbitrage : 2,40 unites de
	# degagement, soit une fois et demie la hauteur de la tourelle elle-meme.
	assert_true(summit < -1.5,
		"elle reste tres en dessous du plan de vol (%.2f) — sinon elle masquerait le combat" % summit)

# --- Le kit d'epine ----------------------------------------------------------

## ⚠️ CE TEST EXISTE PARCE QUE LE MEME DEFAUT A DEJA COUTE DEUX FOIS. Un kit se monte dans
## `_ready()`, donc hors de tout test qui instancie la piece a la main : la tourelle a tire
## pendant une session entiere SANS TETE — cible valide, balles a l'ecran, 750 assertions vertes
## — parce qu'une variable etait typee `MeshInstance3D` la ou la piece est un `Node3D`. Rien
## dans le jeu ne signale une silhouette absente. Le seul garde possible est de charger le
## binaire et de verifier que ce que le moteur va chercher s'y trouve, sous les noms exacts.
func test_the_spine_kit_carries_the_three_pieces_the_engine_mounts() -> void:
	var kit: PackedScene = load(NodeScript.KIT_PATH)
	assert_true(kit != null, "le kit d'epine se charge")
	var assembled := track(kit.instantiate()) as Node3D
	var found := {}
	for child in assembled.get_children():
		var piece := child as MeshInstance3D
		if piece != null:
			found[String(piece.name)] = piece
	for part in ["spine_cradle", "spine_core", "spine_brace"]:
		assert_true(found.has(part), "le kit porte la piece « %s »" % part)

## ⚠️ LA MORT DU NOEUD EST PORTEE PAR LA GEOMETRIE, PAS PAR UN REGLAGE. Le moteur ne detruit que
## `spine_core` : si une seule autre piece portait un emissif, la carcasse resterait allumee et
## un noeud abattu serait indiscernable d'un noeud intact. C'est la regle dure du BRIEF-0094, et
## elle ne se verifie que sur le binaire — une reforge peut la casser sans toucher au code.
func test_only_the_core_of_a_spine_node_carries_light() -> void:
	var kit: PackedScene = load(NodeScript.KIT_PATH)
	var assembled := track(kit.instantiate()) as Node3D
	for child in assembled.get_children():
		var piece := child as MeshInstance3D
		if piece == null or piece.mesh == null:
			continue
		for i in piece.mesh.get_surface_count():
			var material := piece.mesh.surface_get_material(i) as StandardMaterial3D
			if material == null or not material.emission_enabled:
				continue
			assert_eq(String(piece.name), "spine_core",
				"seul le coeur est emissif — « %s » ne doit pas l'etre" % piece.name)

## Le noeud est la seule des trois pieces qui n'a PAS besoin du plafond de gameplay releve : il
## siege au fond de la tranchee, qui lui mange un demi-metre. Le verifier tient l'arbitrage par
## les deux bouts — si une reforge remontait le canal, on le saurait ici et pas en jeu.
func test_a_spine_node_stays_under_the_ceiling_of_inert_decor() -> void:
	var kit: PackedScene = load(NodeScript.KIT_PATH)
	var assembled := track(kit.instantiate()) as Node3D
	var offsets := {
		"spine_cradle": 0.0,
		"spine_core": NodeScript.CORE_LIFT,
		"spine_brace": NodeScript.BRACE_LIFT,
	}
	var tallest := -100.0
	for child in assembled.get_children():
		var piece := child as MeshInstance3D
		if piece == null or not offsets.has(piece.name):
			continue
		tallest = maxf(tallest, float(offsets[piece.name]) + piece.get_aabb().end.y)
	assert_true(absf(tallest - 1.50) < 0.05,
		"le noeud fait bien 1,50 m de haut une fois assemble (%.2f m)" % tallest)

	var hull := track((load(FlybyScript.DECOR_PATH) as PackedScene).instantiate()) as Node3D
	var worst := -100.0
	for section in hull.get_children():
		var s := section as Node3D
		if s == null or not s.name.begins_with("Section_"):
			continue
		for child in s.get_children():
			var marker := child as Node3D
			if marker != null and marker.name.begins_with("Spine_"):
				worst = maxf(worst, s.position.y + marker.position.y)
	assert_true(worst > -10.0, "des marqueurs d'epine ont bien ete trouves")
	assert_true(worst + tallest <= FlybyScript.CEILING_Y,
		"le noeud culmine a %.3f, au-dessus du plafond du decor %.2f"
			% [worst + tallest, FlybyScript.CEILING_Y])

## ⚠️ ON VISE CE QU'ON VOIT, ET C'EST CE QUI ETAIT FAUX. La zone de touche se projetait depuis
## l'assise de la piece ; a 70 deg de plongee, une cible haute d'un metre se projette a une
## vingtaine de centimetres de la. Sur le noeud, rayon 0,78 et cible la plus dure du niveau,
## l'ecart valait un quart du rayon — offert au hasard, et invisible sur toute capture fixe.
func test_the_aim_point_follows_the_mass_and_not_the_seat() -> void:
	var eye := Vector3(0.0, 14.0, 5.0)
	var seat := Vector3(0.0, -4.58, 0.0)
	var from_seat := GameplayPlane.aim_point_of(seat, eye)
	var from_mass := GameplayPlane.aim_point_of(
		seat + Vector3(0.0, NodeScript.HIT_LIFT, 0.0), eye)
	assert_true(from_seat.distance_to(from_mass) > 0.15,
		"l'ecart corrige est reel (%.3f unite)" % from_seat.distance_to(from_mass))
	# Et il va vers le bas de l'ecran : plus la piece est haute, plus elle se projette pres du
	# point au sol de la camera. Un signe inverse voudrait dire qu'on l'a corrige a l'envers.
	assert_true(from_mass.y > from_seat.y,
		"la masse se projette en avant de l'assise (%.3f contre %.3f)" % [from_mass.y, from_seat.y])
	# Le hangar CREUSE : lui n'a rien a corriger, et une valeur non nulle serait une regression.
	assert_eq(BayScript.HIT_LIFT, 0.0, "le hangar ne monte pas, donc ne se decale pas")
