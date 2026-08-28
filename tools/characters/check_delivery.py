#!/usr/bin/env python3
"""Contrôle une livraison de calques de personnage AVANT de l'intégrer.

    python3 tools/characters/check_delivery.py <dossier> [--base tete]

⚠️ IL EXISTE PARCE QUE J'AI FAIT CE CONTRÔLE À LA MAIN DEUX FOIS, sur deux livraisons, et
que les deux ont échoué sur un point différent. Chaque fois, la vérification a pris vingt
minutes de mesures ; chaque fois, le défaut était invisible à l'œil sur les planches livrées
et évident une fois en jeu.

Ce qu'il vérifie, et pourquoi :

1. **MÊME TOILE.** Des tailles différentes rendent l'empilement impossible sans recaler
   chaque pièce à la main.

2. **LES VARIANTES D'EXPRESSION SONT DES SUBSTITUTIONS.** `tete_bouche_ouverte` doit être
   `tete` avec une bouche différente — RIEN d'autre. Livraison du 2026-08-28 (buste) : les
   quatre têtes étaient **redessinées**, pas modifiées. Le visage entier différait, et un
   recalage n'y changeait rien (erreur 29,0 → 27,4 au mieux, au lieu de tomber à zéro).
   Les substituer aurait fait sauter toute la tête à chaque syllabe.
   ⚠️ C'est LE contrôle qui compte : il ne se voit pas sur une planche-contact.

3. **FOND UNIFORME.** Un fond qui dérive laisse un voile après détourage — invisible sur le
   magenta d'origine, bien présent en jeu (62 % de la surface d'un calque, le 2026-08-28).

Ce qu'il NE vérifie PAS : la co-registration ENTRE groupes. Elle n'est plus exigée — un
générateur d'images ne sait pas la produire, et c'est le jeu qui place les groupes
(`ADR-0035`, `resources/data/character_rig.gd`).
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import numpy as np
from PIL import Image

# Part maximale de pixels qui ont le droit de changer entre une base et sa variante.
# Une bouche, c'est ~3 % d'une tête ; des yeux, moins. Au-delà de 12 %, le visage est
# redessiné — mesuré : les variantes fautives du 2026-08-28 étaient à 38 %.
PART_MAX = 0.12
# Au-delà de cet écart-type sur le pourtour, le fond n'est pas uniforme.
FOND_ECART_MAX = 6.0


def dire(ok: bool, message: str) -> bool:
    print("  %s %s" % ("OK  " if ok else "ÉCHEC", message))
    return ok


def _plat(im: Image.Image) -> Image.Image:
    """Ramène une image au même espace de comparaison, détourée ou non.

    ⚠️ UNE BASE DÉJÀ INTÉGRÉE PORTE UN ALPHA ; une livraison brute porte un fond magenta. Les
    comparer telles quelles compte comme « différent » chaque pixel de fond. On aplatit donc
    tout sur du noir : ce qui est transparent et ce qui est fond deviennent la même chose.
    """
    if im.mode == "RGBA":
        fond = Image.new("RGBA", im.size, (0, 0, 0, 255))
        fond.alpha_composite(im)
        return fond.convert("RGB")
    return im.convert("RGB")


def bord(a: np.ndarray, marge: int = 6) -> np.ndarray:
    return np.concatenate([a[:marge].reshape(-1, 3), a[-marge:].reshape(-1, 3),
                           a[:, :marge].reshape(-1, 3), a[:, -marge:].reshape(-1, 3)])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dossier", help="dossier des PNG livrés")
    ap.add_argument("--base", default="tete",
                    help="le calque dont les variantes d'expression dérivent")
    ap.add_argument("--base-file", default=None,
                    help="chemin du calque de base quand il a été livré AVANT ce lot "
                         "(cas normal : les variantes arrivent après)")
    ap.add_argument("--names", default=None,
                    help="renommage `fichier=calque,...` quand le générateur ne nomme pas")
    args = ap.parse_args()

    fichiers = sorted(Path(args.dossier).glob("*.png"))
    if not fichiers:
        sys.exit("[calques] aucun PNG dans %s" % args.dossier)
    renommage = {}
    if args.names:
        for paire in args.names.split(","):
            src, _, dst = paire.partition("=")
            renommage[src.strip()] = dst.strip()
    images = {renommage.get(f.stem, f.stem): _plat(Image.open(f)) for f in fichiers}
    # ⚠️ LA BASE ARRIVE SOUVENT DANS UN LOT PRÉCÉDENT, et c'est le cas normal : on livre la
    # tête, puis ses expressions. Sans cette option, le contrôle le plus important — « la
    # variante SUBSTITUE » — ne pouvait tout simplement pas s'exécuter.
    if args.base_file:
        images[args.base] = _plat(Image.open(args.base_file))
        print("[calques] base lue hors du lot : %s" % args.base_file)
    print("[calques] %d fichiers dans %s" % (len(images), args.dossier))
    bon = True

    print("\n1. même toile")
    tailles = {n: im.size for n, im in images.items()}
    unique = set(tailles.values())
    if len(unique) == 1:
        bon &= dire(True, "une seule taille : %dx%d" % list(unique)[0])
    else:
        bon &= dire(False, "%d tailles differentes : %s" % (len(unique), sorted(unique)))

    print("\n2. les variantes d'expression sont des substitutions")
    if args.base not in images:
        dire(False, "le calque de base `%s` est absent : rien à comparer" % args.base)
        bon = False
    else:
        base = np.asarray(images[args.base]).astype(int)
        variantes = [n for n in images if n.startswith(args.base + "_")]
        if not variantes:
            print("       (aucune variante livrée)")
        for n in sorted(variantes):
            v = np.asarray(images[n]).astype(int)
            if v.shape != base.shape:
                bon &= dire(False, "%s : taille différente de la base" % n)
                continue
            d = np.abs(v - base).sum(axis=2)
            part = float((d > 60).mean())
            bon &= dire(part <= PART_MAX,
                        "%-24s %5.1f %% de pixels changés (max %.0f %%)%s"
                        % (n, 100 * part, 100 * PART_MAX,
                           "" if part <= PART_MAX else "  <- le visage est REDESSINÉ, pas modifié"))

    print("\n3. fond uniforme")
    for n in sorted(images):
        b = bord(np.asarray(images[n]).astype(float))
        median = np.median(b, axis=0)
        # ⚠️ ON NE MESURE QUE LES PIXELS DE FOND. Sur un cadrage serré, le sujet TOUCHE le
        # bord — les cheveux de Lyra le font sur les quatre côtés. Prendre l'écart-type de
        # tout le pourtour mesurait alors la chevelure et criait au fond non uniforme sur une
        # livraison parfaitement correcte. On garde ce qui est proche de la médiane, et on
        # dit aussi QUELLE PART du pourtour est du fond : c'est elle qui dit si `--key auto`
        # a de quoi travailler.
        proche = b[np.linalg.norm(b - median, axis=1) < 60.0]
        part = len(proche) / max(len(b), 1)
        ecart = float(proche.std(axis=0).max()) if len(proche) else 999.0
        med = tuple(int(v) for v in median)
        ok = ecart <= FOND_ECART_MAX and part > 0.25
        bon &= dire(ok, "%-24s #%02x%02x%02x, écart %.1f sur %.0f %% du pourtour"
                    % ((n,) + med + (ecart, 100 * part)))

    print("\n[calques] %s" % ("livraison conforme" if bon
                              else "livraison NON conforme — voir les échecs ci-dessus"))
    return 0 if bon else 1


if __name__ == "__main__":
    sys.exit(main())
