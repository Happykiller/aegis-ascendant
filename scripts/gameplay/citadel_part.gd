class_name CitadelPart
extends Node3D
## Une pièce destructible de la Citadelle de Défense : un relais, ou le noyau.
##
## ⚠️ ELLE EXISTE PARCE QUE LE VERROU A BESOIN D'UNE CIBLE QUI SE REFUSE. Toutes les autres
## cibles du niveau meurent de la même façon : on tire, les PV descendent, la pièce tombe. Le
## noyau, lui, doit rendre les tirs SANS PERDRE UN POINT tant que les deux relais vivent
## (`C6` du plan) — et c'est une invulnérabilité CONDITIONNELLE, pas temporaire. Le
## `_shield_grace` d'`EnemyController` répond à l'autre question : il compte un délai.
##
## ⚠️ ET UN NOYAU « TRÈS RÉSISTANT » NE FERAIT PAS L'AFFAIRE. À 99 % de PV qui descendent
## lentement, le joueur lit un boss et cherche à le finir au lieu de chercher ce qui le protège.
## La règle est donc BOOLÉENNE : aucun dégât, et le tir se voit rebondir. C'est ce que `deflected`
## porte — la pièce dit qu'on l'a touchée en vain, et la citadelle décide comment ça se montre.
##
## ⚠️ CE N'EST PAS LA GÉOMÉTRIE DÉFINITIVE, ET C'EST VOULU (lot 1 du plan). La pièce est une
## boîte : « ne pas passer du temps sur les greebles ou les effets tant que la boucle complète
## n'est pas jouable de bout en bout » (opérateur). La silhouette est le lot 2, sa lecture le
## lot 3 — ce fichier ne porte que la RÈGLE.

## Ce que la pièce est dans la séquence. ⚠️ PAS UNE FAMILLE VISUELLE : c'est ce qui décide de
## quel signal la citadelle écoute, et donc de la boucle « deux relais puis le centre ».
enum Role { RELAY, CORE }

signal destroyed(part: CitadelPart)
## Un tir a porté et n'a rien coûté. ⚠️ IL PART À CHAQUE TIR REFUSÉ, et c'est la seule façon de
## rendre la règle visible sans un mot de HUD : un noyau qui absorbe en silence se lit comme une
## hitbox absente, donc comme un bug.
signal deflected(part: CitadelPart, world: Vector3)

## Le magenta de FONCTION, celui du reste du niveau (`d93d9c`) — la teinte de l'explosion et de
## l'impact refusé. ⚠️ PAS L'AMBRE D'`ADR-0043` : l'ambre est un repère technique et « ne signale
## jamais une cible ». Ce qui se tire reste magenta, partout, ou le joueur apprend deux
## grammaires pour une seule règle. La FORME, elle, vient du kit (`BRIEF-0096`).
const TARGET_TINT := Color("d93d9c")

## De combien la pièce reste tirable au-delà du plan de vol. ⚠️ ELLE DÉBORDE PARCE QUE LA CAMÉRA
## VOIT PLUS LOIN QUE LE PLAN : on tire sur une pièce du verrou avant qu'elle n'y entre, comme
## on tire sur un pont d'envol avant qu'il n'arrive.
const PLANE_MARGIN := 2.0

var role: Role = Role.RELAY
## Ce que la pièce rapporte. Lu par le niveau, qui ne connaît pas les rôles.
var score: int = 0
## Où la masse se projette sur le plan de jeu, sous une caméra qui plonge à 70°.
##
## ⚠️ SANS ELLE, ON TIRE À CÔTÉ EN VISANT JUSTE. La pièce est vissée sur une coque à Y = −4 et
## le plan de jeu est à Y = 0 : deux points de même X et Z mais de hauteurs différentes ne se
## projettent pas au même pixel. C'est le défaut que `GameplayPlane.aim_point_of` corrige, et il
## a coûté deux mètres d'erreur sur les tourelles avant d'être vu.
var lift: float = 0.0

var _health: float = 0.0
var _health_max: float = 0.0
var _alive: bool = true
var _vulnerable: bool = true
var _target: BulletTarget = null
var _bullets: BulletManager = null
var _vfx: VFXManager = null
var _world: Vector3 = Vector3.ZERO
var _registered: bool = false
var _mesh: MeshInstance3D = null
## Les copies de matériau qui n'appartiennent qu'à CETTE pièce, et l'énergie que la forge y a
## calibrée. Le battement l'entoure, il ne la remplace pas.
var _glow: Array[StandardMaterial3D] = []
var _glow_base: float = 1.0


