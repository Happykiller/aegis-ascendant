class_name CoreInterior
extends Node3D
## L'intérieur du noyau du Pale Leviathan — une **zone dédiée**, pas une bulle dessinée
## autour du boss.
##
## ⚠️ CE QU'IL REMPLACE, ET POURQUOI. La plongée d'`ADR-0021` construisait au vol une
## `SphereMesh` de 7 m **retournée** autour du corps du boss. Verdict de l'opérateur au
## playtest du 2026-08-25 : « on n'a pas la sensation que le noyau s'ouvre et qu'on rentre
## dedans, plus qu'il change, et on perd de vue le vaisseau qui est dans la sphère ». Il
## décrivait exactement ce que le code faisait : le chasseur n'allait NULLE PART, on
## dessinait une bulle autour de tout et la caméra glissait de moitié.
##
## Ici, on entre vraiment : le décor est monté **à l'origine du monde**, à l'échelle du plan
## de jeu (`GameplayPlane.BOUNDS`, 28 × 16 m), et l'extérieur est masqué. Conséquence
## voulue et décisive : **une fois dedans, la caméra reprend son cadrage NORMAL**. C'est ce
## qui règle « on perd de vue le vaisseau » — dans le noyau, le jeu se lit comme partout
## ailleurs. Le zoom sert la transition, jamais la phase.

## Décor livré par la forge (BRIEF-0082). Chargé à l'exécution et non `preload` : le jeu
## doit tourner avant que la forge ait livré, sans quoi le code ne serait ni jouable ni
## testable tant qu'un asset manque.
const DECOR_PATH := "res://assets/imported/models/bosses/core_interior.glb"

## Contrat de noms attendu du décor (BRIEF-0082).
const ANCHOR_REACTOR := "Reactor_Core"
const ANCHOR_ENTRY := "Entry_Point"

## Position du réacteur dans le plan, quand le décor ne porte pas son point d'ancrage.
## Le centre : c'est là que le brief demande le réacteur, et un décor qui l'a déplacé sans
## poser l'ancre est un défaut d'asset, pas une raison de faire tomber le combat.
const FALLBACK_REACTOR := Vector2.ZERO
## Entrée par le bas du cadre — la convention du shooter vertical, celle que le joueur a
## déjà apprise. `GameplayPlane.BOUNDS` descend à −8.
const FALLBACK_ENTRY := Vector2(0.0, -6.0)

var _decor: Node3D
var _reactor_plane: Vector2 = FALLBACK_REACTOR

## Le repère de cible : un point doux, additif, qui SUIT le flux et qui BAT.
## Le décor ne bat pas — c'est ce qui distingue la cible de ce qui l'entoure.
var _marker: Sprite3D

## Hauteur du repère au-dessus du plan. Assez pour ne pas s'enfoncer dans le décor du
## réacteur, assez peu pour rester à la même profondeur que le chasseur.
const MARKER_LIFT := 0.15
const MARKER_SIZE := 0.030
const MARKER_SWELL := 0.35
const MARKER_PULSE_RATE := 5.0

# --- Le blindage rotatif (plan « Reactor Chamber », lot 1) -------------------

## ⚠️ LE RAYON ET L'ÉPAISSEUR NE VIVENT PLUS ICI. Ils sont portés par chaque `ReactorRing`,
## avec ses ouvertures : la collision et l'image doivent lire LA MÊME donnée, sinon le joueur
## se cogne à un mur qu'il ne voit pas — ou traverse celui qu'il voit.

## Hauteur d'un mur. ⚠️ Il en a une, désormais : « faut leur donner un corps, pas qu'un halo
## de couleur » (playtest du 2026-08-27). Une face interne, une face externe, un dessus.
const RING_HEIGHT := 0.70
## Nombre de segments par degré d'arc. Un arc de 100° en fait donc une vingtaine — assez
## pour que le bord ne se lise pas comme un polygone, assez peu pour ne rien coûter.
const RING_STEP_DEG := 5.0
## Côté, en mètres, de la tuile de blindage (1 unité = 1 m, ADR-0008).
##
## ⚠️ 2 -> 4 APRÈS LA PREMIÈRE CAPTURE TEXTURÉE, et c'est un recalage prévu : `TEX-0009`
## déclare son échelle en `decided`, pas en `measured`, précisément parce qu'elle ne se
## tranche qu'en regardant. À 2 m la tuile rendait du GRAIN : la bande vue ne fait qu'une
## trentaine de pixels de large après le post-process rétro, et des plaques de 0,8 m y
## tombaient à 24 px, les têtes de boulon à 3 px — sous le pixel, donc du bruit.
##
## À 4 m, une plaque occupe ~1,6 m de monde et déborde la largeur du mur : on en voit UNE
## en travers, avec son chanfrein. C'est ce qu'on veut lire — un blindage appareillé, pas
## une texture. La même image sert, sans regénération : c'est tout l'intérêt d'avoir posé
## l'échelle comme une décision rattrapable.
const TILE_M := 8.0

