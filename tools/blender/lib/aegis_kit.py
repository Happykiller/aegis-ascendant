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
import time as _time
from dataclasses import dataclass, field

import bmesh
import bpy
from mathutils import Matrix, Vector

VERSION = "1.3.0"   # 1.3.0 : depliage en ATLAS (ilots disjoints, packes, recouvrement mesure) — ADR-0046/0047
#                    1.2.0 : tubes, verins, profil d'aile, UV cylindriques/par materiau, lecture .glb (BRIEF-0098)

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
    axis: str = "Y",
) -> list[list[bmesh.types.BMFace]]:
    """Solide de revolution autour de X, Y ou Z.

    `contour` : liste ordonnee de `(position_sur_l_axe, radius, material)`.
    Le `material` d'un point s'applique au segment qui part de ce point vers le
    suivant (celui du dernier point est ignore). Un point de rayon 0 est un
    pole : il est ferme par un eventail.

    `center_x` / `center_z` decalent le solide dans les DEUX directions
    perpendiculaires a l'axe, dans l'ordre des axes restants :
      axis="Y" -> (X, Z)   axis="X" -> (Y, Z)   axis="Z" -> (X, Y)

    Sert aux tuyeres, aux canons, aux futs de tourelle, aux noyaux : c'est la
    primitive ronde commune a toutes les coques.

    Le parametre `axis` a ete ajoute apres coup : le kit ne tournait qu'autour
    de Y, et TROIS scripts avaient fini par reimplementer la rotation localement
    (`_z_drum` et `_x_tube` dans la citadelle, `_disc_stack` dans le Needle
    Scout puis dans le Crescent). La suggestion figurait dans deux rapports de
    forge avant d'etre faite.
    """
    if segments < 3:
        raise ContractError("add_lathe : segments >= 3")
    if axis not in ("X", "Y", "Z"):
        raise ContractError("add_lathe : axis doit valoir 'X', 'Y' ou 'Z' (recu %r)" % axis)

    def _point(along: float, u: float, v: float) -> tuple[float, float, float]:
        if axis == "Y":
            return (u, along, v)
        if axis == "X":
            return (along, u, v)
        return (u, v, along)

    rings: list[list[bmesh.types.BMVert] | bmesh.types.BMVert] = []
    for along, radius, _ in contour:
        if radius <= 1e-6:
            rings.append(bm.verts.new(_point(along, center_x, center_z)))
            continue
        pts = []
        for s in range(segments):
            a = 2.0 * math.pi * s / segments
            pts.append(
                _point(
                    along,
                    center_x + radius * math.cos(a),
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


def _edge_disjoint_lots(
    faces: list[bmesh.types.BMFace],
) -> list[list[bmesh.types.BMFace]]:
    """Decoupe une liste de faces en LOTS SANS ARETE COMMUNE, dans l'ordre recu.

    Glouton et deterministe : on parcourt les faces dans l'ordre donne, on
    garde celles dont aucune arete n'est deja prise par le lot en cours, on
    renvoie les autres au tour suivant. Une grille reguliere se resout en deux
    lots (un damier), un anneau de N faces en deux lots (trois si N est impair).

    Propriete voulue : une liste DEJA sans arete commune rend UN seul lot, egal
    a la liste d'entree, dans le meme ordre. C'est ce qui garantit qu'un appel
    `per_face=True` sur des faces disjointes produit exactement la meme
    geometrie, dans le meme ordre de creation, donc le meme `.glb` a l'octet
    pres, que l'appel de region equivalent.
    """
    pending = list(faces)
    lots: list[list[bmesh.types.BMFace]] = []
    while pending:
        lot: list[bmesh.types.BMFace] = []
        taken: set = set()
        rest: list[bmesh.types.BMFace] = []
        for face in pending:
            edges = set(face.edges)
            if edges & taken:
                rest.append(face)
            else:
                lot.append(face)
                taken |= edges
        lots.append(lot)
        pending = rest
    return lots


def inset_panel(
    bm: bmesh.types.BMesh,
    faces: list[bmesh.types.BMFace],
    material: str,
    thickness: float = 0.012,
    depth: float = -0.008,
    per_face: bool = False,
) -> list[bmesh.types.BMFace]:
    """Decoupe/enfonce un panneau : `inset_region` puis materiau sur le fond.

    C'est le detail par la geometrie exige par l'ADR-0008 : le bord du panneau
    reste en `AA_Hull`, le fond enfonce prend `material`. `depth < 0` creuse.

    *** DEUX PIEGES, tous deux TOTALEMENT SILENCIEUX (BRIEF-0084) ***

    1. **La normale de face vaut (0,0,0) sur un maillage frais.** Une face creee
       par `bm.faces.new()` — donc TOUTE face sortie de `add_box`, `bridge_rings`,
       `cap_ring`, `add_lathe`… — n'a pas de normale tant que personne ne l'a
       calculee. `inset_region` lit cette normale : elle est nulle, l'inset se
       replie sur lui-meme et rend un lisere d'aire NULLE ; `cleanup()` ressoude
       ensuite les sommets confondus et il ne reste **que le changement de
       materiau** — un panneau qui se voit et qui n'existe pas. Mesure de
       reproduction sur 16 quads de 1 m (thickness 0,10 / depth -0,05) : lisere
       0,000000 m2 et 64 -> 32 triangles apres `cleanup()`, contre 1,744132 m2
       et 64 -> 64 une fois les normales calculees ; creux mesure 0,000 m contre
       -0,050 m.

       Le kit appelle donc `bm.normal_update()` LUI-MEME, juste avant
       l'operateur. C'est idempotent : un script qui l'appelle deja de son cote
       obtient exactement la meme geometrie qu'avant (verifie a l'octet sur
       `core_interior.glb` et `leech_drone.glb`, inchanges).

       ⚠️ La mise a jour doit etre GLOBALE, pas ciblee sur les faces passees.
       Tentee en `BMFace.normal_update()` face par face — moins cher, sans effet
       de bord sur le reste du maillage — elle rend un panneau FAUX des que la
       region compte plus d'une face : `inset_region` deplace les sommets
       INTERIEURS de la region le long de leur normale de SOMMET, que seul
       `bm.normal_update()` calcule. Mesure sur la grille de 16 quads : les 9
       sommets interieurs restent a z = 0,000 au lieu de descendre a -0,050, et
       le fond du panneau se voile au lieu d'etre plat. Le defaut est, lui
       aussi, parfaitement silencieux (meme topologie, meme compte de
       triangles).

       ⚠️ Corollaire a connaitre : l'inset creuse le long de la normale, donc
       dans le sens du winding de la face. Une boucle capee a l'envers se
       SOULEVE au lieu de se creuser (cf. `build_aegis_citadel.py:1179`). Tant
       que les normales etaient nulles ce defaut passait inapercu — il ne
       passera plus.

    2. **`inset_region` inset une REGION, pas des faces.** N faces qui partagent
       des aretes ne rendent qu'UN lisere, autour de leur union. Mesure : 16
       quads contigus rendent 16 faces de lisere (le pourtour de la grille) et
       1,744132 m2, la ou une plaque par face en rend 64 et 6,439875 m2, soit
       **3,7 x plus de lisere** et 160 triangles au lieu de 64.

       Ce n'est PAS toujours un defaut, et c'est pour cela que le comportement
       n'a pas ete change d'office : la quasi-totalite des appels du depot
       veulent exactement une region — une plaque de carapace de 20 cellules
       (`build_choir_harvester.py:674`), un petale de trois plaques
       (`build_null_maw.py:500`), un sillon dorsal continu ou un puits de
       verriere (`build_specter_9.py:1283`), une plaque de 1 a 3 bandes
       (`build_aegis_citadel.py:474`). Les rendre face par face ne corrigerait
       rien : cela transformerait chaque plaque en damier de tuiles.

       Quand on veut UNE PLAQUE PAR FACE, c'est `per_face=True` (ou son alias
       lisible `inset_panels()`) : la liste est alors decoupee en lots sans
       arete commune et l'operateur est appele une fois par lot. C'est le cas
       de `build_core_interior.py`, dont les 240 plaques de pont ne donnaient
       qu'un lisere autour de l'arene entiere.

    Retourne les faces de bordure (le lisere), a colorer par `set_material()`.
    """
    faces = [f for f in faces if f is not None and f.is_valid]
    if not faces:
        return []
    idx = mat_index(material)
    rims: list[bmesh.types.BMFace] = []
    lots = _edge_disjoint_lots(faces) if per_face else [faces]
    for lot in lots:
        lot = [f for f in lot if f.is_valid]
        if not lot:
            continue
        # Piege 1 : sans cela l'operateur lit des normales nulles et ne creuse
        # rien. Global et non cible : le fond du panneau descend le long des
        # normales de SOMMET (voir le docstring).
        bm.normal_update()
        res = bmesh.ops.inset_region(
            bm,
            faces=lot,
            use_boundary=True,
            use_even_offset=True,
            thickness=thickness,
            depth=depth,
        )
        # inset_region retourne les faces de *bordure* ; les faces d'origine
        # (passees en entree) restent le fond du panneau.
        for face in lot:
            if face.is_valid:
                face.material_index = idx
        rims += res["faces"]
    return rims


def inset_panels(
    bm: bmesh.types.BMesh,
    faces: list[bmesh.types.BMFace],
    material: str,
    thickness: float = 0.012,
    depth: float = -0.008,
) -> list[bmesh.types.BMFace]:
    """UNE PLAQUE PAR FACE — alias lisible de `inset_panel(..., per_face=True)`.

    Le pluriel est la pour qu'on ait a CHOISIR : `inset_panel` (une region, un
    lisere) et `inset_panels` (une plaque par face) sont deux gestes differents
    et le mauvais des deux est silencieux (voir le piege 2 de `inset_panel`).
    """
    return inset_panel(bm, faces, material, thickness, depth, per_face=True)


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


def triangulate(obj: bpy.types.Object) -> int:
    """Triangule TOUTES les faces, et rend le nombre de faces decoupees.

    ⚠️ A APPELER AVANT TOUT DEPLIAGE — `box_project_uv()` le fait desormais
    lui-meme, cette fonction est publique pour les scripts qui veulent trianguler
    plus tot (avant une mesure, avant un harnais d'orientation).

    POURQUOI CE N'EST PAS UNE OPTIMISATION MAIS UNE CORRECTION. Une projection en
    boite choisit son plan PAR FACE, d'apres la normale de la face. Un quad
    GAUCHE (ses quatre sommets ne sont pas coplanaires) n'a pas de normale :
    Blender lui en donne une moyenne, qui n'est celle d'aucun des deux triangles
    que l'exporteur en tirera. Les deux triangles heritent donc d'une projection
    calculee pour un plan qui n'est pas le leur, et l'un des deux peut se
    retrouver projete selon un axe qui n'est PAS son axe dominant. Son etirement
    depasse alors la borne sqrt(3) de la methode — mesure sur `bay_kit` avant
    correction : densite minimale 0,078 tuile/m pour une borne theorique de
    0,116, soit 2,6 fois trop.

    ⚠️ ET LE DEFAUT EST TOTALEMENT SILENCIEUX : le `.glb` est valide, les UV sont
    presentes et comptees, aucun test ne rougit. Il ne se voit qu'a la texture
    generee, c'est-a-dire trop tard.

    Accessoirement, l'exporteur renonce aux TANGENTES sur les faces de plus de
    quatre sommets (« tangent space can only be computed for tris/quads ») : sans
    triangulation, ADR-0011 est inoperant sur ces faces-la.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    targets = [f for f in bm.faces if len(f.verts) > 3]
    if targets:
        bmesh.ops.triangulate(bm, faces=targets)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return len(targets)


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


@dataclass
class MovingPart:
    """Piece EXPORTEE A PART, destinee a etre animee cote Godot.

    Pourquoi cette primitive existe : `export_hull()` n'exportait qu'UN objet
    maille, si bien qu'aucun sous-ensemble d'une coque ne pouvait bouger. La
    limite a mordu deux fois — mantelet de tourelle et anneau de balise
    (BRIEF-0032-report §9), puis volets et tuyeres du Specter-9. Le repli
    (un `.glb` separe par piece) marche mais impose un fichier, une scene et une
    ligne de provenance pour trois centimetres de geometrie.

    ⚠️ `pivot` est le point d'ARTICULATION, dans le repere d'auteur. C'est LA
    donnee qui compte : la piece est batie en coordonnees absolues comme le reste
    de la coque, puis son origine est ramenee sur ce point. Une piece dont
    l'origine reste a zero decrira un arc de cercle autour du nez du vaisseau au
    lieu de pivoter sur sa charniere — et le defaut ne se voit qu'une fois animee.

    `parent` : nom d'une AUTRE piece mobile dont celle-ci devient l'enfant. Sert aux
    articulations en chaine — un volet porte par une aile a fleche variable doit
    suivre l'aile, sinon il reste en l'air des que celle-ci bouge. Le pivot de
    l'enfant reste exprime dans le repere d'auteur : `export_hull()` le rend relatif
    au parent, ce qui evite de calculer une difference a la main dans chaque script.
    """

    obj: bpy.types.Object
    pivot: tuple[float, float, float]
    parent: str | None = None


def moving_part(
    name: str,
    bm: bmesh.types.BMesh,
    pivot: tuple[float, float, float],
    parent: str | None = None,
) -> MovingPart:
    """Cree une piece mobile depuis un bmesh bati en coordonnees ABSOLUES."""
    return MovingPart(new_object(name, bm), pivot, parent)


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


def box_project_uv(obj: bpy.types.Object, texels_per_meter: float = 1.0) -> None:
    """Deplie les UV par PROJECTION EN BOITE, sur place.

    Chaque face est projetee sur celui des trois plans du monde dont sa normale
    est la plus proche, a l'echelle donnee. C'est un depliage grossier — les
    ilots se recouvrent, les faces obliques sont legerement etirees — et c'est
    exactement ce qu'il faut ici : les feuilles de detail sont REPETABLES et en
    niveaux de gris (ADR-0011), donc leur position exacte sur la coque n'a aucune
    importance. Seules comptent l'echelle et la continuite.

    Pourquoi pas `bpy.ops.uv.smart_project()` : il faut passer en mode edition,
    il depend de la selection, et son resultat bouge d'une version de Blender a
    l'autre. Ici tout est calcule a la main, donc DETERMINISTE — exigence
    ADR-0008, verifiee par la byte-identite de deux exports successifs.

    `texels_per_meter` : combien de fois la feuille se repete par metre. Une
    valeur trop haute transforme le detail mecanique en bruit ; trop basse, les
    plaques deviennent enormes. A juger au rendu, pas au chiffre.

    ⚠️ TRIANGULE D'ABORD, ET CE N'EST PAS UNE COMMODITE (BRIEF-0092). Sur un quad
    gauche, la projection est calculee pour une normale moyenne qui n'est celle
    d'aucun des deux triangles exportes : l'un des deux peut sortir projete selon
    un axe qui n'est pas le sien, avec un etirement SOUS la borne sqrt(3) de la
    methode. Le detail, la mesure et la raison sont dans `triangulate()`.
    """
    triangulate(obj)
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        n = face.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for loop in face.loops:
            co = loop.vert.co
            if ax >= ay and ax >= az:
                u, v = co.y, co.z
            elif ay >= az:
                u, v = co.x, co.z
            else:
                u, v = co.x, co.y
            loop[uv_layer].uv = (u * texels_per_meter, v * texels_per_meter)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def export_hull(
    hull: bpy.types.Object,
    attach_points: list[bpy.types.Object],
    filepath: str,
    contract: HullContract,
    parts: list[MovingPart] | None = None,
) -> HullReport:
    """Exporte la coque en `.glb`, puis **valide le fichier produit**.

    Etapes :
      1. correction d'axe (repere d'auteur -> repere Godot), cf. en-tete ;
      2. export glTF binaire (yup, modificateurs appliques) ;
      3. relecture du `.glb` et verification du contrat ADR-0008 :
         orientation, bounding box (+/- `tolerance`), centrage du pivot,
         budget de triangles, presence des materiaux et des points d'attache.

    `parts` : pieces mobiles exportees en noeuds glTF SEPARES, chacune avec son
    origine sur son point d'articulation (voir `MovingPart`). Elles comptent dans
    le budget de triangles et dans la bounding box — ce sont des morceaux de la
    coque, pas des accessoires. Parametre optionnel : les scripts qui l'ignorent
    se comportent exactement comme avant.

    Leve `ContractError` au moindre ecart : jamais d'export silencieux hors
    contrat.
    """
    parts = parts or []
    _assert_unique_names(hull, parts, attach_points)
    objects = [hull, *[p.obj for p in parts], *attach_points]

    # Garde-fou analytique : la chaine d'axes est-elle encore la bonne ?
    _assert_axis_chain()

    # Temoins ASYMETRIQUES pris dans le repere d'auteur. La bounding box, elle,
    # est symetrique : elle ne peut pas distinguer une coque retournee. Les
    # points d'attache, si (une bouche de tir est a l'avant, une tuyere a
    # l'arriere). On note leur position d'auteur, on la reverifie sur le .glb.
    author_attach = {e.name: Vector(e.location) for e in attach_points}
    ys = [v.co.y for v in hull.data.vertices]
    for part in parts:
        ys += [v.co.y for v in part.obj.data.vertices]
    author_y = (min(ys), max(ys))

    # 1. correction d'axe, cuite dans les donnees (les noeuds glTF restent
    #    a l'identite : aucune transformation cachee cote Godot).
    hull.data.transform(_AXIS_FIX)
    hull.data.update()
    by_name = {p.obj.name: p for p in parts}
    for part in parts:
        # L'ordre compte : on ramene D'ABORD l'origine sur la charniere dans le
        # repere d'auteur, ensuite seulement on tourne. L'inverse ferait pivoter
        # un decalage deja pose et la piece atterrirait ailleurs.
        pivot = Vector(part.pivot)
        part.obj.data.transform(Matrix.Translation(-pivot))
        part.obj.data.transform(_AXIS_FIX)
        part.obj.data.update()
        part.obj.location = _AXIS_FIX @ pivot
        if part.parent is not None:
            owner = by_name.get(part.parent)
            if owner is None:
                raise ContractError(
                    f"piece '{part.obj.name}' : parent '{part.parent}' introuvable"
                )
            # Le parentage de Blender applique l'inverse de la matrice du parent :
            # sans `matrix_parent_inverse` a l'identite, l'enfant serait deplace deux
            # fois. On pose donc la position RELATIVE a la main, ce qui donne aussi
            # exactement ce que Godot lira dans le noeud glTF.
            part.obj.parent = owner.obj
            part.obj.matrix_parent_inverse = Matrix.Identity(4)
            part.obj.location = (_AXIS_FIX @ pivot) - (_AXIS_FIX @ Vector(owner.pivot))
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
            # UV et tangentes exportees depuis ADR-0011 : les feuilles de detail
            # repetables (lignes de panneau, greebles, usure) sont appliquees
            # cote Godot et n'ont aucun support sans coordonnees de texture.
            # Elles etaient explicitement supprimees jusqu'ici — c'etait LE
            # verrou qui rendait toute texture impossible.
            export_tangents=True,
            export_normals=True,
            export_texcoords=True,
        )
        report = _validate_glb(staged, contract, author_y, author_attach)
        shutil.move(staged, filepath)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    print(report.render())
    return report


def _assert_unique_names(
    hull: bpy.types.Object,
    parts: list[MovingPart],
    attach_points: list[bpy.types.Object],
) -> None:
    """Un nom en double cote Blender devient un `Node3D` renomme cote Godot.

    Godot suffixe silencieusement les doublons (`Flap`, `Flap2`...), et le code
    qui adresse la piece par son nom ne trouve alors plus rien — sans la moindre
    erreur au chargement. On refuse ici plutot que de le decouvrir en jeu.
    """
    names = [hull.name] + [p.obj.name for p in parts] + [e.name for e in attach_points]
    seen: set[str] = set()
    dupes = sorted({n for n in names if n in seen or seen.add(n)})
    if dupes:
        raise ContractError(f"noms en double a l'export : {', '.join(dupes)}")


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
    # On parcourt les NŒUDS et non les maillages : une piece mobile a son origine
    # sur sa charniere, donc ses sommets sont en coordonnees LOCALES et sa position
    # reelle vit dans la translation du nœud. Ignorer celle-ci — ce que faisait la
    # version maillage — sortait la piece de la bounding box : un volet pouvait
    # depasser de 40 cm sans que le contrat s'en apercoive.
    # Position MONDE de chaque nœud : on descend le graphe en cumulant les
    # translations. Une piece enfant (volet porte par une aile) est positionnee
    # RELATIVEMENT a son parent — ne lire que sa propre translation la placerait a
    # 45 cm du nez au lieu de 1,25 m, et elle sortirait du controle de dimensions.
    world: dict[int, list[float]] = {}

    def _walk(index: int, base: list[float]) -> None:
        node = gltf["nodes"][index]
        t = node.get("translation", [0.0, 0.0, 0.0])
        here = [base[a] + t[a] for a in range(3)]
        world[index] = here
        for child in node.get("children", []):
            _walk(child, here)

    roots = gltf.get("scenes", [{}])[0].get("nodes", list(range(len(gltf.get("nodes", [])))))
    for root in roots:
        _walk(root, [0.0, 0.0, 0.0])

    for index, node in enumerate(gltf.get("nodes", [])):
        if "mesh" not in node:
            continue
        offset = world.get(index, node.get("translation", [0.0, 0.0, 0.0]))
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            ntri = _primitive_triangles(gltf, prim)
            triangles += ntri
            acc = gltf["accessors"][prim["attributes"]["POSITION"]]
            vertices += acc["count"]
            name = mats[prim["material"]] if "material" in prim else "<none>"
            tris_by_mat[name] = tris_by_mat.get(name, 0) + ntri
            for axis in range(3):
                lo[axis] = min(lo[axis], acc["min"][axis] + offset[axis])
                hi[axis] = max(hi[axis], acc["max"][axis] + offset[axis])

    if not math.isfinite(lo[0]):
        raise ContractError(f"{filepath} : aucune geometrie exportee")

    size = tuple(hi[a] - lo[a] for a in range(3))
    center = tuple((hi[a] + lo[a]) * 0.5 for a in range(3))

    # --- points d'attache ------------------------------------------------
    attach: dict[str, tuple[float, float, float]] = {}
    for index, node in enumerate(gltf.get("nodes", [])):
        if "mesh" in node:
            continue
        t = world.get(index, node.get("translation", [0.0, 0.0, 0.0]))
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


# --------------------------------------------------------------------------
# Ajouts 1.2.0 — BRIEF-0098 (Specter-9 Talvern). NOUVELLES fonctions seulement :
# quinze scripts dependent des precedentes, aucune n'est modifiee.
# --------------------------------------------------------------------------


def _orthonormal_frame(axis: Vector) -> tuple[Vector, Vector, Vector]:
    """Base (u, v, w) orthonormee dont `w` est `axis` normalise. Deterministe."""
    w = Vector(axis).normalized()
    helper = Vector((0.0, 0.0, 1.0)) if abs(w.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    u = helper.cross(w).normalized()
    v = w.cross(u)
    return u, v, w


def add_tube(
    bm: bmesh.types.BMesh,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
    segments: int,
    material: str,
    radius_end: float | None = None,
) -> list[bmesh.types.BMFace]:
    """Cylindre (ou tronc de cone) ferme entre deux points QUELCONQUES.

    `add_lathe` ne tourne qu'autour d'un axe du monde ; un verin d'aerofrein
    couche en diagonale dans sa baie, un axe de charniere incline, un montant de
    verriere n'en ont aucun. Retourne toutes les faces creees.
    """
    if segments < 3:
        raise ContractError("add_tube : segments >= 3")
    p0, p1 = Vector(start), Vector(end)
    axis = p1 - p0
    if axis.length < 1e-9:
        raise ContractError("add_tube : start et end confondus")
    u, v, _ = _orthonormal_frame(axis)
    r1 = radius if radius_end is None else radius_end
    idx = mat_index(material)
    ring0, ring1 = [], []
    for s in range(segments):
        a = 2.0 * math.pi * s / segments
        d = u * math.cos(a) + v * math.sin(a)
        ring0.append(bm.verts.new(p0 + d * radius))
        ring1.append(bm.verts.new(p1 + d * r1))
    faces = [f for f in bridge_rings(bm, ring0, ring1, material) if f is not None]
    for ring, flip in ((ring0, True), (ring1, False)):
        cap = cap_ring(bm, list(reversed(ring)) if flip else ring, material)
        if cap is not None:
            faces.append(cap)
    for face in faces:
        face.material_index = idx
    return faces


def add_actuator(
    bm: bmesh.types.BMesh,
    anchor: tuple[float, float, float],
    tip: tuple[float, float, float],
    barrel_radius: float,
    rod_radius: float,
    barrel_fraction: float = 0.6,
    segments: int = 10,
    barrel_material: str = "AA_Greeble",
    rod_material: str = "AA_Trim",
) -> list[bmesh.types.BMFace]:
    """Verin : deux cylindres emboites, le fut depuis `anchor`, la tige jusqu'a `tip`.

    `barrel_fraction` : part de la course occupee par le fut. La tige part du
    fond du fut (elle est donc DANS le fut sur toute sa longueur, comme une vraie
    tige), ce qui evite un raccord visible a la sortie. Deux embases plus larges
    aux deux bouts font les chapes.
    """
    a, t = Vector(anchor), Vector(tip)
    axis = t - a
    length = axis.length
    if length < 1e-9:
        raise ContractError("add_actuator : anchor et tip confondus")
    d = axis / length
    faces = add_tube(bm, a, a + d * (length * barrel_fraction), barrel_radius,
                     segments, barrel_material)
    faces += add_tube(bm, a + d * (length * 0.12), t, rod_radius, segments,
                      rod_material)
    knuckle = barrel_radius * 1.25
    faces += add_tube(bm, a - d * knuckle * 0.6, a + d * knuckle * 0.6, knuckle,
                      segments, barrel_material)
    faces += add_tube(bm, t - d * knuckle * 0.6, t + d * knuckle * 0.6,
                      rod_radius * 1.6, segments, barrel_material)
    return faces


def airfoil_half_thickness(
    t: float, max_half_thickness: float, peak: float = 0.32, floor: float = 0.0042
) -> float:
    """Demi-epaisseur d'un profil de voilure a la fraction de corde `t`.

    Bord d'attaque ROND (montee en racine carree jusqu'au maitre-couple `peak`),
    bord de fuite FIN (decroissance presque lineaire) — c'est ce qui distingue une
    lame d'aile d'une lentille symetrique. `floor` borne l'epaisseur des bords :
    un bord d'epaisseur nulle degenere au chanfrein.
    """
    t = min(max(t, 0.0), 1.0)
    if t <= peak:
        shape = math.sqrt(t / peak) if peak > 1e-9 else 1.0
    else:
        shape = ((1.0 - t) / (1.0 - peak)) ** 0.85
    return max(max_half_thickness * shape, floor)


def box_project_uv_by_material(
    obj: bpy.types.Object,
    densities: dict[str, float],
    default_texels_per_meter: float,
) -> None:
    """Projection en boite, avec une densite PAR MATERIAU (ADR-0028, BRIEF-0098).

    Le brief demande « une zone, une feuille, une densite » — et de deplier chaque
    zone avant de joindre. Une coque jointe en un seul maillage se deplie donc ici
    face par face selon son slot de materiau : la peau a une densite, les fonds
    de baie (`AA_Greeble`) en ont une autre. Meme methode que `box_project_uv`
    (triangulation d'abord, plan par normale dominante), meme determinisme.
    """
    triangulate(obj)
    mesh = obj.data
    scale_by_index: dict[int, float] = {}
    for name, density in densities.items():
        scale_by_index[mat_index(name)] = density
    bm = bmesh.new()
    bm.from_mesh(mesh)
    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        density = scale_by_index.get(face.material_index, default_texels_per_meter)
        n = face.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for loop in face.loops:
            co = loop.vert.co
            if ax >= ay and ax >= az:
                u, v = co.y, co.z
            elif ay >= az:
                u, v = co.x, co.z
            else:
                u, v = co.x, co.y
            loop[uv_layer].uv = (u * density, v * density)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def cylinder_project_uv(
    obj: bpy.types.Object,
    center: tuple[float, float, float],
    axis: tuple[float, float, float],
    tiles_around: float,
    tiles_per_meter_along: float | None = None,
    reference_radius: float | None = None,
) -> None:
    """Depliage CYLINDRIQUE autour d'un axe (BRIEF-0098, TEX-0019).

    `u` fait le tour de l'axe (`tiles_around` tuiles par tour), `v` court le long
    de l'axe. Si `tiles_per_meter_along` n'est pas donne, il est deduit pour que
    la densite soit HOMOGENE au rayon `reference_radius` (defaut : rayon moyen des
    sommets) : `tiles_around / (2 pi R)`.

    Trois familles de faces, choisies par la normale de chaque face :

      * faces de PEAU (normale radiale) : (angle, position axiale) — le cylindre ;
      * faces de TRANCHE (normale tangentielle : flancs des petales, joues des
        anneaux) : (rayon, position axiale) — sans quoi leur `u` serait constant,
        leur UV d'aire nulle et leur tangente indefinie ;
      * faces de FOND (normale axiale : fond de chambre, culots) : plan polaire
        (x, y) locaux, a la meme densite.

    La couture du tour est traitee face par face : une face qui chevauche l'angle
    zero voit ses `u` bas remontes d'un tour, elle ne s'etire jamais sur toute la
    largeur de la feuille.
    """
    triangulate(obj)
    mesh = obj.data
    c = Vector(center)
    u_dir, v_dir, w_dir = _orthonormal_frame(Vector(axis))
    bm = bmesh.new()
    bm.from_mesh(mesh)
    uv_layer = bm.loops.layers.uv.verify()

    if reference_radius is None:
        radii = []
        for vert in bm.verts:
            rel = vert.co - c
            radii.append(math.hypot(rel.dot(u_dir), rel.dot(v_dir)))
        reference_radius = sum(radii) / max(len(radii), 1)
    if tiles_per_meter_along is None:
        tiles_per_meter_along = tiles_around / (2.0 * math.pi * max(reference_radius, 1e-6))
    dens = tiles_per_meter_along

    for face in bm.faces:
        n = face.normal
        centroid = face.calc_center_median() - c
        radial = centroid - w_dir * centroid.dot(w_dir)
        radial_len = radial.length
        radial_dir = radial / radial_len if radial_len > 1e-9 else u_dir
        tangent_dir = w_dir.cross(radial_dir)
        n_axial = abs(n.dot(w_dir))
        n_radial = abs(n.dot(radial_dir))
        n_tangent = abs(n.dot(tangent_dir))
        uvs = []
        for loop in face.loops:
            rel = loop.vert.co - c
            along = rel.dot(w_dir)
            px, py = rel.dot(u_dir), rel.dot(v_dir)
            if n_axial >= n_radial and n_axial >= n_tangent:
                uvs.append((px * dens, py * dens))
            elif n_tangent > n_radial:
                uvs.append((math.hypot(px, py) * dens, along * dens))
            else:
                angle = math.atan2(py, px)
                if angle < 0.0:
                    angle += 2.0 * math.pi
                uvs.append((angle / (2.0 * math.pi) * tiles_around, along * dens))
        if n_radial >= n_axial and n_radial >= n_tangent:
            us = [uv[0] for uv in uvs]
            if max(us) - min(us) > tiles_around * 0.5:
                uvs = [
                    (u + tiles_around if u < tiles_around * 0.5 else u, v)
                    for u, v in uvs
                ]
        for loop, uv in zip(face.loops, uvs):
            loop[uv_layer].uv = uv
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def texel_density(
    points: list, uvs: list, tris: list[tuple[int, int, int]]
) -> dict[str, float]:
    """Densite de texels par VALEURS SINGULIERES, triangle par triangle (BRIEF-0089).

    Une moyenne d'aires ne verrait aucun etirement : un triangle deux fois trop
    long dans un sens et deux fois trop court dans l'autre a la bonne aire. On
    mesure les deux valeurs singulieres de l'application plan-du-triangle -> UV :
    leur inverse donne les metres par tuile dans les deux directions principales,
    leur rapport l'anisotropie. Retourne un dict vide si rien n'est mesurable.
    """
    lo, hi, total, weight = math.inf, 0.0, 0.0, 0.0
    aniso = 1.0
    for ia, ib, ic in tris:
        pa, pb, pc = (Vector(points[i]) for i in (ia, ib, ic))
        ua, ub, uc = (Vector(uvs[i][:2]) for i in (ia, ib, ic))
        e1, e2 = pb - pa, pc - pa
        area = e1.cross(e2).length * 0.5
        if area < 1e-9:
            continue
        bx = e1.normalized()
        bz = e1.cross(e2).normalized()
        by = bz.cross(bx)
        a11, a21 = e1.dot(bx), e1.dot(by)
        a12, a22 = e2.dot(bx), e2.dot(by)
        det = a11 * a22 - a12 * a21
        if abs(det) < 1e-12:
            continue
        j11, j21 = ub.x - ua.x, ub.y - ua.y
        j12, j22 = uc.x - ua.x, uc.y - ua.y
        i11, i12 = a22 / det, -a12 / det
        i21, i22 = -a21 / det, a11 / det
        m11 = j11 * i11 + j12 * i21
        m12 = j11 * i12 + j12 * i22
        m21 = j21 * i11 + j22 * i21
        m22 = j21 * i12 + j22 * i22
        e = (m11 + m22) * 0.5
        f = (m11 - m22) * 0.5
        g = (m21 + m12) * 0.5
        h = (m21 - m12) * 0.5
        q = math.hypot(e, h)
        r = math.hypot(f, g)
        s1, s2 = q + r, abs(q - r)
        if s2 < 1e-9:
            continue
        lo = min(lo, s2)
        hi = max(hi, s1)
        aniso = max(aniso, s1 / s2)
        total += (s1 + s2) * 0.5 * area
        weight += area
    if weight == 0.0:
        return {}
    mean = total / weight
    return {
        "tiles_per_m_min": lo, "tiles_per_m_max": hi, "tiles_per_m_mean": mean,
        "m_per_tile_mean": 1.0 / mean, "anisotropy_max": aniso,
        "area": weight,
    }


_ACCESSOR_FMT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
_ACCESSOR_N = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def glb_accessor(gltf: dict, blob: bytes, index: int) -> list[tuple]:
    """Decode un accesseur du `.glb` (buffer unique, chunk BIN) en tuples."""
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    fmt = _ACCESSOR_FMT[acc["componentType"]]
    n = _ACCESSOR_N[acc["type"]]
    size = struct.calcsize(fmt)
    stride = view.get("byteStride", size * n)
    base = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    return [
        struct.unpack_from("<" + fmt * n, blob, base + i * stride)
        for i in range(acc["count"])
    ]


def glb_primitives(path: str) -> list[dict]:
    """Relit un `.glb` LIVRE et rend ses primitives, nœud par nœud, en espace MONDE.

    Chaque entree : `node`, `parent`, `translation` (locale), `world` (translation
    cumulee), `material`, `positions` (locales), `uvs` (ou None), `indices`.
    C'est la matiere premiere d'un audit : compter `TEXCOORD_0`, mesurer l'aire
    par materiau, la densite de texels, ou tourner une piece autour de son pivot
    pour lire le signe qui l'ouvre — sur le fichier, jamais sur la scene.
    """
    gltf, blob = _read_glb(path)
    nodes = gltf.get("nodes", [])
    parent_of: dict[int, int | None] = {i: None for i in range(len(nodes))}
    for i, node in enumerate(nodes):
        for child in node.get("children", []):
            parent_of[child] = i
    world: dict[int, tuple[float, float, float]] = {}

    def _world(i: int) -> tuple[float, float, float]:
        if i in world:
            return world[i]
        t = nodes[i].get("translation", [0.0, 0.0, 0.0])
        p = parent_of[i]
        base = _world(p) if p is not None else (0.0, 0.0, 0.0)
        world[i] = (base[0] + t[0], base[1] + t[1], base[2] + t[2])
        return world[i]

    mats = [m.get("name", f"#{k}") for k, m in enumerate(gltf.get("materials", []))]
    out: list[dict] = []
    for i, node in enumerate(nodes):
        if "mesh" not in node:
            continue
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            attrs = prim["attributes"]
            positions = glb_accessor(gltf, blob, attrs["POSITION"])
            uvs = glb_accessor(gltf, blob, attrs["TEXCOORD_0"]) if "TEXCOORD_0" in attrs else None
            if "indices" in prim:
                flat = [t[0] for t in glb_accessor(gltf, blob, prim["indices"])]
            else:
                flat = list(range(len(positions)))
            tris = [tuple(flat[k:k + 3]) for k in range(0, len(flat) - 2, 3)]
            out.append({
                "node": node.get("name", f"node{i}"),
                "parent": nodes[parent_of[i]].get("name") if parent_of[i] is not None else None,
                "translation": tuple(node.get("translation", [0.0, 0.0, 0.0])),
                "world": _world(i),
                "material": mats[prim["material"]] if "material" in prim else "<none>",
                "positions": positions,
                "uvs": uvs,
                "indices": tris,
            })
    return out


# ---------------------------------------------------------------------------
# Depliage en ATLAS (ADR-0046, ADR-0047) — pour les cartes PEINTES
# ---------------------------------------------------------------------------


@dataclass
class AtlasReport:
    """Ce qu'un depliage en atlas a produit. Mesure, jamais suppose."""

    loops: int = 0
    triangles: int = 0
    #: Fraction du carre UV reellement occupee. Ce qui n'est pas occupe est du
    #: texel paye et jamais lu — c'est le rendement du packing.
    fill: float = 0.0
    #: Texels couverts DEUX FOIS ou plus, sur la grille de sondage. Doit valoir 0 :
    #: un atlas peint dont deux faces partagent un texel est impeignable.
    overlap_texels: int = 0
    #: Boucles UV tombees hors du carre [0, 1]. Doit valoir 0.
    outside: int = 0
    probe: int = 0
    seconds: float = 0.0

    def render(self) -> str:
        return (
            "atlas : %d boucles, %d triangles, remplissage %.1f %%, "
            "recouvrement %d texels (sonde %d x %d), hors carre %d, %.1f s"
            % (self.loops, self.triangles, self.fill * 100.0, self.overlap_texels,
               self.probe, self.probe, self.outside, self.seconds)
        )


def atlas_unwrap(
    objects: bpy.types.Object | list[bpy.types.Object],
    *,
    angle_limit_deg: float = 66.0,
    margin: float = 0.0015,
    probe: int = 1024,
    min_fill: float = 0.30,
) -> AtlasReport:
    """Deplie en ATLAS : des ilots DISJOINTS, packes dans [0, 1], sur place.

    ⚠️ CE N'EST PAS `box_project_uv()`, ET LES DEUX NE SERVENT PAS LA MEME CHOSE.
    La projection en boite produit volontairement des ilots QUI SE RECOUVRENT :
    c'est sans consequence pour une feuille repetable en niveaux de gris, ou seule
    l'echelle compte. Une carte PEINTE, elle, donne un sens a chaque texel — un
    matricule, une bande, une ligne de panneau ont une adresse. Deux faces qui
    partagent un texel rendent la peinture impossible. D'ou cette fonction.

    ⚠️ ELLE UTILISE `bpy.ops.uv.smart_project`, QUE LE KIT REFUSAIT PAR PRINCIPE.
    La docstring de `box_project_uv()` disait : « son resultat bouge d'une version de
    Blender a l'autre ». C'etait un argument de prudence, jamais mesure. Il l'a ete
    le 2026-09-05, sur la coque reelle (`specter_9_c.glb`, 102 738 triangles,
    308 214 boucles UV, 40 objets) : **deux executions rendent le meme sha256 des UV,
    au bit pres**, en 0,3 seconde. Trois executions sur un maillage de test penible
    (faces obliques, n-gons, tailles melangees) : idem.

    Ce qui rend cela vrai ici, et qui ne l'etait peut-etre pas quand la regle a ete
    ecrite : la version de Blender est **epinglee** (4.5.11 LTS) et `-t 1` est **force**
    par `scripts/build-hull.sh`. Le jour ou l'une des deux conditions tombe, la mesure
    est a refaire — pas la peine de rediscuter, il suffit de relancer `--check`.

    `angle_limit_deg` : au-dela de cet angle entre deux faces, une couture est posee.
    `margin` : marge entre ilots, en fraction du carre UV. A 2048 px, 0,002 fait 4 px —
    de quoi encaisser le filtrage bilineaire et les mipmaps sans que deux ilots bavent
    l'un sur l'autre.
    `probe` : cote de la grille de sondage du recouvrement. 0 desactive la mesure.
    `min_fill` : plancher de rendement. En dessous, on paie un atlas qu'on ne lit pas.

    Les defauts viennent d'un balayage sur la coque reelle (2026-09-05, 102 738
    triangles) — ce sont des mesures, pas des gouts :

    | angle | marge  | remplissage | recouvrement |
    |-------|--------|-------------|--------------|
    | 45°   | 0,0015 | 39,0 %      | 0            |
    | 66°   | 0,0015 | **54,2 %**  | 0            |
    | 66°   | 0,0008 | 54,2 %      | 0            |
    | 82°   | 0,0015 | —           | **2 texels** |

    A 82°, `smart_project` produit des ilots assez etires pour se recouvrir vraiment :
    le garde n'est donc pas decoratif, il a deja refuse une configuration. Descendre
    la marge sous 0,0015 ne rapporte rien et rapproche les ilots pour rien.

    Leve `ContractError` si un UV sort du carre, si deux faces se recouvrent, ou si le
    remplissage passe sous le plancher — un atlas casse ne doit jamais partir en
    silence, c'est la lecon des trois coques livrees sans aucun UV.
    """
    started = _time.time()
    meshes = [objects] if isinstance(objects, bpy.types.Object) else list(objects)
    meshes = [o for o in meshes if o.type == "MESH"]
    if not meshes:
        raise ContractError("atlas_unwrap : aucun objet maillage")

    # Meme raison que dans box_project_uv : un quad gauche n'a pas de normale, donc
    # pas de couture reproductible. On triangule d'abord.
    for obj in meshes:
        triangulate(obj)

    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    # ⚠️ `island_margin=0` : la marge se pose UNE FOIS, au packing. La passer aux deux
    # etages la applique deux fois et fait chuter le rendement — mesure le 2026-09-05 :
    # 17,4 %% de remplissage avec la marge en double, contre le chiffre du rapport ci-dessous
    # avec une seule. Les defauts de `pack_islands` sont deja les bons (ilots concaves,
    # rotation libre, mise a l'echelle) : on ne les surcharge pas.
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle_limit_deg), island_margin=0.0)
    bpy.ops.uv.pack_islands(margin=margin)
    bpy.ops.object.mode_set(mode="OBJECT")

    report = AtlasReport(probe=probe)
    tris: list[tuple[tuple[float, float], ...]] = []
    for obj in meshes:
        layer = obj.data.uv_layers.active
        if layer is None:
            raise ContractError(f"atlas_unwrap : '{obj.name}' n'a pas de calque UV apres depliage")
        uvs = [tuple(loop.vector) for loop in layer.uv]
        report.loops += len(uvs)
        for u, v in uvs:
            if u < -1e-4 or u > 1.0 + 1e-4 or v < -1e-4 or v > 1.0 + 1e-4:
                report.outside += 1
        for poly in obj.data.polygons:
            loops = list(poly.loop_indices)
            for i in range(1, len(loops) - 1):
                tris.append((uvs[loops[0]], uvs[loops[i]], uvs[loops[i + 1]]))
    report.triangles = len(tris)
    report.fill = sum(
        abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) * 0.5
        for a, b, c in tris
    )
    if probe > 0:
        report.overlap_texels = _uv_overlap_texels(tris, probe)
    report.seconds = _time.time() - started

    if report.outside:
        raise ContractError(
            f"atlas_unwrap : {report.outside} boucles UV hors du carre [0, 1] — "
            "le packing a deborde, la carte ne serait pas adressable"
        )
    if report.overlap_texels:
        raise ContractError(
            f"atlas_unwrap : {report.overlap_texels} texels couverts deux fois "
            f"(sonde {probe}x{probe}) — deux faces partagent de la peinture"
        )
    if report.fill < min_fill:
        raise ContractError(
            f"atlas_unwrap : remplissage {report.fill * 100.0:.1f} % sous le plancher "
            f"de {min_fill * 100.0:.0f} % — on paierait un atlas qu'on ne lit pas"
        )
    return report


