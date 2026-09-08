"""Mechanical failure and geometry-based energy pulses, portable to glTF."""
import math
import bpy
from mathutils import Vector,Matrix
CLIPS = {'Actif':61,'Endommage':61,'Rupture':121,'Rompu':61}


def smooth(t):
    t = max(0,min(1,t))
    return t*t*(3-2*t)


def values(clip,frame):
    wave = math.sin((frame-1)*math.tau/60)
    broken = 1 if clip=='Rompu' else 0
    damage = 1 if clip in ('Endommage','Rompu') else 0
    if clip=='Rupture':
        broken = smooth((frame-22)/76)
        damage = smooth((frame-1)/35)
        wave = 0
    return wave,broken,damage


def cable_points(lane,index,wave,broken,damage):
    gain = 1+2*damage
    if lane=='principal':
        pivot = Vector((-.36,-1.38,1))
        angle = .07*broken+.0015*gain*wave
        point = Vector((-.36,1.36,1))
    else:
        pivot = Vector((.36,-1.4,1))
        angle = -.18*broken+.002*gain*wave
        point = Vector((.36,1.36,.44))
    offset = Vector(((index-2)*.028,0,.018*math.sin(index*1.7)))
    start = pivot+Matrix.Rotation(angle,3,'X')@(point+offset-pivot)
    end = start+Vector(((index-2)*.12*broken,.09+.53*broken,
                       (-.25-.05*index)*broken+.008*wave*broken))
    return start,end


def apply_pose(controls,clip,frame):
    wave,broken,damage = values(clip,frame)
    gain = 1+2*damage
    fade = 1-smooth((broken-.6)/.4)
    for obj in controls:
        obj.location = obj['rest_location']
        obj.rotation_euler = (0,0,0)
        obj.scale = (1,1,1)
        kind = obj['mechanism']
        if kind=='connector':
            obj.location += Vector((.22*broken,1.10*broken,-.16*broken))
            obj.rotation_euler = (.15*broken,0,-.12*broken)
        elif kind=='feed':
            obj.rotation_euler.x = .07*broken+.0015*gain*wave
        elif kind=='secondary':
            obj.rotation_euler.x = -.18*broken+.002*gain*wave
        elif kind=='collar':
            obj.location.x += obj['side']*(.14*broken+.025*damage)
            obj.rotation_euler.y = obj['side']*(.38*broken+.08*damage+.002*wave)
        elif kind=='pulse':
            t = (frame-1)*math.tau/60
            phase = obj['phase']
            pulse = math.sin(t*2+phase)-math.sin(phase)
            radius = max(.001,(1+.025*pulse*gain)*fade)
            obj.scale = (radius,1,radius)
        elif kind in ('wire','wire_tip'):
            a,b = cable_points(obj['lane'],obj['index'],wave,broken,damage)
            direction = b-a
            obj.rotation_euler = direction.to_track_quat('Z','Y').to_euler()
            obj.location = a if kind=='wire' else b
            if kind=='wire':
                obj.scale.z = direction.length
            else:
                obj.scale = (max(.001,fade),)*3


def create_clips(asset):
    controls = [o for o in asset.objects if 'mechanism' in o]
    for obj in controls:
        obj['rest_location'] = list(obj.location)
    for clip,end in CLIPS.items():
        for obj in controls:
            obj.animation_data_create()
            obj.animation_data.action = None
        for frame in range(1,end+1):
            apply_pose(controls,clip,frame)
            for obj in controls:
                for channel in ('location','rotation_euler','scale'):
                    obj.keyframe_insert(data_path=channel,frame=frame)
        for obj in controls:
            action = obj.animation_data.action
            action.name = clip+' | '+obj.name.removeprefix('CTRL | ')
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
            track.mute = clip!='Actif'
            obj.animation_data.action = None
    apply_pose(controls,'Actif',1)


def activate_clip(name):
    for obj in bpy.data.objects:
        if 'mechanism' not in obj or not obj.animation_data:
            continue
        obj.animation_data.action = None
        for track in obj.animation_data.nla_tracks:
            track.mute = track.name!=name
