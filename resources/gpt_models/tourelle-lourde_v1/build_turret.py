"""Long Cortege heavy citadel turret: reference-inspired geometry and rigid recoil rig."""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT))
from geometry import box, line, mesh, pivot, plate, ring, rod, text
from surface_maps import bake_maps

bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
asset=bpy.data.collections.new('LC | TOURELLE LOURDE')
scene.collection.children.link(asset)
bpy.context.view_layer.active_layer_collection=bpy.context.view_layer.layer_collection.children[asset.name]


def material(name,color,metal=.65,rough=.4,emission=0):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*color,1)
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(*color,1)
    bsdf.inputs['Metallic'].default_value=metal
    bsdf.inputs['Roughness'].default_value=rough
    if emission:
        bsdf.inputs['Emission Color'].default_value=(*color,1)
        bsdf.inputs['Emission Strength'].default_value=emission
    return mat


armor=material('LC | dark weathered armor',(.075,.065,.065),.64,.43)
panel=material('LC | warm graphite panels',(.11,.095,.09),.6,.47)
recess=material('LC | deep graphite recesses',(.009,.011,.014),.65,.46)
edge=material('LC | rubbed titanium edges',(.22,.21,.20),.77,.41)
steel=material('LC | recoil piston steel',(.32,.34,.37),.88,.23)
bore=material('LC | unlit bore interior',(.001,.001,.001),0,1)
magenta=material('LC | restrained magenta energy',(.68,.008,.48),.22,.3,4)
amber=material('LC | serial markings',(.40,.30,.17),.3,.47)


def sector(name,start,end,profile,mat):
    """Closed annular sector, with a radial/height cross-section."""
    vertices=[]
    steps=3
    for i in range(steps+1):
        angle=start+(end-start)*i/steps
        vertices.extend((r*math.cos(angle),r*math.sin(angle),z) for r,z in profile)
    width=len(profile)
    faces=[tuple(range(width-1,-1,-1)),tuple(range(steps*width,(steps+1)*width))]
    for i in range(steps):
        for j in range(width):
            faces.append((i*width+j,i*width+(j+1)%width,(i+1)*width+(j+1)%width,(i+1)*width+j))
    return mesh(name,vertices,faces,mat,.012)


def vertical_ring(name,outer,inner,z,depth,mat):
    return sector(name,0,math.tau,[(inner,z),(outer,z),(outer,z+depth),(inner,z+depth)],mat)


def cylinder_z(name,radius,z0,z1,mat,vertices=64):
    return rod(name,(0,0,z0),(0,0,z1),radius,mat,vertices=vertices)


def bevel_box(name,loc,dims,mat,bevel=.10):
    return box(name,loc,dims,mat,bevel)


# Wide, low, stepped anchor: 24 individually armored radial modules.
cylinder_z('BASE | anchor shadow',3.57,.03,.40,recess)
cylinder_z('BASE | structural drum',3.30,.32,.80,armor)
for i in range(24):
    a=math.tau*i/24
    b=math.tau*(i+1)/24
    sector(f'BASE | radial armor shoe {i:02}',a+.012,b-.012,
           [(2.78,.07),(3.62,.07),(3.62,.43),(3.37,.75),(2.86,.82),(2.78,.62)],armor)
    sector(f'BASE | top access panel {i:02}',a+.026,b-.026,
           [(2.92,.805),(3.34,.755),(3.36,.783),(2.92,.838)],panel)
    angle=(a+b)/2
    x,y=3.625*math.cos(angle),3.625*math.sin(angle)
    face=box(f'BASE | outer inset panel {i:02}',(x,y,.27),(.59,.042,.20),recess,.022)
    face.rotation_euler.z=angle-math.pi/2
    label=box(f'BASE | armor latch {i:02}',(x*1.004,y*1.004,.27),(.25,.045,.11),panel,.012)
    label.rotation_euler.z=angle-math.pi/2
    for radius in [2.99,3.28]:
        rod('BASE | fastening bolt',(radius*math.cos(angle),radius*math.sin(angle),.80),
            (radius*math.cos(angle),radius*math.sin(angle),.83),.033,edge,vertices=8)
    if i in [2,8,14,20]:
        glow=box('BASE | magenta status slit',(3.37*math.cos(angle),3.37*math.sin(angle),.79),
                 (.20,.047,.023),magenta,.007)
        glow.rotation_euler.z=angle-math.pi/2
