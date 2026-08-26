#!/usr/bin/env python3
"""Découpe une capture de jeu À L'ÉCHELLE 1:1, pour la juger sans la trahir.

⚠️ POURQUOI CET OUTIL EXISTE — 2026-08-26. Un effet de traînée a été déclaré bon sur
des captures que j'avais moi-même **réduites en 960 px** avant de les regarder. En
pleine résolution, l'opérateur y a vu un carton découpé : arêtes polygonales, aplat
opaque, capuchon hexagonal, halo brun de bloom. La réduction efface EXACTEMENT ce
qu'on cherche — un contour dur, une facette, une couture, une saturation.

`ADR-0006` dit « rendu et regardé ». Regarder une réduction n'est pas regarder le
rendu : c'est regarder un flou qui pardonne. Cet outil ne sait pas redimensionner.

Usage :
    python3 tools/inspect-capture.py <capture.png> [--at X,Y] [--size 700x500]
                                     [--out /tmp/crop.png] [--zoom N]

Sans `--at`, il vise le centre de masse des pixels les plus lumineux — donc l'effet.
`--zoom` agrandit au PLUS PROCHE VOISIN (jamais d'interpolation) : on regarde les
vrais pixels, grossis, pas des pixels inventés.
"""
import argparse
import sys

try:
    import numpy as np
    from PIL import Image
except ImportError:  # pragma: no cover
    print("il faut Pillow et numpy", file=sys.stderr)
    raise SystemExit(2)


def brightest_spot(a: np.ndarray) -> tuple[int, int]:
    """Centre de masse des pixels du centile le plus lumineux."""
    lum = a.mean(axis=2)
    seuil = float(np.percentile(lum, 99.7))
    ys, xs = np.nonzero(lum >= seuil)
    if xs.size == 0:
        h, w = lum.shape
        return w // 2, h // 2
    return int(xs.mean()), int(ys.mean())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capture")
    ap.add_argument("--at", help="X,Y du centre ; défaut : la zone la plus lumineuse")
    ap.add_argument("--size", default="700x500", help="LxH du cadre, en pixels RÉELS")
    ap.add_argument("--zoom", type=int, default=1, help="agrandissement au plus proche voisin")
    ap.add_argument("--out", default="/tmp/capture-1a1.png")
    args = ap.parse_args()

    im = Image.open(args.capture).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    w, h = im.size

    if args.at:
        cx, cy = (int(v) for v in args.at.split(","))
        origine = "demandé"
    else:
        cx, cy = brightest_spot(a)
        origine = "zone la plus lumineuse"

    cw, ch = (int(v) for v in args.size.lower().split("x"))
    x0 = max(0, min(w - cw, cx - cw // 2))
    y0 = max(0, min(h - ch, cy - ch // 2))
    crop = im.crop((x0, y0, x0 + cw, y0 + ch))
    if args.zoom > 1:
        crop = crop.resize((cw * args.zoom, ch * args.zoom), Image.NEAREST)
    crop.save(args.out)

    lum = a.mean(axis=2)
    print(f"[inspect] {args.capture}  {w}x{h}")
    print(f"  centre  ({cx}, {cy})  — {origine}")
    print(f"  cadre   {cw}x{ch} px RÉELS à partir de ({x0}, {y0})"
          + (f", agrandi x{args.zoom} au plus proche voisin" if args.zoom > 1 else ""))
    print(f"  écrêtage : {100.0 * float((lum >= 254.0).mean()):.2f} % des pixels à 254+"
          " (au-delà, le bloom a saturé — un contour y devient un aplat)")
    print(f"  écrit   {args.out}")
    print("  ⚠️ regarder CETTE image, pas une réduction : la réduction efface le défaut.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
