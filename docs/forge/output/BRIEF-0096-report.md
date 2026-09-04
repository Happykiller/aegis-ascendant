# BRIEF-0096 — compte-rendu de forge : le kit de la Citadelle de Défense

- **Agent** : `asset-forge`
- **Date** : 2026-09-04
- **Brief** : [`docs/forge/briefs/BRIEF-0096-citadelle-kit.md`](../briefs/archive/BRIEF-0096-citadelle-kit.md)
- **Plan** : [LOT 2 — la silhouette](../../plans/2026-09-03-citadelle-de-defense-midpoint.md)
- **Script source** : `tools/blender/build_citadel_kit.py` (Blender 4.5.11, kit `aegis_kit` **inchangé**)

## 0. Livrables

| Fichier | sha256 | Taille |
|---|---|---|
| `assets/imported/models/backgrounds/citadel_kit.glb` | `54545b6fca10c94a909d711a944306c24f8bcda486190b41dc2e72bb4f7ddb8d` | 125 316 o |
| `docs/forge/output/BRIEF-0096-planche-citadelle.png` | `043616bb56b2f99b81c457470d448991713ffd4ed4612502cf728e0d15463f98` | 1440 × 3120, **6 vignettes** |
| `tools/blender/build_citadel_kit.py` | — | le script **est** la source (`ADR-0008`) |

**Déterminisme** : `./scripts/build-hull.sh --check citadel_kit` → **« déterminisme OK »**, 0 octet
divergent sur deux exécutions successives (`blender45 -t 1`). Vérifié deux fois au cours du chantier
et une troisième sur le fichier livré.

---

## 1. La table que le moteur attend — emprises MESURÉES sur le binaire

Relevées sur le `.glb` produit, pas sur les constantes du script. Repère local d'une pièce :
**x de coque** (cuit dans la géométrie), **y depuis son assise**, **s relatif à la station 240**.

| Nœud | x min | x max | y min | y max | s min | s max | triangles |
|---|---|---|---|---|---|---|---|
| `citadel_gate` | −17,20 | 17,20 | 0,00 | 3,60 | −0,60 | +0,60 | 260 |
| `citadel_pylon` | **13,58** | 17,20 | 0,00 | 3,60 | −0,90 | +0,90 | 88 |
| `citadel_bastion` | 6,90 | 11,40 | 0,00 | 2,90 | −0,40 | +6,00 | 172 |
| `citadel_crown` | 7,40 | 10,00 | 0,00 | 0,60 | +1,60 | +5,40 | 124 |
| `citadel_relay` | 5,40 | 7,00 | 0,00 | 1,90 | +0,60 | +2,20 | 204 |
| `citadel_conduit` | 1,20 | 5,40 | 0,00 | **0,62** | +0,96 | +1,84 | 80 |
| `citadel_core` | −1,20 | 1,20 | 0,00 | 2,18 | +2,20 | +4,60 | 348 |
| `citadel_shield` | −1,80 | 1,80 | −1,50 | 1,50 | +1,98 | +2,22 | 28 |
| | | | | | | **TOTAL** | **1 304** |

**Les huit noms sont ceux de la table du brief, à la lettre.** Le harnais échoue le build si l'un
manque, si l'un est en trop, ou si l'un porte un enfant ou une transformation.

### Où poser — une translation, un yaw, rien de plus

| Nœud | translation locale | yaw | copies |
|---|---|---|---|
| `citadel_gate` | `(0, −6,60, 0,00)` | 0 | 1 |
| `citadel_pylon` | `(0, −7,65, 0,00)` | 0 **et** π | 2 |
| `citadel_bastion` | `(0, −6,50, −2,80)` | 0 **et** π | 2 |
| `citadel_crown` | `(0, −3,60, −3,50)` | 0 **et** π | 2 |
| `citadel_relay` | `(0, −4,30, −1,40)` | 0 **et** π | 2 — **détruite** |
| `citadel_conduit` | `(0, −4,30, −1,40)` | 0 **et** π | 2 |
| `citadel_core` | `(0, −4,58, −3,40)` | 0 | 1 — **détruite** |
| `citadel_shield` | `(0, −3,90, −2,10)` | 0 | 1 |

⚠️ **Le X de la coque est cuit dans la géométrie**, et c'est ce qui rend l'assemblage
indésynchronisable : tribord et bâbord reçoivent **exactement la même translation**, et pour seule
différence le yaw. Aucune arithmétique côté moteur.

