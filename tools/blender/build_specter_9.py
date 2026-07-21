"""build_specter_9.py — coque 3D du Specter-9, chasseur du joueur.

    blender45 -b -P tools/blender/build_specter_9.py

Produit `assets/imported/models/ships/specter_9.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (aucun alea non seede) et s'auto-valide : `ak.export_hull()`
relit le `.glb` produit et echoue bruyamment si la bounding box, le budget de
triangles, les materiaux, le centrage du pivot ou les points d'attache sortent
du contrat.

Reference de design : `assets/reference/concepts/specter_9_concept_sheet.png`.
Les tables de profil ci-dessous sont relevees sur la vue de dessus de cette
planche (normalisees puis mises a l'echelle des cotes imposees par l'ADR-0008).

Repere d'auteur (ADR-0008) : nez -Y, dessus +Z, **babord +X** (cf. aegis_kit).


PASSE DE DETAIL — BRIEF-0031 (ADR-0011)
=======================================
La version precedente lisait comme un jouet en plastique moule : 1 860 triangles
pour tout le fuselage, quatre aplats bleus « peints », 0,41 m d'epaisseur, aucune
ligne de panneau. Cinq leviers ont ete tires, par ordre de rendement :

1. **Epaisseur** : `CROWN` et `BELLY` plafonnaient a +/-0,11 m. Ils montent a
   +0,165 / -0,150. C'est le seul levier qui change la lecture de volume.
2. **Densite de coque** : la section passe de 15 a **39 abscisses**, les stations
   de 33 a 55. Ce n'est pas de la subdivision decorative : ce sont les faces sur
   lesquelles s'appuient les panneaux et les rainures.
3. **Panneaux a deux niveaux** : double `inset_panel` emboite (technique deja
   prouvee par `build_crescent_interceptor.py:597`), jamais appliquee au heros.
   Marche de coque, puis fond bleu enfonce.
4. **Rainures de panneau** : des *paires* de stations serrees (14 mm) et des
   *paires* d'abscisses serrees creent des bandes fines, creusees a 5 mm. Le
   plaquage se lit enfin en dizaines de plaques, comme sur la planche.
5. **Tuyeres** : buse profonde de 0,21 m, anneaux concentriques, et surtout une
   **levre biseautee vers le DESSUS** (l'axe de la buse remonte de 34 mm). Sans
   elle, l'emissif ne vit que sur des faces arriere que la camera de jeu — a 20
   deg de la verticale — ne voit jamais (BRIEF-0026), alors meme que le vaisseau
   est desormais affiche en gros plan de trois quarts arriere sur l'ecran
   d'accueil.

Regle de placement, appliquee partout : **si une surface n'est pas visible depuis
une camera a 20 deg de la verticale, ce qu'on y met n'existe pas.** Le detail est
donc concentre sur le pont (dessus) ; le ventre ne recoit que le strict minimum.
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

CONTRACT = ak.HullContract(
    name="Specter-9",
    width_x=1.75,       # Godot X — INCHANGE (contrat de gameplay : hitbox)
    length_z=2.46,      # Godot Z — INCHANGE
    # BRIEF-0031 vise 0,50-0,55 m. On borne le contrat a la consigne haute et
    # non aux 0,60 d'ADR-0008 : un depassement silencieux vers 0,58 passerait
    # le test tout en sortant de la fourchette demandee.
    max_height_y=0.55,
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
#: Justification au rapport BRIEF-0031 : une tuile couvre 25 cm, soit ~7 tuiles
#: en envergure et ~10 en longueur — la densite de plaques de la planche.
TEXELS_PER_METER = 4.0

HALF_L = CONTRACT.length_z / 2.0   # 1.230 — nez en -Y, poupe en +Y
HALF_W = CONTRACT.width_x / 2.0    # 0.875 — bout d'aile

# ==========================================================================
# Tables de profil, relevees sur la planche de concept
# ==========================================================================

# Demi-envergure de la coque (planform). La double fleche de l'aile delta se
# lit dans la cassure a y = -0.241 : bord d'attaque avant tres fleche (~20 deg
# de l'axe), puis aile externe nettement moins flechee (~40 deg).
# INCHANGE : c'est la silhouette, et le brief interdit d'y toucher.
PLANFORM: list[tuple[float, float]] = [
    (-1.2300, 0.0000),   # pointe du nez
    (-1.0800, 0.0455),
    (-0.9250, 0.0893),
    (-0.8120, 0.1356),
    (-0.6910, 0.1715),
    (-0.5510, 0.2083),
    (-0.4130, 0.2573),
    (-0.3000, 0.3063),
    (-0.2410, 0.3553),   # cassure du bord d'attaque (double fleche)
    (-0.1010, 0.4611),
    (0.0540, 0.5836),
    (0.2190, 0.7053),
    (0.3470, 0.8199),
    (0.4180, 0.8750),    # coin avant du bout d'aile — LARGEUR MAX
    (0.5730, 0.8750),
    (0.7450, 0.8690),    # coin arriere du bout d'aile
    (0.7730, 0.7540),
    (0.7900, 0.6080),
    (0.8020, 0.5100),
    (0.8190, 0.4280),
    (0.8600, 0.2400),    # bord de fuite, culot
]

# Demi-largeur du fuselage central (au-dela : l'aile, mince).
FUSELAGE: list[tuple[float, float]] = [
    (-1.2300, 0.000),
    (-1.0800, 0.038),
    (-0.9250, 0.072),
    (-0.8120, 0.092),
    (-0.6910, 0.112),
    (-0.5510, 0.132),
    (-0.4130, 0.148),
    (-0.2410, 0.163),
    (-0.1010, 0.172),
    (0.0540, 0.182),
    (0.2190, 0.196),
    (0.4180, 0.208),
    (0.5730, 0.216),
    (0.7450, 0.222),
    (0.8600, 0.226),
]

# Hauteur de l'epine dorsale (z du sommet, sur l'axe).
# BRIEF-0031 levier n.1 : le dos passe de 0,114 a 0,165 m. La planche montre un
# appareil epais, dont le fuselage porte un vrai volume mecanique entre les
# tuyeres ; a 0,114 m on avait une plaque a peine bombee.
CROWN: list[tuple[float, float]] = [
    (-1.2300, 0.000),
    (-1.0800, 0.044),
    (-0.9250, 0.080),
    (-0.8120, 0.102),
    (-0.6910, 0.122),
    (-0.5510, 0.136),
    (-0.4130, 0.146),
    (-0.2410, 0.155),
    (0.0540, 0.162),
    (0.2190, 0.165),
    (0.4180, 0.164),
    (0.5730, 0.160),
    (0.7450, 0.154),
    (0.8600, 0.148),
]

# Profondeur du ventre (z du bas, sur l'axe ; valeurs negatives).
BELLY: list[tuple[float, float]] = [
    (-1.2300, 0.000),
    (-1.0800, -0.036),
    (-0.9250, -0.067),
    (-0.8120, -0.086),
    (-0.6910, -0.103),
    (-0.5510, -0.119),
    (-0.4130, -0.131),
    (-0.2410, -0.139),
    (0.0540, -0.147),
    (0.2190, -0.150),
    (0.4180, -0.150),
    (0.5730, -0.147),
    (0.7450, -0.144),
    (0.8600, -0.142),
]

#: Stations longitudinales de base (la premiere est la pointe du nez).
BASE_STATIONS: tuple[float, ...] = (
    -1.2300, -1.1900, -1.1400, -1.0800, -1.0200, -0.9600, -0.9000, -0.8400,
    -0.7800, -0.7200, -0.6600, -0.6000, -0.5400, -0.4700, -0.4000, -0.3300,
    -0.2600, -0.2000, -0.1300, -0.0500, 0.0400, 0.1300, 0.2200, 0.3100,
    0.4000, 0.4700, 0.5400, 0.6100, 0.6800, 0.7450, 0.7900, 0.8250, 0.8600,
)

#: Rainures TRANSVERSALES : centre de la bande, et etendue laterale.
#: "fus" = coeur du fuselage seul (l'aile y est trop mince pour porter une
#: rainure sans degenerer), "all" = toute la largeur.
#: Aucune rainure en avant de y = -0.90 : la coque y fait moins de 25 cm
#: d'envergure, les cellules y sont sub-millimetriques.
#: Chaque centre est pris au MILIEU d'un intervalle de `BASE_STATIONS` : la
#: paire de stations serrees y decoupe deux bandes residuelles de largeur egale.
#: Decale, un centre laisserait une bande de 8 mm — trop mince pour porter quoi
#: que ce soit, et de la geometrie payee pour rien.
LATERAL_SEAMS: tuple[tuple[float, str], ...] = (
    (-0.8700, "fus"),
    (-0.7500, "fus"),
    (-0.5700, "all"),
    (-0.4350, "all"),
    (-0.2300, "all"),
    (-0.0900, "all"),
    (0.0850, "all"),
    (0.2650, "all"),
    (0.4350, "all"),
    (0.6450, "all"),
    (0.7675, "all"),
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
# cette passe sortait une coque de 2,44 m de haut, avec des sommets projetes a
# x = 0,75 m sur une aile qui n'en fait que 0,17 a cette station.
#
# Le retrait ne s'applique qu'au CONTOUR de la zone, pas aux aretes interieures :
# la grandeur a controler est donc la largeur d'un TRONCON CONTIGU de cellules,
# jamais celle d'une cellule isolee. `_cells()` groupe et filtre pour cela.
#
# Trois grandeurs, et non une seule — chacune correspond a une facon distincte
# de replier une zone :
#   * `min_run`  : largeur totale du troncon (le contour se resserre des DEUX
#                  cotes, il faut donc plus de deux retraits) ;
#   * `min_edge` : largeur de la cellule d'EXTREMITE. Une zone de 45 mm dont la
#                  derniere cellule ne fait que 3 mm se retourne quand meme :
#                  c'est cette cellule-la qui absorbe tout le retrait. C'est le
#                  cas qui a produit la deuxieme coque ratee de cette passe ;
#   * `min_band` : hauteur de la bande, meme raisonnement selon Y.
#: Rainures (retrait 1,8 mm).
MIN_RUN_SEAM, MIN_EDGE_SEAM, MIN_BAND_SEAM = 0.0060, 0.0060, 0.0100
#: Panneaux (retrait cumule 15 mm).
MIN_RUN_PLATE, MIN_EDGE_PLATE, MIN_BAND_PLATE = 0.0500, 0.0200, 0.0240


def _stations() -> list[float]:
    """Stations = base + une PAIRE serree par rainure transversale.

    Une rainure a besoin d'une bande de faces etroite : on l'obtient en
    inserant deux stations distantes de 14 mm autour de son centre. La bande
    ainsi creee est identifiee plus tard a sa seule largeur (< 20 mm), ce qui
    evite de trimballer des index fragiles.
    """
    out = list(BASE_STATIONS)
    for y, _ in LATERAL_SEAMS:
        out += [y - SEAM_HALF, y + SEAM_HALF]
    return sorted(out)


STATIONS: list[float] = _stations()

EDGE_H = 0.012      # demi-epaisseur du bord d'aile (tranche de 24 mm)
ANHEDRAL = 0.030    # affaissement du bout d'aile (lu sur la vue arriere)
SPINE_HW = 0.072    # demi-largeur du sillon dorsal

# Verriere : (y, demi-largeur, hauteur au-dessus de son assise). Bulle nettement
# marquee, comme sur la planche : une verriere trop plate disparaissait a 20 deg
# de camera et le chasseur perdait sa lecture de profil.
CANOPY: list[tuple[float, float, float]] = [
    (-0.7900, 0.000, 0.000),
    (-0.7600, 0.032, 0.041),
    (-0.7200, 0.058, 0.079),
    (-0.6700, 0.080, 0.114),
    (-0.6100, 0.093, 0.139),
    (-0.5450, 0.098, 0.150),
    (-0.4800, 0.097, 0.147),
    (-0.4150, 0.092, 0.134),
    (-0.3500, 0.083, 0.109),
    (-0.3000, 0.070, 0.076),
    (-0.2650, 0.052, 0.041),
    (-0.2450, 0.000, 0.000),
]
CANOPY_SINK = 0.018  # assise de la verriere, sous la ligne d'epine

# Tuyeres.
NACELLE_X = 0.235      # ecartement des axes (lu sur la vue arriere)
NACELLE_Z = -0.030     # axes legerement sous le plan de vol
NACELLE_SEGMENTS = 24  # les tuyeres sont le point focal arriere : on les paie rondes

# Profil de revolution de la tuyere : (y, rayon, materiau du segment sortant).
# Le profil s'arrete a la levre exterieure (y = 1.2300, la poupe qui fixe la
# bounding box) ; toute la buse est ensuite construite a la main par
# `_nozzle_bore`, parce qu'elle n'est PAS un solide de revolution : son axe
# remonte de 34 mm pour que l'emissif se voie du dessus.
NACELLE_PROFILE: list[tuple[float, float, str]] = [
    (0.520, 0.000, "AA_Hull"),     # pole avant, noye dans l'aile
    (0.550, 0.075, "AA_Hull"),
    (0.600, 0.115, "AA_Hull"),
    (0.680, 0.136, "AA_Hull"),
    (0.760, 0.142, "AA_Hull"),
    (0.800, 0.143, "AA_Panel"),    # bandeau bleu marine du fuseau
    (0.860, 0.144, "AA_Panel"),
    (0.900, 0.145, "AA_Hull"),
    (0.920, 0.145, "AA_Hull"),
    (0.930, 0.152, "AA_Greeble"),  # 1er anneau concentrique
    (0.955, 0.152, "AA_Greeble"),
    (0.962, 0.145, "AA_Hull"),
    (0.975, 0.145, "AA_Greeble"),
    (0.985, 0.157, "AA_Greeble"),  # collier mecanique
    (1.050, 0.157, "AA_Greeble"),
    (1.060, 0.146, "AA_Greeble"),
    (1.085, 0.146, "AA_Trim"),
    (1.090, 0.152, "AA_Trim"),     # jonc dore
    (1.120, 0.152, "AA_Trim"),
    (1.125, 0.146, "AA_Hull"),
    (1.140, 0.147, "AA_Hull"),
    (1.150, 0.156, "AA_Greeble"),  # 2e anneau concentrique
    (1.168, 0.156, "AA_Greeble"),
    (1.176, 0.150, "AA_Greeble"),
    (1.186, 0.161, "AA_Greeble"),  # levre exterieure
    (1.2150, 0.160, "AA_Greeble"),
    (1.2300, 0.150, "AA_Greeble"),  # bord de sortie — POUPE (fixe la bbox)
]

#: Buse : (y, rayon, decalage vertical de l'axe). L'axe remonte progressivement,
#: de sorte que la couronne emissive forme une vasque INCLINEE VERS LE HAUT.
#: C'est la reponse directe a BRIEF-0026 : a 20 deg de la verticale, une buse
#: purement axiale ne montre rien de son interieur.
NOZZLE_BORE: tuple[tuple[float, float, float], ...] = (
    (1.2300, 0.150, 0.000),   # doit coincider EXACTEMENT avec la fin du lathe
    (1.1940, 0.122, 0.030),   # levre biseautee : ledge quasi horizontale au-dessus
    (1.1500, 0.112, 0.036),
    (1.0800, 0.098, 0.038),   # anneau concentrique interne
    (1.0300, 0.076, 0.038),
    (1.0150, 0.052, 0.038),
)
NOZZLE_FLOOR_Y = 1.0050  # fond lumineux : 0,225 m de profondeur de buse

# Carenage de tuyere : le bossage de coque qui noie l'avant de chaque cylindre
# dans l'aile. Sans lui, les tuyeres ont l'air posees sur un pont plat ; la
# planche montre au contraire des fuseaux integres, dont seule la partie
# arriere (collier, jonc, tuyere) emerge. (y, demi-largeur, hauteur sur l'axe).
FAIRING: list[tuple[float, float, float]] = [
    (0.340, 0.000, 0.000),
    (0.410, 0.082, 0.104),
    (0.480, 0.124, 0.138),
    (0.560, 0.152, 0.158),
    (0.680, 0.170, 0.172),
    (0.800, 0.174, 0.177),
    (0.900, 0.170, 0.172),
    (0.950, 0.154, 0.152),
    (0.980, 0.000, 0.000),
]

# Poutre dorsale arriere, entre les tuyeres : (y, demi-largeur, z haut, z bas).
TAIL_BOOM: list[tuple[float, float, float, float]] = [
    (0.300, 0.084, 0.148, -0.030),
    (0.550, 0.084, 0.168, -0.086),
    (0.800, 0.082, 0.166, -0.140),
    (1.000, 0.078, 0.160, -0.176),
    (1.100, 0.072, 0.152, -0.188),
]

# Longeron ventral (loge le canon) : (y, demi-largeur, profondeur sous le ventre).
STRAKE: list[tuple[float, float, float]] = [
    (-1.0200, 0.048, 0.023),
    (-0.9000, 0.058, 0.032),
    (-0.7000, 0.070, 0.042),
    (-0.4500, 0.086, 0.056),
    (-0.2000, 0.098, 0.072),
    (0.0500, 0.104, 0.086),
    (0.2500, 0.104, 0.090),
    (0.4200, 0.096, 0.076),
    (0.5200, 0.076, 0.044),
]

# Ecartement (a l'axe) des deux tubes du canon ventral. Derive de la coque :
# la culasse des tubes (breech, y ~= -0.89) doit rester SOUS la coque, or la
# demi-envergure du planform y vaut ~0.104 ; on retranche le rayon de levre du
# tube (BARREL_R*1.22 ~= 0.021) -> ~0.083, arrondi a 0.080. La culasse reste
# ainsi ancree sous le nez, les tubes projettent vers l'avant en un twin
# nettement lisible (ecartement 0.160 m, contre 0.052 auparavant, ou les deux
# tirs sortaient superposes). Le brief evoquait ~0.12, mais a cette valeur les
# tubes flottent hors coque au droit de la bouche (demi-largeur du nez ~0.05) ;
# 0.080 reste sous la largeur maximale du longeron ventral STRAKE (0.104).
# Deplacer BARREL_X deplace ENSEMBLE la geometrie des tubes (build_details) et
# les muzzles (build_attach_points) : flash, tube et balle restent alignes.
BARREL_X = 0.080        # ecartement des deux tubes du canon ventral
BARREL_R = 0.017
BARREL_TIP = -1.0550    # pointe des tubes
MUZZLE_Y = -1.0700      # bouche de tir : juste devant les tubes

# Canons additionnels montes sur l'aile (positions laterales, a l'axe).
WING_MUZZLE_X = 0.500   # canon d'aile (power 3) : sur le bord d'attaque, a mi-aile
TIP_MUZZLE_X = 0.800    # pod de bout d'aile (power 5) : sous la largeur max 0.875


# ==========================================================================
# Interpolation des tables
# ==========================================================================


def lerp_table(table: list[tuple[float, float]], y: float) -> float:
    """Interpolation lineaire d'une table (y, valeur), extremites clampees.

    Volontairement lineaire par morceaux : sur une aile delta hard-surface,
    une spline arrondirait les cassures qui font justement la silhouette.
    """
    if y <= table[0][0]:
        return table[0][1]
    if y >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        y0, v0 = table[i]
        y1, v1 = table[i + 1]
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return v0 + (v1 - v0) * t
    return table[-1][1]


def section_params(y: float) -> tuple[float, float, float, float]:
    """(demi-envergure, demi-fuselage, epine, ventre) a la station `y`."""
    w = lerp_table(PLANFORM, y)
    f = min(lerp_table(FUSELAGE, y), w * 0.94)
    return w, f, lerp_table(CROWN, y), lerp_table(BELLY, y)


def _edge_h(crown: float) -> float:
    """Bord d'aile : jamais plus epais que le corps (sinon nez creuse)."""
    return min(EDGE_H, 0.55 * crown) if crown > 1e-6 else 0.0


