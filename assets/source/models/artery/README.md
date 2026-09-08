# `artery/` — pylône de poupe, conduite et flexible (BRIEF-0108)

Trois livraisons tierces du 2026-09-08, **reconstruites** au budget du jeu.
Cinq binaires en sortent : `stern_pylon.glb`, `artery_conduit.glb`,
`artery_conduit_bend.glb`, `artery_hose.glb`, `artery_hose_bend.glb`
(dans `assets/imported/models/backgrounds/`).

## ⚠️ Ici on ne réduit pas : on **reconstruit**

C'est la différence avec `../stern/` (`BRIEF-0105`). Là-bas, l'agent tiers n'avait livré
que des `.blend` : impossible de faire autre chose que **transformer** un maillage déjà
cuit, en supprimant des pièces entières (raboter ouvrait le flanc des coques fermées —
mesuré, regardé, documenté dans `reduce_stern.py`).

Ici, **les trois livraisons arrivent avec leur générateur complet**. On ne touche donc pas
au maillage : on **repose les constantes** et on relance le générateur de l'auteur.
Une bague de 32 côtés ne se rabote pas — elle se **régénère à 8 côtés**, et elle reste
une bague.

La conséquence porte le critère le plus dur du brief : **le contrat de noms est vide par
construction.** Les repères `CTRL | ` ne sont pas « préservés », ils sont produits par la
ligne de code de l'auteur qui les a toujours produits.

## Les fichiers

| Fichier | Ce que c'est |
|---|---|
| `author/geometry.py` | ⚠️ **verbatim** — identique dans les trois livraisons (même md5) |
| `author/{pylon,conduit,hose}_build.py` | ⚠️ **verbatim** — les générateurs de l'auteur |
| `author/{pylon,conduit,hose}_animation.py` | ⚠️ **verbatim** — les onze clips |
| `author/*_manifest.json` | ce que l'auteur déclare (cotes, clips, repli de matériaux) |
| `forge_geometry.py` | `author/geometry.py` **avec ses six leviers** — c'est ici que le budget se décide |
| `forge_shims.py` | les bouchons `materials` / `studio` / `paths` : zéro texture, zéro chemin tiers |
| `build_artery.py` | le pilote : leviers, listes de suppression, repli de matériaux, UV, export |
| `verify_artery.py` | la vérification **sur les binaires, après réimport** |
| `render_artery_plates.py` | les planches, **à la caméra du jeu** |

Le `.blend` de l'auteur **n'est pas versionné**, et c'est un écart assumé à `ADR-0048` —
voir la réserve §5 du rapport (`docs/forge/output/BRIEF-0108-report.md`).

## Rejouer

```bash
# les cinq binaires
blender-aegis -t 1 -b -noaudio --python assets/source/models/artery/build_artery.py -- --all

# l'inventaire par famille : ce que chaque nom coûte, et s'il est jeté
blender-aegis -t 1 -b -noaudio --python assets/source/models/artery/build_artery.py -- --all --inventory

# la variante du repli de matériaux proposé par le brief (écrit dans build/, gitignoré)
blender-aegis -t 1 -b -noaudio --python assets/source/models/artery/build_artery.py -- --all --brief-materials

# vérifier : contrat de noms, clips rejoués, continuité Rupture->Rompu, UV, images
blender-aegis -t 1 -b -noaudio --python assets/source/models/artery/verify_artery.py

# regarder (ADR-0006)
blender-aegis -t 1 -b -noaudio --python assets/source/models/artery/render_artery_plates.py -- --states --materials
```

⚠️ **`-t 1` est obligatoire** (`docs/KB/.../howto-determinisme-des-coques.md`) : le calcul
des tangentes somme en virgule flottante dans un ordre qui dépend du nombre de workers.
Sans lui, deux exécutions ne rendent pas le même fichier.

## Les six leviers, dans l'ordre de ce qu'ils rapportent

1. **`BEVEL = False`** — les chanfreins à 2 segments posés sur *tous* les objets. Ils
   coûtent l'essentiel du fichier de l'auteur et rendent moins d'un quart de pixel.
2. **`RING_CAP` / `ROD_CAP` / `SECTOR_CAP`** — la résolution des pièces de révolution.
   Une conduite de 10 cm ne vaut pas 32 côtés.
3. **`CURVE_RES` / `CURVE_BEVEL_RES`** — idem pour les tuyaux, qui sont des *courbes* et
   n'ont de triangles qu'à la conversion. ⚠️ Le `pipe()` du pylône réécrit ces deux
   valeurs **après** `geometry.hose()` : sans le patch textuel déclaré dans
   `SOURCE_PATCHES`, le levier est sans effet et **rien ne le signale**.
4. **`KILL`** — les familles qui **n'existent plus** à la taille visée. Elles sont
   construites puis mises à la poubelle (une collection non liée à la scène), pour que le
   `build.py` de l'auteur continue de tourner sans une ligne de changement.
5. **La taille finale**, appliquée après coup par `rescale()` — sommets, pivots, **os** et
   **clés d'animation**. Le `.glb` livré ne contient aucun nœud à l'échelle ≠ 1.
6. **`TRIM`** — un filtre par indice, pour les familles répétées en série.

## Ce que ce dossier ne contient pas

- **Aucune texture** (`ADR-0028`) : les 8 à 13 atlas de chaque livraison sont remplacés
  par les cinq slots du kit, et toutes les images sont purgées avant l'export.
- **Aucun placement** : combien de conduites, où, sur quels tronçons — c'est une décision
  de conception (brief §Hors périmètre). Les planches alignent les pièces pour qu'on les
  regarde, elles ne les posent pas.
