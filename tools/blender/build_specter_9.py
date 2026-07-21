"""build_specter_9.py — coque 3D du Specter-9, chasseur du joueur.

    ./scripts/build-hull.sh specter_9          (JAMAIS `blender45 -b -P` a la main :
    ./scripts/build-hull.sh --check specter_9   le script force `-t 1`, sans quoi les
                                                tangentes divergent d'un run a l'autre)

Produit `assets/imported/models/ships/specter_9.glb` : une coque + SIX pieces
mobiles exportees en nœuds glTF separes (`Wing_L/R`, `Flap_L/R` — enfants des
ailes —, `Nozzle_L/R`).

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (aucun alea non seede) et s'auto-valide : `ak.export_hull()`
relit le `.glb` produit et echoue bruyamment si la bounding box, le budget de
triangles, les materiaux, le centrage du pivot ou les points d'attache sortent
du contrat.

Repere d'auteur (ADR-0008) : nez -Y, dessus +Z, **babord +X** (cf. aegis_kit).


PASSE DE TOPOLOGIE — BRIEF-0035 (la seule qui compte ici)
=========================================================
BRIEF-0033 a corrige le profil, BRIEF-0034 la repartition des masses. Aucun des
deux n'a touche au defaut reel, nomme par le proprietaire :

    « on a un triangle monobloc, alors que l'artwork reprend le principe du
      fuselage, et des ailes »

Les deux passes precedentes dessinaient des lignes sur UNE surface continue. Le
critere de ce brief est binaire et se lit sur un aplat noir vu de dessus : **du
fond doit passer ENTRE les volumes**. Ce que ce script change :

1. **La coque principale n'est plus que le FUSELAGE.** `PLANFORM` ne decrit plus
   une aile delta de 1,75 m d'envergure mais un corps de 0,30 m de large, ferme
   sur lui-meme, avec ses propres flancs verticaux (`EDGE_H` passe de 12 a
   88 mm : le bord de la section cesse d'etre une tranche d'aile et devient un
   borde de 0,18 m de haut).
2. **Chaque nacelle est un corps ferme et separe.** Le fuseau court desormais de
   y = -0,440 (levre d'entree d'air) a y = 1,230 (levre de tuyere) — c'est un
   volume autonome, plus un bossage noye dans l'aile. `SHOULDER` et `INTAKE`,
   qui n'existaient que pour raccorder le fuseau au plan d'aile, disparaissent.
3. **Deux FENTES traversantes par cote.** Entre le flanc du fuselage (x = 0,150)
   et le flanc interne de la nacelle (x = 0,209) il y a 59 mm d'air. Un seul
   element les relie : le caisson `BRIDGE` (y = 0,010 a 0,380). En avant et en
   arriere de lui, on voit le fond de l'image.
4. **Les ailes sont des lames distinctes, mobiles.** `Wing_L/R` pivotent autour
   d'un axe VERTICAL place au flanc externe de la nacelle. Leur emplanture
   (x = 0,545) est a 94 mm de la peau du fuseau : troisieme fente par cote.
5. **`Flap_L/R` sont les ENFANTS des ailes** (`ak.moving_part(parent=...)`),
   sans quoi un volet resterait en l'air des que l'aile bouge.
6. **Le caniveau (`GUTTER_*`) disparait.** C'etait un ersatz de fente creuse
   dans une surface continue ; la fente est maintenant reelle.

⚠️ Le contrat de bounding box est mesure AU REPOS. Une aile qui deborde une fois
repliee le passerait sans un mot — c'est le meme piege qui avait fait tomber le
debattement d'un volet a 2,8 deg sous BRIEF-0034. `_wing_sweep_limit()` remesure
donc a chaque build, sur le maillage livre, l'angle de fleche admissible en
tenant compte des trois contraintes : peau de nacelle, boite englobante, et
croisement avec le fuselage.


PASSE DE PLAN — BRIEF-0034 (lire ADR-0014 d'abord)
==================================================
BRIEF-0033 avait pose comme prealable de **conserver le delta** (« le probleme
est le profil, pas le plan »). C'etait une erreur de diagnostic, tiree d'un
rapport de boite englobante — une statistique qui mesure la boite, jamais la
repartition des masses dedans. ADR-0014 la corrige et autorise la reprise du
PLAN de la planche de reference, derives comprises.

Ce que ce brief change, et rien d'autre : la **vue de dessus**.

1. **L'aile cesse d'etre un delta.** `PLANFORM` avait sa largeur maximale a
   67 % de la longueur puis un culot plein : l'aile remplissait tout l'arriere.
   Le bord d'attaque passe de 52 a **62 deg de fleche**, la largeur maximale
   recule a 73 % (y = 0,580) et le bord de fuite, jusqu'ici droit, est **rake a
   28 deg** : la corde s'effondre en arriere du bout d'aile. L'envergure, elle,
   NE BOUGE PAS (0,875 m) — c'est la corde qui tombe, pas la portee.
2. **Un fuselage central porteur.** `FUSELAGE` retrecit (0,232 -> 0,172 de
   demi-largeur, soit 0,344 m = 20 % de l'envergure, dans la fourchette du
   brief) mais devient un VOLUME : le plan d'aile ne part plus de 0,65 fois
   l'epine mais de **0,34** (`WING_ROOT_FRAC`), ce qui creuse une marche de
   9 cm au flanc du fuselage la ou il n'y avait qu'un bombement continu.
3. **Une rainure, pas une jointure.** `GUTTER_DEPTH` creuse un caniveau de
   30 mm au pied de cette marche : c'est lui qui separe optiquement le
   fuselage des nacelles au lieu de les laisser fondre l'un dans l'autre.
4. **Deux nacelles longues.** Ecartees (0,268 -> 0,352), legerement affinees
   (rayon x 0,915) et surtout **prolongees vers l'avant** par une epaule
   (`SHOULDER`) qui court de y = -0,36 a y = 0,86. Nacelle + epaule = 1,59 m,
   soit **65 % de la longueur** (le brief en demandait 60-75 %).
5. **Deux derives inclinees** a 30 deg vers l'exterieur, sur le dessus des
   nacelles (`FIN`). Elles remplacent les rails verticaux de bout d'aile, qui
   n'existaient que parce que BRIEF-0033 s'interdisait les derives ; il ne
   reste au bout d'aile qu'une **lisse basse** (`RAIL`), qui epaissit la lame.
6. **Une tuyere d'axe** en bout de fuselage (`TAIL_NOZZLE`) : c'est elle qui
   fait lire le fuselage comme porteur jusqu'a la poupe, et non comme une
   arete qui s'arrete.

Ce qui est CONSERVE de BRIEF-0033, sans y toucher : le profil superpose, la
densite de panneautage, les nacelles en volumes propres, les 4 pieces mobiles,
les 10 points d'attache.


PASSE FUSELAGE ET PIECES MOBILES — BRIEF-0033
=============================================
La passe de detail de BRIEF-0031 avait sorti la coque du « jouet » en vue de
dessus, mais la vue de profil restait une **plaque** : 0,516 m de haut pour
2,46 m de long (21 %), aucune structure verticale, des nacelles noyees dans
l'aile. Six leviers, par ordre de rendement :

1. **Profil epaissi ET stratifie.** Le corps passe de 0,315 a 0,380 m
   (CROWN/BELLY), mais surtout la coque cesse d'etre UNE lentille : elle empile
   desormais six couches lisibles de bas en haut — quille ventrale, ecopes de
   nacelle, plan d'aile, corps de fuselage, arete dorsale, verriere. C'est
   l'empilement, pas l'epaisseur brute, qui fait la lecture « appareil ».
2. **Repartition asymetrique de l'epaisseur.** La camera de jeu regarde a 20 deg
   de la verticale : ce qu'on ajoute AU-DESSUS elargit la silhouette vue de
   dessus, ce qu'on ajoute EN DESSOUS est gratuit. 55 % de la hauteur est donc
   sous le plan d'aile, et les volumes dorsaux sont ETROITS (arete de 0,19 m de
   large sur une envergure de 1,75 m).
3. **Nacelles en volumes propres** : ecartees (0,235 -> 0,268), descendues
   (-0,030 -> -0,062), avec col, collier, jonc, et une **ecope ventrale** qui les
   relie a l'aile. Elles saillent de 0,13 m sous l'aile.
4. **Nez plus long** : la verriere recule de 0,13 m, le maitre-couple avant
   s'affine (CROWN et FUSELAGE abaisses en avant de y = -0,80). Le rapport
   longueur/envergure ne bouge pas : c'est la REPARTITION des masses qui change.
5. **Presence verticale sans derive** : deux **rails verticaux de bout d'aile**
   (0,20 m de haut, feux cyan sur l'arete) et une **arete dorsale basse** a
   flancs verticaux. Aucune derive inclinee — voir la note IP ci-dessous.
6. **Pieces mobiles** (`ak.moving_part`, kit etendu pour ce brief) : volets de
   bord de fuite et couronnes de petales de tuyere, chacun avec son origine sur
   son articulation.

Regle de placement inchangee : **si une surface n'est pas visible depuis une
camera a 20 deg de la verticale, ce qu'on y met n'existe pas.**


REFERENCE ET LIMITE IP  (revu par ADR-0014)
===========================================
Cible : `assets/reference/inspiration/reference_specter_9_design_sheet.png`
(planche TIERCE). ADR-0009 l'autorisait comme inspiration ; **ADR-0014 va plus
loin pour CETTE coque seulement** et autorise la reprise de son ARCHITECTURE :
fuselage porteur, nacelles flanquantes, ailes en lames, doubles derives
inclinees. La clause « les assets produits restent originaux » d'ADR-0009 ne
s'applique plus ici — et continue de s'appliquer partout ailleurs dans le jeu.

DEUX traits restent EXCLUS, et ce n'est pas une demi-mesure de prudence :
  * la livree tricolore a bandes rouges -> la palette du kit reste seule
    maitresse (blanc casse, bleu profond, or ; rouge en marquage restreint).
    Un appareil tricolore serait un corps etranger dans une flotte ivoire et
    bleue, independamment de toute question de droits ;
  * tout badge numerote, chiffre, texte, logo ou insigne -> aucun, nulle part.

Si le projet devait etre distribue, ce fichier et le .glb qu'il produit sont
les premiers a refaire (ADR-0014, §Consequence).
"""

from __future__ import annotations

import math
import os
import sys

