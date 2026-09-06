"""Notre transformation de la Specter-9 D — ses 406 pieces entrent dans UN atlas.

    blender-aegis -t 1 -b -P tools/blender/unwrap_specter_9_d.py             # deplie + exporte
    blender-aegis -t 1 -b -P tools/blender/unwrap_specter_9_d.py -- --renders  # + les planches

⚠️ CE N'EST PAS UN SCRIPT DE COQUE DU KIT, ET IL N'EN SUIT PAS LE CONTRAT. Les coques du
kit se generent depuis rien (`ADR-0008` : « le script Python EST la source »). Celle-ci est
un modele TIERS sous regime `ADR-0048` : **sa source est son `.blend`**, versionne dans
`assets/source/models/specter_9_d/`, et c'est lui qui fait foi. Ce fichier est la
transformation qu'on lui applique — exactement la methode de `adapt_specter_9_v3.py`.

⚠️ ET IL NE SAUVEGARDE JAMAIS LE `.blend`. Il l'ouvre, le transforme en memoire, exporte.
La source reste celle de son auteur.

## Ce que cette transformation change, et pourquoi (BRIEF-0102)

La coque portait une **feuille tuilee** a 0,831 tuile/m : tout ce qu'on y peint se repete
tous les 1,20 m. C'est ce qui la separe de la `specter_9_b` — « la B est simple de forme
mais riche de peinture ; la D est riche de forme mais pauvre de peinture ». Une coulure
sous une tuyere, un matricule sur une aile, une trainee sur un bord d'attaque demandent
qu'un texel ait une ADRESSE sur la coque. C'est la definition d'un atlas (`ADR-0047`).

    avant : 406 pieces, chacune projetee en boite, ilots superposes, tuilage libre
    apres : 406 pieces, un seul pack dans [0, 1], ilots disjoints, tuilage 1

## LES CINQ PIEGES DE CETTE PIECE, DANS L'ORDRE OU ILS MORDENT

1. **Le rig se casse sans un mot.** Quatre clips glTF pilotent `CTRL | Wing L/R` et
   `CTRL | Nozzle L/R`, eux-memes portes par des PILOTES Blender qu'un glTF n'execute
   pas. La recette d'export de l'auteur (`scripts/export_asset.py`) les echantillonne en
   images cles ; elle est REPRISE ICI TELLE QUELLE. Un `join`, un `apply` de modificateur
   ou un reparentage suffirait a figer la coque — sans erreur, sans ligne de journal.

2. **Les courbes et les textes ne sont pas des maillages.** 24 courbes et 3 textes
   deviennent des maillages A L'EXPORT. Deplier avant de convertir laisserait 27 pieces
   sans UV d'atlas — et une piece sans UV est definitivement inhabitable (`ADR-0028`).
   La conversion passe donc AVANT le depliage.

3. **La feuille tuilee ne survit pas au nouveau dépliage.** Les six cartes embarquees dans
   le `.glb` sont indexees par les ANCIENNES UV ; posees sur les nouvelles, elles
   rendraient n'importe quoi. Elles sont donc RETIREES du livrable, et chaque materiau
   texture reprend une couleur unie MESUREE sur la carte qu'il perd (moyenne en lineaire).
   Le `.glb` livre ne porte plus aucune texture, conformement a `ADR-0028` — l'atlas cuit
   les remplace.

4. **Mais la cuisson, elle, a besoin des deux.** Un second `.glb` est donc ecrit dans
   `build/` : il garde les cartes ET les deux jeux d'UV (`AtlasUV` en TEXCOORD_0, `TileUV`
   en TEXCOORD_1). C'est LUI que `tools/bake-atlas.py` lit, pour reporter la matiere de la
   feuille dans l'atlas au lieu de la perdre. Il n'est pas versionne : ce script le
   reproduit.

5. **Trianguler la cage change la geometrie livree.** Le kit triangule avant de deplier
   (un quad gauche projette un ilot replie sur lui-meme : 9 398 texels doubles sans ca).
   Mais le BISEAU ne produit pas la meme chose au sommet d'un quad et d'un triangle :
   trianguler tout ajoutait 320 triangles. La regle appliquee ne tranche pas, elle
   MESURE — voir `triangulate_where_free()`.

## Les pieces ne se valent pas, et l'atlas en tient compte

Personne ne peindra sur les 24 petales de tuyere ni sur les stabilisateurs d'un missile.
Chaque famille recoit donc un POIDS, applique entre le depliage et le pack : il agit
lineairement sur la densite de texels et **en carre** sur la surface d'atlas consommee.
Les poids sont dans `FAMILIES` ci-dessous, et le rapport imprime ce que chacune a obtenu.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import sys
from pathlib import Path

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import aegis_kit as ak  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets/source/models/specter_9_d/spectre9_d.blend"
TARGET = ROOT / "assets/imported/models/ships/specter_9_d.glb"
BUILD = ROOT / "build"
#: Ce que lit `tools/bake-atlas.py` : deux jeux d'UV et les cartes d'origine.
BAKE_SOURCE = BUILD / "specter_9_d_atlas_source.glb"
#: L'etat d'AVANT, garde pour la planche de comparaison. `git show HEAD:` en est la
#: reference ; cette copie n'existe que pour ne pas dependre de l'index git.
BEFORE = BUILD / "specter_9_d_before.glb"
#: Ce que la planche de reperage a besoin de savoir : quelle piece est dans quelle zone.
ZONES = BUILD / "specter_9_d_zones.json"

ASSET = "S9D | Aircraft"
CONTROL_NAMES = ["CTRL | Wing L", "CTRL | Wing R", "CTRL | Nozzle L", "CTRL | Nozzle R"]

#: Cote de l'atlas vise. `ADR-0047` tranche la contradiction dormante en faveur de la
#: spec : un atlas de coque se cuit en 2048.
ATLAS_SIDE = 2048
#: Facteur d'echelle de la coque en jeu (`scenes/player/hulls/specter_9_d.tscn`). Il ne
#: sert qu'a exprimer la densite en metres de JEU en plus des metres de modele.
GAME_SCALE = 0.19501

#: (fragment de nom, famille, poids). PREMIERE REGLE QUI MATCHE. Une piece qui ne matche
#: rien fait ECHOUER le script : un poids par defaut serait exactement le genre de silence
#: qui produit une coque nette d'un cote et floue de l'autre.
#:
#: ⚠️ LES POIDS SONT UN ARBITRAGE, ET IL SE DEFEND CHIFFRE. `skin` porte ce qu'on
#: regardera de face a 70 deg d'elevation et ce qu'on peindra ; `mechanism` porte des
#: pieces vues en enfilade, de trois quarts arriere, jamais de face ; `hardware` porte des
#: rivets de 20 mm et des ailerons de missile de 3 mm d'epaisseur — a 45,8 px/m en jeu,
#: un rivet fait UN CINQUIEME de pixel.
FAMILIES: tuple[tuple[str, str, float], ...] = (
    # --- la peau : tout ce qui portera une livree, une trainee, un matricule ---------
    ("continuous editable fuselage", "skin", 1.00),
    ("fitted armor", "skin", 1.00),
    ("editable delta wing core", "skin", 1.00),
    ("wing armor", "skin", 1.00),
    ("nacelle armor", "skin", 1.00),
    ("engine structural shell", "skin", 1.00),
    ("fixed wing-root fairing", "skin", 1.00),
    ("swept vertical stabilizer", "skin", 1.00),
    ("nose armor", "skin", 1.00),
    ("ventral access panel", "skin", 1.00),
    ("nacelle dorsal service plate", "skin", 1.00),
    ("engine service hatch", "skin", 1.00),
    ("intake surround", "skin", 1.00),
    ("recessed thermal intake", "skin", 1.00),
    # La livree du modele est en GEOMETRIE (des panneaux bleus et rouges rapportes) :
    # ces pieces-la sont de la peau, pas de la quincaillerie.
    ("cobalt trailing edge", "skin", 1.00),
    ("rear cobalt spine", "skin", 1.00),
    ("forward cobalt nose accent", "skin", 1.00),
    ("angular cobalt wing flash", "skin", 1.00),
    ("fin cobalt flash", "skin", 1.00),
    ("root blue stripe", "skin", 1.00),
    # --- la verriere : le cadre se peint, le vitrage non ------------------------------
    ("canopy longitudinal frame", "canopy_frame", 1.00),
    ("fixed transverse frame", "canopy_frame", 1.00),
    ("canopy sill bronze", "canopy_frame", 1.00),
    ("fixed smoked glazing", "glazing", 0.55),
    # --- les marquages : petits, mais ce sont eux qu'on veut nets ---------------------
    ("alliance insignia", "markings", 1.00),
    ("wing number", "markings", 1.00),
    ("identification", "markings", 1.00),
    ("scarlet nose pinstripe", "markings", 1.00),
    ("inboard red warning chevron", "markings", 1.00),
    ("red wingtip warning", "markings", 1.00),
    ("fin red tip", "markings", 1.00),
    # --- la mecanique : vue en enfilade, jamais peinte ---------------------------------
    ("nozzle petal", "mechanism", 0.55),
    ("nozzle dark expansion band", "mechanism", 0.55),
    ("nozzle telescopic sleeve", "mechanism", 0.55),
    ("deep ion chamber", "mechanism", 0.55),
    ("cyan exhaust rim", "mechanism", 0.55),
    ("hot central plasma", "mechanism", 0.55),
    ("rcs nozzle", "mechanism", 0.55),
    ("engine heat exchanger", "mechanism", 0.55),
    ("engine reinforcement band", "mechanism", 0.55),
    ("armored coolant line", "mechanism", 0.55),
    ("intake grille", "mechanism", 0.55),
    # --- la quincaillerie : sous le pixel en jeu ---------------------------------------
    ("wing access fastener", "hardware", 0.45),
    ("nacelle plate fastener", "hardware", 0.45),
    ("laser barrel", "hardware", 0.45),
    ("laser muzzle", "hardware", 0.45),
    ("laser receiver", "hardware", 0.45),
    ("missile body", "hardware", 0.45),
    ("missile pointed nose", "hardware", 0.45),
    ("missile pylon", "hardware", 0.45),
    ("missile stabilizer", "hardware", 0.45),
    ("nose optical sensor", "hardware", 0.45),
)


def classify(obj: bpy.types.Object) -> tuple[str, float]:
    """(famille, poids) d'une piece. Leve si le nom n'est couvert par aucune regle."""
    lowered = obj.name.lower()
    for fragment, family, weight in FAMILIES:
        if fragment in lowered:
            return family, weight
    raise ak.ContractError(
        "unwrap : '%s' ne tombe dans aucune famille — le .blend a change de noms, et un "
        "poids par defaut serait un silence" % obj.name
    )


def module_of(obj: bpy.types.Object) -> str:
    """La ZONE au sens du peintre : le module auquel la piece appartient.

    Elle vient des collections du `.blend` (`MODULE | Wing L`...), pas d'une heuristique
    sur le nom : c'est la seule decoupe que l'auteur ait declaree.
    """
    for collection in obj.users_collection:
        if collection.name.startswith("MODULE | "):
            return collection.name.split("| ", 1)[1]
    return "Fuselage"


# ---------------------------------------------------------------------------
# 1. La scene : convertir, puis deplier
# ---------------------------------------------------------------------------


def convert_curves(asset: bpy.types.Collection) -> int:
    """Courbes et textes -> maillages, AVANT le depliage (piege n°2 de l'en-tete)."""
    bpy.ops.object.select_all(action="DESELECT")
    targets = [o for o in asset.all_objects if o.type in {"CURVE", "FONT"}]
    for obj in targets:
        obj.hide_set(False)
        obj.select_set(True)
    if targets:
        bpy.context.view_layer.objects.active = targets[0]
        bpy.ops.object.convert(target="MESH")
    return len(targets)


def _evaluated_triangles(obj: bpy.types.Object) -> int:
    """Le nombre de triangles que cette piece donnera A L'EXPORT, modificateurs compris."""
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    count = sum(len(p.vertices) - 2 for p in mesh.polygons)
    evaluated.to_mesh_clear()
    return count


def triangulate_where_free(meshes: list[bpy.types.Object]) -> list[str]:
    """Triangule chaque piece SI ET SEULEMENT SI sa geometrie livree n'en bouge pas.

    ⚠️ LES DEUX EXIGENCES DE CE LOT S'OPPOSENT, ET C'EST MESURE. `atlas_unwrap()`
    triangule avant de deplier pour une bonne raison (voir `ak.triangulate`) : un quad
    GAUCHE n'a pas de normale, sa projection se calcule pour un plan qui n'est celui
    d'aucun de ses deux triangles, et l'ilot obtenu **se replie sur lui-meme**. Sans
    triangulation prealable, la mesure du 2026-09-06 donne **9 398 texels couverts deux
    fois** (1,5e-02, trente fois le seuil d'`ADR-0047`) : la peinture y serait double.

    Mais ce maillage est porte par des modificateurs, et le BISEAU ne produit pas la
    meme chose aux sommets d'un quad et d'un triangle. Trianguler tout ajoutait
    **320 triangles** (49 436 au lieu de 49 116) a un lot qui ne redessine rien.

    D'ou cette regle, qui n'arbitre pas mais MESURE : on triangule, on recompte la
    geometrie evaluee, et **on annule si elle a bouge**. Deux pieces sur 406 refusent
    (le vitrage et le fuselage continu) ; elles gardent leurs quads, et le recouvrement
    residuel qu'elles causent est mesure par le garde d'`atlas_unwrap()`, qui reste arme.
    """
    refused: list[str] = []
    for obj in meshes:
        before = _evaluated_triangles(obj)
        backup = obj.data.copy()
        ak.triangulate(obj)
        if _evaluated_triangles(obj) != before:
            broken, obj.data = obj.data, backup
            bpy.data.meshes.remove(broken)
            refused.append(obj.name)
        else:
            bpy.data.meshes.remove(backup)
    return refused


def split_uv_layers(meshes: list[bpy.types.Object]) -> int:
    """Prepare deux calques : `AtlasUV` en premier, `TileUV` en second.

    ⚠️ L'ORDRE EST LE CONTRAT. L'exporteur glTF numerote les TEXCOORD dans l'ordre des
    calques : le premier devient `TEXCOORD_0`, celui que Godot lit. L'atlas doit donc
    ECRASER le calque 0, pas s'ajouter apres lui — sinon le jeu echantillonnerait la
    feuille tuilee avec l'adresse de l'atlas, et personne ne verrait d'erreur.

    Les 76 pieces qui portaient deux calques (`UVMap` actif + `SurfaceUV` dormant)
    perdent le dormant : il n'a jamais servi au rendu et il decalerait la numerotation.
    """
    kept = 0
    for obj in meshes:
        layers = obj.data.uv_layers
        if not layers:
            continue  # une courbe convertie sans UV : elle n'a pas de feuille a garder
        for extra in list(layers)[1:]:
            layers.remove(extra)
        layers[0].active = True
        layers[0].active_render = True
        tile = layers.new(name="TileUV", do_init=True)  # copie du calque actif
        tile.active_render = False
        layers[0].name = "AtlasUV"
        layers[0].active = True
        layers[0].active_render = True
        kept += 1
    return kept


def unwrap(asset: bpy.types.Collection) -> tuple[ak.AtlasReport, list[bpy.types.Object]]:
    meshes = sorted([o for o in asset.all_objects if o.type == "MESH"], key=lambda o: o.name)
    for obj in meshes:
        obj.hide_set(False)
    refused = triangulate_where_free(meshes)
    print("[unwrap] triangulation prealable : %d pieces sur %d, %s la refusent (leur "
          "biseau changerait)" % (len(meshes) - len(refused), len(meshes),
                                  " et ".join("'%s'" % n for n in refused) or "aucune"))
    kept = split_uv_layers(meshes)
    print("[unwrap] %d maillages, %d gardent leur feuille en TileUV" % (len(meshes), kept))
    report = ak.atlas_unwrap(
        meshes,
        # ⚠️ ON NE TRIANGULE PAS LA CAGE. Elle n'est pas ce qu'on exporte : BEVEL et
        # SOLIDIFY en tirent la geometrie livree, et trianguler l'entree du biseau
        # ajoutait 320 triangles (49 436 au lieu de 49 116) a un lot qui ne redessine
        # rien. Mesure du 2026-09-06.
        triangulate_first=False,
        weight_of=lambda o: classify(o)[1],
        family_of=lambda o: classify(o)[0],
        texel_side=ATLAS_SIDE,
    )
    print("[unwrap] " + report.render())
    print(report.render_families())
    return report, meshes


# ---------------------------------------------------------------------------
# 2. Les materiaux : une couleur unie MESUREE, et la feuille rendue au bake
# ---------------------------------------------------------------------------


def _srgb_to_linear(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def bind_sheets_to_tile_uv() -> int:
    """Branche chaque image sur `TileUV` — pour que le fichier DISE son jeu d'UV.

    Sans ce nœud, l'exporteur ecrit `texCoord: 0` et la cuisson echantillonnerait la
    feuille avec l'adresse de l'atlas. Avec lui, le `.glb` de cuisson porte
    `texCoord: 1` et `bake-atlas.py` sait ou lire. C'est de l'information portee par le
    fichier plutot que par une option de ligne de commande, donc une chose de moins a se
    rappeler.
    """
    bound = 0
    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        nodes, links = material.node_tree.nodes, material.node_tree.links
        images = [n for n in nodes if n.type == "TEX_IMAGE"]
        if not images:
            continue
        source = nodes.new("ShaderNodeUVMap")
        source.uv_map = "TileUV"
        for node in images:
            links.new(source.outputs["UV"], node.inputs["Vector"])
            bound += 1
    return bound


def flatten_materials() -> dict[str, tuple[float, float, float]]:
    """Retire les cartes et rend a chaque materiau une couleur unie MESUREE sur elles.

    ⚠️ LA COULEUR N'EST PAS RECOPIEE DEPUIS LA CHARTE, elle est MOYENNEE sur la carte que
    le materiau perd, en LINEAIRE. Deux raisons : la palette garde une source de verite
    unique (le fichier), et une moyenne prise en sRGB rendrait une teinte trop claire —
    la moyenne d'une courbe convexe n'est pas la courbe de la moyenne.

    Ce que le `.glb` livre perd : les six cartes embarquees. Ce qu'il gagne : d'etre
    conforme a `ADR-0028` (aucune texture livree par la forge) et de ne plus porter
    d'image indexee par des UV qui n'existent plus.
    """
    tints: dict[str, tuple[float, float, float]] = {}
    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        nodes = material.node_tree.nodes
        shader = nodes.get("Principled BSDF")
        images = [n for n in nodes if n.type == "TEX_IMAGE"]
        if shader is None or not images:
            continue
        base = next((n for n in images
                     if n.image and n.image.colorspace_settings.name != "Non-Color"), None)
        if base is not None:
            pixels = list(base.image.pixels)
            channels = base.image.channels
            means = [sum(pixels[c::channels]) / (len(pixels) / channels) for c in range(3)]
            # Les cartes sont ecrites en sRGB par `scripts/materials.py` ; `image.pixels`
            # rend les octets bruts. On linearise AVANT de moyenner.
            linear = tuple(_srgb_to_linear(v) for v in means)
            shader.inputs["Base Color"].default_value = (*linear, 1.0)
            tints[material.name] = linear
        for node in list(nodes):
            if node.type in {"TEX_IMAGE", "NORMAL_MAP", "UVMAP"}:
                nodes.remove(node)
    for image in list(bpy.data.images):
        if image.users == 0:
            bpy.data.images.remove(image)
    return tints


def drop_tile_uv(meshes: list[bpy.types.Object]) -> None:
    """Le livrable ne porte qu'un jeu d'UV : l'atlas. Le second n'y sert plus a rien."""
    for obj in meshes:
        layers = obj.data.uv_layers
        for layer in list(layers):
            if layer.name == "TileUV":
                layers.remove(layer)
        if layers:
            layers[0].active = True
            layers[0].active_render = True


# ---------------------------------------------------------------------------
# 3. Le rig : la recette d'export de l'auteur, REPRISE TELLE QUELLE
# ---------------------------------------------------------------------------


def bake_clips(scene: bpy.types.Scene) -> list[str]:
    """Echantillonne les pilotes en images cles et remonte les quatre pistes NLA.

    ⚠️ RECOPIEE DE `assets/source/models/specter_9_d/scripts/export_asset.py`, sans une
    valeur changee : quatre clips, les memes bornes de marqueurs, les memes longueurs de
    transition. C'est le contrat que le moteur lit. Un glTF n'execute pas les pilotes de
    Blender : sans cet echantillonnage, le `.glb` sortirait avec une animation VIDE et la
    coque serait figee en jeu — sans une erreur ni une ligne de journal.
    """
    controls = [bpy.data.objects[name] for name in CONTROL_NAMES]
    sampled = {}
    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        sampled[frame] = {obj.name: {"location": list(obj.location),
                                     "rotation": list(obj.rotation_euler)}
                          for obj in controls}
    markers = {marker.name: marker.frame for marker in scene.timeline_markers}
    start = scene.frame_start
    cruise = markers.get("CRUISE", 76)
    intercept = markers.get("INTERCEPT", 151)
    scene.frame_set(start)
    bpy.context.view_layer.update()
    bpy.data.objects["CTRL | Aircraft"].animation_data_clear()
    for obj in controls:
        obj.animation_data_clear()

    def transition(a, b, frames):
        result = {}
        for frame in range(1, frames + 1):
            t = (frame - 1) / (frames - 1)
            t = t * t * (3 - 2 * t)
            result[frame] = {name: {channel: [x * (1 - t) + y * t
                                              for x, y in zip(a[name][channel], b[name][channel])]
                                    for channel in ["location", "rotation"]}
                             for name in CONTROL_NAMES}
        return result

    clips = {
        "Flight_Demo": {frame - start + 1: pose for frame, pose in sampled.items()},
        "Maneuver_to_Cruise": transition(sampled[start], sampled[cruise], 46),
        "Cruise_to_Intercept": transition(sampled[cruise], sampled[intercept], 46),
        "Intercept_to_Maneuver": transition(sampled[intercept], sampled[start], 61),
    }
    for obj in controls:
        for clip, poses in clips.items():
            obj.animation_data_create()
            obj.animation_data.action = None
            for frame, pose in poses.items():
                obj.location = pose[obj.name]["location"]
                obj.rotation_euler = pose[obj.name]["rotation"]
                obj.keyframe_insert(data_path="location", frame=frame)
                obj.keyframe_insert(data_path="rotation_euler", frame=frame)
            action = obj.animation_data.action
            action.name = clip + " | " + obj.name
            track = obj.animation_data.nla_tracks.new()
            track.name = clip
            strip = track.strips.new(clip, 1, action)
            strip.extrapolation = "NOTHING"
            track.mute = True
            obj.animation_data.action = None
        obj.location = sampled[start][obj.name]["location"]
        obj.rotation_euler = sampled[start][obj.name]["rotation"]
    scene.frame_set(1)
    return list(clips)


def export(asset: bpy.types.Collection, path: Path) -> None:
    """Les memes options que l'auteur — `NLA_TRACKS` et echantillonnage force."""
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in asset.all_objects:
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["CTRL | Aircraft"]
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_apply=True, export_animations=True, export_animation_mode="NLA_TRACKS",
        export_force_sampling=True, export_frame_range=False,
        export_anim_slide_to_zero=True, export_extras=True,
        export_cameras=False, export_lights=False)
    print("[unwrap] ecrit %s (%.1f Mo)" % (path, path.stat().st_size / 1e6))


# ---------------------------------------------------------------------------
# 4. Les planches (ADR-0006 : un livrable non regarde n'est pas valide)
# ---------------------------------------------------------------------------


#: Le fond spatial du jeu (#070A12) en lineaire, l'inclinaison de la camera de jeu et
#: son champ : les trois viennent de `tools/render-hull.py`, qui les tient de
#: `scenes/gameplay/graybox.tscn:45`. Juger une coque sur du gris n'a aucun sens, et un
#: rendu a 20 deg d'elevation validerait des surfaces que le joueur ne voit jamais.
BACKDROP = (0.0027, 0.0039, 0.0070, 1.0)
GAME_PITCH_DEG = 20.0
GAME_FOV_DEG = 62.0
TILE = 768
SAMPLES = 48


def _reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    world = bpy.data.worlds.new("preview")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = BACKDROP
    bpy.context.scene.world = world


def _import_hull(path: Path):
    """Importe un `.glb` et le remet dans le sens du JEU.

    ⚠️ LE LACET DE 180 DEG N'EST PAS DECORATIF. Le modele a le nez vers +Z glTF, donc
    vers -Y apres import Blender, alors que la planche et le jeu le lisent nez en haut
    (`scenes/player/hulls/specter_9_d.tscn`). Sans cette rotation, la planche montrerait
    le vaisseau en marche arriere et on jugerait le dessous pour le dessus.
    """
    bpy.ops.import_scene.gltf(filepath=str(path))
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.rotation_euler[2] += math.pi
    bpy.context.view_layer.update()
    import numpy as np

    points = []
    dg = bpy.context.evaluated_depsgraph_get()
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        matrix = obj.matrix_world
        mesh = obj.evaluated_get(dg).to_mesh()
        points.extend([matrix @ v.co for v in mesh.vertices])
        obj.evaluated_get(dg).to_mesh_clear()
    array = np.array([[p.x, p.y, p.z] for p in points])
    center = (array.min(axis=0) + array.max(axis=0)) * 0.5
    radius = float(np.linalg.norm(array.max(axis=0) - array.min(axis=0))) * 0.5
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location = tuple(c - m for c, m in zip(obj.location, center))
    return radius


def _lights(radius: float) -> None:
    for name, position, energy, size in (
        ("Key", (-1.1, -0.9, 1.6), 1400.0, 2.2),
        ("Fill", (1.5, -0.6, 0.35), 380.0, 3.2),
        ("Rim", (0.2, 1.5, 0.9), 900.0, 1.8),
    ):
        data = bpy.data.lights.new(name, type="AREA")
        data.energy = energy * radius * radius
        data.size = size * radius
        light = bpy.data.objects.new(name, data)
        light.location = tuple(c * radius * 4.0 for c in position)
        direction = -light.location.normalized()
        light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(light)


def _camera(pitch_deg: float, fov_deg: float, radius: float) -> None:
    from mathutils import Euler, Vector

    data = bpy.data.cameras.new("cam")
    data.lens_unit = "FOV"
    data.angle = math.radians(fov_deg)
    camera = bpy.data.objects.new("cam", data)
    bpy.context.collection.objects.link(camera)
    rotation = Euler((math.radians(pitch_deg), 0.0, 0.0), "XYZ")
    camera.rotation_euler = rotation
    forward = rotation.to_matrix() @ Vector((0.0, 0.0, -1.0))
    camera.location = -forward * (radius / math.tan(math.radians(fov_deg) * 0.5) * 1.05)
    bpy.context.scene.camera = camera


def _dress(image_path: Path | None, checker: bool = False) -> None:
    """Habille TOUTES les surfaces d'une meme carte, indexee par TEXCOORD_0.

    C'est ce que le regime atlas d'`ADR-0047` fait cote moteur : la carte REMPLACE la
    couleur de palette, elle ne la multiplie pas. On reproduit donc la pose exacte —
    couleur de base neutre, image branchee, tuilage 1.
    """
    if checker:
        image = bpy.data.images.new("checker", width=1024, height=1024)
        image.generated_type = "UV_GRID"
    else:
        image = bpy.data.images.load(str(image_path))
    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        nodes, links = material.node_tree.nodes, material.node_tree.links
        shader = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
        if shader is None:
            continue
        for node in list(nodes):
            if node.type == "TEX_IMAGE":
                nodes.remove(node)
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = image
        texture.interpolation = "Closest" if checker else "Linear"
        links.new(texture.outputs["Color"], shader.inputs["Base Color"])


def _render(path: Path) -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.resolution_x = TILE
    scene.render.resolution_y = TILE
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def _shot(source: Path, out: Path, dress: str) -> None:
    _reset_scene()
    radius = _import_hull(source)
    if dress == "atlas":
        _dress(ROOT / "assets/imported/textures/hull/specter_9_d_albedo.png")
    elif dress == "checker":
        _dress(None, checker=True)
    _lights(radius)
    _camera(GAME_PITCH_DEG, GAME_FOV_DEG, radius)
    _render(out)
    print("[planche] %s" % out)


def _compose(tiles: list[Path], out: Path) -> None:
    """Colle les vignettes cote a cote. Pas de PIL dans le Python de Blender."""
    import numpy as np

    sheet = np.zeros((TILE, TILE * len(tiles), 4), dtype=np.float32)
    for index, path in enumerate(tiles):
        image = bpy.data.images.load(str(path))
        buffer = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(buffer)
        sheet[:, index * TILE:(index + 1) * TILE] = buffer.reshape(TILE, TILE, 4)
        bpy.data.images.remove(image)
    result = bpy.data.images.new("sheet", width=TILE * len(tiles), height=TILE)
    result.pixels.foreach_set(sheet.reshape(-1))
    result.filepath_raw = str(out)
    result.file_format = "PNG"
    result.save()
    print("[planche] %s" % out)


def _local_variance(path: Path) -> float:
    """Ecart-type de luminance SUR LA COQUE, en pourcent — la mesure qui refuse un rendu.

    ⚠️ ELLE EST LA POUR EMPECHER UNE PROMESSE. Mesure du 2026-09-05 sur une autre coque :
    un atlas cuit n'a pas bouge la variance locale, et le rendu a ete refuse. Un atlas
    rend la peinture POSSIBLE ; il ne peint pas. Si ce chiffre ne bouge pas entre les
    deux vignettes, il faut le DIRE, pas le maquiller.
    """
    import numpy as np

    image = bpy.data.images.load(str(path))
    buffer = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(buffer)
    bpy.data.images.remove(image)
    pixels = buffer.reshape(-1, 4)[:, :3]
    luminance = pixels @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    hull = luminance[luminance > 0.01]  # le fond spatial n'est pas de la coque
    return float(hull.std() / max(hull.mean(), 1e-6) * 100.0)


def renders() -> None:
    """Deux planches, a la camera du jeu : l'avant/apres, et le damier UV.

    ⚠️ LA CAPTURE AU BESTIAIRE N'EST PAS FAISABLE ICI, et il ne faut pas faire semblant :
    habiller la coque de l'atlas cote moteur demande de cabler `HullDetailSet`, donc
    d'ecrire dans `resources/` — hors du perimetre de la forge. Ce qui suit est la
    meilleure approximation disponible : le meme eclairage, le meme angle, les deux etats.
    """
    out = ROOT / "docs/forge/output"
    out.mkdir(parents=True, exist_ok=True)
    before, after = BUILD / "shot_before.png", BUILD / "shot_after.png"
    checker = BUILD / "shot_checker.png"
    _shot(BEFORE, before, dress="none")
    _shot(TARGET, after, dress="atlas")
    _shot(TARGET, checker, dress="checker")
    _compose([before, after], out / "BRIEF-0102-avant-apres.png")
    _compose([checker], out / "BRIEF-0102-uv-checker.png")
    print("[planche] variance locale : avant %.1f %%, apres %.1f %% "
          "(un atlas rend la peinture possible, il ne peint pas)"
          % (_local_variance(before), _local_variance(after)))


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    if TARGET.exists() and not BEFORE.exists():
        shutil.copy2(TARGET, BEFORE)
        print("[unwrap] etat d'avant garde dans %s" % BEFORE)
    if "--renders" in sys.argv:
        renders()
        return

    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    asset = bpy.data.collections[ASSET]
    converted = convert_curves(asset)
    print("[unwrap] %d courbes/textes convertis en maillages AVANT depliage" % converted)

    report, meshes = unwrap(asset)
    ZONES.write_text(json.dumps({
        obj.name: {"family": classify(obj)[0], "weight": classify(obj)[1],
                   "module": module_of(obj)}
        for obj in meshes}, indent=1, sort_keys=True) + "\n")
    print("[unwrap] zones ecrites dans %s" % ZONES)

    clips = bake_clips(scene)
    print("[unwrap] %d clips cuits en images cles : %s" % (len(clips), ", ".join(clips)))

    bound = bind_sheets_to_tile_uv()
    print("[unwrap] %d images branchees sur TileUV (TEXCOORD_1)" % bound)
    export(asset, BAKE_SOURCE)

    tints = flatten_materials()
    for name, color in sorted(tints.items()):
        srgb = tuple(round(255 * (v * 12.92 if v <= 0.0031308
                                  else 1.055 * v ** (1 / 2.4) - 0.055)) for v in color)
        print("[unwrap] %-24s -> couleur unie mesuree %s (sRGB %s)"
              % (name, tuple(round(v, 4) for v in color), srgb))
    drop_tile_uv(meshes)
    export(asset, TARGET)

    density = report.families["skin"].density(ATLAS_SIDE) if report.families else 0.0
    print("[unwrap] densite de la peau : %.1f texels/m de modele, soit %.0f texels/m de jeu"
          % (density, density / GAME_SCALE))
    print("[unwrap] TERMINE — cuire ensuite : python3 tools/bake-atlas.py %s --out "
          "assets/imported/textures/hull" % BAKE_SOURCE.relative_to(ROOT))


main()
