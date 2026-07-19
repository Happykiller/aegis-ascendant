#!/usr/bin/env python3
"""Reconstruit un canal alpha pour un asset image généré (ChatGPT / DALL·E).

POURQUOI CE SCRIPT — ChatGPT ne produit PAS de vraie transparence : il **peint un
damier** (ou un fond gris uni) dans une image RGB opaque. Un PNG « transparent »
livré par ChatGPT arrive donc en mode RGB, sans alpha. Il faut reconstruire le
canal alpha côté outillage. Ce script encode les deux recettes vérifiées (session
du 2026-07-19, refonte du fond spatial — BRIEF-0028) au lieu de les réécrire à la
main à chaque asset.

DEUX MODES, selon comment l'image a été générée :

  --mode black   Objet LUMINEUX sur FOND NOIR PUR (nébuleuse, galaxie, VFX).
                 alpha = f(luminance) : le noir devient transparent, le gaz opaque.
                 → toujours demander « fond noir pur » à ChatGPT pour ce cas.

  --mode sat     Objet COLORÉ sur damier NEUTRE peint (rattrapage quand on n'a pas
                 pu obtenir un fond noir). alpha = f(saturation) : le gaz coloré
                 reste, le damier gris part. Garde aussi les pixels très clairs
                 (cœur lumineux). Moins propre que --mode black (résidu possible).

  --mode light   Objet OPAQUE sur fond CLAIR uni / damier blanc (planète, vaisseau).
                 Flood-fill depuis les bords : retire le fond neutre connecté au
                 bord, garde l'objet même s'il contient des zones claires. Érode la
                 frange d'antialiasing.

Toujours prévisualiser (--preview) et juger l'œil avant d'intégrer : les seuils
dépendent de l'image. Dépendances : Pillow, numpy, scipy.

Exemples (ceux qui ont produit les textures du fond) :
  bg-key-alpha.py --mode light in/planet.png out/planet_hero.png --erode 2 --preview p.png
  bg-key-alpha.py --mode sat   in/nebula_a.png out/nebula_a.png --preview p.png
  bg-key-alpha.py --mode black in/nebula_b.png out/nebula_b.png --lo 8 --hi 60 --preview p.png
"""
from __future__ import annotations
import argparse
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

# Couleur d'espace de la scène (resources/graphics/space_environment.tres) pour un
# aperçu fidèle : tout résidu visible ici sera visible en jeu.
SPACE_BG = np.array([10, 13, 24], np.float32)


def _feather(alpha_u8: np.ndarray, radius: float) -> np.ndarray:
	if radius <= 0.0:
		return alpha_u8
	return np.asarray(Image.fromarray(alpha_u8).filter(ImageFilter.GaussianBlur(radius)))


def key_black(a: np.ndarray, lo: float, hi: float, gamma: float) -> np.ndarray:
	"""Fond noir pur -> alpha par luminance (max des canaux)."""
	luma = a.max(2)
	alpha = np.clip((luma - lo) / (hi - lo), 0.0, 1.0) ** gamma
	return (alpha * 255.0).astype(np.uint8)


def key_sat(a: np.ndarray, lo: float, hi: float, gamma: float) -> np.ndarray:
	"""Damier neutre peint -> alpha par saturation, cœur clair préservé."""
	mx = a.max(2)
	mn = a.min(2)
	sat = mx - mn
	alpha = np.clip((sat - lo) / (hi - lo), 0.0, 1.0)
	# Garde les pixels très clairs même peu saturés (cœur lumineux d'une nébuleuse).
	alpha = np.maximum(alpha, np.clip((mx - 95.0) / (150.0 - 95.0), 0.0, 1.0))
	return (alpha ** gamma * 255.0).astype(np.uint8)


def key_light(a: np.ndarray, luma_min: float, sat_max: float, erode: int) -> np.ndarray:
	"""Fond clair uni / damier blanc -> flood-fill depuis les bords."""
	luma = a.max(2)
	sat = a.max(2) - a.min(2)
	bg = (luma > luma_min) & (sat < sat_max)
	lbl, _ = ndimage.label(bg)
	border = set(lbl[0, :]).union(lbl[-1, :], lbl[:, 0], lbl[:, -1])
	border.discard(0)
	keep = ~np.isin(lbl, list(border))
	if erode > 0:
		keep = ndimage.binary_erosion(keep, iterations=erode)
	return (keep * 255).astype(np.uint8)


def main(argv: list[str]) -> int:
	p = argparse.ArgumentParser(description=__doc__,
		formatter_class=argparse.RawDescriptionHelpFormatter)
	p.add_argument("src")
	p.add_argument("dst")
	p.add_argument("--mode", choices=["black", "sat", "light"], required=True)
	p.add_argument("--lo", type=float, default=8.0, help="black/sat: seuil bas")
	p.add_argument("--hi", type=float, default=55.0, help="black/sat: seuil haut")
	p.add_argument("--gamma", type=float, default=0.9, help="black/sat: courbe alpha")
	p.add_argument("--luma-min", type=float, default=226.0, help="light: fond > ce seuil")
	p.add_argument("--sat-max", type=float, default=18.0, help="light: fond < cette satur.")
	p.add_argument("--erode", type=int, default=2, help="light: px de frange rognés")
	p.add_argument("--feather", type=float, default=1.0, help="flou du bord alpha (px)")
	p.add_argument("--preview", help="écrit un aperçu composité sur la couleur d'espace")
	args = p.parse_args(argv)

	im = Image.open(args.src).convert("RGB")
	a = np.asarray(im).astype(np.float32)

	if args.mode == "black":
		alpha = key_black(a, args.lo, args.hi, args.gamma)
	elif args.mode == "sat":
		alpha = key_sat(a, args.lo, args.hi, args.gamma)
	else:
		alpha = key_light(a, args.luma_min, args.sat_max, args.erode)

	alpha = _feather(alpha, args.feather)
	Image.merge("RGBA", (*im.split(), Image.fromarray(alpha))).save(args.dst)

	al = alpha / 255.0
	transp = float((alpha < 10).mean())
	opaque = float((alpha > 200).mean())
	print(f"{args.dst}: {im.size} transparent={transp:.2f} opaque={opaque:.2f}")

	if args.preview:
		comp = (a * al[..., None] + SPACE_BG * (1.0 - al[..., None])).astype(np.uint8)
		Image.fromarray(comp).save(args.preview)
		print(f"preview -> {args.preview} (résidu visible ici = résidu en jeu)")
	return 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
