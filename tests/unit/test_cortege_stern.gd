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

# --- Les quatre etats d'un ancrage ----------------------------------------------
#
## ⚠️ LE QUATRIEME N'EST PAS DANS LA PLANCHE, ET C'EST LE PLUS IMPORTANT. `asset3` dessine
## *Intact*, *Endommage* et *Ouvert/rompu* : trois etats de la PIECE. Le quatrieme —
## **verrouille** — appartient a la SEQUENCE : les verrous du moteur central se voient bien
## avant d'etre attaquables (spec §14). Sans etat visuel propre, le joueur les prendrait pour
## des cibles qui n'encaissent rien, c'est-a-dire pour un bug.
const AnchorScript := preload("res://scripts/gameplay/cortege_anchor.gd")

func test_an_anchor_reads_its_four_states() -> void:
	var seuil := TUNING.anchor_damaged_at
	assert_eq(AnchorScript.look_for(true, true, 1.0, seuil), AnchorScript.Look.INTACT,
		"vivant, ouvert, entier")
	assert_eq(AnchorScript.look_for(true, true, seuil - 0.01, seuil), AnchorScript.Look.DAMAGED,
		"sous le seuil, ses plaques s'ouvrent")
	assert_eq(AnchorScript.look_for(false, false, 0.0, seuil), AnchorScript.Look.BROKEN,
		"mort : la carcasse reste, et c'est la preuve")
	# ⚠️ L'ORDRE DES TESTS COMPTE, et ces deux lignes le gardent.
	assert_eq(AnchorScript.look_for(true, false, 1.0, seuil), AnchorScript.Look.LOCKED,
		"a pleine vie mais verrouille : ce qu'il faut savoir de lui n'est pas sa sante")
	assert_eq(AnchorScript.look_for(false, true, 0.5, seuil), AnchorScript.Look.BROKEN,
		"mort dans la trame ou il etait encore ouvert : il reste rompu")

## ⚠️ LE VERROUILLE CHANGE DE TEINTE, PAS SEULEMENT D'INTENSITE. Un magenta assombri se lirait
## comme « un ancrage deja travaille » — donc comme une cible qu'on a entamee, alors qu'elle
## n'a jamais encaisse. Meme regle que l'ambre de signalisation (`ADR-0043`).
func test_a_locked_anchor_is_not_a_dim_magenta() -> void:
	var froid: Color = AnchorScript.LOCKED_TINT
	var chaud: Color = AnchorScript.TINT
	assert_true(froid.b > froid.r,
		"le verrouille tire vers le bleu (%.2f de bleu pour %.2f de rouge)" % [froid.b, froid.r])
	assert_true(chaud.r > chaud.b,
		"l'actif tire vers le magenta (%.2f de rouge pour %.2f de bleu)" % [chaud.r, chaud.b])
	assert_true(absf(froid.h - chaud.h) > 0.2,
		"et les deux teintes se distinguent d'un coup d'oeil, pas seulement a la mesure")

## ⚠️ L'ENDOMMAGE BRILLE PLUS FORT QUE L'INTACT, ET C'EST CONTRE-INTUITIF. La planche le dessine
## OUVERT, coeur a nu : un etat qui s'assombrirait a mesure qu'on le travaille se lirait comme
## un verrou en train de s'eteindre, c'est-a-dire deja rompu.
func test_a_damaged_anchor_burns_brighter_than_an_intact_one() -> void:
	assert_true(AnchorScript.DAMAGED_GLOW > AnchorScript.INTACT_GLOW,
		"%.2f contre %.2f" % [AnchorScript.DAMAGED_GLOW, AnchorScript.INTACT_GLOW])
	assert_true(AnchorScript.BROKEN_GLOW < AnchorScript.LOCKED_GLOW,
		"et le rompu est le plus sombre des quatre — plus sombre meme qu'un verrou ferme")

