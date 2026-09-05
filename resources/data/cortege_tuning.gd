class_name CortegeTuning
extends Resource
## Les réglages du survol du Long Cortège (niveau 2), et les invariants qui empêchent un
## réglage sensé de rendre le niveau injouable.
##
## ⚠️ ELLE EXISTE PARCE QU'UN SURVOL NE PARDONNE PAS. Le décor défile et **ne revient jamais en
## arrière** : chaque cible n'est tirable que pendant la fenêtre où elle est à l'écran. Des
## points de vie choisis à la main au-dessus de cette fenêtre rendent la cible indestructible
## EN PRATIQUE — et le joueur ne le saura jamais, il croira mal jouer et continuera de tirer
## sur ce qui ne peut pas tomber.
##
## C'est exactement le défaut qu'`ADR-0024` a payé sur le flux du Léviathan : des PV dimensionnés
## contre une cadence optimiste d'un facteur 2,4, qu'aucun test ne voyait parce que l'invariant
## se comparait à lui-même. Le modèle de ce fichier est `LeviathanTuning` et ses sept invariants.

## Les échelles de défense de la coque. ⚠️ ELLES VIVENT ICI ET NON SUR `CortegeTurret` : c'est
## cette Resource qui RÈGLE les deux, et faire dépendre le réglage de la pièce créerait un cycle
## là où il n'y a qu'une table de nombres. La pièce, elle, se contente de dire laquelle elle est.
##
## ⚠️ UNE ÉCHELLE DE PLUS EST UNE FAMILLE DE PLUS À BORNER. Les invariants bouclent sur
## `TurretScale.values()`, et c'est voulu : une échelle non bornée est exactement ce qui rend un
## survol injouable en silence. La troisième est arrivée le 2026-09-05, avec la planche des trois
## classes — et l'avertissement ci-dessus a été tenu : `validate()` a changé avec elle.
##
## ⚠️ L'ORDRE EST CELUI DE LA MASSE, ET IL PORTE UN INVARIANT. `LIGHT < STANDARD < HEAVY` permet
## à l'invariant 3 bis de boucler sur les couples CONSÉCUTIFS au lieu de comparer les familles
## deux à deux à la main. Trois familles font trois comparaisons manuelles, quatre en font six :
## la version écrite à la main aurait cessé d'être exhaustive à la première échelle suivante,
## sans que rien ne le dise. ⚠️ Ne pas réordonner : l'ordre EST la hiérarchie.
##
## ⚠️ ET « STANDARD » EST LA RÉFÉRENCE, d'où ses champs SANS PRÉFIXE (`turret_health`…), comme
## `reference_dps` est la cadence de référence. Ce n'est pas un oubli de nommage : ces valeurs
## sont celles que les dix-sept tourelles du niveau portaient déjà avant que la classe lourde
## n'existe. Les renommer aurait déplacé un réglage joué et testé pendant qu'on en ajoutait un
## autre — deux changements dans un seul diff, dont un invisible.
enum TurretScale { LIGHT, STANDARD, HEAVY }

# ==========================================================================
# Hypothèses de dimensionnement — PAS des réglages
# ==========================================================================

## Cadence du joueur de référence contre une CIBLE LARGE ET FIXE sur la coque (pont d'envol,
## tourelle). Tous les canons portent : c'est le cas favorable, celui de `reference_dps` du
## Léviathan.
@export var reference_dps: float = 420.0

## Cadence contre un NŒUD D'ÉPINE — petit, sur l'axe, à traverser le feu pour l'atteindre.
##
## ⚠️ DEUX HYPOTHÈSES ET NON UNE, et c'est la leçon d'`ADR-0024`. Se comparer à une seule
## cadence revient à se donner raison : sur une baie de plusieurs mètres les canons d'aile
## portent, sur un nœud ils partent à côté. Seuls les canons de nez comptent.
@export var node_reference_dps: float = 208.0

## Vitesse à laquelle la coque défile sous le joueur, en unités/seconde.
##
## ⚠️ ELLE COMMANDE TOUT LE RESTE. Repères du niveau 1 : la surface de la lune défile à
## 1,2 u/s, ses rochers de 0,7 à 3,2. En dessous de 2, un survol devient une dérive : le plan
## de jeu fait 16 unités de haut, donc à 0,8 u/s un point fixe met 20 s à traverser l'écran.
@export var scroll_speed: float = 2.4

## Part du temps où le joueur peut réellement placer ses tirs sur une cible de coque. Le reste
## du temps, il esquive. **C'est le vrai levier de conception**, pas les points de vie.
@export var occupancy_hull: float = 0.55
## Idem pour un nœud, plus bas : il faut s'aligner sur l'axe, là où tout converge.
@export var occupancy_node: float = 0.35

# ==========================================================================
# Structure du niveau
# ==========================================================================

## Le nombre de tronçons joués. ⚠️ Le vaisseau en compte sept (maquettes) ; le niveau 2 s'arrête
## au cinquième, sur Ambry. Les deux derniers appartiennent au niveau 3.
@export var section_count: int = 5
## Longueur d'un tronçon, en unités monde. Doit correspondre à la géométrie livrée.
@export var section_length: float = 100.0

## Durée visée pour le niveau entier, et sa tolérance. C'est la promesse faite au joueur.
## ⚠️ 240 ET NON 210 DEPUIS LA CITADELLE, ET LA PROMESSE A CHANGÉ PARCE QUE LE CONTENU A CHANGÉ.
## Le survol défile en 208 s ; le verrou de mi-parcours en ajoute une trentaine, à l'arrêt. Garder
## 210 aurait obligé à raccourcir l'un des deux pour tenir un chiffre qui décrivait un niveau sans
## verrou. C'est `level_duration()` qui compte les deux, et l'invariant 1 qui les borne ensemble.
@export var target_duration: float = 240.0
@export var duration_tolerance: float = 30.0

# ==========================================================================
# Les trois mécaniques de coque
# ==========================================================================

@export_group("Tourelles")
## Distance sur laquelle une tourelle reste tirable — sa taille plus la hauteur de l'écran.
@export var turret_visible_span: float = 20.0
@export var turret_health: float = 180.0
## ⚠️ LA TOURELLE NE TÉLÉGRAPHIE PLUS, ELLE TIRE EN CONTINU — ET C'EST UN GAIN DE LISIBILITÉ,
## pas une perte. Le modèle précédent était celui du Léviathan : `READY → WINDUP → FIRING →
## RECOVER`, avec un préavis qui annonçait le coup. Il marche sur un boss, qu'on regarde. Il ne
## marche pas ici : « je ne vois pas les tourelles qui me tirent dessus » (opérateur, en jouant
## le 2026-08-29). Sur un décor qui défile, avec dix-sept pièces réparties sur deux flancs, un
## préavis de 0,8 s passe inaperçu — le joueur regarde ailleurs, il esquive.
##
## Un faisceau PERMANENT résout le problème par construction : la menace est visible tout le
## temps, et sa direction se lit d'un coup d'œil. Ce qui remplace le télégraphe, c'est la
## LENTEUR : la tourelle pivote, le joueur va plus vite qu'elle.

