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
const BULB_RADIUS := 0.52
const BULB_LIFT := 0.45
const BULB_TINT := Color("7a4de8")

# --- Les arcs ------------------------------------------------------------------
#
## ⚠️ LE NŒUD ÉTAIT « MOCHE », ET C'ÉTAIT UN PROBLÈME DE JEU AVANT D'ÊTRE UN PROBLÈME D'IMAGE.
## Une boule violette posée sur un socle ne dit pas « tire ici » : c'est la seule cible du
## niveau dont la récompense arrive quarante secondes plus tard, donc la seule qui doive
## s'annoncer d'elle-même. Des arcs qui en jaillissent le disent en une image — « on pourrait
## rajouter comme des éclairs qui en émanent, pour indiquer que c'est un point vital à tirer ? »
## (opérateur, 2026-08-29).
##
## ⚠️ ET ILS SONT REDESSINÉS, PAS ANIMÉS. Un arc électrique n'a pas de trajectoire : il
## RECOMMENCE. Une interpolation lisse se lirait comme un tentacule ; ce qu'il faut, c'est que
## la figure change d'un coup, quelques fois par seconde.
const ARC_COUNT := 5
const ARC_SEGMENTS := 4
const ARC_REACH := 1.35
const ARC_JITTER := 0.34
## Combien de fois par seconde la figure se refait. Plus haut, ça grésille et ça fatigue ;
## plus bas, on voit des traits fixes et l'illusion tombe.
const ARC_REDRAW_HZ := 11.0

signal destroyed(node: CortegeSpineNode)
## Il entre dans sa fenêtre de tir, pour la première et unique fois.
signal engaged(node: CortegeSpineNode)

var tuning: CortegeTuning
var section: int = 0

var _bullet_manager: BulletManager
var _vfx: VFXManager
var _target: BulletTarget
var _bulb: MeshInstance3D
var _bulb_material: StandardMaterial3D
var _arcs: MeshInstance3D
var _arc_mesh: ImmediateMesh
var _arc_timer: float = 0.0
## ⚠️ SEMÉE UNE FOIS, PAS À CHAQUE IMAGE. Cinq nœuds qui tireraient chacun vingt nombres au
## hasard par image, c'est un grésillement différent d'un lancement à l'autre — et surtout une
## figure qui ne se stabilise jamais assez longtemps pour être vue.
var _rng := RandomNumberGenerator.new()

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
	_build_arcs()

## Les arcs qui jaillissent du nœud. Un seul maillage pour les cinq : c'est un instrument de
## lecture, il ne doit pas coûter cinq objets par nœud et vingt-cinq par niveau.
func _build_arcs() -> void:
	_rng.seed = hash(name) + section * 7919
	_arc_mesh = ImmediateMesh.new()
	_arcs = MeshInstance3D.new()
	_arcs.name = "Arcs"
	_arcs.mesh = _arc_mesh
	_arcs.position.y = BULB_LIFT
	_arcs.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# ⚠️ Sans marge, l'arc disparaît dès que le centre du nœud sort du cadre : la boîte
	# englobante d'un `ImmediateMesh` vide est nulle au montage.
	_arcs.extra_cull_margin = 4.0
	var spark := StandardMaterial3D.new()
	spark.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	spark.vertex_color_use_as_albedo = true
	# ⚠️ ADDITIF ET SANS ÉCRITURE DE PROFONDEUR : un éclair passe DEVANT la coque sans la
	# masquer, et deux arcs qui se croisent s'additionnent au lieu de se découper.
	spark.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	spark.no_depth_test = true
	spark.render_priority = 6
	_arcs.material_override = spark
	add_child(_arcs)

## Refait la figure. ⚠️ Appelée quelques fois par seconde, jamais à chaque image.
func _redraw_arcs(energy: float) -> void:
	# ⚠️ Un banc monte la pièce SANS arbre : `_ready()` n'y tourne pas, donc le maillage n'existe
	# pas. C'est l'état normal d'un test, pas une panne — et c'est ce qui rend la logique du nœud
	# vérifiable sans scène.
	if _arc_mesh == null:
		return
	_arc_mesh.clear_surfaces()
	if energy <= 0.01:
		return
	_arc_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
	var tint := Color(BULB_TINT.r, BULB_TINT.g, BULB_TINT.b, 1.0) * energy
	var white := Color(1.0, 0.92, 1.0, 1.0) * energy
	for i in ARC_COUNT:
		var angle := TAU * (float(i) + _rng.randf() * 0.6) / float(ARC_COUNT)
		var direction := Vector3(cos(angle), 0.0, sin(angle))
		var up := Vector3.UP
		var previous := direction * BULB_RADIUS * 0.7
		for step in range(1, ARC_SEGMENTS + 1):
			var t := float(step) / float(ARC_SEGMENTS)
			var point := direction * (BULB_RADIUS * 0.7 + ARC_REACH * t)
			point += up * (_rng.randf_range(-ARC_JITTER, ARC_JITTER) + t * 0.35)
			point += Vector3(_rng.randf_range(-ARC_JITTER, ARC_JITTER), 0.0,
				_rng.randf_range(-ARC_JITTER, ARC_JITTER))
			# Le cœur est blanc, la pointe prend la couleur du nœud : c'est ce qui fait lire
			# une décharge plutôt qu'un fil.
			_arc_mesh.surface_set_color(white.lerp(tint, t - 1.0 / ARC_SEGMENTS))
			_arc_mesh.surface_add_vertex(previous)
			_arc_mesh.surface_set_color(white.lerp(tint, t))
			_arc_mesh.surface_add_vertex(point)
			previous = point
	_arc_mesh.surface_end()


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
func tick(delta: float, world: Vector3, here: Vector2) -> void:
	if _pass == Pass.PASSED:
		return
	_world = world
	var half := tuning.node_visible_span * 0.5
	match _pass:
		Pass.AHEAD:
			if here.y <= half:
				_pass = Pass.LIVE
				if _alive and _bullet_manager != null:
					_bullet_manager.register_target(_target)
					_target.enabled = true
				engaged.emit(self)
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
	var energy := 1.8 + 1.1 * sin(_pulse)
	if _bulb_material != null:
		_bulb_material.emission_energy_multiplier = energy
	_arc_timer -= delta
	if _arc_timer <= 0.0:
		_arc_timer = 1.0 / ARC_REDRAW_HZ
		_redraw_arcs(clampf(energy / 2.9, 0.35, 1.0))

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
	# ⚠️ LES ARCS S'ÉTEIGNENT AVEC LUI, et c'est la moitié de l'information : un nœud abattu qui
	# continuerait de crépiter dirait au joueur qu'il n'a rien fait.
	if _arc_mesh != null:
		_arc_mesh.clear_surfaces()
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
