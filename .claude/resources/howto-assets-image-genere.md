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

## ⚠️ Un brief de forge doit DIRE que la texture viendra d'ailleurs

Relevé par l'opérateur le 2026-08-25, sur le chantier du survol de lune : `BRIEF-0085` demandait
tout le relief **en géométrie** et ne mentionnait nulle part la texture qu'il allait générer. Le
circuit existe pourtant depuis longtemps — c'est ce fichier — mais il n'était écrit que du côté
*intégration*, jamais du côté *commande*.

Ce chantier a **trois mains**, et un brief qui n'en nomme que deux fait travailler la forge dans le
vide :

| Qui | Quoi |
|---|---|
| L'opérateur | **génère les textures** et les dépose dans `assets/source/` |
| La forge | la **géométrie** et surtout des **UV faites pour recevoir la carte** |
| Le concepteur | détoure, dérive, câble le matériau, mesure, intègre |

Deux conséquences à écrire dans tout brief concerné :

- **`ak.box_project_uv()` ne suffit plus.** Il convient à une coque vue de loin sans carte de détail ;
  il donne des îlots arbitraires, coutures et échelles inégales. Une carte plaquée dessus s'étire
  visiblement — et **personne ne le voit avant le rendu final**. Exiger un dépliage continu, la
  **densité de texels mesurée**, les coutures **hors champ**, et une **planche de damier UV** rendue
  à la perspective du jeu.
- **Dire où passe la frontière géométrie / texture, et pourquoi.** Une carte ne remplace pas un
  relief là où il compte : la silhouette du limbe et tout ce qui doit porter une **ombre réelle**
  restent géométriques. Le reste — grain, petits accidents — va à la texture.

## Intégration (rappels qui évitent une reprise)

- Les PNG passent en **Git LFS** (`.gitattributes`) ; committer aussi le `.import` et les `.uid`.
- `assets/source/` est `.gdignore`é (sources non importées) ; la texture in-game va dans
  `assets/imported/backgrounds/`. Une ligne de provenance par fichier dans
  `assets/licenses/ASSET_PROVENANCE.csv` (`*_src` = source, `*_tex` = texture détourée,
  `modified_by` = la recette de reconstruction).
- Objet devant apparaître **rond sous la caméra inclinée** (plan de jeu XZ, caméra Y=14) → le poser
  en **Sprite3D `billboard`**, pas en plan texturé (qui serait écrasé par la perspective).
- Le post-process rétro pixelise **tout** l'écran (~960×540) : inutile de viser un asset 4K fin.

## Une texture posée sur un maillage bâti par code : trois pièges muets, dans cet ordre

Vécu le 2026-08-27 sur le blindage rotatif du réacteur (`TEX-0009`, `scripts/bosses/core_interior.gd`).
Les trois produisent **le même symptôme** — la texture rend du **grain** au lieu de la matière — et
aucun ne lève d'erreur. D'où l'ordre : le diagnostic par l'échelle est celui qui vient à l'esprit en
premier, et c'est le seul des trois qui ne soit **pas** un bug.

| Piège | Ce qu'on voit | Le témoin qui tranche |
|---|---|---|
| **1. Pas de mipmaps** | Grain scintillant, dense, sur toute la surface | `mipmaps/generate=false` est le **défaut d'import de Godot** pour une image. Un maillage 3D vu de loin l'aliase brutalement — ici 1254 px de texture sur 30 px d'écran, soit 40:1. `detect_3d/compress_to=1` était censé le rattraper : il ne se déclenche que si la texture passe dans le viewport 3D de l'ÉDITEUR, donc **jamais** en export sans tête |
| **2. Pas de tangentes** | Éclairage incohérent, sommet par sommet | Une carte de normale se lit dans le repère tangent. `ArrayMesh` bâti à la main sans `ARRAY_TANGENT` : Godot ne dit rien. Remède : `SurfaceTool.create_from(mesh, 0)` + `generate_tangents()` + `commit()` — les normales et les UV suffisent |
| **3. Échelle trop fine** | Motif présent mais illisible, lavé par les mips | Se calcule : `px_écran/m` × la taille du motif. Sous ~10 px, le motif n'existe pas. **Ne se corrige qu'après les deux autres** — sinon on recale une échelle qui n'était pas en cause (fait, sans effet) |

⚠️ **Le piège du diagnostic** : les trois se ressemblent, mais seuls 1 et 2 sont des défauts. Recaler
l'échelle en premier donne une amélioration *partielle* qui ressemble à un progrès et masque les
deux autres. Régler **1, puis 2, puis 3** — et ne juger l'échelle que sur une capture propre.

Un dernier chiffre utile, à calculer avant de demander l'image : le rapport de sous-échantillonnage.
Caméra à 14,9 m, fov 62°, post-process rétro à 960×540 → **~30 px/m**. Une bande de mur d'1 m fait
30 px : tout motif sous 3 cm y est invisible, et une tuile calée sur 2 m y est du bruit. C'est ce
calcul, pas le goût, qui a fait passer `TILE_M` de 2 à 8.