## ⚠️ SANS FLASH, LE JOUEUR NE SAIT PAS QU'IL TOUCHE. L'ancrage est la SEULE cible de la phase :
## deux secondes de tir sans retour se lisent comme « cette piece est invulnerable », et le
## joueur va chercher ailleurs — sur le moteur, qui n'encaisse rien.
func test_a_hit_is_acknowledged() -> void:
	var anchor := track(AnchorScript.make(TUNING.anchor_health, TUNING.anchor_radius, 0)) as CortegeAnchor
	anchor.damaged_at = TUNING.anchor_damaged_at
	anchor.set_vulnerable(true)
	assert_eq(anchor.look(), AnchorScript.Look.INTACT, "il nait intact une fois ouvert")
	anchor.target().hit_callback.call(TUNING.anchor_health * 0.6)
	assert_eq(anchor.look(), AnchorScript.Look.DAMAGED,
		"un coup qui passe le seuil ouvre ses plaques")
	assert_true(anchor.health_ratio() < TUNING.anchor_damaged_at, "et sa vie a baisse")

## ⚠️ UN VERROU FERME ENCAISSE ZERO. Pas « peu » : zero. C'est ce qui tient la sequence du
## central, et une balle deja resolue dans la trame courante trouverait encore la cible si l'on
## se contentait de la desinscrire.
func test_a_locked_anchor_takes_nothing() -> void:
	var anchor := track(AnchorScript.make(TUNING.anchor_health, TUNING.anchor_radius, 0)) as CortegeAnchor
	anchor.set_vulnerable(false)
	anchor.target().hit_callback.call(TUNING.anchor_health * 10.0)
	assert_true(anchor.is_alive(), "il est toujours la")
	assert_almost_eq(anchor.health_ratio(), 1.0, 0.001, "et il n'a rien perdu")
	assert_eq(anchor.look(), AnchorScript.Look.LOCKED, "et il le dit")

func test_a_threshold_that_erases_a_state_is_refused() -> void:
	for valeur in [0.0, 1.0]:
		var tuning: CortegeSternTuning = TUNING.duplicate()
		tuning.anchor_damaged_at = valeur
		assert_true(_says(tuning, "ENDOMMAG"),
			"un seuil a %.2f supprimerait un etat entier, sans rien casser" % valeur)

## ⚠️ LA ZONE DE TOUCHE NE DOIT PAS ETRE PLUS PETITE QUE LA PIECE. Elle vient de la Resource
## (`ADR-0034`), ce qui est juste — mais une hitbox en retrait de la silhouette donne le pire
## retour possible sur la SEULE cible de la phase : le tir passe visiblement sur le verrou, et
## rien ne se produit. Le joueur en conclut qu'il ne faut pas tirer la, et il va chercher sur le
## moteur, qui n'encaisse rien non plus.
func test_the_hitbox_is_never_smaller_than_what_is_drawn() -> void:
	var demi := TUNING.anchor_size.x * TUNING.scale_of(false) * 0.5
	assert_true(TUNING.anchor_radius >= demi,
		"rayon %.2f pour une demi-largeur de %.2f" % [TUNING.anchor_radius, demi])
	var maigre: CortegeSternTuning = TUNING.duplicate()
	maigre.anchor_radius = 0.2
	assert_true(_says(maigre, "passerait à travers"),
		"et une hitbox rabougrie est REFUSEE, pas seulement regrettee")

# --- LOT 3 : l'arrachement ------------------------------------------------------

