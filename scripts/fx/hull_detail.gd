class_name HullDetail
## Plaque une carte de detail sur une coque .glb, SANS toucher a sa palette.
##
## Les coques sont du hard-surface PBR sans texture (ADR-0008), et lisaient
## « jouet » : de grandes surfaces lisses entre quelques panneaux. ADR-0011
## autorise des feuilles de detail repetables en niveaux de gris. Celle-ci
## (`hull_detail_mul.png`) est une CARTE DE MULTIPLICATION : les plaques y valent
## ~1.0 (blanc, donc neutre), les rainures et rivets < 1.0.
##
## Godot calcule `albedo = albedo_texture x albedo_color`. En posant la carte comme
## `albedo_texture` et en GARDANT la couleur de palette importee du .glb, les
## plaques conservent exactement leur teinte et seules les rainures se creusent.
## Aucune couleur n'est recopiee cote Godot : la palette vient du .glb, qui la
## tient du kit — une seule source de verite.
##
## Volontairement une fonction statique, comme SoftDot/FlameStreak : appelable de
## partout, aucun etat.

const DETAIL_MAP := preload("res://assets/imported/textures/hull/hull_detail_mul.png")

## Relief, ajoute apres coup (ADR-0013). La carte de multiplication PEINT des
## rainures ; elle n'en creuse pas — la lumiere ne les voit pas, et la coque reste
## un aplat quelle que soit la finesse du dessin. Ces trois cartes sont DERIVEES de
## la meme feuille de hauteur par `tools/derive-maps.py`, jamais generees.
##
## La feuille de greebles du depot n'est PAS derivee ici : son tuilage mesure 16 %
## d'ecart au bord (contre 1,3 % pour les panneaux), soit une couture franche tous
## les 42 cm sur la coque. A regenerer avant de s'en servir.
const DETAIL_NRM := preload("res://assets/imported/textures/hull/hull_panels_nrm.png")
const DETAIL_ROUGH := preload("res://assets/imported/textures/hull/hull_panels_rough.png")
const DETAIL_AO := preload("res://assets/imported/textures/hull/hull_panels_ao.png")

## Relief discret : une coque de chasseur est lisse, ses rainures sont des traits,
## pas des tranchees. A 1,5 le Specter-9 prenait un aspect martele.
const NORMAL_SCALE := 0.7

## < 1.0 agrandit les plaques (moins de repetitions). Regle au rendu.
##
## Passe de 0,6 a 0,25 le jour ou le RELIEF est arrive. A 0,6 les UV valent 2,4
## tuiles/m, soit une plaque de 6 cm : la carte de multiplication seule s'y noyait
## sans dommage, mais une normale a cette finesse transforme la coque en velours
## cotele — un moire de rainures qui n'a plus rien d'une ligne de panneau.
## A 0,25, la plaque fait 14 cm et redevient une plaque.
## Meme lecon que le tuilage des greebles de la citadelle : le detail fin ne se
## noie pas seulement, il MENT.
const DETAIL_TILING := 0.25

## Materiaux qui recoivent le detail. Le verre (fenetre lisse) et l'emissif
## (lueur de tuyere) en sont EXCLUS : une carte de plaques n'a aucun sens sur eux,
## et creuserait des rainures dans une vitre ou un feu.
const _DETAILED := {
	"AA_Hull": true, "AA_Panel": true, "AA_Trim": true,
	"AA_Greeble": true, "AA_Marking_Red": true,
}

## `hull` : le Node3D instancie du .glb (typiquement le nœud "Hull"). On descend
## chercher chaque MeshInstance3D et on retexture ses surfaces en place.
static func apply(hull: Node) -> void:
	for mesh in _meshes(hull):
		for i in mesh.get_surface_override_material_count():
			var base := mesh.get_active_material(i) as StandardMaterial3D
			if base == null or not _DETAILED.has(base.resource_name):
				continue
			# On DUPLIQUE : le materiau importe est partage entre toutes les
			# instances du .glb (les 4 vaisseaux de l'accueil, le joueur). Le
			# muter en place les changerait tous — et surtout, on ne veut pas
			# ecrire dans la ressource importee.
			var tuned: StandardMaterial3D = base.duplicate()
			tuned.albedo_texture = DETAIL_MAP
			tuned.normal_enabled = true
			tuned.normal_texture = DETAIL_NRM
			tuned.normal_scale = NORMAL_SCALE
			tuned.roughness_texture = DETAIL_ROUGH
			tuned.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
			tuned.ao_enabled = true
			tuned.ao_texture = DETAIL_AO
			tuned.ao_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
			# 0 = l'AO n'assombrit que l'ambiante ; au-dela elle mange la lumiere
			# directe et la coque vire au gris sale sous la cle.
			tuned.ao_light_affect = 0.0
			# Les UV sont a 4 tuiles/m (box_project_uv). A cette densite, sur une
			# petite coque et sous le post-process retro (960x540 + scanlines), les
			# plaques deviennent trop fines et lisent comme du bruit raye. On elargit
			# les plaques d'un facteur ~2.5 pour qu'elles survivent au downsampling.
			tuned.uv1_scale = Vector3(DETAIL_TILING, DETAIL_TILING, DETAIL_TILING)
			mesh.set_surface_override_material(i, tuned)

static func _meshes(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	var mesh := node as MeshInstance3D
	if mesh != null:
		out.append(mesh)
	for child in node.get_children():
		_meshes(child, out)
	return out
