"""Les planches de controle de la poupe (BRIEF-0105) — A LA CAMERA DU JEU.

    blender-aegis -t 1 -b -noaudio --python assets/source/models/stern/render_stern_plates.py -- --states
    blender-aegis -t 1 -b -noaudio --python assets/source/models/stern/render_stern_plates.py -- --texture

⚠️ UN ASSET NON RENDU ET NON REGARDE N'EST PAS VALIDE (`ADR-0006`). Et un rendu
studio ne prouve rien : ce qui compte est le cadrage du jeu, la lumiere du jeu et
la distance du jeu. Tout le rig vient donc de `build_long_cortege.py` — camera
(0 ; 14 ; 5), FOV 62 vertical, trois directionnelles, aucune ombre portee — et
n'est PAS recopie : il est importe.

⚠️ ET LE PONT DE POUPE N'EST PAS LE COULOIR. Mesure, pas souvenir : le corridor
se joue sur un pont a y = -4,30, ou le cadre fait 41,60 m et 46,2 px/m. La poupe
se joue a y = -11,85 : 7,55 m PLUS BAS, donc plus loin, donc **58,77 m de cadre et
32,7 px/m**. Le brief raisonnait sur 45,8 px/m ; le vrai chiffre est un tiers plus
faible, et il rend la coupe encore moins discutable qu'annonce.

Le montage suit `resources/levels/long_cortege_stern.tres`, LU et non recopie :
une cote de jeu qui bouge doit invalider la planche, pas la laisser mentir.
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
import build_long_cortege as blc  # noqa: E402  (le rig de planche du niveau)

MODELS = os.path.join(REPO, "assets", "imported", "models", "backgrounds")
TEXTURED = os.path.join(REPO, "build", "stern_textured")
OUT = os.path.join(REPO, "docs", "forge", "output")

TILE_W = 1920
TILE_H = 1080

#: 30 images/s dans toutes les sources tierces ; les clips demarrent a l'image 1.
FPS = 30


# --------------------------------------------------------------------------
# Les cotes du jeu, LUES dans la Resource
# --------------------------------------------------------------------------

def tuning() -> dict:
    """Relit `long_cortege_stern.tres`. On ne le modifie pas : on s'y plie."""
    path = os.path.join(REPO, "resources", "levels", "long_cortege_stern.tres")
    text = open(path, encoding="utf-8").read()
    out: dict = {}
    for key, raw in re.findall(r"^(\w+) = (.+)$", text, re.M):
        raw = raw.strip()
        vec = re.match(r"Vector3\(([^)]*)\)", raw)
        if vec:
            out[key] = Vector([float(v) for v in vec.group(1).split(",")])
        else:
            try:
                out[key] = float(raw)
            except ValueError:
                pass
    # Les cotes d'encombrement vivent dans le script de la Resource, pas dans
    # l'instance : elles n'y sont ecrites que si elles ont ete surchargees.
    out.setdefault("anchor_size_y", 1.20)
    return out


T = tuning()


def scale_of(central: bool) -> float:
    return T["asset_scale"] * (T["central_scale"] if central else 1.0)


def slot_x(side: float) -> float:
    return side * T["engine_spacing"]


# --------------------------------------------------------------------------
# Import et pose
# --------------------------------------------------------------------------

def place(path: str, position: Vector, k: float, yaw: float = 0.0) -> list:
    """Importe un `.glb` sous un porteur pose a la position DE JEU, a l'echelle."""
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


def clip_action(obj: bpy.types.Object, clip: str):
    ad = obj.animation_data
    if ad is None:
        return None
    for track in ad.nla_tracks:
        for strip in track.strips:
            if strip.action and strip.action.name.split(".")[0] == clip:
                return strip.action
    if ad.action and ad.action.name.split(".")[0] == clip:
        return ad.action
    return None


