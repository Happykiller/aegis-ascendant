"""build_aegis_citadel.py — coque 3D de l'Aegis Citadel, forteresse alliee.

    blender45 -b -P tools/blender/build_aegis_citadel.py

Produit `assets/imported/models/structures/aegis_citadel.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (aucun alea non seede) et s'auto-valide : `ak.export_hull()`
relit le `.glb` produit et echoue bruyamment si la bounding box, le budget de
triangles, les materiaux, le centrage du pivot ou les points d'attache sortent
du contrat.

Reference de design : `assets/reference/concepts/aegis_citadel_concept_sheet.png`.
Les tables ci-dessous sont relevees sur la grande vue de dessus de cette planche
(pixels -> metres, echelle 0,01445 m/px calee sur les deux cotes imposees par
l'ADR-0008 : 19,6 m d'envergure et 16,6 m de long).

Repere d'auteur (ADR-0008) : nez -Y, dessus +Z, **babord +X** (cf. aegis_kit).
Pour CETTE unite : les canons des bras-batteries pointent vers -Y (ils tirent
vers le haut de l'ecran) et la baie d'appontage s'ouvre vers +Y (cote joueur).

REFORGE BRIEF-0032 — ce qui a change par rapport a la premiere passe :
  * les UV sont depliees (`ak.box_project_uv`) : sans elles aucune texture
    n'etait applicable, c'etait LE verrou (ADR-0013) ;
  * les trois masses sont densifiees et surtout **decoupees en plaques
    irregulieres a joints visibles**, avec liseres or — la planche montre des
    dizaines de plaques la ou le modele n'avait que trois grands aplats ;
  * les tourelles **sortent du maillage** (elles bougent : `build_citadel_turret.py`)
    et ne laissent ici que leur socle + le marqueur d'ancrage ;
  * quatre canons par bras en deux paires superposees (au lieu de trois alignes) ;
  * la baie d'appontage est une **gorge reellement creusee** dans la face arriere,
    plus une boite emissive posee a plat ;
  * trois marqueurs `Beacon_01..03` pour les balises flottantes.

La citadelle est vue de deux facons : de tres loin en combat (la silhouette et
les trois masses priment) et **de trois quarts en gros plan sur l'ecran
d'accueil** (le pont superieur compte alors doublement). La regle d'ADR-0011 ne
bouge pas pour autant : ce qu'on pose sous la quille n'existe pas, donc la
quille reste sobre et le detail part sur le pont.
"""

from __future__ import annotations

import math
import os
import random
import sys

