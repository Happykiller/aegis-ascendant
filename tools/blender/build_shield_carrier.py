"""build_shield_carrier.py — coque 3D du Shield Carrier, emetteur de bulle (BRIEF-0046).

    blender45 -b -P tools/blender/build_shield_carrier.py
    ./scripts/build-hull.sh --check shield_carrier      # + controle de determinisme

Produit `assets/imported/models/ships/shield_carrier.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne. Il est
deterministe (aucun alea) et s'auto-valide — `ak.export_hull()` relit le `.glb` produit
et echoue si la bounding box, le budget, les materiaux, le centrage ou les points
d'attache sortent du contrat. Quatre harnais de mesure supplementaires tournent a
chaque build et sont documentes plus bas.

Reference de design : `assets/reference/concepts/null_choir_enemy_families_sheet.png`,
**septieme et derniere cellule** : deux coques en amande enserrant un gros projecteur
central a lentille magenta, plaques d'armure en mosaique, listels ivoire en diagonale
sur les amandes, machinerie vert maladif dans la gouttiere entre amande et projecteur.
C'est la masse la plus lourde de la planche — et ce sera la plus grosse coque legere
du bestiaire (2,20 x 1,80 m contre 1,45 pour le Null Maw et 0,85 pour le Leech Drone).


CE QUI DECIDE DE CETTE COQUE : ELLE DOIT LIRE COMME UNE SOURCE, PAS COMME UN COMBATTANT
=======================================================================================
Cette unite ne tire pas, ne poursuit pas, ne touche jamais : elle rend invulnerables
les autres ennemis de sa bulle. Le joueur doit comprendre en une seconde que c'est
elle qu'il faut abattre d'abord. Quatre partis pris servent exclusivement cette lecture :

1. **Un oeil, pas une bouche.** Le projecteur est un tambour dorsal coiffe d'une
   lentille magenta de 322 mm de rayon qui regarde le CIEL, pas le joueur. La camera
   de jeu est a 20 deg de la verticale : c'est la seule orientation d'emissif qui
   occupe reellement l'ecran. Rien ne pointe vers l'avant.
2. **Aucune pointe, aucun fut, aucun nez.** L'avant est une etrave LARGE et emoussee
   (680 mm de front) percee d'une grille sombre : une face, pas un museau. `Muzzle_C`
   existe parce que `EnemyController` le lit a l'initialisation de toute coque, et il
   est pose sur cette grille — c'est un event, pas une arme.
3. **La masse est l'information.** 2,20 x 1,80 m : presque le double de la Choir Mine,
   deux fois et demie la sangsue. A 46 px elle est deux fois plus large que tout ce
   que le joueur a vu jusque-la, et c'est ce qui se lit avant le detail.
4. **Elle vole, elle n'attend pas.** Contre les deux mines (posees), elle a une
   tuyere ventrale arriere (`Engine_C`) et un berceau arriere qui l'abrite : un
   arriere existe, donc un sens de marche.

Ou va le detail : la camera regarde a 20 deg de la VERTICALE. Tout le detail est sur
les surfaces superieures (mosaique de plaques enfoncees des amandes, pont annulaire
autour du tambour, gradins du projecteur, veines magenta) ; les dessous sont en
`AA_Greeble` sans detail (BRIEF-0026, rappele par ADR-0011).


LES BRAS PORTENT LA SILHOUETTE — LA LECON DE BRIEF-0042, DEJA PAYEE DEUX FOIS
============================================================================
Sur la Choir Mine, six plaques pivotaient parfaitement et l'ouverture etait invisible :
l'enveloppe appartenait a la couronne de modules et non aux plaques, que le pivot
faisait meme RENTRER.

La cause est geometrique et generale. `EnemyPose` tourne la piece autour de la
tangente horizontale a son rayon ; on verifie analytiquement que `axe x radial = +Y` :
un angle positif emmene le rayon vers le HAUT. Une piece qui pointe deja vers
l'exterieur voit donc son rayon multiplie par cos(angle) — **elle rentre**. Pour
qu'une rotation FASSE GROSSIR l'enveloppe, la piece doit plonger sous son propre
plan au repos et se relever vers l'horizontale en s'ouvrant. Le gain vaut exactement
`hypot(e, h) - e` (e = debord radial au-dela de la charniere, h = plongee sous elle)
et l'angle optimal vaut `atan(h / e)` ; **au-dela, l'enveloppe redescend**.

D'ou la mecanique de cette coque : les deux amandes ne sont pas des coques fixes, ce
sont **les deux grands bras de berceau**. Chacune est charniere sur la ligne
longitudinale `x = +/-0,585` et **retombe vers l'exterieur** : tout son bord exterieur
est pose sur le cone de pente `OPEN_DEG` issu de la charniere, si bien qu'a l'ouverture
la coquille entiere se releve d'un coup a l'horizontale et son rayon passe de 1,100 a
1,258 m. Le troisieme bras fait de meme a l'arriere, au-dessus de la tuyere.

Consequence voulue : **les trois extremes lateraux et arriere de la bounding box
appartiennent a des pieces mobiles**, et la coque FIXE (etrave, pont, tambour) ne les
atteint jamais. `_report_growth()` refuse d'exporter si ce n'est plus vrai, a n'importe
quel angle du balayage, globalement ET dans le secteur azimutal propre a chaque bras.

ECART ASSUME AU BRIEF (§ "Pieces articulees"). Le brief decrit des bras qui
« s'ecartent vers l'exterieur EN DECOUVRANT le projecteur ». Un bras qui recouvre la
lentille au repos devrait avoir son extremite du cote INTERIEUR de sa charniere ; le
signe de rotation d'`EnemyPose` la ferait alors plonger DANS le tambour, et surtout
un tel bras ne porterait aucune enveloppe (defaut exact de BRIEF-0042). Ce qui se
decouvre ici n'est donc pas la lentille — visible en permanence, c'est la fonction de
l'unite — mais **la gouttiere emissive et la machinerie vert maladif du joint**, que
les coquilles plaquent au repos et qui s'allume en grand quand elles se relevent.


Repere d'auteur (ADR-0008) : nez -Y, dessus +Z, **babord +X** (cf. aegis_kit).
Kit reutilise SANS modification (kit 1.1.0 : `inset_panel()` met lui-meme les normales
a jour ; l'option `per_face` est choisie ici sciemment, plaque par plaque, parce que la
planche montre une MOSAIQUE d'ecailles et non une grande region enfoncee).
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
    name="Shield Carrier",
    width_x=2.20,        # Godot X — impose par le brief
    length_z=1.80,       # Godot Z — impose par le brief
    max_height_y=0.70,   # Godot Y — plafond du brief
    tri_budget=8_000,    # elle n'arrive pas en essaim : une ou deux par vague
    required_materials=ak.MATERIAL_ORDER,
    required_attach_points=("Muzzle_C", "Engine_C"),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/ships/shield_carrier.glb")

#: Feuille de detail ADR-0011 : ~40 cm de periode sur une coque de 2,20 m.
#: (Choir Mine 4,0 pour 1,15 m ; Leech Drone 6,0 pour 0,70 m — meme densite apparente.)
TEXELS_PER_METER = 2.5

# ==========================================================================
# Geometrie d'ensemble
# ==========================================================================

#: Angle d'ouverture OPTIMAL, commun aux trois bras : c'est lui qui fixe la plongee
#: de chaque bord mobile (h = e * tan(OPEN_DEG)). Au-dela, l'enveloppe se remet a
#: retrecir — `_growth_table()` le montre a chaque build.
OPEN_DEG = 40.0
_TAN_OPEN = math.tan(math.radians(OPEN_DEG))

#: Ligne de charniere des deux coquilles, en X (babord ; `ak.PORT` pose le signe).
JOINT_X = 0.585
#: Hauteur de cette ligne : c'est le niveau du pont, la ou la coquille affleure.
JOINT_Z = 0.140
#: Demi-largeur hors-tout visee (bord exterieur de coquille, au maitre-couple).
TIP_X = 1.100

#: Berceau arriere : charniere et bout.
AFT_HINGE_Y = 0.590
AFT_HINGE_Z = 0.120
AFT_TIP_Y = 0.898

#: Jeu mecanique au joint : la coquille ne touche PAS le flanc du corps fixe.
#: 12 mm — assez pour qu'aucun facettage ne les fasse mordre, assez peu pour que la
#: gouttiere reste une ligne et non une fente.
JOINT_GAP = 0.012

# ==========================================================================
# Corps fixe — un fuseau plat qui porte l'etrave, le pont et le tambour
# ==========================================================================

#: Demi-contour BABORD du corps fixe, de la pointe d'etrave a la face arriere.
#: (x, y) dans le plan de jeu. L'etrave est LARGE (680 mm de front) : c'est une face,
#: pas un museau — le brief interdit tout ce qui ressemble a une arme.
BODY_HALF: tuple[tuple[float, float], ...] = (
    (0.000, -0.902),
    (0.190, -0.894),
    (0.352, -0.858),
    (0.492, -0.780),
    (0.552, -0.672),
    (0.570, -0.516),
    (JOINT_X - JOINT_GAP, -0.330),
    (JOINT_X - JOINT_GAP, -0.020),
    (0.571, 0.190),
    (0.556, 0.330),
    (0.514, 0.440),
    (0.432, 0.520),
    (0.248, 0.562),
    (0.000, 0.572),
)

#: Centre d'homothetie des niveaux (le fuseau n'est pas centre sur l'origine : le
#: mettre a l'echelle autour de (0,0) le deformerait vers l'avant).
BODY_PIVOT = (0.0, -0.165)

#: (echelle du contour, z, materiau de la bande qui MONTE depuis ce niveau, rayon
#: du CERCLE sur lequel refermer le niveau — `None` = contour mis a l'echelle).
#: Le niveau 1,00 est repete a deux hauteurs : c'est le flanc vertical du joint,
#: la paroi contre laquelle la coquille vient se plaquer.
#:
#: ⚠️ Le dernier niveau est un CERCLE et non une homothetie du fuseau. Mis a
#: l'echelle, le contour reste plus long que large : son bord interieur passait
#: 118 mm devant le tambour et ouvrait un croissant de vide en pleine proue — un
#: trou noir parfaitement visible sur la premiere planche de recette.
BODY_LEVELS: tuple[tuple[float, float, str, float | None], ...] = (
    (0.34, -0.200, "AA_Greeble", None),   # plancher ventral
    (0.78, -0.150, "AA_Greeble", None),
    (0.95, -0.060, "AA_Greeble", None),   # ventre
    (1.00, 0.020, "AA_Hull", None),       # ceinture — maitre-couple
    (1.00, JOINT_Z, "AA_Panel", None),    # haut du flanc : la gouttiere du joint
    (0.93, 0.180, "AA_Hull", None),       # pont — la surface que la camera voit
    (0.78, 0.200, "AA_Panel", None),
    (0.56, 0.190, "AA_Greeble", 0.400),   # col circulaire, noye sous le tambour
)

# ==========================================================================
# Projecteur : tambour a gradins coiffe de la lentille magenta
# ==========================================================================

#: (z, rayon, materiau de la bande sortante). C'EST la fonction de l'unite : la
#: lentille fait 322 mm de rayon et regarde le ciel, donc la camera.
PROJECTOR: list[tuple[float, float, str]] = [
    (-0.150, 0.000, "AA_Greeble"),
    (-0.140, 0.180, "AA_Greeble"),
    (-0.080, 0.320, "AA_Greeble"),
    (0.000, 0.410, "AA_Greeble"),
    (0.060, 0.450, "AA_Hull"),
    (0.140, 0.462, "AA_Hull"),            # maitre-couple du tambour
    (0.185, 0.455, "AA_Panel"),           # epaulement : les 20 ecailles du collier
    (0.205, 0.420, "AA_Greeble"),         # gradin
    (0.225, 0.415, "AA_Trim"),            # filet ivoire
    (0.235, 0.372, "AA_Greeble"),
    (0.245, 0.368, "AA_Glass"),           # membrane sombre : le cerne de l'oeil
    (0.252, 0.330, "AA_Glass"),
    (0.258, 0.322, "AA_Emissive_Engine"), # lentille
    (0.286, 0.278, "AA_Emissive_Engine"),
    (0.310, 0.180, "AA_Emissive_Engine"),
    (0.320, 0.000, "AA_Emissive_Engine"), # pole : point haut de la coque
]
PROJECTOR_SEGMENTS = 20

#: Iris : bande de la lentille dont un segment sur cinq repasse en `AA_Greeble`.
#: Quatre rayons sombres, ZERO triangle supplementaire — et l'oeil cesse d'etre
#: une bille rose uniforme (la planche montre un iris a rayons).
IRIS_BAND = 13
IRIS_EVERY = 5

#: Rayon en deca duquel une face compte pour « le projecteur » dans le releve
#: d'emissif (le brief veut la repartition PROJECTEUR contre RESTE DE LA COQUE).
PROJECTOR_RADIUS = 0.470

# ==========================================================================
# Coquilles en amande — les deux grands bras de berceau
# ==========================================================================

#: (y, x du bord exterieur). Le maitre-couple (x = TIP_X) est a y = 0 : c'est LA
#: condition pour que l'axe de charniere soit exactement longitudinal (`EnemyPose`
#: deduit l'axe de la POSITION du pivot ; un pivot hors de l'axe y=0 donnerait une
#: charniere oblique et la coquille vrillerait).
SHELL_STATIONS: tuple[tuple[float, float], ...] = (
    (-0.720, 0.665),
    (-0.600, 0.832),
    (-0.430, 0.972),
    (-0.220, 1.062),
    (0.000, TIP_X),
    (0.220, 1.070),
    (0.400, 1.000),
    (0.530, 0.880),
    (0.630, 0.700),
)

#: Section transversale d'une coquille, de la charniere (u=0) au bord (u=1).
#: `zfac` est une FRACTION de la plongee ; la plongee elle-meme vaut
#: (x_bord - JOINT_X) * tan(OPEN_DEG), donc **tout le bord exterieur est pose sur
#: le meme cone** : a OPEN_DEG la coquille entiere se retrouve a plat, d'un coup.
#: `thick` : epaisseur sous la peau (l'amande est bombee, pas une tole).
SHELL_PROFILE: tuple[tuple[float, float, float], ...] = (
    (0.000, 0.000, 0.105),
    (0.230, 0.098, 0.098),
    (0.470, 0.010, 0.082),
    (0.720, -0.330, 0.060),
    (1.000, -1.000, 0.038),
)

#: Indices de segment d'une bande de coquille (voir `_shell_ring`).
SHELL_TOP = (0, 1, 2, 3)
SHELL_RIM = (4,)
SHELL_BOTTOM = (5, 6, 7, 8)
SHELL_INBOARD = (9,)

#: Une ecaille d'armure = DEUX bandes consecutives, insetees en REGION (un seul
#: lisere autour de leur union). C'est le second usage d'`inset_panel`, choisi
#: sciemment : `per_face` sur les 32 faces du dessus rendait un damier de petites
#: tuiles regulieres — la planche montre de GRANDES ecailles.
SHELL_PLATE_ROWS = ((0, 1), (2, 3), (4, 5), (6, 7))
#: Listel ivoire en diagonale (signature de la planche) : (rangee, segment).
SHELL_TRIM_PLATES = ((1, 1), (2, 2))
#: Deux ecailles vert maladif — « usage tres limite » (charte) — a des positions
#: NON symetriques, et sur la seule coquille babord : le Choeur Nul est asymetrique.
SHELL_GREEN_PLATES = ((0, 0), (3, 3))

# ==========================================================================
# Berceau arriere
# ==========================================================================

#: (fraction du debord e, fraction de la plongee h, demi-largeur, epaisseur).
#: Le bras ARQUE au-dessus de la tuyere (zfac positif au debut) et ne plonge qu'a
#: son talon : la plume sort dessous sans rien traverser.
AFT_PROFILE: tuple[tuple[float, float, float, float], ...] = (
    (0.000, 0.000, 0.340, 0.092),
    (0.330, 0.070, 0.336, 0.086),
    (0.630, -0.060, 0.306, 0.076),
    (0.855, -0.480, 0.238, 0.062),
    (1.000, -1.000, 0.148, 0.044),
)

# ==========================================================================
# Tuyere, etrave, veines : les petites pieces du corps fixe
# ==========================================================================

#: (y, demi-largeur, demi-hauteur, z). Bloc de poussee ventral arriere.
#: ⚠️ La hauteur de la tuyere n'est pas libre : le talon du berceau arriere plonge
#: a z = -0,177. Une plume accrochee plus bas serait transpercee par lui. Elle est
#: donc calee assez haut pour passer AU-DESSUS du talon, et la ligne de visee du
#: joueur (70 deg) l'atteint sans rien traverser.
EXHAUST: tuple[tuple[float, float, float, float], ...] = (
    (0.380, 0.150, 0.080, -0.070),
    (0.560, 0.185, 0.092, -0.083),
    (0.700, 0.170, 0.084, -0.089),
    (0.762, 0.132, 0.064, -0.091),
)
ENGINE_Y = 0.800
ENGINE_Z = -0.091

#: Grille d'etrave : quatre ecailles du pont de proue, creusees une seconde fois en
#: `AA_Glass`. Un bloc en saillie serait soit une arme, soit — comme au premier
#: essai — integralement enterre sous le pont et donc invisible.
INTAKE_PLATES = (0, 1, -1, -2)
MUZZLE_Y = -0.795
MUZZLE_Z = 0.192

#: Veines magenta du pont : (azimut en degres, rayon de depart, rayon d'arrivee).
#: Elles rayonnent du tambour vers la gouttiere ; azimuts NON symetriques deux a
#: deux du meme cote (le Choeur Nul est asymetrique, charte SS4).
VEINS: tuple[tuple[float, float, float], ...] = (
    (34.0, 0.455, 0.548),
    (128.0, 0.455, 0.520),
    (-52.0, 0.455, 0.540),
    (-142.0, 0.455, 0.516),
    (88.0, 0.455, 0.545),
)
VEIN_HALF_W = 0.017
VEIN_HALF_H = 0.011
VEIN_Z = 0.180

#: Segments de gouttiere emissive au joint (indices de segment du contour du corps),
#: cote babord ; `build_body` pose le miroir. C'est ce que les coquilles decouvrent.
GUTTER_SEGMENTS = (5, 6, 7, 8)

#: Blocs vert maladif de la gouttiere (azimut, rayon, demi-largeur, demi-longueur).
GREEN_BLOCKS: tuple[tuple[float, float, float, float, float], ...] = (
    (0.500, -0.260, 0.055, 0.090, 0.150),
    (-0.520, 0.150, 0.048, 0.078, 0.148),
    (0.505, 0.300, 0.040, 0.062, 0.146),
)

# ==========================================================================
# Harnais : debattement, croissance d'enveloppe, aire vue
# ==========================================================================

TRAVEL_FLOOR_DEG = OPEN_DEG    # on refuse d'exporter sous l'angle optimal d'ouverture
TRAVEL_STEP_DEG = 1.0
TRAVEL_MAX_DEG = 90.0
#: Plancher de croissance du diametre apparent pose PAR AVANCE par le brief.
GROWTH_FLOOR_PCT = 10.0

#: Camera de jeu, lue sur `scenes/gameplay/graybox.tscn` (Camera3D de CameraDirector).
#: Transform3D est serialise en LIGNES de la base : les colonnes (les axes) sont donc
#: les transposees. Axe de visee a 70 deg sous l'horizontale, a 14,87 unites du plan
#: de jeu. Mesurer l'enveloppe au cadrage serre de `render-hull.py` (qui colle la
#: camera a ~2,4 m) surestimerait la croissance d'un facteur ~7.
CAM_POS = Vector((0.0, 14.0, 5.0))
CAM_X = Vector((1.0, 0.0, 0.0))
CAM_Y = Vector((0.0, 0.342, -0.940))
CAM_Z = Vector((0.0, 0.940, 0.342))
CAM_FOV_DEG = 62.0
SCREEN_H = 1080.0


# ==========================================================================
# Helpers geometriques — uniquement des primitives du kit, kit NON modifie
# ==========================================================================


def _loft(
    bm: bmesh.types.BMesh,
    rings: list[list[bmesh.types.BMVert]],
    material: str,
    cap_first: str | None = None,
    cap_last: str | None = None,
) -> list[list[bmesh.types.BMFace]]:
    """Relie une suite de sections fermees par des bandes de quads.

    Chaque section est une liste EXPLICITE de points 3D : contrairement au `_sweep`
    du Leech Drone (profil fixe, mis a l'echelle), les coquilles changent de FORME
    d'une station a l'autre — le bord exterieur suit un cone et la peau se bombe.
    Bati sur `ak.add_ring` / `ak.bridge_rings` / `ak.cap_ring` du kit.
    """
    bands = [
        ak.bridge_rings(bm, rings[i], rings[i + 1], material)
        for i in range(len(rings) - 1)
    ]
    if cap_first is not None:
        ak.cap_ring(bm, list(reversed(rings[0])), cap_first)
    if cap_last is not None:
        ak.cap_ring(bm, rings[-1], cap_last)
    return bands


def _ring(bm: bmesh.types.BMesh, points: list[Vector]) -> list[bmesh.types.BMVert]:
    return ak.add_ring(bm, [tuple(p) for p in points])


def _recalc(bm: bmesh.types.BMesh, faces: list[bmesh.types.BMFace]) -> None:
    """Oriente les faces d'un solide qu'on vient de batir, AVANT tout inset.

    ⚠️ Sans cela, le sens de creusement de `ak.inset_panel()` depend du winding
    qu'on a donne a la boucle : une section decrite dans l'autre sens SOULEVE le
    panneau au lieu de le creuser (piege documente dans le kit, corollaire du
    point 1 de `inset_panel`). `ak.new_object()` ne recalcule qu'a la toute fin,
    c'est-a-dire trop tard.
    """
    live = [f for f in faces if f is not None and f.is_valid]
    if live:
        bmesh.ops.recalc_face_normals(bm, faces=live)


def _assert_up(faces: list[bmesh.types.BMFace], label: str) -> None:
    """Garde-fou : ces faces doivent regarder le ciel (donc la camera de jeu)."""
    live = [f for f in faces if f is not None and f.is_valid]
    if not live:
        raise ak.ContractError(f"{label} : aucune face a orienter")
    for face in live:
        face.normal_update()
    worst = min(f.normal.z for f in live)
    if worst <= 0.0:
        raise ak.ContractError(
            f"{label} : une face du dessus regarde vers le bas (n.z = {worst:+.3f}) — "
            "l'inset SOULEVERAIT le panneau au lieu de le creuser."
        )


def _mirror_half(half: tuple[tuple[float, float], ...]) -> list[tuple[float, float]]:
    """Contour ferme depuis un demi-contour babord (premier et dernier sur l'axe)."""
    out = [p for p in half]
    for x, y in reversed(half[1:-1]):
        out.append((-x, y))
    return out


def _scaled(points: list[tuple[float, float]], scale: float) -> list[tuple[float, float]]:
    cx, cy = BODY_PIVOT
    return [(cx + (x - cx) * scale, cy + (y - cy) * scale) for x, y in points]


def _on_circle(x: float, y: float, radius: float) -> tuple[float, float]:
    """Ramene un point sur le cercle de rayon `radius` centre sur l'AXE, meme azimut.

    Garde la correspondance angulaire point a point avec le niveau precedent : un
    cercle echantillonne regulierement, lui, vrillerait les quads du col.
    """
    d = math.hypot(x, y)
    if d < 1e-9:
        return (0.0, radius)
    return (x / d * radius, y / d * radius)


def _bar(
    bm: bmesh.types.BMesh,
    start: Vector,
    end: Vector,
    half_w: float,
    half_h: float,
    material: str,
) -> list[list[bmesh.types.BMFace]]:
    """Barrette rectangulaire orientee de `start` a `end` (veines, blocs, listels)."""
    axis = (end - start)
    axis.z = 0.0
    if axis.length < 1e-9:
        raise ak.ContractError("_bar : longueur nulle")
    axis.normalize()
    side = Vector((-axis.y, axis.x, 0.0))
    up = Vector((0.0, 0.0, 1.0))
    rings = []
    for centre in (start, end):
        rings.append(
            _ring(
                bm,
                [
                    centre + side * half_w + up * half_h,
                    centre - side * half_w + up * half_h,
                    centre - side * half_w - up * half_h,
                    centre + side * half_w - up * half_h,
                ],
            )
        )
    return _loft(bm, rings, material, cap_first=material, cap_last=material)


def _axial_ring(
    bm: bmesh.types.BMesh, y: float, half_w: float, half_h: float, z: float
) -> list[bmesh.types.BMVert]:
    """Section rectangulaire d'une piece axiale (tuyere, event d'etrave)."""
    return _ring(
        bm,
        [
            Vector((half_w, y, z + half_h)),
            Vector((-half_w, y, z + half_h)),
            Vector((-half_w, y, z - half_h)),
            Vector((half_w, y, z - half_h)),
        ],
    )


# ==========================================================================
# Corps fixe
# ==========================================================================


def build_body(bm: bmesh.types.BMesh) -> None:
    """Fuseau plat : ventre, ceinture, flanc du joint, pont annulaire."""
    outline = _mirror_half(BODY_HALF)
    rings = []
    for scale, z, _mat, circle in BODY_LEVELS:
        points = _scaled(outline, scale)
        if circle is not None:
            points = [_on_circle(x, y, circle) for x, y in points]
        rings.append(_ring(bm, [Vector((x, y, z)) for x, y in points]))
    bands = _loft(
        bm,
        rings,
        "AA_Hull",
        cap_first="AA_Greeble",
        cap_last="AA_Greeble",
    )
    for index, band in enumerate(bands):
        ak.set_material(band, BODY_LEVELS[index][2])
    faces = [f for band in bands for f in band]
    _recalc(bm, faces)

    # Gouttiere du joint (bande 4 : la petite pente qui remonte du flanc au pont).
    # C'est CE qui se decouvre quand les coquilles se relevent : quelques segments
    # emissifs, pas l'anneau entier — au-dela ce ne serait plus un accent.
    gutter = bands[4]
    n = len(gutter)
    lit = []
    for seg in GUTTER_SEGMENTS:
        lit.append(gutter[seg % n])
        lit.append(gutter[(n - 1 - seg) % n])
    ak.set_material(lit, "AA_Emissive_Engine")

    # Pont : une ecaille enfoncee PAR FACE (per_face=True). La planche montre une
    # mosaique de plaques distinctes ; un inset de region ne rendrait qu'un seul
    # grand anneau creux et aucune ecaille.
    deck = [f for f in bands[5] if f is not None and f.is_valid]
    _assert_up(deck, "pont du corps fixe")
    ak.set_material(
        ak.inset_panels(bm, deck, "AA_Panel", thickness=0.022, depth=-0.011),
        "AA_Greeble",
    )

    # Grille d'etrave : les quatre ecailles de proue, creusees une seconde fois.
    # `inset_panels` rend les LISERES ; les fonds sont les faces passees en entree,
    # toujours valides — c'est sur elles qu'on recreuse.
    ak.set_material(
        ak.inset_panels(
            bm,
            [deck[i] for i in INTAKE_PLATES],
            "AA_Glass",
            thickness=0.026,
            depth=-0.020,
        ),
        "AA_Trim",   # lippe ivoire : l'event se lit comme une prise, pas comme un trou
    )

    # Veines magenta du pont, du collier du tambour vers la gouttiere.
    for azimuth, r0, r1 in VEINS:
        a = math.radians(azimuth)
        d = Vector((math.cos(a), math.sin(a), 0.0))
        _bar(
            bm,
            Vector((d.x * r0, d.y * r0, VEIN_Z)),
            Vector((d.x * r1, d.y * r1, VEIN_Z)),
            VEIN_HALF_W,
            VEIN_HALF_H,
            "AA_Emissive_Engine",
        )

    # Machinerie vert maladif dans la gouttiere (la planche en montre entre la
    # coquille et le projecteur). `AA_Marking_Red` porte le vert du Choeur Nul.
    for x, y, half_w, half_l, z in GREEN_BLOCKS:
        _bar(
            bm,
            Vector((x, y - half_l, z)),
            Vector((x, y + half_l, z)),
            half_w,
            0.028,
            "AA_Marking_Red",
        )

    # Tuyere ventrale arriere : elle vole sous puissance (Engine_C).
    rings = [_axial_ring(bm, *row) for row in EXHAUST]
    nacelle = _loft(bm, rings, "AA_Greeble", cap_first="AA_Greeble")
    ak.set_material(nacelle[1], "AA_Hull")
    ak.cap_ring(bm, rings[-1], "AA_Emissive_Engine")



def build_projector(bm: bmesh.types.BMesh) -> None:
    """Tambour dorsal + lentille magenta : la fonction de l'unite, tournee vers le ciel."""
    bands = ak.add_lathe(bm, PROJECTOR, PROJECTOR_SEGMENTS, axis="Z")
    faces = [f for band in bands for f in band if f is not None]
    _recalc(bm, faces)
    # Collier a 20 ecailles : per_face, pour la meme raison que le pont.
    collar = [f for f in bands[6] if f is not None and f.is_valid]
    ak.inset_panels(bm, collar, "AA_Greeble", thickness=0.016, depth=-0.009)
    # Iris : un segment sur cinq de la bande mediane de la lentille repasse en
    # sombre. Quatre rayons, zero triangle de plus.
    ak.set_material(
        [f for k, f in enumerate(bands[IRIS_BAND]) if k % IRIS_EVERY == 0],
        "AA_Greeble",
    )


# ==========================================================================
# Coquilles en amande — pieces mobiles Cradle_01 / Cradle_02
# ==========================================================================


def _shell_ring(side: float, y: float, x_out: float) -> list[Vector]:
    """Section d'une coquille : peau (u croissant) puis dessous (u decroissant).

    Le bord exterieur est pose sur le cone de pente `OPEN_DEG` issu de la charniere :
    `plongee = (x_out - JOINT_X) * tan(OPEN_DEG)`. C'est ce qui fait que la coquille
    ENTIERE arrive a plat au meme angle — et que le rayon maximal est atteint la.
    """
    drop = (x_out - JOINT_X) * _TAN_OPEN
    span = x_out - JOINT_X
    top, bottom = [], []
    for u, zfac, thick in SHELL_PROFILE:
        x = JOINT_X + span * u
        z = JOINT_Z + zfac * drop
        top.append(Vector((side * x, y, z)))
        bottom.append(Vector((side * x, y, z - thick)))
    return top + list(reversed(bottom))


def build_shell(index: int, side: float) -> ak.MovingPart:
    """Une coquille en amande, batie en coordonnees ABSOLUES, origine sur sa charniere.

    ⚠️ Toute la matiere est du cote EXTERIEUR de la ligne de charniere. Une ecaille
    posee en deca plongerait vers le bas ET vers l'interieur a l'ouverture, c'est-a-dire
    dans le corps fixe (verifie par le harnais de debattement, qui la verrait mordre).
    """
    bm = bmesh.new()
    rings = [
        _ring(bm, _shell_ring(side, y, x_out)) for y, x_out in SHELL_STATIONS
    ]
    bands = _loft(bm, rings, "AA_Hull", cap_first="AA_Greeble", cap_last="AA_Greeble")
    for band in bands:
        ak.set_material([band[k] for k in SHELL_RIM], "AA_Greeble")
        ak.set_material([band[k] for k in SHELL_BOTTOM], "AA_Hull")
        ak.set_material([band[k] for k in SHELL_INBOARD], "AA_Greeble")
    faces = [f for band in bands for f in band if f is not None]
    _recalc(bm, faces)

    # Grandes ecailles d'armure : chacune couvre DEUX bandes et se creuse en REGION
    # (un seul lisere autour de leur union). Carapace violette, listel ivoire en
    # diagonale (signature de la planche), deux ecailles vert maladif sur la seule
    # coquille babord.
    _assert_up(
        [band[k] for band in bands for k in SHELL_TOP], f"peau de la coquille {index}"
    )
    for row, rows in enumerate(SHELL_PLATE_ROWS):
        for seg in SHELL_TOP:
            plate = [bands[b][seg] for b in rows]
            plate = [f for f in plate if f is not None and f.is_valid]
            if not plate:
                continue
            if (row, seg) in SHELL_TRIM_PLATES:
                material = "AA_Trim"
            elif side > 0.0 and (row, seg) in SHELL_GREEN_PLATES:
                material = "AA_Marking_Red"
            else:
                material = "AA_Panel"
            groove = ak.inset_panel(bm, plate, material, thickness=0.028, depth=-0.014)
            # Le lisere repasse en `AA_Greeble` : sans cela il garde le materiau de
            # la face d'origine et, chanfreine, il accroche assez de lumiere pour
            # transformer la carapace en grille d'aluminium. La planche montre des
            # ecailles separees par des RAINURES SOMBRES.
            ak.set_material(groove, "AA_Greeble")

    return ak.moving_part(
        f"Cradle_{index:02d}", bm, (side * JOINT_X, 0.0, JOINT_Z)
    )


# ==========================================================================
# Berceau arriere — piece mobile Cradle_03
# ==========================================================================


def build_aft_cradle(index: int) -> ak.MovingPart:
    """Arceau arriere : il enjambe la tuyere et retombe en talon derriere elle."""
    bm = bmesh.new()
    reach = AFT_TIP_Y - AFT_HINGE_Y
    drop = reach * _TAN_OPEN
    rings = []
    for efac, zfac, half_w, thick in AFT_PROFILE:
        y = AFT_HINGE_Y + reach * efac
        z = AFT_HINGE_Z + zfac * drop
        # Section HEXAGONALE, pas rectangulaire : au premier rendu la caisse a
        # aretes vives lisait comme un conteneur accroche sous la poupe, et non
        # comme le troisieme bras du berceau.
        rings.append(
            _ring(
                bm,
                [
                    Vector((half_w * 0.68, y, z)),
                    Vector((-half_w * 0.68, y, z)),
                    Vector((-half_w, y, z - thick * 0.42)),
                    Vector((-half_w * 0.80, y, z - thick)),
                    Vector((half_w * 0.80, y, z - thick)),
                    Vector((half_w, y, z - thick * 0.42)),
                ],
            )
        )
    bands = _loft(bm, rings, "AA_Hull", cap_first="AA_Greeble", cap_last="AA_Greeble")
    for band in bands:
        ak.set_material([band[k] for k in (2, 3, 4)], "AA_Greeble")
    faces = [f for band in bands for f in band if f is not None]
    _recalc(bm, faces)
    top = [band[0] for band in bands if band[0] is not None and band[0].is_valid]
    _assert_up(top, "dos du berceau arriere")
    for plate, material in ((top[:2], "AA_Panel"), (top[2:], "AA_Panel")):
        ak.set_material(
            ak.inset_panel(bm, plate, material, thickness=0.026, depth=-0.013),
            "AA_Greeble",
        )
    return ak.moving_part(
        f"Cradle_{index:02d}", bm, (0.0, AFT_HINGE_Y, AFT_HINGE_Z)
    )


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


def _soup(obj):
    """(sommets, triangles) d'un objet, en repere GODOT."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.index_update()
    verts = [_TO_GODOT @ v.co for v in bm.verts]
    tris = [[loop.vert.index for loop in face.loops] for face in bm.faces]
    bm.free()
    return verts, tris


def _soup_with_materials(obj):
    """(sommets, triangles, index de materiau) en repere GODOT — pour les aires."""
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


def _travel_table(hull, parts: list) -> list[tuple]:
    """Debattement mecanique de chaque bras, mesure sur le maillage livre.

    ⚠️ Aucun rayon d'exclusion autour des charnieres, contrairement au Leech Drone
    qui devait en amputer 60 mm pour ne pas compter sa douille comme une collision :
    ici rien n'est encastre dans la coque fixe (le joint garde 12 mm de jeu, le
    berceau arriere repose derriere le tableau), donc la mesure porte sur la
    geometrie REELLE et la marge imprimee au repos est la vraie marge du joint.
    """
    names = [p.obj.name for p in parts]
    pivot = {p.obj.name: _TO_GODOT @ Vector(p.pivot) for p in parts}
    axis = {n: _hinge_axis(pivot[n]) for n in names}

    local, tris, hull_solid = {}, {}, {}
    for part in parts:
        name = part.obj.name
        verts, faces = _soup(part.obj)
        local[name] = [v - pivot[name] for v in verts]
        tris[name] = faces
    hull_solid = Solid(*_soup(hull))

    steps = int(TRAVEL_MAX_DEG / TRAVEL_STEP_DEG)
    limit = {n: TRAVEL_MAX_DEG for n in names}
    blocker = {n: "aucun contact jusqu'a %.0f deg" % TRAVEL_MAX_DEG for n in names}
    margin_at = {n: {} for n in names}

    for s in range(steps + 1):
        deg = s * TRAVEL_STEP_DEG
        angle = math.radians(deg)
        posed = {
            n: [
                Matrix.Translation(pivot[n]) @ Matrix.Rotation(angle, 4, axis[n]) @ v
                for v in local[n]
            ]
            for n in names
        }
        solids = {n: Solid(posed[n], tris[n]) for n in names}
        for i, name in enumerate(names):
            worst, who = 9.9, ""
            d = hull_solid.distance_to(posed[name], tris[name])
            if d < worst:
                worst, who = d, "coque fixe (corps/tambour/tuyere)"
            for j, other in enumerate(names):
                if j == i:
                    continue
                d = solids[other].distance_to(posed[name], tris[name])
                if d < worst:
                    worst, who = d, f"voisin {other}"
            margin_at[name][deg] = (worst, who)
            if worst <= 0.0 and limit[name] > deg:
                limit[name] = deg - TRAVEL_STEP_DEG
                blocker[name] = who

    return [
        (
            p.obj.name,
            pivot[p.obj.name],
            axis[p.obj.name],
            limit[p.obj.name],
            blocker[p.obj.name],
            margin_at[p.obj.name],
        )
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
    print(f"  -> debattement retenu (le plus contraint des trois) : {worst:.1f} deg")
    if worst < TRAVEL_FLOOR_DEG:
        raise ak.ContractError(
            f"debattement insuffisant : {worst:.1f} deg < plancher "
            f"{TRAVEL_FLOOR_DEG:.1f} deg — les bras mordraient avant d'etre ouverts."
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


def _part_state(parts: list):
    state = []
    for part in parts:
        pivot = _TO_GODOT @ Vector(part.pivot)
        verts, _ = _soup(part.obj)
        state.append(
            (
                part.obj.name,
                pivot,
                _radial_axis(pivot),
                Vector((pivot.x, pivot.z)).length,
                [v - pivot for v in verts],
            )
        )
    return state


def _posed_points(hull_verts, state, deg: float, spread: float, yaw_deg: float):
    """Sommets monde (Godot) de toute la coque a une ouverture donnee.

    Reproduit `EnemyPose.pose()` : `Basis(axe, angle)` puis
    `position = rest + radial * rayon_XZ * spread * open`. `yaw_deg` est
    l'orientation du nœud en jeu (0 = nez vers le haut de l'ecran).
    """
    yaw = Matrix.Rotation(math.radians(yaw_deg), 4, "Y")
    out = [(yaw @ v, None) for v in hull_verts]
    angle = math.radians(deg)
    for name, pivot, radial, radius, local in state:
        offset = pivot + radial * (radius * spread)
        rot = Matrix.Rotation(angle, 4, _hinge_axis(pivot))
        for v in local:
            out.append((yaw @ (offset + rot @ v), name))
    return out


def _sector_radius(points, name, azimuth: float, half_width: float = 25.0):
    """Rayon XZ maximal dans un secteur azimutal, pour la piece `name` (None = coque)."""
    best = 0.0
    for v, owner in points:
        keep = (owner is None) if name is None else (owner == name)
        if not keep:
            continue
        r = math.hypot(v.x, v.z)
        if r < 1e-6:
            continue
        a = math.degrees(math.atan2(v.z, v.x))
        delta = abs((a - azimuth + 180.0) % 360.0 - 180.0)
        if delta <= half_width:
            best = max(best, r)
    return best


def _growth_table(hull, parts: list) -> list[tuple]:
    """Croissance du diametre apparent, a la geometrie perspective du jeu.

    Le repere est la coque FERMEE ; le cadrage ne bouge pas d'un etat a l'autre,
    sinon on ne comparerait rien (piege releve dans BRIEF-0042-debattement-radial).
    """
    hull_verts, _ = _soup(hull)
    state = _part_state(parts)
    azimuths = [
        (name, math.degrees(math.atan2(pivot.z, pivot.x)))
        for name, pivot, _r, _rad, _local in state
    ]

    rows = []
    for deg in (0.0, 10.0, 20.0, 30.0, OPEN_DEG, 50.0, 60.0, 70.0):
        entry = [deg]
        for yaw in (0.0, 180.0):
            pts = _posed_points(hull_verts, state, deg, 0.0, yaw)
            screen = [p for p in (_project(v) for v, _ in pts) if p is not None]
            entry.append(_diameter(screen))
        pts = _posed_points(hull_verts, state, deg, 0.0, 0.0)
        r_hull = max(math.hypot(v.x, v.z) for v, owner in pts if owner is None)
        r_arms = max(math.hypot(v.x, v.z) for v, owner in pts if owner is not None)
        sectors = [
            (name, _sector_radius(pts, None, az), _sector_radius(pts, name, az))
            for name, az in azimuths
        ]
        entry.append((r_hull, r_arms, sectors))
        rows.append(entry)
    return rows


def _report_growth(rows: list[tuple]) -> None:
    print("--- croissance du diametre apparent (camera de graybox.tscn, 14,87 u) ---")
    base = rows[0][1]
    base180 = rows[0][2]
    for deg, yaw0, yaw180, radii in rows:
        r_hull, r_arms, sectors = radii
        print(
            f"  {deg:5.1f} deg  diam. ecran {yaw0:7.2f} px "
            f"({100.0 * (yaw0 / base - 1.0):+6.2f} %)"
            f" | retourne {yaw180:7.2f} px "
            f"({100.0 * (yaw180 / base180 - 1.0):+6.2f} %)"
            f" | rayon XZ coque fixe {r_hull:.4f} / bras {r_arms:.4f} m"
        )
        # Garde globale (celle du Leech Drone) : la coque fixe ne doit jamais
        # atteindre le rayon des pieces animees.
        if r_arms <= r_hull:
            raise ak.ContractError(
                f"a {deg:.0f} deg, la coque fixe (r={r_hull:.4f}) deborde les bras "
                f"(r={r_arms:.4f}) — c'est le defaut de BRIEF-0042."
            )
        # Garde par bras : chacun doit porter la silhouette DANS SON SECTEUR, sinon
        # une piece pourrait « porter l'enveloppe » a elle seule pendant que les
        # deux autres remuent derriere la coque sans rien changer.
        for name, r_sector_hull, r_sector_part in sectors:
            if r_sector_part <= r_sector_hull:
                raise ak.ContractError(
                    f"a {deg:.0f} deg, {name} (r={r_sector_part:.4f}) ne deborde plus "
                    f"la coque fixe dans son secteur (r={r_sector_hull:.4f})."
                )
    print("  secteur par bras (repos) : " + ", ".join(
        f"{name} {p:.3f} contre coque {h:.3f} m"
        for name, h, p in rows[0][3][2]
    ))
    grown = 100.0 * (rows[4][1] / base - 1.0)
    print(f"  -> a {OPEN_DEG:.0f} deg : {grown:+.2f} % de diametre apparent")
    if grown < GROWTH_FLOOR_PCT:
        print(
            f"  !! SOUS LE PLANCHER DU BRIEF ({GROWTH_FLOOR_PCT:.0f} %) : l'oscillation "
            "restera un signe de vie, pas une lecture d'etat."
        )
        raise ak.ContractError(
            f"croissance du diametre apparent {grown:.2f} % < plancher "
            f"{GROWTH_FLOOR_PCT:.1f} % — l'articulation serait decorative."
        )


def _spread_table(hull, parts: list) -> None:
    """Effet du COULISSEMENT radial optionnel, par-dessus l'ouverture optimale."""
    hull_verts, _ = _soup(hull)
    state = _part_state(parts)
    base = _diameter(
        [
            p
            for p in (
                _project(v) for v, _ in _posed_points(hull_verts, state, 0.0, 0.0, 0.0)
            )
            if p is not None
        ]
    )
    print("--- coulissement radial optionnel, par-dessus l'ouverture optimale ---")
    for spread in (0.0, 0.15, 0.30, 0.50):
        pts = _posed_points(hull_verts, state, OPEN_DEG, spread, 0.0)
        d = _diameter([p for p in (_project(v) for v, _ in pts) if p is not None])
        gap = max(s[3] for s in state) * spread * 1000.0
        print(
            f"  open_spread {spread:.2f} : diam. {d:7.2f} px "
            f"({100.0 * (d / base - 1.0):+6.2f} %)  jour au joint {gap:6.1f} mm"
        )