## Vitesse de rotation de la tourelle, en degrés par seconde.
##
## ⚠️ C'EST LE SEUL RÉGLAGE DE DIFFICULTÉ DE LA PIÈCE, et il remplace le télégraphe : l'invariant
## 3 vérifie qu'elle reste DISTANÇABLE. Un joueur à 14 u/s qui passe à 8 unités d'une tourelle
## tourne autour d'elle à 100 °/s ; au-delà de cette vitesse, la tourelle le suit quoi qu'il
## fasse et le faisceau devient un impôt.
@export var turret_turn_rate_deg: float = 42.0

## Ce que le faisceau coûte à chaque morsure, et l'intervalle entre deux morsures.
##
## ⚠️ EN MORSURES ET NON PAR SECONDE. Le bouclier du chasseur a sa propre fenêtre : lui verser
## `dps × delta` à chaque image ferait perdre presque tout dans les images gelées, et rendrait
## les dégâts dépendants de la cadence d'affichage. Une morsure toutes les 0,4 s se règle, se
## teste, et se sent.
@export var turret_burn_damage: float = 7.0
@export var turret_burn_interval: float = 0.4
## Portée du faisceau, et sa demi-largeur. ⚠️ La portée doit couvrir la DIAGONALE du plan de
## jeu (16,1 unités) : une tourelle postée dans un coin doit pouvoir atteindre le coin opposé,
## sinon son télégraphe promet un tir qui n'arrive pas — et un télégraphe qui ment est pire
## que pas de télégraphe.
@export var turret_range: float = 34.0
@export var turret_beam_half_width: float = 0.30
## Ce que rapporte une tourelle abattue.
@export var turret_score: int = 900

@export_group("Tourelles légères")
## ⚠️ ELLES MEUBLENT, ELLES NE DÉCIDENT PAS. Une grosse tourelle est un événement local : on la
## voit venir, on choisit de s'en occuper. Une tourelle légère est du décor ACTIF — elle pose une
## pression continue et faible, en batteries, et le joueur la balaie en passant sans jamais avoir
## à s'arrêter dessus. Le jour où l'une des deux prend le rôle de l'autre, la hiérarchie tombe et
## on retrouve la « forêt uniforme de tourelles identiques » que la consigne 8 interdit.

## Sa fenêtre est PLUS COURTE que celle de la grosse, et ce n'est pas un réglage de difficulté :
## une pièce trois fois plus petite se distingue trois fois moins loin. Lui donner la fenêtre de
## la grosse ferait tirer une chose qu'on ne voit pas encore.
@export var light_turret_visible_span: float = 14.0
## ⚠️ ELLE TOMBE EN PASSANT, ET C'EST SA DÉFINITION. À 55 PV elle coûte 4 % de ce qu'un joueur de
## référence peut placer dans sa fenêtre : une rafale d'appoint suffit. L'invariant 2 borne le
## HAUT (au-delà de 35 %, s'en occuper empêche de faire autre chose) ; c'est le rôle de la pièce
## qui borne le bas — une petite tourelle qu'il faut travailler est une grosse tourelle ratée.
@export var light_turret_health: float = 55.0
## ⚠️ ELLE PIVOTE PLUS VITE QUE LA GROSSE, ET C'EST TOUT CE QUE « PLUS PETITE DONC PLUS RAPIDE »
## PEUT VOULOIR DIRE ICI. Mais la borne de l'invariant 3 ne se négocie pas : un joueur à 14 u/s
## contourne une pièce à 8 unités en 100 °/s, et une tourelle au-delà de 60 °/s le suit quoi
## qu'il fasse. À 56 °/s elle est vive — un tiers de plus que les 42 °/s de la grosse — et elle
## reste distançable, avec 7 % de marge sous le plafond. ⚠️ NE PAS MONTER À 66 : la valeur
## d'abord écrite cassait l'invariant, et un faisceau qu'on ne peut pas semer est une taxe.
@export var light_turret_turn_rate_deg: float = 56.0
## Une cadence PLUS LENTE que la grosse, et c'est contre-intuitif pour une pièce dite « rapide ».
## ⚠️ PARCE QU'ELLES VIENNENT PAR QUATRE. Une batterie à la cadence de la lourde cracherait dix
## balles par seconde à elle seule : la somme d'une batterie doit rester sous la menace d'UNE
## grosse tourelle, sinon la hiérarchie s'inverse et le joueur apprend à craindre les petites.
## Ce qui est « plus rapide » chez elle est sa ROTATION, pas son débit.
@export var light_turret_burn_interval: float = 0.62

## ⚠️ IL N'Y A NI `light_turret_burn_damage` NI `light_turret_range`, ET C'EST DÉLIBÉRÉ. Leurs
## équivalents lourds — `turret_burn_damage`, `turret_range`, `turret_beam_half_width` — ne sont
## lus par AUCUN script ni test depuis qu'`ADR-0040` a remplacé le faisceau par des balles : les
## dégâts et la portée d'un tir de tourelle vivent dans son `ProjectileData`
## (`cortege_turret_shot.tres`, `cortege_light_shot.tres`). Leur donner ici un jumeau léger
## aurait créé un réglage que l'on croit régler et qui ne fait rien — le pire des deux mondes, et
## exactement le piège qu'`ADR-0024` a payé. L'écart de dégâts entre les deux échelles est donc
## borné par un TEST sur les deux Resources, pas par un invariant sur des champs morts.
## Ce que rapporte une tourelle légère abattue. ⚠️ PETIT, ET DÉLIBÉRÉMENT : à quatre pièces par
## batterie, un score généreux ferait des batteries la meilleure source de points du niveau, et
## le joueur cesserait de viser ce qui compte.
@export var light_turret_score: int = 240

@export_group("Tourelles lourdes")
## ⚠️ ELLE EST UN ÉVÉNEMENT, ET C'EST TOUT CE QUI LA DISTINGUE. La planche du 2026-09-05 la
## définit par « puissance, dissuasion, contrôle » et par « PEU D'EXEMPLAIRES ». Une tourelle
## lourde qu'on croiserait dix-sept fois ne serait pas une tourelle lourde : ce serait la
## nouvelle tourelle standard, et la hiérarchie à trois classes serait retombée à deux.
##
## Le niveau en pose TROIS, toutes à l'arrière (`cortege_hardpoints.gd`) : c'est la coque qui
## devient « de plus en plus massive » vers la poupe, pas une difficulté qui monte par palier.

