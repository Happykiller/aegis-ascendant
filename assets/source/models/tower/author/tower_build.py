"""Sixteen modular meshes for the 26 m stern cooling tower."""
import math
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geometry as g
from paths import BLEND, ASSET_COLLECTION
from materials import make_materials, load_pixels, resample, save_map, rgba, SOURCE, SAMPLE_BOUNDS
from animation import create_clips
import studio

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.render.fps = 30
scene.frame_end = 121
asset = bpy.data.collections.new(ASSET_COLLECTION)
scene.collection.children.link(asset)
g.COLLECTION = asset
materials = make_materials()
root = g.control('Tour echange thermique 08')
root['asset_number'] = '08/10'
root['dimensions_reference_xyz_m'] = [14, 14, 26]
root['pivot'] = 'Base au centre, sol Z=0'
modules = {}


def sample_material(family, name, metal, roughness):
    source = load_pixels(SOURCE)
    left, top, right, bottom = SAMPLE_BOUNDS[family]
    patch = resample(source[1024-bottom:1024-top, left:right], 1024)[:, :, :3]
    yy, xx = np.mgrid[0:1024, 0:1024]/1024
    if family == 'carbon':
        weave = .78 + .22*np.sin(math.tau*(xx*32+yy*32))*np.sin(math.tau*(xx*32-yy*32))
        patch *= .25 * weave[:, :, None]
    image = save_map(family+'_basecolor', rgba(patch))
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat['surface_family'] = 'panel'
    mat['reference_source'] = SOURCE.name + ' / ' + family
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = roughness
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = image
    mat.node_tree.links.new(tex.outputs['Color'], shader.inputs['Base Color'])
    return mat


materials['carbon'] = sample_material('carbon', '10 | Carbone technique', .45, .51)
materials['pipe'] = sample_material('pipe', '11 | Conduite sombre', .78, .32)


def module(name, slug, mechanism=None, side=0):
    obj = g.control(name, root)
    obj['module_slug'] = slug
    if mechanism:
        obj['mechanism'], obj['side'] = mechanism, side
    modules[slug] = obj
    g.PARENT = obj
    return obj


def box(name, location, size, mat='armor', bevel=.035):
    return g.box(name, location, size, materials[mat], bevel)


def rod(name, a, b, radius, mat='edge', sides=12):
    return g.rod(name, a, b, radius, materials[mat], sides)


def beam(name, a, b, width, depth=None, mat='armor'):
    a, b = Vector(a), Vector(b)
    obj = box(name, (0,0,0), (width, depth or width, (b-a).length), mat, .045)
    rotation = (b-a).to_track_quat('Z','Y').to_matrix()
    for vertex in obj.data.vertices:
        vertex.co = (a+b)/2 + rotation @ vertex.co
    return obj


def column(name, levels, mat='armor'):
    outline = [(-.72,-1),(.72,-1),(1,-.72),(1,.72),(.72,1),(-.72,1),(-1,.72),(-1,-.72)]
    vertices = [(x*w/2,y*d/2,z) for z,w,d in levels for x,y in outline]
    faces = [tuple(reversed(range(8))), tuple((len(levels)-1)*8+i for i in range(8))]
    for j in range(len(levels)-1):
        for i in range(8):
            faces.append((j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i))
    return g.mesh(name, vertices, faces, materials[mat], .045)


def pipe(name, points, radius=.3, mat='pipe'):
    obj = g.hose(name, points, radius, materials[mat])
    obj.data.use_fill_caps = True
    obj.data.resolution_u = 5
    obj.data.bevel_resolution = 1
    return obj


def ring_z(name, x, y, z, radius, depth=.18, mat='panel'):
    obj = g.ring(name, 0, radius, radius*.79, depth, materials[mat], count=20)
    for vertex in obj.data.vertices:
        vx, vy, vz = vertex.co
        vertex.co = (x+vx, y+vz, z+vy)
    return obj


def bolt_front(x, y, z, radius=.055):
    rod('Boulon affleurant', (x,y,z),(x,y-.05,z),radius,'bronze',6)


def marker(name, center, size):
    box('Logement '+name, center, (size[0]+.13,size[1]+.08,size[2]+.12), 'dark', .02)
    box(name, (center[0],center[1]-.055,center[2]),size,'magenta',.016)


def radial(angle, radius, z, tangent=0):
    return Vector((radius*math.cos(angle)-tangent*math.sin(angle),
                   radius*math.sin(angle)+tangent*math.cos(angle),z))


