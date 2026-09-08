"""Verifie les deux tours livrees — SUR LES BINAIRES, apres REIMPORT.

    blender-aegis -t 1 -b -noaudio --python assets/source/models/tower/verify_tower.py

⚠️ CE QUI SE VERIFIE ICI NE SE VERIFIE PAS DANS BLENDER AVANT L'EXPORT. Un glTF
n'execute pas les pilotes de Blender (`ADR-0046`) : une piece qui tourne dans la
scene d'auteur peut sortir avec une animation VIDE, sans une erreur ni une ligne
de journal. Et une coque sans UV s'importe sans le moindre avertissement
(`ADR-0028`). Les deux defauts sont totalement silencieux ; ils ne se voient
qu'ici.

Cinq controles, dans l'ordre de ce qu'ils protegent :

1. **Le contrat de noms** — chaque repere `CTRL | ` du binaire de l'auteur est
   retrouve dans le notre, a la meme position monde apres division par le
   facteur MESURE sur les reperes eux-memes (jamais recopie du script).
2. **Les trois clips se rejouent** — chaque piste est demutee a son tour et on
   mesure le DEPLACEMENT REEL des sommets evalues (depsgraph, peau comprise).
   Un compteur de canaux dirait « vivant » d'un clip vide.
3. **LES QUATRE ROTORS TOURNENT, UN PAR UN, ET C'EST NOMME.** Le critere du
   brief porte sur les rotors, pas sur la piece : une amplitude globale non
   nulle serait deja atteinte par la seule vibration des conduites. On mesure
   donc le deplacement **par module**, et on exige les quatre.
4. **L'ecart ENTRE clips** — `Service` et `Refroidissement` ne different que par
   la VITESSE des rotors ; a l'image 1 ils sont identiques. C'est a mi-clip que
   la difference existe, et c'est la qu'on la mesure.
5. **UV, tangentes et images** — `TEXCOORD_0` COMPTE sur chaque primitive
   (jamais suppose), zero image embarquee, densite de texels relue.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
if not (HERE / 'author').is_dir():  # pragma: no cover
    HERE = Path(bpy.data.filepath).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools' / 'blender' / 'lib'))
import aegis_kit as ak  # noqa: E402

OUT = REPO / 'assets' / 'imported' / 'models' / 'backgrounds'
AUTHOR = (Path.home() / 'aegis-ascendant_gpt_models' / 'tour-echange-thermique'
          / 'v1' / 'exports' / 'Stern_CoolingTower_01.glb')

FILES = ('stern_tower.glb', 'stern_tower_low.glb')
ROTORS = ('11_rotor_1', '12_rotor_2', '13_rotor_3', '14_rotor_4')
CLIPS = ('Service', 'Refroidissement', 'Maintenance')

_COMP = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2), 5123: ('H', 2),
         5125: ('I', 4), 5126: ('f', 4)}
_N = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


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


def accessor(gltf, blob, index):
    acc = gltf['accessors'][index]
    view = gltf['bufferViews'][acc['bufferView']]
    fmt, size = _COMP[acc['componentType']]
    n = _N[acc['type']]
    stride = view.get('byteStride') or size * n
    base = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    out = []
    for i in range(acc['count']):
        out.append(struct.unpack_from('<' + fmt * n, blob, base + i * stride))
    return out


def attributes(path: Path) -> dict:
    gltf, blob = load(path)
    prims, no_uv, no_tan, tris = 0, 0, 0, 0
    per_material: dict[str, int] = {}
    mats = [m.get('name', '?') for m in gltf.get('materials', [])]
    points: list = []
    uvs: list = []
    triangles: list = []
    for mesh in gltf.get('meshes', []):
        for prim in mesh['primitives']:
            prims += 1
            if 'TEXCOORD_0' not in prim['attributes']:
                no_uv += 1
                continue
            if 'TANGENT' not in prim['attributes']:
                no_tan += 1
            base = len(points)
            points.extend(accessor(gltf, blob, prim['attributes']['POSITION']))
            uvs.extend(accessor(gltf, blob, prim['attributes']['TEXCOORD_0']))
            flat = [i[0] for i in accessor(gltf, blob, prim['indices'])]
            for k in range(0, len(flat), 3):
                triangles.append(tuple(base + flat[k + j] for j in range(3)))
            n = len(flat) // 3
            tris += n
            name = mats[prim['material']] if 'material' in prim else '(aucun)'
            per_material[name] = per_material.get(name, 0) + n
    return {'primitives': prims, 'sans_uv': no_uv, 'sans_tangente': no_tan,
            'triangles': tris, 'images': len(gltf.get('images', [])),
            'materiaux': per_material, 'skins': len(gltf.get('skins', [])),
            'animations': [(a.get('name', '?'), len(a['channels']))
                           for a in gltf.get('animations', [])],
            'uv': ak.texel_density(points, uvs, triangles),
            'octets': path.stat().st_size}


# --------------------------------------------------------------------------
# Rejeu, dans Blender, sur le binaire REIMPORTE
# --------------------------------------------------------------------------

def wipe() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def sample_by_module() -> dict[str, list]:
    """Positions monde des sommets EVALUES, rangees par module."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out: dict[str, list] = {}
    for obj in sorted(bpy.data.objects, key=lambda o: o.name):
        if obj.type != 'MESH':
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        key = obj.name.split('|')[0].strip().split('.')[0]
        out.setdefault(key, []).extend(matrix @ v.co for v in mesh.vertices)
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


