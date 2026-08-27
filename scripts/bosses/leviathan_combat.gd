class_name LeviathanCombat
extends Node
## Le combat du Pale Leviathan : **trois cycles, deux temps par cycle** (`ADR-0021`).
##
##     BRISER L'ARMURE  →  PLONGER DANS LE NOYAU  →  éjecté  →  l'armure revient, amoindrie
##
## Cycle 1 : 4 plaques et 4 tourelles-épines. Cycle 2 : 3. Cycle 3 : 2. Le boss se
## dégrade à vue et chaque cycle est plus court que le précédent.
##
## COMPOSITION — `BossController` garde tout le générique (entrée, déplacement, roulis,
## PV, signaux HUD, mort, prise de main sur le déplacement) et sert toujours le Choir
## Harvester. Ce module ne lui prend que deux choses, exactement comme `HarvesterCombat` :
## l'armement (`external_attacks`) et la vulnérabilité du corps.
##
## ⚠️ CE QUE LE PLAYTEST A DEMANDÉ, ET CE QUE CHAQUE PIÈCE DE CE FICHIER Y RÉPOND.
## Verdict : « extrêmement lancinant — le boss va de gauche à droite, on arrose les
## plaques sans faire gaffe en attendant qu'elles disparaissent ; les antennes, je ne
## vois pas à quoi elles servent ; et qu'il faille tirer le noyau, on ne le comprend pas ».
##
##   1. **Les épines tirent** (`_run_spines`). Ce sont des tourelles laser télégraphiées,
##      et **chaque plaque brisée en fait tomber une**. Casser une plaque retire une
##      menace qu'on peut nommer — le rideau s'allège d'un laser, pas d'un septième
##      d'éventail que personne ne compte.
##   2. **On entre dans le noyau** (`_run_dive`). La cible ne se devine plus : le corps
##      s'ouvre, le chasseur y est aspiré, et le flux d'énergie remplit l'écran. La mise
##      en scène (caméra, autopilote, paroi) est au niveau ; le module publie les temps.
##   3. **Les plaques tombent vite** (460 PV au lieu de 1270). Le grief est le temps passé
##      sans décision : la première salve d'armure passe de ~22 s à ~8 s.
##
## ⚠️ « RIEN NE REPOUSSE » N'EST PLUS VRAI, et c'est délibéré (ADR-0021 amende ADR-0018).
## L'armure revient entre deux plongées, avec une plaque de moins à chaque fois. Le boss
## ne se répare pas : il se répare **de plus en plus mal**, et ça se lit sur sa silhouette.
##
## ⚠️ LES PHASES N'AVANCENT PAS AUX SEUILS DE POINTS DE VIE. Chaque bascule a une
## condition matérielle : toutes les plaques du cycle à terre, ou le compte à rebours du
## noyau épuisé. Un boss qui avancerait sur ses PV changerait d'état sans que rien à
## l'écran ne l'explique — c'est ce que faisait le `BossController` générique.

const PLATE_SLOTS := 4
## Distance de repli des plaques au centre, quand aucune coque n'est montée (tests).
## La coque réelle les porte à 3,10 m ; cette valeur ne sert qu'à garder une géométrie
## cohérente là où il n'y a rien à mesurer.
const DEFAULT_PLATE_DIST := 2.6
## Vitesse de rattrapage de l'orientation du croissant, en fraction d'écart par seconde.
const SHELL_FACING_RATE := 1.6
const SPINE_SLOTS := 4
const NODE_COUNT := 3
## Durée de chute d'une pièce détachée, en secondes.
const DEBRIS_FALL_TIME := 1.2

enum Phase { ARMOR, DIVE, DEFEATED }
## Les trois temps d'une plongée. Le module les traverse ; le niveau les met en scène.
enum Dive { ENTER, INSIDE, EJECT }
## Les états d'une tourelle-épine. Mêmes noms que le canon du Harvester, même grammaire :
## un télégraphe, un tir, une récupération.
enum Spine { DOWN, READY, WINDUP, FIRING, RECOVER }

## Le HUD et le niveau écoutent ; le module ne connaît ni l'un ni l'autre.
signal phase_entered(phase: int)
## Santé restante de ce qu'on peut casser MAINTENANT — l'armure du cycle, ou le flux
## pendant la plongée. ⚠️ Ce n'est pas la progression du combat : voir `fight_ratio()`.
signal structure_changed(ratio: float)
signal piece_gauge_changed(index: int, ratio: float, alive: bool)
## Plaque à viser (`-1` = aucune). Émis SEULEMENT au changement.
signal piece_active_changed(index: int)
signal piece_destroyed(phase: int, index: int, world_position: Vector3)
## Aspiration à appliquer au chasseur. Le niveau la relaie ; le module ne touche jamais
## au joueur directement.
signal pull_changed(speed_max: float, radius: float, centre: Vector2)
## La plongée s'ouvre : le niveau prend la main sur la caméra et l'autopilote.
signal dive_started(cycle: int, centre: Vector2)
## Le chasseur est dedans, le tir commence.
signal dive_entered(cycle: int)
## Éjection. `flux_down` dit si le flux est mort — auquel cas le boss meurt juste après.
signal dive_ended(cycle: int, flux_down: bool)
## L'armure s'est reformée, avec `plates` plaques. Le niveau l'annonce au joueur : sans
## cela, une armure qui revient se lit comme un bug, pas comme une mécanique.
signal armour_reformed(cycle: int, plates: int)
## L'armure se reforme, de 0 à 1, et avec COMBIEN de plaques elle revient. Émis pendant
## l'éjection, et une dernière fois à 0 quand elle est là. Sans lui, le joueur passait une
## seconde devant un boss qui ne faisait rien et ne le disait pas (playtest du 2026-08-27).
##
## Le nombre de plaques accompagne le ratio parce que la rangée du HUD doit se dresser AVANT
## que l'armure existe : c'est elle qui montre la reconstruction, cuve par cuve.
signal armour_regen(ratio: float, plates: int)
## Le blindage rotatif s'ouvre ou se referme sur l'azimut du joueur. Émis au CHANGEMENT
## seulement : c'est un état, pas une mesure, et le niveau s'en sert pour dire au joueur —
## sans passer par l'interface — si son tir compte en ce moment.
signal reactor_shield_changed(open: bool)

## Temps qu'il reste dans le noyau, de 1 à 0. ⚠️ **−1 hors plongée** : le HUD doit ÉTEINDRE
## le sablier plutôt que le laisser plein, une barre pleine et figée se lisant comme une
## jauge en panne. Demandé au playtest du 2026-08-27 — la plongée a deux sorties, quota
## rempli ou temps écoulé, et seule la première se voyait.
signal dive_time_left(ratio: float)
## Un tir du joueur a heurté le blindage FERMÉ. Le niveau en fait une gerbe et un son.
##
## ⚠️ SANS LUI, LE BLINDAGE MENT. Le verrou est logique (`BulletTarget.enabled`), pas
## physique : les bolts traversaient l'anneau plein sans rien produire. Le projet a déjà
## nommé ce défaut sur le Harvester — « tirer dessus sans rien produire à l'écran se lit
## comme un défaut, pas comme une armure ».
signal shield_deflected(world_position: Vector3)
## L'état d'un verrou orbital : sa part de vie, et s'il tient encore. Le niveau en fait une
## pastille dans la rangée du HUD — celle-là même qui porte les plaques pendant l'armure.
signal node_gauge_changed(index: int, ratio: float, alive: bool)
## Un verrou tombe. Le niveau en fait une explosion à sa position.
signal node_destroyed(index: int, world_position: Vector3)
## Les verrous sont tous à terre : le réacteur redevient atteignable — quand le corridor
## s'ouvre. Émis une fois par plongée.
signal nodes_cleared

## Graine et part de la dérive organique du flux. Une part modeste : la cible doit rester
## SUIVABLE — « assez pour qu'on suive, pas assez pour qu'on cherche » reste la règle.
const FLUX_DRIFT_SEED := 0.29
const FLUX_ORGANIC_SHARE := 0.45

## État courant du blindage. Faux au repos : hors plongée, il n'y a pas de corridor, et
## annoncer « ouvert » ferait clignoter le signal à chaque entrée.
var _reactor_open: bool = false
## La cible qui ARRÊTE les tirs quand le corridor est fermé. Posée sur l'anneau, au droit du
## joueur : c'est là que ses bolts croisent le blindage.
var _shield_target: BulletTarget
## Le faisceau balayant du réacteur, et son horloge d'armement.
var _sweep: Beam
var _sweep_age: float = 0.0

## Les verrous orbitaux. Tant qu'il en reste un, le flux est intouchable — même corridor
## ouvert. C'est le second gate de la phase, et il se démonte à la main.
var _node_targets: Array[BulletTarget] = []
var _node_health: PackedFloat32Array = PackedFloat32Array()
var _nodes_alive: int = 0

## Rayon de la cible qui arrête les tirs. Assez large pour attraper les bolts des canons
## d'aile, qui montent en parallèle et non depuis l'axe du chasseur.
##
## ⚠️ Un rayon FIXE l'accompagnait, celui de l'anneau extérieur, recopié depuis le décor. Il
## est devenu faux le jour où les murs ont bougé — et il n'aurait de toute façon jamais
## décrit un mur INTÉRIEUR. La position se calcule désormais.
const SHIELD_CATCH_RADIUS := 0.95

@export var tuning: LeviathanTuning
@export var projectile: ProjectileData

var _boss: BossController
var _hull: Node3D
var _bullet_manager: BulletManager
var _player: PlayerFighterController

var _phase: Phase = Phase.ARMOR
var _dive: Dive = Dive.ENTER
var _dive_elapsed: float = 0.0
## Cycle courant, 0-indexé.
var _cycle: int = 0
var _age: float = 0.0
## Répit entre deux temps : le boss ne tire pas, le joueur voit ce qu'il a cassé.
var _interlude: float = 0.0

var _plates: Array[LeviathanPlate] = []
var _flux_target: BulletTarget
var _flux_health: float = 0.0
## Dégâts déjà encaissés par le flux PENDANT la plongée en cours — le plafond d'un passage.
var _dive_damage: float = 0.0
var _missiles: Array[TargetableProjectile] = []

## Rotation de la coquille, en radians — le tempo du temps 1.
var _shell_rotation: float = 0.0
## Orientation vers laquelle le croissant se tient, hors balancement. Suivie en douceur :
## le joueur traverse l'écran, la coquille ne doit pas sauter avec lui.
var _shell_facing: float = 0.0
var _shell_facing_set: bool = false
var _active_piece: int = -1
var _shell_ring: Node3D
var _shell_ring_rest: Transform3D = Transform3D.IDENTITY
## Nombre de volets de l'iris et d'anneaux du puits — le contrat de `BRIEF-0083`.
const IRIS_BLADES := 6
const BORE_RINGS := 5
## Course du recul et du glissement, en mètres (mesures de la forge).
const IRIS_RECOIL := 1.5
const IRIS_SLIDE := 0.6
## Part de l'ouverture consacrée au recul avant que le glissement commence.
const IRIS_RECOIL_SHARE := 0.55
## Ouverture à partir de laquelle le puits est dégagé.
const IRIS_BORE_OPEN := 0.35

