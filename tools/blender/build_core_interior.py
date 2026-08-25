"""build_core_interior.py — l'interieur du noyau ouvert du Pale Leviathan (BRIEF-0082).

    blender45 -b -P tools/blender/build_core_interior.py
    blender45 -b -P tools/blender/build_core_interior.py -- --plate

Produit `assets/imported/models/bosses/core_interior.glb`, et — avec `--plate` —
la planche de recette `docs/forge/output/BRIEF-0082-planche-quatre-vues.png`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne, aucun
alea non seede, deux executions successives donnent le meme sha256. `ak.export_hull()`
relit le `.glb` produit et refuse de publier hors contrat. Quatre harnais de mesure
supplementaires tournent a chaque build — degagement du couloir, cible non coiffee,
echelle contre le Specter-9, UV du fichier produit — et un cinquieme (l'ecart R-G)
tourne avec `--plate`. Tous sont documentes plus bas, et tous ECHOUENT le build.

`tools/blender/lib/aegis_kit.py` est utilise SANS AUCUNE MODIFICATION (il est gele).


CE QUI DECIDE DE CE DECOR : ON DOIT POUVOIR Y VOLER
===================================================
Ce n'est pas une piece de la coque du boss, c'est **le lieu ou l'on arrive**. La
faute a ne pas refaire est mesuree et connue : la coque du Leviathan livre des
« cinq anneaux qu'on franchit » de 0,33 a 0,24 m de large, quand le chasseur qui
doit les traverser fait 1,29 x 2,41 m. Le contrat de noms etait tenu, l'echelle
jamais verifiee, et rien ne l'a signale.

D'ou la regle qui gouverne ce fichier : **toute mesure est rapportee en multiples du
Specter-9**, pas en valeur absolue. `_report_scale()` imprime, a chaque build, la
largeur de chaque travee et de chaque passage en « chasseurs », et echoue si un
passage jouable descend sous 2,5 chasseurs de large. Un decor ou l'on ne peut pas
manoeuvrer est un decor faux, meme si sa bounding box est juste.

Quatre partis pris servent exclusivement cette lecture :

1. **L'arene remplit le plan de jeu.** 30,0 x 18,0 m au sol pour des bornes de
   28 x 16 (`GameplayPlane.BOUNDS`) : 1 m de debord de chaque cote, juste assez
   pour que les parois soient coupees par le cadre et qu'on n'en voie jamais la fin.
2. **Rien ne monte au-dessus du chasseur, sauf la cible.** Le jeu se lit du dessus ;
   toute elevation dans le couloir cache le vaisseau. Le decor vit donc SOUS le plan
   de vol (pont a -0,30 m, travees a -0,05 m, nervures a -0,14 m) et le reacteur est
   le seul volume qui perce vers le haut. C'est aussi ce qui le designe comme cible.
3. **La cible avance par la VALEUR, pas par la teinte.** Aucun emissif nulle part
   ailleurs que sur le reacteur — pas meme un rail de guidage a l'entree, qui aurait
   pourtant aide. L'erreur deja payee sur ce boss (chambre rouge-violet saturee ET
   flux sature, dix points d'ecart) vient d'un decor qui parlait la meme langue que
   la cible. Ici le decor est anthracite et ivoire ; le magenta n'existe qu'au centre.
4. **Le cadre s'ouvre en haut et en bas de l'ecran.** Les parois hautes tiennent les
   flancs et les angles ; au milieu des deux bords longs, elles cedent la place a un
   parapet bas de 0,75 m. Ce n'est pas un renoncement, c'est la seule facon de tenir
   la regle de degagement (voir « L'ECART ASSUME » plus bas), et cela tombe juste :
   dans un shmup vertical, le haut et le bas de l'ecran sont precisement les zones
   qu'il ne faut jamais boucher.


L'ECART ASSUME : LE DISQUE DE RAYON 11 EST PLUS GRAND QUE L'ARENE
================================================================
Le brief demande trois choses qui ne peuvent pas etre vraies ensemble :

  a) une enveloppe au sol de 28 x 16 a 32 x 20 m — donc |Z| <= 10 m au maximum ;
  b) des parois de 2,5 a 4,0 m de haut qui « ferment le cadre » ;
  c) aucune geometrie au-dessus de Y = 0,9 m dans le disque de rayon 11 m.

Le disque de rayon 11 deborde l'arene sur ses deux bords longs : a Z = 9 m il couvre
encore |X| <= sqrt(121 - 81) = 6,32 m. Autrement dit, aucune paroi haute ne peut
exister au milieu des bords hauts et bas, quelle que soit l'enveloppe autorisee.

Arbitrage retenu, et il sert l'intention (« le couloir jouable doit rester libre ») :
la regle (c) est tenue **a la lettre et verifiee par assertion** — `_assert_clearance()`
mesure le rayon du point le plus proche de l'origine parmi TOUS les sommets au-dessus
de Y = 0,9 m hors reacteur, et echoue sous 11,0 m. Ce sont donc les parois qui plient :
six segments hauts sur les flancs et les angles, et un parapet bas (0,75 m, sous le
seuil) en travers des deux ouvertures. Le cadre reste ferme a l'oeil, jamais au vol.

Le contrat de noms est integralement tenu : `Rim_01..06` sont bien six parois de
3,52 m de haut. Ce sont leurs longueurs qui varient, pas leur nature.


OU VA LE DETAIL
===============
La camera de jeu regarde a 20 deg de la VERTICALE (`graybox.tscn`). Tout le detail
est donc sur des faces horizontales ou tournees vers le haut : plaques de pont
enfoncees, capots ivoire des nervures, dos des travees, couronne du reacteur, face
INTERNE des parois (la seule qu'on voie). Les dessous et les faces externes des
parois sont en `AA_Greeble` sans detail (BRIEF-0026, rappele par ADR-0011).
"""

from __future__ import annotations

import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import aegis_kit as ak  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT = os.path.join(REPO, "assets/imported/models/bosses/core_interior.glb")
PLATE = os.path.join(REPO, "docs/forge/output/BRIEF-0082-planche-quatre-vues.png")
FIGHTER = os.path.join(REPO, "assets/imported/models/ships/specter_9.glb")

# ==========================================================================
# Cotes maitresses — repere d'AUTEUR (Z-up ; X lateral, Y profondeur, Z hauteur)
# ==========================================================================
# Rappel de la chaine d'axes du kit : (x, y, z)_auteur -> (-x, z, y)_Godot.
#   * X d'auteur  ->  -X Godot   (lateral, symetrique : sans consequence ici)
#   * Y d'auteur  ->  +Z Godot   (+Y = BAS de l'ecran, la ou l'on entre)
#   * Z d'auteur  ->  +Y Godot   (hauteur)

HALF_X = 15.0            # -> 30,0 m d'envergure (bornes de jeu : 28)
HALF_Y = 9.0             # -> 18,0 m de profondeur (bornes de jeu : 16)

DECK_TOP = -0.30         # dessus du pont : le chasseur vole 30 cm au-dessus
DECK_BOTTOM = -0.62      # dessous du pont (jamais vu, ferme le solide)
PLANE_Z = 0.0            # le plan de vol

RIM_TOP = 3.22           # arete haute des parois -> 3,52 m de haut depuis le pont
RIM_BATTER = 1.55        # devers vers l'interieur, mesure a l'arete haute
RIM_OVERLAP = 0.9        # recouvrement des parois dans les angles (voir rim_paths)

PARAPET_TOP = 0.45       # 0,75 m de haut depuis le pont : sous le seuil de 0,9
PARAPET_DEPTH = 0.68     # epaisseur du parapet
OPEN_HALF_X = 8.30       # demi-largeur de l'ouverture des bords longs
ENTRY_GAP_HALF = 3.00    # demi-largeur de la porte, dans le parapet du bas

CLEARANCE_Z = 0.9        # seuil du brief
CLEARANCE_R = 11.0       # rayon du disque a degager

REACTOR_R = 2.10         # -> 4,20 m de diametre (brief : 3,5 a 4,5)
CATWALK_HALF_W = 1.60    # -> 3,20 m de large, soit 1,8 largeur de chasseur
CATWALK_TOP = -0.05
CATWALK_BOTTOM = -0.45
RIB_TOP = -0.14

TRI_BUDGET = 22000
TEXELS_PER_METER = 0.55  # feuille de detail ADR-0011 : ~1,8 m de periode

#: Le metre-etalon de ce brief — RELU dans le .glb du chasseur a chaque build par
#: `fighter_envelope()`, jamais recopie. Ces deux valeurs ne sont que le repli si
#: le fichier manque. Le brief annonce 1,29 x 0,65 x 2,41 m ; le fichier livre en
#: mesure 1,75 x 0,65 x 2,46 (conforme, lui, au tableau normatif de l'ADR-0008).
#: Un metre-etalon qu'on cite au lieu de le mesurer est precisement ce qui a
#: laisse passer les anneaux de 30 cm.
FIGHTER_W = 1.75
FIGHTER_L = 2.46

#: Segments de revolution du reacteur. 24 : la couronne doit rester ronde vue de
#: dessus a 4,2 m de diametre, c'est la piece la plus regardee de la scene.
REACTOR_SEG = 24

#: Pas d'echantillonnage des parois et nervures, en metres.
WALL_STEP = 0.95

