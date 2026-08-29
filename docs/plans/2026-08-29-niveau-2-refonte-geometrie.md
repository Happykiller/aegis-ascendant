# Niveau 2 — refonte de la géométrie de gameplay

- **Auteur** : session Claude, sur consignes et planche de l'opérateur (2026-08-29)
- **Périmètre** : la géométrie des trois structures de gameplay du Long Cortège, sa palette et
  son relief. **Pas les textures.**
- **Supersède** : la partie « pièces de gameplay » de
  [`2026-08-29-niveau-2-execution.md`](2026-08-29-niveau-2-execution.md), dont les lots A à G
  restent valides pour tout le reste
- **Planche de référence** : `assets/reference/concepts/BRIEF-0091-planche-consignes.png`

## Le constat

> « La géométrie actuelle ne porte pas les fonctions de gameplay. Les captures montrent des
> éléments qui ressemblent davantage à des marqueurs posés sur une piste qu'à des organes d'un
> vaisseau de 6,8 km. » — l'opérateur

Traduit en défauts nommés :

| Structure | Ce qu'on voit | Ce qu'il faut voir |
|---|---|---|
| Tourelle | un jeton circulaire et une boule lumineuse | un **affût** : socle ancré, couronne, bloc blindé, deux canons massifs |
| Pont d'envol | un gros bouton hexagonal magenta | un **trou** : cavité, parois, fond, rails, et un appareil dedans |
| Artère | un laser géant, blanc, plein cadre | une **tranchée technique** : conduits étroits dans une structure sombre |

## ⚠️ La règle de production — elle prime sur tout le reste

> **Chaque structure de gameplay doit être identifiable par sa seule SILHOUETTE, avec au plus
> 6–8 primitives principales. Les textures et les émissifs ne servent qu'à renforcer une
> fonction déjà lisible en géométrie.**

Et son test, qui tranche :

> **En noir et blanc, sans aucun émissif, on doit distinguer immédiatement une tourelle d'un
> hangar.** Aujourd'hui ce test échoue.

⚠️ **Ne jamais demander à la forge « d'améliorer la qualité 3D ».** C'est trop vague, et elle
ajoutera du détail inutile — du détail dont rien ne survit à 23 px/m.

## ⚠️ La décision d'architecture qui conditionne tout

**Le kit est de la géométrie SÉPARÉE, pas de la géométrie cuite dans la coque.**

C'est contre-intuitif — tout le reste du décor est cuit — et c'est obligatoire :

- la **couronne d'une tourelle tourne** ; une pièce cuite dans le tronçon ne tourne pas ;
- les **portes d'un hangar s'ouvrent**, et un hangar abattu doit rester **fermé** ;
- un **appareil doit être posé dans le puits** avant de décoller, donc à une place qui change.

⚠️ **Conséquence, et elle coûte une reforge** : la coque cuit AUJOURD'HUI les socles de tourelle
(`build_turret_pad`), les coamings de baie (`build_bay`) et les bulbes d'épine
(`build_spine_bulb`). Si le kit les fournit, il faut les **retirer de la coque** — sinon on aura
les deux, l'un dans l'autre.

### ⚠️ Et les hangars doivent être de VRAIS trous, ce qui est un changement de méthode

La forge avait écarté la cavité réelle, et sa raison était bonne :

> « Une VRAIE cavité demanderait de trouer la peau (booléen, donc non déterministe, et une peau
> non manifold). Ici la baie est un coaming POSÉ sur le bordé. »

Le compromis tenait tant qu'on visait 0,78 m de profondeur. La planche en demande **1,5 à
2,5 m** — et il n'y a que **1,1 m** de place entre la peau (−4,30) et le plafond du plan de jeu
(−3,20). **La profondeur demandée n'existe qu'en descendant SOUS la peau.**

Donc : la peau doit être **générée avec ses ouvertures**, pas trouée après coup. Pas de booléen ;
on n'émet simplement pas les faces de l'emprise et on raccorde au coaming. Le déterminisme est
préservé, et c'est la seule façon d'obtenir la profondeur.

## Les cotes retenues

