class_name CortegeCitadel
extends Node3D
## La Citadelle de Défense : le verrou de mi-parcours du Long Cortège.
##
## En une phrase, et c'est le cahier des charges entier :
##
##     « Ce gigantesque vaisseau m'a fermé la route ; j'ai saboté son verrou défensif
##      pour continuer. »
##
## ⚠️ CE N'EST PAS UN BOSS, ET C'EST LA CONTRAINTE QUI PRIME SUR TOUTES LES AUTRES. Pas de barre
## de vie, pas de cycles, pas de rideau de projectiles. Ce qui l'en distingue n'est pas une
## intention mais deux chiffres bornés par `CortegeTuning` : le temps de tir qu'elle demande, et
## celui de la séquence entière. Le niveau 1 a déjà deux boss ; un troisième déguisé en décor
## serait le pire des deux mondes.
##
## ⚠️ ET L'ARRÊT DU DÉFILEMENT N'EST PAS UNE MISE EN SCÈNE, C'EST CE QUI REND LA SÉQUENCE
## GÉOMÉTRIQUEMENT POSSIBLE. À 2,4 u/s, quarante secondes de combat vaudraient 96 m de coque —
## un cinquième du vaisseau — quand la fenêtre libre entre la fosse de `s = 228` et le socle de
## `Turret_07` en fait dix-neuf. Le survol freine, s'immobilise, et c'est cet arrêt qui fabrique
## l'arène : le mur en haut de l'écran, le joueur dessous.
##
## ## Ce que ce fichier est, et ce qu'il n'est pas encore
##
## C'est le **lot 1** du plan : la BOUCLE, en boîtes grises. « Ne pas passer du temps sur les
## greebles ou les effets tant que la boucle complète n'est pas jouable de bout en bout »
## (opérateur). La silhouette est le lot 2, la lecture sans HUD le lot 3, l'ouverture jouée le
## lot 4. Une citadelle magnifique dont le verrou ne s'ouvre pas est un échec complet ; une
## boîte grise qui s'ouvre correctement est un succès à habiller.

## ⚠️ SEPT ÉTATS ET NON QUATRE, PARCE QUE TROIS D'ENTRE EUX NE SE VOIENT PAS ENCORE. `ONE_RELAY`
## et `CORE_DEAD` ne changent rien au jeu aujourd'hui — mais ils sont les deux instants que le
## lot 3 doit rendre lisibles (un conduit qui s'éteint, une surcharge), et les découvrir plus
## tard demanderait de rouvrir la machine à états au moment où on ne veut plus y toucher.
enum State { APPROACH, LOCKED, ONE_RELAY, SHIELD_DOWN, CORE_DEAD, OPENING, CLEARED }

# --------------------------------------------------------------------------
# LA GÉOMÉTRIE — LE KIT DE LA FORGE, POSÉ SUR DES COTES RELEVÉES
# --------------------------------------------------------------------------
#
# ⚠️ LES BOÎTES ONT DISPARU, ET LE LOT 1 A EU RAISON DE LES ÉCRIRE. « Ne pas passer de temps sur
# les greebles tant que la boucle n'est pas jouable de bout en bout » : la boucle a été jouée en
# boîtes, la règle s'est lue sans un mot de HUD, et le chronomètre a refusé le dimensionnement.
# Tout ça a été acquis AVANT que la forme existe. Ce fichier ne porte plus que la POSE.
#
# Toutes les cotes sont LOCALES au nœud, dont l'origine est posée à la station
# `tuning.citadel_station` sur le repère du tronçon. Deux conventions, et les confondre a déjà
# coûté un niveau entier de batteries en miroir :
#
#   * `s` se compte depuis la PROUE et croît vers la poupe ; le `z` local DÉCROÎT d'autant.
#     Un décalage `ds` vers la poupe s'écrit donc `z = -ds` ;
#   * les `y` sont ceux de la PEAU, relevés dans `build_long_cortege.py` : pont intérieur
#     −4,30, pont médian −4,99, fond du canal de l'artère −4,58.
#
# ⚠️ ET LES DEUX PLAFONDS D'`ADR-0041` DÉCIDENT DE LA SILHOUETTE, PAS LE GOÛT. Le décor inerte
# ne monte pas au-dessus de −3,00 ; ce qu'on peut détruire va jusqu'à −2,40. C'est pour ça que
# le NOYAU est le point le plus haut de la citadelle et les bastions sa masse : le seul volume
# autorisé à culminer est celui qu'on peut tirer.

## Le kit livré par `BRIEF-0096`. ⚠️ CHARGÉ AU RUNTIME ET NON `preload` : le niveau doit rester
## jouable et mesurable si le binaire manque, comme la coque elle-même. Sans lui, le verrou garde
## sa boucle — le mur ferme toujours la route — et le journal dit qu'il est NU.
const KIT_PATH := "res://assets/imported/models/backgrounds/citadel_kit.glb"

## Le budget vertical, tranché (`C1` du plan, voie « la hauteur par le creux »).
##
## ⚠️ LE BRIEF DEMANDAIT DES BASTIONS DE 1,5 À 2,5 m ET IL N'Y AVAIT QUE 1,30. Trois issues
## étaient ouvertes : réécrire les cotes dans le budget réel, obtenir la hauteur par le CREUX,
## ou amender `ADR-0041`. La deuxième est retenue — c'est celle que le lot B3 a déjà démontrée
## sur cette coque (quatre fosses de 1,55 m, 384 triangles, aucun plafond touché).
##
## ⚠️ LA TRANCHÉE ELLE-MÊME N'EST PAS ENCORE CREUSÉE, et le test d'acceptation a été tenu SANS
## elle : la planche de recette du kit passe le noir et blanc sur une coque plate. Elle affine
## donc la BASE des bastions — leur pied et leur ombre —, elle ne décide plus de la lecture.
## Cette constante existe pour que le jour où on la creuse, l'assise du bastion soit déjà juste.
const MOAT_DEPTH := 1.55