import bmesh

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402  (doit suivre l'ajout au sys.path)

# ==========================================================================
# Contrat (ADR-0008 pour les dimensions, ADR-0011 pour le budget)
# ==========================================================================

#: Fourchette de hauteur imposee par BRIEF-0034 (0,62-0,72 : le plafond monte
#: de 4 cm pour loger les derives). Le contrat du kit ne sait borner qu'un
#: PLAFOND : le plancher est verifie a la main en fin de build, sinon un
#: vaisseau reste plat en toute conformite.
MIN_HEIGHT_Y = 0.62
MAX_HEIGHT_Y = 0.72

CONTRACT = ak.HullContract(
    name="Specter-9",
    width_x=1.75,       # Godot X — INCHANGE (contrat de gameplay : hitbox)
    length_z=2.46,      # Godot Z — INCHANGE
    # BRIEF-0034 : 0,62-0,72 m, soit 25-29 % de la longueur. Cela DEPASSE la
    # fourchette indicative d'ADR-0008 (15-25 %), et c'est explicitement
    # autorise par le brief : le defaut a corriger etait la platitude.
    max_height_y=MAX_HEIGHT_Y,
    tri_budget=60_000,  # ADR-0011 (releve depuis 15 000)
    required_materials=ak.MATERIAL_ORDER,  # les 7 : la planche les utilise tous
    required_attach_points=(
        "Muzzle_L",       # twin de nez, babord   (power 1+)
        "Muzzle_R",       # twin de nez, tribord
        "Muzzle_Wing_L",  # canon d'aile, babord  (power 3)
        "Muzzle_Wing_R",  # canon d'aile, tribord
        "Muzzle_C",       # canon d'axe central   (power 4)
        "Muzzle_Tip_L",   # pod de bout d'aile, babord (power 5)
        "Muzzle_Tip_R",   # pod de bout d'aile, tribord
        "Engine_L",
        "Engine_R",
        "Cockpit",
    ),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/ships/specter_9.glb")

SEED = 90210  # graine unique du Specter-9 (determinisme des greebles)

#: Echelle de repetition de la feuille de detail (ADR-0011 §2), en tuiles/metre.
#: Validee au rendu par BRIEF-0031 : une tuile couvre 25 cm, soit ~7 tuiles en
#: envergure et ~10 en longueur. Le brief demande de ne pas y toucher.
TEXELS_PER_METER = 4.0

HALF_L = CONTRACT.length_z / 2.0   # 1.230 — nez en -Y, poupe en +Y
HALF_W = CONTRACT.width_x / 2.0    # 0.875 — bout d'aile

# ==========================================================================
# Tables de profil
# ==========================================================================

# --------------------------------------------------------------------------
# Le PARTAGE DE LA DEMI-ENVERGURE (BRIEF-0035) — c'est ici que tout se joue.
# --------------------------------------------------------------------------
# La demi-envergure de 0,875 m n'est plus occupee par une seule surface mais par
# CINQ zones, dont deux sont du vide. Le total est un invariant a verifier a la
# main a chaque retouche, et `_print_silhouette_gaps()` le remesure a chaque
# build sur la geometrie reelle :
#
#     0,000 .. 0,130   fuselage (demi-largeur maximale)
#     0,130 .. 0,172   FENTE 1   —  42 mm d'air
#     0,172 .. 0,368   nacelle   (axe 0,270, rayon 0,098 ; collier 0,105)
#     0,368 .. 0,426   FENTE 2   —  58 mm d'air
#     0,426 .. 0,875   aile      (lame mobile, 449 mm de portee exposee)
#
# Ce partage a ete revu au RENDU : la premiere version donnait 0,150 / 0,121 au
# corps et il ne restait que 330 mm d'aile. L'aplat noir montrait bien les
# trouees demandees, mais le vaisseau lisait « trois tubes », plus « chasseur ».
# Le groupe central a donc maigri de 13 % au profit de la lame.
#
# Rien de tout cela ne serait visible si les fentes etaient bouchees sur toute
# la longueur : ce qui les ouvre, c'est que chaque corps a une ETENDUE EN Y
# differente. La nacelle court de -0,440 a 1,230, le fuselage de -1,230 a 1,230,
# l'aile de 0,246 a 0,593 seulement. Le seul point de contact voulu est le
# caisson `BRIDGE` (y = 0,010 a 0,380) — d'ou deux ouvertures par fente.

#: Demi-largeur du FUSELAGE (la coque principale ne decrit plus rien d'autre).
#: Cette table s'appelait `PLANFORM` et decrivait une aile delta ; le nom est
#: conserve parce que c'est toujours le contour en plan de la coque loftee, mais
#: la coque loftee n'est plus que le corps central.
PLANFORM: list[tuple[float, float]] = [
    (-1.2300, 0.0000),   # pointe du nez
    (-1.1500, 0.0165),
    (-1.0800, 0.0269),
    (-0.9800, 0.0416),
    (-0.9000, 0.0533),
    (-0.8000, 0.0672),
    (-0.6800, 0.0836),
    (-0.5400, 0.0992),
    (-0.4000, 0.1114),
    (-0.2400, 0.1213),
    (-0.0500, 0.1283),
    (0.1300, 0.1300),    # maitre-couple : 0,260 m de large
    (0.3100, 0.1287),
    (0.4700, 0.1239),
    (0.6100, 0.1166),
    (0.7600, 0.1053),
    (0.9000, 0.0923),
    (1.0300, 0.0780),    # culot de la poutre arriere, ou se pose la tuyere d'axe
]

#: Demi-largeur du NOYAU de pont : au-dela commence la joue, en pente douce
#: jusqu'au borde vertical. La marche entre les deux (segment `FLANK_SEG`) est
#: le flanc superieur du fuselage — la seule surface quasi verticale que la
#: camera de jeu voit du corps central.
FUSELAGE: list[tuple[float, float]] = [
    (-1.2300, 0.0000),
    (-1.1500, 0.0100),
    (-1.0800, 0.0165),
    (-0.9800, 0.0256),
    (-0.9000, 0.0329),
    (-0.8000, 0.0416),
    (-0.6800, 0.0520),
    (-0.5400, 0.0620),
    (-0.4000, 0.0698),
    (-0.2400, 0.0758),
    (-0.0500, 0.0802),
    (0.1300, 0.0815),
    (0.3100, 0.0806),
    (0.4700, 0.0776),
    (0.6100, 0.0728),
    (0.7600, 0.0659),
    (0.9000, 0.0576),
    (1.0300, 0.0485),
]

# Hauteur de l'epine dorsale (z du sommet, sur l'axe).
# BRIEF-0033 : sommet 0.165 -> 0.195, mais surtout la courbe est RECULEE. Le
# maitre-couple etait a y = 0.05 ; il est desormais a y = 0.22, et l'avant est
# abaisse. C'est ce deplacement, plus que le gain de 3 cm, qui allonge le nez.
#: BRIEF-0034 : le sommet gagne 1 cm (0,195 -> 0,205). Le fuselage ayant perdu
#: 6 cm de largeur, sans cela il aurait perdu du volume au lieu d'en gagner.
#: BRIEF-0035 : prolongee jusqu'a y = 1,030. Le fuselage ne s'arrete plus a
#: 0,860 « entre les deux nacelles » — il a maintenant une poutre arriere propre,
#: et c'est elle qui, en depassant entre les deux fuseaux, ouvre la fente 1 par
#: l'arriere au lieu de la refermer.
CROWN: list[tuple[float, float]] = [
    (-1.2300, 0.000),
    (-1.1500, 0.026),
    (-1.0800, 0.040),
    (-0.9250, 0.070),
    (-0.8120, 0.094),
    (-0.6910, 0.122),
    (-0.5510, 0.152),
    (-0.4130, 0.174),
    (-0.2410, 0.192),
    (0.0540, 0.202),
    (0.2190, 0.205),
    (0.4180, 0.203),
    (0.5730, 0.196),
    (0.7450, 0.186),
    (0.8600, 0.178),
    (0.9600, 0.170),
    (1.0300, 0.162),
]

# Profondeur du ventre (z du bas, sur l'axe ; valeurs negatives).
BELLY: list[tuple[float, float]] = [
    (-1.2300, 0.000),
    (-1.1500, -0.024),
    (-1.0800, -0.036),
    (-0.9250, -0.064),
    (-0.8120, -0.086),
    (-0.6910, -0.110),
    (-0.5510, -0.136),
    (-0.4130, -0.158),
    (-0.2410, -0.172),
    (0.0540, -0.182),
    (0.2190, -0.185),
    (0.4180, -0.183),
    (0.5730, -0.177),
    (0.7450, -0.168),
    (0.8600, -0.160),
    (0.9600, -0.152),
    (1.0300, -0.146),
]

# ==========================================================================
# Ailes a fleche variable (pieces mobiles) et leurs volets (pieces ENFANTS)
# ==========================================================================
#
# TOUTE la geometrie de l'aile est exprimee en POLAIRE autour du pivot, et c'est
# la seule chose qui rend le degagement demontrable au lieu d'espere :
#
#   * une rotation autour du pivot conserve le rayon `r` et ajoute `theta` a
#     l'angle `phi` ;
#   * si TOUS les points de l'aile ont `phi >= 0` au repos et `phi + theta <= 90`
#     en fleche maximale, alors `x = x_pivot + r cos(phi)` ne fait que DECROITRE
#     quand on replie. L'aile ne peut donc ni sortir de la boite englobante en
#     largeur, ni traverser une nacelle situee en deca de `x_pivot`.
#
# Le pivot est pose 21 mm en dehors de la peau du fuseau (0,451) : l'aile est
# bien « greffee au flanc externe de la nacelle » comme le demande le brief, et
# la fente reste ouverte entre les deux.
#
# ⚠️ La demonstration ci-dessus vaut pour un plan ; le maillage a une epaisseur
# et des details. `_wing_sweep_limit()` la REMESURE sommet par sommet a chaque
# build. Sans cela on retombe exactement sur le piege de BRIEF-0034, ou le
# contrat — qui ne connait que la pose de repos — a valide un volet dont le
# debattement reel etait tombe a 2,8 deg.

WING_PIVOT_X = 0.3980     # flanc externe de la nacelle (peau a 0,368)
WING_PIVOT_Y = 0.0300
WING_PIVOT_Z = 0.0120

#: Bord d'attaque et bord de fuite, en (rayon, angle au pivot en degres), de
#: l'emplanture au bout d'aile. Les rayons du bout sont calcules pour que
#: `x = WING_PIVOT_X + r cos(phi)` tombe EXACTEMENT sur 0,875 : l'envergure est
#: un contrat de gameplay (hitbox), elle ne se laisse pas approcher.
#: L'angle de l'emplanture du bord de fuite (60 deg) est la valeur CRITIQUE : la
#: garantie de degagement demande `phi + fleche <= 90`, il ne reste donc que
#: 30 deg de marge, dont 26 sont consommes par la fleche visee. C'est aussi lui
#: qui fixe la corde d'emplanture (0,44 m) : la premiere version, a 56 deg et
#: r = 0,34, donnait une lame de 0,32 m de corde qui lisait « aileron » et non
#: « aile » — vu au rendu d'aplat, pas devine.
WING_TIP_X = HALF_W
WING_LE_ROOT = (0.0280, 8.0)
WING_LE_TIP_ANGLE = 28.0
WING_TE_ROOT = (0.4600, 60.0)
WING_TE_TIP_ANGLE = 44.0

#: Fleche visee (deg). Le brief demande 20 a 30 ; la valeur reellement admissible
#: est REMESUREE a chaque build et le script echoue si elle passe sous ce seuil.
WING_SWEEP_TARGET = 26.0
#: Garde minimale entre l'aile repliee et la peau de la nacelle.
WING_CLEARANCE = 0.012

#: Nombre de nervures (stations d'envergure) et fractions de corde.
#: Les paires serrees (0.300/0.345 et 0.700/0.745) portent les deux rainures
#: longitudinales de l'aile — en FRACTION DE CORDE, jamais en metres
#: (`.claude/resources/pratique-detail-en-fraction-de-corde.md`).
WING_RIBS: tuple[float, ...] = (0.000, 0.180, 0.360, 0.540, 0.720, 0.880, 1.000)
WING_CHORD_T: tuple[float, ...] = (
    0.000, 0.070, 0.170, 0.300, 0.345, 0.500, 0.700, 0.745, 0.880, 1.000,
)
#: Demi-epaisseur maximale de la lame, a l'emplanture puis au bout d'aile.
WING_THICK_ROOT = 0.0300
WING_THICK_TIP = 0.0130
#: Affaissement du bout d'aile (lu sur la vue arriere de la planche).
WING_ANHEDRAL = 0.0260

#: Charniere du volet : une DROITE parallele a X, comme avant BRIEF-0035.
#: Ce n'est pas de la paresse — le volet est un ENFANT de l'aile, et `moving_part`
#: n'exporte qu'une translation (jamais de rotation) : les axes locaux du volet
#: sont ceux de l'aile. Une charniere parallele a l'axe X de l'aile est donc la
#: seule qui reste un axe de nœud une fois l'aile en fleche.
FLAP_HINGE_Y = 0.3820
FLAP_GAP = 0.0110         # jeu de charniere (l'aile s'arrete a HINGE_Y - GAP)
#: Cloison : la coupe du bord de fuite de l'aile. C'est elle que le volet mord
#: quand on le braque trop, et c'est elle que `_flap_travel_limit()` interroge.
FLAP_WALL_Y = FLAP_HINGE_Y - FLAP_GAP
FLAP_HINGE_Z = 0.0060
#: Corde minimale du volet a son emplanture. En deca, l'aile garde son bord de
#: fuite plein : un logement creuse la ou il n'y a pas de volet pour le remplir
#: est un trou, pas une articulation.
FLAP_MIN_CHORD = 0.026
#: Stations du volet, de la charniere vers le bord de fuite.
FLAP_STATIONS: tuple[float, ...] = (0.4700, 0.4960, 0.5220, 0.5480, 0.5740, 0.5930)

# ==========================================================================
# Stations longitudinales
# ==========================================================================

#: Stations longitudinales de base (la premiere est la pointe du nez).
#: BRIEF-0035 : la trame arriere est prolongee jusqu'a 1,030 — le fuselage ne
#: s'arrete plus a 0,860 mais porte une poutre qui sort entre les deux nacelles.
BASE_STATIONS: tuple[float, ...] = (
    -1.2300, -1.1900, -1.1400, -1.0800, -1.0200, -0.9600, -0.9000, -0.8400,
    -0.7800, -0.7200, -0.6600, -0.6000, -0.5400, -0.4700, -0.4000, -0.3300,
    -0.2600, -0.2000, -0.1300, -0.0500, 0.0400, 0.1300, 0.2200, 0.3100,
    0.4000, 0.4700, 0.5400, 0.6100, 0.6890, 0.7600, 0.8100, 0.8600,
    0.9200, 0.9800, 1.0300,
)

#: Stations ajoutees hors trame reguliere.
EXTRA_STATIONS: tuple[float, ...] = ()

#: Rainures TRANSVERSALES : centre de la bande, et etendue laterale.
#: "fus" = coeur du fuselage seul (l'aile y est trop mince pour porter une
#: rainure sans degenerer), "all" = toute la largeur.
#: Chaque centre est pris au MILIEU d'un intervalle de `BASE_STATIONS` : la
#: paire de stations serrees y decoupe deux bandes residuelles de largeur egale.
#: Decale, un centre laisserait une bande de 8 mm — trop mince pour porter quoi
#: que ce soit, et de la geometrie payee pour rien.
#: Un intervalle de base qui porte une rainure doit mesurer au moins
#: 2 x MIN_BAND + 2 x SEAM_HALF = 49 mm, sans quoi les deux bandes RESIDUELLES
#: passent elles aussi sous le seuil de detection (17,5 mm) et sont prises pour
#: des rainures. Le piege est silencieux : le build reussit, et la coque sort
#: avec trois rainures collees la ou on en voulait une.
#: BRIEF-0033 : 11 -> 19 rainures. BRIEF-0034 : 19, redistribuees. BRIEF-0035 :
#: 21, la trame courant desormais jusqu'a la poutre arriere (0,890 / 0,950).
LATERAL_SEAMS: tuple[tuple[float, str], ...] = (
    (-0.9900, "fus"),
    (-0.8700, "fus"),
    (-0.7500, "fus"),
    (-0.6300, "all"),
    (-0.5700, "all"),
    (-0.4350, "all"),
    (-0.3650, "all"),
    (-0.2300, "all"),
    (-0.0900, "all"),
    (-0.0050, "all"),
    (0.0850, "all"),
    (0.1750, "all"),
    (0.2650, "all"),
    (0.3550, "all"),
    (0.4350, "all"),
    (0.5050, "all"),
    (0.5750, "all"),
    (0.6495, "all"),
    (0.7245, "all"),
    (0.8900, "all"),
    (0.9500, "all"),
)

#: Demi-largeur d'une bande de rainure transversale : la bande fait 14 mm.
SEAM_HALF = 0.0070
#: Retrait et profondeur d'une rainure. 5 mm de creux : a 2 mm le chanfrein
#: mangeait la marche et la rainure disparaissait a 20 deg de la verticale.
SEAM_T, SEAM_D = 0.0018, -0.0050

# --- Garde-fou contre l'explosion des insets ------------------------------
# `bmesh.ops.inset_region(use_even_offset=True)` divise le retrait par le sinus
# de l'angle au coin : sur une zone plus etroite que deux fois le retrait, les
# sommets partent a l'infini. Ce n'est pas theorique — la premiere version de
# la passe de detail sortait une coque de 2,44 m de haut, avec des sommets
# projetes a x = 0,75 m sur une aile qui n'en fait que 0,17 a cette station.
#
# Le retrait ne s'applique qu'au CONTOUR de la zone, pas aux aretes interieures :
# la grandeur a controler est donc la largeur d'un TRONCON CONTIGU de cellules,
# jamais celle d'une cellule isolee. `cells()` groupe et filtre pour cela.
#: Rainures (retrait 1,8 mm).
MIN_RUN_SEAM, MIN_EDGE_SEAM, MIN_BAND_SEAM = 0.0050, 0.0040, 0.0100
#: Panneaux. BRIEF-0035 : le fuselage ne fait plus que 0,30 m de large et la
#: joue 56 mm ; les seuils de BRIEF-0034 (50 mm de troncon) auraient eteint
#: SILENCIEUSEMENT tous les panneaux du corps central. Le retrait cumule tombe
#: donc de 15 a 9 mm (`plate()`) et les seuils suivent.
MIN_RUN_PLATE, MIN_EDGE_PLATE, MIN_BAND_PLATE = 0.0220, 0.0090, 0.0240


def _stations() -> list[float]:
    """Stations = base + extras + une PAIRE serree par rainure transversale.

    Une rainure a besoin d'une bande de faces etroite : on l'obtient en
    inserant deux stations distantes de 14 mm autour de son centre. La bande
    ainsi creee est identifiee plus tard a sa seule largeur (< 20 mm), ce qui
    evite de trimballer des index fragiles.
    """
    out = list(BASE_STATIONS) + list(EXTRA_STATIONS)
    for y, _ in LATERAL_SEAMS:
        out += [y - SEAM_HALF, y + SEAM_HALF]
    return sorted(out)


STATIONS: list[float] = _stations()

# --- Le borde : ce qui fait qu'un fuselage n'est pas une aile -------------
# BRIEF-0035. `EDGE_H` etait la demi-epaisseur du BORD D'AILE : 12 mm, une
# tranche de couteau. Le bord de la section n'est plus un bord d'aile mais le
# FLANC du fuselage : 88 mm au-dessus du plan, ~98 mm en dessous, soit un borde
# vertical de 0,186 m. C'est ce borde qui rend le corps central lisible comme un
# volume ferme une fois qu'il n'y a plus d'aile pour le prolonger.
EDGE_H = 0.088
ANHEDRAL = 0.010    # tres leger tombant de la joue vers le borde
SPINE_HW = 0.044    # demi-largeur du sillon dorsal

#: Cote de la JOUE a son raccord au pont, en fraction de l'epine. La branche
#: interne rend 0,65 x epine au meme x : la marche entre les deux vaut donc
#: (0,65 - 0,42) x epine ~ 47 mm au maitre-couple, franchie sur `CHEEK_T[3]`
#: (18 % de la joue, 10 mm) — un flanc a ~78 deg.
#: (Le caniveau `GUTTER_*` de BRIEF-0034 a disparu : c'etait un ersatz de fente
#: creuse dans une surface continue. La fente est maintenant reelle.)
CHEEK_FRAC = 0.42

# Verriere : (y, demi-largeur, hauteur au-dessus de son assise).
# BRIEF-0035 : retrecie de 0,104 a 0,076 de demi-largeur. Le pont ne fait plus
# que 0,094 de demi-largeur a cette station ; a 0,104 la verriere debordait sur
# la joue et le puits vitre se serait ouvert dans le flanc.
CANOPY: list[tuple[float, float, float]] = [
    (-0.6600, 0.0000, 0.000),
    (-0.6300, 0.0225, 0.040),
    (-0.5900, 0.0399, 0.076),
    (-0.5400, 0.0537, 0.108),
    (-0.4800, 0.0624, 0.132),
    (-0.4150, 0.0659, 0.142),
    (-0.3500, 0.0659, 0.140),
    (-0.2850, 0.0624, 0.128),
    (-0.2200, 0.0563, 0.104),
    (-0.1700, 0.0468, 0.074),
    (-0.1300, 0.0347, 0.040),
    (-0.1000, 0.0000, 0.000),
]
CANOPY_SINK = 0.026  # assise de la verriere, sous la ligne d'epine

# ==========================================================================
# Nacelles
# ==========================================================================

# BRIEF-0033 : ecartees et descendues. BRIEF-0034 : ecartees davantage.
# BRIEF-0035 : la nacelle devient un **corps ferme et autonome**, du nez a la
# tuyere. Ce n'est plus un bossage pose sur une aile : le profil de revolution
# court de y = -0,440 (levre d'entree d'air) a y = 1,048 (col), soit 1,49 m —
# 60 % de la longueur — et se ferme sur lui-meme aux deux bouts.
#
# Les deux abscisses qui comptent, et qu'on ne touche pas sans refaire tout le
# partage de la demi-envergure documente plus haut :
#   * bord INTERNE  = 0,270 - 0,098 = 0,172  ->  42 mm d'air jusqu'au fuselage ;
#   * bord EXTERNE  = 0,270 + 0,098 = 0,368  ->  30 mm jusqu'au pivot d'aile.
NACELLE_X = 0.270      # ecartement des axes
NACELLE_Z = -0.040     # axes sous le plan du pont
NACELLE_SEGMENTS = 24  # les tuyeres sont le point focal arriere : on les paie rondes

#: Rayon courant du fuseau (hors collier) — sert aux mesures de degagement.
NACELLE_R = 0.098

# Profil de revolution de la nacelle : (y, rayon, materiau du segment sortant).
# Le profil s'arrete au COL (y = 1.048) : au-dela c'est la couronne de petales,
# qui est une piece mobile exportee a part.
# ⚠️ Le dernier rayon (0.077) est repris a l'identique par `NOZZLE_BORE[0]` et
# par `PETAL_SECTIONS[0]` : les trois doivent bouger ENSEMBLE, sinon la vasque
# emissive decroche du col et on voit au travers.
NACELLE_PROFILE: list[tuple[float, float, str]] = [
    (-0.440, 0.0000, "AA_Greeble"),  # pointe avant du cone d'entree
    (-0.412, 0.0275, "AA_Greeble"),
    (-0.386, 0.0421, "AA_Trim"),     # levre d'entree d'air, doree
    (-0.360, 0.0502, "AA_Hull"),
    (-0.300, 0.0599, "AA_Hull"),
    (-0.200, 0.0713, "AA_Panel"),    # bandeau bleu marine avant
    (-0.080, 0.0802, "AA_Panel"),
    (0.040, 0.0867, "AA_Hull"),
    (0.170, 0.0915, "AA_Hull"),
    (0.300, 0.0948, "AA_Greeble"),
    (0.330, 0.0948, "AA_Greeble"),   # ceinture technique (charniere d'aile)
    (0.360, 0.0948, "AA_Hull"),
    (0.480, 0.0972, "AA_Hull"),
    (0.640, 0.0980, "AA_Panel"),
    (0.780, 0.0980, "AA_Panel"),     # bandeau bleu marine du fuseau
    (0.850, 0.0980, "AA_Hull"),
    (0.890, 0.0980, "AA_Hull"),
    (0.905, 0.0980, "AA_Hull"),
    (0.915, 0.1029, "AA_Greeble"),   # 1er anneau concentrique
    (0.940, 0.1029, "AA_Greeble"),
    (0.948, 0.0980, "AA_Hull"),
    (0.962, 0.0980, "AA_Greeble"),
    (0.972, 0.1053, "AA_Greeble"),   # collier mecanique
    (1.005, 0.1053, "AA_Greeble"),
    (1.012, 0.0964, "AA_Greeble"),
    (1.018, 0.0964, "AA_Trim"),
    (1.023, 0.1013, "AA_Trim"),      # jonc dore
    (1.040, 0.1013, "AA_Trim"),
    (1.045, 0.0948, "AA_Greeble"),
    (1.048, 0.0770, "AA_Greeble"),   # levre du COL — raccord des petales
]


#: Buse emissive, EN AVANT du col : (y, rayon, decalage vertical de l'axe).
#: L'axe remonte, de sorte que la vasque lumineuse s'incline VERS LE HAUT.
#: Reponse directe a BRIEF-0026 : a 20 deg de la verticale, une buse purement
#: axiale ne montre rien de son interieur.
NOZZLE_BORE: tuple[tuple[float, float, float], ...] = (
    (1.0480, 0.077, 0.000),   # doit coincider EXACTEMENT avec la fin du lathe
    (1.0300, 0.071, 0.016),
    (1.0000, 0.064, 0.027),
    (0.9700, 0.052, 0.032),
    (0.9550, 0.036, 0.034),
)
NOZZLE_FLOOR_Y = 0.9450  # fond lumineux

# --- Couronne de petales (piece mobile) -----------------------------------
#: 12 petales, celui d'indice 9 centre exactement en bas : c'est lui qui porte
#: la poupe (y = 1.2300) et donc la longueur du contrat.
NOZZLE_PETALS = 12
PETAL_GAP_DEG = 2.4       # jeu angulaire entre deux petales (couronne FERMEE)
PETAL_ARC = 3             # echantillons d'arc par petale
#: Biseau de sortie : les petales du HAUT sont raccourcis de 70 mm, ceux du bas
#: pas du tout. La couronne s'ouvre donc vers le haut et laisse voir la vasque
#: emissive depuis la camera de jeu.
PETAL_SCARF = 0.070
#: (y, rayon interieur, rayon exterieur) — au repos, couronne FERMEE.
PETAL_SECTIONS: tuple[tuple[float, float, float], ...] = (
    (1.0480, 0.077, 0.093),   # col — c'est le PIVOT
    (1.0900, 0.075, 0.098),
    (1.1400, 0.075, 0.102),
    (1.1900, 0.078, 0.106),
    (1.2300, 0.083, 0.109),   # levre de sortie — POUPE (fixe la bbox)
)

# Carenage dorsal de nacelle : l'arete technique posee sur le DOS du fuseau, qui
# porte le pied de derive. (y, demi-largeur, hauteur au-dessus de l'axe).
# ⚠️ BRIEF-0035 : sa demi-largeur ne doit JAMAIS depasser `NACELLE_R` (0,121).
# Le carenage etait, avant ce brief, la piece qui refermait par le haut l'espace
# entre le fuselage et le fuseau ; un carenage plus large que le fuseau
# reboucherait la fente 1 en vue de dessus et annulerait tout le brief.
FAIRING: list[tuple[float, float, float]] = [
    (0.180, 0.0000, 0.0000),
    (0.300, 0.0502, 0.0583),
    (0.440, 0.0745, 0.0794),
    (0.560, 0.0875, 0.0891),
    (0.700, 0.0940, 0.0940),
    (0.820, 0.0956, 0.0956),
    (0.920, 0.0907, 0.0891),
    (0.980, 0.0778, 0.0745),
    (1.020, 0.0000, 0.0000),
]

# --- Caisson de liaison fuselage <-> nacelle (BRIEF-0035) -----------------
# LE point de contact voulu, et le seul. Il court de y = 0,010 a 0,380 : c'est
# lui qui laisse la fente 1 ouverte par l'AVANT (de -0,440 a 0,010) et par
# l'ARRIERE (de 0,380 a 1,230). Deplacer ses bornes, c'est deplacer les deux
# echancrures que le critere d'acceptation du brief mesure.
# (y, x interieur, x exterieur, z haut, z bas).
BRIDGE: list[tuple[float, float, float, float, float]] = [
    (0.010, 0.082, 0.270, 0.028, -0.056),
    (0.090, 0.082, 0.270, 0.054, -0.072),
    (0.220, 0.082, 0.270, 0.058, -0.076),
    (0.330, 0.082, 0.270, 0.040, -0.066),
    (0.380, 0.082, 0.270, 0.012, -0.038),
]
#: Nervures transversales du caisson (meme raison que `SPINE_FRAMES`).
BRIDGE_FRAMES: tuple[float, ...] = (0.055, 0.170, 0.290)

# --- Derives inclinees (ADR-0014) -----------------------------------------
# BRIEF-0033 se les interdisait et les remplacait par des rails verticaux de
# bout d'aile ; ADR-0014 leve l'interdiction. Elles sont plus rentables que les
# rails a hauteur egale : posees sur les nacelles elles sont AU CENTRE de la
# silhouette, la ou la camera de jeu les voit de trois quarts, tandis qu'un rail
# de bout d'aile ne montre que sa tranche.
#: Inclinaison vers l'exterieur, depuis la verticale. A 30 deg la derive
#: projette 160 mm en vue de dessus (contre 0 pour une derive droite) : c'est
#: cette projection qui la rend lisible dans un shmup vertical.
#: BRIEF-0035 : la derive est le seul element du vaisseau qui pouvait REBOUCHER
#: la fente 2 (nacelle/aile) sans qu'aucun controle s'en apercoive — la bounding
#: box ne mesure pas les trous. Premiere parade : la coucher a 22 deg. Le rendu
#: a montre qu'a 22 deg elle ne se voit plus du tout d'en haut, ce qui annule la
#: raison meme de l'avoir inclinee (BRIEF-0034 §5).
#: Parade retenue : la RECULER derriere l'aile (y = 0,600 a 1,010, quand la lame
#: la plus repliee ne depasse pas y = 0,653) et la redresser a 30 deg. Elle
#: projette alors 145 mm en vue de dessus, dans une zone ou il n'y a rien a
#: boucher.
FIN_CANT_DEG = 30.0
FIN_HEIGHT = 0.290       # envergure de la derive, mesuree dans son propre plan
#: Pied enfonce dans le carenage — mais de 6 cm seulement. A 3 cm (premier
#: essai) 45 % de la derive etait NOYEE dans le carenage et il n'en sortait
#: qu'un moignon : le rendu l'a montre, le calcul ne l'aurait pas dit.
#: BRIEF-0035 : le carenage a baisse avec la nacelle, le pied suit (0,070 ->
#: 0,040) — sinon la derive flotte 3 cm au-dessus de son socle.
FIN_ROOT_Z = 0.040
#: (fraction d'envergure, y bord d'attaque, y bord de fuite, demi-epaisseur).
FIN: tuple[tuple[float, float, float, float], ...] = (
    (0.00, 0.600, 1.012, 0.024),
    (0.28, 0.674, 1.000, 0.019),
    (0.58, 0.762, 0.988, 0.015),
    (0.82, 0.836, 0.976, 0.010),
    (1.00, 0.896, 0.966, 0.006),
)

# --- Tuyere d'axe ---------------------------------------------------------
# La planche montre TROIS sorties : deux fuseaux et une centrale. Ce n'est pas
# un detail decoratif — c'est ce qui fait lire le fuselage comme porteur
# jusqu'a la poupe. Sans elle, l'arete dorsale s'arretait dans le vide et le
# regard concluait « bande posee », exactement le defaut qu'ADR-0014 pointe.
TAIL_NOZZLE: list[tuple[float, float, str]] = [
    (1.010, 0.000, "AA_Hull"),
    (1.024, 0.062, "AA_Hull"),
    (1.060, 0.072, "AA_Greeble"),
    (1.100, 0.072, "AA_Greeble"),
    (1.108, 0.064, "AA_Trim"),
    (1.130, 0.066, "AA_Trim"),
    (1.150, 0.060, "AA_Greeble"),
    (1.185, 0.056, "AA_Greeble"),
]
TAIL_NOZZLE_Z = 0.014    # axe, entre le dessus et le dessous de l'arete
TAIL_BORE_FLOOR = 1.120  # fond emissif, en avant de la levre

# (BRIEF-0035 : `INTAKE`, l'ecope ventrale, a disparu. Elle n'existait que pour
#  relier le fuseau au plan d'aile par le dessous ; il n'y a plus de plan d'aile
#  a cet endroit, et la nacelle a desormais sa propre entree d'air a l'avant.
#  `SHOULDER` a disparu pour la meme raison.)

# ==========================================================================
# Structures dorsale, ventrale et de bout d'aile
# ==========================================================================

# Arete dorsale basse : (y, demi-largeur, z du dessus, z du dessous).
# Flancs VERTICAUX : c'est ce qui la distingue d'un simple bombement de coque
# et la fait lire comme une couche posee sur le pont. Elle prolonge la poutre
# arriere entre les deux fuseaux (au-dela de y = 0.86 la coque s'arrete).
# Elle remplace la « derive » de la planche de reference : elle ne monte qu'a
# 5,5 cm au-dessus du pont et n'a aucune surface inclinee.
#: BRIEF-0034 : la poutre ne se termine plus en lame effilee a y = 1,150 mais
#: en culot rond a y = 1,030, ou vient se poser `TAIL_NOZZLE`.
#: BRIEF-0035 : demi-largeurs ramenees sous celles du pont. Le pont ne fait plus
#: que 0,094 de demi-largeur au maitre-couple : une arete de 0,088 l'aurait
#: recouvert en entier et le fuselage aurait lu comme une simple poutre.
SPINE: list[tuple[float, float, float, float]] = [
    (-0.1450, 0.0087, 0.198, 0.150),
    (-0.0800, 0.0381, 0.224, 0.140),
    (0.0200, 0.0485, 0.244, 0.130),
    (0.1800, 0.0537, 0.260, 0.120),
    (0.3600, 0.0555, 0.258, 0.090),
    (0.5600, 0.0537, 0.250, 0.020),
    (0.7600, 0.0503, 0.236, -0.060),
    (0.9600, 0.0451, 0.216, -0.130),
    (1.0300, 0.0399, 0.196, -0.156),
]

#: Cadres transversaux de l'arete dorsale. Sans eux, l'arete lit — au rendu de
#: dessus — comme une planche blanche de 1,3 m posee sur le pont : la seule
#: chose que la camera de jeu voit d'elle est son DESSUS, et un dessus lisse
#: n'existe pas. Le defaut ne se voyait pas de profil, ou l'arete est excellente.
SPINE_FRAMES: tuple[float, ...] = (0.060, 0.300, 0.520, 0.720, 0.900)

# Quille ventrale : (y, demi-largeur, z du dessus, z du dessous). Elle loge le
# canon a l'avant et descend a -0.345 au maitre-couple. C'est elle qui porte la
# moitie de la hauteur gagnee — et elle est invisible a 20 deg de la verticale,
# masquee par un fuselage deux fois plus large qu'elle.
#: BRIEF-0034 : les trois premieres stations maigrissent. Le nez etant devenu
#: une aiguille (0,046 de demi-envergure a y = -0,98), une quille de 0,058
#: aurait deborde LATERALEMENT de la coque qu'elle est censee porter.
#: BRIEF-0035 : la quille descend a -0,352 et court jusqu'a 0,980. Elle porte a
#: elle seule plus de la moitie de la hauteur, et elle est invisible a 20 deg de
#: la verticale, masquee par le pont.
KEEL: list[tuple[float, float, float, float]] = [
    (-1.0700, 0.0225, -0.026, -0.078),
    (-0.9800, 0.0312, -0.044, -0.116),
    (-0.8000, 0.0451, -0.076, -0.172),
    (-0.5600, 0.0624, -0.120, -0.238),
    (-0.3000, 0.0728, -0.150, -0.296),
    (-0.0200, 0.0797, -0.164, -0.342),
    (0.2200, 0.0815, -0.170, -0.352),
    (0.4200, 0.0763, -0.168, -0.330),
    (0.6000, 0.0676, -0.160, -0.280),
    (0.7600, 0.0572, -0.152, -0.228),
    (0.9000, 0.0451, -0.148, -0.190),
    (0.9800, 0.0104, -0.150, -0.160),
]

#: Cadres transversaux de la quille (meme raison que `SPINE_FRAMES`, cote
#: profil : sans eux la quille est une grande lentille blanche lisse).
KEEL_FRAMES: tuple[float, ...] = (-0.760, -0.420, -0.100, 0.180, 0.440, 0.660, 0.860)

#: Stations de la lisse de nez (chine). Elle court a la jonction pont/joue et
#: trace, de profil comme de trois quarts, la ligne horizontale qui separe le
#: corps superieur du corps inferieur. C'est la couche la moins couteuse de
#: toute la superposition : deux tubes de 12 sections.
#: BRIEF-0035 : prolongee jusqu'a la poupe. Le fuselage etant devenu un corps
#: autonome sur toute la longueur, il n'y a plus de raison d'arreter sa ligne de
#: flanc au tiers avant.
CHINE_Y: tuple[float, ...] = (
    -1.0400, -0.9600, -0.8700, -0.7800, -0.6700, -0.5500, -0.4300, -0.3200,
    -0.2400, -0.1000, 0.0600, 0.2200, 0.3800, 0.5400, 0.7000, 0.8600,
    0.9800,
)

# Longeron ventral avant : ecartement (a l'axe) des deux tubes du canon.
# La culasse des tubes doit rester SOUS la coque : la demi-envergure du
# planform vaut ~0.104 a y = -0.89, on retranche le rayon de levre du tube.
# Deplacer BARREL_X deplace ENSEMBLE la geometrie des tubes (build_details) et
# les muzzles (build_attach_points) : flash, tube et balle restent alignes.
# BRIEF-0034 : resserres (0.080 -> 0.042) et affines. Le nez ayant maigri de
# moitie, des tubes a 0.080 auraient depasse de 40 mm de chaque cote d'une
# coque qui n'en fait plus que 39 a leur station.
BARREL_X = 0.042        # ecartement des deux tubes du canon ventral
BARREL_R = 0.015
BARREL_TIP = -1.0550    # pointe des tubes
MUZZLE_Y = -1.0700      # bouche de tir : juste devant les tubes

# Canons montes sur l'aile : exprimes en FRACTION D'ENVERGURE de la lame, plus
# en metres. BRIEF-0035 : l'aile ne commence plus qu'a x = 0,545, si bien que
# `WING_MUZZLE_X = 0.500` ne designait plus rien — c'est exactement le piege
# decrit dans `pratique-detail-en-fraction-de-corde.md`, applique cette fois a
# un point d'attache et non a un bandeau.
WING_MUZZLE_S = 0.34    # canon d'aile (power 3), au tiers de la lame
TIP_MUZZLE_S = 0.94     # pod de bout d'aile (power 5), au ras du bout


# ==========================================================================
# Interpolation des tables
# ==========================================================================


def lerp_table(table, y: float) -> float:
    """Interpolation lineaire d'une table (y, valeur), extremites clampees.

    Volontairement lineaire par morceaux : sur une aile delta hard-surface,
    une spline arrondirait les cassures qui font justement la silhouette.
    """
    if y <= table[0][0]:
        return table[0][1]
    if y >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        y0, v0 = table[i][0], table[i][1]
        y1, v1 = table[i + 1][0], table[i + 1][1]
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return v0 + (v1 - v0) * t
    return table[-1][1]


def lerp_row(table, y: float, column: int) -> float:
    """Comme `lerp_table`, mais sur la colonne `column` d'une table a n colonnes."""
    return lerp_table([(row[0], row[column]) for row in table], y)


def section_params(y: float) -> tuple[float, float, float, float]:
    """(demi-largeur de coque, demi-pont, epine, ventre) a la station `y`."""
    w = lerp_table(PLANFORM, y)
    f = min(lerp_table(FUSELAGE, y), w * 0.94)
    return w, f, lerp_table(CROWN, y), lerp_table(BELLY, y)


def section_cut(y: float) -> float:
    """Demi-largeur REELLE de la coque loftee.

    BRIEF-0035 : elle vaut desormais toujours `PLANFORM`. L'echancrure de volet
    a quitte la coque principale — le volet est un enfant de l'aile, et l'aile
    est une piece a part entiere. La fonction reste, parce qu'elle est appelee
    partout et qu'elle documente la distinction entre geometrie et etendue.
    """
    return lerp_table(PLANFORM, y)


def _edge_h(crown: float) -> float:
    """Demi-hauteur du BORDE lateral, bornee par l'epaisseur locale du corps."""
    return min(EDGE_H, 0.55 * crown) if crown > 1e-6 else 0.0


def _cheek_shoulder(crown: float, eh: float) -> float:
    """Cote de la joue a son raccord au pont.

    Le `max(..., eh)` n'est pas de la coquetterie : vers la pointe du nez, `eh`
    est lui-meme borne a 0.55 x crown, donc superieur a 0.42 x crown. Sans la
    garde, le bord serait plus HAUT que le pont sur les quinze premiers
    centimetres, et le nez sortirait creuse.
    """
    return max(CHEEK_FRAC * crown, eh)


def z_top(x: float, w: float, f: float, crown: float, belly: float) -> float:
    """Surface superieure : bombe de pont, MARCHE, puis joue jusqu'au borde.

    La marche est implicite : la branche pont rend 0,65 x crown au bord (a = f)
    tandis que la branche joue part de 0,42 x crown. Les deux sommets voisins de
    la section sont distants de 18 % de la joue seulement, donc le pont de faces
    qui les relie EST le flanc superieur du fuselage.
    """
    a = abs(x)
    if f > 1e-6 and a <= f:
        return crown * (1.0 - 0.35 * (a / f) ** 2)
    t = (a - f) / max(w - f, 1e-6)
    t = min(max(t, 0.0), 1.0)
    eh = _edge_h(crown)
    shoulder = _cheek_shoulder(crown, eh)
    return -ANHEDRAL * t * t + (shoulder - eh) * (1.0 - t) ** 1.4 + eh


def z_bot(x: float, w: float, f: float, crown: float, belly: float) -> float:
    a = abs(x)
    if f > 1e-6 and a <= f:
        return belly * (1.0 - 0.35 * (a / f) ** 2)
    t = (a - f) / max(w - f, 1e-6)
    t = min(max(t, 0.0), 1.0)
    eh = min(_edge_h(crown), 0.62 * (-belly)) if belly < 0.0 else _edge_h(crown)
    shoulder = 0.72 * (-belly)
    return -ANHEDRAL * t * t - (max(shoulder - eh, 0.0) * (1.0 - t) ** 1.4 + eh)


# --------------------------------------------------------------------------
# Section transversale : 17 abscisses (BRIEF-0035 : elles etaient 39)
# --------------------------------------------------------------------------
# Le corps central ne fait plus que 0,300 m de large. Les 15 fractions de corde
# heritees de l'aile delta y auraient decoupe des cellules de 4 mm : `cells()`
# les aurait toutes eteintes en silence et la coque serait sortie NUE, sans
# qu'aucun controle ne le signale. On redimensionne donc la trame avec le corps.

#: Fractions de la JOUE (t = 1 au borde, t = 0 au raccord du pont).
#: La paire serree 0.760/0.666 porte l'unique rainure longitudinale que la joue
#: peut loger (5 mm de large) ; le segment 0.180 -> 0.000 est la MARCHE.
CHEEK_T: tuple[float, ...] = (
    1.000,
    0.760, 0.666,   # <- bande de rainure longitudinale (segment 1)
    0.180,          # 2 = joue plate
    0.000,          # 3 = MARCHE (flanc superieur du fuselage)
)
#: Fractions du trajet pont -> sillon dorsal.
FUS_U: tuple[float, ...] = (0.55, 1.00)
#: Fractions du sillon dorsal -> axe.
SPINE_U: tuple[float, ...] = (0.55, 0.00)


def section_x(w: float, f: float) -> list[float]:
    """Les 17 abscisses d'une section, de babord (+w) a tribord (-w)."""
    s = min(SPINE_HW, 0.60 * f)
    d = w - f
    half = [f + t * d for t in CHEEK_T]          # 0..4  (4 = f)
    half += [f + (s - f) * u for u in FUS_U]     # 5..6  (6 = s)
    half += [s * u for u in SPINE_U]             # 7..8  (8 = axe)
    return half + [-v for v in reversed(half[:-1])]


#: Nombre d'abscisses (= sommets de la surface superieure d'une section).
N_TOP = len(section_x(1.0, 0.4))          # 17
#: Nombre de segments par surface (superieure ou inferieure).
N_SEG = N_TOP - 1                          # 16 segments -> index 0..15
RIM_STARBOARD = N_TOP - 1                  # 16
RIM_PORT = 2 * N_TOP - 1                   # 33

#: Index de segment de la rainure LONGITUDINALE de joue (cote babord).
LONG_SEAM_SEGS: tuple[int, ...] = (1,)
#: Segment de la MARCHE (flanc superieur du fuselage).
FLANK_SEG = 3
#: Segments du sillon dorsal (creuse en tant que tel).
SPINE_SEGS: tuple[int, ...] = (6, 7)
#: Etendue laterale des rainures transversales (voir `LATERAL_SEAMS`).
SEG_SPAN_ALL = tuple(range(1, N_SEG))                 # tout sauf les bordes
SEG_SPAN_FUS = tuple(range(4, N_SEG - 4))             # pont seul (4..11)


def top_face(j: int) -> int:
    """Index de la face du segment `j` sur la surface superieure."""
    return j


def bot_face(j: int) -> int:
    """Index de la face du segment `j` sur la surface inferieure."""
    return 2 * N_TOP - 2 - j


MIRROR = {j: (N_TOP - 2) - j for j in range(N_TOP - 1)}


def both(*js: int) -> set[int]:
    """Un ensemble de segments et leurs symetriques (babord + tribord)."""
    out: set[int] = set()
    for j in js:
        out.add(j)
        out.add(MIRROR[j])
    return out


ALL_LONG_SEAMS: set[int] = both(*LONG_SEAM_SEGS)


def run_width(y: float, first: int, last: int) -> float:
    """Largeur (m) du troncon contigu de segments `first..last` a la station `y`.

    Vers le nez, la corde d'aile tombe a quelques centimetres et une cellule y
    mesure moins d'un millimetre : c'est cette mesure — et non une liste de
    zones ecrite a la main — qui eteint rainures et panneaux la ou la coque est
    trop mince pour les porter.
    """
    _, f, _, _ = section_params(y)
    xs = section_x(section_cut(y), f)
    return abs(xs[first] - xs[last + 1])


def contiguous_runs(js: list[int]) -> list[list[int]]:
    """Decoupe une liste triee de segments en troncons d'index consecutifs."""
    runs: list[list[int]] = []
    for j in sorted(js):
        if runs and j == runs[-1][-1] + 1:
            runs[-1].append(j)
        else:
            runs.append([j])
    return runs


# ==========================================================================
# Coque principale
# ==========================================================================


def build_hull() -> object:
    bm = bmesh.new()

    rings: list[list] = []
    for y in STATIONS[1:]:
        w, f, crown, belly = section_params(y)
        xs = section_x(section_cut(y), f)
        top = [(x, y, z_top(x, w, f, crown, belly)) for x in xs]
        bot = [(x, y, z_bot(x, w, f, crown, belly)) for x in reversed(xs)]
        rings.append(ak.add_ring(bm, top + bot))

    nose = bm.verts.new((0.0, STATIONS[0], 0.0))

    bands: list[list] = []
    band_y: list[float] = []
    band_w: list[float] = []
    ak.fan_to_point(bm, rings[0], nose, "AA_Hull")
    for i in range(len(rings) - 1):
        bands.append(ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull"))
        y0, y1 = STATIONS[i + 1], STATIONS[i + 2]
        band_y.append((y0 + y1) * 0.5)
        band_w.append(y1 - y0)
    ak.cap_ring(bm, list(reversed(rings[-1])), "AA_Greeble")

    # Une bande de rainure transversale se reconnait a sa seule largeur (14 mm
    # contre ~35 mm pour une bande courante) : aucun index a maintenir.
    seam_bands = {b for b, wdt in enumerate(band_w) if wdt < SEAM_HALF * 2.5}

    # Cellules deja consommees (materiau pose ou panneau creuse). Une rainure
    # n'ecrase jamais un panneau : elle se faufile entre eux, en plusieurs
    # troncons si besoin — ce qui est exactement la lecture de la planche.
    used: set[tuple[int, int, str]] = set()

    def cells(
        y0: float,
        y1: float,
        js,
        surface: str = "top",
        min_run: float = 0.0,
        min_edge: float = 0.0,
        min_band: float = 0.0,
        skip_seams: bool = False,
    ) -> list:
        """Selectionne des cellules libres en ecartant tout ce qui se replierait.

        Le filtre porte sur le TRONCON contigu (le retrait ne s'applique qu'au
        contour de la zone, pas aux aretes interieures), puis sur ses cellules
        d'extremite, qu'on rogne tant qu'elles sont trop etroites.
        """
        chooser = top_face if surface == "top" else bot_face
        out = []
        for b, ym in enumerate(band_y):
            if not (y0 <= ym <= y1):
                continue
            if skip_seams and b in seam_bands:
                continue
            if min_band > 0.0 and band_w[b] < min_band:
                continue
            free = [
                j for j in js
                if (b, j, surface) not in used
                and bands[b][chooser(j)] is not None
                and bands[b][chooser(j)].is_valid
            ]
            for run in contiguous_runs(free):
                while run and run_width(ym, run[0], run[0]) < min_edge:
                    run = run[1:]
                while run and run_width(ym, run[-1], run[-1]) < min_edge:
                    run = run[:-1]
                if not run or run_width(ym, run[0], run[-1]) < min_run:
                    continue
                for j in run:
                    used.add((b, j, surface))
                    out.append(bands[b][chooser(j)])
        return out

    def pick(y0: float, y1: float, js, surface: str = "top") -> list:
        return cells(y0, y1, js, surface)

    def pick_rim(y0: float, y1: float) -> list:
        out = []
        for b, ym in enumerate(band_y):
            if y0 <= ym <= y1:
                for idx in (RIM_PORT, RIM_STARBOARD):
                    face = bands[b][idx]
                    if face is not None and face.is_valid:
                        out.append(face)
        return out

    def plate(faces: list, material: str) -> None:
        """Panneau a DEUX niveaux (cf. build_crescent_interceptor.py:597).

        Un inset unique laissait un aplat de couleur pleine qui, au rendu,
        « lisait peint ». Le premier inset decoupe une marche restant en coque,
        le second n'accorde au bleu qu'un fond nettement enfonce : la lumiere
        accroche alors deux aretes au lieu d'une, et le panneau existe.
        """
        if not faces:
            return
        ak.inset_panel(bm, faces, "AA_Hull", thickness=0.004, depth=-0.004)
        ak.inset_panel(bm, faces, material, thickness=0.005, depth=-0.005)

    # ---------------------------------------------------------------------
    # 1. Elements identitaires : ils ont priorite sur tout le reste.
    # ---------------------------------------------------------------------

    # --- MARCHE de flanc : peinte, jamais creusee. Elle ne fait que 10 mm de
    #     large — un `plate()` l'effondrerait. C'est la seule surface quasi
    #     verticale que la camera de jeu voit du corps central : le bleu profond
    #     y trace la ligne de flanc sur toute la longueur.
    ak.set_material(pick(-0.860, 1.020, both(FLANK_SEG)), "AA_Panel")

    # --- puits de verriere : bordure doree, cuve sombre (cf. planche) -----
    well = pick(-0.680, -0.085, both(4, 5, 6, 7))
    border = ak.inset_panel(bm, well, "AA_Greeble", thickness=0.008, depth=-0.014)
    ak.set_material(border, "AA_Trim")

    # --- sillon dorsal creuse, du nez a la verriere. En arriere, l'arete
    #     dorsale recouvre entierement cette zone : y creuser une rainure
    #     serait payer de la geometrie invisible.
    ak.inset_panel(
        bm, pick(-1.100, -0.700, both(*SPINE_SEGS)),
        "AA_Greeble", thickness=0.004, depth=-0.014,
    )
    ak.set_material(pick(-0.085, 1.020, both(*SPINE_SEGS)), "AA_Greeble")

    # --- BORDE : la tranche laterale du fuselage, 0,18 m de haut. C'est la
    #     nouveaute de BRIEF-0035 et c'est ce qui fait lire un corps ferme :
    #     on la peint en bleu profond sur toute la partie droite, avec une
    #     coiffe doree au nez et un marquage rouge court.
    ak.set_material(pick_rim(-0.860, 1.020), "AA_Panel")
    ak.set_material(pick_rim(-1.100, -0.900), "AA_Trim")
    ak.set_material(pick_rim(-0.560, -0.480), "AA_Marking_Red")

    # --- arete de joue : tranche doree le long du bord, cote dessus.
    ak.set_material(pick(-0.660, -0.480, both(0)), "AA_Trim")
    ak.set_material(pick(0.180, 0.320, both(0)), "AA_Trim")

    # --- flancs de nez : PEINTS, pas creuses. Sur l'aiguille du nez la joue
    #     tombe sous 20 mm et `plate()` s'y effondre.
    ak.set_material(pick(-1.060, -0.700, both(2)), "AA_Panel")

    # ---------------------------------------------------------------------
    # 2. Rainures LONGITUDINALES. Posees AVANT les panneaux : elles sont la
    #    trame du plaquage, les panneaux viennent s'y appuyer. Le filtre de
    #    largeur les eteint tout seul la ou l'aile est trop mince.
    # ---------------------------------------------------------------------
    for seg in sorted(ALL_LONG_SEAMS):
        ak.inset_panel(
            bm,
            cells(-1.200, 1.020, (seg,), min_run=MIN_RUN_SEAM,
                  min_edge=MIN_EDGE_SEAM, min_band=MIN_BAND_SEAM),
            "AA_Hull",
            thickness=SEAM_T,
            depth=SEAM_D,
        )

    # ---------------------------------------------------------------------
    # 3. Panneaux bleu profond, a deux niveaux (aplats de la planche).
    # ---------------------------------------------------------------------
    # BRIEF-0035 : le corps ne fait plus que 0,300 m de large — les zones sont
    # donc la JOUE (segment 2, ~26 mm) et le PONT (segments 4-5, ~30 mm). Le
    # segment 3 (marche) et les segments 6-7 (sillon dorsal) en sont exclus :
    # ils ont deja leur traitement. `MIN_RUN_PLATE` eteint tout seul ce qui
    # serait plus etroit vers le nez.
    for y0, y1, js in (
        (-0.560, -0.080, both(2)),                  # joue avant
        (-0.860, -0.700, both(4, 5)),               # pont de nez
        (0.020, 0.480, both(2)),                    # joue centrale
        (0.020, 0.400, both(4, 5)),                 # pont, de part et d'autre
        (0.540, 0.900, both(2)),                    # joue arriere
        (0.560, 1.020, both(4, 5)),                 # pont de poutre arriere
    ):
        # `skip_seams=True` : un panneau ne mord jamais sur une bande de rainure.
        # Les grandes plaques bleues se retrouvent donc BORDEES de rainures, ce
        # qui est exactement la lecture de la planche (plaques jointoyees).
        plate(
            cells(y0, y1, js, min_run=MIN_RUN_PLATE, min_edge=MIN_EDGE_PLATE,
                  min_band=MIN_BAND_PLATE, skip_seams=True),
            "AA_Panel",
        )

    # ---------------------------------------------------------------------
    # 4. Rainures TRANSVERSALES : elles decoupent les grandes plages blanches
    #    restantes en plaques, et se scindent d'elles-memes autour des
    #    panneaux deja creuses.
    # ---------------------------------------------------------------------
    for b in sorted(seam_bands):
        ym = band_y[b]
        span = None
        for y, kind in LATERAL_SEAMS:
            if abs(y - ym) < SEAM_HALF:
                span = SEG_SPAN_ALL if kind == "all" else SEG_SPAN_FUS
                break
        if span is None:
            continue
        ak.inset_panel(
            bm,
            cells(ym - 1e-4, ym + 1e-4, span, min_run=MIN_RUN_SEAM,
                  min_edge=MIN_EDGE_SEAM),
            "AA_Hull",
            thickness=SEAM_T,
            depth=SEAM_D,
        )

    # ---------------------------------------------------------------------
    # 5. Dessous : quille sombre et deux panneaux. Volontairement pauvre —
    #    a 20 deg de la verticale le ventre n'existe pas (BRIEF-0026), et
    #    chaque triangle qu'on y depense est un triangle perdu.
    # ---------------------------------------------------------------------
    ak.set_material(pick(-1.050, 1.020, both(*SPINE_SEGS), "bot"), "AA_Greeble")
    plate(
        cells(0.000, 0.600, both(2), "bot", min_run=MIN_RUN_PLATE,
              min_edge=MIN_EDGE_PLATE, min_band=MIN_BAND_PLATE, skip_seams=True),
        "AA_Panel",
    )

    return ak.new_object("Specter9_Hull", bm)


# ==========================================================================
# Sous-ensembles (verriere, nacelles, arete, quille, rails, canon, greebles)
# ==========================================================================


def _rect_ring(bm, y: float, hw: float, z_lo: float, z_hi: float, taper: float = 1.0):
    """Section rectangulaire (4 sommets) : brique de base des longerons."""
    return ak.add_ring(
        bm,
        [
            (hw, y, z_hi),
            (-hw, y, z_hi),
            (-hw * taper, y, z_lo),
            (hw * taper, y, z_lo),
        ],
    )


def _beam_ring(bm, y: float, hw: float, z_hi: float, z_lo: float,
               chamfer: float, top_frac: float, center_x: float = 0.0):
    """Section a FLANCS VERTICAUX et arete chanfreinee (arete dorsale, quille).

    Six sommets. Le chanfrein n'est pas cosmetique : il donne au volume deux
    aretes vives paralleles au lieu d'une, et c'est ce doublet qui fait lire une
    couche posee sur le pont plutot qu'un bombement de la coque elle-meme.
    `chamfer > 0` chanfreine le HAUT (arete dorsale), `chamfer < 0` le BAS
    (quille).
    """
    if chamfer >= 0.0:
        za, zb = z_hi - chamfer, z_hi
        zc, zd = z_lo, z_lo
    else:
        za, zb = z_lo - chamfer, z_lo
        zc, zd = z_hi, z_hi
    return ak.add_ring(
        bm,
        [
            (center_x + hw, y, zc),
            (center_x + hw, y, za),
            (center_x + hw * top_frac, y, zb),
            (center_x - hw * top_frac, y, zb),
            (center_x - hw, y, za),
            (center_x - hw, y, zd),
        ],
    )


def _beam(bm, sections, chamfer: float, top_frac: float,
          materials: tuple[str, str, str], center_x: float = 0.0) -> list[list]:
    """Longeron a flancs verticaux loft le long de `sections`.

    `sections` : (y, demi-largeur, z_hi, z_lo). `materials` = (flanc, chanfrein,
    face plate). Retourne les bandes, pour pouvoir y poser des panneaux.
    """
    side, edge, face = materials
    rings = [
        _beam_ring(bm, y, hw, z_hi, z_lo, chamfer, top_frac, center_x)
        for y, hw, z_hi, z_lo in sections
    ]
    bands = []
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], side)
        ak.set_material([band[1], band[3]], edge)
        ak.set_material([band[2]], face)
        bands.append(band)
    ak.cap_ring(bm, list(reversed(rings[0])), side)
    ak.cap_ring(bm, rings[-1], side)
    return bands


def _strip(bm, samples: list[tuple[float, float, float]], hw: float, material: str,
           center_x: float = 0.0):
    """Bandeau lumineux : petit tube rectangulaire suivant (y, z_bas, z_haut)."""
    rings = [
        ak.add_ring(
            bm,
            [
                (center_x + hw, y, hi),
                (center_x - hw, y, hi),
                (center_x - hw, y, lo),
                (center_x + hw, y, lo),
            ],
        )
        for y, lo, hi in samples
    ]
    for i in range(len(rings) - 1):
        ak.bridge_rings(bm, rings[i], rings[i + 1], material)
    ak.cap_ring(bm, list(reversed(rings[0])), material)
    ak.cap_ring(bm, rings[-1], material)


DOME_ARC = 9  # points d'arc d'une section de dome (verriere, carenage, ecope)


def _dome(bm, sections, center_x, base_z, material: str) -> list[list]:
    """Demi-coque bombee, posee sur une assise plane : verriere, carenage, ecope.

    `sections` : (y, demi-largeur, hauteur au-dessus de l'assise). Une hauteur
    NEGATIVE donne une cloque vers le bas (ecope ventrale). Une section de
    demi-largeur nulle est une pointe. `base_z` : callable(y) -> z d'assise.
    Retourne les bandes de faces, pour pouvoir y poser des panneaux.
    """
    rings: list = []
    tips: list = []
    for y, hw, h in sections:
        z0 = base_z(y)
        if hw <= 1e-6:
            tips.append(bm.verts.new((center_x, y, z0)))
            rings.append(None)
            continue
        pts = [
            (
                center_x + hw * math.cos(math.pi * k / (DOME_ARC - 1)),
                y,
                z0 + h * math.sin(math.pi * k / (DOME_ARC - 1)),
            )
            for k in range(DOME_ARC)
        ]
        rings.append(ak.add_ring(bm, pts))

    solid = [r for r in rings if r is not None]
    bands = []
    ak.fan_to_point(bm, solid[0], tips[0], material)
    for i in range(len(solid) - 1):
        bands.append(ak.bridge_rings(bm, solid[i], solid[i + 1], material))
    ak.fan_to_point(bm, list(reversed(solid[-1])), tips[-1], material)
    return bands


def _circle(bm, y: float, radius: float, cx: float, cz: float,
            segments: int = NACELLE_SEGMENTS):
    """Anneau circulaire dans le plan Y = cste.

    Reproduit EXACTEMENT la formule de `ak.add_lathe(axis="Y")` : c'est ce qui
    permet a `ak.cleanup()` de souder la buse construite a la main sur le
    dernier anneau du solide de revolution, sans couture visible.
    """
    return ak.add_ring(
        bm,
        [
            (
                cx + radius * math.cos(2.0 * math.pi * s / segments),
                y,
                cz + radius * math.sin(2.0 * math.pi * s / segments),
            )
            for s in range(segments)
        ],
    )


def _nozzle_bore(bm, cx: float, cz: float) -> None:
    """Vasque emissive, en avant du col, a axe RELEVE.

    Le probleme resolu ici est de visibilite, pas de style. Une buse coaxiale
    n'expose son emissif que vers l'arriere ; or la camera de jeu regarde a 20
    deg de la verticale et l'ecran d'accueil cadre le vaisseau de trois quarts
    arriere. En remontant l'axe de 42 mm, la couronne emissive devient une
    vasque dont la moitie haute est quasi horizontale — et les petales du haut
    sont raccourcis de 70 mm pour la laisser voir.
    """
    rings = [_circle(bm, y, r, cx, cz + dz) for y, r, dz in NOZZLE_BORE]
    for i in range(len(rings) - 1):
        ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Emissive_Engine")
    floor = bm.verts.new((cx, NOZZLE_FLOOR_Y, cz + NOZZLE_BORE[-1][2]))
    ak.fan_to_point(bm, rings[-1], floor, "AA_Emissive_Engine")


def _deck_z(x: float, y: float) -> float:
    """Cote de la surface superieure de coque au point (x, y)."""
    return z_top(x, *section_params(y))


def _belly_z(x: float, y: float) -> float:
    """Cote de la surface inferieure de coque au point (x, y)."""
    return z_bot(x, *section_params(y))


def _chord_x(y: float, frac: float) -> float:
    """Abscisse a la fraction `frac` de la JOUE, a la station `y`.

    Poser un detail a une abscisse ABSOLUE est ce qui a rendu la moitie des
    bandeaux de BRIEF-0033 caducs des que le bord d'attaque a bouge, puis quatre
    des sept de BRIEF-0034. Exprime en fraction, un bandeau suit la coque quoi
    qu'elle devienne — y compris la reduction de 1,75 m a 0,30 m de large que
    BRIEF-0035 vient d'infliger a cette table.
    """
    _, f, _, _ = section_params(y)
    return f + frac * (section_cut(y) - f)


def nacelle_half_width(y: float) -> float:
    """Demi-largeur de la nacelle vue de dessus, TOUT compris, a la station `y`.

    Interroge les tables (`NACELLE_PROFILE`, `FAIRING`, `PETAL_SECTIONS`) au lieu
    de recopier un maximum : c'est cette fonction que consultent la mesure de
    degagement d'aile et la mesure de fentes, et une constante recopiee y
    mentirait au premier changement de profil.
    """
    if y < NACELLE_PROFILE[0][0] or y > PETAL_SECTIONS[-1][0]:
        return 0.0
    if y > NACELLE_PROFILE[-1][0]:
        return lerp_table([(s[0], s[2]) for s in PETAL_SECTIONS], y)
    r = lerp_table([(p[0], p[1]) for p in NACELLE_PROFILE], y)
    if FAIRING[0][0] <= y <= FAIRING[-1][0]:
        r = max(r, lerp_row(FAIRING, y, 1))
    return r


# --------------------------------------------------------------------------
# Geometrie en plan de l'aile (polaire autour du pivot)
# --------------------------------------------------------------------------


def _wing_polar() -> tuple[tuple[float, float], tuple[float, float]]:
    """(rayon, angle) du bord d'attaque et du bord de fuite AU BOUT D'AILE.

    Les rayons sont DERIVES de l'envergure contractuelle : `x = 0,875` est une
    hitbox, pas une intention. On resout donc `r cos(phi) = 0,875 - x_pivot`
    plutot que d'ecrire un rayon a la main et de constater l'ecart au build.
    """
    reach = WING_TIP_X - WING_PIVOT_X
    le = (reach / math.cos(math.radians(WING_LE_TIP_ANGLE)), WING_LE_TIP_ANGLE)
    te = (reach / math.cos(math.radians(WING_TE_TIP_ANGLE)), WING_TE_TIP_ANGLE)
    return le, te


def _polar(r: float, phi_deg: float) -> tuple[float, float]:
    """Point (x, y) du repere d'auteur, cote BABORD, a (rayon, angle) du pivot."""
    a = math.radians(phi_deg)
    return (WING_PIVOT_X + r * math.cos(a), WING_PIVOT_Y + r * math.sin(a))


def _wing_edges(s: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """Points (x, y) du bord d'attaque et du bord de fuite a l'envergure `s`.

    Interpolation en POLAIRE (rayon et angle), pas en cartesien : c'est ce qui
    garantit qu'aucune nervure intermediaire ne descend sous l'angle de
    l'emplanture, donc qu'aucune ne peut passer derriere le pivot en fleche.
    """
    le_tip, te_tip = _wing_polar()
    le = _polar(
        WING_LE_ROOT[0] + (le_tip[0] - WING_LE_ROOT[0]) * s,
        WING_LE_ROOT[1] + (le_tip[1] - WING_LE_ROOT[1]) * s,
    )
    te = _polar(
        WING_TE_ROOT[0] + (te_tip[0] - WING_TE_ROOT[0]) * s,
        WING_TE_ROOT[1] + (te_tip[1] - WING_TE_ROOT[1]) * s,
    )
    return le, te


def _wing_thickness(s: float, t: float) -> float:
    """Demi-epaisseur de la lame a l'envergure `s`, fraction de corde `t`."""
    th = WING_THICK_ROOT + (WING_THICK_TIP - WING_THICK_ROOT) * s
    # Lentille a bords non nuls : un bord d'epaisseur zero degenere au chanfrein.
    return max(th * (4.0 * t * (1.0 - t)) ** 0.55, 0.0042)


def _wing_plane_z(s: float) -> float:
    """Cote du plan de l'aile a l'envergure `s` (affaissement du bout)."""
    return WING_PIVOT_Z - WING_ANHEDRAL * s * s


def _insettable(faces: list, thickness: float) -> list:
    """Ecarte les faces trop etroites pour supporter un retrait de `thickness`.

    Meme garde-fou que `cells()` sur la coque, mais exprime sur la face elle-meme
    plutot que sur une largeur de troncon — l'aile n'a pas de trame reguliere.
    Sans lui, la PAIRE SERREE de nervures du pied de volet (6 mm d'envergure)
    passait dans `inset_region(use_even_offset=True)`, qui divise le retrait par
    le sinus de l'angle au coin : la lame ressortait 0,98 m au large de l'axe et
    la coque faisait 1,95 m d'envergure au lieu de 1,75.
    """
    out = []
    for face in faces:
        if face is None or not face.is_valid:
            continue
        edges = [e.calc_length() for e in face.edges]
        if edges and min(edges) > thickness * 2.4:
            out.append(face)
    return out


def _flap_root_s() -> float:
    """Envergure a laquelle le volet commence, par bissection sur le bord de fuite.

    Derivee, jamais ecrite : elle depend de `FLAP_HINGE_Y` et du plan de l'aile,
    et les trois pieces qui s'en servent (logement dans l'aile, nervures du
    volet, mesure de debattement) doivent partager EXACTEMENT la meme valeur.
    """
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) * 0.5
        if _wing_edges(mid)[1][1] < FLAP_HINGE_Y + FLAP_MIN_CHORD:
            lo = mid
        else:
            hi = mid
    return hi


def _wing_rib_stations() -> list[float]:
    """Stations d'envergure de l'aile, avec la PAIRE serree du pied de volet.

    Sans les deux stations rapprochees a l'emplanture du volet, la marche du
    logement s'etalerait sur toute une bande et donnerait une rampe au lieu
    d'une cloison — le meme piege que `FLAP_WALL_Y` corrigeait sur la coque
    avant BRIEF-0035.
    """
    s0 = _flap_root_s()
    out = set(WING_RIBS)
    out.add(round(max(s0 - 0.006, 0.0), 6))
    out.add(round(s0, 6))
    return sorted(out)


def _fin(bm, sx: float) -> None:
    """Derive inclinee, montee sur le dessus d'une nacelle (ADR-0014).

    Elle est loftee dans SON propre plan : chaque section est un rectangle
    mince, translate le long de l'axe de derive (incline de `FIN_CANT_DEG` vers
    l'exterieur) et epaissi perpendiculairement a ce plan. Construire la lame
    droite puis la tourner aurait marche aussi, mais aurait laisse le pied
    dessiner un arc au lieu d'epouser le carenage.
    """
    cant = math.radians(FIN_CANT_DEG)
    # axe d'envergure de la derive, et normale a son plan
    ax, az = math.sin(cant), math.cos(cant)
    nx, nz = math.cos(cant), -math.sin(cant)

    rings = []
    for s, y_le, y_te, th in FIN:
        cx = sx * (NACELLE_X + s * FIN_HEIGHT * ax)
        cz = FIN_ROOT_Z + s * FIN_HEIGHT * az
        # `sx` sur la composante x de la normale : sans cela la derive tribord
        # serait epaissie du mauvais cote et son pied sortirait du carenage.
        dx, dz = sx * nx * th, nz * th
        rings.append(
            ak.add_ring(
                bm,
                [
                    (cx + dx, y_le, cz + dz),
                    (cx + dx, y_te, cz + dz),
                    (cx - dx, y_te, cz - dz),
                    (cx - dx, y_le, cz - dz),
                ],
            )
        )
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        # 1 = bord de fuite, 3 = bord d'attaque : deux tranches, en sombre,
        # qui donnent a la lame une epaisseur lisible a 20 deg de la verticale.
        ak.set_material([band[1], band[3]], "AA_Greeble")
        # 0 = flanc EXTERNE. Incline de 34 deg, c'est la seule face de la
        # derive que la camera de jeu voit vraiment : la laisser en blanc de
        # coque la faisait disparaitre dans le pont, qui l'est aussi.
        if 1 <= i <= 2:
            ak.set_material([band[0]], "AA_Panel")
        if i >= len(rings) - 2:
            ak.set_material([band[0], band[2]], "AA_Marking_Red")  # coiffe
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Trim")
    # feu de derive, sur la tranche du bord de fuite
    ak.add_box(
        bm,
        (
            sx * (NACELLE_X + 0.86 * FIN_HEIGHT * ax),
            0.972,
            FIN_ROOT_Z + 0.86 * FIN_HEIGHT * az,
        ),
        (0.024, 0.014, 0.048),
        "AA_Emissive_Engine",
    )


def _bridge(bm, sx: float) -> None:
    """Caisson de liaison fuselage <-> nacelle (BRIEF-0035).

    C'est la seule matiere qui traverse la fente 1. Il est deliberement COURT
    (0,010 a 0,380, soit 15 % de la longueur) : c'est la longueur qu'il n'occupe
    pas qui produit les deux echancrures du critere d'acceptation.

    Ses deux extremites en x sont enfouies — 0,095 est sous le pont (dont la
    demi-largeur vaut 0,145 a ces stations) et 0,330 est l'axe meme de la
    nacelle. Un caisson affleurant laisserait deux coutures visibles au lieu
    d'une piece qui sort d'un corps et entre dans l'autre.
    """
    rings = []
    for y, x_in, x_out, z_hi, z_lo in BRIDGE:
        rings.append(
            ak.add_ring(
                bm,
                [
                    (sx * x_out, y, z_hi),
                    (sx * x_in, y, z_hi),
                    (sx * x_in, y, z_lo),
                    (sx * x_out, y, z_lo),
                ],
            )
        )
    for i in range(len(rings) - 1):
        # 0 = dessus, 1 = flanc interne (celui qui borde la fente), 2 = dessous,
        # 3 = flanc externe. Le dessus est la seule face que la camera de jeu
        # voit : c'est elle qui porte le bleu.
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Greeble")
        ak.set_material([band[0]], "AA_Panel")
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Greeble")

    # Nervures : sans elles le caisson lit, du dessus, comme une simple plaque.
    for y in BRIDGE_FRAMES:
        x_in = lerp_row(BRIDGE, y, 1)
        x_out = lerp_row(BRIDGE, y, 2)
        z_hi, z_lo = lerp_row(BRIDGE, y, 3), lerp_row(BRIDGE, y, 4)
        ak.add_box(
            bm,
            (sx * (x_in + x_out) * 0.5, y, (z_hi + z_lo) * 0.5),
            (x_out - x_in, 0.018, (z_hi - z_lo) * 1.10),
            "AA_Greeble",
        )
    # Bandeau cyan sur le dessus du caisson : il souligne la liaison, donc les
    # deux trouees qui l'encadrent.
    _strip(
        bm,
        [(0.070, 0.046, 0.056), (0.220, 0.050, 0.060), (0.330, 0.034, 0.044)],
        0.009,
        "AA_Emissive_Engine",
        center_x=sx * 0.200,
    )


def _deck_greebles(bm, x: float, y0: float, y1: float, count: int, seed: int,
                   size_range=(0.016, 0.034), height_range=(0.006, 0.014)) -> None:
    """Bandeau de greebles POSE sur le pont, en suivant sa courbure.

    `greeble_strip` interpole lineairement le z entre depart et arrivee : en lui
    donnant la cote reelle de la coque aux deux extremites, les boites se posent
    au lieu de flotter ou de s'enfoncer.
    """
    ak.greeble_strip(
        bm,
        (x, y0, _deck_z(x, y0) - 0.003),
        (x, y1, _deck_z(x, y1) - 0.003),
        count=count,
        seed=seed,
        size_range=size_range,
        height_range=height_range,
    )


def build_details() -> object:
    bm = bmesh.new()
    rng_seed = SEED

    # ---------------------------------------------------------------- verriere
    canopy_base = lambda y: lerp_table(CROWN, y) - CANOPY_SINK  # noqa: E731
    canopy_bands = _dome(bm, CANOPY, 0.0, canopy_base, "AA_Glass")

    # Montants de verriere : la planche ne montre pas un ovale sombre pose a
    # plat mais une bulle STRUCTUREE — deux rails lateraux et une nervure d'axe.
    # On les prend sur les faces du dome (aucun triangle supplementaire).
    for band in canopy_bands:
        ak.set_material([band[k] for k in (0, DOME_ARC - 2) if band[k]], "AA_Greeble")
    for band in canopy_bands[3:6]:
        ak.set_material([band[k] for k in (3, 4) if band[k]], "AA_Greeble")

    # Cadre en RELIEF autour du puits : deux longerons dores suivant le contour
    # de la verriere, plus une traverse avant (pare-brise) et une arriere. C'est
    # ce bourrelet qui donne au cockpit son epaisseur en vue de dessus, et qui
    # empeche la verriere de lire comme un ovale peint.
    for sx in (ak.PORT, ak.STARBOARD):
        rail = []
        for y, hw, _h in CANOPY[1:-1]:
            z0 = canopy_base(y)
            rail.append((y, hw + 0.014, z0 - 0.006, z0 + 0.026))
        rings = [
            ak.add_ring(
                bm,
                [
                    (sx * (hw + 0.010), y, hi),
                    (sx * (hw - 0.006), y, hi),
                    (sx * (hw - 0.006), y, lo),
                    (sx * (hw + 0.010), y, lo),
                ],
            )
            for y, hw, lo, hi in rail
        ]
        for i in range(len(rings) - 1):
            ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Trim")
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Trim")
        ak.cap_ring(bm, rings[-1], "AA_Trim")

    for y, hw, tall, mat in (
        (-0.6450, 0.050, 0.028, "AA_Trim"),     # cadre de pare-brise, en relief
        (-0.5950, 0.066, 0.016, "AA_Greeble"),  # arceau
        (-0.1150, 0.064, 0.030, "AA_Trim"),     # dosseret arriere
    ):
        z0 = canopy_base(y)
        ak.add_box(bm, (0.0, y, z0 + tall * 0.5), (hw * 2.0, 0.024, tall), mat)

    # --------------------------------------------------- arete dorsale basse
    # Presence verticale ORIGINALE : une arete a flancs verticaux, jamais une
    # derive. Flancs en bleu profond, chanfreins en coque, dessus en coque :
    # de profil, deux lignes horizontales paralleles se detachent du pont.
    spine_bands = _beam(
        bm, SPINE, chamfer=0.014, top_frac=0.70,
        materials=("AA_Panel", "AA_Hull", "AA_Hull"),
    )
    # jonc dore au droit de la baie technique (accent, pas une livree)
    for b, (y, _, _, _) in enumerate(SPINE[:-1]):
        if 0.02 <= y <= 0.36:
            ak.set_material([spine_bands[b][1], spine_bands[b][3]], "AA_Trim")

    # Canal technique CREUSE dans le dessus, et cadres transversaux en relief.
    # Le dessus de l'arete est la seule de ses faces que la camera de jeu voit :
    # laisse lisse, l'arete lisait comme une planche blanche posee sur le pont.
    # (Un bandeau sombre POSE ne suffisait pas : enferme dans le solide, il
    # etait simplement invisible. Il faut creuser.)
    ak.inset_panel(
        bm, [band[2] for band in spine_bands[1:-1]],
        "AA_Greeble", thickness=0.011, depth=-0.014,
    )
    for y in SPINE_FRAMES:
        hw, z_hi = lerp_row(SPINE, y, 1), lerp_row(SPINE, y, 2)
        ak.add_box(bm, (0.0, y, z_hi - 0.020), (hw * 2.20, 0.020, 0.050),
                   "AA_Greeble")

    # deux bandeaux cyan sur le dessus de l'arete : lisibles a la verticale.
    for sx in (ak.PORT, ak.STARBOARD):
        _strip(
            bm,
            [
                (0.420, lerp_row(SPINE, 0.420, 2) - 0.012, lerp_row(SPINE, 0.420, 2)),
                (0.700, lerp_row(SPINE, 0.700, 2) - 0.012, lerp_row(SPINE, 0.700, 2)),
                (0.980, lerp_row(SPINE, 0.980, 2) - 0.012, lerp_row(SPINE, 0.980, 2)),
            ],
            0.012,
            "AA_Emissive_Engine",
            center_x=sx * 0.048,
        )

    # ------------------------------------------------------- quille ventrale
    # Chanfrein NEGATIF : c'est le bas qui est coupe. Elle porte la moitie de la
    # hauteur gagnee par ce brief, et elle est invisible depuis la camera de jeu.
    keel_bands = _beam(
        bm, KEEL, chamfer=-0.016, top_frac=0.72,
        materials=("AA_Hull", "AA_Greeble", "AA_Greeble"),
    )
    for b, (y, _, _, _) in enumerate(KEEL[:-1]):
        if -0.30 <= y <= 0.42:
            ak.set_material([keel_bands[b][0], keel_bands[b][4]], "AA_Panel")
    for y in KEEL_FRAMES:
        hw = lerp_row(KEEL, y, 1)
        z_hi, z_lo = lerp_row(KEEL, y, 2), lerp_row(KEEL, y, 3)
        ak.add_box(
            bm, (0.0, y, (z_hi + z_lo) * 0.5 + 0.010),
            (hw * 2.14, 0.020, (z_hi - z_lo) * 0.92), "AA_Greeble",
        )

    # -------------------------------------------------- lisse de nez (chine)
    for sx in (ak.PORT, ak.STARBOARD):
        rings = []
        for y in CHINE_Y:
            w, f, crown, belly = section_params(y)
            zt = z_top(f, w, f, crown, belly)
            zb = z_bot(f, w, f, crown, belly)
            zc = zb + (zt - zb) * 0.44
            x0, x1 = f - 0.012, min(f + 0.024, w - 0.006)
            rings.append(
                ak.add_ring(
                    bm,
                    [
                        (sx * x0, y, zc + 0.010),
                        (sx * x1, y, zc + 0.004),
                        (sx * x1, y, zc - 0.004),
                        (sx * x0, y, zc - 0.010),
                    ],
                )
            )
        for i in range(len(rings) - 1):
            ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Greeble")
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
        ak.cap_ring(bm, rings[-1], "AA_Greeble")

    # ------------------------------------------------------- tuyere d'axe
    # Posee au culot de la poutre dorsale. Elle ne rallonge PAS le vaisseau :
    # sa levre est a y = 1.185, en avant de la poupe (1.230, fixee par les
    # petales). C'est un point de mire, pas une dimension.
    ak.add_lathe(bm, TAIL_NOZZLE, 16, center_x=0.0, center_z=TAIL_NOZZLE_Z)
    bore = [
        _circle(bm, y, r, 0.0, TAIL_NOZZLE_Z, segments=16)
        for y, r in ((1.185, 0.056), (1.170, 0.050), (1.150, 0.040))
    ]
    for i in range(len(bore) - 1):
        ak.bridge_rings(bm, bore[i], bore[i + 1], "AA_Emissive_Engine")
    ak.fan_to_point(
        bm, bore[-1], bm.verts.new((0.0, TAIL_BORE_FLOOR, TAIL_NOZZLE_Z)),
        "AA_Emissive_Engine",
    )

    # ---------------------------------------- nacelles : fuseau, carenage, ecope
    for sign in (ak.PORT, ak.STARBOARD):
        ak.add_lathe(
            bm,
            NACELLE_PROFILE,
            NACELLE_SEGMENTS,
            center_x=sign * NACELLE_X,
            center_z=NACELLE_Z,
        )
        _nozzle_bore(bm, sign * NACELLE_X, NACELLE_Z)

        bands = _dome(
            bm, FAIRING, sign * NACELLE_X, lambda _y: NACELLE_Z, "AA_Hull"
        )
        # aplat bleu sur le dos du carenage, borde de deux rainures prises sur
        # les arcs voisins.
        for b, (y, _, _) in enumerate(FAIRING[1:-2]):
            if 0.50 <= y <= 0.90:
                ak.set_material(
                    [bands[b][k] for k in (2, 3, 4, 5) if bands[b][k]], "AA_Panel"
                )
            if 0.42 <= y <= 0.94:
                ak.set_material(
                    [bands[b][k] for k in (1, 6) if bands[b][k]], "AA_Greeble"
                )

        # bandeau cyan sur le FLANC SUPERIEUR du fuseau : visible du dessus.
        # L'offset (0.052) est la demi-corde du carenage a la hauteur du
        # bandeau, pas un nombre choisi : le carenage ayant maigri de 26 mm avec
        # la nacelle, l'ancien 0.064 aurait laisse le bandeau flotter dans le vide.
        _strip(
            bm,
            [(0.620, 0.044, 0.054), (0.780, 0.050, 0.060), (0.920, 0.044, 0.054)],
            0.009,
            "AA_Emissive_Engine",
            center_x=sign * (NACELLE_X + 0.042),
        )
        # couronne emissive posee sur le DOS du collier : deuxieme temoin de
        # poussee lisible a la verticale, independamment de la vasque.
        ak.add_box(
            bm,
            (sign * NACELLE_X, 0.988, NACELLE_Z + 0.100),
            (0.052, 0.028, 0.014),
            "AA_Emissive_Engine",
        )
        # CHAPE DE CHARNIERE : le tenon fixe qui recoit l'aile. Il sort de la
        # peau du fuseau (0,451) et s'arrete a 8 mm du pivot (0,472) — la ferrure
        # de l'aile vient s'y emboiter. C'est le seul endroit ou les deux corps
        # se touchent presque : partout ailleurs la fente 2 reste ouverte, ce que
        # le critere d'acceptation du brief exige.
        ak.add_box(
            bm,
            (sign * (NACELLE_X + 0.078), WING_PIVOT_Y, WING_PIVOT_Z - 0.004),
            (0.058, 0.130, 0.058),
            "AA_Greeble",
        )
        ak.add_box(
            bm,
            (sign * (NACELLE_X + 0.086), WING_PIVOT_Y, WING_PIVOT_Z + 0.024),
            (0.040, 0.086, 0.014),
            "AA_Trim",
        )

    # ------------------------------------- caissons de liaison (BRIEF-0035)
    for sx in (ak.PORT, ak.STARBOARD):
        _bridge(bm, sx)

    # ---------------------------------------------- derives inclinees (ADR-0014)
    for sx in (ak.PORT, ak.STARBOARD):
        _fin(bm, sx)

    # ------------------------------------------------ longeron ventral + canon
    # deux tubes debouchant sous le nez, loges dans la quille
    barrel_z = _barrel_z()
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_lathe(
            bm,
            [
                (-0.900, 0.000, "AA_Greeble"),
                (-0.890, BARREL_R, "AA_Greeble"),
                (-1.020, BARREL_R, "AA_Greeble"),
                (-1.030, BARREL_R * 1.22, "AA_Trim"),
                (BARREL_TIP, BARREL_R * 1.18, "AA_Trim"),
                (BARREL_TIP, BARREL_R * 0.60, "AA_Greeble"),
                (-1.040, BARREL_R * 0.55, "AA_Greeble"),
                (-1.038, 0.000, "AA_Greeble"),
            ],
            12,
            center_x=sx * BARREL_X,
            center_z=barrel_z,
        )

    # platine doree ventrale + marquage rouge, posees sur le flanc de quille
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(
            bm, (sx * (lerp_row(KEEL, 0.150, 1) + 0.004), 0.150, -0.250),
            (0.014, 0.300, 0.060), "AA_Trim",
        )
        ak.add_box(
            bm, (sx * (lerp_row(KEEL, -0.180, 1) + 0.004), -0.180, -0.230),
            (0.014, 0.090, 0.036), "AA_Marking_Red",
        )

    # --------------------------------------- bloc mecanique dorsal (planche)
    # En avant des tuyeres, un bloc technique encastre dans l'arete : platine
    # sombre, deux joues dorees, hublot cyan. C'est le point de mire de la vue
    # de dessus — on le paie en detail.
    bay_z = lerp_row(SPINE, 0.185, 2)
    ak.add_box(bm, (0.0, 0.185, bay_z - 0.008), (0.078, 0.280, 0.044), "AA_Greeble")
    ak.add_box(bm, (0.0, 0.185, bay_z + 0.014), (0.054, 0.236, 0.014), "AA_Greeble")
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * 0.046, 0.185, bay_z - 0.004),
                   (0.014, 0.300, 0.048), "AA_Trim")
        ak.add_box(bm, (sx * 0.028, 0.072, bay_z + 0.022),
                   (0.016, 0.070, 0.012), "AA_Emissive_Engine")
    ak.add_box(bm, (0.0, 0.150, bay_z + 0.022), (0.022, 0.130, 0.012),
               "AA_Emissive_Engine")
    ak.add_box(bm, (0.0, 0.300, bay_z + 0.018), (0.042, 0.036, 0.020),
               "AA_Marking_Red")

    # --------------------------------------------- petits bandeaux cyan du pont
    # Reperes d'echelle, tous poses sur des faces VUES DU DESSUS, et TOUS en
    # fraction de joue (`_chord_x`). BRIEF-0035 divise la largeur de la coque par
    # six : une seule abscisse absolue heritee aurait atterri dans le vide.
    for sx in (ak.PORT, ak.STARBOARD):
        for y, frac, length in (
            (-0.480, 0.55, 0.070),
            (0.120, 0.70, 0.090),
            (0.480, 0.68, 0.090),
            (0.820, 0.60, 0.080),
        ):
            x = _chord_x(y, frac)
            ak.add_box(
                bm,
                (sx * x, y, _deck_z(sx * x, y) + 0.004),
                (0.014, length, 0.010),
                "AA_Emissive_Engine",
            )

    # ---------------------------------------------------------------- greebles
    # Tous sur le pont, sur le dos des fuseaux, sur les caissons ou sur les
    # flancs de l'arete : les faces arriere ne sont pas vues par la camera de
    # jeu, y semer des greebles serait du gaspillage.
    ak.greeble_strip(
        bm, (0.0, -0.150, bay_z - 0.030), (0.0, 0.030, bay_z - 0.030),
        count=5, seed=rng_seed,
        size_range=(0.014, 0.030), height_range=(0.006, 0.014),
    )
    # ⚠️ Toutes les abscisses ci-dessous ont ete REVUES par BRIEF-0035, pour la
    # troisieme fois en trois briefs. La coque loftee ne fait plus que 0,30 m de
    # large : tout ce qui etait pose au-dela de x = 0,15 tombait dans le vide,
    # c'est-a-dire cinq des sept bandeaux. Ceux qui decoraient l'aile ont
    # demenage DANS `build_wing()` — une piece mobile porte ses propres details.
    for k, sx in enumerate((ak.PORT, ak.STARBOARD)):
        base = rng_seed + 17 * (k + 1)
        # rampe technique le long de l'arete dorsale, sur le pont
        _deck_greebles(bm, sx * 0.072, -0.120, 0.320, 6, base + 2,
                       size_range=(0.014, 0.026), height_range=(0.005, 0.012))
        # joue centrale
        _deck_greebles(bm, sx * 0.120, 0.420, 0.700, 5, base + 3,
                       size_range=(0.014, 0.026), height_range=(0.005, 0.011))
        # joue avant, en avant de la verriere
        _deck_greebles(bm, sx * 0.088, -0.700, -0.520, 4, base + 4,
                       size_range=(0.012, 0.024), height_range=(0.005, 0.010))
        # flancs de nez
        _deck_greebles(bm, sx * 0.040, -0.980, -0.840, 3, base + 5,
                       size_range=(0.010, 0.020), height_range=(0.004, 0.009))
        # dos du carenage de nacelle
        ak.greeble_strip(
            bm,
            (sx * (NACELLE_X - 0.038), 0.560, NACELLE_Z + 0.082),
            (sx * (NACELLE_X - 0.038), 0.900, NACELLE_Z + 0.082),
            count=5,
            seed=base + 6,
            size_range=(0.014, 0.028),
            height_range=(0.006, 0.014),
        )
        # dessus du caisson de liaison : il est PILE dans l'axe du regard entre
        # les deux fentes, c'est la ou un greeble se voit le mieux.
        ak.greeble_strip(
            bm,
            (sx * 0.150, 0.060, 0.056),
            (sx * 0.150, 0.330, 0.050),
            count=4,
            seed=base + 7,
            size_range=(0.014, 0.026),
            height_range=(0.005, 0.011),
        )

    return ak.new_object("Specter9_Details", bm)


