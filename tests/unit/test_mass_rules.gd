extends "res://tests/test_case.gd"
## Le poids des choses : qui écrase qui, et ce que ça coûte.
##
## ⚠️ LE MODE D'ÉCHEC QUE CE FICHIER EXISTE POUR EMPÊCHER. La masse a été ajoutée pour
## RENDRE LES VAGUES JOUABLES — « pendant les vagues d'ennemis, si on ne les tue pas assez
## vite, ils nous empêchent de bouger » (playtest 2026-08-27). Deux façons de la trahir en
## silence, et aucune ne se voit dans un test de compilation :
##
## 1. **Un seuil qui glisse** et n'écrase plus rien : les vagues redeviennent des murs, et
##    le symptôme est exactement celui d'avant la mécanique — on croit à une régression de
##    collision, on va chercher dans `PlaneCollider`.
## 2. **Un seuil qui s'ouvre trop** et écrase tout : le chasseur traverse le porteur de
##    bouclier, puis les boss, et la loi « les corps ne se chevauchent pas » n'a plus
##    d'objet. Le jeu ne plante pas — il devient un couloir.
##
## D'où des cas écrits sur les VALEURS LIVRÉES, pas sur des chiffres de laboratoire.

const ENEMY_DIR := "res://resources/enemies"
const PLAYER_STATS := preload("res://resources/player/specter9_stats.tres")

func _enemy(name: String) -> EnemyData:
	return load("%s/%s.tres" % [ENEMY_DIR, name]) as EnemyData

func _all() -> Array:
	var found := []
	var dir := DirAccess.open(ENEMY_DIR)
	if dir == null:
		return found
	for file in dir.get_files():
		var clean := file.trim_suffix(".remap")
		if clean.ends_with(".tres"):
			found.append([clean.get_basename(), load("%s/%s" % [ENEMY_DIR, clean])])
	return found

# --- La règle, seule ----------------------------------------------------------

func test_a_ratio_and_not_a_difference() -> void:
	# Deux corps de la même catégorie s'arrêtent, même si l'un est un peu plus lourd.
	assert_false(MassRules.crushes(10.0, 9.0, 3.0),
		"9 t n'est pas d'une autre categorie que 10 t")
	assert_true(MassRules.crushes(10.0, 3.0, 3.0),
		"3 t contre 10 t : le rapport est atteint")
	assert_true(MassRules.crushes(10.0, 10.0 / 3.0, 3.0),
		"le seuil exact ecrase (comparaison large)")

func test_nothing_crushes_the_immovable() -> void:
	assert_false(MassRules.crushes(MassRules.INFINITE, MassRules.INFINITE, 3.0),
		"un mur n'ecrase pas un mur")
	assert_false(MassRules.crushes(1e9, MassRules.INFINITE, 3.0),
		"aucune masse finie n'ecrase un inamovible")
	assert_true(MassRules.is_immovable(MassRules.INFINITE), "l'infini est inamovible")
	assert_true(MassRules.is_immovable(0.0),
		"une masse nulle est traitee comme un mur, pas comme une plume")

func test_no_crusher_means_everything_blocks() -> void:
	# Zéro écraseur, c'est la règle d'avant la masse : les tests et le mode sans joueur
	# doivent retrouver EXACTEMENT le comportement d'origine.
	assert_false(MassRules.crushes(0.0, 1.0, 3.0), "sans ecraseur, rien n'est ecrase")
	assert_false(MassRules.crushes(10.0, 1.0, 0.0), "sans rapport, rien n'est ecrase")

func test_the_price_is_paid_per_tonne() -> void:
	assert_almost_eq(MassRules.crush_damage(1.0, 8.0), 8.0, 0.001,
		"une tonne ecrasee coute une fois le tarif")
	assert_almost_eq(MassRules.crush_damage(2.4, 8.0), 19.2, 0.001,
		"le cout suit la masse")
	assert_almost_eq(MassRules.crush_damage(MassRules.INFINITE, 8.0), 0.0, 0.001,
		"on ne facture pas l'ecrasement d'un mur : il n'a pas lieu")