## Le plafond du décor inerte et celui du gameplay (`ADR-0041`), recopiés depuis `CortegeFlyby`
## pour que ce fichier se lise seul — le test les compare aux originaux.
const DECOR_CEILING_Y := CortegeFlyby.CEILING_Y
const GAMEPLAY_CEILING_Y := CortegeFlyby.GAMEPLAY_CEILING_Y

## LA PORTE — la face avant, celle qui ferme.
##
## ⚠️ ELLE COUVRE TOUT LE PLAN DE VOL ET NON LA SEULE COQUE, ET C'EST UNE DÉCISION. La coque
## fait 28 m de large ; le plan de vol, une fois la parallaxe appliquée, en couvre davantage.
## Une barrière arrêtée au bordé laisserait le joueur la CONTOURNER par le vide — et la séquence
## deviendrait facultative, ce qui la vide de son sens (« il ferme physiquement la route »).
## ⚠️ ET LE SURPLOMB A SON PORTEUR DEPUIS `BRIEF-0096` : `citadel_pylon` descend du bout de la
## poutre jusqu'à la lisse d'épaule. Un mur invisible est la même injustice qu'une tourelle qu'on
## croit pouvoir raser et qui traverse.
const GATE_HALF_X := 17.2
const GATE_HALF_S := 0.60
## ⚠️ L'ASSISE PLONGE DANS LA COQUE, ELLE NE SE POSE PAS DESSUS. Le bordé n'est pas plat : quatre
## plans différents sous une seule pièce de 34 m. Une poutre assise sur la cote la plus haute
## flotterait partout ailleurs — au-dessus du vide, en silence.
const GATE_BASE_Y := -6.60
const GATE_TOP_Y := DECOR_CEILING_Y

## LES BASTIONS — la masse, sur le pont médian. Deux, en miroir : `T1` autorise la symétrie POUR
## UN ÉVÉNEMENT, parce qu'elle est ce qui fait lire « gauche + droite → centre » en une seconde.
const BASTION_X := Vector2(6.90, 11.40)
const BASTION_S := Vector2(-0.40, 6.00)
## ⚠️ −6,50 ET NON −6,60 : c'est le fond de la tranchée, la cote pour laquelle la forge a taillé
## la pièce. Le bastion mesure 2,90 m et culmine donc à −3,60, sous le plafond du décor.
const BASTION_BASE_Y := -6.50
const BASTION_TOP_Y := -3.60

## LA COURONNE — ce qui monte jusqu'au plafond du décor et fait la silhouette.
const CROWN_X := Vector2(7.40, 10.00)
const CROWN_S := Vector2(1.60, 5.40)

## LE PORTIQUE — le porteur du surplomb. ⚠️ IL VA À x 13,58 ET NON 15,60, et c'est la forge qui a
## corrigé le brief : la lisse d'épaule est à 13,88, donc EN DEDANS de l'emprise demandée. Arrêté
## plus au large, le portique flotterait — le défaut qu'il existe pour corriger.
const PYLON_BASE_Y := -7.65

## LES RELAIS — sur le pont intérieur, contre le flanc interne des bastions.
const RELAY_X := 6.20
const RELAY_S := 1.40
const RELAY_BASE_Y := -4.30
## L'enveloppe MESURÉE de la pièce du kit (x 5,40 à 7,00 · y 0 à 1,90 · s +0,60 à +2,20).
const RELAY_SIZE := Vector3(1.60, 1.90, 1.60)
## ⚠️ PLUS GÉNÉREUX QUE SA GÉOMÉTRIE, comme la tourelle légère. Le relais est ce qu'on doit
## trouver, pas ce qu'on doit viser au millimètre : une hitbox fidèle en ferait une corvée de
## précision là où la séquence demande de comprendre une règle.
const RELAY_RADIUS := 1.10

## LE CONDUIT — ce qui court du relais vers l'axe. ⚠️ C'EST LA PIÈCE QUI DIT LA RÈGLE SANS
## ÉMISSIF : « ceci alimente cela », en géométrie, donc au test noir et blanc. Il partage
## l'origine du relais, à son pied.
const CONDUIT_TOP := 0.62

## LE NOYAU — sur l'axe, assis au fond de l'artère, et le point le plus haut de la citadelle.
## ⚠️ IL PREND SON ASSISE 28 cm PLUS BAS QUE LES RELAIS et culmine 1,20 m plus haut : il sort de
## l'épine du vaisseau. C'est ce qui le désigne comme le centre sans un mot de HUD.
const CORE_S := 3.40
const CORE_BASE_Y := -4.58
const CORE_SIZE := Vector3(2.40, 2.18, 2.40)
const CORE_RADIUS := 1.50

## LE BOUCLIER — le panneau qui refuse les tirs tant que les deux relais vivent.
##
## ⚠️ SON ARÊTE HAUTE EST EXACTEMENT AU SOMMET DU NOYAU, et il se range au plafond du GAMEPLAY et
## non à celui du décor. La règle d'`ADR-0041` protège « ce qui masquerait le combat SANS JAMAIS
## POUVOIR ÊTRE TOUCHÉ » : le bouclier, lui, se touche — c'est même toute sa fonction, et chaque
## impact doit se voir sur lui. La seconde moitié de la règle ne s'applique donc pas à lui, comme
## elle ne s'applique pas à une tourelle.
const SHIELD_BASE_Y := -3.90
const SHIELD_S := 2.10
const SHIELD_TINT := Color(0.30, 0.72, 1.00, 0.28)

