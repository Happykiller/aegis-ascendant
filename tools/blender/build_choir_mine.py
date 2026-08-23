"""build_choir_mine.py — coque 3D de la Choir Mine, mine stationnaire (BRIEF-0042).

    blender45 -b -P tools/blender/build_choir_mine.py
    ./scripts/build-hull.sh --check choir_mine        # + controle de determinisme

Produit `assets/imported/models/ships/choir_mine.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (aucun alea) et s'auto-valide : `ak.export_hull()` relit le
`.glb` produit et echoue bruyamment si la bounding box, le budget de triangles,
les materiaux, le centrage du pivot ou les points d'attache sortent du contrat.

Reference de design : `assets/reference/concepts/null_choir_enemy_families_sheet.png`,
**troisieme cellule en partant du haut** : un disque radial trapu, un noyau central
en tambour a gradins concentriques coiffe d'une etoile magenta, une carapace de
grandes plaques violettes disposees en corolle autour du noyau, une couronne
peripherique d'une dizaine de modules (futs anthracite, blocs ivoire, blocs vert
maladif) et **une pointe unique** qui casse la symetrie radiale.


CE QUI DECIDE DE CETTE COQUE : ELLE DOIT LIRE COMME UN OBJET
============================================================
C'est la premiere unite du jeu qui n'est pas une machine de vol. Si le joueur la
lit comme un petit vaisseau, il essaiera de l'esquiver au lieu de la traiter comme
un obstacle. Quatre partis pris servent exclusivement cette lecture :

1. **Epaisseur assumee** : 0,50 m pour 1,15 m de diametre, soit 43 % — trois fois
   le ratio d'un chasseur (ADR-0008 vise 15-25 % de la longueur, regle ecrite pour
   des cellules d'avion). Vu de dessus, c'est l'epaisseur qui distingue un galet
   d'une aile. Derogation ASSUMEE, demandee par le brief.
2. **Aucune direction de marche** : pas de nez, pas de tuyere, pas de `Engine_C`
   (le brief l'interdit explicitement) — donc pas de plume d'echappement en jeu.
   Rien dans la silhouette ne dit « je vais quelque part ».
3. **Symetrie radiale d'ordre 6** cassee par UN seul accident (la pointe en -Y).
   Un vaisseau est bilateral ; un objet est radial. La pointe evite la roue dentee.
4. **Couronne de modules greffes** : la peripherie est faite de pieces rapportees
   (futs, caissons) et non d'un bord de fuite continu. Une coque de vol a des
   bords ; une machine posee a des accessoires boulonnes.

Ou va le detail : la camera de jeu regarde a 20 deg de la VERTICALE. Tout ce qui
compte est donc sur les surfaces superieures — plaques bombees, gradins du noyau,
veines magenta du pont, dos des futs. Les flancs verticaux ne portent que du
materiau, jamais de detail (BRIEF-0026, rappele par ADR-0011).


PIECES ARTICULEES — ET LE PIEGE QUE LE CONTRAT NE VOIT PAS
==========================================================
Six `Segment_01..06` sont exportes en nœuds separes (`ak.moving_part`), origine
**sur leur charniere** : le bord INTERIEUR de la plaque, cote noyau, au ras du pont
(r = 0,262 m, z = 0,148 m en repere d'auteur). Une piece dont l'origine reste a
zero decrirait un arc autour du centre du disque au lieu de s'articuler, et
`export_hull()` la validerait sans un mot : la bounding box au repos est parfaite
dans les deux cas (`.claude/resources/pratique-detail-en-fraction-de-corde.md`).

Le jeu (`scripts/enemies/enemy_pose.gd`) DEDUIT l'axe de charniere de la position
du nœud : tangente horizontale au cercle, `axis = (-r.z, 0, r.x)`. Un angle positif
souleve le bord exterieur : la carapace s'ouvre en corolle vers le haut, ce qui
degage le noyau au lieu de le masquer. Ce script **remesure le debattement reel a
chaque build** (`_travel_table()`), sur le maillage livre et avec exactement la
convention de `enemy_pose.gd`, et refuse d'exporter en dessous d'un plancher.

Repere d'auteur (ADR-0008) : nez -Y, dessus +Z, **babord +X** (cf. aegis_kit).
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
# Contrat
# ==========================================================================

CONTRACT = ak.HullContract(
    name="Choir Mine",
    width_x=1.15,       # Godot X — impose par le brief
    length_z=1.15,      # Godot Z — impose par le brief
    max_height_y=0.55,  # Godot Y — derogation assumee (brief) : 0,45 a 0,55
    tri_budget=6_000,   # moitie du plafond « ennemi leger » d'ADR-0011
    required_materials=ak.MATERIAL_ORDER,  # les 7 : cf. plan de materiaux
    required_attach_points=("Muzzle_C",),  # et surtout PAS de Engine_C
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/ships/choir_mine.glb")

#: Rayon d'enveloppe : c'est lui qui porte les 1,15 m de large ET de long.
R_ENV = 0.575

TEXELS_PER_METER = 4.0  # depliage par projection (ADR-0011), comme le Specter-9

# ==========================================================================
# Corps : galet lenticulaire de revolution autour de Z
# ==========================================================================

#: (z, rayon, materiau de la bande sortante). Le materiau d'un point s'applique
#: a la bande qui part de ce point vers le suivant.
#: Lu de bas en haut : culot, ventre, ceinture d'equateur (le maitre-couple),
#: epaulement (l'assise des modules), talus du pont, gorge magenta, puits du noyau.
BODY: list[tuple[float, float, str]] = [
    (-0.230, 0.000, "AA_Greeble"),          # pole bas : culot mecanique
    (-0.210, 0.140, "AA_Hull"),             # ventre : c'est du BLINDAGE, pas de la
    (-0.160, 0.278, "AA_Hull"),             # machinerie (cf. repartition, SS8 du rapport)
    (-0.085, 0.386, "AA_Panel"),
    (-0.010, 0.440, "AA_Hull"),             # equateur — maitre-couple
    (0.045, 0.436, "AA_Hull"),
    (0.090, 0.404, "AA_Hull"),              # epaulement : assise des modules
    (0.118, 0.340, "AA_Greeble"),           # talus du pont
    (0.135, 0.268, "AA_Emissive_Engine"),   # gorge magenta (visible par les fentes)
    (0.137, 0.252, "AA_Greeble"),           # ... et volontairement ETROITE : large,
    (0.138, 0.238, "AA_Greeble"),           # elle faisait une cible concentrique
    (0.140, 0.212, "AA_Greeble"),           # levre du puits, contre le noyau
    (0.143, 0.000, "AA_Greeble"),           # plancher du puits (noye sous le noyau)
]
BODY_SEGMENTS = 24  # multiple de 6 et de 12 : les fentes et les modules tombent juste

# ==========================================================================
# Noyau : tambour a gradins concentriques, coiffe d'une etoile magenta
# ==========================================================================

#: (z, rayon, materiau) — alternance paroi verticale / anneau horizontal, ce qui
#: donne les gradins concentriques de la planche sans une seule texture.
#: ⚠️ Le CENTRE est plein et lumineux, les anneaux sont fins. Le premier jet
#: faisait l'inverse (anneau magenta large, pupille minuscule au fond d'une
#: lentille sombre) : reduit a 46 px — sa taille reelle en jeu — la mine lisait
#: comme un DONUT, et c'est l'anneau qui pulsait, pas le cœur. Ce que le jeu fait
#: respirer doit etre la tache la plus brillante et la plus compacte de l'objet.
CORE: list[tuple[float, float, str]] = [
    (0.130, 0.205, "AA_Greeble"),           # paroi du socle
    (0.188, 0.205, "AA_Panel"),             # gradin violet
    (0.188, 0.176, "AA_Greeble"),           # paroi
    (0.206, 0.176, "AA_Emissive_Engine"),   # filet magenta (halo de repos)
    (0.206, 0.158, "AA_Greeble"),           # paroi
    (0.222, 0.158, "AA_Trim"),              # filet ivoire
    (0.222, 0.136, "AA_Greeble"),           # paroi
    (0.238, 0.136, "AA_Glass"),             # membrane sombre : le cerne du cœur
    (0.238, 0.108, "AA_Glass"),             # paroi
    (0.250, 0.108, "AA_Emissive_Engine"),   # dome du cœur (216 mm de diametre)
    (0.272, 0.000, "AA_Emissive_Engine"),   # pole : point haut de la coque
]
CORE_SEGMENTS = 16

# ==========================================================================
# Carapace : six plaques articulees
# ==========================================================================

SEG_COUNT = 6
#: Les plaques sont centrees a 30 + 60k deg, donc les SIX FENTES tombent a
#: 0, 60, 120... : elles pointent exactement sur un module de la couronne, et la
#: veine magenta qui court dans la fente file droit sur lui.
SEG_ANGLES = tuple(30.0 + 60.0 * k for k in range(SEG_COUNT))

SEG_HINGE_R = 0.262   # rayon de la charniere (bord interieur, cote noyau)
SEG_HINGE_Z = 0.148   # hauteur de la charniere : au ras du pont

#: (rayon, z du dessus, z du dessous, demi-largeur tangentielle).
#: La demi-largeur est donnee en METRES et non en degres : une plaque en part de
#: tarte garde une largeur ANGULAIRE constante, et deux voisines se rejoignent des
#: qu'elles se soulevent (leur rayon apparent diminue, leur angle grossit). Une
#: plaque en petale — large au milieu, retrecie au bout — gagne ~20 deg de
#: debattement pour la meme silhouette. C'est mesure plus bas, pas suppose.
SEG_SECTIONS: tuple[tuple[float, float, float, float], ...] = (
    (0.262, 0.206, 0.148, 0.104),   # emplanture, sur la charniere
    (0.310, 0.202, 0.142, 0.140),
    (0.360, 0.188, 0.130, 0.165),   # maitre-couple de la plaque
    (0.410, 0.163, 0.113, 0.168),
    (0.450, 0.132, 0.095, 0.158),
    (0.482, 0.098, 0.082, 0.120),   # levre exterieure
)
SEG_CROSS = (-1.0, -0.5, 0.0, 0.5, 1.0)  # 5 abscisses transversales
#: Bombe du dos. Le premier jet valait 0,012 : au rendu, les six plaques lisaient
#: comme des coussins gonfles et non comme du blindage (le chanfrein + le lissage
#: par angle ajoutent leur propre rondeur par-dessus). 0,007 garde le galbe qui
#: accroche la lumiere sans la boursouflure.
SEG_RIDGE = 0.007

#: Les deux plaques a levre ivoire. La planche ne montre pas six plaques
#: identiques : deux eclats clairs cassent la ronde. Choix fixe (donc deterministe)
#: et volontairement NON OPPOSE — (1, 4) et (0, 3) seraient diametralement
#: symetriques et ne casseraient rien.
SEG_IVORY = (1, 3)

#: Plaques dont le panneau EXTERIEUR reste en anthracite au lieu de passer en
#: violet. Sans elles, les six dos violets couvraient le disque d'un aplat clair
#: continu : la mine lisait plus lumineuse que la planche, qui est sombre.
SEG_DARK_OUTER = (0, 4, 5)

# ==========================================================================
# Couronne peripherique : 12 postes a 30 deg, dont 11 modules et LA pointe
# ==========================================================================

CROWN_STEP = 30.0
SPIKE_SLOT = 9           # 9 x 30 = 270 deg = -Y : la pointe regarde le joueur

#: type de module par poste (le poste 9 est la pointe). L'alternance n'est pas
#: reguliere : trois ivoires et deux verts poses de facon inegale, comme la
#: planche, pour que la couronne ne lise pas comme une denture de roue.
CROWN_KIND: dict[int, str] = {
    0: "drum", 1: "ivory", 2: "drum", 3: "olive", 4: "drum", 5: "ivory",
    6: "drum", 7: "olive", 8: "drum", 10: "drum", 11: "drum",
}

#: Facteur d'echelle transversale par poste. Les deux postes qui encadrent la
#: pointe (8 et 10) sont volontairement greles : sans cela, la pointe se noyait
#: dans une couronne de modules tous identiques et ne cassait plus rien.
CROWN_SCALE: dict[int, float] = {8: 0.62, 10: 0.62}

#: Rentre certains postes vers l'axe. Les deux voisins de la pointe reculent de
#: 10 % : la pointe depasse alors franchement d'un secteur en retrait, au lieu
#: d'affleurer une couronne parfaitement circulaire. C'est ce qui la fait exister
#: en vue de jeu, ou elle ne mesure qu'une poignee de pixels.
CROWN_REACH: dict[int, float] = {8: 0.88, 10: 0.88}

#: Les seuls futs qui portent une frette ivoire. Toutes les frettes allumees
#: faisaient une denture chromee tout autour du disque.
DRUM_BANDED = (2, 6, 11)

#: Fut : (rayon sur l'axe radial, demi-rayon du fut). Le poste 0 (+X), le poste 6
#: (-X) et le poste 3 (+Y) portent l'enveloppe : leur derniere station est
#: exactement a R_ENV, ce qui donne la largeur ET la longueur hors-tout.
DRUM: tuple[tuple[float, float], ...] = (
    (0.400, 0.070),   # noye dans la coque
    (0.455, 0.082),
    (0.500, 0.086),
    (0.548, 0.082),
    (0.560, 0.066),
    (R_ENV, 0.040),   # face exterieure
)
DRUM_Z = -0.030       # centre du fut : sous l'epaulement, dos visible de dessus
DRUM_PROFILE_SIDES = 10
DRUM_BANDS = ("AA_Greeble", "AA_Greeble", "AA_Trim", "AA_Greeble", "AA_Greeble")

#: Caisson : (rayon, demi-largeur, demi-hauteur).
BLOCK: tuple[tuple[float, float, float], ...] = (
    (0.400, 0.085, 0.074),
    (0.470, 0.090, 0.080),
    (0.545, 0.082, 0.072),
    (R_ENV, 0.062, 0.052),
)
BLOCK_Z = -0.022

#: Pointe : (rayon, demi-largeur, demi-hauteur, z du centre). Elle sort de
#: l'epaulement, s'effile, et se releve legerement (z croissant) pour rester
#: LISIBLE DE DESSUS — une pointe horizontale disparait sous la camera de jeu.
#: ⚠️ Le z de la pointe est BORNE PAR LA PLAQUE QUI LA COIFFE : -Y tombe au centre
#: de `Segment_05`, pas dans une fente (les fentes sont a 0, 60, 120...). Un premier
#: reglage plus haut a fait mordre la plaque au repos — le harnais de debattement
#: l'a refuse (limite -1 deg) la ou la bounding box, elle, restait parfaite.
SPIKE: tuple[tuple[float, float, float, float], ...] = (
    (0.300, 0.116, 0.086, -0.040),   # emplanture, noyee dans la coque
    (0.404, 0.104, 0.076, -0.020),
    (0.478, 0.074, 0.056, 0.000),
    (0.542, 0.038, 0.032, 0.020),
    (R_ENV, 0.012, 0.012, 0.030),    # pointe : min Y d'auteur -> min Z Godot
)
#: Hexagone pose sur une facette (et non sur un sommet) : la facette 0 est le
#: dessus, c'est elle qu'on coiffe d'ivoire pour que la pointe existe de dessus.
SPIKE_PROFILE = (
    (0.50, 0.87), (-0.50, 0.87), (-1.00, 0.00),
    (-0.50, -0.87), (0.50, -0.87), (1.00, 0.00),
)

# ==========================================================================
# Veines magenta du pont (dans les fentes entre plaques)
# ==========================================================================

#: (rayon, demi-largeur, demi-hauteur). Posees SUR le talus du pont, dont elles
#: suivent la pente : leur z est lu dans `BODY` (`_deck_z`), jamais ecrit en dur
#: (`.claude/resources/pratique-detail-en-fraction-de-corde.md`).
VEIN: tuple[tuple[float, float, float], ...] = (
    (0.232, 0.010, 0.005),
    (0.300, 0.008, 0.005),
    (0.360, 0.007, 0.004),
    (0.424, 0.004, 0.004),
)
VEIN_LIFT = 0.005     # la veine affleure au-dessus du pont

#: Couture magenta sur le dos de chaque plaque : (rayon, demi-largeur, demi-hauteur).
SEAM: tuple[tuple[float, float, float], ...] = (
    (0.274, 0.007, 0.005),
    (0.380, 0.006, 0.005),
    (0.474, 0.004, 0.004),
)
SEAM_LIFT = 0.004

#: Bouche de tir : sur l'axe, au CŒUR du noyau (mi-hauteur du tambour). La mine
#: tire une couronne complete depuis son cœur, pas depuis un canon.
MUZZLE_Z = 0.200

# ==========================================================================
# Debattement : plancher exige, pas de valeur ecrite a la main
# ==========================================================================

#: Le jeu plafonne l'ouverture a 85 deg (`EnemyPose.MAX_OPEN_DEG`). On refuse
#: d'exporter une carapace qui n'offrirait pas au moins ce debattement utile.
TRAVEL_FLOOR_DEG = 45.0
TRAVEL_STEP_DEG = 1.0
TRAVEL_MAX_DEG = 90.0
#: Rayon d'exclusion autour de la charniere. Une articulation reelle
#: s'interpenetre par construction dans son logement ; ce qui doit degager, c'est
#: tout le reste. Ici la plaque est POSEE au-dessus du pont (elle ne s'emboite pas),
#: donc 12 mm suffisent : de quoi ignorer le seul chanfrein de l'arete de charniere.
HINGE_SKIP = 0.012


# ==========================================================================
# Helpers geometriques — uniquement des primitives du kit, kit non modifie
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

    `sections` : (centre, demi-vecteur transversal, demi-vecteur vertical).
    Le module radial, le caisson, la pointe, la veine et la couture sortent tous
    d'ici : une seule primitive locale, batie sur `add_ring`/`bridge_rings`/
    `cap_ring` du kit — le kit n'est pas modifie.
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


def _radial_sections(
    theta_deg: float, table, z_of
) -> list[tuple[Vector, Vector, Vector]]:
    """Stations d'une piece greffee sur le rayon `theta_deg`.

    `table` : lignes commencant par (rayon, demi-largeur, ...) ; `z_of(row)` donne
    la hauteur du centre et `row[2]` la demi-hauteur. Tout est exprime en fonction
    du rayon, donc un changement de galbe du corps deplace la piece avec lui.
    """
    radial, tangent, up = _frame(theta_deg)
    out = []
    for row in table:
        r, half_w = row[0], row[1]
        half_h = row[2] if len(row) > 2 else half_w
        out.append((radial * r + up * z_of(row), tangent * half_w, up * half_h))
    return out


def _circle(sides: int) -> tuple[tuple[float, float], ...]:
    """Profil circulaire unitaire, premiere arete en haut (dos du fut)."""
    return tuple(
        (
            math.cos(2.0 * math.pi * (i + 0.5) / sides),
            math.sin(2.0 * math.pi * (i + 0.5) / sides),
        )
        for i in range(sides)
    )


_SQUARE = ((1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0), (1.0, -1.0))


def _lerp_table(pairs: list[tuple[float, float]], x: float) -> float:
    """Interpolation lineaire, extremites clampees."""
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


#: Dessus du corps, du puits vers l'equateur — la source de verite du pont.
_DECK = [(r, z) for z, r, _ in BODY if z >= -0.010][::-1]


def _deck_z(radius: float) -> float:
    """Hauteur du pont au rayon donne (lue dans `BODY`, jamais ecrite en dur)."""
    return _lerp_table(_DECK, radius)


def _seg_top(radius: float) -> float:
    """Hauteur du dos d'une plaque au rayon donne (lue dans `SEG_SECTIONS`)."""
    return _lerp_table([(r, zt) for r, zt, _, _ in SEG_SECTIONS], radius)


