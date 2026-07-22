# BRIEF-0039 — Rapport : le Choir Harvester a des pièces réellement animables

- **Agent** : asset-forge (Claude)
- **Date** : 2026-07-22
- **Brief** : `docs/forge/briefs/BRIEF-0039-choir-harvester-pieces-animables.md`
- **Lu au préalable** : `docs/forge/CHARTE_CREATIVE.md`, la planche
  `assets/reference/concepts/choir_harvester_concept_sheet.png`,
  `tools/blender/lib/aegis_kit.py` (`moving_part`, `HullContract`, `export_hull`),
  `tools/blender/test_moving_parts.py`,
  `.claude/resources/pratique-detail-en-fraction-de-corde.md`,
  et — décisif — le code de combat écrit en parallèle
  (`scripts/bosses/harvester_combat.gd`, `harvester_limb.gd`,
  `resources/bosses/choir_harvester_tuning.tres`).

---

## 1. Livrables

| Fichier | État |
|---|---|
| `tools/blender/build_choir_harvester.py` | reforgé (la source de l'asset, ADR-0008) |
| `assets/imported/models/bosses/choir_harvester.glb` | régénéré, `sha256 a3d88d00d207392653c9984e38bb051575e992bf8d9dc51c706c10010e6394c8`, 803 816 o |
| `docs/forge/output/BRIEF-0039-report.md` | ce fichier |
| `assets/licenses/ASSET_PROVENANCE.csv` | ligne `choir_harvester_hull` mise à jour |

Régénéré **uniquement** par `./scripts/build-hull.sh choir_harvester`.
`./scripts/build-hull.sh --check choir_harvester` : **déterminisme OK, 0 octet divergent**
(même sha256 sur deux exécutions). `./scripts/check.sh` : **ALL GREEN** (161 tests).

### Mesures du `.glb` livré

| Grandeur | Contrat | Mesuré |
|---|---|---|
| largeur X | 4,55 m ±3 % | **4,5505 m** (dérive 0,01 %) |
| longueur Z | 7,00 m ±3 % | **7,0156 m** (dérive 0,22 %) |
| hauteur Y | ≤ 1,60 m | **1,2659 m** |
| centre (X, Z) | ±0,02 m | **(+0,0003 ; −0,0078)** |
| triangles | ≤ 25 000 | **18 666** (27 256 sommets) |
| matériaux | les 7 | les 7, tous assignés |

Le contrat de dimensions n'a **pas** dérivé : rien à signaler de ce côté.

---

## 2. Le défaut corrigé, et ce qu'il a entraîné

Les pièces étaient exportées à l'identité : leur origine était celle du modèle, donc une rotation
les faisait tourner **autour du centre du boss**. Tout ce qui bouge passe désormais par
`ak.moving_part(name, bm, pivot, parent=…)`. Le graphe du `.glb` livré, relu sur le fichier :

```
Hull                       (statique)
Petal_01..05               t = (∓0,951 / 0 / ±0,588 ; +0,550 ; …)   racines
Core                       t = (0 ; +0,050 ; 0)                     racine, statique
Arm_Scythe   t=(-1,990 ; +0,320 ; +0,550)  └─ Scythe_Mid  t=(-0,050 ; +0,160 ; -0,790)
                                                          └─ Scythe_Blade t=(-0,010 ; +0,030 ; -1,200)
Arm_Claw     t=(+1,660 ; +0,160 ; -1,450)  ├─ Claw_Head_1 t=(-0,362 ; -0,100 ; -0,869)
                                            ├─ Claw_Head_2 t=(-0,076 ; -0,120 ; -1,190)
                                            └─ Claw_Head_3 t=(+0,228 ; -0,140 ; -0,852)
Arm_Cannon   t=(-0,220 ; +0,020 ; -2,300)  └─ Cannon_Barrel t=(0 ; 0 ; 0)
Core_Center, Engine_C, Muzzle_Cannon, Muzzle_Claw_1..3   (Node3D, sans maille)
```

Aucun `Hinge_*` ne subsiste ; `Muzzle_L` / `Muzzle_R` ont disparu du modèle **et** du
`HullContract` (`required_attach_points` vaut désormais `Core_Center, Muzzle_Claw_1..3,
Muzzle_Cannon, Engine_C`).

**`Cannon_Barrel` a volontairement une translation nulle** : son pivot partage le Y d'auteur de
celui de `Arm_Cannon`. C'est ce qui rend correct le `limb.joints[0].position.z = recoil` du
combat, qui **écrase** la composante Z au lieu de l'ajouter — avec un décalage non nul au repos,
le fût aurait sauté à la première image.

### Le plan a été dicté par la mécanique, pas seulement par la planche

Le code de combat écrit en parallèle impose des axes précis (repère Godot) :
`root.rotation.x` pour le repli **−70°** d'un appendice détruit, `rotation.y` pour la visée,
`position.z` pour le recul. Traduit en repère d'auteur (`x_Godot = −x_auteur`,
`y_Godot = z_auteur`, `z_Godot = y_auteur`), deux conséquences ont commandé tout le plan :

