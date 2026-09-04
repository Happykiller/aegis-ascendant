extends "res://tests/test_case.gd"
## La Citadelle de Defense : le verrou de mi-parcours du Long Cortege (lot 1 — la boucle).
##
## ⚠️ CE QUE CES TESTS GARDENT N'EST PAS LA MACHINE A ETATS, C'EST CE QUI EST SILENCIEUX AUTOUR
## D'ELLE. Sept defauts sont possibles ici, aucun ne produirait la moindre erreur au lancement,
## et six d'entre eux ne se verraient pas en jouant :
##
##   1. une piece posee trop en arriere s'immobilise HORS du plan de vol et hors de sa propre
##      fenetre : elle ne s'engage jamais, elle ne tire jamais, et le journal ne dit rien ;
##   2. le mur ne couvre pas toute la largeur du plan : le joueur CONTOURNE le verrou par le
##      vide, la sequence devient facultative, et la partie qui l'evite se joue normalement ;
##   3. le noyau naît vulnerable une trame avant son cablage : il tombe avant les relais une
##      fois sur cent, et jamais quand on le cherche ;
##   4. la forme solide reste apres l'ouverture — ou disparaît avant : un mur invisible, ou un
##      passage qui n'en est pas un ;
##   5. la citadelle mord la fosse de s = 228 ou le socle de `Turret_07` : deux volumes qui se
##      traversent, ce qui ne se voit qu'en capture ;
##   6. une boîte franchit l'un des deux plafonds d'`ADR-0041` et masque le combat ;
##   7. le freinage est lineaire au lieu d'etre en racine : le survol s'approche du mur
##      indefiniment sans jamais s'arreter, donc l'etat suivant ne s'ouvre pas.
##
## Le seul qui se verrait en jouant est le quatrieme.

const CitadelScript := preload("res://scripts/gameplay/cortege_citadel.gd")
const PartScript := preload("res://scripts/gameplay/citadel_part.gd")
const TurretScript := preload("res://scripts/gameplay/cortege_turret.gd")
const FlybyScript := preload("res://scripts/vfx/cortege_flyby.gd")
const TuningScript := preload("res://resources/data/cortege_tuning.gd")
const TUNING := preload("res://resources/levels/long_cortege_tuning.tres")
const LEVEL_SCENE := "res://scenes/gameplay/cortege.tscn"

## La FOSSE du troncon 3 et sa garde, lues dans `build_long_cortege.py` (`PITS`, `PIT_KEEPOUT`).
## ⚠️ RECOPIEES ICI FAUTE DE PONT VERS LE PYTHON, et c'est assume : ce qu'elles gardent est que
## la citadelle ne se pose pas DANS un trou de 1,55 m. Le jour ou la fosse bouge, ce test dira
## une contrainte perimee — mais il la dira, alors qu'aujourd'hui rien ne la dirait du tout.
const PIT_S := 228.0
const PIT_HALF_S := 6.0
const PIT_KEEPOUT := 2.20

## Le socle de `Turret_07` : `PAD_RADIUS` du troncon 3.
const PAD_RADIUS_S3 := 2.75


# =============================================================================
# 0. Outillage — la camera est LUE, jamais recopiee
# =============================================================================

## ⚠️ ELLE EST LUE DANS LA SCENE DU NIVEAU, ET C'EST LE POINT DE TOUT CE FICHIER. Ou une piece
## hors du plan de jeu doit etre TIREE depend de l'endroit d'ou on la regarde
## (`GameplayPlane.aim_point_of`). Recopier ici « (0, 14, 5) » ferait passer ces tests au vert
## le jour ou l'on recule la camera — pendant qu'en jeu, les relais sortiraient du plan de vol.
func _camera_eye() -> Vector3:
	var packed: PackedScene = load(LEVEL_SCENE)
	assert_true(packed != null, "la scene du niveau 2 se charge")
	var level := track(packed.instantiate()) as Node3D
	var cam := level.get_node_or_null("CameraDirector/Camera3D") as Node3D
	assert_true(cam != null, "la scene porte bien CameraDirector/Camera3D")
	if cam == null:
		return Vector3(0.0, 14.0, 5.0)
	var eye := _composed_origin(cam)
	# ⚠️ CE GARDE-FOU VAUT TOUS LES AUTRES TESTS DE CE FICHIER. `aim_point_of` a un cas degenere
	# documente : une camera POSEE DANS LE PLAN fait « marcher » le calcul et rend la position de
	# la camera — toutes les cibles au meme endroit, sans une erreur. Un banc qui lirait un oeil
	# a Y = 0 (c'est ce que rend `global_position` hors de l'arbre) verrait donc chaque assertion
	# de ce fichier passer au vert pendant qu'en jeu rien ne serait a sa place.
	assert_true(absf(eye.y) > 1.0,
		"l'oeil de la camera est bien au-dessus du plan (%.2f) — sinon la projection est degeneree et tout ce fichier ment"
			% eye.y)
	return eye

## L'origine d'un nœud, composee A LA MAIN depuis ses parents.
##
## ⚠️ `global_position` NE REPOND QUE DANS L'ARBRE. Hors de lui, le moteur rend l'identite et
## ecrit une ligne au journal que personne ne lit dans une suite de 800 tests. Une scene
## `instantiate()` n'est PAS dans l'arbre : lire l'oeil ainsi aurait rendu (0, 0, 0).
func _composed_origin(node: Node3D) -> Vector3:
	var t := Transform3D.IDENTITY
	var current := node
	while current != null:
		t = current.transform * t
		current = current.get_parent() as Node3D
	return t.origin

