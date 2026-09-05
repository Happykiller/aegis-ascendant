"""build_leech_drone.py — coque 3D du Leech Drone, chasseur d'accrochage (BRIEF-0044).

    blender-aegis -b -P tools/blender/build_leech_drone.py
    ./scripts/build-hull.sh --check leech_drone       # + controle de determinisme

Produit `assets/imported/models/ships/leech_drone.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne. Il
est deterministe (aucun alea) et s'auto-valide — `ak.export_hull()` relit le `.glb`
produit et echoue si la bounding box, le budget, les materiaux, le centrage ou les
points d'attache sortent du contrat. Trois harnais de mesure supplementaires
tournent a chaque build et sont documentes plus bas.

Reference de design : `assets/reference/concepts/null_choir_enemy_families_sheet.png`,
**quatrieme cellule en partant du haut** : petit corps globulaire a panneautage
radial, gros oeil magenta dorsal, trois bras courts termines par des pinces a
doigts recourbes, verins ivoire visibles dans les bras.


CE QUI DECIDE DE CETTE COQUE : ELLE DOIT LIRE COMME UNE CHOSE QUI VIENT
======================================================================
C'est le premier ennemi du jeu qui poursuit le joueur. Contre les deux mines
(BRIEF-0042/0043), qui sont des objets qui attendent, celle-ci doit avoir un
avant, un arriere et un moteur ; contre le Needle Scout, elle doit etre trapue et
finir en pinces ouvertes. Quatre partis pris servent exclusivement cette lecture :

1. **Une bouche a l'avant, une tuyere a l'arriere.** Le museau ivoire (`Muzzle_C`)
   et la nacelle magenta (`Engine_C`) sont sur l'axe, aux deux bouts : c'est le
   couple qui donne un sens de marche a un corps par ailleurs presque spherique.
2. **Deux pinces devant, une derriere** — et non le triskele parfait de la
   planche. Motif mesure, pas esthetique : la coque est 21 % plus longue que large
   (0,70 x 0,85), et le brief exige que **les pinces soient la partie la plus
   exterieure dans les quatre directions**. Un triskele a 120 deg place ses deux
   pinces arriere a y = +0,5 R : il faudrait alors 0,85 m de large pour tenir les
   0,85 m de long, ou laisser la queue deborder les pinces — le defaut meme que
   BRIEF-0042 a paye. La triade est donc tournee de 180 deg : les deux grosses
   pinces menent (ce que le brief demande : « on doit voir ce qu'elle veut faire
   avant qu'elle le fasse ») et la troisieme devient l'ancre posterieure — la
   sangsue reelle en a une. Les quatre extremes de la bbox sont des bouts de doigt.
3. **La plus petite coque du bestiaire** : 0,70 x 0,85 m contre 1,15 (Choir Mine),
   1,45 (Null Maw), 1,90 (Needle Scout). Sa fragilite se lit a la taille.
4. **Silhouette en trepied, pas en disque.** Vue de dessus, deux grands vides
   separent les bras : a 46 px c'est ce qui la distingue instantanement des deux
   mines, qui sont pleines et rondes.

Ou va le detail : la camera de jeu regarde a 20 deg de la VERTICALE. Le detail est
sur le dessus (calotte panneautee, gradins du noyau, dos des bras, veines) ; les
dessous sont en `AA_Greeble` sans detail (BRIEF-0026, rappele par ADR-0011).


LES PINCES PORTENT LA SILHOUETTE — LA LECON DE BRIEF-0042
=========================================================
Sur la Choir Mine, les six plaques pivotaient parfaitement et l'ouverture etait
invisible : l'enveloppe appartenait a la couronne de modules (r = 0,578) et non aux
plaques (0,496 fermees, 0,477 a 45 deg — le pivot les faisait RENTRER).

La cause est purement geometrique, et elle est generale. `EnemyPose` tourne la piece
autour de la tangente horizontale a son rayon ; un angle positif emmene le rayon
vers le HAUT (`axe x radial = +Y`, verifie analytiquement). Une piece qui pointe
deja vers l'exterieur voit donc son rayon multiplie par cos(angle) : elle rentre.
**Pour qu'une rotation FASSE GROSSIR l'enveloppe, la piece doit pointer vers le
BAS au repos** et se relever vers l'horizontale en s'ouvrant.

C'est le principe de cette coque : au repos, les trois pinces pendent sous le
plan de jeu, doigts recourbes — posture de predateur pret a mordre ; a l'ouverture
elles se deplient a l'horizontale et le diametre apparent grandit de 22,9 %
(16,2 % dans l'orientation ou elle fait face au joueur — c'est ce chiffre-la qui
decide, et le plancher du brief est de 12 %).
Le gain vaut exactement `sqrt(e^2 + h^2) - e`, ou `e` est le debord radial du bout
de doigt au-dela de la charniere et `h` sa plongee sous elle ; l'angle optimal vaut
`atan(h / e)` et **au-dela, l'enveloppe redescend**. Les deux nombres sont donc
choisis ici, pas subis (`_growth_table()` les remesure a chaque build).

Repere d'auteur (ADR-0008) : nez -Y, dessus +Z, **babord +X** (cf. aegis_kit).
"""

from __future__ import annotations

import json
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

# ==========================================================================
# Contrat
# ==========================================================================

