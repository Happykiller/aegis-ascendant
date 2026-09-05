"""build_turret_kit.py — le kit d'affut de tourelle du Long Cortege (BRIEF-0093).

    blender-aegis -b -P tools/blender/build_turret_kit.py
    blender-aegis -b -P tools/blender/build_turret_kit.py -- --plate
    ./scripts/build-hull.sh --check turret_kit       # + controle de determinisme

Produit `assets/imported/models/backgrounds/turret_kit.glb` et, avec `--plate`,
la planche de recette `docs/forge/output/BRIEF-0093-planche-tourelles.png`.

Le script EST la source (ADR-0008) : aucun `.blend` versionne, aucun alea, deux
executions successives rendent le meme sha256.


CE QUE CE FICHIER EST, ET CE QU'IL N'EST PAS
============================================
Ce n'est PAS une tourelle. C'est un KIT de huit pieces, chacune modelisee dans
SON repere, origine au point d'assemblage. Le moteur les instancie et les
compose : c'est lui qui fait DIX-SEPT tourelles differentes a partir d'un seul
kit. La coque, elle, ne porte plus aucun socle cuit (`build_turret_pad()` a
disparu de `build_long_cortege.py`, BRIEF-0093) — elle ne porte que le marqueur.

    turret_pad            socle ancre        origine : centre, Y = assise
    turret_anchor_skirt   jupe d'ancrage     origine : centre, Y = assise
    turret_ring           couronne DE ROTATION  origine : centre, SUR SON AXE
    turret_body           bloc canon blinde  origine : centre, sur l'axe
    turret_barrel         UN tube de 2,90 m  origine : la culasse
    turret_barrel_short   UN tube de 2,20 m  origine : la culasse
    turret_service_box    coffret technique  origine : sa base
    turret_pipe           faisceau de conduites  origine : sa base


LA REGLE QUI PRIME SUR TOUT LE RESTE
====================================
« La structure doit etre identifiable par sa seule SILHOUETTE, avec au plus 6-8
primitives principales. Les emissifs ne servent qu'a renforcer une fonction deja
lisible en geometrie. »

La tourelle assemblee en compte SIX :

    1. le socle, disque tres aplati a bourrelet chanfreine
    2. la couronne, cylindre bas ENFONCE dans le socle
    3. le bloc blinde, parallelepipede trapu a chanfreins
    4. et 5. les DEUX canons, paralleles, qui debordent de 1,92 m du socle
    6. l'appareillage — coffrets et conduites, sur le plateau du socle

Le test d'acceptation du brief est le meme que celui de BRIEF-0091, pris par
l'autre bout : en noir et blanc, emissifs coupes, un HANGAR est un cadre creux et
une TOURELLE est un canon. Ce qui les separe n'est ni la couleur ni la lumiere,
c'est que l'un CREUSE et que l'autre DEPASSE.


⚠️ LE POINT MECANIQUE QUI NE SE VOIT PAS SUR UNE PLANCHE
========================================================
`turret_ring` — et tout ce qui est monte dessus — tourne autour de l'axe Y, EN UN
BLOC, a 42 deg/s (`cortege_turret.gd`). Si l'origine de la couronne n'est pas
exactement sur son axe de rotation, la tourelle balaie en decrivant un cercle au
lieu de pivoter sur place, et ça ne se voit qu'en jeu, EN MOUVEMENT.

Ce n'est donc pas laisse a l'appreciation : `_assert_on_axis()` relit le BINAIRE
et verifie, sur `turret_ring` et sur `turret_body`, que le centroide des sommets
et la boite englobante sont centres sur (0, ·, 0) au micron. Les deux echouent le
build.


⚠️ OU LE BUDGET A ETE DEPENSE, ET OU IL NE L'A PAS ETE
======================================================
Le budget est LARGE et c'est delibere : 55 000 triangles pour dix-sept tourelles,
soit ~3 200 par tourelle assemblee, dix fois ce qu'a coute un hangar. Mais large
ne veut pas dire fin : le post-traitement retro rend a 960x540, soit 23 px/m sur
la coque, et toute geometrie plus fine que 9 cm est moyennee puis disparait.
Mesure a nos depens sur la coque texturee : -33 pct de luminance pour un relief
qu'on ne voyait plus.

Le budget est donc alle a QUATRE choses, et a rien d'autre :

  * LES CHANFREINS SUR LES GRANDES ARETES. Ils accrochent la lumiere cle a
    n'importe quelle resolution — c'est la seule depense qui ne s'evapore pas au
    downscale. Toutes les aretes verticales du bloc et des coffrets sont coupees
    a 22 cm, tous les bords horizontaux par un anneau en retrait.
  * LA PROFONDEUR REELLE. La couronne est ENFONCEE de 16 cm dans la cuvette du
    socle ; les canons sont LOGES dans un masque creuse de 12 cm. Un creux se lit
    par son ombre portee, qui survit au downscale ; un rivet non.
  * LA SILHOUETTE. Ce qui depasse (les tubes, 1,92 m au-dela du socle) et ce qui
    creuse (la cuvette, le masque).
  * LA VARIETE. Deux longueurs de canon, une jupe optionnelle, un ecartement et
    des angles d'appareillage libres.

Rien n'a ete depense en rivets, en vis, en grilles ni en petits reliefs. Les
revolutions sont a 24 segments (socle, couronne) et 16 (tubes) : a 23 px/m le
contour est identique a 64.


L'ECHELLE DE DEPLIAGE — POURQUOI 0,200 ET PAS PLUS FIN
======================================================
Le kit partage les slots du borde (`AA_Hull`, `AA_Greeble`, `AA_Trim`,
`AA_Emissive_Engine`). Deux echelles de depliage sur un MEME slot, c'est la faute
qu'a corrigee BRIEF-0090 sur Ambry : la carte sortirait au bon grain sur la coque
et au mauvais sur la tourelle, cote a cote. Le kit est donc deplie a la densite du
borde — 0,200 tuile/m, 5,00 m par tuile — comme `bay_kit.glb`. Le brief le dit
explicitement : « aux memes materiaux et a la meme densite de depliage ».
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
# Meme raison que pour `bay_kit` : une assise calculee ici et une assise calculee
# la-bas divergeraient en silence, et aucun harnais separe ne le verrait.
sys.path.insert(0, _HERE)
import build_long_cortege as cortege  # noqa: E402
import build_bay_kit as baykit        # noqa: E402  (planche : le hangar temoin)

OUTPUT = os.path.join(_REPO, "assets/imported/models/backgrounds/turret_kit.glb")
PLATE = os.path.join(_REPO, "docs/forge/output/BRIEF-0093-planche-tourelles.png")
HULL = cortege.OUTPUT
BAY_KIT = baykit.OUTPUT

# ==========================================================================
# Cotes maitresses — repere KIT (X lateral, Y haut, Z survol, +Z = PROUE)
# ==========================================================================
# Y = 0 est le plan d'ASSISE du socle sur la peau, c'est-a-dire le Y que porte
# desormais le marqueur `Turret_NN` de la coque — exactement comme le Y du
# marqueur `Bay_NN` est devenu la bouche (BRIEF-0091). TOUTES les pieces sont
# modelisees sur ce plan.

#: Diametre du socle. Brief : 3,40 m (planche 3,0-4,0 ; 1,5 a 2 x le joueur).
PAD_D = 3.40
PAD_R = PAD_D * 0.5
#: Hauteur du bourrelet au-dessus de l'assise. ⚠️ 18 cm et non 8 : sous 9 cm un
#: relief est moyenne puis disparait au downscale. Le bourrelet EST la lecture
#: « socle visiblement ancre » de la planche ; il doit survivre au filtre.
PAD_RIM_H = 0.18
#: Le plateau ou se posent coffrets et conduites (« details autour du socle »).
PAD_SHELF_Y = 0.14
PAD_SHELF_R0 = 1.24
#: Profondeur ENTERREE du socle. ⚠️ Elle n'est pas decorative. Le pourtour du
#: socle accuse jusqu'a 0,683 m de denivele (mesure sur les 17 emplacements,
#: table au compte-rendu) : sans jupe, le socle ne poserait que d'un cote,
#: exactement comme le coaming du hangar avant BRIEF-0091.
PAD_BURIED = 0.85
#: La cuvette ou la couronne s'enfonce. Son fond, et son rayon interieur.
PAD_WELL_Y = 0.02
PAD_WELL_R = 1.16
PAD_SEG = 24

#: Jupe d'ancrage SUPPLEMENTAIRE — la premiere des trois familles de variete.
#: Le moteur la pose ou non ; sans elle le socle est identique.
SKIRT_R = 2.08
SKIRT_TOP = 0.06
SKIRT_BURIED = 0.80

#: La couronne de rotation. Brief : 60-70 pct du socle -> 2,25 m ; hauteur 0,35.
RING_D = 2.25
RING_R = RING_D * 0.5
RING_H = 0.35
RING_SEG = 24
#: Elle se pose au fond de la cuvette : elle emerge donc de 0,19 m seulement
#: au-dessus du bourrelet. C'est ça, « enfoncee dans le socle ».
RING_BASE = PAD_WELL_Y
RING_TOP = RING_BASE + RING_H

#: Le bloc canon blinde — RECTANGULAIRE TRAPU, surtout pas une sphere.
#: ⚠️ 1,92 m DE LARGE POUR 1,52 m DE LONG, ET C'EST LA LARGEUR QUI EST CALCULEE,
#: pas choisie : le masque doit LOGER les deux tubes, manchons de recul compris,
#: a l'ecartement maximal que la variete autorise. Le manchon fait 0,44 m de
#: diametre, l'entraxe maximal 1,00 m ; il faut donc 1,44 m de face avant PLATE,
#: donc 1,48 m de facette entre les deux chanfreins, donc 1,92 m hors tout. Un
#: bloc plus etroit rendrait « des canons colles devant une boite » — le defaut
#: exact que le brief demande de corriger.
BODY_HX = 0.96
BODY_Z0, BODY_Z1 = -0.80, 0.72
BODY_H = 1.01
BODY_CHAMFER = 0.22
BODY_BASE = RING_TOP
BODY_TOP = BODY_BASE + BODY_H
#: Demi-largeur de la FACETTE AVANT PLATE : c'est l'ouverture du masque.
MANTLET_HX = BODY_HX - BODY_CHAMFER
#: Le viseur : la seule chose qui monte plus haut que le bloc, et elle est
#: etroite. Elle porte la cote de hauteur totale du brief.
SIGHT_H = 0.32
#: Hauteur totale de la tourelle au-dessus de l'assise. Brief : 1,70 m.
TURRET_H = BODY_TOP + SIGHT_H

#: Le masque : les canons sont LOGES dedans, pas colles devant. Toute la facette
#: avant du bloc est en retrait de 12 cm — pas une plaque posee, un CREUX, qui
#: porte une ombre sur toute sa largeur. Une ombre survit au downscale, un rivet
#: non.
MANTLET_DEPTH = 0.12
#: Draft du creux : le fond est legerement plus petit que la bouche. Une paroi
#: verticale rend une valeur unique ; une paroi en depouille en rend deux.
MANTLET_DRAFT = 0.03

#: LES CANONS SONT EXAGERES, ET C'EST DELIBERE. Un tube physiquement juste mais
#: fin disparait apres le post-traitement : a 23 px/m, 12 cm font trois pixels.
#: 34 cm de diametre en font huit — ça tient.
BARREL_LEN = 2.90
BARREL_SHORT_LEN = 2.20
BARREL_R = 0.17
#: Rayon du manchon de recul, a la culasse. C'est LUI qui dimensionne le masque.
BARREL_SLEEVE = BARREL_R * 1.30
BARREL_SEG = 16
#: Hauteur de l'axe des tubes. A mi-bloc (0,53 sur 1,01 en repere bloc), et assez
#: haut pour que le manchon passe AU-DESSUS des coffrets quand la tourelle pivote.
BARREL_Y = 0.90
#: Z de la CULASSE : au fond du masque, pas sur la face avant. C'est la
#: difference entre « loge dans un masque » et « colle devant une boite ».
BARREL_Z = BODY_Z1 - MANTLET_DEPTH
#: Entraxe des deux tubes. 0,43 + 0,17 = 0,60 de demi-largeur -> 1,20 m hors
#: tout, la cote du brief. Le moteur peut l'ecarter (variete) sans sortir du
#: masque : la borne est verifiee au harnais.
BARREL_GAUGE = 0.86
BARREL_GAUGE_MAX = 0.98

#: L'appareillage.
BOX_W, BOX_D, BOX_H = 0.78, 0.44, 0.42
PIPE_R = 0.07
PIPE_LEN = 1.05
#: Rayon ou l'appareillage se pose sur le plateau du socle.
FITTING_R = 1.46

#: L'œil energetique. Brief : <= 25 pct de la tourelle — regle DURE. Il est au
#: FOND du masque, entre les deux tubes : il ne peut pas baver sur la silhouette.
EYE_R = 0.18
EYE_RISE = 0.06

#: Emprise hors-tout de l'installation posee sur la peau, jupe comprise. ⚠️ Elle
#: doit valoir `cortege.TURRET_FOOTPRINT_R` AU CENTIMETRE : c'est avec ce rayon
#: que la coque echantillonne sa peau pour calculer l'assise du marqueur. Deux
#: valeurs qui derivent, c'est un socle qui flotte d'un cote. Verifie au harnais.
FOOTPRINT_R = SKIRT_R

#: Meme densite que le borde : voir l'en-tete (deux echelles sur un meme slot).
TEXELS_PER_METER = cortege.HULL_TEXELS_PER_METER

#: Budget du brief : 55 000 tri pour dix-sept tourelles, ~3 200 par tourelle
#: assemblee. Une tourelle = socle + jupe + couronne + bloc + 2 tubes + 2
#: coffrets + 1 faisceau.
TRI_BUDGET_ASSEMBLED = 3_200
TRI_BUDGET_LEVEL = 55_000

#: Couleurs reservees aux TIRS (charte SS3) : interdites ici comme ailleurs.
FORBIDDEN_HEX = cortege.FORBIDDEN_HEX

#: Les huit noms de nœuds. Le moteur monte par le NOM : le harnais echoue si l'un
#: manque, si l'un est en trop, ou si l'un porte un enfant.
PART_NAMES = (
    "turret_pad", "turret_anchor_skirt", "turret_ring", "turret_body",
    "turret_barrel", "turret_barrel_short", "turret_service_box", "turret_pipe",
)

#: ⚠️ HUIT NŒUDS POUR SIX PIECES AU BRIEF, ET LES DEUX EN PLUS SONT LE LIVRABLE
#: « VARIETE ». Le brief demande trois familles obtenues « par assemblage seul,
#: sans reforge » : une jupe d'ancrage presente ou non, et une longueur de canon
#: « au choix parmi deux ». Aucune des deux ne s'obtient en deplaçant une piece.
#: La seule autre voie serait une mise a l'echelle non uniforme du tube, qui
#: etirerait son frein de bouche — un defaut visible, pour economiser 210
#: triangles sur un budget de 55 000.

#: OU CHAQUE PIECE TOMBE DANS LA TOURELLE ASSEMBLEE, et combien de fois.
#: ⚠️ Ce n'est pas une commodite de rapport : sans elle, l'aire par materiau se
#: mesurerait dans le repere de CHAQUE piece, ou la jupe enterree du socle passe
#: pour visible. La repartition 80/15/5 du brief parle de l'ECRAN : elle doit se
#: mesurer la ou les pieces sont posees, et avec leurs copies.
ASSEMBLY_OFFSET: dict[str, tuple[float, float, float]] = {
    "turret_pad": (0.0, 0.0, 0.0),
    "turret_anchor_skirt": (0.0, 0.0, 0.0),
    "turret_ring": (0.0, RING_BASE, 0.0),
    "turret_body": (0.0, BODY_BASE, 0.0),
    "turret_barrel": (-BARREL_GAUGE * 0.5, BARREL_Y, BARREL_Z),
    "turret_barrel_short": (BARREL_GAUGE * 0.5, BARREL_Y, BARREL_Z),
    "turret_service_box": (0.0, PAD_SHELF_Y, FITTING_R),
    "turret_pipe": (0.0, PAD_SHELF_Y, -FITTING_R),
}
#: Le tube est pose DEUX fois (les deux voies) et le coffret deux fois (la
#: variation que le brief prevoit). Le tube court est une ALTERNATIVE au long :
#: il ne compte pas dans la tourelle assemblee, sans quoi on facturerait quatre
#: canons a une tourelle qui en porte deux.
ASSEMBLY_COPIES: dict[str, int] = {name: 1 for name in PART_NAMES}
ASSEMBLY_COPIES.update({"turret_barrel": 2, "turret_barrel_short": 0,
                        "turret_service_box": 2})

#: LES TROIS FAMILLES — c'est le livrable « variete », et il se regarde sur la
#: planche. Le moteur n'a besoin de rien d'autre que de ce tableau : chaque
#: colonne est un parametre d'assemblage, aucune n'est une geometrie nouvelle.
#:
#: (nom, jupe, longueur de canon, entraxe, nb de coffrets, angles des coffrets,
#:  faisceau de conduites, angle du faisceau)
FAMILIES: tuple[tuple, ...] = (
    ("A - avancee", False, "turret_barrel_short", 0.72, 1, (128.0,), False, 0.0),
    ("B - de borde", True, "turret_barrel", 0.86, 2, (118.0, -118.0), True, 180.0),
    ("C - lourde", True, "turret_barrel", 0.98, 2, (96.0, -142.0), True, 205.0),
)


# ==========================================================================
# Primitives — bobinage CALCULE, jamais suppose
# ==========================================================================


def _new_object(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    """Objet a 7 slots normalises, SANS `recalc_face_normals`.

    Meme raison que sur la coque et sur `bay_kit` : l'heuristique de bmesh peut
    retourner une piece entiere, et une piece retournee DISPARAIT en jeu (culling
    arriere) sans qu'aucune bbox, aucun compte de triangles ni aucune mesure d'UV
    ne le voie. Les sens sont poses par calcul, et `_assert_outward()` les relit.
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
    """Un quad dont la normale part du cote `want`. Deterministe."""
    verts = [a, b, c, d]
    normal = (b.co - a.co).cross(c.co - a.co)
    if normal.dot(want) < 0.0:
        verts.reverse()
    return _face(bm, verts, material)


