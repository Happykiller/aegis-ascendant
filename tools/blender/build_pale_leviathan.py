"""build_pale_leviathan.py — coque 3D du Pale Leviathan, boss final (BRIEF-0024).

    blender45 -b -P tools/blender/build_pale_leviathan.py

Produit `assets/imported/models/bosses/pale_leviathan.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (tout alea passe par `random.Random(seed)`, jamais par le
module `random` global) et s'auto-valide : `ak.export_hull()` relit le `.glb`
produit et echoue bruyamment si la bounding box, le budget de triangles, les
materiaux, le centrage du pivot ou les points d'attache sortent du contrat.

Reference de design : `assets/reference/concepts/pale_leviathan_concept_sheet.png`.

Repere d'auteur (ADR-0008) : nez -Y, dessus +Z, **babord +X** (cf. aegis_kit).
La « face menaçante » (le noyau) regarde donc vers -Y.


LE MODELE EST EN PLUSIEURS OBJETS — ce que le kit ne prevoit pas encore
======================================================================
Les quatre phases du boss doivent pouvoir manipuler les pieces separement
(ouvrir la coquille, exposer le noyau, briser une epine). Le brief impose donc
des objets nommes : `Core`, `Shell_Crescent`, `Spike_01..04` — plus `Body`, le
corps dont partent les epines. En glTF, un objet Blender = un noeud = un noeud
Godot : il faut donc exporter 6 maillages, pas un maillage fusionne.

Or `ak.export_hull(hull, attach_points, ...)` n'applique la correction d'axe
qu'a **un seul** maillage (`hull.data.transform(_AXIS_FIX)`) ; les autres objets
de la liste sont traites comme des Empties (seule leur `location` est tournee).

Le kit etant partage et gele pendant cette mission, on ne le modifie pas. On le
contourne de la seule facon qui reste honnete :

  * `Body` est passe comme `hull` — il est choisi pour porter **a lui seul**
    l'etendue longitudinale totale (proue en `Y_MIN`, dard de queue en `Y_MAX`),
    car `export_hull()` compare le Y d'auteur du `hull` au Z du .glb complet ;
  * les cinq autres maillages recoivent explicitement la meme correction d'axe,
    en reutilisant la matrice du kit (`ak._AXIS_FIX`) plutot qu'une copie locale
    qui pourrait deriver, puis sont passes dans la liste `attach_points` — que
    l'exporteur du kit se contente de selectionner. Leur `location` valant
    (0,0,0), la rotation que le kit leur applique est un no-op, et la validation
    d'orientation les ignore (ce sont des noeuds a maillage).

Evolution demandee au kit (signalee, non faite) : `export_hull(parts: list[Object], ...)`.
"""

from __future__ import annotations

import math
import os
import random
import sys