static func make(p_role: Role, p_health: float, p_radius: float,
		p_lift: float, p_score: int) -> CitadelPart:
	var part := CitadelPart.new()
	part.role = p_role
	part.score = p_score
	part.lift = p_lift
	part._health = p_health
	part._health_max = p_health
	# La cible naît avec la pièce — même contrat que la tourelle et le nœud d'épine : il n'y a
	# qu'une porte pour les dégâts, et les tests passent par elle.
	part._target = BulletTarget.make(BulletManager.Team.ENEMY, p_radius, part._take_damage)
	part._target.enabled = false
	return part

## Prend sa forme dans le kit de la Citadelle (`BRIEF-0096`).
##
## ⚠️ ELLE S'APPROPRIE SA LUEUR, ET SANS ÇA ABATTRE UN RELAIS ÉTEINDRAIT LES DEUX. Les deux
## relais sont deux instances de la MÊME pièce du `.glb` : ils partagent donc le matériau
## `AA_Emissive_Engine` que la forge y a posé. Éteindre le partagé, c'est éteindre l'autre bord —
## exactement le piège que les cinq bulbes d'épine cuits dans la coque rendaient inévitable, et
## qui a déjà été payé sur les puits et sur les tourelles. Un état par pièce demande un matériau
## par pièce.
##
## ⚠️ ET LE MONTAGE EST FACULTATIF. Un banc de test monte la pièce sans arbre et sans kit : elle
## doit rester pilotable, parce que c'est la RÈGLE qu'on y vérifie, pas la silhouette.
## ⚠️ `side` ET `inset` NE SONT PAS DE LA CÉRÉMONIE : SANS EUX LA PIÈCE PART AILLEURS, ET LE
## JOURNAL NE DIT RIEN. La forge cuit le **X de coque dans la géométrie** — le relais tribord est
## modelé à `x` 5,40 → 7,00, et le miroir se fait par un yaw de π, pas par un signe. Or ce nœud-ci
## se place, lui, au CENTRE DE MASSE de la pièce (`±6,20`), parce que c'est de là que se déduit
## la hitbox. Composer les deux sans rien retrancher additionne deux fois le même écart :
## la pièce de tribord s'en va à `x` 11,60 — au large du bastion, au-dessus du vide — et celle de
## bâbord, faute de yaw, revient se poser SUR L'AXE, derrière le noyau.
##
## ⚠️ ET C'EST LA CAPTURE QUI L'A VU, PAS LES TESTS. Le build était vert, les 850 tests aussi, et
## les deux relais étaient à des dizaines de mètres de leur place. `test_the_two_relays_land_where
## _the_kit_says` garde désormais la COMPOSITION — position du nœud plus boîte du maillage — au
## lieu de garder chaque moitié séparément.
func mount(source: MeshInstance3D, side: float = 1.0, inset: float = 0.0) -> void:
	if source == null or source.mesh == null:
		return
	_mesh = MeshInstance3D.new()
	_mesh.name = "Shape"
	_mesh.position.x = -side * inset
	_mesh.rotation.y = 0.0 if side > 0.0 else PI
	_mesh.mesh = source.mesh
	_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for i in source.mesh.get_surface_count():
		var base := source.mesh.surface_get_material(i) as StandardMaterial3D
		if base == null:
			continue
		if not base.emission_enabled:
			_mesh.set_surface_override_material(i, base)
			continue
		var mine: StandardMaterial3D = base.duplicate()
		_mesh.set_surface_override_material(i, mine)
		_glow_base = mine.emission_energy_multiplier
		_glow.append(mine)
	add_child(_mesh)

func setup(bullet_manager: BulletManager, vfx: VFXManager) -> void:
	_bullets = bullet_manager
	_vfx = vfx

# --- Ce que la citadelle lit ---------------------------------------------------

func is_alive() -> bool:
	return _alive

## ⚠️ VULNÉRABLE N'EST PAS « VIVANT ». Le noyau est vivant tout le temps et vulnérable seulement
## quand les deux relais sont tombés : confondre les deux rendrait le bouclier invisible au code
## qui doit l'afficher.
func is_vulnerable() -> bool:
	return _vulnerable

func set_vulnerable(on: bool) -> void:
	_vulnerable = on

## La part de vie qui reste, de 1 à 0. Lue par la mise en scène, jamais par la règle.
## Fait battre la lueur de CETTE pièce, en part de l'énergie que la forge lui a calibrée.
##
## ⚠️ RELATIF ET NON ABSOLU : écrire une énergie en dur ici écraserait `emissiveStrength` du
## binaire, et la prochaine reforge qui la retoucherait n'aurait aucun effet — en silence. Même
## contrat que le nœud d'épine.
func set_glow(factor: float) -> void:
	for material in _glow:
		material.emission_energy_multiplier = _glow_base * maxf(factor, 0.0)

