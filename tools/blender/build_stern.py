"""build_stern.py — la carene de poupe du Long Cortege (BRIEF-0106).

    blender-aegis -t 1 -b -noaudio -P tools/blender/build_stern.py
    blender-aegis -t 1 -b -noaudio -P tools/blender/build_stern.py -- --plate

Produit `assets/imported/models/backgrounds/stern_hull.glb` et, avec `--plate`,
`docs/forge/output/BRIEF-0106-planche.png` — rendue A LA CAMERA DU JEU, avec les
trois groupes propulsifs REELS montes dessus (`ADR-0006` : un asset non rendu et
non regarde n'est pas valide).

⚠️ `-t 1` EST OBLIGATOIRE. Meme raison que `scripts/build-hull.sh` et que
`assets/source/models/stern/reduce_stern.py` : sans lui, deux executions ne
rendent pas le meme fichier. Verifie ici sur trois executions.


CE QUE CETTE PIECE EST, ET CE QU'ELLE REMPLACE
==============================================
Les vingt derniers metres du Cortege, `s in [500, 520]`, sur lesquels sont
boulonnes les trois groupes propulsifs du `BRIEF-0105`. Elle remplace la dalle
grise de 34 x 1,6 x 22 m que `CortegeStern.build()` pose aujourd'hui.

Le nœud `Stern` est pose par `cortege_root.gd` a `z = -508` sous le meme parent
que les cinq troncons : le repere LOCAL de ce fichier est donc

    z_local = 508 - s          (s = distance depuis la pointe de proue)

soit `z = +8` a la jonction (s = 500) et `z = -12` a l'arriere (s = 520).


L'ANNEAU DE JONCTION EST IMPORTE, JAMAIS RECOPIE
================================================
Le premier anneau est `blc._half_profile(500.0, side)`, bord par bord, pris dans
`build_long_cortege` — c'est le critere qui prime au brief. Deux ecritures d'une
meme cote finissent toujours par diverger, et ce niveau en a deja paye deux (le
coaming du hangar, l'emprise du socle de tourelle). `_assert_junction()` relit le
`.glb` PRODUIT et compare les 48 sommets au micron.

⚠️ Et il compare les DEUX bords separement. A `s = 500` la coque se trouve etre
symetrique (`_asym` rend (1, 1)), mais rien ne le garantit demain : si un jour un
bord bouge sans l'autre, le harnais echoue plutot que de livrer une marche.


LA CONTRAINTE QUI A DECIDE DE TOUTE LA FORME : IL N'Y A PAS DE PLACE
====================================================================
Le brief interdit toute geometrie dans l'emprise d'un berceau : 10 x 15 m plus
0,5 m de garde, aux stations `x = 0` et `x = +/-10,28`. Ces trois prismes se
RECOUVRENT — 5,5 + 5,5 = 11,0 m de demi-emprises pour un entraxe de 10,28 — et
leur union est une seule bande :

    |x| <= 15,78   et   |z| <= 8,00     ->  rien au-dessus du pont (-11,85)

Consequences, et aucune n'est un gout :

  * « des masses hautes ENTRE les berceaux » (brief §2) est **geometriquement
    impossible** : il n'y a aucun metre carre libre entre deux berceaux. Le
    relief vertical est donc reporte sur les FLANCS (|x| >= 16,20) et sur le
    MASSIF ARRIERE (z <= -8,60), les deux seules zones libres.
  * la premiere marche d'evasement ne peut pas etre progressive : la coque doit
    passer de 12,04 m de demi-largeur (jonction) a plus de 15,78 m en une seule
    fois, exactement a `s = 500`. Elle le fait par un CHANFREIN de 0,90 m qui
    part vers l'exterieur au-dessus du niveau du pont — les deux marches
    suivantes, elles, sont libres et franches (s = 505,4 et s = 511).
  * l'artere ne peut pas se terminer DANS le bassin : tout ce qui y depasserait
    du pont mordrait un berceau. Son collecteur est donc pose de l'autre cote de
    la jonction, `z in [8,15 ; 9,45]`, a cheval sur la fin du canal du corridor —
    la seule position ou il soit a la fois visible et hors emprise.

⚠️ ET LA PAROI AVANT DU BASSIN NE SE VOIT PAS. On ne voit pas le mur AVANT d'une
fosse quand on la regarde de face et de haut : on en voit le fond et le mur du
FOND. Mesure a la camera du jeu (0 ; 14 ; 5) posee a `z = 11,47` local :
le fond du bassin n'apparait qu'a partir de `z = +6,49`, tout ce qui est plus
avant etant masque par le pont du corridor lui-meme. Le mur du fond (z = -8,60)
est au contraire pleine face : c'est LA surface a habiller, et c'est pour cela
que le massif arriere porte les tours.


CE QUE LES PLANCHES ONT DONNE — TROIS, PAS DIX
==============================================
Le brief en propose dix et previent : « ce n'est pas une liste de courses ».
Trois ont ete retenues, chacune sur UNE installation bornee :

    asset07  pylone spatial      -> les quatre pylones de rive (etagement,
                                    fuseau rectangulaire, socle debordant)
    asset08  bride de moteur     -> la chaine de brides du rebord de bassin
                                    (segments repetes, rails de guidage)
    asset08  conduite d'energie  -> le collecteur d'artere (tube octogonal,
                                    colliers de serrage, section vitree)

Une quatrieme, `asset08` tour d'echange thermique, sert aux deux tours du massif
arriere — socle evase, fut cannele, diffuseur en cone. Les six autres planches
sont laissees : « un module de relief ne se pose que dans l'emprise d'une
installation » (regle issue du `BRIEF-0094`).


L'EMISSIF : UNE SEULE INSTALLATION, ET ELLE S'ETEINT D'UN BLOC
==============================================================
`CortegeStern.blackout()` eteint tout ce qui porte `AA_Emissive_Engine`. Une
veine rangee ailleurs resterait allumee sur un vaisseau mort, sans erreur ni test
rouge. Le slot n'est donc porte QUE par la jonction d'artere, prise comme un tout :
le collecteur (section vitree) et l'anneau de distribution encastre dans le pont
qui en part. Rien d'autre du fichier ne le touche, et `_audit()` le compte sur le
binaire.

⚠️ L'anneau est ENCASTRE, jamais pose : ses rubans sont a `y = -11,99`, sous le
plan du pont. C'est ce qui lui permet d'exister dans l'emprise des berceaux (elle
n'interdit que ce qui DEPASSE) et c'est aussi la lecon du `BRIEF-0094` — une bande
emissive posee sur le point haut vole la lisibilite aux projectiles ; un creux,
non.


TEXTURE : AUCUNE (ADR-0028)
===========================
Zero image dans le `.glb`, PBR par facteurs, comme tout le niveau. Le depliage
est une projection en boite a **0,20 tuile/m** — la densite EXACTE de la peau du
corridor (`blc.HULL_TEXELS_PER_METER`), lue et non recopiee.

⚠️ La projection est calculee dans un repere DECALE de +2,00 m en z. Sans ce
decalage, `v = z_local x 0,20` vaudrait 1,60 a la jonction quand le troncon 5 y
vaut -20,00 : la carte sauterait de 0,6 tuile pile a l'endroit qu'on regarde. Avec
lui, `v = 2,00` — entier, donc en phase. Meme piege que `HULL_TILES_PER_SECTION`,
meme remede.


ANIMATION : AUCUNE (ADR-0046 §6)
================================
La poupe est de la structure. Ce qui bouge — nacelles, berceaux, verrous, bras —
est deja livre et anime par `reduce_stern.py`.
"""

from __future__ import annotations

import json
import math
import os
import re
import struct
import sys
import tempfile

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402
import build_long_cortege as blc  # noqa: E402  (l'anneau de jonction vient de la)

OUTPUT = os.path.join(_REPO, "assets/imported/models/backgrounds/stern_hull.glb")
PLATE = os.path.join(_REPO, "docs/forge/output/BRIEF-0106-planche.png")
TUNING = os.path.join(_REPO, "resources/levels/long_cortege_stern.tres")
MODELS = os.path.join(_REPO, "assets/imported/models/backgrounds")

# ==========================================================================
# Les cotes du jeu — LUES, jamais decidees ici
# ==========================================================================


def _game_tuning() -> dict:
    """Relit `long_cortege_stern.tres`. On ne le modifie pas : on s'y plie."""
    text = open(TUNING, encoding="utf-8").read()
    out: dict = {}
    for key, raw in re.findall(r"^(\w+) = (.+)$", text, re.M):
        raw = raw.strip()
        vec = re.match(r"Vector3\(([^)]*)\)", raw)
        if vec:
            out[key] = Vector([float(v) for v in vec.group(1).split(",")])
        else:
            try:
                out[key] = float(raw)
            except ValueError:
                pass
    out.setdefault("anchor_size_y", 1.20)
    out.setdefault("cradle_size", Vector((11.19, 4.64, 14.00)))
    out.setdefault("engine_size", Vector((9.10, 5.49, 11.93)))
    return out


T = _game_tuning()