# ==========================================================================
# Coque fixe : corps, noyau, couronne, pointe, veines
# ==========================================================================


def _crown_drum(bm: bmesh.types.BMesh, slot: int, scale: float, reach: float) -> None:
    sections = _radial_sections(
        slot * CROWN_STEP,
        [(r * reach, hr * scale, hr * scale) for r, hr in DRUM],
        lambda row: DRUM_Z,
    )
    bands = _sweep(
        bm, sections, _circle(DRUM_PROFILE_SIDES),
        DRUM_BANDS if slot in DRUM_BANDED else ("AA_Greeble",) * (len(DRUM) - 1),
        cap_first="AA_Greeble", cap_last="AA_Greeble",
    )
    # Bouchon de fut : un anneau enfonce sur la face exterieure ferait du detail
    # invisible (flanc vertical). Le seul detail paye ici est le dos du fut, vu de
    # dessus : on y enfonce la bande centrale.
    ak.inset_panel(bm, [bands[2][0]], "AA_Panel", thickness=0.006, depth=-0.006)


def _crown_block(
    bm: bmesh.types.BMesh, slot: int, scale: float, reach: float, material: str
) -> None:
    sections = _radial_sections(
        slot * CROWN_STEP,
        [(r * reach, hw * scale, hh * scale) for r, hw, hh in BLOCK],
        lambda row: BLOCK_Z,
    )
    bands = _sweep(
        bm, sections, _SQUARE, (material,) * (len(BLOCK) - 1),
        cap_first="AA_Greeble", cap_last="AA_Greeble",
    )
    # Face 0 de chaque bande = le dessus (profil carre, premier cote en haut).
    ak.inset_panel(
        bm, [bands[i][0] for i in range(len(bands))], "AA_Greeble",
        thickness=0.010, depth=-0.006,
    )