CONTRACT = ak.HullContract(
    name="Core Interior (Pale Leviathan)",
    width_x=2.0 * HALF_X,
    length_z=2.0 * HALF_Y,
    max_height_y=4.0,
    tri_budget=TRI_BUDGET,
    required_materials=ak.MATERIAL_ORDER,
    required_attach_points=("Reactor_Core", "Entry_Point"),
    tolerance=0.01,
    pivot_tolerance=0.02,
)


# ==========================================================================
# Helpers geometriques
# ==========================================================================


def _resample(path: list[tuple[float, float]], step: float) -> list[tuple[float, float]]:
    """Reechantillonne une polyligne 2D a pas ~constant, extremites conservees."""
    out = [path[0]]
    for a, b in zip(path, path[1:]):
        length = math.dist(a, b)
        count = max(1, int(round(length / step)))
        for k in range(1, count + 1):
            t = k / count
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def _inward_normals(path: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Normale unitaire de chaque station, orientee vers l'origine.

    Prise comme moyenne des normales des segments adjacents : sans cela, un pan
    coupe d'angle ouvrirait une fente a chaque changement de direction.
    """
    seg: list[tuple[float, float]] = []
    for a, b in zip(path, path[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        norm = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / norm, dx / norm
        mid = ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5)
        if nx * mid[0] + ny * mid[1] > 0.0:  # pointe vers l'exterieur : on retourne
            nx, ny = -nx, -ny
        seg.append((nx, ny))
    out = []
    for i in range(len(path)):
        left = seg[max(0, i - 1)]
        right = seg[min(len(seg) - 1, i)]
        nx, ny = left[0] + right[0], left[1] + right[1]
        norm = math.hypot(nx, ny) or 1.0
        out.append((nx / norm, ny / norm))
    return out


def _sweep(
    bm: bmesh.types.BMesh,
    path: list[tuple[float, float]],
    profile: list[tuple[float, float, str]],
    step: float = WALL_STEP,
) -> list[list[bmesh.types.BMFace]]:
    """Balaye un profil ferme le long d'une polyligne au sol.

    `profile` : liste ordonnee de `(deport vers l'interieur, hauteur, materiau)`,
    parcourue comme un POLYGONE FERME — le dernier point se recolle au premier
    par le dessous. On obtient donc un solide, ce qui permet a
    `recalc_face_normals()` d'orienter seul toutes les faces (aucun winding a
    tenir a la main, c'est la source d'erreur numero un de ce genre de balayage).

    Retourne les bandes de faces, indexees par segment du profil : c'est ce qui
    permet d'aller repeindre ou enfoncer la seule face interne, plus tard.
    """
    stations = _resample(path, step)
    normals = _inward_normals(stations)
    rings = []
    for (px, py), (nx, ny) in zip(stations, normals):
        rings.append(
            ak.add_ring(
                bm,
                [(px + nx * t, py + ny * t, z) for t, z, _m in profile],
            )
        )
    bands: list[list[bmesh.types.BMFace]] = [[] for _ in profile]
    for a, b in zip(rings, rings[1:]):
        faces = ak.bridge_rings(bm, a, b, profile[0][2], closed=True)
        for i, face in enumerate(faces):
            if face is None:
                continue
            face.material_index = ak.mat_index(profile[i][2])
            bands[i].append(face)
    ak.cap_ring(bm, rings[0], "AA_Greeble")
    ak.cap_ring(bm, list(reversed(rings[-1])), "AA_Greeble")
    return bands


def _plate_grid(
    bm: bmesh.types.BMesh,
    corner_a: tuple[float, float],
    corner_b: tuple[float, float],
    nx: int,
    ny: int,
    z: float,
    material: str,
) -> tuple[list[list[bmesh.types.BMVert]], list[list[bmesh.types.BMFace]]]:
    """Nappe horizontale reguliere. Retourne (grille de sommets, grille de faces)."""
    x0, y0 = corner_a
    x1, y1 = corner_b
    verts = [
        [
            bm.verts.new(
                (x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny, z)
            )
            for j in range(ny + 1)
        ]
        for i in range(nx + 1)
    ]
    idx = ak.mat_index(material)
    faces = []
    for i in range(nx):
        column = []
        for j in range(ny):
            face = bm.faces.new(
                (verts[i][j], verts[i + 1][j], verts[i + 1][j + 1], verts[i][j + 1])
            )
            face.material_index = idx
            column.append(face)
        faces.append(column)
    return verts, faces


def _boundary_loop(
    verts: list[list[bmesh.types.BMVert]],
) -> list[bmesh.types.BMVert]:
    """Contour d'une grille de sommets, dans l'ordre (sens direct)."""
    nx, ny = len(verts) - 1, len(verts[0]) - 1
    loop = [verts[i][0] for i in range(nx + 1)]
    loop += [verts[nx][j] for j in range(1, ny + 1)]
    loop += [verts[i][ny] for i in range(nx - 1, -1, -1)]
    loop += [verts[0][j] for j in range(ny - 1, 0, -1)]
    return loop


def _skirt(
    bm: bmesh.types.BMesh, loop: list[bmesh.types.BMVert], z: float, material: str
) -> None:
    """Ferme une nappe en solide : jupe verticale jusqu'a `z`, puis fond."""
    lower = ak.add_ring(bm, [(v.co.x, v.co.y, z) for v in loop])
    ak.bridge_rings(bm, loop, lower, material, closed=True)
    ak.cap_ring(bm, lower, material)


def _inset(
    bm: bmesh.types.BMesh,
    faces: list[bmesh.types.BMFace],
    material: str,
    thickness: float,
    depth: float,
    border: str = "AA_Greeble",
) -> None:
    """Enfonce chaque face de `faces` comme une plaque distincte.

    DEUX PIEGES, et les deux sont totalement silencieux — geometrie inchangee,
    aucun message, contrat vert.

    1. `inset_region` lit la NORMALE des faces. Sur un bmesh fraichement bati elle
       vaut zero et l'operateur ne fait rien. Le brief le signale ; le kit etant
       gele, c'est ici que `normal_update()` doit etre appele.

    2. `inset_region` inset une REGION, pas des faces. Deux faces qui partagent
       une arete n'en forment qu'une. Sur le pont, les 240 plaques contigues ne
       produisaient donc qu'UN unique lisere de 9 cm tout autour de l'arene : le
       damier annonce par 2 200 triangles n'existait nulle part au rendu, et il a
       fallu recadrer la planche pour s'en apercevoir. On decoupe donc la liste en
       lots SANS ARETE COMMUNE (deux suffisent pour une grille reguliere) et on
       appelle l'operateur une fois par lot. Les faces d'un lot non traite restent
       intactes : `inset_region` ne touche pas aux voisines de la region.
    """
    pending = [f for f in faces if f is not None and f.is_valid]
    while pending:
        batch: list[bmesh.types.BMFace] = []
        used: set = set()
        rest: list[bmesh.types.BMFace] = []
        for face in pending:
            edges = set(face.edges)
            if edges & used:
                rest.append(face)
            else:
                batch.append(face)
                used |= edges
        bm.normal_update()
        rim = ak.inset_panel(bm, batch, material, thickness=thickness, depth=depth)
        ak.set_material(rim, border)
        pending = [f for f in rest if f.is_valid]


# ==========================================================================
# 1. Le sol — `Floor`
# ==========================================================================

#: Grille du pont : 20 x 12 plaques de 1,50 m, soit un peu plus d'une longueur de
#: chasseur par plaque. C'est la seule trame qui donne l'echelle en vue de dessus
#: quand rien d'autre n'est dans le cadre.
DECK_NX, DECK_NY = 20, 12

#: Nervures transversales, en Y. Bombees vers l'exterieur : le pont se lit alors
#: comme le fond d'une carcasse, pas comme un damier.
RIB_ROWS = (2.4, 4.8, 7.2)
RIB_BULGE = 0.9


def _deck_plates(bm: bmesh.types.BMesh) -> None:
    verts, cells = _plate_grid(
        bm, (-HALF_X, -HALF_Y), (HALF_X, HALF_Y), DECK_NX, DECK_NY, DECK_TOP, "AA_Hull"
    )
    _skirt(bm, _boundary_loop(verts), DECK_BOTTOM, "AA_Greeble")

    # La cuvette du reacteur mange le centre : inutile d'enfoncer des plaques qui
    # seront couvertes, et surtout on evite d'y faire coexister deux surfaces.
    # AUCUNE TEINTE SUR LE PONT — seulement trois profondeurs de plaque.
    # Une premiere version y semait des plaques violettes et ivoire : rendues,
    # ce sont des carres colores isoles poses sur un sol neutre, et le jeu a
    # deja un vocabulaire pour ca — le violet est la couleur de l'Orbit Drone,
    # l'ivoire celle du Rescue Beacon (charte §3). Un decor n'a pas le droit
    # d'imiter un bonus. La variation passe donc par le relief, pas par la
    # couleur, ce qui laisse toute la saturation disponible a la cible.
    flush: list[bmesh.types.BMFace] = []
    bay: list[bmesh.types.BMFace] = []
    proud: list[bmesh.types.BMFace] = []
    for i in range(DECK_NX):
        for j in range(DECK_NY):
            cx = -HALF_X + (2 * HALF_X) * (i + 0.5) / DECK_NX
            cy = -HALF_Y + (2 * HALF_Y) * (j + 0.5) / DECK_NY
            if math.hypot(cx, cy) < REACTOR_R + 0.6:
                continue
            face = cells[i][j]
            # Motif purement arithmetique (aucun alea, ADR-0008).
            key = (i * 7 + j * 5) % 17
            if key == 3 and j % 2 == 0:
                bay.append(face)
            elif key == 11 and (i + j) % 3 == 0:
                proud.append(face)
            else:
                flush.append(face)
    _inset(bm, flush, "AA_Hull", 0.070, -0.032, border="AA_Greeble")
    _inset(bm, bay, "AA_Greeble", 0.070, -0.105, border="AA_Greeble")
    _inset(bm, proud, "AA_Hull", 0.070, 0.030, border="AA_Greeble")


