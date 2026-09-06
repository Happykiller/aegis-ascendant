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
    """Les cartes de surface — REECRITES PAR LE PROJET LE 2026-09-06.

    ⚠️ CE QUE LA LIVRAISON GENERAIT NE CONTENAIT RIEN. Mesure sur le .glb livre : les six
    cartes etaient des APLATS. L'albedo modulait de +/-2,3 %, la rugosite de +/-5 %, et la
    normale de **+/-2 sur 255** — branchee de surcroit a une force de 0,22. C'est trois a
    dix fois sous le seuil auquel un detail existe dans ce jeu. L'operateur l'a vu tout de
    suite : « il lui manque les textures pour etre aussi beau que le B ».

    ⚠️ ET LA REPONSE N'ETAIT PAS PLUS DE TEXELS. Densite UV mesuree sur le maillage :
    0,831 tuile/m, soit une tuile pour 1,20 m de modele — 0,235 m en jeu, c'est-a-dire
    **11 pixels a l'ecran** a 45,8 px/m. Un damier fin y serait sous-pixel quelle que soit
    la resolution. Il faut UN MOTIF FORT PAR TUILE, et du contraste.

    D'ou le dessin : une TOLE par tuile, sa rainure de joint sur le bord (donc raccord
    automatique), un lisere clair a l'interieur, une rangee de rivets, et un grain brosse.
    La hauteur porte tout ; la normale s'en DERIVE (`ADR-0013` : une normale ne se genere
    pas). La resolution reste a 512 : a 11 px a l'ecran elle est deja sur-echantillonnee
    quarante fois, et la monter n'aurait paye que du poids.
    """
    size = config['texture_resolution']
    rng = random.Random(config['surface_seed'])
    n = size * size

    def idx(x, y):
        return (y % size) * size + (x % size)

    # --- LE RELIEF, en niveaux de gris : c'est lui qui porte tout le reste --------
    hauteur = [0.0] * n
    grain = [rng.uniform(-1.0, 1.0) for _ in range(n)]
    # ⚠️ CES DEUX LARGEURS SONT DIMENSIONNEES CONTRE L'ECRAN, PAS CONTRE L'IMAGE.
    # Une tuile couvre 11 px a l'ecran (0,831 tuile/m, coque a 2,46 m, 45,8 px/m). Une
    # rainure a 1 % de la tuile — ce que la premiere version faisait — vaut donc 0,11 px :
    # elle n'existe pas. A 4,2 % elle vaut 0,46 px en jeu et 2 px au bestiaire, ou la coque
    # est montree cinq fois plus grande. C'est le compromis : une ligne franche de pres,
    # un assombrissement au bon endroit de loin.
    joint = max(3, size // 24)          # 4,2 % de la tuile : la rainure de joint
    lisere = max(1, size // 150)        # le lisere clair, juste en dedans
    for y in range(size):
        for x in range(size):
            db = min(x, y, size - 1 - x, size - 1 - y)   # distance au bord de la tuile
            h = 0.05 * grain[idx(x, y)]                  # grain brosse, tres faible
            if db < joint:
                h -= 1.0 - (db / joint) * 0.35           # la rainure creuse
            elif db < joint + lisere + 1:
                h += 0.45                                # le lisere accroche la lumiere
            hauteur[idx(x, y)] = h
    # Les rivets : une rangee le long du joint, a pas regulier mais pas au bord.
    pas = max(8, size // 7)
    marge = joint + lisere + max(2, size // 128)
    # Les rivets ne se verront QU'AU BESTIAIRE (0,13 px en jeu, ~1 px de pres). C'est
    # assumé : ils recompensent le gros plan sans pretendre porter la lecture de loin.
    rayon = max(1, size // 110)
    rivets = [0.0] * n
    for k in range(0, size, pas):
        for cx, cy in ((k, marge), (k, size - 1 - marge), (marge, k), (size - 1 - marge, k)):
            for dy in range(-rayon, rayon + 1):
                for dx in range(-rayon, rayon + 1):
                    if dx * dx + dy * dy <= rayon * rayon:
                        rivets[idx(cx + dx, cy + dy)] = 1.0
    for i in range(n):
        if rivets[i]:
            hauteur[i] += 0.55

    # --- L'ALBEDO, une carte par teinte ------------------------------------------
    colors = {'white': config['paint_white_srgb'], 'blue': config['paint_blue_srgb'],
              'red': config['paint_red_srgb'], 'metal': [.29, .32, .35]}
    directory = ASSETS / 'textures'
    directory.mkdir(exist_ok=True)
    for name, color in colors.items():
        pixels = bytearray()
        for i in range(n):
            h = hauteur[i]
            # ⚠️ LE CONTRASTE EST CE QUI SURVIT, PAS LA FINESSE. Le joint assombrit de 20 %,
            # le lisere eclaircit de 12 % : dix fois la modulation d'origine.
            f = 1.0 + (0.12 * h if h > 0 else 0.20 * h)
            f += 0.030 * grain[i]
            pixels.extend(int(max(0, min(255, c * 255 * f))) for c in color)
        png(directory / f'{name}_basecolor.png', size, pixels)

    # --- LA RUGOSITE : le creux accroche la poussiere, le lisere est poli ---------
    roughness = bytearray()
    for i in range(n):
        h = hauteur[i]
        v = int(max(0, min(255, 148 - h * 34 + grain[i] * 8)))
        roughness.extend([v] * 3)
    png(directory / 'surface_roughness.png', size, roughness)

    # --- LA NORMALE, DERIVEE de la hauteur (ADR-0013) ----------------------------
    # Differences centrees, en tangent-space OpenGL (+Y vers le haut de l'image).
    force = 2.6
    normal = bytearray()
    for y in range(size):
        for x in range(size):
            dx = (hauteur[idx(x + 1, y)] - hauteur[idx(x - 1, y)]) * force
            dy = (hauteur[idx(x, y + 1)] - hauteur[idx(x, y - 1)]) * force
            longueur = (dx * dx + dy * dy + 1.0) ** 0.5
            normal.extend((int((-dx / longueur * 0.5 + 0.5) * 255),
                           int((dy / longueur * 0.5 + 0.5) * 255),
                           int((1.0 / longueur * 0.5 + 0.5) * 255)))
    png(directory / 'surface_normal.png', size, normal)

    # L'usure reste une carte a part : le builder la reclame, rien ne la lit encore.
    wear = bytearray()
    for i in range(n):
        wear.extend([255 if hauteur[i] < -0.5 else 0] * 3)
    png(directory / 'wear_mask.png', size, wear)


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
                normal.inputs['Strength'].default_value=.85
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
