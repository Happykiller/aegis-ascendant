"""Render the saved editable model. Arguments after --: --quick, --motion, --views hero top."""
import argparse
import sys
from pathlib import Path
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from paths import BLENDER, PREVIEWS, WORK
parser=argparse.ArgumentParser()
parser.add_argument('--quick',action='store_true')
parser.add_argument('--motion',action='store_true')
parser.add_argument('--views',nargs='+')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
bpy.ops.wm.open_mainfile(filepath=str(BLENDER/'spectre9_d.blend'))
scene=bpy.context.scene
# Orthographic underside inspection needs illumination from below the aircraft.
light_data=bpy.data.lights.new('STUDIO | underside inspection','AREA')
light_data.energy=1900
light_data.shape='DISK'
light_data.size=9
underlight=bpy.data.objects.new(light_data.name,light_data)
scene.collection.objects.link(underlight)
underlight.location=(0,0,-8)
underlight.rotation_euler.x=3.141592653589793
underlight.hide_render=True
if args.motion:
    directory=WORK/'motion_frames'
    directory.mkdir(exist_ok=True)
    scene.camera=bpy.data.objects['CAM | hero']
    scene.render.resolution_x=900
    scene.render.resolution_y=675
    scene.cycles.samples=12
    jobs=[('hero',frame,str(directory/f'{index:03}.png')) for index,frame in enumerate(range(1,241,3))]
else:
    views=args.views or ['hero','rear','top','bottom','left','front','back','canopy','cruise','intercept']
    jobs=[('hero' if view in ['cruise','intercept'] else view,
           76 if view=='cruise' else 151 if view=='intercept' else 1,
           str(PREVIEWS/f'spectre9_d_{view}.png')) for view in views]
if args.quick:
    scene.render.resolution_percentage=60
    scene.cycles.samples=12
for camera,frame,path in jobs:
    underlight.hide_render=camera!='bottom'
    scene.camera=bpy.data.objects['CAM | '+camera]
    scene.frame_set(frame)
    bpy.data.objects['STUDIO | floor'].hide_render=camera in {'top','bottom','left','front','back'}
    scene.render.filepath=path
    bpy.ops.render.render(write_still=True)
print('RENDER COMPLETE',flush=True)
