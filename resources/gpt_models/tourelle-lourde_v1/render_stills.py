"""Render static checks from the saved deliverable."""
from pathlib import Path
import bpy

OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'tourelle_lourde.blend'))
scene=bpy.context.scene
for camera,frame,name in [('CAM | reference three-quarter',1,'hero'),('CAM | top',1,'top'),
                          ('CAM | front',1,'front'),('CAM | side',1,'side'),
                          ('CAM | reference three-quarter',151,'recoil')]:
    scene.camera=bpy.data.objects[camera]
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/f'tourelle_lourde_{name}.png')
    bpy.ops.render.render(write_still=True)
print('STILLS COMPLETE',flush=True)
