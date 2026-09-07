"""Reduction des quatre pieces de poupe livrees par l'agent tiers (BRIEF-0105).

    blender-aegis -t 1 -b -noaudio --python assets/source/models/stern/reduce_stern.py -- <piece>
    blender-aegis -t 1 -b -noaudio --python assets/source/models/stern/reduce_stern.py -- --all
    blender-aegis -t 1 -b -noaudio --python assets/source/models/stern/reduce_stern.py -- --all --textured

⚠️ `-t 1` EST OBLIGATOIRE (voir `scripts/build-hull.sh`) : le calcul des tangentes somme
en virgule flottante dans un ordre qui depend du nombre de workers. Sans lui, deux
executions ne rendent pas le meme fichier.

CE QUE CE SCRIPT N'EST PAS
--------------------------
Ce n'est pas un generateur (`ADR-0008`) : c'est une TRANSFORMATION d'une source tierce
qu'on ne sait pas regenerer (`ADR-0048`). Les `.blend` d'a cote sont la source ; ce
fichier est la seule chose qui les separe du `.glb` livre.

LES CINQ LEVIERS, DANS L'ORDRE DE CE QU'ILS RAPPORTENT
------------------------------------------------------
0. **L'ECHELLE A LAQUELLE ON JUGE.** Mesuree, pas supposee : le pont de poupe est a
   y = -11,85 (le couloir, lui, est a -4,30). Le cadre y fait 58,77 m pour 1920 px,
   soit **32,7 px/m** en lateral — et non les 45,8 du brief, qui valent pour le
   couloir. A l'echelle de jeu (0,870), **1 m rend 28,4 px**.
1. **Les biseaux.** La source de l'ancrage fait 10 144 triangles, son `.glb` livre en
   fait 54 640. L'ecart n'est PAS de la geometrie : c'est un modificateur `BEVEL` a
   2 segments, pose sur 295 objets sur 295, large de 1 a 12 mm. Un biseau de 8 mm fait
   **0,23 pixel**. Il coute 81 % du fichier et ne rend rien. Il part en entier.
2. **La visserie.** Tout ce qui porte `09 | Vis et raccords` : 11 736 triangles sur le
   moteur, dont 10 752 pour un seul nom, « Rivet de blindage ». Un rivet de 6,3 cm fait
   1,8 pixel.
3. **Ce qui est trop petit pour exister** (`cull`). Tout objet dont l'EMPRISE A L'ECRAN
   — le produit de ses deux plus grandes cotes, pas la plus grande — passe sous
   `size_floor`, sauf s'il est emissif : une lumiere se lit bien au-dessous de sa
   taille geometrique, une ecaille non.
4. **La de-subdivision** (`coarsen`), sur les seules grandes pieces de revolution.
   ⚠️ Sans elle, le desherbage supprime les bagues structurelles du moteur et la
   nacelle devient un fut nu ceint d'anneaux magenta.
5. **Le desherbage** (`cull_to_budget`), et c'est lui qui finit le travail : les pieces
   sont triees par RENDEMENT — pixels par triangle — et **supprimees ENTIERES** jusqu'au
   budget. On ne rabote pas : voir `MAX_COLLAPSE`, qui porte la mesure.

⚠️ LES PIECES MOBILES NE SE REDUISENT PAS COMME LE RESTE. Une machoire, un piston, un
petale porte une animation ; la supprimer fait disparaitre le mouvement avec la forme.
Elles portent donc une valeur 2,5 fois superieure (`MOVING_VALUE`), et le rapport dit ce
qu'elles coutent.

⚠️ L'EMISSIF EST TOUJOURS SEUL DANS SON MAILLAGE, ET IL A UNE PART RESERVEE DU BUDGET
(`GLOW_SHARE`), prise avant tout desherbage. Sans elle, le tri au rendement laisse **zero
triangle emissif sur le bras** — une veine lumineuse est une petite piece chere en
triangles, donc le pire rendement de la coque. Or `CortegeSkin` reconnait son emissif PAR
SON NOM : ce qui n'est plus sur `AA_Emissive_Engine` reste allume sur un vaisseau mort,
sans qu'aucune erreur ne le dise.

⚠️ CE QUI N'EST JAMAIS TOUCHE : les reperes `CTRL | ` (ce sont des `Empty`, la reduction
n'agit que sur les maillages), les pistes NLA, et le repere d'axes — la conversion Y-up
standard de glTF est celle dont `long_cortege_stern.tres` a deja tire ses cotes.
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter, defaultdict

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(bpy.data.filepath or __file__))
if not os.path.isdir(os.path.join(HERE, "..")):  # pragma: no cover
    HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools", "blender", "lib"))
import aegis_kit as ak  # noqa: E402

OUT_DIR = os.path.join(REPO, "assets", "imported", "models", "backgrounds")

# --------------------------------------------------------------------------
# Contrat de materiaux (BRIEF-0105 §2). Les neuf slots de l'auteur se replient
# sur les cinq du kit ; seuls trois sont effectivement portes par la geometrie.
# --------------------------------------------------------------------------
MATERIAL_MAP: dict[str, str] = {
    "01 | Anthracite blinde": "AA_Hull",
    "02 | Acier gris use": "AA_Hull",
    "03 | Tranches acier brosse": "AA_Hull",
    "04 | Cavites graphite": "AA_Greeble",
    "05 | Conduites noires": "AA_Greeble",
    "09 | Vis et raccords": "AA_Greeble",
    "06 | Energie magenta": "AA_Emissive_Engine",
    "07 | Coeur plasma": "AA_Emissive_Engine",
    "08 | Balises rouges": "AA_Emissive_Engine",
}
EMISSIVE = "AA_Emissive_Engine"

#: Materiaux dont toute la geometrie disparait (levier 2).
KILL_MATERIALS = {"09 | Vis et raccords"}

#: Densite de depliage, en tuiles par metre. 0,70 tuile/m = 1,43 m par tuile —
#: la meme qu'Ambry sur le Long Cortege (`AMBRY_TEXELS_PER_METER`), et pour la
#: meme raison : ces pieces se voient de bien plus pres que les 500 m de borde
#: (0,200 tuile/m). Aucune contrainte d'entier ici : rien ne joint un troncon.
TILES_PER_METER = 0.70

#: Angle de lissage — identique au reste du depot (`ak.shade_smooth_by_angle`).
SMOOTH_ANGLE = 0.0



class Piece:
    def __init__(self, key, blend, collection, root, out, budget,
                 size_floor, protect_area, mirror=False):
        self.key = key
        self.blend = blend
        self.collection = collection
        self.root = root
        self.out = out
        self.budget = budget
        self.size_floor = size_floor
        self.protect_area = protect_area
        self.mirror = mirror


#: `size_floor` est une EMPRISE A L'ECRAN, en m2 du repere d'auteur (avant
#: `asset_scale`). Mesure du cadrage reel (voir `render_stern_plates.py`) : le
#: pont de poupe est a y = -11,85, le cadre y fait 58,77 m et la camera rend
#: **32,7 px/m** — pas les 45,8 du couloir. A l'echelle 0,870, 1 m2 couvre donc
#: 28,4 x 28,4 px, et 0,25 m2 environ 14 x 14 px.
#:
#: Les valeurs sont proportionnelles a l'emprise de la piece : 0,23 pct de son
#: propre encombrement. C'est la meme regle pour les quatre, pas quatre reglages.
PIECES: dict[str, Piece] = {
    "engine": Piece(
        "engine", "stern_engine.blend", "GMP | Groupe moteur principal",
        "CTRL | Moteur", "stern_engine.glb", 8_000, 0.250, 5.00),
    "cradle": Piece(
        "cradle", "stern_cradle.blend", "BM | Berceau moteur",
        "CTRL | Berceau", "stern_cradle.glb", 6_000, 0.240, 4.50),
    "anchor": Piece(
        "anchor", "stern_anchor.blend", "AD | Ancrage destructible",
        "CTRL | Ancrage", "stern_anchor.glb", 900, 0.0080, 0.150),
    "arm": Piece(
        "arm", "stern_arm.blend", "BA | Bras ancrage",
        "CTRL | Bras ancrage", "stern_arm.glb", 500, 0.0085, 0.160, mirror=True),
}


# --------------------------------------------------------------------------
# Outils
# --------------------------------------------------------------------------

def tri_count(obj: bpy.types.Object) -> int:
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def bbox_dims(obj: bpy.types.Object) -> tuple[float, float, float]:
    d = obj.dimensions
    return (abs(d.x), abs(d.y), abs(d.z))


def screen_area(obj: bpy.types.Object) -> float:
    """L'empreinte a l'ecran, approchee : le produit des deux plus grandes cotes.

    ⚠️ ET PAS LA PLUS GRANDE COTE SEULE, QUI SE TROMPE SUR TOUT CE QUI EST MINCE.
    Une sangle de 4,86 m de tour et 3 cm d'epaisseur a une « plus grande
    dimension » de 4,86 m : le critere de taille la classait parmi les grandes
    pieces alors qu'elle ne couvre presque rien. Le produit des deux plus grandes
    cotes est, lui, proportionnel a ce que la camera en voit."""
    d = sorted(bbox_dims(obj))
    return d[1] * d[2]


def ctrl_ancestor(obj: bpy.types.Object) -> bpy.types.Object | None:
    cur = obj.parent
    while cur is not None:
        if cur.name.startswith("CTRL"):
            return cur
        cur = cur.parent
    return None


def moving_ancestor(obj: bpy.types.Object, root: str) -> bpy.types.Object:
    """Le premier CTRL ANIME au-dessus de `obj`, sinon la racine.

    ⚠️ C'EST LE CRITERE DE FUSION, ET IL N'EST PAS ARBITRAIRE. Deux pieces
    portees par le meme CTRL anime bougent exactement ensemble : rien ne
    distingue leurs maillages a l'execution, et les separer coute un appel de
    dessin ET un plancher de douze triangles chacune. Fusionner sur un CTRL
    NON anime, en revanche, souderait une machoire a son bati.
    """
    cur = obj.parent
    while cur is not None:
        if cur.name.startswith("CTRL") and is_animated(cur):
            return cur
        cur = cur.parent
    return bpy.data.objects[root]


def is_animated(obj: bpy.types.Object) -> bool:
    ad = obj.animation_data
    return bool(ad and (ad.nla_tracks or ad.action))


def object_materials(obj: bpy.types.Object) -> set[str]:
    mesh = obj.data
    if not mesh.materials:
        return set()
    used = {p.material_index for p in mesh.polygons}
    out = set()
    for i in used:
        if i < len(mesh.materials) and mesh.materials[i] is not None:
            out.add(mesh.materials[i].name)
    return out


def deselect_all() -> None:
    for obj in bpy.data.objects:
        obj.select_set(False)


# --------------------------------------------------------------------------
# Etapes
# --------------------------------------------------------------------------

def load(piece: Piece) -> bpy.types.Collection:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, piece.blend))
    bpy.context.scene.frame_set(1)
    asset = bpy.data.collections[piece.collection]
    keep = set(asset.all_objects)
    for obj in list(bpy.data.objects):
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    # Les pistes NLA sont coupees : la pose de reference du reparentage doit
    # etre celle de l'image 1 au repos, exactement comme a l'export de l'auteur.
    for obj in asset.all_objects:
        if obj.animation_data:
            for track in obj.animation_data.nla_tracks:
                track.mute = True
    bpy.context.view_layer.update()
    return asset


def curves_to_mesh(asset: bpy.types.Collection) -> None:
    """Les conduites sont des courbes. On baisse leur resolution AVANT de les
    convertir : c'est la seule reduction qui ne coute aucune forme, la section
    d'un tube de 10 cm ne valant pas 16 cotes a 4 pixels."""
    curves = [o for o in asset.all_objects if o.type == "CURVE"]
    if not curves:
        return
    for obj in curves:
        data = obj.data
        data.resolution_u = 1
        if getattr(data, "bevel_resolution", 0) > 1:
            data.bevel_resolution = 1
    deselect_all()
    for obj in curves:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = curves[0]
    bpy.ops.object.convert(target="MESH")


