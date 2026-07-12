"""build_choir_harvester.py — coque 3D du Choir Harvester, mini-boss (BRIEF-0023).

    blender45 -b -P tools/blender/build_choir_harvester.py

Produit `assets/imported/models/bosses/choir_harvester.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (aucun alea non seede) et s'auto-valide : `ak.export_hull()`
relit le `.glb` produit et echoue bruyamment si la bounding box, le budget de
triangles, les materiaux, le centrage du pivot ou les points d'attache sortent
du contrat.

Reference de design : `assets/source/concepts/choir_harvester_concept_sheet.png`
(corps discoide blinde cercle d'anneaux segmentes, noyau magenta protege par cinq
petales en iris, grand bras-faux replie au-dessus du corps, deux bras a griffes a
oeil magenta, module arriere relie par un cou segmente).

Repere d'auteur (ADR-0008) : face menacante -Y, dessus +Z, **babord +X**
(cf. l'en-tete d'aegis_kit : le signe de X est contre-intuitif).


COQUE MULTI-OBJETS — pourquoi ce script est different des quatre autres
======================================================================
Le gameplay doit pouvoir cibler et animer le noyau, les cinq petales de l'iris,
les trois bras et le module arriere : ils sont donc livres comme **objets
distincts et nommes** (`Core`, `Petal_01..05`, `Arm_Scythe`, `Arm_Claw_L`,
`Arm_Claw_R`, `Pod_Rear`), et non fusionnes dans une coque unique comme le
Specter-9 ou le Needle Scout.

`ak.export_hull(hull, attach_points, ...)` n'expose aujourd'hui qu'**un** objet
maille : les pieces sont donc passees dans la liste `attach_points`, qui est en
pratique « la liste des objets a selectionner en plus de la coque ». Deux
consequences, assumees et verifiees ici :

  1. la correction d'axe (`_AXIS_FIX`) n'est appliquee par `export_hull()` qu'a
     `hull.data` ; on l'applique donc nous-memes aux pieces, en reutilisant
     **la constante du kit** (jamais une copie locale : une divergence ferait
     voler la coque a reculons) ;
  2. le validateur du kit calcule la bounding box a partir des accesseurs glTF,
     donc dans l'espace **local** de chaque maillage. Toutes les pieces sont
     donc laissees a la transformation identite, geometrie exprimee dans le
     repere global : les chiffres valides par le kit sont alors les vrais
     chiffres monde. Les pivots d'animation sont livres a cote, sous forme de
     points d'attache `Hinge_*`.

Le kit gagnerait un parametre `parts: list[Object]` — signale au compte-rendu,
pas fait ici (trois autres coques s'appuient dessus en parallele).
"""

from __future__ import annotations

import math
import os
import sys

import bmesh
from mathutils import Matrix, Vector

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
    required_attach_points=("Core_Center", "Muzzle_L", "Muzzle_R", "Engine_C"),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/bosses/choir_harvester.glb")

SEED = 40507  # graine unique du Choir Harvester (determinisme des greebles)

HALF_L = CONTRACT.length_z / 2.0   # 3.500 — prow en -Y, module arriere en +Y
HALF_W = CONTRACT.width_x / 2.0    # 2.275 — lame de la faux / griffe tribord

# ==========================================================================
# Carapace discoide : ellipse en vue de dessus, puits d'iris circulaire
# ==========================================================================

CARA_AX = 1.82      # demi-largeur du disque blinde
CARA_AY = 2.20      # demi-longueur du disque blinde
IRIS_R = 0.95       # rayon du puits d'iris (circulaire, il loge noyau + petales)
N_SEG = 36          # segments angulaires du disque (multiple de 12 : les rings)

