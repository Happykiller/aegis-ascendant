"""Reconstruction des trois livraisons tierces du BRIEF-0108, a leur budget.

    blender-aegis -t 1 -b -noaudio --python assets/source/models/artery/build_artery.py -- --all
    blender-aegis -t 1 -b -noaudio --python assets/source/models/artery/build_artery.py -- pylon
    blender-aegis -t 1 -b -noaudio --python assets/source/models/artery/build_artery.py -- --all --inventory

⚠️ `-t 1` EST OBLIGATOIRE (`scripts/build-hull.sh`, `howto-determinisme-des-coques.md`) :
le calcul des tangentes somme en virgule flottante dans un ordre qui depend du
nombre de workers. Sans lui, deux executions ne rendent pas le meme fichier.

CE QUE CE SCRIPT EST, ET EN QUOI IL DIFFERE DE `reduce_stern.py`
---------------------------------------------------------------
Le `BRIEF-0105` avait recu quatre `.blend` sans generateur : il ne pouvait que
TRANSFORMER un maillage deja cuit, et il l'a fait en supprimant des pieces
entieres (raboter ouvrait le flanc des coques fermees, mesure et regarde).

Ici on a mieux : **les trois livraisons arrivent avec leur generateur complet**.
On ne transforme donc rien — on RECONSTRUIT. Le `build.py` de l'auteur est
execute VERBATIM (`author/*_build.py`, copies au bit pres) par-dessus un
`geometry.py` dont chaque constante de resolution est devenue un levier
(`forge_geometry.py`). Une bague de 32 cotes ne se rabote pas : elle se
regenere a 6, et elle reste une bague.

⚠️ LA CONSEQUENCE EST LE CONTRAT DE NOMS. Les reperes `CTRL | ` ne sont pas
« preserves » : ils sont produits par la ligne de code de l'auteur qui les a
toujours produits. Le diff est vide par construction, pas par precaution.

LES QUATRE DECISIONS DU LOT
---------------------------
1. **Le pylone est reconstruit a 5,3 m, pas mis a l'echelle** (§PYLON_KILL).
   Ce qui n'existe plus a cette taille est SUPPRIME : passerelles, garde-corps,
   echelle de service, caillebotis, visserie, pochoir. Ce qui survit est
   ramene a la taille reelle par `rescale()`, une seule fois, a la fin.
2. **La conduite et le flexible sont des CIBLES**, pas du decor : leurs quatre
   clips sont la mecanique. Aucun levier ne touche aux `CTRL`, aux pistes NLA,
   ni aux pieces qui portent un `mechanism`.
3. **Zero image** (`ADR-0028`) : les neuf a douze materiaux de l'auteur se
   replient sur les cinq slots du kit, par nom, et toutes les images sont
   purgees avant l'export.
4. **UV comptees, jamais supposees** : projection en boite, densite ci-dessous.
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
if not (HERE / 'author').is_dir():  # pragma: no cover - lancement via bpy
    HERE = Path(bpy.data.filepath).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools' / 'blender' / 'lib'))
sys.path.insert(0, str(HERE))
import aegis_kit as ak  # noqa: E402
import forge_geometry as g  # noqa: E402
import forge_shims  # noqa: E402

OUT_DIR = REPO / 'assets' / 'imported' / 'models' / 'backgrounds'
TMP = Path(os.environ.get('ARTERY_TMP', '/tmp/aa-artery'))

# --------------------------------------------------------------------------
# Densite de depliage
# --------------------------------------------------------------------------
#: ⚠️ ECART ASSUME AVEC LA LETTRE DU BRIEF, ET IL EST CHIFFRE. Le brief demande
#: « la densite de la peau du corridor », soit `HULL_TEXELS_PER_METER = 0,200`
#: tuile/m (20 tuiles pour 100 m de troncon). A cette densite, un flexible de
#: 0,14 m de diametre recoit **0,028 tuile** sur toute sa largeur : sa carte de
#: detail n'existerait pas. On reprend donc la densite des quatre pieces du
#: `BRIEF-0105` posees juste a cote (`AMBRY_TEXELS_PER_METER = 0,70`, soit
#: 1,43 m/tuile), et pour la meme raison qu'elles : ces pieces se voient de
#: bien plus pres que les 500 m de borde. Aucune contrainte d'entier ne
#: s'applique — rien ici ne joint un troncon.
TILES_PER_METER = 0.70
SMOOTH_ANGLE = 0.0

# --------------------------------------------------------------------------
# Contrat de materiaux (BRIEF-0108 §4)
# --------------------------------------------------------------------------
#: ⚠️ TROIS SLOTS SONT NEUFS ET DEUX NE SUIVENT PAS LE REPLI PROPOSE. Le brief
#: envoie `10 | Carbone technique` et `10 | Gaine tressee reference 06` sur
#: `AA_Panel`. Mesure : dans la palette Unisson, **`AA_Panel` est le violet
#: `#452663`** (`aegis_kit.PALETTES`), pas un gris de panneau. Le repli du brief
#: peindrait donc en violet la gaine tressee — c'est-a-dire **la totalite du
#: tube du flexible**, 7 716 des 25 028 triangles de l'auteur — alors que sa
#: matiere d'origine est un noir metallique (base 0,018-0,09, metallic 0,58).
#: Les deux vont sur `AA_Greeble` (`#141419`, metallic 0,75), qui est
#: litteralement la meme intention. Le brief demandait de le dire plutot que de
#: le suivre : c'est fait, et la planche d'arbitrage rend les deux options.
MATERIAL_MAP: dict[str, str] = {
    '01 | Anthracite blinde': 'AA_Hull',
    '02 | Acier gris use': 'AA_Hull',
    '03 | Tranches acier brosse': 'AA_Hull',
    '04 | Cavites graphite': 'AA_Greeble',
    '05 | Conduites noires': 'AA_Greeble',
    '09 | Vis et raccords': 'AA_Greeble',
    '11 | Conduite sombre': 'AA_Greeble',
    '10 | Carbone technique': 'AA_Greeble',
    '10 | Gaine tressee reference 06': 'AA_Greeble',
    '06 | Energie magenta': 'AA_Emissive_Engine',
    '07 | Coeur plasma': 'AA_Emissive_Engine',
    '08 | Balises rouges': 'AA_Emissive_Engine',
}
#: Le repli propose par le brief, rendu cote a cote sur la planche d'arbitrage.
MATERIAL_MAP_BRIEF = dict(MATERIAL_MAP, **{
    '10 | Carbone technique': 'AA_Panel',
    '10 | Gaine tressee reference 06': 'AA_Panel',
})
EMISSIVE = 'AA_Emissive_Engine'

# --------------------------------------------------------------------------
# LE PYLONE — ce qui n'existe plus a 5,3 m
# --------------------------------------------------------------------------
#: 24 m -> 5,3 m, soit k = 0,2208. Le pont de poupe rend a **32,7 px/m**
#: (mesure du `BRIEF-0105`, cadre 58,77 m pour 1920 px a `deck_y = -11,85`),
#: et le pylone se pose sur les etagères de rive a l'echelle du jeu 0,870.
#: Un metre d'auteur rend donc 32,7 x 0,2208 x 0,870 = **6,3 px**.
PYLON_HEIGHT = 5.3
PYLON_SOURCE_HEIGHT = 24.0
PYLON_SCALE = PYLON_HEIGHT / PYLON_SOURCE_HEIGHT

#: ⚠️ CE QUI EST SUPPRIME EST SUPPRIME PARCE QU'IL A CESSE D'ETRE CE QU'IL EST,
#: pas parce qu'il coute cher. Un garde-corps de 1,10 m devient un rebord de
#: 24 cm : ce n'est plus un garde-corps, c'est une nervure. Un barreau d'echelle
#: espace de 30 cm en devient un de 6,6 cm : ce n'est plus une echelle, c'est une
#: rayure. Le detail humain d'un pylone de 24 m ne RETRECIT pas a 5,3 m, il
#: CHANGE DE NATURE — et une rayure de 0,4 px ne se voit pas, elle scintille.
PYLON_KILL = {
    # --- L'ECHELLE HUMAINE, QUI N'EST PLUS HUMAINE (4 148 tri) ---
    # Un metre d'auteur rend 6,5 px une fois le pylone a 5,3 m et le jeu a
    # `asset_scale = 0,870`. Tout ce qui ci-dessous se mesure en centimetres
    # d'auteur tombe donc sous le demi-pixel : ce n'est plus du detail, c'est
    # du scintillement.
    'Barreau echelle',          # 52 barreaux a 30 cm d'ecart -> 6,6 cm : 0,4 px
    'Montant echelle',
    'Montant garde corps',      # 1,10 m -> 24 cm : un rebord, pas un garde-corps
    'Lisse de garde corps',
    'Retour garde corps',
    'Balise garde corps',
    'Caillebotis longitudinal',  # 73 lames de 4,5 cm -> 1 cm, soit 0,3 px
    'Plinthe',
    'Feu passerelle', 'Logement Feu passerelle',
    # ⚠️ CE QUI RESTE DES DEUX PASSERELLES EST LEUR CADRE ET SON PLANCHER.
    # A 5,3 m une passerelle est une console de 29 cm de large, soit 1,9 px, et
    # ses garde-corps de 24 cm ne sont plus des garde-corps. Mais ⚠️ LA CAMERA
    # DU JEU REGARDE PRESQUE A LA VERTICALE (avant (0 ; -0,940 ; -0,342)) : un
    # cadre sans plancher se voit PAR-DESSOUS, et la premiere version rendait
    # deux rectangles vides. Les 16 caillebotis TRANSVERSAUX, qui traversent
    # toute la largeur, le referment pour 192 triangles ; les 73 longitudinaux
    # et les garde-corps en coutaient 1 596 de plus pour rien.

    # --- LA VISSERIE (levier 2 du BRIEF-0105) ---
    'Boulon affleurant',        # rayon 5,5 cm -> 1,2 cm : 0,16 px
    'Goujon socle',
    'Vis capot',

    # --- CE QUI SE CACHE DERRIERE AUTRE CHOSE ---
    'Conduite interne',         # ⚠️ le nom le dit : elles courent A L'INTERIEUR
                                # de la colonne, derriere les douze plaques de
                                # blindage. 768 triangles jamais vus.
    'Longeron de capot',        # section 10 x 9 cm -> 0,65 x 0,59 px
    'Nervure montant',
    'Raidisseur metallique',    # section 10 x 24 cm -> 0,65 x 1,6 px
    'U refroidissement',        # tuyau de 24 cm de diametre -> 1,6 px
    'Interface verticale',      # 4 bagues de 64 cm -> 4,2 px, pour 256 tri
    'Collier interface moteur',  # 8 bagues -> 5,2 px, pour 512 tri
    'Collier conduite',         # 20 bagues a fleur du tuyau -> 1 280 tri

    # --- CE QUI FERAIT DU MOIRE PLUTOT QUE DU DETAIL ---
    # 28 ailettes FIXES de 1,0 px d'epaisseur, au pas de 3,2 px, collees aux
    # 28 ailettes MOBILES du meme pas. Garder les deux ne double pas la
    # lisibilite : ca fait battre deux trames a la meme frequence. On garde
    # celles qui BOUGENT — ce sont elles qui portent les trois clips.
    'Ailette thermique fixe',

    # --- LE POCHOIR : 0,9 m -> 20 cm, soit 1,3 px de haut. Illisible. ---
    'Repere discret 07',

    # --- LA CIME : une antenne de 1,2 cm de rayon, soit 0,16 px ---
    # Elle scintillerait au lieu de se voir, et elle emportait 0,75 m de
    # hauteur qui ne portaient rien.
    'Embase antenne', 'Antenne', 'Balise antenne',

    # --- LES TEMOINS SOUS LE DEMI-PIXEL ---
    # `Temoin maintenance` fait 44 x 4 cm -> 2,9 x 0,26 px : une lumiere de
    # moins d'un quart de pixel de haut ne s'allume pas, elle clignote.
    'Logement Temoin maintenance', 'Temoin maintenance',
}
#: Un plateau de passerelle sur deux suffit a dire « il y a une passerelle » :
#: ce qui reste des deux passerelles est leur DALLE, et rien d'autre.
PYLON_TRIM: dict[str, int] = {}

# --------------------------------------------------------------------------
# LA CONDUITE — cible destructible, budget 700
# --------------------------------------------------------------------------
CONDUIT_KILL = {
    'Boulon', 'Vis embase', 'Vis collier', 'Vis prise',      # visserie
    'Barreau cage',        # 12 barreaux de 1,7 cm autour d'une chambre : 1,6 px
    'Blindage chambre',    # 12 ecailles de 1 cm d'epaisseur PLAQUEES sur le tube
    'Blindage noyau secondaire',
    'Renfort noyau',
    'Frettes conduit',     # 6 bagues de 4,5 cm, a fleur du tube qu'elles ceignent
    'Nervure montant',
    'Ligne de service',
    'Joint socket',
}
CONDUIT_TRIM = {
    'Collier secondaire': 3,   # 7 colliers de 5,5 cm -> 3 : le rythme suffit
    'Bague chambre': 2,
}

# --------------------------------------------------------------------------
# LE FLEXIBLE — il habille la liaison, budget 350
# --------------------------------------------------------------------------
#: ⚠️ LE TUBE EST LE SEUL ENDROIT OU LA RESOLUTION SE PATCHE DANS LE TEXTE. Il
#: est genere dans le `build.py` de l'auteur, pas dans `geometry.py` : ses
#: `192 x 20` sont ecrits en dur. On les remplace, et l'algorithme de l'auteur
#: recalcule LUI-MEME les poids de peau et les UV a la nouvelle resolution —
#: ce qu'un decimateur aurait fait a l'aveugle.
SOURCE_PATCHES = {
    'hose_build.py': [('steps, sides = 192, 20', 'steps, sides = 12, 6')],
    # Le pochoir « 07 » est un objet TEXTE cree hors de `geometry.py` : aucun
    # levier ne l'atteint. A 5,3 m il mesure 20 cm de haut, soit 1,2 px — il
    # n'est plus un pochoir, il est une tache. On vide son corps de texte.
    # ⚠️ ET SON HELPER `pipe()` REECRIT LA RESOLUTION DES TUYAUX APRES
    # `geometry.hose()` : `resolution_u = 5`, `bevel_resolution = 1`. Le levier 3
    # etait donc sans effet, et il ne se voyait sur AUCUN compteur — le pylone
    # consolide ses courbes en maillage DANS le `build.py` de l'auteur, donc
    # bien avant que le pilote ne puisse toucher a quoi que ce soit. Les huit
    # tuyaux coutaient 2 044 triangles, 61 % de la piece, pour des conduites de
    # 13 cm de diametre a 5,3 m, soit 0,85 px de large.
    'pylon_build.py': [("font.body = '07'", "font.body = ''"),
                       ('obj.data.resolution_u = 5',
                        'obj.data.resolution_u = g.CURVE_RES'),
                       ('obj.data.bevel_resolution = 1',
                        'obj.data.bevel_resolution = g.CURVE_BEVEL_RES')],
}
HOSE_KILL = {
    'Vis prise', 'Vis bride', 'Boulon collier',   # visserie
    'Fond prise',          # au fond d'un port de 5 cm : jamais vu
    'Port ',               # idem
    'Face connecteur',
    'Garde noyau',         # 2 bagues de 1,2 cm de part et d'autre de l'anneau
    'Joint ',
    'Frette acier',
    'Protection laterale',
    'Bride de fixation',
    'Demi coque',          # le collier : 6,2 cm de large a 46 px/m -> 2,9 px
}
HOSE_TRIM = {
    'Cable interne': 2,    # 5 brins -> 3. Ils ne se comptent pas, ils s'ebouriffent
}


class Piece:
    def __init__(self, key, build, animation, collection, budget, exports,
                 kill, trim, levers, module_collection=None, height=None):
        self.key = key
        self.build = build
        self.animation = animation
        self.collection = collection
        self.module_collection = module_collection
        self.budget = budget
        self.exports = exports      # [(fichier, racine|None)]
        self.kill = kill
        self.trim = trim
        self.levers = levers
        self.height = height


PIECES: dict[str, Piece] = {
    'pylon': Piece(
        'pylon', 'pylon_build.py', 'pylon_animation.py',
        'PT | Pylone technique 07', 3_200,
        [('stern_pylon.glb', None)],
        PYLON_KILL, PYLON_TRIM,
        dict(RING_CAP=8, ROD_CAP=6, SECTOR_CAP=6, CURVE_RES=1, CURVE_BEVEL_RES=0),
        height=PYLON_HEIGHT),
    'conduit': Piece(
        'conduit', 'conduit_build.py', 'conduit_animation.py',
        'CE | Conduite energetique', 700,
        [('artery_conduit.glb', 'CTRL | Conduit principal'),
         ('artery_conduit_bend.glb', 'CTRL | Conduit secondaire coude')],
        CONDUIT_KILL, CONDUIT_TRIM,
        # ⚠️ `ROD_CAP=12` ET `CURVE_RES=2` SONT UNE CORRECTION VUE AU RENDU, PAS
        # UN REGLAGE, ET ELLE NE FERME PAS TOUT — voir la reserve du rapport.
        # Le noyau magenta du coude est un cylindre de rayon 0,151 DANS une
        # gaine de rayon 0,143 : ils s'interpenetrent PAR CONSTRUCTION. A huit
        # cotes, les sommets de la gaine ressortent entre les faces du noyau et
        # mordent la bande lumineuse d'une couronne noire de trois pixels. Il
        # faut que le rayon INSCRIT du noyau depasse le rayon CIRCONSCRIT de la
        # gaine : 0,151 x cos(pi/12) = 0,1459 > 0,143. ⚠️ Mais le clip fait
        # PULSER ce rayon de +/-2,5 % (x3 en `Endommage`) : au creux de la
        # pulsation le noyau redescend a 0,1435 et repasse SOUS la gaine, quel
        # que soit le nombre de cotes. C'est la geometrie de l'auteur, pas la
        # reduction ; a 32 cotes elle donnait un cheveu, a 12 elle donne un
        # cran. Aucun compteur ne dit ca ; seule la capture le dit.
        dict(RING_CAP=8, ROD_CAP=12, SECTOR_CAP=4, CURVE_RES=2, CURVE_BEVEL_RES=1)),
    'hose': Piece(
        'hose', 'hose_build.py', 'hose_animation.py',
        'FT | Faisceau technique', 350,
        [('artery_hose.glb', 'FT | Module droit'),
         ('artery_hose_bend.glb', 'CTRL | Ligne 01')],
        HOSE_KILL, HOSE_TRIM,
        dict(RING_CAP=6, ROD_CAP=5, SECTOR_CAP=3, CURVE_RES=1, CURVE_BEVEL_RES=0),
        module_collection='FT | Module droit'),
}


# --------------------------------------------------------------------------
# Outils
# --------------------------------------------------------------------------

def tri_count(obj) -> int:
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def deselect_all() -> None:
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)


def scene_objects(piece: Piece):
    out = list(bpy.data.collections[piece.collection].objects)
    if piece.module_collection:
        out += list(bpy.data.collections[piece.module_collection].objects)
    return out


def subtree(name: str, piece: Piece):
    if name in bpy.data.collections:
        return list(bpy.data.collections[name].objects)
    root = bpy.data.objects[name]
    return [root, *root.children_recursive]


def ctrl_ancestor(obj):
    cur = obj.parent
    while cur is not None:
        if cur.name.startswith('CTRL'):
            return cur
        cur = cur.parent
    return None


def is_skinned(obj) -> bool:
    return any(m.type == 'ARMATURE' for m in obj.modifiers)


def object_materials(obj) -> set[str]:
    mesh = obj.data
    if not mesh.materials:
        return set()
    used = {p.material_index for p in mesh.polygons}
    return {mesh.materials[i].name for i in used
            if i < len(mesh.materials) and mesh.materials[i] is not None}


# --------------------------------------------------------------------------
# Etapes
# --------------------------------------------------------------------------

def build(piece: Piece) -> None:
    """Execute le `build.py` de l'auteur VERBATIM, leviers poses."""
    g.reset_levers()
    g.KILL = set(piece.kill)
    g.TRIM = dict(piece.trim)
    for key, value in piece.levers.items():
        setattr(g, key, value)
    forge_shims.install(g, HERE / 'author' / piece.animation, TMP / piece.key,
                        piece.collection, piece.module_collection)
    source = HERE / 'author' / piece.build
    code = source.read_text(encoding='utf-8')
    for old, new in SOURCE_PATCHES.get(piece.build, []):
        if old not in code:
            raise RuntimeError(f'patch introuvable dans {piece.build} : {old!r}')
        code = code.replace(old, new)
        print(f'PATCH {piece.build} : {old!r} -> {new!r}')
    module = {'__name__': '__main__', '__file__': str(source)}
    exec(compile(code, str(source), 'exec'), module)


