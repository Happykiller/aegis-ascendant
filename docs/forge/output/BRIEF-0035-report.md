# BRIEF-0035 — Rapport : casser le monobloc, ailes à flèche variable

- **Agent** : asset-forge (Claude)
- **Date** : 2026-07-21
- **Brief** : `docs/forge/briefs/BRIEF-0035-specter-9-volumes-separes-ailes-mobiles.md`
- **Lu au préalable** : `docs/forge/CHARTE_CREATIVE.md`, `docs/decisions/ADR-0014-silhouette-du-specter-9.md`,
  `.claude/resources/pratique-detail-en-fraction-de-corde.md`, la planche
  `assets/reference/inspiration/reference_specter_9_design_sheet.png` (vues DESSUS et DESSOUS).

---

## 1. Le critère n°1 — l'aplat noir vu de dessus

`docs/forge/output/BRIEF-0035-aplat-noir-avant-apres.png` — trois panneaux, rendu orthographique
Cycles, matériau d'émission noir pur, fond blanc, transformation d'affichage `Standard` (l'AgX par
défaut de Blender 4.x mappe le blanc à ~0,75 et aurait donné un fond gris).

| Panneau | Contenu |
|---|---|
| gauche | **AVANT** — le `.glb` de BRIEF-0034, restauré depuis l'objet Git LFS `620aa13f…` |
| centre | **APRÈS** — le `.glb` livré, ailes **déployées** (pose de repos) |
| droite | **APRÈS** — même `.glb`, ailes à **26° de flèche** |

**Avant** : un triangle plein. Le seul blanc qui pénètre est une fente de quelques millimètres entre
les tuyères, dans les 8 % arrière de la silhouette. Le contour est convexe partout ailleurs.

**Après** : la silhouette est un assemblage de cinq corps. Le blanc pénètre en **trois endroits par
côté** :

