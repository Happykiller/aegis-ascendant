"""build_specter_9_c.py — le Specter-9 TALVERN, la cellule-temoin (BRIEF-0098, ADR-0044).

    ./scripts/build-hull.sh specter_9_c          (JAMAIS `blender45 -b -P` a la main :
    ./scripts/build-hull.sh --check specter_9_c   le script force `-t 1`, sans quoi les
                                                  tangentes divergent d'un run a l'autre)

Produit `assets/imported/models/ships/specter_9_c.glb` : une coque + TRENTE-NEUF
pieces mobiles exportees en nœuds glTF separes :

    Wing_L/R              fleche variable, axe vertical, pivot au flanc de nacelle
      Flap_L/R            enfants des ailes, charniere le long de X
    Nozzle_L/R            corps de tuyere ENTIER (col, chambre, anneau) ; pivot SUR
                          L'AXE, dans le plan des charnieres de petales ; lacet +/-6 deg
      Petal_L/R_00..11    douze petales par tuyere, enfants de la tuyere, charniere
                          tangente au cercle des charnieres
    Airbrake_L/R          aerofreins dorsaux, charniere AVANT le long de X
    Intake_L/R            rampe d'entree d'air, charniere AVANT le long de X
    Rudder_L/R            gouverne de derive, axe = l'axe de la derive (incline 30 deg)
    Grapple_L/R           grappins d'appontage, charniere le long de X sous le nez
    Canopy                verriere, charniere ARRIERE le long de X

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe et s'auto-valide : `ak.export_hull()` relit le `.glb` produit
et echoue si la bounding box, le garde-fou de triangles (400 000, ADR-0044 §2 —
un garde-fou d'accident, pas une cible), les materiaux, le pivot ou les points
d'attache sortent du contrat. Puis `_audit()` relit le fichier une seconde fois
pour compter `TEXCOORD_0`, mesurer l'aire par materiau et la densite de texels.

Repere d'auteur (ADR-0008) : nez -Y, dessus +Z, **babord +X** (cf. aegis_kit).


CE QUE CETTE COQUE EST — ET CE QU'ELLE N'EST PAS
================================================
C'est la MEME UNITE que `specter_9.glb` (ADR-0014 s'applique tel quel) : le plan de
`build_specter_9.py` est repris — partage de la demi-envergure, fentes traversantes,
emplanture polaire de BRIEF-0036, pivot d'aile enfoui, dix points d'attache. Les
cotes qui ont bouge sont toutes justifiees en commentaire a l'endroit ou elles
bougent ; le partage de la demi-envergure et les fentes n'ont PAS bouge.

Ce qui change, c'est l'EXECUTION (BRIEF-0098 §direction) :

  * echelle 1 — silhouette : identique au plan, masses a la meme place ;
  * echelle 2 — cassures : rainures creusees a 5-6 mm, panneaux en retrait a deux
    niveaux, biseaux a DEUX segments sur la peau (trois sur les couronnes de tuyere
    et le cadre de verriere) ;
  * echelle 3 — mecanique, dans les zones techniques SEULEMENT : cadre de verriere
    et cockpit, tuyeres a rotule et douze petales, carter de pivot, baies
    d'aerofrein avec verins, gorge d'entree d'air, logements de grappin.
    Un chasseur est lisse ; ses zones techniques sont denses.


LES PLAFONDS MECANIQUES SE REMESURENT A CHAQUE BUILD (BRIEF-0035/0036)
======================================================================
Le contrat de `export_hull()` ne connait que la pose de REPOS. Une piece qui
traverse sa voisine une fois ouverte le passerait sans un mot — c'est le piege
qui a fait tomber un volet a 2,8 deg sous une bbox parfaite (BRIEF-0034). Chaque
famille a donc ici sa mesure, faite SUR LE MAILLAGE LIVRE, et le build ECHOUE
sous la cible du brief :

    famille      cible       methode
    Wing         >= 30 deg   polaire (peau de nacelle, bbox, fuselage) — BRIEF-0035
    Flap         +/-14 deg   cloison d'echancrure — BRIEF-0034 ; emplanture — BRIEF-0036
    Nozzle       +/-6 deg    balayage BVH contre la douille de nacelle
    Petal        >= 20 deg   balayage BVH contre tuyere, nacelle, petales voisins
    Airbrake     >= 55 deg   balayage BVH contre coque, derives, verriere
    Intake       >= 12 deg   balayage BVH contre nacelle, emplanture, fuselage
    Rudder       +/-22 deg   balayage BVH contre derive, carenage, nacelle
    Grapple      >= 90 deg   balayage BVH contre quille, tubes de canon
    Canopy       >= 35 deg   balayage BVH contre coque (puits, dosseret, arete)

Le balayage BVH (`_sweep_family`) tourne les sommets de la piece autour de sa
charniere par pas de 1 deg et interroge un arbre BVH de chaque voisin : distance
au plus proche point de surface, et signe (interieur/exterieur) par la normale.
Il s'arrete a la premiere image ou une distance passe sous `CLEARANCE_MIN`. Le
rapport final donne, pour chaque couple (piece ouverte x voisine), le jeu minimal
en millimetres a la cible du brief : c'est la « table des degagements ».


AXES ET SIGNES : MESURES SUR LE .GLB, JAMAIS DEDUITS
====================================================
`_audit()` relit le `.glb` produit et, pour chaque famille, applique une rotation
de +5 deg autour de l'axe candidat aux sommets locaux du nœud, puis regarde dans
quel sens la piece est partie (le bout d'aile recule-t-il ? le petale s'ecarte-t-il
de l'axe ? le bord de fuite de la gouverne va-t-il a babord ?). C'est ce signe-la,
et pas celui que la construction laisse supposer, qui est imprime pour `ShipFlight`.


TEXTURES (ADR-0028) — LA FORGE NE LIVRE QUE LES UV
==================================================
Trois zones, depliees SEPAREMENT (par materiau dans la coque, par nœud pour les
tuyeres), densites mesurees sur le `.glb` par valeurs singulieres (BRIEF-0089) :

    TEX-0017  coque hors AA_Greeble        boite, 2,5 tuiles/m (0,40 m par tuile)
    TEX-0018  AA_Greeble de la coque       boite, 4,0 tuiles/m (0,25 m par tuile)
    TEX-0019  Nozzle_* et Petal_*          CYLINDRIQUE autour de l'axe de tuyere,
                                           2 tuiles au tour, v a la meme densite

Aucune texture n'est embarquee : les materiaux du `.glb` sont des couleurs unies.
"""

from __future__ import annotations

import math
import os
import struct
import sys