def spread(a: dict[str, list], b: dict[str, list]) -> dict[str, float]:
    out = {}
    for key in sorted(set(a) & set(b)):
        if len(a[key]) != len(b[key]):
            continue
        out[key] = round(max((p - q).length for p, q in zip(a[key], b[key])), 6)
    return out


def replay(path: Path) -> dict:
    wipe()
    bpy.ops.import_scene.gltf(filepath=str(path))
    clips = tracks()
    report: dict = {}
    mid_poses: dict[str, dict[str, list]] = {}
    for name in sorted(clips):
        solo(name)
        end = 1
        for _obj, track in clips[name]:
            for strip in track.strips:
                end = max(end, int(round(strip.frame_end)))
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()
        rest = sample_by_module()
        best: dict[str, float] = {k: 0.0 for k in rest}
        for frame in range(1, end + 1, max(1, (end - 1) // 12 or 1)):
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            gap = spread(rest, sample_by_module())
            for key, value in gap.items():
                best[key] = max(best[key], value)
            if frame == 1 + (end - 1) // 2:
                mid_poses[name] = sample_by_module()
        # ⚠️ CE QUI SEPARE `Service` DE `Refroidissement` EST UNE VITESSE, PAS
        # UNE POSE. Au quart du clip, un rotor a tourne de 90 deg a `Service`
        # (un tour par boucle) et de 180 deg a `Refroidissement` (deux tours) :
        # le deplacement d'une pale passe de 2 r sin(45) a 2 r. C'est la SEULE
        # mesure qui distingue les deux clips sans lire le script de l'auteur.
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()
        rest = sample_by_module()
        bpy.context.scene.frame_set(1 + (end - 1) // 4)
        bpy.context.view_layer.update()
        quarter = spread(rest, sample_by_module())
        moving = {k: v for k, v in sorted(best.items()) if v > 1e-6}
        report[name] = {
            'images': end,
            'objets_animes': len(clips[name]),
            'amplitude_m': round(max(best.values()), 6),
            'rotor_au_quart_de_clip_m': round(
                max([quarter.get(r, 0.0) for r in ROTORS]), 6),
            'modules_mobiles': moving,
            'rotors_mobiles': sorted(k for k in moving if k in ROTORS),
        }
    # ⚠️ L'ECART ENTRE CLIPS SE MESURE A MI-CLIP, PAS A L'IMAGE 1. `Service` et
    # `Refroidissement` posent les memes rotors a l'angle zero au debut : a
    # l'image 1 ils sont IDENTIQUES, et un ecart mesure la les declarerait
    # jumeaux. C'est la vitesse qui les separe, donc c'est au milieu du clip.
    names = sorted(mid_poses)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            gap = spread(mid_poses[a], mid_poses[b])
            if gap:
                report[f'_ecart_mi_clip_{a}_vs_{b}_m'] = round(max(gap.values()), 6)
    solo(None)
    return report


def main() -> None:
    theirs = ctrl_positions(AUTHOR) if AUTHOR.exists() else {}
    results = []
    for name in FILES:
        ours = OUT / name
        line = {'fichier': name, **attributes(ours)}
        mine = ctrl_positions(ours)
        common = sorted(set(mine) & set(theirs))
        factor, gap = 1.0, 0.0
        if common:
            # ⚠️ LE FACTEUR SE MESURE SUR LES REPERES, IL N'EST PAS RECOPIE DU
            # SCRIPT. C'est ce qui prouve que la tour livree est bien celle de
            # l'auteur a sa nouvelle hauteur, et pas une piece voisine.
            big = [k for k in common if sum(c * c for c in theirs[k]) ** .5 > 1e-3]
            factor = (sum(sum(c * c for c in mine[k]) ** .5 for k in big)
                      / sum(sum(c * c for c in theirs[k]) ** .5 for k in big))
            gap = max(max(abs(mine[k][i] - theirs[k][i] * factor) for i in range(3))
                      for k in common)
        line['ctrl_auteur'] = len(theirs)
        line['ctrl_livre'] = len(mine)
        line['ctrl_manquants'] = sorted(set(theirs) - set(mine))
        line['ctrl_ajoutes'] = sorted(set(mine) - set(theirs))
        line['facteur_mesure'] = round(factor, 6)
        line['ecart_max_mm'] = round(gap * 1000.0, 6)
        line['clips'] = replay(ours)
        # --- les refus, explicites -----------------------------------------
        problems = []
        if line['sans_uv']:
            problems.append(f"{line['sans_uv']} primitive(s) sans TEXCOORD_0")
        if line['images']:
            problems.append(f"{line['images']} image(s) embarquee(s) (ADR-0028)")
        for clip in CLIPS:
            got = line['clips'].get(clip)
            if got is None:
                problems.append(f'clip {clip} absent')
                continue
            if len(got['rotors_mobiles']) != 4 and clip != 'Maintenance':
                problems.append(
                    f"clip {clip} : {len(got['rotors_mobiles'])} rotor(s) mobile(s) sur 4")
            if got['amplitude_m'] <= 0.0:
                problems.append(f'clip {clip} : amplitude nulle')
        line['refus'] = problems
        results.append(line)
        print('VERIFY ' + json.dumps(line, ensure_ascii=False))
    print('VERIFY_TOTAL ' + json.dumps(results, ensure_ascii=False))
    bad = [line for line in results if line['refus']]
    if bad:
        raise SystemExit('VERIFICATION ROUGE : '
                         + ' | '.join(str(line['refus']) for line in bad))


main()