import bmesh
from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402  (doit suivre l'ajout au sys.path)

# ==========================================================================
# Contrat (ADR-0008, tableau des dimensions imposees)
# ==========================================================================

CONTRACT = ak.HullContract(
    name="Pale Leviathan",
    width_x=7.02,       # Godot X
    length_z=8.77,      # Godot Z
    max_height_y=2.50,  # Godot Y — plafond du brief
    tri_budget=25_000,
    required_materials=ak.MATERIAL_ORDER,  # les 7, palette Choeur Nul
    required_attach_points=("Core_Center", "Muzzle_L", "Muzzle_R", "Muzzle_C"),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/bosses/pale_leviathan.glb")

#: Graine maitresse. Toute la variation (ecailles, craquelures du noyau,
#: greebles) en derive. Rejouer le script est byte-identique.
SEED = 481516

HALF_L = CONTRACT.length_z / 2.0   # 4.385 — proue en -Y, dard en +Y
HALF_W = CONTRACT.width_x / 2.0    # 3.510 — pointes d'epines

# ==========================================================================
# Le noyau
# ==========================================================================

CORE_R = 1.05              # rayon du noyau : ~30 % de la largeur, comme la planche
CORE_SEGMENTS = 28         # c'est LA cible du joueur : on la paie ronde
CORE_RINGS = 16
CORE_CRUST_P = 0.42        # part des facettes qui deviennent croute violette
CORE_CRUST_LIFT = 0.028    # relief de la croute (les craquelures glow entre elles)
CORE_CRUST_INSET = 0.030

# ==========================================================================
# Le corps (Body) — porte a lui seul l'etendue longitudinale (cf. en-tete)
# ==========================================================================

BODY_SECTION_N = 14        # sommets par section (pair : dos/ventre alignes)

#: Index de face, dans une bande de `bridge_rings`, par zone de la section.
#: L'angle de la section demarre au dos (+Z) et tourne vers tribord.
BODY_DORSAL = (13, 0)
BODY_STARBOARD = (3, 4)
BODY_VENTRAL = (6, 7)
BODY_PORT = (10, 11)

BODY_STATIONS: list[float] = [
    -4.385, -4.200, -4.000, -3.750, -3.450, -3.150, -2.850, -2.550,
    -2.250, -1.950, -1.700, -1.450, -1.200, -0.950, -0.700, -0.450,
    -0.200, 0.050, 0.300, 0.550, 0.800, 1.050, 1.350, 1.650,
    1.950, 2.250, 2.550, 2.850, 3.150, 3.450, 3.750, 4.050,
    4.250, 4.385,
]

# Demi-largeur du corps. Masse au centre (il porte le noyau), proue en LAME
# large et plate (pas une aiguille : la planche montre un bec blinde), dard
# segmente a l'arriere.
BODY_HW: list[tuple[float, float]] = [
    (-4.385, 0.010), (-4.150, 0.090), (-3.900, 0.200), (-3.600, 0.340),
    (-3.250, 0.500), (-2.900, 0.640), (-2.550, 0.760), (-2.200, 0.860),
    (-1.850, 0.980), (-1.500, 1.120), (-1.050, 1.300), (-0.600, 1.480),
    (-0.150, 1.620), (0.300, 1.660), (0.750, 1.600), (1.200, 1.480),
    (1.650, 1.330), (2.100, 1.150), (2.550, 0.950), (3.000, 0.740),
    (3.450, 0.540), (3.900, 0.320), (4.200, 0.160), (4.385, 0.010),
]

BODY_TOP: list[tuple[float, float]] = [
    (-4.385, 0.010), (-3.900, 0.130), (-3.300, 0.260), (-2.600, 0.360),
    (-1.800, 0.440), (-0.900, 0.500), (0.300, 0.540), (1.200, 0.490),
    (2.100, 0.400), (3.000, 0.290), (3.900, 0.160), (4.385, 0.020),
]

BODY_BOT: list[tuple[float, float]] = [
    (-4.385, -0.010), (-3.900, -0.100), (-3.300, -0.200), (-2.600, -0.280),
    (-1.800, -0.350), (-0.900, -0.400), (0.300, -0.420), (1.200, -0.385),
    (2.100, -0.320), (3.000, -0.240), (3.900, -0.130), (4.385, -0.020),
]

#: Devers lateral de l'axe : le corps n'est pas droit, il serpente. Premiere
#: source d'asymetrie (la planche montre un corps qui vrille).
BODY_BEND: list[tuple[float, float]] = [
    (-4.385, 0.200), (-3.000, 0.140), (-1.500, 0.050), (0.000, 0.000),
    (1.500, -0.080), (3.000, -0.200), (4.385, -0.300),
]

#: Renflement dissymetrique : l'epaule babord est plus lourde a l'avant,
#: l'epaule tribord a l'arriere. Deuxieme source d'asymetrie.
BODY_PORT_MUL: list[tuple[float, float]] = [
    (-4.385, 1.00), (-2.400, 1.10), (-0.600, 1.16), (0.750, 1.06),
    (2.550, 0.94), (4.385, 0.90),
]
BODY_STAR_MUL: list[tuple[float, float]] = [
    (-4.385, 1.00), (-2.400, 0.92), (-0.600, 0.90), (0.750, 1.02),
    (2.550, 1.12), (4.385, 1.10),
]

# Collier blinde autour du noyau (le « joint » de la planche, gros plan bas-gauche).
#
# Deux rangees concentriques de tuiles **tangentielles** (longues le long de
# l'anneau, courtes en radial). Une premiere version faisait des plaques
# radiales pleine largeur : de dessus, l'anneau devenait une roue a rayons, un
# tournesol — tout sauf une carapace. Des tuiles tangentielles qui se recouvrent
# donnent la lecture « ecailles » de la planche.
#
# (rayon interne, rayon externe, z interne, z externe, tuiles, dephasage)
COLLAR_ROWS: tuple[tuple[float, float, float, float, int, float], ...] = (
    (1.44, 1.95, 0.56, 0.40, 22, 0.00),   # rangee externe, posee la premiere
    (1.06, 1.52, 0.78, 0.58, 17, 0.45),   # rangee interne, qui la recouvre
)
COLLAR_Z_BASE = 0.02       # les tuiles plongent dans le corps : pas de flottement
COLLAR_OVERLAP = 1.28

# Deux fourreaux d'arme qui debordent de la proue (les « bras » avant).
POD_X = 1.05
POD_Z = 0.05
POD_PROFILE: list[tuple[float, float, str]] = [
    (-0.550, 0.000, "AA_Greeble"),
    (-0.620, 0.150, "AA_Hull"),
    (-0.900, 0.205, "AA_Hull"),
    (-1.150, 0.212, "AA_Trim"),
    (-1.230, 0.228, "AA_Trim"),     # collier ivoire
    (-1.480, 0.222, "AA_Hull"),
    (-1.560, 0.196, "AA_Panel"),
    (-1.880, 0.178, "AA_Panel"),
    (-1.960, 0.158, "AA_Greeble"),
    (-2.240, 0.142, "AA_Greeble"),
    (-2.300, 0.120, "AA_Emissive_Engine"),
    (-2.340, 0.088, "AA_Emissive_Engine"),
    (-2.345, 0.000, "AA_Emissive_Engine"),   # bouche
]
MUZZLE_Y = -2.395
MUZZLE_C = (0.0, -1.135, 0.060)   # canon axial du noyau, juste devant la sphere

# Aileron ventral (le croc central de la planche).
FIN: list[tuple[float, float, float]] = [
    # (y, demi-epaisseur, z du bord bas)
    (-0.500, 0.130, -0.400),
    (-1.000, 0.120, -0.640),
    (-1.500, 0.100, -0.780),
    (-2.000, 0.070, -0.800),
    (-2.450, 0.040, -0.660),
    (-2.800, 0.018, -0.420),
]

# ==========================================================================
# La coquille en croissant (Shell_Crescent) — l'« anneau incomplet »
# ==========================================================================
#
# Parametree par l'azimut phi (degres) dans le plan XY, mesure depuis babord :
#   phi =   0  -> babord (+X)      phi =  90 -> arriere (+Y)
#   phi = 180  -> tribord (-X)     phi = -90 -> avant  (-Y)
#
# La coquille court de -150 deg (corne avant-tribord) a +80 deg (corne
# arriere-babord) : 230 deg. Les 130 deg manquants ouvrent sur le quadrant
# arriere-tribord, exactement la ou sortent les deux longues epines. C'est
# l'anneau incomplet, et il est ouvert du cote ou le boss est le plus arme.

CR_PHI_A = -150.0
CR_PHI_B = 80.0
CR_OVERLAP = 1.26          # chevauchement angulaire : chaque tuile monte sur la precedente

#: Trois rangees concentriques de tuiles **tangentielles**, qui se recouvrent en
#: radial ET en azimut : c'est la definition meme d'une armure a ecailles.
#: La rangee interne est la plus haute — c'est elle qui *surplombe* le noyau.
#: (radial_lo, radial_hi, tuiles, elevation, minceur, dephasage)
CR_ROWS: tuple[tuple[float, float, int, float, float, float], ...] = (
    (0.22, 1.00, 30, 0.000, 0.62, 0.00),    # externe (posee la premiere, la plus basse)
    (-0.40, 0.30, 26, 0.045, 0.72, 0.37),   # mediane
    (-1.00, -0.32, 22, 0.090, 0.66, 0.68),  # interne : elle passe au-dessus du noyau
)

CR_R: list[tuple[float, float]] = [      # rayon median de la plaque
    (-150, 2.60), (-120, 2.20), (-90, 1.75), (-60, 1.55),
    (-30, 1.70), (0, 2.05), (40, 2.45), (80, 2.70),
]
CR_W: list[tuple[float, float]] = [      # demi-largeur radiale
    (-150, 0.22), (-120, 0.40), (-90, 0.60), (-60, 0.72),
    (-30, 0.70), (0, 0.60), (40, 0.42), (80, 0.24),
]
CR_Z: list[tuple[float, float]] = [      # altitude de la fibre neutre
    (-150, 0.22), (-120, 0.46), (-90, 0.72), (-60, 0.85),
    (-30, 0.86), (0, 0.78), (40, 0.55), (80, 0.28),
]
CR_T: list[tuple[float, float]] = [      # epaisseur du blindage
    (-150, 0.08), (-120, 0.14), (-90, 0.19), (-60, 0.22),
    (-30, 0.22), (0, 0.18), (40, 0.12), (80, 0.07),
]
CR_TILT: list[tuple[float, float]] = [   # devers : le bord interne se souleve
    (-150, 6), (-120, 14), (-90, 22), (-60, 25),
    (-30, 24), (0, 18), (40, 11), (80, 5),
]

#: Tirage des materiaux de plaque. Majorite d'ivoire (« Pale » Leviathan),
#: ponctue d'anthracite et de violet. Tire avec un `random.Random` seede.
CR_PLATE_MATS = (
    "AA_Trim", "AA_Trim", "AA_Trim", "AA_Hull",
    "AA_Trim", "AA_Panel", "AA_Hull", "AA_Trim",
)

# ==========================================================================
# Les quatre bras-epines
# ==========================================================================
#
# Courbes de Bezier quadratiques (racine, controle, pointe) dans le repere
# d'auteur. Aucune paire n'est le miroir d'une autre : longueurs, epaisseurs,
# nombres de vertebres et courbures different. Les deux pointes extremes
# (Spike_01 a tribord, Spike_03 a babord) fixent la largeur imposee de 7,02 m —
# l'enveloppe est equilibree, la silhouette ne l'est pas.

SPIKES: tuple[dict, ...] = (
    {   # tribord-arriere : la plus longue, la plus fine, l'aiguille
        "name": "Spike_01",
        "root": (-1.05, 0.55, 0.05),
        "ctrl": (-2.25, 1.55, 0.34),
        "tip": (-HALF_W, 3.450, -0.100),
        "r0": 0.340, "sides": 10, "vertebrae": 8, "flat": 0.58, "taper": 1.30,
    },
    {   # tribord-lateral : plus courte, trapue, la « pince »
        "name": "Spike_02",
        "root": (-1.35, -0.25, 0.15),
        "ctrl": (-2.40, 0.15, 0.36),
        "tip": (-3.150, 1.150, 0.000),
        "r0": 0.375, "sides": 10, "vertebrae": 5, "flat": 0.66, "taper": 1.15,
    },
    {   # babord-arriere : le bras lourd, tres segmente
        "name": "Spike_03",
        "root": (1.15, 0.60, 0.10),
        "ctrl": (2.30, 1.35, 0.40),
        "tip": (HALF_W, 2.850, -0.050),
        "r0": 0.465, "sides": 10, "vertebrae": 7, "flat": 0.62, "taper": 1.10,
    },
    {   # babord-avant : la faux, seule epine dirigee vers l'avant
        "name": "Spike_04",
        "root": (1.30, -0.45, 0.05),
        "ctrl": (2.35, -1.25, 0.32),
        "tip": (2.550, -2.600, -0.050),
        "r0": 0.395, "sides": 10, "vertebrae": 6, "flat": 0.60, "taper": 1.22,
    },
)

SPIKE_SAMPLES = 5          # stations par vertebre
SPIKE_TIP_R = 0.018
SPIKE_FLARE = 0.17         # relief de la vertebre (ecaille qui recouvre la suivante)


# ==========================================================================
# Interpolation des tables
# ==========================================================================


def lerp_table(table: list[tuple[float, float]], x: float) -> float:
    """Interpolation lineaire d'une table (abscisse, valeur), extremites clampees.

    Lineaire par morceaux, volontairement : une spline arrondirait les cassures
    de plaque qui font justement la silhouette hard-surface.
    """
    if x <= table[0][0]:
        return table[0][1]
    if x >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        x0, v0 = table[i]
        x1, v1 = table[i + 1]
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return v0 + (v1 - v0) * t
    return table[-1][1]


# ==========================================================================
# Primitives locales (le kit ne les fournit pas : elles sont specifiques ici)
# ==========================================================================


def _slab(
    bm: bmesh.types.BMesh,
    lo: list[tuple[float, float, float]],
    hi: list[tuple[float, float, float]],
    mat_top: str,
    mat_side: str = "AA_Hull",
    mat_bot: str = "AA_Greeble",
) -> tuple[bmesh.types.BMFace | None, list]:
    """Tuile blindee : deux quads (dessous/dessus) relies par 4 flancs.

    Contrairement a `ak.add_box`, elle n'est pas alignee sur les axes : c'est ce
    qui permet de poser des ecailles sur une surface courbe.

    Retourne `(face du dessus, les 4 flancs)`. Les flancs sont dans l'ordre du
    ring, donc `sides[0]` est le **bord d'attaque** de la tuile : c'est la
    contremarche qui depasse quand la tuile monte sur sa voisine, et c'est elle
    qu'on rend emissive pour obtenir les interstices lumineux de la planche.
    """
    ring_lo = ak.add_ring(bm, lo)
    ring_hi = ak.add_ring(bm, hi)
    sides = ak.bridge_rings(bm, ring_lo, ring_hi, mat_side)
    top = ak.cap_ring(bm, ring_hi, mat_top)
    ak.cap_ring(bm, list(reversed(ring_lo)), mat_bot)
    return top, sides


def _bezier(p0, p1, p2, t: float) -> Vector:
    u = 1.0 - t
    return Vector(
        (
            u * u * p0[k] + 2.0 * u * t * p1[k] + t * t * p2[k]
            for k in range(3)
        )
    )


def _bezier_tangent(p0, p1, p2, t: float) -> Vector:
    u = 1.0 - t
    return Vector(
        (
            2.0 * u * (p1[k] - p0[k]) + 2.0 * t * (p2[k] - p1[k])
            for k in range(3)
        )
    )


def _frame(tangent: Vector) -> tuple[Vector, Vector]:
    """Repere transverse (droite, haut) d'une section perpendiculaire a `tangent`."""
    t = tangent.normalized()
    right = t.cross(Vector((0.0, 0.0, 1.0)))
    if right.length < 1e-5:
        right = Vector((1.0, 0.0, 0.0))
    right.normalize()
    up = right.cross(t).normalized()
    return right, up


# ==========================================================================
# Noyau
# ==========================================================================


def build_core() -> object:
    """Sphere magenta emissive, sillonnee de craquelures lumineuses.

    La croute (plaques violettes en relief) est *soulevee* facette par facette :
    ce qui reste au niveau de la sphere — les interstices et les parois d'inset —
    est emissif. La lumiere sort donc *d'entre* les plaques, comme sur la planche.
    Le tirage des facettes de croute est seede : rejouer donne le meme noyau.
    """
    bm = bmesh.new()

    contour: list[tuple[float, float, str]] = []
    for i in range(CORE_RINGS + 1):
        a = math.pi * i / CORE_RINGS
        contour.append(
            (-CORE_R * math.cos(a), CORE_R * math.sin(a), "AA_Emissive_Engine")
        )
    bands = ak.add_lathe(bm, contour, CORE_SEGMENTS)

    faces = [f for band in bands for f in band if f is not None and f.is_valid]
    rng = random.Random(SEED + 101)
    for face in faces:
        if rng.random() >= CORE_CRUST_P:
            continue  # facette laissee nue : c'est une craquelure lumineuse
        mat = "AA_Panel" if rng.random() < 0.78 else "AA_Hull"
        ak.inset_panel(
            bm, [face], mat,
            thickness=CORE_CRUST_INSET,
            depth=CORE_CRUST_LIFT * rng.uniform(0.7, 1.25),
        )

    return ak.new_object("Core", bm)


# ==========================================================================
# Corps
# ==========================================================================


def _body_section(y: float) -> list[tuple[float, float, float]]:
    """Section fermee du corps a la station `y`, du dos vers tribord."""
    hw = lerp_table(BODY_HW, y)
    top = lerp_table(BODY_TOP, y)
    bot = lerp_table(BODY_BOT, y)
    bend = lerp_table(BODY_BEND, y)
    port_mul = lerp_table(BODY_PORT_MUL, y)
    star_mul = lerp_table(BODY_STAR_MUL, y)

    z_mid = (top + bot) * 0.5
    up_h = top - z_mid
    dn_h = z_mid - bot

    pts: list[tuple[float, float, float]] = []
    for k in range(BODY_SECTION_N):
        a = math.pi * 0.5 + 2.0 * math.pi * k / BODY_SECTION_N
        c, s = math.cos(a), math.sin(a)
        mul = port_mul if c >= 0.0 else star_mul
        # Superellipse : flancs plus plats qu'une ellipse -> carapace, pas ballon.
        x = bend + hw * mul * math.copysign(abs(c) ** 0.72, c)
        z = z_mid + (up_h if s >= 0.0 else dn_h) * math.copysign(abs(s) ** 0.80, s)
        pts.append((x, y, z))
    return pts


def _body_axis(y: float) -> tuple[float, float, float]:
    top = lerp_table(BODY_TOP, y)
    bot = lerp_table(BODY_BOT, y)
    return (lerp_table(BODY_BEND, y), y, (top + bot) * 0.5)


def build_body() -> object:
    bm = bmesh.new()

    rings = [ak.add_ring(bm, _body_section(y)) for y in BODY_STATIONS[1:-1]]
    prow = bm.verts.new(_body_axis(BODY_STATIONS[0]))
    stern = bm.verts.new(_body_axis(BODY_STATIONS[-1]))

    ak.fan_to_point(bm, rings[0], prow, "AA_Trim")     # pointe de proue, ivoire
    bands: list[list] = []
    band_y: list[float] = []
    for i in range(len(rings) - 1):
        bands.append(ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull"))
        band_y.append((BODY_STATIONS[i + 1] + BODY_STATIONS[i + 2]) * 0.5)
    ak.fan_to_point(bm, list(reversed(rings[-1])), stern, "AA_Hull")

    def pick(y0: float, y1: float, ks: tuple[int, ...]) -> list:
        out = []
        for b, ym in enumerate(band_y):
            if y0 <= ym <= y1:
                for k in ks:
                    face = bands[b][k]
                    if face is not None and face.is_valid:
                        out.append(face)
        return out

    # --- dos ivoire (la carapace pale), ventre sombre ---------------------
    ak.set_material(pick(-4.4, 4.4, BODY_DORSAL), "AA_Trim")
    ak.set_material(pick(-4.4, 4.4, BODY_VENTRAL), "AA_Greeble")

    # --- lignes lumineuses de flanc, volontairement dissymetriques --------
    # Babord : longue veine avant. Tribord : veine arriere, plus courte.
    ak.set_material(pick(-3.10, 1.00, (11,)), "AA_Emissive_Engine")
    ak.set_material(pick(-0.90, 3.30, (3,)), "AA_Emissive_Engine")

    # --- panneaux enfonces : la carapace n'est jamais lisse ---------------
    for y0, y1, ks in (
        (-3.60, -2.30, BODY_DORSAL),
        (-2.20, -1.30, BODY_PORT),
        (-1.60, -0.60, BODY_STARBOARD),
        (1.40, 2.60, BODY_DORSAL),
        (1.90, 3.20, BODY_PORT),
        (2.40, 3.60, BODY_STARBOARD),
    ):
        ak.inset_panel(
            bm, pick(y0, y1, ks), "AA_Panel", thickness=0.030, depth=-0.028
        )

    _build_collar(bm)
    _build_pods(bm)
    _build_fin(bm)
    _build_dorsal_scales(bm)
    _build_membranes(bm)
    _build_nodules(bm)

    # Greebles mecaniques sur le dos arriere (seedes).
    ak.greeble_strip(
        bm, (0.10, 1.60, 0.44), (-0.10, 2.90, 0.32), count=7, seed=SEED + 11,
        size_range=(0.050, 0.120), height_range=(0.030, 0.075),
    )
    ak.greeble_strip(
        bm, (0.55, -2.20, 0.30), (0.30, -3.20, 0.20), count=5, seed=SEED + 12,
        size_range=(0.045, 0.100), height_range=(0.025, 0.060),
    )

    return ak.new_object("Body", bm)


def _build_collar(bm: bmesh.types.BMesh) -> None:
    """Anneau de tuiles autour du noyau (gros plan de la planche).

    Deux rangees concentriques, dephasees, dont les tuiles se recouvrent : la
    rangee interne monte sur l'externe. Chaque tuile porte un bord d'attaque
    emissif (une fois sur deux, tirage seede) : l'anneau *respire* autour du
    noyau au lieu d'etre une simple couronne peinte.
    """
    rng = random.Random(SEED + 201)
    for r_in, r_out, z_in, z_out, count, phase in COLLAR_ROWS:
        step = 2.0 * math.pi / count
        for k in range(count):
            a0 = (k + phase) * step
            a1 = a0 + step * COLLAR_OVERLAP
            ri = r_in + rng.uniform(-0.02, 0.03)
            ro = r_out + rng.uniform(-0.05, 0.06)
            zi = z_in + rng.uniform(-0.03, 0.05)
            zo = z_out + rng.uniform(-0.04, 0.03)

            lo, hi = [], []
            for a, rise in ((a0, 0.0), (a1, 0.035)):
                for r, z in ((ri, zi), (ro, zo)):
                    x, y = r * math.cos(a), r * math.sin(a)
                    lo.append((x, y, COLLAR_Z_BASE))
                    hi.append((x, y, z + rise))
            # ordre du ring : (a0,in) (a0,out) (a1,out) (a1,in)
            lo = [lo[0], lo[1], lo[3], lo[2]]
            hi = [hi[0], hi[1], hi[3], hi[2]]

            mat = CR_PLATE_MATS[rng.randrange(len(CR_PLATE_MATS))]
            top, sides = _slab(bm, lo, hi, mat, mat_side="AA_Greeble")
            if rng.random() < 0.5:
                ak.set_material([sides[0]], "AA_Emissive_Engine")
            if top is not None and rng.random() < 0.45:
                ak.inset_panel(bm, [top], "AA_Panel", thickness=0.035, depth=-0.024)


def _build_pods(bm: bmesh.types.BMesh) -> None:
    """Les deux fourreaux d'arme qui debordent de la proue (bouches Muzzle_L/R)."""
    for sign in (ak.PORT, ak.STARBOARD):
        ak.add_lathe(
            bm, POD_PROFILE, 12, center_x=sign * POD_X, center_z=POD_Z
        )
        # embase qui les rattache au corps
        ak.add_box(
            bm, (sign * (POD_X - 0.22), -0.95, POD_Z - 0.02),
            (0.44, 1.10, 0.24), "AA_Greeble",
        )


def _build_fin(bm: bmesh.types.BMesh) -> None:
    """Croc ventral avant : la lame qui pend sous la proue (planche, vue de face)."""
    rings = []
    for y, hw, z_low in FIN:
        z_top = lerp_table(BODY_BOT, y) + 0.06
        bend = lerp_table(BODY_BEND, y)
        rings.append(
            ak.add_ring(
                bm,
                [
                    (bend + hw, y, z_top),
                    (bend - hw, y, z_top),
                    (bend - hw * 0.35, y, z_low),
                    (bend + hw * 0.35, y, z_low),
                ],
            )
        )
    for i in range(len(rings) - 1):
        ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Trim")
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Greeble")

    # veine magenta sur l'arete du croc
    ak.add_box(bm, (0.06, -1.55, -0.735), (0.045, 1.30, 0.055),
               "AA_Emissive_Engine")


def _build_dorsal_scales(bm: bmesh.types.BMesh) -> None:
    """Ecailles dorsales : tuiles qui se recouvrent le long de l'echine.

    Leur demi-largeur est **derivee de `BODY_HW`** a la station courante, et le
    decalage lateral est borne par la marge restante : une ecaille ne peut donc
    pas se retrouver a flotter a cote de la coque, ce qui arrivait sur la proue
    quand elle etait une aiguille.
    """
    rng = random.Random(SEED + 301)
    spans = [
        (-4.20, -2.30, 10, 0.64),   # proue : le bec blinde, jusqu'a la pointe
        (-2.20, -1.25, 4, 0.66),    # epaules
        (1.15, 2.05, 4, 0.72),      # dos arriere
        (2.15, 4.20, 10, 0.62),     # dard, jusqu'a la pointe
    ]
    for y0, y1, count, spread in spans:
        for k in range(count):
            ya = y0 + (y1 - y0) * k / count
            yb = min(y0 + (y1 - y0) * (k + 1.35) / count, y1 + 0.08)
            hw_a = lerp_table(BODY_HW, ya) * spread * rng.uniform(0.85, 1.05)
            hw_b = lerp_table(BODY_HW, yb) * spread * rng.uniform(0.70, 0.92)
            # Decalage lateral seede, borne par ce qui reste de coque : les
            # ecailles ne sont pas centrees, mais elles restent posees dessus.
            margin = max(lerp_table(BODY_HW, ya) - hw_a, 0.0)
            off = rng.uniform(-margin, margin) * 0.8
            lo, hi = [], []
            for y, hw, rise in ((ya, hw_a, 0.045), (yb, hw_b, 0.010)):
                bend = lerp_table(BODY_BEND, y) + off
                z = lerp_table(BODY_TOP, y)
                for sx in (1.0, -1.0):
                    lo.append((bend + sx * hw, y, z - 0.11))
                    hi.append((bend + sx * hw, y, z + rise + 0.030))
            lo = [lo[0], lo[1], lo[3], lo[2]]
            hi = [hi[0], hi[1], hi[3], hi[2]]
            mat = CR_PLATE_MATS[rng.randrange(len(CR_PLATE_MATS))]
            top, sides = _slab(bm, lo, hi, mat, mat_side="AA_Panel")
            if rng.random() < 0.45:
                ak.set_material([sides[0]], "AA_Emissive_Engine")
            if top is not None and rng.random() < 0.5:
                ak.inset_panel(bm, [top], "AA_Greeble",
                               thickness=0.040, depth=-0.022)


def _build_membranes(bm: bmesh.types.BMesh) -> None:
    """Membranes sombres translucides (AA_Glass) : les « yeux » de la proue.

    Trois, de tailles differentes, deliberement non appairees. Chacune est
    clampee a la demi-largeur du corps a sa station : pas de vitre en l'air.
    """
    for x, y, hw, hl in ((0.30, -2.55, 0.17, 0.40),
                         (-0.24, -3.05, 0.12, 0.28),
                         (0.16, -3.55, 0.08, 0.20)):
        body_hw = lerp_table(BODY_HW, y)
        x = math.copysign(min(abs(x), max(body_hw - hw - 0.04, 0.0)), x)
        z = lerp_table(BODY_TOP, y)
        bend = lerp_table(BODY_BEND, y)
        ak.add_box(bm, (bend + x, y, z + 0.01), (hw * 2, hl * 2, 0.10), "AA_Glass")


def _build_nodules(bm: bmesh.types.BMesh) -> None:
    """Nodules vert maladif (AA_Marking_Red) — usage tres limite (charte §3).

    Un par racine d'epine, poses sur le dos : ce sont les « bourgeons » d'ou
    sortent les bras. Cinquieme sur l'epaule tribord, pour rompre l'appariement.
    """
    rng = random.Random(SEED + 401)
    for spike in SPIKES:
        rx, ry, _ = spike["root"]
        x, y = rx * 0.78, ry * 0.78
        z = lerp_table(BODY_TOP, y) + 0.02 + rng.uniform(-0.01, 0.02)
        ak.add_box(bm, (x, y, z), (0.15, 0.15, 0.11), "AA_Marking_Red")
    ak.add_box(
        bm, (-0.62, -1.55, lerp_table(BODY_TOP, -1.55) + 0.02),
        (0.12, 0.12, 0.10), "AA_Marking_Red",
    )


# ==========================================================================
# Coquille en croissant
# ==========================================================================


def _cr_point(phi_deg: float, radial: float, height: float) -> Vector:
    """Point de la coquille : `radial` en -1..1 (interne..externe), `height` en n."""
    p = math.radians(phi_deg)
    r = lerp_table(CR_R, phi_deg)
    w = lerp_table(CR_W, phi_deg)
    z = lerp_table(CR_Z, phi_deg)
    tilt = math.radians(lerp_table(CR_TILT, phi_deg))

    # bord interne souleve : c'est ce qui fait *surplomber* le noyau
    rr = r + radial * w * math.cos(tilt)
    zz = z - radial * w * math.sin(tilt)
    # normale de plaque (orthogonale a la corde et a la tangente)
    n = Vector(
        (math.sin(tilt) * math.cos(p), math.sin(tilt) * math.sin(p), math.cos(tilt))
    )
    return Vector((rr * math.cos(p), rr * math.sin(p), zz)) + n * height


def build_crescent() -> object:
    bm = bmesh.new()
    rng = random.Random(SEED + 501)
    span = CR_PHI_B - CR_PHI_A

    # --- nappe emissive continue, sous les tuiles -------------------------
    # Elle n'est visible que par les fentes de l'armure : la lumiere sort
    # *d'entre* les ecailles, elle n'est pas peinte dessus.
    glow_rings = []
    n_glow = 46
    for i in range(n_glow + 1):
        phi = CR_PHI_A + span * i / n_glow
        pts = [
            _cr_point(phi, -0.95, -0.045),
            _cr_point(phi, 0.95, -0.045),
            _cr_point(phi, 0.95, -0.130),
            _cr_point(phi, -0.95, -0.130),
        ]
        glow_rings.append(ak.add_ring(bm, [tuple(p) for p in pts]))
    for i in range(n_glow):
        ak.bridge_rings(bm, glow_rings[i], glow_rings[i + 1], "AA_Emissive_Engine")
    ak.cap_ring(bm, list(reversed(glow_rings[0])), "AA_Emissive_Engine")
    ak.cap_ring(bm, glow_rings[-1], "AA_Emissive_Engine")

    # --- trois rangees concentriques de tuiles tangentielles --------------
    for radial_lo, radial_hi, count, lift, thin, phase in CR_ROWS:
        step = span / count
        for k in range(-1, count):
            phi_a = max(CR_PHI_A + (k + phase) * step, CR_PHI_A)
            phi_b = min(phi_a + step * CR_OVERLAP, CR_PHI_B)
            if phi_b - phi_a < step * 0.35:
                continue
            _crescent_plate(
                bm, rng, phi_a, phi_b, radial_lo, radial_hi,
                lift_a=lift, lift_b=lift + 0.028, thin=thin,
            )

    # --- cornes : deux pointes qui prolongent les extremites du croissant --
    for phi, length, mat in ((CR_PHI_A, -22.0, "AA_Trim"),
                             (CR_PHI_B, 16.0, "AA_Trim")):
        base = [
            tuple(_cr_point(phi, -0.9, 0.02)),
            tuple(_cr_point(phi, 0.9, 0.02)),
            tuple(_cr_point(phi, 0.9, -0.08)),
            tuple(_cr_point(phi, -0.9, -0.08)),
        ]
        ring = ak.add_ring(bm, base)
        tip = bm.verts.new(tuple(_cr_point(phi + length, 0.0, -0.02)))
        ak.fan_to_point(bm, ring, tip, mat)
        ak.cap_ring(bm, list(reversed(ring)), "AA_Greeble")

    return ak.new_object("Shell_Crescent", bm)


def _crescent_plate(
    bm: bmesh.types.BMesh,
    rng: random.Random,
    phi_a: float,
    phi_b: float,
    radial_lo: float,
    radial_hi: float,
    lift_a: float,
    lift_b: float,
    thin: float = 1.0,
) -> None:
    """Une ecaille tangentielle : elle monte sur celle qui la precede.

    Son bord d'attaque (`phi_a`) depasse donc en contremarche ; une fois sur
    deux (tirage seede) cette contremarche est emissive. Aucun dessus n'est
    emissif : une premiere version en mettait, et le croissant devenait un
    tournesol de rayons magenta qui volait la vedette au noyau — or le noyau est
    la cible, et lui seul doit hurler en magenta (lisibilite, spec pilier B).
    """
    ra = radial_lo + rng.uniform(-0.04, 0.04)
    rb = radial_hi + rng.uniform(-0.05, 0.05)
    lo, hi = [], []
    for phi, lift in ((phi_a, lift_a), (phi_b, lift_b)):
        t = lerp_table(CR_T, phi) * thin
        for radial in (ra, rb):
            lo.append(tuple(_cr_point(phi, radial, lift - t * 0.40)))
            hi.append(tuple(_cr_point(phi, radial, lift + t * 0.60)))
    lo = [lo[0], lo[1], lo[3], lo[2]]
    hi = [hi[0], hi[1], hi[3], hi[2]]

    mat = CR_PLATE_MATS[rng.randrange(len(CR_PLATE_MATS))]
    top, sides = _slab(bm, lo, hi, mat, mat_side="AA_Greeble")
    if rng.random() < 0.5:
        ak.set_material([sides[0]], "AA_Emissive_Engine")
    if top is not None and rng.random() < 0.40:
        ak.inset_panel(bm, [top], "AA_Panel", thickness=0.045, depth=-0.028)


# ==========================================================================
# Bras-epines
# ==========================================================================


def _spike_radius(t: float, r0: float, vertebrae: int, taper: float) -> float:
    """Rayon a l'abscisse `t` : effilement global + relief de vertebre."""
    base = r0 * (1.0 - t) ** taper + SPIKE_TIP_R
    frac = (t * vertebrae) % 1.0
    return base * (1.0 + SPIKE_FLARE * (1.0 - frac) ** 1.6)


def build_spike(spec: dict) -> object:
    """Bras segmente : sections elliptiques (aplaties) le long d'une Bezier.

    Le rayon repart en avant a chaque vertebre : chaque segment recouvre le
    suivant comme une ecaille, et l'anneau de jonction — le plus etroit — est
    emissif. C'est la « veine de magenta » de la planche, obtenue par la
    geometrie et non par une texture (ADR-0008).
    """
    bm = bmesh.new()
    p0, p1, p2 = spec["root"], spec["ctrl"], spec["tip"]
    sides = spec["sides"]
    vertebrae = spec["vertebrae"]
    n = vertebrae * SPIKE_SAMPLES

    rings = []
    for i in range(n):
        t = i / n
        center = _bezier(p0, p1, p2, t)
        right, up = _frame(_bezier_tangent(p0, p1, p2, t))
        r = _spike_radius(t, spec["r0"], vertebrae, spec["taper"])
        rx, rz = r, r * spec["flat"]
        pts = []
        for j in range(sides):
            a = 2.0 * math.pi * j / sides
            p = center + up * (rz * math.cos(a)) + right * (rx * math.sin(a))
            pts.append(tuple(p))
        rings.append(ak.add_ring(bm, pts))

    tip = bm.verts.new(tuple(Vector(p2)))

    top_ks = (0, 1, sides - 1)
    bottom_k = sides // 2
    side_ks = (2, sides - 2)

    for i in range(n - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        phase = i % SPIKE_SAMPLES
        if phase == SPIKE_SAMPLES - 1:
            # jonction de vertebres : anneau lumineux sur tout le pourtour
            ak.set_material(band, "AA_Emissive_Engine")
            continue
        if phase == 0:
            ak.set_material(band, "AA_Trim")   # collier ivoire d'attaque
            continue
        ak.set_material([band[k] for k in top_ks], "AA_Trim")
        ak.set_material([band[k] for k in side_ks], "AA_Panel")
        ak.set_material([band[bottom_k]], "AA_Greeble")

    ak.fan_to_point(bm, rings[-1], tip, "AA_Trim")     # griffe ivoire
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")

    return ak.new_object(spec["name"], bm)


# ==========================================================================
# Points d'attache
# ==========================================================================


def build_attach_points() -> list:
    """Positions **derivees de la geometrie**, jamais devinees."""
    points = [ak.attach_point("Core_Center", (0.0, 0.0, 0.0))]
    points += list(ak.attach_pair("Muzzle", POD_X, MUZZLE_Y, POD_Z))
    points.append(ak.attach_point("Muzzle_C", MUZZLE_C))
    return points


# ==========================================================================
# Assemblage
# ==========================================================================


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)

    body = build_body()
    core = build_core()
    crescent = build_crescent()
    spikes = [build_spike(spec) for spec in SPIKES]

    # Le noyau reste lisse : un chanfrein sur ses ~200 ecailles de croute
    # coutait plus de 4 000 triangles pour un gain nul sur une sphere emissive.
    ak.cleanup(core)
    ak.shade_smooth_by_angle(core, angle_deg=30.0)

    for obj in (body, crescent, *spikes):
        ak.cleanup(obj)
        # Chanfrein a 1 segment, 6 mm : nettement sous la profondeur des
        # panneaux (28-45 mm), donc la marche reste franche. 34 deg ne prend
        # que les vraies aretes de structure, pas la courbure des sections.
        ak.bevel_sharp_edges(obj, width=0.006, segments=1, angle_deg=34.0)
        ak.shade_smooth_by_angle(obj, angle_deg=34.0)

    # --- correction d'axe des pieces annexes (cf. en-tete de module) -------
    # `export_hull()` ne la fait que pour l'objet passe en `hull`. On reutilise
    # SA matrice, jamais une copie : si le kit corrige sa chaine d'axes, les six
    # maillages bougent ensemble. A supprimer des que le kit exporte une liste.
    parts = [core, crescent, *spikes]
    for part in parts:
        part.data.transform(ak._AXIS_FIX)  # noqa: SLF001
        part.data.update()

    ak.export_hull(body, parts + build_attach_points(), OUTPUT, CONTRACT)


if __name__ == "__main__":
    main()