⚠️ **Chaque pièce est centrée en Z sur son origine**, au micron, et le harnais l'exige sur les huit.
Le yaw de π envoie `(x, z)` sur `(−x, −z)` : une pièce dont la boîte n'est pas centrée en Z se
retrouverait à bâbord **décalée le long du vaisseau** de deux fois son excentricité — un bastion à
`s + 6` d'un bord et à `s − 6` de l'autre. Aucune bbox, aucun compte de triangles ne le verrait ;
il faudrait jouer la séquence et regarder les deux bords en même temps. Vérifié après coup sur la
scène montée : les cinq pièces miroitées occupent **la même plage en `s` des deux bords**.

### Les plafonds, composés assise + hauteur mesurée (`ADR-0041`)

| Nœud | assise | hauteur mesurée | sommet | plafond | marge |
|---|---|---|---|---|---|
| `citadel_gate` | −6,60 | 3,60 | **−3,00** | −3,00 (décor) | 0,00 |
| `citadel_pylon` | −7,65 | 3,60 | −4,05 | −3,00 | 1,05 |
| `citadel_bastion` | −6,50 | 2,90 | −3,60 | −3,00 | 0,60 |
| `citadel_crown` | −3,60 | 0,60 | **−3,00** | −3,00 | 0,00 |
| `citadel_relay` | −4,30 | 1,90 | **−2,40** | −2,40 (gameplay) | 0,00 |
| `citadel_conduit` | −4,30 | 0,62 | −3,68 | −3,00 | 0,68 |
| `citadel_core` | −4,58 | 2,18 | **−2,40** | −2,40 (gameplay) | 0,00 |
| `citadel_shield` | −3,90 (centre) | ±1,50 | **−2,40** | −2,40 (gameplay) | 0,00 |

**Aucun dépassement.** Le noyau domine le décor inerte de **0,60 m** — c'est ce surplomb, et lui
seul, qui le désigne comme le centre sans un mot de HUD. Le harnais ne teste pas « la pièce la plus
haute » (relais, noyau et bouclier sont **ex æquo à −2,40**, qui est le plafond du gameplay) : il
teste que **rien d'inerte n'approche le noyau à moins de 30 cm**.

---

## 2. Le test noir et blanc — ce que la planche montre

> « En noir et blanc, émissifs coupés, on identifie bastion ≠ relais ≠ noyau ≠ passage sans
> hésitation. » — consigne 19, et critère qui décide du lot.

La **vignette 1** de la planche est ce test, et la **vignette 2** (plan orthographique, noir et
blanc) le refait sous l'angle où la caméra du jeu travaille vraiment — elle plonge à 70°, donc à
**20° de la verticale**. Les quatre signatures sont **mesurées**, pas affirmées :

| Pièce | Axe | Mesure qui le tient (harnais bloquant) |
|---|---|---|
| porte | **LONGUEUR** | 34,40 m pour 1,20 m d'épaisseur = **28,7 : 1** ; refus sous 20 : 1, et refus si une autre pièce devient plus longue |
| bastion | **MASSE ÉTAGÉE** | **4,50 m de large pour 2,90 m de haut** — plus large que haut, refusé sinon ; deux niveaux, −3,60 puis −3,00 |
| relais | **BRANCHEMENT** | fût prismatique 1,60 × 1,90 (rapport **1,19**, borné à 0,90–1,45), collier débordant de **0,18 m**, conduit de **4,20 m** de long pour 0,62 m de haut (refus sous 6 : 1) |
| noyau | **RÉVOLUTION** | constance du rayon **1,0000** sur 16 facettes, contre **1,2939** pour le relais — refus si le noyau dépasse 1,05 ou si le relais descend sous 1,10 |

**La denture existe et elle se voit d'en haut.** Douze dents, six par rangée, en opposition de
phase sur `x ±2,40` : vues en plan, elles dessinent un damier qui coupe la poutre en son milieu.
C'est la figure qu'on lit sur la vignette 2 sans une ligne de légende — et c'est par là que la
porte s'ouvrira au LOT 4.

⚠️ **La denture est en PLAN et non en élévation, et c'est une conséquence de la caméra.** Un joint
de *finger cut* dans la face avant — la solution évidente, celle d'une vraie porte — est présenté à
20° de l'incidence rasante et ne rend presque aucun pixel. C'est exactement la mesure qui avait
coûté une couronne émissive au nœud d'épine (`BRIEF-0094`) ; elle n'a pas été repayée ici.