def _rib_path(y0: float, x_from: float, x_to: float) -> list[tuple[float, float]]:
    sign = 1.0 if y0 > 0 else -1.0
    pts = []
    steps = 10
    for k in range(steps + 1):
        x = x_from + (x_to - x_from) * k / steps
        bow = RIB_BULGE * sign * (1.0 - (x / (HALF_X - 0.5)) ** 2)
        pts.append((x, y0 + bow))
    return pts


#: Profil d'une nervure : 0,48 m de large, capot ivoire, sommet a -0,14 m — donc
#: entierement SOUS le chasseur et sous les travees qui l'enjambent.
RIB_PROFILE = [
    (0.00, DECK_TOP, "AA_Greeble"),   # 0 flanc externe
    (0.00, -0.26, "AA_Hull"),         # 1
    (0.13, RIB_TOP, "AA_Hull"),       # 2 dessus, sombre
    (0.29, RIB_TOP, "AA_Trim"),       # 3 lisere ivoire de 0,10 m
    (0.39, RIB_TOP, "AA_Hull"),       # 4
    (0.48, -0.26, "AA_Greeble"),      # 5
    (0.48, DECK_TOP, "AA_Greeble"),   # 6 dessous
]


def _deck_ribs(bm: bmesh.types.BMesh) -> None:
    # Les nervures sont coupees autour de X = 0 : les deux travees nord/sud y
    # passent, et deux solides qui s'interpenetrent scintillent au rendu.
    for row in RIB_ROWS:
        for y0 in (row, -row):
            for x_from, x_to in ((-HALF_X + 0.5, -1.65), (1.65, HALF_X - 0.5)):
                _sweep(bm, _rib_path(y0, x_from, x_to), RIB_PROFILE, step=1.4)


#: Profil du parapet qui ferme les deux bords ouverts. Sommet a +0,45 m, soit
#: 0,45 m au-dessus du plan de vol : sous le seuil de degagement de 0,9 m.
PARAPET_PROFILE = [
    (0.00, DECK_TOP, "AA_Greeble"),
    (0.00, 0.20, "AA_Hull"),
    (0.14, PARAPET_TOP, "AA_Hull"),                    # dessus, sombre
    (PARAPET_DEPTH - 0.26, PARAPET_TOP, "AA_Trim"),    # lisere ivoire de 0,12 m
    (PARAPET_DEPTH - 0.14, PARAPET_TOP, "AA_Hull"),
    (PARAPET_DEPTH, 0.10, "AA_Panel"),                 # face interne
    (PARAPET_DEPTH, DECK_TOP, "AA_Greeble"),
]


def _parapets(bm: bmesh.types.BMesh) -> None:
    span = OPEN_HALF_X + 0.10
    # Bord haut de l'ecran (Y d'auteur negatif) : parapet continu, c'est le fond
    # de la cavite. Bord bas : deux tronçons et une porte de 5,20 m — par ou l'on
    # entre. L'asymetrie est volontaire, elle donne un sens de lecture au lieu.
    _sweep(bm, [(-span, -HALF_Y), (span, -HALF_Y)], PARAPET_PROFILE, step=1.1)
    _sweep(bm, [(-span, HALF_Y), (-ENTRY_GAP_HALF, HALF_Y)], PARAPET_PROFILE, step=1.1)
    _sweep(bm, [(ENTRY_GAP_HALF, HALF_Y), (span, HALF_Y)], PARAPET_PROFILE, step=1.1)


def _entry_chevrons(bm: bmesh.types.BMesh) -> None:
    """Trois chevrons ivoire poses sur le pont, en travers de la porte d'entree.

    Pas d'emissif : c'est la VALEUR qui doit guider, sinon on rejoue l'erreur du
    decor qui parle la meme langue que la cible (voir l'en-tete).
    """
    for k, y in enumerate((8.05, 7.35, 6.65)):
        width = ENTRY_GAP_HALF - 0.55 - 0.22 * k
        for side in (-1.0, 1.0):
            ak.add_box(
                bm,
                (side * width * 0.5, y, DECK_TOP - 0.005),
                (width, 0.22, 0.06),
                "AA_Trim",
            )


def _wall_machinery(bm: bmesh.types.BMesh) -> None:
    """Bandeau de caissons au pied des parois, hauteur 0,45 m maximum.

    Le budget etait a 50 % et la peripherie etait nue. Le detail va la parce que
    c'est la seule bande de l'arene ou l'on ne se bat pas : au centre, tout ce
    qu'on ajoute finit derriere un rideau de projectiles.
    `ak.greeble_strip` est integralement pilote par sa graine (ADR-0008).
    """
    # 2,50 m de retrait, et pas 1,15 : le devers des parois surplombe 1,55 m de
    # pont, et la premiere version de ce bandeau etait integralement cachee sous
    # cette casquette en vue de dessus. Ce qui ne se voit pas depuis la camera de
    # jeu n'existe pas (BRIEF-0026).
    inset = 2.50
    runs = (
        ((HALF_X - inset, -HALF_Y + 1.6), (HALF_X - inset, HALF_Y - 1.6), 22, 5101),
        ((-(HALF_X - inset), -HALF_Y + 1.6), (-(HALF_X - inset), HALF_Y - 1.6), 22, 5102),
        ((-(HALF_X - 3.4), -HALF_Y + inset), (-OPEN_HALF_X + 0.6, -HALF_Y + inset), 7, 5103),
        ((OPEN_HALF_X - 0.6, -HALF_Y + inset), (HALF_X - 3.4, -HALF_Y + inset), 7, 5104),
        ((-(HALF_X - 3.4), HALF_Y - inset), (-OPEN_HALF_X + 0.6, HALF_Y - inset), 7, 5105),
        ((OPEN_HALF_X - 0.6, HALF_Y - inset), (HALF_X - 3.4, HALF_Y - inset), 7, 5106),
    )
    for start, end, count, seed in runs:
        ak.greeble_strip(
            bm,
            (start[0], start[1], DECK_TOP),
            (end[0], end[1], DECK_TOP),
            count,
            seed,
            material="AA_Greeble",
            size_range=(0.42, 0.95),
            height_range=(0.14, 0.42),
            jitter=0.16,
        )


def build_floor() -> bpy.types.Object:
    bm = bmesh.new()
    _deck_plates(bm)
    _deck_ribs(bm)
    _parapets(bm)
    _wall_machinery(bm)
    _entry_chevrons(bm)
    return ak.new_object("Floor", bm)


# ==========================================================================
# 2. Les parois — `Rim_01..06`
# ==========================================================================

#: Profil d'une paroi. Face externe verticale (elle borne l'enveloppe a 30 x 18),
#: face interne en devers : de 0,55 m de deport au pied a 1,55 m a l'arete haute.
#: On voit donc la face interne depuis la camera de jeu — c'est elle qui dit
#: qu'on est DANS une cavite, et c'est la seule qui recoive du detail.
RIM_PROFILE = [
    (0.00, DECK_TOP, "AA_Greeble"),           # 0 pied externe
    (0.00, 1.30, "AA_Greeble"),               # 1 face externe (jamais vue)
    (0.00, 2.45, "AA_Greeble"),               # 2
    (0.12, RIM_TOP, "AA_Hull"),               # 3 chant superieur, sombre
    (RIM_BATTER - 0.22, RIM_TOP, "AA_Trim"),  # 4 lisere ivoire de 0,22 m
    (RIM_BATTER, RIM_TOP - 0.05, "AA_Hull"),  # 5 arete interne
    (RIM_BATTER - 0.10, 2.30, "AA_Hull"),     # 6 face interne haute
    (0.95, 1.55, "AA_Panel"),                 # 7 face interne mediane
    (0.62, 0.78, "AA_Hull"),                  # 8 face interne basse
    (0.55, DECK_TOP, "AA_Greeble"),           # 9 pied interne
]
RIM_INNER_BANDS = (6, 8)
RIM_PANEL_BAND = 7


def rim_paths() -> list[tuple[str, list[tuple[float, float]]]]:
    """Les six parois, en repere d'auteur, dans le sens horaire vu de Godot.

    Deux flancs longs sur toute la profondeur, quatre retours d'angle sur les bords
    haut/bas. Les retours d'angle MORDENT dans les flancs (`RIM_OVERLAP`) : une
    premiere version chanfreinait les angles, et le pont debordait alors le mur sur
    un triangle de 4,5 m2 — un trou noir dans chaque coin, parfaitement visible en
    vue de dessus. Un recouvrement franc coute quelques triangles caches et ne peut
    pas laisser de jour.

    Le milieu des bords haut/bas n'a volontairement AUCUNE paroi haute : voir
    « L'ECART ASSUME » en tete de module.
    """
    o = RIM_OVERLAP
    return [
        ("Rim_01", [(HALF_X, -HALF_Y), (HALF_X, HALF_Y)]),
        ("Rim_02", [(HALF_X - o, -HALF_Y), (OPEN_HALF_X, -HALF_Y)]),
        ("Rim_03", [(-OPEN_HALF_X, -HALF_Y), (-(HALF_X - o), -HALF_Y)]),
        ("Rim_04", [(-HALF_X, HALF_Y), (-HALF_X, -HALF_Y)]),
        ("Rim_05", [(-(HALF_X - o), HALF_Y), (-OPEN_HALF_X, HALF_Y)]),
        ("Rim_06", [(OPEN_HALF_X, HALF_Y), (HALF_X - o, HALF_Y)]),
    ]