## Ou la face avant du verrou se projette dans le plan, apres `travelled` unites de survol.
func _wall_plane_y(travelled: float, eye: Vector3) -> float:
	var a := GameplayPlane.aim_point_of(
		CitadelScript.piece_world(TUNING, CitadelScript.gate_end_local(-1.0), travelled), eye)
	var b := GameplayPlane.aim_point_of(
		CitadelScript.piece_world(TUNING, CitadelScript.gate_end_local(1.0), travelled), eye)
	return (a.y + b.y) * 0.5

## La distance parcourue a laquelle le survol s'immobilise. ⚠️ TROUVEE PAR DICHOTOMIE ET NON
## CALCULEE : la relation passe par la projection de la camera, et la reecrire ici serait
## refaire le calcul que l'on veut verifier.
func _lock_travelled(eye: Vector3) -> float:
	var lo := 0.0
	var hi := TUNING.section_length * float(TUNING.section_count)
	for _i in 60:
		var mid := (lo + hi) * 0.5
		if _wall_plane_y(mid, eye) > TUNING.citadel_wall_plane_y:
			lo = mid
		else:
			hi = mid
	# ⚠️ `hi` ET NON LE MILIEU. La citadelle se verrouille au PREMIER instant ou le mur est a la
	# hauteur demandee ou en dessous ; rendre le milieu de l'intervalle rendrait une distance ou
	# le mur est encore un cheveu trop haut, donc un etat encore `APPROACH`.
	return hi

## Ou une piece se projette dans le plan, une fois le survol immobilise.
func _plane_at_lock(local: Vector3, lift: float, eye: Vector3) -> Vector2:
	var lock := _lock_travelled(eye)
	var world := CitadelScript.piece_world(TUNING, local, lock)
	return GameplayPlane.aim_point_of(world + Vector3(0.0, lift, 0.0), eye)


# =============================================================================
# 1. Le reglage : ce que les invariants REFUSENT
# =============================================================================

func test_the_delivered_tuning_accepts_the_citadel() -> void:
	assert_eq(TUNING.validate().size(), 0,
		"le reglage livre passe ses invariants, citadelle comprise : %s" % str(TUNING.validate()))

## ⚠️ LA LECTURE « GAUCHE + DROITE → CENTRE » VIT DANS LES PV, PAS DANS UNE INTENTION. Un noyau
## moins cher qu'un relais ferait de la protection l'obstacle et de l'objectif une formalite —
## et aucune capture ne le montrerait.
func test_a_core_cheaper_than_a_relay_is_refused() -> void:
	var tuning := TUNING.duplicate() as CortegeTuning
	tuning.citadel_core_health = TUNING.citadel_relay_health - 1.0
	var errors := tuning.validate()
	assert_true(errors.size() > 0, "un noyau moins cher qu'un relais doit etre refuse")

## ⚠️ CE QUI SEPARE LE VERROU D'UN BOSS EST UN CHIFFRE, PAS UNE PHRASE. Le brief l'interdit en
## trois mots (« ce n'est pas un boss ») ; sans borne, une suite d'ajustements raisonnables y
## mene sans qu'aucun garde-fou ne s'en apercoive.
func test_a_lock_that_becomes_a_boss_is_refused() -> void:
	var tuning := TUNING.duplicate() as CortegeTuning
	tuning.citadel_core_health = TUNING.citadel_core_health * 4.0
	assert_true(tuning.validate().size() > 0,
		"un verrou de %.0f s de tir doit etre refuse" % tuning.citadel_fight_time())

## Et l'inverse : un dos d'ane n'est pas un verrou.
func test_a_lock_that_falls_in_passing_is_refused() -> void:
	var tuning := TUNING.duplicate() as CortegeTuning
	tuning.citadel_relay_health = 120.0
	tuning.citadel_core_health = 200.0
	assert_true(tuning.validate().size() > 0,
		"un verrou de %.0f s de tir doit etre refuse" % tuning.citadel_fight_time())

## ⚠️ UN MUR HORS DU PLAN DE VOL N'ARRETE PLUS RIEN, et l'arret du survol devient un temps mort
## ou le joueur attend sans comprendre. C'est le defaut le plus couteux possible : la sequence
## se joue, elle ne bloque rien, et rien au journal ne le dit.
func test_a_wall_outside_the_flight_plane_is_refused() -> void:
	var tuning := TUNING.duplicate() as CortegeTuning
	tuning.citadel_wall_plane_y = GameplayPlane.BOUNDS.end.y
	assert_true(tuning.validate().size() > 0, "un mur pose au plafond du plan doit etre refuse")

## ⚠️ ET UN MUR TROP BAS NE LAISSE PLUS DE TERRAIN. La chambre du reacteur a deja paye ce
## defaut, mesure : « c'est comme si tout le cercle etait un mur pour moi ».
func test_a_wall_that_leaves_no_arena_is_refused() -> void:
	var tuning := TUNING.duplicate() as CortegeTuning
	tuning.citadel_wall_plane_y = GameplayPlane.BOUNDS.position.y + 4.0
	assert_true(tuning.validate().size() > 0,
		"un mur qui ne laisse que %.1f unites d'arene doit etre refuse" % tuning.citadel_arena_height())