def convert_curves(piece: Piece) -> None:
    """Les tuyaux sont des COURBES : ils n'ont de triangles qu'ici.

    Leur resolution a deja ete baissee a la creation (`CURVE_RES`), ce qui est
    la seule reduction du lot qui ne coute aucune forme : la section d'un tube
    de 10 cm ne vaut pas seize cotes a quatre pixels."""
    curves = [o for o in scene_objects(piece) if o.type in ('CURVE', 'FONT')]
    if not curves:
        return
    # ⚠️ ET ON REPASSE LA RESOLUTION ICI, PARCE QUE LE `build.py` DU PYLONE LA
    # REECRIT APRES COUP : son helper `pipe()` remet `resolution_u = 5` sur le
    # dos de `geometry.hose()`. Quatre collecteurs verticaux a 26 anneaux de
    # 8 cotes, c'etaient 1 664 triangles pour des tuyaux de 6,6 cm — la moitie
    # du budget du pylone, dans une piece qu'on ne distingue pas du fut.
    for obj in curves:
        if obj.type == 'CURVE':
            obj.data.resolution_u = max(1, g.CURVE_RES)
            if obj.data.bevel_depth:
                obj.data.bevel_resolution = g.CURVE_BEVEL_RES
    deselect_all()
    for obj in curves:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = curves[0]
    names = [o.name for o in curves]
    bpy.ops.object.convert(target='MESH')
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != 'MESH':
            continue
        entry = g.LEDGER.setdefault(name.split('.')[0], [0, 0, 0, 0])
        entry[1] += tri_count(obj)
        if obj.get('aa_killed'):
            entry[3] += tri_count(obj)


