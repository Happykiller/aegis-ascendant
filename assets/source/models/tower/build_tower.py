"""Reconstruction de la tour d'echange thermique livree (BRIEF-0112).

    blender-aegis -t 1 -b -noaudio --python assets/source/models/tower/build_tower.py -- --all
    blender-aegis -t 1 -b -noaudio --python assets/source/models/tower/build_tower.py -- --all --inventory

⚠️ `-t 1` EST OBLIGATOIRE (`howto-determinisme-des-coques.md`) : le calcul des
tangentes somme en virgule flottante dans un ordre qui depend du nombre de
workers. Sans lui, deux executions ne rendent pas le meme fichier.

CE QUE CE SCRIPT EST
--------------------
La quatrieme livraison tierce a arriver avec **son generateur complet**. On
applique donc exactement la methode du `BRIEF-0108` : le `build.py` de l'auteur
est execute VERBATIM (`author/tower_build.py`, copie au bit pres) par-dessus un
`geometry.py` dont chaque constante de resolution est devenue un levier.

⚠️ ET C'EST LE MEME `geometry.py`, AU MD5 : `author/geometry.py` de cette
livraison est **octet pour octet** celui des trois livraisons du `BRIEF-0108`
(`96fb44d83a06750ff5dd678ded65f258`). On ne le recopie donc pas patche : on
importe `../artery/forge_geometry.py`, et on VERIFIE l'egalite au demarrage.
Deux copies d'un meme levier, c'est un levier qui divergera un jour en silence.

⚠️ ON REGENERE, ON NE DECIME JAMAIS. Une bague de 64 cotes ne se rabote pas :
elle se regenere a 8, et elle reste une bague.

LA SEULE CONTRAINTE DURE EST LA HAUTEUR, ET ELLE EST MESUREE
------------------------------------------------------------
L'auteur livre **26,00 m**. La camera du jeu est a `y = 14` : pose sur le pont
de poupe (-11,85), une tour de 26 m culmine a **+14,15**, c'est-a-dire A LA
HAUTEUR EXACTE DE L'ŒIL. Elle ne serait plus un decor, elle remplirait le cadre.

⚠️ ET CE N'EST PAS LE PLAFOND QUI BORNE CETTE PIECE, C'EST SON EMPREINTE.
La tour de l'auteur mesure **14 m de large pour 26 de haut**, soit **0,538 m de
plan par metre de hauteur**. Les deux enveloppes du brief donnent 5,20 m
(regle A, sous le plafond -3,20 depuis le plateau du massif) et 8,60 m
(regle B, sommet <= +2 depuis une etagere de rive) ; il faudrait respectivement
2,80 m et 4,63 m de plan LIBRE pour les prendre. Or la poupe n'offre que deux
fenetres, et elles sont mesurees :

    plateau du bossage (z = -8,60 .. -11,20)   2,60 m  ->  4,83 m de tour
    etagere de rive du massif (-8,60 .. -11,60) 3,00 m  ->  5,57 m de tour

**La borne est 4,83 m, et elle vient du sol.** On livre donc **4,70 m** — un
seul binaire, quatre stations, 3,4 cm de marge a chaque bout du plat le plus
court. Ce que la regle B apporte n'est alors PAS de la hauteur de piece, c'est
**3,80 m d'assise** : la meme tour posee sur la rive (-4,60) culmine a +0,10,
contre -3,70 sur le plateau (-8,40).

Si le concepteur veut depenser les 0,87 m que la rive autorise en plus, c'est
`VARIANTS` ci-dessous — une ligne — plus un plateau de rive elargi dans
`tools/blender/build_stern.py` (`TOWER_SEAT_STAGES`).

⚠️ AUCUN BUDGET DE TRIANGLES (brief §« ne coupez rien pour tenir »). Ce qui est
supprime l'est parce qu'il **a cesse d'etre ce qu'il est** a la taille visee —
un garde-corps de 1,10 m devient un rebord de 27 cm, un barreau de grille de
2,1 cm devient une rayure de 0,12 px — jamais parce qu'il coute cher.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ARTERY = REPO / 'assets' / 'source' / 'models' / 'artery'

sys.path.insert(0, str(REPO / 'tools' / 'blender' / 'lib'))
sys.path.insert(0, str(ARTERY))
sys.path.insert(0, str(HERE))
import aegis_kit as ak  # noqa: E402
import forge_geometry as g  # noqa: E402
import forge_shims  # noqa: E402

OUT_DIR = REPO / 'assets' / 'imported' / 'models' / 'backgrounds'
TMP = Path(os.environ.get('TOWER_TMP', '/tmp/aa-tower'))

#: ⚠️ LE `geometry.py` DE CETTE LIVRAISON EST CELUI DES TROIS AUTRES. On le
#: verifie au md5 plutot que de le supposer : si l'auteur le fait diverger un
#: jour, les leviers de `../artery/forge_geometry.py` ne decriraient plus cette
#: piece, et rien ne le dirait.
GEOMETRY_MD5 = '96fb44d83a06750ff5dd678ded65f258'

# --------------------------------------------------------------------------
# Densite de depliage
# --------------------------------------------------------------------------
#: La densite des pieces du `BRIEF-0105`/`BRIEF-0108` posees a cote
#: (`AMBRY_TEXELS_PER_METER`), et pour la meme raison qu'elles : ces pieces se
#: voient de bien plus pres que les 500 m de borde du corridor (0,200 tuile/m).
#: A 0,200, un carter de ventilateur de 0,55 m de diametre recevrait 0,11 tuile
#: sur toute sa largeur : sa carte de detail n'existerait pas.
TILES_PER_METER = 0.70
SMOOTH_ANGLE = 0.0

# --------------------------------------------------------------------------
# Contrat de materiaux — la convention du BRIEF-0108, sans un slot de plus
# --------------------------------------------------------------------------
#: Les onze slots de l'auteur retombent sur les cinq du kit. `10 | Carbone
#: technique` et `11 | Conduite sombre` ont deja ete arbitres au `BRIEF-0108` :
#: ils vont sur `AA_Greeble` (`#141419`, metallic 0,75) et NON sur `AA_Panel`,
#: qui est le violet de faction `#452663` — mesure a l'epoque, +46 % de
#: luminance et x 3,1 de saturation sur une piece qui doit rester sombre.
MATERIAL_MAP: dict[str, str] = {
    '01 | Anthracite blinde': 'AA_Hull',
    '02 | Acier gris use': 'AA_Hull',
    '03 | Tranches acier brosse': 'AA_Hull',
    '04 | Cavites graphite': 'AA_Greeble',
    '05 | Conduites noires': 'AA_Greeble',
    '09 | Vis et raccords': 'AA_Greeble',
    '10 | Carbone technique': 'AA_Greeble',
    '11 | Conduite sombre': 'AA_Greeble',
    '06 | Energie magenta': 'AA_Emissive_Engine',
    '07 | Coeur plasma': 'AA_Emissive_Engine',
    '08 | Balises rouges': 'AA_Emissive_Engine',
}
EMISSIVE = 'AA_Emissive_Engine'

# --------------------------------------------------------------------------
# CE QUI N'EXISTE PLUS A 4,70 m
# --------------------------------------------------------------------------
#: L'auteur construit pour 26 m ; on livre 4,70 m, soit **k = 0,1808**. La tour
#: de rive rend **8,2 px par metre d'auteur** (45,4 px/m a y = -4,60), celle du
#: plateau **6,8** (37,7 px/m a y = -8,40). Le tableau se lit avec le second
#: chiffre, qui est le plus severe des deux.
#:
#: ⚠️ CE QUI EST SUPPRIME L'EST PARCE QU'IL A CHANGE DE NATURE, pas parce qu'il
#: coute. Le detail humain d'une tour de 26 m ne RETRECIT pas a 5 m : un
#: garde-corps de 1,10 m devient un rebord de 21 cm, un caillebotis au pas de
#: 16 cm devient une trame de 3 cm — et une rayure de 0,2 px ne se voit pas,
#: elle scintille.
TOWER_KILL = {
    # --- LA VISSERIE (0,04 a 0,15 m d'auteur -> 0,3 a 1,1 px) ---------------
    'Boulon affleurant',        # r = 5,5 cm -> 0,8 px de large, x 0 vus
    'Boulon nervure',           # 24 boulons de 7,5 cm sur le diffuseur
    'Goujon ancrage',           # 16 goujons de 10 cm de haut : 0,7 px
    'Vis porte',                # 16 vis de 5,5 cm autour des portes

    # --- L'ECHELLE HUMAINE, QUI N'EST PLUS HUMAINE -------------------------
    # La passerelle de service est CONSERVEE (c'est elle qui donne l'echelle de
    # la piece, et c'est le seul element dont on deduise qu'on y monte) ; ce qui
    # part, c'est ce qui la garnit.
    'Montant garde corps',      # 20 montants de 3,5 cm de rayon -> 0,5 px
    'Lisse garde corps',        # 3,2 cm -> 0,47 px : une rayure, pas une lisse
    'Retour garde corps',
    'Caillebotis',              # 27 lames de 4,5 cm au pas de 16 cm -> 0,33 px
    'Traverse caillebotis',     # 13 lames de 2,7 cm -> 0,20 px
    'Plinthe passerelle',       # 6 cm d'epaisseur -> 0,44 px
    'Plinthe socle',            # ⚠️ voir la note ci-dessous : elle RESTE
    'Balise passerelle', 'Logement Balise passerelle',   # 4,5 x 13 cm

    # --- LES GRILLES FILAIRES : DU MOIRE, PAS DU DETAIL --------------------
    # 32 rayons de 2,1 cm de rayon au pas de 45 deg, plus 12 anneaux de 4,4 cm,
    # a plat sur le dessus des quatre carters. Vus de la camera du jeu, qui
    # plonge a 70 deg, ils sont EN PLEIN CADRE et ils battent : deux trames de
    # 0,3 px superposees ne font pas une grille, elles font du bruit. La bouche
    # du carter reste fermee par sa couronne et son bord d'acier.
    'Rayon grille ventilation',
    'Grille ventilateur',

    # --- CE QUI EST A FLEUR DE CE QU'IL CEINT ------------------------------
    'Collier de raccord',       # 16 bagues de 9 cm d'epaisseur sur un tuyau
    'Collier vertical',         # 8 bagues idem
    'Bord acier',               # frette de 12 cm posee sur la couronne de bouche

    # --- LES TEMOINS SOUS LE DEMI-PIXEL ------------------------------------
    # `Temoin capot` fait 65 x 8,5 cm -> 4,8 x 0,63 px ; `Temoin ventilateur`
    # 6,5 x 6 cm -> 0,45 px. Une lumiere d'un demi-pixel ne s'allume pas, elle
    # clignote — et elle vole du magenta a l'artere, qui doit rester lisible.
    'Temoin capot',
    'Temoin ventilateur',
    'Voyant porte',
    'Insert capot',             # 4 cm d'epaisseur, plaque sur le capot
    'Insert de porte',          # idem sur la porte
    'Fixation nervure',         # 32 tetons de 5,5 cm

    # --- LE POCHOIR : 0,8 m -> 14,5 cm, soit 5,4 px pour DEUX chiffres -----
    # 3,4 px par glyphe : ce n'est plus un pochoir, c'est du moire. ⚠️ Et c'est
    # un NUMERO DE SERIE DE L'AUTEUR (« asset 08/10 »), pas un marquage du jeu.
    # (retire par `SOURCE_PATCHES` : c'est un objet TEXTE, aucun levier ne
    #  l'atteint depuis `geometry.py`.)
}

#: Un element sur N. Les series longues ne se comptent pas, elles font un
#: RYTHME : en garder une sur deux garde le rythme et rend la trame lisible au
#: lieu de la faire battre.
TOWER_TRIM: dict[str, int] = {
    # 8 x 23 = 184 ailettes d'echangeur de 12 cm d'epaisseur au pas de 50 cm
    # (0,9 px au pas de 3,7). Une sur deux : le pas passe a 7,4 px, qui se voit.
    'Ailette echangeur': 2,
    # 23 ailettes coniques de 7,5 cm au pas de 17,4 cm sur le diffuseur : c'est
    # LA silhouette du haut de la tour, mais a 1,3 px au pas de 1,3 px elle est
    # exactement a la frequence de Nyquist. Une sur deux, et elle existe.
    'Ailette de dissipation': 2,
    # 6 anneaux concentriques de 9 cm sur la grille du diffuseur.
    'Grille concentrique': 2,
    # 24 rayons de 5,5 cm sur la meme grille.
    'Rayon de grille': 2,
    # 32 montants de carter de 12 cm : un sur deux suffit a dire « cage ».
    'Montant ventilateur': 2,
}

#: ⚠️ DEUX PATCHES TEXTUELS, ET ILS SONT DECLARES.
SOURCE_PATCHES: dict[str, list[tuple[str, str]]] = {
    'tower_build.py': [
        # (a) Le pochoir « 08 » est un objet TEXTE cree hors de `geometry.py` :
        #     aucun levier ne l'atteint. A 4,70 m il mesure 14,5 cm de haut,
        #     soit 5,4 px pour DEUX chiffres — 3,4 px par glyphe, ce qui moire
        #     au lieu de se lire. On vide son corps de texte ; l'objet reste,
        #     donc le `build.py` de l'auteur continue de tourner sans une ligne
        #     de changement (son `assert ... == 16` compte les maillages).
        ("font.body, font.align_x, font.size, font.extrude = '08','CENTER',.8,.004",
         "font.body, font.align_x, font.size, font.extrude = '','CENTER',.8,.004"),
        # (b) ⚠️ LE MEME PIEGE QU'AU `BRIEF-0108`, DANS LE MEME HELPER : `pipe()`
        #     REECRIT `resolution_u` et `bevel_resolution` APRES
        #     `geometry.hose()`. Le levier 3 serait donc sans effet, et rien ne
        #     le dirait — les huit conduites de refroidissement sont des COURBES,
        #     elles n'ont de triangles qu'a la conversion.
        ('obj.data.resolution_u = 5', 'obj.data.resolution_u = g.CURVE_RES'),
        ('obj.data.bevel_resolution = 1',
         'obj.data.bevel_resolution = g.CURVE_BEVEL_RES'),
    ],
}

#: Les leviers de resolution. Une bague de 64 cotes sur un carter de 2,3 m
#: d'auteur (0,58 m livre, 21 px) n'a pas besoin de 64 cotes : elle en a besoin
#: de 12, et c'est ce que la camera peut lire.
TOWER_LEVERS = dict(RING_CAP=12, ROD_CAP=8, SECTOR_CAP=6,
                    CURVE_RES=2, CURVE_BEVEL_RES=1)

#: `BEVEL = False` — les chanfreins a 2 segments poses sur *tous* les objets par
#: `geometry.mesh()`. Ils portent l'essentiel des 129 272 triangles du binaire
#: livre et rendent moins d'un quart de pixel. (Levier 1, pose par
#: `forge_geometry.reset_levers()`.)

ASSET_COLLECTION = 'TT | Tour thermique 08'
CLIPS = ('Service', 'Refroidissement', 'Maintenance')

#: (fichier, hauteur en metres) — un seul binaire, quatre stations.
#:
#: ⚠️ LA HAUTEUR EST CELLE QUE LA STATION LA PLUS SERREE AUTORISE, et c'est le
#: plateau du bossage : 2,60 m de plat en `z` pour une piece qui prend 0,538 m
#: de plan par metre de haut. `tools/blender/build_stern.py` porte la meme
#: valeur dans `TOWER_HEIGHT` et son harnais `_seat_probe()` la verifie sur le
#: binaire — un ecart entre les deux echoue le build de la carene.
VARIANTS = (
    ('stern_tower.glb', 4.70),
)


# --------------------------------------------------------------------------
# Outils
# --------------------------------------------------------------------------

def tri_count(obj) -> int:
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def deselect_all() -> None:
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)


def asset_objects() -> list:
    return list(bpy.data.collections[ASSET_COLLECTION].objects)


def is_skinned(obj) -> bool:
    return any(m.type == 'ARMATURE' for m in obj.modifiers)


# --------------------------------------------------------------------------
# Etapes
# --------------------------------------------------------------------------

def check_author_geometry() -> None:
    digest = hashlib.md5((HERE / 'author' / 'geometry.py').read_bytes()).hexdigest()
    if digest != GEOMETRY_MD5:
        raise RuntimeError(
            f'author/geometry.py a change (md5 {digest}) : les leviers de '
            '../artery/forge_geometry.py ne decrivent plus cette piece.')
    artery = hashlib.md5(
        (ARTERY / 'author' / 'geometry.py').read_bytes()).hexdigest()
    if artery != GEOMETRY_MD5:
        raise RuntimeError(
            f'../artery/author/geometry.py a change (md5 {artery}).')


def build() -> None:
    """Execute le `build.py` de l'auteur VERBATIM, leviers poses."""
    g.reset_levers()
    g.KILL = set(TOWER_KILL)
    g.TRIM = dict(TOWER_TRIM)
    for key, value in TOWER_LEVERS.items():
        setattr(g, key, value)
    forge_shims.install(g, HERE / 'author' / 'tower_animation.py',
                        TMP, ASSET_COLLECTION, None)
    source = HERE / 'author' / 'tower_build.py'
    code = source.read_text(encoding='utf-8')
    for old, new in SOURCE_PATCHES['tower_build.py']:
        if old not in code:
            raise RuntimeError(f'patch introuvable dans tower_build.py : {old!r}')
        code = code.replace(old, new)
        print(f'PATCH tower_build.py : {old!r} -> {new!r}')
    module = {'__name__': '__main__', '__file__': str(source)}
    exec(compile(code, str(source), 'exec'), module)