## Sa fenêtre est plus longue que celle de la standard : une pièce deux fois plus grande se
## distingue de plus loin. Même raisonnement que pour la légère, pris par l'autre bout.
@export var heavy_turret_visible_span: float = 26.0
## ⚠️ ELLE NE TOMBE PAS EN PASSANT, ET C'EST SA DÉFINITION. À 520 PV elle coûte 21 % de ce qu'un
## joueur de référence peut placer dans sa fenêtre — contre 9 % pour la standard et 4 % pour la
## légère. S'en occuper est une DÉCISION, comme un pont d'envol. L'invariant 2 borne toujours le
## haut à 35 % : au-delà, le survol devient une file d'attente.
@export var heavy_turret_health: float = 520.0
## ⚠️ ELLE PIVOTE PLUS LENTEMENT QUE LA STANDARD, ET C'EST CE QUI LA REND JOUABLE. Elle frappe
## plus fort et vit plus longtemps : si elle suivait aussi vite, elle n'aurait aucun défaut à
## exploiter. La lenteur est la contrepartie de la masse — c'est la même règle que l'invariant 3
## tient pour tout le monde, ici prise dans le sens du poids.
@export var heavy_turret_turn_rate_deg: float = 30.0
## Une cadence PLUS DENSE que la standard. ⚠️ ELLE EST SEULE, LÀ OÙ LES LÉGÈRES VIENNENT PAR
## QUATRE : c'est ce qui permet de la faire tirer plus souvent sans que la somme d'un groupe
## dépasse la pièce au-dessus. Le raisonnement de `light_turret_burn_interval`, retourné.
@export var heavy_turret_burn_interval: float = 0.30
## Ce que rapporte une tourelle lourde abattue. Le double de la standard : c'est le prix du
## temps qu'on lui consacre, et il n'y en a que trois dans le niveau.
@export var heavy_turret_score: int = 1800

@export_group("Ponts d'envol")
## ⚠️ ILS COÛTENT CHER À FAIRE TOMBER, C'EST LEUR RAISON D'ÊTRE. Un pont laissé debout produit
## en continu ; l'abattre est une décision, pas un réflexe. Mais le prix a une borne, et c'est
## l'invariant 2 qui la tient.
@export var bay_visible_span: float = 24.0
@export var bay_health: float = 900.0
## Intervalle entre deux lâchers, tant que le pont vit.
@export var bay_release_interval: float = 2.2
## Combien d'unités par lâcher.
@export var bay_release_count: int = 2
## Le pool propre à CHAQUE pont. ⚠️ Il est alloué au montage du niveau et jamais pendant la
## partie (spec §26.1) : il doit couvrir le pire cas, soit tous les lâchers d'un pont qui vit
## jusqu'au bout de sa fenêtre. `validate()` le vérifie plutôt que de le supposer.
@export var bay_pool_size: int = 10
@export var bay_score: int = 4200

@export_group("Épine dorsale")
## Un nœud par tronçon.
@export var node_visible_span: float = 14.0
@export var node_health: float = 260.0
## Ce qu'un nœud abattu abîme : les tourelles du tronçon SUIVANT.
@export var node_weakens_next_section: bool = true
@export var node_score: int = 2600

## Ce qu'il reste à une tourelle abîmée, en part de son réglage nominal.
##
## ⚠️ CES DEUX FACTEURS EXISTENT PARCE QUE L'EXTINCTION TOTALE A VIDÉ LE NIVEAU. Mesuré en jeu le
## 2026-08-30 : les cinq nœuds tombent, chacun éteignait tout son tronçon, et **quinze tourelles
## sur dix-sept** se taisaient avant d'être à portée. Le joueur y lisait une panne, pas une
## récompense. Une tourelle abîmée reste donc vivante — elle pivote plus lentement et tire moins
## souvent — et l'invariant 8 borne les deux valeurs des DEUX côtés : trop haut la récompense ne
## se sent pas, trop bas on retrouve l'extinction sous un autre nom.
@export var turret_weakened_turn_factor: float = 0.45
@export var turret_weakened_interval_factor: float = 2.6

@export_group("La Citadelle de Défense")
## Le verrou de mi-parcours : une fortification transversale qui FERME LA ROUTE, s'ouvre en
## sabotant deux relais puis un noyau, et rend le passage praticable.
##
## ⚠️ CE N'EST PAS UN BOSS, ET C'EST LA CONTRAINTE QUI PRIME SUR TOUTES LES AUTRES. Pas de barre
## de vie, pas de rideau de projectiles, pas de cycles. Ce qui la distingue d'un boss n'est pas
## une intention mais un CHIFFRE : `citadel_fight_time()`, borné des deux côtés ci-dessous. Sous
## le plancher, c'est un dos d'âne ; au-dessus du plafond, c'est un boss qui ne dit pas son nom,
## et le niveau 2 en a déjà un au niveau 1.

## La station de la FACE AVANT du verrou, comptée depuis la proue.
##
## ⚠️ ELLE EST CONTRAINTE PAR TROIS VOISINS MESURÉS, pas choisie : la garde de la fosse de
## `s = 228` finit à 236,2 ; le socle de `Turret_07` commence à 255,25 ; `Spine_03` est à 260,2.
## Il reste 19 m, et la citadelle en occupe 6,4. ⚠️ ET LA COQUE S'Y ÉLARGIT — `TAPER` monte de
## 1,000 à 236 vers 1,230 à 258 : la fortification est posée sur une rampe, pas sur un plateau.
## C'est assumé (un verrou qui s'évase se lit comme un contrefort) mais ça se sait avant de
## sculpter la géométrie définitive.
@export var citadel_station: float = 240.0

## Où la face avant s'IMMOBILISE dans le plan de jeu, en unités du plan.
##
## ⚠️ LE RALENTISSEMENT N'EST PAS UN EFFET DE MISE EN SCÈNE, C'EST CE QUI REND LA SÉQUENCE
## POSSIBLE. À 2,4 u/s, 40 s de combat vaudraient 96 m de coque — un cinquième du vaisseau, quand
## la fenêtre libre en fait 19. Le survol s'arrête donc pendant le combat, et c'est cet arrêt qui
## fabrique l'arène : le mur en haut, le joueur dessous.
@export var citadel_wall_plane_y: float = 4.0

## Sur combien d'unités de plan le survol freine avant de s'arrêter. La décélération est
## CONSTANTE (`brake_factor()`), donc la durée du freinage vaut `2 x span / vitesse`.
@export var citadel_brake_span: float = 5.0
## Combien de temps le survol met à retrouver sa vitesse une fois la route ouverte.
@export var citadel_resume_time: float = 3.0
## Ce que dure l'ouverture, entre le noyau mort et la route praticable.
@export var citadel_open_time: float = 2.2