import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402  (doit suivre l'ajout au sys.path)

if tuple(int(p) for p in ak.VERSION.split(".")) < (1, 2, 0):
    raise ak.ContractError(
        f"aegis_kit {ak.VERSION} : ce script a besoin des ajouts de la 1.2.0 "
        "(depliage cylindrique, projection par materiau, tubes, verins)"
    )

# ==========================================================================
# Contrat (ADR-0008 pour les dimensions, ADR-0044 pour le garde-fou)
# ==========================================================================

MIN_HEIGHT_Y = 0.62
MAX_HEIGHT_Y = 0.72

CONTRACT = ak.HullContract(
    name="Specter-9 Talvern",
    width_x=1.75,       # Godot X — contrat de gameplay (hitbox), ailes deployees
    length_z=2.46,      # Godot Z — idem
    max_height_y=MAX_HEIGHT_Y,
    #: ADR-0044 §2 : ce n'est plus un plafond de qualite mais un garde-fou
    #: d'ACCIDENT. Au-dela, c'est un biseau a trop de segments ou une revolution
    #: sur-echantillonnee, pas du detail.
    tri_budget=400_000,
    required_materials=ak.MATERIAL_ORDER,
    required_attach_points=(
        "Muzzle_L", "Muzzle_R", "Muzzle_Wing_L", "Muzzle_Wing_R", "Muzzle_C",
        "Muzzle_Tip_L", "Muzzle_Tip_R", "Engine_L", "Engine_R", "Cockpit",
    ),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/ships/specter_9_c.glb")

SEED = 90211  # graine unique de la cellule-temoin (la coque en service a 90210)

#: ⛔ PERIMEES depuis ADR-0047 (2026-09-05) — gardees comme trace, plus lues nulle part.
#: Elles calaient le depliage par zones de BRIEF-0098 §Texture (une tuile = 0,40 m sur
#: la peau, 0,25 m dans les baies, deux tuiles au tour de chaque tuyere) pour accueillir
#: trois feuilles REPETABLES, TEX-0017 a TEX-0019, jamais commandees. La coque est
#: desormais depliee en ATLAS : un seul carre UV, des ilots disjoints, un albedo peint.
_PERIMEES_HULL_TILES_PER_M = 2.5
_PERIMEES_GREEBLE_TILES_PER_M = 4.0
_PERIMEES_NOZZLE_TILES_AROUND = 2.0

#: Jeu minimal admis entre une piece mobile et sa voisine, a toute pose de la
#: plage cible. En deca, le build ECHOUE.
CLEARANCE_MIN = 0.0025

HALF_L = CONTRACT.length_z / 2.0   # 1.230 — nez en -Y, poupe en +Y
HALF_W = CONTRACT.width_x / 2.0    # 0.875 — bout d'aile

# ==========================================================================
# Tables de profil — reprises de build_specter_9.py (BRIEF-0034..0036)
# ==========================================================================
# Le PARTAGE DE LA DEMI-ENVERGURE ne bouge pas :
#     0,000 .. 0,130   fuselage        0,130 .. 0,172   FENTE 1 (42 mm)
#     0,172 .. 0,368   nacelle         0,368 .. 0,426   FENTE 2 (58 mm)
#     0,426 .. 0,875   aile

PLANFORM: list[tuple[float, float]] = [
    (-1.2300, 0.0000), (-1.1500, 0.0165), (-1.0800, 0.0269), (-0.9800, 0.0416),
    (-0.9000, 0.0533), (-0.8000, 0.0672), (-0.6800, 0.0836), (-0.5400, 0.0992),
    (-0.4000, 0.1114), (-0.2400, 0.1213), (-0.0500, 0.1283), (0.1300, 0.1300),
    (0.3100, 0.1287), (0.4700, 0.1239), (0.6100, 0.1166), (0.7600, 0.1053),
    (0.9000, 0.0923), (1.0300, 0.0780),
]

FUSELAGE: list[tuple[float, float]] = [
    (-1.2300, 0.0000), (-1.1500, 0.0100), (-1.0800, 0.0165), (-0.9800, 0.0256),
    (-0.9000, 0.0329), (-0.8000, 0.0416), (-0.6800, 0.0520), (-0.5400, 0.0620),
    (-0.4000, 0.0698), (-0.2400, 0.0758), (-0.0500, 0.0802), (0.1300, 0.0815),
    (0.3100, 0.0806), (0.4700, 0.0776), (0.6100, 0.0728), (0.7600, 0.0659),
    (0.9000, 0.0576), (1.0300, 0.0485),
]

CROWN: list[tuple[float, float]] = [
    (-1.2300, 0.000), (-1.1500, 0.026), (-1.0800, 0.040), (-0.9250, 0.070),
    (-0.8120, 0.094), (-0.6910, 0.122), (-0.5510, 0.152), (-0.4130, 0.174),
    (-0.2410, 0.192), (0.0540, 0.202), (0.2190, 0.205), (0.4180, 0.203),
    (0.5730, 0.196), (0.7450, 0.186), (0.8600, 0.178), (0.9600, 0.170),
    (1.0300, 0.162),
]

BELLY: list[tuple[float, float]] = [
    (-1.2300, 0.000), (-1.1500, -0.024), (-1.0800, -0.036), (-0.9250, -0.064),
    (-0.8120, -0.086), (-0.6910, -0.110), (-0.5510, -0.136), (-0.4130, -0.158),
    (-0.2410, -0.172), (0.0540, -0.182), (0.2190, -0.185), (0.4180, -0.183),
    (0.5730, -0.177), (0.7450, -0.168), (0.8600, -0.160), (0.9600, -0.152),
    (1.0300, -0.146),
]

# --------------------------------------------------------------------------
# Ailes (polaire autour du pivot — BRIEF-0035/0036, inchange)
# --------------------------------------------------------------------------
WING_PIVOT_X = 0.3980
WING_PIVOT_Y = 0.0300
WING_PIVOT_Z = 0.0120
WING_TIP_X = HALF_W
WING_LE_ROOT = (0.0280, 8.0)
WING_LE_TIP_ANGLE = 28.0
WING_TE_ROOT = (0.4600, 60.0)
WING_TE_TIP_ANGLE = 44.0
#: BRIEF-0098 : la cible monte de 26 a 30 deg. La garantie polaire demande
#: `phi + fleche <= 90` avec phi = 60 a l'emplanture du bord de fuite : il reste
#: 30 deg, la cible les consomme tous — c'est la mesure qui tranche.
WING_SWEEP_TARGET = 30.0
WING_CLEARANCE = 0.012
WING_RIBS: tuple[float, ...] = (0.000, 0.180, 0.360, 0.540, 0.720, 0.880, 1.000)
#: Fractions de corde. Resserrees vers le bord d'attaque (0,02 / 0,05) : un bord
#: d'attaque ROND demande deux echantillons dans ses premiers centimetres, sinon le
#: profil « reel » du brief se lit comme un coin.
WING_CHORD_T: tuple[float, ...] = (
    0.000, 0.020, 0.050, 0.110, 0.180, 0.300, 0.345, 0.500, 0.700, 0.745,
    0.880, 1.000,
)
WING_THICK_ROOT = 0.0300
WING_THICK_TIP = 0.0130
#: Position du maitre-couple du profil, en fraction de corde. Un profil de
#: voilure a son epaisseur maximale vers 30 % : c'est ce qui donne un bord
#: d'attaque rond et un bord de fuite fin — la lentille symetrique du plan de
#: depart avait le sien a 50 %.
WING_PEAK_T = 0.32
WING_ANHEDRAL = 0.0260
FLAP_HINGE_Y = 0.3820
FLAP_GAP = 0.0110
FLAP_WALL_Y = FLAP_HINGE_Y - FLAP_GAP
FLAP_HINGE_Z = 0.0060
FLAP_MIN_CHORD = 0.026
FLAP_TRAVEL_TARGET = 14.0

# --------------------------------------------------------------------------
# Stations longitudinales et rainures (inchangees)
# --------------------------------------------------------------------------
BASE_STATIONS: tuple[float, ...] = (
    -1.2300, -1.1900, -1.1400, -1.0800, -1.0200, -0.9600, -0.9000, -0.8400,
    -0.7800, -0.7200, -0.6600, -0.6000, -0.5400, -0.4700, -0.4000, -0.3300,
    -0.2600, -0.2000, -0.1300, -0.0500, 0.0400, 0.1300, 0.2200, 0.3100,
    0.4000, 0.4700, 0.5400, 0.6100, 0.6890, 0.7600, 0.8100, 0.8600,
    0.9200, 0.9800, 1.0300,
)
#: Aucune station hors trame : la baie d'aerofrein prend ses bornes sur les
#: aretes des bandes de rainure 0,085 et 0,265 (voir `AIRBRAKE_Y0/Y1`) — une
#: station ajoutee entre deux aretes voisines laisserait une bande de 3 mm.
EXTRA_STATIONS: tuple[float, ...] = ()

LATERAL_SEAMS: tuple[tuple[float, str], ...] = (
    (-0.9900, "fus"), (-0.8700, "fus"), (-0.7500, "fus"), (-0.6300, "all"),
    (-0.5700, "all"), (-0.4350, "all"), (-0.3650, "all"), (-0.2300, "all"),
    (-0.0900, "all"), (-0.0050, "all"), (0.0850, "all"), (0.1750, "all"),
    (0.2650, "all"), (0.3550, "all"), (0.4350, "all"), (0.5050, "all"),
    (0.5750, "all"), (0.6495, "all"), (0.7245, "all"), (0.8900, "all"),
    (0.9500, "all"),
)
SEAM_HALF = 0.0070
#: BRIEF-0098 : 6 mm de creux (5 sur la coque en service). Avec un biseau a deux
#: segments de 3 mm, un creux de 5 mm perdait un tiers de sa marche ; a 6 mm la
#: rainure ombre encore apres postérisation (verifie a la planche « 20 niveaux »).
SEAM_T, SEAM_D = 0.0018, -0.0060
MIN_RUN_SEAM, MIN_EDGE_SEAM, MIN_BAND_SEAM = 0.0050, 0.0040, 0.0100
MIN_RUN_PLATE, MIN_EDGE_PLATE, MIN_BAND_PLATE = 0.0220, 0.0090, 0.0240


def _stations() -> list[float]:
    out = list(BASE_STATIONS) + list(EXTRA_STATIONS)
    for y, _ in LATERAL_SEAMS:
        out += [y - SEAM_HALF, y + SEAM_HALF]
    return sorted(out)


STATIONS: list[float] = _stations()

EDGE_H = 0.088
ANHEDRAL = 0.010
SPINE_HW = 0.044
CHEEK_FRAC = 0.42

# --------------------------------------------------------------------------
# Verriere et cockpit (BRIEF-0098 §2)
# --------------------------------------------------------------------------
CANOPY: list[tuple[float, float, float]] = [
    (-0.6400, 0.0000, 0.000),
    (-0.6120, 0.0176, 0.034),
    (-0.5750, 0.0311, 0.064),
    (-0.5300, 0.0419, 0.091),
    (-0.4750, 0.0487, 0.112),
    (-0.4150, 0.0514, 0.120),
    (-0.3550, 0.0514, 0.118),
    (-0.2950, 0.0487, 0.108),
    (-0.2350, 0.0439, 0.088),
    (-0.1900, 0.0365, 0.062),
    (-0.1500, 0.0271, 0.034),
    (-0.1100, 0.0000, 0.000),
]
#: BRIEF-0098 : la verriere est plus ETROITE que sur la coque en service (demi-
#: largeur 0,051 au lieu de 0,066) et plus COURTE (-0,640 -> -0,110) : elle doit
#: tenir DANS le puits (segments 4-7, demi-largeur 0,048 a 0,058, plancher de
#: -0,652 a -0,093), puisqu'elle en decolle a l'ouverture. Premiere version a
#: -0,660 : la pointe avant entrait de 29 mm dans la paroi du puits.
#: Assise de la verriere sous la ligne d'epine. La coque en service l'enfonce de
#: 26 mm dans un puits de 14 : la base du dome est NOYEE. Ici la verriere est une
#: piece mobile : sa base doit se poser SUR le plancher du puits, pas dedans.
CANOPY_SINK = 0.032
#: Profondeur du puits de cockpit (le creux dans le pont). 40 mm : il faut de la
#: place pour un berceau, un arceau et deux consoles sous 142 mm de bulle.
WELL_DEPTH = 0.040
#: Charniere de verriere : ARRIERE, le long de X (BRIEF-0098). Elle est posee
#: 8 mm en arriere de la pointe du dome et 6 mm au-dessus de sa base : la pointe,
#: en dessous et en avant de l'axe, descend de moins de 5 mm a 35 deg — dans le
#: puits, pas dans le dosseret.
CANOPY_HINGE_Y = CANOPY[-1][0] + 0.008
CANOPY_TARGET = 35.0
#: Les trois montants du cadre (BRIEF-0098 : « cadre AA_Trim a trois montants »),
#: en y ; largeur et epaisseur du montant.
CANOPY_MULLIONS: tuple[float, ...] = (-0.5750, -0.4150, -0.2350)
CANOPY_MULLION_W = 0.012
CANOPY_MULLION_T = 0.007

# --------------------------------------------------------------------------
# Nacelles (BRIEF-0035 pour le partage ; BRIEF-0098 pour l'entree et la douille)
# --------------------------------------------------------------------------
NACELLE_X = 0.270
NACELLE_Z = -0.040
#: 32 segments (24 sur la coque en service) : les tuyeres sont le point focal
#: arriere et la couronne de douze petales se lit sur leur rondeur.
NACELLE_SEGMENTS = 32
NACELLE_R = 0.098

#: Entree d'air (BRIEF-0098 §5) : la nacelle ne se ferme plus en cone plein mais
#: s'ouvre par une LEVRE OBLIQUE (le haut en avant du bas de `INTAKE_RAKE`), une
#: gorge sombre et un cone central. (y moyen de la levre, rayon externe, rayon de
#: gorge).
INTAKE_LIP_Y = -0.412
INTAKE_RAKE = 0.016          # le haut de la levre est a -0,428, le bas a -0,396
INTAKE_LIP_R = 0.046
INTAKE_THROAT_R = 0.036
INTAKE_THROAT_Y = -0.335     # fond de gorge
INTAKE_CONE_APEX_Y = -0.398  # pointe du cone central, dans la gorge
#: Rampe mobile (`Intake_*`) sur la levre superieure : de la charniere (avant) a
#: son bord arriere, demi-angle couvert autour du sommet, epaisseur.
INTAKE_RAMP_Y0 = -0.400
INTAKE_RAMP_Y1 = -0.300
INTAKE_RAMP_HALF_DEG = 46.0
INTAKE_RAMP_T = 0.006
INTAKE_RAMP_LIFT = 0.003     # jeu entre la rampe et la peau, au repos
INTAKE_TARGET = 12.0

#: Profil de revolution : commence a la LEVRE ARRIERE de l'entree d'air (-0,360)
#: — l'avant est bati a la main, oblique — et se termine par une DOUILLE creuse
#: (rebord a 0,985, paroi interne jusqu'a 0,928, fond a 0,925) dans laquelle
#: tourne le col de tuyere. Le col est dans `Nozzle_*`, pas ici.
#: Trois anneaux de panneau creuses sur la longueur : les bandes `AA_Panel` de
#: 0,088/-0,200, 0,640/0,780 et l'anneau technique 0,300/0,330 sont EN RETRAIT
#: (rayon -3 mm) et bordes de deux marches, au lieu d'etre peints.
NACELLE_PROFILE: list[tuple[float, float, str]] = [
    (-0.360, 0.0502, "AA_Hull"),
    (-0.300, 0.0599, "AA_Hull"),
    (-0.204, 0.0710, "AA_Hull"),
    (-0.200, 0.0713, "AA_Hull"),      # marche
    (-0.196, 0.0683, "AA_Panel"),     # anneau 1 en retrait
    (-0.084, 0.0772, "AA_Panel"),
    (-0.080, 0.0802, "AA_Hull"),      # marche
    (0.040, 0.0867, "AA_Hull"),
    (0.170, 0.0915, "AA_Hull"),
    (0.296, 0.0946, "AA_Hull"),
    (0.300, 0.0948, "AA_Greeble"),    # marche
    (0.304, 0.0918, "AA_Greeble"),    # anneau 2 : ceinture technique du pivot
    (0.356, 0.0918, "AA_Greeble"),
    (0.360, 0.0948, "AA_Hull"),
    (0.480, 0.0972, "AA_Hull"),
    (0.636, 0.0980, "AA_Hull"),
    (0.640, 0.0980, "AA_Panel"),      # marche
    (0.644, 0.0950, "AA_Panel"),      # anneau 3 en retrait
    (0.776, 0.0950, "AA_Panel"),
    (0.780, 0.0980, "AA_Hull"),
    (0.850, 0.0980, "AA_Hull"),
    (0.905, 0.0980, "AA_Hull"),
    (0.915, 0.1029, "AA_Greeble"),    # 1er anneau concentrique
    (0.940, 0.1029, "AA_Greeble"),
    (0.948, 0.0980, "AA_Hull"),
    (0.962, 0.0980, "AA_Greeble"),
    (0.972, 0.1053, "AA_Greeble"),    # collier mecanique
    (0.985, 0.1053, "AA_Greeble"),    # rebord de la douille
    (0.985, 0.0860, "AA_Greeble"),    # face annulaire du rebord
    (0.928, 0.0860, "AA_Greeble"),    # paroi interne (vers l'AVANT)
    (0.925, 0.0000, "AA_Greeble"),    # fond de douille
]
NACELLE_SOCKET_Y0 = 0.925
NACELLE_SOCKET_Y1 = 0.985
NACELLE_SOCKET_R = 0.086
#: Etendue en y de la nacelle vue de dessus (levre avant -> rebord de douille),
#: pour `nacelle_half_width()`.
NACELLE_Y_FRONT = INTAKE_LIP_Y - INTAKE_RAKE

# --- Tuyere a rotule (piece mobile `Nozzle_*`) -------------------------------
#: Le corps de tuyere ENTIER est dans le nœud : col (dans la douille), evasement,
#: anneau dore, chambre emissive, et les douze petales en enfants. Le pivot est
#: SUR L'AXE, a `NOZZLE_HINGE_Y` — le plan des charnieres de petales.
NOZZLE_HINGE_Y = 1.048
NOZZLE_BODY: list[tuple[float, float, str]] = [
    (0.934, 0.0000, "AA_Greeble"),    # pole, 9 mm en arriere du fond de douille
    (0.938, 0.0560, "AA_Greeble"),    # nez du col, dans la douille
    (0.960, 0.0660, "AA_Greeble"),
    (0.985, 0.0720, "AA_Greeble"),    # sortie de douille (jeu radial 14 mm)
    (0.999, 0.0840, "AA_Greeble"),    # evasement, HORS de la douille
    (1.010, 0.0940, "AA_Greeble"),
    (1.016, 0.0940, "AA_Trim"),
    (1.020, 0.1010, "AA_Trim"),       # anneau dore
    (1.038, 0.1010, "AA_Trim"),
    (1.042, 0.0940, "AA_Greeble"),
    (1.048, 0.0770, "AA_Greeble"),    # col — les petales s'y raccordent
]
#: Chambre emissive, EN AVANT du col, a axe RELEVE (BRIEF-0026 : a 20 deg de la
#: verticale une buse coaxiale ne montre rien). (y, rayon, decalage vertical).
NOZZLE_BORE: tuple[tuple[float, float, float], ...] = (
    (1.0480, 0.077, 0.000),
    (1.0300, 0.071, 0.012),
    (1.0000, 0.062, 0.020),
    (0.9750, 0.048, 0.024),
    (0.9600, 0.030, 0.026),
)
NOZZLE_FLOOR_Y = 0.9500
NOZZLE_YAW_TARGET = 6.0

# --- Couronne de petales (24 pieces mobiles, enfants des tuyeres) --------------
NOZZLE_PETALS = 12
PETAL_GAP_DEG = 2.4
PETAL_ARC = 4
PETAL_SCARF = 0.070
#: Rayon du cercle des charnieres : sur la PEAU EXTERNE du pied de petale
#: (0,093). Premiere version au milieu de l'epaisseur (0,085) : le coin externe
#: du pied avancait de 2,7 mm dans le cone du col a 20 deg et le balayage BVH
#: refusait. Sur la peau externe, le coin interne RECULE en s'ouvrant et le jeu
#: ne fait que croitre. Le pied est pose `PETAL_ROOT_GAP` en arriere du col.
PETAL_HINGE_R = 0.093
PETAL_ROOT_GAP = 0.003
PETAL_SECTIONS: tuple[tuple[float, float, float], ...] = (
    (1.0480, 0.077, 0.093),
    (1.0900, 0.075, 0.098),
    (1.1400, 0.075, 0.102),
    (1.1900, 0.078, 0.106),
    (1.2300, 0.083, 0.109),   # levre de sortie — POUPE (fixe la bbox)
)
PETAL_OPEN_TARGET = 20.0

# Carenage dorsal de nacelle (pied de derive).
FAIRING: list[tuple[float, float, float]] = [
    (0.180, 0.0000, 0.0000), (0.300, 0.0502, 0.0583), (0.440, 0.0745, 0.0794),
    (0.560, 0.0875, 0.0891), (0.700, 0.0940, 0.0940), (0.820, 0.0956, 0.0956),
    (0.920, 0.0907, 0.0891), (0.980, 0.0778, 0.0745), (1.020, 0.0000, 0.0000),
]

BRIDGE: list[tuple[float, float, float, float, float]] = [
    (0.010, 0.082, 0.270, 0.028, -0.056),
    (0.090, 0.082, 0.270, 0.054, -0.072),
    (0.220, 0.082, 0.270, 0.058, -0.076),
    (0.330, 0.082, 0.270, 0.040, -0.066),
    (0.380, 0.082, 0.270, 0.012, -0.038),
]
BRIDGE_FRAMES: tuple[float, ...] = (0.055, 0.170, 0.290)

# --------------------------------------------------------------------------
# Emplanture fixe (BRIEF-0036, inchangee) + carter de pivot (BRIEF-0098)
# --------------------------------------------------------------------------
GLOVE_MARGIN = 0.014
GLOVE_ARC_MARGIN = 0.018
GLOVE_NOSE_Y = -0.260
GLOVE_FLOOR_MAX = 0.048
GLOVE_SINK = 0.006
#: Fin de l'arc de logement : 90 deg, PAS PLUS — au-dela, l'arc revient vers
#: l'avant en y et le loft par stations n'est plus monotone. Le coin arriere de
#: racine (60 deg) arrive exactement a 90 deg a la fleche cible de 30 : la
#: reserve est nulle, c'est la mesure de recouvrement qui tranche.
GLOVE_ARC_END_DEG = 90.0
GLOVE_PSI_DEG: tuple[float, ...] = (
    8.0, 16.0, 24.0, 32.0, 39.0, 45.0, 50.0, 53.5, 56.0, 57.2, 58.0,
    58.6, 61.0, 64.0, 68.0, 73.0, 79.0, 85.0, GLOVE_ARC_END_DEG,
)
GLOVE_TAIL: tuple[tuple[float, float], ...] = (
    (0.560, 0.336), (0.585, 0.296), (0.610, 0.271),
)
GLOVE_THICK: list[tuple[float, float]] = [
    (-0.260, 0.0040), (-0.150, 0.0150), (0.000, 0.0250), (0.180, 0.0300),
    (0.340, 0.0290), (0.470, 0.0220), (0.560, 0.0130), (0.610, 0.0030),
]
GLOVE_V: tuple[float, ...] = (0.00, 0.18, 0.42, 0.72, 0.90, 1.00)
GLOVE_PROFILE: tuple[float, ...] = (0.30, 0.72, 1.00, 0.92, 0.62, 0.34)
GLOVE_MIN_CLEARANCE = 0.003

# --------------------------------------------------------------------------
# Derives et gouvernes (ADR-0014 ; BRIEF-0098 §6)
# --------------------------------------------------------------------------
FIN_CANT_DEG = 30.0
FIN_HEIGHT = 0.290
FIN_ROOT_Z = 0.040
#: (fraction d'envergure, y bord d'attaque, y bord de fuite, demi-epaisseur).
#: BRIEF-0098 : le bord de fuite du PIED recule de 1,012 a 0,975 — la nacelle
#: s'arrete en douille a 0,985 et le corps de tuyere (mobile) passe dessous.
FIN: tuple[tuple[float, float, float, float], ...] = (
    (0.00, 0.600, 0.975, 0.024),
    (0.28, 0.674, 0.992, 0.019),
    (0.58, 0.762, 0.988, 0.015),
    (0.82, 0.836, 0.976, 0.010),
    (1.00, 0.896, 0.966, 0.006),
)
#: Gouverne : envergure couverte (fractions), part de corde, jeu de charniere.
#: Elle commence a 0,26 d'envergure : en dessous, la derive est NOYEE dans la
#: nacelle (le pied est 6 cm sous la peau) et une gouverne y traverserait le
#: fuseau au premier degre.
RUDDER_S0, RUDDER_S1 = 0.26, 0.95
RUDDER_CHORD_FRAC = 0.34
RUDDER_GAP = 0.005
RUDDER_TARGET = 22.0

# --------------------------------------------------------------------------
# Aerofreins dorsaux (BRIEF-0098 §7)
# --------------------------------------------------------------------------
#: La baie est decoupee dans les CELLULES de la JOUE (segments 0..2 : la
#: tablette plate qui court entre la marche de flanc et le borde), entre les
#: aretes de deux bandes de rainure. Premiere version a cheval sur la marche
#: (segments 2..4) : une trappe en L dont l'inset s'effondrait — le balayage
#: BVH la trouvait 13 mm DANS le fuselage au repos. La trappe suit la surface
#: du pont (elle n'est pas plane : la joue tombe), et sa charniere est AVANT.
AIRBRAKE_Y0, AIRBRAKE_Y1 = 0.0850 + SEAM_HALF, 0.2650 - SEAM_HALF
AIRBRAKE_SEGS: tuple[int, ...] = (0, 1, 2)
AIRBRAKE_BAY_DEPTH = 0.022
AIRBRAKE_T = 0.008
AIRBRAKE_MARGIN = 0.0045   # jeu entre la trappe et le bord de la baie (interne, avant, arriere)
#: Marge EXTERNE plus large : le bord externe de la baie est l'arete meme du
#: borde, dont les normales de sommet penchent a 45 deg vers l'exterieur — la
#: paroi de baie y est en devers, et la trappe la frolait a 2 mm.
AIRBRAKE_MARGIN_OUT = 0.0090
AIRBRAKE_TARGET = 55.0

# --------------------------------------------------------------------------
# Arete dorsale, quille, chine (inchangees sauf note)
# --------------------------------------------------------------------------
#: BRIEF-0098 : l'arete commence a -0,085 (et non -0,145) : la verriere se
#: termine a -0,100 et sa charniere est a -0,092 — l'arete ne peut plus la
#: chevaucher, puisque la verriere bouge.
SPINE: list[tuple[float, float, float, float]] = [
    (-0.0850, 0.0120, 0.204, 0.150),
    (-0.0300, 0.0381, 0.226, 0.140),
    (0.0200, 0.0485, 0.244, 0.130),
    (0.1800, 0.0537, 0.260, 0.120),
    (0.3600, 0.0555, 0.258, 0.090),
    (0.5600, 0.0537, 0.250, 0.020),
    (0.7600, 0.0503, 0.236, -0.060),
    (0.9600, 0.0451, 0.216, -0.130),
    (1.0300, 0.0399, 0.196, -0.156),
]
SPINE_FRAMES: tuple[float, ...] = (0.060, 0.300, 0.520, 0.720, 0.900)
#: Rail magnetique dorsal (BRIEF-0098 §1) : le chenal creuse dans le dessus de
#: l'arete, et ses deux filets emissifs FINS au fond — le seul emissif dorsal
#: autorise hors tuyeres.
RAIL_Y0, RAIL_Y1 = 0.400, 0.990
RAIL_DEPTH = 0.016
RAIL_FILET_HW = 0.0035

KEEL: list[tuple[float, float, float, float]] = [
    (-1.0700, 0.0225, -0.026, -0.078), (-0.9800, 0.0312, -0.044, -0.116),
    (-0.8000, 0.0451, -0.076, -0.172), (-0.5600, 0.0624, -0.120, -0.238),
    (-0.3000, 0.0728, -0.150, -0.296), (-0.0200, 0.0797, -0.164, -0.342),
    (0.2200, 0.0815, -0.170, -0.352), (0.4200, 0.0763, -0.168, -0.330),
    (0.6000, 0.0676, -0.160, -0.280), (0.7600, 0.0572, -0.152, -0.228),
    (0.9000, 0.0451, -0.148, -0.190), (0.9800, 0.0104, -0.150, -0.160),
]
KEEL_FRAMES: tuple[float, ...] = (-0.420, -0.100, 0.180, 0.440, 0.660, 0.860)

#: Grappins d'appontage (BRIEF-0098 §8). Le bras est couche a plat CONTRE le
#: flanc de quille, sa charniere (le long de X) a l'AVANT de son logement, sa
#: pointe vers l'ARRIERE ; il pend vers le bas a 90 deg. Le logement est un
#: retrait de 4 mm dans le flanc de quille (`AA_Greeble`, TEX-0018), borde de
#: hachures rouges sans texte.
GRAPPLE_HINGE_Y = -0.790
GRAPPLE_TIP_Y = -0.600
GRAPPLE_R = 0.011
GRAPPLE_STANDOFF = 0.015    # axe du bras au-dela du flanc de quille
GRAPPLE_BAY_DEPTH = 0.004
GRAPPLE_TARGET = 90.0

CHINE_Y: tuple[float, ...] = (
    -1.0400, -0.9600, -0.8700, -0.7800, -0.6700, -0.5500, -0.4300, -0.3200,
    -0.2400, -0.1000, 0.0600, 0.2200, 0.3800, 0.5400, 0.7000, 0.8600, 0.9800,
)

BARREL_X = 0.042
BARREL_R = 0.015
BARREL_TIP = -1.0550
MUZZLE_Y = -1.0700
WING_MUZZLE_S = 0.34
TIP_MUZZLE_S = 0.94

#: Tuyere d'axe (inchangee).
TAIL_NOZZLE: list[tuple[float, float, str]] = [
    (1.010, 0.000, "AA_Hull"), (1.024, 0.062, "AA_Hull"), (1.060, 0.072, "AA_Greeble"),
    (1.100, 0.072, "AA_Greeble"), (1.108, 0.064, "AA_Trim"), (1.130, 0.066, "AA_Trim"),
    (1.150, 0.060, "AA_Greeble"), (1.185, 0.056, "AA_Greeble"),
]
TAIL_NOZZLE_Z = 0.014
TAIL_BORE_FLOOR = 1.120


# ==========================================================================
# Interpolation des tables et section transversale (BRIEF-0035, inchange)
# ==========================================================================


def lerp_table(table, y: float) -> float:
    """Interpolation lineaire d'une table (y, valeur), extremites clampees."""
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
    return lerp_table([(row[0], row[column]) for row in table], y)


def section_params(y: float) -> tuple[float, float, float, float]:
    w = lerp_table(PLANFORM, y)
    f = min(lerp_table(FUSELAGE, y), w * 0.94)
    return w, f, lerp_table(CROWN, y), lerp_table(BELLY, y)


def section_cut(y: float) -> float:
    return lerp_table(PLANFORM, y)


def _edge_h(crown: float) -> float:
    return min(EDGE_H, 0.55 * crown) if crown > 1e-6 else 0.0


def _cheek_shoulder(crown: float, eh: float) -> float:
    return max(CHEEK_FRAC * crown, eh)


def z_top(x: float, w: float, f: float, crown: float, belly: float) -> float:
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


CHEEK_T: tuple[float, ...] = (1.000, 0.760, 0.666, 0.180, 0.000)
FUS_U: tuple[float, ...] = (0.55, 1.00)
SPINE_U: tuple[float, ...] = (0.55, 0.00)


def section_x(w: float, f: float) -> list[float]:
    s = min(SPINE_HW, 0.60 * f)
    d = w - f
    half = [f + t * d for t in CHEEK_T]
    half += [f + (s - f) * u for u in FUS_U]
    half += [s * u for u in SPINE_U]
    return half + [-v for v in reversed(half[:-1])]


N_TOP = len(section_x(1.0, 0.4))          # 17
N_SEG = N_TOP - 1
RIM_STARBOARD = N_TOP - 1
RIM_PORT = 2 * N_TOP - 1
LONG_SEAM_SEGS: tuple[int, ...] = (1,)
FLANK_SEG = 3
SPINE_SEGS: tuple[int, ...] = (6, 7)
SEG_SPAN_ALL = tuple(range(1, N_SEG))
SEG_SPAN_FUS = tuple(range(4, N_SEG - 4))


def top_face(j: int) -> int:
    return j


def bot_face(j: int) -> int:
    return 2 * N_TOP - 2 - j


MIRROR = {j: (N_TOP - 2) - j for j in range(N_TOP - 1)}


def both(*js: int) -> set[int]:
    out: set[int] = set()
    for j in js:
        out.add(j)
        out.add(MIRROR[j])
    return out


ALL_LONG_SEAMS: set[int] = both(*LONG_SEAM_SEGS)


def run_width(y: float, first: int, last: int) -> float:
    _, f, _, _ = section_params(y)
    xs = section_x(section_cut(y), f)
    return abs(xs[first] - xs[last + 1])


def contiguous_runs(js: list[int]) -> list[list[int]]:
    runs: list[list[int]] = []
    for j in sorted(js):
        if runs and j == runs[-1][-1] + 1:
            runs[-1].append(j)
        else:
            runs.append([j])
    return runs


def _deck_z(x: float, y: float) -> float:
    return z_top(x, *section_params(y))


def _belly_z(x: float, y: float) -> float:
    return z_bot(x, *section_params(y))


def _chord_x(y: float, frac: float) -> float:
    _, f, _, _ = section_params(y)
    return f + frac * (section_cut(y) - f)


def _airbrake_x_range(y: float, side: float) -> tuple[float, float]:
    """Abscisses (interne, externe) de la baie d'aerofrein a la station `y`.

    Derivees de la SECTION (segments `AIRBRAKE_SEGS`), jamais ecrites : la baie
    et la trappe interrogent la meme fonction, elles ne peuvent pas diverger.
    """
    _, f, _, _ = section_params(y)
    xs = section_x(section_cut(y), f)
    lo = min(AIRBRAKE_SEGS)
    hi = max(AIRBRAKE_SEGS) + 1
    a, b = sorted((abs(xs[lo]), abs(xs[hi])))
    return side * a, side * b


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

    # ⚠️ NORMALES AVANT LE PLAQUAGE — la lecon de BRIEF-0036 (aile), mesuree ici
    # sur la coque elle-meme : le loft enroule ses faces vers l'INTERIEUR, et
    # `inset_panel` creuse le long de la normale de winding. Sans ce recalcul, le
    # puits de cockpit sortait en BLOC de 40 mm sur le pont et les baies
    # d'aerofrein en blocs de 22 mm — trouve par le balayage BVH (la trappe etait
    # « a l'interieur de la coque » de 16 mm au repos), pas par la relecture.
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    seam_bands = {b for b, wdt in enumerate(band_w) if wdt < SEAM_HALF * 2.5}
    used: set[tuple[int, int, str]] = set()

    def cells(y0, y1, js, surface="top", min_run=0.0, min_edge=0.0,
              min_band=0.0, skip_seams=False) -> list:
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

    def pick(y0, y1, js, surface="top") -> list:
        return cells(y0, y1, js, surface)

    def pick_rim(y0, y1) -> list:
        out = []
        for b, ym in enumerate(band_y):
            if y0 <= ym <= y1:
                for idx in (RIM_PORT, RIM_STARBOARD):
                    face = bands[b][idx]
                    if face is not None and face.is_valid:
                        out.append(face)
        return out

    def plate(faces: list, material: str) -> None:
        """Panneau a DEUX niveaux : marche en coque, fond en retrait."""
        if not faces:
            return
        ak.inset_panel(bm, faces, "AA_Hull", thickness=0.004, depth=-0.004)
        ak.inset_panel(bm, faces, material, thickness=0.005, depth=-0.006)

    # ---------------------------------------------------------------------
    # 1. Elements identitaires
    # ---------------------------------------------------------------------
    ak.set_material(pick(-0.860, 1.020, both(FLANK_SEG)), "AA_Panel")

    # --- puits de cockpit : bordure doree, cuve sombre PROFONDE (40 mm) ---
    # BRIEF-0098 §2 : il y a un cockpit dedans, et la verriere est une piece
    # mobile posee sur le plancher. Le puits est le seul creux du pont qu'on
    # regarde a travers une vitre : c'est lui qui recoit TEX-0018.
    well = pick(-0.680, -0.085, both(4, 5, 6, 7))
    sill = ak.inset_panel(bm, well, "AA_Greeble", thickness=0.007, depth=-0.002)
    ak.set_material(sill, "AA_Trim")                       # seuil dore, 7 mm
    ak.inset_panel(bm, well, "AA_Greeble", thickness=0.003, depth=-(WELL_DEPTH - 0.002))

    # --- baies d'aerofrein (BRIEF-0098 §7) : deux trappes de part et d'autre
    #     de l'arete, entre la verriere et les derives. La baie est creusee
    #     ici ; la trappe est une piece mobile qui la recouvre a fleur.
    for sx_js in (set(AIRBRAKE_SEGS), {MIRROR[j] for j in AIRBRAKE_SEGS}):
        bay = cells(AIRBRAKE_Y0, AIRBRAKE_Y1, sorted(sx_js))
        ak.inset_panel(bm, bay, "AA_Greeble", thickness=0.003,
                       depth=-AIRBRAKE_BAY_DEPTH)

    ak.inset_panel(bm, pick(-1.100, -0.700, both(*SPINE_SEGS)),
                   "AA_Greeble", thickness=0.004, depth=-0.014)
    ak.set_material(pick(-0.085, 1.020, both(*SPINE_SEGS)), "AA_Greeble")

    ak.set_material(pick_rim(-0.860, 1.020), "AA_Panel")
    ak.set_material(pick_rim(-1.100, -0.900), "AA_Trim")
    # (le pave rouge de borde de la coque en service est supprime : vu de
    #  profil il pesait a lui seul plus que tout le budget de marquage ; le
    #  rouge de cette coque, ce sont les hachures des logements de grappin.)

    ak.set_material(pick(-0.660, -0.480, both(0)), "AA_Trim")
    ak.set_material(pick(0.180, 0.320, both(0)), "AA_Trim")
    ak.set_material(pick(-1.060, -0.700, both(2)), "AA_Panel")

    # ---------------------------------------------------------------------
    # 2. Rainures LONGITUDINALES
    # ---------------------------------------------------------------------
    for seg in sorted(ALL_LONG_SEAMS):
        ak.inset_panel(
            bm,
            cells(-1.200, 1.020, (seg,), min_run=MIN_RUN_SEAM,
                  min_edge=MIN_EDGE_SEAM, min_band=MIN_BAND_SEAM),
            "AA_Hull", thickness=SEAM_T, depth=SEAM_D,
        )

    # ---------------------------------------------------------------------
    # 3. Panneaux bleu profond, a deux niveaux
    # ---------------------------------------------------------------------
    for y0, y1, js in (
        (-0.560, -0.080, both(2)),
        (-0.860, -0.700, both(4, 5)),
        (0.020, 0.480, both(2)),
        (0.020, 0.400, both(4, 5)),
        (0.540, 0.900, both(2)),
        (0.560, 1.020, both(4, 5)),
    ):
        plate(
            cells(y0, y1, js, min_run=MIN_RUN_PLATE, min_edge=MIN_EDGE_PLATE,
                  min_band=MIN_BAND_PLATE, skip_seams=True),
            "AA_Panel",
        )

    # ---------------------------------------------------------------------
    # 4. Rainures TRANSVERSALES
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
            "AA_Hull", thickness=SEAM_T, depth=SEAM_D,
        )

    # ---------------------------------------------------------------------
    # 5. Dessous : quille sombre et deux panneaux (le ventre vient APRES le
    #    dos, ADR-0044 §2 — mais il existe au bestiaire, donc il est panneaute).
    # ---------------------------------------------------------------------
    ak.set_material(pick(-1.050, 1.020, both(*SPINE_SEGS), "bot"), "AA_Greeble")
    for y0, y1, js in (
        (0.000, 0.600, both(2)),
        (-0.700, -0.100, both(2)),
        (0.020, 0.480, both(4, 5)),
    ):
        plate(
            cells(y0, y1, js, "bot", min_run=MIN_RUN_PLATE,
                  min_edge=MIN_EDGE_PLATE, min_band=MIN_BAND_PLATE,
                  skip_seams=True),
            "AA_Panel",
        )
    # rainures transversales ventrales (le ventre est vu au bestiaire)
    for b in sorted(seam_bands):
        ym = band_y[b]
        if -0.95 < ym < 1.0:
            ak.inset_panel(
                bm,
                cells(ym - 1e-4, ym + 1e-4, SEG_SPAN_ALL, "bot",
                      min_run=MIN_RUN_SEAM, min_edge=MIN_EDGE_SEAM),
                "AA_Hull", thickness=SEAM_T, depth=SEAM_D,
            )

    return ak.new_object("Specter9C_Hull", bm)


# ==========================================================================
# Briques de sous-ensembles
# ==========================================================================


def _rect_ring(bm, y: float, hw: float, z_lo: float, z_hi: float, taper: float = 1.0):
    return ak.add_ring(
        bm, [(hw, y, z_hi), (-hw, y, z_hi), (-hw * taper, y, z_lo), (hw * taper, y, z_lo)]
    )


def _beam_ring(bm, y, hw, z_hi, z_lo, chamfer, top_frac, center_x=0.0):
    """Section a FLANCS VERTICAUX et arete chanfreinee (arete dorsale, quille)."""
    if chamfer >= 0.0:
        za, zb = z_hi - chamfer, z_hi
        zc, zd = z_lo, z_lo
    else:
        za, zb = z_lo - chamfer, z_lo
        zc, zd = z_hi, z_hi
    return ak.add_ring(
        bm,
        [
            (center_x + hw, y, zc), (center_x + hw, y, za),
            (center_x + hw * top_frac, y, zb), (center_x - hw * top_frac, y, zb),
            (center_x - hw, y, za), (center_x - hw, y, zd),
        ],
    )


def _beam(bm, sections, chamfer, top_frac, materials, center_x=0.0):
    """Longeron a flancs verticaux. Retourne (bandes, toutes les faces)."""
    side, edge, face = materials
    rings = [
        _beam_ring(bm, y, hw, z_hi, z_lo, chamfer, top_frac, center_x)
        for y, hw, z_hi, z_lo in sections
    ]
    bands, all_faces = [], []
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], side)
        ak.set_material([band[1], band[3]], edge)
        ak.set_material([band[2]], face)
        bands.append(band)
        all_faces += [f for f in band if f is not None]
    for cap in (ak.cap_ring(bm, list(reversed(rings[0])), side),
                ak.cap_ring(bm, rings[-1], side)):
        if cap is not None:
            all_faces.append(cap)
    return bands, all_faces