CONTRACT = ak.HullContract(
    name="Leech Drone",
    width_x=0.70,        # Godot X — impose par le brief
    length_z=0.85,       # Godot Z — impose par le brief
    max_height_y=0.34,   # Godot Y — plafond du brief
    tri_budget=4_000,    # le plus serre du bestiaire : elle arrive en essaim
    required_materials=ak.MATERIAL_ORDER,
    required_attach_points=("Muzzle_C", "Engine_C"),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/ships/leech_drone.glb")

TEXELS_PER_METER = 6.0   # coque deux fois plus petite que la mine : feuille plus dense

# ==========================================================================
# Geometrie d'ensemble — les quatre extremes de la bbox sont des bouts de doigt
# ==========================================================================

#: Demi-largeur hors-tout visee (bout de doigt des pinces avant).
TIP_X = 0.3334
#: Y du bout de doigt des pinces avant (Godot : min Z = le nez).
TIP_Y_FRONT = -0.4179
#: Y du bout de doigt de la pince arriere.
TIP_Y_AFT = 0.4250

#: Angle d'ouverture OPTIMAL, commun aux trois pinces : c'est lui qui fixe la
#: plongee `h` de chaque bout de doigt (h = e * tan(OPEN_DEG)). Au-dela,
#: l'enveloppe se remet a retrecir — `_growth_table()` le montre a chaque build.
OPEN_DEG = 51.0

#: Rayon (dans le plan) de la charniere de chaque pince, et sa hauteur.
HINGE_R_FRONT = 0.3500
HINGE_Z_FRONT = 0.0620
HINGE_R_AFT = 0.3000
HINGE_Z_AFT = -0.0050

# ==========================================================================
# Corps : galet globulaire de revolution autour de Z
# ==========================================================================

#: (z, rayon, materiau de la bande sortante). Lu de bas en haut : culot mecanique,
#: ventre blinde, ceinture d'equateur (maitre-couple), calotte panneautee violette,
#: collier du puits de noyau.
BODY: list[tuple[float, float, str]] = [
    (-0.1150, 0.000, "AA_Greeble"),
    (-0.1030, 0.072, "AA_Greeble"),
    (-0.0720, 0.136, "AA_Hull"),
    (-0.0300, 0.184, "AA_Hull"),
    (0.0100, 0.208, "AA_Hull"),          # equateur — maitre-couple
    (0.0460, 0.204, "AA_Hull"),
    (0.0760, 0.187, "AA_Panel"),         # calotte : la surface que la camera voit
    (0.1010, 0.156, "AA_Panel"),
    (0.1180, 0.126, "AA_Greeble"),       # collier du puits
    (0.1220, 0.104, "AA_Greeble"),
    (0.1240, 0.000, "AA_Greeble"),       # plancher du puits (noye sous le noyau)
]
BODY_SEGMENTS = 18   # multiple de 3 et de 6 : bras, veines et panneaux tombent juste

# ==========================================================================
# Noyau dorsal : tambour a gradins, coiffe de la lentille magenta
# ==========================================================================

CORE: list[tuple[float, float, str]] = [
    (0.1120, 0.102, "AA_Greeble"),
    (0.1260, 0.102, "AA_Panel"),              # gradin violet
    (0.1260, 0.088, "AA_Greeble"),
    (0.1350, 0.088, "AA_Trim"),               # filet ivoire
    (0.1350, 0.074, "AA_Greeble"),
    (0.1400, 0.074, "AA_Glass"),              # membrane sombre : le cerne de l'oeil
    (0.1400, 0.060, "AA_Glass"),
    (0.1450, 0.060, "AA_Emissive_Engine"),    # lentille magenta (120 mm)
    (0.1520, 0.000, "AA_Emissive_Engine"),    # pole : point haut de la coque
]
CORE_SEGMENTS = 12

# ==========================================================================
# Museau (avant) et nacelle moteur (arriere) : le couple qui donne un sens
# ==========================================================================

#: (y, demi-largeur, demi-hauteur, z du centre). Ventouse ivoire de la sangsue.
SNOUT: tuple[tuple[float, float, float, float], ...] = (
    (-0.1400, 0.072, 0.056, 0.0050),   # emplanture, noyee dans le corps
    (-0.2200, 0.060, 0.047, 0.0100),
    (-0.2760, 0.042, 0.033, 0.0140),
    (-0.3080, 0.024, 0.019, 0.0165),   # levre
)
MUZZLE_Y = -0.3140
MUZZLE_Z = 0.0170

#: (y, demi-largeur, demi-hauteur, z du centre). Nacelle DORSALE : la plume passe
#: au-dessus de la pince arriere, jamais au travers.
NACELLE: tuple[tuple[float, float, float, float], ...] = (
    (0.1250, 0.070, 0.052, 0.0560),
    (0.1950, 0.078, 0.058, 0.0640),
    (0.2450, 0.070, 0.052, 0.0680),
    (0.2660, 0.052, 0.038, 0.0700),   # levre de tuyere
)
ENGINE_Y = 0.2760
ENGINE_Z = 0.0700

# ==========================================================================
# Bras fixes (epaule + verin ivoire + chape) — ils s'arretent A la charniere
# ==========================================================================

#: (rayon, demi-largeur, demi-hauteur, z, materiau). Le verin ivoire du milieu est
#: la signature de la planche ; c'est aussi lui qui fera lire un coulissement
#: radial comme un verin qui sort, si le jeu en demande un.
ARM: tuple[tuple[float, float, float, float, str], ...] = (
    (0.1500, 0.062, 0.050, 0.000, "AA_Greeble"),   # emplanture, noyee dans le corps
    (0.2100, 0.056, 0.044, 0.000, "AA_Trim"),      # verin ivoire
    (0.2750, 0.042, 0.034, 0.000, "AA_Greeble"),
    (0.3150, 0.044, 0.038, 0.000, "AA_Greeble"),   # chape (joues de charniere)
)
#: Rayon de la douille de chape, autour de l'axe de charniere. Surface de
#: revolution autour de CET axe : une rotation ne peut pas la faire mordre.
SOCKET_R = 0.040
SOCKET_HALF = 0.042

# ==========================================================================
# Pinces articulees
# ==========================================================================

#: Chemin normalise d'un doigt, dans le plan (radial, vertical) de la pince, du
#: pivot (0,0) au bout (1,-1). Il sort vite puis plonge : c'est ce qui donne un
#: doigt CROCHU au repos et un doigt TENDU une fois ouvert.
FINGER_PATH: tuple[tuple[float, float], ...] = (
    (0.000, 0.000),
    (0.270, -0.170),
    (0.510, -0.390),
    (0.720, -0.620),
    (0.885, -0.820),
    (1.000, -1.000),
)

#: (demi-largeur, demi-hauteur) le long du chemin — poignet puis paume.
#: La paume s'arrete TOT (station 1 sur 5) : au premier rendu elle mangeait la
#: moitie de la pince et les trois doigts, reduits a des moignons, ne se lisaient
#: plus du tout en vue de jeu. Ce sont les doigts qui disent ce que fait l'engin.
PALM_W: tuple[tuple[float, float], ...] = (
    (0.052, 0.046),
    (0.050, 0.041),
)
#: Doigt : (demi-largeur, demi-hauteur) aux stations 1..5 du chemin.
FINGER_W: tuple[tuple[float, float], ...] = (
    (0.019, 0.030),
    (0.017, 0.025),
    (0.014, 0.019),
    (0.010, 0.013),
    (0.004, 0.005),
)
#: Ecart tangentiel des trois doigts a la base puis au bout : ils CONVERGENT.
#: L'ecart doit depasser la demi-largeur x2, sinon les doigts se touchent et la
#: pince redevient un bloc — c'est le VIDE entre eux qui la fait lire comme une main.
#: Il doit AUSSI depasser la demi-largeur de la paume (0,050) : sinon, vue du
#: dessus — c'est-a-dire en jeu — la paume couvre exactement ses propres doigts et
#: la pince redevient un moignon. Les doigts lateraux debordent donc de 2 mm.
FINGER_SPREAD = ((-0.052, -0.034), (0.0, 0.0), (0.052, 0.034))
#: Le doigt du milieu va au bout du chemin ; les deux lateraux s'arretent avant.
FINGER_REACH = (0.895, 1.000, 0.895)

# ==========================================================================
# Detail de dessus : veines magenta et deux nodules verts
# ==========================================================================

#: (rayon, demi-largeur, demi-hauteur) — veine posee sur la pente de la calotte.
VEIN: tuple[tuple[float, float, float], ...] = (
    (0.0960, 0.009, 0.004),
    (0.1450, 0.007, 0.004),
    (0.1950, 0.005, 0.003),
)
VEIN_LIFT = 0.004

#: Nodules `AA_Marking_Red` (vert maladif pour le Choeur Nul) : usage tres limite.
#: Deux seulement, de tailles differentes, a des azimuts non opposes — la charte
#: veut du Choeur Nul asymetrique.
NODULE = ((18.0, 1.00), (163.0, 0.78))
NODULE_BOX: tuple[tuple[float, float, float], ...] = (
    (0.1650, 0.040, 0.030),
    (0.2010, 0.044, 0.033),
    (0.2280, 0.032, 0.024),
)
NODULE_Z = 0.0250

# ==========================================================================
# Harnais : debattement, croissance d'enveloppe, aire vue
# ==========================================================================

TRAVEL_FLOOR_DEG = OPEN_DEG    # on refuse d'exporter sous l'angle optimal d'ouverture
TRAVEL_STEP_DEG = 1.0
TRAVEL_MAX_DEG = 180.0
#: Rayon d'exclusion autour du pivot. Toute la ferrure (douille de chape + poignet)
#: tient dedans, et une rotation autour du pivot CONSERVE la distance au pivot :
#: ce qui est exclu ne peut, par construction, rencontrer rien d'autre. La valeur
#: est verifiee par `_assert_hinge_skip()`, pas choisie a vue.
HINGE_SKIP = 0.060

#: Croissance minimale du diametre apparent exigee par le brief (BRIEF-0044).
GROWTH_FLOOR_PCT = 12.0

#: Camera de jeu, lue sur `scenes/gameplay/graybox.tscn` (Camera3D de CameraDirector).
#: Transform3D est serialise en LIGNES de la base : les colonnes (les axes) sont
#: donc les transposees. Axe de visee a 70 deg sous l'horizontale, a 14,87 unites
#: du plan de jeu. Mesurer l'enveloppe au cadrage serre de `render-hull.py`
#: (2,4 m d'un objet de 1 m) surestimerait la croissance d'un facteur ~7.
CAM_POS = Vector((0.0, 14.0, 5.0))
CAM_X = Vector((1.0, 0.0, 0.0))
CAM_Y = Vector((0.0, 0.342, -0.940))
CAM_Z = Vector((0.0, 0.940, 0.342))
CAM_FOV_DEG = 62.0
SCREEN_H = 1080.0


# ==========================================================================
# Helpers geometriques — uniquement des primitives du kit, kit NON modifie
# ==========================================================================


def _frame(theta_deg: float) -> tuple[Vector, Vector, Vector]:
    """(radial, tangentiel, vertical) au poste angulaire `theta_deg`."""
    a = math.radians(theta_deg)
    return (
        Vector((math.cos(a), math.sin(a), 0.0)),
        Vector((-math.sin(a), math.cos(a), 0.0)),
        Vector((0.0, 0.0, 1.0)),
    )


def _sweep(
    bm: bmesh.types.BMesh,
    sections: list[tuple[Vector, Vector, Vector]],
    profile: tuple[tuple[float, float], ...],
    band_materials: tuple[str, ...],
    cap_first: str | None = None,
    cap_last: str | None = None,
) -> list[list[bmesh.types.BMFace]]:
    """Balaye un profil ferme le long de stations orientees.

    `sections` : (centre, demi-vecteur transversal, demi-vecteur vertical). Bras,
    museau, nacelle, paume, doigts, veines et nodules sortent tous d'ici : une
    seule primitive locale, batie sur `add_ring`/`bridge_rings`/`cap_ring` du kit.
    """
    rings = [
        ak.add_ring(bm, [tuple(c + u * pu + v * pv) for pu, pv in profile])
        for c, u, v in sections
    ]
    bands = [
        ak.bridge_rings(bm, rings[i], rings[i + 1], band_materials[i])
        for i in range(len(rings) - 1)
    ]
    if cap_first is not None:
        ak.cap_ring(bm, list(reversed(rings[0])), cap_first)
    if cap_last is not None:
        ak.cap_ring(bm, rings[-1], cap_last)
    return bands


def _circle(sides: int) -> tuple[tuple[float, float], ...]:
    """Profil circulaire unitaire, premiere arete en haut (dos de la piece)."""
    return tuple(
        (
            math.cos(2.0 * math.pi * (i + 0.5) / sides),
            math.sin(2.0 * math.pi * (i + 0.5) / sides),
        )
        for i in range(sides)
    )


_SQUARE = ((1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0), (1.0, -1.0))
_HEX = (
    (0.55, 1.0), (-0.55, 1.0), (-1.0, 0.0),
    (-0.55, -1.0), (0.55, -1.0), (1.0, 0.0),
)


def _inset(
    bm: bmesh.types.BMesh, faces: list, material: str, thickness: float, depth: float
) -> list:
    """`ak.inset_panel` PRECEDE d'une mise a jour des normales — et c'est vital.

    ⚠️ PIEGE MESURE (et parfaitement silencieux). `bmesh.ops.inset_region` calcule
    son offset a partir de la normale de face. Sur un BMesh fraichement bati par
    `bm.faces.new()` (donc par `bridge_rings`, `add_lathe`, `_sweep`...), cette
    normale vaut **(0, 0, 0)** tant que personne ne l'a demandee : l'inset produit
    alors quatre faces de bordure d'aire NULLE, que `ak.cleanup()` supprime au
    passage suivant. Resultat : le panneau n'est ni enfonce ni cerne — il ne reste
    que le changement de materiau, et rien dans le rapport de contrat ne le dit.

    Mesure : 0,000000 m2 d'aire de bordure sans `normal_update()`, 0,000714 avec.
    Le kit n'est pas modifie (consigne du brief) ; on corrige a l'appel.
    """
    bm.normal_update()
    return ak.inset_panel(bm, faces, material, thickness=thickness, depth=depth)


def _lerp_table(pairs: list[tuple[float, float]], x: float) -> float:
    if x <= pairs[0][0]:
        return pairs[0][1]
    if x >= pairs[-1][0]:
        return pairs[-1][1]
    for i in range(len(pairs) - 1):
        x0, v0 = pairs[i]
        x1, v1 = pairs[i + 1]
        if x0 <= x <= x1:
            return v0 + (v1 - v0) * (x - x0) / (x1 - x0)
    return pairs[-1][1]


#: Dessus du corps, du puits vers l'equateur — la source de verite de la calotte.
_DECK = [(r, z) for z, r, _ in BODY if z >= 0.0][::-1]


def _deck_z(radius: float) -> float:
    """Hauteur de la calotte au rayon donne (lue dans `BODY`, jamais en dur)."""
    return _lerp_table(_DECK, radius)


def _axial_sections(
    table, axis: Vector, cross: Vector, up: Vector
) -> list[tuple[Vector, Vector, Vector]]:
    """Stations d'une piece axiale : lignes `(along, demi-largeur, demi-hauteur, z)`."""
    return [
        (axis * along + up * z, cross * half_w, up * half_h)
        for along, half_w, half_h, z in table
    ]


# ==========================================================================
# Pinces : la geometrie qui PORTE la silhouette
# ==========================================================================


def _claw_geometry(hinge_r: float, tip_r: float) -> tuple[float, float, float]:
    """(debord radial `e`, plongee `h`, gain de rayon a l'ouverture optimale).

    C'est toute la mecanique de la coque en trois lignes : le bout de doigt est a
    `e` au-dela de la charniere et `h` en dessous ; une rotation de `atan(h/e)`
    autour de la tangente le ramene a l'horizontale, ou son rayon vaut `sqrt(e^2+h^2)`.
    """
    e = tip_r - hinge_r
    h = e * math.tan(math.radians(OPEN_DEG))
    return e, h, math.hypot(e, h) - e


def _claw_sections(
    theta_deg: float, hinge_r: float, hinge_z: float, tip_r: float,
    first: int, last: int, widths, spread: tuple[float, float], reach: float,
) -> list[tuple[Vector, Vector, Vector]]:
    """Stations d'un doigt (ou de la paume) le long de `FINGER_PATH`.

    Le chemin est normalise ; on le met a l'echelle par (`e`, `h`), donc le bout du
    doigt du milieu tombe EXACTEMENT sur le rayon vise. `spread` interpole l'ecart
    tangentiel de la base au bout : les trois doigts convergent.
    """
    radial, tangent, up = _frame(theta_deg)
    e, h, _ = _claw_geometry(hinge_r, tip_r)
    base = radial * hinge_r + up * hinge_z
    out = []
    span = max(1, last - first)
    for k in range(first, last + 1):
        pu, pv = FINGER_PATH[k]
        pu, pv = pu * reach, pv * reach
        t = (k - first) / span
        side = spread[0] + (spread[1] - spread[0]) * t
        half_w, half_h = widths[k - first]
        centre = base + radial * (e * pu) + up * (h * pv) + tangent * side
        out.append((centre, tangent * half_w, up * half_h))
    return out


def build_claw(
    index: int, theta_deg: float, hinge_r: float, hinge_z: float, tip_r: float
) -> ak.MovingPart:
    """Une pince, batie en coordonnees ABSOLUES, origine sur sa charniere.

    Poignet (douille de revolution autour de l'axe de charniere) + paume + trois
    doigts. La douille est une surface de revolution autour de l'axe de rotation :
    par construction elle ne peut pas mordre la chape, quel que soit l'angle.
    """
    bm = bmesh.new()
    radial, tangent, up = _frame(theta_deg)
    hinge = radial * hinge_r + up * hinge_z

    # --- poignet : douille cylindrique centree sur l'axe de charniere ---------
    knuckle = [
        (hinge + tangent * s, radial * SOCKET_R, up * SOCKET_R)
        for s in (-SOCKET_HALF, 0.0, SOCKET_HALF)
    ]
    _sweep(
        bm, knuckle, _circle(6), ("AA_Greeble", "AA_Greeble"),
        cap_first="AA_Greeble", cap_last="AA_Greeble",
    )

    # --- paume : stations 0..2 du chemin -------------------------------------
    palm = _claw_sections(
        theta_deg, hinge_r, hinge_z, tip_r, 0, 1, PALM_W, (0.0, 0.0), 1.0
    )
    bands = _sweep(bm, palm, _HEX, ("AA_Hull",), cap_last=None)
    # Facette 0 du profil hexagonal = le dessus : c'est la seule surface de la
    # pince que la camera de jeu voit vraiment. Elle porte le panneau violet.
    # Le dos de la paume porte un panneau violet CERNE de magenta : trois taches
    # chaudes aux trois extremites de la coque. Elles ne coutent pas un triangle
    # (ce sont les faces de bordure que `inset_panel` cree de toute facon) et ce
    # sont elles qui, vues du dessus, disent « ici il y a une main » quand les
    # doigts sont raccourcis par la perspective.
    # ⚠️ 14 mm et pas 8 : un listel plus fin que DEUX fois la largeur de chanfrein
    # (2 x 3,5 mm) est INTEGRALEMENT mange par `bevel_sharp_edges` — mesure, les
    # quatre faces magenta disparaissaient du .glb sans un mot. Le defaut ne se
    # voit pas sur le nombre de triangles, seulement sur le compte par materiau.
    border = _inset(bm, [band[0] for band in bands], "AA_Panel", 0.014, -0.005)
    ak.set_material(border, "AA_Emissive_Engine")
    ak.set_material([bands[0][3]], "AA_Greeble")  # dessous

    # --- trois doigts : stations 2..5 ----------------------------------------
    for finger in range(3):
        sections = _claw_sections(
            theta_deg, hinge_r, hinge_z, tip_r, 1, 5,
            FINGER_W, FINGER_SPREAD[finger], FINGER_REACH[finger],
        )
        _sweep(
            bm, sections, _SQUARE,
            ("AA_Hull", "AA_Panel", "AA_Greeble", "AA_Trim"),  # griffe ivoire au bout
            cap_first="AA_Greeble", cap_last="AA_Trim",
        )

    return ak.moving_part(f"Claw_{index:02d}", bm, tuple(hinge))


# ==========================================================================
# Coque fixe
# ==========================================================================


def _arm(bm: bmesh.types.BMesh, theta_deg: float, hinge_r: float, hinge_z: float) -> None:
    """Bras FIXE : epaule, verin ivoire, chape. Il s'arrete a la charniere."""
    radial, tangent, up = _frame(theta_deg)
    scale = hinge_r / HINGE_R_FRONT
    sections = []
    materials = []
    for r, half_w, half_h, dz, mat in ARM:
        r = 0.150 + (r - 0.150) * scale if scale != 1.0 else r
        sections.append((radial * r + up * (hinge_z + dz), tangent * half_w, up * half_h))
        materials.append(mat)
    bands = _sweep(
        bm, sections, _HEX, tuple(materials[:-1]),
        cap_first="AA_Greeble", cap_last="AA_Greeble",
    )
    # Dos du bras (facette 0) : liseré enfoncé, vu de dessus.
    _inset(bm, [bands[2][0]], "AA_Panel", 0.008, -0.005)


def _vein(bm: bmesh.types.BMesh, theta_deg: float) -> None:
    """Veine magenta courant du noyau vers un bras, posee sur la calotte."""
    radial, tangent, up = _frame(theta_deg)
    sections = [
        (radial * r + up * (_deck_z(r) + VEIN_LIFT), tangent * hw, up * hh)
        for r, hw, hh in VEIN
    ]
    _sweep(
        bm, sections, _SQUARE, ("AA_Emissive_Engine",) * (len(VEIN) - 1),
        cap_first="AA_Emissive_Engine", cap_last="AA_Emissive_Engine",
    )


def _nodule(bm: bmesh.types.BMesh, theta_deg: float, scale: float) -> None:
    radial, tangent, up = _frame(theta_deg)
    sections = [
        (radial * r + up * NODULE_Z, tangent * (hw * scale), up * (hh * scale))
        for r, hw, hh in NODULE_BOX
    ]
    _sweep(
        bm, sections, _HEX, ("AA_Marking_Red",) * (len(NODULE_BOX) - 1),
        cap_first="AA_Greeble", cap_last="AA_Greeble",
    )


def build_hull(claw_posts: list[tuple[float, float, float, float]]) -> object:
    bm = bmesh.new()

    body_bands = ak.add_lathe(bm, BODY, BODY_SEGMENTS, axis="Z")
    ak.add_lathe(bm, CORE, CORE_SEGMENTS, axis="Z")

    # Panneautage RADIAL de la calotte — la signature de la planche. Chaque face
    # de la bande est enfoncee SEPAREMENT : c'est le liston anthracite laisse
    # entre deux enfoncements qui dessine les rayons. Un `inset_region` sur toute
    # la bande d'un coup ne ferait qu'un seul grand panneau annulaire, sans un
    # seul rayon — le detail doit etre de la geometrie, pas une intention.
    for band_index, fill in ((6, "AA_Panel"), (5, "AA_Hull")):
        for k, face in enumerate(body_bands[band_index]):
            if face is None or not face.is_valid:
                continue
            # Bande basse : une face sur trois seulement. Sur deux, la ceinture
            # lisait comme un second anneau concentrique et doublait le noyau ;
            # sur trois, elle donne six bossages irreguliers a l'equateur — et
            # elle rentre dans le budget, qui est ici le plus serre du bestiaire.
            if band_index == 5 and k % 3:
                continue
            _inset(bm, [face], fill, 0.007, -0.005)

    # Museau ivoire (avant) : la ventouse de la sangsue.
    _sweep(
        bm,
        _axial_sections(SNOUT, Vector((0.0, 1.0, 0.0)), Vector((1.0, 0.0, 0.0)),
                        Vector((0.0, 0.0, 1.0))),
        _HEX, ("AA_Greeble", "AA_Trim", "AA_Greeble"),
        cap_first="AA_Greeble", cap_last="AA_Glass",   # bouche sombre
    )

    # Nacelle dorsale (arriere) + tuyere magenta enfoncee.
    nac = _axial_sections(NACELLE, Vector((0.0, 1.0, 0.0)), Vector((1.0, 0.0, 0.0)),
                          Vector((0.0, 0.0, 1.0)))
    bands = _sweep(
        bm, nac, _HEX, ("AA_Greeble", "AA_Hull", "AA_Greeble"),
        cap_first="AA_Greeble", cap_last="AA_Emissive_Engine",
    )
    _inset(bm, [bands[1][0]], "AA_Panel", 0.010, -0.006)

    for theta, hinge_r, hinge_z, _tip in claw_posts:
        _arm(bm, theta, hinge_r, hinge_z)
        _vein(bm, theta)

    for theta, scale in NODULE:
        _nodule(bm, theta, scale)

    return ak.new_object("LeechDrone_Hull", bm)


def build_attach_points() -> list:
    return [
        ak.attach_point("Muzzle_C", (0.0, MUZZLE_Y, MUZZLE_Z)),
        ak.attach_point("Engine_C", (0.0, ENGINE_Y, ENGINE_Z)),
    ]


# ==========================================================================
# Harnais 1 — debattement mecanique, convention EXACTE de EnemyPose
# ==========================================================================

#: (x, y, z)_auteur -> (-x, z, y)_Godot : la chaine appliquee par `export_hull`.
_TO_GODOT = Matrix(((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)))


def _hinge_axis(position: Vector) -> Vector:
    """Copie EXACTE de `EnemyPose._hinge_axis` (scripts/enemies/enemy_pose.gd)."""
    radial = Vector((position.x, position.z))
    if radial.length_squared < 1e-6:
        return Vector((1.0, 0.0, 0.0))
    radial.normalize()
    return Vector((-radial.y, 0.0, radial.x))


def _radial_axis(position: Vector) -> Vector:
    """Copie EXACTE de `EnemyPose._radial_axis`."""
    radial = Vector((position.x, position.z))
    if radial.length_squared < 1e-6:
        return Vector((0.0, 0.0, 0.0))
    radial.normalize()
    return Vector((radial.x, 0.0, radial.y))


def _clip_sphere(verts: list, tri: list, pivot: Vector, skip: float,
                 out: list, depth: int = 0) -> None:
    """Garde de `tri` ce qui est HORS de la sphere (`pivot`, `skip`), en coupant."""
    d = [(verts[i] - pivot).length for i in tri]
    if min(d) >= skip:
        out.append(list(tri))
        return
    if max(d) <= skip or depth >= 4:
        return
    k = max(range(3), key=lambda i: (verts[tri[i]] - verts[tri[(i + 1) % 3]]).length)
    a, b, c = tri[k], tri[(k + 1) % 3], tri[(k + 2) % 3]
    mid = len(verts)
    verts.append((verts[a] + verts[b]) * 0.5)
    _clip_sphere(verts, [a, mid, c], pivot, skip, out, depth + 1)
    _clip_sphere(verts, [mid, b, c], pivot, skip, out, depth + 1)


def _soup(obj, pivot: Vector | None = None, skip: float = 0.0):
    """(sommets, triangles) d'un objet, en repere GODOT, compactes."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.index_update()
    raw = [_TO_GODOT @ v.co for v in bm.verts]
    tris: list = []
    for face in bm.faces:
        idx = [loop.vert.index for loop in face.loops]
        if skip > 0.0 and pivot is not None:
            _clip_sphere(raw, idx, pivot, skip, tris)
        else:
            tris.append(idx)
    bm.free()
    keep, remap, out = [], {}, []
    for tri in tris:
        row = []
        for i in tri:
            if i not in remap:
                remap[i] = len(keep)
                keep.append(raw[i])
            row.append(remap[i])
        out.append(row)
    return keep, out


def _soup_with_materials(obj):
    """(sommets, triangles, index de materiau) en repere GODOT — pour l'aire vue."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.index_update()
    verts = [_TO_GODOT @ v.co for v in bm.verts]
    tris, mats = [], []
    for face in bm.faces:
        tris.append([loop.vert.index for loop in face.loops])
        mats.append(face.material_index)
    bm.free()
    return verts, tris, mats


class Solid:
    """Soupe de triangles figee, prete a repondre « a quelle distance ? »."""

    def __init__(self, verts: list, tris: list):
        self.verts = verts
        self.tris = tris
        self.tree = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)

    def distance_to(self, verts: list, tris: list) -> float:
        other = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)
        if other.overlap(self.tree):
            return 0.0
        best = 3.0
        for v in verts:
            hit = self.tree.find_nearest(v, best)
            if hit[3] is not None:
                best = min(best, hit[3])
        for v in self.verts:
            hit = other.find_nearest(v, best)
            if hit[3] is not None:
                best = min(best, hit[3])
        return best


