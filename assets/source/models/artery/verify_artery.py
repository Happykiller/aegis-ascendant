"""Verifie les binaires livres — SUR LES BINAIRES, apres REIMPORT.

    blender-aegis -t 1 -b -noaudio --python assets/source/models/artery/verify_artery.py

⚠️ CE QUI SE VERIFIE ICI NE SE VERIFIE PAS DANS BLENDER AVANT L'EXPORT. Un glTF
n'execute pas les pilotes de Blender (`ADR-0046`) : une piece qui bouge dans la
scene d'auteur peut sortir avec une animation VIDE, sans une erreur ni une ligne
de journal. Et une coque sans UV s'importe sans le moindre avertissement
(`ADR-0028`). Les deux defauts sont totalement silencieux ; ils ne se voient
qu'ici.

Quatre controles, dans l'ordre de ce qu'ils protegent :

1. **Le contrat de noms** — chaque repere `CTRL | ` du binaire de l'auteur est
   retrouve dans le notre, a la meme position monde, au 1/10 de mm. Pour le
   pylone, qui est reconstruit a 5,3 m, la comparaison se fait apres division
   par le facteur mesure, et les reperes disparus sont NOMMES.
2. **Les clips se rejouent** — le `.glb` est reimporte, chaque piste est
   demutee a son tour, et on mesure le DEPLACEMENT REEL des sommets evalues
   (depsgraph), peau comprise. Un clip dont l'amplitude est nulle est un clip
   mort, et c'est exactement ce qu'un compteur de canaux ne dit pas.
3. **La continuite `Rupture` -> `Rompu`** — derniere image de l'un contre
   premiere image de l'autre, sommet par sommet. Si elle casse, la piece saute
   d'une pose a l'autre a l'instant precis ou le joueur regarde.
4. **UV et images** — `TEXCOORD_0` compte sur chaque primitive, zero image.
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
if not (HERE / 'author').is_dir():  # pragma: no cover
    HERE = Path(bpy.data.filepath).resolve().parent
REPO = HERE.parents[3]
OUT = REPO / 'assets' / 'imported' / 'models' / 'backgrounds'
AUTHOR = Path.home() / 'aegis-ascendant_gpt_models'

#: (livre, binaire par module de l'auteur, facteur attendu, ASSET COMPLET de l'auteur)
#:
#: ⚠️ LA TROISIEME COLONNE DE REFERENCE N'EST PAS UN LUXE. Les exports PAR MODULE
#: de l'auteur portent, chacun, UN repere fige dans la pose ROMPUE de son
#: mecanisme parent (`Demi collier 1.13 1`, `Noyau secondaire 0.79`, `Noyau
#: Ligne 011`). Ce n'est pas notre reconstruction qui derive : on le prouve en
#: comparant les sous-ensembles de l'auteur A SON PROPRE ASSET COMPLET, qui
#: donne exactement le meme ecart sur exactement le meme repere. Contre l'asset
#: complet, notre ecart est de 0,000000 mm sur 100 pct des reperes.
PAIRS = [
    ('stern_pylon.glb',
     AUTHOR / 'pylone-technique/v1/exports/Stern_Pylon_01.glb', None, None),
    ('artery_conduit.glb',
     AUTHOR / 'conduite-energetique/v1/exports/conduit_droit.glb', 1.0,
     AUTHOR / 'conduite-energetique/v1/exports/conduite_energetique.glb'),
    ('artery_conduit_bend.glb',
     AUTHOR / 'conduite-energetique/v1/exports/conduit_coude.glb', 1.0,
     AUTHOR / 'conduite-energetique/v1/exports/conduite_energetique.glb'),
    ('artery_hose.glb',
     AUTHOR / 'flexible-technique/v1/exports/flexible_droit.glb', 1.0, None),
    ('artery_hose_bend.glb',
     AUTHOR / 'flexible-technique/v1/exports/flexible_coude.glb', 1.0,
     AUTHOR / 'flexible-technique/v1/exports/flexible_technique.glb'),
]

_COMP = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2), 5123: ('H', 2),
         5125: ('I', 4), 5126: ('f', 4)}
_N = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


# --------------------------------------------------------------------------
# Lecture du binaire, sans Blender
# --------------------------------------------------------------------------

def load(path: Path):
    data = path.read_bytes()
    assert data[:4] == b'glTF', path
    off, gltf, blob = 12, None, b''
    while off < len(data):
        length, kind = struct.unpack_from('<II', data, off)
        chunk = data[off + 8: off + 8 + length]
        if kind == 0x4E4F534A:
            gltf = json.loads(chunk.decode('utf-8'))
        else:
            blob = chunk
        off += 8 + length + (-length % 4)
    return gltf, blob


def trs(node):
    if 'matrix' in node:
        m = node['matrix']
        return [[m[0], m[4], m[8], m[12]], [m[1], m[5], m[9], m[13]],
                [m[2], m[6], m[10], m[14]], [m[3], m[7], m[11], m[15]]]
    t = node.get('translation', [0, 0, 0])
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    s = node.get('scale', [1, 1, 1])
    R = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    M = [[R[i][j] * s[j] for j in range(3)] + [t[i]] for i in range(3)]
    return M + [[0, 0, 0, 1]]


def mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)]
            for i in range(4)]


def ctrl_positions(path: Path) -> dict[str, tuple[float, float, float]]:
    gltf, _ = load(path)
    nodes = gltf.get('nodes', [])
    world: dict[int, list] = {}
    ident = [[1 if i == j else 0 for j in range(4)] for i in range(4)]

    def walk(i, P):
        M = mul(P, trs(nodes[i]))
        world[i] = M
        for c in nodes[i].get('children', []):
            walk(c, M)

    for scene in gltf.get('scenes', []):
        for root in scene.get('nodes', []):
            walk(root, ident)
    for i in range(len(nodes)):
        if i not in world:
            walk(i, ident)
    return {nodes[i].get('name', ''): (world[i][0][3], world[i][1][3], world[i][2][3])
            for i in range(len(nodes)) if nodes[i].get('name', '').startswith('CTRL')}


def attributes(path: Path) -> dict:
    gltf, _ = load(path)
    prims, no_uv, no_tan, tris = 0, 0, 0, 0
    per_material: dict[str, int] = {}
    mats = [m.get('name', '?') for m in gltf.get('materials', [])]
    for mesh in gltf.get('meshes', []):
        for prim in mesh['primitives']:
            prims += 1
            if 'TEXCOORD_0' not in prim['attributes']:
                no_uv += 1
            if 'TANGENT' not in prim['attributes']:
                no_tan += 1
            n = (gltf['accessors'][prim['indices']]['count'] // 3 if 'indices' in prim
                 else gltf['accessors'][prim['attributes']['POSITION']]['count'] // 3)
            tris += n
            name = mats[prim['material']] if 'material' in prim else '(aucun)'
            per_material[name] = per_material.get(name, 0) + n
    return {'primitives': prims, 'sans_uv': no_uv, 'sans_tangente': no_tan,
            'triangles': tris, 'images': len(gltf.get('images', [])),
            'materiaux': per_material, 'skins': len(gltf.get('skins', [])),
            'animations': [(a.get('name', '?'), len(a['channels']))
                           for a in gltf.get('animations', [])],
            'octets': path.stat().st_size}


# --------------------------------------------------------------------------
# Rejeu, dans Blender, sur le binaire REIMPORTE
# --------------------------------------------------------------------------

def wipe() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def sample(fps: int = 30):
    """Positions monde de tous les sommets EVALUES (modificateurs compris)."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out = []
    for obj in sorted(bpy.data.objects, key=lambda o: o.name):
        if obj.type != 'MESH':
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for vertex in mesh.vertices:
            out.append(matrix @ vertex.co)
        evaluated.to_mesh_clear()
    return out