def _strip(bm, samples, hw, material, center_x=0.0):
    """Bandeau lumineux : petit tube rectangulaire suivant (y, z_bas, z_haut)."""
    rings = [
        ak.add_ring(
            bm,
            [(center_x + hw, y, hi), (center_x - hw, y, hi),
             (center_x - hw, y, lo), (center_x + hw, y, lo)],
        )
        for y, lo, hi in samples
    ]
    for i in range(len(rings) - 1):
        ak.bridge_rings(bm, rings[i], rings[i + 1], material)
    ak.cap_ring(bm, list(reversed(rings[0])), material)
    ak.cap_ring(bm, rings[-1], material)


DOME_ARC = 11  # points d'arc d'une section de dome (9 sur la coque en service)


def _dome(bm, sections, center_x, base_z, material: str) -> list[list]:
    """Demi-coque bombee, posee sur une assise plane (verriere)."""
    rings: list = []
    tips: list = []
    for y, hw, h in sections:
        z0 = base_z(y)
        if hw <= 1e-6:
            tips.append(bm.verts.new((center_x, y, z0)))
            rings.append(None)
            continue
        pts = [
            (center_x + hw * math.cos(math.pi * k / (DOME_ARC - 1)), y,
             z0 + h * math.sin(math.pi * k / (DOME_ARC - 1)))
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


def _circle(bm, y, radius, cx, cz, segments=NACELLE_SEGMENTS, y_of_angle=None):
    """Anneau circulaire dans le plan Y = cste (ou oblique si `y_of_angle`).

    Reproduit la formule de `ak.add_lathe(axis="Y")` pour que `ak.cleanup()`
    soude les anneaux batis a la main sur ceux des solides de revolution.
    """
    pts = []
    for s in range(segments):
        a = 2.0 * math.pi * s / segments
        yy = y if y_of_angle is None else y_of_angle(a)
        pts.append((cx + radius * math.cos(a), yy, cz + radius * math.sin(a)))
    return ak.add_ring(bm, pts)


def _lathe_rings(bm, contour, cx, cz, segments=NACELLE_SEGMENTS):
    """Solide de revolution bati a la main : rend (anneaux, bandes de faces).

    Comme `ak.add_lathe`, mais on garde la main sur les anneaux : la nacelle
    doit souder son entree d'air oblique en avant et sa douille en arriere.
    """
    rings = []
    for along, radius, _ in contour:
        if radius <= 1e-6:
            rings.append(bm.verts.new((cx, along, cz)))
        else:
            rings.append(_circle(bm, along, radius, cx, cz, segments))
    bands = []
    for i in range(len(contour) - 1):
        mat = contour[i][2]
        a, b = rings[i], rings[i + 1]
        if isinstance(a, bmesh.types.BMVert) and isinstance(b, list):
            bands.append(ak.fan_to_point(bm, b, a, mat))
        elif isinstance(b, bmesh.types.BMVert) and isinstance(a, list):
            bands.append(ak.fan_to_point(bm, a, b, mat))
        elif isinstance(a, list) and isinstance(b, list):
            bands.append([f for f in ak.bridge_rings(bm, a, b, mat) if f is not None])
        else:
            bands.append([])
    return rings, bands


def _polar_slab(bm, cx, cz, y_stations, angle_lo, angle_hi, r_inner_fn, thickness,
                material, arc_points=9):
    """Plaque COURBE autour de l'axe (cx, cz) : rampe d'entree d'air, raidisseur
    de petale. `r_inner_fn(y)` rend le rayon de la face interne a la station y."""
    rings = []
    for y in y_stations:
        r0 = r_inner_fn(y)
        r1 = r0 + thickness
        outer = [
            (cx + r1 * math.cos(a), y, cz + r1 * math.sin(a))
            for a in (angle_lo + (angle_hi - angle_lo) * k / (arc_points - 1)
                      for k in range(arc_points))
        ]
        inner = [
            (cx + r0 * math.cos(a), y, cz + r0 * math.sin(a))
            for a in (angle_lo + (angle_hi - angle_lo) * k / (arc_points - 1)
                      for k in reversed(range(arc_points)))
        ]
        rings.append(ak.add_ring(bm, outer + inner))
    faces = []
    for i in range(len(rings) - 1):
        faces += [f for f in ak.bridge_rings(bm, rings[i], rings[i + 1], material) if f]
    for cap in (ak.cap_ring(bm, list(reversed(rings[0])), material),
                ak.cap_ring(bm, rings[-1], material)):
        if cap is not None:
            faces.append(cap)
    return faces


def _nozzle_bore(bm, cx: float, cz: float) -> None:
    """Chambre emissive, en avant du col, a axe RELEVE (voir NOZZLE_BORE)."""
    rings = [_circle(bm, y, r, cx, cz + dz) for y, r, dz in NOZZLE_BORE]
    for i in range(len(rings) - 1):
        ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Emissive_Engine")
    floor = bm.verts.new((cx, NOZZLE_FLOOR_Y, cz + NOZZLE_BORE[-1][2]))
    ak.fan_to_point(bm, rings[-1], floor, "AA_Emissive_Engine")


# --------------------------------------------------------------------------
# Nacelle : rayons, entree d'air, douille
# --------------------------------------------------------------------------

NACELLE_OUTER: list[tuple[float, float]] = [
    (y, r) for y, r, _ in NACELLE_PROFILE[: 1 + max(
        i for i, p in enumerate(NACELLE_PROFILE) if p[0] == NACELLE_SOCKET_Y1 and p[1] > 0.1
    )]
]


def _intake_lip_y(angle: float) -> float:
    """y de la levre d'entree d'air a l'angle `angle` (0 = +x, pi/2 = sommet)."""
    return INTAKE_LIP_Y - INTAKE_RAKE * math.sin(angle)


def _nacelle_radius(y: float, angle: float = math.pi * 0.5) -> float:
    """Rayon NU du fuseau a la station `y` (a l'angle `angle` en avant de -0,36,
    ou la levre est oblique)."""
    y_lip = _intake_lip_y(angle)
    if y <= y_lip:
        return INTAKE_LIP_R
    if y < NACELLE_OUTER[0][0]:
        t = (y - y_lip) / (NACELLE_OUTER[0][0] - y_lip)
        return INTAKE_LIP_R + (NACELLE_OUTER[0][1] - INTAKE_LIP_R) * t
    return lerp_table(NACELLE_OUTER, y)


def nacelle_half_width(y: float) -> float:
    """Demi-largeur de la nacelle + tuyere vue de dessus, tout compris, a `y`."""
    if y < NACELLE_Y_FRONT or y > PETAL_SECTIONS[-1][0]:
        return 0.0
    if y > NOZZLE_HINGE_Y:
        return lerp_table([(s[0], s[2]) for s in PETAL_SECTIONS], y)
    if y > NACELLE_SOCKET_Y1:
        return lerp_table([(p[0], p[1]) for p in NOZZLE_BODY if p[1] > 0.0], y)
    return _nacelle_radius(y)


def _nacelle(bm, sx: float) -> None:
    """Fuseau : entree d'air oblique + gorge + cone central, corps de revolution
    aux trois anneaux en retrait, DOUILLE creuse en arriere (le col de tuyere y
    tourne). Un seul manifold ferme."""
    cx, cz = sx * NACELLE_X, NACELLE_Z
    rings, _ = _lathe_rings(bm, NACELLE_PROFILE, cx, cz)
    lip_outer = _circle(bm, 0.0, INTAKE_LIP_R, cx, cz, y_of_angle=_intake_lip_y)
    lip_inner = _circle(bm, 0.0, INTAKE_THROAT_R, cx, cz, y_of_angle=_intake_lip_y)
    throat = _circle(bm, INTAKE_THROAT_Y, INTAKE_THROAT_R - 0.003, cx, cz)
    apex = bm.verts.new((cx, INTAKE_CONE_APEX_Y, cz))
    ak.bridge_rings(bm, lip_outer, rings[0], "AA_Hull")
    ak.bridge_rings(bm, lip_inner, lip_outer, "AA_Trim")      # la levre doree
    ak.bridge_rings(bm, throat, lip_inner, "AA_Greeble")      # la gorge
    ak.fan_to_point(bm, throat, apex, "AA_Greeble")           # le cone central

    # Bandeau cyan sur le flanc superieur du fuseau (visible du dessus), FIN.
    _strip(
        bm,
        [(0.620, 0.046, 0.054), (0.780, 0.052, 0.060), (0.920, 0.046, 0.054)],
        0.005, "AA_Emissive_Engine", center_x=sx * (NACELLE_X + 0.040),
    )


# --------------------------------------------------------------------------
# Aile en plan (polaire), emplanture fixe (BRIEF-0036, inchange)
# --------------------------------------------------------------------------


def _wing_polar():
    reach = WING_TIP_X - WING_PIVOT_X
    le = (reach / math.cos(math.radians(WING_LE_TIP_ANGLE)), WING_LE_TIP_ANGLE)
    te = (reach / math.cos(math.radians(WING_TE_TIP_ANGLE)), WING_TE_TIP_ANGLE)
    return le, te


def _polar(r: float, phi_deg: float) -> tuple[float, float]:
    a = math.radians(phi_deg)
    return (WING_PIVOT_X + r * math.cos(a), WING_PIVOT_Y + r * math.sin(a))


def _wing_edges(s: float):
    le_tip, te_tip = _wing_polar()
    le = _polar(WING_LE_ROOT[0] + (le_tip[0] - WING_LE_ROOT[0]) * s,
                WING_LE_ROOT[1] + (le_tip[1] - WING_LE_ROOT[1]) * s)
    te = _polar(WING_TE_ROOT[0] + (te_tip[0] - WING_TE_ROOT[0]) * s,
                WING_TE_ROOT[1] + (te_tip[1] - WING_TE_ROOT[1]) * s)
    return le, te


def _glove_floor(y: float) -> float:
    return min(GLOVE_FLOOR_MAX, NACELLE_Z + _nacelle_radius(y) - GLOVE_SINK)


def _glove_x_in(y: float) -> float:
    r = _nacelle_radius(y)
    dz = _glove_floor(y) - NACELLE_Z
    return NACELLE_X - math.sqrt(max(r * r - dz * dz, 0.0)) + 0.006


def _root_chord_rel():
    a = (WING_LE_ROOT[0] * math.cos(math.radians(WING_LE_ROOT[1])),
         WING_LE_ROOT[0] * math.sin(math.radians(WING_LE_ROOT[1])))
    b = (WING_TE_ROOT[0] * math.cos(math.radians(WING_TE_ROOT[1])),
         WING_TE_ROOT[0] * math.sin(math.radians(WING_TE_ROOT[1])))
    return a, b


def _glove_rho(phi_deg: float) -> float:
    a, b = _root_chord_rel()
    ab = (b[0] - a[0], b[1] - a[1])
    length = math.hypot(ab[0], ab[1])
    nx, ny = ab[1] / length, -ab[0] / length
    p0 = a[0] * nx + a[1] * ny
    arc = WING_TE_ROOT[0] + GLOVE_ARC_MARGIN
    cos_t = math.cos(math.radians(phi_deg) - math.atan2(ny, nx))
    if cos_t <= 1e-4:
        return arc
    return min((p0 + GLOVE_MARGIN) / cos_t, arc)


_GLOVE_STATIONS: list[tuple[float, float]] | None = None


def _glove_stations() -> list[tuple[float, float]]:
    global _GLOVE_STATIONS
    if _GLOVE_STATIONS is not None:
        return _GLOVE_STATIONS
    out: list[tuple[float, float]] = []
    apex = _polar(_glove_rho(GLOVE_PSI_DEG[0]), GLOVE_PSI_DEG[0])
    nose = (_glove_x_in(GLOVE_NOSE_Y), GLOVE_NOSE_Y)
    for t in (0.0, 0.16, 0.34, 0.54, 0.76):
        out.append((nose[1] + (apex[1] - nose[1]) * t, nose[0] + (apex[0] - nose[0]) * t))
    for phi in GLOVE_PSI_DEG:
        x, y = _polar(_glove_rho(phi), phi)
        out.append((y, x))
    for y, x in GLOVE_TAIL:
        out.append((y, x))
    for i in range(len(out) - 1):
        if out[i + 1][0] <= out[i][0] + 1e-6:
            raise ak.ContractError(
                f"emplanture : stations non monotones en y ({out[i][0]:.4f} -> {out[i + 1][0]:.4f})"
            )
    _GLOVE_STATIONS = out
    return out


def _glove_x_out(y: float) -> float:
    stations = _glove_stations()
    if y < stations[0][0] or y > stations[-1][0]:
        return -1.0
    return lerp_table(stations, y)


def _glove_top(x: float, y: float) -> float:
    x_in, x_out = _glove_x_in(y), _glove_x_out(y)
    if x_out < 0.0 or x_out <= x_in:
        return _glove_floor(y)
    v = min(max((abs(x) - x_in) / (x_out - x_in), 0.0), 1.0)
    prof = lerp_table(list(zip(GLOVE_V, GLOVE_PROFILE)), v)
    return _glove_floor(y) + lerp_table(GLOVE_THICK, y) * prof


def _in_glove(x: float, y: float) -> bool:
    x_out = _glove_x_out(y)
    return x_out > 0.0 and _glove_x_in(y) <= abs(x) <= x_out


def _wing_thickness(s: float, t: float) -> float:
    """Demi-epaisseur de la lame : PROFIL DE VOILURE (bord d'attaque rond au
    maitre-couple `WING_PEAK_T`, bord de fuite fin) — BRIEF-0098 §3."""
    th = WING_THICK_ROOT + (WING_THICK_TIP - WING_THICK_ROOT) * s
    return ak.airfoil_half_thickness(t, th, peak=WING_PEAK_T)


def _wing_plane_z(s: float) -> float:
    return WING_PIVOT_Z - WING_ANHEDRAL * s * s


def _insettable(faces: list, thickness: float) -> list:
    out = []
    for face in faces:
        if face is None or not face.is_valid:
            continue
        edges = [e.calc_length() for e in face.edges]
        if edges and min(edges) > thickness * 2.4:
            out.append(face)
    return out


def _flap_root_s() -> float:
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) * 0.5
        if _wing_edges(mid)[1][1] < FLAP_HINGE_Y + FLAP_MIN_CHORD:
            lo = mid
        else:
            hi = mid
    return hi