## ⚠️ IL TREMBLE, IL NE GLISSE PAS. Le tremblement dit « ca cede » ; un glissement dirait « ca
## tombe », et la piece ne serait plus arrachee, elle serait lachee. Il MONTE aussi : une
## vibration d'intensite fixe se lit comme un moteur qui ronronne, pas comme une tenue qui se
## degrade seconde apres seconde.
func test_the_engine_shakes_before_it_leaves_and_the_shake_grows() -> void:
	var a := TUNING.detach_shake_amplitude
	var hz := TUNING.detach_shake_hz
	var de := TUNING.detach_shake_at
	var vers := TUNING.detach_leave_at
	assert_true(EngineScript.shake_at(de - 0.01, de, vers, a, hz) == Vector3.ZERO,
		"rien avant l'heure du tremblement")
	assert_true(EngineScript.shake_at(vers + 0.01, de, vers, a, hz) == Vector3.ZERO,
		"et rien apres le depart : ce qui bouge alors, c'est la derive")
	# L'enveloppe monte : on compare deux maxima sur deux fenetres successives.
	var tot := 0.0
	var fin := 0.0
	var t := de
	while t < vers:
		var m: float = EngineScript.shake_at(t, de, vers, a, hz).length()
		assert_true(m <= a * 1.2, "il ne depasse jamais son amplitude (%.3f a t = %.2f)" % [m, t])
		if t < (de + vers) * 0.5:
			tot = maxf(tot, m)
		else:
			fin = maxf(fin, m)
		t += 0.01
	assert_true(fin > tot,
		"la seconde moitie tremble plus fort que la premiere (%.3f contre %.3f)" % [fin, tot])

## ⚠️ ET IL RESTE DANS SON BERCEAU PENDANT QU'IL TREMBLE. Un tremblement qui l'en sortirait
## ferait lire « il est deja parti », et la bascule qui suit n'aurait plus rien a annoncer.
func test_the_shake_never_lifts_the_engine_out_of_its_cradle() -> void:
	var creux := TUNING.cradle_size.y * TUNING.scale_of(false) * 0.25
	assert_true(TUNING.detach_shake_amplitude <= creux,
		"%.2f m de tremblement pour %.2f m de debattement" % [TUNING.detach_shake_amplitude, creux])
	var large: CortegeSternTuning = TUNING.duplicate()
	large.detach_shake_amplitude = 5.0
	assert_true(_says(large, "en sortirait avant de s'arracher"),
		"et un tremblement demesure est REFUSE")

## ⚠️ LA POUSSEE NE SE COUPE PAS AU DEPART, ELLE S'ETEINT EN DERIVANT (spec §9 et §16). Couper
## au moment du depart ferait lire une panne ; ce qu'il faut lire, c'est une machine qui
## fonctionne encore et que plus rien ne retient.
func test_the_thrust_dies_while_drifting_not_when_it_leaves() -> void:
	var vers := TUNING.detach_leave_at
	var fini := TUNING.detach_gone_at
	assert_almost_eq(EngineScript.thrust_at(0.0, vers, fini), 1.0, 0.001,
		"a plein regime tant qu'il tient")
	assert_almost_eq(EngineScript.thrust_at(vers, vers, fini), 1.0, 0.001,
		"et ENCORE a plein regime a l'instant ou il quitte son berceau")
	var milieu := EngineScript.thrust_at((vers + fini) * 0.5, vers, fini)
	assert_true(milieu > 0.2 and milieu < 0.8,
		"a mi-derive il crache encore, mais moins (%.2f)" % milieu)
	assert_almost_eq(EngineScript.thrust_at(fini, vers, fini), 0.0, 0.001,
		"et il s'est tu quand il sort du cadre")
	assert_almost_eq(EngineScript.thrust_at(fini + 9.0, vers, fini), 0.0, 0.001,
		"sans jamais repartir")

