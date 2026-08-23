# BRIEF-0080 — Retourner `Spike_01` et `Spike_02` vers l'avant (reprise de 0045)

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-23

## ⚠️ LIRE D'ABORD : ce brief reprend un brief RATÉ, et l'erreur était dans la commande

`BRIEF-0045` demandait de retourner `Spike_03` et `Spike_04`. La forge l'a exécuté parfaitement et
l'a prouvé sur six points mesurés. **Le brief désignait les mauvaises épines**, et le livrable a été
annulé.

La cause, à connaître avant de toucher quoi que ce soit :

> **`BossController` applique `FACING_PLAYER = Vector3(0, PI, 0)` à la coque** (`boss_controller.gd:94`).
> Une rotation de 180° autour de Y envoie `(x, y, z)` sur `(−x, y, −z)`. **Tout axe mesuré dans le
> `.glb` est donc vu RETOURNÉ de 180° en jeu.**

Le brief précédent relevait les angles dans le fichier et les présentait comme ceux du plan de jeu.
D'où le tableau réel :

| Épine | angle dans le **fichier** | angle **en jeu** (fichier + 180°) | verdict |
|---|---|---|---|
| `Spike_01` | −111,3° | **+68,7°** | vers l'arrière — **à retourner** |
| `Spike_02` | −71,0° | **+109,0°** | vers l'arrière — **à retourner** |
| `Spike_03` | +59,3° | **−120,7°** | vers le joueur — **NE PAS TOUCHER** |
| `Spike_04` | +111,5° | **−68,5°** | vers le joueur — **NE PAS TOUCHER** |

Convention du plan de jeu, inchangée : `x = X`, `y = −Z`, **le joueur est à −90°**.

## Objectif

Réorienter **`Spike_01` et `Spike_02`** pour qu'elles pointent vers le joueur **en jeu**, comme le
font déjà `Spike_03` et `Spike_04`. Tout le reste de la coque est conservé à l'identique.

**Cible mesurable** : les quatre axes `Spike_NN → Muzzle_Spike_NN` doivent tomber dans
**[+20° ; +160°] dans le repère du FICHIER** — ce qui donne [−160° ; −20°] en jeu.

⚠️ **Vérifier dans les DEUX repères dans le rapport.** Donner pour chaque épine l'angle du fichier
**et** l'angle en jeu (+180°, ramené dans ]−180 ; 180]). C'est la seule façon de rendre l'erreur de
0045 impossible à répéter : un tableau à une seule colonne ne dit pas dans quel repère il est.

## Contexte

Les épines sont des tourelles laser (`ADR-0021`) : chacune télégraphie puis tire, et chaque plaque
d'armure brisée en éteint une. Le playtest a rejeté le rendu — *« les lasers qui devaient partir des
tentacules, ça n'a pas de sens ; là ça sort d'un peu n'importe où »*. Le code compense aujourd'hui en
tirant **depuis la pointe mais vers le joueur** : la pièce montre une direction, le tir en prend une
autre. Une fois les quatre épines tournées vers l'avant, le faisceau pourra enfin **prolonger l'axe**
de la pièce, et la menace se lira sur la silhouette avant le tir.

## Contraintes

### Ce qui NE DOIT PAS changer

- **Le contrat de noms**, à l'identique : `Shell_Ring`, `Shell_Crescent`, `Plate_01..04`,
  `Spike_01..04` (+ `_Mid`, `_Tip`), `Node_01..03`, `Core`, `Core_Center`, `Heart`, `Maw_Center`,
  `Maw_Lip`, `Muzzle_Spike_01..04`.
- **`Spike_03` et `Spike_04`** : orientation, longueur, courbure — **inchangées**. Ce sont elles qui
  étaient bonnes.
- **L'inégalité des épines** et l'asymétrie générale : silhouette validée par `BRIEF-0041`.
- **Budgets** : ~27 710 triangles (plafond 30 000), `AA_Hull` ≥ 30 %, `AA_Emissive_Engine` ≤ 8 %,
  `AA_Greeble` ≤ 20 %.