def _wing_rib_stations() -> list[float]:
    s0 = _flap_root_s()
    out = set(WING_RIBS)
    out.add(round(max(s0 - 0.006, 0.0), 6))
    out.add(round(s0, 6))
    return sorted(out)


# --------------------------------------------------------------------------
# Derives et gouvernes (BRIEF-0098 §6)
# --------------------------------------------------------------------------


def _fin_frame(sx: float):
    """Repere de la derive `sx` : P(s, y, n) -> point 3D, et (axe d'envergure,
    normale au plan, origine). L'axe est incline de FIN_CANT_DEG vers l'exterieur ;
    la normale +n pointe vers l'EXTERIEUR ET LE BAS (la face -n est celle que la
    camera de jeu voit)."""
    cant = math.radians(FIN_CANT_DEG)
    axis = Vector((sx * math.sin(cant), 0.0, math.cos(cant)))
    normal = Vector((sx * math.cos(cant), 0.0, -math.sin(cant)))
    origin = Vector((sx * NACELLE_X, 0.0, FIN_ROOT_Z))

    def point(s: float, y: float, n: float) -> tuple[float, float, float]:
        p = origin + axis * (s * FIN_HEIGHT) + Vector((0.0, y, 0.0)) + normal * n
        return (p.x, p.y, p.z)

    return point, axis, normal, origin


def _fin_geom(s: float) -> tuple[float, float, float]:
    return lerp_row(FIN, s, 1), lerp_row(FIN, s, 2), lerp_row(FIN, s, 3)


def _fin_hinge_y(s: float) -> float:
    """y de la ligne de charniere de gouverne a l'envergure `s` : une DROITE
    (les deux bouts a `RUDDER_CHORD_FRAC` de la corde locale, interpolation
    lineaire entre les deux) — une charniere n'est un axe que si elle est droite."""
    def at(ss: float) -> float:
        y_le, y_te, _ = _fin_geom(ss)
        return y_te - RUDDER_CHORD_FRAC * (y_te - y_le)
    y0, y1 = at(RUDDER_S0), at(1.0)
    return y0 + (y1 - y0) * (s - RUDDER_S0) / (1.0 - RUDDER_S0)


FIN_ARC_K = 3   # points interieurs de l'arc concave du logement de gouverne (5 : cordes de 3,6 mm, sous le biseau)
RUDDER_NOSE_M = 7


def _fin_root_section(s: float) -> list[tuple[float, float]]:
    y_le, y_te, th = _fin_geom(s)
    c = y_te - y_le
    return [(y_le, 0.0), (y_le + 0.12 * c, th), (y_te - 0.10 * c, th),
            (y_te, 0.0), (y_te - 0.10 * c, -th), (y_le + 0.12 * c, -th)]


def _fin_slotted_section(s: float) -> list[tuple[float, float]]:
    """Section de derive au droit de la gouverne : le bord de fuite est un ARC
    CONCAVE concentrique a la charniere (rayon = demi-epaisseur + jeu), de sorte
    que le nez rond de la gouverne y tourne sans jamais s'en approcher."""
    y_le, y_te, th = _fin_geom(s)
    c = y_te - y_le
    y_h = _fin_hinge_y(s)
    radius = th + RUDDER_GAP
    phi = math.asin(min(th / radius, 1.0))
    y_cut = y_h - radius * math.cos(phi)
    pts = [(y_le, 0.0), (y_le + 0.12 * c, th), (y_cut, th)]
    for k in range(1, FIN_ARC_K + 1):
        a = phi - 2.0 * phi * k / (FIN_ARC_K + 1)
        pts.append((y_h - radius * math.cos(a), radius * math.sin(a)))
    pts += [(y_cut, -th), (y_le + 0.12 * c, -th)]
    return pts


def _rudder_section(s: float) -> list[tuple[float, float]]:
    """Section de gouverne : nez en DEMI-CERCLE centre sur la charniere, corps
    effile jusqu'au bord de fuite."""
    y_le, y_te, th = _fin_geom(s)
    y_h = _fin_hinge_y(s)
    c_r = y_te - y_h
    pts = []
    for k in range(RUDDER_NOSE_M):
        a = math.pi * 0.5 - math.pi * k / (RUDDER_NOSE_M - 1)
        pts.append((y_h - th * math.cos(a), th * math.sin(a)))
    pts += [(y_te - 0.15 * c_r, -th * 0.55), (y_te, 0.0), (y_te - 0.15 * c_r, th * 0.55)]
    return pts


def _fin(bm, sx: float) -> None:
    """Derive inclinee (ADR-0014) en DEUX solides : pied a corde pleine (noye dans
    la nacelle jusqu'a s = 0,26) et partie haute au bord de fuite echancre pour
    la gouverne. Feu de derive en bout, en cylindre."""
    point, axis, _n, _o = _fin_frame(sx)

    def fan_cap(ring, material, flip):
        # ⚠️ Un n-gone CONCAVE (la section echancree) sort de
        # `bmesh.ops.triangulate` avec des sommets dupliques : validate() le
        # jette et l'exporteur previent « mesh not valid ». Un eventail vers le
        # centroide est valide par construction — la section est etoilee depuis
        # sa mi-corde.
        centroid = Vector((0.0, 0.0, 0.0))
        for v in ring:
            centroid += v.co
        apex = bm.verts.new(centroid / len(ring))
        ak.fan_to_point(bm, list(reversed(ring)) if flip else ring, apex, material)

    def loft(stations, section_fn, materials_fn):
        rings = [ak.add_ring(bm, [point(s, y, n) for y, n in section_fn(s)]) for s in stations]
        bands = []
        for i in range(len(rings) - 1):
            band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
            materials_fn(i, band)
            bands.append(band)
        fan_cap(rings[0], "AA_Greeble", True)
        fan_cap(rings[-1], "AA_Trim", False)
        return bands

    def root_mats(_i, band):
        ak.set_material([band[0], band[2], band[3], band[5]], "AA_Greeble")

    loft((0.0, 0.14, RUDDER_S0), _fin_root_section, root_mats)

    # La partie haute NAIT 4 mm SOUS le sommet du pied : deux solides dont les
    # culots partageraient un plan (et trois sommets, apres soudure) produisent
    # des triangles jumeaux a la triangulation — validate() les jette et
    # l'exporteur previent « mesh not valid ». En chevauchement de volume, rien
    # ne se partage.
    upper = (RUDDER_S0 - 0.004, 0.40, 0.58, 0.72, 0.82, 0.92, 1.00)
    n_pts = len(_fin_slotted_section(0.5))

    def upper_mats(i, band):
        # 0 = bord d'attaque haut, 1 = flanc EXTERNE (+n), 2 = plat avant l'arc,
        # 3..3+K = arc concave, puis plat, flanc INTERNE (-n), bord d'attaque bas.
        ak.set_material([band[0], band[n_pts - 1]], "AA_Greeble")
        ak.set_material(band[2: 3 + FIN_ARC_K + 1], "AA_Greeble")
        if 1 <= i <= 3:
            ak.set_material([band[n_pts - 2]], "AA_Panel")   # face vue d'en haut
        if i >= len(upper) - 2:
            ak.set_material([band[1], band[n_pts - 2]], "AA_Panel")  # coiffe bleue

    loft(upper, _fin_slotted_section, upper_mats)

    y_le, _, _ = _fin_geom(0.97)
    ak.add_tube(bm, point(0.93, y_le + 0.012, 0.0), point(1.02, y_le + 0.012, 0.0),
                0.006, 8, "AA_Emissive_Engine")


# --------------------------------------------------------------------------
# Caisson de liaison, emplanture, carter de pivot
# --------------------------------------------------------------------------


def _bridge(bm, sx: float) -> None:
    rings = []
    for y, x_in, x_out, z_hi, z_lo in BRIDGE:
        rings.append(ak.add_ring(bm, [(sx * x_out, y, z_hi), (sx * x_in, y, z_hi),
                                      (sx * x_in, y, z_lo), (sx * x_out, y, z_lo)]))
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Greeble")
        ak.set_material([band[0]], "AA_Panel")
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Greeble")
    for y in BRIDGE_FRAMES:
        x_in, x_out = lerp_row(BRIDGE, y, 1), lerp_row(BRIDGE, y, 2)
        z_hi, z_lo = lerp_row(BRIDGE, y, 3), lerp_row(BRIDGE, y, 4)
        ak.add_box(bm, (sx * (x_in + x_out) * 0.5, y, (z_hi + z_lo) * 0.5),
                   (x_out - x_in, 0.018, (z_hi - z_lo) * 1.10), "AA_Greeble")
    _strip(bm, [(0.070, 0.046, 0.056), (0.220, 0.050, 0.060), (0.330, 0.034, 0.044)],
           0.006, "AA_Emissive_Engine", center_x=sx * 0.200)


def _glove(bm, sx: float) -> None:
    """Emplanture fixe (BRIEF-0036) + CARTER DE PIVOT demontable (BRIEF-0098 §3) :
    platine doree et quatre fixations, sur le dos, au droit du pivot enfoui."""
    stations = _glove_stations()
    rings: list = []
    for y, x_out in stations:
        x_in = min(_glove_x_in(y), x_out - 0.002)
        floor = _glove_floor(y)
        th = lerp_table(GLOVE_THICK, y)
        xs = [x_in + (x_out - x_in) * v for v in GLOVE_V]
        top = [(sx * x, y, floor + th * p) for x, p in zip(xs, GLOVE_PROFILE)]
        bot = [(sx * x, y, floor) for x in xs]
        rings.append(ak.add_ring(bm, top + list(reversed(bot))))
    n = len(GLOVE_V)
    bands: list[list] = []
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        bands.append(band)
        y_mid = (stations[i][0] + stations[i + 1][0]) * 0.5
        ak.set_material([band[n - 1]], "AA_Greeble")   # levre sombre (l'or vu depassait)
        ak.set_material([band[2 * n - 1]], "AA_Greeble")
    nose_y = stations[0][0]
    apex = bm.verts.new((sx * _glove_x_in(nose_y), nose_y - 0.026,
                         _glove_floor(nose_y) + lerp_table(GLOVE_THICK, nose_y) * 0.5))
    nose_faces = ak.fan_to_point(bm, list(reversed(rings[0])), apex, "AA_Hull")
    tail_face = ak.cap_ring(bm, rings[-1], "AA_Greeble")
    glove_faces = [f for band in bands for f in band if f is not None]
    glove_faces += [f for f in nose_faces if f is not None]
    if tail_face is not None:
        glove_faces.append(tail_face)
    bmesh.ops.recalc_face_normals(bm, faces=glove_faces)

    seam = [b[1] for b in bands if b[1] is not None and b[1].is_valid]
    ak.inset_panel(bm, _insettable(seam, SEAM_T), "AA_Hull", thickness=SEAM_T, depth=SEAM_D)
    plate_faces = []
    for i, band in enumerate(bands):
        y_mid = (stations[i][0] + stations[i + 1][0]) * 0.5
        if -0.020 <= y_mid <= 0.420:
            plate_faces += [band[j] for j in (2, 3) if band[j] is not None]
    plate_faces = _insettable(plate_faces, 0.006)
    if plate_faces:
        ak.inset_panel(bm, plate_faces, "AA_Hull", thickness=0.005, depth=-0.004)
        ak.inset_panel(bm, plate_faces, "AA_Panel", thickness=0.006, depth=-0.006)

    # --- carter de pivot demontable : embase sombre, platine doree, 4 fixations
    y_hub = WING_PIVOT_Y + 0.058
    x_hub = WING_PIVOT_X - 0.034
    z_hub = _glove_top(x_hub, y_hub)
    ak.add_box(bm, (sx * x_hub, y_hub, z_hub - 0.002), (0.092, 0.156, 0.022), "AA_Greeble")
    ak.add_box(bm, (sx * x_hub, y_hub, z_hub + 0.008), (0.056, 0.106, 0.014), "AA_Trim")
    for dx, dy in ((-0.020, -0.044), (0.020, -0.044), (-0.020, 0.044), (0.020, 0.044)):
        x, y = sx * (x_hub + dx), y_hub + dy
        ak.add_tube(bm, (x, y, z_hub + 0.012), (x, y, z_hub + 0.019), 0.0045, 8, "AA_Greeble")


# --------------------------------------------------------------------------
# Cockpit (dans le maillage principal, sous la verriere mobile)
# --------------------------------------------------------------------------