def _assert_hinge_skip(hull, parts: list) -> None:
    """La sphere d'exclusion doit couvrir TOUTE la ferrure, des deux cotes.

    Sans ce controle, `HINGE_SKIP` serait un reglage a vue : trop petit, il fait
    echouer une articulation parfaitement saine (la douille frotte la chape par
    construction) ; trop grand, il masque une vraie collision. On mesure donc ce
    qu'il ampute reellement.
    """
    print("--- controle du rayon d'exclusion de charniere ---")
    hull_verts, _ = _soup(hull)
    for part in parts:
        pivot = _TO_GODOT @ Vector(part.pivot)
        verts, _ = _soup(part.obj)
        inside_part = max(
            ((v - pivot).length for v in verts if (v - pivot).length < HINGE_SKIP),
            default=0.0,
        )
        inside_hull = max(
            ((v - pivot).length for v in hull_verts if (v - pivot).length < HINGE_SKIP),
            default=0.0,
        )
        # Ce qui compte : aucune geometrie ne doit se trouver JUSTE au-dela du
        # rayon d'exclusion cote piece mobile (sinon on ampute une vraie surface
        # portante et la mesure ment).
        print(
            f"  {part.obj.name}  ampute {inside_part * 1000:5.1f} mm de piece / "
            f"{inside_hull * 1000:5.1f} mm de coque autour du pivot "
            f"(rayon {HINGE_SKIP * 1000:.0f} mm)"
        )


