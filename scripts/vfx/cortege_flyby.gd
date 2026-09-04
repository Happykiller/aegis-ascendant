class_name CortegeFlyby
extends Node3D
## La coque du Long Cortège qui défile sous le joueur pendant tout le niveau 2.
##
## ⚠️ IL REMPLACE LE FOND, IL NE S'Y AJOUTE PAS. Même arbitrage que le survol de lune
## (`ADR-0027`) et pour la même raison mesurée : sur la machine qui contraint, le fond spatial
## complet coûte 13,05 ms sur les 16,67 disponibles à 60 Hz. Une coque pleine page PAR-DESSUS
## lui ne tiendrait pas. Le décor porte donc son propre ciel, en `deep_sky`.
##
## ⚠️ ET LA DIFFÉRENCE AVEC LA LUNE EST LE MÉCANISME MÊME. La lune défile par ROTATION : sa
## surface tourne, on ne la parcourt jamais. Ici on va d'un bout à l'autre d'un objet fini, dans
## un seul sens, sans jamais revenir en arrière — c'est une TRANSLATION, et c'est ce qui rend
## chaque cible ratée définitivement ratée.
##
## Le `.glb` est chargé au RUNTIME et non `preload` : le niveau doit être jouable et mesurable
## avant que la forge ait livré (`BRIEF-0089`). Sans lui, une doublure procédurale prend sa
## place et le journal le dit — une doublure qui se croit livrée est le genre de défaut muet que
## ce dépôt collectionne.

const DECOR_PATH := "res://assets/imported/models/backgrounds/long_cortege.glb"

## Le plafond du plan de jeu. ⚠️ RIEN DE LA COQUE NE MONTE AU-DESSUS : un volume qui traverserait
## le plan masquerait le combat sans jamais pouvoir être touché. Repris de `MoonFlyby`, où c'est
## un test qui l'a attrapé la première fois.
const CEILING_Y := -3.0

## Le plafond des PIÈCES DE GAMEPLAY, et il est plus haut que celui du décor.
##
## ⚠️ LA DISTINCTION N'EST PAS UN ASSOUPLISSEMENT, C'EST LA RÈGLE LUE CORRECTEMENT. Ce que le
## plafond protège tient en une phrase : « masquerait le combat SANS JAMAIS POUVOIR ÊTRE TOUCHÉ ».
## Une tourelle se tire dessus — la seconde moitié ne s'applique pas à elle, et la première non
## plus : à −2,40 elle reste 2,40 unités SOUS le plan de vol, elle ne peut ni masquer le chasseur
## ni le heurter.
##
## ⚠️ ET LA CONTRAINTE EST MESURÉE, PAS THÉORIQUE. La hauteur de 1,70 m demandée par la planche
## de l'opérateur ne tient pas sous −3,00 à DIX emplacements sur dix-sept : la chine du bordé n'y
## laisse que 1,28 m. Les trois issues étaient d'écarter dix marqueurs, de rabaisser les tourelles
## à 1,25 m — et de redevenir le jeton qu'on vient de remplacer —, ou de lire la règle pour ce
## qu'elle dit. Dépassement au pire : 0,42 m.
const GAMEPLAY_CEILING_Y := -2.4

## Le ciel propre au survol, sous la coque. Plus bas que le fond habituel (-5) pour loger la
## coque entre lui et le plan de jeu.
const SKY_Y := -38.0
const SKY_SIZE := Vector2(320.0, 260.0)

## ⚠️ LA COQUE LIVRÉE PORTE DÉJÀ SA HAUTEUR. Ses sommets vont de -12,60 à -3,20 : la forge l'a
## dessinée pour tenir juste sous le plafond du plan de jeu. Y ajouter un décalage la
## renfoncerait de douze unités et rendrait faux tout ce qu'elle a calculé. La doublure, elle,
## est bâtie à cette même hauteur pour que les deux se remplacent sans rien changer d'autre.
const HULL_Y := -8.0

## Largeur de la coque, en unités.
##
## ⚠️ ELLE NE REMPLIT PAS LE CADRE, ET C'EST VOULU. La caméra plonge à 70° et voit très loin
## devant : à Z = -70, le cadre fait 170 unités de large. Aucune coque rigide ne peut couvrir
## à la fois cette distance et le premier plan — la lune du niveau 1 n'y arrive qu'en étant une
## sphère de 60 de rayon. Les trois maquettes tranchent la question : la coque y occupe le
## centre, et l'espace se voit de part et d'autre. 44 unités la font tenir les deux tiers du
## cadre au premier plan, comme sur les planches. Mesuré en capture, pas estimé.
const HULL_WIDTH := 44.0

