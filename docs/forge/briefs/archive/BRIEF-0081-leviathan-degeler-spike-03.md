# BRIEF-0081 — Dégeler l'azimut de `Spike_03` pour obtenir les quatre épines vers l'avant

- **Statut** : livré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-24
- **Suite de** : `BRIEF-0080` (non livré, à raison) — lire son rapport **avant** ce brief

## D'où vient ce brief

`BRIEF-0080` demandait de retourner `Spike_01` et `Spike_02` en gelant `Spike_03` et `Spike_04`.
La forge a livré la mesure et **opposé le seuil** : le retournement des deux fait tomber le jour
`Spike_02`↔`Spike_03` de 1 516 mm à 159 mm et l'écart angulaire minimal de 40,3° à 5,4°. Deux des
quatre membres se lisent alors comme un doublet parallèle. Refus juste, et la planche le montre.

Le rapport a identifié la vraie cause : **c'est `Spike_03`, gelée par le brief, qui bouche le
secteur dont `Spike_02` a besoin.** Le gel était une précaution de ma part, pas une contrainte de
conception. **Ce brief le lève** — c'est la piste 1 du §8 de `BRIEF-0080`.

## Objectif

Les **quatre** épines pointent vers le joueur **en jeu**, sans doublet parallèle.

Moyen proposé (tu peux en proposer un meilleur, chiffres à l'appui) : **reculer l'azimut de
`Spike_03` de 20 à 25°** — sa *position* autour de la coque — **sans dégrader son axe**, ce qui
rouvre le couloir de `Spike_02`, puis retourner `Spike_01` et `Spike_02`.

**Cible mesurable** : les quatre axes `Spike_NN → Muzzle_Spike_NN` dans **[−160° ; −20°] en jeu**,
c'est-à-dire [+20° ; +160°] dans le repère du fichier.

## ⚠️ Les deux repères, encore et toujours

`BossController` applique `FACING_PLAYER = Vector3(0, PI, 0)` (`scripts/bosses/boss_controller.gd:94`).
**Tout axe mesuré dans le `.glb` est vu retourné de 180° en jeu.** Donne les quatre angles dans les
DEUX repères, comme l'a fait `BRIEF-0080`. Convention du plan de jeu : `x = X`, `y = −Z`, le joueur
est à **−90°**.

Le contrôle d'instrument de 0080 (mesurer la coque du dépôt avant de la modifier, et retrouver
+68,7 / +109,0 / −120,7 / −68,5) est une bonne pratique : refais-le.

## ⚠️ Correction d'une donnée que 0080 a utilisée de bonne foi

Le §7 de ton rapport signale que deux conventions d'azimut de plaque coexistent, et que ton harnais
« plaque en chute » a dû en choisir une. **J'ai mesuré depuis, et c'est le CODE qui avait tort** —
il sera corrigé dans le même temps que ce brief.

Azimuts **réels** des plaques, composés depuis la racine du `.glb` (rayon 3,10 m, espacement 54°) :

| nœud | azimut réel (repère fichier, plan XZ) |
|---|---|
| `Plate_01` | **−152,0°** |
| `Plate_02` | **+154,0°** |
| `Plate_03` | **+100,0°** |
| `Plate_04` | **+46,0°** |

**Emploie ces valeurs** pour le harnais de dégagement « plaque en chute », et non `TAU·i/alive`. Les
plaques couvrent un **croissant de 198°**, pas un anneau : c'est conforme à `BRIEF-0041`, et le nom
`Shell_Crescent` le dit.

> ⚠️ **Correction, apportée après la livraison — cette section contenait une erreur de ma part.**
> J'y écrivais que les `PLATES` du script « sont des azimuts locaux à `Shell_Crescent`, pas des
> azimuts monde ». **C'est faux, et la forge l'a relevé.** Les valeurs que je donne ci-dessus
> (−152 / +154 / +100 / +46) sont exprimées en `atan2(Z, X)`, convention **miroir** du plan de jeu
> du projet (`x = X`, `y = −Z`). Ramenées dans ce plan, les mêmes plaques sont à
> **−28 / +26 / +80 / +134°** — c'est-à-dire, au dixième près, les `PLATES` du script.
> **`PLATES` EST le bon jeu d'azimuts.** Le seul faux était `base_angle = TAU·i/alive` du runtime,
> depuis corrigé (`fix(boss): la plaque qui brille est enfin celle qu'on peut toucher`).
>
> La leçon est la même que celle de `BRIEF-0045`, et je l'ai répétée en la citant : **des angles
> justes présentés sans leur repère ne valent rien.** J'ai donné une mesure exacte en la décrivant
> mal. Le livrable n'en a pas souffert — la forge a remesuré au lieu de me croire.

## Contraintes

### Ce qui NE DOIT PAS changer

- **Le contrat de noms**, à l'identique : `Shell_Ring`, `Shell_Crescent`, `Plate_01..04`,
  `Spike_01..04` (+ `_Mid`, `_Tip`), `Node_01..03`, `Core`, `Core_Center`, `Heart`, `Maw_Center`,
  `Maw_Lip`, `Muzzle_Spike_01..04`.
