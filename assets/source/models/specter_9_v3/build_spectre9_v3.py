"""Variable-sweep wings and articulated exhaust petals, driven by one speed control."""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parent/'v2'))
from geometry import box, line, mesh, pivot, plate, remove, ring, rod, text

bpy.ops.wm.open_mainfile(filepath=str(OUT.parent/'v2/spectre9_v2.blend'))
scene=bpy.context.scene
ship=bpy.data.collections['SPECTRE 9 | assembly']
bpy.context.view_layer.active_layer_collection=bpy.context.view_layer.layer_collection.children[ship.name]
scene.frame_set(135)
for obj in ship.objects:
    if obj.animation_data:
        obj.animation_data_clear()
    if 'Canopy hinge' in obj.name or 'bay door' in obj.name or 'elevon' in obj.name or 'rudder' in obj.name:
        obj.rotation_euler=(0,0,0)
    if 'cannon slide' in obj.name:
        obj.location.y=1.15
bpy.context.view_layer.update()

white,blue,dark,steel,gold,red,glass,cyan,rubber=[
    next(mat for mat in bpy.data.materials if mat.name.startswith(f'{i:02}')) for i in range(1,10)]


def matching(*terms):
    return [obj for obj in ship.objects if any(term in obj.name for term in terms)]


remove(matching('wing titanium substrate','segmented armor','leading edge cobalt','wingtip warning',
                'swept cobalt wing','trailing cobalt','elevon','squadron 09','wing stencil',
                'warning stencil','serial stencil','red service hatch'))
remove(matching('exhaust','nozzle petal','ion core','ion chamber','luminous annulus','engine mechanical body'))

controller=pivot('CTRL | Flight configuration',(0,0,2.8),[])
controller['speed']=0.0
controller.id_properties_ui('speed').update(min=0,max=1,soft_min=0,soft_max=1,
    description='Normalized visual speed: 0 = wings wide / nozzles open; 1 = wings swept / nozzles narrow')
controller['wing_sweep_max_degrees']=30.0
controller['nozzle_petal_max_degrees']=18.0
controller['note']='Art-directed flight configuration; no aerodynamic or engine simulation.'
for frame,value in [(1,0),(24,0),(84,1),(108,1),(168,0),(180,0)]:
    controller['speed']=value
    controller.keyframe_insert(data_path='["speed"]',frame=frame)


def speed_driver(obj,path,index,expression):
    driver=obj.driver_add(path,index).driver
    driver.type='SCRIPTED'
    variable=driver.variables.new()
    variable.name='speed'
    variable.type='SINGLE_PROP'
    variable.targets[0].id=controller
    variable.targets[0].data_path='["speed"]'
    driver.expression=expression


