"""build_aegis_citadel.py — coque 3D de l'Aegis Citadel, forteresse alliee (BRIEF-0025).

    blender45 -b -P tools/blender/build_aegis_citadel.py

Produit `assets/imported/models/structures/aegis_citadel.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (aucun alea non seede) et s'auto-valide : `ak.export_hull()`
relit le `.glb` produit et echoue bruyamment si la bounding box, le budget de
triangles, les materiaux, le centrage du pivot ou les points d'attache sortent
du contrat.

Reference de design : `assets/source/concepts/aegis_citadel_concept_sheet.png`.
Les tables ci-dessous sont relevees sur la grande vue de dessus de cette planche
(pixels -> metres, echelle 0,01445 m/px calee sur les deux cotes imposees par
l'ADR-0008 : 19,6 m d'envergure et 16,6 m de long).

Repere d'auteur (ADR-0008) : nez -Y, dessus +Z, **babord +X** (cf. aegis_kit).
Pour CETTE unite : les canons des bras-batteries pointent vers -Y (ils tirent
vers le haut de l'ecran) et la baie d'appontage s'ouvre vers +Y (cote joueur).

La citadelle est un objet de FOND, immobile, vu de tres loin : la lisibilite de
la silhouette prime sur le detail. Trois masses seulement doivent se lire d'un
coup d'oeil — corps central en prisme, deux bras-batteries, noyau cyan — et le
noyau est volontairement surdimensionne (7,0 m sur 16,6 m de long) : c'est la
signature permanente de la faction Vanguard.
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
# Contrat (ADR-0008, tableau des dimensions imposees + BRIEF-0025)
# ==========================================================================

CONTRACT = ak.HullContract(
    name="Aegis Citadel",
    width_x=19.60,      # Godot X — bout de bras a bout de bras
    length_z=16.60,     # Godot Z — bouche des canons a talon de la rampe
    max_height_y=5.00,  # Godot Y — plafond impose par le brief
    tri_budget=30_000,
    required_materials=ak.MATERIAL_ORDER,  # les 7 : la planche les utilise tous
    required_attach_points=(
        "Core_Center",
        "Muzzle_Battery_L",
        "Muzzle_Battery_R",
        "Dock_Entry",
    ),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/structures/aegis_citadel.glb")

SEED = 30250  # graine unique de la citadelle (determinisme des greebles)

HALF_W = CONTRACT.width_x / 2.0    # 9.80 — bord externe des bras
HALF_L = CONTRACT.length_z / 2.0   # 8.30 — bouche des canons / talon de rampe

# ==========================================================================
# Tables de profil, relevees sur la vue de dessus de la planche
# ==========================================================================

# Corps central : (y, demi-largeur, z du pont, z de la quille).
#
# Table volontairement ANGULEUSE, pas une courbe echantillonnee : la charte
# demande un « prisme axial », et le premier jet — treize stations suivant une
# ellipse — donnait en silhouette un oeuf, pas une forteresse. D'ou trois
# cassures franches (proue, epaule, hanche) et un long flanc PARALLELE de 5,6 m
# qui porte tout le caractere prismatique de la piece.
HULL: list[tuple[float, float, float, float]] = [
    (-7.60, 1.55, 0.78, -0.62),   # face de proue
    (-6.40, 2.95, 1.06, -1.02),   # cassure de proue (grande diagonale)
    (-5.40, 3.52, 1.16, -1.24),   # cassure d'epaule
    (-4.00, 3.75, 1.22, -1.38),   # largeur max atteinte
    (-1.00, 3.75, 1.24, -1.45),   # |
    (1.60, 3.75, 1.22, -1.42),    # +-- flanc parallele : le prisme
    (3.00, 3.45, 1.16, -1.28),    # cassure de hanche
    (4.30, 2.75, 1.08, -1.04),
    (5.60, 1.60, 0.94, -0.66),    # culasse arriere, au-dessus de la baie
]

# Bras-batterie (une seule table : l'autre bras en est la copie miroir).
# Meme parti pris : flanc externe rectiligne sur 5,4 m, extremites tronquees.
ARM_X = 7.65        # axe du bras (|x|)
ARM: list[tuple[float, float, float, float]] = [
    (-6.60, 0.95, 0.70, -0.70),   # nez du bras (les canons en sortent)
    (-5.85, 1.66, 0.94, -0.94),
    (-4.90, 2.15, 1.05, -1.05),   # |  7.65 + 2.15 = 9.80 = HALF_W (bbox X)
    (-1.00, 2.15, 1.05, -1.05),   # +-- flanc parallele
    (1.30, 2.15, 1.03, -1.03),    # |
    (2.60, 1.82, 0.98, -0.98),
    (3.70, 0.90, 0.74, -0.74),    # culot du bras
]

# Noyau cristallin : (y, demi-largeur). Prisme hexagonal facette, pointes avant
# et arriere, assis en travers du pont du corps central. Volontairement enorme :
# 4,0 m de large et 7,0 m de long, soit 42 % de la longueur totale.
CORE: list[tuple[float, float]] = [
    (-5.30, 0.00),   # pointe avant
    (-4.40, 0.90),
    (-3.20, 1.58),
    (-1.90, 1.98),   # section maitresse
    (-0.60, 1.94),
    (0.50, 1.55),
    (1.20, 0.88),
    (1.70, 0.00),    # pointe arriere
]
CORE_BASE_Z = 1.05   # assise, noyee dans le pont
CORE_MID_Z = 2.25    # ligne de plus grande largeur du cristal
CORE_TOP_Z = 3.30    # sommet — POINT LE PLUS HAUT DE LA COQUE
CORE_HW_MAX = 1.98
# Sommet a 3,30 et non 3,40 : les nervures saillent de 7 cm au-dessus de la
# facette et le chanfrein ajoute encore quelques millimetres. A 3,40 la coque
# mesurait 4,98 m de haut pour un plafond a 5,00 — 2 cm de marge, c'est-a-dire
# aucune. 10 cm rendus ici sur un cristal de 2,25 m ne se voient pas.

# Canons principaux : (offset lateral depuis l'axe du bras, y de la bouche).
# Le tube externe est le plus long : c'est lui qui fixe la bbox en -Y et qui
# porte le point d'attache Muzzle_Battery_*.
BARRELS: list[tuple[float, float]] = [
    (0.95, -HALF_L),    # tube externe — BOUCHE PRINCIPALE (bbox -Y)
    (0.00, -8.10),
    (-0.95, -7.90),
]
BARREL_R = 0.26
BARREL_Z = 1.05       # les tubes chevauchent le pont du bras (cf. vue de profil)
BARREL_ROOT = -4.30   # culasse, sous les colliers, au ras du pont du bras
BARREL_SEGMENTS = 10

# Tubes arriere (visibles sur la vue arriere de la planche) : plus courts.
AFT_BARRELS: list[float] = [0.70, -0.70]
AFT_TIP = 5.30
AFT_R = 0.24
AFT_Z = 0.10

# Tourelles secondaires a double tube : (x, y, z d'assise).
TURRETS: list[tuple[float, float, float]] = [
    (2.00, -6.20, 1.02),      # epaule avant babord
    (-2.00, -6.20, 1.02),     # epaule avant tribord
    (2.85, 2.05, 1.05),       # flanc arriere babord
    (-2.85, 2.05, 1.05),      # flanc arriere tribord
    (ARM_X, 0.30, 0.90),      # pont du bras babord
    (-ARM_X, 0.30, 0.90),     # pont du bras tribord
]
TURRET_R = 0.82

# Entretoises corps <-> bras : (y, z). Cylindres transversaux a colliers.
STRUTS: list[tuple[float, float]] = [
    (-3.00, 0.05),
    (0.80, 0.05),
]
STRUT_X0 = 3.30    # noye dans le flanc du corps central
STRUT_X1 = 5.75    # noye dans le flanc du bras
STRUT_SEGMENTS = 12

# Baie d'appontage : rampe trapezoidale, chevrons cyan pointant vers l'avant.
DOCK_Y0 = 5.20     # sous la culasse du corps central
DOCK_Y1 = HALF_L   # talon de la rampe — TALON (bbox +Y)
DOCK_HW0 = 1.78
DOCK_HW1 = 1.58
DOCK_TOP_Z = -0.16
DOCK_BOT_Z = -0.44


# ==========================================================================
# Helpers locaux
#
# Le kit fournit `add_lathe()` (revolution autour de Y : les canons). Cette
# coque a aussi besoin de solides de revolution autour de Z (fûts de tourelle)
# et autour de X (entretoises transversales), ainsi que de barres orientables
# (chevrons de la rampe). Ces trois helpers sont construits **exclusivement**
# avec les primitives publiques du kit (`add_ring`, `bridge_rings`,
# `fan_to_point`, `cap_ring`) : aucune geometrie n'est codee en dur ici que le
# kit saurait deja faire. Voir le compte-rendu : une revolution parametrable par
# axe serait la bonne evolution du kit.
# ==========================================================================


def lerp_table(table: list[tuple[float, ...]], y: float, col: int = 1) -> float:
    """Interpolation lineaire par morceaux d'une table `(y, ...)`, extremites clampees."""
    if y <= table[0][0]:
        return table[0][col]
    if y >= table[-1][0]:
        return table[-1][col]
    for i in range(len(table) - 1):
        y0, y1 = table[i][0], table[i + 1][0]
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return table[i][col] + (table[i + 1][col] - table[i][col]) * t
    return table[-1][col]


