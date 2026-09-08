"""`author/geometry.py` REECRIT AVEC SES LEVIERS (BRIEF-0108).

C'est une copie de `author/geometry.py` — identique pour les trois livraisons,
verifie au md5 — dans laquelle chaque constante de resolution est devenue un
LEVIER pilotable. Le `build.py` de l'auteur s'execute VERBATIM par-dessus : il
appelle exactement les memes fonctions, avec exactement les memes arguments, et
c'est ici, et seulement ici, que le budget se decide.

⚠️ POURQUOI PATCHER LA GEOMETRIE PLUTOT QUE DECIMER LE MAILLAGE. Le `BRIEF-0105`
l'a mesure et regarde : ces livraisons ne sont pas des surfaces, ce sont des
PILES DE COQUES FERMEES. Un `COLLAPSE` qui laisse sept triangles a une boite de
douze lui ouvre le flanc, et la coque se couvre d'un zigzag noir que rien ne
signale. Ici on a mieux que la decimation : **on a le generateur**. Une bague de
32 cotes ne se rabote pas, elle se REGENERE a 6 cotes — et elle reste une bague.

LES SIX LEVIERS
---------------
1. `BEVEL` — les chanfreins. Ils coutent 81 % du fichier de l'auteur et rendent
   0,23 pixel. Ils partent avec les `WEIGHTED_NORMAL` qui les accompagnent.
2. `RING_CAP` / `ROD_CAP` / `SECTOR_CAP` — la resolution des pieces de
   revolution : `count=64`, `32`, `40`, `24`... redescendent a ce que la camera
   peut lire. Une conduite de 10 cm de diametre ne vaut pas 32 cotes.
3. `CURVE_RES` / `CURVE_BEVEL_RES` — idem pour les tuyaux, qui sont des courbes
   et n'existent qu'a la conversion.
4. `KILL` — les familles de pieces qui N'EXISTENT PLUS a la taille visee. Elles
   ne sont pas rapetissees : elles sont construites puis mises a la POUBELLE, une
   collection separee que l'export ne voit pas. Construites, pour que le
   `build.py` de l'auteur continue de tourner sans une ligne de changement
   (`beam()` relit les sommets de la boite qu'il vient de creer).
5. `SCALE` — la taille finale, appliquee APRES coup par `rescale()` : le pylone
   est reconstruit a 5,3 m, pas mis a l'echelle depuis 24.
6. `TRIM` — un filtre par indice, pour les familles repetees en serie (une
   marche sur deux, un collier sur trois).
"""

from __future__ import annotations

import math
import bpy
from mathutils import Vector

COLLECTION = None
PARENT = None

# --------------------------------------------------------------------------
# Les leviers. Le pilote (`build_artery.py`) les pose avant chaque piece.
# --------------------------------------------------------------------------
BEVEL = False          #: levier 1 — chanfreins et normales ponderees
RING_CAP = 64          #: levier 2 — cotes d'une bague
ROD_CAP = 12           #: levier 2 — cotes d'un cylindre
SECTOR_CAP = 64        #: levier 2 — pas d'un secteur (arc)
CURVE_RES = 8          #: levier 3 — `resolution_u` d'un tuyau
CURVE_BEVEL_RES = 2    #: levier 3 — `bevel_resolution` d'un tuyau
KILL: set[str] = set()  #: levier 4 — familles envoyees a la poubelle
TRIM: dict[str, int] = {}  #: levier 6 — famille -> garder un element sur N

TRASH_NAME = 'AA | Poubelle'
_seen: dict[str, int] = {}

#: Le GRAND LIVRE : nom de famille -> [pieces construites, triangles bruts,
#: pieces jetees, triangles jetes]. C'est lui qui dit ce qu'une famille coute
#: AVANT toute fusion — le pylone consolide ses douze modules dans le
#: `build.py` de l'auteur, et apres ca plus rien n'est mesurable par nom.
LEDGER: dict[str, list[int]] = {}


def reset_levers() -> None:
    global BEVEL, RING_CAP, ROD_CAP, SECTOR_CAP, CURVE_RES, CURVE_BEVEL_RES
    global KILL, TRIM, _seen, LEDGER
    BEVEL, RING_CAP, ROD_CAP, SECTOR_CAP = False, 64, 12, 64
    CURVE_RES, CURVE_BEVEL_RES = 8, 2
    KILL, TRIM, _seen, LEDGER = set(), {}, {}, {}


def _killed(name: str) -> bool:
    """Vrai si `name` appartient a une famille supprimee, ou tombe hors du pas.

    ⚠️ LE COMPTEUR EST PAR NOM ET IL EST ORDONNE : `build.py` cree ses pieces
    dans un ordre fixe, donc « un collier sur trois » designe toujours les
    memes trois colliers. C'est ce qui rend la reconstruction deterministe.
    """
    for pattern in KILL:
        if name.startswith(pattern):
            return True
    for pattern, step in TRIM.items():
        if name.startswith(pattern):
            index = _seen.get(pattern, 0)
            _seen[pattern] = index + 1
            return index % step != 0
    return False


def _link(obj, name: str, tris: int) -> None:
    """Range l'objet dans la collection d'asset — ou dans la poubelle.

    ⚠️ LA POUBELLE EST UNE COLLECTION NON LIEE A LA SCENE. Les pieces jetees
    sont quand meme CONSTRUITES : `beam()` relit les sommets de la boite qu'il
    vient de creer, et `consolidate()` du pylone fusionne `control.children` —
    ne pas les creer casserait le `build.py` de l'auteur, qu'on veut verbatim.
    N'etant enfant d'aucun CTRL et dans aucune collection de scene, elles ne
    sont ni fusionnees, ni selectionnees, ni exportees."""
    entry = LEDGER.setdefault(name, [0, 0, 0, 0])
    entry[0] += 1
    entry[1] += tris
    if _killed(name):
        trash = bpy.data.collections.get(TRASH_NAME) or bpy.data.collections.new(TRASH_NAME)
        trash.objects.link(obj)
        obj['aa_killed'] = True
        entry[2] += 1
        entry[3] += tris
    else:
        COLLECTION.objects.link(obj)
        obj.parent = PARENT


