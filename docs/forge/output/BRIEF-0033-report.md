# BRIEF-0033 — Specter-9 : fuselage et pièces mobiles — rapport de forge

- **Agent** : `asset-forge` (Claude)
- **Date** : 2026-07-21
- **Brief** : `docs/forge/briefs/BRIEF-0033-specter-9-fuselage-et-pieces-mobiles.md`
- **Cadre** : ADR-0008 (pipeline), ADR-0011 (budgets), ADR-0013 (textures), ADR-0009 (référence IP),
  charte créative §3/§4/§6.
- **Kit** : `tools/blender/lib/aegis_kit.py` **non modifié** (voir §9 pour ce qui lui a manqué).

---

## 1. Livrables

| Fichier | État |
|---|---|
| `tools/blender/build_specter_9.py` | retravaillé (1 787 lignes) |
| `assets/imported/models/ships/specter_9.glb` | régénéré — coque + **4 pièces mobiles** (LFS) |
| `assets/licenses/ASSET_PROVENANCE.csv` | ligne `specter_9_hull` **réécrite**, pas dupliquée |
| `docs/forge/output/BRIEF-0033-report.md` | ce document |

Aucun autre fichier touché : ni `scenes/`, ni `scripts/`, ni `resources/`, ni les tests, ni le kit.

---

## 2. Déterminisme — verdict du `--check`

```
$ ./scripts/build-hull.sh --check specter_9
[build-hull] specter_9
contrat OK — Specter-9
  ...
[build-hull]   déterminisme OK — 59e2f024a5e498e3295bb52806492e6d4d6a4ff7c9c0a5de3c49dbee9df38b2d
```

**Deux exécutions consécutives donnent un `.glb` byte-identique.** Le fichier livré porte ce
sha256, pour 2 586 916 octets. Tous les builds de cette session sont passés par
`./scripts/build-hull.sh` (qui force `-t 1`) ; `blender45 -b -P` n'a jamais été appelé à la main
sur ce script.

À noter : contrairement à l'Aegis Citadel de BRIEF-0032, le Specter-9 n'a montré **aucune**
divergence de tangentes, y compris avant ce brief. C'est cohérent avec l'en-tête de
`build-hull.sh` : la stabilité apparente du Specter-9 est ce qui avait fait croire que le défaut
venait du modèle et non de l'ordonnancement. Le `-t 1` reste donc la seule garantie transportable.

`./scripts/check.sh` : **ALL GREEN** (109 méthodes de test, 720 assertions, 0 échec) — l'import
Godot du `.glb` reformé ne casse rien.

---

## 3. Mesures réelles, relevées sur le `.glb` livré

### 3.1 Contrat

| Mesure | Avant (BRIEF-0031) | Après | Contrat |
|---|---|---|---|
| Largeur X | 1,750 m | **1,7500 m** | 1,75 ±3 % ✔ |
| Longueur Z | 2,460 m | **2,4600 m** | 2,46 ±3 % ✔ |
| **Hauteur Y** | 0,516 m | **0,6325 m** | 0,62–0,68 ✔ |
| **Hauteur / longueur** | 21,0 % | **25,7 %** | 25–28 % ✔ |
| Triangles | 29 716 | **42 520** | ≤ 60 000 ✔ (71 % du plafond) |
| Sommets | 32 198 | **48 184** | — |
| Pivot (X, Z) | — | **(−0,0000, +0,0000)** | ±0,02 m ✔ |
| `TEXCOORD_0` + `TANGENT` | oui | **oui, sur les 5 maillages** | ✔ |
| Fichier | 1,9 Mo | 2 586 916 o | — |

Répartition verticale (repère Godot) : **Y ∈ [−0,3450 ; +0,2875]**. Soit **54,5 % de la hauteur
sous le plan d'aile** — c'est un choix, voir §5.

### 3.2 Triangles par matériau

