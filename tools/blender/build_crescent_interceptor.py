"""build_crescent_interceptor.py — coque 3D du Crescent Interceptor (BRIEF-0029).

    blender45 -b -P tools/blender/build_crescent_interceptor.py

Produit `assets/imported/models/ships/crescent_interceptor.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (aucun alea non seede) et s'auto-valide : `ak.export_hull()`
relit le `.glb` produit et echoue bruyamment si la bounding box, le budget de
triangles, les materiaux, le centrage du pivot ou les points d'attache sortent
du contrat.

Reference de design : `assets/source/references/reference_asset_overview_board.png`,
panneau ENNEMIS, rangee du haut, 2e vignette (« CRESCENT INTERCEPTOR ») : fuselage
central etroit et cranté, deux longerons lateraux termines par des tuyeres, et deux
lames laterales balayant vers l'avant. On transpose l'intention (ADR-0009), jamais
le coloris : la reference est grise a reacteurs bleus, la coque livree porte la
palette antagoniste du Choeur Nul (anthracite / violet / ivoire / magenta).

CE QUI L'OPPOSE AU NEEDLE SCOUT (le seul critere qui compte, cf. brief)
======================================================================
Le Needle Scout est un dard mono-bloc : 0,65 x 1,90 m, un seul volume effile,
une pointe. Le Crescent Interceptor est son contraire exact, par construction :

1. **Proportions inversees** : 1,10 x 1,60 m — presque deux fois plus large, plus
   court. A 30 px de haut, c'est le rapport largeur/longueur qui se lit en premier,
   avant tout detail.
2. **Silhouette ajouree** : trois masses separees par du vide (fuselage + deux
   longerons) la ou le Scout n'en a qu'une. Le vide est un trait de silhouette
   aussi fort qu'une arete.
3. **Deux arcs en croissant** ouverts vers l'avant, soulignes d'une gorge magenta
   sur leur face SUPERIEURE : vu de dessus, la coque dessine deux parentheses
   lumineuses « ( ) » autour du fuselage. Le Scout, lui, ne montre qu'un trait
   axial unique.

OU VIT LE DETAIL (contrainte de lisibilite, pas de gout)
========================================================
La camera de jeu est a 20 deg de la verticale : on voit ces coques quasiment de
dessus. Tout l'emissif et tous les panneaux d'accent sont donc poses sur des
surfaces **superieures** (gorges dorsales, dessus des longerons, dessus des lames).
Les tuyeres gardent un fond magenta, mais il n'est PAS compte comme de l'emissif
lisible : c'est le defaut releve sur le Specter-9 (BRIEF-0026). La lecture
lumineuse en jeu vient des gorges dorsales, qui, elles, regardent la camera.

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
# Contrat (BRIEF-0029 ; classe « ennemi leger » de l'ADR-0008)
# ==========================================================================

CONTRACT = ak.HullContract(
    name="Crescent Interceptor",
    width_x=1.10,       # Godot X — impose par le brief
    length_z=1.60,      # Godot Z — impose par le brief
    max_height_y=0.28,  # Godot Y — plafond impose par le brief
    tri_budget=3_000,   # meme budget « ennemi leger » que le Needle Scout
    required_materials=ak.MATERIAL_ORDER,
    required_attach_points=("Muzzle_C", "Engine_C", "Engine_L", "Engine_R"),
)

OUTPUT = os.path.join(
    _REPO, "assets/imported/models/ships/crescent_interceptor.glb"
)

NOSE_Y = -0.800    # pointe du fuselage    -> min Y auteur = min Z Godot
TAIL_Y = 0.800     # levre des tuyeres     -> max Y auteur
HALF_W = 0.550     # sommet de l'arc exterieur des lames -> largeur hors-tout

BOOM_X = 0.335     # entraxe des longerons (distance positive a l'axe)

# ==========================================================================
# Fuselage central — tables de profil
# ==========================================================================
# Volontairement etroit (0,226 m au maitre-couple pour 1,10 m hors-tout, soit
# 21 %) : c'est ce qui laisse lire les deux longerons comme des masses separees
# et non comme les bords d'une meme aile pleine.

PLANFORM: list[tuple[float, float]] = [
    (-0.800, 0.006),   # micro-section de nez (voir NOSE_CAP plus bas)
    (-0.740, 0.020),
    (-0.660, 0.038),
    (-0.560, 0.058),
    (-0.440, 0.078),
    (-0.300, 0.096),
    (-0.150, 0.108),
    (0.000, 0.113),    # maitre-couple
    (0.150, 0.110),
    (0.300, 0.100),
    (0.440, 0.086),
    (0.560, 0.070),
    (0.640, 0.056),
]

CROWN: list[tuple[float, float]] = [
    (-0.800, 0.004),
    (-0.740, 0.014),
    (-0.660, 0.030),
    (-0.560, 0.048),
    (-0.440, 0.066),
    (-0.300, 0.082),
    (-0.150, 0.092),
    (0.000, 0.096),    # point haut de la carene
    (0.150, 0.094),
    (0.300, 0.088),
    (0.440, 0.078),
    (0.560, 0.066),
    (0.640, 0.056),
]

# Ventre nettement moins creuse que le dos : a 20 deg de la verticale, le joueur
# ne voit jamais le dessous — y depenser du volume serait payer des triangles
# pour rien et epaissir la coque en pure perte.
BELLY: list[tuple[float, float]] = [
    (-0.800, -0.003),
    (-0.740, -0.010),
    (-0.660, -0.022),
    (-0.560, -0.036),
    (-0.440, -0.048),
    (-0.300, -0.058),
    (-0.150, -0.066),
    (0.000, -0.070),
    (0.150, -0.068),
    (0.300, -0.064),
    (0.440, -0.056),
    (0.560, -0.046),
    (0.640, -0.038),
]

# Demi-largeur de la rainure d'energie dorsale (creusee dans la section
# elle-meme, pas insetee : gratuite en triangles et incapable de degenerer pres
# du nez). Volontairement etroite : au premier rendu, une rainure de 56 mm de
# levre a levre entierement peinte en magenta donnait un ruban rose qui volait
# la vedette a tout le reste. Elle fait desormais 30 mm au plus large, et seul
# son *fond* est emissif — les deux parois restent anthracite.
CREST: list[tuple[float, float]] = [
    (-0.800, 0.003),
    (-0.640, 0.006),
    (-0.400, 0.009),
    (-0.150, 0.012),
    (0.050, 0.015),
    (0.300, 0.012),
    (0.640, 0.008),
]

GROOVE_DEPTH = 0.013

# Stations serrees a l'avant (la courbure du nez s'y joue et c'est ce que le
# joueur voit venir), lâches a l'arriere : les deux stations supprimees pour
# tenir le budget de 3 000 triangles l'ont ete la, ou la carene est quasi
# rectiligne et ou rien ne se perd.
STATIONS: list[float] = [
    -0.800, -0.760, -0.710, -0.650, -0.570, -0.480, -0.380, -0.270,
    -0.150, -0.030, 0.090, 0.330, 0.450, 0.640,
]

# NEZ — pourquoi une micro-section et non une pointe (`fan_to_point`)
# --------------------------------------------------------------------------
# Lecon acquise sur le Needle Scout : biseauter un sommet ou convergent douze
# aretes quasi paralleles fait « exploser » le biseau le long de l'axe et
# remplace la pointe par une bille noire de 2-3 cm. La bounding box n'y voit
# rien (6 mm de perte, tres en deca des +/-3 %). On termine donc le nez par une
# section de 12 x 8 mm fermee en n-gon : l'angle entre aretes redevient sain.

# --------------------------------------------------------------------------
# Section transverse du fuselage : 12 sommets, indices de faces stables
# --------------------------------------------------------------------------
#
#            v3 ---- v4          rainure d'energie (magenta, creusee)
#          v2 \      / v5
#        v1  /  ‾‾‾‾  \  v6      epaules dorsales (verriere / carapace)
#     v0 -------------------- v7  chine (arete vive : la ligne de lecture)
#        v11 \        / v8
#            v10 -- v9          ventre
#
# `bridge_rings` produit la face `i` entre les sommets `i` et `i+1`.

F_SHOULDER = (1, 5)      # epaules dorsales — SURFACE VUE PAR LE JOUEUR
F_GROOVE_WALL = (2, 4)   # parois de la rainure (restent anthracite)
F_GROOVE = (3,)          # fond de la rainure d'energie — le seul emissif axial
F_FLANK = (0, 6)         # flancs superieurs
F_BELLY_Q = (8, 10)
F_KEEL = (9,)


def lerp_table(table: list[tuple[float, float]], y: float) -> float:
    """Interpolation lineaire d'une table (y, valeur), extremites clampees.

    Lineaire par morceaux et non splinee : une spline arrondirait les cassures
    de section qui font justement la lecture « carapace segmentee ».
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