def _circle(radius: float, segments: int,
            phase: float = 0.0) -> list[tuple[float, float]]:
    """Points (x, z) d'un polygone regulier CENTRE SUR L'ORIGINE.

    ⚠️ Centre sur l'origine, et pas ailleurs : c'est de cette fonction que depend
    le fait que `turret_ring` tourne sur place. `_assert_on_axis()` le reverifie
    sur le binaire, parce qu'une faute ici ne se verrait qu'en jeu, en mouvement.
    """
    return [(radius * math.cos(phase + 2.0 * math.pi * k / segments),
             radius * math.sin(phase + 2.0 * math.pi * k / segments))
            for k in range(segments)]


def _octagon(hx: float, hz: float, chamfer: float) -> list[tuple[float, float]]:
    """Rectangle 2hx x 2hz aux quatre coins coupes. Sens trigonometrique.

    ⚠️ LE CHANFREIN EST LA DEPENSE PRINCIPALE DE CE KIT. Un coin a 90 deg scintille
    a 23 px/m et ne rend aucune lumiere ; un coin coupe de 22 cm porte une bande
    claire sur toute la hauteur du bloc, a n'importe quelle resolution. C'est ce
    qui fait qu'un cube gris se lit comme du blindage et non comme une boite.
    """
    return [
        (hx, hz - chamfer), (hx - chamfer, hz),
        (-(hx - chamfer), hz), (-hx, hz - chamfer),
        (-hx, -(hz - chamfer)), (-(hx - chamfer), -hz),
        (hx - chamfer, -hz), (hx, -(hz - chamfer)),
    ]


def _loft_y(bm: bmesh.types.BMesh,
            rings: list[tuple[list[tuple[float, float]], float]],
            materials: list[str],
            skip: set[tuple[int, int]] | None = None) -> list[list]:
    """Relie des anneaux fermes empiles en Y. Rend les sommets, anneau par anneau.

    `rings` : (points (x, z), y), du bas vers le haut, PUIS vers l'interieur si le
    profil rentre (une cuvette, une gorge). `materials` : un par bande.
    `skip` : les (bande, segment) a ne pas emettre — c'est ainsi qu'on PERCE une
    facette pour y creuser un masque, sans jamais supprimer une face apres coup.

    ⚠️ LE SENS DES FACES EST CALCULE PAR PRODUIT VECTORIEL, ET LA REGLE A CHANGE
    LE 2026-08-29. Elle etait « la normale part du cote oppose a l'axe ». C'est
    FAUX partout ou le profil rentre, et c'est mesure, pas suppose : le socle
    sortait avec 41 faces retournees — tout son plateau, toute la paroi de sa
    cuvette et son fond — parce qu'une surface qui regarde vers le haut ou vers
    l'interieur d'un creux ne regarde pas « loin de l'axe ». Elles auraient
    disparu en jeu par culling arriere, sans une ligne au journal, et le harnais
    d'alors les declarait bonnes.

    La regle juste ne parle pas de l'axe du tout : les anneaux etant ordonnes dans
    le sens trigonometrique, la normale sortante d'un quad vaut

        (montee du profil)  x  (sens de parcours de l'anneau)

    Elle rend le bon cote pour une paroi verticale, pour un plafond, pour un fond
    de cuvette et pour une gorge, sans qu'on ait a le declarer nulle part.
    """
    verts = [[bm.verts.new(Vector((x, y, z))) for x, z in points]
             for points, y in rings]
    blocked = skip or set()
    for k in range(len(rings) - 1):
        low, high = verts[k], verts[k + 1]
        count = len(low)
        for i in range(count):
            if (k, i) in blocked:
                continue
            j = (i + 1) % count
            climb = (high[i].co + high[j].co - low[i].co - low[j].co) * 0.5
            along = low[j].co - low[i].co
            want = climb.cross(along)
            if want.length < 1e-9:
                want = (high[j].co - high[i].co).cross(climb)
            _quad_facing(bm, low[i], low[j], high[j], high[i], materials[k], want)
    return verts


def _cap_low(bm: bmesh.types.BMesh, ring: list, material: str) -> None:
    """Ferme le PREMIER anneau d'un empilement en Y : la face regarde vers -Y."""
    _face_facing(bm, list(ring), material, Vector((0.0, -1.0, 0.0)))


def _cap_high(bm: bmesh.types.BMesh, ring: list, material: str) -> None:
    """Ferme le DERNIER anneau d'un empilement en Y : la face regarde vers +Y.

    ⚠️ ET C'EST LA QU'ON S'ETAIT TROMPE. Le socle et la jupe fermaient leur
    dernier anneau vers le BAS — le fond de la cuvette regardait le sol. Deux
    faces, invisibles a toute mesure de bbox, de triangles ou d'UV, et le fond de
    la cuvette disparaissait en jeu. Les deux fonctions existent donc separement
    plutot qu'un `want` passe a l'appel : un sens qu'on ECRIT a chaque appel est
    un sens qu'on finit par ecrire a l'envers. `_assert_solid()` le reverifie.
    """
    _face_facing(bm, list(ring), material, Vector((0.0, 1.0, 0.0)))


def _loft_z(bm: bmesh.types.BMesh, stops: list[tuple[float, float]],
            segments: int, materials: list[str],
            cx: float = 0.0, cy: float = 0.0) -> list[list]:
    """Un tube : anneaux circulaires empiles le long de +Z. Normales calculees.

    `stops` : (z, rayon) de la culasse vers la bouche. Un materiau par bande.
    Meme regle que `_loft_y` — (montee) x (parcours) — et pour la meme raison :
    la bouche du canon est CREUSEE, donc son cone regarde vers l'axe. La regle
    radiale d'avant refusait ces 16 faces-la, qui etaient justes, et acceptait les
    41 du socle, qui ne l'etaient pas.
    """
    verts = []
    for z, radius in stops:
        ring = []
        for k in range(segments):
            a = 2.0 * math.pi * k / segments
            ring.append(bm.verts.new(
                Vector((cx + radius * math.cos(a), cy + radius * math.sin(a), z))))
        verts.append(ring)
    for k in range(len(stops) - 1):
        low, high = verts[k], verts[k + 1]
        for i in range(segments):
            j = (i + 1) % segments
            climb = (high[i].co + high[j].co - low[i].co - low[j].co) * 0.5
            along = low[j].co - low[i].co
            # ⚠️ `along x climb` et non l'inverse : les anneaux de `_loft_z`
            # tournent dans l'autre sens que ceux de `_loft_y` (l'angle y decrit
            # (x, y), ici (x, z)). Verifie sur un temoin au demarrage.
            want = along.cross(climb)
            if want.length < 1e-9:
                want = Vector((0.0, 0.0, 1.0))
            _quad_facing(bm, low[i], low[j], high[j], high[i], materials[k], want)
    return verts


def _cap_z(bm: bmesh.types.BMesh, ring: list, material: str,
           entering: bool) -> None:
    """Ferme un anneau de `_loft_z` : -Z a l'entree du profil, +Z a sa sortie."""
    _face_facing(bm, list(ring), material,
                 Vector((0.0, 0.0, -1.0 if entering else 1.0)))


def _chamfered_block(bm: bmesh.types.BMesh, hx: float, hz: float,
                     y0: float, y1: float, chamfer: float, inset: float,
                     side_material: str, top_material: str,
                     cx: float = 0.0, cz: float = 0.0,
                     skip: set[tuple[int, int]] | None = None) -> list[list]:
    """Un pave dont les DOUZE grandes aretes sont coupees. Coque FERMEE.

    Quatre aretes verticales par l'octogone, quatre en haut et quatre en bas par
    un anneau en retrait de `inset`. C'est le seul detail que ce kit s'autorise a
    repeter : il coute 16 triangles par arete et il rend de la lumiere a toutes
    les resolutions, ce qu'aucun rivet ne fait.

    ⚠️ Le fond est TOUJOURS ferme, meme enterre dans une autre piece. Un pave
    ouvert par-dessous n'est pas un solide : sa normale de bord ne se verifie pas,
    et le harnais de coque ne peut plus prouver que rien n'est retourne. Deux
    triangles invisibles sont moins chers qu'un controle qu'on ne peut plus faire.
    """
    lip = min(inset, (y1 - y0) * 0.35)
    profile = [_shift_xz(_octagon(hx - inset, hz - inset,
                                  max(chamfer - inset, 0.04)), cx, cz),
               _shift_xz(_octagon(hx, hz, chamfer), cx, cz)]
    rings = [(profile[0], y0), (profile[1], y0 + lip),
             (profile[1], y1 - lip), (profile[0], y1)]
    verts = _loft_y(bm, rings, [side_material] * 3, skip=skip)
    _cap_high(bm, verts[-1], top_material)
    _cap_low(bm, verts[0], "AA_Greeble")
    return verts


