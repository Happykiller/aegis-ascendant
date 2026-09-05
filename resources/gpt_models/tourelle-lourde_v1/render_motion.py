"""Render an eight-second animation at 10 fps, preserving the short recoil impulses."""
from pathlib import Path

import bpy

OUT=Path(__file__).resolve().parent
(OUT/'motion_frames').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'tourelle_lourde.blend'))
scene=bpy.context.scene
scene.camera=bpy.data.objects['CAM | reference three-quarter']
scene.camera.data.ortho_scale=14.0
scene.cycles.samples=8
scene.render.resolution_x=720
scene.render.resolution_y=540
scene.render.resolution_percentage=100
for index,frame in enumerate(range(1,241,3)):
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/'motion_frames'/f'{index:03}.png')
    bpy.ops.render.render(write_still=True)
print('MOTION RENDER COMPLETE',flush=True)