## ⚠️ SE DIMENSIONNER SUR L'OCCUPATION DE LA COQUE OUVERTE REVIENT A SE DONNER RAISON : l'arene
## du verrou est plus etroite, ses tourelles tirent d'un point fixe, le joueur esquive plus qu'il
## ne tire. C'est exactement le defaut qu'`ADR-0024` a paye sur le flux du Leviathan.
func test_an_arena_declared_more_generous_than_the_open_hull_is_refused() -> void:
	var tuning := TUNING.duplicate() as CortegeTuning
	tuning.occupancy_citadel = TUNING.occupancy_hull + 0.05
	assert_true(tuning.validate().size() > 0,
		"une occupation de verrou plus genereuse que celle de la coque doit etre refusee")


# =============================================================================
# 2. Le freinage ATTEINT l'arret — et ce n'est pas evident
# =============================================================================

## ⚠️ UN FACTEUR LINEAIRE EN DISTANCE N'ARRIVE JAMAIS. `du/dt = -k.u` est une approche
## exponentielle : le vaisseau se traînerait devant le mur sans jamais l'atteindre, donc
## `LOCKED` ne s'ouvrirait pas, donc la sequence entiere resterait bloquee — sans une erreur.
## La racine EST la deceleration constante, et elle touche zero en temps fini.
func test_the_brake_is_a_constant_deceleration_and_not_a_ramp() -> void:
	var span := TUNING.citadel_brake_span
	assert_almost_eq(TuningScript.brake_factor(span * 2.0, span), 1.0, 0.001,
		"au-dela du seuil, le survol garde sa vitesse de croisiere")
	assert_almost_eq(TuningScript.brake_factor(0.0, span), 0.0, 0.001,
		"a l'arret, le facteur est nul")
	# A mi-distance, une rampe lineaire rendrait 0,5 ; la racine rend 0,707.
	assert_true(TuningScript.brake_factor(span * 0.5, span) > 0.6,
		"a mi-distance le survol va encore vite (%.3f) — une rampe lineaire n'atteindrait pas l'arret"
			% TuningScript.brake_factor(span * 0.5, span))

## Et il s'arrete VRAIMENT : on integre le freinage pas a pas, et la distance restante tombe.
func test_the_brake_reaches_zero_in_finite_time() -> void:
	var span := TUNING.citadel_brake_span
	var remaining := span
	var elapsed := 0.0
	var dt := 1.0 / 60.0
	while remaining > 0.0 and elapsed < 30.0:
		remaining -= TUNING.scroll_speed * TuningScript.brake_factor(remaining, span) * dt
		elapsed += dt
	assert_true(remaining <= 0.0,
		"le freinage atteint l'arret (reste %.4f apres %.1f s)" % [remaining, elapsed])
	assert_true(elapsed < 12.0, "et il y met %.1f s, pas une eternite" % elapsed)


# =============================================================================
# 3. La pose sur la coque LIVREE
# =============================================================================

func test_the_citadel_lands_on_the_section_that_carries_its_station() -> void:
	assert_eq(CitadelScript.section_of(TUNING), 2,
		"s = %.0f tombe dans le troncon 3" % TUNING.citadel_station)
	assert_almost_eq(CitadelScript.local_z_in_section(TUNING), -40.0, 0.001,
		"et a 40 m du debut de ce troncon, en z local")

## ⚠️ LE TRONCON EST BIEN A -200, ET C'EST LA COQUE QUI LE DIT. Une citadelle posee sur un
## troncon dont l'origine aurait bouge se retrouverait cent metres plus loin, en silence.
func test_the_citadel_station_matches_the_delivered_hull() -> void:
	var hull := track((load(FlybyScript.DECOR_PATH) as PackedScene).instantiate()) as Node3D
	var section := hull.get_node_or_null("Section_03") as Node3D
	assert_true(section != null, "la coque livree porte Section_03")
	if section == null:
		return
	var monde_z: float = section.position.z + CitadelScript.local_z_in_section(TUNING)
	assert_almost_eq(monde_z, -TUNING.citadel_station, 0.001,
		"la citadelle se pose a z = %.1f, soit la station %.0f" % [monde_z, TUNING.citadel_station])

## ⚠️ TROIS VOISINS MESURES, ET AUCUN N'EST NEGOCIABLE. La fenetre libre de la mi-parcours fait
## dix-neuf metres ; la citadelle en occupe six. Mordre l'un des trois ne produirait aucune
## erreur — juste deux volumes qui se traversent, ce qui ne se voit qu'en capture.
func test_the_citadel_bites_none_of_its_three_neighbours() -> void:
	var avant: float = TUNING.citadel_station + CitadelScript.BASTION_S.x
	var arriere: float = TUNING.citadel_station + CitadelScript.BASTION_S.y
	assert_true(arriere > avant, "l'emprise a bien une longueur")
	var fosse_fin := PIT_S + PIT_HALF_S + PIT_KEEPOUT
	assert_true(avant > fosse_fin,
		"le bord avant (%.1f) reste en aval de la garde de la fosse (%.1f)" % [avant, fosse_fin])
	var markers := _section_markers("Section_03")
	assert_true(markers.has("Turret_07"), "Turret_07 est bien sur le troncon 3")
	for nom in markers:
		var station: float = 200.0 - (markers[nom] as Vector3).z
		var garde := PAD_RADIUS_S3 if String(nom).begins_with("Turret_") else 4.30
		var libre: bool = station - garde > arriere or station + garde < avant
		assert_true(libre,
			"%s est a s = %.1f (garde %.2f) et l'emprise va de %.1f a %.1f : les deux se traversent"
				% [nom, station, garde, avant, arriere])

