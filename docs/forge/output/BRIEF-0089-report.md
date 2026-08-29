# BRIEF-0089 — compte-rendu de forge : la coque du Long Cortège

- **Agent** : `asset-forge`
- **Date** : 2026-08-29
- **Brief** : [`docs/forge/briefs/BRIEF-0089-long-cortege-coque.md`](../briefs/BRIEF-0089-long-cortege-coque.md)
- **Script source** : `tools/blender/build_long_cortege.py` (Blender 4.5.11, kit `aegis_kit` **inchangé**)

## 0. Livrables

| Fichier | sha256 | Taille |
|---|---|---|
| `assets/imported/models/backgrounds/long_cortege.glb` | `4a4400d8924951202532eb7f844eb7ff62496b310867eafddd5365dd919d1599` | 3 308 404 o |
| `docs/forge/output/BRIEF-0089-planche-sections.png` | `d5d5237aa46cc33008cff7f336a82ba80f628b5e94c96f83f8b013130c7db57b` | 1440 × 3364 |
| `tools/blender/build_long_cortege.py` | — | le script **est** la source (ADR-0008) |

**Déterminisme** : `./scripts/build-hull.sh --check long_cortege` → *déterminisme OK*, **0 octet divergent**
sur deux exécutions successives (`blender45 -t 1`). Vérifié trois fois au cours du chantier.
`./scripts/check.sh` → **ALL GREEN** avec le fichier en place.

## 1. La correction de dimensions, et ce qu'elle a changé de méthode

Le brief écrivait « ≈ 34 unités par tronçon ». Le concepteur l'a corrigé en cours de forge :
**100 unités**, 500 au total, pour un défilement à 2,4 u/s. C'est cette correction qui décide de
tout le fichier.

| | Emprise | Triangles | tri/m² |
|---|---|---|---|
| Pale Leviathan | coque de boss | — | 195 |
| `core_interior` | 30 × 18 m | 19 414 | 36 |
| **`long_cortege`** | **500 × 28 m** | **39 434** | **2,8** |

À 6,4 tri/m² de plafond, une coque modelée pièce par pièce n'entre pas. La réponse est un
**vocabulaire modulaire** de huit familles, instancié le long du tronçon avec des variations
seedées — c'est exactement ce que montrent les trois maquettes : un bordé fait de modules qui se
répètent, et quelques accidents forts qui portent la lecture.

| Famille | Coût | S1 | S2 | S3 | S4 | S5 | Total |
|---|---|---|---|---|---|---|---|
| plaques de bordé | 12 tri | 169 | 264 | 263 | 265 | 225 | **1 186** |
| nervures transversales | 12 tri × 6 | 20 | 42 | 48 | 42 | 48 | **200** |
| lisses longitudinales | 12 tri | 6 | 6 | 6 | 6 | 6 | **30** |
| greffes (blocs empilés) | ~40 tri/couche | 13 | 26 | 28 | 34 | 22 | **123** |
| pastilles lumineuses | 12 tri | 48 | 84 | 90 | 96 | 92 | **410** |
| plateformes de tourelle | ~230 tri | 2 | 3 | 3 | 4 | 5 | **17** |
| baies hexagonales | ~230 tri | 1 | 2 | 2 | 1 | 1 | **7** |
| Ambry | — | — | — | — | — | 414 faces | **1** |

### Le budget : 39 434 triangles sur 90 000 (43,8 %)

**Je n'ai pas rogné en silence, et je ne demande pas de rallonge.** Le brief autorisait 90 000 et
l'ADR-0011 monte à 120 000 pour la classe *structure* ; j'en consomme 44 %. Ce n'est pas de la
prudence, c'est une conséquence mesurée : à 20° de la verticale et à 500 m de long, **ce qui se
lit, ce sont les pentes et les arêtes, pas la finesse**. Chaque plaque coûte 12 triangles et rend
une arête vive, un flanc en dépouille éclairé et une ligne d'ombre ; doubler leur nombre
doublerait le bruit, pas la lecture — et la texture (LOT C) est *faite pour* porter les joints,
les rivets et l'usure qui manquent encore.

