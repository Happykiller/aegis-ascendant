# BRIEF-0105 — La poupe entre dans le budget : réduire quatre livraisons tierces

- **Statut** : à faire
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-06

## Objectif

Rendre **jouables** les quatre pièces livrées par l'agent tiers pour la phase finale du niveau 2.
Elles sont justes de cotes, riches d'animations et propres de contrat — et **elles ne peuvent pas
entrer dans le jeu en l'état**.

## Contexte

### L'audit, mesuré sur les binaires

```
groupe_moteur_principal.glb   70,4 Mo   1 300 maillages   276 816 triangles   11 images   3 clips
berceau_moteur.glb            64,9 Mo     968 maillages   157 104 triangles   11 images   4 clips
ancrage_destructible.glb      59,4 Mo     300 maillages    54 640 triangles   11 images   5 clips
bras_ancrage.glb (+ miroir)   60,1 Mo       —              66 332 triangles   11 images   6 clips
```

Aux quantités que la phase demande — **3 moteurs, 3 berceaux, 10 ancrages, ~20 bras** :

> ⚠️ **3 170 000 triangles et près d'un gigaoctet.** Pour mémoire, `long_cortege.glb` — les
> 500 mètres de coque, cinq tronçons, trente marqueurs — en fait **49 458**. C'est
> **soixante-quatre fois tout le niveau**.

Ce n'est pas une livraison ratée : c'est une livraison **à un autre budget**. La géométrie est
bonne, les cotes sont celles des planches, le contrat de mariage est écrit au millimètre. Tout ce
lot consiste à la faire entrer.

### Ce qui est DÉJÀ en place côté jeu, et qu'il ne faut pas casser

La phase est **entièrement jouable en boîtes grises** (LOTS 1 à 4 et 8, plan
`2026-09-06-arrachement-des-moteurs`). Les cotes du jeu sont **dérivées de vos repères** :

| Cote de jeu | Valeur | D'où elle vient |
|---|---|---|
| `asset_scale` | **0,870** | la portée de l'ancrage : `entraxe + 3,700 × k ≤ 13,6` |
| `engine_spacing` | 10,28 | berceaux presque jointifs, `11,19 k (1+1,06)/2 + 0,25` |
| `deck_y` | −11,85 | le sommet du groupe passe sous le plafond de vol (−2,40) |
| `hold_plane_y` | 6,47 | les deux rangées d'ancrages dans le cadre |
| assise du moteur | (0 ; 3,70 ; −1,00) | **votre contrat de mariage**, converti en Y-up |

⚠️ **Ces cinq valeurs vivent dans `resources/levels/long_cortege_stern.tres` et ne sont pas à
toucher.** Si la réduction change une cote, c'est la Resource qui suit — jamais l'inverse.

## Ce qu'il faut faire

### 1. ⚠️ LA RÉDUCTION, ET C'EST LE LOT

**Budget total de la poupe : 80 000 triangles**, toutes pièces et toutes quantités confondues.
C'est déjà une fois et demie le niveau entier ; au-delà, la phase coûte plus cher que les 500 m
qu'elle conclut.

| Pièce | livré | quantité | cible unitaire | total |
|---|---|---|---|---|
| groupe moteur | 276 816 | ×3 | **≤ 8 000** | 24 000 |
| berceau | 157 104 | ×3 | **≤ 6 000** | 18 000 |
| ancrage | 54 640 | ×10 | **≤ 900** | 9 000 |
| bras d'ancrage | 66 332 | ×20 | **≤ 500** | 10 000 |
| | | | **marge** | 19 000 |

⚠️ **CE QUI DISPARAÎT EN PREMIER EST CE QUI NE SE VOIT PAS À 45,8 px/m.** Un boulon de 3 cm fait
**1,4 pixel**. Une bague de 8 cm en fait 3,7. Le dépôt a déjà payé cette leçon sur 500 m de coque
(`BRIEF-0089`) : « le détail perçu vient des textures, pas des triangles ». Coupez la
visserie, les congés, les bagues internes et tout ce que le fût cache ; gardez la **silhouette**,
les arêtes qui prennent la lumière, et les pièces MOBILES.

