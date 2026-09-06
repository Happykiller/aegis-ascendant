# BRIEF-0101 — compte-rendu : les greffes se sèment AUTOUR d'un affût

- **Brief** : `docs/forge/briefs/BRIEF-0101-degager-l-assise-des-tourelles.md`
- **Date** : 2026-09-06 — `asset-forge`
- **Livrables** : `tools/blender/build_long_cortege.py`,
  `assets/imported/models/backgrounds/long_cortege.glb`, ce fichier.
- **Empreinte du binaire** : `sha256 9e846c7c2c764aa8550e26113bdfa0f64590d0d2e8d441a9be0d9915dd919142`
  (2 530 944 octets, 46 770 triangles, 27/27 primitives avec `TEXCOORD_0`, 0 image embarquée).

---

## 1. La garde, et le critère qu'elle applique

`_turret_clash()` rejoint `_ambry_clash()`, `_bay_clash()` et `_pit_clash()`, au même
endroit et dans le même style. Elle sert **quatre** familles, et non deux :

| Famille | Hauteur | Ce qu'elle fait quand la garde parle |
|---|---|---|
| `build_grafts()` | 0,70 à 1,05 m | **s'écarte** dans son emprise (`_graft_place`, 49 places d'essai) |
| `build_plates()` | 0,16 et 0,34 m | **se décale** de ±1,5 m au plus (`_plate_place`) |
| `build_ribs()` | 0,32 et 0,45 m | **s'éloigne** de son installation, jusqu'à 2,0 m (`RIB_NUDGES`) |
| `build_pips()` | 0,05 m | est retirée — un feu de 0,50 m n'a pas de groupe à tenir |

Le brief n'en nommait que deux. Les deux autres sont là parce que le **critère
d'acceptation se mesure sur tout le maillage du disque**, pas sur deux familles : une
nervure de 0,45 m laissée en place aurait rendu la mesure fausse, et l'aurait rendue fausse
en silence — exactement le défaut que ce lot corrige.

**Rayon retenu : 2,50 m partout** (`TURRET_KEEPOUT_R`), comme le brief le demande :
`TURRET_FOOTPRINT_R` (2,08) × l'échelle de la classe lourde (1,200) = 2,496. Le script de
coque ne sait pas quelle classe le moteur pose où, et ne doit pas le savoir.

### Le critère est le PLAN D'ASSISE, pas la peau — et c'est un arbitrage

Le brief demande deux choses qui ne peuvent pas être vraies ensemble :

- « aucune géométrie au-dessus de la peau dans un disque de 2,50 m » ;
- « le bordé n'est pas redevenu plat ».

Interdire tout relief dans dix-sept disques de 19,6 m², c'est vider l'emprise, donc annuler
`BRIEF-0094` (« une tourelle, et la machinerie autour »). La garde applique donc le second
membre de la phrase du brief, celui qui est **mesurable et qui décrit le défaut** :
« échantillonner la hauteur du maillage dans le disque et **la comparer à l'assise** ».

Un module est refusé **s'il monte au-dessus du plan d'assise** de l'affût. C'est le plan sur
lequel `turret_kit.glb` est modelisé : le kit ne montre rien en dessous, donc rien de ce qui
reste dessous ne peut l'enterrer. Un massif de 0,34 m posé sur une peau qui plonge de 0,40 m
sous l'assise vit ; le même massif posé au point haut du disque s'écarte. C'est l'arbitrage
« sur mesure, pas d'office » que le brief demandait pour les tôles de 0,16 — appliqué aux
quatre hauteurs, sans en exempter aucune.

Le calcul est exact et non statistique : `_surface_box`/`_surface_poly` posent un dessus
**plan**, à `min(peau aux coins) + rise`. `_box_top()` recalcule cette valeur sans émettre.

---

## 2. Le contrat de marqueurs — diff VIDE

Relevé sur les deux binaires (celui de `HEAD` et celui livré), nœud par nœud : nom, parent,
translation locale et position monde, à cinq décimales (1/100 000 de mètre).

```
$ python3 contract.py base.glb > avant.txt      # 30 lignes
$ python3 contract.py long_cortege.glb > apres.txt
$ diff -u avant.txt apres.txt
(aucune sortie)
```

