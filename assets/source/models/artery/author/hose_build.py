"""Asset 06: five independently skinned hoses, armored couplings and release cables."""
import math
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geometry as g
from paths import BLEND, ASSET_COLLECTION, MODULE_COLLECTION
from materials import make_materials, load_pixels, save_map, resample, rgba, SOURCE, SAMPLE_BOUNDS
from animation import JOINTS, create_clips
import studio

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.render.fps = 30
scene.frame_end = 121
materials = make_materials()


def braided_material():
    """Use the supplied sheath sample for color, with explicit technical weave relief."""
    source = load_pixels(SOURCE)
    left, top, right, bottom = SAMPLE_BOUNDS['energy']
    patch = resample(source[941-bottom:941-top, left:right], 1024)[:, :, :3]
    gray = patch.mean(axis=2)
    yy, xx = np.mgrid[0:1024, 0:1024] / 1024
    a = np.sin(math.tau * (xx * 12 + yy * 24))
    b = np.sin(math.tau * (xx * 12 - yy * 24))
    weave = np.maximum(a, b)
    color = np.repeat((.018 + .035 * gray + .014 * (weave + 1))[:, :, None], 3, axis=2)
    height = weave * .045
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 8
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 8
    normals = np.stack((-dx, -dy, np.ones_like(dx)), axis=2)
    normals /= np.linalg.norm(normals, axis=2)[:, :, None]
    base = save_map('braid_basecolor', rgba(color))
    normal = save_map('braid_normal', rgba(normals * .5 + .5), True)
    mat = bpy.data.materials.new('10 | Gaine tressee reference 06')
    mat.use_nodes = True
    mat['reference_source'] = SOURCE.name + ' / Gaine technique'
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Metallic'].default_value = .58
    shader.inputs['Roughness'].default_value = .40
    for image, target in [(base, 'Base Color'), (normal, 'Normal')]:
        tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = image
        if target == 'Normal':
            node = mat.node_tree.nodes.new('ShaderNodeNormalMap')
            mat.node_tree.links.new(tex.outputs['Color'], node.inputs['Color'])
            mat.node_tree.links.new(node.outputs['Normal'], shader.inputs['Normal'])
        else:
            mat.node_tree.links.new(tex.outputs['Color'], shader.inputs[target])
    return mat


materials['braid'] = braided_material()


def point(t, lane, straight=False):
    x, z = [(-.27, .23), (.27, .23), (-.205, .55), (.205, .55), (0, .17)][lane]
    if straight:
        x, z = 0, .30
    else:
        x += (-1 if lane % 2 else 1) * .025 * math.sin(math.pi * t)
        sag = .12 if lane in (2, 3) else .055
        z += -sag * math.sin(math.pi * t) + .09 * math.sin(math.tau * t) * (-1 if lane % 2 else 1)
    return Vector((x, -1.15 + 2.30 * t, z))


def armature(name, parent, lane, straight):
    data = bpy.data.armatures.new(name)
    obj = bpy.data.objects.new('CTRL | Flexion ' + name, data)
    g.COLLECTION.objects.link(obj)
    obj.parent = parent
    obj['mechanism'] = 'flex'
    obj['lane'] = lane
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for index in range(JOINTS):
        bone = data.edit_bones.new(f'FLEX_{index:02}')
        bone.head = point(index / (JOINTS - 1), lane, straight)
        bone.tail = bone.head + Vector((0, .06, 0))
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)
    return obj