var _heart_node: Node3D
## Les six volets de l'iris (`BRIEF-0083`), et leur pose au repos. Enfants de `Core`.
var _shutters: Array[Node3D] = []
var _shutter_rest: Array[Transform3D] = []
## Les pièces qui BOUCHENT le puits, à escamoter quand l'iris s'ouvre.
##
## ⚠️ SANS ÇA, L'IRIS S'OUVRE SUR RIEN. Mesuré par la forge sur le `.glb` et visible sur sa
## planche de recette (vignette 5 contre vignette 6) : volets grands ouverts, le trou que
## le joueur voit reste bouché par `Ring_01..05` à 0,193 m et par le maillage de `Core`.
## Le mécanisme joue, et l'écran ne montre aucune ouverture — exactement le grief
## d'origine (« ça change, ça ne s'ouvre pas »).
var _bore_fillers: Array[MeshInstance3D] = []
## Maillage propre de `Core`, mis de côté pendant l'escamotage.
##
## ⚠️ ON RETIRE LE MAILLAGE, ON NE CACHE PAS LE NŒUD. Les six volets sont ENFANTS de
## `Core` : `visible = false` sur le nœud escamoterait l'iris avec le noyau, et le
## mécanisme qu'on vient de fabriquer disparaîtrait au moment précis où il doit se voir.
var _core_mesh: Mesh
var _core_instance: MeshInstance3D
var _highlight: StandardMaterial3D
## Le flux d'énergie, dans le noyau ouvert : sa propre identité visuelle.
##
## ⚠️ MESURÉ, PAS SUPPOSÉ. Le grief du playtest — « on ne voit rien, je ne sais pas du tout
## ce qu'il faut faire » — n'était pas un excès de lumière. Relevé sur capture : la chambre
## est à R−G 41,9 / B−G 34,9, le flux à 31,5 / 25,6. **Dix points d'écart sur les deux axes
## de teinte** : la cible et le décor occupaient la même case chromatique, et seule la
## luminance les séparait — ce qui ne désigne pas une cible. Le flux vire donc au **blanc
## chaud**, la seule teinte que ni la chambre (rouge-violet) ni le fond spatial (bleu)
## n'occupent.
var _flux_glow: StandardMaterial3D
## État du halo de flux, pour ne réassigner le `material_overlay` qu'au changement.
var _flux_lit: bool = false
## Ouverture de la coquille, de 0 (close) à 1 (le noyau est béant).
var _shell_open: float = 0.0

## Les tourelles-épines. Tableaux parallèles, dimensionnés une fois : aucune allocation
## pendant le combat.
var _spine_nodes: Array[Node3D] = []
var _spine_rest: Array[Transform3D] = []
## Pointe de chaque épine, en espace LOCAL de son nœud.
##
## ⚠️ L'origine d'un nœud `Spike_0X` est à sa BASE, contre le corps — mesuré sur le
## `.glb` : origine à (0,0,0), maillage centré à z = +0,99, longueur 2,63. Tirer depuis
## `node.global_position` fait donc partir le laser du CORPS, pas de la pointe. Au
## playtest : « ça sort d'un peu n'importe où, ça manque de cohésion ». La pointe est le
## sommet de la boîte englobante le plus éloigné de cette origine.
var _spine_tip: Array[Vector3] = []
var _spine_beams: Array[Beam] = []
## Direction de tir de chaque épine, dans le plan. Relevée à chaque pointage.
##
## Elle existe pour être VÉRIFIABLE : le faisceau n'est monté que dans l'arbre de scène,
## donc jamais en test, et sans cela la seule propriété qui compte ici — le tir prolonge
## l'axe de la pièce — ne pourrait être gardée nulle part. Préallouée, jamais réallouée.
var _spine_aim: PackedVector2Array = PackedVector2Array()
var _spine_state: PackedInt32Array = PackedInt32Array()
var _spine_timer: PackedFloat32Array = PackedFloat32Array()

## Les nœuds décoratifs, qui tombent avec la première armure.
var _debris: Array[Node3D] = []
var _debris_rest: Array[Transform3D] = []
var _debris_fall: PackedFloat32Array = PackedFloat32Array()
## Chute des plaques abattues, par emplacement.
var _plate_fall: PackedFloat32Array = PackedFloat32Array()
## Pose d'origine de chaque emplacement de plaque, relevée UNE SEULE FOIS au montage.
##
## ⚠️ Ne jamais la relire depuis le nœud au début d'un cycle : à ce moment-là la plaque
## est encore dans la pose où sa chute l'a laissée — basculée et écartée. On mémoriserait
## cette pose comme « repos », et l'armure reformée repousserait de travers, un peu plus à
## chaque cycle.
var _plate_rest: Array[Transform3D] = []
## Disposition RÉELLE des emplacements de plaque, relevée une fois au montage.
## `_plate_angle` et `_plate_dist` sont dans le plan de jeu (hitbox, exposition) ;
## `_plate_radial` est un rayon 3D dans le repère du parent (axe de chute).
var _plate_angle: PackedFloat32Array = PackedFloat32Array()
var _plate_dist: PackedFloat32Array = PackedFloat32Array()
var _plate_radial: Array[Vector3] = []

var _fan_timer: float = 0.0
var _missile_timer: float = 0.0
## Dégâts encaissés par la cible courante — le numérateur de la jauge.
var _local_damage: float = 0.0
## Dégâts encaissés depuis le début du combat — la progression, qui ne remonte jamais.

## Les formes de collision de la chambre, refaites à chaque image et JAMAIS réallouées.
## Voir [PlaneShapes] : les murs tournent et le noyau dérive, donc les fabriquer en objets
## reviendrait à allouer soixante fois par seconde dans une boucle critique (spec §26.1).
var _shapes := PlaneShapes.new()

## Dégâts placés sur le FLUX seul, et la SEULE mesure d'avancement du combat. Un compteur
## « tous dégâts confondus » vivait ici ; il a été retiré avec la jauge qui le lisait, plutôt
## que laissé à dormir. La jauge du boss ne doit descendre QUE dans le noyau — « en phase
## externe du boss sa barre de vie ne devrait pas descendre » (playtest du 2026-08-27).
## L'armure est une PORTE, pas de la santé : elle repousse à chaque cycle, et compter sa
## destruction comme un progrès promettait au joueur un avancement qu'il perdait aussitôt.
var _flux_damage: float = 0.0

# --- Montage ------------------------------------------------------------------

func _ready() -> void:
	_boss = get_parent() as BossController
	if _boss == null:
		push_error("[Leviathan] le module doit etre enfant d'un BossController")
		return
	if tuning == null:
		# ⚠️ On REND l'armement au boss générique. Sans cela le module ne monte pas,
		# `external_attacks` reste à `true` (déclaré dans la scène), le boss ne tire
		# rien, et `vulnerable` garde son défaut : le boss final devient un sac à PV
		# inoffensif. Dégrader vers l'ancien comportement vaut mieux que dégrader vers
		# l'absence de combat.
		push_error("[Leviathan] aucun LeviathanTuning : retour aux motifs generiques")
		_boss.external_attacks = false
		set_physics_process(false)
		return
	var errors := tuning.validate()
	if not errors.is_empty():
		# Le réglage est refusé AVANT le combat, pas découvert au milieu.
		push_error("[Leviathan] tuning invalide : %s" % ", ".join(errors))
	_boss.external_attacks = true
	_boss.began.connect(_on_boss_began)
	_boss.defeated.connect(_on_boss_defeated)
	set_physics_process(false)

func _on_boss_began(bullet_manager: BulletManager, player: PlayerFighterController) -> void:
	setup(_boss.hull(), bullet_manager, player)
	set_physics_process(true)

func _on_boss_defeated(_world_position: Vector3) -> void:
	set_physics_process(false)
	release()

## Montage. `hull` peut être nul : les tests font tourner toute la boucle sans coque,
## et une plaque sans nœud à poser reste une plaque qui vit, encaisse et tombe.
func setup(hull: Node3D, bullet_manager: BulletManager, player: PlayerFighterController) -> void:
	_hull = hull
	_bullet_manager = bullet_manager
	_player = player
	release()
	_cycle = 0
	_flux_health = tuning.flux_health
	_flux_damage = 0.0
	_plate_fall.resize(PLATE_SLOTS)
	_plate_fall.fill(-1.0)
	_plate_rest.clear()
	for i in PLATE_SLOTS:
		var node: Node3D = _hull.find_child("Plate_%02d" % (i + 1), true, false) as Node3D if _hull != null else null
		_plate_rest.append(node.transform if node != null else Transform3D.IDENTITY)
	_build_flux()
	# ⚠️ AVANT `_measure_plate_layout()` : la mesure a besoin de `Shell_Ring`, qui est le
	# centre du cercle des plaques et l'origine du repère de leur axe de chute.
	_bind_shell_visual()
	_measure_plate_layout()
	_build_spines()
	_collect_debris()
	_arm_cycle(0)
	_enter_phase(Phase.ARMOR)
	# Hook de vérification : la plongée arrive après huit secondes de jeu, donc personne
	# ne la REGARDE jamais (ADR-0006). `++ --leviathan-phase=2` y saute.
	_apply_phase_hook()

## (Re)dresse l'armure du cycle : `plates_for_cycle` plaques et autant de tourelles.
##
## ⚠️ CE COMMENTAIRE DÉCRIVAIT UNE INTENTION QUE LE CODE N'A JAMAIS EUE. Il annonçait des
## plaques « REDISTRIBUÉES à chaque cycle », réparties à 120° quand il n'en reste que
## trois. Rien de tel n'arrivait au maillage : `plate.node.transform = rest_transform`
## le remet à sa place sculptée, et seule la HITBOX se déplaçait. On bougeait la cible
## sans bouger la pièce, ce qui est la cause du défaut corrigé ici.
##
## Les emplacements sont ceux de la coque, définitivement. Quand des plaques tombent, les
## survivantes ne se réarrangent pas : le croissant se creuse, et c'est le balancement
## face au joueur (`shell_sway_deg`) qui garantit qu'il y a toujours une cible.
func _arm_cycle(cycle: int) -> void:
	var alive := tuning.plates_for_cycle(cycle)
	_release_plates()
	_plates.clear()
	for i in alive:
		# ⚠️ L'ANGLE VIENT DE LA COQUE. Il valait `TAU·i/alive` — une redistribution
		# régulière qui n'était appliquée QU'À LA HITBOX : le maillage, lui, retrouve sa
		# pose sculptée deux lignes plus bas. On déplaçait la cible sans déplacer la pièce.
		var plate := LeviathanPlate.make(i, _plate_angle[i], tuning.plate_health,
			tuning.plate_hitbox_radius, Callable(self, "_on_plate_hit").bind(i))
		plate.radius = _plate_dist[i]
		plate.orient_fall(_plate_radial[i] if i < _plate_radial.size() else Vector3.ZERO)
		if _hull != null:
			plate.node = _hull.find_child("Plate_%02d" % (i + 1), true, false) as Node3D
			if plate.node == null:
				push_error("[Leviathan] coque sans 'Plate_%02d' (contrat BRIEF-0040)" % (i + 1))
			else:
				plate.rest_transform = _plate_rest[i]
				plate.rest_basis = plate.rest_transform.basis
				# La plaque qui revient RETROUVE sa pose d'origine, pas celle où sa chute
				# l'a laissée.
				plate.node.transform = plate.rest_transform
				plate.node.visible = true
				_collect_meshes(plate.node, plate.meshes)
		_plates.append(plate)
		if _bullet_manager != null:
			_bullet_manager.register_target(plate.target)
		_plate_fall[i] = -1.0
	# Les emplacements au-delà du compte restent à terre, invisibles.
	for i in range(alive, PLATE_SLOTS):
		_plate_fall[i] = 1.0
		if _hull != null:
			var node := _hull.find_child("Plate_%02d" % (i + 1), true, false) as Node3D
			if node != null:
				node.visible = false
	for i in _spine_state.size():
		var up := i < alive
		_spine_state[i] = Spine.READY if up else Spine.DOWN
		# Les épines se relaient au lieu de tirer ensemble : quatre lasers simultanés
		# sont un mur, quatre lasers déphasés sont une danse.
		_spine_timer[i] = tuning.spine_interval * float(i) / float(maxi(alive, 1))
		if i < _spine_nodes.size() and _spine_nodes[i] != null:
			_spine_nodes[i].visible = up
			_spine_nodes[i].transform = _spine_rest[i]
		if i < _spine_beams.size() and _spine_beams[i] != null:
			_spine_beams[i].extinguish()
	_local_damage = 0.0
	_active_piece = -1
	# Le croissant se recentre : moins de plaques, donc un milieu différent.
	_shell_facing_set = false
	_shell_open = 0.0

