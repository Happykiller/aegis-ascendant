"""build_choir_harvester.py — coque 3D du Choir Harvester, mini-boss (BRIEF-0039).

    ./scripts/build-hull.sh choir_harvester        # JAMAIS un `blender45` nu : -t 1

Produit `assets/imported/models/bosses/choir_harvester.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (aucun alea non seede) et s'auto-valide : `ak.export_hull()`
relit le `.glb` produit et echoue bruyamment si la bounding box, le budget de
triangles, les materiaux, le centrage du pivot ou les points d'attache sortent
du contrat.

Reference de design : `assets/reference/concepts/choir_harvester_concept_sheet.png`
(corps-iris discoide, cinq petales blindes sur un noyau magenta, une faux a bras
segmente et lame en croissant, une griffe a trois tetes a oeil magenta, un canon a
fut segmente et bouches multiples).

Repere d'auteur (ADR-0008) : face menacante -Y, dessus +Z, **babord +X**
(cf. l'en-tete d'aegis_kit : le signe de X est contre-intuitif).


CE QUE BRIEF-0039 CHANGE — des pieces qui peuvent enfin BOUGER
==============================================================
La version precedente livrait bien des objets distincts, mais tous a la
transformation identite : leur origine etait celle du modele. Une piece pareille
tourne autour du centre du boss, pas autour de sa charniere ; les marqueurs
`Hinge_*` livres a cote ne servaient a rien, Godot ne sachant pas s'en servir sans
reparenter a la main. Tout ce qui bouge passe desormais par `ak.moving_part()`,
qui pose l'origine SUR le pivot et accepte un `parent` (chaines articulees).

Contrat de noms (le code du combat est ecrit contre lui, `harvester_combat.gd`) :

    Arm_Scythe -> Scythe_Mid -> Scythe_Blade      (chaine : epaule, coude, poignet)
    Arm_Claw   -> Claw_Head_1..3                  (epaule, puis le cou de chaque tete)
    Arm_Cannon -> Cannon_Barrel                   (rotule, puis l'axe de recul)
    Petal_01..05                                  (leur charniere)
    Core                                          (statique, mais noeud a part)


LE PLAN VIENT DE LA MECANIQUE, PAS SEULEMENT DE LA PLANCHE
==========================================================
`harvester_combat.gd` ne pose pas des angles quelconques : il ecrit, en repere
Godot, `root.rotation.x` (le repli a -70 deg d'un appendice detruit), la visee en
`rotation.y`, et le recul du fut en `position.z`. Traduit en repere d'auteur
(x_Godot = -x_auteur, y_Godot = z_auteur, z_Godot = y_auteur) :

  * le repli et l'estoc tournent autour d'un axe PARALLELE A X passant par le
    pivot — donc **x est conserve** ;
  * le recul du fut vaut +0,25 m en Y d'auteur (vers l'arriere) : le canon TIRE
    donc vers l'avant (-Y), et sa bouche doit se trouver du cote de la face
    menacante, sinon le faisceau naitrait derriere le boss.

Consequence directe sur le plan, et c'est LA raison pour laquelle le module
arriere de la version precedente ne pouvait pas devenir un canon a sa place :
un appendice qui surplombe la carapace traverse le corps des qu'il pique de
70 deg, puisque la rotation conserve son x. Les trois appendices sont donc
montes de facon a piquer dans le VIDE :

  * la faux sur le flanc babord, toute sa geometrie a |x| >= 1,74 (au-dela de la
    carapace) ou, pour le crochet de lame, a un rayon superieur a celui de la
    carapace vue depuis l'epaule ;
  * la griffe sur le flanc tribord, tendue vers l'avant : son repli l'emmene
    devant le bord avant du disque ;
  * le canon en avant du disque, legerement decale a babord (asymetrie de la
    charte, et la place qu'il faut a la griffe en fin de balayage) : tout ce qui
    pique tombe devant y = -2,30, ou il n'y a rien.

La propulsion, elle, ne bouge pas : elle est **dans la coque** (poupe segmentee,
trois tuyeres magenta, `Engine_C`). Ce n'est pas un quatrieme appendice — elle
n'a ni pivot, ni nom au contrat, ni vie propre.

Chaque debattement est REMESURE a chaque build sur le maillage livre
(`_clearance_table()`, plus bas) : la lecon la plus chere du projet est qu'un
contrat de bounding box valide une pose fixe et ne voit RIEN d'un defaut
d'animation (`.claude/resources/pratique-detail-en-fraction-de-corde.md`).
"""

from __future__ import annotations

import math
import os
import sys