def _well_floor_z(y: float) -> float:
    """Cote du plancher du puits de cockpit sur l'axe (le puits est un inset de
    `WELL_DEPTH` sous le pont)."""
    return lerp_table(CROWN, y) - WELL_DEPTH + 0.002


def _cockpit(bm) -> None:
    """Le pilote est en DECUBITUS VENTRAL (fiche du bestiaire) : un BERCEAU
    incline, un arceau de visee devant, deux consoles laterales — AA_Greeble,
    avec trois fentes emissives de 1 cm. Tout tient sous la bulle (120 mm) et
    dans la largeur du puits (< 0,048)."""
    # berceau : plaque inclinee, plus haute a l'avant (la tete regarde devant)
    y0, y1 = -0.560, -0.230
    hw = 0.024
    rings = []
    for y, lift in ((y0, 0.026), (y0 + 0.06, 0.028), (y1 - 0.05, 0.016), (y1, 0.012)):
        z = _well_floor_z(y) + lift
        rings.append(ak.add_ring(bm, [(hw, y, z), (-hw, y, z),
                                      (-hw * 0.8, y, z - 0.010), (hw * 0.8, y, z - 0.010)]))
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Greeble")
        ak.set_material([band[0]], "AA_Panel")
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Greeble")
    # pieds du berceau
    for y in (y0 + 0.04, y1 - 0.03):
        ak.add_box(bm, (0.0, y, _well_floor_z(y) + 0.006), (0.030, 0.014, 0.014), "AA_Greeble")

    # arceau de visee : deux montants et un linteau, devant la tete — 11 mm en
    # arriere du montant avant de verriere (a -0,585 il le traversait)
    ya = -0.552
    za = _well_floor_z(ya)
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * 0.026, ya, za + 0.026), (0.007, 0.008, 0.052), "AA_Greeble")
    ak.add_box(bm, (0.0, ya, za + 0.052), (0.059, 0.008, 0.008), "AA_Greeble")
    ak.add_box(bm, (0.0, ya + 0.0045, za + 0.052), (0.028, 0.002, 0.010),
               "AA_Emissive_Engine")   # fente de visee, 1 cm de haut

    # consoles laterales, avec une fente emissive chacune
    for sx in (ak.PORT, ak.STARBOARD):
        yc = -0.400
        zc = _well_floor_z(yc)
        ak.add_box(bm, (sx * 0.034, yc, zc + 0.012), (0.012, 0.180, 0.024), "AA_Greeble")
        ak.add_box(bm, (sx * 0.034, yc - 0.030, zc + 0.0255), (0.010, 0.040, 0.002),
                   "AA_Emissive_Engine")
        ak.add_box(bm, (sx * 0.034, yc + 0.045, zc + 0.0255), (0.010, 0.030, 0.002),
                   "AA_Emissive_Engine")
    # dosseret arriere (fixe), en arriere de la charniere de verriere
    yd = CANOPY_HINGE_Y + 0.010
    zd = lerp_table(CROWN, yd) - CANOPY_SINK
    ak.add_box(bm, (0.0, yd, zd + 0.010), (0.080, 0.014, 0.020), "AA_Greeble")
    # paliers de charniere de verriere, de part et d'autre
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_tube(bm, (sx * 0.020, CANOPY_HINGE_Y, zd + 0.006),
                    (sx * 0.032, CANOPY_HINGE_Y, zd + 0.006), 0.005, 8, "AA_Trim")


# --------------------------------------------------------------------------
# Baies d'aerofrein : verins et machinerie (fixes ; la trappe est mobile)
# --------------------------------------------------------------------------


def _airbrake_bay_machinery(bm, sx: float) -> None:
    """Un verin couche en diagonale au fond de la baie, deux nervures. Le fond
    de baie est `AA_Greeble` (TEX-0018) ; le verin ne monte jamais au-dessus du
    dessous de la trappe fermee (jeu 5 mm, mesure au build)."""
    x_in, x_out = _airbrake_x_range((AIRBRAKE_Y0 + AIRBRAKE_Y1) * 0.5, sx)
    x_mid = (x_in + x_out) * 0.5

    def floor(y: float) -> float:
        return _deck_z(x_mid, y) - AIRBRAKE_BAY_DEPTH

    ya, yt = AIRBRAKE_Y1 - 0.022, AIRBRAKE_Y0 + 0.040
    ak.add_actuator(bm, (x_mid, ya, floor(ya) + 0.004), (x_mid, yt, floor(yt) + 0.006),
                    0.0040, 0.0022, barrel_fraction=0.58, segments=8)
    for y in (AIRBRAKE_Y0 + 0.070, AIRBRAKE_Y1 - 0.060):
        ak.add_box(bm, (x_mid, y, floor(y) + 0.003), (abs(x_out - x_in) * 0.7, 0.006, 0.006),
                   "AA_Greeble")


# --------------------------------------------------------------------------
# Quille, logements de grappin
# --------------------------------------------------------------------------


def _keel_flank_x(y: float) -> float:
    return lerp_row(KEEL, y, 1)


def _grapple_axis_z() -> float:
    """Hauteur de l'axe du bras : au milieu du flanc de quille a la charniere."""
    y = GRAPPLE_HINGE_Y
    return (lerp_row(KEEL, y, 2) + lerp_row(KEEL, y, 3)) * 0.5 - 0.006


def _keel(bm) -> None:
    bands, faces = _beam(bm, KEEL, chamfer=-0.016, top_frac=0.72,
                         materials=("AA_Hull", "AA_Greeble", "AA_Greeble"))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    for b, (y, _, _, _) in enumerate(KEEL[:-1]):
        if -0.30 <= y <= 0.42:
            ak.set_material([bands[b][0], bands[b][4]], "AA_Panel")
    # logements de grappin : un retrait de 4 mm dans le flanc, entre les
    # stations -0,80 et -0,56 (bande 2), des deux cotes
    bay = [bands[2][0], bands[2][4]]
    rim = ak.inset_panel(bm, bay, "AA_Greeble", thickness=0.004, depth=-GRAPPLE_BAY_DEPTH)
    ak.set_material(rim, "AA_Greeble")
    for y in KEEL_FRAMES:
        hw = lerp_row(KEEL, y, 1)
        z_hi, z_lo = lerp_row(KEEL, y, 2), lerp_row(KEEL, y, 3)
        ak.add_box(bm, (0.0, y, (z_hi + z_lo) * 0.5 + 0.010),
                   (hw * 2.14, 0.020, (z_hi - z_lo) * 0.92), "AA_Greeble")
    # hachures rouges SANS texte au bord inferieur de chaque logement
    for sx in (ak.PORT, ak.STARBOARD):
        for k in range(5):
            y = GRAPPLE_HINGE_Y + 0.030 + k * 0.030
            x = sx * (_keel_flank_x(y) + 0.001)
            z = lerp_row(KEEL, y, 3) + 0.016
            ak.add_box(bm, (x, y, z), (0.003, 0.010, 0.014), "AA_Marking_Red")


# ==========================================================================
# Assemblage des details fixes
# ==========================================================================


def build_details() -> object:
    bm = bmesh.new()
    rng_seed = SEED

    _cockpit(bm)

    # --- arete dorsale + rail magnetique --------------------------------
    spine_bands, spine_faces = _beam(bm, SPINE, chamfer=0.014, top_frac=0.70,
                                     materials=("AA_Panel", "AA_Hull", "AA_Hull"))
    bmesh.ops.recalc_face_normals(bm, faces=spine_faces)
    # bloc technique creuse (avant du rail), puis LE RAIL : chenal profond avec
    # deux filets emissifs fins au fond — le seul emissif dorsal hors tuyeres.
    ak.inset_panel(bm, [band[2] for band in spine_bands[1:4]], "AA_Greeble",
                   thickness=0.010, depth=-0.014)
    rail_top = [band[2] for band in spine_bands[4:]]
    ak.inset_panel(bm, rail_top, "AA_Greeble", thickness=0.008, depth=-RAIL_DEPTH)
    for sx in (ak.PORT, ak.STARBOARD):
        samples = []
        for y in (RAIL_Y0, 0.560, 0.760, 0.960, RAIL_Y1):
            z_hi = lerp_row(SPINE, y, 2) - RAIL_DEPTH
            samples.append((y, z_hi + 0.001, z_hi + 0.005))
        _strip(bm, samples, RAIL_FILET_HW, "AA_Emissive_Engine", center_x=sx * 0.013)
    for y in SPINE_FRAMES:
        hw, z_hi = lerp_row(SPINE, y, 1), lerp_row(SPINE, y, 2)
        ak.add_box(bm, (0.0, y, z_hi - 0.022), (hw * 2.20, 0.016, 0.046), "AA_Greeble")
    # bloc mecanique dorsal, ETROIT (les aerofreins sont a cote)
    bay_z = lerp_row(SPINE, 0.185, 2)
    ak.add_box(bm, (0.0, 0.185, bay_z - 0.006), (0.050, 0.250, 0.030), "AA_Greeble")
    ak.add_box(bm, (0.0, 0.185, bay_z + 0.010), (0.036, 0.200, 0.010), "AA_Greeble")
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * 0.028, 0.185, bay_z - 0.002), (0.008, 0.260, 0.034), "AA_Trim")
    ak.add_box(bm, (0.0, 0.150, bay_z + 0.016), (0.016, 0.110, 0.008), "AA_Emissive_Engine")
    ak.add_box(bm, (0.0, 0.300, bay_z + 0.014), (0.030, 0.030, 0.012), "AA_Marking_Red")

    # --- quille, chine --------------------------------------------------
    _keel(bm)
    for sx in (ak.PORT, ak.STARBOARD):
        rings = []
        for y in CHINE_Y:
            w, f, crown, belly = section_params(y)
            zt = z_top(f, w, f, crown, belly)
            zb = z_bot(f, w, f, crown, belly)
            zc = zb + (zt - zb) * 0.44
            x0, x1 = f - 0.012, min(f + 0.024, w - 0.006)
            rings.append(ak.add_ring(bm, [(sx * x0, y, zc + 0.010), (sx * x1, y, zc + 0.004),
                                          (sx * x1, y, zc - 0.004), (sx * x0, y, zc - 0.010)]))
        for i in range(len(rings) - 1):
            ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Greeble")
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
        ak.cap_ring(bm, rings[-1], "AA_Greeble")

    # --- tuyere d'axe ---------------------------------------------------
    ak.add_lathe(bm, TAIL_NOZZLE, 20, center_x=0.0, center_z=TAIL_NOZZLE_Z)
    bore = [_circle(bm, y, r, 0.0, TAIL_NOZZLE_Z, segments=20)
            for y, r in ((1.185, 0.056), (1.170, 0.050), (1.150, 0.040))]
    for i in range(len(bore) - 1):
        ak.bridge_rings(bm, bore[i], bore[i + 1], "AA_Emissive_Engine")
    ak.fan_to_point(bm, bore[-1], bm.verts.new((0.0, TAIL_BORE_FLOOR, TAIL_NOZZLE_Z)),
                    "AA_Emissive_Engine")

    # --- nacelles, caissons, emplantures, derives, baies ------------------
    for sx in (ak.PORT, ak.STARBOARD):
        _nacelle(bm, sx)
        _bridge(bm, sx)
        _glove(bm, sx)
        _fin(bm, sx)
        _airbrake_bay_machinery(bm, sx)

    # --- canon ventral ----------------------------------------------------
    barrel_z = _barrel_z()
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_lathe(
            bm,
            [(-0.900, 0.000, "AA_Greeble"), (-0.890, BARREL_R, "AA_Greeble"),
             (-1.020, BARREL_R, "AA_Greeble"), (-1.030, BARREL_R * 1.22, "AA_Trim"),
             (BARREL_TIP, BARREL_R * 1.18, "AA_Trim"), (BARREL_TIP, BARREL_R * 0.60, "AA_Greeble"),
             (-1.040, BARREL_R * 0.55, "AA_Greeble"), (-1.038, 0.000, "AA_Greeble")],
            14, center_x=sx * BARREL_X, center_z=barrel_z,
        )
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * (lerp_row(KEEL, 0.150, 1) + 0.004), 0.150, -0.250),
                   (0.010, 0.200, 0.040), "AA_Greeble")

    # --- greebles : zones techniques SEULEMENT (dessus des caissons) --------
    for k, sx in enumerate((ak.PORT, ak.STARBOARD)):
        ak.greeble_strip(bm, (sx * 0.150, 0.060, 0.056), (sx * 0.150, 0.330, 0.050),
                         count=4, seed=rng_seed + 17 * (k + 1) + 7,
                         size_range=(0.014, 0.026), height_range=(0.005, 0.011))

    return ak.new_object("Specter9C_Details", bm)


def _barrel_z() -> float:
    y = -1.020
    return (lerp_row(KEEL, y, 2) + lerp_row(KEEL, y, 3)) * 0.5


# ==========================================================================
# Pieces mobiles (ak.moving_part -> nœuds glTF separes)
# ==========================================================================


def _wing_section(s: float, y_clamp: float | None = None):
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
        h = _wing_thickness(s, t0)
        top.append((x, y, z0 + h))
        bot.append((x, y, z0 - h))
    return top, bot


def _flap_fitting_spans() -> tuple[float, float]:
    s0 = _flap_root_s()
    return s0 + 0.15 * (1.0 - s0), s0 + 0.85 * (1.0 - s0)


def build_wing(side: float) -> ak.MovingPart:
    """Aile a fleche variable : lame a PROFIL DE VOILURE, rainures de longeron,
    panneaux bleus en retrait, pod de bout d'aile avec feu de position, deux
    paliers de charniere de volet sous l'intrados. Batie a babord, miroitee."""
    tag = "L" if side > 0 else "R"
    bm = bmesh.new()
    s0 = _flap_root_s()
    stations = _wing_rib_stations()

    rings = []
    for s in stations:
        top, bot = _wing_section(s, y_clamp=FLAP_WALL_Y if s >= s0 - 1e-9 else None)
        rings.append(ak.add_ring(bm, top + list(reversed(bot))))

    n = len(WING_CHORD_T)
    bands = []
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        bands.append(band)
        ak.set_material([band[n - 1]], "AA_Greeble")
        ak.set_material([band[2 * n - 1]], "AA_Trim")
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Greeble")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    # rainures de longeron (paires serrees 0,300/0,345 et 0,700/0,745)
    for j in (5, 8):
        for jj in (j, 2 * n - 2 - j):
            ak.inset_panel(bm, _insettable([b[jj] for b in bands], SEAM_T),
                           "AA_Hull", thickness=SEAM_T, depth=SEAM_D)
    # panneaux bleus EN RETRAIT sur l'extrados (fractions d'envergure)
    for s0f, s1f, js, mat in (
        (0.00, 0.38, (2, 3), "AA_Panel"),
        (0.26, 0.72, (6, 7), "AA_Panel"),
        (0.60, 1.00, (2, 3, 4), "AA_Panel"),
    ):
        faces = []
        for i in range(len(bands)):
            mid = (stations[i] + stations[i + 1]) * 0.5
            if s0f <= mid <= s1f:
                faces += [bands[i][j] for j in js]
        faces = _insettable(faces, 0.006)
        if faces:
            ak.inset_panel(bm, faces, "AA_Hull", thickness=0.005, depth=-0.004)
            ak.inset_panel(bm, faces, mat, thickness=0.006, depth=-0.006)
    for i in range(len(bands)):
        mid = (stations[i] + stations[i + 1]) * 0.5
        if 0.20 <= mid <= 0.62:
            ak.set_material([bands[i][2 * n - 1]], "AA_Trim")

    # --- pod de bout d'aile (Muzzle_Tip) avec feu de position de 1 cm -------
    (x_le, y_le), (x_te, y_te) = _wing_edges(1.0)
    y_te = min(y_te, FLAP_WALL_Y)
    z_tip = _wing_plane_z(1.0)
    ak.add_lathe(
        bm,
        [(y_le - 0.046, 0.000, "AA_Greeble"), (y_le - 0.040, 0.006, "AA_Trim"),
         (y_le - 0.026, 0.014, "AA_Greeble"), (y_le - 0.010, 0.017, "AA_Greeble"),
         (y_le + 0.004, 0.017, "AA_Emissive_Engine"), (y_le + 0.014, 0.017, "AA_Greeble"),
         (y_te - 0.012, 0.017, "AA_Greeble"), (y_te + 0.004, 0.012, "AA_Greeble"),
         (y_te + 0.008, 0.000, "AA_Greeble")],
        14, center_x=x_le - 0.018, center_z=z_tip,
    )

    # --- paliers de charniere de volet, cote INTRADOS, en avant de la cloison
    for s in _flap_fitting_spans():
        (lx, ly), (tx, ty) = _wing_edges(s)
        t = min(max((FLAP_WALL_Y - 0.016 - ly) / max(ty - ly, 1e-6), 0.0), 1.0)
        x = lx + (tx - lx) * t
        z = _wing_plane_z(s) - _wing_thickness(s, 0.95) - 0.004
        ak.add_box(bm, (x, FLAP_WALL_Y - 0.016, z), (0.020, 0.022, 0.008), "AA_Greeble")

    if side < 0:
        for vert in bm.verts:
            vert.co.x = -vert.co.x
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    return ak.moving_part(f"Wing_{tag}", bm, (side * WING_PIVOT_X, WING_PIVOT_Y, WING_PIVOT_Z))


def build_flap(side: float) -> ak.MovingPart:
    """Volet de bord de fuite, ENFANT de l'aile, avec ses deux ferrures de
    charniere visibles cote intrados."""
    tag = "L" if side > 0 else "R"
    bm = bmesh.new()
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
        ak.set_material([band[n - 1]], "AA_Greeble")   # tranche de bord de fuite, sombre
        ak.set_material([band[2 * n - 1]], "AA_Greeble")
    ak.cap_ring(bm, list(reversed(ribs[0])), "AA_Greeble")
    ak.cap_ring(bm, ribs[-1], "AA_Greeble")
    for s in _flap_fitting_spans():
        (lx, ly), (tx, ty) = _wing_edges(s)
        t = min(max((FLAP_HINGE_Y + 0.016 - ly) / max(ty - ly, 1e-6), 0.0), 1.0)
        x = lx + (tx - lx) * t
        z = _wing_plane_z(s) - _wing_thickness(s, t) - 0.004
        ak.add_box(bm, (side * x, FLAP_HINGE_Y + 0.016, z), (0.020, 0.022, 0.008), "AA_Greeble")
    xs = [v.co.x for v in bm.verts]
    pivot = ((min(xs) + max(xs)) * 0.5, FLAP_HINGE_Y, FLAP_HINGE_Z)
    return ak.moving_part(f"Flap_{tag}", bm, pivot, parent=f"Wing_{tag}")