1. **le repli tourne autour d'un axe parallèle à X : `x` est conservé.** Un appendice qui
   surplombe la carapace la **traverse** dès qu'il pique de 70°, quoi qu'on fasse. Les trois
   appendices sont donc montés pour piquer dans le vide : la faux sur le flanc bâbord (toute sa
   géométrie au-delà du cerclage), la griffe sur le flanc tribord tendue vers l'avant, le canon
   en avant du disque ;
2. **le recul vaut +0,25 m en Y d'auteur, soit vers l'arrière : le canon tire donc vers l'AVANT**
   (−Y, la face menaçante). Une bouche tournée vers l'arrière aurait fait naître le faisceau
   derrière le boss (`_muzzle_offset` ne lit que la position du point d'attache).

C'est pour cela que le module arrière n'est pas devenu un canon **à sa place** : à l'arrière, un
canon tirant vers l'avant survole la carapace et la traverse au repli. Le canon a donc pris la
place du bec avant, décalé de 22 cm à bâbord (asymétrie de charte §4, et la place dont la griffe
a besoin en fin de balayage — voir §3). L'arrière garde la lecture de la planche (bloc segmenté,
nervures, dérives, trois tuyères magenta) mais **fait partie de la coque** : ni pivot, ni nom au
contrat, ni vie propre. Ce n'est pas un quatrième appendice.

---

## 3. Tableau de dégagement à fond de course — le livrable central

Mesure faite **à chaque build**, sur le maillage réellement livré (chanfrein compris), en
rejouant dans le repère Godot exactement les rotations qu'écrit `harvester_combat.gd`, aux
amplitudes du `.tres`. Méthode : BVH sur soupe de triangles, test d'intersection exact
(`BVHTree.overlap`) puis distance minimale interrogée **dans les deux sens** (sommet mobile → face
fixe *et* sommet fixe → face mobile ; un seul sens laisserait passer une lame mince qui traverse
une grande face). Poses balayées : 5 valeurs de déploiement × 5 à 7 valeurs de visée, plus
l'ouverture de l'iris en 15 pas. **Une marge nulle fait échouer le build** (`ContractError`), le
`.glb` n'est alors pas publié.

| Pièce | Débattement appliqué | Marge minimale mesurée | Pose la plus serrée |
|---|---|---|---|
| `Arm_Scythe` + `Scythe_Mid` + `Scythe_Blade` / coque | estoc ±55° cumulés (0,45 / 0,35 / 0,20) **et** repli −70° | **22,5 mm** | déploi 0,50, estoc −16°, sur `Arm_Scythe` |
| `Arm_Claw` + `Claw_Head_1..3` / coque | balayage ±32°, têtes ±18°, repli −70° | **37,1 mm** | déploi 1,00, balayage +32°, sur `Arm_Claw` |
| `Claw_Head_1..3` entre elles | ±18° chacune | **37,0 mm** | déploi 1,00, balayage +16°, têtes 1↔2 |
| `Arm_Claw` + têtes / **canon** | balayage ±32°, têtes ±18° | **228,2 mm** | déploi 1,00, balayage +32°, tête 2 |
| `Arm_Cannon` + `Cannon_Barrel` / coque | repli −70°, recul 0,25 m | **183,3 mm** | déploi 0,00 (canon replié) |
| `Cannon_Barrel` dans `Arm_Cannon` | course −0,25 m le long du fût | **26,1 mm** | recul plein |
| `Petal_01..05` / coque | ouverture 0 → **78°** | **56,9 mm** | `Petal_01`, iris fermé |
| `Petal_01..05` entre eux | ouverture 0 → **78°** | **109,0 mm** | `Petal_04/05`, iris fermé |

