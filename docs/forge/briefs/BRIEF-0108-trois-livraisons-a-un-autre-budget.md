# BRIEF-0108 — Trois livraisons tierces à faire entrer : pylône, conduite, flexible

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-08

## Objectif

Rendre **jouables** trois pièces livrées par l'agent tiers le 2026-09-08. Elles sont justes de
cotes, riches d'animations, propres de contrat — et **elles ne peuvent pas entrer en l'état**.

C'est exactement la situation du `BRIEF-0105`, et sa leçon vaut ici : *ce n'est pas une livraison
ratée, c'est une livraison à un autre budget.*

## L'audit, mesuré sur les binaires

Source : `~/aegis-ascendant_gpt_models/`.

| Pièce | Triangles | Cotes (m) | Clips | Repères `CTRL` | Images |
|---|---|---|---|---|---|
| `pylone-technique/Stern_Pylon_01.glb` | **88 504** (12 sous-pièces) | 12 × **24** × 9 | Service, Refroidissement, Maintenance | 25 | 13 |
| `conduite-energetique/conduit_droit.glb` | **21 284** | 1,60 × 1,41 × 3,85 | Actif, Endommagé, Rupture, Rompu | 39 | 11 |
| `conduite-energetique/conduit_coude.glb` | **13 400** | idem | idem | idem | 8 |
| `flexible-technique/flexible_droit.glb` | **25 028** | 0,84 × 0,87 × 2,84 | Intact, Endommagé, Rupture, Rompu | 81 | 13 |
| `flexible-technique/flexible_coude.glb` | **25 028** | idem | idem | idem | 13 |

Pour mémoire : **le corridor entier — 500 m de coque, cinq tronçons, trente marqueurs — fait
49 458 triangles.** Un seul flexible droit en fait la moitié.

⚠️ **`bras-ancrage` et `ancrage-destructible` du même dossier ne sont PAS de cette livraison.**
Chiffres identiques à l'octet près à l'audit du `BRIEF-0105` (66 332 et 54 640), datés du 6 : ils
sont déjà réduits et intégrés sous `stern_arm.glb` et `stern_anchor.glb`. Ne pas y toucher.

## Ce qui est DÉCIDÉ, et qui commande le lot

L'opérateur a tranché deux choses le 2026-09-08 :

1. **Le pylône est RECONSTRUIT à la taille de son emplacement**, pas mis à l'échelle.
2. **La conduite et le flexible deviennent des CIBLES DESTRUCTIBLES** sur l'artère du corridor —
   pas du décor. Leurs quatre clips `Intact / Endommagé / Rupture / Rompu` sont la mécanique.

## Ce qu'il faut faire

### 1. ⚠️ LE PYLÔNE SE RECONSTRUIT, IL NE SE MET PAS À L'ÉCHELLE

Il fait **24 m de haut**. Son emplacement sur la poupe — les étagères de rive, entre la coque et
le plafond de construction (`CEILING_Y = −3,20`) — en offre **5,3**.

⚠️ **UN FACTEUR 0,22 TUE LE DÉTAIL, ET C'EST MESURABLE.** Le pont de poupe rend à **32,7 px/m** :
un boulon de 3,5 cm y fait déjà 1,1 pixel à l'échelle 1 ; réduit de 0,22 il tombe à **0,25 px**.
On paierait 88 504 triangles pour du bruit.

Reconstruisez-le depuis son script (`v1/scripts/build.py`, `v1/work/topology.py`, le `.blend` est
là aussi) **à 5,3 m**, en SUPPRIMANT ce qui n'existerait plus à cette taille au lieu de le
rétrécir. Ce qui doit survivre :

- la **silhouette** — c'est elle qu'on reconnaît, et c'est tout ce qui portera à 32,7 px/m ;
- les **trois clips** (`Service`, `Refroidissement`, `Maintenance`) ;
- les **arêtes qui prennent la lumière**, et rien de ce que le fût cache.

