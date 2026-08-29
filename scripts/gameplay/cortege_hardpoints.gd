class_name CortegeHardpoints
extends Node3D
## Les points d'ancrage du Long Cortège : dix-sept tourelles, sept ponts, cinq nœuds d'épine.
##
## ⚠️ IL EXISTE PARCE QUE LES PIÈCES SONT SUR UN OBJET QUI BOUGE. Chaque pièce est ajoutée comme
## ENFANT de son marqueur dans la coque livrée : le défilement les emmène toutes, sans une seule
## ligne d'arithmétique de position, et donc sans aucune façon de désynchroniser une tourelle de
## la coupole qu'on voit. Ce qui reste à faire ici tient en trois choses : les créer au bon
## endroit, les faire avancer dans le bon ordre, et relier un nœud abattu aux tourelles qu'il
## éteint.
##
## ⚠️ IL LES FAIT AVANCER LUI-MÊME, ELLES N'ONT PAS DE `_process`. Vingt-neuf pièces qui
## traiteraient chacune leur image, c'est vingt-neuf appels de script par trame pour un travail
## que rien n'oblige à disperser — et surtout un ordre de passage indéfini, alors qu'un nœud doit
## pouvoir éteindre une tourelle AVANT qu'elle ait tiré dans la même trame.
##
## ⚠️ LES COQUES LÂCHÉES PAR LES PONTS VIVENT ICI, SOUS `Released`, ET NON SOUS LEUR PONT. Un
## `EnemyController` pose sa coque en coordonnées LOCALES ; parentée au pont, elle serait décalée
## de tout ce que le décor a parcouru et dériverait un peu plus à chaque seconde. Ce nœud-ci ne
## bouge jamais : c'est ce qui en fait le bon parent.

signal turret_destroyed(turret: CortegeTurret)
signal bay_destroyed(bay: CortegeBay)
signal node_destroyed(node: CortegeSpineNode)
## Un nœud entre dans sa fenêtre — le niveau s'en sert pour l'expliquer, une seule fois.
signal node_engaged(node: CortegeSpineNode)
signal section_silenced(section: int, turrets: int)

var tuning: CortegeTuning

var _turrets: Array[CortegeTurret] = []
var _bays: Array[CortegeBay] = []
var _nodes: Array[CortegeSpineNode] = []
var _released: Node3D
## Combien de tronçons ont RÉELLEMENT été montés. ⚠️ ET NON `tuning.section_count` : le réglage
## dit ce que le niveau vise, la coque livrée dit ce qu'il y a. Les confondre fait désigner par
## un nœud un tronçon qui n'existe pas — inoffensif ici, mais c'est la même confusion qui, sur
## un survol raccourci pour une mesure, éteindrait un tronçon fantôme.
var _sections_built: int = 0

## ⚠️ LA CAMÉRA EST UN PARAMÈTRE DE COLLISION SUR CE NIVEAU, et c'est contre-intuitif. Les
## pièces sont hors du plan de jeu ; où il faut tirer pour les toucher dépend donc d'où on les
## regarde. Elle bouge (secousses, recadrages) : on la relit à chaque image plutôt que de figer
## un décalage qui deviendrait faux au premier tremblement.
var _camera: Node3D = null

## Monte les pièces sur les tronçons livrés.
##
## ⚠️ IL PREND DES TRONÇONS, PAS LE SURVOL. Il n'a besoin de rien d'autre que d'une liste de
## nœuds portant des marqueurs — lui passer `CortegeFlyby` le rendrait dépendant du défilement,
## donc impossible à monter dans un test, donc la chaîne « un nœud éteint le tronçon suivant »
## resterait vérifiable nulle part. C'est la seule mécanique du jeu dont la récompense arrive
## quarante secondes après la cause : c'est précisément celle qu'aucune partie ne prouve.
func build(sections: Array[Node3D], p_tuning: CortegeTuning, bullet_manager: BulletManager,
		player: PlayerFighterController, vfx: VFXManager, camera: Node3D = null) -> void:
	tuning = p_tuning
	_camera = camera
	_released = Node3D.new()
	_released.name = "Released"
	add_child(_released)
	_sections_built = sections.size()
	for index in sections.size():
		for child in sections[index].get_children():
			var marker := child as Node3D
			if marker == null:
				continue
			if marker.name.begins_with("Turret_"):
				_add_turret(marker, index, bullet_manager, player, vfx)
			elif marker.name.begins_with("Bay_"):
				_add_bay(marker, index, bullet_manager, player, vfx)
			elif marker.name.begins_with("Spine_"):
				_add_node(marker, index, bullet_manager, vfx)
	print("[Cortege] armement — %d tourelles, %d ponts, %d nœuds, %d coques en réserve"
		% [_turrets.size(), _bays.size(), _nodes.size(), _released.get_child_count()])