def _travel_table(hull, parts: list) -> list[tuple]:
    """Debattement mecanique de chaque pince, mesure sur le maillage livre."""
    names = [p.obj.name for p in parts]
    pivot = {p.obj.name: _TO_GODOT @ Vector(p.pivot) for p in parts}
    axis = {n: _hinge_axis(pivot[n]) for n in names}

    local, tris, hull_solid = {}, {}, {}
    for part in parts:
        name = part.obj.name
        verts, faces = _soup(part.obj, pivot[name], HINGE_SKIP)
        local[name] = [v - pivot[name] for v in verts]
        tris[name] = faces
        hull_solid[name] = Solid(*_soup(hull, pivot[name], HINGE_SKIP))

    steps = int(TRAVEL_MAX_DEG / TRAVEL_STEP_DEG)
    limit = {n: TRAVEL_MAX_DEG for n in names}
    blocker = {n: "aucun contact jusqu'a %.0f deg" % TRAVEL_MAX_DEG for n in names}
    margin_at = {n: {} for n in names}

    for s in range(steps + 1):
        deg = s * TRAVEL_STEP_DEG
        angle = math.radians(deg)
        posed = {
            n: [Matrix.Translation(pivot[n]) @ Matrix.Rotation(angle, 4, axis[n]) @ v
                for v in local[n]]
            for n in names
        }
        solids = {n: Solid(posed[n], tris[n]) for n in names}
        for i, name in enumerate(names):
            worst, who = 9.9, ""
            d = hull_solid[name].distance_to(posed[name], tris[name])
            if d < worst:
                worst, who = d, "coque fixe (bras/corps)"
            for j, other in enumerate(names):
                if j == i:
                    continue
                d = solids[other].distance_to(posed[name], tris[name])
                if d < worst:
                    worst, who = d, f"voisine {other}"
            margin_at[name][deg] = (worst, who)
            if worst <= 0.0 and limit[name] > deg:
                limit[name] = deg - TRAVEL_STEP_DEG
                blocker[name] = who

    return [
        (p.obj.name, pivot[p.obj.name], axis[p.obj.name],
         limit[p.obj.name], blocker[p.obj.name], margin_at[p.obj.name])
        for p in parts
    ]