**30 marqueurs, 0 ligne de différence** : `Turret_01..17`, `Bay_01..07`, `Spine_01..05`,
`Ambry`. Aucune position n'a bougé, aucun parent n'a changé, aucun nom n'a bougé. Le harnais
du build re-vérifie de son côté les Y de `Bay_NN` et `Spine_NN` contre `bay_mouth_y()` et
`spine_seat_y()`, et les cinq translations de tronçon contre `SECTION_LENGTH`.

---

## 3. Le dégagement, mesuré sur le binaire livré

Méthode : on relit le `.glb`, on reconstruit les positions monde (les tronçons sont des
nœuds translatés), et pour **chaque sommet** tombant dans le disque de 2,50 m autour d'un
`Turret_NN` on compare son Y à l'assise du marqueur. Un sommet compte comme **module** s'il
dépasse `_surface_y()` de plus de 2 cm ; sinon c'est la **peau** (elle ne s'en écarte que du
bruit du `float32`).

| Marqueur | Assise | **AVANT** — plus haut sommet / assise | **APRÈS** — module / assise | APRÈS — peau / assise | Sommets dans le disque | Relief restant (au-dessus de la peau) |
|---|---:|---:|---:|---:|---:|---|
| Turret_01 | -4,4172 | **+1,0095** | **-0,5138** | -0,0072 | 15 | +0,128 |
| Turret_02 | -5,0066 | +0,2961 | *aucun module* | -0,0020 | 6 | — |
| Turret_03 | -4,9429 | +0,2948 | *aucun module* | +0,0029 | 8 | — |
| Turret_04 | -4,9419 | +0,9001 | *aucun module* | +0,0019 | 10 | — |
| Turret_05 | -4,2782 | +0,3929 | -0,5272 | -0,0218 | 52 | +0,141 |
| Turret_06 | -4,3277 | +0,0065 | -0,3472 | +0,0065 | 68 | +0,314 |
| Turret_07 | -4,9529 | +0,4197 | *aucun module* | -0,0371 | 10 | — |
| Turret_08 | -4,2831 | +0,8074 | -0,0247 | -0,0169 | 80 | +0,106 |
| Turret_09 | -4,3217 | +0,8216 | **-0,0036** | +0,0006 | 124 | +0,313 |
| Turret_10 | -4,9463 | +0,1412 | *aucun module* | -0,0437 | 14 | — |
| Turret_11 | -4,9579 | +0,4225 | *aucun module* | -0,0321 | 12 | — |
| Turret_12 | -4,2919 | +0,7190 | -0,1398 | -0,0081 | 63 | +0,248 |
| Turret_13 | -4,3381 | +0,2099 | -0,2861 | **+0,0099** | 88 | +0,338 |
| Turret_14 | -4,9439 | +0,4425 | *aucun module* | +0,0039 | 14 | — |
| Turret_15 | -4,2837 | +0,3984 | -0,3422 | -0,0163 | 15 | +0,320 |
| Turret_16 | -4,9531 | +0,3165 | *aucun module* | -0,0369 | 7 | — |
| Turret_17 | -4,4709 | -0,3343 | -0,3343 | -0,4691 | 52 | +0,159 |