def _barrel_z() -> float:
    """Axe des tubes du canon : centre sur la section de quille sous le nez."""
    y = -1.020
    return (lerp_row(KEEL, y, 2) + lerp_row(KEEL, y, 3)) * 0.5


# ==========================================================================
# Pieces mobiles (ak.moving_part -> nœuds glTF separes)
# ==========================================================================


def _wing_section(s: float, y_clamp: float | None = None):
    """Nervure de l'aile a l'envergure `s` : (points dessus, points dessous).

    `y_clamp` tronque la nervure vers l'arriere — c'est ce qui creuse le
    logement du volet : l'aile s'arrete la ou le volet commence, faute de quoi
    la piece traverse la lame des la premiere image d'animation.

    ⚠️ La troncature REPARAMETRE la corde (`t * t_max`) au lieu d'ecraser les
    points au-dela de la coupe sur la coupe. La premiere version faisait
    l'inverse et produisait 4 a 6 sommets confondus par nervure : Blender
    signalait « Mesh Wing_L is not valid », `bevel_sharp_edges` projetait ensuite
    des sommets a 15 cm au-dessus de la lame, et la coque sortait a 1,79 m de
    large — toujours dans la tolerance de 3 % du contrat, donc SANS ERREUR.
    """
    (x_le, y_le), (x_te, y_te) = _wing_edges(s)
    span = y_te - y_le
    t_max = 1.0
    if y_clamp is not None and span > 1e-6 and y_te > y_clamp:
        t_max = min(max((y_clamp - y_le) / span, 0.06), 1.0)
    z0 = _wing_plane_z(s)
    top, bot = [], []
    for t0 in WING_CHORD_T:
        t = t0 * t_max
        x = x_le + (x_te - x_le) * t
        y = y_le + span * t
        # L'epaisseur suit la fraction de la corde REELLE : sans cela la lame
        # tronquee sortirait coupee en pleine masse, epaisse au bord de fuite.
        h = _wing_thickness(s, t0)
        top.append((x, y, z0 + h))
        bot.append((x, y, z0 - h))
    return top, bot