# ==========================================================================
# Harnais 3 — repartition des materiaux : aire VUE et aire TOTALE
# ==========================================================================


def _collect_triangles(hull, parts: list):
    """(sommets, triangle, materiau, « appartient au projecteur ») en repere Godot."""
    out = []
    for obj in [hull] + [p.obj for p in parts]:
        verts, faces, mats = _soup_with_materials(obj)
        for face, mat in zip(faces, mats):
            pts = [verts[i] for i in face]
            centre = (pts[0] + pts[1] + pts[2]) / 3.0
            near = math.hypot(centre.x, centre.z) <= PROJECTOR_RADIUS
            out.append((pts, mat, near))
    return out


def _total_area_share(tris) -> tuple[list[tuple[str, float]], float]:
    """Part de chaque materiau dans l'aire TOTALE des faces (flancs et dessous compris).

    Le bestiaire presente les coques de trois quarts : une aire de marquage n'a de
    sens qu'avec la vue depuis laquelle on la mesure, d'ou cette seconde mesure.
    """
    areas: dict[int, float] = {}
    emissive_projector = 0.0
    for pts, mat, near in tris:
        area = (pts[1] - pts[0]).cross(pts[2] - pts[0]).length * 0.5
        areas[mat] = areas.get(mat, 0.0) + area
        if near and ak.MATERIAL_ORDER[mat] == "AA_Emissive_Engine":
            emissive_projector += area
    total = sum(areas.values())
    shares = [
        (ak.MATERIAL_ORDER[m], 100.0 * a / total)
        for m, a in sorted(areas.items(), key=lambda kv: -kv[1])
    ]
    return shares, 100.0 * emissive_projector / total