La marge restante est donc **délibérément laissée au concepteur** : elle paie les tourelles, les
ponts et les nœuds qu'il instanciera sur les 30 points d'attache, qui eux seront vus de près.

## 2. Mesures relevées **sur le `.glb` produit** (jamais sur la scène en mémoire)

| Tronçon | Triangles | % budget (18 000) | z monde | bbox (l × h × L) | **sommet Y** |
|---|---|---|---|---|---|
| `Section_01` | 6 572 | 36,5 % | `[-100 , 0]` | 28,00 × 9,36 × 100,00 | **−3,240** |
| `Section_02` | 7 870 | 43,7 % | `[-200 , -100]` | 28,00 × 9,38 × 100,00 | **−3,220** |
| `Section_03` | 8 026 | 44,6 % | `[-300 , -200]` | 28,00 × 9,40 × 100,00 | **−3,204** |
| `Section_04` | 8 222 | 45,7 % | `[-400 , -300]` | 28,00 × 9,39 × 100,00 | **−3,207** |
| `Section_05` | 8 744 | 48,6 % | `[-500 , -400]` | 28,00 × 9,40 × 100,00 | **−3,200** |
| **TOTAL** | **39 434** | **43,8 %** | `[-500 , 0]` | **28,0000** × 9,40 × 500,00 | **−3,200** |

- 63 414 sommets, 27 primitives, 5 maillages, 3 308 404 octets.
- **Le sommet le plus haut des 500 m est le mât d'antenne d'Ambry, à Y = −3,200**, soit
  **20 cm sous le plafond `Y = −3`**. Viennent ensuite les bulbes d'arête (−3,220 / −3,240) puis
  les greffes les plus hautes (−3,204 à −3,207).
- Le script s'impose un **plafond de construction à −3,20**, bloquant lui aussi : les 20 cm
  réservés sont la place où le jeu posera ses tourelles et ses nœuds. Une coque qui les mangerait
  obligerait à reforger.

### Jonctions : mesurées, pas estimées

Deux contrôles distincts, tous deux bloquants :

1. **Bout à bout** : `min(z)` du tronçon *n* − `max(z)` du tronçon *n+1* = **0,00000 m** aux quatre
   jonctions (tolérance 1 × 10⁻⁴). Ni trou ni recouvrement.
2. **Profils identiques** : les deux anneaux de peau de part et d'autre d'un plan de jonction sont
   comparés point par point (arrondis à 0,1 mm) — **jeux de 34 points strictement égaux**. C'est ce
   second contrôle qui garantit qu'on ne verra pas une *marche* là où il n'y a pas de trou. Le
   fuseau de proue s'achève à `s = 88` par un smoothstep, dont la dérivée est nulle : le profil est
   déjà plat 12 m avant la jonction 1-2.
3. Aucun module n'approche un plan de jonction à moins de **1,5 m** (garde vérifiée par
   construction), sans quoi le contrôle n°2 n'aurait plus de sens.

## 3. Dépliage et **densité de texels mesurée**

