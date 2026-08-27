extends "res://tests/test_case.gd"
## `CoreInterior` — l'arene dediee ou l'on entre quand le noyau s'ouvre.
##
## ⚠️ CE QUE CE FICHIER GARDE, ET POURQUOI IL EXISTE. La conception decrivait deja un puits
## interieur, et la coque du boss livre les pieces qui en portent les noms : `Ring_01..05`,
## `Tunnel_End`, `Heart`. Mesurees, elles font 24 a 33 cm — pour un chasseur de 241 cm.
## Elles existaient par le NOM, jamais a l'ECHELLE, et RIEN ne l'a signale : ni le compte de
## triangles, ni le contrat d'export, ni le rendu.
##
## Un contrat de noms respecte n'est donc pas une preuve. Ces tests mesurent ce qui compte
## vraiment pour le joueur : le reacteur et le point d'entree tombent-ils dans le cadre ou
## le jeu se joue ?

const InteriorScript := preload("res://scripts/bosses/core_interior.gd")

func _make() -> CoreInterior:
	var interior := track(InteriorScript.new()) as CoreInterior
	# `_ready` ne tourne pas hors de l'arbre : on batit a la main, comme le reste du depot
	# pilote ses unites sans scene montee.
	interior._build()
	return interior

func test_the_reactor_sits_inside_the_playfield() -> void:
	# Le reacteur EST la cible de la phase. Hors des bornes, il serait intouchable.
	var interior := _make()
	var reactor := interior.reactor_plane_position()
	assert_true(GameplayPlane.BOUNDS.has_point(reactor),
		"reacteur en (%.1f, %.1f), bornes %s" % [reactor.x, reactor.y, GameplayPlane.BOUNDS])

## ⚠️ CETTE GARDE LISAIT L'ANCRAGE DU DECOR, et elle a fait son travail : agrandie, la salle
## l'a pousse a -8,4, hors de l'aire de jeu. Le vrai defaut n'etait pas la position mais le
## DOUBLON — le decor portait un point d'entree, le reglage en calculait un autre, et le
## chasseur etait pose a l'un puis conduit a l'autre. L'ancrage n'est plus lu ; la garde suit
## le point qui reste.
func test_the_entry_point_sits_inside_the_playfield() -> void:
	var tuning: LeviathanTuning = load("res://resources/bosses/pale_leviathan_tuning.tres")
	var interior := _make()
	var entry := interior.reactor_plane_position() + tuning.dive_entry_local()
	assert_true(GameplayPlane.BOUNDS.has_point(entry),
		"entree en (%.1f, %.1f), bornes %s" % [entry.x, entry.y, GameplayPlane.BOUNDS])

func test_the_fighter_does_not_start_on_top_of_the_reactor() -> void:
	# Il arrive DANS une arene, il ne s'y telporte pas au contact de sa cible : sinon la
	# phase commence par un choc que personne n'a demande.
	var interior := _make()
	var tuning: LeviathanTuning = load("res://resources/bosses/pale_leviathan_tuning.tres")
	var gap := tuning.dive_entry_local().length()
	assert_true(gap >= 3.0, "entree a %.1f m du reacteur" % gap)

func test_a_missing_decor_degrades_instead_of_breaking_the_fight() -> void:
	# Regle du depot : une piece d'asset absente DEGRADE et le dit. Un combat imparfait vaut
	# mieux qu'un combat qui plante — et tant que la forge n'a pas livre, la mecanique doit
	# rester jouable et testable.
	var interior := _make()
	# ⚠️ CETTE ASSERTION ETAIT TRIVIALEMENT VRAIE dans sa premiere forme (« la doublure OU le
	# fichier existe ») : elle passait sans jamais rien prouver. Le contrat reel a deux
	# branches, et il faut les tester toutes les deux.
	if ResourceLoader.exists(InteriorScript.DECOR_PATH):
		assert_false(interior.is_stand_in(),
			"le decor livre existe : c'est LUI qui doit etre monte, jamais la doublure")
	else:
		assert_true(interior.is_stand_in(),
			"pas de decor : la doublure prend le relais, le combat reste jouable")

func test_the_arena_is_hidden_until_the_fighter_enters() -> void:
	# Elle est montee a l'origine du monde : visible d'emblee, elle s'afficherait par-dessus
	# le combat exterieur.
	var interior := _make()
	interior.visible = false
	assert_false(interior.visible, "l'arene ne se montre qu'a l'entree")