## De combien le vaisseau commence EN AVANT du joueur.
##
## ⚠️ SANS LUI, LE SURVOL COMMENCE AU MILIEU DE LA PROUE. La coque livrée s'étend de Z = -500
## (l'arrière, où Ambry est greffé) à Z = 0 (la proue) : à distance nulle, le joueur démarre
## déjà posé sur le premier tronçon, sans l'avoir vu venir. Vingt-deux unités, soit neuf
## secondes à la vitesse de croisière, lui laissent le temps de voir arriver ce qu'il survole —
## et c'est la première image du niveau.
const LEAD_IN := 22.0

signal section_entered(index: int)
signal survey_finished()

## Vitesse de défilement, en unités/seconde. Posée par le niveau depuis `CortegeTuning` : elle
## commande la durée, donc les fenêtres de tir, donc tout l'équilibrage.
var scroll_speed: float = 2.4
var section_length: float = 100.0
var section_count: int = 5

## Le nœud qui porte les cinq tronçons. ⚠️ C'EST LUI QU'ON DÉPLACE, ET LUI SEUL. La forge a
## livré les tourelles, les baies et les nœuds d'épine comme ENFANTS de leur tronçon : déplacer
## chaque tronçon séparément les emmènerait, mais déplacer le décor entier revient au même en
## une seule écriture — et surtout, ça ne peut pas désynchroniser un marqueur de sa section.
var _decor: Node3D
var _sections: Array[Node3D] = []
var _sky: MeshInstance3D
var _is_stand_in: bool = false
var _travelled: float = 0.0
var _entered: int = -1
var _finished: bool = false

func _ready() -> void:
	reveal(false)
	_build()

## Allume ou éteint le survol. ⚠️ `set_process` AUSSI : un décor caché qui continue de calculer
## son défilement dépense pour rien, et se retrouve ailleurs qu'où on l'a laissé.
func reveal(on: bool) -> void:
	visible = on
	set_process(on)
	if not on:
		return
	_travelled = 0.0
	_entered = -1
	_finished = false
	_place_sections()

## Place le survol au début d'un tronçon. Pour la vérification uniquement — le jeu ne saute
## jamais : un survol se traverse.
func skip_to_section(index: int) -> void:
	_travelled = float(clampi(index, 0, section_count - 1)) * section_length
	_entered = -1
	_finished = false
	_place_sections()

## Les tronçons, dans l'ordre de la proue vers l'arrière. ⚠️ C'EST LE SEUL ACCÈS À LA COQUE
## DEPUIS L'EXTÉRIEUR, et il est délibérément étroit : les mécaniques ont besoin des marqueurs
## que porte chaque tronçon, elles n'ont besoin de rien d'autre. Ouvrir le décor entier
## laisserait le gameplay dépendre d'une hiérarchie que la forge peut légitimement changer.
func sections() -> Array[Node3D]:
	return _sections

func is_stand_in() -> bool:
	return _is_stand_in

## Ce qui a été parcouru, en part du survol entier — pour l'indicateur de progression.
func progress() -> float:
	var total := section_length * float(section_count)
	return clampf(_travelled / total, 0.0, 1.0) if total > 0.001 else 0.0

func current_section() -> int:
	return clampi(int(_travelled / maxf(section_length, 0.001)), 0, section_count - 1)

## Ce qui a été parcouru, en unités monde depuis le début du survol.
##
## ⚠️ IL EXISTE PARCE QU'UNE PIÈCE POSÉE SUR LA COQUE NE PEUT PAS LIRE SA PROPRE POSITION HORS
## DE L'ARBRE : `global_position` ne répond que dans une scène montée, et renvoie l'identité
## ailleurs — en silence. Une mécanique qui a besoin de savoir OÙ elle est pour décider (le
## verrou de mi-parcours s'arrête à une station précise) le déduit donc de ce nombre, avec
## `section_z_at()`. C'est ce qui la rend vérifiable sans jouer deux minutes de défilement.
func travelled() -> float:
	return _travelled