## La matière du blindage — TEX-0009, dérivées d'`ADR-0013` (la normale ne se génère jamais).
const _TEX_DIR := "res://assets/imported/textures/bosses/"
const ARMOUR_MUL := preload(_TEX_DIR + "reactor_armour_height_1024_mul.png")
const ARMOUR_NRM := preload(_TEX_DIR + "reactor_armour_height_1024_nrm.png")
const ARMOUR_ROUGH := preload(_TEX_DIR + "reactor_armour_height_1024_rough.png")
const ARMOUR_AO := preload(_TEX_DIR + "reactor_armour_height_1024_ao.png")

## ⚠️ SOUS LE PLAN DE JEU, ET C'EST UNE RÈGLE DE LECTURE. L'ordre de priorité est
## joueur > projectiles > dangers > point faible > MACHINES > décor : un anneau posé à
## y = 0 serait coplanaire aux balles et les masquerait une fois sur deux.
##
## ⚠️ MAIS PAS TROP BAS. À −0,30, les anneaux passaient SOUS les nervures du décor livré et
## se lisaient comme de la peinture au sol — pas comme la machine qui bloque. Ils remontent
## juste sous le plan : au-dessus du sol, en dessous de tout ce qui se joue.
const RING_LIFT := -0.08

var _rings: Array[Node3D] = []

## Taille d'un verrou à l'écran.
##
## ⚠️ 0,055 A ÉTÉ ESSAYÉ ET REGARDÉ : les verrous rendaient des NUAGES de 180 px, plus larges
## que le réacteur lui-même. Un point doux grossi ne devient pas une pièce, il devient une
## brume — et une pièce à abattre doit avoir un bord. On reste juste au-dessus du repère de
## cible (0,030) : plus gros que lui, sans lui disputer l'écran.
const NODE_SIZE := 0.018
var _nodes: Array[Sprite3D] = []
var _entry_plane: Vector2 = FALLBACK_ENTRY
## Vrai quand on a monté la doublure procédurale faute de décor livré. Le niveau le
## journalise : un intérieur en doublure ne doit jamais passer pour l'asset final.
var _is_stand_in: bool = false

func _ready() -> void:
	visible = false
	_build()

func is_stand_in() -> bool:
	return _is_stand_in

## Position du réacteur dans le plan de jeu — la cible de la phase.
## Pose le repère de cible sur le flux, dans le plan de jeu. Le rendre invisible en
## passant `false` (hors plongée).
##
## ⚠️ CE QU'IL FERME, ET CE N'ÉTAIT PAS UN MANQUE DE DÉCORATION. La cible réelle dérive
## jusqu'à ~2,6 u de l'ancre, et RIEN ne la dessinait dans l'arène : le halo du flux se pose
## sur le cœur du boss, resté DEHORS pendant la plongée. Le joueur tirait donc sur le
## réacteur du décor pendant que la cible était ailleurs — « le noyau semble juste un point
## du décor » (playtest du 2026-08-27). Un signal faux, pas un signal absent.
func set_target_marker(plane_position: Vector2, lit: bool) -> void:
	if _marker == null:
		return
	_marker.visible = lit
	if not lit:
		return
	_marker.position = GameplayPlane.to_world(plane_position) + Vector3(0.0, MARKER_LIFT, 0.0)

