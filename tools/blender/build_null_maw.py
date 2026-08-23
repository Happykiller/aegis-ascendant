"""build_null_maw.py — coque 3D du Null Maw, ennemi leger du Choeur Nul (BRIEF-0043).

    blender45 -b -P tools/blender/build_null_maw.py

Produit `assets/imported/models/ships/null_maw.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne. Il
est deterministe (aucun alea), s'auto-valide via `ak.export_hull()` — bounding box,
budget de triangles, materiaux, centrage du pivot, points d'attache — et refuse
d'exporter si une piece mobile mord la coque ou sa voisine.


CE QUE CETTE COQUE DOIT ETRE, ET SURTOUT CE QU'ELLE NE DOIT PAS ETRE
====================================================================
Le Null Maw est une **variante de famille de la Choir Mine** : meme faction, meme
palette, meme classe d'objet, meme vocabulaire de carapace segmentee. Le seul test
qui compte est donc negatif : *distingue-t-on les deux en aplat noir, vu de dessus,
a petite taille ?* Quatre partis pris repondent oui, et chacun s'oppose terme a
terme a la mine (tableau du BRIEF-0043) :

1. **Le centre est un TROU, pas un noyau.** Le puits est un percement REEL et
   TRAVERSANT de la coque (rayon 0,160 m au plus etroit) : vu de dessus on voit le
   fond de l'espace au travers, et l'aplat noir montre un anneau, pas un disque.
   Le magenta **borde** ce vide (levre + haut de gorge) ; il ne le remplit jamais.
   Un emissif central plein aurait reconstitue le noyau d'une mine — exactement ce
   que le brief interdit.
2. **Cinq petales de longueurs franchement inegales** (0,26 a 0,52 m) a des
   azimuts **irreguliers** (ecarts de 56 a 110 deg) : la silhouette est une fleur
   dentelee et asymetrique, pas une couronne reguliere (charte 4 : le Choeur Nul
   est asymetrique).
3. **La coque est ouverte** : entre les petales, on voit au travers jusqu'a
   l'anneau d'accretion, 15 cm plus bas. Une mine est pleine et ramassee.
4. **1,45 m au lieu de 1,15 m** : plus large, donc plus dangereuse — le signal de
   taille porte une information juste (plus de portee, plus de points de vie).

Le vocabulaire de FAMILLE est conserve, sinon les deux unites n'appartiendraient
plus au meme peuple : anneaux de plaques concentriques sur le collier, carapace
ivoire, greebles vert maladif tres limites, et surtout les **fissures magenta
rayonnantes** de la planche — ici retournees : elles ne rayonnent plus *d'un coeur*,
elles rayonnent *d'un vide*.


LA MECANIQUE — corolle en bascule
=================================
Chaque petale est une plaque coudee, articulee sur une charniere TANGENTIELLE
posee sur le collier, **a l'exterieur du puits** (r = 0,275 m > rayon de levre
0,226 m). De part et d'autre de cette charniere :

  * vers l'exterieur, le **bras** (0,26 a 0,52 m) qui porte la silhouette ;
  * vers l'interieur, la **langue**, qui surplombe la bouche du puits.

Une seule rotation, dans le sens ou le bras descend, releve donc la langue : la
corolle s'ouvre comme une fleur, la langue se retire du puits, et l'empreinte au
sol grandit avant de se refermer. C'est la bascule demandee par le brief, pas un
couvercle qui glisse.

    angle positif = OUVERTURE (bras vers le bas, langue vers le haut)
    axe de rotation = tangentielle = up x radial, passant par le pivot

⚠️ Le piege documente dans `aegis_kit.moving_part` : une piece dont l'origine reste
a zero decrit un arc autour du centre de l'objet. Les cinq petales ont donc leur
origine SUR leur charniere. `Ring`, lui, tourne bel et bien autour du centre : son
origine reste a (0, 0, 0), et c'est correct — il ne fait que pivoter sur l'axe.

Repere d'auteur (ADR-0008) : nez -Y, dessus +Z, **babord +X** (cf. aegis_kit).
La corolle s'ouvre vers +Z, c'est-a-dire vers la camera.
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
    name="Null Maw",
    width_x=1.45,       # Godot X — impose par le brief (plus large que la mine)
    length_z=1.45,      # Godot Z
    max_height_y=0.45,  # Godot Y — derogation assumee : ce n'est pas un avion
    tri_budget=7_000,
    required_materials=ak.MATERIAL_ORDER,
    required_attach_points=("Muzzle_C",),   # PAS d'Engine_C : elle n'a pas de moteur
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/ships/null_maw.glb")

MIN_HEIGHT = 0.35   # plancher impose par le brief (le contrat ne borne que le haut)

#: Depliage par projection (ADR-0011 SS2). Meme densite que la Choir Mine et que
#: le Specter-9 : deux unites de la meme famille doivent porter la meme feuille de
#: detail a la meme echelle, sinon elles ne se ressemblent plus de pres.
TEXELS_PER_METER = 4.0

# --- puits et collier ------------------------------------------------------
LIP_R = 0.226        # rayon de la bouche (levre)
THROAT_MIN_R = 0.160  # rayon le plus etroit du percement : ce qu'on voit au travers
COLLAR_R = 0.305     # rayon exterieur du collier
CROWN_Z = 0.098      # point haut de la couronne qui borde le puits
FLOOR_Z = -0.150     # dessous du collier (point bas de la coque)

R_HINGE = 0.275      # rayon des charnieres — HORS du puits (cote exterieur)
Z_HINGE = 0.115      # hauteur des charnieres, portees par les contreforts

LATHE_SEGMENTS = 30  # segments de revolution du collier

#: Profil du collier, revolutionne autour de Z : (z, rayon, materiau du segment).
#: Le contour se referme sur lui-meme (dernier point = premier) : le solide est
#: un TORE, donc un percement traversant. Les bandes concentriques du dessus
#: (violet / anthracite / ivoire) sont le vocabulaire de plaques de la famille.
COLLAR_PROFILE: list[tuple[float, float, str]] = [
    (0.010, 0.305, "AA_Hull"),              # tranche haute, bord exterieur
    (0.046, 0.298, "AA_Panel"),             # anneau de plaques violettes
    (0.068, 0.281, "AA_Hull"),
    (0.084, 0.262, "AA_Trim"),              # anneau de carapace ivoire
    (0.096, 0.243, "AA_Trim"),              # couronne ivoire : la levre de la bouche
    (CROWN_Z, 0.234, "AA_Trim"),
    (0.086, LIP_R, "AA_Emissive_Engine"),   # haut de gorge : le magenta BORDE le vide
    (0.058, 0.214, "AA_Greeble"),           # la gorge s'eteint vite : c'est un PUITS
    (0.036, 0.208, "AA_Greeble"),           # gorge : anthracite tres sombre
    (-0.030, 0.186, "AA_Glass"),            # membrane : le puits s'assombrit
    (-0.096, 0.168, "AA_Glass"),
    (-0.132, THROAT_MIN_R, "AA_Greeble"),   # sortie basse — le puits est TRAVERSANT
    (-0.148, 0.198, "AA_Greeble"),          # dessous
    (FLOOR_Z, 0.252, "AA_Greeble"),
    (-0.118, 0.292, "AA_Panel"),
    (-0.062, 0.307, "AA_Hull"),             # tranche exterieure
    (-0.016, 0.308, "AA_Hull"),
    (0.010, 0.305, "AA_Hull"),              # fermeture du contour
]

# --- corolle ---------------------------------------------------------------
#: (azimut deg, longueur du bras, bout ivoire ?). Les azimuts sont IRREGULIERS
#: (ecarts 74 / 59 / 110 / 56 / 61 deg) et les longueurs franchement inegales :
#: c'est ce qui interdit a la silhouette de retomber sur la couronne reguliere de
#: la mine. Les quatre longueurs qui portent les extremes de la bounding box sont
#: calees pour que l'enveloppe reste centree (tolerance de pivot : 20 mm) — la
#: cinquieme est libre, donc franchement plus courte.
PETALS: list[tuple[float, float, bool]] = [
    (22.0, 0.5186, False),
    (96.0, 0.4698, True),
    (155.0, 0.5356, False),
    (265.0, 0.4688, True),
    (321.0, 0.2620, False),
]

ARM_STATIONS = 7          # subdivisions du bras
ARM_ELEV_ROOT = 12.0      # deg — elevation du bras a l'emplanture, au repos
ARM_ELEV_TIP = 20.0       # deg — elevation au bout : le bras se releve, ca cuvette

#: Demi-largeur du bras : (t normalise, demi-largeur). Maximum vers 20 % de la
#: longueur, puis effilement — un PETALE, pas une lame.
ARM_WIDTH: list[tuple[float, float]] = [
    (0.00, 0.082), (0.34, 0.090), (0.55, 0.108), (0.78, 0.082), (1.00, 0.030),
]
#: Demi-epaisseur du bras.
ARM_THICK: list[tuple[float, float]] = [
    (0.00, 0.013), (0.50, 0.009), (1.00, 0.004),
]

#: Langue : (u depuis la charniere, v, demi-largeur, demi-epaisseur). u negatif =
#: vers l'axe. La langue surplombe la couronne de 12 a 18 mm au repos.
TONGUE: list[tuple[float, float, float, float]] = [
    (-0.1454, -0.0110, 0.042, 0.006),   # bout : lèvre interieure, face au vide
    (-0.1100, -0.0062, 0.058, 0.008),
    (-0.0700, 0.0000, 0.072, 0.011),
    (-0.0300, 0.0022, 0.079, 0.013),
]

#: Section transverse : abscisses normalisees, du bord -t au bord +t.
CROSS: tuple[float, ...] = (-1.0, -0.62, -0.22, 0.22, 0.62, 1.0)
CUP = 0.26        # relevement des bords (la plaque cuvette vers le vide)

# --- anneau d'accretion ----------------------------------------------------
#: Trois arcs de longueurs inegales : un anneau BRISE tourne visiblement, un
#: anneau lisse ne tourne pas — et les breches cassent le disque dans l'aplat.
RING_ARCS: list[tuple[float, float]] = [(6.0, 96.0), (120.0, 74.0), (208.0, 116.0)]
RING_STEP_DEG = 12.0
#: Section de l'anneau : (rayon, z). Barreau arrondi, sous la corolle.
RING_SECTION: list[tuple[float, float]] = [
    (0.335, -0.072), (0.345, -0.050), (0.366, -0.042), (0.406, -0.042),
    (0.428, -0.050), (0.436, -0.066), (0.428, -0.082), (0.366, -0.088),
    (0.345, -0.086),
]
RING_TOP_BANDS = (2,)      # bande du dessus (celle qu'on voit d'en haut)
RING_GLOW_EVERY = 4        # une dent lumineuse sur trois : l'anneau se voit tourner

# --- mesure ----------------------------------------------------------------
SWEEP_MAX_DEG = 75.0   # borne d'exploration du debattement
SWEEP_STEP_DEG = 2.5
HINGE_SKIP = 0.055     # rayon d'exclusion autour de la charniere (joint reel)


# ==========================================================================
# Outils locaux (le kit n'est pas modifie : tout ce qui suit s'appuie sur lui)
# ==========================================================================


def lerp_table(table: list[tuple[float, float]], t: float) -> float:
    """Interpolation lineaire d'une table (abscisse, valeur), bornes clampees."""
    if t <= table[0][0]:
        return table[0][1]
    if t >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        t0, v0 = table[i]
        t1, v1 = table[i + 1]
        if t0 <= t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return table[-1][1]


