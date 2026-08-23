class_name EnemyPose
extends RefCounted
## Ouvre une coque articulée — segments de mine, pétales de corolle.
##
## Les coques du jeu étaient jusqu'ici des blocs rigides : seul le boss avait des
## pièces mobiles, et par un code qui lui est propre (`HarvesterLimb`). Une mine qui
## s'ouvre pendant son télégraphe a besoin de la même chose, mais sur une unité
## POOLÉE, instanciée en champ — d'où un composant sans état de scène, qui se
## rebranche à chaque réactivation.
##
## ⚠️ UN SEUL ÉCRIVAIN PAR ROTATION (`.claude/resources/pratique-ecrivain-unique.md`).
## Les pièces ne se posent jamais elles-mêmes : `pose()` est le seul endroit du
## projet qui écrit leur `rotation`. Deux écrivains sur une même rotation, et c'est
## le dernier appelé qui gagne, silencieusement, une image sur deux.
##
## ⚠️ `find_child(nom, true, false)` RÉCURSIF. `get_node_or_null` rendait `null` sur
## cinq pièces sur neuf du mini-boss — un boss aux bras inertes, invisible aux tests
## headless, parce que les articulations sont des enfants indirects du maillage.

## Sécurité : au-delà, une pièce traverse sa voisine. Le débattement réel de chaque
## coque est mesuré par la forge et déclaré dans la Resource ; ceci n'est que le
## garde-fou qui empêche une donnée absurde de désassembler la coque à l'écran.
const MAX_OPEN_DEG := 85.0

## Plafond du coulissement radial, en fraction du rayon de la pièce. Même rôle que
## `MAX_OPEN_DEG` : empêcher une donnée absurde de désassembler la coque à l'écran.
const MAX_SPREAD := 0.5

var _parts: Array[Node3D] = []
## Axe de rotation de chaque pièce, en repère de la coque. Calculé UNE FOIS au
## branchement : c'est ce qui dispense d'écrire un axe par pièce dans la donnée.
var _axes: PackedVector3Array = PackedVector3Array()
## Position de repos et direction radiale de chaque pièce, pour le coulissement.
var _rest: PackedVector3Array = PackedVector3Array()
var _radial: PackedVector3Array = PackedVector3Array()
var _open_deg: float = 0.0
var _spread: float = 0.0


## Branche toutes les pièces nommées `<prefix>_01`, `<prefix>_02`… présentes dans la
## coque. Rend `null` si elle n'en a aucune — une coque rigide est un cas normal,
## pas une erreur : les neuf familles écrites avant celle-ci n'ont rien qui bouge.
static func bind(hull: Node3D, prefix: String, open_deg: float,
		spread: float = 0.0) -> EnemyPose:
	if hull == null or prefix.is_empty():
		return null
	var pose := EnemyPose.new()
	pose._open_deg = clampf(open_deg, 0.0, MAX_OPEN_DEG)
	pose._spread = clampf(spread, 0.0, MAX_SPREAD)
	var index := 1
	while true:
		var part := hull.find_child("%s_%02d" % [prefix, index], true, false) as Node3D
		if part == null:
			break
		pose._parts.append(part)
		pose._axes.append(_hinge_axis(part.position))
		pose._rest.append(part.position)
		pose._radial.append(_radial_axis(part.position))
		index += 1
	return pose if not pose._parts.is_empty() else null


## Direction « vers l'extérieur » d'une pièce : son propre rayon, dans le plan de
## la coque. Même parade que `_hinge_axis` pour une pièce sur l'axe.
static func _radial_axis(local_position: Vector3) -> Vector3:
	var radial := Vector2(local_position.x, local_position.z)
	if radial.length_squared() < 0.000001:
		return Vector3.ZERO
	radial = radial.normalized()
	return Vector3(radial.x, 0.0, radial.y)


## L'axe d'ouverture d'une pièce se DÉDUIT de sa position, il ne se déclare pas.
##
## Une pièce posée sur le pourtour d'un objet radial bascule vers l'extérieur : sa
## charnière est donc horizontale et TANGENTE au cercle, c'est-à-dire perpendiculaire
## à son propre rayon. Un axe par pièce dans la Resource serait six nombres à tenir
## à jour à chaque reforge de coque, et six occasions de se tromper de signe.
##
## ⚠️ Rend l'axe X pour une pièce pile sur l'axe : le rayon y est indéfini, et
## normaliser un vecteur nul rendrait NaN — qui se propagerait dans une rotation et
## ferait disparaître la pièce sans une seule erreur au journal.
static func _hinge_axis(local_position: Vector3) -> Vector3:
	var radial := Vector2(local_position.x, local_position.z)
	if radial.length_squared() < 0.000001:
		return Vector3.RIGHT
	radial = radial.normalized()
	return Vector3(-radial.y, 0.0, radial.x)


## Pose la coque. `ratio` va de 0 (fermée) à 1 (grande ouverte).
## Zéro allocation : on écrit des bases et des vecteurs déjà dimensionnés (spec §31).
##
## ⚠️ DEUX GESTES, PAS UN. Le pivot ouvre la coque ; le COULISSEMENT radial fait
## grossir son enveloppe. Le second existe parce que le premier, seul, ne se voit
## pas : 45° mesurés et testés restent invisibles sur un objet de 46 pixels vu de
## dessus, sous le bloom. Ce qui se lit à cette taille est l'enveloppe globale, pas
## l'angle d'une pièce — le Pale Leviathan écarte ET élargit sa coquille de 18 %
## pour la même raison.
##
## Le coulissement se fait le long du PROPRE rayon de chaque pièce : il éloigne les
## voisines l'une de l'autre au lieu de les rapprocher, donc il ne peut pas créer
## d'interpénétration entre plaques. Sa limite est ailleurs — la couronne de
## modules à l'équateur — et c'est une mesure, pas une estimation.
func pose(ratio: float) -> void:
	var open := clampf(ratio, 0.0, 1.0)
	var angle := deg_to_rad(_open_deg) * open
	for i in _parts.size():
		_parts[i].transform.basis = Basis(_axes[i], angle)
		if _spread > 0.0:
			_parts[i].position = _rest[i] + _radial[i] * _rest[i].length() * _spread * open


## Referme tout. Appelée quand l'instance retourne au pool : une mine recyclée qui
## revient déjà ouverte annonce une charge qui n'aura pas lieu.
func reset() -> void:
	pose(0.0)
	# Le coulissement laisse une position, pas seulement une rotation : sans cette
	# remise explicite, une instance recyclee reviendrait avec ses plaques ecartees.
	for i in _parts.size():
		_parts[i].position = _rest[i]
