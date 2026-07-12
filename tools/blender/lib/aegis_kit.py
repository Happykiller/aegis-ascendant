"""aegis_kit — bibliotheque hard-surface partagee des coques d'Aegis Ascendant.

Cette bibliotheque est la *source de coherence* entre les cinq coques du jeu
(Specter-9, Needle Scout, Choir Harvester, Pale Leviathan, Aegis Citadel).
Elle n'implemente **aucune** geometrie specifique a une coque : uniquement des
outils generiques, la palette normative, les materiaux normalises, l'export
glTF conforme a l'ADR-0008 et la validation de contrat.

Blender 4.5 LTS, headless uniquement (`blender45 -b -P <script>`).


REPERE D'AUTEUR (ADR-0008)
==========================
On modelise dans le repere Blender (Z-up) impose par l'ADR-0008 :

    nez     -> -Y
    dessus  -> +Z

*** PIEGE MAJEUR, lire avant de placer un point d'attache ***

Dans ce repere, le cote **BABORD (port, gauche du vaisseau) est +X** et le
cote **TRIBORD (starboard, droite) est -X**. C'est contre-intuitif : c'est la
consequence mecanique du choix "nez vers -Y" (right = forward x up = -X).

N'ecrivez jamais un signe de X a la main pour un element lateral :
utilisez `PORT` / `STARBOARD` ou, mieux, `attach_pair()` qui pose
automatiquement le `_L` a babord et le `_R` a tribord.


CORRECTION D'AXE A L'EXPORT (important)
=======================================
L'ADR-0008 affirme que le repere d'auteur ci-dessus donne, apres
`export_yup=True`, un nez vers -Z dans Godot. **C'est faux**, et c'est verifie :
l'exporteur glTF de Blender applique (x, y, z) -> (x, z, -y), donc un nez
modelise en -Y ressort en **+Z** cote Godot, c'est-a-dire vers le BAS de
l'ecran : toutes les coques voleraient a reculons.

Les deux regles de l'ADR sont inconciliables telles quelles. On conserve la
regle normative qui porte le gameplay (**nez vers -Z dans Godot**, vers le haut
de l'ecran) et on conserve aussi le repere d'auteur (**nez vers -Y**) pour que
les cinq coques, produites separement, restent interoperables.

`export_hull()` reconcilie les deux en appliquant, en un seul endroit, une
rotation de 180 deg autour de Z juste avant l'export. Composee avec `yup`, la
transformation totale vaut :

    (x, y, z)_auteur  ->  (-x, z, y)_glTF/Godot

    nez     -Y  ->  -Z   (haut de l'ecran)   OK
    dessus  +Z  ->  +Y                        OK
    babord  +X  ->  -X   (gauche Godot)       OK  (rotation rigide, pas un miroir)

C'est une rotation rigide : elle ne miroite pas la coque, elle la retourne.
Aucun script de coque ne doit refaire cette correction : elle vit ici.
Le contrat est re-verifie *sur le .glb produit* (pas sur la scene en memoire)
par `export_hull()`, qui relit le fichier binaire et echoue si l'orientation,
la bounding box, le budget, les materiaux ou les points d'attache sont hors
contrat.
"""

from __future__ import annotations

import json
import math
import os
import random
import shutil
import struct
import tempfile
from dataclasses import dataclass, field

import bmesh
import bpy
from mathutils import Matrix, Vector

VERSION = "1.0.0"

# --------------------------------------------------------------------------
# Repere d'auteur
# --------------------------------------------------------------------------

#: Signe de X du cote babord (gauche du vaisseau) dans le repere d'auteur.
PORT = 1.0
#: Signe de X du cote tribord (droite du vaisseau) dans le repere d'auteur.
STARBOARD = -1.0

#: Rotation appliquee a l'export pour honorer "nez vers -Z" cote Godot.
_AXIS_FIX = Matrix.Rotation(math.pi, 4, "Z")

#: Conversion Z-up -> Y-up appliquee par l'exporteur glTF de Blender.
#: (x, y, z) -> (x, z, -y). Constatee empiriquement sur Blender 4.5.11, pas
#: supposee : c'est elle qui invalide la phrase d'orientation de l'ADR-0008.
_YUP = Matrix(
    ((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1))
)

#: Chaine complete voulue : (x, y, z)_auteur -> (-x, z, y)_glTF.
_EXPECTED_CHAIN = Matrix(
    ((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))
)


