"""Twelve modular meshes for the 24 m stern service pylon, with skeletal louvers."""
import math
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector

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
root = g.control('Pylone technique 07')
root['asset_number'] = '07/10'
root['dimensions_reference_xyz_m'] = [12, 9, 24]
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


base = module('Socle', '01_socle')
column('Socle octogonal', [(0,12,9),(.5,12,9),(.8,11.5,8.5),(1.15,10.5,7.5)], 'armor')
for x in (-4.8,-2.4,0,2.4,4.8):
    for y in (-3.1,3.1):
        box('Tuile ancrage', (x,y,1.13),(2.2,1.25,.22),'panel',.07)
        for dx in (-.8,.8):
            rod('Goujon socle',(x+dx,y,1.25),(x+dx,y,1.36),.095,'edge',6)
for x in (-4.7,-1.6,1.6,4.7):
    marker('Balise socle',(x,-4.27,.61),(1.0,.055,.12))
for x in (-4.5,4.5):
    box('Bloc interface sol',(x,0,1.6),(1.2,2.2,.85),'armor',.1)
    for y in (-.7,.7):
        ring_z('Interface verticale',x,y,2.1,.32,.18)

core = module('Module central', '02_module_central')
column('Ossature centrale', [(1.15,5.1,4.25),(3.6,4.8,4),(5.2,3.7,3.2),
                             (13.8,3.6,3.15),(15.1,3,2.7),(20.3,2.65,2.35)],'dark')
for sign in (-1,1):
    for z,height,width,depth in [(3.1,3.4,3.7,2.1),(7.1,3.4,2.95,1.65),(10.7,3.4,2.95,1.65),
                                (14.2,2.8,2.65,1.57),(17.45,3.6,2.1,1.23),(19.8,.65,2.1,1.23)]:
        y = sign*depth
        box('Plaque blindage centrale',(0,y,z),(width,.19,height),'armor',.12)
        box('Insert carbone',(0,y+sign*.108,z+.07),(width*.72,.04,height*.76),'carbon',.04)
        for x in (-width*.45,width*.45):
            box('Longeron de capot',(x,y+sign*.13,z),(.10,.09,height*.88),'edge',.018)
            for dz in (-height*.39,height*.39):
                rod('Vis capot',(x,y+sign*.17,z+dz),(x,y+sign*.23,z+dz),.06,'bronze',6)
        if sign < 0:
            marker('Temoin maintenance',(.65,-depth-.15,z-height*.35),(.44,.04,.09))
for side in (-1,1):
    for y in (-1.05,1.05):
        pipe('Conduite interne',[(side*1.5,y,2),(side*1.8,y,4),(side*1.78,y,13),(side*1.23,y,16),(side*1.15,y,20)],.18)
    for z in (5.4,8.9,12.5,16.2,19.2):
        box('Traverse de colonne',(side*1.74,0,z),(.30,2.1,.19),'panel',.03)
# The sole stencil allowed by the board is subtle and belongs to the fixed core.
font = bpy.data.curves.new('Repere 07','FONT')
font.body = '07'
font.align_x = 'CENTER'
font.size = .9
font.extrude = .003
text = bpy.data.objects.new('Repere discret 07',font)
asset.objects.link(text)
text.parent = core
text.location = (0,-1.81,9.85)
text.rotation_euler.x = math.pi/2
font.materials.append(materials['edge'])
# Rear service ladder: 0.55 m clear width, 0.30 m rung spacing.
for x in (-.36,.36):
    rod('Montant echelle',(x,1.92,1.3),(x,1.92,17),.04,'edge')
for i in range(52):
    z = 1.45+i*.3
    rod('Barreau echelle',(-.36,1.92,z),(.36,1.92,z),.026,'edge',8)

crown = module('Couronne de refroidissement', '03_couronne', 'crown')
column('Tour superieure',[(20,2.55,2.3),(20.5,2.5,2.3),(22.6,1.9,1.8),(23.15,1.35,1.3)],'armor')
for x in (-.77,.77):
    box('Ailette sommitale',(x,0,21.5),(.23,1.63,2.7),'panel',.075)
    marker('Ligne sommet',(x,-.93,21.45),(.09,.035,1.65))