def _shift_xz(points: list[tuple[float, float]], dx: float,
              dz: float) -> list[tuple[float, float]]:
    """Decale un profil (x, z)."""
    return [(x + dx, z + dz) for x, z in points]


# ==========================================================================
# LE SOCLE — un disque tres aplati, ancre, et son plateau d'appareillage
# ==========================================================================


def build_pad() -> bpy.types.Object:
    """`turret_pad`. Origine : centre du socle, Y = plan d'assise sur la peau.

    Sept anneaux, six bandes, et chacune fait un travail :

        -0,85 -> -0,10   la JUPE ENTERREE, en depouille. Elle absorbe les 0,683 m
                         de denivele mesures sur le pourtour des dix-sept
                         emplacements : sans elle le socle poserait d'un cote et
                         flotterait de l'autre, exactement comme le coaming du
                         hangar avant BRIEF-0091.
        -0,10 -> +0,04   le CHANFREIN d'assise : la grande arete qui fait le tour
                         du socle, celle que la lumiere cle accroche de loin.
        +0,04 -> +0,18   le BOURRELET. 18 cm : au-dessus du seuil de 9 cm sous
                         lequel le downscale efface tout relief.
        +0,18 -> +0,14   le PLATEAU, ou se posent coffrets et conduites.
        +0,14 -> +0,18   la levre de cuvette, en relief.
        +0,18 -> +0,02   la paroi de la CUVETTE, ou la couronne s'enfonce.

    ⛔ AUCUN EMISSIF ICI. Le socle de BRIEF-0089 avait un cœur magenta plein — un
    « jeton lumineux », precisement ce que ce brief remplace. La lumiere de la
    tourelle est son œil, et rien d'autre.
    """
    bm = bmesh.new()
    outer = _circle(PAD_R, PAD_SEG)
    rings = [
        (_circle(PAD_R - 0.26, PAD_SEG), -PAD_BURIED),
        (outer, -0.10),
        (outer, 0.04),
        (_circle(PAD_R - 0.10, PAD_SEG), PAD_RIM_H),
        (_circle(PAD_SHELF_R0, PAD_SEG), PAD_SHELF_Y),
        (_circle(PAD_WELL_R + 0.06, PAD_SEG), PAD_RIM_H),
        (_circle(PAD_WELL_R, PAD_SEG), PAD_WELL_Y),
    ]
    verts = _loft_y(bm, rings,
                    ["AA_Greeble",   # jupe enterree
                     "AA_Hull",      # chanfrein d'assise
                     "AA_Hull",      # bourrelet
                     "AA_Hull",      # plateau
                     "AA_Trim",      # levre de cuvette : le seul liseré clair
                     "AA_Greeble"])  # paroi de la cuvette
    # ⚠️ Le dernier anneau est le FOND DE LA CUVETTE, et il regarde le CIEL.
    # Il regardait le sol jusqu'au 2026-08-29 — voir `_cap_high()`.
    _cap_high(bm, verts[-1], "AA_Greeble")
    _cap_low(bm, verts[0], "AA_Greeble")
    return _new_object("turret_pad", bm)


def build_anchor_skirt() -> bpy.types.Object:
    """`turret_anchor_skirt` — la jupe d'ancrage SUPPLEMENTAIRE, optionnelle.

    Premiere des trois familles de variete : le moteur la pose ou ne la pose pas.
    C'est un anneau plat, large, enterre plus profond que le socle : il donne aux
    tourelles de poupe l'assise massive que la table `PAD_RADIUS` de la coque
    reservait deja (« de plus en plus massives vers la poupe »), sans qu'aucune
    geometrie nouvelle ne soit necessaire.

    ⚠️ Son rayon hors-tout, 2,08 m, EST l'emprise du kit — la meme valeur que
    `cortege.TURRET_FOOTPRINT_R`, avec laquelle la coque echantillonne sa peau
    pour poser l'assise du marqueur. Le harnais refuse qu'elles divergent.
    """
    bm = bmesh.new()
    # ⚠️ UN ANNEAU FERME, PAS UN DISQUE. La jupe se refermait par un couvercle
    # plein de 1,66 m de rayon, tout entier sous le socle : 8,66 m2 de surface
    # que rien ne peut voir, comptes comme visibles dans la repartition par
    # materiau. Le profil revient donc sur lui-meme — il n'y a plus de couvercle,
    # plus de fond, et la piece reste une coque fermee (`_assert_solid()`).
    outer_low = _circle(SKIRT_R - 0.22, PAD_SEG)
    rings = [
        (outer_low, -SKIRT_BURIED),
        (_circle(SKIRT_R, PAD_SEG), -0.16),
        (_circle(SKIRT_R, PAD_SEG), -0.04),
        (_circle(SKIRT_R - 0.16, PAD_SEG), SKIRT_TOP),
        (_circle(PAD_R - 0.06, PAD_SEG), SKIRT_TOP),   # sous la levre du socle
        (_circle(PAD_R - 0.12, PAD_SEG), -0.12),       # paroi interieure
        (_circle(PAD_R - 0.12, PAD_SEG), -SKIRT_BURIED + 0.06),
        (outer_low, -SKIRT_BURIED),                    # le profil se referme
    ]
    # ⚠️ LA COURONNE VISIBLE EST EN `AA_Hull`, PAS EN `AA_Trim`, ET C'EST UNE
    # CORRECTION DE RENDU, PAS UN GOUT. L'ivoire froid de l'Unisson (#DDDCD2) sur
    # un anneau de 2,9 m2 qui fait le TOUR de la piece, c'est la faute que
    # BRIEF-0089 a chiffree : un materiau clair pose sur une arete CONTINUE
    # occupe plus de pixels qu'une piece entiere. Regarde sur la planche, l'effet
    # etait un halo blanc autour de chaque tourelle, qui volait le contraste aux
    # projectiles. L'ivoire reste sur ce qui est PETIT et POSE : coffrets,
    # conduites, radiateur, levre de cuvette.
    _loft_y(bm, rings,
            ["AA_Greeble",   # depouille exterieure, enterree
             "AA_Hull",      # chanfrein d'assise
             "AA_Hull",      # bandeau
             "AA_Hull",      # la couronne visible autour du socle
             "AA_Greeble",   # paroi interieure, sous le socle
             "AA_Greeble",
             "AA_Greeble"])  # fond annulaire
    return _new_object("turret_anchor_skirt", bm)


# ==========================================================================
# LA COURONNE — c'est ELLE qui tourne, et son origine EST son axe
# ==========================================================================


def build_ring() -> bpy.types.Object:
    """`turret_ring`. Origine : SUR L'AXE DE ROTATION, au fond de la cuvette.

    ⚠️ CETTE PIECE EST LA SEULE DU KIT DONT L'ORIGINE SOIT UN MECANISME ET NON UN
    POINT DE POSE. Le moteur la fait tourner a 42 deg/s autour de son Y ; si son
    maillage n'est pas centre sur cet axe au micron, la tourelle balaie en
    decrivant un cercle au lieu de pivoter sur place — et ça ne se voit qu'en jeu,
    EN MOUVEMENT, donc jamais sur une planche. `_assert_on_axis()` le relit sur le
    binaire produit.

    Sept anneaux : une portee basse en retrait (l'ombre qui dit « enfonce »), le
    fut chanfreine en haut et en bas, une gorge en violet sombre a mi-hauteur —
    elle casse le cylindre en deux et donne un pas de rotation lisible quand la
    piece tourne — puis la portee superieure ou s'assied le bloc.
    """
    bm = bmesh.new()
    rings = [
        (_circle(RING_R - 0.10, RING_SEG), 0.0),
        (_circle(RING_R, RING_SEG), 0.09),
        (_circle(RING_R, RING_SEG), 0.15),
        (_circle(RING_R - 0.07, RING_SEG), 0.20),
        (_circle(RING_R - 0.02, RING_SEG), 0.26),
        (_circle(RING_R - 0.02, RING_SEG), RING_H - 0.05),
        (_circle(RING_R - 0.16, RING_SEG), RING_H),
    ]
    verts = _loft_y(bm, rings,
                    ["AA_Hull",      # portee basse, en retrait
                     "AA_Hull",      # fut
                     "AA_Panel",     # la gorge : violet sombre, un seul tour
                     "AA_Panel",
                     "AA_Hull",      # fut haut
                     "AA_Hull"])     # chanfrein de couronnement
    _cap_high(bm, verts[-1], "AA_Hull")
    _cap_low(bm, verts[0], "AA_Greeble")
    return _new_object("turret_ring", bm)


# ==========================================================================
# LE BLOC BLINDE — rectangulaire trapu, et son masque REELLEMENT creuse
# ==========================================================================

#: Le masque occupe TOUTE la facette avant plate de la bande mediane du bloc.
#: L'index 1 est le segment (sommet 1 -> sommet 2) de l'octogone, c'est-a-dire sa
#: face +Z ; la bande 1 est celle qui va de `lip` a `BODY_H - 0,16`.
_MANTLET_BAND = 1
_MANTLET_FACET = 1


def build_body() -> bpy.types.Object:
    """`turret_body`. Origine : sur l'axe de rotation, au sommet de la couronne.

    ⚠️ RECTANGULAIRE TRAPU, SURTOUT PAS UNE SPHERE (brief). Un dome se lit comme
    un jeton vu de dessus a 20 deg de la verticale — c'est exactement le reproche
    de l'operateur. Un pave chanfreine, lui, montre trois faces de valeurs
    differentes des qu'une lumiere cle l'eclaire : il a un AVANT.

    Quatre volumes, et pas un de plus :

        1. le pave principal, 1,92 x 1,52 x 1,01, chanfreine sur ses douze aretes,
           et dont la FACETTE AVANT EST PERCEE ;
        2. le MASQUE : la facette percee est refermee 12 cm plus loin, en
           depouille. Les canons y sont LOGES — leur culasse est au fond du creux,
           pas sur la face avant. C'est la seule difference entre « un affut » et
           « deux tubes colles devant une boite », et elle se lit a l'ombre que le
           creux porte sur toute la largeur du bloc ;
        3. le viseur, etroit, qui porte la cote de hauteur totale (1,70 m) ;
        4. le bloc de recul arriere, en surplomb : il donne une POUPE au bloc, ce
           qui fait qu'on lit d'un coup d'œil ou la tourelle regarde, meme
           immobile et meme en noir et blanc.

    Plus l'ŒIL : un seul emissif dans tout le kit, 0,36 m de large pour une
    tourelle de 1,70 m — 21,2 pct, sous la regle dure des 25 pct du brief.

    ⚠️ QUATRE COQUES FERMEES, PAS UN AMAS DE FACES. Le viseur et le bloc de recul
    sont des solides a part entiere, poses en intersection. C'est ce qui permet a
    `_assert_solid()` de prouver, composante par composante, que rien n'est
    retourne : une nappe ouverte n'a pas de volume, donc pas de preuve.
    """
    bm = bmesh.new()
    hz = (BODY_Z1 - BODY_Z0) * 0.5
    cz = (BODY_Z1 + BODY_Z0) * 0.5
    lip = 0.11

    # 1. Le pave, sa facette avant PERCEE (le masque la refermera).
    top_lip = 0.16
    rings = [
        (_shift(_octagon(BODY_HX - lip, hz - lip, BODY_CHAMFER - lip), cz), 0.0),
        (_shift(_octagon(BODY_HX, hz, BODY_CHAMFER), cz), lip),
        (_shift(_octagon(BODY_HX, hz, BODY_CHAMFER), cz), BODY_H - top_lip),
        (_shift(_octagon(BODY_HX - 0.09, hz - 0.09, BODY_CHAMFER - 0.05), cz),
         BODY_H),
    ]
    verts = _loft_y(bm, rings, ["AA_Hull", "AA_Hull", "AA_Hull"],
                    skip={(_MANTLET_BAND, _MANTLET_FACET)})
    _cap_high(bm, verts[-1], "AA_Hull")
    _cap_low(bm, verts[0], "AA_Greeble")

    # 2. LE MASQUE. Les quatre sommets du trou, dans l'ordre ou `_loft_y` les
    #    aurait employes, puis le fond en retrait et en depouille.
    lo, hi = verts[_MANTLET_BAND], verts[_MANTLET_BAND + 1]
    i, j = _MANTLET_FACET, _MANTLET_FACET + 1
    rim = [lo[i], lo[j], hi[j], hi[i]]
    floor_z = BODY_Z1 - MANTLET_DEPTH
    d = MANTLET_DRAFT
    deep = [bm.verts.new(Vector((v.co.x - math.copysign(d, v.co.x),
                                 v.co.y + (d if k >= 2 else -d), floor_z)))
            for k, v in enumerate(rim)]
    centre = Vector((0.0, (lo[i].co.y + hi[i].co.y) * 0.5, floor_z))
    for k in range(4):
        m = (k + 1) % 4
        mid = (rim[k].co + rim[m].co + deep[k].co + deep[m].co) * 0.25
        want = centre - mid
        want.z = 0.0
        if want.length < 1e-9:
            want = Vector((0.0, 0.0, 1.0))
        _quad_facing(bm, rim[k], rim[m], deep[m], deep[k], "AA_Greeble", want)
    _face_facing(bm, deep, "AA_Greeble", Vector((0.0, 0.0, 1.0)))

    # 3. Le viseur : le seul volume qui monte au-dessus du bloc. Il est ETROIT —
    #    c'est ce qui fait qu'une tourelle n'a pas la meme tete de face et de
    #    profil, donc qu'on lit ou elle regarde meme immobile.
    _chamfered_block(bm, 0.30, 0.34, BODY_H - 0.04, BODY_H + SIGHT_H, 0.09, 0.06,
                     "AA_Hull", "AA_Trim", cz=cz + 0.14)
    # 4. Le bloc de recul / radiateur, en surplomb a l'arriere. Il est POSE assez
    #    haut pour que la rotation ne le fasse jamais passer sur un coffret :
    #    le harnais mesure ce degagement, il n'est pas laisse a l'œil.
    _chamfered_block(bm, 0.52, 0.15, 0.32, 0.84, 0.10, 0.07,
                     "AA_Hull", "AA_Trim", cz=BODY_Z0 - 0.11)

    # L'ŒIL, au fond du masque, entre les deux tubes. Une lentille legerement
    # conique, en saillie de 6 cm sur le fond du creux mais toujours 6 cm EN
    # RETRAIT de la face avant : elle ne peut pas baver sur la silhouette, et
    # eteinte elle reste lisible — c'est un relief dans une ombre.
    eye_y = BARREL_Y - BODY_BASE
    eye = _loft_z(bm, [(floor_z - 0.04, EYE_R * 0.72),
                       (floor_z, EYE_R),
                       (floor_z + EYE_RISE * 0.45, EYE_R),
                       (floor_z + EYE_RISE, EYE_R * 0.78)],
                  12, ["AA_Greeble", "AA_Greeble", "AA_Emissive_Engine"],
                  cy=eye_y)
    _cap_z(bm, eye[0], "AA_Greeble", entering=True)
    _cap_z(bm, eye[-1], "AA_Emissive_Engine", entering=False)
    return _new_object("turret_body", bm)


