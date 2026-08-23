extends "res://tests/test_case.gd"
## Les coques LIVRÉES tiennent-elles le contrat que le code attend d'elles ?
##
## `test_enemy_pose.gd` prouve que la mécanique d'ouverture est juste — sur des
## nœuds construits à la main. Il ne dit rien de la coque réellement expédiée :
## un `.glb` dont les pièces s'appelleraient `Plate_1` au lieu de `Segment_01`
## passerait toute la porte de qualité, et la mine s'ouvrirait... jamais. Sans
## erreur, sans test rouge, et invisible sur une capture au repos.
##
## C'est le même trou que `test_enemy_resources.gd` a fermé pour les Resources.

const CHOIR_MINE_HULL := preload("res://assets/imported/models/ships/choir_mine.glb")
const CHOIR_MINE_DATA := preload("res://resources/enemies/choir_mine.tres")

## Débattement mécanique MESURÉ sur le maillage livré (BRIEF-0042-report.md) :
## première interpénétration plaque/voisine à 57°, dernière valeur sûre 56°.
## Ce n'est pas une préférence, c'est une propriété de la géométrie.
const CHOIR_MINE_CLEARANCE_DEG := 56.0

func test_the_shipped_mine_hull_carries_the_parts_the_code_looks_for() -> void:
	var hull := track(CHOIR_MINE_HULL.instantiate()) as Node3D
	var pose := EnemyPose.bind(hull, CHOIR_MINE_DATA.moving_part_prefix,
		CHOIR_MINE_DATA.open_angle_deg)
	assert_true(pose != null,
		"les pièces '%s_NN' existent dans la coque livrée" % CHOIR_MINE_DATA.moving_part_prefix)
	var found := 0
	for child in hull.find_children("Segment_*", "Node3D", true, false):
		found += 1
	assert_eq(found, 6, "les six segments annoncés par le brief sont là")

## ⚠️ LA GARDE QUI COMPTE. L'ouverture réglée dans la Resource doit rester sous le
## débattement mesuré sur CETTE coque. Une reforge qui rapprocherait les plaques
## rendrait la valeur fausse sans que rien ne le dise : la bbox, le budget, les
## matériaux et le pivot resteraient parfaits, et les plaques se traverseraient à
## l'écran. Le contrat d'export mesure cinq choses, et aucune ne parle de la forme.
func test_the_mine_never_opens_past_what_its_geometry_allows() -> void:
	assert_true(CHOIR_MINE_DATA.open_angle_deg <= CHOIR_MINE_CLEARANCE_DEG,
		"l'ouverture réglée (%.0f°) tient sous le débattement mesuré (%.0f°)"
			% [CHOIR_MINE_DATA.open_angle_deg, CHOIR_MINE_CLEARANCE_DEG])
	assert_true(CHOIR_MINE_DATA.open_angle_deg > 0.0, "et elle s'ouvre pour de bon")

## Une mine n'a pas de moteur. Si une reforge lui rendait un `Engine_C`, le
## contrôleur lui accrocherait une plume et elle se lirait comme un vaisseau en
## approche — exactement ce qu'on a passé un brief à éviter.
func test_the_mine_hull_declares_no_engine() -> void:
	var hull := track(CHOIR_MINE_HULL.instantiate()) as Node3D
	assert_true(hull.find_child("Muzzle_C", true, false) != null,
		"la bouche existe : le contrôleur la lit à l'initialisation")
	assert_true(hull.find_child("Engine_C", true, false) == null,
		"et aucune tuyère : une mine derive, elle ne pousse pas")
