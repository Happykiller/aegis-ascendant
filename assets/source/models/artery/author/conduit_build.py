"""Two modular power conduits with opening collars and exposed breakaway wires."""
import sys
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from paths import BLEND,ASSET_COLLECTION
import geometry as g
from materials import make_materials
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
m = make_materials()
root = g.control('Conduite energetique')
root['asset_number'] = '05/10'
root['reference'] = 'asset5_Planche technique de conduite énergétique futuriste.png'
root['dimensions_xyz_m'] = [1.6,3.8,1.4]
fixed = g.control('Raccord coque',root)
moving = g.control('Raccord moteur',root,explode=(0,.6,0))
moving['mechanism'] = 'connector'


def box(name,loc,size,mat='armor',bevel=.009):
    return g.box(name,loc,size,m[mat],bevel)


def bolt_x(x,y,z,side):
    g.rod('Boulon',(x,y,z),(x+side*.016,y,z),.016,m['bronze'],6)


def clad(name,profile,x,width):
    g.prism_x(name,profile,x-width/2,x+width/2,m['armor'],.012)
    for y,z in profile:
        for side in (-1,1):
            box('Platine '+name,(x+side*(width/2+.004),y,z),(.018,.14,.13),'panel',.005)
            bolt_x(x+side*(width/2+.018),y,z,side)


# Each mounting end is an autonomous armored bracket.
for end,parent in [(-1,fixed),(1,moving)]:
    g.PARENT = parent
    y = end*1.64
    box('Base raccord',(0,y,.10),(1.6,.52,.20),'dark')
    for x in (-.60,-.20,.20,.60):
        box('Tuile embase',(x,y,.226),(.37,.49,.052),'panel')
        for dy in (-.16,.16):
            g.rod('Vis embase',(x,y+dy,.256),(x,y+dy,.277),.025,m['bronze'],6)
    for side in (-1,1):
        profile=[(y-.21,.22),(y-.21,1.20),(y-.11,1.33),(y+.13,1.33),(y+.22,1.12),(y+.22,.22)]
        clad('Blindage raccord',profile,side*.58,.31)
        for z in (.43,.69,.95,1.2):
            box('Panneau montant',(side*.755,y,z),(.03,.34,.205),'panel')
            box('Nervure montant',(side*.775,y,z-.07),(.009,.28,.02),'edge',.002)
        box('Prise technique',(side*.60,y-end*.252,.71),(.16,.075,.26))
        box('Indicateur raccord',(side*.60,y-end*.296,.71),(.07,.015,.14),'magenta',.003)
    box('Traverse haute',(0,y,1.245),(1.0,.36,.18))
    for x in (-.33,0,.33):
        box('Capot haut',(x,y,1.354),(.31,.32,.032),'panel')
    for x,z in [(-.36,1.0),(.36,1.0 if end==-1 else .44)]:
        box('Boitier terminaison',(x,y,z),(.40,.40,.42))
        box('Platine terminaison',(x,y+end*.22,z),(.32,.04,.32),'panel')
        g.ring('Socket conduite',y-end*.23,.235,.162,.10,m['panel'],center=(x,z),count=40)
        g.ring('Joint socket',y-end*.30,.184,.157,.035,m['dark'],center=(x,z),count=40)
    box('Voyant traverse',(0,y-end*.195,1.26),(.18,.016,.055),'magenta',.003)
g.pivot(moving,(0,1.64,.70))
# Main straight feed has reusable armored collars and separate emissive cores.
feed = g.control('Conduit principal',root,explode=(-.24,0,.25))
feed['mechanism'] = 'feed'
g.PARENT = feed
x,z = -.36,1.0
for start,end in [(-1.38,-.93),(-.44,.30),(.89,1.40)]:
    g.rod('Tube principal',(x,start,z),(x,end,z),.158,m['dark'],32)
    for y in (start+.025,end-.025):
        g.ring('Frettes conduit',y,.183,.151,.045,m['edge'],center=(x,z),count=32)
for center in (-.68,.60):
    g.rod('Chambre energie',(x,center-.25,z),(x,center+.25,z),.147,m['dark'],32)
    for a in range(6):
        t = a*math.tau/6
        shell = g.sector('Blindage chambre',[(center-.20,.178),(center+.20,.178),
            (center+.20,.168),(center-.20,.168)],t+.12,t+math.tau/6-.12,m['armor'],5,.003)
        for vertex in shell.data.vertices:
            vertex.co.x += x
            vertex.co.z += z
        dx,dz = .176*math.cos(t+math.pi/6),.176*math.sin(t+math.pi/6)
        g.rod('Barreau cage',(x+dx,center-.24,z+dz),(x+dx,center+.24,z+dz),.017,m['edge'],10)
    for y in (center-.24,center+.24):
        g.ring('Bague chambre',y,.202,.149,.064,m['armor'],center=(x,z),count=32)
    pulse = g.control('Noyau principal '+str(center),feed)
    pulse['mechanism'],pulse['phase'] = 'pulse',center
    g.PARENT = pulse
    g.rod('Plasma principal',(x,center-.22,z),(x,center+.22,z),.158,m['magenta'],32)
    g.pivot(pulse,(x,center,z))
    g.PARENT = feed