#: Stations radiales : t=0 sur la levre du puits, t=1 sur le bord de carapace.
T_RINGS = (0.00, 0.16, 0.34, 0.55, 0.72, 0.86, 0.95, 1.00)
Z_TOP = (0.30, 0.36, 0.385, 0.36, 0.30, 0.21, 0.12, 0.03)
Z_BOT = (-0.30, -0.36, -0.40, -0.38, -0.32, -0.22, -0.12, -0.03)

#: Puits d'iris : (rayon, z) du haut de la levre jusqu'au plancher.
WELL = ((IRIS_R, 0.30), (0.88, 0.12), (0.84, -0.04), (0.60, -0.09))
WELL_MATS = ("AA_Greeble", "AA_Emissive_Engine", "AA_Greeble")

RIM_BLOCKS = 24     # cerclage exterieur segmente
RIM_SPIKES = (38.0, 92.0, 148.0, 214.0, 322.0)  # ergots ivoire (deg, asymetriques)

# ==========================================================================
# Prow : bec blinde avant. La planche fait definir la pointe avant par les
# bras ; le contrat du kit exige que la coque porte elle-meme les extremes en Y
# (temoin d'orientation asymetrique). Le bec resout les deux : il donne au boss
# une face avant lisible et il ancre y = -3.50.
# ==========================================================================

#: (y, demi-largeur, z_haut, z_bas). Volontairement mince et bas : ce bec est
#: un ajout a la planche, il ancre le contrat — il ne doit pas voler la
#: silhouette au disque ni aux bras, qui, eux, viennent du concept.
PROW: tuple[tuple[float, float, float, float], ...] = (
    (-2.02, 0.52, 0.10, -0.16),
    (-2.45, 0.46, 0.09, -0.18),
    (-2.86, 0.37, 0.06, -0.19),
    (-3.20, 0.24, 0.03, -0.17),
    (-3.42, 0.13, 0.00, -0.12),
    (-HALF_L, 0.045, -0.035, -0.085),   # pointe : min Y de la coque
)

# ==========================================================================
# Arriere : cou segmente + berceau (deux longerons qui encadrent le module et
# ancrent y = +3.50), puis le module lui-meme (objet `Pod_Rear`).
# ==========================================================================

NECK = ((0.0, 1.98, 0.06), (0.0, 2.18, 0.06), (0.0, 2.38, 0.05), (0.0, 2.56, 0.05))
NECK_R = (0.30, 0.27, 0.24, 0.22)

#: Longeron de berceau (cote babord ; le cote tribord est son miroir).
CRADLE = (
    (0.88, 1.92, 0.03),
    (0.86, 2.42, 0.01),
    (0.82, 2.94, -0.01),
    (0.78, 3.34, -0.02),
    (0.74, HALF_L, -0.02),   # pointe : max Y de la coque
)

POD_CENTER_Z = 0.02
#: Profil de revolution du module arriere : (y, rayon, materiau du segment).
POD_PROFILE = (
    (2.42, 0.000, "AA_Greeble"),
    (2.47, 0.260, "AA_Greeble"),
    (2.56, 0.400, "AA_Hull"),
    (2.72, 0.495, "AA_Hull"),
    (2.94, 0.540, "AA_Panel"),
    (3.14, 0.535, "AA_Panel"),
    (3.20, 0.565, "AA_Greeble"),   # collier mecanique
    (3.28, 0.565, "AA_Trim"),      # jonc ivoire
    (3.33, 0.520, "AA_Greeble"),
    (3.42, 0.505, "AA_Greeble"),   # culot
    (3.40, 0.420, "AA_Emissive_Engine"),
    (3.33, 0.350, "AA_Emissive_Engine"),
    (3.28, 0.000, "AA_Emissive_Engine"),  # fond lumineux
)
POD_SEG = 20
POD_NOZZLES = (70.0, 190.0, 310.0)   # tuyeres secondaires (deg autour de l'axe)
#: `add_lathe` ne sait faire que des sections rondes ; un module rond de 1,08 m
#: de diametre ferait de ce boss un objet epais, illisible a 20 deg de camera
#: (ADR-0008). On l'aplatit en fin de construction : fuseau ovale, tuyeres
#: ovales — exactement la lecture de la planche en vue de dessus.
POD_FLATTEN_Z = 0.70