#: La station de la poupe (s, en metres depuis la proue) : l'origine du repere local.
STATION = T["station"]                      # 508,0
#: Le pont qui porte les berceaux.
DECK_Y = T["deck_y"]                        # -11,85
#: L'entraxe des trois groupes.
SPACING = T["engine_spacing"]               # 10,28

#: Le plafond que TOUT le decor du niveau respecte (`blc.BUILD_CEILING_Y`).
CEILING_Y = blc.BUILD_CEILING_Y             # -3,20
#: La quille : la carene du corridor ne descend pas plus bas.
KEEL_Y = -12.60

#: La station de jonction, et son z LOCAL.
JOINT_S = 500.0
JOINT_Z = STATION - JOINT_S                 # +8,0
#: L'arriere de la poupe.
TAIL_Z = -12.0                              # s = 520

#: L'emprise interdite d'un berceau : 10 x 15 m plus 0,5 m de garde, en DEMIES.
KEEPOUT_HALF_X = 0.5 * 10.0 + 0.5           # 5,50
KEEPOUT_HALF_Z = 0.5 * 15.0 + 0.5           # 8,00
#: Les trois stations laterales.
ENGINE_X = (-SPACING, 0.0, SPACING)
#: L'union des trois emprises : elles se RECOUVRENT (voir l'en-tete).
KEEPOUT_X = SPACING + KEEPOUT_HALF_X        # 15,78

#: Budget du brief.
TRI_BUDGET = 20_000

#: La densite de la peau du corridor, LUE dans le module (0,20 tuile/m).
TEXELS_PER_METER = blc.HULL_TEXELS_PER_METER
#: Decalage de projection : sans lui la carte saute a la jonction (voir l'en-tete).
UV_SHIFT_Z = 2.0

# ==========================================================================
# La section transversale — 25 points par bord, MEME topologie que le corridor
# ==========================================================================
# Le premier anneau EST celui du corridor ; tous les autres reprennent ses 25
# indices avec d'autres coordonnees. C'est ce qui permet de border la jonction
# sans changer de topologie, donc sans coudre a la main.
#
#   0..8    le fond du bassin, de l'axe au pied de paroi
#   9..12   la paroi du bassin (fruit de 0,60 m sur 5 a 7 m)
#   13      l'arete de rive
#   14..18  les trois terrasses etagees, marches franches
#   19      la facette exterieure : le point le PLUS LARGE
#   20..24  le dessous, jusqu'a la quille

#: Le fond du bassin (la « sole »). L'assise des berceaux est une DALLE posee
#: dessus, a `DECK_Y` : c'est ce qui donne au pourtour son creux sans percer la
#: peau (voir `build_apron()`).
SOLE_Y = -12.00
#: Le pied de paroi le plus INTERIEUR que la coque s'autorise. Il est a 0,62 m de
#: l'union des trois emprises (15,78) : c'est toute la marge disponible.
BASIN_MIN_X = 16.40

#: Les trois bandes de station, et c'est LA le profil d'evasement.
#:
#: ⚠️ LA BOUCHE DU BASSIN S'OUVRE EN MEME TEMPS QUE LA COQUE, et la premiere
#: version ne le faisait pas : le rebord restait a 17,00 dans les trois bandes,
#: seule l'etagere exterieure gagnait 1,7 m. Rendu et regarde de dessus, le
#: resultat etait un rectangle — l'evasement ne se lisait nulle part. Ici les
#: quatre cotes bougent ensemble a chaque marche : pied de paroi, arete de rive,
#: terrasses et bord. De dessus, le bassin S'OUVRE.
#:
#: ⚠️ ET LA RIVE MONTE VERS L'ARRIERE. Les deux vont ensemble : a chaque marche la
#: terrasse change d'altitude en meme temps que de largeur, si bien qu'on voit la
#: face horizontale du gradin et pas seulement le bord de la silhouette. Le brief
#: le dit : « ce qui distingue une marche d'une pente, c'est la face horizontale
#: entre les deux ».
#:
#: (nom, z_avant, z_arriere, rive_y, pied de paroi, arete de rive, bord)
BANDS: tuple[tuple[str, float, float, float, float, float, float], ...] = (
    ("B1", JOINT_Z, 2.72, -6.60, BASIN_MIN_X, 16.60, 17.00),
    ("B2", 2.60, -2.88, -5.60, 17.30, 17.60, 18.40),
    ("B3", -3.00, -8.48, -4.60, 18.20, 18.60, 19.80),
)
#: Le massif arriere : le bassin s'y referme, et son plateau porte les tours.
AFT_Z = -8.60
AFT_CREST_Y = -4.60
AFT_PLATEAU_Y = -8.40
#: Le plateau du massif, en FRACTIONS du pied de paroi (indices 0..8) : le plateau
#: central, puis l'epaulement qui remonte vers la rive.
AFT_TOP_Y = (AFT_PLATEAU_Y, AFT_PLATEAU_Y, AFT_PLATEAU_Y, AFT_PLATEAU_Y,
             AFT_PLATEAU_Y, -7.60, -6.20, -4.90, AFT_CREST_Y)

#: ⚠️ IL N'Y A PAS DE CHANFREIN DE PROUE, ET CE N'EST PAS UN OUBLI. La premiere
#: version en portait un de 0,90 m : la premiere marche partait vers l'arriere en
#: biais, ce qui donnait a la poupe une entree taillee plutot qu'une plaque. Le
#: harnais d'emprise l'a refuse, et il a raison — MESURE : 17,79 m2 de decor
#: au-dessus du pont dans les emprises de berceau.
#:
#: La raison est arithmetique et sans echappatoire. Le bordage du corridor a
#: `s = 500` s'arrete a |x| = 12,04, l'union des trois emprises va jusqu'a
#: |x| = 15,78, et le premier anneau de la poupe est a |x| >= 16,40. Toute face
#: qui relie l'un a l'autre traverse donc la bande interdite. Tant qu'elle est
#: dans le PLAN `z = 8,00` son ombre est un segment d'aire nulle et elle ne mord
#: rien ; des qu'elle prend la moindre epaisseur en z, elle balaie la bande.
#:
#: La face avant de la poupe est donc **rigoureusement plane**, a la limite exacte
#: de l'emprise. Le brief ne laisse pas un centimetre : 508 - 8 = 500. Le relief
#: qui lui manque est repris AVANT elle, par `build_shoulders()`, dans le seul
#: volume libre qui reste : `z >= 8,00`, de part et d'autre du corridor.
FORE_FACE_Z = JOINT_Z

#: Fractions du pied de paroi pour les points 5..8 du fond.
FLOOR_T = (0.000, 0.159, 0.317, 0.476, 0.634, 0.770, 0.867, 0.945, 1.000)
#: Fractions de la paroi (entre pied et arete) aux points 9..12.
WALL_T = (0.28, 0.52, 0.72, 0.88)
WALL_X_T = (0.20, 0.40, 0.62, 0.83)


def _band_of(z: float) -> tuple:
    for band in BANDS:
        if band[2] - 1e-9 <= z <= band[1] + 1e-9:
            return band
    return BANDS[-1]


def _half_stern(z: float, aft: bool = False) -> list[tuple[float, float]]:
    """La demi-section tribord de la poupe a la station `z`, 25 points."""
    _, _, _, crest_y, basin_x, crest_x, wmax = _band_of(z)
    top = list(AFT_TOP_Y) if aft else [SOLE_Y] * 9
    crest = AFT_CREST_Y if aft else crest_y
    shelf = wmax - crest_x
    pts: list[tuple[float, float]] = []
    for i, t in enumerate(FLOOR_T):
        pts.append((basin_x * t, top[i]))
    base = top[8]
    for xt, yt in zip(WALL_X_T, WALL_T):
        pts.append((basin_x + (crest_x - basin_x) * xt, base + (crest - base) * yt))
    pts.append((crest_x, crest))                              # 13 arete de rive
    pts.append((crest_x + shelf / 3.0, crest - 0.10))         # 14 terrasse 1
    pts.append((crest_x + shelf / 3.0 + 0.10, crest - 1.20))  # 15 contremarche
    pts.append((crest_x + 2.0 * shelf / 3.0, crest - 1.30))   # 16 terrasse 2
    pts.append((crest_x + 2.0 * shelf / 3.0 + 0.10, crest - 2.40))
    pts.append((wmax, crest - 2.50))                          # 18 terrasse 3
    pts.append((wmax + 0.10, crest - 3.70))                   # 19 point le + large
    pts.append((wmax - 0.20, -11.30))                         # 20 bord bas
    # ⚠️ LE PLUS PETIT DEFAUT DE CE FICHIER TENAIT DANS CE `max()`. Sans lui, la
    # sous-chine rentrait a `wmax - 1,90` : en bande avant (wmax = 17,00) l'arete
    # 20 -> 21 traversait le plan du pont a |x| = 15,63, soit 15 cm DANS l'union
    # des emprises. 1,57 m2 de dessous de coque au-dessus du pont, sous un
    # berceau lateral, mesures par le harnais. Invisible a l'œil, refuse au
    # micron.
    pts.append((max(wmax - 1.90, BASIN_MIN_X - 0.10), -12.10))  # 21 sous-chine
    pts.append((max(wmax - 6.60, 8.00), -12.45))              # 22 fond
    pts.append((5.00, -12.55))                                # 23 fond
    pts.append((0.00, -12.58))                                # 24 quille
    return pts


