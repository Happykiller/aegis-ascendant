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
func pulse_target_marker(age: float) -> void:
	if _marker == null or not _marker.visible:
		return
	var beat := 0.5 + 0.5 * sin(age * MARKER_PULSE_RATE)
	_marker.pixel_size = MARKER_SIZE * (1.0 + MARKER_SWELL * beat)
	_marker.modulate = Color(1.0, 0.45 + 0.35 * beat, 0.25 + 0.2 * beat,
		0.55 + 0.45 * beat)

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