- **Les plaques, la coquille, le noyau, les nœuds** : aucune modification. Seules les épines bougent.
- **L'inégalité des épines** (longueurs différentes, `Spike_04` est un moignon de 2,68 m) et
  l'asymétrie générale — silhouette validée par `BRIEF-0041`.
- **Budgets** : ≤ 30 000 triangles, `AA_Hull` ≥ 30 %, `AA_Emissive_Engine` ≤ 8 %, `AA_Greeble` ≤ 20 %.
- **UV et tangentes sur 145/145 surfaces** — la coque est la seule du dépôt à les avoir toutes.
- **Déterminisme** : `./scripts/build-hull.sh pale_leviathan` (force `-t 1`), deux exécutions
  rendent un `.glb` byte-identique (`ADR-0008`).
- **Le mât suit sa racine.** `_build_masts()` relit `root` pour poser le mât : si tu bouges la racine
  de `Spike_03`, le mât doit suivre. Ton rapport l'avait noté pour `Spike_02`.
- **`Muzzle_Spike_NN` reste au bout** de son épine (centre→`Spike_NN` < centre→`Muzzle_Spike_NN`).

### Le seuil, posé AVANT la mesure

Références mesurées par `BRIEF-0080`, sur lesquelles ces bornes sont calées :

| | dépôt | V1 (0080) | V2 refusée (0080) |
|---|---|---|---|
| jour minimal entre voisines | 1 516 mm | 1 029 mm | **159 mm** |
| écart angulaire minimal | 40,3° | 23,4° | **5,4°** |
| largeur de coque | 11,031 m | 11,029 m | **11,311 m** |

**Ne livre pas si l'un de ces trois seuils est franchi :**

1. **jour minimal entre deux épines voisines < 800 mm** ;
2. **écart angulaire minimal < 20°** (0045 avait accepté 26,8° ; en dessous de 20° on retombe vers
   le doublet) ;
3. **largeur de coque > 11,15 m** — le contrat dit 11,00 et V2 vivait à 94 % de sa tolérance. Si tu
   as besoin de plus, **dis-le et chiffre-le** plutôt que de le prendre.

Si les quatre épines vers l'avant sont **inatteignables** dans ces bornes, **ne livre pas** : rends
le meilleur compromis chiffré (y compris « V1 de 0080 reste le meilleur »), et dis lequel des trois
seuils bloque. Une coque cohérente à 3/4 vaut mieux qu'une coque incohérente à 4/4 — c'est le même
seuil qu'en 0080, et tu as eu raison de l'opposer.

### La provision de braquage à ±40°

Ton §6 a établi qu'elle est **le seul obstacle à des épines planes** (sans elle : 277,8 / 185,7 mm,
mieux que la coque actuelle) et qu'elle ne cause **pas** le refus de 0080 — jour, éventail et
largeur sont des grandeurs planes.

Elle n'a toujours aucune contrepartie dans le code (`_spine_track` et `SPINE_TRACK_DEG` supprimés),
mais l'opérateur veut des tentacules animées : **garde-la si elle ne coûte rien**. Si elle est le
seul obstacle à tenir les trois seuils, **donne les deux variantes chiffrées** (avec et sans) et
laisse-moi trancher — ne paye pas une arche pour une porte que rien ne franchit.

⚠️ Ton §8.3 note qu'à 159 mm deux voisines braquées de 40° se traversent, et que rien ne le
signale. Si tu gardes la provision, **mesure les épines entre elles sous braquage**, pas seulement
au repos.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_pale_leviathan.py` | seules les définitions d'épines changent |
| `assets/imported/models/bosses/pale_leviathan.glb` | régénérée par `./scripts/build-hull.sh pale_leviathan` |
| `docs/forge/output/BRIEF-0081-planche-quatre-vues.png` | vue de dessus avant/après annotée des quatre axes **dans le repère du jeu**, plus quatre vues |
| `docs/forge/output/BRIEF-0081-report.md` | rapport |

## Ce que le rapport doit prouver, par la mesure

1. **Les quatre angles, dans les DEUX repères**, avant et après. Les quatre dans [−160° ; −20°] en jeu.
2. **Les trois seuils** ci-dessus, chiffrés, avec la comparaison au dépôt et à V1.
3. **Les bouches sont au bout**, pour les quatre.
4. **Aucune interpénétration** : épines entre elles, épines contre la coquille, et **plaque en chute
   contre épine** — avec les azimuts réels donnés plus haut. Marge minimale en millimètres.
5. **Budgets tenus** : triangles, matériaux, bbox.
6. **UV et tangentes** : 145/145.
7. **Déterminisme** : deux exécutions, même sha256.
8. **Preuve que rien d'autre n'a bougé** : hachage par maillage (plaques, coquille, noyau, nœuds).

## Provenance

Mettre à jour la ligne du `.glb` dans `assets/licenses/ASSET_PROVENANCE.csv` (le hash changera), et
ajouter la ligne de la planche.
