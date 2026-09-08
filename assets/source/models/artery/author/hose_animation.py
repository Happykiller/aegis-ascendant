"""Portable skeletal flexion and mechanical connector release, baked at 30 fps."""
import math
import bpy
from mathutils import Vector

CLIPS = {'Intact': 61, 'Endommage': 61, 'Rupture': 121, 'Rompu': 61}
JOINTS = 13


def smooth(t):
    t = min(1, max(0, t))
    return t * t * (3 - 2 * t)


def state(clip, frame):
    time = (frame - 1) / 60
    wave = math.sin(math.tau * time)
    damage = float(clip in ('Endommage', 'Rompu'))
    broken = float(clip == 'Rompu')
    if clip == 'Rupture':
        wave = 0
        broken = smooth((frame - 20) / 80)
        damage = broken
    return wave, damage, broken


def displacement(t, lane, wave, damage, broken):
    envelope = math.sin(math.pi * t)
    side = -1 if lane % 2 == 0 else 1
    return Vector((side * (.006 * wave * (1 + 2 * damage) * envelope + .12 * broken * t**2),
                   -.08 * broken * t**2,
                   .009 * wave * (1 + 2 * damage) * envelope - (.09 + lane * .008) * broken * t**2))


def apply_pose(objects, clip, frame):
    wave, damage, broken = state(clip, frame)
    for obj in objects:
        kind = obj.get('mechanism')
        if not kind:
            continue
        lane = obj.get('lane', 0)
        obj.location = obj['rest_location']
        obj.rotation_euler = (0, 0, 0)
        obj.scale = (1, 1, 1)
        if kind == 'flex':
            for index, bone in enumerate(obj.pose.bones):
                offset = displacement(index / (JOINTS - 1), lane, wave, damage, broken)
                bone.location = bone.bone.matrix_local.to_3x3().inverted() @ offset
        elif kind == 'connector':
            obj.location += Vector((.055 * (-1 if lane % 2 == 0 else 1) * broken,
                                    .62 * broken, -.055 * broken))
            obj.rotation_euler = (.12 * broken, .05 * broken, .07 * broken)
        elif kind == 'collar':
            obj.location += displacement(obj['t'], lane, wave, damage, broken)
            obj.rotation_euler.y = obj['side'] * (.025 * damage + .35 * broken)
            obj.location.x += obj['side'] * .025 * broken
        elif kind == 'pulse':
            radius = max(.001, (1 + .018 * wave * (1 + damage)) * (1 - broken))
            obj.scale = (radius, 1, radius)
        elif kind == 'wire':
            obj.location += displacement(1, lane, wave, damage, broken)
            obj.scale = (max(.001, broken),) * 3
            obj.rotation_euler.y = .03 * wave * broken
        elif kind == 'socket':
            obj.location += displacement(1, lane, wave, damage, broken)


def create_clips(objects):
    controls = [obj for obj in objects if obj.get('mechanism')]
    for obj in controls:
        obj['rest_location'] = list(obj.location)
    for clip, end in CLIPS.items():
        for obj in controls:
            obj.animation_data_create()
            obj.animation_data.action = None
        for frame in range(1, end + 1):
            apply_pose(controls, clip, frame)
            for obj in controls:
                if obj.type == 'ARMATURE':
                    for bone in obj.pose.bones:
                        bone.keyframe_insert('location', frame=frame, group=bone.name)
                else:
                    for channel in ('location', 'rotation_euler', 'scale'):
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
            track.mute = clip != 'Intact'
            obj.animation_data.action = None
    apply_pose(controls, 'Intact', 1)


def activate_clip(name):
    for obj in bpy.data.objects:
        if obj.animation_data:
            obj.animation_data.action = None
            for track in obj.animation_data.nla_tracks:
                track.mute = track.name != name