## Part du temps où le joueur peut réellement placer ses tirs PENDANT LE VERROU.
##
## ⚠️ MESURÉE EN JEU LE 2026-09-04, ET ELLE VALAIT 0,45 AU JUGÉ — LE MÊME DÉFAUT QU'`ADR-0024`,
## AU MÊME FACTEUR. Ce fichier écrivait, deux lignes plus haut, que se dimensionner sur
## l'occupation de la coque ouverte « reviendrait à se donner raison ». Puis il choisissait 0,45
## sans mesurer, c'est-à-dire qu'il se donnait raison quand même : l'invariant se comparait à
## lui-même.
##
## La partie de l'opérateur a tranché : **3 800 PV tombés en 47,9 s**, soit 79 dps effectifs sur
## les 420 de référence — **0,19**, pas 0,45. Facteur 2,4, exactement celui que le flux du
## Léviathan avait coûté. Et le temps était du VRAI combat : « j'ai compris tout de suite »
## (opérateur), donc rien de ces 47,9 s n'est passé à chercher quoi tirer.
##
## ⚠️ ELLE EST PLUS BASSE QUE TOUT LE RESTE DU NIVEAU, ET C'EST COHÉRENT. L'arène fait une
## douzaine d'unités au lieu de seize, la fortification tient le haut de l'écran, ses tourelles
## tirent d'un point FIXE et les ponts d'envol continuent de produire pendant l'arrêt — sept
## coques écrasées dans la partie mesurée. Le joueur esquive plus qu'il ne tire.
@export var occupancy_citadel: float = 0.19

## Les deux relais, dans n'importe quel ordre. Tant qu'UN SEUL vit, le noyau est intouchable.
@export var citadel_relay_health: float = 800.0
## Le noyau. ⚠️ PLUS CHER QU'UN RELAIS, et l'invariant 10 le tient : un noyau qui tomberait plus
## vite que ce qui le protège inverserait la lecture « GAUCHE + DROITE → CENTRE ».
@export var citadel_core_health: float = 1100.0
@export var citadel_relay_score: int = 2200
@export var citadel_core_score: int = 6000

# ==========================================================================
# Fonctions dérivées — à lire, jamais à recopier dans un test
# ==========================================================================

## Combien de temps un pont passe AU-DESSUS DU TERRAIN, et non dans sa fenêtre de tir.
##
## ⚠️ LES DEUX NE SONT PAS LA MÊME CHOSE, et les confondre a produit un pont qui ne lâchait
## qu'UNE FOIS là où l'invariant en promettait deux. La fenêtre de tir déborde le plan de vol —
## la caméra plonge et voit loin devant, donc on tire sur un pont bien avant qu'il n'arrive.
## Mais il ne peut LÂCHER que quand il est au-dessus du terrain : une coque née plus haut que la
## borne du plan est détruite à sa première trame par le despawn de `EnemyController`. C'est
## donc la hauteur du plan de vol, et elle seule, qui dit la pression qu'un pont exerce.
func release_window() -> float:
	if scroll_speed <= 0.001:
		return 0.0
	return GameplayPlane.BOUNDS.size.y / scroll_speed

## Combien de temps une cible reste tirable, à la vitesse de défilement courante.
func window_for(visible_span: float) -> float:
	if scroll_speed <= 0.001:
		return 0.0
	return visible_span / scroll_speed

## Ce qu'un joueur de référence peut réellement placer dans cette fenêtre.
func reachable_damage(visible_span: float, dps: float, occupancy: float) -> float:
	return dps * occupancy * window_for(visible_span)

func turret_reachable() -> float:
	return reachable_damage(turret_visible_span, reference_dps, occupancy_hull)

# --------------------------------------------------------------------------
# Les réglages, LUS PAR ÉCHELLE
# --------------------------------------------------------------------------
# ⚠️ CES SEPT FONCTIONS EXISTENT POUR QUE `validate()` ET LA PIÈCE LISENT LA MÊME TABLE. Une
# seconde échelle recopiée à la main dans la tourelle serait une échelle que les invariants ne
# voient pas — exactement le défaut d'`ADR-0024`, où l'invariant se comparait à lui-même pendant
# que le vrai réglage dérivait. Ici il n'y a qu'une porte, et les tests passent par elle.
#
# ⚠️ ELLES NE SONT PAS DANS UNE BOUCLE CRITIQUE. La tourelle les lit à chaque image, mais une
# lecture de champ derrière un `match` ne coûte rien et n'alloue pas (spec §31).

func turret_span_of(scale: TurretScale) -> float:
	match scale:
		TurretScale.LIGHT: return light_turret_visible_span
		TurretScale.HEAVY: return heavy_turret_visible_span
	return turret_visible_span

func turret_health_of(scale: TurretScale) -> float:
	match scale:
		TurretScale.LIGHT: return light_turret_health
		TurretScale.HEAVY: return heavy_turret_health
	return turret_health

func turret_turn_rate_of(scale: TurretScale) -> float:
	match scale:
		TurretScale.LIGHT: return light_turret_turn_rate_deg
		TurretScale.HEAVY: return heavy_turret_turn_rate_deg
	return turret_turn_rate_deg

func turret_burn_interval_of(scale: TurretScale) -> float:
	match scale:
		TurretScale.LIGHT: return light_turret_burn_interval
		TurretScale.HEAVY: return heavy_turret_burn_interval
	return turret_burn_interval

func turret_score_of(scale: TurretScale) -> int:
	match scale:
		TurretScale.LIGHT: return light_turret_score
		TurretScale.HEAVY: return heavy_turret_score
	return turret_score

## Ce qu'un joueur de référence peut placer dans la fenêtre de CETTE échelle.
func turret_reachable_of(scale: TurretScale) -> float:
	return reachable_damage(turret_span_of(scale), reference_dps, occupancy_hull)

## Le nom de l'échelle, pour que le message d'un invariant dise LAQUELLE des trois il refuse.
static func turret_scale_name(scale: TurretScale) -> String:
	match scale:
		TurretScale.LIGHT: return "une tourelle légère"
		TurretScale.HEAVY: return "une tourelle lourde"
	return "une tourelle standard"

func bay_reachable() -> float:
	return reachable_damage(bay_visible_span, reference_dps, occupancy_hull)

func node_reachable() -> float:
	return reachable_damage(node_visible_span, node_reference_dps, occupancy_node)

## Le temps passé à DÉFILER, déduit de la géométrie et de la vitesse — jamais saisi à la main.
func scroll_duration() -> float:
	if scroll_speed <= 0.001:
		return 0.0
	return float(section_count) * section_length / scroll_speed

## La durée du niveau TELLE QU'ELLE SE JOUE.
##
## ⚠️ ELLE N'EST PLUS CELLE DU DÉFILEMENT, ET C'EST UN DÉFAUT CORRIGÉ. Le verrou de mi-parcours
## IMMOBILISE le survol : freinage, combat et ouverture se jouent à vitesse nulle ou réduite,
## soit une trentaine de secondes que la géométrie ne voit pas. L'invariant 1 comparait donc
## 208 s à la promesse pendant que le niveau en durait 240 — et rien ne l'aurait dit. Pire : la
## borne haute de l'invariant 9 (30 s de tir) autorise un verrou qui pousserait le niveau à
## 245 s, hors de la promesse, en restant vert partout.
func level_duration() -> float:
	return scroll_duration() + citadel_sequence_time()