def build_nozzle(side: float) -> ak.MovingPart:
    """Corps de tuyere a ROTULE : col dans la douille de nacelle, evasement,
    anneau dore, chambre emissive. Pivot SUR L'AXE dans le plan des charnieres
    (BRIEF-0098) : le lacet tourne le corps ET ses douze petales enfants."""
    tag = "L" if side > 0 else "R"
    cx, cz = side * NACELLE_X, NACELLE_Z
    bm = bmesh.new()
    _lathe_rings(bm, NOZZLE_BODY, cx, cz)
    _nozzle_bore(bm, cx, cz)
    # six bossages de verin de pétale autour de l'evasement (zone technique)
    for k in range(6):
        a = math.pi / 6.0 + k * math.pi / 3.0
        r0, r1 = 0.088, 0.100
        ak.add_tube(bm, (cx + r0 * math.cos(a), 1.004, cz + r0 * math.sin(a)),
                    (cx + r1 * math.cos(a), 1.004, cz + r1 * math.sin(a)),
                    0.006, 8, "AA_Greeble")
    return ak.moving_part(f"Nozzle_{tag}", bm, (cx, NOZZLE_HINGE_Y, cz))


def _petal_angle(p: int) -> float:
    return p * 2.0 * math.pi / NOZZLE_PETALS


def _petal_pivot(side: float, p: int) -> tuple[float, float, float]:
    cx, cz = side * NACELLE_X, NACELLE_Z
    mid = _petal_angle(p)
    return (cx + PETAL_HINGE_R * math.cos(mid), NOZZLE_HINGE_Y, cz + PETAL_HINGE_R * math.sin(mid))


def _petal_open_axis(p: int) -> Vector:
    """Axe (repere d'auteur) dont la rotation POSITIVE ecarte le petale de
    l'axe de tuyere : l'oppose de la tangente au cercle des charnieres."""
    mid = _petal_angle(p)
    return Vector((math.sin(mid), 0.0, -math.cos(mid)))


def build_petal(side: float, p: int) -> ak.MovingPart:
    """Un petale de tuyere, enfant de `Nozzle_*`, ferme au repos, avec un
    raidisseur longitudinal sur sa face externe. Les petales du haut sont
    raccourcis de `PETAL_SCARF` (la chambre se voit depuis la camera de jeu)."""
    tag = "L" if side > 0 else "R"
    cx, cz = side * NACELLE_X, NACELLE_Z
    bm = bmesh.new()
    step = 2.0 * math.pi / NOZZLE_PETALS
    gap = math.radians(PETAL_GAP_DEG)
    last = len(PETAL_SECTIONS) - 1
    mid = _petal_angle(p)
    a0, a1 = mid - step * 0.5 + gap * 0.5, mid + step * 0.5 - gap * 0.5
    scarf = PETAL_SCARF * (0.5 + 0.5 * math.sin(mid))
    angles = [a0 + (a1 - a0) * k / (PETAL_ARC - 1) for k in range(PETAL_ARC)]
    rings = []
    scarfed: list[tuple[float, float]] = []
    for k, (y, r_in, r_out) in enumerate(PETAL_SECTIONS):
        yy = y - scarf * (k / last) + (PETAL_ROOT_GAP if k == 0 else 0.0)
        scarfed.append((yy, r_out))
        outer = [(cx + r_out * math.cos(a), yy, cz + r_out * math.sin(a)) for a in angles]
        inner = [(cx + r_in * math.cos(a), yy, cz + r_in * math.sin(a)) for a in reversed(angles)]
        rings.append(ak.add_ring(bm, outer + inner))
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Greeble")
        # peau EXTERNE en blanc de coque (metal clair de la planche de concept) :
        # les petales sont le point focal arriere, et douze petales anthracite
        # portaient a eux seuls le greeble vu de la camera de jeu a 23 %.
        ak.set_material(band[: PETAL_ARC - 1], "AA_Hull")
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Trim")     # la levre de sortie seule est doree
    # raidisseur : nervure courbe sur la face externe, du 2e au 4e anneau
    half = step * 0.10
    _polar_slab(bm, cx, cz, [scarfed[1][0], scarfed[2][0], scarfed[3][0]],
                mid - half, mid + half, lambda y: lerp_table(scarfed, y) - 0.0005,
                0.0045, "AA_Greeble", arc_points=3)
    return ak.moving_part(f"Petal_{tag}_{p:02d}", bm, _petal_pivot(side, p),
                          parent=f"Nozzle_{tag}")


def _airbrake_stations() -> list[float]:
    y0, y1 = AIRBRAKE_Y0 + AIRBRAKE_MARGIN, AIRBRAKE_Y1 - AIRBRAKE_MARGIN
    return [y0 + (y1 - y0) * k / 7.0 for k in range(8)]


def _airbrake_hinge(side: float) -> tuple[float, float, float]:
    y = AIRBRAKE_Y0 + AIRBRAKE_MARGIN
    x_in, x_out = _airbrake_x_range(y, side)
    x_mid = (x_in + side * AIRBRAKE_MARGIN + x_out - side * AIRBRAKE_MARGIN_OUT) * 0.5
    return (x_mid, y, _deck_z(x_mid, y))


def build_airbrake(side: float) -> ak.MovingPart:
    """Trappe d'aerofrein : plaque CONFORME au pont (elle suit la joue et la
    marche), epaisse de 8 mm, a fleur de la coque au repos. Charniere AVANT."""
    tag = "L" if side > 0 else "R"
    bm = bmesh.new()
    rings = []
    for y in _airbrake_stations():
        x_in, x_out = _airbrake_x_range(y, side)
        a, b = x_in + side * AIRBRAKE_MARGIN, x_out - side * AIRBRAKE_MARGIN_OUT
        xs = [a + (b - a) * k / 5.0 for k in range(6)]
        top = [(x, y, _deck_z(x, y)) for x in xs]
        bot = [(x, y, _deck_z(x, y) - AIRBRAKE_T) for x in xs]
        rings.append(ak.add_ring(bm, top + list(reversed(bot))))
    n = 6
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Greeble")
        ak.set_material(band[: n - 1], "AA_Hull")
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Greeble")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # une rainure au milieu du dessus, et l'oeil de la trappe : un panneau bleu
    top_faces = []
    bm.faces.ensure_lookup_table()
    for face in bm.faces:
        if face.material_index == ak.mat_index("AA_Hull"):
            top_faces.append(face)
    top_faces = _insettable(top_faces, 0.006)
    if top_faces:
        ak.inset_panel(bm, top_faces, "AA_Panel", thickness=0.006, depth=-0.003)
    return ak.moving_part(f"Airbrake_{tag}", bm, _airbrake_hinge(side))


def _intake_ramp_r(y: float) -> float:
    return _nacelle_radius(y, math.pi * 0.5) + INTAKE_RAMP_LIFT


def build_intake(side: float) -> ak.MovingPart:
    """Rampe d'entree d'air variable : plaque courbe sur la levre superieure de
    la nacelle, 3 mm au-dessus de la peau, charniere AVANT le long de X."""
    tag = "L" if side > 0 else "R"
    cx, cz = side * NACELLE_X, NACELLE_Z
    bm = bmesh.new()
    half = math.radians(INTAKE_RAMP_HALF_DEG)
    ys = [INTAKE_RAMP_Y0 + (INTAKE_RAMP_Y1 - INTAKE_RAMP_Y0) * k / 5.0 for k in range(6)]
    faces = _polar_slab(bm, cx, cz, ys, math.pi * 0.5 - half, math.pi * 0.5 + half,
                        _intake_ramp_r, INTAKE_RAMP_T, "AA_Hull", arc_points=9)
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    # bord d'attaque dore de la rampe (le premier anneau de faces)
    bm.faces.ensure_lookup_table()
    pivot = (cx, INTAKE_RAMP_Y0, cz + _intake_ramp_r(INTAKE_RAMP_Y0) + INTAKE_RAMP_T)
    return ak.moving_part(f"Intake_{tag}", bm, pivot)


def _rudder_s0() -> float:
    return RUDDER_S0 + RUDDER_GAP / FIN_HEIGHT


def _rudder_axis(side: float) -> tuple[tuple[float, float, float], Vector]:
    """(pivot, axe unitaire) de la gouverne, repere d'auteur : la ligne de
    charniere, droite, inclinee comme la derive."""
    point, axis, _n, _o = _fin_frame(side)
    s0 = _rudder_s0()
    pivot = point(s0, _fin_hinge_y(s0), 0.0)
    slope = (_fin_hinge_y(1.0) - _fin_hinge_y(RUDDER_S0)) / (1.0 - RUDDER_S0)
    direction = (axis * FIN_HEIGHT + Vector((0.0, slope, 0.0))).normalized()
    return pivot, direction


def build_rudder(side: float) -> ak.MovingPart:
    tag = "L" if side > 0 else "R"
    point, _a, _n, _o = _fin_frame(side)
    bm = bmesh.new()
    s0 = _rudder_s0()
    stations = [s0 + (1.0 - s0) * k / 6.0 for k in range(7)]
    rings = [ak.add_ring(bm, [point(s, y, n) for y, n in _rudder_section(s)]) for s in stations]
    m = RUDDER_NOSE_M
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        ak.set_material(band[: m - 1], "AA_Greeble")            # nez rond
        ak.set_material([band[m], band[m + 1]], "AA_Greeble")   # tranche de fuite
        if 1 <= i <= 4:
            ak.set_material([band[m - 1]], "AA_Panel")          # flanc vu d'en haut
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Trim")
    pivot, _ = _rudder_axis(side)
    return ak.moving_part(f"Rudder_{tag}", bm, pivot)


def _grapple_points(side: float):
    z = _grapple_axis_z()
    x0 = side * (_keel_flank_x(GRAPPLE_HINGE_Y) + GRAPPLE_STANDOFF)
    x1 = side * (_keel_flank_x(GRAPPLE_TIP_Y) + GRAPPLE_STANDOFF)
    return (x0, GRAPPLE_HINGE_Y, z), (x1, GRAPPLE_TIP_Y, z)


def build_grapple(side: float) -> ak.MovingPart:
    """Grappin d'appontage : bras conique couche contre le flanc de quille,
    articule sur une chape (les joues sont dans la coque), tete a deux dents."""
    tag = "L" if side > 0 else "R"
    bm = bmesh.new()
    root, tip = _grapple_points(side)
    ak.add_tube(bm, root, tip, GRAPPLE_R, 10, "AA_Greeble", radius_end=GRAPPLE_R * 0.7)
    # tourillon coaxial a la charniere, entre les deux joues de la chape
    ak.add_tube(bm, (root[0] - side * 0.004, root[1], root[2]),
                (root[0] + side * 0.012, root[1], root[2]), 0.012, 10, "AA_Greeble")
    # tete : bloc dore et deux dents vers le bas
    ak.add_box(bm, (tip[0], tip[1] - 0.004, tip[2]), (0.022, 0.022, 0.018), "AA_Greeble")
    for dx in (-0.006, 0.006):
        ak.add_tube(bm, (tip[0] + dx, tip[1], tip[2] - 0.004),
                    (tip[0] + dx * 1.6, tip[1] + 0.010, tip[2] - 0.020), 0.0035, 6, "AA_Greeble")
    return ak.moving_part(f"Grapple_{tag}", bm, root)


def _grapple_mounts(bm) -> None:
    """Les deux joues de chape de chaque grappin, DANS la coque (elles ne
    bougent pas), de part et d'autre du tourillon, 3 mm de jeu."""
    z = _grapple_axis_z()
    for side in (ak.PORT, ak.STARBOARD):
        x_flank = side * _keel_flank_x(GRAPPLE_HINGE_Y)
        x0 = x_flank + side * (GRAPPLE_STANDOFF + 0.012)
        for dy in (-0.021, 0.021):
            ak.add_box(bm, ((x_flank + x0) * 0.5, GRAPPLE_HINGE_Y + dy, z),
                       (abs(x0 - x_flank) + 0.004, 0.012, 0.030), "AA_Greeble")


def _canopy_base_z(y: float) -> float:
    return lerp_table(CROWN, y) - CANOPY_SINK


def _canopy_hinge() -> tuple[float, float, float]:
    return (0.0, CANOPY_HINGE_Y, _canopy_base_z(CANOPY[-1][0]) + 0.006)


def build_canopy() -> ak.MovingPart:
    """Verriere en goutte : bulle `AA_Glass`, deux longerons de base et TROIS
    montants `AA_Trim` (cadre du brief), charniere ARRIERE le long de X."""
    bm = bmesh.new()
    _dome(bm, CANOPY, 0.0, _canopy_base_z, "AA_Glass")

    # longerons de base : ils recouvrent le joint bulle/puits
    for sx in (ak.PORT, ak.STARBOARD):
        rings = []
        for y, hw, _h in CANOPY[1:-1]:
            z0 = _canopy_base_z(y)
            rings.append(ak.add_ring(bm, [(sx * (hw + 0.004), y, z0 + 0.014),
                                          (sx * (hw - 0.004), y, z0 + 0.014),
                                          (sx * (hw - 0.004), y, z0 - 0.002),
                                          (sx * (hw + 0.004), y, z0 - 0.002)]))
        for i in range(len(rings) - 1):
            ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Trim")
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Trim")
        ak.cap_ring(bm, rings[-1], "AA_Trim")

    # trois montants : barres courbes epousant la bulle
    for y_m in CANOPY_MULLIONS:
        hw = lerp_row(CANOPY, y_m, 1)
        h = lerp_row(CANOPY, y_m, 2)
        z0 = _canopy_base_z(y_m)
        rings = []
        for k in range(DOME_ARC):
            a = math.pi * k / (DOME_ARC - 1)
            ci, co = (hw - 0.001), (hw + CANOPY_MULLION_T)
            hi_, ho = (h - 0.001), (h + CANOPY_MULLION_T)
            w2 = CANOPY_MULLION_W * 0.5
            rings.append(ak.add_ring(bm, [
                (ci * math.cos(a), y_m - w2, z0 + hi_ * math.sin(a)),
                (co * math.cos(a), y_m - w2, z0 + ho * math.sin(a)),
                (co * math.cos(a), y_m + w2, z0 + ho * math.sin(a)),
                (ci * math.cos(a), y_m + w2, z0 + hi_ * math.sin(a)),
            ]))
        for i in range(len(rings) - 1):
            ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Trim")
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Trim")
        ak.cap_ring(bm, rings[-1], "AA_Trim")

    # traverse arriere (le dosseret est dans la coque ; ceci est la ferrure de
    # charniere, sur la verriere)
    y_r = CANOPY[-2][0]
    z_r = _canopy_base_z(y_r)
    ak.add_box(bm, (0.0, y_r + 0.006, z_r + 0.010), (0.040, 0.016, 0.014), "AA_Trim")
    return ak.moving_part("Canopy", bm, _canopy_hinge())


# ==========================================================================
# Points d'attache
# ==========================================================================


def _wing_le_point(s: float) -> tuple[float, float, float]:
    (x_le, y_le), _ = _wing_edges(s)
    return (x_le, y_le - 0.030, _wing_plane_z(s))


def build_attach_points() -> list:
    points: list = []
    points += list(ak.attach_pair("Muzzle", BARREL_X, MUZZLE_Y, _barrel_z()))
    points.append(ak.attach_point("Muzzle_C", (0.0, MUZZLE_Y, _barrel_z())))
    x_wing, y_wing, z_wing = _wing_le_point(WING_MUZZLE_S)
    points += list(ak.attach_pair("Muzzle_Wing", x_wing, y_wing, z_wing))
    (x_le, y_le), _ = _wing_edges(1.0)
    points += list(ak.attach_pair("Muzzle_Tip", x_le - 0.018, y_le - 0.050, _wing_plane_z(1.0)))
    # Engine_* au FOND DE CHAMBRE de chaque tuyere (BRIEF-0098) : la plume part de la.
    points += list(ak.attach_pair("Engine", NACELLE_X, NOZZLE_FLOOR_Y + 0.004,
                                  NACELLE_Z + NOZZLE_BORE[-1][2]))
    y_mid = (CANOPY[0][0] + CANOPY[-1][0]) * 0.5
    peak = max(CANOPY, key=lambda s: s[2])
    points.append(ak.attach_point("Cockpit", (0.0, y_mid, _canopy_base_z(y_mid) + peak[2] * 0.45)))
    return points


# ==========================================================================
# Finition et depliage
# ==========================================================================


def _finish(obj, bevel: float, segments: int) -> None:
    """Nettoyage, biseaux (2 segments sur la peau, 3 sur les couronnes et le
    cadre de verriere), lissage par angle. Le depliage vient a part, par zone."""
    ak.cleanup(obj)
    ak.bevel_sharp_edges(obj, width=bevel, segments=segments, angle_deg=34.0)
    ak.shade_smooth_by_angle(obj, angle_deg=34.0)


# ==========================================================================
# Mesures polaires heritees (BRIEF-0035/0036)
# ==========================================================================


def _flap_travel_limit(part: ak.MovingPart) -> float:
    _, y_p, z_p = part.pivot
    limit = math.pi * 0.5
    for vert in part.obj.data.vertices:
        dy, dz = vert.co.y - y_p, vert.co.z - z_p
        for sign in (1.0, -1.0):
            a, b = dy, -sign * dz
            target = FLAP_WALL_Y - y_p
            radius = math.hypot(a, b)
            if radius < 1e-9 or abs(target) > radius:
                continue
            phase = math.atan2(b, a)
            angle = math.acos(target / radius) + phase
            angle = angle % (2.0 * math.pi)
            if 1e-4 < angle <= math.pi * 0.5:
                limit = min(limit, angle)
    return math.degrees(limit)


def _wing_sweep_limit(wing: ak.MovingPart, flap: ak.MovingPart) -> tuple[float, str]:
    px, py, _ = wing.pivot
    pts = [(abs(v.co.x), v.co.y) for v in wing.obj.data.vertices]
    pts += [(abs(v.co.x), v.co.y) for v in flap.obj.data.vertices]
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
            if half > 0.0 and x < NACELLE_X + half + WING_CLEARANCE:
                return theta - step, (
                    f"peau de nacelle a y = {y:+.3f} (x = {x:.4f}, peau {NACELLE_X + half:.4f})"
                )
        theta += step
    return limit, reason


def _glove_clearance(wing: ak.MovingPart, flap: ak.MovingPart) -> tuple[float, str]:
    px, py, _ = wing.pivot
    travel = min(_flap_travel_limit(flap), FLAP_TRAVEL_TARGET)
    samples = [(abs(v.co.x), v.co.y, v.co.z) for v in wing.obj.data.vertices]
    _, hy, hz = flap.pivot
    for delta in (-travel, -travel * 0.5, 0.0, travel * 0.5, travel):
        rad = math.radians(delta)
        cos_d, sin_d = math.cos(rad), math.sin(rad)
        for v in flap.obj.data.vertices:
            dy, dz = v.co.y - hy, v.co.z - hz
            samples.append((abs(v.co.x), hy + dy * cos_d - dz * sin_d, hz + dy * sin_d + dz * cos_d))
    polar = [(math.hypot(ax - abs(px), y - py), math.atan2(y - py, ax - abs(px)), z)
             for ax, y, z in samples]
    best = 1e9
    where = "aucun sommet sous l'emplanture"
    theta = 0.0
    while theta <= WING_SWEEP_TARGET + 1e-9:
        rad = math.radians(theta)
        for r, phi, z in polar:
            x = abs(px) + r * math.cos(phi + rad)
            y = py + r * math.sin(phi + rad)
            if not _in_glove(x, y):
                continue
            gap = _glove_floor(y) - z
            if gap < best:
                best = gap
                where = (f"fleche {theta:.0f} deg, (x = {x:.4f}, y = {y:+.4f}, z = {z:+.4f}) "
                         f"sous plancher {_glove_floor(y):.4f}")
        theta += 1.0
    return best, where