## Relève la disposition RÉELLE des plaques, une seule fois au montage.
##
## ⚠️ MESURÉ, PAS CONVENU — et c'est un correctif, pas un raffinement. Le code posait
## `base_angle = TAU·i/alive`, soit quatre plaques réparties sur 360°. La coque en porte
## quatre sur un CROISSANT de 198° — son nœud s'appelle `Shell_Crescent`, et `BRIEF-0041`
## a validé cette silhouette. Azimuts réels dans le plan de jeu : −28 / 26 / 80 / 134°,
## tous à 3,10 m de l'axe (rayon constant : elles sont bien sur un cercle).
##
## Écart mesuré entre ce que le code croyait et ce que la coque porte : 152 / 64 / 80 /
## 136°, soit jusqu'à **5,05 m** entre la hitbox et le maillage sur une coque de 11 m. La
## plaque qui BRILLE n'était donc pas celle qu'on pouvait TOUCHER. Rien ne pouvait le
## montrer : une hitbox ne se dessine pas, et aucun test ne comparait les deux — ils
## vérifiaient que `base_angle` valait `TAU·i/4`, c'est-à-dire que le bug était bien là.
func _measure_plate_layout() -> void:
	_plate_angle.resize(PLATE_SLOTS)
	_plate_dist.resize(PLATE_SLOTS)
	_plate_radial.clear()
	# Le centre du cercle des plaques est l'axe de la COQUILLE, pas l'origine du boss :
	# c'est autour de lui que `_pose_shell()` les fait tourner. Mesuré sur la coque, les
	# quatre sont à 3,100 m de cet axe — un rayon constant, donc c'est bien le bon centre.
	var centre := Vector2.ZERO
	if _shell_ring != null and _boss != null:
		centre = GameplayPlane.to_plane(_relative_to(_shell_ring, _boss).origin)
	for i in PLATE_SLOTS:
		# Repli : la répartition régulière d'avant. Les tests font tourner toute la boucle
		# sans coque, et une plaque sans nœud doit rester cohérente avec elle-même.
		var ang := wrapf(TAU * float(i) / float(PLATE_SLOTS), -PI, PI)
		var dist := DEFAULT_PLATE_DIST
		var radial := Vector3(cos(ang), 0.0, sin(ang))
		var node: Node3D = _hull.find_child("Plate_%02d" % (i + 1), true, false) as Node3D \
			if _hull != null else null
		if node != null and _boss != null:
			var here := _relative_to(node, _boss)
			var rel := GameplayPlane.to_plane(here.origin) - centre
			if rel.length_squared() > 0.01:
				ang = rel.angle()
				dist = rel.length()
			# L'axe de chute vit dans le repère du PARENT de la plaque — `rest_basis
			# .rotated()` compose à gauche — et NON en monde. Un axe juste exprimé dans le
			# mauvais repère fait basculer la pièce de travers sans qu'aucun test bronche.
			var host := node.get_parent() as Node3D
			if host != null and _shell_ring != null:
				var to_host := _relative_to(host, _boss)
				var arm := to_host.basis.inverse() \
					* (here.origin - _relative_to(_shell_ring, _boss).origin)
				arm.y = 0.0
				if arm.length_squared() > 0.0001:
					radial = arm.normalized()
		_plate_angle[i] = ang
		_plate_dist[i] = dist
		_plate_radial.append(radial)

## Transformation de `node` dans le repère de `ancestor`, composée à la main.
##
## ⚠️ NE PAS employer `global_transform` ici. Il n'a de valeur que pour un nœud DANS
## l'arbre de scène, et les tests n'y montent jamais rien : ils bâtissent des arbres
## locaux. La mesure serait alors silencieusement remplacée par son repli — le test
## passerait au vert en ne gardant rien, ce qui est le défaut même qu'on répare ici.
static func _relative_to(node: Node3D, ancestor: Node3D) -> Transform3D:
	var t := Transform3D.IDENTITY
	var cur := node
	while cur != null and cur != ancestor:
		t = cur.transform * t
		cur = cur.get_parent() as Node3D
	return t

func _build_flux() -> void:
	_flux_target = BulletTarget.make(BulletManager.Team.ENEMY, tuning.flux_hitbox_radius,
		Callable(self, "_on_flux_hit"))
	_flux_target.enabled = false   # il n'existe que dans le noyau, pendant la plongée
	# ⚠️ LA CIBLE D'ARRÊT PASSE EN PREMIER. `BulletManager._resolve_hits` parcourt les cibles
	# dans l'ordre d'enregistrement et CONSOMME la balle sur la première qui la réclame. Le
	# blindage doit donc être vu avant le flux — sinon un tir traverserait un anneau fermé
	# pour aller toucher le noyau, ce qui est exactement ce qu'il est censé empêcher.
	# (Les deux ne sont jamais actives en même temps, mais l'ordre est une garantie, pas un
	# effet de bord d'un état.)
	_shield_target = BulletTarget.make(BulletManager.Team.ENEMY, SHIELD_CATCH_RADIUS,
		Callable(self, "_on_shield_hit"))
	_shield_target.enabled = false
	_node_targets.clear()
	_node_health.resize(tuning.node_count)
	for i in tuning.node_count:
		var node := BulletTarget.make(BulletManager.Team.ENEMY, tuning.node_hitbox_radius,
			Callable(self, "_on_node_hit").bind(i))
		node.enabled = false
		_node_targets.append(node)
	if _bullet_manager != null:
		# ⚠️ ORDRE D'ENREGISTREMENT : les verrous D'ABORD. Ils orbitent EN DEHORS de l'anneau
		# extérieur, donc un bolt les croise avant le blindage ; enregistrés après, le
		# blindage aurait consommé des tirs destinés à ce qui le verrouille.
		for node in _node_targets:
			_bullet_manager.register_target(node)
		_bullet_manager.register_target(_shield_target)
		_bullet_manager.register_target(_flux_target)

## Résout la coquille, le cœur et le halo. Nuls en test (coque absente) : la boucle
## tourne sans 3D, seule la géométrie des hitbox compte.
func _bind_shell_visual() -> void:
	_shell_ring = null
	_heart_node = null
	if _hull != null:
		_shell_ring = _hull.find_child("Shell_Ring", true, false) as Node3D
		if _shell_ring == null:
			push_error("[Leviathan] coque sans 'Shell_Ring' (contrat BRIEF-0040)")
		else:
			_shell_ring_rest = _shell_ring.transform
		# ⚠️ `Core`, PAS `Heart`. Mesuré dans le `.glb` : `Heart` fait 0,63 × 0,31 × 0,56 m et
		# vit à l'intérieur du noyau — invisible. `Core` fait 3,17 × 2,38 × 3,17 m : c'est la
		# masse que le joueur voit au centre quand la coquille s'ouvre. Tout le traitement
		# visuel du « cœur » a d'abord été posé sur `Heart` : son battement n'a jamais rien
		# fait à l'écran, et le halo du flux non plus. On animait une pièce invisible.
		_heart_node = _hull.find_child("Core", true, false) as Node3D
		_bind_iris()
	if _highlight == null:
		# Additif, non éclairé : un halo qui s'AJOUTE à la texture au lieu de la
		# remplacer. Il monte vers le blanc chaud au sommet de son battement, sans quoi
		# il se lit comme un reflet sur une coque déjà rose.
		_highlight = StandardMaterial3D.new()
		_highlight.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_highlight.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		_highlight.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_highlight.albedo_color = Color(0.95, 0.35, 0.72, 1.0)
	if _flux_glow == null:
		_flux_glow = StandardMaterial3D.new()
		_flux_glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_flux_glow.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		_flux_glow.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_flux_glow.albedo_color = Color(1.0, 0.92, 0.72, 0.0)   # éteint hors du noyau

## Les épines deviennent des tourelles. Leur faisceau n'est construit que dans l'arbre :
## en test il reste nul, et `_fire_spine` le null-garde — la portée est éprouvée à part
## par `test_beam_geometry.gd`, sur la fonction statique.
func _build_spines() -> void:
	_spine_nodes.clear()
	_spine_rest.clear()
	_spine_tip.clear()
	_spine_beams.clear()
	if _sweep == null:
		_sweep = Beam.make()
		# ⚠️ `top_level` comme les épines : `Beam.aim()` pose le faisceau en coordonnées du
		# monde, et un parent qui bouge le décalerait deux fois.
		_sweep.top_level = true
		_sweep.visible = false
		# ROUGE, et non le corail par défaut : c'est la couleur que la spec de l'opérateur
		# réserve au danger immédiat, et l'orange est déjà pris par les explosions et les
		# bonus. Rouge sécurité Helios (charte créative) pour le bord, cœur blanc chaud.
		_sweep.tint(Color(1.0, 0.90, 0.86), Color("c93a31"))
		add_child(_sweep)
	_spine_state.resize(SPINE_SLOTS)
	_spine_timer.resize(SPINE_SLOTS)
	_spine_aim.resize(SPINE_SLOTS)
	for i in SPINE_SLOTS:
		var node: Node3D = null
		if _hull != null:
			node = _hull.find_child("Spike_%02d" % (i + 1), true, false) as Node3D
			if node == null:
				push_error("[Leviathan] coque sans 'Spike_%02d' (contrat BRIEF-0040)" % (i + 1))
		_spine_nodes.append(node)
		_spine_rest.append(node.transform if node != null else Transform3D.IDENTITY)
		# ⚠️ LA COQUE LIVRE SA PROPRE BOUCHE. `Muzzle_Spike_0X` fait partie du contrat de
		# noms depuis le premier brief, posé au bout de l'épine — et personne ne l'avait
		# câblé : le code calculait la pointe par boîte englobante alors que le point exact
		# était dans le `.glb`. Mesuré : base à ~4,1 du centre, bouche à ~5,0.
		# Le calcul reste en repli, pour une coque qui n'aurait pas la bouche.
		var muzzle := _hull.find_child("Muzzle_Spike_%02d" % (i + 1), true, false) as Node3D \
			if _hull != null else null
		if muzzle != null and node != null and _boss != null:
			# Composé à la main : `global_transform` exige l'arbre de scène, que les tests
			# ne montent jamais. La pointe retomberait sur son repli sans que rien ne le
			# dise — même piège que pour la disposition des plaques.
			_spine_tip.append(_relative_to(node, _boss).affine_inverse()
				* _relative_to(muzzle, _boss).origin)
		else:
			_spine_tip.append(_far_corner(node))
		var beam: Beam = null
		if is_inside_tree():
			beam = Beam.make()
			# ⚠️ `top_level` OBLIGATOIRE. `Beam.aim()` pose le faisceau en coordonnées
			# MONDE ; ce module est un `Node` enfant du `BossController`, et Godot remonte
			# l'arbre jusqu'au premier ancêtre `Node3D` pour composer les transformations —
			# le faisceau subirait donc la position du boss DEUX fois et partirait hors du
			# cadre. Symptôme : aucun laser à l'écran, et rien au journal.
			beam.top_level = true
			add_child(beam)
		_spine_beams.append(beam)
		_spine_state[i] = Spine.DOWN
		_spine_timer[i] = 0.0