def build_wing(side: float) -> ak.MovingPart:
    """Aile a fleche variable — lame distincte, greffee au flanc de la nacelle.

    ⚠️ Le PIVOT est toute la primitive : l'origine du nœud est posee sur l'axe
    de fleche (vertical). Cote Godot, faire varier la rotation autour de l'axe
    VERTICAL du nœud ouvre et referme la fleche ; les deux cotes tournent en
    sens opposes.

    Position de REPOS = ailes DEPLOYEES (fleche minimale). C'est l'etat que le
    `.glb` montre, donc celui que le contrat de bounding box mesure — d'ou
    `_wing_sweep_limit()`, qui verifie l'AUTRE pose.
    """
    tag = "L" if side > 0 else "R"
    bm = bmesh.new()
    s0 = _flap_root_s()
    stations = _wing_rib_stations()

    # ⚠️ La lame est TOUJOURS batie cote babord, puis miroitee en fin de
    # fonction. Multiplier les abscisses par `side` des la construction inverse
    # l'orientation des faces, et `bmesh.ops.inset_region(use_even_offset=True)`
    # explose sur une face retournee : l'aile tribord sortait avec un sommet a
    # y = -3,18 m, ce qui donnait une coque de 4,41 m de long. Le contrat l'a
    # bien vu — mais seulement parce que le degat etait ENORME.
    rings = []
    for s in stations:
        # Le logement n'est creuse que la ou le volet existe reellement.
        top, bot = _wing_section(s, y_clamp=FLAP_WALL_Y if s >= s0 - 1e-9 else None)
        rings.append(ak.add_ring(bm, top + list(reversed(bot))))

    n = len(WING_CHORD_T)
    bands = []
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        bands.append(band)
        # segment n-1 = tranche de BORD DE FUITE (la cloison du volet) ;
        # segment 2n-1 = tranche de BORD D'ATTAQUE.
        ak.set_material([band[n - 1]], "AA_Greeble")
        ak.set_material([band[2 * n - 1]], "AA_Trim")
    # emplanture : sombre, elle borde la fente et doit se lire comme une coupe.
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Greeble")

    # --- plaquage de la lame ---------------------------------------------
    # L'aile porte desormais l'essentiel de la surface plate du vaisseau : c'est
    # ici que le detail rend, pas sur un fuselage de 0,30 m. Les indices sont des
    # FRACTIONS DE CORDE (`WING_CHORD_T`), donc ils survivent a un changement de
    # plan — la lecon de BRIEF-0034, appliquee des la construction.
    for j in (3, 7):        # bandes serrees 0.300/0.345 et 0.700/0.745
        for jj in (j, 2 * n - 2 - j):
            ak.inset_panel(
                bm, _insettable([b[jj] for b in bands], SEAM_T),
                "AA_Hull", thickness=SEAM_T, depth=SEAM_D,
            )
    # Les zones sont donnees en FRACTION d'envergure, pas en index de bande :
    # `_wing_rib_stations()` insere une paire serree dont la position depend de
    # `FLAP_HINGE_Y`, et un index de bande ecrit en dur designerait autre chose
    # au premier reglage de volet.
    for s0f, s1f, js, mat in (
        (0.00, 0.38, (1, 2), "AA_Panel"),      # chevron bleu d'emplanture
        (0.26, 0.72, (5, 6), "AA_Panel"),      # aplat bleu mi-corde
        (0.60, 1.00, (1, 2), "AA_Panel"),      # bout d'aile
    ):
        faces = []
        for i in range(len(bands)):
            mid = (stations[i] + stations[i + 1]) * 0.5
            if s0f <= mid <= s1f:
                faces += [bands[i][j] for j in js]
        faces = _insettable(faces, 0.006)
        if faces:
            ak.inset_panel(bm, faces, "AA_Hull", thickness=0.005, depth=-0.004)
            ak.inset_panel(bm, faces, mat, thickness=0.006, depth=-0.005)
    # tranche doree du bord d'attaque externe + un court marquage rouge
    for i in range(len(bands)):
        mid = (stations[i] + stations[i + 1]) * 0.5
        if 0.20 <= mid <= 0.62:
            ak.set_material(
                [bands[i][2 * n - 1]],
                "AA_Marking_Red" if 0.34 <= mid <= 0.46 else "AA_Trim",
            )

    # --- ferrure de charniere : elle plonge vers la chape de la nacelle ----
    # ⚠️ C'est la piece la plus CONTRAIGNANTE de toute l'aile pour la fleche :
    # son coin arriere-interne est le point dont l'angle polaire est le plus
    # grand, donc le premier a passer derriere le pivot en se repliant. Une
    # premiere version, centree 4 mm plus en dedans et 18 mm plus en arriere,
    # faisait tomber la fleche admissible de 32 a 28 deg — mesure faite, pas
    # devinee, exactement comme pour le volet de BRIEF-0034.
    ak.add_box(
        bm,
        (WING_PIVOT_X + 0.040, WING_PIVOT_Y - 0.008, WING_PIVOT_Z),
        (0.052, 0.100, 0.046),
        "AA_Greeble",
    )

    # --- lisse et feu de bout d'aile --------------------------------------
    (x_le, y_le), (x_te, y_te) = _wing_edges(1.0)
    y_te = min(y_te, FLAP_WALL_Y)
    z_tip = _wing_plane_z(1.0)
    ak.add_box(
        bm,
        (x_le - 0.014, (y_le + y_te) * 0.5, z_tip + 0.014),
        (0.030, abs(y_te - y_le) * 0.86, 0.030),
        "AA_Greeble",
    )
    ak.add_box(
        bm,
        (x_le - 0.014, (y_le + y_te) * 0.5, z_tip + 0.030),
        (0.020, abs(y_te - y_le) * 0.52, 0.012),
        "AA_Emissive_Engine",
    )

    # --- bandeaux et greebles de l'extrados -------------------------------
    for s, t, length in ((0.30, 0.42, 0.076), (0.66, 0.38, 0.066)):
        (lx, ly), (tx, ty) = _wing_edges(s)
        x = lx + (tx - lx) * t
        y = min(ly + (ty - ly) * t, FLAP_WALL_Y - 0.030)
        ak.add_box(
            bm,
            (x, y, _wing_plane_z(s) + _wing_thickness(s, t) + 0.002),
            (0.014, length, 0.010),
            "AA_Emissive_Engine",
        )
    (ax, ay), (bx, by) = _wing_edges(0.28)
    (cx2, cy2), (dx2, dy2) = _wing_edges(0.82)
    ak.greeble_strip(
        bm,
        (ax + (bx - ax) * 0.55, min(ay + (by - ay) * 0.55, FLAP_WALL_Y - 0.04),
         _wing_plane_z(0.28) + _wing_thickness(0.28, 0.55)),
        (cx2 + (dx2 - cx2) * 0.55, min(cy2 + (dy2 - cy2) * 0.55, FLAP_WALL_Y - 0.04),
         _wing_plane_z(0.82) + _wing_thickness(0.82, 0.55)),
        count=5,
        seed=SEED + 31,
        size_range=(0.014, 0.028),
        height_range=(0.005, 0.011),
    )

    # Miroir final (voir l'avertissement en tete de fonction). Les greebles sont
    # donc STRICTEMENT symetriques d'un cote a l'autre : c'est un gain, la
    # dissymetrie n'ayant jamais ete voulue sur un chasseur Vanguard.
    if side < 0:
        for vert in bm.verts:
            vert.co.x = -vert.co.x
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])

    return ak.moving_part(
        f"Wing_{tag}", bm, (side * WING_PIVOT_X, WING_PIVOT_Y, WING_PIVOT_Z)
    )


