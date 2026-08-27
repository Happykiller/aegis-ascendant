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

## Angle mort mesuré le 2026-08-27 aux canons de nez : **0,90 u**. Fermé le même jour en
## faisant naître le bolt sur l'axe du chasseur (`BOLT_FORWARD_OFFSET`). Il doit le rester.
const DEAD_ZONE_LIMIT := 0.0

func _nose_offset() -> float:
	var hull := track(HULL.instantiate()) as Node3D
	var node := hull.get_node_or_null(NodePath("Muzzle_L")) as Node3D
	assert_true(node != null, "la coque livrée porte bien Muzzle_L")
	if node == null:
		return 0.0
	# Même projection que le contrôleur : le monde -Z est le haut de l'écran.
	return -node.position.z

## L'angle mort vient d'une addition simple, et chacun de ses termes peut bouger tout
## seul : l'avance du point de naissance, la vitesse de l'arme, le rayon de la cible.
func test_there_is_no_blind_spot_in_front_of_the_nose() -> void:
	# La balle est déplacée AVANT le premier test de collision (`BulletManager.step()` :
	# on avance, puis `_resolve_hits`). Sa première position testée est donc déjà en avant.
	var first_test := PlayerFighterController.BOLT_FORWARD_OFFSET + PULSE.speed * TICK
	var reach := PULSE.radius + SCOUT.hitbox_radius
	var dead_zone := maxf(0.0, first_test - reach)
	assert_true(dead_zone <= DEAD_ZONE_LIMIT,
		"angle mort de %.2f u (naissance à %.2f, premier test à %.2f, portée %.2f)"
			% [dead_zone, PlayerFighterController.BOLT_FORWARD_OFFSET, first_test, reach])

## Le bolt ne naît PLUS au bout du canon, et l'écart n'est pas un détail : c'est la
## distance sur laquelle il traverse la coque avant d'en sortir. Mesurée ici pour qu'une
## coque re-exportée avec un nez plus long ne l'allonge pas en silence.
func test_the_flash_stays_on_the_gun_and_the_bolt_does_not() -> void:
	var muzzle := _nose_offset()
	assert_true(muzzle > PlayerFighterController.BOLT_FORWARD_OFFSET,
		"le canon (%.2f u) est bien en avant du point de naissance (%.2f u)"
			% [muzzle, PlayerFighterController.BOLT_FORWARD_OFFSET])
	var crossing := (muzzle - PlayerFighterController.BOLT_FORWARD_OFFSET) / PULSE.speed
	assert_true(crossing <= 0.060,
		"le bolt sort du nez en %.0f ms — au-delà, il se voit naître DANS la coque"
			% (crossing * 1000.0))

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