| Matériau | Triangles | Rôle |
|---|---|---|
| `AA_Hull` | 26 575 | coque |
| `AA_Greeble` | 10 137 | mécanique, creux, cadres, écopes |
| `AA_Trim` | 2 746 | joncs, cadre de verrière, arête de rail, lèvre de pétale |
| `AA_Panel` | 1 382 | panneaux bleus |
| `AA_Emissive_Engine` | 1 374 | vasques, bandeaux, feux de bout d'aile |
| `AA_Marking_Red` | 166 | deux marquages restreints |
| `AA_Glass` | 140 | verrière |

Les **7 matériaux** sont présents et assignés, `MATERIAL_ORDER` intact.

### 3.3 Répartition par nœud

| Nœud | Triangles | Type |
|---|---|---|
| `Specter9` | 38 908 | coque |
| `Flap_L` / `Flap_R` | 366 chacun | pièce mobile |
| `Nozzle_L` / `Nozzle_R` | 1 440 chacun | pièce mobile |

---

## 4. Pièces mobiles — pivots dans les deux repères

`ak.moving_part()` a été utilisé pour les quatre pièces. La chaîne d'axes du kit est
`(x, y, z)_auteur → (−x, z, y)_glTF` ; les valeurs ci-dessous, **relues sur le `.glb`**, la
vérifient point par point.