def _wing_inboard_x(y: float, sweep_deg: float = 0.0) -> float:
    rad = math.radians(sweep_deg)
    best = -1.0
    for k in range(81):
        s = k / 80.0
        (lx, ly), (tx, ty) = _wing_edges(s)
        for m in range(41):
            t = m / 40.0
            x = lx + (tx - lx) * t
            yy = ly + (ty - ly) * t
            if sweep_deg:
                dx, dy = x - WING_PIVOT_X, yy - WING_PIVOT_Y
                r, phi = math.hypot(dx, dy), math.atan2(dy, dx) + rad
                x = WING_PIVOT_X + r * math.cos(phi)
                yy = WING_PIVOT_Y + r * math.sin(phi)
            if abs(yy - y) <= 0.006:
                best = x if best < 0.0 else min(best, x)
    return best


def _print_root_coverage() -> list[str]:
    """Recouvrement de la racine par l'emplanture aux deux extremes de fleche
    (BRIEF-0036) : un ecart negatif est un recouvrement, un positif une fente."""
    out = []
    for sweep in (0.0, WING_SWEEP_TARGET):
        y0 = _polar(WING_LE_ROOT[0], WING_LE_ROOT[1] + sweep)[1]
        y1 = _polar(WING_TE_ROOT[0], WING_TE_ROOT[1] + sweep)[1]
        worst, worst_y = -1e9, y0
        for k in range(121):
            y = y0 + (y1 - y0) * k / 120.0
            inboard = _wing_inboard_x(y, sweep)
            x_out = _glove_x_out(y)
            if inboard < 0.0 or x_out < 0.0:
                continue
            gap = inboard - x_out
            if gap > worst:
                worst, worst_y = gap, y
        verdict = "RECOUVREMENT" if worst < 0.0 else "FENTE"
        out.append(f"racine a {sweep:4.1f} deg de fleche (y {y0:+.3f} -> {y1:+.3f}) : "
                   f"pire ecart {worst * 1000:+7.1f} mm a y = {worst_y:+.3f}  [{verdict}]")
    return out


def _print_silhouette_gaps() -> None:
    print("  fentes vues de dessus (demi-envergure, cote babord) :")
    for label, y in (("nez de nacelle   ", -0.360), ("avant du caisson ", -0.100),
                     ("caisson (fermee) ", 0.200), ("arriere caisson  ", 0.560),
                     ("emplanture d'aile", 0.300), ("poupe            ", 0.960)):
        fus = section_cut(y)
        nac_lo = NACELLE_X - nacelle_half_width(y)
        nac_hi = NACELLE_X + nacelle_half_width(y)
        bridged = BRIDGE[0][0] <= y <= BRIDGE[-1][0]
        gap1 = 0.0 if bridged else max(nac_lo - fus, 0.0)
        x_out = _glove_x_out(y)
        g2 = ("emplanture absente" if x_out < 0.0
              else f"emplanture jusqu'a x = {x_out:.3f} ({(x_out - nac_hi) * 1000:+4.0f} mm)")
        print(f"    y = {y:+.3f}  {label} : fente 1 = {gap1 * 1000:5.0f} mm | {g2}")


# ==========================================================================
# Balayage BVH : plafonds mecaniques et table des degagements (BRIEF-0098)
# ==========================================================================


def _mesh_arrays(obj) -> tuple[list[Vector], list[list[int]]]:
    verts = [v.co.copy() for v in obj.data.vertices]
    polys = [list(p.vertices) for p in obj.data.polygons]
    return verts, polys


def _bvh(verts: list[Vector], polys: list[list[int]]) -> BVHTree | None:
    if not polys:
        return None
    return BVHTree.FromPolygons([tuple(v) for v in verts], polys, all_triangles=False)


def _rotate_points(points: list[Vector], pivot: Vector, axis: Vector, deg: float) -> list[Vector]:
    rot = Matrix.Rotation(math.radians(deg), 3, axis)
    return [pivot + rot @ (p - pivot) for p in points]


def _bbox(points: list[Vector], pad: float) -> tuple[Vector, Vector]:
    lo = Vector((min(p.x for p in points) - pad, min(p.y for p in points) - pad,
                 min(p.z for p in points) - pad))
    hi = Vector((max(p.x for p in points) + pad, max(p.y for p in points) + pad,
                 max(p.z for p in points) + pad))
    return lo, hi


def _filtered_bvh(verts, polys, lo: Vector, hi: Vector) -> BVHTree | None:
    """BVH des seuls polygones dont un sommet tombe dans la boite [lo, hi] :
    la coque fait des centaines de milliers de triangles, une piece n'en
    approche que quelques milliers."""
    keep = []
    for poly in polys:
        for i in poly:
            v = verts[i]
            if lo.x <= v.x <= hi.x and lo.y <= v.y <= hi.y and lo.z <= v.z <= hi.z:
                keep.append(poly)
                break
    return _bvh(verts, keep)


#: Direction du rayon de containment : legerement hors axe, pour ne jamais
#: longer une arete ni un plan de la trame (les stations sont a y constant).
_RAY_DIR = Vector((0.0137, 0.0071, 1.0)).normalized()


def _winding(tree: BVHTree, p: Vector, max_hits: int = 64) -> int:
    """Nombre de solides FERMES contenant `p`, par lancer de rayon : +1 a chaque
    sortie (normale dans le sens du rayon), -1 a chaque entree. Robuste aux
    solides qui se chevauchent — ce que la coque est partout — la ou le test
    « signe de la normale au point le plus proche » ment sur toute arete
    convexe (une trappe 15 mm EN L'AIR au-dessus de sa baie etait vue a
    l'interieur du borde, parce que son point le plus proche etait le haut de
    celui-ci)."""
    count = 0
    origin = p.copy()
    for _ in range(max_hits):
        loc, nor, _idx, dist = tree.ray_cast(origin, _RAY_DIR)
        if loc is None:
            break
        count += 1 if nor.dot(_RAY_DIR) > 0.0 else -1
        origin = loc + _RAY_DIR * 1e-5
    return count


def _min_gap(points: list[Vector], tree: BVHTree | None,
             near_only: float | None = None) -> tuple[float, Vector | None]:
    """Distance SIGNEE minimale des points a la surface de `tree` : negative si
    le point est CONTENU (nombre d'enroulement > 0), positive sinon.

    `near_only` : si donne, le containment n'est verifie que pour les points a
    moins de cette distance de la surface (entre deux pas de 1 deg, une piece
    bouge de quelques millimetres : un point ne peut pas passer de 8 mm dehors
    a « dedans » sans avoir ete pres de la surface)."""
    if tree is None:
        return math.inf, None
    best, where = math.inf, None
    for p in points:
        loc, _nor, _idx, dist = tree.find_nearest(p)
        if loc is None:
            continue
        if near_only is None or dist < near_only:
            signed = -dist if _winding(tree, p) > 0 else dist
        else:
            signed = dist
        if signed < best:
            best, where = signed, p
    return best, where


class _Family:
    """Une famille de pieces mobiles a balayer : ses objets (enfants compris),
    son pivot, son axe d'OUVERTURE (rotation positive = ouverture), sa cible,
    l'angle maximal explore, et ses voisins (label -> fonction angle -> BVH)."""

    def __init__(self, name, parts, pivot, axis, target, theta_max, neighbors,
                 symmetric=False):
        self.name = name
        self.parts = parts
        self.pivot = Vector(pivot)
        self.axis = Vector(axis).normalized()
        self.target = target
        self.theta_max = theta_max
        self.neighbors = neighbors
        self.symmetric = symmetric
        self.points: list[Vector] = []
        for part in parts:
            self.points += [v.co.copy() for v in part.obj.data.vertices]


def _sweep_family(fam: _Family, step: float = 1.0) -> dict:
    """Plafond mecanique (deg) et jeux a la cible, pour une famille.

    Balaie theta de 0 a `theta_max` (et de 0 a -theta_max si `symmetric`) ;
    s'arrete a la premiere image ou un voisin passe sous CLEARANCE_MIN. Rend
    aussi, pour chaque voisin, le jeu minimal a la CIBLE du brief."""
    result = {"name": fam.name, "ceiling": math.inf, "reason": "aucune butee",
              "gaps_at_target": {}, "gap_at_rest": {}}
    signs = (1.0, -1.0) if fam.symmetric else (1.0,)
    for sign in signs:
        theta = 0.0
        stopped = False
        while theta <= fam.theta_max + 1e-9 and not stopped:
            pts = _rotate_points(fam.points, fam.pivot, fam.axis, sign * theta)
            for label, provider in fam.neighbors:
                gap, where = _min_gap(pts, provider(sign * theta),
                                      near_only=None if abs(theta) < 1e-9 else 0.008)
                if abs(theta) < 1e-9:
                    result["gap_at_rest"][label] = min(result["gap_at_rest"].get(label, math.inf), gap)
                if abs(theta - fam.target) < step * 0.5 + 1e-9:
                    key = f"{label}" if not fam.symmetric else f"{label} ({'+' if sign > 0 else '-'})"
                    result["gaps_at_target"][key] = gap
                if gap < CLEARANCE_MIN:
                    ceiling = theta - step
                    if ceiling < result["ceiling"]:
                        result["ceiling"] = ceiling
                        w = f"({where.x:+.3f}, {where.y:+.3f}, {where.z:+.3f})" if where else "?"
                        result["reason"] = (
                            f"{label} a {sign * theta:+.0f} deg (jeu {gap * 1000:+.1f} mm, sommet {w})"
                        )
                    stopped = True
                    break
            theta += step
    return result


def _static_provider(tree: BVHTree | None):
    return lambda _theta: tree


def _moving_provider(part: ak.MovingPart, pivot, axis):
    """Voisin qui bouge AVEC la famille (petale adjacent) : son BVH est rebati
    a chaque angle, autour de son propre pivot."""
    verts, polys = _mesh_arrays(part.obj)
    pv, ax = Vector(pivot), Vector(axis).normalized()
    cache: dict[float, BVHTree | None] = {}

    def provider(theta: float):
        key = round(theta, 3)
        if key not in cache:
            cache[key] = _bvh(_rotate_points(verts, pv, ax, theta), polys)
        return cache[key]

    return provider


def _measure_all(ship, parts: dict[str, ak.MovingPart]) -> list[dict]:
    """Construit les familles, les balaie, rend la liste des resultats.

    Les voisins sont pris AU REPOS (sauf les petales adjacents, qui s'ouvrent
    ensemble) : c'est la table « piece ouverte x voisine » du brief."""
    hull_verts, hull_polys = _mesh_arrays(ship)
    part_arrays = {name: _mesh_arrays(p.obj) for name, p in parts.items()}

    def hull_near(points: list[Vector], pad: float):
        lo, hi = _bbox(points, pad)
        return _static_provider(_filtered_bvh(hull_verts, hull_polys, lo, hi))

    def part_near(name: str, points: list[Vector], pad: float):
        verts, polys = part_arrays[name]
        lo, hi = _bbox(points, pad)
        return _static_provider(_filtered_bvh(verts, polys, lo, hi))

    families: list[_Family] = []
    for side, tag in ((ak.PORT, "L"), (ak.STARBOARD, "R")):
        wing, flap = parts[f"Wing_{tag}"], parts[f"Flap_{tag}"]
        nozzle = parts[f"Nozzle_{tag}"]
        petals = [parts[f"Petal_{tag}_{p:02d}"] for p in range(NOZZLE_PETALS)]

        # --- aile (+ volet, son enfant), axe vertical, fleche vers l'arriere ----
        pts = [v.co.copy() for v in wing.obj.data.vertices] + [v.co.copy() for v in flap.obj.data.vertices]
        swept = pts + _rotate_points(pts, Vector(wing.pivot), Vector((0, 0, side)), 45.0)
        families.append(_Family(
            f"Wing_{tag}", [wing, flap], wing.pivot, (0.0, 0.0, side), WING_SWEEP_TARGET, 45.0,
            [("coque", hull_near(swept, 0.03)),
             (f"Nozzle_{tag}", part_near(f"Nozzle_{tag}", swept, 0.03)),
             (f"Airbrake_{tag}", part_near(f"Airbrake_{tag}", swept, 0.03)),
             (f"Rudder_{tag}", part_near(f"Rudder_{tag}", swept, 0.03))],
        ))
        # --- volet : +/-, contre l'aile (sa cloison) et la coque (emplanture) ---
        fpts = [v.co.copy() for v in flap.obj.data.vertices]
        fswept = fpts + _rotate_points(fpts, Vector(flap.pivot), Vector((1, 0, 0)), 40.0) \
            + _rotate_points(fpts, Vector(flap.pivot), Vector((1, 0, 0)), -40.0)
        families.append(_Family(
            f"Flap_{tag}", [flap], flap.pivot, (1.0, 0.0, 0.0), FLAP_TRAVEL_TARGET, 40.0,
            [(f"Wing_{tag}", part_near(f"Wing_{tag}", fswept, 0.02)),
             ("coque", hull_near(fswept, 0.02))], symmetric=True,
        ))
        # --- tuyere (+ 12 petales), lacet autour de la verticale ---------------
        npts = [v.co.copy() for v in nozzle.obj.data.vertices]
        for petal in petals:
            npts += [v.co.copy() for v in petal.obj.data.vertices]
        nswept = npts + _rotate_points(npts, Vector(nozzle.pivot), Vector((0, 0, 1)), 12.0) \
            + _rotate_points(npts, Vector(nozzle.pivot), Vector((0, 0, 1)), -12.0)
        families.append(_Family(
            f"Nozzle_{tag}", [nozzle] + petals, nozzle.pivot, (0.0, 0.0, 1.0),
            NOZZLE_YAW_TARGET, 12.0,
            [("coque (douille)", hull_near(nswept, 0.02)),
             (f"Rudder_{tag}", part_near(f"Rudder_{tag}", nswept, 0.02))], symmetric=True,
        ))
        # --- petales : chacun contre la tuyere, la coque, ses deux voisins -----
        for p, petal in enumerate(petals):
            ppts = [v.co.copy() for v in petal.obj.data.vertices]
            pivot, axis = Vector(_petal_pivot(side, p)), _petal_open_axis(p)
            pswept = ppts + _rotate_points(ppts, pivot, axis, 40.0)
            prev_p, next_p = (p - 1) % NOZZLE_PETALS, (p + 1) % NOZZLE_PETALS
            families.append(_Family(
                f"Petal_{tag}_{p:02d}", [petal], pivot, axis, PETAL_OPEN_TARGET, 40.0,
                [(f"Nozzle_{tag}", part_near(f"Nozzle_{tag}", pswept, 0.02)),
                 ("coque", hull_near(pswept, 0.02)),
                 (f"Petal_{tag}_{prev_p:02d}", _moving_provider(
                     petals[prev_p], _petal_pivot(side, prev_p), _petal_open_axis(prev_p))),
                 (f"Petal_{tag}_{next_p:02d}", _moving_provider(
                     petals[next_p], _petal_pivot(side, next_p), _petal_open_axis(next_p)))],
            ))
        # --- aerofrein : charniere avant, s'ouvre vers le haut -----------------
        brake = parts[f"Airbrake_{tag}"]
        bpts = [v.co.copy() for v in brake.obj.data.vertices]
        bswept = bpts + _rotate_points(bpts, Vector(brake.pivot), Vector((1, 0, 0)), 100.0) \
            + _rotate_points(bpts, Vector(brake.pivot), Vector((1, 0, 0)), 50.0)
        families.append(_Family(
            f"Airbrake_{tag}", [brake], brake.pivot, (1.0, 0.0, 0.0), AIRBRAKE_TARGET, 100.0,
            [("coque (baie, arete, derives)", hull_near(bswept, 0.02)),
             ("Canopy", part_near("Canopy", bswept, 0.02)),
             (f"Rudder_{tag}", part_near(f"Rudder_{tag}", bswept, 0.02))],
        ))
        # --- rampe d'entree d'air ---------------------------------------------
        ramp = parts[f"Intake_{tag}"]
        rpts = [v.co.copy() for v in ramp.obj.data.vertices]
        rswept = rpts + _rotate_points(rpts, Vector(ramp.pivot), Vector((1, 0, 0)), 60.0)
        families.append(_Family(
            f"Intake_{tag}", [ramp], ramp.pivot, (1.0, 0.0, 0.0), INTAKE_TARGET, 60.0,
            [("coque (nacelle, emplanture)", hull_near(rswept, 0.02)),
             (f"Wing_{tag}", part_near(f"Wing_{tag}", rswept, 0.02))],
        ))
        # --- gouverne : +/- autour de l'axe de derive --------------------------
        rudder = parts[f"Rudder_{tag}"]
        r_pivot, r_axis = _rudder_axis(side)
        rdpts = [v.co.copy() for v in rudder.obj.data.vertices]
        rdswept = rdpts + _rotate_points(rdpts, Vector(r_pivot), r_axis, 40.0) \
            + _rotate_points(rdpts, Vector(r_pivot), r_axis, -40.0)
        families.append(_Family(
            f"Rudder_{tag}", [rudder], r_pivot, r_axis, RUDDER_TARGET, 40.0,
            [("coque (derive, nacelle)", hull_near(rdswept, 0.02)),
             (f"Nozzle_{tag}", part_near(f"Nozzle_{tag}", rdswept, 0.02)),
             (f"Airbrake_{tag}", part_near(f"Airbrake_{tag}", rdswept, 0.02))], symmetric=True,
        ))
        # --- grappin : pend vers le bas (rotation NEGATIVE autour de +X) --------
        grapple = parts[f"Grapple_{tag}"]
        gpts = [v.co.copy() for v in grapple.obj.data.vertices]
        gswept = gpts + _rotate_points(gpts, Vector(grapple.pivot), Vector((-1, 0, 0)), 90.0) \
            + _rotate_points(gpts, Vector(grapple.pivot), Vector((-1, 0, 0)), 150.0)
        families.append(_Family(
            f"Grapple_{tag}", [grapple], grapple.pivot, (-1.0, 0.0, 0.0), GRAPPLE_TARGET, 150.0,
            [("coque (quille, chape, tubes)", hull_near(gswept, 0.02))],
        ))

    canopy = parts["Canopy"]
    cpts = [v.co.copy() for v in canopy.obj.data.vertices]
    cswept = cpts + _rotate_points(cpts, Vector(canopy.pivot), Vector((-1, 0, 0)), 80.0) \
        + _rotate_points(cpts, Vector(canopy.pivot), Vector((-1, 0, 0)), 40.0)
    families.append(_Family(
        "Canopy", [canopy], canopy.pivot, (-1.0, 0.0, 0.0), CANOPY_TARGET, 80.0,
        [("coque (puits, dosseret, arete)", hull_near(cswept, 0.02)),
         ("Airbrake_L", part_near("Airbrake_L", cswept, 0.02)),
         ("Airbrake_R", part_near("Airbrake_R", cswept, 0.02))],
    ))

    return [_sweep_family(f) for f in families]