**Une correction faite APRÈS avoir regardé le premier tirage** (`ADR-0006`, dans les deux sens) :
le capot du relais portait `AA_Trim` comme celui du noyau. En noir et blanc, les deux pièces se
présentaient alors toutes deux comme « un volume sombre coiffé d'une tache claire » — la seule
lecture que le brief interdit. Le relais est désormais **uniformément sombre**, tenu par l'ombre de
son collier ; le noyau garde sa pointe claire. Les deux ne partagent plus aucun signal.

---

## 3. La règle dure — aucun émissif hors des pièces qui meurent

| Pièce | émissif (m², kit brut) | part de sa propre aire |
|---|---|---|
| `citadel_relay` | 1,68 | **11,3 %** |
| `citadel_core` | 4,19 | **20,3 %** |
| **les six autres** | **0,000** | — |

Vérifié **par matériau sur le binaire**, pas à l'œil : le harnais compte l'aire `AA_Emissive_Engine`
pièce par pièce et échoue le build si une septième en porte un millimètre carré — ou si l'une des
deux destructibles n'en porte plus. C'est la règle du nœud d'épine, reprise telle quelle.

Les deux émissifs **regardent la caméra** : ce sont des anneaux quasi horizontaux (relais : bague
de r 0,74 à 0,52 ; noyau : ceinture puis couronne de r 1,20 à 1,00), coiffés d'un capot sombre.
Un flanc lumineux, même évasé, est présenté presque de profil à une caméra qui plonge de 70° et ne
rend quasiment rien — mesure de `BRIEF-0094`.

---

## 4. Les deux écarts au tableau du brief — assumés, mesurés, et dits

### 4.1 `citadel_pylon` va jusqu'à **x = 13,58** et non 15,60

Le tableau du brief donne au portique « x 15,60 à 17,20 ». **La page suivante du même brief** lui
demande de « venir s'appuyer sur la **lisse d'épaule** (`x ≈ 13,88`, `Y ≈ −7,65`) ». Les deux
énoncés ne peuvent pas être vrais ensemble : la lisse est *inboard* de l'emprise. Un portique
arrêté à 15,60 flotte au-dessus du vide — le défaut même qu'il existe pour corriger, et « un mur
invisible est la même injustice qu'une tourelle qu'on croit pouvoir raser ».

Le talon descend donc chercher la coque, et **la morsure est mesurée contre le profil réel** (taper
du tronçon 3 compris, `_flank_x()`), pas contre la table nominale :

- morsure du talon dans le flanc : **0,19 m à 0,56 m** sur toute sa hauteur d'appui ;
- première valeur essayée, 13,75 : morsure de **0,002 m** au point haut — le portique *effleurait*
  la coque. Le flanc n'est pas vertical (il rentre de 0,53 m entre −7,65 et −6,35) : c'est cette
  pente, et le taper, qui décident, pas la cote nominale.

Le surplomb, lui, est chiffré : coque **28,56 m** de large à `s = 240` (taper compris, et non 28,00),
porte **34,40 m** → **2,92 m de poutre en l'air par bord**, que le portique couvre **en entier**
(x 13,58 → 17,20). La porte occupe **82,7 %** du cadre de la caméra au plan du pont (**41,60 m**,
recalculé, pas recopié).

### 4.2 `citadel_conduit` culmine à **+0,62** et non +0,35

Entre son départ (`x 5,40`, pont intérieur à −4,30) et son arrivée (`x 1,20`, rebord de l'artère à
−4,02), **la peau monte de 0,28 m** — mesuré sur `cortege._surface_y`, pas estimé. Un caisson de
0,35 m assis à −4,30 serait enterré **aux quatre cinquièmes** à son extrémité intérieure,
c'est-à-dire précisément là où il doit se lire.

Le dessus est donc **horizontal à −3,72** et c'est le **dessous** qui suit le terrain. Mesures sur
la peau réelle, sur toute l'emprise et sur toute la largeur en `s` :

- garde minimale au-dessus de la peau : **0,302 m** ;
- flottement maximal : **0,023 m** ; enterrement maximal : **0,038 m**.

Le talus du caisson est calé sur les abscisses **réelles** du profil (x 1,66 → 2,44 après taper) et
non dessinées : posé ailleurs, il faisait flotter la pièce d'une dizaine de centimètres sur un
demi-mètre, en silence.

---

## 5. Ce que le conduit raconte, et où il s'arrête

