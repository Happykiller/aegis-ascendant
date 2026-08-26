"""build_impact_debris.py — le bolide et son eclat (BRIEF-0086).

    blender45 -b -P tools/blender/build_impact_debris.py
    blender45 -b -P tools/blender/build_impact_debris.py -- --plate
    ./scripts/build-hull.sh --check impact_debris     # + controle de determinisme

Produit `assets/imported/models/vfx/bolide.glb` et `assets/imported/models/vfx/impact_shard.glb`
et, avec `--plate`, `docs/forge/output/BRIEF-0086-planche-silhouettes.png`.

Le script EST la source des deux assets (ADR-0008) : aucun `.blend` versionne, aucun alea, deux
executions successives rendent les memes sha256. Dix harnais de mesure tournent a chaque build et
**tous echouent le build** — voir `_audit()`.


CE QUI DECIDE DE CES DEUX COQUES : ELLES FONT 8 PIXELS
======================================================
Le bolide tombe sur une lune posee a 96 unites de la camera. A cette distance le cadre visible fait
~115 m de haut pour 540 px de rendu utile : **une piece de 1,7 m occupe 8 pixels**. Le chiffre est
donne par le brief, mesure et non estime, et il commande tout ce qui suit.

1. **Rien sous ~40 cm.** Un detail plus petit n'est jamais echantillonne : le payer en triangles,
   c'est payer du bruit. `_min_feature()` mesure la plus petite arete du polyedre AVANT
   triangulation et echoue le build si elle descend sous le plancher de la piece.
2. **Le budget va dans la SILHOUETTE.** A 8 px on ne lit qu'un contour : sa proportion, ses coins,
   et surtout la facon dont il CHANGE quand la piece tourne. Une sphere ne change jamais.
3. **Les budgets du brief sont des plafonds.** 400 triangles pour le bolide, 150 pour l'eclat ; on
   livre 5 a 10 fois moins, parce qu'un triangle de plus ne se verrait pas.

⚠️ **ET LE BOLIDE EST RENDU NON ECLAIRE.** `moon_flyby.gd` lui pose un `StandardMaterial3D` en
`SHADING_MODE_UNSHADED` avec emission x3,4 : en jeu, **aucune facette ne se voit**, la piece est un
aplat sature. Toute l'information tient donc dans son CONTOUR — c'est ce qui interdit une patate
convexe et impose des aretes longues et des proportions franches. La planche de recette rend le
bolide dans ce mode exact (ligne 1) et sous la lumiere du jeu (ligne 3, au cas ou l'emission serait
adoucie plus tard).

⚠️ **ET LE CONTOUR SE FAIT MANGER PAR LE BLOOM.** `space_environment.tres` pose
`glow_hdr_threshold = 1,6` ; le bolide est a 3,4. Il deborde donc du seuil et le moteur lui ajoute
un halo dont la LARGEUR EST EN PIXELS D'ECRAN, pas en metres : a 8 px il noie la silhouette, a 24 il
la borde seulement. La planche ne simule pas ce halo — elle mesure la geometrie. Le compte-rendu
dit ce que ca implique.

⚠️ **L'ECLAT, LUI, EST ECLAIRE** (albedo 0,42, aucun emissif) : sa silhouette arrive intacte a
l'ecran. C'est la piece dont la forme paie le plus.


LA FORME : ON TAILLE, ON NE BRUITE PAS
======================================
Les trois rochers du survol (`build_moon_flyby.py`) partent d'une icosphere de 1 280 triangles
bruitee puis rabattue sur onze plans de cassure. Ici ce serait le mauvais outil : a 8 px un bruit a
haute frequence disparait entierement et ne laisse qu'un cercle. On part donc d'une BOITE aux
proportions voulues et on la TAILLE avec une poignee de plans (`_chunk()`), ce qui donne :

  * des facettes GRANDES et franches, dont l'orientation est choisie et non tiree ;
  * un contour a coins nets, dont la longueur change fortement avec la rotation ;
  * une trentaine de triangles au lieu de mille.

C'est un solide CONVEXE : a 8 px une concavite de 40 cm vaut moins d'un pixel, la payer serait
absurde. Ce qui se lit, c'est l'allongement et les coins.


L'ORIENTATION EN JEU : LA LONGUEUR EST SUR Z, LA COURSE EST OBLIQUE
==================================================================
Le contrat de noms du brief dit « plus long que large » : la grande dimension du bolide est donc
**Godot +Z**, et le harnais refuse le build si Z n'excede pas X d'au moins 20 %.

⚠️ **Piege d'integration.** `moon_flyby.basis_from_up()` construit une base dont l'axe **Y** suit la
direction donnee — c'est ce qu'il faut pour les `CylinderMesh` de la trainee et de l'onde, batis le
long de +Y. Le pointer tel quel sur le bolide coucherait la piece EN TRAVERS de sa course. Pour
aligner la longueur sur `bolide_heading()`, il faut une base qui met la direction sur **Z**
(`Basis.looking_at()`, ou la base ci-dessus tournee de -90 deg autour de X).


LA MATIERE : ELLE NE VIENT PAS D'ICI (ADR-0028)
===============================================
Aucune texture n'est produite ni embarquee. Les deux pieces reutilisent `TEX-0002` (roche
d'asteroide), deja derivee et en jeu, comme les trois rochers du survol.

⚠️ **La tuile de `TEX-0002` est calee sur 8 m de roche, et cette echelle est une CONTRAINTE DURE
partagee** : elle vaut pour la piece de 2,5 m comme pour le rocher de 20 m. Normaliser le depliage
sur la piece donnerait un grain trois fois trop fin et ferait lire le bolide comme du gravier.
D'ou `ak.box_project_uv(obj, texels_per_meter=1/8)`, litteralement la meme ligne que
`build_moon_flyby.build_rock()`, avec la meme constante. Cote Godot, `uv1_scale` reste (1, 1, 1).

⚠️ **Aucun emissif dans le `.glb`.** La chaleur est posee par le code ; une emission cuite s'y
ajouterait sans qu'on puisse l'eteindre. On livre une roche froide et sombre, exactement l'albedo
`Asteroid_Rock` du survol.


POURQUOI PAS `ak.export_hull()`
===============================
Le brief l'attendait — les deux pieces sont bien a l'origine, donc le probleme de `BRIEF-0085` (des
corps qui portent une translation) ne se pose pas ici. C'est un AUTRE point du contrat qui bloque :
`_validate_glb()` refuse tout materiau hors `MATERIAL_ORDER` (« materiau hors nomenclature
ADR-0008 »), et la couleur exigee par le brief est celle de la roche du survol, qui n'appartient a
aucune palette de faction. Utiliser `AA_Hull` livrerait du blanc casse Vanguard (#EDEAE3) ou de
l'anthracite Null Choir sur des cailloux neutres, et casserait le partage de materiau avec
`Asteroid_Rock`. L'export et sa validation sont donc refaits ici, meme correction d'axe et meme
relecture du binaire produit, **sans toucher au kit** (`aegis_kit` 1.1.0, importe tel quel pour
`box_project_uv`, `cleanup` et `ContractError`).
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
from mathutils import Matrix, Vector

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import aegis_kit as ak  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BOLIDE_GLB = "assets/imported/models/vfx/bolide.glb"
SHARD_GLB = "assets/imported/models/vfx/impact_shard.glb"
PLATE_PNG = "docs/forge/output/BRIEF-0086-planche-silhouettes.png"

# ==========================================================================
# Budgets, echelles, couleurs
# ==========================================================================

TRI_BUDGET_BOLIDE = 400
TRI_BUDGET_SHARD = 150

#: Metres de roche couverts par une tuile de `TEX-0002`. ⚠️ CONTRAINTE DURE PARTAGEE avec
#: `build_moon_flyby.ROCK_METRES_PER_TILE` : la meme valeur sur toutes les roches du jeu,
#: quelle que soit leur taille. Cuite dans les UV — cote Godot `uv1_scale` reste (1, 1, 1).
ROCK_METRES_PER_TILE = 8.0

#: Plus petite arete toleree sur le polyedre (avant triangulation), PAR PIECE. En dessous,
#: on paie un detail que le rendu n'echantillonne jamais — voir l'en-tete.
#: ⚠️ Le plancher n'est pas le meme pour les deux, et ce n'est pas un assouplissement de
#: confort : le brief dit « rien sous ~40 cm » a l'echelle du BOLIDE, qui fait 2,55 m. L'eclat,
#: lui, EST un detail de 40 cm — il ne fait qu'un metre de long pour 28 cm d'epaisseur, et lui
#: imposer 40 cm d'arete minimale reviendrait a interdire sa propre section.
MIN_FEATURE_M = {"Bolide": 0.25, "Shard": 0.10}

#: Albedo LINEAIRE de la roche. Copie exacte de `moon_flyby.ROCK_ALBEDO`, elle-meme reprise
#: de `scripts/vfx/moon_flyby.gd` ou elle a ete validee en capture. Froide (B > R), sombre,
#: aucun emissif. Aucune couleur de la charte ne convient : ses palettes sont des palettes de
#: FACTION, et un caillou n'en a pas.
ROCK_ALBEDO = (0.100, 0.098, 0.118)

#: Dimensions VOULUES, dans le repere Godot (X largeur, Y hauteur, Z longueur).
#: ⚠️ Le contrat de noms dit « plus long que large » : Z > X, et le harnais le verifie.
BOLIDE_SIZE = (1.38, 1.10, 2.70)
SHARD_SIZE = (0.50, 0.28, 1.05)

#: Tolerance sur ces dimensions, en fraction.
SIZE_TOLERANCE = 0.04


# ==========================================================================
# Taille de coupe — une boite, quelques plans, rien d'autre
# ==========================================================================


def _box(bm: bmesh.types.BMesh, size: tuple[float, float, float]) -> None:
    """Boite alignee sur les axes, centree, `size` = dimensions PLEINES."""
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=res["verts"])


def _cut(bm: bmesh.types.BMesh, normal: tuple[float, float, float], offset: float) -> None:
    """Retranche le demi-espace `n . p > offset` et referme la coupe.

    `offset` est en METRES le long de `normal` (normalise ici) : c'est la distance du plan a
    l'origine, donc une profondeur de coupe qui se lit directement. `clear_outer` laisse un
    trou ouvert — `holes_fill` le referme par un n-gon, triangule en fin de course.
    """
    plane_no = Vector(normal).normalized()
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(
        bm,
        geom=geom,
        dist=1e-6,
        plane_co=plane_no * offset,
        plane_no=plane_no,
        clear_outer=True,
    )
    edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if edges:
        bmesh.ops.holes_fill(bm, edges=edges, sides=0)


def _chunk(size: tuple[float, float, float],
           cuts: tuple[tuple[tuple[float, float, float], float], ...],
           weld: float) -> bmesh.types.BMesh:
    """Une boite taillee par une liste de plans. Convexe, facettes franches, peu de triangles.

    `weld` dissout les aretes plus courtes que lui. Deux plans qui se croisent pres d'un coin
    deja coupe laissent une ECHARDE de quelques centimetres : invisible au rendu, mais elle
    coute des sommets, elle degrade la tangente mikktspace et elle fait mentir la mesure de
    taille de detail. `dissolve_degenerate` est fait pour ca — on ne la corrige pas a la main.
    """
    bm = bmesh.new()
    _box(bm, size)
    for normal, offset in cuts:
        _cut(bm, normal, offset)
    if weld > 0.0:
        bmesh.ops.dissolve_degenerate(bm, dist=weld, edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def _fit(bm: bmesh.types.BMesh, target: tuple[float, float, float]) -> tuple[float, float, float]:
    """Recentre sur la bbox et met a l'echelle ANISOTROPE pour atteindre `target` (repere auteur).

    On recentre AVANT : les coupes sont dissymetriques par construction, le barycentre de la
    boite d'origine n'est plus le centre de la piece taillee. Le contrat exige l'origine AU
    CENTRE, pas « la ou la boite etait ».
    """
    lo = [min(v.co[a] for v in bm.verts) for a in range(3)]
    hi = [max(v.co[a] for v in bm.verts) for a in range(3)]
    centre = Vector([(lo[a] + hi[a]) * 0.5 for a in range(3)])
    factor = [target[a] / (hi[a] - lo[a]) for a in range(3)]
    for vert in bm.verts:
        vert.co = Vector([(vert.co[a] - centre[a]) * factor[a] for a in range(3)])
    return tuple(factor)


def _min_feature(bm: bmesh.types.BMesh) -> float:
    """Plus petite arete du POLYEDRE, avant triangulation : la vraie taille de detail.

    Mesurer apres triangulation n'aurait pas de sens : les diagonales ajoutees dans un n-gon
    ne sont pas des aretes de forme, elles ne se voient sur aucun contour.
    """
    return min(e.calc_length() for e in bm.edges)


def _facets(bm: bmesh.types.BMesh) -> list[float]:
    """Aires des facettes PLANES, regroupees par normale (avant triangulation), decroissant."""
    groups: list[tuple[Vector, float]] = []
    for face in bm.faces:
        normal = face.normal.normalized()
        for index, (ref, area) in enumerate(groups):
            if ref.dot(normal) > 0.999:
                groups[index] = (ref, area + face.calc_area())
                break
        else:
            groups.append((normal, face.calc_area()))
    return sorted((a for _, a in groups), reverse=True)


# ==========================================================================
# Les deux pieces
# ==========================================================================
#
# Repere d'AUTEUR (ADR-0008) : longueur le long de -Y (l'avant), hauteur +Z, largeur X.
# La chaine d'axes (x, y, z) -> (-x, z, y) envoie donc Y sur la LONGUEUR Godot (Z) et Z sur
# la HAUTEUR Godot (Y). Les `_SIZE` ci-dessus sont en repere Godot ; `_author_size()` les
# remet dans l'ordre du modeleur.


def _author_size(godot_size: tuple[float, float, float]) -> tuple[float, float, float]:
    """(X, Y, Z)_Godot -> (X, Y, Z)_auteur : la longueur passe de Z a Y, la hauteur de Y a Z."""
    return (godot_size[0], godot_size[2], godot_size[1])


#: LE BOLIDE — « le coin ». Un bloc allonge, epaule a l'avant-bas par une grande cassure
#: oblique, qui s'affine vers l'arriere en une arete. Trois intentions, et une seule compte
#: vraiment a 8 px :
#:   * l'ALLONGEMENT (2,70 pour 1,38 de large, soit 1,96) : c'est lui qui distingue la
#:     piece d'un point — et c'est le seul de ces trois traits qui tienne a 8 px ;
#:   * l'ASYMETRIE avant/arriere : l'avant est massif, l'arriere pointu — en tournant, le
#:     contour passe d'un trapeze court a un fuseau long, et cette pulsation est LE signal ;
#:   * deux grandes facettes franches (la cassure avant-bas et le flanc babord), pour le jour
#:     ou le code adoucirait l'emission.
BOLIDE_CUTS = (
    ((-0.32, -0.55, -0.77), 0.86),   # GRANDE cassure avant-bas : la facette principale
    ((0.28, 0.62, 0.73), 0.90),      # cassure arriere-haut, presque opposee : un bloc CISAILLE
    ((0.12, -0.95, 0.29), 1.14),     # le nez est tronque en biais, jamais pointu
    ((-0.18, 0.94, -0.30), 1.13),    # la queue aussi, mais pas du meme cote : dissymetrie
    ((0.95, 0.22, -0.24), 0.80),     # long flanc tribord, franc et profond
    ((-0.90, 0.26, 0.36), 0.90),     # flanc babord, moins mordu : les deux cotes different
    ((0.44, -0.44, -0.78), 0.95),    # eclat de coin avant-bas-tribord
)

#: L'ECLAT — « l'echarde ». Une lame plate qui pointe vers l'avant et se casse net a
#: l'arriere en deux facettes. A 8 px c'est un TRAIT, pas une tache : exactement ce qu'on
#: veut d'un morceau arrache. L'epaisseur decroit de la cassure vers la pointe, ce qui fait
#: varier son aire projetee d'un facteur 2 sur un tour — une sphere, elle, ne bouge pas.
SHARD_CUTS = (
    ((0.72, -0.69, 0.06), 0.30),     # taille tribord vers la pointe
    ((-0.68, -0.72, -0.12), 0.30),   # taille babord vers la pointe
    ((0.34, 0.90, 0.26), 0.44),      # cassure arriere, facette 1
    ((-0.28, 0.87, -0.40), 0.44),    # cassure arriere, facette 2
    ((0.06, -0.34, 0.94), 0.19),     # la lame s'amincit vers l'avant (dessus)
    ((-0.10, -0.26, -0.96), 0.20),   # et vers l'avant (dessous)
)


def build_piece(name: str, godot_size: tuple[float, float, float],
                cuts, weld: float) -> tuple[bpy.types.Object, dict]:
    """Taille la piece, la recentre, la triangule, la deplie et rend ses mesures d'atelier."""
    bm = _chunk(_author_size(godot_size), cuts, weld)
    factor = _fit(bm, _author_size(godot_size))
    stats = {
        "min_feature_m": _min_feature(bm),
        "facettes": len(_facets(bm)),
        "aires_facettes": _facets(bm),
        "aire_totale": sum(f.calc_area() for f in bm.faces),
        "echelle": factor,
    }
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    # ⚠️ Faces PLATES assumees, comme les rochers du survol : une roche cassante n'a pas de
    # normale continue, et c'est justement la nettete des aretes qui fait la silhouette.
    for face in bm.faces:
        face.smooth = False
    obj = _new_object(name, bm, _rock_material())
    ak.cleanup(obj, merge_dist=1e-4)
    # ⚠️ MEME ECHELLE MONDE QUE LES TROIS ROCHERS DU SURVOL — 8 m par tuile, pas une tuile par
    # piece. Normaliser ici ferait lire le bolide comme du gravier (TEX-0002, contrainte dure).
    ak.box_project_uv(obj, texels_per_meter=1.0 / ROCK_METRES_PER_TILE)
    return obj, stats