**Toutes les marges sont strictement positives.** Aucune pièce ne mord.

Deux lignes ont été ajoutées au-delà des six demandées : les têtes entre elles, et la griffe
contre le canon. Ce sont elles qui ont sauté les premières — le brief ne les demandait pas
justement parce que personne ne les avait vues venir.

### Convention de mesure : la sphère de charnière

Une articulation réelle s'interpénètre **par construction** (une boule dans sa calotte, une
racine de pétale dans son berceau). La mesure écarte donc, **des deux côtés**, la matière située à
moins d'un rayon donné du pivot. C'est licite et non arbitraire : une rotation autour d'un axe
passant par le pivot **conserve la distance au pivot**, donc rien de ce qui est exclu ne peut
rencontrer ce qui ne l'est pas. Les triangles à cheval sur la sphère sont **découpés**
récursivement (arête la plus longue, profondeur 4), pas conservés en bloc : l'exclusion est
géométrique et non « par triangle ». La première version, qui gardait un triangle dès qu'un
sommet sortait, criait sur l'interpénétration normale des rotules — un faux positif finit
toujours par être désactivé.

| Pièce | Rayon exclu |
|---|---|
| `Arm_Scythe`, `Arm_Claw` | 0,20 m |
| `Arm_Cannon` | 0,44 m (la calotte enveloppe la boule) |
| `Petal_01..05` | 0,09 m |

### Ce que la mesure a corrigé, dans l'ordre

1. **Un bug dans la mesure elle-même** : le recul était appliqué sur la 2ᵉ composante (Godot Y) au
   lieu de la 3ᵉ (Godot Z). Le fût *montait* au lieu de rentrer et heurtait l'alésage. Une
   morsure signalée qui n'existait pas — le pendant exact du faux négatif redouté.
2. **Le mât d'emplanture** : un longeron d'épaisseur constante se faisait raboter par le bras dès
   −70°. Il est désormais **horizontal, son axe passe par le pivot, et il est aminci sur ses 30
   derniers centimètres** : ce qui subsiste près de la rotule est un pion centré sur l'axe de
   rotation.
3. **La première vertèbre** partait du pivot et balayait un cylindre autour de lui. `ak.limb()`
   accepte maintenant un `root_gap` (16 cm) : le bras est dégagé de sa rotule — ce qui, en prime,
   lit comme un vrai joint (la planche montre des segments séparés, pas un tube).
4. **L'ordre des trois têtes de griffe** : `harvester_combat` tourne la tête `i` de
   `converge × (i−1)`, soit −18° pour la 1 et +18° pour la 3. Avec la tête 1 à l'**extérieur**, ces
   deux angles envoyaient la tête 3 dans le canon dès le premier balayage. La tête 1 est donc
   l'**interne** : les deux angles écartent alors les têtes de la coque et du canon, et les lignes
   de tir se croisent — c'est bien une convergence.
5. **Le bras de griffe a été raccourci et son épaule avancée** : 32° au bout d'un bras de 2,2 m
   emmenaient la tête la plus interne en travers du bec.
6. **Trois blocs du cerclage sont arasés** (secteur avant-tribord, celui que la griffe balaie) :
   ils coûtaient 30 mm de dégagement. Arasés, ils se lisent comme une échancrure de service — la
   planche montre justement un anneau irrégulier.
7. **Les ailettes de bouche du canon** sont entièrement en avant de y = −3,23 : au-delà, la course
   de recul les ramenait dans la couronne du manchon. Le collier ivoire du manchon a été tourné de
   30° pour qu'aucune de ses trois griffes ne soit dans le **plan horizontal**, celui que les
   ailettes traversent.

### Enveloppe balayée (pour information : rien ne heurte, mais il faut le savoir)

Le contrat de bounding box ne vaut qu'au repos. Mesuré sur les mêmes poses, le volume réellement
balayé en jeu, en repère d'auteur :

| Pièce | Au repos | En mouvement |
|---|---|---|
| faux | x ∈ [1,200 ; 2,275], z ∈ [+0,169 ; +0,661] | x **inchangé** (la rotation conserve x), z ∈ [**−3,167 ; +3,007**] |
| griffe | x ∈ [−2,275 ; −0,922], z ∈ [−0,175 ; +0,302] | x ∈ [**−2,819** ; −0,388], z ∈ [−1,730 ; +0,302] |