def petal_frame(azimuth_deg: float) -> tuple[Vector, Vector, Vector]:
    """(charniere, radial unitaire, tangentiel unitaire) d'un petale."""
    a = math.radians(azimuth_deg)
    radial = Vector((math.cos(a), math.sin(a), 0.0))
    tangent = Vector((0.0, 0.0, 1.0)).cross(radial).normalized()
    hinge = Vector((R_HINGE * radial.x, R_HINGE * radial.y, Z_HINGE))
    return hinge, radial, tangent


def arm_path(length: float) -> list[tuple[float, float]]:
    """Ligne moyenne du bras en (u, v) locaux, integree a pas constant.

    L'elevation monte de `ARM_ELEV_ROOT` a `ARM_ELEV_TIP` : le bras se releve
    doucement, la corolle forme une cuvette qui converge vers le puits. Calcule
    plutot que tabule — donc juste par construction, et deterministe.
    """
    points = [(0.0, 0.0)]
    u = v = 0.0
    step = length / ARM_STATIONS
    for k in range(ARM_STATIONS):
        t = (k + 0.5) / ARM_STATIONS
        elev = math.radians(ARM_ELEV_ROOT + (ARM_ELEV_TIP - ARM_ELEV_ROOT) * t)
        u += step * math.cos(elev)
        v += step * math.sin(elev)
        points.append((u, v))
    return points


