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


def _champ_tuilable(size, cellules, rng):
    """Un champ doux, ALEATOIRE mais qui se raccorde a lui-meme.

    Une grille grossiere de `cellules` valeurs, interpolee en douceur avec bouclage : le bord
    droit retrouve le bord gauche par construction, donc la tuile se repete sans couture.
    C'est ce qui permet de salir une surface entiere sans qu'un liseré n'apparaisse tous les
    1,20 m — le defaut classique d'une feuille repetee.
    """
    grille = [[rng.uniform(0.0, 1.0) for _ in range(cellules)] for _ in range(cellules)]
    champ = [0.0] * (size * size)
    for y in range(size):
        fy = y * cellules / size
        y0 = int(fy) % cellules
        y1 = (y0 + 1) % cellules
        ty = fy - int(fy)
        ty = ty * ty * (3.0 - 2.0 * ty)
        for x in range(size):
            fx = x * cellules / size
            x0 = int(fx) % cellules
            x1 = (x0 + 1) % cellules
            tx = fx - int(fx)
            tx = tx * tx * (3.0 - 2.0 * tx)
            haut = grille[y0][x0] * (1 - tx) + grille[y0][x1] * tx
            bas = grille[y1][x0] * (1 - tx) + grille[y1][x1] * tx
            champ[y * size + x] = haut * (1 - ty) + bas * ty
    return champ