def mute_tracks() -> None:
    for obj in bpy.data.objects:
        if obj.animation_data:
            for track in obj.animation_data.nla_tracks:
                track.mute = True


def apply_modifiers() -> None:
    """Cuit tout SAUF l'armature — elle porte les quatre charnieres de capot."""
    for obj in asset_objects():
        if obj.type != 'MESH':
            continue
        for mod in list(obj.modifiers):
            if mod.type == 'ARMATURE':
                continue
            deselect_all()
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=mod.name)


def remap_materials() -> None:
    """Replie les slots de l'auteur sur les cinq du kit, et PURGE les images.

    ⚠️ L'ORDRE EST FORCE PAR BLENDER : `mesh.materials.clear()` remet tous les
    `material_index` a zero. On releve donc la cible AVANT de vider les slots.

    ⚠️ ET LA PURGE N'EST PAS COSMETIQUE (`ADR-0028`) : la livraison porte
    **13 images embarquees**, et le harnais du Long Cortege echoue le build si
    une seule apparait dans un `.glb`.
    """
    targets: dict[str, list[str]] = {}
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        mesh = obj.data
        names = [m.name if m else '' for m in mesh.materials]
        per_poly = []
        for poly in mesh.polygons:
            src = names[poly.material_index] if poly.material_index < len(names) else ''
            dst = MATERIAL_MAP.get(src)
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


