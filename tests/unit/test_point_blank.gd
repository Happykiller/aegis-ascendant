extends "res://tests/test_case.gd"
## Peut-on toucher un ennemi collé au nez ? (`LOI-ENN-04`)
##
## Le genre en fait une faute nommée : « une unité qu'on ne peut plus atteindre parce
## qu'on est trop près est une punition sans lecture ». Chez nous la question est plus
## grave qu'ailleurs, parce que **rien ne pousse le joueur à s'écarter** : un chasseur
## ordinaire n'inflige aucun dégât de contact (seuls la sangsue, la mine et les pièces de
## boss le font). Une unité posée dans l'angle mort y resterait **inoffensive ET
## invulnérable** — une impasse dont le joueur ne peut pas déduire la règle.
##
## ⚠️ CE FICHIER NE PROUVE PAS QUE TOUT VA BIEN. Il MESURE l'angle mort et le borne :
## il rougit le jour où une retouche de coque, de vitesse ou de rayon l'agrandit.

const PlayerScene := preload("res://scenes/player/player_fighter.tscn")
const HULL := preload("res://assets/imported/models/ships/specter_9.glb")
const PULSE: ProjectileData = preload("res://resources/weapons/pulse_shot.tres")
const SCOUT: EnemyData = preload("res://resources/enemies/needle_scout.tres")

## Cadence physique du projet (défaut moteur, aucune surcharge dans project.godot).
const TICK := 1.0 / 60.0

## Angle mort MESURÉ le 2026-08-27 : 0,90 unité devant le centre du chasseur, aux canons
## de nez. La borne laisse une marge de 15 % ; au-delà, ce n'est plus la même géométrie et
## il faut le regarder, pas le rattraper.
const DEAD_ZONE_LIMIT := 1.04

func _nose_offset() -> float:
	var hull := track(HULL.instantiate()) as Node3D
	var node := hull.get_node_or_null(NodePath("Muzzle_L")) as Node3D
	assert_true(node != null, "la coque livrée porte bien Muzzle_L")
	if node == null:
		return 0.0
	# Même projection que le contrôleur : le monde -Z est le haut de l'écran.
	return -node.position.z

## L'angle mort vient d'une addition simple, et chacun de ses trois termes peut bouger
## tout seul : la coque (la position du canon), l'arme (sa vitesse), le bestiaire (le
## rayon de la cible).
func test_the_nose_blind_spot_stays_within_its_measured_bound() -> void:
	var muzzle := _nose_offset()
	# La balle est déplacée AVANT le premier test de collision (`BulletManager.step()` :
	# on avance, puis `_resolve_hits`). Sa première position testée est donc déjà en avant.
	var first_test := muzzle + PULSE.speed * TICK
	var reach := PULSE.radius + SCOUT.hitbox_radius
	var dead_zone := maxf(0.0, first_test - reach)
	assert_true(dead_zone <= DEAD_ZONE_LIMIT,
		"angle mort de %.2f u devant le chasseur (canon à %.2f, premier test à %.2f, portée %.2f)"
			% [dead_zone, muzzle, first_test, reach])

## Les canons d'aile et de bout d'aile sont modélisés DERRIÈRE le centre du chasseur.
## Conséquence non évidente et qui vaut d'être écrite : l'angle mort du nez se referme en
## montant en puissance — le joueur le subit donc exactement quand il est le plus faible.
func test_the_wing_guns_start_behind_the_nose() -> void:
	var hull := track(HULL.instantiate()) as Node3D
	for gun in ["Muzzle_Wing_L", "Muzzle_Wing_R", "Muzzle_Tip_L", "Muzzle_Tip_R"]:
		var node := hull.get_node_or_null(NodePath(gun)) as Node3D
		assert_true(node != null, "%s existe" % gun)
		if node == null:
			continue
		assert_true(-node.position.z < _nose_offset(),
			"%s tire de plus près que le nez" % gun)