def tube(name, lane, straight, rig, radius, braided):
    # Dense axial rings support actual smooth skin deformation and corrugation.
    steps, sides = 192, 20
    vertices = []
    for j in range(steps + 1):
        t = j / steps
        center = point(t, lane, straight)
        tangent = (point(min(1, t+.001), lane, straight) - point(max(0, t-.001), lane, straight)).normalized()
        axis_x = Vector((1, 0, 0))
        axis_x = (axis_x - tangent * axis_x.dot(tangent)).normalized()
        axis_z = axis_x.cross(tangent).normalized()
        r = radius * (1 + (0 if braided else .065 * math.cos(math.tau * t * 64)))
        for i in range(sides):
            angle = i * math.tau / sides
            vertices.append(center + r * (axis_x * math.cos(angle) + axis_z * math.sin(angle)))
    faces = []
    for j in range(steps):
        for i in range(sides):
            faces.append((j*sides+i, j*sides+(i+1)%sides, (j+1)*sides+(i+1)%sides, (j+1)*sides+i))
    faces.extend([tuple(reversed(range(sides))), tuple(steps*sides+i for i in range(sides))])
    obj = g.mesh(name, vertices, faces, materials['braid' if braided else 'hose'], 0)
    obj['flexible_surface'] = True
    uv = obj.data.uv_layers.new(name='GaineUV')
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4
        for loop_index in face.loop_indices:
            vi = obj.data.loops[loop_index].vertex_index
            ring, side = divmod(vi, sides)
            u = side / sides
            if side == 0 and any(v % sides == sides-1 for v in face.vertices):
                u = 1
            uv.data[loop_index].uv = (u, ring / steps * 4)
    groups = [obj.vertex_groups.new(name=f'FLEX_{i:02}') for i in range(JOINTS)]
    for j in range(steps + 1):
        value = j / steps * (JOINTS - 1)
        index = min(JOINTS - 2, int(value))
        weight = value - index
        ids = list(range(j*sides, (j+1)*sides))
        if weight < 1:
            groups[index].add(ids, 1-weight, 'REPLACE')
        if weight > 0:
            groups[index+1].add(ids, weight, 'REPLACE')
    modifier = obj.modifiers.new('Flexion continue', 'ARMATURE')
    modifier.object = rig
    return obj


def ring(name, y, x, z, radius, material='panel', depth=.06, inner=None):
    return g.ring(name, y, radius, inner if inner else radius*.78, depth, materials[material], center=(x, z), count=24)


def coupling(parent, name, center, sign, radius):
    g.PARENT = parent
    x, y, z = center
    ring('Joint ' + name, y, x, z, radius*.90, 'dark', .065)
    ring('Frette acier ' + name, y, x, z, radius, 'edge', .04)
    g.box('Boitier octogonal ' + name, (x, y+sign*.11, z), (radius*2, .22, radius*2), materials['armor'], .035)
    ring('Face connecteur ' + name, y+sign*.225, x, z, radius*.87, 'panel', .035)
    ring('Port ' + name, y+sign*.251, x, z, radius*.63, 'dark', .03, radius*.47)
    g.rod('Fond prise ' + name, (x, y+sign*.22, z), (x, y+sign*.235, z), radius*.48, materials['dark'], 20)
    for dx in (-.72, .72):
        for dz in (-.72, .72):
            g.rod('Vis prise ' + name, (x+dx*radius, y+sign*.223, z+dz*radius),
                  (x+dx*radius, y+sign*.24, z+dz*radius), .009, materials['bronze'], 6)
    for dx in (-1, 1):
        g.box('Protection laterale ' + name, (x+dx*radius, y+sign*.11, z),
              (.02, .14, radius*1.28), materials['panel'], .007)
    # Emission insert is an independent part, physically retracting on failure.
    pulse = g.control('Noyau ' + name, parent)
    pulse['mechanism'] = 'pulse'
    g.PARENT = pulse
    ring('Anneau magenta ' + name, y-sign*.057, x, z, radius*.86, 'magenta', .036)
    g.pivot(pulse, (x, y-sign*.057, z))
    g.PARENT = parent
    for offset in (-.079, -.031):
        ring('Garde noyau ' + name, y+sign*offset, x, z, radius*.91, 'armor', .012)