#: Les quatre retours d'angle sont poses 2 cm plus bas que les flancs. Motif
#: mesure, pas esthetique : leurs chants superieurs sont coplanaires dans les
#: zones de recouvrement, et deux faces coplanaires produisent un damier de
#: z-fighting — quatre taches noires de 2 x 1,5 m dans les coins, parfaitement
#: visibles sur la premiere planche rendue.
RIM_END_DROP = 0.02


def build_rim(
    name: str, path: list[tuple[float, float]], drop: float = 0.0
) -> ak.MovingPart:
    bm = bmesh.new()
    profile = [(t, z - drop, m) for t, z, m in RIM_PROFILE]
    bands = _sweep(bm, path, profile)
    # Panneaux enfonces sur les seules faces internes : c'est la moitie de la
    # paroi que la camera voit, l'autre moitie ne merite pas un triangle.
    inner = [f for band in RIM_INNER_BANDS for f in bands[band]]
    _inset(bm, inner, "AA_Greeble", 0.10, -0.055, border="AA_Hull")
    # La bande mediane est la plus regardee : elle prend le violet de la charte,
    # segmente. C'est le seul endroit du decor ou le violet couvre une surface.
    _inset(bm, bands[RIM_PANEL_BAND], "AA_Panel", 0.14, -0.075, border="AA_Hull")
    return ak.moving_part(name, bm, (0.0, 0.0, 0.0))


# ==========================================================================
# 3. Les travees — `Catwalk_01..04`
# ==========================================================================

#: (nom, direction dans le plan d'auteur, portee exterieure)
#: Rappel : +Y d'auteur = BAS de l'ecran. `Catwalk_03` est donc la travee
#: d'entree, celle qui traverse la porte du parapet.
CATWALK_SPEC = (
    ("Catwalk_01", (0.0, -1.0), HALF_Y - PARAPET_DEPTH),
    ("Catwalk_02", (-1.0, 0.0), HALF_X - 0.55),
    ("Catwalk_03", (0.0, 1.0), HALF_Y),
    ("Catwalk_04", (1.0, 0.0), HALF_X - 0.55),
)
CATWALK_INNER = 1.95


def build_catwalk(name: str, direction: tuple[float, float], reach: float) -> ak.MovingPart:
    bm = bmesh.new()
    dx, dy = direction
    ax, ay = -dy, dx  # travers
    length = reach - CATWALK_INNER
    n_long = max(4, int(round(length / 0.92)))

    def point(s: float, t: float, z: float) -> tuple[float, float, float]:
        return (dx * s + ax * t, dy * s + ay * t, z)

    # Nappe superieure : n_long x 3 cellules. Trois dans le travers, parce qu'une
    # travee doit se lire comme un plancher a bordures, pas comme une poutre.
    verts = [
        [
            bm.verts.new(
                point(
                    CATWALK_INNER + length * i / n_long,
                    -CATWALK_HALF_W + 2.0 * CATWALK_HALF_W * j / 3,
                    CATWALK_TOP,
                )
            )
            for j in range(4)
        ]
        for i in range(n_long + 1)
    ]
    idx = ak.mat_index("AA_Hull")
    cells: list[list[bmesh.types.BMFace]] = []
    for i in range(n_long):
        column = []
        for j in range(3):
            face = bm.faces.new(
                (verts[i][j], verts[i + 1][j], verts[i + 1][j + 1], verts[i][j + 1])
            )
            face.material_index = idx
            column.append(face)
        cells.append(column)
    _skirt(bm, _boundary_loop(verts), CATWALK_BOTTOM, "AA_Greeble")

    middle = [cells[i][1] for i in range(n_long)]
    edges = [cells[i][j] for i in range(n_long) for j in (0, 2)]
    _inset(bm, middle, "AA_Greeble", 0.09, -0.045)
    _inset(bm, edges, "AA_Hull", 0.07, -0.030, border="AA_Trim")
    # Bandes d'avertissement au BOUT de la travee, contre la paroi. Elles etaient
    # d'abord au pied du reacteur : douze taches vert vif encerclaient la cible et
    # lui disputaient l'oeil, dans la seule zone de l'ecran ou il ne faut pas
    # hesiter. Le vert maladif de la charte est a « usage tres limite » ; il est
    # ici a l'endroit ou l'on ralentit, pas a celui ou l'on tire.
    ak.set_material([cells[-1][1]], "AA_Marking_Red")
    return ak.moving_part(name, bm, (0.0, 0.0, 0.0))


# ==========================================================================
# 4. Le reacteur — `Reactor`
# ==========================================================================

#: Coquille de revolution du reacteur, en UN seul contour ferme (hauteur, rayon,
#: materiau ; le materiau d'un point s'applique a la bande qui en part).
#:
#: LA CONTRAINTE QUI DECIDE DE CETTE FORME : la camera regarde a 20 deg de la
#: VERTICALE. Une premiere version coiffait le reacteur d'une calotte ivoire posee
#: AU-DESSUS de la lentille : rendue, la cible etait un bouton blanc et pas un
#: gramme de magenta n'atteignait l'ecran. C'est exactement le defaut que BRIEF-0026
#: avait deja paye sur le Specter-9. La partie emissive est donc ce qu'il y a de
#: PLUS HAUT, degagee de toute structure : un dome ouvert au ciel.
REACTOR_SHELL_BASE = [
    (-0.36, 0.00, "AA_Greeble"),          # pole bas, noye sous le pont
    (-0.36, REACTOR_R, "AA_Hull"),        # -> disque de fond (jamais vu)
    (0.18, REACTOR_R, "AA_Trim"),         # -> flanc externe de la couronne
    (0.12, 1.98, "AA_Greeble"),           # -> chant ivoire de la couronne
    (-0.42, 1.80, "AA_Greeble"),          # -> paroi interne de la douve
    (-0.50, 1.20, "AA_Hull"),             # -> fond de la douve
    (0.50, 1.30, "AA_Emissive_Engine"),   # -> fut anthracite
    (0.66, 1.12, "AA_Glass"),             # -> epaulement emissif (anneau magenta)
    (1.30, 1.12, "AA_Trim"),              # -> manchon translucide
    (1.46, 0.98, "AA_Emissive_Engine"),   # -> couronne ivoire
]

#: Dome emissif. 1,96 m de diametre apparent vu de dessus, soit 1,52 largeur de
#: chasseur : la cible se lit a la taille du vaisseau qui la vise, meme sous les
#: projectiles.
DOME_BASE_Z = 1.46
DOME_R = 0.98
DOME_H = 0.52
DOME_STEPS = 7

BUTTRESS_COUNT = 6
VENT_R = 1.55


def reactor_shell() -> list[tuple[float, float, str]]:
    contour = list(REACTOR_SHELL_BASE)
    for k in range(1, DOME_STEPS + 1):
        angle = math.pi * 0.5 * k / DOME_STEPS
        contour.append(
            (DOME_BASE_Z + DOME_H * math.sin(angle), DOME_R * math.cos(angle),
             "AA_Emissive_Engine")
        )
    return contour


def _buttress(bm: bmesh.types.BMesh, theta: float) -> None:
    """Arc-boutant ivoire : de la couronne au manchon, en arc rentrant.

    Six d'entre eux enjambent la douve. Vus de dessus ils decoupent l'anneau
    magenta de l'epaulement en six quartiers — c'est ce qui empeche la cible de
    se confondre avec un simple halo rond, meme noyee sous les tirs. Ils
    s'arretent SOUS le dome : rien ne doit passer au-dessus de l'emissif.
    """
    steps = 7
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    half_w, half_t = 0.155, 0.09
    rings = []
    for k in range(steps + 1):
        u = k / steps
        radius = 1.95 + (1.14 - 1.95) * (u ** 1.35)
        height = -0.10 + 1.52 * math.sin(u * math.pi * 0.5)
        cx, cy = radius * cos_t, radius * sin_t
        tx, ty = -sin_t, cos_t
        rings.append(
            ak.add_ring(
                bm,
                [
                    (cx + tx * half_w, cy + ty * half_w, height - half_t),
                    (cx - tx * half_w, cy - ty * half_w, height - half_t),
                    (cx - tx * half_w, cy - ty * half_w, height + half_t),
                    (cx + tx * half_w, cy + ty * half_w, height + half_t),
                ],
            )
        )
    for a, b in zip(rings, rings[1:]):
        ak.bridge_rings(bm, a, b, "AA_Trim", closed=True)
    ak.cap_ring(bm, rings[0], "AA_Trim")
    ak.cap_ring(bm, list(reversed(rings[-1])), "AA_Trim")


