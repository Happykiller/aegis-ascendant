class_name CortegeAnchor
extends Node3D
## Un verrou d'ancrage : la SEULE chose sur quoi on tire dans la phase finale du niveau 2.
##
## ⚠️ ON NE TIRE PAS SUR LE MOTEUR. C'est la règle de la phase, et elle est contre-intuitive
## pour un joueur de shmup : la masse énorme qui remplit l'écran est décorative, et ce qui la
## retient — trois pièces de deux mètres — est tout ce qui compte. La lisibilité de cette règle
## est le critère d'acceptation n°5 de la spec, pas un détail de mise en scène.
##
## ⚠️ ET DEUX MÈTRES, C'EST GRAND — MAIS PAS AUTANT QUE JE L'AI ÉCRIT. Un ancrage fait 2,09 m à
## l'échelle retenue. La densité de la POUPE n'est pas celle du corridor : son pont est à −11,85,
## le cadre y couvre 58,77 m et la caméra rend **32,7 px/m**, pas 45,8 (mesuré par la forge au
## `BRIEF-0105`). L'ancrage fait donc **68 pixels**, pas 96. La spec est tenue — « pas de petit
## weakpoint de 10 pixels » — mais avec un tiers de marge en moins que je ne le croyais.
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

## ⚠️ CES ÉNERGIES ONT ÉTÉ MULTIPLIÉES PAR QUATRE QUAND LA VRAIE PIÈCE EST ENTRÉE, ET C'EST UNE
## CORRECTION DE LISIBILITÉ, PAS DE GOÛT. La boîte grise était émissive SUR TOUTE SA SURFACE :
## 68 pixels de magenta à 32,7 px/m. La pièce réduite ne l'est que sur ses fentes — une dizaine
## de pixels. À énergie égale, le verrou cessait de se distinguer de la structure du berceau, et
## le joueur ne pouvait plus dire ce qu'il devait viser. Vu en capture, à 1:1.
const LOCKED_GLOW := 1.10
const INTACT_GLOW := 4.00
## L'endommagé brille PLUS FORT que l'intact : ses plaques sont ouvertes et son cœur est à nu.
const DAMAGED_GLOW := 7.00
## Ce qu'il reste de lueur à un ancrage rompu : une carcasse sombre, jamais rien. Même règle
## que l'œil d'une tourelle abattue et que la veine d'un tronçon éteint.
const BROKEN_GLOW := 0.05

## Le battement de l'endommagé — c'est lui qui dit « celui-ci va céder ».
const DAMAGED_PULSE_HZ := 5.5
const DAMAGED_PULSE_DEPTH := 0.45
## Le flash blanc d'un coup au but. ⚠️ SANS LUI, LE JOUEUR NE SAIT PAS QU'IL TOUCHE : l'ancrage
## est la seule cible de la phase, et deux secondes de tir sans retour se lisent comme « cette
## pièce est invulnérable ».
const HIT_FLASH_TIME := 0.10
const HIT_FLASH_GAIN := 2.8

## Ce que vaut le bandeau d'état selon l'état. Additif : au-delà de 1 il sature en blanc et
## perd sa teinte, donc l'information qu'il porte.
const HALO_LOCKED := 0.22
const HALO_INTACT := 0.62
const HALO_DAMAGED := 0.95

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
## TOUS les émissifs de la pièce réduite — elle en a plusieurs surfaces, pas une.
var _glows: Array[StandardMaterial3D] = []
var _halo: StandardMaterial3D = null
var _anim: AnimationPlayer = null
## Le clip joué, pour ne pas le relancer à chaque image.
var _clip: String = ""
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

## Le binaire réduit (`BRIEF-0105`) : 900 triangles pour 2,40 m, contre 54 640 livrés.
const KIT := "res://assets/imported/models/backgrounds/stern_anchor.glb"

## Monte la pièce réduite, ou sa boîte grise si elle manque.
##
## ⚠️ LA DOUBLURE RESTE : les bancs montent l'ancrage sans arbre ni import, et c'est ce qui
## rend ses quatre états vérifiables sans jouer quatre minutes de survol.
func build(size: Vector3) -> void:
	var packed: PackedScene = load(KIT) as PackedScene
	if packed == null:
		build_greybox(size)
		return
	var piece := packed.instantiate() as Node3D
	if piece == null:
		build_greybox(size)
		return
	piece.name = "Anchor"
	add_child(piece)
	_claim_glow(piece)
	_anim = _player_of(piece)
	_build_band(size)
	_apply_look()

