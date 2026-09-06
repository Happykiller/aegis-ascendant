extends "res://tests/test_case.gd"
## La phase finale du niveau 2 : l'arrachement des moteurs.
##
## ⚠️ CE BANC EXISTE PARCE QUE LA PHASE EST INJOUABLE EN TEST. Elle arrive au terme de quatre
## minutes de survol, elle demande de detruire dix verrous a la main, et le pilote de
## demonstration tire droit devant : aucune partie automatisee ne la traverse. Tout ce qui
## compte ici est donc ecrit en fonctions PURES — l'etat d'un moteur, sa trajectoire de depart,
## l'ouverture du central — et c'est la seule raison pour laquelle elles sont statiques.

const TUNING: CortegeSternTuning = preload("res://resources/levels/long_cortege_stern.tres")
const EngineScript := preload("res://scripts/gameplay/cortege_engine.gd")
const SternScript := preload("res://scripts/gameplay/cortege_stern.gd")

# --- Le reglage livre -----------------------------------------------------------

func test_the_shipped_tuning_is_valid() -> void:
	var errors := TUNING.validate()
	assert_eq(errors.size(), 0, "le reglage livre passe ses invariants : %s"
		% ", ".join(errors))

## ⚠️ LES DEUX BINAIRES LIVRES NE TIENNENT PAS SOUS LE PLAFOND DE VOL A PLEINE ECHELLE, et ce
## test le prouve plutot que de le raconter. Moteur 5,49 m + berceau 4,64 m = 10,13 m empiles ;
## le plafond de jeu est a -2,40 et la quille a -12,60. C'est la decision D5 du plan.
func test_a_full_scale_engine_would_cross_the_flight_plane() -> void:
	var brut: CortegeSternTuning = TUNING.duplicate()
	brut.asset_scale = 1.0
	brut.central_scale = 1.0
	assert_true(brut.stack_top_y(false) > CortegeFlyby.GAMEPLAY_CEILING_Y,
		"a pleine echelle le groupe culmine a %.2f pour un plafond a %.2f"
			% [brut.stack_top_y(false), CortegeFlyby.GAMEPLAY_CEILING_Y])
	var dits := brut.validate()
	var trouve := false
	for d in dits:
		if d.contains("plafond de vol"):
			trouve = true
	assert_true(trouve, "et l'invariant le DIT, au lieu de laisser une capture le decouvrir : %s"
		% ", ".join(dits))

## ⚠️ ET « COLLER LES TROIS GROUPES » N'AURAIT PAS SUFFI. Trois berceaux livres JOINTIFS font
## 33,6 m pour un joueur qui n'en couvre que 28 : la reduction d'echelle n'etait pas une option
## de confort, c'etait la seule issue. Ce test garde le raisonnement, pas seulement le resultat.
func test_three_full_scale_cradles_do_not_fit_the_players_reach() -> void:
	var largeur := 3.0 * TUNING.cradle_size.x
	assert_true(largeur > GameplayPlane.BOUNDS.size.x,
		"trois berceaux jointifs font %.2f m pour une zone de vol large de %.2f"
			% [largeur, GameplayPlane.BOUNDS.size.x])
	assert_true(TUNING.half_span() <= GameplayPlane.BOUNDS.end.x,
		"reduits, ils tiennent : bord a |x| = %.2f pour une portee de %.2f"
			% [TUNING.half_span(), GameplayPlane.BOUNDS.end.x])

## ⚠️ LE SILENCE FINAL PORTE L'AVEU DE LYRA (decision D3). Le raccourcir couperait la replique
## la plus importante du niveau, et rien a l'ecran ne dirait qu'il manque quelque chose.
func test_the_final_silence_holds_lyras_confession() -> void:
	var script: DialogueScript = load("res://resources/dialogue/lyra_cortege.tres")
	var aveu := script.find(&"survey_end")
	assert_true(aveu != null, "l'aveu est toujours dans le script du niveau")
	assert_true(TUNING.silence_time >= aveu.hold,
		"le silence dure %.2f s pour une replique qui en tient %.2f a l'ecran"
			% [TUNING.silence_time, aveu.hold])
	var court: CortegeSternTuning = TUNING.duplicate()
	court.silence_time = 3.0
	assert_true(_says(court, "aveu de Lyra"),
		"et un silence trop court est REFUSE, pas seulement regrette")

func _says(tuning: CortegeSternTuning, fragment: String) -> bool:
	for e in tuning.validate():
		if e.contains(fragment):
			return true
	return false

