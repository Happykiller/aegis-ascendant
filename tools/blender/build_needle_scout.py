"""build_needle_scout.py — coque 3D du Needle Scout, ennemi leger (BRIEF-0022).

    blender45 -b -P tools/blender/build_needle_scout.py

Produit `assets/imported/models/ships/needle_scout.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (aucun alea) et s'auto-valide : `ak.export_hull()` relit le
`.glb` produit et echoue bruyamment si la bounding box, le budget de triangles,
les materiaux, le centrage du pivot ou les points d'attache sortent du contrat.

Reference de design : `assets/source/concepts/null_choir_enemy_families_sheet.png`,
**premiere famille** (rangee du haut) : un dard biconique, tres effile, symetrique,
plaques de carapace anthracite/violet, deux plaques ivoire a mi-corps, une fine
rainure d'energie magenta courant du nez a la poupe et s'ouvrant sur un noyau-oeil
dorsal, et deux ailettes arriere en fleche.

PARTI PRIS DE PRODUCTION
========================
Le Needle Scout est instancie **en masse** : le budget est de 3 000 triangles, et
la lisibilite a 30 px de haut prime sur le detail. Trois consequences assumees :

1. La ligne d'energie n'est **pas** un inset pose apres coup, mais une rainure en V
   creusee dans la section elle-meme (2 sommets par anneau). Elle coute donc presque
   rien, elle est geometriquement reelle (l'ADR-0008 veut du detail par la geometrie),
   et elle ne degenere pas la ou les faces deviennent minuscules — pres du nez, un
   `inset_region` aurait produit des faces nulles.
2. Aucun greeble seme : a cette taille a l'ecran, un greeble est du bruit qui coute
   des triangles. Le detail est porte par les cassures de silhouette (chine, ailettes,
   rainure, noyau) — les seules choses qui restent lisibles reduites.
3. La poupe du concept est une pointe ; le brief exige une tuyere (`Engine_C`, depart
   de trainee). La pointe arriere est donc resolue en **petite tuyere effilee**
   (78 mm de diametre pour 1,90 m de long, levre ivoire, fond magenta) : la
   silhouette de dard est conservee, et la trainee a une origine physique.

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
    name="Needle Scout",
    width_x=0.65,       # Godot X
    length_z=1.90,      # Godot Z
    max_height_y=0.30,  # Godot Y — plafond impose par le brief
    tri_budget=3_000,
    required_materials=ak.MATERIAL_ORDER,  # les 7 : cf. plan de materiaux ci-dessous
    required_attach_points=("Muzzle_C", "Engine_C"),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/ships/needle_scout.glb")

NOSE_Y = -0.950   # pointe du dard  (min Y auteur -> min Z Godot)
TAIL_Y = 0.950    # levre de tuyere (max Y auteur) — les deux fixent la longueur
HALF_W = 0.325    # bout d'ailette  — fixe la largeur

# ==========================================================================
# Tables de profil, relevees sur la vue de dessus de la planche
# ==========================================================================

# Demi-largeur de la coque. Bords d'attaque quasi rectilignes (c'est un dard),
# maitre-couple juste en arriere du milieu, puis effilement continu vers la poupe.
PLANFORM: list[tuple[float, float]] = [
    (-0.950, 0.007),   # pointe (voir NOSE_CAP : ce n'est volontairement pas 0)
    (-0.880, 0.022),
    (-0.780, 0.048),
    (-0.650, 0.079),
    (-0.500, 0.112),
    (-0.350, 0.145),
    (-0.200, 0.180),
    (-0.050, 0.212),
    (0.050, 0.228),
    (0.180, 0.230),    # maitre-couple
    (0.320, 0.212),
    (0.460, 0.180),
    (0.600, 0.142),
    (0.720, 0.104),
    (0.820, 0.068),
    (0.900, 0.032),    # jonction avec la tuyere
]

# Hauteur de la carene dorsale (z du sommet, sur l'axe).
CROWN: list[tuple[float, float]] = [
    (-0.950, 0.005),
    (-0.880, 0.016),
    (-0.780, 0.032),
    (-0.650, 0.050),
    (-0.500, 0.068),
    (-0.350, 0.084),
    (-0.200, 0.098),
    (-0.050, 0.110),
    (0.050, 0.115),    # point haut de la coque
    (0.180, 0.113),
    (0.320, 0.106),
    (0.460, 0.094),
    (0.600, 0.080),
    (0.720, 0.066),
    (0.820, 0.046),
    (0.900, 0.034),
]

# Profondeur du ventre (z du bas, sur l'axe ; negatif). Volontairement moins
# creuse que le dos : vu de dessus a 20 deg, c'est le dos qui porte la lecture.
BELLY: list[tuple[float, float]] = [
    (-0.950, -0.004),
    (-0.880, -0.012),
    (-0.780, -0.026),
    (-0.650, -0.040),
    (-0.500, -0.054),
    (-0.350, -0.066),
    (-0.200, -0.078),
    (-0.050, -0.088),
    (0.050, -0.092),
    (0.180, -0.090),
    (0.320, -0.084),
    (0.460, -0.074),
    (0.600, -0.062),
    (0.720, -0.052),
    (0.820, -0.037),
    (0.900, -0.030),
]

# Demi-largeur de la rainure d'energie dorsale. Le brief demande une **fine**
# ligne : au maitre-couple, la rainure fait 28 mm de levre a levre pour 460 mm de
# coque (6 %). Elle ne s'ouvre en losange qu'autour du noyau (y ~ +0.05), comme
# sur la planche, puis se referme en filet jusqu'a la tuyere.
CREST: list[tuple[float, float]] = [
    (-0.950, 0.003),
    (-0.860, 0.007),
    (-0.600, 0.011),
    (-0.300, 0.014),
    (-0.100, 0.024),
    (0.050, 0.042),    # noyau
    (0.200, 0.026),
    (0.400, 0.017),
    (0.650, 0.013),
    (0.900, 0.010),
]

GROOVE_DEPTH = 0.014   # enfoncement de la rainure sous la levre dorsale

#: Stations longitudinales. La premiere n'est **pas** une pointe geometrique
#: mais une minuscule section (cf. `NOSE_CAP`).
STATIONS: list[float] = [
    -0.950, -0.910, -0.860, -0.800, -0.720, -0.630, -0.530, -0.420,
    -0.310, -0.200, -0.100, 0.000, 0.100, 0.200, 0.320, 0.450,
    0.580, 0.700, 0.810, 0.900,
]

# NEZ — pourquoi une micro-section et non une pointe (`fan_to_point`)
# --------------------------------------------------------------------------
# Le nez se termine par une section de 14 x 9 mm, fermee par une n-gon. Ce n'est
# pas de la coquetterie : sur un dard aussi acere, un `bevel` applique a un sommet
# ou convergent douze aretes quasi paralleles s'echappe le long de l'axe
# (l'etendue d'un biseau de sommet varie en 1/sin(angle entre aretes)) et remplace
# la pointe par une **bille** noire de 2 a 3 cm. La lecture de dard est detruite,
# et aucun controle du contrat ne s'en apercoit : la bounding box n'y perdait que
# 6 mm, tres en deca des +/-3 %. Seul un rendu de controle l'a montre.
# Une micro-section rend l'angle entre aretes sain : le biseau n'y produit qu'un
# chanfrein de 4 mm, invisible en jeu, et la pointe reste une pointe.

# --- Ailettes arriere (plan, cote babord ; le cote tribord est symetrique) ---
# (x, y, demi-epaisseur). Fleche arriere marquee ; le bout d'ailette (B) porte
# la largeur hors-tout de la coque.
FIN: list[tuple[float, float, float]] = [
    (0.190, 0.200, 0.022),   # A — emplanture, bord d'attaque (noyee dans la coque)
    (HALF_W, 0.520, 0.006),  # B — bout d'ailette avant  -> LARGEUR MAX
    (0.300, 0.700, 0.006),   # C — bout d'ailette arriere
    (0.100, 0.620, 0.020),   # D — emplanture, bord de fuite (noyee dans la coque)
]

# --- Noyau-oeil dorsal : (rayon, z, materiau de la bande sortante) ------------
CORE_Y = 0.050
CORE: list[tuple[float, float, str]] = [
    (0.062, 0.104, "AA_Greeble"),          # assise, noyee dans la carene
    (0.052, 0.124, "AA_Trim"),             # socle
    (0.038, 0.128, "AA_Glass"),            # lunette ivoire -> membrane
    (0.024, 0.126, "AA_Emissive_Engine"),  # membrane sombre -> pupille
    (0.012, 0.134, "AA_Emissive_Engine"),  # pupille magenta
]
CORE_SEGMENTS = 10

# --- Tuyere : (y, rayon, materiau du segment sortant) -------------------------
NOZZLE_Z = 0.002       # axe, centre sur la section de coque a y = 0.90
NOZZLE_SEGMENTS = 12
NOZZLE: list[tuple[float, float, str]] = [
    (0.855, 0.000, "AA_Greeble"),          # pole avant, noye dans la coque
    (0.868, 0.036, "AA_Greeble"),
    (0.930, 0.039, "AA_Greeble"),
    (0.950, 0.033, "AA_Trim"),             # levre ivoire — POUPE (bbox)
    (0.944, 0.024, "AA_Emissive_Engine"),
    (0.900, 0.019, "AA_Emissive_Engine"),
    (0.896, 0.000, "AA_Emissive_Engine"),  # fond lumineux
]

MUZZLE_Y = -0.955      # bouche de tir : 5 mm devant la pointe, sur l'axe


# ==========================================================================
# Interpolation
# ==========================================================================


def lerp_table(table: list[tuple[float, float]], y: float) -> float:
    """Interpolation lineaire d'une table (y, valeur), extremites clampees.

    Lineaire par morceaux, comme sur le Specter-9 : une spline arrondirait les
    cassures de bord d'attaque qui font justement la silhouette de dard.
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


