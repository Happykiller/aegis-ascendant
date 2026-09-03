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

# --------------------------------------------------------------------------
# LES BATTERIES LÉGÈRES — ancrées sur les installations, pas sur des marqueurs
# --------------------------------------------------------------------------
#
# ⚠️ ELLES N'ONT PAS DE MARQUEUR À ELLES, ET C'EST UNE DÉCISION D'ARCHITECTURE. La coque livrée
# fige trente marqueurs ; leur en ajouter vingt-et-un aurait demandé une reforge du `.glb`, et
# surtout les aurait posés en ABSOLU — le jour où une installation se déplace (c'est le lot B du
# plan d'enrichissement), chaque batterie serait restée en arrière, orpheline de ce qu'elle garde.
#
# Une batterie appartient à son installation : c'est ce que dit la consigne 9 (« 2 à 4 petites
# pièces autour d'une grosse installation, le long d'un bord ou autour d'un hangar »), et c'est
# ce que le code dit ici. Chaque pièce est enfant du marqueur de son HÔTE, décalée en local :
# déplacer l'hôte emmène sa garde, sans qu'une seule ligne de cette table ne change.
#
# ⚠️ ELLE HÉRITE DU Y DE SON HÔTE, ET C'EST L'APPROXIMATION À CONNAÎTRE. Le Y d'un marqueur est
# échantillonné sur la peau, au point de l'hôte ; une pièce posée quatre mètres plus loin prend
# la même assise. Les marqueurs sont « toujours sur une bande plate » et la coque ne bouge pas de
# façon sensible sur cette distance — mais c'est vrai par CONSTRUCTION de la coque actuelle, pas
# par calcul. Le jour où le lot B lui donne du relief, cette hypothèse se re-vérifie EN REGARDANT.
#
# ⚠️ UNE GRAPPE DEVANT L'HÔTE, ET NON UNE FILE À SON FLANC — CORRIGÉ EN REGARDANT (ADR-0006).
# La première table écartait les pièces le long de la coque, et la capture a montré des tourelles
# ISOLÉES, jamais un groupe. La cause est mesurable : le pont médian ne fait que 2,95 m de large
# (|x| de 7,35 à 10,30) et le pont intérieur 4,60 m, quand il faut ~4,05 m entre une petite et le
# socle de sa lourde. AUCUNE grappe transversale n'est possible sur cette coque.
#
# Mais deux PETITES n'ont besoin que de 1,70 m l'une de l'autre. La batterie se pose donc en
# grappe serrée, DÉCALÉE de quatre à sept mètres devant son hôte, au lieu de s'étaler à son
# flanc : chaque batterie tient dans moins de trois mètres de coque, et se lit comme un groupe.
#
# ⚠️ AUCUN PAS RÉGULIER, ET AUCUN TIRAGE. Sept batteries sur vingt-quatre installations, de deux
# à quatre pièces, avec deux tronçons laissés nus : « zone calme → batterie → grande installation
# → respiration » (consigne 15). Les zones vides sont un LIVRABLE, pas un manque — et la première
# batterie est posée contre une tourelle lourde pour que le joueur voie les deux échelles côte à
# côte la première fois qu'il en rencontre une.
#
# ⚠️ ET ELLE NE FRANCHIT JAMAIS LA CONTREMARCHE DE CHINE. Le profil de la coque a DEUX paliers,
# séparés par une marche de 60 cm à |x| entre 6,80 et 7,35 : le pont intérieur (|x| de 2,20 à
# 6,80, à −4,30) et le pont médian (7,35 à 10,30, à −4,99). Une pièce qui hérite du Y de son
# hôte et se pose de l'autre côté de la marche FLOTTE de soixante-neuf centimètres — au-dessus du
# vide, en silence, et personne ne le verrait avant une capture. Chaque offset garde donc sa
# pièce sur le palier de son hôte, et `test_cortege_light_turrets.gd` le vérifie sur la coque
# livrée plutôt que sur cette phrase.
#
# Format : [nom de l'hôte, [[dx, ds], ...]] — `dx` en latéral (+ = tribord), `ds` le long de la
# coque depuis la proue. La conversion en Z local est faite au montage : `s` croît vers la poupe,
# `z` décroît.
const BATTERIES: Array = [
	# Révélation : deux pièces devant une lourde, même bord, tronçon 1. Pont intérieur.
	["Turret_01", [[1.8, 3.4], [3.2, 4.8]]],
	# Garde de hangar, bâbord, tronçon 2. L'emprise de l'ouverture interdit 4,30 m de part et
	# d'autre : la grappe se pose DEVANT le puits, pas à son flanc.
	["Bay_02", [[0.0, 6.0], [1.7, 6.4], [0.8, 8.0]]],
	["Turret_05", [[-1.4, -3.6], [-2.9, -4.6]]],
	# ⚠️ RIEN AU DÉBUT DU TRONÇON 3 (s 214 à 246) : c'est la respiration, et elle est voulue.
	["Bay_05", [[-1.4, 5.6], [0.3, 6.0], [-0.8, 7.4], [0.8, 8.2]]],
	["Turret_10", [[1.0, 4.0], [2.3, 5.3], [0.6, 5.8]]],
	# ⚠️ ET RIEN ENTRE 348 ET 410 : la seconde respiration, avant que le tronçon 5 ne se ferme.
	["Turret_13", [[-1.0, -4.2], [0.6, -4.8], [-0.4, -6.2]]],
	["Turret_16", [[0.6, 4.2], [2.4, 4.7], [1.0, 6.2], [2.8, 6.8]]],
]

