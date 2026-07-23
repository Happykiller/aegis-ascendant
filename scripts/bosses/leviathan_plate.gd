class_name LeviathanPlate
extends RefCounted
## Une plaque d'armure du Pale Leviathan : sa vie, sa place sur l'orbite, et le moment
## où elle encaisse (`docs/design/BOSS_PALE_LEVIATHAN.md` §3).
##
## LA MÉCANIQUE QU'ELLE PORTE — la fenêtre de tir naît d'une **géométrie**, pas d'un
## minuteur. Les quatre plaques sont enchâssées dans la coquille et défilent avec elle ;
## une plaque n'encaisse que lorsqu'elle passe dans l'arc face au joueur. Le reste du
## temps, le corps la masque et les tirs se réfléchissent.
##
## C'est la différence de nature avec l'iris du Harvester : là-bas la fenêtre était un
## **état** que le joueur provoquait ; ici c'est une **position** qu'il doit lire et
## anticiper. Il n'attend pas, il choisit son moment.
##
## RIEN NE REPOUSSE. Une plaque tombée est tombée — c'est le pilier du combat, et c'est
## ce qui rend la progression lisible sur la silhouette au lieu d'une jauge.
##
## `RefCounted` et non `Node` : ni arbre, ni `_process`, ni signaux. Le module la fait
## avancer dans son propre ordre, et elle reste instanciable à la main en test.

enum State { ALIVE, FALLING, DOWN }

## Identifie la plaque pour le module (`Plate_01`..`Plate_04`).
var index: int = 0
var state: State = State.ALIVE
var health: float = 0.0
var max_health: float = 0.0
## Position angulaire sur la coquille, en radians, **au repos**. Les quatre plaques
## sont réparties régulièrement : c'est cet écart qui garantit qu'il y a presque
## toujours une cible disponible, donc aucun temps mort dans la phase.
var base_angle: float = 0.0
## Nœud `Plate_0X` de la coque. Nul en test : une plaque sans nœud à poser reste une
## plaque qui vit, encaisse et tombe.
var node: Node3D
var rest_basis: Basis = Basis.IDENTITY
## Axe de chute, déduit de la position radiale — jamais saisi à la main. Même raison
## que les pétales du Harvester : `ak.moving_part()` pose l'origine sur la charnière
## sans réorienter les axes locaux.
var fall_axis: Vector3 = Vector3.RIGHT
var target: BulletTarget
var elapsed: float = 0.0

static func make(p_index: int, p_base_angle: float, p_health: float,
		hitbox_radius: float, hit_callback: Callable) -> LeviathanPlate:
	var plate := LeviathanPlate.new()
	plate.index = p_index
	plate.base_angle = p_base_angle
	plate.max_health = p_health
	plate.health = p_health
	plate.target = BulletTarget.make(BulletManager.Team.ENEMY, hitbox_radius, hit_callback)
	return plate

## Angle courant de la plaque, orbite de la coquille comprise.
func angle_at(shell_rotation: float) -> float:
	return wrapf(base_angle + shell_rotation, -PI, PI)

## La plaque est-elle dans l'arc face au joueur ? C'est **toute** la mécanique de la
## phase 1 : hors de l'arc, le corps la masque et le tir se réfléchit.
##
## L'arc est centré sur 0 (la direction de la caméra), et `arc_deg` est sa largeur
## TOTALE — d'où le demi-arc dans la comparaison. Se tromper là-dessus doublerait
## silencieusement la fenêtre de tir de la phase.
func is_exposed(shell_rotation: float, arc_deg: float) -> bool:
	if state != State.ALIVE:
		return false
	return absf(angle_at(shell_rotation)) <= deg_to_rad(arc_deg) * 0.5

## Vrai tant que la plaque protège le corps et tire son éventail. Une plaque tombée
## cesse les deux à la fois : le rideau s'allège d'un quart, et le joueur le sent.
func is_up() -> bool:
	return state == State.ALIVE

## Encaisse des dégâts. Retourne vrai **le seul frame où la plaque tombe**, pour que
## l'appelant joue l'explosion une fois, pas une fois par balle de la salve.
func apply_damage(amount: float) -> bool:
	if state != State.ALIVE:
		return false
	health = maxf(health - amount, 0.0)
	if health > 0.0:
		return false
	state = State.FALLING
	elapsed = 0.0
	# ⚠️ Avant tout le reste : une cible active sur une plaque tombée est un mur
	# invisible qui mange les balles du joueur.
	target.enabled = false
	return true

func tick(delta: float, fall_time: float) -> void:
	if state != State.FALLING:
		return
	elapsed += delta
	if elapsed >= fall_time:
		state = State.DOWN
		elapsed = 0.0

## Part de chute, de 0 (en place) à 1 (pendue). Seule sortie d'animation de la classe :
## le module la transforme en angle.
func fall_ratio(fall_time: float) -> float:
	match state:
		State.ALIVE:
			return 0.0
		State.FALLING:
			return clampf(elapsed / maxf(fall_time, 0.0001), 0.0, 1.0)
		State.DOWN:
			return 1.0
	return 0.0

func health_ratio() -> float:
	return health / max_health if max_health > 0.0 else 0.0
