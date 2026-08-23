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
const NULL_MAW_HULL := preload("res://assets/imported/models/ships/null_maw.glb")
const NULL_MAW_DATA := preload("res://resources/enemies/null_maw.tres")
const LEECH_HULL := preload("res://assets/imported/models/ships/leech_drone.glb")
const LEECH_DATA := preload("res://resources/enemies/leech_drone.tres")

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


# --- Null Maw -----------------------------------------------------------------

## Débattement mesuré (BRIEF-0043-report.md) : première interpénétration
## pétale/anneau à 57,5°, l'anneau tournant impose de retenir cette valeur pour les
## cinq pétales. La butée est toujours l'anneau, jamais un voisin.
const NULL_MAW_CLEARANCE_DEG := 57.5

func test_the_shipped_maw_hull_carries_the_parts_the_code_looks_for() -> void:
	var hull := track(NULL_MAW_HULL.instantiate()) as Node3D
	var pose := EnemyPose.bind(hull, NULL_MAW_DATA.moving_part_prefix,
		NULL_MAW_DATA.open_angle_deg, NULL_MAW_DATA.open_spread)
	assert_true(pose != null, "les pétales existent dans la coque livrée")
	assert_eq(hull.find_children("Petal_*", "Node3D", true, false).size(), 5,
		"les cinq pétales annoncés par le brief sont là")

func test_the_maw_never_opens_past_what_its_geometry_allows() -> void:
	assert_true(NULL_MAW_DATA.open_angle_deg <= NULL_MAW_CLEARANCE_DEG,
		"l'ouverture réglée (%.1f°) tient sous le débattement mesuré (%.1f°)"
			% [NULL_MAW_DATA.open_angle_deg, NULL_MAW_CLEARANCE_DEG])

# --- Leech Drone --------------------------------------------------------------

## Débattement mesuré (BRIEF-0044-report.md) : première interpénétration à 147°
## sur la pince arrière, 166° sur les deux avant. Il n'y a donc PAS de butée
## mécanique à respecter ici — la douille de poignet est une surface de révolution.
## Ce qui borne l'ouverture est la LECTURE : au-delà de 51° l'enveloppe apparente
## redescend. C'est le seul réglage du bestiaire dont la limite ne soit pas une
## collision, et il vaut de le dire plutôt que de le laisser deviner.
const LEECH_CLEARANCE_DEG := 146.0

func test_the_shipped_leech_hull_carries_the_parts_the_code_looks_for() -> void:
	var hull := track(LEECH_HULL.instantiate()) as Node3D
	var pose := EnemyPose.bind(hull, LEECH_DATA.moving_part_prefix,
		LEECH_DATA.open_angle_deg, LEECH_DATA.open_spread)
	assert_true(pose != null, "les pinces existent dans la coque livrée")
	assert_eq(hull.find_children("Claw_*", "Node3D", true, false).size(), 3,
		"les trois pinces annoncées par le brief sont là")

func test_the_leech_opening_stays_within_reach() -> void:
	assert_true(LEECH_DATA.open_angle_deg <= LEECH_CLEARANCE_DEG,
		"l'ouverture réglée (%.0f°) tient sous la première interpénétration (%.0f°)"
			% [LEECH_DATA.open_angle_deg, LEECH_CLEARANCE_DEG])

## ⚠️ CELLE-CI DOIT AVOIR UN MOTEUR, à l'inverse des deux mines. C'est la plume
## d'échappement qui la fait lire comme une chose qui VIENT ; sans `Engine_C` le
## contrôleur n'en pose aucune et une poursuivante ressemblerait à un objet qui
## dérive — exactement le contresens que les mines, elles, recherchent.
func test_the_leech_hull_declares_an_engine() -> void:
	var hull := track(LEECH_HULL.instantiate()) as Node3D
	assert_true(hull.find_child("Engine_C", true, false) != null,
		"elle a une tuyère : elle poursuit, elle ne dérive pas")
	assert_true(hull.find_child("Muzzle_C", true, false) != null,
		"et la bouche que le contrôleur lit à l'initialisation")