signal turret_destroyed(turret: CortegeTurret)
signal bay_destroyed(bay: CortegeBay)
signal node_destroyed(node: CortegeSpineNode)
## Un nœud entre dans sa fenêtre — le niveau s'en sert pour l'expliquer, une seule fois.
signal node_engaged(node: CortegeSpineNode)
signal section_weakened(section: int, turrets: int)

var tuning: CortegeTuning

var _turrets: Array[CortegeTurret] = []
## ⚠️ UNE LISTE À PART, ET NON MÉLANGÉE AUX LOURDES. `turret_count()` et `turrets_intact_in()`
## servent à dire au joueur ce qu'un nœud d'épine vient de lui gagner : y verser vingt-et-une
## pièces d'appoint ferait tripler un chiffre dont la promesse, elle, n'a pas changé. Les deux
## listes avancent ensemble, se comptent séparément.
var _light_turrets: Array[CortegeTurret] = []
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
			# ⚠️ APRÈS la pièce lourde et non à sa place : une batterie garde une installation,
			# elle ne la remplace pas. Un hôte sans entrée dans la table n'en a simplement pas.
			_add_battery(marker, index, bullet_manager, player, vfx)
	print("[Cortege] armement — %d tourelles (+%d légères), %d ponts, %d nœuds, %d coques en réserve"
		% [_turrets.size(), _light_turrets.size(), _bays.size(), _nodes.size(),
			_released.get_child_count()])

func _add_turret(marker: Node3D, section: int, bullet_manager: BulletManager,
		player: PlayerFighterController, vfx: VFXManager) -> void:
	var turret := CortegeTurret.make(tuning, section)
	turret.serial = _turrets.size()
	turret.name = "Turret"
	turret.setup(bullet_manager, player, vfx)
	turret.destroyed.connect(_on_turret_destroyed)
	marker.add_child(turret)
	_turrets.append(turret)

## Monte la batterie légère d'un hôte, s'il en a une.
##
## ⚠️ `ds` DEVIENT `-dz`, ET CE SIGNE N'EST PAS COSMÉTIQUE. La station `s` se compte depuis la
## proue et croît vers la poupe ; le Z local du tronçon décroît d'autant (`_z(s) = -(s - origine)`
## dans `build_long_cortege.py`). Écrire `dz = ds` aurait posé chaque batterie en miroir de
## l'autre côté de son hôte — géométriquement valide, silencieux, et faux d'un bout à l'autre du
## niveau. C'est exactement la classe de défaut qui a coûté le plus cher sur les épines du
## Léviathan.
func _add_battery(marker: Node3D, section: int, bullet_manager: BulletManager,
		player: PlayerFighterController, vfx: VFXManager) -> void:
	for entry in BATTERIES:
		if String(entry[0]) != marker.name:
			continue
		for offset in entry[1]:
			var turret := CortegeTurret.make(tuning, section,
				CortegeTuning.TurretScale.LIGHT)
			turret.serial = _light_turrets.size()
			turret.name = "LightTurret"
			turret.position = Vector3(float(offset[0]), 0.0, -float(offset[1]))
			turret.setup(bullet_manager, player, vfx)
			turret.destroyed.connect(_on_turret_destroyed)
			marker.add_child(turret)
			_light_turrets.append(turret)
		return

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
	# ⚠️ LA PIÈCE EST VISÉE PAR SA MASSE, PAS PAR SON ASSISE. `aim_point_of` corrige la parallaxe
	# du marqueur ; il restait celle de la pièce elle-même, qui vaut sa hauteur. Chaque famille
	# déclare la sienne — et le hangar déclare zéro, parce qu'il creuse au lieu de monter.
	for node in _nodes:
		var w := node.global_position + Vector3(0.0, CortegeSpineNode.HIT_LIFT, 0.0)
		node.tick(delta, w, GameplayPlane.aim_point_of(w, eye))
	# ⚠️ `hit_lift()` ET NON LA CONSTANTE : les deux échelles n'ont pas la même hauteur de masse,
	# et c'est elle qui décide où il faut tirer pour toucher sous une caméra qui plonge à 70°.
	# Appliquer la hauteur de la lourde à une pièce deux fois plus petite ferait viser à côté —
	# le défaut exact que `aim_point_of` a été écrit pour corriger, réintroduit par la bande.
	for turret in _turrets:
		var w := turret.global_position + Vector3(0.0, turret.hit_lift(), 0.0)
		turret.tick(delta, w, GameplayPlane.aim_point_of(w, eye))
	for light in _light_turrets:
		var w := light.global_position + Vector3(0.0, light.hit_lift(), 0.0)
		light.tick(delta, w, GameplayPlane.aim_point_of(w, eye))
	for bay in _bays:
		var w := bay.global_position + Vector3(0.0, CortegeBay.HIT_LIFT, 0.0)
		bay.tick(delta, w, GameplayPlane.aim_point_of(w, eye))