func _section_markers(nom_section: String) -> Dictionary:
	var hull := track((load(FlybyScript.DECOR_PATH) as PackedScene).instantiate()) as Node3D
	var section := hull.get_node_or_null(nom_section) as Node3D
	var markers := {}
	if section == null:
		return markers
	for child in section.get_children():
		var marker := child as Node3D
		if marker != null:
			markers[String(marker.name)] = marker.position
	return markers


# =============================================================================
# 4. Les deux plafonds d'ADR-0041
# =============================================================================

## ⚠️ LA DISTINCTION N'EST PAS UN ASSOUPLISSEMENT, C'EST LA REGLE LUE CORRECTEMENT : le decor
## INERTE ne monte pas au-dessus de -3,00, ce qu'on peut DETRUIRE va jusqu'a -2,40. Le noyau est
## donc autorise a etre le point le plus haut de la citadelle, et les bastions ne le sont pas.
func test_no_inert_volume_of_the_citadel_reaches_the_decor_ceiling() -> void:
	assert_almost_eq(CitadelScript.GATE_TOP_Y, FlybyScript.CEILING_Y, 0.001,
		"la porte culmine exactement au plafond du decor inerte")
	assert_true(CitadelScript.BASTION_TOP_Y < FlybyScript.CEILING_Y,
		"le pont du bastion (%.2f) reste sous le plafond du decor" % CitadelScript.BASTION_TOP_Y)

func test_the_destructible_pieces_stay_under_the_gameplay_ceiling() -> void:
	var relais: float = CitadelScript.RELAY_BASE_Y + CitadelScript.RELAY_SIZE.y
	var noyau: float = CitadelScript.CORE_BASE_Y + CitadelScript.CORE_SIZE.y
	# ⚠️ UNE TOLERANCE D'UN MILLIMETRE, ET ELLE N'EST PAS DE LA COMPLAISANCE : -4,58 + 2,18 rend
	# -2,4000001 en flottant simple. Comparer au strict ferait echouer une piece qui affleure
	# EXACTEMENT le plafond, ce qui est le cas voulu.
	const EPAISSEUR_FLOTTANTE := 0.001
	assert_true(relais <= FlybyScript.GAMEPLAY_CEILING_Y + EPAISSEUR_FLOTTANTE,
		"un relais culmine a %.2f pour un plafond de gameplay a %.2f"
			% [relais, FlybyScript.GAMEPLAY_CEILING_Y])
	assert_true(noyau <= FlybyScript.GAMEPLAY_CEILING_Y + EPAISSEUR_FLOTTANTE,
		"le noyau culmine a %.2f pour un plafond de gameplay a %.2f"
			% [noyau, FlybyScript.GAMEPLAY_CEILING_Y])
	# ⚠️ ET C'EST LE NOYAU QUI EST LE PLUS HAUT. C'est ce qui le designe comme le centre sans un
	# mot de HUD : le seul volume autorise a culminer est celui qu'on peut tirer.
	assert_true(noyau >= relais, "le noyau (%.2f) domine les relais (%.2f)" % [noyau, relais])
	assert_true(noyau > CitadelScript.GATE_TOP_Y,
		"et il domine la porte (%.2f) : le point le plus haut du verrou est sa cible"
			% CitadelScript.GATE_TOP_Y)

## ⚠️ LA TOURELLE DU VERROU SIEGE A -3,60 ET NON SUR LA COURONNE A -3,00, ET LE KIT LE DECIDE.
## A -3,00, l'affut leger culminerait AU-DESSUS du plafond de gameplay ; la couronne est donc
## batie ailleurs que sous les tourelles. Le kit est MESURE ici, pas recopie : le jour ou la
## forge l'agrandit, ce test le voit avant le jeu.
func test_a_guard_turret_seated_on_the_bastion_stays_under_the_gameplay_ceiling() -> void:
	var kit: PackedScene = load(TurretScript.KIT_PATH)
	assert_true(kit != null, "le kit de tourelle se charge")
	var assembled := track(kit.instantiate()) as Node3D
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
		tallest = maxf(tallest, float(offsets[piece.name]) + piece.get_aabb().end.y)
	assert_true(tallest > 1.0, "l'affut a une hauteur mesurable (%.2f m)" % tallest)
	var sommet: float = CitadelScript.TURRET_Y + tallest * TurretScript.LIGHT_GEOM_SCALE
	assert_true(sommet <= FlybyScript.GAMEPLAY_CEILING_Y,
		"une tourelle du verrou culmine a %.2f pour un plafond a %.2f — la couronne ne doit pas la porter"
			% [sommet, FlybyScript.GAMEPLAY_CEILING_Y])


# =============================================================================
# 5. A L'ARRET, TOUT CE QUI SE TIRE EST TIRABLE
# =============================================================================