import bmesh

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402  (doit suivre l'ajout au sys.path)

# ==========================================================================
# Contrat (ADR-0008 pour X/Z, ADR-0011 pour la hauteur et le budget)
# ==========================================================================

CONTRACT = ak.HullContract(
    name="Aegis Citadel",
    width_x=19.60,      # Godot X — bout de bras a bout de bras (NORMATIF)
    length_z=16.60,     # Godot Z — bouche des canons a talon de la rampe (NORMATIF)
    max_height_y=5.60,  # Godot Y — plafond releve par ADR-0011 (etait 5,00)
    tri_budget=120_000,  # ADR-0011, classe « structure »
    required_materials=ak.MATERIAL_ORDER,  # les 7 : la planche les utilise tous
    required_attach_points=(
        "Core_Center",
        "Muzzle_Battery_L",
        "Muzzle_Battery_R",
        "Dock_Entry",
        "Core_Prism",
        "Battery_L",
        "Battery_R",
        "Dock_Bay",
        "Turret_01",
        "Turret_02",
        "Turret_03",
        "Turret_04",
        "Turret_05",
        "Turret_06",
        "Beacon_01",
        "Beacon_02",
        "Beacon_03",
    ),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/structures/aegis_citadel.glb")

SEED = 30250  # graine unique de la citadelle (determinisme des greebles/plaques)

HALF_W = CONTRACT.width_x / 2.0    # 9.80 — bord externe des bras
HALF_L = CONTRACT.length_z / 2.0   # 8.30 — bouche des canons / talon de rampe

# Une tuile de feuille de detail couvre 8,33 m de coque (1 / 0,12). Le Specter-9
# est a 4 tuiles/m parce qu'il mesure 2 m ; la citadelle en fait 19,6, et a la
# meme densite la feuille lit comme du bruit raye — l'echelle est le piege
# signale par le brief. A 0,12 la tuile porte a peu pres la taille d'un
# bras-batterie : elle module les grandes surfaces sans concurrencer les plaques
# geometriques, qui restent la source du detail lisible.
TEXELS_PER_METER = 0.12

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
#
# Ces neuf stations sont les SOMMETS de la silhouette : `densify()` en insere
# d'autres par interpolation lineaire, ce qui ne deplace aucun point de la
# surface (on subdivise des segments droits) mais donne les bandes ou decouper
# les plaques. Les cassures ne sont donc jamais lissees.
HULL: list[tuple[float, float, float, float]] = [
    (-7.60, 1.55, 0.78, -0.62),   # face de proue
    (-6.40, 2.95, 1.06, -1.02),   # cassure de proue (grande diagonale)
    (-5.40, 3.52, 1.16, -1.24),   # cassure d'epaule
    (-4.00, 3.75, 1.22, -1.38),   # largeur max atteinte
    (-1.00, 3.75, 1.24, -1.45),   # |
    (1.60, 3.75, 1.22, -1.42),    # +-- flanc parallele : le prisme
    (3.00, 3.45, 1.16, -1.28),    # cassure de hanche
    (4.30, 2.75, 1.08, -1.04),
    (5.60, 1.60, 0.94, -0.66),    # culasse arriere, percee par la gorge de baie
]
HULL_STEP = 0.34   # pas de densification (m)

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
ARM_STEP = 0.32

# Noyau cristallin : (y, demi-largeur). Prisme facette, pointes avant et
# arriere, assis en travers du pont du corps central. Volontairement enorme :
# 4,0 m de large et 7,0 m de long, soit 42 % de la longueur totale.
# ⚠️ Le plan du cristal est un HEXAGONE, pas une ellipse. Le premier jet
# echantillonnait un ovale : en vue de dessus le noyau se rendait comme un oeuf
# lumineux, quelle que soit la finesse des facettes. La planche montre deux
# aretes droites qui filent vers chaque pointe et un flanc parallele au milieu.
# Les stations intermediaires ci-dessous sont EXACTEMENT sur ces droites (elles
# ne servent qu'a porter les nervures) : la cassure est aux epaules, a -2,60 et
# -0,60.
CORE: list[tuple[float, float]] = [
    (-5.30, 0.000),  # pointe avant
    (-4.40, 0.660),  # |
    (-3.50, 1.320),  # +-- arete droite avant
    (-2.60, 1.980),  # epaule avant (cassure)
    (-1.60, 1.980),  # flanc parallele
    (-0.60, 1.980),  # epaule arriere (cassure)
    (0.20, 1.291),   # |
    (0.95, 0.646),   # +-- arete droite arriere
    (1.70, 0.000),   # pointe arriere
]
CORE_BASE_Z = 1.05   # assise, noyee dans le pont
CORE_TOP_Z = 3.70    # sommet — POINT LE PLUS HAUT DE LA COQUE
CORE_HW_MAX = 1.98
# Le sommet passe de 3,30 a 3,70 : ADR-0011 releve le plafond de hauteur a
# 5,60 m et la planche montre un cristal QUI DOMINE la forteresse, pas un
# bandeau pose sur le pont. La coque monte a ~5,3 m, il reste ~0,3 m de marge.

# Section du cristal, en coordonnees normalisees (u = x/demi-largeur,
# w = hauteur relative entre l'assise et le sommet). SEPT sommets : arete
# faitiere sur l'axe, deux pans de toit, deux epaulements, deux flancs, assise
# pincee. La planche montre un cristal a grandes facettes planes.
#
# ⚠️ Le nombre de facettes est contraint par le LISSAGE, pas par le gout : le
# maillage final passe a `shade_smooth_by_angle(34 deg)`. Une section a dix
# sommets donnait des aretes a ~30 deg entre facettes voisines — donc lissees,
# donc invisibles : le cristal se rendait comme une goutte blanche, exactement le
# defaut qu'on corrige. Sept sommets portent les memes 2,65 m de haut avec des
# angles de 36 a 90 deg : chaque arete reste VIVE. Moins de facettes, mais des
# facettes qui existent.
CORE_SECTION: list[tuple[float, float]] = [
    (0.00, 1.00),    # arete faitiere (sur l'axe)
    (-0.72, 0.74),   # pan de toit tribord
    (-1.00, 0.34),   # plus grande largeur tribord
    (-0.50, 0.00),   # assise tribord
    (0.50, 0.00),    # assise babord
    (1.00, 0.34),    # plus grande largeur babord
    (0.72, 0.74),    # pan de toit babord
]
#: Voies de nervure (u, w) : les aretes de taille que la planche souligne.
CORE_RIB_LANES: tuple[tuple[float, float], ...] = (
    (0.00, 1.00),
    (0.72, 0.74),
    (-0.72, 0.74),
)
#: Chaine de la table, du flanc babord au flanc tribord en passant par le faite.
#: Sert aux nervures EN TRAVERS (aretes de table).
CORE_TABLE_CHAIN: tuple[tuple[float, float], ...] = (
    (1.00, 0.34),
    (0.72, 0.74),
    (0.00, 1.00),
    (-0.72, 0.74),
    (-1.00, 0.34),
)

# Canons principaux : (offset lateral depuis l'axe du bras, y de la bouche, z).
# QUATRE tubes par bras en DEUX PAIRES SUPERPOSEES (la planche, encart des
# canons) : rangee haute avancee, rangee basse en retrait. Le tube haut externe
# est le plus long : c'est lui qui fixe la bbox en -Y et qui porte le point
# d'attache Muzzle_Battery_*.
BARREL_HI_Z = 1.34
BARREL_LO_Z = 0.74
BARRELS: list[tuple[float, float, float]] = [
    (0.55, -HALF_L, BARREL_HI_Z),   # haut externe — BOUCHE PRINCIPALE (bbox -Y)
    (-0.55, -8.14, BARREL_HI_Z),    # haut interne
    (1.00, -7.98, BARREL_LO_Z),     # bas externe
    (-1.00, -7.82, BARREL_LO_Z),    # bas interne
]
# La paire basse est ECARTEE de 45 cm par rapport a la haute, et non posee
# strictement dessous : deux paires exactement superposees ne font que DEUX
# tubes en vue de dessus, or la planche en montre bien quatre sur sa grande vue
# de dessus, en deux rangees d'altitude differente. L'ecart conserve
# l'empilement (visible de trois quarts et de face) tout en rendant les quatre
# bouches lisibles depuis la camera de jeu, qui regarde a 20 deg de la verticale.
BARREL_R = 0.215
BARREL_ROOT = -4.35   # culasse, dans le mantelet
BARREL_SEGMENTS = 10

# Tubes arriere (visibles sur la vue arriere de la planche) : plus courts.
AFT_BARRELS: list[float] = [0.70, -0.70]
AFT_TIP = 5.30
AFT_R = 0.24
AFT_Z = 0.10

# Socles de tourelle : (x, y). Le z d'assise est DERIVE du pont (voir
# `_deck_z`), il n'est plus recopie a la main. Les tourelles elles-memes ne font
# plus partie de ce maillage (BRIEF-0032 §2) : elles sont un modele a part,
# instancie par Godot sur les marqueurs `Turret_01..06`, qui sont poses
# exactement sur ce point d'assise.
TURRETS: list[tuple[float, float]] = [
    (2.00, -6.20),      # epaule avant babord
    (-2.00, -6.20),     # epaule avant tribord
    (2.85, 2.05),       # flanc arriere babord
    (-2.85, 2.05),      # flanc arriere tribord
    (ARM_X, 0.30),      # pont du bras babord
    (-ARM_X, 0.30),     # pont du bras tribord
]
TURRET_SEAT_R = 0.88

# Balises flottantes : (x, y, z) au centre de la nacelle, position de REPOS.
# La planche en montre trois, tenues dans un champ hexagonal : une au-dessus de
# la proue, deux en retrait de part et d'autre de la poupe. Elles sont hors de
# la coque et l'animation les fait deriver de +/-0,55 m en orbite et +/-0,30 m
# en vertical : les trois points sont choisis pour que, meme au plus pres, la
# nacelle ne rentre dans rien et ne deborde pas la bbox X/Z.
#   * Beacon_01 : 1,4 m au-dessus du pont de proue, en avant de la passerelle.
#   * Beacon_02/03 : dans le vide entre le culot des bras (y = 3,70) et la
#     rampe (demi-largeur 1,62) — a x = +/-4,60 il n'y a aucune coque.
BEACONS: list[tuple[float, float, float]] = [
    (0.00, -7.55, 2.55),
    (4.60, 5.60, 1.85),
    (-4.60, 5.60, 1.85),
]

# Entretoises corps <-> bras : (y, z). Cylindres transversaux a colliers.
STRUTS: list[tuple[float, float]] = [
    (-3.00, 0.05),
    (0.80, 0.05),
]
STRUT_X0 = 3.30    # noye dans le flanc du corps central
STRUT_X1 = 5.75    # noye dans le flanc du bras
STRUT_SEGMENTS = 12

# Gorge d'appontage : le portail est perce dans la face arriere du corps
# central, et la gorge s'enfonce de 1,9 m VERS L'AVANT. Chaque anneau est une
# section a 10 sommets, comme les sections de coque, ce qui permet de la relier
# directement au dernier anneau du corps.
#   (y, demi-largeur, z plafond, z plancher)
THROAT: list[tuple[float, float, float, float]] = [
    (5.60, 1.16, 0.50, -0.20),    # bouche, dans la face arriere
    (4.80, 1.06, 0.44, -0.16),
    (3.70, 0.94, 0.38, -0.12),    # fond, ferme par une paroi emissive
]

# Baie d'appontage : rampe trapezoidale, chevrons cyan pointant vers l'avant.
DOCK_Y0 = 5.55     # au ras de la face arriere : la rampe prolonge la gorge
DOCK_Y1 = HALF_L   # talon de la rampe — TALON (bbox +Y)
DOCK_HW0 = 1.66
DOCK_HW1 = 1.48
DOCK_TOP_Z = -0.16
DOCK_BOT_Z = -0.48


# ==========================================================================
# Helpers locaux
# ==========================================================================


def densify(
    table: list[tuple[float, ...]], max_step: float
) -> list[tuple[float, ...]]:
    """Insere des stations intermediaires, par interpolation LINEAIRE.

    La silhouette est rigoureusement inchangee : on subdivise des segments
    droits, donc chaque point insere est deja sur la surface. Ce n'est pas un
    lissage — les cassures franches (proue, epaule, hanche) restent des
    cassures. On ne gagne que des bandes de faces, c'est-a-dire de quoi
    decouper des plaques et poser des liseres.
    """
    out: list[tuple[float, ...]] = []
    for i in range(len(table) - 1):
        a, b = table[i], table[i + 1]
        span = b[0] - a[0]
        steps = max(1, int(math.ceil(abs(span) / max_step)))
        for s in range(steps):
            t = s / steps
            out.append(tuple(a[c] + (b[c] - a[c]) * t for c in range(len(a))))
    out.append(tuple(table[-1]))
    return out


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
    """Section prismatique a 14 sommets : pont plat, flancs chanfreines, quille.

    Les sommets 2/5 (pont) et 9/12 (quille) sont EXACTEMENT sur les droites que
    forment leurs voisins : ils n'infléchissent rien, la silhouette est celle
    d'une section a 10 sommets. Ils ne servent qu'a couper le pont en QUATRE
    lisieres au lieu de deux — la planche montre un pavage de plaques aussi fin
    en travers qu'en long, et a trois faces de large le pont ne pouvait porter
    que des bandes traversantes.

    Ordre (fixe l'index des faces produites par `bridge_rings`) :
      0 lisse P | 1-2 pont P | 3 pont central | 4-5 pont S | 6 lisse S
      7 flanc S | 8-9 quille S | 10 quille centrale | 11-12 quille P | 13 flanc P
    """
    zm = zb + 0.58 * (zt - zb)
    pts = [
        (cx + hw, y, zm),
        (cx + 0.86 * hw, y, zt),
        (cx + 0.58 * hw, y, zt),
        (cx + 0.30 * hw, y, zt),
        (cx - 0.30 * hw, y, zt),
        (cx - 0.58 * hw, y, zt),
        (cx - 0.86 * hw, y, zt),
        (cx - hw, y, zm),
        (cx - 0.80 * hw, y, zb),
        (cx - 0.54 * hw, y, zb),
        (cx - 0.28 * hw, y, zb),
        (cx + 0.28 * hw, y, zb),
        (cx + 0.54 * hw, y, zb),
        (cx + 0.80 * hw, y, zb),
    ]
    return ak.add_ring(bm, pts)


#: Index de face, dans une bande de `_hull_ring`, par role.
F_CHINE_P, F_CHINE_S = 0, 6
F_DECK_C, F_KEEL_C = 3, 10
F_FLANK_S, F_FLANK_P = 7, 13
#: Lisieres de pont et de quille (deux de chaque cote).
DECK_SIDE: set[int] = {1, 2, 4, 5}
KEEL_SIDE: set[int] = {8, 9, 11, 12}
CHINES: set[int] = {F_CHINE_P, F_CHINE_S}
FLANKS: set[int] = {F_FLANK_P, F_FLANK_S}


def _prismatic_body(bm, cx: float, table, cap_front: str, cap_rear: str | None):
    """Construit un corps depuis une table `(y, hw, zt, zb)`.

    Retourne `(bandes, y_milieu_de_bande, anneaux)` : de quoi selectionner
    ensuite des faces par zone (plaques, panneaux, liseres) et, si
    `cap_rear` vaut `None`, de quoi percer la face arriere (gorge de baie).
    """
    rings = [_hull_ring(bm, cx, y, hw, zt, zb) for y, hw, zt, zb in table]
    bands, band_y = [], []
    for i in range(len(rings) - 1):
        bands.append(ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull"))
        band_y.append((table[i][0] + table[i + 1][0]) * 0.5)
    ak.cap_ring(bm, list(reversed(rings[0])), cap_front)
    if cap_rear is not None:
        ak.cap_ring(bm, rings[-1], cap_rear)
    return bands, band_y, rings


def _pick(bands, band_y, y0: float, y1: float, faces: set[int]) -> list:
    """Faces des bandes dont le milieu tombe dans [y0, y1], pour les roles donnes."""
    out = []
    for b, ym in enumerate(band_y):
        if y0 <= ym <= y1:
            for j in sorted(faces):
                face = bands[b][j]
                if face is not None and face.is_valid:
                    out.append(face)
    return out


def _plate_zone(
    bm,
    bands,
    band_y,
    y0: float,
    y1: float,
    roles: set[int],
    seed: int,
    *,
    thickness: float = 0.05,
    depth: float = -0.030,
    run_range: tuple[int, int] = (1, 3),
    joint: str = "AA_Greeble",
    gold_every: int = 6,
    panel_every: int = 0,
    panel_thickness: float = 0.14,
    panel_depth: float = -0.045,
    min_area: float = 0.05,
) -> int:
    """Decoupe une zone de coque en PLAQUES IRREGULIERES a joints visibles.

    C'est le coeur de la reforge. Chaque plaque est un `inset_panel` applique a
    une poignee de bandes consecutives (1 a 3, tiree au sort de facon seedee) :
    le fond reste ivoire, la couronne d'inset devient le joint — anthracite le
    plus souvent, **or** une fois sur `gold_every`, ce qui donne les liseres que
    la planche fait courir le long des aretes de panneau.

    ⚠️ `thickness` est la LARGEUR DU JOINT, pas celle de la plaque. A 0,12 m la
    coque rendait un carrelage : des tuiles separees par du mortier large. Le
    joint doit rester une ligne (0,04 a 0,06 m sur des plaques de 1 a 2 m) —
    c'est ce que montre la planche, ou la plaque touche presque sa voisine.
    Meme logique pour l'or : a une plaque sur trois il devenait la couleur
    dominante ; a une sur six ou huit il redevient un accent.

    Un plat sur `panel_every` recoit un SECOND inset emboite, en bleu : c'est la
    technique deja eprouvee sur `build_crescent_interceptor.py:597-598` (double
    inset), jamais appliquee ici — elle evite l'aplat bleu massif tout en
    donnant au panneau une bordure ivoire et un joint.

    Retourne le nombre de plaques decoupees.
    """
    rng = random.Random(seed)
    indices = [b for b, ym in enumerate(band_y) if y0 <= ym <= y1]
    plates = 0
    for role in sorted(roles):
        i = 0
        while i < len(indices):
            n = min(rng.randint(*run_range), len(indices) - i)
            group = []
            for k in range(i, i + n):
                face = bands[indices[k]][role]
                if face is not None and face.is_valid and face.calc_area() > min_area:
                    group.append(face)
            i += n
            if not group:
                continue
            th = thickness * (0.72 + 0.56 * rng.random())
            borders = ak.inset_panel(bm, group, "AA_Hull", thickness=th, depth=depth)
            plates += 1
            ak.set_material(
                borders, "AA_Trim" if gold_every and plates % gold_every == 0 else joint
            )
            if panel_every and plates % panel_every == 0:
                ak.inset_panel(
                    bm, group, "AA_Panel",
                    thickness=panel_thickness, depth=panel_depth,
                )
    return plates


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


def _rib_chain(
    bm,
    points: list[tuple[float, float, float]],
    width: float,
    rise: float = 0.055,
    drop: float = 0.34,
    material: str = "AA_Greeble",
) -> None:
    """Nervure suivant une ligne brisee quelconque de la surface du cristal.

    Chaque troncon est une petite barre droite (`_bar`) posee a l'altitude
    moyenne de ses deux bouts. C'est ce qui permet de faire courir une nervure
    aussi bien le LONG du cristal (voies de facette) qu'EN TRAVERS (aretes de
    table), la ou une barre unique tendue d'un bout a l'autre passerait 60 cm
    au-dessus de la surface au milieu.
    """
    for i in range(len(points) - 1):
        x0, y0, z0 = points[i]
        x1, y1, z1 = points[i + 1]
        zc = (z0 + z1) * 0.5
        _bar(bm, (x0, y0), (x1, y1), width, zc - drop, zc + rise, material)


def _triangulate_ngons(obj) -> None:
    """Triangule les seules n-gons (> 4 sommets), en place.

    Sans cela, l'exporteur glTF renonce aux tangentes (« Tangent space can only
    be computed for tris/quads ») et le `.glb` sort sans `TANGENT` — donc sans
    espace normal pour les cartes de relief (ADR-0013). Les n-gons viennent des
    culots (`ak.cap_ring`) : une poignee de faces. Le nombre de triangles
    exportes ne change pas (glTF triangule de toute facon).
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(obj.data)
    bm.free()


def _deck_z(table, y: float) -> float:
    """Altitude du pont a la station `y` (colonne 2 des tables de profil)."""
    return lerp_table(table, y, col=2)


def turret_seat(index: int) -> tuple[float, float, float]:
    """Point d'assise de la tourelle `index` : sur l'axe du fut, au ras du pont.

    C'est LA position du marqueur `Turret_NN` et l'origine attendue du modele
    `citadel_turret.glb`. Elle est derivee du pont, jamais devinee.
    """
    x, y = TURRETS[index]
    table = ARM if abs(x) > 5.0 else HULL
    return (x, y, _deck_z(table, y))


# ==========================================================================
# Corps central
# ==========================================================================


def build_core_hull():
    bm = bmesh.new()
    table = densify(HULL, HULL_STEP)
    bands, band_y, rings = _prismatic_body(bm, 0.0, table, "AA_Hull", None)

    # --- plaquage du pont : des dizaines de plaques, pas trois aplats -------
    # Bordes babord/tribord : c'est la surface que la camera de jeu voit le
    # mieux (20 deg de la verticale) et celle que l'ecran d'accueil montre en
    # gros plan.
    #
    # Le bleu est pose par ZONE CONTIGUE, pas saupoudre : la planche montre de
    # grands champs bleus eux-memes decoupes en plaques, encadres de champs
    # ivoire. Une plaque bleue isolee tous les quatre panneaux donnait un damier.
    for y0, y1, seed, panel in (
        (-7.60, -5.40, 101, 0),    # proue : ivoire
        (-5.40, -1.00, 103, 2),    # champ bleu avant (flanc du cristal)
        (-1.00, 3.00, 105, 2),     # champ bleu arriere
        (3.00, 5.60, 107, 0),      # poupe : ivoire
    ):
        _plate_zone(
            bm, bands, band_y, y0, y1, DECK_SIDE, SEED + seed,
            thickness=0.055, depth=-0.032, run_range=(1, 4),
            gold_every=6, panel_every=panel,
            panel_thickness=0.07, panel_depth=-0.040,
        )
    # Pont central : seulement l'avant et l'arriere — le milieu est occupe par
    # le puits du noyau.
    _plate_zone(
        bm, bands, band_y, -7.60, -5.60, {F_DECK_C}, SEED + 109,
        thickness=0.05, depth=-0.028, run_range=(1, 2), gold_every=4,
    )
    _plate_zone(
        bm, bands, band_y, 2.00, 5.60, {F_DECK_C}, SEED + 111,
        thickness=0.05, depth=-0.028, run_range=(1, 2), gold_every=4, panel_every=3,
    )

    # --- puits du noyau : cuve sombre a collerette etagee ------------------
    # Trois insets emboites (la planche montre un cadre a gradins autour du
    # cristal) : marche ivoire, jonc or, cuve anthracite.
    well = _pick(bands, band_y, -5.60, 2.00, {F_DECK_C})
    ak.set_material(ak.inset_panel(bm, well, "AA_Hull", thickness=0.14, depth=-0.05),
                    "AA_Greeble")
    ak.set_material(ak.inset_panel(bm, well, "AA_Hull", thickness=0.10, depth=-0.04),
                    "AA_Trim")
    ak.inset_panel(bm, well, "AA_Greeble", thickness=0.12, depth=-0.12)

    # --- lisses : liseres or aux deux bouts, plaques au milieu -------------
    ak.set_material(_pick(bands, band_y, -7.60, -6.20, CHINES), "AA_Trim")
    ak.set_material(_pick(bands, band_y, 4.70, 5.60, CHINES), "AA_Trim")
    _plate_zone(
        bm, bands, band_y, -6.20, 4.70, CHINES, SEED + 113,
        thickness=0.045, depth=-0.028, run_range=(1, 2), gold_every=5, panel_every=3,
        panel_thickness=0.08, panel_depth=-0.035,
    )

    # --- flancs bas : visibles de trois quarts, plaques plus longues -------
    _plate_zone(
        bm, bands, band_y, -7.60, 5.60, FLANKS, SEED + 115,
        thickness=0.055, depth=-0.032, run_range=(2, 4), gold_every=7, panel_every=3,
    )

    # --- quille : mecanique sombre, volontairement sobre ------------------
    # ADR-0011 : ce qui n'est pas visible depuis la camera de jeu n'existe pas.
    # La quille ne recoit donc que sa teinte et de grandes decoupes.
    ak.set_material(_pick(bands, band_y, -7.60, 5.60, {F_KEEL_C}), "AA_Greeble")
    _plate_zone(
        bm, bands, band_y, -6.00, 4.00, KEEL_SIDE, SEED + 117,
        thickness=0.10, depth=-0.05, run_range=(5, 8), gold_every=0, panel_every=1,
    )

    # --- gorge d'appontage : percee dans la face arriere -------------------
    # Le dernier anneau du corps n'a PAS ete ferme (`cap_rear=None`) : on le
    # relie a la bouche de la gorge, ce qui produit une face arriere annulaire
    # — donc un vrai trou — puis on enfonce la gorge vers l'avant. La planche
    # consacre un encart entier a cette gorge profonde ; une boite emissive
    # posee a plat ne pouvait pas la rendre.
    throat = [_hull_ring(bm, 0.0, y, hw, zt, zb) for y, hw, zt, zb in THROAT]
    ak.bridge_rings(bm, rings[-1], throat[0], "AA_Hull")     # face arriere percee
    ak.bridge_rings(bm, throat[0], throat[1], "AA_Greeble")  # parois de la gorge
    # Le FOND de la gorge est lumineux sur toute sa profondeur, pas seulement
    # sur sa paroi terminale : vue de l'arriere, une gorge aux parois anthracite
    # se rendait comme un trou noir, alors que la planche montre une lumiere qui
    # deborde du tunnel. Ce sont 1,1 m de tunnel, tres encaisses : le cyan n'en
    # sort que par l'ouverture.
    ak.bridge_rings(bm, throat[1], throat[2], "AA_Emissive_Engine")
    ak.cap_ring(bm, throat[2], "AA_Emissive_Engine")         # fond lumineux

    # encadrement du portail : jonc or + linteau anthracite
    y_mouth, hw_mouth, zt_mouth, zb_mouth = THROAT[0]
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(
            bm, (sx * (hw_mouth + 0.12), y_mouth - 0.06, (zt_mouth + zb_mouth) * 0.5),
            (0.20, 0.30, zt_mouth - zb_mouth + 0.30), "AA_Trim",
        )
    ak.add_box(bm, (0.0, y_mouth - 0.06, zt_mouth + 0.14),
               (2.72, 0.30, 0.22), "AA_Greeble")
    ak.add_box(bm, (0.0, y_mouth - 0.10, zt_mouth + 0.02),
               (1.40, 0.22, 0.10), "AA_Emissive_Engine")
    # feux de guidage dans la gorge
    for sx in (ak.PORT, ak.STARBOARD):
        for k in range(3):
            ak.add_box(
                bm, (sx * (1.02 - 0.04 * k), 5.20 - 0.55 * k, 0.30 - 0.03 * k),
                (0.06, 0.34, 0.07), "AA_Emissive_Engine",
            )

    # --- socles de tourelle (les tourelles, elles, sont un modele a part) ---
    for i, (x, _) in enumerate(TURRETS):
        if abs(x) > 5.0:
            continue   # les socles des bras sont poses par `build_arm`
        _turret_seat(bm, *turret_seat(i))

    # --- superstructure de pont ------------------------------------------
    # La planche couvre le pont du corps central de blocs : caissons de service
    # le long du cadre du noyau, batterie de vents, treuils. C'est ce que la
    # camera de jeu voit en premier (elle regarde a 20 deg de la verticale) et
    # c'etait le grand absent du premier modele — trois aplats et rien dessus.
    for sx in (ak.PORT, ak.STARBOARD):
        for k in range(4):
            y = -3.90 + k * 1.55
            ak.add_box(bm, (sx * 3.16, y, 1.16), (0.62, 1.05, 0.30), "AA_Greeble")
            ak.add_box(bm, (sx * 3.16, y, 1.32), (0.50, 0.86, 0.06), "AA_Hull")
            ak.add_box(bm, (sx * 3.16, y, 1.36), (0.22, 0.60, 0.04), "AA_Trim")
        ak.greeble_strip(
            bm,
            (sx * 3.24, -3.10, 1.20),
            (sx * 3.24, 2.40, 1.20),
            count=7,
            seed=SEED + (31 if sx > 0 else 37),
            size_range=(0.16, 0.36),
            height_range=(0.08, 0.24),
            jitter=0.06,
        )

    # bloc de proue blinde, a gradins (la planche montre une etrave etagee)
    ak.add_box(bm, (0.0, -7.05, 0.86), (2.30, 1.10, 0.34), "AA_Hull")
    ak.add_box(bm, (0.0, -7.28, 1.02), (1.60, 0.72, 0.22), "AA_Greeble")
    ak.add_box(bm, (0.0, -7.28, 1.13), (1.05, 0.50, 0.08), "AA_Trim")
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * 1.30, -6.95, 1.00), (0.50, 1.20, 0.28), "AA_Greeble")
        ak.add_box(bm, (sx * 1.30, -6.95, 1.15), (0.24, 0.60, 0.08), "AA_Emissive_Engine")
        # mats d'antenne, en avant de la passerelle
        ak.add_box(bm, (sx * 0.72, -7.42, 1.30), (0.10, 0.10, 0.70), "AA_Greeble")
        ak.add_box(bm, (sx * 0.72, -7.42, 1.68), (0.20, 0.20, 0.08), "AA_Trim")

    # caissons de poupe, de part et d'autre du portail
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * 1.86, 4.30, 1.02), (0.90, 1.30, 0.34), "AA_Greeble")
        ak.add_box(bm, (sx * 1.86, 4.30, 1.20), (0.62, 0.90, 0.08), "AA_Emissive_Engine")

    return ak.new_object("Citadel_Hull", bm)


def _turret_seat(bm, x: float, y: float, z: float) -> None:
    """Socle circulaire encastre : couronne anthracite, levre doree, cuve.

    Le modele de tourelle vient s'y poser, origine sur cet axe, a l'altitude
    `z`. La cuve est creusee sous le pont pour que le fut ne semble pas colle
    dessus.
    """
    ak.add_lathe(
        bm,
        [
            (z - 0.42, 0.00, "AA_Greeble"),
            (z - 0.42, TURRET_SEAT_R * 0.86, "AA_Greeble"),
            (z - 0.08, TURRET_SEAT_R * 0.90, "AA_Greeble"),
            (z + 0.03, TURRET_SEAT_R, "AA_Trim"),          # levre doree
            (z + 0.06, TURRET_SEAT_R * 0.92, "AA_Hull"),
            (z + 0.02, TURRET_SEAT_R * 0.72, "AA_Greeble"),
            (z - 0.20, TURRET_SEAT_R * 0.66, "AA_Greeble"),  # cuve
            (z - 0.22, 0.00, "AA_Greeble"),
        ],
        14,
        center_x=x,
        center_z=y,
        axis="Z",
    )


# ==========================================================================
# Bras-batteries
# ==========================================================================


def build_arm(sx: float):
    """Un bras-batterie complet (capsule + mantelet + quatre tubes), cote `sx`.

    `sx` vaut `ak.PORT` (+1) ou `ak.STARBOARD` (-1) : jamais un signe ecrit a la
    main (cf. le piege d'orientation documente dans le kit).
    """
    bm = bmesh.new()
    cx = sx * ARM_X
    tag = 0 if sx > 0 else 1000
    table = densify(ARM, ARM_STEP)
    bands, band_y, _ = _prismatic_body(bm, cx, table, "AA_Greeble", "AA_Greeble")

    # --- pont du bras : le grand aplat bleu de la planche, EN PLAQUES -------
    # La planche montre un champ bleu unique couvrant les deux tiers du pont du
    # bras, lui-meme decoupe en plaques, cerne d'ivoire. On garde ce champ (il
    # fait la lecture du bras a distance) mais chaque plaque a desormais son
    # joint et sa bordure ivoire.
    for y0, y1, seed, panel in (
        (-6.60, -3.20, 201, 0),    # avant du bras : ivoire (sous le mantelet)
        (-3.20, 2.20, 203, 1),     # champ bleu principal
        (2.20, 3.70, 205, 0),      # culot : ivoire
    ):
        _plate_zone(
            bm, bands, band_y, y0, y1, DECK_SIDE | {F_DECK_C},
            SEED + seed + tag,
            thickness=0.055, depth=-0.032, run_range=(1, 4),
            gold_every=6, panel_every=panel,
            panel_thickness=0.07, panel_depth=-0.040,
        )
    _plate_zone(
        bm, bands, band_y, -6.60, 3.70, FLANKS, SEED + 207 + tag,
        thickness=0.055, depth=-0.030, run_range=(2, 3), gold_every=6, panel_every=3,
    )
    _plate_zone(
        bm, bands, band_y, -5.00, 2.60, KEEL_SIDE, SEED + 209 + tag,
        thickness=0.10, depth=-0.05, run_range=(4, 6), gold_every=0, panel_every=1,
    )
    ak.set_material(_pick(bands, band_y, -6.60, -4.60, CHINES), "AA_Trim")
    ak.set_material(_pick(bands, band_y, 3.00, 3.70, CHINES), "AA_Trim")
    _plate_zone(
        bm, bands, band_y, -4.60, 3.00, CHINES, SEED + 211 + tag,
        thickness=0.045, depth=-0.028, run_range=(1, 2), gold_every=5,
    )

    # --- mantelet : le bloc de culasse etage d'ou sortent les quatre tubes --
    # La planche montre un empilement de blocs, pas une boite : trois gradins,
    # un capot dore, une visee cyan et deux joues laterales.
    ak.add_box(bm, (cx, -5.05, 0.30), (3.94, 2.60, 0.90), "AA_Greeble")   # socle
    ak.add_box(bm, (cx, -5.20, 0.86), (3.40, 2.20, 0.34), "AA_Hull")      # gradin bas
    ak.add_box(bm, (cx, -5.30, 1.06), (2.90, 1.90, 0.16), "AA_Trim")      # jonc
    ak.add_box(bm, (cx, -5.35, 1.30), (2.20, 1.70, 0.36), "AA_Greeble")   # gradin haut
    ak.add_box(bm, (cx, -4.30, 1.06), (3.44, 1.10, 0.54), "AA_Greeble")   # culasse
    ak.add_box(bm, (cx, -4.30, 1.36), (1.16, 0.80, 0.14), "AA_Emissive_Engine")
    ak.add_box(bm, (cx, -3.55, 1.14), (2.40, 0.56, 0.36), "AA_Hull")
    ak.add_box(bm, (cx, -3.55, 1.33), (0.90, 0.30, 0.08), "AA_Marking_Red")
    for sd in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (cx + sd * 1.72, -5.00, 0.80), (0.42, 2.10, 0.86), "AA_Hull")
        ak.add_box(bm, (cx + sd * 1.76, -5.00, 1.10), (0.26, 1.30, 0.10), "AA_Trim")

    # --- quatre canons, deux paires superposees, pointes vers -Y ------------
    for d, tip, bz in BARRELS:
        ak.add_lathe(
            bm,
            [
                (BARREL_ROOT, 0.00, "AA_Greeble"),            # pole de culasse
                (BARREL_ROOT + 0.05, 0.32, "AA_Greeble"),
                (BARREL_ROOT - 0.55, 0.32, "AA_Greeble"),     # bloc de culasse
                (BARREL_ROOT - 0.58, 0.37, "AA_Trim"),        # collier de culasse
                (BARREL_ROOT - 0.86, 0.37, "AA_Trim"),
                (BARREL_ROOT - 0.90, BARREL_R, "AA_Hull"),
                (BARREL_ROOT - 1.90, BARREL_R, "AA_Greeble"),
                (BARREL_ROOT - 1.94, BARREL_R * 1.22, "AA_Trim"),   # collier median
                (BARREL_ROOT - 2.30, BARREL_R * 1.22, "AA_Trim"),
                # Le long fut est IVOIRE et non anthracite : la planche montre
                # des tubes clairs cercles de noir et d'or. En anthracite, les
                # huit canons se rendaient comme huit tiges noires, et le bras
                # perdait sa masse blanche.
                (BARREL_ROOT - 2.34, BARREL_R * 0.94, "AA_Hull"),
                (tip + 0.86, BARREL_R * 0.94, "AA_Greeble"),
                (tip + 0.82, BARREL_R * 1.16, "AA_Hull"),     # manchon de bouche
                (tip + 0.24, BARREL_R * 1.16, "AA_Hull"),
                (tip + 0.20, BARREL_R * 1.00, "AA_Greeble"),
                (tip + 0.05, BARREL_R * 1.10, "AA_Greeble"),  # levre de bouche
                (tip, BARREL_R * 1.04, "AA_Greeble"),         # BOUCHE (bbox -Y)
                (tip + 0.03, BARREL_R * 0.52, "AA_Emissive_Engine"),
                (tip + 0.28, BARREL_R * 0.48, "AA_Emissive_Engine"),
                (tip + 0.32, 0.00, "AA_Emissive_Engine"),     # ame lumineuse
            ],
            BARREL_SEGMENTS,
            center_x=cx + sx * d,
            center_z=bz,
        )
        # collier de fixation au sortir du mantelet
        ak.add_box(bm, (cx + sx * d, -6.30, bz), (0.56, 0.30, 0.56), "AA_Trim")
        ak.add_box(bm, (cx + sx * d, -6.62, bz), (0.48, 0.24, 0.48), "AA_Greeble")

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
    for k in range(8):
        y = -3.80 + k * 0.98
        ak.add_box(
            bm,
            (cx + sx * 2.10, y, 0.30),
            (0.10, 0.30, 0.14),
            "AA_Emissive_Engine",
        )

    # --- socle de tourelle du pont du bras --------------------------------
    seat = turret_seat(4 if sx > 0 else 5)
    _turret_seat(bm, *seat)

    # --- greebles de pont, semees (deterministes) -------------------------
    # Elles sont sur le DESSUS, seule surface que la camera de jeu voit, et
    # ecartees du socle de tourelle.
    ak.greeble_strip(
        bm,
        (cx + sx * 1.30, -2.40, 1.03),
        (cx + sx * 1.30, 2.60, 1.03),
        count=9,
        seed=SEED + 11 + tag,
        size_range=(0.18, 0.44),
        height_range=(0.10, 0.30),
        jitter=0.06,
    )
    ak.greeble_strip(
        bm,
        (cx - sx * 1.30, -2.10, 1.03),
        (cx - sx * 1.30, 2.90, 1.03),
        count=7,
        seed=SEED + 13 + tag,
        size_range=(0.16, 0.38),
        height_range=(0.08, 0.24),
        jitter=0.06,
    )

    return ak.new_object("Citadel_Arm_" + ("L" if sx > 0 else "R"), bm)


# ==========================================================================
# Noyau cristallin — la signature de la silhouette
# ==========================================================================


def _core_hw(y: float) -> float:
    """Demi-largeur du cristal a la station `y`."""
    return lerp_table(CORE, y)


def _core_z(y: float, w: float) -> float:
    """Altitude d'une voie de facette (`w` normalise) a la station `y`.

    Le cristal se PINCE vers ses deux pointes : la hauteur suit la largeur,
    sinon le prisme resterait un bandeau plat aux extremites.
    """
    k = _core_hw(y) / CORE_HW_MAX
    return CORE_BASE_Z + (CORE_TOP_Z - CORE_BASE_Z) * w * (0.28 + 0.72 * k)


def build_core_prism():
    """Prisme facette, integralement emissif cyan.

    Dix voies de facette par section (`CORE_SECTION`) et quinze stations : la
    planche montre un cristal a grandes facettes planes et aretes vives, pas une
    goutte. Les aretes sont ensuite soulignees par des nervures anthracite —
    voir plus bas, c'est la seule facon de les faire exister.
    """
    bm = bmesh.new()
    rings = []
    for y, hw in CORE:
        if hw <= 1e-6:
            rings.append(bm.verts.new((0.0, y, _core_z(y, 0.62))))
            continue
        rings.append(
            ak.add_ring(
                bm,
                [(u * hw, y, _core_z(y, w)) for u, w in CORE_SECTION],
            )
        )

    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        if isinstance(a, bmesh.types.BMVert):
            ak.fan_to_point(bm, b, a, "AA_Emissive_Engine")
        elif isinstance(b, bmesh.types.BMVert):
            ak.fan_to_point(bm, a, b, "AA_Emissive_Engine")
        else:
            ak.bridge_rings(bm, a, b, "AA_Emissive_Engine")

    # --- nervures de taille, sur les aretes de facette --------------------
    # Un materiau emissif ne recoit PAS la lumiere : ses facettes ont toutes la
    # meme valeur, et le cristal, si soigne soit-il en geometrie, se rendait
    # comme une goutte blanche uniforme. Les facettes ne peuvent donc exister
    # que par la geometrie : de fines nervures anthracite courent le long des
    # quatre aretes de taille (deux aretes de table, deux epaulements). Ce sont
    # les traits sombres que montre la planche sur le cristal.
    #
    # Elles sont BALAYEES par petits pas et non posees station par station : une
    # barre droite tendue sur une station entiere depassait de 60 cm au-dessus
    # des pointes — trois griffes noires. Les pointes restent nues : c'est la
    # que le verre doit etre le plus pur.
    # Le pas (0,20 m) et la saillie (0,055 m) sont lies : chaque barre est
    # droite alors que la facette monte, donc elle s'enfonce de (pente x pas / 2)
    # au milieu. Tant que cette fleche reste sous la saillie, la nervure est
    # continue ; a 0,35 m de pas elle se rompait en pointilles.
    # ⚠️ La LARGEUR de nervure est un choix de lisibilite, pas de style. A 9 cm
    # sur un cristal de 4 m, elle fait un pixel a la distance de jeu : le noyau
    # redevenait une goutte blanche malgre toutes les facettes. A 18 cm elle lit
    # comme le plombage d'un vitrail — c'est ce que montre la planche, ou les
    # aretes du cristal sont des traits epais, pas des cheveux.
    # Pas de balayage : 0,12 m. A 0,20 les nervures montaient en marches d'un
    # demi-decimetre la ou le cristal se pince, et la ceinture de taille se
    # rendait en dents de scie sur la vue de trois quarts — le defaut se voyait
    # avant meme de zoomer.
    step = 0.12
    y_start, y_end = -5.05, 1.50
    steps = int(round((y_end - y_start) / step))
    for u, w in CORE_RIB_LANES:
        _rib_chain(
            bm,
            [
                (u * _core_hw(y_start + i * step), y_start + i * step,
                 _core_z(y_start + i * step, w))
                for i in range(steps + 1)
            ],
            0.18,
        )

    # --- aretes de table : les nervures EN TRAVERS ------------------------
    # Sans elles, les voies longitudinales ne se refermaient sur rien et le
    # cristal restait un ballon raye. La planche montre une table hexagonale :
    # deux longues aretes (les voies) et, a chaque bout, deux aretes obliques
    # qui convergent vers la pointe. Ces trois traverses les dessinent.
    for y in (-4.30, -2.60, -0.60, 1.05):
        hw = _core_hw(y)
        _rib_chain(
            bm,
            [(u * hw, y, _core_z(y, w)) for u, w in CORE_TABLE_CHAIN],
            0.15,
        )

    # ceinture de taille a la plus grande largeur : elle ferme le dessin des
    # facettes par le bas et donne au cristal une assise lisible de loin.
    # Balayee au meme pas que les autres nervures, et non posee station par
    # station : une barre de 0,90 m a altitude fixe depassait la ou le cristal
    # se pince, et la ceinture se rendait en dents de scie.
    for sx in (ak.PORT, ak.STARBOARD):
        _rib_chain(
            bm,
            [
                (sx * _core_hw(y_start + i * step), y_start + i * step,
                 _core_z(y_start + i * step, 0.34))
                for i in range(steps + 1)
            ],
            0.16,
            rise=0.16,
            drop=0.16,
        )

    return ak.new_object("Citadel_Core", bm)


def build_core_frame():
    """Le cadre technique qui enchasse le noyau : or, anthracite, rouge."""
    bm = bmesh.new()

    # jonc dore continu autour de l'assise du cristal, EMERGEANT du pont
    for sx in (ak.PORT, ak.STARBOARD):
        for i in range(len(CORE) - 1):
            y0, hw0 = CORE[i]
            y1, hw1 = CORE[i + 1]
            if hw0 < 1e-6 and hw1 < 1e-6:
                continue
            _bar(
                bm,
                (sx * (hw0 + 0.16), y0),
                (sx * (hw1 + 0.16), y1),
                0.24,
                CORE_BASE_Z - 0.34,
                CORE_BASE_Z + 0.30,
                "AA_Trim",
            )
            # seconde ceinture anthracite, en retrait : le gradin de la planche
            _bar(
                bm,
                (sx * (hw0 + 0.40), y0),
                (sx * (hw1 + 0.40), y1),
                0.26,
                CORE_BASE_Z - 0.30,
                CORE_BASE_Z + 0.14,
                "AA_Greeble",
            )

    # contreforts anthracite : trois paires d'arcs-boutants sur les flancs,
    # avec capot dore et carre de visee cyan (la planche les montre etages)
    for sx in (ak.PORT, ak.STARBOARD):
        for y in (-4.10, -2.20, -0.30):
            ak.add_box(bm, (sx * 2.62, y, 0.98), (1.16, 0.94, 0.66), "AA_Greeble")
            ak.add_box(bm, (sx * 2.62, y, 1.34), (0.92, 0.70, 0.18), "AA_Trim")
            ak.add_box(bm, (sx * 2.62, y, 1.45), (0.42, 0.34, 0.08), "AA_Emissive_Engine")
        # marquages rouges de zone reglementee, de part et d'autre du puits.
        # Petits : la charte les dit « restreints », et en 0,86 m de long ils
        # devenaient deux dalles roses aussi lisibles que le cristal.
        ak.add_box(bm, (sx * 2.62, -1.25, 1.32), (0.52, 0.30, 0.08), "AA_Marking_Red")
        ak.add_box(bm, (sx * 2.62, 0.70, 1.32), (0.52, 0.30, 0.08), "AA_Marking_Red")

    # culasse avant et arriere du cadre : deux blocs techniques qui tiennent les
    # pointes du cristal (sans eux, le cristal semble pose, pas enchasse)
    for y, depth in ((-5.05, 0.80), (1.50, 0.90)):
        ak.add_box(bm, (0.0, y, 1.02), (1.60, depth, 0.62), "AA_Greeble")
        ak.add_box(bm, (0.0, y, 1.34), (1.20, depth * 0.7, 0.16), "AA_Trim")

    return ak.new_object("Citadel_CoreFrame", bm)


# ==========================================================================
# Entretoises, passerelle, baie d'appontage
# ==========================================================================


def build_struts():
    bm = bmesh.new()
    for y, z in STRUTS:
        for sx in (ak.PORT, ak.STARBOARD):
            ak.add_lathe(
                bm,
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
                center_x=y,
                center_z=z,
                axis="X",
            )
    return ak.new_object("Citadel_Struts", bm)


def build_bridge():
    """Passerelle de proue : verriere sombre + marquage rouge (cf. planche)."""
    bm = bmesh.new()
    ak.add_box(bm, (0.0, -6.55, 1.16), (2.20, 1.36, 0.46), "AA_Hull")
    ak.add_box(bm, (0.0, -6.90, 1.42), (1.44, 0.74, 0.32), "AA_Glass")
    ak.add_box(bm, (0.0, -6.10, 1.44), (0.94, 0.36, 0.24), "AA_Trim")
    ak.add_box(bm, (0.0, -7.36, 1.06), (0.54, 0.26, 0.16), "AA_Marking_Red")
    for sd in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sd * 1.36, -6.60, 1.12), (0.42, 1.10, 0.34), "AA_Greeble")
        ak.add_box(bm, (sd * 1.36, -6.60, 1.30), (0.28, 0.70, 0.08), "AA_Emissive_Engine")
    # antennes / greebles de proue
    ak.greeble_strip(
        bm,
        (0.0, -5.90, 1.24),
        (0.0, -5.30, 1.24),
        count=4,
        seed=SEED + 7,
        size_range=(0.18, 0.40),
        height_range=(0.12, 0.34),
        jitter=0.05,
    )
    return ak.new_object("Citadel_Bridge", bm)


def build_dock():
    """Rampe d'appontage arriere : plancher creuse, rails dores, chevrons cyan.

    La gorge, elle, est percee dans la coque par `build_core_hull()`. Ici on ne
    construit que ce qui SORT de la coque : la rampe et ses feux. La baie
    regarde vers +Y — c'est-a-dire vers le joueur, en bas de l'ecran.
    """
    bm = bmesh.new()

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
    ak.cap_ring(bm, lo, "AA_Greeble")
    # ⚠️ La boucle est parcourue de babord vers tribord : capee telle quelle, sa
    # normale pointe VERS LE BAS, et `inset_panel(depth<0)` — qui creuse le long
    # de la normale — SOULEVAIT le plancher de 12 cm au lieu de le creuser. La
    # rampe se rendait comme une dalle bleue bombee qui masquait ses propres
    # chevrons. Les normales ne sont recalculees qu'a `new_object()`, donc trop
    # tard pour les insets : il faut donner la bonne boucle ici.
    deck = ak.cap_ring(bm, list(reversed(hi)), "AA_Hull")
    if deck is not None:
        # plancher CREUSE entre deux margelles (la planche montre une gorge, pas
        # une dalle) : deux insets emboites, le second nettement enfonce. Le
        # fond est bleu et non anthracite — en anthracite, la rampe se rendait
        # comme un trou noir de 3 m dans une coque ivoire, et c'est tout ce
        # qu'on voyait de la baie depuis la camera de jeu.
        ak.set_material(
            ak.inset_panel(bm, [deck], "AA_Hull", thickness=0.14, depth=-0.03),
            "AA_Trim",
        )
        ak.inset_panel(bm, [deck], "AA_Panel", thickness=0.12, depth=-0.09)

    # rails lateraux dores, poses sur les margelles
    for sx in (ak.PORT, ak.STARBOARD):
        _bar(
            bm,
            (sx * (DOCK_HW0 - 0.09), DOCK_Y0),
            (sx * (DOCK_HW1 - 0.09), DOCK_Y1),
            0.14,
            DOCK_TOP_Z - 0.04,
            DOCK_TOP_Z + 0.16,
            "AA_Trim",
        )
        # main-courante anthracite exterieure
        _bar(
            bm,
            (sx * (DOCK_HW0 + 0.02), DOCK_Y0),
            (sx * (DOCK_HW1 + 0.02), DOCK_Y1),
            0.10,
            DOCK_TOP_Z - 0.02,
            DOCK_TOP_Z + 0.24,
            "AA_Greeble",
        )

    # chevrons cyan pointant vers l'avant (guidage d'appontage).
    # Le dernier chevron s'arrete a 0,15 m du talon : sa pointe et sa
    # demi-largeur debordaient de 13 cm au-dela de DOCK_Y1, et c'etait ELLE qui
    # fixait la bbox en +Y — le pivot partait de 6,7 cm hors tolerance.
    for k in range(5):
        y = DOCK_Y0 + 0.40 + k * 0.50
        half = 0.82 - 0.04 * k
        for sx in (ak.PORT, ak.STARBOARD):
            _bar(
                bm,
                (0.0, y - 0.30),
                (sx * half, y + 0.14),
                0.16,
                DOCK_TOP_Z - 0.14,
                DOCK_TOP_Z - 0.06,
                "AA_Emissive_Engine",
            )

    # feux d'approche de part et d'autre du talon
    for sx in (ak.PORT, ak.STARBOARD):
        for k in range(3):
            ak.add_box(
                bm,
                (sx * (DOCK_HW1 + 0.10), DOCK_Y1 - 0.30 - 0.70 * k, DOCK_TOP_Z + 0.08),
                (0.16, 0.34, 0.18),
                "AA_Emissive_Engine",
            )

    return ak.new_object("Citadel_Dock", bm)


# ==========================================================================
# Points d'attache et reperes de pieces
# ==========================================================================


def build_markers() -> list:
    """Empties exportes en `Node3D` cote Godot.

    Trois familles, dans un seul et meme mecanisme (le kit n'exporte qu'UN objet
    maille : voir le compte-rendu) :
      - les points d'attache fonctionnels (`Core_Center`, `Muzzle_Battery_L/R`,
        `Dock_Entry`) ;
      - les reperes de pieces (`Core_Prism`, `Battery_L/R`, `Dock_Bay`) ;
      - les **points d'ancrage** des sous-modeles animes : `Turret_01..06` au
        point d'assise de la tourelle sur le pont, `Beacon_01..03` au centre de
        la nacelle. L'origine du sous-modele et le marqueur coincident : un
        marqueur pose a mi-hauteur du fut ferait flotter la tourelle.
    Toutes les positions sont **derivees de la geometrie**, jamais devinees.
    """
    points: list = []

    # --- points d'attache fonctionnels -----------------------------------
    core_y = (CORE[0][0] + CORE[-1][0]) * 0.5
    points.append(
        ak.attach_point("Core_Center", (0.0, core_y, (CORE_BASE_Z + CORE_TOP_Z) * 0.5))
    )

    # bouche des canons principaux : dans l'axe du tube le plus avance
    d_main, tip_main, z_main = BARRELS[0]
    points += list(
        ak.attach_pair("Muzzle_Battery", ARM_X + d_main, tip_main - 0.05, z_main)
    )

    # entree de baie : au milieu de la rampe, sur sa surface
    points.append(
        ak.attach_point("Dock_Entry", (0.0, (DOCK_Y0 + DOCK_Y1) * 0.5, DOCK_TOP_Z + 0.10))
    )

    # --- reperes de pieces -----------------------------------------------
    points.append(ak.attach_point("Core_Prism", (0.0, core_y, _core_z(core_y, 0.52))))
    points += list(ak.attach_pair("Battery", ARM_X, -1.45, 0.0))
    points.append(
        ak.attach_point("Dock_Bay", (0.0, THROAT[0][0] - 0.30, DOCK_TOP_Z + 0.20))
    )

    # --- ancrages des sous-modeles animes --------------------------------
    for i in range(len(TURRETS)):
        points.append(ak.attach_point(f"Turret_{i + 1:02d}", turret_seat(i)))
    for i, position in enumerate(BEACONS):
        points.append(ak.attach_point(f"Beacon_{i + 1:02d}", position))

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
        build_bridge(),
        build_dock(),
    ]

    citadel = ak.join_objects(parts, "AegisCitadel")
    ak.cleanup(citadel)
    # Chanfrein a UN segment, large de 3 cm : deux fois moins que le creux des
    # panneaux (5 a 12 cm), donc la marche reste franche a la distance de jeu, et
    # les aretes du prisme accrochent la lumiere sans arrondir la silhouette.
    # ADR-0011 autorise d'aller a 2 segments ; essaye au rendu (voir le
    # compte-rendu BRIEF-0032) : sur une coque qui vaut par ses aretes vives, le
    # second segment ramollit le prisme sans rien apporter aux joints de plaque.
    ak.bevel_sharp_edges(citadel, width=0.03, segments=1, angle_deg=34.0)
    ak.shade_smooth_by_angle(citadel, angle_deg=34.0)
    _triangulate_ngons(citadel)

    # UV par projection en boite (ADR-0013) : sans elles, le `.glb` n'a ni
    # TEXCOORD_0 ni TANGENT et AUCUNE carte n'est applicable — c'etait le verrou
    # de cette coque. Aucune texture n'est embarquee : seulement les coordonnees.
    ak.box_project_uv(citadel, TEXELS_PER_METER)

    ak.export_hull(citadel, build_markers(), OUTPUT, CONTRACT)


if __name__ == "__main__":
    main()