def apply_modifiers(piece: Piece) -> None:
    """Cuit tout SAUF l'armature — elle porte la deformation, elle reste."""
    for obj in scene_objects(piece):
        if obj.type != 'MESH':
            continue
        for mod in list(obj.modifiers):
            if mod.type == 'ARMATURE':
                continue
            deselect_all()
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=mod.name)


def remap_materials(piece: Piece, table: dict[str, str]) -> None:
    """Replie les slots de l'auteur sur les cinq du kit, et PURGE les images.

    ⚠️ L'ORDRE EST FORCE PAR BLENDER : `mesh.materials.clear()` remet tous les
    `material_index` a zero. On releve donc la cible AVANT de vider les slots.

    ⚠️ ET LA PURGE N'EST PAS COSMETIQUE (`ADR-0028`) : le harnais du Long
    Cortege echoue le build si une image apparait dans un `.glb`, et les trois
    livraisons en portaient huit a treize chacune."""
    targets: dict[str, list[str]] = {}
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        mesh = obj.data
        names = [m.name if m else '' for m in mesh.materials]
        per_poly = []
        for poly in mesh.polygons:
            src = names[poly.material_index] if poly.material_index < len(names) else ''
            dst = table.get(src)
            if dst is None:
                raise RuntimeError(f'{obj.name} : materiau inconnu {src!r}')
            per_poly.append(dst)
        targets[obj.name] = per_poly

    for coll in (bpy.data.materials, bpy.data.images, bpy.data.textures):
        for block in list(coll):
            coll.remove(block, do_unlink=True)

    ak.set_faction(ak.FACTION_NULL_CHOIR)
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        mesh = obj.data
        mesh.materials.clear()
        ak.apply_material_slots(mesh)
        for poly, dst in zip(mesh.polygons, targets[obj.name]):
            poly.material_index = ak.mat_index(dst)