## LES TOURELLES LÉGÈRES DU VERROU — quatre, deux par bord, SUR DEUX PONTS.
##
## ⚠️ ELLES ÉTAIENT QUATRE SUR LE SEUL PONT DU BASTION, ET LA COURONNE LES EN A CHASSÉES. La
## pièce livrée occupe `s +1,60 à +5,40` sur ce pont : le socle léger fait 1,04 m de rayon, donc
## les DEUX ne peuvent pas tenir en avant d'elle (il faudrait `s ≤ 0,56`), et le bastion est trop
## court pour en loger une derrière. La seconde descend donc sur le pont intérieur — deux ponts
## au lieu d'un empilement, ce qui vaut mieux en composition.
##
## ⚠️ ET ELLES SONT VERS L'AVANT, CE QUI N'EST PAS UNE COMPOSITION. Une pièce posée trop en
## arrière s'immobilise hors du plan de vol ET hors de sa propre fenêtre de 14 unités : elle ne
## s'engagerait JAMAIS, sans une ligne au journal. C'est le défaut muet que
## `test_cortege_citadel.gd` garde.
##
## ⚠️ CELLE DU PONT INTÉRIEUR EST DERRIÈRE LE CONDUIT, à 0,42 m de sa dernière station : posée
## devant, son socle se serait couché sur le caisson.
## Format : [x, ds, assise].
const GUARDS: Array = [
	[9.20, 0.40, BASTION_TOP_Y],
	[4.60, 3.30, RELAY_BASE_Y],
]

## Part de l'ouverture passée sur la MORT DU NOYAU avant que les mécanismes ne bougent.
## ⚠️ UN SEUL RÉGLAGE POUR DEUX TEMPS : `citadel_open_time` dit ce que coûte l'ouverture entière.
## En faire deux réglages laisserait dériver la somme sans que l'invariant 9 ne la voie.
const CORE_BEAT_SHARE := 0.4

signal state_changed(state: State)
## Le mur a ATTEINT sa station et le survol est à l'arrêt.
##
## ⚠️ UN SIGNAL À PART, ET NON `state_changed(LOCKED)`, PARCE QUE `LOCKED` EST SAUTABLE. Les
## relais deviennent tirables à l'instant où le freinage commence : un joueur qui en abat un
## pendant ces cinq secondes fait passer la machine en `ONE_RELAY` avant que le mur ne soit en
## place, et l'état `LOCKED` n'est alors JAMAIS traversé. Tout ce qui écoutait « le mur est
## arrivé » se serait tu — journal horodaté compris, celui-là même sur lequel repose le critère
## « sous 45 s ». Le mur annonce donc son arrivée lui-même, quoi que fasse le combat.
signal wall_locked()
signal relay_destroyed(part: CitadelPart)
signal core_destroyed(part: CitadelPart)
## La route est praticable. ⚠️ C'EST CE SIGNAL, ET LUI SEUL, QUI REND LE SURVOL — pas la mort du
## noyau : entre les deux il y a l'ouverture, et une route rendue trop tôt ferait traverser un
## mur encore debout.
signal cleared()
## Une tourelle du verrou est tombée. Elle vaut ce que vaut une tourelle légère, et c'est le
## niveau qui le sait.
signal turret_destroyed(turret: CortegeTurret)

var tuning: CortegeTuning
var section: int = 0

var _state: State = State.APPROACH
var _bullets: BulletManager = null
var _player: PlayerFighterController = null
var _vfx: VFXManager = null

var _gate: Node3D = null
var _shield: MeshInstance3D = null

var _relays: Array[CitadelPart] = []
var _core: CitadelPart = null
var _turrets: Array[CortegeTurret] = []

var _relays_down: int = 0
var _open_clock: float = 0.0
var _resume_clock: float = 0.0
## L'horloge de la séquence, pour que le journal MESURE au lieu de raconter. Le survol n'est pas
## horodaté (dette du backlog) : sans elle, « sous 45 s » ne se vérifie sur aucune trace.
var _clock: float = 0.0
var _armed: bool = false
## Le mur a ATTEINT sa station. ⚠️ SÉPARÉ DE L'ÉTAT DE COMBAT, ET C'EST UN DÉFAUT CORRIGÉ AVANT
## D'AVOIR ÉTÉ JOUÉ. Les relais deviennent tirables à l'instant précis où le freinage commence :
## un joueur qui en abat un pendant ces cinq secondes faisait quitter `APPROACH`, et la vitesse
## tombait alors à zéro d'un coup — le vaisseau s'arrêtait net, deux unités trop haut, sur une
## porte que le joueur ne pouvait plus atteindre. Le mur continue donc son approche quoi que
## fasse le combat : c'est la géométrie qui dit quand il est en place, pas l'état des relais.
var _locked: bool = false
## La face avant, dans le plan de jeu. Relue à chaque image : la caméra bouge (secousses,
## recadrages), donc figer un décalage le rendrait faux au premier tremblement.
var _wall_a: Vector2 = Vector2.ZERO
var _wall_b: Vector2 = Vector2.ZERO
var _wall_y: float = 1000.0
## ⚠️ TANT QUE LE MUR N'A PAS ÉTÉ RELEVÉ, IL N'EXISTE PAS. Sans ce drapeau, la première image
## physique verserait une capsule de 90 cm posée à l'ORIGINE du plan — c'est-à-dire exactement
## là où le chasseur naît. Le joueur serait dégagé d'un mur invisible au premier dixième de
## seconde du niveau, une fois sur deux selon l'ordre des deux boucles.
var _measured: bool = false