## Fait battre le repère. Appelé par le niveau, à l'image : le battement est ce qui le
## sépare du décor, qui lui ne bat pas.
## `exposed` : le corridor est-il ouvert sur l'azimut du joueur ?
##
## ⚠️ LE BATTEMENT PORTE L'INFORMATION, pas l'interface. Le joueur doit savoir si son tir
## compte SANS lire le HUD — c'est la règle que la spec de l'opérateur pose elle-même : « la
## vulnérabilité doit être compréhensible sans lire l'UI ». Fermé, le repère respire
## lentement et pâle ; ouvert, il bat vite et blanchit.
func pulse_target_marker(age: float, exposed: bool = true) -> void:
	if _marker == null or not _marker.visible:
		return
	var rate := MARKER_PULSE_RATE if exposed else MARKER_PULSE_RATE * 0.35
	var beat := 0.5 + 0.5 * sin(age * rate)
	var swell := MARKER_SWELL if exposed else MARKER_SWELL * 0.4
	_marker.pixel_size = MARKER_SIZE * (1.0 + swell * beat)
	if exposed:
		_marker.modulate = Color(1.0, 0.72 + 0.28 * beat, 0.55 + 0.45 * beat,
			0.75 + 0.25 * beat)
	else:
		_marker.modulate = Color(0.85, 0.32 + 0.14 * beat, 0.22 + 0.10 * beat,
			0.30 + 0.18 * beat)

## Dresse le blindage : un nœud par anneau, chacun portant ses arcs pleins.
##
## La géométrie se déduit des MÊMES données que le gameplay (`ReactorRing`) : c'est ce qui
## garantit qu'on tire là où l'on voit une ouverture. Deux sources séparées auraient fini
## par diverger, et le joueur aurait tiré dans un blindage plein en croyant viser un trou.
func build_rings(rings: Array[ReactorRing]) -> void:
	for node in _rings:
		node.queue_free()
	_rings.clear()
	for i in rings.size():
		var ring := rings[i]
		if ring == null:
			continue
		var pivot := Node3D.new()
		pivot.name = "Ring%d" % i
		pivot.position = Vector3(0.0, RING_LIFT, 0.0)
		var step := 360.0 / float(ring.apertures)
		# Un arc PLEIN entre deux ouvertures : on dessine ce qui bloque, pas ce qui ouvre.
		var solid := step - ring.aperture_deg
		for k in ring.apertures:
			var start := float(k) * step + ring.aperture_deg * 0.5
			pivot.add_child(_arc(ring.radius, ring.thickness, start, solid, i * ring.apertures + k))
		add_child(pivot)
		_rings.append(pivot)

## Fait tourner le blindage. `age` est celui du COMBAT — le même que celui dont
## `ReactorRings` déduit l'ouverture, sinon l'image mentirait sur l'état du jeu.
func pose_rings(rings: Array[ReactorRing], age: float) -> void:
	for i in mini(_rings.size(), rings.size()):
		var ring := rings[i]
		if ring == null:
			continue
		_rings[i].rotation.y = -deg_to_rad(ring.phase_deg + ring.speed_deg * age)