def _seen_area_share(tris, size: int = 420):
    """Part de chaque materiau dans les pixels VUS, z-buffer a la camera du jeu.

    Compter l'aire des triangles surestimerait tout ce qui est cache (dessous des
    coquilles, gorge du puits). Ici on rasterise reellement, avec profondeur : ce qui
    est occulte ne compte pas. C'est la mesure qui arbitre « accent ou livree ».
    """
    screen = []
    for pts, mat, near in tris:
        proj = [_project(p) for p in pts]
        if any(p is None for p in proj):
            continue
        depth = sum((p - CAM_POS).dot(CAM_Z) for p in pts) / 3.0
        screen.append((proj, depth, mat, near))

    xs = [p[0] for proj, _, _, _ in screen for p in proj]
    ys = [p[1] for proj, _, _, _ in screen for p in proj]
    lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)
    span = max(hi_x - lo_x, hi_y - lo_y) * 1.02
    scale = (size - 1) / span

    zbuf = [1e9] * (size * size)
    mbuf = [-1] * (size * size)
    pbuf = [False] * (size * size)
    for proj, depth, mat, near in screen:
        px = [((p[0] - lo_x) * scale, (p[1] - lo_y) * scale) for p in proj]
        x0 = max(0, int(min(p[0] for p in px)))
        x1 = min(size - 1, int(max(p[0] for p in px)) + 1)
        y0 = max(0, int(min(p[1] for p in px)))
        y1 = min(size - 1, int(max(p[1] for p in px)) + 1)
        (ax, ay), (bx, by), (cx, cy) = px
        # ⚠️ COORDONNEES BARYCENTRIQUES EXACTES, et pas la variante heritee du
        # harnais du Leech Drone : celle-ci calculait
        #   w0 = ((by-ay)(cx-sx) - (bx-sx)(cy-ay)) / det
        # qui se developpe en `1 + u.x (AC.y - AB.y) / det` — une fonction qui
        # ne depend meme pas de u.y, donc pas une barycentrique. Elle REJETTE le
        # centre de gravite d'un triangle sur deux (verifie a la main sur
        # a=(0,0) b=(1,0) c=(0,1) : w2 = -0,75) et amputait ici 40 % des pixels
        # de la lentille. Le defaut est silencieux : il rend des pourcentages
        # d'allure normale, seulement faux.
        denom = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(denom) < 1e-9:
            continue
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                sx, sy = x + 0.5, y + 0.5
                w0 = ((by - cy) * (sx - cx) + (cx - bx) * (sy - cy)) / denom
                w1 = ((cy - ay) * (sx - cx) + (ax - cx) * (sy - cy)) / denom
                w2 = 1.0 - w0 - w1
                if w0 < 0.0 or w1 < 0.0 or w2 < 0.0:
                    continue
                idx = y * size + x
                # depth = distance le long de l'axe camera, negative devant :
                # le plus GRAND (moins negatif) est le plus proche.
                if depth > -zbuf[idx]:
                    zbuf[idx] = -depth
                    mbuf[idx] = mat
                    pbuf[idx] = near

    total = sum(1 for m in mbuf if m >= 0)
    counts: dict[int, int] = {}
    projector = 0
    for m, near in zip(mbuf, pbuf):
        if m < 0:
            continue
        counts[m] = counts.get(m, 0) + 1
        if near and ak.MATERIAL_ORDER[m] == "AA_Emissive_Engine":
            projector += 1
    shares = [
        (ak.MATERIAL_ORDER[m], 100.0 * c / total)
        for m, c in sorted(counts.items(), key=lambda kv: -kv[1])
    ]
    return shares, 100.0 * projector / total


