"""build_bay_kit.py — le kit de pont d'envol du Long Cortege (BRIEF-0091).

    blender45 -b -P tools/blender/build_bay_kit.py
    blender45 -b -P tools/blender/build_bay_kit.py -- --plate
    blender45 -b -P tools/blender/build_bay_kit.py -- --doors-plate
    ./scripts/build-hull.sh --check bay_kit          # + controle de determinisme

Produit `assets/imported/models/backgrounds/bay_kit.glb`, avec `--plate` la
planche de recette `docs/forge/output/BRIEF-0091-planche-hangars.png`, et avec
`--doors-plate` celle des battants `docs/forge/output/BRIEF-0095-planche-portes.png`.

Le script EST la source (ADR-0008) : aucun `.blend` versionne, aucun alea, deux
executions successives rendent le meme sha256.


CE QUE CE FICHIER EST, ET CE QU'IL N'EST PAS
============================================
Ce n'est PAS un hangar. C'est un KIT de sept pieces, chacune modelisee dans SON
repere, origine au point d'assemblage. Le moteur les instancie et les compose :
c'est lui qui fait sept hangars differents a partir d'un seul kit, par rotation,
par largeur et par presence des blocs. La coque, elle, ne porte plus que
l'OUVERTURE (`build_long_cortege.py`, BRIEF-0091) — plus aucune geometrie de
baie n'y est cuite.

    bay_frame_left     montant gauche du coaming   origine : bord gauche, Y = peau
    bay_frame_right    montant droit — MIROIR      origine : bord droit
    bay_frame_top      traverse avant (proue)      origine : milieu du bord avant
    bay_inner_wall     paroi du puits, anneau      origine : centre, Y = peau
    bay_floor          le fond                     origine : centre, -1,80 m
    bay_launch_rail    UN rail ; le moteur en pose deux
    bay_service_block  bloc de servitude, optionnel
    bay_door_left      battant bâbord (BRIEF-0095)  origine : arete de jonction
    bay_door_right     battant tribord — DEMI-TOUR  origine : arete de jonction


LA REGLE QUI PRIME SUR TOUT LE RESTE
====================================
« La structure doit etre identifiable par sa seule SILHOUETTE, avec au plus 6-8
primitives principales. Les emissifs ne servent qu'a renforcer une fonction deja
lisible en geometrie. »

Le hangar assemble en compte SIX :

    1. l'anneau de coaming (4 nœuds, mais UNE lecture : un cadre epais)
    2. la gorge — soffite biseaute puis paroi en depouille
    3. le fond
    4. et 5. les deux rails
    6. le bloc de servitude (facultatif)

⛔ Rien n'a ete ajoute « pour la qualite 3D ». A 23 px/m de detail utile apres le
post-traitement retro, tout detail sous ~9 cm disparait : du detail ajoute est du
budget depense pour du bruit. Les seules subdivisions de ce fichier servent soit
a une bande emissive, soit a un chanfrein qui porte une arete vive.


LES QUATRE REGLES VISUELLES DE LA PLANCHE, ET OU ELLES SONT DANS LE CODE
=======================================================================
1. TOUJOURS UN TROU, JAMAIS UN BOUTON. La coque est percee (pas de booleen : on
   n'emet pas les faces de l'emprise) et le kit ne rebouche rien : il borde.
2. L'INTERIEUR EST PLUS SOMBRE QUE L'EXTERIEUR. Ce n'est pas un vœu, c'est une
   affectation : tout ce qui regarde le puits est `AA_Greeble` (#141419), tout ce
   qui regarde le ciel est `AA_Hull` (#24252B). Rapport de luminance mesure au
   compte-rendu.
3. BANDES LUMINEUSES SEULEMENT EN PARTIE. Trois bandes, et rien d'autre : un
   liseré sous la levre du coaming, un pied de paroi, deux filets le long des
   rails. JAMAIS le fond entier — c'est exactement la faute de BRIEF-0089
   (hexagone emissif plein, sept fois dans le niveau).
4. L'APPAREIL EST VISIBLE AVANT LE DECOLLAGE. Le puits laisse 4,60 x 7,10 m
   libres a la bouche : un chasseur de 1,8 x 2,5 m y tient pose sur les rails, vu
   du dessus. La planche le montre avec le Specter-9 REEL.


LE PIEGE DE LA CAVITE OUVERTE — ET LE HARNAIS QUI LE TIENT
==========================================================
La coque est CREUSE. Une fois la peau trouee, on voit a travers : l'interieur du
vaisseau, puis sa face opposee. Un puits qui laisse voir le vide se lit comme un
trou dans le modele — c'est pire que le bouton qu'on remplace.

`bay_inner_wall` et `bay_floor` doivent donc FERMER le puits. Ce n'est pas laisse
a l'appreciation : `_audit()` verifie sur le BINAIRE que la levre exterieure de
l'anneau contient les QUATRE COINS de l'ouverture de la coque, et que le fond
deborde du pied de l'anneau. Les deux echouent le build.


L'ECHELLE DE DEPLIAGE — POURQUOI 0,200 ET PAS PLUS FIN
======================================================
Le kit partage les slots du borde (`AA_Hull`, `AA_Greeble`, ...). Deux echelles
de depliage sur un MEME slot, c'est la faute qu'a corrigee BRIEF-0090 sur Ambry :
la carte sortirait au bon grain sur la coque et au mauvais sur le hangar, cote a
cote, a 20 cm l'un de l'autre. Le kit est donc deplie a la densite du borde —
0,200 tuile/m, 5,00 m par tuile. Si le concepteur veut du grain sur l'interieur du
puits, la reponse n'est pas de changer ce chiffre mais de declarer un slot propre,
comme `AA_Hull_Ambry` : une ligne, et le harnais suivra.
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
# Les deux livrables sont indissociables (c'est pourquoi le brief les met dans un
# seul lot) : une ouverture de 6,00 m et un coaming modelise pour 6,05 ne se
# verraient sur aucun harnais separe. En important, une seule constante fait foi.
sys.path.insert(0, _HERE)
import build_long_cortege as cortege  # noqa: E402

OUTPUT = os.path.join(_REPO, "assets/imported/models/backgrounds/bay_kit.glb")
PLATE = os.path.join(_REPO, "docs/forge/output/BRIEF-0091-planche-hangars.png")
HULL = cortege.OUTPUT
FIGHTER = cortege.FIGHTER

# ==========================================================================
# Cotes maitresses — repere KIT (X lateral, Y haut, Z survol, +Z = PROUE)
# ==========================================================================
# Y = 0 est le plan de la BOUCHE, c'est-a-dire le Y que porte le marqueur
# `Bay_NN` de la coque. TOUTES les pieces sont modelisees dessus.

#: L'ouverture, reprise telle quelle de la coque (jamais recopiee a la main).
OPEN_HALF_X = cortege.BAY_HALF_X            # 3,00 -> 6,00 m de large
OPEN_HALF_Z = cortege.BAY_HALF_S            # 4,25 -> 8,50 m de long
#: Profondeur peau -> fond.
WELL_DEPTH = cortege.BAY_WELL_DEPTH         # 1,80 m

#: Largeur du coaming vers l'exterieur. ⚠️ 0,80 et non 1,10 : a 1,10 le montant
#: exterieur d'une baie a |x| = 9,30 tombait a x = 13,40, c'est-a-dire SUR la
#: facette exterieure qui plonge de -5,10 a -6,35 — la jupe n'y touchait plus la
#: coque et le coaming flottait. Mesure : a 0,80 le bord exterieur est a 13,10,
#: ou la peau est a -6,04, et la jupe de 1,80 m descend a -6,13. Elle mord.
#:
#: ⚠️ La COQUE tient ce chiffre elle aussi (`cortege.BAY_COAMING_W`) : c'est avec
#: lui qu'elle verifie qu'aucun socle de tourelle ne vient toucher un coaming. Les
#: deux ne peuvent plus deriver — cette egalite est controlee ici, a l'import, et
#: pas laissee a la memoire de qui modifiera l'un des deux.
COAM_W = 0.80
if abs(COAM_W - cortege.BAY_COAMING_W) > 1e-9:
    raise ak.ContractError(
        f"coaming : le kit dit {COAM_W} m, la coque {cortege.BAY_COAMING_W} m — "
        "les marges socle/pont d'envol seraient calculees sur une piece qui "
        "n'existe pas")
#: Hauteur au-dessus de la peau. La planche donne 0,4 a 0,8 ; le brief fixe 0,60.
COAM_H = 0.60
#: Profondeur de la jupe ENTERREE. Elle n'est pas decorative : l'ouverture de
#: 6,00 m enjambe la chine, et le pourtour accuse 0,78 m de denivele. Sans jupe,
#: le coaming ne poserait que d'un cote.
COAM_SKIRT = 1.80
#: Debord des montants aux extremites : ils possedent les quatre coins, et leur
#: face exterieure y rentre a 35 pct. C'est ce chanfrein qui donne au cadre sa
#: lecture OCTOGONALE du dessus, comme sur la planche de consignes.
COAM_END = 0.70
COAM_END_SCALE = 0.35

#: Retrait des parois internes par rapport a l'ouverture.
WALL_INSET = 0.70
#: Debord de la levre de l'anneau SOUS le coaming. C'est lui qui ferme le puits :
#: il doit contenir les quatre coins de l'ouverture, et le harnais le verifie.
LIP_OUT = 0.40

RAIL_W = 0.35
RAIL_H = 0.22
#: Longueur du rail. Le puits fait 7,10 m de long en clair ; le rail court du
#: fond vers la sortie en laissant 0,25 m a chaque bout.
RAIL_LEN = 6.60
#: Ecartement des deux rails, pose par le MOTEUR. Ici pour la planche et pour le
#: controle de garde : un chasseur de 1,8 m d'envergure doit tenir entre eux.
RAIL_GAUGE = 2.30

BLOCK_X, BLOCK_Z, BLOCK_H = 1.30, 0.90, 0.45

# --------------------------------------------------------------------------
# LES DEUX BATTANTS (BRIEF-0095) — cotes DONNEES par le moteur
# --------------------------------------------------------------------------
# ⚠️ AUCUNE DE CES QUATRE COTES N'EST UN CHOIX D'AUTEUR. Elles viennent de
# `scripts/gameplay/cortege_bay.gd`, qui fabriquait les battants lui-meme en
# `BoxMesh` de 3,00 x 0,14 x 8,50 et les retire de 3,00 m sur +-X. Les changer
# ici ne changerait pas le moteur : cela ferait seulement un battant qui ne
# ferme plus. Elles sont donc RELUES depuis l'ouverture, jamais recopiees.
#
#   emprise    x de 0 a -3,00 (bâbord), z de -4,25 a +4,25
#   epaisseur  <= 0,22
#   plafond    <= +0,18 au-dessus de la peau (il passe SOUS la levre du coaming)
#   course     3,00 m sur +-X

#: Le battant couvre exactement une demi-ouverture, et sa longueur EST celle du
#: puits : c'est ce qui fait qu'il n'y a aucun jour contre les montants.
DOOR_SPAN_X = OPEN_HALF_X                   # 3,00
DOOR_HALF_Z = OPEN_HALF_Z                   # 4,25
#: La course du moteur (`CortegeBay.DOOR_SLIDE`). Ici pour la planche et pour la
#: mesure de debord ouverte — le mouvement, lui, reste au moteur.
DOOR_SLIDE = 3.00

#: Plan superieur courant, et plan de la poutre de nez / des sabots. Le second
#: est le POINT LE PLUS HAUT de la piece : 0,175 < 0,18, sous la levre.
DOOR_TOP = 0.150
DOOR_RIM_TOP = 0.175
#: Fond des caissons (7,5 cm de creux) et fond de la rainure de sabot (5 cm).
DOOR_POCKET_Y = 0.075
DOOR_SHOE_GROOVE_Y = DOOR_RIM_TOP - 0.05

#: LA DENTURE. Six bandes alternees sur les 8,50 m : trois dents et trois creux
#: par battant, donc six alternances sur la ligne de fermeture.
#:
#: ⚠️ LA DENT AVANCE PLUS QUE LE CREUX NE RECULE (0,12 contre 0,10), ET C'EST LA
#: SEULE FACON D'AVOIR « AUCUN JOUR » SANS FACES COINCIDENTES. A egalite, les
#: deux battants se toucheraient sur des faces exactement coplanaires : un jour
#: nul en geometrie, mais un scintillement garanti au rendu. Avec 2 cm
#: d'interpenetration, il n'existe aucun (x, z) de l'ouverture que l'un des deux
#: ne couvre pas — et `_audit()` le RASTERISE pour le prouver, il ne le suppose
#: pas.
DOOR_TOOTH = 0.12
DOOR_NOTCH = 0.10
DOOR_TEETH = 6

#: Sabot de guidage a chaque extremite en Z, la ou le battant s'engage dans le
#: cadre : bande surelevee au plan de la poutre, creusee d'une rainure.
DOOR_SHOE = 0.45
#: Refend entre deux caissons.
DOOR_LAND = 0.65

#: LE CHEVRON — le sens de lecture, et il ne coute pas un triangle.
#: La levre INTERIEURE des caissons n'est pas droite : elle s'ecarte vers
#: l'exterieur (-X) a mesure qu'on approche du milieu du battant. Les trois
#: caissons dessinent donc une pointe large, tournee vers le cote ou le battant
#: se retire. Un chevron en relief aurait coute quatre stations de profil, soit
#: +448 triangles pour la paire : le budget de 1 200 ne les a pas.
DOOR_RIM_IN_END = -0.62
DOOR_RIM_IN_MID = -1.70
DOOR_RIM_OUT = -2.66

#: Budget du brief pour les DEUX battants reunis.
TRI_BUDGET_DOORS = 1_200

#: OU CHAQUE PIECE TOMBE DANS LE HANGAR ASSEMBLE, et combien de fois.
#: ⚠️ Ce n'est pas une commodite de rapport : sans elle, l'aire par materiau se
#: mesurerait dans le repere de CHAQUE piece, ou la jupe enterree du coaming
#: passe pour visible (son x local vaut 0 a 0,80, alors qu'assemblee elle est a
#: 3,00 a 3,80 du centre). La repartition 80/15/5 du brief parle de l'ecran :
#: elle doit se mesurer la ou les pieces sont posees, et avec leurs copies.
ASSEMBLY_OFFSET: dict[str, tuple[float, float, float]] = {}
ASSEMBLY_COPIES: dict[str, int] = {}

#: Les neuf noms de nœuds. Le moteur monte par le NOM : le harnais echoue si
#: l'un manque, si l'un est en trop, ou si l'un porte un enfant.
#:
#: ⚠️ LES DEUX BATTANTS SONT EN FIN DE LISTE, ET CE N'EST PAS COSMETIQUE. Les
#: sept premieres pieces sont acceptees, cablees et mesurees cote moteur : leurs
#: accesseurs doivent sortir aux memes octets qu'avant BRIEF-0095. L'exporteur
#: ecrit dans l'ordre des objets ; ajouter en tete decalerait les sept.
PART_NAMES = (
    "bay_frame_left", "bay_frame_right", "bay_frame_top",
    "bay_inner_wall", "bay_floor", "bay_launch_rail", "bay_service_block",
    "bay_door_left", "bay_door_right",
)
#: Les sept pieces que BRIEF-0095 s'interdit de toucher. Le harnais compare leurs
#: accesseurs a la reference si on la lui donne (`--check-frozen <glb>`).
FROZEN_PARTS = PART_NAMES[:7]

ASSEMBLY_OFFSET.update({
    "bay_frame_left": (-OPEN_HALF_X, 0.0, 0.0),
    "bay_frame_right": (OPEN_HALF_X, 0.0, 0.0),
    "bay_frame_top": (0.0, 0.0, OPEN_HALF_Z),
    "bay_inner_wall": (0.0, 0.0, 0.0),
    "bay_floor": (0.0, -WELL_DEPTH, 0.0),
    "bay_launch_rail": (-RAIL_GAUGE * 0.5, -WELL_DEPTH, -RAIL_LEN * 0.5),
    "bay_service_block": (OPEN_HALF_X + COAM_W * 0.5, COAM_H, 2.6),
    # Fermes, les deux battants sont a leur point d'assemblage : leur origine EST
    # le centre de l'ouverture, au plan de la peau.
    "bay_door_left": (0.0, 0.0, 0.0),
    "bay_door_right": (0.0, 0.0, 0.0),
})
#: La traverse est posee DEUX fois (avant et arriere, demi-tour), le rail deux
#: fois (les deux voies) et le bloc deux fois (la variation que le brief prevoit).
ASSEMBLY_COPIES.update({name: 1 for name in PART_NAMES})
ASSEMBLY_COPIES.update({"bay_frame_top": 2, "bay_launch_rail": 2,
                        "bay_service_block": 2})

#: Meme densite que le borde : voir l'en-tete (deux echelles sur un meme slot).
TEXELS_PER_METER = cortege.HULL_TEXELS_PER_METER

#: Budget du brief : 20 000 tri pour sept instances, soit ~2 800 par hangar
#: assemble. Un hangar = les 7 pieces, le rail compte double.
TRI_BUDGET_ASSEMBLED = 2_800
TRI_BUDGET_LEVEL = 20_000

#: Couleurs reservees aux TIRS (charte SS3) : interdites ici comme ailleurs.
FORBIDDEN_HEX = cortege.FORBIDDEN_HEX


# ==========================================================================
# Primitives — bobinage CALCULE, jamais suppose
# ==========================================================================


def _new_object(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    """Objet a 7 slots normalises, SANS `recalc_face_normals`.

    Meme raison que sur la coque : plusieurs pieces de ce kit sont des surfaces
    OUVERTES (l'anneau de paroi n'a ni dessus ni dessous), et l'heuristique de
    bmesh peut y retourner toute la piece. Une paroi a l'envers laisse voir le
    vide interieur de la coque — exactement le defaut que le brief interdit — et
    aucune bbox, aucun compte de triangles, aucune mesure d'UV ne le verrait.
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