## Le bandeau d'état — ⚠️ IL EXISTE PARCE QUE LA VRAIE PIÈCE NE SE DÉSIGNE PAS ELLE-MÊME.
##
## La boîte grise était émissive SUR TOUTE SA SURFACE : 68 pixels de magenta, impossible à
## confondre. La pièce réduite ne l'est que sur ses fentes — 36 triangles sur 900, une dizaine
## de pixels perdus dans la structure d'un berceau qui en compte des centaines. Multiplier
## l'énergie a rendu l'ÉTAT lisible — on distingue le bleu verrouillé du magenta actif — mais
## pas la CIBLE.
##
## ⚠️ ET C'EST UN CRITÈRE D'ACCEPTATION, PAS UNE PRÉFÉRENCE. La spec §7 demande un ancrage
## « gros, identifiable, légèrement lumineux » et le §21 exige qu'une capture communique
## « les attaches sont destructibles ». Un joueur qui ne sait pas quoi viser tire sur le moteur,
## qui n'encaisse rien, et toute la phase se lit comme cassée.
##
## ⚠️ ET CE N'EST PAS UN HALO. La première version enveloppait la pièce d'une boîte additive sans
## test de profondeur : elle passait DEVANT les nacelles et se lisait comme un cube de couleur
## posé sur le vaisseau — le grief exact qu'`ADR-0043` a payé sur l'ambre de signalisation.
## Un bandeau plaqué sur la face avant, occulté normalement, appartient à la pièce ; un volume
## flottant appartient à l'interface.
func _build_band(size: Vector3) -> void:
	var mesh := MeshInstance3D.new()
	mesh.name = "Band"
	var box := BoxMesh.new()
	# ⚠️ IL REMPLIT LA PIÈCE AU LIEU DE LA SURLIGNER. Trois versions ont échoué avant celle-ci :
	# une bande sur la face avant (invisible dès que la rangée arrière fait demi-tour), une bande
	# sur le dessus (trop mince à 32,7 px/m), et un halo débordant sans test de profondeur — qui
	# passait DEVANT les nacelles et se lisait comme un cube posé sur le vaisseau. Un volume
	# additif à l'intérieur de la silhouette, occulté normalement, donne à l'ancrage la lueur
	# que la spec §7 lui demande sans lui ajouter de contour.
	box.size = Vector3(size.x * 0.88, size.y * 0.62, size.z * 0.88)
	mesh.mesh = box
	mesh.position = Vector3(0.0, size.y * 0.30, 0.0)
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_halo = StandardMaterial3D.new()
	_halo.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_halo.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	# ⚠️ AVEC test de profondeur : le bandeau se fait masquer par ce qui passe devant, comme
	# toute pièce du vaisseau. C'est ça qui le fait appartenir à l'ancrage.
	_halo.render_priority = 3
	_halo.albedo_color = TINT
	mesh.material_override = _halo
	add_child(mesh)

## ⚠️ CHAQUE VERROU SA COPIE. Les dix ancrages sont dix instances du MÊME `.glb` : ils partagent
## leurs matériaux, et en éteindre un les éteindrait tous. C'est le piège déjà payé sur les deux
## relais de la Citadelle et sur les cinq bulbes d'épine.
func _claim_glow(root: Node) -> void:
	for node in _descendants(root):
		var mesh := node as MeshInstance3D
		if mesh == null:
			continue
		for i in mesh.get_surface_override_material_count():
			var base := mesh.get_active_material(i) as StandardMaterial3D
			if base == null or not base.emission_enabled:
				continue
			var mine: StandardMaterial3D = base.duplicate()
			mesh.set_surface_override_material(i, mine)
			_glows.append(mine)
			if _glow == null:
				_glow = mine

static func _descendants(node: Node, out: Array[Node] = []) -> Array[Node]:
	for child in node.get_children():
		out.append(child)
		_descendants(child, out)
	return out

static func _player_of(root: Node) -> AnimationPlayer:
	for node in _descendants(root):
		var player := node as AnimationPlayer
		if player != null:
			return player
	return null

## La boîte grise, gardée comme doublure.
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
	_glows.append(_glow)
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
	_play_clip()
	if _glows.is_empty():
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
	# ⚠️ TOUS LES ÉMISSIFS, PAS LE PREMIER. La pièce réduite en porte plusieurs surfaces ; n'en
	# piloter qu'une laisserait des morceaux de verrou allumés sur une carcasse.
	for mat in _glows:
		mat.emission = teinte
		mat.emission_energy_multiplier = energie
		mat.albedo_color = Color(0.05, 0.05, 0.06) if _look == Look.BROKEN \
			else Color(0.10, 0.10, 0.13)
	if _halo == null:
		return
	var force := HALO_INTACT
	match _look:
		Look.LOCKED: force = HALO_LOCKED
		Look.BROKEN: force = 0.0
		Look.DAMAGED: force = HALO_DAMAGED * (1.0 + DAMAGED_PULSE_DEPTH * sin(_pulse))
	if _flash > 0.0:
		force += 0.5 * (_flash / HIT_FLASH_TIME)
	_halo.albedo_color = Color(teinte.r, teinte.g, teinte.b, 1.0) * force

## ⚠️ LE CLIP SUIT L'ÉTAT, ET IL NE SE RELANCE PAS À CHAQUE IMAGE. `play()` appelé soixante fois
## par seconde remet l'animation à zéro : la mâchoire tremblerait sur place au lieu de s'ouvrir.
func _play_clip() -> void:
	if _anim == null:
		return
	var voulu := "Intact"
	match _look:
		Look.LOCKED: voulu = "Fermeture"
		Look.DAMAGED: voulu = "Endommage"
		Look.BROKEN: voulu = "Rompu"
	if voulu == _clip or not _anim.has_animation(voulu):
		return
	_clip = voulu
	_anim.play(voulu)
