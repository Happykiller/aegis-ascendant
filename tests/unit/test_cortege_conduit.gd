extends "res://tests/test_case.gd"
## Les conduites de l'artere : la seule prise du survol sur sa propre fin.
##
## ⚠️ CE BANC EXISTE PARCE QUE LA MECANIQUE EST INJOUABLE EN TEST. Elle demande quatre minutes de
## defilement et de viser des pieces de 21 px en passant : aucune partie automatisee ne la
## traverse. Tout ce qui compte est donc ecrit en fonctions PURES, et c'est la seule raison pour
## laquelle elles sont statiques.

const TUNING: CortegeTuning = preload("res://resources/levels/long_cortege_tuning.tres")
const Conduit := preload("res://scripts/gameplay/cortege_conduit.gd")

func test_the_shipped_tuning_is_valid() -> void:
	var errors := TUNING.validate()
	assert_eq(errors.size(), 0, "le reglage livre passe ses invariants : %s" % ", ".join(errors))

# =============================================================================
# Les quatre etats
# =============================================================================

## ⚠️ `SEVERING` N'EST JAMAIS UNE LECTURE DE SANTE. La rupture est un INSTANT : la rendre depuis
## la vie la ferait rejouer a chaque image de la trame ou la vie vaut zero, et le clip `Rupture`
## repartirait de zero soixante fois par seconde.
func test_the_break_is_a_moment_not_a_reading() -> void:
	for ratio in [0.0, 0.2, 0.5, 1.0]:
		assert_true(Conduit.state_for(true, ratio, 0.5) != Conduit.State.SEVERING,
			"a %.2f de vie, l'etat de repos n'est pas SEVERING" % ratio)
	assert_eq(Conduit.state_for(false, 0.0, 0.5), Conduit.State.SEVERED,
		"morte, elle est SEVERED")

func test_the_leak_opens_below_the_threshold() -> void:
	assert_eq(Conduit.state_for(true, 1.0, 0.5), Conduit.State.ACTIVE, "intacte")
	assert_eq(Conduit.state_for(true, 0.51, 0.5), Conduit.State.ACTIVE, "juste au-dessus")
	assert_eq(Conduit.state_for(true, 0.50, 0.5), Conduit.State.DAMAGED, "au seuil, elle fuit")
	assert_eq(Conduit.state_for(true, 0.10, 0.5), Conduit.State.DAMAGED, "et en dessous")

## ⚠️ LES QUATRE CLIPS SONT UTILISES. Livrer quatre animations et n'en jouer que deux, c'est payer
## une piece animee pour un decor — et c'est exactement ce que le BRIEF-0108 a coute a reduire en
## gardant les cles cuites.
func test_all_four_clips_are_used() -> void:
	var vus := {}
	for etat: int in [Conduit.State.ACTIVE, Conduit.State.DAMAGED,
			Conduit.State.SEVERING, Conduit.State.SEVERED]:
		vus[Conduit.clip_of(etat as Conduit.State)] = true
	assert_eq(vus.size(), 4, "quatre etats, quatre clips distincts : %s" % str(vus.keys()))

## ⚠️ ET LEURS NOMS SONT CEUX DU BINAIRE, PAS CEUX QU'ON CROIT. Un clip mal nomme ne produit
## AUCUNE erreur : `AnimationPlayer.has_animation()` rend faux, `_play_clip` passe son chemin, et
## la piece reste sur sa pose de depart pendant qu'on lui tire dessus.
func test_the_clip_names_are_the_ones_in_the_binary() -> void:
	var packed: PackedScene = load(Conduit.KIT)
	assert_true(packed != null, "la conduite se charge")
	if packed == null:
		return
	var piece := track(packed.instantiate()) as Node3D
	var player := Conduit._player_of(piece)
	assert_true(player != null, "elle porte une AnimationPlayer")
	if player == null:
		return
	for etat: int in [Conduit.State.ACTIVE, Conduit.State.DAMAGED,
			Conduit.State.SEVERING, Conduit.State.SEVERED]:
		var nom := Conduit.clip_of(etat as Conduit.State)
		assert_true(player.has_animation(nom),
			"le binaire porte le clip « %s »" % nom)

