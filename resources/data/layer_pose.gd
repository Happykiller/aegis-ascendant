class_name LayerPose
extends Resource
## Où poser UN calque de personnage, sur la toile de référence de son gréement.
##
## ⚠️ CE FICHIER EXISTE PARCE QU'UN GÉNÉRATEUR D'IMAGES NE SAIT PAS CO-ENREGISTRER. Le
## contrat `CHR-0001` exigeait « même toile, même cadrage, même origine » ; la livraison du
## 2026-08-28 a rendu dix fichiers de 1024×1536 dont l'empilement était **faux** — une tête de
## 907 px pour un corps de 1460. Chaque pièce est dessinée à sa propre échelle, cadrée pour
## remplir sa toile : le modèle ne sait pas qu'il dessine la pièce d'un puzzle.
##
## La contrainte était donc impossible à tenir, et le contrôle de dimensions la faisait passer
## pour respectée. On a changé de côté : le générateur livre des pièces indépendantes, et
## c'est le JEU qui les assemble. Un réglage se corrige en trente secondes ; une planche se
## regénère en une heure et retombe sur le même écueil.

## Le nom du calque, tel que le fichier s'appelle.
@export var layer: StringName = &""
## Le groupe dont il vient. **Documentaire, mais pas décoratif** : les pièces d'un même groupe
## ont été dessinées ensemble, donc elles PARTAGENT échelle et décalage. Deux valeurs qui
## divergent dans un groupe sont un signe d'erreur de saisie, pas un réglage fin.
@export var group: StringName = &""
## Facteur appliqué autour du CENTRE de la toile de référence.
@export var scale: float = 1.0
## Translation, en pixels de la toile de référence, appliquée après l'échelle.
@export var offset: Vector2 = Vector2.ZERO

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if layer == &"":
		errors.append("layer est vide — un placement désigne un calque")
	if scale <= 0.0:
		errors.append("scale (%.3f) doit être > 0" % scale)
	return errors