def regroup(piece: Piece) -> list:
    """Fusionne les maillages qui partagent le meme repere CTRL porteur.

    ⚠️ 300 MAILLAGES, C'EST 300 APPELS DE DESSIN, et ces pieces se posent EN
    SERIE le long de 500 m. Le regroupement est une reduction a part entiere.
    Il ne casse rien : les `CTRL | ` sont des Empties, ils ne sont pas touches —
    c'est eux que le jeu adresse.

    ⚠️ ON NE FUSIONNE JAMAIS AU-DELA D'UN CTRL, et jamais un maillage PEAUSSE.
    Deux pieces sous deux CTRL differents peuvent bouger l'une sans l'autre ;
    les souder ferait disparaitre le mouvement. Le tube du flexible, lui, porte
    sa propre armature : il reste seul."""
    groups: dict[str, list] = {}
    for obj in scene_objects(piece):
        if obj.type != 'MESH' or is_skinned(obj):
            continue
        ctrl = ctrl_ancestor(obj)
        if ctrl is None:
            raise RuntimeError(f'{obj.name} : aucun ancetre CTRL')
        groups.setdefault(ctrl.name, []).append(obj)

    made = []
    for ctrl_name in sorted(groups):
        members = sorted(groups[ctrl_name], key=lambda o: o.name)
        ctrl = bpy.data.objects[ctrl_name]
        deselect_all()
        for obj in members:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = members[0]
        if len(members) > 1:
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            bpy.ops.object.join()
        joined = bpy.context.view_layer.objects.active
        short = ctrl_name.split('|', 1)[1].strip()
        joined.name = f'MESH | {short}'
        joined.data.name = joined.name
        joined.parent = ctrl
        joined.matrix_parent_inverse = ctrl.matrix_world.inverted()
        made.append(joined)
    bpy.context.view_layer.update()
    return made


