"""Build Spectre 9-D from the supplied concept and local editable parameters. Blender 5.2."""
import json
import math
import sys
import uuid
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from paths import ASSETS, BLENDER, VERSION
from geometry import box, clip_polygon, control, curve, label, loft, mesh, panel, parent_keep_world, project_uv, rod, tube
from materials import make_materials, material

config = json.loads((VERSION/'parameters.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1
asset = bpy.data.collections.new('S9D | Aircraft')
scene.collection.children.link(asset)
bpy.context.view_layer.active_layer_collection=bpy.context.view_layer.layer_collection.children[asset.name]
m = make_materials(config)
root = control('CTRL | Aircraft')
root['wing_sweep_deg']=0.0
root['nozzle_extension_m']=0.0
root.id_properties_ui('wing_sweep_deg').update(min=0,max=35,description='Symmetrical wing sweep. 0 = maneuver; cruise and interception are defined in parameters.json.')
root.id_properties_ui('nozzle_extension_m').update(min=0,max=.8,description='Rigid telescopic nozzle extension in meters.')
root['canopy']='Fixed: no hinge, no opening animation'
modules = {}


def module(name):
    collection=bpy.data.collections.new('MODULE | '+name)
    asset.children.link(collection)
    layer=bpy.context.view_layer.layer_collection.children[asset.name].children[collection.name]
    bpy.context.view_layer.active_layer_collection=layer
    modules[name]=collection
    return collection


def attach_module(collection,parent):
    for obj in list(collection.objects):
        if obj != parent and obj.parent is None:
            parent_keep_world(obj,parent)


# Long, narrow faceted central hull: nose -Y, twin engines aft (+Y).
hull=module('Fuselage')
sections=[(-6.3,.025,-.20,.025,.025),(-5.8,.24,-.14,.13,.15),
          (-4.85,.54,-.05,.30,.31),(-3.55,.77,.02,.48,.46),
          (-2.10,.84,.025,.52,.55),(-.4,.90,.01,.53,.92),
          (1.5,1.04,-.02,.52,1.00),(3.4,1.0,-.035,.50,.90),
          (5.15,.71,-.12,.32,.42),(5.75,.34,-.17,.17,.26)]
hull_core=loft('HULL | continuous editable fuselage',sections,m['dark'])
# Faceted armor follows the underlying loft. Editable gaps remain real geometry.
for row in range(len(sections)-1):
    for column in range(12):
        indices=[row*12+column,row*12+(column+1)%12,(row+1)*12+(column+1)%12,(row+1)*12+column]
        points=[hull_core.data.vertices[index].co.copy() for index in indices]
        center=sum(points,Vector())/4
        points=[center+(point-center)*.966 for point in points]
        for point in points:
            point.z += .014 if column<6 else -.014
        obj=mesh(f'HULL | fitted armor {row:02}-{column:02}',points,[(0,1,2,3)],m['white'],.006)
        obj.modifiers.new('Editable skin thickness','SOLIDIFY').thickness=.018

# Distinct dorsal blue spine remains visible around the fixed canopy.
panel('HULL | forward cobalt nose accent',[(-.10,-5.48),(.10,-5.48),(.27,-4.72),(-.27,-4.72)],
      lambda x,y:-.02+(y+5.48)*.27,m['blue'],.018)
panel('HULL | rear cobalt spine',[(-.33,-.28),(.33,-.28),(.32,2.5),(-.32,2.5)],
      lambda x,y:.57,m['blue'],.018)
# Nose panels follow a piecewise upper fuselage profile.
def hull_top(x,y):
    for a,b in zip(sections,sections[1:]):
        if a[0]<=y<=b[0]:
            t=(y-a[0])/(b[0]-a[0])
            width=a[1]*(1-t)+b[1]*t
            center=a[2]*(1-t)+b[2]*t
            up=a[3]*(1-t)+b[3]*t
            return center+up*math.sqrt(max(0,1-(x/max(width,.01))**2))+.017
    return .3
for side,tag in [(-1,'L'),(1,'R')]:
    for j,(y0,y1,w0,w1) in enumerate([(-5.80,-5.19,.19,.34),(-5.14,-4.59,.35,.54),(-4.54,-3.91,.53,.64)]):
        outline=[(side*.09,y0),(side*w0,y0),(side*w1,y1),(side*.16,y1)]
        panel(tag+' | nose armor '+str(j),outline,hull_top,m['white'])
    curve(tag+' | scarlet nose pinstripe',[(side*.32,-5.2,.13),(side*.48,-4.4,.25),
          (side*.64,-3.7,.31)],.024,m['red'])
    # Broad fixed wing-root fairings connect hull to the adaptive wings.
    outline=[(side*.59,-3.40),(side*1.08,-2.44),(side*1.73,.02),
             (side*1.90,3.6),(side*.83,4.24)]
    panel(tag+' | fixed wing-root fairing',outline,lambda x,y:.09+.03*y,m['white'],.20)
    panel(tag+' | root blue stripe',[(side*.8,-1.6),(side*1.16,-.92),(side*1.62,2.7),
          (side*1.27,2.81)],lambda x,y:.13+.03*y,m['blue'])
    # Intake cavities and grilles, ahead of each engine shoulder.
    panel(tag+' | intake surround',[(side*.95,-1.20),(side*1.46,-.59),(side*1.65,.62),
          (side*1.04,.17)],lambda x,y:.42+.035*y,m['blue'],.14)
    panel(tag+' | recessed thermal intake',[(side*1.08,-.76),(side*1.39,-.39),
          (side*1.49,.34),(side*1.13,.09)],lambda x,y:.446+.035*y,m['dark'])
    for j in range(5):
        y=-.4+j*.125
        curve(tag+' | intake grille '+str(j),[(side*1.15,y,.47),(side*1.39,y+.15,.48)],.018,m['metal'])
    for y in [-2.6,2.05]:
        tube(tag+' | RCS nozzle '+str(y),(side*.94,y,-.15),[(-.10,.075),(.10,.12),(.10,.06),(-.10,.055)],m['dark'],16)
    panel(tag+' | ventral access panel',[(side*.25,-2.0),(side*.62,-1.5),(side*.64,2.1),
          (side*.27,2.4)],lambda x,y:-.60,m['metal'],.02)
tube('HULL | nose optical sensor',(0,-6.12,-.15),[(-.025,.045),(.025,.045),(.025,.025),(-.025,.025)],m['dark'],16)
label('HULL | identification',config['name'],(0,2.0,.59),.15,m['black'])
attach_module(hull,root)

# Fixed smoked glass crown, lofted independently with longitudinal bronze framing.
canopy=module('Fixed canopy')
canopy_sections=[(-4.66,.025,.23,.025,.015),(-4.19,.35,.40,.29,.04),
                 (-3.47,.58,.48,.53,.04),(-2.48,.65,.50,.68,.04),
                 (-1.46,.57,.51,.55,.04),(-.72,.38,.51,.32,.04),(-.43,.09,.50,.045,.025)]
glazing=loft('CANOPY | fixed smoked glazing',canopy_sections,m['glass'],24)
for face in glazing.data.polygons:
    face.use_smooth=True
for side,tag in [(-1,'L'),(1,'R')]:
    curve(tag+' | canopy sill bronze',[(side*w,y,z+.016) for y,w,z,up,down in canopy_sections],.026,m['bronze'])
    curve(tag+' | canopy longitudinal frame',[(side*w*.72,y,z+up*.70) for y,w,z,up,down in canopy_sections],.017,m['bronze'])
for j in [1,2,4,5]:
    y,w,z,up,down=canopy_sections[j]
    curve('CANOPY | fixed transverse frame '+str(j),[(w*math.cos(a),y,z+up*math.sin(a))
          for a in [i*math.pi/20 for i in range(21)]],.022,m['bronze'])
attach_module(canopy,root)

# Wings: original delta outline with separated clipped armor panels and broad livery.
wing_controls=[]
wing_outline=[(1.0,-2.48),(1.68,-.76),(4.45,3.02),(4.40,3.80),(2.22,3.03),(1.02,3.38)]
for side,tag in [(-1,'L'),(1,'R')]:
    wing=module('Wing '+tag)
    pivot=control('CTRL | Wing '+tag,(side*1.0,-2.48,.05),root)
    wing_controls.append(pivot)
    outline=[(side*x,y) for x,y in wing_outline]
    def wing_z(x,y):
        return .065+.092*(abs(x)-1.0)
    panel(tag+' | editable delta wing core',outline,wing_z,m['dark'],.15)
    # Individual armor plates with narrow real joints, not painted fake relief.
    for row in range(9):
        y0=-2.5+row*.73
        for col in range(5):
            x0=.94+col*.75+(row%2)*.18
            poly=wing_outline[:]
            for axis,bound,greater in [(0,x0,True),(0,x0+.734,False),(1,y0,True),(1,y0+.714,False)]:
                if poly:
                    poly=clip_polygon(poly,axis,bound,greater)
            if len(poly)<3:
                continue
            outline=[(side*x,y) for x,y in poly]
            panel(f'{tag} | wing armor {row:02}-{col:02}',outline,
                  lambda x,y:wing_z(x,y)+.034,m['white'],.035)
    blue=[(1.32,-.92),(1.62,-.28),(3.89,2.95),(3.18,2.65),(1.44,.58)]
    panel(tag+' | angular cobalt wing flash',[(side*x,y) for x,y in blue],
          lambda x,y:wing_z(x,y)+.078,m['blue'],.02)
    panel(tag+' | cobalt trailing edge',[(side*x,y) for x,y in [(2.14,2.77),(4.24,3.43),(4.20,3.63),(2.12,3.0)]],
          lambda x,y:wing_z(x,y)+.072,m['blue'],.022)
    panel(tag+' | red wingtip warning',[(side*x,y) for x,y in [(4.23,2.87),(4.45,3.02),(4.40,3.80),(4.20,3.73)]],
          lambda x,y:wing_z(x,y)+.075,m['red'])
    label(tag+' | wing number','09',(side*3.02,2.40,wing_z(side*3.02,2.4)+.087),.52,m['black'],(0,side*.092,math.pi))
    # Aegis-style three-prong insignia, built as editable native geometry.
    for poly in [[(0,-.20),(-.19,.17),(-.055,.08)],[(0,-.20),(.19,.17),(.055,.08)],
                 [(-.12,.20),(0,.105),(.12,.20),(0,.165)]]:
        panel(tag+' | alliance insignia',[(side*(2.34+x),1.79+y) for x,y in poly],
              lambda x,y:wing_z(x,y)+.084,m['blue'],.008)
    # Fine warning accents and maintenance fasteners reinforce the reference livery.
    panel(tag+' | inboard red warning chevron',[(side*x,y) for x,y in [(1.82,.36),(2.08,.70),(2.00,.88),(1.76,.55)]],
          lambda x,y:wing_z(x,y)+.087,m['red'],.012)
    for px,py in [(1.7,1.1),(2.0,2.5),(3.76,3.15),(2.65,1.7)]:
        for dx in [-.075,.075]:
            rod(tag+' | wing access fastener',(side*(px+dx),py,wing_z(side*px,py)+.042),
                (side*(px+dx),py,wing_z(side*px,py)+.052),.016,m['metal'],count=8)
    # Outboard laser and one missile under each adaptive wing.
    gunx=side*2.24
    rod(tag+' | laser receiver',(gunx,.45,-.095),(gunx,1.80,-.095),.13,m['dark'])
    tube(tag+' | laser barrel',(gunx,.12,-.095),[(-.8,.079),(.4,.079),(.4,.047),(-.8,.047)],m['metal'],24)
    tube(tag+' | laser muzzle',(gunx,-.68,-.095),[(-.04,.096),(.06,.096),(.06,.049),(-.04,.049)],m['dark'],24)
    missilex=side*2.85
    box(tag+' | missile pylon',(missilex,1.80,-.03),(.11,.75,.34),m['metal'])
    rod(tag+' | missile body',(missilex,.86,-.37),(missilex,2.82,-.37),.12,m['white'])
    rod(tag+' | missile pointed nose',(missilex,.52,-.37),(missilex,.88,-.37),.015,m['red'],.12)
    for j in range(4):
        fin=box(tag+' | missile stabilizer '+str(j),(missilex,2.59,-.37),(.04,.39,.43),m['blue'],.009)
        fin.rotation_euler.y=j*math.pi/2
    attach_module(wing,pivot)
    driver=pivot.driver_add('rotation_euler',2).driver
    variable=driver.variables.new()
    variable.name='sweep'
    variable.targets[0].id=root
    variable.targets[0].data_path='["wing_sweep_deg"]'
    driver.expression=f'{side} * sweep * pi / 180'

# Twin engines: armored cylindrical housings, separate sliding nozzle assemblies.
nozzle_controls=[]
for side,tag in [(-1,'L'),(1,'R')]:
    x=side*config['engine_spacing_m']/2
    engine=module('Engine '+tag)
    tube(tag+' | engine structural shell',(x,0,.28),[(.45,.50),(1.0,.69),(4.75,.69),(5.58,.61),
         (5.58,.54),(.45,.42)],m['dark'],40)
    for j,(y0,y1) in enumerate([(.70,1.56),(1.64,2.64),(2.72,3.65),(3.74,4.68)]):
        # Four individual curved upper armor strips per longitudinal bay.
        for k in range(5):
            a0=.07+k*math.pi/5
            a1=(k+1)*math.pi/5-.07
            radius=.705
            verts=[(x+radius*math.cos(a),y,.28+radius*math.sin(a))
                   for y in [y0,y1] for a in [a0,(a0+a1)/2,a1]]
            obj=mesh(f'{tag} | nacelle armor {j}-{k}',verts,[(0,1,4,3),(1,2,5,4)],
                     m['blue'] if j in [0,3] else m['white'],.012)
            solid=obj.modifiers.new('Editable armor thickness','SOLIDIFY')
            solid.thickness=.045
    for y in [1.16,2.12,3.14,4.20]:
        box(tag+' | nacelle dorsal service plate',(x,y,1.004),(.45,.43,.025),m['blue'] if y==4.20 else m['white'],.028)
        for dx in [-.18,.18]:
            rod(tag+' | nacelle plate fastener',(x+dx,y-.14,1.015),(x+dx,y-.14,1.036),.018,m['metal'],count=8)
    for j in range(7):
        box(tag+' | engine heat exchanger',(x+side*.48,4.25+j*.065,.78),(.22,.024,.029),m['dark'],.006)
    for y in [1.62,2.69,3.70,4.76]:
        tube(tag+' | engine reinforcement band',(x,y,.28),[(-.045,.725),(.045,.725),(.045,.68),(-.045,.68)],m['metal'])
    # Outboard service hatch and coolant lines.
    box(tag+' | engine service hatch',(x+side*.67,3.18,.20),(.09,1.08,.42),m['blue'],.055)
    for z in [.0,.47]:
        curve(tag+' | armored coolant line',[(x+side*.63,1.44,z),(x+side*.75,2.0,z),
              (x+side*.75,3.84,z),(x+side*.64,4.36,z)],.033,m['metal'])
    attach_module(engine,root)
    nozzle=module('Nozzle '+tag)
    pivot=control('CTRL | Nozzle '+tag,(x,4.81,.28),root)
    nozzle_controls.append(pivot)
    tube(tag+' | nozzle telescopic sleeve',(x,0,.28),[(4.48,.55),(5.79,.55),(5.94,.62),(6.20,.62),
         (6.20,.47),(5.89,.44),(4.48,.44)],m['metal'],48)
    for y in [5.12,5.48,5.84,6.14]:
        tube(tag+' | nozzle dark expansion band',(x,y,.28),[(-.045,.59),(.045,.59),(.045,.54),(-.045,.54)],m['dark'])
    for k in range(12):
        a=k*math.tau/12
        verts=[]
        for y,r in [(5.73,.58),(6.22,.635)]:
            for da in [-.18,.18]:
                verts.append((x+r*math.cos(a+da),y,.28+r*math.sin(a+da)))
        obj=mesh(tag+' | nozzle petal '+str(k),verts,[(0,1,3,2)],m['dark'],.008)
        solid=obj.modifiers.new('Editable petal thickness','SOLIDIFY')
        solid.thickness=.026
    tube(tag+' | cyan exhaust rim',(x,6.205,.28),[(-.014,.495),(.014,.495),(.014,.455),(-.014,.455)],m['cyan'],48)
    rod(tag+' | deep ion chamber',(x,5.87,.28),(x,5.89,.28),.435,m['cyan'],count=48)
    rod(tag+' | hot central plasma',(x,5.88,.28),(x,5.90,.28),.22,m['hot'],count=32)
    control('MARKER | exhaust '+tag,(x,6.26,.28),pivot)
    attach_module(nozzle,pivot)
    driver=pivot.driver_add('location',1).driver
    variable=driver.variables.new()
    variable.name='extension'
    variable.targets[0].id=root
    variable.targets[0].data_path='["nozzle_extension_m"]'
    driver.expression='4.81 + extension'

# Two swept, outward-canted fins, independent editable modules attached to fixed hull.
for side,tag in [(-1,'L'),(1,'R')]:
    tail=module('Tail fin '+tag)
    profile=[(2.02,.40),(3.85,2.18),(4.81,2.18),(4.24,1.16),(5.30,.40)]
    verts=[(side*(1.16+.18*z)+dx,y,z) for dx in [-.045,.045] for y,z in profile]
    n=len(profile)
    mesh(tag+' | swept vertical stabilizer',verts,[tuple(range(n)),tuple(reversed(range(n,2*n)))] +
         [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],m['white'],.018)
    for dx in [-.051,.051]:
        poly=[(2.79,.61),(3.99,1.79),(4.48,1.79),(3.99,.93),(4.6,.61)]
        mesh(tag+' | fin cobalt flash',[(side*(1.16+.18*z)+dx,y,z) for y,z in poly],
             [tuple(range(len(poly)))],m['blue'],0)
        poly=[(3.85,2.10),(3.91,2.19),(4.80,2.19),(4.76,2.10)]
        mesh(tag+' | fin red tip',[(side*(1.16+.18*z)+dx,y,z) for y,z in poly],
             [tuple(range(len(poly)))],m['red'],0)
    attach_module(tail,root)

# Source UVs and asset-library entries remain editable; modifiers are never applied here.
bpy.context.view_layer.update()
for obj in asset.all_objects:
    if obj.type=='MESH':
        bm=bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        bm.to_mesh(obj.data)
        bm.free()
    project_uv(obj)
# Normalize the reference rest-state dimensions; configurable overall proportions.
corners = [obj.matrix_world @ Vector(corner) for obj in asset.all_objects
           if obj.type in {'MESH','CURVE','FONT'} for corner in obj.bound_box]
measured = [max(p[i] for p in corners)-min(p[i] for p in corners) for i in range(3)]
root.scale = (config['span_m']/measured[0], config['length_m']/measured[1], config['height_m']/measured[2])
bpy.context.view_layer.update()
asset.asset_mark()
asset.asset_data.description='Spectre 9-D: modular fixed-canopy interceptor. Append the complete collection for the rig.'
for collection in modules.values():
    collection['module_role']=collection.name
    collection.asset_mark()
    collection.asset_data.description='Editable component. Append the complete aircraft collection to preserve the complete flight rig.'
# The source root exposes a two-channel, easily editable demonstration action.
for frame,sweep,extension in [(1,0,0),(31,0,0),(76,config['wing_sweep_cruise_deg'],config['nozzle_cruise_extension_m']),
        (106,config['wing_sweep_cruise_deg'],config['nozzle_cruise_extension_m']),
        (151,config['wing_sweep_intercept_deg'],config['nozzle_intercept_extension_m']),
        (181,config['wing_sweep_intercept_deg'],config['nozzle_intercept_extension_m']),(241,0,0)]:
    root['wing_sweep_deg']=float(sweep)
    root['nozzle_extension_m']=float(extension)
    root.keyframe_insert(data_path='["wing_sweep_deg"]',frame=frame)
    root.keyframe_insert(data_path='["nozzle_extension_m"]',frame=frame)
root.animation_data.action.name='SOURCE | Flight state controls'
source_action=root.animation_data.action
source_action.asset_mark()
for name,a,b,frames in [
    ('Maneuver to Cruise',(0,0),(config['wing_sweep_cruise_deg'],config['nozzle_cruise_extension_m']),46),
    ('Cruise to Intercept',(config['wing_sweep_cruise_deg'],config['nozzle_cruise_extension_m']),
      (config['wing_sweep_intercept_deg'],config['nozzle_intercept_extension_m']),46),
    ('Intercept to Maneuver',(config['wing_sweep_intercept_deg'],config['nozzle_intercept_extension_m']),(0,0),61)]:
    root.animation_data.action=None
    for frame,pose in [(1,a),(frames,b)]:
        root['wing_sweep_deg']=float(pose[0])
        root['nozzle_extension_m']=float(pose[1])
        root.keyframe_insert(data_path='["wing_sweep_deg"]',frame=frame)
        root.keyframe_insert(data_path='["nozzle_extension_m"]',frame=frame)
    root.animation_data.action.name='SOURCE | '+name
    root.animation_data.action.asset_mark()
    root.animation_data.action.use_fake_user=True
root.animation_data.action=source_action
# Standard Blender asset catalogs: add the version folder as an Asset Library.
catalogs={name:str(uuid.uuid5(uuid.NAMESPACE_URL,'spectre9-d/'+name)) for name in ['Aircraft','Modules','Materials','Animations']}
asset.asset_data.catalog_id=catalogs['Aircraft']
for collection in modules.values():
    collection.asset_data.catalog_id=catalogs['Modules']
for mat in m.values():
    mat.asset_data.catalog_id=catalogs['Materials']
for action in bpy.data.actions:
    if action.asset_data:
        action.asset_data.catalog_id=catalogs['Animations']
(VERSION/'blender_assets.cats.txt').write_text('VERSION 1\n\n'+''.join(f'{identifier}:Spectre 9-D/{name}:{name}\n' for name,identifier in catalogs.items()))
scene.frame_start=1
scene.frame_end=241
scene.render.fps=30
for frame,name in [(1,'MANEUVER'),(76,'CRUISE'),(151,'INTERCEPT'),(241,'MANEUVER')]:
    scene.timeline_markers.new(name,frame=frame)
scene.frame_set(1)

studio=bpy.data.collections.new('STUDIO | excluded from export')
scene.collection.children.link(studio)
bpy.context.view_layer.active_layer_collection=bpy.context.view_layer.layer_collection.children[studio.name]
box('STUDIO | floor',(0,0,-.90),(200,200,.06),material('STUDIO | midnight',(.012,.022,.035),.2,.55),0)
for name,position,energy,size,color in [('Key',(1,-8,12),2400,8,(.86,.94,1)),
    ('Fill',(-9,-2,7),2200,7,(1,.87,.73)),('Rim',(2,10,9),3200,7,(.50,.72,1))]:
    data=bpy.data.lights.new('STUDIO | '+name,'AREA')
    data.energy=energy
    data.shape='DISK'
    data.size=size
    data.color=color
    obj=bpy.data.objects.new(data.name,data)
    studio.objects.link(obj)
    obj.location=position
    obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
for name,position,target,scale in [('hero',(11,-16,11),(0,0,.3),16.2),('rear',(-11,16,8),(0,.7,.5),16.2),
    ('top',(0,0,22),(0,0,0),17.5),('bottom',(0,0,-22),(0,0,0),17.5),
    ('left',(-22,0,1.0),(0,0,1.0),15.7),('front',(0,-23,1),(0,0,1),12.8),
    ('back',(0,23,1),(0,0,1),12.8),('canopy',(4,-7,4),(0,-2.6,.5),6.8)]:
    data=bpy.data.cameras.new('CAM | '+name)
    data.type='ORTHO'
    data.ortho_scale=scale
    obj=bpy.data.objects.new(data.name,data)
    studio.objects.link(obj)
    obj.location=position
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.data.objects['CAM | top'].rotation_euler.z=math.pi
scene.camera=bpy.data.objects['CAM | hero']
scene.render.engine='CYCLES'
scene.cycles.samples=config['preview_samples']
scene.cycles.use_denoising=True
scene.render.resolution_x=1500
scene.render.resolution_y=1125
scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('World')
scene.world.color=(.07,.07,.07)
scene.view_settings.view_transform='AgX'
compositor=bpy.data.node_groups.new('STUDIO | restrained ion glow','CompositorNodeTree')
scene.compositing_node_group=compositor
compositor.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
layers=compositor.nodes.new('CompositorNodeRLayers')
glow=compositor.nodes.new('CompositorNodeGlare')
glow.inputs['Type'].default_value='Fog Glow'
glow.inputs['Threshold'].default_value=1.5
glow.inputs['Strength'].default_value=.16
output=compositor.nodes.new('NodeGroupOutput')
compositor.links.new(layers.outputs['Image'],glow.inputs['Image'])
compositor.links.new(glow.outputs['Image'],output.inputs['Image'])
reference=bpy.data.images.load(str(ASSETS/'references/spectre9_d.png'))
reference.name='REFERENCE | supplied Spectre 9-D design sheet'
reference.pack()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=18
            area.spaces.active.region_3d.view_location=(0,0,.3)
            area.spaces.active.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
            area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.wm.save_as_mainfile(filepath=str(BLENDER/'spectre9_d.blend'))
print('BUILD COMPLETE',flush=True)
