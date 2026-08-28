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

# ⚠️ `scipy` n'est PAS importé ici, et ce n'est pas un oubli : il n'est pas installé sur
# ce poste (cf. l'en-tête de `derive-maps.py`, écrit exprès sans lui). Seul `key_light()`
# en a besoin — pour ses composantes connexes — et il l'importe lui-même.
#
# L'import était au niveau module, si bien que le script entier refusait de démarrer, y
# compris pour `--mode black` qui ne fait qu'un seuil de luminance en numpy. Un mode
# parfaitement fonctionnel était donc inaccessible à cause d'une dépendance d'un autre
# mode. Ne pas remonter cet import.

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
	"""Fond clair uni / damier blanc -> flood-fill depuis les bords.

	Seul mode à dépendre de `scipy` : l'import est local pour que son absence ne
	condamne pas `black` et `sat`, qui tiennent en numpy (voir en-tête du module).
	"""
	from scipy import ndimage  # noqa: PLC0415 — local, et volontairement

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


def _key_du_bord(a: np.ndarray, marge: int = 6) -> tuple[int, int, int]:
	"""La couleur du fond, MESURÉE sur le pourtour au lieu d'être supposée.

	⚠️ UN GÉNÉRATEUR NE REND PAS LA COULEUR QU'ON LUI DEMANDE. Livraison du 2026-08-28 : neuf
	calques sur un magenta ≈ #FF00FF, et le dixième sur **(239, 6, 237)**. Seize points d'écart
	suffisent — avec une clé supposée pure, ce calque gardait un voile à 2 % d'opacité sur
	**62 % de sa surface**, invisible à l'œil sur le fond d'origine et bien présent en jeu.
	"""
	bord = np.concatenate([
		a[:marge].reshape(-1, 3), a[-marge:].reshape(-1, 3),
		a[:, :marge].reshape(-1, 3), a[:, -marge:].reshape(-1, 3)])
	return tuple(int(v) for v in np.median(bord, axis=0))


def key_chroma(a: np.ndarray, key: tuple[int, int, int], tol: float,
		soft: float) -> tuple[np.ndarray, np.ndarray]:
	"""Fond d'une COULEUR CONNUE (magenta, vert). Rend l'alpha ET l'image dé-diffusée.

	⚠️ C'EST LE CAS LE PLUS PROPRE, ET IL MANQUAIT. Les trois autres modes devinent le fond
	à partir de la luminance ou de la saturation : ils se trompent dès que le sujet est
	sombre (`black`) ou clair (`light`). Quand on a pu IMPOSER la couleur du fond à la
	génération — ce que fait `docs/forge/characters/` en demandant du magenta — il n'y a
	plus rien à deviner : on connaît la couleur, on la retire.

	⚠️ ET ON DÉ-DIFFUSE. Un détourage sans despill laisse une frange magenta dans les
	cheveux et sur les bords clairs : invisible sur le fond magenta d'origine, criante sur
	le fond sombre du jeu. C'est le défaut qu'on ne voit qu'une fois intégré.
	"""
	# ⚠️ UNE DISTANCE RVB N'EST PAS UN ALPHA, et c'est le premier piège. Un pixel moitié
	# cheveux moitié magenta est à mi-distance des deux — mais la distance rendue est
	# NON LINÉAIRE en α dès que la tolérance entre en jeu, et l'alpha sort trop opaque : le
	# dé-prémultiplié corrige alors trop peu, et la frange survit. Mesuré : **59 % des pixels
	# de bord encore magenta** avec cette recette-là.
	#
	# La bonne mesure est le DÉBORDEMENT du canal : le magenta est fort en rouge et en bleu,
	# faible en vert. `min(R,B) − V` vaut +255 sur la clé pure, et devient négatif sur un
	# sujet chaud ou neutre. Comme le mélange est linéaire, cette quantité l'est aussi — donc
	# elle donne un α juste.
	kr, kg, kb = key
	if kg < min(kr, kb):                       # magenta, cyan… : le vert est minoritaire
		spill = np.minimum(a[:, :, 0], a[:, :, 2]) - a[:, :, 1]
		s_key = float(min(kr, kb) - kg)
	else:                                      # vert
		spill = a[:, :, 1] - np.maximum(a[:, :, 0], a[:, :, 2])
		s_key = float(kg - max(kr, kb))
	# `tol` : zone morte au ras de la clé. `soft` : marge SOUS zéro avant que l'alpha ne
	# plafonne — et elle doit rester PETITE.
	# ⚠️ ELLE VALAIT 45, ET LA COMBINAISON ÉTAIT TRANSPARENTE. Un pixel sans débordement
	# (bleu nuit, blanc, gris : `spill` ≈ 0) tombait à α = 0,88, et le dé-prémultiplié, en
	# retirant 12 % de magenta qui n'y était pas, virait le bleu nuit au sarcelle (45,61,99 ->
	# 19,68,81). Mesuré sur `figure.png` le 2026-08-28 : 246 948 pixels du sujet entre 192 et
	# 239 d'alpha, 61 381 seulement à 255 — et l'anneau de la planète visible à travers ses
	# jambes. Le mélange est linéaire : un sujet NEUTRE est à α = 1 dès que spill ≤ 0.
	alpha = np.clip(((s_key - tol) - spill) / max(s_key - tol + soft, 1e-3), 0.0, 1.0)
	# ⚠️ DÉ-PRÉMULTIPLIÉ, PAS UN RABOTAGE DE CANAL. Un pixel de bord vaut
	# `c = α·f + (1−α)·k` : le fond y est MÉLANGÉ, pas superposé. Retrancher « l'excès de
	# rouge et de bleu » laisse un cast violet — mesuré le 2026-08-28 sur les cheveux de
	# Lyra : **65 % des pixels de bord restaient magenta**, invisibles sur le fond magenta
	# d'origine et criants sur le fond sombre du jeu. On inverse le mélange : `f = (c −
	# (1−α)·k) / α`. C'est exact, et ça ne laisse rien.
	k = np.array(key, dtype=np.float32)
	al = alpha[..., None]
	sur = np.maximum(al, 1e-3)
	rgb = (a - (1.0 - al) * k) / sur
	# Là où il ne reste presque rien d'objet, l'inversion amplifie le bruit : on retombe sur
	# la couleur d'origine plutôt que d'inventer.
	rgb = np.where(al < 0.06, a, rgb)
	return (alpha * 255.0).astype(np.uint8), np.clip(rgb, 0, 255).astype(np.uint8)


