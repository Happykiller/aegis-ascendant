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

## ⚠️ LE SENS DE V — DEFAUT TROUVE LE 2026-09-06, ET IL ETAIT TOTALEMENT SILENCIEUX

Cet outil ecrivait ses deux cartes **retournees verticalement**. En glTF, `v = 0` designe
le HAUT de l'image (§3.8.2 de la specification) ; le code posait le texel a la ligne
`(1 - v) * cote`, c'est-a-dire en bas. Godot lit la meme convention que glTF, et Blender
y revient apres l'inversion de son importeur : les deux moteurs echantillonnaient donc le
MIROIR de ce qu'on avait cuit.

Sur une feuille repetable, un retournement ne se voit pas — le motif est statistiquement
le meme a l'endroit et a l'envers, et c'est pourquoi le defaut a survecu. **Sur un atlas,
il melange toute la coque** : la verriere prend la peinture du sabord, l'aile prend celle
d'une tuyere. Trouve en REGARDANT la coque habillee (`ADR-0006`), jamais par un test.

⚠️ Consequence : **tout atlas cuit avant cette date est faux et doit etre recuit.**

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


def _to_linear(srgb: np.ndarray) -> np.ndarray:
    """Decode du sRGB vers le lineaire — l'inverse exact de `_to_srgb`."""
    low = srgb / 12.92
    high = np.power((srgb + 0.055) / 1.055, 2.4)
    return np.where(srgb <= 0.04045, low, high)


def sheet_of(gltf: dict, blob: bytes, index: int, cache: dict) -> np.ndarray:
    """L'image embarquee n° `index`, decodee en LINEAIRE.

    ⚠️ Une carte d'albedo d'un glTF est en sRGB par specification, et tout le reste de
    cet outil calcule en lineaire (voir `_to_srgb`). La decoder ici est la seule facon
    que la teinte moyenne d'un materiau texture soit comparable a un `baseColorFactor`,
    qui, lui, est lineaire. Sans cette conversion, les coques a textures ressortiraient
    systematiquement plus claires que les coques a facteurs.
    """
    if index in cache:
        return cache[index]
    view = gltf["bufferViews"][gltf["images"][index]["bufferView"]]
    start = view.get("byteOffset", 0)
    raw = blob[start:start + view["byteLength"]]
    import io

    image = Image.open(io.BytesIO(raw)).convert("RGB")
    cache[index] = _to_linear(np.asarray(image, dtype=np.float64) / 255.0)
    return cache[index]


def materials(gltf: dict, blob: bytes) -> list[dict]:
    """La matiere de chaque materiau : une teinte, et si elle existe, sa feuille.

    ⚠️ TOUTES LES COQUES NE PORTENT PAS LEUR PALETTE EN FACTEURS. `ADR-0047` a ete ecrit
    sur les coques du kit, dont chaque materiau est un `baseColorFactor` et rien d'autre.
    Une coque tierce comme la `specter_9_d` n'en a AUCUN : ses quatre teintes vivent dans
    des textures (`white/blue/red/metal_basecolor`) appliquees par materiau. Lire le seul
    facteur y rendait un gris de defaut sur 90 %% de la coque — un aplat, silencieux.

    Deux regimes, et le fichier tranche :
      facteur  : la teinte EST le `baseColorFactor`, lu tel quel.
      feuille  : la teinte est la MOYENNE de la carte, en lineaire ; et si le maillage a
                 garde le jeu d'UV de cette carte (`texCoord`), la carte est REPORTEE
                 dans l'atlas au lieu d'etre moyennee. C'est ce qui evite qu'un
                 depliage en atlas ne fasse perdre la matiere qu'on avait deja.
    """
    cache: dict[int, np.ndarray] = {}
    out = []
    for index, material in enumerate(gltf.get("materials", [])):
        pbr = material.get("pbrMetallicRoughness", {})
        base = pbr.get("baseColorTexture")
        entry = {
            "name": material.get("name", f"mat{index}"),
            "color": tuple(pbr.get("baseColorFactor", [0.8, 0.8, 0.8, 1.0]))[:3],
            "sheet": None,
            "texcoord": 0,
            "mode": "facteur",
        }
        if base is not None:
            source = gltf["textures"][base["index"]]["source"]
            sheet = sheet_of(gltf, blob, source, cache)
            entry["sheet"] = sheet
            entry["texcoord"] = int(base.get("texCoord", 0))
            entry["color"] = tuple(float(v) for v in sheet.reshape(-1, 3).mean(axis=0))
            entry["mode"] = "feuille"
        out.append(entry)
    return out