## Les nœuds : décor pur depuis ADR-0020, ils tombent avec la première armure.
func _collect_debris() -> void:
	_debris.clear()
	_debris_rest.clear()
	_debris_fall.resize(0)
	if _hull == null:
		return
	for i in NODE_COUNT:
		var node := _hull.find_child("Node_%02d" % (i + 1), true, false) as Node3D
		if node == null:
			continue
		node.visible = true
		_debris.append(node)
		_debris_rest.append(node.transform)
		_debris_fall.append(-1.0)

## Sommet de la boîte englobante d'un nœud le plus éloigné de son origine, en espace
## local. C'est la pointe d'une épine — le seul endroit d'où un laser puisse partir sans
## que ça se voie.
static func _far_corner(node: Node3D) -> Vector3:
	if node == null:
		return Vector3.ZERO
	var box := AABB()
	var first := true
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(node, meshes)
	if not node.is_inside_tree():
		return Vector3.ZERO   # hors arbre (tests) : pas de coque, donc pas de pointe
	var to_node := node.global_transform.affine_inverse()
	for mesh in meshes:
		# ⚠️ Passer par les transformations GLOBALES : composer `mesh.transform` à la main
		# ne marche que si le maillage est le nœud lui-même ou son enfant direct, et se
		# trompe silencieusement d'un niveau dès qu'il est plus profond.
		var local: AABB = to_node * (mesh.global_transform * mesh.mesh.get_aabb())
		box = local if first else box.merge(local)
		first = false
	if first:
		return Vector3.ZERO
	var best := Vector3.ZERO
	var far := -1.0
	for i in 8:
		var corner := box.get_endpoint(i)
		var d := corner.length()
		if d > far:
			far = d
			best = corner
	return best

## Tous les `MeshInstance3D` sous un nœud, racine comprise. Mirror de `HarvesterLimb`.
static func _collect_meshes(node: Node, into: Array[MeshInstance3D]) -> void:
	var mesh := node as MeshInstance3D
	if mesh != null and mesh.mesh != null:
		into.append(mesh)
	for child in node.get_children():
		_collect_meshes(child, into)

func _apply_phase_hook() -> void:
	for arg in OS.get_cmdline_user_args():
		if not arg.begins_with("--leviathan-phase"):
			continue
		var wanted := arg.get_slice("=", 1).to_int() if "=" in arg else 0
		if wanted >= 2:
			_force_dive()
		return

## Abat toute l'armure du cycle et ouvre la plongée. Réservé au hook de debug.
##
## ⚠️ Passe par `_on_plate_hit`, pas par `plate.apply_damage` : c'est le chemin réel des
## dégâts, celui qui fait tomber les épines et publie les jauges. Le raccourci menait à
## un état que le jeu ne produit jamais.
func _force_dive() -> void:
	if _phase != Phase.ARMOR:
		return
	for plate in _plates:
		_on_plate_hit(plate.max_health, plate.index)

# --- Boucle -------------------------------------------------------------------

func _physics_process(delta: float) -> void:
	tick(delta)

## Toute la logique du combat. Publique et sans dépendance à l'arbre : les tests la
## pilotent directement, ce qui rend vérifiable un enchaînement qu'aucune capture ne
## pourrait couvrir — trois cycles demandent quarante secondes de jeu.
func tick(delta: float) -> void:
	if tuning == null:
		return
	_age += delta
	var origin := _origin()
	_tick_missiles(delta)
	_tick_debris(delta)
	_tick_plate_falls(delta)
	if _interlude > 0.0:
		_interlude = maxf(_interlude - delta, 0.0)
		_pose_shell()
		return
	match _phase:
		Phase.ARMOR: _run_armor(delta, origin)
		Phase.DIVE: _run_dive(delta, origin)
		Phase.DEFEATED: return
	_sync_targets(origin)

## Position du boss dans le plan. Le plan est la vérité des collisions : il ne dépend ni
## de l'arbre ni du roulis, et reste lisible en test où rien n'est monté.
func _origin() -> Vector2:
	return _boss.plane_position if _boss != null else Vector2.ZERO

func _sync_targets(origin: Vector2) -> void:
	for plate in _plates:
		var a := plate.angle_at(_shell_rotation)
		plate.target.position = origin + Vector2(cos(a), sin(a)) * plate.radius
	if _flux_target != null:
		_flux_target.position = _flux_origin(origin) + _flux_offset()

## Azimut moyen des plaques encore debout, au repos — le « milieu » du croissant.
##
## Moyenne CIRCULAIRE : la moyenne arithmétique de −170° et +170° vaut 0°, soit le point
## diamétralement opposé au bon. Le croissant vit à cheval sur le repli de l'angle dès
## que la coquille a tourné, donc ce piège est la règle et non l'exception.
func _crescent_bearing() -> float:
	var x := 0.0
	var y := 0.0
	for plate in _plates:
		if not plate.is_up():
			continue
		x += cos(plate.base_angle)
		y += sin(plate.base_angle)
	if absf(x) < 0.0001 and absf(y) < 0.0001:
		return 0.0
	return atan2(y, x)

## Direction du joueur vue du boss, en radians dans le plan de jeu. Sans joueur monté
## (tests, écran-titre), la convention du projet : il est en dessous, à −90°.
func _player_bearing(origin: Vector2) -> float:
	if _player == null:
		return -PI * 0.5
	var to_player := _player.plane_position - origin
	return to_player.angle() if to_player.length_squared() > 0.01 else -PI * 0.5

## Où vit le flux pendant la plongée, dans le plan de jeu.
##
## ⚠️ LE BOSS RESTE DEHORS QUAND LE JOUEUR ENTRE. Depuis que la plongée bascule vers une
## zone dédiée (`CoreInterior`), la cible n'est plus au centre du corps du boss mais sur le
## réacteur de cette zone, monté à l'origine du monde. Laisser le flux sur le boss le
## plaçait hors de l'arène intérieure : on tirait dans le vide sans que rien ne le signale.
##
## `Vector2.INF` — la valeur au repos — veut dire « aucune zone montée » : on retombe alors
## sur le corps du boss, ce qui est exactement le comportement d'avant. Les tests, qui ne
## montent aucune zone, ne changent donc pas de régime.
var dive_anchor: Vector2 = Vector2.INF

## Le blindage rotatif : le flux n'est atteignable que si TOUS les anneaux ouvrent sur
## l'azimut du joueur (`ReactorRings`).
##
## ⚠️ C'EST CE QUI TRANSFORME UNE CIBLE FIXE EN PUZZLE DE POSITIONNEMENT — le défaut nommé
## au playtest : « le joueur entre dans le noyau puis se retrouve face à une cible quasiment
## fixe ». Il ne s'agit pas d'attendre : un corridor existe en permanence quelque part sur
## le cercle (simulé), il faut ALLER le chercher.
##
## Sans anneau réglé, le flux reste atteignable en permanence : le comportement d'avant,
## que les tests existants continuent de mesurer.
func _update_reactor_shield(origin: Vector2) -> void:
	if _flux_target == null:
		return
	# ⚠️ DEUX PORTES, ET IL FAUT LES DEUX. Le corridor dit QUAND on peut tirer, les verrous
	# disent SI. Un joueur qui trouve son corridor avant d'avoir abattu les verrous tire donc
	# encore dans le vide — d'où la gerbe de déviation, qui vaut pour les deux cas.
	var open := _nodes_alive == 0
	var centre := _flux_origin(origin)
	var hit := Vector2.INF
	if open and not tuning.reactor_rings.is_empty() and _player != null:
		# ⚠️ LA LIGNE DE TIR, PAS L'AZIMUT. Le chasseur tire DROIT VERS LE HAUT : se placer
		# sur le côté ne lui donne aucun angle sur le noyau, et un corridor calculé depuis
		# son azimut ne décrivait pas ce que ses balles rencontrent. On teste le segment
		# qu'un bolt doit VRAIMENT parcourir, du chasseur jusqu'au flux.
		# ⚠️ LE NOYAU EST EXCLU DE CE TEST, et il faut le dire. Il est dans `_shapes` pour
		# arrêter le CHASSEUR ; s'il y restait ici, il bloquerait le tir qui le vise —
		# la cible ferait écran à elle-même. On s'arrête donc au bord du flux.
		var to_local := _flux_offset()
		var aim := centre + to_local
		var stop := aim + (_player.plane_position - aim).normalized() \
			* tuning.flux_hitbox_radius
		hit = PlaneCollider.first_hit(_shapes, _player.plane_position, stop,
			tuning.bolt_radius)
		open = hit == PlaneCollider.NO_HIT
	_flux_target.enabled = open
	# La cible d'arrêt vit à l'inverse : elle n'existe QUE quand le corridor est fermé, et
	# elle se pose sur l'anneau, au droit du joueur — là où ses bolts croisent le blindage.
	if _shield_target != null:
		# ⚠️ LA CIBLE D'ARRÊT SE POSE LÀ OÙ LE MUR EST VRAIMENT, sur le premier point de la
		# ligne de tir qui touche du plein. Elle était posée sur un rayon fixe et sur
		# l'azimut du joueur : les bolts la manquaient et traversaient le mur — « les tirs
		# aussi peuvent passer » (playtest du 2026-08-27).
		_shield_target.enabled = not open and hit != PlaneCollider.NO_HIT
		if _shield_target.enabled:
			_shield_target.position = hit
	if open != _reactor_open:
		_reactor_open = open
		reactor_shield_changed.emit(open)

## L'âge du combat, celui dont `ReactorRings` déduit l'ouverture. Public parce que le décor
## doit poser ses anneaux sur LA MÊME horloge : une seconde source de temps ferait dériver
## l'image par rapport à l'état réel, et le joueur tirerait dans un blindage qu'il croit
## ouvert.
func combat_age() -> float:
	return _age

## Redresse les verrous — MOINS NOMBREUX À CHAQUE CYCLE, exactement comme l'armure
## (`ADR-0021` : « le boss se répare de plus en plus mal »).
##
## ⚠️ LE DÉFAUT QUE ÇA CORRIGE, ET IL A RENDU LE COMBAT INFINI. Ils se relevaient ENTIERS à
## chaque plongée. Un joueur qui ne parvenait pas à les abattre dans les cinq secondes ne
## touchait donc JAMAIS le flux — zéro dégât, à chaque passage, pour toujours. Playtest du
## 2026-08-27 : « DERNIER ASSAUT » onze fois de suite, puis l'opérateur a fermé le jeu.
##
## Ce n'était pas une question d'équilibrage mais de STRUCTURE : une porte remise à neuf à
## chaque tentative est un mur binaire, pas une difficulté. Le projet avait déjà répondu à
## ça pour l'armure ; les verrous suivent la même règle.
func _arm_nodes() -> void:
	_nodes_alive = 0
	var standing := maxi(tuning.node_count - _cycle, 1) if tuning.node_count > 0 else 0
	for i in _node_targets.size():
		var alive := i < standing
		_node_health[i] = tuning.node_health if alive else 0.0
		_node_targets[i].enabled = alive
		if alive:
			_nodes_alive += 1
		node_gauge_changed.emit(i, 1.0 if alive else 0.0, alive)

## Les verrous tournent autour du réacteur, régulièrement répartis.
func _orbit_nodes(origin: Vector2) -> void:
	if _node_targets.is_empty():
		return
	var centre := _flux_origin(origin)
	var step := TAU / float(_node_targets.size())
	var turn := deg_to_rad(tuning.node_orbit_deg * _age)
	for i in _node_targets.size():
		if not _node_targets[i].enabled:
			continue
		var a := turn + step * float(i)
		_node_targets[i].position = centre \
			+ Vector2(cos(a), sin(a)) * tuning.node_orbit_radius