def strip_bevels(asset: bpy.types.Collection) -> int:
    """Levier 1 : les biseaux et les normales ponderees qui les accompagnent."""
    removed = 0
    for obj in asset.all_objects:
        if obj.type != "MESH":
            continue
        for mod in list(obj.modifiers):
            if mod.type in {"BEVEL", "WEIGHTED_NORMAL"}:
                obj.modifiers.remove(mod)
                removed += 1
    return removed


def cull(asset: bpy.types.Collection, piece: Piece) -> dict:
    """Leviers 2 et 3 : la visserie, puis ce qui est trop petit pour exister."""
    killed_screw = Counter()
    killed_small = Counter()
    for obj in list(asset.all_objects):
        if obj.type != "MESH":
            continue
        mats = object_materials(obj)
        tris = tri_count(obj)
        if mats and mats <= KILL_MATERIALS:
            killed_screw[obj.name.split(".")[0]] += tris
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        glow = any(MATERIAL_MAP.get(m) == EMISSIVE for m in mats)
        if glow:
            continue
        if screen_area(obj) < piece.size_floor:
            killed_small[obj.name.split(".")[0]] += tris
            bpy.data.objects.remove(obj, do_unlink=True)
    return {
        "visserie_tris": sum(killed_screw.values()),
        "visserie_noms": killed_screw.most_common(10),
        "menu_fretin_tris": sum(killed_small.values()),
        "menu_fretin_noms": killed_small.most_common(10),
    }