## Un arc plein, à plat dans le plan, en `ArrayMesh`. ⚠️ La rotation d'un `Node3D` autour de
## Y va dans le sens INVERSE de l'azimut du plan (le monde −Z est le haut de l'écran) : d'où
## le signe de `pose_rings`. Une erreur ici décalerait l'image de l'ouverture réelle, ce qui
## est le seul défaut que cette phase ne peut pas se permettre.
func _arc(radius: float, thickness: float, start_deg: float, span_deg: float,
		index: int) -> MeshInstance3D:
	var inner := radius - thickness * 0.5
	var outer := radius + thickness * 0.5
	var steps := maxi(int(span_deg / RING_STEP_DEG), 2)
	var lift := Vector3(0.0, RING_HEIGHT, 0.0)
	# ⚠️ SOUPE DE TRIANGLES, PAS UN MAILLAGE INDEXÉ, et c'est le fond du défaut signalé au
	# playtest : « les murs sont pas complets, on dirait juste des U inversés ». La version
	# indexée partageait ses sommets entre le dessus et les parois, ce qui interdit une
	# normale PAR FACE — le bloc rendait donc à plat, sans arête, et se lisait comme une
	# coquille. Et il l'était : il n'avait ni dessous ni bouchons d'extrémité, on voyait
	# dedans au bord des ouvertures.
	#
	# Ici chaque quad porte ses quatre sommets et sa normale. Six faces, le volume est CLOS,
	# et l'éclairage donne enfin une arête au sommet du mur. Le coût est nul à cette échelle
	# (~400 triangles pour tout le blindage), et c'est ce que « faut leur donner un corps,
	# pas qu'un halo de couleur » demandait vraiment.
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	# Le dépliage, en LONGUEUR D'ARC RÉELLE et non en fraction d'angle. Les deux anneaux n'ont
	# pas le même rayon (5,8 m et 2,2 m) : à fraction d'angle égale, la plaque du mur extérieur
	# serait étirée deux fois et demie plus que celle du mur intérieur, et la même texture
	# rendrait deux matières différentes. Ici la densité de texels est la MÊME partout.
	var wide := thickness / TILE_M
	var tall := RING_HEIGHT / TILE_M
	# ⚠️ CHAQUE ARC LIT UNE BANDE DIFFÉRENTE DE LA TUILE, et ce n'est pas une coquetterie.
	# Le mur fait 1,00 m pour une tuile de 2 m : la face vue n'échantillonne que `v` de 0 à
	# 0,50. Sans décalage, LA MOITIÉ HAUTE DE LA TEXTURE NE SERAIT JAMAIS VUE — et les cinq
	# arcs porteraient tous exactement la même plaque, ce qui se remarque d'autant plus qu'ils
	# tournent l'un devant l'autre. Deux décalages irrationnels entre eux (racine de 2 et
	# nombre d'or moins un) ne reviennent jamais en phase : la tuile est employée en entier et
	# aucun arc n'est le jumeau d'un autre.
	var slide_u := fmod(float(index) * 0.6180339887, 1.0)
	var slide_v := fmod(float(index) * 0.4142135624, 1.0)
	for s in steps:
		var a0 := deg_to_rad(start_deg + span_deg * float(s) / float(steps))
		var a1 := deg_to_rad(start_deg + span_deg * float(s + 1) / float(steps))
		var r0 := Vector3(cos(a0), 0.0, sin(a0))
		var r1 := Vector3(cos(a1), 0.0, sin(a1))
		var i0 := r0 * inner
		var o0 := r0 * outer
		var i1 := r1 * inner
		var o1 := r1 * outer
		var radial := (r0 + r1).normalized()
		var u0 := slide_u + radius * (a0 - deg_to_rad(start_deg)) / TILE_M
		var u1 := slide_u + radius * (a1 - deg_to_rad(start_deg)) / TILE_M
		_quad(vertices, normals, uvs, i0 + lift, o0 + lift, o1 + lift, i1 + lift, Vector3.UP,
			Vector2(u0, slide_v), Vector2(u0, slide_v + wide), Vector2(u1, slide_v + wide), Vector2(u1, slide_v))
		_quad(vertices, normals, uvs, i1, o1, o0, i0, Vector3.DOWN,
			Vector2(u1, slide_v), Vector2(u1, slide_v + wide), Vector2(u0, slide_v + wide), Vector2(u0, slide_v))
		_quad(vertices, normals, uvs, o0, o1, o1 + lift, o0 + lift, radial,
			Vector2(u0, slide_v), Vector2(u1, slide_v), Vector2(u1, slide_v + tall), Vector2(u0, slide_v + tall))
		_quad(vertices, normals, uvs, i1, i0, i0 + lift, i1 + lift, -radial,
			Vector2(u1, slide_v), Vector2(u0, slide_v), Vector2(u0, slide_v + tall), Vector2(u1, slide_v + tall))
	# Les BOUCHONS. Un arc s'arrête net des deux côtés, et ces deux tranches bordent
	# précisément les ouvertures — c'est-à-dire le seul endroit que le joueur regarde.
	var ab := deg_to_rad(start_deg)
	var ae := deg_to_rad(start_deg + span_deg)
	var rb := Vector3(cos(ab), 0.0, sin(ab))
	var re := Vector3(cos(ae), 0.0, sin(ae))
	var tb := Vector3(-sin(ab), 0.0, cos(ab))
	var te := Vector3(-sin(ae), 0.0, cos(ae))
	_quad(vertices, normals, uvs, rb * inner, rb * outer, rb * outer + lift, rb * inner + lift, -tb,
		Vector2(slide_u, slide_v), Vector2(slide_u + wide, slide_v),
		Vector2(slide_u + wide, slide_v + tall), Vector2(slide_u, slide_v + tall))
	_quad(vertices, normals, uvs, re * outer, re * inner, re * inner + lift, re * outer + lift, te,
		Vector2(slide_u, slide_v), Vector2(slide_u + wide, slide_v),
		Vector2(slide_u + wide, slide_v + tall), Vector2(slide_u, slide_v + tall))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	# ⚠️ LES TANGENTES, ET LEUR ABSENCE NE PRODUIT AUCUNE ERREUR. Une carte de normale se lit
	# dans le repère tangent : sans `ARRAY_TANGENT`, Godot n'a pas ce repère et l'éclairage
	# part au hasard, sommet par sommet. À l'écran ça ne ressemble pas à un bug — ça ressemble
	# à du GRAIN, et on croit à une texture trop fine. J'ai d'abord recalé l'échelle de la
	# tuile pour ça, sans effet : le défaut n'était pas là.
	#
	# `generate_tangents()` les calcule depuis les normales et les UV, qu'on a déjà.
	var tangents := SurfaceTool.new()
	tangents.create_from(mesh, 0)
	tangents.generate_tangents()
	var node := MeshInstance3D.new()
	node.mesh = tangents.commit()
	var material := StandardMaterial3D.new()
	# Sombre et peu saturé : c'est une MACHINE, elle passe derrière le gameplay. Un corps
	# éclairé — pas un aplat émissif — pour qu'on lise son volume et non une décalcomanie.
	#
	# La MATIÈRE vient de TEX-0009 (BRIEF-0027). ⚠️ `albedo_texture` reçoit la carte de
	# MULTIPLICATION, pas un albédo : Godot calcule `albedo = albedo_texture x albedo_color`,
	# donc la teinte violet-graphite ci-dessous survit et seuls les creux s'assombrissent.
	# C'est le mécanisme d'`ADR-0011`, et il évite une seconde génération d'image.
	material.albedo_color = Color(0.22, 0.19, 0.28)
	material.albedo_texture = ARMOUR_MUL
	material.normal_enabled = true
	material.normal_texture = ARMOUR_NRM
	material.normal_scale = 1.6
	material.roughness_texture = ARMOUR_ROUGH
	material.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	material.ao_enabled = true
	material.ao_texture = ARMOUR_AO
	material.ao_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	# 0 = l'AO n'assombrit que l'ambiante. Au-delà elle mange la lumière directe et le
	# blindage vire au gris sale sous la clé.
	material.ao_light_affect = 0.0
	material.metallic = 0.55
	material.roughness = 0.45
	# ⚠️ ÉMISSION DIVISÉE PAR TROIS (0,30 -> 0,10) LE JOUR OÙ LA MATIÈRE EST ARRIVÉE. Elle
	# était là pour qu'un volume nu se voie ; elle laverait maintenant le relief qu'elle
	# remplaçait. On en garde juste assez pour que le mur ne disparaisse pas dans le noir
	# quand il passe hors de la clé.
	material.emission_enabled = true
	material.emission = Color(0.42, 0.22, 0.60)
	material.emission_energy_multiplier = 0.10
	# ⚠️ ON NE CULLE PAS, alors même que le volume est clos désormais. Godot enroule ses faces
	# avant dans le sens HORAIRE, et je n'ai pas vérifié le sens de CES quads : activer
	# `CULL_BACK` sur une supposition ferait disparaître des murs entiers. Le volume étant
	# opaque et fermé, le tampon de profondeur suffit — le rendu est identique, et gratuit.
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	node.material_override = material
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return node