def _face_facing(bm: bmesh.types.BMesh, verts: list, material: str, want: Vector):
    """Une face dont la normale part du cote `want`. Deterministe."""
    if len(verts) < 3:
        return None
    normal = (verts[1].co - verts[0].co).cross(verts[2].co - verts[0].co)
    order = list(verts) if normal.dot(want) >= 0.0 else list(reversed(verts))
    return _face(bm, order, material)


def _quad_facing(bm: bmesh.types.BMesh, a, b, c, d, material: str, want: Vector):
    """Un quad dont la normale part du cote `want`. Deterministe.

    Le sens est CALCULE et non ecrit a la main : l'anneau de paroi fait le tour du
    puits et le bon sens change a chaque cote. Une regle ecrite a la main y serait
    fausse une fois sur deux.
    """
    verts = [a, b, c, d]
    normal = (b.co - a.co).cross(c.co - a.co)
    if normal.dot(want) < 0.0:
        verts.reverse()
    return _face(bm, verts, material)


def _octagon(hx: float, hz: float, chamfer: float) -> list[tuple[float, float]]:
    """Rectangle 2hx x 2hz aux quatre coins coupes. Sens trigonometrique en (x, z).

    L'octogone n'est pas un ornement : c'est la forme des ouvertures de la planche
    de consignes, et un coin coupe est ce qui empeche une arete a 90 deg de
    scintiller a 23 px/m.
    """
    return [
        (hx, hz - chamfer), (hx - chamfer, hz),
        (-(hx - chamfer), hz), (-hx, hz - chamfer),
        (-hx, -(hz - chamfer)), (-(hx - chamfer), -hz),
        (hx - chamfer, -hz), (hx, -(hz - chamfer)),
    ]


def _loft_ring(bm: bmesh.types.BMesh,
               rings: list[tuple[list[tuple[float, float]], float]],
               materials: list[str], inward: bool) -> None:
    """Relie des anneaux fermes empiles en Y, normales vers l'interieur ou non.

    `rings` : (points (x, z), y). `materials` : un par bande, du bas de la liste
    vers le haut. `inward` : les faces regardent l'axe du puits.
    """
    verts = [[bm.verts.new(Vector((x, y, z))) for x, z in points]
             for points, y in rings]
    for k in range(len(rings) - 1):
        low, high = verts[k], verts[k + 1]
        count = len(low)
        for i in range(count):
            j = (i + 1) % count
            mid = (low[i].co + low[j].co + high[i].co + high[j].co) * 0.25
            radial = Vector((mid.x, 0.0, mid.z))
            if radial.length > 1e-6:
                radial.normalize()
            want = -radial + Vector((0.0, 1.0, 0.0))
            if not inward:
                want = radial + Vector((0.0, 1.0, 0.0))
            _quad_facing(bm, low[i], low[j], high[j], high[i],
                         materials[k], want)


def _sweep(bm: bmesh.types.BMesh,
           sections: list[list[Vector]], materials: list[str],
           cap_first: bool, cap_last: bool, cap_material: str) -> None:
    """Balaye un profil FERME le long d'une suite de sections.

    Les normales sont posees par la regle de la main droite du profil : chaque
    section est donnee dans le sens qui rend les faces sortantes, ce que
    `_assert_outward()` reverifie piece par piece sur le maillage fini.
    """
    verts = [[bm.verts.new(p) for p in section] for section in sections]
    count = len(sections[0])
    for k in range(len(sections) - 1):
        low, high = verts[k], verts[k + 1]
        for i in range(count):
            j = (i + 1) % count
            _face(bm, [low[i], low[j], high[j], high[i]], materials[i])
    if cap_first:
        _face(bm, list(reversed(verts[0])), cap_material)
    if cap_last:
        _face(bm, list(verts[-1]), cap_material)


# ==========================================================================
# LE COAMING — un cadre epais, et c'est toute la silhouette
# ==========================================================================
#
# Section transversale, en (u, y) : `u` est la distance vers l'EXTERIEUR depuis le
# bord de l'ouverture, `y` la hauteur au-dessus de la peau. Huit points, pas un de
# plus, et chacun a une raison :
#
#      +0.60  P0 ___________ P1            P0 P1  le dessus, plat
#                            \  P2         P1 P2  le chanfrein : l'arete vive
#      +0.44  P7 |            |            P6 P7  LA BANDE EMISSIVE, 14 cm
#      +0.30  P6 |            |                   (regle 3 : en partie, jamais tout)
#       0.00     |            | P3         P2 P3  la face exterieure
#             ---|------------|---  peau
#      -1.80  P5 |________ P4              P3 P4  la jupe, en depouille
#                                          P4 P5  le dessous, enterre
#                                          P5..P0 la face INTERNE, au plan exact
#                                                 de l'ouverture
#
# ⚠️ La face interne est a u = 0 EXACTEMENT. C'est ce qui fait que le coaming ne
# retrecit pas l'ouverture de 6,00 m : il la borde, il ne la mord pas.
COAM_SECTION: tuple[tuple[float, float, str], ...] = (
    (0.00, COAM_H, "AA_Hull"),                          # P0 -> P1 : dessus
    (0.66, COAM_H, "AA_Trim"),                          # P1 -> P2 : chanfrein
    (1.00, COAM_H - 0.18, "AA_Hull"),                   # P2 -> P3 : face ext.
    (1.00, -0.30, "AA_Greeble"),                        # P3 -> P4 : jupe
    (0.60, -COAM_SKIRT, "AA_Greeble"),                  # P4 -> P5 : dessous
    (0.00, -COAM_SKIRT, "AA_Greeble"),                  # P5 -> P6 : face int. bas
    (0.00, 0.30, "AA_Emissive_Engine"),                 # P6 -> P7 : LA BANDE
    (0.00, 0.44, "AA_Greeble"),                         # P7 -> P0 : face int. haut
)


def _coam_section(origin: Vector, out: Vector, along: Vector,
                  offset: float, scale: float) -> list[Vector]:
    """Une section du coaming posee dans le monde du kit.

    `out` : la direction vers l'exterieur du hangar. `along` : l'axe de balayage.
    `scale` : retrait de la face exterieure (1 au courant, 0,35 aux extremites).
    """
    return [origin + along * offset + out * (u * COAM_W * scale)
            + Vector((0.0, y, 0.0))
            for u, y, _ in COAM_SECTION]


def _build_coaming_beam(name: str, out: Vector, along: Vector,
                        half_length: float, chamfered_ends: bool
                        ) -> bpy.types.Object:
    """Un montant ou une traverse de coaming.

    Les MONTANTS possedent les quatre coins (ils courent sur toute la longueur,
    debord compris) et leurs extremites sont chanfreinees ; les TRAVERSES se
    logent entre eux. Aucun recouvrement, aucun trou : les faces internes des
    montants sont a |x| = 3,00 et la traverse va de -3,00 a +3,00.
    """
    bm = bmesh.new()
    origin = Vector((0.0, 0.0, 0.0))
    if chamfered_ends:
        stops = ((-half_length, COAM_END_SCALE), (-half_length + COAM_END, 1.0),
                 (half_length - COAM_END, 1.0), (half_length, COAM_END_SCALE))
    else:
        stops = ((-half_length, 1.0), (half_length, 1.0))
    sections = [_coam_section(origin, out, along, offset, scale)
                for offset, scale in stops]
    materials = [m for _, _, m in COAM_SECTION]
    # ⚠️ Le sens du profil depend de l'orientation du triedre (out, along, Y) :
    # ecrit a la main, il serait faux pour le montant droit, qui est un MIROIR du
    # gauche et non une copie. On le CALCULE.
    if out.cross(Vector((0.0, 1.0, 0.0))).dot(along) < 0.0:
        sections = [list(reversed(s)) for s in sections]
        materials = list(reversed(materials[-1:] + materials[:-1]))
    _sweep(bm, sections, materials, cap_first=True, cap_last=True,
           cap_material="AA_Hull")
    return _new_object(name, bm)


def build_frame_left() -> bpy.types.Object:
    """Montant gauche. Origine : bord GAUCHE de l'ouverture, a hauteur de peau."""
    return _build_coaming_beam(
        "bay_frame_left", out=Vector((-1.0, 0.0, 0.0)),
        along=Vector((0.0, 0.0, 1.0)),
        half_length=OPEN_HALF_Z + COAM_W, chamfered_ends=True)


def build_frame_right() -> bpy.types.Object:
    """Montant droit — MIROIR du gauche, pas une copie.

    Une copie translatee aurait ses faces retournees (le triedre change de
    chiralite) : la piece disparaitrait en jeu par culling arriere, sans une
    ligne au journal. C'est pour cela que `_build_coaming_beam` calcule le sens
    du profil au lieu de l'ecrire.
    """
    return _build_coaming_beam(
        "bay_frame_right", out=Vector((1.0, 0.0, 0.0)),
        along=Vector((0.0, 0.0, 1.0)),
        half_length=OPEN_HALF_Z + COAM_W, chamfered_ends=True)


def build_frame_top() -> bpy.types.Object:
    """Traverse avant (cote proue). Origine : milieu du bord avant.

    Le moteur la pose DEUX fois — a l'avant telle quelle, a l'arriere tournee
    d'un demi-tour : c'est la meme piece, et c'est ce qui fait un anneau ferme
    avec trois nœuds au lieu de quatre.
    """
    return _build_coaming_beam(
        "bay_frame_top", out=Vector((0.0, 0.0, 1.0)),
        along=Vector((1.0, 0.0, 0.0)),
        half_length=OPEN_HALF_X, chamfered_ends=False)


# ==========================================================================
# LA GORGE ET LE FOND — ce qui ferme le puits
# ==========================================================================