func _on_node_hit(damage: float, index: int) -> void:
	if index < 0 or index >= _node_targets.size():
		return
	if not _node_targets[index].enabled:
		return
	_node_health[index] = maxf(_node_health[index] - damage, 0.0)
	_account(damage)
	node_gauge_changed.emit(index, _node_health[index] / maxf(tuning.node_health, 0.001), true)
	if _node_health[index] > 0.0:
		return
	_node_targets[index].enabled = false
	_nodes_alive -= 1
	node_gauge_changed.emit(index, 0.0, false)
	node_destroyed.emit(index, GameplayPlane.to_world(_node_targets[index].position))
	if _nodes_alive <= 0:
		nodes_cleared.emit()

## Où se trouve un verrou, dans le plan de jeu. Le décor s'en sert pour le dessiner : une
## seconde source de position ferait dessiner le verrou ailleurs qu'il ne se touche.
func node_plane_position(index: int) -> Vector2:
	if index < 0 or index >= _node_targets.size():
		return Vector2.ZERO
	return _node_targets[index].position

## Ce verrou tient-il encore ?
func node_alive(index: int) -> bool:
	return index >= 0 and index < _node_targets.size() and _node_targets[index].enabled

## Combien de verrous tiennent encore.
func nodes_alive() -> int:
	return _nodes_alive

## Le joueur ne TRAVERSE pas les murs. Il est repoussé radialement, du côté d'où il vient.
##
## ⚠️ APPLIQUÉ ICI ET NON DANS LE CONTRÔLEUR DU JOUEUR : les murs n'existent que pendant la
## plongée, et le chasseur n'a aucune raison de connaître le réacteur. La contrainte vit
## avec ce qui la produit — c'est déjà la règle de l'aspiration (`pull_changed`).
##
## ⚠️ Et elle s'applique APRÈS le déplacement du joueur, pas à sa place : sa commande reste
## pleine, on corrige seulement le résultat. Piloter à sa place se lirait comme une perte de
## contrôle, ce que le projet refuse depuis `GravityWell.leaves_room()`.
## Verse dans `shapes` tout ce que le Leviathan oppose au chasseur, À CET INSTANT.
##
## ⚠️ CE QUI EST SOLIDE CHANGE AVEC LA PHASE, et c'est le fond de ce boss. Pendant l'armure,
## c'est sa COQUE et ses plaques ; dans le noyau, ce sont les murs rotatifs et le flux. Les
## verser tous ensemble ferait apparaître une coque là où le joueur a plongé pour l'oublier.
##
## Le niveau appelle ceci ; il ne connaît ni les plaques ni les anneaux. C'est l'application
## de la loi « les corps ne se chevauchent pas » à ce boss (`docs/KB/REGLES/lois.md`), et
## c'est aussi ce qui la rend applicable au suivant : un boss déclare ses formes, il n'écrit
## pas de collision.
func fill_solids(shapes: PlaneShapes) -> void:
	if tuning == null:
		return
	var origin := _origin()
	if _phase == Phase.DIVE:
		# ⚠️ SEULEMENT UNE FOIS DANS LA CHAMBRE. Avant `dive_anchor`, le chasseur est encore
		# dehors, en approche guidée vers la gueule : verser les murs ici les posait autour du
		# CORPS DU BOSS, et un enregistrement de partie a montré le chasseur en contact avec
		# eux pendant tout le zoom d'entrée. Ils n'existent que dans le lieu qu'ils gardent.
		if not dive_anchor.is_finite():
			return
		var centre := _flux_origin(origin)
		ReactorRings.fill_shapes(shapes, tuning.reactor_rings, centre, _age)
		shapes.add_disc(centre + _flux_offset(), tuning.flux_hitbox_radius)
		return
	# ⚠️ PAS DE COQUE PENDANT L'ENTRÉE. Le boss descend vers sa place ; le rendre solide
	# pendant qu'il traverse l'arène pousserait un joueur qui n'a rien fait de mal.
	if _boss == null or not _boss.is_in_place():
		return
	shapes.add_disc(origin, _boss.hitbox_radius)
	for plate in _plates:
		if not plate.is_up():
			continue
		var a := plate.angle_at(_shell_rotation)
		shapes.add_disc(origin + Vector2(cos(a), sin(a)) * plate.radius,
			tuning.plate_hitbox_radius)

## Combien de formes `fill_solids()` peut produire — pour dimensionner UNE fois.
func solid_capacity() -> int:
	if tuning == null:
		return 0
	return maxi(ReactorRings.shape_count(tuning.reactor_rings) + 1,
		tuning.plate_count + 1)

## Refait les formes de la chambre pour CET instant : les murs tournant, plus le noyau.
##
## ⚠️ LE NOYAU EST UN CORPS, ET IL NE L'ÉTAIT PAS. « Le réacteur central ne devrait pas être
## franchissable » (playtest du 2026-08-27) : on lui traversait le ventre. Il entre ici comme
## un disque au même titre qu'un mur — c'est tout l'intérêt d'avoir un module de collision
## plutôt qu'un cas particulier par obstacle.
func _rebuild_shapes(origin: Vector2) -> void:
	var centre := _flux_origin(origin)
	_shapes.clear()
	ReactorRings.fill_shapes(_shapes, tuning.reactor_rings, centre, _age)
	_shapes.add_disc(centre + _flux_offset(), tuning.flux_hitbox_radius)

func _enforce_walls(_origin: Vector2) -> void:
	if _player == null or _shapes.size() == 0:
		return
	var here := _player.plane_position
	# ⚠️ UNE CAPSULE, PAS UN DISQUE. Décrit par un cercle de sa demi-envergure, le chasseur
	# laissait son NEZ dépasser de 0,38 et entrer dans le blindage — vu en jeu, capture à
	# l'appui, le 2026-08-27. Le corps se lit dans les stats, où il est MESURÉ sur le modèle.
	var freed := PlaneCollider.resolve_capsule(_shapes, here, _player.plane_forward(),
		_player.stats.body_half_length, _player.stats.body_radius)
	if not freed.is_equal_approx(here):
		_player.plane_position = freed

## Le faisceau qui balaie le réacteur. Il tourne en permanence pendant la plongée : c'est
## lui qui empêche de camper sous le noyau une fois le corridor trouvé.
##
## ⚠️ IL S'ARME APRÈS COUP. Pendant `sweep_arm_delay`, il est VISIBLE et INOFFENSIF : le
## joueur qui vient d'entrer voit d'où il part et dans quel sens il tourne avant de pouvoir
## en mourir. Une mort qu'on ne pouvait pas lire venir n'est pas une difficulté.
func _update_sweep(delta: float, origin: Vector2) -> void:
	if _sweep == null or tuning.sweep_half_width <= 0.0:
		return
	_sweep_age += delta
	var centre := _flux_origin(origin)
	var a := deg_to_rad(tuning.sweep_speed_deg * _age)
	var reach := centre + Vector2(cos(a), sin(a)) * tuning.sweep_range
	var armed := _sweep_age >= tuning.sweep_arm_delay
	_sweep.aim(centre, reach,
		tuning.sweep_half_width if armed else tuning.sweep_half_width * 0.30)
	_sweep.set_regime(2.6 if armed else 0.4, 0.0 if armed else 1.0)
	if not armed or _player == null:
		return
	if Beam.hits(centre, reach, tuning.sweep_half_width, _player.plane_position, 0.25):
		_player.take_contact_damage(tuning.sweep_damage)

## Le corridor est-il ouvert en ce moment, sur l'azimut du joueur ?
func reactor_open() -> bool:
	return _reactor_open

## Azimut d'une ouverture, en degrés, le plus proche de celui du joueur — ce vers quoi il
## doit aller. `ReactorRings.NO_OPENING` si le blindage est intégralement fermé.
func nearest_opening_deg(origin: Vector2) -> float:
	if tuning.reactor_rings.is_empty():
		return ReactorRings.NO_OPENING
	var bearing := rad_to_deg(_player_bearing(_flux_origin(origin)))
	return ReactorRings.nearest_opening(tuning.reactor_rings, bearing, _age)

## Rayon maximal de la dérive du flux autour de son ancre.
##
## ⚠️ CE N'EST PAS UN CERCLE DE RAYON `flux_drift_radius`. La figure de base est une
## Lissajous dont le coin atteint √2 × rayon, et la dérive organique s'y ajoute. Exposé
## pour que le repère visuel, les tests et le réglage partagent UNE vérité — la borne était
## jusqu'ici un `sqrt(2.0)` recopié dans deux tests, qui ne pouvait que diverger du code.
func flux_drift_envelope() -> float:
	if tuning == null or tuning.flux_drift_period <= 0.0:
		return 0.0
	return tuning.flux_drift_radius * sqrt(2.0) \
		+ OrganicDrift.max_offset(tuning.flux_drift_radius * FLUX_ORGANIC_SHARE)


## Où le flux est VRAIMENT, dans le plan de jeu — ancre du noyau plus sa dérive.
##
## ⚠️ PUBLIQUE PARCE QUE PERSONNE NE LE SAVAIT. La cible dérive jusqu'à 1,6 u de l'ancre, et
## rien ne la dessinait dans l'arène : le halo du flux se pose sur le cœur du boss, qui est
## resté DEHORS pendant la plongée. Le joueur tirait donc sur le réacteur du décor pendant
## que la cible était ailleurs — « le noyau semble juste un point du décor » (playtest du
## 2026-08-27). Le niveau s'en sert pour poser un repère qui SUIT la cible.
func flux_plane_position() -> Vector2:
	return _flux_origin(_origin()) + _flux_offset()

func _flux_origin(origin: Vector2) -> Vector2:
	if _phase != Phase.DIVE or not dive_anchor.is_finite():
		return origin
	return dive_anchor

## Dérive du flux dans le noyau : assez pour qu'on suive, pas assez pour qu'on cherche.
##
## ⚠️ La figure de base est une Lissajous de rapport 0,7 — donc elle BOUCLE. On lui ajoute
## la dérive organique (`ADR-0029`, périodes non harmoniques) : la cible reste suivable,
## sa trajectoire cesse d'être prévisible. C'est le « rien ne bouge, fête foraine » du
## playtest, appliqué au noyau.
func _flux_offset() -> Vector2:
	if _phase != Phase.DIVE or tuning.flux_drift_period <= 0.0:
		return Vector2.ZERO
	var t := TAU * _age / tuning.flux_drift_period
	var figure := Vector2(cos(t), sin(t * 0.7)) * tuning.flux_drift_radius
	return figure + OrganicDrift.offset(_age, FLUX_DRIFT_SEED,
		tuning.flux_drift_radius * FLUX_ORGANIC_SHARE)

# --- Temps 1 — BRISER L'ARMURE ------------------------------------------------