Deux conséquences pratiques :

- **l'estoc de la faux est une très grande amplitude** : ±55° cumulés au bout d'un bras de 3,8 m
  lèvent la lame à **3 m au-dessus du plan** au réarme et la descendent autant à l'abattage. C'est
  spectaculaire et voulu (« réarme au-dessus du corps »), mais à la caméra du jeu (20° de la
  verticale) cela se lit surtout comme une lame qui glisse vers le joueur, avec beaucoup de
  parallaxe. Si l'effet déçoit, c'est le coefficient 0,45/0,35/0,20 qu'il faut revoir, pas la
  coque ;
- **la griffe déborde de 0,54 m** au-delà de la silhouette de repos en fin de balayage extérieur.
  Aucun contact, et le plan de jeu fait 24 unités de large. La marge de culling de 12 m posée par
  `BossController._pad_cull_margin()` couvre largement les deux cas.

---

## 4. Rendus regardés (ADR-0006)

Trois planches 4 vues ont été produites et **regardées** avant la livraison
(`blender45 -b -P tools/render-hull.py -- <glb>`), plus un rendu **iris ouvert** obtenu en
appliquant aux pétales du `.glb` livré exactement la pose du combat
(`Basis(UP × radial, 78°)`) puis en réexportant. Elles ne sont pas versionnées (binaires non
demandés par le brief ; elles seraient passées par Git LFS pour rien).

**Ce que la première planche a montré, et qui a été corrigé :**

- les pétales lisaient comme une **fleur blanche** : le liseré ivoire était aussi large que la
  plaque. `PETAL_CROSS` resserré → plaques anthracite à liseré fin, couture magenta ;
- la poupe lisait comme un **bulbe violet lisse** : rétrécie, assombrie, plaques enfoncées,
  quatre nervures transversales, deux dérives latérales ;
- le canon ne lisait pas du tout de dessus (un fût pointé vers l'avant se voit **par le cul** à
  20° de la verticale) : ajout d'**ailettes horizontales** et d'une couronne de bouche large, plus
  trois bouches secondaires magenta ;
- le modèle était **plat** (1,12 m pour un plafond à 1,60) : couronne relevée, iris et noyau
  remontés en conséquence — 1,27 m aujourd'hui, et le trois-quarts a enfin du volume.

**Critère « iris ouvert »** : à 78°, en vue de dessus, les cinq pétales sont debout et le noyau
magenta est **entièrement découvert**, sans qu'aucun pétale ne morde son voisin ni la lèvre du
puits (marges 109,0 mm et 56,9 mm). Vérifié **par rendu**, pas par calcul. L'iris fermé laisse un
œil de 0,16 m de rayon par lequel le noyau reste visible : le point faible est annoncé avant même
de s'ouvrir.

---

## 5. Fidélité à la planche, et écarts assumés

Respecté : corps-iris discoïde à cinq pétales blindés sur un noyau magenta ; anneaux segmentés et
ergots ivoire asymétriques ; faux à vertèbres et lame en croissant à fil lumineux ; **une seule**
griffe qui se divise en trois têtes à œil magenta ; canon à fût segmenté et bouches multiples ;
palette Chœur Nul stricte (anthracite `#24252B`, violet `#452663`, ivoire `#DDDCD2`, magenta
`#D93D9C`, vert maladif en marquage unique).

Écarts, tous imposés par la mécanique du combat et signalés plutôt qu'inventés en silence :

| Écart | Raison |
|---|---|
| Le canon est **en avant**, pas à l'arrière | le recul et l'origine du faisceau imposent un tir vers l'avant ; à l'arrière il traversait la carapace au repli (§2) |
| Le canon est **décalé de 22 cm à bâbord** | place nécessaire à la griffe en fin de balayage ; asymétrie de charte |
| L'arrière est un **bloc propulsif fixe** | il porte le max Y et `Engine_C` ; il garde la lecture « col segmenté + module » de la planche sans être un quatrième appendice |
| La faux est montée sur le **flanc**, elle n'arque plus au-dessus du corps | un bras au-dessus du disque le traverse au repli −70° |
| Les têtes de griffe sont **plus petites** que sur la planche | il fallait 0,55 m entre têtes pour encaisser ±18° de convergence |
| Le bec avant de la version précédente a **disparu** | il n'existait que pour porter les extrêmes en Y, contrainte levée depuis que `export_hull(parts=…)` prend les pièces mobiles dans sa bounding box |