def rotate_z(obj, angle):
    rotation = Matrix.Rotation(angle,3,'Z')
    for vertex in obj.data.vertices:
        vertex.co = rotation @ vertex.co
    return obj


def radial_box(name, angle, radius, z, width, depth, height, mat='armor', bevel=.04):
    obj = box(name,(0,-radius,z),(width,depth,height),mat,bevel)
    return rotate_z(obj,angle+math.pi/2)


def annulus(name, z, outer, inner, depth, mat='panel', x=0, y=0, count=64):
    obj = g.ring(name,0,outer,inner,depth,materials[mat],count=count)
    # Thin fins and wire grilles do not need dense bevel topology at game distance.
    if depth <= .18:
        for modifier in list(obj.modifiers):
            obj.modifiers.remove(modifier)
        for face in obj.data.polygons:
            face.use_smooth = face.index // count in (0,2)
    for vertex in obj.data.vertices:
        vx,vy,vz = vertex.co
        vertex.co = (x+vx,y+vz,z+vy)
    return obj


def conical_sector(name, sections, start, end, mat='armor', count=6):
    obj = g.sector(name,sections,start,end,materials[mat],count,.025)
    for vertex in obj.data.vertices:
        x,y,z = vertex.co
        vertex.co = (x,z,y)
    return obj


base = module('Socle et ancrages','01_socle')
column('Socle octogonal',[(0,14,14),(.65,14,14),(1.0,13.6,13.6),(1.35,12.9,12.9)],'armor')
for x in (-5.5,5.5):
    for y in (-5.5,5.5):
        box('Pied ancrage',(x,y,1.55),(2.15,2.15,1.05),'armor',.16)
        for dx in (-.7,.7):
            for dy in (-.7,.7):
                rod('Goujon ancrage',(x+dx,y+dy,2.05),(x+dx,y+dy,2.19),.10,'edge',6)
        marker('Balise pied',(x,y-1.1,1.5),(.75,.06,.15))
for angle in (-math.pi/2,0,math.pi/2,math.pi):
    radial_box('Plinthe socle',angle,6.83,.6,3.2,.12,.45,'panel',.04)
    radial_box('Ligne socle',angle,6.91,.64,1.65,.04,.10,'magenta',.01)

core = module('Section centrale echangeurs','02_section_centrale')
column('Ossature octogonale',[(1.35,6.6,6.6),(4.2,6.2,6.2),(14.4,5.7,5.7),(17.3,5.2,5.2)],'dark')
for index in range(8):
    angle = index*math.tau/8
    for z,radius in [(2.6,3.25),(7.4,3.05),(14.8,2.86),(17,2.68)]:
        radial_box('Ceinture octogonale',angle,radius,z,1.68,.23,.27,'panel',.05)
    for side in (-1,1):
        a = radial(angle,3.06,3.0,side*.70)
        b = radial(angle,2.77,16.5,side*.70)
        beam('Montant central',a,b,.20,.24,'armor')
    if index%2:
        for j in range(23):
            z = 4.2+j*.50
            radius = 3.05-(z-4.2)*.018
            radial_box('Ailette echangeur',angle,radius,z,1.27,.28,.12,'edge',.013)
        radial_box('Montant temoin',angle,3.21,9.4,.12,.05,4.6,'magenta',.015)
    else:
        for z,height in [(3.15,2.2),(10.5,4.5),(14.5,2.8)]:
            radius = 3.13-(z-3)*.023
            radial_box('Capot technique fixe',angle,radius,z,1.7,.19,height,'armor',.065)
            radial_box('Insert capot',angle,radius+.105,z,1.24,.04,height*.77,'carbon',.025)
            radial_box('Temoin capot',angle,radius+.145,z-height*.34,.65,.035,.085,'magenta',.012)
    for z in (4.4,8.0,11.6,15.8):
        p = radial(angle,3.12-(z-4)*.02,z,.72)
        rod('Fixation nervure',p,p+radial(angle,.08,0),.055,'bronze',6)
# Sole marking permitted by the board.
font = bpy.data.curves.new('Repere 08','FONT')
font.body, font.align_x, font.size, font.extrude = '08','CENTER',.8,.004
label = bpy.data.objects.new('Repere discret 08',font)
asset.objects.link(label)
label.parent = core
label.location = (0,-3.13,9.65)
label.rotation_euler.x = math.pi/2
font.materials.append(materials['edge'])

