# BRIEF-0114 — Rapport de forge : Ambry cesse d'être une plaque

- **Brief** : `docs/forge/briefs/BRIEF-0114-ambry-se-lit-comme-un-asset-non-fini.md`
- **Date** : 2026-09-13
- **Outil** : Blender 5.2.1 LTS (`blender-aegis`), toujours `-t 1`
- **Livrables** : `tools/blender/build_long_cortege.py` (`build_ambry()` retravaillée + mode
  `--ambry`), `assets/imported/models/backgrounds/long_cortege.glb`,
  `docs/forge/output/BRIEF-0114-planche.png`, ce rapport
- **Périmètre respecté** : aucun `.gd`, `.tscn`, `.tres` touché ; le complexe industriel du
  tronçon 5, la poupe et le reste du bordé sont **inchangés au micron** (vérifié en relisant les
  deux binaires) ; aucun commit.

---

## 0. La réponse en une ligne

**Ambry n'a pas monté d'un millimètre et porte 3,8 fois plus de triangles**, parce que tout le
relief est allé **dans le négatif** : le radeau n'est plus une dalle, c'est un **plateau sombre à
−4,78 dans lequel des dalles ivoire sont posées**. Le même mécanisme — ne pas couvrir — donne les
deux lectures qui manquaient : le **joint** de 12 cm qui dit « c'est fait de panneaux », et le
**creux** de 0,4 à 4 m qui dit « c'est un lieu, et il a un dedans ».

| Mesure | Avant | Après |
|---|---:|---:|
| Triangles d'Ambry (objet propre) | **828** | **3 168** (×3,83) |
| Triangles dans l'emprise `x 6,90..14,10 / s 443,5..476,5` (méthode du brief) | **1 024** | **3 364** (×3,29) |
| dont **faces ivoire `AA_Hull_Ambry`** | **126** | **1 712** (×13,6) |
| Ivoire par mètre linéaire | **4,7** | **63,4** |
| Densité sur les 154 m² d'emprise | **6,7 tri/m²** | **21,8 tri/m²** |
| **Contraste local** (fenêtres 16 px, cadre proue) | **11,51** | **24,90** (×2,16) |
| **Contraste local** (fenêtres 16 px, cadre poupe) | **10,83** | **28,37** (×2,62) |
| **Luminance moyenne** (cadre proue) | **230,9** | **212,8** (−7,8 %) |
| **Luminance moyenne** (cadre poupe) | **225,0** | **220,5** (−2,0 %) |
| Sommet d'Ambry | **−3,200** | **−3,200** (identique, c'est le mât) |
| Deuxième point le plus haut | **−3,27** (serre) | **−3,53** (serre) — **26 cm gagnés** |

Le voisin de comparaison, le complexe industriel du `BRIEF-0111` validé sans réserve, fait
**18 tri/m²**. Ambry en fait maintenant **21,8** — et c'est la destination du niveau, vue de plus
près que tout le reste du corridor. **Les comptes sont rapportés, ils n'ont été contraints par
rien.**

---

## 1. Ce qui a décidé de tout : on ne pouvait pas monter, donc on a creusé

Le radeau est à `−4,48`, le plafond de construction à `−3,20`, et le mât d'antenne y touchait
déjà. Ambry est dans le plan de vol (`x 7,60..13,60`, donc `|x| ≤ 14`) : **règle A seule**, aucune
dérogation de flanc possible.

Le brief le dit et la mesure du `BRIEF-0110` le chiffre : sur cette caméra un plan rend **94 %** de
sa longueur à l'écran, une hauteur **34 %**. Ambry offre 148,5 m² de radeau à 94 % de rendement.
Tout le lot est donc allé **dans le plan et dans le négatif du plan**.

### Le plateau, et pourquoi il remplace la dalle

```
  −4,48   dessus des dalles ivoire                ← inchangé
  −4,62   fond de la coursive                     ← nouveau palier
  −4,78   fond du PLATEAU (AMBRY_TRAY_Y)          ← nouveau, 30 cm sous les dalles
  −4,84   dessous du radeau (AMBRY_RAFT_THICK)    ← inchangé
```