func _run_armor(delta: float, origin: Vector2) -> void:
	# ⚠️ ELLE NE SE REFERMAIT JAMAIS. `_shell_open` ne faisait que monter (pendant la
	# plongée) et n'était remis à zéro qu'au montage du combat : dès le premier cycle, la
	# coquille restait ouverte pour TOUJOURS, y compris pendant les armures suivantes que
	# la bannière annonce pourtant comme reformées. Invisible tant que rien n'était monté
	# dessus ; avec l'iris, elle laisserait les six volets écartés sur un boss censé être
	# clos, et la silhouette fermée exigée par le brief n'existerait qu'au premier cycle.
	if tuning.shell_open_time > 0.0:
		_shell_open = maxf(_shell_open - delta / tuning.shell_open_time, 0.0)
	# ⚠️ LE CROISSANT FAIT FACE AU JOUEUR, IL NE TOURNE PLUS EN ROND. L'armure ne couvre
	# que 198° : en rotation continue, son vide se présentait 27 % du temps au premier
	# cycle et 37 % au deuxième — deux à trois secondes par tour avec RIEN à tirer, ce
	# qui est précisément le « lancinant » du playtest. Ce n'était pas une question de
	# vitesse, c'était de la géométrie : aucun réglage de période ne l'enlevait.
	#
	# Un boss tourne sa protection vers la menace. Le croissant est donc tenu face au
	# joueur et balance autour de lui : les plaques défilent toujours — mesuré, les
	# quatre passent en tête à ±60° — mais le vide ne passe jamais devant.
	var facing := wrapf(_player_bearing(origin) - _crescent_bearing(), -PI, PI)
	if not _shell_facing_set:
		_shell_facing = facing
		_shell_facing_set = true
	else:
		_shell_facing = wrapf(_shell_facing
			+ wrapf(facing - _shell_facing, -PI, PI) * minf(delta * SHELL_FACING_RATE, 1.0),
			-PI, PI)
	var sway := 0.0
	if tuning.shell_orbit_period > 0.0:
		sway = deg_to_rad(tuning.shell_sway_deg) \
			* sin(TAU * _age / tuning.shell_orbit_period)
	_shell_rotation = wrapf(_shell_facing + sway, -PI, PI)
	var arc := tuning.effective_arc_deg(_plates_up())
	# La direction du joueur, MESURÉE. L'arc était centré sur 0, qui pointe le flanc
	# tribord du boss : avec des angles de plaque fictifs ça ne se voyait pas, avec les
	# vrais on exposerait un côté que le joueur ne regarde jamais.
	var aim := _player_bearing(origin)
	var active := -1
	var best := INF
	for plate in _plates:
		plate.tick(delta, tuning.shell_break_time)
		if not plate.is_exposed(_shell_rotation, arc, aim):
			continue
		var offset := absf(plate.offset_from(_shell_rotation, aim))
		if offset < best:
			best = offset
			active = plate.index
	# ⚠️ UNE SEULE plaque encaisse, et c'est celle qui brille. Quand toutes les plaques
	# exposées encaissaient, les dégâts se répartissaient sur quatre barres qui
	# descendaient ensemble : rien ne tombait avant la fin de la phase.
	for plate in _plates:
		plate.target.enabled = plate.index == active and plate.is_up()
	_set_active_piece(active)
	_pose_shell()
	_run_spines(delta, origin)
	_fan_timer -= delta
	if _fan_timer <= 0.0:
		_fan_timer = tuning.fan_interval
		_fire_fans(origin)
	_missile_timer -= delta
	if _missile_timer <= 0.0:
		_missile_timer = tuning.missile_salvo_interval
		_launch_missiles(origin)
	if _plates_up() == 0:
		_begin_dive()

## Les tourelles-épines. Trois temps, comme le canon du Harvester : le télégraphe fin qui
## annonce, le faisceau qui frappe, la récupération. ⚠️ C'est le télégraphe qui fait le
## duel — un laser sans réarme est un impôt, pas une attaque.
func _run_spines(delta: float, origin: Vector2) -> void:
	for i in _spine_state.size():
		if _spine_state[i] == Spine.DOWN:
			continue
		_spine_timer[i] -= delta
		if _spine_timer[i] > 0.0:
			if _spine_state[i] == Spine.WINDUP or _spine_state[i] == Spine.FIRING:
				_aim_spine(i, origin)
			continue
		match _spine_state[i]:
			Spine.READY:
				_spine_state[i] = Spine.WINDUP
				_spine_timer[i] = tuning.spine_windup_time
			Spine.WINDUP:
				_spine_state[i] = Spine.FIRING
				_spine_timer[i] = tuning.spine_beam_time
			Spine.FIRING:
				_spine_state[i] = Spine.RECOVER
				_spine_timer[i] = tuning.spine_recover_time
				if i < _spine_beams.size() and _spine_beams[i] != null:
					_spine_beams[i].extinguish()
			Spine.RECOVER:
				_spine_state[i] = Spine.READY
				_spine_timer[i] = tuning.spine_interval

## Tend le faisceau d'une épine et, s'il est armé, brûle ce qu'il touche.
##
## ⚠️ La bouche est la POINTE de l'épine quand la coque est là, pas un point calculé sur
## un cercle. Un laser qui sort du corps pendant que l'épine pointe ailleurs rend la
## menace illisible sur la silhouette — et c'est précisément ce qu'on reproche à ces
## pièces depuis le début : qu'on ne voie pas à quoi elles servent.
func _aim_spine(index: int, origin: Vector2) -> void:
	var direction := _spine_direction(index)
	var muzzle := origin + direction * 3.2
	var node: Node3D = _spine_nodes[index] if index < _spine_nodes.size() else null
	if node != null and _boss != null:
		# La bouche est la POINTE de l'épine — mesurée sur le maillage, pas l'origine du
		# nœud, qui est à sa base contre le corps.
		var here := _relative_to(node, _boss)
		var base := origin + GameplayPlane.to_plane(here.origin)
		muzzle = origin + GameplayPlane.to_plane(here * _spine_tip[index])
		# ⚠️ LE TIR SUIT L'AXE DE L'ÉPINE, enfin. Il partait de la pointe mais visait le
		# joueur : la pièce montrait une direction, le faisceau en prenait une autre, et
		# c'est le grief du playtest — « les lasers, ça sort d'un peu n'importe où ».
		# Deux épines sur quatre pointaient alors vers l'arrière ; prolonger leur axe
		# aurait tiré à l'opposé de la cible. `BRIEF-0081` a reforgé la coque : les
		# quatre visent le joueur (−28,9 / −139,1 / −104,4 / −68,5° dans le plan), donc
		# l'axe est enfin une direction de tir défendable.
		#
		# La direction se MESURE — base vers pointe — au lieu de se déduire d'un angle.
		# Elle ne dépend ainsi d'aucune convention de repère, et c'est ce qui a coûté
		# `BRIEF-0045` : `BossController` applique `FACING_PLAYER = (0, PI, 0)`, donc tout
		# axe relevé dans le `.glb` est vu retourné de 180° en jeu. Un vecteur mesuré
		# entre deux points du même repère ne peut pas se tromper de repère.
		var axis := muzzle - base
		if axis.length_squared() > 0.01:
			direction = axis.normalized()
	if index < _spine_aim.size():
		_spine_aim[index] = direction
	var reach := muzzle + direction * tuning.spine_range
	var firing := _spine_state[index] == Spine.FIRING
	if index < _spine_beams.size() and _spine_beams[index] != null:
		var beam := _spine_beams[index]
		beam.aim(muzzle, reach, tuning.spine_half_width if firing else tuning.spine_half_width * 0.35)
		beam.set_regime(2.4 if firing else 0.35, 0.0 if firing else 1.0)
	if not firing or _player == null:
		return
	if Beam.hits(muzzle, reach, tuning.spine_half_width, _player.plane_position, 0.25):
		_player.take_contact_damage(tuning.spine_damage)

## Direction d'une épine : sa place autour du corps, entraînée par la coquille. Le
## faisceau part donc là où l'épine POINTE — sinon le joueur ne peut pas lire la menace
## sur la silhouette, et le laser semble sortir de nulle part.
func _spine_direction(index: int) -> Vector2:
	var a := wrapf(TAU * float(index) / float(SPINE_SLOTS) + _shell_rotation * 0.5, -PI, PI)
	return Vector2(cos(a), sin(a))

# --- Temps 2 — PLONGER DANS LE NOYAU ------------------------------------------

func _begin_dive() -> void:
	_enter_phase(Phase.DIVE)

func _run_dive(delta: float, origin: Vector2) -> void:
	_dive_elapsed += delta
	_shell_open = minf(_shell_open + delta / tuning.shell_open_time, 1.0)
	_pose_shell()
	match _dive:
		Dive.ENTER:
			# L'aspiration accompagne le chasseur vers l'ouverture. Elle reste sous sa
			# vitesse : il entre parce qu'il le veut, pas parce qu'on le lui impose.
			pull_changed.emit(tuning.pull_speed_max, tuning.pull_radius, origin)
			if _dive_elapsed >= tuning.dive_enter_time:
				_set_dive(Dive.INSIDE)
		Dive.INSIDE:
			pull_changed.emit(0.0, tuning.pull_radius, origin)
			_orbit_nodes(origin)
			_rebuild_shapes(origin)
			_update_reactor_shield(origin)
			dive_time_left.emit(
				1.0 - clampf(_dive_elapsed / maxf(tuning.dive_time, 0.001), 0.0, 1.0))
			_update_sweep(delta, origin)
			if _dive_elapsed >= tuning.dive_time:
				_set_dive(Dive.EJECT)
		Dive.EJECT:
			# La reconstruction se MONTRE. Pas quand le flux est tombé : là, rien ne revient.
			if _flux_health > 0.0 and tuning.dive_eject_time > 0.0:
				armour_regen.emit(minf(_dive_elapsed / tuning.dive_eject_time, 1.0),
					tuning.plates_for_cycle(_cycle + 1))
			if _dive_elapsed >= tuning.dive_eject_time:
				_leave_dive()

func _set_dive(next: Dive) -> void:
	_dive = next
	_dive_elapsed = 0.0
	match next:
		Dive.INSIDE:
			# Le flux n'est une cible QUE dans le noyau : dehors, il n'est pas atteignable
			# et le joueur n'a aucune raison de croire qu'il l'est.
			# ⚠️ `_reactor_open` repart à faux : le premier alignement doit s'ANNONCER,
			# sinon le joueur entre dans un corridor déjà ouvert sans que rien ne le dise.
			_reactor_open = false
			_flux_target.enabled = tuning.reactor_rings.is_empty()
			_sweep_age = 0.0
			if _sweep != null:
				_sweep.visible = not tuning.reactor_rings.is_empty()
			_arm_nodes()
			_local_damage = 0.0
			_dive_damage = 0.0
			_publish_structure()
			dive_entered.emit(_cycle)
		Dive.EJECT:
			# Le sablier s'ÉTEINT, il ne se vide pas jusqu'à zéro : l'éjection peut venir du
			# quota rempli, et laisser la barre finir sa course dirait au joueur qu'il a été
			# sorti par le temps alors qu'il a réussi.
			dive_time_left.emit(-1.0)
			_flux_target.enabled = false
			_reactor_open = false
			if _shield_target != null:
				_shield_target.enabled = false
			for node in _node_targets:
				node.enabled = false
			_nodes_alive = 0
			if _sweep != null:
				_sweep.extinguish()
				_sweep.visible = false
			dive_ended.emit(_cycle, _flux_health <= 0.0)

## Fin de plongée : le boss meurt si le flux est tombé, sinon l'armure se reforme.
func _leave_dive() -> void:
	# Le corps reprend sa dérive : le combat redevient mobile en même temps que l'armure
	# revient. Relâcher AVANT la mort aussi, sinon un boss vaincu resterait figé pendant
	# la finale.
	if _boss != null:
		_boss.release_drive()
	if _flux_health <= 0.0:
		_enter_phase(Phase.DEFEATED)
		return
	_cycle += 1
	_arm_cycle(_cycle)
	_enter_phase(Phase.ARMOR)
	armour_regen.emit(0.0, _plates.size())   # elle est là : la reconstruction s'efface
	armour_reformed.emit(_cycle, _plates.size())

# --- Rendu de la coque --------------------------------------------------------