⚠️ **Les mètres font foi, pas les pixels de la planche.** Vérifié : à mon cadrage réel, la coque
occupe 41,60 m sur 1920 px, soit 46 px/m — les repères en pixels de la planche sont environ deux
fois trop bas. Mais les **ratios du §8 tombent juste**, et ils s'accordent aux mètres :

| Pièce | Planche | Ratio §8 × joueur (1,76 m) | Retenu |
|---|---|---|---|
| Socle de tourelle | 3,0–4,0 m | 2,6–3,5 m | **3,4 m** |
| Hauteur de tourelle | 1,5–2,0 m | — | **1,7 m** |
| Longueur de canon | 2,5–3,5 m | — | **2,9 m** |
| Largeur des deux canons | 1,0–1,4 m | — | **1,2 m** |
| Ouverture de hangar | 5–7 m large, 7–10 m long | 5,3–7,0 m | **6,0 × 8,5 m** |
| Profondeur de hangar | 1,5–2,5 m | — | **1,8 m** |
| Coaming | 0,4–0,8 m | — | **0,6 m** |
| Nœud d'épine | — | 0,7–1,0 × joueur | **1,5 m** |

⚠️ **Les canons sont exagérés de 30 à 50 %**, délibérément. Un canon physiquement juste mais fin
disparaît après le post-traitement : à 23 px/m de détail utile, un tube de 12 cm fait trois
pixels. C'est une règle de lisibilité, pas une erreur d'échelle.

## Les quatre niveaux Z

Une stratification simple donne plus de profondeur que cinquante détails plans :

| Niveau | Usage |
|---|---|
| Z0 | la peau du bordé |
| Z + 0,2 | plaques, greffes |
| Z + 0,6 | nervures, coamings, machinerie |
| Z + 1,2 à + 2,0 | tourelles, hangars |

## La palette — 80 / 15 / 5

| Part | Rôle |
|---|---|
| **80 %** | gris / anthracite — la structure |
| **15 %** | grège moyen — l'appareillage |
| **5 %** | magenta / violet — l'émissif **et rien d'autre** |

⚠️ **Réduire de 60 à 70 % les aplats violets actuels.** Les grands rectangles violets sabotent la
hiérarchie : ils lisent comme des decals arbitraires, pas comme des volumes. Une greffe doit se
distinguer par sa **hauteur, son orientation et sa silhouette** — la couleur ne fait que
confirmer.

⚠️ Et l'aire se **mesure** sur le binaire livré, comme la forge l'a déjà fait pour `AA_Trim`
(2,29 %). Ce n'est pas une intention, c'est un chiffre à rendre.

## Faire respirer la coque

Séquence à viser : **15–20 m calmes → une installation → zone calme → un hangar → calme → un
groupe de tourelles.** Pas `élément → élément → élément`.

⚠️ C'est aussi du **gameplay** : quand un gros équipement entre dans le cadre, le joueur doit le
remarquer. Sur un fond chargé en permanence, il ne remarque rien.

---

# Les lots, dans l'ordre

> **État au 2026-08-29** : lots 1 et 2 livrés, acceptés et câblés. Les lots **3 à 5 sont partis
> ensemble** dans `BRIEF-0094` — ils remodèlent tous la peau du bordé, et trois reforges
> séparées du même fichier auraient divergé. Le lot 6 attend leur validation.

## LOT 1 — Le pont d'envol devient une cavité — ✅ LIVRÉ

**Le plus radical, et le premier**, parce que c'est celui où l'écart est le plus grand.

- `BRIEF-0091` : la coque perd ses coamings de baie et gagne **sept ouvertures réelles** dans sa
  peau, aux positions des marqueurs `Bay_NN`.
- `BRIEF-0092` : un **kit de hangar** en 7 pièces, assemblé paramétriquement :
  `bay_frame_left`, `bay_frame_right`, `bay_frame_top`, `bay_inner_wall`, `bay_floor`,
  `bay_launch_rail`, `bay_service_block`.
- Moteur : la séquence de décollage en **quatre temps** de la planche —
  *appareil au repos → allumage des moteurs → décollage → puits vide.*

