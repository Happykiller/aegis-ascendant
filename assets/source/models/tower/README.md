# `tower/` — la tour d'échange thermique de poupe (BRIEF-0112)

Quatrième livraison tierce du dossier, arrivée le 2026-09-08 avec **son générateur
complet**. Un binaire en sort : `stern_tower.glb`, dans
`assets/imported/models/backgrounds/`, monté quatre fois par le code sur les repères
`CTRL | Tour 01…04` que pose `tools/blender/build_stern.py`.

## ⚠️ Ici on ne décime pas : on **reconstruit**

C'est la méthode du `BRIEF-0108`, appliquée telle quelle. Le `build.py` de l'auteur est
exécuté **verbatim** (`author/tower_build.py`, copie au bit près) par-dessus un
`geometry.py` dont chaque constante de résolution est devenue un levier. Une bague de
64 côtés ne se rabote pas — elle se **régénère à 12**, et elle reste une bague.

**129 272 triangles livrés → 8 388.** Le contrat de noms est **vide par construction** :
les 32 repères `CTRL | ` sont produits par la ligne de code de l'auteur qui les a toujours
produits (écart mesuré contre son binaire : **0,0 mm sur 32/32**).

## ⚠️ `forge_geometry.py` n'est **pas** dupliqué ici

`author/geometry.py` de cette livraison est **octet pour octet** celui des trois livraisons
du `BRIEF-0108` (`md5 96fb44d83a06750ff5dd678ded65f258`). On importe donc
`../artery/forge_geometry.py` et `../artery/forge_shims.py`, et `build_tower.py` **vérifie
l'égalité md5 au démarrage** — si l'auteur fait diverger son module un jour, le build
échoue au lieu de reconstruire une pièce que les leviers ne décrivent plus.

## La hauteur : ce n'est pas le plafond qui borne, c'est l'empreinte

L'auteur livre **26,00 m**, et 26 m ne rentre nulle part : posée sur le pont de poupe,
une telle tour culmine à `y = +14,15`, c'est-à-dire **à la hauteur exacte de l'œil de la
caméra**.

La tour mesure **14 m de large pour 26 de haut**, soit **0,538 m de plan par mètre de
hauteur**. Les deux enveloppes légales du brief donnent 5,20 m (règle A) et 8,60 m
(règle B) ; il faudrait 2,80 et 4,63 m de plan **libre** pour les dépenser. La poupe n'en
a pas :

| Station | Plat mesuré (en `z`) | Tour possible |
|---|---:|---:|
| plateau du bossage (`z −8,60 … −11,20`) | 2,60 m | **4,83 m** |
| plateau de rive du massif (`z −8,60 … −11,60`) | 3,00 m | 5,57 m |

**On livre 4,70 m** — un seul binaire, quatre stations, 3,4 cm de marge à chaque bout du
plat le plus court. Ce que la règle B apporte n'est donc pas de la hauteur de pièce, c'est
**3,80 m d'assise** : la même tour posée sur la rive (`−4,60`) culmine à `+0,10`, contre
`−3,70` sur le plateau (`−8,40`).

## Les fichiers

| Fichier | Ce que c'est |
|---|---|
| `author/geometry.py` | ⚠️ **verbatim** — identique aux trois livraisons du `BRIEF-0108` (même md5) |
| `author/tower_build.py` | ⚠️ **verbatim** — le générateur de l'auteur, 16 modules |
| `author/tower_animation.py` | ⚠️ **verbatim** — les trois clips |
| `author/tower_manifest.json` | ce que l'auteur déclare (cotes, clips, repli de matériaux) |
| `build_tower.py` | le pilote : leviers, liste de suppression, repli de matériaux, UV, export |
| `verify_tower.py` | la vérification **sur le binaire, après réimport** |

Les leviers eux-mêmes sont dans `../artery/forge_geometry.py`, les bouchons
`materials` / `studio` / `paths` dans `../artery/forge_shims.py`.

## Rejouer

```bash
# le binaire
blender-aegis -t 1 -b -noaudio --python assets/source/models/tower/build_tower.py -- --all

# l'inventaire par famille : ce que chaque nom coûte, et s'il est jeté
blender-aegis -t 1 -b -noaudio --python assets/source/models/tower/build_tower.py -- --all --inventory

# vérifier : contrat de noms, 3 clips rejoués, LES QUATRE ROTORS, UV, images
blender-aegis -t 1 -b -noaudio --python assets/source/models/tower/verify_tower.py

# la carène et ses quatre repères (le harnais `_seat_probe` relit l'assise)
blender-aegis -t 1 -b -noaudio --python tools/blender/build_stern.py
```

⚠️ **`-t 1` est obligatoire** (`docs/KB/.../howto-determinisme-des-coques.md`) : le calcul
des tangentes somme en virgule flottante dans un ordre qui dépend du nombre de workers.
Sans lui, deux exécutions ne rendent pas le même fichier.

## Les deux pièges qui ont coûté du temps ailleurs, et qui sont ici aussi

1. **`pipe()` réécrit la résolution des courbes APRÈS `geometry.hose()`.** Exactement le
   défaut trouvé sur le pylône au `BRIEF-0108`, dans le même helper, à la même ligne. Sans
   le patch textuel déclaré (`SOURCE_PATCHES`), le levier 3 est **sans effet et rien ne le
   dit** — les huit conduites de refroidissement sont des courbes, elles n'ont de triangles
   qu'à la conversion.
2. **On redimensionne AVANT de déplier.** `box_project_uv()` projette en **mètres** :
   déplier à la taille de l'auteur puis réduire d'un facteur `k` multiplie la densité par
   `1/k`. Aucune erreur, aucun test rouge, et ça ne se verrait qu'une fois la texture
   générée — donc trop tard.

## Ce que ce dossier ne contient pas

- **Aucune texture** (`ADR-0028`) : les 13 atlas de la livraison sont purgés, avec leurs
  matériaux, avant l'export. **Zéro image embarquée** dans le binaire.
- **Le `.blend` de l'auteur** — écart assumé à `ADR-0048`, pour la même raison qu'au
  `BRIEF-0108` (§10.3) : le générateur est **complet**, il part d'une scène vide, et le
  dépôt s'en sert à chaque build. La copie est dans
  `~/aegis-ascendant_gpt_models/tour-echange-thermique/v1/blender/`.
- **Le code de jeu** : monter les tours et câbler les rotors appartient au concepteur.
