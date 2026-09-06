"""Editable lofts, planar panels, tubes and rigid module assembly."""
import math
import bpy
from mathutils import Vector


def mesh(name, vertices, faces, material, bevel=0.012):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    if material:
        data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new('Editable edge bevel', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 2
        modifier = obj.modifiers.new('Weighted panel normals', 'WEIGHTED_NORMAL')
        modifier.keep_sharp = True
    return obj


def box(name, location, dimensions, material, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new('Editable edge bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        obj.modifiers.new('Weighted panel normals', 'WEIGHTED_NORMAL')
    return obj


def tube(name, center, sections, material, count=32):
    """Closed radial cross-section swept around Y; supports truly hollow tubes."""
    x, y, z = center
    vertices = [(x+r*math.cos(i*math.tau/count), y+dy, z+r*math.sin(i*math.tau/count))
                for dy, r in sections for i in range(count)]
    faces = []
    for j in range(len(sections)):
        k = (j+1) % len(sections)
        for i in range(count):
            n = (i+1) % count
            faces.append((j*count+i,j*count+n,k*count+n,k*count+i))
    obj = mesh(name, vertices, faces, material, .006)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def rod(name, start, end, radius, material, radius_end=None, count=16):
    delta = Vector(end)-Vector(start)
    bpy.ops.mesh.primitive_cone_add(vertices=count, radius1=radius,
        radius2=radius if radius_end is None else radius_end, depth=delta.length,
        location=(Vector(start)+Vector(end))/2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = delta.to_track_quat('Z','Y').to_euler()
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def panel(name, outline, surface, material, thickness=.035):
    top = [(x,y,surface(x,y)) for x,y in outline]
    n = len(top)
    vertices = top + [(x,y,z-thickness) for x,y,z in top]
    faces = [tuple(range(n)), tuple(reversed(range(n,2*n)))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name, vertices, faces, material, .006)


def loft(name, sections, material, count=12):
    """Sections: y, half-width, center-z, upper-radius, lower-radius."""
    vertices = []
    for y,w,z,up,down in sections:
        for i in range(count):
            a = math.tau*i/count
            vertices.append((w*math.cos(a),y,z+math.sin(a)*(up if math.sin(a)>=0 else down)))
    faces = [tuple(reversed(range(count)))]
    for j in range(len(sections)-1):
        for i in range(count):
            n=(i+1)%count
            faces.append((j*count+i,j*count+n,(j+1)*count+n,(j+1)*count+i))
    faces.append(tuple(range((len(sections)-1)*count,len(sections)*count)))
    return mesh(name,vertices,faces,material,.018)


def curve(name, points, radius, material):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = radius
    data.bevel_resolution = 2
    spline = data.splines.new('POLY')
    spline.points.add(len(points)-1)
    for p, xyz in zip(spline.points,points):
        p.co = (*xyz,1)
    obj = bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(material)
    return obj


def label(name, body, position, size, material, rotation=(0,0,0)):
    data = bpy.data.curves.new(name,'FONT')
    data.body = body
    data.align_x = 'CENTER'
    data.size = size
    data.extrude = .0005
    obj = bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = rotation
    data.materials.append(material)
    return obj


def parent_keep_world(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world


def control(name, position=(0,0,0), parent=None):
    obj = bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    obj.empty_display_type = 'ARROWS'
    obj.empty_display_size = .5
    if parent:
        parent_keep_world(obj,parent)
    return obj


def clip_polygon(points, axis, boundary, greater):
    result = []
    for a,b in zip(points,points[1:]+points[:1]):
        inside_a = (a[axis]>=boundary) == greater
        inside_b = (b[axis]>=boundary) == greater
        if inside_a:
            result.append(a)
        if inside_a != inside_b:
            t = (boundary-a[axis])/(b[axis]-a[axis])
            result.append(tuple(a[k]+t*(b[k]-a[k]) for k in range(2)))
    return result


def project_uv(obj, repeat_m=1.5):
    """Portable explicit box UVs; editable panels are separate UV islands."""
    if obj.type != 'MESH':
        return
    layer = obj.data.uv_layers.new(name='SurfaceUV')
    for face in obj.data.polygons:
        normal = obj.matrix_world.to_3x3() @ face.normal
        dominant = max(range(3),key=lambda i:abs(normal[i]))
        axes = [i for i in range(3) if i != dominant]
        for index in face.loop_indices:
            p = obj.matrix_world @ obj.data.vertices[obj.data.loops[index].vertex_index].co
            layer.data[index].uv = (p[axes[0]]/repeat_m,p[axes[1]]/repeat_m)