def local_box(
    bm: bmesh.types.BMesh,
    origin: Vector,
    radial: Vector,
    tangent: Vector,
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    material: str,
    top_material: str | None = None,
) -> None:
    """Boite orientee dans le repere local (radial, tangentiel, vertical).

    `ak.add_box` ne sait faire que des boites alignees sur les axes du monde ;
    tout ce qui se pose sur un petale ou sur le collier est oriente par un azimut.
    On n'utilise ici que des primitives du kit (`add_ring`, `bridge_rings`,
    `cap_ring`) : le kit reste inchange.
    """
    up = Vector((0.0, 0.0, 1.0))
    cu, ct, cv = center
    du, dt, dv = (s * 0.5 for s in size)
    base = origin + radial * cu + tangent * ct + up * cv
    corners = ((-du, -dt), (du, -dt), (du, dt), (-du, dt))
    low = ak.add_ring(bm, [tuple(base + radial * a + tangent * b - up * dv)
                           for a, b in corners])
    high = ak.add_ring(bm, [tuple(base + radial * a + tangent * b + up * dv)
                            for a, b in corners])
    ak.bridge_rings(bm, low, high, material)
    ak.cap_ring(bm, list(reversed(low)), material)
    ak.cap_ring(bm, high, top_material or material)


# ==========================================================================
# Coque statique : collier perce, contreforts, charnieres, fissures
# ==========================================================================


def build_collar(bm: bmesh.types.BMesh) -> None:
    """Le corps : un tore, donc un puits **traversant** de part en part."""
    ak.add_lathe(
        bm,
        [(z, r, mat) for z, r, mat in COLLAR_PROFILE],
        LATHE_SEGMENTS,
        axis="Z",
    )


