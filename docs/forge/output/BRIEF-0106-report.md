# BRIEF-0106 — La poupe du Long Cortège : compte-rendu de forge

- **Brief** : [`docs/forge/briefs/BRIEF-0106-la-poupe-du-long-cortege.md`](../briefs/BRIEF-0106-la-poupe-du-long-cortege.md)
- **Agent** : `asset-forge` — Blender 5.2.1 LTS, `-t 1`
- **Date** : 2026-09-07
- **Porte de qualité** : `./scripts/check.sh` → **ALL GREEN** (959 tests, 7 734 assertions, 0 échec)

## Livrables

| Fichier | Contenu |
|---|---|
| `tools/blender/build_stern.py` | le générateur — **il est la source** (`ADR-0008`), il importe `build_long_cortege` pour son anneau de jonction |
| `assets/imported/models/backgrounds/stern_hull.glb` | la carène, 234 Kio, `sha256 067f5c73…5b8c168c` |
| `docs/forge/output/BRIEF-0106-planche.png` | six vignettes rendues **à la caméra du jeu**, les trois groupes réels montés |
| `assets/licenses/ASSET_PROVENANCE.csv` | ligne `stern_hull` |
| `assets/imported/models/backgrounds/stern_hull.glb.import` | généré par `./scripts/check.sh` — la convention du dépôt est de le committer |

```sh
blender-aegis -t 1 -b -noaudio -P tools/blender/build_stern.py            # le binaire
blender-aegis -t 1 -b -noaudio -P tools/blender/build_stern.py -- --plate # + la planche
```

---

## 1. ⚠️ La contrainte qui a décidé de toute la forme : les trois emprises se recouvrent

C'est le fait dominant du brief, et il n'y était pas écrit. Le critère d'acceptation interdit
toute géométrie dans **10 × 15 m plus 0,5 m de garde** autour de chaque berceau, aux stations
`x = 0` et `x = ±10,28`. Les demi-emprises valent donc `5,50` en X — et **5,50 + 5,50 = 11,00 m
pour un entraxe de 10,28**.

Les trois prismes ne sont pas trois zones : **ils se recouvrent de 0,72 m et n'en forment
qu'une**.

```
   |x| <= 15,78   et   |z| <= 8,00      ->  rien au-dessus du pont (-11,85)
```

Trois conséquences, toutes structurelles :

1. **« Des masses hautes ENTRE les berceaux » (§2) est géométriquement impossible.** Il n'y a
   pas un mètre carré libre entre deux berceaux. Le relief vertical est reporté sur les deux
   seules zones libres : les **flancs** (`|x| ≥ 16,20`) et le **massif arrière** (`z ≤ −8,60`).
2. **La première marche d'évasement ne peut pas être progressive.** La coque doit passer de
   12,04 m de demi-largeur à plus de 15,78 m *en une seule station*, et cette station est
   `s = 500` — c'est-à-dire la jonction elle-même.
3. **L'artère ne peut pas se terminer dans le bassin.** Tout ce qui y dépasserait du pont
   mordrait un berceau. Son collecteur est donc posé de l'autre côté de la jonction.

### Et la marge à l'avant est **exactement nulle**

`508,0 − 8,00 = 500,0`. Le bord avant de l'emprise tombe **au micron sur l'anneau de jonction**
que le brief impose par ailleurs de reproduire à l'identique. L'anneau du corridor est donc,
lui-même, dans le plan limite de l'emprise.

C'est mesuré et c'est sans échappatoire : la face avant de la poupe est **rigoureusement plane**
(`z = 8,000`), parce que son ombre au sol est alors un segment d'aire nulle. Une première
version portait un chanfrein de 0,90 m : le harnais a compté **17,79 m² de décor au-dessus du
pont** dans les emprises, et il avait raison.

Le relief que cette face ne peut pas porter est repris **en avant d'elle**, par les deux
épaulements de `build_shoulders()` (`z ∈ [8,00 ; 9,40]`, hors emprise).

---

## 2. La jonction — le critère qui prime

`build_stern.py` **importe** `build_long_cortege._half_profile(500.0, side)`, bord par bord.
Aucune cote du corridor n'est recopiée. Le harnais `_assert_junction()` relit le `.glb`
**produit** et compare les 48 sommets :