# ==========================================================================
# Materiau — couleur unie, aucun emissif, aucune texture (ADR-0028)
# ==========================================================================


def _rock_material() -> bpy.types.Material:
    """Un SEUL datablock : les deux pieces portent la meme roche que le survol."""
    existing = bpy.data.materials.get("Asteroid_Rock")
    if existing is not None:
        return existing
    mat = bpy.data.materials.new("Asteroid_Rock")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    color = (*ROCK_ALBEDO, 1.0)
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Emission Strength"].default_value = 0.0
    mat.diffuse_color = color
    return mat


def _new_object(name: str, bm: bmesh.types.BMesh,
                material: bpy.types.Material) -> bpy.types.Object:
    """Objet maille a un seul slot de materiau.

    ⚠️ `ak.new_object()` poserait les SEPT slots normalises de l'ADR-0008 et leurs couleurs de
    faction. Un debris n'appartient a aucune faction. Le slot est pose AVANT le transfert du
    BMesh — sans quoi `mesh.materials` remettrait tous les `material_index` a zero.
    """
    mesh = bpy.data.meshes.new(name)
    mesh.materials.append(material)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# ==========================================================================
# Export — meme chaine d'axes que le kit, refaite ici (voir l'en-tete)
# ==========================================================================

_AXIS_FIX = Matrix.Rotation(math.pi, 4, "Z")
_YUP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))