def build_inner_wall() -> bpy.types.Object:
    """La paroi du puits, en anneau ferme. Origine : centre, a hauteur de peau.

    Six anneaux, cinq bandes, et chacune fait un travail :

        levre  ->  haut de paroi   le SOFFITE : il rentre de 1,10 m en 0,30 m de
                                   chute. C'est lui qui ferme le puits sous le
                                   coaming, et c'est lui que le harnais verifie.
        haut   ->  bas de paroi    la paroi, en legere depouille (8 cm sur 1,12) :
                                   elle accroche la lumiere rasante et dit
                                   « profond » sans une seule texture.
        ressaut                    12 cm de retrait, en violet sombre : il donne
                                   au puits un PIED, sans quoi la paroi et le
                                   fond fusionnent en un seul aplat noir.
        bande                      18 cm d'emissif, AU PIED, jamais au fond.
        raccord                    la derniere marche vers le fond.

    ⚠️ L'anneau n'a ni dessus ni dessous : c'est une surface ouverte, et ses
    normales sont posees par calcul (`_loft_ring(inward=True)`). Retournee, elle
    laisserait voir l'interieur creux de la coque.
    """
    inner_x = OPEN_HALF_X - WALL_INSET
    inner_z = OPEN_HALF_Z - WALL_INSET
    rings = [
        (_octagon(inner_x - 0.32, inner_z - 0.32, 0.42), -WELL_DEPTH),
        (_octagon(inner_x - 0.20, inner_z - 0.20, 0.44), -WELL_DEPTH + 0.12),
        (_octagon(inner_x - 0.20, inner_z - 0.20, 0.44), -WELL_DEPTH + 0.30),
        (_octagon(inner_x - 0.08, inner_z - 0.08, 0.46), -WELL_DEPTH + 0.38),
        (_octagon(inner_x, inner_z, 0.50), -0.30),
        (_octagon(OPEN_HALF_X + LIP_OUT, OPEN_HALF_Z + LIP_OUT, 0.50), 0.0),
    ]
    materials = ["AA_Greeble",              # raccord au fond
                 "AA_Emissive_Engine",      # la bande de pied
                 "AA_Panel",                # le ressaut
                 "AA_Greeble",              # la paroi
                 "AA_Greeble"]              # le soffite
    bm = bmesh.new()
    _loft_ring(bm, rings, materials, inward=True)
    return _new_object("bay_inner_wall", bm)


def build_floor() -> bpy.types.Object:
    """Le fond. Origine : centre, a -1,80 m sous la peau — donc Y = 0 chez lui.

    Une DALLE et non un plan : une surface d'epaisseur nulle vue de trois quarts
    ne rend rien sur sa tranche, et le fond du puits est justement ce qu'on voit
    en biais. Elle deborde du pied de l'anneau : le harnais verifie qu'elle le
    couvre, faute de quoi un liseré de vide courrait tout autour.

    ⛔ AUCUN EMISSIF ICI. C'est la faute de BRIEF-0089, et elle est nommee dans le
    brief : « un fond magenta plein ». La lumiere du puits vient des bandes, pas
    du sol.
    """
    inner_x = OPEN_HALF_X - WALL_INSET
    inner_z = OPEN_HALF_Z - WALL_INSET
    top = _octagon(inner_x - 0.10, inner_z - 0.10, 0.45)
    low = _octagon(inner_x - 0.24, inner_z - 0.24, 0.42)
    bm = bmesh.new()
    _loft_ring(bm, [(low, -0.28), (top, 0.0)], ["AA_Greeble"], inward=False)
    plate = [bm.verts.new(Vector((x, 0.0, z))) for x, z in top]
    _face_facing(bm, plate, "AA_Greeble", Vector((0.0, 1.0, 0.0)))
    return _new_object("bay_floor", bm)


# ==========================================================================
# L'APPAREILLAGE — rails et bloc de servitude
# ==========================================================================


def build_launch_rail() -> bpy.types.Object:
    """UN rail ; le moteur en pose deux. Origine : au fond, a l'ARRIERE du puits.

    Il court vers la sortie (+Z, cote proue) et s'abaisse aux deux bouts : une
    rampe, pas une poutre posee. Deux filets emissifs courent a son pied — c'est
    la deuxieme des trois bandes du kit, et celle qui dit dans quel sens
    l'appareil part.
    """
    half_b, half_t = RAIL_W * 0.5, RAIL_W * 0.5 - 0.04
    stops = ((0.0, 0.10), (0.45, RAIL_H), (RAIL_LEN - 0.60, RAIL_H),
             (RAIL_LEN, 0.10))
    sections = [[Vector((-half_b, 0.0, z)), Vector((-half_t, h, z)),
                 Vector((half_t, h, z)), Vector((half_b, 0.0, z))]
                for z, h in stops]
    bm = bmesh.new()
    # ⚠️ Le rail est tout entier en `AA_Trim` — c'est L'APPAREILLAGE de la
    # planche (« 15 pct grege moyen : les rails, les blocs de servitude »), et
    # c'est ce qui doit se detacher du puits sombre pour que le joueur comprenne
    # sur quoi l'appareil est pose. Seul son dessous, jamais vu, reste sombre.
    _sweep(bm, sections,
           ["AA_Trim", "AA_Trim", "AA_Trim", "AA_Greeble"],
           cap_first=True, cap_last=True, cap_material="AA_Trim")
    # Les deux filets, a plat sur le fond, 1,5 cm au-dessus pour ne pas
    # scintiller contre lui.
    for side in (-1.0, 1.0):
        a, b = half_b + 0.01, half_b + 0.10
        quad = [Vector((side * a, 0.015, 0.25)), Vector((side * b, 0.015, 0.25)),
                Vector((side * b, 0.015, RAIL_LEN - 0.25)),
                Vector((side * a, 0.015, RAIL_LEN - 0.25))]
        verts = [bm.verts.new(p) for p in quad]
        _quad_facing(bm, *verts, "AA_Emissive_Engine", Vector((0.0, 1.0, 0.0)))
    return _new_object("bay_launch_rail", bm)


def build_service_block() -> bpy.types.Object:
    """Bloc de servitude — optionnel, pour varier. Origine : sa base.

    ⚠️ SA HAUTEUR EST BORNEE PAR LE PLAFOND DU JEU, pas par le gout. Pose sur le
    dessus du coaming (bouche + 0,60), il culmine a bouche + 1,05. La bouche la
    plus haute des sept baies est a -4,321 : le bloc s'arrete a -3,271, sous le
    plafond de construction -3,200. Le harnais le recalcule a chaque build.
    """
    rings = [
        (_octagon(BLOCK_X * 0.5, BLOCK_Z * 0.5, 0.16), 0.0),
        (_octagon(BLOCK_X * 0.5, BLOCK_Z * 0.5, 0.16), BLOCK_H - 0.17),
        (_octagon(BLOCK_X * 0.5 - 0.03, BLOCK_Z * 0.5 - 0.03, 0.15),
         BLOCK_H - 0.09),
        (_octagon(BLOCK_X * 0.5 - 0.10, BLOCK_Z * 0.5 - 0.10, 0.14), BLOCK_H),
    ]
    bm = bmesh.new()
    _loft_ring(bm, rings, ["AA_Trim", "AA_Emissive_Engine", "AA_Trim"],
               inward=False)
    top = [bm.verts.new(Vector((x, BLOCK_H, z))) for x, z in rings[-1][0]]
    _face_facing(bm, top, "AA_Hull", Vector((0.0, 1.0, 0.0)))
    return _new_object("bay_service_block", bm)


# ==========================================================================
# LES BATTANTS — ce qui fermait le puits en BoxMesh (BRIEF-0095)
# ==========================================================================
#
# Section transversale d'un battant, en (x, y), du bord de JONCTION vers
# l'exterieur. Douze stations, pas une de plus, et le budget de 1 200 triangles
# pour la paire est ce qui a fixe ce douze : chaque station coute 2 triangles par
# span, et le battant en compte une vingtaine.
#
#   +0.175  S2___S3                      S0 S1  la face de jonction
#          /      \S4___S5               S1 S2  LE TRAIT DE BORDURE (emissif)
#   +0.150 |             \               S2 S3  la poutre de nez, 28 cm
#          |S1            S6____S7       S3 S4  la marche vers le plan courant
#   +0.075 |              (caisson)      S4 S5  le plan courant
#          |                    /S8_S9   S5 S6  la levre du caisson — LE CHEVRON
#          |                        \S10 S6 S7  le fond du caisson, 7,5 cm creux
#    0.000 S0______________________ S11  S8 S9  le plan courant, cote exterieur
#                                        S9 S10 le chanfrein exterieur
#          x = e                x = -3,00 S10 S11 la face exterieure
#                                        S11 S0 LE DESSOUS, PLAT, a y = 0
#
# ⚠️ LE DESSOUS EST PLAT ET SANS TROU, ET C'EST LUI QUI FAIT L'OBSCURITE. Le
# brief ne demande pas une porte jolie, il demande que le puits ne fuie pas sa
# lueur magenta quand il ne produit pas : c'est le contraste noir -> magenta qui
# fait lire l'ouverture. Une seule fente et le contraste tombe.
#
# ⚠️ ET LE PROFIL EST STRICTEMENT DECROISSANT EN X. Ce n'est pas une elegance :
# le bord de jonction se DEPLACE avec la denture (de +0,12 a -0,10), et si une
# station de la poutre de nez passait derriere la levre du caisson, le profil se
# croiserait — un solide retourne sur lui-meme, que ni la bbox ni le compte de
# triangles ne verraient. `_door_section()` le verifie a chaque section.


def _door_bands() -> list[tuple[float, float, str]]:
    """Le decoupage en Z : sabot, caisson, refend, caisson, refend, caisson, sabot.

    ⚠️ SYMETRIQUE EN Z, ET C'EST CE QUI PERMET AU BATTANT TRIBORD D'EXISTER. Le
    battant droit est le gauche tourne d'un demi-tour (voir `build_door_right`) :
    tout ce qui n'est pas symetrique en Z y apparaitrait retourne. Seule la
    denture ne l'est pas — et c'est justement ce qu'on veut, puisque c'est ce qui
    la rend complementaire.
    """
    inner = DOOR_HALF_Z - DOOR_SHOE
    pocket = (2.0 * inner - 2.0 * DOOR_LAND) / 3.0
    bands = [(-DOOR_HALF_Z, -inner, "shoe")]
    z = -inner
    for k in range(3):
        bands.append((z, z + pocket, "pocket"))
        z += pocket
        if k < 2:
            bands.append((z, z + DOOR_LAND, "land"))
            z += DOOR_LAND
    bands.append((inner, DOOR_HALF_Z, "shoe"))
    return bands


def _door_edge(z: float) -> float:
    """L'abscisse du bord de jonction a la cote `z` — la denture.

    Bandes paires : la dent avance a +0,12. Bandes impaires : le creux recule a
    -0,10. Le battant tribord etant le miroir par demi-tour, la bande `k` du
    gauche fait face a la bande `DOOR_TEETH - 1 - k` du droit, de parite
    opposee : une dent tombe toujours en face d'un creux.
    """
    step = 2.0 * DOOR_HALF_Z / DOOR_TEETH
    index = int(math.floor((z + DOOR_HALF_Z) / step + 1e-9))
    index = max(0, min(DOOR_TEETH - 1, index))
    return DOOR_TOOTH if index % 2 == 0 else -DOOR_NOTCH


def _door_section(z: float, kind: str, edge: float) -> list[Vector]:
    """Les douze stations du profil, posees a la cote `z`."""
    top = DOOR_RIM_TOP
    main = DOOR_RIM_TOP if kind == "shoe" else DOOR_TOP
    if kind == "pocket":
        floor = DOOR_POCKET_Y
    elif kind == "shoe":
        floor = DOOR_SHOE_GROOVE_Y
    else:
        floor = main
    # Le chevron : la levre interieure s'ecarte vers -X au milieu du battant.
    fraction = 1.0 - abs(z) / DOOR_HALF_Z
    rim_in = DOOR_RIM_IN_END + (DOOR_RIM_IN_MID - DOOR_RIM_IN_END) * fraction
    profile = [
        (edge, 0.0),
        (edge, top - 0.09),
        (edge - 0.09, top),
        (edge - 0.28, top),
        (edge - 0.34, main),
        (rim_in, main),
        (rim_in - 0.06, floor),
        (DOOR_RIM_OUT + 0.06, floor),
        (DOOR_RIM_OUT, main),
        (-DOOR_SPAN_X + 0.06, main),
        (-DOOR_SPAN_X, main - 0.06),
        (-DOOR_SPAN_X, 0.0),
    ]
    for (xa, _), (xb, _) in zip(profile, profile[1:]):
        if xb > xa + 1e-9:
            raise ak.ContractError(
                f"bay_door : profil non decroissant en x a z = {z:+.3f} "
                f"({xa:+.4f} puis {xb:+.4f}) — le solide se croiserait")
    return [Vector((x, y, z)) for x, y in profile]


#: Materiau de chaque arete du profil, index par index. Les caissons et le
#: dessous sont sombres (regle 2 du kit : ce qui regarde le puits est plus sombre
#: que ce qui regarde le ciel) ; la poutre de nez, le chanfrein exterieur et les
#: sabots sont de l'APPAREILLAGE, comme les rails.
DOOR_MATERIALS: tuple[str, ...] = (
    "AA_Greeble",              # S0 S1 face de jonction — matee, jamais vue
    "AA_Emissive_Engine",      # S1 S2 LE TRAIT DE BORDURE
    "AA_Hull",                 # S2 S3 poutre de nez
    "AA_Greeble",              # S3 S4 marche — une ligne d'ombre
    "AA_Hull",                 # S4 S5 plan courant
    "AA_Greeble",              # S5 S6 levre du caisson
    "AA_Greeble",              # S6 S7 fond du caisson
    "AA_Greeble",              # S7 S8 levre exterieure du caisson
    "AA_Hull",                 # S8 S9 plan courant
    "AA_Trim",                 # S9 S10 chanfrein exterieur — LE SEUL filet clair
    "AA_Greeble",              # S10 S11 face exterieure
    "AA_Greeble",              # S11 S0 le dessous
)


