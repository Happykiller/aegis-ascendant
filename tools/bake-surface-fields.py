#!/usr/bin/env python3
"""bake-surface-fields.py — cuire, en espace atlas, ce que la coque SAIT d'elle-meme.

    python3 tools/bake-surface-fields.py assets/imported/models/ships/specter_9_d.glb \\
        --out assets/imported/textures/hull --name specter_9_d [--side 2048]

Ecrit trois cartes, toutes en espace atlas :

    <nom>_wnrm.png   la NORMALE MONDE     (ou chaque point regarde)
    <nom>_wpos.png   la POSITION MONDE    (ou il est, normalisee dans la boite)
    <nom>_curv.png   la COURBURE          (128 = plat, plus = saillant, moins = rentrant)


POURQUOI CET OUTIL EXISTE — ET LE DEFAUT QU'IL REPARE
=====================================================
`weather-atlas.py` a d'abord tente de deduire les aretes du RELIEF CUIT. Refuse sur mesure
le 2026-09-06 : 43 % des texels marques, et l'image de controle ne montrait que la decoupe
des 406 pieces. La cause est que la cuisson d'atlas derive son relief des aretes du
maillage ; sur une coque faite de pieces separees, ces aretes sont les silhouettes des
pieces, et deriver une pente d'une image discontinue mesure la DECOUPE, pas la coque.

Il fallait donc demander au MAILLAGE, pas a l'image. C'est ce que fait ce fichier.

⚠️ ET LA COURBURE, ELLE, EST LEGITIME MEME SUR LES BORDS DE PIECE. Chaque piece est un
solide ferme : l'arete de son blindage est une VRAIE arete convexe, et c'est exactement la
qu'une peinture s'ecaille. Ce qui etait faux, c'etait le signal — pas l'intention.


CE QUE CHAQUE CARTE PERMET
==========================
  * `wnrm` — la poussiere se depose sur ce qui regarde vers le HAUT. C'est le repere le plus
    fort d'une coque sale, et il ne demande rien d'autre que la normale.
  * `curv` — la peinture s'ecaille sur le CONVEXE (bords de tole, nez, bords d'attaque) et
    la crasse s'accumule dans le CONCAVE (angles rentrants, jonctions).
  * `wpos` — de quoi faire couler une trainee vers le bas. Non exploitee aujourd'hui : elle
    demande un balayage par ilot, et un `weather-atlas` qui la lit sans le faire tirerait
    des trainees dans des directions arbitraires. Cuite quand meme, parce que la recuire
    coute une passe complete.

⚠️ LES TROIS SONT DES DONNEES, PAS DES IMAGES. Elles s'importent en `Non-Color` et ne se
regardent pas comme un rendu : une normale monde est un barbouillage vert-rose, et c'est
normal.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

_spec = importlib.util.spec_from_file_location(
    "bake_atlas", Path(__file__).resolve().parent / "bake-atlas.py")
_ba = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ba)


def node_matrices(gltf: dict) -> dict[str, np.ndarray]:
    """La transformation MONDE de chaque nœud portant un maillage.

    ⚠️ `bake-atlas.py` lit les POSITION brutes, sans transformation — c'est sans consequence
    pour une couleur, et faux pour une position ou une normale. Une nacelle posee a x = −1,3
    a les memes coordonnees locales que sa jumelle a +1,3 : sans la chaine des parents, les
    deux tomberaient au meme endroit du monde et la poussiere se deposerait de travers.
    """
    nodes = gltf.get("nodes", [])
    parent: dict[int, int] = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i

    def local(n: dict) -> np.ndarray:
        m = np.eye(4)
        if "matrix" in n:
            return np.asarray(n["matrix"], dtype=np.float64).reshape(4, 4).T
        if "rotation" in n:
            x, y, z, w = n["rotation"]
            m[:3, :3] = np.array([
                [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        if "scale" in n:
            m[:3, :3] = m[:3, :3] @ np.diag(n["scale"])
        if "translation" in n:
            m[:3, 3] = n["translation"]
        return m

    out: dict[str, np.ndarray] = {}
    for i, n in enumerate(nodes):
        if "mesh" not in n:
            continue
        m = np.eye(4)
        chain: list[int] = []
        j: int | None = i
        while j is not None:
            chain.append(j)
            j = parent.get(j)
        for k in reversed(chain):
            m = m @ local(nodes[k])
        out[n.get("name", "?")] = m
    return out


def curvature(pos: np.ndarray, nrm: np.ndarray, tris: np.ndarray) -> np.ndarray:
    """La courbure par sommet — positive en saillie, negative en creux.

    Pour chaque arete, on compare la difference des NORMALES a la direction de l'arete :
    si les normales s'ecartent dans le sens de l'arete, la surface est convexe. C'est la
    mesure discrete usuelle, et elle ne demande que ce qu'un `.glb` porte deja.

    ⚠️ NORMALISEE PAR LA LONGUEUR D'ARETE. Sans ca, une piece finement maillee rendrait des
    valeurs dix fois plus grandes qu'une piece grossiere, et l'ecaillage se concentrerait
    sur les pieces les mieux definies plutot que sur les vraies aretes.
    """
    somme = np.zeros(len(pos), dtype=np.float64)
    compte = np.zeros(len(pos), dtype=np.float64)
    for a, b in ((0, 1), (1, 2), (2, 0)):
        i, j = tris[:, a], tris[:, b]
        d = pos[j] - pos[i]
        longueur = np.linalg.norm(d, axis=1)
        bon = longueur > 1e-9
        dn = nrm[j] - nrm[i]
        k = np.zeros(len(i))
        k[bon] = np.einsum("ij,ij->i", dn[bon], d[bon]) / (longueur[bon] ** 2)
        for cible, valeur in ((i, k), (j, k)):
            np.add.at(somme, cible, valeur)
            np.add.at(compte, cible, 1.0)
    return somme / np.maximum(compte, 1.0)


def fill_field(buf: np.ndarray, mask: np.ndarray, uv: np.ndarray, tris: np.ndarray,
               field: np.ndarray, side: int) -> None:
    """Comme `fill_triangles`, mais interpole un ATTRIBUT au lieu de poser une couleur."""
    px = uv[:, 0] * side
    py = uv[:, 1] * side
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
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
        if not inside.any():
            continue
        window = buf[y0:y1, x0:x1]
        window[inside] = (w0[inside, None] * field[ia]
                          + w1[inside, None] * field[ib]
                          + w2[inside, None] * field[ic])
        mask[y0:y1, x0:x1][inside] = True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("glb", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--side", type=int, default=2048)
    args = ap.parse_args()

    gltf, blob = _ba.read_glb(args.glb)
    prims = _ba.primitives(gltf, blob)
    world = node_matrices(gltf)
    side = args.side

    wnrm = np.zeros((side, side, 3), dtype=np.float64)
    wpos = np.zeros((side, side, 3), dtype=np.float64)
    curv = np.zeros((side, side, 3), dtype=np.float64)
    mask = np.zeros((side, side), dtype=bool)

    lo = np.array([1e18] * 3)
    hi = np.array([-1e18] * 3)
    prepares = []
    for prim in prims:
        node = gltf["nodes"]
        m = world.get(prim["node"], np.eye(4))
        pos = prim["pos"]
        wp = (m[:3, :3] @ pos.T).T + m[:3, 3]
        # La normale se transforme par la transposee de l'inverse ; ici les
        # transformations sont des rotations-translations, donc la rotation suffit.
        attrs = None
        for n in node:
            if n.get("name") == prim["node"] and "mesh" in n:
                attrs = gltf["meshes"][n["mesh"]]["primitives"][0]["attributes"]
                break
        if attrs is None or "NORMAL" not in attrs:
            continue
        nl = np.asarray(_ba.accessor(gltf, blob, attrs["NORMAL"]), dtype=np.float64)
        if len(nl) != len(pos):
            continue
        wn = (m[:3, :3] @ nl.T).T
        wn /= np.maximum(np.linalg.norm(wn, axis=1, keepdims=True), 1e-9)
        k = curvature(wp, wn, prim["tris"])
        lo = np.minimum(lo, wp.min(axis=0))
        hi = np.maximum(hi, wp.max(axis=0))
        prepares.append((prim, wp, wn, k))

    etendue = np.maximum(hi - lo, 1e-6)
    for prim, wp, wn, k in prepares:
        uv = prim["uv"]
        tris = prim["tris"]
        fill_field(wnrm, mask, uv, tris, wn * 0.5 + 0.5, side)
        fill_field(wpos, mask, uv, tris, (wp - lo) / etendue, side)
        # ⚠️ L'ECHELLE DE LA COURBURE EST ARBITRAIRE ET DOIT L'ETRE : elle depend de la
        # finesse du maillage. On la comprime en tangente hyperbolique, ce qui borne les
        # aretes vives sans ecraser les courbures douces.
        c = np.tanh(k * 3.0) * 0.5 + 0.5
        fill_field(curv, mask, uv, tris, np.repeat(c[:, None], 3, axis=1), side)

    for buf, nom in ((wnrm, "wnrm"), (wpos, "wpos"), (curv, "curv")):
        img = np.clip(buf * 255.0, 0, 255).astype(np.uint8)
        Image.fromarray(img).save(args.out / f"{args.name}_{nom}.png")
    Image.fromarray((mask * 255).astype(np.uint8)).save(args.out / f"{args.name}_cover.png")

    couvert = mask.mean()
    haut = (wnrm[..., 1] > 0.72) & mask
    saillant = (curv[..., 0] > 0.62) & mask
    rentrant = (curv[..., 0] < 0.38) & mask
    print(f"[bake-surface-fields] {args.glb.name}  ({len(prepares)} primitives)")
    print(f"  couverture     {couvert * 100:5.1f} %")
    print(f"  vers le haut   {haut.sum() / max(1, mask.sum()) * 100:5.1f} % des texels couverts")
    print(f"  saillant       {saillant.sum() / max(1, mask.sum()) * 100:5.1f} %")
    print(f"  rentrant       {rentrant.sum() / max(1, mask.sum()) * 100:5.1f} %")
    print(f"  boite monde    {np.round(lo, 3)} -> {np.round(hi, 3)}")
    print(f"  ecrit          {args.out}/{args.name}_{{wnrm,wpos,curv,cover}}.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