| Mesure | Valeur |
|---|---|
| Sommets comparés | **48 / 48** |
| Écart maximal | **6,56 × 10⁻⁷ m** (0,66 µm) |
| Demi-largeur à la jonction | **12,040 m** |
| Station | `s = 500,0` → `z_local = +8,00` |

L'écart résiduel est la précision du `float32` du glTF, pas une dérive : les valeurs d'auteur
sont bit à bit celles du module.

⚠️ Le harnais compare **les deux bords séparément**. À `s = 500` la coque se trouve être
symétrique (`_asym(500)` rend `(1,00 ; 1,00)`), mais rien ne le garantit demain : si un bord
bougeait sans l'autre, le build échouerait au lieu de livrer une marche.

**Le repère.** `cortege_root.gd` pose le nœud `Stern` à `z = −508` sous le même parent que les
cinq tronçons. Le repère local du `.glb` est donc `z_local = 508 − s` : `+8` à la jonction,
`−12` à l'arrière.

---

## 3. L'évasement — profil de largeur station par station

Relevé **sur le binaire**, par coupe de chaque triangle au plan de la station (et non par
proximité de sommets — la peau est un loft à dix anneaux, une mesure par sommets rendait zéro
sur six stations).

| s | demi-largeur | bouche du bassin | arête de rive |
|---|---|---|---|
| 500,0 *(corridor)* | **12,04** | — | −4,58 … −5,10 (pont du corridor) |
| 500,0 … 505,3 (B1) | **17,10** | 16,40 | **−6,60** |
| 505,3 … 511,0 (B2) | **18,50** | 17,30 | **−5,60** |
| 511,0 … 520,0 (B3) | **19,90** | 18,20 | **−4,60** |
| 520,0 (arrondi arrière) | 18,31 | — | — |

Trois marches franches (0,12 m de transition), donc **28,1 m de large au corridor contre
39,8 m à la poupe** — un facteur 1,65.

⚠️ **Ce ne sont pas seulement les bords qui bougent.** Une première version ne faisait varier
que l'étagère extérieure : le rebord restait à 17,00 dans les trois bandes et, rendue de dessus,
la poupe était un **rectangle** — l'évasement ne se lisait nulle part. Ici les quatre cotes
bougent ensemble à chaque marche (pied de paroi, arête de rive, terrasses, bord) **et l'arête de
rive monte de 1,00 m à chaque fois**. C'est ce qui donne à chaque marche sa **face horizontale**,
seule chose qu'une caméra qui plonge à 70° distingue d'une pente. Vignette 4 de la planche.

---

## 4. Triangles — 2 514 sur un budget de 20 000 (12,6 %)

| Famille | Triangles | Ce qu'elle fait |
|---|---|---|
| `skin` | 910 | le loft : 10 anneaux de 48 points, de la jonction au massif arrière |
| `towers` | 524 | les deux tours d'échange thermique du massif arrière |
| `manifold` | 436 | le collecteur d'artère, ses colliers, sa section vitrée |
| `rim_clamps` | 312 | la chaîne de brides du rebord + les rails de guidage |
| `pylons` | 240 | les quatre pylônes de rive |
| `shoulders` | 96 | les deux épaulements avant |
| `glow` | 48 | les tirets encastrés de l'anneau de distribution |
| `apron` | 12 | la dalle d'assise, d'un seul tenant |

**Rien n'a dû être coupé.** Le budget n'a pas été la contrainte de cette pièce — l'emprise l'a
été. Les 17 486 triangles restants sont disponibles si le concepteur veut densifier ; le rapport
signale plus bas les deux endroits où ça vaudrait la peine.

---

## 5. Les emprises, mesurées sur le binaire

Le harnais ne teste pas des sommets : il **découpe** chaque triangle par le demi-espace
`y > −11,85`, puis rogne son ombre `(x, z)` par le rectangle d'emprise (Sutherland-Hodgman) et
somme l'aire restante. Un triangle peut traverser une emprise sans qu'aucun de ses trois sommets
n'y soit ; un test de sommets ne l'aurait pas vu.