## Les pièces, pour les faire avancer depuis un banc. Le jeu, lui, passe par `_process`.
func turrets() -> Array[CortegeTurret]:
	return _turrets

func nodes() -> Array[CortegeSpineNode]:
	return _nodes

func bays() -> Array[CortegeBay]:
	return _bays

func light_turrets() -> Array[CortegeTurret]:
	return _light_turrets

func turret_count() -> int:
	return _turrets.size()

func light_turret_count() -> int:
	return _light_turrets.size()

func bay_count() -> int:
	return _bays.size()

func node_count() -> int:
	return _nodes.size()

## Combien de tourelles restent INTACTES dans un tronçon — pour l'annonce faite au joueur.
##
## ⚠️ UNE TOURELLE ABÎMÉE N'EST PAS COMPTÉE ICI, ET ELLE EST POURTANT BIEN VIVANTE. Ce compte
## sert à dire au joueur ce que son nœud vient de lui gagner ; une pièce diminuée est justement
## ce qu'il a gagné. `is_alive()` répond à l'autre question — celle des dégâts.
func turrets_intact_in(section: int) -> int:
	var intact := 0
	for turret in _turrets:
		if turret.section == section and turret.is_alive() and not turret.is_weakened():
			intact += 1
	return intact

func _on_turret_destroyed(turret: CortegeTurret) -> void:
	turret_destroyed.emit(turret)

func _on_bay_destroyed(bay: CortegeBay) -> void:
	bay_destroyed.emit(bay)

func _on_node_engaged(node: CortegeSpineNode) -> void:
	node_engaged.emit(node)

func _on_node_destroyed(node: CortegeSpineNode) -> void:
	node_destroyed.emit(node)
	if not tuning.node_weakens_next_section:
		return
	var target := CortegeSpineNode.weakened_section(node.section, _sections_built)
	if target < 0:
		# Le dernier nœud du survol ne soulage rien : il n'y a pas de tronçon d'après DANS CE
		# NIVEAU. Ce n'est pas une erreur — le vaisseau, lui, continue.
		return
	var touched := 0
	for turret in _turrets:
		if turret.section == target and turret.is_alive() and not turret.is_weakened():
			turret.weaken()
			touched += 1
	# ⚠️ LES LÉGÈRES FAIBLISSENT AUSSI, MAIS NE SONT PAS COMPTÉES DANS L'ANNONCE. Un nœud coupe
	# l'énergie d'un tronçon : laisser une batterie à pleine vigueur pendant que les lourdes
	# traînent se lirait comme une panne de la récompense, et c'est le défaut qu'`ADR` a payé le
	# 2026-08-30. Mais le chiffre annoncé au joueur reste celui des installations : le gonfler de
	# vingt-et-une pièces d'appoint promettrait une récompense plus grosse qu'elle n'est. Le sens
	# de l'écart est le bon — on donne un peu plus qu'on n'annonce.
	for light in _light_turrets:
		if light.section == target and light.is_alive() and not light.is_weakened():
			light.weaken()
	# ⚠️ RIEN À DIRE QUAND IL N'Y A RIEN À ABÎMER. Annoncer « tronçon 02 · 0 tourelles »
	# apprendrait au joueur que la mécanique ne sert à rien, au moment exact où elle vient de
	# lui coûter un effort.
	if touched > 0:
		section_weakened.emit(target, touched)
