#!/usr/bin/env python3
"""Rasterise un SVG et l'écrit en PNG, pour qu'on le REGARDE avant de l'intégrer.

    python3 tools/preview-svg.py assets/source/ui/hud/fighter_hud_frame.svg
    python3 tools/preview-svg.py assets/source/vfx/projectiles/*.svg   # planche contact

Ce script existe à cause d'un ADR. Le 12/07/2026, six couches de parallaxe livrées
par la forge ont été intégrées sans avoir jamais été rendues : conformes au brief,
provenancées, aux bons chemins — et visuellement inutilisables (des aplats
vectoriels qui, à l'écran, donnaient un tapis de losanges blancs, pire que le vide
qu'ils remplaçaient). Voir docs/decisions/ADR-0006.

La règle qui en découle : **un livrable de la forge n'est pas un asset validé tant
qu'il n'a pas été rendu et regardé.** Le SVG écrit à la main convient aux formes
fonctionnelles (icônes, cadres d'UI, bonus) ; il ne convient pas au pictural.

Plusieurs fichiers -> une planche contact unique, sur le fond spatial du jeu, ce
qui est le seul contexte où juger : un asset clair sur fond blanc ment.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cairosvg
from PIL import Image

## Le fond spatial du jeu (#070A12) : juger un asset sur du blanc n'a aucun sens.
BACKDROP = (7, 10, 18, 255)
TILE = 320
OUT = Path("/tmp/svg-preview.png")


def render(path: Path, size: int) -> Image.Image:
    png = Path("/tmp/_svg_tile.png")
    cairosvg.svg2png(url=str(path), write_to=str(png), output_width=size, output_height=size)
    tile = Image.new("RGBA", (size, size), BACKDROP)
    return Image.alpha_composite(tile, Image.open(png).convert("RGBA"))


def main() -> None:
    paths = [Path(a) for a in sys.argv[1:]]
    if not paths:
        raise SystemExit(__doc__)
    missing = [p for p in paths if not p.is_file()]
    if missing:
        raise SystemExit("introuvable : %s" % ", ".join(str(p) for p in missing))

    if len(paths) == 1:
        render(paths[0], 768).convert("RGB").save(OUT)
    else:
        columns = min(len(paths), 5)
        rows = (len(paths) + columns - 1) // columns
        sheet = Image.new("RGBA", (TILE * columns, TILE * rows), BACKDROP)
        for i, path in enumerate(paths):
            sheet.paste(render(path, TILE), ((i % columns) * TILE, (i // columns) * TILE))
        sheet.convert("RGB").save(OUT)

    for path in paths:
        print("  %s" % path)
    print("\n-> %s   (l'OUVRIR : un asset non regardé n'est pas un asset validé)" % OUT)


if __name__ == "__main__":
    main()
