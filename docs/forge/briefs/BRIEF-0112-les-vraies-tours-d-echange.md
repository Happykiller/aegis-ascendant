# BRIEF-0112 — Les vraies tours d'échange thermique

- **Statut** : livré — intégré, mais deux tours sur quatre sont hors cadre (`BRIEF-0113`)
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-08
- **Livraison tierce** : `~/aegis-ascendant_gpt_models/tour-echange-thermique/`

## Objectif

Faire entrer `Stern_CoolingTower_01.glb` — et remplacer les deux tours d'échange **régénérées** au
`BRIEF-0110`, qui l'ont été faute de pièce livrée. Celle-ci est arrivée le jour même.

## L'audit, mesuré sur le binaire

| | |
|---|---|
| Triangles | **129 272** — la plus grosse livraison du dossier |
| Cotes | 14,00 × **26,00** × 14,00 m |
| Clips | `Service`, `Refroidissement`, `Maintenance` |
| Repères `CTRL` | **32**, dont **quatre rotors de ventilateur**, un noyau thermique, une passerelle de service, des panneaux de maintenance à charnières, un diffuseur conique |
| Slots | la convention connue (`01 Anthracite`… `06 Energie magenta`, plus `10 Carbone technique` et `11 Conduite sombre` déjà arbitrés au `BRIEF-0108`) |
| Source | **`.blend` + générateur complet** — donc on **régénère** à basse densité, on ne décime pas |
| Modules | 16 sous-pièces exportées à part |

## ⚠️ AUCUN BUDGET DE TRIANGLES

L'opérateur l'a tranché le 2026-09-08 : *« je ne veux pas entendre parler de budget et de
restriction, je veux un jeu beau »*, et la mesure lui donne raison — la poupe entière rend à
**2,0 à 3,7 ms** sur les **16,67** d'une image à 60 Hz.

**Ne coupez rien « pour tenir ».** Rapportez les comptes, ne les contraignez pas. Ce qui reste
vrai et n'est pas un budget : un détail de 3 cm fait **1,4 pixel** à 45,8 px/m — ne le payez pas
parce que personne ne le verra, pas parce qu'il coûte.

## ⚠️ LA SEULE CONTRAINTE DURE EST LA HAUTEUR, ET ELLE EST MESURÉE

**26 m ne rentre nulle part dans ce niveau.** La caméra du jeu est à `y = 14` :

| Assise | Sommet d'une tour de 26 m | Par rapport à la caméra |
|---|---:|---:|
| Pont de poupe (−11,85) | **+14,15** | **à sa hauteur exacte** |
| Plateau du massif (−8,40) | +17,60 | **+3,60 au-dessus** |
| Étagère de rive B2 (−5,60) | +20,40 | +6,40 au-dessus |
| Pont médian du corridor (−4,99) | +21,01 | +7,01 au-dessus |

Une tour qui monte à la hauteur de l'œil ne se lit plus comme un décor : elle **remplit le cadre**
et masque le jeu.

**Deux enveloppes légales, et vous choisissez :**

| Règle | Où | Hauteur maximale |
|---|---|---|
| **A — sous le plafond de construction** (`−3,20`) | partout | 8,65 m depuis le pont de poupe · 5,20 depuis le plateau · 2,40 depuis l'étagère B2 |
| **B — sommet ≤ `y = +2`, base à `|x| ≥ 16`** | flancs de poupe seulement | 8,60 m depuis B1 · **7,60 depuis B2** · 6,60 depuis B3 |

⚠️ **LA RÈGLE B EST CELLE QUI PAIE, ET VOICI POURQUOI ELLE EST LÉGALE.** Le plafond `−3,20`
protège la couche où le chasseur vole ; or le plan de vol s'arrête à **`|x| = 14`**. Au-delà, le
joueur n'ira jamais : une tour peut donc y monter jusqu'à son altitude sans qu'il la traverse
jamais. C'est le seul endroit du niveau où de la vraie hauteur est possible.

⚠️ **ET LE CORRIDOR N'A PAS DE FLANCS.** Sa demi-largeur plafonne à ~12 m : tout y est **dans** le
plan de vol. « Utilisable partout » est vrai du modèle, pas de cette coque — sur les 500 m, seule
la règle A s'applique, donc 1,1 à 1,8 m de ciel. Dites-le si vous en tirez autre chose.