#: ⛔ AUCUNE DECIMATION PAR COLLAPSE. Ce n'est pas un oubli, c'est une mesure.
#:
#: Quatre versions rendues a la camera du jeu, meme cadrage, meme lumiere :
#:
#:   ratio 0,26 (tout le monde rabote)  -> la nacelle rend une TOLE DECHIQUETEE
#:   ratio 0,42 + grandes pieces figees -> dents noires sur tous les capots
#:   ratio 0,62 + desherbage            -> dents noires residuelles
#:   AUCUN collapse + desherbage        -> propre, et le budget est tenu
#:
#: La raison est topologique et elle vaut pour toute livraison de ce genre : ce
#: maillage n'est pas une surface, c'est une PILE DE CENTAINES DE COQUES FERMEES.
#: Un capot est une boite de douze triangles ; un collapse qui lui en laisse sept
#: lui ouvre le flanc, on voit au travers, et la coque se couvre d'un zigzag
#: sombre — que RIEN ne signale, ni erreur, ni compteur. Un assemblage de pieces
#: rigides ne se reduit pas en rabotant chaque piece : il se reduit en gardant
#: MOINS DE PIECES, ENTIERES.
#:
#: Consequence, et elle est forte : **aucun sommet de l'auteur n'a bouge**. Tout
#: triangle livre est exactement le sien, sauf sur les pieces de revolution que
#: `coarsen()` de-subdivise.
MAX_COLLAPSE = 1.0