def z_top(x: float, w: float, f: float, crown: float, belly: float) -> float:
    """Surface superieure : bombe de fuselage, puis aile mince a anhedral."""
    a = abs(x)
    if f > 1e-6 and a <= f:
        return crown * (1.0 - 0.35 * (a / f) ** 2)
    t = (a - f) / max(w - f, 1e-6)
    t = min(max(t, 0.0), 1.0)
    eh = _edge_h(crown)
    shoulder = 0.65 * crown
    return -ANHEDRAL * t * t + (shoulder - eh) * (1.0 - t) ** 1.4 + eh


def z_bot(x: float, w: float, f: float, crown: float, belly: float) -> float:
    a = abs(x)
    if f > 1e-6 and a <= f:
        return belly * (1.0 - 0.35 * (a / f) ** 2)
    t = (a - f) / max(w - f, 1e-6)
    t = min(max(t, 0.0), 1.0)
    eh = _edge_h(crown)
    shoulder = 0.65 * (-belly)
    return -ANHEDRAL * t * t - ((shoulder - eh) * (1.0 - t) ** 1.4 + eh)


# --------------------------------------------------------------------------
# Section transversale : 39 abscisses (contre 15 auparavant)
# --------------------------------------------------------------------------

#: Fractions de la corde d'aile (t = 1 au bord d'aile, t = 0 a l'emplanture).
#: Les PAIRES serrees (0.668/0.640 et 0.212/0.184) delimitent les deux rainures
#: LONGITUDINALES : elles suivent la fleche de l'aile, comme les lignes de
#: panneau rayonnantes de la planche, au lieu de couper droit.
WING_T: tuple[float, ...] = (
    1.000, 0.955, 0.900, 0.800, 0.700,
    0.684, 0.652,          # <- bande de rainure longitudinale A (segment 5)
    0.550, 0.440, 0.330, 0.242,
    0.226, 0.194,          # <- bande de rainure longitudinale B (segment 11)
    0.100, 0.000,          # 14 = emplanture
)
#: Fractions du trajet emplanture -> sillon dorsal.
FUS_U: tuple[float, ...] = (0.34, 0.67, 1.00)
#: Fractions du sillon dorsal -> axe.
SPINE_U: tuple[float, ...] = (0.55, 0.00)