def _door_span_materials(kind: str, wall: bool) -> list[str]:
    """Les materiaux d'une bande, selon ce qu'elle est.

    Sur un refend il n'y a pas de caisson : les aretes S5..S8 y sont du plan
    courant, et les peindre en `AA_Greeble` y tracerait trois bandes noires sur
    une surface plate. Sur un sabot, la rainure reste en `AA_Greeble` : creux =
    sombre, la meme regle que pour les caissons. `AA_Panel` (le violet du
    ressaut) y a ete essaye puis retire — sur les battants RETIRES, deux barres
    violettes couraient en travers du borde et tiraient l'œil plus que la lueur
    du puits, qui est l'information.

    ⚠️ AUCUNE GRANDE SURFACE EN `AA_Trim` SUR UN BATTANT, ET C'EST UNE CORRECTION
    DE RENDU. Le premier jet donnait la poutre de nez et les sabots a `AA_Trim`
    — l'ivoire froid #DDDCD2 de l'appareillage, celui des rails. Dans le puits
    sombre il detache le rail ; sur la PEAU, a cote d'un coaming en #24252B, il
    faisait deux cadres blancs autour de trous noirs, et les battants ne
    lisaient plus comme la piece qui les entoure. Il ne reste de `AA_Trim` que
    le filet du chanfrein exterieur, large de 6 cm, exactement comme sur le
    chanfrein du coaming.
    """
    if wall:                                   # la joue d'une dent : tout sombre
        return ["AA_Greeble"] * len(DOOR_MATERIALS)
    materials = list(DOOR_MATERIALS)
    if kind == "shoe":
        for i in (5, 6, 7):
            materials[i] = "AA_Greeble"
    elif kind == "land":
        for i in (5, 6, 7):
            materials[i] = "AA_Hull"
    return materials


def _door_sweep(bm: bmesh.types.BMesh,
                sections: list[tuple[list[Vector], str, bool]]) -> None:
    """Balaye le profil ferme le long des sections, materiau par bande."""
    verts = [[bm.verts.new(p) for p in points] for points, _, _ in sections]
    count = len(sections[0][0])
    for k in range(len(sections) - 1):
        low, high = verts[k], verts[k + 1]
        kind = sections[k + 1][1]
        wall = abs(sections[k + 1][0][0].z - sections[k][0][0].z) < 1e-9
        materials = _door_span_materials(kind, wall)
        for i in range(count):
            j = (i + 1) % count
            _face(bm, [low[i], low[j], high[j], high[i]], materials[i])
    _face(bm, list(reversed(verts[0])), "AA_Greeble")
    _face(bm, list(verts[-1]), "AA_Greeble")


def _build_door(name: str, turn: bool) -> bpy.types.Object:
    """Un battant. `turn` : demi-tour autour de Y (le battant tribord).

    ⚠️ UN DEMI-TOUR, PAS UN MIROIR, ET LA DIFFERENCE EST TOUT LE SUJET. Un miroir
    en X seul ne peut PAS produire deux dentures complementaires : le bord du
    battant droit y tomberait a l'oppose de celui du gauche pour chaque z, donc
    soit les deux se chevauchent partout, soit ils laissent un jour partout —
    demontre en une ligne, `-t(z) = t(z)` n'a que la solution `t = 0`. Il faut
    retourner AUSSI en Z. Le demi-tour le fait, et il conserve la chiralite : les
    normales restent bonnes, ce qu'un miroir aurait retourne en silence.
    Visuellement, le battant reste bien le miroir de l'autre — tout le dessin est
    symetrique en Z sauf la denture, qui est justement ce qu'on veut inverser.
    """
    stops: list[float] = []
    for z0, z1, _ in _door_bands():
        stops += [z0, z1]
    step = 2.0 * DOOR_HALF_Z / DOOR_TEETH
    stops += [-DOOR_HALF_Z + step * k for k in range(1, DOOR_TEETH)]
    cuts: list[float] = []
    for z in sorted(stops):
        if not cuts or abs(z - cuts[-1]) > 1e-6:
            cuts.append(z)

    sections: list[tuple[list[Vector], str, bool]] = []
    for z0, z1 in zip(cuts, cuts[1:]):
        middle = 0.5 * (z0 + z1)
        kind = next(k for a, b, k in _door_bands() if a - 1e-9 <= middle <= b + 1e-9)
        edge = _door_edge(middle)
        for z in (z0, z1):
            points = _door_section(z, kind, edge)
            if sections and all((p - q).length < 1e-9
                                for p, q in zip(points, sections[-1][0])):
                continue
            sections.append((points, kind, False))
    if turn:
        sections = [([Vector((-p.x, p.y, -p.z)) for p in points], kind, wall)
                    for points, kind, wall in reversed(sections)]

    bm = bmesh.new()
    _door_sweep(bm, sections)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    # ⚠️ RECALCUL AUTORISE ICI, ET SEULEMENT ICI. L'en-tete de `_new_object()`
    # l'interdit parce que la moitie du kit est faite de surfaces OUVERTES, ou
    # l'heuristique de bmesh peut retourner toute la piece. Un battant, lui, est
    # un solide FERME : le recalcul y est exact, et `_audit()` le prouve sur le
    # binaire en mesurant le volume signe, qui serait negatif si les normales
    # rentraient.
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _new_object(name, bm)


def build_door_left() -> bpy.types.Object:
    """Le battant bâbord. Origine : arete de jonction (x = 0), milieu (z = 0),
    plan de la peau (y = 0). Il couvre x de -3,00 a 0 et se retire vers -X."""
    return _build_door("bay_door_left", turn=False)


def build_door_right() -> bpy.types.Object:
    """Le battant tribord, demi-tour du bâbord. Il couvre 0 a +3,00, part vers +X."""
    return _build_door("bay_door_right", turn=True)


# ==========================================================================
# Harnais de scene (avant export)
# ==========================================================================


# ⚠️ `_triangulate()` A DISPARU, ET C'EST UNE PROMOTION (BRIEF-0092).
# Ce fichier a decouvert le defaut — les montants chanfreines font des quads
# GAUCHES (leur determinant vaut 1,5 dz (b-a) ds, jamais nul), et `box_project_uv`
# les projetait selon une normale moyenne qui n'est celle d'aucun de leurs deux
# triangles : densite minimale mesuree 0,078 tuile/m pour une borne theorique de
# 0,116. Mais RIEN dans ce raisonnement n'est propre a ce kit : n'importe quel
# asset du depot peut porter un quad gauche, et le defaut est silencieux partout
# pareil. La correction vit donc dans `aegis_kit.triangulate()`, appelee par
# `box_project_uv()` elle-meme. Le kit triangule ici pour tout le monde ; ce
# fichier n'a plus a s'en souvenir.


def _assert_outward(obj: bpy.types.Object, axis: Vector) -> None:
    """Les faces d'une piece regardent-elles du bon cote ?

    ⚠️ CE HARNAIS EXISTE PARCE QUE LE DEFAUT EST TOTALEMENT SILENCIEUX. Une piece
    retournee ne rate aucune bbox, aucun compte de triangles, aucune mesure d'UV :
    elle DISPARAIT en jeu (culling arriere), et le journal reste muet. Sur ce kit,
    une paroi retournee laisserait voir l'interieur creux de la coque — le defaut
    que le brief nomme « pire que pas de puits ».

    `axis` : la direction ou la piece est censee ne PAS regarder (l'axe du puits
    pour l'anneau, le bas pour le fond).
    """
    mesh = obj.data
    mesh.calc_loop_triangles()
    wrong = 0
    checked = 0
    for polygon in mesh.polygons:
        centre = polygon.center
        radial = Vector((centre.x, 0.0, centre.z))
        if axis.y < -0.5:                     # le fond : rien ne regarde en bas
            if polygon.normal.y < -0.55:
                wrong += 1
            checked += 1
            continue
        if radial.length < 0.05 or abs(polygon.normal.y) > 0.75:
            continue
        radial.normalize()
        checked += 1
        if polygon.normal.dot(radial) > 0.35:
            wrong += 1
    if checked < 8:
        raise ak.ContractError(f"{obj.name} : {checked} faces controlables, "
                               "le harnais d'orientation ne prouve rien")
    if wrong:
        raise ak.ContractError(
            f"{obj.name} : {wrong} faces sur {checked} regardent du mauvais cote "
            "— la piece disparaitrait en jeu sans un mot")


