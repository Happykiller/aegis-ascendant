#!/usr/bin/env python3
"""Rend une coque .glb en planche 4 vues, pour qu'on la REGARDE avant de l'intégrer.

    blender45 -b -P tools/render-hull.py -- assets/imported/models/ships/needle_scout.glb
    blender45 -b -P tools/render-hull.py -- .../specter_9.glb --out /tmp/specter.png

Pendant du tools/preview-svg.py, côté 3D. Le 2D avait son garde-fou depuis
ADR-0006 (« un livrable de la forge n'est pas un asset validé tant qu'il n'a pas
été rendu et regardé ») ; la 3D n'en avait aucun. On ne pouvait juger une coque
qu'en jeu, où elle fait 0,65 m et passe en deux secondes — autant dire pas.

BRIEF-0026 exigeait déjà de juger « depuis un angle qui reproduit la caméra de
jeu », et notait que c'est l'absence de cette vérification qui a produit le
défaut du Specter-9 (émissif cyan dépensé sur des faces invisibles d'en haut).
Ce brief est resté en brouillon. Ce script est ce qui lui manquait.

⚠️ La vue « game » n'est PAS reconstituée à l'estime. Elle vient de la base réelle
de scenes/gameplay/graybox.tscn:45 — dont l'axe de visée est à 70° AU-DESSUS du
plan (20° écartés de la verticale), pas les « ~20° au-dessus du plan » qu'annonce
BRIEF-0026. Un rendu à 20° d'élévation montrerait la coque de profil et validerait
des surfaces que le joueur ne voit jamais.
"""

from __future__ import annotations

import math
import os
import sys

import bpy
import numpy as np
from mathutils import Euler, Vector

## Le fond spatial du jeu (#070A12) : juger une coque sur du gris n'a aucun sens.
BACKDROP = (0.0027, 0.0039, 0.0070, 1.0)  # sRGB (7,10,18) -> linéaire
TILE = 640
SAMPLES = 64
OUT_DEFAULT = "/tmp/hull-preview.png"

## L'inclinaison de la caméra de jeu, lue sur graybox.tscn:45 : l'axe de visée
## descend de 70° sous l'horizontale. C'est un shmup vertical — on voit les
## coques quasiment de dessus, très légèrement de trois quarts arrière.
GAME_PITCH_DEG = 20.0  # écart à la verticale
GAME_FOV_DEG = 62.0

## (nom, pitch depuis la verticale, azimut autour de Z, fov)
VIEWS = (
    ("game", GAME_PITCH_DEG, 0.0, GAME_FOV_DEG),
    ("dessus", 0.0, 0.0, 45.0),
    ("profil", 90.0, 90.0, 45.0),
    ("trois-quarts", 55.0, 40.0, 45.0),
)


def _args() -> tuple[str, str]:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if not argv:
        raise SystemExit(__doc__)
    src = argv[0]
    out = OUT_DEFAULT
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    if not os.path.isfile(src):
        raise SystemExit("introuvable : %s" % src)
    return src, out


def _reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    world = bpy.data.worlds.new("preview")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = BACKDROP
    bpy.context.scene.world = world


def _bounds() -> tuple[np.ndarray, float]:
    """Centre et demi-diagonale des maillages importés, en coordonnées monde."""
    points = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            points.append(obj.matrix_world @ Vector(corner))
    if not points:
        raise SystemExit("le .glb ne contient aucun maillage")
    array = np.array([[p.x, p.y, p.z] for p in points])
    low, high = array.min(axis=0), array.max(axis=0)
    return (low + high) * 0.5, float(np.linalg.norm(high - low)) * 0.5


def _lights(radius: float) -> None:
    """Trois points. ADR-0008 prévient que sans éclairage travaillé « les meshes
    paraîtront pires que les sprites » — une planche mal éclairée ferait rejeter
    une coque correcte."""
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
        # Orienter vers l'origine : la coque y est recentrée avant l'appel.
        direction = -light.location.normalized()
        light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(light)


def _camera(pitch_deg: float, azimuth_deg: float, fov_deg: float, radius: float):
    data = bpy.data.cameras.new("cam")
    data.lens_unit = "FOV"
    data.angle = math.radians(fov_deg)
    camera = bpy.data.objects.new("cam", data)
    bpy.context.collection.objects.link(camera)

    # Euler (pitch autour de X, puis azimut autour de Z). À pitch nul la caméra
    # regarde droit vers le bas et le nez (+Y en repère Blender après import
    # glTF) pointe vers le haut de l'image : c'est la lecture du jeu.
    pitch, azimuth = math.radians(pitch_deg), math.radians(azimuth_deg)
    rotation = Euler((pitch, 0.0, azimuth), "XYZ")
    camera.rotation_euler = rotation
    # La direction se dérive de l'Euler, PAS de camera.matrix_world : celle-ci
    # n'est réévaluée qu'au prochain passage du depsgraph, donc elle vaut encore
    # l'identité ici. S'y fier plaçait les quatre caméras au même point, et deux
    # vues sur quatre sortaient noires (la coque hors champ).
    forward = rotation.to_matrix() @ Vector((0.0, 0.0, -1.0))
    distance = radius / math.tan(math.radians(fov_deg) * 0.5) * 1.15
    camera.location = -forward * distance
    bpy.context.scene.camera = camera
    return camera


def _render(path: str) -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    # CPU explicite : ce script tourne en WSL sans GPU fiable (ADR-0002).
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.resolution_x = TILE
    scene.render.resolution_y = TILE
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def _compose(tiles: list[str], out: str) -> None:
    """Planche 2×2. Pas de PIL dans le Python de Blender — numpy + bpy.data.images."""
    sheet = np.zeros((TILE * 2, TILE * 2, 4), dtype=np.float32)
    for index, path in enumerate(tiles):
        image = bpy.data.images.load(path)
        buffer = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(buffer)
        tile = buffer.reshape(TILE, TILE, 4)
        row, column = index // 2, index % 2
        # Les images Blender sont stockées de bas en haut : la ligne 0 est en bas.
        # On empile donc la première vue en HAUT de la planche.
        top = (1 - row) * TILE
        sheet[top : top + TILE, column * TILE : (column + 1) * TILE] = tile
        bpy.data.images.remove(image)

    result = bpy.data.images.new("sheet", width=TILE * 2, height=TILE * 2)
    result.pixels.foreach_set(sheet.reshape(-1))
    result.filepath_raw = out
    result.file_format = "PNG"
    result.save()


def main() -> None:
    src, out = _args()
    _reset()
    bpy.ops.import_scene.gltf(filepath=src)

    center, radius = _bounds()
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.location = (obj.location.x - center[0],
                            obj.location.y - center[1],
                            obj.location.z - center[2])
    _lights(radius)

    tiles = []
    for name, pitch, azimuth, fov in VIEWS:
        _camera(pitch, azimuth, fov, radius)
        path = "/tmp/_hull_%s.png" % name
        _render(path)
        tiles.append(path)
        print("  vue %s" % name)

    _compose(tiles, out)
    print("\n  %s   (rayon %.3f m)" % (src, radius))
    print("  planche : %s | %s / %s | %s"
          % (VIEWS[0][0], VIEWS[1][0], VIEWS[2][0], VIEWS[3][0]))
    print("\n-> %s   (l'OUVRIR : une coque non regardée n'est pas une coque validée)" % out)


if __name__ == "__main__":
    main()