## Un quad plat, en deux triangles, avec SA normale sur ses quatre sommets. Les sommets ne
## sont partagés avec aucune autre face : c'est ce qui donne une arête franche au mur.
func _quad(vertices: PackedVector3Array, normals: PackedVector3Array, uvs: PackedVector2Array,
		a: Vector3, b: Vector3, c: Vector3, d: Vector3, normal: Vector3,
		ua: Vector2, ub: Vector2, uc: Vector2, ud: Vector2) -> void:
	vertices.append_array([a, b, c, a, c, d])
	uvs.append_array([ua, ub, uc, ua, uc, ud])
	for i in 6:
		normals.append(normal)

## Dresse les verrous orbitaux. Même point doux que le repère de cible, en plus gros et en
## CYAN-VERT : ils ne sont ni la cible (orange) ni le blindage (violet), et le joueur doit
## pouvoir les distinguer d'un coup d'œil pendant qu'il cherche son corridor.
func build_nodes(count: int) -> void:
	for node in _nodes:
		node.queue_free()
	_nodes.clear()
	for i in count:
		var sprite := Sprite3D.new()
		sprite.name = "Lock%d" % i
		sprite.texture = SoftDot.texture()
		sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		sprite.shaded = false
		sprite.transparent = true
		sprite.no_depth_test = true
		sprite.render_priority = 3
		sprite.pixel_size = NODE_SIZE
		sprite.visible = false
		add_child(sprite)
		_nodes.append(sprite)