def _assert_axis_chain() -> None:
    """La chaine (x, y, z)_auteur -> (-x, z, y)_glTF, verifiee sur des temoins ASYMETRIQUES.

    La bounding box ne verrait pas un demi-tour : elle est symetrique. Ceci le voit.
    """
    chain = _YUP @ _AXIS_FIX
    for probe, expected in (
        (Vector((1.0, 2.0, 3.0)), Vector((-1.0, 3.0, 2.0))),
        (Vector((0.0, -1.25, 0.4)), Vector((0.0, 0.4, -1.25))),
        (Vector((0.8, 0.0, -0.65)), Vector((-0.8, -0.65, 0.0))),
    ):
        got = chain.to_3x3() @ probe
        if (got - expected).length > 1e-5:
            raise ak.ContractError(f"chaine d'axes rompue : {tuple(probe)} -> {tuple(got)}")


def _read_glb(path: str) -> tuple[dict, bytes]:
    """Relit le `.glb` produit : on valide le livrable, pas nos intentions."""
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


def export(obj: bpy.types.Object, filepath: str, budget: int,
           godot_size: tuple[float, float, float], stats: dict) -> dict:
    """Corrige les axes, exporte la piece SEULE, puis relit le binaire et l'audite."""
    _assert_axis_chain()
    obj.data.transform(_AXIS_FIX)
    obj.data.update()
    obj.location = (0.0, 0.0, 0.0)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    absolute = os.path.join(ROOT, filepath)
    os.makedirs(os.path.dirname(absolute), exist_ok=True)
    staging = tempfile.mkdtemp(prefix="aegis-debris-")
    staged = os.path.join(staging, os.path.basename(absolute))
    try:
        bpy.ops.export_scene.gltf(
            filepath=staged,
            export_format="GLB",
            export_yup=True,
            export_apply=True,
            use_selection=True,
            export_materials="EXPORT",
            export_cameras=False,
            export_lights=False,
            export_animations=False,
            export_skins=False,
            export_extras=False,
            export_tangents=True,
            export_normals=True,
            export_texcoords=True,
        )
        report = _audit(staged, obj.name, budget, godot_size, stats)
        report["fichier"] = filepath
        os.replace(staged, absolute)
    finally:
        if os.path.isdir(staging):
            for leftover in os.listdir(staging):
                os.remove(os.path.join(staging, leftover))
            os.rmdir(staging)
    report["octets"] = os.path.getsize(absolute)
    return report


# ==========================================================================
# Les harnais — tout ce qui suit ECHOUE le build
# ==========================================================================


