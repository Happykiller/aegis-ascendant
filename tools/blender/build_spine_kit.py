"""build_spine_kit.py — le kit de nœud d'epine du Long Cortege (BRIEF-0094).

    blender-aegis -b -P tools/blender/build_spine_kit.py
    blender-aegis -b -P tools/blender/build_spine_kit.py -- --plate
    ./scripts/build-hull.sh --check spine_kit        # + controle de determinisme

Produit `assets/imported/models/backgrounds/spine_kit.glb` et, avec `--plate`, la
planche de recette `docs/forge/output/BRIEF-0094-planche-epine.png`.

Le script EST la source (ADR-0008) : aucun `.blend` versionne, aucun alea, deux
executions successives rendent le meme sha256.


CE QUE CE FICHIER EST, ET POURQUOI IL EXISTE
============================================
Trois pieces, chacune modelisee dans SON repere, origine au point d'assemblage.
Le moteur les instancie sur le marqueur `Spine_NN` de la coque — qui porte
desormais le PLAN D'ASSISE DANS LE FOND DU CANAL (`cortege.spine_seat_y`).

    spine_cradle   le berceau, ancre au fond du canal   origine : centre, Y = assise
    spine_core     le CŒUR — la partie qui meurt        origine : sa base, sur le berceau
    spine_brace    une entretoise, posee 2 ou 4 fois    origine : son pied, sur le berceau

⚠️ LA RAISON DU KIT N'EST PAS ESTHETIQUE, ELLE EST MECANIQUE. Le nœud est
DESTRUCTIBLE. La coque cuisait cinq bulbes dans cinq maillages qui partagent un
seul jeu de materiaux : eteindre l'un, c'etait eteindre les cinq. C'est la meme
raison qui a sorti les hangars (BRIEF-0091) et les affuts (BRIEF-0093) de la
coque, et c'est la troisieme fois qu'elle se verifie.

Le partage est plus fin ici que pour les deux autres kits, et le brief le dit :
**le moteur detruit `spine_core` SEUL.** Le berceau et les entretoises restent en
place — un nœud abattu laisse une carcasse, pas un trou. D'ou la regle dure, et
son harnais : AUCUN EMISSIF HORS DU CŒUR. S'il y en avait ailleurs, la mort du
nœud ne se verrait pas.


LA TROISIEME SILHOUETTE, ET C'EST LE TEST D'ACCEPTATION
=======================================================
« En noir et blanc, emissifs coupes, les trois structures se distinguent. Le
hangar creuse, la tourelle depasse — les deux sont acquis. Le nœud d'epine doit
maintenant s'y ajouter sans ressembler a ni l'un ni l'autre. »

Ce qui separe les deux premieres est un axe : l'un CREUSE, l'autre DEPASSE. Une
troisieme piece ne peut pas se placer sur cet axe-la sans tomber du cote de l'un
des deux. Elle se place donc sur un autre :

    hangar       negatif, horizontal, RECTANGULAIRE    un cadre vide
    tourelle     positif, horizontal, TRAPU            un tambour et deux tubes
    nœud         positif, VERTICAL, EFFILE             un fut et des diagonales

Le nœud est la seule chose du niveau qui soit plus HAUTE que large (1,50 m pour
1,24 m d'emprise, et son fut ne fait que 0,52 m de large sur 1,20 m de haut), et
la seule qui porte des DIAGONALES — les entretoises, inclinees a 24 deg. Une
tourelle n'a rien d'oblique, un hangar n'a rien de vertical. Les deux signaux
sont geometriques : ils survivent au noir et blanc, et ils survivent aux 23 px/m
du post-traitement.

Six primitives principales, la regle du brief en autorise 6 a 8 :

    1. le berceau, socle octogonal aplati, ancre dans le fond du canal
    2. le fut, effile, de 0,52 a 0,30 m
    3. la lanterne, chapiteau evase — LE seul emissif de toute la piece
    4. le capot, sombre, qui coiffe la lanterne et l'empeche de baver
    5. l'aiguille
    6. les entretoises (2 ou 4, en miroir)


IL SIEGE AU FOND DE LA TRANCHEE, ET C'EST UN CHANGEMENT DE FOND
===============================================================
Le bulbe cuit siegeait au SOMMET de la crete dorsale — le point le plus haut du
vaisseau. La crete n'existe plus : BRIEF-0094 l'a remplacee par un canal enfonce
de 0,56 m sous son rebord. Le nœud siege donc DANS ce canal, sur la conduite
qu'il alimente.

Ce n'est pas un detail de mise en scene. `cortege_spine_node.gd` ecrit que le
nœud « est plus dur a atteindre qu'il n'est dur a tuer » : c'etait une intention
que la geometrie contredisait, puisqu'il etait posé sur le point le plus expose
de la coque. Il est maintenant loge entre deux rebords, et seuls sa lanterne et
son aiguille depassent du plan du bordé — 0,89 m sur 1,50.


L'ECHELLE DE DEPLIAGE — LA MEME QUE LE BORDE, ET C'EST OBLIGATOIRE
==================================================================
Le kit partage les slots du borde (`AA_Hull`, `AA_Greeble`, `AA_Trim`,
`AA_Emissive_Engine`). Deux echelles de depliage sur un MEME slot, c'est la faute
qu'a corrigee BRIEF-0090 sur Ambry : la carte sortirait au bon grain sur la coque
et au mauvais sur le nœud, cote a cote. Le kit est donc deplie a 0,200 tuile/m
(5,00 m par tuile) comme `bay_kit.glb` et `turret_kit.glb`.
"""

from __future__ import annotations