def texture_files(config):
    """Les cartes de surface — REECRITES PAR LE PROJET, puis SALIES (2026-09-06).

    ⚠️ CE QUE LA LIVRAISON GENERAIT NE CONTENAIT RIEN. Mesure sur le .glb livre : les six
    cartes etaient des APLATS. L'albedo modulait de +/-2,3 %, la rugosite de +/-5 %, et la
    normale de **+/-2 sur 255** — branchee de surcroit a une force de 0,22. Trois a dix fois
    sous le seuil auquel un detail existe dans ce jeu.

    ⚠️ ET LA REPONSE N'ETAIT PAS PLUS DE TEXELS. Densite UV mesuree sur le maillage :
    0,831 tuile/m, soit une tuile pour 1,20 m de modele — 0,235 m en jeu, c'est-a-dire
    **11 pixels a l'ecran** a 45,8 px/m. Un damier fin y serait sous-pixel quelle que soit
    la resolution. La resolution reste donc a 512.

    LES DEUX ETAGES DE CETTE CARTE, ET LEUR ECHELLE A L'ECRAN

      1. LA STRUCTURE — une tole par tuile, sa rainure de joint sur le bord (donc raccord
         automatique), un lisere clair en dedans, une rangee de rivets. La rainure fait
         4,2 % de la tuile : 0,46 px en jeu, 2 px au bestiaire.
      2. LA PATINE — un champ doux a huit cellules, donc des taches d'environ un tiers de
         tuile : **~4 px a l'ecran**. C'est la seule echelle a laquelle une salissure peut
         encore exister sur cette coque, et c'est elle qui fait qu'une peinture n'est pas
         un aplat. S'y ajoute la crasse qui s'accumule PRES DES JOINTS, ou elle s'accumule
         vraiment.

    ⚠️ ELLE SERA TOUJOURS REGULIERE, et il faut le savoir : une feuille qui se repete ne
    peut pas poser une coulure a un endroit choisi. Pour ca il faut un atlas peint, ou toute
    la coque tient dans une seule image. La difference se voit au bestiaire, cote a cote avec
    la `specter_9_b` : celle-ci lit comme un appareil use, celle-la comme un appareil propre.

    La hauteur porte la structure ; la normale s'en DERIVE (`ADR-0013`).
    """
    size = config['texture_resolution']
    rng = random.Random(config['surface_seed'])
    n = size * size

    def idx(x, y):
        return (y % size) * size + (x % size)

    # --- LE RELIEF, en niveaux de gris : il porte la structure -------------------
    hauteur = [0.0] * n
    grain = [rng.uniform(-1.0, 1.0) for _ in range(n)]
    # ⚠️ CES DEUX LARGEURS SONT DIMENSIONNEES CONTRE L'ECRAN, PAS CONTRE L'IMAGE.
    # Une rainure a 1 % de la tuile vaut 0,11 px : elle n'existe pas. A 4,2 % elle vaut
    # 0,46 px en jeu et 2 px au bestiaire, ou la coque est montree cinq fois plus grande.
    joint = max(3, size // 24)
    lisere = max(1, size // 150)
    proximite = [0.0] * n            # 1 au bord du joint, 0 au centre de la tole
    for y in range(size):
        for x in range(size):
            db = min(x, y, size - 1 - x, size - 1 - y)
            h = 0.05 * grain[idx(x, y)]
            if db < joint:
                h -= 1.0 - (db / joint) * 0.35
            elif db < joint + lisere + 1:
                h += 0.45
            hauteur[idx(x, y)] = h
            # La crasse s'etale sur un huitieme de tuile a partir du joint.
            etalement = max(1.0, size / 8.0)
            proximite[idx(x, y)] = max(0.0, 1.0 - db / etalement)
    pas = max(8, size // 7)
    marge = joint + lisere + max(2, size // 128)
    # Les rivets ne se verront QU'AU BESTIAIRE (0,13 px en jeu, ~1 px de pres). C'est
    # assume : ils recompensent le gros plan sans pretendre porter la lecture de loin.
    rayon = max(1, size // 110)
    for k in range(0, size, pas):
        for cx, cy in ((k, marge), (k, size - 1 - marge), (marge, k), (size - 1 - marge, k)):
            for dy in range(-rayon, rayon + 1):
                for dx in range(-rayon, rayon + 1):
                    if dx * dx + dy * dy <= rayon * rayon:
                        hauteur[idx(cx + dx, cy + dy)] += 0.55

    # --- LA PATINE : deux champs doux, aux deux echelles qui survivent -----------
    taches = _champ_tuilable(size, 8, rng)        # ~1/3 de tuile : 4 px a l'ecran
    voile = _champ_tuilable(size, 3, rng)         # une tuile entiere : 11 px
    crasse = [0.0] * n
    for i in range(n):
        # La crasse s'accumule pres des joints ET la ou le voile est sombre.
        crasse[i] = min(1.0, proximite[i] * (0.55 + 0.45 * taches[i]) + 0.25 * (1.0 - voile[i]))

    # --- L'ALBEDO, une carte par teinte ------------------------------------------
    colors = {'white': config['paint_white_srgb'], 'blue': config['paint_blue_srgb'],
              'red': config['paint_red_srgb'], 'metal': [.29, .32, .35]}
    directory = ASSETS / 'textures'
    directory.mkdir(exist_ok=True)
    for name, color in colors.items():
        pixels = bytearray()
        for i in range(n):
            h = hauteur[i]
            f = 1.0 + (0.12 * h if h > 0 else 0.20 * h)      # la structure
            f *= 1.0 - 0.17 * crasse[i]                       # la crasse assombrit
            f *= 0.93 + 0.14 * taches[i]                      # la peinture n'est pas unie
            f += 0.030 * grain[i]
            # ⚠️ ET ELLE SE DESATURE EN VIEILLISSANT. Une peinture sale ne fait pas que
            # foncer : elle tire vers le gris. Sans ce melange, le rouge sali reste un
            # rouge sombre — ce qui se lit comme une ombre, pas comme de l'usure.
            gris = (color[0] + color[1] + color[2]) / 3.0
            for c in color:
                v = (c * (1.0 - 0.35 * crasse[i]) + gris * 0.35 * crasse[i]) * 255 * f
                pixels.append(int(max(0, min(255, v))))
        png(directory / f'{name}_basecolor.png', size, pixels)

    # --- LA RUGOSITE : le creux et la crasse accrochent, le lisere est poli -------
    roughness = bytearray()
    for i in range(n):
        h = hauteur[i]
        v = int(max(0, min(255, 148 - h * 34 + crasse[i] * 42 + (taches[i] - 0.5) * 26
                           + grain[i] * 8)))
        roughness.extend([v] * 3)
    png(directory / 'surface_roughness.png', size, roughness)

    # --- LA NORMALE, DERIVEE de la hauteur (ADR-0013) ----------------------------
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

    wear = bytearray()
    for i in range(n):
        wear.extend([int(max(0, min(255, crasse[i] * 255)))] * 3)
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