ENGINE_Y = 3.395   # plan de sortie du module (origine de la trainee)

# ==========================================================================
# Noyau et iris (le point faible : ce que le joueur doit viser)
# ==========================================================================

#: (rayon, z) du noyau, du collier de base jusqu'a l'apex.
CORE_RINGS = ((0.62, -0.10), (0.58, 0.00), (0.50, 0.10), (0.36, 0.19), (0.18, 0.25))
CORE_APEX_Z = 0.29
CORE_SEG = 24
CORE_MATS = ("AA_Greeble", "AA_Glass", "AA_Emissive_Engine", "AA_Emissive_Engine")

PETAL_COUNT = 5
PETAL_ANGLES = tuple(18.0 + 72.0 * i for i in range(PETAL_COUNT))
PETAL_HINGE_R = 1.02      # charniere : sur la levre du puits
PETAL_HINGE_Z = 0.26
PETAL_TILT = 20.0         # deg — iris entrouvert : le magenta fuse dans les jours
#: Longueur calibree pour que les cinq pointes laissent un oeil magenta ouvert
#: au centre (rayon ~0,27 m) : c'est par la que le noyau se voit de face, et
#: c'est ce qui fait du point faible une cible evidente. Un petale plus long
#: refermait l'iris en dome et masquait le noyau.
PETAL_LEN = 0.86
#: (s le long du petale, demi-largeur, demi-epaisseur). Les largeurs sont
#: bornees par le pas de 72 deg de l'iris : au-dela, les petales
#: s'interpenetrent au lieu de se cotoyer.
PETAL_SECTIONS = (
    (0.00, 0.365, 0.052),
    (0.15, 0.395, 0.048),   # epaulement, le plus large
    (0.36, 0.345, 0.040),
    (0.55, 0.270, 0.032),
    (0.68, 0.175, 0.024),
)
PETAL_RIDGE = 0.045       # arete centrale bombee sur le dos du petale
#: Repartition transversale des sommets d'une section (fraction de demi-largeur).
PETAL_CROSS = (-1.0, -0.60, -0.26, 0.0, 0.26, 0.60, 1.0)

# ==========================================================================
# Bras (trois, asymetriques : c'est la signature du Choeur Nul)
# ==========================================================================

#: Faux : chaine de vertebres, epaule arriere babord, arc au-dessus du corps.
SCYTHE_PATH = (
    (0.98, 1.48, 0.44),
    (1.30, 1.05, 0.60),
    (1.58, 0.52, 0.70),
    (1.76, -0.06, 0.74),
    (1.86, -0.66, 0.72),
    (1.88, -1.24, 0.66),
    (1.80, -1.78, 0.58),
    (1.62, -2.22, 0.50),
)
SCYTHE_R = (0.20, 0.19, 0.175, 0.165, 0.155, 0.145, 0.135, 0.125)

#: Lame en croissant : ces points sont l'ame de la lame ; le dos deborde de
#: `BLADE_BACK` vers l'exterieur (c'est lui qui porte l'extreme +X du modele).
#: Au crochet de la lame, le dos regarde vers l'avant : c'est lui, et non la
#: pointe, qui limite la reprise de la lame en Y (il doit rester en retrait du
#: bec, qui porte le min Y). D'ou le renflement decroissant en fin de tableau.
SCYTHE_BLADE = (
    (1.62, -2.22, 0.50),
    (1.88, -2.58, 0.46),
    (2.008, -2.94, 0.42),
    (1.90, -3.20, 0.38),
    (1.64, -3.30, 0.34),
    (1.30, -3.28, 0.31),
    (1.00, -3.14, 0.29),
)
BLADE_BACK = (0.10, 0.20, 0.27, 0.22, 0.13, 0.08, 0.03)   # epaisseur du dos
BLADE_EDGE = (0.14, 0.30, 0.40, 0.42, 0.38, 0.28, 0.09)   # portee du tranchant
BLADE_TH = (0.130, 0.115, 0.100, 0.090, 0.075, 0.055, 0.028)