## Et le flexible porte les memes, a un nom pres — c'est ce que `_play_clip` traduit.
func test_the_hose_carries_the_same_states() -> void:
	var packed: PackedScene = load(Conduit.HOSE)
	assert_true(packed != null, "le flexible se charge")
	if packed == null:
		return
	var brin := track(packed.instantiate()) as Node3D
	var player := Conduit._player_of(brin)
	assert_true(player != null, "il porte une AnimationPlayer")
	if player == null:
		return
	for nom in ["Intact", "Endommage", "Rupture", "Rompu"]:
		assert_true(player.has_animation(nom), "le flexible porte « %s »" % nom)

## ⚠️ LE REPERE DE FUITE EST LU, PAS SUPPOSE. C'est la lecon payee sur la bouche de tuyere le
## 2026-09-08 : l'auteur livre le repere, et le code calculait une position depuis la boite
## englobante. Ici la gerbe doit naitre a la fuite, pas au centre de la piece.
func test_the_leak_socket_is_read_from_the_binary() -> void:
	var packed: PackedScene = load(Conduit.KIT)
	if packed == null:
		return
	var piece := track(packed.instantiate()) as Node3D
	var fuite := Conduit._socket_of(piece, Conduit.LEAK_SOCKET)
	assert_true(fuite != Vector3.ZERO,
		"la conduite porte « %s » (%.2f ; %.2f ; %.2f)"
			% [Conduit.LEAK_SOCKET, fuite.x, fuite.y, fuite.z])

# =============================================================================
# La cible
# =============================================================================

## ⚠️ IL N'Y A QU'UNE PORTE POUR LES DEGATS, et les tests passent par elle — meme contrat que la
## tourelle, le nœud et l'ancrage.
func test_damage_goes_through_the_target_and_kills_once() -> void:
	var conduit := Conduit.make(100.0, 1.1, 450)
	track(conduit)
	# ⚠️ UN COMPTEUR LOCAL NE SURVIT PAS A UNE LAMBDA. GDScript capture les variables locales par
	# VALEUR : `morts += 1` dans le corps de la lambda incremente une copie, et l'assertion lit
	# toujours zero — sans erreur, sans avertissement. Il faut un type par REFERENCE.
	var morts: Array[int] = [0]
	conduit.severed.connect(func(_c: CortegeConduit) -> void: morts[0] += 1)
	var cible := conduit.target()
	assert_true(cible != null and cible.hit_callback.is_valid(), "la cible est cablee")
	cible.hit_callback.call(60.0)
	assert_true(conduit.is_alive(), "elle encaisse")
	assert_eq(conduit.state(), Conduit.State.DAMAGED, "et elle fuit")
	cible.hit_callback.call(60.0)
	assert_false(conduit.is_alive(), "le second coup la coupe")
	assert_eq(conduit.state(), Conduit.State.SEVERING, "elle joue sa rupture")
	# ⚠️ ET ELLE NE MEURT QU'UNE FOIS. Une balle deja resolue dans la trame courante trouverait
	# encore la cible : sans cette garde, le niveau compterait deux conduites pour une.
	cible.hit_callback.call(60.0)
	assert_eq(morts[0], 1, "un seul `severed` pour une conduite")

## ⚠️ LA PIECE NE DECIDE PAS DE L'EFFET, ELLE LE SIGNALE. Elle emet `severed` et rien d'autre :
## qui compte, ce qu'on en fait et quand la charge est figee appartiennent au niveau. Une piece
## qui irait toucher le reglage de la poupe serait intestable sans quatre minutes de survol.
func test_the_piece_knows_nothing_about_the_stern() -> void:
	var source := FileAccess.get_file_as_string("res://scripts/gameplay/cortege_conduit.gd")
	assert_true(source.length() > 0, "le script se lit")
	# On cherche des IDENTIFIANTS, pas des mots : le docstring de la piece explique bien qu'elle
	# retire de la charge a la poupe, et il doit pouvoir le dire. Ce qui est interdit, c'est de le
	# FAIRE.
	for interdit in ["CortegeStern", "CortegeSternTuning", "surge_bite", "anchor_health",
			"charge_floor"]:
		assert_false(source.contains(interdit),
			"la conduite ne connait pas « %s » — c'est le niveau qui compte" % interdit)