## ⚠️ LE DEFAUT LE PLUS SILENCIEUX DE TOUT LE LOT. Une piece posee quelques metres trop en
## arriere s'immobilise au-dessus du plan de vol : elle ne s'engage jamais, elle ne tire jamais,
## elle ne se tire pas — et la partie se joue exactement comme si elle n'existait pas.
func test_every_target_of_the_lock_sits_inside_the_flight_plane() -> void:
	var eye := _camera_eye()
	var cibles := [
		["le relais babord", CitadelScript.relay_local(-1.0), CitadelScript.RELAY_SIZE.y * 0.5],
		["le relais tribord", CitadelScript.relay_local(1.0), CitadelScript.RELAY_SIZE.y * 0.5],
		["le noyau", CitadelScript.core_local(), CitadelScript.CORE_SIZE.y * 0.5],
	]
	for cible in cibles:
		var here: Vector2 = _plane_at_lock(cible[1], cible[2], eye)
		assert_true(GameplayPlane.is_inside(here),
			"%s s'immobilise en (%.2f, %.2f), hors du plan de vol" % [cible[0], here.x, here.y])

## ⚠️ ET UNE TOURELLE DOIT ETRE DANS SA PROPRE FENETRE, CE QUI EST PLUS STRICT. Sa fenetre fait
## 14 unites ; hors d'elle, `CortegeTurret` ne passe jamais de `AHEAD` a `LIVE` — la piece est
## montee, visible, et muette pour toujours.
func test_every_guard_turret_of_the_lock_is_inside_its_own_firing_window() -> void:
	var eye := _camera_eye()
	var half: float = TUNING.light_turret_visible_span * 0.5
	for side in [-1.0, 1.0]:
		for index in CitadelScript.TURRET_S.size():
			var here := _plane_at_lock(CitadelScript.turret_local(side, index),
				TurretScript.LIGHT_HIT_LIFT, eye)
			assert_true(absf(here.y) <= half,
				"une tourelle du verrou s'immobilise a y = %.2f pour une fenetre de +/- %.1f : elle ne s'engagerait jamais"
					% [here.y, half])
			assert_true(GameplayPlane.is_inside(here),
				"et elle reste dans le plan de vol (%.2f, %.2f)" % [here.x, here.y])

## ⚠️ SI LE MUR NE FERME PAS TOUTE LA LARGEUR, LE JOUEUR LE CONTOURNE PAR LE VIDE. La coque fait
## 28 m ; le plan de vol, une fois la parallaxe appliquee, en couvre davantage. Une barriere
## arretee au borde rendrait la sequence FACULTATIVE — et la partie qui l'evite se jouerait
## normalement, sans une ligne au journal.
func test_the_gate_closes_the_whole_flight_plane() -> void:
	var eye := _camera_eye()
	var lock := _lock_travelled(eye)
	var a := GameplayPlane.aim_point_of(
		CitadelScript.piece_world(TUNING, CitadelScript.gate_end_local(-1.0), lock), eye)
	var b := GameplayPlane.aim_point_of(
		CitadelScript.piece_world(TUNING, CitadelScript.gate_end_local(1.0), lock), eye)
	assert_true(a.x <= GameplayPlane.BOUNDS.position.x,
		"le bout babord du mur (%.2f) atteint le bord du plan (%.2f)"
			% [a.x, GameplayPlane.BOUNDS.position.x])
	assert_true(b.x >= GameplayPlane.BOUNDS.end.x,
		"le bout tribord du mur (%.2f) atteint le bord du plan (%.2f)"
			% [b.x, GameplayPlane.BOUNDS.end.x])

## L'arene que le mur laisse au joueur, mesuree et non declaree.
func test_the_lock_leaves_the_player_a_real_arena() -> void:
	var eye := _camera_eye()
	var mur := _wall_plane_y(_lock_travelled(eye), eye)
	assert_almost_eq(mur, TUNING.citadel_wall_plane_y, 0.05,
		"le mur s'immobilise ou le reglage le demande")
	assert_true(mur - GameplayPlane.BOUNDS.position.y >= 9.0,
		"il reste %.1f unites d'arene sous le mur" % (mur - GameplayPlane.BOUNDS.position.y))


# =============================================================================
# 6. LA BOUCLE — et elle se joue dans les deux ordres
# =============================================================================

## Monte le verrou et le fait avancer a la main. ⚠️ AUCUN ARBRE DE SCENE : `global_position` ne
## repond que dans une scene montee, et c'est pour ca que la citadelle recoit le parcouru et
## l'oeil au lieu de les lire. Ce banc est exactement ce que cette decision achete.
func _mounted() -> CortegeCitadel:
	var citadel := track(CitadelScript.make(TUNING)) as CortegeCitadel
	citadel.setup(null, null, null)
	return citadel

func test_the_core_is_untouchable_while_a_single_relay_stands() -> void:
	var eye := _camera_eye()
	var lock := _lock_travelled(eye)
	var citadel := _mounted()
	citadel.tick(0.016, lock, eye)
	var core := citadel.core()
	assert_false(core.is_vulnerable(), "le noyau naît protege")
	core.target().hit_callback.call(9999.0)
	assert_true(core.is_alive(), "un tir encaisse par le bouclier ne le tue pas")
	assert_almost_eq(core.health_ratio(), 1.0, 0.0001,
		"et il ne lui coute PAS UN POINT — un noyau a 99 pct qui descend racontait un boss")
	# Un seul relais tombe : rien ne change.
	citadel.relays()[0].target().hit_callback.call(TUNING.citadel_relay_health)
	citadel.tick(0.016, lock, eye)
	assert_eq(citadel.state(), CitadelScript.State.ONE_RELAY, "un relais tombe, l'etat le dit")
	core.target().hit_callback.call(9999.0)
	assert_almost_eq(core.health_ratio(), 1.0, 0.0001,
		"et le noyau ne perd toujours rien avec un seul relais debout")