def primitives(gltf: dict, blob: bytes) -> list[dict]:
    """Toutes les primitives, triées par nom de nœud — l'ordre fait le déterminisme."""
    mats = materials(gltf, blob)
    fallback = {"name": "?", "color": (0.8, 0.8, 0.8), "sheet": None,
                "texcoord": 0, "mode": "facteur"}
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
            material = mats[mat_index] if mat_index < len(mats) else fallback
            # Le jeu d'UV de la feuille. Absent (une courbe convertie n'en a pas), on
            # retombe sur la teinte moyenne : jamais sur les UV de l'atlas, qui
            # echantillonneraient la feuille a une adresse qui n'est pas la sienne.
            key = "TEXCOORD_%d" % material["texcoord"]
            tile = (np.asarray(accessor(gltf, blob, attrs[key]), dtype=np.float64)
                    if material["sheet"] is not None and material["texcoord"] and key in attrs
                    else None)
            out.append({
                "node": name,
                "material": material["name"],
                "color": material["color"],
                "sheet": material["sheet"] if tile is not None else None,
                "tile": tile,
                "pos": np.asarray(pos, dtype=np.float64),
                "uv": np.asarray(uv, dtype=np.float64),
                "tris": np.asarray(flat, dtype=np.int64).reshape(-1, 3),
            })
    out.sort(key=lambda p: (p["node"], p["material"]))
    return out


# --- Rasterisation ----------------------------------------------------------


def fill_triangles(rgb: np.ndarray, mask: np.ndarray, uv: np.ndarray,
                   tris: np.ndarray, color: tuple[float, float, float], side: int,
                   sheet: np.ndarray | None = None,
                   tile: np.ndarray | None = None) -> None:
    """Remplit chaque triangle de sa couleur, par barycentriques exactes.

    ⚠️ De VRAIES barycentriques, pas un test de centre de gravité : le harnais hérité
    d'un script précédent rejetait un triangle sur deux et amputait 40 % des pixels
    d'une pièce (`pratique-revue-asset`, 2026-08-25).

    ⚠️ ET SI LA PIÈCE PORTE ENCORE SA FEUILLE, ON LA REPORTE AU LIEU DE LA MOYENNER.
    `sheet` est la carte tuilée, `tile` le jeu d'UV qui l'indexe : les mêmes
    barycentriques qui décident du dedans interpolent l'adresse dans la feuille. Le
    dépliage en atlas cesse ainsi d'être une PERTE — la tôle, le liseré, les rivets et
    la patine déjà mesurés sur cette coque passent dans l'atlas à leur échelle monde,
    au lieu d'être remplacés par un aplat.

    Échantillonnage au PLUS PROCHE et non bilinéaire : exact, donc déterministe
    (`ADR-0047` §3), et sans invention entre deux texels.
    """
    px = uv[:, 0] * side
    py = uv[:, 1] * side  # glTF §3.8.2 : v = 0 est le HAUT de l image (voir l en-tete)
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
        if sheet is None or tile is None:
            window[inside] = color
        else:
            w2 = 1.0 - w0 - w1
            su = w0[inside] * tile[ia, 0] + w1[inside] * tile[ib, 0] + w2[inside] * tile[ic, 0]
            sv = w0[inside] * tile[ia, 1] + w1[inside] * tile[ib, 1] + w2[inside] * tile[ic, 1]
            height, width = sheet.shape[0], sheet.shape[1]
            # La feuille se REPETE : c'est ce qu'elle est, une tuile. Le modulo est donc
            # le comportement juste, pas un garde-fou.
            sx = np.mod((su * width).astype(np.int64), width)
            sy = np.mod((sv * height).astype(np.int64), height)
            window[inside] = sheet[sy, sx]
        mask[y0:y1, x0:x1][inside] = True