def build_parts() -> list[bpy.types.Object]:
    parts = [
        build_frame_left(), build_frame_right(), build_frame_top(),
        build_inner_wall(), build_floor(), build_launch_rail(),
        build_service_block(),
        build_door_left(), build_door_right(),
    ]
    names = [obj.name for obj in parts]
    if names != list(PART_NAMES):
        raise ak.ContractError(
            f"contrat de noms rompu : {names} au lieu de {list(PART_NAMES)}")
    _assert_outward(bpy.data.objects["bay_inner_wall"],
                    Vector((1.0, 0.0, 0.0)))
    _assert_outward(bpy.data.objects["bay_floor"], Vector((0.0, -1.0, 0.0)))
    for obj in parts:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
        bm.to_mesh(obj.data)
        bm.free()
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

    Le kit est fait de pieces dont l'avant et l'arriere ne se ressemblent pas
    (le rail monte d'un cote, la traverse n'existe que cote proue). Une chaine
    d'axes fausse d'un demi-tour les poserait a l'envers dans chaque hangar, et
    la bounding box ne le dirait pas.
    """
    for probe in (Vector((1.0, 2.0, 3.0)), Vector((-3.0, 0.6, 4.25)),
                  Vector((1.15, -1.8, -3.3))):
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
    staging = tempfile.mkdtemp(prefix="aegis-baykit-")
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
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    counts = {"VEC2": 2, "VEC3": 3, "VEC4": 4, "SCALAR": 1}[acc["type"]]
    fmt = {5126: "f", 5125: "I", 5123: "H", 5121: "B"}[acc["componentType"]]
    size = struct.calcsize("<" + fmt) * counts
    stride = view.get("byteStride", size)
    base = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    return [struct.unpack_from("<" + fmt * counts, blob, base + i * stride)
            for i in range(acc["count"])]


def _indices(gltf: dict, blob: bytes, prim: dict) -> list[int]:
    return [v[0] for v in _accessor(gltf, blob, prim["indices"])]


def _point_in_convex(point: tuple[float, float],
                     polygon: list[tuple[float, float]]) -> bool:
    """Le point est-il dans le polygone CONVEXE (ordre quelconque) ?"""
    sign = 0
    count = len(polygon)
    for i in range(count):
        ax, az = polygon[i]
        bx, bz = polygon[(i + 1) % count]
        cross = (bx - ax) * (point[1] - az) - (bz - az) * (point[0] - ax)
        if abs(cross) < 1e-9:
            continue
        if sign == 0:
            sign = 1 if cross > 0 else -1
        elif (cross > 0) != (sign > 0):
            return False
    return True


def _convex_order(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    cx = sum(p[0] for p in points) / len(points)
    cz = sum(p[1] for p in points) / len(points)
    return sorted(points, key=lambda p: math.atan2(p[1] - cz, p[0] - cx))


def _texel_density(points: list[tuple], uvs: list[tuple],
                   tris: list[tuple[int, int, int]]) -> dict:
    """Densite par VALEURS SINGULIERES de l'application plan -> UV.

    Une moyenne d'aires ne verrait aucun etirement : un triangle deux fois trop
    long dans un sens et deux fois trop court dans l'autre a la bonne aire.
    """
    lo, hi, total, weight = math.inf, 0.0, 0.0, 0.0
    aniso = 0.0
    for ia, ib, ic in tris:
        pa, pb, pc = (Vector(points[i]) for i in (ia, ib, ic))
        ua, ub, uc = (Vector(uvs[i]) for i in (ia, ib, ic))
        e1, e2 = pb - pa, pc - pa
        normal = e1.cross(e2)
        area = normal.length * 0.5
        if area < 1e-9:
            continue
        basis_x = e1.normalized()
        basis_y = normal.normalized().cross(basis_x)
        m11, m21 = e1.dot(basis_x), e1.dot(basis_y)
        m12, m22 = e2.dot(basis_x), e2.dot(basis_y)
        det = m11 * m22 - m12 * m21
        if abs(det) < 1e-12:
            continue
        du1, dv1 = ub - ua, uc - ua
        j = [[(du1.x * m22 - dv1.x * m21) / det, (dv1.x * m11 - du1.x * m12) / det],
             [(du1.y * m22 - dv1.y * m21) / det, (dv1.y * m11 - du1.y * m12) / det]]
        a = j[0][0] ** 2 + j[1][0] ** 2
        b = j[0][0] * j[0][1] + j[1][0] * j[1][1]
        c = j[0][1] ** 2 + j[1][1] ** 2
        trace, diff = a + c, math.sqrt(max((a - c) ** 2 + 4 * b * b, 0.0))
        s_max = math.sqrt(max((trace + diff) * 0.5, 0.0))
        s_min = math.sqrt(max((trace - diff) * 0.5, 0.0))
        if s_min <= 1e-9:
            continue
        lo = min(lo, s_min)
        hi = max(hi, s_max)
        aniso = max(aniso, s_max / s_min)
        total += math.sqrt(s_min * s_max) * area
        weight += area
    if weight <= 0.0:
        return {}
    mean = total / weight
    return {"tiles_per_m_min": lo, "tiles_per_m_max": hi,
            "tiles_per_m_mean": mean, "m_per_tile_mean": 1.0 / mean,
            "anisotropy_max": aniso}


def _signed_volume(points: list[tuple], tris: list[tuple[int, int, int]]) -> float:
    """Volume signe d'une soupe de triangles fermee (theoreme de la divergence).

    ⚠️ C'EST LA PREUVE QUE LES NORMALES SORTENT, ET ELLE SE FAIT SUR LE BINAIRE.
    Une piece retournee ne rate aucune bbox, aucun compte de triangles, aucune
    mesure d'UV : elle DISPARAIT en jeu par culling arriere, sans une ligne au
    journal. Sur un solide ferme, le volume signe est positif si et seulement si
    le bobinage est sortant. Aucune heuristique, aucun echantillonnage.
    """
    total = 0.0
    for ia, ib, ic in tris:
        a, b, c = (Vector(points[i]) for i in (ia, ib, ic))
        total += a.dot(b.cross(c))
    return total / 6.0


def _footprint_gap(doors: dict[str, tuple[list, list]], step: float
                   ) -> tuple[int, int, tuple[float, float] | None]:
    """L'ouverture est-elle entierement couverte par les deux battants fermes ?

    On RASTERISE l'emprise des deux solides projetee sur (x, z) et l'on compte
    les cellules decouvertes. Un solide ferme se projette exactement sur son
    emprise : inutile de trier les faces du dessous, tout triangle compte.

    ⚠️ POURQUOI MESURER PLUTOT QUE RAISONNER. La denture est le seul endroit du
    battant ou le jour peut naitre, et il y naitrait d'une erreur d'un
    centimetre sur une seule bande — invisible sur une bbox, invisible sur un
    compte de triangles, et visible en jeu comme un filet magenta qui court au
    milieu d'un pont mort. Le brief en fait un critere d'echec du build.
    """
    nx = int(round(2.0 * OPEN_HALF_X / step))
    nz = int(round(2.0 * OPEN_HALF_Z / step))
    covered = [[False] * nx for _ in range(nz)]
    for points, tris in doors.values():
        for ia, ib, ic in tris:
            ax, _, az = points[ia]
            bx, _, bz = points[ib]
            cx, _, cz = points[ic]
            area = (bx - ax) * (cz - az) - (bz - az) * (cx - ax)
            if abs(area) < 1e-12:
                continue
            i0 = max(0, int(math.floor((min(ax, bx, cx) + OPEN_HALF_X) / step)))
            i1 = min(nx - 1, int(math.ceil((max(ax, bx, cx) + OPEN_HALF_X) / step)))
            k0 = max(0, int(math.floor((min(az, bz, cz) + OPEN_HALF_Z) / step)))
            k1 = min(nz - 1, int(math.ceil((max(az, bz, cz) + OPEN_HALF_Z) / step)))
            for k in range(k0, k1 + 1):
                pz = -OPEN_HALF_Z + (k + 0.5) * step
                row = covered[k]
                for i in range(i0, i1 + 1):
                    if row[i]:
                        continue
                    px = -OPEN_HALF_X + (i + 0.5) * step
                    w0 = (bx - ax) * (pz - az) - (bz - az) * (px - ax)
                    w1 = (cx - bx) * (pz - bz) - (cz - bz) * (px - bx)
                    w2 = (ax - cx) * (pz - cz) - (az - cz) * (px - cx)
                    if area > 0.0:
                        row[i] = w0 >= 0.0 and w1 >= 0.0 and w2 >= 0.0
                    else:
                        row[i] = w0 <= 0.0 and w1 <= 0.0 and w2 <= 0.0
    holes = 0
    first: tuple[float, float] | None = None
    for k in range(nz):
        for i in range(nx):
            if not covered[k][i]:
                holes += 1
                if first is None:
                    first = (-OPEN_HALF_X + (i + 0.5) * step,
                             -OPEN_HALF_Z + (k + 0.5) * step)
    return holes, nx * nz, first


def _audit(path: str) -> dict:
    """Relit le `.glb` PRODUIT et verifie tout ce que le brief exige.

    On lit le binaire et non la scene en memoire : c'est la seule chose que Godot
    chargera. Les trois coques du depot sorties sans UV (ADR-0028) avaient toutes
    une scene Blender parfaite.
    """
    gltf, blob = _read_glb(path)
    problems: list[str] = []
    materials = [m.get("name", f"#{i}") for i, m in enumerate(gltf.get("materials", []))]
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
    seen_area: dict[str, float] = {}
    built_area: dict[str, float] = {}
    total_area = 0.0
    total_seen = 0.0
    lip: list[tuple[float, float]] = []
    wall_foot: list[tuple[float, float]] = []
    floor_top: list[tuple[float, float]] = []
    density: dict[str, dict] = {}
    doors: dict[str, tuple[list, list]] = {}

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
            material = materials[prim["material"]] if "material" in prim else "<aucun>"
            used_materials.add(material)
            base = len(pts)
            pts += points
            if has_uv:
                uvs += _accessor(gltf, blob, attrs["TEXCOORD_0"])
            for axis in range(3):
                lo[axis] = min(lo[axis], acc["min"][axis])
                hi[axis] = max(hi[axis], acc["max"][axis])
            for k in range(0, len(tri_indices) - 2, 3):
                ia, ib, ic = (tri_indices[k], tri_indices[k + 1], tri_indices[k + 2])
                tris.append((base + ia, base + ib, base + ic))
                pa = Vector(points[ia])
                area = (Vector(points[ib]) - pa).cross(
                    Vector(points[ic]) - pa).length * 0.5
                total_area += area
                area_by_material[material] = area_by_material.get(material, 0.0) + area
                # ⚠️ L'AIRE VUE ET L'AIRE ASSEMBLEE, comptees a part. La jupe enterree du coaming pese
                # lourd et ne rend pas un pixel : melangee au reste, elle
                # gonflerait la part « structure » et la repartition 80/15/5
                # deviendrait un chiffre sans rapport avec l'ecran. Est « vue »
                # ce qui est au-dessus du plan de la peau OU dans le puits.
                cx = (points[ia][0] + points[ib][0] + points[ic][0]) / 3.0
                cy = (points[ia][1] + points[ib][1] + points[ic][1]) / 3.0
                cz = (points[ia][2] + points[ib][2] + points[ic][2]) / 3.0
                ox, oy, oz = ASSEMBLY_OFFSET[name]
                cx, cy, cz = cx + ox, cy + oy, cz + oz
                copies = ASSEMBLY_COPIES[name]
                built_area[material] = built_area.get(material, 0.0) \
                    + area * copies
                if cy > -0.02 or (abs(cx) <= OPEN_HALF_X + 0.05
                                  and abs(cz) <= OPEN_HALF_Z + 0.05):
                    seen_area[material] = \
                        seen_area.get(material, 0.0) + area * copies
                    total_seen += area * copies
        if uvs:
            density[name] = _texel_density(pts, uvs, tris)
        if name.startswith("bay_door_"):
            doors[name] = (pts, tris)
        # ⚠️ Le `.glb` est DANS LE REPERE DU KIT : la chaine
        # `_AUTHOR_FIX` puis `export_yup` rend l'identite, et
        # `_assert_axis_chain()` le reverifie sur trois temoins asymetriques.
        for px, py, pz in pts:
            if name == "bay_inner_wall":
                if abs(py) < 1e-4:
                    lip.append((px, pz))
                if abs(py + WELL_DEPTH) < 1e-4:
                    wall_foot.append((px, pz))
            elif name == "bay_floor" and abs(py) < 1e-4:
                floor_top.append((px, pz))
        triangles_total += triangles
        stats[name] = {"triangles": triangles,
                       "min": tuple(lo), "max": tuple(hi),
                       "size": tuple(hi[a] - lo[a] for a in range(3))}

    # --- LE PUITS EST-IL FERME ? -----------------------------------------
    # La coque est CREUSE : une levre trop courte laisse voir l'interieur du
    # vaisseau par les coins de l'ouverture, et l'on ne s'en apercoit qu'au
    # rendu, sur un coin, a une seule perspective. Ce controle-la est
    # geometrique et il est total.
    if lip:
        ordered = _convex_order(list(set(lip)))
        for sx in (-1.0, 1.0):
            for sz in (-1.0, 1.0):
                corner = (sx * OPEN_HALF_X, sz * OPEN_HALF_Z)
                if not _point_in_convex(corner, ordered):
                    problems.append(
                        f"la levre de 'bay_inner_wall' ne couvre pas le coin "
                        f"{corner} de l'ouverture — on verrait l'interieur creux "
                        "de la coque a travers le puits")
    else:
        problems.append("'bay_inner_wall' n'a aucun sommet au plan de la peau")
    if floor_top and wall_foot:
        floor_poly = _convex_order(list(set(floor_top)))
        for point in set(wall_foot):
            if not _point_in_convex(point, floor_poly):
                problems.append(
                    "le fond ne couvre pas le pied de la paroi : un liseré de "
                    f"vide courrait autour du puits (point {point})")
                break
    # ⚠️ LA FACE INTERNE DU COAMING EST AU PLAN EXACT DE L'OUVERTURE, ET C'EST
    # CE QUI FAIT QUE LES DEUX LIVRABLES S'EMBOITENT. Chaque piece a son origine
    # au point d'assemblage : la face interne doit donc etre a 0,000 dans SON
    # repere, et la piece ne s'etendre que d'un cote. Un demi-centimetre de trop
    # et le coaming mord l'ouverture de 6,00 m ; un demi-centimetre de moins et
    # un liseré de peau nue court le long du puits.
    for name, axis, sign, span in (("bay_frame_left", 0, -1.0, COAM_W),
                                   ("bay_frame_right", 0, 1.0, COAM_W),
                                   ("bay_frame_top", 2, 1.0, COAM_W)):
        piece = stats.get(name)
        if piece is None:
            continue
        near = piece["max"][axis] if sign < 0 else piece["min"][axis]
        far = piece["min"][axis] if sign < 0 else piece["max"][axis]
        if abs(near) > 1e-4:
            problems.append(
                f"{name} : sa face interne est a {near:+.4f} au lieu de 0 — le "
                "coaming ne borde plus l'ouverture de la coque au millimetre")
        if abs(abs(far) - span) > 1e-4:
            problems.append(
                f"{name} : sa face exterieure est a {far:+.4f}, largeur "
                f"{abs(far):.4f} au lieu de {span}")
    left = stats.get("bay_frame_left")
    if left and abs(left["size"][2] - 2 * (OPEN_HALF_Z + COAM_W)) > 1e-4:
        problems.append(
            f"bay_frame_left : {left['size'][2]:.4f} m de long au lieu de "
            f"{2 * (OPEN_HALF_Z + COAM_W):.4f} — les montants possedent les "
            "quatre coins, la traverse se loge entre eux")
    top = stats.get("bay_frame_top")
    if top and abs(top["size"][0] - 2 * OPEN_HALF_X) > 1e-4:
        problems.append(
            f"bay_frame_top : {top['size'][0]:.4f} m de large au lieu de "
            f"{2 * OPEN_HALF_X:.4f}")

    # --- LES BATTANTS : emprise, plafond, sens, et AUCUN JOUR --------------
    # Les quatre cotes du brief viennent du moteur. Elles sont donc verifiees
    # ici sur le binaire, une par une, et chacune echoue le build.
    door_report: dict[str, dict] = {}
    for name, sign in (("bay_door_left", -1.0), ("bay_door_right", 1.0)):
        piece = stats.get(name)
        if piece is None:
            continue
        lo_x, lo_y, lo_z = piece["min"]
        hi_x, hi_y, hi_z = piece["max"]
        volume = _signed_volume(*doors[name])
        door_report[name] = {
            "triangles": piece["triangles"],
            "min": piece["min"], "max": piece["max"], "size": piece["size"],
            "volume": volume,
        }
        # 1. l'emprise fermee : le battant couvre SA demi-ouverture, en entier.
        outer = lo_x if sign < 0.0 else hi_x
        if abs(outer - sign * DOOR_SPAN_X) > 1e-4:
            problems.append(
                f"{name} : bord exterieur a {outer:+.4f} au lieu de "
                f"{sign * DOOR_SPAN_X:+.4f} — soit il ne rejoint pas le montant, "
                "soit il deborde du hangar une fois ouvert")
        if abs(lo_z + DOOR_HALF_Z) > 1e-4 or abs(hi_z - DOOR_HALF_Z) > 1e-4:
            problems.append(
                f"{name} : z de {lo_z:+.4f} a {hi_z:+.4f} au lieu de "
                f"{-DOOR_HALF_Z:+.4f} a {DOOR_HALF_Z:+.4f}")
        # 2. la denture franchit la ligne de fermeture, mais d'elle SEULE.
        inner = hi_x if sign < 0.0 else lo_x
        if abs(abs(inner) - DOOR_TOOTH) > 1e-4:
            problems.append(
                f"{name} : la dent avance jusqu'a {inner:+.4f} au lieu de "
                f"{sign * -DOOR_TOOTH:+.4f}")
        # 3. le plafond : il glisse SOUS la levre du coaming.
        if hi_y > 0.18 + 1e-6:
            problems.append(
                f"{name} : point le plus haut {hi_y:+.4f} > +0,18 — il chevauche "
                "la levre du coaming au lieu de passer dessous")
        if hi_y - lo_y > 0.22 + 1e-6:
            problems.append(
                f"{name} : epaisseur {hi_y - lo_y:.4f} > 0,22")
        if abs(lo_y) > 1e-6:
            problems.append(
                f"{name} : son dessous est a {lo_y:+.4f} et non au plan de la "
                "peau — l'origine EST le point d'assemblage")
        # 4. les normales sortent.
        if volume <= 0.0:
            problems.append(
                f"{name} : volume signe {volume:+.4f} — la piece est retournee, "
                "elle disparaitrait en jeu sans un mot")
    if len(doors) == 2:
        holes, cells, first = _footprint_gap(doors, 0.02)
        door_report["closure"] = {"holes": holes, "cells": cells}
        if holes:
            problems.append(
                f"les deux battants fermes laissent {holes} cellule(s) de jour "
                f"sur {cells} (premiere en {first}) — le puits fuirait sa lueur "
                "magenta alors qu'il ne produit pas")
        pair = sum(door_report[n]["triangles"] for n in
                   ("bay_door_left", "bay_door_right") if n in door_report)
        door_report["triangles"] = pair
        if pair > TRI_BUDGET_DOORS:
            problems.append(
                f"{pair} triangles pour les deux battants > budget "
                f"{TRI_BUDGET_DOORS}")

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

    # --- budget et plafond -------------------------------------------------
    assembled = triangles_total + stats.get("bay_launch_rail", {}).get(
        "triangles", 0) + stats.get("bay_frame_top", {}).get("triangles", 0)
    if assembled > TRI_BUDGET_ASSEMBLED:
        problems.append(
            f"{assembled} triangles par hangar assemble > budget "
            f"{TRI_BUDGET_ASSEMBLED}")
    mouth_high = max(cortege.bay_mouth_y(s, x)[0] for s, x in cortege.BAYS)
    top_of_bay = mouth_high + COAM_H + BLOCK_H
    if top_of_bay > cortege.BUILD_CEILING_Y:
        problems.append(
            f"le bloc de servitude pose sur le coaming culmine a {top_of_bay:.3f}, "
            f"au-dessus du plafond de construction {cortege.BUILD_CEILING_Y}")

    if problems:
        raise ak.ContractError(
            "CONTRAT ROMPU — bay_kit\n" + "\n".join(f"  - {p}" for p in problems))

    return {
        "parts": stats,
        "primitives": (prims_uv, prims_tan, prims_total),
        "triangles": triangles_total,
        "assembled": assembled,
        "level": assembled * len(cortege.BAYS),
        "materials": sorted(used_materials),
        "area_by_material": area_by_material,
        "seen_by_material": seen_area,
        "built_by_material": built_area,
        "total_built": sum(built_area.values()),
        "total_area": total_area,
        "total_seen": total_seen,
        "density": density,
        "doors": door_report,
        "mouth_high": mouth_high,
        "top_of_bay": top_of_bay,
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
    print("\n--- bay_kit : mesures relevees sur le .glb PRODUIT ---")
    print(f"  {'piece':<20} {'tri':>5}  {'bbox (l x h x L)':>24}")
    for name in PART_NAMES:
        s = report["parts"][name]
        print(f"  {name:<20} {s['triangles']:>5}  "
              f"{s['size'][0]:7.2f} x {s['size'][1]:5.2f} x {s['size'][2]:7.2f}")
    print(f"  {'TOTAL (kit unique)':<20} {report['triangles']:>5}")
    print(f"  hangar assemble (rail x2, traverse x2) : {report['assembled']} tri "
          f"/ {TRI_BUDGET_ASSEMBLED} ; sept hangars : {report['level']} "
          f"/ {TRI_BUDGET_LEVEL}")
    print(f"\n  ouverture {2 * OPEN_HALF_X:.2f} x {2 * OPEN_HALF_Z:.2f} m ; "
          f"puits {WELL_DEPTH:.2f} m ; coaming {COAM_H:.2f} m au-dessus, "
          f"jupe {COAM_SKIRT:.2f} m")
    print(f"  clair du puits a la bouche : "
          f"{2 * (OPEN_HALF_X - WALL_INSET):.2f} x "
          f"{2 * (OPEN_HALF_Z - WALL_INSET):.2f} m "
          f"(un chasseur de 1,8 x 2,5 m y tient pose sur les rails)")
    print(f"  bouche la plus haute des 7 baies {report['mouth_high']:+.3f} ; "
          f"coaming {report['mouth_high'] + COAM_H:+.3f} ; bloc de servitude "
          f"{report['top_of_bay']:+.3f} (plafond de construction "
          f"{cortege.BUILD_CEILING_Y:+.2f})")

    doors = report.get("doors") or {}
    if doors:
        print("\n  --- les deux battants (BRIEF-0095) ---")
        for name in ("bay_door_left", "bay_door_right"):
            d = doors[name]
            print(f"    {name:<16} {d['triangles']:>4} tri  "
                  f"x [{d['min'][0]:+.3f} ; {d['max'][0]:+.3f}]  "
                  f"y [{d['min'][1]:+.3f} ; {d['max'][1]:+.3f}]  "
                  f"z [{d['min'][2]:+.3f} ; {d['max'][2]:+.3f}]  "
                  f"volume {d['volume']:+.3f} m3")
        print(f"    paire : {doors['triangles']} tri / {TRI_BUDGET_DOORS} ; "
              f"epaisseur {doors['bay_door_left']['size'][1]:.3f} m (max 0,220) ; "
              f"plafond {doors['bay_door_left']['max'][1]:+.3f} (max +0,180)")
        c = doors["closure"]
        print(f"    fermeture : {c['holes']} cellule(s) de jour sur {c['cells']} "
              "rasterisees a 2 cm sur toute l'ouverture")
        print(f"    ouverts a {DOOR_SLIDE:.2f} m : le battant occupe "
              f"x [{-DOOR_SPAN_X - DOOR_SLIDE:+.2f} ; "
              f"{DOOR_TOOTH - DOOR_SLIDE:+.2f}] ; la face exterieure du coaming "
              f"est a {-OPEN_HALF_X - COAM_W:+.2f} -> "
              f"{DOOR_SPAN_X + DOOR_SLIDE - OPEN_HALF_X - COAM_W:.2f} m de "
              "battant reposent sur le borde (mesure pour le concepteur, "
              "l'animation est du moteur)")

    print(f"\n  primitives : {report['primitives'][0]}/{report['primitives'][2]} "
          f"TEXCOORD_0, {report['primitives'][1]}/{report['primitives'][2]} TANGENT")
    print("  densite de texels (valeurs singulieres, triangle par triangle), "
          f"cible {TEXELS_PER_METER:.3f} tuile/m ({1 / TEXELS_PER_METER:.2f} m/tuile)")
    for name in PART_NAMES:
        d = report["density"].get(name)
        if not d:
            continue
        print(f"    {name:<20} {d['tiles_per_m_min']:.3f} a "
              f"{d['tiles_per_m_max']:.3f}, moyenne {d['tiles_per_m_mean']:.3f} "
              f"t/m ({d['m_per_tile_mean']:.2f} m/tuile), aniso "
              f"{d['anisotropy_max']:.2f}")

    print("\n  repartition en AIRE, relevee sur le .glb — kit brut, hangar "
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
        print(f"    {name:<22} {raw:7.1f} m2 {100.0 * raw / total:5.1f} %  "
              f"{area:7.1f} m2 {100.0 * area / built_total:5.1f} %  "
              f"{seen:7.1f} m2 {100.0 * seen / seen_total:5.1f} %")
    print(f"    {'TOTAL':<22} {total:7.1f} m2          {built_total:7.1f} m2"
          f"          {seen_total:7.1f} m2")
    print(f"  octets     : {report['bytes']}")


def main() -> None:
    report = build()
    _print_report(report)
    if "--plate" in sys.argv:
        render_plate(report)
    if "--doors-plate" in sys.argv:
        render_doors_plate(report)


# ==========================================================================
# Planche de recette — `--plate`
# ==========================================================================
# ADR-0006 : un livrable de la forge n'est pas valide tant qu'il n'a pas ete
# rendu et REGARDE. La premiere vignette EST le test d'acceptation du brief :
# un hangar et une tourelle actuelle dans le MEME cadre, en noir et blanc,
# emissifs coupes. Deux vignettes separees ne prouveraient rien.

TILE_W = 1440
SCENE_H = 620
CLOSE_H = 620
ELEV_H = 380
UV_H = 420
SAMPLES = 32

BACKDROP = (0.012, 0.016, 0.035, 1.0)
AMBIENT = tuple(c * 0.8 for c in (0.55, 0.62, 0.78))
GAME_LIGHTS = (
    ("Key", Vector((0.329, -0.8192, -0.4698)), 1.55, (1.0, 0.976, 0.925)),
    ("Rim", Vector((-0.0819, -0.342, 0.9361)), 0.70, (0.596, 0.855, 1.0)),
    ("Fill", Vector((-0.4, -0.449, -0.799)), 0.55, (0.85, 0.91, 1.0)),
)
CAM_POS = cortege.CAM_POS
CAM_FORWARD = cortege.CAM_FORWARD
CAM_UP = cortege.CAM_UP
CAM_FOV_V = cortege.CAM_FOV_V

#: La paire qui sert de test d'acceptation : elles sont a 8 m l'une de l'autre,
#: du meme bord, donc dans le meme cadre a la camera du jeu — et sans se
#: recouvrir (0,25 m de contact entre le coaming et la levre du socle).
ACCEPTANCE_BAY = 7          # Bay_07, s = 436, x = -9,30
ACCEPTANCE_TURRET = 428.0   # Turret_14, s = 428, x = -9,40


def _to_blender(v: Vector) -> Vector:
    return Vector((v.x, -v.z, v.y))


def _plate_reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    world = bpy.data.worlds.new("plate")
    world.use_nodes = True
    tree = world.node_tree
    tree.nodes.clear()
    output = tree.nodes.new("ShaderNodeOutputWorld")
    mix = tree.nodes.new("ShaderNodeMixShader")
    path = tree.nodes.new("ShaderNodeLightPath")
    sky = tree.nodes.new("ShaderNodeBackground")
    ambient = tree.nodes.new("ShaderNodeBackground")
    sky.inputs[0].default_value = BACKDROP
    ambient.inputs[0].default_value = (*AMBIENT, 1.0)
    tree.links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
    tree.links.new(ambient.outputs[0], mix.inputs[1])
    tree.links.new(sky.outputs[0], mix.inputs[2])
    tree.links.new(mix.outputs[0], output.inputs[0])
    scene = bpy.context.scene
    scene.world = world
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"


def _plate_lights() -> None:
    for name, direction, energy, color in GAME_LIGHTS:
        data = bpy.data.lights.new(name, type="SUN")
        data.energy = energy * math.pi
        data.color = color
        data.angle = 0.0
        light = bpy.data.objects.new(name, data)
        light.rotation_euler = _to_blender(direction).to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(light)


def _plate_camera(name: str, position: Vector, forward: Vector, up: Vector,
                  fov: float, ortho: float | None = None) -> bpy.types.Object:
    data = bpy.data.cameras.new(name)
    data.lens_unit = "FOV"
    data.sensor_fit = "VERTICAL"
    data.angle_y = fov
    if ortho is not None:
        data.type = "ORTHO"
        data.ortho_scale = ortho
    data.clip_start = 0.02
    data.clip_end = 1600.0
    camera = bpy.data.objects.new(name, data)
    right = forward.cross(up).normalized()
    camera.matrix_world = Matrix((
        (right.x, up.x, -forward.x, position.x),
        (right.y, up.y, -forward.y, position.y),
        (right.z, up.z, -forward.z, position.z),
        (0.0, 0.0, 0.0, 1.0),
    ))
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    return camera


def _import(path: str, name: str, position: Vector, yaw: float = 0.0) -> list:
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    fresh = [o for o in bpy.context.scene.objects if o not in before]
    holder = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(holder)
    holder.location = _to_blender(position)
    holder.rotation_euler = Euler((0.0, 0.0, yaw), "XYZ")
    for obj in fresh:
        if obj.parent is None:
            obj.parent = holder
            obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.visible_shadow = False
    return fresh


def _assemble_bay(index: int, shift: float, blocks: bool = True,
                  doors: float | None = None) -> list:
    """Monte UN hangar sur la baie `index` (1-base), comme le fera le moteur.

    C'est la SEULE facon de juger le lot : la coque livre un trou, le kit livre
    sept pieces, et ni l'un ni l'autre ne prouve quoi que ce soit seul.
    """
    s, x = cortege.BAYS[index - 1]
    mouth, _ = cortege.bay_mouth_y(s, x)
    z = -s + shift
    placed: list = []
    plan = [
        ("bay_frame_left", Vector((x - OPEN_HALF_X, mouth, z)), 0.0),
        ("bay_frame_right", Vector((x + OPEN_HALF_X, mouth, z)), 0.0),
        ("bay_frame_top", Vector((x, mouth, z + OPEN_HALF_Z)), 0.0),
        ("bay_frame_top", Vector((x, mouth, z - OPEN_HALF_Z)), math.pi),
        ("bay_inner_wall", Vector((x, mouth, z)), 0.0),
        ("bay_floor", Vector((x, mouth - WELL_DEPTH, z)), 0.0),
        ("bay_launch_rail",
         Vector((x - RAIL_GAUGE * 0.5, mouth - WELL_DEPTH,
                 z - RAIL_LEN * 0.5)), 0.0),
        ("bay_launch_rail",
         Vector((x + RAIL_GAUGE * 0.5, mouth - WELL_DEPTH,
                 z - RAIL_LEN * 0.5)), 0.0),
    ]
    if blocks:
        side = 1.0 if x < 0.0 else -1.0
        plan += [
            ("bay_service_block",
             Vector((x + side * (OPEN_HALF_X + COAM_W * 0.5), mouth + COAM_H,
                     z + 2.6)), 0.0),
            ("bay_service_block",
             Vector((x + side * (OPEN_HALF_X + COAM_W * 0.5), mouth + COAM_H,
                     z - 2.6)), math.pi),
        ]
    if doors is not None:
        # Les battants montent a leur point d'assemblage, et la course du moteur
        # n'est qu'une TRANSLATION de ce point : c'est tout le contrat.
        plan += [
            ("bay_door_left", Vector((x - doors, mouth, z)), 0.0),
            ("bay_door_right", Vector((x + doors, mouth, z)), 0.0),
        ]
    for name, position, yaw in plan:
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
            placed.append(obj)
    return placed


#: Luminance des slots, pour la vignette en noir et blanc. On garde la VALEUR
#: (c'est ce que « noir et blanc » veut dire) et l'on coupe l'emission.
def _grey_material(name: str) -> bpy.types.Material:
    palette = ak.PALETTES[ak.FACTION_NULL_CHOIR]
    hexes = {
        "AA_Hull": palette["hull"], "AA_Panel": palette["panel"],
        "AA_Trim": palette["trim"], "AA_Greeble": palette["greeble"],
        "AA_Glass": palette["glass"], "AA_Emissive_Engine": palette["emissive"],
        "AA_Marking_Red": palette["marking"],
        "AA_Hull_Ambry": ak.PALETTES[ak.FACTION_VANGUARD]["hull"],
    }
    key = name.split(".")[0]
    linear = ak.srgb_hex_to_linear(hexes.get(key, "#808080"))
    value = 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    material = bpy.data.materials.new("grey_" + key)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (value, value, value, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.0
    out = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(bsdf.outputs[0], out.inputs[0])
    return material


def _to_greyscale(objects: list) -> None:
    """Noir et blanc, EMISSIFS COUPES — le test d'acceptation du brief.

    Ce n'est pas un effet de style : c'est ce qui retire a la geometrie toute
    aide de couleur et de lumiere. S'il faut le magenta pour distinguer un hangar
    d'une tourelle, la silhouette ne fait pas son travail.
    """
    cache: dict[str, bpy.types.Material] = {}
    for obj in objects:
        if obj.type != "MESH":
            continue
        for slot in obj.material_slots:
            if slot.material is None:
                continue
            key = slot.material.name.split(".")[0]
            if key not in cache:
                cache[key] = _grey_material(key)
            slot.material = cache[key]


def _checker_material() -> bpy.types.Material:
    mat = bpy.data.materials.new("UV_Checker")
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    coord = tree.nodes.new("ShaderNodeTexCoord")
    fine = tree.nodes.new("ShaderNodeTexChecker")
    fine.inputs["Scale"].default_value = 16.0
    fine.inputs["Color1"].default_value = (0.62, 0.62, 0.64, 1.0)
    fine.inputs["Color2"].default_value = (0.16, 0.16, 0.18, 1.0)
    coarse = tree.nodes.new("ShaderNodeTexChecker")
    coarse.inputs["Scale"].default_value = 1.0
    coarse.inputs["Color1"].default_value = (1.0, 0.86, 0.55, 1.0)
    coarse.inputs["Color2"].default_value = (0.55, 0.72, 1.0, 1.0)
    mix = tree.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 1.0
    bsdf = tree.nodes.new("ShaderNodeBsdfDiffuse")
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(coord.outputs["UV"], fine.inputs["Vector"])
    tree.links.new(coord.outputs["UV"], coarse.inputs["Vector"])
    tree.links.new(fine.outputs["Color"], mix.inputs["Color1"])
    tree.links.new(coarse.outputs["Color"], mix.inputs["Color2"])
    tree.links.new(mix.outputs["Color"], bsdf.inputs["Color"])
    tree.links.new(bsdf.outputs[0], out.inputs[0])
    return mat


def _apply_checker(objects: list) -> None:
    checker = _checker_material()
    for obj in objects:
        if obj.type != "MESH":
            continue
        obj.data.materials.clear()
        obj.data.materials.append(checker)


def _label(camera, text: str, u: float, v: float, height: float,
           width: int, tile_height: int, color=(1.0, 1.0, 1.0)) -> None:
    curve = bpy.data.curves.new(text, type="FONT")
    curve.body = text
    obj = bpy.data.objects.new("label_" + text[:14], curve)
    material = bpy.data.materials.new("label_" + text[:14])
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs[0].default_value = (*color, 1.0)
    emission.inputs[1].default_value = 4.0
    out = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(emission.outputs[0], out.inputs[0])
    obj.data.materials.append(material)
    obj.parent = camera
    depth = 1.0
    if camera.data.type == "ORTHO":
        half_h = camera.data.ortho_scale * 0.5
    else:
        half_h = math.tan(camera.data.angle_y * 0.5) * depth
    half_w = half_h * width / tile_height
    curve.size = height * 2.0 * half_h
    obj.location = (u * half_w, v * half_h, -depth)
    obj.visible_shadow = False
    bpy.context.collection.objects.link(obj)


def _render(path: str, width: int, height: int) -> None:
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def _game_shift(aim_s: float) -> float:
    """Decalage du decor pour que la station `aim_s` tombe au centre du champ."""
    depth = (cortege.CAM_POS.y - (-4.30)) / -cortege.CAM_FORWARD.y
    return aim_s + cortege.CAM_POS.z + cortege.CAM_FORWARD.z * depth


def _tile_acceptance(path: str, report: dict, greyscale: bool) -> None:
    """LE TEST D'ACCEPTATION : un hangar et une tourelle dans le MEME cadre.

    « En noir et blanc, tous emissifs coupes, on doit distinguer immediatement un
    hangar d'une tourelle. » Le meme cadre est rendu deux fois — en valeurs, puis
    en couleur — pour que l'on voie du meme coup ce que la silhouette fait seule
    et ce que l'emissif AJOUTE. S'il fallait la couleur, la premiere image le
    dirait.
    """
    _plate_reset()
    shift = _game_shift(0.5 * (cortege.BAYS[ACCEPTANCE_BAY - 1][0]
                               + ACCEPTANCE_TURRET))
    decor = _import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    parts = _assemble_bay(ACCEPTANCE_BAY, shift)
    fighter = _import(FIGHTER, "Player", Vector((0.0, 0.0, 3.4)))
    if greyscale:
        _to_greyscale(decor + parts + fighter)
    _plate_lights()
    camera = _plate_camera("game", _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                           _to_blender(CAM_UP), CAM_FOV_V)
    if greyscale:
        _label(camera, "TEST D'ACCEPTATION — NOIR ET BLANC, EMISSIFS COUPES : "
                       "hangar (Bay_07) et tourelle (Turret_14) dans le meme cadre",
               -0.97, 0.88, 0.040, TILE_W, SCENE_H, (1.0, 0.88, 0.55))
        _label(camera, "la silhouette seule doit trancher : cadre rectangulaire "
                       "creux de 7,60 x 10,10 m contre disque plein de 6,40 m",
               -0.97, 0.79, 0.031, TILE_W, SCENE_H)
    else:
        _label(camera, "LE MEME CADRE, EN COULEUR — ce que l'emissif AJOUTE a une "
                       "fonction deja lisible en geometrie",
               -0.97, 0.88, 0.040, TILE_W, SCENE_H, (1.0, 0.88, 0.55))
        _label(camera, "trois bandes et rien d'autre : liseré sous la levre, pied "
                       "de paroi, filets de rail. JAMAIS le fond entier.",
               -0.97, 0.79, 0.031, TILE_W, SCENE_H)
    _label(camera, "camera de graybox.tscn sans retouche (0, 14, 5), FOV 62, "
                   "70 deg sous l'horizontale ; Specter-9 reel a sa place de jeu",
           -0.97, -0.91, 0.029, TILE_W, SCENE_H, (0.72, 0.84, 1.0))
    _render(path, TILE_W, SCENE_H)


def _tile_close(path: str, report: dict) -> None:
    """Le puits de pres, avec le Specter-9 POSE SUR LES RAILS.

    Regle 4 de la planche : « l'appareil est visible avant le decollage ». Elle
    ne se demontre pas par une cote, elle se regarde. On voit du meme coup que le
    puits est FERME — aucun morceau de l'interieur creux de la coque n'apparait.
    """
    _plate_reset()
    s, x = cortege.BAYS[ACCEPTANCE_BAY - 1]
    mouth, _ = cortege.bay_mouth_y(s, x)
    shift = _game_shift(s)
    _import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    _assemble_bay(ACCEPTANCE_BAY, shift)
    # Le chasseur est POSE dans le puits, sur les rails : c'est la position du
    # premier temps de la sequence de decollage (« appareil au repos »).
    _import(FIGHTER, "Docked",
            Vector((x, mouth - WELL_DEPTH + 0.42, -s + shift)))
    _plate_lights()
    eye = Vector((x + 5.6, mouth + 9.0, -s + shift + 7.4))
    target = Vector((x, mouth - 0.6, -s + shift))
    forward = (target - eye).normalized()
    up = forward.cross(Vector((1.0, 0.0, 0.0))).cross(forward).normalized()
    camera = _plate_camera("close", _to_blender(eye), _to_blender(forward),
                           _to_blender(up), math.radians(46.0))
    _label(camera, "LE PUITS DE PRES — un chasseur POSE SUR LES RAILS, visible "
                   "avant le decollage (regle 4)",
           -0.97, 0.89, 0.038, TILE_W, CLOSE_H, (1.0, 0.88, 0.55))
    _label(camera, f"clair a la bouche {2 * (OPEN_HALF_X - WALL_INSET):.2f} x "
                   f"{2 * (OPEN_HALF_Z - WALL_INSET):.2f} m, fond a "
                   f"{WELL_DEPTH:.2f} m sous la peau ; le puits est FERME — "
                   "aucun morceau de l'interieur creux n'apparait",
           -0.97, 0.80, 0.029, TILE_W, CLOSE_H)
    _render(path, TILE_W, CLOSE_H)


def _plane_slab(y: float, half_x: float, half_z: float, thickness: float,
                color: tuple[float, float, float], strength: float,
                centre_z: float = 0.0) -> None:
    """Un plan de reference materialise POUR LA SEULE PLANCHE.

    Une dalle et non un plan : vu de face, une surface d'epaisseur nulle ne rend
    aucun pixel. Rien de tout cela ne part dans le `.glb`.
    """
    bm = bmesh.new()
    corners = ((-half_x, centre_z - half_z), (half_x, centre_z - half_z),
               (half_x, centre_z + half_z), (-half_x, centre_z + half_z))
    rings = []
    for level in (y - thickness, y):
        rings.append([bm.verts.new(_to_blender(Vector((x, level, z))))
                      for x, z in corners])
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[1])))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
    mesh = bpy.data.meshes.new("slab")
    material = bpy.data.materials.new("slab")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs[0].default_value = (*color, 1.0)
    emission.inputs[1].default_value = strength
    out = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(emission.outputs[0], out.inputs[0])
    mesh.materials.append(material)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("slab", mesh)
    obj.visible_shadow = False
    obj.visible_diffuse = False
    obj.visible_glossy = False
    obj.visible_transmission = False
    bpy.context.collection.objects.link(obj)


def _tile_elevation(path: str, report: dict) -> None:
    """LE KIT SEUL, DE FACE, avec les trois plans qui decident de tout.

    La coque en est absente et c'est le seul moyen de repondre a la question du
    brief autrement que par un chiffre : la profondeur demandee (1,5 a 2,5 m)
    n'existe qu'en descendant SOUS la peau, puisqu'il n'y a que 1,1 m entre elle
    et le plafond du plan de jeu. On voit les trois plans, on voit ou est le
    fond, et l'on voit que le coaming ne touche pas le plafond.
    """
    _plate_reset()
    s, x = cortege.BAYS[ACCEPTANCE_BAY - 1]
    mouth, low = cortege.bay_mouth_y(s, x)
    # Le hangar est monte a l'origine : Y = 0 est le plan de la peau.
    for name, position, yaw in (
            ("bay_frame_left", Vector((-OPEN_HALF_X, 0.0, 0.0)), 0.0),
            ("bay_frame_right", Vector((OPEN_HALF_X, 0.0, 0.0)), 0.0),
            ("bay_frame_left", Vector((-OPEN_HALF_X, 0.0, 0.0)), 0.0),
            ("bay_frame_right", Vector((OPEN_HALF_X, 0.0, 0.0)), 0.0),
            ("bay_frame_top", Vector((0.0, 0.0, OPEN_HALF_Z)), 0.0),
            ("bay_frame_top", Vector((0.0, 0.0, -OPEN_HALF_Z)), math.pi),
            ("bay_inner_wall", Vector((0.0, 0.0, 0.0)), 0.0),
            ("bay_floor", Vector((0.0, -WELL_DEPTH, 0.0)), 0.0),
            ("bay_launch_rail",
             Vector((-RAIL_GAUGE * 0.5, -WELL_DEPTH, -RAIL_LEN * 0.5)), 0.0),
            ("bay_launch_rail",
             Vector((RAIL_GAUGE * 0.5, -WELL_DEPTH, -RAIL_LEN * 0.5)), 0.0),
            ("bay_service_block",
             Vector((-OPEN_HALF_X - COAM_W * 0.5, COAM_H, 2.6)), 0.0)):
        before = set(bpy.context.scene.objects)
        bpy.ops.import_scene.gltf(filepath=OUTPUT)
        fresh = [o for o in bpy.context.scene.objects if o not in before]
        for obj in fresh:
            if obj.name.split(".")[0] != name:
                bpy.data.objects.remove(obj, do_unlink=True)
                continue
            obj.location = _to_blender(position)
            obj.rotation_euler = Euler((0.0, 0.0, yaw), "XYZ")
            obj.visible_shadow = False
    # Les trois plans : la peau (ambre), le plafond du jeu (rouge), le fond.
    # ⚠️ TROIS PLANS DE REFERENCE, et le troisieme est coupe en deux pour
    # tomber A COTE du hangar : une elevation de face ne montre pas le fond d'un
    # puits, mais elle peut montrer OU il est. Aucun cyan, aucun corail : ces
    # deux couleurs appartiennent aux tirs, meme dans une planche.
    _plane_slab(0.0, 0.02, 9.4, 0.10, (0.95, 0.72, 0.28), 2.0)
    _plane_slab(cortege.CEILING_Y - mouth, 0.02, 9.4, 0.10, (0.90, 0.32, 0.26), 2.0)
    for side in (-1.0, 1.0):
        _plane_slab(-WELL_DEPTH, 0.02, 2.1, 0.10, (0.72, 0.86, 0.60), 2.0,
                    centre_z=side * 7.3)
    _plate_lights()
    camera = _plate_camera(
        "elev", _to_blender(Vector((34.0, -0.45, 0.0))),
        _to_blender(Vector((-1.0, 0.0, 0.0))), _to_blender(Vector((0.0, 1.0, 0.0))),
        math.radians(30.0), ortho=5.2)
    _label(camera, "LE KIT SEUL, ELEVATION DE TRIBORD (proue a droite) — peau "
                   "(ambre) 0,00 ; coaming +0,60 ; "
                   f"fond (vert) -{WELL_DEPTH:.2f} ; plafond du jeu (rouge) "
                   f"{cortege.CEILING_Y - mouth:+.2f}",
           -0.985, 0.86, 0.052, TILE_W, ELEV_H, (1.0, 0.88, 0.55))
    _label(camera, f"la profondeur demandee (1,5 a 2,5 m) n'existe qu'ICI, SOUS "
                   f"la peau : il n'y a que {cortege.CEILING_Y - mouth:.2f} m "
                   f"au-dessus. Denivele du pourtour {mouth - low:.2f} m, absorbe "
                   f"par la jupe de {COAM_SKIRT:.2f} m.",
           -0.985, -0.88, 0.042, TILE_W, ELEV_H)
    _render(path, TILE_W, ELEV_H)


def _tile_top(path: str, report: dict) -> None:
    """Le troncon 5 de dessus : sept trous dans une coque, pas sept boutons."""
    _plate_reset()
    _import(HULL, "Decor", Vector((0.0, 0.0, 0.0)))
    for index in (7,):
        _assemble_bay(index, 0.0)
    _plate_lights()
    centre = -(cortege.BAYS[ACCEPTANCE_BAY - 1][0])
    camera = _plate_camera(
        "top", _to_blender(Vector((0.0, 60.0, centre))),
        _to_blender(Vector((0.0, -1.0, 0.0))), _to_blender(Vector((-1.0, 0.0, 0.0))),
        math.radians(30.0), ortho=28.05)
    _label(camera, "VUE DE DESSUS — Bay_07 monte, Turret_14 a sa gauche ; "
                   "l'ouverture est PERCEE dans la peau, pas posee dessus",
           -0.985, 0.84, 0.062, TILE_W, ELEV_H, (1.0, 0.88, 0.55))
    _label(camera, f"{report['assembled']} tri par hangar assemble "
                   f"({report['level']} pour les sept, budget "
                   f"{TRI_BUDGET_LEVEL})",
           -0.985, -0.88, 0.048, TILE_W, ELEV_H)
    _label(camera, "proue", -0.985, 0.52, 0.055, TILE_W, ELEV_H, (0.72, 0.84, 1.0))
    _render(path, TILE_W, ELEV_H)


def _tile_uv(path: str, report: dict) -> None:
    _plate_reset()
    shift = _game_shift(cortege.BAYS[ACCEPTANCE_BAY - 1][0])
    decor = _import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    parts = _assemble_bay(ACCEPTANCE_BAY, shift)
    _apply_checker(decor + parts)
    _plate_lights()
    camera = _plate_camera("uv", _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                           _to_blender(CAM_UP), CAM_FOV_V)
    d = report["density"]["bay_inner_wall"]
    _label(camera, "DAMIER UV — grande case = 1 tuile de 5,00 m, petite = 62,5 cm ; "
                   "la MEME echelle sur la coque et sur le kit",
           -0.97, 0.88, 0.038, TILE_W, UV_H, (1.0, 0.88, 0.55))
    _label(camera, f"projection en boite {TEXELS_PER_METER:.3f} tuile/m ; "
                   f"anisotropie max mesuree sur la paroi {d['anisotropy_max']:.2f} "
                   f"(borne theorique de la methode : 1,73)",
           -0.97, 0.78, 0.030, TILE_W, UV_H)
    _render(path, TILE_W, UV_H)


def _compose(tiles: list[tuple[str, int]], out: str) -> None:
    import numpy as np

    height = sum(h for _, h in tiles)
    sheet = np.zeros((height, TILE_W, 4), dtype=np.float32)
    sheet[..., 3] = 1.0
    cursor = 0
    for path, tile_h in tiles:
        image = bpy.data.images.load(path)
        buffer = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(buffer)
        tile = buffer.reshape(tile_h, TILE_W, 4)
        top = height - cursor - tile_h
        sheet[top:top + tile_h] = tile
        cursor += tile_h
        bpy.data.images.remove(image)
    result = bpy.data.images.new("sheet", width=TILE_W, height=height)
    result.pixels.foreach_set(sheet.reshape(-1))
    result.filepath_raw = out
    result.file_format = "PNG"
    result.save()
    bpy.data.images.remove(result)
    print(f"-> {out}  ({TILE_W} x {height})")


# ==========================================================================
# Planche des battants — `--doors-plate` (BRIEF-0095)
# ==========================================================================
# Quatre vues, et deux d'entre elles ne sont pas negociables : une FERMEE et une
# OUVERTE A 3,00 m. La seconde est la seule qui reponde a la question que le
# brief pose vraiment — ou finit un battant de 3,00 m qu'on retire de 3,00 m.

DOORS_PLATE = os.path.join(_REPO, "docs/forge/output/BRIEF-0095-planche-portes.png")
GAME_H = 640
TOP_H = 900
FRONT_H = 620


def _tile_doors_game(path: str, opening: float, title: str, note: str) -> None:
    """Le hangar a la CAMERA DU JEU, portes fermees ou ouvertes.

    C'est le seul cadrage qui juge : le battant fait 3,00 x 8,50 m et sera vu a
    23 px/m, de trois quarts, sept fois dans le niveau. Une belle vue de trois
    quarts a 2 m ne prouverait rien du tout (ADR-0006).
    """
    _plate_reset()
    s, x = cortege.BAYS[ACCEPTANCE_BAY - 1]
    shift = _game_shift(s)
    _import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    _assemble_bay(ACCEPTANCE_BAY, shift, doors=opening)
    _import(FIGHTER, "Player", Vector((0.0, 0.0, 3.4)))
    _plate_lights()
    camera = _plate_camera("game", _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                           _to_blender(CAM_UP), CAM_FOV_V)
    _label(camera, title, -0.97, 0.89, 0.036, TILE_W, GAME_H, (1.0, 0.88, 0.55))
    _label(camera, note, -0.97, 0.81, 0.026, TILE_W, GAME_H)
    _label(camera, "camera de graybox.tscn sans retouche (0, 14, 5), FOV 62, "
                   "70 deg sous l'horizontale ; Specter-9 reel a sa place",
           -0.97, -0.92, 0.024, TILE_W, GAME_H, (0.72, 0.84, 1.0))
    _render(path, TILE_W, GAME_H)


def _pose_kit(plan: list[tuple[str, Vector, float]]) -> None:
    """Pose des pieces du kit a l'origine (planches hors coque)."""
    for name, position, yaw in plan:
        before = set(bpy.context.scene.objects)
        bpy.ops.import_scene.gltf(filepath=OUTPUT)
        for obj in [o for o in bpy.context.scene.objects if o not in before]:
            if obj.name.split(".")[0] != name:
                bpy.data.objects.remove(obj, do_unlink=True)
                continue
            obj.location = _to_blender(position)
            obj.rotation_euler = Euler((0.0, 0.0, yaw), "XYZ")
            obj.visible_shadow = False