def build_flap(side: float) -> ak.MovingPart:
    """Volet de bord de fuite, ENFANT de l'aile (`parent="Wing_L/R"`).

    Sans ce parentage, le volet resterait en l'air des que l'aile se replie —
    c'est exactement le manque que `ak.moving_part(parent=...)` vient combler.

    ⚠️ Le PIVOT reste exprime dans le repere d'auteur ; `export_hull()` le rend
    relatif au parent. La charniere est parallele a X : c'est le seul axe qui
    reste un axe de nœud une fois l'aile en fleche, puisque `moving_part`
    n'exporte pas de rotation.
    """
    tag = "L" if side > 0 else "R"
    bm = bmesh.new()

    # Le volet occupe la matiere que l'aile a laissee derriere `FLAP_HINGE_Y`.
    # On balaie l'envergure DEPUIS `_flap_root_s()` — la meme fonction que le
    # logement de l'aile interroge, de sorte que les deux pieces ne peuvent pas
    # diverger d'un build a l'autre.
    s0 = _flap_root_s()
    ribs = []
    for k in range(7):
        s = s0 + (1.0 - s0) * k / 6.0
        (x_le, y_le), (x_te, y_te) = _wing_edges(s)
        span = max(y_te - y_le, 1e-6)
        t0 = min(max((FLAP_HINGE_Y - y_le) / span, 0.0), 1.0)
        z0 = _wing_plane_z(s)
        top, bot = [], []
        for u in (0.0, 0.28, 0.56, 0.80, 1.0):
            t = t0 + (1.0 - t0) * u
            x = x_le + (x_te - x_le) * t
            y = y_le + (y_te - y_le) * t
            h = max(_wing_thickness(s, t), 0.0042)
            top.append((side * x, y, z0 + h))
            bot.append((side * x, y, z0 - h))
        ribs.append(ak.add_ring(bm, top + list(reversed(bot))))

    n = 5
    for i in range(len(ribs) - 1):
        band = ak.bridge_rings(bm, ribs[i], ribs[i + 1], "AA_Hull")
        ak.set_material([band[n - 1]], "AA_Trim")       # tranche de bord de fuite
        ak.set_material([band[2 * n - 1]], "AA_Greeble")  # face de charniere
    ak.cap_ring(bm, list(reversed(ribs[0])), "AA_Greeble")
    ak.cap_ring(bm, ribs[-1], "AA_Greeble")

    # Le x du pivot ne change RIEN au mouvement (une rotation autour d'un axe
    # parallele a X laisse x invariant) — il place seulement le nœud. On le met
    # au milieu de la ligne de charniere, pour qu'il soit dans la piece.
    xs = [v.co.x for v in bm.verts]
    pivot = ((min(xs) + max(xs)) * 0.5, FLAP_HINGE_Y, FLAP_HINGE_Z)
    return ak.moving_part(f"Flap_{tag}", bm, pivot, parent=f"Wing_{tag}")