| Nœud | Pivot (repère d'auteur : nez −Y, dessus +Z, bâbord +X) | Origine du nœud glTF/Godot | Rôle du pivot |
|---|---|---|---|
| `Flap_L` | (+0,7370 ; +0,6230 ; −0,0200) | **(−0,7370 ; −0,0200 ; +0,6230)** | ligne de charnière, bord de fuite bâbord |
| `Flap_R` | (−0,7370 ; +0,6230 ; −0,0200) | **(+0,7370 ; −0,0200 ; +0,6230)** | ligne de charnière, bord de fuite tribord |
| `Nozzle_L` | (+0,2680 ; +1,0480 ; −0,0620) | **(−0,2680 ; −0,0620 ; +1,0480)** | centre du **col** de tuyère bâbord |
| `Nozzle_R` | (−0,2680 ; +1,0480 ; −0,0620) | **(+0,2680 ; −0,0620 ; +1,0480)** | centre du **col** de tuyère tribord |

Chacune est un **nœud glTF séparé** portant son propre maillage, sans rotation ni échelle, avec
`TEXCOORD_0` et `TANGENT`.

### 4.1 Le pivot a été vérifié **animé**, pas seulement lu

Le brief prévient qu'une origine restée à zéro ne se voit qu'une fois la pièce animée. J'ai donc
reposé les quatre pièces (volets à −12°, couronnes à ×1,45 radial) et re-rendu :

- **volets** : ils battent sur leur charnière, le bord de fuite descend de **34,5 mm**
  (`corde 0,166 × sin 12°`), la charnière ne bouge pas ;
- **contre-épreuve chiffrée** : la même rotation appliquée autour de l'origine du modèle
  (pivot laissé à zéro) déplacerait le volet de **145 mm vers le bas et 17 mm vers l'avant** —
  il se détacherait franchement de l'aile ;
- **tuyères** : la couronne s'évase autour du col, sans dérive longitudinale — l'échelle radiale
  (Godot X/Y, qui sont X et Z d'auteur) est bien un évasement pur.

### 4.2 Dégagement des volets à ±12° — mesuré, pas supposé

L'aile est **réellement échancrée** : en arrière de `y = 0,610` (repère d'auteur) la section de
coque s'arrête à `|x| = 0,600` au lieu d'aller jusqu'au bord d'aile. Une cloison quasi verticale
est créée par une paire de stations serrées (0,6070 / 0,6100). Au repos le volet remplit
l'échancrure : **la silhouette vue de dessus est celle d'avant**, au jeu de charnière près.

Marge du volet par rapport à cette cloison, calculée sur la boîte englobante locale réelle :

| Braquage | Z minimal atteint (local) | Marge à la cloison |
|---|---|---|
| **−12°** | −0,01106 | **+1,94 mm** |
| **+12°** | −0,00665 | **+6,35 mm** |

Le volet **ne traverse pas l'aile** sur toute la plage demandée. La marge du côté −12° est fine
(2 mm) : c'est le prix du jeu de charnière de 13 mm, lui-même dicté par la géométrie (le coin
supérieur avant du volet est à 54 mm de l'axe, il avance de `54 × sin 12° = 11,2 mm`). **Au-delà
de ±13° le volet mordrait la cloison** — c'est la limite à respecter côté Godot.

### 4.3 Tuyères

- 12 pétales par couronne, **fermés au repos** (jeu angulaire de 2,4°), longueur 0,182 m en bas.
- Biseau de sortie : les pétales du haut sont **raccourcis de 70 mm**. Sans ce biseau, une
  couronne de 0,18 m de long autour d'un alésage de 0,10 m de rayon masque la vasque émissive
  depuis une caméra à 20° de la verticale — soit exactement le défaut que BRIEF-0026 avait
  identifié sur la version précédente.
- La vasque émissive (dans la coque) reste à axe relevé de 42 mm, en avant du col.
- **`Engine_L/R` sont à Z = +1,2340, soit 4 mm DERRIÈRE la lèvre des pétales** (Z = +1,2300) :
  la plume de traînée sort de l'arrière de la couronne et non de son milieu.

### 4.4 Points d'attache — les 10 conservés, mêmes rôles

| Nom | Position (Godot X, Y, Z) |
|---|---|
| `Muzzle_L` / `Muzzle_R` | (∓0,0800 ; −0,0676 ; −1,0700) |
| `Muzzle_C` | (0 ; −0,0676 ; −1,0700) |
| `Muzzle_Wing_L` / `_R` | (∓0,5000 ; −0,0180 ; −0,0518) |
| `Muzzle_Tip_L` / `_R` | (∓0,8000 ; −0,0062 ; +0,4180) |
| `Engine_L` / `Engine_R` | (∓0,2680 ; −0,0440 ; +1,2340) |
| `Cockpit` | (0 ; +0,2088 ; −0,3800) |

Tous restent **dérivés de la géométrie** (station de bord d'attaque inversée, axe des tubes,
centre du volume de verrière), jamais écrits en dur. Trois valeurs bougent, et chacune est la
conséquence mécanique d'un changement de coque, pas un réglage :

- `Cockpit` recule de 0,138 m — la verrière a reculé d'autant ;
- `Engine_L/R` reculent de 0,014 m — pour passer derrière la couronne de pétales ;
- `Muzzle_L/R/C` descendent de 0,011 m — l'axe des tubes est centré sur la section de quille,
  laquelle est plus profonde.

`Muzzle_Wing_L/R` et `Muzzle_Tip_L/R` sont inchangés au millimètre près.

---

## 5. Ce que le rendu montre — et le compromis d'épaisseur, assumé

Rendu : `blender45 -b -P tools/render-hull.py -- assets/imported/models/ships/specter_9.glb`
(4 vues : game 20° / dessus / profil / trois-quarts), regardé à chaque itération — quatre passes.

### 5.1 Vue « profil » : appareil superposé, oui

Le critère du brief est tenu. De bas en haut, la silhouette de profil empile **six couches
distinctes**, chacune avec sa propre arête horizontale :

1. **quille ventrale** à flancs verticaux (−0,345 m au maître-couple), flanc bleu, platine or,
   marquage rouge, six cadres transversaux ;
2. **écopes ventrales** de nacelle, ventre sombre, trois nervures ;
3. **plan d'aile** vu par la tranche, avec sa **lisse de nez** (chine) qui trace la ligne
   horizontale séparant corps supérieur et corps inférieur ;
4. **corps de fuselage** ;
5. **arête dorsale basse** à flancs verticaux bleus, canal technique creusé sur le dessus, six
   cadres transversaux ;
6. **verrière** en retrait dans son puits, encadrée en relief (deux longerons or + pare-brise +
   dosseret).

Plus, en volumes propres : les **nacelles** (qui saillent de 0,13 m sous l'aile, avec col,
collier, jonc or, anneaux et couronne de pétales) et les **rails de bout d'aile** (lame à arête
plate, jonc or sur le dessus, flanc bleu).