## ⚠️ LES DEUX ORDRES DOIVENT DONNER LA MEME OUVERTURE. Nommer un « premier » et un « second »
## relais ferait dependre la sequence du bord attaque : la moitie des parties jouerait un autre
## jeu que l'autre moitie, sans qu'aucune trace ne le dise.
func test_both_relay_orders_open_the_same_lock() -> void:
	var eye := _camera_eye()
	var lock := _lock_travelled(eye)
	for ordre in [[0, 1], [1, 0]]:
		var citadel := _mounted()
		citadel.tick(0.016, lock, eye)
		for i in ordre:
			citadel.relays()[i].target().hit_callback.call(TUNING.citadel_relay_health)
		citadel.tick(0.016, lock, eye)
		assert_eq(citadel.state(), CitadelScript.State.SHIELD_DOWN,
			"ordre %s : les deux relais tombes, le bouclier tombe avec eux" % str(ordre))
		assert_true(citadel.core().is_vulnerable(),
			"ordre %s : et le noyau devient touchable" % str(ordre))
		citadel.core().target().hit_callback.call(TUNING.citadel_core_health)
		assert_false(citadel.core().is_alive(), "ordre %s : le noyau tombe" % str(ordre))
		free_tracked()

## ⚠️ LA ROUTE N'EST RENDUE QU'A `CLEARED`, ET JAMAIS AVANT. Entre la mort du noyau et le
## passage praticable il y a l'ouverture : rendre la route a la mort du noyau ferait traverser
## un mur encore debout.
func test_the_route_opens_only_after_the_opening_has_run() -> void:
	var eye := _camera_eye()
	var lock := _lock_travelled(eye)
	var citadel := _mounted()
	citadel.tick(0.016, lock, eye)
	for relay in citadel.relays():
		relay.target().hit_callback.call(TUNING.citadel_relay_health)
	citadel.core().target().hit_callback.call(TUNING.citadel_core_health)
	citadel.tick(0.016, lock, eye)
	assert_eq(citadel.state(), CitadelScript.State.CORE_DEAD,
		"le noyau mort, l'ouverture commence — la route n'est pas encore rendue")
	assert_false(citadel.is_cleared(), "et elle ne l'est pas")
	var horloge := 0.0
	while not citadel.is_cleared() and horloge < 20.0:
		citadel.tick(0.05, lock, eye)
		horloge += 0.05
	assert_true(citadel.is_cleared(), "l'ouverture aboutit (%.2f s)" % horloge)
	assert_almost_eq(horloge, TUNING.citadel_open_time, 0.12,
		"et elle dure ce que le reglage promet")

## ⚠️ LA FORME SOLIDE EXISTE DANS TOUS LES ETATS SAUF `CLEARED`. Un mur qui n'apparaîtrait qu'a
## l'arret laisserait le joueur se poster derriere lui pendant le freinage, puis se retrouver du
## mauvais cote sans avoir rien fait de mal. Et un mur qui SURVIVRAIT a l'ouverture serait un
## mur invisible : la meme injustice qu'une tourelle qu'on croit pouvoir raser et qui traverse.
func test_the_solid_stands_until_cleared_and_not_one_frame_longer() -> void:
	var eye := _camera_eye()
	var lock := _lock_travelled(eye)
	var citadel := _mounted()
	citadel.tick(0.016, lock, eye)
	var shapes := PlaneShapes.new()
	citadel.fill_solids(shapes)
	assert_eq(shapes.size(), 1, "le verrou ferme la route avant meme d'avoir ete engage")
	assert_eq(shapes.kind_at(0), PlaneShapes.Kind.CAPSULE, "et il le fait par un segment epais")
	for relay in citadel.relays():
		relay.target().hit_callback.call(TUNING.citadel_relay_health)
	citadel.core().target().hit_callback.call(TUNING.citadel_core_health)
	var horloge := 0.0
	while not citadel.is_cleared() and horloge < 20.0:
		citadel.tick(0.05, lock, eye)
		horloge += 0.05
		shapes.clear()
		citadel.fill_solids(shapes)
		if not citadel.is_cleared():
			assert_eq(shapes.size(), 1,
				"la route reste fermee tant que l'etat n'est pas CLEARED (%s)" % citadel.state_name())
	shapes.clear()
	citadel.fill_solids(shapes)
	assert_eq(shapes.size(), 0, "et elle s'ouvre exactement a CLEARED")

## ⚠️ AUCUNE FORME AVANT D'AVOIR RELEVE LE MUR. Sans ce garde, la premiere image physique
## verserait une capsule de 90 cm posee a l'ORIGINE du plan — la ou le chasseur naît.
func test_an_unmeasured_wall_blocks_nobody() -> void:
	var citadel := track(CitadelScript.make(TUNING)) as CortegeCitadel
	var shapes := PlaneShapes.new()
	citadel.fill_solids(shapes)
	assert_eq(shapes.size(), 0,
		"un verrou qui n'a pas encore ete releve ne pose aucun obstacle")


# =============================================================================
# 7. LE SURVOL OBEIT AU VERROU
# =============================================================================