## ⚠️ LA SEQUENCE DE LA SPEC §9 EST UNE SUITE D'INSTANTS, ET CHACUN DOIT ETRE SEUL A SON HEURE.
## Ce test lit la phase a chaque etape et verifie que ce qui doit avoir commence a commence, et
## que ce qui ne doit pas encore bouger ne bouge pas. C'est le seul endroit ou la chronologie
## complete est verifiee d'un bloc.
func test_the_detach_sequence_plays_in_the_order_the_spec_writes() -> void:
	var vers := TUNING.detach_leave_at
	# T+0 : rien.
	assert_true(EngineScript.shake_at(0.0, TUNING.detach_shake_at, vers,
		TUNING.detach_shake_amplitude, TUNING.detach_shake_hz) == Vector3.ZERO,
		"T+0 : le verrou vient de ceder, la piece est encore intacte")
	assert_true(EngineScript.drift_offset(0.0, vers, TUNING.drift_speed, 1.0) == Vector3.ZERO,
		"et il n'a pas commence a partir")
	# T+0,2 : il tremble, il ne bouge pas.
	var secousse := EngineScript.shake_at(TUNING.detach_shake_at + 0.05,
		TUNING.detach_shake_at, vers, TUNING.detach_shake_amplitude, TUNING.detach_shake_hz)
	assert_true(secousse.length() > 0.0, "T+0,2 : il tremble")
	assert_true(EngineScript.drift_offset(TUNING.detach_shake_at + 0.05, vers,
		TUNING.drift_speed, 1.0) == Vector3.ZERO, "mais il n'a pas bouge d'un centimetre")
	# T+0,8 : il bascule, il ne part pas.
	var angle := EngineScript.tilt_at(TUNING.detach_tilt_at + 0.1, TUNING.detach_tilt_at,
		vers, TUNING.detach_tilt_degrees)
	assert_true(angle > 0.0, "T+0,8 : il bascule")
	assert_true(EngineScript.drift_offset(TUNING.detach_tilt_at + 0.1, vers,
		TUNING.drift_speed, 1.0) == Vector3.ZERO, "et il est toujours dans son berceau")
	# T+1,2 : il part, et sa bascule est finie.
	assert_almost_eq(EngineScript.tilt_at(vers, TUNING.detach_tilt_at, vers,
		TUNING.detach_tilt_degrees), deg_to_rad(TUNING.detach_tilt_degrees), 0.001,
		"T+1,2 : il a fini de basculer quand il part")

## ⚠️ LES TROIS PARTENT DIFFEREMMENT, ET C'EST CE QUI DONNE L'IMPRESSION D'UNE VRAIE PHYSIQUE
## SANS EN SIMULER UNE (spec §10). Un test qui ne verifierait qu'un moteur laisserait passer
## trois departs identiques — la faute exacte que la spec prend la peine d'ecarter.
func test_the_three_engines_leave_in_three_different_directions() -> void:
	var t := TUNING.detach_gone_at
	var gauche := EngineScript.drift_offset(t, TUNING.detach_leave_at, TUNING.drift_speed, -1.0)
	var centre := EngineScript.drift_offset(t, TUNING.detach_leave_at, TUNING.drift_speed, 0.0)
	var droite := EngineScript.drift_offset(t, TUNING.detach_leave_at, TUNING.drift_speed, 1.0)
	assert_true(gauche.x < 0.0, "babord derive a babord")
	assert_true(droite.x > 0.0, "tribord derive a tribord")
	assert_almost_eq(centre.x, 0.0, 0.001, "le central part droit vers le haut")
	assert_true(gauche.z < 0.0 and centre.z < 0.0 and droite.z < 0.0,
		"les trois montent : ils partent par ou sortent leurs flammes")
	# ⚠️ ET LE CENTRAL N'EST PAS UN LATERAL SANS COTE : sa rotation propre le distingue.
	assert_true(TUNING.central_spin_deg > 0.0,
		"le central tourne sur lui-meme — sans quoi son depart serait le seul a ne rien raconter")

# --- LOT 4 : la flamme et la poussee --------------------------------------------

const FlameScript := preload("res://scripts/fx/cortege_flame.gd")