Ce n'est plus une plaque. La preuve la plus nette est la vue trois-quarts — le cadrage de l'écran
d'accueil — où le vaisseau a maintenant un dessus, un dessous et un flanc distincts.

### 5.2 Vue « game » (20° de la verticale) : **l'épaisseur ne nuit pas**, et voici pourquoi

Réponse franche à la question posée : **non, la coque ne lit pas comme un pâté de dessus.** Mais
ce n'est pas une chance, c'est la conséquence d'un choix pris avant de modéliser :

> Ce qu'on ajoute **au-dessus** du plan d'aile élargit la silhouette vue de dessus. Ce qu'on
> ajoute **en dessous** est gratuit pour cette lecture. Et ce qu'on ajoute au-dessus doit être
> **étroit**.

D'où la répartition **54,5 % sous / 45,5 % sur** le plan d'aile, et une arête dorsale de
**0,176 m** de large seulement sur une envergure de 1,75 m (10 %). La quille (−0,345 m, large de
0,216 m) et les écopes (≈ −0,24 m) portent l'essentiel du gain et sont intégralement masquées, de
dessus, par un fuselage deux fois plus large qu'elles.

Deux défauts de lecture de dessus sont apparus au rendu et ont été corrigés :

| Défaut vu au rendu | Cause | Correction |
|---|---|---|
| L'arête dorsale lisait comme une **planche blanche lisse** de 1,3 m | son dessus est la seule de ses faces que la caméra voit, et il était nu | canal technique **creusé** (`inset_panel` sur les faces de dessus) + 6 cadres en relief. Un bandeau sombre simplement *posé* avait d'abord été essayé : enfermé dans le solide, il était invisible. |
| Les rails de bout d'aile **flottaient hors de l'aile** | posés à `x = 0,846` constant, alors que la demi-envergure tombe sous 0,846 en avant de `y = 0,40` | le rail suit désormais le bord d'attaque (`min(w(y) − 0,028 ; 0,846)`) puis se redresse au bout d'aile |

Un troisième défaut concernait le profil : l'écope ventrale, laissée en blanc de coque, lisait
comme une grosse cloque lisse ; elle est passée en ventre sombre, flancs bleus et bouche noire.

### 5.3 Je n'ai pas redescendu l'épaisseur

Le brief autorise de redescendre si l'épaisseur nuit. Elle ne nuit pas, et je n'ai pas voulu
rendre un chiffre par prudence : **0,6325 m, soit 25,7 %**, dans la fourchette basse des 25–28 %
demandés. J'ai visé la borne basse volontairement — au-delà, il aurait fallu monter le point haut
(verrière ou arête), c'est-à-dire précisément la partie qui coûte en lecture de dessus.

---

## 6. Ce qui a changé dans le script, par ordre de rendement

1. **Profil épaissi et stratifié** — `CROWN` 0,165 → 0,195 et `BELLY` −0,150 → −0,185 (corps
   0,315 → 0,380 m), mais surtout la coque cesse d'être *une* lentille : arête dorsale, quille,
   écopes, chine et rails sont des **volumes propres à flancs verticaux**, pas des bombements.
2. **Nacelles en volumes distincts** — écartées 0,235 → 0,268, descendues −0,030 → −0,062. Il
   reste 3 cm d'air entre l'arête dorsale et chaque fuseau, et le fuseau saille de 13 cm sous
   l'aile. Col, collier, jonc or, deux anneaux concentriques, couronne de pétales.
