extends "res://tests/test_case.gd"
## Le jeu de detail d'une coque (ADR-0044 §4) : une Resource validee, resolue depuis
## la coque, et posee PAR NOEUD — les tuyeres recoivent leur propre matiere.
##
## Le runner tourne en `--script` : pas de rendu, mais `MeshInstance3D` et
## `StandardMaterial3D` se construisent, et c'est tout ce dont `HullDetail` a besoin.
## On monte donc une fausse coque a la main : deux maillages au meme materiau `AA_Hull`,
## l'un sous `Nozzle_L`, l'autre pas.

const DefaultSet := preload("res://resources/player/hull_detail_default.tres")
const SetScript := preload("res://resources/data/hull_detail_set.gd")

func _material(name: String) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.resource_name = name
	return material

func _mesh_with(material: StandardMaterial3D) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.surface_set_material(0, material)
	mesh.mesh = box
	return mesh

## Une coque avec une tuyere : `Hull/Body` (AA_Hull), `Hull/Nozzle_L/Cone` (AA_Hull),
## et une vitre `Hull/Glass` (AA_Glass) qui ne doit rien recevoir.
func _hull() -> Node3D:
	var hull := track(Node3D.new()) as Node3D
	var body := _mesh_with(_material("AA_Hull"))
	body.name = "Body"
	hull.add_child(body)
	var nozzle := Node3D.new()
	nozzle.name = "Nozzle_L"
	hull.add_child(nozzle)
	var cone := _mesh_with(_material("AA_Hull"))
	cone.name = "Cone"
	nozzle.add_child(cone)
	var glass := _mesh_with(_material("AA_Glass"))
	glass.name = "Glass"
	hull.add_child(glass)
	return hull

func _rich_set() -> HullDetailSet:
	var detail: HullDetailSet = DefaultSet.duplicate()
	detail.nozzle_mul = DefaultSet.ao
	detail.nozzle_normal = DefaultSet.normal
	detail.nozzle_roughness = DefaultSet.roughness
	detail.nozzle_ao = DefaultSet.mul
	detail.nozzle_tiling = 2.0
	return detail

# --- La Resource ---------------------------------------------------------------

func test_the_default_set_validates_and_has_no_nozzle_set() -> void:
	assert_true(DefaultSet.validate().is_empty(), "le jeu partage est valide (%s)" % ", ".join(DefaultSet.validate()))
	assert_false(DefaultSet.has_nozzle_set(), "le jeu partage n'a pas de matiere de tuyere")

func test_a_set_without_a_map_is_rejected() -> void:
	var detail: HullDetailSet = DefaultSet.duplicate()
	detail.roughness = null
	assert_false(detail.validate().is_empty(), "une carte manquante rend le jeu invalide")

func test_the_nozzle_set_is_all_or_nothing() -> void:
	var detail: HullDetailSet = DefaultSet.duplicate()
	detail.nozzle_normal = DefaultSet.normal
	assert_false(detail.validate().is_empty(), "une seule carte de tuyere sur quatre est refusee")
	assert_false(detail.has_nozzle_set(), "et le jeu de tuyere n'est pas repute present")
	assert_true(_rich_set().validate().is_empty(), "les quatre cartes de tuyere valident")

# --- La resolution ------------------------------------------------------------

func test_an_unknown_hull_gets_the_shared_set() -> void:
	assert_true(HullDetail.set_for("res://assets/imported/models/ships/specter_9.glb") == DefaultSet,
		"la coque en service recoit le jeu partage")
	assert_true(HullDetail.set_for("") == DefaultSet, "une coque sans chemin aussi")

func test_registered_sets_are_keyed_by_file_name() -> void:
	# Le registre est vide tant que la cellule-temoin n'a pas ses textures (LOT 3) ;
	# ce test garde le CONTRAT de la cle : le nom de fichier, pas le chemin — donc le
	# meme fichier sous deux chemins recoit le meme jeu, registre vide ou non.
	assert_true(HullDetail.set_for("res://a/specter_9_c.glb") == HullDetail.set_for("specter_9_c.glb"),
		"la resolution ne lit que le nom de fichier")
	for key: String in HullDetail.SETS:
		assert_eq(key, key.get_file(), "la cle '%s' est un nom de fichier" % key)
		var detail: HullDetailSet = HullDetail.SETS[key]
		assert_true(detail.validate().is_empty(), "le jeu de '%s' est valide" % key)

# --- La pose --------------------------------------------------------------------

func test_apply_dresses_hull_and_skips_glass() -> void:
	var hull := _hull()
	HullDetail.apply(hull, DefaultSet)
	var body := hull.get_node("Body") as MeshInstance3D
	var tuned := body.get_surface_override_material(0) as StandardMaterial3D
	assert_true(tuned != null, "la coque recoit un materiau ajuste")
	assert_true(tuned.albedo_texture == DefaultSet.mul, "avec la carte de multiplication du jeu")
	assert_true(tuned.normal_enabled and tuned.normal_texture == DefaultSet.normal, "et sa normale")
	var glass := hull.get_node("Glass") as MeshInstance3D
	assert_true(glass.get_surface_override_material(0) == null, "la vitre ne recoit rien (glass_alpha = -1)")