## Pose un verrou. `alive` faux l'éteint — un verrou abattu ne doit plus rien désigner.
##
## ⚠️ Appelée par index et non par tableau : un `PackedVector2Array` reconstruit à chaque
## image allouerait soixante fois par seconde, pour quatre positions.
func pose_node(index: int, plane_position: Vector2, alive: bool, age: float) -> void:
	if index < 0 or index >= _nodes.size():
		return
	var sprite := _nodes[index]
	sprite.visible = alive
	if not alive:
		return
	sprite.position = GameplayPlane.to_world(plane_position) + Vector3(0.0, MARKER_LIFT, 0.0)
	# Ils RESPIRENT, sans battre : le battement rapide appartient au noyau vulnérable, et
	# deux choses qui battent pareil se lisent comme la même chose.
	var breath := 0.5 + 0.5 * sin(age * 2.1 + float(index) * 1.7)
	sprite.modulate = Color(0.40 + 0.22 * breath, 1.0, 0.72 + 0.20 * breath,
		0.55 + 0.30 * breath)

func reactor_plane_position() -> Vector2:
	return _reactor_plane

## Où le chasseur apparaît en arrivant.
func entry_plane_position() -> Vector2:
	return _entry_plane

func _build() -> void:
	if ResourceLoader.exists(DECOR_PATH):
		var packed := load(DECOR_PATH) as PackedScene
		if packed != null:
			_decor = packed.instantiate() as Node3D
	if _decor == null:
		_decor = _build_stand_in()
		_is_stand_in = true
	add_child(_decor)
	_read_anchors()
	_build_marker()

## Lit les points d'ancrage du décor. Un ancrage absent DÉGRADE vers une valeur sensée et
## le dit : c'est la règle du projet pour les pièces d'asset manquantes (cf. les bouches de
## canon du chasseur), parce qu'un combat qui plante vaut moins qu'un combat imparfait.
## Le repère est construit ICI et non dans le décor livré : il doit exister même quand la
## forge n'a rien livré (doublure), sans quoi la cible redeviendrait invisible au premier
## décor manquant — exactement le cas où l'on en a le plus besoin.
func _build_marker() -> void:
	_marker = Sprite3D.new()
	_marker.name = "TargetMarker"
	_marker.texture = SoftDot.texture()
	_marker.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_marker.shaded = false
	_marker.transparent = true
	_marker.no_depth_test = true
	_marker.render_priority = 4
	_marker.pixel_size = MARKER_SIZE
	_marker.visible = false
	add_child(_marker)

func _read_anchors() -> void:
	_reactor_plane = _anchor_or(ANCHOR_REACTOR, FALLBACK_REACTOR)
	_entry_plane = _anchor_or(ANCHOR_ENTRY, FALLBACK_ENTRY)

func _anchor_or(anchor_name: String, fallback: Vector2) -> Vector2:
	if _decor == null:
		return fallback
	var node := _decor.find_child(anchor_name, true, false) as Node3D
	if node == null:
		if not _is_stand_in:
			push_warning("[CoreInterior] décor sans ancrage '%s' (contrat BRIEF-0082)" % anchor_name)
		return fallback
	return _plane_of(node)

## Position d'un nœud du décor dans le plan de jeu, en REMONTANT la chaîne de parenté.
##
## ⚠️ NE JAMAIS LIRE `position` SEULE : elle est LOCALE. Un ancrage imbriqué sous un pivot
## rendrait une coordonnée fausse, plausible, et parfaitement silencieuse — la cible de la
## phase se poserait à côté du réacteur sans que rien ne le signale.
## Ce n'est pas une précaution théorique : le 2026-08-25, le Specter-9 a été mesuré ainsi,
## bornes agrégées en espace local, et rendu **1,29 m** de large au lieu de **1,752 m** —
## ses ailes sont portées par des nœuds transformés. Le chiffre faux est parti dans un
## brief de forge avant d'être rattrapé.
## `global_position` ne suffit pas non plus : hors de l'arbre — le régime des tests — il ne
## veut rien dire. On compose donc les transformations jusqu'au décor, ce qui est juste
## dans les deux cas.
func _plane_of(node: Node3D) -> Vector2:
	var local := Transform3D.IDENTITY
	var walk: Node = node
	while walk != null and walk != _decor:
		var as_3d := walk as Node3D
		if as_3d != null:
			local = as_3d.transform * local
		walk = walk.get_parent()
	# Le plan de jeu est (X, −Z) : même projection que les bouches de canon du chasseur.
	return Vector2(local.origin.x, -local.origin.z)