def fuselage_section(y: float) -> tuple[float, float, float, float, float]:
    """(demi-largeur, carene, ventre, demi-rainure, profondeur de rainure)."""
    w = lerp_table(PLANFORM, y)
    c = lerp_table(CROWN, y)
    b = lerp_table(BELLY, y)
    # Bornes indispensables : sans elles, la rainure devient plus large que la
    # coque (ou plus profonde que la carene) pres du nez, et la section se
    # retourne sur elle-meme.
    s = min(lerp_table(CREST, y), 0.42 * w)
    g = min(GROOVE_DEPTH, 0.35 * c)
    return w, c, b, s, g


def fuselage_ring(y: float) -> list[tuple[float, float, float]]:
    w, c, b, s, g = fuselage_section(y)
    sh = (w + s) * 0.55
    return [
        (w, y, 0.0),               # v0  chine babord
        (sh, y, c * 0.74),         # v1  epaule babord
        (s, y, c),                 # v2  levre de rainure babord
        (s * 0.45, y, c - g),      # v3  fond de rainure babord
        (-s * 0.45, y, c - g),     # v4  fond de rainure tribord
        (-s, y, c),                # v5  levre de rainure tribord
        (-sh, y, c * 0.74),        # v6  epaule tribord
        (-w, y, 0.0),              # v7  chine tribord
        (-w * 0.62, y, b * 0.74),  # v8
        (-w * 0.22, y, b),         # v9  quille tribord
        (w * 0.22, y, b),          # v10 quille babord
        (w * 0.62, y, b * 0.74),   # v11
    ]


