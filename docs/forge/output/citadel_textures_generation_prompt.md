# Prompts de génération — textures de l'Aegis Citadel

- **Brief** : `docs/forge/briefs/BRIEF-0032-aegis-citadel-reforge.md`
- **Produit par** : skill `/asset-image`
- **Cadre** : ADR-0013 (textures déverrouillées)
- **Outil prévu** : ChatGPT imagegen — **cinq images, cinq prompts indépendants**
- **Statut** : **livré et intégré** le 2026-07-21 (panneaux, greebles, cristal appliqués ;
  usure et marquages en attente — voir `assets/source/README.md`)

> ⚠️ Les cinq images ont été rendues en **1254 × 1254**, pas en 2048 : le générateur n'honore pas la
> taille demandée. Les fichiers ont donc été renommés sans le suffixe `_2048`, qui mentait. Trois des
> cinq avaient une **couture** malgré la consigne (jusqu'à 12,3 % sur le cristal), rattrapée par
> `--fix-tiling 90` — la preuve qu'il faut **mesurer** le tuilage et non le croire sur parole.

---

## Avant de commencer — deux choses à savoir

**Tu ne génères que des niveaux de gris.** La normale, la rugosité et l'occlusion sont **calculées**
par `tools/derive-maps.py`. Ne les demande jamais à ChatGPT : il peint une image violette *qui
ressemble* à une normal map, dont les pentes sont fausses — le relief s'éclaire alors à l'envers, et
le défaut a l'air correct sur l'image.

**L'échelle est le piège n°1.** Les feuilles actuelles du projet sont calées sur un chasseur de 2 m.
La citadelle en fait **19,6**. Chaque prompt donne donc une taille réelle explicite — c'est ce qui
évite qu'une belle texture lise comme du bruit rayé une fois posée.

Après chaque génération, la ligne `tuilage :` de l'outil doit dire **OK**, et il faut **ouvrir la
preview** : son quart haut-gauche montre l'image en 2×2 tuiles, c'est là qu'une couture se voit.

---

## 1/5 — citadel_panels_height

**PROMPT — à coller tel quel :**

```
Texture répétable sans couture, en niveaux de gris, représentant le blindage de coque
d'une immense forteresse spatiale militaire. Grandes plaques d'armure de forme
irrégulière — hexagones tronqués, trapèzes, rectangles aux coins coupés — assemblées
bord à bord et séparées par des joints creusés nets. Rivets et boulons aux angles des
plaques. Quelques trappes de maintenance rectangulaires à cadre en relief, réparties
sans régularité. Deux ou trois plaques plus épaisses que les autres, en léger surplomb.

Échelle : environ six plaques sur la largeur de l'image, chaque plaque représentant à
peu près un mètre cinquante en taille réelle. Motif dense mais lisible, jamais bruité.

Carte de HAUTEUR : le gris clair est la surface saillante de la plaque, le gris sombre
est le fond des joints creusés. Dégradés doux à l'intérieur des plaques, transitions
franches aux joints. Utiliser toute la plage du noir au blanc.

Vue orthogonale strictement de dessus, éclairage neutre et parfaitement plat, aucune
ombre portée, aucun reflet.

Éviter absolument : couleur, teinte, sépia, texte, lettres, chiffres, labels, logo,
emblème, filigrane, signature, nom de marque ou d'artiste, perspective, point de fuite,
ombre portée, éclairage directionnel, vignettage, bords assombris, cadre, bordure, objet
isolé au centre, fond visible, photographie d'un vaisseau réel, rouille, végétation.
```

| | |
|---|---|
| **Format** | PNG, 2048 × 2048, niveaux de gris |
| **Déposer** | `assets/source/textures/citadel/citadel_panels_height.png` |
| **Ensuite** | `python3 tools/derive-maps.py assets/source/textures/citadel/citadel_panels_height.png --out assets/imported/textures/citadel --mul --preview /tmp/citadel_panels.png` |
| **Vérifier** | ligne `tuilage : … OK` + ouvrir `/tmp/citadel_panels.png` |
| **Produit** | `citadel_panels_nrm.png`, `_rough.png`, `_ao.png`, `_mul.png` |

**Provenance** (source ; une ligne par dérivée à ajouter ensuite) :

```csv
citadel_panels_height_src,assets/source/textures/citadel/citadel_panels_height.png,raster_texture,"ChatGPT imagegen (OpenAI)",,"tiers (genere IA)",proprietary-internal,2026-07-21,docs/forge/output/citadel_textures_generation_prompt.md,,"Carte de hauteur N&B repetable — blindage de coque a l'echelle forteresse (plaques ~1,5 m). ADR-0013."
```

---

## 2/5 — citadel_greebles_height

**PROMPT — à coller tel quel :**

```
Texture répétable sans couture, en niveaux de gris, représentant l'encombrement
mécanique du pont extérieur d'une forteresse spatiale militaire. Tuyauteries de
diamètres variés qui courent en lignes brisées à angles droits, faisceaux de câbles
plaqués, coffrets techniques, grilles de ventilation à lamelles, petits réservoirs
cylindriques, échelles de service, poignées et rails d'arrimage, boîtiers de jonction.
Répartition irrégulière : des zones denses et des zones presque nues, jamais une grille
uniforme.

Échelle : les plus gros éléments représentent environ un mètre en taille réelle, les
plus petits une vingtaine de centimètres. Matériel militaire fonctionnel, entretenu,
lourd — pas de la ferraille.

Carte de HAUTEUR : le gris clair est le sommet des pièces en saillie, le gris sombre le
pont sur lequel elles reposent. Utiliser toute la plage du noir au blanc.

Vue orthogonale strictement de dessus, éclairage neutre et parfaitement plat, aucune
ombre portée, aucun reflet.

Éviter absolument : couleur, teinte, texte, lettres, chiffres, labels, logo, emblème,
filigrane, signature, nom de marque ou d'artiste, perspective, point de fuite, ombre
portée, éclairage directionnel, vignettage, bords assombris, cadre, bordure, objet isolé
au centre, photographie d'un moteur réel, rouille, saleté organique, végétation.
```

| | |
|---|---|
| **Format** | PNG, 2048 × 2048, niveaux de gris |
| **Déposer** | `assets/source/textures/citadel/citadel_greebles_height.png` |
| **Ensuite** | `python3 tools/derive-maps.py assets/source/textures/citadel/citadel_greebles_height.png --out assets/imported/textures/citadel --strength 9 --preview /tmp/citadel_greebles.png` |
| **Vérifier** | ligne `tuilage : … OK` + ouvrir `/tmp/citadel_greebles.png` |
| **Produit** | `citadel_greebles_nrm.png`, `_rough.png`, `_ao.png` |

> `--strength 9` et non 6 : les greebles doivent saillir davantage que les lignes de panneau,
> sinon ils lisent comme un décalque plat sur la coque.

**Provenance :**

```csv
citadel_greebles_height_src,assets/source/textures/citadel/citadel_greebles_height.png,raster_texture,"ChatGPT imagegen (OpenAI)",,"tiers (genere IA)",proprietary-internal,2026-07-21,docs/forge/output/citadel_textures_generation_prompt.md,,"Carte de hauteur N&B repetable — encombrement mecanique de pont (tuyaux, trappes, grilles). ADR-0013."
```

---

## 3/5 — citadel_wear_mask

**PROMPT — à coller tel quel :**

```
Texture répétable sans couture, en niveaux de gris, représentant l'encrassement d'une
coque métallique de vaisseau militaire spatial en service. Coulures verticales longues
et fines partant de points hauts, comme des traînées sous des évents. Auréoles diffuses
autour de zones de rejet. Assombrissement progressif le long de lignes qui suggèrent
des arêtes de plaques. Quelques éclaboussures et taches irrégulières de tailles variées.
Aspect doux et diffus, sans aucune forme géométrique nette.

Carte de MASQUE : le blanc est la surface propre, le noir est la zone la plus encrassée.
Grande majorité de l'image en blanc ou gris très clair — la coque est entretenue, elle
n'est pas à l'abandon. Encrassement présent sur environ un quart de la surface.

Vue orthogonale strictement de dessus, éclairage neutre et parfaitement plat.

Éviter absolument : couleur, teinte, rouille orange, texte, lettres, chiffres, logo,
filigrane, signature, perspective, ombre portée, vignettage, bords assombris, cadre,
plaques, rivets, panneaux, lignes de structure, formes géométriques dures, mousse,
végétation, aspect abandonné ou épave.
```

| | |
|---|---|
| **Format** | PNG, 2048 × 2048, niveaux de gris |
| **Déposer** | `assets/source/textures/citadel/citadel_wear_mask.png` |
| **Ensuite** | `python3 tools/derive-maps.py assets/source/textures/citadel/citadel_wear_mask.png --out assets/imported/textures/citadel --mask --preview /tmp/citadel_wear.png` |
| **Vérifier** | ligne `tuilage : … OK` + ouvrir `/tmp/citadel_wear.png` |
| **Produit** | `citadel_wear_mask.png` |

> `--mask` : on ne dérive **ni normale ni AO** d'une salissure — creuser la coque là où elle est
> seulement sale donnerait des cratères de crasse.

**Provenance :**

```csv
citadel_wear_mask_src,assets/source/textures/citadel/citadel_wear_mask.png,raster_texture,"ChatGPT imagegen (OpenAI)",,"tiers (genere IA)",proprietary-internal,2026-07-21,docs/forge/output/citadel_textures_generation_prompt.md,,"Masque N&B repetable — encrassement et coulures. Blanc = propre. ADR-0013."
```

---

## 4/5 — crystal_facets_height

**PROMPT — à coller tel quel :**

```
Texture répétable sans couture, en niveaux de gris, représentant la surface taillée d'un
énorme cristal minéral. Grandes facettes planes aux arêtes rectilignes et vives, de
tailles et d'orientations variées, se rencontrant à angles nets comme une pierre
précieuse taillée à la main. À l'intérieur des facettes, de fines fractures internes et
des inclusions allongées. Quelques arêtes secondaires plus courtes qui subdivisent les
plus grandes facettes.

Échelle : trois à quatre grandes facettes seulement sur la largeur de l'image, chacune
représentant à peu près un mètre en taille réelle. Composition large et calme, jamais un
motif fin ou répétitif.

Carte de HAUTEUR : le gris clair est le sommet d'une facette, le gris sombre le creux
d'une arête entre deux facettes. Aplats francs à l'intérieur des facettes, transitions
nettes aux arêtes. Utiliser toute la plage du noir au blanc.

Vue orthogonale strictement de dessus, éclairage neutre et parfaitement plat, aucune
ombre portée, aucun reflet, aucune réfraction, aucun éclat spéculaire.

Éviter absolument : couleur, teinte, bleu, cyan, turquoise, texte, lettres, chiffres,
logo, filigrane, signature, perspective, ombre portée, éclairage directionnel, reflets,
scintillement, halo, vignettage, cadre, objet isolé au centre, fond visible,
photographie d'une gemme réelle, monture, bijou.
```

| | |
|---|---|
| **Format** | PNG, 2048 × 2048, niveaux de gris |
| **Déposer** | `assets/source/textures/citadel/crystal_facets_height.png` |
| **Ensuite** | `python3 tools/derive-maps.py assets/source/textures/citadel/crystal_facets_height.png --out assets/imported/textures/citadel --strength 4 --mul --mul-floor 0.7 --preview /tmp/crystal.png` |
| **Vérifier** | ligne `tuilage : … OK` + ouvrir `/tmp/crystal.png` |
| **Produit** | `crystal_facets_nrm.png`, `_rough.png`, `_ao.png`, `_mul.png` |

> La couleur cyan est **bannie du prompt** : elle vient du matériau `AA_Emissive_Engine` du kit, qui
> reste la source de vérité de la palette (ADR-0013). Une texture qui la porterait ferait diverger
> le noyau de la charte.
>
> `--mul-floor 0.7` : sur un émissif, une multiplication trop noire éteint le cristal au lieu de le
> facetter.

**Provenance :**

```csv
crystal_facets_height_src,assets/source/textures/citadel/crystal_facets_height.png,raster_texture,"ChatGPT imagegen (OpenAI)",,"tiers (genere IA)",proprietary-internal,2026-07-21,docs/forge/output/citadel_textures_generation_prompt.md,,"Carte de hauteur N&B repetable — facettes du noyau cristallin. Sans couleur : le cyan vient du materiau. ADR-0013."
```

---

## 5/5 — citadel_deck_markings_mask

**PROMPT — à coller tel quel :**

```
Texture répétable sans couture, en niveaux de gris, représentant les marquages peints au
sol d'un pont d'envol militaire. Uniquement des formes géométriques : bandes de danger à
hachures diagonales parallèles, chevrons directionnels alignés, équerres d'angle,
cercles concentriques de zone d'appontage, lignes de guidage continues et pointillées,
rectangles de délimitation à coins ouverts. Marquages usés par endroits, avec des
ruptures et des écaillages le long des tracés.

Échelle : les bandes de danger font une trentaine de centimètres de large en taille
réelle, les cercles de zone environ trois mètres de diamètre. Grandes zones de pont
laissées entièrement nues entre les marquages.

Carte de MASQUE : le blanc est le marquage peint, le noir est le pont nu. Environ un
cinquième de l'image en blanc, pas davantage.

Vue orthogonale strictement de dessus, éclairage neutre et parfaitement plat.

Éviter absolument : texte, lettres, mots, chiffres, nombres, numéros, caractères,
symboles alphabétiques, logo, emblème, filigrane, signature, couleur, teinte jaune,
perspective, ombre portée, vignettage, bords assombris, cadre, plaques, rivets, tuyaux,
relief, vaisseau, personnage, flèche isolée au centre.
```

| | |
|---|---|
| **Format** | PNG, 2048 × 2048, niveaux de gris |
| **Déposer** | `assets/source/textures/citadel/citadel_deck_markings_mask.png` |
| **Ensuite** | `python3 tools/derive-maps.py assets/source/textures/citadel/citadel_deck_markings_mask.png --out assets/imported/textures/citadel --mask --preview /tmp/citadel_markings.png` |
| **Vérifier** | ligne `tuilage : … OK` + ouvrir `/tmp/citadel_markings.png` |
| **Produit** | `citadel_deck_markings_mask.png` |

> **Aucun texte, y compris les chiffres.** Ce n'est pas une coquetterie : un générateur d'images rend
> des glyphes déformés qui lisent comme une faute, et un numéro inventé peut ressembler à un
> marquage sous licence. Le bloc « éviter » les liste sept fois pour cette raison.

**Provenance :**

```csv
citadel_deck_markings_mask_src,assets/source/textures/citadel/citadel_deck_markings_mask.png,raster_texture,"ChatGPT imagegen (OpenAI)",,"tiers (genere IA)",proprietary-internal,2026-07-21,docs/forge/output/citadel_textures_generation_prompt.md,,"Masque N&B repetable — marquages geometriques de pont, sans aucun texte. Blanc = marquage. ADR-0013."
```

---

## Si une image ne convient pas

Corriger **le prompt**, pas l'image, et régénérer. Les leviers, par ordre d'efficacité :

| Symptôme | Levier |
|---|---|
| Motif trop fin, lit comme du bruit | baisser le nombre d'éléments annoncé (« quatre plaques » au lieu de six) |
| Relief mou une fois dérivé | renforcer « utiliser toute la plage du noir au blanc », puis `--strength` plus haut |
| Couture visible (`tuilage` ≠ OK) | réinsister sur « répétable sans couture » en tête **et** en fin de prompt ; en dernier recours `--fix-tiling 64`, en regardant le résultat |
| Ombres ou perspective apparues | remonter « vue orthogonale, éclairage plat » avant la description du sujet |
| Image teintée | l'outil le signale (`chroma moyenne`) ; ajouter « strictement noir et blanc » |