def build_buttresses(bm: bmesh.types.BMesh) -> None:
    """Joues de charniere de chaque petale, portees par le collier.

    ⚠️ CHARNIERE EN FOURCHE, et c'est une correction mesuree, pas un style. Le
    premier jet posait un axe cylindrique PLEIN traversant la racine du petale :
    la plaque enveloppait l'axe, donc les deux solides s'interpenetraient DES LA
    POSE DE REPOS, et le debattement mesure tombait a 0 deg. Le contrat d'export,
    lui, ne s'apercevait de rien.

    La coque ne porte donc de matiere que **hors de la largeur du petale** : deux
    joues qui encadrent sa racine, et deux bossages d'axe ivoire sur leurs faces
    exterieures. Rien ne peut plus se toucher, et la charniere se lit quand meme.

    Deux consequences chiffrees, et elles bornent la geometrie du petale :

      * la joue occupe |t| in [0,088 ; 0,116] m, et le petale ne depasse JAMAIS
        0,098 m de demi-largeur ; la ou il est plus large que 0,088, il est deja
        a plus de 0,085 m de la charniere ;
      * la joue tient tout entiere a moins de **0,058 m** de la charniere. Comme
        une rotation autour de la charniere conserve la distance a la charniere,
        toute matiere du petale situee au-dela ne peut pas l'atteindre, a aucun
        angle. C'est ce chiffre — et non un reglage a vue — qui fixe le rayon
        d'exclusion `HINGE_SKIP` de la mesure de degagement.
    """
    up = Vector((0.0, 0.0, 1.0))
    for azimuth, _length, _ivory in PETALS:
        hinge, radial, tangent = petal_frame(azimuth)
        for side in (-1.0, 1.0):
            # joue : elle encadre la racine du petale sans jamais la toucher, et
            # monte 6 mm plus haut que lui — la charniere se lit d'en haut.
            cheek_low = ak.add_ring(bm, [
                tuple(hinge + radial * du + tangent * (side * dt) - up * 0.049)
                for du, dt in ((-0.030, 0.088), (0.026, 0.088),
                               (0.026, 0.116), (-0.030, 0.116))
            ])
            cheek_high = ak.add_ring(bm, [
                tuple(hinge + radial * du + tangent * (side * dt) + up * 0.019)
                for du, dt in ((-0.026, 0.088), (0.022, 0.088),
                               (0.022, 0.116), (-0.026, 0.116))
            ])
            ak.bridge_rings(bm, cheek_low, cheek_high, "AA_Greeble")
            ak.cap_ring(bm, cheek_high, "AA_Panel")

            # bossage d'axe : centre sur la charniere, donc invariant par la
            # rotation du petale — il ne peut pas etre rattrape par la piece.
            rings = []
            for offset, radius in ((0.100, 0.023), (0.122, 0.018)):
                rings.append(ak.add_ring(bm, [
                    tuple(hinge + tangent * (side * offset)
                          + radial * (radius * math.cos(2.0 * math.pi * s / 8))
                          + up * (radius * math.sin(2.0 * math.pi * s / 8)))
                    for s in range(8)
                ]))
            ak.bridge_rings(bm, rings[0], rings[1], "AA_Trim")
            ak.cap_ring(bm, rings[1] if side > 0 else list(reversed(rings[1])),
                        "AA_Trim")


def build_teeth(bm: bmesh.types.BMesh) -> None:
    """Onze crochets ivoire penches au-dessus de la levre : c'est une GUEULE.

    Trois raisons, dans l'ordre d'importance :

      * le bord du puits devient **dentele**, donc lisible comme un trou et non
        comme un disque sombre pose sur la coque — c'est ce que l'aplat noir doit
        montrer ;
      * onze crochets pour cinq petales : les deux rythmes ne coincident jamais,
        ce qui interdit a la bouche de retomber sur la symetrie de la corolle ;
      * ils reprennent l'ivoire de carapace de la famille (planche de concept)
        sans reprendre son motif de couronne de modules.

    Ils restent **sous** les langues au repos (sommet a 0,0975 m contre 0,1035 m
    pour le dessous d'une langue) ; la mesure de degagement le verifie, elle ne le
    suppose pas.
    """
    up = Vector((0.0, 0.0, 1.0))
    count = 9
    for k in range(count):
        _hinge, radial, tangent = petal_frame(360.0 * k / count + 7.0)
        half = 0.019 if k % 2 else 0.023      # crochets inegaux, comme le reste
        base = ak.add_ring(bm, [
            tuple(radial * du + tangent * dt + up * dz)
            for du, dt, dz in ((0.238, -half, 0.086), (0.262, -half, 0.080),
                               (0.262, half, 0.080), (0.238, half, 0.086))
        ])
        apex = bm.verts.new(tuple(radial * 0.219 + up * 0.0975))
        ak.fan_to_point(bm, base, apex, "AA_Trim")
        ak.cap_ring(bm, list(reversed(base)), "AA_Greeble")


def build_fissures(bm: bmesh.types.BMesh) -> None:
    """Fissures magenta rayonnantes — le motif de famille, retourne.

    Sur la planche, elles convergent vers un coeur lumineux. Ici elles partent du
    **vide** : elles s'arretent net sur la levre du puits. C'est le meme signe
    graphique, et il dit l'inverse.

    Posees dans les intervalles entre petales, la ou la camera de jeu les voit :
    sous un petale, une fissure n'existe pas (regle de BRIEF-0026).
    """
    gaps = []
    for i, (azimuth, _l, _iv) in enumerate(PETALS):
        nxt = PETALS[(i + 1) % len(PETALS)][0]
        span = (nxt - azimuth) % 360.0
        gaps.append((azimuth + span * 0.5, span))
    for middle, span in gaps:
        count = 1 if span < 70.0 else 2
        for k in range(count):
            offset = 0.0 if count == 1 else (k - 1) * span * 0.24
            _, radial, tangent = petal_frame(middle + offset)
            origin = Vector((0.0, 0.0, 0.0))
            local_box(
                bm, origin, radial, tangent,
                (0.256, 0.0, 0.083), (0.058, 0.011, 0.008),
                "AA_Emissive_Engine",
            )