wing_controls=[]
nozzle_controls=[]
tip_witnesses=[]
nozzle_witnesses=[]
for side,label in [(-1,'L'),(1,'R')]:
    def mirror(points):
        return [(side*x,y) for x,y in points]

    # The fixed glove hides the small rotating root; the entire outer airfoil sweeps.
    glove=[(.86,-1.92),(1.42,-.55),(2.32,.84),(2.35,1.70),(2.07,2.50),(.97,3.7)]
    plate(label+' | fixed wing glove',mirror(glove),.22,.17,white)
    plate(label+' | glove cobalt inlay',mirror([(1.48,-.3),(2.27,.85),(2.27,1.55),
          (1.99,1.88),(1.82,.54)]),.246,.024,blue)
    # A visible bearing and sweep-slot make the new mechanical function legible.
    rod(label+' | wing pivot bearing',(side*1.99,1.16,.23),(side*1.99,1.16,.32),.29,dark,vertices=40)
    rod(label+' | wing pivot cap',(side*1.99,1.16,.32),(side*1.99,1.16,.355),.20,steel,vertices=32)
    for i in range(8):
        angle=math.tau*i/8
        x=side*1.99+.15*math.cos(angle)
        y=1.16+.15*math.sin(angle)
        rod(label+' | bearing bolt',(x,y,.352),(x,y,.365),.022,gold,vertices=8)
    arc=[(side*(1.99+.45*math.cos(a)),1.16+.45*math.sin(a),.249)
         for a in [math.radians(-40+i*8) for i in range(16)]]
    line(label+' | sweep track',arc,.024,dark)

    before=set(ship.objects)
    outline=[(1.96,.92),(2.36,1.18),(4.45,3.75),(4.40,4.46),(3.30,4.13),(2.14,2.04)]
    plate(label+' | sweeping airfoil',mirror(outline),.205,.135,white)
    plate(label+' | swept leading edge',mirror([(2.35,1.18),(4.45,3.75),(4.34,3.98),
          (2.42,1.55)]),.23,.024,blue)
    plate(label+' | outer wing cobalt band',mirror([(2.65,2.10),(3.78,3.74),
          (3.45,3.58),(2.42,2.05)]),.233,.024,blue)
    plate(label+' | outer wing red tip',mirror([(4.29,3.56),(4.45,3.75),
          (4.40,4.46),(4.22,4.40)]),.245,.15,red)
    text(label+' | wing number','09',(side*3.71,3.55,.25),.46,dark,(0,0,math.pi))
    text(label+' | wing no step','NO STEP',(side*2.83,2.63,.25),.075,red,(0,0,math.pi))
    elevon=plate(label+' | moving elevon',mirror([(3.30,4.13),(4.22,4.43),
          (4.17,4.62),(3.24,4.30)]),.20,.07,blue)
    elevon_control=pivot('CTRL | '+label+' elevon',(side*3.3,4.13,.20),[elevon])
    tip=pivot('MARKER | '+label+' wingtip',(side*4.45,3.75,.20),[])
    tip_witnesses.append(tip)
    wing_parts=set(ship.objects)-before
    # Parent only the roots of subassemblies; keep the elevon's own hinge intact.
    roots=[obj for obj in wing_parts if obj.parent not in wing_parts]
    sweep=pivot('CTRL | '+label+' wing sweep',(side*1.99,1.16,.20),roots)
    speed_driver(sweep,'rotation_euler',2,f'{side*math.radians(30)} * speed')
    wing_controls.append(sweep)

    # Wing-mounted cannons follow the airfoil; a geared pylon counter-rotates to
    # preserve their forward direction. The existing slide remains independently usable.
    cannon_roots=[obj for obj in ship.objects if obj.name.startswith(label+' |') and
                  any(term in obj.name for term in ['cannon pylon','cannon armored sleeve'])]
    cannon_roots.append(bpy.data.objects['CTRL | '+label+' cannon slide'])
    bpy.context.view_layer.update()
    for obj in cannon_roots:
        obj.location.x += side*.32
        obj.location.y += 1.05
    mount=pivot('CTRL | '+label+' pylon alignment',(side*2.72,2.33,-.25),cannon_roots)
    world=mount.matrix_world.copy()
    mount.parent=sweep
    mount.matrix_world=world
    speed_driver(mount,'rotation_euler',2,f'{-side*math.radians(30)} * speed')

    # Replacement nozzle: fixed throat, recessed emissive core, twenty rigid petals.
    x=side*1.24
    rod(label+' | engine inner casing',(x,1.62,.08),(x,5.30,.08),.60,dark,vertices=32)
    ring(label+' | nozzle fixed throat',(x,5.34,.08),.755,.565,.17,steel)
    ring(label+' | recessed ion ring',(x,5.45,.08),.54,.44,.055,cyan)
    rod(label+' | recessed ion core',(x,5.39,.08),(x,5.405,.08),.44,cyan,vertices=40)
    for i in range(20):
        angle=math.tau*i/20
        # Local X is the tangential hinge, local Y is aft, local Z points inward.
        tangent=Vector((-math.sin(angle),0,math.cos(angle)))
        aft=Vector((0,1,0))
        inward=Vector((-math.cos(angle),0,-math.sin(angle)))
        basis=Matrix((tangent,aft,inward)).transposed().to_4x4()
        basis.translation=(x+.735*math.cos(angle),5.38,.08+.735*math.sin(angle))
        hinge=pivot(f'CTRL | {label} nozzle petal {i:02}',(0,0,0),[])
        hinge.matrix_world=basis
        # Bake orientation into a parent so the driven local X stays a true tangent axis.
        anchor=pivot(f'{label} | nozzle hinge anchor {i:02}',(0,0,0),[])
        anchor.matrix_world=basis
        hinge.parent=anchor
        hinge.matrix_parent_inverse=Matrix.Identity(4)
        hinge.matrix_basis=Matrix.Identity(4)
        vertices=[(-.132,0,0),(.132,0,0),(.112,.99,.035),(-.112,.99,.035)]
        petal=mesh(f'{label} | articulated nozzle petal {i:02}',vertices,[(0,1,2,3)],steel,.006)
        petal.modifiers.new('Petal thickness','SOLIDIFY').thickness=.024
        petal.parent=hinge
        petal.matrix_parent_inverse=Matrix.Identity(4)
        # Dark reinforcement travels as part of the same rigid petal.
        rib=box(f'{label} | nozzle petal rib {i:02}',(0,.45,-.011),(.035,.74,.025),dark,.006)
        rib.parent=hinge
        rib.matrix_parent_inverse=Matrix.Identity(4)
        speed_driver(hinge,'rotation_euler',0,f'{math.radians(18)} * speed')
        nozzle_controls.append(hinge)
        if i==0:
            witness=pivot('MARKER | '+label+' nozzle lip',(0,0,0),[])
            witness.parent=hinge
            witness.matrix_parent_inverse=Matrix.Identity(4)
            witness.location=(0,.99,.035)
            nozzle_witnesses.append(witness)