def _dome_ribs(bm: bmesh.types.BMesh) -> None:
    """Six meridiens sombres poses sur le dome.

    Sans eux le dome se lit comme une BULLE : une boule rose lisse, sans echelle
    ni mecanique, au milieu d'une arene industrielle. Les meridiens le rendent a
    ce qu'il doit etre — un iris segmente — et coutent 300 triangles.
    """
    for k in range(BUTTRESS_COUNT):
        theta = 2.0 * math.pi * (k + 0.5) / BUTTRESS_COUNT
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        tx, ty = -sin_t, cos_t
        half_w, half_t = 0.075, 0.045
        rings = []
        steps = 6
        for j in range(steps + 1):
            angle = math.pi * 0.5 * j / steps
            radius = (DOME_R + 0.02) * math.cos(angle)
            height = DOME_BASE_Z + (DOME_H + 0.02) * math.sin(angle)
            cx, cy = radius * cos_t, radius * sin_t
            rings.append(
                ak.add_ring(
                    bm,
                    [
                        (cx + tx * half_w, cy + ty * half_w, height - half_t),
                        (cx - tx * half_w, cy - ty * half_w, height - half_t),
                        (cx - tx * half_w, cy - ty * half_w, height + half_t),
                        (cx + tx * half_w, cy + ty * half_w, height + half_t),
                    ],
                )
            )
        for a, b in zip(rings, rings[1:]):
            ak.bridge_rings(bm, a, b, "AA_Greeble", closed=True)
        ak.cap_ring(bm, rings[0], "AA_Greeble")
        ak.cap_ring(bm, list(reversed(rings[-1])), "AA_Greeble")


def _vent_slots(bm: bmesh.types.BMesh) -> None:
    """Six braises magenta au fond de la douve, entre les arcs-boutants.

    Elles elargissent la part emissive du reacteur SANS deborder sur le decor :
    tout ce qui brille dans cette arene appartient a la cible, et rien d'autre.
    """
    for k in range(BUTTRESS_COUNT):
        theta = 2.0 * math.pi * (k + 0.5) / BUTTRESS_COUNT
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        # Le fond de la douve est incline : on lit sa hauteur au rayon de l'event.
        floor = -0.42 + (-0.50 + 0.42) * (1.80 - VENT_R) / (1.80 - 1.20)
        cx, cy = VENT_R * cos_t, VENT_R * sin_t
        tx, ty = -sin_t, cos_t
        half_l, half_w = 0.30, 0.13
        low = ak.add_ring(
            bm,
            [
                (cx + tx * half_l + cos_t * half_w, cy + ty * half_l + sin_t * half_w, floor),
                (cx - tx * half_l + cos_t * half_w, cy - ty * half_l + sin_t * half_w, floor),
                (cx - tx * half_l - cos_t * half_w, cy - ty * half_l - sin_t * half_w, floor),
                (cx + tx * half_l - cos_t * half_w, cy + ty * half_l - sin_t * half_w, floor),
            ],
        )
        high = ak.add_ring(bm, [(v.co.x, v.co.y, floor + 0.07) for v in low])
        ak.bridge_rings(bm, low, high, "AA_Emissive_Engine", closed=True)
        ak.cap_ring(bm, high, "AA_Emissive_Engine")
        ak.cap_ring(bm, list(reversed(low)), "AA_Emissive_Engine")


def build_reactor() -> ak.MovingPart:
    bm = bmesh.new()
    # axis="Z" : le reacteur est un solide de revolution VERTICAL. Le kit tourne
    # autour de Y par defaut — l'oublier couche la cible sur le flanc, et seule la
    # hauteur de la bounding box le signale.
    ak.add_lathe(bm, reactor_shell(), REACTOR_SEG, axis="Z")
    for k in range(BUTTRESS_COUNT):
        _buttress(bm, 2.0 * math.pi * k / BUTTRESS_COUNT)
    _dome_ribs(bm)
    _vent_slots(bm)
    return ak.moving_part("Reactor", bm, (0.0, 0.0, 0.0))


# ==========================================================================
# 5. Points d'ancrage
# ==========================================================================


def build_attach_points() -> list[bpy.types.Object]:
    """`Reactor_Core` au centre de masse de la cible, `Entry_Point` sur la porte.

    Les deux sont poses en repere d'AUTEUR ; `export_hull()` les transporte.
    `Entry_Point` est a +Y d'auteur, donc +Z Godot, donc au bas de l'ecran : c'est
    le seul temoin asymetrique de la scene, et c'est lui qui prouve au contrat que
    l'arene n'est pas exportee a l'envers.
    """
    return [
        ak.attach_point("Reactor_Core", (0.0, 0.0, 1.10)),
        ak.attach_point("Entry_Point", (0.0, HALF_Y - 1.40, PLANE_Z)),
    ]


# ==========================================================================
# Harnais de mesure
# ==========================================================================


def fighter_envelope() -> tuple[float, float, float]:
    """(largeur X, hauteur Y, longueur Z) du Specter-9, lue dans son `.glb`.

    On parcourt les noeuds et non les maillages : les volets et les tuyeres du
    chasseur sont des pieces mobiles dont la position vit dans la translation du
    noeud (meme piege que dans `_validate_glb` du kit).
    """
    if not os.path.isfile(FIGHTER):
        return (FIGHTER_W, 0.65, FIGHTER_L)
    with open(FIGHTER, "rb") as handle:
        data = handle.read()
    length = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20 : 20 + length])
    world: dict[int, list[float]] = {}

    def walk(index: int, base: list[float]) -> None:
        node = gltf["nodes"][index]
        t = node.get("translation", [0.0, 0.0, 0.0])
        here = [base[a] + t[a] for a in range(3)]
        world[index] = here
        for child in node.get("children", []):
            walk(child, here)

    for root in gltf.get("scenes", [{}])[0].get("nodes", []):
        walk(root, [0.0, 0.0, 0.0])
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for index, node in enumerate(gltf.get("nodes", [])):
        if "mesh" not in node:
            continue
        offset = world.get(index, [0.0, 0.0, 0.0])
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            acc = gltf["accessors"][prim["attributes"]["POSITION"]]
            for axis in range(3):
                lo[axis] = min(lo[axis], acc["min"][axis] + offset[axis])
                hi[axis] = max(hi[axis], acc["max"][axis] + offset[axis])
    return (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])