## Fait tourner la coquille, l'écarte pendant la plongée, pulse le halo de la plaque à
## viser et couche les pièces abattues. Un seul écrivain sur la pose (le module), comme
## le Harvester : deux auteurs sur une même rotation finissent par se marcher dessus.
## `.transform =` réassigne un type valeur — aucune allocation par image.
## Résout les six volets, les bouche-trous du puits et le maillage du noyau.
##
## Nuls quand la coque est absente (tests) : l'iris est du RENDU, la mécanique du combat
## n'en dépend pas — c'est ce qui permet de piloter le module sans 3D.
func _bind_iris() -> void:
	_shutters.clear()
	_shutter_rest.clear()
	_bore_fillers.clear()
	_core_mesh = null
	_core_instance = null
	if _hull == null:
		return
	for i in IRIS_BLADES:
		var blade := _hull.find_child("Shutter_%02d" % (i + 1), true, false) as Node3D
		if blade == null:
			push_error("[Leviathan] coque sans 'Shutter_%02d' (contrat BRIEF-0083)" % (i + 1))
			continue
		_shutters.append(blade)
		_shutter_rest.append(blade.transform)
	for i in BORE_RINGS:
		var ring := _hull.find_child("Ring_%02d" % (i + 1), true, false) as MeshInstance3D
		if ring != null:
			_bore_fillers.append(ring)
	_core_instance = _heart_node as MeshInstance3D
	if _core_instance != null:
		_core_mesh = _core_instance.mesh

## Pose l'iris pour une ouverture donnée. **Recul PUIS glissement, jamais l'inverse.**
##
## ⚠️ L'ORDRE N'EST PAS UN EFFET DE STYLE, il est mesuré. Glisser avant d'être descendu
## fait entrer le volet dans `Shell_Crescent` : la forge a relevé une marge de 0,0 mm dès
## 300 mm de glissement à recul nul. Les deux temps sont donc strictement séquentiels.
##
## Le recul se fait en −Y local, c'est-à-dire vers le cœur (`Heart` vit à Y = −1,64) et
## donc à l'opposé de la caméra, qui regarde le plan par le dessus. La direction de
## glissement est LUE sur la pose au repos — `normalize(x, 0, z)` — et non écrite en dur :
## un repère se mesure, il ne se convient pas (la leçon de `BRIEF-0045`).
func _pose_iris() -> void:
	if _shutters.is_empty():
		return
	var back := clampf(_shell_open / IRIS_RECOIL_SHARE, 0.0, 1.0) * IRIS_RECOIL
	var slide := clampf((_shell_open - IRIS_RECOIL_SHARE) / (1.0 - IRIS_RECOIL_SHARE), 0.0, 1.0) * IRIS_SLIDE
	for i in _shutters.size():
		var rest := _shutter_rest[i]
		var radial := Vector3(rest.origin.x, 0.0, rest.origin.z)
		# Un volet pile sur l'axe n'a pas de direction radiale : il ne glisse pas.
		radial = radial.normalized() if radial.length_squared() > 0.0001 else Vector3.ZERO
		_shutters[i].transform = Transform3D(rest.basis,
			rest.origin + Vector3(0.0, -back, 0.0) + radial * slide)

## Escamote ce qui bouche le puits, dès que l'iris s'écarte vraiment.
##
## Voir `_bore_fillers` : sans cet escamotage, les volets s'ouvrent sur la masse du noyau
## et l'écran ne montre aucune ouverture.
func _pose_bore() -> void:
	var open := _shell_open > IRIS_BORE_OPEN
	for filler in _bore_fillers:
		filler.visible = not open
	if _core_instance != null:
		_core_instance.mesh = null if open else _core_mesh

func _pose_shell() -> void:
	if _shell_ring != null:
		var basis := _shell_ring_rest.basis * Basis(Vector3.UP, _shell_rotation)
		var opened := _shell_ring_rest.origin + Vector3(0.0, 0.0, tuning.shell_open_offset * _shell_open)
		_shell_ring.transform = Transform3D(basis.scaled(Vector3.ONE * (1.0 + 0.18 * _shell_open)), opened)
	_pose_iris()
	_pose_bore()
	# ⚠️ PAS DE BATTEMENT QUAND LE NOYAU EST ESCAMOTE. `scale` porte sur le NŒUD `Core`, et
	# les six volets en sont les enfants : le battement les ferait respirer de ±22 cm sur
	# leur rayon de 1,86 m, en pleine ouverture, alors qu'il n'anime plus aucun maillage
	# visible. Un mécanisme qui tremble ne se lit plus comme un mécanisme.
	if _heart_node != null and _core_instance != null and _core_instance.mesh == null:
		_heart_node.scale = Vector3.ONE
	elif _heart_node != null:
		# ⚠️ Le cœur ne bat QUE dans le noyau ouvert. Un cœur qui palpite au centre
		# pendant le temps 1 attire l'œil autant que le halo de la plaque à viser, et les
		# deux sont roses : on désignait deux cibles à la fois, dont une intouchable.
		_heart_node.scale = Vector3.ONE * (1.0 + 0.12 * _shell_open * sin(_age * 6.0))
		# Le flux ne s'allume qu'une fois le noyau ouvert, et il bat : dedans, c'est la
		# SEULE chose de cette couleur, donc la seule qui puisse dire « tire ici ».
		if _flux_glow != null:
			var beat := 0.55 + 0.45 * (0.5 + 0.5 * sin(_age * 7.0))
			_flux_glow.albedo_color = Color(1.0, 0.92, 0.72, _shell_open * beat)
			_apply_flux_glow(_shell_open > 0.02)
	if _highlight != null:
		var pulse := 0.5 + 0.5 * sin(_age * 4.0)
		_highlight.albedo_color = Color(0.95, 0.35 + 0.45 * pulse, 0.72 + 0.24 * pulse,
			0.55 + 0.45 * pulse)

## Couche les plaques abattues. `fall_ratio` était calculé depuis le premier jour et
## n'était appliqué à AUCUN maillage — la plaque mourait sans que rien ne bouge.
func _tick_plate_falls(delta: float) -> void:
	for plate in _plates:
		if plate.node == null:
			continue
		var fall := plate.fall_ratio(tuning.shell_break_time)
		if fall <= 0.0:
			continue
		# ⚠️ ELLE TOMBE, ELLE NE RÉTRÉCIT PAS. La mise à l'échelle vers 0,05 faisait
		# « s'évaporer » la plaque sur place au lieu de la faire basculer : à l'écran, une
		# pièce d'armure qui disparaît en fondu ne se lit pas comme une pièce arrachée.
		# Elle pivote maintenant vers l'extérieur autour de sa tangente, s'écarte du corps
		# et part vers l'arrière — puis s'efface une fois hors de la silhouette.
		var rest := plate.rest_transform
		var swing := plate.rest_basis.rotated(plate.fall_axis, fall * PI * 0.75)
		var radial := Vector3(cos(plate.base_angle), 0.0, sin(plate.base_angle))
		plate.node.transform = Transform3D(swing,
			rest.origin + radial * fall * 1.8 + Vector3(0.0, -1.2 * fall * fall, 0.0))
		if fall >= 1.0 and plate.node.visible:
			plate.node.visible = false
	# Les épines tombées suivent le même mouvement, une seconde après la plaque qui les
	# a emportées : on voit la cause, puis l'effet.
	for i in _spine_state.size():
		if _spine_state[i] != Spine.DOWN or i >= _spine_nodes.size():
			continue
		var node := _spine_nodes[i]
		if node == null or not node.visible:
			continue
		var rest := _spine_rest[i]
		node.transform = Transform3D(rest.basis.scaled(Vector3.ONE * 0.92), rest.origin)
		node.visible = false

## Pose le halo du flux sur les maillages du cœur, ou le retire. Au CHANGEMENT seulement :
## réassigner un `material_overlay` par image serait gratuit en pure perte, même raison que
## pour le halo des plaques.
func _apply_flux_glow(lit: bool) -> void:
	if lit == _flux_lit or _heart_node == null:
		return
	_flux_lit = lit
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(_heart_node, meshes)
	for mesh in meshes:
		mesh.material_overlay = _flux_glow if lit else null

## Fait tomber les pièces décoratives. Aucune allocation : `Vector3` et `Transform3D`
## sont des types valeur, et les tableaux sont dimensionnés au montage.
func _tick_debris(delta: float) -> void:
	for i in _debris.size():
		var fall := _debris_fall[i]
		if fall < 0.0 or fall >= 1.0:
			continue
		fall = minf(fall + delta / DEBRIS_FALL_TIME, 1.0)
		_debris_fall[i] = fall
		var node := _debris[i]
		if node == null:
			continue
		var rest := _debris_rest[i]
		var drift := Vector3(rest.origin.x * 1.4, -6.0 * fall * fall, rest.origin.z * 1.4) * fall
		node.transform = Transform3D(
			rest.basis.rotated(Vector3.FORWARD, fall * PI * 1.2).scaled(Vector3.ONE * maxf(1.0 - fall * 0.9, 0.05)),
			rest.origin + drift)
		if fall >= 1.0:
			node.visible = false

func _shed_debris() -> void:
	for i in _debris.size():
		if _debris_fall[i] < 0.0:
			_debris_fall[i] = 0.0
			return

func _set_active_piece(index: int) -> void:
	if index == _active_piece:
		return
	_active_piece = index
	_apply_highlight(index)
	piece_active_changed.emit(index)

## Pose le halo sur les maillages de la plaque active, le retire des autres. Appelé
## seulement au changement : réassigner un `material_overlay` par image serait gratuit
## en pure perte.
func _apply_highlight(index: int) -> void:
	for plate in _plates:
		var lit: Material = _highlight if (plate.index == index and plate.is_up()) else null
		for mesh in plate.meshes:
			mesh.material_overlay = lit

# --- Armement -----------------------------------------------------------------

## Un éventail par plaque **encore debout** : moins de plaques = moins de rideau. Le
## retour de la destruction est immédiat et physique, sans qu'aucun texte ne l'explique.
func _fire_fans(origin: Vector2) -> void:
	if _bullet_manager == null or projectile == null:
		return
	for plate in _plates:
		if not plate.is_up():
			continue
		var a := plate.angle_at(_shell_rotation)
		var muzzle := origin + Vector2(cos(a), sin(a)) * 2.6
		for i in tuning.fan_bullets:
			var t := float(i) / float(maxi(tuning.fan_bullets - 1, 1)) - 0.5
			var spread := deg_to_rad(tuning.fan_spread_deg) * t
			_bullet_manager.spawn_from_data(BulletManager.Team.ENEMY, muzzle,
				Vector2(0.0, -1.0).rotated(spread), projectile)

func _launch_missiles(origin: Vector2) -> void:
	var aim := _player.plane_position if _player != null else origin + Vector2(0.0, -6.0)
	for i in tuning.missile_count:
		var spread := deg_to_rad(20.0 * (i - (tuning.missile_count - 1) * 0.5))
		var direction := (aim - origin).normalized().rotated(spread)
		var missile := TargetableProjectile.make(origin, direction * tuning.missile_speed,
			tuning.missile_health, tuning.missile_hitbox_radius, tuning.missile_turn_rate,
			tuning.missile_damage, Callable(self, "_on_missile_hit").bind(_missiles.size()))
		_missiles.append(missile)
		if _bullet_manager != null:
			_bullet_manager.register_target(missile.target)

func _tick_missiles(delta: float) -> void:
	var chase := _player.plane_position if _player != null else Vector2.ZERO
	for missile in _missiles:
		if not missile.alive:
			continue
		missile.tick(delta, chase)
		if _player != null and missile.reaches(_player.plane_position, 0.25):
			_player.take_contact_damage(missile.damage)
			missile.consume()
	# ⚠️ On ne compacte le tableau que lorsqu'il grossit : `filter()` alloue, et cette
	# boucle tourne à chaque image pendant toute la durée du combat.
	if _missiles.size() > 24:
		var kept: Array[TargetableProjectile] = []
		for missile in _missiles:
			if missile.alive:
				kept.append(missile)
			elif _bullet_manager != null:
				_bullet_manager.unregister_target(missile.target)
		_missiles = kept