#: Part du budget RESERVEE a l'emissif, avant tout desherbage.
#:
#: ⚠️ SANS RESERVE, L'EMISSIF DISPARAIT — mesure : trier au rendement laissait
#: **zero triangle emissif sur le bras** et douze sur l'ancrage. C'est logique et
#: c'est le piege : une veine lumineuse est une petite piece chere en triangles,
#: donc le pire rendement de la coque. Or elle ne s'achete pas en pixels : c'est
#: elle qui dit qu'une machine est vivante, et c'est elle que le blackout du
#: LOT 8 doit pouvoir eteindre. Elle a donc son propre budget, pris d'abord.
GLOW_SHARE = 0.14

#: Ce qui protege une piece mobile du desherbage : elle porte une animation, et
#: la supprimer emporte le mouvement avec la forme.
MOVING_VALUE = 2.5


def cull_to_budget(asset: bpy.types.Collection, piece: Piece) -> dict:
    """DESHERBAGE : on SUPPRIME des pieces entieres au lieu de toutes les raboter.

    ⚠️ C'EST LE RENVERSEMENT DE METHODE DU LOT, ET IL VIENT D'UNE CAPTURE. La
    premiere version decimait tout le monde au meme ratio : a 0,26, la nacelle
    rendait une tole dechiquetee de triangles noirs — mesure a la camera du jeu,
    invisible sur tout compteur. Un assemblage de 700 pieces rigides ne se
    reduit pas en rabotant chaque piece : il se reduit en **gardant moins de
    pieces, entieres**. On trie donc par emprise a l'ecran croissante et on
    supprime jusqu'a ce que le `COLLAPSE` restant tienne au-dessus de
    `MAX_COLLAPSE`.

    L'emissif et les pieces mobiles portent une valeur artificiellement haute :
    ce ne sont pas leurs pixels qui comptent, c'est ce qu'ils racontent.
    """
    # ⚠️ ON TRIE PAR RENDEMENT, PAS PAR TAILLE. Trier par emprise seule gardait,
    # sur l'ancrage, une couronne emissive de 508 triangles — 58 pct du budget
    # pour une lampe — et supprimait la SEMELLE, c'est-a-dire la piece par
    # laquelle l'ancrage tient au berceau. Ce qu'on achete, c'est des pixels par
    # triangle.
    pools: dict[bool, list] = {True: [], False: []}
    for obj in asset.all_objects:
        if obj.type != "MESH":
            continue
        mats = object_materials(obj)
        glow = any(MATERIAL_MAP.get(m) == EMISSIVE for m in mats)
        moving = moving_ancestor(obj, piece.root).name != piece.root
        value = max(screen_area(obj), 1e-5)
        if moving:
            value *= MOVING_VALUE
        pools[glow].append((value / max(tri_count(obj), 1), obj.name, obj))

    killed = Counter()

    def weed(items: list, target: float) -> int:
        items.sort(key=lambda t: (t[0], t[1]))
        total = sum(tri_count(o) for _v, _n, o in items)
        for _value, _name, obj in items:
            if total <= target:
                break
            tris = tri_count(obj)
            killed[obj.name.split(".")[0]] += tris
            total -= tris
            bpy.data.objects.remove(obj, do_unlink=True)
        return total

    glow_kept = weed(pools[True], piece.budget * GLOW_SHARE)
    solid_kept = weed(pools[False], piece.budget - glow_kept)
    return {
        "desherbage_tris": sum(killed.values()),
        "desherbage_noms": killed.most_common(10),
        "tris_apres_desherbage": glow_kept + solid_kept,
        "reserve_emissif": glow_kept,
    }


