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
## ⚠️ IL A QUATRE ÉTATS, ET TROIS SONT DANS LA PLANCHE. `asset3_ancrage_destructible` dessine
## *Intact*, *Endommagé* (plaques ouvertes, étincelles) et *Ouvert/rompu* (mâchoire déployée,
## connexion rompue). Le quatrième — **verrouillé** — n'est pas dans la planche parce qu'il
## n'appartient pas à la pièce : il appartient à la séquence. Les verrous du moteur central
## existent et se voient bien avant d'être attaquables (spec §14), et sans un état visuel
## propre, le joueur les prendrait pour des cibles qui n'encaissent rien — c'est-à-dire pour
## un bug.

## Ce qu'un ancrage rend quand il tombe — le seul point d'entrée des dégâts.
signal destroyed(anchor: CortegeAnchor)

## Ce que le joueur doit pouvoir lire d'un coup d'œil.
enum Look { LOCKED, INTACT, DAMAGED, BROKEN }

## La teinte du magenta d'énergie de la faction, celle du kit de coque.
const TINT := Color("d93d9c")
## ⚠️ LE VERROUILLÉ N'EST PAS UN MAGENTA FAIBLE, C'EST UNE AUTRE COULEUR. Un magenta assombri se
## lirait comme « un ancrage abîmé », donc comme une cible déjà travaillée ; le bleu froid dit
## « pas encore ». C'est la même règle que l'ambre de signalisation (`ADR-0043`) : un état se
## distingue par sa TEINTE avant de se distinguer par son intensité.
const LOCKED_TINT := Color(0.30, 0.52, 0.72)

const LOCKED_GLOW := 0.12
const INTACT_GLOW := 0.90
## L'endommagé brille PLUS FORT que l'intact : ses plaques sont ouvertes et son cœur est à nu.
const DAMAGED_GLOW := 1.60
## Ce qu'il reste de lueur à un ancrage rompu : une carcasse sombre, jamais rien. Même règle
## que l'œil d'une tourelle abattue et que la veine d'un tronçon éteint.
const BROKEN_GLOW := 0.02

## Le battement de l'endommagé — c'est lui qui dit « celui-ci va céder ».
const DAMAGED_PULSE_HZ := 5.5
const DAMAGED_PULSE_DEPTH := 0.45
## Le flash blanc d'un coup au but. ⚠️ SANS LUI, LE JOUEUR NE SAIT PAS QU'IL TOUCHE : l'ancrage
## est la seule cible de la phase, et deux secondes de tir sans retour se lisent comme « cette
## pièce est invulnérable ».
const HIT_FLASH_TIME := 0.10
const HIT_FLASH_GAIN := 2.8

var score: int = 0
## Sa place dans le groupe, pour le journal — l'anonymat coûte cher en investigation.
var serial: int = 0
## En dessous de cette part de vie, il passe en `DAMAGED`.
var damaged_at: float = 0.45
var spark_interval: float = 0.55

var _health: float = 0.0
var _health_max: float = 0.0
var _alive: bool = true
var _vulnerable: bool = false
var _target: BulletTarget = null
var _bullets: BulletManager = null
var _vfx: VFXManager = null
var _world: Vector3 = Vector3.ZERO
var _glow: StandardMaterial3D = null
var _registered: bool = false
var _pulse: float = 0.0
var _flash: float = 0.0
var _spark_clock: float = 0.0
var _look: Look = Look.LOCKED

static func make(health: float, radius: float, p_score: int) -> CortegeAnchor:
	var anchor := CortegeAnchor.new()
	anchor.score = p_score
	anchor._health = health
	anchor._health_max = health
	# La cible naît avec la pièce — même contrat que la tourelle, le nœud et la Citadelle : il
	# n'y a qu'une porte pour les dégâts, et les tests passent par elle.
	anchor._target = BulletTarget.make(BulletManager.Team.ENEMY, radius, anchor._take_damage)
	anchor._target.enabled = false
	return anchor

func setup(bullets: BulletManager, vfx: VFXManager) -> void:
	_bullets = bullets
	_vfx = vfx

# --- La règle, pure et testable sans arbre -------------------------------------

## Ce que le joueur doit lire, déduit de l'état de la pièce et de rien d'autre.
##
## ⚠️ L'ORDRE DES TESTS COMPTE. Un ancrage mort est `BROKEN` même s'il est encore « ouvert » aux
## dégâts pendant la trame de sa mort ; un ancrage verrouillé est `LOCKED` même à pleine vie,
## parce que ce que le joueur doit savoir de lui n'est pas sa santé, c'est qu'il ne sert à rien
## de le viser.
static func look_for(alive: bool, vulnerable: bool, ratio: float, seuil: float) -> Look:
	if not alive:
		return Look.BROKEN
	if not vulnerable:
		return Look.LOCKED
	return Look.DAMAGED if ratio <= seuil else Look.INTACT

# --- La pièce ------------------------------------------------------------------