#: Materiau du segment `i -> i+1` de la demi-section (24 entrees).
#: ⚠️ AUCUN VIOLET NI AUCUN IVOIRE SUR LA PEAU. Sur 500 m, le `BRIEF-0094` a
#: mesure qu'un materiau qui suit une arete CONTINUE occupe plus de pixels que
#: n'importe quelle piece — et le compte de triangles ne le dit pas. Ici la peau
#: est en deux gris ; la couleur n'appartient qu'aux installations.
HALF_MATERIALS: tuple[str, ...] = (
    "AA_Hull", "AA_Hull", "AA_Hull", "AA_Hull",         # 0-4  fond
    "AA_Hull", "AA_Hull", "AA_Hull", "AA_Hull",         # 4-8  fond
    "AA_Greeble", "AA_Greeble", "AA_Greeble",           # 8-11 paroi du bassin
    "AA_Greeble", "AA_Hull",                            # 11-13
    "AA_Hull", "AA_Hull", "AA_Hull",                    # 13-16 terrasses
    "AA_Hull", "AA_Hull", "AA_Greeble",                 # 16-19
    "AA_Greeble", "AA_Greeble", "AA_Greeble",           # 19-22 dessous
    "AA_Greeble", "AA_Greeble",                         # 22-24
)


def _ring_materials() -> list[str]:
    n = 25
    mats = [HALF_MATERIALS[i] for i in range(n - 1)]
    mats += [HALF_MATERIALS[2 * n - 3 - i] for i in range(n - 1, 2 * n - 2)]
    return mats


RING_MATERIALS = _ring_materials()
RING_SIZE = 48


def _close(tribord: list[tuple[float, float]],
           babord: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Anneau ferme de 48 points, tribord puis babord — meme regle que `blc._ring`."""
    return tribord + [(-x, y) for x, y in reversed(babord[1:-1])]


def _joint_ring() -> list[tuple[float, float]]:
    """L'anneau du corridor a `s = 500`, IMPORTE bord par bord."""
    return _close(blc._half_profile(JOINT_S, 1.0), blc._half_profile(JOINT_S, -1.0))


def _stern_ring(z: float, aft: bool = False) -> list[tuple[float, float]]:
    half = _half_stern(z, aft)
    return _close(half, half)


def _ring_z(ring: list[tuple[float, float]], z: float) -> list[Vector]:
    """Pose un anneau a la station `z`."""
    return [Vector((x, y, z)) for x, y in ring]


# ==========================================================================
# Primitives de maillage — memes principes que `build_long_cortege`
# ==========================================================================


def _new_object(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    """Objet aux 7 slots du kit, SANS `recalc_face_normals`.

    La poupe est une coque fermee mais elle porte un bassin : sur une surface
    concave, l'heuristique de bmesh peut retourner des pans entiers sans qu'aucune
    bounding box ne s'en apercoive. Le bobinage est pose par construction et
    `_orient()` le verifie au VOLUME SIGNE, composant par composant.
    """
    mesh = bpy.data.meshes.new(name)
    ak.apply_material_slots(mesh)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _face(bm: bmesh.types.BMesh, verts: list, material: str):
    clean: list = []
    for v in verts:
        if v not in clean:
            clean.append(v)
    if len(clean) < 3:
        return None
    try:
        face = bm.faces.new(clean)
    except ValueError:
        return None
    face.material_index = ak.mat_index(material)
    return face


def _bridge(bm: bmesh.types.BMesh, front: list, back: list,
            materials: list[str]) -> None:
    """Relie deux anneaux fermes. `front` est a plus grand z."""
    n = len(front)
    for i in range(n):
        j = (i + 1) % n
        _face(bm, [front[i], front[j], back[j], back[i]], materials[i])


def _cap(bm: bmesh.types.BMesh, ring: list, material: str, facing_front: bool):
    order = list(reversed(ring)) if facing_front else list(ring)
    return _face(bm, order, material)


def _signed_volume(bm: bmesh.types.BMesh) -> float:
    total = 0.0
    for face in bm.faces:
        verts = [loop.vert.co for loop in face.loops]
        a = verts[0]
        for i in range(1, len(verts) - 1):
            b, c = verts[i], verts[i + 1]
            total += a.dot(b.cross(c)) / 6.0
    return total


def _orient(bm: bmesh.types.BMesh, name: str) -> None:
    """Retourne le composant entier si son volume signe est negatif.

    ⚠️ C'EST LE SEUL CONTROLE QUI VOIE UNE COQUE A L'ENVERS. Une face retournee
    ne produit aucune erreur : elle DISPARAIT en jeu (culling arriere) et le
    journal reste muet. Sur une piece fermee et bobinee de facon coherente, le
    signe du volume tranche pour toutes les faces d'un coup.
    """
    volume = _signed_volume(bm)
    if abs(volume) < 1e-6:
        raise ak.ContractError(f"{name} : volume nul — piece non fermee ?")
    if volume < 0.0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])


def _box(bm: bmesh.types.BMesh, x0: float, x1: float, y0: float, y1: float,
         z0: float, z1: float, side_mat: str, top_mat: str | None = None) -> None:
    """Une boite alignee, faces sortantes.

    ⚠️ LES BORNES SONT TRIEES, ET CE N'EST PAS DU CONFORT. Toute cette poupe se
    construit en miroir (`side * x`), ce qui INVERSE l'ordre des bornes a babord :
    la boite y sortait retournee, invisible en jeu, et son volume signe annulait
    exactement celui de tribord — le controle d'orientation lisait zero et ne
    voyait rien. Un defaut silencieux qui en masquait un autre.
    """
    top_mat = top_mat or side_mat
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    lo = [Vector((x0, y0, z0)), Vector((x1, y0, z0)),
          Vector((x1, y0, z1)), Vector((x0, y0, z1))]
    hi = [Vector((x0, y1, z0)), Vector((x1, y1, z0)),
          Vector((x1, y1, z1)), Vector((x0, y1, z1))]
    lv = [bm.verts.new(v) for v in lo]
    hv = [bm.verts.new(v) for v in hi]
    _face(bm, [hv[0], hv[3], hv[2], hv[1]], top_mat)
    _face(bm, [lv[0], lv[1], lv[2], lv[3]], side_mat)
    for i in range(4):
        j = (i + 1) % 4
        _face(bm, [lv[i], hv[i], hv[j], lv[j]], side_mat)


def _prism(bm: bmesh.types.BMesh, cx: float, cz: float, radii: list[float],
           y0: float, y1: float, sides: int, side_mat: str, cap_mat: str,
           phase: float = 0.0) -> tuple[list, list]:
    """Un prisme vertical a `sides` cotes, rayon par sommet (cannelures)."""
    lo, hi = [], []
    for i in range(sides):
        a = phase + 2.0 * math.pi * i / sides
        r = radii[i % len(radii)]
        x, z = cx + r * math.cos(a), cz + r * math.sin(a)
        lo.append(bm.verts.new(Vector((x, y0, z))))
        hi.append(bm.verts.new(Vector((x, y1, z))))
    for i in range(sides):
        j = (i + 1) % sides
        _face(bm, [lo[i], lo[j], hi[j], hi[i]], side_mat)
    _face(bm, list(reversed(hi)), cap_mat)
    _face(bm, lo, cap_mat)
    return lo, hi


def _cone(bm: bmesh.types.BMesh, cx: float, cz: float, r0: float, r1: float,
          y0: float, y1: float, sides: int, side_mat: str, cap_mat: str) -> None:
    lo, hi = [], []
    for i in range(sides):
        a = 2.0 * math.pi * i / sides
        lo.append(bm.verts.new(Vector((cx + r0 * math.cos(a), y0,
                                       cz + r0 * math.sin(a)))))
        hi.append(bm.verts.new(Vector((cx + r1 * math.cos(a), y1,
                                       cz + r1 * math.sin(a)))))
    for i in range(sides):
        j = (i + 1) % sides
        _face(bm, [lo[i], lo[j], hi[j], hi[i]], side_mat)
    _face(bm, list(reversed(hi)), cap_mat)
    _face(bm, lo, cap_mat)


def _tube_x(bm: bmesh.types.BMesh, x0: float, x1: float, cy: float, cz: float,
            radius: float, sides: int, material: str) -> tuple[list, list]:
    """Un tube d'axe X, ouvert : les bouts sont fermes par l'appelant."""
    a0, a1 = [], []
    for i in range(sides):
        a = 2.0 * math.pi * (i + 0.5) / sides
        y, z = cy + radius * math.cos(a), cz + radius * math.sin(a)
        a0.append(bm.verts.new(Vector((x0, y, z))))
        a1.append(bm.verts.new(Vector((x1, y, z))))
    for i in range(sides):
        j = (i + 1) % sides
        _face(bm, [a0[i], a1[i], a1[j], a0[j]], material)
    return a0, a1


# ==========================================================================
# 1. LA PEAU — le loft de la jonction au massif arriere
# ==========================================================================