def draw_segment(buf: np.ndarray, a: tuple[float, float], b: tuple[float, float],
                 side: int, width: float, value: float) -> None:
    """Trace un segment épais dans un tampon (distance point-segment, anti-aliasé)."""
    ax, ay = a[0] * side, a[1] * side
    bx, by = b[0] * side, b[1] * side
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


def _to_srgb(linear: np.ndarray) -> np.ndarray:
    """Encode du lineaire vers sRGB (courbe standard, pas une gamma 2,2 approchee).

    On travaille en LINEAIRE tant qu'on calcule — remplissage, usure, dilatation — parce
    que multiplier des couleurs n'a de sens que la. L'encodage se fait une seule fois, a
    l'ecriture.
    """
    low = linear * 12.92
    high = 1.055 * np.power(np.clip(linear, 1e-8, None), 1.0 / 2.4) - 0.055
    return np.where(linear <= 0.0031308, low, high)


def bake(glb: Path, side: int, angle_deg: float, line_px: float,
         groove: float, wear: float) -> tuple[Image.Image, Image.Image, dict]:
    gltf, blob = read_glb(glb)
    prims = primitives(gltf, blob)

    rgb = np.zeros((side, side, 3), dtype=np.float64)
    mask = np.zeros((side, side), dtype=bool)
    height = np.ones((side, side), dtype=np.float64)

    for prim in prims:
        fill_triangles(rgb, mask, prim["uv"], prim["tris"], prim["color"][:3], side,
                       sheet=prim.get("sheet"), tile=prim.get("tile"))

    edges = 0
    for prim in prims:
        uv = prim["uv"]
        for u, v in sharp_edges(prim, angle_deg):
            draw_segment(height, uv[u], uv[v], side, line_px, groove)
            edges += 1

    # L'usure suit la rainure : là où la surface casse, la peinture s'use.
    #
    # ⚠️ DISCRÈTE, ET C'EST MESURÉ. À 0,35 la coque ressortait presque noire là où la
    # palette est sombre — parce que la rainure est comptée DEUX FOIS : peinte ici dans
    # l'albédo, puis dérivée en occlusion et en normale par `tools/derive-maps.py`, qui
    # l'assombrit une seconde fois à l'éclairage. Le bleu de charte `#1C2B5E` n'a que
    # **2,8 % de luminance relative** contre 82,4 % pour le blanc cassé : à ce niveau,
    # un facteur 0,8 de plus le fait basculer dans le noir.
    #
    # ⚠️ ET LA PALETTE N'Y EST POUR RIEN — vérifié le 2026-09-05 en mesurant la planche
    # de référence elle-même : son bleu médian (#113051) est à **2,8 %** lui aussi, la
    # même valeur exactement. Ce qui fait lire « bleu » sur la planche et « noir » chez
    # nous, ce n'est pas la teinte, c'est ce qu'on lui ajoute par-dessus.
    #
    # La rainure appartient donc au RELIEF, pas à la peinture.
    worn = 1.0 - (1.0 - height) * wear
    rgb *= worn[..., None]

    dilate(rgb, mask, passes=max(4, int(side / 256)))
    dilate_height(height, mask, passes=max(4, int(side / 256)))

    # ⚠️ LINEAIRE -> sRGB, ET CE N'EST PAS UNE FINITION. Mesure du 2026-09-05 : sans
    # cette conversion, la coque perdait **29 % de luminance** en jeu et le bleu marine
    # de la livree sortait a 1,7/255 — noir. Le `baseColorFactor` d'un glTF est LINEAIRE
    # par specification ; un PNG d'albedo est relu en sRGB par Godot. Ecrire l'un dans
    # l'autre sans encoder, c'est appliquer une gamma 2,2 de trop.
    #
    # La correspondance etait exacte a l'entier sur les sept materiaux, ce qui a permis
    # d'identifier la cause sans tatonner : AA_Hull cuisait a (216, 210, 196) la ou la
    # charte dit (237, 234, 227). C'est la signature d'un espace de couleur, pas d'un
    # reglage.
    albedo = Image.fromarray(np.clip(_to_srgb(rgb) * 255.0 + 0.5, 0, 255).astype(np.uint8))
    relief = Image.fromarray(np.clip(height * 255.0 + 0.5, 0, 255).astype(np.uint8))
    reportee = sum(len(p["tris"]) for p in prims if p.get("tile") is not None)
    stats = {
        "primitives": len(prims),
        "triangles": int(sum(len(p["tris"]) for p in prims)),
        "aretes_creusees": edges,
        "couverture": float(mask.mean()),
        "materiaux": sorted({p["material"] for p in prims}),
        "triangles_feuille_reportee": int(reportee),
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


# --- Planche de reperage ----------------------------------------------------

#: Une couleur par zone. Elles ne sortent PAS de la palette de charte : cette planche
#: n'est pas un asset de jeu, c'est un plan de travail, et ses couleurs doivent se
#: distinguer entre elles avant d'etre jolies. Fixes, donc deterministes.
ZONE_COLORS = (
    (232, 92, 60), (86, 176, 232), (240, 196, 72), (128, 208, 120),
    (200, 116, 224), (240, 140, 176), (120, 132, 240), (96, 216, 200),
    (224, 160, 96), (160, 176, 96), (200, 200, 200),
)


def _font(size: int):
    from PIL import ImageFont

    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def plate(albedo: Image.Image, prims: list[dict], zones: dict, side: int,
          out: Path) -> dict:
    """La planche de reperage : OU L'ON PEINT, et sous quel nom.

    ⚠️ SANS ELLE, UN ATLAS EST INPEIGNABLE PAR UN HUMAIN. 406 pieces packees
    automatiquement produisent un damier d'ilots dont rien ne dit lequel est le nez et
    lequel est la derive babord. La demande de peinture qui suivra (`ADR-0028`) a besoin
    d'un plan, pas d'une image.

    Le decoupage en zones vient du `.blend` lui-meme (ses collections `MODULE | ...`),
    pas d'une heuristique : c'est la seule decoupe que l'auteur ait declaree.
    """
    from PIL import ImageDraw

    modules = sorted({z["module"] for z in zones.values()}) or ["?"]
    index_of = {name: i for i, name in enumerate(modules)}
    zone = np.zeros((side, side), dtype=np.uint8)  # 0 = vide, i+1 = module i
    centroids: dict[str, tuple[float, float, float]] = {}
    labels: list[tuple[float, float, float, str]] = []
    for prim in prims:
        info = zones.get(prim["node"])
        if info is None:
            continue
        fill_zone(zone, prim["uv"], prim["tris"], index_of[info["module"]] + 1, side)
        uv = prim["uv"][prim["tris"]]
        area = float(np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
                            - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])).sum() * 0.5)
        center = prim["uv"].mean(axis=0)
        labels.append((area, float(center[0]), float(center[1]), prim["node"]))
        best = centroids.get(info["module"])
        if best is None or area > best[0]:
            centroids[info["module"]] = (area, float(center[0]), float(center[1]))

    legend_height = 40 + 26 * ((len(modules) + 1) // 2)
    sheet = Image.new("RGB", (side, side + legend_height), (14, 16, 22))
    # ⚠️ LE DOSAGE N'EST PAS UN GOUT. Trop d'albedo et les zones ne se distinguent plus
    # les unes des autres ; trop de teinte et on ne reconnait plus la piece qu'on
    # regarde. La moitie-moitie garde les deux lisibles, et c'est le seul critere.
    base = np.asarray(albedo, dtype=np.float64) * 0.40
    tint = np.zeros_like(base)
    for name, i in index_of.items():
        tint[zone == i + 1] = ZONE_COLORS[i % len(ZONE_COLORS)]
    painted = np.where((zone > 0)[..., None], base * 0.50 + tint * 0.50, base)
    sheet.paste(Image.fromarray(np.clip(painted, 0, 255).astype(np.uint8)), (0, 0))

    draw = ImageDraw.Draw(sheet)
    big = _font(max(16, side // 90))
    small = _font(max(12, side // 130))

    def stamp(x: float, y: float, text: str, font, color) -> None:
        px, py = x * side, y * side
        draw.text((px, py), text, font=font, fill=(0, 0, 0), anchor="mm",
                  stroke_width=3, stroke_fill=(0, 0, 0))
        draw.text((px, py), text, font=font, fill=color, anchor="mm")

    # Les vingt plus grosses pieces se nomment ; en dessous, l'ilot est trop petit pour
    # qu'un nom y tienne, et la couleur de zone suffit.
    for _, x, y, name in sorted(labels, reverse=True)[:20]:
        stamp(x, y, name.split("| ")[-1], small, (245, 245, 245))
    for name, (_, x, y) in sorted(centroids.items()):
        stamp(x, y - 0.012, name.upper(), big,
              ZONE_COLORS[index_of[name] % len(ZONE_COLORS)])

    total = float((zone > 0).sum()) or 1.0
    draw.text((16, side + 10), "SPECTER-9 D — atlas %d x %d, zones du .blend "
              "(part de l'atlas)" % (side, side), font=big, fill=(235, 235, 235))
    for i, name in enumerate(modules):
        column, row = i % 2, i // 2
        x, y = 16 + column * (side // 2), side + 40 + row * 26
        draw.rectangle([x, y + 4, x + 18, y + 20], fill=ZONE_COLORS[i % len(ZONE_COLORS)])
        draw.text((x + 26, y + 3), "%-18s %5.1f %%"
                  % (name, 100.0 * float((zone == i + 1).sum()) / total),
                  font=small, fill=(220, 220, 220))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return {name: 100.0 * float((zone == index_of[name] + 1).sum()) / total
            for name in modules}


def fill_zone(zone: np.ndarray, uv: np.ndarray, tris: np.ndarray, value: int,
              side: int) -> None:
    """Marque chaque triangle d'un indice de zone — meme rasterisation que l'albedo."""
    px = uv[:, 0] * side
    py = uv[:, 1] * side
    for ia, ib, ic in tris:
        ax, ay, bx, by, cx, cy = px[ia], py[ia], px[ib], py[ib], px[ic], py[ic]
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
        zone[y0:y1, x0:x1][inside] = value


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
    parser.add_argument("--wear", type=float, default=0.12,
                        help="part de la rainure reportée sur l'albédo")
    parser.add_argument("--check", action="store_true",
                        help="cuit deux fois et compare — l'invariant d'ADR-0008")
    parser.add_argument("--stem", default=None,
                        help="nom des cartes ; par défaut celui du .glb. Utile quand la "
                             "cuisson lit un intermédiaire de build et non le livrable")
    parser.add_argument("--zones", type=Path, default=None,
                        help="JSON {nœud: {module, family, weight}} — la découpe en zones")
    parser.add_argument("--plate", type=Path, default=None,
                        help="planche de repérage à écrire (demande --zones)")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.stem or args.glb.stem

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
    if stats["triangles_feuille_reportee"]:
        print("  feuille REPORTEE dans l'atlas sur %d triangles sur %d — les autres "
              "prennent la teinte moyenne de leur materiau"
              % (stats["triangles_feuille_reportee"], stats["triangles"]))
    if args.plate is not None:
        if args.zones is None:
            raise SystemExit("--plate sans --zones : la planche n'aurait aucun nom de zone")
        gltf, blob = read_glb(args.glb)
        shares = plate(albedo, primitives(gltf, blob),
                       json.loads(args.zones.read_text()), args.size, args.plate)
        print("  ecrit %s" % args.plate)
        for name, share in sorted(shares.items(), key=lambda kv: -kv[1]):
            print("    zone %-16s %5.1f %% de l'atlas" % (name, share))
    print("  ⚠️ la hauteur n'est PAS une normale : la passer a tools/derive-maps.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