def build_markings(bm: bmesh.types.BMesh) -> None:
    """Vert maladif, « usage tres limite » (charte 3) : trois events, pas une livree."""
    for azimuth, radius, height in ((44.0, 0.286, 0.052), (188.0, 0.290, 0.049),
                                    (296.0, 0.288, 0.050)):
        _, radial, tangent = petal_frame(azimuth)
        local_box(
            bm, Vector((0.0, 0.0, 0.0)), radial, tangent,
            (radius, 0.0, height), (0.030, 0.052, 0.011),
            "AA_Greeble", top_material="AA_Marking_Red",
        )


def build_hull():
    bm = bmesh.new()
    build_collar(bm)
    build_buttresses(bm)
    build_teeth(bm)
    build_fissures(bm)
    build_markings(bm)
    return ak.new_object("NullMaw_Hull", bm)


# ==========================================================================
# Petales — la corolle articulee
# ==========================================================================


def build_petal(index: int) -> ak.MovingPart:
    """Plaque coudee : langue vers le puits, bras vers l'exterieur, charniere entre.

    Construite en coordonnees ABSOLUES comme le reste de la coque ; `ak.moving_part`
    ramene ensuite l'origine sur la charniere. Sans cela, la piece decrirait un arc
    autour du centre de l'objet au lieu de basculer sur sa charniere.
    """
    azimuth, length, ivory = PETALS[index]
    hinge, radial, tangent = petal_frame(azimuth)
    up = Vector((0.0, 0.0, 1.0))
    bm = bmesh.new()

    #: (u, v, demi-largeur, demi-epaisseur), du bout de langue au bout de bras.
    stations: list[tuple[float, float, float, float]] = list(TONGUE)
    for k, (u, v) in enumerate(arm_path(length)):
        t = k / ARM_STATIONS
        stations.append((u, v, lerp_table(ARM_WIDTH, t), lerp_table(ARM_THICK, t)))

    rings = []
    for u, v, half_w, half_h in stations:
        cup = CUP * half_w
        base = hinge + radial * u + up * v
        top = [base + tangent * (k * half_w) + up * (half_h + cup * k * k)
               for k in CROSS]
        bot = [base + tangent * (k * half_w) - up * (half_h * (1.0 - 0.3 * k * k)
                                                     - cup * k * k)
               for k in CROSS]
        rings.append(ak.add_ring(bm, [tuple(p) for p in top]
                                 + [tuple(p) for p in reversed(bot)]))

    n = len(CROSS)
    bands: list[list] = []
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        bands.append(band)
        for j, face in enumerate(band):
            if face is None or not face.is_valid:
                continue
            if j in (n - 1, 2 * n - 1):
                face.material_index = ak.mat_index("AA_Trim")     # tranches ivoire
            elif j >= n:
                face.material_index = ak.mat_index("AA_Greeble")  # dessous
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Emissive_Engine")  # levre interieure
    ak.cap_ring(bm, rings[-1], "AA_Trim" if ivory else "AA_Greeble")

    # Carapace segmentee : trois plaques violettes ENFONCEES sur le dessus, separees
    # par des joints restes en `AA_Hull`. C'est le detail par la geometrie exige par
    # l'ADR-0008, et c'est aussi ce qui raccorde le Null Maw au reste de la flotte du
    # Choeur Nul — sur le Needle Scout comme sur la planche de concept, le violet
    # couvre l'essentiel du dessus, l'anthracite ne fait que les joints. Un petale
    # uniformement anthracite lisait comme une lame de metal nu, pas comme une
    # carapace.
    for first, last in ((0, len(TONGUE) - 2), (len(TONGUE), len(bands) - 1)):
        plate = [bands[i][j] for i in range(first, min(last, len(bands) - 1) + 1)
                 for j in range(n - 1)]
        ak.inset_panel(bm, plate, "AA_Panel", thickness=0.006, depth=-0.004)

    # Liseré magenta sur la levre interieure, POSE SUR LE DESSUS : une tranche
    # verticale ne se voit pas d'une camera a 20 deg de la verticale (BRIEF-0026),
    # et c'est justement ce liseré qui doit dire ou est le danger.
    u0, v0, w0, h0 = TONGUE[0]
    u1, v1, w1, h1 = TONGUE[1]
    local_box(
        bm, hinge, radial, tangent,
        ((u0 + u1) * 0.5, 0.0, (v0 + v1) * 0.5 + h0 + 0.004),
        (abs(u1 - u0) + 0.012, w0 * 1.7, 0.009),
        "AA_Emissive_Engine",
    )
    # Nervure ivoire sur le dessus du bras : elle dessine le petale a petite taille.
    mid = arm_path(length)[ARM_STATIONS // 2]
    local_box(
        bm, hinge, radial, tangent,
        (mid[0] * 0.92, 0.0, mid[1] * 0.92 + 0.012),
        (length * 0.62, 0.013, 0.007),
        "AA_Trim",
    )

    return ak.moving_part(f"Petal_{index + 1:02d}", bm, tuple(hinge))


# ==========================================================================
# Anneau d'accretion — il ne fait que tourner sur lui-meme
# ==========================================================================


def build_ring() -> ak.MovingPart:
    """Anneau brise, sous la corolle, autour du puits.

    Son origine reste a (0, 0, 0) : c'est le seul cas ou le piege documente par
    `ak.moving_part` n'en est pas un, puisque la piece tourne effectivement autour
    du centre de l'objet. Trois arcs de longueurs inegales et une dent lumineuse
    sur trois : sans irregularite, une rotation d'anneau est invisible.
    """
    bm = bmesh.new()
    glow = 0
    for start, span in RING_ARCS:
        steps = max(2, int(round(span / RING_STEP_DEG)))
        rings = []
        for s in range(steps + 1):
            a = math.radians(start + span * s / steps)
            rings.append(ak.add_ring(bm, [
                (r * math.cos(a), r * math.sin(a), z) for r, z in RING_SECTION
            ]))
        for i in range(len(rings) - 1):
            band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Greeble")
            glow += 1
            lit = (glow % RING_GLOW_EVERY) == 0
            for j, face in enumerate(band):
                if face is None or not face.is_valid:
                    continue
                if j in RING_TOP_BANDS:
                    face.material_index = ak.mat_index(
                        "AA_Emissive_Engine" if lit else "AA_Panel"
                    )
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Trim")
        ak.cap_ring(bm, rings[-1], "AA_Trim")
    return ak.moving_part("Ring", bm, (0.0, 0.0, 0.0))


# ==========================================================================
# Points d'attache
# ==========================================================================


def build_attach_points() -> list:
    """`Muzzle_C` au centre du puits, sur l'axe. **Aucun `Engine_C`** : le Null Maw
    derive avec le decor, il n'a pas de moteur, et `EnemyController` ne pose une
    plume que si la coque en declare un."""
    return [ak.attach_point("Muzzle_C", (0.0, 0.0, 0.0))]


# ==========================================================================
# Mesure — ce qu'une pose fixe ne prouve pas
#
# `export_hull()` ne connait que la pose de repos : une piece qui traverse la
# coque des qu'elle bouge passe le contrat sans un mot. On remesure donc a chaque
# build, sur le maillage REELLEMENT livre.
#
# Toutes les mesures sont faites dans le repere d'AUTEUR. Le passage au repere
# Godot ((x, y, z) -> (-x, z, y)) est une rotation propre (determinant +1) : elle
# conserve distances et angles, donc un degagement mesure ici vaut tel quel en jeu.
# Les pivots et les axes sont PUBLIES en repere Godot, eux, puisque c'est le code
# de jeu qui s'en sert.
# ==========================================================================

_TO_GODOT = Matrix(((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)))


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
    """(sommets, triangles) d'un objet, compactes.

    `skip` : rayon autour de `pivot` dont la geometrie est ecartee. Une charniere
    reelle s'interpenetre par construction (la plaque enveloppe son axe) ; ce qui
    doit degager, c'est tout le reste. L'exclusion est SYMETRIQUE (piece et coque),
    ce qui est licite : une rotation autour d'un axe passant par le pivot conserve
    la distance au pivot.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.index_update()
    raw = [v.co.copy() for v in bm.verts]
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

        Les deux sens de requete sont necessaires : un seul laisserait passer une
        plaque mince qui traverse une grande face sans qu'aucun de ses sommets n'en
        approche.
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


def petal_pose(part: ak.MovingPart, azimuth: float, angle: float,
               skip: float = HINGE_SKIP):
    """Sommets du petale (repere d'auteur) apres ouverture de `angle` radians."""
    hinge, _radial, tangent = petal_frame(azimuth)
    verts, tris = _soup(part.obj, hinge, skip)
    rot = Matrix.Rotation(angle, 4, tangent)
    return [hinge + rot @ (v - hinge) for v in verts], tris


def travel_table(hull, petals: list, ring) -> list[tuple]:
    """Debattement disponible de chaque petale, avant auto-intersection.

    On balaie l'ouverture par pas de `SWEEP_STEP_DEG` et on retient le dernier
    angle ou TOUTES les marges restent strictement positives. C'est le
    debattement MECANIQUE : ce que la piece peut faire, pas ce que le jeu lui
    demandera.

    Les deux marges sont rendues separement parce que les remedes le sont : mordre
    la coque ou l'anneau se corrige en remontant la charniere ou en descendant
    l'anneau, mordre un voisin en amincissant le petale ou en ecartant les azimuts.
    """
    rows = []
    steps = int(SWEEP_MAX_DEG / SWEEP_STEP_DEG)
    posed: dict[tuple[int, int], tuple] = {}
    for index, part in enumerate(petals):
        for s in range(steps + 1):
            posed[(index, s)] = petal_pose(part, PETALS[index][0],
                                           math.radians(s * SWEEP_STEP_DEG))

    for index, part in enumerate(petals):
        hinge, _r, _t = petal_frame(PETALS[index][0])
        hull_soup = _soup(hull, hinge, HINGE_SKIP)
        ring_soup = _soup(ring.obj, hinge, HINGE_SKIP)
        obstacle = Solid(
            hull_soup[0] + ring_soup[0],
            hull_soup[1] + [[i + len(hull_soup[0]) for i in t]
                            for t in ring_soup[1]],
        )
        limit, cause = 0.0, "aucune (butee hors balayage)"
        margin_hull = 9.9
        for s in range(steps + 1):
            deg = s * SWEEP_STEP_DEG
            d = obstacle.distance_to(*posed[(index, s)])
            if d <= 0.0:
                cause = "coque + anneau"
                break
            limit, margin_hull = deg, min(margin_hull, d)

        margin_pair, pair_where = 9.9, "-"
        for other in ((index - 1) % len(petals), (index + 1) % len(petals)):
            for s in range(int(limit / SWEEP_STEP_DEG) + 1):
                deg = s * SWEEP_STEP_DEG
                d = Solid(*posed[(other, s)]).distance_to(*posed[(index, s)])
                if d <= 0.0:
                    limit = max(0.0, deg - SWEEP_STEP_DEG)
                    cause = f"voisin Petal_{other + 1:02d}"
                    break
                if d < margin_pair:
                    margin_pair, pair_where = d, f"Petal_{other + 1:02d} a {deg:.0f} deg"
        rows.append((f"Petal_{index + 1:02d}", PETALS[index][1], limit, cause,
                     margin_hull, margin_pair, pair_where))
    return rows


def aperture_table(petals: list) -> list[tuple[float, float, float]]:
    """Ouverture du puits VUE DE DESSUS, par angle : (deg, part degagee, rayon libre).

    Methode : on tire des rayons verticaux depuis le plan de la levre vers le haut,
    sur une grille polaire couvrant la bouche du puits. Un rayon qui touche un
    petale est occulte. C'est exactement ce que voit la camera de jeu (a 20 deg de
    la verticale), et ca ne depend d'aucune estimation a la main.

    `rayon libre` = plus grand disque central entierement degage. Le puits devient
    TRAVERSANT a l'oeil quand ce rayon atteint `THROAT_MIN_R` : on voit alors le
    fond de l'espace au travers de la coque.

    On releve au passage l'**empreinte au sol** (rayon hors-tout de la corolle en
    projection verticale). Elle ne sert pas la lecture mais le gameplay : c'est
    elle qui dit de combien la coque deborde de sa hitbox quand la corolle
    travaille — et elle ne varie pas de facon monotone.
    """
    rings = 24
    spokes = 96
    samples = []
    for i in range(rings):
        r = LIP_R * (i + 0.5) / rings
        for j in range(spokes):
            a = 2.0 * math.pi * j / spokes
            samples.append((r, Vector((r * math.cos(a), r * math.sin(a),
                                       CROWN_Z + 0.002))))
    out = []
    for s in range(0, int(SWEEP_MAX_DEG / SWEEP_STEP_DEG) + 1):
        deg = s * SWEEP_STEP_DEG
        verts: list = []
        tris: list = []
        for index, part in enumerate(petals):
            v, t = petal_pose(part, PETALS[index][0], math.radians(deg), 0.0)
            tris += [[i + len(verts) for i in tri] for tri in t]
            verts += v
        tree = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)
        clear = 0
        blocked_r = LIP_R
        for r, origin in samples:
            if tree.ray_cast(origin, Vector((0.0, 0.0, 1.0)))[0] is None:
                clear += 1
            else:
                blocked_r = min(blocked_r, r)
        span = max(math.hypot(v.x, v.y) for v in verts)
        out.append((deg, clear / len(samples), blocked_r, span))
    return out


def material_areas(objects: list) -> dict[str, float]:
    areas: dict[str, float] = {}
    for obj in objects:
        for poly in obj.data.polygons:
            name = ak.MATERIAL_ORDER[poly.material_index]
            areas[name] = areas.get(name, 0.0) + poly.area
    return areas


def _bounds(objs: list) -> tuple[Vector, Vector]:
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    for obj in objs:
        for vert in obj.data.vertices:
            for a in range(3):
                lo[a] = min(lo[a], vert.co[a])
                hi[a] = max(hi[a], vert.co[a])
    return lo, hi


# ==========================================================================
# Assemblage
# ==========================================================================


def _triangulate_ngons(obj) -> None:
    """Coupe les n-gons — sans quoi l'export n'a AUCUNE tangente.

    L'exporteur glTF de Blender abandonne le calcul mikktspace des qu'une face
    depasse quatre sommets (« Tangent space can only be computed for tris/quads,
    aborting ») : il le dit dans le flot de sortie, puis exporte quand meme, sans
    l'attribut TANGENT. Aucune erreur, aucun test rouge, aucune ligne au journal —
    la coque a des UV, donc elle a l'air texturable, et tout shader de relief y
    reste plat. On ne le decouvre qu'en se demandant, des semaines plus tard,
    pourquoi une normal map ne fait rien.

    Ce script en produit des dizaines : chaque `cap_ring` (culot de crochet,
    tranche d'arc d'anneau, bout de petale) est une n-gon. La passe est
    obligatoire, pas cosmetique. Elle ne change PAS le nombre de triangles
    livres : une n-gon de n sommets vaut n-2 triangles, que ce soit ici ou dans
    l'exporteur.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(obj.data)
    bm.free()


def _finish(obj, width: float = 0.005, angle: float = 36.0) -> None:
    """Soudure, chanfrein, lissage, **decoupe des n-gons**, **depliage UV**.

    Le depliage vient en dernier : le chanfrein et la triangulation creent des
    faces, les deplier avant les laisserait sans coordonnees coherentes.
    """
    ak.cleanup(obj)
    ak.bevel_sharp_edges(obj, width=width, segments=1, angle_deg=angle)
    ak.shade_smooth_by_angle(obj, angle_deg=angle)
    _triangulate_ngons(obj)
    # UV par projection en boite (ADR-0011) : le support des feuilles de detail
    # repetables, appliquees cote Godot. Aucune texture n'est embarquee dans le
    # `.glb` — seulement les coordonnees, et les tangentes qu'elles rendent
    # calculables.
    ak.box_project_uv(obj, TEXELS_PER_METER)


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)

    hull = build_hull()
    petals = [build_petal(i) for i in range(len(PETALS))]
    ring = build_ring()
    parts = [*petals, ring]

    _finish(hull)
    for part in parts:
        _finish(part.obj)

    objs = [hull] + [p.obj for p in parts]

    # --- mesures en repere d'auteur ---------------------------------------
    lo, hi = _bounds(objs)
    print("--- mesures en repere d'auteur (avant correction d'axe) ---")
    for obj in objs:
        o_lo, o_hi = _bounds([obj])
        print(f"  {obj.name:<14} x[{o_lo.x:+.3f} {o_hi.x:+.3f}] "
              f"y[{o_lo.y:+.3f} {o_hi.y:+.3f}] z[{o_lo.z:+.3f} {o_hi.z:+.3f}] "
              f"{len(obj.data.polygons)} faces")
    print(f"  TOTAL          {hi.x - lo.x:.4f} x {hi.y - lo.y:.4f} x "
          f"{hi.z - lo.z:.4f} m   centre "
          f"({(hi.x + lo.x) * 0.5:+.4f}, {(hi.y + lo.y) * 0.5:+.4f}, "
          f"{(hi.z + lo.z) * 0.5:+.4f})")
    height = hi.z - lo.z
    if height < MIN_HEIGHT:
        raise ak.ContractError(
            f"hauteur {height:.4f} m < plancher {MIN_HEIGHT} m impose par le brief"
        )

    # --- repartition des materiaux, en AIRE -------------------------------
    areas = material_areas(objs)
    total = sum(areas.values())
    print("--- repartition des materiaux (aire reelle) ---")
    for name in ak.MATERIAL_ORDER:
        share = areas.get(name, 0.0) / total * 100.0
        print(f"  {name:<20} {areas.get(name, 0.0):.4f} m2   {share:5.2f} %")
    emissive = areas.get("AA_Emissive_Engine", 0.0) / total * 100.0
    print(f"  emissif : {emissive:.2f} % (au-dela de ~10 %, c'est une livree)")

    # --- pivots publies en repere Godot -----------------------------------
    print("--- pieces mobiles : pivot et axe, en repere GODOT ---")
    for index in range(len(PETALS)):
        hinge, _radial, tangent = petal_frame(PETALS[index][0])
        gp = _TO_GODOT @ hinge
        ga = _TO_GODOT @ tangent
        print(f"  Petal_{index + 1:02d}  pivot ({gp.x:+.4f}, {gp.y:+.4f}, {gp.z:+.4f})"
              f"   axe ({ga.x:+.4f}, {ga.y:+.4f}, {ga.z:+.4f})   angle > 0 = ouverture")
    print("  Ring      pivot (+0.0000, +0.0000, +0.0000)   axe (0, 1, 0)   rotation pure")

    # --- debattement mecanique --------------------------------------------
    print("--- debattement mecanique disponible (maillage livre) ---")
    for row in travel_table(hull, petals, ring):
        name, length, limit, cause, m_hull, m_pair, where = row
        print(f"  {name}  bras {length * 1000:5.0f} mm   "
              f"debattement {limit:5.1f} deg   bute : {cause:<28} "
              f"marge coque {m_hull * 1000:6.1f} mm   "
              f"marge voisin {m_pair * 1000:6.1f} mm ({where})")

    # --- ouverture du puits vue de dessus ---------------------------------
    print("--- ouverture du puits, vue de dessus ---")
    table = aperture_table(petals)
    for deg, clear, free_r, span in table:
        through = "TRAVERSANT" if free_r >= THROAT_MIN_R else ""
        print(f"  {deg:5.1f} deg   bouche degagee {clear * 100:5.1f} %   "
              f"disque central libre r={free_r:.3f} m   "
              f"empreinte {span * 2.0:.3f} m  {through}")
    through = [d for d, _c, r, _s in table if r >= THROAT_MIN_R]
    wide = [d for d, c, _r, _s in table if c >= 0.90]
    print(f"  SEUIL « puits franchement visible » : {through[0]:.1f} deg "
          f"(le percement devient traversant a l'oeil, on voit l'espace au fond)")
    print(f"  bouche degagee a 90 % a partir de {wide[0]:.1f} deg ; "
          f"debattement mecanique disponible : voir tableau ci-dessus")

    ak.export_hull(hull, build_attach_points(), OUTPUT, CONTRACT, parts=parts)


if __name__ == "__main__":
    main()