def build_fuselage() -> object:
    bm = bmesh.new()

    rings = [ak.add_ring(bm, fuselage_ring(y)) for y in STATIONS]
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

    # --- ligne d'energie dorsale : magenta sur toute la longueur -----------
    # Deja creusee par la section (v3/v4) : il ne reste qu'a lui donner son
    # materiau. Zero triangle supplementaire, et elle regarde la camera.
    ak.set_material(pick(NOSE_Y, 0.640, F_GROOVE), "AA_Emissive_Engine")
    ak.set_material(pick(NOSE_Y, 0.640, F_GROOVE_WALL), "AA_Greeble")

    # --- verriere/capteur : bandeau vitre sur les epaules avant ------------
    # Enfonce, donc borde d'anthracite : il lit comme une membrane encastree
    # dans la carapace et non comme une zone repeinte.
    ak.inset_panel(
        bm, pick(-0.480, -0.200, F_SHOULDER), "AA_Glass",
        thickness=0.006, depth=-0.005,
    )

    # --- carapace segmentee : plaques enfoncees sur les epaules dorsales ----
    # Trois plaques courtes plutot qu'une longue coulee : les joints anthracite
    # entre elles sont ce qui fait lire une carapace *segmentee* (charte §4).
    # Une seule est violette : le violet du kit remonte tres clair sous la key
    # light, et trois plaques d'affilee faisaient du dos du fuselage un ruban
    # lavande. Les deux autres sont creusees en anthracite sombre — meme relief,
    # pas de tache de couleur.
    for y0, y1, mat in (
        (-0.150, 0.060, "AA_Greeble"),
        (0.100, 0.300, "AA_Panel"),
        (0.340, 0.600, "AA_Greeble"),
    ):
        ak.inset_panel(
            bm, pick(y0, y1, F_SHOULDER), mat,
            thickness=0.006, depth=-0.006,
        )

    # --- lisere ivoire de bord d'attaque -----------------------------------
    # Deux pixels a l'ecran, mais c'est ce qui fait exister la pointe quand la
    # coque est haute de 30 px.
    ak.set_material(pick(NOSE_Y, -0.700, F_FLANK), "AA_Trim")
    ak.inset_panel(
        bm, pick(0.150, 0.420, F_FLANK), "AA_Trim",
        thickness=0.007, depth=-0.004,
    )

    # --- dessous (jamais vu en jeu : traite au minimum) ---------------------
    ak.set_material(pick(NOSE_Y, 0.640, F_KEEL), "AA_Greeble")
    ak.set_material(pick(-0.200, 0.500, F_BELLY_Q), "AA_Panel")

    return ak.new_object("CrescentInterceptor_Fuselage", bm)


