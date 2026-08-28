#!/usr/bin/env python3
"""Greffe une bouche ouverte d'une tête livrée sur une figure d'un seul tenant.

⚠️ POURQUOI CE BRICOLAGE EXISTE. La figure CHR-0004 est livrée d'un tenant, donc sans variante
de bouche — et l'accueil avait une bouche qui bougeait avec l'ancienne tête (CHR-0001). Le
générateur ne sait pas retoucher par masque (trois livraisons régénérées). Mais la bouche ouverte
de l'ancienne tête est du MÊME style et de la MÊME palette : réduite à ~30 px, feutrée, et
recalée en teinte sur la peau du nouveau visage, elle passe à l'échelle d'affichage.

Usage : graft_mouth.py <figure.png> <tete_ouverte.png> <x0,y0,x1,y1 sur la tête> \
          <cx,cy sur la figure> <largeur cible px> <sortie.png>
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

fig_p, src_p, box, centre, width, out = sys.argv[1:8]
x0, y0, x1, y1 = map(int, box.split(','))
cx, cy = map(float, centre.split(','))
width = float(width)

fig = Image.open(fig_p).convert('RGBA')
src = Image.open(src_p).convert('RGBA').crop((x0, y0, x1, y1))
s = width / (x1 - x0)
patch = src.resize((max(1, round(src.width * s)), max(1, round(src.height * s))), Image.LANCZOS)

# Teinte : la peau autour de la bouche, source contre cible, par canal. ⚠️ MÉDIANE DES PIXELS
# OPAQUES d'un anneau autour de la zone — une moyenne à coordonnées fixes tombait sur du
# transparent et rendait un facteur vert de 18,7.
def ring_skin(im, box, pad):
    a = np.asarray(im.convert('RGBA')).astype(float)
    bx0, by0, bx1, by1 = box
    outer = a[max(0, by0 - pad):by1 + pad, max(0, bx0 - pad):bx1 + pad]
    m = np.ones(outer.shape[:2], bool)
    m[pad:pad + (by1 - by0), pad:pad + (bx1 - bx0)] = False
    px = outer[m & (outer[..., 3] > 200)][:, :3]
    return np.median(px, axis=0)
src_skin = ring_skin(Image.open(src_p), (x0, y0, x1, y1), 12)
half_w, half_h = patch.width / 2, patch.height / 2
dst_box = (round(cx - half_w), round(cy - half_h), round(cx + half_w), round(cy + half_h))
dst_skin = ring_skin(fig, dst_box, 4)
ratio = dst_skin / np.maximum(src_skin, 1.0)
p = np.asarray(patch).astype(float)
p[..., :3] = np.clip(p[..., :3] * ratio, 0, 255)
patch = Image.fromarray(p.astype(np.uint8))

# Masque : ellipse feutrée, pour que le bord de la greffe ne se lise pas.
mask = Image.new('L', patch.size, 0)
from PIL import ImageDraw
ImageDraw.Draw(mask).ellipse((2, 2, patch.width - 3, patch.height - 3), fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(max(1.0, patch.width * 0.08)))
alpha = np.asarray(patch)[..., 3].astype(float) / 255.0 * np.asarray(mask).astype(float)
patch.putalpha(Image.fromarray(alpha.astype(np.uint8)))

pos = (round(cx - patch.width / 2), round(cy - patch.height / 2))
fig.alpha_composite(patch, pos)
fig.save(out)
print('greffe', patch.size, 'posee en', pos, 'teinte x', np.round(ratio, 3))