## ⚠️ LA SPEC CHIFFRE LA VARIATION — longueur ±10 a 15 %, largeur ±5 a 10 % — et ces bornes
## valent mieux qu'un « ca bouge un peu ». Au-dela, la flamme bat comme un coeur et attire
## l'oeil hors de la cible ; en deca, elle est morte. Ce test echantillonne dix secondes.
func test_a_healthy_flame_breathes_within_the_specs_bounds() -> void:
	var l_min := 9.0
	var l_max := 0.0
	var w_min := 9.0
	var w_max := 0.0
	var t := 0.0
	while t < 10.0:
		var f: Vector2 = FlameScript.shape_at(t, 0.4, FlameScript.Regime.STEADY)
		l_min = minf(l_min, f.x); l_max = maxf(l_max, f.x)
		w_min = minf(w_min, f.y); w_max = maxf(w_max, f.y)
		t += 0.01
	assert_true(l_max <= 1.16 and l_min >= 0.84,
		"longueur entre %.3f et %.3f — la spec borne a ±15 %%" % [l_min, l_max])
	assert_true(w_max <= 1.11 and w_min >= 0.89,
		"largeur entre %.3f et %.3f — la spec borne a ±10 %%" % [w_min, w_max])
	# ⚠️ ET ELLE BOUGE VRAIMENT : une flamme constante passerait les deux bornes ci-dessus.
	assert_true(l_max - l_min > 0.10, "elle respire pour de bon (%.3f d'amplitude)" % (l_max - l_min))

## ⚠️ ABIMEE, ELLE N'EST PAS PLUS PETITE : ELLE EST PLUS IRREGULIERE. Une flamme qui retrecit se
## lirait comme un moteur qu'on eteint proprement ; ce qu'il faut lire, c'est une machine qui
## perd sa tenue.
func test_a_damaged_flame_gets_erratic_not_small() -> void:
	var regimes: Array = [FlameScript.Regime.STEADY, FlameScript.Regime.ROUGH,
		FlameScript.Regime.SPUTTER]
	var precedent := 0.0
	var moyennes: Array[float] = []
	for r in regimes:
		var lo := 9.0
		var hi := 0.0
		var somme := 0.0
		var n := 0
		var t := 0.0
		while t < 10.0:
			var f: Vector2 = FlameScript.shape_at(t, 0.4, r)
			lo = minf(lo, f.x); hi = maxf(hi, f.x); somme += f.x; n += 1
			t += 0.01
		var amplitude := hi - lo
		assert_true(amplitude > precedent,
			"chaque palier est plus irregulier que le precedent (%.3f apres %.3f)"
				% [amplitude, precedent])
		precedent = amplitude
		moyennes.append(somme / float(n))
	assert_true(moyennes[1] > moyennes[0] * 0.85,
		"et la premiere avarie ne RETRECIT pas la flamme (%.2f contre %.2f)"
			% [moyennes[1], moyennes[0]])

## ⚠️ « POUSSEE INTERMITTENTE » (spec §8) VEUT DIRE QU'ELLE S'INTERROMPT. Une simple variation
## d'amplitude, si grande soit-elle, ne se lit jamais comme une coupure : il faut un seuil.
func test_the_sputtering_flame_actually_cuts_out() -> void:
	var creux := 0
	var t := 0.0
	while t < 10.0:
		if FlameScript.shape_at(t, 0.4, FlameScript.Regime.SPUTTER).x < 0.45:
			creux += 1
		t += 0.01
	assert_true(creux > 20, "elle s'interrompt vraiment (%d echantillons sous 45 %%)" % creux)
	var jamais := 0
	t = 0.0
	while t < 10.0:
		if FlameScript.shape_at(t, 0.4, FlameScript.Regime.STEADY).x < 0.45:
			jamais += 1
		t += 0.01
	assert_eq(jamais, 0, "alors qu'une flamme saine ne hoquette jamais")