def planar_merge(obj) -> None:
    """Fusionne les faces coplanaires, puis triangule. Sans perte de forme.

    Une boite subdivisee en grille redevient six faces, donc douze triangles.

    ⚠️ TRIANGULER ICI, ET CE N'EST PAS COSMETIQUE (`ak.triangulate`) : sur un
    quad gauche, la projection en boite est calculee pour une normale moyenne
    qui n'est celle d'aucun des deux triangles exportes."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.dissolve_limit(
        bm, angle_limit=math.radians(1.0), verts=bm.verts[:], edges=bm.edges[:],
        delimit={'MATERIAL'})
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    ak.triangulate(obj)


def rescale(piece: Piece) -> None:
    """Ramene la piece a sa taille de jeu — sommets, pivots, os ET cles.

    ⚠️ CE N'EST PAS « METTRE A L'ECHELLE LE `.glb` ». Le maillage qui arrive ici
    n'est plus celui de l'auteur : c'est celui que son generateur produit une
    fois retirees les pieces qui n'existent plus a 5,3 m. La taille finale est
    posee sur cette geometrie-la, et elle est CUITE dans les sommets — le
    fichier livre ne contient aucun noeud a l'echelle != 1.

    ⚠️ ET LES CLES D'ANIMATION SE MISENT A L'ECHELLE AUSSI. Une translation de
    6 mm keyframee reste 6 mm si on ne touche qu'aux sommets : le mouvement
    deviendrait quatre fois trop grand par rapport a la piece."""
    if piece.height is None:
        return
    objects = scene_objects(piece)
    # ⚠️ LE FACTEUR SE MESURE, IL NE SE SUPPOSE PAS. L'auteur livre 24,00 m,
    # antenne comprise — or l'antenne, son embase et sa balise n'existent plus a
    # cette taille (0,7 px de large) et sont supprimees. Ce qui reste mesure
    # moins que 24 : c'est de CETTE hauteur-la que se deduit le facteur, sinon
    # la piece reconstruite n'occuperait pas l'emplacement qu'on lui donne.
    lo, hi = 1e9, -1e9
    for obj in objects:
        if obj.type != 'MESH':
            continue
        for corner in obj.bound_box:
            z = (obj.matrix_world @ Vector(corner)).z
            lo, hi = min(lo, z), max(hi, z)
    built = hi - lo
    k = piece.height / built
    print(f'SCALE {piece.key} : {built:.4f} m reconstruits -> {piece.height} m, k = {k:.6f}')
    for mesh in {o.data for o in objects if o.type == 'MESH'}:
        for vertex in mesh.vertices:
            vertex.co *= k
        mesh.update()
    for obj in objects:
        obj.location = obj.location * k
        inverse = obj.matrix_parent_inverse.copy()
        inverse.translation = inverse.translation * k
        obj.matrix_parent_inverse = inverse
        if 'rest_location' in obj:
            obj['rest_location'] = [v * k for v in obj['rest_location']]
    for obj in objects:
        if obj.type != 'ARMATURE':
            continue
        deselect_all()
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        for bone in obj.data.edit_bones:
            bone.head = bone.head * k
            bone.tail = bone.tail * k
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(False)
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        if not curve.data_path.endswith('location'):
                            continue
                        for key in curve.keyframe_points:
                            key.co.y *= k
                            key.handle_left.y *= k
                            key.handle_right.y *= k
    bpy.context.view_layer.update()


def export(piece: Piece, root: str | None, path: Path) -> None:
    deselect_all()
    objects = scene_objects(piece) if root is None else subtree(root, piece)
    for obj in objects:
        obj.select_set(True)
        if obj.animation_data:
            for track in obj.animation_data.nla_tracks:
                track.mute = True
    bpy.context.view_layer.objects.active = objects[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format='GLB', use_selection=True,
        export_apply=False, export_animations=True,
        export_animation_mode='NLA_TRACKS', export_force_sampling=True,
        export_frame_range=False, export_anim_slide_to_zero=True,
        export_optimize_animation_keep_anim_object=True,
        export_extras=True, export_cameras=False, export_lights=False,
        export_materials='EXPORT', export_normals=True, export_texcoords=True,
        export_tangents=True, export_skins=True,
    )


def run(piece: Piece, inventory: bool, table: dict[str, str],
        out_dir: Path, suffix: str = '') -> dict:
    build(piece)
    if piece.module_collection:
        # Le `build.py` de l'auteur masque sa collection de module en sortant ;
        # un objet masque ne se selectionne pas, donc ne s'exporte pas.
        bpy.data.collections[piece.module_collection].hide_viewport = False
        bpy.data.collections[piece.module_collection].hide_render = False
    bpy.context.scene.frame_set(1)
    for obj in bpy.data.objects:
        if obj.animation_data:
            for track in obj.animation_data.nla_tracks:
                track.mute = True
    bpy.context.view_layer.update()
    convert_curves(piece)
    apply_modifiers(piece)
    if inventory:
        rows = sorted(g.LEDGER.items(), key=lambda kv: -kv[1][1])
        for name, (n, tris, kn, ktris) in rows:
            tag = 'JETE' if kn == n else ('PART' if kn else '    ')
            print(f'INV {tris:7d} x{n:4d}  {tag}  {name}')
    remap_materials(piece, table)
    groups = regroup(piece)
    skinned = [o for o in scene_objects(piece) if o.type == 'MESH' and is_skinned(o)]
    for obj in groups:
        planar_merge(obj)
    # ⚠️ ON REDIMENSIONNE AVANT DE DEPLIER, ET L'ORDRE INVERSE EST UN DEFAUT
    # SILENCIEUX. `box_project_uv()` projette en METRES : deplier a la taille de
    # l'auteur puis reduire d'un facteur k multiplie la densite par 1/k. Mesure
    # sur la premiere version du pylone : **2,97 tuile/m au lieu de 0,70**, soit
    # 4,4 fois trop — aucune erreur d'import, aucun test rouge, et ca ne se
    # serait vu qu'une fois la texture generee, donc trop tard (`ADR-0028`).
    rescale(piece)
    for obj in groups + skinned:
        ak.box_project_uv(obj, TILES_PER_METER)
        ak.shade_smooth_by_angle(obj, SMOOTH_ANGLE)

    stats = {'piece': piece.key, 'budget': piece.budget,
             'source_tris': sum(v[1] for v in g.LEDGER.values()),
             'jetes_tris': sum(v[3] for v in g.LEDGER.values()),
             'fichiers': []}
    for name, root in piece.exports:
        path = out_dir / name.replace('.glb', suffix + '.glb')
        export(piece, root, path)
        objects = scene_objects(piece) if root is None else subtree(root, piece)
        meshes = [o for o in objects if o.type == 'MESH']
        glow = 0
        for obj in meshes:
            for poly in obj.data.polygons:
                if obj.data.materials[poly.material_index].name == EMISSIVE:
                    glow += len(poly.vertices) - 2
        stats['fichiers'].append({
            'fichier': str(path), 'octets': path.stat().st_size,
            'tris': sum(tri_count(o) for o in meshes),
            'tris_emissif': glow, 'maillages': len(meshes),
            'ctrl': sum(1 for o in objects if o.name.startswith('CTRL')),
        })
    return stats


def main() -> None:
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    inventory = '--inventory' in argv
    brief_table = '--brief-materials' in argv
    keys = [a for a in argv if not a.startswith('--')] or list(PIECES)
    table = MATERIAL_MAP_BRIEF if brief_table else MATERIAL_MAP
    out_dir = (REPO / 'build' / 'artery_brief_materials') if brief_table else OUT_DIR
    out = []
    for key in keys:
        stats = run(PIECES[key], inventory, table, out_dir)
        out.append(stats)
        print('ARTERY ' + json.dumps(stats, ensure_ascii=False))
    print('ARTERY_TOTAL ' + json.dumps(out, ensure_ascii=False))


main()