# Clamshell collars peel away instead of a solid unbreakable ring.
for y in (-1.15,-.03,1.13):
    for side in (-1,1):
        collar = g.control('Demi collier '+str(y)+' '+str(side),feed,explode=(side*.18,0,.1))
        collar['mechanism'],collar['side'] = 'collar',side
        g.PARENT = collar
        start = -math.pi/2 if side==1 else math.pi/2
        obj = g.sector('Coque collier',[(y-.07,.23),(y+.07,.23),(y+.07,.181),(y-.07,.181)],start,start+math.pi,m['panel'],12,.006)
        for v in obj.data.vertices:
            v.co.x += x
            v.co.z += z
        for t in (start+.35,start+math.pi/2,start+math.pi-.35):
            dx,dz = .242*math.cos(t),.242*math.sin(t)
            g.rod('Vis collier',(x+dx,y-.074,z+dz),(x+dx,y-.090,z+dz),.015,m['bronze'],6)
        g.pivot(collar,(x,y,z))
g.pivot(feed,(x,-1.38,z))
# Secondary S-shaped hose: three reusable spans joined by rounded elbows.
secondary = g.control('Conduit secondaire coude',root,explode=(.3,0,-.1))
secondary['mechanism'] = 'secondary'
g.PARENT = secondary
points=[(.36,-1.4,1.0),(.36,-1.05,.99),(.36,-.64,.85),(.36,-.18,.56),(.36,.25,.44),(.36,1.4,.44)]
g.hose('Gaine coudee',points,.143,m['hose'])
for y,z in [(-1.23,.995),(-.87,.94),(-.54,.78),(-.23,.59),(.13,.46),(.38,.44),(1.18,.44)]:
    g.ring('Collier secondaire',y,.18,.137,.055,m['edge'],center=(.36,z),count=32)
for center,z in [(-.94,.96),(.79,.44)]:
    pulse = g.control('Noyau secondaire '+str(center),secondary)
    pulse['mechanism'],pulse['phase'] = 'pulse',center+2
    g.PARENT = pulse
    g.rod('Plasma secondaire',(.36,center-.15,z),(.36,center+.15,z),.151,m['magenta'],32)
    g.pivot(pulse,(.36,center,z))
    g.PARENT = secondary
    for y in (center-.17,center+.17):
        g.ring('Protection noyau',y,.184,.138,.054,m['armor'],center=(.36,z),count=32)
    for a in range(6):
        t = a*math.tau/6
        shell = g.sector('Blindage noyau secondaire',[(center-.14,.170),(center+.14,.170),
            (center+.14,.159),(center-.14,.159)],t+.12,t+math.tau/6-.12,m['armor'],5,.003)
        for vertex in shell.data.vertices:
            vertex.co.x += .36
            vertex.co.z += z
    for dx in (-.16,.16):
        g.rod('Renfort noyau',(.36+dx,center-.18,z),(.36+dx,center+.18,z),.017,m['edge'],10)
g.pivot(secondary,(.36,-1.40,1.0))
# Fine internal cables remain hidden in the intact pipe, and become exposed
# when the connector separates. Their endpoint transforms are baked per clip.
for lane,x,z in [('principal',-.36,1.0),('secondaire',.36,.44)]:
    for index in range(5):
        wire = g.control('Cable expose '+lane+' '+str(index),root)
        wire['mechanism'],wire['lane'],wire['index'] = 'wire',lane,index
        g.PARENT = wire
        g.hose('Ame cable',[(0,0,0),(.035*(index-2),-.035,.4),(.015,0,.75),(0,0,1)],.014,m['bronze' if index%2 else 'hose'])
        tip = g.control('Extremite '+lane+' '+str(index),root)
        tip['mechanism'],tip['lane'],tip['index'] = 'wire_tip',lane,index
        g.PARENT = tip
        g.rod('Bout cable lumineux',(0,0,-.018),(0,0,.018),.016,m['magenta'],10)
# Two small service lines make the lower routing readable.
g.PARENT = fixed
for x in (-.03,.13):
    g.hose('Ligne de service',[(x,-1.43,.36),(x,-1.0,.31),(x,-.30,.28),(x,.40,.29),(x,1.39,.30)],.027,m['hose'])
for name,loc,parent,role in [('Socket coque',(0,-1.9,.7),fixed,'mount_hull'),
    ('Socket moteur',(0,1.9,.7),moving,'mount_engine'),
    ('VFX fuite principale',(-.36,1.42,1),feed,'vfx_leak'),
    ('VFX fuite secondaire',(.36,1.42,.44),secondary,'vfx_leak')]:
    c = g.control(name,parent)
    c.location = loc
    c.matrix_parent_inverse = parent.matrix_world.inverted()
    c['role'] = role
for obj in asset.objects:
    if obj.type=='MESH':
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(obj.data)
        bm.free()
        g.uv_map(obj)
create_clips(asset)
studio.setup(scene)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
print('BUILD COMPLETE',len(asset.objects),flush=True)