head = module('Diffuseur conique et grille radiale','03_diffuseur')
# Lower expanding neck is paneled; upper cone consists of separated cooling fins.
for index in range(12):
    angle = index*math.tau/12
    conical_sector('Panneau de col evase',[(17.1,3.26),(21.2,4.42),(21.2,4.23),(17.1,3.06)],
                   angle+.025,angle+math.tau/12-.025,'armor',4)
    beam('Raidisseur de col',radial(angle,3.3,17.15),radial(angle,4.48,21.25),.16,.20,'panel')
    if index%2 == 0:
        beam('Bande thermique de col',radial(angle+.09,3.47,17.75),radial(angle+.09,4.33,20.7),.10,.07,'magenta')
annulus('Ceinture basse diffuseur',17.15,3.40,3.02,.24,'panel')
annulus('Ceinture intermediaire',21.25,4.63,4.21,.30,'armor')
for j in range(23):
    z = 21.65+j*.174
    radius = 4.62+(z-21.65)*.54
    annulus('Ailette de dissipation',z,radius,radius-.18,.075,'panel' if j%4==0 else 'dark')
for index in range(12):
    angle = index*math.tau/12
    beam('Nervure diffuseur',radial(angle,4.61,21.35),radial(angle,6.84,25.72),.24,.28,'armor')
    beam('Arete nervure',radial(angle+.018,4.70,21.55),radial(angle+.018,6.80,25.52),.065,.08,'edge')
    if index%2 == 0:
        beam('Ligne magenta diffuseur',radial(angle-.023,4.82,21.88),radial(angle-.023,6.67,25.32),.075,.065,'magenta')
    for z,r in ((21.5,4.76),(25.53,6.76)):
        p = radial(angle,r,z)
        rod('Boulon nervure',p,p+radial(angle,.075,0),.075,'bronze',6)
annulus('Couronne de bouche',25.77,6.95,6.46,.46,'armor')
annulus('Bord acier',25.94,6.96,6.77,.12,'edge')
annulus('Lit du noyau',25.16,1.04,.73,.16,'dark')
for r in (1.55,2.6,3.65,4.7,5.7,6.35):
    annulus('Grille concentrique',25.25+.06*r,r+.045,r-.045,.07,'edge')
for index in range(24):
    angle = index*math.tau/24
    beam('Rayon de grille',radial(angle,1.03,25.25),radial(angle,6.45,25.66),.055,.065,'edge')
for index in range(4):
    socket = g.control('VFX dissipation '+str(index+1),head)
    socket.location = radial(index*math.pi/2,2.6,25.8)
    socket['role'] = 'vfx_heat'

for index,(sx,sy) in enumerate([(-1,-1),(1,-1),(-1,1),(1,1)],4):
    ctrl = module('Support structurel '+str(index-3),f'{index:02}_support_{index-3}')
    a = Vector((sx*5.5,sy*5.5,2.03))
    b = Vector((sx*2.55,sy*2.55,14.8))
    beam('Jambe blindee',a,b,.72,.81,'armor')
    beam('Rail de renfort',a+Vector((sx*.32,0,.2)),b+Vector((sx*.32,0,-.2)),.15,.19,'panel')
    middle = a.lerp(b,.28)
    box('Noeud de renfort',middle,(1.02,1.02,1.15),'panel',.12)
    marker('Indicateur support',(middle.x,middle.y-.55,middle.z),(.20,.055,.63))
    beam('Contrefiche basse',(sx*5.3,sy*5.3,2.1),(sx*3.4,sy*3.4,5.2),.38,.43,'dark')
    g.pivot(ctrl,a)

panels = module('Panneaux de maintenance','08_panneaux_techniques')
data = bpy.data.armatures.new('Charnières panneaux')
rig = bpy.data.objects.new('CTRL | Charnières maintenance',data)
asset.objects.link(rig)
rig.parent = panels
rig['mechanism'] = 'panels'
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for index in range(4):
    angle = index*math.pi/2
    bone = data.edit_bones.new(f'CAPOT_{index+1:02}')
    bone.head = radial(angle,3.15,5.85,-.84)
    bone.tail = bone.head+Vector((0,0,.5))
bpy.ops.object.mode_set(mode='OBJECT')
rig.select_set(False)
for index in range(4):
    angle = index*math.pi/2
    previous = set(panels.children)
    radial_box('Porte de maintenance',angle,3.15,5.85,1.65,.22,3.0,'armor',.065)
    radial_box('Insert de porte',angle,3.275,5.85,1.2,.04,2.35,'carbon',.025)
    radial_box('Voyant porte',angle,3.31,4.85,.7,.04,.10,'magenta',.012)
    for tangent in (-.64,.64):
        for z in (4.60,7.12):
            p = radial(angle,3.30,z,tangent)
            rod('Vis porte',p,p+radial(angle,.055,0),.06,'bronze',6)
    for obj in set(panels.children)-previous:
        if obj.type == 'MESH':
            group = obj.vertex_groups.new(name=f'CAPOT_{index+1:02}')
            group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