def _stations() -> list[tuple[float, list[tuple[float, float]]]]:
    """(z, anneau) — de l'avant vers l'arriere."""
    rings: list[tuple[float, list]] = []
    rings.append((JOINT_Z, _joint_ring()))
    for _name, z_fore, z_aft, *_ in BANDS:
        rings.append((z_fore, _stern_ring(z_fore)))
        rings.append((z_aft, _stern_ring(z_aft)))
    rings.append((AFT_Z, _stern_ring(AFT_Z, aft=True)))
    rings.append((TAIL_Z + 0.40, _stern_ring(TAIL_Z + 0.40, aft=True)))
    tail = [(x * 0.92, y - (0.50 if y > DECK_Y else 0.0))
            for x, y in _stern_ring(TAIL_Z, aft=True)]
    rings.append((TAIL_Z, tail))
    return rings


def build_skin(bm: bmesh.types.BMesh) -> None:
    """Le loft. Marches FRANCHES : deux anneaux a 0,12 m l'un de l'autre.

    ⚠️ Le premier bridge relie deux anneaux a la MEME station (`z = 8,00`) : c'est
    la face avant, plane par obligation (voir `FORE_FACE_Z`). Les deux suivants
    (`z = 2,72 -> 2,60` et `-2,88 -> -3,00`) sont les deux epaulements, francs a
    0,12 m — assez pour que la contremarche existe, trop peu pour qu'on la lise
    comme une pente.
    """
    previous: list | None = None
    for z, ring in _stations():
        current = [bm.verts.new(v) for v in _ring_z(ring, z)]
        if previous is not None:
            _bridge(bm, previous, current, RING_MATERIALS)
        previous = current
    _cap(bm, previous, "AA_Greeble", facing_front=False)


# ==========================================================================
# 2. L'ASSISE — la dalle plane sur laquelle les trois berceaux se posent
# ==========================================================================
# Le fond du loft est a `SOLE_Y` (-12,00) ; l'assise est une DALLE de 0,15 m
# posee dessus, dont le dessus est a `DECK_Y` (-11,85) EXACTEMENT.
#
# ⚠️ SON DESSUS EST AU NIVEAU DU PONT, PAS AU-DESSUS : elle ne « mord » donc
# aucune emprise de berceau (le brief interdit ce qui DEPASSE). Et c'est ce qui
# donne gratuitement au pourtour son creux de 0,15 m — la gorge ou court l'anneau
# d'artere, et le seul relief de sol qui reste visible entre les nacelles.

APRON_HALF_X = 15.95
APRON_FORE_Z = 7.95
APRON_AFT_Z = -8.20
#: ⚠️ UNE SEULE DALLE, ET C'EST UNE DECISION MESUREE. Une version a trois dalles
#: (une par groupe, joint dans le creux entre deux berceaux) a ete construite puis
#: abandonnee : le creneau disponible est trop etroit pour un joint honnete.
#:
#:   le brief demande 10 m d'assise par berceau      -> central jusqu'a 5,00
#:                                                      lateral a partir de 5,28
#:   le berceau CENTRAL en mesure en fait 10,32       -> il va jusqu'a 5,16
#:   le berceau LATERAL commence a                       5,41
#:
#: Satisfaire a la fois la cote du brief ET l'enveloppe reelle des pieces ne laisse
#: que `[5,16 ; 5,28]`, soit **0,12 m** — un trait, pas un joint, et une assise a
#: 0,00 m de marge sous un berceau lateral. La dalle est donc d'un seul tenant :
#: 31,90 x 16,15 m, 5,95 m de marge laterale sur la cote du brief.
#:
#: Son dessus est a `DECK_Y` EXACTEMENT, pas au-dessus : elle ne mord donc aucune
#: emprise (le brief interdit ce qui DEPASSE du pont) et elle donne gratuitement au
#: pourtour son creux de 0,15 m — la gorge ou court l'anneau d'artere.


def build_apron(bm: bmesh.types.BMesh) -> None:
    _box(bm, -APRON_HALF_X, APRON_HALF_X, SOLE_Y, DECK_Y,
         APRON_AFT_Z, APRON_FORE_Z, "AA_Greeble", "AA_Hull")


# ==========================================================================
# 3. L'ARTERE — collecteur et anneau de distribution (LE SEUL EMISSIF)
# ==========================================================================

#: La gorge de rive : entre le bord de l'assise et le pied de paroi.
GROOVE_X = APRON_HALF_X + 0.22
GLOW_Y = SOLE_Y + 0.01
#: ⚠️ 0,09 ET NON 0,15 DE DEMI-LARGEUR, ET LE RUBAN EST TIRETE. Rendu et regarde :
#: en continu et a 0,30 m de large, l'anneau dessinait un RECTANGLE NEON autour du
#: pont — la chose la plus lumineuse d'un cadre ou le joueur doit lire dix verrous.
#: C'est mot pour mot le defaut que le `BRIEF-0094` a corrige sur l'arete dorsale
#: du corridor. Tirete, il se lit comme une rangee de feux de balisage : on voit
#: qu'il alimente, on ne le regarde plus a la place des cibles. Aire emissive
#: mesuree sur le binaire : voir le compte-rendu.
GLOW_HALF = 0.09
GLOW_DASH = 1.30
GLOW_GAP = 1.45


def _ribbon(bm: bmesh.types.BMesh, x0: float, x1: float,
            z0: float, z1: float) -> None:
    v = [bm.verts.new(Vector((x0, GLOW_Y, z0))),
         bm.verts.new(Vector((x1, GLOW_Y, z0))),
         bm.verts.new(Vector((x1, GLOW_Y, z1))),
         bm.verts.new(Vector((x0, GLOW_Y, z1)))]
    _face(bm, [v[0], v[3], v[2], v[1]], "AA_Emissive_Engine")


def _dashes(bm: bmesh.types.BMesh, x0: float, x1: float,
            a: float, b: float, along_z: bool) -> None:
    """Une file de tirets entre `a` et `b`, le long de z (ou de x)."""
    cursor = a
    while cursor + GLOW_DASH <= b + 1e-9:
        if along_z:
            _ribbon(bm, x0, x1, cursor, cursor + GLOW_DASH)
        else:
            _ribbon(bm, cursor, cursor + GLOW_DASH, x0, x1)
        cursor += GLOW_DASH + GLOW_GAP


def build_glow_ring(bm: bmesh.types.BMesh) -> None:
    """Les tirets encastres : deux files de rive et la traverse arriere.

    ⚠️ ILS SONT DANS LA GORGE, A 0,15 m SOUS LE PONT. Poses a plat sur l'assise,
    les memes tirets seraient au niveau des semelles de berceau ; encastres, la
    geometrie les ombre d'elle-meme et ils ne mordent aucune emprise (le brief
    n'interdit que ce qui DEPASSE du pont).
    """
    for side in (-1.0, 1.0):
        _dashes(bm, side * (GROOVE_X - GLOW_HALF), side * (GROOVE_X + GLOW_HALF),
                APRON_AFT_Z + 0.20, APRON_FORE_Z - 0.60, along_z=True)
    _dashes(bm, AFT_Z + 0.14, APRON_AFT_Z - 0.06,
            -(GROOVE_X + GLOW_HALF), GROOVE_X + GLOW_HALF, along_z=False)


#: Le collecteur : de l'autre cote de la jonction, a cheval sur la fin du canal.
MANIFOLD_Z0 = JOINT_Z + 0.15                       # 8,15
MANIFOLD_Z1 = JOINT_Z + 1.45                       # 9,45
MANIFOLD_CZ = (MANIFOLD_Z0 + MANIFOLD_Z1) * 0.5
MANIFOLD_CY = -4.05
MANIFOLD_R = 0.62
MANIFOLD_HALF_X = 11.60
#: Les sections vitrees : c'est la seule matiere emissive du fichier avec l'anneau.
GLASS_SPANS = ((-0.70, 0.70), (-6.05, -5.35), (5.35, 6.05))