def convert_curves() -> None:
    """Les huit conduites sont des COURBES : elles n'ont de triangles qu'ici."""
    curves = [o for o in asset_objects() if o.type in ('CURVE', 'FONT')]
    if not curves:
        return
    for obj in curves:
        if obj.type == 'CURVE':
            obj.data.resolution_u = max(1, g.CURVE_RES)
            if obj.data.bevel_depth:
                obj.data.bevel_resolution = g.CURVE_BEVEL_RES
    deselect_all()
    for obj in curves:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = curves[0]
    bpy.ops.object.convert(target='MESH')


def planar_merge(obj) -> None:
    """Fusionne les faces coplanaires, puis triangule. SANS PERTE DE FORME.

    Une boite subdivisee en grille redevient six faces, donc douze triangles.

    ⚠️ TRIANGULER ICI, ET CE N'EST PAS COSMETIQUE : sur un quad gauche, la
    projection en boite est calculee pour une normale moyenne qui n'est celle
    d'aucun des deux triangles exportes.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.dissolve_limit(
        bm, angle_limit=math.radians(1.0), verts=bm.verts[:], edges=bm.edges[:],
        delimit={'MATERIAL'})
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    ak.triangulate(obj)


def rescale(height: float) -> float:
    """Ramene la tour a sa taille de jeu — sommets, pivots, os ET cles.

    ⚠️ CE N'EST PAS « METTRE A L'ECHELLE LE `.glb` ». Le maillage qui arrive ici
    n'est plus celui de l'auteur : c'est celui que son generateur produit une
    fois retirees les pieces qui n'existent plus a cette taille. La hauteur
    finale est posee sur CETTE geometrie-la, et elle est CUITE dans les sommets.

    ⚠️ ET LE FACTEUR SE MESURE. L'auteur annonce 26,00 m ; ce qui survit en
    mesure moins (le bord d'acier de la couronne de bouche est supprime). C'est
    de la hauteur RECONSTRUITE que se deduit le facteur, sinon la tour
    n'occuperait pas l'emplacement qu'on lui donne.
    """
    objects = asset_objects()
    lo, hi = 1e9, -1e9
    for obj in objects:
        if obj.type != 'MESH':
            continue
        for corner in obj.bound_box:
            z = (obj.matrix_world @ Vector(corner)).z
            lo, hi = min(lo, z), max(hi, z)
    built = hi - lo
    k = height / built
    print(f'SCALE : {built:.4f} m reconstruits -> {height} m, k = {k:.6f}')
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
    # ⚠️ SEULES LES COURBES DE TRANSLATION SE MISENT A L'ECHELLE. La vibration
    # des conduites est keyframee en METRES (+/- 8 mm) : sans ca, elle resterait
    # 8 mm sur une piece cinq fois plus petite, soit cinq fois trop. Les courbes
    # de ROTATION (les quatre rotors) et d'ECHELLE (la pulsation du noyau) sont
    # sans dimension : les toucher casserait le mouvement.
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
    return k


def export(path: Path) -> None:
    deselect_all()
    objects = asset_objects()
    for obj in objects:
        obj.select_set(True)
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


def run(name: str, height: float, inventory: bool, out_dir: Path) -> dict:
    build()
    bpy.context.scene.frame_set(1)
    mute_tracks()
    bpy.context.view_layer.update()
    convert_curves()
    apply_modifiers()
    if inventory:
        rows = sorted(g.LEDGER.items(), key=lambda kv: -kv[1][1])
        for fam, (n, tris, kn, ktris) in rows:
            tag = 'JETE' if kn == n else ('PART' if kn else '    ')
            print(f'INV {tris:7d} x{n:4d}  {tag}  {fam}')
    remap_materials()
    meshes = [o for o in asset_objects() if o.type == 'MESH']
    for obj in meshes:
        if not is_skinned(obj):
            planar_merge(obj)
    # ⚠️ ON REDIMENSIONNE AVANT DE DEPLIER, ET L'ORDRE INVERSE EST UN DEFAUT
    # SILENCIEUX (`BRIEF-0108` §7.2) : `box_project_uv()` projette en METRES.
    # Deplier a la taille de l'auteur puis reduire d'un facteur k multiplie la
    # densite par 1/k — 4 fois trop, sans une erreur ni un test rouge.
    k = rescale(height)
    for obj in meshes:
        ak.box_project_uv(obj, TILES_PER_METER)
        ak.shade_smooth_by_angle(obj, SMOOTH_ANGLE)

    path = out_dir / name
    export(path)
    glow = 0
    for obj in meshes:
        for poly in obj.data.polygons:
            if obj.data.materials[poly.material_index].name == EMISSIVE:
                glow += len(poly.vertices) - 2
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for obj in meshes:
        for corner in obj.bound_box:
            w = obj.matrix_world @ Vector(corner)
            lo = Vector((min(lo[i], w[i]) for i in range(3)))
            hi = Vector((max(hi[i], w[i]) for i in range(3)))
    return {
        'fichier': str(path), 'octets': path.stat().st_size,
        'hauteur': height, 'k': k,
        'tris': sum(tri_count(o) for o in meshes),
        'tris_emissif': glow,
        'maillages': len(meshes),
        'ctrl': sum(1 for o in asset_objects() if o.name.startswith('CTRL')),
        'source_tris': sum(v[1] for v in g.LEDGER.values()),
        'jetes_tris': sum(v[3] for v in g.LEDGER.values()),
        'cotes': [round(hi[i] - lo[i], 4) for i in range(3)],
    }


def main() -> None:
    check_author_geometry()
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    inventory = '--inventory' in argv
    wanted = [a for a in argv if not a.startswith('--')]
    out = []
    for name, height in VARIANTS:
        if wanted and name not in wanted:
            continue
        stats = run(name, height, inventory, OUT_DIR)
        out.append(stats)
        print('TOWER ' + json.dumps(stats, ensure_ascii=False))
    print('TOWER_TOTAL ' + json.dumps(out, ensure_ascii=False))


main()