def _report_travel(rows: list[tuple]) -> None:
    print("--- debattement mecanique mesure (convention EnemyPose, coulissement 0) ---")
    worst = 360.0
    for name, pivot, axis, limit, blocker, margins in rows:
        m0 = margins.get(0.0, (0.0, ""))[0] * 1000.0
        mo = margins.get(float(int(OPEN_DEG)), (0.0, ""))[0] * 1000.0
        m85 = margins.get(85.0, (0.0, ""))[0] * 1000.0
        print(
            f"  {name}  pivot Godot ({pivot.x:+.4f}, {pivot.y:+.4f}, {pivot.z:+.4f})"
            f"  axe ({axis.x:+.4f}, {axis.y:+.4f}, {axis.z:+.4f})"
            f"  1re interpenetration {limit + TRAVEL_STEP_DEG:5.1f} deg  [{blocker}]"
            f"  marge : repos {m0:5.1f} | {OPEN_DEG:.0f} deg {mo:5.1f} | 85 deg {m85:5.1f} mm"
        )
        worst = min(worst, limit)
    print(f"  -> debattement retenu (la plus contrainte des trois) : {worst:.1f} deg")
    if worst < TRAVEL_FLOOR_DEG:
        raise ak.ContractError(
            f"debattement insuffisant : {worst:.1f} deg < plancher "
            f"{TRAVEL_FLOOR_DEG:.1f} deg — les pinces mordraient avant d'etre ouvertes."
        )