⚠️ **ET LES PIÈCES MOBILES NE SE DÉCIMENT PAS COMME LE RESTE.** Une mâchoire, un piston, un
pétale de tuyère porte une animation : le décimer trop l'aplatit et le mouvement disparaît avec.
Traitez-les à part, plus généreusement, et dites combien de triangles ils vous coûtent.

### 2. Le contrat de matériaux — ⚠️ SANS LUI RIEN NE PEUT S'ÉTEINDRE

Vos neuf slots (`01 | Anthracite blinde`, `06 | Energie magenta`, `07 | Coeur plasma`…) doivent
se replier sur les cinq du kit :

| Vos slots | Slot du jeu |
|---|---|
| Anthracite blindé, Acier gris usé, Tranches acier brossé | `AA_Hull` |
| Cavités graphite, Conduites noires, Vis et raccords | `AA_Greeble` |
| — les liserés clairs, s'il y en a | `AA_Trim` |
| — les volumes de faction | `AA_Panel` |
| **Énergie magenta, Cœur plasma, Balises rouges** | **`AA_Emissive_Engine`** |

⚠️ **`CortegeSkin` RECONNAÎT SON ÉMISSIF PAR SON NOM.** Une veine peinte dans un autre slot
resterait allumée sur un vaisseau mort, et **rien ne le signalerait** — ni erreur, ni test. C'est
le défaut que `BRIEF-0103` a déjà nommé, et il coûte ici l'image finale du niveau : le blackout
du LOT 8 ne prendrait pas.

### 3. Le contrat de noms — ⚠️ LES REPÈRES `CTRL | ` NE BOUGENT PAS D'UN DIXIÈME DE MILLIMÈTRE

C'est le meilleur de votre livraison et c'est ce sur quoi le jeu s'appuie :

- berceau : `CTRL | Socket ancrage AV/AR D/G`, `Socket VFX rupture …`, `Socket puissance …`,
  `Verrou …` ;
- moteur : `CTRL | Socket ancrage arriere / droit / gauche`, `Anneau emissif`, `Petale NN` ;
- ancrage : `CTRL | VFX impact`, `VFX rupture D/G`, `Montage berceau`, `Contact moteur` ;
- bras : `CTRL | Patin contact`, `Machoire mobile`, `VFX rupture`, `VFX pivot`.

Le moteur les adresse par leur nom. Une translation silencieuse déplacerait dix verrous et vingt
sockets d'effets sans qu'une ligne de code ne change.

### 4. Les clips restent, et voici à quoi ils servent

| Pièce | clip | état du jeu |
|---|---|---|
| moteur | `Fonctionnement` | `ACTIVE` |
| | `Endommage` | `DAMAGED_1` / `DAMAGED_2` |
| | `Detachement` | `DETACHING` |
| berceau | `Intact` | tant que le moteur tient |
| | `Sous_contrainte` | `DAMAGED_2` |
| | `Liberation` | `DETACHING` |
| | `Berceau_vide` | après le départ — c'est l'image du silence final |
| ancrage | `Intact` / `Endommage` / `Rompu` | ses trois états visuels |
| | `Ouverture` / `Fermeture` | le verrouillage du moteur central |
| bras | les six | idem |

⚠️ **UN glTF N'EXÉCUTE PAS LES DRIVERS BLENDER** (`ADR-0046`). Vérifiez que les clés sont
**cuites** dans le binaire réduit, et jouez-les après réimport.

### 5. L'arbitrage de la texture (décision D4 du plan)

Le Long Cortège est en **PBR par facteurs, zéro image**, et son harnais échoue le build si une
texture apparaît. Vos pièces arrivent avec **onze atlas chacune**.