def build_manifold(bm: bmesh.types.BMesh) -> None:
    """Le terminus de l'artere : tube octogonal, colliers, section vitree.

    ⚠️ IL EST A `z >= 8,15`, DONC HORS DE LA POUPE PROPREMENT DITE, et c'est la
    seule position possible. Dans le bassin il mordrait un berceau ; sur la paroi
    avant il serait invisible (voir l'en-tete) ; ici il coiffe la fin du canal
    magenta, il se lit au-dessus du pont du corridor, et le blackout du LOT 8
    l'eteint avec tout le reste.
    """
    cuts = [-MANIFOLD_HALF_X]
    for a, b in sorted(GLASS_SPANS):
        cuts += [a, b]
    cuts.append(MANIFOLD_HALF_X)
    for i in range(len(cuts) - 1):
        x0, x1 = cuts[i], cuts[i + 1]
        glazed = any(abs(x0 - a) < 1e-9 and abs(x1 - b) < 1e-9
                     for a, b in GLASS_SPANS)
        material = "AA_Emissive_Engine" if glazed else "AA_Greeble"
        a0, a1 = _tube_x(bm, x0, x1, MANIFOLD_CY, MANIFOLD_CZ, MANIFOLD_R,
                         8, material)
        _face(bm, a0, material)
        _face(bm, list(reversed(a1)), material)
    # Les colliers de serrage (planche asset08) : six bagues courtes.
    for x in (-9.40, -7.60, -3.70, 3.70, 7.60, 9.40):
        a0, a1 = _tube_x(bm, x - 0.16, x + 0.16, MANIFOLD_CY, MANIFOLD_CZ,
                         MANIFOLD_R + 0.20, 8, "AA_Panel")
        _face(bm, a0, "AA_Panel")
        _face(bm, list(reversed(a1)), "AA_Panel")
    # Le bloc de jonction en croix, sur l'axe.
    # ⚠️ SON CHAPEAU N'EST PLUS EN `AA_Trim`. Rendu et regarde : l'ivoire froid
    # posait un rectangle BLANC de 3,7 x 1,5 m au milieu du cadre, plus clair que
    # tout le reste de l'image — un accent devenu le sujet. Il ne reste de l'ivoire
    # qu'un bandeau de 0,18 m sur la face avant.
    _box(bm, -1.85, 1.85, -4.95, CEILING_Y - 0.10, MANIFOLD_Z0 - 0.10,
         MANIFOLD_Z1 + 0.10, "AA_Greeble", "AA_Hull")
    _box(bm, -1.55, 1.55, -3.66, -3.48, MANIFOLD_Z1 + 0.10, MANIFOLD_Z1 + 0.16,
         "AA_Trim")
    # Les quatre pieds, poses sur la peau REELLE du corridor.
    for x in (-9.80, -4.60, 4.60, 9.80):
        s = STATION - MANIFOLD_CZ
        base = blc._surface_y(s, x) - 0.35
        _box(bm, x - 0.42, x + 0.42, base, MANIFOLD_CY + 0.10,
             MANIFOLD_CZ - 0.38, MANIFOLD_CZ + 0.38, "AA_Greeble")


# ==========================================================================
# 4. LA CHAINE DE BRIDES — le rebord du bassin (planche asset08)
# ==========================================================================


def build_rim_clamps(bm: bmesh.types.BMesh) -> None:
    """La chaine de brides : des BRACKETS qui chevauchent l'arete de rive.

    C'est la « ceinture d'alveole » de la planche `asset08`, transposee. Aucun
    collier ne peut faire le tour d'un berceau — l'emprise l'interdit — alors la
    chaine borde le BASSIN entier : un seul geste au lieu de trois impossibles.

    ⚠️ ELLE DEBORDE VERS L'INTERIEUR, ET C'EST LE POINT. Rendue et regardee, la
    premiere version (des blocs poses sur l'arete) laissait la paroi du bassin
    nue : deux grands trapezes gris de 7 m de haut, sans un pli, en plein cadre.
    Le bracket descend maintenant de 2,60 m le long de cette paroi et avance
    jusqu'a 0,50 m du pied — ce qui la nervure sans rien mettre au-dessus du pont.
    Marge a l'emprise des berceaux : `basin_x - 0,50 - 15,78`, soit 0,12 m dans la
    bande avant et 1,92 m dans la bande arriere.
    """
    z = APRON_FORE_Z - 0.20
    index = 0
    while z > AFT_Z + 0.70:
        length = 1.50 if index % 3 == 2 else 1.00
        band = _band_of(z - length * 0.5)
        crest_y, basin_x, crest_x = band[3], band[4], band[5]
        x_in = max(basin_x - 0.50, BASIN_MIN_X - 0.38)
        x_out = crest_x + 0.26
        for side in (-1.0, 1.0):
            _box(bm, side * x_in, side * x_out, crest_y - 2.60, crest_y + 0.46,
                 z - length, z, "AA_Greeble", "AA_Hull")
            if index % 3 == 2:
                _box(bm, side * (x_in + 0.16), side * (x_out - 0.16),
                     crest_y + 0.46, crest_y + 0.74, z - length + 0.24, z - 0.24,
                     "AA_Panel", "AA_Panel")
        z -= length + 0.85
        index += 1
    # Le rail de guidage (planche `asset08`) : une ligne horizontale a mi-paroi,
    # bande par bande. Sans lui, la paroi du bassin reste un trapeze de 7 m sans
    # une seule arete horizontale — a 32,7 px/m, une surface plate de cette taille
    # ne rend pas un pli.
    for _name, z_fore, z_aft, crest_y, basin_x, _crest_x, _wmax in BANDS:
        for side in (-1.0, 1.0):
            _box(bm, side * (basin_x - 0.28), side * basin_x,
                 crest_y - 3.55, crest_y - 3.05,
                 max(z_aft, AFT_Z + 0.10), min(z_fore, APRON_FORE_Z),
                 "AA_Greeble", "AA_Hull")


# ==========================================================================
# 4 bis. LES EPAULEMENTS AVANT — le relief que la face plane ne peut pas porter
# ==========================================================================
#  ⚠️ ILS SONT A `z >= 8,00`, DONC HORS EMPRISE, ET C'EST LEUR RAISON D'ETRE. La
#  face avant de la poupe est plane par obligation (voir `FORE_FACE_Z`) : elle
#  n'offre pas un centimetre de relief au moment precis ou le joueur decouvre la
#  poupe. Le seul volume libre est celui qui borde le corridor de part et d'autre,
#  `z in [8,00 ; 9,40]` et `|x| >= 11,4` — la ou le bordage s'arrete a 11,94 m. Ces
#  deux blocs etages y prennent le corridor en tenaille : ce sont eux qui donnent
#  a l'arrivee sa lecture de PORTE, et ils sont volontairement plus bas que le
#  collecteur pour ne pas lui voler l'axe.

SHOULDER_Z0 = JOINT_Z
SHOULDER_Z1 = JOINT_Z + 1.40
#: (x interieur, x exterieur, retrait en z, sommet)
SHOULDER_STAGES = (
    (11.40, 17.00, 0.00, -5.90),
    (12.55, 16.35, 0.22, -4.40),
    (13.60, 15.40, 0.46, CEILING_Y - 0.15),
)


def build_shoulders(bm: bmesh.types.BMesh) -> None:
    for side in (-1.0, 1.0):
        for i, (xi, xo, inset, top) in enumerate(SHOULDER_STAGES):
            _box(bm, side * xi, side * xo, -11.60, top,
                 SHOULDER_Z0 + inset, SHOULDER_Z1 - inset,
                 "AA_Greeble" if i == 0 else "AA_Hull", "AA_Hull")
        # Le bandeau de flanc, seul accent colore de la piece.
        _box(bm, side * 17.02, side * 16.86, -8.60, -6.10,
             SHOULDER_Z0 + 0.24, SHOULDER_Z1 - 0.24, "AA_Panel")


# ==========================================================================
# 5. LES PYLONES DE RIVE (planche asset07)
# ==========================================================================
#  ⚠️ ILS SONT SUR LES FLANCS PARCE QU'IL N'Y A PAS D'« ENTRE LES BERCEAUX ».
#  Le brief demande des masses hautes entre les groupes ; l'union des trois
#  emprises ne laisse pas un metre carre libre entre eux (en-tete). Les flancs
#  (|x| >= 16,20) et le massif arriere sont les deux seules zones ou du relief
#  vertical puisse exister, et c'est la qu'il est.

#: ⚠️ LES DEUX PAIRES SONT DANS LES BANDES 2 ET 3, PAS DANS LA BANDE 1. L'etagere
#: de rive n'existe qu'au-dela de l'arete, et la bande avant n'en a que 0,40 m —
#: un pylone y aurait ete un trait. Les bandes 2 et 3 offrent 0,80 et 1,20 m
#: d'etagere, et le pylone les enjambe de part et d'autre de l'arete : 1,70 m
#: d'assise en bande 2, 2,20 en bande 3.
PYLON_Z = (-0.40, -6.00)
#: Retrait de chaque etage, de part et d'autre, et son sommet.
PYLON_STAGES = ((0.00, 1.75, -8.60), (0.22, 1.45, -6.00),
                (0.45, 1.15, -4.20), (0.68, 0.80, CEILING_Y - 0.10))


def build_pylons(bm: bmesh.types.BMesh) -> None:
    """Les quatre pylones de rive (planche `asset07`) : fuseau etage, socle
    debordant, bandeau lateral.

    ⚠️ ILS SONT SUR LES FLANCS PARCE QU'IL N'Y A PAS D'« ENTRE LES BERCEAUX ». Le
    brief demande des masses hautes entre les groupes ; l'union des trois emprises
    ne laisse pas un metre carre libre entre eux (en-tete). Les flancs et le massif
    arriere sont les deux seules zones ou du relief vertical puisse exister.
    """
    for cz in PYLON_Z:
        band = _band_of(cz)
        x_in = band[4] - 0.50
        x_out = band[6] - 0.10
        for side in (-1.0, 1.0):
            for i, (inset, hz, top) in enumerate(PYLON_STAGES):
                _box(bm, side * (x_in + inset), side * (x_out - inset),
                     SOLE_Y, top, cz - hz, cz + hz,
                     "AA_Greeble" if i == 0 else "AA_Hull", "AA_Hull")
            _box(bm, side * (x_out - 0.24), side * (x_out - 0.40), -8.20, -5.20,
                 cz - 0.95, cz + 0.95, "AA_Panel", "AA_Panel")