def _accessor(gltf: dict, blob: bytes, index: int) -> list[tuple]:
    """Lit un accesseur du binaire. On mesure le FICHIER, pas la scene en memoire."""
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    counts = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[acc["type"]]
    fmt = {5126: "f", 5125: "I", 5123: "H", 5121: "B"}[acc["componentType"]]
    stride = struct.calcsize(fmt) * counts
    base = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    step = view.get("byteStride", stride)
    return [struct.unpack_from("<" + fmt * counts, blob, base + i * step)
            for i in range(acc["count"])]


def _tile_density(positions: list[tuple], uvs: list[tuple],
                  indices: list[int]) -> dict:
    """Metres de roche par tuile, MESURES triangle par triangle sur le maillage livre.

    On ne compare pas des aires (une aire moyenne ne voit AUCUN etirement : un triangle deux
    fois trop long dans un sens et deux fois trop court dans l'autre a la bonne aire). On
    calcule les deux valeurs singulieres de la matrice plan-vers-UV, qui donnent les metres
    par tuile dans les deux directions principales, et leur rapport donne l'anisotropie.
    """
    rows: list[tuple[float, float, float]] = []
    for i in range(0, len(indices), 3):
        a, b, c = (Vector(positions[indices[i + k]]) for k in range(3))
        ua, ub, uc = (Vector(uvs[indices[i + k]]) for k in range(3))
        e1, e2 = b - a, c - a
        area = e1.cross(e2).length * 0.5
        if area < 1e-12:
            continue
        # Base orthonormee du plan du triangle : on ramene la 3D a une 2D locale.
        x = e1.normalized()
        n = e1.cross(e2).normalized()
        y = n.cross(x)
        p1 = Vector((e1.dot(x), e1.dot(y)))
        p2 = Vector((e2.dot(x), e2.dot(y)))
        d1, d2 = ub - ua, uc - ua
        det = p1.x * p2.y - p1.y * p2.x
        if abs(det) < 1e-12:
            continue
        # J : plan (m) -> UV (tuiles). Ses valeurs singulieres sont des tuiles/m.
        j00 = (d1.x * p2.y - d2.x * p1.y) / det
        j01 = (d2.x * p1.x - d1.x * p2.x) / det
        j10 = (d1.y * p2.y - d2.y * p1.y) / det
        j11 = (d2.y * p1.x - d1.y * p2.x) / det
        e = (j00 * j00 + j01 * j01 + j10 * j10 + j11 * j11) * 0.5
        f = math.sqrt(max(0.0, (0.5 * (j00 * j00 + j01 * j01 - j10 * j10 - j11 * j11)) ** 2
                          + (j00 * j10 + j01 * j11) ** 2))
        s_max = math.sqrt(max(1e-18, e + f))
        s_min = math.sqrt(max(1e-18, e - f))
        rows.append((area, 1.0 / s_max, 1.0 / s_min))
    total = sum(r[0] for r in rows)
    return {
        "min_m_par_tuile": min(r[1] for r in rows),
        "max_m_par_tuile": max(r[2] for r in rows),
        "moyenne_m_par_tuile": sum(r[0] * 0.5 * (r[1] + r[2]) for r in rows) / total,
        "anisotropie_max": max(r[2] / r[1] for r in rows),
        "anisotropie_moyenne": sum(r[0] * r[2] / r[1] for r in rows) / total,
    }


def _audit(path: str, name: str, budget: int,
           godot_size: tuple[float, float, float], stats: dict) -> dict:
    """Neuf controles sur le FICHIER produit. Le moindre ecart echoue le build."""
    gltf, blob = _read_glb(path)
    problems: list[str] = []

    nodes = gltf.get("nodes", [])
    mesh_nodes = [n for n in nodes if "mesh" in n]
    if len(nodes) != 1 or len(mesh_nodes) != 1:
        problems.append(f"attendu 1 seul nœud maille, trouve {len(nodes)} nœuds "
                        f"({len(mesh_nodes)} mailles)")
    if not mesh_nodes:
        raise ak.ContractError(f"CONTRAT ROMPU — {name} : aucun maillage exporte")
    node = mesh_nodes[0]

    # 1. contrat de noms — lu par le code
    if node.get("name") != name:
        problems.append(f"contrat de noms : nœud « {node.get('name')} », attendu « {name} »")

    # 2. le nœud est a l'origine (aucune translation cachee cote Godot)
    translation = node.get("translation", [0.0, 0.0, 0.0])
    if max(abs(v) for v in translation) > 1e-6:
        problems.append(f"nœud translate {tuple(translation)} — il doit rester a l'origine")

    triangles = 0
    vertices = 0
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    with_uv = 0
    with_tangent = 0
    primitives = 0
    density: dict = {}
    for prim in gltf["meshes"][node["mesh"]]["primitives"]:
        primitives += 1
        attrs = prim["attributes"]
        acc = gltf["accessors"][attrs["POSITION"]]
        vertices += acc["count"]
        for axis in range(3):
            lo[axis] = min(lo[axis], acc["min"][axis])
            hi[axis] = max(hi[axis], acc["max"][axis])
        indices = [i[0] for i in _accessor(gltf, blob, prim["indices"])]
        triangles += len(indices) // 3
        # 3. UV : COMPTEES dans le binaire, jamais supposees (ADR-0028)
        if "TEXCOORD_0" in attrs:
            with_uv += 1
            density = _tile_density(_accessor(gltf, blob, attrs["POSITION"]),
                                    _accessor(gltf, blob, attrs["TEXCOORD_0"]),
                                    indices)
        if "TANGENT" in attrs:
            with_tangent += 1
    if with_uv != primitives:
        problems.append(f"TEXCOORD_0 sur {with_uv}/{primitives} primitives — ADR-0028 exige 100 %")
    if with_tangent != primitives:
        problems.append(f"TANGENT sur {with_tangent}/{primitives} primitives")

    size = tuple(hi[a] - lo[a] for a in range(3))
    centre = tuple((hi[a] + lo[a]) * 0.5 for a in range(3))

    # 4. dimensions voulues
    for axis, label in ((0, "largeur X"), (1, "hauteur Y"), (2, "longueur Z")):
        drift = abs(size[axis] - godot_size[axis]) / godot_size[axis]
        if drift > SIZE_TOLERANCE:
            problems.append(f"{label} = {size[axis]:.4f} m, attendu {godot_size[axis]:.4f} "
                            f"(+/-{SIZE_TOLERANCE:.0%}) — ecart {drift:.2%}")

    # 5. origine AU CENTRE, sur les trois axes
    for axis, label in ((0, "X"), (1, "Y"), (2, "Z")):
        if abs(centre[axis]) > 0.01:
            problems.append(f"origine decentree en {label} : {centre[axis]:+.4f} m (tolerance 1 cm)")

    # 6. « plus long que large » (contrat de noms du brief, pour le bolide)
    if name == "Bolide" and size[2] <= size[0] * 1.2:
        problems.append(f"le bolide doit etre plus long que large : Z = {size[2]:.2f}, "
                        f"X = {size[0]:.2f}")

    # 7. budget de triangles (un PLAFOND)
    if triangles > budget:
        problems.append(f"{triangles} triangles > budget {budget}")

    # 8. aucune texture, aucun emissif (ADR-0028 + contrainte du brief)
    if gltf.get("images"):
        problems.append(f"{len(gltf['images'])} image(s) embarquee(s) — ADR-0028 l'interdit")
    for mat in gltf.get("materials", []):
        pbr = mat.get("pbrMetallicRoughness", {})
        for key in ("baseColorTexture", "metallicRoughnessTexture"):
            if key in pbr:
                problems.append(f"materiau {mat.get('name')} : {key} — ADR-0028 l'interdit")
        for key in ("normalTexture", "occlusionTexture", "emissiveTexture"):
            if key in mat:
                problems.append(f"materiau {mat.get('name')} : {key} — ADR-0028 l'interdit")
        emissive = mat.get("emissiveFactor", [0.0, 0.0, 0.0])
        if max(emissive) > 0.0 or "KHR_materials_emissive_strength" in mat.get("extensions", {}):
            problems.append(f"materiau {mat.get('name')} : emissif cuit — le brief l'interdit "
                            "(la chaleur est posee par le code)")

    # 9. densite de texels : la MEME echelle monde que les rochers du survol.
    # ⚠️ Elle est cuite dans les UV en coordonnees LOCALES : une echelle posee sur le nœud
    # cote Godot la multiplie d'autant. Sous 1,3 c'est invisible ; au-dela, il faut revenir
    # ici changer `*_SIZE` et rebatir, pas etirer le nœud.
    if density and not (ROCK_METRES_PER_TILE * 0.55 <= density["moyenne_m_par_tuile"]
                        <= ROCK_METRES_PER_TILE * 1.45):
        problems.append(f"densite de texels hors cible : {density['moyenne_m_par_tuile']:.2f} "
                        f"m/tuile, attendu {ROCK_METRES_PER_TILE:.1f}")

    # 10. rien sous MIN_FEATURE_M — voir l'en-tete
    floor = MIN_FEATURE_M[name]
    if stats["min_feature_m"] < floor:
        problems.append(f"plus petite arete {stats['min_feature_m']:.3f} m < "
                        f"{floor} m : detail jamais echantillonne a 8 px")

    if problems:
        raise ak.ContractError(f"CONTRAT ROMPU — {name} ({path})\n"
                               + "\n".join(f"  - {p}" for p in problems))

    return {
        "nom": name,
        "triangles": triangles,
        "sommets": vertices,
        "primitives": primitives,
        "texcoord": with_uv,
        "tangent": with_tangent,
        "bbox": size,
        "centre": centre,
        "materiaux": [m.get("name") for m in gltf.get("materials", [])],
        "densite": density,
        "budget": budget,
        **stats,
    }


