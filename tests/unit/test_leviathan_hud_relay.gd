extends "res://tests/test_case.gd"
## Le RELAIS entre le module du boss final et le HUD — pas le module, pas le HUD.
##
## ⚠️ POURQUOI CE FICHIER EXISTE. `test_leviathan_combat.gd` gardait deja les deux mesures
## du combat, et il avait raison sur les deux : `structure_ratio()` se remplit a chaque
## bascule, `fight_ratio()` ne remonte jamais. Le module etait juste. C'est le CABLAGE qui
## etait faux : le niveau envoyait au HUD la premiere, et la seconde — la seule qui prouve
## qu'on avance — n'allait qu'a la musique. Aucun test du module ne pouvait le voir.
##
## Playtest du 2026-08-25, sur un combat pourtant juge mieux equilibre : « phase 1 phase 2
## phase 1 phase 2, j'ai l'impression que c'etait en boucle ». Le joueur decrivait la
## jauge : elle faisait litteralement une boucle sous ses yeux.
##
## La lecon du depot, appliquee : un test d'unite ne remplace pas un test de branchement.

const CombatScript := preload("res://scripts/bosses/leviathan_combat.gd")
const LevelScript := preload("res://scripts/gameplay/graybox_root.gd")

## Un HUD reduit a ce que le relais lui demande : il n'affiche rien, il note tout.
## `CanvasLayer` parce que `_hud` est type ainsi dans le niveau.
class HudSpy extends CanvasLayer:
	var health: Array[float] = []
	var cycles: Array[String] = []

	func set_boss_health(ratio: float) -> void:
		health.append(ratio)

	func set_boss_cycle(text: String) -> void:
		cycles.append(text)

## Le niveau monte SANS arbre : `_hud` et `_audio` sont `@onready`, donc encore nuls tant
## que `_ready` n'a pas tourne — c'est ce qui rend le relais testable a la main. On pose
## l'espion et le module, rien d'autre.
func _make_level(combat: LeviathanCombat) -> Node:
	var level := track(LevelScript.new())
	var spy := HudSpy.new()
	level.add_child(spy)          # possede par le niveau : libere avec lui
	level._hud = spy
	level._leviathan = combat
	return level

func _make_combat() -> LeviathanCombat:
	var combat := track(CombatScript.new()) as LeviathanCombat
	combat.tuning = LeviathanTuning.new()
	combat.setup(null, null, null)
	return combat

func _kill_armour(combat: LeviathanCombat) -> void:
	for plate in combat.plates():
		combat._on_plate_hit(plate.max_health, plate.index)

## Traverse une plongee entiere. Meme decalage d'un tick que dans `test_leviathan_combat` :
## le premier tick BASCULE, il ne plonge pas.
func _ride_dive(combat: LeviathanCombat) -> void:
	var t := combat.tuning
	combat.tick(0.016)
	combat.tick(t.dive_enter_time + 0.01)
	combat.tick(t.dive_time + 0.01)
	combat.tick(t.dive_eject_time + 0.01)
	combat.tick(2.0)

# --- La jauge ---------------------------------------------------------------

func test_the_hud_gauge_shows_the_fight_not_the_current_target() -> void:
	# LE test du defaut. Apres un cycle complet, les deux mesures DIVERGENT : la cible
	# courante est pleine (l'armure vient de se reformer), la progression ne l'est plus.
	# Un relais qui se retromperait de mesure enverrait 1.0 — et ce test le verrait.
	var combat := _make_combat()
	var level := _make_level(combat)
	_kill_armour(combat)
	_ride_dive(combat)
	assert_almost_eq(combat.structure_ratio(), 1.0, 0.001,
		"pre-requis : la cible courante s'est bien remplie")
	assert_true(combat.fight_ratio() < 1.0, "pre-requis : la progression, elle, a baisse")
	level._on_leviathan_structure(combat.structure_ratio())
	var spy: HudSpy = level._hud
	assert_eq(spy.health.size(), 1, "le HUD a bien recu une valeur")
	assert_almost_eq(spy.health[0], combat.fight_ratio(), 0.001,
		"le HUD recoit la PROGRESSION DU COMBAT, jamais la sante de la cible courante")

func test_the_hud_gauge_never_climbs_back_up() -> void:
	# Trois cycles d'affilee. Une seule remontee suffit a rendre le combat illisible :
	# c'est elle que l'operateur a lue comme une boucle.
	var combat := _make_combat()
	var level := _make_level(combat)
	for cycle in 3:
		level._on_leviathan_structure(combat.structure_ratio())
		_kill_armour(combat)
		level._on_leviathan_structure(combat.structure_ratio())
		_ride_dive(combat)
	level._on_leviathan_structure(combat.structure_ratio())
	var spy: HudSpy = level._hud
	assert_true(spy.health.size() >= 7, "les sept relais ont eu lieu")
	for i in range(1, spy.health.size()):
		assert_true(spy.health[i] <= spy.health[i - 1] + 0.001,
			"la jauge ne remonte JAMAIS (releve %d : %f apres %f)"
				% [i, spy.health[i], spy.health[i - 1]])
	assert_true(spy.health[spy.health.size() - 1] < spy.health[0],
		"et elle a bel et bien descendu")

# --- Le compteur de cycle ---------------------------------------------------

func test_the_cycle_counter_reads_as_a_player_would_say_it() -> void:
	var combat := _make_combat()
	var level := _make_level(combat)
	assert_eq(level._leviathan_cycle_label(0, 3), "CYCLE 1 / 3", "premier cycle, 1-indexe")
	assert_eq(level._leviathan_cycle_label(2, 3), "CYCLE 3 / 3", "dernier cycle prevu")

func test_beyond_the_last_cycle_the_counter_is_NAMED_not_numbered() -> void:
	# ⚠️ LE COMBAT N'EST PAS BORNE A `cycle_count` et ne l'a jamais ete :
	# `plates_for_cycle()` rend le plancher de plaques indefiniment, et le boss ne meurt
	# qu'une fois le flux assez frappe. L'invariant 5 du tuning garantit que trois tours
	# SUFFIRAIENT a la cadence de reference — pas qu'il n'y en aura jamais quatre.
	# Le playtest en a produit un quatrieme, affiche « cycle 4/3 » : un compteur qui
	# depasse son total dit au joueur que le jeu s'est trompe, alors que c'est lui qui n'a
	# pas place les degats.
	var combat := _make_combat()
	var level := _make_level(combat)
	for cycle in [3, 4, 9]:
		var label: String = level._leviathan_cycle_label(cycle, 3)
		assert_eq(label, "DERNIER ASSAUT", "au-dela du dernier cycle, on NOMME le depassement")
		assert_false(label.contains("/"), "et surtout on ne compte plus : jamais de « 4 / 3 »")

func test_a_fourth_cycle_is_playable_and_stays_readable() -> void:
	# Le depassement n'est pas une panne : il doit rester jouable. Quatre cycles d'affilee,
	# sans degats sur le flux — exactement la partie du 2026-08-25.
	var combat := _make_combat()
	var level := _make_level(combat)
	for cycle in 4:
		_kill_armour(combat)
		_ride_dive(combat)
	assert_true(combat.cycle() >= 3, "on est bien alle au-dela des trois cycles prevus")
	assert_true(combat.plates().size() > 0, "et l'armure est revenue : le combat continue")
	var progress := combat.fight_ratio()
	assert_true(progress >= 0.0 and progress < 1.0,
		"la progression reste bornee et a bien avance, meme hors des cycles prevus")