def section(y: float) -> tuple[float, float, float, float, float]:
    """(demi-largeur, carene, ventre, demi-rainure, profondeur de rainure)."""
    w = lerp_table(PLANFORM, y)
    c = lerp_table(CROWN, y)
    b = lerp_table(BELLY, y)
    # La rainure ne peut pas etre plus large que la coque ni plus profonde que
    # la carene : sans ces bornes, le nez (ou w et c tendent vers 0) se retourne.
    s = min(lerp_table(CREST, y), 0.42 * w)
    g = min(GROOVE_DEPTH, 0.35 * c)
    return w, c, b, s, g


# --------------------------------------------------------------------------
# Section transverse : 12 sommets, indices de faces stables
# --------------------------------------------------------------------------
#
#            v3 ---- v4          rainure (magenta, creusee)
#          v2 \      / v5
#        v1  /  ‾‾‾‾  \  v6      epaules dorsales (carapace violette)
#     v0 -------------------- v7  chine (arete vive : la ligne de lecture)
#        v11 \        / v8
#            v10 -- v9          ventre (quille anthracite)
#
# `bridge_rings` produit la face `i` entre les sommets `i` et `i+1`.

F_SHOULDER = (1, 5)      # epaules dorsales (panneaux violets)
F_GROOVE = (2, 3, 4)     # parois + fond de la rainure d'energie
F_FLANK = (0, 6)         # flancs superieurs (plaques ivoire a mi-corps)
F_BELLY_Q = (8, 10)      # quartiers de ventre
F_KEEL = (9,)            # quille centrale


