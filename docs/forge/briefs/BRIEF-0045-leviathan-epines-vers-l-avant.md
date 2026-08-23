# BRIEF-0045 — Retourner deux épines du Pale Leviathan vers l'avant

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-23

## Objectif

Réorienter **`Spike_03` et `Spike_04`** de la coque du Pale Leviathan pour qu'elles pointent vers
l'**avant** du boss (côté joueur), comme le font déjà `Spike_01` et `Spike_02`. Tout le reste de la
coque est **conservé à l'identique**.

⚠️ **Ce n'est PAS une reforge.** La silhouette est validée (`BRIEF-0041`, `ADR-0014`) et le contrat
d'export passe. On corrige l'orientation de deux pièces sur trente maillages.

## Contexte

Les épines sont devenues des **tourelles laser** (`ADR-0021`) : chacune télégraphie puis tire, et
chaque plaque d'armure brisée en éteint une. Le playtest a rejeté le résultat — *« les lasers qui
devaient partir des tentacules, ça n'a pas de sens ; là ça sort d'un peu n'importe où, ça manque de
cohésion »*.

La cause a été **mesurée** dans le `.glb` livré, en composant les translations parent→enfant du
glTF. Angles de l'axe `Spike_NN` → `Muzzle_Spike_NN`, projetés dans le plan de jeu (x = X, y = −Z).
**Le joueur est à −90°** :

| Épine | axe dans le plan | angle | verdict |
|---|---|---|---|
| `Spike_01` | (−0,89 ; −2,29) | **−111,3°** | pointe vers le joueur — **à conserver** |
| `Spike_02` | (+0,73 ; −2,13) | **−71,0°** | pointe vers le joueur — **à conserver** |
| `Spike_03` | (+0,92 ; +1,54) | **+59,3°** | pointe vers l'**arrière** — à retourner |
| `Spike_04` | (−0,49 ; +1,24) | **+111,5°** | pointe vers l'**arrière** — à retourner |

Un faisceau qui prolonge l'axe d'une épine tournée vers l'arrière part à l'opposé de sa cible. Le
code compense aujourd'hui en tirant depuis la pointe **mais vers le joueur**, ce qui se lit comme
une incohérence : la pièce montre une direction, le tir en prend une autre.

## Contraintes

### IP

Rien de nouveau : aucun nom, silhouette ou élément identifiable d'une licence tierce. La coque du
Leviathan est originale et le reste.

### Ce qui NE DOIT PAS changer

- **Le contrat de noms**, à l'identique : `Shell_Ring`, `Shell_Crescent`, `Plate_01..04`,
  `Spike_01..04` (+ `_Mid`, `_Tip`), `Node_01..03`, `Core`, `Core_Center`, `Heart`, `Maw_Center`,
  `Maw_Lip`, `Muzzle_Spike_01..04`. Le code du combat les résout par nom.
- **`Spike_01` et `Spike_02`** : orientation, longueur, courbure — inchangées.
- **L'inégalité des épines** (`Spike_01` ≈ 5,81 m de corde contre `Spike_04` bien plus courte) et
  l'asymétrie générale : c'est la silhouette validée par `BRIEF-0041`.
- **Budgets** : ~27 710 triangles (plafond 30 000), répartition matériaux `AA_Hull` ≥ 30 %,
  `AA_Emissive_Engine` ≤ 8 %, `AA_Greeble` ≤ 20 %.
- **UV et tangentes sur 145/145 surfaces** — la coque est la seule du dépôt à les avoir toutes, ne
  pas les perdre. ⚠️ Sans `_triangulate_ngons()` l'exporteur glTF abandonne les tangentes en
  silence, et sans dépliage les UV n'existent pas du tout.
- **Déterminisme** : passer par `./scripts/build-hull.sh` (force `-t 1`), deux exécutions doivent
  rendre un `.glb` byte-identique (`ADR-0008`, `howto-determinisme-des-coques.md`).

### Ce qui doit changer

- `Spike_03` et `Spike_04` : axe `base → Muzzle` dans le **demi-plan avant**, soit un angle dans
  **[−160° ; −20°]** avec la convention ci-dessus. Viser une répartition qui garde la coque
  asymétrique — ne pas produire un miroir exact de `Spike_01`/`Spike_02`.
- Les `Muzzle_Spike_03` et `Muzzle_Spike_04` suivent leur épine et **restent au bout** (la bouche
  doit rester le point le plus éloigné du corps, sur l'axe de la pièce).
- La **bbox** peut bouger : elle est aujourd'hui 11,03 × 3,16 × 14,00 m. Rester sous **12,0 × 3,4 ×
  15,0** ; si la contrainte oblige à dépasser, le dire plutôt que de raccourcir une épine.

## ⚠️ Le seuil, posé AVANT la mesure

**Si retourner ces deux épines dégrade la silhouette validée** — perte de l'asymétrie, épines qui
mordent la coquille ou les plaques, croisement de pièces, encombrement du dégagement des plaques —
**dis-le et ne livre pas.** Une coque cohérente avec deux épines mal orientées vaut mieux qu'une
coque incohérente dont les quatre épines pointent bien.

Vérifier explicitement l'**interpénétration** : `Spike_03`/`Spike_04` retournées ne doivent croiser
ni `Shell_Ring`, ni `Shell_Crescent`, ni aucune `Plate_NN` **dans toutes les positions d'orbite de
la coquille** (elle tourne, période 9 s) ni pendant la chute d'une plaque (bascule ~135° vers
l'extérieur, écartement 1,8 m).

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_pale_leviathan.py` | script modifié — **seules** les définitions de `Spike_03` et `Spike_04` changent |
| `assets/imported/models/bosses/pale_leviathan.glb` | coque régénérée par `./scripts/build-hull.sh pale_leviathan` |
| `docs/forge/output/BRIEF-0045-planche-quatre-vues.png` | planche de recette, dont une vue **de dessus** où les quatre axes d'épines se lisent |
| `docs/forge/output/BRIEF-0045-report.md` | rapport (voir ci-dessous) |

## Ce que le rapport doit prouver, par la mesure

1. **Les quatre angles après reforge**, avec la même convention que le tableau ci-dessus. Les quatre
   doivent tomber dans [−160° ; −20°].
2. **Les bouches sont au bout** : distance centre→`Spike_NN` et centre→`Muzzle_Spike_NN`, la seconde
   strictement plus grande, pour les quatre.
3. **Aucune interpénétration**, testée sur au moins 8 positions d'orbite réparties sur le tour, plus
   l'état « plaque en chute ». Donner la marge minimale en millimètres.
4. **Budgets tenus** : triangles, répartition des trois matériaux, bbox.
5. **UV et tangentes** : 145/145 surfaces, ou le compte réel s'il change avec la géométrie.
6. **Déterminisme** : deux exécutions, même sha256.

⚠️ **Mesurer chaque point, ne pas le déduire.** Le contrat d'export de ce projet vérifie bbox,
triangles, matériaux, pivot et attaches — **aucune de ces cinq mesures ne parle de la forme**, et
une coque a déjà passé le contrat en ne ressemblant pas à ses planches
(`.claude/resources/pratique-revue-asset.md`).

## Provenance

Coque dérivée de l'existant, produite par script Blender versionné. Mettre à jour la ligne du
`.glb` dans `assets/licenses/ASSET_PROVENANCE.csv` si le hash change (il changera).