| Mesure | Valeur | Limite |
|---|---|---|
| Décor au-dessus du pont dans les emprises | **0,000000 m²** | 0 |
| Marge latérale minimale *(hors plan de jonction)* | **0,240 m** | ≥ 0 |
| Marge longitudinale minimale *(idem)* | **0,450 m** | ≥ 0 |
| Distance à l'enveloppe **réelle** d'un berceau | **0,872 m** | — |
| `y_max` | **−3,292 m** | ≤ −3,20 |
| `y_min` | **−12,600 m** | ≥ −12,60 |
| Assise plane, d'un seul tenant | **31,90 × 16,15 m** | ≥ 10 × 15 par groupe |

Le `y_min = −12,600` **est** le point de quille du corridor : il vient de l'anneau de jonction
importé, pas d'une valeur écrite ici.

### L'assise est d'un seul tenant, et c'est aussi une mesure

Une version à trois dalles (une par groupe, joint dans le creux entre deux berceaux) a été
construite puis abandonnée. Le créneau disponible est trop étroit :

| Contrainte | Borne |
|---|---|
| Le brief demande 10 m d'assise par berceau | central jusqu'à `x = 5,00` · latéral à partir de `5,28` |
| Le berceau **central** en mesure en réalité **10,32** | il va jusqu'à `5,16` |
| Le berceau **latéral** commence à | `5,41` |

Satisfaire à la fois la cote du brief **et** l'enveloppe réelle des pièces ne laisse que
`[5,16 ; 5,28]`, soit **0,12 m** — un trait, pas un joint, et une assise à 0,00 m de marge sous
un berceau latéral. La dalle fait donc **31,90 × 16,15 m d'un seul tenant**, avec 5,95 m de
marge latérale sur la cote du brief.

⚠️ **Cote à faire suivre** : le brief écrit « une assise plane d'au moins 10 × 15 m sous chaque
berceau », mais le berceau central mesure **10,32 m** de large à l'échelle du jeu
(`11,19 × 0,87 × 1,06`). La cote du brief est 32 cm plus étroite que la pièce qu'elle doit
porter.

Le plus petit défaut corrigé de cette pièce tenait dans un `max()` : sans lui, la sous-chine
rentrait à `wmax − 1,90` et, en bande avant, l'arête 20 → 21 traversait le plan du pont à
`|x| = 15,63` — **15 cm dans l'emprise, sur 1,57 m²**, sous un berceau latéral. Invisible à
l'œil, refusé au micron.

---

## 6. L'émissif : une seule installation, et elle s'éteint d'un bloc

`CortegeStern.blackout()` éteint tout ce qui porte `AA_Emissive_Engine`. Le slot n'est porté
que par **la jonction d'artère prise comme un tout** :

- le **collecteur** (`z ∈ [8,15 ; 9,45]`), avec ses trois sections vitrées ;
- l'**anneau de distribution** qui en part, encastré dans la gorge du pont à `y = −11,99`.

| Mesure | Valeur |
|---|---|
| Aire `AA_Emissive_Engine` | **19,8 m²** |
| Part de l'aire totale | **0,35 %** |
| Autres slots | `AA_Greeble` 49,49 % · `AA_Hull` 47,61 % · `AA_Panel` 2,53 % · `AA_Trim` 0,03 % |

⚠️ **Il a fallu diviser cette aire par deux après l'avoir regardée.** La première version portait
un ruban **continu** de 0,30 m : rendu à la caméra du jeu, il dessinait un **rectangle néon**
autour du pont, la chose la plus lumineuse d'un cadre où le joueur doit lire dix verrous. C'est
mot pour mot le défaut que le `BRIEF-0094` a corrigé sur l'arête dorsale du corridor. Le ruban
est désormais **tireté** (1,30 m de trait, 1,45 m de vide), large de 0,18 m, et **encastré de
0,15 m sous le plan du pont** — la géométrie l'ombre d'elle-même. Vignettes 1 et 5.