## ⚠️ TROIS REGIMES, ET AUCUN N'EST DECORATIF. Loin, le survol garde sa vitesse ; au verrou il
## s'arrete VRAIMENT (un survol qui rampe a 5 pct laisserait la citadelle deriver hors du plan
## pendant le combat) ; apres l'ouverture il repart progressivement.
func test_the_flyby_obeys_the_lock_in_three_regimes() -> void:
	var eye := _camera_eye()
	var lock := _lock_travelled(eye)
	var loin := _mounted()
	loin.tick(0.016, lock - TUNING.citadel_brake_span * 4.0, eye)
	assert_almost_eq(loin.scroll_factor(), 1.0, 0.001,
		"loin du verrou, le survol garde sa vitesse de croisiere")
	free_tracked()

	var arrete := _mounted()
	arrete.tick(0.016, lock, eye)
	assert_eq(arrete.state(), CitadelScript.State.LOCKED, "au verrou, l'etat le dit")
	assert_almost_eq(arrete.scroll_factor(), 0.0, 0.001, "et le survol est a l'ARRET, pas ralenti")

	for relay in arrete.relays():
		relay.target().hit_callback.call(TUNING.citadel_relay_health)
	arrete.core().target().hit_callback.call(TUNING.citadel_core_health)
	var horloge := 0.0
	while not arrete.is_cleared() and horloge < 20.0:
		arrete.tick(0.05, lock, eye)
		horloge += 0.05
	assert_almost_eq(arrete.scroll_factor(), 0.0, 0.001,
		"a l'instant ou la route s'ouvre, le survol n'a pas encore repris")
	for _i in int(TUNING.citadel_resume_time / 0.05) + 2:
		arrete.tick(0.05, lock, eye)
	assert_almost_eq(arrete.scroll_factor(), 1.0, 0.001,
		"et il retrouve sa vitesse apres %.1f s de reprise" % TUNING.citadel_resume_time)

## ⚠️ UN OUTIL DE VERIFICATION QUI GELE LE JEU EST PIRE QUE PAS D'OUTIL. `--cortege-from=4` pose
## le survol cent metres APRES la citadelle : le mur est derriere le joueur, sa hauteur de plan
## est negative, donc la condition d'arret est vraie — et sans garde, le verrou s'arme sur une
## porte qu'on ne peut plus ni voir ni tirer. Le survol ne repart jamais, sans une erreur.
func test_a_survey_that_starts_downstream_of_the_lock_is_not_frozen_by_it() -> void:
	var eye := _camera_eye()
	var citadel := _mounted()
	citadel.tick(0.016, _lock_travelled(eye) + TUNING.section_length, eye)
	assert_true(citadel.is_cleared(),
		"un depart en aval du verrou reputat la route franchie (etat %s)" % citadel.state_name())
	assert_almost_eq(citadel.scroll_factor(), 1.0, 0.001,
		"et le survol garde sa vitesse — il n'a jamais freine, il n'a pas a reprendre")
	var shapes := PlaneShapes.new()
	citadel.fill_solids(shapes)
	assert_eq(shapes.size(), 0, "et rien ne barre la route derriere le joueur")

## ⚠️ LES RELAIS DEVIENNENT TIRABLES A L'INSTANT PRECIS OU LE FREINAGE COMMENCE, et c'est ce qui
## rend ce cas atteignable des la premiere partie. Si l'approche du mur dependait de l'etat du
## combat, un relais abattu pendant ces cinq secondes ferait tomber la vitesse a zero d'un coup :
## le vaisseau s'arreterait net, deux unites trop haut, sur une porte que le joueur ne pourrait
## plus atteindre — et rien au journal ne le dirait. C'est la GEOMETRIE qui dit quand le mur est
## en place.
func test_a_relay_lost_during_the_brake_does_not_freeze_the_wall_too_high() -> void:
	var eye := _camera_eye()
	var lock := _lock_travelled(eye)
	var citadel := _mounted()
	# ⚠️ L'ARRIVEE DU MUR DOIT S'ANNONCER MEME SUR CE CHEMIN. C'est ce que la premiere ecriture
	# ratait : la machine passait de ONE_RELAY a SHIELD_DOWN sans jamais traverser `LOCKED`, donc
	# la ligne horodatee « VERROU » ne s'imprimait pas — et le critere « sous 45 s » ne repose sur
	# rien d'autre que ce journal. Toute lecture du lot 3 cablee sur l'arrivee du mur se serait
	# tue aussi. Le mur annonce donc son arrivee LUI-MEME, quoi que fasse le combat.
	var vu := [false]
	citadel.wall_locked.connect(func() -> void: vu[0] = true)
	var mi_freinage := lock - TUNING.citadel_brake_span * 0.5
	citadel.tick(0.016, mi_freinage, eye)
	citadel.relays()[0].target().hit_callback.call(TUNING.citadel_relay_health)
	citadel.tick(0.016, mi_freinage, eye)
	assert_eq(citadel.state(), CitadelScript.State.ONE_RELAY, "un relais est bien tombe")
	assert_true(citadel.scroll_factor() > 0.0,
		"et le survol continue d'avancer vers sa station (%.3f)" % citadel.scroll_factor())
	# Le mur atteint sa place malgre tout, et c'est la qu'il s'arrete.
	citadel.tick(0.016, lock, eye)
	assert_almost_eq(citadel.scroll_factor(), 0.0, 0.001,
		"puis il s'arrete exactement a sa station, comme si rien ne s'etait passe")
	assert_almost_eq(citadel.wall_plane_y(), TUNING.citadel_wall_plane_y, 0.05,
		"a la hauteur voulue (%.2f) et pas deux unites plus haut" % citadel.wall_plane_y())
	assert_true(vu[0], "le mur annonce son arrivee meme quand le combat a deja commence")
	assert_eq(citadel.state(), CitadelScript.State.ONE_RELAY,
		"et l'etat ne recule pas vers LOCKED : un relais abattu EST abattu")

