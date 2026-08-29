class_name CortegeSpineNode
extends Node3D
## Un nœud de l'épine dorsale : l'abattre éteint les tourelles du tronçon SUIVANT.
##
## ⚠️ C'EST LA TROISIÈME MÉCANIQUE, ET LA SEULE QUI DEMANDE D'AVOIR COMPRIS LE VAISSEAU. Une
## tourelle se voit, un pont se voit ; un nœud ne paie que si le joueur relie ce qu'il vient de
## casser à ce qui ne lui tire plus dessus cent unités plus loin. C'est aussi ce qui le rend
## FRAGILE en conception : si le survol devient illisible, c'est le nœud qu'on retire du tronçon,
## jamais le pont (voir le plan d'exécution du niveau 2).
##
## ⚠️ SA RÉCOMPENSE EST DIFFÉRÉE, ET IL FAUT DONC LA DIRE. Rien à l'écran ne relie une cause à
## un effet séparés de quarante secondes : le nœud émet, le niveau annonce, et Lyra le nomme.
## Sans cette chaîne, le joueur abat un bulbe lumineux et n'apprend rien.
##
## ⚠️ IL EST PLUS DUR À ATTEINDRE QU'IL N'EST DUR À TUER. Il siège sur l'axe du vaisseau, là où
## convergent les tourelles des deux bords, et il est petit : `CortegeTuning` le dimensionne
## contre une SECONDE cadence de référence (`node_reference_dps`), celle des seuls canons de nez.
## Se dimensionner contre la cadence d'une cible large reviendrait à se donner raison — c'est
## exactement le défaut qu'`ADR-0024` a payé sur le flux du Léviathan.

enum Pass { AHEAD, LIVE, PASSED }

## Le bulbe. Même raison d'être que l'œil d'une tourelle : la géométrie livrée est cuite dans le
## tronçon et partage ses matériaux, donc l'état de la pièce est porté par un volume à nous.
const BULB_RADIUS := 0.62
const BULB_LIFT := 0.45
const BULB_TINT := Color("7a4de8")

signal destroyed(node: CortegeSpineNode)

var tuning: CortegeTuning
var section: int = 0

var _bullet_manager: BulletManager
var _vfx: VFXManager
var _target: BulletTarget
var _bulb: MeshInstance3D
var _bulb_material: StandardMaterial3D

var _pass: Pass = Pass.AHEAD
var _health: float = 0.0
var _alive: bool = true
var _pulse: float = 0.0
var _world: Vector3 = Vector3.ZERO

static func make(p_tuning: CortegeTuning, p_section: int) -> CortegeSpineNode:
	var node := CortegeSpineNode.new()
	node.tuning = p_tuning
	node.section = p_section
	node._health = p_tuning.node_health
	# La cible nait avec la piece — meme raison que pour la tourelle.
	node._target = BulletTarget.make(BulletManager.Team.ENEMY, 0.78, node._take_damage)
	node._target.enabled = false
	return node

func setup(bullet_manager: BulletManager, vfx: VFXManager) -> void:
	_bullet_manager = bullet_manager
	_vfx = vfx

func _ready() -> void:
	_bulb_material = StandardMaterial3D.new()
	_bulb_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_bulb_material.albedo_color = BULB_TINT
	_bulb_material.emission_enabled = true
	_bulb_material.emission = BULB_TINT
	_bulb_material.emission_energy_multiplier = 1.8
	var mesh := SphereMesh.new()
	mesh.radius = BULB_RADIUS
	mesh.height = BULB_RADIUS * 2.0
	mesh.radial_segments = 10
	mesh.rings = 5
	_bulb = MeshInstance3D.new()
	_bulb.name = "Bulb"
	_bulb.mesh = mesh
	_bulb.material_override = _bulb_material
	_bulb.position.y = BULB_LIFT
	_bulb.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_bulb)

func is_alive() -> bool:
	return _alive

func has_passed() -> bool:
	return _pass == Pass.PASSED

## La cible que le gestionnaire de balles connait. ⚠️ EXPOSEE PARCE QUE C'EST LE VRAI CHEMIN DES
## DEGATS : un test qui appellerait une methode ecrite pour lui ne verifierait pas le chemin que
## le jeu emprunte. Ici il n'y a qu'une porte, et tout le monde passe par elle.
func target() -> BulletTarget:
	return _target

## Dans sa fenetre, ni encore devant ni deja derriere.
func is_engaged() -> bool:
	return _pass == Pass.LIVE

## Un pas de la pièce. ⚠️ SA POSITION LUI EST DONNÉE, ELLE NE LA LIT PAS DANS L'ARBRE. Elle est
## pourtant enfant d'un marqueur qui défile, et `global_position` répondrait — mais seulement
## DANS un arbre monté. La passer en paramètre rend la pièce pilotable sans scène, donc
## vérifiable : c'est exactement ce qui a rendu `LeviathanCombat` testable là où trois cycles
## demandent quarante secondes de jeu. Le gestionnaire, lui, sait lire l'arbre.
func tick(delta: float, world: Vector3) -> void:
	if _pass == Pass.PASSED:
		return
	_world = world
	var here := GameplayPlane.to_plane(world)
	var half := tuning.node_visible_span * 0.5
	match _pass:
		Pass.AHEAD:
			if here.y <= half:
				_pass = Pass.LIVE
				if _alive and _bullet_manager != null:
					_bullet_manager.register_target(_target)
					_target.enabled = true
		Pass.LIVE:
			if here.y < -half:
				_retire()
				return
	if _target != null:
		_target.position = here
	if not _alive or _pass != Pass.LIVE:
		return
	# ⚠️ IL BAT, ET C'EST SA SEULE PUBLICITÉ. Rien n'oblige le joueur à tirer sur un point de
	# l'axe : le battement est ce qui distingue le nœud du bordé qui l'entoure, et c'est en
	# entrant dans sa fenêtre qu'il doit se mettre à battre — pas avant, sinon il attire vers
	# une cible encore hors de portée.
	_pulse = fmod(_pulse + delta * 3.0, TAU)
	if _bulb_material != null:
		_bulb_material.emission_energy_multiplier = 1.8 + 1.1 * sin(_pulse)

func _take_damage(damage: float) -> void:
	if not _alive:
		return
	_health -= damage
	if _health > 0.0:
		return
	_alive = false
	if _bulb_material != null:
		_bulb_material.emission_energy_multiplier = 0.0
		_bulb_material.albedo_color = Color(0.05, 0.04, 0.08)
	if _vfx != null:
		_vfx.spawn_explosion(_world, VfxExplosion.Category.MEDIUM,
			Color(0.62, 0.42, 1.0))
	_retire()
	destroyed.emit(self)

func _retire() -> void:
	_pass = Pass.PASSED
	if _target != null:
		_target.enabled = false
		if _bullet_manager != null:
			_bullet_manager.unregister_target(_target)

# --- Fonction pure, testable sans arbre de scène ------------------------------

## Quel tronçon un nœud éteint. ⚠️ LE SUIVANT, PAS LE SIEN : éteindre son propre tronçon
## récompenserait après coup un joueur qui a déjà traversé le danger, et ne changerait donc
## rien à sa partie. Renvoie -1 quand il n'y a plus de suivant — le dernier nœud du survol ne
## soulage rien, et c'est une information de conception, pas un cas d'erreur.
static func silenced_section(section_index: int, section_count: int) -> int:
	var next := section_index + 1
	return next if next < section_count else -1