# --- Transitions --------------------------------------------------------------

func _enter_phase(next: Phase) -> void:
	_phase = next
	# ⚠️ Les dégâts de ce qui vient d'être détruit ne comptent plus : la jauge repart à
	# plein pour la cible suivante. C'est l'idiome de shmup — « il lui reste une barre » —
	# et c'est ce qui remplace une barre unique qui n'avançait que d'un tiers pour vingt
	# secondes de jeu.
	_local_damage = 0.0
	match next:
		Phase.ARMOR:
			_interlude = 0.0 if _cycle == 0 else 1.2
			# Le corps reste CLOS tout le combat : seul le flux le tue. Les tirs qui
			# ratent une sous-cible ricochent au lieu d'entamer une barre de 20 000 PV
			# qui ferait avancer les phases par les dégâts.
			if _boss != null:
				_boss.vulnerable = false
		Phase.DIVE:
			_dive = Dive.ENTER
			_dive_elapsed = 0.0
			_interlude = 0.0
			_set_active_piece(-1)
			# ⚠️ LE BOSS S'IMMOBILISE. Il dérive de gauche à droite en permanence ; un
			# noyau qui glisse pendant que le chasseur est dedans emporterait le joueur
			# hors du cadre sans qu'il ait rien fait. `drive_toward` à vitesse nulle est
			# la prise de main prévue pour ça (`BossController.drive_toward`).
			if _boss != null:
				_boss.drive_toward(_origin(), 0.0)
			dive_started.emit(_cycle, _origin())
		Phase.DEFEATED:
			release()
			# Le flux est tombé : c'est LA condition de mort. On la traduit en mort du
			# BossController, qui émet `defeated` et déclenche la finale du niveau — le
			# corps clos ne serait jamais mort de lui-même.
			if _boss != null:
				_boss.defeat()
	phase_entered.emit(next)
	_publish_structure()

# --- Dégâts -------------------------------------------------------------------

func _on_plate_hit(damage: float, index: int) -> void:
	if index < 0 or index >= _plates.size():
		return
	var plate := _plates[index]
	if not plate.is_up():
		return
	_account(damage)
	if plate.apply_damage(damage):
		# ⚠️ LA PLAQUE EMPORTE SON ÉPINE. C'est la réponse au « je ne vois pas à quoi
		# servent les antennes » : elles tirent, et casser une plaque en éteint une.
		# La récompense est une menace en moins, pas un septième d'éventail.
		_drop_spine(index)
		_shed_debris()
		piece_destroyed.emit(Phase.ARMOR, index, _piece_world(plate.target.position))
	piece_gauge_changed.emit(index, plate.health_ratio(), plate.is_up())

func _drop_spine(index: int) -> void:
	if index < 0 or index >= _spine_state.size():
		return
	_spine_state[index] = Spine.DOWN
	if index < _spine_beams.size() and _spine_beams[index] != null:
		_spine_beams[index].extinguish()

## Encaissement du flux, PLAFONNE A UN PASSAGE.
##
## ⚠️ TROIS CYCLES NE PEUVENT PAS ETRE GARANTIS PAR UN NOMBRE DE PV, et trois playtests
## l'ont démontré. Les dégâts réellement placés par plongée sont allés de **600 à plus de
## 1200** pour le même joueur à la même puissance — du simple au double. Pour tomber
## toujours au troisième passage il faudrait `flux_health > 2 × 1200` **et**
## `flux_health ≤ 3 × 600` : c'est contradictoire, aucune valeur ne satisfait les deux.
##
## La refonte de la plongée en arène dédiée (`ADR-0025`) a encore doublé la mise : le
## réacteur est droit devant le chasseur, ligne de tir dégagée, on ne le rate plus. Le
## boss est alors tombé en **deux** cycles — la panne exacte que l'invariant 5 nommait,
## « il meurt trop tôt et les cycles ne servent à rien ».
##
## On plafonne donc la casse : **au plus un tiers de la réserve par passage**. Trois
## cycles deviennent le MEILLEUR cas, vrai par construction et non par calibrage ; mieux
## jouer raccourcit chaque plongée sans jamais en supprimer une. Moins bien jouer en
## ouvre une de plus, ce qui reste la sanction juste.
## Un tir a heurté le blindage fermé. Il est CONSOMMÉ, et il le fait savoir.
##
## ⚠️ Aucun dégât, et c'est le point : ce n'est pas une armure à user, c'est une porte à
## trouver. Mais un tir qui disparaît sans rien produire se lit comme un défaut du jeu —
## d'où la gerbe. `damage` est ignoré volontairement.
func _on_shield_hit(_damage: float) -> void:
	if _shield_target == null:
		return
	shield_deflected.emit(GameplayPlane.to_world(_shield_target.position))

func _on_flux_hit(damage: float) -> void:
	if _phase != Phase.DIVE or _dive != Dive.INSIDE or _flux_health <= 0.0:
		return
	var room := maxf(tuning.flux_damage_per_dive() - _dive_damage, 0.0)
	# ⚠️ LE PLAFOND CESSE DE PLAFONNER AU DERNIER CYCLE PRÉVU. `ADR-0026` l'a posé pour
	# empêcher de finir TROP TÔT ; rien ne bornait le nombre de cycles. C'est le filet de
	# sécurité de la terminaison — la vraie cause du combat infini est ailleurs, dans les
	# verrous qui se relevaient entiers (voir `_arm_nodes`).
	if _cycle >= maxi(tuning.cycle_count - 1, 0):
		room = _flux_health
	var applied := minf(damage, room)
	_flux_damage += applied
	if applied <= 0.0:
		# Garde-fou : on ne devrait plus passer ici, la saturation éjectant désormais tout
		# de suite. Reste pour les coups de la même image que celui qui a rempli le quota.
		return
	_dive_damage += applied
	_account(applied)
	_flux_health = maxf(_flux_health - applied, 0.0)
	if _flux_health <= 0.0:
		# Le flux tombe : on ne coupe pas la plongée en deux, l'éjection reste jouée.
		_set_dive(Dive.EJECT)
	elif _dive_damage >= tuning.flux_damage_per_dive():
		# ⚠️ LE QUOTA EST REMPLI : ON SORT. Sans cette ligne, le joueur qui l'atteignait en
		# 3 s attendait les 5 s de `dive_time` devant une jauge GELÉE — ses tirs portaient
		# encore, ils ne comptaient plus, et rien ne le disait. C'est le défaut que
		# l'opérateur a nommé au playtest du 2026-08-27.
		#
		# Ce n'est pas un changement d'équilibrage : `ADR-0026` l'écrivait déjà — « mieux
		# jouer RACCOURCIT chaque plongée sans jamais en supprimer une ». Le plafond par
		# passage garantit toujours les trois cycles ; seule l'attente disparaît.
		#
		# `dive_time` reste la sortie de celui qui n'atteint PAS le quota : rater sa
		# plongée doit coûter du temps, pas l'enfermer.
		_set_dive(Dive.EJECT)

func _on_missile_hit(damage: float, index: int) -> void:
	if index < 0 or index >= _missiles.size():
		return
	_missiles[index].apply_damage(damage)

func _account(damage: float) -> void:
	_local_damage += damage
	_publish_structure()

func _publish_structure() -> void:
	structure_changed.emit(structure_ratio())

func _piece_world(plane: Vector2) -> Vector3:
	return GameplayPlane.to_world(plane)

# --- Lectures -----------------------------------------------------------------

func phase() -> int:
	return _phase

func dive_step() -> int:
	return _dive

func cycle() -> int:
	return _cycle

func shell_rotation() -> float:
	return _shell_rotation

func plates() -> Array[LeviathanPlate]:
	return _plates

func shell_open_ratio() -> float:
	return _shell_open

## Nombre de tourelles-épines encore debout — ce que le joueur voit diminuer.
func spines_up() -> int:
	var up := 0
	for state in _spine_state:
		if state != Spine.DOWN:
			up += 1
	return up

func _plates_up() -> int:
	var up := 0
	for plate in _plates:
		if plate.is_up():
			up += 1
	return up

## Santé de ce qu'on peut casser MAINTENANT, entre 1 et 0.
func structure_ratio() -> float:
	if tuning == null:
		return 1.0
	var total := tuning.flux_health if _phase == Phase.DIVE \
		else tuning.plate_health * float(maxi(_plates.size(), 1))
	if total <= 0.0:
		return 0.0
	return clampf(1.0 - _local_damage / total, 0.0, 1.0)

## Part du combat qui reste, toutes phases confondues.
##
## ⚠️ À NE PAS CONFONDRE avec `structure_ratio()`. Le HUD montre la cible courante — elle
## se remplit à nouveau à chaque bascule. La musique, elle, doit suivre le combat : lui
## donner le ratio local faisait culminer la partition à mi-combat puis redescendre d'un
## cran. Entendu au playtest, lisible au journal (`music 9 -> 8 -> 9`).
func fight_ratio() -> float:
	if tuning == null:
		return 1.0
	# ⚠️ LE FLUX SEUL, ET PLUS TOUTE LA STRUCTURE. « En phase externe du boss, sa barre de
	# vie ne devrait pas descendre » (playtest du 2026-08-27) — et c'est la bonne règle :
	# l'armure REPOUSSE à chaque cycle, donc la casser n'est pas un progrès. La compter
	# faisait descendre la jauge pendant le temps 1 puis la faisait stagner pendant que le
	# joueur frappait la seule chose qui compte vraiment.
	#
	# Avec le plafond d'`ADR-0026`, une plongée retire au plus un tiers du flux : la jauge
	# tombe donc par tiers, une marche par phase interne. C'est exactement ce que
	# l'opérateur décrit — « la barre de vie générale du boss descendra de 33 % à chaque
	# phase interne ».
	#
	# Elle ne remonte toujours jamais (`ADR-0023`) : `_flux_damage` ne fait que croître.
	var total := tuning.flux_health
	return clampf(1.0 - _flux_damage / total, 0.0, 1.0) if total > 0.0 else 1.0

## Publie l'état de toutes les jauges. Le niveau l'appelle après `begin()`, quand le HUD
## est prêt : interroger avant afficherait des pastilles éteintes sur un boss intact.
##
## ⚠️ Seulement pendant le temps 1. Les publier dans le noyau RALLUME une rangée que le
## niveau vient d'éteindre : `set_boss_limb()` rend visible la pastille qu'il met à jour.
func publish_gauges() -> void:
	if _phase == Phase.ARMOR:
		for plate in _plates:
			piece_gauge_changed.emit(plate.index, plate.health_ratio(), plate.is_up())
	_publish_structure()

func _release_plates() -> void:
	if _bullet_manager == null:
		return
	for plate in _plates:
		plate.target.enabled = false
		_bullet_manager.unregister_target(plate.target)

## Retire TOUTES les cibles du gestionnaire. Sans cela, un boss vaincu ou un remontage
## laisse des cibles actives, callback vivant, position figée : un mur invisible qui
## mange les balles du joueur.
func release() -> void:
	for beam in _spine_beams:
		if beam != null:
			beam.extinguish()
	if _bullet_manager == null:
		return
	_release_plates()
	for missile in _missiles:
		missile.target.enabled = false
		_bullet_manager.unregister_target(missile.target)
	_missiles.clear()
	for node in _node_targets:
		node.enabled = false
		_bullet_manager.unregister_target(node)
	_node_targets.clear()
	if _shield_target != null:
		_shield_target.enabled = false
		_bullet_manager.unregister_target(_shield_target)
	if _flux_target != null:
		_flux_target.enabled = false
		_bullet_manager.unregister_target(_flux_target)