3. **Nez plus long** — la verrière recule de 0,13 m (`CANOPY` : −0,79…−0,245 → −0,66…−0,10),
   `CANOPY_SINK` 18 → 26 mm (« en retrait »), et le maître-couple passe de `y = 0,05` à
   `y = 0,22` avec un avant abaissé. **Le planform n'est pas touché** : c'est la répartition des
   masses qui allonge le nez, pas le rapport longueur/envergure (inchangé à 1,41).
4. **Présence verticale sans dérive** — rails de bout d'aile (0,17 m de haut, jonc or, feu cyan)
   + arête dorsale basse (5,5 cm au-dessus du pont).
5. **Pièces mobiles** — voir §4.
6. **Panneautage densifié** — 11 → **19 rainures transversales**, 55 → **72 stations**. Les deux
   rainures longitudinales, le double `inset_panel` emboîté et les filtres anti-repliement
   (`min_run` / `min_edge` / `min_band`) sont conservés tels quels.

---

## 7. Limite IP — ce qui a été explicitement écarté

La planche `assets/reference/inspiration/reference_specter_9_design_sheet.png` a servi de **cible
d'intention** (ADR-0009), jamais de calque. Les trois traits porteurs de licence sont écartés,
et le sont **structurellement**, pas par omission :

| Trait exclu | Ce qui le remplace |
|---|---|
| Deux dérives inclinées en V | **rails verticaux de bout d'aile** (lames droites, alignées sur l'axe de vol, vocabulaire de rail de lancement) + **arête dorsale basse** à flancs verticaux. Aucune surface inclinée, aucun empennage. |
| Livrée tricolore blanc/bleu/**rouge vif** en bandes | palette Helios Vanguard seule : blanc cassé `#EDEAE3`, bleu profond `#1C2B5E`, or `#E4B54A`. Le rouge `#C93A31` totalise **166 triangles sur 42 520** (0,4 %), en deux marquages restreints. |
| Badge numéroté sur la dérive | **aucun chiffre, aucun texte**, nulle part sur la coque. |

Ce qui a été transposé : épaisseur, superposition des volumes, nacelles comme masses propres, nez
long à verrière en retrait, densité de panneautage, vocabulaire d'animation (volets, pétales).

Le canon de la charte §4 est respecté : triangulaire, deux propulseurs, ailes courtes, nez
central, cockpit visible original, aucune transformation humanoïde, pièces mobiles limitées.

---

## 8. Limites connues

1. **Le jeu de charnière des volets se voit.** 13 mm de fente à `y = 0,610`, visible de dessus
   comme une ligne sombre en travers de l'aile externe. C'est assumé — ça lit comme une gouverne
   articulée — mais c'est bien un écart de 13 mm au planform d'origine dans cette bande, comblé
   uniquement quand le volet est au repos. Réduire la fente imposerait de réduire le braquage.
2. **Braquage plafonné à ±13°.** Au-delà, le coin supérieur avant du volet mord la cloison
   (§4.2). Si l'animation Godot veut plus, il faudra arrondir le bord d'attaque du volet en
   demi-cylindre centré sur l'axe — faisable, mais ce n'était pas nécessaire pour les ±12°
   demandés.
3. **Coût GPU non mesuré.** +43 % de triangles (29 716 → 42 520). Je n'ai pas de moyen de lancer
   le build Windows depuis la forge : la mesure du **temps GPU par image** (accueil *et* combat,
   méthode `.claude/resources/howto-mesurer-la-perf.md`) reste à faire côté session principale.
   ADR-0011 §1 laisse penser que l'impact sera sous le bruit de mesure, mais c'est une
   présomption, pas un relevé.
4. **Le ventre est riche pour ce qu'on en voit.** Quille, écopes et leurs cadres coûtent de la
   géométrie qu'une caméra à 20° ne verra jamais. C'est délibéré : c'est ce qui fait exister le
   profil sur l'écran d'accueil et en gros plan. Si le budget devenait contraignant, c'est le
   premier endroit où couper.
5. **La verrière reste un dôme lisse** sous son cadre. La planche montre un cockpit habité
   (siège, HUD) ; rien de tel n'est modélisé, et à l'échelle du jeu ça ne se verrait pas.
6. **Aucune texture produite** (hors périmètre du brief). Les UV en projection de boîte à
   4,0 tuiles/m sont conservés tels quels, et s'appliquent désormais aussi aux quatre pièces
   mobiles — sans quoi la feuille de détail se serait arrêtée net au bord des volets.

---

## 9. Ce qui a manqué au kit — signalé, non corrigé

`aegis_kit.py` n'a **pas** été modifié. Trois manques rencontrés, par ordre d'importance :

1. **`HullContract` ne borne qu'un PLAFOND de hauteur** (`max_height_y`). Or le défaut que ce
   brief corrige est l'inverse : une coque **trop plate** reste parfaitement conforme et
   s'exporte sans un mot. J'ai dû ajouter le plancher à la main dans `main()` du script de coque
   (`MIN_HEIGHT_Y = 0.62`). Un `min_height_y` optionnel dans le contrat mettrait cette garantie
   au même endroit que les autres, pour toutes les coques.
2. **Aucune primitive de longeron à flancs verticaux.** J'ai écrit `_beam_ring` / `_beam`
   localement (section hexagonale chanfreinée, loftée) pour l'arête dorsale et la quille — les
   deux volumes qui font la superposition. `build_choir_harvester.py` et
   `build_citadel_beacon.py` portent déjà un `_rect_ring` du même esprit, et ce script en avait
   un aussi. C'est la même histoire que `add_lathe(axis=)` : trois scripts réimplémentent la même
   chose avant que ça ne remonte au kit.
3. **`moving_part()` ne sait pas vérifier le dégagement.** Le kit valide la bbox au repos, ce qui
   est déjà beaucoup (il attrape la pièce hors contrat), mais rien ne dit qu'une pièce ne
   traversera pas la coque à ±12°. J'ai fait le calcul à la main (§4.2) et rendu une pose
   déployée pour le voir. Un `MovingPart(..., axis=, limits=)` que `export_hull()` testerait par
   balayage épargnerait ce travail — et surtout, il l'imposerait.

Point positif à consigner : `moving_part()` + `export_hull(parts=…)` ont fonctionné exactement
comme annoncés, y compris l'ordre translation-puis-rotation documenté dans le kit, et la bbox
qui tient compte de l'origine déportée. `tools/blender/test_moving_parts.py` a été la meilleure
documentation disponible — l'usage y est complet et vérifié.

---

## 10. Critères d'acceptation

- [x] `./scripts/build-hull.sh --check specter_9` : **déterminisme OK** (§2)
- [x] Bbox X/Z inchangée (1,7500 × 2,4600, écart 0,00 %) ; hauteur **0,6325 m** ∈ [0,62 ; 0,68]
- [x] **42 520** triangles ≤ 60 000 ; `TEXCOORD_0` et `TANGENT` présents sur les 5 maillages
- [x] Les **10 points d'attache** conservés aux mêmes rôles (§4.4)
- [x] `Flap_L/R` et `Nozzle_L/R` : **nœuds séparés**, origine sur leur articulation (§4)
- [x] **Rendu et regardé** (ADR-0006), 4 itérations ; profil = appareil superposé ; game =
      silhouette lisible de dessus (§5)
- [x] Aucun des trois traits sous licence (§7)
- [x] Provenance : ligne `specter_9_hull` **réécrite**, CSV relu (147 lignes, 11 colonnes, aucune
      ligne mal formée)
- [x] `./scripts/check.sh` vert
