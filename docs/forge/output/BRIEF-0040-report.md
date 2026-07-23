# BRIEF-0040 — compte-rendu : Pale Leviathan, coque animable, texturable et à sa taille

- **Brief** : `docs/forge/briefs/BRIEF-0040-pale-leviathan-reforge.md`
- **Exécuté par** : asset-forge
- **Date** : 2026-07-23
- **Références lues avant production** : `docs/forge/CHARTE_CREATIVE.md`, le brief,
  les trois planches `assets/reference/concepts/pale_leviathan_{parts,core_states,phases}_sheet.png`,
  `ADR-0018`, `docs/design/BOSS_PALE_LEVIATHAN.md` §9, `tools/blender/build_choir_harvester.py`
  (le modèle de reforge de BRIEF-0039).

---

## 1. Livrables

| Fichier | Nature |
|---|---|
| `tools/blender/build_pale_leviathan.py` | le script reforgé — il **est** la source de l'asset (ADR-0008) |
| `assets/imported/models/bosses/pale_leviathan.glb` | régénéré par `./scripts/build-hull.sh pale_leviathan` |
| `docs/forge/output/BRIEF-0040-report.md` | ce compte-rendu |
| `docs/forge/output/BRIEF-0040-planche-quatre-vues.png` | planche de recette au repos (`tools/render-hull.py`) |
| `docs/forge/output/BRIEF-0040-poses-de-recette.png` | les quatre poses regardées : repos / gueule ouverte / coquille basculée / plaques arrachées |

Provenance mise à jour dans `assets/licenses/ASSET_PROVENANCE.csv` : la ligne `pale_leviathan_hull`
est **remplacée** (pas dupliquée), deux lignes ajoutées pour les planches de rendu.

**Aucun `.gd`, `.tscn`, `.tres`, ni `project.godot` n'a été touché** (écrivain unique — le module de
combat s'écrit en parallèle). `aegis_kit.py` est réutilisé **sans modification**.

---

## 2. Chiffres réels (relevés sur le `.glb` livré, pas sur la scène)

| Mesure | Valeur | Contrat |
|---|---|---|
| Bounding box (Godot X × Y × Z) | **11,0334 × 3,1531 × 13,9972 m** | 11,0 × ≤ 3,20 × 14,0 (±3 %) → écart **0,30 %** en X, **0,02 %** en Z |
| Centre (pivot) | **(+0,0001, +0,0065, −0,0014)** | ±0,02 m en X et Z |
| Triangles | **31 098** | budget 40 000 (plafond ADR-0011 de la classe boss : 90 000) |
| Sommets | 47 921 | — |
| Poids | 2 619 144 o | — |
| Matériaux | les **7** présents : `AA_Emissive_Engine` 7 957 t, `AA_Greeble` 11 714 t, `AA_Trim` 4 756 t, `AA_Panel` 3 458 t, `AA_Hull` 2 785 t, `AA_Glass` 248 t, `AA_Marking_Red` 180 t | `ak.MATERIAL_ORDER` |
| Attributs de sommet | `POSITION`, `NORMAL`, **`TEXCOORD_0`**, **`TANGENT`** | UV **et** tangentes |
| Nœuds maillés | **30** (1 coque + 29 pièces mobiles) | contrat de noms |
| Points d'attache | **14** | les 14 demandés |
| Déterminisme | `./scripts/build-hull.sh --check pale_leviathan` → **0 octet divergent** | sha256 `b475fc240d553912dd524b8d7ac72d49aef6e0d4cf929bfb3838e8d24fc727b5` |

Hiérarchie exportée, relue dans le JSON du `.glb` :

```
Body                                            (hull, statique)
Shell_Ring -> Shell_Crescent -> Plate_01..04
Core -> { Maw_Lip -> Node_01..03 , Ring_01..05 , Heart }
Spike_0X -> Spike_0X_Mid -> Spike_0X_Tip        (x4, racines détachables)
```

