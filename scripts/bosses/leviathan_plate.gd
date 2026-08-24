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
## Maillages de la plaque, racine comprise. Résolus UNE fois au montage : c'est sur eux que
## le module pose la surbrillance de la plaque active, et les rechercher par image coûterait
## une descente d'arbre à chaque frame (cf. `HarvesterLimb.meshes`).
var meshes: Array[MeshInstance3D] = []
var rest_basis: Basis = Basis.IDENTITY
## Pose complète au repos — position comprise. La chute déplace la plaque autant qu'elle
## la fait pivoter : garder seulement la base obligerait à relire la position du nœud à
## chaque image, alors qu'elle est déjà en train de bouger.
var rest_transform: Transform3D = Transform3D.IDENTITY
## Axe de chute — la TANGENTE à l'anneau au point où la plaque est posée.
##
## ⚠️ CE COMMENTAIRE A MENTI PENDANT DES SEMAINES. Il annonçait un axe « déduit de la
## position radiale » ; rien ne le déduisait, et les quatre plaques basculaient toutes
## autour du même `Vector3.RIGHT`. Celle du sommet se couchait vers l'avant, celle du
## flanc pivotait de travers : « les boucliers descendent très bizarrement » au playtest.
## Un commentaire qui décrit une intention non câblée est pire qu'aucun commentaire — il
## empêche de chercher là où c'est cassé. L'axe est désormais posé par `orient_fall()`.
var fall_axis: Vector3 = Vector3.RIGHT
## Distance du centre du boss, en metres — MESUREE sur la coque au montage.
##
## ⚠️ Elle valait 2,6 en dur dans `_sync_targets()` alors que les plaques sont a 3,10 m
## de l'axe. Une hitbox posee 50 cm en deca du maillage se touche encore par hasard : ce
## genre d'ecart ne casse rien franchement, il rend juste le tir capricieux.
var radius: float = 2.6
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

## Oriente la chute : la plaque bascule vers l'EXTÉRIEUR de l'anneau, en pivotant autour
## de la tangente au cercle. C'est le mouvement d'une écaille qui se décolle, et il est
## différent pour chaque plaque puisqu'il dépend de sa place.
##
## L'anneau est dans le plan XZ de la coque (Y = haut) : le rayon au point d'angle `a`
## vaut `(cos a, 0, sin a)`, et la tangente `(-sin a, 0, cos a)`.
## `radial` est le rayon qui va du centre de rotation de la coquille vers la plaque,
## EXPRIME DANS LE REPERE DE SON PARENT — c'est la que `rest_basis.rotated()` compose.
## Nul (le defaut), on retombe sur l'ancienne deduction depuis `base_angle`, ce dont les
## tests ont besoin : ils font vivre des plaques sans aucune coque montee.
func orient_fall(radial: Vector3 = Vector3.ZERO) -> void:
	var arm := radial
	arm.y = 0.0
	if arm.length_squared() <= 0.0001:
		arm = Vector3(cos(base_angle), 0.0, sin(base_angle))
	# La charniere est tangentielle : `radial x UP` fait basculer la plaque VERS
	# L'EXTERIEUR pour un angle positif, ce que `_tick_plate_falls` applique. Sous elle il
	# y a la coquille puis le pont — une bascule vers l'interieur les traverserait.
	fall_axis = arm.normalized().cross(Vector3.UP).normalized()

## Angle courant de la plaque, orbite de la coquille comprise.
func angle_at(shell_rotation: float) -> float:
	return wrapf(base_angle + shell_rotation, -PI, PI)

## La plaque est-elle dans l'arc face au joueur ? C'est **toute** la mécanique de la
## phase 1 : hors de l'arc, le corps la masque et le tir se réfléchit.
##
## `arc_deg` est la largeur TOTALE de l'arc — d'où le demi-arc dans la comparaison. Se
## tromper là-dessus doublerait silencieusement la fenêtre de tir de la phase.
##
## ⚠️ L'arc est centré sur `centre_rad`, la direction du JOUEUR, et non sur 0. Tant que
## `base_angle` valait `TAU·i/alive`, centrer sur 0 était sans conséquence : les angles
## étaient fictifs des deux côtés. Sur la géométrie réelle, 0 pointe le flanc tribord du
## boss, à 90° de celui qui tire — on exposait un côté que le joueur ne voit jamais.
func is_exposed(shell_rotation: float, arc_deg: float, centre_rad: float = 0.0) -> bool:
	if state != State.ALIVE:
		return false
	return absf(offset_from(shell_rotation, centre_rad)) <= deg_to_rad(arc_deg) * 0.5

## Écart angulaire entre la plaque et la direction visée, dans ]−PI ; PI]. C'est lui qui
## départage les plaques exposées : la plus proche du joueur est celle qui encaisse.
func offset_from(shell_rotation: float, centre_rad: float) -> float:
	return wrapf(angle_at(shell_rotation) - centre_rad, -PI, PI)

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
