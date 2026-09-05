#!/usr/bin/env python3
"""Cuit l'ATLAS d'une coque : un albédo peint, et une hauteur à dériver.

    python3 tools/bake-atlas.py <coque.glb> --out assets/imported/textures/hulls
    python3 tools/bake-atlas.py <coque.glb> --out /tmp/x --check   # 2 passes + sha256

⚠️ POURQUOI CET OUTIL EXISTE — mesuré le 2026-09-05. Sur les 50 textures importées du
dépôt, **49 sont des niveaux de gris ou des normal maps**. Aucune coque ne porte
d'albédo peint : `HullDetail` pose une carte qui *multiplie* la couleur de palette du
`.glb` et ne peut donc, par construction, **jamais éclaircir** — ni peindre une bande,
ni un filet, ni un matricule. C'est l'écart mesuré avec les planches de concept, où
toute la richesse est de la peinture. Les réflexions d'environnement ont été testées
comme levier alternatif : négatif, deux passes monotones (`ADR-0045`).

## Ce qu'il cuit, et d'où ça vient

- **`<coque>_albedo.png`** — la couleur. Chaque triangle est rempli de la couleur de son
  matériau, **lue dans le `.glb`** (`baseColorFactor`) et non recopiée ici : la palette a
  une seule source de vérité, le kit, et elle transite par le fichier. Par-dessus, les
  lignes de panneau et l'usure d'arête.
- **`<coque>_height.png`** — le relief, en niveaux de gris, **à passer à
  `tools/derive-maps.py`** qui en tire normale, rugosité et occlusion. `ADR-0013` est
  formel : une normal map se dérive, elle ne se génère pas — une image violette
  plausible a des gradients faux et un éclairage incohérent.

## Les lignes de panneau ne sont pas inventées

Elles sont **les arêtes du maillage lui-même**. Une arête dont l'angle dièdre dépasse le
seuil est une cassure de surface : c'est exactement là qu'un panneau se termine sur un
vrai appareil. On projette ces arêtes dans l'espace UV et on les creuse. Le dessin suit
donc la géométrie au lieu de la contredire — ce qui est le défaut classique d'une
texture posée à côté de la forme qu'elle habille.

## Déterminisme

Aucun aléa non graine, ordre d'itération fixé par le nom de nœud, arithmétique numpy
seule. `--check` cuit deux fois et compare les sha256 : c'est l'invariant d'`ADR-0008`
appliqué à la texture. Un bake Cycles ne pourrait pas en dire autant — il échantillonne.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# --- Lecture glTF (pur Python — ce module ne doit PAS dépendre de Blender) ----
#
# ⚠️ Duplication assumée avec `tools/blender/lib/aegis_kit.py` (`_read_glb`,
# `glb_accessor`) : ce module-là importe `bpy` au chargement, donc il est inutilisable
# hors de Blender. Mutualiser demanderait d'extraire un troisième module ; à faire le
# jour où une troisième copie apparaît, pas avant.

_COMPONENT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read_glb(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    if raw[:4] != b"glTF":
        raise SystemExit(f"{path} n'est pas un glTF binaire")
    offset, gltf, blob = 12, None, b""
    while offset < len(raw):
        length, kind = struct.unpack_from("<II", raw, offset)
        chunk = raw[offset + 8: offset + 8 + length]
        if kind == 0x4E4F534A:
            gltf = json.loads(chunk)
        elif kind == 0x004E4942:
            blob = chunk
        offset += 8 + length + (-length % 4)
    if gltf is None:
        raise SystemExit(f"{path} : pas de bloc JSON")
    return gltf, blob


def accessor(gltf: dict, blob: bytes, index: int) -> list[tuple]:
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    fmt = _COMPONENT[acc["componentType"]]
    n = _COUNT[acc["type"]]
    size = struct.calcsize("<" + fmt) * n
    stride = view.get("byteStride", size)
    base = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    out = []
    for i in range(acc["count"]):
        out.append(struct.unpack_from("<" + fmt * n, blob, base + i * stride))
    return out


def primitives(gltf: dict, blob: bytes) -> list[dict]:
    """Toutes les primitives, triées par nom de nœud — l'ordre fait le déterminisme."""
    mats = [m.get("name", f"mat{i}") for i, m in enumerate(gltf.get("materials", []))]
    colors = []
    for m in gltf.get("materials", []):
        pbr = m.get("pbrMetallicRoughness", {})
        colors.append(tuple(pbr.get("baseColorFactor", [0.8, 0.8, 0.8, 1.0])))
    out = []
    for node in gltf.get("nodes", []):
        if "mesh" not in node:
            continue
        name = node.get("name", "?")
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            attrs = prim["attributes"]
            if "TEXCOORD_0" not in attrs:
                raise SystemExit(
                    f"'{name}' n'a pas de TEXCOORD_0 : impossible de cuire un atlas "
                    "sur un maillage sans UV (ADR-0028)"
                )
            pos = accessor(gltf, blob, attrs["POSITION"])
            uv = accessor(gltf, blob, attrs["TEXCOORD_0"])
            flat = ([t[0] for t in accessor(gltf, blob, prim["indices"])]
                    if "indices" in prim else list(range(len(pos))))
            mat_index = prim.get("material", 0)
            out.append({
                "node": name,
                "material": mats[mat_index] if mat_index < len(mats) else "?",
                "color": colors[mat_index] if mat_index < len(colors) else (0.8, 0.8, 0.8, 1.0),
                "pos": np.asarray(pos, dtype=np.float64),
                "uv": np.asarray(uv, dtype=np.float64),
                "tris": np.asarray(flat, dtype=np.int64).reshape(-1, 3),
            })
    out.sort(key=lambda p: (p["node"], p["material"]))
    return out