Aucun élément identifiable d'une licence tierce : formes, proportions et détails sont dérivés de
notre seule planche.

---

## 6. Points à traiter côté intégration (hors périmètre de ce brief)

**⚠️ 1 — les pièces enfants ne sont pas des enfants directs de la coque.** Le contrat de noms
impose le parentage (`Scythe_Mid` sous `Arm_Scythe`, etc.), et le `.glb` le respecte. Mais
`HarvesterLimb.make()` les cherche par `hull.get_node_or_null(NodePath("Scythe_Mid"))` : un
`NodePath` relatif ne regarde que les **enfants directs**. En l'état, `Scythe_Mid`,
`Scythe_Blade`, `Claw_Head_1..3` et `Cannon_Barrel` remonteront `null` et déclencheront le
`push_error` « coque sans pièce mobile ». Deux remèdes possibles, tous deux côté code :
`hull.find_child(name, true, false)`, ou des chemins complets (`"Arm_Scythe/Scythe_Mid"`).
Je ne touche pas au GDScript (écrivain unique), donc je le signale ici.

**2 — la zone de touche d'un appendice est centrée sur son pivot.** `_limb_offset()` lit
`limb.root.position`, c'est-à-dire l'épaule, avec `limb_hitbox_radius = 0,85`. Or le corps de la
lame est à **2,9 m** de son épaule (sa pointe à 3,8 m) et les têtes de griffe à **1,4 à 1,6 m** de
la leur : le joueur qui tire sur ce qu'il voit ne touchera rien. Un décalage de zone de touche par appendice (ou une zone
posée sur la dernière articulation) réglerait la question ; les positions sont lisibles sur la
coque, comme le fait déjà `_limb_offset`.

**3 — l'iris est réglé à 72° dans le `.tres`, le brief en demandait 78°.** Le modèle est mesuré
et validé **à 78°** ; 72° est donc couvert avec plus de marge encore. Rien à corriger, sauf si
l'on voulait vraiment les 78°.

**4 — le canon ne pointe pas.** `_pose_limbs()` n'écrit que le repli sur `Arm_Cannon` ; les ±30°
de pointage du brief ne sont appliqués nulle part. Le modèle les encaisserait (la rotule est une
calotte sphérique centrée sur le pivot, invariante par rotation), mais je n'ai pas mesuré ce
débattement puisque le combat ne l'utilise pas. À demander si le pointage revient.

**5 — suggestion pour le kit** (pas faite : `aegis_kit.py` n'est pas au périmètre de ce brief) —
`ak.attach_point()` ne sait pas parenter. `Muzzle_Claw_1..3` et `Muzzle_Cannon` sont donc des
nœuds racines **fixes** : ils ne suivent ni la convergence des têtes, ni le balayage, ni le recul.
Pour ce combat c'est sans conséquence (le code s'en sert comme d'un point d'apparition, la
direction est calculée à part), mais une charge visuelle posée à la bouche s'en apercevrait. Un
paramètre `parent=` sur `attach_point()`, symétrique de celui de `moving_part()`, coûterait cinq
lignes dans `export_hull()`.

---

## 7. Limites connues

- Le dégagement est mesuré **appendice contre coque** et **appendice contre canon** ; les
  combinaisons faux × griffe ne le sont pas (elles sont sur des flancs opposés, à plus de 3 m
  l'une de l'autre). Si un futur brief rapproche deux appendices, la ligne sera à ajouter.
- Les 22,5 mm de la faux et les 26,1 mm du fût sont les deux marges les plus fines. Elles sont
  positives et remesurées à chaque build, mais elles ne laissent pas la place à un chanfrein plus
  large ni à un détail posé près d'une charnière. Le corollaire de
  `pratique-detail-en-fraction-de-corde.md` s'applique en plein : tout nouveau détail sur ces
  pièces doit être posé **en fraction**, et le build le dira.
- L'état endommagé (fissures, fumée) n'est pas modélisé : hors périmètre, il viendra par shader.
- Aucune texture ni SFX : hors périmètre.