def remap_materials(asset: bpy.types.Collection) -> None:
    """Replie les neuf slots de l'auteur sur la nomenclature du kit.

    ⚠️ L'ORDRE EST FORCE PAR BLENDER : `mesh.materials.clear()` remet tous les
    `material_index` a zero. On releve donc la cible AVANT de vider les slots.
    """
    targets: dict[str, list[str]] = {}
    for obj in asset.all_objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        names = [m.name if m else "" for m in mesh.materials]
        per_poly = []
        for poly in mesh.polygons:
            src = names[poly.material_index] if poly.material_index < len(names) else ""
            dst = MATERIAL_MAP.get(src)
            if dst is None:
                raise RuntimeError(f"{obj.name} : materiau inconnu {src!r}")
            per_poly.append(dst)
        targets[obj.name] = per_poly

    # Purge complete : materiaux, images, textures. Sans elle `set_faction()`
    # refuse (une coque = une faction) et le `.glb` embarquerait onze atlas.
    for coll in (bpy.data.materials, bpy.data.images, bpy.data.textures):
        for block in list(coll):
            coll.remove(block, do_unlink=True)

    ak.set_faction(ak.FACTION_NULL_CHOIR)
    for obj in asset.all_objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        mesh.materials.clear()
        ak.apply_material_slots(mesh)
        per_poly = targets[obj.name]
        for poly, dst in zip(mesh.polygons, per_poly):
            poly.material_index = ak.mat_index(dst)


def regroup(asset: bpy.types.Collection, piece: Piece) -> list[tuple]:
    """Fusionne les maillages par CTRL porteur, et separe l'emissif.

    ⚠️ 1 300 maillages, c'est 1 300 appels de dessin. Le regroupement est une
    reduction a part entiere, et il ne casse rien : les reperes `CTRL | ` sont
    des Empties, ils ne sont pas touches — c'est eux que le jeu adresse.
    """
    groups: dict[tuple, list] = defaultdict(list)
    for obj in list(asset.all_objects):
        if obj.type != "MESH":
            continue
        if ctrl_ancestor(obj) is None:
            raise RuntimeError(f"{obj.name} : aucun ancetre CTRL")
        ctrl = moving_ancestor(obj, piece.root)
        mats = object_materials(obj)
        glow = mats == {EMISSIVE}
        if not glow and EMISSIVE in mats:
            # Un maillage mixte : on separe l'emissif par bmesh plus tard n'a
            # pas lieu d'etre ici — l'auteur ne melange pas, on le verifie.
            raise RuntimeError(f"{obj.name} : maillage mixte emissif/solide")
        keep = screen_area(obj) >= piece.protect_area
        groups[(ctrl.name, glow, keep)].append(obj)

    made = []
    for (ctrl_name, glow, keep) in sorted(groups):
        members = sorted(groups[(ctrl_name, glow, keep)], key=lambda o: o.name)
        ctrl = bpy.data.objects[ctrl_name]
        deselect_all()
        for obj in members:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = members[0]
        if len(members) > 1:
            bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
            bpy.ops.object.join()
        joined = bpy.context.view_layer.objects.active
        short = ctrl_name.split("|", 1)[1].strip()
        tag = "GLOW" if glow else ("KEEP" if keep else "MESH")
        joined.name = f"{tag} | {short}"
        joined.data.name = joined.name
        joined.parent = ctrl
        joined.matrix_parent_inverse = ctrl.matrix_world.inverted()
        made.append((joined, ctrl, glow, is_animated(ctrl), keep))
    bpy.context.view_layer.update()
    return made