#: Griffe tribord : longue, sortante — sa serre externe porte l'extreme -X.
#: Le montage est sur le FLANC (a demi noye dans la carapace), pas sur le dos.
CLAW_R_PATH = (
    (-1.30, -0.78, 0.14),
    (-1.56, -1.16, 0.02),
    (-1.74, -1.56, -0.08),
    (-1.83, -1.96, -0.16),
    (-1.845, -2.34, -0.20),
)
CLAW_R_R = (0.17, 0.15, 0.135, 0.12, 0.11)
CLAW_R_SPREAD = (-52.0, -6.0, 34.0)   # deg (dans le plan XY) des trois serres

#: Griffe babord : plus courte, repliee vers l'axe, sous la faux.
CLAW_L_PATH = (
    (1.02, -1.34, 0.16),
    (1.08, -1.82, 0.04),
    (0.98, -2.28, -0.08),
    (0.78, -2.66, -0.16),
)
CLAW_L_R = (0.16, 0.14, 0.125, 0.11)
CLAW_L_SPREAD = (-40.0, 4.0, 46.0)

TALON_LEN = 0.38
TALON_ROOT = 0.62   # facteur d'epaisseur a la base de la serre
TALON_TIP = 0.30    # ... et a la pointe
EYE_R = 0.140       # l'oeil est une bouche de tir : il doit se voir de dessus


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

    `rotation_difference` prend l'arc le plus court : le roulis residuel est
    donc entierement determine par `direction` — reproductible.
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
) -> None:
    """Bras articule : vertebres + articulations + veines magenta.

    Le rendu segmente de la planche vient de la geometrie (une boite par
    vertebre, une sphere par articulation), pas d'une texture.
    """
    for i in range(len(path) - 1):
        a, b = Vector(path[i]), Vector(path[i + 1])
        r0, r1 = radii[i], radii[i + 1]
        rad = (r0 + r1) * 0.5
        # la vertebre est legerement retractee : l'articulation la deborde
        d = (b - a)
        length = d.length
        if length < 1e-6:
            continue
        u = d / length
        seg_box(bm, a + u * rad * 0.35, b - u * rad * 0.35, rad * 0.86, rad * 0.80, material)
        # veine lumineuse dans l'interstice, sur le flanc superieur
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
    for i, point in enumerate(path):
        knuckle(bm, point, radii[i] * 0.92, joint_material)


def claw_head(bm, wrist, direction: Vector, spread: tuple, radius: float) -> Vector:
    """Griffe a oeil magenta : trois serres ivoire + un oeil emissif sous verre.

    Retourne la position de l'oeil (elle sert de bouche de tir).
    """
    wrist = Vector(wrist)
    fwd = direction.normalized()
    # base mecanique de la griffe
    knuckle(bm, wrist, radius * 1.10, "AA_Panel")

    for angle in spread:
        rot = Matrix.Rotation(math.radians(angle), 3, "Z")
        heading = rot @ fwd
        heading.z -= 0.22          # les serres plongent : elles agrippent
        heading.normalize()
        base = wrist + heading * radius * 0.55
        mid = base + heading * TALON_LEN * 0.52 + Vector((0.0, 0.0, 0.05))
        tip = mid + heading * TALON_LEN * 0.60 + Vector((0.0, 0.0, -0.10))
        seg_box(bm, base, mid, radius * TALON_ROOT, radius * TALON_ROOT * 0.90,
                "AA_Trim")
        seg_box(bm, mid, tip, radius * TALON_TIP, radius * TALON_TIP * 0.90,
                "AA_Trim")

    eye = wrist + fwd * radius * 0.28 + Vector((0.0, 0.0, radius * 0.30))
    knuckle(bm, eye, EYE_R, "AA_Emissive_Engine")
    knuckle(bm, eye + fwd * 0.030, EYE_R * 0.78, "AA_Glass")
    return eye