def _shift(points: list[tuple[float, float]],
           dz: float) -> list[tuple[float, float]]:
    """Decale un profil (x, z) le long de Z."""
    return [(x, z + dz) for x, z in points]


# ==========================================================================
# LES CANONS — exageres, et c'est une regle de lisibilite
# ==========================================================================


def _barrel(name: str, length: float) -> bpy.types.Object:
    """UN tube ; le moteur en pose deux, paralleles. Origine : LA CULASSE.

    Le profil a cinq paliers et chacun est une lecture, pas un ornement :

        0,00 -> 0,26   le MANCHON de recul, plus gros que le tube. C'est lui qui
                       dit que le canon sort d'un mecanisme et non d'un trou, et
                       c'est lui qui dimensionne l'ouverture du masque.
        0,26 -> 0,42   le chanfrein de manchon.
        0,42 -> L-0,55 le TUBE, legerement conique (17 -> 15 cm de rayon) : un
                       tube parfaitement cylindrique se lit comme une paille.
        L-0,55 -> L-0,10  le FREIN DE BOUCHE, un renflement.
        L-0,10 -> L    la bouche, CREUSEE.

    ⚠️ 34 cm de diametre pour un canon de vaisseau, c'est ENORME, et c'est
    delibere : a 23 px/m de detail utile, un tube physiquement juste de 12 cm fait
    trois pixels et disparait apres le post-traitement. Ce n'est pas une erreur
    d'echelle, c'est la regle de lisibilite du brief.

    ⚠️ ET LA BOUCHE CREUSEE EST CE QUI A FAIT ECHOUER LE HARNAIS D'ORIENTATION
    D'AVANT. Son cone regarde vers l'axe du tube — il le doit, c'est un trou — et
    la regle « toute face regarde loin de l'axe » le declarait retourne. Les 16
    faces refusees etaient justes ; ce sont les 41 du socle, acceptees, qui ne
    l'etaient pas. Voir `_assert_solid()`.
    """
    bm = bmesh.new()
    r = BARREL_R
    stops = [
        (0.0, BARREL_SLEEVE),
        (0.26, BARREL_SLEEVE),
        (0.42, r),
        (length - 0.55, r * 0.90),
        (length - 0.44, r * 1.16),
        (length - 0.14, r * 1.16),
        (length - 0.10, r * 0.94),
        (length, r * 0.94),
    ]
    materials = ["AA_Hull",     # manchon
                 "AA_Hull",     # chanfrein de manchon
                 "AA_Hull",     # tube
                 "AA_Trim",     # epaulement du frein : le seul clair du tube
                 "AA_Hull",     # frein de bouche
                 "AA_Hull",
                 "AA_Hull"]
    verts = _loft_z(bm, stops, BARREL_SEG, materials)
    _cap_z(bm, verts[0], "AA_Greeble", entering=True)
    # La bouche est CREUSEE : un disque plein se lit comme un bouchon.
    mouth = []
    for k in range(BARREL_SEG):
        a = 2.0 * math.pi * k / BARREL_SEG
        mouth.append(bm.verts.new(Vector((r * 0.58 * math.cos(a),
                                          r * 0.58 * math.sin(a),
                                          length - 0.14))))
    for i in range(BARREL_SEG):
        j = (i + 1) % BARREL_SEG
        _quad_facing(bm, verts[-1][i], verts[-1][j], mouth[j], mouth[i],
                     "AA_Greeble", Vector((0.0, 0.0, 1.0)))
    _cap_z(bm, mouth, "AA_Greeble", entering=False)
    return _new_object(name, bm)


def build_barrel() -> bpy.types.Object:
    return _barrel("turret_barrel", BARREL_LEN)


def build_barrel_short() -> bpy.types.Object:
    """Le tube court — la troisieme famille de variete, par assemblage seul."""
    return _barrel("turret_barrel_short", BARREL_SHORT_LEN)


# ==========================================================================
# L'APPAREILLAGE — coffret et conduites, sur le plateau du socle
# ==========================================================================


def build_service_box() -> bpy.types.Object:
    """`turret_service_box`. Origine : sa base, au centre de son empreinte.

    Le moteur en pose 0, 1 ou 2, a l'angle qu'il veut sur le plateau du socle :
    c'est la deuxieme famille de variete. Sa profondeur radiale (0,44 m) est
    calee sur la largeur du plateau (1,24 -> 1,60 m) : pose a r = 1,46 il ne
    deborde ni sur la cuvette ni hors du bourrelet.

    ⚠️ SA GORGE EST DANS LE PROFIL, PLUS UN RUBAN POSE DESSUS. Elle etait un
    second loft, 3 cm PLUS PETIT que le coffret : entierement a l'interieur, donc
    invisible, et 16 aretes de bord dans une piece qu'on croyait pleine. Un creux
    qui ne creuse pas ne coute pas moins cher qu'un creux — il coute pareil et il
    ne rend rien.
    """
    bm = bmesh.new()
    hx, hz, ch = BOX_W * 0.5, BOX_D * 0.5, 0.11
    body = _octagon(hx, hz, ch)
    foot = _octagon(hx - 0.07, hz - 0.07, 0.04)
    groove = _octagon(hx - 0.06, hz - 0.06, 0.05)
    rings = [(foot, 0.0), (body, 0.06), (body, 0.17), (groove, 0.20),
             (groove, 0.28), (body, 0.31), (body, BOX_H - 0.06),
             (foot, BOX_H)]
    verts = _loft_y(bm, rings,
                    ["AA_Trim", "AA_Trim", "AA_Greeble", "AA_Greeble",
                     "AA_Greeble", "AA_Trim", "AA_Trim"])
    _cap_high(bm, verts[-1], "AA_Hull")
    _cap_low(bm, verts[0], "AA_Greeble")
    return _new_object("turret_service_box", bm)


def build_pipe() -> bpy.types.Object:
    """`turret_pipe` — un FAISCEAU de trois conduites. Origine : sa base.

    Trois tubes de 14 cm de diametre et deux colliers. ⚠️ 14 cm et non 6 : sous
    9 cm, le downscale moyenne le relief et il ne reste qu'une salissure. Trois
    tubes de 14 cm lisent comme un faisceau ; dix tubes de 4 cm lisent comme du
    bruit, pour quatre fois le budget.

    Il court TANGENTIELLEMENT au socle (le long de X, dans son repere), ce qui
    lui donne une orientation propre : pose a deux angles differents, le meme
    faisceau ne donne pas la meme silhouette.

    ⚠️ LES DEUX COLLIERS SONT A DEUX ENDROITS. Ils etaient tous les deux a x = 0,
    la boucle qui devait les ecarter n'utilisant pas sa variable : le soudage des
    doublons les fusionnait en un seul, au milieu. Un faisceau tenu par un collier
    unique ne se lit pas comme un faisceau.
    """
    bm = bmesh.new()
    for k, offset in enumerate((-0.17, 0.0, 0.17)):
        lift = 0.10 + 0.05 * (1 - abs(k - 1))
        stops = [(-PIPE_LEN * 0.5, PIPE_R * 0.62),
                 (-PIPE_LEN * 0.5 + 0.08, PIPE_R),
                 (PIPE_LEN * 0.5 - 0.08, PIPE_R),
                 (PIPE_LEN * 0.5, PIPE_R * 0.62)]
        # Un tube couche : construit le long de Z, puis bascule sur X. Les
        # anneaux sont ecrits directement dans le repere final — une rotation
        # appliquee apres coup rendrait le sens des faces indemontrable.
        ring_verts = []
        for z, radius in stops:
            ring = []
            for i in range(8):
                a = 2.0 * math.pi * i / 8
                ring.append(bm.verts.new(Vector((
                    z, lift + radius * math.sin(a),
                    offset + radius * math.cos(a)))))
            ring_verts.append(ring)
        for b in range(3):
            low, high = ring_verts[b], ring_verts[b + 1]
            for i in range(8):
                j = (i + 1) % 8
                climb = (high[i].co + high[j].co - low[i].co - low[j].co) * 0.5
                along = low[j].co - low[i].co
                # « conduites » : la part grege du brief (15 pct), avec les
                # coffrets et le radiateur.
                _quad_facing(bm, low[i], low[j], high[j], high[i],
                             "AA_Trim", climb.cross(along))
        _face_facing(bm, list(ring_verts[0]), "AA_Greeble",
                     Vector((-1.0, 0.0, 0.0)))
        _face_facing(bm, list(ring_verts[-1]), "AA_Greeble",
                     Vector((1.0, 0.0, 0.0)))
    # Les deux colliers : ce sont eux qui font du faisceau UNE piece et non trois
    # tuyaux poses cote a cote.
    for cx in (-0.30, 0.30):
        collar = _shift_xz(_octagon(0.07, 0.27, 0.05), cx, 0.0)
        narrow = _shift_xz(_octagon(0.06, 0.25, 0.05), cx, 0.0)
        verts = _loft_y(bm, [(collar, 0.0), (collar, 0.05), (narrow, 0.28)],
                        ["AA_Greeble", "AA_Greeble"])
        _cap_high(bm, verts[-1], "AA_Greeble")
        _cap_low(bm, verts[0], "AA_Greeble")
    return _new_object("turret_pipe", bm)


# ==========================================================================
# Harnais de scene (avant export)
# ==========================================================================


