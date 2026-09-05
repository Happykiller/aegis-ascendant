"""Compare editable-driver evaluation with the baked GLB, including pylon alignment."""
import json
import math
import struct
from pathlib import Path

import bpy

OUT=Path(__file__).resolve().parent
names=['CTRL | '+side+' '+part for side in ['L','R']
       for part in ['wing sweep','pylon alignment','nozzle petal 00','nozzle petal 10']]
names += ['MARKER | '+side+' '+part for side in ['L','R'] for part in ['wingtip','nozzle lip']]


def capture():
    states={}
    for frame in [1,54,84,138,168]:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        states[frame]={name:bpy.data.objects[name].matrix_world.copy() for name in names}
    return states


bpy.ops.wm.open_mainfile(filepath=str(OUT/'spectre9_v3.blend'))
source=capture()
driver_count=sum(len(obj.animation_data.drivers) for obj in bpy.context.scene.objects if obj.animation_data)
assert driver_count==44,driver_count
span_low=abs(source[1]['MARKER | R wingtip'].translation.x-source[1]['MARKER | L wingtip'].translation.x)
span_high=abs(source[84]['MARKER | R wingtip'].translation.x-source[84]['MARKER | L wingtip'].translation.x)
assert span_high<span_low*.8,(span_low,span_high)
radii={}
for side,sign in [('L',-1),('R',1)]:
    for frame in [1,84]:
        point=source[frame]['MARKER | '+side+' nozzle lip'].translation
        radii[f'{side}_{frame}']=math.hypot(point.x-sign*1.24,point.z-.08)
    assert radii[f'{side}_84']<radii[f'{side}_1']*.7,radii
    pylon_low=source[1]['CTRL | '+side+' pylon alignment'].to_quaternion()
    pylon_high=source[84]['CTRL | '+side+' pylon alignment'].to_quaternion()
    assert pylon_low.rotation_difference(pylon_high).angle<.001
    sweep=source[1]['CTRL | '+side+' wing sweep'].to_quaternion().rotation_difference(
        source[84]['CTRL | '+side+' wing sweep'].to_quaternion()).angle
    assert abs(math.degrees(sweep)-30)<.01

# Test the user's manual slider separately from its demonstration keyframes.
controller=bpy.data.objects['CTRL | Flight configuration']
controller.animation_data_clear()
for speed in [0,.5,1]:
    controller['speed']=speed
    controller.update_tag(refresh={'OBJECT'})
    bpy.context.view_layer.update()
    angle=bpy.data.objects['CTRL | R wing sweep'].rotation_euler.z
    assert abs(angle-math.radians(30)*speed)<.00001,(speed,angle)

with (OUT/'spectre9_v3.glb').open('rb') as stream:
    stream.read(12)
    length,kind=struct.unpack('<II',stream.read(8))
    document=json.loads(stream.read(length))
assert document.get('animations')
assert len(document.get('images',[]))>=3
assert all('bufferView' in image for image in document['images'])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(OUT/'spectre9_v3.glb'))
exported=capture()
error=max(abs(source[frame][name][row][col]-exported[frame][name][row][col])
          for frame in source for name in names for row in range(4) for col in range(4))
assert error<.0001,error
report={'glb_reimport':'OK','blender_version':bpy.app.version_string,'editable_speed_drivers':driver_count,
        'sweep_degrees':30,'wingtip_span_low_m':round(span_low,3),'wingtip_span_high_m':round(span_high,3),
        'nozzle_exit_diameter_low_m':round(2*radii['R_1'],3),
        'nozzle_exit_diameter_high_m':round(2*radii['R_84'],3),
        'pylons_remain_forward':True,'manual_speed_slider':'OK',
        'exported_animation_clips':len(document['animations']),
        'max_transform_error':error}
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