# --- Rasterisation ----------------------------------------------------------


def fill_triangles(rgb: np.ndarray, mask: np.ndarray, uv: np.ndarray,
                   tris: np.ndarray, color: tuple[float, float, float], side: int) -> None:
    """Remplit chaque triangle de sa couleur, par barycentriques exactes.

    ⚠️ De VRAIES barycentriques, pas un test de centre de gravité : le harnais hérité
    d'un script précédent rejetait un triangle sur deux et amputait 40 % des pixels
    d'une pièce (`pratique-revue-asset`, 2026-08-25).
    """
    px = uv[:, 0] * side
    py = (1.0 - uv[:, 1]) * side  # l'image a son origine en haut
    for ia, ib, ic in tris:
        ax, ay = px[ia], py[ia]
        bx, by = px[ib], py[ib]
        cx, cy = px[ic], py[ic]
        x0 = max(int(math.floor(min(ax, bx, cx))) - 1, 0)
        x1 = min(int(math.ceil(max(ax, bx, cx))) + 2, side)
        y0 = max(int(math.floor(min(ay, by, cy))) - 1, 0)
        y1 = min(int(math.ceil(max(ay, by, cy))) + 2, side)
        if x1 <= x0 or y1 <= y0:
            continue
        det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(det) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        w0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / det
        w1 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / det
        inside = (w0 >= -1e-9) & (w1 >= -1e-9) & (w0 + w1 <= 1.0 + 1e-9)
        if not inside.any():
            continue
        window = rgb[y0:y1, x0:x1]
        window[inside] = color
        mask[y0:y1, x0:x1][inside] = True


def draw_segment(buf: np.ndarray, a: tuple[float, float], b: tuple[float, float],
                 side: int, width: float, value: float) -> None:
    """Trace un segment épais dans un tampon (distance point-segment, anti-aliasé)."""
    ax, ay = a[0] * side, (1.0 - a[1]) * side
    bx, by = b[0] * side, (1.0 - b[1]) * side
    pad = width + 1.5
    x0 = max(int(math.floor(min(ax, bx) - pad)), 0)
    x1 = min(int(math.ceil(max(ax, bx) + pad)), side)
    y0 = max(int(math.floor(min(ay, by) - pad)), 0)
    y1 = min(int(math.ceil(max(ay, by) + pad)), side)
    if x1 <= x0 or y1 <= y0:
        return
    gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    if length2 < 1e-12:
        return
    t = np.clip(((gx - ax) * dx + (gy - ay) * dy) / length2, 0.0, 1.0)
    dist = np.hypot(gx - (ax + t * dx), gy - (ay + t * dy))
    strength = np.clip((width - dist) / max(width, 1e-6), 0.0, 1.0)
    window = buf[y0:y1, x0:x1]
    np.minimum(window, 1.0 - strength * (1.0 - value), out=window)


def sharp_edges(prim: dict, angle_deg: float) -> list[tuple[int, int]]:
    """Les arêtes dont l'angle dièdre dépasse le seuil — les vraies cassures.

    Une arête partagée par deux triangles dont les normales divergent est une fin de
    panneau. Une arête de bord (un seul triangle) en est une aussi : c'est une couture.
    """
    normals: dict[tuple[int, int], list[np.ndarray]] = {}
    pos = prim["pos"]
    for ia, ib, ic in prim["tris"]:
        n = np.cross(pos[ib] - pos[ia], pos[ic] - pos[ia])
        norm = np.linalg.norm(n)
        if norm < 1e-12:
            continue
        n = n / norm
        for u, v in ((ia, ib), (ib, ic), (ic, ia)):
            normals.setdefault((min(u, v), max(u, v)), []).append(n)
    cos_limit = math.cos(math.radians(angle_deg))
    out = []
    for (u, v), faces in normals.items():
        if len(faces) == 1:
            out.append((u, v))
        elif len(faces) >= 2 and float(np.dot(faces[0], faces[1])) < cos_limit:
            out.append((u, v))
    out.sort()
    return out


# --- Cuisson ----------------------------------------------------------------