## Le rythme d'un tronçon. ⚠️ SUR LE DÉFILEMENT ET NON SUR LA DURÉE JOUÉE : c'est une cadence
## spatiale — combien de temps sépare deux entrées de tronçon — et le verrou n'en déplace aucune.
func section_duration() -> float:
	return scroll_duration() / float(maxi(section_count, 1))

# --------------------------------------------------------------------------
# La Citadelle — ce que ses réglages COÛTENT en temps
# --------------------------------------------------------------------------

## Combien de temps le verrou tient un joueur de référence, dégâts seuls.
##
## ⚠️ LES TROIS CIBLES COMPTENT ENSEMBLE, ET DANS N'IMPORTE QUEL ORDRE. Les deux relais se
## valent, le noyau vient après : la somme est la même quel que soit le chemin, et c'est
## précisément ce que le lot 1 doit prouver en jouant les deux ordres.
func citadel_fight_time() -> float:
	var dps := reference_dps * occupancy_citadel
	if dps <= 0.001:
		return 0.0
	return (2.0 * citadel_relay_health + citadel_core_health) / dps

## Le rapport entre la vitesse de DÉFILEMENT et celle du mur DANS LE PLAN.
##
## ⚠️ MESURÉ, PAS DÉDUIT, ET IL FAISAIT MENTIR LE FREINAGE DE 20 %. La caméra plonge et
## PROJETTE : un mètre de coque parcouru ne fait pas un mètre de plan. Le freinage prédit avec
## la vitesse de défilement donnait 4,17 s ; avec ce facteur il donne 5,06 s — et le journal
## horodaté de la partie du 2026-09-04 en a chronométré **5,0**. La première écriture assumait
## l'écart en le déclarant « optimiste, donc sûr pour un plafond » : c'était vrai, et c'était
## quand même une seconde d'erreur sur un budget de quarante-cinq.
##
## ⚠️ IL DÉPEND DE LA CAMÉRA DE `cortege.tscn`, et rien ici ne peut le vérifier —
## `validate()` tourne sans scène. C'est `test_cortege_citadel.gd` qui le garde : il relit la
## caméra du niveau et refait le calcul. Une caméra reculée sans toucher ce nombre y échoue.
const PLANE_SPEED_RATIO := 0.8235

## Ce que dure le FREINAGE, à décélération constante.
func citadel_brake_time() -> float:
	var plan := scroll_speed * PLANE_SPEED_RATIO
	if plan <= 0.001:
		return 0.0
	return 2.0 * citadel_brake_span / plan

## Ce que le critère d'acceptation CHRONOMÈTRE : du premier mètre de freinage à la route
## praticable.
##
## ⚠️ LA REPRISE N'Y EST PAS, ET C'EST CE QUE LE JOURNAL A MONTRÉ. La partie mesurée donne
## « freinage » à +0,0 s et « route praticable » à +55,1 s : le chronomètre s'arrête à `CLEARED`,
## la rampe de reprise court après. Border la séquence ENTIÈRE contre le budget du brief aurait
## refusé trois secondes qui ne sont pas comptées, et laissé passer trois secondes qui le sont.
func citadel_lock_time() -> float:
	return citadel_brake_time() + citadel_fight_time() + citadel_open_time

## Ce que dure la séquence ENTIÈRE : le freinage, le combat, l'ouverture, la reprise.
##
## ⚠️ LE FREINAGE ET LA REPRISE COMPTENT, ET ILS ONT FAILLI ÊTRE OUBLIÉS. Huit des quarante-quatre
## secondes de la séquence se jouent hors combat : les mesurer à part reviendrait à promettre
## trente secondes et à en jouer quarante. C'est cette fonction que `level_duration()` lit —
## le niveau paie la reprise, même si le chronomètre du critère s'arrête avant.
func citadel_sequence_time() -> float:
	return citadel_lock_time() + citadel_resume_time

## La hauteur d'arène que le mur laisse au joueur, du plancher du plan à la face avant.
func citadel_arena_height() -> float:
	return citadel_wall_plane_y - GameplayPlane.BOUNDS.position.y

## Le facteur de vitesse pendant le freinage, à `remaining` unités de plan de l'arrêt.
##
## ⚠️ EN RACINE ET NON EN LINÉAIRE, ET LA DIFFÉRENCE EST QU'UNE DES DEUX N'ARRIVE JAMAIS. Un
## facteur linéaire en distance donne `du/dt = -k.u` : une approche exponentielle, qui ne touche
## pas l'arrêt en temps fini — le vaisseau se traînerait indéfiniment devant le mur, et l'état
## suivant ne s'ouvrirait pas. La racine, elle, EST la décélération constante : `v² = 2.a.d`.
## Elle atteint zéro, et elle se lit comme un vaisseau qui freine.
static func brake_factor(remaining: float, span: float) -> float:
	if span <= 0.001:
		return 0.0 if remaining <= 0.0 else 1.0
	return sqrt(clampf(remaining / span, 0.0, 1.0))

# ==========================================================================
# validate() — les invariants
# ==========================================================================

