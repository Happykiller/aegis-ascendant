class_name LeviathanSpike
extends RefCounted
## Une épine du Pale Leviathan — attachée au corps, puis **détachée et autonome**
## (`docs/design/BOSS_PALE_LEVIATHAN.md` §5).
##
## LE MOMENT QU'ELLE PORTE — en phase 3, les quatre épines s'arrachent du corps et
## viennent chercher le joueur. C'est le geste le plus spectaculaire du combat : une
## pièce qui faisait partie de la silhouette depuis trois minutes s'en sépare.
##
## Chaque épine a un **rôle distinct**, et c'est ce qui crée le dilemme de la phase :
## la bloqueuse s'interpose devant le noyau, donc frapper le boss coûte de ne pas
## nettoyer, et l'inverse. Il n'y a pas de bonne réponse absolue, seulement une bonne
## réponse à l'instant.
##
## ⚠️ CE QU'ELLE NE FAIT PAS — elle ne reparente aucun nœud. Le détachement visuel
## appartient au module, qui possède l'arbre ; cette classe ne dit que *où en est*
## l'épine et *où elle veut aller*. Deux écrivains sur la même transformation finissent
## toujours par se marcher dessus (leçon `harvester_limb.gd`).

enum Role {
	CHARGER,  ## fonceuse : charge télégraphiée, traverse l'écran
	GUNNER,   ## tireuse : se poste à distance et ajuste
	BLOCKER,  ## bloqueuse : s'interpose entre le joueur et le noyau
	ESCORT,   ## escorte : orbite le noyau à courte distance
}

enum State { ATTACHED, DETACHING, FREE, DEAD }

var index: int = 0
var role: Role = Role.CHARGER
var state: State = State.ATTACHED
var health: float = 0.0
var max_health: float = 0.0
## Position dans le plan de jeu. Ne vaut que détachée : tant qu'elle est sur le corps,
## le module la recalcule depuis la coque.
var plane_position: Vector2 = Vector2.ZERO
## Angle d'implantation sur le corps, en radians. Sert à la placer au détachement.
var base_angle: float = 0.0
var node: Node3D
var rest_transform: Transform3D = Transform3D.IDENTITY
var target: BulletTarget
var elapsed: float = 0.0
## Phase d'attaque propre au rôle (la fonceuse est la seule à en avoir une vraie).
var attack_elapsed: float = 0.0
var attack_lock: Vector2 = Vector2.ZERO
var charging: bool = false

static func make(p_index: int, p_role: Role, p_base_angle: float, p_health: float,
		hitbox_radius: float, hit_callback: Callable) -> LeviathanSpike:
	var spike := LeviathanSpike.new()
	spike.index = p_index
	spike.role = p_role
	spike.base_angle = p_base_angle
	spike.max_health = p_health
	spike.health = p_health
	spike.target = BulletTarget.make(BulletManager.Team.ENEMY, hitbox_radius, hit_callback)
	return spike

## Les quatre rôles, dans l'ordre d'implantation. ⚠️ Un rôle par épine, jamais deux
## fonceuses : la phase perdrait son dilemme et redeviendrait un exercice d'esquive.
static func role_for(index: int) -> Role:
	match index % 4:
		0: return Role.CHARGER
		1: return Role.GUNNER
		2: return Role.BLOCKER
	return Role.ESCORT

## Lance le détachement. Le module s'occupe du reparentage visuel ; ici on ouvre la
## fenêtre pendant laquelle l'épine n'est plus sur le corps mais pas encore autonome.
func detach(from_position: Vector2) -> void:
	if state != State.ATTACHED:
		return
	state = State.DETACHING
	elapsed = 0.0
	plane_position = from_position
	target.position = from_position
	target.enabled = true

func tick(delta: float, detach_time: float) -> void:
	if state != State.DETACHING:
		return
	elapsed += delta
	if elapsed >= detach_time:
		state = State.FREE
		elapsed = 0.0

## Où l'épine veut être, selon son rôle. Fonction **pure** : elle ne déplace rien, elle
## répond. Le module applique le déplacement, borné par la vitesse du rôle.
##
## `core` est la position du noyau, `player` celle du chasseur.
func desired_position(core: Vector2, player: Vector2, blocker_offset: float,
		escort_radius: float, age: float) -> Vector2:
	match role:
		Role.CHARGER:
			# Elle vise le point verrouillé au début de sa charge, jamais la position
			# courante du joueur : un projectile qui suit sa cible est imparable.
			return attack_lock if charging else core
		Role.GUNNER:
			# Se poste en haut, décalée : elle tire de loin et ne doit pas encombrer
			# le couloir où le joueur esquive.
			return Vector2(core.x + sin(age * 0.6) * 6.0, core.y - 1.0)
		Role.BLOCKER:
			# Entre le joueur et le noyau — c'est elle qui crée le dilemme.
			var toward := player - core
			if toward.length_squared() < 0.0001:
				return core
			return core + toward.normalized() * blocker_offset
		Role.ESCORT:
			var a := age * 0.9 + base_angle
			return core + Vector2(cos(a), sin(a)) * escort_radius
	return core

## Verrouille le point de charge. Appelé au DÉBUT du réarme — c'est le télégraphe qui
## rend la charge esquivable, et le verrou est ce qui rend le télégraphe honnête.
func begin_charge(lock: Vector2) -> void:
	charging = true
	attack_elapsed = 0.0
	attack_lock = lock

func end_charge() -> void:
	charging = false
	attack_elapsed = 0.0

func is_free() -> bool:
	return state == State.FREE

func is_alive() -> bool:
	return state != State.DEAD

## Retourne vrai **le seul frame où l'épine tombe**.
func apply_damage(amount: float) -> bool:
	if state == State.DEAD:
		return false
	health = maxf(health - amount, 0.0)
	if health > 0.0:
		return false
	state = State.DEAD
	elapsed = 0.0
	target.enabled = false
	return true

func health_ratio() -> float:
	return health / max_health if max_health > 0.0 else 0.0
