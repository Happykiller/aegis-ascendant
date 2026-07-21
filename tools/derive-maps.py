#!/usr/bin/env python3
"""Dérive normale / rugosité / AO depuis une carte de HAUTEUR en niveaux de gris.

    python3 tools/derive-maps.py assets/source/textures/citadel/citadel_panels_height_2048.png \
        --out assets/imported/textures/citadel --name citadel_panels --preview /tmp/p.png

POURQUOI CE SCRIPT — un générateur d'images ne produit **pas** de vraie normal map.
Il peint une image violette *qui y ressemble* : les gradients n'encodent aucune
pente réelle, donc l'éclairage est faux et le relief part dans le mauvais sens
selon la zone. Le défaut est vicieux parce que l'image « a l'air correcte ».

La seule chose qu'un générateur fait bien, c'est une **hauteur en niveaux de gris** :
clair = saillant, sombre = creux. Tout le reste se calcule. C'est ce que fait ce
script (ADR-0013).

Pendant de `bg-key-alpha.py`, qui encode l'autre piège de génération (la fausse
transparence peinte en damier).

SORTIES (suffixes fixes, attendus par le code Godot) :
    <name>_nrm.png    normale tangent-space (OpenGL, +Y vers le haut)
    <name>_rough.png  rugosité — le creux est plus rugueux que la plaque
    <name>_ao.png     occlusion approchée — assombrit les creux
    <name>_mul.png    carte de multiplication d'albedo (option --mul)

⚠️ LE TUILAGE — un « seamless » demandé n'est pas un seamless obtenu. `--check-tiling`
colle l'image à elle-même et mesure la discontinuité au raccord. Le vérifier AVANT
d'intégrer : une couture se voit en jeu comme une grille régulière sur la coque, et
on l'attribue alors au modèle plutôt qu'à la texture.

Dépendances : Pillow, numpy. (Pas scipy : il n'est pas installé sur ce poste, et
tout ce qu'il faut ici tient en convolutions séparables de rayon 1.)
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image


# --------------------------------------------------------------------------
# Lecture
# --------------------------------------------------------------------------


def load_height(path: str) -> np.ndarray:
    """Charge une image en hauteur normalisée [0,1], float32.

    Convertie en luminance : une hauteur *doit* être grise, mais un générateur
    rend souvent un gris très légèrement teinté. On ne s'en formalise pas, on
    projette — en signalant si la dérive de teinte est forte, parce que c'est le
    symptôme d'une image qui n'est pas la carte demandée.
    """
    img = Image.open(path)
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    chroma = float(rgb.max(axis=2).mean() - rgb.min(axis=2).mean())
    if chroma > 0.08:
        print(
            f"  ⚠ image nettement colorée (chroma moyenne {chroma:.3f}) — "
            "est-ce bien une carte de HAUTEUR en niveaux de gris ?"
        )
    return rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def _autolevel(h: np.ndarray, low: float = 1.0, high: float = 99.0) -> np.ndarray:
    """Étale la hauteur sur [0,1] par percentiles.

    Un générateur rend rarement une plage complète : une hauteur qui vit entre
    0,38 et 0,61 produit, sans ce recadrage, une normale plate et un relief nul —
    et on conclurait à tort que la dérivation ne marche pas.
    """
    lo, hi = np.percentile(h, [low, high])
    if hi - lo < 1e-4:
        return np.zeros_like(h)
    return np.clip((h - lo) / (hi - lo), 0.0, 1.0)


# --------------------------------------------------------------------------
# Convolutions (toriques : le voisin du bord droit est le bord gauche)
# --------------------------------------------------------------------------


def _sobel(h: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Gradients Sobel, en enroulement torique.

    `np.roll` et non un padding par réplication : la feuille est faite pour être
    RÉPÉTÉE. Un gradient calculé sur un bord répliqué crée une pente artificielle
    au raccord, donc une arête lumineuse tous les N mètres sur la coque — une
    couture qu'on ne verrait qu'en jeu, une fois la texture posée.
    """
    def sh(dy: int, dx: int) -> np.ndarray:
        return np.roll(np.roll(h, dy, axis=0), dx, axis=1)

    gx = (
        (sh(-1, -1) + 2.0 * sh(0, -1) + sh(1, -1))
        - (sh(-1, 1) + 2.0 * sh(0, 1) + sh(1, 1))
    )
    gy = (
        (sh(-1, -1) + 2.0 * sh(-1, 0) + sh(-1, 1))
        - (sh(1, -1) + 2.0 * sh(1, 0) + sh(1, 1))
    )
    return gx / 8.0, gy / 8.0


def _blur(h: np.ndarray, radius: int) -> np.ndarray:
    """Flou boîte séparable torique, `radius` px. Sert à l'AO (occlusion large)."""
    if radius < 1:
        return h
    k = 2 * radius + 1
    out = h
    for axis in (0, 1):
        acc = np.zeros_like(out)
        for d in range(-radius, radius + 1):
            acc += np.roll(out, d, axis=axis)
        out = acc / k
    return out