def sweep_rect(bm, sections: tuple, materials: tuple, cap: str = "AA_Greeble") -> list:
    """Longeron : chaine de sections rectangulaires (y, hw, z_hi, z_lo) bridees.

    Sert au bec et aux longerons du berceau, qui sont des volumes tendus, pas
    des chaines de vertebres.
    """
    rings = []
    for y, hw, z_hi, z_lo in sections:
        rings.append(
            ak.add_ring(
                bm,
                [(hw, y, z_hi), (-hw, y, z_hi), (-hw, y, z_lo), (hw, y, z_lo)],
            )
        )
    bands = []
    for i in range(len(rings) - 1):
        bands.append(ak.bridge_rings(bm, rings[i], rings[i + 1], materials[i]))
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


# ==========================================================================
# Coque principale : carapace, anneaux, bec, cou, berceau
# ==========================================================================


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
    well_rings = [top_rings[0]] + [
        polar_ring(bm, r, z, N_SEG) for r, z in WELL[1:]
    ]
    for i in range(len(well_rings) - 1):
        ak.bridge_rings(bm, well_rings[i], well_rings[i + 1], WELL_MATS[i])
    floor = bm.verts.new((0.0, 0.0, -0.11))
    ak.fan_to_point(bm, well_rings[-1], floor, "AA_Greeble")

    # --- ventre ferme -------------------------------------------------------
    belly = bm.verts.new((0.0, 0.0, -0.36))
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
    for i in range(RIM_BLOCKS):
        theta = 2.0 * math.pi * i / RIM_BLOCKS
        px, py = CARA_AX * math.cos(theta), CARA_AY * math.sin(theta)
        tx, ty = -CARA_AX * math.sin(theta), CARA_AY * math.cos(theta)
        psi = math.atan2(ty, tx)
        nrm = Vector((math.sin(psi), -math.cos(psi), 0.0))
        oriented_box(
            bm,
            Vector((px, py, 0.0)) + nrm * 0.030,
            (0.240, 0.400, 0.190),
            Matrix.Rotation(psi - math.pi / 2.0, 3, "Z"),
            "AA_Panel" if i % 2 == 0 else "AA_Greeble",
        )
    # anneau interne de tenons ivoire (deuxieme cercle de la planche)
    for i in range(12):
        theta = 2.0 * math.pi * (i + 0.5) / 12.0
        x, y = cara_xy(0.62, theta)
        oriented_box(
            bm,
            (x, y, lerp_z(Z_TOP, 0.62) + 0.030),
            (0.110, 0.190, 0.070),
            Matrix.Rotation(theta + math.pi / 2.0, 3, "Z"),
            "AA_Trim",
        )
    # ergots ivoire sur le bord (asymetriques : pas un cercle regulier)
    for deg in RIM_SPIKES:
        theta = math.radians(deg)
        px, py = CARA_AX * math.cos(theta), CARA_AY * math.sin(theta)
        nrm = Vector((px / CARA_AX**2, py / CARA_AY**2, 0.0)).normalized()
        base = Vector((px, py, 0.0))
        seg_box(bm, base - nrm * 0.06, base + nrm * 0.15, 0.105, 0.055, "AA_Trim")
        seg_box(bm, base + nrm * 0.15, base + nrm * 0.30, 0.040, 0.022, "AA_Trim")

    # --- bec blinde avant (porte le min Y de la coque) ----------------------
    sweep_rect(
        bm,
        PROW,
        ("AA_Hull", "AA_Hull", "AA_Hull", "AA_Trim", "AA_Trim"),
        cap="AA_Greeble",
    )
    # arete lumineuse sur le dos du bec
    for i in range(len(PROW) - 2):
        y0, _, zt0, _ = PROW[i]
        y1, _, zt1, _ = PROW[i + 1]
        seg_box(
            bm,
            (0.0, y0, zt0 + 0.012),
            (0.0, y1, zt1 + 0.012),
            0.030,
            0.014,
            "AA_Emissive_Engine",
        )
    # mandibules laterales du bec
    for sx in (ak.PORT, ak.STARBOARD):
        seg_box(
            bm,
            (sx * 0.62, -2.10, -0.02),
            (sx * 0.34, -3.02, -0.06),
            0.080,
            0.075,
            "AA_Greeble",
        )
        seg_box(
            bm,
            (sx * 0.34, -3.02, -0.06),
            (sx * 0.20, -3.36, -0.08),
            0.045,
            0.040,
            "AA_Trim",
        )

    # --- cou segmente -------------------------------------------------------
    limb(bm, NECK, NECK_R, "AA_Panel", glow_from=0)

    # --- berceau : deux longerons qui encadrent le module (portent max Y) ---
    for sx in (ak.PORT, ak.STARBOARD):
        sections = tuple(
            (y, 0.105, z + 0.135, z - 0.135) if i < len(CRADLE) - 1
            else (y, 0.048, z + 0.055, z - 0.055)
            for i, (x, y, z) in enumerate(CRADLE)
        )
        rings = [
            ak.add_ring(
                bm,
                [
                    (sx * CRADLE[i][0] + hw, y, z_hi),
                    (sx * CRADLE[i][0] - hw, y, z_hi),
                    (sx * CRADLE[i][0] - hw, y, z_lo),
                    (sx * CRADLE[i][0] + hw, y, z_lo),
                ],
            )
            for i, (y, hw, z_hi, z_lo) in enumerate(sections)
        ]
        mats = ("AA_Panel", "AA_Panel", "AA_Greeble", "AA_Trim")
        for i in range(len(rings) - 1):
            ak.bridge_rings(bm, rings[i], rings[i + 1], mats[i])
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
        ak.cap_ring(bm, rings[-1], "AA_Trim")

    # --- greebles : mecanique exposee sur le dos, derriere l'iris -----------
    for k, sx in enumerate((ak.PORT, ak.STARBOARD)):
        ak.greeble_strip(
            bm,
            (sx * 0.55, 1.10, lerp_z(Z_TOP, 0.45)),
            (sx * 1.05, 1.55, lerp_z(Z_TOP, 0.72)),
            count=5,
            seed=SEED + 13 * (k + 1),
            size_range=(0.050, 0.110),
            height_range=(0.030, 0.070),
        )

    return ak.new_object("Hull", bm)