# ==========================================================================
# Longerons lateraux — profil et section
# ==========================================================================
# Poutre effilee vers l'avant, epaisse a l'arriere ou elle porte la tuyere.

# (y, demi-largeur, carene, ventre)
BOOM_PROFILE: list[tuple[float, float, float, float]] = [
    (-0.170, 0.010, 0.008, -0.007),
    (-0.080, 0.030, 0.026, -0.020),
    (0.020, 0.046, 0.040, -0.032),
    (0.140, 0.056, 0.050, -0.040),
    (0.280, 0.062, 0.056, -0.046),
    (0.410, 0.063, 0.058, -0.048),
    (0.530, 0.060, 0.056, -0.047),
    (0.630, 0.056, 0.052, -0.045),
    (0.700, 0.052, 0.048, -0.043),
]

#: Derive de `BOOM_PROFILE` : deux listes independantes finiraient par diverger.
BOOM_STATIONS: list[float] = [row[0] for row in BOOM_PROFILE]

# Section octogonale du longeron : 8 sommets, indices de faces stables.
#            u2                dessus (surface vue par le joueur)
#        u3      u1
#     u4            u0         flancs (invisibles en jeu)
#        u5      u7
#            u6                dessous
B_TOP_OUT = 1    # dessus, moitie exterieure -> plaques ivoire
B_TOP_IN = 2     # dessus, moitie interieure -> gorge magenta / panneaux


def boom_ring(
    sign: float, y: float, w: float, c: float, b: float
) -> list[tuple[float, float, float]]:
    cx = sign * BOOM_X
    return [
        (cx + sign * w, y, 0.0),
        (cx + sign * w * 0.60, y, c * 0.86),
        (cx, y, c),
        (cx - sign * w * 0.60, y, c * 0.86),
        (cx - sign * w, y, 0.0),
        (cx - sign * w * 0.60, y, b * 0.86),
        (cx, y, b),
        (cx + sign * w * 0.60, y, b * 0.86),
    ]


