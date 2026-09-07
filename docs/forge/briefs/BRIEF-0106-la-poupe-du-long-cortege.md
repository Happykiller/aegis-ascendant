# BRIEF-0106 — La poupe du Long Cortège : la structure qui porte les trois moteurs

- **Statut** : livré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-06

## Objectif

Modeler **la carène de poupe** : les vingt derniers mètres du Long Cortège, ceux sur lesquels
sont boulonnés les trois groupes propulsifs. C'est la dernière boîte grise de la phase finale —
tout le reste est en place et jouable.

## Contexte

### Où elle vient, et ce qu'elle remplace

La phase finale (`docs/plans/2026-09-06-arrachement-des-moteurs.md`) est **entièrement jouable** :
arrivée, dix verrous à quatre états, arrachement en cinq temps, flammes, poussée, silence, aveu.
Les nacelles, berceaux et ancrages sont les pièces réduites du `BRIEF-0105` — 60 020 triangles.

Ce qui manque est la **structure sous eux**. Aujourd'hui : une dalle grise de 34 × 1,6 × 22 m,
posée par le code, et elle se voit — une boîte sous des pièces finies.

### ⚠️ ELLE DOIT CASSER LA SILHOUETTE DU CORRIDOR, ET C'EST LE POINT

La spec §2 : *« La poupe doit casser radicalement la silhouette du corridor précédent : beaucoup
plus large, plus massive, relief vertical marqué, moteurs dépassant franchement de la coque,
grandes zones mécaniques autour des berceaux. »*

Après quatre minutes d'un corridor de 24 à 28 m qui ne varie qu'en largeur, l'arrivée à la poupe
doit se lire **en une image** comme un changement de nature. La planche maîtresse
`phase_final_niveau2_vaiseau_monde.png` en donne la lecture : un bloc étagé qui remplit le cadre.

### Les cotes du jeu, qui sont des contraintes et non des suggestions

| Cote | Valeur | D'où elle vient |
|---|---|---|
| Station de la poupe | **508,0** | `long_cortege_stern.tres` : 8 m après le cinquième tronçon |
| Pont qui porte les berceaux | **y = −11,85** | le sommet du groupe passe sous le plafond de vol (−2,40) |
| Berceaux | x = **0 et ±10,28**, 9,74 m de large chacun | entraxe `engine_spacing` |
| Emprise des trois groupes | **|x| ≤ 15,15** | bord extérieur des berceaux |
| Plafond de construction | **y ≤ −3,20** | `BUILD_CEILING_Y`, comme tout le décor du niveau |
| Quille | **y ≥ −12,60** | la carène du corridor n'y descend pas plus bas |

### ⚠️ L'ANNEAU DE JONCTION, RELEVÉ SUR LE MODULE

À `s = 500` le corridor rend un profil tribord de 25 points, dont voici les extrêmes et les
paliers qui comptent :

```
   x  +0,000  y  −4,580     fond du canal
   x  +0,963  y  −4,020     arête interne du rebord
   x  +5,848  y  −4,340     pont intérieur, lèvre de chine
   x  +6,321  y  −4,940     pont médian
   x +10,621  y  −5,100     facette extérieure
   x +12,040  y  −8,950     BORD, demi-largeur de la coque
   x +11,438  y −10,600     sous-chine
   x  +0,000  y −12,600     quille
```

**Demi-largeur à la jonction : 12,04 m** (`kx = 0,860` à s = 500).

