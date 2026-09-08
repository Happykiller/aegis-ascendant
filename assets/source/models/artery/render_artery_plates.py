"""Les planches de controle du BRIEF-0108 — A LA CAMERA DU JEU.

    blender-aegis -t 1 -b -noaudio --python assets/source/models/artery/render_artery_plates.py -- --states
    blender-aegis -t 1 -b -noaudio --python assets/source/models/artery/render_artery_plates.py -- --materials

⚠️ UN ASSET NON RENDU ET NON REGARDE N'EST PAS VALIDE (`ADR-0006`). Un rendu
studio ne prouve rien : ce qui compte est le cadrage du jeu, sa lumiere et sa
distance. Tout le rig vient donc de `build_long_cortege.py` — camera (0 ; 14 ; 5),
FOV 62 vertical, trois directionnelles, aucune ombre portee — et n'est PAS
recopie : il est importe.

⚠️ ET LES DEUX PIECES NE SE JOUENT PAS AU MEME ENDROIT, DONC PAS A LA MEME
DISTANCE. Mesure, pas souvenir :

    pont du corridor   y = -4,30   cadre 41,60 m   46,2 px/m
    pont de poupe      y = -11,85  cadre 58,77 m   32,7 px/m

Le pylone se pose sur les etagères de rive de la POUPE (32,7 px/m, a
`asset_scale` lu dans `long_cortege_stern.tres`) ; la conduite et le flexible
sur l'artere du CORRIDOR (46,2 px/m). Juger les trois au meme cadrage serait
mentir d'un tiers sur l'un des deux.

⚠️ LE PLACEMENT N'EST PAS UN LIVRABLE (brief §Hors perimetre). Les pieces sont
alignees sur le pont pour etre REGARDEES, pas posees : combien, ou, sur quels
troncons, c'est une decision de conception.
"""

from __future__ import annotations

import math
import os
import re
import sys
import tempfile

import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools", "blender"))
sys.path.insert(0, os.path.join(REPO, "tools", "blender", "lib"))
import build_long_cortege as blc  # noqa: E402

MODELS = os.path.join(REPO, "assets", "imported", "models", "backgrounds")
ALT = os.path.join(REPO, "build", "artery_brief_materials")
OUT = os.path.join(REPO, "docs", "forge", "output")

TILE_W, TILE_H = 1920, 1080
FPS = 30

#: Le pont du corridor, ou se pose l'artere (`build_long_cortege.HULL_*`).
CORRIDOR_DECK = -4.30


def tuning() -> dict:
    """Relit `long_cortege_stern.tres`. On ne le modifie pas : on s'y plie."""
    path = os.path.join(REPO, "resources", "levels", "long_cortege_stern.tres")
    out: dict = {}
    for key, raw in re.findall(r"^(\w+) = (.+)$", open(path, encoding="utf-8").read(), re.M):
        raw = raw.strip()
        vec = re.match(r"Vector3\(([^)]*)\)", raw)
        if vec:
            out[key] = Vector([float(v) for v in vec.group(1).split(",")])
        else:
            try:
                out[key] = float(raw)
            except ValueError:
                pass
    return out


T = tuning()


def place(path: str, position: Vector, k: float, yaw: float = 0.0) -> list:
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    fresh = [o for o in bpy.context.scene.objects if o not in before]
    holder = bpy.data.objects.new(os.path.basename(path), None)
    bpy.context.collection.objects.link(holder)
    holder.location = blc._to_blender(position)
    holder.rotation_euler = Euler((0.0, 0.0, yaw), "XYZ")
    holder.scale = (k, k, k)
    for obj in fresh:
        if obj.parent is None:
            obj.parent = holder
            obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.visible_shadow = False
    return fresh


def solo(objects: list, clip: str) -> None:
    """Ne laisse qu'une piste vivante. Les autres se taisent."""
    for obj in objects:
        if obj.animation_data is None:
            continue
        obj.animation_data.action = None
        for track in obj.animation_data.nla_tracks:
            track.mute = track.name != clip


