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
const INTACT_GLOW := 6.00
## L'endommagé brille PLUS FORT que l'intact : ses plaques sont ouvertes et son cœur est à nu.
const DAMAGED_GLOW := 10.00
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
## --- LES ARCS, ET POURQUOI ILS SONT LA MEME RÉPONSE QU'AU NŒUD D'ÉPINE ------
##
## ⚠️ « ON NE SAIT PAS DE QUOI L'IA PARLE » (opérateur, après avoir joué la phase). Lyra dit
## « ne tirez pas sur les moteurs : coupez leurs ancrages », et dix pièces de deux mètres se
## taisent au milieu d'une carène qui en compte des centaines. La même chose s'était produite
## sur le nœud d'épine — « une boule violette posée sur un socle ne dit pas *tire ici* » — et la
## réponse avait été des arcs. Elle vaut ici mot pour mot, et l'opérateur l'a nommée lui-même.
##
## ⚠️ ET ILS SONT REDESSINÉS, PAS ANIMÉS. Un arc électrique n'a pas de trajectoire : il
## RECOMMENCE. Une interpolation lisse se lirait comme un tentacule ; ce qu'il faut, c'est que
## la figure change d'un coup, quelques fois par seconde.
##
## ⚠️ ET UN VERROU FERMÉ NE CRÉPITE PAS. C'est ce qui fait des arcs une DÉSIGNATION et pas une
## décoration : ils disent « celui-ci, maintenant ». Les faire crépiter tous rendrait le bleu du
## verrouillé inutile, et le joueur retournerait tirer au hasard.
const ARC_COUNT := 4
const ARC_SEGMENTS := 3
const ARC_REACH := 0.95
const ARC_JITTER := 0.22
const ARC_REDRAW_HZ := 12.0

## La DÉSIGNATION : le moment où le niveau montre au joueur ce dont il parle.
##
## ⚠️ ELLE DURE CE QUE DURE LA RÉPLIQUE, ET PAS UNE SECONDE DE PLUS. Un marqueur permanent cesse
## d'être une explication pour devenir une interface — et le jeu n'en a aucune sur ses cibles.
## Pendant la fenêtre, les arcs portent plus loin et la pièce brûle : après, elle redevient un
## verrou qui crépite comme les autres.
const DESIGNATE_REACH := 2.4
const DESIGNATE_GLOW := 2.6

## Le CHEVRON — « une illustration visuelle comme un indicateur qui indique les points
## d'ancrage » (opérateur, 2026-09-07, mot pour mot).
##
## ⚠️ LES ARCS SEULS NE SUFFISENT PAS, ET LA CAPTURE LE DIT. À 32,7 px/m, un éclair qui part
## d'une pièce de deux mètres posée au milieu d'une carène de quarante se lit comme une RAYURE
## sur la coque : il dit « il se passe quelque chose ici », pas « vise ICI ». Le chevron dit la
## seconde chose, et c'est la seule que Lyra ait besoin de faire comprendre.
##
## ⚠️ ET IL PASSE DEVANT TOUT. C'est le contraire exact de la règle du bandeau — qui, lui, doit
## se faire masquer parce qu'il APPARTIENT à la pièce. Un marqueur n'appartient à rien : à moitié
## enfoui derrière une nacelle, il désignerait la nacelle. Il ne vit que pendant la fenêtre, et
## c'est ce qui lui permet de tricher sur la profondeur sans devenir une interface.
const MARK_SPAN := 1.90
const MARK_RISE := 1.05
const MARK_STROKE := 0.34
const MARK_LIFT := 3.20
const MARK_BOB := 0.36
const MARK_HZ := 1.9
const MARK_FADE := 0.80

## La direction de vue de la caméra de jeu — (0 ; 14 ; 5), plongée 70,1° (`GameplayPlane`).
##
## ⚠️ ELLE SERT À DONNER UNE LARGEUR AUX ARCS. Un `PRIMITIVE_LINES` fait UN pixel quoi qu'il
## arrive : c'est ce qui les faisait ressembler à des fissures de la coque sur la première
## capture. Un ruban orienté face à la caméra a une épaisseur en MÈTRES, donc une épaisseur
## lisible à la densité du pont de poupe.
const VIEW_DIR := Vector3(0.0, -0.9403, -0.3403)
const ARC_WIDTH := 0.115

const HALO_LOCKED := 0.22
const HALO_INTACT := 0.85
const HALO_DAMAGED := 1.25

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
var _arc_mesh: ImmediateMesh = null
var _arcs: MeshInstance3D = null
var _arc_timer: float = 0.0
var _arc_rng := RandomNumberGenerator.new()
## Ce qu'il reste de la fenêtre de désignation, en secondes.
var _designate: float = 0.0
var _designate_span: float = 1.0
var _mark: MeshInstance3D = null
var _mark_mat: StandardMaterial3D = null
var _mark_base_y: float = 0.0
var _mark_clock: float = 0.0
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
	_build_arcs(size)
	_build_mark(size)
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