**Cible : ≤ 3 200 triangles.** Repère : la carène de poupe entière en fait 3 182, et il y a
**quatre** pylônes → 12 800 pour les quatre, sur les **16 798** qui restent du budget de 80 000
de la poupe (63 202 consommés aujourd'hui).

### 2. La conduite et le flexible : réduits POUR ÊTRE RÉPÉTÉS

Ce ne sont pas des pièces uniques : elles se poseront en série le long des 500 m. **C'est la
quantité qui décide du budget, pas la pièce.**

| Pièce | Cible unitaire | Pourquoi |
|---|---|---|
| conduite (droite et coudée) | **≤ 700** | c'est la CIBLE : elle a droit à plus que ce qui l'accompagne |
| flexible (droit et coudé) | **≤ 350** | il habille la liaison, il ne se vise pas |

⚠️ **CE QUI DISPARAÎT EN PREMIER EST CE QUI NE SE VOIT PAS.** Le dépôt a déjà payé cette leçon
deux fois (`BRIEF-0089`, `BRIEF-0105`) : coupez la visserie, les congés, les bagues internes,
tout ce que la gaine cache. Gardez la silhouette et les pièces MOBILES.

⚠️ **ET LES PIÈCES MOBILES NE SE DÉCIMENT PAS COMME LE RESTE.** Les 81 repères du flexible et les
39 de la conduite portent des brins, des câbles et des colliers qui s'animent : décimés trop, ils
s'aplatissent et le mouvement disparaît avec. Traitez-les à part, plus généreusement, et **dites
ce qu'ils coûtent**.

### 3. ⚠️ LES QUATRE CLIPS SONT LA MÉCANIQUE, PAS UNE DÉCORATION

`Intact → Endommagé → Rupture → Rompu` est le contrat d'une pièce destructible, et c'est
exactement ce que `CortegeAnchor` fait déjà avec ses quatre états. Ils doivent être **cuits en
clés** dans le binaire réduit (`ADR-0046` : un glTF n'exécute pas les drivers Blender) et rejoués
après réimport.

⚠️ **La pose finale de `Rupture` EST le début de `Rompu`.** Cette continuité doit survivre à la
réduction, sinon la pièce saute d'une pose à l'autre à l'instant précis où le joueur regarde.

### 4. Le contrat de matériaux — ⚠️ SANS LUI RIEN NE PEUT S'ÉTEINDRE

Les slots livrés se replient sur les cinq du kit, comme au `BRIEF-0105` :

| Slots livrés | Slot du jeu |
|---|---|
| `01 Anthracite blindé`, `02 Acier gris usé`, `03 Tranches acier brossé` | `AA_Hull` |
| `04 Cavités graphite`, `05 Conduites noires`, `09 Vis et raccords`, `11 Conduite sombre` | `AA_Greeble` |
| `10 Carbone technique`, `10 Gaine tressée référence 06` | `AA_Panel` |
| **`06 Énergie magenta`** | **`AA_Emissive_Engine`** |

⚠️ **TROIS SLOTS SONT NEUFS** (`10 Carbone technique`, `11 Conduite sombre`, `10 Gaine tressée`) :
ils n'étaient pas dans la table du `BRIEF-0105`. Le repli proposé ci-dessus est une décision du
concepteur — si le rendu le dément, **dites-le au lieu de le suivre**.

⚠️ **`CortegeSkin` RECONNAÎT SON ÉMISSIF PAR SON NOM.** Une veine peinte dans un autre slot
resterait allumée sur un vaisseau mort, et **rien ne le signalerait** — ni erreur, ni test. C'est
le défaut nommé au `BRIEF-0103` et le blackout du niveau en dépend.

## Texture (ADR-0028)

**Aucune.** Le Long Cortège entier est en PBR par facteurs, zéro image, et son harnais échoue le
build si une texture apparaît. Les trois pièces arrivent avec 8 à 13 atlas chacune : elles se
replient sur les facteurs, comme les quatre du `BRIEF-0105`.

**Dépliage** : projection en boîte à la densité de la peau du corridor. `TEXCOORD_0` compté.

## Animation (ADR-0046 §6)

**Conservée, et c'est un critère.** Onze clips au total.

## Provenance et source (ADR-0048)

Les trois arrivent **avec leur `.blend` et leurs scripts** — le contrat est donc satisfaisable
d'emblée, contrairement au `BRIEF-0105`. Versez les sources sous `assets/source/models/` et une
ligne par binaire dans `assets/licenses/ASSET_PROVENANCE.csv`, créditant l'agent tiers pour la
géométrie et la forge pour la réduction.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `assets/imported/models/backgrounds/stern_pylon.glb` | le pylône, reconstruit à 5,3 m |
| `assets/imported/models/backgrounds/artery_conduit.glb` | la conduite droite, réduite |
| `assets/imported/models/backgrounds/artery_conduit_bend.glb` | la conduite coudée |
| `assets/imported/models/backgrounds/artery_hose.glb` | le flexible droit |
| `assets/imported/models/backgrounds/artery_hose_bend.glb` | le flexible coudé |
| `assets/source/models/artery/` | les `.blend`, scripts et harnais de réduction |
| `docs/forge/output/BRIEF-0108-report.md` | mesures avant/après, pièce par pièce et par famille |
| `docs/forge/output/BRIEF-0108-planche.png` | rendus à la caméra du jeu |

## Critères d'acceptation

- [ ] **Cibles tenues** : pylône ≤ 3 200 ; conduite ≤ 700 ; flexible ≤ 350. Le rapport donne le
      compte **par pièce et par famille**, avant et après.
- [ ] **Le pylône est RECONSTRUIT, pas mis à l'échelle** : le rapport dit ce qui a été supprimé et
      pourquoi ça n'existait plus à 5,3 m. Une simple mise à l'échelle est un échec du lot.
- [ ] **Les repères `CTRL | ` sont inchangés**, au 1/10 de mm, diff du contrat de noms **VIDE**
      pour la conduite et le flexible. Pour le pylône reconstruit, la liste des repères
      supprimés est **nommée**.
- [ ] **`AA_Emissive_Engine` porte tout ce qui doit s'éteindre**, compté sur le binaire.
- [ ] **Les onze clips se rejouent après import**, y compris la continuité `Rupture` → `Rompu`.
- [ ] **Zéro image embarquée**, `TEXCOORD_0` sur toutes les primitives.
- [ ] **Déterminisme** : trois exécutions, zéro octet divergent.
- [ ] **Rendu et REGARDÉ à la caméra du jeu** (`ADR-0006`), aux **quatre états** de la conduite et
      du flexible. ⚠️ `Rompu` est celui que personne ne pense à regarder, et c'est celui que le
      joueur verra le plus longtemps — une fois qu'il a tiré, la pièce reste comme ça.
- [ ] **Ce qui n'a pas pu être réduit sans perdre**, nommé. Un budget dépassé avec sa raison est
      un résultat ; un budget dépassé en silence n'en est pas un.

## Hors périmètre

- **Le code de jeu.** La mécanique des conduites destructibles fait l'objet d'un plan séparé :
  ne toucher à aucun `.gd`, `.tscn` ni `.tres`.
- **Le placement.** Combien de conduites, où, et sur quels tronçons — c'est une décision de
  conception, pas de forge. Vous livrez des pièces, pas une pose.
- **`bras-ancrage` et `ancrage-destructible`** : déjà intégrés au `BRIEF-0105`.