# Convert newly modeled curves and give all new surfaces portable, explicit UVs.
scene.frame_start=1
scene.frame_end=180
scene.render.fps=30
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
for obj in ship.objects:
    if obj.type in {'MESH','CURVE','FONT'}:
        obj.select_set(True)
bpy.context.view_layer.objects.active=next(obj for obj in ship.objects if obj.type=='MESH')
bpy.ops.object.convert(target='MESH')
for obj in ship.objects:
    if obj.type!='MESH' or obj.data.uv_layers:
        continue
    uv=obj.data.uv_layers.new(name='UVMap')
    for face in obj.data.polygons:
        dominant=max(range(3),key=lambda axis:abs(face.normal[axis]))
        axes=[axis for axis in range(3) if axis!=dominant]
        for loop_index in face.loop_indices:
            point=obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv=(point[axes[0]]/2.65,point[axes[1]]/2.65)

scene.timeline_markers.clear()
for frame,name in [(1,'LOW SPEED | wings wide / nozzle open'),(84,'HIGH SPEED | swept / narrow'),
                   (168,'LOW SPEED | return')]:
    scene.timeline_markers.new(name,frame=frame)
scene.name='SPECTRE 9 | variable geometry speed demonstration'
scene.camera=bpy.data.objects['Camera | rear three-quarter']
bpy.data.objects['Camera | top orthographic'].data.ortho_scale=18.8
scene.render.resolution_x=1400
scene.render.resolution_y=1050
scene.cycles.samples=32
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
controller.select_set(True)
bpy.context.view_layer.objects.active=controller
scene['INSTRUCTIONS']='Select CTRL | Flight configuration > Object custom properties > speed (0..1). Clear its keyframes for manual control.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'spectre9_v3.blend'))

# glTF does not carry Blender drivers. Bake evaluated transforms on a temporary
# in-memory scene state for export; the saved .blend retains its editable drivers.
driven=[obj for obj in ship.objects if obj.animation_data and obj.animation_data.drivers]
samples={obj.name:[] for obj in driven}
for frame in range(1,181):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    for obj in driven:
        samples[obj.name].append(tuple(obj.rotation_euler))
for obj in driven:
    for curve in list(obj.animation_data.drivers):
        obj.driver_remove(curve.data_path,curve.array_index)
    for frame,value in enumerate(samples[obj.name],1):
        obj.rotation_euler=value
        obj.keyframe_insert(data_path='rotation_euler',frame=frame)
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
for obj in ship.objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active=controller
bpy.ops.export_scene.gltf(filepath=str(OUT/'spectre9_v3.glb'),use_selection=True,
    export_format='GLB',export_apply=True,export_animations=True,export_animation_mode='SCENE',
    export_frame_range=True,export_force_sampling=True,export_anim_scene_split_object=False,
    export_extras=True)

# Reopen the actual deliverable before rendering it.
bpy.ops.wm.open_mainfile(filepath=str(OUT/'spectre9_v3.blend'))
scene=bpy.context.scene
for camera_name,frame,name in [
    ('Camera | top orthographic',1,'wings_open'),('Camera | top orthographic',84,'wings_swept'),
    ('Camera | rear three-quarter',1,'nozzles_open'),('Camera | rear three-quarter',84,'nozzles_narrow')]:
    scene.camera=bpy.data.objects[camera_name]
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/f'spectre9_v3_{name}.png')
    bpy.ops.render.render(write_still=True)
print('V3 BUILD COMPLETE')
