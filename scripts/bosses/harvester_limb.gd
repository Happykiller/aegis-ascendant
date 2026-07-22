class_name HarvesterLimb
extends RefCounted
## Un appendice du Choir Harvester : sa vie, son état, et sa zone de touche.
##
## CE QU'IL NE FAIT PAS — il ne pose aucune rotation et ne tire aucune balle. Un
## appendice est tour à tour plié par sa destruction et braqué par sa visée : deux
## écrivains sur la même rotation finissent toujours par se marcher dessus. La pose
## a donc UN seul auteur, `harvester_combat.gd`, qui compose repli et visée. Cette
## classe ne fait que dire *où en est* l'appendice.
##
## `RefCounted` et non `Node` : il n'a besoin ni d'arbre, ni de `_process`, ni de
## signaux. Le module le fait avancer dans son propre ordre, ce qui rend la boucle du
## combat lisible d'un seul endroit — et le rend instanciable à la main en test.

## Le cycle complet, dans l'ordre. `FALLING` et `RISING` sont des ANIMATIONS ; `DOWN`
## est l'attente. Les trois valent « à terre » pour l'iris : seul `ALIVE` referme.
enum State { ALIVE, FALLING, DOWN, RISING }

## Identifie l'appendice pour le module, qui branche dessus son attaque et sa pose.
var kind: StringName = &""
var state: State = State.ALIVE
var health: float = 0.0
var max_health: float = 0.0
## Nœud racine de la pièce mobile (`Arm_Scythe`, `Arm_Claw`, `Arm_Cannon`).
var root: Node3D
## Sous-pièces articulées, dans l'ordre du contrat de noms (BRIEF-0039).
var joints: Array[Node3D] = []
var target: BulletTarget
## Temps écoulé DANS l'état courant. Remis à zéro à chaque bascule.
var elapsed: float = 0.0

## `node_names` : la racine d'abord, puis ses articulations. Un nom absent de la
## coque n'est pas une erreur silencieuse : la coque et le code partagent un contrat
## (BRIEF-0039), et une faute de frappe côté Blender doit se voir.
static func make(p_kind: StringName, hull: Node3D, node_names: PackedStringArray,
		p_health: float, hitbox_radius: float, hit_callback: Callable) -> HarvesterLimb:
	var limb := HarvesterLimb.new()
	limb.kind = p_kind
	limb.max_health = p_health
	limb.health = p_health
	# Coque nulle = montage sans 3D (tests headless). Ce n'est PAS le cas d'une coque
	# présente à laquelle il manque une pièce : celui-là est un contrat rompu, et il
	# doit crier.
	if hull != null:
		for i in node_names.size():
			# ⚠️ `find_child` RÉCURSIF, et surtout pas `get_node_or_null(NodePath(nom))`.
			# Les articulations sont des enfants INDIRECTS : `Scythe_Blade` pend de
			# `Scythe_Mid`, lui-même sous `Arm_Scythe` (c'est tout l'intérêt des chaînes
			# de `ak.moving_part`). Un chemin relatif ne voit que les enfants directs et
			# aurait rendu `null` sur cinq pièces sur neuf — un boss aux bras inertes,
			# sans qu'aucun test headless ne le voie, puisqu'ils tournent sans coque.
			# `owned = false` : les nœuds d'un `.glb` instancié n'appartiennent pas à la
			# scène qui les monte.
			var node := hull.find_child(node_names[i], true, false) as Node3D
			if node == null:
				push_error("[Harvester] coque sans piece mobile '%s' (contrat BRIEF-0039)" % node_names[i])
				continue
			if i == 0:
				limb.root = node
			else:
				limb.joints.append(node)
	limb.target = BulletTarget.make(BulletManager.Team.ENEMY, hitbox_radius, hit_callback)
	return limb

## Vrai tant que l'appendice attaque et protège le corps. C'est LA question que pose
## l'iris — et la réponse ne devient vraie qu'au bout du redéploiement, pas à la fin
## du minuteur de repousse : « quand un appendice s'est reformé », il se referme.
func is_up() -> bool:
	return state == State.ALIVE

## Encaisse des dégâts. Retourne vrai **le seul frame où l'appendice tombe**, pour que
## l'appelant déclenche explosion et son une fois, pas une fois par balle de la salve.
func apply_damage(amount: float) -> bool:
	if state != State.ALIVE:
		return false
	health = maxf(health - amount, 0.0)
	if health > 0.0:
		return false
	_enter(State.FALLING)
	target.enabled = false
	return true

## Fait avancer la machine à états. `tuning` porte les durées ; rien n'est en dur.
func tick(delta: float, tuning: HarvesterTuning) -> void:
	elapsed += delta
	match state:
		State.FALLING:
			if elapsed >= tuning.limb_retract_time:
				_enter(State.DOWN)
		State.DOWN:
			# L'attente occupe ce qui RESTE du délai de repousse une fois le repli et
			# le redéploiement décomptés : c'est `limb_rebuild_time` qui fait foi, de
			# la destruction au retour en service.
			var wait := tuning.limb_rebuild_time - tuning.limb_retract_time - tuning.limb_deploy_time
			if elapsed >= maxf(wait, 0.0):
				_enter(State.RISING)
		State.RISING:
			if elapsed >= tuning.limb_deploy_time:
				_enter(State.ALIVE)
				health = max_health
				target.enabled = true

## Part de déploiement, de 0 (replié contre la coque) à 1 (sorti). C'est la seule
## sortie d'animation de cette classe : le module la transforme en angles.
func deploy_ratio(tuning: HarvesterTuning) -> float:
	match state:
		State.ALIVE:
			return 1.0
		State.FALLING:
			return 1.0 - clampf(elapsed / maxf(tuning.limb_retract_time, 0.0001), 0.0, 1.0)
		State.DOWN:
			return 0.0
		State.RISING:
			return clampf(elapsed / maxf(tuning.limb_deploy_time, 0.0001), 0.0, 1.0)
	return 1.0

## Part de vie restante, pour un retour visuel d'endommagement (émissifs, fissures).
func health_ratio() -> float:
	return health / max_health if max_health > 0.0 else 0.0

func _enter(next: State) -> void:
	state = next
	elapsed = 0.0