func test_a_set_can_open_the_glass() -> void:
	# La cellule-temoin a un cockpit DERRIERE sa vitre ; le kit livre la meme vitre a
	# 0,86 pour toutes les coques. C'est le jeu qui l'eclaircit, pas le kit.
	var hull := _hull()
	var detail: HullDetailSet = DefaultSet.duplicate()
	detail.glass_alpha = 0.35
	assert_true(detail.validate().is_empty(), "une opacite dans [0, 1] est valide")
	HullDetail.apply(hull, detail)
	var glass := (hull.get_node("Glass") as MeshInstance3D).get_surface_override_material(0) as StandardMaterial3D
	assert_true(glass != null, "la vitre recoit un materiau ajuste")
	assert_almost_eq(glass.albedo_color.a, 0.35, 1e-6, "avec l'opacite du jeu")
	assert_eq(glass.transparency, BaseMaterial3D.TRANSPARENCY_ALPHA, "et une vraie transparence")
	assert_true(glass.albedo_texture == null, "mais aucune carte de plaques sur une vitre")
	detail.glass_alpha = 1.5
	assert_false(detail.validate().is_empty(), "au-dela de 1, refuse")

func test_without_a_nozzle_set_the_nozzle_wears_the_hull_maps() -> void:
	var hull := _hull()
	HullDetail.apply(hull, DefaultSet)
	var cone := hull.get_node("Nozzle_L/Cone") as MeshInstance3D
	var tuned := cone.get_surface_override_material(0) as StandardMaterial3D
	assert_true(tuned != null and tuned.albedo_texture == DefaultSet.mul,
		"sans matiere de tuyere, la tuyere porte la peau de coque")

func test_the_nozzle_set_goes_to_nozzle_nodes_only() -> void:
	var hull := _hull()
	var detail := _rich_set()
	HullDetail.apply(hull, detail)
	var cone := (hull.get_node("Nozzle_L/Cone") as MeshInstance3D).get_surface_override_material(0) as StandardMaterial3D
	var body := (hull.get_node("Body") as MeshInstance3D).get_surface_override_material(0) as StandardMaterial3D
	assert_true(cone.albedo_texture == detail.nozzle_mul, "la tuyere recoit sa carte de multiplication")
	assert_almost_eq(cone.uv1_scale.x, detail.nozzle_tiling, 1e-6, "et son tuilage")
	assert_true(body.albedo_texture == detail.mul, "la coque garde la sienne")
	assert_almost_eq(body.uv1_scale.x, detail.tiling, 1e-6, "et son tuilage")

func test_the_imported_material_is_never_mutated() -> void:
	var hull := _hull()
	var body := hull.get_node("Body") as MeshInstance3D
	var imported := body.mesh.surface_get_material(0) as StandardMaterial3D
	HullDetail.apply(hull, DefaultSet)
	assert_true(imported.albedo_texture == null, "le materiau importe n'a pas ete touche")
	assert_true(body.get_surface_override_material(0) != imported, "la pose est une copie")

# --- Le regime ATLAS (ADR-0047) ------------------------------------------------

func _atlas_set() -> HullDetailSet:
	var detail: HullDetailSet = DefaultSet.duplicate()
	detail.albedo = DefaultSet.ao   # n'importe quelle texture fait l'affaire ici
	detail.tiling = 1.0
	return detail

func test_an_atlas_set_replaces_the_palette_instead_of_multiplying_it() -> void:
	# ⚠️ LE POINT QUI RENVERSE LA POSE. Une feuille MULTIPLIE la couleur du .glb ; un
	# atlas la porte deja. Sans la mise au blanc, un borde blanc casse peint en blanc
	# casse ressortirait deux fois teinte — du beige, et personne ne saurait pourquoi.
	var hull := _hull()
	var detail := _atlas_set()
	HullDetail.apply(hull, detail)
	var body := (hull.get_node("Body") as MeshInstance3D).get_surface_override_material(0) as StandardMaterial3D
	assert_true(body.albedo_texture == detail.albedo, "l'atlas est pose en albedo")
	assert_almost_eq(body.albedo_color.r, 1.0, 1e-6, "et la couleur passe au neutre")
	assert_almost_eq(body.albedo_color.g, 1.0, 1e-6, "sur les trois canaux")
	assert_almost_eq(body.albedo_color.b, 1.0, 1e-6, "sans exception")
	assert_almost_eq(body.uv1_scale.x, 1.0, 1e-6, "et le tuilage vaut 1 : chaque texel a une adresse")

func test_an_atlas_covers_the_nozzles_too() -> void:
	# Un atlas couvre TOUTE la coque : la matiere de tuyere separee n'a plus de sens,
	# la tuyere a deja ses texels dans l'image.
	var hull := _hull()
	var detail := _atlas_set()
	detail.nozzle_mul = DefaultSet.mul
	detail.nozzle_normal = DefaultSet.normal
	detail.nozzle_roughness = DefaultSet.roughness
	detail.nozzle_ao = DefaultSet.ao
	HullDetail.apply(hull, detail)
	var cone := (hull.get_node("Nozzle_L/Cone") as MeshInstance3D).get_surface_override_material(0) as StandardMaterial3D
	assert_true(cone.albedo_texture == detail.albedo, "la tuyere porte l'atlas, pas une matiere a part")

func test_an_atlas_with_a_tiling_other_than_one_is_refused() -> void:
	# Le defaut serait SILENCIEUX : le dessin glisserait, le matricule finirait sur une
	# aile, et rien dans le journal ne le dirait.
	var detail := _atlas_set()
	assert_true(detail.validate().is_empty(), "un atlas a tuilage 1 est valide")
	detail.tiling = 0.25
	assert_false(detail.validate().is_empty(), "a tuilage 0,25 il est refuse")
	detail.tiling = 1.0
	detail.nozzle_mul = DefaultSet.mul
	detail.nozzle_normal = DefaultSet.normal
	detail.nozzle_roughness = DefaultSet.roughness
	detail.nozzle_ao = DefaultSet.ao
	assert_false(detail.validate().is_empty(), "et un atlas AVEC matiere de tuyere aussi")

func test_the_shared_set_is_not_an_atlas() -> void:
	assert_false(DefaultSet.is_atlas(), "le jeu partage reste une feuille repetable")
