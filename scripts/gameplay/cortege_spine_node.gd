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

## Le kit. ⚠️ LE NŒUD N'EST PLUS CUIT DANS LE TRONÇON, ET C'EST CE QUI LE REND MORTEL. Un bulbe
## cuit dans la coque partage les matériaux de ses quatre voisins : l'éteindre les éteignait
## tous. Le `BRIEF-0094` en a fait un kit pour la même raison que le hangar et la tourelle avant
## lui — une pièce qui meurt seule veut un matériau qui lui appartienne.
const KIT_PATH := "res://assets/imported/models/backgrounds/spine_kit.glb"

## Les cotes d'assemblage, RELEVÉES DANS LE BINAIRE et non recopiées du rapport de forge.
const CORE_LIFT := 0.21
const BRACE_LIFT := 0.30
const BRACE_GAUGE := 0.50
## L'écartement en Z de la famille à quatre entretoises.
const BRACE_SPREAD := 0.78

## Le centre de la lanterne : `spine_core` monte à +0,21, sa bande émissive court de 0,68 à 1,00
## dans son propre repère. C'est la seule hauteur qui compte pour le jeu — voir `HIT_LIFT`.
const LANTERN_Y := CORE_LIFT + 0.84
const LANTERN_RADIUS := 0.34

## ⚠️ CE QUE LE JOUEUR VISE N'EST PAS OÙ LA PIÈCE EST POSÉE, ET L'ÉCART SE VOIT.
##
## La caméra plonge à 70° : une cible haute d'un mètre se projette sur le plan de jeu à vingt
## bons centimètres de son assise. La zone de touche était calée sur l'assise, donc décalée vers
## l'arrière de tout ce que la pièce fait de haut. Sur un hangar, large de six mètres, personne
## ne le sentait ; sur le nœud, qui tient dans un rayon de 0,78 et qui est déjà la cible la plus
## dure du niveau, c'était un quart du rayon offert au hasard. On projette donc la LANTERNE.
const HIT_LIFT := LANTERN_Y

## La teinte de la lanterne, celle du kit (`AA_Emissive_Engine`). Les arcs et l'explosion la
## reprennent : ce qui jaillit du nœud et ce qui reste quand il meurt parlent de la même lumière.
const NODE_TINT := Color(1.0, 0.067, 0.479)

## Deux familles, par assemblage seul, comme les trois de la tourelle. ⚠️ TIRÉE DU TRONÇON, PAS
## DU HASARD : un tirage aléatoire donnerait une répartition différente à chaque lancement, donc
## deux captures qu'on ne peut plus comparer — et un survol se juge en comparant deux passages.
const BRACE_COUNT: Array[int] = [2, 4]

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

## De combien la lanterne bat, en part de l'énergie que la forge lui a calibrée. ⚠️ RELATIF ET
## NON ABSOLU : écrire une énergie en dur ici écraserait `emissiveStrength` du binaire, et la
## prochaine reforge qui la retoucherait n'aurait aucun effet — en silence.
const PULSE_DEPTH := 0.45

signal destroyed(node: CortegeSpineNode)
## Il entre dans sa fenêtre de tir, pour la première et unique fois.
signal engaged(node: CortegeSpineNode)

var tuning: CortegeTuning
var section: int = 0

var _bullet_manager: BulletManager
var _vfx: VFXManager
var _target: BulletTarget
## Le cœur, et lui seul. Berceau et entretoises lui survivent : un nœud abattu laisse une
## carcasse, et c'est ce qui rend sa mort lisible depuis le plan de vol.
var _core: Node3D
var _glow: Array[StandardMaterial3D] = []
## L'énergie que la forge a calibrée, lue au montage. Le battement l'entoure, il ne la remplace pas.
var _glow_base: float = 1.0
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
	_build_node()
	_build_arcs()


## Assemble les trois pièces du kit. Le berceau et les entretoises portent le nœud ; le cœur
## porte la lumière, et c'est le seul que la mort emporte.
func _build_node() -> void:
	var packed: PackedScene = load(KIT_PATH) as PackedScene
	if packed == null:
		push_error("[Cortege] kit d'épine introuvable : %s" % KIT_PATH)
		return
	var kit := packed.instantiate()
	_place(kit, "spine_cradle", Vector3.ZERO, 0.0)
	_core = _place(kit, "spine_core", Vector3(0.0, CORE_LIFT, 0.0), 0.0)
	var braces := BRACE_COUNT[section % BRACE_COUNT.size()]
	# ⚠️ LE YAW VAUT π À BÂBORD, ET L'INCLINAISON EST DANS LA GÉOMÉTRIE. La pièce penche toujours
	# vers son −X local : la retourner suffit à la faire pencher vers l'axe des deux côtés. Écrire
	# un tangage ici le ferait diverger du binaire à la première reforge.
	for side in [-1.0, 1.0]:
		var dz := 0.0 if braces == 2 else BRACE_SPREAD
		for offset in ([0.0] if braces == 2 else [-dz, dz]):
			_place(kit, "spine_brace",
				Vector3(side * BRACE_GAUGE, BRACE_LIFT, offset), 0.0 if side > 0.0 else PI)
	kit.queue_free()