func _add_turret(marker: Node3D, section: int, bullet_manager: BulletManager,
		player: PlayerFighterController, vfx: VFXManager) -> void:
	var turret := CortegeTurret.make(tuning, section)
	turret.serial = _turrets.size()
	turret.name = "Turret"
	turret.setup(bullet_manager, player, vfx)
	turret.destroyed.connect(_on_turret_destroyed)
	marker.add_child(turret)
	_turrets.append(turret)

func _add_bay(marker: Node3D, section: int, bullet_manager: BulletManager,
		player: PlayerFighterController, vfx: VFXManager) -> void:
	var bay := CortegeBay.make(tuning, section)
	bay.name = "Bay"
	marker.add_child(bay)
	# ⚠️ APRÈS `add_child`, parce que le pool a besoin d'un parent DANS l'arbre pour que les
	# coques soient prêtes : `EnemyController._ready()` est ce qui les endort, et une coque qui
	# n'a jamais été endormie s'active toute seule au premier `_physics_process`.
	bay.build(bullet_manager, player, vfx, _released)
	bay.destroyed.connect(_on_bay_destroyed)
	_bays.append(bay)

func _add_node(marker: Node3D, section: int, bullet_manager: BulletManager,
		vfx: VFXManager) -> void:
	var node := CortegeSpineNode.make(tuning, section)
	node.name = "SpineNode"
	node.setup(bullet_manager, vfx)
	node.destroyed.connect(_on_node_destroyed)
	marker.add_child(node)
	_nodes.append(node)

## ⚠️ L'ORDRE COMPTE : les nœuds d'abord. Un nœud abattu dans cette trame doit avoir éteint les
## tourelles de son tronçon suivant AVANT qu'elles ne tirent — sinon la récompense arrive une
## image trop tard, ce qui est invisible mais faux, et le jour où le tronçon se raccourcit ça
## devient visible.
func _process(delta: float) -> void:
	var eye := _camera.global_position if is_instance_valid(_camera) else Vector3.ZERO
	for node in _nodes:
		var w := node.global_position
		node.tick(delta, w, GameplayPlane.aim_point_of(w, eye))
	for turret in _turrets:
		var w := turret.global_position
		turret.tick(delta, w, GameplayPlane.aim_point_of(w, eye))
	for bay in _bays:
		var w := bay.global_position
		bay.tick(delta, w, GameplayPlane.aim_point_of(w, eye))

## Les pièces, pour les faire avancer depuis un banc. Le jeu, lui, passe par `_process`.
func turrets() -> Array[CortegeTurret]:
	return _turrets

func nodes() -> Array[CortegeSpineNode]:
	return _nodes

func bays() -> Array[CortegeBay]:
	return _bays

func turret_count() -> int:
	return _turrets.size()

func bay_count() -> int:
	return _bays.size()

func node_count() -> int:
	return _nodes.size()

## Combien de tourelles restent debout dans un tronçon — pour l'annonce faite au joueur.
func turrets_alive_in(section: int) -> int:
	var alive := 0
	for turret in _turrets:
		if turret.section == section and turret.is_alive() and not turret.is_silenced():
			alive += 1
	return alive

func _on_turret_destroyed(turret: CortegeTurret) -> void:
	turret_destroyed.emit(turret)

func _on_bay_destroyed(bay: CortegeBay) -> void:
	bay_destroyed.emit(bay)

func _on_node_engaged(node: CortegeSpineNode) -> void:
	node_engaged.emit(node)

func _on_node_destroyed(node: CortegeSpineNode) -> void:
	node_destroyed.emit(node)
	if not tuning.node_silences_next_section:
		return
	var target := CortegeSpineNode.silenced_section(node.section, _sections_built)
	if target < 0:
		# Le dernier nœud du survol ne soulage rien : il n'y a pas de tronçon d'après DANS CE
		# NIVEAU. Ce n'est pas une erreur — le vaisseau, lui, continue.
		return
	var silenced := 0
	for turret in _turrets:
		if turret.section == target and turret.is_alive() and not turret.is_silenced():
			turret.silence()
			silenced += 1
	# ⚠️ RIEN À DIRE QUAND IL N'Y A RIEN À ÉTEINDRE. Annoncer « tronçon 02 éteint · 0 tourelles »
	# apprendrait au joueur que la mécanique ne sert à rien, au moment exact où elle vient de
	# lui coûter un effort.
	if silenced > 0:
		section_silenced.emit(target, silenced)