def _spike(bm: bmesh.types.BMesh) -> None:
    """LA rupture asymetrique : une corne unique, pointee sur le joueur (-Y)."""
    sections = _radial_sections(
        SPIKE_SLOT * CROWN_STEP,
        [(r, hw, hh, zc) for r, hw, hh, zc in SPIKE],
        lambda row: row[3],
    )
    bands = _sweep(
        bm, sections, SPIKE_PROFILE, ("AA_Panel",) * (len(SPIKE) - 1),
        cap_first="AA_Greeble", cap_last="AA_Trim",
    )
    # Facette 0 = le dessus : ivoire, seule surface de la pointe que le joueur voit.
    for band in bands:
        ak.set_material([band[0]], "AA_Trim")


def _vein(bm: bmesh.types.BMesh, theta_deg: float) -> None:
    """Veine magenta dans une fente, posee sur la pente du pont."""
    sections = _radial_sections(
        theta_deg, VEIN, lambda row: _deck_z(row[0]) + VEIN_LIFT
    )
    _sweep(
        bm, sections, _SQUARE, ("AA_Emissive_Engine",) * (len(VEIN) - 1),
        cap_first="AA_Emissive_Engine", cap_last="AA_Emissive_Engine",
    )


def build_hull() -> object:
    bm = bmesh.new()

    ak.add_lathe(bm, BODY, BODY_SEGMENTS, axis="Z")
    ak.add_lathe(bm, CORE, CORE_SEGMENTS, axis="Z")

    for slot, kind in sorted(CROWN_KIND.items()):
        scale = CROWN_SCALE.get(slot, 1.0)
        reach = CROWN_REACH.get(slot, 1.0)
        if kind == "drum":
            _crown_drum(bm, slot, scale, reach)
        else:
            _crown_block(
                bm, slot, scale, reach,
                "AA_Trim" if kind == "ivory" else "AA_Marking_Red",
            )

    _spike(bm)

    # Les six fentes : a 0, 60, 120... (entre deux plaques), donc pile sur un poste
    # de couronne. La veine relie le noyau au module : le disque se lit comme un
    # circuit, pas comme une roue.
    for k in range(SEG_COUNT):
        _vein(bm, k * 60.0)

    return ak.new_object("ChoirMine_Hull", bm)