def _assert_axis_chain() -> None:
    """Verifie analytiquement la chaine d'axes avant tout export.

    Si quelqu'un « corrige » `_AXIS_FIX` en identite (en suivant l'ADR-0008 au
    pied de la lettre), toutes les coques volent a reculons. La bounding box ne
    le voit pas : elle est symetrique, min/max Z sont inchanges par un
    demi-tour. Ce controle-ci, lui, le voit tout de suite.
    """
    chain = _YUP @ _AXIS_FIX
    for axis, expected, label in (
        (Vector((0, -1, 0)), Vector((0, 0, -1)), "nez (-Y auteur -> -Z Godot)"),
        (Vector((0, 0, 1)), Vector((0, 1, 0)), "dessus (+Z auteur -> +Y Godot)"),
        (Vector((1, 0, 0)), Vector((-1, 0, 0)), "babord (+X auteur -> -X Godot)"),
    ):
        got = chain.to_3x3() @ axis
        if (got - expected).length > 1e-6:
            raise ContractError(
                "chaine d'axes rompue — " + label + f" : obtenu {tuple(got)}, "
                f"attendu {tuple(expected)}. Voir l'en-tete d'aegis_kit."
            )


class ContractError(RuntimeError):
    """Le livrable ne respecte pas le contrat de l'ADR-0008 : on echoue fort."""


# --------------------------------------------------------------------------
# Palette et materiaux normalises (charte SS3 + ADR-0008)
# --------------------------------------------------------------------------

FACTION_VANGUARD = "vanguard"
FACTION_NULL_CHOIR = "null_choir"

#: Couleurs de la charte creative, en sRGB hexadecimal.
PALETTES: dict[str, dict[str, str]] = {
    FACTION_VANGUARD: {
        "hull": "#EDEAE3",       # blanc casse   - coques
        "panel": "#1C2B5E",      # bleu profond  - panneaux
        "trim": "#E4B54A",       # or            - accents, insignes
        "greeble": "#24252B",    # anthracite    - mecanique, creux
        "glass": "#0D1119",      # verriere sombre
        "emissive": "#3FD9E8",   # cyan          - tuyeres, lignes lumineuses
        "marking": "#C93A31",    # rouge securite- marquages restreints
    },
    FACTION_NULL_CHOIR: {
        "hull": "#24252B",       # anthracite    - coques
        "panel": "#452663",      # violet sombre - segments
        "trim": "#DDDCD2",       # ivoire froid  - carapaces
        "greeble": "#141419",    # anthracite tres sombre - creux
        "glass": "#0A0910",      # membrane sombre
        "emissive": "#D93D9C",   # magenta       - lumieres, armes
        "marking": "#7C9E52",    # vert maladif  - usage tres limite
    },
}

#: Ordre canonique des slots de materiau. L'index d'un materiau dans cette
#: liste EST son `material_index` sur toutes les coques : il est stable.
MATERIAL_ORDER: tuple[str, ...] = (
    "AA_Hull",
    "AA_Panel",
    "AA_Trim",
    "AA_Greeble",
    "AA_Glass",
    "AA_Emissive_Engine",
    "AA_Marking_Red",
)

#: (cle de palette, metallic, roughness, alpha, emission_strength)
_MATERIAL_SPECS: dict[str, tuple[str, float, float, float, float]] = {
    "AA_Hull": ("hull", 0.05, 0.45, 1.0, 0.0),
    "AA_Panel": ("panel", 0.15, 0.40, 1.0, 0.0),
    "AA_Trim": ("trim", 0.85, 0.28, 1.0, 0.0),
    "AA_Greeble": ("greeble", 0.75, 0.55, 1.0, 0.0),
    "AA_Glass": ("glass", 0.00, 0.08, 0.86, 0.0),
    "AA_Emissive_Engine": ("emissive", 0.00, 0.30, 1.0, 2.5),
    "AA_Marking_Red": ("marking", 0.00, 0.50, 1.0, 0.0),
}

_faction: str = FACTION_VANGUARD


def set_faction(faction: str) -> None:
    """Choisit la palette (`FACTION_VANGUARD` ou `FACTION_NULL_CHOIR`).

    A appeler **une seule fois**, avant toute creation de materiau : les noms
    de materiaux (`AA_Hull`...) sont identiques d'une faction a l'autre, car
    les scenes Godot s'y raccrochent. Melanger deux factions dans une meme
    coque n'a donc pas de sens et est refuse.
    """
    global _faction
    if faction not in PALETTES:
        raise ContractError(f"faction inconnue : {faction!r}")
    if bpy.data.materials and faction != _faction:
        raise ContractError(
            "set_faction() apres creation de materiaux : une coque = une faction."
        )
    _faction = faction