def dilate(rgb: np.ndarray, mask: np.ndarray, passes: int) -> None:
    """Étale la couleur hors des îlots.

    ⚠️ SANS CELA, LA COQUE PORTE UN LISERÉ NOIR. Le filtrage bilinéaire et les mipmaps
    échantillonnent en dehors de l'îlot ; si le fond est vide, ils ramènent du vide sur
    le bord de chaque panneau. C'est le défaut classique d'un atlas cuit sans marge.
    """
    for _ in range(passes):
        grown = mask.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            shifted_mask = np.roll(mask, (dy, dx), axis=(0, 1))
            shifted_rgb = np.roll(rgb, (dy, dx), axis=(0, 1))
            take = shifted_mask & ~grown
            rgb[take] = shifted_rgb[take]
            grown |= take
        mask[...] = grown


def bake(glb: Path, side: int, angle_deg: float, line_px: float,
         groove: float, wear: float) -> tuple[Image.Image, Image.Image, dict]:
    gltf, blob = read_glb(glb)
    prims = primitives(gltf, blob)

    rgb = np.zeros((side, side, 3), dtype=np.float64)
    mask = np.zeros((side, side), dtype=bool)
    height = np.ones((side, side), dtype=np.float64)

    for prim in prims:
        fill_triangles(rgb, mask, prim["uv"], prim["tris"], prim["color"][:3], side)

    edges = 0
    for prim in prims:
        uv = prim["uv"]
        for u, v in sharp_edges(prim, angle_deg):
            draw_segment(height, uv[u], uv[v], side, line_px, groove)
            edges += 1

    # L'usure suit la rainure : là où la surface casse, la peinture s'use.
    worn = 1.0 - (1.0 - height) * wear
    rgb *= worn[..., None]

    dilate(rgb, mask, passes=max(4, int(side / 256)))
    dilate_height(height, mask, passes=max(4, int(side / 256)))

    albedo = Image.fromarray(np.clip(rgb * 255.0 + 0.5, 0, 255).astype(np.uint8))
    relief = Image.fromarray(np.clip(height * 255.0 + 0.5, 0, 255).astype(np.uint8))
    stats = {
        "primitives": len(prims),
        "triangles": int(sum(len(p["tris"]) for p in prims)),
        "aretes_creusees": edges,
        "couverture": float(mask.mean()),
        "materiaux": sorted({p["material"] for p in prims}),
    }
    return albedo, relief, stats


def dilate_height(height: np.ndarray, mask: np.ndarray, passes: int) -> None:
    """Même dilatation, sur le relief — sinon la rainure s'arrête net au bord d'îlot."""
    grown = mask.copy()
    for _ in range(passes):
        step = grown.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            shifted_mask = np.roll(grown, (dy, dx), axis=(0, 1))
            shifted = np.roll(height, (dy, dx), axis=(0, 1))
            take = shifted_mask & ~step
            height[take] = shifted[take]
            step |= take
        grown = step


def digest(image: Image.Image) -> str:
    return hashlib.sha256(image.tobytes()).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("glb", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="répertoire de sortie")
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--angle", type=float, default=28.0,
                        help="angle dièdre (deg) au-delà duquel une arête est creusée")
    parser.add_argument("--line-px", type=float, default=1.6, help="demi-largeur du trait")
    parser.add_argument("--groove", type=float, default=0.45,
                        help="fond de rainure, 0 = noir, 1 = plat")
    parser.add_argument("--wear", type=float, default=0.35,
                        help="part de la rainure reportée sur l'albédo")
    parser.add_argument("--check", action="store_true",
                        help="cuit deux fois et compare — l'invariant d'ADR-0008")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.glb.stem

    albedo, relief, stats = bake(args.glb, args.size, args.angle,
                                 args.line_px, args.groove, args.wear)
    if args.check:
        again = bake(args.glb, args.size, args.angle, args.line_px, args.groove, args.wear)
        same = digest(albedo) == digest(again[0]) and digest(relief) == digest(again[1])
        print("  determinisme : %s (albedo %s, hauteur %s)"
              % ("OK" if same else "ECHEC", digest(albedo), digest(relief)))
        if not same:
            return 1

    albedo_path = args.out / f"{stem}_albedo.png"
    relief_path = args.out / f"{stem}_height.png"
    albedo.save(albedo_path)
    relief.save(relief_path)

    print(f"  {stats['primitives']} primitives, {stats['triangles']} triangles, "
          f"{stats['aretes_creusees']} aretes creusees")
    print(f"  couverture de l'atlas : {stats['couverture'] * 100.0:.1f} %")
    print(f"  materiaux : {', '.join(stats['materiaux'])}")
    print(f"  ecrit {albedo_path} ({albedo.size[0]}x{albedo.size[1]})")
    print(f"  ecrit {relief_path}")
    print("  ⚠️ la hauteur n'est PAS une normale : la passer a tools/derive-maps.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