# ==========================================================================
# Harnais 2 — croissance du diametre apparent, a la perspective REELLE du jeu
# ==========================================================================


def _project(point: Vector) -> tuple[float, float] | None:
    """Projette un point monde Godot sur l'ecran du jeu, en pixels."""
    d = point - CAM_POS
    vx, vy, vz = d.dot(CAM_X), d.dot(CAM_Y), d.dot(CAM_Z)
    if vz >= -1e-6:
        return None
    focal = (SCREEN_H * 0.5) / math.tan(math.radians(CAM_FOV_DEG) * 0.5)
    return (focal * vx / -vz, focal * vy / -vz)


def _hull2d(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Enveloppe convexe 2D (chaine monotone)."""
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2:
                (ox, oy), (ax, ay) = out[-2], out[-1]
                if (ax - ox) * (p[1] - oy) - (ay - oy) * (p[0] - ox) > 0:
                    break
                out.pop()
            out.append(p)
        return out

    return half(pts)[:-1] + half(pts[::-1])[:-1]


def _diameter(points: list[tuple[float, float]]) -> float:
    hull = _hull2d(points)
    best = 0.0
    for i in range(len(hull)):
        for j in range(i + 1, len(hull)):
            best = max(best, math.dist(hull[i], hull[j]))
    return best


def _posed_points(hull_verts, part_state, deg: float, spread: float, yaw_deg: float):
    """Sommets monde (Godot) de toute la coque a une ouverture donnee.

    Reproduit `EnemyPose.pose()` : `Basis(axe, angle)` puis
    `position = rest + radial * rayon_XZ * spread * open`. `yaw_deg` est
    l'orientation du nœud en jeu (0 = nez vers le haut de l'ecran).
    """
    yaw = Matrix.Rotation(math.radians(yaw_deg), 4, "Y")
    out = [(yaw @ v, False) for v in hull_verts]
    angle = math.radians(deg)
    for pivot, radial, radius, local in part_state:
        offset = pivot + radial * (radius * spread)
        rot = Matrix.Rotation(angle, 4, pivot_axis(pivot))
        for v in local:
            out.append((yaw @ (offset + rot @ v), True))
    return out


def pivot_axis(pivot: Vector) -> Vector:
    return _hinge_axis(pivot)


def _growth_table(hull, parts: list) -> list[tuple]:
    """Croissance du diametre apparent, a la geometrie perspective du jeu.

    Trois mesures par angle : diametre max (plus grande distance entre deux points
    de la silhouette projetee), largeur et hauteur ecran. Le repere est la coque
    FERMEE ; le cadrage ne bouge pas d'un etat a l'autre, sinon on ne comparerait
    rien (piege releve dans BRIEF-0042-debattement-radial SS4.2).
    """
    hull_verts, _ = _soup(hull)
    part_state = []
    for part in parts:
        pivot = _TO_GODOT @ Vector(part.pivot)
        verts, _ = _soup(part.obj)
        part_state.append((
            pivot,
            _radial_axis(pivot),
            Vector((pivot.x, pivot.z)).length,
            [v - pivot for v in verts],
        ))

    rows = []
    for deg in (0.0, 10.0, 20.0, 30.0, 40.0, OPEN_DEG, 60.0, 70.0):
        entry = [deg]
        for yaw in (0.0, 180.0):
            pts = _posed_points(hull_verts, part_state, deg, 0.0, yaw)
            screen = [p for p in (_project(v) for v, _ in pts) if p is not None]
            claw = [
                p for p, (_, is_claw) in zip(
                    (_project(v) for v, _ in pts), pts
                ) if p is not None and is_claw
            ]
            entry.append((_diameter(screen), _diameter(claw)))
        # rayon XZ maximal, coque fixe contre pinces : « qui porte l'enveloppe »
        pts = _posed_points(hull_verts, part_state, deg, 0.0, 0.0)
        r_hull = max(math.hypot(v.x, v.z) for v, is_claw in pts if not is_claw)
        r_claw = max(math.hypot(v.x, v.z) for v, is_claw in pts if is_claw)
        entry.append((r_hull, r_claw))
        rows.append(entry)
    return rows


def _spread_table(hull, parts: list) -> None:
    """Effet du COULISSEMENT radial optionnel, par-dessus l'ouverture optimale.

    `EnemyPose` peut, en plus du pivot, faire glisser chaque piece le long de son
    rayon (`open_spread`, plafonne a 0,5 du rayon XZ). Ici la rotation suffit deja
    largement ; on mesure quand meme ce que le coulissement ajoute, ET ce qu'il
    coute — il ouvre un jour VISIBLE entre la douille et la chape du bras.
    """
    hull_verts, _ = _soup(hull)
    state = []
    for part in parts:
        pivot = _TO_GODOT @ Vector(part.pivot)
        verts, _ = _soup(part.obj)
        state.append((pivot, _radial_axis(pivot),
                      Vector((pivot.x, pivot.z)).length, [v - pivot for v in verts]))
    base = _diameter([p for p in (_project(v) for v, _ in
                                  _posed_points(hull_verts, state, 0.0, 0.0, 0.0))
                      if p is not None])
    print("--- coulissement radial optionnel, par-dessus l'ouverture optimale ---")
    for spread in (0.0, 0.15, 0.30, 0.50):
        pts = _posed_points(hull_verts, state, OPEN_DEG, spread, 0.0)
        d = _diameter([p for p in (_project(v) for v, _ in pts) if p is not None])
        gap = max(s[2] for s in state) * spread * 1000.0
        print(
            f"  open_spread {spread:.2f} : diam. {d:6.2f} px "
            f"({100.0 * (d / base - 1.0):+6.2f} %)  jour a la charniere {gap:5.1f} mm"
        )


def _report_growth(rows: list[tuple]) -> None:
    print("--- croissance du diametre apparent (camera de graybox.tscn, 14,87 u) ---")
    base = rows[0][1][0]
    base180 = rows[0][2][0]
    for deg, yaw0, yaw180, radii in rows:
        r_hull, r_claw = radii
        print(
            f"  {deg:5.1f} deg  diam. ecran {yaw0[0]:7.2f} px "
            f"({100.0 * (yaw0[0] / base - 1.0):+6.2f} %)"
            f" | nez au joueur {yaw180[0]:7.2f} px "
            f"({100.0 * (yaw180[0] / base180 - 1.0):+6.2f} %)"
            f" | rayon XZ coque {r_hull:.4f} / pinces {r_claw:.4f} m"
        )
        if r_claw <= r_hull:
            raise ak.ContractError(
                f"a {deg:.0f} deg, la coque fixe (r={r_hull:.4f}) deborde les pinces "
                f"(r={r_claw:.4f}) — c'est le defaut de BRIEF-0042."
            )
    grown = 100.0 * (rows[5][1][0] / base - 1.0)
    print(f"  -> a {OPEN_DEG:.0f} deg : {grown:+.2f} % de diametre apparent")
    if grown < GROWTH_FLOOR_PCT:
        raise ak.ContractError(
            f"croissance du diametre apparent {grown:.2f} % < plancher "
            f"{GROWTH_FLOOR_PCT:.1f} % — l'articulation serait decorative."
        )


# ==========================================================================
# Harnais 3 — repartition des materiaux dans l'AIRE VUE par la camera de jeu
# ==========================================================================


def _seen_area_share(hull, parts: list, size: int = 360) -> list[tuple[str, float]]:
    """Part de chaque materiau dans les pixels VUS, z-buffer a la camera du jeu.

    Compter l'aire des triangles surestimerait tout ce qui est cache (dessous des
    doigts, gorge du puits). Ici on rasterise reellement, avec profondeur : ce qui
    est occulte ne compte pas. C'est la mesure que demande le brief pour arbitrer
    « accent ou livree » sur l'emissif.
    """
    tris = []
    for obj, pivot in [(hull, None)] + [(p.obj, Vector(p.pivot)) for p in parts]:
        verts, faces, mats = _soup_with_materials(obj)
        for face, mat in zip(faces, mats):
            tris.append(([verts[i] for i in face], mat))

    screen = []
    for pts, mat in tris:
        proj = [_project(p) for p in pts]
        if any(p is None for p in proj):
            continue
        depth = sum((p - CAM_POS).dot(CAM_Z) for p in pts) / 3.0
        screen.append((proj, depth, mat))

    xs = [p[0] for proj, _, _ in screen for p in proj]
    ys = [p[1] for proj, _, _ in screen for p in proj]
    lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)
    span = max(hi_x - lo_x, hi_y - lo_y) * 1.02
    scale = (size - 1) / span

    zbuf = [1e9] * (size * size)
    mbuf = [-1] * (size * size)
    for proj, depth, mat in screen:
        px = [((p[0] - lo_x) * scale, (p[1] - lo_y) * scale) for p in proj]
        x0 = max(0, int(min(p[0] for p in px)))
        x1 = min(size - 1, int(max(p[0] for p in px)) + 1)
        y0 = max(0, int(min(p[1] for p in px)))
        y1 = min(size - 1, int(max(p[1] for p in px)) + 1)
        (ax, ay), (bx, by), (cx, cy) = px
        det = (by - ay) * (cx - ax) - (bx - ax) * (cy - ay)
        if abs(det) < 1e-9:
            continue
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                sx, sy = x + 0.5, y + 0.5
                w0 = ((by - ay) * (cx - sx) - (bx - sx) * (cy - ay)) / det
                w1 = ((sy - ay) * (cx - ax) - (bx - ax) * (cy - ay)) / det
                w2 = 1.0 - w0 - w1
                if w0 < 0.0 or w1 < 0.0 or w2 < 0.0:
                    continue
                idx = y * size + x
                # depth = distance le long de l'axe camera, negative devant :
                # le plus GRAND (moins negatif) est le plus proche.
                if depth > -zbuf[idx]:
                    zbuf[idx] = -depth
                    mbuf[idx] = mat

    total = sum(1 for m in mbuf if m >= 0)
    counts: dict[int, int] = {}
    for m in mbuf:
        if m >= 0:
            counts[m] = counts.get(m, 0) + 1
    return [
        (ak.MATERIAL_ORDER[m], 100.0 * c / total)
        for m, c in sorted(counts.items(), key=lambda kv: -kv[1])
    ]


def _report_seen_area(shares: list[tuple[str, float]]) -> None:
    print("--- aire VUE par la camera de jeu (z-buffer, occlusion comprise) ---")
    for name, pct in shares:
        print(f"  {name:<20} {pct:5.2f} %")
    emissive = dict(shares).get("AA_Emissive_Engine", 0.0)
    verdict = "accent" if emissive <= 10.0 else "LIVREE (au-dela du seuil du brief)"
    print(f"  -> emissif : {emissive:.2f} % de l'aire vue — {verdict}")


# ==========================================================================
# Controle du livrable : UV presentes sur 100 % des primitives
# ==========================================================================


def _assert_texcoords(path: str) -> None:
    """Relit le `.glb` PRODUIT et compte `TEXCOORD_0`.

    Deux coques du depot (`needle_scout`, `crescent_interceptor`) sont sorties sans
    UV : l'exporteur n'emet aucun avertissement, la bounding box est parfaite, le
    contrat passe — et aucune feuille de detail (ADR-0011) ne peut plus s'y poser.
    Le defaut est totalement silencieux ; on ne le suppose donc pas absent, on le
    verifie sur le fichier.
    """
    with open(path, "rb") as handle:
        data = handle.read()
    length = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20 : 20 + length])
    total = 0
    with_uv = 0
    with_tan = 0
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
            f"{path} : {total - with_uv} primitive(s) sans TEXCOORD_0 — la coque ne "
            "pourrait recevoir aucune carte de detail (ADR-0011)."
        )


# ==========================================================================
# Assemblage
# ==========================================================================


def _triangulate_ngons(obj) -> None:
    """Decoupe les seules faces de plus de 4 sommets — et rien d'autre.

    Sans cela l'exporteur renonce aux TANGENTES (« tangent space can only be
    computed for tris/quads ») et ADR-0011 devient inoperant. Les n-gons viennent
    des `cap_ring` (culots de douille, tranches de doigt) ; les quads sont gardes
    tels quels, mikktspace les accepte.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(obj.data)
    bm.free()