func _build() -> void:
	add_child(_make_sky())
	var decor: Node3D = null
	if ResourceLoader.exists(DECOR_PATH):
		var packed: PackedScene = load(DECOR_PATH) as PackedScene
		if packed != null:
			decor = packed.instantiate() as Node3D
	if decor != null:
		decor.name = "Hull"
		add_child(decor)
		_decor = decor
		_collect_sections(decor)
		# ⚠️ FACULTATIF ET SILENCIEUX QUAND IL MANQUE. Les cartes viennent de l'opérateur
		# (`ADR-0028`, demandes `TEX-0010` à `TEX-0014`) et n'existent pas encore : la coque
		# se joue nue, avec les seules couleurs de palette du `.glb`. Le journal dit lequel
		# des deux états on regarde — sans quoi on jugerait un rendu texturé qui ne l'est pas.
		var dressed := CortegeSkin.apply(decor)
		print("[Cortege] coque %s" % ("habillée — %d surfaces" % dressed if dressed > 0
			else "NUE — aucune carte dans %s" % CortegeSkin.MAPS_DIR.get_base_dir().get_file()))
	if _sections.is_empty():
		_is_stand_in = true
		_decor = Node3D.new()
		_decor.name = "Hull"
		add_child(_decor)
		_build_stand_in()
	_silence_shadows()
	_place_sections()

## Résout les tronçons par CONTRAT DE NOMS, comme `MoonFlyby` le fait pour ses rochers :
## `Section_01` … `Section_NN`, enfants directs du décor.
func _collect_sections(decor: Node3D) -> void:
	for child in decor.get_children():
		var node := child as Node3D
		if node != null and node.name.begins_with("Section_"):
			_sections.append(node)
	# ⚠️ `String(...)` ET PAS `a.name < b.name`. `Node.name` est un `StringName`, et l'opérateur
	# `<` sur un `StringName` NE COMPARE PAS DANS L'ORDRE ALPHABÉTIQUE : il compare des pointeurs
	# internes, pour la vitesse. Le tri rendait donc un ordre ARBITRAIRE — mesuré :
	# `[05, 04, 03, 01, 02]` — et, pire, dépendant de l'allocation, donc différent d'un
	# lancement à l'autre.
	#
	# ⚠️ ET RIEN NE LE MONTRAIT. Le défilement, lui, est juste : il déplace le décor entier et
	# ne consulte jamais cet ordre. Le numéro de tronçon affiché est juste aussi : il se déduit
	# de la distance parcourue. Seul le NUMÉRO PORTÉ PAR CHAQUE PIÈCE était faux — donc un nœud
	# du tronçon 1 éteignait les tourelles du 5, et le journal annonçait « nœud d'épine 04
	# abattu » pendant qu'on survolait le premier. C'est l'opérateur qui l'a vu en jouant.
	_sections.sort_custom(func(a: Node3D, b: Node3D) -> bool:
		return String(a.name) < String(b.name))

## La doublure : un tronçon = une dalle nervurée. Elle ne cherche pas à être belle, elle cherche
## à rendre le niveau JOUABLE et MESURABLE avant la livraison de la forge.
func _build_stand_in() -> void:
	for i in section_count:
		var section := Node3D.new()
		section.name = "Section_%02d" % (i + 1)
		var plate := MeshInstance3D.new()
		var mesh := BoxMesh.new()
		mesh.size = Vector3(HULL_WIDTH, 2.0, section_length)
		plate.mesh = mesh
		var mat := StandardMaterial3D.new()
		# Anthracite de l'Unisson (charte §3), plus clair d'un tronçon à l'autre pour que la
		# jonction se voie pendant la mise au point.
		#
		# ⚠️ BIEN PLUS SOMBRE QUE LA VALEUR DE CHARTE, et ce n'est pas une erreur : le
		# post-traitement rétro applique un `lift` de 1,25 qui remonte les tons moyens
		# (`ADR-0016`). Une première doublure à 0,10 est ressortie BEIGE à l'écran. Ce qu'on
		# règle ici est ce qui sort du shader, pas ce qui entre.
		var teinte := 0.035 + 0.006 * float(i)
		mat.albedo_color = Color(teinte, teinte, teinte * 1.15)
		mat.roughness = 0.72
		mat.metallic = 0.15
		plate.material_override = mat
		section.add_child(plate)
		# ⚠️ La doublure reproduit l'espacement du `.glb` livré : tronçon N à Z = -N × longueur,
		# et la hauteur portée par la géométrie. Sans quoi passer de l'une à l'autre déplacerait
		# le décor sans que rien ne le dise.
		section.position = Vector3(0.0, HULL_Y, -float(i) * section_length)
		_decor.add_child(section)
		_sections.append(section)

