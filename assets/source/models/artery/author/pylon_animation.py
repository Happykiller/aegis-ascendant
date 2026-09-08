"""Subtle coolant vibration and articulated exchanger louvers."""
import math
import bpy

CLIPS = {'Service': 61, 'Refroidissement': 61, 'Maintenance': 121}


def apply_pose(objects, clip, frame):
    period = CLIPS[clip] - 1
    wave = math.sin(math.tau * (frame-1) / period)
    opening = math.sin(math.pi * (frame-1) / period)**2 if clip == 'Maintenance' else 0
    for obj in objects:
        kind = obj.get('mechanism')
        if not kind:
            continue
        obj.location = obj['rest_location']
        obj.rotation_euler = (0, 0, 0)
        obj.scale = (1, 1, 1)
        if kind == 'louvers':
            angle = .035 * wave
            if clip == 'Refroidissement':
                angle = .32 + .045 * wave
            if clip == 'Maintenance':
                angle = 1.15 * opening
            for bone in obj.pose.bones:
                bone.rotation_mode = 'XYZ'
                bone.rotation_euler = (0, angle, 0)
        elif kind == 'coolant':
            gain = 2 if clip == 'Refroidissement' else 1
            obj.location.x += obj['side'] * .006 * gain * wave
        elif kind == 'crown':
            obj.rotation_euler.z = .0012 * wave


def create_clips(objects):
    controls = [obj for obj in objects if obj.get('mechanism')]
    for obj in controls:
        obj['rest_location'] = list(obj.location)
    for clip, end in CLIPS.items():
        for obj in controls:
            obj.animation_data_create()
            obj.animation_data.action = None
        for frame in range(1, end+1):
            apply_pose(controls, clip, frame)
            for obj in controls:
                if obj.type == 'ARMATURE':
                    for bone in obj.pose.bones:
                        bone.keyframe_insert('rotation_euler', frame=frame, group=bone.name)
                else:
                    for channel in ('location', 'rotation_euler'):
                        obj.keyframe_insert(channel, frame=frame)
        for obj in controls:
            action = obj.animation_data.action
            action.name = clip + ' | ' + obj.name
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for curve in bag.fcurves:
                            for key in curve.keyframe_points:
                                key.interpolation = 'LINEAR'
            track = obj.animation_data.nla_tracks.new()
            track.name = clip
            strip = track.strips.new(clip, 1, action)
            strip.extrapolation = 'NOTHING'
            track.mute = clip != 'Service'
            obj.animation_data.action = None
    apply_pose(controls, 'Service', 1)


def activate_clip(name):
    for obj in bpy.data.objects:
        if obj.animation_data:
            obj.animation_data.action = None
            for track in obj.animation_data.nla_tracks:
                track.mute = track.name != name