## ⚠️ LA STRUCTURE SE MONTE ICI, LES VOLUMES DANS `_ready()`, ET LA FRONTIÈRE EST DÉLIBÉRÉE.
## `_ready()` ne tourne QUE dans un arbre de scène : tout ce qui décide d'une POSITION —
## les bouts de la porte, les relais, le noyau, les tourelles — doit donc exister avant, sinon
## rien de tout ça n'est vérifiable sans jouer quarante secondes de survol. Ce qui reste à
## `_ready()` est ce qui ne décide de rien : des boîtes.
static func make(p_tuning: CortegeTuning) -> CortegeCitadel:
	var citadel := CortegeCitadel.new()
	citadel.tuning = p_tuning
	citadel.section = section_of(p_tuning)
	for side in [-1.0, 1.0]:
		var nom := "Star" if side > 0.0 else "Port"
		var relay := CitadelPart.make(CitadelPart.Role.RELAY, p_tuning.citadel_relay_health,
			RELAY_RADIUS, RELAY_SIZE.y * 0.5, p_tuning.citadel_relay_score)
		relay.name = "Relay%s" % nom
		relay.position = relay_local(side)
		citadel.add_child(relay)
		citadel._relays.append(relay)
		for index in GUARDS.size():
			var turret := CortegeTurret.make(p_tuning, citadel.section,
				CortegeTuning.TurretScale.LIGHT)
			turret.serial = citadel._turrets.size()
			turret.name = "GuardTurret%02d" % citadel._turrets.size()
			turret.position = guard_local(side, index)
			citadel.add_child(turret)
			citadel._turrets.append(turret)
	citadel._core = CitadelPart.make(CitadelPart.Role.CORE, p_tuning.citadel_core_health,
		CORE_RADIUS, CORE_SIZE.y * 0.5, p_tuning.citadel_core_score)
	citadel._core.name = "Core"
	citadel._core.position = core_local()
	citadel.add_child(citadel._core)
	# ⚠️ INVULNÉRABLE DÈS SA NAISSANCE, et non « rendu invulnérable au montage ». Un noyau né
	# vulnérable est touchable pendant la trame qui sépare sa création de son câblage, et ce
	# genre de fenêtre d'une image ne se reproduit jamais quand on la cherche.
	citadel._core.set_vulnerable(false)
	return citadel

# --- La pose, en fonctions PURES ---------------------------------------------
#
# ⚠️ ELLES EXISTENT POUR QUE LE MONTAGE ET LES TESTS LISENT LA MÊME TABLE. Une position recopiée
# dans un test vérifie le test, pas le jeu — et c'est le défaut qu'`ADR-0024` a payé, où
# l'invariant se comparait à lui-même pendant que le vrai réglage dérivait.

static func gate_end_local(side: float) -> Vector3:
	return Vector3(side * GATE_HALF_X, GATE_TOP_Y, 0.0)

static func relay_local(side: float) -> Vector3:
	return Vector3(side * RELAY_X, RELAY_BASE_Y, -RELAY_S)

static func core_local() -> Vector3:
	return Vector3(0.0, CORE_BASE_Y, -CORE_S)

## Où siège une tourelle de garde. ⚠️ CHAQUE ENTRÉE PORTE SON PROPRE PONT : les deux ne sont pas
## à la même hauteur, et prendre l'assise de l'une pour l'autre poserait la seconde 70 cm au-dessus
## du vide — le défaut de la contremarche de chine, réintroduit par la bande.
static func guard_local(side: float, index: int) -> Vector3:
	var entry: Array = GUARDS[index]
	return Vector3(side * float(entry[0]), float(entry[2]), -float(entry[1]))

## Où une pièce de la citadelle se trouve DANS LE MONDE après `travelled` unités de survol.
##
## ⚠️ ELLE REFAIT LA COMPOSITION DE L'ARBRE, ET ELLE LA REFAIT AVEC LA FONCTION DU SURVOL. Le
## moteur ne rend `global_position` que pour un nœud DANS l'arbre de scène : hors de lui il
## renvoie l'identité, en silence si l'on ne lit pas le journal. Une citadelle qui lirait sa
## position dans l'arbre serait donc invérifiable sans jouer quarante secondes de défilement —
## et c'est précisément la pose qui décide si une pièce s'immobilise dans le plan de vol ou dix
## unités au-dessus, hors de sa propre fenêtre, muette pour toujours.
##
## ⚠️ ET ELLE N'INVENTE AUCUNE ARITHMÉTIQUE : `CortegeFlyby.section_z_at()` place le tronçon,
## `local_z_in_section()` place la citadelle dedans, `local.z` place la pièce dans la citadelle.
## Ce sont les trois transformations que le graphe de scène compose, écrites une fois.
static func piece_world(p_tuning: CortegeTuning, local: Vector3, travelled: float) -> Vector3:
	var section_z := CortegeFlyby.section_z_at(section_of(p_tuning), p_tuning.section_length,
		travelled)
	return Vector3(local.x, local.y, section_z + local_z_in_section(p_tuning) + local.z)