Une dalle ivoire est une boîte enfoncée de 4 cm dans le plateau ; **deux dalles ne se touchent
jamais**. Ce qui les sépare n'est pas creusé, il n'est simplement **pas couvert** — d'où aucun
booléen, aucune face coplanaire, et un coût qui se paie une seule fois.

- **joint de 12 cm** (5,5 px à 45,8 px/m, le plus petit trait qui se lise encore) → une ligne
  sombre de 30 cm de fond, dont on ne voit pas le fond : un trait franc ;
- **creux de 0,40 à 4 m** → le fond `AA_Greeble` `#141419` est vu en entier (à 32° hors de la
  verticale, un creux de 0,30 m montre son fond dès 0,19 m de largeur) : une fouille, une ruelle,
  un bac, une fosse.

### Neuf bandes longitudinales, et aucune ne s'arrête

Ce qui fait lire une **construction** plutôt qu'une plaque, c'est d'abord une trame. Le radeau est
découpé en neuf bandes qui courent les 27 m entiers, et les quatre zones s'inscrivent **dedans** :

| Bande | `x` | Largeur | Traitement |
|---|---|---:|---|
| rive intérieure | 7,90 → 8,26 | 0,36 | dalles, pas 1,80 m |
| **gouttière** | 8,26 → 8,46 | 0,20 | **ouverte sur le plateau** — ligne sombre continue |
| **le bâti** | 8,46 → 11,16 | 2,70 | modules, serre, fosses, fouille |
| joint | 11,16 → 11,28 | 0,12 | ouvert |
| bordure | 11,28 → 11,46 | 0,18 | dalles, pas 2,60 m |
| coursive bâbord | 11,48 → 11,96 | 0,48 | dalles à **−4,62** (en creux), pas 1,45 m |
| **caniveau** | 11,96 → 12,22 | 0,26 | **ouvert** — deuxième ligne sombre continue |
| coursive tribord | 12,22 → 12,68 | 0,46 | dalles à −4,62 |
| bordure | 12,70 → 12,88 | 0,18 | dalles |
| joint | 12,88 → 13,00 | 0,12 | ouvert |
| rive extérieure | 13,00 → 13,40 | 0,40 | dalles, pas 1,90 m + taquets |

La coursive avait été livrée d'un seul tenant au premier tirage : **1,20 m de blanc plat sur 27 m**,
c'est-à-dire la moitié du « il n'y a rien à lire ». Le caniveau central l'ouvre sur le plateau et
lui donne sa ligne. C'est visible sur la planche, vignette 2 contre vignette 1.

---

## 2. Les quatre zones — et ce qui les distingue, dispositif par dispositif

C'est le **critère principal** du brief : pas « il y a plus de matière », mais « on voit un lieu,
et il a des parties ». Trois **tranchées** de 0,55 m ouvertes jusqu'au fond du plateau barrent
3,38 m de radeau — 155 × 25 px à l'écran — et **ne coupent jamais la coursive** : la passerelle
reste continue d'un bout à l'autre, Ambry reste INTACTE.

| # | Zone | `s` | Longueur | Ce qui la fait reconnaître en une image | Tri |
|---|---|---|---:|---|---:|
| 1 | **greffe** | 446,50 → 452,30 | 5,8 m | une **fouille d'ancrage** ouverte de 4 m, traversée de trois poutres ivoire, quatre sabots d'ancrage clairs au fond ; six taquets d'amarrage sur la rive ; en avant, les **deux colliers** anthracite | 180 |
| 2 | **habitation** | 452,85 → 464,10 | 11,2 m | **quatre modules** à parapet et **toit en bac** (trappe claire dans un puits sombre), séparés par **trois ruelles en creux** enjambées d'une passerelle claire ; façade bâbord percée (porte sombre, linteau, auvent, deux fenêtres) | 612 |
| 3 | **serre** | 464,65 → 469,90 | 5,2 m | la **seule forme courbe** des 500 m et le **seul vert** (`#7C9E52`) ; sept arceaux verts, verrière, **et cinq bacs de culture verts au sol** — le vert se lit désormais aussi à plat | 276 |
| 4 | **antenne** | 470,45 → 473,50 | 3,1 m | le **mât et ses trois vergues en croix, SOMBRES sur un socle clair**, debout dans une **fosse de machinerie** ouverte | 156 |