def _uv_overlap_texels(tris: list, side: int) -> int:
    """Compte les texels couverts par DEUX triangles ou plus.

    Rasterise chaque triangle dans sa boite englobante, par coordonnees
    barycentriques. ⚠️ La leçon de `pratique-revue-asset` s'applique : un rastériseur
    recopie ment. Celui-ci calcule de VRAIES barycentriques (le defaut mesure le
    2026-08-25 rejetait le centre de gravite d'un triangle sur deux et amputait 40 %
    des pixels d'une piece).

    ⚠️ ET IL A MENTI A SON PREMIER ESSAI, DANS L'AUTRE SENS (2026-09-05). Version
    naive, il rapportait 1 a 4 texels doubles sur 1 048 576 — sur un packing pourtant
    sain. Cause : deux triangles ADJACENTS partagent une arete, et un centre de texel
    tombant exactement dessus satisfait `w >= 0` des deux cotes. C'etait un departage
    d'egalite, pas un recouvrement. Chaque triangle est donc RETRACTE d'un quart de
    texel vers son centroide avant rasterisation : les contacts d'arete disparaissent,
    les vrais recouvrements — qui sont des recouvrements d'AIRE — restent.
    """
    import numpy as np

    shrink = 0.25 / side
    counts = np.zeros((side, side), dtype=np.uint16)
    for a, b, c in tris:
        cx = (a[0] + b[0] + c[0]) / 3.0
        cy = (a[1] + b[1] + c[1]) / 3.0
        pulled = []
        for px_, py_ in (a, b, c):
            dx, dy = cx - px_, cy - py_
            norm = math.hypot(dx, dy)
            if norm <= shrink * 2.0:
                pulled = []
                break
            pulled.append((px_ + dx * shrink / norm, py_ + dy * shrink / norm))
        if not pulled:
            continue  # triangle plus petit qu'un demi-texel : impeignable, donc ignore
        a, b, c = pulled
        x0 = max(int(math.floor(min(a[0], b[0], c[0]) * side)), 0)
        x1 = min(int(math.ceil(max(a[0], b[0], c[0]) * side)) + 1, side)
        y0 = max(int(math.floor(min(a[1], b[1], c[1]) * side)), 0)
        y1 = min(int(math.ceil(max(a[1], b[1], c[1]) * side)) + 1, side)
        if x1 <= x0 or y1 <= y0:
            continue
        xs = (np.arange(x0, x1) + 0.5) / side
        ys = (np.arange(y0, y1) + 0.5) / side
        px, py = np.meshgrid(xs, ys)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / d
        w1 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / d
        inside = (w0 >= 0.0) & (w1 >= 0.0) & (w0 + w1 <= 1.0)
        counts[y0:y1, x0:x1] += inside.astype(np.uint16)
    return int(np.count_nonzero(counts > 1))
