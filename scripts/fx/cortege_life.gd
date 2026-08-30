class_name CortegeLife
extends Node
## Habille une coque du Long Cortège avec SES pièces, pour le bestiaire.
##
## ⚠️ IL EXISTE PARCE QUE `CitadelLife` AURAIT VISSÉ DES TOURELLES HELIOS SUR UNE COQUE DU NULL
## CHOIR. L'écran du bestiaire monte `CitadelLife` sur toute fiche de famille `FORTRESS` — c'était
## sans conséquence tant que la seule forteresse du jeu était l'Aegis Citadel. Appliqué au
## Cortège, il aurait instancié `citadel_turret.tscn` sur ses dix-sept marqueurs `Turret_` : une
## fiche parfaitement lisible, parfaitement animée, et qui aurait montré au joueur l'armement de
## SON camp sur le vaisseau d'en face. Rien ne l'aurait signalé.
##
## ⚠️ ET IL MONTE LES VRAIES PIÈCES DU NIVEAU, pas des maquettes. `CortegeTurret` et
## `CortegeSpineNode` construisent leur affût dans `_ready()` à partir des kits de la forge, sans
## rien demander à un `BulletManager` ni à un joueur : les instancier ici donne exactement ce que
## le joueur survole, et une reforge de kit met la fiche à jour toute seule. Une maquette aurait
## divergé au premier brief.
##
## ⚠️ LES PIÈCES NE SONT PAS ANIMÉES ICI, ET C'EST VOULU. Leur mouvement — la rotation d'un canon,
## la pulsation d'un nœud — est piloté par `CortegeHardpoints`, qui a besoin d'un point de visée
## dans le plan de jeu. Le bestiaire n'a pas de plan de jeu. Les faire respirer demanderait de
## dupliquer cette logique, donc d'entretenir deux vérités sur la même pièce.

const TuningResource := preload("res://resources/levels/long_cortege_tuning.tres")
const TurretScript := preload("res://scripts/gameplay/cortege_turret.gd")
const NodeScript := preload("res://scripts/gameplay/cortege_spine_node.gd")

## Pose les tourelles et les nœuds d'épine sur les marqueurs de la coque.
##
## ⚠️ LES MARQUEURS SONT ENFANTS DES TRONÇONS, PAS DE LA COQUE. Le `.glb` porte cinq `Section_NN`
## qui portent chacun leurs `Turret_NN` et `Spine_NN` : chercher les marqueurs à la racine ne
## trouverait rien, en silence, et la fiche montrerait un vaisseau désarmé.
static func apply(hull: Node3D) -> void:
	if hull == null:
		return
	var section := 0
	for child in hull.get_children():
		if not String(child.name).begins_with("Section_"):
			continue
		var serial := 0
		for marker in child.get_children():
			var anchor := marker as Node3D
			if anchor == null:
				continue
			var name := String(anchor.name)
			if name.begins_with("Turret_"):
				var turret := TurretScript.make(TuningResource, section)
				turret.serial = serial
				turret.setup(null, null, null)
				anchor.add_child(turret)
				serial += 1
			elif name.begins_with("Spine_"):
				var node := NodeScript.make(TuningResource, section)
				node.setup(null, null)
				anchor.add_child(node)
		section += 1