# ==========================================================================
# 6. LES TOURS D'ECHANGE THERMIQUE (planche asset08)
# ==========================================================================
#  Elles se dressent sur le plateau du massif arriere, dans les DEUX creneaux
#  libres entre les trois nacelles : c'est la seule facon d'obtenir une masse
#  haute qui se lise entre les moteurs sans mordre un berceau.

TOWER_X = (-5.40, 5.40)
TOWER_Z = -10.05


def build_towers(bm: bmesh.types.BMesh) -> None:
    for cx in TOWER_X:
        # Socle evase, quatre contreforts.
        _prism(bm, cx, TOWER_Z, [1.52], AFT_PLATEAU_Y - 0.30, -7.55, 8,
               "AA_Greeble", "AA_Greeble")
        for a in (0.25, 0.75, 1.25, 1.75):
            ang = a * math.pi
            bx, bz = cx + 1.30 * math.cos(ang), TOWER_Z + 1.30 * math.sin(ang)
            _box(bm, bx - 0.34, bx + 0.34, AFT_PLATEAU_Y - 0.30, -6.40,
                 bz - 0.34, bz + 0.34, "AA_Greeble", "AA_Hull")
        # Fut cannele : 16 cotes, deux rayons alternes.
        _prism(bm, cx, TOWER_Z, [1.02, 0.90], -7.55, -4.55, 16,
               "AA_Hull", "AA_Greeble")
        # Diffuseur en cone et sa grille.
        _cone(bm, cx, TOWER_Z, 1.02, 1.58, -4.55, CEILING_Y - 0.22, 16,
              "AA_Hull", "AA_Panel")
        _prism(bm, cx, TOWER_Z, [1.58], CEILING_Y - 0.22, CEILING_Y - 0.10, 16,
               "AA_Panel", "AA_Panel")
    # Le bloc de ventilation central : bas, dans la colonne de poussee du moteur
    # central — rien de haut ne doit s'y trouver.
    _box(bm, -2.10, 2.10, AFT_PLATEAU_Y - 0.30, -6.90, TOWER_Z - 1.60,
         TOWER_Z + 1.60, "AA_Greeble", "AA_Hull")


# ==========================================================================
# Assemblage
# ==========================================================================

PARTS = (
    ("skin", build_skin, True),
    ("apron", build_apron, True),
    ("manifold", build_manifold, True),
    ("rim_clamps", build_rim_clamps, True),
    ("shoulders", build_shoulders, True),
    ("pylons", build_pylons, True),
    ("towers", build_towers, True),
    ("glow", build_glow_ring, False),      # rubans plats : pas de volume
)


def build_hull() -> bpy.types.Object:
    ak.set_faction(ak.FACTION_NULL_CHOIR)
    bm = bmesh.new()
    stats: dict[str, int] = {}
    for name, builder, closed in PARTS:
        piece = bmesh.new()
        builder(piece)
        if closed:
            _orient(piece, name)
        stats[name] = sum(len(f.verts) - 2 for f in piece.faces)
        mesh = bpy.data.meshes.new("_tmp_" + name)
        piece.to_mesh(mesh)
        piece.free()
        bm.from_mesh(mesh)
        bpy.data.meshes.remove(mesh)
    obj = _new_object("SternHull", bm)
    _weld(obj)
    ak.triangulate(obj)
    _project_uv(obj)
    obj["parts"] = json.dumps(stats)
    return obj


def _weld(obj: bpy.types.Object, dist: float = 1e-5) -> None:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)
    bm.to_mesh(obj.data)
    bm.free()


def _project_uv(obj: bpy.types.Object) -> None:
    """Projection en boite a la densite du corridor, dans un repere DECALE.

    Le decalage (`UV_SHIFT_Z`) met `v` en phase avec le troncon 5 a la jonction :
    sans lui, la carte y sauterait de 0,6 tuile. Voir l'en-tete.
    """
    obj.data.transform(Matrix.Translation(Vector((0.0, 0.0, UV_SHIFT_Z))))
    ak.box_project_uv(obj, TEXELS_PER_METER)
    obj.data.transform(Matrix.Translation(Vector((0.0, 0.0, -UV_SHIFT_Z))))
    obj.data.update()


# ==========================================================================
# Export — meme chaine d'axes que `build_long_cortege`, verifiee
# ==========================================================================

_AUTHOR_FIX = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def _author(v: Vector) -> Vector:
    return Vector((v.x, -v.z, v.y))


def export(obj: bpy.types.Object, filepath: str) -> dict:
    blc._assert_axis_chain()
    obj.data.transform(_AUTHOR_FIX)
    obj.data.update()
    obj.location = (0.0, 0.0, 0.0)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    staging = tempfile.mkdtemp(prefix="aegis-stern-hull-")
    staged = os.path.join(staging, os.path.basename(filepath))
    try:
        bpy.ops.export_scene.gltf(
            filepath=staged, export_format="GLB", export_yup=True,
            export_apply=True, use_selection=True, export_materials="EXPORT",
            export_cameras=False, export_lights=False, export_animations=False,
            export_skins=False, export_extras=False, export_tangents=True,
            export_normals=True, export_texcoords=True)
        report = _audit(staged)
        os.replace(staged, filepath)
    finally:
        if os.path.isdir(staging):
            for leftover in os.listdir(staging):
                os.remove(os.path.join(staging, leftover))
            os.rmdir(staging)
    return report


# ==========================================================================
# Les harnais — tout ce qui suit ECHOUE le build
# ==========================================================================


def _clip(poly: list[tuple[float, float]], x0: float, x1: float,
          z0: float, z1: float) -> list[tuple[float, float]]:
    """Sutherland-Hodgman : le polygone (x, z) rogne par le rectangle."""
    def half(pts, keep, coord, value, sign):
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            da = sign * (a[coord] - value)
            db = sign * (b[coord] - value)
            if da >= 0.0:
                out.append(a)
            if (da >= 0.0) != (db >= 0.0):
                t = da / (da - db)
                out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        return out
    poly = half(poly, None, 0, x0, 1.0)
    if not poly:
        return []
    poly = half(poly, None, 0, x1, -1.0)
    if not poly:
        return []
    poly = half(poly, None, 1, z0, 1.0)
    if not poly:
        return []
    return half(poly, None, 1, z1, -1.0)


def _area(poly: list[tuple[float, float]]) -> float:
    total = 0.0
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        total += a[0] * b[1] - b[0] * a[1]
    return abs(total) * 0.5


def _keepout_bite(points: list[tuple], tris: list[tuple[int, int, int]]) -> dict:
    """Quelle aire de decor DEPASSE dans une emprise de berceau ?

    ⚠️ MESURE EXACTE, PAS UN TEST DE SOMMETS. Un triangle peut traverser une
    emprise sans qu'aucun de ses trois sommets n'y soit. On coupe donc chaque
    triangle par le demi-espace `y > pont`, puis on rogne son ombre (x, z) par le
    rectangle : ce qui reste est de l'aire volee a un berceau, en metres carres.
    """
    worst = 0.0
    total = 0.0
    where: tuple | None = None
    for ia, ib, ic in tris:
        tri = [Vector(points[i]) for i in (ia, ib, ic)]
        if max(v.y for v in tri) <= DECK_Y + 1e-4:
            continue
        # Decoupe par y > DECK_Y.
        above: list[Vector] = []
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            da, db = a.y - DECK_Y, b.y - DECK_Y
            if da > 1e-4:
                above.append(a)
            if (da > 1e-4) != (db > 1e-4):
                t = da / (da - db)
                above.append(a + (b - a) * t)
        if len(above) < 3:
            continue
        shadow = [(v.x, v.z) for v in above]
        for cx in ENGINE_X:
            piece = _clip(shadow, cx - KEEPOUT_HALF_X, cx + KEEPOUT_HALF_X,
                          -KEEPOUT_HALF_Z, KEEPOUT_HALF_Z)
            if len(piece) < 3:
                continue
            area = _area(piece)
            if area > 1e-6:
                total += area
                if area > worst:
                    worst = area
                    where = (cx, min(v.y for v in above), max(v.y for v in above))
    return {"area": total, "worst": worst, "where": where}


