"""Editable hard-surface primitives; axial engine geometry runs along Y."""
import math
import bpy
from mathutils import Vector

COLLECTION = None
PARENT = None


def mesh(name, vertices, faces, material, bevel=.025):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    COLLECTION.objects.link(obj)
    obj.parent = PARENT
    data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new('Chanfreins editables', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 2
        obj.modifiers.new('Normales ponderees', 'WEIGHTED_NORMAL')
    return obj


def box(name, location, size, material, bevel=.035, angle=0):
    vertices = []
    for x, y, z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),
                    (1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]:
        x, y, z = x*size[0]/2, y*size[1]/2, z*size[2]/2
        vertices.append((location[0]+x*math.cos(angle)-z*math.sin(angle),
                         location[1]+y, location[2]+x*math.sin(angle)+z*math.cos(angle)))
    return mesh(name, vertices, [(0,4,6,2),(1,3,7,5),(0,1,5,4),
                                (2,6,7,3),(0,2,3,1),(4,5,7,6)], material, bevel)


def sector(name, sections, start, end, material, count=4, bevel=.02):
    """Closed radial profile swept over a partial arc (armor plate or annulus)."""
    closed = abs(end-start-math.tau) < 1e-6
    n = count if closed else count+1
    vertices = [(r*math.cos(start+(end-start)*i/count), y,
                 r*math.sin(start+(end-start)*i/count))
                for y, r in sections for i in range(n)]
    faces = []
    for j in range(len(sections)):
        k = (j+1) % len(sections)
        for i in range(count):
            following = (i+1) % n
            faces.append((j*n+i, j*n+following, k*n+following, k*n+i))
    if not closed:
        faces += [tuple(reversed([j*n for j in range(len(sections))])),
                  tuple(j*n+count for j in range(len(sections)))]
    return mesh(name, vertices, faces, material, bevel)


def ring(name, y, outer, inner, depth, material, center=(0,0), count=64):
    # Full revolution without overlapping end caps.
    sections = [(y-depth/2, outer),(y+depth/2, outer),
                (y+depth/2, inner),(y-depth/2, inner)]
    vertices = [(center[0]+r*math.cos(i*math.tau/count), dy,
                 center[1]+r*math.sin(i*math.tau/count))
                for dy, r in sections for i in range(count)]
    faces = [(j*count+i, j*count+(i+1)%count,
              ((j+1)%4)*count+(i+1)%count, ((j+1)%4)*count+i)
             for j in range(4) for i in range(count)]
    return mesh(name, vertices, faces, material, .008)


def rod(name, start, end, radius, material, count=12):
    delta = Vector(end)-Vector(start)
    rotation = delta.to_track_quat('Z','Y').to_matrix()
    vertices = [tuple(Vector(start)+rotation@Vector((radius*math.cos(i*math.tau/count),
                radius*math.sin(i*math.tau/count), h)))
                for h in (0,delta.length) for i in range(count)]
    faces = [tuple(reversed(range(count))), tuple(range(count,2*count))]
    faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    return mesh(name, vertices, faces, material, .008)


def hose(name, points, radius, material):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = radius
    data.bevel_resolution = 2
    data.resolution_u = 8
    spline = data.splines.new('BEZIER')
    spline.bezier_points.add(len(points)-1)
    for point, xyz in zip(spline.bezier_points, points):
        point.co = xyz
        point.handle_left_type = 'AUTO'
        point.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, data)
    COLLECTION.objects.link(obj)
    obj.parent = PARENT
    data.materials.append(material)
    return obj


def control(name, parent=None, explode=(0,0,0)):
    obj = bpy.data.objects.new('CTRL | '+name, None)
    COLLECTION.objects.link(obj)
    obj.parent = parent
    obj.empty_display_type = 'ARROWS'
    obj.empty_display_size = .4
    obj['explode_offset'] = list(explode)
    return obj


def uv_map(obj):
    from materials import map_surface
    map_surface(obj)


def prism_x(name, outline, x0, x1, material, bevel=.04):
    """Extrude an ordered YZ silhouette along X."""
    n = len(outline)
    vertices = [(x,y,z) for x in (x0,x1) for y,z in outline]
    faces = [tuple(reversed(range(n))),tuple(range(n,n*2))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vertices,faces,material,bevel)


def ring_x(name, center, outer, inner, depth, material, count=40):
    obj = ring(name,0,outer,inner,depth,material,count=count)
    for v in obj.data.vertices:
        x,y,z = v.co
        v.co = (center[0]+y,center[1]+x,center[2]+z)
    obj.data.update()
    return obj


def pivot(obj, location):
    obj.location = location
    bpy.context.view_layer.update()
    for child in obj.children:
        child.matrix_parent_inverse = obj.matrix_world.inverted()
