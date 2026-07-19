"""build_specter_9.py — coque 3D du Specter-9, chasseur du joueur (BRIEF-0021).

    blender45 -b -P tools/blender/build_specter_9.py

Produit `assets/imported/models/ships/specter_9.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (aucun alea non seede) et s'auto-valide : `ak.export_hull()`
relit le `.glb` produit et echoue bruyamment si la bounding box, le budget de
triangles, les materiaux, le centrage du pivot ou les points d'attache sortent
du contrat.

Reference de design : `assets/source/concepts/specter_9_concept_sheet.png`.
Les tables de profil ci-dessous sont relevees sur la vue de dessus de cette
planche (normalisees puis mises a l'echelle des cotes imposees par l'ADR-0008).

Repere d'auteur (ADR-0008) : nez -Y, dessus +Z, **babord +X** (cf. aegis_kit).
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
# Contrat (ADR-0008, tableau des dimensions imposees)
# ==========================================================================

CONTRACT = ak.HullContract(
    name="Specter-9",
    width_x=1.75,       # Godot X
    length_z=2.46,      # Godot Z
    max_height_y=0.60,  # Godot Y — plafond de lisibilite en vue de dessus
    tri_budget=15_000,
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

HALF_L = CONTRACT.length_z / 2.0   # 1.230 — nez en -Y, poupe en +Y
HALF_W = CONTRACT.width_x / 2.0    # 0.875 — bout d'aile

# ==========================================================================
# Tables de profil, relevees sur la planche de concept
# ==========================================================================

# Demi-envergure de la coque (planform). La double fleche de l'aile delta se
# lit dans la cassure a y = -0.241 : bord d'attaque avant tres fleche (~20 deg
# de l'axe), puis aile externe nettement moins flechee (~40 deg).
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
CROWN: list[tuple[float, float]] = [
    (-1.2300, 0.000),
    (-1.0800, 0.030),
    (-0.9250, 0.055),
    (-0.8120, 0.070),
    (-0.6910, 0.084),
    (-0.5510, 0.094),
    (-0.4130, 0.101),
    (-0.2410, 0.107),
    (0.0540, 0.112),
    (0.2190, 0.114),
    (0.4180, 0.113),
    (0.5730, 0.110),
    (0.7450, 0.106),
    (0.8600, 0.102),
]

# Profondeur du ventre (z du bas, sur l'axe ; valeurs negatives).
BELLY: list[tuple[float, float]] = [
    (-1.2300, 0.000),
    (-1.0800, -0.026),
    (-0.9250, -0.048),
    (-0.8120, -0.062),
    (-0.6910, -0.074),
    (-0.5510, -0.086),
    (-0.4130, -0.094),
    (-0.2410, -0.100),
    (0.0540, -0.106),
    (0.2190, -0.108),
    (0.4180, -0.108),
    (0.5730, -0.106),
    (0.7450, -0.104),
    (0.8600, -0.102),
]

#: Stations longitudinales de la coque (la premiere est la pointe du nez).
STATIONS: list[float] = [
    -1.2300, -1.1900, -1.1400, -1.0800, -1.0200, -0.9600, -0.9000, -0.8400,
    -0.7800, -0.7200, -0.6600, -0.6000, -0.5400, -0.4700, -0.4000, -0.3300,
    -0.2600, -0.2000, -0.1300, -0.0500, 0.0400, 0.1300, 0.2200, 0.3100,
    0.4000, 0.4700, 0.5400, 0.6100, 0.6800, 0.7450, 0.7900, 0.8250, 0.8600,
]

EDGE_H = 0.012      # demi-epaisseur du bord d'aile (tranche de 24 mm)
ANHEDRAL = 0.030    # affaissement du bout d'aile (lu sur la vue arriere)
SPINE_HW = 0.072    # demi-largeur du sillon dorsal

# Verriere : (y, demi-largeur, hauteur au-dessus de son assise). Bulle nettement
# marquee, comme sur la planche : une verriere trop plate disparaissait a 20 deg
# de camera et le chasseur perdait sa lecture de profil.
CANOPY: list[tuple[float, float, float]] = [
    (-0.7900, 0.000, 0.000),
    (-0.7600, 0.032, 0.038),
    (-0.7200, 0.058, 0.073),
    (-0.6700, 0.080, 0.105),
    (-0.6100, 0.093, 0.128),
    (-0.5450, 0.098, 0.138),
    (-0.4800, 0.097, 0.135),
    (-0.4150, 0.092, 0.123),
    (-0.3500, 0.083, 0.100),
    (-0.3000, 0.070, 0.070),
    (-0.2650, 0.052, 0.038),
    (-0.2450, 0.000, 0.000),
]
CANOPY_SINK = 0.018  # assise de la verriere, sous la ligne d'epine

# Tuyeres.
NACELLE_X = 0.235      # ecartement des axes (lu sur la vue arriere)
NACELLE_Z = -0.030     # axes legerement sous le plan de vol
NACELLE_SEGMENTS = 24  # les tuyeres sont le point focal arriere : on les paie rondes

# Profil de revolution de la tuyere : (y, rayon, materiau du segment sortant).
NACELLE_PROFILE: list[tuple[float, float, str]] = [
    (0.520, 0.000, "AA_Hull"),     # pole avant, noye dans l'aile
    (0.550, 0.075, "AA_Hull"),
    (0.600, 0.115, "AA_Hull"),
    (0.680, 0.136, "AA_Hull"),
    (0.800, 0.143, "AA_Hull"),
    (0.920, 0.145, "AA_Hull"),
    (0.955, 0.145, "AA_Greeble"),
    (0.965, 0.157, "AA_Greeble"),  # collier mecanique
    (1.050, 0.157, "AA_Greeble"),
    (1.060, 0.146, "AA_Greeble"),
    (1.085, 0.146, "AA_Trim"),
    (1.090, 0.152, "AA_Trim"),     # jonc dore
    (1.120, 0.152, "AA_Trim"),
    (1.125, 0.146, "AA_Hull"),
    (1.150, 0.147, "AA_Hull"),
    (1.160, 0.160, "AA_Greeble"),  # levre exterieure
    (1.215, 0.159, "AA_Greeble"),
    (1.2300, 0.150, "AA_Greeble"), # bord de sortie — POUPE (bbox)
    (1.2220, 0.118, "AA_Emissive_Engine"),
    (1.2000, 0.110, "AA_Emissive_Engine"),
    (1.1700, 0.102, "AA_Emissive_Engine"),
    (1.1500, 0.098, "AA_Emissive_Engine"),
    (1.1480, 0.000, "AA_Emissive_Engine"),  # fond lumineux de la tuyere
]

# Carenage de tuyere : le bossage de coque qui noie l'avant de chaque cylindre
# dans l'aile. Sans lui, les tuyeres ont l'air posees sur un pont plat ; la
# planche montre au contraire des fuseaux integres, dont seule la partie
# arriere (collier, jonc, tuyere) emerge. (y, demi-largeur, hauteur sur l'axe).
FAIRING: list[tuple[float, float, float]] = [
    (0.360, 0.000, 0.000),
    (0.410, 0.078, 0.088),
    (0.480, 0.120, 0.118),
    (0.560, 0.150, 0.136),
    (0.680, 0.168, 0.150),
    (0.800, 0.172, 0.155),
    (0.900, 0.168, 0.150),
    (0.950, 0.152, 0.132),
    (0.975, 0.000, 0.000),
]

# Poutre dorsale arriere, entre les tuyeres : (y, demi-largeur, z haut, z bas).
TAIL_BOOM: list[tuple[float, float, float, float]] = [
    (0.300, 0.082, 0.100, -0.020),
    (0.550, 0.082, 0.116, -0.060),
    (0.800, 0.080, 0.114, -0.100),
    (1.000, 0.076, 0.110, -0.130),
    (1.100, 0.070, 0.104, -0.140),
]

# Longeron ventral (loge le canon) : (y, demi-largeur, profondeur sous le ventre).
STRAKE: list[tuple[float, float, float]] = [
    (-1.0200, 0.048, 0.022),
    (-0.9000, 0.058, 0.030),
    (-0.7000, 0.070, 0.040),
    (-0.4500, 0.086, 0.052),
    (-0.2000, 0.098, 0.066),
    (0.0500, 0.104, 0.078),
    (0.2500, 0.104, 0.082),
    (0.4200, 0.096, 0.070),
    (0.5200, 0.076, 0.040),
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


def section_x(w: float, f: float) -> list[float]:
    """Les 15 abscisses d'une section, de babord (+W) a tribord (-W).

    L'echantillonnage suit les lignes structurelles : bord d'aile, aile
    externe/interne, emplanture, flanc de fuselage, sillon dorsal, axe. Les
    index de segments qui en decoulent servent ensuite a poser les panneaux.
    """
    s = min(SPINE_HW, 0.60 * f)
    d = w - f
    half = [w, f + 0.85 * d, f + 0.60 * d, f + 0.30 * d, f, (s + f) * 0.5, s, 0.0]
    return half + [-v for v in reversed(half[:-1])]


# Index de face dans une bande produite par `bridge_rings` (ring de 30 verts :
# 15 dessus de babord a tribord, puis 15 dessous de tribord a babord).
N_TOP = 15
RIM_STARBOARD = 14
RIM_PORT = 29


def top_face(j: int) -> int:
    """Index de la face du segment `j` (0..13) sur la surface superieure."""
    return j


def bot_face(j: int) -> int:
    """Index de la face du segment `j` (0..13) sur la surface inferieure."""
    return 28 - j


MIRROR = {j: 13 - j for j in range(14)}


def both(*js: int) -> set[int]:
    """Un ensemble de segments et leurs symetriques (babord + tribord)."""
    out: set[int] = set()
    for j in js:
        out.add(j)
        out.add(MIRROR[j])
    return out


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
    ak.fan_to_point(bm, rings[0], nose, "AA_Hull")
    for i in range(len(rings) - 1):
        bands.append(ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull"))
        band_y.append((STATIONS[i + 1] + STATIONS[i + 2]) * 0.5)
    ak.cap_ring(bm, list(reversed(rings[-1])), "AA_Greeble")

    def pick(y0: float, y1: float, js: set[int], surface="top") -> list:
        """Selectionne les faces d'une zone : intervalle de stations x segments."""
        chooser = top_face if surface == "top" else bot_face
        out = []
        for b, ym in enumerate(band_y):
            if y0 <= ym <= y1:
                for j in js:
                    face = bands[b][chooser(j)]
                    if face is not None and face.is_valid:
                        out.append(face)
        return out

    def pick_rim(y0: float, y1: float) -> list:
        out = []
        for b, ym in enumerate(band_y):
            if y0 <= ym <= y1:
                for idx in (RIM_PORT, RIM_STARBOARD):
                    face = bands[b][idx]
                    if face is not None and face.is_valid:
                        out.append(face)
        return out

    # --- puits de verriere : bordure doree, cuve sombre (cf. planche) -----
    well = pick(-0.800, -0.240, {5, 6, 7, 8})
    border = ak.inset_panel(bm, well, "AA_Greeble", thickness=0.012, depth=-0.014)
    ak.set_material(border, "AA_Trim")

    # --- sillon dorsal creuse : avant du nez, puis toute la poutre -------
    ak.inset_panel(
        bm, pick(-1.100, -0.810, {6, 7}), "AA_Greeble", thickness=0.005, depth=-0.014
    )
    ak.inset_panel(
        bm, pick(-0.220, 0.845, {6, 7}), "AA_Greeble", thickness=0.006, depth=-0.020
    )

    # --- panneaux bleu profond, enfonces (aplats de la planche) ----------
    for y0, y1, js in (
        (-0.900, -0.500, both(3, 4)),   # epaules, de part et d'autre du cockpit
        (-0.280, 0.400, both(0)),       # lisere de bord d'attaque externe
        (-0.100, 0.500, both(1, 2)),    # grand chevron d'aile externe
        (0.550, 0.800, both(2, 3)),     # emplanture arriere
    ):
        # 10 mm de creux : a 6 mm, le biseau mangeait toute la marche et les
        # panneaux avaient l'air peints, pas decoupes.
        ak.inset_panel(
            bm, pick(y0, y1, js), "AA_Panel", thickness=0.010, depth=-0.010
        )

    # --- bouts d'aile : coiffe doree + marquage rouge --------------------
    ak.set_material(pick(0.420, 0.520, both(0)), "AA_Trim")
    ak.set_material(pick(0.520, 0.630, both(0)), "AA_Marking_Red")
    ak.set_material(pick(0.630, 0.750, both(0)), "AA_Trim")
    ak.set_material(pick_rim(0.420, 0.750), "AA_Trim")

    # --- coiffes dorees de bord d'attaque avant (deux marques symetriques)
    ak.set_material(pick(-0.870, -0.750, both(0)), "AA_Trim")
    ak.set_material(pick_rim(-0.870, -0.750), "AA_Trim")

    # --- dessous : quille sombre et panneaux bleus -----------------------
    ak.set_material(pick(-1.050, 0.845, {6, 7}, "bot"), "AA_Greeble")
    ak.inset_panel(
        bm, pick(0.000, 0.600, both(1, 2), "bot"), "AA_Panel",
        thickness=0.010, depth=-0.010,
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


def _strip(bm, samples: list[tuple[float, float, float]], hw: float, material: str):
    """Bandeau lumineux : petit tube rectangulaire suivant (y, z_bas, z_haut)."""
    rings = [_rect_ring(bm, y, hw, lo, hi) for y, lo, hi in samples]
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


def build_details() -> object:
    bm = bmesh.new()
    rng_seed = SEED

    # ---------------------------------------------------------------- verriere
    _dome(bm, CANOPY, 0.0, lambda y: lerp_table(CROWN, y) - CANOPY_SINK, "AA_Glass")

    # ---------------------------------------- tuyeres et leurs carenages de coque
    for sign in (ak.PORT, ak.STARBOARD):
        ak.add_lathe(
            bm,
            NACELLE_PROFILE,
            NACELLE_SEGMENTS,
            center_x=sign * NACELLE_X,
            center_z=NACELLE_Z,
        )
        bands = _dome(
            bm, FAIRING, sign * NACELLE_X, lambda _y: NACELLE_Z, "AA_Hull"
        )
        # aplat bleu sur le dos du carenage (cf. planche)
        for b, (y, _, _) in enumerate(FAIRING[1:-2]):
            if 0.50 <= y <= 0.90:
                ak.set_material(
                    [bands[b][k] for k in (2, 3, 4, 5) if bands[b][k]], "AA_Panel"
                )

    # ------------------------------------------------- poutre dorsale arriere
    boom = [_rect_ring(bm, y, hw, lo, hi) for y, hw, hi, lo in TAIL_BOOM]
    for i in range(len(boom) - 1):
        ak.bridge_rings(bm, boom[i], boom[i + 1], "AA_Greeble")
    ak.cap_ring(bm, list(reversed(boom[0])), "AA_Greeble")
    ak.cap_ring(bm, boom[-1], "AA_Greeble")

    # jonc dore encadrant la poupe (lisible sur la vue arriere)
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * 0.076, 1.040, -0.020), (0.016, 0.120, 0.150), "AA_Trim")
    ak.add_box(bm, (0.0, 1.040, -0.128), (0.150, 0.120, 0.018), "AA_Trim")

    # bandeau lumineux de l'epine dorsale (sillon), puis barre verticale de poupe
    _strip(
        bm,
        [
            (-1.070, 0.028, 0.036),
            (-0.960, 0.041, 0.049),
            (-0.850, 0.052, 0.060),
        ],
        0.014,
        "AA_Emissive_Engine",
    )
    _strip(
        bm,
        [
            (-0.190, 0.086, 0.096),
            (-0.050, 0.089, 0.099),
            (0.040, 0.091, 0.101),
        ],
        0.018,
        "AA_Emissive_Engine",
    )
    _strip(
        bm,
        [
            (0.340, 0.114, 0.122),
            (0.700, 0.113, 0.121),
            (1.040, 0.108, 0.116),
        ],
        0.020,
        "AA_Emissive_Engine",
    )
    ak.add_box(bm, (0.0, 1.104, -0.030), (0.030, 0.020, 0.130), "AA_Emissive_Engine")

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
    plate_z = lerp_table(BELLY, 0.200) - 0.082
    ak.add_box(bm, (0.0, 0.200, plate_z + 0.006), (0.150, 0.320, 0.014), "AA_Trim")
    ak.add_box(bm, (0.0, 0.080, plate_z + 0.002), (0.070, 0.045, 0.016),
               "AA_Marking_Red")

    # --------------------------------------- assemblage du canon, dans le sillon
    bay_z = lerp_table(CROWN, 0.185) - 0.020
    ak.add_box(bm, (0.0, 0.185, bay_z + 0.026), (0.104, 0.260, 0.052), "AA_Greeble")
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * 0.062, 0.185, bay_z + 0.030),
                   (0.014, 0.280, 0.044), "AA_Trim")
    ak.add_box(bm, (0.0, 0.150, bay_z + 0.055), (0.022, 0.120, 0.010),
               "AA_Emissive_Engine")

    # ---------------------------------------------------------------- greebles
    ak.greeble_strip(
        bm, (0.0, -0.150, bay_z), (0.0, 0.030, bay_z), count=4, seed=rng_seed,
        size_range=(0.014, 0.030), height_range=(0.006, 0.014),
    )
    for k, sx in enumerate((ak.PORT, ak.STARBOARD)):
        w0, f0, c0, b0 = section_params(0.660)
        z_surface = z_top(sx * 0.320, w0, f0, c0, b0)
        ak.greeble_strip(
            bm,
            (sx * 0.320, 0.560, z_surface),
            (sx * 0.320, 0.780, z_surface),
            count=5,
            seed=rng_seed + 17 * (k + 1),
            size_range=(0.018, 0.038),
            height_range=(0.005, 0.012),
        )
        # greebles posees sur l'epaule du carenage (et non plus sur le cylindre,
        # desormais noye dedans)
        ak.greeble_strip(
            bm,
            (sx * 0.285, 0.700, 0.116),
            (sx * 0.285, 0.880, 0.116),
            count=3,
            seed=rng_seed + 41 * (k + 1),
            size_range=(0.016, 0.030),
            height_range=(0.006, 0.014),
        )

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

    Les offsets de tir et de trainee du controleur joueur seront lus ici : une
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

    # --- tuyeres : centre du plan de sortie (origine de la trainee). ----------
    exit_y = max(y for y, _, _ in NACELLE_PROFILE)
    points += list(ak.attach_pair("Engine", NACELLE_X, exit_y - 0.010, NACELLE_Z))

    # --- cockpit : centre du volume de verriere. ------------------------------
    y_mid = (CANOPY[0][0] + CANOPY[-1][0]) * 0.5
    peak = max(CANOPY, key=lambda s: s[2])
    z_mid = lerp_table(CROWN, y_mid) - CANOPY_SINK + peak[2] * 0.45
    points.append(ak.attach_point("Cockpit", (0.0, y_mid, z_mid)))

    return points


# ==========================================================================
# Assemblage
# ==========================================================================


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_VANGUARD)

    hull, _ = build_hull()
    details = build_details()

    ship = ak.join_objects([hull, details], "Specter9")
    ak.cleanup(ship)
    # Chanfrein a UN segment, plus etroit (4 mm) que la moitie du creux des
    # panneaux (10 mm) : la marche reste franche. Un biseau a 2 segments
    # arrondissait entierement les panneaux (ils avaient l'air peints) et
    # coutait 5 000 triangles de plus pour un gain nul a la distance de jeu.
    # Le seuil de 34 deg ne prend que les vraies aretes de structure.
    ak.bevel_sharp_edges(ship, width=0.004, segments=1, angle_deg=34.0)
    ak.shade_smooth_by_angle(ship, angle_deg=34.0)

    ak.export_hull(ship, build_attach_points(), OUTPUT, CONTRACT)


if __name__ == "__main__":
    main()