def _audit(path: str) -> dict:
    gltf, blob = blc._read_glb(path)
    if gltf.get("images"):
        raise ak.ContractError(
            f"{path} : {len(gltf['images'])} image(s) embarquee(s) — "
            "le regime du niveau est le PBR par facteurs (ADR-0028).")

    report: dict = {"path": path, "bytes": os.path.getsize(path)}
    materials = [m.get("name", "?") for m in gltf.get("materials", [])]
    points: list[tuple] = []
    uvs: list[tuple] = []
    tris: list[tuple[int, int, int]] = []
    per_material: dict[str, float] = {}
    triangles = 0
    for mesh in gltf.get("meshes", []):
        for prim in mesh.get("primitives", []):
            attrs = prim["attributes"]
            if "TEXCOORD_0" not in attrs:
                raise ak.ContractError(
                    f"{path} : primitive sans TEXCOORD_0 — un maillage sans UV "
                    "est definitivement inhabitable (ADR-0028).")
            base = len(points)
            pos = ak.glb_accessor(gltf, blob, attrs["POSITION"])
            uv = ak.glb_accessor(gltf, blob, attrs["TEXCOORD_0"])
            points.extend(pos)
            uvs.extend(uv)
            idx = ak.glb_accessor(gltf, blob, prim["indices"])
            flat = [i[0] for i in idx]
            name = materials[prim["material"]] if "material" in prim else "?"
            area = 0.0
            for k in range(0, len(flat), 3):
                a, b, c = (base + flat[k + j] for j in range(3))
                tris.append((a, b, c))
                va, vb, vc = (Vector(points[i]) for i in (a, b, c))
                area += (vb - va).cross(vc - va).length * 0.5
            triangles += len(flat) // 3
            per_material[name] = per_material.get(name, 0.0) + area

    report["triangles"] = triangles
    report["vertices"] = len(points)
    report["materials"] = per_material
    total_area = sum(per_material.values())
    report["area"] = total_area
    glow = per_material.get("AA_Emissive_Engine", 0.0)
    report["glow_area"] = glow
    report["glow_share"] = glow / total_area if total_area else 0.0
    if glow <= 0.0:
        raise ak.ContractError("aucun AA_Emissive_Engine : l'artere n'arrive nulle part")

    if triangles > TRI_BUDGET:
        raise ak.ContractError(
            f"{triangles} triangles pour un budget de {TRI_BUDGET}")

    ys = [p[1] for p in points]
    report["y_min"], report["y_max"] = min(ys), max(ys)
    if report["y_max"] > CEILING_Y + 1e-6:
        raise ak.ContractError(
            f"plafond creve : y_max = {report['y_max']:.3f} > {CEILING_Y}")
    if report["y_min"] < KEEL_Y - 1e-6:
        raise ak.ContractError(
            f"sous la quille : y_min = {report['y_min']:.3f} < {KEEL_Y}")

    zs = [p[2] for p in points]
    report["z_min"], report["z_max"] = min(zs), max(zs)
    report["half_width"] = max(abs(p[0]) for p in points)
    if report["half_width"] < 18.0:
        raise ak.ContractError(
            f"demi-largeur {report['half_width']:.2f} < 18 m : l'evasement "
            "demande par le brief n'est pas atteint")

    bite = _keepout_bite(points, tris)
    report["keepout"] = bite
    if bite["area"] > 1e-6:
        raise ak.ContractError(
            f"{bite['area']:.4f} m2 de decor dans l'emprise d'un berceau "
            f"(pire triangle {bite['worst']:.4f} m2, {bite['where']})")

    report["junction"] = _assert_junction(points)
    report["uv"] = ak.texel_density(points, uvs, tris)
    report["width_profile"] = _width_profile(points, tris)
    return report


def _assert_junction(points: list[tuple]) -> dict:
    """Les 48 sommets du corridor doivent etre LA, au micron, des deux bords."""
    wanted = _joint_ring()
    worst = 0.0
    missing: list[str] = []
    fore = [p for p in points if abs(p[2] - JOINT_Z) < 1e-4]
    for i, (x, y) in enumerate(wanted):
        best = min((abs(p[0] - x) + abs(p[1] - y) for p in fore), default=9e9)
        worst = max(worst, best)
        if best > 1e-6:
            missing.append(f"#{i} ({x:+.6f} ; {y:+.6f}) ecart {best:.3e}")
    if missing:
        raise ak.ContractError(
            "l'anneau de jonction n'est pas celui du corridor : "
            + " | ".join(missing[:6]))
    return {"points": len(wanted), "worst": worst, "at_z": JOINT_Z,
            "half_width": max(abs(x) for x, _ in wanted)}


def _width_profile(points: list[tuple], tris: list) -> list[tuple[float, float]]:
    """La demi-largeur station par station, COUPEE dans le binaire.

    ⚠️ ON COUPE, ON NE CHERCHE PAS LES SOMMETS PROCHES. La peau est un loft a dix
    anneaux : entre deux marches il n'y a aucun sommet, et une mesure « sommets a
    moins de 30 cm » y rendait zero — la coque paraissait disparaitre sur six
    stations. On intersecte donc chaque triangle par le plan de la station et on
    prend le |x| maximum du segment obtenu.
    """
    out: list[tuple[float, float]] = []
    z = JOINT_Z
    while z >= TAIL_Z - 1e-9:
        widest = 0.0
        for ia, ib, ic in tris:
            tri = [points[i] for i in (ia, ib, ic)]
            zs = [v[2] for v in tri]
            if min(zs) > z or max(zs) < z:
                continue
            for i in range(3):
                a, b = tri[i], tri[(i + 1) % 3]
                if (a[2] - z) * (b[2] - z) > 0.0:
                    continue
                if abs(b[2] - a[2]) < 1e-12:
                    widest = max(widest, abs(a[0]), abs(b[0]))
                    continue
                t = (z - a[2]) / (b[2] - a[2])
                widest = max(widest, abs(a[0] + (b[0] - a[0]) * t))
        out.append((STATION - z, widest))
        z -= 1.0
    return out


# ==========================================================================
# Orchestration
# ==========================================================================


def build() -> dict:
    ak.reset_scene()
    obj = build_hull()
    parts = json.loads(obj["parts"])
    report = export(obj, OUTPUT)
    report["parts"] = parts
    return report


def _print(report: dict) -> None:
    print("")
    print("=" * 78)
    print("  LA POUPE DU LONG CORTEGE — carene (BRIEF-0106)")
    print("=" * 78)
    print(f"  {report['path']}")
    print(f"  {report['bytes'] / 1024:.1f} Kio · {report['triangles']} triangles "
          f"/ {TRI_BUDGET} ({100.0 * report['triangles'] / TRI_BUDGET:.1f} %) · "
          f"{report['vertices']} sommets")
    print("")
    print("  Par famille (triangles avant soudure) :")
    for name, count in sorted(report["parts"].items(), key=lambda kv: -kv[1]):
        print(f"    {name:<12} {count:>6}")
    print("")
    print("  Emprise :")
    print(f"    y  {report['y_min']:+8.3f} .. {report['y_max']:+8.3f}   "
          f"(quille {KEEL_Y} · plafond {CEILING_Y})")
    print(f"    z  {report['z_min']:+8.3f} .. {report['z_max']:+8.3f}   "
          f"(s = {STATION - report['z_max']:.2f} .. {STATION - report['z_min']:.2f})")
    print(f"    demi-largeur max {report['half_width']:.3f} m")
    print("")
    j = report["junction"]
    print(f"  Jonction s = {JOINT_S:.0f} (z = {j['at_z']:+.2f}) : {j['points']} "
          f"sommets, ecart max {j['worst']:.2e} m, demi-largeur "
          f"{j['half_width']:.3f} m")
    k = report["keepout"]
    print(f"  Emprise des berceaux : {k['area']:.6f} m2 de decor au-dessus du pont "
          f"(pire {k['worst']:.6f})")
    print("")
    uv = report["uv"]
    print(f"  UV — projection en boite {TEXELS_PER_METER:.2f} tuile/m "
          f"({1.0 / TEXELS_PER_METER:.2f} m/tuile), decalage z {UV_SHIFT_Z:+.2f}")
    print(f"    moyenne {uv['tiles_per_m_mean']:.4f} tuile/m "
          f"({uv['m_per_tile_mean']:.3f} m/tuile) · anisotropie max "
          f"{uv['anisotropy_max']:.3f} (borne racine(3) = 1,732)")
    print("")
    print("  Aire par materiau :")
    for name, area in sorted(report["materials"].items(), key=lambda kv: -kv[1]):
        print(f"    {name:<22} {area:9.1f} m2   "
              f"{100.0 * area / report['area']:5.2f} %")
    print("")
    print("  Profil de largeur (s -> demi-largeur) :")
    line = ""
    for s, w in report["width_profile"]:
        line += f"  {s:6.1f}:{w:6.2f}"
        if len(line) > 66:
            print("   " + line)
            line = ""
    if line:
        print("   " + line)
    print("=" * 78)
    print("")


# ==========================================================================
# La planche de recette — A LA CAMERA DU JEU (ADR-0006)
# ==========================================================================
# Tout le rig vient de `build_long_cortege` : camera (0 ; 14 ; 5), FOV 62
# vertical, trois directionnelles, aucune ombre portee. Il n'est pas recopie.
#
# ⚠️ ET LA POUPE EST RENDUE A SA VRAIE PLACE. `cortege_flyby.gd` immobilise le
# defilement a `stop_at() = LEAD_IN + station - hold`, ce qui pose le centre des
# berceaux a `z = -hold` en monde, soit -6,47 — et non a l'origine. Une planche
# cadree a z = 0 rendrait la poupe 6,47 m trop pres.

TILE_W = 1920
TILE_H = 1080
STERN_WORLD_Z = -T["hold_plane_y"]


def _scale_of(central: bool) -> float:
    return T["asset_scale"] * (T["central_scale"] if central else 1.0)