| # | Échancrure | Ouverte par | Largeur mesurée |
|---|---|---|---|
| 1a | fuselage / nacelle, **partie avant** | l'avant (nez de nacelle → caisson) | 106 mm à y = −0,360, 65 mm à y = −0,100 |
| 1b | fuselage / nacelle, **partie arrière** | l'arrière (caisson → poupe) | 53 mm à y = +0,560, 86 mm à y = +0,960 |
| 2 | nacelle / bord d'attaque d'aile | fore et aft (l'aile ne couvre que 0,03 → 0,49 en Y) | 149 mm à y = +0,200, 197 mm à y = +0,300 |

Le brief demandait **au minimum deux par côté** : il y en a trois. Le contour n'est plus convexe :
l'arrière est un trident (poutre centrale + deux fuseaux) et les flancs sont interrompus par les
fentes d'emplanture d'aile.

Ces largeurs ne sont pas relevées à la main : `_print_silhouette_gaps()` les **remesure à chaque
build** sur les tables de géométrie, et le résultat est imprimé dans la sortie de
`./scripts/build-hull.sh`. La bounding box, elle, ne mesure pas les trous — c'est exactement ce qui a
laissé passer BRIEF-0033 et BRIEF-0034.

---

## 2. Ce qui a changé dans le plan

### 2.1 Le partage de la demi-envergure

La demi-envergure de 0,875 m n'est plus occupée par une surface unique mais par **cinq zones, dont
deux sont du vide** :

```
0,000 .. 0,130   fuselage    (corps fermé, bordé vertical de 0,186 m)
0,130 .. 0,172   FENTE 1     42 mm d'air
0,172 .. 0,368   nacelle     corps fermé, axe 0,270, rayon 0,098
0,368 .. 0,426   FENTE 2     58 mm d'air
0,426 .. 0,875   aile        lame mobile, 449 mm de portée exposée
```

Ce tableau est recopié en tête de `tools/blender/build_specter_9.py` : c'est l'invariant à vérifier
avant de toucher à quoi que ce soit.

### 2.2 Les corps

- **Le fuselage** — la coque loftée ne décrit plus que lui. `EDGE_H` passe de 12 mm (une tranche de
  bord d'aile) à 88 mm : le bord de la section devient un **bordé vertical de 0,186 m de haut**.
  C'est lui qui fait lire un corps fermé une fois qu'il n'y a plus d'aile pour le prolonger. Il court
  du nez à y = 1,030, où vient se poser la tuyère d'axe.
- **Les nacelles** — le profil de révolution court désormais de y = −0,440 (lèvre d'entrée d'air) à
  y = 1,048 (col), soit **1,49 m = 60 % de la longueur**, et se ferme aux deux bouts. `SHOULDER` et
  `INTAKE`, qui n'existaient que pour raccorder le fuseau au plan d'aile, ont disparu.
- **Le caisson de liaison** (`BRIDGE`, nouveau) — la **seule** matière qui traverse la fente 1, de
  y = 0,010 à 0,380. C'est la longueur qu'il n'occupe *pas* qui produit les échancrures 1a et 1b.
- **Le caniveau** (`GUTTER_*`) a été supprimé : c'était un ersatz de fente creusé dans une surface
  continue. La fente est maintenant réelle.

### 2.3 La section transversale : 39 abscisses → 17

Le corps central ne fait plus que 0,300 m de large. Les 15 fractions de corde héritées de l'aile
delta y auraient découpé des cellules de 4 mm : `cells()` les aurait **toutes éteintes en silence**,
et la coque serait sortie nue sans qu'aucun contrôle ne le signale. La trame a donc été
redimensionnée avec le corps (`CHEEK_T`, 5 fractions ; une rainure longitudinale de joue au lieu de
deux ; les seuils `MIN_*_PLATE` descendent de 50 à 22 mm et le retrait de `plate()` de 15 à 9 mm).

En contrepartie, **le détail a déménagé sur l'aile**, qui est désormais la grande surface plate du
vaisseau : deux rainures longitudinales et trois panneaux bleus enfoncés, tous exprimés en
**fraction de corde et de demi-envergure** (jamais en index de bande ni en mètre).

---

## 3. Ailes à flèche variable

### 3.1 Structure livrée (vérifiée sur le graphe glTF du `.glb`)

```
Specter9   mesh
Wing_L     mesh  t=(-0.3980, +0.0120, +0.0300)   enfants=[Flap_L]
  Flap_L   mesh  t=(-0.3416, -0.0060, +0.3520)   (RELATIF à Wing_L)
Wing_R     mesh  t=(+0.3980, +0.0120, +0.0300)   enfants=[Flap_R]
  Flap_R   mesh  t=(+0.3416, -0.0060, +0.3520)
Nozzle_L   mesh  t=(-0.2700, -0.0400, +1.0480)
Nozzle_R   mesh  t=(+0.2700, -0.0400, +1.0480)
```

Six pièces mobiles, `Flap_L/R` **enfants** de `Wing_L/R` (`ak.moving_part(..., parent=...)`), origine
de chaque nœud sur son articulation.

- `Wing_L/R` : pivot sur l'axe **vertical** (Y Godot), au flanc externe de la nacelle. **Sens opposé
  entre bâbord et tribord.**
- `Flap_L/R` : charnière **parallèle à X**. Ce n'est pas de la paresse : `moving_part` n'exporte
  qu'une translation, jamais de rotation, donc les axes locaux du volet sont ceux de l'aile. Une
  charnière parallèle à l'axe X de l'aile est la seule qui reste un axe de nœud une fois l'aile en
  flèche.
- **Position de repos = ailes déployées** (flèche minimale, bord d'attaque à 29,5° de l'axe
  transversal). C'est l'état que le `.glb` montre et que le contrat mesure.

### 3.2 Débattement mesuré — et le piège de la bbox au repos

Le brief demandait de traiter explicitement le fait que **le contrat mesure la pose de repos**. Deux
mesures sont désormais faites *sur le maillage livré*, à chaque build, et **bloquantes** :

```
volets : plafond de debattement mesure 21.1 deg
ailes  : fleche admissible mesuree 32.25 deg (cible 26)
         premiere butee : peau de nacelle a y = +0.478 (x = 0.3790, peau 0.3672)
```

`_wing_sweep_limit()` balaie l'angle par pas de 0,25°, sommet par sommet, sur **l'aile ET son volet**
(qui la suit puisqu'il en est l'enfant), et teste trois choses : largeur ≤ largeur au repos,
longueur ≤ ±1,230, et |x| ≥ peau de nacelle + 12 mm. Le build **échoue** si le résultat passe sous
`WING_SWEEP_TARGET = 26°`.

Vérification indépendante, faite sur le `.glb` publié en appliquant la rotation hors du script :

| Flèche | Largeur X | Hauteur Y | Longueur Z |
|---|---|---|---|
| 0° (repos, livré) | **1,7520** | 0,6464 | **2,4600** |
| 13° | 1,6113 | 0,6464 | 2,4600 |
| 26° | **1,4309** | 0,6464 | 2,4600 |
| 32° (limite mesurée) | 1,3361 | 0,6464 | 2,4600 |

**Aucune dimension n'augmente en repliant.** Ce n'est pas un hasard mais une propriété
constructive : toute la géométrie de l'aile est exprimée en **polaire autour du pivot**, avec un
angle ≥ 0 au repos. Une rotation conserve le rayon et ajoute θ à l'angle ; tant que
`angle + flèche ≤ 90°`, `x = x_pivot + r·cos(angle)` ne peut que **décroître**. L'aile ne peut donc
ni sortir de la boîte en largeur, ni traverser une nacelle située en deçà de `x_pivot`.
`WING_TE_ROOT = (0.340, 56°)` est la valeur critique : elle ne laisse que 34° de marge, dont 26 sont
consommés par la flèche visée. (La marge Z est large : la poupe est fixée par les pétales de tuyère
à z = 1,230 et le volet le plus reculé n'atteint que 0,653 à 26°.)

### 3.3 Deux défauts trouvés par la mesure, pas par la relecture

1. **`nacelle_half_width()` rend un rayon, pas une abscisse.** La première version de
   `_wing_sweep_limit()` comparait `x` au rayon (0,098) au lieu de la peau (`NACELLE_X + rayon` =
   0,368). Résultat annoncé : « 45° admissibles, aucune butée ». Réalité : l'aile traversait le
   fuseau dès 33°. Corrigé, la mesure tombe à 32,25° — ce qui est la bonne réponse.
2. **La ferrure de charnière est la pièce la plus contraignante de toute l'aile.** Son coin
   arrière-interne a l'angle polaire le plus grand, donc c'est lui qui passe derrière le pivot le
   premier. Centrée 4 mm plus en dedans et 18 mm plus en arrière, elle faisait tomber la flèche
   admissible de 32° à **28°**. Même mécanisme exactement que le marquage doré qui avait fait tomber
   un volet à 2,8° sous BRIEF-0034.

---

## 4. Mesures du `.glb` livré

| Grandeur | Valeur | Contrat |
|---|---|---|
| Largeur X | **1,7520 m** | 1,75 ± 3 % ✔ (écart 0,11 %) |
| Longueur Z | **2,4600 m** | 2,46 ± 3 % ✔ (écart 0,00 %) |
| Hauteur Y | **0,6464 m** | 0,62 – 0,72 ✔ (26,3 % de la longueur) |
| Triangles | **31 840** | ≤ 60 000 ✔ (53 % du budget) |
| Sommets | 40 253 | — |
| Pivot | X −0,0000 / Z +0,0000 | ± 0,02 ✔ |
| Matériaux | 7 / 7 (`AA_Hull`, `AA_Panel`, `AA_Trim`, `AA_Greeble`, `AA_Glass`, `AA_Emissive_Engine`, `AA_Marking_Red`) | ✔ |
| UV + tangentes | présentes sur **les 7 maillages**, 4,0 tuiles/m | ✔ |
| Points d'attache | 10 / 10 | ✔ |
| Taille | 2 153 276 o | — |
| Déterminisme | `./scripts/build-hull.sh --check specter_9` → **OK**, sha256 `f1f21f07…` | ✔ |
| Livrée tricolore / chiffres | aucun (ADR-0014) | ✔ |

Le budget de triangles **baisse** (45 828 → 31 840) alors que le brief autorisait à le dépenser :
séparer les volumes coûte des faces de fermeture, mais la disparition de l'aile delta (39 abscisses
× 71 stations) en rend beaucoup plus. La marge de 28 160 triangles reste disponible.

### Points d'attache — un changement de dérivation à signaler

`Muzzle_Wing_L/R` et `Muzzle_Tip_L/R` étaient dérivés par inversion de `PLANFORM` à |x| = 0,500 et
0,800. `PLANFORM` ne décrit plus que le fuselage (max 0,130) : l'inversion aurait levé une
`ContractError` à chaque build. C'est le piège de
`.claude/resources/pratique-detail-en-fraction-de-corde.md` appliqué cette fois à un **point
d'attache** et non à un bandeau. Ils sont désormais dérivés d'une **fraction d'envergure de la
lame** (`WING_MUZZLE_S = 0.34`, `TIP_MUZZLE_S = 0.94`) :

| Point | Avant | Après (repère Godot X, Y, Z) |
|---|---|---|
| `Muzzle_Wing_L/R` | ∓0,500 / −0,018 / +0,007 | **∓0,5935 / +0,0090 / +0,0516** |
| `Muzzle_Tip_L/R` | ∓0,800 / −0,018 / +0,607 | **∓0,8528 / −0,0110 / +0,2297** |

Les huit autres ne bougent que du fait de l'écartement de nacelle (`Engine_L/R` : 0,352 → 0,270).
Le rôle de chacun est inchangé (échelle de puissance, spec §9.1). **À vérifier côté intégration** :
si un `.tres` d'arme fige un offset en dur, il faut le relire.

---

## 5. Lisibilité en vue de jeu — verdict franc

`docs/forge/output/BRIEF-0035-lisibilite-vue-de-jeu.png` : la vue « game » (70° au-dessus du plan,
la caméra réelle de `graybox.tscn`), recadrée sur la coque puis réduite à 48, 64 et 96 px de large,
avant et après.

**Ce que je lis honnêtement :**

- **À 48 px, la silhouette reste identifiable, et elle est plus distinctive qu'avant.** Le corps
  central lit comme une flèche verticale claire, les trois sorties de tuyère forment une base
  reconnaissable. Un joueur retrouve son vaisseau.
- **Mais les ailes perdent en cohésion.** Elles sont séparées du corps par 58 mm, soit **1,6 px** à
  48 px sur un fond sombre : le vide et l'ombre se confondent, et les lames lisent comme deux
  éclats détachés plutôt que comme les extrémités d'un même appareil. À 64 px le lien se rétablit,
  à 96 px il n'y a plus de doute.
- **Le contour extérieur est moins compact.** L'ancienne silhouette était un aplat triangulaire :
  une seule masse, imbattable en lisibilité brute. La nouvelle est plus verticale et plus ajourée.
  Sur un fond de nébuleuse chargé, elle sera *un peu* plus fragile.

**Mon arbitrage, si la lecture pose problème en jeu** — par ordre de coût croissant, et **aucun ne
touche au critère n°1** :

1. **Feu de bord d'attaque d'emplanture** (gratuit, ~40 triangles) : un bandeau `AA_Emissive_Engine`
   posé sur la racine de chaque aile. À 48 px, deux points cyan de part et d'autre du corps
   rattachent les lames au fuselage sans rien reboucher. **C'est le levier que je recommande en
   premier** : il joue sur la perception, pas sur la géométrie.
2. **Resserrer la fente 2** de 58 à ~35 mm (`WING_PIVOT_X` de 0,398 à 0,375, et la chape de nacelle
   qui suit). L'échancrure reste franche sur l'aplat — elle vaudrait encore 3,5 fois la largeur du
   trait de rainure — et l'aile lit comme greffée. **Coût : la flèche admissible retombe autour de
   28°**, donc plus que les 26 visés mais avec peu de marge pour la suite.
3. **Élargir la lame** (corde d'emplanture 0,44 → 0,50) en reculant `WING_TE_ROOT` : plus de masse
   claire à la même envergure. **Coût : la flèche admissible tombe sous 26°** — la contrainte
   `angle + flèche ≤ 90°` est saturée. À écarter sauf si le débattement est revu à la baisse.

Je n'ai pas appliqué ces leviers : le brief dit de proposer l'arbitrage plutôt que de le subir, et
le choix entre « lisibilité maximale » et « débattement de flèche » appartient au concepteur.

---

## 6. Autres décisions et leurs raisons

- **Les dérives ont été reculées, pas couchées.** À 34° d'inclinaison elles projetaient jusqu'à
  x = 0,493 en vue de dessus et **rebouchaient la fente 2** — le seul élément du vaisseau capable
  d'annuler le brief sans qu'aucun contrôle s'en aperçoive. Première parade : les coucher à 22°. Le
  rendu a montré qu'à 22° elles ne se voient plus du tout d'en haut, ce qui annule la raison même de
  les avoir inclinées (BRIEF-0034 §5). Parade retenue : les **reculer** derrière l'aile
  (y = 0,600 → 1,012, quand la lame la plus repliée ne dépasse pas y = 0,653) et les **redresser à
  30°**. Elles projettent 145 mm en vue de dessus, dans une zone où il n'y a rien à boucher.
- **Deux explosions de maillage attrapées en cours de route**, toutes deux dues à
  `bmesh.ops.inset_region(use_even_offset=True)` :
  1. La troncature du logement de volet écrasait 4 à 6 sommets par nervure sur la ligne de coupe.
     Blender annonçait « Mesh Wing_L is not valid », le chanfrein projetait ensuite des sommets à
     15 cm au-dessus de la lame, et la coque sortait à **1,79 m de large — toujours dans la
     tolérance de 3 %, donc sans erreur**. Corrigé en **reparamétrant** la corde (`t · t_max`).
  2. Multiplier les abscisses par `side` dès la construction **retourne les faces** : l'inset
     explosait côté tribord et sortait un sommet à y = −3,18 m (coque de 4,41 m). L'aile est
     désormais bâtie côté bâbord puis **miroitée en fin de fonction**. Effet de bord bienvenu : les
     greebles des deux ailes sont strictement symétriques.
  Ajouté au passage : `_insettable()`, garde-fou qui écarte toute face dont la plus courte arête ne
  supporte pas le retrait demandé — l'équivalent, sur l'aile, de ce que `cells()` fait sur la coque.
- **Tout le détail est posé en fraction**, conformément à
  `.claude/resources/pratique-detail-en-fraction-de-corde.md` : bandeaux cyan par `_chord_x()`,
  panneaux d'aile par fraction d'envergure (`stations[i]`) et non par index de bande — parce que
  `_wing_rib_stations()` insère une paire serrée dont la position dépend de `FLAP_HINGE_Y`, et qu'un
  index écrit en dur désignerait autre chose au premier réglage de volet.

---

## 7. Limites connues

1. **`Muzzle_Wing_*` et `Muzzle_Tip_*` sont sur une pièce mobile mais restent figés.**
   `ak.attach_point()` ne sait créer qu'un `Empty` à la racine : le kit n'expose aucun parentage pour
   les points d'attache. Les deux paires restent à la position « ailes déployées ». Sans conséquence
   sur le tir (les offsets sont lus une fois), visible seulement si l'on veut faire partir un flash
   de canon d'aile en flèche maximale. **Manque du kit à signaler** (`MovingPart` sait se parenter,
   `attach_point` non) — hors périmètre de ce brief, qui interdit de toucher à `aegis_kit.py`.
2. **Le débattement de volet passe de 18,5° à 21,1°** (le jeu applique 11°) : aucune régression,
   mais la valeur a changé, `ShipFlight` devrait être relu si sa marge était calée dessus.
3. **`_print_silhouette_gaps()` mesure la fente 2 sur le plan d'aile NON tronqué.** Aux stations où
   seul le volet subsiste (y > 0,371), il affiche « aile absente » alors qu'il y a de la matière.
   La mesure reste juste là où elle compte (l'emplanture) ; l'aplat noir reste le juge.
4. **Les nacelles ont maigri de 19 %** (rayon 0,121 → 0,098) pour rendre de l'envergure à l'aile. La
   tuyère et ses pétales ont suivi à la même échelle : les plumes de propulsion côté Godot sont
   dimensionnées sur un rayon de sortie qui passe de 0,135 à 0,109 m. **À revoir côté VFX.**
5. **Pas de `.blend`, pas de texture** — conforme au brief. `assets/reference/` n'a pas été touché.

---

## 8. Livrables

| Fichier | Rôle |
|---|---|
| `tools/blender/build_specter_9.py` | script retravaillé (source de l'asset, ADR-0008) |
| `assets/imported/models/ships/specter_9.glb` | coque + 6 pièces mobiles (Git LFS) |
| `docs/forge/output/BRIEF-0035-report.md` | ce rapport |
| `docs/forge/output/BRIEF-0035-aplat-noir-avant-apres.png` | **le critère n°1**, avant / après / flèche 26° |
| `docs/forge/output/BRIEF-0035-lisibilite-vue-de-jeu.png` | vue « game » à 48 / 64 / 96 px, avant et après |
| `docs/forge/output/BRIEF-0035-planche-4-vues.png` | planche de contrôle (game, dessus, profil, trois-quarts) |

Provenance mise à jour dans `assets/licenses/ASSET_PROVENANCE.csv` (la ligne `specter_9_hull` est
**remplacée**, non dupliquée ; trois lignes de rendu ajoutées).

---

## 9. Critères d'acceptation

- [x] **L'aplat noir vu de dessus montre des trouées** — trois par côté, mesurées et rendues.
- [x] `Wing_L/R` sont des pièces mobiles ; `Flap_L/R` sont leurs **enfants** (vérifié sur le graphe glTF).
- [x] Débattement de flèche **mesuré et remesuré à chaque build** (32,25° pour 26 visés), ailes déployées au repos.
- [x] Bbox X/Z inchangée à ±3 % **au repos** (1,7520 × 2,4600) **et vérifiée en position repliée** (aucune dimension n'augmente à 13°, 26° ni 32°).
- [x] `./scripts/build-hull.sh --check specter_9` : déterminisme OK.
- [x] ≤ 60 000 triangles (31 840) ; UV et tangentes présentes ; 10 points d'attache conservés.
- [x] Aucune bande rouge de livrée, aucun chiffre.