# --- La règle sur les fiches livrées ------------------------------------------

func test_every_enemy_declares_a_usable_mass() -> void:
	for pair in _all():
		var data: EnemyData = pair[1]
		assert_true(data.mass > 0.0 and not is_inf(data.mass),
			"%s : masse finie et > 0" % pair[0])
		assert_true(data.validate().is_empty(),
			"%s : %s" % [pair[0], ", ".join(data.validate())])

func test_the_scouts_no_longer_wall_the_player() -> void:
	# Le cœur de la plainte : une vague d'éclaireurs ne doit plus jamais être un mur.
	var mass: float = PLAYER_STATS.mass
	var ratio: float = PLAYER_STATS.crush_mass_ratio
	for pair in _all():
		var name: String = pair[0]
		var data: EnemyData = pair[1]
		if not name.begins_with("needle_scout"):
			continue
		assert_true(MassRules.crushes(mass, data.mass, ratio),
			"%s doit etre traversable : c'est lui qui bloquait les vagues" % name)

func test_the_shield_carrier_still_stops_the_fighter() -> void:
	# La contrepartie, et elle est aussi importante : si TOUT devient traversable, le
	# porteur de bouclier cesse d'etre la cible prioritaire qu'il est censé être.
	var carrier := _enemy("shield_carrier")
	assert_false(MassRules.crushes(PLAYER_STATS.mass, carrier.mass,
		PLAYER_STATS.crush_mass_ratio),
		"le porteur de bouclier est un corps, pas une plume")

func test_crossing_a_wave_costs_but_does_not_kill() -> void:
	# Sans invulnérabilité, écraser la vague la plus dense doit rester survivable — la
	# fenêtre d'invulnérabilité ne fait qu'améliorer ce chiffre.
	var scout := _enemy("needle_scout")
	var cost: float = MassRules.crush_damage(scout.mass * 5.0,
		PLAYER_STATS.crush_damage_per_mass)
	assert_true(cost < PLAYER_STATS.shield_max,
		"cinq eclaireurs d'un coup coutent %.0f pour %.0f de bouclier"
			% [cost, PLAYER_STATS.shield_max])
	assert_true(cost > PLAYER_STATS.shield_max * 0.25,
		"et ca doit COUTER : foncer dans le tas ne peut pas etre la strategie dominante")

# --- La portée : écraser exactement là où on aurait été bloqué ----------------

## ⚠️ LE PIÈGE GÉOMÉTRIQUE, ET IL EST SILENCIEUX. L'écrasement et le blocage sont mesurés
## par deux codes différents : `PlaneCollider.capsule_blocks()` ÉCHANTILLONNE l'axe du
## chasseur en cinq points, `WaveSpawner.crush_contacts()` mesure la distance EXACTE au
## segment. Si l'écrasement portait moins loin que le blocage, il existerait une bande où
## une unité arrête le chasseur sans jamais être broyée — un mur invisible, exactement le
## défaut qu'on prétend corriger. L'exact doit donc toujours couvrir l'échantillonné.
func test_the_crush_reach_covers_everything_that_would_block() -> void:
	var half: float = 1.23
	var radius: float = 0.88
	var axis := Vector2(0.0, 1.0)
	var centre := Vector2.ZERO
	var enemy_radius: float = 0.45
	var reach := enemy_radius + radius
	var missed := 0
	var tested := 0
	for ix in 41:
		for iy in 41:
			var at := Vector2(lerpf(-4.0, 4.0, ix / 40.0), lerpf(-4.0, 4.0, iy / 40.0))
			var shapes := PlaneShapes.new()
			shapes.reserve(1)
			shapes.add_disc(at, enemy_radius)
			if not PlaneCollider.capsule_blocks(shapes, centre, axis, half, radius):
				continue
			tested += 1
			if PlaneCollider.distance_to_segment(at, centre - axis * half,
					centre + axis * half) > reach:
				missed += 1
	assert_true(tested > 0, "l'echantillonnage a bien trouve des positions bloquantes")
	assert_eq(missed, 0,
		"%d position(s) bloqueraient sans etre ecrasees — un mur invisible" % missed)