cylinder_z('BASE | upper step',2.83,.74,.94,recess)
for i in range(32):
    a=math.tau*i/32+.009
    b=math.tau*(i+1)/32-.009
    sector('BASE | segmented inner track',a,b,[(2.32,.94),(2.77,.94),(2.69,1.07),(2.32,1.07)],panel)
cylinder_z('BASE | yaw bearing core',1.98,1.0,1.40,recess)
for z in [1.05,1.28,1.38]:
    # Full rings use enough angular sectors to remain circular.
    for i in range(24):
        sector('BASE | polished bearing race',math.tau*i/24,math.tau*(i+1)/24,
               [(1.94,z),(2.12,z),(2.12,z+.045),(1.94,z+.045)],edge)
base_objects=set(asset.objects)

# The yaw platform and broad rear armored body.
cylinder_z('HEAD | rotating pedestal',1.99,1.40,1.59,armor)
plate('HEAD | lower chamfered pan',[(-2.45,-1.3),(-2.18,-1.66),(2.18,-1.66),(2.45,-1.3),
      (2.45,1.90),(2.13,2.34),(-2.13,2.34),(-2.45,1.90)],1.89,.31,recess,.055)
bevel_box('HEAD | structural bridge',(0,.54,2.47),(4.56,3.10,1.40),recess,.19)
for side,tag in [(-1,'L'),(1,'R')]:
    x=side*1.38
    bevel_box(tag+' | armored rear block',(x,.78,3.04),(2.32,3.28,2.08),armor,.25)
    # Separate armor plates leave thin, deep joints with visible rubbed edges.
    for j,y in enumerate([-.30,.71,1.72]):
        bevel_box(tag+' | outer side armor',(side*2.55,y,3.04),(.18,.92,1.40),panel,.075)
        bevel_box(tag+' | side inset',(side*2.652,y,3.04),(.023,.66,1.11),armor,.043)
        for z in [2.60,3.47]:
            rod(tag+' | side armor fastener',(side*2.669,y-.25,z),(side*2.687,y-.25,z),.035,edge,vertices=8)
        line(tag+' | side panel worn border',[(side*2.675,y-.31,2.56),(side*2.675,y-.31,3.50),
              (side*2.675,y+.24,3.50)],.011,edge)
    for j,y in enumerate([-.42,.60,1.62]):
        bevel_box(tag+' | roof armor slab',(x,y,4.057),(1.92,.94,.18),panel,.075)
        bevel_box(tag+' | roof center inset',(x,y,4.161),(1.36,.64,.027),armor,.038)
        for dx in [-.77,.77]:
            box(tag+' | roof edge strap',(x+dx,y,4.174),(.055,.71,.045),edge,.012)
    # Front vertical cheek modules, bevelled like the reference.
    bevel_box(tag+' | frontal cheek',(side*2.20,-1.05,3.18),(.64,.40,1.41),armor,.13)
    box(tag+' | frontal cheek inset',(side*2.20,-1.268,3.12),(.38,.032,.87),recess,.05)
    line(tag+' | front cheek bright rim',[(side*2.43,-1.291,2.55),
         (side*2.43,-1.291,3.58),(side*2.04,-1.291,3.70)],.014,edge)
    # Rear equipment cassettes and low-profile cooling slats.
    bevel_box(tag+' | rear equipment cassette',(x,2.49,2.75),(1.68,.30,1.12),armor,.10)
    for i in range(7):
        box(tag+' | rear radiator slat',(x,2.671,2.35+i*.13),(1.32,.055,.047),edge,.009)
    line(tag+' | rear utility conduit',[(side*2.25,2.49,2.15),(side*2.42,2.25,1.86),
         (side*1.9,1.7,1.73)],.055,recess)

# Narrow central channel and small magenta energy optic, never a full glowing hull.
bevel_box('HEAD | center spine',(0,.70,3.54),(.51,3.08,.90),armor,.11)
bevel_box('HEAD | sensor bezel',(0,-1.04,3.51),(.66,.40,.72),recess,.09)
box('HEAD | sensor center glass',(0,-1.258,3.50),(.24,.030,.31),magenta,.04)
for x in [-.23,.23]:
    box('HEAD | magenta sensor slit',(x,-1.262,3.50),(.047,.03,.43),magenta,.008)
for y in [-.35,.24,.83,1.42]:
    box('HEAD | center spine armor',(0,y,4.005),(.48,.48,.10),panel,.035)
    box('HEAD | spine thin magenta indicator',(0,y,4.065),(.18,.045,.018),magenta,.005)