def _shell_report(mesh: bpy.types.Mesh) -> dict:
    """Topologie et volume signe de chaque coque connexe d'un maillage.

    Trois mesures, et aucune n'est une opinion :

      * les aretes de BORD (une seule face) — une nappe ouverte n'est pas un
        solide, et on ne peut rien prouver dessus ;
      * les aretes INCOHERENTES (deux faces qui la parcourent dans le meme sens)
        — c'est la signature exacte d'une plaque retournee, ou qu'elle soit ;
      * le VOLUME SIGNE de chaque coque (theoreme de la divergence) — une coque
        entierement retournee est parfaitement coherente avec elle-meme, seul son
        volume la trahit, en devenant negatif.
    """
    use: dict[tuple[int, int], list[int]] = {}
    for poly in mesh.polygons:
        loop = list(poly.vertices)
        for k, a in enumerate(loop):
            b = loop[(k + 1) % len(loop)]
            use.setdefault((min(a, b), max(a, b)), []).append(1 if a < b else -1)
    boundary = [e for e, d in use.items() if len(d) == 1]
    excess = [e for e, d in use.items() if len(d) > 2]
    flipped = [e for e, d in use.items() if len(d) == 2 and d[0] == d[1]]

    parent = list(range(len(mesh.vertices)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for poly in mesh.polygons:
        loop = list(poly.vertices)
        for v in loop[1:]:
            ra, rb = root(loop[0]), root(v)
            if ra != rb:
                parent[rb] = ra
    volumes: dict[int, float] = {}
    for poly in mesh.polygons:
        loop = [mesh.vertices[i].co for i in poly.vertices]
        key = root(poly.vertices[0])
        acc = 0.0
        for k in range(1, len(loop) - 1):
            acc += loop[0].dot(loop[k].cross(loop[k + 1])) / 6.0
        volumes[key] = volumes.get(key, 0.0) + acc
    return {"boundary": boundary, "excess": excess, "flipped": flipped,
            "volumes": volumes}


def _assert_solid(obj: bpy.types.Object) -> None:
    """LA PIECE EST-ELLE UN SOLIDE, ET REGARDE-T-ELLE DEHORS ?

    ⚠️ CE HARNAIS A REMPLACE `_assert_outward()` LE 2026-08-29, ET IL NE L'A PAS
    ASSOUPLI — IL L'A RETOURNE. L'ancien demandait a chaque face de regarder « du
    cote oppose a l'axe ». C'est une bonne question pour un cylindre plein et une
    mauvaise pour toute piece qui CREUSE, ce que ce kit fait partout. Mesure sur
    les huit pieces, avant correction :

        turret_barrel   16 faces REFUSEES et pourtant justes — la bouche est
                        percee, son cone regarde forcement vers l'axe du tube ;
        turret_pad      41 faces ACCEPTEES et pourtant retournees — tout le
                        plateau, toute la paroi de la cuvette et son fond ;
        turret_anchor_skirt  une couronne superieure retournee, idem.

    Le harnais bloquait donc le build sur les faces correctes et laissait passer
    les fausses. Un controle qui se trompe dans les deux sens est pire que pas de
    controle : il fait perdre du temps ET il rassure.

    La question juste ne parle pas de l'axe. Une piece est bonne si :

      1. elle est FERMEE — aucune arete de bord, aucune arete a plus de deux
         faces. Sans cela, « dedans » et « dehors » n'ont pas de sens ;
      2. son bobinage est COHERENT — toute arete interieure est parcourue une
         fois dans chaque sens. Une seule plaque retournee casse cette propriete,
         qu'elle soit sur une bosse, dans un creux ou sur un plafond ;
      3. le volume signe de CHAQUE coque connexe est POSITIF. Les points 1 et 2
         ne distinguent pas un solide d'un solide integralement retourne ; le
         volume, si.

    Les trois ensemble prouvent ce que le brief a besoin de savoir : aucune face
    ne disparaitra par culling arriere. Et le defaut reste totalement silencieux
    sans eux — ni bbox, ni compte de triangles, ni mesure d'UV ne le voit.
    """
    report = _shell_report(obj.data)
    if report["boundary"]:
        raise ak.ContractError(
            f"{obj.name} : {len(report['boundary'])} arete(s) de BORD — la piece "
            "n'est pas une coque fermee, on ne peut pas prouver de quel cote elle "
            "regarde (ex. sommets "
            f"{report['boundary'][0]})")
    if report["excess"]:
        raise ak.ContractError(
            f"{obj.name} : {len(report['excess'])} arete(s) a plus de deux faces "
            "— maillage non manifold")
    if report["flipped"]:
        raise ak.ContractError(
            f"{obj.name} : {len(report['flipped'])} arete(s) parcourue(s) deux "
            "fois dans le meme sens — une plaque est RETOURNEE et disparaitrait "
            "en jeu sans un mot (culling arriere)")
    for key, volume in sorted(report["volumes"].items()):
        if volume <= 1e-6:
            raise ak.ContractError(
                f"{obj.name} : une coque connexe a un volume signe de "
                f"{volume:+.6f} m3 — elle est retournee EN ENTIER, ce qu'un "
                "bobinage coherent ne suffit pas a voir")


#: ⚠️ COMBIEN DE COQUES FERMEES PAR PIECE, ET C'EST UN CONTRAT. Un volume qui
#: apparait ou qui disparait est une faute de frappe qui ne se voit sur aucune
#: planche : deux colliers de conduite fusionnes en un seul ont vecu ainsi
#: jusqu'au 2026-08-29. Le compte est donc ECRIT, et relu apres soudage.
SHELL_COUNT: dict[str, int] = {
    "turret_pad": 1,
    "turret_anchor_skirt": 1,
    "turret_ring": 1,
    "turret_body": 4,          # pave+masque, viseur, bloc de recul, œil
    "turret_barrel": 1,
    "turret_barrel_short": 1,
    "turret_service_box": 1,
    "turret_pipe": 5,          # trois conduites, deux colliers
}


def _assert_shell_count(obj: bpy.types.Object) -> None:
    found = len(_shell_report(obj.data)["volumes"])
    want = SHELL_COUNT[obj.name]
    if found != want:
        raise ak.ContractError(
            f"{obj.name} : {found} coque(s) fermee(s) au lieu de {want} — un "
            "volume a fusionne avec un autre ou n'a pas ete emis")


def build_parts() -> list[bpy.types.Object]:
    parts = [
        build_pad(), build_anchor_skirt(), build_ring(), build_body(),
        build_barrel(), build_barrel_short(), build_service_box(), build_pipe(),
    ]
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
        # ⚠️ APRES le soudage et AVANT la triangulation : c'est le maillage
        # soude qui part a l'export, et c'est la fusion de deux sommets qui
        # ferait apparaitre une arete a trois faces. Le controle doit voir la
        # meme topologie que Godot.
        _assert_solid(obj)
        _assert_shell_count(obj)
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

    Le kit est fait de pieces dont l'avant et l'arriere ne se ressemblent pas (le
    canon ne sort que d'un cote, le bloc a un masque a l'avant et des joues a
    l'arriere). Une chaine d'axes fausse d'un demi-tour poserait dix-sept
    tourelles retournees, et aucune bounding box ne le dirait.
    """
    for probe in (Vector((1.0, 2.0, 3.0)), Vector((-0.86, 0.72, 2.9)),
                  Vector((1.7, -0.85, -0.94))):
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
    staging = tempfile.mkdtemp(prefix="aegis-turretkit-")
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


def turret_seat_y(s: float, x: float) -> tuple[float, float]:
    """(Y d'ASSISE du socle, Y du point le plus bas de son emprise).

    ⚠️ CE N'EST PAS UNE COPIE : la fonction VIT DANS `build_long_cortege`, qui
    est le seul endroit ou la peau existe, et c'est elle qui pose le Y du
    marqueur `Turret_NN`. Une assise recalculee ici divergerait en silence de
    celle qui a servi a placer le marqueur, et le socle flotterait — la faute
    exacte que `bay_mouth_y()` a evitee au hangar.
    """
    return cortege.turret_seat_y(s, x)


#: ⚠️ LE PLAFOND DES PIECES DE GAMEPLAY, ET CE N'EST PLUS UN CLIQUET (BRIEF-0094).
#:
#: Ce qui suivait ici etait une valeur d'attente : `CEILING_OVERSHOOT_MAX = 0,43`
#: figeait le depassement MESURE (0,422 m au pire) du plafond du decor -3,00, en
#: disant que l'arbitrage appartenait au concepteur. Il a ete rendu.
#:
#: La regle a ete relue, pas assouplie. Ce que le plafond protege tient en une
#: phrase : « un volume qui masquerait le combat SANS JAMAIS POUVOIR ETRE
#: TOUCHE ». Une tourelle se tire dessus — la seconde moitie ne la concerne pas,
#: et la premiere non plus : a -2,40 elle reste 2,40 unites SOUS le plan de vol,
#: elle ne peut ni masquer le chasseur ni le heurter. Le decor INERTE, lui, reste
#: sous -3,00 (`cortege.CEILING_Y`, harnais de la coque, inchange).
#:
#: La borne est donc la vraie : celle du moteur. Elle est lue dans
#: `scripts/vfx/cortege_flyby.gd` (`GAMEPLAY_CEILING_Y`) et un test moteur la
#: tient de son cote (`test_no_turret_ever_reaches_the_flight_plane`, qui charge
#: le kit, assemble la piece la plus haute et la pose sur le pire marqueur).
#:
#: ⚠️ Elle est RECOPIEE, et c'est le seul endroit du kit ou une valeur du moteur
#: l'est. Blender ne lit pas le GDScript ; le harnais ci-dessous verifie donc que
#: le fichier moteur porte toujours ce nombre, et echoue si les deux ont derive.
GAMEPLAY_CEILING_Y = -2.40
#: Le fichier qui fait foi. Relu a chaque build : deux ecritures d'une meme cote
#: finissent toujours par diverger si rien ne les confronte.
FLYBY_SOURCE = os.path.join(
    _REPO, "scripts/vfx/cortege_flyby.gd")


def _assert_gameplay_ceiling() -> None:
    """Le plafond recopie ici est-il celui que le moteur applique ?"""
    try:
        with open(FLYBY_SOURCE, encoding="utf-8") as handle:
            source = handle.read()
    except OSError:
        return          # hors du depot : on ne peut rien affirmer, on se tait
    marker = "const GAMEPLAY_CEILING_Y := "
    if marker not in source:
        raise ak.ContractError(
            f"{FLYBY_SOURCE} ne declare plus GAMEPLAY_CEILING_Y : le kit ne peut "
            "plus verifier contre quoi il mesure")
    value = source.split(marker, 1)[1].split("\n", 1)[0].strip()
    if abs(float(value) - GAMEPLAY_CEILING_Y) > 1e-9:
        raise ak.ContractError(
            f"plafond de gameplay : {GAMEPLAY_CEILING_Y} ici, {value} dans "
            f"{os.path.basename(FLYBY_SOURCE)} — les deux ont derive")


def _assert_on_axis(name: str, points: list[tuple],
                    problems: list[str], revolution: bool) -> None:
    """LA PIECE TOURNE-T-ELLE SUR PLACE ?

    ⚠️ LE HARNAIS LE PLUS IMPORTANT DE CE FICHIER, ET CELUI QU'AUCUNE PLANCHE NE
    REMPLACE. Le moteur fait tourner `turret_ring` et tout ce qui est monte dessus
    a 42 deg/s autour de Y. Si le maillage n'est pas centre sur cet axe, la
    tourelle BALAIE EN DECRIVANT UN CERCLE au lieu de pivoter — un defaut qui ne
    se voit ni sur un rendu fixe, ni sur une bbox, ni sur un compte de triangles,
    et qui ne se decouvre qu'en jouant.

    Deux mesures, parce qu'une seule se laisse tromper : le CENTROIDE des sommets
    (qu'un maillage asymetrique deplacerait) ET la boite englobante (qu'une
    symetrie de facade laisserait centree). Les deux doivent tenir au micron.
    """
    if not points:
        problems.append(f"{name} : aucun sommet, l'axe ne peut pas etre verifie")
        return
    # ⚠️ SUR LES POSITIONS UNIQUES, ET C'EST INDISPENSABLE. Le tableau de sommets
    # d'un `.glb` est DEDOUBLE — l'exportateur y recopie un sommet autant de fois
    # qu'il porte de normales, d'UV ou de materiaux differents. Un centroide
    # calcule dessus pese donc les coutures et non la matiere : mesure ici,
    # -1,04e-4 sur un maillage rigoureusement symetrique. La boite englobante,
    # elle, ne s'y trompe jamais — d'ou les deux mesures.
    points = sorted({(round(p[0], 6), round(p[1], 6), round(p[2], 6))
                     for p in points})
    measures = [("centroide x", sum(p[0] for p in points) / len(points)),
                ("bbox x", (min(p[0] for p in points)
                            + max(p[0] for p in points)) * 0.5)]
    if revolution:
        # ⚠️ SEULE LA COURONNE EST UN SOLIDE DE REVOLUTION. Le bloc, lui, DOIT
        # etre dissymetrique en Z : il a un masque a l'avant et un bloc de recul
        # a l'arriere, c'est ce qui fait qu'on lit ou il regarde. Lui demander
        # d'etre centre en Z reviendrait a lui interdire d'avoir un avant.
        measures += [("centroide z", sum(p[2] for p in points) / len(points)),
                     ("bbox z", (min(p[2] for p in points)
                                 + max(p[2] for p in points)) * 0.5)]
    for label, value in measures:
        if abs(value) > 1e-4:
            problems.append(
                f"{name} : {label} = {value:+.6f} au lieu de 0 — l'origine n'est "
                "pas sur l'axe de rotation, la tourelle balaierait en decrivant "
                "un cercle au lieu de pivoter sur place")


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
    seen_area: dict[str, float] = {}
    built_area: dict[str, float] = {}
    total_area = 0.0
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
            for k in range(0, len(tri_indices) - 2, 3):
                ia, ib, ic = (tri_indices[k], tri_indices[k + 1],
                              tri_indices[k + 2])
                tris.append((base + ia, base + ib, base + ic))
                pa = Vector(points[ia])
                area = (Vector(points[ib]) - pa).cross(
                    Vector(points[ic]) - pa).length * 0.5
                total_area += area
                area_by_material[material] = \
                    area_by_material.get(material, 0.0) + area
                # ⚠️ L'AIRE VUE ET L'AIRE ASSEMBLEE, comptees a part. La jupe
                # enterree du socle pese lourd et ne rend pas un pixel : melangee
                # au reste, elle gonflerait la part « structure » et la
                # repartition 80/15/5 deviendrait un chiffre sans rapport avec
                # l'ecran. Est « vue » ce qui est au-dessus du plan d'assise.
                cy = (points[ia][1] + points[ib][1] + points[ic][1]) / 3.0
                oy = ASSEMBLY_OFFSET[name][1]
                copies = ASSEMBLY_COPIES[name]
                built_area[material] = built_area.get(material, 0.0) \
                    + area * copies
                # ⚠️ DEUX CONDITIONS ET NON UNE. « Au-dessus de l'assise » ne
                # suffit pas : le fond de la couronne et le dessous du bloc sont
                # au-dessus de l'assise et ne rendent pas un pixel. La camera du
                # jeu plonge a 70 deg — une face qui regarde le pont ne lui est
                # JAMAIS presentee. Sans ce second filtre, 14 m2 de dessous
                # entraient dans une repartition censee decrire l'ecran.
                normal = (Vector(points[ib]) - pa).cross(
                    Vector(points[ic]) - pa)
                downward = normal.length > 1e-12 and \
                    normal.normalized().y < -0.5
                if cy + oy > -0.02 and copies and not downward:
                    seen_area[material] = \
                        seen_area.get(material, 0.0) + area * copies
                    total_seen += area * copies
        part_points[name] = pts
        if uvs:
            density[name] = _texel_density(pts, uvs, tris)
        # ⚠️ Le `.glb` est DANS LE REPERE DU KIT : la chaine `_AUTHOR_FIX` puis
        # `export_yup` rend l'identite, et `_assert_axis_chain()` le reverifie sur
        # trois temoins asymetriques.
        if name in ("turret_ring", "turret_body"):
            _assert_on_axis(name, pts, problems,
                            revolution=name == "turret_ring")
        triangles_total += triangles
        stats[name] = {"triangles": triangles,
                       "min": tuple(lo), "max": tuple(hi),
                       "size": tuple(hi[a] - lo[a] for a in range(3))}

    # --- LES COTES DU BRIEF, RELEVEES SUR LE BINAIRE ----------------------
    for name, axis, want, label in (
            ("turret_pad", 0, PAD_D, "diametre du socle"),
            ("turret_pad", 2, PAD_D, "diametre du socle (Z)"),
            ("turret_ring", 0, RING_D, "diametre de la couronne"),
            ("turret_ring", 1, RING_H, "hauteur de la couronne"),
            ("turret_barrel", 2, BARREL_LEN, "longueur de canon")):
        piece = stats.get(name)
        if piece is None:
            continue
        if abs(piece["size"][axis] - want) > 1e-3:
            problems.append(
                f"{name} : {label} = {piece['size'][axis]:.4f} m au lieu de "
                f"{want:.2f} m (cote du brief)")
    body = stats.get("turret_body")
    if body is not None:
        crest = BODY_BASE + body["max"][1]
        if abs(crest - TURRET_H) > 1e-3:
            problems.append(
                f"hauteur totale {crest:.4f} m au lieu de {TURRET_H:.2f} m "
                "(cote du brief)")
        if body["size"][1] > body["size"][0] or body["size"][1] > body["size"][2]:
            problems.append(
                "turret_body : il est plus haut que large ou que long — le brief "
                "demande un bloc RECTANGULAIRE TRAPU, surtout pas une tour")
    # La largeur hors-tout des deux canons : la cote 1,20 m du brief.
    gun_span = BARREL_GAUGE + 2.0 * BARREL_R
    if abs(gun_span - 1.20) > 1e-6:
        problems.append(f"largeur des deux canons {gun_span:.3f} m au lieu de 1,20")
    # ⚠️ La borne n'est plus la largeur du BLOC mais l'ouverture du MASQUE, et
    # elle porte sur le MANCHON de recul, pas sur le tube : c'est le manchon qui
    # loge dans le creux. Mesuree sur la largeur du bloc, la borne laissait
    # passer un ecartement ou le manchon traversait la paroi du masque.
    reach = BARREL_GAUGE_MAX * 0.5 + BARREL_SLEEVE
    if reach > MANTLET_HX - 0.02:
        problems.append(
            f"a l'ecartement maximal ({BARREL_GAUGE_MAX:.2f} m) le manchon atteint "
            f"{reach:.3f} m alors que le masque n'ouvre qu'a {MANTLET_HX:.2f} m : "
            "la variete percerait la paroi du creux")
    for label, gauge in ((name, g) for name, _s, _b, g, *_r in FAMILIES):
        if gauge > BARREL_GAUGE_MAX + 1e-9:
            problems.append(
                f"la famille « {label} » demande un ecartement de {gauge:.2f} m, "
                f"au-dela du maximum {BARREL_GAUGE_MAX:.2f} m")
    # L'emprise du kit et celle avec laquelle la coque a pose ses marqueurs.
    if abs(FOOTPRINT_R - cortege.TURRET_FOOTPRINT_R) > 1e-9:
        problems.append(
            f"emprise du kit {FOOTPRINT_R:.3f} m contre "
            f"{cortege.TURRET_FOOTPRINT_R:.3f} m echantillonnee par la coque : "
            "les deux valeurs ont derive, l'assise du marqueur est fausse")
    # L'œil est-il coince entre les deux manchons de recul ?
    eye_gap = BARREL_GAUGE * 0.5 - BARREL_SLEEVE - EYE_R
    if eye_gap < 0.01:
        problems.append(
            f"l'œil ({EYE_R:.2f} m de rayon) touche le manchon du canon : il ne "
            f"reste que {eye_gap:+.3f} m entre les deux au fond du masque")
    # L'œil : la regle DURE des 25 pct.
    eye_ratio = 2.0 * EYE_R / TURRET_H
    if eye_ratio > 0.25:
        problems.append(
            f"l'œil fait {100 * eye_ratio:.1f} pct de la tourelle — le brief pose "
            "25 pct comme regle dure")
    # L'emprise tient-elle dans la reservation de la coque ?
    if FOOTPRINT_R > min(cortege.PAD_RADIUS) - 0.05:
        problems.append(
            f"emprise du kit {FOOTPRINT_R:.2f} m > reservation minimale "
            f"{min(cortege.PAD_RADIUS):.2f} m de la coque — le garde mutuel "
            "tourelle/pont de BRIEF-0092 arbitrerait sur une emprise fausse")

    # --- LA ROTATION PASSE-T-ELLE AU-DESSUS DE L'APPAREILLAGE ? -----------
    # ⚠️ MESURE NEUVE, ET ELLE N'A PAS D'EQUIVALENT AILLEURS DANS LE DEPOT. Le
    # brief prevoit un appareillage POSE SUR LE SOCLE et un bloc QUI TOURNE
    # au-dessus, a 42 deg/s : les deux se recouvrent forcement en plan, et rien
    # d'autre que leur denivele ne les separe. Un coffret trop haut de 5 cm ne se
    # voit sur aucune planche — il se voit en jeu, une fois par tour, quand le
    # bloc le traverse. La mesure se fait par TRANCHES DE 2 cm en hauteur : c'est
    # la seule façon de ne pas comparer un rayon a une hauteur qu'il n'atteint
    # jamais. Le rayon tournant est pris a l'ecartement MAXIMAL des canons.
    clearance, clearance_at = math.inf, ""
    slabs: dict[int, list[float]] = {}
    static: dict[int, list[float]] = {}
    for name, points in part_points.items():
        if name == "turret_barrel_short":
            continue
        rotates = name in ("turret_ring", "turret_body", "turret_barrel")
        offsets = [ASSEMBLY_OFFSET[name]]
        if name == "turret_barrel":
            offsets = [(side * BARREL_GAUGE_MAX * 0.5, BARREL_Y, BARREL_Z)
                       for side in (-1.0, 1.0)]
        for ox, oy, oz in offsets:
            for px, py, pz in points:
                y = py + oy
                if rotates:
                    radius = math.hypot(px + ox, pz + oz)
                else:
                    # Pose a `FITTING_R` : le Z local est radial, le X tangentiel.
                    radius = math.hypot(FITTING_R + pz, px) \
                        if name in ("turret_service_box", "turret_pipe") \
                        else math.hypot(px, pz)
                bucket = int(math.floor(y / 0.02))
                target = slabs if rotates else static
                target.setdefault(bucket, []).append(radius)
    for bucket, radii in sorted(slabs.items()):
        near = static.get(bucket)
        if not near:
            continue
        gap = min(near) - max(radii)
        if gap < clearance:
            clearance = gap
            clearance_at = f"Y = {bucket * 0.02:+.2f} m"
    if clearance < 0.05:
        problems.append(
            f"degagement de rotation {clearance:+.3f} m a {clearance_at} : le "
            "bloc ou un canon passe sur une piece posee sur le socle. Le defaut "
            "ne se voit qu'en jeu, une fois par tour")

    # --- LES DIX-SEPT EMPLACEMENTS, MESURES SUR LA COQUE -------------------
    seats: list[tuple[str, float, float, float, float]] = []
    overshoot = 0.0
    for number, (s, x) in enumerate(cortege.TURRETS, start=1):
        seat, low = turret_seat_y(s, x)
        crest = seat + TURRET_H
        seats.append((f"Turret_{number:02d}", seat, low, seat - low, crest))
        overshoot = max(overshoot, crest - cortege.CEILING_Y)
        if seat - low > PAD_BURIED - 0.10:
            problems.append(
                f"Turret_{number:02d} : denivele {seat - low:.3f} m sous "
                f"l'emprise, la jupe de {PAD_BURIED:.2f} m ne mord plus la peau "
                "du cote bas")
    _assert_gameplay_ceiling()
    summit = max(row[4] for row in seats)
    if summit > GAMEPLAY_CEILING_Y:
        problems.append(
            f"la tourelle la plus haute culmine a {summit:.3f}, au-dessus du "
            f"plafond des PIECES DE GAMEPLAY ({GAMEPLAY_CEILING_Y:.2f}) — c'est "
            "la vraie borne depuis BRIEF-0094, et un test moteur la tient aussi")

    # --- LE BALAYAGE DES CANONS CROISE-T-IL UN HANGAR ? --------------------
    # ⚠️ Cette mesure N'EXISTAIT PAS avant ce lot, parce qu'avant ce lot les
    # tourelles n'avaient pas de canon. Le garde de BRIEF-0092 arbitre sur des
    # SOCLES ; un tube de 2,90 m qui tourne balaie trois fois plus loin.
    sweep = BARREL_Z + BARREL_LEN
    bay_sweep: list[tuple[str, str, float]] = []
    for number, (ts, tx) in enumerate(cortege.TURRETS, start=1):
        for index, (bs, bx) in enumerate(cortege.BAYS, start=1):
            dx = max(abs(tx - bx) - cortege.BAY_HALF_X - cortege.BAY_COAMING_W, 0.0)
            ds = max(abs(ts - bs) - cortege.BAY_HALF_S - cortege.BAY_COAMING_W, 0.0)
            distance = math.hypot(dx, ds)
            if distance < sweep:
                bay_sweep.append((f"Turret_{number:02d}", f"Bay_{index:02d}",
                                  sweep - distance))

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
    assembled = sum(stats.get(name, {}).get("triangles", 0) * ASSEMBLY_COPIES[name]
                    for name in PART_NAMES)
    if assembled > TRI_BUDGET_ASSEMBLED:
        problems.append(
            f"{assembled} triangles par tourelle assemblee > budget "
            f"{TRI_BUDGET_ASSEMBLED}")
    level = assembled * len(cortege.TURRETS)
    if level > TRI_BUDGET_LEVEL:
        problems.append(f"{level} triangles pour le niveau > budget "
                        f"{TRI_BUDGET_LEVEL}")

    if problems:
        raise ak.ContractError(
            "CONTRAT ROMPU — turret_kit\n" + "\n".join(f"  - {p}" for p in problems))

    return {
        "parts": stats,
        "primitives": (prims_uv, prims_tan, prims_total),
        "triangles": triangles_total,
        "assembled": assembled,
        "level": level,
        "materials": sorted(used_materials),
        "area_by_material": area_by_material,
        "seen_by_material": seen_area,
        "built_by_material": built_area,
        "total_built": sum(built_area.values()),
        "total_area": total_area,
        "total_seen": total_seen,
        "density": density,
        "seats": seats,
        "clearance": (clearance, clearance_at),
        "overshoot": overshoot,
        "bay_sweep": bay_sweep,
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
    print("\n--- turret_kit : mesures relevees sur le .glb PRODUIT ---")
    print(f"  {'piece':<22} {'tri':>5} {'x':>2}  {'bbox (l x h x L)':>24}")
    for name in PART_NAMES:
        s = report["parts"][name]
        print(f"  {name:<22} {s['triangles']:>5} {ASSEMBLY_COPIES[name]:>2}  "
              f"{s['size'][0]:7.2f} x {s['size'][1]:5.2f} x {s['size'][2]:7.2f}")
    print(f"  {'TOTAL (kit unique)':<22} {report['triangles']:>5}")
    print(f"  tourelle assemblee : {report['assembled']} tri / "
          f"{TRI_BUDGET_ASSEMBLED} ; dix-sept tourelles : {report['level']} / "
          f"{TRI_BUDGET_LEVEL}")

    print("\n  TABLE DES EMPRISES — c'est elle qui dit au moteur ou poser chaque")
    print("  piece. Repere local du marqueur `Turret_NN` (X lateral, Y haut, "
          "Z survol, +Z = proue).")
    # ⚠️ L'apostrophe sort de la f-string : une expression de f-string ne peut pas
    # contenir d'antislash avant Python 3.12 ; Blender 4.5 embarquait 3.11, la 5.2
    # embarque 3.13 — la contrainte est levee, la formulation reste valable.
    entete = "position d'assemblage"
    print(f"    {'piece':<22} {'parent':<10} {entete:<28} {'copies'}")
    plan = (
        ("turret_pad", "marqueur", "(0, 0, 0)", "1"),
        ("turret_anchor_skirt", "marqueur", "(0, 0, 0)", "0 ou 1"),
        ("turret_service_box", "marqueur",
         f"yaw t, r = {FITTING_R:.2f}, y = {PAD_SHELF_Y:+.2f}", "0, 1 ou 2"),
        ("turret_pipe", "marqueur",
         f"yaw t, r = {FITTING_R:.2f}, y = {PAD_SHELF_Y:+.2f}", "0 ou 1"),
        ("turret_ring", "ROTATEUR", f"(0, {RING_BASE:+.2f}, 0)", "1"),
        ("turret_body", "ROTATEUR", f"(0, {BODY_BASE:+.2f}, 0)", "1"),
        ("turret_barrel*", "ROTATEUR",
         f"(+/-e/2, {BARREL_Y:+.2f}, {BARREL_Z:+.2f})", "2"),
    )
    for name, parent, where, copies in plan:
        print(f"    {name:<22} {parent:<10} {where:<28} {copies}")
    print(f"    ROTATEUR : Node3D a (0, 0, 0) du marqueur, rotation Y libre "
          f"(42 deg/s). e = ecartement, {BARREL_GAUGE:.2f} m par defaut, "
          f"{BARREL_GAUGE_MAX:.2f} m au maximum.")

    print("\n  LES TROIS FAMILLES — variete par ASSEMBLAGE SEUL, sans reforge")
    print(f"    {'famille':<14} {'jupe':<5} {'canon':<21} {'ecart':>6} "
          f"{'coffrets':<16} {'conduites'}")
    for name, skirt, barrel, gauge, boxes, angles, pipe, pipe_a in FAMILIES:
        angle_txt = "/".join(f"{a:.0f}" for a in angles[:boxes])
        print(f"    {name:<14} {'oui' if skirt else 'non':<5} {barrel:<21} "
              f"{gauge:>6.2f} {f'{boxes} a {angle_txt} deg':<16} "
              f"{f'1 a {pipe_a:.0f} deg' if pipe else 'aucune'}")

    print(f"\n  cotes du brief, relevees sur le binaire : socle "
          f"{report['parts']['turret_pad']['size'][0]:.2f} m de diametre ; "
          f"couronne {report['parts']['turret_ring']['size'][0]:.2f} m x "
          f"{report['parts']['turret_ring']['size'][1]:.2f} m ; canon "
          f"{report['parts']['turret_barrel']['size'][2]:.2f} m (court "
          f"{report['parts']['turret_barrel_short']['size'][2]:.2f} m) ; "
          f"largeur des deux canons {BARREL_GAUGE + 2 * BARREL_R:.2f} m ; "
          f"hauteur totale {TURRET_H:.2f} m")
    print(f"  la couronne emerge de {RING_TOP - PAD_RIM_H:.2f} m au-dessus du "
          f"bourrelet du socle : elle y est ENFONCEE de "
          f"{RING_H - (RING_TOP - PAD_RIM_H):.2f} m")
    print(f"  les tubes debordent de {BARREL_Z + BARREL_LEN - PAD_R:.2f} m au-dela "
          f"du socle (rayon {PAD_R:.2f} m) ; portee hors-tout "
          f"{BARREL_Z + BARREL_LEN:.2f} m depuis l'axe ; culasse au FOND du "
          f"masque ({BARREL_Z:+.2f}), pas sur la face avant ({BODY_Z1:+.2f})")
    gap, where = report["clearance"]
    print(f"  degagement de rotation mesure : {gap:+.3f} m au plus serre "
          f"({where}) — bloc et canons a l'ecartement maximal contre coffrets, "
          f"conduites et socle, par tranches de 2 cm")
    print(f"  œil : {2 * EYE_R:.2f} m pour une tourelle de {TURRET_H:.2f} m, soit "
          f"{100 * 2 * EYE_R / TURRET_H:.1f} pct (regle dure : 25 pct)")
    print(f"  emprise hors-tout posee sur la peau : {FOOTPRINT_R:.2f} m de rayon, "
          f"dans la reservation minimale {min(cortege.PAD_RADIUS):.2f} m")

    print("\n  LES DIX-SEPT EMPLACEMENTS, mesures sur la coque livree")
    print(f"    {'marqueur':<12} {'assise':>8} {'bas':>8} {'denivele':>9} "
          f"{'sommet':>8} {'plafond':>9}")
    for name, seat, low, deniv, crest in report["seats"]:
        flag = "  DEPASSE" if crest > cortege.CEILING_Y else ""
        print(f"    {name:<12} {seat:>8.3f} {low:>8.3f} {deniv:>9.3f} "
              f"{crest:>8.3f} {cortege.CEILING_Y - crest:>9.3f}{flag}")
    over = [n for n, _, _, _, c in report["seats"] if c > cortege.CEILING_Y]
    summit = max(c for _, _, _, _, c in report["seats"])
    print(f"    denivele max {max(d for _, _, _, d, _ in report['seats']):.3f} m, "
          f"absorbe par une jupe de {PAD_BURIED:.2f} m")
    print(f"    {len(over)} tourelles sur {len(report['seats'])} montent au-dessus "
          f"du plafond du DECOR INERTE ({cortege.CEILING_Y:+.2f}), de "
          f"{report['overshoot']:.3f} m au pire — et c'est ACTE : une tourelle se "
          "tire dessus.")
    print(f"    la plus haute culmine a {summit:+.3f}, soit "
          f"{GAMEPLAY_CEILING_Y - summit:.3f} m sous le plafond des PIECES DE "
          f"GAMEPLAY ({GAMEPLAY_CEILING_Y:+.2f}) et {-summit:.2f} unites sous le "
          "plan de vol")
    if report["bay_sweep"]:
        print("\n  ⚠️ BALAYAGE DES CANONS AU-DESSUS D'UN PONT D'ENVOL (mesure "
              "neuve : avant ce lot les tourelles n'avaient pas de canon)")
        for turret, bay, depth in report["bay_sweep"]:
            print(f"    {turret} balaie {depth:.2f} m au-dela du coaming de {bay}")

    print(f"\n  primitives : {report['primitives'][0]}/{report['primitives'][2]} "
          f"TEXCOORD_0, {report['primitives'][1]}/{report['primitives'][2]} TANGENT")
    print("  densite de texels (valeurs singulieres, triangle par triangle), "
          f"cible {TEXELS_PER_METER:.3f} tuile/m ({1 / TEXELS_PER_METER:.2f} m/tuile)")
    for name in PART_NAMES:
        d = report["density"].get(name)
        if not d:
            continue
        print(f"    {name:<22} {d['tiles_per_m_min']:.3f} a "
              f"{d['tiles_per_m_max']:.3f}, moyenne {d['tiles_per_m_mean']:.3f} "
              f"t/m ({d['m_per_tile_mean']:.2f} m/tuile), aniso "
              f"{d['anisotropy_max']:.2f}")

    print("\n  repartition en AIRE, relevee sur le .glb — kit brut, tourelle "
          "ASSEMBLEE, et ce qui en est VU")
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


# ==========================================================================
# Planche de recette — `--plate`
# ==========================================================================
# ADR-0006 : un livrable de la forge n'est pas valide tant qu'il n'a pas ete rendu
# et REGARDE. La premiere vignette EST le test d'acceptation du brief : une
# tourelle et un hangar dans le MEME cadre, en noir et blanc, emissifs coupes.
# Deux vignettes separees ne prouveraient rien — c'est la COMPARAISON qui est le
# test.

TILE_W = 1440
SCENE_H = 620
CLOSE_H = 660
FAMILY_H = 560
ELEV_H = 400
UV_H = 420
SAMPLES = 32

BACKDROP = baykit.BACKDROP
AMBIENT = baykit.AMBIENT
GAME_LIGHTS = baykit.GAME_LIGHTS
CAM_POS = cortege.CAM_POS
CAM_FORWARD = cortege.CAM_FORWARD
CAM_UP = cortege.CAM_UP
CAM_FOV_V = cortege.CAM_FOV_V

#: La paire qui sert de test d'acceptation — la MEME que BRIEF-0091, prise par
#: l'autre bout. Elles sont a 8 m l'une de l'autre, du meme bord, donc dans le
#: meme cadre a la camera du jeu.
ACCEPTANCE_BAY = 7          # Bay_07, s = 436, x = -9,30
ACCEPTANCE_TURRET = 14      # Turret_14, s = 428, x = -9,40


def _to_blender(v: Vector) -> Vector:
    return Vector((v.x, -v.z, v.y))


def _plate_reset() -> None:
    baykit._plate_reset()


def _plate_lights() -> None:
    baykit._plate_lights()


def _plate_camera(name, position, forward, up, fov, ortho=None):
    return baykit._plate_camera(name, position, forward, up, fov, ortho)


def _label(*args, **kwargs) -> None:
    baykit._label(*args, **kwargs)


def _render(path: str, width: int, height: int) -> None:
    baykit._render(path, width, height)


def _import(path: str, name: str, position: Vector, yaw: float = 0.0) -> list:
    return baykit._import(path, name, position, yaw)


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


def _assemble_turret(centre: Vector, family: int, aim: float = 0.0) -> list:
    """Monte UNE tourelle a `centre` (Y = assise), selon la famille demandee.

    C'est la SEULE façon de juger le lot : le kit livre huit pieces, et aucune ne
    prouve quoi que ce soit seule. `aim` est l'azimut de la tourelle — c'est lui
    que le moteur anime a 42 deg/s, et il ne fait tourner QUE le rotateur.
    """
    name, skirt, barrel, gauge, boxes, angles, pipe, pipe_a = FAMILIES[family]
    del name
    placed: list = []
    if skirt:
        placed += _place("turret_anchor_skirt", centre)
    placed += _place("turret_pad", centre)
    for k in range(boxes):
        a = math.radians(angles[k])
        placed += _place(
            "turret_service_box",
            centre + Vector((FITTING_R * math.sin(a), PAD_SHELF_Y,
                             FITTING_R * math.cos(a))), -a)
    if pipe:
        a = math.radians(pipe_a)
        placed += _place(
            "turret_pipe",
            centre + Vector((FITTING_R * math.sin(a), PAD_SHELF_Y,
                             FITTING_R * math.cos(a))), -a)
    # Le ROTATEUR : couronne, bloc et tubes tournent en un bloc autour de l'axe Y
    # qui passe par l'origine de la couronne.
    ca, sa = math.cos(aim), math.sin(aim)

    def spin(local: Vector) -> Vector:
        return Vector((local.x * ca + local.z * sa, local.y,
                       -local.x * sa + local.z * ca))

    for part, local in (("turret_ring", Vector((0.0, RING_BASE, 0.0))),
                        ("turret_body", Vector((0.0, BODY_BASE, 0.0)))):
        placed += _place(part, centre + spin(local), aim)
    for side in (-1.0, 1.0):
        placed += _place(
            barrel,
            centre + spin(Vector((side * gauge * 0.5, BARREL_Y, BARREL_Z))),
            aim)
    return placed


def _game_shift(aim_s: float) -> float:
    return baykit._game_shift(aim_s)


def _look_at(eye: Vector, target: Vector) -> tuple[Vector, Vector]:
    """(avant, haut) d'une camera qui vise `target` depuis `eye`, SANS ROULIS.

    ⚠️ LA FORMULE EMPLOYEE JUSQU'ICI RENDAIT UN « HAUT » HORIZONTAL. Elle
    s'ecrivait `(avant x X) x avant`, ce qui developpe en `X - avant (avant . X)`
    : des que la visee n'a pas de composante en X — le cas exact de la vue de
    famille, alignee sur l'axe — elle rend X, c'est-a-dire une camera COUCHEE A
    90 deg. Le rendu montrait le socle DEBOUT COMME UN MUR et deux tourelles sur
    trois hors cadre, et il fallait le regarder pour s'en apercevoir : aucune
    mesure de ce fichier ne cadre une image (ADR-0006, dans les deux sens).

    Le haut se PROJETTE : on retire de la verticale du monde sa part le long de
    l'axe de visee. Et on verifie qu'il pointe encore vers le haut, sans quoi la
    faute se reinstalle en silence a la prochaine vue.

    ⚠️ La meme expression vit encore dans `build_bay_kit._tile_close()` (hors
    perimetre de ce brief) : elle y est moins visible parce que la visee y porte
    du X, mais elle y roule la camera d'autant. A signaler au concepteur.
    """
    forward = (target - eye).normalized()
    world_up = Vector((0.0, 1.0, 0.0))
    up = world_up - forward * forward.dot(world_up)
    if up.length < 1e-6:
        raise ak.ContractError(
            "camera a la verticale : le haut de l'image est indefini")
    up.normalize()
    if up.y <= 0.0:
        raise ak.ContractError("le haut de la camera pointe vers le bas")
    return forward, up


def _tile_acceptance(path: str, report: dict, greyscale: bool) -> None:
    """LE TEST D'ACCEPTATION : une tourelle et un hangar dans le MEME cadre.

    « En noir et blanc, tous emissifs coupes, on distingue immediatement une
    tourelle d'un hangar. » Le meme cadre est rendu deux fois — en valeurs, puis
    en couleur — pour que l'on voie du meme coup ce que la silhouette fait seule
    et ce que l'emissif AJOUTE. S'il fallait la couleur, la premiere image le
    dirait.
    """
    _plate_reset()
    ts, tx = cortege.TURRETS[ACCEPTANCE_TURRET - 1]
    bs, _ = cortege.BAYS[ACCEPTANCE_BAY - 1]
    shift = _game_shift(0.5 * (ts + bs))
    decor = _import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    bay = baykit._assemble_bay(ACCEPTANCE_BAY, shift)
    seat, _ = turret_seat_y(ts, tx)
    turret = _assemble_turret(Vector((tx, seat, -ts + shift)), 2,
                              aim=math.radians(-28.0))
    fighter = _import(baykit.FIGHTER, "Player", Vector((0.0, 0.0, 3.4)))
    if greyscale:
        baykit._to_greyscale(decor + bay + turret + fighter)
    _plate_lights()
    camera = _plate_camera("game", _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                           _to_blender(CAM_UP), CAM_FOV_V)
    if greyscale:
        _label(camera, "TEST D'ACCEPTATION — NOIR ET BLANC, EMISSIFS COUPES : "
                       "tourelle (Turret_14) et hangar (Bay_07) dans le meme cadre",
               -0.97, 0.88, 0.040, TILE_W, SCENE_H, (1.0, 0.88, 0.55))
        _label(camera, "la silhouette seule doit trancher : le hangar CREUSE "
                       "(un cadre vide), la tourelle DEPASSE — deux tubes a "
                       f"{BARREL_Z + BARREL_LEN:.2f} m de l'axe, soit "
                       f"{BARREL_Z + BARREL_LEN - PAD_R:.2f} m au-dela du socle",
               -0.97, 0.79, 0.031, TILE_W, SCENE_H)
    else:
        _label(camera, "LE MEME CADRE, EN COULEUR — ce que l'emissif AJOUTE a une "
                       "fonction deja lisible en geometrie",
               -0.97, 0.88, 0.040, TILE_W, SCENE_H, (1.0, 0.88, 0.55))
        _label(camera, "un seul emissif sur toute la tourelle : l'œil, "
                       f"{2 * EYE_R:.2f} m pour {TURRET_H:.2f} m de haut, au fond "
                       f"du masque ({100 * 2 * EYE_R / TURRET_H:.0f} pct, regle "
                       "dure 25). Ni socle lumineux, ni couronne.",
               -0.97, 0.79, 0.031, TILE_W, SCENE_H)
    _label(camera, "camera de graybox.tscn sans retouche (0, 14, 5), FOV 62, "
                   "70 deg sous l'horizontale ; Specter-9 reel a sa place de jeu",
           -0.97, -0.91, 0.029, TILE_W, SCENE_H, (0.72, 0.84, 1.0))
    _render(path, TILE_W, SCENE_H)


def _tile_three_quarter(path: str, report: dict) -> None:
    """LA TOURELLE SEULE, DE TROIS QUARTS — ce que la camera du jeu ne montre pas.

    La vue de jeu plonge a 70 deg : elle dit si la piece se LIT, pas comment elle
    est faite. Ce cadrage-ci dit le reste — la couronne enfoncee, le masque creuse,
    les chanfreins qui portent la lumiere cle.
    """
    _plate_reset()
    ts, tx = cortege.TURRETS[ACCEPTANCE_TURRET - 1]
    shift = _game_shift(ts)
    _import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    seat, _ = turret_seat_y(ts, tx)
    centre = Vector((tx, seat, -ts + shift))
    _assemble_turret(centre, 1, aim=math.radians(-34.0))
    _plate_lights()
    eye = centre + Vector((4.6, 3.2, 5.4))
    target = centre + Vector((0.0, 0.78, 0.45))
    forward, up = _look_at(eye, target)
    camera = _plate_camera("tq", _to_blender(eye), _to_blender(forward),
                           _to_blender(up), math.radians(34.0))
    _label(camera, "TROIS QUARTS, TOURELLE SEULE (famille B) — un canon, pas un "
                   "jeton",
           -0.97, 0.89, 0.040, TILE_W, CLOSE_H, (1.0, 0.88, 0.55))
    _label(camera, f"socle {PAD_D:.2f} m ; couronne {RING_D:.2f} m ENFONCEE de "
                   f"{RING_H - (RING_TOP - PAD_RIM_H):.2f} m dans la cuvette ; "
                   f"bloc trapu {2 * BODY_HX:.2f} x {BODY_Z1 - BODY_Z0:.2f} x "
                   f"{BODY_H:.2f} ; tubes de "
                   f"{BARREL_LEN:.2f} m logés dans un masque creusé de "
                   f"{MANTLET_DEPTH:.2f} m",
           -0.97, 0.80, 0.029, TILE_W, CLOSE_H)
    _label(camera, "le budget est passe dans les chanfreins et la profondeur — "
                   f"{report['assembled']} tri assembles pour "
                   f"{TRI_BUDGET_ASSEMBLED} autorises, aucun rivet",
           -0.97, -0.90, 0.029, TILE_W, CLOSE_H, (0.72, 0.84, 1.0))
    _render(path, TILE_W, CLOSE_H)


def _tile_families(path: str, report: dict) -> None:
    """TROIS EXEMPLAIRES DIFFERENTS COTE A COTE — le livrable « variete ».

    Dix-sept tourelles identiques se liraient comme dix-sept fois la meme. Cette
    vignette est le SEUL moyen de juger si le kit tient sa promesse : les trois
    sont faites des memes huit pieces, aucune geometrie ne les separe.
    """
    _plate_reset()
    spacing = 7.2
    for k in range(3):
        _assemble_turret(Vector(((k - 1) * spacing, 0.0, 0.0)), k,
                         aim=math.radians((-32.0, 14.0, -8.0)[k]))
    baykit._plane_slab(0.0, spacing * 1.6, 4.2, 0.12, (0.95, 0.72, 0.28), 0.9)
    _plate_lights()
    eye = Vector((0.0, 5.2, 13.6))
    target = Vector((0.0, 0.85, 0.0))
    forward, up = _look_at(eye, target)
    camera = _plate_camera("fam", _to_blender(eye), _to_blender(forward),
                           _to_blender(up), math.radians(38.0))
    _label(camera, "TROIS EXEMPLAIRES DIFFERENTS, MEMES HUIT PIECES — la variete "
                   "est un livrable, pas un bonus",
           -0.97, 0.89, 0.038, TILE_W, FAMILY_H, (1.0, 0.88, 0.55))
    for k, (name, skirt, barrel, gauge, boxes, angles, pipe, _a) in \
            enumerate(FAMILIES):
        _label(camera, name, -0.88 + 0.60 * k, -0.62, 0.034, TILE_W, FAMILY_H,
               (0.72, 0.84, 1.0))
        _label(camera,
               f"{'jupe' if skirt else 'sans jupe'} · "
               f"{'canon court' if 'short' in barrel else 'canon long'} · "
               f"ecart {gauge:.2f} · {boxes} coffret(s)"
               f"{' · conduites' if pipe else ''}",
               -0.88 + 0.60 * k, -0.72, 0.022, TILE_W, FAMILY_H)
        del angles
    _label(camera, "le moteur n'a besoin d'AUCUNE geometrie nouvelle : jupe "
                   "presente ou non, deux longueurs de tube, ecartement libre, "
                   "coffrets et conduites a l'angle voulu",
           -0.97, -0.89, 0.026, TILE_W, FAMILY_H)
    _render(path, TILE_W, FAMILY_H)


def _tile_elevation(path: str, report: dict) -> None:
    """LE KIT SEUL, ELEVATION — les cotes du brief, et le plafond qu'elles ratent.

    Trois plans : l'assise (ambre), le plafond du decor (rouge), et le sommet
    atteint (vert). C'est la seule image qui montre le conflit mesure entre la
    hauteur demandee (1,70 m) et le degagement offert par la coque sous les
    tourelles de crete (1,27 m au pire). L'emplacement montre est celui que la
    MESURE designe comme le plus serre, pas un numero ecrit a la main.
    """
    _plate_reset()
    # ⚠️ L'EMPLACEMENT LE PLUS SERRE EST CHOISI PAR MESURE, pas par son numero :
    # une ligne de `TURRETS` qui bouge deplacerait le pire cas, et la vignette
    # illustrerait alors un conflit qui n'est plus le bon.
    worst = max(report["seats"], key=lambda row: row[1])
    tightest, seat = worst[0], worst[1]
    over = sum(1 for row in report["seats"] if row[4] > cortege.CEILING_Y)
    _assemble_turret(Vector((0.0, 0.0, 0.0)), 1, aim=0.0)
    baykit._plane_slab(0.0, 0.02, 5.6, 0.10, (0.95, 0.72, 0.28), 2.0)
    baykit._plane_slab(cortege.CEILING_Y - seat, 0.02, 5.6, 0.10,
                       (0.90, 0.32, 0.26), 2.0)
    baykit._plane_slab(TURRET_H, 0.02, 1.9, 0.10, (0.72, 0.86, 0.60), 2.0,
                       centre_z=-3.2)
    _plate_lights()
    camera = _plate_camera(
        "elev", _to_blender(Vector((26.0, 0.85, 0.4))),
        _to_blender(Vector((-1.0, 0.0, 0.0))), _to_blender(Vector((0.0, 1.0, 0.0))),
        math.radians(30.0), ortho=6.4)
    _label(camera, "ELEVATION DE TRIBORD (proue a droite) — assise (ambre) 0,00 ; "
                   f"sommet (vert) +{TURRET_H:.2f} ; plafond du decor (rouge) "
                   f"{cortege.CEILING_Y - seat:+.2f} sous {tightest}",
           -0.985, 0.87, 0.048, TILE_W, ELEV_H, (1.0, 0.88, 0.55))
    _label(camera, f"{over} des {len(report['seats'])} emplacements montent "
                   f"au-dessus du plafond du DECOR ({cortege.CEILING_Y:+.2f}) : "
                   f"{TURRET_H:.2f} m demandes pour "
                   f"{cortege.CEILING_Y - seat:.2f} m offerts. ACTE au "
                   f"BRIEF-0094 — la borne des pieces de GAMEPLAY est "
                   f"{GAMEPLAY_CEILING_Y:+.2f}, et un test moteur la tient.",
           -0.985, -0.86, 0.035, TILE_W, ELEV_H)
    _render(path, TILE_W, ELEV_H)


def _tile_uv(path: str, report: dict) -> None:
    _plate_reset()
    ts, tx = cortege.TURRETS[ACCEPTANCE_TURRET - 1]
    shift = _game_shift(ts)
    decor = _import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    seat, _ = turret_seat_y(ts, tx)
    turret = _assemble_turret(Vector((tx, seat, -ts + shift)), 2,
                              aim=math.radians(-28.0))
    baykit._apply_checker(decor + turret)
    _plate_lights()
    camera = _plate_camera("uv", _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                           _to_blender(CAM_UP), CAM_FOV_V)
    d = report["density"]["turret_body"]
    _label(camera, "DAMIER UV — grande case = 1 tuile de 5,00 m, petite = 62,5 cm ; "
                   "la MEME echelle sur la coque et sur le kit",
           -0.97, 0.88, 0.038, TILE_W, UV_H, (1.0, 0.88, 0.55))
    _label(camera, f"projection en boite {TEXELS_PER_METER:.3f} tuile/m ; "
                   f"anisotropie max mesuree sur le bloc {d['anisotropy_max']:.2f} "
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


def render_plate(report: dict) -> None:
    staging = tempfile.mkdtemp(prefix="aegis-turretkit-plate-")
    tiles: list[tuple[str, int]] = []
    try:
        path = os.path.join(staging, "bw.png")
        _tile_acceptance(path, report, greyscale=True)
        tiles.append((path, SCENE_H))
        path = os.path.join(staging, "color.png")
        _tile_acceptance(path, report, greyscale=False)
        tiles.append((path, SCENE_H))
        path = os.path.join(staging, "tq.png")
        _tile_three_quarter(path, report)
        tiles.append((path, CLOSE_H))
        path = os.path.join(staging, "fam.png")
        _tile_families(path, report)
        tiles.append((path, FAMILY_H))
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