Points d'attache livrés : `Core_Center`, `Maw_Center`, `Tunnel_End`, `Muzzle_C`, `Muzzle_L`,
`Muzzle_R`, `Muzzle_Plate_01..04`, `Muzzle_Spike_01..04`.

---

## 3. Le tableau de dégagement — mesuré à fond de course, à chaque build

Ce tableau **n'est pas rédigé à la main** : il est imprimé par `_clearance_table()` à chaque
exécution du script, sur le maillage réellement livré, en rejouant les rotations que le combat
écrira (repère Godot, euler YXZ, ou basis `UP × radial` pour les charnières tangentielles). Une
marge nulle ou négative lève `ContractError` et **empêche l'export** : le `.glb` ne peut pas exister
si une pièce mord.

| Pièce | Débattement appliqué | Marge minimale mesurée | Pose la plus serrée |
|---|---|---|---|
| `Shell_Ring` / coque | orbite **360°** continu | **61,8 mm** | orbite 0° |
| `Shell_Crescent` / coque | orbite 360° × bascule **0 → 65°** | **206,7 mm** | orbite 120°, bascule 0° |
| `Plate_01..04` / coque, coquille et entre elles | chute **0 → −80°** × orbite × bascule | **97,8 mm** | orbite 270°, bascule 65°, chute 0° (`Plate_04`) |
| `Core` / coque | rotation **360°** continu | **305,4 mm** | noyau 120° |
| `Maw_Lip` / coque et noyau | ouverture **0 → 90°** | **52,4 mm** | noyau 30°, lèvre 0° (griffes au-dessus du noyau) |
| `Node_01..03` / lèvre, noyau, coque | rétraction **0 → −60°** × lèvre × noyau | **48,0 mm** | noyau 120°, lèvre 27° (`Node_02` contre la lèvre) |
| `Ring_01..05` / paroi du puits et entre eux | **360°** continu, vitesses distinctes | **63,6 mm** | `Ring_04`–`Ring_05` |
| `Spike_01..04` / coque | pointage **±40°** | **114,1 mm** | `Spike_02`, pointage 0° |
| `Spike_0X_Mid` et `_Tip` / coque et chaîne | flexion **±25°** chacun (plan de jeu) | **110,1 mm** | `Spike_02_Mid`–`Spike_02_Tip` |
| *(en plus)* `Maw_Lip` ouverte / **aplomb du puits, vue de dessus** | lèvre 90°, nœuds −60° | **103,3 mm** | noyau 30° |

**Rayons d'exclusion de charnière** (une articulation réelle s'interpénètre par construction : rotule
dans son logement, racine dans son berceau ; l'exclusion est **symétrique**, appliquée des deux côtés,
et licite parce qu'une rotation autour d'un axe passant par le pivot conserve la distance au pivot) :
lèvre 0,14 m ; nœuds 0,24 m ; plaques 0,16 m ; croissant 0,18 m ; épines 1,20 × le rayon local du bras
à l'articulation (0,36 à 0,51 m).

### La ligne qui n'est pas conforme, et pourquoi

**La flexion `_Mid` / `_Tip` est mesurée dans le plan de jeu (`rotation.y`), pas dans le plan
vertical.** Le script mesure aussi la flexion verticale (`rotation.x`) et imprime son plafond réel :

```
[i  ] flexion VERTICALE (rotation.x) encaissee sans morsure : +/-5 deg
```

Ce n'est pas un défaut du modèle, c'est une conséquence des dimensions imposées : le boss fait **3,05 m
d'épaisseur pour 14 m de long**, et une épine est posée ~30 cm au-dessus du pont. Faire piquer de 25°
un maillon de 2,5 m demande **1,05 m de vide sous lui** ; il n'y en a nulle part, et il n'y en aurait
pas davantage sur une coque deux fois plus épaisse que le plafond d'ADR-0018.