func test_the_flame_regime_follows_the_engine_state() -> void:
	assert_eq(FlameScript.regime_for(EngineScript.State.ACTIVE, false),
		FlameScript.Regime.STEADY, "intact : elle tient")
	assert_eq(FlameScript.regime_for(EngineScript.State.DAMAGED_1, false),
		FlameScript.Regime.ROUGH, "un verrou perdu : elle devient irreguliere")
	assert_eq(FlameScript.regime_for(EngineScript.State.DAMAGED_2, false),
		FlameScript.Regime.SPUTTER, "deux : elle hoquette")
	assert_eq(FlameScript.regime_for(EngineScript.State.ACTIVE, true),
		FlameScript.Regime.DYING, "et l'arrachement prime sur le compte")

## ⚠️ L'ORDRE EST CALME → CHARGE → SOUFFLE, ET LA CHARGE EST DEVANT. Un preavis qui suivrait le
## souffle ne previendrait rien — evident ecrit ainsi, et c'est pourtant l'inversion la plus
## facile a commettre en calculant des restes de modulo.
func test_the_surge_warns_before_it_burns() -> void:
	var p := TUNING.surge_period
	var w := TUNING.surge_warning
	var b := TUNING.surge_blast
	assert_eq(EngineScript.surge_at(0.0, p, w, b, TUNING.surge_vent, false),
		EngineScript.Surge.CALM, "le cycle commence au calme")
	assert_eq(EngineScript.surge_at(p - w - b + 0.01, p, w, b, TUNING.surge_vent, false),
		EngineScript.Surge.CHARGE, "puis il charge")
	assert_eq(EngineScript.surge_at(p - b + 0.01, p, w, b, TUNING.surge_vent, false),
		EngineScript.Surge.BLAST, "puis il souffle")
	assert_eq(EngineScript.surge_at(p + 0.01, p, w, b, TUNING.surge_vent, false),
		EngineScript.Surge.CALM, "et sans extinction, il repart au calme")
	# ⚠️ ET LE PREAVIS PRECEDE TOUJOURS LE SOUFFLE, sur tout un cycle.
	var vu_charge := false
	var t := 0.0
	while t < p:
		var phase: int = EngineScript.surge_at(t, p, w, b, TUNING.surge_vent, false)
		if phase == EngineScript.Surge.CHARGE:
			vu_charge = true
		if phase == EngineScript.Surge.BLAST:
			assert_true(vu_charge, "aucun souffle n'arrive sans preavis (t = %.2f)" % t)
		t += 0.01

## ⚠️ L'EXTINCTION N'APPARTIENT QU'AU CENTRAL, ET SEULEMENT APRES LES DEUX LATERAUX (spec §15).
## Elle donne « une fenetre tres confortable pour attaquer » — c'est ce qui empeche la derniere
## etape de la phase de devenir une attente.
func test_only_the_central_engine_vents_and_only_at_the_end() -> void:
	var p := TUNING.surge_period
	var v := TUNING.surge_vent
	var vus := {}
	var t := 0.0
	while t < (p + v) * 2.0:
		vus[EngineScript.surge_at(t, p, TUNING.surge_warning, TUNING.surge_blast, v, true)] = true
		t += 0.01
	assert_true(vus.has(EngineScript.Surge.VENT), "avec extinction, elle arrive")
	vus.clear()
	t = 0.0
	while t < p * 3.0:
		vus[EngineScript.surge_at(t, p, TUNING.surge_warning, TUNING.surge_blast, v, false)] = true
		t += 0.01
	assert_false(vus.has(EngineScript.Surge.VENT), "sans extinction, jamais")

## ⚠️ TROIS COLONNES QUI SE TOUCHERAIENT NE LAISSERAIENT NULLE PART OU ALLER, et la poussee
## cesserait d'etre une menace pour devenir une taxe. La premiere version prenait la largeur de
## la NACELLE (7,14 m) au lieu de celle du panache (2,4) : il restait 1,94 m entre deux
## colonnes, moins que l'envergure du chasseur. L'invariant l'a refuse avant toute capture.
func test_there_is_always_a_lane_between_two_thrust_columns() -> void:
	var couloir := TUNING.engine_spacing - TUNING.danger_half_width(false) \
		- TUNING.danger_half_width(true)
	assert_true(couloir >= 2.5,
		"%.2f m entre deux colonnes, pour un chasseur qui en fait 1,75 d'envergure" % couloir)
	var large: CortegeSternTuning = TUNING.duplicate()
	large.danger_spread = 4.0
	assert_true(_says(large, "nulle part où s'écarter"),
		"et des colonnes qui se toucheraient sont REFUSEES")