def build_nozzle(side: float) -> ak.MovingPart:
    """Couronne de petales de tuyere, FERMEE au repos.

    Elle sera mise a l'ECHELLE cote Godot (pas tournee) : le pivot est donc le
    centre du COL, et la couronne s'ouvre en s'evasant autour de lui.
    Les petales du haut sont raccourcis de `PETAL_SCARF` : c'est ce biseau qui
    laisse voir la vasque emissive depuis une camera a 20 deg de la verticale.
    """
    tag = "L" if side > 0 else "R"
    cx, cz = side * NACELLE_X, NACELLE_Z
    bm = bmesh.new()

    step = 2.0 * math.pi / NOZZLE_PETALS
    gap = math.radians(PETAL_GAP_DEG)
    last = len(PETAL_SECTIONS) - 1
    for p in range(NOZZLE_PETALS):
        mid = p * step
        a0, a1 = mid - step * 0.5 + gap * 0.5, mid + step * 0.5 - gap * 0.5
        scarf = PETAL_SCARF * (0.5 + 0.5 * math.sin(mid))
        angles = [a0 + (a1 - a0) * k / (PETAL_ARC - 1) for k in range(PETAL_ARC)]
        rings = []
        for k, (y, r_in, r_out) in enumerate(PETAL_SECTIONS):
            yy = y - scarf * (k / last)
            outer = [
                (cx + r_out * math.cos(a), yy, cz + r_out * math.sin(a))
                for a in angles
            ]
            inner = [
                (cx + r_in * math.cos(a), yy, cz + r_in * math.sin(a))
                for a in reversed(angles)
            ]
            rings.append(ak.add_ring(bm, outer + inner))
        for i in range(len(rings) - 1):
            mat = "AA_Trim" if i == len(rings) - 2 else "AA_Greeble"
            ak.bridge_rings(bm, rings[i], rings[i + 1], mat)
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
        ak.cap_ring(bm, rings[-1], "AA_Trim")

    pivot = (cx, PETAL_SECTIONS[0][0], cz)
    return ak.moving_part(f"Nozzle_{tag}", bm, pivot)