## Le tronçon qui porte le verrou. ⚠️ PURE ET STATIQUE : c'est elle qui décide sous quel nœud la
## citadelle se monte, et se tromper de tronçon la poserait cent mètres plus loin, en silence.
static func section_of(p_tuning: CortegeTuning) -> int:
	if p_tuning.section_length <= 0.001:
		return 0
	return clampi(int(p_tuning.citadel_station / p_tuning.section_length), 0,
		maxi(p_tuning.section_count - 1, 0))

## Le `z` local, dans le repère du TRONÇON, où la citadelle se pose.
static func local_z_in_section(p_tuning: CortegeTuning) -> float:
	var origine := float(section_of(p_tuning)) * p_tuning.section_length
	return -(p_tuning.citadel_station - origine)

## ⚠️ PAS DE CAMÉRA ICI, ET C'EST LA MÊME RAISON QUE POUR LA POSE : `Camera3D.global_position`
## ne répond que dans l'arbre. L'œil est donné à chaque image par le niveau, qui, lui, y est.
func setup(bullet_manager: BulletManager, player: PlayerFighterController,
		vfx: VFXManager) -> void:
	_bullets = bullet_manager
	_player = player
	_vfx = vfx
	for relay in _relays:
		relay.setup(bullet_manager, vfx)
		relay.destroyed.connect(_on_relay_destroyed)
	_core.setup(bullet_manager, vfx)
	_core.destroyed.connect(_on_core_destroyed)
	_core.deflected.connect(_on_core_deflected)
	for turret in _turrets:
		turret.setup(bullet_manager, player, vfx)
		turret.destroyed.connect(_on_turret_destroyed)

func _ready() -> void:
	_build_mass()

# ==========================================================================
# LE MONTAGE — des boîtes, et rien d'autre (lot 1)
# ==========================================================================

## Va chercher les formes dans le kit et les pose.
##
## ⚠️ LA TABLE VIENT DU RAPPORT DE FORGE, MESURÉE SUR LE BINAIRE — pas des constantes du script
## qui l'a produit. Chaque pièce est centrée en Z sur son origine au micron, et son X de coque
## est CUIT dans la géométrie : bâbord et tribord reçoivent donc **exactement la même
## translation**, pour seule différence un yaw de π. Il n'y a aucune arithmétique de côté ici, et
## c'est ce qui rend l'assemblage indésynchronisable.
##
## ⚠️ ET LE YAW DE π ENVOIE `(x, z)` SUR `(−x, −z)`. Une pièce dont la boîte ne serait pas centrée
## en Z se retrouverait à bâbord DÉCALÉE LE LONG DU VAISSEAU de deux fois son excentricité — un
## bastion à `s + 6` d'un bord et à `s − 6` de l'autre. Aucune boîte englobante, aucun compte de
## triangles ne le verrait : il faudrait jouer la séquence et regarder les deux bords en même
## temps. La forge l'a vérifié sur les huit ; ce commentaire est là pour que personne ne le
## défasse.
##
## Format : [nom dans le kit, assise Y, décalage `ds`, en miroir ?].
const PIECES: Array = [
	["citadel_gate", GATE_BASE_Y, 0.00, false],
	["citadel_pylon", PYLON_BASE_Y, 0.00, true],
	["citadel_bastion", BASTION_BASE_Y, 2.80, true],
	["citadel_crown", BASTION_TOP_Y, 3.50, true],
	["citadel_conduit", RELAY_BASE_Y, RELAY_S, true],
]

func _build_mass() -> void:
	var kit := _open_kit()
	if kit == null:
		return
	for entry in PIECES:
		var nom := String(entry[0])
		var source := kit.get_node_or_null(nom) as MeshInstance3D
		if source == null:
			push_error("[Citadel] pièce de kit manquante : %s" % nom)
			continue
		for side in ([-1.0, 1.0] if bool(entry[3]) else [1.0]):
			var piece := MeshInstance3D.new()
			piece.name = "%s%s" % [nom, "Port" if side < 0.0 else ""]
			piece.mesh = source.mesh
			piece.position = Vector3(0.0, float(entry[1]), -float(entry[2]))
			piece.rotation.y = 0.0 if side > 0.0 else PI
			piece.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(piece)
			if nom == "citadel_gate":
				_gate = piece
	# ⚠️ LES DEUX PIÈCES QUI MEURENT PRENNENT LEUR FORME ICI, ET CHACUNE S'APPROPRIE SA LUEUR.
	# Deux relais qui partageraient le matériau du `.glb` s'éteindraient ensemble — le piège que
	# les cinq bulbes d'épine cuits dans la coque rendaient inévitable.
	var relay_mesh := kit.get_node_or_null("citadel_relay") as MeshInstance3D
	for i in _relays.size():
		# `_relays[0]` est BÂBORD — voir `_build_parts` : l'ordre de la boucle EST le côté.
		_relays[i].mount(relay_mesh, -1.0 if i == 0 else 1.0, RELAY_X)
	# ⚠️ LE NOYAU EST SUR L'AXE : sa géométrie est déjà centrée en x, il n'a rien à retrancher.
	_core.mount(kit.get_node_or_null("citadel_core") as MeshInstance3D)
	_build_shield(kit)
	kit.queue_free()

## Ouvre le kit. ⚠️ SON ABSENCE NE CASSE PAS LE NIVEAU, ET ELLE SE DIT. Le binaire vient de la
## forge ; sans lui le verrou garde sa boucle entière — le mur ferme toujours la route, les
## relais tombent, le noyau s'ouvre — et seule la forme manque. Un `preload` sur un fichier
## absent est une erreur de COMPILATION en GDScript : le niveau entier cesserait de se monter
## pour une silhouette.
func _open_kit() -> Node:
	if not ResourceLoader.exists(KIT_PATH):
		print("[Citadel] verrou NU — %s absent" % KIT_PATH.get_file())
		return null
	var packed: PackedScene = load(KIT_PATH) as PackedScene
	if packed == null:
		push_error("[Citadel] kit illisible : %s" % KIT_PATH)
		return null
	return packed.instantiate()