func test_the_maw_hull_declares_no_engine() -> void:
	var hull := track(NULL_MAW_HULL.instantiate()) as Node3D
	assert_true(hull.find_child("Engine_C", true, false) == null,
		"un puits derive, il ne pousse pas")

# --- Ce qui survit a l'import, et ce qui ne survit pas -------------------------

## ⚠️ DEUX DEFAUTS QUI SE RESSEMBLENT ET N'ONT RIEN A VOIR.
##
## Un `.glb` sans triangulation ni UV sort de Blender sans TANGENT ni TEXCOORD_0 —
## l'exporteur abandonne mikktspace en silence. On en a conclu, la forge comme moi,
## que le relief de ces coques ne s'allumerait jamais. **C'est faux pour les
## tangentes** : l'import Godot porte `meshes/ensure_tangents=true` (identique sur
## toutes les coques du depot), et le moteur les FABRIQUE. Mesure a l'appui :
## `needle_scout.glb` a 0 tangente sur 7 primitives dans le fichier, et 7 surfaces
## sur 7 avec tangentes une fois chargee.
##
## **Les UV, elles, ne s'inventent pas.** Aucun importateur ne peut deviner comment
## deplier une coque. Une surface sans UV ne peut recevoir AUCUNE carte de detail —
## `HullDetail.apply()` n'aurait rien ou plaquer. C'est la propriete qui decide, et
## c'est donc elle qu'on garde.
##
## La lecon vaut au-dela du cas : un test ecrit sur la mauvaise propriete est PIRE
## qu'aucun test, parce qu'il ne peut pas echouer et qu'il rassure. La premiere
## version de ce test portait sur les tangentes ; elle etait vacante.
const HULLS_THAT_MUST_CARRY_UVS := {
	"choir_mine": CHOIR_MINE_HULL,
	"null_maw": NULL_MAW_HULL,
	"leech_drone": LEECH_HULL,
}

func _uv_coverage(scene: PackedScene) -> Vector2i:
	var hull := track(scene.instantiate())
	var surfaces := 0
	var uvs := 0
	for mesh in _meshes(hull):
		var array_mesh := mesh.mesh as ArrayMesh
		if array_mesh == null:
			continue
		for i in array_mesh.get_surface_count():
			surfaces += 1
			if array_mesh.surface_get_format(i) & Mesh.ARRAY_FORMAT_TEX_UV:
				uvs += 1
	return Vector2i(uvs, surfaces)

func test_the_new_hulls_can_all_receive_a_detail_map() -> void:
	for name in HULLS_THAT_MUST_CARRY_UVS:
		var coverage := _uv_coverage(HULLS_THAT_MUST_CARRY_UVS[name])
		assert_true(coverage.y > 0, "%s a bien des surfaces" % name)
		assert_eq(coverage.x, coverage.y,
			"%s porte ses UV (%d sur %d surfaces)" % [name, coverage.x, coverage.y])

## LA GARDE EST-ELLE VACANTE ? Non, et voici la preuve : la coque historique du
## Needle Scout n'a AUCUNE UV, et le test ci-dessus la refuserait.
##
## Elle n'y figure pas volontairement — c'est une dette connue, inscrite au backlog,
## et l'ajouter rendrait la porte rouge sur un defaut deja arbitre. Le jour ou elle
## sera reforgee, elle rejoint la liste et ce test-ci disparait.
func test_the_uv_check_would_actually_catch_a_bad_hull() -> void:
	var legacy := _uv_coverage(preload("res://assets/imported/models/ships/needle_scout.glb"))
	assert_true(legacy.y > 0, "la coque historique a bien des surfaces")
	assert_eq(legacy.x, 0,
		"et aucune UV : la garde n'est pas vacante (dette connue, %d/%d)"
			% [legacy.x, legacy.y])

func _meshes(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	var mesh := node as MeshInstance3D
	if mesh != null:
		out.append(mesh)
	for child in node.get_children():
		_meshes(child, out)
	return out