#: Au-dela de ce nombre de triangles, un objet passe d'abord par un
#: DE-SUBDIVISION avant toute autre reduction.
COARSEN_CAP = 48
COARSEN_MAX_STEPS = 2


def coarsen(asset: bpy.types.Collection, piece: Piece) -> int:
    """De-subdivise les pieces de revolution AVANT toute fusion.

    ⚠️ C'EST UNE QUESTION DE QUALITE, PAS DE BUDGET, ET ELLE S'EST VUE AU RENDU.
    Le fut du moteur est ceint de bagues a 512 triangles (« Couple structurel »,
    « Joint noir de couple », « Sangle de contention ») : des tores reguliers.
    Fusionnes puis reduits au `COLLAPSE`, ils rendaient un zigzag de triangles
    sombres sur toute la nacelle — a 32,7 px/m, une tole dechiquetee. Le
    `COLLAPSE` ne sait pas qu'un tore est un tore ; l'`UNSUBDIV`, si : il divise
    la resolution de la grille par deux a chaque passe et la bague reste une
    bague. On de-subdivise donc CHAQUE PIECE, tant qu'elle est encore un
    quadrillage regulier, et le `COLLAPSE` ne finit plus que le reste.
    """
    steps = 0
    for obj in asset.all_objects:
        if obj.type != "MESH":
            continue
        if screen_area(obj) < piece.protect_area:
            continue
        for _ in range(COARSEN_MAX_STEPS):
            if tri_count(obj) <= COARSEN_CAP:
                break
            mod = obj.modifiers.new("AA_Unsubdiv", "DECIMATE")
            mod.decimate_type = "UNSUBDIV"
            mod.iterations = 1
            deselect_all()
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            before = tri_count(obj)
            bpy.ops.object.modifier_apply(modifier=mod.name)
            steps += 1
            if tri_count(obj) >= before:
                break
    return steps