func health_ratio() -> float:
	return clampf(_health / maxf(_health_max, 0.001), 0.0, 1.0)

## La cible que le gestionnaire de balles connaît. ⚠️ EXPOSÉE PARCE QUE C'EST LE VRAI CHEMIN DES
## DÉGÂTS : un test qui appellerait une méthode écrite pour lui ne vérifierait pas le chemin que
## le jeu emprunte.
func target() -> BulletTarget:
	return _target

## Un pas de la pièce. ⚠️ SA POSITION LUI EST DONNÉE, ELLE NE LA LIT PAS DANS L'ARBRE — même
## contrat que le nœud d'épine, et pour la même raison : c'est ce qui la rend pilotable sans
## scène, donc vérifiable sans jouer trente secondes de survol.
func tick(world: Vector3, here: Vector2) -> void:
	_world = world
	if _target == null:
		return
	_target.position = here
	if not _alive:
		return
	# ⚠️ ELLE N'EST TIRABLE QUE DANS LE PLAN, ET C'EST UNE ÉCONOMIE AUTANT QU'UNE JUSTESSE. Une
	# cible inscrite alors qu'elle est encore à trente unités devant fait payer son test à
	# chaque balle du niveau, et se laisserait toucher par un tir perdu hors cadre.
	#
	# ⚠️ ET LE VA-ET-VIENT EST SYMÉTRIQUE, CE QU'IL N'ÉTAIT PAS. La première écriture éteignait
	# la cible en sortant du plan SANS remettre le drapeau d'inscription : la pièce qui rentrait
	# à nouveau restait éteinte À VIE. Cible inscrite, tir qui la traverse, verrou inouvrable —
	# et pas une ligne au journal. La caméra bouge (secousses, recadrages), donc la frontière
	# est franchie dans les deux sens pour de vrai.
	var inside := GameplayPlane.is_inside(here, PLANE_MARGIN)
	if inside and not _registered:
		_registered = true
		if _bullets != null:
			_bullets.register_target(_target)
	_target.enabled = inside
	# ⚠️ ET UNE PIÈCE VIVANTE QUI PASSE SOUS LE PLAN REND SA CIBLE POUR DE BON. Le survol dure
	# encore deux minutes après le verrou : une cible qui resterait inscrite ferait payer son
	# test à chaque balle de ce qui reste, pour une pièce qu'on ne peut plus jamais toucher —
	# le survol ne revient jamais en arrière. C'est la passe monotone que la tourelle et le nœud
	# d'épine tiennent déjà, et qui manquait ici.
	if here.y < GameplayPlane.BOUNDS.position.y - PLANE_MARGIN:
		_retire()

func _take_damage(damage: float) -> void:
	if not _alive:
		return
	if not _vulnerable:
		# ⚠️ AUCUN POINT NE BOUGE, ET LE TIR SE VOIT QUAND MÊME. C'est la moitié de la règle :
		# refuser en silence apprendrait au joueur que la pièce n'a pas de hitbox.
		deflected.emit(self, _world)
		return
	_health -= damage
	if _health > 0.0:
		return
	_alive = false
	if _vfx != null:
		_vfx.spawn_explosion(_world,
			VfxExplosion.Category.HEAVY if role == Role.CORE else VfxExplosion.Category.MEDIUM,
			TARGET_TINT)
	# ⚠️ LA LUEUR S'ÉTEINT AVANT QUE LA FORME NE PARTE, et l'ordre importe pour la trame où les
	# deux arrivent : un matériau encore allumé sur un maillage déjà libéré n'éteint rien.
	for material in _glow:
		material.emission_energy_multiplier = 0.0
	_glow.clear()
	if _mesh != null:
		_mesh.queue_free()
		_mesh = null
	_retire()
	destroyed.emit(self)

## ⚠️ ELLE REND SA CIBLE, ET CE N'EST PAS UNE PROPRETÉ D'INTENTION. Trois cibles qui resteraient
## inscrites après leur mort feraient payer à chaque balle du reste du niveau le coût d'un test
## qui ne peut plus rien toucher — et le survol dure encore deux minutes après le verrou.
func _retire() -> void:
	if _target == null:
		return
	_target.enabled = false
	if _registered and _bullets != null:
		_bullets.unregister_target(_target)
	_registered = false
