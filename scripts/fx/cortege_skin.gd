class_name CortegeSkin
## Habille les matériaux nommés de la coque du Long Cortège avec les cartes dérivées.
##
## ⚠️ CE N'EST PAS `HullDetail`, ET LA DIFFÉRENCE EST TOUT LE FICHIER. `HullDetail` pose UNE
## feuille de détail sur TOUTES les surfaces d'un chasseur, et son réglage principal est
## `uv1_scale` : les coques de chasseur sont dépliées en tuiles/unité, pas en mètres, donc
## l'échelle se rattrape au moteur. Ici c'est l'inverse : la forge a déplié le Cortège en
## MÈTRES (`HULL_TEXELS_PER_METER = 0,200`, soit 5,00 m par tuile), et cette métrique est ce
## qui rend les jonctions de tronçons invisibles — elle ne tient que parce que `100 × 0,200`
## est entier (`BRIEF-0089-report.md`). **Toucher à `uv1_scale` ici rouvrirait une couture
## tous les 100 m, cinq fois dans le niveau.** Aucune mise à l'échelle, donc.
##
## ⚠️ ET C'EST UNE CARTE PAR MATÉRIAU, pas une feuille pour tout le monde. Le bordé, les
## greffes rapportées, la machinerie et l'artère lumineuse racontent quatre choses
## différentes — c'est même le seul moyen qu'a le niveau de dire que ce vaisseau est
## *agrégé* et non construit. Une feuille unique les rendrait tous identiques, et l'on aurait
## payé quatre images pour un seul matériau.
##
## ⚠️ RIEN N'EST `preload`. Les cartes viennent de l'opérateur (`ADR-0028` : la texture est sa
## voie) et n'existent pas tant qu'il ne les a pas fournies. Un `preload` sur un fichier absent
## est une erreur de COMPILATION en GDScript : le niveau entier cesserait de se monter, et la
## porte de qualité tomberait, pour un habillage qui est censé être facultatif. Chargement au
## runtime, matériau par matériau : ce qui manque est simplement sauté, et le journal le dit.

## Le dossier des cartes dérivées, tel que l'annoncent les `integration_notes` des demandes
## `TEX-0010` à `TEX-0014`.
const MAPS_DIR := "res://assets/imported/textures/cortege/"

## Quel jeu de cartes pour quel matériau du `.glb`. La clé est le `resource_name` importé,
## c'est-à-dire le nom donné par `aegis_kit` — le contrat de nommage de la forge.
const SKINS: Dictionary = {
	&"AA_Hull": "cortege_hull",
	&"AA_Panel": "cortege_panel",
	&"AA_Greeble": "cortege_greeble",
	# ⚠️ POSÉ PAR `BRIEF-0090`, ET SA RAISON N'EST PAS LA COULEUR : c'est l'ÉCHELLE. Ambry est
	# déplié à 0,700 tuile/m contre 0,200 pour le bordé ; toute face d'Ambry restée sur un slot
	# du bordé aurait reçu sa carte 3,5 fois trop fine — un défaut latent qu'on n'aurait
	# découvert qu'une fois les images générées, et qui aurait demandé une reforge.
	&"AA_Hull_Ambry": "ambry_hull",
}

## L'émissif est à part : c'est une COULEUR, pas une hauteur. Aucune normale n'en est dérivée
## (règle 2 du contrat de texture), et la même image sert d'albédo et d'émission.
const EMISSIVE_MATERIAL := &"AA_Emissive_Engine"
const EMISSIVE_MAP := "cortege_emissive"

## ⚠️ Discret. Le relief d'un bordé de 500 m se lit à 23 px/m après le post-traitement rétro :
## au-delà, la coque prend l'aspect martelé qu'`ADR-0011` a déjà payé sur le Specter-9 à 1,5.
const NORMAL_SCALE := 0.7

## Habille la coque. Renvoie le nombre de surfaces effectivement retexturées — zéro quand
## l'opérateur n'a pas encore fourni les images, et c'est un état normal, pas une panne.
static func apply(hull: Node) -> int:
	var dressed := 0
	for mesh in _meshes(hull):
		for i in mesh.get_surface_override_material_count():
			var base := mesh.get_active_material(i) as StandardMaterial3D
			if base == null:
				continue
			var name := StringName(base.resource_name)
			var tuned: StandardMaterial3D = null
			if name == EMISSIVE_MATERIAL:
				tuned = _skin_emissive(base)
			elif SKINS.has(name):
				tuned = _skin_surface(base, String(SKINS[name]))
			if tuned == null:
				continue
			mesh.set_surface_override_material(i, tuned)
			dressed += 1
	return dressed

## Une surface de relief : hauteur dérivée en normale, rugosité et AO, plus la carte de
## multiplication en albédo.
static func _skin_surface(base: StandardMaterial3D, stem: String) -> StandardMaterial3D:
	var nrm := _map(stem, "nrm")
	var mul := _map(stem, "mul")
	# ⚠️ TOUT OU RIEN, PAR MATÉRIAU. Poser la multiplication sans la normale donnerait des
	# rainures PEINTES que la lumière ne voit pas — la coque resterait un aplat, et l'on
	# conclurait que la texture ne sert à rien. C'est mot pour mot la leçon d'`ADR-0013`,
	# écrite en tête de `hull_detail.gd`.
	if nrm == null or mul == null:
		return null
	# On DUPLIQUE : le matériau importé appartient au `.glb`, et l'écrire en place mute une
	# ressource partagée que rien ne remettra en état.
	var tuned: StandardMaterial3D = base.duplicate()
	tuned.albedo_texture = mul
	tuned.normal_enabled = true
	tuned.normal_texture = nrm
	tuned.normal_scale = NORMAL_SCALE
	var rough := _map(stem, "rough")
	if rough != null:
		tuned.roughness_texture = rough
		tuned.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	var ao := _map(stem, "ao")
	if ao != null:
		tuned.ao_enabled = true
		tuned.ao_texture = ao
		tuned.ao_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
		# 0 = l'AO n'assombrit que l'ambiante. Au-delà elle mange la lumière directe et la
		# coque vire au gris sale sous la clé.
		tuned.ao_light_affect = 0.0
	return tuned

## L'artère et le fond des puits : la même image en albédo et en émission.
##
## ⚠️ L'INTENSITÉ RESTE CELLE DU `.glb`. `aegis_kit` pose l'émissif à 2,5, et c'est le réglage
## qui a été jugé en capture sur la coque nue. La texture apporte un MOTIF, pas une puissance :
## la remonter ici noierait les signaux que le moteur pose par-dessus — le bulbe d'un nœud
## d'épine, le couvercle d'un puits — et le joueur ne verrait plus ce qu'il a détruit.
static func _skin_emissive(base: StandardMaterial3D) -> StandardMaterial3D:
	var map := _map(EMISSIVE_MAP, "")
	if map == null:
		return null
	var tuned: StandardMaterial3D = base.duplicate()
	tuned.albedo_texture = map
	tuned.emission_enabled = true
	tuned.emission_texture = map
	return tuned

## Une carte, ou `null` si l'opérateur ne l'a pas encore fournie.
static func _map(stem: String, suffix: String) -> Texture2D:
	var path := MAPS_DIR + stem + ("_" + suffix if suffix != "" else "") + ".png"
	if not ResourceLoader.exists(path):
		return null
	return load(path) as Texture2D

static func _meshes(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	var mesh := node as MeshInstance3D
	if mesh != null:
		out.append(mesh)
	for child in node.get_children():
		_meshes(child, out)
	return out