def _tile_doors_top(path: str, report: dict) -> None:
    """LE DESSUS, PORTES FERMEES — la denture, les caissons, le chevron.

    Elle repond au reproche mot pour mot : « on dirait des jeux faits avec des
    formes carrees ». Deux dalles y feraient un rectangle coupe en deux par un
    trait droit ; ici la ligne de fermeture est dentee, chaque battant porte
    trois caissons en creux dont la levre interieure dessine une pointe vers le
    cote ou il se retire, et une poutre de nez le borde.
    """
    _plate_reset()
    _pose_kit([
        ("bay_frame_left", Vector((-OPEN_HALF_X, 0.0, 0.0)), 0.0),
        ("bay_frame_right", Vector((OPEN_HALF_X, 0.0, 0.0)), 0.0),
        ("bay_frame_top", Vector((0.0, 0.0, OPEN_HALF_Z)), 0.0),
        ("bay_frame_top", Vector((0.0, 0.0, -OPEN_HALF_Z)), math.pi),
        ("bay_inner_wall", Vector((0.0, 0.0, 0.0)), 0.0),
        ("bay_floor", Vector((0.0, -WELL_DEPTH, 0.0)), 0.0),
        ("bay_door_left", Vector((0.0, 0.0, 0.0)), 0.0),
        ("bay_door_right", Vector((0.0, 0.0, 0.0)), 0.0),
    ])
    _plate_lights()
    camera = _plate_camera(
        "doors_top", _to_blender(Vector((0.0, 40.0, 0.0))),
        _to_blender(Vector((0.0, -1.0, 0.0))), _to_blender(Vector((1.0, 0.0, 0.0))),
        math.radians(30.0), ortho=8.6)
    d = report["doors"]
    _label(camera, "LE DESSUS, PORTES FERMEES — ligne de fermeture DENTEE, "
                   "3 dents par battant",
           -0.985, 0.92, 0.034, TILE_W, TOP_H, (1.0, 0.88, 0.55))
    _label(camera, "trois caissons en creux par battant ; leur levre interieure "
                   "s'ecarte au milieu : le chevron dit de quel cote il part",
           -0.985, 0.86, 0.024, TILE_W, TOP_H)
    _label(camera, f"{d['triangles']} tri pour la paire (budget "
                   f"{TRI_BUDGET_DOORS}) ; {d['closure']['holes']} cellule de "
                   f"jour sur {d['closure']['cells']} rasterisees a 2 cm",
           -0.985, -0.92, 0.024, TILE_W, TOP_H, (0.72, 0.84, 1.0))
    _label(camera, "proue ->", 0.72, 0.72, 0.028, TILE_W, TOP_H, (0.72, 0.84, 1.0))
    _label(camera, "il part vers -X", -0.985, -0.62, 0.028, TILE_W, TOP_H,
           (0.72, 0.84, 1.0))
    _render(path, TILE_W, TOP_H)