C'est la pièce que le brief désigne comme la plus importante, et elle ne porte **aucun émissif** :
elle dit « ceci alimente cela » **en géométrie**, donc au test noir et blanc. Sa ligne de faîte est
horizontale et rectiligne sur 4,20 m, cap sur l'axe, portée par trois colliers.

⚠️ **Il s'arrête à `x = 1,20`, sur le rebord de l'artère, et non sur le noyau** — le brief le fige
ainsi, et c'est juste : les quatre conduits lumineux du fond du canal prennent le relais sur les
deux derniers mètres. Le chemin complet se lit **relais → caisson → artère → noyau**, et le
vaisseau fournit déjà le troisième terme. Son bouchon intérieur porte le seul `AA_Trim` de la
pièce : c'est là qu'elle passe la main.

---

## 6. Textures, UV, densité

Le brief porte sa section **Texture** (`ADR-0028`) et elle est sans ambiguïté : **aucune demande
`TEX-NNNN` nouvelle**, `TEX-0015` livrée mais **non câblée par ce lot** (le panneau porte
`AA_Glass` ; `AA_Shield_Field` est du LOT 3), `TEX-0016` refusée et **aucun ambre posé ici**.

- **Aucune texture dans le `.glb`** : zéro image, zéro `baseColorTexture` / `normalTexture` /
  `occlusionTexture` / `emissiveTexture` — le harnais échoue le build si l'un apparaît.
- **`TEXCOORD_0` COMPTÉ, pas supposé** : **22/22 primitives**, et **22/22 en `TANGENT`**.
- **Dépliage en boîte à 0,200 tuile/m** (5,00 m par tuile) — la densité du bordé, de `bay_kit`,
  `turret_kit` et `spine_kit`. Deux échelles sur un même slot était la faute corrigée par
  `BRIEF-0090`, et le verrou est le seul objet du niveau qui touche la coque sur 34 m.

| Pièce | densité min | max | moyenne | m/tuile | anisotropie max |
|---|---|---|---|---|---|
| `citadel_gate` | 0,136 | 0,200 | 0,198 | 5,04 | 1,47 |
| `citadel_pylon` | 0,197 | 0,200 | 0,200 | 5,01 | 1,02 |
| `citadel_bastion` | 0,140 | 0,200 | 0,196 | 5,10 | 1,43 |
| `citadel_crown` | 0,141 | 0,200 | 0,198 | 5,05 | 1,41 |
| `citadel_relay` | 0,115 | 0,200 | 0,191 | 5,24 | 1,73 |
| `citadel_conduit` | 0,149 | 0,200 | 0,198 | 5,05 | 1,35 |
| `citadel_core` | 0,120 | 0,200 | 0,181 | 5,53 | 1,67 |
| `citadel_shield` | 0,200 | 0,200 | 0,200 | 5,01 | 1,00 |

L'anisotropie plafonne à **1,73**, qui est la **borne théorique de la projection en boîte**
(√3, atteinte par une facette également inclinée sur les trois plans) : aucune face n'est étirée
au-delà de ce que la méthode impose. La densité minimale reste au-dessus de la borne basse de la
méthode (0,113). **La planche porte sa vignette de damier UV**, à la perspective du jeu : la même
case sur la coque et sur le kit, raccord compris.

---

## 7. Matériaux, aires, budget

| Matériau | kit brut | | verrou assemblé | | ce qui en est **vu** | |
|---|---|---|---|---|---|---|
| `AA_Hull` | 397,67 m² | 65,5 % | 531,44 m² | 63,2 % | 307,32 m² | 71,3 % |
| `AA_Greeble` | 179,68 m² | 29,6 % | 274,95 m² | 32,7 % | 91,85 m² | 21,3 % |
| `AA_Glass` | 19,34 m² | 3,2 % | 19,34 m² | 2,3 % | 19,34 m² | 4,5 % |
| `AA_Trim` | **4,50 m²** | **0,7 %** | 7,76 m² | 0,9 % | 7,76 m² | 1,8 % |
| `AA_Emissive_Engine` | 5,86 m² | 1,0 % | 7,54 m² | 0,9 % | 4,87 m² | 1,1 % |
| **TOTAL** | 607,06 m² | | 841,03 m² | | 431,14 m² | |

- **`AA_Trim` à 0,7 %** de l'aire du kit (plafond du brief : 3 %) — il ne sert qu'aux **merlons de
  couronne**, aux **dents** et au **bouchon intérieur du conduit**. Aucun liséré continu : 34 m
  d'arête ivoire occupent plus de pixels que n'importe quelle pièce du niveau (leçon de
  `BRIEF-0089`, payée deux fois).
