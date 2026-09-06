class_name CortegeAnchor
extends Node3D
## Un verrou d'ancrage : la SEULE chose sur quoi on tire dans la phase finale du niveau 2.
##
## ⚠️ ON NE TIRE PAS SUR LE MOTEUR. C'est la règle de la phase, et elle est contre-intuitive
## pour un joueur de shmup : la masse énorme qui remplit l'écran est décorative, et ce qui la
## retient — trois pièces de deux mètres — est tout ce qui compte. La lisibilité de cette règle
## est le critère d'acceptation n°5 de la spec, pas un détail de mise en scène.
##
## ⚠️ ET DEUX MÈTRES, C'EST GRAND. Un ancrage fait 1,88 m à l'échelle retenue, soit ~86 px à
## l'écran (45,8 px/m) : trois quarts de la longueur du chasseur. La spec l'exige — « pas de
## petit weakpoint de 10 pixels » — et c'est ce qui autorise à ne PAS mettre de marqueur d'aide
## par-dessus.
##
## ⚠️ IL PEUT ÊTRE VIVANT SANS ÊTRE VULNÉRABLE, et confondre les deux casse la séquence. Les
## ancrages du moteur central restent verrouillés tant que les deux latéraux tiennent (spec §14) :
## ils existent, ils se voient, ils encaissent zéro. Même distinction que le noyau de la Citadelle.

## Ce qu'un ancraga rend quand il tombe — le seul point d'entrée des dégâts.
signal destroyed(anchor: CortegeAnchor)

## La teinte du magenta d'énergie de la faction, celle du kit de coque.
const TINT := Color("d93d9c")
## Ce qu'il reste de lueur à un ancrage rompu : une carcasse sombre, jamais rien.
## Même règle que l'œil d'une tourelle abattue et que la veine d'un tronçon éteint.
const DEAD_GLOW := 0.02

var score: int = 0
## Sa place dans le groupe, pour le journal — l'anonymat coûte cher en investigation.
var serial: int = 0

var _health: float = 0.0
var _alive: bool = true
var _vulnerable: bool = false
var _target: BulletTarget = null
var _bullets: BulletManager = null
var _vfx: VFXManager = null
var _world: Vector3 = Vector3.ZERO
var _glow: StandardMaterial3D = null
var _registered: bool = false

static func make(health: float, radius: float, p_score: int) -> CortegeAnchor:
	var anchor := CortegeAnchor.new()
	anchor.score = p_score
	anchor._health = health
	# La cible naît avec la pièce — même contrat que la tourelle, le nœud et la Citadelle : il
	# n'y a qu'une porte pour les dégâts, et les tests passent par elle.
	anchor._target = BulletTarget.make(BulletManager.Team.ENEMY, radius, anchor._take_damage)
	anchor._target.enabled = false
	return anchor

func setup(bullets: BulletManager, vfx: VFXManager) -> void:
	_bullets = bullets
	_vfx = vfx

## La boîte grise du LOT 1. ⚠️ ELLE SERA REMPLACÉE PAR `asset3_ancrage_destructible`, et c'est
## voulu : la phase doit être jouable, testée et FINIE avant qu'un seul asset final n'entre.
## C'est la leçon de la cellule témoin — un lot qui commence par les assets se retrouve avec de
## beaux objets et pas de jeu.
func build_greybox(size: Vector3) -> void:
	var mesh := MeshInstance3D.new()
	mesh.name = "Greybox"
	var box := BoxMesh.new()
	box.size = size
	mesh.mesh = box
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_glow = StandardMaterial3D.new()
	_glow.albedo_color = Color(0.10, 0.10, 0.13)
	_glow.metallic = 0.6
	_glow.roughness = 0.5
	_glow.emission_enabled = true
	_glow.emission = TINT
	_glow.emission_energy_multiplier = 0.9
	mesh.material_override = _glow
	add_child(mesh)

func is_alive() -> bool:
	return _alive

func is_vulnerable() -> bool:
	return _vulnerable

## Ouvre ou ferme la prise aux dégâts. ⚠️ ELLE PILOTE AUSSI L'INSCRIPTION AUPRÈS DU GESTIONNAIRE
## DE BALLES : un verrou fermé qui resterait inscrit encaisserait quand même, et le joueur
## verrait tomber une pièce qu'on lui dit protégée.
func set_vulnerable(on: bool) -> void:
	_vulnerable = on and _alive
	if _target == null:
		return
	_target.enabled = _vulnerable
	if _bullets == null:
		return
	if _vulnerable and not _registered:
		_bullets.register_target(_target)
		_registered = true
	elif not _vulnerable and _registered:
		_bullets.unregister_target(_target)
		_registered = false

## La cible que le gestionnaire de balles connaît. ⚠️ EXPOSÉE PARCE QUE C'EST LE VRAI CHEMIN DES
## DÉGÂTS : un test qui appellerait une méthode écrite pour lui ne vérifierait pas le chemin que
## le jeu emprunte.
func target() -> BulletTarget:
	return _target

## Un pas. ⚠️ SA POSITION LUI EST DONNÉE, ELLE NE LA LIT PAS DANS L'ARBRE — même contrat que le
## nœud d'épine, et pour la même raison : c'est ce qui la rend pilotable sans scène.
func tick(world: Vector3, here: Vector2) -> void:
	_world = world
	if _target != null:
		_target.position = here

func _take_damage(damage: float) -> void:
	# ⚠️ LE VERROU FERMÉ ENCAISSE ZÉRO, ET IL LE FAIT ICI. Le désinscrire suffirait presque —
	# mais une balle déjà résolue dans la trame courante trouverait encore la cible, et le
	# moteur central perdrait un ancrage avant son tour, une fois de temps en temps.
	if not _alive or not _vulnerable:
		return
	_health -= damage
	if _health > 0.0:
		return
	_alive = false
	set_vulnerable(false)
	if _glow != null:
		_glow.emission_energy_multiplier = DEAD_GLOW
		_glow.albedo_color = Color(0.05, 0.05, 0.06)
	if _vfx != null:
		_vfx.spawn_explosion(_world, VfxExplosion.Category.MEDIUM, TINT)
	destroyed.emit(self)