⚠️ **NE TRANCHEZ PAS : RENDEZ LA COMPARAISON.** Livrez les deux versions et **une capture du même
cadrage**, à la caméra du jeu, côte à côte. L'opérateur décide en regardant (`ADR-0006`). Dites
aussi ce que coûte l'option texturée en mégaoctets de LFS.

## Texture (ADR-0028)

**Aucune à produire.** Soit on garde vos atlas tels quels (option A de l'arbitrage), soit on
repasse en PBR par facteurs comme le reste du niveau (option B). Aucune image nouvelle.

## Animation (ADR-0046 §6)

**Conservée, et c'est un critère.** Dix-huit clips au total, cuits en clés, rejoués après import.
⚠️ La pose finale de `Liberation` **est** le début de `Berceau_vide` : cette continuité doit
survivre à la réduction, sinon le berceau saute d'une pose à l'autre à l'instant où le joueur
regarde le plus attentivement.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `assets/imported/models/backgrounds/stern_engine.glb` | le groupe moteur, réduit |
| `assets/imported/models/backgrounds/stern_cradle.glb` | le berceau, réduit |
| `assets/imported/models/backgrounds/stern_anchor.glb` | l'ancrage destructible, réduit |
| `assets/imported/models/backgrounds/stern_arm.glb` | le bras (et son miroir si nécessaire) |
| `assets/source/models/stern/` | les `.blend` sources et les scripts de réduction (`ADR-0048`) |
| `docs/forge/output/BRIEF-0105-report.md` | mesures avant/après, pièce par pièce |
| `docs/forge/output/BRIEF-0105-arbitrage-texture.png` | les deux versions, même cadrage |

## Provenance

Une ligne par binaire dans `assets/licenses/ASSET_PROVENANCE.csv`, créditant l'agent tiers comme
auteur de la géométrie et la forge comme auteur de la réduction. `ADR-0048` s'applique : un
modèle tiers entre **avec sa source**.

## Critères d'acceptation

- [ ] **Budget tenu : ≤ 80 000 triangles** pour la poupe entière, aux quantités du jeu. Le
      rapport donne le compte **par pièce et par famille**, avant et après.
- [ ] **Les repères `CTRL | ` sont inchangés**, au 1/10 de mm, diff du contrat de noms **VIDE**.
      C'est le critère qui prime : le jeu les adresse par leur nom.
- [ ] **`AA_Emissive_Engine` porte tout ce qui doit s'éteindre**, compté sur le binaire.
      ⚠️ Sans ça le blackout du LOT 8 ne prend pas, et **rien ne le dira**.
- [ ] **Les dix-huit clips sont là et se rejouent après import**, y compris la continuité
      `Liberation` → `Berceau_vide`.
- [ ] **Les pièces mobiles sont traitées à part**, et le rapport dit ce qu'elles coûtent.
- [ ] `./scripts/build-hull.sh --check` équivalent : **zéro octet divergent, trois exécutions**.
- [ ] **Rendu et REGARDÉ à la caméra du jeu** (`ADR-0006`), aux quatre états qui comptent :
      moteur intact, moteur endommagé, arrachement en cours, **berceau vide**. Le dernier est
      celui que personne ne pense à regarder, et c'est l'image qui clôt le niveau.
- [ ] **La capture d'arbitrage de la texture**, deux versions au même cadrage, avec le coût LFS.
- [ ] **Ce qui n'a pas pu être réduit sans perdre**, nommé. Un budget dépassé avec sa raison est
      un résultat ; un budget dépassé en silence n'en est pas un.

## Hors périmètre

- **Le code de jeu.** La phase est jouable et testée (957 tests) : ne toucher à aucun `.gd`,
  `.tscn` ni `.tres`. Les cotes du jeu suivront vos mesures, elles ne les précèdent pas.
- **La géométrie de poupe elle-même** (le pont qui porte les trois groupes) : c'est le LOT 6.
- **Toute reprise de silhouette.** Les planches ont été validées, les cotes sont bonnes. On
  réduit, on ne redessine pas.