def _hull_ring(bm, cx: float, y: float, hw: float, zt: float, zb: float):
    """Section prismatique a 10 sommets : pont plat, flancs chanfreines, quille.

    Ordre (fixe l'index des faces produites par `bridge_rings`) :
      0 lisse babord | 1 pont babord | 2 pont central | 3 pont tribord
      4 lisse tribord | 5 flanc bas tribord | 6 quille tribord | 7 quille centrale
      8 quille babord | 9 flanc bas babord
    """
    zm = zb + 0.58 * (zt - zb)
    pts = [
        (cx + hw, y, zm),
        (cx + 0.86 * hw, y, zt),
        (cx + 0.30 * hw, y, zt),
        (cx - 0.30 * hw, y, zt),
        (cx - 0.86 * hw, y, zt),
        (cx - hw, y, zm),
        (cx - 0.80 * hw, y, zb),
        (cx - 0.28 * hw, y, zb),
        (cx + 0.28 * hw, y, zb),
        (cx + 0.80 * hw, y, zb),
    ]
    return ak.add_ring(bm, pts)


#: Index de face, dans une bande de `_hull_ring`, par role.
F_CHINE_P, F_DECK_P, F_DECK_C, F_DECK_S, F_CHINE_S = 0, 1, 2, 3, 4
F_KEEL_S, F_KEEL_C, F_KEEL_P = 6, 7, 8