# ==========================================================================
# Build
# ==========================================================================


def _reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for collection in (bpy.data.meshes, bpy.data.materials, bpy.data.objects,
                       bpy.data.lights, bpy.data.cameras, bpy.data.curves):
        for datablock in list(collection):
            collection.remove(datablock)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


PIECES = (
    ("Bolide", BOLIDE_SIZE, BOLIDE_CUTS, 0.26, TRI_BUDGET_BOLIDE, BOLIDE_GLB),
    ("Shard", SHARD_SIZE, SHARD_CUTS, 0.10, TRI_BUDGET_SHARD, SHARD_GLB),
)


def build() -> list[dict]:
    """Les deux pieces, chacune dans sa scene propre et son propre `.glb`."""
    reports = []
    for name, size, cuts, weld, budget, path in PIECES:
        _reset()
        obj, stats = build_piece(name, size, cuts, weld)
        reports.append(export(obj, path, budget, size, stats))
    return reports


def _print(reports: list[dict]) -> None:
    print("\n=== BRIEF-0086 — bolide et eclats " + "=" * 44)
    for r in reports:
        d = r["densite"]
        print(f"\n  {r['nom']} — {r['fichier']} ({r['octets']} o)")
        print(f"    triangles       : {r['triangles']} (plafond {r['budget']})"
              f" — {r['sommets']} sommets, {r['primitives']} primitive(s)")
        print(f"    bbox Godot      : {r['bbox'][0]:.3f} x {r['bbox'][1]:.3f} x "
              f"{r['bbox'][2]:.3f} m (X larg., Y haut., Z long.)")
        print(f"    origine         : ({r['centre'][0]:+.4f}, {r['centre'][1]:+.4f}, "
              f"{r['centre'][2]:+.4f})")
        print(f"    TEXCOORD_0      : {r['texcoord']}/{r['primitives']} — "
              f"TANGENT {r['tangent']}/{r['primitives']}")
        print(f"    densite texels  : {d['min_m_par_tuile']:.2f} a {d['max_m_par_tuile']:.2f} "
              f"m/tuile (moyenne {d['moyenne_m_par_tuile']:.2f}, cible "
              f"{ROCK_METRES_PER_TILE:.1f}) — anisotropie max {d['anisotropie_max']:.2f}")
        print(f"    tuiles par metre: {1.0 / ROCK_METRES_PER_TILE:.4f} "
              f"— la piece couvre {r['bbox'][2] / ROCK_METRES_PER_TILE:.2f} tuile en longueur")
        print(f"    facettes planes : {r['facettes']} — la plus grande "
              f"{r['aires_facettes'][0] / r['aire_totale']:.0%} de la surface, "
              f"les trois plus grandes {sum(r['aires_facettes'][:3]) / r['aire_totale']:.0%}")
        print(f"    plus petite arete : {r['min_feature_m']:.3f} m "
              f"(plancher {MIN_FEATURE_M[r['nom']]})")
        print(f"    materiaux       : {', '.join(r['materiaux'])} — aucune texture, aucun emissif")
    print()


# ==========================================================================
# Planche de recette — `--plate`
# ==========================================================================
#
# ⚠️ CE N'EST PAS UNE BELLE VUE, C'EST LA RECETTE DU BRIEF. On rend les deux pieces A 8 ET A
# 24 PIXELS, sur fond noir, a cote d'une SPHERE LISSE DE MEME TAILLE. Si a 8 px la piece et la
# sphere sont indiscernables, la coque ne sert a rien et c'est la silhouette qu'il faut
# reprendre — pas la texture.
#
# Comment on rend « 8 pixels » sans tricher : camera ORTHOGRAPHIQUE, `ortho_scale` = 1,75 x la
# plus grande dimension de la piece, rendu dans un cadre de 14 px. La piece couvre donc
# exactement 8 px, et la sphere de reference — meme diametre, meme cadre, meme camera — en
# couvre 8 aussi. Aucune perspective ne vient fausser la comparaison. Les tuiles sont ensuite
# agrandies au PLUS PROCHE VOISIN (x 12 et x 4) : on regarde les vrais pixels, grossis, jamais
# un reechantillonnage qui les lisserait.
#
# ⚠️ ET LES DEUX PIECES NE SE RENDENT PAS PAREIL, PARCE QUE LE JEU NE LES REND PAS PAREIL.
# Le bolide porte un materiau NON ECLAIRE (`moon_flyby.gd`, emission x3,4) : il sort en aplat
# sature, sans la moindre facette. L'eclat, lui, est ECLAIRE. La planche montre donc le bolide
# dans son mode de jeu (ligne 1) ET sous la lumiere du jeu (ligne 3), et chaque ligne a sa
# sphere de reference rendue dans le MEME mode — comparer un caillou eclaire a une sphere
# emissive ne prouverait rien.