**Le pire module du vaisseau est 3,6 mm SOUS l'assise** (`Turret_09`). Il était **1,0095 m
au-dessus** avant ce lot (`Turret_01`, une greffe : la couronne noyée et le bloc coupé à
mi-hauteur que l'opérateur a vus en jouant).

Les seules valeurs positives qui subsistent — de +0,0006 à **+0,0099 m** — appartiennent
**à la peau elle-même**, et il faut le dire précisément : l'assise est le point le plus haut
de l'emprise du **kit** (rayon 2,08 m), et entre 2,08 et 2,50 m la coque continue de monter.
Analytiquement, `_surface_y` monte jusqu'à +0,276 m au-dessus de l'assise dans ce couronne
(Turret_03) ; sur le maillage réellement exporté, le maximum est +0,0099 m. Ce n'est pas un
module : ça ne se déplace pas, c'est le vaisseau. Le corriger demanderait de changer
`TURRET_FOOTPRINT_R` ou le profil — hors périmètre (« ce lot déplace ce qui gêne, il ne
redessine rien »).

**Le bordé n'est pas devenu plat** : du relief subsiste dans **10 des 17 disques**, jusqu'à
+0,338 m au-dessus de la peau, et jusqu'à 124 sommets dans un même disque. La machinerie
entoure toujours l'installation ; elle passe simplement sous le plan du socle.

### Le harnais qui l'empêche de revenir

Cette mesure n'est pas un contrôle de circonstance : elle est **cuite dans `_audit()`** et
**échoue le build**. Elle relit le `.glb` produit (pas la scène Blender) et refuse tout
module au-dessus d'une assise dans le disque. Elle s'imprime aussi à chaque build, y compris
quand tout va bien — « un garde-fou qui ne parle que le jour où il échoue ne dit jamais de
combien on est passé près ».

---

## 4. Comptes avant / après

Comptes de **boîtes émises**, c'est-à-dire la colonne que le build imprime depuis toujours :

| Famille | Avant | Après | Écart | Écartées (déplacées) | Perdues |
|---|---:|---:|---:|---:|---:|
| greffes | 60 | **54** | **-10,0 %** | 8 | 5 |
| plaques | 349 | **311** | **-10,9 %** | 16 | 38 |
| nervures | 85 | **75** | -11,8 % | 15 | 4 |
| pastilles | 84 | **75** | -10,7 % | 0 | 9 |
| lisses, conduits, travées, fosses, collerettes, passerelle | — | inchangés | 0 % | — | — |
| triangles | 47 526 | 46 770 | -1,6 % | | |

Les quatre familles restent **sous les 15 %** que le brief pose comme seuil.

Sur les **35 greffes tirées** du vaisseau, 8 (23 %) ont trouvé une place de repli, 5 (14 %)
n'en ont trouvé aucune, 22 n'ont pas bougé d'un millimètre. Le déplacement est **latéral
d'abord** : une greffe est hébergée par une emprise de 8,4 m et fait jusqu'à 11,4 m de long
— la reculer la ferait sortir de son emprise, donc la perdrait, alors que la largeur offre
28 m. Les places de repli sont jugées **plus sévèrement** que la place tirée (canal, bord du
bordé, baies, fosses) : déplacer une greffe pour la poser sur une ouverture de hangar serait
remplacer un défaut par un autre.

Les 253,8 m de bordé calme (50,8 %), les 15 plages nues, la densité de texels
(0,197 tuile/m de moyenne pour 0,200 visé), la largeur hors-tout, le plafond de construction
et les jonctions de tronçons sont **identiques au bit près** à l'avant.

---

## 5. Le flux `rng` — ce qui a bougé et ce qui n'a pas bougé

Le flux est unique et partagé : c'est le point le plus fragile de ce fichier. Trois
décisions le protègent, et une le laisse dériver.

1. **La place tirée est toujours essayée en premier** (`GRAFT_NUDGES[0] == (0, 0)`,
   `PLATE_NUDGES[0] == 0`, `RIB_NUDGES[0] == 0`) et elle est jugée **exactement** comme
   avant ce brief, plus la garde. Un module qui ne gênait personne est bit à bit celui
   d'avant.
2. **Une greffe barrée consomme ses tirages** : elle emprunte le mécanisme `blocked` des
   baies et des fosses (« on tire, puis on décide d'émettre »), au lieu de sortir tôt.
3. **Aucun tirage n'a été ajouté ni retiré** : les échelles de repli sont des constantes.

**Ce qui dérive quand même, et il faut le dire** : une greffe *déplacée* change de centre,
donc de dégagement sous le plafond de construction, donc le nombre de terrasses que la
boucle pose avant de `break` — et cette boucle tire un `rng.uniform` par terrasse. Huit
greffes déplacées peuvent donc décaler le flux en aval dans leur tronçon. C'est visible dans
les comptes (les greffes du tronçon 2 passent de 11 à 13 boîtes : il y en a *plus*, pas
moins). Le brief l'autorise ; le résultat reste parfaitement déterministe, ce que la section
suivante vérifie.

---

## 6. Déterminisme — zéro octet divergent, trois fois

```
$ ./scripts/build-hull.sh --check long_cortege   (x3, soit six constructions)
[build-hull]   déterminisme OK — 9e846c7c2c764aa8550e26113bdfa0f64590d0d2e8d441a9be0d9915dd919142
[build-hull]   déterminisme OK — 9e846c7c2c764aa8550e26113bdfa0f64590d0d2e8d441a9be0d9915dd919142
[build-hull]   déterminisme OK — 9e846c7c2c764aa8550e26113bdfa0f64590d0d2e8d441a9be0d9915dd919142
```

Six exécutions, un seul sha256. `-t 1` partout (le script l'impose lui-même).

---

## 7. Ce que la garde ne couvre PAS

1. **Les tourelles légères ne sont pas des marqueurs.** Le moteur les pose à des décalages
   écrits dans `cortege_hardpoints.gd` (table `BATTERIES`), que la forge ne lit pas et ne
   doit pas lire — ce serait une dépendance à l'envers. Une greffe, une plaque ou une
   nervure peut donc encore en enterrer une, et **ce lot n'y peut rien**. L'arbitrage
   (remonter les décalages dans la forge sous forme de marqueurs, ou borner autrement côté
   moteur) est une décision de conception.
2. **La peau elle-même** monte jusqu'à +0,0099 m au-dessus de l'assise entre 2,08 et 2,50 m
   de rayon (mesuré ; +0,276 m analytiquement, la tessellation n'en retient pas le pic).
   C'est structurel : l'assise est définie sur l'emprise du kit, pas sur le disque de
   dégagement. Deux issues, toutes deux hors périmètre de ce brief : porter
   `TURRET_FOOTPRINT_R` à 2,50 (ce qui remonterait les 17 assises, donc **déplacerait les
   marqueurs en Y** — interdit ici), ou aplanir le profil sous les affûts.
3. **Le hors-disque immédiat.** Une greffe de 1,05 m posée à 2,51 m du centre reste
   autorisée. Elle ne masque pas le socle mais elle peut masquer un canon en dépression.
   Aucune mesure du brief ne le couvre ; le rendu ne l'a pas montré.
4. **Ce que le moteur pose lui-même** — kits de tourelle, de hangar, d'épine, citadelle —
   n'appartient pas à ce `.glb` et n'est pas testé ici.

---

## 8. Le rendu, regardé (ADR-0006)

Un chiffre ne suffit pas : la coque a été **rendue et regardée**, avec un affût **réel**
(`turret_kit.glb`, ses huit pièces sont modelisées sur le plan d'assise) posé sur son
marqueur, à la perspective du jeu (caméra `(0, 14, 5)`, 70° de plongée, les trois
directionnelles du jeu, sans ombre portée).

- **`Turret_01`, avant** : deux masses sombres mordent la couronne à 4 h et à 8 h, et un
  coin de greffe traverse le socle — c'est ce que l'opérateur a vu en jouant.
- **`Turret_01`, après** : le disque est net, la couronne et le socle sont entiers, la
  machinerie commence en dehors du cercle.
- **`Turret_09`, plan large** (le cas le plus serré après correction : -0,0036 m) : plaques,
  nervures et un feu magenta entourent l'affût de tout près, sans jamais monter dessus.

⚠️ **La planche de recette de `BRIEF-0089` n'a PAS été régénérée** — elle n'est pas un
livrable de ce brief et elle porte sur 5,7 Mo en LFS. Elle décrit donc encore la coque
d'avant (tourelle enterrée comprise). Une commande suffit à la remettre à jour, et c'est un
arbitrage du concepteur :

```bash
blender-aegis -t 1 -b -P tools/blender/build_long_cortege.py -- --plate
```

## 9. Texture et animation (ADR-0028, ADR-0046 §6)

- **Aucune texture**, et rien n'a changé : 8 matériaux en facteurs PBR, **0 image**,
  **0 texture**, **0 sampler** dans le `.glb`. Le dépliage de la peau reste
  `ak.box_project_uv()` à 0,200 tuile/m ; les faces déplacées le sont dans le même repère et
  gardent leur densité (0,144 à 0,200, moyenne 0,197 — identique à l'avant).
  **27/27 primitives portent `TEXCOORD_0`** et `TANGENT`, compté dans le binaire.
- **Aucune animation** : la coque est figée, aucune famille mobile, aucun pilote, aucune
  image clé. Tout ce qui bouge sur le Cortège est posé par le moteur sur les marqueurs.