text('HEAD | serial','LC / CITADELLE / 03',(0,1.99,4.10),.105,edge)
head_objects=set(asset.objects)-base_objects
yaw=pivot('CTRL | Yaw 360',(0,0,1.42),head_objects)

# An independent elevation cradle, carried by the yaw ring.
before_pitch=set(asset.objects)
rod('CRADLE | transverse trunnion',(-2.35,-.91,2.72),(2.35,-.91,2.72),.32,recess,vertices=32)
for side,tag in [(-1,'L'),(1,'R')]:
    x=side*1.43
    bevel_box(tag+' | fixed recoil cradle',(x,-1.70,2.72),(1.46,1.96,1.28),armor,.16)
    bevel_box(tag+' | front recoil collar',(x,-2.64,2.72),(1.36,.27,1.13),edge,.10)
    bevel_box(tag+' | collar dark face',(x,-2.793,2.72),(1.13,.055,.89),recess,.085)
    for offset in [-1,1]:
        bevel_box(tag+' | cradle side hatch',(x+offset*.738,-1.70,2.74),(.042,1.18,.82),panel,.047)
        box(tag+' | cradle side hatch inset',(x+offset*.766,-1.70,2.74),(.015,.92,.58),armor,.022)
        for y in [-2.1,-1.3]:
            rod(tag+' | cradle hatch bolt',(x+offset*.77,y,3.02),
                (x+offset*.79,y,3.02),.03,edge,vertices=8)
    for y in [-2.1,-1.65,-1.2]:
        box(tag+' | cradle cooling groove',(x,y,3.372),(.67,.045,.019),recess,.004)
    for offset in [-.51,.51]:
        # Stationary cylinder body, with a moving piston fixed to the barrel slide.
        rod(tag+' | recoil cylinder',(x+offset,-2.35,2.96),(x+offset,-1.0,2.96),.095,recess)
        ring(tag+' | piston gland',(x+offset,-2.36,2.96),.12,.057,.12,edge)
    box(tag+' | cradle magenta inset',(x,-1.32,3.383),(.32,.48,.028),recess,.035)
    box(tag+' | cradle energy slit',(x,-1.32,3.408),(.067,.30,.012),magenta,.008)
pitch_roots=set(asset.objects)-before_pitch
pitch=pivot('CTRL | Elevation',(0,-.91,2.72),pitch_roots)
world=pitch.matrix_world.copy()
pitch.parent=yaw
pitch.matrix_world=world

recoils=[]
muzzles=[]
for side,tag in [(-1,'L'),(1,'R')]:
    x=side*1.43
    before=set(asset.objects)
    rod(tag+' | sliding barrel core',(x,-5.70,2.72),(x,-1.77,2.72),.325,recess,vertices=32)
    # Angular, stepped barrel jackets lead into the exposed circular muzzle.
    for j,(y,length,width,height) in enumerate([(-3.15,1.05,1.05,.91),(-4.02,.71,.88,.76),
                                               (-4.67,.56,.70,.62)]):
        bevel_box(tag+f' | barrel armor jacket {j}',(x,y,2.72),(width,length,height),armor,.105)
        box(tag+' | barrel jacket roof plate',(x,y,2.72+height/2+.014),(width*.73,length*.73,.045),panel,.036)
        for offset in [-1,1]:
            line(tag+' | jacket edge highlight',[(x+offset*width*.39,y-length*.36,2.72+height*.44),
                 (x+offset*width*.39,y+length*.36,2.72+height*.44)],.012,edge)
            box(tag+' | jacket side access plate',(x+offset*(width/2+.01),y,2.72),
                (.035,length*.61,height*.49),panel,.027)
            box(tag+' | jacket locking tab',(x+offset*(width/2+.033),y,2.72),
                (.018,.15,.14),edge,.017)
    ring(tag+' | exposed forward barrel',(x,-5.535,2.72),.31,.24,1.37,armor)
    for y in [-5.12,-5.74,-6.21]:
        ring(tag+' | muzzle reinforcing band',(x,y,2.72),.352,.284,.12,edge)
    # A real hollow muzzle with internal lining and a dark recessed bore.
    ring(tag+' | hollow muzzle lip',(x,-6.38,2.72),.361,.263,.17,edge)
    ring(tag+' | rifled bore lining',(x,-6.15,2.72),.269,.24,.53,recess)
    rod(tag+' | recessed dark bore',(x,-5.875,2.72),(x,-5.855,2.72),.24,bore,vertices=32)
    for offset in [-.51,.51]:
        rod(tag+' | sliding hydraulic piston',(x+offset,-3.00,2.96),(x+offset,-1.90,2.96),.054,steel)
    muzzle=pivot('MARKER | '+tag+' muzzle',(x,-6.47,2.72),[])
    muzzles.append(muzzle)
    recoil=pivot('CTRL | '+tag+' recoil',(x,-2.15,2.72),set(asset.objects)-before)
    world=recoil.matrix_world.copy()
    recoil.parent=pitch
    recoil.matrix_world=world
    recoils.append(recoil)