panels['rig_name'] = rig.name

pipes = module('Conduites principales','09_conduites','coolant')
for index in range(4):
    angle = index*math.pi/2
    for tangent in (-.40,.40):
        points = [radial(angle,6.65,1.9,tangent),radial(angle,5.75,1.9,tangent),
                  radial(angle,4.9,2.5,tangent),radial(angle,3.65,4.0,tangent*2.875),
                  radial(angle,3.47,7.85,tangent*2.875),radial(angle,3.16,8.7,tangent*2.875)]
        pipe('Liaison de refroidissement',points,.27 if tangent<0 else .22)
        for r in (6.38,5.82):
            center = radial(angle,r,1.9,tangent)
            obj = g.ring('Collier de raccord',0,.35 if tangent<0 else .30,.26 if tangent<0 else .21,.16,materials['panel'],count=20)
            rotate_z(obj,angle-math.pi/2)
            for vertex in obj.data.vertices:
                vertex.co += center
        center = radial(angle,3.47,6.7,tangent*2.875)
        annulus('Collier vertical',6.7,.33 if tangent<0 else .28,.25 if tangent<0 else .20,.16,'panel',center.x,center.y,24)
    socket = g.control('Socket moteur '+str(index+1),pipes)
    socket.location = radial(angle,6.65,1.9)
    socket['role'] = 'engine_interface'

housings = module('Carter des quatre ventilateurs','10_carters_ventilation')
fan_centers = []
for index in range(4):
    angle = math.pi/4+index*math.pi/2
    center = radial(angle,4.52,0)
    fan_centers.append(center)
    x,y = center.x,center.y
    annulus('Embase ventilateur',2.35,1.12,.69,.35,'armor',x,y)
    annulus('Corps ventilateur',3.5,.96,.76,2.0,'dark',x,y,32)
    annulus('Couronne ventilateur',6.62,1.14,.96,.32,'panel',x,y)
    annulus('Bord de grille ventilateur',6.86,1.15,1.00,.16,'edge',x,y)
    for j in range(8):
        a = j*math.tau/8
        offset = radial(a,.98,0)
        beam('Montant ventilateur',(x+offset.x,y+offset.y,2.4),(x+offset.x,y+offset.y,6.6),.12,.14,'armor')
        if j%2 == 0:
            offset = radial(a,1.01,0)
            beam('Temoin ventilateur',(x+offset.x,y+offset.y,3.0),(x+offset.x,y+offset.y,5.8),.065,.06,'magenta')
    for r in (.36,.65,.91):
        annulus('Grille ventilateur',6.88,r+.022,r-.022,.045,'edge',x,y,32)
    for j in range(8):
        a = j*math.tau/8
        start = Vector((x,y,6.88))+radial(a,.13,0)
        end = Vector((x,y,6.88))+radial(a,1.02,0)
        rod('Rayon grille ventilation',start,end,.021,'edge',8)
    socket = g.control('VFX ventilation '+str(index+1),housings)
    socket.location = (x,y,7)
    socket['role'] = 'vfx_ventilation'

for index,center in enumerate(fan_centers,11):
    ctrl = module('Rotor ventilateur '+str(index-10),f'{index:02}_rotor_{index-10}','fan')
    ctrl['direction'] = -1 if index%2 else 1
    x,y = center.x,center.y
    rod('Moyeu rotor',(x,y,6.36),(x,y,6.61),.22,'panel',24)
    for j in range(6):
        a = j*math.tau/6
        outline = [(.20,-.07,6.48),(.51,-.13,6.54),(.91,.01,6.54),(.87,.21,6.42),(.42,.16,6.43)]
        vertices = []
        for dz in (-.025,.025):
            for r,t,z in outline:
                p = Vector((x,y,0))+radial(a,r,z+dz,t)
                vertices.append(p)
        faces = [tuple(reversed(range(5))),tuple(range(5,10))]
        faces += [(j,(j+1)%5,(j+1)%5+5,j+5) for j in range(5)]
        g.mesh('Pale profilee',vertices,faces,materials['edge'],.012)
    g.pivot(ctrl,(x,y,6.48))