def _tile_doors_front(path: str, report: dict) -> None:
    """VUE DE PROUE — bâbord FERME, tribord OUVERT a 3,00 m, dans le meme cadre.

    Deux images separees ne prouveraient rien : c'est la comparaison qui montre
    d'un coup que le battant ferme passe SOUS la levre du coaming (0,175 contre
    0,60) et ou il finit une fois retire.

    ⚠️ OBLIQUE ET NON ORTHOGRAPHIQUE, ET C'EST UNE CORRECTION DE PLANCHE. Une
    elevation stricte a ete rendue d'abord : sur une vignette large de 1 440 px
    il faut 13 m de champ pour tenir la course, ce qui donne 20 px a un battant
    de 0,175 m — l'objet meme de la vignette devenait un cheveu, et le puits noir
    occupait tout le reste. A 25 deg au-dessus de l'horizontale et en longue
    focale, l'epaisseur, la levre et le debord se voient tous les trois. Plus
    rasant que cela, le speculaire lave toutes les valeurs et la piece devient
    blanche : mesure faite a 18 deg. Les traverses avant et arriere sont
    volontairement absentes — elles masqueraient tout.
    """
    _plate_reset()
    _pose_kit([
        ("bay_frame_left", Vector((-OPEN_HALF_X, 0.0, 0.0)), 0.0),
        ("bay_frame_right", Vector((OPEN_HALF_X, 0.0, 0.0)), 0.0),
        ("bay_inner_wall", Vector((0.0, 0.0, 0.0)), 0.0),
        ("bay_floor", Vector((0.0, -WELL_DEPTH, 0.0)), 0.0),
        ("bay_launch_rail",
         Vector((-RAIL_GAUGE * 0.5, -WELL_DEPTH, -RAIL_LEN * 0.5)), 0.0),
        ("bay_launch_rail",
         Vector((RAIL_GAUGE * 0.5, -WELL_DEPTH, -RAIL_LEN * 0.5)), 0.0),
        ("bay_door_left", Vector((0.0, 0.0, 0.0)), 0.0),
        ("bay_door_right", Vector((DOOR_SLIDE, 0.0, 0.0)), 0.0),
    ])
    # ⚠️ AUCUNE DALLE DE REFERENCE ICI. Elles ont ete essayees : a 18 deg, deux
    # plans distants de 18 cm sont deux traits confondus, et ils masquent le
    # dessus des battants qu'ils sont censes coter. Le rapport de hauteur se lit
    # tout seul — le battant contre la levre du coaming, 0,175 contre 0,60.
    _plate_lights()
    # Longue focale et recul : le coaming court sur 10 m en Z, et de pres il
    # remplit le cadre a lui seul.
    eye = Vector((1.2, 16.0, 34.0))
    target = Vector((1.2, 0.55, 0.0))
    forward = (target - eye).normalized()
    # ⚠️ LE « HAUT » SE CALCULE PAR PROJECTION, PAS PAR DEUX PRODUITS VECTORIELS
    # SUR X. Le motif `forward.cross(X).cross(forward)` employe ailleurs dans ce
    # fichier ne marche que pour une visee qui a une composante en X : ici, la
    # visee est dans le plan (Y, Z) et il rend exactement l'axe X — la camera
    # sort roulee d'un quart de tour, avec le champ vertical applique en travers.
    # Rien dans le rendu ne dit « roule » : on n'y voit qu'un cadrage etrange.
    world_up = Vector((0.0, 1.0, 0.0))
    up = (world_up - forward * forward.dot(world_up)).normalized()
    camera = _plate_camera("doors_front", _to_blender(eye), _to_blender(forward),
                           _to_blender(up), math.radians(11.6))
    door = report["doors"]["bay_door_left"]
    _label(camera, "VUE DE PROUE (25 deg, longue focale) — bâbord FERME, "
                   f"tribord OUVERT A {DOOR_SLIDE:.2f} m, meme cadre",
           -0.985, 0.88, 0.044, TILE_W, FRONT_H, (1.0, 0.88, 0.55))
    _label(camera, f"dessus mesure {door['max'][1]:+.3f} (plafond du brief "
                   f"+0,180) ; epaisseur {door['size'][1]:.3f} (max 0,220) ; "
                   "levre du coaming +0,60 — il passe DESSOUS",
           -0.985, 0.79, 0.030, TILE_W, FRONT_H)
    _label(camera, f"ouvert, il occupe |x| de {OPEN_HALF_X:.2f} a "
                   f"{DOOR_SPAN_X + DOOR_SLIDE:.2f} : "
                   f"{DOOR_SPAN_X + DOOR_SLIDE - OPEN_HALF_X - COAM_W:.2f} m "
                   f"passent la face exterieure du coaming "
                   f"({OPEN_HALF_X + COAM_W:.2f}) et reposent sur le borde",
           -0.985, -0.88, 0.030, TILE_W, FRONT_H, (0.72, 0.84, 1.0))
    _render(path, TILE_W, FRONT_H)