- **Cinq slots employés**, ceux que le brief nomme. `AA_Panel` et `AA_Marking_Red` sont **refusés
  par le harnais** : pas de violet surfacique de plus sur ce vaisseau, pas de rouge.
- **1 304 triangles pour le kit** (budget 3 000), **1 972 pour le verrou assemblé** (13 instances).
  La citadelle est posée **une fois par partie** ; à titre de comparaison, `turret_kit` coûte
  2 240 × 38 instances.
- L'aire « vue » est une **approximation dite comme telle** : la tranchée de bastion n'étant pas
  encore creusée, la part enterrée est estimée sur la peau actuelle.

---

## 8. Les harnais bloquants, et les quatre défauts qu'ils ont attrapés

Tout ce qui suit **échoue le build**, sur le binaire relu, jamais sur la scène en mémoire.

| Harnais | Ce qu'il prouve |
|---|---|
| noms / racines / identité | les huit nœuds, sans enfant ni transformation |
| `_assert_solid` (partagé avec `turret_kit`) | coque fermée, bobinage cohérent, **volume signé positif** par coque connexe |
| `SHELL_COUNT` | 13 / 4 / 1 / 5 / 1 / 4 / 1 / 1 volumes — un volume fusionné ou oublié ne se voit sur aucune planche |
| émissif par pièce | zéro hors `citadel_relay` et `citadel_core`, non nul sur les deux |
| emprises vs brief | six cotes par pièce, avec **deux écarts nommés** (§4) ; toute autre dérive échoue |
| centrage en Z + « franchement tribord » | le miroir par yaw π est exact le long du vaisseau |
| plafonds `ADR-0041` | assise du plan **composée** avec la hauteur mesurée |
| silhouettes | les quatre rapports du §2 |
| `_pylon_bite` | le talon **mord** le flanc réel (taper compris) |
| `_conduit_ground` | garde, flottement et enterrement sur la peau réelle |
| UV / tangentes / textures / couleurs réservées | 22/22, zéro image, ni cyan `#3FD9E8` ni corail `#FF5A3D` |
| densité de texels | bornes de la projection en boîte |
| budgets | 3 000 triangles, `AA_Trim` ≤ 3 % |

**Quatre défauts attrapés pendant la forge, et aucun ne se serait vu sur une image :**

1. **104 arêtes retournées** sur la porte. Cause : une marche de section pose deux anneaux à la
   **même** cote d'axe ; le `want` radial y est orthogonal à la vraie normale, le produit scalaire
   vaut zéro et le bobinage se décide au hasard des arrondis. Corrigé en n'appliquant l'indice
   axial **qu'aux facettes réellement axiales**.
2. **63 arêtes de bord** sur la porte. Cause : sur une marche où seul le sommet change, trois des
   quatre points sont **alignés** ; la facette de fermeture est plate. La garder fabrique un
   triangle d'aire nulle (tangente instable, donc byte-identité perdue), la supprimer ouvre une
   **jonction en T**. Corrigé en remplaçant les créneaux lofté par des **dents séparées** et les
   marches par des **rampes de 0,20 m** — invisibles à 23 px/m, et prouvables.
3. **Deux bouchons retournés** sur le portique et le conduit : ces deux pièces se construisent en
   **descendant** leur axe, et le sens d'empilement était supposé. Il est désormais **mesuré**.
4. **Le chapiteau du portique affleurait ses jambes** sur quatre plans : `remove_doubles` soudait
   les sommets et l'arête commune portait quatre faces. Deux coques qui s'interpénètrent doivent se
   **chevaucher**, jamais s'affleurer.

---

## 9. ⚠️ Trois choses à trancher côté moteur

### 9.1 La seconde tourelle de garde tombe **dans** la couronne

`CortegeCitadel.TURRET_S = [0.40, 2.20]` à `TURRET_X = 9,20`, sur le pont du bastion à −3,60.
`citadel_crown` occupe `s +1,60 → +5,40` et `x 7,40 → 10,00`, **assise −3,60** : la tourelle de
`s + 2,20` est donc **0,60 m à l'intérieur** de la couronne, en x comme en s. La première
(`s + 0,40`) est libre, à 1,20 m en avant.