Mesure par **valeurs singulières de l'application plan-du-triangle → UV**, triangle par triangle
(une moyenne d'aires ne verrait aucun étirement : un triangle deux fois trop long dans un sens et
deux fois trop court dans l'autre a la bonne aire).

| Pièce | Cible | m/tuile | Mesuré (tuiles/m) | **Moyenne** | Anisotropie max |
|---|---|---|---|---|---|
| `Section_01` | 0,200 | 5,00 | 0,116 – 0,200 | **0,197** (5,07 m/tuile) | 1,73 |
| `Section_02` | 0,200 | 5,00 | 0,124 – 0,200 | **0,198** (5,06) | 1,62 |
| `Section_03` | 0,200 | 5,00 | 0,125 – 0,200 | **0,198** (5,06) | 1,60 |
| `Section_04` | 0,200 | 5,00 | 0,125 – 0,200 | **0,198** (5,06) | 1,60 |
| `Section_05` | 0,200 | 5,00 | 0,125 – 0,200 | **0,198** (5,05) | 1,60 |
| **Ambry** | **0,700** | **1,43** | 0,609 – 0,700 | **0,699** (1,43) | 1,15 |

> **Les minima ne sont pas un défaut de dépliage : c'est la borne de la méthode.** Une projection
> en boîte étire par `1/cos(angle à l'axe dominant)`, et le pire cas géométrique est la normale
> `(1,1,1)/√3`, à 54,74° de son axe dominant, soit **√3 = 1,732**. La valeur mesurée la plus basse
> (0,116 = 0,200/1,72) est donc **exactement** la borne théorique, atteinte par les coins des blocs
> greffés. Le harnais échoue si une face descend en dessous, si le maximum dépasse la cible, ou si
> la moyenne s'écarte de plus de 14 % — les trois sont vérifiés à chaque build.

### ⚠️ La contrainte que le brief ne pouvait pas connaître : `L × densité` doit être ENTIER

Les cinq tronçons sont cinq objets séparés, chacun déplié dans **son** repère local.
`box_project_uv()` écrit `v = z_local × densité` sur toute face dont la normale est dominante en X
ou en Y — c'est-à-dire le pont et les flancs, donc tout ce qu'on voit. À la jonction, le tronçon
amont finit à `v = −L × densité` et le tronçon aval repart de `v = 0`.

**Si `L × densité` n'est pas un entier, la carte saute d'une demi-tuile à chaque jonction — quatre
fois dans le niveau, tous les 100 m.** La constante du script n'est donc pas « 0,2 tuile/m » mais
`HULL_TILES_PER_SECTION = 20`, dont 0,200 tuile/m est *déduit*. **Toute demande `TEX-` future doit
respecter cette règle** : si le concepteur veut changer l'échelle du bordé, la nouvelle valeur doit
vérifier `100 × densité ∈ ℤ` (0,15 / 0,20 / 0,25 / 0,30 conviennent ; 0,22 non).

### Coutures et échelle monde à annoncer au LOT C

- **Bordé** : 1 tuile couvre **5,00 m** ; 20 tuiles par tronçon, 100 sur les 500 m ; 5,6 tuiles en
  travers des 28 m. Coutures = les discontinuités d'axe dominant de la projection en boîte, donc
  **les arêtes vives elles-mêmes** (chines, flancs de plaque, murs de coaming) — jamais au milieu
  d'une surface plane. Les jonctions de tronçons ne sont **pas** des coutures (voir ci-dessus).
- **Ambry** : 1 tuile couvre **1,43 m**, soit **3,5 × plus fin** que le bordé.
- ⚠️ **`uv1_scale` doit rester `(1, 1, 1)` côté Godot** : l'échelle est déjà cuite dans les UV.
- La **planche de contrôle au damier** est la dernière vignette de la planche de recette, rendue à
  la perspective du jeu : grande case = 1 tuile de 5,00 m, petite = 1/8 de tuile = 62,5 cm. Les
  cases restent carrées sur les ponts et ne s'allongent que sur les facettes obliques, dans le
  rapport annoncé.

## 4. Les 30 marqueurs — **enfants de leur tronçon**, et c'est délibéré

Le brief dit « cinq nœuds racines, **sans enfants maillés** ». Le mot *maillés* fait le partage :
les 30 points d'attache sont des **Empties parentés à leur tronçon** (`Node3D` côté Godot).

**Raison mécanique** : le moteur fait défiler le décor en translatant les nœuds de tronçon. Des
marqueurs racines à coordonnées absolues resteraient sur place pendant que la coque glisse
dessous — un bug livré par la forge, invisible à l'import. Le harnais vérifie qu'**aucun enfant ne
porte de maillage** et que les 30 noms exacts sont présents ; **le build échoue si un seul manque**.

Positions **locales au tronçon**, repère Godot (le monde = local + translation du nœud) :

| Marqueur | Tronçon | x | y | z local |
|---|---|---|---|---|
| `Turret_01` | `Section_01` | −6,00 | −3,811 | −68,00 |
| `Turret_02` | `Section_01` | +9,40 | −4,332 | −84,00 |
| `Turret_03` | `Section_02` | +9,60 | −4,328 | −18,00 |
| `Turret_04` | `Section_02` | −9,20 | −4,321 | −40,00 |
| `Turret_05` | `Section_02` | +5,60 | −3,662 | −76,00 |
| `Turret_06` | `Section_03` | −8,40 | −4,308 | −14,00 |
| `Turret_07` | `Section_03` | +9,80 | −4,332 | −46,00 |
| `Turret_08` | `Section_03` | −5,60 | −3,662 | −78,00 |
| `Turret_09` | `Section_04` | +8,20 | −4,304 | −12,00 |
| `Turret_10` | `Section_04` | −9,80 | −4,332 | −36,00 |
| `Turret_11` | `Section_04` | +10,10 | −4,337 | −60,00 |
| `Turret_12` | `Section_04` | −6,20 | −3,676 | −86,00 |
| `Turret_13` | `Section_05` | +8,80 | −4,315 | −10,00 |
| `Turret_14` | `Section_05` | −9,40 | −4,325 | −28,00 |
| `Turret_15` | `Section_05` | −6,00 | −3,671 | −52,00 |
| `Turret_16` | `Section_05` | −10,20 | −4,338 | −70,00 |
| `Turret_17` | `Section_05` | +9,00 | −4,318 | −88,00 |
| `Bay_01` | `Section_01` | +9,00 | −3,460 | −86,00 |
| `Bay_02` | `Section_02` | −9,20 | −3,460 | −26,00 |
| `Bay_03` | `Section_02` | +9,20 | −3,460 | −82,00 |
| `Bay_04` | `Section_03` | −9,30 | −3,460 | −28,00 |
| `Bay_05` | `Section_03` | +9,30 | −3,460 | −90,00 |
| `Bay_06` | `Section_04` | −9,30 | −3,460 | −48,00 |
| `Bay_07` | `Section_05` | −9,30 | −3,460 | −36,00 |
| `Spine_01` | `Section_01` | 0,00 | −3,525 | −50,00 |
| `Spine_02` | `Section_02` | 0,00 | −3,160 | −50,00 |
| `Spine_03` | `Section_03` | 0,00 | −3,160 | −50,00 |
| `Spine_04` | `Section_04` | 0,00 | −3,160 | −50,00 |
| `Spine_05` | `Section_05` | 0,00 | −3,160 | −50,00 |
| `Ambry` | `Section_05` | +10,65 | −4,200 | −60,00 |

**Conventions de pose**, pour que le jeu sache où poser quoi :

- `Turret_NN` : au **plan de pose** de la plateforme (10 cm au-dessus de la lèvre du socle). Densité
  croissante 2 / 3 / 3 / 4 / 5, rayon du socle croissant de 2,30 m (S1) à 3,20 m (S5) — « de plus en
  plus massives » (maquette 3). Jamais sur l'axe : `|x| ≥ 5,60`.
- `Bay_NN` : à la **bouche** du puits (4 cm au-dessus de la lèvre), pour qu'un chasseur instancié
  apparaisse à l'ouverture et non 1,2 m plus bas. Ouverture hexagonale de 6,80 × 6,40 m, puits de
  1,22 m, fond émissif.
- `Spine_NN` : sur l'axe, 6 cm au-dessus du sommet du bulbe. Exactement un par tronçon.
- Tous portent une **rotation identité** : ils sont posés sur des bandes horizontales, aucune n'est
  sur une facette inclinée. Le jeu n'a rien à corriger.

## 5. Ce que le rendu a attrapé, et qui n'aurait été vu par aucun harnais (ADR-0006)

Deux fautes ont survécu à onze contrôles verts et n'ont été trouvées **qu'en regardant la planche**.

**1. Les sept baies rendaient des hexagones VIDES.** La lèvre était à −3,90 et le fond émissif à
−5,65 : « un puits de 1,75 m ». Sauf que la peau **n'est pas trouée** (pas de booléen : il n'est pas
déterministe et rendrait la peau non manifold) et qu'elle court à −4,30 sous la bouche. Le pont
occultait donc intégralement le fond. Contrat vert, UV vertes, budget vert, et la mécanique
principale du niveau invisible. Le fond passe désormais **au-dessus** du pont le plus haut de
l'emprise (−4,20 contre −4,30) et la lèvre monte d'autant : puits de 0,78 m, entièrement vu.

