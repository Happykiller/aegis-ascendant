class_name CodexEntry
extends Resource
## Une fiche du bestiaire : une coque, sa fiction, et un POINTEUR vers ses valeurs
## de jeu — jamais une copie de ces valeurs.
##
## POURQUOI DES POINTEURS ET PAS DES CHIFFRES — recopier ici les 20 PV du Needle
## Scout créerait une deuxième source de vérité, et le bestiaire mentirait au premier
## rééquilibrage venu, sans que rien ne le signale. La fiche référence donc la
## Resource de gameplay et lit dedans. Même raisonnement pour les dimensions : elles
## ne sont PAS un champ, elles se mesurent sur la boîte englobante de la coque
## affichée (`CodexScreen._hull_bounds`).
##
## Ne reste en dur que ce qui n'existe nulle part ailleurs, parce que c'est de la
## fiction : désignation, classe, constructeur, masse, équipage, statut, notice
## (BRIEF-0037).

## Camp d'appartenance. Pilote la couleur d'accent de la fiche — cyan Helios ou
## magenta Null Choir (charte §3).
enum Camp { HELIOS, NULL_CHOIR }

@export var display_name: String = ""
@export var camp: Camp = Camp.NULL_CHOIR

@export_group("Fiche (fiction — BRIEF-0037)")
## Champs COURTS : affichés tout en capitales, donc en ASCII sans accent. Press
## Start 2P dessine les capitales accentuées en hauteur de bas-de-casse, et un `É`
## troue le mot (ADR-0012).
@export var designation: String = ""
@export var hull_class: String = ""
@export var builder: String = ""
@export var status: String = ""
## Notice : affichée en casse normale, les minuscules accentuées y sont correctes.
@export_multiline var notice: String = ""
@export var mass_t: float = 0.0
@export var crew: int = 0

@export_group("Modele")
## La coque `.glb` mise en scène. C'est elle, et elle seule, qui donne les dimensions.
@export var hull_scene: PackedScene
## Distance de cadrage (m). 0 = déduite de la taille de la coque, ce qui est le cas
## normal ; ne la forcer que si une coque très creuse se cadre mal toute seule.
@export var frame_distance: float = 0.0

@export_group("Source des valeurs de jeu — exactement UNE")
@export var player_stats: PlayerStats
@export var enemy_data: EnemyData
## Les boss ne portent pas de Resource : leurs valeurs sont des `@export` posés sur
## la scène de gameplay. On les lit SANS instancier (voir `_scene_value`).
@export var boss_scene: PackedScene

@export_group("Variantes")
## Profils de vol partageant cette coque. Le Needle Scout en a huit : les faire
## défiler comme huit fiches montrerait huit fois le même modèle.
@export var variants: Array[EnemyData] = []

# --- Lecture des valeurs de jeu -----------------------------------------------
# Zéro n'est jamais une valeur affichable ici : il signifie « cette coque n'a pas
# cette caractéristique », et la fiche écrit un tiret plutôt qu'un faux chiffre.

## Points de structure.
func hull_points() -> float:
	if player_stats != null:
		return player_stats.shield_max
	if enemy_data != null:
		return enemy_data.max_health
	return _scene_float(boss_scene, &"max_health")

## Vitesse de déplacement (unités/s). Les boss dérivent au lieu d'avancer : ils n'en
## ont pas, et la fiche le dit.
func speed() -> float:
	if player_stats != null:
		return player_stats.max_speed
	if enemy_data != null:
		return enemy_data.move_speed
	return 0.0

## Secondes entre deux tirs.
func fire_interval() -> float:
	if player_stats != null:
		return player_stats.fire_interval
	if enemy_data != null:
		return enemy_data.fire_interval
	return _scene_float(boss_scene, &"fire_interval")

## Rayon de la zone de touche logique (unités).
func hitbox_radius() -> float:
	if player_stats != null:
		return player_stats.hitbox_radius
	if enemy_data != null:
		return enemy_data.hitbox_radius
	return _scene_float(boss_scene, &"hitbox_radius")

## Points marqués à la destruction. Le joueur n'en rapporte évidemment aucun.
func score_value() -> int:
	if enemy_data != null:
		return enemy_data.score_value
	return 0

## Nombre de phases — un boss seulement.
func phase_count() -> int:
	if boss_scene == null:
		return 0
	return int(_scene_float(boss_scene, &"phase_count"))

# --- Validation ---------------------------------------------------------------

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if display_name.is_empty():
		errors.append("display_name is required")
	if hull_scene == null:
		errors.append("hull_scene is required (it carries the dimensions)")
	var sources := 0
	if player_stats != null:
		sources += 1
	if enemy_data != null:
		sources += 1
	if boss_scene != null:
		sources += 1
	if sources != 1:
		# Deux sources, ce sont deux vérités concurrentes ; zéro, c'est une fiche
		# muette. Les deux sont des erreurs de câblage, pas des cas dégradés.
		errors.append("exactly one stats source expected (player_stats / enemy_data / boss_scene), got %d" % sources)
	if mass_t < 0.0:
		errors.append("mass_t must be >= 0")
	if crew < 0:
		errors.append("crew must be >= 0")
	if frame_distance < 0.0:
		errors.append("frame_distance must be >= 0")
	for field: Array in [["designation", designation], ["hull_class", hull_class],
			["builder", builder], ["status", status]]:
		var value: String = field[1]
		if _has_non_ascii(value):
			errors.append("%s must be pure ASCII (Press Start 2P, ADR-0012): %s" % [field[0], value])
	errors.append_array(_validate_stats_source())
	return errors

func _validate_stats_source() -> PackedStringArray:
	# La fiche ne revalide pas les Resources de gameplay dans le détail — elles ont
	# leur propre validate() et leurs propres tests. On vérifie seulement qu'elle en
	# tire de quoi remplir la ligne principale.
	var errors := PackedStringArray()
	if hull_points() <= 0.0:
		errors.append("hull_points resolved to %s — stats source is empty or mis-wired" % hull_points())
	return errors

## Les champs courts partent en capitales dans une police qui n'a pas de capitale
## accentuée lisible : un accent y est un défaut d'affichage, pas un détail.
static func _has_non_ascii(value: String) -> bool:
	for i in value.length():
		if value.unicode_at(i) > 127:
			return true
	return false

## Lit un `@export` sur le nœud racine d'une scène SANS l'instancier.
##
## ⚠️ Instancier `choir_harvester.tscn` ferait tourner `boss_controller._ready()` —
## c'est-à-dire du gameplay complet (entrée en scène, tirs, recherche du
## BulletManager) dans un écran de menu. `SceneState` donne accès aux valeurs
## sérialisées sans rien construire, ce qui est exactement ce qu'on veut.
static func _scene_float(scene: PackedScene, property: StringName) -> float:
	if scene == null:
		return 0.0
	var state := scene.get_state()
	if state == null or state.get_node_count() == 0:
		return 0.0
	for i in state.get_node_property_count(0):
		if state.get_node_property_name(0, i) == property:
			return float(state.get_node_property_value(0, i))
	return 0.0