def _bounds(objs: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    lo = Vector((9e9, 9e9, 9e9))
    hi = Vector((-9e9, -9e9, -9e9))
    for obj in objs:
        for vert in obj.data.vertices:
            for a in range(3):
                lo[a] = min(lo[a], vert.co[a])
                hi[a] = max(hi[a], vert.co[a])
    return lo, hi


def _triangles(obj: bpy.types.Object) -> int:
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def _assert_clearance(objs: list[bpy.types.Object]) -> float:
    """Aucune geometrie au-dessus de 0,9 m dans le disque de rayon 11, hors reacteur.

    C'est LE critere qui rendait la version precedente injouable en creux : une
    sphere de 7 m refermee autour de tout. On ne le suppose pas tenu, on le mesure
    sur les sommets, et on echoue avant l'export.
    """
    worst = 9e9
    culprit = ""
    for obj in objs:
        if obj.name == "Reactor":
            continue
        for vert in obj.data.vertices:
            if vert.co.z <= CLEARANCE_Z:
                continue
            radius = math.hypot(vert.co.x, vert.co.y)
            if radius < worst:
                worst, culprit = radius, obj.name
    print(
        f"--- degagement du couloir : premier obstacle au-dessus de "
        f"{CLEARANCE_Z:.2f} m a r = {worst:.3f} m ({culprit or 'aucun'}) ---"
    )
    if worst < CLEARANCE_R:
        raise ak.ContractError(
            f"geometrie a r = {worst:.3f} m au-dessus de {CLEARANCE_Z} m "
            f"({culprit}) : le disque de rayon {CLEARANCE_R} m doit rester libre."
        )
    return worst


def _assert_target_uncapped(reactor: bpy.types.Object) -> tuple[float, float]:
    """Rien de structurel ne doit passer AU-DESSUS de l'emissif du reacteur.

    Ce controle existe parce que le defaut a ete commis ici meme, et qu'il n'a
    ete vu qu'au rendu : la premiere version coiffait la lentille d'une calotte
    ivoire. Vue de dessus — c'est-a-dire vue du jeu — la cible etait un bouton
    blanc, et pas un pixel de magenta n'arrivait a l'ecran. Ni la bounding box,
    ni le budget, ni le contrat de materiaux ne disent quoi que ce soit de ce
    qui CACHE quoi. Celui-ci, si.

    Seul `AA_Greeble` est tolere au-dessus : ce sont les six meridiens poses sur
    le dome, qui le segmentent sans le masquer. Et l'on ne regarde QUE la colonne
    verticale du dome (rayon < DOME_R) : les arcs-boutants montent plus haut que
    la base du dome, mais a cote de lui, pas devant.
    """
    emissive = ak.mat_index("AA_Emissive_Engine")
    ribs = ak.mat_index("AA_Greeble")
    mesh = reactor.data
    top_emissive = -9e9
    top_structure = -9e9
    for poly in mesh.polygons:
        verts = [mesh.vertices[i].co for i in poly.vertices]
        z = max(v.z for v in verts)
        if poly.material_index == emissive:
            top_emissive = max(top_emissive, z)
        elif poly.material_index != ribs and min(
            math.hypot(v.x, v.y) for v in verts
        ) < DOME_R - 0.02:
            top_structure = max(top_structure, z)
    shadowed = "aucune" if top_structure < -1e8 else f"z = {top_structure:.3f} m"
    print(
        f"--- cible degagee : emissif jusqu'a z = {top_emissive:.3f} m ; "
        f"structure dans la colonne du dome : {shadowed} ---"
    )
    if top_structure > DOME_BASE_Z + 0.05:
        raise ak.ContractError(
            f"structure du reacteur a z = {top_structure:.3f} m, au-dessus de la "
            f"base du dome ({DOME_BASE_Z:.3f} m) : elle masquerait l'emissif en "
            "vue de dessus, qui est la vue du jeu."
        )
    return top_emissive, top_structure


def _report_scale(objs: list[bpy.types.Object]) -> None:
    """Tout se mesure en chasseurs. C'est l'objet meme de ce brief.

    Le defaut a ne pas refaire (`Ring_01..05` a 0,33 m pour un vaisseau de 1,29 m)
    n'a ete vu par aucun controle existant : ni la bounding box, ni le budget de
    triangles, ni les materiaux ne parlent d'echelle relative. Celui-ci, si.
    """
    lo, hi = _bounds(objs)
    width, height, length = fighter_envelope()
    rows = [
        ("arene, largeur", hi.x - lo.x, width),
        ("arene, profondeur", hi.y - lo.y, length),
        ("reacteur, diametre", 2.0 * REACTOR_R, width),
        ("dome emissif, diametre", 2.0 * DOME_R, width),
        ("travee, largeur", 2.0 * CATWALK_HALF_W, width),
        ("porte d'entree, largeur", 2.0 * ENTRY_GAP_HALF, width),
        ("ouverture des bords longs", 2.0 * OPEN_HALF_X, width),
        ("passage reacteur <-> paroi", HALF_X - 0.55 - REACTOR_R, width),
        ("passage reacteur <-> parapet", HALF_Y - PARAPET_DEPTH - REACTOR_R, width),
        ("garde au sol sous le chasseur", PLANE_Z - DECK_TOP, height),
    ]
    print(
        f"--- echelle mesuree CONTRE LE SPECTER-9 REEL "
        f"({width:.3f} x {height:.3f} x {length:.3f} m, lu dans specter_9.glb) ---"
    )
    if abs(width - 1.29) < 0.05:
        print("  (le brief annonce 1,29 m de large : c'est bien la valeur du fichier)")
    else:
        print(
            f"  ATTENTION : le brief annonce 1,29 m de large, le fichier en mesure "
            f"{width:.3f}. Toutes les colonnes ci-dessous emploient la valeur MESUREE."
        )
    for label, value, unit in rows:
        kind = "hauteurs" if unit == height else ("longueurs" if unit == length else "largeurs")
        print(f"  {label:<30} {value:7.3f} m = {value / unit:6.2f} {kind} de chasseur")
    narrow = min(
        HALF_X - 0.55 - REACTOR_R,
        HALF_Y - PARAPET_DEPTH - REACTOR_R,
        2.0 * ENTRY_GAP_HALF,
    )
    print(
        f"  passage le plus etroit         {narrow:7.3f} m = {narrow / width:6.2f} "
        "largeurs de chasseur (plancher : 2,50)"
    )
    if narrow < 2.5 * width:
        raise ak.ContractError(
            f"passage le plus etroit {narrow:.2f} m = {narrow / width:.2f} "
            "chasseur : sous le plancher de 2,5 largeurs, on ne peut pas y manoeuvrer."
        )


def _assert_texcoords(path: str) -> tuple[int, int, int]:
    """Relit le `.glb` PRODUIT et compte `TEXCOORD_0` / `TANGENT`.

    Quatre coques du depot sont sorties sans UV : l'exporteur n'emet aucun
    avertissement, la bounding box est parfaite, le contrat passe — et plus aucune
    feuille de detail (ADR-0011) ne peut s'y poser. On le verifie sur le fichier.
    """
    with open(path, "rb") as handle:
        data = handle.read()
    length = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20 : 20 + length])
    total = with_uv = with_tan = 0
    for mesh in gltf.get("meshes", []):
        for prim in mesh["primitives"]:
            total += 1
            with_uv += 1 if "TEXCOORD_0" in prim["attributes"] else 0
            with_tan += 1 if "TANGENT" in prim["attributes"] else 0
    print(
        f"--- UV du .glb livre : {with_uv}/{total} primitives portent TEXCOORD_0, "
        f"{with_tan}/{total} portent TANGENT ---"
    )
    if total == 0 or with_uv != total:
        raise ak.ContractError(
            f"{path} : {total - with_uv} primitive(s) sans TEXCOORD_0."
        )
    return with_uv, with_tan, total


# ==========================================================================
# Assemblage
# ==========================================================================


