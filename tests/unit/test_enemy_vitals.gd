extends "res://tests/test_case.gd"
## Les signes vitaux d'une coque (EnemyVitals) — ce que la mine MONTRE.
##
## ⚠️ Ce fichier existe à cause d'une capture, pas d'un raisonnement. La première
## version des signes vitaux ne faisait que monter l'énergie de l'émissif, ×2,4 à
## pleine menace. Tous les tests étaient verts. En jeu, mesuré sur la capture : la
## mine en plein télégraphe rendait un pic de luminance de 236,6 quand les dormantes
## rendaient 215 à 227 — l'engagement était DANS la dispersion du repos.
##
## Deux causes, et aucune n'était visible depuis le code : les pixels du noyau
## étaient déjà écrêtés (244-255), donc multiplier leur énergie était une opération
## nulle ; et le fond du jeu est une nébuleuse magenta, exactement la teinte du
## Chœur Nul. Sur un fond lumineux, ce qui se voit n'est pas l'intensité mais le
## CHANGEMENT DE TEINTE.
##
## D'où ces tests : ils portent sur la teinte, parce que c'est la grandeur qui
## décide. La luminance, elle, se recouvrait toujours après correction.

const MAGENTA := Color(0.851, 0.239, 0.612)
const BASE_ENERGY := 2.5

func _hull() -> Node3D:
	var hull := track(Node3D.new()) as Node3D
	var mesh := MeshInstance3D.new()
	mesh.mesh = BoxMesh.new()
	var material := StandardMaterial3D.new()
	# C'est le nom qui fait foi : le kit Blender le pose sur toutes les coques.
	material.resource_name = "AA_Emissive_Engine"
	material.emission = MAGENTA
	material.emission_energy_multiplier = BASE_ENERGY
	mesh.set_surface_override_material(0, material)
	hull.add_child(mesh)
	return hull

func _material(hull: Node3D) -> StandardMaterial3D:
	return (hull.get_child(0) as MeshInstance3D).get_active_material(0) as StandardMaterial3D

## Une coque sans noyau émissif n'a rien à faire respirer, et ce n'est pas une
## erreur : les neuf familles écrites avant celle-ci fonctionnent très bien sans.
func test_a_hull_without_a_core_binds_to_nothing() -> void:
	assert_true(EnemyVitals.bind(null) == null, "pas de coque, pas de signes vitaux")
	assert_true(EnemyVitals.bind(track(Node3D.new()) as Node3D) == null,
		"une coque sans maillage émissif ne rend pas un objet vide")

## ⚠️ On DUPLIQUE le matériau. `AA_Emissive_Engine` porte le même nom sur TOUTES les
## coques du jeu : le muter en place ferait battre le chasseur du joueur au rythme
## d'une mine.
func test_binding_never_touches_the_material_shared_by_every_hull() -> void:
	var hull := _hull()
	var shared := _material(hull)
	var vitals := EnemyVitals.bind(hull)
	assert_true(vitals != null, "le noyau est trouvé")
	vitals.update(0.016, 1.0)
	assert_almost_eq(shared.emission_energy_multiplier, BASE_ENERGY, 0.0001,
		"le matériau d'origine n'a pas bougé")
	assert_true(_material(hull) != shared, "l'instance a le sien")

## Une mine qui dort doit lire comme ÉTEINTE. Sans cette atténuation, son réveil
## part du même niveau qu'un ennemi ordinaire et n'a plus d'amplitude pour se faire
## remarquer — c'est la moitié du défaut mesuré en capture.
func test_a_sleeping_hull_burns_lower_than_a_living_one() -> void:
	var hull := _hull()
	var vitals := EnemyVitals.bind(hull)
	vitals.update(0.016, 0.0)
	assert_true(_material(hull).emission_energy_multiplier < BASE_ENERGY * 0.6,
		"endormie, elle est nettement en dessous du nominal (%f)"
			% _material(hull).emission_energy_multiplier)