# Small visible center energy coupling between the two barrel cradles.
before=set(asset.objects)
rod('CRADLE | center power feed',(0,-2.26,3.08),(0,-1.08,3.08),.12,recess)
ring('CRADLE | center magenta coupling',(0,-1.85,3.08),.19,.14,.14,magenta)
rod('CRADLE | center energy lens',(0,-2.29,3.08),(0,-2.26,3.08),.09,magenta)
for obj in set(asset.objects)-before:
    world=obj.matrix_world.copy()
    obj.parent=pitch
    obj.matrix_world=world

# Portable UVs and actual texture maps on the armor. Edge lines remain geometry.
bpy.ops.object.select_all(action='DESELECT')
for obj in asset.objects:
    if obj.type in {'MESH','CURVE','FONT'}:
        obj.select_set(True)
bpy.context.view_layer.objects.active=next(obj for obj in asset.objects if obj.type=='MESH')
bpy.ops.object.convert(target='MESH')
for obj in asset.objects:
    if obj.type!='MESH':
        continue
    uv=obj.data.uv_layers.get('UVMap') or obj.data.uv_layers.new(name='UVMap')
    for face in obj.data.polygons:
        normal=obj.matrix_world.to_3x3() @ face.normal
        dominant=max(range(3),key=lambda axis:abs(normal[axis]))
        axes=[axis for axis in range(3) if axis!=dominant]
        for index in face.loop_indices:
            point=obj.matrix_world @ obj.data.vertices[obj.data.loops[index].vertex_index].co
            uv.data[index].uv=(point[axes[0]]/1.65,point[axes[1]]/1.65)
albedo=bpy.data.images.load(str(OUT/'textures/gunmetal_albedo.png'))
albedo.pack()
maps=bake_maps(albedo,OUT/'textures')
for mat,factor in [(armor,(.76,.78,.83,1)),(panel,(.99,.94,.91,1))]:
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    bsdf=nodes.get('Principled BSDF')
    texture=nodes.new('ShaderNodeTexImage')
    texture.image=albedo
    multiply=nodes.new('ShaderNodeMixRGB')
    multiply.blend_type='MULTIPLY'
    multiply.inputs[0].default_value=1
    multiply.inputs[2].default_value=factor
    links.new(texture.outputs['Color'],multiply.inputs[1])
    links.new(multiply.outputs[0],bsdf.inputs['Base Color'])
    roughness=nodes.new('ShaderNodeTexImage')
    roughness.image=maps['roughness']
    links.new(roughness.outputs['Color'],bsdf.inputs['Roughness'])
    normal=nodes.new('ShaderNodeTexImage')
    normal.image=maps['normal']
    normal_map=nodes.new('ShaderNodeNormalMap')
    links.new(normal.outputs['Color'],normal_map.inputs['Color'])
    links.new(normal_map.outputs[0],bsdf.inputs['Normal'])

# Demonstration: aim, alternate shots, then a synchronized two-barrel salvo.
scene.frame_start=1
scene.frame_end=240
scene.render.fps=30
for obj,axis,poses in [(yaw,2,[(1,0),(25,0),(55,-22),(105,-22),(135,20),(175,20),(215,0),(240,0)]),
                       (pitch,0,[(1,0),(25,0),(55,-13),(105,-13),(135,-22),(175,-22),(215,0),(240,0)])]:
    for frame,angle in poses:
        obj.rotation_euler[axis]=math.radians(angle)
        obj.keyframe_insert(data_path='rotation_euler',frame=frame)

shot_frames={'L':[66,90,150,166,224],'R':[77,101,150,166,224]}
for obj,tag in zip(recoils,['L','R']):
    rest=obj.location.y
    keys={1:0,240:0}
    for fire in shot_frames[tag]:
        keys.update({fire-1:0,fire+1:.56,fire+4:.40,fire+11:0})
    for frame,travel in sorted(keys.items()):
        obj.location.y=rest+travel
        obj.keyframe_insert(data_path='location',frame=frame)
    obj['recoil_travel_m']=.56
    obj['operation']='Rigid barrel translates along local +Y. No mesh scaling.'