def pose(objects: list, clip: str, frame: int, store: dict) -> None:
    """Fige `objects` sur l'image `frame` du clip `clip`.

    ⚠️ ON RELEVE LA POSE, ON NE LA LAISSE PAS ANIMEE. Trois groupes a trois
    instants differents du meme clip ne tiennent pas dans une seule image de
    scene : on evalue, on note, et on gele a la fin.
    """
    for obj in objects:
        act = clip_action(obj, clip)
        if act is None:
            continue
        obj.animation_data.action = act
        for track in obj.animation_data.nla_tracks:
            track.mute = True
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    for obj in objects:
        if obj.animation_data is None:
            continue
        store[obj.name] = (
            Vector(obj.location),
            obj.rotation_quaternion.copy(),
            Vector(obj.scale),
        )


def freeze(store: dict) -> None:
    for name, (loc, quat, scl) in store.items():
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        obj.animation_data_clear()
        obj.location = loc
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = quat
        obj.scale = scl
    bpy.context.view_layer.update()


# --------------------------------------------------------------------------
# Le montage de la poupe
# --------------------------------------------------------------------------

STATES = {
    # nom          moteur                    berceau                 ancrage      bras
    "intact": (("Fonctionnement", 12), ("Intact", 12), ("Intact", 12), ("Serre", 12)),
    "endommage": (("Endommage", 34), ("Sous_contrainte", 34), ("Endommage", 20),
                  ("Serre", 20)),
    "arrachement": (("Detachement", 98), ("Liberation", 98), ("Rompu", 20),
                    ("Rupture", 88)),
    "vide": (None, ("Berceau_vide", 30), ("Rompu", 40), ("Rompu", 40)),
}


def build_stern(state: str, textured: bool) -> None:
    """Trois groupes, a la place exacte que leur donne `cortege_engine.gd`."""
    suffix = "_textured" if textured else ""
    root = TEXTURED if textured else MODELS
    engine_clip, cradle_clip, anchor_clip, arm_clip = STATES[state]
    store: dict = {}
    for side in (-1.0, 0.0, 1.0):
        central = side == 0.0
        k = scale_of(central)
        g = Vector((slot_x(side), T["deck_y"], 0.0))

        cradle = place(os.path.join(root, f"stern_cradle{suffix}.glb"), g, k)
        pose(cradle, cradle_clip[0], cradle_clip[1], store)

        if engine_clip is not None:
            seat = g + Vector((0.0, T["engine_seat"].y * k, T["engine_seat"].z * k))
            engine = place(os.path.join(root, f"stern_engine{suffix}.glb"), seat, k)
            pose(engine, engine_clip[0], engine_clip[1], store)

        total = int(T["central_anchors"] if central else T["lateral_anchors"])
        ay = (T["socket_y"] + T["anchor_size_y"] * 0.5) * k
        for i in range(total):
            if i < 2:
                cote = -1.0 if i == 0 else 1.0
                local = Vector((cote * T["socket_x"] * k, ay, T["socket_z_front"] * k))
            elif total <= 3:
                local = Vector((0.0, ay, T["socket_z_rear"] * k))
            else:
                cote = -1.0 if i == 2 else 1.0
                local = Vector((cote * T["socket_x"] * k, ay, T["socket_z_rear"] * k))
            anchor = place(os.path.join(root, f"stern_anchor{suffix}.glb"), g + local, k)
            pose(anchor, anchor_clip[0], anchor_clip[1], store)

        # ⚠️ LES BRAS SONT PLACES PAR LA FORGE, PAS PAR LE JEU. `cortege_engine.gd`
        # ne les monte pas encore (c'est le LOT 7) : on les pose aux quatre coins
        # du berceau, machoire tournee vers le fut, ce que decrit leur planche.
        for cote in (-1.0, 1.0):
            for prof in (T["socket_z_front"], T["socket_z_rear"]):
                name = "stern_arm_mirror" if cote > 0.0 else "stern_arm"
                local = Vector((cote * (T["socket_x"] + 1.15) * k,
                                T["socket_y"] * k * 0.55, prof * k))
                yaw = -math.pi * 0.5 if cote > 0.0 else math.pi * 0.5
                arm = place(os.path.join(root, f"{name}{suffix}.glb"), g + local, k, yaw)
                pose(arm, arm_clip[0], arm_clip[1], store)
    freeze(store)


