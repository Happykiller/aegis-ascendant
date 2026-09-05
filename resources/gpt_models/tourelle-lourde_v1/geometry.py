"""Small, explicit Blender modeling helpers used by the Spectre 9 revision."""
import math

import bpy
from mathutils import Vector


def finish(obj, name, material, bevel=0):
    obj.name = name
    if material:
        obj.data.materials.append(material)
    if bevel:
        edge = obj.modifiers.new('Machined edges', 'BEVEL')
        edge.width = bevel
        edge.segments = 1
        obj.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return obj


def mesh(name, vertices, faces, material, bevel=0):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    return finish(obj, name, material, bevel)


def box(name, location, dimensions, material, bevel=.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.scale = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, material, bevel)


def rod(name, start, end, radius, material, end_radius=None, vertices=16):
    direction = Vector(end)-Vector(start)
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                  radius2=radius if end_radius is None else end_radius,
                                  depth=direction.length, location=(Vector(start)+Vector(end))/2)
    obj = bpy.context.object
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return finish(obj, name, material, .005)


def plate(name, points, height, thickness, material, bevel=.012):
    count = len(points)
    vertices = [(x,y,height) for x,y in points] + [(x,y,height-thickness) for x,y in points]
    faces = [tuple(range(count)), tuple(range(count*2-1,count-1,-1))]
    faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    return mesh(name, vertices, faces, material, bevel)


def line(name, points, radius, material):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = radius
    data.bevel_resolution = 2
    spline = data.splines.new('POLY')
    spline.points.add(len(points)-1)
    for point, coordinate in zip(spline.points, points):
        point.co = (*coordinate,1)
    obj = bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    return finish(obj,name,material)


def ring(name, center, outer, inner, depth, material):
    x,y,z = center
    count = 40
    vertices = []
    for yy,radius in [(y-depth/2,outer),(y+depth/2,outer),(y-depth/2,inner),(y+depth/2,inner)]:
        vertices.extend((x+radius*math.cos(i*math.tau/count),yy,z+radius*math.sin(i*math.tau/count))
                        for i in range(count))
    faces = []
    for i in range(count):
        j = (i+1)%count
        faces += [(i,j,count+j,count+i),(2*count+i,3*count+i,3*count+j,2*count+j),
                  (i,2*count+i,2*count+j,j),(count+i,count+j,3*count+j,3*count+i)]
    return mesh(name,vertices,faces,material,.006)


def text(name, body, location, size, material, rotation=(0,0,0)):
    data = bpy.data.curves.new(name,'FONT')
    data.body = body
    data.size = size
    data.align_x = 'CENTER'
    data.extrude = .0004
    obj = bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    return finish(obj,name,material)


def pivot(name, location, objects):
    obj = bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.empty_display_type = 'ARROWS'
    obj.empty_display_size = .3
    bpy.context.view_layer.update()
    for child in objects:
        world = child.matrix_world.copy()
        child.parent = obj
        child.matrix_world = world
    return obj


def key_rotation(obj, values, axis=0):
    for frame,degrees in values:
        obj.rotation_euler[axis] = math.radians(degrees)
        obj.keyframe_insert(data_path='rotation_euler', frame=frame)


def clip_polygon(points, axis, bound, keep_greater):
    result = []
    for start,end in zip(points,points[1:]+points[:1]):
        inside_start = (start[axis] >= bound) == keep_greater
        inside_end = (end[axis] >= bound) == keep_greater
        if inside_start:
            result.append(start)
        if inside_start != inside_end:
            t = (bound-start[axis])/(end[axis]-start[axis])
            result.append(tuple(start[j]+t*(end[j]-start[j]) for j in range(2)))
    return result


def remove(objects):
    for obj in list(objects):
        bpy.data.objects.remove(obj,do_unlink=True)
