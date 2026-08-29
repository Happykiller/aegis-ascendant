class_name CortegeSkin
## Habille les matériaux nommés de la coque du Long Cortège avec les cartes dérivées.
##
## ⚠️ CE N'EST PAS `HullDetail`, ET LA DIFFÉRENCE EST TOUT LE FICHIER. `HullDetail` pose UNE
## feuille de détail sur TOUTES les surfaces d'un chasseur ; ici c'est une carte par matériau,
## parce que le bordé, les greffes, la machinerie et l'artère racontent quatre choses
## différentes — c'est même le seul moyen qu'a le niveau de dire que ce vaisseau est *agrégé*
## et non construit.
##
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
const NORMAL_SCALE := 0.45

## Agrandissement des tuiles du bordé de l'Unisson. **< 1 agrandit** : `uv1_scale` multiplie les
## coordonnées, donc 0,5 fait couvrir DEUX FOIS plus de monde à la même image.
##
## ⚠️ IL A FALLU MESURER POUR LE VOULOIR. À l'échelle livrée — 5,00 m par tuile —, une plaque de
## 2 m fait 46 px à l'écran mais un joint de 10 cm n'en fait que 2 : une fois les mipmaps
## activées (et il le fallait, sans elles la coque SCINTILLE), le filtrage moyenne ce détail
## jusqu'à le faire disparaître. Résultat mesuré : la coque perdait **33 % de luminance** — le
## prix du relief et de l'occlusion — pour un détail qu'on ne voyait plus. C'est exactement le
## marché qu'`ADR-0016` a déjà refusé une fois sur ce projet.
##
## ⚠️ ET C'EST AUTORISÉ, CONTRE TOUTE ATTENTE. La règle de la forge n'interdit pas de mettre à
## l'échelle : elle exige que `100 × densité` reste ENTIER, sans quoi `v` saute d'une demi-tuile
## à chaque jonction de tronçon (`BRIEF-0089-report.md`). Or 0,200 × 0,5 = 0,100, et
## 100 × 0,100 = 10 — entier. Les cinq jonctions restent invisibles. Toute autre valeur doit
## refaire ce calcul : 0,5 et 0,25 passent, 0,4 (densité 0,08, produit 8) passe aussi, 0,3 non.
const HULL_UV_SCALE := 0.5

## ⚠️ AMBRY GARDE LA SIENNE. Elle est un objet unique, sans jonction à assurer, et son dépliage
## serré (1,43 m par tuile) EST la révélation du niveau : c'est lui qui la fait lire construite
## à l'échelle de la main. L'agrandir la ramènerait à l'échelle du vaisseau qui l'a emportée.
const AMBRY_UV_SCALE := 1.0

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
				var scale := AMBRY_UV_SCALE if name == &"AA_Hull_Ambry" else HULL_UV_SCALE
				tuned = _skin_surface(base, String(SKINS[name]), scale)
			if tuned == null:
				continue
			mesh.set_surface_override_material(i, tuned)
			dressed += 1
	return dressed

## Une surface de relief : hauteur dérivée en normale, rugosité et AO, plus la carte de
## multiplication en albédo.
static func _skin_surface(base: StandardMaterial3D, stem: String,
		uv_scale: float) -> StandardMaterial3D:
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
	tuned.uv1_scale = Vector3(uv_scale, uv_scale, uv_scale)
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
## ⚠️ L'INTENSITÉ BAISSE AVEC L'ARRIVÉE DE LA TEXTURE, ET C'EST L'INVERSE DE CE QUE J'AVAIS
## ÉCRIT ICI. `aegis_kit` pose l'émissif à 2,5, et ce réglage a été jugé en capture sur une
## COULEUR PLATE : il fallait 2,5 pour qu'un aplat sombre lise comme une lumière. La texture,
## elle, porte déjà ses propres canaux quasi blancs sur un fond noir — 2,5 par-dessus les fait
## sortir de la plage, le bloom achève le travail, et l'artère devient une barre BLANCHE. Elle
## perd alors sa couleur, c'est-à-dire son appartenance à l'Unisson. Vu en capture.
##
## ⚠️ Et l'enjeu n'est pas que l'ambiance : les signaux que le moteur pose PAR-DESSUS — le bulbe
## d'un nœud d'épine, le couvercle d'un puits — doivent rester distinguables de la matière. Une
## artère saturée les noie, et le joueur ne voit plus ce qu'il a détruit.
const EMISSIVE_ENERGY := 1.0

static func _skin_emissive(base: StandardMaterial3D) -> StandardMaterial3D:
	var map := _map(EMISSIVE_MAP, "")
	if map == null:
		return null
	var tuned: StandardMaterial3D = base.duplicate()
	tuned.uv1_scale = Vector3(HULL_UV_SCALE, HULL_UV_SCALE, HULL_UV_SCALE)
	tuned.albedo_texture = map
	tuned.emission_enabled = true
	tuned.emission_texture = map
	tuned.emission_energy_multiplier = EMISSIVE_ENERGY
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