## ⚠️ IL FREINE AVANT D'ARRIVER, ET C'EST CE QUI REND L'ARRET LISIBLE. Un survol qui s'arreterait
## net se lirait comme une image gelee, pas comme un vaisseau qui bloque la route.
func test_the_flyby_slows_before_it_stops() -> void:
	var eye := _camera_eye()
	var lock := _lock_travelled(eye)
	var citadel := _mounted()
	citadel.tick(0.016, lock - TUNING.citadel_brake_span * 0.5, eye)
	var facteur := citadel.scroll_factor()
	assert_true(facteur > 0.0 and facteur < 1.0,
		"a mi-freinage, le survol est ralenti sans etre arrete (%.3f)" % facteur)
	assert_eq(citadel.state(), CitadelScript.State.APPROACH,
		"et il n'est pas encore verrouille")


# =============================================================================
# 8. LES PIECES RENDENT LEUR CIBLE, ET LA REPRENNENT
# =============================================================================

## ⚠️ LE VA-ET-VIENT EST SYMETRIQUE, ET IL NE L'ETAIT PAS. La premiere ecriture eteignait la
## cible en sortant du plan SANS remettre le drapeau d'inscription : la piece qui rentrait a
## nouveau restait eteinte A VIE. Cible inscrite, tir qui la traverse, verrou INOUVRABLE — et
## pas une ligne au journal. La camera bouge (secousses, recadrages) : la frontiere est franchie
## dans les deux sens pour de vrai.
func test_a_part_that_leaves_the_plane_and_returns_is_shootable_again() -> void:
	var part := track(PartScript.make(PartScript.Role.RELAY, 100.0, Vector3.ONE, 1.0, 0.5, 10)) \
		as CitadelPart
	part.setup(null, null)
	var dedans := Vector2(0.0, 2.0)
	var dehors := Vector2(0.0, GameplayPlane.BOUNDS.end.y + 10.0)
	part.tick(Vector3.ZERO, dedans)
	assert_true(part.target().enabled, "dans le plan, elle est tirable")
	part.tick(Vector3.ZERO, dehors)
	assert_false(part.target().enabled, "hors du plan, elle ne l'est plus")
	part.tick(Vector3.ZERO, dedans)
	assert_true(part.target().enabled, "et elle le redevient en rentrant")
	part.target().hit_callback.call(100.0)
	assert_false(part.is_alive(), "un tir la tue bien apres son retour")

## ⚠️ ET UNE PIECE VIVANTE QUI PASSE SOUS LE PLAN REND SA CIBLE POUR DE BON. Le survol dure
## encore deux minutes apres le verrou, et il ne revient jamais en arriere : une cible qui
## resterait inscrite ferait payer son test a chaque balle de ce qui reste, pour une piece qu'on
## ne peut plus jamais toucher. C'est la passe monotone que la tourelle et le noeud d'epine
## tiennent deja.
func test_a_living_part_that_passes_below_the_plane_gives_its_target_back() -> void:
	var part := track(PartScript.make(PartScript.Role.CORE, 100.0, Vector3.ONE, 1.0, 0.5, 10)) \
		as CitadelPart
	part.setup(null, null)
	part.tick(Vector3.ZERO, Vector2(0.0, 2.0))
	assert_true(part.target().enabled, "elle est tirable dans le plan")
	part.tick(Vector3.ZERO, Vector2(0.0, GameplayPlane.BOUNDS.position.y - 10.0))
	assert_true(part.is_alive(), "elle est passee sans mourir")
	assert_false(part.target().enabled, "et elle a rendu sa cible")


# =============================================================================
# 9. LE VERROU FAIBLIT AVEC SON TRONCON
# =============================================================================

## ⚠️ LA RECOMPENSE AVAIT UN TROU EXACTEMENT LA OU ELLE SE SENT. Le verrou est sur le troncon 3,
## et c'est le noeud du troncon 2 qui l'eteint. Les vingt-et-une batteries de coque
## faiblissaient, annoncees au bandeau — et les quatre seules tourelles qui canardent le joueur
## pendant qu'il est IMMOBILE devant le mur gardaient toute leur vigueur.
func test_a_spine_node_weakens_the_guard_turrets_of_the_lock() -> void:
	var citadel := _mounted()
	var gardes := citadel.turrets()
	assert_true(gardes.size() >= 4, "le verrou porte bien ses tourelles (%d)" % gardes.size())
	for t in gardes:
		assert_false(t.is_weakened(), "elles naissent intactes")
	var cible := CortegeSpineNode.weakened_section(
		CitadelScript.section_of(TUNING) - 1, TUNING.section_count)
	assert_eq(cible, CitadelScript.section_of(TUNING),
		"le noeud du troncon precedent vise bien celui du verrou")
	citadel.weaken_section(cible)
	for t in gardes:
		assert_true(t.is_weakened(), "et elles faiblissent avec lui")

## Et un noeud lointain ne desarme pas le verrou.
func test_a_distant_spine_node_leaves_the_lock_alone() -> void:
	var citadel := _mounted()
	citadel.weaken_section(CitadelScript.section_of(TUNING) + 1)
	for t in citadel.turrets():
		assert_false(t.is_weakened(),
			"un noeud qui eteint un autre troncon ne touche pas aux tourelles du verrou")