# --------------------------------------------------------------------------
# Dérivations
# --------------------------------------------------------------------------


def to_normal(h: np.ndarray, strength: float) -> np.ndarray:
    """Normale tangent-space, convention **OpenGL** (+Y vers le haut).

    Godot attend cette convention : une normale DirectX (Y inversé) donne un
    relief qui s'éclaire à l'envers — creux et bosses permutés. Le défaut est
    difficile à voir sur une plaque isolée et évident sur une coque entière.
    """
    gx, gy = _sobel(h)
    nx = -gx * strength
    ny = gy * strength          # +Y haut : gy est déjà orienté ligne 0 = haut
    nz = np.ones_like(h)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    rgb = np.stack([nx / norm, ny / norm, nz / norm], axis=2)
    return ((rgb * 0.5 + 0.5) * 255.0).astype(np.uint8)


def to_rough(h: np.ndarray, base: float, span: float) -> np.ndarray:
    """Rugosité : le creux est plus rugueux que la plaque.

    Une plaque entretenue est satinée, un joint encrassé ne l'est pas. C'est ce
    contraste qui fait lire le détail sous une lumière rasante — plus, souvent,
    que la normale elle-même.
    """
    r = np.clip(base + (1.0 - h) * span, 0.0, 1.0)
    return (r * 255.0).astype(np.uint8)


def to_ao(h: np.ndarray, radius: int, strength: float) -> np.ndarray:
    """Occlusion approchée : écart entre la hauteur et sa moyenne locale.

    Ce n'est pas une AO calculée par lancer de rayons — c'est une cavité
    relative. Suffisant pour une feuille de détail répétable, et gratuit.
    """
    ao = 1.0 - np.clip((_blur(h, radius) - h) * strength, 0.0, 1.0)
    return (np.clip(ao, 0.0, 1.0) * 255.0).astype(np.uint8)


def to_mul(h: np.ndarray, floor: float) -> np.ndarray:
    """Carte de multiplication d'albedo : plaques à ~1.0, creux < 1.0.

    Même contrat que `hull_detail_mul.png` (ADR-0011) : multipliée sur la couleur
    de palette, elle creuse les rainures **sans introduire aucune teinte**.
    """
    m = floor + (1.0 - floor) * h
    return (np.clip(m, 0.0, 1.0) * 255.0).astype(np.uint8)


# --------------------------------------------------------------------------
# Tuilage
# --------------------------------------------------------------------------


def tiling_error(h: np.ndarray) -> tuple[float, float]:
    """Discontinuité aux deux raccords, en % de la dynamique de l'image.

    On compare la colonne 0 à la colonne -1 (et la ligne 0 à la ligne -1) : c'est
    exactement ce que verra le shader au moment de répéter la feuille.
    """
    dyn = float(h.max() - h.min()) or 1.0
    ex = float(np.abs(h[:, 0] - h[:, -1]).mean()) / dyn * 100.0
    ey = float(np.abs(h[0, :] - h[-1, :]).mean()) / dyn * 100.0
    return ex, ey