# ==========================================================================
# Noyau et petales : les objets que le gameplay cible
# ==========================================================================


def build_core() -> object:
    bm = bmesh.new()
    rings = [polar_ring(bm, r, z, CORE_SEG) for r, z in CORE_RINGS]
    for i in range(len(rings) - 1):
        ak.bridge_rings(bm, rings[i], rings[i + 1], CORE_MATS[i])
    apex = bm.verts.new((0.0, 0.0, CORE_APEX_Z))
    ak.fan_to_point(bm, rings[-1], apex, "AA_Emissive_Engine")
    base = bm.verts.new((0.0, 0.0, -0.12))
    ak.fan_to_point(bm, list(reversed(rings[0])), base, "AA_Greeble")
    # nervures magenta : le noyau irradie, comme sur la planche
    for i in range(8):
        theta = 2.0 * math.pi * (i + 0.5) / 8.0
        d = Vector((math.cos(theta), math.sin(theta), 0.0))
        seg_box(
            bm,
            d * 0.10 + Vector((0.0, 0.0, 0.255)),
            d * 0.54 + Vector((0.0, 0.0, 0.075)),
            0.030,
            0.022,
            "AA_Emissive_Engine",
        )
    return ak.new_object("Core", bm)


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


def build_petal(index: int) -> object:
    """Un petale blinde de l'iris : plaque bombee, bord ivoire, couture magenta."""
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

    return ak.new_object(f"Petal_{index + 1:02d}", bm)