marker('Balise couronne',(0,-1.2,20.35),(1,.06,.16))
rod('Embase antenne',(0,0,23.1),(0,0,23.45),.22,'dark',16)
rod('Antenne',(0,0,23.4),(0,0,23.9),.055,'edge')
rod('Balise antenne',(0,0,23.9),(0,0,24),.055,'magenta')

supports = module('Renforts structurels', '04_renforts')
for side in (-1,1):
    for rear in (-1,1):
        a = (side*4.5,rear*2.3,1.35)
        b = (side*1.7,rear*1.0,14.9)
        beam('Renfort diagonal',a,b,.57,.64,'armor')
        beam('Raidisseur metallique',(a[0]+side*.23,a[1],a[2]+.3),(b[0]+side*.23,b[1],b[2]-.3),.10,.24,'edge')
        mid = Vector(a).lerp(Vector(b),.34)
        box('Noeud de renfort',mid,(.9,.88,1.0),'panel',.1)
        if rear < 0:
            marker('Indicateur renfort',(mid.x,mid.y-.46,mid.z),(.17,.05,.66))
        beam('Jambe inferieure',(side*4.6,rear*2.3,1.4),(side*2.3,rear*1.3,5.4),.4,.44,'dark')

for side, slug in [(-1,'05_conduites_gauche'),(1,'06_conduites_droite')]:
    control = module('Conduites '+str(side),slug,'coolant',side)
    for offset in (-.65,.65):
        x = side*(2.3+abs(offset)*.55)
        y = offset
        pipe('Collecteur vertical',[(x,y,1.7),(x,y,3),(side*2.3,y,4.4),(side*2.3,y,12.6),
                                    (side*2.3,y,14),(side*1.55,y,14.65)],.30)
        for z in (3,5.3,8.4,11.4,13.7):
            ring_z('Collier conduite',side*2.3 if z>3 else x,y,z,.37,.18)
    for j in range(2):
        x = side*(1.8+j*.9)
        pipe('Raccord moteur',[(x,-4.05,1.45),(x,-3.5,1.45),(x,-2.55,2.1),(side*2.5,-1.0,3.8),
                              (side*2.5,-.65,5.1)],.32 if j == 0 else .25)
        for y in (-3.85,-3.28):
            g.ring('Collier interface moteur',y,.40 if j == 0 else .33,.31 if j == 0 else .24,.17,materials['panel'],center=(x,1.45),count=20)
        socket = g.control('Socket moteur '+str(side)+' '+str(j),control)
        socket.location = (x,-4.05,1.45)
        socket['role'] = 'engine_interface'
    for z in (4.2,13.6):
        ring_z('Bague energie',side*2.3,-.65,z,.315,.14,'magenta')
    socket = g.control('VFX vapeur '+str(side),control)
    socket.location = (side*1.55,.65,14.65)
    socket['role'] = 'vfx_steam'

for side, number in [(-1,7),(1,8)]:
    housing = module('Bloc echangeur '+str(side),f'{number:02}_echangeur_'+('gauche' if side<0 else 'droit'))
    x = side*2.8
    box('Carter echangeur',(x,.95,7.2),(1.8,1.35,7.5),'dark',.18)
    for xx in (x-.8,x+.8):
        box('Cadre echangeur',(xx,.14,7.2),(.17,.23,7.8),'panel',.04)
    for z in (3.35,11.05):
        box('Capot echangeur',(x,.78,z),(1.9,1.75,.36),'armor',.07)
        marker('Etat echangeur',(x,-.17,z),(1.1,.035,.11))
    for j in range(14):
        z = 3.8+j*.49
        box('Ailette thermique fixe',(x,1.67,z),(1.45,.22,.16),'edge',.013)
    for z in (4.3,9.8):
        pipe('U refroidissement',[(x+.5,1.4,z),(x+.72,1.95,z),(x-.72,1.95,z),(x-.5,1.4,z)],.12)
    cover = module('Volets echangeur '+str(side),f'{number+2:02}_volets_'+('gauche' if side<0 else 'droit'))
    data = bpy.data.armatures.new('Articulation des lames '+str(side))
    rig = bpy.data.objects.new('CTRL | Lames thermiques '+str(side),data)
    asset.objects.link(rig)
    rig.parent = cover
    rig['mechanism'] = 'louvers'
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for j in range(14):
        z = 3.8+j*.49
        bone = data.edit_bones.new(f'LAME_{j:02}')
        bone.head = (x-.72,-.05,z)
        bone.tail = (x+.72,-.05,z)
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.select_set(False)
    for j in range(14):
        z = 3.8+j*.49
        obj = box('Lame orientable',(x,-.055,z),(1.42,.11,.36),'edge',.016)
        group = obj.vertex_groups.new(name=f'LAME_{j:02}')
        group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    cover['rig_name'] = rig.name