## Ce qu'il faut faire

### 1. Régénérer à la hauteur qui rentre

Comme au `BRIEF-0108` : le générateur de l'auteur tourne, ses constantes de résolution sont des
leviers. **Supprimez ce qui n'existerait plus** à la taille retenue, ne rétrécissez pas.

Ce qui doit survivre : la **silhouette**, les **quatre rotors** et les trois clips.

### 2. Remplacer les deux tours du massif

`build_stern.py` porte `build_towers()` — régénérée hier à 1 592 triangles pour deux, à
`x = ±5,40`, `z = −10,05`. ⚠️ **Elles sont DANS le plan de vol** (|x| ≤ 14) : la règle A s'y
applique, donc 5,20 m. Retirez-les et posez `CTRL | Tour 01/02` à leur station.

### 3. Et deux tours de flanc, qui sont le vrai gain

Sur les étagères de rive, à `|x| ≥ 16`. C'est là que la règle B s'applique et que la pièce peut
faire **7 à 8,6 m** — trois fois ce que le plateau permet. `CTRL | Tour 03/04`.

⚠️ **VÉRIFIEZ LE RECOUVREMENT AVEC CE QUI EST DÉJÀ SUR LES FLANCS** : les deux socles de pylône
du `BRIEF-0110` (`x = ±17,20`, `z = −0,40`), les huit repères `Liaison`, et les plates-formes
volantes de la garnison — dont le `BRIEF-0110` signale déjà un recouvrement résiduel de 2,28 m³.

### 4. Les rotors — une question de conception, pas de forge

Livrez les quatre rotors **animés dans les clips**. Le code décidera s'ils tournent en permanence
ou seulement tant que les moteurs vivent : arrêtés au blackout, ils feraient une belle image de
fin. Dites simplement dans le rapport **quel clip fait tourner quoi**.

## Texture (ADR-0028) / Animation (ADR-0046)

**Aucune image** — PBR par facteurs, `CortegeSkin` posera les cartes dérivées.
**Les trois clips sont conservés et cuits en clés**, rejoués après réimport.

## Livrables

| Fichier | Description |
|---|---|
| `assets/imported/models/backgrounds/stern_tower.glb` | la tour, régénérée |
| `assets/source/models/tower/` | source auteur + pilote + vérification (`ADR-0048`) |
| `tools/blender/build_stern.py` | `build_towers()` retirée, quatre repères `CTRL \| Tour NN` |
| `assets/imported/models/backgrounds/stern_hull.glb` | la carène |
| `docs/forge/output/BRIEF-0112-report.md` | hauteur retenue, repères, marges, comptes |
| `docs/forge/output/BRIEF-0112-planche.png` | rendus à la caméra du jeu, **tours instanciées** |

## Critères d'acceptation

- [ ] **La hauteur retenue est justifiée par la mesure**, règle A ou B nommée, et le sommet de
      chaque tour est donné en `y` absolu.
- [ ] **Aucune tour ne croise le plan de vol** : soit sous `−3,20`, soit à `|x| ≥ 16`.
- [ ] **Quatre repères `CTRL | Tour NN`**, `y` échantillonné, marquant le **bas** de la pièce.
- [ ] **Les quatre rotors et les trois clips se rejouent après réimport.**
- [ ] **Recouvrement mesuré** avec les socles de pylône, les repères `Liaison` et les
      plates-formes volantes — en m³, par pièce.
- [ ] **La jonction `s = 500` et les trois canaux d'échappement sont intacts.**
- [ ] **Déterminisme** : trois exécutions, zéro octet divergent.
- [ ] **Rendu et REGARDÉ à la caméra du jeu**, avec les tours instanciées, **avant/après au même
      cadrage**. ⚠️ Le critère est « on voit une tour d'échange », pas « il y a de la matière ».

## Hors périmètre

- **Le code de jeu** : le concepteur monte les tours et câble les rotors.
- **Le complexe industriel du tronçon 5** (`BRIEF-0111`) et **le corridor**.
- **Les nacelles, berceaux, verrous, bras, canaux.**