func _place(kit: Node, part: String, offset: Vector3, yaw: float) -> MeshInstance3D:
	var source := kit.get_node_or_null(part) as MeshInstance3D
	if source == null:
		push_error("[Cortege] pièce de kit manquante : %s" % part)
		return null
	var piece := MeshInstance3D.new()
	piece.name = part
	piece.mesh = source.mesh
	piece.position = offset
	piece.rotation.y = yaw
	piece.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_claim_glow(piece, source)
	add_child(piece)
	return piece

## Donne à CE nœud sa propre copie du matériau de la lanterne.
##
## ⚠️ SANS CETTE COPIE, ABATTRE UN NŒUD ÉTEINDRAIT LES CINQ. C'est exactement le piège que le
## bulbe cuit dans la coque rendait inévitable, et il a déjà été payé sur les puits et sur les
## tourelles : un état par pièce demande un matériau par pièce.
func _claim_glow(piece: MeshInstance3D, source: MeshInstance3D) -> void:
	for i in source.mesh.get_surface_count():
		var base := source.mesh.surface_get_material(i) as StandardMaterial3D
		if base == null:
			continue
		if not base.emission_enabled:
			piece.set_surface_override_material(i, base)
			continue
		var mine: StandardMaterial3D = base.duplicate()
		piece.set_surface_override_material(i, mine)
		_glow_base = mine.emission_energy_multiplier
		_glow.append(mine)

## Les arcs qui jaillissent du nœud. Un seul maillage pour les cinq : c'est un instrument de
## lecture, il ne doit pas coûter cinq objets par nœud et vingt-cinq par niveau.
func _build_arcs() -> void:
	_rng.seed = hash(name) + section * 7919
	_arc_mesh = ImmediateMesh.new()
	_arcs = MeshInstance3D.new()
	_arcs.name = "Arcs"
	_arcs.mesh = _arc_mesh
	_arcs.position.y = LANTERN_Y
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
	var tint := Color(NODE_TINT.r, NODE_TINT.g, NODE_TINT.b, 1.0) * energy
	var white := Color(1.0, 0.92, 1.0, 1.0) * energy
	for i in ARC_COUNT:
		var angle := TAU * (float(i) + _rng.randf() * 0.6) / float(ARC_COUNT)
		var direction := Vector3(cos(angle), 0.0, sin(angle))
		var up := Vector3.UP
		var previous := direction * LANTERN_RADIUS
		for step in range(1, ARC_SEGMENTS + 1):
			var t := float(step) / float(ARC_SEGMENTS)
			var point := direction * (LANTERN_RADIUS + ARC_REACH * t)
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
	var swell := 1.0 + PULSE_DEPTH * sin(_pulse)
	for material in _glow:
		material.emission_energy_multiplier = _glow_base * swell
	_arc_timer -= delta
	if _arc_timer <= 0.0:
		_arc_timer = 1.0 / ARC_REDRAW_HZ
		_redraw_arcs(clampf(swell / (1.0 + PULSE_DEPTH), 0.35, 1.0))

func _take_damage(damage: float) -> void:
	if not _alive:
		return
	_health -= damage
	if _health > 0.0:
		return
	_alive = false
	# ⚠️ LE CŒUR DISPARAÎT, LE BERCEAU RESTE. C'est toute la raison d'être du kit : ce qui reste
	# après le tir est une carcasse sombre, donc une preuve visible depuis le plan de vol qu'on
	# est passé par là. Éteindre la lanterne sans retirer le cœur laisserait un nœud intact et
	# muet, indiscernable d'un nœud jamais touché.
	for material in _glow:
		material.emission_energy_multiplier = 0.0
	_glow.clear()
	if _core != null:
		_core.queue_free()
		_core = null
	# ⚠️ LES ARCS S'ÉTEIGNENT AVEC LUI, et c'est la moitié de l'information : un nœud abattu qui
	# continuerait de crépiter dirait au joueur qu'il n'a rien fait.
	if _arc_mesh != null:
		_arc_mesh.clear_surfaces()
	if _vfx != null:
		_vfx.spawn_explosion(_world, VfxExplosion.Category.MEDIUM, NODE_TINT)
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
static func weakened_section(section_index: int, section_count: int) -> int:
	var next := section_index + 1
	return next if next < section_count else -1
