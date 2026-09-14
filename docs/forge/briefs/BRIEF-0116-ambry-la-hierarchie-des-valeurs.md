# BRIEF-0116 — Ambry : la hiérarchie des valeurs, et deux accents à rétablir

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-14
- **Planche** : `assets/reference/concepts/ambry_concept_sheet_2026-09.png`
- **Suite de** : `BRIEF-0115` (livré) et du correctif de valeur de ce jour (commit `e55bba3`)

## Ce qui vient d'être trouvé, et qui change le cadre de ce lot

Ambry était **surexposée**. Mesuré en comparant sa bande en jeu à la **vue gameplay de sa propre
planche**, sur la même emprise :

| | planche | avant | après |
|---|---:|---:|---:|
| luminance médiane | 51 | 135 | **86** |
| tons moyens (60–160) | 29,8 % | 10,7 % | **19,5 %** |
| quasi-blanc (> 200) | 7,0 % | **41,6 %** | **2,9 %** |
| saturation | 26,7 % | 13,5 % | **17,7 %** |

Un plafond de valeur et un réchauffement ont été posés côté code (`AMBRY_VALUE_CEILING`,
`AMBRY_WARM`), et les textures livrées au `BRIEF-0115` **se voient enfin** — sans qu'aucune image
ait été touchée.

⚠️ **CE CHANGEMENT PÉRIME DEUX DE VOS ARBITRAGES**, et c'est pour ça que ce lot existe. Vous les
aviez tranchés en regardant une Ambry dont 41 % de la surface était blanche : ce que vous avez vu
alors n'est plus ce qu'on voit.

## 1. La bâche bleue — à rejuger

Vous l'aviez posée au `#1C2B5E` de la planche de matières, puis **ramenée à l'écru** :

> « elle devenait l'objet le plus visible des vingt-sept mètres, avant les fenêtres »

C'était juste **à l'époque** : contre du blanc pur, un bleu profond est un trou noir. Contre l'ivoire
amorti d'aujourd'hui, ce n'est plus le même rapport — et la saturation d'Ambry est à **17,7 %**
quand la planche est à **26,7 %**. Il nous manque de la couleur, et la bâche est le seul accent
froid que la planche lui donne.

**Reposez le bleu, rendez, regardez.** Le critère ne change pas : **les fenêtres doivent rester
l'élément le plus lumineux de la pièce.** Si le bleu les vole encore, dites-le et gardez l'écru —
mais cette fois le verdict se prend sur la nouvelle valeur.

## 2. Le pas d'appontage — à rejuger aussi

Il est aujourd'hui `#141419`, le plus sombre de la palette, et vous l'avez voulu ainsi :

> « un pont clair de plus effacerait le pas ; c'est sa valeur SOMBRE qui le fait lire comme un pas »

Même remarque : **c'était vrai contre du blanc.** Or la planche montre l'inverse — un pas
**jaune-ocre chaud** avec un H sombre, et c'est l'un des deux seuls accents colorés de la pièce.

⚠️ **ET C'EST L'ENDROIT LE PLUS CHARGÉ D'AMBRY.** C'est de là que le pilote est parti, deux
semaines avant qu'elle ne se taise. Il est vide. Un accent chaud sur un pas vide dit autre chose
qu'un trou noir.

**Vous tranchez**, et vous le mesurez : le pas doit rester **distinct** du pont qui l'entoure — par
la couleur si ce n'est plus par la valeur. Donnez l'écart de luminance et de teinte obtenu.

## 3. ⚠️ Le vrai sujet : les modules sont tous à la même valeur

C'est le point que le code **ne peut pas** régler : les sept modules partagent `AA_Hull_Ambry`,
donc un seul albédo. Sur la planche, ils ne sont pas du tout à la même valeur — certains sont
nettement plus sombres que leurs voisins, et **c'est ce qui les fait compter comme sept modules**
plutôt que comme une masse.

> **C'est exactement le « boîtes identiques » que le panneau *À ÉVITER* de la planche interdit.**
> Vous l'aviez levé par la géométrie au `BRIEF-0115` — sept modules, aucune cote partagée, sept
> traitements de toit. La VALEUR les a re-uniformisés derrière vous.