# ==========================================================================
# Bras
# ==========================================================================


def build_scythe() -> object:
    bm = bmesh.new()
    limb(bm, SCYTHE_PATH, SCYTHE_R, "AA_Panel")

    # lame : sections a 7 sommets — dos epais, tranchant mince et lumineux
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
    # Le fil de la lame porte une bande emissive assez LARGE dans le plan de la
    # lame (et pas seulement sur la tranche) : a 20 deg de camera, une lueur
    # posee sur la tranche est vue par la tranche, donc invisible.
    blade_mats = (
        "AA_Trim",
        "AA_Trim",
        "AA_Emissive_Engine",
        "AA_Emissive_Engine",
        "AA_Emissive_Engine",
        "AA_Emissive_Engine",
        "AA_Trim",
        "AA_Trim",
        "AA_Greeble",
    )
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Trim")
        for j, face in enumerate(band):
            if face is not None and face.is_valid:
                face.material_index = ak.mat_index(blade_mats[j])
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Trim")

    return ak.new_object("Arm_Scythe", bm)


def build_claw(name: str, path: tuple, radii: tuple, spread: tuple) -> tuple[object, Vector]:
    bm = bmesh.new()
    limb(bm, path, radii, "AA_Panel")
    heading = Vector(path[-1]) - Vector(path[-2])
    eye = claw_head(bm, path[-1], heading, spread, radii[-1] * 1.35)
    return ak.new_object(name, bm), eye


def build_pod() -> object:
    bm = bmesh.new()
    ak.add_lathe(bm, list(POD_PROFILE), POD_SEG, center_x=0.0, center_z=POD_CENTER_Z)

    # tuyeres secondaires magenta
    for deg in POD_NOZZLES:
        a = math.radians(deg)
        ak.add_lathe(
            bm,
            [
                (3.06, 0.000, "AA_Greeble"),
                (3.10, 0.120, "AA_Greeble"),
                (3.30, 0.140, "AA_Greeble"),
                (3.36, 0.155, "AA_Trim"),
                (3.40, 0.130, "AA_Emissive_Engine"),
                (3.36, 0.095, "AA_Emissive_Engine"),
                (3.34, 0.000, "AA_Emissive_Engine"),
            ],
            10,
            center_x=0.34 * math.cos(a),
            center_z=POD_CENTER_Z + 0.34 * math.sin(a),
        )

    # blindage segmente du module : huit ecailles posees a plat sur le fuseau.
    # Rotation autour de Y : R_y(pi/2 - a) amene le +Z local sur la normale
    # radiale (cos a, 0, sin a) — l'ecaille epouse la surface.
    for i in range(8):
        a = 2.0 * math.pi * (i + 0.5) / 8.0
        nrm = Vector((math.cos(a), 0.0, math.sin(a)))
        center = Vector((0.0, 2.86, POD_CENTER_Z)) + nrm * 0.50
        oriented_box(
            bm,
            center,
            (0.150, 0.480, 0.090),
            Matrix.Rotation(math.pi / 2.0 - a, 3, "Y"),
            "AA_Panel" if i % 2 == 0 else "AA_Hull",
        )
    for sx in (ak.PORT, ak.STARBOARD):
        seg_box(
            bm,
            (sx * 0.50, 3.24, POD_CENTER_Z + 0.16),
            (sx * 0.74, 3.34, POD_CENTER_Z + 0.30),
            0.030,
            0.075,
            "AA_Trim",
        )

    bmesh.ops.scale(
        bm,
        vec=Vector((1.0, 1.0, POD_FLATTEN_Z)),
        space=Matrix.Translation(Vector((0.0, 0.0, -POD_CENTER_Z))),
        verts=bm.verts[:],
    )
    return ak.new_object("Pod_Rear", bm)


