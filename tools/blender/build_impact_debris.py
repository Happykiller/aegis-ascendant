"""build_impact_debris.py — le bolide et son eclat (BRIEF-0086).

    blender45 -b -P tools/blender/build_impact_debris.py
    blender45 -b -P tools/blender/build_impact_debris.py -- --plate
    ./scripts/build-hull.sh --check impact_debris     # + controle de determinisme

Produit `assets/imported/models/vfx/bolide.glb` et `assets/imported/models/vfx/impact_shard.glb`
et, avec `--plate`, `docs/forge/output/BRIEF-0086-planche-silhouettes.png`.

Le script EST la source des deux assets (ADR-0008) : aucun `.blend` versionne, aucun alea, deux
executions successives rendent les memes sha256. Neuf harnais de mesure tournent a chaque build et
**tous echouent le build** — voir `_audit()`.


CE QUI DECIDE DE CES DEUX COQUES : ELLES FONT 8 PIXELS
======================================================
Le bolide tombe sur une lune posee a 96 unites de la camera. A cette distance le cadre visible fait
~115 m de haut pour 540 px de rendu utile : **une piece de 1,7 m occupe 8 pixels**. Le chiffre est
donne par le brief, mesure et non estime, et il commande tout ce qui suit.

1. **Rien sous ~40 cm.** Un detail plus petit n'est jamais echantillonne : le payer en triangles,
   c'est payer du bruit. `_min_feature()` mesure la plus petite arete du polyedre AVANT
   triangulation et echoue le build si elle descend sous 0,20 m.
2. **Le budget va dans la SILHOUETTE.** A 8 px on ne lit qu'un contour : sa proportion, ses coins,
   et surtout la facon dont il CHANGE quand la piece tourne. Une sphere ne change jamais.
3. **Les budgets du brief sont des plafonds.** 400 triangles pour le bolide, 150 pour l'eclat ; on
   livre 5 a 10 fois moins, parce qu'un triangle de plus ne se verrait pas.

⚠️ **ET LE BOLIDE EST RENDU NON ECLAIRE.** `moon_flyby.gd` lui pose un `StandardMaterial3D` en
`SHADING_MODE_UNSHADED` avec emission x3,4 : en jeu, **aucune facette ne se voit**, la piece est un
aplat orange. Toute l'information tient donc dans son CONTOUR — c'est ce qui interdit une patate
convexe et impose des aretes longues et des proportions franches. La planche de recette rend le
bolide dans ce mode exact (ligne 1) et sous la lumiere du jeu (ligne 2, au cas ou l'emission serait
adoucie plus tard).


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

#: Plus petite arete toleree sur le polyedre (avant triangulation). En dessous, on paie un
#: detail que le rendu n'echantillonne jamais — voir l'en-tete.
MIN_FEATURE_M = 0.20

#: Albedo LINEAIRE de la roche. Copie exacte de `moon_flyby.ROCK_ALBEDO`, elle-meme reprise
#: de `scripts/vfx/moon_flyby.gd` ou elle a ete validee en capture. Froide (B > R), sombre,
#: aucun emissif. Aucune couleur de la charte ne convient : ses palettes sont des palettes de
#: FACTION, et un caillou n'en a pas.
ROCK_ALBEDO = (0.100, 0.098, 0.118)

#: Dimensions VOULUES, dans le repere Godot (X largeur, Y hauteur, Z longueur).
#: ⚠️ Le contrat de noms dit « plus long que large » : Z > X, et le harnais le verifie.
BOLIDE_SIZE = (1.62, 1.30, 2.50)
SHARD_SIZE = (0.46, 0.26, 1.00)

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
           cuts: tuple[tuple[tuple[float, float, float], float], ...]) -> bmesh.types.BMesh:
    """Une boite taillee par une liste de plans. Convexe, facettes franches, peu de triangles."""
    bm = bmesh.new()
    _box(bm, size)
    for normal, offset in cuts:
        _cut(bm, normal, offset)
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
#:   * l'ALLONGEMENT (2,50 pour 1,62 de large) : c'est lui qui distingue la piece d'un point ;
#:   * l'ASYMETRIE avant/arriere : l'avant est massif, l'arriere pointu — en tournant, le
#:     contour passe d'un trapeze court a un fuseau long, et cette pulsation est LE signal ;
#:   * deux grandes facettes franches (la cassure avant-bas et le flanc babord), pour le jour
#:     ou le code adoucirait l'emission.
BOLIDE_CUTS = (
    ((-0.20, -0.78, -0.60), 0.62),   # grande cassure avant-bas : LA facette principale
    ((0.86, 0.44, 0.14), 0.72),      # long flanc tribord, presque plan
    ((-0.90, 0.16, 0.36), 0.70),     # flanc babord, moins profond : la piece est dissymetrique
    ((0.10, 0.80, 0.58), 0.92),      # l'arriere-haut se rabat : la queue s'affine
    ((-0.34, 0.72, -0.60), 0.88),    # l'arriere-bas aussi : la queue finit en arete
    ((0.30, -0.62, 0.72), 0.90),     # epaulement avant-haut, franc
    ((0.05, -0.12, -0.99), 0.55),    # ventre plat : une assise, pas une bosse
    ((0.62, -0.70, -0.35), 1.00),    # eclat de coin avant-tribord
)

#: L'ECLAT — « l'echarde ». Une lame plate qui pointe vers l'avant et se casse net a
#: l'arriere. A 8 px c'est un TRAIT, pas une tache : c'est exactement ce qu'on veut d'un
#: morceau arrache. L'epaisseur decroit de la cassure vers la pointe.
SHARD_CUTS = (
    ((0.70, -0.71, 0.08), 0.30),     # taille tribord vers la pointe
    ((-0.66, -0.74, -0.14), 0.30),   # taille babord vers la pointe
    ((0.38, 0.88, 0.28), 0.44),      # cassure arriere, facette 1
    ((-0.30, 0.86, -0.42), 0.44),    # cassure arriere, facette 2
    ((0.06, -0.30, 0.95), 0.19),     # la lame s'amincit vers l'avant (dessus)
    ((-0.10, -0.22, -0.97), 0.20),   # et vers l'avant (dessous)
)


def build_piece(name: str, godot_size: tuple[float, float, float],
                cuts) -> tuple[bpy.types.Object, dict]:
    """Taille la piece, la recentre, la triangule, la deplie et rend ses mesures d'atelier."""
    bm = _chunk(_author_size(godot_size), cuts)
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

    # 9. densite de texels : la MEME echelle monde que les rochers du survol
    if density and not (ROCK_METRES_PER_TILE * 0.55 <= density["moyenne_m_par_tuile"]
                        <= ROCK_METRES_PER_TILE * 1.45):
        problems.append(f"densite de texels hors cible : {density['moyenne_m_par_tuile']:.2f} "
                        f"m/tuile, attendu {ROCK_METRES_PER_TILE:.1f}")

    # 10. rien sous MIN_FEATURE_M — voir l'en-tete
    if stats["min_feature_m"] < MIN_FEATURE_M:
        problems.append(f"plus petite arete {stats['min_feature_m']:.3f} m < "
                        f"{MIN_FEATURE_M} m : detail jamais echantillonne a 8 px")

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
    ("Bolide", BOLIDE_SIZE, BOLIDE_CUTS, TRI_BUDGET_BOLIDE, BOLIDE_GLB),
    ("Shard", SHARD_SIZE, SHARD_CUTS, TRI_BUDGET_SHARD, SHARD_GLB),
)


def build() -> list[dict]:
    """Les deux pieces, chacune dans sa scene propre et son propre `.glb`."""
    reports = []
    for name, size, cuts, budget, path in PIECES:
        _reset()
        obj, stats = build_piece(name, size, cuts)
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
        print(f"    plus petite arete : {r['min_feature_m']:.3f} m (plancher {MIN_FEATURE_M})")
        print(f"    materiaux       : {', '.join(r['materiaux'])} — aucune texture, aucun emissif")
    print()


def main() -> None:
    reports = build()
    _print(reports)
    if "--plate" in sys.argv:
        import build_impact_debris_plate  # noqa: F401  (jamais atteint : voir plus bas)


if __name__ == "__main__":
    main()