# ==========================================================================
# Plaques articulees
# ==========================================================================


def build_segment(index: int) -> ak.MovingPart:
    """Une plaque de carapace, batie en coordonnees ABSOLUES, origine sur sa charniere.

    Section transverse (5 abscisses) : dos bombe + dessous plat, refermes par deux
    tranches. `bridge_rings` donne des indices de face stables :
      0..3   dos       4 tranche +k      5..8 dessous       9 tranche -k
    """
    bm = bmesh.new()
    theta = SEG_ANGLES[index]
    radial, tangent, up = _frame(theta)

    rings = []
    for r, z_top, z_bot, half_w in SEG_SECTIONS:
        top, bottom = [], []
        for k in SEG_CROSS:
            base = radial * r + tangent * (k * half_w)
            crest = SEG_RIDGE * (1.0 - k * k)
            top.append(tuple(base + up * (z_top + crest)))
            bottom.append(tuple(base + up * (z_bot - crest * 0.35)))
        rings.append(ak.add_ring(bm, top + list(reversed(bottom))))

    bands = []
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        ak.set_material([band[j] for j in (4, 5, 6, 7, 8, 9)], "AA_Greeble")
        bands.append(band)

    lip = "AA_Trim" if index in SEG_IVORY else "AA_Hull"
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")   # tranche interieure
    ak.cap_ring(bm, rings[-1], lip)                           # levre exterieure
    ak.set_material([bands[-1][j] for j in (0, 1, 2, 3)], lip)

    # Deux panneaux enfonces sur le dos : c'est le joint entre eux qui fait lire
    # une carapace segmentee (charte SS4) plutot qu'une ecaille peinte. Le liston
    # anthracite laisse autour (16 mm) est ce qui empeche le dos de lire comme un
    # aplat viole d'un bord a l'autre.
    for lo, hi, fill in (
        (0, 2, "AA_Panel"),
        (2, 4, "AA_Hull" if index in SEG_DARK_OUTER else "AA_Panel"),
    ):
        ak.inset_panel(
            bm,
            [bands[b][j] for b in range(lo, hi) for j in (0, 1, 2, 3)],
            fill, thickness=0.016, depth=-0.009,
        )

    # Couture magenta le long de la crete : la plaque « fuit » de la lumiere, et
    # elle emporte sa fuite quand elle s'ouvre (c'est une piece mobile).
    _sweep(
        bm,
        _radial_sections(
            theta, SEAM, lambda row: _seg_top(row[0]) + SEG_RIDGE + SEAM_LIFT
        ),
        _SQUARE,
        ("AA_Emissive_Engine",) * (len(SEAM) - 1),
        cap_first="AA_Emissive_Engine",
        cap_last="AA_Emissive_Engine",
    )

    hinge = radial * SEG_HINGE_R + up * SEG_HINGE_Z
    return ak.moving_part(f"Segment_{index + 1:02d}", bm, tuple(hinge))