import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402  (doit suivre l'ajout au sys.path)

# ==========================================================================
# Contrat (ADR-0008, tableau des dimensions imposees)
# ==========================================================================

CONTRACT = ak.HullContract(
    name="Choir Harvester",
    width_x=4.55,       # Godot X
    length_z=7.00,      # Godot Z
    max_height_y=1.60,  # Godot Y — plafond de lisibilite en vue de dessus
    tri_budget=25_000,
    required_materials=ak.MATERIAL_ORDER,  # les 7 : la planche les utilise tous
    required_attach_points=(
        "Core_Center",
        "Muzzle_Claw_1",
        "Muzzle_Claw_2",
        "Muzzle_Claw_3",
        "Muzzle_Cannon",
        "Engine_C",
    ),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/bosses/choir_harvester.glb")

SEED = 40507  # graine unique du Choir Harvester (determinisme des greebles)

#: 3,500 — la bouche du canon porte le min Y, le culot de poupe le max Y. La
#: largeur, elle, est portee par le dos de lame (+X) et la serre externe (-X).
HALF_L = CONTRACT.length_z / 2.0

# ==========================================================================
# Corps-iris : carapace ovoide, puits d'iris circulaire
# ==========================================================================

CARA_AX = 1.62      # demi-largeur du disque blinde
CARA_AY = 2.05      # demi-longueur du disque blinde
IRIS_R = 0.92       # rayon du puits d'iris (il loge noyau + petales)
N_SEG = 36          # segments angulaires du disque (multiple de 12 : les rings)

#: Stations radiales : t=0 sur la levre du puits, t=1 sur le bord de carapace.
T_RINGS = (0.00, 0.16, 0.34, 0.55, 0.72, 0.86, 0.95, 1.00)
Z_TOP = (0.36, 0.44, 0.47, 0.44, 0.36, 0.25, 0.14, 0.04)
Z_BOT = (-0.34, -0.44, -0.48, -0.45, -0.38, -0.26, -0.14, -0.04)

#: Puits d'iris : (rayon, z) du haut de la levre jusqu'au plancher.
WELL = ((IRIS_R, 0.36), (0.86, 0.15), (0.82, -0.02), (0.58, -0.07))
WELL_MATS = ("AA_Greeble", "AA_Emissive_Engine", "AA_Greeble")

RIM_BLOCKS = 24     # cerclage exterieur segmente
#: Blocs arases (indices) : le secteur avant-tribord que la griffe balaie.
RIM_FLUSH = (15, 16, 17)
RIM_SPIKES = (38.0, 92.0, 148.0, 214.0, 322.0)  # ergots ivoire (deg, asymetriques)

# ==========================================================================
# Poupe : bloc propulsif fondu dans la coque (fixe — ce n'est PAS un appendice).
# Il porte le max Y du modele et le point d'attache `Engine_C`.
# ==========================================================================

#: (y, demi-largeur, z_haut, z_bas) — le bloc sort de sous le disque et s'affine.
STERN: tuple[tuple[float, float, float, float], ...] = (
    (1.30, 0.76, 0.24, -0.30),
    (1.86, 0.72, 0.27, -0.33),
    (2.34, 0.63, 0.25, -0.31),
    (2.80, 0.52, 0.21, -0.27),
    (3.18, 0.39, 0.15, -0.21),
    (HALF_L, 0.25, 0.07, -0.13),   # culot : max Y du modele
)
STERN_MATS = ("AA_Hull", "AA_Hull", "AA_Panel", "AA_Greeble", "AA_Greeble")

#: Tuyeres : (x, z, rayon). La centrale est la principale.
STERN_NOZZLES = ((0.0, -0.02, 0.170), (0.40, 0.00, 0.105), (-0.40, 0.00, 0.105))
NOZZLE_Y0 = 3.02    # fond de chambre
NOZZLE_Y1 = 3.44    # plan de sortie
ENGINE_Y = 3.46     # origine de la trainee

# ==========================================================================
# Noyau et iris (le point faible : ce que le joueur doit viser)
# ==========================================================================

#: (rayon, z) du noyau, du collier de base jusqu'a l'apex.
CORE_RINGS = ((0.60, -0.08), (0.56, 0.04), (0.48, 0.17), (0.34, 0.28), (0.17, 0.36))
CORE_APEX_Z = 0.42
CORE_SEG = 24
CORE_MATS = ("AA_Greeble", "AA_Glass", "AA_Emissive_Engine", "AA_Emissive_Engine")

PETAL_COUNT = 5
PETAL_ANGLES = tuple(18.0 + 72.0 * i for i in range(PETAL_COUNT))
#: Charniere : au-dessus de la levre du puits, sur un berceau ivoire. Elle est
#: POSEE SUR la carapace et non noyee dedans — un petale dont la racine est
#: enterree ne peut pas s'ouvrir sans raboter le pont.
PETAL_HINGE_R = 1.00
PETAL_HINGE_Z = 0.55
PETAL_TILT = 12.0         # deg — iris ferme : le magenta ne fuse que par l'oeil
#: Longueur calibree pour que les cinq pointes laissent un oeil magenta ouvert au
#: centre (rayon ~0,16 m) : c'est par la que le noyau se voit iris ferme, et c'est
#: ce qui fait du point faible une cible evidente.
PETAL_LEN = 0.86
#: (s le long du petale, demi-largeur, demi-epaisseur). Les largeurs sont bornees
#: par le pas de 72 deg de l'iris : au-dela, les petales se mordent au lieu de se
#: cotoyer. L'ouverture, elle, les ECARTE (le rayon de chaque section croit avec
#: l'angle) : la pose fermee est donc le cas critique.
PETAL_SECTIONS = (
    (0.00, 0.355, 0.048),
    (0.15, 0.385, 0.045),   # epaulement, le plus large
    (0.36, 0.340, 0.038),
    (0.55, 0.265, 0.030),
    (0.68, 0.170, 0.022),
)
PETAL_RIDGE = 0.045       # arete centrale bombee sur le dos du petale
#: Repartition transversale des sommets d'une section (fraction de demi-largeur).
PETAL_CROSS = (-1.0, -0.88, -0.34, 0.0, 0.34, 0.88, 1.0)
PETAL_BRACKET_Z = 0.448   # sommet du berceau de charniere (sous le petale)

# ==========================================================================
# Faux — flanc babord. Trois maillons, trois pivots (epaule, coude, poignet).
# ==========================================================================

#: Emplanture : le mat qui sort du flanc et porte la rotule d'epaule. Le pivot est
#: pousse assez LOIN du bord (|x| = 1,99 contre 1,76 pour le cerclage) pour que le
#: bras, dont la rotation conserve x, pique de 70 deg sans raboter le mat ni la
#: jante : c'est la mesure de degagement qui a fixe ce chiffre, pas l'oeil.
SCYTHE_PIVOT = (1.99, 0.55, 0.32)
SCYTHE_MAST_Y = 0.55
SCYTHE_JOINT_R = 0.175

#: Bras superieur : de l'epaule au coude.
SCYTHE_UPPER = (
    (1.99, 0.55, 0.32),
    (2.02, 0.16, 0.41),
    (2.04, -0.24, 0.48),
)
SCYTHE_UPPER_R = (0.175, 0.160, 0.148)

#: Avant-bras : du coude au poignet.
SCYTHE_MID = (
    (2.04, -0.24, 0.48),
    (2.07, -0.66, 0.52),
    (2.08, -1.08, 0.53),
    (2.05, -1.44, 0.51),
)
SCYTHE_MID_R = (0.148, 0.138, 0.128, 0.120)

#: Lame en croissant : ces points sont l'ame de la lame ; le dos deborde de
#: `BLADE_BACK` vers l'exterieur (c'est lui qui porte l'extreme +X du modele).
SCYTHE_BLADE = (
    (2.05, -1.44, 0.51),
    (2.14, -1.86, 0.49),
    (2.175, -2.28, 0.46),
    (2.09, -2.66, 0.43),
    (1.88, -2.96, 0.40),
    (1.55, -3.14, 0.38),
    (1.20, -3.14, 0.36),
)
BLADE_BACK = (0.055, 0.085, 0.100, 0.085, 0.060, 0.040, 0.020)
BLADE_EDGE = (0.150, 0.300, 0.400, 0.420, 0.380, 0.280, 0.090)
BLADE_TH = (0.120, 0.105, 0.092, 0.082, 0.070, 0.052, 0.026)

# ==========================================================================
# Griffe a trois tetes — flanc tribord, tendue vers l'avant.
# ==========================================================================

#: L'epaule est POUSSEE VERS L'AVANT du flanc, et le bras raccourci : le combat
#: balaie la racine de +/-32 deg, et 32 deg au bout d'un bras de 2,2 m emmenent la
#: tete la plus interne en travers du bec, sur le canon. Bras court = balayage
#: lisible ET degage. C'est la mesure qui a impose ce plan, pas la planche.
CLAW_PIVOT = (-1.66, -1.45, 0.16)
CLAW_MAST_Y = -1.45
CLAW_JOINT_R = 0.165

CLAW_ARM = (
    (-1.66, -1.45, 0.16),
    (-1.66, -1.79, 0.11),
    (-1.62, -2.12, 0.06),
)
CLAW_ARM_R = (0.165, 0.150, 0.138)

#: Fourche : les trois cous, en triangle (c'est la lecture du panneau de detail —
#: trois tetes a distances differentes, pas un eventail plat).
#: ⚠️ ORDRE : la tete 1 est la plus INTERNE. `harvester_combat` fait tourner la
#: tete `i` de `converge * (i - 1)`, soit -18 deg pour la 1 et +18 deg pour la 3 ;
#: avec la 1 a l'interieur, ces deux angles ECARTENT les tetes de la coque et du
#: canon, et leurs lignes de tir se croisent — c'est bien une convergence. L'ordre
#: inverse envoyait la tete 3 dans le canon des le premier balayage (mesure).
#: (cou, direction de la tete dans le plan XY)
#: Les cous sont DERIVES des tetes (position voulue moins la longueur du cou) et
#: non l'inverse : ce sont les tetes qui doivent s'ecarter entre elles, tenir dans
#: la largeur et degager le canon.
CLAW_NECKS = (
    ((-1.298, -2.319, 0.06), (0.30, -0.954)),   # 1 — interne
    ((-1.584, -2.640, 0.04), (-0.02, -1.000)),  # 2 — mediane, la plus avancee
    ((-1.888, -2.302, 0.02), (-0.32, -0.947)),  # 3 — externe : porte le -X
)
CLAW_STALK = 0.42    # longueur du cou a la tete
CLAW_HEAD_R = 0.120
TALON_LEN = 0.21
TALON_ROOT = 0.62    # facteur d'epaisseur a la base de la serre
TALON_TIP = 0.30     # ... et a la pointe
TALON_SPREAD = (-32.0, 0.0, 32.0)
EYE_R = 0.105        # l'oeil est une bouche de tir : il doit se voir de dessus

# ==========================================================================
# Canon — sous le bec avant, dans l'axe. Il TIRE VERS L'AVANT (-Y) : c'est le
# signe du recul (`position.z = +0,25` cote Godot) qui l'impose.
# ==========================================================================

#: Le canon est DECALE A BABORD. Deux raisons, dans cet ordre : la griffe, en fin
#: de balayage, passe devant le bec et il lui faut la place (mesure) ; et
#: l'asymetrie est la signature du Choeur Nul (charte §4). Un canon pile dans l'axe
#: aurait aussi coupe l'iris en deux dans la vue de dessus.
CANNON_X = 0.22
CANNON_Z = 0.02
CANNON_PIVOT = (CANNON_X, -2.30, CANNON_Z)
#: Rotule spherique : une calotte centree sur le pivot est invariante par
#: rotation. C'est ce qui permet au canon de piquer de 70 deg sans raboter le col.
CANNON_BALL_R = 0.20
CANNON_SOCKET = (0.26, 0.42)     # rayons interne et externe de la calotte
CANNON_SOCKET_DEG = (45.0, 72.0)  # ouverture angulaire depuis l'axe de tir
#: Manchon de glissement du fut (solidaire de `Arm_Cannon`).
SLEEVE_Y = (-2.62, -2.98)
SLEEVE_R = (0.30, 0.44)
SLEEVE_STRUTS = (30.0, 150.0, 270.0)
#: Col fixe (coque) : mince, sinon la calotte le raboterait au repli.
CANNON_NECK = (
    (CANNON_X, -1.86, CANNON_Z - 0.04),
    (CANNON_X, -2.10, CANNON_Z - 0.02),
    (CANNON_X, -2.28, CANNON_Z),
)
CANNON_NECK_R = (0.24, 0.20, 0.185)

#: Fut : (y, rayon, materiau). Le pole arriere ferme la culasse.
BARREL_PROFILE = (
    (-2.85, 0.000, "AA_Greeble"),
    (-2.86, 0.225, "AA_Greeble"),
    (-2.94, 0.245, "AA_Panel"),
    (-3.02, 0.228, "AA_Greeble"),
    (-3.06, 0.248, "AA_Panel"),
    (-3.16, 0.232, "AA_Greeble"),
    (-3.20, 0.250, "AA_Trim"),
    (-3.27, 0.222, "AA_Panel"),
    (-3.36, 0.212, "AA_Greeble"),
    (-3.40, 0.236, "AA_Trim"),
    (-3.475, 0.198, "AA_Greeble"),
    (-HALF_L, 0.150, "AA_Emissive_Engine"),   # levre de bouche : min Y du modele
    (-3.47, 0.088, "AA_Emissive_Engine"),
    (-3.44, 0.000, "AA_Emissive_Engine"),
)
BARREL_SEG = 18
#: Bouches secondaires : (azimut deg) autour du fut.
BARREL_MOUTHS = (40.0, 160.0, 280.0)
MUZZLE_Y = -3.56    # point d'attache : juste devant la levre

# ==========================================================================
# Helpers geometriques locaux (au-dessus du kit, jamais a la place du kit)
# ==========================================================================


def _verts_of(faces: list) -> list:
    """Sommets uniques d'un paquet de faces."""
    verts = {v for f in faces if f is not None and f.is_valid for v in f.verts}
    return list(verts)


def oriented_box(bm, center, size, rot, material: str) -> list:
    """Boite orientee : `ak.add_box` ne sait faire qu'aligne sur les axes."""
    faces = ak.add_box(bm, (0.0, 0.0, 0.0), size, material)
    verts = _verts_of(faces)
    if rot is not None:
        bmesh.ops.rotate(bm, cent=(0.0, 0.0, 0.0), matrix=rot, verts=verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=verts)
    return faces


def _align_y(direction: Vector) -> Matrix:
    """Rotation qui amene l'axe local +Y d'une boite sur `direction`.

    `rotation_difference` prend l'arc le plus court : le roulis residuel est donc
    entierement determine par `direction` — reproductible.
    """
    return Vector((0.0, 1.0, 0.0)).rotation_difference(direction.normalized()).to_matrix()


def seg_box(bm, a, b, half_w: float, half_h: float, material: str) -> list:
    """Vertebre : boite tendue du point `a` au point `b`."""
    va, vb = Vector(a), Vector(b)
    delta = vb - va
    length = delta.length
    if length < 1e-6:
        return []
    return oriented_box(
        bm,
        (va + vb) * 0.5,
        (2.0 * half_w, length, 2.0 * half_h),
        _align_y(delta),
        material,
    )


def knuckle(bm, center, radius: float, material: str) -> list:
    """Articulation : icosphere subdivisee une fois (80 faces, angles < 30 deg,
    donc epargnee par le biseau — c'est ce qui la rend abordable)."""
    res = bmesh.ops.create_icosphere(
        bm,
        subdivisions=1,
        radius=radius,
        matrix=Matrix.Translation(Vector(center)),
    )
    verts = res["verts"]
    idx = ak.mat_index(material)
    faces = []
    for face in {f for v in verts for f in v.link_faces}:
        if all(v in verts for v in face.verts):
            face.material_index = idx
            faces.append(face)
    return faces


def limb(
    bm,
    path: tuple,
    radii: tuple,
    material: str,
    joint_material: str = "AA_Greeble",
    glow_from: int = 1,
    joints: bool = True,
    root_gap: float = 0.0,
) -> None:
    """Bras articule : vertebres + articulations + veines magenta.

    Le rendu segmente de la planche vient de la geometrie (une boite par vertebre,
    une sphere par articulation), pas d'une texture.

    `root_gap` : recul supplementaire de la PREMIERE vertebre. Une vertebre qui
    part du pivot balaie un cylindre autour de lui et rabote le mat qui porte la
    rotule — mesure a l'appui. La degager de 20 cm rend le repli propre, et lit
    comme un vrai joint (la planche montre des segments separes, pas un tube).
    """
    for i in range(len(path) - 1):
        a, b = Vector(path[i]), Vector(path[i + 1])
        rad = (radii[i] + radii[i + 1]) * 0.5
        d = b - a
        length = d.length
        if length < 1e-6:
            continue
        u = d / length
        # la vertebre est legerement retractee : l'articulation la deborde
        gap = rad * 0.35 + (root_gap if i == 0 else 0.0)
        seg_box(bm, a + u * gap, b - u * rad * 0.35, rad * 0.86, rad * 0.80, material)
        if i >= glow_from:
            side = u.cross(Vector((0.0, 0.0, 1.0)))
            if side.length > 1e-6:
                side.normalize()
                mid = (a + b) * 0.5
                seg_box(
                    bm,
                    mid + side * rad * 0.80 - u * length * 0.22,
                    mid + side * rad * 0.80 + u * length * 0.22,
                    0.018,
                    rad * 0.34,
                    "AA_Emissive_Engine",
                )
    if joints:
        for i, point in enumerate(path):
            knuckle(bm, point, radii[i] * 0.92, joint_material)


def sweep_rect(bm, sections: tuple, materials: tuple, cap: str = "AA_Greeble") -> list:
    """Longeron : chaine de sections rectangulaires (y, hw, z_hi, z_lo) bridees."""
    rings = [
        ak.add_ring(bm, [(hw, y, z_hi), (-hw, y, z_hi), (-hw, y, z_lo), (hw, y, z_lo)])
        for y, hw, z_hi, z_lo in sections
    ]
    bands = [
        ak.bridge_rings(bm, rings[i], rings[i + 1], materials[i])
        for i in range(len(rings) - 1)
    ]
    ak.cap_ring(bm, list(reversed(rings[0])), cap)
    ak.cap_ring(bm, rings[-1], materials[-1])
    return bands


def polar_ring(bm, radius: float, z: float, segments: int, phase: float = 0.0) -> list:
    """Boucle horizontale (autour de Z) : la primitive du disque et du noyau."""
    return ak.add_ring(
        bm,
        [
            (
                radius * math.cos(2.0 * math.pi * i / segments + phase),
                radius * math.sin(2.0 * math.pi * i / segments + phase),
                z,
            )
            for i in range(segments)
        ],
    )


def ell_radius(theta: float) -> float:
    """Rayon de l'ellipse de carapace a l'angle `theta`."""
    c, s = math.cos(theta), math.sin(theta)
    return 1.0 / math.sqrt((c / CARA_AX) ** 2 + (s / CARA_AY) ** 2)


def ell_x(y: float) -> float:
    """Demi-largeur de la carapace a la station `y` (0 hors du disque).

    Sert a poser les emplantures EN FRACTION DE LA COQUE et non en coordonnee
    absolue (`.claude/resources/pratique-detail-en-fraction-de-corde.md`) : le jour
    ou l'ovoide change, les mats suivent au lieu de flotter.
    """
    k = 1.0 - (y / CARA_AY) ** 2
    return CARA_AX * math.sqrt(k) if k > 0.0 else 0.0


def cara_xy(t: float, theta: float) -> tuple[float, float]:
    """Point de la carapace : `t`=0 sur la levre du puits, `t`=1 sur le bord."""
    r = IRIS_R + t * (ell_radius(theta) - IRIS_R)
    return (r * math.cos(theta), r * math.sin(theta))


def lerp_z(table: tuple, t: float) -> float:
    """Interpolation lineaire de `table` (parallele a `T_RINGS`) en `t`."""
    for i in range(len(T_RINGS) - 1):
        t0, t1 = T_RINGS[i], T_RINGS[i + 1]
        if t0 <= t <= t1:
            k = (t - t0) / (t1 - t0)
            return table[i] + (table[i + 1] - table[i]) * k
    return table[-1]


def spherical_shell(
    bm,
    center: Vector,
    axis: Vector,
    radii: tuple[float, float],
    deg: tuple[float, float],
    segments: int,
    steps: int,
    mats: tuple[str, str],
) -> None:
    """Calotte spherique creuse, centree sur `center`, ouverte autour de `axis`.

    Sert la rotule du canon. Une calotte centree sur le pivot est INVARIANTE par
    rotation : c'est ce qui autorise 70 deg de repli sans que la piece mobile
    rabote le col fixe qu'elle enveloppe. Le detour geometrique est le prix de
    l'articulation.
    """
    axis = axis.normalized()
    side = axis.orthogonal().normalized()
    other = axis.cross(side).normalized()

    def ring(radius: float, angle: float) -> list:
        a = math.radians(angle)
        along = axis * (radius * math.cos(a))
        rad = radius * math.sin(a)
        return ak.add_ring(
            bm,
            [
                tuple(
                    center
                    + along
                    + (side * math.cos(2.0 * math.pi * s / segments)
                       + other * math.sin(2.0 * math.pi * s / segments)) * rad
                )
                for s in range(segments)
            ],
        )

    angles = [deg[0] + (deg[1] - deg[0]) * i / steps for i in range(steps + 1)]
    inner = [ring(radii[0], a) for a in angles]
    outer = [ring(radii[1], a) for a in angles]
    for i in range(steps):
        ak.bridge_rings(bm, inner[i + 1], inner[i], mats[0])
        ak.bridge_rings(bm, outer[i], outer[i + 1], mats[1])
    ak.bridge_rings(bm, inner[0], outer[0], mats[1])
    ak.bridge_rings(bm, outer[-1], inner[-1], mats[1])


def tube(
    bm,
    a: float,
    b: float,
    radii: tuple[float, float],
    segments: int,
    mats: tuple[str, str],
    center: tuple[float, float] = (0.0, 0.0),
) -> None:
    """Manchon creux d'axe Y, ouvert aux deux bouts (le fut coulisse dedans)."""
    rings = {}
    for y in (a, b):
        for k, r in enumerate(radii):
            rings[(y, k)] = ak.add_ring(
                bm,
                [
                    (
                        center[0] + r * math.cos(2.0 * math.pi * s / segments),
                        y,
                        center[1] + r * math.sin(2.0 * math.pi * s / segments),
                    )
                    for s in range(segments)
                ],
            )
    ak.bridge_rings(bm, rings[(a, 1)], rings[(b, 1)], mats[1])   # peau externe
    ak.bridge_rings(bm, rings[(b, 0)], rings[(a, 0)], mats[0])   # alesage
    ak.bridge_rings(bm, rings[(a, 0)], rings[(a, 1)], mats[1])   # couronne avant
    ak.bridge_rings(bm, rings[(b, 1)], rings[(b, 0)], mats[1])   # couronne arriere


# ==========================================================================
# Coque : carapace, poupe propulsive, emplantures des trois appendices
# ==========================================================================


def _mast(bm, side: float, y: float, out_x: float, z: float, radius: float) -> None:
    """Emplanture d'appendice : le mat qui sort du flanc et porte la rotule.

    `out_x` est un ABSOLU signe deja calcule sur `ell_x(y)` par l'appelant : le mat
    part de la peau du disque, il ne flotte pas a cote.

    ⚠️ Le mat est MINCE sur ses 30 derniers centimetres. Ce n'est pas un choix de
    style : la piece mobile tourne autour du pivot, donc elle balaie une sphere
    centree dessus. Tout ce que le mat laisse depasser au-dela du rayon de la
    rotule se fait raboter au premier repli — et la premiere version, un simple
    longeron d'epaisseur constante, se faisait mordre par le bras a -70 deg.
    """
    # Le mat est HORIZONTAL et son axe passe par le pivot : ainsi la matiere qui
    # subsiste pres de la rotule est un simple pion centre sur l'axe de rotation,
    # et non un longeron oblique dont le coin vient croiser le balayage du bras.
    root = Vector((side * (ell_x(y) - 0.34), y, z))
    tip = Vector((out_x, y, z))
    waist = root + (tip - root) * 0.42
    seg_box(bm, root, waist, radius * 1.25, radius * 1.05, "AA_Panel")
    seg_box(bm, waist, tip, radius * 0.48, radius * 0.44, "AA_Greeble")
    seg_box(
        bm,
        root + (tip - root) * 0.10 + Vector((0.0, 0.0, radius * 1.05)),
        waist + Vector((0.0, 0.0, radius * 1.02)),
        0.030,
        0.016,
        "AA_Emissive_Engine",
    )
    knuckle(bm, tip, radius * 0.92, "AA_Greeble")


def build_hull() -> object:
    bm = bmesh.new()
    thetas = [2.0 * math.pi * j / N_SEG for j in range(N_SEG)]

    # --- carapace : deux nappes polaires (dessus, dessous) -----------------
    top_rings = [
        ak.add_ring(bm, [(*cara_xy(t, th), Z_TOP[k]) for th in thetas])
        for k, t in enumerate(T_RINGS)
    ]
    bot_rings = [
        ak.add_ring(bm, [(*cara_xy(t, th), Z_BOT[k]) for th in thetas])
        for k, t in enumerate(T_RINGS)
    ]
    # fond de plaque anthracite tres sombre : ce sont les joints entre plaques,
    # les plaques elles-memes seront extrudees par-dessus (inset_panel).
    top_bands = [
        ak.bridge_rings(bm, top_rings[k], top_rings[k + 1], "AA_Greeble")
        for k in range(len(T_RINGS) - 1)
    ]
    bot_bands = [
        ak.bridge_rings(bm, bot_rings[k], bot_rings[k + 1], "AA_Greeble")
        for k in range(len(T_RINGS) - 1)
    ]

    # --- puits d'iris : la levre descend vers le plancher, anneau magenta ---
    well_rings = [top_rings[0]] + [polar_ring(bm, r, z, N_SEG) for r, z in WELL[1:]]
    for i in range(len(well_rings) - 1):
        ak.bridge_rings(bm, well_rings[i], well_rings[i + 1], WELL_MATS[i])
    floor = bm.verts.new((0.0, 0.0, -0.09))
    ak.fan_to_point(bm, well_rings[-1], floor, "AA_Greeble")

    # --- ventre ferme -------------------------------------------------------
    belly = bm.verts.new((0.0, 0.0, -0.38))
    ak.fan_to_point(bm, bot_rings[0], belly, "AA_Greeble")

    # --- plaques de carapace : couronne (6 secteurs) puis anneau externe ----
    for s in range(6):
        cols = range(6 * s, 6 * s + 5)
        crown = [top_bands[k][j] for k in (1, 2, 3, 4) for j in cols]
        ak.inset_panel(bm, crown, "AA_Hull", thickness=0.030, depth=0.014)
    for s in range(12):
        cols = range(3 * s, 3 * s + 2)
        mat = "AA_Panel" if s % 2 == 0 else "AA_Hull"
        outer = [top_bands[k][j] for k in (5, 6) for j in cols]
        ak.inset_panel(bm, outer, mat, thickness=0.022, depth=0.010)
    # marquage vert maladif (usage tres limite, charte) sur une plaque de dos
    ak.inset_panel(
        bm,
        [top_bands[k][j] for k in (2, 3) for j in (19, 20)],
        "AA_Marking_Red",
        thickness=0.018,
        depth=0.006,
    )
    # dessous : quelques plaques violettes, le reste reste sombre
    for s in range(4):
        cols = range(9 * s + 1, 9 * s + 7)
        ak.inset_panel(
            bm,
            [bot_bands[k][j] for k in (2, 3, 4) for j in cols],
            "AA_Panel",
            thickness=0.030,
            depth=0.012,
        )

    # --- lignes d'energie magenta dans les interstices ----------------------
    # Fines et confinees a la couronne : tracees plus larges et jusqu'au bord,
    # elles transformaient le disque en roue a rayons et volaient la vedette a
    # l'iris — or c'est l'iris, et lui seul, que le joueur doit voir en premier.
    for s in range(6):
        theta = 2.0 * math.pi * (6 * s + 5.5) / N_SEG
        pts = []
        for t in (0.08, 0.30, 0.52, 0.70):
            x, y = cara_xy(t, theta)
            pts.append(Vector((x, y, lerp_z(Z_TOP, t) + 0.014)))
        for i in range(len(pts) - 1):
            seg_box(bm, pts[i], pts[i + 1], 0.016, 0.010, "AA_Emissive_Engine")

    # --- cerclage exterieur segmente ---------------------------------------
    # Les blocs de `RIM_FLUSH` sont ARASES : c'est le secteur que la griffe balaie
    # en fin de visee. Un cerclage de hauteur constante lui coutait 30 mm de
    # degagement (mesure) ; arase, il en rend 40 et se lit comme une echancrure de
    # service — la planche montre justement un anneau irregulier.
    for i in range(RIM_BLOCKS):
        theta = 2.0 * math.pi * i / RIM_BLOCKS
        px, py = CARA_AX * math.cos(theta), CARA_AY * math.sin(theta)
        tx, ty = -CARA_AX * math.sin(theta), CARA_AY * math.cos(theta)
        psi = math.atan2(ty, tx)
        nrm = Vector((math.sin(psi), -math.cos(psi), 0.0))
        flush = i in RIM_FLUSH
        oriented_box(
            bm,
            Vector((px, py, 0.0)) + nrm * (-0.060 if flush else 0.024),
            (0.210, 0.300, 0.150) if flush else (0.230, 0.380, 0.185),
            Matrix.Rotation(psi - math.pi / 2.0, 3, "Z"),
            "AA_Panel" if i % 2 == 0 else "AA_Greeble",
        )
    # anneau interne de tenons ivoire (deuxieme cercle de la planche)
    for i in range(12):
        theta = 2.0 * math.pi * (i + 0.5) / 12.0
        x, y = cara_xy(0.62, theta)
        oriented_box(
            bm,
            (x, y, lerp_z(Z_TOP, 0.62) + 0.028),
            (0.105, 0.180, 0.066),
            Matrix.Rotation(theta + math.pi / 2.0, 3, "Z"),
            "AA_Trim",
        )
    # ergots ivoire sur le bord (asymetriques : pas un cercle regulier)
    for deg in RIM_SPIKES:
        theta = math.radians(deg)
        px, py = CARA_AX * math.cos(theta), CARA_AY * math.sin(theta)
        nrm = Vector((px / CARA_AX**2, py / CARA_AY**2, 0.0)).normalized()
        base = Vector((px, py, 0.0))
        seg_box(bm, base - nrm * 0.05, base + nrm * 0.11, 0.100, 0.052, "AA_Trim")
        seg_box(bm, base + nrm * 0.11, base + nrm * 0.22, 0.038, 0.021, "AA_Trim")

    # --- berceaux de charniere des petales ---------------------------------
    # Ils remplissent le jeu sous la racine du petale SANS le toucher : c'est ce
    # qui rend l'iris ouvrable (une charniere noyee dans le pont rabote le pont).
    for deg in PETAL_ANGLES:
        theta = math.radians(deg)
        radial = Vector((math.cos(theta), math.sin(theta), 0.0))
        base = radial * PETAL_HINGE_R
        oriented_box(
            bm,
            (base.x, base.y, PETAL_BRACKET_Z - 0.075),
            (0.360, 0.150, 0.150),
            Matrix.Rotation(theta + math.pi / 2.0, 3, "Z"),
            "AA_Trim",
        )

    # --- poupe propulsive (fixe : elle porte le max Y et `Engine_C`) --------
    stern_bands = sweep_rect(bm, STERN, STERN_MATS, cap="AA_Greeble")
    # Plaques enfoncees : sans elles la poupe lit comme un bulbe lisse — c'est le
    # defaut qu'a montre la premiere planche 4 vues.
    for k, band in enumerate(stern_bands):
        ak.inset_panel(bm, [band[0]], "AA_Panel" if k % 2 else "AA_Hull",
                       thickness=0.055, depth=0.016)
        ak.inset_panel(bm, [band[2]], "AA_Greeble", thickness=0.055, depth=0.014)
    # Nervures transversales : elles donnent le rythme segmente de la planche.
    for i, (y0, hw) in enumerate(((1.98, 0.71), (2.44, 0.62), (2.86, 0.50), (3.22, 0.38))):
        oriented_box(bm, (0.0, y0, 0.02), (2.0 * hw + 0.09, 0.085, 0.42),
                     None, "AA_Trim" if i % 2 else "AA_Greeble")
    # Derives laterales : elles rendent la poupe lisible de dessus.
    for sx in (ak.PORT, ak.STARBOARD):
        seg_box(bm, (sx * 0.70, 2.16, 0.02), (sx * 1.02, 2.86, 0.02),
                0.055, 0.115, "AA_Panel")
        seg_box(bm, (sx * 1.02, 2.86, 0.02), (sx * 0.92, 3.16, 0.02),
                0.030, 0.075, "AA_Trim")
    for x, z, r in STERN_NOZZLES:
        ak.add_lathe(
            bm,
            [
                (NOZZLE_Y0, 0.000, "AA_Greeble"),
                (NOZZLE_Y0 + 0.05, r * 0.70, "AA_Greeble"),
                (NOZZLE_Y1 - 0.14, r * 0.86, "AA_Greeble"),
                (NOZZLE_Y1 - 0.05, r, "AA_Trim"),
                (NOZZLE_Y1, r * 0.82, "AA_Emissive_Engine"),
                (NOZZLE_Y1 - 0.06, r * 0.52, "AA_Emissive_Engine"),
                (NOZZLE_Y1 - 0.09, 0.000, "AA_Emissive_Engine"),
            ],
            14,
            center_x=x,
            center_z=z,
        )
    # veines magenta le long de la poupe
    for sx in (ak.PORT, ak.STARBOARD):
        seg_box(bm, (sx * 0.72, 1.90, 0.24), (sx * 0.52, 2.90, 0.20),
                0.026, 0.012, "AA_Emissive_Engine")

    # --- greebles : mecanique exposee sur le dos ----------------------------
    for k, sx in enumerate((ak.PORT, ak.STARBOARD)):
        ak.greeble_strip(
            bm,
            (sx * 0.52, 1.02, lerp_z(Z_TOP, 0.45)),
            (sx * 0.98, 1.42, lerp_z(Z_TOP, 0.74)),
            count=5,
            seed=SEED + 13 * (k + 1),
            size_range=(0.050, 0.105),
            height_range=(0.028, 0.062),
        )

    # --- emplantures des trois appendices -----------------------------------
    _mast(bm, ak.PORT, SCYTHE_MAST_Y, SCYTHE_PIVOT[0], SCYTHE_PIVOT[2], SCYTHE_JOINT_R)
    _mast(bm, ak.STARBOARD, CLAW_MAST_Y, CLAW_PIVOT[0], CLAW_PIVOT[2], CLAW_JOINT_R)

    # col du canon + rotule (la boule appartient a la coque, la calotte au canon)
    limb(bm, CANNON_NECK, CANNON_NECK_R, "AA_Panel", glow_from=0, joints=False)
    knuckle(bm, CANNON_PIVOT, CANNON_BALL_R, "AA_Greeble")
    for sx in (ak.PORT, ak.STARBOARD):
        seg_box(bm, (CANNON_X + sx * 0.34, -1.72, -0.10),
                (CANNON_X + sx * 0.16, -2.06, -0.04), 0.060, 0.055, "AA_Greeble")

    return ak.new_object("Hull", bm)


# ==========================================================================
# Noyau et petales : les objets que le gameplay cible
# ==========================================================================


def build_core() -> ak.MovingPart:
    """Noyau. Statique au contrat, mais noeud a part : le gameplay le cible, et
    son pivot est son propre centre (une pulsation d'echelle reste centree)."""
    bm = bmesh.new()
    rings = [polar_ring(bm, r, z, CORE_SEG) for r, z in CORE_RINGS]
    for i in range(len(rings) - 1):
        ak.bridge_rings(bm, rings[i], rings[i + 1], CORE_MATS[i])
    apex = bm.verts.new((0.0, 0.0, CORE_APEX_Z))
    ak.fan_to_point(bm, rings[-1], apex, "AA_Emissive_Engine")
    base = bm.verts.new((0.0, 0.0, -0.10))
    ak.fan_to_point(bm, list(reversed(rings[0])), base, "AA_Greeble")
    # nervures magenta : le noyau irradie, comme sur la planche
    for i in range(8):
        theta = 2.0 * math.pi * (i + 0.5) / 8.0
        d = Vector((math.cos(theta), math.sin(theta), 0.0))
        seg_box(
            bm,
            d * 0.10 + Vector((0.0, 0.0, 0.365)),
            d * 0.52 + Vector((0.0, 0.0, 0.115)),
            0.030,
            0.022,
            "AA_Emissive_Engine",
        )
    return ak.moving_part("Core", bm, (0.0, 0.0, 0.05))


def _petal_frame(deg: float) -> tuple[Vector, Vector, Vector, Vector]:
    """(charniere, axe du petale, axe transversal, normale du petale)."""
    theta = math.radians(deg)
    hinge = Vector(
        (
            PETAL_HINGE_R * math.cos(theta),
            PETAL_HINGE_R * math.sin(theta),
            PETAL_HINGE_Z,
        )
    )
    inward = Vector((-math.cos(theta), -math.sin(theta), 0.0))
    tilt = math.radians(PETAL_TILT)
    axis = (inward * math.cos(tilt) + Vector((0.0, 0.0, 1.0)) * math.sin(tilt)).normalized()
    cross = Vector((-math.sin(theta), math.cos(theta), 0.0))
    normal = cross.cross(axis).normalized()
    return hinge, axis, cross, normal


def build_petal(index: int) -> ak.MovingPart:
    """Un petale blinde de l'iris : plaque bombee, bord ivoire, couture magenta.

    Son pivot EST sa charniere : cote Godot, `Basis(axe_tangent, angle)` suffit a
    l'ouvrir (c'est ce que fait `harvester_combat._pose_iris()`, qui deduit l'axe
    tangent de la position du noeud).
    """
    bm = bmesh.new()
    hinge, axis, cross, normal = _petal_frame(PETAL_ANGLES[index])

    rings = []
    for s, hw, th in PETAL_SECTIONS:
        base = hinge + axis * s
        top, bot = [], []
        for k in PETAL_CROSS:
            side = cross * (k * hw)
            crest = PETAL_RIDGE * (1.0 - k * k)
            top.append(tuple(base + side + normal * (th + crest)))
            bot.append(tuple(base + side - normal * th))
        rings.append(ak.add_ring(bm, top + list(reversed(bot))))

    n = len(PETAL_CROSS)
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        for j, face in enumerate(band):
            if face is None or not face.is_valid:
                continue
            if j in (0, n - 2):
                face.material_index = ak.mat_index("AA_Trim")     # lisere ivoire
            elif j in (n - 1, 2 * n - 1):
                face.material_index = ak.mat_index("AA_Trim")     # tranche
            elif j >= n:
                face.material_index = ak.mat_index("AA_Greeble")  # dessous

    tip = bm.verts.new(tuple(hinge + axis * PETAL_LEN))
    ak.fan_to_point(bm, rings[-1], tip, "AA_Trim")
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")

    # couture magenta le long de la crete : le petale « fuit » de la lumiere
    for i in range(len(PETAL_SECTIONS) - 1):
        s0, _, th0 = PETAL_SECTIONS[i]
        s1, _, th1 = PETAL_SECTIONS[i + 1]
        p0 = hinge + axis * s0 + normal * (th0 + PETAL_RIDGE + 0.008)
        p1 = hinge + axis * s1 + normal * (th1 + PETAL_RIDGE + 0.008)
        seg_box(bm, p0, p1, 0.022, 0.012, "AA_Emissive_Engine")

    return ak.moving_part(f"Petal_{index + 1:02d}", bm, tuple(hinge))


# ==========================================================================
# Faux — trois maillons chaines
# ==========================================================================


def build_scythe_upper() -> ak.MovingPart:
    bm = bmesh.new()
    limb(bm, SCYTHE_UPPER, SCYTHE_UPPER_R, "AA_Panel", glow_from=0, root_gap=0.16)
    return ak.moving_part("Arm_Scythe", bm, SCYTHE_UPPER[0])


def build_scythe_mid() -> ak.MovingPart:
    bm = bmesh.new()
    limb(bm, SCYTHE_MID, SCYTHE_MID_R, "AA_Panel", glow_from=0)
    return ak.moving_part("Scythe_Mid", bm, SCYTHE_MID[0], parent="Arm_Scythe")


def build_scythe_blade() -> ak.MovingPart:
    """Lame en croissant : sections a 9 sommets — dos epais, tranchant lumineux."""
    bm = bmesh.new()
    knuckle(bm, SCYTHE_BLADE[0], SCYTHE_MID_R[-1] * 0.96, "AA_Greeble")

    rings = []
    for i, point in enumerate(SCYTHE_BLADE):
        p = Vector(point)
        if i == 0:
            tan = Vector(SCYTHE_BLADE[1]) - p
        elif i == len(SCYTHE_BLADE) - 1:
            tan = p - Vector(SCYTHE_BLADE[-2])
        else:
            tan = Vector(SCYTHE_BLADE[i + 1]) - Vector(SCYTHE_BLADE[i - 1])
        # `out` pointe vers le DOS de la lame (cote convexe) : le tranchant est
        # donc en -out, sur la face concave du croissant — comme une vraie faux.
        out = Vector((0.0, 0.0, 1.0)).cross(tan).normalized()
        nrm = tan.normalized().cross(out).normalized()
        back, edge, th = BLADE_BACK[i], BLADE_EDGE[i], BLADE_TH[i]
        rings.append(
            ak.add_ring(
                bm,
                [
                    tuple(p + out * back + nrm * th * 0.35),        # dos, dessus
                    tuple(p + nrm * th * 0.50),                     # crete
                    tuple(p - out * edge * 0.62 + nrm * th * 0.30), # depart du fil
                    tuple(p - out * edge + nrm * 0.012),            # levre haute
                    tuple(p - out * (edge + 0.030)),                # tranchant
                    tuple(p - out * edge - nrm * 0.012),            # levre basse
                    tuple(p - out * edge * 0.62 - nrm * th * 0.30), # depart du fil
                    tuple(p - nrm * th * 0.50),                     # ventre
                    tuple(p + out * back - nrm * th * 0.35),        # dos, dessous
                ],
            )
        )
    # Le fil porte une bande emissive LARGE dans le plan de la lame (et pas
    # seulement sur la tranche) : a 20 deg de camera, une lueur posee sur la
    # tranche est vue par la tranche, donc invisible.
    blade_mats = (
        "AA_Trim", "AA_Trim", "AA_Emissive_Engine", "AA_Emissive_Engine",
        "AA_Emissive_Engine", "AA_Emissive_Engine", "AA_Trim", "AA_Trim",
        "AA_Greeble",
    )
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Trim")
        for j, face in enumerate(band):
            if face is not None and face.is_valid:
                face.material_index = ak.mat_index(blade_mats[j])
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Trim")

    return ak.moving_part("Scythe_Blade", bm, SCYTHE_BLADE[0], parent="Scythe_Mid")


# ==========================================================================
# Griffe a trois tetes
# ==========================================================================


def build_claw_arm() -> ak.MovingPart:
    """Bras + fourche. Les trois cous partent d'ici ; les tetes sont a part."""
    bm = bmesh.new()
    limb(bm, CLAW_ARM, CLAW_ARM_R, "AA_Panel", glow_from=0, root_gap=0.16)
    fork = Vector(CLAW_ARM[-1])
    for neck, _ in CLAW_NECKS:
        target = Vector(neck)
        seg_box(bm, fork, target, 0.072, 0.062, "AA_Panel")
        knuckle(bm, target, 0.096, "AA_Greeble")
    return ak.moving_part("Arm_Claw", bm, CLAW_PIVOT)


def build_claw_head(index: int) -> tuple[ak.MovingPart, Vector]:
    """Tete a oeil magenta : trois serres ivoire, un oeil emissif sous verre.

    Retourne la piece et la position de l'oeil (elle sert de bouche de tir).
    """
    neck, flat = CLAW_NECKS[index]
    bm = bmesh.new()
    origin = Vector(neck)
    fwd = Vector((flat[0], flat[1], -0.10)).normalized()
    head = origin + fwd * CLAW_STALK

    seg_box(bm, origin, head, 0.062, 0.055, "AA_Panel")
    seg_box(
        bm,
        origin + fwd * CLAW_STALK * 0.30 + Vector((0.0, 0.0, 0.062)),
        origin + fwd * CLAW_STALK * 0.80 + Vector((0.0, 0.0, 0.055)),
        0.018,
        0.014,
        "AA_Emissive_Engine",
    )
    knuckle(bm, head, CLAW_HEAD_R, "AA_Panel")

    for angle in TALON_SPREAD:
        rot = Matrix.Rotation(math.radians(angle), 3, "Z")
        heading = rot @ fwd
        heading.z -= 0.20          # les serres plongent : elles agrippent
        heading.normalize()
        base = head + heading * CLAW_HEAD_R * 0.55
        mid = base + heading * TALON_LEN * 0.52 + Vector((0.0, 0.0, 0.04))
        tip = mid + heading * TALON_LEN * 0.60 + Vector((0.0, 0.0, -0.08))
        seg_box(bm, base, mid, CLAW_HEAD_R * TALON_ROOT, CLAW_HEAD_R * TALON_ROOT * 0.9,
                "AA_Trim")
        seg_box(bm, mid, tip, CLAW_HEAD_R * TALON_TIP, CLAW_HEAD_R * TALON_TIP * 0.9,
                "AA_Trim")

    eye = head + fwd * CLAW_HEAD_R * 0.26 + Vector((0.0, 0.0, CLAW_HEAD_R * 0.34))
    knuckle(bm, eye, EYE_R, "AA_Emissive_Engine")
    knuckle(bm, eye + fwd * 0.028, EYE_R * 0.78, "AA_Glass")

    part = ak.moving_part(f"Claw_Head_{index + 1}", bm, neck, parent="Arm_Claw")
    return part, eye + fwd * 0.10


# ==========================================================================
# Canon
# ==========================================================================


def build_cannon_breech() -> ak.MovingPart:
    """Culasse : calotte de rotule + manchon de glissement + entretoises."""
    bm = bmesh.new()
    pivot = Vector(CANNON_PIVOT)
    spherical_shell(
        bm,
        pivot,
        Vector((0.0, -1.0, 0.0)),
        CANNON_SOCKET,
        CANNON_SOCKET_DEG,
        16,
        4,
        ("AA_Greeble", "AA_Panel"),
    )
    tube(bm, SLEEVE_Y[0], SLEEVE_Y[1], SLEEVE_R, 18, ("AA_Greeble", "AA_Panel"),
         center=(CANNON_X, CANNON_Z))
    # entretoises calotte -> manchon
    for deg in SLEEVE_STRUTS:
        a = math.radians(deg)
        d = Vector((math.cos(a), 0.0, math.sin(a)))
        socket_mid = pivot + Vector((0.0, -1.0, 0.0)) * (
            CANNON_SOCKET[1] * math.cos(math.radians(CANNON_SOCKET_DEG[0]))
        ) + d * (CANNON_SOCKET[1] * math.sin(math.radians(CANNON_SOCKET_DEG[0])))
        sleeve_pt = Vector((CANNON_X, SLEEVE_Y[0], CANNON_Z)) + d * SLEEVE_R[1] * 0.9
        seg_box(bm, socket_mid, sleeve_pt, 0.055, 0.050, "AA_Greeble")
        seg_box(
            bm,
            socket_mid + Vector((0.0, 0.0, 0.0)) + d * 0.03,
            sleeve_pt + d * 0.03,
            0.016,
            0.014,
            "AA_Emissive_Engine",
        )
    # ⚠️ Pas de joue laterale sur la culasse a hauteur du fut : la course de recul
    # de 25 cm y ramene les ailettes du fut, et la mesure l'a refuse. Le manchon,
    # ses entretoises et son collier suffisent a lui donner du volume.
    # Collier ivoire du manchon. Aucune de ses trois griffes n'est dans le PLAN
    # HORIZONTAL : c'est la que passent les ailettes du fut quand il recule.
    for deg in (90.0, 210.0, 330.0):
        a = math.radians(deg)
        d = Vector((math.cos(a), 0.0, math.sin(a)))
        seg_box(
            bm,
            Vector((CANNON_X, SLEEVE_Y[1] + 0.06, CANNON_Z)) + d * SLEEVE_R[1] * 0.92,
            Vector((CANNON_X, SLEEVE_Y[1] - 0.02, CANNON_Z)) + d * (SLEEVE_R[1] + 0.09),
            0.070,
            0.060,
            "AA_Trim",
        )
    return ak.moving_part("Arm_Cannon", bm, CANNON_PIVOT)


def build_cannon_barrel() -> ak.MovingPart:
    """Fut coulissant.

    ⚠️ Son pivot a le MEME Y d'auteur que celui de `Arm_Cannon` : cote Godot le
    decalage `position.z` du noeud vaut donc 0 au repos, et le combat peut ecrire
    `position.z = cannon_recoil` sans faire sauter la piece a la premiere image.
    """
    bm = bmesh.new()
    ak.add_lathe(bm, list(BARREL_PROFILE), BARREL_SEG,
                 center_x=CANNON_X, center_z=CANNON_Z)
    for deg in BARREL_MOUTHS:
        a = math.radians(deg)
        ak.add_lathe(
            bm,
            [
                (-3.24, 0.000, "AA_Greeble"),
                (-3.28, 0.075, "AA_Greeble"),
                (-3.42, 0.086, "AA_Greeble"),
                (-3.46, 0.096, "AA_Trim"),
                (-3.49, 0.078, "AA_Emissive_Engine"),
                (-3.47, 0.046, "AA_Emissive_Engine"),
                (-3.45, 0.000, "AA_Emissive_Engine"),
            ],
            10,
            center_x=CANNON_X + 0.165 * math.cos(a),
            center_z=CANNON_Z + 0.165 * math.sin(a),
        )
    # dents ivoire de bouche — en retrait de la levre : c'est le profil du fut,
    # et lui seul, qui doit porter le min Y du modele (y = -3,50).
    for deg in (100.0, 220.0, 340.0):
        a = math.radians(deg)
        d = Vector((math.cos(a), 0.0, math.sin(a)))
        seg_box(
            bm,
            Vector((CANNON_X, -3.30, CANNON_Z)) + d * 0.212,
            Vector((CANNON_X, -3.44, CANNON_Z)) + d * 0.152,
            0.042,
            0.036,
            "AA_Trim",
        )
    # Ailettes HORIZONTALES : a 20 deg de la verticale, un fut pointe vers l'avant
    # se voit par le cul et ne ressemble a rien. Ce sont elles, et la couronne de
    # bouche, qui disent « canon » dans la seule vue que le joueur aura.
    for sx in (ak.PORT, ak.STARBOARD):
        # ⚠️ Entierement en AVANT de y = -3,23 : au-dela, la course de recul les
        # ramenerait dans la couronne du manchon (mesure, deux fois de suite).
        seg_box(bm, (CANNON_X + sx * 0.20, -3.26, CANNON_Z),
                (CANNON_X + sx * 0.42, -3.38, CANNON_Z), 0.052, 0.034, "AA_Panel")
        seg_box(bm, (CANNON_X + sx * 0.42, -3.38, CANNON_Z),
                (CANNON_X + sx * 0.33, -3.50, CANNON_Z), 0.034, 0.024, "AA_Trim")
        seg_box(bm, (CANNON_X + sx * 0.24, -3.30, CANNON_Z + 0.034),
                (CANNON_X + sx * 0.38, -3.40, CANNON_Z + 0.034),
                0.014, 0.010, "AA_Emissive_Engine")
    return ak.moving_part(
        "Cannon_Barrel",
        bm,
        (CANNON_PIVOT[0], CANNON_PIVOT[1], CANNON_PIVOT[2]),
        parent="Arm_Cannon",
    )


# ==========================================================================
# Points d'attache
# ==========================================================================


def build_attach_points(eyes: list) -> list:
    """Positions **derivees de la geometrie**, jamais devinees.

    Les `Hinge_*` de la version precedente ont disparu : le pivot vit desormais
    dans l'origine de la piece, et laisser des marqueurs concurrents inviterait un
    futur lecteur a s'en servir.
    """
    points = [
        ak.attach_point("Core_Center", (0.0, 0.0, 0.14)),
        ak.attach_point("Engine_C", (0.0, ENGINE_Y, -0.01)),
        ak.attach_point("Muzzle_Cannon", (CANNON_X, MUZZLE_Y, CANNON_Z)),
    ]
    for i, eye in enumerate(eyes):
        points.append(ak.attach_point(f"Muzzle_Claw_{i + 1}", tuple(eye)))
    return points


# ==========================================================================
# Mesure de degagement — le livrable central de BRIEF-0039
#
# Le contrat d'`export_hull()` ne connait QUE la pose de repos. Un appendice qui
# traverse la coque des qu'il bouge le passe sans un mot : c'est exactement ce
# qui a coute quatre briefs au Specter-9 (un marquage a cheval sur une charniere
# avait fait tomber le debattement d'un volet de 18,5 a 2,8 deg — bounding box
# parfaite, volet dans la coque). On remesure donc a chaque build, sur le
# maillage REELLEMENT livre, en rejouant les rotations que le combat ecrit.
# ==========================================================================

#: Repere d'auteur -> repere Godot : (x, y, z) -> (-x, z, y). Rotation rigide
#: (determinant +1) : un axe se transporte comme un vecteur, un angle est
#: conserve. Toute la mesure se fait DANS LE REPERE GODOT, avec exactement les
#: rotations qu'ecrit `harvester_combat.gd` — un signe faux valide un bras qui
#: traverse la coque, et personne ne le verrait avant le jeu.
_TO_GODOT = Matrix(((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)))

#: Amplitudes appliquees par le gameplay (`harvester_combat.gd` + le .tres).
FOLD_DEG = -70.0          # repli d'un appendice detruit (rotation.x de la racine)
SCYTHE_SWING_DEG = 55.0   # cumule sur la chaine : 0,45 / 0,35 / 0,20
CLAW_SWEEP_DEG = 32.0     # balayage de visee (rotation.y de la racine)
CLAW_CONVERGE_DEG = 18.0  # ecart des tetes 1 et 3 (rotation.y de chaque cou)
CANNON_RECOIL = 0.25      # translation +Z Godot du fut
IRIS_OPEN_DEG = 78.0      # exigence du brief (le .tres en applique 72)

#: Rayon d'exclusion de charniere, par appendice. Une articulation reelle
#: s'interpenetre PAR CONSTRUCTION (boule dans sa calotte, racine de petale dans
#: son berceau) ; la mesure ecarte donc, des DEUX cotes, la matiere a moins de ce
#: rayon du pivot. C'est licite : une rotation autour d'un axe passant par le
#: pivot conserve la distance au pivot, donc rien de ce qui est exclu ne peut
#: rencontrer ce qui ne l'est pas.
SCYTHE_SKIP = 0.20
CLAW_SKIP = 0.20
CANNON_SKIP = 0.44        # la calotte enveloppe la boule : elle est plus large
PETAL_SKIP = 0.09


def _godot_euler(x: float, y: float, z: float) -> Matrix:
    """Basis Godot pour `rotation = Vector3(x, y, z)` — ordre YXZ, en radians."""
    return (
        Matrix.Rotation(y, 4, "Y")
        @ Matrix.Rotation(x, 4, "X")
        @ Matrix.Rotation(z, 4, "Z")
    )


def _clip_sphere(verts: list, tri: list, pivot: Vector, skip: float,
                 out: list, depth: int = 0) -> None:
    """Garde de `tri` ce qui est HORS de la sphere (`pivot`, `skip`), en coupant.

    Un simple test « tous les sommets dedans ? » ne suffit pas : un longeron
    modelise d'un seul tenant produit des triangles de 30 cm qui enjambent la
    sphere de charniere. Ils etaient donc conserves ENTIERS, avec la matiere du
    joint dedans — et la mesure criait sur une interpenetration normale. On coupe
    donc l'arete la plus longue, recursivement : l'exclusion devient geometrique
    et non plus « par triangle ».
    """
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
    """(sommets, triangles) d'un objet, en repere GODOT, compactes.

    `skip` : rayon autour de `pivot` dont la geometrie est ecartee. Une charniere
    reelle s'interpenetre par construction (une boule dans sa calotte, une racine
    de petale dans son berceau) ; ce qui doit degager, c'est tout le reste. Le
    rayon retenu est publie piece par piece au compte-rendu.
    """
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
    # compactage : le BVH n'aime pas les sommets orphelins, et les boucles de
    # `find_nearest` parcourent la liste des sommets telle quelle.
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


class Solid:
    """Soupe de triangles figee, prete a repondre « a quelle distance ? »."""

    def __init__(self, verts: list, tris: list):
        self.verts = verts
        self.tris = tris
        self.tree = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)

    def distance_to(self, verts: list, tris: list) -> float:
        """Distance minimale a une autre soupe ; 0.0 si elles se mordent.

        Deux sens de requete : un sommet mobile pres d'une face fixe, ET un sommet
        fixe pres d'une face mobile. Un seul sens laisserait passer une lame mince
        qui traverse une grande face sans qu'aucun de ses sommets n'en approche.
        """
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


class Rig:
    """Chaine articulee posable : pivots, parentage et maillages en repere Godot.

    Reproduit exactement ce que Godot fera du `.glb` : origine de la piece sur son
    pivot, position de l'enfant RELATIVE au parent, rotation en euler YXZ.
    """

    def __init__(self, parts: list, skip: dict):
        self.names = [p.obj.name for p in parts]
        self.pivot = {p.obj.name: _TO_GODOT @ Vector(p.pivot) for p in parts}
        self.parent = {p.obj.name: p.parent for p in parts}
        self.verts, self.tris = {}, {}
        for part in parts:
            name = part.obj.name
            verts, tris = _soup(part.obj, self.pivot[name], skip.get(name, 0.0))
            self.verts[name] = [v - self.pivot[name] for v in verts]  # local
            self.tris[name] = tris

    def pose(self, angles: dict, shift: dict | None = None) -> dict:
        """Sommets monde de chaque piece, pour un jeu d'angles (radians)."""
        shift = shift or {}
        world: dict = {}
        out: dict = {}
        for name in self.names:
            parent = self.parent[name]
            offset = self.pivot[name] - (
                Vector((0.0, 0.0, 0.0)) if parent is None else self.pivot[parent]
            )
            local = Matrix.Translation(offset + shift.get(name, Vector((0.0,) * 3)))
            base = Matrix.Identity(4) if parent is None else world[parent]
            world[name] = base @ local @ _godot_euler(*angles.get(name, (0.0, 0.0, 0.0)))
            out[name] = [world[name] @ v for v in self.verts[name]]
        return out

    def clearance(self, poses: list, obstacle: Solid) -> tuple[float, str]:
        """Marge minimale sur toutes les poses, et la pose ou elle est atteinte."""
        best, where = 9.9, "aucune pose"
        for label, angles, shift in poses:
            for name, verts in self.pose(angles, shift).items():
                if not self.tris[name]:
                    continue
                d = obstacle.distance_to(verts, self.tris[name])
                if d < best:
                    best, where = d, f"{label} / {name}"
        return best, where


def _rad(deg: float) -> float:
    return math.radians(deg)


def _scythe_poses() -> list:
    """Repli x estoc. `root.x = fold + swing*0,45`, `mid.x = swing*0,35`,
    `blade.x = swing*0,20` — et `swing` est proportionnel au deploiement."""
    poses = []
    for d in (0.0, 0.25, 0.5, 0.75, 1.0):
        fold = _rad(FOLD_DEG) * (1.0 - d)
        for k in (-1.0, -0.6, -0.3, 0.0, 0.3, 0.6, 1.0):
            swing = _rad(SCYTHE_SWING_DEG) * k * d
            poses.append((
                f"deploi {d:.2f} estoc {k * SCYTHE_SWING_DEG:+.0f} deg",
                {
                    "Arm_Scythe": (fold + swing * 0.45, 0.0, 0.0),
                    "Scythe_Mid": (swing * 0.35, 0.0, 0.0),
                    "Scythe_Blade": (swing * 0.20, 0.0, 0.0),
                },
                {},
            ))
    return poses


def _claw_poses() -> list:
    poses = []
    for d in (0.0, 0.25, 0.5, 0.75, 1.0):
        fold = _rad(FOLD_DEG) * (1.0 - d)
        for k in (-1.0, -0.5, 0.0, 0.5, 1.0):
            sweep = _rad(CLAW_SWEEP_DEG) * k * d
            converge = _rad(CLAW_CONVERGE_DEG) * d
            angles = {"Arm_Claw": (fold, sweep, 0.0)}
            for i in range(3):
                angles[f"Claw_Head_{i + 1}"] = (0.0, converge * (i - 1), 0.0)
            poses.append((
                f"deploi {d:.2f} balayage {k * CLAW_SWEEP_DEG:+.0f} deg", angles, {},
            ))
    return poses


def _cannon_poses() -> list:
    poses = []
    for d in (0.0, 0.25, 0.5, 0.75, 1.0):
        fold = _rad(FOLD_DEG) * (1.0 - d)
        for recoil in (0.0, CANNON_RECOIL * 0.5, CANNON_RECOIL):
            poses.append((
                f"deploi {d:.2f} recul {recoil:.2f} m",
                {"Arm_Cannon": (fold, 0.0, 0.0)},
                {"Cannon_Barrel": Vector((0.0, 0.0, recoil))},
            ))
    return poses


def _petal_axis(pivot: Vector) -> Vector:
    """L'axe que `harvester_combat._bind_iris()` calcule : UP x radial."""
    radial = Vector((pivot.x, 0.0, pivot.z))
    return Vector((0.0, 1.0, 0.0)).cross(radial.normalized()).normalized()


def _iris_clearance(petals: list, hull) -> tuple[float, str, float, str]:
    """Degagement de l'iris : chaque petale contre la coque ET contre ses voisins.

    Les deux mesures sont distinctes parce que les remedes le sont : mordre le
    pont se corrige en remontant la charniere, mordre un voisin en amincissant
    le petale ou en reduisant le pas.
    """
    soups = {}
    hulls = {}
    for part in petals:
        pivot = _TO_GODOT @ Vector(part.pivot)
        verts, tris = _soup(part.obj, pivot, PETAL_SKIP)
        soups[part.obj.name] = (pivot, [v - pivot for v in verts], tris)
        hulls[part.obj.name] = Solid(*_soup(hull, pivot, PETAL_SKIP))

    best_hull, where_hull = 9.9, ""
    best_pair, where_pair = 9.9, ""
    steps = 14
    for s in range(steps + 1):
        angle = _rad(IRIS_OPEN_DEG) * s / steps
        posed = {}
        for name, (pivot, verts, tris) in soups.items():
            basis = Matrix.Rotation(angle, 4, _petal_axis(pivot))
            mat = Matrix.Translation(pivot) @ basis
            posed[name] = ([mat @ v for v in verts], tris)
        for name, (verts, tris) in posed.items():
            d = hulls[name].distance_to(verts, tris)
            if d < best_hull:
                best_hull, where_hull = d, f"{name} a {math.degrees(angle):.0f} deg"
        names = sorted(posed)
        for i, name in enumerate(names):
            other = names[(i + 1) % len(names)]
            solid = Solid(*posed[other])
            d = solid.distance_to(*posed[name])
            if d < best_pair:
                best_pair = d
                where_pair = f"{name}/{other} a {math.degrees(angle):.0f} deg"
    return best_hull, where_hull, best_pair, where_pair


def _clearance_table(hull, parts: dict, petals: list) -> list:
    """Le tableau exige par le brief : piece / debattement / marge minimale."""
    hull_solid = Solid(*_soup(hull))
    rows = []

    def hull_around(part: ak.MovingPart, skip: float) -> Solid:
        """Coque privee de la matiere a moins de `skip` du pivot de `part`.

        L'exclusion doit etre SYMETRIQUE : une rotation autour d'un axe passant
        par le pivot conserve la distance au pivot, donc un sommet mobile a la
        distance r ne peut rencontrer que de la matiere fixe a la meme distance r.
        Ecarter la charniere d'un seul cote (la piece, pas le mat qui la porte)
        faisait crier la mesure sur l'interpenetration NORMALE d'une rotule dans
        son logement — et un faux positif finit toujours par etre desactive.
        """
        return Solid(*_soup(hull, _TO_GODOT @ Vector(part.pivot), skip))

    scythe = Rig(
        [parts["Arm_Scythe"], parts["Scythe_Mid"], parts["Scythe_Blade"]],
        {"Arm_Scythe": SCYTHE_SKIP},
    )
    margin, where = scythe.clearance(
        _scythe_poses(), hull_around(parts["Arm_Scythe"], SCYTHE_SKIP)
    )
    rows.append(("Arm_Scythe + Scythe_Mid + Scythe_Blade",
                 f"estoc +/-{SCYTHE_SWING_DEG:.0f} deg cumules, repli {FOLD_DEG:.0f} deg",
                 margin, where))

    claw = Rig(
        [parts["Arm_Claw"]] + [parts[f"Claw_Head_{i + 1}"] for i in range(3)],
        {"Arm_Claw": CLAW_SKIP},
    )
    margin, where = claw.clearance(
        _claw_poses(), hull_around(parts["Arm_Claw"], CLAW_SKIP)
    )
    rows.append(("Arm_Claw + Claw_Head_1..3",
                 f"balayage +/-{CLAW_SWEEP_DEG:.0f} deg, tetes +/-{CLAW_CONVERGE_DEG:.0f} deg, "
                 f"repli {FOLD_DEG:.0f} deg",
                 margin, where))

    # Tetes entre elles : leur ecartement est le vrai risque, pas la coque.
    head_rig = Rig(
        [parts["Arm_Claw"]] + [parts[f"Claw_Head_{i + 1}"] for i in range(3)],
        {"Arm_Claw": 0.0},
    )
    worst, worst_where = 9.9, ""
    for label, angles, shift in _claw_poses():
        posed = head_rig.pose(angles, shift)
        for a, b in ((1, 2), (2, 3), (1, 3)):
            na, nb = f"Claw_Head_{a}", f"Claw_Head_{b}"
            solid = Solid(posed[na], head_rig.tris[na])
            d = solid.distance_to(posed[nb], head_rig.tris[nb])
            if d < worst:
                worst, worst_where = d, f"{label} / {na}-{nb}"
    rows.append(("Claw_Head_1..3 entre elles",
                 f"+/-{CLAW_CONVERGE_DEG:.0f} deg chacune", worst, worst_where))

    # Griffe contre canon : les deux appendices se font face de part et d'autre du
    # bec. Aucune ligne du brief ne le demande — c'est justement pour ca qu'il faut
    # le mesurer : la tete 3 balaie vers l'interieur, ou le canon l'attend.
    cannon_rest = Solid(
        *(lambda a, b: (a[0] + [v for v in b[0]],
                        a[1] + [[i + len(a[0]) for i in t] for t in b[1]]))(
            _soup(parts["Arm_Cannon"].obj), _soup(parts["Cannon_Barrel"].obj)
        )
    )
    margin, where = claw.clearance(_claw_poses(), cannon_rest)
    rows.append(("Arm_Claw + tetes / canon",
                 f"balayage +/-{CLAW_SWEEP_DEG:.0f} deg, tetes +/-{CLAW_CONVERGE_DEG:.0f} deg",
                 margin, where))

    cannon = Rig(
        [parts["Arm_Cannon"], parts["Cannon_Barrel"]], {"Arm_Cannon": CANNON_SKIP}
    )
    margin, where = cannon.clearance(
        _cannon_poses(), hull_around(parts["Arm_Cannon"], CANNON_SKIP)
    )
    rows.append(("Arm_Cannon + Cannon_Barrel / coque",
                 f"repli {FOLD_DEG:.0f} deg, recul {CANNON_RECOIL:.2f} m",
                 margin, where))

    # Recul du fut DANS sa culasse : c'est la course, pas la coque, qui borne.
    breech = Solid(*_soup(parts["Arm_Cannon"].obj))
    barrel_verts, barrel_tris = _soup(parts["Cannon_Barrel"].obj)
    worst, worst_where = 9.9, ""
    for k in range(9):
        travel = CANNON_RECOIL * k / 8.0
        # ⚠️ la course est en Z GODOT (3e composante), pas en Y : c'est le meme
        # `position.z` que le combat ecrit. La confondre avec Y faisait monter le
        # fut au lieu de le faire rentrer — et la premiere mesure a bel et bien
        # signale une morsure inexistante.
        moved = [v + Vector((0.0, 0.0, travel)) for v in barrel_verts]
        d = breech.distance_to(moved, barrel_tris)
        if d < worst:
            worst, worst_where = d, f"recul {travel:.3f} m"
    rows.append(("Cannon_Barrel dans Arm_Cannon",
                 f"course {CANNON_RECOIL:.2f} m", worst, worst_where))

    hull_margin, hull_where, pair_margin, pair_where = _iris_clearance(petals, hull)
    rows.append(("Petal_01..05 / coque", f"ouverture 0 -> {IRIS_OPEN_DEG:.0f} deg",
                 hull_margin, hull_where))
    rows.append(("Petal_01..05 entre eux", f"ouverture 0 -> {IRIS_OPEN_DEG:.0f} deg",
                 pair_margin, pair_where))
    return rows


# ==========================================================================
# Assemblage
# ==========================================================================


def _finish(obj, width: float = 0.008, angle: float = 30.0) -> None:
    ak.cleanup(obj)
    ak.bevel_sharp_edges(obj, width=width, segments=1, angle_deg=angle)
    ak.shade_smooth_by_angle(obj, angle_deg=angle)


def _bounds(objs: list) -> tuple[Vector, Vector]:
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    for obj in objs:
        for vert in obj.data.vertices:
            for a in range(3):
                lo[a] = min(lo[a], vert.co[a])
                hi[a] = max(hi[a], vert.co[a])
    return lo, hi


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)

    hull = build_hull()
    petals = [build_petal(i) for i in range(PETAL_COUNT)]
    heads, eyes = [], []
    for i in range(3):
        part, eye = build_claw_head(i)
        heads.append(part)
        eyes.append(eye)
    parts = [
        build_core(),
        *petals,
        build_scythe_upper(),
        build_scythe_mid(),
        build_scythe_blade(),
        build_claw_arm(),
        *heads,
        build_cannon_breech(),
        build_cannon_barrel(),
    ]
    by_name = {p.obj.name: p for p in parts}

    _finish(hull)
    for part in parts:
        _finish(part.obj)

    # --- controle en repere d'auteur, avant tout export --------------------
    objs = [hull] + [p.obj for p in parts]
    lo, hi = _bounds(objs)
    print("--- mesures en repere d'auteur (avant correction d'axe) ---")
    for obj in objs:
        o_lo, o_hi = _bounds([obj])
        print(
            f"  {obj.name:<14} x[{o_lo.x:+.3f} {o_hi.x:+.3f}] "
            f"y[{o_lo.y:+.3f} {o_hi.y:+.3f}] z[{o_lo.z:+.3f} {o_hi.z:+.3f}] "
            f"{len(obj.data.polygons)} faces"
        )
    print(
        f"  TOTAL          x[{lo.x:+.3f} {hi.x:+.3f}] y[{lo.y:+.3f} {hi.y:+.3f}] "
        f"z[{lo.z:+.3f} {hi.z:+.3f}]  ->  {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} "
        f"x {hi.z - lo.z:.3f} m"
    )

    # --- degagement a fond de course (BRIEF-0039) --------------------------
    print("--- degagement des pieces mobiles (maillage livre, poses du combat) ---")
    failures = []
    for name, travel, margin, where in _clearance_table(hull, by_name, petals):
        verdict = "OK " if margin > 0.0 else "MORD"
        print(f"  [{verdict}] {name:<38} {travel:<52} {margin * 1000:7.1f} mm  ({where})")
        if margin <= 0.0:
            failures.append(f"{name} : {where}")
    if failures:
        raise ak.ContractError(
            "pieces mobiles qui mordent la coque ou leur voisine :\n"
            + "\n".join(f"  - {f}" for f in failures)
        )

    ak.export_hull(hull, build_attach_points(eyes), OUTPUT, CONTRACT, parts=parts)


if __name__ == "__main__":
    main()