**Ce qu'il faut : deux ou trois paliers de valeur**, déclarés comme des slots locaux frères de
`AA_Hull_Ambry` — par exemple `AA_Hull_Ambry_B` et `AA_Hull_Ambry_C`, plus sombres de 15 et 30 %.

⚠️ **Et la répartition n'est pas décorative.** Un avant-poste se construit par ajouts sur quarante
ans : le bloc d'origine et ses extensions n'ont ni le même âge ni la même tôle. Que les paliers
racontent cette chronologie — pas un damier.

⚠️ **Le code les habillera tout seul** : `CortegeSkin` choisit l'échelle d'UV, le relief et le
plafond de valeur par le **suffixe `_Ambry`**, pas par une liste. Un slot de plus hérite de tout.
⚠️ Mais son entrée dans `SKINS` ne se pose que **quand ses cartes existent** — un banc le refuse
autrement. Dites dans le rapport si vous voulez des cartes propres à chaque palier, ou s'ils
partagent celles de `AA_Hull_Ambry` (auquel cas je ne déclare rien et ils vivent de leur couleur).

## Ce qui ne change pas

- **La géométrie du `BRIEF-0115` est acceptée.** Ce lot touche des matériaux et des couleurs, pas
  des formes. Le re-plombé, la roche, la serre, les quarante-six fenêtres restent tels quels.
- ⚠️ **Le bord avant reste à `s = 446,5 ± 1`** — le code y déclenche la réplique de Lyra, et
  `test_the_front_edge_of_ambry_is_read_from_the_hull` le vérifie.
- **Aucune image** (`ADR-0028`) : couleurs et slots seulement.
- **Aucun `.gd`, `.tscn`, `.tres`.**
- Le magenta reste interdit sur Ambry ; le vert de la serre reste son seul vert.

## Texture (ADR-0028) / Animation (ADR-0046 §6)

**Aucune image, et c'est un refus motivé.** Ce lot ne touche que des **couleurs de matériau** et des
**slots** : aucune surface neuve n'apparaît, donc rien de neuf n'a besoin d'être peint. Les douze
cartes d'Ambry sont livrées et posées, et le correctif de valeur de ce jour vient précisément de
montrer qu'elles fonctionnaient — c'était la valeur qui les écrasait, pas elles qui manquaient.

⚠️ **Et si vous ajoutez des paliers**, dites dans le rapport s'ils réclament des cartes propres ou
s'ils partagent celles de `AA_Hull_Ambry`. Le second cas est le défaut et il est très bien : deux
tôles de la même famille posées à dix ans d'écart ont le même appareillage et pas la même valeur.

**Géométrie et animation figées.** Ambry n'en prend aucune ici.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_long_cortege.py` | les paliers de valeur, la bâche, le pas |
| `assets/imported/models/backgrounds/long_cortege.glb` | le corridor |
| `docs/forge/output/BRIEF-0116-report.md` | valeurs par slot, répartition des paliers, verdicts sur la bâche et le pas |
| `docs/forge/output/BRIEF-0116-planche.png` | avant/après **au cadrage du jeu** |

## Critères d'acceptation

- [ ] **On compte les modules** sur la capture en jeu. C'est le critère principal.
- [ ] **Les fenêtres restent l'élément le plus lumineux d'Ambry** — c'est le garde-fou de tout ce
      lot, et il prime sur les deux accents.
- [ ] **La bâche et le pas sont rejugés et le rapport dit lesquels ont bougé, avec la mesure.**
      Garder l'ancien arbitrage est une réponse recevable ; ne pas le rejuger ne l'est pas.
- [ ] **La saturation d'Ambry se rapproche de 26,7 %** (elle est à 17,7). Rapportée, pas forcée.
- [ ] **Rien au-dessus de `−3,20`**, `s = 500` intacte, déterminisme sur trois exécutions.
- [ ] `./scripts/check.sh` vert, `test_the_front_edge_of_ambry_is_read_from_the_hull` compris.
- [ ] **Rendu et REGARDÉ à la caméra du jeu** (`ADR-0006`), avant/après au même cadrage.

## Hors périmètre

- La géométrie, les textures, le code de jeu.
- Le reste du bordé, le complexe du tronçon 5, la poupe.
