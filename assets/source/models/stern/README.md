# Poupe du Long Cortège — les quatre sources tierces et leur réduction

Quatre pièces livrées par un agent tiers pour la phase finale du niveau 2
(`BRIEF-0105`). Elles entrent ici **avec leur source** (`ADR-0048`), et le dépôt
écrit la transformation qu'il leur applique — c'est tout ce dossier.

| Source ici | Livraison d'origine | Sortie |
|---|---|---|
| `stern_engine.blend` | `groupe-moteur-principal/v2` (`groupe_moteur_principal.blend`) | `assets/imported/models/backgrounds/stern_engine.glb` |
| `stern_cradle.blend` | `berceau-moteur/v1` (`berceau_moteur.blend`) | `stern_cradle.glb` |
| `stern_anchor.blend` | `ancrage-destructible/v1` (`ancrage_destructible.blend`) | `stern_anchor.glb` |
| `stern_arm.blend` | `bras-ancrage/v1` (`bras_ancrage.blend`) | `stern_arm.glb` + `stern_arm_mirror.glb` |

Les `.blend` sont **les fichiers de l'auteur, octet pour octet** : aucune retouche
manuelle, rien à rouvrir dans Blender pour reproduire une livraison. Tout ce que le
dépôt leur fait vit dans `reduce_stern.py`.

## Les deux commandes

```sh
# Les cinq binaires du jeu (option B : PBR par facteurs, zéro image)
blender-aegis -t 1 -b -noaudio --python assets/source/models/stern/reduce_stern.py -- --all

# Les mêmes, avec les onze atlas de l'auteur (option A), dans build/ — gitignoré
blender-aegis -t 1 -b -noaudio --python assets/source/models/stern/reduce_stern.py -- --all --textured

# Les planches de contrôle, à la caméra du jeu (ADR-0006)
blender-aegis -t 1 -b -noaudio --python assets/source/models/stern/render_stern_plates.py -- --states --texture
```

⚠️ **`-t 1` est obligatoire** — même raison que `scripts/build-hull.sh` : sans lui, deux
exécutions ne rendent pas le même fichier. Vérifié ici sur trois exécutions, zéro octet
divergent.

## Ce que la réduction fait, dans l'ordre, et ce qu'elle rapporte

| Levier | Ce qu'il coupe | Mesure (moteur) |
|---|---|---|
| 1. Les biseaux | `BEVEL` 2 segments, 1 à 12 mm, sur 100 % des objets | 267 344 → 50 656 tri |
| 2. La visserie | tout ce qui porte `09 \| Vis et raccords` | −11 736 tri |
| 3. Les conduites | courbes ramenées à `resolution_u = 1` avant conversion | — |
| 4. La dé-subdivision | seulement les grandes pièces de révolution (bagues, étages de tuyère) | −11 000 tri environ |
| 5. Le désherbage | **suppression de pièces entières**, triées au rendement pixels/triangle | jusqu'au budget |

⛔ **Aucune décimation par `COLLAPSE`.** Ce n'est pas un oubli : quatre versions ont été
rendues à la caméra du jeu et regardées. Sous 0,62 de ratio, la nacelle rend une **tôle
déchiquetée** de triangles noirs — un capot est une boîte de douze triangles, et un
collapse qui lui en laisse sept lui **ouvre le flanc**. Le maillage de l'auteur n'est pas
une surface : c'est une pile de centaines de coques fermées, et une coque fermée a un
plancher. Un assemblage de pièces rigides ne se réduit pas en rabotant chaque pièce ; il
se réduit en gardant **moins de pièces, entières**.

Conséquence, et elle est forte : **aucun sommet de l'auteur n'a bougé**, hors les pièces
de révolution que `coarsen()` dé-subdivise.

## Ce que la réduction NE touche jamais

- **Les repères `CTRL | `** — ce sont des `Empty`, la réduction n'agit que sur les
  maillages. Vérifié sur le binaire : 100 repères sur 100, écart **0,000000 mm**.
- **Les pistes NLA** — les 18 clips sortent avec les mêmes canaux et les mêmes
  amplitudes que les binaires de l'auteur, à `0,00e+00` près.
- **Le repère et l'échelle** — pas de correction d'axe : la conversion Y-up standard de
  glTF est celle dont `long_cortege_stern.tres` a déjà tiré ses cotes
  (`(0 ; 1 ; 3,7)` auteur → `engine_seat = (0 ; 3,70 ; −1,00)`).

## Ce que la réduction remplace

Les neuf slots de l'auteur se replient sur la nomenclature du kit
(`tools/blender/lib/aegis_kit.py`), palette de l'Unisson :

| Auteur | Kit |
|---|---|
| `01 Anthracite blinde`, `02 Acier gris use`, `03 Tranches acier brosse` | `AA_Hull` |
| `04 Cavites graphite`, `05 Conduites noires`, `09 Vis et raccords` | `AA_Greeble` |
| `06 Energie magenta`, `07 Coeur plasma`, `08 Balises rouges` | `AA_Emissive_Engine` |

⚠️ `CortegeSkin` reconnaît son émissif **par son nom** : une veine rangée ailleurs
resterait allumée sur un vaisseau mort, sans erreur ni test rouge. L'émissif est donc
isolé dans son propre maillage (`GLOW | …`) et il a une **part réservée du budget**
(`GLOW_SHARE`), prise avant tout désherbage — sans elle, le tri au rendement laissait
*zéro* triangle émissif sur le bras.

Les UV sont refaites en **projection en boîte à 0,70 tuile/m** (1,43 m par tuile, la
densité d'Ambry sur le Long Cortège). Mesuré sur les binaires : 0,68 à 0,70 tuile/m en
moyenne, anisotropie maximale 1,41 à 1,68 pour une borne théorique de √3 = 1,732.

## Limites connues

- La variante **texturée** (option A) n'est pas versionnée : 236 Mo de LFS pour cinq
  binaires, contre 2,4 Mo en PBR par facteurs. Une commande la reconstruit.
- `coarsen()` est le seul endroit où de la géométrie d'auteur est modifiée. Le seuil est
  une **emprise à l'écran** (`protect_area`), pas un nombre de triangles.
- Les `.blend` pèsent 243 Mo à eux quatre, dont l'essentiel est les onze atlas 2048²
  empaquetés. Si l'option B est retenue définitivement, les dépaqueter les ramènerait
  à ~24 Mo — mais l'option A deviendrait irreproductible depuis le dépôt seul.