thermal = module('Noyau thermique','15_noyau_thermique','thermal')
rod('Coeur emissif',(0,0,24.82),(0,0,25.44),.62,'magenta',48)
annulus('Couronne du coeur',25.22,.82,.65,.16,'magenta')
g.pivot(thermal,(0,0,25.2))
socket = g.control('VFX panache thermique',thermal)
socket.location = (0,0,.35)
socket['role'] = 'vfx_plume'

walkway = module('Passerelle de service','16_passerelle')
xmin,xmax,ymin,ymax,z = -6.3,-2.1,-2.2,.4,13.25
for y in (ymin,ymax):
    beam('Rive passerelle',(xmin,y,z),(xmax,y,z),.18,.20,'armor')
for x in (xmin,xmax):
    beam('Traverse passerelle',(x,ymin,z),(x,ymax,z),.18,.20,'armor')
for j in range(27):
    x = xmin+(xmax-xmin)*j/26
    box('Caillebotis',(x,(ymin+ymax)/2,z+.045),(.045,ymax-ymin,.06),'edge',.004)
for j in range(13):
    y = ymin+(ymax-ymin)*j/12
    box('Traverse caillebotis',((xmin+xmax)/2,y,z+.04),(xmax-xmin,.027,.065),'edge',.004)
for y in (ymin,ymax):
    box('Plinthe passerelle',((xmin+xmax)/2,y,z+.15),(xmax-xmin,.06,.22),'panel',.015)
    for j in range(5):
        x = xmin+(xmax-xmin)*j/4
        rod('Montant garde corps',(x,y,z+.08),(x,y,z+1.2),.035,'edge',8)
    for dz in (.65,1.17):
        rod('Lisse garde corps',(xmin,y,z+dz),(xmax,y,z+dz),.032,'edge',8)
for dz in (.65,1.17):
    rod('Retour garde corps',(xmin,ymin,z+dz),(xmin,ymax,z+dz),.032,'edge',8)
for x in (xmin+.2,xmax-.2):
    marker('Balise passerelle',(x,ymin-.10,z),(.23,.045,.13))
for y in (ymin+.3,ymax-.3):
    beam('Console passerelle',(xmin+.35,y,z-.12),(-2.4,y,z-1.9),.16,.19,'armor')
socket = g.control('Socket passerelle',walkway)
socket.location = (xmin,(ymin+ymax)/2,z+.08)
socket['role'] = 'walkway_interface'

def consolidate(control):
    """Bake small construction parts into one editable modular mesh, preserving UVs."""
    pieces = [obj for obj in control.children if obj.type in ('MESH','CURVE','FONT')]
    bpy.ops.object.select_all(action='DESELECT')
    for obj in pieces:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.convert(target='MESH')
    pieces = [obj for obj in control.children if obj.type == 'MESH']
    for obj in pieces:
        bpy.context.view_layer.objects.active = obj
        for modifier in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        # Converted curve/font caps can retain disconnected border vertices.
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
        bm.to_mesh(obj.data)
        bm.free()
        g.uv_map(obj)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in pieces:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = control['module_slug']
    obj.data.name = obj.name+' | Mesh'
    obj['module_slug'] = control['module_slug']
    # Join can retain unneeded repeated material slots; consolidate identical slots.
    unique = []
    lookup = {}
    for index, mat in enumerate(obj.data.materials):
        if mat not in unique:
            unique.append(mat)
        lookup[index] = unique.index(mat)
    indices = [lookup[p.material_index] for p in obj.data.polygons]
    obj.data.materials.clear()
    for mat in unique:
        obj.data.materials.append(mat)
    for face, index in zip(obj.data.polygons, indices):
        face.material_index = index
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    if 'rig_name' in control:
        modifier = obj.modifiers.new('Capots independants','ARMATURE')
        modifier.object = bpy.data.objects[control['rig_name']]
        obj['panel_surface'] = True
    return obj

for control in modules.values():
    consolidate(control)
# Attachments retain their world placement when assigning useful reusable pivots.
for slug,location in {
    '02_section_centrale':(0,0,1.35),
    '03_diffuseur':(0,0,17.1),
    '08_panneaux_techniques':(0,0,5.85),
    '09_conduites':(0,0,1.9),
    '10_carters_ventilation':(0,0,2.35),
    '16_passerelle':(-2.1,-.9,13.25),
}.items():
    g.pivot(modules[slug],location)
create_clips(list(asset.objects))
for obj in asset.objects:
    if obj.type == 'EMPTY':
        obj.empty_display_size = .25
assert len([obj for obj in asset.objects if obj.type == 'MESH']) == 16
studio.setup(scene)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
print('BUILD COMPLETE',len(asset.objects),'objects, 16 modular meshes',flush=True)
