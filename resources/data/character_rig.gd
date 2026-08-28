class_name CharacterRig
extends Resource
## Le gréement d'un personnage : où poser chacun de ses calques (`ADR-0035`).
##
## Les valeurs sont exprimées sur une **toile de référence** — celle des fichiers livrés — et
## l'affichage les ramène ensuite à sa propre taille. C'est ce qui permet au même gréement de
## servir l'accueil pied-en-cap, le HUD et le briefing sans être retouché.

## La toile sur laquelle les placements sont écrits. Tous les calques la partagent.
@export var canvas: Vector2 = Vector2(1024.0, 1536.0)
@export var layers: Array[LayerPose] = []

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if canvas.x <= 0.0 or canvas.y <= 0.0:
		errors.append("canvas doit être positif")
	if layers.is_empty():
		errors.append("aucun placement")
	var vus := {}
	var echelles := {}
	for i in layers.size():
		var pose := layers[i]
		if pose == null:
			errors.append("layers[%d] est nul" % i)
			continue
		for error in pose.validate():
			errors.append("layers[%d] : %s" % [i, error])
		if pose.layer != &"":
			if vus.has(pose.layer):
				errors.append("layers[%d] : le calque `%s` est déjà placé par layers[%d]"
					% [i, pose.layer, vus[pose.layer]])
			vus[pose.layer] = i
		# ⚠️ UN GROUPE PARTAGE SON PLACEMENT. Ses pièces ont été dessinées ensemble : deux
		# valeurs différentes dans un même groupe sont une faute de saisie, pas un réglage —
		# et elles désaligneraient des pièces qui, elles, sont co-enregistrées.
		if pose.group != &"":
			var signature := "%.5f|%.2f|%.2f" % [pose.scale, pose.offset.x, pose.offset.y]
			if echelles.has(pose.group) and echelles[pose.group] != signature:
				errors.append("layers[%d] : `%s` s'écarte de son groupe `%s` (%s contre %s)"
					% [i, pose.layer, pose.group, signature, echelles[pose.group]])
			echelles[pose.group] = signature
	return errors

func pose_of(layer: StringName) -> LayerPose:
	for pose in layers:
		if pose != null and pose.layer == layer:
			return pose
	return null

## L'emprise de la figure assemblée, en pixels de la toile de référence. C'est elle que
## l'affichage cadre — pas la toile, qui est bien plus grande que le sujet.
##
## ⚠️ Calculée sur les BOÎTES DE TOILE et non sur l'alpha : le module ne lit pas les pixels,
## et une emprise qui dépendrait du contenu changerait au premier calque retouché.
func bounds() -> Rect2:
	var union := Rect2()
	var premier := true
	for pose in layers:
		if pose == null:
			continue
		var origin := canvas * 0.5 * (1.0 - pose.scale) + pose.offset
		var rect := Rect2(origin, canvas * pose.scale)
		union = rect if premier else union.merge(rect)
		premier = false
	return union