def _prismatic_body(bm, cx: float, table, cap_front: str, cap_rear: str):
    """Construit un corps ferme depuis une table `(y, hw, zt, zb)`.

    Retourne `(bandes, y_milieu_de_bande)` : de quoi selectionner ensuite des
    faces par zone (panneaux, liseres) comme le fait `build_specter_9`.
    """
    rings = [_hull_ring(bm, cx, y, hw, zt, zb) for y, hw, zt, zb in table]
    bands, band_y = [], []
    for i in range(len(rings) - 1):
        bands.append(ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull"))
        band_y.append((table[i][0] + table[i + 1][0]) * 0.5)
    ak.cap_ring(bm, list(reversed(rings[0])), cap_front)
    ak.cap_ring(bm, rings[-1], cap_rear)
    return bands, band_y


def _pick(bands, band_y, y0: float, y1: float, faces: set[int]) -> list:
    """Faces des bandes dont le milieu tombe dans [y0, y1], pour les roles donnes."""
    out = []
    for b, ym in enumerate(band_y):
        if y0 <= ym <= y1:
            for j in faces:
                face = bands[b][j]
                if face is not None and face.is_valid:
                    out.append(face)
    return out


def _z_drum(bm, cx: float, cy: float, profile, segments: int) -> None:
    """Solide de revolution autour de **Z** : `profile` = [(z, rayon, materiau)].

    Sert aux fûts de tourelle (le kit ne sait tourner qu'autour de Y).
    """
    rings = []
    for z, r, _ in profile:
        if r <= 1e-6:
            rings.append(bm.verts.new((cx, cy, z)))
            continue
        rings.append(
            ak.add_ring(
                bm,
                [
                    (
                        cx + r * math.cos(2.0 * math.pi * s / segments),
                        cy + r * math.sin(2.0 * math.pi * s / segments),
                        z,
                    )
                    for s in range(segments)
                ],
            )
        )
    _stitch(bm, rings, [m for _, _, m in profile])


def _x_tube(bm, cy: float, cz: float, profile, segments: int) -> None:
    """Solide de revolution autour de **X** : `profile` = [(x, rayon, materiau)].

    Sert aux entretoises transversales corps <-> bras.
    """
    rings = []
    for x, r, _ in profile:
        if r <= 1e-6:
            rings.append(bm.verts.new((x, cy, cz)))
            continue
        rings.append(
            ak.add_ring(
                bm,
                [
                    (
                        x,
                        cy + r * math.cos(2.0 * math.pi * s / segments),
                        cz + r * math.sin(2.0 * math.pi * s / segments),
                    )
                    for s in range(segments)
                ],
            )
        )
    _stitch(bm, rings, [m for _, _, m in profile])


def _stitch(bm, rings, materials) -> None:
    """Relie une suite de boucles (ou de poles) : commun a `_z_drum`/`_x_tube`."""
    for i in range(len(rings) - 1):
        a, b, mat = rings[i], rings[i + 1], materials[i]
        if isinstance(a, bmesh.types.BMVert) and isinstance(b, list):
            ak.fan_to_point(bm, b, a, mat)
        elif isinstance(b, bmesh.types.BMVert) and isinstance(a, list):
            ak.fan_to_point(bm, a, b, mat)
        elif isinstance(a, list) and isinstance(b, list):
            ak.bridge_rings(bm, a, b, mat)


def _bar(bm, p0, p1, width: float, z_lo: float, z_hi: float, material: str) -> None:
    """Barre prismatique orientee librement dans le plan XY (chevrons, liseres)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    nx, ny = -dy / length * width * 0.5, dx / length * width * 0.5
    corners = [
        (p0[0] + nx, p0[1] + ny),
        (p1[0] + nx, p1[1] + ny),
        (p1[0] - nx, p1[1] - ny),
        (p0[0] - nx, p0[1] - ny),
    ]
    lo = ak.add_ring(bm, [(x, y, z_lo) for x, y in corners])
    hi = ak.add_ring(bm, [(x, y, z_hi) for x, y in corners])
    ak.bridge_rings(bm, lo, hi, material)
    ak.cap_ring(bm, list(reversed(lo)), material)
    ak.cap_ring(bm, hi, material)


# ==========================================================================
# Corps central
# ==========================================================================


def build_core_hull():
    bm = bmesh.new()
    bands, band_y = _prismatic_body(bm, 0.0, HULL, "AA_Hull", "AA_Greeble")

    # --- aplats bleus du pont, borde LARGE -------------------------------
    # `thickness` = largeur du liston blanc laisse autour du panneau. A 0,12 m
    # sur une face de pont large de 2 m, le bleu mangeait 90 % de la surface et
    # la citadelle virait au bleu : la coque Vanguard est blanc casse, le bleu
    # n'est qu'un panneau. On borde donc a 0,32 m, et on laisse la proue et la
    # poupe entierement blanches (elles portent les liseres or).
    for y0, y1 in ((-5.40, -1.00), (-1.00, 3.00)):
        ak.inset_panel(
            bm,
            _pick(bands, band_y, y0, y1, {F_DECK_P, F_DECK_S}),
            "AA_Panel",
            thickness=0.32,
            depth=-0.07,
        )

    # --- puits du noyau : cuve sombre bordee d'or, creusee dans le pont ---
    well = _pick(bands, band_y, -5.60, 2.00, {F_DECK_C})
    border = ak.inset_panel(bm, well, "AA_Greeble", thickness=0.16, depth=-0.10)
    ak.set_material(border, "AA_Trim")

    # --- lisses : liseres or aux deux bouts, bandeau bleu au milieu -------
    ak.set_material(_pick(bands, band_y, -7.40, -6.00, {F_CHINE_P, F_CHINE_S}), "AA_Trim")
    ak.set_material(_pick(bands, band_y, 4.40, 5.40, {F_CHINE_P, F_CHINE_S}), "AA_Trim")
    ak.inset_panel(
        bm,
        _pick(bands, band_y, -4.00, 1.60, {F_CHINE_P, F_CHINE_S}),
        "AA_Panel",
        thickness=0.22,
        depth=-0.05,
    )

    # --- quille : mecanique sombre ---------------------------------------
    ak.set_material(
        _pick(bands, band_y, -7.40, 5.40, {F_KEEL_C}), "AA_Greeble"
    )
    ak.inset_panel(
        bm,
        _pick(bands, band_y, -6.00, 4.00, {F_KEEL_P, F_KEEL_S}),
        "AA_Panel",
        thickness=0.12,
        depth=-0.06,
    )

    return ak.new_object("Citadel_Hull", bm)


# ==========================================================================
# Bras-batteries
# ==========================================================================


def build_arm(sx: float):
    """Un bras-batterie complet (capsule + mantelet + tubes), du cote `sx`.

    `sx` vaut `ak.PORT` (+1) ou `ak.STARBOARD` (-1) : jamais un signe ecrit a la
    main (cf. le piege d'orientation documente dans le kit).
    """
    bm = bmesh.new()
    cx = sx * ARM_X
    bands, band_y = _prismatic_body(bm, cx, ARM, "AA_Greeble", "AA_Greeble")

    # grand aplat bleu du pont du bras (le plus visible de la planche), borde
    # large : le bras doit rester une masse BLANCHE ponctuee de bleu.
    ak.inset_panel(
        bm,
        _pick(bands, band_y, -2.00, 2.00, {F_DECK_P, F_DECK_S}),
        "AA_Panel",
        thickness=0.34,
        depth=-0.08,
    )
    ak.inset_panel(
        bm,
        _pick(bands, band_y, -4.20, 2.00, {F_KEEL_P, F_KEEL_S}),
        "AA_Panel",
        thickness=0.20,
        depth=-0.07,
    )
    ak.set_material(_pick(bands, band_y, -6.20, -4.20, {F_CHINE_P, F_CHINE_S}), "AA_Trim")

    # --- mantelet : le bloc de culasse d'ou sortent les trois tubes -------
    ak.add_box(bm, (cx, -5.30, 0.55), (3.90, 2.10, 1.05), "AA_Greeble")
    ak.add_box(bm, (cx, -5.30, 1.10), (2.40, 1.20, 0.22), "AA_Trim")
    ak.add_box(bm, (cx, -3.10, 0.98), (3.30, 1.30, 0.60), "AA_Greeble")
    ak.add_box(bm, (cx, -3.10, 1.30), (1.10, 0.90, 0.16), "AA_Emissive_Engine")

    # --- canons principaux, pointes vers -Y (haut de l'ecran) -------------
    for d, tip in BARRELS:
        ak.add_lathe(
            bm,
            [
                (BARREL_ROOT, 0.00, "AA_Greeble"),          # pole de culasse
                (BARREL_ROOT + 0.05, 0.34, "AA_Greeble"),
                (BARREL_ROOT - 0.90, 0.34, "AA_Greeble"),   # bloc de culasse
                (BARREL_ROOT - 0.95, BARREL_R, "AA_Greeble"),
                (tip + 1.05, BARREL_R, "AA_Greeble"),
                (tip + 1.00, BARREL_R * 1.20, "AA_Trim"),   # collier dore
                (tip + 0.45, BARREL_R * 1.20, "AA_Trim"),
                (tip + 0.40, BARREL_R, "AA_Greeble"),
                (tip + 0.06, BARREL_R * 1.06, "AA_Greeble"),  # levre de bouche
                (tip, BARREL_R * 1.02, "AA_Greeble"),       # BOUCHE (bbox -Y)
                (tip + 0.02, BARREL_R * 0.55, "AA_Emissive_Engine"),
                (tip + 0.30, BARREL_R * 0.50, "AA_Emissive_Engine"),
                (tip + 0.34, 0.00, "AA_Emissive_Engine"),   # ame lumineuse
            ],
            BARREL_SEGMENTS,
            center_x=cx + sx * d,
            center_z=BARREL_Z,
        )
        # collier de fixation sur le pont du bras
        ak.add_box(
            bm, (cx + sx * d, -6.10, BARREL_Z - 0.10), (0.62, 0.34, 0.72), "AA_Trim"
        )

    # --- tubes arriere (vue arriere de la planche) ------------------------
    for d in AFT_BARRELS:
        ak.add_lathe(
            bm,
            [
                (2.20, 0.00, "AA_Greeble"),
                (2.30, AFT_R, "AA_Greeble"),
                (AFT_TIP - 0.30, AFT_R, "AA_Greeble"),
                (AFT_TIP - 0.26, AFT_R * 1.18, "AA_Trim"),
                (AFT_TIP, AFT_R * 1.18, "AA_Trim"),
                (AFT_TIP, AFT_R * 0.55, "AA_Emissive_Engine"),
                (AFT_TIP - 0.34, AFT_R * 0.50, "AA_Emissive_Engine"),
                (AFT_TIP - 0.38, 0.00, "AA_Emissive_Engine"),
            ],
            8,
            center_x=cx + sx * d,
            center_z=AFT_Z,
        )

    # --- lumieres d'echelle sur la lisse externe (charte §4) --------------
    # Bord externe a 2,10 + 0,05 = 2,15 du centre du bras : elles affleurent la
    # lisse sans deborder, sinon ce sont ELLES qui fixeraient la largeur hors
    # tout (et la bbox derivait de +0,6 %).
    for k in range(6):
        y = -3.60 + k * 1.30
        ak.add_box(
            bm,
            (cx + sx * 2.10, y, 0.30),
            (0.10, 0.34, 0.16),
            "AA_Emissive_Engine",
        )

    # --- greebles de pont, semees (deterministes) -------------------------
    ak.greeble_strip(
        bm,
        (cx + sx * 1.40, -1.60, 1.02),
        (cx + sx * 1.40, 2.20, 1.02),
        count=5,
        seed=SEED + (11 if sx > 0 else 23),
        size_range=(0.22, 0.46),
        height_range=(0.10, 0.26),
        jitter=0.05,
    )

    return ak.new_object("Citadel_Arm_" + ("L" if sx > 0 else "R"), bm)


# ==========================================================================
# Noyau cristallin — la signature de la silhouette
# ==========================================================================


def build_core_prism():
    """Prisme hexagonal facette, integralement emissif cyan.

    Chaque section est un hexagone (large a mi-hauteur, arete faitiere en haut,
    base etroite) dont la hauteur suit la largeur : le cristal se pince vers ses
    deux pointes au lieu de rester un bandeau plat, ce qui lui donne ses facettes.
    """
    bm = bmesh.new()
    rings = []
    for y, hw in CORE:
        if hw <= 1e-6:
            rings.append(bm.verts.new((0.0, y, CORE_MID_Z)))
            continue
        k = hw / CORE_HW_MAX
        z_mid = CORE_BASE_Z + (CORE_MID_Z - CORE_BASE_Z) * (0.35 + 0.65 * k)
        z_top = CORE_BASE_Z + (CORE_TOP_Z - CORE_BASE_Z) * (0.30 + 0.70 * k)
        rings.append(
            ak.add_ring(
                bm,
                [
                    (hw, y, z_mid),                  # arete babord (plus grande largeur)
                    (0.52 * hw, y, z_top),           # facette babord
                    (-0.52 * hw, y, z_top),          # faitiere
                    (-hw, y, z_mid),                 # arete tribord
                    (-0.62 * hw, y, CORE_BASE_Z),    # base tribord
                    (0.62 * hw, y, CORE_BASE_Z),     # base babord
                ],
            )
        )
    _stitch(bm, rings, ["AA_Emissive_Engine"] * len(rings))

    # --- nervures de taille, sur les aretes de facette --------------------
    # Un materiau emissif ne recoit PAS la lumiere : ses facettes ont toutes la
    # meme valeur, et le cristal, si soigne soit-il en geometrie, se rendait
    # comme une goutte blanche uniforme. Les facettes ne peuvent donc exister
    # que par la geometrie : de fines nervures anthracite courent le long des
    # trois aretes de taille (faitiere + deux aretes de facette). Ce sont les
    # traits sombres que montre la planche sur le cristal.
    #
    # Elles sont BALAYEES par petits pas de 0,35 m et non posees station par
    # station : une barre droite tendue sur une station entiere depassait de
    # 60 cm au-dessus des pointes du cristal — trois griffes noires. Les pointes
    # (les 0,9 m de chaque bout) restent nues : c'est la que le verre doit etre
    # le plus pur.
    # Le pas (0,22 m) et la saillie (0,07 m) sont lies : chaque barre est droite
    # alors que la facette monte, donc elle s'enfonce de (pente x pas / 2) au
    # milieu. Tant que cette fleche reste sous la saillie, la nervure est
    # continue ; a 0,35 m de pas elle se rompait en pointilles.
    step = 0.22
    y_start, y_end = -4.20, 1.00
    steps = int(round((y_end - y_start) / step))
    for lane in (0.0, 0.52, -0.52):
        for i in range(steps):
            y0 = y_start + i * step
            y1 = y0 + step
            z_mid = _core_top_z((y0 + y1) * 0.5)
            _bar(
                bm,
                (lane * _core_hw(y0), y0),
                (lane * _core_hw(y1), y1),
                0.11,
                z_mid - 0.40,
                z_mid + 0.07,
                "AA_Greeble",
            )

    return ak.new_object("Citadel_Core", bm)


def _core_hw(y: float) -> float:
    """Demi-largeur du cristal a la station `y`."""
    return lerp_table(CORE, y)


def _core_top_z(y: float) -> float:
    """Altitude de la facette faitiere du cristal a la station `y`."""
    k = _core_hw(y) / CORE_HW_MAX
    return CORE_BASE_Z + (CORE_TOP_Z - CORE_BASE_Z) * (0.30 + 0.70 * k)


def build_core_frame():
    """Le cadre technique qui enchasse le noyau : or, anthracite, rouge."""
    bm = bmesh.new()

    # jonc dore continu autour de l'assise du cristal
    for sx in (ak.PORT, ak.STARBOARD):
        for i in range(len(CORE) - 1):
            y0, hw0 = CORE[i]
            y1, hw1 = CORE[i + 1]
            if hw0 < 1e-6 and hw1 < 1e-6:
                continue
            _bar(
                bm,
                (sx * (hw0 + 0.14), y0),
                (sx * (hw1 + 0.14), y1),
                0.22,
                CORE_BASE_Z - 0.34,
                CORE_BASE_Z + 0.16,
                "AA_Trim",
            )

    # contreforts anthracite : deux paires d'arcs-boutants sur les flancs
    for sx in (ak.PORT, ak.STARBOARD):
        for y in (-4.10, -0.30):
            ak.add_box(bm, (sx * 2.55, y, 1.00), (1.10, 0.90, 0.60), "AA_Greeble")
            ak.add_box(bm, (sx * 2.55, y, 1.34), (0.86, 0.66, 0.16), "AA_Trim")

    # marquages rouges de zone reglementee, de part et d'autre du puits
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * 2.55, -2.20, 1.28), (0.70, 0.90, 0.12), "AA_Marking_Red")

    return ak.new_object("Citadel_CoreFrame", bm)


# ==========================================================================
# Tourelles secondaires
# ==========================================================================


def build_turrets():
    bm = bmesh.new()
    for x, y, z in TURRETS:
        _z_drum(
            bm,
            x,
            y,
            [
                (z - 0.30, 0.00, "AA_Greeble"),
                (z - 0.30, TURRET_R * 0.90, "AA_Greeble"),
                (z + 0.10, TURRET_R, "AA_Hull"),
                (z + 0.34, TURRET_R * 0.96, "AA_Hull"),
                (z + 0.40, TURRET_R * 0.70, "AA_Trim"),
                (z + 0.44, 0.00, "AA_Trim"),
            ],
            12,
        )
        # casemate + oeil cyan
        ak.add_box(bm, (x, y - 0.24, z + 0.52), (0.92, 0.86, 0.34), "AA_Greeble")
        ak.add_box(bm, (x, y - 0.10, z + 0.70), (0.34, 0.30, 0.10), "AA_Emissive_Engine")
        # double tube, pointe vers -Y
        for sd in (ak.PORT, ak.STARBOARD):
            ak.add_lathe(
                bm,
                [
                    (y - 0.20, 0.00, "AA_Greeble"),
                    (y - 0.24, 0.13, "AA_Greeble"),
                    (y - 1.30, 0.13, "AA_Greeble"),
                    (y - 1.34, 0.16, "AA_Trim"),
                    (y - 1.46, 0.16, "AA_Trim"),
                    (y - 1.46, 0.07, "AA_Greeble"),
                    (y - 1.30, 0.06, "AA_Greeble"),
                    (y - 1.28, 0.00, "AA_Greeble"),
                ],
                8,
                center_x=x + sd * 0.24,
                center_z=z + 0.52,
            )
    return ak.new_object("Citadel_Turrets", bm)


# ==========================================================================
# Entretoises, passerelle, baie d'appontage
# ==========================================================================


def build_struts():
    bm = bmesh.new()
    for y, z in STRUTS:
        for sx in (ak.PORT, ak.STARBOARD):
            _x_tube(
                bm,
                y,
                z,
                [
                    (sx * STRUT_X0, 0.00, "AA_Greeble"),
                    (sx * STRUT_X0, 0.58, "AA_Greeble"),
                    (sx * (STRUT_X0 + 0.32), 0.58, "AA_Greeble"),
                    (sx * (STRUT_X0 + 0.36), 0.76, "AA_Trim"),   # collier dore
                    (sx * (STRUT_X0 + 0.62), 0.76, "AA_Trim"),
                    (sx * (STRUT_X0 + 0.66), 0.52, "AA_Greeble"),
                    (sx * (STRUT_X0 + 1.00), 0.52, "AA_Greeble"),
                    (sx * (STRUT_X0 + 1.04), 0.68, "AA_Emissive_Engine"),  # anneau cyan
                    (sx * (STRUT_X0 + 1.24), 0.68, "AA_Emissive_Engine"),
                    (sx * (STRUT_X0 + 1.28), 0.52, "AA_Greeble"),
                    (sx * (STRUT_X0 + 1.70), 0.52, "AA_Greeble"),
                    (sx * (STRUT_X0 + 1.74), 0.78, "AA_Trim"),
                    (sx * (STRUT_X0 + 2.06), 0.78, "AA_Trim"),
                    (sx * (STRUT_X0 + 2.10), 0.60, "AA_Greeble"),
                    (sx * STRUT_X1, 0.60, "AA_Greeble"),
                    (sx * STRUT_X1, 0.00, "AA_Greeble"),
                ],
                STRUT_SEGMENTS,
            )
    return ak.new_object("Citadel_Struts", bm)


def build_bridge():
    """Passerelle de proue : verriere sombre + marquage rouge (cf. planche)."""
    bm = bmesh.new()
    ak.add_box(bm, (0.0, -6.55, 1.16), (2.10, 1.30, 0.44), "AA_Hull")
    ak.add_box(bm, (0.0, -6.90, 1.40), (1.40, 0.72, 0.30), "AA_Glass")
    ak.add_box(bm, (0.0, -6.10, 1.42), (0.90, 0.34, 0.22), "AA_Trim")
    ak.add_box(bm, (0.0, -7.36, 1.06), (0.52, 0.26, 0.16), "AA_Marking_Red")
    # antennes / greebles de proue
    ak.greeble_strip(
        bm,
        (0.0, -5.90, 1.24),
        (0.0, -5.20, 1.24),
        count=3,
        seed=SEED + 7,
        size_range=(0.20, 0.40),
        height_range=(0.12, 0.30),
        jitter=0.04,
    )
    return ak.new_object("Citadel_Bridge", bm)


def build_dock():
    """Baie d'appontage arriere : gorge lumineuse, rampe, chevrons cyan.

    La baie regarde vers +Y — c'est-a-dire vers le joueur, en bas de l'ecran.
    """
    bm = bmesh.new()

    # gorge : bouche lumineuse encastree dans la culasse du corps central
    ak.add_box(bm, (0.0, 5.28, 0.10), (3.30, 1.10, 1.30), "AA_Greeble")
    ak.add_box(bm, (0.0, 5.56, 0.16), (2.30, 0.60, 1.00), "AA_Emissive_Engine")
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * 1.52, 5.60, 0.20), (0.34, 0.66, 1.20), "AA_Trim")

    # rampe trapezoidale
    lo = ak.add_ring(
        bm,
        [
            (DOCK_HW0, DOCK_Y0, DOCK_BOT_Z),
            (-DOCK_HW0, DOCK_Y0, DOCK_BOT_Z),
            (-DOCK_HW1, DOCK_Y1, DOCK_BOT_Z),
            (DOCK_HW1, DOCK_Y1, DOCK_BOT_Z),
        ],
    )
    hi = ak.add_ring(
        bm,
        [
            (DOCK_HW0, DOCK_Y0, DOCK_TOP_Z),
            (-DOCK_HW0, DOCK_Y0, DOCK_TOP_Z),
            (-DOCK_HW1, DOCK_Y1, DOCK_TOP_Z),
            (DOCK_HW1, DOCK_Y1, DOCK_TOP_Z),
        ],
    )
    ak.bridge_rings(bm, lo, hi, "AA_Hull")
    ak.cap_ring(bm, list(reversed(lo)), "AA_Greeble")
    deck = ak.cap_ring(bm, hi, "AA_Hull")
    if deck is not None:
        ak.inset_panel(bm, [deck], "AA_Panel", thickness=0.20, depth=-0.05)

    # rails lateraux dores
    for sx in (ak.PORT, ak.STARBOARD):
        _bar(
            bm,
            (sx * (DOCK_HW0 - 0.16), DOCK_Y0),
            (sx * (DOCK_HW1 - 0.16), DOCK_Y1),
            0.30,
            DOCK_TOP_Z - 0.10,
            DOCK_TOP_Z + 0.22,
            "AA_Trim",
        )

    # chevrons cyan pointant vers l'avant (guidage d'appontage)
    for k in range(4):
        y = DOCK_Y0 + 0.62 + k * 0.72
        half = 0.86 - 0.05 * k
        for sx in (ak.PORT, ak.STARBOARD):
            _bar(
                bm,
                (0.0, y - 0.34),
                (sx * half, y + 0.16),
                0.20,
                DOCK_TOP_Z - 0.02,
                DOCK_TOP_Z + 0.08,
                "AA_Emissive_Engine",
            )

    # feux d'approche de part et d'autre du talon
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(
            bm,
            (sx * (DOCK_HW1 + 0.10), DOCK_Y1 - 0.30, DOCK_TOP_Z + 0.10),
            (0.20, 0.40, 0.24),
            "AA_Emissive_Engine",
        )

    return ak.new_object("Citadel_Dock", bm)


# ==========================================================================
# Points d'attache et reperes de pieces
# ==========================================================================


def build_markers() -> list:
    """Empties exportes en `Node3D` cote Godot.

    Deux familles, dans un seul et meme mecanisme (le kit n'exporte qu'UN objet
    maille : voir le compte-rendu) :
      - les points d'attache fonctionnels exiges par le brief (`Core_Center`,
        `Muzzle_Battery_L/R`, `Dock_Entry`) ;
      - les reperes de pieces (`Core_Prism`, `Battery_L/R`, `Turret_01..06`,
        `Dock_Bay`), poses au barycentre reel de chaque piece.
    Toutes les positions sont **derivees de la geometrie**, jamais devinees.
    """
    points: list = []

    # --- points d'attache fonctionnels -----------------------------------
    core_y = (CORE[0][0] + CORE[-1][0]) * 0.5
    points.append(
        ak.attach_point("Core_Center", (0.0, core_y, (CORE_BASE_Z + CORE_TOP_Z) * 0.5))
    )

    # bouche des canons principaux : dans l'axe du tube externe, au ras de la levre
    d_main, tip_main = BARRELS[0]
    points += list(
        ak.attach_pair("Muzzle_Battery", ARM_X + d_main, tip_main - 0.05, BARREL_Z)
    )

    # entree de baie : au milieu de la rampe, sur sa surface
    points.append(
        ak.attach_point("Dock_Entry", (0.0, (DOCK_Y0 + DOCK_Y1) * 0.5, DOCK_TOP_Z + 0.10))
    )

    # --- reperes de pieces (nommage exige par le brief) -------------------
    points.append(ak.attach_point("Core_Prism", (0.0, core_y, CORE_MID_Z)))
    points += list(ak.attach_pair("Battery", ARM_X, -1.45, 0.0))
    points.append(
        ak.attach_point("Dock_Bay", (0.0, DOCK_Y0 + 0.20, DOCK_TOP_Z + 0.30))
    )
    for i, (x, y, z) in enumerate(TURRETS):
        points.append(ak.attach_point(f"Turret_{i + 1:02d}", (x, y, z + 0.52)))

    return points


# ==========================================================================
# Assemblage
# ==========================================================================


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_VANGUARD)

    parts = [
        build_core_hull(),
        build_arm(ak.PORT),
        build_arm(ak.STARBOARD),
        build_struts(),
        build_core_prism(),
        build_core_frame(),
        build_turrets(),
        build_bridge(),
        build_dock(),
    ]

    citadel = ak.join_objects(parts, "AegisCitadel")
    ak.cleanup(citadel)
    # Chanfrein a UN segment, large de 3 cm : deux fois moins que le creux des
    # panneaux (6 a 8 cm), donc la marche reste franche a la distance de jeu, et
    # les aretes du prisme accrochent la lumiere sans arrondir la silhouette.
    ak.bevel_sharp_edges(citadel, width=0.03, segments=1, angle_deg=34.0)
    ak.shade_smooth_by_angle(citadel, angle_deg=34.0)

    ak.export_hull(citadel, build_markers(), OUTPUT, CONTRACT)


if __name__ == "__main__":
    main()
