"""Render both viewing angles, then encode with ffmpeg at 5 fps input / 30 fps output."""
from pathlib import Path

import bpy

OUT=Path(__file__).resolve().parent
(OUT/'motion_frames').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'spectre9_v3.blend'))
scene=bpy.context.scene
scene.cycles.samples=8
scene.render.resolution_x=720
scene.render.resolution_y=540
scene.render.resolution_percentage=100
index=0
for camera in ['Camera | top orthographic','Camera | rear three-quarter']:
    scene.camera=bpy.data.objects[camera]
    for frame in range(1,181,6):
        scene.frame_set(frame)
        scene.render.filepath=str(OUT/'motion_frames'/f'{index:03}.png')
        bpy.ops.render.render(write_still=True)
        index+=1