## Les arcs. ⚠️ UN SEUL MAILLAGE PAR VERROU, et il n'existe que tant qu'ils servent : c'est un
## instrument de lecture, il ne doit pas coûter dix objets par poupe.
func _build_arcs(size: Vector3) -> void:
	_arc_mesh = ImmediateMesh.new()
	_arcs = MeshInstance3D.new()
	_arcs.name = "Arcs"
	_arcs.mesh = _arc_mesh
	_arcs.position.y = size.y * 0.6
	_arcs.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# ⚠️ Sans marge, l'arc disparaît dès que le centre du verrou sort du cadre : la boîte
	# englobante d'un `ImmediateMesh` vide est nulle au montage. Piège déjà payé sur le nœud.
	_arcs.extra_cull_margin = 4.0
	var spark := StandardMaterial3D.new()
	spark.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	spark.vertex_color_use_as_albedo = true
	# Additif et sans écriture de profondeur : un éclair passe DEVANT la pièce sans la masquer,
	# et deux arcs qui se croisent s'additionnent au lieu de se découper.
	spark.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	spark.no_depth_test = true
	# Un ruban vu par sa tranche disparaîtrait la moitié du temps : pas de face arrière ici.
	spark.cull_mode = BaseMaterial3D.CULL_DISABLED
	spark.render_priority = 6
	_arcs.material_override = spark
	add_child(_arcs)
	_arc_rng.seed = hash(name) + serial * 7919

## Le chevron de désignation. Construit une fois : sa géométrie ne change pas, seuls sa taille,
## son ballant et sa lumière varient.
func _build_mark(size: Vector3) -> void:
	var forme := ImmediateMesh.new()
	forme.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	# Un V qui pointe vers le bas, dessiné dans le plan local XY : le matériau est en panneau
	# d'affichage, donc ce plan fait toujours face à la caméra, quel que soit le cadrage.
	_stroke(forme, Vector2(-MARK_SPAN * 0.5, MARK_RISE), Vector2.ZERO)
	_stroke(forme, Vector2.ZERO, Vector2(MARK_SPAN * 0.5, MARK_RISE))
	forme.surface_end()
	_mark = MeshInstance3D.new()
	_mark.name = "Mark"
	_mark.mesh = forme
	_mark_base_y = size.y * 0.5 + MARK_LIFT
	_mark.position.y = _mark_base_y
	_mark.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_mark.extra_cull_margin = 6.0
	_mark.visible = false
	_mark_mat = StandardMaterial3D.new()
	_mark_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mark_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_mark_mat.no_depth_test = true
	_mark_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	# ⚠️ ET SANS FACE ARRIÈRE À ÉLIMINER. Un panneau d'affichage dont on aurait pris le sens
	# de rotation à l'envers ne rend RIEN, sans erreur ni avertissement — le défaut se
	# diagnostique par une capture vide, ce qui coûte un cycle de déploiement complet.
	_mark_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_mark_mat.render_priority = 7
	_mark_mat.albedo_color = Color.WHITE
	_mark.material_override = _mark_mat
	add_child(_mark)

## Un trait épais entre deux points du plan local, en deux triangles.
func _stroke(forme: ImmediateMesh, un: Vector2, deux: Vector2) -> void:
	var n := (deux - un).orthogonal().normalized() * (MARK_STROKE * 0.5)
	var p: Array[Vector2] = [un + n, deux + n, deux - n, un - n]
	for i: int in [0, 1, 2, 0, 2, 3]:
		var v: Vector2 = p[i]
		forme.surface_add_vertex(Vector3(v.x, v.y, 0.0))

## ⚠️ LE NIVEAU MONTRE CE DONT IL PARLE. Appelée quand Lyra désigne les ancrages, et quand les
## verrous centraux s'ouvrent — les deux seuls moments où le joueur apprend quelque chose.
func designate(duration: float) -> void:
	_designate = maxf(_designate, duration)
	_designate_span = maxf(_designate, 0.001)

func is_designated() -> bool:
	return _designate > 0.0

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
	if _designate > 0.0:
		_designate = maxf(_designate - delta, 0.0)
	_tick_mark(delta)
	_arc_timer -= delta
	if _arc_timer <= 0.0:
		_arc_timer = 1.0 / ARC_REDRAW_HZ
		_redraw_arcs()
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