**2. Le Cortège lisait comme une piste d'aéroport.** Première répartition : crête ivoire sur 1,64 m,
arête lumineuse de 0,52 m, trois lisses ivoire par flanc, toutes les nervures en ivoire, couronne
de socle ivoire. À la perspective du jeu : six rubans blancs et un néon magenta plein cadre, quand
les trois maquettes montrent une **masse anthracite** où l'ivoire et le magenta sont rares.
Corrigé : arête lumineuse ramenée à **0,28 m** (liseré ivoire 0,64 m), une nervure sur trois en
ivoire, une seule lisse claire par flanc, liseré de socle à 5 % du rayon, 12 % de plaques violettes
au lieu de 20 %.

> **La leçon qui dépasse ce fichier** : sur une pièce de 500 m, un matériau clair appliqué à une
> arête **continue** occupe plus de pixels qu'une pièce entière, et aucun compte de triangles ni
> aucune répartition en aire ne le dit. `AA_Trim` ne fait que **2,29 %** de l'aire du modèle final —
> et faisait déjà moins de 6 % dans la version qui ressemblait à un aéroport.

Trois autres défauts ont été trouvés par les harnais et corrigés : les cinq familles de modules
écrivaient `s` **global** dans le `z` **local** (le tronçon 5 posait ses plaques 400 m derrière
lui — attrapé par le contrôle de jonction) ; `Matrix.Rotation(pi)` de Blender introduisait 35 µm
d'erreur en X dans la translation du nœud à 400 m (remplacée par une matrice à coefficients
entiers) ; et `_clip_lane` avait un minimum de 0,9 m qui supprimait **en silence** les 30 lisses
(0,36 m) et les 410 pastilles (0,56 m) — d'où le compte de modules imprimé à chaque build.