def _report_area(hull, parts: list) -> None:
    tris = _collect_triangles(hull, parts)
    seen, seen_projector = _seen_area_share(tris)
    total, total_projector = _total_area_share(tris)
    seen_map = dict(seen)
    total_map = dict(total)
    print("--- repartition des materiaux : aire VUE (z-buffer) et aire TOTALE ---")
    print(f"  {'materiau':<20} {'aire vue':>9} {'aire totale':>12}")
    for name, pct in seen:
        print(f"  {name:<20} {pct:8.2f} % {total_map.get(name, 0.0):10.2f} %")
    for name, pct in total:
        if name not in seen_map:
            print(f"  {name:<20} {'(cache)':>9} {pct:10.2f} %")
    emissive_seen = seen_map.get("AA_Emissive_Engine", 0.0)
    emissive_total = total_map.get("AA_Emissive_Engine", 0.0)
    print(
        f"  -> emissif : {emissive_seen:.2f} % de l'aire vue "
        f"({seen_projector:.2f} % projecteur + {emissive_seen - seen_projector:.2f} % "
        f"reste de la coque) | {emissive_total:.2f} % de l'aire totale "
        f"({total_projector:.2f} % projecteur)"
    )
    if emissive_seen - seen_projector > 3.0:
        raise ak.ContractError(
            f"emissif hors projecteur = {emissive_seen - seen_projector:.2f} % de "
            "l'aire vue > 3 % : ce n'est plus un accent, c'est une livree (brief)."
        )


