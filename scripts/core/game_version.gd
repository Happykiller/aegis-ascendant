class_name GameVersion
## La version du jeu : UN seul chiffre, lu là où il est écrit.
##
## ⚠️ IL EXISTE PARCE QUE LE LIVRABLE A COMMENCÉ À CIRCULER. Tant que le jeu ne sortait pas
## du dépôt, « la version » était le hash du dernier commit et personne n'en avait besoin.
## Depuis qu'on publie des `.exe` (`scripts/release.sh`), un testeur qui rapporte un défaut
## doit pouvoir dire SUR QUOI il l'a vu, et nous devons pouvoir le retrouver.
##
## La source de vérité est `application/config/version` dans `project.godot` — celle que
## Godot grave dans les métadonnées de l'exécutable Windows. Tout le reste la LIT :
## l'écran-titre, l'écran de pause, et `release.sh` qui refuse de publier un tag qui ne lui
## correspond pas. Une version recopiée quelque part serait une version qui finirait par
## mentir.

const SETTING := "application/config/version"

## Ce que le projet déclare, ou "0.0.0" si le réglage a disparu — un écran ne plante pas
## pour une version manquante.
static func current() -> String:
	return str(ProjectSettings.get_setting(SETTING, "0.0.0"))

## `MAJEUR.MINEUR.CORRECTIF` et rien d'autre. Godot n'impose aucune forme ; nous si, parce
## que le tag GitHub `vX.Y.Z` en est dérivé, et qu'un tag ne se corrige pas après coup.
static func is_semver(version: String) -> bool:
	var parts := version.split(".")
	if parts.size() != 3:
		return false
	for part in parts:
		if part.is_empty() or not part.is_valid_int() or part.to_int() < 0:
			return false
		# "01" et "1" désigneraient la même version avec deux tags différents.
		if part.length() > 1 and part.begins_with("0"):
			return false
	return true

## Ce qui s'affiche à l'écran. Le mot « prototype » fait partie de l'identité du produit
## tant que le jeu n'a pas atteint 1.0 : il dit au testeur ce qu'il tient dans les mains.
static func label() -> String:
	var version := current()
	return "v%s — prototype" % version if version.begins_with("0.") else "v%s" % version