# ==========================================================================
# Points d'attache
# ==========================================================================


def build_attach_points() -> list:
    # PAS de Engine_C : une mine n'a pas de moteur, et le controleur ne pose une
    # plume d'echappement que si la coque en declare un (brief SS« Points d'attache »).
    return [ak.attach_point("Muzzle_C", (0.0, 0.0, MUZZLE_Z))]


# ==========================================================================
# Harnais de debattement — remesure a chaque build, sur le maillage livre
# ==========================================================================

#: (x, y, z)_auteur -> (-x, z, y)_Godot : la chaine appliquee par `export_hull`.
_TO_GODOT = Matrix(((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)))


def _hinge_axis(position: Vector) -> Vector:
    """Copie EXACTE de `EnemyPose._hinge_axis` (scripts/enemies/enemy_pose.gd).

    Mesurer avec une autre convention que celle du jeu ne mesurerait rien : c'est
    le jeu qui pose la piece, pas ce script.
    """
    radial = Vector((position.x, position.z))
    if radial.length_squared < 1e-6:
        return Vector((1.0, 0.0, 0.0))
    radial.normalize()
    return Vector((-radial.y, 0.0, radial.x))


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


class Solid:
    """Soupe de triangles figee, prete a repondre « a quelle distance ? »."""

    def __init__(self, verts: list, tris: list):
        self.verts = verts
        self.tris = tris
        self.tree = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)

    def distance_to(self, verts: list, tris: list) -> float:
        """Distance minimale a une autre soupe ; 0.0 si elles se mordent.

        Les deux sens de requete : un sommet mobile pres d'une face fixe ET un
        sommet fixe pres d'une face mobile. Un seul sens laisserait passer une
        plaque mince qui traverse une grande face sans qu'un sommet n'en approche.
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


def _travel_table(hull, parts: list) -> list[tuple]:
    """Debattement mecanique de chaque plaque, mesure sur le maillage livre.

    Reproduit exactement `EnemyPose.pose()` : origine sur la charniere, axe deduit
    de la position du nœud, `Basis(axe, angle)`, meme angle pour les six plaques.
    Rend, par plaque : (nom, pivot Godot, angle limite, obstacle, marge a l'angle
    retenu).
    """
    names = [p.obj.name for p in parts]
    pivot = {p.obj.name: _TO_GODOT @ Vector(p.pivot) for p in parts}
    axis = {n: _hinge_axis(pivot[n]) for n in names}

    local, tris, hull_solid = {}, {}, {}
    for part in parts:
        name = part.obj.name
        verts, faces = _soup(part.obj, pivot[name], HINGE_SKIP)
        local[name] = [v - pivot[name] for v in verts]
        tris[name] = faces
        # La coque est amputee de la meme sphere de charniere, des DEUX cotes :
        # une rotation autour d'un axe passant par le pivot conserve la distance
        # au pivot, donc rien de ce qui est exclu ne peut rencontrer le reste.
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
                worst, who = d, "coque fixe (noyau/pont)"
            for other in (names[(i + 1) % len(names)], names[(i - 1) % len(names)]):
                d = solids[other].distance_to(posed[name], tris[name])
                if d < worst:
                    worst, who = d, f"voisine {other}"
            margin_at[name][deg] = (worst, who)
            if worst <= 0.0 and limit[name] > deg:
                limit[name] = deg - TRAVEL_STEP_DEG
                blocker[name] = who

    rows = []
    for part in parts:
        name = part.obj.name
        rows.append((name, pivot[name], limit[name], blocker[name], margin_at[name]))
    return rows


def _report_travel(rows: list[tuple]) -> None:
    print("--- debattement mecanique mesure (convention EnemyPose, pas fixe) ---")
    worst = 360.0
    for name, pivot, limit, blocker, margins in rows:
        m45 = margins.get(45.0, (0.0, ""))[0] * 1000.0
        m60 = margins.get(60.0, (0.0, ""))[0] * 1000.0
        print(
            f"  {name}  pivot Godot ({pivot.x:+.4f}, {pivot.y:+.4f}, {pivot.z:+.4f})"
            f"  limite {limit:5.1f} deg  [{blocker}]"
            f"  marge a 45 deg {m45:6.1f} mm | a 60 deg {m60:6.1f} mm"
        )
        worst = min(worst, limit)
    print(f"  -> debattement retenu (le plus contraint des six) : {worst:.1f} deg")
    if worst < TRAVEL_FLOOR_DEG:
        raise ak.ContractError(
            f"debattement insuffisant : {worst:.1f} deg < plancher "
            f"{TRAVEL_FLOOR_DEG:.1f} deg — la carapace s'auto-intersecterait "
            "avant d'etre ouverte."
        )


# ==========================================================================
# Assemblage
# ==========================================================================


def _triangulate_ngons(obj) -> None:
    """Decoupe les seules faces de plus de 4 sommets — et rien d'autre.

    Sans cela, l'exporteur renonce aux TANGENTES (« tangent space can only be
    computed for tris/quads ») et ADR-0011 devient inoperant sur cette coque :
    une feuille de detail sans tangentes n'a aucun support de normal map. Les
    n-gons viennent des `cap_ring` (tranches de plaque, culots de fut) ; les quads
    sont conserves tels quels, mikktspace les accepte. Le nombre de triangles a
    l'export est inchange — l'exporteur triangulait deja, mais trop tard.
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
    # Chanfrein a 1 segment : sur un objet radial de 6 000 triangles, on ne paie
    # que les aretes qui portent la lecture (gradins du noyau, bords de plaque,
    # levres de fut). Le lissage par angle fait le reste.
    ak.bevel_sharp_edges(obj, width=0.005, segments=1, angle_deg=33.0)
    _triangulate_ngons(obj)
    # 24 deg et non 33 : au premier rendu, les plaques et les futs lissaient en
    # plastique mou. Un objet mecanique doit garder ses facettes ; seul le galbe
    # des plaques et la revolution du corps meritent d'etre fondus.
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


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)

    hull = build_hull()
    parts = [build_segment(i) for i in range(SEG_COUNT)]

    _finish(hull)
    for part in parts:
        _finish(part.obj)

    objs = [hull] + [p.obj for p in parts]
    lo, hi = _bounds(objs)
    print("--- mesures en repere d'auteur (avant correction d'axe) ---")
    for obj in objs:
        o_lo, o_hi = _bounds([obj])
        print(
            f"  {obj.name:<16} x[{o_lo.x:+.3f} {o_hi.x:+.3f}] "
            f"y[{o_lo.y:+.3f} {o_hi.y:+.3f}] z[{o_lo.z:+.3f} {o_hi.z:+.3f}] "
            f"{len(obj.data.polygons)} faces"
        )
    print(
        f"  TOTAL            x[{lo.x:+.3f} {hi.x:+.3f}] y[{lo.y:+.3f} {hi.y:+.3f}] "
        f"z[{lo.z:+.3f} {hi.z:+.3f}]  ->  {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} "
        f"x {hi.z - lo.z:.3f} m"
    )

    _report_travel(_travel_table(hull, parts))

    ak.export_hull(hull, build_attach_points(), OUTPUT, CONTRACT, parts=parts)


if __name__ == "__main__":
    main()
