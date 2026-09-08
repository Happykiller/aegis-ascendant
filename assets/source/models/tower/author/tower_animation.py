"""Independent fans, coolant vibration, service panels and geometric thermal pulse."""
import math
import bpy

CLIPS = {'Service': 61, 'Refroidissement': 61, 'Maintenance': 121}


def apply_pose(objects, clip, frame):
    t = (frame-1)/(CLIPS[clip]-1)
    wave = math.sin(math.tau*t)
    opening = math.sin(math.pi*t)**2 if clip == 'Maintenance' else 0
    for obj in objects:
        kind = obj.get('mechanism')
        if not kind:
            continue
        obj.location = obj['rest_location']
        obj.rotation_euler = (0,0,0)
        obj.scale = (1,1,1)
        if kind == 'fan':
            turns = 2 if clip == 'Refroidissement' else 1
            obj.rotation_euler.z = obj['direction']*math.tau*t*turns if clip != 'Maintenance' else 0
        elif kind == 'panels':
            for bone in obj.pose.bones:
                bone.rotation_mode = 'XYZ'
                bone.rotation_euler = (0,-1.05*opening,0)
        elif kind == 'coolant':
            obj.location.z += .008*wave*(2 if clip == 'Refroidissement' else 1)
        elif kind == 'thermal':
            radius = 1+.018*wave*(2 if clip == 'Refroidissement' else 1)
            obj.scale = (radius,radius,1)


def create_clips(objects):
    controls = [obj for obj in objects if obj.get('mechanism')]
    for obj in controls:
        obj['rest_location'] = list(obj.location)
    for clip,end in CLIPS.items():
        for obj in controls:
            obj.animation_data_create()
            obj.animation_data.action = None
        for frame in range(1,end+1):
            apply_pose(controls,clip,frame)
            for obj in controls:
                if obj.type == 'ARMATURE':
                    for bone in obj.pose.bones:
                        bone.keyframe_insert('rotation_euler',frame=frame,group=bone.name)
                else:
                    for channel in ('location','rotation_euler','scale'):
                        obj.keyframe_insert(channel,frame=frame)
        for obj in controls:
            action = obj.animation_data.action
            action.name = clip+' | '+obj.name
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for curve in bag.fcurves:
                            for key in curve.keyframe_points:
                                key.interpolation = 'LINEAR'
            track = obj.animation_data.nla_tracks.new()
            track.name = clip
            strip = track.strips.new(clip,1,action)
            strip.extrapolation = 'NOTHING'
            track.mute = clip != 'Service'
            obj.animation_data.action = None
    apply_pose(controls,'Service',1)


def activate_clip(name):
    for obj in bpy.data.objects:
        if obj.animation_data:
            obj.animation_data.action = None
            for track in obj.animation_data.nla_tracks:
                track.mute = track.name != name