def ring_points(y: float) -> list[tuple[float, float, float]]:
    w, c, b, s, g = section(y)
    sh = (w + s) * 0.55          # x des epaules dorsales
    return [
        (w, y, 0.0),             # v0  chine babord
        (sh, y, c * 0.72),       # v1  epaule babord
        (s, y, c),               # v2  levre de rainure babord
        (s * 0.45, y, c - g),    # v3  fond de rainure babord
        (-s * 0.45, y, c - g),   # v4  fond de rainure tribord
        (-s, y, c),              # v5  levre de rainure tribord
        (-sh, y, c * 0.72),      # v6  epaule tribord
        (-w, y, 0.0),            # v7  chine tribord
        (-w * 0.62, y, b * 0.74),  # v8
        (-w * 0.22, y, b),       # v9  quille tribord
        (w * 0.22, y, b),        # v10 quille babord
        (w * 0.62, y, b * 0.74),  # v11
    ]


# ==========================================================================
# Coque
# ==========================================================================


def build_hull() -> object:
    bm = bmesh.new()

    rings = [ak.add_ring(bm, ring_points(y)) for y in STATIONS]

    # Nez : n-gon de 14 x 9 mm (cf. NOSE_CAP), pas un eventail vers un sommet.
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Trim")

    bands: list[list] = []
    band_y: list[float] = []
    for i in range(len(rings) - 1):
        bands.append(ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull"))
        band_y.append((STATIONS[i] + STATIONS[i + 1]) * 0.5)
    ak.cap_ring(bm, list(reversed(rings[-1])), "AA_Greeble")

    def pick(y0: float, y1: float, faces: tuple[int, ...]) -> list:
        out = []
        for b, ym in enumerate(band_y):
            if y0 <= ym <= y1:
                for j in faces:
                    face = bands[b][j]
                    if face is not None and face.is_valid:
                        out.append(face)
        return out

    # --- rainure d'energie : magenta sur toute la longueur ---------------
    # Elle est deja creusee par la section (v3/v4) : il ne reste qu'a lui donner
    # son materiau. Zero triangle de plus, et elle ne peut pas degenerer au nez.
    ak.set_material(pick(-0.950, 0.900, F_GROOVE), "AA_Emissive_Engine")

    # --- carapace : plaques violettes enfoncees sur les epaules dorsales ---
    # Quatre plaques et non deux longues coulees : les joints anthracite entre
    # elles sont ce qui fait lire une *carapace segmentee* (le trait dominant du
    # Choeur Nul dans la charte §4) plutot qu'une carene peinte. Le budget le
    # permet largement, et un joint reste lisible la ou un greeble disparait.
    for y0, y1 in (
        (-0.780, -0.500),
        (-0.460, -0.150),
        (0.150, 0.400),
        (0.450, 0.770),
    ):
        ak.inset_panel(
            bm, pick(y0, y1, F_SHOULDER), "AA_Panel",
            thickness=0.006, depth=-0.007,
        )

    # --- plaques ivoire : les deux eclats clairs de la planche ------------
    # Enfoncees : la bordure reste anthracite, ce qui les fait lire comme des
    # plaques de carapace rapportees, et non comme une zone repeinte.
    ak.inset_panel(
        bm, pick(-0.210, 0.060, F_FLANK), "AA_Trim",
        thickness=0.008, depth=-0.005,
    )
    # lisere de bord d'attaque (le fil de la lame : deux pixels, mais c'est ce
    # qui fait exister la pointe quand le vaisseau est haut de 30 px)
    ak.set_material(pick(-0.950, -0.855, F_FLANK), "AA_Trim")

    # --- dessous : quille sombre, quartiers violets -----------------------
    ak.set_material(pick(-0.950, 0.900, F_KEEL), "AA_Greeble")
    ak.set_material(pick(-0.120, 0.600, F_BELLY_Q), "AA_Panel")

    return ak.new_object("NeedleScout_Hull", bm)


# ==========================================================================
# Detail : ailettes, noyau, tuyere, marquages
# ==========================================================================


def _fin(bm: bmesh.types.BMesh, sign: float) -> None:
    """Ailette arriere : prisme fin, tire du polygone de plan `FIN`."""
    top = ak.add_ring(bm, [(sign * x, y, t) for x, y, t in FIN])
    bot = ak.add_ring(bm, [(sign * x, y, -t) for x, y, t in FIN])
    faces = ak.bridge_rings(bm, top, bot, "AA_Hull")
    # face 0 = A->B : le bord d'attaque, coiffe d'ivoire comme sur la planche.
    ak.set_material([faces[0]], "AA_Trim")
    ak.cap_ring(bm, list(reversed(top)), "AA_Panel")
    ak.cap_ring(bm, bot, "AA_Panel")


def _disc_stack(
    bm: bmesh.types.BMesh,
    center: tuple[float, float],
    profile: list[tuple[float, float, str]],
    segments: int,
) -> None:
    """Empilement d'anneaux coaxiaux a l'axe Z : le noyau-oeil dorsal.

    `add_lathe` du kit tourne autour de l'axe Y (tuyeres, canons) ; un oeil pose
    sur le dos tourne, lui, autour de Z. Cette variante locale reste dans le kit
    au sens ou elle n'utilise que ses primitives (`add_ring`, `bridge_rings`,
    `cap_ring`, `fan_to_point`) — elle ne le modifie pas.
    """
    cx, cy = center
    rings = []
    for radius, z, _ in profile:
        rings.append(
            ak.add_ring(
                bm,
                [
                    (
                        cx + radius * math.cos(2.0 * math.pi * s / segments),
                        cy + radius * math.sin(2.0 * math.pi * s / segments),
                        z,
                    )
                    for s in range(segments)
                ],
            )
        )
    for i in range(len(rings) - 1):
        ak.bridge_rings(bm, rings[i], rings[i + 1], profile[i][2])
    ak.cap_ring(bm, rings[-1], profile[-1][2])


def build_details() -> object:
    bm = bmesh.new()

    for sign in (ak.PORT, ak.STARBOARD):
        _fin(bm, sign)

    _disc_stack(bm, (0.0, CORE_Y), CORE, CORE_SEGMENTS)

    ak.add_lathe(bm, NOZZLE, NOZZLE_SEGMENTS, center_x=0.0, center_z=NOZZLE_Z)

    # Marquages vert maladif (`AA_Marking_Red` porte le vert du Choeur Nul) :
    # deux events d'echappement sur les epaules arriere. Le premier jet les
    # faisait de 46 x 110 mm : deux dalles vert vif qui volaient la vedette a la
    # ligne magenta. La charte §3 dit « usage tres limite » — ils font desormais
    # 22 x 62 mm, une mouche sur chaque epaule.
    for sign in (ak.PORT, ak.STARBOARD):
        ak.add_box(
            bm, (sign * 0.120, 0.430, 0.060), (0.022, 0.062, 0.012),
            "AA_Marking_Red",
        )

    return ak.new_object("NeedleScout_Details", bm)


# ==========================================================================
# Points d'attache (derives de la geometrie, jamais devines)
# ==========================================================================


def build_attach_points() -> list:
    return [
        # bouche de tir : sur l'axe, juste devant la pointe du dard.
        ak.attach_point("Muzzle_C", (0.0, MUZZLE_Y, 0.0)),
        # tuyere : centre du plan de sortie (origine de la trainee).
        ak.attach_point("Engine_C", (0.0, TAIL_Y - 0.004, NOZZLE_Z)),
    ]


# ==========================================================================
# Assemblage
# ==========================================================================


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)

    ship = ak.join_objects([build_hull(), build_details()], "NeedleScout")
    ak.cleanup(ship)
    # Chanfrein a 1 segment et seuil eleve (38 deg) : sur un budget de 3 000
    # triangles, on ne paie que les aretes qui portent la silhouette (chine,
    # levres de rainure, ailettes, levre de tuyere). Les raccords doux de la
    # carene restent nets grace au lissage par angle.
    ak.bevel_sharp_edges(ship, width=0.004, segments=1, angle_deg=38.0)
    ak.shade_smooth_by_angle(ship, angle_deg=38.0)

    ak.export_hull(ship, build_attach_points(), OUTPUT, CONTRACT)


if __name__ == "__main__":
    main()