# ==========================================================================
# Points d'attache
# ==========================================================================


def _wing_le_point(s: float) -> tuple[float, float, float]:
    """Point du bord d'attaque de l'aile a l'envergure `s`, legerement en avant."""
    (x_le, y_le), _ = _wing_edges(s)
    return (x_le, y_le - 0.030, _wing_plane_z(s))


def build_attach_points() -> list:
    """Positions **derivees de la geometrie**, jamais devinees.

    Les offsets de tir et de trainee du controleur joueur sont lus ici : une
    approximation se verrait a l'ecran. Les sept muzzles mappent l'echelle de
    puissance (spec 9.1) : twin de nez (Muzzle_L/R) des le power 1, canons
    d'aile (Muzzle_Wing_L/R) au power 3, canon d'axe (Muzzle_C) au power 4,
    pods de bout d'aile (Muzzle_Tip_L/R) au power 5.

    ⚠️ LIMITE CONNUE, signalee au rapport de BRIEF-0035 : `Muzzle_Wing_*` et
    `Muzzle_Tip_*` sont desormais sur une PIECE MOBILE, mais `ak.attach_point()`
    ne sait creer qu'un Empty a la racine — le kit n'expose pas de parentage
    pour les points d'attache. Les deux paires restent donc figees a la position
    « ailes deployees ». Sans consequence sur le tir (les offsets sont lus une
    fois), visible seulement si l'on veut faire partir un flash du canon d'aile
    en fleche maximale.
    """
    points: list = []

    # --- twin de nez : dans l'axe des tubes, juste devant leur pointe. --------
    points += list(ak.attach_pair("Muzzle", BARREL_X, MUZZLE_Y, _barrel_z()))

    # --- canon d'axe central : entre les deux tubes, meme plan de tir. --------
    points.append(ak.attach_point("Muzzle_C", (0.0, MUZZLE_Y, _barrel_z())))

    # --- canons d'aile et pods de bout d'aile : sur le bord d'attaque de la
    #     LAME, a une fraction d'envergure. BRIEF-0035 : c'est un changement de
    #     DERIVATION rendu obligatoire par le plan — l'aile ne commence plus
    #     qu'a |x| = 0,545, si bien que les abscisses absolues 0,500 et 0,800
    #     ne designaient plus rien. Les inverser sur `PLANFORM`, qui ne decrit
    #     plus que le fuselage, aurait leve une `ContractError` a chaque build.
    x_wing, y_wing, z_wing = _wing_le_point(WING_MUZZLE_S)
    points += list(ak.attach_pair("Muzzle_Wing", x_wing, y_wing, z_wing))

    x_tip, y_tip, z_tip = _wing_le_point(TIP_MUZZLE_S)
    points += list(ak.attach_pair("Muzzle_Tip", x_tip, y_tip, z_tip))

    # --- tuyeres : DERRIERE la couronne de petales, sinon la plume de trainee
    #     sortirait du milieu de la tuyere et traverserait les petales. Le z
    #     suit l'axe releve de la vasque.
    exit_y = PETAL_SECTIONS[-1][0] + 0.004
    points += list(
        ak.attach_pair("Engine", NACELLE_X, exit_y, NACELLE_Z + 0.018)
    )

    # --- cockpit : centre du volume de verriere. ------------------------------
    y_mid = (CANOPY[0][0] + CANOPY[-1][0]) * 0.5
    peak = max(CANOPY, key=lambda s: s[2])
    z_mid = lerp_table(CROWN, y_mid) - CANOPY_SINK + peak[2] * 0.45
    points.append(ak.attach_point("Cockpit", (0.0, y_mid, z_mid)))

    return points