def _triangulate_ngons(obj: bpy.types.Object) -> None:
    """Decoupe les seules faces de plus de 4 sommets.

    Sans cela l'exporteur renonce aux TANGENTES (« tangent space can only be
    computed for tris/quads ») et ADR-0011 devient inoperant.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(obj.data)
    bm.free()


def _finish(obj: bpy.types.Object, bevel: bool) -> None:
    ak.cleanup(obj)
    if bevel:
        # Chanfrein a 1 segment, et pas sur le pont : les 220 plaques enfoncees du
        # sol offrent 1 800 aretes vives dont aucune ne se voit a 20 deg de la
        # verticale — les biseauter couterait la moitie du budget pour rien.
        ak.bevel_sharp_edges(obj, width=0.018, segments=1, angle_deg=34.0)
    _triangulate_ngons(obj)
    ak.shade_smooth_by_angle(obj, angle_deg=26.0)
    ak.box_project_uv(obj, TEXELS_PER_METER)


def build() -> tuple[bpy.types.Object, list[ak.MovingPart], list[bpy.types.Object]]:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)

    floor = build_floor()
    parts = [build_reactor()]
    parts += [build_catwalk(*spec) for spec in CATWALK_SPEC]
    parts += [
        build_rim(name, path, RIM_END_DROP if name not in ("Rim_01", "Rim_04") else 0.0)
        for name, path in rim_paths()
    ]

    _finish(floor, bevel=False)
    for part in parts:
        _finish(part.obj, bevel=True)
    return floor, parts, build_attach_points()


def main() -> None:
    floor, parts, anchors = build()
    objs = [floor] + [p.obj for p in parts]

    lo, hi = _bounds(objs)
    print("--- mesures en repere d'auteur (avant correction d'axe) ---")
    total_tris = 0
    for obj in objs:
        o_lo, o_hi = _bounds([obj])
        tris = _triangles(obj)
        total_tris += tris
        print(
            f"  {obj.name:<12} x[{o_lo.x:+8.3f} {o_hi.x:+8.3f}] "
            f"y[{o_lo.y:+8.3f} {o_hi.y:+8.3f}] z[{o_lo.z:+7.3f} {o_hi.z:+7.3f}] "
            f"{tris:6d} tris"
        )
    print(
        f"  {'TOTAL':<12} x[{lo.x:+8.3f} {hi.x:+8.3f}] y[{lo.y:+8.3f} {hi.y:+8.3f}] "
        f"z[{lo.z:+7.3f} {hi.z:+7.3f}]  ->  {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} "
        f"x {hi.z - lo.z:.3f} m, {total_tris} tris "
        f"({100.0 * total_tris / TRI_BUDGET:.1f} % du budget)"
    )

    _assert_clearance(objs)
    _assert_target_uncapped(parts[0].obj)
    _report_scale(objs)

    ak.export_hull(floor, anchors, OUTPUT, CONTRACT, parts=parts)
    _assert_texcoords(OUTPUT)

    if "--plate" in sys.argv:
        stats = render_plate()
        # L'echec vient APRES l'ecriture de la planche : un contraste insuffisant
        # se corrige en le regardant, pas en lisant un nombre sans son image.
        if stats["gap"] < 25.0:
            raise ak.ContractError(
                f"ecart R-G de {stats['gap']:.2f} points < 25 : le decor ne recule "
                "pas assez derriere la cible (BRIEF-0082)."
            )



# ==========================================================================
# Planche de recette — `--plate`
# ==========================================================================
# Un livrable de la forge n'est pas un asset valide tant qu'il n'a pas ete rendu
# et REGARDE (ADR-0006). Ici la planche fait davantage : elle PROUVE l'echelle.
# La quatrieme vue pose cinq Specter-9 reels — le meme `.glb` que le jeu charge —
# sur le pont, a la meme projection orthographique que la premiere. C'est la seule
# image qui aurait attrape les anneaux de 30 cm de la coque du boss.

TILE_W, TILE_H = 900, 620
SAMPLES = 96
BACKDROP = (0.0027, 0.0039, 0.0070, 1.0)   # #070A12, le fond spatial du jeu
TOP_SCALE = 31.6                            # emprise horizontale des vues de dessus

#: Positions des chasseurs de la vue 4, en coordonnees GODOT (x, z) — celles que
#: le code manipulera. +Z est le bas de l'ecran, la ou l'on entre.
FIGHTER_POSES = (
    (0.0, 7.55, 0.0),      # sur le point d'entree, dans la porte du parapet
    (0.0, 3.90, 0.0),      # remontant la travee d'entree
    (4.35, 0.20, 18.0),    # en rase-mottes le long du reacteur
    (-9.60, -3.10, -12.0),  # au large, entre reacteur et paroi babord
    (10.40, 5.30, 8.0),    # au plus pres de la paroi tribord, sans la mordre
)


def _plate_reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    world = bpy.data.worlds.new("plate")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = BACKDROP
    bpy.context.scene.world = world
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"          # WSL sans GPU fiable (ADR-0002)
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.resolution_x = TILE_W
    scene.render.resolution_y = TILE_H
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    # AgX (le defaut de Blender 4.x) desature violemment les hautes lumieres : la
    # dome magenta ressortirait blanc et la mesure R-G du brief serait fausse.
    # « Standard » rend les couleurs telles que les materiaux les portent.
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"


def _plate_lights() -> None:
    """Trois sources larges. Une arene de 30 m eclairee comme un jouet ne se lit pas."""
    for name, position, energy, size, color in (
        ("Key", (-16.0, -26.0, 24.0), 42000.0, 22.0, (0.86, 0.88, 1.00)),
        ("Fill", (22.0, 14.0, 12.0), 15000.0, 30.0, (0.72, 0.66, 0.86)),
        ("Rim", (0.0, 30.0, 8.0), 20000.0, 18.0, (0.95, 0.80, 0.92)),
    ):
        data = bpy.data.lights.new(name, type="AREA")
        data.energy = energy
        data.size = size
        data.color = color
        light = bpy.data.objects.new(name, data)
        light.location = position
        light.rotation_euler = (
            (-Vector(position)).to_track_quat("-Z", "Y").to_euler()
        )
        bpy.context.collection.objects.link(light)


def _camera(name: str, location, rotation, ortho: float | None, fov: float = 40.0):
    data = bpy.data.cameras.new(name)
    if ortho is not None:
        data.type = "ORTHO"
        data.ortho_scale = ortho
    else:
        data.lens_unit = "FOV"
        data.angle = math.radians(fov)
    camera = bpy.data.objects.new(name, data)
    camera.location = location
    camera.rotation_euler = rotation
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    return camera


def _text_material() -> bpy.types.Material:
    mat = bpy.data.materials.get("PLATE_TEXT")
    if mat is not None:
        return mat
    mat = bpy.data.materials.new("PLATE_TEXT")
    mat.use_nodes = True
    tree = mat.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    emit = tree.nodes.new("ShaderNodeEmission")
    emit.inputs[0].default_value = (0.92, 0.94, 0.98, 1.0)
    emit.inputs[1].default_value = 1.0
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(emit.outputs[0], out.inputs[0])
    return mat


def _label(
    camera, body: str, frame_w: float, u: float, v: float, size: float,
    align: str = "LEFT", distance: float = 4.0, aspect: float = TILE_H / TILE_W,
) -> bpy.types.Object:
    """Pose un texte DANS LE REPERE DE LA CAMERA, a `distance` devant elle.

    Parenter le texte a la camera evite d'avoir a projeter des coordonnees monde :
    la meme legende se pose identiquement sur une vue orthographique et sur une
    perspective. `u`/`v` sont des fractions de la largeur/hauteur du cadre.
    """
    frame_h = frame_w * aspect
    curve = bpy.data.curves.new("label", type="FONT")
    curve.body = body
    curve.size = size * frame_h
    curve.align_x = align
    curve.align_y = "CENTER"
    obj = bpy.data.objects.new("label", curve)
    obj.data.materials.append(_text_material())
    bpy.context.collection.objects.link(obj)
    obj.parent = camera
    obj.matrix_parent_inverse.identity()
    obj.location = (u * frame_w, v * frame_h, -distance)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    return obj


def _render(path: str, width: int = TILE_W, height: int = TILE_H) -> None:
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x, scene.render.resolution_y = TILE_W, TILE_H


def _read_png(path: str, width: int, height: int):
    import numpy as np

    image = bpy.data.images.load(path)
    buffer = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(buffer)
    bpy.data.images.remove(image)
    return buffer.reshape(height, width, 4)


def _stack(top: str, bottom: str, out: str, height: int) -> None:
    """Empile deux bandes en une tuile. Les images Blender sont ecrites du bas
    vers le haut : la premiere bande va donc dans la moitie HAUTE du tableau."""
    import numpy as np

    tile = np.zeros((TILE_H, TILE_W, 4), dtype=np.float32)
    tile[:, :, 3] = 1.0
    tile[TILE_H - height :, :, :] = _read_png(top, TILE_W, height)
    tile[: TILE_H - height, :, :] = _read_png(
        bottom, TILE_W, TILE_H - height
    )
    tile[TILE_H - height, :, :3] = 0.10
    image = bpy.data.images.new("tile3", width=TILE_W, height=TILE_H)
    image.pixels.foreach_set(tile.reshape(-1))
    image.filepath_raw = out
    image.file_format = "PNG"
    image.save()


def _load_srgb(path: str):
    """Relit un PNG en valeurs sRGB brutes (0-1), sans conversion lineaire.

    C'est ce qu'exige la mesure du brief : « au moins 25 points d'ecart R-G »
    s'entend sur des octets d'image, pas sur des intensites lineaires.
    """
    import numpy as np

    image = bpy.data.images.load(path)
    image.colorspace_settings.name = "Non-Color"
    buffer = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(buffer)
    bpy.data.images.remove(image)
    return buffer.reshape(TILE_H, TILE_W, 4)


def _import_fighter() -> bpy.types.Object:
    """Importe le Specter-9 REEL et le fond en un seul objet.

    Pas de bloc de substitution aux cotes du chasseur : c'est le fichier que le
    jeu charge qui est pose sur le pont. Une maquette « a peu pres a l'echelle »
    reintroduirait exactement le defaut que cette planche doit exclure.
    """
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=FIGHTER)
    fresh = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in fresh if o.type == "MESH"]
    for obj in fresh:
        if obj.type != "MESH":
            bpy.data.objects.remove(obj, do_unlink=True)
    joined = ak.join_objects(meshes, "Specter9_Ref")
    joined.location = (0.0, 0.0, -900.0)   # au rebut : seuls ses clones servent
    return joined


def _place_fighters(source: bpy.types.Object) -> list[bpy.types.Object]:
    clones = []
    for index, (gx, gz, yaw) in enumerate(FIGHTER_POSES):
        clone = source.copy()          # donnees partagees : aucun cout memoire
        clone.data = source.data
        clone.name = f"Specter9_{index + 1}"
        # Repere Blender apres import glTF : Godot (x, y, z) -> (x, z, -y).
        clone.location = (gx, -gz, 0.0)
        clone.rotation_euler = (0.0, 0.0, math.radians(yaw))
        bpy.context.collection.objects.link(clone)
        clones.append(clone)
    return clones


def _in_fighters(label: str, value: float, width: float) -> str:
    """« travee 3,20 m = 1,8 chasseur » — la seule unite qui compte ici."""
    return (
        f"{label} {value:.2f} m = {value / width:.1f} chasseur"
        f"{'s' if value / width >= 2.0 else ''}"
    ).replace(".", ",")


def _measure_contrast(top_camera) -> dict:
    """Mesure l'ecart R-G entre le reacteur et l'ensemble sol + parois.

    Methode : deux rendus de la MEME vue de dessus. Le premier est la vue de
    recette. Le second remplace tous les materiaux par des emissions plates —
    rouge pour le reacteur, vert pour sol + parois, bleu pour les travees — et
    sert de masque exact. Aucune selection de pixels a l'oeil, aucun seuil de
    teinte : la mesure porte sur les objets nommes du contrat.
    """
    import numpy as np

    scene = bpy.context.scene
    scene.camera = top_camera
    beauty_path = "/tmp/_core_measure_beauty.png"
    _render(beauty_path)
    beauty = _load_srgb(beauty_path)

    groups = {}
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        if obj.name == "Reactor":
            groups[obj.name] = (1.0, 0.0, 0.0)
        elif obj.name == "Floor" or obj.name.startswith("Rim_"):
            groups[obj.name] = (0.0, 1.0, 0.0)
        else:
            groups[obj.name] = (0.0, 0.0, 1.0)

    saved: dict[str, list] = {}
    flats: dict[tuple, bpy.types.Material] = {}
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        colour = groups[obj.name]
        if colour not in flats:
            mat = bpy.data.materials.new("ID_%d%d%d" % colour)
            mat.use_nodes = True
            tree = mat.node_tree
            for node in list(tree.nodes):
                tree.nodes.remove(node)
            emit = tree.nodes.new("ShaderNodeEmission")
            emit.inputs[0].default_value = (*colour, 1.0)
            out = tree.nodes.new("ShaderNodeOutputMaterial")
            tree.links.new(emit.outputs[0], out.inputs[0])
            flats[colour] = mat
        saved[obj.name] = [slot.material for slot in obj.material_slots]
        for slot in obj.material_slots:
            slot.material = flats[colour]

    world_colour = scene.world.node_tree.nodes["Background"].inputs[0].default_value[:]
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    samples, denoise, filter_size = (
        scene.cycles.samples, scene.cycles.use_denoising, scene.render.filter_size
    )
    # Filtre quasi nul : on veut des masques francs, pas des bords fondus qui
    # melangeraient un pixel de reacteur et un pixel de paroi.
    scene.cycles.samples, scene.cycles.use_denoising = 1, False
    scene.render.filter_size = 0.01
    id_path = "/tmp/_core_measure_id.png"
    _render(id_path)
    ident = _load_srgb(id_path)
    scene.cycles.samples, scene.cycles.use_denoising = samples, denoise
    scene.render.filter_size = filter_size
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = world_colour
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        for slot, mat in zip(obj.material_slots, saved[obj.name]):
            slot.material = mat

    reactor = (ident[:, :, 0] > 0.6) & (ident[:, :, 1] < 0.4)
    decor = (ident[:, :, 1] > 0.6) & (ident[:, :, 0] < 0.4)
    out = {}
    for label, mask in (("reactor", reactor), ("decor", decor)):
        pixels = beauty[mask]
        red, green = float(pixels[:, 0].mean()) * 255.0, float(pixels[:, 1].mean()) * 255.0
        blue = float(pixels[:, 2].mean()) * 255.0
        out[label] = {
            "px": int(mask.sum()), "R": red, "G": green, "B": blue, "R-G": red - green,
        }
    out["gap"] = out["reactor"]["R-G"] - out["decor"]["R-G"]
    print("--- contraste mesure sur la vue de dessus (sRGB 0-255) ---")
    for label in ("reactor", "decor"):
        row = out[label]
        print(
            f"  {label:<8} {row['px']:7d} px   R={row['R']:6.2f} G={row['G']:6.2f} "
            f"B={row['B']:6.2f}   R-G = {row['R-G']:+7.2f}"
        )
    print(f"  ecart R-G reacteur - decor = {out['gap']:+.2f} points (plancher : 25)")
    return out


def _compose(tiles: list[str], out: str) -> None:
    import numpy as np

    sheet = np.zeros((TILE_H * 2, TILE_W * 2, 4), dtype=np.float32)
    sheet[:, :, 3] = 1.0
    for index, path in enumerate(tiles):
        image = bpy.data.images.load(path)
        buffer = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(buffer)
        bpy.data.images.remove(image)
        tile = buffer.reshape(TILE_H, TILE_W, 4)
        row, column = index // 2, index % 2
        # Les images Blender sont stockees de bas en haut : la ligne 0 est en bas.
        top = (1 - row) * TILE_H
        sheet[top : top + TILE_H, column * TILE_W : (column + 1) * TILE_W] = tile
    for axis in (TILE_H - 1, TILE_H, TILE_H + 1):
        sheet[axis, :, :3] = 0.10
    for axis in (TILE_W - 1, TILE_W, TILE_W + 1):
        sheet[:, axis, :3] = 0.10
    result = bpy.data.images.new("plate", width=TILE_W * 2, height=TILE_H * 2)
    result.pixels.foreach_set(sheet.reshape(-1))
    result.filepath_raw = out
    result.file_format = "PNG"
    result.save()


def render_plate() -> dict:
    _plate_reset()
    bpy.ops.import_scene.gltf(filepath=OUTPUT)
    # L'importateur glTF ajoute un vide de scene ; il ne gene rien, on le laisse.
    _plate_lights()

    top = _camera("top", (0.0, 0.0, 30.0), (0.0, 0.0, 0.0), ortho=TOP_SCALE)
    stats = _measure_contrast(top)

    tiles = []

    # --- 1. vue de dessus ------------------------------------------------
    bpy.context.scene.camera = top
    labels = [
        _label(top, "1 — VUE DE DESSUS (orthographique) — la lecture du jeu",
               TOP_SCALE, -0.472, 0.455, 0.032),
        _label(top, "arene 30,0 x 18,0 m   |   bornes de jeu 28 x 16 m",
               TOP_SCALE, -0.472, 0.405, 0.026),
        _label(top, f"REACTEUR {2.0 * REACTOR_R:.2f} m".replace(".", ","),
               TOP_SCALE, 0.0, -0.175, 0.026, align="CENTER"),
        _label(top, "ENTREE", TOP_SCALE, 0.0, -0.435, 0.026, align="CENTER"),
        _label(top, f"ecart R-G reacteur/decor : {stats['gap']:+.1f} points",
               TOP_SCALE, 0.472, 0.455, 0.026, align="RIGHT"),
    ]
    _render("/tmp/_core_v1.png")
    tiles.append("/tmp/_core_v1.png")
    for obj in labels:
        bpy.data.objects.remove(obj, do_unlink=True)

    # --- 2. trois quarts -------------------------------------------------
    eye = Vector((-19.0, -25.0, 21.0))
    quarter = _camera(
        "quarter", eye, (-eye).to_track_quat("-Z", "Y").to_euler(), ortho=None, fov=42.0
    )
    frame = 2.0 * 4.0 * math.tan(math.radians(42.0) * 0.5)
    labels = [
        _label(quarter, "2 — TROIS QUARTS — on est DANS une cavite",
               frame, -0.472, 0.455, 0.032),
        _label(quarter, "parois 3,52 m, devers 1,55 m vers l'interieur",
               frame, -0.472, 0.405, 0.026),
    ]
    _render("/tmp/_core_v2.png")
    tiles.append("/tmp/_core_v2.png")
    for obj in labels:
        bpy.data.objects.remove(obj, do_unlink=True)

    # --- 3. coupes ------------------------------------------------------
    # Deux bandes empilees. En orthographique, `clip_start` EST le plan de coupe :
    # la moitie proche disparait et l'on voit l'arene ouverte, comme sur une coupe
    # d'atelier. Une seule coupe laissait les deux tiers de la tuile vides — une
    # arene de 3,84 m de haut pour 30 m de large ne remplit pas un cadre carre.
    half = TILE_H // 2
    aspect_a = half / TILE_W
    section_x = _camera("section_x", (0.0, -40.0, 1.35), (math.pi * 0.5, 0.0, 0.0),
                        ortho=TOP_SCALE)
    section_x.data.clip_start = 40.0
    section_x.data.clip_end = 90.0
    labels = [
        _label(section_x, "3 — COUPES.  En travers, plan Godot Z = 0 (regard vers le haut de l'ecran)",
               TOP_SCALE, -0.478, 0.38, 0.075, distance=41.0, aspect=aspect_a),
        _label(section_x, "hauteur totale 3,84 m   |   pont -0,30   |   vol 0,00   |   parois +3,22",
               TOP_SCALE, -0.478, 0.25, 0.060, distance=41.0, aspect=aspect_a),
    ]
    _render("/tmp/_core_v3a.png", TILE_W, half)
    for obj in labels:
        bpy.data.objects.remove(obj, do_unlink=True)

    aspect_b = (TILE_H - half) / TILE_W
    section_y = _camera("section_y", (-40.0, 0.0, 1.35),
                        (math.pi * 0.5, 0.0, -math.pi * 0.5), ortho=21.0)
    section_y.data.clip_start = 40.0
    section_y.data.clip_end = 90.0
    labels = [
        _label(section_y, "En long, plan Godot X = 0 — a droite : le haut de l'ecran",
               21.0, -0.478, 0.38, 0.075, distance=41.0, aspect=aspect_b),
        _label(section_y, "parapets 0,75 m : ils ferment le cadre sans jamais entrer dans le couloir",
               21.0, -0.478, 0.25, 0.060, distance=41.0, aspect=aspect_b),
    ]
    _render("/tmp/_core_v3b.png", TILE_W, TILE_H - half)
    for obj in labels:
        bpy.data.objects.remove(obj, do_unlink=True)
    _stack("/tmp/_core_v3a.png", "/tmp/_core_v3b.png", "/tmp/_core_v3.png", half)
    tiles.append("/tmp/_core_v3.png")

    # --- 4. dessus + Specter-9 a l'echelle -------------------------------
    source = _import_fighter()
    clones = _place_fighters(source)
    fw = fighter_envelope()[0]
    lo = Vector((9e9, 9e9, 9e9))
    hi = Vector((-9e9, -9e9, -9e9))
    for corner in source.bound_box:
        point = source.matrix_world @ Vector(corner)
        for a in range(3):
            lo[a] = min(lo[a], point[a])
            hi[a] = max(hi[a], point[a])
    print(
        "--- Specter-9 pose sur la planche : "
        f"{hi.x - lo.x:.3f} x {hi.z - lo.z:.3f} x {hi.y - lo.y:.3f} m "
        "(X x Y x Z Godot), 5 exemplaires ---"
    )
    bpy.context.scene.camera = top
    labels = [
        _label(top, "4 — VUE DE DESSUS AVEC LE SPECTER-9 A L'ECHELLE",
               TOP_SCALE, -0.472, 0.455, 0.032),
        _label(top,
               f"5 x specter_9.glb, {hi.x - lo.x:.2f} x {hi.y - lo.y:.2f} m "
               "— meme fichier que le jeu",
               TOP_SCALE, -0.472, 0.405, 0.026),
        _label(top, _in_fighters("reacteur", 2.0 * REACTOR_R, fw),
               TOP_SCALE, 0.472, 0.455, 0.026, align="RIGHT"),
        _label(top, _in_fighters("travee", 2.0 * CATWALK_HALF_W, fw),
               TOP_SCALE, 0.472, 0.405, 0.026, align="RIGHT"),
        _label(top, _in_fighters("porte", 2.0 * ENTRY_GAP_HALF, fw),
               TOP_SCALE, 0.0, -0.435, 0.026, align="CENTER"),
    ]
    _render("/tmp/_core_v4.png")
    tiles.append("/tmp/_core_v4.png")
    for obj in labels:
        bpy.data.objects.remove(obj, do_unlink=True)
    for clone in clones:
        bpy.data.objects.remove(clone, do_unlink=True)

    os.makedirs(os.path.dirname(PLATE), exist_ok=True)
    _compose(tiles, PLATE)
    print(f"\n-> {PLATE}")
    return stats


if __name__ == "__main__":
    main()