# ==========================================================================
# Controle du livrable : UV presentes sur 100 % des primitives
# ==========================================================================


def _assert_texcoords(path: str) -> None:
    """Relit le `.glb` PRODUIT et compte `TEXCOORD_0`.

    Trois coques du depot (`needle_scout`, `crescent_interceptor`, `choir_harvester`)
    sont sorties sans UV : l'exporteur n'emet aucun avertissement, la bounding box est
    parfaite, le contrat passe — et aucune feuille de detail (ADR-0011) ne peut plus
    s'y poser. Le defaut est totalement silencieux ; on ne le suppose donc pas absent,
    on le verifie sur le fichier.
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

    Sans cela l'exporteur renonce aux TANGENTES (« tangent space can only be computed
    for tris/quads ») et ADR-0011 devient inoperant. Les n-gons viennent des
    `cap_ring` (culots, bouts de coquille) ; les quads sont gardes tels quels.
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
    # Chanfrein a 1 segment, 6 mm : bien moins que la moitie de la largeur de
    # rainure (22 a 28 mm), sinon `bevel_sharp_edges` mange integralement le lisere
    # et les plaques disparaissent du compte par materiau, sans un mot.
    ak.bevel_sharp_edges(obj, width=0.006, segments=1, angle_deg=33.0)
    _triangulate_ngons(obj)
    # 24 deg : un objet mecanique garde ses facettes ; seuls le tambour et la
    # lentille meritent d'etre fondus.
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


def build_hull() -> object:
    bm = bmesh.new()
    build_body(bm)
    build_projector(bm)
    return ak.new_object("ShieldCarrier_Hull", bm)


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)

    hull = build_hull()
    parts = [
        build_shell(1, ak.PORT),
        build_shell(2, ak.STARBOARD),
        build_aft_cradle(3),
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
            f"  {obj.name:<20} x[{o_lo.x:+.4f} {o_hi.x:+.4f}] "
            f"y[{o_lo.y:+.4f} {o_hi.y:+.4f}] z[{o_lo.z:+.4f} {o_hi.z:+.4f}] "
            f"{len(obj.data.polygons)} faces"
        )
    print(
        f"  TOTAL                x[{lo.x:+.4f} {hi.x:+.4f}] y[{lo.y:+.4f} {hi.y:+.4f}] "
        f"z[{lo.z:+.4f} {hi.z:+.4f}]  ->  {hi.x - lo.x:.4f} x {hi.y - lo.y:.4f} "
        f"x {hi.z - lo.z:.4f} m"
    )
    e_shell = TIP_X - JOINT_X
    h_shell = e_shell * _TAN_OPEN
    e_aft = AFT_TIP_Y - AFT_HINGE_Y
    h_aft = e_aft * _TAN_OPEN
    for label, e, h, r in (
        ("coquilles", e_shell, h_shell, TIP_X),
        ("berceau arriere", e_aft, h_aft, AFT_TIP_Y),
    ):
        gain = math.hypot(e, h) - e
        print(
            f"  {label:<16} : debord e={e:.4f} m, plongee h={h:.4f} m, "
            f"gain de rayon {gain * 1000:.1f} mm ({100.0 * gain / r:.2f} %)"
        )

    _report_travel(_travel_table(hull, parts))
    _report_growth(_growth_table(hull, parts))
    _spread_table(hull, parts)
    _report_area(hull, parts)

    ak.export_hull(hull, build_attach_points(), OUTPUT, CONTRACT, parts=parts)
    _assert_texcoords(OUTPUT)


if __name__ == "__main__":
    main()