def deck(level: float, width: float, depth: float, name: str) -> None:
    """Le pont, boite grise. Sans lui les pieces flottent et la planche ment."""
    mesh = bpy.data.meshes.new(name)
    verts = []
    for sx in (-0.5, 0.5):
        for sy in (-0.5, 0.5):
            for sz in (-0.5, 0.5):
                verts.append((sx * width, sz * depth, sy * 1.6))
    mesh.from_pydata(verts, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
                                 (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = blc._to_blender(Vector((0.0, level - 0.80, 0.0)))
    mat = bpy.data.materials.new(name + "Grey")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.009, 0.009, 0.013, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.4
    bsdf.inputs["Roughness"].default_value = 0.6
    mesh.materials.append(mat)
    obj.visible_shadow = False
    bpy.context.collection.objects.link(obj)


def blackout() -> None:
    """Eteint `AA_Emissive_Engine`, et LUI SEUL.

    ⚠️ C'EST LA PREUVE VISUELLE DU CONTRAT DE MATERIAUX, pas un effet. Une veine
    encore allumee ici a ete peinte dans un autre slot — le defaut que rien ne
    signale, ni erreur ni test rouge, et dont depend le blackout du niveau."""
    for mat in bpy.data.materials:
        if not mat.name.split(".")[0].startswith("AA_Emissive") or not mat.use_nodes:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                node.inputs["Emission Strength"].default_value = 0.0


# --------------------------------------------------------------------------
# Les montages
# --------------------------------------------------------------------------

#: (clip conduite/flexible, image) — 121 images pour `Rupture`, 61 sinon.
ARTERY_STATES = {
    "intact": (("Actif", "Intact"), 12),
    "endommage": (("Endommage", "Endommage"), 34),
    "rupture": (("Rupture", "Rupture"), 88),
    "rompu": (("Rompu", "Rompu"), 30),
}


def build_artery(state: str, root: str) -> None:
    (conduit_clip, hose_clip), frame = ARTERY_STATES[state]
    # ⚠️ POSEES DANS LE PLAN DE JEU (24 x 14), PAS AU LOIN. Le rectangle
    # logique va de x = -12 a +12 et de z = -7 a +7 : c'est la que le joueur
    # les croisera, et c'est donc la qu'il faut les regarder.
    layout = [
        ("artery_conduit.glb", -8.5, conduit_clip),
        ("artery_conduit_bend.glb", -3.0, conduit_clip),
        ("artery_hose.glb", 2.5, hose_clip),
        ("artery_hose_bend.glb", 7.5, hose_clip),
    ]
    for name, x, clip in layout:
        objects = place(os.path.join(root, name),
                        Vector((x, CORRIDOR_DECK, 0.0)), 1.0)
        solo(objects, clip)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()


def build_pylons(clip: str, frame: int) -> None:
    """Quatre pylones, a l'echelle de jeu de la poupe, sur son pont."""
    k = T["asset_scale"]
    for x in (-1.5, -0.5, 0.5, 1.5):
        objects = place(os.path.join(MODELS, "stern_pylon.glb"),
                        Vector((x * T["engine_spacing"] * 0.62, T["deck_y"], 0.0)), k)
        solo(objects, clip)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()


def frame_px(level: float) -> tuple[float, float]:
    metrics = blc._frame_coverage(level)
    return metrics["frame_width"], TILE_W / metrics["frame_width"]


def tile(path: str, kind: str, head: str, tint, sub: str = "",
         dark: bool = False, checker: bool = False, root: str = MODELS) -> None:
    blc._plate_reset()
    bpy.context.scene.render.fps = FPS
    if kind.startswith("pylon"):
        level = T["deck_y"]
        deck(level, T["engine_spacing"] * 2.6 + 8.0, 18.0, "SternDeck")
        build_pylons("Maintenance" if kind == "pylon_maintenance" else "Service",
                     90 if kind == "pylon_maintenance" else 12)
    else:
        level = CORRIDOR_DECK
        deck(level, 30.0, 17.0, "CorridorDeck")
        build_artery(kind, root)
    if checker:
        blc._apply_checker([o for o in bpy.context.scene.objects if o.type == "MESH"])
    if dark:
        blackout()
    blc._plate_lights()
    camera = blc._plate_camera(
        "game", blc._to_blender(blc.CAM_POS), blc._to_blender(blc.CAM_FORWARD),
        blc._to_blender(blc.CAM_UP), blc.CAM_FOV_V)
    width, px = frame_px(level)
    blc._label(camera, head, -0.96, 0.90, 0.030, TILE_W, TILE_H, tint)
    if sub:
        blc._label(camera, sub, -0.96, 0.84, 0.024, TILE_W, TILE_H, (0.72, 0.84, 1.0))
    blc._label(camera,
               f"camera du jeu (0 ; 14 ; 5), FOV 62 vertical, pont y = {level:.2f} — "
               f"cadre {width:.2f} m, {px:.1f} px/m en lateral",
               -0.96, -0.92, 0.022, TILE_W, TILE_H, (0.72, 0.84, 1.0))
    blc._render(path, TILE_W, TILE_H)


PLATE = [
    ("pylon_service", "1 — LE PYLONE RECONSTRUIT A 5,30 m  ·  quatre exemplaires, "
     "clip Service", (1.0, 0.88, 0.55),
     "2 612 triangles chacun (budget 3 200) contre 88 504 livres ; hauteur 5,30 m "
     "contre 24,00 ; 25 reperes CTRL sur 25"),
    ("pylon_maintenance", "2 — LE MEME, clip Maintenance  ·  les 28 lames "
     "thermiques s'ouvrent a 66 degres", (1.0, 0.88, 0.55),
     "c'est la SEULE difference visible entre les trois clips : elles sont donc "
     "les 336 triangles qu'il ne fallait pas couper"),
    ("intact", "3 — L'ARTERE, etat INTACT  ·  Actif / Actif / Intact / Intact",
     (0.62, 0.92, 1.0),
     "de gauche a droite : conduite droite (652 tri / 700), conduite coudee (648 / 700), "
     "flexible droit (320 / 350), flexible coude (344 / 350)"),
    ("endommage", "4 — ETAT ENDOMMAGE  ·  la vibration triple, les colliers "
     "s'ecartent", (1.0, 0.80, 0.45), ""),
    ("rupture", "5 — RUPTURE EN COURS  ·  image 88 sur 121", (1.0, 0.55, 0.45), ""),
    ("rompu", "6 — ROMPU  ·  ⚠️ l'etat que le joueur verra LE PLUS LONGTEMPS : "
     "une fois qu'il a tire, la piece reste comme ca", (1.0, 0.42, 0.42),
     "raccords arraches, brins exposes, noyaux eteints — la continuite "
     "Rupture -> Rompu est mesuree a 0,000000 m"),
]


def plate_states() -> None:
    staging = tempfile.mkdtemp(prefix="aegis-artery-")
    tiles = []
    try:
        for kind, head, tint, sub in PLATE:
            path = os.path.join(staging, f"{kind}.png")
            tile(path, kind, head, tint, sub)
            tiles.append((path, TILE_H))
        path = os.path.join(staging, "blackout.png")
        tile(path, "rompu",
             "7 — ROMPU, EMISSIF COUPE  ·  seul `AA_Emissive_Engine` est eteint : "
             "ce qui reste allume ici est mal range", (1.0, 0.55, 0.55),
             "la preuve du contrat de materiaux — 412 tri emissifs sur le pylone, "
             "88 par conduite, 96 par flexible", dark=True)
        tiles.append((path, TILE_H))
        path = os.path.join(staging, "checker.png")
        tile(path, "intact",
             "8 — DAMIER UV a la perspective du jeu  ·  projection en boite "
             "0,70 tuile/m (1,43 m par tuile)", (0.80, 1.0, 0.80),
             "les cases doivent rester carrees et de meme taille d'une piece a "
             "l'autre — TEXCOORD_0 compte sur 51 primitives sur 51",
             checker=True)
        tiles.append((path, TILE_H))
        os.makedirs(OUT, exist_ok=True)
        blc._compose(tiles, os.path.join(OUT, "BRIEF-0108-planche.png"), width=TILE_W)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


def plate_materials() -> None:
    """L'arbitrage des trois slots neufs : `AA_Greeble` contre `AA_Panel`.

    ⚠️ LE BRIEF PROPOSE `AA_Panel`, ET `AA_Panel` EST VIOLET. Ce n'est pas une
    opinion : `aegis_kit.PALETTES[null_choir]["panel"] = #452663`. La forge
    rend les deux au meme cadrage et laisse l'operateur regarder."""
    staging = tempfile.mkdtemp(prefix="aegis-artery-mat-")
    tiles = []
    try:
        for root, head, tint, sub in (
            (ALT, "OPTION DU BRIEF — `10 | Carbone technique` et "
                  "`10 | Gaine tressee` sur `AA_Panel`", (0.86, 0.60, 1.0),
             "AA_Panel est le VIOLET #452663 de la palette Unisson : c'est la "
             "gaine entiere du flexible qui le prend, 200 de ses 320 triangles"),
            (MODELS, "OPTION RETENUE — les deux sur `AA_Greeble`",
             (0.62, 0.92, 1.0),
             "AA_Greeble est le #141419 metallique du kit, soit exactement "
             "l'intention de la matiere d'origine (noir tresse, metallic 0,58)"),
        ):
            path = os.path.join(staging, os.path.basename(root) + ".png")
            tile(path, "intact", head, tint, sub, root=root)
            tiles.append((path, TILE_H))
        os.makedirs(OUT, exist_ok=True)
        blc._compose(tiles, os.path.join(OUT, "BRIEF-0108-arbitrage-materiaux.png"),
                     width=TILE_W)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--tile" in argv:
        i = argv.index("--tile")
        tile(os.path.abspath(argv[i + 2]), argv[i + 1], "essai", (1, 1, 1),
             dark="--dark" in argv, checker="--checker" in argv)
        return
    if not argv or "--states" in argv:
        plate_states()
    if "--materials" in argv:
        plate_materials()


main()