## 6. Ambry — et un écart au brief qu'il faut trancher

L'avant-poste humain est un **ruban de 27 × 5,5 m** greffé sur le bordé tribord du tronçon 5
(`s` 446 → 474, `x` 7,60 → 13,60), 414 faces. Radeau plan à −4,48, douze béquilles de longueurs
toutes différentes qui descendent sur une facette inclinée, deux colliers de greffe qui mordent le
bordé, quatre modules d'habitation alignés, une passerelle continue à garde-corps, un pas
d'appontage, une serre voûtée et un mât d'antenne.

Il est **intact et re-plombé**, jamais en ruine : c'est ce qui doit rendre la découverte
insoutenable. Il jure par trois moyens qui ne dépendent d'aucune texture — l'**orthogonalité**
(tout est aligné sur deux axes, au-dessus d'une coque faite de facettes), la **valeur**
(`AA_Trim` ivoire `#DDDCD2` contre `AA_Hull` anthracite `#24252B`, rapport de 1 à 12 en luminance),
et l'**absence totale de magenta**.

> ⚠️ **ÉCART ASSUMÉ — le brief demande « matériaux `AA_Hull` / `AA_Trim` **clairs** contre
> l'anthracite ». Sous la palette Null Choir, `AA_Hull` **EST** l'anthracite** (`#24252B`) : c'est
> le même matériau que le bordé. Le contraste ne peut donc venir que d'`AA_Trim`, et le kit refuse
> de mélanger deux factions dans une coque (`set_faction()` lève `ContractError`). Ambry est donc
> **dominée par `AA_Trim`**, `AA_Hull` n'y servant qu'aux colliers de greffe — ce qui est cohérent :
> ce sont eux qui appartiennent au vaisseau, pas l'avant-poste.

> ⚠️ **CONSÉQUENCE À TRANCHER AVANT `TEX-`** : Ambry **partage les 7 matériaux du bordé**. La
> demande « bordé humain » du LOT C ne pourra donc **pas** lui être propre : elle recevra la carte
> du bordé, à une échelle 3,5 × plus fine (ce qui, en soi, la fait déjà lire comme une construction
> à l'échelle de la main). **Si tu veux une carte dédiée, il faut un huitième slot** (p. ex.
> `AA_Ambry_Hull`) : dis-le et je reforge — c'est une modification locale, la géométrie ne bouge
> pas. Je ne l'ai pas prise seule parce que le brief nomme explicitement `AA_Hull`/`AA_Trim`.

Le **vert maladif** `#7C9E52` (`AA_Marking_Red` sous cette palette) n'existe **qu'ici**, sur la
serre : 85,7 m² sur 60 373, soit **0,14 %** de l'aire du modèle. C'est le seul emploi des 500 m,
conforme au « usage très limité » de la charte.

## 7. Palette, émissif, et la réserve de lisibilité

Les **7 matériaux `AA_*` sont présents et assignés** (le build échoue si l'un est présent mais non
assigné). Répartition **en aire**, relevée sur le `.glb` :

| Matériau | Couleur (charte) | Aire | Part |
|---|---|---|---|
| `AA_Greeble` | `#141419` | 38 841 m² | 64,33 % |
| `AA_Hull` | `#24252B` anthracite | 15 106 m² | 25,02 % |
| `AA_Panel` | `#452663` violet sombre | 4 545 m² | 7,53 % |
| `AA_Trim` | `#DDDCD2` ivoire froid | 1 381 m² | 2,29 % |
| `AA_Emissive_Engine` | `#D93D9C` magenta | 390 m² | **0,65 %** |
| `AA_Marking_Red` | `#7C9E52` vert maladif | 86 m² | 0,14 % |
| `AA_Glass` | `#0A0910` | 25 m² | 0,04 % |

> `AA_Greeble` domine parce qu'il porte **toute la carène** — ventre, sous-chine, dessous des
> modules — qui n'est jamais vue depuis la caméra du jeu. Sur les seules faces tournées vers le
> ciel, la répartition visible est très différente : anthracite dominant, violet en plaques, ivoire
> en accents.

- ⛔ **Aucun cyan `#3FD9E8`, aucun corail `#FF5A3D`** : un harnais compare chaque `baseColorFactor`
  et chaque `emissiveFactor` aux deux couleurs réservées aux tirs et **échoue le build** à moins de
  0,02 d'écart linéaire.
- **L'émissif magenta a été rationné en connaissance de cause.** Le magenta est aussi une couleur
  de tir ennemi (charte §3). Première version : fond de baie émissif plein (35 m² par baie, sept
  fois). Ramené à un cœur à 66 % cerclé d'`AA_Panel` sombre, et cœur de socle de tourelle réduit de
  0,46 R à 0,36 R. **Total : 0,65 % de l'aire.** C'est au concepteur de vérifier en capture que les
  balles se lisent encore par-dessus — c'est le seul critère qui vaille (`ADR-0006`).
- **Deux extensions glTF** apparaissent, aucune n'est une texture :
  `KHR_materials_emissive_strength` (le kit pose l'émissif à 2,5) et `KHR_materials_transmission`
  (l'`AA_Glass` de la serre, α = 0,86). `"images": null`.

## 8. ⛔ Aucune texture (`ADR-0028`) — et ce que la géométrie donne au LOT C

Le `.glb` ne porte **aucune image, aucune `baseColorTexture`, aucune `normalTexture`, aucune
`occlusionTexture`, aucune `emissiveTexture`** : sept matériaux en couleur unie par facteurs. Le
harnais échoue le build si l'un d'eux apparaît. Le damier de la planche de recette **n'existe que
dans le rendu**.

Les six sujets prévus par le brief peuvent maintenant être chiffrés, puisque **c'est la géométrie
qui donne l'échelle monde** :

| Sujet `TEX-` | Matériau visé | `world_scale` à déclarer | Remarque |
|---|---|---|---|
| bordé de coque | `AA_Hull` | **5,00 m/tuile** | mesuré, pas décidé ; `100 × densité ∈ ℤ` |
| hauteur du bordé | `AA_Hull` | **5,00 m/tuile** | niveaux de gris, jamais de normal map |
| panneaux d'usure / greffes | `AA_Panel` | **5,00 m/tuile** | 7,5 % de l'aire, en plaques |
| émissif d'épine | `AA_Emissive_Engine` | bande de **0,28 m** de large sur 500 m | 1 tuile = 5 m de longueur |
| émissif de baie | `AA_Emissive_Engine` | hexagone de **4,49 × 4,22 m** | 0,9 tuile ; une seule tuile suffit |
| bordé d'Ambry | `AA_Trim` | **1,43 m/tuile** | ⚠️ voir §6 : slot partagé |

## 9. Cadrage — une mesure que le brief demandait sans le savoir

Le brief pose 28 m « le plan de jeu fait 28 : la coque emplit l'écran ». Les 28 m emplissent le plan
de jeu **à `Y = 0`** ; le pont de la coque est 4,30 m plus bas, donc plus loin de la caméra, donc
dans un cadre plus large. Calculé à chaque build depuis la caméra de `graybox.tscn` :

- pont à `Y = −4,30` → profondeur **19,47 m**, cadre **41,60 m** de large ;
- **la coque de 28 m en couvre 67,3 %** : environ un sixième de l'écran de chaque côté montre le
  ciel du niveau. C'est fidèle à la maquette *phase 1* (nébuleuse de part et d'autre) et un peu
  moins aux maquettes 2 et 3, où la coque déborde du cadre.
- Pour un **bord à bord** exact, deux réglages possibles, tous deux mesurés :
  **FOV 44,0°** (au lieu de 62) **ou caméra à `Y = 8,02`** (au lieu de 14).

**Je n'ai pas élargi la coque** : 28 m est une exigence explicite du brief et la largeur est
contrôlée à 10⁻³ près (`28,0000 m`). Le choix appartient au concepteur, et il est réversible sans
reforge.

## 10. Ce que le script ne réutilise pas du kit, et pourquoi

`aegis_kit` est employé **sans aucune modification**. Trois de ses fonctions sont refaites
localement — incompatibilités de contrat, vérifiées dans son code, sur le précédent déjà documenté
de `build_moon_flyby.py` :

1. **`export_hull()`** exporte *une* coque dont le nœud reste à l'origine ; ici chaque tronçon porte
   une translation que le moteur relit. Son contrôle d'orientation compare le Y d'auteur des
   sommets **locaux** au Z du glTF **translation comprise** — faux dès que le nœud bouge. Il impose
   en outre un pivot centré à 2 cm et une bbox largeur × longueur : sans objet à 500 m. Export et
   validation sont refaits à l'identique sur le fond (même correction d'axe, même relecture du
   `.glb` **produit**, même règle « au moindre écart, on échoue »).
2. **`new_object()`** appelle `recalc_face_normals`. Les tronçons 2 à 5 sont des **tubes ouverts aux
   deux bouts** (seuls la pointe de proue et la coupe de poupe sont fermées) : sur une surface
   ouverte, l'heuristique de bmesh peut retourner toute la pièce. Une coque à l'envers **disparaît**
   en jeu (culling arrière) sans qu'aucune bbox, aucun compte de triangles ni aucune mesure d'UV ne
   le voie. Le bobinage est donc posé à la main et `_assert_skin_outward()` le vérifie face par
   face, sur trois familles (pont, fond, flancs), **avant** que le moindre module ne soit posé.
3. **`cleanup()`**, pour la même raison : `_weld()` ne soude que les doubles.

Le kit fournit tout le reste sans retouche : `set_faction()`, `material()`,
`apply_material_slots()`, `mat_index()`, `box_project_uv()`, `srgb_hex_to_linear()`, `join_objects()`,
`shade_smooth_by_angle()`, `ContractError`.

## 11. Les onze harnais bloquants

Tous relisent le **`.glb` produit** (sauf 1, 2 et 11, qui portent sur la scène avant export) :

1. chaîne d'axes sur trois témoins **asymétriques**, plus l'équivalence prouvée avec la chaîne du kit ;
2. orientation de la peau, face par face, avant pose des modules ;
3. plafond du jeu (−3,00) **et** plafond de construction (−3,20) ;
4. contrat de noms : cinq racines exactes, aucune racine inattendue, aucun enfant maillé ;
5. les **30 marqueurs** aux noms exacts, aucun manquant, aucun en double, aucun inattendu ;
6. translations des nœuds : `(0, 0, −100 n)` à 10⁻⁴ près, aucune rotation, aucune échelle ;
7. jonctions bout à bout **et** égalité des deux anneaux de peau ;
8. `TEXCOORD_0` **et** `TANGENT` comptés sur **27/27** primitives ;
9. densité de texels : plancher théorique de la projection en boîte, plafond à la cible, moyenne à ±14 % ;
10. les 7 matériaux présents **et assignés**, aucune couleur de tir, aucune texture, aucune image ;
11. budgets (18 000 par tronçon, 90 000 au total) et largeur hors-tout à 10⁻³ près.

## 12. Limites connues

- **La coque ne couvre que 67 % de la largeur du cadre** à la caméra actuelle (§9). Réglage
  concepteur, pas reforge.
- **Ambry partage les matériaux du bordé** (§6) : une carte qui lui serait propre demande un slot
  supplémentaire.
- **Les sections 2 à 5 ont exactement la même peau.** C'est un choix : moduler le profil ferait
  courir un risque de marche aux jonctions, et la variation vient des modules (nombre de nervures
  6/7/8/7/9, greffes plus grosses vers la poupe, densité de tourelles croissante). Vu de dessus,
  les cinq vignettes de la planche se distinguent bien ; vu au ras, la répétition sera portée par
  la texture.
- **Le puits des baies est un coaming posé, pas une cavité percée** (§5). À 20° de la verticale la
  différence ne se voit pas ; elle se verrait à la rasante, ce que la caméra ne fait jamais.
- **Aucune tourelle, aucun pont, aucun nœud modélisé** : hors périmètre, uniquement leurs points
  d'attache — comme demandé.
- La planche de recette **ne simule pas** le post-process rétro ni le bloom du jeu
  (`glow_hdr_threshold = 1,6` alors que l'émissif est à 2,5) : les cœurs de tourelle et l'arête
  seront **plus larges** à l'écran qu'ici. C'est une raison de plus de vérifier la lisibilité des
  balles en capture.

## 13. Suggestions

1. **`ak.box_project_uv()` mériterait une variante « décor découpé »** qui accepte un décalage de
   `v` par pièce, pour que la contrainte « `L × densité` entier » n'ait pas à être redécouverte par
   le prochain décor en tronçons. Trois lignes dans le kit.
2. **`scripts/build-hull.sh --check` ne contrôle que le premier `.glb` repéré dans un script**
   (déjà signalé par BRIEF-0086). Ici il n'y en a qu'un, mais le piège reste.
3. Le compte de modules imprimé à chaque build a attrapé deux familles disparues en silence. Ce
   serait un réflexe utile pour toute forge procédurale : **imprimer ce qu'on a posé**, pas
   seulement ce qu'on a mesuré.