L'ivoire `AA_Trim` a subi la même correction : le chapeau du collecteur en portait 3,7 × 1,5 m,
un rectangle blanc au milieu du cadre. Il n'en reste qu'un bandeau de 0,18 m (0,03 % de l'aire).

**La preuve du contrat est la vignette 5** : seul `AA_Emissive_Engine` y est éteint. Ce qui
resterait allumé serait rangé ailleurs — et rien, ni erreur ni test, ne le signalerait.

---

## 7. Texture et UV (`ADR-0028`)

**Aucune texture livrée. Zéro image embarquée** — le harnais échoue le build si `images` n'est
pas vide. Régime PBR par facteurs, comme tout le niveau.

Dépliage : **projection en boîte à 0,20 tuile/m**, soit **5,00 m par tuile** — la densité
*exacte* de la peau du corridor, **lue** dans `blc.HULL_TEXELS_PER_METER` et non recopiée.

| Mesure sur le binaire | Valeur |
|---|---|
| Densité moyenne | **0,1992 tuile/m** (5,021 m/tuile) |
| Anisotropie maximale | **1,511** (borne théorique de la méthode : √3 = 1,732) |
| `TEXCOORD_0` | **présent sur 5 primitives / 5**, compté sur le `.glb` |

⚠️ **La projection est calculée dans un repère décalé de +2,00 m en z**, et ce n'est pas un
détail. `box_project_uv` écrit `v = z_local × 0,20` sur toutes les faces dont la normale domine
en X ou Y — c'est-à-dire le pont et les flancs. À la jonction, le tronçon 5 finit à `v = −20,00`
(entier) et la poupe repartirait à `v = 1,60` : **0,6 tuile de saut, pile à l'endroit qu'on
regarde**. Avec le décalage, la poupe y vaut `v = 2,00` — en phase. Même piège que
`HULL_TILES_PER_SECTION`, même remède.

Le brief demandant une projection en boîte (et non un dépliage continu), il n'y a **pas de
couture à situer** : les îlots se recouvrent par construction et la position d'une face sur la
carte n'a aucune importance. La **vignette 6** donne quand même le damier à la perspective du
jeu — c'est là qu'un étirement se verrait.

---

## 8. Animation (`ADR-0046` §6)

**Figée**, comme le brief le déclare. Le `.glb` ne contient aucune `animation` ni aucun
`Empty` : ce qui bouge (nacelles, berceaux, verrous, bras) est livré et animé par
`reduce_stern.py` au `BRIEF-0105`.

---

## 9. Les planches : trois retenues, six laissées

Le brief en propose dix et prévient que ce n'est pas une liste de courses. Chacune des retenues
sert **une installation bornée**, conformément à la règle issue du `BRIEF-0094` (« un module de
relief ne se pose que dans l'emprise d'une installation ») :

| Planche | Ce qui en est transposé | Où |
|---|---|---|
| `asset07` pylône spatial | fuseau étagé à quatre gradins, socle débordant, bandeau de flanc | 4 pylônes de rive, bandes 2 et 3 |
| `asset08` bride de moteur | segments répétés, blocs de verrouillage, rails de guidage | la chaîne de brackets du rebord de bassin |
| `asset08` conduite d'énergie | tube octogonal, colliers de serrage, section vitrée | le collecteur d'artère |
| `asset08` tour thermique *(4ᵉ)* | socle évasé à contreforts, fût cannelé, diffuseur en cône | les 2 tours du massif arrière |

**Laissées** : flexibles, cryogénie, collier, anneau de maintenance, réseau de refroidissement,
déflecteur d'échappement. Le déflecteur mérite une mention : il est **animé** et se monte sur le
berceau — il appartient à une pièce mobile, pas à la structure, et son emplacement naturel est
au cœur de l'emprise interdite.

**Deux transpositions méritent d'être justifiées.**

- *La bride ne peut pas ceinturer une alvéole.* Un collier autour d'un berceau est exactement ce
  que l'emprise interdit. La chaîne borde donc **le bassin entier** : un seul geste au lieu de
  trois impossibles. Ses brackets débordent de 0,50 m vers l'intérieur et descendent de 2,60 m
  le long de la paroi — c'est ce qui nervure une paroi de 7 m qui, rendue nue, était deux grands
  trapèzes gris sans un pli.
- *Le pylône fait 24 m sur sa planche ; il en fait 8,5 ici.* Entre le pont de poupe (−11,85) et
  le plafond de construction (−3,20) il y a 8,65 m, pas 24. C'est la silhouette (fuseau étagé,
  plan rectangulaire, gradins) qui est transposée, pas l'échelle.