def srgb_hex_to_linear(hex_color: str) -> tuple[float, float, float, float]:
    """Convertit "#RRGGBB" (sRGB) en RGBA lineaire (ce que Blender attend)."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        raise ContractError(f"couleur hex invalide : {hex_color!r}")
    out: list[float] = []
    for i in (0, 2, 4):
        c = int(h[i : i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], 1.0)


def material(name: str) -> bpy.types.Material:
    """Retourne le materiau normalise `name`, memoise (un seul datablock)."""
    if name not in _MATERIAL_SPECS:
        raise ContractError(
            f"materiau non normalise : {name!r} (attendus : {list(MATERIAL_ORDER)})"
        )
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing

    key, metallic, roughness, alpha, emission = _MATERIAL_SPECS[name]
    color = srgb_hex_to_linear(PALETTES[_faction][key])

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Alpha"].default_value = alpha
    if emission > 0.0:
        bsdf.inputs["Emission Color"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = emission
    else:
        bsdf.inputs["Emission Strength"].default_value = 0.0
    if alpha < 1.0:
        # Blender 4.2+ : `blend_method` est deprecie mais c'est encore lui que
        # l'exporteur glTF lit pour decider `alphaMode`. On regle les deux.
        mat.blend_method = "BLEND"
        mat.surface_render_method = "BLENDED"
        bsdf.inputs["Transmission Weight"].default_value = 0.30
    mat.diffuse_color = color  # utile en rendu de controle
    return mat


def mat_index(name: str) -> int:
    """Index de slot stable du materiau `name` (voir `MATERIAL_ORDER`)."""
    try:
        return MATERIAL_ORDER.index(name)
    except ValueError as exc:  # pragma: no cover - garde-fou
        raise ContractError(f"materiau non normalise : {name!r}") from exc


def apply_material_slots(mesh: bpy.types.Mesh) -> None:
    """Pose les 7 slots normalises sur `mesh`, dans l'ordre de `MATERIAL_ORDER`.

    PIEGE BLENDER : `mesh.materials.clear()` remet a **zero** le
    `material_index` de tous les polygones. Poser les slots apres un
    `bmesh.to_mesh()` effacerait donc silencieusement toute l'assignation de
    materiaux (tout repasse en `AA_Hull`, sans le moindre avertissement).
    Les slots doivent etre poses **avant** le transfert du BMesh : c'est ce que
    fait `new_object()`, et c'est pourquoi cette fonction refuse d'ecraser des
    slots existants.
    """
    if list(mesh.materials):
        raise ContractError(
            f"{mesh.name} : slots de materiaux deja poses — les reposer "
            "remettrait tous les material_index a zero."
        )
    for name in MATERIAL_ORDER:
        mesh.materials.append(material(name))


# --------------------------------------------------------------------------
# Scene
# --------------------------------------------------------------------------


def reset_scene() -> None:
    """Repart d'une scene vide et de reglages d'usine (build reproductible)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for collection in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.objects,
        bpy.data.lights,
        bpy.data.cameras,
    ):
        for datablock in list(collection):
            collection.remove(datablock)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def new_object(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    """Cree un objet maille depuis un `BMesh`, avec les 7 slots normalises.

    Le `BMesh` est consomme (free) : ne pas le reutiliser apres l'appel.
    Les slots sont poses **avant** le transfert (cf. `apply_material_slots`).
    """
    mesh = bpy.data.meshes.new(name)
    apply_material_slots(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# --------------------------------------------------------------------------
# Primitives et helpers hard-surface
# --------------------------------------------------------------------------


def add_ring(
    bm: bmesh.types.BMesh, points: list[tuple[float, float, float]]
) -> list[bmesh.types.BMVert]:
    """Cree une boucle de sommets (non fermee par une face)."""
    return [bm.verts.new(p) for p in points]


def bridge_rings(
    bm: bmesh.types.BMesh,
    ring_a: list[bmesh.types.BMVert],
    ring_b: list[bmesh.types.BMVert],
    material: str,
    closed: bool = True,
) -> list[bmesh.types.BMFace]:
    """Relie deux boucles de meme longueur par une bande de quads.

    `closed=True` : les boucles sont cycliques (tube). `closed=False` : bande
    ouverte (nappe). Retourne les faces creees, dans l'ordre des segments,
    ce qui permet de les selectionner ensuite par index (panneaux, marquages).
    """
    if len(ring_a) != len(ring_b):
        raise ContractError("bridge_rings : boucles de tailles differentes")
    idx = mat_index(material)
    n = len(ring_a)
    count = n if closed else n - 1
    faces: list[bmesh.types.BMFace] = []
    for i in range(count):
        j = (i + 1) % n
        quad = (ring_a[i], ring_a[j], ring_b[j], ring_b[i])
        # Une section peut degenerer (pointe, pole) : on saute les doublons.
        if len(set(quad)) < 3:
            faces.append(None)  # type: ignore[arg-type]
            continue
        verts = []
        for v in quad:
            if v not in verts:
                verts.append(v)
        try:
            face = bm.faces.new(verts)
        except ValueError:
            face = None  # face deja existante (jonction de poles)
        if face is not None:
            face.material_index = idx
        faces.append(face)  # type: ignore[arg-type]
    return faces


def fan_to_point(
    bm: bmesh.types.BMesh,
    ring: list[bmesh.types.BMVert],
    apex: bmesh.types.BMVert,
    material: str,
    closed: bool = True,
) -> list[bmesh.types.BMFace]:
    """Ferme une boucle par un eventail de triangles vers `apex` (nez, pole)."""
    idx = mat_index(material)
    n = len(ring)
    count = n if closed else n - 1
    faces = []
    for i in range(count):
        a, b = ring[i], ring[(i + 1) % n]
        if len({a, b, apex}) < 3:
            continue
        try:
            face = bm.faces.new((a, b, apex))
        except ValueError:
            continue
        face.material_index = idx
        faces.append(face)
    return faces


def cap_ring(
    bm: bmesh.types.BMesh, ring: list[bmesh.types.BMVert], material: str
) -> bmesh.types.BMFace | None:
    """Ferme une boucle par une n-gon (culot arriere)."""
    try:
        face = bm.faces.new(ring)
    except ValueError:
        return None
    face.material_index = mat_index(material)
    return face


def add_box(
    bm: bmesh.types.BMesh,
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    material: str,
) -> list[bmesh.types.BMFace]:
    """Boite alignee sur les axes. Retourne ses 6 faces."""
    idx = mat_index(material)
    res = bmesh.ops.create_cube(bm, size=1.0)
    verts = res["verts"]
    bmesh.ops.scale(bm, vec=Vector(size), verts=verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=verts)
    faces = {f for v in verts for f in v.link_faces}
    out = []
    for face in faces:
        if all(v in verts for v in face.verts):
            face.material_index = idx
            out.append(face)
    return out


def add_lathe(
    bm: bmesh.types.BMesh,
    contour: list[tuple[float, float, str]],
    segments: int,
    center_x: float = 0.0,
    center_z: float = 0.0,
) -> list[list[bmesh.types.BMFace]]:
    """Solide de revolution autour de l'axe Y (l'axe longitudinal du vaisseau).

    `contour` : liste ordonnee de `(y, radius, material)` decrivant le profil.
    Le `material` d'un point s'applique au segment qui part de ce point vers le
    suivant (celui du dernier point est ignore). Un point de rayon 0 est un
    pole : il est ferme par un eventail.

    Sert aux tuyeres, aux canons, aux noyaux : c'est la primitive ronde
    commune a toutes les coques.
    """
    if segments < 3:
        raise ContractError("add_lathe : segments >= 3")
    rings: list[list[bmesh.types.BMVert] | bmesh.types.BMVert] = []
    for y, radius, _ in contour:
        if radius <= 1e-6:
            rings.append(bm.verts.new((center_x, y, center_z)))
            continue
        pts = []
        for s in range(segments):
            a = 2.0 * math.pi * s / segments
            pts.append(
                (
                    center_x + radius * math.cos(a),
                    y,
                    center_z + radius * math.sin(a),
                )
            )
        rings.append(add_ring(bm, pts))

    bands: list[list[bmesh.types.BMFace]] = []
    for i in range(len(contour) - 1):
        mat = contour[i][2]
        a, b = rings[i], rings[i + 1]
        if isinstance(a, bmesh.types.BMVert) and isinstance(b, list):
            bands.append(fan_to_point(bm, b, a, mat))
        elif isinstance(b, bmesh.types.BMVert) and isinstance(a, list):
            bands.append(fan_to_point(bm, a, b, mat))
        elif isinstance(a, list) and isinstance(b, list):
            bands.append([f for f in bridge_rings(bm, a, b, mat) if f is not None])
        else:  # deux poles consecutifs : rien a construire
            bands.append([])
    return bands


def inset_panel(
    bm: bmesh.types.BMesh,
    faces: list[bmesh.types.BMFace],
    material: str,
    thickness: float = 0.012,
    depth: float = -0.008,
) -> list[bmesh.types.BMFace]:
    """Decoupe/enfonce un panneau : `inset_region` puis materiau sur le fond.

    C'est le detail par la geometrie exige par l'ADR-0008 : le bord du panneau
    reste en `AA_Hull`, le fond enfonce prend `material`. `depth < 0` creuse.
    """
    faces = [f for f in faces if f is not None and f.is_valid]
    if not faces:
        return []
    res = bmesh.ops.inset_region(
        bm,
        faces=faces,
        use_boundary=True,
        use_even_offset=True,
        thickness=thickness,
        depth=depth,
    )
    # inset_region retourne les faces de *bordure* ; les faces d'origine
    # (passees en entree) restent le fond du panneau.
    idx = mat_index(material)
    for face in faces:
        if face.is_valid:
            face.material_index = idx
    return res["faces"]


def set_material(faces: list[bmesh.types.BMFace], material: str) -> None:
    """Assigne un materiau a un ensemble de faces (tolere les `None`)."""
    idx = mat_index(material)
    for face in faces:
        if face is not None and face.is_valid:
            face.material_index = idx


def greeble_strip(
    bm: bmesh.types.BMesh,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    count: int,
    seed: int,
    material: str = "AA_Greeble",
    size_range: tuple[float, float] = (0.012, 0.030),
    height_range: tuple[float, float] = (0.006, 0.018),
    jitter: float = 0.006,
) -> list[bmesh.types.BMFace]:
    """Bandeau de greebles : petites boites semees le long d'un segment.

    Deterministe : entierement pilote par `seed` (ADR-0008, determinisme).
    """
    rng = random.Random(seed)
    sx, sy, sz = start
    ex, ey, ez = end
    faces: list[bmesh.types.BMFace] = []
    for i in range(count):
        t = (i + 0.5) / count
        cx = sx + (ex - sx) * t + rng.uniform(-jitter, jitter)
        cy = sy + (ey - sy) * t + rng.uniform(-jitter, jitter)
        cz = sz + (ez - sz) * t
        w = rng.uniform(*size_range)
        d = rng.uniform(*size_range)
        h = rng.uniform(*height_range)
        faces += add_box(bm, (cx, cy, cz + h * 0.5), (w, d, h), material)
    return faces


def mirror_x(bm: bmesh.types.BMesh, merge_dist: float = 1e-4) -> None:
    """Duplique toute la geometrie en miroir par rapport au plan X=0, et soude.

    A utiliser quand on n'a construit qu'une moitie de coque. Le winding des
    faces dupliquees est inverse (un miroir retourne l'orientation), sinon les
    normales de la moitie ajoutee pointeraient vers l'interieur.

    On evite volontairement `bmesh.ops.symmetrize`, dont l'enum `direction`
    ("quelle moitie garde-t-on ?") se prend a l'envers une fois sur deux.
    """
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.duplicate(bm, geom=geom)
    created = res["geom"]
    for elem in created:
        if isinstance(elem, bmesh.types.BMVert):
            elem.co.x = -elem.co.x
    faces = [e for e in created if isinstance(e, bmesh.types.BMFace)]
    if faces:
        bmesh.ops.reverse_faces(bm, faces=faces)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=merge_dist)


def bevel_sharp_edges(
    obj: bpy.types.Object,
    width: float = 0.005,
    segments: int = 2,
    angle_deg: float = 28.0,
) -> None:
    """Biseaute les aretes vives : c'est ce qui accroche la lumiere.

    Seules les aretes manifold dont l'angle entre faces depasse `angle_deg`
    sont biseautees. `clamp_overlap` evite l'auto-intersection sur les bords
    minces (bords d'aile, levres de tuyere).
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    limit = math.radians(angle_deg)
    edges = [
        e
        for e in bm.edges
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > limit
    ]
    if edges:
        bmesh.ops.bevel(
            bm,
            geom=edges,
            offset=width,
            offset_type="OFFSET",
            segments=segments,
            profile=0.5,
            affect="EDGES",
            clamp_overlap=True,
            # -1 = heriter du materiau des faces adjacentes. Le defaut de
            # bmesh (`material=0`) forcerait TOUS les chanfreins en AA_Hull :
            # les tuyeres emissives se retrouveraient cerclees de blanc.
            material=-1,
            miter_outer="SHARP",
            miter_inner="SHARP",
        )
    bm.to_mesh(obj.data)
    bm.free()


def shade_smooth_by_angle(obj: bpy.types.Object, angle_deg: float = 32.0) -> None:
    """Lissage par angle, sans dependre d'un operateur ni d'un modificateur.

    On marque `sharp` toute arete dont l'angle depasse le seuil et on passe
    toutes les faces en lisse : Blender (et donc l'exporteur glTF) en deduit
    les normales scindees. Resultat identique a "Shade Auto Smooth", mais
    purement declaratif, donc rejouable a l'identique.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    limit = math.radians(angle_deg)
    for face in bm.faces:
        face.smooth = True
    for edge in bm.edges:
        if len(edge.link_faces) != 2:
            edge.smooth = False
        else:
            edge.smooth = edge.calc_face_angle(math.pi) <= limit
    bm.to_mesh(obj.data)
    bm.free()


def cleanup(obj: bpy.types.Object, merge_dist: float = 1e-5) -> None:
    """Soude les sommets doubles et recalcule les normales."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=merge_dist)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()


def join_objects(objects: list[bpy.types.Object], name: str) -> bpy.types.Object:
    """Fusionne plusieurs objets en un seul (les slots restent alignes)."""
    if not objects:
        raise ContractError("join_objects : aucun objet")
    target = objects[0]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = target
    if len(objects) > 1:
        bpy.ops.object.join()
    target.name = name
    target.data.name = name
    return target


# --------------------------------------------------------------------------
# Points d'attache
# --------------------------------------------------------------------------


def attach_point(
    name: str, location: tuple[float, float, float]
) -> bpy.types.Object:
    """Cree un point d'attache (Empty -> `Node3D` cote Godot).

    `location` est exprime dans le **repere d'auteur** (nez -Y, dessus +Z) ;
    `export_hull()` le transporte dans le repere Godot.
    """
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.08
    empty.location = Vector(location)
    bpy.context.scene.collection.objects.link(empty)
    return empty


def attach_pair(
    base_name: str, x: float, y: float, z: float
) -> tuple[bpy.types.Object, bpy.types.Object]:
    """Cree la paire `<base>_L` (babord) et `<base>_R` (tribord).

    `x` doit etre la distance **positive** a l'axe : le signe est pose ici, une
    fois pour toutes, ce qui evite d'inverser babord et tribord (voir le piege
    documente en tete de module).
    """
    d = abs(x)
    return (
        attach_point(f"{base_name}_L", (PORT * d, y, z)),
        attach_point(f"{base_name}_R", (STARBOARD * d, y, z)),
    )


# --------------------------------------------------------------------------
# Contrat et export
# --------------------------------------------------------------------------


@dataclass
class HullContract:
    """Contrat ADR-0008 d'une coque, exprime dans le repere **Godot**.

    `width_x` / `length_z` sont les dimensions imposees par le tableau de
    l'ADR-0008 ; `max_height_y` borne l'epaisseur (lisibilite en vue de dessus).
    """

    name: str
    width_x: float
    length_z: float
    max_height_y: float
    tri_budget: int
    required_materials: tuple[str, ...] = MATERIAL_ORDER
    required_attach_points: tuple[str, ...] = ()
    tolerance: float = 0.03
    #: Tolerance de centrage du pivot, en metres.
    pivot_tolerance: float = 0.02


@dataclass
class HullReport:
    """Mesures reelles relevees sur le `.glb` livre."""

    name: str
    filepath: str
    triangles: int
    vertices: int
    size: tuple[float, float, float] = (0.0, 0.0, 0.0)
    center: tuple[float, float, float] = (0.0, 0.0, 0.0)
    materials: dict[str, int] = field(default_factory=dict)
    attach_points: dict[str, tuple[float, float, float]] = field(default_factory=dict)
    file_bytes: int = 0

    def render(self) -> str:
        lines = [
            f"contrat OK — {self.name}",
            f"  fichier    : {self.filepath} ({self.file_bytes} o)",
            f"  triangles  : {self.triangles}",
            f"  sommets    : {self.vertices}",
            "  bbox (Godot X,Y,Z) : "
            f"{self.size[0]:.4f} x {self.size[1]:.4f} x {self.size[2]:.4f} m",
            "  centre     : "
            f"({self.center[0]:+.4f}, {self.center[1]:+.4f}, {self.center[2]:+.4f})",
            "  materiaux  : "
            + ", ".join(f"{k}={v}t" for k, v in sorted(self.materials.items())),
        ]
        for key in sorted(self.attach_points):
            x, y, z = self.attach_points[key]
            lines.append(f"  attache    : {key:<12} ({x:+.4f}, {y:+.4f}, {z:+.4f})")
        return "\n".join(lines)


def _read_glb(path: str) -> tuple[dict, bytes]:
    """Relit le `.glb` produit : on valide le livrable, pas nos intentions."""
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:4] != b"glTF":
        raise ContractError(f"{path} : ce n'est pas un glTF binaire")
    gltf: dict | None = None
    buffer = b""
    offset = 12
    while offset < len(data):
        length, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + length]
        offset += length
        if kind == 0x4E4F534A:
            gltf = json.loads(chunk)
        elif kind == 0x004E4942:
            buffer = chunk
    if gltf is None:
        raise ContractError(f"{path} : chunk JSON absent")
    return gltf, buffer


def _primitive_triangles(gltf: dict, prim: dict) -> int:
    if "indices" in prim:
        return gltf["accessors"][prim["indices"]]["count"] // 3
    return gltf["accessors"][prim["attributes"]["POSITION"]]["count"] // 3


def export_hull(
    hull: bpy.types.Object,
    attach_points: list[bpy.types.Object],
    filepath: str,
    contract: HullContract,
) -> HullReport:
    """Exporte la coque en `.glb`, puis **valide le fichier produit**.

    Etapes :
      1. correction d'axe (repere d'auteur -> repere Godot), cf. en-tete ;
      2. export glTF binaire (yup, modificateurs appliques) ;
      3. relecture du `.glb` et verification du contrat ADR-0008 :
         orientation, bounding box (+/- `tolerance`), centrage du pivot,
         budget de triangles, presence des materiaux et des points d'attache.

    Leve `ContractError` au moindre ecart : jamais d'export silencieux hors
    contrat.
    """
    objects = [hull, *attach_points]

    # Garde-fou analytique : la chaine d'axes est-elle encore la bonne ?
    _assert_axis_chain()

    # Temoins ASYMETRIQUES pris dans le repere d'auteur. La bounding box, elle,
    # est symetrique : elle ne peut pas distinguer une coque retournee. Les
    # points d'attache, si (une bouche de tir est a l'avant, une tuyere a
    # l'arriere). On note leur position d'auteur, on la reverifie sur le .glb.
    author_attach = {e.name: Vector(e.location) for e in attach_points}
    ys = [v.co.y for v in hull.data.vertices]
    author_y = (min(ys), max(ys))

    # 1. correction d'axe, cuite dans les donnees (les noeuds glTF restent
    #    a l'identite : aucune transformation cachee cote Godot).
    hull.data.transform(_AXIS_FIX)
    hull.data.update()
    for empty in attach_points:
        empty.location = _AXIS_FIX @ empty.location

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = hull

    # On exporte d'abord hors de l'arbre d'assets, on valide, et on ne publie
    # qu'ensuite. Sans ce detour, un .glb hors contrat resterait sur le disque
    # apres un echec — et Godot l'importerait sans rien dire.
    staging = tempfile.mkdtemp(prefix="aegis-hull-")
    staged = os.path.join(staging, os.path.basename(filepath))
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
            export_tangents=False,
            export_normals=True,
            export_texcoords=False,
        )
        report = _validate_glb(staged, contract, author_y, author_attach)
        shutil.move(staged, filepath)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    print(report.render())
    return report


def _validate_glb(
    filepath: str,
    contract: HullContract,
    author_y: tuple[float, float] | None = None,
    author_attach: dict[str, Vector] | None = None,
) -> HullReport:
    gltf, buffer = _read_glb(filepath)
    problems: list[str] = []

    # --- geometrie -------------------------------------------------------
    mats = [m.get("name", f"#{i}") for i, m in enumerate(gltf.get("materials", []))]
    tris_by_mat: dict[str, int] = {}
    triangles = 0
    vertices = 0
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for mesh in gltf.get("meshes", []):
        for prim in mesh["primitives"]:
            ntri = _primitive_triangles(gltf, prim)
            triangles += ntri
            acc = gltf["accessors"][prim["attributes"]["POSITION"]]
            vertices += acc["count"]
            name = mats[prim["material"]] if "material" in prim else "<none>"
            tris_by_mat[name] = tris_by_mat.get(name, 0) + ntri
            for axis in range(3):
                lo[axis] = min(lo[axis], acc["min"][axis])
                hi[axis] = max(hi[axis], acc["max"][axis])

    if not math.isfinite(lo[0]):
        raise ContractError(f"{filepath} : aucune geometrie exportee")

    size = tuple(hi[a] - lo[a] for a in range(3))
    center = tuple((hi[a] + lo[a]) * 0.5 for a in range(3))

    # --- points d'attache ------------------------------------------------
    attach: dict[str, tuple[float, float, float]] = {}
    for node in gltf.get("nodes", []):
        if "mesh" in node:
            continue
        t = node.get("translation", [0.0, 0.0, 0.0])
        attach[node.get("name", "?")] = (t[0], t[1], t[2])

    report = HullReport(
        name=contract.name,
        filepath=filepath,
        triangles=triangles,
        vertices=vertices,
        size=size,  # type: ignore[arg-type]
        center=center,  # type: ignore[arg-type]
        materials=tris_by_mat,
        attach_points=attach,
        file_bytes=os.path.getsize(filepath),
    )

    # --- contrat : bounding box -----------------------------------------
    for axis, label, expected in (
        (0, "largeur X", contract.width_x),
        (2, "longueur Z", contract.length_z),
    ):
        drift = abs(size[axis] - expected) / expected
        if drift > contract.tolerance:
            problems.append(
                f"{label} = {size[axis]:.4f} m, attendu {expected:.4f} m "
                f"(+/-{contract.tolerance:.0%}) — ecart {drift:.2%}"
            )
    if size[1] > contract.max_height_y:
        problems.append(
            f"hauteur Y = {size[1]:.4f} m > plafond {contract.max_height_y:.4f} m"
        )

    # --- contrat : pivot centre -----------------------------------------
    for axis, label in ((0, "X"), (2, "Z")):
        if abs(center[axis]) > contract.pivot_tolerance:
            problems.append(
                f"pivot decentre en {label} : {center[axis]:+.4f} m "
                f"(tolerance +/-{contract.pivot_tolerance} m)"
            )

    # --- contrat : orientation ------------------------------------------
    # Invariant exact de la chaine d'axes : le Z du glTF doit reproduire le Y
    # du repere d'auteur (nez = min Y -> min Z = avant, vers le haut de
    # l'ecran). Une inversion de signe ici, et toute la flotte vole a
    # reculons sans qu'aucun autre controle ne s'en apercoive.
    if author_y is not None:
        for label, expected, got in (
            ("nez (min Z)", author_y[0], lo[2]),
            ("poupe (max Z)", author_y[1], hi[2]),
        ):
            if abs(expected - got) > 1e-3:
                problems.append(
                    f"orientation rompue : {label} = {got:+.4f} en glTF, "
                    f"attendu {expected:+.4f} (Y d'auteur)."
                )

    # Temoin asymetrique : chaque point d'attache doit se retrouver exactement
    # ou la chaine d'axes le predit, (x, y, z) -> (-x, z, y). Une coque
    # retournee passe le test de bounding box (symetrique) mais echoue ici,
    # parce qu'une bouche de tir est a l'avant et une tuyere a l'arriere.
    if author_attach:
        for name, src in author_attach.items():
            expected = (-src.x, src.z, src.y)
            got = attach.get(name)
            if got is None:
                continue
            if max(abs(expected[i] - got[i]) for i in range(3)) > 1e-4:
                problems.append(
                    f"orientation rompue sur {name} : glTF "
                    f"({got[0]:+.4f}, {got[1]:+.4f}, {got[2]:+.4f}), attendu "
                    f"({expected[0]:+.4f}, {expected[1]:+.4f}, {expected[2]:+.4f}). "
                    "La coque pointe a l'envers ou babord/tribord sont inverses."
                )
    elif contract.required_attach_points:
        problems.append("aucun point d'attache : orientation non verifiable")

    # --- contrat : budget de triangles -----------------------------------
    if triangles > contract.tri_budget:
        problems.append(
            f"{triangles} triangles > budget {contract.tri_budget}"
        )

    # --- contrat : materiaux ---------------------------------------------
    for name in contract.required_materials:
        if tris_by_mat.get(name, 0) <= 0:
            problems.append(f"materiau requis absent ou non assigne : {name}")
    for name in tris_by_mat:
        if name not in MATERIAL_ORDER:
            problems.append(f"materiau hors nomenclature ADR-0008 : {name}")

    # --- contrat : points d'attache --------------------------------------
    for name in contract.required_attach_points:
        if name not in attach:
            problems.append(f"point d'attache requis absent : {name}")

    if problems:
        raise ContractError(
            f"CONTRAT ROMPU — {contract.name} ({filepath})\n"
            + "\n".join(f"  - {p}" for p in problems)
        )
    return report