## Le bouclier. ⚠️ C'EST UN VOLUME, PAS UNE LUEUR. Le joueur doit voir que son tir s'arrête
## QUELQUE PART, sur une surface qui a une place : un halo posé sur le noyau se lirait comme une
## propriété du noyau — donc comme « il encaisse » —, et non comme « quelque chose le protège ».
##
## ⚠️ SA TEINTE EST PROVISOIRE, ET SA REMPLAÇANTE EST DÉJÀ AU DÉPÔT. `TEX-0015` est livrée et
## acceptée : elle rendra le panneau MAGENTA au LOT 3, de la même famille que le noyau qu'il
## protège. C'est alors la STRUCTURE — une maille fixe contre un point net qui bouge — qui devra
## les séparer, et ça ne s'est encore vu sur aucune capture.
func _build_shield(kit: Node) -> void:
	var source := kit.get_node_or_null("citadel_shield") as MeshInstance3D
	if source == null:
		push_error("[Citadel] pièce de kit manquante : citadel_shield")
		return
	_shield = MeshInstance3D.new()
	_shield.name = "Shield"
	_shield.mesh = source.mesh
	_shield.position = Vector3(0.0, SHIELD_BASE_Y, -SHIELD_S)
	_shield.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var mat := StandardMaterial3D.new()
	mat.albedo_color = SHIELD_TINT
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.emission_enabled = true
	mat.emission = Color(SHIELD_TINT.r, SHIELD_TINT.g, SHIELD_TINT.b)
	mat.emission_energy_multiplier = 0.9
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_shield.material_override = mat
	add_child(_shield)
	# ⚠️ IL SUIT L'ÉTAT ET NON L'ORDRE DE MONTAGE. Le bouclier peut naître APRÈS que les deux
	# relais soient tombés — un `--cortege-from` posé au mauvais endroit, un banc de mesure — et
	# un rideau devant un noyau touchable apprendrait au joueur l'inverse de la règle.
	_shield.visible = _core != null and not _core.is_vulnerable()

# ==========================================================================
# LA BOUCLE
# ==========================================================================

## Un pas du verrou. ⚠️ APPELÉ PAR LE NIVEAU, comme les points d'ancrage : quinze pièces qui
## traiteraient chacune leur image, c'est un ordre de passage indéfini — alors que le bouclier
## doit tomber AVANT que le noyau ne prenne le premier tir de la même trame.
func tick(delta: float, travelled: float, eye: Vector3) -> void:
	_measure_wall(travelled, eye)
	if _armed:
		_clock += delta
	for relay in _relays:
		var w := piece_world(tuning, relay.position, travelled) + Vector3(0.0, relay.lift, 0.0)
		relay.tick(w, GameplayPlane.aim_point_of(w, eye))
	var wc := piece_world(tuning, _core.position, travelled) + Vector3(0.0, _core.lift, 0.0)
	_core.tick(wc, GameplayPlane.aim_point_of(wc, eye))
	for turret in _turrets:
		var wt := piece_world(tuning, turret.position, travelled) \
			+ Vector3(0.0, turret.hit_lift(), 0.0)
		turret.tick(delta, wt, GameplayPlane.aim_point_of(wt, eye))
	_advance(delta)

## Relève où la face avant se projette dans le plan. ⚠️ LES DEUX BOUTS, ET NON LE CENTRE : le mur
## fait 34 m de large et la parallaxe n'est pas la même à ses deux extrémités. Un segment déduit
## du centre serait juste au milieu et faux aux bords, c'est-à-dire exactement là où le joueur
## cherche à passer.
func _measure_wall(travelled: float, eye: Vector3) -> void:
	_wall_a = GameplayPlane.aim_point_of(piece_world(tuning, gate_end_local(-1.0), travelled), eye)
	_wall_b = GameplayPlane.aim_point_of(piece_world(tuning, gate_end_local(1.0), travelled), eye)
	_wall_y = (_wall_a.y + _wall_b.y) * 0.5
	_measured = true

func _advance(delta: float) -> void:
	_advance_wall()
	match _state:
		State.APPROACH:
			# ⚠️ LE CONTOURNEMENT SE TESTE AVANT L'ARMEMENT, ET L'ORDRE EST CE QUI EMPÊCHE LE
			# JOURNAL DE MENTIR. Un mur déjà passé satisfait AUSSI la condition de freinage : en
			# armant d'abord, la trace annonçait « route fermée droit devant » sur une porte
			# franchie depuis cent mètres. Un journal qui raconte le contraire de ce qui se
			# passe coûte plus cher qu'un journal muet.
			# ⚠️ UN SURVOL QUI DÉMARRE EN AVAL DU VERROU L'A DÉJÀ FRANCHI, et sans cette ligne
			# il se figerait pour toujours. `--cortege-from=4` pose le survol cent mètres après
			# la citadelle : le mur est alors DERRIÈRE le joueur, sa hauteur de plan est
			# négative, la condition d'arrêt est donc vraie — et le verrou s'arme sur une porte
			# qu'on ne peut plus ni voir ni tirer. Le survol ne repartirait jamais, sans une
			# erreur. Un outil de vérification qui gèle le jeu est pire que pas d'outil.
			if _wall_y < GameplayPlane.BOUNDS.position.y:
				_log("verrou déjà en aval du départ — la route est réputée franchie")
				_enter(State.CLEARED)
			# Le mur en place fait passer `LOCKED` depuis `_advance_wall()` : rien à faire ici.
		State.CORE_DEAD:
			_open_clock += delta
			if _open_clock >= tuning.citadel_open_time * CORE_BEAT_SHARE:
				_enter(State.OPENING)
		State.OPENING:
			_open_clock += delta
			if _open_clock >= tuning.citadel_open_time:
				_enter(State.CLEARED)
		State.CLEARED:
			_resume_clock = minf(_resume_clock + delta, tuning.citadel_resume_time)
		_:
			pass