def section_x(w: float, f: float) -> list[float]:
    """Les 39 abscisses d'une section, de babord (+W) a tribord (-W).

    L'echantillonnage suit les lignes structurelles : bord d'aile, aile
    externe/interne, emplanture, flanc de fuselage, sillon dorsal, axe — mais
    trois fois plus finement qu'avant, et avec des paires serrees la ou passent
    les rainures. Les index de segments qui en decoulent servent ensuite a poser
    panneaux et rainures.
    """
    s = min(SPINE_HW, 0.60 * f)
    d = w - f
    half = [f + t * d for t in WING_T]           # 0..14  (14 = f)
    half += [f + (s - f) * u for u in FUS_U]     # 15..17 (17 = s)
    half += [s * u for u in SPINE_U]             # 18..19 (19 = axe)
    return half + [-v for v in reversed(half[:-1])]


#: Nombre d'abscisses (= sommets de la surface superieure d'une section).
N_TOP = len(section_x(1.0, 0.4))          # 39
#: Nombre de segments par surface (superieure ou inferieure).
N_SEG = N_TOP - 1                          # 38 sommets -> index 0..37
RIM_STARBOARD = N_TOP - 1                  # 38
RIM_PORT = 2 * N_TOP - 1                   # 77

#: Index de segment des deux rainures LONGITUDINALES (cote babord).
LONG_SEAM_SEGS: tuple[int, ...] = (5, 11)
#: Segments du sillon dorsal (creuse en tant que tel).
SPINE_SEGS: tuple[int, ...] = (17, 18)
#: Etendue laterale des rainures transversales (voir `LATERAL_SEAMS`).
SEG_SPAN_ALL = tuple(range(1, N_SEG))                 # tout sauf les bords d'aile
SEG_SPAN_FUS = tuple(range(14, N_SEG - 14 + 1))       # coeur du fuselage


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
    w, f, _, _ = section_params(y)
    xs = section_x(w, f)
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


