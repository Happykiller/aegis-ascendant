class_name TargetableProjectile
extends RefCounted
## Un projectile ennemi que le joueur peut **abattre** — les missiles de la phase 1 du
## Pale Leviathan (`docs/design/BOSS_PALE_LEVIATHAN.md` §3.3 et §8.2).
##
## POURQUOI CETTE PRIMITIVE EXISTE — elle apprend au joueur qu'il peut *répondre* à un
## projectile au lieu de seulement l'esquiver. C'est la leçon dont il aura besoin en
## phase 3, quand il devra choisir entre frapper le boss et nettoyer l'écran.
##
## ⚠️ AUCUNE EXTENSION DU `BulletManager` N'A ÉTÉ NÉCESSAIRE, contrairement à ce que le
## document de conception annonçait comme « à vérifier ». `_resolve_target()` ignore les
## balles de la MÊME équipe que la cible (`if _teams[i] == target.team: continue`). Un
## projectile ennemi qui enregistre une `BulletTarget` d'équipe `ENEMY` est donc
## naturellement touché par les tirs du joueur, et par eux seuls. Le mécanisme était
## déjà là ; il n'avait simplement jamais servi à autre chose qu'à des coques.
##
## `RefCounted` et non `Node` : ni arbre, ni `_process`, ni signaux. Le module du boss
## le fait avancer dans son propre ordre, ce qui rend la boucle lisible d'un seul
## endroit — et le rend instanciable à la main en test.

## Vitesse en dessous de laquelle on ne tente plus de virer. Un projectile quasi
## immobile n'a pas de direction fiable, et `angle_to` sur un vecteur nul rendrait
## `NaN` — qui se propagerait dans la position jusqu'à sortir le missile du monde sans
## une seule erreur au journal.
const MIN_STEERING_SPEED := 0.01

var plane_position: Vector2 = Vector2.ZERO
var velocity: Vector2 = Vector2.ZERO
var health: float = 0.0
var max_health: float = 0.0
## Vitesse de virage, en radians par seconde. Zéro = trajectoire rectiligne.
var turn_rate: float = 0.0
var damage: float = 0.0
var target: BulletTarget
## Faux dès que le projectile est abattu, sorti du plan, ou a frappé.
var alive: bool = true

## `hit_callback` reçoit les dégâts encaissés PAR LE PROJECTILE (tir du joueur), et non
## ceux qu'il inflige : c'est le contrat de `BulletTarget`.
static func make(p_position: Vector2, p_velocity: Vector2, p_health: float,
		hitbox_radius: float, p_turn_rate: float, p_damage: float,
		hit_callback: Callable) -> TargetableProjectile:
	var projectile := TargetableProjectile.new()
	projectile.plane_position = p_position
	projectile.velocity = p_velocity
	projectile.max_health = p_health
	projectile.health = p_health
	projectile.turn_rate = p_turn_rate
	projectile.damage = p_damage
	# Équipe ENEMY : ce sont les balles du JOUEUR qui le touchent (voir l'en-tête).
	projectile.target = BulletTarget.make(BulletManager.Team.ENEMY, hitbox_radius, hit_callback)
	projectile.target.position = p_position
	return projectile

## Fait avancer le projectile d'une image. `chase` est la position à poursuivre ; le
## virage est **borné par `turn_rate`**, ce qui est ce qui rend le missile esquivable :
## un projectile qui vire instantanément est un projectile qui touche toujours.
func tick(delta: float, chase: Vector2) -> void:
	if not alive:
		return
	var speed := velocity.length()
	if turn_rate > 0.0 and speed > MIN_STEERING_SPEED:
		var desired := chase - plane_position
		if desired.length_squared() > 0.0:
			# On tourne la VITESSE, on ne la remplace pas : la norme est conservée, donc
			# un missile ne peut pas accélérer en virant.
			var turn := clampf(velocity.angle_to(desired), -turn_rate * delta, turn_rate * delta)
			velocity = velocity.rotated(turn)
	plane_position += velocity * delta
	target.position = plane_position
	# Sorti du plan : on le retire plutôt que de le laisser courir. La marge évite
	# qu'un missile né au bord ne meure à l'image de sa création.
	if not GameplayPlane.is_inside(plane_position, 3.0):
		_retire()

## Encaisse un tir du joueur. Retourne vrai **le seul frame où le projectile tombe**,
## pour que l'appelant joue l'explosion et le son une fois, pas une fois par balle.
func apply_damage(amount: float) -> bool:
	if not alive:
		return false
	health = maxf(health - amount, 0.0)
	if health > 0.0:
		return false
	_retire()
	return true

## Le projectile a-t-il atteint `point` (le joueur) ? La portée est la somme des rayons.
func reaches(point: Vector2, other_radius: float) -> bool:
	if not alive:
		return false
	var reach := target.radius + other_radius
	return plane_position.distance_squared_to(point) <= reach * reach

## Consomme le projectile après qu'il a frappé. Distinct d'`apply_damage` : ici il n'est
## pas abattu, il s'est dépensé — l'appelant ne doit pas jouer la même explosion.
func consume() -> void:
	_retire()

func health_ratio() -> float:
	return health / max_health if max_health > 0.0 else 0.0

## ⚠️ Désactive la cible AVANT de la déclarer morte. Une cible laissée active dans le
## `BulletManager` sur un projectile éteint est un mur invisible qui mange les balles
## du joueur — le défaut exact contre lequel `HarvesterCombat.release()` a été écrit.
func _retire() -> void:
	alive = false
	if target != null:
		target.enabled = false
