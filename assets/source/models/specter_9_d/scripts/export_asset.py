"""Export the saved source without overwriting it; bake portable reusable clips in memory."""
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from paths import BLENDER, EXPORTS, REPORTS

CONTROL_NAMES=['CTRL | Wing L','CTRL | Wing R','CTRL | Nozzle L','CTRL | Nozzle R']
bpy.ops.wm.open_mainfile(filepath=str(BLENDER/'spectre9_d.blend'))
scene=bpy.context.scene
root=bpy.data.objects['CTRL | Aircraft']
controls=[bpy.data.objects[name] for name in CONTROL_NAMES]
# Sample the actual source animation, including changes made by the receiving artist.
sampled={}
for frame in range(scene.frame_start,scene.frame_end+1):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    sampled[frame]={obj.name:{'location':list(obj.location),'rotation':list(obj.rotation_euler)} for obj in controls}
markers={marker.name:marker.frame for marker in scene.timeline_markers}
start=scene.frame_start
cruise=markers.get('CRUISE',76)
intercept=markers.get('INTERCEPT',151)
scene.frame_set(start)
bpy.context.view_layer.update()
root.animation_data_clear()
for obj in controls:
    obj.animation_data_clear()


def transition(a,b,frames):
    result={}
    for frame in range(1,frames+1):
        t=(frame-1)/(frames-1)
        t=t*t*(3-2*t)
        result[frame]={}
        for name in CONTROL_NAMES:
            result[frame][name]={channel:[x*(1-t)+y*t for x,y in zip(a[name][channel],b[name][channel])]
                                  for channel in ['location','rotation']}
    return result


clips={
    'Flight_Demo':{frame-start+1:pose for frame,pose in sampled.items()},
    'Maneuver_to_Cruise':transition(sampled[start],sampled[cruise],46),
    'Cruise_to_Intercept':transition(sampled[cruise],sampled[intercept],46),
    'Intercept_to_Maneuver':transition(sampled[intercept],sampled[start],61),
}
for obj in controls:
    for clip,poses in clips.items():
        obj.animation_data_create()
        obj.animation_data.action=None
        for frame,pose in poses.items():
            obj.location=pose[obj.name]['location']
            obj.rotation_euler=pose[obj.name]['rotation']
            obj.keyframe_insert(data_path='location',frame=frame)
            obj.keyframe_insert(data_path='rotation_euler',frame=frame)
        action=obj.animation_data.action
        action.name=clip+' | '+obj.name
        track=obj.animation_data.nla_tracks.new()
        track.name=clip
        strip=track.strips.new(clip,1,action)
        strip.extrapolation='NOTHING'
        track.mute=True
        obj.animation_data.action=None
    obj.location=sampled[start][obj.name]['location']
    obj.rotation_euler=sampled[start][obj.name]['rotation']
scene.frame_set(1)
# Convert curves/text only in this unsaved export session. Source modifiers remain intact.
asset=bpy.data.collections['S9D | Aircraft']
bpy.ops.object.select_all(action='DESELECT')
curves=[obj for obj in asset.all_objects if obj.type in {'CURVE','FONT'}]
for obj in curves:
    obj.select_set(True)
if curves:
    bpy.context.view_layer.objects.active=curves[0]
    bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for obj in asset.all_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(EXPORTS/'spectre9_d.glb'),export_format='GLB',use_selection=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',
    export_force_sampling=True,export_frame_range=False,export_anim_slide_to_zero=True,export_extras=True,
    export_cameras=False,export_lights=False)
report={'source_blend_preserved':True,'clip_names':list(clips),'sampled_source_frames':len(sampled),
        'mechanism':'Rigid wing sweep and nozzle translation; source drivers baked to node transforms.'}
(REPORTS/'export.json').write_text(json.dumps(report,indent=2)+'\n')
print('EXPORT COMPLETE',flush=True)
