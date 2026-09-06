"""Deterministic, editable material sources and portable PBR texture files."""
import random
import struct
import sys
import zlib
import bpy
from paths import ASSETS


def png(path, size, pixels):
    def chunk(kind, data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows = b''.join(b'\x00'+pixels[y*size*3:(y+1)*size*3] for y in range(size))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,2,0,0,0))
                    +chunk(b'IDAT',zlib.compress(rows,7))+chunk(b'IEND',b''))


def texture_files(config):
    size = config['texture_resolution']
    rng = random.Random(config['surface_seed'])
    noise = [rng.uniform(-1,1) for _ in range(size*size)]
    scratches = bytearray(size*size)
    for _ in range(size*2):
        x,y = rng.randrange(size),rng.randrange(size)
        for j in range(rng.randrange(3,24)):
            scratches[((y+j)%size)*size+(x+j//5)%size] = 1
    colors = {'white':config['paint_white_srgb'], 'blue':config['paint_blue_srgb'],
              'red':config['paint_red_srgb'], 'metal':[.29,.32,.35]}
    directory = ASSETS / 'textures'
    directory.mkdir(exist_ok=True)
    for name,color in colors.items():
        pixels = bytearray()
        for i,n in enumerate(noise):
            variation = 1 + .023*n + (.06 if scratches[i] else 0)
            pixels.extend(int(max(0,min(255,c*255*variation))) for c in color)
        png(directory/f'{name}_basecolor.png',size,pixels)
    roughness = bytearray()
    normal = bytearray()
    wear = bytearray()
    for i,n in enumerate(noise):
        value = int(130+n*12-scratches[i]*17)
        roughness.extend([value]*3)
        normal.extend((128+int(n*2),128+int(noise[(i+1)%len(noise)]*2),255))
        wear.extend([255*scratches[i]]*3)
    png(directory/'surface_roughness.png',size,roughness)
    png(directory/'surface_normal.png',size,normal)
    png(directory/'wear_mask.png',size,wear)


def material(name,color,metal=0,rough=.4,emission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color,1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color,1)
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = rough
    if emission:
        shader.inputs['Emission Color'].default_value = (*color,1)
        shader.inputs['Emission Strength'].default_value = emission
    mat.asset_mark()
    return mat


def make_materials(config):
    required = [f'{name}_basecolor.png' for name in ['white','blue','red','metal']]
    required += ['surface_roughness.png','surface_normal.png','wear_mask.png']
    if '--regenerate-textures' in sys.argv or any(not (ASSETS/'textures'/name).exists() for name in required):
        texture_files(config)
    materials = {}
    for name in ['white','blue','red','metal']:
        mat = material('MAT | '+name,(.5,.5,.5),.72 if name=='metal' else .35)
        nodes,links = mat.node_tree.nodes,mat.node_tree.links
        shader = nodes.get('Principled BSDF')
        for kind,filename in [('base','%s_basecolor.png'%name),('rough','surface_roughness.png'),('normal','surface_normal.png')]:
            image = bpy.data.images.load(str(ASSETS/'textures'/filename),check_existing=True)
            if kind!='base':
                image.colorspace_settings.name='Non-Color'
            image.pack()
            texture = nodes.new('ShaderNodeTexImage')
            texture.image=image
            if kind=='normal':
                normal=nodes.new('ShaderNodeNormalMap')
                normal.inputs['Strength'].default_value=.22
                links.new(texture.outputs['Color'],normal.inputs['Color'])
                links.new(normal.outputs[0],shader.inputs['Normal'])
            else:
                links.new(texture.outputs['Color'],shader.inputs['Base Color' if kind=='base' else 'Roughness'])
        materials[name]=mat
    materials['dark']=material('MAT | graphite cavities',(.012,.022,.034),.55,.42)
    materials['glass']=material('MAT | fixed smoked canopy',(.011,.028,.043),.52,.13)
    materials['glass'].node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.85
    materials['bronze']=material('MAT | canopy bronze',(.38,.21,.073),.83,.27)
    materials['black']=material('MAT | insignia ink',(.006,.012,.019),.1,.5)
    materials['cyan']=material('MAT | ion cyan',(.004,.35,.9),.1,.24,8)
    materials['hot']=material('MAT | ion core',(.10,.75,1),.05,.2,14)
    return materials