# --- Doublure procédurale ---------------------------------------------------
#
# ⚠️ CE N'EST PAS L'ASSET, et ça ne doit jamais en tenir lieu à la livraison. Elle existe
# pour que la MÉCANIQUE — bascule, cadrage, cible, entrée du chasseur — soit jouable et
# testable avant que la forge ait rendu. Un sol, une bordure, quatre travées, un réacteur :
# juste assez pour qu'on lise un lieu vu du dessus.

func _build_stand_in() -> Node3D:
	var root := Node3D.new()
	root.name = "StandIn"
	var bounds := GameplayPlane.BOUNDS
	root.add_child(_slab("Floor", Vector3(bounds.size.x + 4.0, 0.2, bounds.size.y + 4.0),
		Vector3(0.0, -0.6, 0.0), Color(0.07, 0.04, 0.10), 0.0))
	# La bordure : quatre pans bas, inclinés vers l'intérieur par leur seule position. Ils
	# ferment le cadre sans monter assez haut pour cacher le chasseur.
	var half_x := bounds.size.x * 0.5 + 1.0
	var half_z := bounds.size.y * 0.5 + 1.0
	root.add_child(_slab("Rim_01", Vector3(bounds.size.x + 4.0, 2.2, 0.6),
		Vector3(0.0, 0.2, -half_z), Color(0.11, 0.06, 0.15), 0.10))
	root.add_child(_slab("Rim_02", Vector3(bounds.size.x + 4.0, 2.2, 0.6),
		Vector3(0.0, 0.2, half_z), Color(0.11, 0.06, 0.15), 0.10))
	root.add_child(_slab("Rim_03", Vector3(0.6, 2.2, bounds.size.y + 4.0),
		Vector3(-half_x, 0.2, 0.0), Color(0.11, 0.06, 0.15), 0.10))
	root.add_child(_slab("Rim_04", Vector3(0.6, 2.2, bounds.size.y + 4.0),
		Vector3(half_x, 0.2, 0.0), Color(0.11, 0.06, 0.15), 0.10))
	# Quatre travées vers le centre : elles donnent l'échelle et le sens de lecture.
	root.add_child(_slab("Catwalk_01", Vector3(9.0, 0.3, 1.6), Vector3(-6.5, -0.35, 0.0),
		Color(0.16, 0.10, 0.20), 0.05))
	root.add_child(_slab("Catwalk_02", Vector3(9.0, 0.3, 1.6), Vector3(6.5, -0.35, 0.0),
		Color(0.16, 0.10, 0.20), 0.05))
	root.add_child(_slab("Catwalk_03", Vector3(1.6, 0.3, 5.0), Vector3(0.0, -0.35, -4.5),
		Color(0.16, 0.10, 0.20), 0.05))
	root.add_child(_slab("Catwalk_04", Vector3(1.6, 0.3, 5.0), Vector3(0.0, -0.35, 4.5),
		Color(0.16, 0.10, 0.20), 0.05))
	# Le réacteur : la seule chose claire et chaude du lieu. Le décor RECULE pour que la
	# cible avance — l'erreur déjà payée sur ce boss était d'avoir peint les deux dans la
	# même teinte, à dix points d'écart R−G.
	var reactor := _slab("Reactor", Vector3(4.0, 1.4, 4.0), Vector3(0.0, 0.1, 0.0),
		Color(1.0, 0.92, 0.72), 3.2)
	root.add_child(reactor)
	return root

func _slab(slab_name: String, size: Vector3, at: Vector3, tint: Color, glow: float) -> MeshInstance3D:
	var box := BoxMesh.new()
	box.size = size
	var material := StandardMaterial3D.new()
	material.albedo_color = tint
	if glow > 0.0:
		material.emission_enabled = true
		material.emission = tint
		material.emission_energy_multiplier = glow
	var mesh := MeshInstance3D.new()
	mesh.name = slab_name
	mesh.mesh = box
	mesh.material_override = material
	mesh.position = at
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mesh