for frame,label in [(1,'REST'),(55,'AIM'),(66,'FIRE LEFT'),(77,'FIRE RIGHT'),
                    (150,'DUAL SALVO'),(215,'RETURN'),(224,'FRONT SALVO')]:
    scene.timeline_markers.new(label,frame=frame)
scene.frame_set(1)

# Studio and cameras are isolated from the exported asset.
studio=bpy.data.collections.new('STUDIO | not exported')
scene.collection.children.link(studio)
bpy.context.view_layer.active_layer_collection=bpy.context.view_layer.layer_collection.children[studio.name]
floor_mat=material('STUDIO | midnight floor',(.006,.012,.019),.22,.55)
box('STUDIO | floor',(0,0,-.09),(200,200,.13),floor_mat,0)
for name,location,power,size,color in [
    ('Key',(2,-7,12),2600,8,(.87,.93,1)),('Warm fill',(-8,-3,7),2400,7,(1,.83,.71)),
    ('Rim',(3,7,9),3300,6,(.70,.77,1)),('Front',(0,-11,6),1200,5,(1,.90,.85))]:
    data=bpy.data.lights.new('STUDIO | '+name,'AREA')
    data.energy=power
    data.shape='DISK'
    data.size=size
    data.color=color
    obj=bpy.data.objects.new(data.name,data)
    studio.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector((0,-.5,1.7))-obj.location).to_track_quat('-Z','Y').to_euler()


def camera(name,location,target,scale):
    data=bpy.data.cameras.new(name)
    data.type='ORTHO'
    data.ortho_scale=scale
    obj=bpy.data.objects.new(name,data)
    studio.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj


hero=camera('CAM | reference three-quarter',(11,-14,10),(0,-.8,1.65),13.7)
top=camera('CAM | top',(0,-1.25,22),(0,-1.25,0),14.3)
top.rotation_euler.z=math.pi
front=camera('CAM | front',(0,-20,5.4),(0,-.9,1.9),11.5)
side=camera('CAM | side',(18,-1.3,4.8),(0,-1.3,1.9),12.9)
scene.camera=hero
scene.unit_settings.system='METRIC'
scene.render.engine='CYCLES'
scene.cycles.samples=40
scene.cycles.use_denoising=True
scene.render.resolution_x=1500
scene.render.resolution_y=1125
scene.world=bpy.data.worlds.new('World')
scene.world.color=(.065,.065,.065)
scene.view_settings.view_transform='AgX'
compositor=bpy.data.node_groups.new('LC | restrained energy bloom','CompositorNodeTree')
scene.compositing_node_group=compositor
compositor.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
nodes=compositor.nodes
layers=nodes.new('CompositorNodeRLayers')
glare=nodes.new('CompositorNodeGlare')
glare.inputs['Type'].default_value='Fog Glow'
glare.inputs['Threshold'].default_value=2
glare.inputs['Quality'].default_value='High'
glare.inputs['Strength'].default_value=.22
output=nodes.new('NodeGroupOutput')
compositor.links.new(layers.outputs['Image'],glare.inputs['Image'])
compositor.links.new(glare.outputs['Image'],output.inputs['Image'])
reference=bpy.data.images.load(str(OUT/'reference.png'))
reference.name='REFERENCE | supplied turret concept sheet'
reference.pack()
bpy.ops.object.select_all(action='DESELECT')
for obj in asset.objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active=yaw
bpy.ops.export_scene.gltf(filepath=str(OUT/'tourelle_lourde.glb'),use_selection=True,
    export_format='GLB',export_apply=True,export_animations=True,export_animation_mode='SCENE',
    export_frame_range=True,export_force_sampling=True,export_anim_scene_split_object=False,export_extras=True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=16
            area.spaces.active.region_3d.view_location=(0,-.7,1.8)
            area.spaces.active.region_3d.view_rotation=hero.rotation_euler.to_quaternion()
            area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'tourelle_lourde.blend'))
jobs=[(hero,1,'hero'),(top,1,'top'),(front,1,'front'),(side,1,'side'),(hero,151,'recoil')]
if '--model-only' in sys.argv:
    jobs=[]
if '--preview' in sys.argv:
    scene.cycles.samples=16
    scene.render.resolution_percentage=65
    jobs=jobs[:1]
for cam,frame,name in jobs:
    scene.camera=cam
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/f'tourelle_lourde_{name}.png')
    bpy.ops.render.render(write_still=True)
print('TURRET BUILD COMPLETE',flush=True)