### Le mât était ivoire sur ivoire, et il ne rendait aucun contour

Mesuré, pas supposé : sur le premier tirage, la vignette de poupe montre **une étoile blanche sur
du blanc**. Les trois vergues et le fût sont passés en `AA_Greeble` sur un socle resté clair. C'est
maintenant la seule chose qui distingue la quatrième zone de la troisième, et elle se lit d'un bout
à l'autre du cadre.

### Les colliers de greffe ne se voyaient pas non plus — et c'était la zone 1 entière

Écrits en `_surface_box()`, ils prenaient leur assise au **minimum** de quatre coins dont l'un
tombait sur la facette extérieure à `−6,66` : leur dessus sortait à **`−6,40`**, deux mètres sous le
radeau. La « greffe », première des quatre zones, n'avait **strictement rien à montrer**.

Ils sont réécrits en **trois massifs par collier**, chacun montant de *sa* peau locale jusqu'au ras
du radeau (`−4,42` / `−4,38` / `−4,34`), avec trois brides sombres en travers. Une bride qui pince
le bordé, et **qu'on voit arriver avant Ambry elle-même** — ce qui est exactement ce qu'on veut
d'une révélation.

⚠️ Ils restent en **`AA_Hull` anthracite** : ils appartiennent au vaisseau, pas à l'avant-poste.
Le **pas d'appontage** aussi (1,84 × 3,40 m, quatre bandes sombres) : c'est sa valeur SOMBRE qui le
fait lire comme un pas.

---

## 3. Les douze béquilles : elles se voient, et par leurs DEUX bouts

Le brief : *« une idée qu'on ne voit pas n'est pas une idée livrée »*. Constat mesuré avant de
toucher à quoi que ce soit : **à 70° de plongée, rien sous un radeau de 5,5 m n'est visible.**

Le rayon de vue qui passe par l'arête basse extérieure du radeau `(13,40 ; −4,84)` ressort à
`x = 14,56` quand il atteint la peau à `y = −6,47` — au-delà de la zone de garde (`14,10`). **Tout
le dessous du radeau, sans exception, est dans son ombre propre.** Rallonger les béquilles,
les élargir ou les déplacer sous le radeau n'y aurait rien changé.

Les douze sont donc devenues des **traverses qui sortent par leurs deux bouts** :

| | Quoi | Pourquoi c'est visible |
|---|---|---|
| **bâbord** | une **tête** de 0,22 m de large qui déborde du bord intérieur, **recoupée à douze longueurs différentes** (0,15 à 0,44 m), posée sur le pont du vaisseau par son **sabot** | le bord intérieur fait face à la caméra : rien ne l'occulte. Douze languettes sombres inégales sur 27 m de tôle claire |
| **tribord** | une **béquille** qui descend sur la facette extérieure jusqu'à `x` 13,50 → 13,63 (toutes différentes, donc **douze longueurs différentes**, 2,0 à 2,3 m) | ses 35 premiers centimètres passent **au large** de l'ombre du radeau : le rayon limite est à `x = 13,94` à `y = −5,15`. Douze dents sombres le long de la rive |