def planar_merge(obj: bpy.types.Object) -> None:
    """Fusionne les faces coplanaires, puis triangule.

    Sans perte : une boite subdivisee en grille redevient six faces, donc douze
    triangles a l'export.

    ⚠️ ON NE SOUDE PAS LES ILOTS, ET C'EST MESURE. Un groupe fusionne est un tas
    d'ilots fermes ; `DECIMATE` ne descend pas un ilot sous quatre faces, donc le
    plancher d'un groupe vaut 4 x son nombre d'ilots (bras : 144 triangles
    obtenus pour 53 vises). Souder les ilots jointifs a 6 mm pour leur rendre un
    chemin de collapse a ete essaye : le bras gagne 9 triangles et **l'ancrage en
    perd 225** (930 -> 1 155). La soudure cree des aretes non-manifold qui
    BLOQUENT le collapse au lieu de l'ouvrir. Le plancher reste, il est structurel,
    et le rapport le nomme."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.dissolve_limit(
        bm, angle_limit=math.radians(1.0), verts=bm.verts[:], edges=bm.edges[:],
        delimit={"MATERIAL"})
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    # ⚠️ TRIANGULER ICI, ET CE N'EST PAS COSMETIQUE. Le ratio du modificateur
    # `DECIMATE` s'applique au nombre de FACES, pas de triangles : sur un
    # maillage rendu a l'etat de n-gones par la fusion coplanaire, un ratio
    # calcule en triangles vise a cote et le budget est depasse en silence
    # (mesure : 647 triangles pour un budget de 500 sur le bras).
    ak.triangulate(obj)


def unwrap(obj: bpy.types.Object) -> None:
    ak.box_project_uv(obj, TILES_PER_METER)


def export(piece: Piece, path: str, textured: bool) -> None:
    deselect_all()
    asset = bpy.data.collections[piece.collection]
    for obj in asset.all_objects:
        obj.select_set(True)
    root = bpy.data.objects[piece.root]
    bpy.context.view_layer.objects.active = root
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True,
        export_apply=True, export_animations=True,
        export_animation_mode="NLA_TRACKS", export_force_sampling=True,
        export_frame_range=False, export_anim_slide_to_zero=True,
        export_optimize_animation_keep_anim_object=True,
        export_extras=True, export_cameras=False, export_lights=False,
        export_materials="EXPORT", export_normals=True, export_texcoords=True,
        export_tangents=True,
    )


def run(piece: Piece, textured: bool) -> dict:
    asset = load(piece)
    before = sum(tri_count(o) for o in asset.all_objects if o.type == "MESH")
    curves_to_mesh(asset)
    after_curves = sum(tri_count(o) for o in asset.all_objects if o.type == "MESH")
    bevels = strip_bevels(asset)
    culled = cull(asset, piece)
    coarsened = coarsen(asset, piece) if COARSEN_CAP > 0 else 0
    for obj in list(asset.all_objects):
        if obj.type == "MESH":
            planar_merge(obj)
    weeded = cull_to_budget(asset, piece)
    if os.environ.get("STERN_DEBUG"):
        fam = Counter()
        cnt = Counter()
        for o in asset.all_objects:
            if o.type != "MESH":
                continue
            fam[o.name.split(".")[0]] += tri_count(o)
            cnt[o.name.split(".")[0]] += 1
        for k, v in fam.most_common(24):
            d = sorted(abs(x) for x in bbox_dims(
                [o for o in asset.all_objects if o.name.split(".")[0] == k][0]))
            print(f"FAM {v:7d} x{cnt[k]:4d}  {d[1]*d[2]:7.3f} m2  {k}")
    if not textured:
        remap_materials(asset)
    groups = regroup(asset, piece)
    pre_decimate = sum(tri_count(o) for o, _c, _g, _m, _k in groups)
    moving = sum(tri_count(o) for o, c, _g, m, _k in groups if m and c.name != piece.root)
    glow = sum(tri_count(o) for o, _c, g, _m, _k in groups if g)
    for obj, _c, _g, _m, _k in groups:
        if not textured:
            unwrap(obj)
        else:
            ak.triangulate(obj)
        ak.shade_smooth_by_angle(obj, SMOOTH_ANGLE)
    total = sum(tri_count(o) for o, _c, _g, _m, _k in groups)

    suffix = "_textured" if textured else ""

    def target(name: str) -> str:
        return name.replace(".glb", suffix + ".glb")

    out = os.path.join(OUT_DIR, target(piece.out))
    if textured:
        # ⚠️ HORS DU DEPOT VERSIONNE, ET C'EST LE POINT DE L'ARBITRAGE. La version
        # texturee pese ses onze atlas ; `build/` est gitignore. Elle ne sert qu'a
        # la planche de comparaison, tant que l'operateur n'a pas tranche.
        out = os.path.join(REPO, "build", "stern_textured", target(piece.out))
    export(piece, out, textured)
    stats = {
        "piece": piece.key,
        "source_tris": before,
        "source_tris_avec_conduites": after_curves,
        "modificateurs_biseau_retires": bevels,
        "passes_de_desubdivision": coarsened,
        "groupes": len(groups),
        "tris_avant_decimation": pre_decimate,
        "tris_final": total,
        "tris_mobiles": moving,
        "tris_emissif": glow,
        "budget": piece.budget,
        **weeded,
        "fichier": out,
        "octets": os.path.getsize(out),
        **culled,
    }
    if piece.mirror:
        root = bpy.data.objects[piece.root]
        root.scale.x = -1.0
        bpy.context.view_layer.update()
        mirror_out = os.path.join(
            os.path.dirname(out), target(piece.out.replace(".glb", "_mirror.glb")))
        export(piece, mirror_out, textured)
        stats["miroir"] = mirror_out
        stats["miroir_octets"] = os.path.getsize(mirror_out)
    return stats


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    textured = "--textured" in argv
    keys = [a for a in argv if not a.startswith("--")]
    if "--all" in argv or not keys:
        keys = list(PIECES)
    out = []
    for key in keys:
        stats = run(PIECES[key], textured)
        out.append(stats)
        print("REDUCE " + json.dumps(stats, ensure_ascii=False))
    print("REDUCE_TOTAL " + json.dumps(out, ensure_ascii=False))


main()