func validate() -> PackedStringArray:
	var errors := PackedStringArray()

	# --- Hypothèses ------------------------------------------------------
	if reference_dps <= 0.0 or node_reference_dps <= 0.0:
		errors.append("les deux cadences de référence doivent être > 0 — ce sont les hypothèses de dimensionnement, pas des options")
	if scroll_speed <= 0.0:
		errors.append("scroll_speed doit être > 0 — un survol qui n'avance pas n'est pas un survol")
	for value in [occupancy_hull, occupancy_node]:
		if value <= 0.0 or value > 1.0:
			errors.append("les occupations sont des parts de temps, dans (0, 1]")
			break

	# --- INVARIANT 1 : le niveau dure ce qu'on a promis -------------------
	if section_count <= 0:
		errors.append("section_count doit être > 0")
	elif section_length <= 0.0:
		errors.append("section_length doit être > 0")
	elif duration_tolerance < 0.0:
		errors.append("duration_tolerance doit être >= 0")
	else:
		var duree := level_duration()
		if absf(duree - target_duration) > duration_tolerance:
			errors.append("le survol dure %.0f s, hors de la cible %.0f ± %.0f — changez la vitesse ou la longueur des tronçons"
				% [duree, target_duration, duration_tolerance])

	# --- INVARIANT 2 : TOUTE CIBLE TOMBE DANS SA FENÊTRE -----------------
	# ⚠️ C'EST L'INVARIANT QUI DÉCIDE SI LE NIVEAU EXISTE. Un survol ne revient jamais en
	# arrière : au-dessus de ce que la fenêtre permet, la cible est indestructible EN PRATIQUE,
	# et le joueur croira mal jouer.
	#
	# ⚠️ MAIS LA BORNE BASSE N'EST PAS LA MÊME POUR TOUS, et sa première écriture s'est
	# trompée en leur appliquant la même règle. Les trois cibles ne jouent pas le même rôle :
	#
	#   - un PONT et un NŒUD sont des DÉCISIONS. Ils doivent coûter — sous 45 % de ce qui est
	#     atteignable, ils tombent en passant et le choix de les viser n'existe plus ;
	#   - une TOURELLE est une cible d'OPPORTUNITÉ. Il y en a douze à dix-huit, souvent
	#     plusieurs à l'écran. Elle a besoin d'un PLAFOND, pas d'un plancher : au-delà de 35 %
	#     de la fenêtre, s'occuper d'une seule tourelle empêche de faire quoi que ce soit
	#     d'autre, et le survol devient une file d'attente.
	var decisions := [
		["un pont d'envol", bay_health, bay_reachable(), bay_visible_span],
		["un nœud d'épine", node_health, node_reachable(), node_visible_span],
	]
	for cible in decisions:
		var nom: String = cible[0]
		var pv: float = cible[1]
		var atteignable: float = cible[2]
		var portee: float = cible[3]
		if portee <= 0.0:
			errors.append("%s : sa fenêtre de tir est nulle — il ne serait jamais tirable" % nom)
		elif pv <= 0.0:
			errors.append("%s : ses points de vie doivent être > 0" % nom)
		elif pv > atteignable:
			errors.append("%s demande %.0f dégâts mais %.0f seulement sont atteignables en %.1f s — il ne peut PAS tomber, et le joueur croira mal jouer"
				% [nom, pv, atteignable, window_for(portee)])
		elif pv < atteignable * 0.45:
			errors.append("%s demande %.0f dégâts pour %.0f atteignables — il tombe en passant, et le choix de le viser n'existe plus"
				% [nom, pv, atteignable])
	# ⚠️ LES DEUX ÉCHELLES PASSENT LE MÊME PLAFOND. Une tourelle légère qu'il faudrait travailler
	# n'est pas une tourelle légère : c'est une grosse tourelle ratée, et le joueur qui s'arrête
	# sur une batterie de quatre a perdu son survol. Boucler ici plutôt que de recopier le test
	# est ce qui garantit qu'une échelle future ne naîtra pas hors invariant.
	for scale in TurretScale.values():
		var nom_t := turret_scale_name(scale)
		var portee_t := turret_span_of(scale)
		var pv_t := turret_health_of(scale)
		if portee_t <= 0.0:
			errors.append("%s : sa fenêtre de tir est nulle" % nom_t)
		elif pv_t <= 0.0:
			errors.append("%s : ses points de vie doivent être > 0" % nom_t)
		elif pv_t > turret_reachable_of(scale) * 0.35:
			errors.append("%s demande %.0f dégâts, soit %.0f%% de la fenêtre — au-delà de 35%%, s'en occuper empêche de faire autre chose et le survol devient une file d'attente"
				% [nom_t, pv_t, pv_t / turret_reachable_of(scale) * 100.0])

	# --- INVARIANT 3 : UNE TOURELLE SE DISTANCE -------------------------
	#
	# ⚠️ IL REMPLACE « TOUTE ATTAQUE LOURDE EST TÉLÉGRAPHIÉE », et il le remplace parce que le
	# télégraphe ne marchait pas ici. La règle de la spec §11.2 dit qu'un tir sans préavis est
	# une taxe et non une difficulté ; elle reste vraie. Ce qui change, c'est la façon de la
	# tenir : sur un boss qu'on regarde, on annonce le coup ; sur dix-sept pièces réparties le
	# long d'un décor qui défile, on rend la menace PERMANENTE et VISIBLE, et on la fait
	# perdre. Le faisceau est son propre préavis, à condition qu'on puisse le semer.
	#
	# Le seuil se calcule et ne se choisit pas : un joueur à `max_speed` qui contourne une
	# tourelle à distance `d` tourne autour d'elle à `max_speed / d` radians par seconde. La
	# tourelle doit rester sous cette vitesse, avec de la marge — sinon elle colle au joueur
	# quoi qu'il fasse, et le faisceau redevient une taxe.
	const PLAYER_SPEED := 14.0     # `player_stats.gd` : max_speed
	const CLOSE_RANGE := 8.0       # la distance à laquelle on passe VRAIMENT près d'une pièce
	var escapable_deg := rad_to_deg(PLAYER_SPEED / CLOSE_RANGE)
	# ⚠️ LA BORNE EST LA MÊME POUR LES DEUX, PARCE QU'ELLE DÉCRIT LE JOUEUR ET NON LA PIÈCE.
	# Elle se calcule à partir de sa vitesse et de la distance de passage ; une pièce plus petite
	# ne rend pas le joueur plus agile. C'est ce qui plafonne « plus petite donc plus rapide » à
	# 60 °/s, et une tourelle légère à 66 °/s a été refusée ici avant d'atteindre le jeu.
	for scale in TurretScale.values():
		var nom_r := turret_scale_name(scale)
		var rate := turret_turn_rate_of(scale)
		if rate <= 0.0:
			errors.append("%s : sa vitesse de rotation doit être > 0 — une tourelle qui ne pivote pas ne vise jamais personne" % nom_r)
		elif rate > escapable_deg * 0.6:
			errors.append("%s pivote à %.0f °/s alors qu'un joueur en contourne une à %.0f °/s : elle le suivrait quoi qu'il fasse, et un tir qu'on ne peut pas semer est une taxe, pas une difficulté"
				% [nom_r, rate, escapable_deg])
		if turret_burn_interval_of(scale) <= 0.0:
			errors.append("%s : son intervalle de tir doit être > 0 — sinon la morsure dépend de la cadence d'affichage" % nom_r)

	# --- INVARIANT 3 bis : LA HIÉRARCHIE DES ÉCHELLES EXISTE -------------
	# ⚠️ SANS LUI, RIEN N'EMPÊCHE LES DEUX FAMILLES DE CONVERGER. Elles ont chacune sept
	# réglages ; à force d'ajustements, une légère qui tape aussi fort et voit aussi loin
	# qu'une lourde redevient la « forêt uniforme de tourelles identiques » que ce lot existe
	# pour éviter — et rien, ni test ni capture, ne le signalerait. Les trois écarts qui
	# PORTENT la hiérarchie sont donc déclarés, pas espérés.
	# ⚠️ IL BOUCLE SUR LES COUPLES CONSÉCUTIFS, IL NE COMPARE PLUS DEUX FAMILLES À LA MAIN.
	# Avec deux échelles, trois `if` écrits à la main suffisaient. Avec trois, il en faudrait six
	# pour rester exhaustif, et avec quatre, dix — la version manuelle aurait cessé de tout
	# couvrir à la première échelle suivante, en silence. L'ordre de l'enum EST la hiérarchie
	# (`LIGHT < STANDARD < HEAVY`) : il suffit donc de vérifier chaque marche.
	var echelles: Array = TurretScale.values()
	for i in echelles.size() - 1:
		var petite: TurretScale = echelles[i]
		var grande: TurretScale = echelles[i + 1]
		var np := turret_scale_name(petite)
		var ng := turret_scale_name(grande)
		if turret_health_of(petite) >= turret_health_of(grande):
			errors.append("%s a %.0f PV pour %.0f à %s : elle ne tombe plus en passant, et la hiérarchie des échelles disparaît"
				% [np, turret_health_of(petite), turret_health_of(grande), ng])
		if turret_span_of(petite) >= turret_span_of(grande):
			errors.append("%s se voit sur %.1f pour %.1f à %s : une pièce plus petite ne se distingue pas d'aussi loin"
				% [np, turret_span_of(petite), turret_span_of(grande), ng])
		# ⚠️ LA CADENCE VA DANS L'AUTRE SENS, et ce n'est pas une inversion de signe distraite :
		# une petite tourelle tire MOINS souvent, parce qu'elle vient en groupe. La somme d'une
		# batterie doit rester sous la pièce du dessus, sinon le joueur apprend à craindre les
		# petites et la hiérarchie s'inverse sans qu'aucun nombre n'ait l'air faux.
		if turret_burn_interval_of(petite) <= turret_burn_interval_of(grande):
			errors.append("%s tire toutes les %.2f s pour %.2f s à %s : elles viennent en groupe, et un groupe plus dense que la pièce au-dessus inverse la hiérarchie"
				% [np, turret_burn_interval_of(petite), turret_burn_interval_of(grande), ng])
		# ⚠️ LA ROTATION AUSSI : « plus petite donc plus vive » est la contrepartie de la masse.
		# Une lourde qui suivrait aussi vite qu'une légère n'aurait aucun défaut à exploiter, et
		# ses 520 PV deviendraient une taxe au lieu d'une décision.
		if turret_turn_rate_of(petite) <= turret_turn_rate_of(grande):
			errors.append("%s pivote à %.0f °/s pour %.0f °/s à %s : la masse doit se payer en lenteur, sinon la grosse pièce n'a aucun défaut à exploiter"
				% [np, turret_turn_rate_of(petite), turret_turn_rate_of(grande), ng])

	# --- INVARIANT 4 : un pont laissé debout PRODUIT ---------------------
	# Sans quoi l'abattre ne serait pas une décision : c'est la pression qu'il exerce qui
	# donne sa valeur au choix de le faire taire.
	if bay_release_interval <= 0.0:
		errors.append("bay_release_interval doit être > 0 — un pont qui ne produit pas n'est pas une menace")
	elif bay_release_count <= 0:
		errors.append("bay_release_count doit être >= 1")
	else:
		var lachers := int(release_window() / bay_release_interval)
		if lachers < 2:
			errors.append("un pont ne lâche que %d fois pendant qu'il survole le terrain (%.1f s) — trop peu pour peser sur la décision de l'abattre"
				% [lachers, release_window()])

	# --- INVARIANT 4 bis : LE POOL D'UN PONT COUVRE SON PIRE CAS ---------
	# ⚠️ Un pont à court de coques cesse de produire sans que rien ne le dise, et sa menace
	# s'éteint toute seule — le joueur croirait l'avoir fait taire. Le pire cas se CALCULE :
	# c'est le nombre de lâchers que sa fenêtre autorise, fois la taille d'un lâcher.
	if bay_release_interval > 0.0 and bay_release_count > 0:
		var pire := (int(release_window() / bay_release_interval) + 1) * bay_release_count
		if bay_pool_size < pire:
			errors.append("le pool d'un pont tient %d coques pour %d lâchées au pire — il s'épuiserait en pleine fenêtre, et le pont semblerait s'être tu tout seul"
				% [bay_pool_size, pire])

	# --- INVARIANT 5 : les cadences ne sont pas nulles --------------------
	for pair in [["turret_burn_damage", turret_burn_damage], ["turret_range", turret_range],
			["turret_beam_half_width", turret_beam_half_width]]:
		if float(pair[1]) <= 0.0:
			errors.append("%s doit être > 0" % pair[0])

	# --- INVARIANT 6 : un télégraphe ne promet pas un tir hors de portée --
	# La diagonale du plan de vol ordinaire : une tourelle dans un coin, le joueur dans
	# l'autre. En dessous, le faisceau s'arrête avant sa cible alors que la ligne de visée
	# l'a désignée.
	var diagonale := GameplayPlane.BOUNDS.size.length()
	if turret_range > 0.0 and turret_range < diagonale:
		errors.append("portée de tourelle %.1f pour une diagonale de plan de %.1f — le télégraphe désignerait une cible que le faisceau n'atteint pas"
			% [turret_range, diagonale])

	# --- INVARIANT 8 : une tourelle abîmée reste une tourelle ------------
	# ⚠️ CE N'EST PAS UN GARDE-FOU DE CONFORT. Sa version précédente — l'extinction — a été
	# mesurée en jeu : 15 tourelles sur 17 neutralisées, un niveau vidé par sa propre
	# récompense, et une pièce immobile que le joueur a lue comme cassée. Les deux bornes qui
	# suivent disent la même chose dans les deux sens : l'affaiblissement doit se SENTIR, et il
	# ne doit jamais redevenir un silence.
	if turret_weakened_turn_factor <= 0.0:
		errors.append("turret_weakened_turn_factor doit être > 0 — une tourelle abîmée qui ne pivote plus se lit comme cassée, pas comme abîmée, et c'est le défaut que ce réglage corrige")
	elif turret_weakened_turn_factor < 0.2:
		errors.append("turret_weakened_turn_factor = %.2f : à ce point la rotation ne se voit plus, et l'extinction revient sous un autre nom"
			% turret_weakened_turn_factor)
	elif turret_weakened_turn_factor >= 1.0:
		errors.append("turret_weakened_turn_factor = %.2f : abattre un nœud ne changerait rien à la rotation, donc la récompense ne se sentirait pas"
			% turret_weakened_turn_factor)
	if turret_weakened_interval_factor <= 1.0:
		errors.append("turret_weakened_interval_factor doit être > 1 — sinon une tourelle abîmée tire aussi vite qu'intacte")
	elif scroll_speed > 0.0:
		# Combien de fois une tourelle abîmée mord ENCORE pendant qu'on la survole. En dessous de
		# deux, le joueur ne la voit jamais tirer et croit qu'elle est morte — ce qui nous
		# ramène exactement au défaut d'origine.
		#
		# ⚠️ ET C'EST L'ÉCHELLE LÉGÈRE QUI EST LE CAS SERRÉ, PAS LA LOURDE : elle a la fenêtre la
		# plus courte ET l'intervalle le plus long. Ne vérifier que la lourde laisserait passer
		# une batterie entière de pièces muettes — et une batterie muette se lit comme un décor,
		# pas comme une récompense.
		for scale in TurretScale.values():
			var intervalle := turret_burn_interval_of(scale)
			var fenetre := turret_span_of(scale)
			if intervalle <= 0.0 or fenetre <= 0.0:
				continue
			var traversee := fenetre / scroll_speed
			var morsures := traversee / (intervalle * turret_weakened_interval_factor)
			if morsures < 2.0:
				errors.append("%s abîmée ne tirerait que %.1f fois pendant sa fenêtre (%.1f s) : en dessous de deux morsures le joueur ne la voit jamais tirer et la croit morte"
					% [turret_scale_name(scale), morsures, traversee])

	# --- INVARIANT 9 : LA CITADELLE N'EST PAS UN BOSS, ET C'EST UN CHIFFRE ---
	#
	# ⚠️ LES DEUX BORNES DISENT LA MÊME CHOSE DANS LES DEUX SENS, et aucune n'est un confort.
	# Sous le plancher, le verrou tombe avant d'avoir été compris : le joueur traverse une
	# fortification de 500 m sans savoir ce qu'il vient de faire, et les deux relais n'ont servi
	# à rien. Au-dessus du plafond, ce n'est plus un verrou de level design, c'est un troisième
	# boss — et le brief l'interdit en une phrase (« ce n'est pas un boss »).
	# ⚠️ LE PLAFOND DU COMBAT A DISPARU, ET C'EST UN NOMBRE INVENTÉ QU'ON RETIRE. La première
	# écriture bornait le temps de tir à « 30 s » — un chiffre qui ne venait de nulle part, et
	# qui a refusé le bon réglage dès que l'occupation a été MESURÉE. Ce que le brief spécifie,
	# lui, est la durée de la SÉQUENCE : 30 à 45 s. Le combat n'a donc plus qu'un plancher — un
	# verrou qui tombe en quatre secondes n'est pas un verrou — et son plafond se DÉDUIT du
	# budget, freinage et ouverture retirés.
	const CITADEL_FIGHT_FLOOR := 12.0
	const CITADEL_LOCK_FLOOR := 30.0
	const CITADEL_LOCK_CEILING := 45.0
	if occupancy_citadel <= 0.0 or occupancy_citadel > 1.0:
		errors.append("occupancy_citadel est une part de temps, dans (0, 1]")
	elif occupancy_citadel > occupancy_hull:
		errors.append("occupancy_citadel = %.2f pour %.2f sur la coque ouverte : l'arène du verrou est PLUS étroite, la déclarer plus généreuse revient à se dimensionner contre soi-même"
			% [occupancy_citadel, occupancy_hull])
	if citadel_relay_health <= 0.0 or citadel_core_health <= 0.0:
		errors.append("les points de vie de la citadelle doivent être > 0")
	elif occupancy_citadel > 0.0 and reference_dps > 0.0:
		var combat := citadel_fight_time()
		if combat < CITADEL_FIGHT_FLOOR:
			errors.append("le verrou tient %.0f s de tir pour %.0f au moins : il tomberait avant d'avoir été compris, et les deux relais n'auraient servi à rien"
				% [combat, CITADEL_FIGHT_FLOOR])
		# ⚠️ CE QUE LE CRITÈRE CHRONOMÈTRE, ET RIEN D'AUTRE : du premier mètre de freinage à la
		# route praticable. La partie du 2026-09-04 a mesuré 55,1 s là où ce réglage en
		# promettait 29 — c'est cette borne, une fois l'occupation honnête, qui a refusé les
		# 3 800 PV d'origine.
		var verrou := citadel_lock_time()
		if verrou > CITADEL_LOCK_CEILING or verrou < CITADEL_LOCK_FLOOR:
			errors.append("le verrou dure %.0f s, hors de la fourchette %.0f–%.0f du brief — freinage %.1f s, combat %.1f s, ouverture %.1f s"
				% [verrou, CITADEL_LOCK_FLOOR, CITADEL_LOCK_CEILING,
					citadel_brake_time(), combat, citadel_open_time])
	if citadel_open_time <= 0.0 or citadel_resume_time <= 0.0 or citadel_brake_span <= 0.0:
		errors.append("freinage, ouverture et reprise de la citadelle doivent être > 0 — un verrou qui s'arrête et repart d'un coup n'a pas de séquence")

	# --- INVARIANT 10 : « GAUCHE + DROITE → CENTRE » se lit dans les PV -----
	# ⚠️ SANS LUI, LE VERROU S'INVERSE EN SILENCE. Le noyau est ce que les deux relais
	# protègent : un noyau moins cher qu'un seul d'entre eux ferait de la protection l'obstacle
	# et de l'objectif une formalité, et la règle que la planche explique sans un mot de HUD
	# deviendrait fausse à l'usage sans qu'aucune capture ne le montre.
	if citadel_core_health > 0.0 and citadel_relay_health > 0.0 \
			and citadel_core_health < citadel_relay_health:
		errors.append("le noyau a %.0f PV pour %.0f à un relais : ce qui protège coûterait plus cher que ce qu'il protège, et la lecture « gauche + droite → centre » s'inverse"
			% [citadel_core_health, citadel_relay_health])

	# --- INVARIANT 11 : LE MUR LAISSE UNE ARÈNE, ET IL EST DANS LE PLAN -----
	#
	# ⚠️ LES DEUX BORNES SONT GÉOMÉTRIQUES, PAS ESTHÉTIQUES. Trop haut, le mur sort du plan de
	# vol : il ne bloque plus rien, et l'arrêt du survol devient un temps mort où le joueur
	# attend sans comprendre. Trop bas, il ne reste plus de terrain — la chambre du réacteur a
	# déjà payé ce défaut, mesuré : « c'est comme si tout le cercle était un mur pour moi ».
	const CITADEL_ARENA_FLOOR := 9.0
	const CITADEL_WALL_MARGIN := 2.0
	if citadel_arena_height() < CITADEL_ARENA_FLOOR:
		errors.append("le mur à y = %.1f ne laisse que %.1f unités d'arène pour %.1f au moins — un lieu où l'on ne peut pas exister n'est pas un terrain"
			% [citadel_wall_plane_y, citadel_arena_height(), CITADEL_ARENA_FLOOR])
	if citadel_wall_plane_y > GameplayPlane.BOUNDS.end.y - CITADEL_WALL_MARGIN:
		errors.append("le mur à y = %.1f sort du plan de vol (plafond %.1f) : il n'arrêterait plus personne, et l'arrêt du survol deviendrait un temps mort"
			% [citadel_wall_plane_y, GameplayPlane.BOUNDS.end.y])

	# --- INVARIANT 12 : LE VERROU EST SUR LA COQUE, PAS DEVANT ELLE --------
	# Une station hors du survol donnerait un verrou qui ne se déclenche jamais — et un niveau
	# qui se joue exactement comme avant, sans une ligne au journal.
	if citadel_station <= 0.0 or citadel_station >= section_length * float(section_count):
		errors.append("la citadelle est à s = %.0f, hors du survol (0 à %.0f) : elle ne se déclencherait jamais"
			% [citadel_station, section_length * float(section_count)])

	return errors