---

## 10. Déterminisme

Trois exécutions consécutives, `-t 1` :

```
067f5c738a0192cdc167dd769bbb93e74cef46bdba3f830360b9acd85b8c168c
067f5c738a0192cdc167dd769bbb93e74cef46bdba3f830360b9acd85b8c168c
067f5c738a0192cdc167dd769bbb93e74cef46bdba3f830360b9acd85b8c168c
```

**Zéro octet divergent.** Aucun aléa dans le fichier, seedé ou non.

---

## 11. Ce qui a été rendu et regardé (`ADR-0006`)

`docs/forge/output/BRIEF-0106-planche.png`, six vignettes 1920 × 1080, rig **importé** de
`build_long_cortege` (caméra `(0 ; 14 ; 5)`, FOV 62 vertical, trois directionnelles, aucune ombre
portée) :

1. **caméra du jeu, les trois groupes montés** — nacelles, berceaux, dix verrous, bras ;
2. **la même, sans les groupes** — ce que la carène fait toute seule ;
3. **la jonction `s = 500` en vue rasante** — la vue que personne ne pense à demander ;
4. **de dessus** — l'évasement en marches et les trois emprises laissées libres ;
5. **blackout** — seul `AA_Emissive_Engine` éteint ;
6. **damier UV** à la perspective du jeu.

⚠️ **La poupe y est rendue à sa vraie place, `z = −6,47`, et non à l'origine.**
`cortege_flyby.gd` immobilise le défilement à `LEAD_IN + station − hold`, ce qui pose le centre
des berceaux à `z = −hold_plane_y`. La planche du `BRIEF-0105` cadrait à `z = 0`, soit 6,47 m
trop près. Le cadre lui-même est inchangé (il ne dépend que de `deck_y`) : **58,77 m et
32,7 px/m**, les deux chiffres du brief, revérifiés.

Trois corrections viennent **de ces rendus** et d'aucun calcul : le ruban émissif continu, le
chapeau ivoire, et l'évasement qui ne se lisait pas de dessus. Elles sont documentées à leur
place dans le script.

---

## 12. ⚠️ Ce qui n'a pas pu être tenu, et ce qui contredit une cote du jeu

### 12.1 Les masses hautes « entre les berceaux » (brief §2) — impossible

Démontré au §1 : l'union des trois emprises est continue de `x = −15,78` à `+15,78`. Aucune
géométrie ne peut se dresser entre deux berceaux sans violer le critère d'acceptation, qui prime.
**Le relief vertical est donc entièrement latéral et arrière.** Les deux tours thermiques du
massif arrière sont posées dans les **créneaux entre les nacelles** (`x = ±5,40`), assez loin en
arrière pour être hors emprise : c'est le plus proche d'un « entre les berceaux » que la règle
autorise.

### 12.2 La première marche est un mur, pas un épaulement

Le brief décrit l'évasement comme progressif de `s = 500` à `s ≈ 512`. Il ne peut pas l'être :
**5,06 m des 7,86 m d'évasement total tombent à `s = 500` exactement**, en une face plane, parce
que rien ne peut occuper la bande `12,04 < |x| < 15,78` au-dessus du pont dès `z < 8,00`. Les
deux marches suivantes (`+1,40` chacune) sont, elles, franches et libres.

### 12.3 Le collecteur d'artère déborde de 1,61 m en avant de `s = 500`

`z_max = +9,610`, soit `s = 498,39`. La poupe elle-même tient dans `s ∈ [500 ; 520]` ; seul le
collecteur est en avant, à cheval sur la fin du canal magenta du corridor.

C'est **la seule position possible** et elle mérite l'arbitrage du concepteur :

