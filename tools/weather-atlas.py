#!/usr/bin/env python3
"""weather-atlas.py — poser l'usure SUR un atlas cuit, la ou la coque se salit vraiment.

    python3 tools/weather-atlas.py assets/imported/textures/hull/specter_9_d
        [--grime 0.26] [--edge 0.30] [--mottle 0.06] [--preview /tmp/p.png]

Lit `<stem>_albedo.png`, `<stem>_ao.png` et `<stem>_height.png` ; ecrit
`<stem>_albedo_worn.png`. C'est CETTE image que le jeu porte ; l'atlas brut reste a cote,
intact, pour qu'une recuisson ne detruise rien.


POURQUOI CET OUTIL — ET POURQUOI IL NE POUVAIT PAS EXISTER AVANT
================================================================
Une feuille de detail REPETABLE ne peut pas salir un endroit choisi : tout ce qu'on y met
revient partout. C'est la limite qui separait la `specter_9_d` de la `specter_9_b`, et
l'operateur l'a dite sans jargon : « on a un bel objet 3D mais qui manque de texture, de
couleur, de patine ».

Un atlas leve cette limite : chaque texel a une ADRESSE sur la coque. Cet outil s'en sert.


CE QU'IL FAIT, ET SUR QUELLE MESURE
===================================
Il ne peint pas au hasard : il lit la GEOMETRIE, deja cuite dans deux cartes.

  * LA CRASSE SUIT L'OCCLUSION. `<stem>_ao.png` dit ou la lumiere n'entre pas — creux de
    joint, dessous de nacelle, angle rentrant. C'est exactement la ou la salissure
    s'accumule sur une vraie coque. Mesure sur la Specter-9 D : 17,8 % des texels couverts
    sont sous 200 d'occlusion, donc concernes.
  * L'USURE SUIT LES ARETES. Le gradient de `<stem>_height.png` est fort la ou la tole
    casse. Une peinture s'y ecaille en premier et laisse voir le metal : on tire donc vers
    le gris, on eclaircit legerement, on rend plus rugueux.
  * ET LA PEINTURE SALE SE DESATURE, elle ne fait pas que foncer. Sans ce melange vers le
    gris, un rouge sali reste un rouge sombre — ce qui se lit comme une OMBRE et non comme
    de l'usure. C'est la meme lecon que sur la feuille tuilee, et elle vaut deux fois plus
    ici, ou les zones sales sont grandes.


⚠️ IL NE MORD PAS SUR TOUTES LES COQUES — MESURE, PUIS ECARTE SUR LA SPECTER-9 D
================================================================================
Essaye le 2026-09-06 sur cette coque, et REFUSE sur mesure. Les deux masques n'y sont que
des CONTOURS DE PIECES : 43 % des texels couverts marques « arete », et l'image de controle
ne montre que la decoupe des 406 morceaux.

La cause est structurelle et vaut d'etre connue avant de relancer l'outil ailleurs : la
cuisson d'atlas derive son relief des ARETES DU MAILLAGE. Sur une coque dont le detail vit
dans des PIECES SEPAREES — 406 objets ici — les seules aretes sont les silhouettes de ces
pieces. Il n'y a aucun creux DANS une surface a trouver, donc rien a salir qui ne soit un
liseré autour de chaque morceau. Peindre l'usure la-dessus dessine un surpiquage brillant
sur tout le vaisseau.

Chiffres du refus, apres avoir coupe l'ecaillage et ne garder que la crasse :
**variance locale 7,13 -> 7,06, soit -1,0 %**. L'outil ne depose rien de visible ; il ne
fait que desaturer (23,8 -> 20,1). On ne cable pas un rendu que la mesure dit nul.

Il reste juste pour une coque dont les panneaux sont ENFONCES DANS la surface — celles du
kit, ou `ak.inset_panel()` creuse vraiment. Et il redeviendra utile ici le jour ou la
cuisson saura sortir une carte de POSITION MONDE par texel : c'est elle qui manque pour
qu'une trainee coule vers le bas.


⚠️ CE QU'IL NE FAIT PAS, ET IL FAUT LE SAVOIR
=============================================
PAS DE COULURES DIRECTIONNELLES. Une trainee sous une tuyere descend dans le repere du
MONDE ; l'atlas, lui, est en espace UV, ou « le bas » ne veut rien dire. Les faire
demanderait une carte de position monde par texel, que `bake-atlas.py` ne cuit pas encore.
Une trainee tiree dans l'axe des UV tomberait dans une direction arbitraire, differente sur
chaque ilot — pire que pas de trainee.

⚠️ ET IL NE DEBORDE PAS D'UN ILOT SUR L'AUTRE. Les texels de FOND (6,5 % de l'atlas) sont
exclus de tout adoucissement : un flou qui les traverserait tirerait la couleur d'une aile
sur une nacelle, et le defaut ne se verrait qu'en jeu, sur une couture.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def dilater(champ: np.ndarray, plein: np.ndarray, passes: int = 24) -> np.ndarray:
    """Etale les texels COUVERTS dans les marges, par vagues successives.

    ⚠️ SANS ELLE, TOUTE CARTE DERIVEE D'UN ATLAS EST FAUSSE SUR SES BORDS. Un atlas laisse du
    vide entre les ilots ; la hauteur y tombe a zero, donc son GRADIENT y explose. Une normale
    ou une occlusion derivee sans dilatation dessine un liseré autour de CHAQUE ilot — mesure
    le 2026-09-06 sur la Specter-9 D : 43 % des texels couverts etaient marques « arete »,
    et le masque n'etait qu'un contour de decoupe.

    C'est un defaut a la fois grave et invisible : sur le modele, ces liseres apparaissent
    comme des surpiqures brillantes le long de chaque couture, et on ne les voit qu'en jeu,
    sous un angle rasant.

    Le remede est celui de tous les pipelines d'atlas : on recopie la valeur du voisin couvert
    le plus proche dans la marge, assez loin pour que le filtrage de texture et les mipmaps
    n'aillent jamais chercher du vide.
    """
    sortie = champ.astype(np.float32).copy()
    connu = plein.copy()
    for _ in range(passes):
        if connu.all():
            break
        somme = np.zeros_like(sortie)
        compte = np.zeros(sortie.shape[:2], dtype=np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            voisin = np.roll(np.roll(sortie, dy, axis=0), dx, axis=1)
            masque = np.roll(np.roll(connu, dy, axis=0), dx, axis=1)
            if sortie.ndim == 3:
                somme += voisin * masque[..., None]
            else:
                somme += voisin * masque
            compte += masque
        neuf_ = (~connu) & (compte > 0)
        if sortie.ndim == 3:
            sortie[neuf_] = somme[neuf_] / compte[neuf_][..., None]
        else:
            sortie[neuf_] = somme[neuf_] / compte[neuf_]
        connu = connu | neuf_
    return sortie


def _flou(champ: np.ndarray, masque: np.ndarray, rayon: int) -> np.ndarray:
    """Moyenne locale qui IGNORE le fond, par sommes cumulees.

    ⚠️ Le masque est floute lui aussi et sert de diviseur : sans ca un texel au bord d'un
    ilot verrait sa moyenne tiree vers zero par le fond, et l'usure ferait un lisere sombre
    sur chaque couture — exactement l'artefact qu'un atlas est cense eviter.
    """
    def somme(a: np.ndarray) -> np.ndarray:
        c = np.cumsum(np.cumsum(np.pad(a, ((1, 0), (1, 0))), axis=0), axis=1)
        h, w = a.shape
        y0 = np.clip(np.arange(h) - rayon, 0, h)
        y1 = np.clip(np.arange(h) + rayon + 1, 0, h)
        x0 = np.clip(np.arange(w) - rayon, 0, w)
        x1 = np.clip(np.arange(w) + rayon + 1, 0, w)
        return (c[np.ix_(y1, x1)] - c[np.ix_(y0, x1)]
                - c[np.ix_(y1, x0)] + c[np.ix_(y0, x0)])
    poids = somme(masque.astype(np.float32))
    return somme(champ * masque) / np.maximum(poids, 1e-6)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stem", help="prefixe des cartes, sans _albedo.png")
    ap.add_argument("--grime", type=float, default=0.26, help="force de la crasse (0-1)")
    ap.add_argument("--edge", type=float, default=0.30, help="force de l'ecaillage d'arete")
    ap.add_argument("--mottle", type=float, default=0.06, help="marbrure de la peinture")
    ap.add_argument("--seed", type=int, default=90601)
    ap.add_argument("--preview", help="PNG de controle : masques cote a cote")
    args = ap.parse_args()

    stem = Path(args.stem)
    albedo = np.asarray(Image.open(f"{stem}_albedo.png").convert("RGB")).astype(np.float32)
    plein = albedo.sum(2) >= 12.0          # les texels reellement occupes

    # ⚠️ ON DEMANDE AU MAILLAGE, PAS A L'IMAGE. Les champs cuits par
    # `bake-surface-fields.py` disent, pour chaque texel, OU IL REGARDE et S'IL EST EN
    # SAILLIE. Deduire ces deux choses du relief cuit ne mesurait que la decoupe des
    # pieces — refuse sur mesure le 2026-09-06, 43 % de la coque marquee « arete ».
    champs = Path(f"{stem}_curv.png")
    if not champs.exists():
        raise SystemExit(
            f"{champs} manquant — lance d'abord :\n"
            f"  python3 tools/bake-surface-fields.py <coque>.glb --out {stem.parent} "
            f"--name {stem.name}")
    wnrm = np.asarray(Image.open(f"{stem}_wnrm.png").convert("RGB")).astype(np.float32) / 255.0
    curv = np.asarray(Image.open(f"{stem}_curv.png").convert("L")).astype(np.float32) / 255.0
    cover = np.asarray(Image.open(f"{stem}_cover.png").convert("L")) > 127
    wnrm = dilater(wnrm, cover)
    curv = dilater(curv, cover)

    # --- LA POUSSIERE SE DEPOSE SUR CE QUI REGARDE VERS LE HAUT -------------------
    # C'est le repere le plus fort d'une coque sale, et le seul qui ne demande que la
    # normale. Le seuil est doux : une surface a 45 deg en prend deja la moitie.
    haut = np.clip((wnrm[..., 1] - 0.5) * 2.6, 0.0, 1.0)

    # --- LA CRASSE S'ACCUMULE DANS LE CONCAVE, LA PEINTURE S'ECAILLE SUR LE CONVEXE --
    rentrant = np.clip((0.5 - curv) * 5.0, 0.0, 1.0)
    saillant = np.clip((curv - 0.5) * 5.0, 0.0, 1.0)

    # --- ET RIEN DE TOUT CA N'EST UNIFORME -------------------------------------
    # ⚠️ UNE PEINTURE NE S'ECAILLE PAS PARTOUT PAREIL. Sans cette modulation, l'ecaillage
    # souligne CHAQUE arete du vaisseau au meme degre : on lit un surpiquage, pas une
    # usure. Deux echelles de bruit, l'une large (des zones plus abimees que d'autres),
    # l'autre fine (le grain de l'ecaillage).
    rng = np.random.default_rng(args.seed)
    def bruit(cellules: int) -> np.ndarray:
        petit = rng.random((cellules, cellules)).astype(np.float32)
        return np.asarray(Image.fromarray((petit * 255).astype(np.uint8))
                          .resize(albedo.shape[:2][::-1], Image.BICUBIC)).astype(np.float32) / 255.0
    zones = bruit(12)
    grain = bruit(96)
    marbre = zones

    crasse = np.clip((0.62 * haut + 0.85 * rentrant) * (0.45 + 0.85 * zones), 0.0, 1.0)
    crasse = np.clip(_flou(crasse, plein, 2) * 1.1, 0.0, 1.0)
    arete = np.clip(saillant * (0.25 + 1.15 * zones) * (0.55 + 0.75 * grain), 0.0, 1.0)

    gris = albedo.mean(axis=2, keepdims=True)
    sorti = albedo.copy()

    # La crasse assombrit ET desature — sinon elle se lit comme une ombre.
    f = (1.0 - args.grime * crasse)[..., None]
    sorti = sorti * (1.0 - 0.42 * crasse[..., None]) + gris * (0.42 * crasse[..., None])
    sorti *= f

    # L'ecaillage montre le metal : gris clair, legerement bleute.
    metal = np.array([164.0, 168.0, 174.0], dtype=np.float32)
    m = (args.edge * arete)[..., None]
    sorti = sorti * (1.0 - m) + metal * m

    sorti *= (1.0 - args.mottle * 0.5 + args.mottle * marbre)[..., None]

    # ⚠️ LE FOND RESTE LE FOND. Le peindre ferait deborder de la couleur sur les coutures
    # au premier filtrage de texture, et ca ne se verrait qu'en jeu.
    sorti = np.where(plein[..., None], sorti, albedo)
    sorti = np.clip(sorti, 0, 255).astype(np.uint8)
    Image.fromarray(sorti, "RGB").save(f"{stem}_albedo_worn.png")

    couvert = plein.mean()
    print(f"[weather-atlas] {stem.name}")
    print(f"  couverture         {couvert * 100:5.1f} % de l'atlas")
    print(f"  crasse > 0,25      {((crasse > 0.25) & plein).sum() / max(1, plein.sum()) * 100:5.1f} % des texels couverts")
    print(f"  ecaillage > 0,25   {((arete > 0.25) & plein).sum() / max(1, plein.sum()) * 100:5.1f} %")
    avant = albedo[plein].std()
    apres = sorti.astype(np.float32)[plein].std()
    print(f"  ecart-type         {avant:5.1f} -> {apres:5.1f}  ({(apres / avant - 1) * 100:+.1f} %)")
    print(f"  ecrit  {stem}_albedo_worn.png")

    if args.preview:
        bande = np.concatenate([
            (crasse * 255).astype(np.uint8), (arete * 255).astype(np.uint8)], axis=1)
        Image.fromarray(bande, "L").save(args.preview)
        print(f"  controle  {args.preview}  (crasse | ecaillage)")
    print("  ⚠ un asset non regarde n'est pas valide (ADR-0006) : ouvre la carte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
