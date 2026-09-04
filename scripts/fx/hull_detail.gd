class_name HullDetail
## Plaque un jeu de cartes de detail sur une coque .glb, SANS toucher a sa palette.
##
## Les coques sont du hard-surface PBR sans texture (ADR-0008), et lisaient
## « jouet » : de grandes surfaces lisses entre quelques panneaux. ADR-0011
## autorise des feuilles de detail repetables en niveaux de gris. La carte de
## multiplication d'un jeu (`HullDetailSet.mul`) vaut ~1.0 sur les plaques (blanc,
## donc neutre) et < 1.0 dans les rainures et rivets.
##
## Godot calcule `albedo = albedo_texture x albedo_color`. En posant la carte comme
## `albedo_texture` et en GARDANT la couleur de palette importee du .glb, les
## plaques conservent exactement leur teinte et seules les rainures se creusent.
## Aucune couleur n'est recopiee cote Godot : la palette vient du .glb, qui la
## tient du kit — une seule source de verite.
##
## UN JEU PAR COQUE (ADR-0044 §4). Le jeu partage (`hull_detail_default.tres`) sert
## toute coque qui n'en declare pas ; la cellule-temoin a le sien, cale pour le gros
## plan. Le jeu se RESOUT depuis le chemin de scene de la coque instanciee : l'appelant
## n'a rien a savoir, `apply(hull)` reste l'API partout.
##
## ET DEUX MATIERES DANS UN JEU : la coque, et ses tuyeres. Les sept materiaux `AA_*`
## sont imposes, un huitieme n'existe pas — la matiere de tuyere n'est possible que
## parce que `Nozzle_*` et `Petal_*` sont des NOEUDS separes. Le choix se fait par le
## nom du noeud, pas par le materiau.
##
## Volontairement une fonction statique, comme SoftDot : appelable de
## partout, aucun etat.

const DEFAULT_SET: HullDetailSet = preload("res://resources/player/hull_detail_default.tres")

## Les jeux dedies, par NOM DE FICHIER de la coque (`scene_file_path` du .glb
## instancie). Une coque absente d'ici recoit le jeu partage. ⚠️ La cle est le nom
## de fichier, pas le chemin complet : une coque montee via une scene d'ajustement
## (`specter_9_b.tscn`) garde son .glb comme racine et c'est lui qu'on lit.
const SETS: Dictionary = {}

## Materiaux qui recoivent le detail. Le verre (fenetre lisse) et l'emissif
## (lueur de tuyere) en sont EXCLUS : une carte de plaques n'a aucun sens sur eux,
## et creuserait des rainures dans une vitre ou un feu.
const _DETAILED := {
	"AA_Hull": true, "AA_Panel": true, "AA_Trim": true,
	"AA_Greeble": true, "AA_Marking_Red": true,
}

## Le jeu qu'une coque doit recevoir. Statique et pure : c'est ce que le test verifie.
static func set_for(scene_path: String) -> HullDetailSet:
	var chosen: HullDetailSet = SETS.get(scene_path.get_file())
	return chosen if chosen != null else DEFAULT_SET

## `hull` : le Node3D instancie du .glb (typiquement le nœud "Hull"). On descend
## chercher chaque MeshInstance3D et on retexture ses surfaces en place.
## `detail` : le jeu a poser ; `null` = resolu depuis la coque elle-meme.
static func apply(hull: Node, detail: HullDetailSet = null) -> void:
	if hull == null:
		return
	if detail == null:
		detail = set_for(hull.scene_file_path)
	for mesh in _meshes(hull):
		var on_nozzle := detail.has_nozzle_set() and _under_nozzle(mesh, hull)
		for i in mesh.get_surface_override_material_count():
			var base := mesh.get_active_material(i) as StandardMaterial3D
			if base == null or not _DETAILED.has(base.resource_name):
				continue
			# On DUPLIQUE : le materiau importe est partage entre toutes les
			# instances du .glb (les 4 vaisseaux de l'accueil, le joueur). Le
			# muter en place les changerait tous — et surtout, on ne veut pas
			# ecrire dans la ressource importee.
			var tuned: StandardMaterial3D = base.duplicate()
			if on_nozzle:
				_dress(tuned, detail.nozzle_mul, detail.nozzle_normal, detail.nozzle_roughness,
					detail.nozzle_ao, detail.nozzle_normal_scale, detail.nozzle_tiling)
			else:
				_dress(tuned, detail.mul, detail.normal, detail.roughness, detail.ao,
					detail.normal_scale, detail.tiling)
			mesh.set_surface_override_material(i, tuned)

static func _dress(tuned: StandardMaterial3D, mul: Texture2D, normal: Texture2D,
		roughness: Texture2D, ao: Texture2D, normal_scale: float, tiling: float) -> void:
	tuned.albedo_texture = mul
	tuned.normal_enabled = true
	tuned.normal_texture = normal
	tuned.normal_scale = normal_scale
	tuned.roughness_texture = roughness
	tuned.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	tuned.ao_enabled = true
	tuned.ao_texture = ao
	tuned.ao_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	# 0 = l'AO n'assombrit que l'ambiante ; au-dela elle mange la lumiere
	# directe et la coque vire au gris sale sous la cle.
	tuned.ao_light_affect = 0.0
	# Les UV du .glb sont metriques (box_project_uv). Le facteur elargit ou resserre
	# les plaques pour qu'elles survivent au post-process retro (960x540 + scanlines) :
	# a 4 tuiles/m sur une petite coque, 0,25 fait une plaque de 14 cm.
	tuned.uv1_scale = Vector3(tiling, tiling, tiling)

## Un maillage est « de tuyere » si lui ou l'un de ses ancetres sous la coque porte un
## nom de tuyere ou de petale. Le .glb nomme ses noeuds d'apres les pieces mobiles du
## kit ; un maillage de tuyere s'appelle `Nozzle_L`, ou pend sous lui.
static func _under_nozzle(mesh: Node, hull: Node) -> bool:
	var node: Node = mesh
	while node != null and node != hull:
		if node.name.begins_with("Nozzle_") or node.name.begins_with("Petal_"):
			return true
		node = node.get_parent()
	return false

static func _meshes(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	var mesh := node as MeshInstance3D
	if mesh != null:
		out.append(mesh)
	for child in node.get_children():
		_meshes(child, out)
	return out