Ce que ça implique pour `leviathan_combat.gd` : **écrire la flexion des épines sur `rotation.y`**
(l'axe du pointage), ce qui est de toute façon le seul plan où un fouettement se lit sous une caméra
qui regarde de dessus. Si un jour la flexion verticale est voulue (une épine qui pique vers le joueur
avant de se détacher), elle est jouable **au-delà de ±5° seulement une fois l'épine détachée**, quand
la coque n'est plus sous elle.

### Vérifié par rendu, pas par calcul

`docs/forge/output/BRIEF-0040-poses-de-recette.png`, quatre panneaux :

1. **repos, vue de dessus** — le noyau bouche la gueule, la lèvre et ses trois nœuds surplombent son
   bord arrière ;
2. **`Maw_Lip` à 90°, maillage `Core` masqué, vue de dessus** — c'est l'angle de la caméra de jeu :
   le puits est **entièrement dégagé**, les cinq anneaux se lisent en enfilade et le `Heart` brille au
   fond, dans l'axe. Aucune matière de la lèvre ni des nœuds ne passe au-dessus de l'ouverture
   (mesure : 103,3 mm au-delà du bord du puits, sur toute l'orbite du noyau) ;
3. **`Shell_Crescent` à 65°, vue de profil** — la coquille se cabre comme un capot, sans qu'un seul
   point ne plonge vers la coque ;
4. **`Plate_01..04` à −80°, trois-quarts** — les quatre plaques se dressent vers l'extérieur ; elles ne
   se mordent ni entre elles, ni avec la coquille, ni avec le pont.

⚠️ **Un piège de recette rencontré, et corrigé** : l'importateur glTF de Blender pose
`rotation_mode = 'QUATERNION'`. Écrire `rotation_euler` sur un nœud importé **ne fait rien**, sans
erreur ni message — mes deux premiers rendus « gueule ouverte » montraient donc une lèvre parfaitement
immobile, et j'ai failli les livrer comme preuve. Les rendus ci-dessus sont produits après correction,
et ils **valident indépendamment** la convention de rotation du harnais de mesure : les deux
implémentations, écrites séparément, donnent le même mouvement (lèvre qui se relève vers l'arrière à
+90°, croissant qui se cabre à +65°, plaque qui se soulève vers l'extérieur à −80°).

---

## 4. Choix créatifs, et ce qui les a imposés

### 4.1 La coque est plate, et tout se joue dans le plan de la caméra

La caméra de jeu regarde le plan à 20° de la verticale : d'un boss de 14 m, le joueur voit sa face
supérieure. Le puits descend donc **vers le bas**, la gueule s'ouvre **vers le haut**, et la coquille
orbite autour d'un axe **vertical** — les quatre plaques défilent latéralement face au joueur, ce qui
fait de la fenêtre de tir de la phase 1 une **géométrie** et non un minuteur (ADR-0018 §2). La
silhouette est un disque blindé de 3,05 m d'épaisseur pour 14 m : tout ce qui compte se voit d'en
haut, rien ne se cache sous le ventre.

### 4.2 Les trois décisions de charnière, qui sont des décisions de plan

- **`Maw_Lip`** — en repère Godot, `rotation.x = +90°` fait **monter ce qui est en avant du pivot**.
  Sa charnière est donc posée *derrière* l'ouverture (y = +2,14 en repère d'auteur), et toute sa
  matière est en avant d'elle. À 90° la pièce se dresse **hors du puits** ; sa trace en vue de dessus
  se replie sur une bande de 40 cm située au-delà du bord de l'ouverture. Une charnière posée au
  centre aurait fait plonger la moitié arrière dans la coque ; posée devant, elle aurait laissé la
  lèvre en travers du tunnel — et la phase 4 se joue précisément dans cet axe de vue.
- **`Plate_0X`** — charnière **tangentielle sur le bord interne**, axe `UP × radial` (la convention
  que `harvester_combat._bind_iris()` a déjà établie pour l'iris du mini-boss : le code déduit l'axe
  de la position du nœud, sans donnée supplémentaire). À −80° la plaque **se soulève vers
  l'extérieur**. Elle ne peut pas tomber vers le bas : sous elle il y a la coquille, puis le pont ;
  une chute vers l'intérieur traverse les deux, quel que soit le réglage. Le geste lit comme une
  écaille qu'on arrache — c'est le panneau CORE EXPOSED de la planche des phases.
- **`Shell_Crescent`** — charnière tangente au bord arrière, **et posée derrière les plaques**
  (y = +3,86), pas derrière le croissant seul (y = +3,02). Les plaques sont ses enfants : une plaque
  restée en arrière de l'axe plonge dans la coque dès les premiers degrés. C'est exactement ce que la
  mesure a trouvé au premier essai (morsure à 56° de chute, charnière à y = +3,26).

### 4.3 L'invariant de piste — la leçon la plus chère de cette reforge

La coquille orbite au-dessus du pont sur 360°. Tout ce que la coque pose **sous elle** doit rester
sous un plafond, sinon c'est raboté une fois sur deux — et la bounding box au repos n'en dit rien.
Le script porte l'invariant en clair (`SHELL_TRACK`, `track_ceiling()`), parce que la première version
l'a violé deux fois :

- les trois ponts d'armes de proue étaient à r = 3,5 m, en pleine piste : **~500 triangles en
  interpénétration** avec l'anneau porteur. Ils sont désormais sur le bec, à r ≥ 5,1 m ;
- les mâts d'épine étaient des longerons obliques à demi-largeur constante : leur section débordait
  vers l'axe, dans la course des plaques. Ils sont désormais **verticaux**, leur axe passant sous le
  pivot, terminés par un **pion plus mince que l'épine** — qui vit à l'intérieur d'elle et n'en sort
  jamais, quel que soit le pointage. C'est le même remède que la rotule sphérique du canon du
  Harvester : ce qui est centré sur l'axe de rotation est invariant par cette rotation.

### 4.4 Le détail en fraction, jamais en coordonnée absolue

Corollaire hérité du Specter-9, appliqué partout où c'était possible :

- les écailles dorsales, les crêtes de bec et de dard, les membranes et les greebles sont posés en
  **fraction de la corde restante** de la jupe (`hull_top(r, azimut)`) : si le contour change, ils
  suivent au lieu de flotter ;
- le rayon des cinq anneaux du puits est **dérivé de la paroi** (`ring_radius()` lit
  `shaft_radius()` à l'altitude de leur **arête basse**, la plus serrée, pas à leur mi-hauteur — cinq
  centimètres d'écart, et la mesure les avait effectivement refusés) ;
- les nervures des anneaux saillent **vers l'intérieur** du puits : vers l'extérieur, elles mangeaient
  le jeu radial que `ring_radius()` venait de calculer. C'est le détail-posé-en-absolu exact que le
  corollaire interdit.

### 4.5 Ce que les planches ont dicté

- **`parts_sheet`** (la référence) : quatre pièces d'un même éclaté — corps, anneau, croissant,
  plaques — puis noyau, lèvre, nœuds, anneaux internes, cœur, et quatre épines en **trois segments**.
  Le contrat de noms est respecté à la lettre ; les deux erreurs de légende signalées par le brief ne
  sont **pas** recopiées (le 3ᵉ segment s'appelle `Tip`, et la largeur est bien de 11 m).
- **`core_states_sheet`** : le noyau est une croûte de plaques violettes **soulevée facette par
  facette** sur une sphère émissive — la lumière sort *d'entre* les plaques, elle n'est pas peinte
  dessus (CRACK VEINS). La proportion de croûte est passée de 42 % à **78 %** après le premier rendu :
  à 42 %, le noyau lisait comme une ampoule et non comme une coquille fissurée. Les anneaux internes
  portent leur ouverture décalée d'un anneau au suivant — l'**OFFSET GATE** que la planche nomme, et
  qui interdit la descente en ligne droite.
- **`phases_sheet`** : la coquille en croissant est un **anneau incomplet** (230° de matière, les 130°
  manquants ouvrant sur le quadrant avant-tribord, là où le boss est le plus armé).
- **La silhouette** : le dard est **fourchu**. La première version, dard en pointe unique, lisait comme
  une soucoupe volante ; la fourche rend la lecture « créature ». Contrainte technique associée, notée
  dans le script : les deux pointes doivent tomber sur des azimuts **échantillonnés** (81° et 99°,
  multiples du pas de 9°), sinon la discrétisation les rabote, la longueur tombe à 13,7 m — encore
  dans la tolérance — mais **le centre dérive de 15 cm, sept fois la tolérance de pivot**.

### 4.6 Palette

Palette Null Choir de la charte §3, sans écart : anthracite `#24252B` (coque), violet `#452663`
(segments), ivoire `#DDDCD2` (carapaces — le boss est *pâle*, la majorité des tuiles sont ivoire),
magenta `#D93D9C` (noyau, coutures, bouches), vert maladif `#7C9E52` **très limité** (un marquage de
pont, quatre nodules au pied des mâts : 180 triangles sur 31 098, soit 0,58 %). Aucun cyan, aucun
corail : ils sont réservés au gameplay (DA §6).

Après le premier rendu, la probabilité qu'une contremarche de tuile soit émissive est passée de 0,50 à
**0,26** : à une sur deux, le magenta lisait comme des confettis semés sur la carapace au lieu d'un
réseau de coutures, et il volait la vedette au noyau — qui est *la* cible (spec pilier B).

### 4.7 Les UV

`ak.box_project_uv(obj, 0.18)` sur **chacun des 30 maillages**, dans la passe de finition, après le
chanfrein et la triangulation (les deux créent des faces ; déplier avant les laisserait sans UV
cohérente). 0,18 texel/m = **une tuile pour 5,55 m** : sur cette coque, les écailles de
`leviathan_scales_height` (période mesurée 0,99 m) lisent à ~1,1 m, l'échelle des planches.

⚠️ **Un verrou silencieux découvert au passage** : l'exportateur glTF refuse le calcul mikktspace dès
qu'un maillage porte une face de plus de quatre sommets — « *Tangent space can only be computed for
tris/quads, aborting* » — et **exporte quand même, sans l'attribut `TANGENT`**. Les `cap_ring` du
script (culots, tranches de secteur) en produisent des dizaines. Une passe `_triangulate_ngons()` est
donc obligatoire, et pas cosmétique : sans elle la coque a des UV, donc l'air texturable, et tout
shader de relief y reste plat. `build_choir_harvester.py` **n'a pas cette passe** — voir §6.

---

## 5. Limites connues

1. **La flexion verticale des épines plafonne à ±5°** (§3). Le contrat de ±25° est tenu dans le plan
   de jeu, pas dans le plan vertical, et ce n'est pas rattrapable sur une coque de 3,05 m
   d'épaisseur.
2. **`Maw_Lip`, `Ring_01..05` et `Heart` sont enfants de `Core`.** C'est le contrat de noms, et c'est
   cohérent (tout le puits tourne avec le noyau). Conséquence à connaître avant d'écrire la phase 4 :
   `Core.visible = false` **cache tout le puits avec lui**. Pour escamoter le noyau, agir sur son
   *maillage* (matériau, échelle) et non sur la visibilité du nœud. Le script le dit dans son en-tête.
3. **Les points d'attache ne suivent pas les pièces mobiles.** `ak.attach_point()` ne sait pas
   parenter : `Muzzle_Plate_01..04` et `Muzzle_Spike_01..04` sont des nœuds **racines figés à la pose
   de repos**. Comme sur le Choir Harvester, c'est sans conséquence tant que le combat s'en sert comme
   point d'apparition et calcule la direction à part ; une charge visuelle posée à la bouche d'une
   plaque basculée, elle, s'en apercevrait.
4. **L'état endommagé n'est pas modélisé** (hors périmètre) : il viendra par shader, avec
   `leviathan_damage_mask`.
5. **Aucune texture n'est appliquée** (hors périmètre) : le `.glb` porte les coordonnées, rien d'autre.
   Le jeu de textures reste dans `assets/source/textures/leviathan/`.
6. **Le vortex n'est pas de la géométrie.** Le puits est un entonnoir blindé ; la profondeur violette
   à spirales magenta du panneau VORTEX OPEN est un shader, comme le dit la conception (§9.5).
7. **Le rendu de recette est un rendu Cycles neutre.** Le noyau y paraît rose pâle plutôt que magenta
   profond : l'émissif à 2,5 sature en trois points sous cet éclairage. À juger en jeu, où le
   post-process rétro et le bloom le reprennent — pas sur cette planche.
8. **Six anneaux sur la planche, cinq livrés.** Le contrat de noms dit `Ring_01..05` ; j'ai suivi le
   contrat, comme la conception le demandait (« à trancher à la reforge »). Un sixième s'ajouterait
   sans rien casser : le rayon est dérivé de la paroi, il suffit d'une ligne dans `RINGS`.

---

## 6. Suggestions (rien n'a été fait hors périmètre)

1. **`build_choir_harvester.py` n'a ni `box_project_uv()` ni triangulation des n-gons.** Le mini-boss
   est donc dans l'état exact que ce brief vient de corriger sur le boss final : ni UV, ni tangentes,
   donc aucune texture applicable. La correction est de deux lignes dans son `_finish()`, plus la
   passe `_triangulate_ngons()` copiée telle quelle. Un brief de dix minutes.
2. **Promouvoir le harnais de dégagement dans `aegis_kit`.** `Solid`, `Rig`, `_soup`, `_clip_sphere`
   et `_godot_euler` existent maintenant en **deux copies** (Harvester et Leviathan), à quelques
   détails près. La version de ce script est la plus générale (exclusions multiples par pièce,
   rotations par basis explicite en plus des eulers). Le troisième boss articulé fera la troisième
   copie.
3. **`ak.attach_point(name, location, parent=)`**, symétrique de `moving_part()` : cinq lignes dans
   `export_hull()`, et les bouches suivent enfin leur pièce (limite n° 3, déjà signalée par le rapport
   de BRIEF-0039 — c'est la deuxième fois qu'elle coûte une ligne de « limites connues »).
4. **Un rendu posé, versionné.** `tools/render-hull.py` ne sait montrer qu'une pose de repos ; or
   « une pièce mobile non posée n'est pas vérifiée » est exactement le corollaire d'ADR-0006. Le
   script de pose que j'ai utilisé est resté hors dépôt (le brief ne prescrit pas `tools/`) ; il tient
   en 60 lignes et se réduit à `render-hull.py` plus trois options `--pose`, `--tangent`, `--hide`.
   ⚠️ Y inscrire le piège du `rotation_mode = 'QUATERNION'` (§3), qui fait rendre une pose de repos en
   croyant rendre une pose extrême.
5. **`ring_gap_deg = 70` est cohérent avec le modèle** : les cinq ouvertures sont décalées de 72° d'un
   anneau au suivant. Si `LeviathanTuning` change cet angle, le modèle ne suit pas tout seul — c'est
   une valeur dupliquée entre la coque et le réglage, et elle mérite un commentaire des deux côtés.

---

## 7. Conformité au brief

- [x] Toutes les pièces du contrat de noms existent, avec les bons parents (relu dans le JSON du `.glb`).
- [x] `ak.box_project_uv()` appelé sur **chaque** maillage ; le `.glb` porte `TEXCOORD_0` **et** `TANGENT`.
- [x] `./scripts/build-hull.sh --check pale_leviathan` : **0 octet divergent**.
- [x] Auto-validation d'`ak.export_hull()` : bbox, hauteur, budget, matériaux, pivot, orientation,
      14 points d'attache — tout passe, et le contrat du script porte bien `tri_budget = 40_000`.
- [x] Tableau « pièce / débattement appliqué / marge minimale mesurée » : §3, dix lignes, toutes
      strictement positives, **remesurées à chaque build** et bloquantes.
- [x] Vérifié par rendu : gueule à 90° en vue de dessus, plaques à −80°.
- [x] Planche 4 vues produite **et regardée** — trois itérations de plan en sont sorties (noyau trop
      clair, magenta en confettis, dard en pointe unique qui lisait comme une soucoupe).
- [x] Chiffres réels partout : §2.