def _boom(bm: bmesh.types.BMesh, sign: float) -> None:
    rings = [
        ak.add_ring(bm, boom_ring(sign, y, w, c, b))
        for y, w, c, b in BOOM_PROFILE
    ]
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Trim")

    bands: list[list] = []
    band_y: list[float] = []
    for i in range(len(rings) - 1):
        bands.append(ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull"))
        band_y.append((BOOM_STATIONS[i] + BOOM_STATIONS[i + 1]) * 0.5)
    ak.cap_ring(bm, list(reversed(rings[-1])), "AA_Greeble")

    def pick(y0: float, y1: float, index: int) -> list:
        out = []
        for b, ym in enumerate(band_y):
            if y0 <= ym <= y1:
                face = bands[b][index]
                if face is not None and face.is_valid:
                    out.append(face)
        return out

    # Gorge d'energie magenta courant sur le dessus du longeron : deuxieme axe
    # lumineux vu par le joueur. Interrompue a mi-longueur (deux troncons au
    # lieu d'une coulee continue) : la coupure fait lire une carapace segmentee,
    # et divise par deux la surface rose — le premier rendu en avait trop.
    for y0, y1 in ((0.000, 0.220), (0.330, 0.600)):
        ak.inset_panel(
            bm, pick(y0, y1, B_TOP_IN), "AA_Emissive_Engine",
            thickness=0.014, depth=-0.007,
        )
    # Panneaux d'accent (brief) : dessus des longerons uniquement. Un seul
    # violet, encadre de deux panneaux sourds — meme raison qu'ailleurs.
    ak.inset_panel(
        bm, pick(-0.080, 0.200, B_TOP_OUT), "AA_Greeble",
        thickness=0.007, depth=-0.005,
    )
    ak.inset_panel(
        bm, pick(0.340, 0.480, B_TOP_OUT), "AA_Trim",
        thickness=0.007, depth=-0.005,
    )
    ak.inset_panel(
        bm, pick(0.480, 0.660, B_TOP_OUT), "AA_Panel",
        thickness=0.007, depth=-0.005,
    )


# ==========================================================================
# Lames en croissant — LA signature de la silhouette
# ==========================================================================
# Deux polylignes de meme longueur : le bord de fuite exterieur (convexe, il
# porte la largeur hors-tout) et le bord d'attaque interieur (concave). Les deux
# se rejoignent presque en corne arriere et en corne avant.
#
# DEUX JETS REJETES AU RENDU (planche 4 vues), et la lecon vaut d'etre ecrite :
#
#   1er jet — rails quasi paralleles a l'axe, 120 mm d'ecart : la lame lisait
#     comme une quatrieme echarde. La coque montrait cinq pointes paralleles.
#   2e jet — on a repondu en ELARGISSANT la lame (220 mm de corde). Erreur de
#     diagnostic : une lame large ne lit pas « croissant », elle lit « feuille ».
#
# Ce qui fait un croissant n'est ni la finesse ni la largeur, c'est la COURBURE :
# il faut que l'arc balaie franchement en X et que le bord interieur soit
# reellement concave (bombant vers l'exterieur en son milieu, au-dela de la corde
# qui joint ses deux extremites). D'ou le trace ci-dessous : talon ancre sur le
# longeron a x = 0,35, ventre pousse a x = 0,55, pointe qui revient a x = 0,25
# pres de l'axe. Balayage lateral de 300 mm pour une lame de 100 mm de large :
# vu de dessus, les deux lames dessinent une parenthese « ( ) » autour du
# fuselage — une forme qu'aucun dard mono-bloc ne peut imiter.
#
# Les extremites ne sont PAS des pointes exactes : une corne strictement fermee
# produirait des sections degenerees et, apres biseautage, la meme « bille » que
# celle observee au nez du Needle Scout.

CRESCENT_OUT: list[tuple[float, float]] = [
    (0.352, 0.420),     # talon, noye dans le longeron
    (0.452, 0.318),
    (0.520, 0.180),
    (0.548, 0.010),
    (HALF_W, -0.100),   # ventre de l'arc -> LARGEUR HORS-TOUT
    (0.520, -0.280),
    (0.440, -0.440),
    (0.330, -0.560),
    (0.253, -0.638),    # pointe, ramenee vers l'axe : elle « referme » l'arc
]

CRESCENT_IN: list[tuple[float, float]] = [
    (0.330, 0.400),
    (0.398, 0.300),
    (0.428, 0.180),
    (0.443, 0.020),
    (0.437, -0.110),
    (0.408, -0.250),
    (0.345, -0.390),
    (0.268, -0.500),
    (0.245, -0.632),
]

# Demi-epaisseur de la lame, station par station (mince : c'est une lame).
CRESCENT_H: list[float] = [
    0.008, 0.020, 0.025, 0.026, 0.026, 0.023, 0.018, 0.012, 0.005,
]

CRESCENT_Z = 0.010   # la lame vole legerement au-dessus du plan median

#: Abscisses le long de la corde (0 = bord exterieur, 1 = bord interieur) des
#: rails intermediaires de la section. La gorge emissive occupe l'intervalle
#: [0.72, 0.92] : 20 % d'une corde de 100 mm, soit un filet de 20 mm. Au premier
#: rendu elle en occupait la moitie et la lame entiere paraissait rose.
C_RAILS = (0.25, 0.72, 0.92)

# Section transverse de la lame : 8 sommets.
#        w1 --------- w2 -w3      dessus ; w2->w3 = gorge magenta (face camera)
#     w0                     w4   bords minces
#        w6 --------- w5          dessous (jamais vu en jeu)
C_TOP_OUT = 1    # dessus principal -> plaques ivoire / violettes
C_TOP_IN = 2     # gorge d'energie


def _crescent(bm: bmesh.types.BMesh, sign: float) -> None:
    rings = []
    for i, ((xo, yo), (xi, yi)) in enumerate(zip(CRESCENT_OUT, CRESCENT_IN)):
        h = CRESCENT_H[i]

        def at(t: float) -> tuple[float, float]:
            return (xo + (xi - xo) * t, yo + (yi - yo) * t)

        a, b, c = (at(t) for t in C_RAILS)
        rings.append(
            ak.add_ring(
                bm,
                [
                    (sign * xo, yo, CRESCENT_Z),
                    (sign * a[0], a[1], CRESCENT_Z + h),
                    (sign * b[0], b[1], CRESCENT_Z + h * 0.86),
                    (sign * c[0], c[1], CRESCENT_Z + h * 0.60),
                    (sign * xi, yi, CRESCENT_Z),
                    (sign * b[0], b[1], CRESCENT_Z - h * 0.52),
                    (sign * a[0], a[1], CRESCENT_Z - h * 0.78),
                ],
            )
        )

    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")

    bands: list[list] = []
    for i in range(len(rings) - 1):
        bands.append(ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull"))
    ak.cap_ring(bm, rings[-1], "AA_Trim")

    def pick(i0: int, i1: int, index: int) -> list:
        out = []
        for b in range(i0, i1):
            face = bands[b][index]
            if face is not None and face.is_valid:
                out.append(face)
        return out

    # Gorge magenta suivant le bord d'attaque interieur : vue de dessus, c'est
    # elle qui trace l'arc. Sans elle le croissant existe en geometrie mais
    # s'eteint a 30 px, faute de contraste avec le fond spatial.
    ak.inset_panel(
        bm, pick(1, 7, C_TOP_IN), "AA_Emissive_Engine",
        thickness=0.004, depth=-0.004,
    )
    # Plaques ivoire sur le dessus de la lame : la seule grande valeur claire de
    # la coque, posee exactement la ou la camera de jeu la voit. Deux plaques
    # separees d'un joint anthracite (carapace segmentee, charte §4). Aucune
    # plaque violette ici : au 2e rendu, le violet du kit remonte tres clair sous
    # la key light et transformait la coque en machine lavande.
    ak.inset_panel(
        bm, pick(1, 4, C_TOP_OUT), "AA_Trim",
        thickness=0.008, depth=-0.004,
    )
    ak.inset_panel(
        bm, pick(5, 7, C_TOP_OUT), "AA_Trim",
        thickness=0.008, depth=-0.004,
    )


# ==========================================================================
# Liaison fuselage <-> longeron, tuyeres, greebles, marquages
# ==========================================================================

# Plaque de liaison (delta arriere). Contour en plan, cote babord. Ramenee vers
# l'arriere et retrecie apres le premier rendu : elle occupait alors le tiers de
# la surface vue, entierement en violet, et ecrasait tout le reste. Elle est
# desormais anthracite avec un petit panneau violet inset, et laisse le champ
# libre aux lames.
STRUT: list[tuple[float, float]] = [
    (0.055, 0.585),
    (BOOM_X, 0.585),
    (BOOM_X, 0.245),
    (0.080, 0.320),
]
STRUT_TOP = 0.028
STRUT_BOTTOM = -0.020

# Tuyere : (y, rayon, materiau du segment sortant). La levre ivoire porte la
# poupe de la coque (max Y auteur), donc la longueur hors-tout.
NOZZLE_SEGMENTS = 8
NOZZLE: list[tuple[float, float, str]] = [
    (0.660, 0.000, "AA_Greeble"),          # pole avant, noye dans le longeron
    (0.672, 0.050, "AA_Greeble"),
    (0.740, 0.055, "AA_Panel"),
    (0.782, 0.057, "AA_Greeble"),
    (TAIL_Y, 0.049, "AA_Trim"),            # levre ivoire — POUPE
    (0.792, 0.035, "AA_Emissive_Engine"),
    (0.762, 0.027, "AA_Emissive_Engine"),
    (0.758, 0.000, "AA_Emissive_Engine"),  # fond lumineux
]
NOZZLE_Z = 0.004

MUZZLE_Y = -0.806   # 6 mm devant la pointe du fuselage, sur l'axe


def _strut(bm: bmesh.types.BMesh, sign: float) -> None:
    top = ak.add_ring(bm, [(sign * x, y, STRUT_TOP) for x, y in STRUT])
    bot = ak.add_ring(bm, [(sign * x, y, STRUT_BOTTOM) for x, y in STRUT])
    ak.bridge_rings(bm, top, bot, "AA_Hull")
    cap = ak.cap_ring(bm, list(reversed(top)), "AA_Hull")
    if cap is not None:
        # DEUX insets emboites, et non un seul : la plaque de liaison est la
        # plus grande surface horizontale de la coque, donc celle que la camera
        # voit le mieux. Un inset unique y laissait une dalle violette de
        # 200 x 220 mm qui, au rendu, devenait la couleur dominante du vaisseau.
        # Le premier inset creuse une decoupe de panneau en anthracite, le
        # second n'accorde au violet qu'un timbre central.
        ak.inset_panel(bm, [cap], "AA_Hull", thickness=0.026, depth=-0.004)
        ak.inset_panel(bm, [cap], "AA_Panel", thickness=0.052, depth=-0.004)
    ak.cap_ring(bm, bot, "AA_Greeble")


def build_details() -> object:
    bm = bmesh.new()

    for sign in (ak.PORT, ak.STARBOARD):
        _boom(bm, sign)
        _crescent(bm, sign)
        _strut(bm, sign)
        ak.add_lathe(
            bm, NOZZLE, NOZZLE_SEGMENTS,
            center_x=sign * BOOM_X, center_z=NOZZLE_Z,
        )

    # Greebles sur le DESSUS des longerons (seule surface que la camera voit).
    # Seeds differents par cote : le Choeur Nul est asymetrique (charte §4), et
    # une dissymetrie de bruit mecanique s'obtient ici sans un triangle de plus
    # ni le moindre risque sur la bounding box.
    for sign, seed in ((ak.PORT, 2917), (ak.STARBOARD, 6043)):
        ak.greeble_strip(
            bm,
            (sign * BOOM_X, 0.100, 0.050),
            (sign * BOOM_X, 0.560, 0.048),
            count=3,
            seed=seed,
            size_range=(0.014, 0.026),
            height_range=(0.008, 0.016),
            jitter=0.005,
        )

    # `AA_Marking_Red` porte le vert maladif du Choeur Nul : la charte §3 en
    # prescrit un « usage tres limite ». Deux mouches d'echappement de 20 x 46 mm
    # posees a plat sur les longerons, de tailles legerement inegales.
    for sign, length in ((ak.PORT, 0.046), (ak.STARBOARD, 0.038)):
        ak.add_box(
            bm, (sign * (BOOM_X - 0.026), 0.610, 0.052),
            (0.020, length, 0.010), "AA_Marking_Red",
        )

    # Capteur axial : oeil magenta pose sur le dos du fuselage, juste devant le
    # bandeau vitre. C'est le point de mire de la coque en vue de dessus.
    _disc_stack(bm, (0.0, -0.520), SENSOR, SENSOR_SEGMENTS)

    return ak.new_object("CrescentInterceptor_Details", bm)


# --- Capteur dorsal : (rayon, z, materiau de la bande sortante) -------------
SENSOR: list[tuple[float, float, str]] = [
    (0.048, 0.058, "AA_Greeble"),
    (0.040, 0.078, "AA_Trim"),
    (0.028, 0.086, "AA_Glass"),
    (0.016, 0.090, "AA_Emissive_Engine"),
    (0.007, 0.094, "AA_Emissive_Engine"),
]
SENSOR_SEGMENTS = 9


def _disc_stack(
    bm: bmesh.types.BMesh,
    center: tuple[float, float],
    profile: list[tuple[float, float, str]],
    segments: int,
) -> None:
    """Empilement d'anneaux coaxiaux a l'axe Z (un oeil pose sur le dos).

    `ak.add_lathe` tourne autour de l'axe Y (tuyeres, canons) ; un capteur
    dorsal tourne, lui, autour de Z. Cette variante n'utilise que des primitives
    du kit (`add_ring`, `bridge_rings`, `cap_ring`) : elle ne le modifie pas.
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


# ==========================================================================
# Points d'attache (derives de la geometrie, jamais devines)
# ==========================================================================


def build_attach_points() -> list:
    points = [
        # Bouche de tir unique, sur l'axe, a la pointe du fuselage.
        ak.attach_point("Muzzle_C", (0.0, MUZZLE_Y, 0.0)),
        # Trainee centrale consommee par EnemyController : sur l'axe, au niveau
        # du plan de sortie des tuyeres, la ou les deux plumes se rejoignent.
        ak.attach_point("Engine_C", (0.0, TAIL_Y - 0.006, NOZZLE_Z)),
    ]
    # Tuyeres reelles, en bout de longeron. Non consommees aujourd'hui : posees
    # pour une double trainee ulterieure sans re-modelisation.
    points.extend(ak.attach_pair("Engine", BOOM_X, TAIL_Y - 0.006, NOZZLE_Z))
    return points


# ==========================================================================
# Assemblage
# ==========================================================================


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)

    ship = ak.join_objects(
        [build_fuselage(), build_details()], "CrescentInterceptor"
    )
    ak.cleanup(ship)
    # Le biseau est de TRES loin le premier poste de triangles : a 38 deg il
    # doublait la coque (1 443 -> 3 181, hors budget). Cette coque a beaucoup
    # plus de bords francs que le Needle Scout — trois volumes, deux lames,
    # neuf panneaux insetes — et chaque bord d'inset presente une arete a 90 deg.
    # Le seuil est donc porte a 50 deg : on ne paie plus que les aretes
    # reellement vives (chines, levres de gorge, bords de lame, levres de
    # tuyere), et les raccords doux de carene restent nets par le lissage.
    ak.bevel_sharp_edges(ship, width=0.004, segments=1, angle_deg=50.0)
    ak.shade_smooth_by_angle(ship, angle_deg=50.0)

    ak.export_hull(ship, build_attach_points(), OUTPUT, CONTRACT)


if __name__ == "__main__":
    main()