func test_an_out_of_order_detach_sequence_is_refused() -> void:
	var tuning: CortegeSternTuning = TUNING.duplicate()
	tuning.detach_burst_at = 0.1   # avant le tremblement
	assert_true(_says(tuning, "l'envers"),
		"deux instants inverses feraient partir le moteur avant qu'il ne tremble")

func test_a_central_engine_that_bites_its_neighbour_is_refused() -> void:
	var tuning: CortegeSternTuning = TUNING.duplicate()
	tuning.central_scale = 1.8
	assert_true(_says(tuning, "mord celui du bord"),
		"deux berceaux qui s'interpenetrent melangeraient les ancrages des deux moteurs")

func test_anchors_out_of_reach_are_refused() -> void:
	var tuning: CortegeSternTuning = TUNING.duplicate()
	tuning.engine_spacing = 13.0
	assert_true(_says(tuning, "hors de port"),
		"c'est le defaut des tourelles de coque, et il serait pire ici : l'ancrage est la SEULE cible")

# --- La machine a etats ---------------------------------------------------------

## ⚠️ ELLE PREND LE TOTAL, ET NON TROIS. Le moteur central porte quatre ancrages : une regle
## ecrite en dur pour trois lui donnerait `DAMAGED_2` des le deuxieme, puis plus rien jusqu'au
## quatrieme — une progression muette au milieu, que rien ne signalerait.
func test_the_state_of_an_engine_is_deduced_from_its_anchors() -> void:
	assert_eq(EngineScript.state_for(0, 3, false), EngineScript.State.ACTIVE,
		"intact tant qu'aucun verrou n'est tombe")
	assert_eq(EngineScript.state_for(1, 3, false), EngineScript.State.DAMAGED_1,
		"le premier verrou ouvre le premier palier")
	assert_eq(EngineScript.state_for(2, 3, false), EngineScript.State.DAMAGED_2,
		"le deuxieme ouvre le second")
	assert_eq(EngineScript.state_for(3, 3, false), EngineScript.State.DETACHED,
		"le dernier le detache")
	# Le central, a quatre : deux paliers pleins, pas un trou au milieu.
	assert_eq(EngineScript.state_for(1, 4, false), EngineScript.State.DAMAGED_1,
		"un verrou sur quatre : premier palier")
	assert_eq(EngineScript.state_for(2, 4, false), EngineScript.State.DAMAGED_2,
		"a mi-chemin le central est deja au second palier — sans quoi deux verrous ne diraient rien")
	assert_eq(EngineScript.state_for(3, 4, false), EngineScript.State.DAMAGED_2,
		"trois sur quatre : toujours le second, il reste une attache")
	assert_eq(EngineScript.state_for(2, 4, true), EngineScript.State.DETACHING,
		"la sequence d'arrachement prime sur le compte")

## ⚠️ RIEN NE BOUGE AVANT `detach_leave_at`, ET C'EST LA MOITIE DE LA LECTURE. Entre le dernier
## verrou et le depart, le moteur TREMBLE et ses conduites eclatent. S'il glissait deja, le
## joueur lirait « il tombe » au lieu de « il s'arrache ».
func test_a_detaching_engine_does_not_move_before_it_leaves() -> void:
	var leave := TUNING.detach_leave_at
	for t in [0.0, 0.2, 0.5, 0.8, leave]:
		assert_true(EngineScript.drift_offset(t, leave, TUNING.drift_speed, 1.0) == Vector3.ZERO,
			"a t = %.2f s le moteur est encore dans son berceau" % t)
	var apres := EngineScript.drift_offset(leave + 1.0, leave, TUNING.drift_speed, 1.0)
	assert_true(apres.z < 0.0, "puis il part vers le HAUT de l'ecran — par ou sortent ses flammes")
	assert_true(apres.x > 0.0, "et vers son bord : tribord derive a tribord")

## ⚠️ IL NE PEUT PAS PERCUTER LE JOUEUR (spec §11). Une trajectoire ecrite le garantit ; une
## simulation ne le garantirait qu'en moyenne. Ce test echantillonne les quatre secondes.
func test_a_detached_engine_never_comes_back_into_the_play_area() -> void:
	for side in [-1.0, 0.0, 1.0]:
		var depart := Vector2(TUNING.slot_x(side), TUNING.hold_plane_y)
		var t := TUNING.detach_leave_at
		while t <= TUNING.detach_gone_at:
			var offset := EngineScript.drift_offset(t, TUNING.detach_leave_at,
				TUNING.drift_speed, side)
			# `offset.z` est en Z monde : le plan compte -z vers le haut.
			var ici := Vector2(depart.x + offset.x, depart.y - offset.z)
			assert_true(ici.y >= depart.y,
				"a t = %.2f s le moteur %+.0f est a y = %.2f — il redescendrait vers le joueur"
					% [t, side, ici.y])
			t += 0.1