⚠️ **L'appareil au repos est la VRAIE coque ennemie, pas un décor.** C'est le détail qui fera le
plus progresser la compréhension : le joueur voit un vaisseau immobile dans une cavité, ses
moteurs s'allumer, puis décoller. Il comprend alors que la structure **produit** les ennemis, ce
qu'aucune animation décorative ne lui dira.

Cela demande une addition au moteur : `EnemyController.park(world_position)` — visible, inactif,
posé. Elle est générique : tout niveau qui met un ennemi en scène avant de l'engager en aura
besoin.

## LOT 2 — La tourelle devient un affût — ✅ LIVRÉ

- `BRIEF-0093` : kit de 6 pièces — `turret_pad`, `turret_ring`, `turret_body`, `turret_barrel`,
  `turret_service_box`, `turret_pipe`.
- Assemblage : `[socle large] → [couronne] → [bloc blindé] ⇒ ══ deux canons ══`
- Trois éléments de machinerie autour du socle, **pas plus** : une paire de conduites, un
  radiateur, un coffret. Assez pour dire « appareil fonctionnel », pas assez pour en faire un
  modèle héroïque.
- Moteur : la **couronne** tourne (pas la tourelle entière), les canons partent d'elle, l'œil
  reste ≤ 25 % et vit entre les canons.

## LOT 3 — L'artère devient une tranchée — `BRIEF-0094`

- Canal **enfoncé** dans la coque, ~2 m de large, rebord mécanique sombre.
- 3 ou 4 bandes de 10–25 cm, **avec des interruptions**, et des nœuds ponctuels plus lumineux.
- ⛔ **Plus de grand centre blanc continu.**

⚠️ C'était déjà la consigne de `TEX-0013` — « au moins la moitié de l'aire SOMBRE », « le halo
est le travail du moteur, pas de l'image ». La texture la respecte ; c'est la **géométrie** qui
ne la portait pas, et l'émission moteur qui la noyait.

## LOT 4 — La palette — `BRIEF-0094`

Retirer 60–70 % des surfaces violettes. Mesure d'aire par matériau **rendue au rapport**.

## LOT 5 — Le relief — `BRIEF-0094`

Quelques nervures et masses en Z + 0,5 **autour des installations**, pour les ancrer. Rien
ailleurs : les zones calmes sont un livrable, pas un manque.

## LOT 6 — La décoration

**Seulement après validation des cinq précédents.**

---

# Le test d'acceptation

1. **Noir et blanc, émissifs coupés** (`--no-glow`, désaturation) : tourelle ≠ hangar, sans
   hésitation. C'est le test qui décide.
2. **Aire par matériau mesurée** sur le `.glb` : 80 / 15 / 5 ± 5 points.
3. **Silhouette ≤ 8 primitives principales** par structure, comptées au rapport.
4. **Budget** : la coque est à 39 434 tri sur 90 000. Le kit dispose donc de **50 000
   triangles** — largement de quoi faire 17 tourelles et 7 hangars soignés.
5. **Le plafond**, et il s'est dédoublé en cours de route : le **décor inerte** reste sous
   **−3,00**, les **pièces de gameplay** montent jusqu'à **−2,40**. La règle protège de ce qui
   masquerait le combat *sans jamais pouvoir être touché* ; une tourelle se tire dessus. Un test
   moteur (`test_no_turret_ever_reaches_the_flight_plane`) charge le kit, assemble la pièce la
   plus haute et la pose sur le pire marqueur pour tenir la borne.
   **30 marqueurs** intacts — sauf le `s` de `Turret_02` et `Turret_05`, arbitré au `BRIEF-0092` —
   et `build-hull.sh --check` déterministe.
6. Et la règle qui prime : **une capture regardée** (`ADR-0006`).

# Ce que ce plan ne fait pas

- **Il ne touche pas aux textures.** Elles sont livrées, intégrées et correctes ; le défaut est
  géométrique. Les revoir avant d'avoir la bonne géométrie serait retoucher la peinture d'un
  mur qu'on va abattre.
- Il ne change **ni les mécaniques ni l'équilibrage** : une tourelle tire toujours des balles en
  pivotant lentement, un pont produit toujours tant qu'il vit, un nœud éteint toujours le
  tronçon suivant. Ce qui change est ce qu'on en **voit**.