def _place(path: str, position: Vector, k: float, yaw: float = 0.0) -> list:
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    fresh = [o for o in bpy.context.scene.objects if o not in before]
    holder = bpy.data.objects.new(os.path.basename(path), None)
    bpy.context.collection.objects.link(holder)
    holder.location = blc._to_blender(position)
    holder.rotation_euler = Euler((0.0, 0.0, yaw), "XYZ")
    holder.scale = (k, k, k)
    for obj in fresh:
        if obj.parent is None:
            obj.parent = holder
            obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.visible_shadow = False
    return fresh


def _pose(objects: list, clip: str, frame: int, store: dict) -> None:
    for obj in objects:
        ad = obj.animation_data
        if ad is None:
            continue
        action = None
        for track in ad.nla_tracks:
            for strip in track.strips:
                if strip.action and strip.action.name.split(".")[0] == clip:
                    action = strip.action
        if action is None and ad.action and ad.action.name.split(".")[0] == clip:
            action = ad.action
        if action is None:
            continue
        ad.action = action
        for track in ad.nla_tracks:
            track.mute = True
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    for obj in objects:
        if obj.animation_data is None:
            continue
        store[obj.name] = (Vector(obj.location),
                           obj.rotation_quaternion.copy(), Vector(obj.scale))


def _freeze(store: dict) -> None:
    for name, (loc, quat, scl) in store.items():
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        obj.animation_data_clear()
        obj.location = loc
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = quat
        obj.scale = scl
    bpy.context.view_layer.update()


def _mount_groups(origin: Vector) -> None:
    """Les trois groupes, a la place exacte que leur donne `cortege_engine.gd`."""
    store: dict = {}
    for side in (-1.0, 0.0, 1.0):
        central = side == 0.0
        k = _scale_of(central)
        g = origin + Vector((side * SPACING, DECK_Y, 0.0))
        cradle = _place(os.path.join(MODELS, "stern_cradle.glb"), g, k)
        _pose(cradle, "Intact", 12, store)
        seat = g + Vector((0.0, T["engine_seat"].y * k, T["engine_seat"].z * k))
        engine = _place(os.path.join(MODELS, "stern_engine.glb"), seat, k)
        _pose(engine, "Fonctionnement", 12, store)
        total = int(T["central_anchors"] if central else T["lateral_anchors"])
        ay = (T["socket_y"] + T["anchor_size_y"] * 0.5) * k
        for i in range(total):
            if i < 2:
                cote = -1.0 if i == 0 else 1.0
                local = Vector((cote * T["socket_x"] * k, ay,
                                T["socket_z_front"] * k))
            elif total <= 3:
                local = Vector((0.0, ay, T["socket_z_rear"] * k))
            else:
                cote = -1.0 if i == 2 else 1.0
                local = Vector((cote * T["socket_x"] * k, ay,
                                T["socket_z_rear"] * k))
            _pose(_place(os.path.join(MODELS, "stern_anchor.glb"), g + local, k),
                  "Intact", 12, store)
        for cote in (-1.0, 1.0):
            for prof in (T["socket_z_front"], T["socket_z_rear"]):
                name = "stern_arm_mirror" if cote > 0.0 else "stern_arm"
                local = Vector((cote * (T["socket_x"] + 1.15) * k,
                                T["socket_y"] * k * 0.55, prof * k))
                yaw = -math.pi * 0.5 if cote > 0.0 else math.pi * 0.5
                _pose(_place(os.path.join(MODELS, f"{name}.glb"), g + local, k, yaw),
                      "Serre", 12, store)
    _freeze(store)


def _mount_corridor(origin: Vector) -> list:
    """Le troncon 5 du corridor, pour juger la jonction et le contraste."""
    return blc._import(os.path.join(MODELS, "long_cortege.glb"), "corridor",
                       origin + Vector((0.0, 0.0, STATION)))


def _tile(path: str, view: str, dark: bool = False, checker: bool = False) -> None:
    blc._plate_reset()
    origin = Vector((0.0, 0.0, STERN_WORLD_Z))
    hull = blc._import(OUTPUT, "stern_hull", origin)
    corridor = _mount_corridor(origin)
    groups = view != "nude"
    if groups:
        _mount_groups(origin)
    if checker:
        blc._apply_checker([o for o in bpy.context.scene.objects
                            if o.type == "MESH"])
    if dark:
        for mat in bpy.data.materials:
            if not mat.name.split(".")[0].startswith("AA_Emissive"):
                continue
            if not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    node.inputs["Emission Strength"].default_value = 0.0
    blc._plate_lights()

    if view == "joint":
        cam_pos = Vector((0.0, 9.0, 21.0))
        forward = Vector((0.0, -0.500, -0.866))
        up = Vector((0.0, 0.866, -0.500))
        fov = blc.CAM_FOV_V
    elif view == "top":
        cam_pos = Vector((0.0, 60.0, STERN_WORLD_Z))
        forward = Vector((0.0, -1.0, 0.0))
        up = Vector((0.0, 0.0, -1.0))
        fov = blc.CAM_FOV_V
    else:
        cam_pos = blc.CAM_POS
        forward = blc.CAM_FORWARD
        up = blc.CAM_UP
        fov = blc.CAM_FOV_V
    camera = blc._plate_camera("game", blc._to_blender(cam_pos),
                               blc._to_blender(forward), blc._to_blender(up), fov)
    metrics = blc._frame_coverage(DECK_Y)
    px = TILE_W / metrics["frame_width"]
    heads = {
        "game": ("1 — CAMERA DU JEU, les trois groupes montes  ·  la poupe est "
                 "posee a sa place de jeu (z = %.2f)" % STERN_WORLD_Z),
        "nude": ("2 — LA MEME, SANS LES GROUPES  ·  ce que la carene fait toute "
                 "seule : bassin, rive, pylones, massif arriere"),
        "joint": ("3 — LA JONCTION s = 500, vue rasante  ·  c'est la qu'une "
                  "erreur d'un centimetre se voit"),
        "top": ("4 — DE DESSUS  ·  l'evasement en marches et les trois emprises "
                "de berceau, laissees libres"),
    }
    head = heads[view]
    tint = (1.0, 0.88, 0.55)
    if dark:
        head = ("5 — BLACKOUT  ·  seul `AA_Emissive_Engine` est eteint : ce qui "
                "reste allume ici est mal range")
        tint = (1.0, 0.55, 0.55)
    if checker:
        head = ("6 — DAMIER UV a la perspective du jeu  ·  projection en boite "
                "%.2f tuile/m (%.2f m par tuile)"
                % (TEXELS_PER_METER, 1.0 / TEXELS_PER_METER))
        tint = (0.72, 1.0, 0.82)
    blc._label(camera, head, -0.96, 0.90, 0.028, TILE_W, TILE_H, tint)
    if view in ("game", "nude") and not checker:
        blc._label(camera,
                   f"camera du jeu (0 ; 14 ; 5), FOV 62 vertical, pont de poupe "
                   f"y = {DECK_Y:.2f} — cadre {metrics['frame_width']:.2f} m, "
                   f"{px:.1f} px/m en lateral",
                   -0.96, 0.84, 0.022, TILE_W, TILE_H)
        blc._label(camera,
                   "corridor 12,04 m de demi-largeur -> poupe 19,70 : "
                   "trois marches a s = 500 / 505,3 / 511,0",
                   -0.96, 0.79, 0.022, TILE_W, TILE_H, (0.72, 0.84, 1.0))
    blc._render(path, TILE_W, TILE_H)
    del hull, corridor


def render_plate(only: tuple[str, ...] | None = None, out: str = PLATE) -> None:
    """La planche complete, ou un sous-ensemble (`--views`) pour iterer.

    ⚠️ `--views` N'EST PAS LE LIVRABLE. Six vignettes Cycles coutent douze minutes ;
    juger une correction de silhouette n'en demande que trois. La planche livree
    est toujours celle sans argument.
    """
    staging = tempfile.mkdtemp(prefix="aegis-stern-plate-")
    tiles: list[tuple[str, int]] = []
    wanted = only or ("game", "nude", "joint", "top", "dark", "checker")
    try:
        for view in ("game", "nude", "joint", "top"):
            if view not in wanted:
                continue
            path = os.path.join(staging, f"{view}.png")
            _tile(path, view)
            tiles.append((path, TILE_H))
        if "dark" in wanted:
            path = os.path.join(staging, "dark.png")
            _tile(path, "game", dark=True)
            tiles.append((path, TILE_H))
        if "checker" in wanted:
            path = os.path.join(staging, "checker.png")
            _tile(path, "nude", checker=True)
            tiles.append((path, TILE_H))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        blc._compose(tiles, out, width=TILE_W)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    only = None
    out = PLATE
    for arg in argv:
        if arg.startswith("--views="):
            only = tuple(arg.split("=", 1)[1].split(","))
        if arg.startswith("--out="):
            out = os.path.abspath(arg.split("=", 1)[1])
    if "--plate-only" in argv:
        render_plate(only, out)
        return
    report = build()
    _print(report)
    if "--plate" in argv:
        render_plate(only, out)


if __name__ == "__main__":
    main()