## Place la coque selon ce qui a défilé. Le décor avance vers +Z, c'est-à-dire vers le bas de
## l'écran : le joueur remonte le vaisseau de la proue vers l'arrière.
func _place_sections() -> void:
	if _decor != null:
		_decor.position.z = _travelled - LEAD_IN

func _process(delta: float) -> void:
	if _finished:
		return
	_travelled += scroll_speed * delta
	_place_sections()
	var section := current_section()
	if section != _entered:
		_entered = section
		section_entered.emit(section)
	if _travelled >= section_length * float(section_count) + LEAD_IN:
		_finished = true
		survey_finished.emit()

## Le ciel du survol : même shader que le fond spatial, mais sur son chemin `deep_sky`.
## ⚠️ CE N'EST PAS UN RÉGLAGE, C'EST UN CHEMIN. Baisser l'intensité de la nébuleuse à zéro
## n'économiserait rien — le shader calcule ses cinq champs de bruit quoi qu'il arrive.
func _make_sky() -> MeshInstance3D:
	_sky = MeshInstance3D.new()
	_sky.name = "CortegeSky"
	var mesh := PlaneMesh.new()
	mesh.size = SKY_SIZE
	_sky.mesh = mesh
	_sky.position = Vector3(0.0, SKY_Y, -4.0)
	_sky.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# Le ciel est un plan immense vu de très près : sans marge, il disparaît dès que son centre
	# sort du frustum. Même valeur que les deux autres ciels du jeu.
	_sky.extra_cull_margin = 100.0
	var backdrop: Resource = load("res://shaders/space_background.gdshader")
	if backdrop != null:
		var mat := ShaderMaterial.new()
		mat.shader = backdrop
		mat.set_shader_parameter(&"deep_sky", true)
		mat.set_shader_parameter(&"scroll_speed", -0.5)
		# ⚠️ Le chemin `deep_sky` ne rend que des étoiles sur une couleur de fond — c'est ce qui
		# le rend presque gratuit. Cette couleur est donc le SEUL levier d'ambiance disponible
		# ici, et les maquettes demandent un fond violacé, pas un noir neutre. Elle ne coûte
		# rien : c'est la constante sur laquelle les étoiles sont additionnées.
		mat.set_shader_parameter(&"deep_color", Color(0.035, 0.012, 0.055))
		_sky.material_override = mat
		_sky.material_override.render_priority = -1
	return _sky

## ⚠️ La carte d'ombres directionnelle s'arrête à 40 unités : une coque de 500 se retrouverait à
## moitié dedans, à moitié dehors, et la couture se verrait défiler. Aucune ombre portée.
func _silence_shadows() -> void:
	for node in _all_meshes(self):
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

func _all_meshes(root: Node) -> Array[MeshInstance3D]:
	var found: Array[MeshInstance3D] = []
	for child in root.get_children():
		var mesh := child as MeshInstance3D
		if mesh != null:
			found.append(mesh)
		found.append_array(_all_meshes(child))
	return found

# --- Fonctions pures, testables sans arbre de scène ---------------------------

## Où se trouve un tronçon après une distance parcourue. ⚠️ STATIQUE ET PURE, comme
## `MoonFlyby.drifted()` : c'est ce qui permet de tester le défilement sans monter la scène.
##
## Le tronçon N est posé à -N × longueur dans le `.glb` ; le décor entier avance vers +Z.
static func section_z_at(index: int, length: float, travelled: float) -> float:
	return -float(index) * length + travelled - LEAD_IN

## Le tronçon sous le joueur après cette distance.
static func section_at(travelled: float, length: float, count: int) -> int:
	if length <= 0.001 or count <= 0:
		return 0
	return clampi(int(travelled / length), 0, count - 1)

## Combien de temps une cible reste tirable, à cette vitesse. Le survol ne revient jamais en
## arrière : c'est cette fenêtre, et elle seule, qui borne ce qu'on peut abattre.
static func window_for(visible_span: float, speed: float) -> float:
	return visible_span / speed if speed > 0.001 else 0.0
