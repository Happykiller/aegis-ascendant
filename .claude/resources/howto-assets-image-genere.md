# Howto — intégrer un asset image généré par ChatGPT (le piège de la fausse transparence)

L'opérateur génère les images hors dépôt (ChatGPT / DALL·E) et les dépose dans `assets/source/` ;
la session principale détoure et intègre. **Le piège qui coûte un aller-retour** : quand on demande
un « fond transparent », **ChatGPT ne produit pas de vraie transparence — il peint le damier**
(ou un fond gris uni) dans une image **RGB opaque, sans canal alpha**. Vécu le 2026-07-19 (refonte
du fond spatial, BRIEF-0028) : trois PNG « transparents » livrés étaient en fait RGB ; le damier
gris repassait en fantôme dès qu'on tirait un alpha par luminance, et deux images ont dû être
**régénérées sur fond noir** — un tour complet perdu.

## Les deux réflexes

1. **Vérifier le mode avant tout** : `python3 -c "from PIL import Image; print(Image.open('x.png').mode)"`.
   `RGB` = pas d'alpha (damier peint). `RGBA` avec coins à alpha 0 = vraie transparence.

2. **Demander le bon fond selon la nature de l'objet** (ChatGPT ne sait pas faire de vrai alpha) :
   - Objet **lumineux** (nébuleuse, galaxie, VFX, explosion) → exiger un **FOND NOIR PUR**
     (`solid black #000000, NOT transparent, NOT a checkerboard`). Le noir se reconstruit en alpha
     par luminance, sans résidu.
   - Objet **opaque** (planète, vaisseau) → un **fond clair uni** (blanc), détouré par flood-fill.
   - **Jamais** compter sur « transparent background » seul : on récupère un damier.

## Reconstruire l'alpha — encodé, pas à refaire à la main

`tools/bg-key-alpha.py` encode les trois recettes vérifiées (Pillow + numpy + scipy). Toujours
`--preview` et **juger l'œil** (les seuils dépendent de l'image ; le preview est composité sur la
couleur d'espace, donc tout résidu visible dans le preview sera visible en jeu) :

```bash
# nébuleuse/galaxie sur fond noir pur -> alpha par luminance
python3 tools/bg-key-alpha.py --mode black src.png assets/imported/backgrounds/out.png --lo 8 --hi 60 --preview p.png
# planète/objet opaque sur fond clair -> flood-fill depuis les bords + érosion de frange
python3 tools/bg-key-alpha.py --mode light src.png assets/imported/backgrounds/out.png --erode 2 --preview p.png
# rattrapage : gaz coloré sur damier neutre -> clé par saturation (moins propre)
python3 tools/bg-key-alpha.py --mode sat  src.png assets/imported/backgrounds/out.png --lo 14 --hi 40 --preview p.png
```

## Intégration (rappels qui évitent une reprise)

- Les PNG passent en **Git LFS** (`.gitattributes`) ; committer aussi le `.import` et les `.uid`.
- `assets/source/` est `.gdignore`é (sources non importées) ; la texture in-game va dans
  `assets/imported/backgrounds/`. Une ligne de provenance par fichier dans
  `assets/licenses/ASSET_PROVENANCE.csv` (`*_src` = source, `*_tex` = texture détourée,
  `modified_by` = la recette de reconstruction).
- Objet devant apparaître **rond sous la caméra inclinée** (plan de jeu XZ, caméra Y=14) → le poser
  en **Sprite3D `billboard`**, pas en plan texturé (qui serait écrasé par la perspective).
- Le post-process rétro pixelise **tout** l'écran (~960×540) : inutile de viser un asset 4K fin.