- **UV et tangentes sur 145/145 surfaces** — la coque est la seule du dépôt à les avoir toutes.
- **Déterminisme** : passer par `./scripts/build-hull.sh` (force `-t 1`), deux exécutions rendent un
  `.glb` byte-identique (`ADR-0008`).
- **bbox** : rester sous 12,0 × 3,4 × 15,0 m (elle vaut 11,03 × 3,16 × 14,00).

### Ce que le travail de 0045 t'apprend, et qui te fera gagner du temps

Le patch de 0045 est conservé (scratchpad de session, `BRIEF-0045-travail-forge.patch`). Deux
constats de la forge y sont transposables **en miroir** :

- **La version « à plat » ne passait pas le harnais de dégagement** : une épine avant, braquée de
  40°, revenait vers l'axe et mordait le mât de sa voisine. D'où une **arche de 22 à 28 cm**, sous la
  rotule d'épaule, qui ne changeait ni la hauteur de coque ni l'aire de silhouette (±0,3 %).
- Le balayage systématique (504 géométries, 455 évaluées sur 25 poses) n'avait trouvé **aucune
  solution plane à longueur constante** — les seules qui dégageaient raccourcissaient l'épine de
  4,49 m à ~2 m, ce qui inverse la hiérarchie protégée par `BRIEF-0041`.

⚠️ **La provision de braquage à ±40° n'a plus de contrepartie dans le code** : `_spine_track` et
`SPINE_TRACK_DEG` étaient déclarés et jamais appliqués ; ils ont été supprimés. Un braquage sera
peut-être réimplémenté (l'opérateur veut des tentacules animées), donc **garde la provision si elle
ne coûte rien**. Mais si elle est le seul obstacle à des épines planes, **dis-le et propose les deux
variantes chiffrées** plutôt que de payer une arche pour une porte que rien ne franchit.

## ⚠️ Le seuil, posé AVANT la mesure

**Si retourner ces deux épines dégrade la silhouette validée** — asymétrie perdue, interpénétration
avec la coquille, les plaques ou les mâts, dégagement des plaques encombré — **dis-le et ne livre
pas.** Une coque cohérente avec deux épines mal orientées vaut mieux qu'une coque incohérente dont
les quatre pointent bien. `BRIEF-0045` a prouvé que ce seuil est réaliste : la solution y existait,
mais au prix d'une arche.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_pale_leviathan.py` | **seules** les définitions de `Spike_01` et `Spike_02` changent |
| `assets/imported/models/bosses/pale_leviathan.glb` | régénérée par `./scripts/build-hull.sh pale_leviathan` |
| `docs/forge/output/BRIEF-0080-planche-quatre-vues.png` | dont une vue **de dessus** avant/après, annotée des quatre axes **dans le repère du jeu** |
| `docs/forge/output/BRIEF-0080-report.md` | rapport |

## Ce que le rapport doit prouver, par la mesure

1. **Les quatre angles, dans les DEUX repères** (fichier et jeu). Les quatre doivent viser le joueur
   en jeu, c'est-à-dire tomber dans [−160° ; −20°] **après** application de `FACING_PLAYER`.
2. **Les bouches sont au bout** : centre→`Spike_NN` < centre→`Muzzle_Spike_NN`, pour les quatre.
3. **Aucune interpénétration**, sur au moins 8 positions d'orbite plus l'état « plaque en chute »
   (bascule 135°, +1,8 m radial, −1,2·fall² vertical). Donner la marge minimale en millimètres.
4. **Budgets tenus** : triangles, matériaux, bbox.
5. **UV et tangentes** : 145/145.
6. **Déterminisme** : deux exécutions, même sha256.
7. **Preuve que `Spike_03` et `Spike_04` n'ont pas bougé** : hachage par maillage, comme en 0045.

## Provenance

Mettre à jour la ligne du `.glb` dans `assets/licenses/ASSET_PROVENANCE.csv` (le hash changera).