def lane_build(lane, root, straight=False):
    label = ('Droit' if straight else 'Ligne') + f' {lane+1:02}'
    group = g.control(label, root)
    group['module'] = 'straight' if straight else 'bent'
    group['lane'] = lane
    radius = .039 if lane == 4 else .068
    rig = armature(label, group, lane, straight)
    g.PARENT = group
    tube('Gaine ' + label, lane, straight, rig, radius, lane in (0, 3))
    for sign, t in [(-1, 0), (1, 1)]:
        parent = g.control(('Raccord fixe ' if sign < 0 else 'Raccord mobile ') + label, group)
        parent['lane'] = lane
        if sign > 0:
            parent['mechanism'] = 'connector'
        c = point(t, lane, straight)
        coupling(parent, label + str(sign), c, sign, .072 if lane == 4 else .14)
        g.pivot(parent, c)
        socket = g.control('Socket ' + label + str(sign), parent)
        socket.location = (0, sign*.25, 0)
        socket['role'] = 'mount_hull' if sign < 0 else 'mount_engine'
    for t in (.14, .52, .87):
        x, y, z = point(t, lane, straight)
        for side in (-1, 1):
            collar = g.control('Collier ' + label + f' {t} {side}', group)
            collar['mechanism'], collar['lane'], collar['side'], collar['t'] = 'collar', lane, side, t
            g.PARENT = collar
            start = -math.pi/2 if side > 0 else math.pi/2
            obj = g.sector('Demi coque ' + label, [(y-.031,radius*1.4),(y+.031,radius*1.4),
                            (y+.031,radius*1.06),(y-.031,radius*1.06)],start,start+math.pi,materials['panel'],10,.004)
            for vertex in obj.data.vertices:
                vertex.co.x += x
                vertex.co.z += z
            for angle in (start+.4, start+1.55, start+2.75):
                bx, bz = x+radius*1.38*math.cos(angle), z+radius*1.38*math.sin(angle)
                g.rod('Boulon collier ' + label, (bx,y-.032,bz),(bx,y-.045,bz),.008,materials['bronze'],6)
            g.pivot(collar, (x,y,z))
    end = point(1, lane, straight)
    vfx = g.control('VFX fuite ' + label, group)
    vfx.location = end
    vfx['mechanism'], vfx['lane'], vfx['role'] = 'socket', lane, 'vfx_leak'
    wires = g.control('Brins exposes ' + label, group)
    wires.location = end
    wires['mechanism'], wires['lane'] = 'wire', lane
    g.PARENT = wires
    for index in range(5):
        offset = (index-2)*.015
        g.hose('Cable interne ' + label, [(offset,0,0),(offset*1.5,.13,-.02),
               (offset*2,.27,-.07),(offset*3,.40,-.13-index*.012)],.005,
               materials['bronze' if index%2 else 'hose'])
    return group


asset = bpy.data.collections.new(ASSET_COLLECTION)
scene.collection.children.link(asset)
g.COLLECTION = asset
root = g.control('Flexible technique 06')
root['asset_number'] = '06/10'
for lane in range(5):
    lane_build(lane, root)
# Compact service brackets join the bundle only at the fixed end.
g.PARENT = root
for x in (-.27, .27):
    g.box('Bride de fixation', (x,-1.04,.069), (.23,.19,.06), materials['armor'], .015)
    for dx in (-.075,.075):
        g.rod('Vis bride',(x+dx,-1.04,.1),(x+dx,-1.04,.113),.015,materials['bronze'],6)
module = bpy.data.collections.new(MODULE_COLLECTION)
scene.collection.children.link(module)
module.hide_render = True
g.COLLECTION = module
module_root = g.control('Module droit 06')
lane_build(0, module_root, True)
for collection in (asset, module):
    for obj in collection.objects:
        if obj.type == 'MESH':
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            bm.to_mesh(obj.data)
            bm.free()
            if not obj.get('flexible_surface'):
                g.uv_map(obj)
create_clips(list(asset.objects) + list(module.objects))
module.hide_viewport = True
studio.setup(scene)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
print('BUILD COMPLETE', len(asset.objects), flush=True)