PLATE_W, PLATE_H = 1920, 1200
TILE = 168                      #: cote d'affichage d'une vignette, en pixels de planche
CLOSEUP = 430                   #: cote de la vue de trois quarts
#: (pixels occupes par la piece, cote du cadre rendu, facteur d'agrandissement)
BLOCKS = ((8, 14, TILE // 14), (24, 42, TILE // 42))
FRAME_RATIO = 1.75              #: cadre / sujet — identique dans les deux blocs

#: Trois poses de chute. Ce ne sont pas trois jolis angles : c'est la question « le contour
#: CHANGE-t-il pendant la chute ? », a laquelle une sphere repond non par construction.
POSES_DEG = (0.0, 62.0, 133.0)

#: Axe de culbute, dans le repere d'auteur. ⚠️ Volontairement PRESQUE PERPENDICULAIRE a la
#: longueur (qui court le long de Y) : un axe pris le long de la piece la ferait tourner sur
#: elle-meme sans que sa silhouette bouge d'un pixel, et la planche ne prouverait rien.
TUMBLE_AXIS = (0.86, 0.18, 0.48)

#: Orientation de base — « trois quarts en chute », l'angle reel : la piece pique vers le bas
#: de l'ecran, legerement de biais et legerement vers le spectateur.
BASE_EULER_DEG = (-68.0, -14.0, 22.0)

#: Le fond du jeu passe au NOIR ici : le brief demande fond noir, et un fond noir est aussi le
#: pire des cas pour une silhouette (aucun contraste de complaisance).
#: L'ambiante du jeu (`space_environment.tres`, couleur x energie) reste, elle : sans elle le
#: cote a l'ombre tomberait a zero et la piece paraitrait plus fine qu'elle n'est.
AMBIENT = tuple(c * 0.8 for c in (0.55, 0.62, 0.78))

#: Les trois directionnelles de `scenes/gameplay/graybox.tscn`, direction = -Z de leur base.
GAME_LIGHTS = (
    ("Key", (0.329, -0.8192, -0.4698), 1.55, (1.0, 0.976, 0.925)),
    ("Rim", (-0.0819, -0.342, 0.9361), 0.70, (0.596, 0.855, 1.0)),
    ("Fill", (-0.4, -0.449, -0.799), 0.55, (0.85, 0.91, 1.0)),
)

#: `moon_flyby.IMPACT_WARM`, en sRGB comme dans le code Godot.
IMPACT_WARM = (1.0, 0.80, 0.45)
IMPACT_EMISSION = 3.4
#: L'albedo des eclats dans `moon_flyby.gd` — plus clair que la lune, volontairement.
SHARD_ALBEDO_SRGB = (0.42, 0.39, 0.40)

SAMPLES = 256                   #: cadres de 14 px : le cout est nul, l'antialiasing compte


def _srgb(hex_or_rgb) -> tuple[float, float, float]:
    """sRGB -> lineaire, sur un triplet 0-1 (les Color de Godot sont en sRGB)."""
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                 for c in hex_or_rgb)


def _plate_scene() -> None:
    """Scene de rendu des vignettes : fond NOIR pour la camera, ambiante du jeu ailleurs."""
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
    sky.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
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
    scene.cycles.use_denoising = False
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_depth = "8"
    # ⚠️ 1,0 et non le defaut 1,5. Le filtre de reconstruction est ce qui decide de
    # l'antialiasing du contour, donc de tout ce que cette planche mesure. 1,0 approche un
    # sous-echantillonnage 2x2 en boite, ce que fait le rendu du jeu ; 1,5 aurait etale la
    # piece sur un pixel et demi de plus et rendu la sphere et le caillou plus semblables
    # qu'ils ne le sont.
    scene.render.filter_size = 1.00
    # ⚠️ « Standard » et non AgX : cette planche compare des CONTOURS et des couleurs cuites
    # dans le code. Une courbe de tonalite ferait mentir l'aplat non eclaire du bolide.
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    for name, direction, energy, color in GAME_LIGHTS:
        data = bpy.data.lights.new(name, type="SUN")
        # Godot : L = albedo x energie x N.L. Cycles : L = albedo x force x N.L / pi.
        data.energy = energy * math.pi
        data.color = color
        data.angle = 0.0
        light = bpy.data.objects.new(name, data)
        # Repere Godot -> Blender apres import glTF : (x, y, z) -> (x, -z, y).
        aim = Vector((direction[0], -direction[2], direction[1]))
        light.rotation_euler = aim.to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(light)


def _unshaded_material(name: str) -> bpy.types.Material:
    """L'aplat du bolide en jeu : emission pure, saturee, sans la moindre facette."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    emission = tree.nodes.new("ShaderNodeEmission")
    emission.inputs[0].default_value = (*_srgb(IMPACT_WARM), 1.0)
    emission.inputs[1].default_value = IMPACT_EMISSION
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(emission.outputs[0], out.inputs[0])
    return mat


def _lit_material(name: str, linear: tuple[float, float, float]) -> bpy.types.Material:
    """⚠️ `linear` est deja en LINEAIRE : c'est ce que porte le `.glb`, donc ce qu'on rend."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*linear, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 1.0
    return mat


def _sphere(name: str, diameter: float) -> bpy.types.Object:
    """La SPHERE LISSE de reference — le temoin du brief, et l'etat de l'art a remplacer.

    Meme diametre que la plus grande dimension de la piece, donc meme empreinte maximale a
    l'ecran : c'est la comparaison la plus severe pour nous, et la plus honnete.
    """
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=diameter * 0.5)
    for face in bm.faces:
        face.smooth = True
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _pose(obj: bpy.types.Object, angle_deg: float) -> None:
    base = (Matrix.Rotation(math.radians(BASE_EULER_DEG[2]), 4, "Z")
            @ Matrix.Rotation(math.radians(BASE_EULER_DEG[1]), 4, "Y")
            @ Matrix.Rotation(math.radians(BASE_EULER_DEG[0]), 4, "X"))
    tumble = Matrix.Rotation(math.radians(angle_deg), 4, Vector(TUMBLE_AXIS).normalized())
    obj.matrix_world = tumble @ base


def _tile_camera(nominal: float) -> bpy.types.Object:
    """Orthographique : « 8 px » est alors une VERITE GEOMETRIQUE, pas un cadrage a l'oeil."""
    data = bpy.data.cameras.new("tile")
    data.type = "ORTHO"
    data.ortho_scale = nominal * FRAME_RATIO
    cam = bpy.data.objects.new("tile", data)
    cam.location = (0.0, -20.0, 0.0)
    cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def _render(path: str, size: int) -> None:
    scene = bpy.context.scene
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def _footprint(path: str) -> dict:
    """Mesure l'empreinte reellement rendue : combien de pixels, et dans quelle boite.

    C'est la seule facon de repondre « la piece fait bien 8 px » autrement qu'en le
    supposant, et de chiffrer « elle se distingue d'une sphere » autrement qu'a l'oeil.
    """
    import numpy as np
    image = bpy.data.images.load(path)
    width, height = image.size
    buffer = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(buffer)
    bpy.data.images.remove(image)
    luma = buffer.reshape(height, width, 4)[:, :, :3].max(axis=2)
    mask = luma > 0.06
    if not mask.any():
        return {"pixels": 0, "boite": (0, 0), "mask": mask}
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    return {
        "pixels": int(mask.sum()),
        "couverture": float(luma[mask].sum()),
        "boite": (int(cols[-1] - cols[0] + 1), int(rows[-1] - rows[0] + 1)),
        "mask": mask,
    }


def _iou(a, b) -> float:
    """Recouvrement des deux empreintes. 1,00 = la piece et la sphere sont LE MEME objet."""
    import numpy as np
    union = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / union) if union else 1.0