## L'approche du mur, et elle ne dépend d'aucun état de combat.
func _advance_wall() -> void:
	if _locked or _state == State.CLEARED:
		return
	# ⚠️ UN MUR DÉJÀ SOUS LE PLAN N'EST PAS « ARRIVÉ », IL EST PASSÉ. Le verrouiller ici
	# arrêterait un survol démarré en aval de la citadelle (`--cortege-from=4`) sur une porte
	# qu'on ne peut plus ni voir ni tirer. C'est l'état `APPROACH` qui traite ce cas.
	if _wall_y < GameplayPlane.BOUNDS.position.y:
		return
	# ⚠️ IL S'ARME QUAND LE MUR ENTRE DANS LE FREINAGE, pas au montage : l'horloge de la séquence
	# doit mesurer la séquence, pas les deux minutes de survol qui la précèdent.
	if not _armed and _wall_y <= tuning.citadel_wall_plane_y + tuning.citadel_brake_span \
			and _wall_y >= GameplayPlane.BOUNDS.position.y:
		_armed = true
		_log("route fermée droit devant — freinage")
	if _wall_y > tuning.citadel_wall_plane_y:
		return
	_locked = true
	_log("VERROU — le survol est à l'arrêt, deux relais et un noyau")
	wall_locked.emit()
	# ⚠️ ET L'ÉTAT NE RECULE JAMAIS. Si le combat a déjà commencé pendant le freinage, la
	# machine est en `ONE_RELAY` (ou au-delà) et y reste : un relais abattu EST abattu. Seul un
	# verrou encore intact traverse `LOCKED`.
	if _state == State.APPROACH:
		_enter(State.LOCKED)

func _enter(next: State) -> void:
	if _state == next:
		return
	# ⚠️ LA REPRISE PART DE LA VITESSE COURANTE, PAS DE ZÉRO. Une route qui s'ouvre sur un
	# vaisseau qui n'a jamais freiné — un départ en aval du verrou, un verrou brisé pendant
	# l'approche — imposerait sinon trois secondes de ralenti que rien à l'écran n'expliquerait.
	# Amorcer l'horloge à la vitesse du moment rend la rampe continue dans tous les cas.
	var facteur := scroll_factor()
	_state = next
	if next == State.CLEARED:
		_resume_clock = tuning.citadel_resume_time * facteur
	match next:
		State.LOCKED:
			pass
		State.ONE_RELAY:
			_log("un relais est tombé — le bouclier tient encore")
		State.SHIELD_DOWN:
			_log("les deux relais sont tombés — BOUCLIER À TERRE, le noyau est touchable")
			_core.set_vulnerable(true)
			if _shield != null:
				_shield.visible = false
		State.CORE_DEAD:
			_log("noyau détruit — l'ouverture commence")
		State.OPENING:
			_log("les mécanismes écartent la voie")
		State.CLEARED:
			# ⚠️ LA ROUTE EST RENDUE ICI, ET SEULEMENT ICI. Tant que ce n'est pas fait, la forme
			# solide reste : un passage ouvert par l'animation et non par l'état laisserait
			# traverser un mur encore debout, ou l'inverse — un mur invisible.
			_log("route praticable — le survol repart")
			# ⚠️ ET LA PORTE CESSE D'ÊTRE DESSINÉE. Le fichier se prémunit du mur invisible ;
			# sans cette ligne il livrait l'injustice miroir — un volume de 34 m qui dit
			# « fermé » pendant que le joueur le traverse. Escamoter la boîte n'est PAS
			# l'ouverture du lot 4 : c'est la version qui ne mente pas en attendant.
			if _gate != null:
				_gate.visible = false
			cleared.emit()
	state_changed.emit(_state)

func _on_relay_destroyed(part: CitadelPart) -> void:
	_relays_down += 1
	relay_destroyed.emit(part)
	# ⚠️ DANS N'IMPORTE QUEL ORDRE, ET C'EST LE COMPTE QUI LE GARANTIT. Nommer un « premier » et
	# un « second » relais ferait dépendre la séquence du bord attaqué — et la moitié des parties
	# jouerait un autre jeu que l'autre moitié, sans qu'aucune trace ne le dise.
	if _relays_down >= _relays.size():
		_enter(State.SHIELD_DOWN)
	else:
		_enter(State.ONE_RELAY)

func _on_core_destroyed(part: CitadelPart) -> void:
	_open_clock = 0.0
	core_destroyed.emit(part)
	_enter(State.CORE_DEAD)

## Un tir a porté sur le bouclier. ⚠️ IL NE COÛTE RIEN ET IL SE VOIT : sans retour, le joueur
## conclut que le noyau n'a pas de hitbox et cesse de le viser — donc n'apprend jamais qu'il
## faut d'abord couper les relais.
func _on_core_deflected(_part: CitadelPart, world: Vector3) -> void:
	if _vfx != null:
		_vfx.spawn_explosion(world, VfxExplosion.Category.IMPACT,
			Color(SHIELD_TINT.r, SHIELD_TINT.g, SHIELD_TINT.b))