func test_the_tilt_stops_once_the_engine_has_left() -> void:
	var plein := deg_to_rad(TUNING.detach_tilt_degrees)
	assert_almost_eq(EngineScript.tilt_at(0.0, TUNING.detach_tilt_at, TUNING.detach_leave_at,
		TUNING.detach_tilt_degrees), 0.0, 0.001, "il ne bascule pas avant son heure")
	assert_almost_eq(EngineScript.tilt_at(TUNING.detach_leave_at, TUNING.detach_tilt_at,
		TUNING.detach_leave_at, TUNING.detach_tilt_degrees), plein, 0.001,
		"il a fini de basculer quand il quitte le berceau")
	assert_almost_eq(EngineScript.tilt_at(9.0, TUNING.detach_tilt_at, TUNING.detach_leave_at,
		TUNING.detach_tilt_degrees), plein, 0.001,
		"et il garde son angle : une bascule qui continuerait le ferait tourner sur lui-meme")

# --- L'ordre de la sequence -----------------------------------------------------

## ⚠️ LE CENTRAL S'OUVRE SUR DEUX MOTEURS PARTIS, PAS SUR DEUX MOTEURS ABIMES. Le compter sur
## l'endommagement l'ouvrirait pendant que les lateraux tirent encore, et la redirection
## d'energie que la spec raconte (§14) n'aurait pas eu lieu.
func test_the_central_engine_opens_only_when_both_sides_are_gone() -> void:
	assert_false(SternScript.core_is_exposed(0), "aucun lateral parti : il reste verrouille")
	assert_false(SternScript.core_is_exposed(1), "un seul : toujours verrouille")
	assert_true(SternScript.core_is_exposed(2), "les deux : l'energie converge, il s'ouvre")

## ⚠️ LA POUPE ENTRE DANS LE CADRE, ELLE N'Y APPARAIT PAS — meme regle que les vagues d'ennemis,
## et elle vaut d'autant plus pour une masse qui remplit l'ecran.
func test_the_stern_arrives_from_outside_the_frame() -> void:
	var debut := SternScript.arrival_y(0.0, TUNING.hold_plane_y, TUNING.arrival_rise,
		TUNING.arrival_time)
	assert_true(debut > 12.28,
		"a t = 0 la poupe est a y = %.2f, au-dela du bord haut de l'ecran (12,28)" % debut)
	var fin := SternScript.arrival_y(TUNING.arrival_time, TUNING.hold_plane_y,
		TUNING.arrival_rise, TUNING.arrival_time)
	assert_almost_eq(fin, TUNING.hold_plane_y, 0.001, "et elle s'arrete a sa station")
	# Elle DESCEND, sans repartir : une entree qui rebondirait se lirait comme un defaut.
	var precedent := debut
	var t := 0.0
	while t <= TUNING.arrival_time:
		var y := SternScript.arrival_y(t, TUNING.hold_plane_y, TUNING.arrival_rise,
			TUNING.arrival_time)
		assert_true(y <= precedent + 0.0001, "elle ne remonte jamais (t = %.2f)" % t)
		precedent = y
		t += 0.1

# --- Ce que le moteur NE fait pas ------------------------------------------------

## ⚠️ LE MOTEUR NE PREND AUCUN DEGAT — PAS « PEU », AUCUN. C'est le critere d'acceptation n°3 de
## la spec, et c'est ce qui distingue la phase d'un boss. La regle n'est pas tenue par une
## condition qu'on pourrait oublier : elle est tenue par une ABSENCE, et ce test garde l'absence.
func test_an_engine_is_not_a_target_at_all() -> void:
	var engine := track(EngineScript.make(TUNING, 1.0)) as CortegeEngine
	assert_false(engine.has_method("target"),
		"un moteur n'expose pas de cible : il n'est pas tirable, il est PORTE")
	assert_eq(engine.lost_anchors(), 0, "et il nait intact")
	assert_eq(engine.state(), EngineScript.State.ACTIVE, "et actif")