def build_hull() -> tuple[object, dict]:
    bm = bmesh.new()

    rings: list[list] = []
    for y in STATIONS[1:]:
        w, f, crown, belly = section_params(y)
        xs = section_x(w, f)
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
        ak.inset_panel(bm, faces, "AA_Hull", thickness=0.006, depth=-0.005)
        ak.inset_panel(bm, faces, material, thickness=0.009, depth=-0.006)

    # ---------------------------------------------------------------------
    # 1. Elements identitaires : ils ont priorite sur tout le reste.
    # ---------------------------------------------------------------------

    # --- puits de verriere : bordure doree, cuve sombre (cf. planche) -----
    well = pick(-0.800, -0.240, both(15, 16, 17, 18))
    border = ak.inset_panel(bm, well, "AA_Greeble", thickness=0.012, depth=-0.016)
    ak.set_material(border, "AA_Trim")

    # --- sillon dorsal creuse : avant du nez, puis toute la poutre -------
    ak.inset_panel(
        bm, pick(-1.100, -0.810, both(*SPINE_SEGS)),
        "AA_Greeble", thickness=0.005, depth=-0.016,
    )
    ak.inset_panel(
        bm, pick(-0.220, 0.845, both(*SPINE_SEGS)),
        "AA_Greeble", thickness=0.006, depth=-0.024,
    )

    # --- bouts d'aile : coiffe doree + marquage rouge --------------------
    ak.set_material(pick(0.420, 0.520, both(0)), "AA_Trim")
    ak.set_material(pick(0.520, 0.630, both(0)), "AA_Marking_Red")
    ak.set_material(pick(0.630, 0.750, both(0)), "AA_Trim")
    ak.set_material(pick_rim(0.420, 0.750), "AA_Trim")

    # --- coiffes dorees de bord d'attaque avant (deux marques symetriques)
    ak.set_material(pick(-0.870, -0.750, both(0)), "AA_Trim")
    ak.set_material(pick_rim(-0.870, -0.750), "AA_Trim")

    # ---------------------------------------------------------------------
    # 2. Rainures LONGITUDINALES. Posees AVANT les panneaux : elles sont la
    #    trame du plaquage, les panneaux viennent s'y appuyer. Le filtre de
    #    largeur les eteint tout seul la ou l'aile est trop mince.
    # ---------------------------------------------------------------------
    for seg in sorted(ALL_LONG_SEAMS):
        ak.inset_panel(
            bm,
            cells(-1.200, 0.845, (seg,), min_run=MIN_RUN_SEAM,
                  min_edge=MIN_EDGE_SEAM, min_band=MIN_BAND_SEAM),
            "AA_Hull",
            thickness=SEAM_T,
            depth=SEAM_D,
        )

    # ---------------------------------------------------------------------
    # 3. Panneaux bleu profond, a deux niveaux (aplats de la planche).
    # ---------------------------------------------------------------------
    for y0, y1, js in (
        (-1.100, -0.900, both(9, 10, 12, 13)),   # flancs de nez
        (-0.900, -0.500, both(9, 10, 12, 13, 14)),  # epaules, autour du cockpit
        (-0.520, -0.150, both(2, 3, 4)),         # aile avant, mi-corde
        (-0.280, 0.400, both(0, 1)),             # lisere de bord d'attaque externe
        (-0.100, 0.500, both(3, 4, 6, 7)),       # grand chevron d'aile externe
        (0.300, 0.560, both(9, 10, 12, 13)),     # aile interne arriere
        (0.550, 0.800, both(7, 8, 9, 10)),       # emplanture arriere
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
    # 4. Rainures TRANSVERSALES : ce qui manquait le plus. Elles decoupent
    #    les grandes plages blanches restantes en plaques, et se scindent
    #    d'elles-memes autour des panneaux deja creuses.
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
    ak.set_material(pick(-1.050, 0.845, both(*SPINE_SEGS), "bot"), "AA_Greeble")
    plate(
        cells(0.000, 0.600, both(3, 4, 7, 8), "bot", min_run=MIN_RUN_PLATE,
              min_edge=MIN_EDGE_PLATE, min_band=MIN_BAND_PLATE, skip_seams=True),
        "AA_Panel",
    )

    obj = ak.new_object("Specter9_Hull", bm)
    return obj, {}


# ==========================================================================
# Sous-ensembles (verriere, tuyeres, poutre, canon, greebles)
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


DOME_ARC = 9  # points d'arc d'une section de dome (verriere, carenage)


def _dome(bm, sections, center_x, base_z, material: str) -> list[list]:
    """Demi-coque bombee, posee sur une assise plane : verriere et carenages.

    `sections` : (y, demi-largeur, hauteur au-dessus de l'assise). Une section
    de demi-largeur nulle est une pointe. `base_z` : callable(y) -> z d'assise.
    Le fond (la corde d'assise) est ferme mais reste noye dans la coque.
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
    """Buse profonde a levre biseautee VERS LE HAUT.

    Le probleme resolu ici est de visibilite, pas de style. Une buse coaxiale
    n'expose son emissif que vers l'arriere ; or la camera de jeu regarde a 20
    deg de la verticale et l'ecran d'accueil cadre le vaisseau de trois quarts
    arriere. En remontant l'axe de la buse de 38 mm sur 0,22 m de profondeur, la
    couronne emissive devient une vasque dont la moitie haute est quasi
    horizontale : elle se lit a la verticale comme de l'arriere.
    """
    rings = [_circle(bm, y, r, cx, cz + dz) for y, r, dz in NOZZLE_BORE]
    for i in range(len(rings) - 1):
        ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Emissive_Engine")
    floor = bm.verts.new((cx, NOZZLE_FLOOR_Y, cz + NOZZLE_BORE[-1][2]))
    ak.fan_to_point(bm, rings[-1], floor, "AA_Emissive_Engine")


def _deck_z(x: float, y: float) -> float:
    """Cote de la surface superieure de coque au point (x, y)."""
    return z_top(x, *section_params(y))


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
    # On les prend sur les faces du dome (aucun triangle supplementaire) :
    # arcs k = 0 et k = 7 pour les rails, k = 3/4 pour la nervure d'axe.
    for band in canopy_bands:
        ak.set_material([band[k] for k in (0, DOME_ARC - 2) if band[k]], "AA_Greeble")
    for band in canopy_bands[3:6]:
        ak.set_material([band[k] for k in (3, 4) if band[k]], "AA_Greeble")

    # Cadre en RELIEF autour du puits : deux longerons dores suivant le contour
    # de la verriere, plus une traverse avant et une traverse arriere. C'est ce
    # bourrelet qui donne au cockpit son epaisseur en vue de dessus.
    for sx in (ak.PORT, ak.STARBOARD):
        rail = []
        for y, hw, _h in CANOPY[1:-1]:
            z0 = canopy_base(y)
            rail.append((y, hw + 0.013, z0 - 0.004, z0 + 0.022))
        rings = [
            ak.add_ring(
                bm,
                [
                    (sx * (hw + 0.009), y, hi),
                    (sx * (hw - 0.005), y, hi),
                    (sx * (hw - 0.005), y, lo),
                    (sx * (hw + 0.009), y, lo),
                ],
            )
            for y, hw, lo, hi in rail
        ]
        for i in range(len(rings) - 1):
            ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Trim")
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Trim")
        ak.cap_ring(bm, rings[-1], "AA_Trim")

    for y, hw, tall in ((-0.7750, 0.046, 0.020), (-0.2600, 0.062, 0.024)):
        z0 = canopy_base(y)
        ak.add_box(bm, (0.0, y, z0 + tall * 0.5), (hw * 2.0, 0.022, tall), "AA_Trim")

    # ---------------------------------------- tuyeres et leurs carenages de coque
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
        # aplat bleu sur le dos du carenage (cf. planche), borde de deux
        # rainures longitudinales prises sur les arcs voisins.
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
        _strip(
            bm,
            [(0.620, 0.128, 0.140), (0.760, 0.140, 0.152), (0.900, 0.132, 0.144)],
            0.011,
            "AA_Emissive_Engine",
            center_x=sign * (NACELLE_X + 0.098),
        )
        # couronne emissive posee sur le DOS de la levre : deuxieme temoin de
        # poussee lisible a la verticale, independamment de la buse.
        ak.add_box(
            bm,
            (sign * NACELLE_X, 1.1680, NACELLE_Z + 0.150),
            (0.070, 0.026, 0.014),
            "AA_Emissive_Engine",
        )

    # ------------------------------------------------- poutre dorsale arriere
    boom = [_rect_ring(bm, y, hw, lo, hi) for y, hw, hi, lo in TAIL_BOOM]
    for i in range(len(boom) - 1):
        ak.bridge_rings(bm, boom[i], boom[i + 1], "AA_Greeble")
    ak.cap_ring(bm, list(reversed(boom[0])), "AA_Greeble")
    ak.cap_ring(bm, boom[-1], "AA_Greeble")

    # jonc dore encadrant la poupe (lisible sur la vue arriere)
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * 0.078, 1.040, -0.040), (0.016, 0.120, 0.210), "AA_Trim")
    ak.add_box(bm, (0.0, 1.040, -0.180), (0.150, 0.120, 0.018), "AA_Trim")

    # bandeau lumineux de l'epine dorsale (sillon), puis barre verticale de poupe
    _strip(
        bm,
        [(-1.070, 0.036, 0.046), (-0.960, 0.056, 0.066), (-0.850, 0.072, 0.082)],
        0.014,
        "AA_Emissive_Engine",
    )
    _strip(
        bm,
        [(-0.190, 0.122, 0.134), (-0.050, 0.128, 0.140), (0.040, 0.131, 0.143)],
        0.018,
        "AA_Emissive_Engine",
    )
    _strip(
        bm,
        [(0.340, 0.160, 0.172), (0.700, 0.160, 0.172), (1.040, 0.150, 0.162)],
        0.020,
        "AA_Emissive_Engine",
    )
    ak.add_box(bm, (0.0, 1.104, -0.040), (0.030, 0.020, 0.170), "AA_Emissive_Engine")

    # ------------------------------------------------ longeron ventral + canon
    strake = []
    for y, hw, depth in STRAKE:
        belly = lerp_table(BELLY, y)
        strake.append(_rect_ring(bm, y, hw, belly - depth, belly + 0.006, taper=0.86))
    for i in range(len(strake) - 1):
        ak.bridge_rings(bm, strake[i], strake[i + 1], "AA_Greeble")
    ak.cap_ring(bm, list(reversed(strake[0])), "AA_Greeble")
    ak.cap_ring(bm, strake[-1], "AA_Greeble")

    # deux tubes debouchant sous le nez
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

    # platine doree ventrale + marquage rouge (visibles sur la vue de profil)
    plate_z = lerp_table(BELLY, 0.200) - 0.090
    ak.add_box(bm, (0.0, 0.200, plate_z + 0.006), (0.150, 0.320, 0.014), "AA_Trim")
    ak.add_box(bm, (0.0, 0.080, plate_z + 0.002), (0.070, 0.045, 0.016),
               "AA_Marking_Red")

    # --------------------------------------- bloc mecanique dorsal (planche)
    # La planche montre, en avant des tuyeres, un bloc technique encastre dans
    # le sillon : platine sombre, deux joues dorees, hublot cyan. C'est le point
    # de mire de la vue de dessus — on le paie en detail.
    bay_z = lerp_table(CROWN, 0.185) - 0.020
    ak.add_box(bm, (0.0, 0.185, bay_z + 0.030), (0.106, 0.280, 0.060), "AA_Greeble")
    ak.add_box(bm, (0.0, 0.185, bay_z + 0.062), (0.074, 0.236, 0.016), "AA_Greeble")
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * 0.064, 0.185, bay_z + 0.034),
                   (0.016, 0.300, 0.050), "AA_Trim")
        ak.add_box(bm, (sx * 0.040, 0.072, bay_z + 0.072),
                   (0.018, 0.070, 0.012), "AA_Emissive_Engine")
    ak.add_box(bm, (0.0, 0.150, bay_z + 0.072), (0.026, 0.130, 0.012),
               "AA_Emissive_Engine")
    ak.add_box(bm, (0.0, 0.300, bay_z + 0.068), (0.058, 0.036, 0.020), "AA_Marking_Red")

    # --------------------------------------------- petits bandeaux cyan du pont
    # Reperes d'echelle, tous poses sur des faces VUES DU DESSUS.
    for sx in (ak.PORT, ak.STARBOARD):
        for y, x, length in (
            (-0.430, 0.300, 0.070),
            (-0.150, 0.470, 0.080),
            (0.180, 0.560, 0.080),
            (0.520, 0.420, 0.070),
        ):
            ak.add_box(
                bm,
                (sx * x, y, _deck_z(sx * x, y) + 0.004),
                (0.016, length, 0.010),
                "AA_Emissive_Engine",
            )

    # ---------------------------------------------------------------- greebles
    # Une douzaine de boites auparavant, ~60 desormais, TOUTES sur le pont ou
    # sur le dos des fuseaux : les flancs verticaux et les faces arriere ne sont
    # pas vus par la camera de jeu, y semer des greebles serait du gaspillage.
    ak.greeble_strip(
        bm, (0.0, -0.150, bay_z), (0.0, 0.030, bay_z), count=5, seed=rng_seed,
        size_range=(0.014, 0.030), height_range=(0.006, 0.014),
    )
    for k, sx in enumerate((ak.PORT, ak.STARBOARD)):
        base = rng_seed + 17 * (k + 1)
        # bandeau d'emplanture arriere (le plus visible en gros plan d'accueil)
        _deck_greebles(bm, sx * 0.320, 0.540, 0.800, 6, base + 1,
                       size_range=(0.018, 0.038))
        # rampe technique le long du sillon
        _deck_greebles(bm, sx * 0.150, -0.120, 0.320, 6, base + 2,
                       size_range=(0.014, 0.028), height_range=(0.005, 0.012))
        # aile externe, entre les deux rainures longitudinales
        _deck_greebles(bm, sx * 0.520, 0.080, 0.420, 5, base + 3,
                       size_range=(0.016, 0.032), height_range=(0.005, 0.011))
        # epaule avant, de part et d'autre du cockpit
        _deck_greebles(bm, sx * 0.230, -0.760, -0.520, 4, base + 4,
                       size_range=(0.013, 0.026), height_range=(0.005, 0.010))
        # flancs de nez
        _deck_greebles(bm, sx * 0.075, -1.060, -0.900, 3, base + 5,
                       size_range=(0.011, 0.021), height_range=(0.004, 0.009))
        # dos du carenage de tuyere
        ak.greeble_strip(
            bm,
            (sx * (NACELLE_X - 0.052), 0.620, 0.150),
            (sx * (NACELLE_X - 0.052), 0.900, 0.150),
            count=5,
            seed=base + 6,
            size_range=(0.016, 0.030),
            height_range=(0.006, 0.014),
        )
        # bout d'aile, en avant de la coiffe doree
        _deck_greebles(bm, sx * 0.760, 0.470, 0.680, 4, base + 7,
                       size_range=(0.014, 0.026), height_range=(0.004, 0.009))

    return ak.new_object("Specter9_Details", bm)


def _barrel_z() -> float:
    """Axe des tubes du canon : centre sur la section du longeron ventral."""
    y = -1.020
    hw, depth = STRAKE[0][1], STRAKE[0][2]
    belly = lerp_table(BELLY, y)
    return (belly - depth + belly + 0.006) * 0.5


# ==========================================================================
# Points d'attache
# ==========================================================================


def _leading_edge_station(half_span: float) -> float:
    """Station `y` du **bord d'attaque** ou la demi-envergure vaut `half_span`.

    On ne parcourt que la branche avant du planform : du nez (`y = -1.230`) au
    coin avant du bout d'aile (`y = 0.418`, largeur maximale). Sur cette branche
    la demi-envergure croit de facon monotone, donc l'inversion est unique.
    Au-dela (branche arriere, bord de fuite) la meme demi-largeur se retrouve :
    on s'arrete avant pour ne pas y basculer.
    """
    tip_y = _tip_front_station()
    for i in range(len(PLANFORM) - 1):
        y0, w0 = PLANFORM[i]
        y1, w1 = PLANFORM[i + 1]
        if y1 > tip_y:  # on a atteint le coin avant : au-dela c'est le culot
            break
        if w0 <= half_span <= w1:
            t = (half_span - w0) / (w1 - w0)
            return y0 + (y1 - y0) * t
    raise ak.ContractError(
        f"demi-envergure {half_span} hors du bord d'attaque du planform"
    )


def _tip_front_station() -> float:
    """Station `y` du coin avant du bout d'aile (premiere largeur maximale)."""
    return max(PLANFORM, key=lambda p: p[1])[0]


def build_attach_points() -> list:
    """Positions **derivees de la geometrie**, jamais devinees.

    Les offsets de tir et de trainee du controleur joueur sont lus ici : une
    approximation se verrait a l'ecran. Les sept muzzles mappent l'echelle de
    puissance (spec 9.1) : twin de nez (Muzzle_L/R) des le power 1, canons
    d'aile (Muzzle_Wing_L/R) au power 3, canon d'axe (Muzzle_C) au power 4,
    pods de bout d'aile (Muzzle_Tip_L/R) au power 5.
    """
    points: list = []

    # --- twin de nez : dans l'axe des tubes, juste devant leur pointe. --------
    points += list(ak.attach_pair("Muzzle", BARREL_X, MUZZLE_Y, _barrel_z()))

    # --- canon d'axe central : entre les deux tubes, meme plan de tir. --------
    points.append(ak.attach_point("Muzzle_C", (0.0, MUZZLE_Y, _barrel_z())))

    # --- canons d'aile : sur le bord d'attaque, a la station ou la demi-
    #     envergure vaut WING_MUZZLE_X ; z pris sur la surface superieure d'aile
    #     a cette station (anhedral compris via z_top).
    y_wing = _leading_edge_station(WING_MUZZLE_X)
    z_wing = z_top(WING_MUZZLE_X, *section_params(y_wing))
    points += list(ak.attach_pair("Muzzle_Wing", WING_MUZZLE_X, y_wing, z_wing))

    # --- pods de bout d'aile : au coin avant du bout d'aile (largeur max
    #     0.875), en retrait a x = TIP_MUZZLE_X pour rester sur la coque ; z sur
    #     la surface d'aile a cette station (anhedral marque en bout d'aile).
    y_tip = _tip_front_station()
    z_tip = z_top(TIP_MUZZLE_X, *section_params(y_tip))
    points += list(ak.attach_pair("Muzzle_Tip", TIP_MUZZLE_X, y_tip, z_tip))

    # --- tuyeres : centre du plan de sortie (origine de la trainee). Le z suit
    #     desormais l'axe RELEVE de la buse : la trainee doit sortir du trou
    #     lumineux, pas de la tole en dessous.
    exit_y = NOZZLE_BORE[0][0]
    points += list(
        ak.attach_pair(
            "Engine", NACELLE_X, exit_y - 0.010, NACELLE_Z + NOZZLE_BORE[1][2] * 0.5
        )
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
    Le nombre de triangles exportes ne change pas (glTF triangule de toute
    facon) : seule la topologie de ces quelques culots change.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(obj.data)
    bm.free()


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_VANGUARD)

    hull, _ = build_hull()
    details = build_details()

    ship = ak.join_objects([hull, details], "Specter9")
    ak.cleanup(ship)
    # Chanfrein a UN segment, plus etroit (3,5 mm) que la moitie du creux des
    # rainures (5 mm) et des panneaux (11 mm) : la marche reste franche.
    # ADR-0011 autorise desormais d'aller a 2 segments ; essaye au rendu, il
    # arrondit les rainures fines au point de les effacer — c'est exactement le
    # defaut « plastique moule » qu'on corrige. On reste donc a 1 segment, ce
    # qui est un choix de LECTURE, pas une contrainte de budget.
    ak.bevel_sharp_edges(ship, width=0.0035, segments=1, angle_deg=34.0)
    ak.shade_smooth_by_angle(ship, angle_deg=34.0)
    _triangulate_ngons(ship)

    # UV par projection en boite (ADR-0011 §2) : support des feuilles de detail
    # repetables en niveaux de gris, appliquees cote Godot. Aucune texture n'est
    # embarquee dans le .glb — seulement les coordonnees.
    ak.box_project_uv(ship, TEXELS_PER_METER)

    ak.export_hull(ship, build_attach_points(), OUTPUT, CONTRACT)


if __name__ == "__main__":
    main()