#: Les cinq lignes de la planche. (cle, libelle, sujet, mode, nominal)
#: `sujet` : "piece" -> la coque livree ; "sphere" -> le temoin lisse de meme taille.
def _rows() -> tuple:
    return (
        ("bolide_flat", ("Bolide", "non eclaire - COMME EN JEU"), "piece", "flat", "Bolide"),
        ("sphere_flat", ("Sphere lisse", "temoin, non eclairee"), "sphere", "flat", "Bolide"),
        ("bolide_lit", ("Bolide", "sous la lumiere du jeu"), "piece", "lit_rock", "Bolide"),
        ("shard_lit", ("Shard", "eclaire - COMME EN JEU"), "piece", "lit_shard", "Shard"),
        ("sphere_lit", ("Sphere lisse", "temoin, eclairee"), "sphere", "lit_shard", "Shard"),
    )


def _build_subject(kind: str, mode: str, piece: str) -> bpy.types.Object:
    name, size, cuts, weld, _budget, _path = next(p for p in PIECES if p[0] == piece)
    nominal = max(size)
    if kind == "piece":
        obj, _ = build_piece(name, size, cuts, weld)
        obj.data.materials.clear()
    else:
        obj = _sphere("Sphere_" + name, nominal)
    if mode == "flat":
        material = _unshaded_material("plate_flat")
    elif mode == "lit_rock":
        # EXACTEMENT l'albedo du .glb livre — pas un gris de complaisance.
        material = _lit_material("plate_rock", ROCK_ALBEDO)
    else:
        # L'albedo que `moon_flyby.gd` pose deja sur les eclats, converti en lineaire.
        material = _lit_material("plate_shard", _srgb(SHARD_ALBEDO_SRGB))
    obj.data.materials.append(material)
    return obj


def _render_tiles(outdir: str) -> dict:
    """Rend les 35 vignettes et mesure chacune. Retourne les chemins et les mesures."""
    tiles: dict = {}
    measures: dict = {}
    for key, _label, kind, mode, piece in _rows():
        nominal = max(next(p for p in PIECES if p[0] == piece)[1])
        for pixels, frame, _zoom in BLOCKS:
            for index, angle in enumerate(POSES_DEG):
                _plate_scene()
                obj = _build_subject(kind, mode, piece)
                _pose(obj, angle)
                _tile_camera(nominal)
                path = os.path.join(outdir, f"{key}_{pixels}_{index}.png")
                _render(path, frame)
                tiles[(key, pixels, index)] = path
                measures[(key, pixels, index)] = _footprint(path)
        # la vue de trois quarts, pose du milieu, plein cadre
        _plate_scene()
        obj = _build_subject(kind, mode, piece)
        _pose(obj, POSES_DEG[1])
        _tile_camera(nominal)
        path = os.path.join(outdir, f"{key}_closeup.png")
        _render(path, CLOSEUP)
        tiles[(key, "closeup", 0)] = path
    return {"tiles": tiles, "measures": measures}


# --------------------------------------------------------------------------
# Composition — une scene ou 1 unite = 1 pixel de planche
# --------------------------------------------------------------------------

INK = (0.93, 0.94, 0.96)
DIM = (0.60, 0.63, 0.70)
WARN = (1.0, 0.78, 0.36)
GOOD = (0.62, 0.90, 0.62)


def _layout_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    world = bpy.data.worlds.new("layout")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
    scene.world = world
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 4
    scene.cycles.use_denoising = False
    scene.render.resolution_x, scene.render.resolution_y = PLATE_W, PLATE_H
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    data = bpy.data.cameras.new("layout")
    data.type = "ORTHO"
    data.ortho_scale = PLATE_W
    cam = bpy.data.objects.new("layout", data)
    cam.location = (PLATE_W * 0.5, PLATE_H * 0.5, 10.0)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam


def _quad(name: str, x: float, y: float, w: float, h: float,
          z: float = 0.0) -> bpy.types.Object:
    """Quad en coordonnees PLANCHE (origine en haut a gauche, y vers le bas).

    `z` est la PROFONDEUR, et elle n'est pas cosmetique : deux quads coplanaires se
    disputent le pixel et le premier essai a vu les bandes de temoin recouvrir la moitie
    des vignettes. Fond a -1, vignettes a 0, texte a +1.
    """
    bm = bmesh.new()
    top = PLATE_H - y
    verts = [bm.verts.new((v[0], v[1], z)) for v in ((x, top - h, 0), (x + w, top - h, 0),
                                                     (x + w, top, 0), (x, top, 0))]
    face = bm.faces.new(verts)
    uv = bm.loops.layers.uv.verify()
    for loop, coord in zip(face.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = coord
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def _image_quad(path: str, x: float, y: float, side: float) -> None:
    """Vignette agrandie au PLUS PROCHE VOISIN : on regarde les pixels, pas un flou."""
    obj = _quad("tile_" + os.path.basename(path), x, y, side, side, z=0.0)
    mat = bpy.data.materials.new("m_" + os.path.basename(path))
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    tex = tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    tex.image.colorspace_settings.name = "sRGB"
    tex.interpolation = "Closest"
    tex.extension = "EXTEND"
    emission = tree.nodes.new("ShaderNodeEmission")
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(tex.outputs["Color"], emission.inputs[0])
    tree.links.new(emission.outputs[0], out.inputs[0])
    obj.data.materials.append(mat)


def _rect(x: float, y: float, w: float, h: float, color, strength: float = 1.0) -> None:
    obj = _quad(f"rect{x}_{y}", x, y, w, h, z=-1.0)
    mat = bpy.data.materials.new(f"mr{x}_{y}")
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    emission = tree.nodes.new("ShaderNodeEmission")
    emission.inputs[0].default_value = (*color, 1.0)
    emission.inputs[1].default_value = strength
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(emission.outputs[0], out.inputs[0])
    obj.data.materials.append(mat)


def _text(body: str, x: float, y: float, size: float, color=INK,
          align: str = "LEFT") -> None:
    """Texte en coordonnees PLANCHE. `y` est la LIGNE DE BASE."""
    curve = bpy.data.curves.new(body[:24], type="FONT")
    curve.body = body
    curve.size = size
    curve.align_x = align
    obj = bpy.data.objects.new("t_" + body[:20], curve)
    obj.location = (x, PLATE_H - y, 1.0)
    mat = bpy.data.materials.new("mt_" + body[:20])
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    emission = tree.nodes.new("ShaderNodeEmission")
    emission.inputs[0].default_value = (*color, 1.0)
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(emission.outputs[0], out.inputs[0])
    obj.data.materials.append(mat)
    bpy.context.collection.objects.link(obj)


LEFT = 296.0        #: largeur de la colonne des libelles
MARGIN = 26.0
GAP = 6.0
BLOCK_GAP = 46.0
TOP = 152.0
ROW_GAP = 10.0
CLOSEUP_X = 1442.0


def _compose(rendered: dict, reports: list[dict], out: str) -> None:
    _layout_scene()
    block_w = 3 * TILE + 2 * GAP
    x8 = LEFT
    x24 = x8 + block_w + BLOCK_GAP
    rows = _rows()
    grid_h = len(rows) * TILE + (len(rows) - 1) * ROW_GAP

    _text("BRIEF-0086 - le bolide et son eclat : la silhouette survit-elle a 8 pixels ?",
          MARGIN, 50, 31)
    _text("A 96 m de camera, 115 m de cadre pour 540 px de rendu utile : une piece de 1,7 m "
          "occupe 8 px. Camera ORTHOGRAPHIQUE, sphere temoin de MEME diametre, meme cadre, "
          "meme lumiere.", MARGIN, 84, 17, DIM)
    _text("Agrandissement au plus proche voisin (x12 et x4) : on regarde les vrais pixels, "
          "grossis - jamais un reechantillonnage qui les lisserait.", MARGIN, 110, 17, DIM)

    _text("8 PIXELS - trois poses de chute", x8, TOP - 14, 21, WARN)
    _text("24 PIXELS", x24, TOP - 14, 21, WARN)
    _text("TROIS QUARTS EN CHUTE - l'angle reel", CLOSEUP_X, TOP - 14, 19, WARN)

    for row, (key, label, _kind, _mode, _piece) in enumerate(rows):
        y = TOP + row * (TILE + ROW_GAP)
        witness = key.startswith("sphere")
        if witness:
            _rect(MARGIN - 10, y - 5, x24 + block_w - MARGIN + 20, TILE + 10,
                  (0.065, 0.065, 0.090))
        colour = DIM if witness else INK
        _text(label[0], MARGIN, y + TILE * 0.5 - 4, 21, colour)
        _text(label[1], MARGIN, y + TILE * 0.5 + 22, 16, DIM)
        for block, (pixels, _frame, _zoom) in enumerate(BLOCKS):
            base_x = (x8, x24)[block]
            for index in range(len(POSES_DEG)):
                _image_quad(rendered["tiles"][(key, pixels, index)],
                            base_x + index * (TILE + GAP), y, TILE)

    # --- la colonne de droite : deux vues de trois quarts, a la taille reelle
    captions = (
        ("bolide_lit", f"Bolide - {BOLIDE_SIZE[2]:.2f} x {BOLIDE_SIZE[0]:.2f} x "
                       f"{BOLIDE_SIZE[1]:.2f} m - albedo livre, lumiere du jeu"),
        ("shard_lit", f"Shard - {SHARD_SIZE[2]:.2f} x {SHARD_SIZE[0]:.2f} x "
                      f"{SHARD_SIZE[1]:.2f} m - albedo livre, lumiere du jeu"),
    )
    for index, (key, caption) in enumerate(captions):
        y = TOP + index * (CLOSEUP + (grid_h - 2 * CLOSEUP))
        _image_quad(rendered["tiles"][(key, "closeup", 0)], CLOSEUP_X, y, CLOSEUP)
        _text(caption, CLOSEUP_X + 8, y + CLOSEUP - 14, 16, DIM)

    # --- le verdict, chiffre -------------------------------------------
    foot = TOP + grid_h + 34
    measures = rendered["measures"]
    for index, (piece_key, sphere_key, label) in enumerate(
            (("bolide_flat", "sphere_flat", "Bolide"), ("shard_lit", "sphere_lit", "Shard"))):
        ious = [_iou(measures[(piece_key, 8, i)]["mask"],
                     measures[(sphere_key, 8, i)]["mask"]) for i in range(len(POSES_DEG))]
        boxes = [measures[(piece_key, 8, i)]["boite"] for i in range(len(POSES_DEG))]
        pix = [measures[(piece_key, 8, i)]["pixels"] for i in range(len(POSES_DEG))]
        spix = [measures[(sphere_key, 8, i)]["pixels"] for i in range(len(POSES_DEG))]
        _text(f"{label} a 8 px : boites {', '.join(f'{b[0]}x{b[1]}' for b in boxes)} px   |   "
              f"{min(pix)}-{max(pix)} px allumes contre {min(spix)}-{max(spix)} pour la "
              f"sphere ({min(pix) / max(1, min(spix)) - 1:+.0%} a "
              f"{max(pix) / max(1, max(spix)) - 1:+.0%})   |   "
              f"recouvrement piece/sphere {min(ious):.0%}-{max(ious):.0%}",
              MARGIN, foot + index * 27, 18, GOOD)

    r = {x["nom"]: x for x in reports}
    _text(f"Bolide {r['Bolide']['triangles']} tri (plafond 400)  .  "
          f"Shard {r['Shard']['triangles']} tri (plafond 150)  .  "
          f"projection en boite a {ROCK_METRES_PER_TILE:.0f} m/tuile "
          f"({1.0 / ROCK_METRES_PER_TILE:.3f} tuile/m), la MEME echelle monde que les trois "
          f"asteroides du survol  .  aucune texture, aucun emissif dans les .glb (ADR-0028)",
          MARGIN, foot + 2 * 27 + 8, 16, DIM)
    _text("⚠ Cette planche ne simule PAS le bloom du jeu. glow_hdr_threshold = 1,6 et le "
          "bolide est pose a 3,4 d'emission : en jeu un halo s'ajoute autour de la ligne 1 "
          "et arrondit son contour. Voir le compte-rendu.",
          MARGIN, foot + 2 * 27 + 36, 16, WARN)

    bpy.context.scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"-> {out}")


def plate(reports: list[dict]) -> None:
    outdir = tempfile.mkdtemp(prefix="aegis-plate-")
    try:
        rendered = _render_tiles(outdir)
        _print_plate(rendered)
        _compose(rendered, reports, os.path.join(ROOT, PLATE_PNG))
    finally:
        for leftover in os.listdir(outdir):
            os.remove(os.path.join(outdir, leftover))
        os.rmdir(outdir)


def _print_plate(rendered: dict) -> None:
    measures = rendered["measures"]
    print("\n  --- recette de silhouette (mesuree sur les vignettes rendues) ---")
    for piece_key, sphere_key, label in (("bolide_flat", "sphere_flat", "Bolide"),
                                         ("shard_lit", "sphere_lit", "Shard")):
        for pixels, _frame, _zoom in BLOCKS:
            ious = [_iou(measures[(piece_key, pixels, i)]["mask"],
                         measures[(sphere_key, pixels, i)]["mask"])
                    for i in range(len(POSES_DEG))]
            boxes = [measures[(piece_key, pixels, i)]["boite"]
                     for i in range(len(POSES_DEG))]
            pix = [measures[(piece_key, pixels, i)]["pixels"] for i in range(len(POSES_DEG))]
            spix = [measures[(sphere_key, pixels, i)]["pixels"] for i in range(len(POSES_DEG))]
            sboxes = [measures[(sphere_key, pixels, i)]["boite"]
                      for i in range(len(POSES_DEG))]
            # Le temoin doit etre IMMOBILE d'une pose a l'autre : c'est la moitie de la
            # demonstration. On le mesure au lieu de l'affirmer.
            steady = [_iou(measures[(sphere_key, pixels, 0)]["mask"],
                           measures[(sphere_key, pixels, i)]["mask"])
                      for i in range(1, len(POSES_DEG))]
            print(f"    {label:<7} a {pixels:>2} px : boites "
                  f"{', '.join(f'{b[0]}x{b[1]}' for b in boxes)} | "
                  f"{min(pix)}-{max(pix)} px allumes contre {min(spix)}-{max(spix)} (sphere) | "
                  f"recouvrement {min(ious):.0%}-{max(ious):.0%}")
            print(f"      temoin sphere : boites "
                  f"{', '.join(f'{b[0]}x{b[1]}' for b in sboxes)} | "
                  f"immobilite d'une pose a l'autre {min(steady):.0%}")
    print()


def main() -> None:
    reports = build()
    _print(reports)
    if "--plate" in sys.argv:
        plate(reports)


if __name__ == "__main__":
    main()