def walkway(name, xmin, xmax, ymin, ymax, z, slug):
    ctrl = module(name,slug)
    # Geometric open grating, perimeter beams, toe boards and 1.10 m guardrails.
    for y in (ymin,ymax):
        beam('Poutre de rive',(xmin,y,z),(xmax,y,z),.18,.22,'armor')
        box('Plinthe',( (xmin+xmax)/2,y,z+.16),(xmax-xmin,.07,.22),'panel',.018)
    for x in (xmin,xmax):
        beam('Traverse passerelle',(x,ymin,z),(x,ymax,z),.18,.18,'armor')
    nx = int((xmax-xmin)/.16)
    for i in range(nx+1):
        x = xmin+(xmax-xmin)*i/nx
        box('Caillebotis longitudinal',(x,(ymin+ymax)/2,z+.05),(.045,ymax-ymin,.06),'edge',.004)
    ny = int((ymax-ymin)/.22)
    for i in range(ny+1):
        y = ymin+(ymax-ymin)*i/ny
        box('Caillebotis transversal',((xmin+xmax)/2,y,z+.045),(xmax-xmin,.027,.065),'edge',.004)
    for y in (ymin,ymax):
        steps = math.ceil((xmax-xmin)/1.25)
        for i in range(steps+1):
            x = xmin+(xmax-xmin)*i/steps
            rod('Montant garde corps',(x,y,z+.1),(x,y,z+1.2),.035,'edge',8)
        for dz in (.66,1.17):
            rod('Lisse de garde corps',(xmin,y,z+dz),(xmax,y,z+dz),.032,'edge',8)
    for x in (xmin,xmax):
        for dz in (.66,1.17):
            rod('Retour garde corps',(x,ymin,z+dz),(x,ymax,z+dz),.032,'edge',8)
        marker('Feu passerelle',(x,ymin-.1,z-.05),(.22,.05,.14))
        rod('Balise garde corps',(x,ymin,z+1.18),(x,ymin,z+1.4),.06,'magenta',10)
    # Triangulated brackets reach the load-bearing tower.
    for x in (xmin+.5,xmax-.5):
        beam('Console passerelle',(x,(ymin+ymax)/2,z-.14),(max(-1.5,min(1.5,x)),0,z-1.7),.13,.18,'armor')
    for x in (xmin+.45,xmax-.45):
        socket = g.control('Socket passerelle '+slug+' '+str(x),ctrl)
        socket.location = (x,(ymin+ymax)/2,z+.1)
        socket['role'] = 'walkway_interface'


walkway('Passerelle basse',-5.65,1.6,-3.2,-1.9,8.4,'11_passerelle_basse')
walkway('Passerelle haute',1.35,5.65,-.4,1.6,15.8,'12_passerelle_haute')


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
        modifier = obj.modifiers.new('Lames independantes','ARMATURE')
        modifier.object = bpy.data.objects[control['rig_name']]
        obj['louver_surface'] = True
    return obj


for control in modules.values():
    consolidate(control)
g.pivot(crown,(0,0,20))
for slug, location in {
    '05_conduites_gauche': (-2.3,0,1.35),
    '06_conduites_droite': (2.3,0,1.35),
    '07_echangeur_gauche': (-2.8,.95,3.35),
    '08_echangeur_droit': (2.8,.95,3.35),
    '09_volets_gauche': (-2.8,-.05,3.8),
    '10_volets_droit': (2.8,-.05,3.8),
    '11_passerelle_basse': (-2.025,-2.55,8.4),
    '12_passerelle_haute': (3.5,.6,15.8),
}.items():
    g.pivot(modules[slug],location)
create_clips(list(asset.objects))
for obj in asset.objects:
    if obj.type == 'EMPTY':
        obj.empty_display_size = .25
assert len([obj for obj in asset.objects if obj.type == 'MESH']) == 12
studio.setup(scene)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
print('BUILD COMPLETE',len(asset.objects),'objects, 12 modular meshes',flush=True)