def fix_tiling(h: np.ndarray, band: int) -> np.ndarray:
    """Force le raccord par fondu miroir sur `band` px — RATTRAPAGE, pas méthode.

    Le fondu duplique visiblement le motif sur la bande : il sauve une image
    presque bonne, il ne sauve pas une image qui n'a jamais été pensée seamless.
    Regarder le résultat avant de s'en contenter.
    """
    out = h.copy()
    ramp = np.linspace(0.0, 1.0, band, dtype=np.float32)
    for _ in range(2):  # une passe par axe, via transposition
        left = out[:, :band]
        right = out[:, -band:]
        out[:, :band] = left * ramp + right[:, ::-1] * (1.0 - ramp)
        out = out.T
    return out


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _save(arr: np.ndarray, path: str, mode: str) -> None:
    Image.fromarray(arr, mode).save(path)
    print(f"  écrit  {path}  ({arr.shape[1]}x{arr.shape[0]}, {mode})")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Dérive normale/rugosité/AO depuis une hauteur N&B (ADR-0013).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("height", help="PNG de hauteur en niveaux de gris")
    ap.add_argument("--out", required=True, help="répertoire de sortie")
    ap.add_argument("--name", help="préfixe des sorties (défaut : déduit du fichier)")
    ap.add_argument("--strength", type=float, default=6.0, help="force du relief (défaut 6)")
    ap.add_argument("--rough-base", type=float, default=0.30)
    ap.add_argument("--rough-span", type=float, default=0.45)
    ap.add_argument("--ao-radius", type=int, default=12)
    ap.add_argument("--ao-strength", type=float, default=2.5)
    ap.add_argument("--mul", action="store_true", help="produire aussi la carte de multiplication")
    ap.add_argument("--mul-floor", type=float, default=0.55, help="noirceur max des creux")
    ap.add_argument(
        "--mask",
        action="store_true",
        help="l'entrée est un MASQUE (usure, marquages), pas une hauteur : "
        "on ne dérive ni normale ni AO, on sort seulement <name>_mask.png recadré",
    )
    ap.add_argument("--no-autolevel", action="store_true")
    ap.add_argument("--check-tiling", action="store_true", help="mesurer la couture et s'arrêter")
    ap.add_argument("--fix-tiling", type=int, metavar="PX", help="fondu miroir de PX px (rattrapage)")
    ap.add_argument("--preview", metavar="PNG", help="planche contact 2x2 tuiles + cartes")
    args = ap.parse_args()

    if not os.path.exists(args.height):
        print(f"introuvable : {args.height}", file=sys.stderr)
        return 2

    # On retire le suffixe de RÔLE du nom source : les sorties portent le leur
    # (`_nrm`, `_rough`, `_mask`…), et sans ça un `citadel_wear_mask.png` produit un
    # `citadel_wear_mask_mask.png`. `_mask` doit passer AVANT `_height` : une source
    # peut porter les deux mots, jamais le même deux fois.
    name = args.name or os.path.basename(args.height).rsplit(".", 1)[0]
    for suffix in ("_height_2048", "_mask_2048", "_2048", "_height", "_mask"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break

    print(f"[derive-maps] {args.height}")
    h = load_height(args.height)
    if h.shape[0] != h.shape[1]:
        print(f"  ⚠ image non carrée ({h.shape[1]}x{h.shape[0]}) — le tuilage sera anisotrope")

    ex, ey = tiling_error(h)
    verdict = "OK" if max(ex, ey) < 4.0 else "COUTURE VISIBLE"
    print(f"  tuilage : écart bord X {ex:.1f} %, bord Y {ey:.1f} %  -> {verdict}")
    if args.check_tiling:
        return 0 if max(ex, ey) < 4.0 else 1

    if args.fix_tiling:
        h = fix_tiling(h, args.fix_tiling)
        ex, ey = tiling_error(h)
        print(f"  après fondu miroir : X {ex:.1f} %, Y {ey:.1f} % — REGARDER le résultat")

    if not args.no_autolevel:
        before = float(h.max() - h.min())
        h = _autolevel(h)
        print(f"  autolevel : dynamique {before:.2f} -> 1.00")

    os.makedirs(args.out, exist_ok=True)

    # Un masque n'encode pas un relief : dériver une normale d'une tache de
    # salissure creuserait la coque là où elle est seulement sale.
    if args.mask:
        _save((h * 255.0).astype(np.uint8), os.path.join(args.out, f"{name}_mask.png"), "L")
        if args.preview:
            _preview_mask(h, args.preview)
        print("  ⚠ un asset non regardé n'est pas validé (ADR-0006) : ouvre la preview.")
        return 0

    nrm = to_normal(h, args.strength)
    rough = to_rough(h, args.rough_base, args.rough_span)
    ao = to_ao(h, args.ao_radius, args.ao_strength)
    _save(nrm, os.path.join(args.out, f"{name}_nrm.png"), "RGB")
    _save(rough, os.path.join(args.out, f"{name}_rough.png"), "L")
    _save(ao, os.path.join(args.out, f"{name}_ao.png"), "L")
    if args.mul:
        _save(to_mul(h, args.mul_floor), os.path.join(args.out, f"{name}_mul.png"), "L")

    if args.preview:
        _preview(h, nrm, rough, ao, args.preview)

    print("  ⚠ un asset non regardé n'est pas validé (ADR-0006) : ouvre la preview.")
    return 0


def _preview_mask(h, path: str) -> None:
    """Masque en 2x2 tuiles : la seule chose à juger ici est la couture."""
    size = 768
    tiled = np.tile((h * 255.0).astype(np.uint8), (2, 2))
    Image.fromarray(tiled, "L").resize((size, size), Image.LANCZOS).save(path)
    print(f"  preview {path}  (2x2 tuiles)")


def _preview(h, nrm, rough, ao, path: str) -> None:
    """Planche contact : la hauteur en 2x2 TUILES (pour voir la couture), puis les cartes."""
    hh = (h * 255.0).astype(np.uint8)
    tiled = np.tile(hh, (2, 2))
    size = 512
    cells = [
        Image.fromarray(tiled, "L").convert("RGB").resize((size, size), Image.LANCZOS),
        Image.fromarray(nrm, "RGB").resize((size, size), Image.LANCZOS),
        Image.fromarray(rough, "L").convert("RGB").resize((size, size), Image.LANCZOS),
        Image.fromarray(ao, "L").convert("RGB").resize((size, size), Image.LANCZOS),
    ]
    sheet = Image.new("RGB", (size * 2, size * 2), (10, 13, 24))
    for i, cell in enumerate(cells):
        sheet.paste(cell, ((i % 2) * size, (i // 2) * size))
    sheet.save(path)
    print(f"  preview {path}  (haut-gauche = 2x2 tuiles : c'est là qu'une couture se voit)")


if __name__ == "__main__":
    raise SystemExit(main())