# ==========================================================================
# Assemblage
# ==========================================================================


def _triangulate_ngons(obj) -> None:
    """Triangule les seules n-gons (> 4 sommets), en place.

    Sans cela, l'exporteur glTF renonce aux tangentes (« Tangent space can only
    be computed for tris/quads ») et ADR-0011 §2 — qui exige *UV et tangentes*
    pour que les feuilles de detail aient un espace normal — reste inapplique.
    Les n-gons viennent des culots (`ak.cap_ring`), une poignee de faces : on ne
    triangule pas les quads, qui restent lisibles et n'ont aucun probleme.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(obj.data)
    bm.free()


def _finish(obj, bevel: float, segments: int = 1) -> None:
    """Passe de finition commune a la coque et aux pieces mobiles."""
    ak.cleanup(obj)
    # Chanfrein a UN segment, plus etroit (3,5 mm) que la moitie du creux des
    # rainures (5 mm) et des panneaux (11 mm) : la marche reste franche.
    # ADR-0011 autorise 2 segments ; essaye au rendu, il arrondit les rainures
    # fines au point de les effacer — c'est exactement le defaut « plastique
    # moule » qu'on corrige. On reste donc a 1 segment : choix de LECTURE.
    ak.bevel_sharp_edges(obj, width=bevel, segments=segments, angle_deg=34.0)
    ak.shade_smooth_by_angle(obj, angle_deg=34.0)
    _triangulate_ngons(obj)
    # UV par projection en boite (ADR-0011 §2) : support des feuilles de detail
    # repetables en niveaux de gris, appliquees cote Godot. Aucune texture n'est
    # embarquee dans le .glb — seulement les coordonnees.
    ak.box_project_uv(obj, TEXELS_PER_METER)


def _flap_travel_limit(part: ak.MovingPart) -> float:
    """Plafond de braquage du volet, en degres, MESURE sur le maillage livre.

    Le volet tourne autour d'un axe parallele a X passant par son pivot. Un
    sommet (y, z) va en
        y' = y_p + (y - y_p) cos t - (z - z_p) sin t
    et mord la cloison des que `y' < FLAP_WALL_Y`. Le plafond est le plus
    petit angle qui fait mordre UN sommet, dans l'un ou l'autre sens.

    Pourquoi le mesurer plutot que le calculer : la valeur depend de la forme
    du volet, donc de la corde de l'aile au bord de fuite, donc du plan. Elle
    change des qu'on touche a la silhouette — et `ShipFlight` est regle dessus.
    """
    _, y_p, z_p = part.pivot
    limit = math.pi * 0.5
    for vert in part.obj.data.vertices:
        # repere d'auteur : le maillage n'a pas encore ete transporte en Godot
        dy, dz = vert.co.y - y_p, vert.co.z - z_p
        for sign in (1.0, -1.0):
            # resout dy*cos(t) - sign*dz*sin(t) = -(y_p - FLAP_WALL_Y)
            a, b = dy, -sign * dz
            target = FLAP_WALL_Y - y_p           # negatif (= -FLAP_GAP)
            radius = math.hypot(a, b)
            if radius < 1e-9 or abs(target) > radius:
                continue                          # ce sommet ne mord jamais
            phase = math.atan2(b, a)
            angle = math.acos(target / radius) + phase
            # ramene dans (0, pi/2] : hors de cette plage, ce n'est plus un
            # braquage de volet mais un demi-tour de la piece.
            angle = angle % (2.0 * math.pi)
            if 1e-4 < angle <= math.pi * 0.5:
                limit = min(limit, angle)
    return math.degrees(limit)


def _wing_sweep_limit(wing: ak.MovingPart, flap: ak.MovingPart) -> tuple[float, str]:
    """Fleche maximale admissible, en degres, MESUREE sur le maillage livre.

    C'est la reponse directe au piege que le brief demande de traiter : le
    contrat de `export_hull()` ne connait QUE la pose de repos. Une aile qui
    deborde une fois repliee, ou qui entre dans la nacelle, le passerait sans un
    mot — exactement comme le volet de BRIEF-0034 dont le debattement reel etait
    tombe a 2,8 deg sous un contrat parfaitement vert.

    On balaie donc l'angle par pas de 0,25 deg et on teste, sommet par sommet et
    pour l'aile ET son volet (qui la suit, etant son enfant), trois choses :

      1. |x| <= |x| AU REPOS                    — la boite englobante en largeur
      2. |y| <= HALF_L                          — la boite englobante en longueur
      3. |x| >= nacelle_half_width(y) + garde   — la peau du fuseau

    La reference du test 1 est l'etendue REELLE de la piece au repos, chanfrein
    compris, et non `HALF_W` : la lame touche l'envergure contractuelle par
    construction, et un demi-millimetre de chanfrein aurait suffi a faire echouer
    la mesure a l'angle zero.

    Retourne (angle, motif de l'arret).
    """
    px, py, _ = wing.pivot
    pts = [(abs(v.co.x), v.co.y) for v in wing.obj.data.vertices]
    pts += [(abs(v.co.x), v.co.y) for v in flap.obj.data.vertices]
    # En polaire autour du pivot, cote babord (|x| : les deux ailes sont
    # symetriques, une seule mesure suffit et vaut pour l'autre).
    polar = []
    for ax, y in pts:
        dx, dy = ax - abs(px), y - py
        polar.append((math.hypot(dx, dy), math.atan2(dy, dx)))
    x_rest = max(abs(px) + r * math.cos(phi) for r, phi in polar)

    reason = "aucune butee sous 45 deg"
    limit = 45.0
    step = 0.25
    theta = 0.0
    while theta <= 45.0:
        rad = math.radians(theta)
        for r, phi in polar:
            x = abs(px) + r * math.cos(phi + rad)
            y = py + r * math.sin(phi + rad)
            if x > x_rest + 1e-4:
                return theta - step, f"largeur ({x:.4f} > {x_rest:.4f} au repos)"
            if abs(y) > HALF_L + 1e-4:
                return theta - step, f"longueur ({y:+.4f} hors +/-{HALF_L:.3f})"
            half = nacelle_half_width(y)
            # ⚠️ `nacelle_half_width` rend un RAYON : la peau est a
            # `NACELLE_X + rayon`. Comparer x au rayon seul faisait passer
            # 45 deg de fleche pour admissibles alors que l'aile traversait le
            # fuseau des 33 — le genre d'erreur qu'une mesure « verte » cache.
            if half > 0.0 and x < NACELLE_X + half + WING_CLEARANCE:
                return theta - step, (
                    f"peau de nacelle a y = {y:+.3f} "
                    f"(x = {x:.4f}, peau {NACELLE_X + half:.4f})"
                )
        theta += step
    return limit, reason


def _wing_inboard_x(y: float) -> float:
    """|x| minimal de la LAME a la station `y`, ou -1 si l'aile n'y est pas.

    Echantillonne le plan de l'aile (envergure x corde) plutot que de resoudre
    analytiquement : le bord de fuite est tronque par le logement du volet, et
    une formule fermee mentirait des qu'on bougera `FLAP_HINGE_Y`.
    """
    best = -1.0
    for k in range(81):
        s = k / 80.0
        (lx, ly), (tx, ty) = _wing_edges(s)
        for m in range(41):
            t = m / 40.0
            x = lx + (tx - lx) * t
            yy = ly + (ty - ly) * t
            if abs(yy - y) <= 0.006:
                best = x if best < 0.0 else min(best, x)
    return best


def _print_silhouette_gaps() -> None:
    """Mesure, station par station, la LARGEUR DES FENTES vues de dessus.

    C'est le critere d'acceptation de BRIEF-0035 exprime en chiffres. L'aplat
    noir reste le juge ; cette mesure sert a savoir POURQUOI une fente s'est
    refermee quand elle se referme — la bounding box, elle, ne mesure pas les
    trous, et c'est precisement ce qui a laissé passer deux briefs.
    """
    print("  fentes vues de dessus (demi-envergure, cote babord) :")
    for label, y in (
        ("nez de nacelle   ", -0.360),
        ("avant du caisson ", -0.100),
        ("caisson (fermee) ", 0.200),
        ("arriere caisson  ", 0.560),
        ("emplanture d'aile", 0.300),
        ("poupe            ", 0.960),
    ):
        fus = section_cut(y)
        nac_lo = NACELLE_X - nacelle_half_width(y)
        nac_hi = NACELLE_X + nacelle_half_width(y)
        bridged = BRIDGE[0][0] <= y <= BRIDGE[-1][0]
        gap1 = 0.0 if bridged else max(nac_lo - fus, 0.0)
        # fente 2 : de la peau du fuseau au point le plus interne de la lame.
        inboard = _wing_inboard_x(y)
        g2 = "aile absente" if inboard < 0.0 else f"{(inboard - nac_hi) * 1000:5.0f} mm"
        print(
            f"    y = {y:+.3f}  {label} : "
            f"fente 1 = {gap1 * 1000:5.0f} mm | fente 2 = {g2}"
        )


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_VANGUARD)

    ship = ak.join_objects([build_hull(), build_details()], "Specter9")
    _finish(ship, bevel=0.0035)

    wings = [build_wing(ak.PORT), build_wing(ak.STARBOARD)]
    flaps = [build_flap(ak.PORT), build_flap(ak.STARBOARD)]
    parts = wings + flaps + [build_nozzle(ak.PORT), build_nozzle(ak.STARBOARD)]
    for part in parts:
        _finish(part.obj, bevel=0.0022)

    travel = min(_flap_travel_limit(p) for p in flaps)
    sweep, reason = _wing_sweep_limit(wings[0], flaps[0])

    report = ak.export_hull(
        ship, build_attach_points(), OUTPUT, CONTRACT, parts=parts
    )

    # Le contrat du kit ne borne qu'un PLAFOND de hauteur. Le defaut corrige par
    # BRIEF-0033 etait l'inverse : une coque trop PLATE reste conforme. On
    # verifie donc le plancher ici, et on echoue bruyamment.
    if report.size[1] < MIN_HEIGHT_Y:
        raise ak.ContractError(
            f"hauteur Y = {report.size[1]:.4f} m < plancher {MIN_HEIGHT_Y:.2f} m "
            "(BRIEF-0033 : la coque doit cesser de lire comme une plaque)"
        )
    # ... et il ne borne QUE la pose de repos. Le debattement de fleche est donc
    # verifie ici, sur le maillage livre, et il est bloquant.
    if sweep < WING_SWEEP_TARGET:
        raise ak.ContractError(
            f"fleche admissible mesuree = {sweep:.2f} deg < cible "
            f"{WING_SWEEP_TARGET:.1f} deg — butee : {reason}\n"
            "  (BRIEF-0035 : la bbox est mesuree AU REPOS, elle ne voit pas ce defaut)"
        )
    print(
        f"  hauteur/longueur : {report.size[1] / report.size[2]:.1%} "
        f"(cible BRIEF-0034 : 25-29 %)"
    )
    print(f"  volets : plafond de debattement mesure {travel:.1f} deg")
    print(
        f"  ailes  : fleche admissible mesuree {sweep:.2f} deg "
        f"(cible {WING_SWEEP_TARGET:.0f}) — premiere butee : {reason}"
    )
    _print_silhouette_gaps()


if __name__ == "__main__":
    main()
