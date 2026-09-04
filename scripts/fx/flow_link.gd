class_name FlowLink
## Un lien fait de POINTS QUI DÉFILENT entre deux unités — pas un trait plein.
##
## ⚠️ POURQUOI IL EXISTE. Première version du lien du porteur de bouclier : un ruban plein.
## Verdict de l'opérateur en jouant : « pas de trait grossier comme ça, les liens que ce
## soit pour lui ou la mine attractive on pourrait plutôt utiliser un effet de particule ».
## Il avait raison, et pour la raison qu'on avait déjà écrite le matin même — un trait plein
## est du CARTON : il ne dit ni sens, ni mouvement, ni intensité.
##
## ⚠️ ET IL AVAIT MAL LU CE TRAIT, ce qui est pire qu'un défaut esthétique. Il l'a compris
## comme « on me ralentit », alors que le porteur rend ses VOISINS invulnérables et ne
## touche pas le joueur. Un signe qui se fait mal comprendre est plus dangereux qu'un signe
## absent : il enseigne une règle fausse. D'où le SENS DU DÉFILEMENT, qui est ici l'essentiel
## — les points remontent des protégés VERS le porteur, donc « c'est lui qui les tient ».
##
## LA TECHNIQUE, et pourquoi ce n'est pas un système de particules. Un `GPUParticles3D` par
## lien coûterait un émetteur par unité couverte, à recréer quand la liste change. Ici un
## seul quad porte `SoftDot` RÉPÉTÉE le long de sa longueur, et c'est le décalage d'UV qu'on
## anime : les points défilent sans qu'aucune particule n'existe. Zéro allocation, un
## `draw call` par lien, et le même outil sert au rayon tracteur du Null Maw.

## Combien de points par unité monde. Plus haut, plus le chapelet est serré.
const DOTS_PER_UNIT := 0.55

## Vitesse de défilement, en tours d'UV par seconde. ⚠️ NÉGATIVE : la texture défile dans le
## sens inverse de l'offset, et un chapelet qui remonte à l'envers dirait le contraire de ce
## qu'on veut faire lire.
const FLOW_SPEED := -1.6


## Monte un lien, éteint. Le matériau lui appartient : deux liens de teintes différentes ne
## doivent pas se le partager.
static func build(tint: Color, width: float, energy: float) -> MeshInstance3D:
	var quad := QuadMesh.new()
	quad.size = Vector2(1.0, 1.0)
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	material.albedo_texture = SoftDot.texture()
	material.albedo_color = tint
	material.emission_enabled = true
	material.emission = tint
	material.emission_energy_multiplier = energy
	# Le chapelet se répète le long de la longueur ; en travers, un seul point.
	material.uv1_scale = Vector3(1.0, 1.0, 1.0)
	var node := MeshInstance3D.new()
	node.mesh = quad
	node.material_override = material
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	node.visible = false
	# ⚠️ `top_level` : le lien est posé en coordonnées MONDE et ne doit PAS subir la
	# transformation de l'unité qui le porte, laquelle bouge sous lui.
	node.top_level = true
	return node


## Tend le lien entre deux points du monde et fait défiler ses points.
##
## `age` fait avancer le chapelet ; `camera_basis` garde le ruban FACE À LA CAMÉRA — sans
## quoi son orientation autour de la corde reste arbitraire et on le voit par la tranche,
## donc presque pas. Défaut déjà payé sur ce même lien.
## ⚠️ `density` EXISTE PARCE QU'UN LIEN COURT NE SE LIT PAS COMME UN FLUX À LA DENSITÉ DES
## LONGS. `DOTS_PER_UNIT` a été réglée sur les liens du porteur, qui font des dizaines de mètres.
## Les conduits de la Citadelle en font 6,4 : à 0,55 point par mètre ils rendent TROIS gros
## lampions, vus en capture — deux lumières, pas une circulation. Le défaut est le pendant exact
## de celui que la largeur a payé : là c'était trop fin pour se voir, ici c'est trop gros pour
## dire quelque chose. Le défaut de ce paramètre garde tous les appelants existants inchangés.
static func aim(link: MeshInstance3D, from: Vector3, to: Vector3,
		camera_basis: Basis, width: float, age: float,
		density: float = DOTS_PER_UNIT) -> void:
	var span := from.distance_to(to)
	if link == null or span < 0.05:
		if link != null:
			link.visible = false
		return
	link.visible = true
	link.position = (from + to) * 0.5
	link.basis = MoonFlyby.billboard_basis(camera_basis, to - from, 0.0, span, width)
	var material := link.material_override as StandardMaterial3D
	if material == null:
		return
	var dots := maxf(span * density, 1.0)
	material.uv1_scale = Vector3(1.0, dots, 1.0)
	material.uv1_offset = Vector3(0.0, fmod(age * FLOW_SPEED, 1.0), 0.0)


## Combien de points porte un lien de cette longueur. Pure — c'est la seule chose de ce
## fichier qui se vérifie sans arbre de scène, et elle garde l'invariant qui compte : un
## lien court ne doit jamais tomber à zéro point, sinon il disparaît quand il devrait
## seulement raccourcir.
static func dot_count(span: float, density: float = DOTS_PER_UNIT) -> float:
	return maxf(span * density, 1.0)