# ==========================================================================
# Points d'attache
# ==========================================================================


def build_attach_points(eye_l: Vector, eye_r: Vector) -> list:
    """Positions **derivees de la geometrie**, jamais devinees.

    Les `Hinge_*` ne sont pas exiges par le brief : ils portent les pivots
    d'animation (iris, bras, module) que la transformation identite des pieces
    ne peut pas porter elle-meme. Godot les recoit en `Node3D`.
    """
    points = [
        ak.attach_point("Core_Center", (0.0, 0.0, 0.10)),
        # les tirs sortent des yeux de griffe (les bras sont asymetriques : pas
        # d'`attach_pair` ici, mais les constantes de bord du kit).
        ak.attach_point("Muzzle_L", (eye_l.x, eye_l.y - 0.16, eye_l.z)),
        ak.attach_point("Muzzle_R", (eye_r.x, eye_r.y - 0.16, eye_r.z)),
        ak.attach_point("Engine_C", (0.0, ENGINE_Y, POD_CENTER_Z)),
    ]
    for i in range(PETAL_COUNT):
        hinge, _, _, _ = _petal_frame(PETAL_ANGLES[i])
        points.append(ak.attach_point(f"Hinge_Petal_{i + 1:02d}", tuple(hinge)))
    points.append(ak.attach_point("Hinge_Arm_Scythe", SCYTHE_PATH[0]))
    points.append(ak.attach_point("Hinge_Arm_Claw_L", CLAW_L_PATH[0]))
    points.append(ak.attach_point("Hinge_Arm_Claw_R", CLAW_R_PATH[0]))
    points.append(ak.attach_point("Hinge_Pod_Rear", (0.0, POD_PROFILE[0][0], POD_CENTER_Z)))
    return points


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
    parts = [build_core()]
    parts += [build_petal(i) for i in range(PETAL_COUNT)]
    parts.append(build_scythe())
    claw_l, eye_l = build_claw("Arm_Claw_L", CLAW_L_PATH, CLAW_L_R, CLAW_L_SPREAD)
    claw_r, eye_r = build_claw("Arm_Claw_R", CLAW_R_PATH, CLAW_R_R, CLAW_R_SPREAD)
    parts += [claw_l, claw_r, build_pod()]

    for obj in [hull, *parts]:
        _finish(obj)

    # Controle en repere d'auteur, avant tout export : la coque doit porter les
    # extremes en Y (temoin d'orientation du kit), les bras les extremes en X.
    lo, hi = _bounds([hull, *parts])
    h_lo, h_hi = _bounds([hull])
    print("--- mesures en repere d'auteur (avant correction d'axe) ---")
    for obj in [hull, *parts]:
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
    if abs(h_lo.y - lo.y) > 1e-3 or abs(h_hi.y - hi.y) > 1e-3:
        raise ak.ContractError(
            "la coque ne porte pas les extremes en Y : le temoin d'orientation "
            f"du kit echouera (coque {h_lo.y:+.3f}/{h_hi.y:+.3f}, "
            f"modele {lo.y:+.3f}/{hi.y:+.3f})."
        )

    # Correction d'axe des pieces : `export_hull()` ne la fait que pour `hull`.
    # On reutilise la constante du kit (jamais une copie : une divergence ferait
    # voler la coque a reculons sans qu'aucun controle ne s'en apercoive).
    for obj in parts:
        obj.data.transform(ak._AXIS_FIX)
        obj.data.update()

    ak.export_hull(hull, [*parts, *build_attach_points(eye_l, eye_r)], OUTPUT, CONTRACT)


if __name__ == "__main__":
    main()