Deux issues, au choix du concepteur, et les deux tiennent aux cotes actuelles :
**reculer la seconde tourelle à `s ≤ +1,15`**, ou **avancer la couronne à `s ≥ +2,90`** (l'emprise
de la couronne est figée par le brief, donc c'est la première qui coûte le moins).

Accessoirement : la première tourelle, à `s + 2,40` en repère bastion, se pose à **0,38 m** du bord
du pont ; un socle léger de rayon ≈ 0,50 m déborde alors de ~0,12 m. `s + 1,00` la met au large.

### 9.2 L'assise du bouclier est **décidée**, pas relevée

Le brief donne « centre du panneau, Y −1,50 → +1,50 » sans dire où tombe ce centre. Retenu :
**−3,90**, qui met son arête haute **exactement au sommet du noyau** (−2,40) et son pied à −5,40,
sous le fond du canal — un champ sort de la coque, il ne se pose pas dessus. Le panneau est posé
**1,30 m en avant du noyau** (`s 242,10`), donc du côté d'où vient le joueur : le tir s'arrête
*devant* la cible, pas *sur* elle. À confirmer ou à corriger d'un chiffre.

### 9.3 Un défaut de planche qui touche **les trois kits précédents**

L'importateur glTF pose `rotation_mode = 'QUATERNION'` sur tout ce qu'il crée. Écrire
`obj.rotation_euler` sur un objet en mode quaternion **n'a aucun effet** : la valeur est rangée,
jamais lue, et Blender ne dit rien. Au premier tirage de cette planche, les cinq pièces de bâbord
se sont posées **exactement par-dessus celles de tribord** — un demi-verrou, et le « côté saboté »
de la vignette 4 était le même que le côté intact.

⚠️ **`build_spine_kit._place()`, `build_turret_kit._place()` et `build_bay_kit._import()` écrivent
la même ligne.** Leurs yaw de planche sont donc ignorés eux aussi : l'**azimut des tourelles** et le
**miroir des entretoises d'épine** n'ont jamais été rendus dans les planches de `BRIEF-0093` et
`BRIEF-0094`. Corrigé ici (`rotation_mode = "XYZ"` d'abord) ; **hors périmètre de ce brief** pour
les trois autres fichiers, mais la correction est d'une ligne et les planches méritent d'être
retirées.

---

## 10. La planche de recette (`--plate`)

`blender45 -b -t 1 -P tools/blender/build_citadel_kit.py -- --plate`, Cycles CPU 32 échantillons
+ débruitage, six vignettes empilées par numpy (pas de PIL dans le Python de Blender).

| # | Vignette | Ce qu'elle prouve |
|---|---|---|
| 1 | **Test d'acceptation — noir et blanc, émissifs coupés** | bastion ≠ relais ≠ noyau ≠ passage, dans **le même cadre**, à la caméra de `graybox.tscn` sans retouche (0, 14, 5), FOV 62, Specter-9 réel à sa place |
| 2 | **Le plan, en noir et blanc** | les quatre axes vus comme la caméra les voit (elle est à 20° de la verticale) : une ligne qui traverse, deux masses, deux branchements, **un seul volume rond** — et la **denture** |
| 3 | Le même cadre **en couleur** | ce que l'émissif **ajoute** à une fonction déjà lisible : trois signaux magenta, et rien d'autre |
| 4 | **Trois quarts, un relais abattu** | le partage en huit nœuds : bastion, couronne et portique **restent**, le relais et son conduit ont disparu |
| 5 | **De face, à la largeur exacte du cadre de jeu** | le surplomb de 2,92 m par bord, et le portique qui va chercher la lisse d'épaule |
| 6 | **Damier UV** | la même case sur la coque et sur le kit, raccord compris |

---

## 11. Ce que ce lot ne fait pas

- **La tranchée de bastion** (fond −6,50) : hors périmètre, prise comme acquise. Les vignettes la
  montrent donc **non creusée** — le bastion émerge de 1,37 m du pont médian au lieu des 2,90 m
  qu'il lira une fois la tranchée faite. Le kit, lui, est bâti pour −6,50.
- **`AA_Shield_Field` et `TEX-0015`** : LOT 3.
- **Les quatre états visuels** et **l'ouverture animée** : LOT 3 et LOT 4. Ce lot ne livre que la
  **denture** qui la rendra possible.
- **Les tourelles de garde** : `turret_kit` en échelle légère, posé par le moteur. Elles
  n'apparaissent sur la planche que pour montrer le conflit d'emprise du §9.1.