def _finish(obj) -> None:
    ak.cleanup(obj)
    # Chanfrein a 1 segment : sur une coque de 4 000 triangles, on ne paie que les
    # aretes qui portent la lecture (gradins du noyau, aretes de bras, doigts).
    ak.bevel_sharp_edges(obj, width=0.0035, segments=1, angle_deg=33.0)
    _triangulate_ngons(obj)
    # 24 deg : un objet mecanique garde ses facettes ; seules la revolution du
    # corps et la lentille du noyau meritent d'etre fondues.
    ak.shade_smooth_by_angle(obj, angle_deg=24.0)
    ak.box_project_uv(obj, TEXELS_PER_METER)


def _bounds(objs) -> tuple[Vector, Vector]:
    lo = Vector((9e9, 9e9, 9e9))
    hi = Vector((-9e9, -9e9, -9e9))
    for obj in objs:
        for vert in obj.data.vertices:
            for a in range(3):
                lo[a] = min(lo[a], vert.co[a])
                hi[a] = max(hi[a], vert.co[a])
    return lo, hi


def claw_posts() -> list[tuple[float, float, float, float]]:
    """(azimut, rayon de charniere, z de charniere, rayon du bout de doigt).

    Les deux pinces avant sont posees par `ak.PORT` / `ak.STARBOARD` : aucun signe
    de X n'est ecrit a la main (piege documente en tete d'`aegis_kit`).
    """
    posts = []
    for side in (ak.PORT, ak.STARBOARD):
        theta = math.degrees(math.atan2(TIP_Y_FRONT, side * TIP_X))
        posts.append((theta, HINGE_R_FRONT, HINGE_Z_FRONT,
                      math.hypot(TIP_X, TIP_Y_FRONT)))
    posts.append((90.0, HINGE_R_AFT, HINGE_Z_AFT, TIP_Y_AFT))
    return posts


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)

    posts = claw_posts()
    hull = build_hull(posts)
    parts = [
        build_claw(i + 1, theta, hinge_r, hinge_z, tip_r)
        for i, (theta, hinge_r, hinge_z, tip_r) in enumerate(posts)
    ]

    _finish(hull)
    for part in parts:
        _finish(part.obj)

    objs = [hull] + [p.obj for p in parts]
    lo, hi = _bounds(objs)
    print("--- mesures en repere d'auteur (avant correction d'axe) ---")
    for obj in objs:
        o_lo, o_hi = _bounds([obj])
        print(
            f"  {obj.name:<18} x[{o_lo.x:+.4f} {o_hi.x:+.4f}] "
            f"y[{o_lo.y:+.4f} {o_hi.y:+.4f}] z[{o_lo.z:+.4f} {o_hi.z:+.4f}] "
            f"{len(obj.data.polygons)} faces"
        )
    print(
        f"  TOTAL              x[{lo.x:+.4f} {hi.x:+.4f}] y[{lo.y:+.4f} {hi.y:+.4f}] "
        f"z[{lo.z:+.4f} {hi.z:+.4f}]  ->  {hi.x - lo.x:.4f} x {hi.y - lo.y:.4f} "
        f"x {hi.z - lo.z:.4f} m"
    )
    for theta, hinge_r, _hz, tip_r in posts:
        e, h, gain = _claw_geometry(hinge_r, tip_r)
        print(
            f"  pince a {theta:7.2f} deg : debord e={e:.4f} m, plongee h={h:.4f} m, "
            f"gain de rayon {gain * 1000:.1f} mm ({100.0 * gain / tip_r:.2f} %)"
        )

    _assert_hinge_skip(hull, parts)
    _report_travel(_travel_table(hull, parts))
    _report_growth(_growth_table(hull, parts))
    _spread_table(hull, parts)
    _report_seen_area(_seen_area_share(hull, parts))

    ak.export_hull(hull, build_attach_points(), OUTPUT, CONTRACT, parts=parts)
    _assert_texcoords(OUTPUT)


if __name__ == "__main__":
    main()