# ==========================================================================
# Audit du .glb livre : UV comptees, aires, densites, axes et signes
# ==========================================================================


def _tri_area(pts, tri) -> float:
    a, b, c = (Vector(pts[i]) for i in tri)
    return (b - a).cross(c - a).length * 0.5


def _audit(path: str) -> dict:
    prims = ak.glb_primitives(path)
    by_node: dict[str, dict] = {}
    area_by_mat: dict[str, float] = {}
    uv_missing: list[str] = []
    zones = {"coque (TEX-0017)": ([], [], []), "AA_Greeble coque (TEX-0018)": ([], [], []),
             "tuyeres + petales (TEX-0019)": ([], [], [])}
    for prim in prims:
        node = prim["node"]
        entry = by_node.setdefault(node, {"triangles": 0, "parent": prim["parent"],
                                          "world": prim["world"], "translation": prim["translation"],
                                          "positions": [], "indices": []})
        entry["triangles"] += len(prim["indices"])
        if prim["uvs"] is None:
            uv_missing.append(f"{node}/{prim['material']}")
        for tri in prim["indices"]:
            area_by_mat[prim["material"]] = area_by_mat.get(prim["material"], 0.0) + _tri_area(prim["positions"], tri)
        if node.startswith("Nozzle_") or node.startswith("Petal_"):
            zone = None if prim["material"] == "AA_Emissive_Engine" else "tuyeres + petales (TEX-0019)"
        elif prim["material"] == "AA_Greeble":
            zone = "AA_Greeble coque (TEX-0018)"
        elif prim["material"] in ("AA_Hull", "AA_Panel", "AA_Trim", "AA_Marking_Red"):
            zone = "coque (TEX-0017)"
        else:
            zone = None
        if zone and prim["uvs"] is not None:
            pts, uvs, tris = zones[zone]
            base = len(pts)
            pts.extend(prim["positions"])
            uvs.extend(prim["uvs"])
            tris.extend((a + base, b + base, c + base) for a, b, c in prim["indices"])
        # pour les signes : garder la geometrie locale du nœud
        off = len(entry["positions"])
        entry["positions"].extend(prim["positions"])
        entry["indices"].extend((a + off, b + off, c + off) for a, b, c in prim["indices"])

    density = {zone: ak.texel_density(*data) for zone, data in zones.items()}
    trim_by_node: dict[str, float] = {}
    for prim in prims:
        if prim["material"] in ("AA_Trim", "AA_Emissive_Engine", "AA_Marking_Red"):
            key = f"{prim['node']}/{prim['material']}"
            trim_by_node[key] = trim_by_node.get(key, 0.0) + sum(
                _tri_area(prim["positions"], t) for t in prim["indices"])
    total_area = sum(area_by_mat.values())
    return {"nodes": by_node, "area_by_mat": area_by_mat, "total_area": total_area,
            "uv_missing": uv_missing, "primitives": len(prims), "density": density,
            "accent_by_node": trim_by_node}


def _godot_axis(author_axis) -> tuple[float, float, float]:
    """(x, y, z)_auteur -> (-x, z, y)_Godot : la chaine d'axes d'`export_hull`,
    appliquee a un VECTEUR (rotation rigide, le sens de rotation est conserve)."""
    x, y, z = author_axis
    return (-x, z, y)


def _sign_probe(node: dict, axis: tuple[float, float, float], probe) -> str:
    """Tourne le nœud de +5 deg autour de `axis` (repere Godot, origine = pivot)
    et rend ce que `probe(avant, apres)` conclut. C'est le signe MESURE."""
    pts = [Vector(p) for p in node["positions"]]
    rot = Matrix.Rotation(math.radians(5.0), 3, Vector(axis))
    after = [rot @ p for p in pts]
    return probe(pts, after)


def _print_axes_and_signs(audit: dict) -> list[str]:
    """Pour chaque famille : axe Godot et signe qui OUVRE, lus sur le .glb."""
    nodes = audit["nodes"]
    lines: list[str] = []

    def far_along(pts, key):
        return max(pts, key=key)

    # Ailes : le bout (|x| max) doit reculer (+z Godot) quand la fleche s'ouvre.
    for tag in ("L", "R"):
        node = nodes[f"Wing_{tag}"]
        tip_index = max(range(len(node["positions"])), key=lambda i: abs(node["positions"][i][0]))

        def probe(before, after, i=tip_index):
            return "recule (+z)" if after[i].z > before[i].z else "avance (-z)"
        verdict = _sign_probe(node, (0.0, 1.0, 0.0), probe)
        sign = "+" if "recule" in verdict else "-"
        lines.append(f"Wing_{tag}: axe Godot (0, 1, 0), rotation {sign} = fleche (le bout {verdict})")
    for tag in ("L", "R"):
        node = nodes[f"Flap_{tag}"]
        te = max(range(len(node["positions"])), key=lambda i: node["positions"][i][2])

        def probe(before, after, i=te):
            return "monte (+y)" if after[i].y > before[i].y else "descend (-y)"
        verdict = _sign_probe(node, (1.0, 0.0, 0.0), probe)
        lines.append(f"Flap_{tag}: axe Godot (1, 0, 0), rotation + : le bord de fuite {verdict}")
    for tag in ("L", "R"):
        node = nodes[f"Nozzle_{tag}"]
        # Le pivot est au plan des charnieres (z local ~ 0, l'arriere du corps) :
        # on sonde le COL (les 10 % de sommets les plus en avant), dont le
        # deplacement est l'oppose de celui de la sortie.
        order = sorted(range(len(node["positions"])), key=lambda i: node["positions"][i][2])
        neck = order[: max(1, len(order) // 10)]

        def probe(before, after, ids=neck):
            dx = sum(after[i].x - before[i].x for i in ids) / len(ids)
            return "vers +x (tribord)" if dx < 0.0 else "vers -x (babord)"
        verdict = _sign_probe(node, (0.0, 1.0, 0.0), probe)
        lines.append(f"Nozzle_{tag}: lacet, axe Godot (0, 1, 0), rotation + : la sortie va {verdict} "
                     "(sonde sur le col, qui va a l'oppose)")
        # petales : axe = Z x radial, radial = position du petale dans le repere de la tuyere
        for p in range(NOZZLE_PETALS):
            pn = nodes[f"Petal_{tag}_{p:02d}"]
            rx, ry, _rz = pn["translation"]
            rl = math.hypot(rx, ry)
            radial = (rx / rl, ry / rl, 0.0)
            axis = (-radial[1], radial[0], 0.0)      # Z x radial
            far = max(range(len(pn["positions"])), key=lambda i: pn["positions"][i][2])

            def probe(before, after, i=far, r=radial):
                d0 = before[i].x * r[0] + before[i].y * r[1]
                d1 = after[i].x * r[0] + after[i].y * r[1]
                return "s'ecarte" if d1 > d0 else "rentre"
            verdict = _sign_probe(pn, axis, probe)
            if p in (0, 3, 6, 9):
                lines.append(
                    f"Petal_{tag}_{p:02d}: radial ({radial[0]:+.3f}, {radial[1]:+.3f}, 0), "
                    f"axe = Z x radial ({axis[0]:+.3f}, {axis[1]:+.3f}, 0), rotation + : le petale {verdict}"
                )
            elif verdict != "s'ecarte":
                lines.append(f"Petal_{tag}_{p:02d}: ATTENTION, rotation + autour de Z x radial : le petale {verdict}")
    for family, what, key_far in (("Airbrake", "le bord arriere", lambda p: p[2]),
                                  ("Intake", "le bord arriere", lambda p: p[2])):
        for tag in ("L", "R"):
            node = nodes[f"{family}_{tag}"]
            far = max(range(len(node["positions"])), key=lambda i: key_far(node["positions"][i]))

            def probe(before, after, i=far):
                return "monte (+y)" if after[i].y > before[i].y else "descend (-y)"
            verdict = _sign_probe(node, (1.0, 0.0, 0.0), probe)
            lines.append(f"{family}_{tag}: axe Godot (1, 0, 0), rotation + : {what} {verdict}")
    for side, tag in ((ak.PORT, "L"), (ak.STARBOARD, "R")):
        node = nodes[f"Rudder_{tag}"]
        _pv, axis_author = _rudder_axis(side)
        axis = _godot_axis(tuple(axis_author))
        te = max(range(len(node["positions"])), key=lambda i: node["positions"][i][2])

        def probe(before, after, i=te):
            return "vers -x (babord)" if after[i].x < before[i].x else "vers +x (tribord)"
        verdict = _sign_probe(node, axis, probe)
        lines.append(f"Rudder_{tag}: axe Godot ({axis[0]:+.4f}, {axis[1]:+.4f}, {axis[2]:+.4f}), "
                     f"rotation + : le bord de fuite va {verdict}")
    for tag in ("L", "R"):
        node = nodes[f"Grapple_{tag}"]
        tip = max(range(len(node["positions"])), key=lambda i: node["positions"][i][2])

        def probe(before, after, i=tip):
            return "descend (-y)" if after[i].y < before[i].y else "monte (+y)"
        verdict = _sign_probe(node, (1.0, 0.0, 0.0), probe)
        lines.append(f"Grapple_{tag}: axe Godot (1, 0, 0), rotation + : la pointe {verdict}")
    node = nodes["Canopy"]
    front = min(range(len(node["positions"])), key=lambda i: node["positions"][i][2])

    def probe(before, after, i=front):
        return "monte (+y)" if after[i].y > before[i].y else "descend (-y)"
    verdict = _sign_probe(node, (1.0, 0.0, 0.0), probe)
    lines.append(f"Canopy: axe Godot (1, 0, 0), rotation + : l'avant {verdict}")
    return lines


# ==========================================================================
# Assemblage
# ==========================================================================

EXPECTED_MOVING_NODES = 2 + 2 + 2 + 2 * NOZZLE_PETALS + 2 + 2 + 2 + 2 + 1   # 39


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_VANGUARD)

    details = build_details()
    dbm = bmesh.new()
    dbm.from_mesh(details.data)
    _grapple_mounts(dbm)
    dbm.to_mesh(details.data)
    dbm.free()
    ship = ak.join_objects([build_hull(), details], "Specter9C")
    _finish(ship, bevel=0.0030, segments=2)
    if ship.data.validate(verbose=True):
        print("  ⚠️ validate() a CORRIGE le maillage principal (voir les lignes ci-dessus)")

    parts: dict[str, ak.MovingPart] = {}
    for side in (ak.PORT, ak.STARBOARD):
        for builder in (build_wing, build_flap, build_airbrake, build_intake,
                        build_rudder, build_grapple):
            part = builder(side)
            _finish(part.obj, bevel=0.0022, segments=2)
            parts[part.obj.name] = part
        nozzle = build_nozzle(side)
        _finish(nozzle.obj, bevel=0.0020, segments=3)
        parts[nozzle.obj.name] = nozzle
        for p in range(NOZZLE_PETALS):
            petal = build_petal(side, p)
            _finish(petal.obj, bevel=0.0016, segments=3)
            parts[petal.obj.name] = petal
    canopy = build_canopy()
    _finish(canopy.obj, bevel=0.0020, segments=3)
    parts[canopy.obj.name] = canopy

    if len(parts) != EXPECTED_MOVING_NODES:
        raise ak.ContractError(f"{len(parts)} pieces mobiles, {EXPECTED_MOVING_NODES} attendues")

    # --- depliage en ATLAS (ADR-0047) ---------------------------------------
    #
    # ⚠️ REMPLACE LE DEPLIAGE PAR ZONES, ET CE N'EST PAS UN REGLAGE. Le plan d'origine
    # projetait en boite par materiau (coque 2,5 t/m, greeble 4 t/m) et en cylindre sur
    # les tuyeres, pour accueillir trois feuilles REPETABLES — TEX-0017 a TEX-0019.
    # Ces trois demandes n'ont jamais ete commandees, et elles sont desormais caduques :
    # une feuille repetable MULTIPLIE la palette, elle ne peut donc jamais peindre une
    # bande, un filet ni un matricule. La livree demandee par l'operateur exige un
    # albedo, donc un atlas, donc des ilots DISJOINTS — ce que la projection en boite
    # ne produit pas, par construction (elle les fait se recouvrir, volontairement).
    #
    # Le depliage se fait EN UNE FOIS sur la coque et ses 39 pieces mobiles : un seul
    # carre UV, une seule image. Faire autrement donnerait 40 atlas.
    atlas = ak.atlas_unwrap([ship] + [p.obj for p in parts.values()],
                            angle_limit_deg=66.0, margin=0.003)
    print("  " + atlas.render())

    # --- mesures heritees (polaires) ---------------------------------------
    travel = min(_flap_travel_limit(parts["Flap_L"]), _flap_travel_limit(parts["Flap_R"]))
    sweep, reason = _wing_sweep_limit(parts["Wing_L"], parts["Flap_L"])
    gap, gap_where = _glove_clearance(parts["Wing_L"], parts["Flap_L"])

    # --- balayages BVH -------------------------------------------------------
    results = _measure_all(ship, parts)

    ordered = [parts[k] for k in sorted(parts, key=lambda n: (0 if n.startswith("Wing") else
                                                              1 if n.startswith("Flap") else
                                                              2 if n.startswith("Nozzle") else
                                                              3 if n.startswith("Petal") else 4, n))]
    report = ak.export_hull(ship, build_attach_points(), OUTPUT, CONTRACT, parts=ordered)

    problems: list[str] = []
    if report.size[1] < MIN_HEIGHT_Y:
        problems.append(f"hauteur Y = {report.size[1]:.4f} m < plancher {MIN_HEIGHT_Y:.2f} m")
    if sweep < WING_SWEEP_TARGET:
        problems.append(f"fleche admissible (polaire) {sweep:.2f} deg < cible {WING_SWEEP_TARGET} — {reason}")
    if travel < FLAP_TRAVEL_TARGET:
        problems.append(f"debattement de volet (cloison) {travel:.1f} deg < cible {FLAP_TRAVEL_TARGET}")
    if gap < GLOVE_MIN_CLEARANCE:
        problems.append(f"jeu emplanture/aile {gap * 1000:.1f} mm < {GLOVE_MIN_CLEARANCE * 1000:.0f} mm — {gap_where}")

    targets = {"Wing": WING_SWEEP_TARGET, "Flap": FLAP_TRAVEL_TARGET, "Nozzle": NOZZLE_YAW_TARGET,
               "Petal": PETAL_OPEN_TARGET, "Airbrake": AIRBRAKE_TARGET, "Intake": INTAKE_TARGET,
               "Rudder": RUDDER_TARGET, "Grapple": GRAPPLE_TARGET, "Canopy": CANOPY_TARGET}
    print("\n  PLAFONDS MECANIQUES (balayage BVH, pas 1 deg, jeu minimal "
          f"{CLEARANCE_MIN * 1000:.1f} mm) :")
    for res in results:
        family = res["name"].split("_")[0]
        target = targets[family]
        ceiling = res["ceiling"]
        ok = ceiling >= target
        print(f"    {res['name']:<14} plafond {ceiling if ceiling < math.inf else 'aucune butee':>12}"
              f"{' deg' if ceiling < math.inf else ''}  cible {target:>5.1f}  "
              f"{'OK ' if ok else 'ECHEC'}  {res['reason']}")
        if not ok:
            problems.append(f"{res['name']} : plafond {ceiling} deg < cible {target} — {res['reason']}")
        for label, g in sorted(res["gaps_at_target"].items()):
            print(f"        a la cible, jeu vs {label:<28} {g * 1000:+7.1f} mm")
            if g < CLEARANCE_MIN:
                problems.append(f"{res['name']} vs {label} : jeu {g * 1000:+.1f} mm a la cible")
        for label, g in sorted(res["gap_at_rest"].items()):
            if g < CLEARANCE_MIN * 0.6:
                problems.append(f"{res['name']} vs {label} : jeu {g * 1000:+.1f} mm AU REPOS")

    # --- audit du fichier ----------------------------------------------------
    audit = _audit(OUTPUT)
    print(f"\n  AUDIT DU .GLB : {audit['primitives']} primitives, "
          f"TEXCOORD_0 absent sur {len(audit['uv_missing'])}")
    if audit["uv_missing"]:
        problems.append("TEXCOORD_0 absent : " + ", ".join(audit["uv_missing"][:10]))
    total = audit["total_area"]
    print(f"  aire totale {total:.4f} m2 — repartition :")
    caps = {"AA_Trim": 0.04, "AA_Emissive_Engine": 0.03, "AA_Marking_Red": 0.01}
    floors = {"AA_Hull": 0.55, "AA_Panel": 0.12, "AA_Greeble": 0.08}
    for mat in ak.MATERIAL_ORDER:
        share = audit["area_by_mat"].get(mat, 0.0) / total
        flag = ""
        if mat in caps and share > caps[mat]:
            flag = f"  <-- PLAFOND {caps[mat]:.0%} DEPASSE"
            problems.append(f"{mat} = {share:.1%} de l'aire > plafond {caps[mat]:.0%}")
        elif mat in floors and share < floors[mat]:
            flag = f"  (sous la cible {floors[mat]:.0%})"
        print(f"    {mat:<20} {share:6.1%}{flag}")
    print("  accents (or, emissif, rouge) par nœud, m2 :")
    for key, a in sorted(audit["accent_by_node"].items(), key=lambda kv: -kv[1])[:12]:
        print(f"    {key:<32} {a:.4f}")
    print("  densites de texels (valeurs singulieres, sur le .glb) :")
    for zone, d in audit["density"].items():
        if d:
            print(f"    {zone:<32} moyenne {d['tiles_per_m_mean']:.3f} t/m ({d['m_per_tile_mean']:.3f} m/tuile), "
                  f"min {d['tiles_per_m_min']:.3f}, max {d['tiles_per_m_max']:.3f}, "
                  f"anisotropie max {d['anisotropy_max']:.2f}, aire {d['area']:.3f} m2")
    print("  triangles par nœud :")
    for name, node in sorted(audit["nodes"].items(), key=lambda kv: -kv[1]["triangles"]):
        print(f"    {name:<14} {node['triangles']:>7}  parent={node['parent']}")
    print("  AXES ET SIGNES (mesures sur le .glb, +5 deg) :")
    for line in _print_axes_and_signs(audit):
        print(f"    {line}")

    print(f"\n  volets     : plafond de debattement (cloison) {travel:.1f} deg")
    print(f"  ailes      : fleche admissible (polaire) {sweep:.2f} deg — butee : {reason}")
    print(f"  emplanture : jeu vertical minimal {gap * 1000:.1f} mm — {gap_where}")
    for line in _print_root_coverage():
        print("  " + line)
        if "FENTE" in line:
            problems.append("racine d'aile decouverte : " + line)
    _print_silhouette_gaps()

    if problems:
        os.remove(OUTPUT)
        raise ak.ContractError("BRIEF-0098 — build REFUSE :\n" + "\n".join(f"  - {p}" for p in problems))


if __name__ == "__main__":
    main()