import json
import math
import os
import struct
import sys
import tempfile

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402  (doit suivre l'ajout au sys.path)

# ⚠️ LE KIT LIT SES COTES DANS LE SCRIPT DE LA COQUE, IL NE LES RECOPIE PAS.
# Meme raison que pour `bay_kit` et `turret_kit` : une assise calculee ici et une
# assise calculee la-bas divergeraient en silence, et aucun harnais separe ne le
# verrait. `build_turret_kit` est importe pour ses HARNAIS — le controle de
# solidite et le controle d'axe y sont ecrits, mesures et commentes ; les
# recopier, c'est se donner deux versions a maintenir de la meme preuve.
sys.path.insert(0, _HERE)
import build_long_cortege as cortege   # noqa: E402
import build_bay_kit as baykit         # noqa: E402  (planche : le hangar temoin)
import build_turret_kit as turretkit   # noqa: E402  (planche + harnais partages)

OUTPUT = os.path.join(_REPO, "assets/imported/models/backgrounds/spine_kit.glb")
PLATE = os.path.join(_REPO, "docs/forge/output/BRIEF-0094-planche-epine.png")
HULL = cortege.OUTPUT
FIGHTER = cortege.FIGHTER

# ==========================================================================
# Cotes maitresses — repere KIT (X lateral, Y haut, Z survol, +Z = PROUE)
# ==========================================================================
# Y = 0 est le plan d'ASSISE dans le fond du canal, c'est-a-dire le Y que porte
# desormais le marqueur `Spine_NN` de la coque. TOUTES les pieces sont modelisees
# sur ce plan.

#: Hauteur totale du nœud assemble. Brief : « 0,7 a 1,0 x la largeur du joueur
#: (1,76 m) -> viser 1,50 m ».
NODE_H = 1.50

# --- Le berceau -----------------------------------------------------------
#: Demi-emprise. ⚠️ Elle doit valoir `cortege.SPINE_FOOTPRINT_HX/HS` AU
#: MILLIMETRE : c'est avec elle que la coque echantillonne sa peau pour calculer
#: l'assise du marqueur. Deux valeurs qui derivent, c'est un berceau qui flotte
#: d'un cote. Verifie au harnais, comme `BAY_COAMING_W` et `TURRET_FOOTPRINT_R`.
CRADLE_HX = 0.66
CRADLE_HZ = 1.28
#: Le chanfrein des quatre angles : c'est lui qui accroche la lumiere cle a
#: n'importe quelle resolution, et c'est la seule depense de triangles qui ne
#: s'evapore pas au downscale (mesure de BRIEF-0093).
CRADLE_CHAMFER = 0.20
#: Hauteur au-dessus de l'assise. Le plateau porte le cœur ET les pieds des
#: entretoises.
CRADLE_TOP = 0.30
#: Retrait du plateau : le berceau est un tronc de pyramide, pas une boite.
CRADLE_TAPER = 0.08
#: ⚠️ PROFONDEUR ENTERREE, ET ELLE N'EST PAS DECORATIVE. Le fond du canal MONTE
#: dans le fuseau de proue : sous l'emprise de `Spine_01`, il accuse 0,047 m de
#: denivele (mesure a la coque, table au compte-rendu). Sans jupe, le berceau ne
#: poserait que d'un cote — exactement le defaut que BRIEF-0091 a corrige sur le
#: coaming du hangar.
CRADLE_BURIED = 0.26
#: La cuvette ou le cœur s'emboite : il y est ENFONCE, il n'est pas pose dessus.
#: ⚠️ ET C'EST ELLE QUI DONNE SON OFFSET D'ASSEMBLAGE AU CŒUR. Le brief pose
#: « origine a sa base, posee sur le berceau » : la base du cœur repose donc au
#: FOND de la cuvette, pas sur le plateau. Poser le cœur a `CRADLE_TOP` le ferait
#: flotter de 9 cm au-dessus de son logement — un defaut de 9 cm ne se voit sur
#: aucune planche a 23 px/m, et il se verrait sur toutes une fois le nœud abattu.
CRADLE_WELL_Y = CRADLE_TOP - 0.09
CRADLE_WELL_HX = 0.30

# --- Le cœur --------------------------------------------------------------
#: Ou le cœur se pose : au fond de la cuvette du berceau.
CORE_LIFT = CRADLE_WELL_Y
#: Hauteur du cœur : le total moins l'emboitement. 1,29 m.
CORE_H = NODE_H - CORE_LIFT
#: Le fut, effile. ⚠️ Sa MINCEUR est le signal : 0,52 m de large pour 1,29 m de
#: haut, c'est la seule piece du niveau plus haute que large.
CORE_BASE_HX = 0.26
CORE_NECK_HX = 0.15
CORE_FOOT_Y = 0.10
CORE_NECK_Y = 0.68
#: La lanterne — chapiteau evase, et LE seul emissif de tout le kit.
#: ⚠️ 0,30 m de haut et non 0,20 : sous 9 cm un relief disparait au downscale, et
#: sous ~5 px une bande lumineuse cesse d'etre une bande pour devenir un point.
#: A 23 px/m, 0,30 m font 7 px — ça tient.
LANTERN_Y0 = CORE_NECK_Y
LANTERN_Y1 = CORE_NECK_Y + 0.30
LANTERN_HX = 0.34
#: ⚠️ LA COURONNE — ET SANS ELLE LE NŒUD EST ETEINT VU DU JEU. Mesure faite sur
#: le premier tirage de la planche : la camera plonge a 70 deg, donc a 20 deg de
#: la VERTICALE. Un flanc de lanterne, meme evase, lui est presente presque de
#: profil et ne rend quasiment aucun pixel ; le capot, lui, occupe tout le
#: dessus. Resultat : un nœud parfaitement sombre a la perspective du jeu — la
#: seule cible du niveau dont la recompense arrive quarante secondes plus tard,
#: et on ne la voyait pas.
#:
#: La reponse est une surface emissive qui REGARDE LA CAMERA : un anneau
#: quasi-horizontal de 16 cm de large au sommet de la lanterne, entre son bord
#: (0,34) et le pied du capot (0,18). Vu d'en haut, le nœud est un anneau clair
#: autour d'une pointe sombre — une figure que ni la tourelle ni le hangar ne
#: produisent. Vu de cote, c'est toujours une lanterne coiffee.
SHOULDER_Y = LANTERN_Y1 + 0.02
SHOULDER_HX = 0.18
#: Le capot : sombre, il coiffe la lanterne. Sans lui, l'emissif bave vers le
#: haut sur toute la piece et le nœud redevient la boule lumineuse qu'on remplace.
HOOD_Y1 = SHOULDER_Y + 0.20
HOOD_TOP_HX = 0.115
#: L'aiguille : elle finit la silhouette et elle donne au nœud sa verticale.
NEEDLE_Y1 = CORE_H
NEEDLE_HX = 0.055
CORE_SEG = 8

# --- L'entretoise ---------------------------------------------------------
#: Le pied, sur le plateau du berceau. ⚠️ Il doit rester DANS l'emprise :
#: `BRACE_FOOT_R + BRACE_HX` ne peut pas depasser `CRADLE_HX` (verifie au
#: harnais), sans quoi l'entretoise porte a faux au-dessus du fond du canal.
BRACE_FOOT_R = 0.50
BRACE_HX = 0.10
BRACE_HZ = 0.10
#: Debord de la semelle. ⚠️ `BRACE_FOOT_R + BRACE_HX + BRACE_PAD` doit
#: rester <= `CRADLE_HX` : une entretoise dont la semelle deborde du berceau
#: porte a faux au-dessus du fond du canal. Verifie au harnais.
BRACE_PAD = 0.03
#: La montee et l'INCLINAISON. C'est elle le second signal de silhouette : rien
#: d'autre dans le niveau n'est oblique. 0,28 m de deport pour 0,62 m de montee
#: = 24,3 deg.
BRACE_H = 0.62
BRACE_LEAN = 0.34
#: Le collier du haut : il ENSERRE le fut, il ne l'effleure pas.
BRACE_COLLAR_HX = 0.115
BRACE_COLLAR_HZ = 0.13
BRACE_COLLAR_H = 0.17

#: Emprise hors-tout posee sur la peau. Elle est celle du berceau : les
#: entretoises se posent DESSUS.
FOOTPRINT_HX = CRADLE_HX
FOOTPRINT_HZ = CRADLE_HZ

#: Meme densite que le borde : voir l'en-tete (deux echelles sur un meme slot).
TEXELS_PER_METER = cortege.HULL_TEXELS_PER_METER

#: Budget. Un nœud assemble (berceau + cœur + 4 entretoises) ; cinq nœuds au
#: niveau. Large au regard des 26 400 triangles de la coque et des 90 000 du
#: budget total, mais il n'a aucune raison d'etre depense : la piece est petite
#: et vue de loin.
TRI_BUDGET_ASSEMBLED = 1_400
TRI_BUDGET_LEVEL = 7_000

#: Couleurs reservees aux TIRS (charte SS3) : interdites ici comme ailleurs.
FORBIDDEN_HEX = cortege.FORBIDDEN_HEX

#: Les trois noms de nœuds. Ils sont FIGES PAR LE BRIEF, pas choisis ici : le
#: moteur monte par le NOM, et le harnais echoue si l'un manque, si l'un est en
#: trop, ou si l'un porte un enfant.
PART_NAMES = ("spine_cradle", "spine_core", "spine_brace")

#: OU CHAQUE PIECE TOMBE DANS LE NŒUD ASSEMBLE, et combien de fois.
#: ⚠️ Ce n'est pas une commodite de rapport : sans elle, l'aire par materiau se
#: mesurerait dans le repere de CHAQUE piece, ou la jupe enterree du berceau
#: passe pour visible.
ASSEMBLY_OFFSET: dict[str, tuple[float, float, float]] = {
    "spine_cradle": (0.0, 0.0, 0.0),
    "spine_core": (0.0, CORE_LIFT, 0.0),
    "spine_brace": (BRACE_FOOT_R, CRADLE_TOP, 0.0),
}
#: L'entretoise est posee QUATRE fois dans l'assemblage de reference.
ASSEMBLY_COPIES: dict[str, int] = {"spine_cradle": 1, "spine_core": 1,
                                   "spine_brace": 4}

#: LES DEUX FAMILLES — c'est le livrable « variete », et le brief les nomme :
#: « le moteur en pose deux ou quatre, en miroir ». Aucune geometrie nouvelle.
#: (nom, nombre d'entretoises, deport en Z de chaque paire)
FAMILIES: tuple[tuple[str, int, float], ...] = (
    ("A - deux entretoises", 2, 0.0),
    ("B - quatre entretoises", 4, 0.78),
)


# ==========================================================================
# Primitives — bobinage CALCULE, jamais suppose
# ==========================================================================


def _new_object(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    """Objet a 7 slots normalises, SANS `recalc_face_normals`.

    Meme raison que sur la coque et sur les deux autres kits : l'heuristique de
    bmesh peut retourner une piece entiere, et une piece retournee DISPARAIT en
    jeu (culling arriere) sans qu'aucune bbox, aucun compte de triangles ni
    aucune mesure d'UV ne le voie.
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


def _face_facing(bm: bmesh.types.BMesh, verts: list, material: str,
                 want: Vector):
    """Une face dont la normale part du cote `want`. DETERMINISTE.

    Le bobinage est CALCULE et non ecrit a la main : le fut est effile, le capot
    est renverse, l'entretoise est inclinee — une regle ecrite serait fausse une
    fois sur deux, et une face retournee ne se voit sur aucune mesure.
    """
    ring = list(verts)
    normal = (ring[1].co - ring[0].co).cross(ring[2].co - ring[0].co)
    if normal.dot(want) < 0.0:
        ring.reverse()
    return _face(bm, ring, material)


def _quad_facing(bm: bmesh.types.BMesh, a, b, c, d, material: str,
                 want: Vector):
    return _face_facing(bm, [a, b, c, d], material, want)


def _octagon(hx: float, hz: float, chamfer: float) -> list[tuple[float, float]]:
    """Rectangle a quatre angles coupes, dans le plan (x, z), sens direct."""
    c = min(chamfer, min(hx, hz) * 0.9)
    return [
        (hx - c, hz), (hx, hz - c), (hx, -(hz - c)), (hx - c, -hz),
        (-(hx - c), -hz), (-hx, -(hz - c)), (-hx, hz - c), (-(hx - c), hz),
    ]


def _regular(hx: float, segments: int) -> list[tuple[float, float]]:
    """Polygone regulier de rayon circonscrit tel que la DEMI-LARGEUR vaille
    `hx` : c'est la cote qui se mesure sur la bbox, donc la seule qui doit etre
    juste au harnais."""
    radius = hx / math.cos(math.pi / segments)
    return [(radius * math.sin(2.0 * math.pi * (k + 0.5) / segments),
             radius * math.cos(2.0 * math.pi * (k + 0.5) / segments))
            for k in range(segments)]


def _loft(bm: bmesh.types.BMesh,
          stops: list[tuple[float, list[tuple[float, float]]]],
          materials: list[str], cap_low: str | None,
          cap_high: str | None,
          offsets: list[tuple[float, float]] | None = None) -> list:
    """Empile des anneaux et les relie. Rend les anneaux de sommets crees.

    `stops` : (y, points en (x, z)). `materials` : le materiau de la bande
    montante `i -> i+1`. `offsets` : un decalage (dx, dz) par etage — c'est ce
    qui permet a l'entretoise d'etre INCLINEE sans une seule rotation ecrite.
    """
    rings: list[list] = []
    for level, (y, points) in enumerate(stops):
        dx, dz = offsets[level] if offsets else (0.0, 0.0)
        rings.append([bm.verts.new(Vector((x + dx, y, z + dz)))
                      for x, z in points])
    for i in range(len(rings) - 1):
        low, high = rings[i], rings[i + 1]
        material = materials[i]
        for k in range(len(low)):
            m = (k + 1) % len(low)
            mid = (low[k].co + low[m].co + high[m].co + high[k].co) * 0.25
            axis_x = 0.5 * (stops[i][1][k][0] + stops[i][1][m][0]) \
                + 0.5 * (stops[i + 1][1][k][0] + stops[i + 1][1][m][0])
            axis_z = 0.5 * (stops[i][1][k][1] + stops[i][1][m][1]) \
                + 0.5 * (stops[i + 1][1][k][1] + stops[i + 1][1][m][1])
            want = Vector((axis_x, 0.0, axis_z))
            if want.length < 1e-9:
                want = Vector((mid.x, 0.0, mid.z))
            _quad_facing(bm, low[k], low[m], high[m], high[k], material, want)
    if cap_low is not None:
        _face_facing(bm, rings[0], cap_low, Vector((0.0, -1.0, 0.0)))
    if cap_high is not None:
        _face_facing(bm, rings[-1], cap_high, Vector((0.0, 1.0, 0.0)))
    return rings


def _box(bm: bmesh.types.BMesh, cx: float, cz: float,
         hx: float, hz: float, y0: float, y1: float,
         side: str, top: str, bottom: str | None = None) -> None:
    points = [(cx - hx, cz - hz), (cx + hx, cz - hz),
              (cx + hx, cz + hz), (cx - hx, cz + hz)]
    rings: list[list] = []
    for y in (y0, y1):
        rings.append([bm.verts.new(Vector((x, y, z))) for x, z in points])
    centre = Vector((cx, 0.0, cz))
    for k in range(4):
        m = (k + 1) % 4
        mid = (rings[0][k].co + rings[0][m].co) * 0.5
        _quad_facing(bm, rings[0][k], rings[0][m], rings[1][m], rings[1][k],
                     side, Vector((mid.x - centre.x, 0.0, mid.z - centre.z)))
    _face_facing(bm, rings[1], top, Vector((0.0, 1.0, 0.0)))
    _face_facing(bm, rings[0], bottom or side, Vector((0.0, -1.0, 0.0)))


# ==========================================================================
# Le berceau
# ==========================================================================


def build_cradle() -> bpy.types.Object:
    """Le socle qui ancre le nœud au fond du canal — plus large que le cœur.

    Un tronc de pyramide octogonal, enterre de 0,26 m, coiffe d'un plateau creuse
    d'une cuvette ou le cœur s'EMBOITE. La cuvette n'est pas un ornement : c'est
    elle qui fait lire « le cœur est monte dans le berceau » plutot que « pose
    dessus », et un creux porte une ombre qui survit au downscale (BRIEF-0093).

    ⚠️ LES PAROIS DE LA CUVETTE REGARDENT VERS L'AXE, ET C'EST L'INVERSE DE TOUT
    LE RESTE DE LA PIECE. Un creux est un solide vu de l'interieur : la matiere
    est DEHORS. Elles sont donc emises a la main, avec un `want` dirige vers
    l'axe, et non par `_loft()` qui oriente vers l'exterieur — c'est exactement
    la faute que `_assert_solid()` de `build_turret_kit` a ete ecrit pour
    attraper (« un controle qui se trompe dans les deux sens est pire que pas de
    controle »).
    """
    bm = bmesh.new()
    base = _octagon(CRADLE_HX, CRADLE_HZ, CRADLE_CHAMFER)
    shelf = _octagon(CRADLE_HX - CRADLE_TAPER, CRADLE_HZ - CRADLE_TAPER,
                     CRADLE_CHAMFER)
    lip = _octagon(CRADLE_HX - CRADLE_TAPER - 0.02,
                   CRADLE_HZ - CRADLE_TAPER - 0.02, CRADLE_CHAMFER)
    _loft(bm, [(-CRADLE_BURIED, base), (0.06, base),
               (CRADLE_TOP - 0.06, shelf), (CRADLE_TOP, lip)],
          ["AA_Greeble", "AA_Greeble", "AA_Greeble"],
          cap_low="AA_Greeble", cap_high=None)
    # Le plateau, perce de sa cuvette. Le plateau est un octogone et la bouche
    # aussi : les deux ont huit sommets ranges par angle croissant, la couronne
    # se pave donc sans triangle degenere.
    mouth = _regular(CRADLE_WELL_HX, CORE_SEG)
    floor = _regular(CRADLE_WELL_HX - 0.03, CORE_SEG)
    top_ring = [bm.verts.new(Vector((x, CRADLE_TOP, z))) for x, z in lip]
    mouth_ring = [bm.verts.new(Vector((x, CRADLE_TOP, z))) for x, z in mouth]
    floor_ring = [bm.verts.new(Vector((x, CRADLE_WELL_Y, z))) for x, z in floor]
    for k in range(CORE_SEG):
        m = (k + 1) % CORE_SEG
        _quad_facing(bm, top_ring[k], top_ring[m], mouth_ring[m], mouth_ring[k],
                     "AA_Hull", Vector((0.0, 1.0, 0.0)))
        mid = (mouth_ring[k].co + mouth_ring[m].co) * 0.5
        _quad_facing(bm, mouth_ring[k], mouth_ring[m], floor_ring[m],
                     floor_ring[k], "AA_Greeble",
                     Vector((-mid.x, 0.0, -mid.z)))
    _face_facing(bm, floor_ring, "AA_Trim", Vector((0.0, 1.0, 0.0)))
    return _new_object("spine_cradle", bm)


# ==========================================================================
# Le cœur — la seule piece qui meurt, la seule qui porte l'emissif
# ==========================================================================


def build_core() -> bpy.types.Object:
    """Fut effile, lanterne evasee, capot sombre, aiguille.

    ⚠️ L'EMISSIF EST ICI ET NULLE PART AILLEURS, ET C'EST UNE REGLE DURE DU
    BRIEF : « le moteur eteint et detruit `spine_core` seul — berceau et
    entretoises restent en place. Aucun emissif hors du cœur, sans quoi la mort
    du nœud ne se verra pas. » Le harnais compte l'aire emissive des trois
    pieces et echoue le build si l'une des deux autres en porte.

    Et il est CONFINE : la lanterne est un anneau de 0,30 m sur une piece de
    1,20, coiffee d'un capot plus large qu'elle. Le brief de la tourelle posait
    « œil <= 25 pct de la piece » comme regle dure ; on la reprend telle quelle,
    faute d'avoir une raison d'etre plus genereux avec la seule cible dont la
    recompense arrive quarante secondes plus tard.
    """
    bm = bmesh.new()
    base = _regular(CORE_BASE_HX, CORE_SEG)
    neck = _regular(CORE_NECK_HX, CORE_SEG)
    lantern_low = _regular(LANTERN_HX - 0.14, CORE_SEG)
    lantern_high = _regular(LANTERN_HX, CORE_SEG)
    shoulder = _regular(SHOULDER_HX, CORE_SEG)
    hood_top = _regular(HOOD_TOP_HX, CORE_SEG)
    needle_low = _regular(NEEDLE_HX, CORE_SEG)
    needle_high = _regular(NEEDLE_HX * 0.35, CORE_SEG)
    _loft(bm, [
        (0.0, base),
        (CORE_FOOT_Y, base),
        (CORE_NECK_Y, neck),
        (LANTERN_Y0 + 0.05, lantern_low),
        (LANTERN_Y1, lantern_high),
        (SHOULDER_Y, shoulder),
        (HOOD_Y1, hood_top),
        (HOOD_Y1 + 0.03, needle_low),
        (NEEDLE_Y1, needle_high),
    ], [
        "AA_Greeble",           # le pied, dans la cuvette
        "AA_Greeble",           # le fut
        "AA_Emissive_Engine",   # l'evasement de la lanterne
        "AA_Emissive_Engine",   # le flanc de la lanterne
        "AA_Emissive_Engine",   # LA COURONNE — la seule face qui regarde le jeu
        "AA_Greeble",           # le capot
        "AA_Greeble",           # le col de l'aiguille
        "AA_Trim",              # l'aiguille
    ], cap_low="AA_Greeble", cap_high="AA_Trim")
    return _new_object("spine_core", bm)


# ==========================================================================
# L'entretoise
# ==========================================================================


def build_brace() -> bpy.types.Object:
    """Une diagonale : pied sur le berceau, collier sur le fut.

    ⚠️ ELLE EST MODELISEE PENCHEE, PAS TOURNEE A L'ASSEMBLAGE. Le moteur pose la
    piece par une translation et un yaw autour de Y — c'est ce que fait deja
    `turret_kit` pour ses coffrets. Lui demander en plus un tangage introduirait
    un angle a recalculer cote moteur, donc une seconde ecriture de la meme cote,
    donc une divergence. L'inclinaison est DANS la geometrie : elle est juste par
    construction, et le harnais la remesure sur le binaire.

    Origine : le PIED, cote berceau (le brief le fige). Le moteur pose donc la
    piece a (+/-BRACE_FOOT_R, CRADLE_TOP, +/-dz) avec un yaw de 0 ou de pi ; la
    piece penche toujours vers son -X local, donc toujours vers l'axe.
    """
    bm = bmesh.new()
    section = [(-BRACE_HX, -BRACE_HZ), (BRACE_HX, -BRACE_HZ),
               (BRACE_HX, BRACE_HZ), (-BRACE_HX, BRACE_HZ)]
    pad = [(-BRACE_HX - BRACE_PAD, -BRACE_HZ - BRACE_PAD),
           (BRACE_HX + BRACE_PAD, -BRACE_HZ - BRACE_PAD),
           (BRACE_HX + BRACE_PAD, BRACE_HZ + BRACE_PAD),
           (-BRACE_HX - BRACE_PAD, BRACE_HZ + BRACE_PAD)]
    thin = [(-BRACE_HX * 0.78, -BRACE_HZ), (BRACE_HX * 0.78, -BRACE_HZ),
            (BRACE_HX * 0.78, BRACE_HZ), (-BRACE_HX * 0.78, BRACE_HZ)]
    lean = BRACE_LEAN
    _loft(bm, [
        (-0.05, pad),
        (0.07, pad),
        (0.16, section),
        (BRACE_H - BRACE_COLLAR_H, thin),
        (BRACE_H, thin),
    ], ["AA_Greeble", "AA_Greeble", "AA_Hull", "AA_Hull"],
        cap_low="AA_Greeble", cap_high="AA_Hull",
        offsets=[(0.0, 0.0), (0.0, 0.0), (-lean * 0.16 / BRACE_H, 0.0),
                 (-lean * (BRACE_H - BRACE_COLLAR_H) / BRACE_H, 0.0),
                 (-lean, 0.0)])
    # Le collier : il enserre le fut. Sa demi-largeur en X le fait mordre sur
    # l'axe du nœud (verifie au harnais : il doit RECOUVRIR le fut, pas
    # l'effleurer).
    _box(bm, -lean, 0.0, BRACE_COLLAR_HX, BRACE_COLLAR_HZ,
         BRACE_H - BRACE_COLLAR_H, BRACE_H + 0.02,
         "AA_Greeble", "AA_Trim")
    return _new_object("spine_brace", bm)


# ==========================================================================
# Harnais de scene (avant export)
# ==========================================================================

#: ⚠️ COMBIEN DE COQUES FERMEES PAR PIECE, ET C'EST UN CONTRAT. Un volume qui
#: apparait ou qui disparait est une faute de frappe qui ne se voit sur aucune
#: planche (precedent mesure au BRIEF-0093 : deux colliers de conduite fusionnes
#: en un seul, restes ainsi jusqu'a ce que ce compte soit ECRIT).
SHELL_COUNT: dict[str, int] = {
    "spine_cradle": 1,
    "spine_core": 1,
    "spine_brace": 2,          # la jambe, le collier
}


def build_parts() -> list[bpy.types.Object]:
    parts = [build_cradle(), build_core(), build_brace()]
    names = [obj.name for obj in parts]
    if names != list(PART_NAMES):
        raise ak.ContractError(
            f"contrat de noms rompu : {names} au lieu de {list(PART_NAMES)}")
    for obj in parts:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
        bm.to_mesh(obj.data)
        bm.free()
        # ⚠️ APRES le soudage et AVANT la triangulation : c'est le maillage soude
        # qui part a l'export, et c'est la fusion de deux sommets qui ferait
        # apparaitre une arete a trois faces. Le controle doit voir la meme
        # topologie que Godot. `_assert_solid` VIT DANS `build_turret_kit` : sa
        # demonstration (bord, bobinage, volume signe) y est ecrite et mesuree,
        # la recopier donnerait deux versions de la meme preuve.
        turretkit._assert_solid(obj)
        found = len(turretkit._shell_report(obj.data)["volumes"])
        if found != SHELL_COUNT[obj.name]:
            raise ak.ContractError(
                f"{obj.name} : {found} coque(s) fermee(s) au lieu de "
                f"{SHELL_COUNT[obj.name]} — un volume a fusionne avec un autre "
                "ou n'a pas ete emis")
        ak.triangulate(obj)
        ak.shade_smooth_by_angle(obj, angle_deg=26.0)
        ak.box_project_uv(obj, TEXELS_PER_METER)
    return parts


# ==========================================================================
# Export — meme chaine d'axes que la coque (ADR-0008)
# ==========================================================================

_YUP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
_AUTHOR_FIX = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def _author(v: Vector) -> Vector:
    return Vector((v.x, -v.z, v.y))


def _assert_axis_chain() -> None:
    """La chaine complete rend l'identite, sur des temoins ASYMETRIQUES.

    L'entretoise penche vers son -X : une chaine fausse d'un demi-tour la ferait
    pencher vers l'exterieur, les quatre a la fois, et la bounding box du kit
    serait rigoureusement la meme.
    """
    for probe in (Vector((1.0, 2.0, 3.0)), Vector((-0.28, 0.62, 0.0)),
                  Vector((0.62, -0.26, 1.05))):
        author = _author(probe)
        if (author - _AUTHOR_FIX.to_3x3() @ probe).length > 1e-9:
            raise ak.ContractError("_author() et _AUTHOR_FIX divergent")
        if (_YUP.to_3x3() @ author - probe).length > 1e-9:
            raise ak.ContractError("chaine d'axes rompue")


def _read_glb(path: str) -> tuple[dict, bytes]:
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:4] != b"glTF":
        raise ak.ContractError(f"{path} : ce n'est pas un glTF binaire")
    gltf: dict | None = None
    blob = b""
    offset = 12
    while offset < len(data):
        length, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset:offset + length]
        offset += length
        if kind == 0x4E4F534A:
            gltf = json.loads(chunk)
        elif kind == 0x004E4942:
            blob = chunk
    if gltf is None:
        raise ak.ContractError(f"{path} : chunk JSON absent")
    return gltf, blob


def export(parts: list[bpy.types.Object], filepath: str) -> dict:
    _assert_axis_chain()
    for obj in parts:
        obj.data.transform(_AUTHOR_FIX)
        obj.data.update()
        obj.location = (0.0, 0.0, 0.0)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    staging = tempfile.mkdtemp(prefix="aegis-spinekit-")
    staged = os.path.join(staging, os.path.basename(filepath))
    try:
        bpy.ops.export_scene.gltf(
            filepath=staged, export_format="GLB", export_yup=True,
            export_apply=True, use_selection=True, export_materials="EXPORT",
            export_cameras=False, export_lights=False, export_animations=False,
            export_skins=False, export_extras=False, export_tangents=True,
            export_normals=True, export_texcoords=True,
        )
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


def _accessor(gltf: dict, blob: bytes, index: int) -> list[tuple]:
    return turretkit._accessor(gltf, blob, index)


def _indices(gltf: dict, blob: bytes, prim: dict) -> list[int]:
    return turretkit._indices(gltf, blob, prim)


def _audit(path: str) -> dict:
    """Relit le `.glb` PRODUIT et verifie tout ce que le brief exige.

    On lit le binaire et non la scene en memoire : c'est la seule chose que Godot
    chargera. Les trois coques du depot sorties sans UV (ADR-0028) avaient toutes
    une scene Blender parfaite.
    """
    gltf, blob = _read_glb(path)
    problems: list[str] = []
    materials = [m.get("name", f"#{i}")
                 for i, m in enumerate(gltf.get("materials", []))]
    nodes = gltf.get("nodes", [])
    roots = gltf.get("scenes", [{}])[0].get("nodes", list(range(len(nodes))))
    root_names = [nodes[i].get("name", "?") for i in roots]

    for name in PART_NAMES:
        if name not in root_names:
            problems.append(f"piece '{name}' absente du kit — le moteur monte "
                            "par le NOM, il ne la trouverait pas")
    for name in root_names:
        if name not in PART_NAMES:
            problems.append(f"nœud inattendu : '{name}'")

    stats: dict[str, dict] = {}
    prims_total = prims_uv = prims_tan = 0
    triangles_total = 0
    used_materials: set[str] = set()
    area_by_material: dict[str, float] = {}
    built_area: dict[str, float] = {}
    seen_area: dict[str, float] = {}
    emissive_by_part: dict[str, float] = {}
    total_area = 0.0
    total_built = 0.0
    total_seen = 0.0
    density: dict[str, dict] = {}
    part_points: dict[str, list[tuple]] = {}

    for index in roots:
        node = nodes[index]
        name = node.get("name", "?")
        if node.get("children"):
            problems.append(f"{name} : une piece de kit n'a pas d'enfant")
        if "mesh" not in node:
            problems.append(f"{name} : nœud sans maillage")
            continue
        if node.get("translation") or node.get("rotation") or node.get("scale"):
            problems.append(
                f"{name} : le nœud doit rester a l'identite — l'origine EST le "
                "point d'assemblage, le moteur pose la transformation")
        triangles = 0
        lo = [math.inf] * 3
        hi = [-math.inf] * 3
        pts: list[tuple] = []
        uvs: list[tuple] = []
        tris: list[tuple[int, int, int]] = []
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            prims_total += 1
            attrs = prim["attributes"]
            has_uv = "TEXCOORD_0" in attrs
            prims_uv += 1 if has_uv else 0
            prims_tan += 1 if "TANGENT" in attrs else 0
            acc = gltf["accessors"][attrs["POSITION"]]
            points = _accessor(gltf, blob, attrs["POSITION"])
            tri_indices = _indices(gltf, blob, prim)
            triangles += len(tri_indices) // 3
            material = materials[prim["material"]] if "material" in prim \
                else "<aucun>"
            used_materials.add(material)
            base = len(pts)
            pts += points
            if has_uv:
                uvs += _accessor(gltf, blob, attrs["TEXCOORD_0"])
            for axis in range(3):
                lo[axis] = min(lo[axis], acc["min"][axis])
                hi[axis] = max(hi[axis], acc["max"][axis])
            copies = ASSEMBLY_COPIES[name]
            oy = ASSEMBLY_OFFSET[name][1]
            for k in range(0, len(tri_indices) - 2, 3):
                ia, ib, ic = (tri_indices[k], tri_indices[k + 1],
                              tri_indices[k + 2])
                tris.append((base + ia, base + ib, base + ic))
                pa = Vector(points[ia])
                normal = (Vector(points[ib]) - pa).cross(
                    Vector(points[ic]) - pa)
                area = normal.length * 0.5
                total_area += area
                area_by_material[material] = \
                    area_by_material.get(material, 0.0) + area
                built_area[material] = built_area.get(material, 0.0) \
                    + area * copies
                total_built += area * copies
                if material == "AA_Emissive_Engine":
                    emissive_by_part[name] = \
                        emissive_by_part.get(name, 0.0) + area
                # ⚠️ L'AIRE VUE ET L'AIRE ASSEMBLEE, comptees a part (methode de
                # BRIEF-0093). La jupe ENTERREE du berceau pese lourd et ne rend
                # pas un pixel : melangee au reste, elle gonflerait la part
                # « structure ». Est vue une face au-dessus du plan d'assise dont
                # la normale ne regarde pas le fond du canal.
                cy = (points[ia][1] + points[ib][1] + points[ic][1]) / 3.0
                downward = normal.length > 1e-12 and \
                    normal.normalized().y < -0.5
                if cy + oy > -0.02 and copies and not downward:
                    seen_area[material] = \
                        seen_area.get(material, 0.0) + area * copies
                    total_seen += area * copies
        part_points[name] = pts
        if uvs:
            density[name] = turretkit._texel_density(pts, uvs, tris)
        # ⚠️ Le berceau et le cœur sont poses SUR L'AXE du marqueur : leur
        # origine doit y etre, au micron. Le defaut ne se verrait pas sur une
        # planche — cinq nœuds decales de 3 cm chacun dans une direction
        # differente, c'est cinq nœuds qui ne sont plus au milieu du canal.
        if name in ("spine_cradle", "spine_core"):
            turretkit._assert_on_axis(name, pts, problems, revolution=True)
        triangles_total += triangles
        stats[name] = {"triangles": triangles,
                       "min": tuple(lo), "max": tuple(hi),
                       "size": tuple(hi[a] - lo[a] for a in range(3))}

    # --- LA REGLE DURE DU BRIEF : AUCUN EMISSIF HORS DU CŒUR --------------
    for name in PART_NAMES:
        if name == "spine_core":
            continue
        if emissive_by_part.get(name, 0.0) > 1e-9:
            problems.append(
                f"{name} porte {emissive_by_part[name]:.3f} m2 d'emissif — le "
                "moteur ne detruit QUE `spine_core` : un emissif ailleurs "
                "resterait allume sur une carcasse, et la mort du nœud ne se "
                "verrait pas")
    if emissive_by_part.get("spine_core", 0.0) <= 1e-9:
        problems.append("spine_core ne porte aucun emissif : la cible vitale du "
                        "niveau ne s'annoncerait plus")

    # --- LES COTES DU BRIEF, RELEVEES SUR LE BINAIRE ----------------------
    cradle = stats.get("spine_cradle")
    core = stats.get("spine_core")
    brace = stats.get("spine_brace")
    if cradle is not None:
        if abs(cradle["size"][0] - 2 * CRADLE_HX) > 1e-3:
            problems.append(
                f"spine_cradle : {cradle['size'][0]:.4f} m de large au lieu de "
                f"{2 * CRADLE_HX:.2f}")
        if abs(cradle["max"][1] - CRADLE_TOP) > 1e-3:
            problems.append(
                f"spine_cradle : plateau a {cradle['max'][1]:.4f} au lieu de "
                f"{CRADLE_TOP:.2f}")
    if core is not None:
        total_h = CORE_LIFT + core["max"][1]
        if abs(total_h - NODE_H) > 1e-3:
            problems.append(
                f"hauteur totale du nœud {total_h:.4f} m au lieu de "
                f"{NODE_H:.2f} m (cote du brief : 0,7 a 1,0 x 1,76 m)")
        # ⚠️ LA REGLE DE SILHOUETTE, MESUREE : il doit etre plus HAUT que LARGE.
        # C'est ce qui le separe de la tourelle (trapue) et du hangar (plat), et
        # c'est le seul test qui vaille en noir et blanc.
        if core["size"][1] <= max(core["size"][0], core["size"][2]):
            problems.append(
                "spine_core : il est plus large que haut — la troisieme "
                "silhouette du niveau doit etre la VERTICALE, sans quoi elle "
                "retombe sur la tourelle")
        if core["size"][0] > 2 * CRADLE_HX:
            problems.append(
                f"spine_core ({core['size'][0]:.2f} m) deborde de son berceau "
                f"({2 * CRADLE_HX:.2f} m) : le brief demande un berceau PLUS "
                "LARGE que le cœur")
    # La lanterne : la meme regle dure que l'œil de la tourelle, 25 pct.
    lantern_ratio = (LANTERN_Y1 - LANTERN_Y0) / NODE_H
    if lantern_ratio > 0.25:
        problems.append(
            f"la lanterne fait {100 * lantern_ratio:.1f} pct du nœud — la regle "
            "dure des kits de ce niveau est 25 pct")
    # L'entretoise PENCHE-T-ELLE ? Mesure sur le binaire, pas sur la constante.
    if brace is not None:
        measured_lean = -brace["min"][0]
        if abs(measured_lean - (BRACE_LEAN + BRACE_COLLAR_HX)) > 1e-3:
            problems.append(
                f"spine_brace : deport mesure {measured_lean:.4f} m au lieu de "
                f"{BRACE_LEAN + BRACE_COLLAR_HX:.4f} — l'inclinaison est le "
                "second signal de silhouette, elle ne peut pas deriver")
        if BRACE_FOOT_R + BRACE_HX + BRACE_PAD > CRADLE_HX + 1e-9:
            problems.append(
                f"le pied de l'entretoise atteint "
                f"{BRACE_FOOT_R + BRACE_HX + BRACE_PAD:.3f} m alors que le berceau "
                f"n'ouvre qu'a {CRADLE_HX:.2f} m : elle porterait a faux")
        # Le collier ENSERRE-T-IL le fut ? Le fut, a la hauteur du collier, a
        # pour demi-largeur `hx(y)`. Le collier doit le RECOUVRIR.
        y = CRADLE_TOP + BRACE_H - BRACE_COLLAR_H * 0.5 - CORE_LIFT
        shaft = CORE_BASE_HX + (CORE_NECK_HX - CORE_BASE_HX) * \
            min(max((y - CORE_FOOT_Y) / (CORE_NECK_Y - CORE_FOOT_Y), 0.0), 1.0)
        inner = BRACE_FOOT_R - BRACE_LEAN - BRACE_COLLAR_HX
        if inner > shaft:
            problems.append(
                f"le collier de l'entretoise s'arrete a {inner:.3f} m de l'axe "
                f"alors que le fut n'y mesure que {shaft:.3f} m : elle ne tient "
                "rien")

    # --- L'EMPRISE PARTAGEE AVEC LA COQUE ---------------------------------
    if abs(FOOTPRINT_HX - cortege.SPINE_FOOTPRINT_HX) > 1e-9 or \
            abs(FOOTPRINT_HZ - cortege.SPINE_FOOTPRINT_HS) > 1e-9:
        problems.append(
            f"emprise du kit ({FOOTPRINT_HX}, {FOOTPRINT_HZ}) contre "
            f"({cortege.SPINE_FOOTPRINT_HX}, {cortege.SPINE_FOOTPRINT_HS}) "
            "echantillonnee par la coque : les deux valeurs ont derive, "
            "l'assise du marqueur est fausse")

    # --- LES CINQ EMPLACEMENTS, MESURES SUR LA COQUE LIVREE ---------------
    seats: list[tuple[str, float, float, float, float, float]] = []
    for number, s in enumerate(cortege.SPINES, start=1):
        seat, low = cortege.spine_seat_y(s)
        scale = cortege._scales(s)[0]
        rim = cortege._surface_y(s, cortege.CANAL_RIM_X * scale)
        crest = seat + NODE_H
        seats.append((f"Spine_{number:02d}", seat, low, rim, crest,
                      crest - rim))
        if seat - low > CRADLE_BURIED - 0.08:
            problems.append(
                f"Spine_{number:02d} : denivele {seat - low:.3f} m sous "
                f"l'emprise, la jupe de {CRADLE_BURIED:.2f} m ne mord plus le "
                "fond du canal du cote bas")
        if crest > cortege.CEILING_Y:
            problems.append(
                f"Spine_{number:02d} : le nœud culmine a {crest:.3f}, au-dessus "
                f"du plafond du DECOR ({cortege.CEILING_Y}) — il siege dans une "
                "tranchee, il n'a aucune raison d'y arriver")
        if FOOTPRINT_HX > cortege.CANAL_FLOOR_HALF * scale - 0.04:
            problems.append(
                f"Spine_{number:02d} : le berceau ({2 * FOOTPRINT_HX:.2f} m) ne "
                f"tient pas dans le fond plat du canal "
                f"({2 * cortege.CANAL_FLOOR_HALF * scale:.2f} m)")

    # --- UV, materiaux, textures -----------------------------------------
    if prims_total == 0 or prims_uv != prims_total:
        problems.append(
            f"{prims_total - prims_uv} primitive(s) sur {prims_total} sans "
            "TEXCOORD_0 — la surface ne pourrait recevoir aucune carte (ADR-0028)")
    if prims_tan != prims_total:
        problems.append(
            f"{prims_total - prims_tan} primitive(s) sur {prims_total} sans TANGENT")
    forbidden = [ak.srgb_hex_to_linear(h)[:3] for h in FORBIDDEN_HEX]
    for material in gltf.get("materials", []):
        pbr = material.get("pbrMetallicRoughness", {})
        colors = [tuple(pbr.get("baseColorFactor", [0, 0, 0, 1])[:3]),
                  tuple(material.get("emissiveFactor", [0, 0, 0]))]
        for color in colors:
            for banned, hexa in zip(forbidden, FORBIDDEN_HEX):
                if max(abs(c - b) for c, b in zip(color, banned)) < 0.02:
                    problems.append(
                        f"materiau {material.get('name')} : couleur {hexa} — elle "
                        "appartient aux tirs (charte SS3)")
        if "baseColorTexture" in pbr or "metallicRoughnessTexture" in pbr or \
                "normalTexture" in material or "occlusionTexture" in material or \
                "emissiveTexture" in material:
            problems.append(
                f"materiau {material.get('name')} : TEXTURE dans le .glb — la "
                "matiere vient de l'operateur (ADR-0028)")
    if gltf.get("images"):
        problems.append("le .glb embarque des images : interdit par ADR-0028")

    # --- densite de texels -----------------------------------------------
    floor_density = TEXELS_PER_METER / math.sqrt(3.0) * 0.98
    for name, measure in density.items():
        if not measure:
            continue
        if measure["tiles_per_m_min"] < floor_density:
            problems.append(
                f"{name} : densite minimale {measure['tiles_per_m_min']:.4f} "
                f"sous la borne {floor_density:.4f} de la projection en boite")
        if measure["tiles_per_m_max"] > TEXELS_PER_METER * 1.02:
            problems.append(
                f"{name} : densite maximale {measure['tiles_per_m_max']:.4f} "
                f"au-dessus de la cible {TEXELS_PER_METER:.4f}")

    # --- budget -----------------------------------------------------------
    assembled = sum(stats.get(name, {}).get("triangles", 0)
                    * ASSEMBLY_COPIES[name] for name in PART_NAMES)
    if assembled > TRI_BUDGET_ASSEMBLED:
        problems.append(
            f"{assembled} triangles par nœud assemble > budget "
            f"{TRI_BUDGET_ASSEMBLED}")
    level = assembled * len(cortege.SPINES)
    if level > TRI_BUDGET_LEVEL:
        problems.append(f"{level} triangles pour le niveau > budget "
                        f"{TRI_BUDGET_LEVEL}")

    if problems:
        raise ak.ContractError(
            "CONTRAT ROMPU — spine_kit\n" + "\n".join(f"  - {p}" for p in problems))

    return {
        "parts": stats,
        "primitives": (prims_uv, prims_tan, prims_total),
        "triangles": triangles_total,
        "assembled": assembled,
        "level": level,
        "materials": sorted(used_materials),
        "area_by_material": area_by_material,
        "built_by_material": built_area,
        "seen_by_material": seen_area,
        "total_area": total_area,
        "total_built": total_built,
        "total_seen": total_seen,
        "emissive_by_part": emissive_by_part,
        "density": density,
        "seats": seats,
        "bytes": os.path.getsize(path),
    }


# ==========================================================================
# Build
# ==========================================================================


def build() -> dict:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)
    parts = build_parts()
    return export(parts, OUTPUT)


def _print_report(report: dict) -> None:
    print("\n--- spine_kit : mesures relevees sur le .glb PRODUIT ---")
    print(f"  {'piece':<16} {'tri':>5} {'x':>2}  {'bbox (l x h x L)':>24}")
    for name in PART_NAMES:
        s = report["parts"][name]
        print(f"  {name:<16} {s['triangles']:>5} {ASSEMBLY_COPIES[name]:>2}  "
              f"{s['size'][0]:7.2f} x {s['size'][1]:5.2f} x {s['size'][2]:7.2f}")
    print(f"  {'TOTAL (kit unique)':<16} {report['triangles']:>5}")
    print(f"  nœud assemble : {report['assembled']} tri / "
          f"{TRI_BUDGET_ASSEMBLED} ; cinq nœuds : {report['level']} / "
          f"{TRI_BUDGET_LEVEL}")

    print("\n  TABLE DES EMPRISES — c'est elle qui dit au moteur ou poser chaque")
    print("  piece. Repere local du marqueur `Spine_NN` (X lateral, Y haut, "
          "Z survol, +Z = proue).")
    entete = "position d'assemblage"
    print(f"    {'piece':<16} {'parent':<10} {entete:<30} {'copies'}")
    plan = (
        ("spine_cradle", "marqueur", "(0, 0, 0)", "1"),
        ("spine_core", "marqueur", f"(0, {CORE_LIFT:+.2f}, 0)",
         "1 — la SEULE detruite"),
        ("spine_brace", "marqueur",
         f"(+/-{BRACE_FOOT_R:.2f}, {CRADLE_TOP:+.2f}, +/-dz) yaw 0 ou pi",
         "2 ou 4"),
    )
    for name, parent, where, copies in plan:
        print(f"    {name:<16} {parent:<10} {where:<30} {copies}")
    print(f"    dz = 0 pour deux entretoises, "
          f"{FAMILIES[1][2]:.2f} pour quatre. Le yaw vaut pi du cote babord : la "
          "piece\n    penche toujours vers son -X local, donc toujours vers "
          "l'axe du nœud.")
    print("    ⚠️ Le moteur DETRUIT `spine_core` SEUL. Berceau et entretoises "
          "restent : un nœud\n    abattu laisse une carcasse, et c'est pour "
          "cela qu'aucune des deux ne porte d'emissif.")

    print("\n  LES DEUX FAMILLES — variete par ASSEMBLAGE SEUL, sans reforge")
    for name, count, dz in FAMILIES:
        print(f"    {name:<24} {count} entretoises, dz = {dz:.2f} m")

    print(f"\n  cotes relevees sur le binaire : hauteur totale "
          f"{CORE_LIFT + report['parts']['spine_core']['max'][1]:.2f} m "
          f"(cible {NODE_H:.2f}) ; berceau "
          f"{report['parts']['spine_cradle']['size'][0]:.2f} x "
          f"{report['parts']['spine_cradle']['size'][2]:.2f} m ; fut "
          f"{report['parts']['spine_core']['size'][0]:.2f} m de large pour "
          f"{report['parts']['spine_core']['size'][1]:.2f} m de haut "
          f"(rapport {report['parts']['spine_core']['size'][1] / report['parts']['spine_core']['size'][0]:.2f} : 1)")
    print(f"  lanterne : {LANTERN_Y1 - LANTERN_Y0:.2f} m sur un nœud de "
          f"{NODE_H:.2f} m, soit "
          f"{100 * (LANTERN_Y1 - LANTERN_Y0) / NODE_H:.1f} pct (regle dure : 25) "
          f"— sa COURONNE horizontale fait "
          f"{LANTERN_HX - SHOULDER_HX:.2f} m de large et elle est coiffee par un "
          f"capot de {HOOD_Y1 - SHOULDER_Y:.2f} m")
    print(f"  entretoise : {BRACE_LEAN:.2f} m de deport pour {BRACE_H:.2f} m de "
          f"montee, soit {math.degrees(math.atan2(BRACE_LEAN, BRACE_H)):.1f} deg "
          "— la seule oblique du niveau")
    print("  emissif par piece (m2, kit brut) : "
          + ", ".join(f"{n} {report['emissive_by_part'].get(n, 0.0):.3f}"
                      for n in PART_NAMES))

    print("\n  LES CINQ EMPLACEMENTS, mesures sur la coque livree")
    print(f"    {'marqueur':<12} {'assise':>8} {'bas':>8} {'denivele':>9} "
          f"{'rebord':>8} {'sommet':>8} {'hors tranchee':>14} {'plafond':>9}")
    for name, seat, low, rim, crest, above in report["seats"]:
        print(f"    {name:<12} {seat:>8.3f} {low:>8.3f} {seat - low:>9.3f} "
              f"{rim:>8.3f} {crest:>8.3f} {above:>14.3f} "
              f"{cortege.CEILING_Y - crest:>9.3f}")
    print(f"    la tranchee cache {min(r[3] - r[1] for r in report['seats']):.2f} "
          f"a {max(r[3] - r[1] for r in report['seats']):.2f} m du nœud ; il en "
          f"depasse {min(r[5] for r in report['seats']):.2f} a "
          f"{max(r[5] for r in report['seats']):.2f} m")
    print(f"    plafond du DECOR {cortege.CEILING_Y:+.2f} : marge "
          f"{cortege.CEILING_Y - max(r[4] for r in report['seats']):.3f} m — "
          "aucun depassement, le nœud n'a pas besoin du plafond de GAMEPLAY "
          "(-2,40)")

    print(f"\n  primitives : {report['primitives'][0]}/{report['primitives'][2]} "
          f"TEXCOORD_0, {report['primitives'][1]}/{report['primitives'][2]} TANGENT")
    print("  densite de texels (valeurs singulieres, triangle par triangle), "
          f"cible {TEXELS_PER_METER:.3f} tuile/m ({1 / TEXELS_PER_METER:.2f} m/tuile)")
    for name in PART_NAMES:
        d = report["density"].get(name)
        if not d:
            continue
        print(f"    {name:<16} {d['tiles_per_m_min']:.3f} a "
              f"{d['tiles_per_m_max']:.3f}, moyenne {d['tiles_per_m_mean']:.3f} "
              f"t/m ({d['m_per_tile_mean']:.2f} m/tuile), aniso "
              f"{d['anisotropy_max']:.2f}")

    print("\n  repartition en AIRE, relevee sur le .glb — kit brut, nœud "
          "ASSEMBLE, et ce qui en est VU")
    total = report["total_area"] or 1.0
    built_total = report["total_built"] or 1.0
    seen_total = report["total_seen"] or 1.0
    print(f"    {'materiau':<22} {'kit':>8} {'':>7}  {'assemble':>8} {'':>7}  "
          f"{'vu':>8} {'':>7}")
    for name, area in sorted(report["built_by_material"].items(),
                             key=lambda kv: -kv[1]):
        raw = report["area_by_material"].get(name, 0.0)
        seen = report["seen_by_material"].get(name, 0.0)
        print(f"    {name:<22} {raw:7.2f} m2 {100.0 * raw / total:5.1f} %  "
              f"{area:7.2f} m2 {100.0 * area / built_total:5.1f} %  "
              f"{seen:7.2f} m2 {100.0 * seen / seen_total:5.1f} %")
    print(f"    {'TOTAL':<22} {total:7.2f} m2          {built_total:7.2f} m2"
          f"          {seen_total:7.2f} m2")
    print(f"  octets     : {report['bytes']}")


def main() -> None:
    report = build()
    _print_report(report)
    if "--plate" in sys.argv:
        render_plate(report)


# ==========================================================================
# Planche de recette — `--plate`
# ==========================================================================
# ADR-0006 : un livrable de la forge n'est pas valide tant qu'il n'a pas ete rendu
# et REGARDE. La premiere vignette EST le test d'acceptation du brief, et il porte
# maintenant sur TROIS silhouettes et non deux : « en noir et blanc, emissifs
# coupes, les trois structures se distinguent ». Une vignette par piece ne
# prouverait rien — c'est la COMPARAISON, dans un seul cadre, qui est le test.

TILE_W = 1440
SCENE_H = 620
CLOSE_H = 660
ARTERY_H = 560
RHYTHM_H = 380
UV_H = 420

BACKDROP = baykit.BACKDROP
AMBIENT = baykit.AMBIENT
CAM_POS = cortege.CAM_POS
CAM_FORWARD = cortege.CAM_FORWARD
CAM_UP = cortege.CAM_UP
CAM_FOV_V = cortege.CAM_FOV_V

#: LE CADRE D'ACCEPTATION, ET IL EST CHOISI PAR LA MESURE, PAS A L'ŒIL.
#: La camera du jeu est fixe (0, 14, 5) et plonge a 70 deg : a la profondeur du
#: pont, elle ne voit qu'une FENETRE de 16 m en `s` — de l'aim + 3 m (le bas du
#: cadre, ou vole le chasseur) a l'aim - 13 m. Il faut donc les trois familles
#: dans ces 16 m. `Bay_06` (s = 348), `Spine_04` (s = 350) et `Turret_11`
#: (s = 360) y tiennent, en visant s = 353 : le hangar en bas a babord, le nœud
#: au centre sur l'axe, la tourelle en haut a tribord. C'est le seul endroit des
#: 500 m ou les trois se cotoient sans qu'Ambry entre dans le cadre et vole la
#: lecture. Premier essai fait a s = 348 : `Turret_10` (s = 336) tombait DERRIERE
#: la camera, et le test d'acceptation ne montrait que deux structures sur trois.
ACCEPTANCE_SPINE = 4
ACCEPTANCE_BAY = 6
ACCEPTANCE_TURRETS = (11,)
ACCEPTANCE_AIM = 353.0


def _to_blender(v: Vector) -> Vector:
    return Vector((v.x, -v.z, v.y))


def _place(name: str, position: Vector, yaw: float = 0.0) -> list:
    """Importe UNE piece du kit et la pose. Comme le fera le moteur."""
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=OUTPUT)
    fresh = [o for o in bpy.context.scene.objects if o not in before]
    keep = [o for o in fresh if o.name.split(".")[0] == name]
    for obj in fresh:
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in keep:
        obj.location = _to_blender(position)
        obj.rotation_euler = Euler((0.0, 0.0, yaw), "XYZ")
        obj.visible_shadow = False
    return keep


def _assemble_node(centre: Vector, family: int, core: bool = True) -> list:
    """Monte UN nœud a `centre` (Y = assise), selon la famille demandee.

    C'est la SEULE façon de juger le lot : le kit livre trois pieces, et aucune
    ne prouve quoi que ce soit seule. `core=False` rend la CARCASSE — ce que le
    joueur voit apres avoir abattu le nœud, et la seule image qui montre que le
    partage en trois pieces sert a quelque chose.
    """
    _name, braces, dz = FAMILIES[family]
    del _name
    placed = _place("spine_cradle", centre)
    if core:
        placed += _place("spine_core", centre + Vector((0.0, CORE_LIFT, 0.0)))
    zs = (0.0,) if braces == 2 else (dz, -dz)
    for z in zs:
        for side, yaw in ((1.0, 0.0), (-1.0, math.pi)):
            placed += _place(
                "spine_brace",
                centre + Vector((side * BRACE_FOOT_R, CRADLE_TOP, z)), yaw)
    return placed


def _assemble_turret(number: int, shift: float, aim: float) -> list:
    s, x = cortege.TURRETS[number - 1]
    seat, _ = cortege.turret_seat_y(s, x)
    return turretkit._assemble_turret(Vector((x, seat, -s + shift)), 2, aim=aim)


def _decor_and_kits(shift: float, core: bool = True) -> tuple[list, list]:
    """Le borde et les trois familles montees dessus, a leur place de jeu."""
    decor = baykit._import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    kits: list = []
    kits += baykit._assemble_bay(ACCEPTANCE_BAY, shift)
    for number in ACCEPTANCE_TURRETS:
        kits += _assemble_turret(number, shift,
                                 math.radians(-28.0 if number % 2 else 34.0))
    s = cortege.SPINES[ACCEPTANCE_SPINE - 1]
    seat, _ = cortege.spine_seat_y(s)
    kits += _assemble_node(Vector((0.0, seat, -s + shift)), 1, core=core)
    return decor, kits


def _tile_acceptance(path: str, report: dict, greyscale: bool) -> None:
    """LE TEST D'ACCEPTATION : les TROIS structures dans le MEME cadre."""
    baykit._plate_reset()
    shift = baykit._game_shift(ACCEPTANCE_AIM)
    decor, kits = _decor_and_kits(shift)
    # ⚠️ LE CHASSEUR EST DECALE DE 3,60 m A TRIBORD, ET C'EST UNE MESURE, PAS UN
    # CADRAGE FLATTEUR. Le nœud siege SUR L'AXE du vaisseau, exactement la ou le
    # Specter-9 vole quand il ne manœuvre pas : au premier tirage, le chasseur le
    # masquait entierement et le test d'acceptation ne montrait que deux
    # structures sur trois. Le joueur n'est pas cloue a l'axe — il traverse un
    # plan de 24 unites de large —, mais le fait qu'il masque sa cible quand il y
    # est EST une information de conception, et elle est au compte-rendu.
    fighter = baykit._import(FIGHTER, "Player", Vector((3.6, 0.0, 3.4)))
    if greyscale:
        baykit._to_greyscale(decor + kits + fighter)
    baykit._plate_lights()
    camera = baykit._plate_camera("game", _to_blender(CAM_POS),
                                  _to_blender(CAM_FORWARD),
                                  _to_blender(CAM_UP), CAM_FOV_V)
    if greyscale:
        baykit._label(
            camera, "TEST D'ACCEPTATION — NOIR ET BLANC, EMISSIFS COUPES : LES "
            "TROIS STRUCTURES DANS LE MEME CADRE",
            -0.97, 0.90, 0.038, TILE_W, SCENE_H, (1.0, 0.88, 0.55))
        baykit._label(
            camera, "hangar (Bay_06) : il CREUSE — un cadre vide.   "
            "tourelles (Turret_10/11) : elles DEPASSENT — un tambour trapu et "
            "deux tubes.",
            -0.97, 0.82, 0.028, TILE_W, SCENE_H)
        baykit._label(
            camera, "nœud (Spine_04) : il MONTE — un fut de 0,52 m de large sur "
            f"1,20 m de haut, tenu par quatre diagonales a "
            f"{math.degrees(math.atan2(BRACE_LEAN, BRACE_H)):.0f} deg, au fond "
            "de la tranchee.",
            -0.97, 0.75, 0.028, TILE_W, SCENE_H, (0.72, 0.84, 1.0))
    else:
        baykit._label(
            camera, "LE MEME CADRE, EN COULEUR — ce que l'emissif AJOUTE a une "
            "fonction deja lisible en geometrie",
            -0.97, 0.90, 0.038, TILE_W, SCENE_H, (1.0, 0.88, 0.55))
        baykit._label(
            camera, "l'artere n'est plus une bande : quatre conduits de 12 a "
            "18 cm au FOND d'un canal de 2,00 m enfonce de 0,56 m, coupes par "
            "des travees sombres",
            -0.97, 0.82, 0.028, TILE_W, SCENE_H)
        baykit._label(
            camera, "un seul emissif sur tout le nœud : la lanterne, "
            f"{LANTERN_Y1 - LANTERN_Y0:.2f} m pour {NODE_H:.2f} m de haut "
            f"({100 * (LANTERN_Y1 - LANTERN_Y0) / NODE_H:.0f} pct), coiffee d'un "
            "capot sombre",
            -0.97, 0.75, 0.028, TILE_W, SCENE_H, (0.72, 0.84, 1.0))
    baykit._label(
        camera, "camera de graybox.tscn sans retouche (0, 14, 5), FOV 62, "
        "70 deg sous l'horizontale ; Specter-9 reel a sa place de jeu",
        -0.97, -0.92, 0.028, TILE_W, SCENE_H, (0.72, 0.84, 1.0))
    baykit._render(path, TILE_W, SCENE_H)


def _tile_close(path: str, report: dict) -> None:
    """LE NŒUD DE TROIS QUARTS, ET SA CARCASSE — le partage en trois pieces."""
    baykit._plate_reset()
    s = cortege.SPINES[ACCEPTANCE_SPINE - 1]
    shift = baykit._game_shift(s)
    baykit._import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    seat, _ = cortege.spine_seat_y(s)
    centre = Vector((0.0, seat, -s + shift))
    # ⚠️ LES DEUX NŒUDS SONT DECALES EN Z, PAS EN X. Le canal ne fait que 2,00 m
    # de large : un second nœud pose a 2,60 m sur le cote se serait retrouve sur
    # la tole du pont, hors de sa tranchee, et la comparaison aurait ete fausse.
    _assemble_node(centre + Vector((0.0, 0.0, 2.1)), 1, core=True)
    _assemble_node(centre + Vector((0.0, 0.0, -2.1)), 0, core=False)
    baykit._plate_lights()
    # ⚠️ Recul et champ CALCULES, pas choisis : deux nœuds a 4,20 m l'un de
    # l'autre demandent un cadre plus large que la distance ne le donnait au
    # premier essai — le nœud le plus proche sortait par le bord gauche.
    eye = centre + Vector((4.8, 3.5, 0.8))
    target = centre + Vector((0.0, 0.55, 0.0))
    forward, up = turretkit._look_at(eye, target)
    camera = baykit._plate_camera("close", _to_blender(eye),
                                  _to_blender(forward), _to_blender(up),
                                  math.radians(42.0))
    baykit._label(camera, "TROIS QUARTS DANS LA TRANCHEE — au fond le nœud entier "
                          "(famille B), devant la CARCASSE",
                  -0.97, 0.90, 0.038, TILE_W, CLOSE_H, (1.0, 0.88, 0.55))
    baykit._label(
        camera, "le moteur detruit `spine_core` SEUL : le berceau et les "
        "entretoises restent, et rien n'y est emissif —\nc'est ce qui fait qu'un "
        "nœud abattu se VOIT abattu, et c'est pour cela que la piece est un kit "
        "et pas une coque.",
        -0.97, 0.80, 0.027, TILE_W, CLOSE_H)
    baykit._label(
        camera, f"berceau {2 * CRADLE_HX:.2f} x {2 * CRADLE_HZ:.2f} m, enterre "
        f"de {CRADLE_BURIED:.2f} ; fut {2 * CORE_BASE_HX:.2f} -> "
        f"{2 * CORE_NECK_HX:.2f} m ; lanterne {2 * LANTERN_HX:.2f} m, couronne "
        f"{LANTERN_HX - SHOULDER_HX:.2f} m ; "
        f"{report['assembled']} tri assembles pour {TRI_BUDGET_ASSEMBLED}",
        -0.97, -0.90, 0.027, TILE_W, CLOSE_H, (0.72, 0.84, 1.0))
    baykit._render(path, TILE_W, CLOSE_H)


def _tile_artery(path: str, report: dict) -> None:
    """L'ARTERE DE PRES — la vue que le brief demande explicitement."""
    baykit._plate_reset()
    s = cortege.SPINES[ACCEPTANCE_SPINE - 1]
    shift = baykit._game_shift(s)
    baykit._import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    seat, _ = cortege.spine_seat_y(s)
    centre = Vector((0.0, seat, -s + shift))
    _assemble_node(centre, 1)
    baykit._plate_lights()
    # Une vue basse et rasante : c'est la seule qui montre qu'un canal est un
    # CREUX. Vu du dessus, un creux et une bande peinte rendent la meme image.
    # ⚠️ TROIS ESSAIS POUR CE CADRAGE, ET CHACUN A APPRIS QUELQUE CHOSE. A 13 m
    # et 1,5 m de haut (11 deg), le rebord masquait son propre fond et l'on ne
    # voyait plus que la ligne de lumiere — exactement l'image qu'on corrige. A
    # 4 m du nœud, le berceau (1,32 m dans un canal de 2,00) remplissait la
    # tranchee et il n'en restait rien a voir. A 2 m de haut et 1,9 m de l'axe,
    # on etait DANS la tranchee : plus de rebord dans le cadre, donc plus de
    # creux, juste un sol plat et deux rubans. Ce qui fait lire un creux, c'est
    # sa PAROI : il faut donc reculer et monter (26 deg, 10 m) et refermer le
    # champ (22 deg) pour que les 0,56 m de paroi occupent une soixantaine de
    # pixels. La cote se lit alors, et le nœud siege dedans.
    eye = centre + Vector((5.0, 4.2, 8.0))
    target = centre + Vector((0.0, -0.35, 0.5))
    forward, up = turretkit._look_at(eye, target)
    camera = baykit._plate_camera("artery", _to_blender(eye),
                                  _to_blender(forward), _to_blender(up),
                                  math.radians(22.0))
    baykit._label(camera, "L'ARTERE DE PRES — une TRANCHEE, plus une bande",
                  -0.97, 0.90, 0.040, TILE_W, ARTERY_H, (1.0, 0.88, 0.55))
    baykit._label(
        camera, f"canal de {2 * cortege.CANAL_HALF:.2f} m enfonce de "
        f"{cortege.CANAL_RIM_Y - cortege.CANAL_FLOOR_Y:.2f} m sous son rebord ; "
        f"4 conduits de {100 * (cortege.CONDUIT_LANES[1][1] - cortege.CONDUIT_LANES[1][0]):.0f} "
        f"et {100 * (cortege.CONDUIT_LANES[0][1] - cortege.CONDUIT_LANES[0][0]):.0f} cm, "
        f"soit {100 * sum(b - a for a, b in cortege.CONDUIT_LANES) / cortege.CANAL_HALF:.0f} "
        "pct de sa largeur",
        -0.97, 0.81, 0.028, TILE_W, ARTERY_H)
    baykit._label(
        camera, "les travees sombres BARRENT le canal — la coupure est de la "
        "matiere, pas seulement un trou dans la lumiere",
        -0.97, -0.88, 0.028, TILE_W, ARTERY_H, (0.72, 0.84, 1.0))
    baykit._render(path, TILE_W, ARTERY_H)


def _tile_rhythm(path: str, report: dict) -> None:
    """LA VUE LONGUE — calme / installation / calme, sur 120 m."""
    baykit._plate_reset()
    decor = baykit._import(HULL, "Decor", Vector((0.0, 0.0, 0.0)))
    del decor
    for number in range(1, len(cortege.TURRETS) + 1):
        s, x = cortege.TURRETS[number - 1]
        if not 246.0 <= s <= 372.0:
            continue
        _assemble_turret(number, 0.0, math.radians(-24.0 + 12.0 * number))
    for number in range(1, len(cortege.BAYS) + 1):
        s, _x = cortege.BAYS[number - 1]
        if 246.0 <= s <= 372.0:
            baykit._assemble_bay(number, 0.0)
    for number, s in enumerate(cortege.SPINES, start=1):
        if not 246.0 <= s <= 372.0:
            continue
        seat, _ = cortege.spine_seat_y(s)
        _assemble_node(Vector((0.0, seat, -s)), 1)
    baykit._plate_lights()
    centre = -309.0
    camera = baykit._plate_camera(
        "rhythm", _to_blender(Vector((0.0, 60.0, centre))),
        _to_blender(Vector((0.0, -1.0, 0.0))),
        _to_blender(Vector((-1.0, 0.0, 0.0))),
        math.radians(30.0), ortho=32.0)
    calm = sum(c["calme_total"] for c in report["hull"]["counts"])
    baykit._label(
        camera, "LE RYTHME, SUR 128 m (s = 245 a 373) — proue a gauche : "
        "calme, installation, calme",
        -0.985, 0.86, 0.055, TILE_W, RHYTHM_H, (1.0, 0.88, 0.55))
    baykit._label(
        camera, f"{calm:.0f} m de tole nue sur 500, soit "
        f"{100 * calm / cortege.SHIP_LENGTH:.0f} pct de la longueur ; plus "
        f"longue plage {max(c['calme_max'] for c in report['hull']['counts']):.0f} m. "
        "Hors des emprises d'installation, le borde ne porte que ses lisses.",
        -0.985, -0.86, 0.042, TILE_W, RHYTHM_H)
    baykit._render(path, TILE_W, RHYTHM_H)


def _tile_uv(path: str, report: dict) -> None:
    baykit._plate_reset()
    shift = baykit._game_shift(ACCEPTANCE_AIM)
    decor, kits = _decor_and_kits(shift)
    baykit._apply_checker(decor + kits)
    baykit._plate_lights()
    camera = baykit._plate_camera("uv", _to_blender(CAM_POS),
                                  _to_blender(CAM_FORWARD),
                                  _to_blender(CAM_UP), CAM_FOV_V)
    d = report["density"]["spine_core"]
    baykit._label(
        camera, "DAMIER UV — grande case = 1 tuile de 5,00 m, petite = 62,5 cm ; "
        "la MEME echelle sur la coque et sur les trois kits",
        -0.97, 0.90, 0.036, TILE_W, UV_H, (1.0, 0.88, 0.55))
    baykit._label(
        camera, f"projection en boite {TEXELS_PER_METER:.3f} tuile/m ; "
        f"anisotropie max mesuree sur le cœur {d['anisotropy_max']:.2f} "
        "(borne theorique de la methode : 1,73)",
        -0.97, 0.81, 0.028, TILE_W, UV_H)
    baykit._render(path, TILE_W, UV_H)


def render_plate(report: dict) -> None:
    # ⚠️ La planche a besoin des MESURES DE LA COQUE (part calme, plus longue
    # plage) : elle les relit du build de la coque, elle ne les reinvente pas.
    report["hull"] = cortege.build()
    ak.reset_scene()
    staging = tempfile.mkdtemp(prefix="aegis-spinekit-plate-")
    tiles: list[tuple[str, int]] = []
    try:
        path = os.path.join(staging, "bw.png")
        _tile_acceptance(path, report, greyscale=True)
        tiles.append((path, SCENE_H))
        path = os.path.join(staging, "color.png")
        _tile_acceptance(path, report, greyscale=False)
        tiles.append((path, SCENE_H))
        path = os.path.join(staging, "close.png")
        _tile_close(path, report)
        tiles.append((path, CLOSE_H))
        path = os.path.join(staging, "artery.png")
        _tile_artery(path, report)
        tiles.append((path, ARTERY_H))
        path = os.path.join(staging, "rhythm.png")
        _tile_rhythm(path, report)
        tiles.append((path, RHYTHM_H))
        path = os.path.join(staging, "uv.png")
        _tile_uv(path, report)
        tiles.append((path, UV_H))
        os.makedirs(os.path.dirname(PLATE), exist_ok=True)
        turretkit._compose(tiles, PLATE)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


if __name__ == "__main__":
    main()