def mesh(name, vertices, faces, material, bevel=.025):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    _link(obj, name, sum(len(f) - 2 for f in faces))
    data.materials.append(material)
    if bevel and BEVEL:
        modifier = obj.modifiers.new('Chanfreins editables', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 2
        obj.modifiers.new('Normales ponderees', 'WEIGHTED_NORMAL')
    return obj


def box(name, location, size, material, bevel=.035, angle=0):
    vertices = []
    for x, y, z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),
                    (1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]:
        x, y, z = x*size[0]/2, y*size[1]/2, z*size[2]/2
        vertices.append((location[0]+x*math.cos(angle)-z*math.sin(angle),
                         location[1]+y, location[2]+x*math.sin(angle)+z*math.cos(angle)))
    return mesh(name, vertices, [(0,4,6,2),(1,3,7,5),(0,1,5,4),
                                (2,6,7,3),(0,2,3,1),(4,5,7,6)], material, bevel)


def sector(name, sections, start, end, material, count=4, bevel=.02):
    count = max(2, min(count, SECTOR_CAP))
    closed = abs(end-start-math.tau) < 1e-6
    n = count if closed else count+1
    vertices = [(r*math.cos(start+(end-start)*i/count), y,
                 r*math.sin(start+(end-start)*i/count))
                for y, r in sections for i in range(n)]
    faces = []
    for j in range(len(sections)):
        k = (j+1) % len(sections)
        for i in range(count):
            following = (i+1) % n
            faces.append((j*n+i, j*n+following, k*n+following, k*n+i))
    if not closed:
        faces += [tuple(reversed([j*n for j in range(len(sections))])),
                  tuple(j*n+count for j in range(len(sections)))]
    return mesh(name, vertices, faces, material, bevel)


def ring(name, y, outer, inner, depth, material, center=(0,0), count=64):
    count = max(3, min(count, RING_CAP))
    sections = [(y-depth/2, outer),(y+depth/2, outer),
                (y+depth/2, inner),(y-depth/2, inner)]
    vertices = [(center[0]+r*math.cos(i*math.tau/count), dy,
                 center[1]+r*math.sin(i*math.tau/count))
                for dy, r in sections for i in range(count)]
    faces = [(j*count+i, j*count+(i+1)%count,
              ((j+1)%4)*count+(i+1)%count, ((j+1)%4)*count+i)
             for j in range(4) for i in range(count)]
    return mesh(name, vertices, faces, material, .008)


def rod(name, start, end, radius, material, count=12):
    count = max(3, min(count, ROD_CAP))
    delta = Vector(end)-Vector(start)
    rotation = delta.to_track_quat('Z','Y').to_matrix()
    vertices = [tuple(Vector(start)+rotation@Vector((radius*math.cos(i*math.tau/count),
                radius*math.sin(i*math.tau/count), h)))
                for h in (0,delta.length) for i in range(count)]
    faces = [tuple(reversed(range(count))), tuple(range(count,2*count))]
    faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    return mesh(name, vertices, faces, material, .008)


def hose(name, points, radius, material):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = radius
    data.bevel_resolution = CURVE_BEVEL_RES
    data.resolution_u = CURVE_RES
    spline = data.splines.new('BEZIER')
    spline.bezier_points.add(len(points)-1)
    for point, xyz in zip(spline.bezier_points, points):
        point.co = xyz
        point.handle_left_type = 'AUTO'
        point.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, data)
    # Un tuyau est une COURBE : ses triangles n'existent qu'a la conversion.
    # Le grand livre les recomptera apres coup (`build_artery.recount_curves`).
    _link(obj, name, 0)
    data.materials.append(material)
    return obj


def control(name, parent=None, explode=(0,0,0)):
    """⚠️ LE REPERE `CTRL | ` N'EST JAMAIS TOUCHE — c'est le contrat de noms.

    Aucun levier ne s'applique ici : les Empties sont crees, nommes et places
    par le code de l'auteur, mot pour mot. C'est ce qui rend le diff vide."""
    obj = bpy.data.objects.new('CTRL | '+name, None)
    COLLECTION.objects.link(obj)
    obj.parent = parent
    obj.empty_display_type = 'ARROWS'
    obj.empty_display_size = .4
    obj['explode_offset'] = list(explode)
    return obj


def uv_map(obj):
    """⛔ NEUTRALISE. L'auteur deplie ici sur SES atlas ; nous deplions en
    projection en boite a la densite du corridor, apres la fusion des groupes
    (`build_artery.py`). Deplier deux fois ne ferait qu'ecraser le premier."""
    return None


def prism_x(name, outline, x0, x1, material, bevel=.04):
    n = len(outline)
    vertices = [(x,y,z) for x in (x0,x1) for y,z in outline]
    faces = [tuple(reversed(range(n))),tuple(range(n,n*2))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vertices,faces,material,bevel)


def ring_x(name, center, outer, inner, depth, material, count=40):
    obj = ring(name,0,outer,inner,depth,material,count=count)
    for v in obj.data.vertices:
        x,y,z = v.co
        v.co = (center[0]+y,center[1]+x,center[2]+z)
    obj.data.update()
    return obj


def pivot(obj, location):
    obj.location = location
    bpy.context.view_layer.update()
    for child in obj.children:
        child.matrix_parent_inverse = obj.matrix_world.inverted()