## Le battement du chevron. ⚠️ IL RESPIRE ET IL BALLOTTE, parce qu'un triangle immobile posé
## au-dessus d'une pièce se confond avec une pièce de plus. C'est le mouvement qui le sépare du
## vaisseau, pas sa forme.
func _tick_mark(delta: float) -> void:
	if _mark == null:
		return
	var portant := _look == Look.INTACT or _look == Look.DAMAGED
	_mark.visible = _designate > 0.0 and portant
	if not _mark.visible:
		return
	_mark_clock += delta
	var battement := sin(_mark_clock * MARK_HZ * TAU)
	_mark.position.y = _mark_base_y + MARK_BOB * battement
	var taille := 1.0 + 0.10 * battement
	_mark.scale = Vector3(taille, taille, taille)
	# ⚠️ IL S'ÉTEINT, IL NE DISPARAÎT PAS. Un marqueur qui s'efface d'une image à l'autre se lit
	# comme un défaut d'affichage — le joueur croit avoir perdu quelque chose.
	var reste := minf(_designate / MARK_FADE, 1.0)
	# Et il entre par le même chemin : la première seconde le monte au lieu de le poser.
	var entree := minf((_designate_span - _designate) / MARK_FADE, 1.0)
	var force: float = 2.2 * reste * entree * (0.82 + 0.18 * battement)
	_mark_mat.albedo_color = Color(1.0, 0.72, 0.94) * force

## Refait la figure. ⚠️ SEULEMENT SUR UN VERROU QU'ON PEUT ABATTRE : c'est ce qui fait des arcs
## une désignation et non une décoration.
func _redraw_arcs() -> void:
	if _arc_mesh == null:
		return
	_arc_mesh.clear_surfaces()
	if _look != Look.INTACT and _look != Look.DAMAGED:
		return
	var portee := ARC_REACH
	var force := 1.0
	if _designate > 0.0:
		portee = DESIGNATE_REACH
		force = 1.6
	elif _look == Look.DAMAGED:
		portee = ARC_REACH * 1.35
		force = 1.3
	_arc_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	var blanc := Color(1.0, 0.94, 1.0, 1.0) * force
	var teinte := Color(TINT.r, TINT.g, TINT.b, 1.0) * force
	for i in ARC_COUNT:
		var angle := TAU * (float(i) + _arc_rng.randf() * 0.6) / float(ARC_COUNT)
		var direction := Vector3(cos(angle), 0.0, sin(angle))
		var precedent := direction * 0.25
		var teinte_avant := blanc
		var large_avant := ARC_WIDTH
		for step in range(1, ARC_SEGMENTS + 1):
			var k := float(step) / float(ARC_SEGMENTS)
			var point := direction * (0.25 + portee * k)
			point += Vector3.UP * (_arc_rng.randf_range(-ARC_JITTER, ARC_JITTER) + k * 0.30)
			point += Vector3(_arc_rng.randf_range(-ARC_JITTER, ARC_JITTER), 0.0,
				_arc_rng.randf_range(-ARC_JITTER, ARC_JITTER))
			# Le cœur est blanc, la pointe prend la couleur du verrou : c'est ce qui fait lire
			# une décharge plutôt qu'un fil.
			var teinte_apres := blanc.lerp(teinte, k)
			# ⚠️ ET L'ÉCLAIR S'AFFINE. Un ruban d'épaisseur constante se lit comme un tuyau ;
			# c'est la pointe effilée qui donne la direction, donc la pièce d'où ça part.
			var large_apres: float = ARC_WIDTH * (1.0 - 0.62 * k)
			_ribbon(precedent, point, large_avant, large_apres, teinte_avant, teinte_apres)
			precedent = point
			teinte_avant = teinte_apres
			large_avant = large_apres
	_arc_mesh.surface_end()

## Un segment d'éclair, en ruban face à la caméra. ⚠️ LA PERPENDICULAIRE VIENT DE LA DIRECTION
## DE VUE, pas d'un axe du monde : un ruban dont la largeur suivrait Y serait écrasé par la
## plongée de 70°, et un ruban dont elle suivrait X disparaîtrait sur les arcs horizontaux.
func _ribbon(un: Vector3, deux: Vector3, large_un: float, large_deux: float,
		teinte_un: Color, teinte_deux: Color) -> void:
	var axe := (deux - un)
	if axe.length_squared() < 0.000001:
		return
	var cote := axe.normalized().cross(VIEW_DIR)
	if cote.length_squared() < 0.000001:
		return
	cote = cote.normalized()
	var a1 := un + cote * large_un
	var a2 := un - cote * large_un
	var b1 := deux + cote * large_deux
	var b2 := deux - cote * large_deux
	for trio: Array in [[a1, teinte_un], [b1, teinte_deux], [b2, teinte_deux],
			[a1, teinte_un], [b2, teinte_deux], [a2, teinte_un]]:
		_arc_mesh.surface_set_color(trio[1] as Color)
		_arc_mesh.surface_add_vertex(trio[0] as Vector3)

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
	if _designate > 0.0 and (_look == Look.INTACT or _look == Look.DAMAGED):
		energie *= DESIGNATE_GLOW
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