def render_doors_plate(report: dict) -> None:
    staging = tempfile.mkdtemp(prefix="aegis-baydoors-")
    tiles: list[tuple[str, int]] = []
    try:
        path = os.path.join(staging, "shut.png")
        _tile_doors_game(
            path, 0.0,
            "PONT FERME — le puits ne fuit AUCUNE lueur",
            "c'est le contraste noir puis magenta qui fait lire l'ouverture ; "
            "un pont abattu reste ferme, et cela se lit sans un mot")
        tiles.append((path, GAME_H))
        path = os.path.join(staging, "open.png")
        _tile_doors_game(
            path, DOOR_SLIDE,
            f"PONT OUVERT A {DOOR_SLIDE:.2f} m — la course reelle du moteur",
            "la lueur apparait ; le trait de bordure passe sous le coaming, et "
            "2,20 m de battant retire reposent sur le borde")
        tiles.append((path, GAME_H))
        path = os.path.join(staging, "top.png")
        _tile_doors_top(path, report)
        tiles.append((path, TOP_H))
        path = os.path.join(staging, "front.png")
        _tile_doors_front(path, report)
        tiles.append((path, FRONT_H))
        os.makedirs(os.path.dirname(DOORS_PLATE), exist_ok=True)
        _compose(tiles, DOORS_PLATE)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


def render_plate(report: dict) -> None:
    staging = tempfile.mkdtemp(prefix="aegis-baykit-plate-")
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
        path = os.path.join(staging, "top.png")
        _tile_top(path, report)
        tiles.append((path, ELEV_H))
        path = os.path.join(staging, "elev.png")
        _tile_elevation(path, report)
        tiles.append((path, ELEV_H))
        path = os.path.join(staging, "uv.png")
        _tile_uv(path, report)
        tiles.append((path, UV_H))
        os.makedirs(os.path.dirname(PLATE), exist_ok=True)
        _compose(tiles, PLATE)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


if __name__ == "__main__":
    main()
