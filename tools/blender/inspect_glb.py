#!/usr/bin/env python3
"""Relit un .glb livre et imprime ce qui se verifie sans Blender.

    python3 tools/blender/inspect_glb.py assets/imported/models/bosses/pale_leviathan.glb

Trois choses, et elles se lisent dans le JSON/binaire du fichier, pas dans le
souvenir qu'on a du script qui l'a produit :

  * la **repartition des materiaux** — en sommets, en triangles et en AIRE.
    L'aire est la seule des trois qui dise ce que l'oeil verra : un materiau
    peut porter 30 % des sommets sur des greebles minuscules et ne rien couvrir ;
  * le **contrat de noms** — noeuds maillees, parents, comptes ;
  * les **attributs de sommet** presents (`TEXCOORD_0`, `TANGENT`).
"""

from __future__ import annotations

import json
import math
import struct
import sys

_COMP = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2),
         5125: ("I", 4), 5126: ("f", 4)}
_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def load(path: str) -> tuple[dict, bytes]:
    with open(path, "rb") as fh:
        data = fh.read()
    assert data[:4] == b"glTF", "pas un .glb"
    off, gltf, blob = 12, None, b""
    while off < len(data):
        length, kind = struct.unpack_from("<II", data, off)
        chunk = data[off + 8: off + 8 + length]
        if kind == 0x4E4F534A:
            gltf = json.loads(chunk.decode("utf-8"))
        else:
            blob = chunk
        off += 8 + length + (-length % 4)
    return gltf, blob


def read_accessor(gltf: dict, blob: bytes, index: int) -> list:
    acc = gltf["accessors"][index]
    fmt, size = _COMP[acc["componentType"]]
    n = _COUNT[acc["type"]]
    view = gltf["bufferViews"][acc["bufferView"]]
    base = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride") or (size * n)
    out = []
    for i in range(acc["count"]):
        out.append(struct.unpack_from("<" + fmt * n, blob, base + i * stride))
    return out


def main() -> None:
    path = sys.argv[1]
    gltf, blob = load(path)
    mats = [m["name"] for m in gltf.get("materials", [])]

    verts: dict[str, int] = {}
    tris: dict[str, int] = {}
    area: dict[str, float] = {}
    attrs: dict[str, set] = {}
    total_v = total_t = 0

    node_of_mesh: dict[int, str] = {}
    for node in gltf["nodes"]:
        if "mesh" in node:
            node_of_mesh.setdefault(node["mesh"], node.get("name", "?"))

    for mi, mesh in enumerate(gltf["meshes"]):
        name = node_of_mesh.get(mi, mesh.get("name", "?"))
        for prim in mesh["primitives"]:
            mat = mats[prim["material"]] if "material" in prim else "(aucun)"
            pos = read_accessor(gltf, blob, prim["attributes"]["POSITION"])
            idx = [i[0] for i in read_accessor(gltf, blob, prim["indices"])]
            verts[mat] = verts.get(mat, 0) + len(pos)
            tris[mat] = tris.get(mat, 0) + len(idx) // 3
            total_v += len(pos)
            total_t += len(idx) // 3
            acc = 0.0
            for k in range(0, len(idx), 3):
                a, b, c = (pos[idx[k]], pos[idx[k + 1]], pos[idx[k + 2]])
                u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
                v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
                cx = u[1] * v[2] - u[2] * v[1]
                cy = u[2] * v[0] - u[0] * v[2]
                cz = u[0] * v[1] - u[1] * v[0]
                acc += 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)
            area[mat] = area.get(mat, 0.0) + acc
            attrs.setdefault(name, set()).update(prim["attributes"].keys())

    total_a = sum(area.values())
    print(f"--- {path}")
    print(f"  {total_v} sommets, {total_t} triangles, "
          f"{total_a:.1f} m2 de surface, {len(gltf['meshes'])} maillages")
    print(f"  {'materiau':<22} {'sommets':>9} {'tris':>9} {'aire m2':>9}   part v / t / aire")
    for mat in sorted(area, key=lambda m: -area[m]):
        print(f"  {mat:<22} {verts[mat]:>9} {tris[mat]:>9} {area[mat]:>9.2f}   "
              f"{100.0 * verts[mat] / total_v:5.1f} % "
              f"{100.0 * tris[mat] / total_t:5.1f} % "
              f"{100.0 * area[mat] / total_a:5.1f} %")

    missing = [n for n, a in attrs.items()
               if "TEXCOORD_0" not in a or "TANGENT" not in a]
    print(f"  UV+tangentes sur {len(attrs) - len(missing)}/{len(attrs)} maillages"
          + (f" — MANQUE : {missing}" if missing else ""))

    parent = {}
    for i, node in enumerate(gltf["nodes"]):
        for c in node.get("children", []):
            parent[c] = node.get("name", "?")
    print("  hierarchie des noeuds maillees :")
    for i, node in enumerate(gltf["nodes"]):
        if "mesh" in node:
            print(f"    {node.get('name', '?'):<20} parent={parent.get(i, '(racine)')}")


if __name__ == "__main__":
    main()