def main(argv: list[str]) -> int:
	p = argparse.ArgumentParser(description=__doc__,
		formatter_class=argparse.RawDescriptionHelpFormatter)
	p.add_argument("src")
	p.add_argument("dst")
	p.add_argument("--mode", choices=["black", "sat", "light", "chroma"], required=True)
	p.add_argument("--lo", type=float, default=8.0, help="black/sat: seuil bas")
	p.add_argument("--hi", type=float, default=55.0, help="black/sat: seuil haut")
	p.add_argument("--gamma", type=float, default=0.9, help="black/sat: courbe alpha")
	p.add_argument("--luma-min", type=float, default=226.0, help="light: fond > ce seuil")
	p.add_argument("--sat-max", type=float, default=18.0, help="light: fond < cette satur.")
	p.add_argument("--erode", type=int, default=2, help="light: px de frange rognés")
	p.add_argument("--key", default="auto",
		help="chroma: couleur du fond en hexa, ou `auto` pour la MESURER au pourtour")
	p.add_argument("--tol", type=float, default=18.0,
		help="chroma: zone morte au ras de la clé")
	p.add_argument("--soft", type=float, default=0.0,
		help="chroma: marge sous zéro avant le plafond d'alpha (0 : un sujet neutre est opaque)")
	p.add_argument("--feather", type=float, default=1.0, help="flou du bord alpha (px)")
	p.add_argument("--preview", help="écrit un aperçu composité sur la couleur d'espace")
	args = p.parse_args(argv)

	im = Image.open(args.src).convert("RGB")
	a = np.asarray(im).astype(np.float32)

	rgb_out = im
	if args.mode == "black":
		alpha = key_black(a, args.lo, args.hi, args.gamma)
	elif args.mode == "sat":
		alpha = key_sat(a, args.lo, args.hi, args.gamma)
	elif args.mode == "chroma":
		if args.key == "auto":
			key = _key_du_bord(a)
			print("cle mesuree au bord : #%02x%02x%02x" % key)
		else:
			key = tuple(int(args.key.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
		alpha, rgb = key_chroma(a, key, args.tol, args.soft)
		rgb_out = Image.fromarray(rgb)
		a = rgb.astype(np.float32)
	else:
		alpha = key_light(a, args.luma_min, args.sat_max, args.erode)

	alpha = _feather(alpha, args.feather)
	Image.merge("RGBA", (*rgb_out.split(), Image.fromarray(alpha))).save(args.dst)

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