def tracks() -> dict[str, list]:
    found: dict[str, list] = {}
    for obj in bpy.data.objects:
        if not obj.animation_data:
            continue
        for track in obj.animation_data.nla_tracks:
            found.setdefault(track.name, []).append((obj, track))
    return found


def solo(name: str | None) -> None:
    for obj in bpy.data.objects:
        if not obj.animation_data:
            continue
        obj.animation_data.action = None
        for track in obj.animation_data.nla_tracks:
            track.mute = track.name != name


def replay(path: Path) -> dict:
    wipe()
    bpy.ops.import_scene.gltf(filepath=str(path))
    clips = tracks()
    report = {}
    poses: dict[str, dict[str, list]] = {}
    for name in sorted(clips):
        solo(name)
        frames = []
        end = 1
        for _obj, track in clips[name]:
            for strip in track.strips:
                end = max(end, int(round(strip.frame_end)))
        for frame in (1, end):
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            frames.append(sample())
        # amplitude : le plus grand deplacement d'un sommet sur tout le clip
        amplitude = 0.0
        rest = None
        for frame in range(1, end + 1, max(1, (end - 1) // 12 or 1)):
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            current = sample()
            if rest is None:
                rest = current
            for a, b in zip(rest, current):
                amplitude = max(amplitude, (a - b).length)
        poses[name] = {'debut': frames[0], 'fin': frames[1], 'images': end}
        report[name] = {'images': end, 'amplitude_m': round(amplitude, 6),
                        'objets_animes': len(clips[name])}
    # ⚠️ TROIS CLIPS PEUVENT BOUGER ET RESTER INDISCERNABLES. Sur le pylone,
    # `Service` et `Refroidissement` different par une POSE STATIQUE des lames
    # (0,035 rad contre 0,32) : l'amplitude INTERNE de chacun est minuscule, et
    # un compteur d'amplitude seul les declarerait tous les deux « vivants »
    # sans voir qu'ils sont differents. On mesure donc aussi l'ecart ENTRE
    # clips, a l'image 1.
    names = sorted(poses)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pa, pb = poses[a]['debut'], poses[b]['debut']
            if len(pa) == len(pb):
                report[f'_ecart_{a}_vs_{b}_m'] = round(
                    max((p - q).length for p, q in zip(pa, pb)), 6)
    # continuite : derniere pose de Rupture == premiere pose de Rompu
    if 'Rupture' in poses and 'Rompu' in poses:
        a, b = poses['Rupture']['fin'], poses['Rompu']['debut']
        gap = max((p - q).length for p, q in zip(a, b)) if len(a) == len(b) else float('nan')
        report['_continuite_rupture_rompu_m'] = round(gap, 9)
    solo(None)
    return report


def main() -> None:
    results = []
    for name, author_path, expected, whole_path in PAIRS:
        ours = OUT / name
        line = {'fichier': name, **attributes(ours)}
        mine = ctrl_positions(ours)
        theirs = ctrl_positions(author_path) if author_path.exists() else {}
        # facteur d'echelle mesure sur les reperes communs
        common = sorted(set(mine) & set(theirs))
        factor, gap = expected if expected else 1.0, 0.0
        if common and expected is None:
            # ⚠️ LE FACTEUR SE MESURE SUR LES REPERES, IL N'EST PAS RECOPIE DU
            # SCRIPT DE CONSTRUCTION. C'est ce qui prouve que le pylone livre
            # est bien celui de l'auteur a 5,3 m, et pas une piece voisine.
            big = [k for k in common if sum(c * c for c in theirs[k]) ** .5 > 1e-3]
            factor = (sum(sum(c * c for c in mine[k]) ** .5 for k in big)
                      / sum(sum(c * c for c in theirs[k]) ** .5 for k in big))
        if common:
            gap = max(max(abs(mine[k][i] - theirs[k][i] * factor) for i in range(3))
                      for k in common)
        line['ctrl_auteur'] = len(theirs)
        line['ctrl_livre'] = len(mine)
        line['ctrl_manquants'] = sorted(set(theirs) - set(mine))
        line['ctrl_ajoutes'] = sorted(set(mine) - set(theirs))
        line['facteur_mesure'] = round(factor, 6)
        line['ecart_max_mm'] = round(gap * 1000.0, 6)
        if whole_path and whole_path.exists():
            whole = ctrl_positions(whole_path)
            shared = sorted(set(mine) & set(whole))
            line['ecart_max_mm_vs_asset_complet'] = round(1000.0 * max(
                max(abs(mine[k][i] - whole[k][i]) for i in range(3))
                for k in shared), 6)
            line['reperes_figes_par_l_auteur'] = sorted(
                k for k in sorted(set(theirs) & set(whole))
                if max(abs(theirs[k][i] - whole[k][i]) for i in range(3)) > 1e-9)
        line['clips'] = replay(ours)
        results.append(line)
        print('VERIFY ' + json.dumps(line, ensure_ascii=False))
    print('VERIFY_TOTAL ' + json.dumps(results, ensure_ascii=False))


main()
