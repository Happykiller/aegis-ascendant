"""Check dimensions, non-deforming independent recoil, hierarchy and exported animation."""
import json
import math
import struct
from pathlib import Path

import bpy
from mathutils import Vector

OUT=Path(__file__).resolve().parent
names=['CTRL | Yaw 360','CTRL | Elevation','CTRL | L recoil','CTRL | R recoil',
       'MARKER | L muzzle','MARKER | R muzzle']
frames=[1,55,65,67,76,78,101,149,151,162,167,177,215,225,240]


def capture():
    result={}
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        result[frame]={name:bpy.data.objects[name].matrix_world.copy() for name in names}
    return result


bpy.ops.wm.open_mainfile(filepath=str(OUT/'tourelle_lourde.blend'))
source=capture()
scene=bpy.context.scene
scene.frame_set(1)
asset=bpy.data.collections['LC | TOURELLE LOURDE']
corners=[obj.matrix_world @ Vector(corner) for obj in asset.objects if obj.type=='MESH' for corner in obj.bound_box]
dimensions=[max(p[i] for p in corners)-min(p[i] for p in corners) for i in range(3)]
assert 9.9<dimensions[1]<10.3,dimensions
assert 4.1<dimensions[2]<4.3,dimensions
for tag in ['L','R']:
    recoil=bpy.data.objects['CTRL | '+tag+' recoil']
    assert recoil.parent.name=='CTRL | Elevation'
    assert bpy.data.objects['MARKER | '+tag+' muzzle'].parent==recoil
    for frame in frames:
        scene.frame_set(frame)
        assert all(abs(value-1)<1e-6 for value in recoil.scale),'Scaled recoil assembly'
    scene.frame_set(1)
    rest=recoil.location.y
    scene.frame_set(67 if tag=='L' else 78)
    assert abs(recoil.location.y-rest-.56)<1e-5
    scene.frame_set(151)
    assert abs(recoil.location.y-rest-.56)<1e-5
    scene.frame_set(240)
    assert abs(recoil.location.y-rest)<1e-5
# Right barrel has not fired during the first left recoil peak.
scene.frame_set(1)
right_rest=bpy.data.objects['CTRL | R recoil'].location.y
scene.frame_set(67)
assert abs(bpy.data.objects['CTRL | R recoil'].location.y-right_rest)<1e-5

with (OUT/'tourelle_lourde.glb').open('rb') as stream:
    stream.read(12)
    length,kind=struct.unpack('<II',stream.read(8))
    document=json.loads(stream.read(length))
assert document.get('animations')
assert len(document.get('images',[]))>=3
assert all('bufferView' in image for image in document['images'])
for mat in document['materials']:
    if mat['name'] in ['LC | dark weathered armor','LC | warm graphite panels']:
        assert 'normalTexture' in mat
        assert 'metallicRoughnessTexture' in mat['pbrMetallicRoughness']
        assert all(0<=x<=1 for x in mat['pbrMetallicRoughness'].get('baseColorFactor',[1]*4))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(OUT/'tourelle_lourde.glb'))
exported=capture()
error=max(abs(source[frame][name][row][column]-exported[frame][name][row][column])
          for frame in frames for name in names for row in range(4) for column in range(4))
assert error<1e-4,error
triangles=0
for obj in bpy.context.scene.objects:
    assert obj.type not in {'LIGHT','CAMERA'}
    if obj.type=='MESH':
        obj.data.calc_loop_triangles()
        triangles+=len(obj.data.loop_triangles)
report={'glb_reimport':'OK','dimensions_xyz_m':[round(value,3) for value in dimensions],
        'triangles':triangles,'recoil_travel_m':.56,'independent_alternating_recoil':True,
        'synchronized_salvo':True,'no_recoil_scaling':True,'embedded_pbr_images':len(document['images']),
        'animation_clips':len(document['animations']),'max_transform_error':error}
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