# --- La teinte : la grandeur qui décide ---------------------------------------

func _red_green_gap(hull: Node3D) -> float:
	var emission := _material(hull).emission
	return emission.r - emission.g

## L'ÉVEIL RESTE MAGENTA. Le magenta dit « elle t'a vu », le blanc dit « c'est
## parti » : les confondre, c'est n'avoir qu'un seul signal pour deux moments, et
## le joueur ne sait plus lequel des cinq objets à l'écran va lui exploser dessus.
func test_mere_alertness_never_changes_the_colour() -> void:
	var hull := _hull()
	var vitals := EnemyVitals.bind(hull)
	vitals.update(0.016, EnemyReaction.ALERT_CEILING)
	assert_almost_eq(_red_green_gap(hull), MAGENTA.r - MAGENTA.g, 0.0001,
		"au plus fort de l'éveil, elle est encore magenta")

## L'engagement vire au blanc chaud. C'est la mesure qui a séparé les deux états en
## capture : écart rouge-vert de 7,2 pour la mine engagée contre 26,8 à 53,2 pour
## les dormantes, sans recouvrement — là où la luminance, elle, se recouvrait.
func test_committing_turns_the_core_white() -> void:
	var hull := _hull()
	var vitals := EnemyVitals.bind(hull)
	var asleep := 0.0
	vitals.update(0.016, 0.0)
	asleep = _red_green_gap(hull)
	vitals.update(0.016, 1.0)
	var committed := _red_green_gap(hull)
	assert_true(committed < asleep * 0.35,
		"le noyau a franchement vire au blanc (%f contre %f au repos)" % [committed, asleep])

## Le virage est PROGRESSIF sur le télégraphe : c'est ce qui en fait une jauge que
## le joueur peut lire, et non un interrupteur qu'il subit.
func test_the_colour_shift_tracks_the_telegraph() -> void:
	assert_almost_eq(EnemyVitals.commit_ratio(EnemyReaction.ALERT_CEILING), 0.0, 0.0001,
		"à l'éveil plein, l'engagement n'a pas commencé")
	assert_almost_eq(EnemyVitals.commit_ratio(1.0), 1.0, 0.0001, "à la charge, il est total")
	var half := EnemyVitals.commit_ratio((EnemyReaction.ALERT_CEILING + 1.0) * 0.5)
	assert_almost_eq(half, 0.5, 0.0001, "et il progresse au milieu (%f)" % half)
	assert_almost_eq(EnemyVitals.commit_ratio(0.0), 0.0, 0.0001, "endormie, aucun engagement")

## Une instance recyclée qui revient en scène doit être éteinte et magenta : elle
## annoncerait sinon une charge qui n'aura pas lieu.
func test_a_recycled_hull_comes_back_asleep() -> void:
	var hull := _hull()
	var vitals := EnemyVitals.bind(hull)
	vitals.update(0.016, 1.0)
	vitals.reset()
	assert_almost_eq(_red_green_gap(hull), MAGENTA.r - MAGENTA.g, 0.0001,
		"elle a retrouvé sa teinte de repos")
	assert_true(_material(hull).emission_energy_multiplier < BASE_ENERGY,
		"et son régime de sommeil")

## Deux mines côte à côte ne doivent jamais battre ensemble : la synchronisation
## trahit la machine (ADR-0015). Le déphasage suit un pas irrationnel, donc il est
## reproductible d'un lancement à l'autre — contrairement à un tirage aléatoire.
func test_two_neighbouring_hulls_never_breathe_in_step() -> void:
	var first := _hull()
	var second := _hull()
	var a := EnemyVitals.bind(first)
	var b := EnemyVitals.bind(second)
	a.update(0.016, 0.0)
	b.update(0.016, 0.0)
	assert_true(absf(_material(first).emission_energy_multiplier
		- _material(second).emission_energy_multiplier) > 0.0001,
		"leurs respirations sont déphasées")