func _on_turret_destroyed(turret: CortegeTurret) -> void:
	turret_destroyed.emit(turret)

## Un nœud d'épine vient d'éteindre un tronçon : les tourelles du verrou en font partie.
##
## ⚠️ SANS ELLE, LA RÉCOMPENSE A UN TROU EXACTEMENT LÀ OÙ ELLE SE REMARQUE. Le verrou est sur le
## tronçon 3, et c'est le nœud du tronçon 2 qui l'éteint (`weakened_section(1, 5) = 2`). Les
## vingt-et-une batteries de coque faiblissent, annoncées au bandeau — et les quatre seules
## tourelles qui canardent le joueur pendant qu'il est IMMOBILE devant le mur gardaient toute
## leur vigueur. C'est le défaut que `CortegeHardpoints._on_node_destroyed` dit vouloir éviter
## (« laisser une batterie à pleine vigueur se lirait comme une panne de la récompense »),
## reproduit sur les pièces où il se sent le plus.
##
## ⚠️ ELLES NE SONT PAS COMPTÉES DANS L'ANNONCE, comme les autres légères : le chiffre promis au
## joueur reste celui des installations lourdes.
func weaken_section(target: int) -> void:
	if target != section:
		return
	for turret in _turrets:
		if turret.is_alive() and not turret.is_weakened():
			turret.weaken()

# ==========================================================================
# CE QUE LE NIVEAU LIT
# ==========================================================================

func state() -> State:
	return _state

func state_name() -> String:
	return String(State.keys()[_state])

## Le facteur de vitesse du survol, de 1 (croisière) à 0 (arrêt).
##
## ⚠️ LE VERROU NE TOUCHE PAS AU SURVOL, IL DIT CE QU'IL VEUT. Écrire `scroll_speed` d'ici
## donnerait deux écrivains à la même valeur — le réglage du niveau et la citadelle — et le
## jour où l'un des deux se tait, la vitesse reste là où l'autre l'a laissée.
func scroll_factor() -> float:
	if _state == State.CLEARED:
		if tuning.citadel_resume_time <= 0.001:
			return 1.0
		return clampf(_resume_clock / tuning.citadel_resume_time, 0.0, 1.0)
	# ⚠️ C'EST LA GÉOMÉTRIE QUI DÉCIDE, PAS L'ÉTAT DU COMBAT. Un relais abattu pendant le
	# freinage ne doit pas figer le vaisseau deux unités trop haut : le mur va jusqu'à sa place,
	# quoi qu'il arrive aux relais entre-temps.
	if _locked:
		return 0.0
	# ⚠️ ET UN MUR DÉJÀ DERRIÈRE LE JOUEUR NE RALENTIT PERSONNE. `brake_factor()` rendrait zéro
	# pour une distance négative — c'est-à-dire un survol figé par une porte franchie.
	if _wall_y < GameplayPlane.BOUNDS.position.y:
		return 1.0
	return CortegeTuning.brake_factor(_wall_y - tuning.citadel_wall_plane_y,
		tuning.citadel_brake_span)

## Verse la forme qui FERME LA ROUTE. ⚠️ ELLE EXISTE DANS TOUS LES ÉTATS SAUF `CLEARED`, et pas
## seulement pendant le combat : un mur qui n'apparaîtrait qu'à l'arrêt laisserait le joueur se
## poster derrière lui pendant le freinage, puis se retrouver du mauvais côté sans avoir rien
## fait de mal.
func fill_solids(shapes: PlaneShapes) -> void:
	if _state == State.CLEARED or not _measured:
		return
	# ⚠️ AUCUN `reserve()` ICI, ET C'EST VOULU. `PlaneShapes._push()` dimensionne lui-même, une
	# fois, par croissance géométrique ; demander `size() + 1` à chaque image physique ferait
	# dépendre la capacité de l'ORDRE des fournisseurs le jour où un second verse dans la même
	# liste — et le contrat de `reserve()` dit « à appeler UNE FOIS, au montage ».
	shapes.add_capsule(_wall_a, _wall_b, wall_radius())

## L'épaisseur du mur dans le plan. ⚠️ PLUS ÉPAIS QUE SA GÉOMÉTRIE, ET DÉLIBÉRÉMENT : un chasseur
## à 14 u/s parcourt 23 cm par image physique. Une paroi fine se traverse sur une image lente,
## et le joueur y lit un mur qui ne marche pas une fois sur dix — le pire des deux.
func wall_radius() -> float:
	return GATE_HALF_S + 0.30

## Où le mur se tient dans le plan, pour les tests et pour le journal.
func wall_plane_y() -> float:
	return _wall_y

## Ce que la séquence a duré, en secondes depuis le début du freinage. ⚠️ IL EXISTE PARCE QUE
## « SOUS 45 s » DOIT SE MESURER : le journal du survol n'est pas horodaté (dette du backlog), et
## un critère d'acceptation qu'aucune trace ne porte n'est pas un critère.
func elapsed() -> float:
	return _clock

func relays() -> Array[CitadelPart]:
	return _relays

func core() -> CitadelPart:
	return _core

func turrets() -> Array[CortegeTurret]:
	return _turrets

func is_cleared() -> bool:
	return _state == State.CLEARED

func _log(quoi: String) -> void:
	print("[Citadel] +%05.1f s — %s" % [_clock, quoi])