## La boîte grise du LOT 1. ⚠️ ELLE SERA REMPLACÉE PAR `asset3_ancrage_destructible`, livré le
## 2026-09-06 — 54 640 triangles pour 2,4 m, donc pas avant sa réduction (LOT 5). La phase est
## jouable et finie sans lui, et c'est le point.
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
	mesh.material_override = _glow
	add_child(mesh)
	_apply_look()

func is_alive() -> bool:
	return _alive

func is_vulnerable() -> bool:
	return _vulnerable

func look() -> Look:
	return _look

func health_ratio() -> float:
	return clampf(_health / maxf(_health_max, 0.001), 0.0, 1.0)

## Ouvre ou ferme la prise aux dégâts. ⚠️ ELLE PILOTE AUSSI L'INSCRIPTION AUPRÈS DU GESTIONNAIRE
## DE BALLES : un verrou fermé qui resterait inscrit encaisserait quand même, et le joueur
## verrait tomber une pièce qu'on lui dit protégée.
func set_vulnerable(on: bool) -> void:
	_vulnerable = on and _alive
	if _target != null:
		_target.enabled = _vulnerable
	if _bullets != null:
		if _vulnerable and not _registered:
			_bullets.register_target(_target)
			_registered = true
		elif not _vulnerable and _registered:
			_bullets.unregister_target(_target)
			_registered = false
	_refresh_look()

## La cible que le gestionnaire de balles connaît. ⚠️ EXPOSÉE PARCE QUE C'EST LE VRAI CHEMIN DES
## DÉGÂTS : un test qui appellerait une méthode écrite pour lui ne vérifierait pas le chemin que
## le jeu emprunte.
func target() -> BulletTarget:
	return _target

## Un pas. ⚠️ SA POSITION LUI EST DONNÉE, ELLE NE LA LIT PAS DANS L'ARBRE — même contrat que le
## nœud d'épine, et pour la même raison : c'est ce qui la rend pilotable sans scène.
func tick(delta: float, world: Vector3, here: Vector2) -> void:
	_world = world
	if _target != null:
		_target.position = here
	if _flash > 0.0:
		_flash = maxf(_flash - delta, 0.0)
	if _look == Look.DAMAGED:
		_pulse = fmod(_pulse + delta * DAMAGED_PULSE_HZ, TAU)
		# ⚠️ LES ÉTINCELLES SONT LE SEUL SIGNAL QUI PORTE À DISTANCE. Le battement se voit quand
		# on regarde la pièce ; l'étincelle se voit du coin de l'œil, et c'est ce qui ramène le
		# joueur sur le verrou qu'il a laissé à moitié.
		_spark_clock -= delta
		if _spark_clock <= 0.0 and _vfx != null:
			_spark_clock = spark_interval
			_vfx.spawn_explosion(_world, VfxExplosion.Category.IMPACT, TINT)
	_apply_look()

func _take_damage(damage: float) -> void:
	# ⚠️ LE VERROU FERMÉ ENCAISSE ZÉRO, ET IL LE FAIT ICI. Le désinscrire suffirait presque —
	# mais une balle déjà résolue dans la trame courante trouverait encore la cible, et le
	# moteur central perdrait un ancrage avant son tour, une fois de temps en temps.
	if not _alive or not _vulnerable:
		return
	_health -= damage
	_flash = HIT_FLASH_TIME
	if _health > 0.0:
		_refresh_look()
		return
	_alive = false
	set_vulnerable(false)
	if _vfx != null:
		_vfx.spawn_explosion(_world, VfxExplosion.Category.MEDIUM, TINT)
	destroyed.emit(self)

func _refresh_look() -> void:
	var avant := _look
	_look = look_for(_alive, _vulnerable, health_ratio(), damaged_at)
	if _look != avant:
		# Le battement repart de zéro à chaque changement : sans ça, un verrou qui passe en
		# `DAMAGED` hérite d'une phase quelconque et le groupe clignote en désordre.
		_pulse = 0.0
		_spark_clock = 0.0
	_apply_look()

## ⚠️ LA CARCASSE RESTE, ET C'EST LA PREUVE. Un verrou rompu qui disparaîtrait laisserait le
## joueur compter ce qui manque au lieu de voir ce qu'il a fait — même règle que le berceau vide
## et que le cœur de nœud d'épine.
func _apply_look() -> void:
	if _glow == null:
		return
	var teinte := LOCKED_TINT if _look == Look.LOCKED else TINT
	var energie := INTACT_GLOW
	match _look:
		Look.LOCKED: energie = LOCKED_GLOW
		Look.BROKEN: energie = BROKEN_GLOW
		Look.DAMAGED: energie = DAMAGED_GLOW * (1.0 + DAMAGED_PULSE_DEPTH * sin(_pulse))
	if _flash > 0.0:
		energie += HIT_FLASH_GAIN * (_flash / HIT_FLASH_TIME)
		teinte = teinte.lerp(Color.WHITE, 0.6)
	_glow.emission = teinte
	_glow.emission_energy_multiplier = energie
	_glow.albedo_color = Color(0.05, 0.05, 0.06) if _look == Look.BROKEN \
		else Color(0.10, 0.10, 0.13)