def deck() -> None:
    """Le pont de poupe, exactement la boite grise de `cortege_stern.gd`.

    Il n'est pas un livrable (c'est le LOT 6) : sans lui, les trois groupes
    flottent dans le vide et la planche ment sur ce que le joueur verra.
    """
    half = T["engine_spacing"] + 11.19 * scale_of(False) * 0.5
    mesh = bpy.data.meshes.new("SternDeck")
    bm_size = Vector((half * 2.0 + 4.0, 1.60, 14.0 * scale_of(False) * 1.6))
    verts = []
    for sx in (-0.5, 0.5):
        for sy in (-0.5, 0.5):
            for sz in (-0.5, 0.5):
                verts.append((sx * bm_size.x, sz * bm_size.z, sy * bm_size.y))
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
             (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("SternDeck", mesh)
    obj.location = blc._to_blender(Vector((0.0, T["deck_y"] - 0.80, 0.0)))
    mat = bpy.data.materials.new("SternDeckGrey")
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

    ⚠️ C'EST LA PREUVE VISUELLE DU CONTRAT DE MATERIAUX, pas un effet. Si une
    veine reste allumee sur cette image, c'est qu'elle a ete peinte dans un autre
    slot — le defaut que rien ne signale (ni erreur, ni test rouge) et qui coute
    l'image finale du niveau.
    """
    for mat in bpy.data.materials:
        if not mat.name.split(".")[0].startswith("AA_Emissive"):
            continue
        if not mat.use_nodes:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                node.inputs["Emission Strength"].default_value = 0.0


def frame_metrics() -> dict:
    return blc._frame_coverage(T["deck_y"])


def tile(path: str, state: str, textured: bool, dark: bool = False,
         checker: bool = False) -> None:
    blc._plate_reset()
    bpy.context.scene.render.fps = FPS
    deck()
    build_stern(state, textured)
    if checker:
        blc._apply_checker([o for o in bpy.context.scene.objects if o.type == "MESH"])
    if dark:
        blackout()
    blc._plate_lights()
    camera = blc._plate_camera(
        "game", blc._to_blender(blc.CAM_POS), blc._to_blender(blc.CAM_FORWARD),
        blc._to_blender(blc.CAM_UP), blc.CAM_FOV_V)
    metrics = frame_metrics()
    px = TILE_W / metrics["frame_width"]
    titles = {
        "intact": "1 — MOTEUR INTACT  ·  Fonctionnement / Intact / Intact / Serre",
        "endommage": "2 — MOTEUR ENDOMMAGE  ·  Endommage / Sous_contrainte / "
                     "Endommage / Serre",
        "arrachement": "3 — ARRACHEMENT EN COURS  ·  Detachement / Liberation / "
                       "Rompu / Rupture",
        "vide": "4 — BERCEAU VIDE  ·  aucun moteur / Berceau_vide / Rompu / Rompu",
    }
    head = titles[state]
    tint = (1.0, 0.88, 0.55)
    if dark:
        head = ("5 — BERCEAU VIDE, EMISSIF COUPE  ·  seul `AA_Emissive_Engine` est "
                "eteint : ce qui reste allume ici est mal range")
        tint = (1.0, 0.55, 0.55)
    if checker:
        head = (f"6 — DAMIER UV a la perspective du jeu  ·  projection en boite "
                f"0,70 tuile/m (1,43 m par tuile)")
    blc._label(camera, head, -0.96, 0.90, 0.030, TILE_W, TILE_H, tint)
    blc._label(camera,
               f"camera du jeu (0 ; 14 ; 5), FOV 62 vertical, pont de poupe "
               f"y = {T['deck_y']:.2f} — cadre {metrics['frame_width']:.2f} m, "
               f"{px:.1f} px/m en lateral ({px * 0.940:.1f} en profondeur)",
               -0.96, 0.84, 0.024, TILE_W, TILE_H)
    blc._label(camera,
               f"asset_scale {T['asset_scale']:.3f} (central x{T['central_scale']:.2f}) ; "
               f"entraxe {T['engine_spacing']:.2f} m ; assise moteur "
               f"({T['engine_seat'].x:.0f} ; {T['engine_seat'].y:.2f} ; "
               f"{T['engine_seat'].z:.2f}) — lus dans long_cortege_stern.tres",
               -0.96, 0.78, 0.022, TILE_W, TILE_H, (0.72, 0.84, 1.0))
    blc._render(path, TILE_W, TILE_H)


def plate_states() -> None:
    staging = tempfile.mkdtemp(prefix="aegis-stern-")
    tiles = []
    try:
        for state in ("intact", "endommage", "arrachement", "vide"):
            path = os.path.join(staging, f"{state}.png")
            tile(path, state, textured=False)
            tiles.append((path, TILE_H))
        path = os.path.join(staging, "blackout.png")
        tile(path, "vide", textured=False, dark=True)
        tiles.append((path, TILE_H))
        path = os.path.join(staging, "checker.png")
        tile(path, "intact", textured=False, checker=True)
        tiles.append((path, TILE_H))
        os.makedirs(OUT, exist_ok=True)
        blc._compose(tiles, os.path.join(OUT, "BRIEF-0105-etats.png"), width=TILE_W)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


def plate_texture() -> None:
    """L'arbitrage de D4 : le meme cadrage, avec et sans les onze atlas."""
    staging = tempfile.mkdtemp(prefix="aegis-stern-tex-")
    tiles = []
    try:
        for textured in (True, False):
            path = os.path.join(staging, f"{'A' if textured else 'B'}.png")
            blc._plate_reset()
            bpy.context.scene.render.fps = FPS
            deck()
            build_stern("intact", textured)
            blc._plate_lights()
            camera = blc._plate_camera(
                "game", blc._to_blender(blc.CAM_POS), blc._to_blender(blc.CAM_FORWARD),
                blc._to_blender(blc.CAM_UP), blc.CAM_FOV_V)
            metrics = frame_metrics()
            px = TILE_W / metrics["frame_width"]
            size = sum(
                os.path.getsize(os.path.join(TEXTURED if textured else MODELS, f))
                for f in os.listdir(TEXTURED if textured else MODELS)
                if f.startswith("stern_") and f.endswith(".glb"))
            if textured:
                head = ("OPTION A — LES ONZE ATLAS DE L'AUTEUR, tels que livres "
                        "(albedo / normale / rugosite-metal / emission)")
                tint = (1.0, 0.72, 0.45)
            else:
                head = ("OPTION B — PBR PAR FACTEURS, comme tout le reste du niveau "
                        "(AA_Hull / AA_Greeble / AA_Emissive_Engine, zero image)")
                tint = (0.62, 0.92, 1.0)
            blc._label(camera, head, -0.96, 0.90, 0.030, TILE_W, TILE_H, tint)
            blc._label(camera,
                       f"cout Git LFS des cinq binaires : {size / 1e6:.1f} Mo",
                       -0.96, 0.84, 0.026, TILE_W, TILE_H)
            blc._label(camera,
                       f"meme cadrage, meme lumiere, meme pose — camera du jeu, "
                       f"{px:.1f} px/m en lateral",
                       -0.96, -0.92, 0.022, TILE_W, TILE_H, (0.72, 0.84, 1.0))
            blc._render(path, TILE_W, TILE_H)
            tiles.append((path, TILE_H))
        os.makedirs(OUT, exist_ok=True)
        blc._compose(tiles, os.path.join(OUT, "BRIEF-0105-arbitrage-texture.png"),
                     width=TILE_W)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    # `--tile <etat> <chemin>` : une seule vignette, pour iterer sans payer six
    # rendus Cycles a chaque essai de reduction.
    if "--tile" in argv:
        i = argv.index("--tile")
        tile(os.path.abspath(argv[i + 2]), argv[i + 1], textured=False,
             dark="--dark" in argv, checker="--checker" in argv)
        return
    if not argv or "--states" in argv:
        plate_states()
    if "--texture" in argv:
        plate_texture()


main()