L'inégalité **est** le sujet — c'est elle qui dit qu'on a posé cela sur un vaisseau qui n'était pas
fait pour le recevoir. Elle se voit désormais deux fois, sur les deux bords, à 45,8 px/m. Vignettes
2 et 4 de la planche (et l'élévation, où les douze descentes sont alignées sous le radeau).

---

## 4. Rien n'a monté — et la pièce a même rendu 26 cm de ciel

Mesuré **sur le binaire produit**, pas sur l'intention :

| | Avant | Après |
|---|---:|---:|
| mât d'antenne | −3,200 | **−3,200** |
| parapet des modules | −3,29 | **−3,62** |
| faîte de la serre | −3,27 | **−3,53** |
| dessus du radeau | −4,48 | −4,48 |
| fond du plateau | — | **−4,78** |
| **plafond de construction (règle A)** | **−3,20** | **−3,20** |

`_assert_build_ceiling()` (bloquant, il lit le `.glb` produit, translation comprise) et le garde
local de `build_ambry()` passent tous deux. Le sommet vaut **exactement** `BUILD_CEILING_Y`, comme
avant : c'est le mât, et il est par construction la chose la plus haute des 500 m.

Le **deuxième** point le plus haut est descendu de 26 cm : les modules se dressent maintenant depuis
le fond du plateau (`−4,78`) et non depuis le radeau, ce qui leur rend 30 cm de hauteur **utile**
tout en les faisant culminer *plus bas*. Le « ciel » disponible pour ce que le jeu posera plus tard
sur Ambry est donc **plus grand qu'avant**, pas plus petit.

---

## 5. Le cadre — rien ne sort par le haut de l'image

Ambry est dans le plan de vol : **règle A uniquement**, la règle B des flancs de poupe ne
s'applique pas. Deux contrôles, tous deux verts :

- **plafond** : sommet `−3,200 ≤ −3,20` (mesuré sur le binaire, ci-dessus) ;
- **banc** : `test_the_front_edge_of_ambry_is_read_from_the_hull` — **le bord avant lu dans le
  binaire vaut `s = 446,500`**, contre `446,5 ± 1` exigé. `./scripts/check.sh` est vert :
  **1 034 tests, 8 842 assertions, 0 échec**, dont
  `test_the_ambry_line_waits_until_ambry_is_in_the_frame` et
  `test_nothing_of_the_hull_rises_into_the_play_field`.

> ⚠️ **C'est la contrainte qui a le plus pesé sur le plan.** `CortegeRoot._slot_front_edge()` lit le
> `z` local le plus grand des faces `AA_Hull_Ambry` : **aucune face ivoire ne peut se poser en avant
> de `s = 446,50`**, sous peine de décaler la réplique de Lyra. Les colliers, eux, sont en `AA_Hull`
> et débordent librement jusqu'à `s = 445,05` — c'est même devenu leur rôle : annoncer Ambry avant
> qu'elle n'entre.

**Les 42 repères du corridor sont identiques au micron** entre les deux binaires — vérifié en
comparant les translations de nœuds des deux `.glb`, pas en relisant la table : dix-sept tourelles,
sept ponts, cinq nœuds, douze repères de conduite, cinq du complexe, et le repère `Ambry` lui-même
(`+10,65 ; −4,200 ; −60,00`).

---

## 6. Les mesures d'image — avant/après, même cadrage, mêmes fenêtres

Le masque de mesure est **calculé, jamais estimé** : la projection du radeau (`x 7,90..13,40`, au
plan `y = −4,48`) rasterisée puis **érodée de 3 px**. C'est la seule fenêtre strictement identique
avant et après, parce qu'elle ne dépend d'aucune géométrie qui a changé. Un rectangle aligné sur
les axes aurait mordu sur le bordé anthracite et fait chuter la luminance **des deux côtés** — donc
menti dans le sens flatteur.

| Vignette (1920 × 1080) | Pixels | Luminance | Contraste local 16 px | Fenêtres |
|---|---:|---:|---:|---:|
| avant — cadre proue (`s 439,5..466,0`) | 156 021 | 230,9 | **11,51** | 549 |
| **après — cadre proue** | 156 021 | **212,8** | **24,90** | 549 |
| avant — cadre poupe (`s 454,0..480,5`) | 223 961 | 225,0 | **10,83** | 803 |
| **après — cadre poupe** | 223 961 | **220,5** | **28,37** | 803 |

- **Contraste local : ×2,16 et ×2,62.** C'est très exactement le défaut que le brief décrit
  (« presque plate ») et c'est ce que le lot corrige.
- **Valeur claire conservée.** La luminance perd **7,8 %** au plus. Le seuil du brief (130 sur une
  base de 165) autorise **−21 %** ; on est à un tiers de la marge. La décision de l'opérateur — *la
  valeur claire reste* — est tenue avec de la réserve.

> ⚠️ **Ces chiffres ne sont pas comparables aux 17,4 / 6,7 du brief**, qui sont mesurés sur une
> capture de jeu avec le post-traitement rétro (lift 1,25, bloom). Ce qui est comparable, et ce que
> le brief demande, c'est le **couple avant/après mesuré à l'identique** — ci-dessus.
>
> ⚠️ **Et la planche est CONSERVATRICE.** `_plate_lights()` ne projette aucune ombre (c'est délibéré
> depuis le `BRIEF-0089` : valider un relief qui ne se lirait *que* par ses ombres serait un piège).
> En jeu, `directional_shadow_max_distance` vaut 40 et Ambry est à ~20 m de la caméra : **chaque
> joint et chaque creux recevra une ombre portée que la planche ne montre pas.**

---

## 7. Les comptes, rapportés et non contraints

### Par famille (compteur du générateur, triangles réels, n-gones comptés comme triangulés)

| Famille | Tri | Part |
|---|---:|---:|
| bandes longitudinales (rives, bordures, coursive, caniveau) | 744 | 23,5 % |
| zone habitation (4 modules complets) | 612 | 19,3 % |
| **traverses** (12 têtes + 12 sabots + 12 béquilles) | 432 | 13,6 % |
| colliers de greffe (6 massifs + 18 brides) | 288 | 9,1 % |
| zone serre (verrière, arceaux, bacs, pignons) | 276 | 8,7 % |
| garde-corps (20 montants) | 240 | 7,6 % |
| zone greffe (fouille, poutres, sabots, taquets) | 180 | 5,7 % |
| rive intérieure (dalles des quatre zones) | 168 | 5,3 % |
| zone antenne (socle, fosse, mât, vergues) | 156 | 4,9 % |
| pas d'appontage | 60 | 1,9 % |
| plateau | 12 | 0,4 % |
| **TOTAL** | **3 168** | **21,3 tri/m²** |

### Par slot, dans le binaire, emprise du brief

| Slot | Avant | Après |
|---|---:|---:|
| **`AA_Hull_Ambry`** (les faces ivoire) | 126 | **1 712** |
| `AA_Greeble` | 573 | 1 103 |
| `AA_Hull` (colliers + pas d'appontage) | 159 | 237 |
| `AA_Glass` | 72 | 168 |
| `AA_Marking_Red` (la serre) | 86 | 144 |
| `AA_Panel` | 8 | **0** — voir §9 |
| **TOTAL** | **1 024** | **3 364** |

*(l'écart de 196 tri entre 3 168 et 3 364 est la peau du bordé que la boîte d'emprise recouvre ;
elle était comptée de la même façon dans les 1 024 du brief — la comparaison est donc à méthode
constante.)*

### Coût, à l'échelle du corridor

| | Avant | Après |
|---|---:|---:|
| `Section_05` | 12 686 tri (70,5 % du budget) | **15 026** (83,5 %) |
| corridor entier | 51 642 tri (57,4 %) | **53 982** (60,0 %) |
| `.glb` | 2 915 612 o | **3 152 288 o** (+8,1 %) |

**Aucun budget n'a été appliqué** (décision de l'opérateur du 2026-09-08). Ce qui a été appliqué,
c'est l'autre règle du brief, celle qui n'est pas un budget : *un détail de 3 cm fait 1,4 pixel*.
Le plus petit trait posé est le **joint de 12 cm** (5,5 px) ; rien n'est plus fin.

---

## 8. Textures et UV (ADR-0028)

**Aucune image nouvelle, aucune image dans le `.glb`** — le harnais `_audit()` le vérifie et il est
bloquant (`baseColorTexture`, `normalTexture`, `images`…). Le brief l'avait tranché : le manque
était du relief, pas de la peau. Les quatre cartes `ambry_hull_*` existantes restent valables : la
géométrie nouvelle vit sur les **huit slots déjà déclarés**.

- **Dépliage** : `ak.box_project_uv(ambry, 0,700 tuile/m)`, **inchangé** — le brief ne demande pas
  de dépliage continu pour cette pièce, et Ambry garde son échelle propre (1,43 m par tuile contre
  5,00 m pour le bordé).
- **`TEXCOORD_0` compté, jamais supposé** : `_audit()` compte les primitives du `.glb` et échoue si
  une seule en manque. Les **8 primitives** du `Section_05` portent `TEXCOORD_0` **et** `TANGENT`.
- **Densité de texels mesurée** (mesure Blender, béquilles comprises) : **0,522 à 0,700 tuile/m,
  moyenne 0,699, anisotropie max 1,34** (avant : 0,609 à 0,700 / 0,699 / 1,15). Le minimum et
  l'anisotropie ont bougé pour une seule raison : les **flancs en dépouille** des dalles et des
  modules (3 à 8 cm de retrait). Une face inclinée de θ reçoit une projection en boîte comprimée en
  `cos θ` ; à 1,34, l'écart reste **sous la demi-tuile** et invisible sur le damier.
- **Planche au damier UV** : vignette 5. Grande case = 1,43 m, petite = 17,9 cm. Les cases restent
  carrées sur le radeau, les modules, la coursive et les rives — aucun étirement.

---

## 9. Ce que j'ai changé sans que le brief le demande, et pourquoi

1. **Plus une seule face `AA_Panel` sur Ambry** (8 tri avant, 0 après). Le violet `#452663` est la
   couleur de panneau **de faction de l'Unisson**. Quatre capots violets sur les toits des modules
   étaient, au premier tirage, **la chose la plus visible de toute la pièce** — exactement la
   lecture « décals arbitraires » que l'opérateur a déjà signalée ailleurs, et exactement ce que
   l'interdit de magenta cherche à éviter : *l'absence des couleurs de l'Unisson est ce qui dit
   qu'Ambry n'est pas de ce vaisseau*. Les capots sont devenus des **trappes ivoire dans un puits
   sombre**. Si le concepteur juge que le violet doit revenir, une seule ligne suffit.
2. **Les colliers et le mât ont changé de matériau de rendu, pas de rôle** (§2). Les colliers
   restent `AA_Hull` anthracite comme le brief l'exige ; seul leur **plan** a changé. Le mât est
   passé de `AA_Hull_Ambry` à `AA_Greeble` : ivoire sur ivoire, il ne rendait aucun contour.
3. **Le mode `--ambry`** a été ajouté au générateur (planche avant/après, dessus, élévation,
   damier, **et les mesures de luminance/contraste**). Il vit dans `tools/`, ce que le brief
   autorise, et il rend le critère chiffré **reproductible** au lieu d'être une affirmation.

---

## 10. Limites connues

### 10.1 ⚠️ Les slots du bordé portés par Ambry reçoivent leurs cartes 3,5 fois trop fines

**C'est un défaut préexistant que ce lot amplifie, et il est côté code — donc hors de mon
périmètre.** `CortegeSkin.apply()` (`scripts/fx/cortege_skin.gd`, l. 140) choisit l'échelle d'UV
**par nom de matériau** :

```gdscript
var scale := AMBRY_UV_SCALE if name == &"AA_Hull_Ambry" else HULL_UV_SCALE
```

Or l'objet Ambry entier est déplié à **0,700 tuile/m**, bordé à 0,200. Toute face d'Ambry qui n'est
pas `AA_Hull_Ambry` — `AA_Greeble`, `AA_Hull`, `AA_Glass`, `AA_Marking_Red` — reçoit donc la carte
du bordé **3,5 fois trop fine**. Le commentaire du `BRIEF-0090` dans ce même fichier décrit
précisément ce piège, mais la garde qu'il a posée ne couvre qu'un slot sur cinq.

| Slot d'Ambry concerné | Avant | Après |
|---|---:|---:|
| `AA_Greeble` | 573 tri | **1 103** |
| `AA_Hull` | 159 | 237 |
| `AA_Glass` | 72 | 168 |
| `AA_Marking_Red` | 86 | 144 |

Sur les fonds de creux sombres, personne ne le verra. Sur les **arceaux verts de la serre** et le
**pas d'appontage**, qui sont larges et clairs, c'est visible dès que les cartes du bordé seront
posées. Deux corrections possibles, l'une et l'autre côté concepteur :

- un **neuvième slot déclaré** (`AA_Greeble_Ambry`) plus son entrée dans `CortegeSkin.SKINS` —
  c'est exactement ce qu'a fait le `BRIEF-0090` pour le huitième ; ou
- une échelle **par maillage** plutôt que par nom de matériau, ce qui règle le cas une fois pour
  toutes.

Je n'ai pas ouvert le neuvième slot de mon propre chef : il aurait été **muet** en jeu
(`CortegeSkin` ne le connaît pas), donc livré sans carte, et c'est une décision d'intégration.

### 10.2 Les modules d'habitation font 1,04 m de haut

Ambry est un avant-poste de quatre-vingts personnes ; à 1 unité = 1 m, ses modules sont des
**casemates basses** (fond du plateau `−4,78` → parapet `−3,62`). Le plafond de vol l'impose et
la règle A l'interdit de discussion. Le lot a gagné 30 cm en faisant partir les modules du fond du
plateau au lieu du radeau — c'est tout ce qui était disponible. Les portes font 0,68 m.

### 10.3 Un cadre de jeu ne montre que 26,4 m, Ambry en fait 27 (30 avec ses colliers)

Il n'existe **aucun cadrage** qui montre Ambry entière à la caméra du jeu. La planche en donne donc
deux (proue et poupe), et la vue de dessus pour le plan d'ensemble. Ce n'est pas une limite du lot :
c'est ce que le joueur vivra, et c'est aussi pourquoi les zones devaient être lisibles **une par
une**, ce qui a guidé leur longueur (5,8 / 11,2 / 5,2 / 3,1 m).

### 10.4 Les tranchées ne coupent pas la coursive

Délibéré : « passerelle continue d'un bout à l'autre » fait partie de ce qui rend Ambry INTACTE.
Elles barrent 3,38 m des 5,50 m du radeau. À l'écran c'est suffisant (155 px), mais si le
concepteur veut une séparation totale, il faudra renoncer à la continuité de la coursive — et ce
serait un arbitrage de sens, pas de forme.

---

## 11. Déterminisme et vérifications

- **Trois exécutions, zéro octet divergent** :
  `b11d7ecfec96921fffb4a558bc0acd42bd60f9b134fb39adf888fd069353b0ac` — identique aux trois
  lancements (`blender-aegis -t 1 -b`, comme l'impose `scripts/build-hull.sh`).
- **Tous les harnais bloquants du générateur passent** : plafond de construction et plafond de vol,
  jonctions de tronçons, contrat de noms, les 30 marqueurs, UV et tangentes sur 100 % des
  primitives, largeurs, couleurs réservées aux tirs, absence de texture et d'image, orientation des
  normales, gardes de tourelle, dégagement du complexe, emprise de garde d'Ambry, les sept
  ouvertures réellement percées.
- **`./scripts/check.sh` : ALL GREEN** — 1 034 tests, 8 842 assertions, 0 échec, 0 erreur
  d'analyse.
- **Les 42 repères du corridor sont inchangés au micron** (comparaison des deux binaires).

## 12. La planche

`docs/forge/output/BRIEF-0114-planche.png` — 1920 × 6300, SEPT vignettes :

| # | Vue | Ce qu'elle prouve |
|---|---|---|
| 1 | **AVANT**, caméra du jeu, cadre proue | la plaque blanche que l'opérateur a signalée deux fois |
| 2 | **APRÈS**, **même cadrage** | greffe puis habitation : fouille, ruelles, joints, têtes de traverses, pas d'appontage |
| 3 | **AVANT**, caméra du jeu, cadre poupe | idem, moitié arrière |
| 4 | **APRÈS**, **même cadrage** | habitation, serre, antenne : la croix sombre du mât, les bacs verts, les tranchées |
| 5 | **Damier UV** à la perspective du jeu | 0,700 tuile/m sur Ambry contre 0,200 sur le bordé ; aucune image dans le `.glb` |
| 6 | **De dessus** (31 m, orthographique) | **le plan** — les quatre zones et les trois tranchées d'un seul regard |
| 7 | **Élévation tribord** (31 m) + dalle du plafond de vol | rien au-dessus de `−3,20` ; les douze béquilles alignées sous le radeau |

Le Specter-9 réel est à sa place de jeu sur les quatre vignettes de caméra (ADR-0025) : les balles
doivent se lire par-dessus, et elles se lisent.
