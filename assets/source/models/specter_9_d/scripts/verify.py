"""Validate the editable source and GLB: size, fixed canopy, rigid motion and all four clips."""
import json
import hashlib
import math
import struct
import sys
from pathlib import Path

import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from paths import ASSETS, BLENDER, EXPORTS, REPORTS, VERSION

NAMES=['CTRL | Wing L','CTRL | Wing R','CTRL | Nozzle L','CTRL | Nozzle R']
config=json.loads((VERSION/'parameters.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(BLENDER/'spectre9_d.blend'))
scene=bpy.context.scene
asset=bpy.data.collections['S9D | Aircraft']
canopy=bpy.data.objects['CANOPY | fixed smoked glazing']
assert canopy.parent.name=='CTRL | Aircraft'
assert any(obj.modifiers for obj in asset.all_objects if obj.type=='MESH'),'Source modifiers were lost'
assert asset.asset_data,'Missing Asset Browser entry'
for img in bpy.data.images:
    if img.source=='FILE' and img.users:
        assert img.packed_file or img.packed_files, img.name
source={}
canopy_rest=None
state_dimensions={}
for frame in range(1,242):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    source[frame]={name:bpy.data.objects[name].matrix_world.copy() for name in NAMES}
    if canopy_rest is None:
        canopy_rest=canopy.matrix_world.copy()
    assert max(abs(canopy.matrix_world[i][j]-canopy_rest[i][j]) for i in range(4) for j in range(4))<1e-6
    for name in NAMES:
        assert all(abs(v-1)<1e-6 for v in bpy.data.objects[name].scale),name
    if frame in [1,76,151]:
        corners=[]
        graph=bpy.context.evaluated_depsgraph_get()
        for obj in asset.all_objects:
            if obj.type not in {'MESH','CURVE','FONT'}:
                continue
            evaluated=obj.evaluated_get(graph)
            data=evaluated.to_mesh()
            corners.extend(evaluated.matrix_world @ vertex.co for vertex in data.vertices)
            evaluated.to_mesh_clear()
        state_dimensions[frame]=[max(p[i] for p in corners)-min(p[i] for p in corners) for i in range(3)]
rest=state_dimensions[1]
assert abs(rest[0]-config['span_m'])<.08,rest
assert abs(rest[1]-config['length_m'])<.08,rest
assert abs(rest[2]-config['height_m'])<.08,rest
assert state_dimensions[1][0]>state_dimensions[76][0]>state_dimensions[151][0]
for tag in ['L','R']:
    name='CTRL | Nozzle '+tag
    travel=(source[151][name].translation-source[1][name].translation).length
    assert .5<travel<.7,travel
for tag in ['L','R']:
    name='CTRL | Wing '+tag
    angle=source[1][name].to_quaternion().rotation_difference(source[151][name].to_quaternion()).angle
    assert angle>math.radians(10),angle

raw=(EXPORTS/'spectre9_d.glb').read_bytes()
magic,version,length=struct.unpack_from('<4sII',raw)
assert magic==b'glTF' and version==2 and length==len(raw)
size,kind=struct.unpack_from('<II',raw,12)
doc=json.loads(raw[20:20+size])
expected={'Flight_Demo','Maneuver_to_Cruise','Cruise_to_Intercept','Intercept_to_Maneuver'}
assert {clip['name'] for clip in doc['animations']}==expected
for clip in doc['animations']:
    animated={doc['nodes'][c['target']['node']]['name'] for c in clip['channels']}
    assert animated==set(NAMES),(clip['name'],animated)
    assert all(c['target']['path'] in {'rotation','translation'} for c in clip['channels'])
assert len(doc['images'])>=6
assert all('bufferView' in image for image in doc['images'])
for mat in doc['materials']:
    if mat['name'] in {'MAT | white','MAT | blue','MAT | red','MAT | metal'}:
        assert 'normalTexture' in mat,mat['name']
        assert 'baseColorTexture' in mat['pbrMetallicRoughness'],mat['name']
        assert 'metallicRoughnessTexture' in mat['pbrMetallicRoughness'],mat['name']

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(EXPORTS/'spectre9_d.glb'))
scene=bpy.context.scene
for obj in scene.objects:
    assert obj.type not in {'CAMERA','LIGHT'}
    assert not obj.name.startswith(('STUDIO |','CAM |'))


def select_clip(name):
    for control in NAMES:
        data=bpy.data.objects[control].animation_data
        data.action=None
        for track in data.nla_tracks:
            track.mute=track.name!=name


# Blender imports NLA strips at frame 1 even when glTF starts at time zero.
select_clip('Flight_Demo')
error=0.0
for frame in range(1,242):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    for name in NAMES:
        actual=bpy.data.objects[name].matrix_world
        error=max(error,max(abs(actual[i][j]-source[frame][name][i][j]) for i in range(4) for j in range(4)))
assert error<1e-4,error
clip_checks={}
for name,a,b,duration in [('Maneuver_to_Cruise',1,76,46),('Cruise_to_Intercept',76,151,46),('Intercept_to_Maneuver',151,1,61)]:
    select_clip(name)
    worst=0.0
    for frame,reference in [(1,a),(duration,b)]:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for control in NAMES:
            actual=bpy.data.objects[control].matrix_world
            worst=max(worst,max(abs(actual[i][j]-source[reference][control][i][j]) for i in range(4) for j in range(4)))
    assert worst<1e-4,(name,worst)
    clip_checks[name]=worst
triangles=0
for obj in scene.objects:
    if obj.type=='MESH':
        obj.data.calc_loop_triangles()
        triangles+=len(obj.data.loop_triangles)
report={'glb_reimport':'OK','blender_version':bpy.app.version_string,
        'dimensions_xyz_m':{str(k):[round(v,3) for v in values] for k,values in state_dimensions.items()},
        'triangles':triangles,'mesh_objects':sum(o.type=='MESH' for o in scene.objects),
        'source_modifiers_preserved':True,'fixed_canopy':True,'rigid_motion_without_scale_keys':True,
        'embedded_pbr_images':len(doc['images']),'clips':sorted(expected),
        'flight_demo_frames_checked':241,'max_transform_error':error,'transition_endpoint_errors':clip_checks,
        'verified_file_sha256':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in
            [('blender/spectre9_d.blend',BLENDER/'spectre9_d.blend'),('exports/spectre9_d.glb',EXPORTS/'spectre9_d.glb')]},
        'limits':['No gameplay controller or collision meshes','No LODs','Artistic interpretation of hidden surfaces and mechanism']}
(REPORTS/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
print('VERIFICATION COMPLETE',flush=True)