## ⚠️ SEULE L'ABSCISSE COMPTE. Une borne en `y` creerait un endroit sur juste sous le moteur —
## exactement la ou le joueur doit se poster pour travailler ses verrous, donc exactement la ou
## la poussee doit le chasser.
func test_the_thrust_column_catches_the_player_at_any_height() -> void:
	var demi := TUNING.danger_half_width(false)
	var x := TUNING.slot_x(1.0)
	assert_true(SternScript.in_thrust_column(x, x, demi), "sous l'axe, il brule")
	assert_true(SternScript.in_thrust_column(x + demi - 0.01, x, demi), "au bord aussi")
	assert_false(SternScript.in_thrust_column(x + demi + 0.5, x, demi), "a cote, il est au sec")
	assert_false(SternScript.in_thrust_column(0.0, x, demi),
		"et le couloir central reste sur pendant qu'un lateral souffle")

func test_the_warning_window_matches_what_the_spec_asks() -> void:
	assert_true(TUNING.surge_warning >= 0.30 and TUNING.surge_warning <= 0.50,
		"%.2f s de preavis : la spec en demande 0,30 a 0,50" % TUNING.surge_warning)
	for valeur in [0.05, 1.20]:
		var tuning: CortegeSternTuning = TUNING.duplicate()
		tuning.surge_warning = valeur
		assert_true(_says(tuning, "préavis de poussée"),
			"un preavis de %.2f s est REFUSE" % valeur)

## ⚠️ CE TEST GARDE UN DEFAUT QUI RENDAIT LA ZONE DECORATIVE, ET QUE SEULE UNE CAPTURE A VU.
##
## La premiere version infligeait `46 x delta` a chaque image — un taux par seconde, ce qui
## parait juste. Mais `PlayerShield.take_hit()` accorde **1,2 s d'invulnerabilite** apres tout
## coup encaisse : sur un souffle de 0,95 s, le joueur prenait EXACTEMENT une image de degats,
## soit 0,77 point sur 100. Mesure en jeu : le bouclier affichait 99. Le code se lisait comme
## s'il infligeait cinquante fois plus, et rien ne le contredisait.
##
## Le modele est donc une MORSURE par contact, cadencee par le bouclier et non par notre horloge.
func test_the_thrust_bites_instead_of_ticking() -> void:
	var stats: PlayerStats = load("res://resources/player/specter9_stats.tres")
	assert_true(stats != null, "les caracteristiques du chasseur se lisent")
	assert_true(stats.invuln_time > TUNING.surge_blast * 0.5,
		"l'invulnerabilite (%.2f s) couvre l'essentiel d'un souffle (%.2f s) — c'est POUR CA qu'un taux par seconde ne marche pas"
			% [stats.invuln_time, TUNING.surge_blast])
	assert_true(TUNING.surge_bite >= 10.0 and TUNING.surge_bite <= 34.0,
		"la morsure vaut %.0f sur %.0f de bouclier" % [TUNING.surge_bite, stats.shield_max])
	# Une morsure trop faible laisse camper dans une voie ; une morsure trop forte punit une
	# inattention d'une vie, dans une phase qui n'a aucune vague pour la rendre.
	for valeur in [2.0, 90.0]:
		var tuning: CortegeSternTuning = TUNING.duplicate()
		tuning.surge_bite = valeur
		assert_true(_says(tuning, "souffle"),
			"une morsure de %.0f est REFUSEE" % valeur)