⚠️ **Le premier anneau de la poupe DOIT ÊTRE CET ANNEAU-LÀ, au micron.** Le module
`build_long_cortege.py` expose `_half_profile(s, side)` : importez-le et prenez le profil à
`s = 500`, ne le recopiez pas. Deux écritures d'une même cote finissent toujours par diverger, et
ce fichier en a déjà payé deux (le coaming du hangar, l'emprise du socle de tourelle).

### Ce que le cadre permet

À la profondeur du pont de poupe (`y = −11,85`), la caméra de jeu couvre **58,77 m** de large et
rend **32,7 px/m** (mesuré par la forge au `BRIEF-0105`, pas 45,8 comme au corridor). Une poupe
de 40 m occupe donc les deux tiers du cadre, contre 24 m pour le corridor : **le contraste de
largeur est disponible, il suffit de le prendre.**

## Ce qu'il faut faire

### 1. L'évasement — la lecture principale

De `s = 500` (demi-largeur 12,04) à `s ≈ 512`, la coque s'ouvre jusqu'à **18 à 20 m de
demi-largeur**. Pas un cône : des **épaulements**, deux ou trois marches franches, chacune prenant
la lumière différemment. C'est ce qui rend l'évasement lisible à 32,7 px/m — une pente continue,
à cette densité, ne se lit pas.

⚠️ **Et l'évasement se voit PAR LE HAUT.** La caméra plonge à 70° : ce qui distingue une marche
d'une pente, c'est la face horizontale entre les deux, pas le profil.

### 2. Le relief vertical, qui manque totalement au corridor

Le corridor est plat : il n'offre que 2,59 m entre son pont et le plafond de vol. La poupe en
offre **9,45** (de −11,85 à −2,40). C'est le seul endroit du niveau où de la hauteur est
disponible, et la spec la demande explicitement.

Des masses hautes **entre** les berceaux et sur les flancs : tours, colonnes, pylônes. Elles
doivent monter assez pour se lire comme du relief, sans jamais dépasser **y = −3,20**.

### 3. Les trois alvéoles de berceau

Chaque groupe s'assied à `x = 0` et `x = ±10,28`, sur `y = −11,85`. Il lui faut :

- une **assise plane** d'au moins 10 × 15 m sous chaque berceau ;
- de la **machinerie autour** — la spec §2 dit « grandes zones mécaniques autour des berceaux » ;
- et **rien au-dessus** : les nacelles montent jusqu'à −2,40 et les flammes sortent du cadre.

⚠️ **RIEN NE DOIT ENTRER DANS L'EMPRISE D'UN BERCEAU** (10 × 15 m centré sur sa station, plus
0,5 m de garde). Une pièce de décor qui mord un berceau se lit comme une collision, et surtout
elle masquerait un verrou — la seule cible de la phase.

### 4. L'habillage, avec les planches déjà fournies

Dix planches attendent, et elles ont été faites pour ici :

| Planche | Où elle sert |
|---|---|
| `asset5` conduite énergétique, `asset8` conduit magenta | l'artère qui alimente les trois groupes |
| `asset8` bride de moteur | la ceinture d'une alvéole |
| `asset7` pylône spatial | les masses hautes entre les berceaux |
| `asset8` tour thermique, `asset9` réseau de refroidissement | idem, côté flancs |
| `asset9` déflecteur d'échappement | autour des tuyères |
| `asset9` collier, `asset9` anneau de maintenance | les alvéoles |
| `asset6` flexibles, `asset8` cryogénie | les liaisons |

⚠️ **CE N'EST PAS UNE LISTE DE COURSES.** La spec §20 fixe le budget artistique : « concentrer le
travail sur peu de pièces, et investir dans les VFX ». Prenez-en **trois ou quatre**, celles qui
servent la silhouette, et laissez les autres. Une poupe couverte de tout ce qui existe redevient
un tapis de greebles — c'est le défaut que `BRIEF-0094` a corrigé sur 500 m de coque, et la règle
qui en est sortie tient ici : **un module de relief ne se pose que dans l'emprise d'une
installation.**

### 5. L'artère se termine ici

Le canal magenta court sur les 500 m et alimente les moteurs. Il doit **arriver quelque part** :
une jonction visible entre l'axe du corridor et les trois groupes. C'est aussi ce qui rend le
blackout du LOT 8 lisible — l'artère s'éteint avec les moteurs, et on doit voir ce qu'elle
alimentait.

⚠️ **`AA_Emissive_Engine` SUR CETTE JONCTION, et sur elle seule.** `CortegeStern.blackout()`
éteint tout ce qui porte ce slot ; une veine peinte ailleurs resterait allumée sur un vaisseau
mort, et **rien ne le signalerait**.

## Texture (ADR-0028)

**Aucune.** Le Long Cortège entier est en PBR par facteurs, zéro image, et son harnais échoue le
build si une texture apparaît. Les pièces de poupe du `BRIEF-0105` respectent déjà ce régime.

**Dépliage** : projection en boîte à la densité de la peau du corridor. `TEXCOORD_0` compté.

## Animation (ADR-0046 §6)

**Figée.** La poupe est de la structure. Ce qui bouge — les nacelles, les berceaux, les verrous —
est déjà livré et animé.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_stern.py` | le générateur, qui **importe** `build_long_cortege` pour son anneau |
| `assets/imported/models/backgrounds/stern_hull.glb` | la carène de poupe |
| `docs/forge/output/BRIEF-0106-report.md` | mesures, jonction, triangles, emprises |
| `docs/forge/output/BRIEF-0106-planche.png` | rendus à la caméra du jeu |

## Provenance

Une ligne neuve `stern_hull` dans `assets/licenses/ASSET_PROVENANCE.csv`.

## Critères d'acceptation

- [ ] **La jonction à `s = 500` est exacte** : le premier anneau de la poupe est celui que
      `_half_profile(500.0, side)` rend, au micron, **des deux bords** (la coque est asymétrique).
      C'est le critère qui prime — une marche d'un centimètre à la jonction se voit en vol.
- [ ] **Budget : ≤ 20 000 triangles.** Les 60 020 des pièces mobiles sont déjà dépensés sur les
      80 000 de la phase. Le compte est donné, et ce qui a dû être coupé est nommé.
- [ ] **Rien dans l'emprise des trois berceaux** (10 × 15 m + 0,5 de garde, aux stations x = 0
      et ±10,28), mesuré sur le binaire. ⚠️ Une pièce qui y entre masque un verrou.
- [ ] **Rien au-dessus de `y = −3,20`**, mesuré. Rien sous `y = −12,60`.
- [ ] **La demi-largeur atteint 18 m ou plus**, et l'évasement se fait en **marches**, pas en
      pente. Le rapport donne le profil de largeur station par station.
- [ ] **`AA_Emissive_Engine` uniquement sur la jonction de l'artère**, compté sur le binaire.
- [ ] **Zéro image embarquée**, `TEXCOORD_0` sur toutes les primitives.
- [ ] **Déterminisme** : trois exécutions, zéro octet divergent.
- [ ] **Rendu et REGARDÉ à la caméra du jeu** (`ADR-0006`), avec les trois groupes réels montés :
      une vue d'ensemble, et une vue **de la jonction** avec le corridor — c'est là qu'une
      erreur d'un centimètre se voit, et c'est la vue que personne ne pense à demander.

## Hors périmètre

- **Le code de jeu.** La phase est jouable et testée (959 tests) : ne toucher à aucun `.gd`,
  `.tscn` ni `.tres`. La dalle grise que la poupe remplace est posée par `CortegeStern.build()` —
  je la retirerai quand le binaire sera là.
- **Les nacelles, berceaux, verrous et bras** : livrés et réduits au `BRIEF-0105`.
- **Le corridor** : ses cinq tronçons ne changent pas d'un sommet.