- dans le bassin, il mordrait un berceau ;
- sur la paroi avant, il serait **invisible** — on ne voit pas le mur avant d'une fosse quand on
  la regarde de face et de haut. Calculé sur la caméra du jeu, puis confirmé au rendu : le fond
  du bassin n'apparaît qu'à partir de `z = +6,49`, tout ce qui est plus en avant étant masqué par
  le pont du corridor lui-même (rayon rasant le rebord du canal à `y = −4,02`) ;
- à `z ≥ 8,00`, il coiffe la fin du canal, il se lit au-dessus du pont du corridor, et il est
  hors emprise.

Il interpénètre le bordé du tronçon 5 sur ses 1,4 derniers mètres (ses quatre pieds prennent
leur assise dans `blc._surface_y`, donc sur la peau **réelle**). Aucun sommet du corridor n'est
modifié. **Si le concepteur préfère que la poupe s'arrête net à `s = 500`, il suffit de retirer
`build_manifold` de `PARTS` — mais l'artère n'arrivera alors nulle part de visible.**

### 12.4 Le massif arrière et ses tours sont en bord de cadre

Le sommet des deux tours thermiques (`y = −3,29`) sort par le haut du cadre à la caméra du jeu,
comme les panaches des nacelles. Leur base et leur fût restent visibles entre les nacelles
(vignette 1) et l'ensemble se lit entièrement sur la vignette 3. C'est assumé — une structure qui
déborde le cadre dit que le vaisseau est plus grand que l'écran — mais cela signifie que
**524 triangles (21 % de la pièce) rendent peu de pixels**. Si le concepteur veut les récupérer,
c'est là.

### 12.5 Trois cotes du jeu à faire suivre au concepteur

1. **`hold_plane_y = 6,47` déplace la poupe de 6,47 m par rapport à la planche du `BRIEF-0105`.**
   Cette planche-là rendait la poupe à `z = 0` ; en jeu elle s'arrête à `z = −6,47`. Le cadre
   (58,77 m, 32,7 px/m) n'en dépend pas, mais le cadrage vertical si.
2. **`engine_spacing = 10,28` rend les trois emprises de berceau sécantes** (0,72 m de
   recouvrement). Si l'intention était trois zones distinctes, c'est l'entraxe ou la garde qu'il
   faut revoir — pas la carène. À titre indicatif : l'enveloppe **réelle** des trois berceaux
   laisse 0,25 m entre le central et un latéral, et la carène s'en tient à **0,87 m**.
3. **La dalle grise que la poupe remplace** (`CortegeStern.build()`) a son dessus à
   `deck_y − 0,80 + 0,80 = deck_y`. L'assise livrée a son dessus à `deck_y` **exactement** : le
   remplacement est direct, aucune cote de `cortege_stern.gd` ne bouge. La carène est simplement
   plus grande que la dalle : **39,80 × 21,61 m** contre **34,30 × 22,40**.

### 12.6 Aucun `.gd`, `.tscn` ni `.tres` n'a été touché

Vérifié sur `git status` : les seuls fichiers écrits sont `tools/blender/build_stern.py`, le
`.glb`, son `.glb.import` (généré par `check.sh`), la planche, ce rapport et la ligne de
provenance. `long_cortege.glb` n'a pas bougé d'un octet — le corridor est **lu**, jamais
regénéré.

---

## 13. Suggestions

- **Un marqueur plutôt qu'une arithmétique.** La poupe est posée par `z = −station` dans
  `cortege_root.gd`. Si elle prenait un `Empty` porté par le tronçon 5 (comme les trente
  marqueurs de coque), la station cesserait d'être écrite à deux endroits. Hors périmètre ici.
- **Les 17 486 triangles restants.** Les deux surfaces qui les mériteraient sont la **paroi
  intérieure du bassin** (deux trapèzes de 7 m, vus en biais tout au long de la phase) et
  l'**assise**, si un jour un berceau est retiré du décor. Aucune des deux ne se voit assez
  aujourd'hui pour justifier la dépense.
- **La face avant plane** gagnerait à porter un relief si le plafond de l'emprise était descendu
  (par exemple « rien au-dessus de `deck_y + 5` » plutôt que « rien au-dessus du pont ») : la
  bande `12,04 < |x| < 15,78` s'ouvrirait alors aux gradins bas, et l'évasement pourrait
  vraiment se faire en trois temps.
