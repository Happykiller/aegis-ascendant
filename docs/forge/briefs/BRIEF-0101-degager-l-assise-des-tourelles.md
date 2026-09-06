# BRIEF-0101 — Les greffes se sèment AUTOUR d'un affût, jamais dessus

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-06

## Objectif

Une tourelle du Long Cortège est **enfoncée dans le bordé** : son socle et le bas de son bloc
disparaissent sous une greffe. Rendre à `build_long_cortege.py` la règle qui existe déjà pour les
bastions — **rien de saillant sous une tourelle** — et régénérer la coque.

## Contexte

### Ce qui a été vu, et ce que la mesure explique

Trouvé en jouant le 2026-09-06 : « *il y a une tour qui se superpose sur un décor* ». En zoom, la
tourelle a la **couronne entièrement noyée** dans une dalle violette, et le bloc coupé à mi-hauteur.

La cause est une chaîne de trois faits qui sont chacun corrects :

1. **`turret_seat_y()` échantillonne la PEAU, pas les modules.** C'est écrit dans le fichier, et
   c'est voulu : l'assise d'un affût est le point le plus haut de son emprise *sur le bordé*.
2. **Les greffes se sèment sur les emprises de marqueur, délibérément** (`build_grafts` :
   « *c'est ce qui fait le groupe : une tourelle, et la machinerie autour* »).
3. **Une greffe monte de 0,70 à 1,05 m** depuis `BRIEF-0094`, contre 0,30 à 0,80 avant.

Il manque la quatrième : rien n'interdit à une greffe de se poser **sur le disque d'assise**
plutôt qu'autour. Le garde existe pour les bastions — « ⚠️ ET AUCUN SOUS UNE TOURELLE :
`turret_seat_y()` échantillonne la peau et non les modules, donc un affût posé sur un bastion
s'y enfoncerait de 1,20 m » — et il n'a jamais été étendu aux autres familles.

### Ce qu'une tourelle montre au-dessus de son assise

Relevé sur `turret_kit.glb` (le kit reforgé par `BRIEF-0100`), à l'échelle native :

| Pièce | Hauteur au-dessus de l'assise |
|---|---|
| `turret_pad` | **+0,27 m** |
| `turret_ring` | +0,40 m (0,04 de pose + 0,36) |
| `turret_body` | jusqu'à **+1,52 m** |

Une greffe de 0,70 à 1,05 m avale donc **le socle, la couronne, et les deux tiers du bloc**. Et un
massif de `build_plates` (0,34 m) suffit à enterrer le socle en entier.

## Ce qu'il faut faire

### 1. Un garde de dégagement, sur le modèle de ceux qui existent

`_one_graft()` rejette déjà contre trois choses : `_ambry_clash()`, `_bay_clash()` et
`_pit_clash()`. Il en faut une quatrième — **`_turret_clash()`** — et elle doit servir aux
**deux** familles qui montent du relief dans une emprise :

- `build_grafts()` — les masses de 0,70 à 1,05 m ;
- `build_plates()` — les massifs de 0,34 m (les tôles de 0,16 sont en dessous du socle : à
  arbitrer sur mesure, pas d'office).

⚠️ **La greffe ne doit pas DISPARAÎTRE de l'emprise, elle doit s'en écarter.** Tout l'intérêt de
`BRIEF-0094` est que la machinerie entoure l'installation ; une exclusion qui viderait l'emprise
rendrait le bordé plat, ce que ce brief-là avait corrigé. Si le rejet fait chuter le compte de
greffes, **décaler plutôt que rejeter** — et dire au rapport combien de greffes ont été déplacées
et combien perdues.

### 2. Le rayon d'exclusion : 2,50 m, et pas 2,08

`TURRET_FOOTPRINT_R = 2,08` est l'emprise de la classe **native**. Mais le moteur pose désormais
**trois classes** (`BRIEF-0100`), et la lourde est à l'échelle 1,200 : son emprise vaut **2,50 m**.

⚠️ **Le script de coque ne sait pas quelle classe va où** — c'est une décision de gameplay
(`cortege_hardpoints.gd`), et lui faire lire le moteur créerait une dépendance à l'envers. On
dégage donc **2,50 m partout**, la plus grande des trois. C'est aussi ce qui rend le résultat
robuste : re-classer une tourelle demain ne rouvrira pas ce défaut.

### 3. Ce que ce garde ne pourra PAS couvrir, et il faut le dire

Les **tourelles légères** ne sont pas des marqueurs : le moteur les pose à des décalages écrits
dans `cortege_hardpoints.gd` (table `BATTERIES`), que la forge ne voit pas. Une greffe peut donc
encore en enterrer une, et ce brief n'y peut rien. **Le signaler au rapport** plutôt que de faire
semblant ; l'arbitrage — remonter les décalages dans la forge, ou borner autrement — est une
décision de conception.

## Texture (ADR-0028)

**Aucune, et rien ne change.** Le Long Cortège est en PBR par facteurs, zéro image, et le harnais
d'audit échoue le build si une texture apparaît. Ce lot ne touche qu'au placement de volumes
existants. Le dépliage de la peau (`ak.box_project_uv()` à 0,200 tuile/m) est **inchangé** : les
faces déplacées le sont dans le même repère et gardent leur densité.

## Animation (ADR-0046 §6)

**La coque est figée, et elle doit le rester.** Le Long Cortège est un décor défilant : tout ce
qui bouge dessus — tourelles, ponts, nœuds d'épine, citadelle — est **posé par le moteur** sur des
marqueurs, et n'appartient pas à ce `.glb`. Aucune famille mobile, aucun pilote, aucune image clé.

⚠️ **Et les marqueurs ne bougent pas d'un millimètre.** `Turret_01..17`, `Bay_01..07`,
`Spine_01..05` gardent leurs positions exactes : le moteur les adresse par leur nom, et une
translation silencieuse déplacerait dix-sept tourelles, sept hangars et cinq nœuds sans qu'une
seule ligne de code ne change. C'est le premier critère d'acceptation.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_long_cortege.py` | le garde de dégagement, dans les deux familles |
| `assets/imported/models/backgrounds/long_cortege.glb` | la coque régénérée |
| `docs/forge/output/BRIEF-0101-report.md` | mesures, comptes avant/après, limites |

## Provenance

Mettre à jour **la ligne existante** `long_cortege_hull` de `assets/licenses/ASSET_PROVENANCE.csv`
(ne pas en créer une seconde : c'est une reforge, comme `BRIEF-0084` l'a fait). Y nommer le rayon
d'exclusion retenu, les comptes de greffes et de plaques avant/après, et le fait que les positions
de marqueurs sont inchangées.

## Critères d'acceptation

- [ ] **Les trente marqueurs sont aux mêmes positions**, au 1/10 de mm. Diff du contrat de noms
      (nœud, parent, position monde) **VIDE**. ⚠️ C'est le critère qui prime sur tous les autres :
      un marqueur déplacé casse silencieusement dix-sept tourelles.
- [ ] **Aucune géométrie au-dessus de la peau dans un disque de 2,50 m** autour de chacun des
      dix-sept `Turret_NN`. ⚠️ **Mesuré sur le binaire livré**, pas déduit du script : échantillonner
      la hauteur du maillage dans le disque et la comparer à l'assise. Un « le rejet est en place »
      n'est pas une réponse — c'est exactement ce que `turret_seat_y()` croyait déjà.
- [ ] **Le bordé n'est pas redevenu plat.** Compte de greffes et de plaques avant/après au rapport ;
      une chute de plus de 15 % demande un déplacement, pas une acceptation.
- [ ] `./scripts/build-hull.sh --check long_cortege` : **zéro octet divergent**, trois exécutions.
- [ ] **`TEXCOORD_0` compté** et **zéro image embarquée** — le harnais du cortège échoue sinon.
- [ ] Les harnais existants restent verts : jonction des tronçons, plafond de construction,
      dégagements pont/tourelle (`_pad_bay_clearances()`), zones calmes (`FREE_GAPS`).
- [ ] Le rapport dit **ce que le garde ne couvre pas** (les tourelles légères, voir §3).

## Hors périmètre

- **Toute retouche de forme** : ce lot déplace ce qui gêne, il ne redessine rien.
- **Les positions de marqueurs** — voir le premier critère.
- **Le code de jeu** : ne toucher à aucun `.gd`, `.tscn` ni `.tres`.
- **La citadelle** (`citadel_kit.glb`) : ses pièces sont posées par le moteur, et le dégagement de
  ses gardes vient d'être traité côté code.
