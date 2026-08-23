# BRIEF-0042 — mesure : débattement RADIAL des plaques de la Choir Mine

- **Nature** : mesure seule. **Aucun asset n'a été reforgé.**
  `tools/blender/build_choir_mine.py` et `assets/imported/models/ships/choir_mine.glb`
  sont **inchangés** (ni ouverts en écriture, ni régénérés).
- **Exécuté par** : asset-forge — 2026-08-23
- **Lu avant** : `docs/forge/CHARTE_CREATIVE.md`, `docs/forge/output/BRIEF-0042-report.md`
  (harnais et convention), `scripts/enemies/enemy_pose.gd`, `resources/data/enemy_data.gd`,
  `scenes/gameplay/graybox.tscn` (géométrie réelle de la caméra de jeu).
- **Livrables** : ce compte-rendu + `docs/forge/output/BRIEF-0042-planche-ecart-radial.png`.

---

## 0. Réponse courte

| Question | Réponse mesurée |
|---|---|
| Marge de coulissement avant interpénétration | **il n'y en a pas.** Zéro contact jusqu'à **300 mm** (115 % du rayon), et la marge **augmente** avec l'écart : 12,6 mm → 99,9 mm |
| Ce qui bloque | **rien.** La couronne de fûts n'est jamais approchée : son sommet est **88 mm sous** le point le plus bas d'une plaque ouverte à 45° |
| En fraction du rayon | le plafond utile est celui du **code** : `EnemyPose.MAX_SPREAD = 0,5`, soit **150,5 mm** = **57,4 %** du rayon XZ (0,262 m) |
| Croissance du diamètre apparent, à ce plafond | **+8,5 %** (dessus) / **+7,7 %** (vue jeu) en diamètre maximal — **+12,2 %** / **+10,2 %** en diamètre équivalent (aire) — **46 px → 50 px** à la taille du jeu |
| Ça se lit à 46 px ? | **Oui à `open_spread = 0,50`. Non à 0,33.** Voir §5 |

**La marge n'est pas nulle : l'idée tient.** Mais elle ne tient qu'à partir de ~0,45 de
coulissement, et pas pour la raison attendue — l'obstacle n'existe pas, c'est **l'enveloppe qui
n'appartient pas aux plaques** (§4.1). Le seul chiffre qui décide, la croissance de diamètre,
frôle la barre des 10 % : il la passe sur l'aire, il la manque de 1,5 point sur le diamètre max.

---

## 1. Méthode — le même harnais, vérifié contre le rapport d'origine

Harnais BVH identique à `_travel_table()` de `build_choir_mine.py`, réécrit **en lecture seule**
dans le bac à sable (le `.glb` livré est importé, jamais réécrit) :

- soupe de triangles des 7 maillages, en repère **Godot** (`glTF Blender (bx,by,bz)` → `(bx, bz, -by)`) ;
- convention **exacte** de `EnemyPose` : origine de la pièce sur la charnière,
  `axe = normalize(-pos.z, 0, pos.x)`, `Basis(axe, 45°)`, **même angle pour les six** ;
- coulissement ajouté : translation le long de `normalize(pos.x, 0, pos.z)`, **après** la rotation
  (comme `pose()` : `position = rest + radial * |rest| * spread * open`, la base étant écrite à part) ;
- distance minimale **triangle-à-triangle dans les deux sens** (sommet mobile → face fixe *et*
  sommet fixe → face mobile), plaque contre coque **et** plaque contre ses deux voisines ;
- deux variantes : avec la sphère de charnière de 12 mm exclue (`HINGE_SKIP`, comparable au rapport
  d'origine) et **sans aucune exclusion** (lecture brute, plus sévère). Les deux sont données.

**Contrôle de fidélité — le harnais reproduit le rapport d'origine au dixième de millimètre :**

| ouverture (écart 0) | 0° | 45° | 56° | 57° |
|---|---|---|---|---|
| marge, rapport BRIEF-0042 §3 | 10,1 mm | 12,9 mm | 0,7 mm | 0 (contact) |
| marge, ce harnais | **10,1 mm** | **12,9 mm** | **0,7 mm** | **0 (contact)** |

Pivots relus sur le `.glb` : `Segment_01..06` en (±0,2269 / 0 ; +0,1480 ; ±0,1310 / ±0,2620).
**Rayon XZ vérifié : 0,26200 m pour les six**, à 10⁻⁵ près (la valeur annoncée dans la demande est
donc juste, et elle est bien identique pour `Segment_02`/`_05` et pour les quatre autres).

---

## 2. Question 1 — de combien peut-elle coulisser avant de mordre ?

**Réponse : aucune limite mécanique dans le domaine atteignable.** Balayage de 0 à 300 mm
(0 à 115 % du rayon), pas de 1 mm jusqu'à 150 mm puis de 5 mm, sur les **six** plaques :
**zéro contact**, et la marge **croît de façon monotone**.

| écart | 0 | 30 | 60 | 90 | **100** | 120 | **150** | 200 | 250 | 300 mm |
|---|---|---|---|---|---|---|---|---|---|---|
| marge, lecture brute | 12,6 | 18,6 | 25,5 | 32,6 | **36,6** | 44,6 | **56,6** | 82,0 | 94,2 | 98,7 mm |
| marge, avec `HINGE_SKIP` | 12,9 | 19,0 | 25,9 | 33,3 | **37,3** | 45,3 | **57,3** | — | — | — |
| obstacle le plus proche | talus du pont | idem | idem | idem | idem | idem | idem | idem | idem | idem |

Les six plaques donnent les mêmes valeurs au dixième de millimètre, **sauf `Segment_05`** au-delà de
250 mm (100,0 mm au lieu de 94,4) : c'est la plaque qui coiffe la pointe asymétrique, et en
s'éloignant elle la découvre. Aucune conséquence — c'est un gain de marge, pas une perte.

### Pourquoi la couronne de fûts n'est pas l'obstacle

L'hypothèse de la demande est réfutée par la géométrie, et c'est net :

| | cote Y (Godot) |
|---|---|
| sommet de la couronne de fûts et caissons | **+0,060 m** |
| point le plus bas d'une plaque ouverte à 45° (sa charnière) | **+0,148 m** |
| dégagement vertical | **88 mm, constant quel que soit l'écart** |

Une plaque ouverte à 45° **survole** la couronne de 88 mm. Le coulissement est horizontal : il ne
peut donc pas la rencontrer. L'objet le plus proche est le **talus du pont** (la pente qui descend
du puits de noyau vers l'épaulement) — et il **s'écarte tout seul** : le point de contact le plus
proche glisse de r = 0,260 m / y = +0,136 vers r = 0,389 m / y = +0,097 pendant que la plaque, elle,
reste à y ≥ +0,148. La plaque monte, le pont descend : la fente s'ouvre.

**Conséquence à retenir : `open_spread` n'a pas de garde-fou géométrique.** Contrairement à
`open_angle_deg` (mur dur à 57°), rien dans le maillage n'arrête le coulissement. Le seul plafond
est `EnemyPose.MAX_SPREAD = 0,5`, et il est **arbitraire, pas mesuré**. C'est un choix de lecture,
pas une sécurité mécanique — le dire dans la donnée éviterait qu'on le croie mesuré.

---

## 3. Question 2 — la valeur, en mm et en fraction du rayon

### ⚠️ Deux « rayons » circulent, et ils diffèrent de 14,9 %

`enemy_data.gd` documente `open_spread` comme « fraction de leur **propre rayon** », mais
`enemy_pose.gd` écrit :

```gdscript
_parts[i].position = _rest[i] + _radial[i] * _rest[i].length() * _spread * open
```

`_rest[i].length()` est la distance **3D à l'origine de la coque** : `|(0,2269 ; 0,1480 ; 0,1310)|`
= **0,30091 m**. Le rayon de la plaque — sa distance à **l'axe Y**, celui qui porte le coulissement —
vaut **0,26200 m**. L'écart est de **+14,9 %** : une valeur d'`open_spread` réglée en croyant
raisonner sur 0,262 m produit un coulissement 14,9 % plus grand que prévu.

Ce n'est pas un bug (le facteur est constant, donc absorbable dans le réglage), mais c'est un piège
à reforge : **si la coque est un jour rebâtie avec une autre hauteur de charnière, le rapport entre
les deux rayons change** et tous les `open_spread` glissent en silence. Deux issues, au choix de la
session : diviser par `Vector2(_rest[i].x, _rest[i].z).length()` (et le commentaire redevient vrai),
ou corriger le commentaire. Ci-dessous, **les deux conversions**.

| `open_spread` (code, ÷ 0,30091 m) | écart réel | en % du rayon XZ (0,262 m) | marge restante |
|---|---|---|---|
| 0,10 | 30,1 mm | 11,5 % | 18,6 mm |
| 0,20 | 60,2 mm | 23,0 % | 25,6 mm |
| 0,30 | 90,3 mm | 34,5 % | 32,7 mm |
| 0,33 | 100,0 mm | 38,2 % | 36,6 mm |
| 0,40 | 120,4 mm | 46,0 % | 44,7 mm |
| **0,50** *(plafond `MAX_SPREAD`)* | **150,5 mm** | **57,4 %** | **56,8 mm** |
| 0,53 | 160,0 mm | 61,1 % | 61,7 mm |
| 0,61 | 185,0 mm | 70,6 % | 76,4 mm |

**Écart maximal sûr, en fraction du rayon de la plaque : 0,574 du rayon XZ** (= `open_spread` 0,50,
le plafond du code). Ce n'est pas la limite du maillage — il n'y en a pas — c'est la limite du code,
et elle tombe au bon endroit (§5).

---

## 4. Question 3 — croissance de l'enveloppe apparente vue de dessus

### 4.1 D'abord, pourquoi le pivot seul ne se voit pas

Mesuré sur le maillage, c'est structurel et ça n'a rien à voir avec l'angle :

| | rayon maximal |
|---|---|
| couronne de fûts et caissons (le maître-couple) | **0,578 m** |
| plaques, coque **fermée** | 0,496 m |
| plaques, ouvertes à **45°** | **0,477 m** — elles *rentrent* de 19 mm |

**L'enveloppe de la mine appartient à la couronne, pas aux plaques.** Les plaques vivent 82 mm en
retrait du bord. Tout mouvement de plaque est donc **invisible sur le diamètre** tant qu'elle n'a
pas franchi la ligne de la couronne — ce qui demande **101,4 mm** de coulissement rien que pour
*rattraper* le bord. Le pivot de 45°, lui, fait l'inverse : il **réduit** le rayon des plaques.
C'est l'explication complète de « le code fait bien pivoter les six pièces et le joueur ne voit rien ».

### 4.2 Méthode de mesure de l'enveloppe — et un piège évité

Le rendu de recette de `tools/render-hull.py` cadre serré : la caméra est à **2,36 m** d'un objet de
1,15 m. Une pièce soulevée de 30 cm y grossit de **14,5 %** par simple perspective. La caméra du jeu
(`scenes/gameplay/graybox.tscn` : position (0 ; 14 ; 5), 70° sous l'horizontale, fov 62°) est à
**14,9 unités** du plan de jeu : la même pièce n'y grossit que de **1,9 %**. Mesurer l'enveloppe sur
la planche de recette **surestimait la croissance d'un facteur 7**.

Les huit vignettes de la planche sont donc rendues avec la **géométrie perspective réelle du jeu**
(distance/taille = 12,9), cadrage **figé sur l'état fermé** — comparer des enveloppes avec un
cadrage recalculé par état ne comparerait rien du tout. L'enveloppe est ensuite relevée par
seuillage de luminance sur le rendu (fond `#070A12`), à 640 px puis à 46 px.

### 4.3 Le tableau qui décide

Croissance par rapport à l'état **fermé**. « diamètre max » = plus grande dimension de la silhouette ;
« diam. équivalent » = diamètre du disque de même aire (il rend compte du remplissage des festons
entre les modules, que le diamètre max ignore).

| `open_spread` | écart | **diamètre max** (dessus / jeu) | diam. équivalent (dessus / jeu) | aire de silhouette (dessus / jeu) | à 46 px (largeur / pixels allumés) |
|---|---|---|---|---|---|
| — (45°, écart 0) | 0 mm | **+0,0 % / +0,0 %** | −0,1 % / +1,1 % | −0,1 % / +2,1 % | **46 px (+0) / −0,2 %** |
| 0,10 | 30 mm | +0,0 % / +0,0 % | +1,5 % / +2,4 % | +3,0 % / +4,9 % | 46 px (+0) / +2,4 % |
| 0,20 | 60 mm | +0,0 % / +0,3 % | +3,6 % / +4,2 % | +7,3 % / +8,5 % | 46 px (+0) / +5,0 % |
| 0,30 | 90 mm | +0,0 % / +2,7 % | +5,5 % / +6,2 % | +11,4 % / +12,9 % | 46 px (+0) / +6,4 % |
| 0,33 | 100 mm | **+0,0 % / +3,5 %** | +6,3 % / +6,9 % | +13,0 % / +14,3 % | 47 px (+1) / +8,4 % |
| 0,40 | 120 mm | +3,2 % / +5,1 % | +8,7 % / +8,3 % | +18,2 % / +17,2 % | 50 px (+4) / +14,3 % |
| **0,50** | **150 mm** | **+8,5 % / +7,7 %** | **+12,2 % / +10,2 %** | **+25,9 % / +21,5 %** | **50 px (+4) / +21,6 %** |
| 0,53 *(hors plafond)* | 160 mm | +10,1 % / +8,2 % | +13,0 % / +10,8 % | +27,6 % / +22,9 % | 52 px (+6) / +24,8 % |
| 0,61 *(hors plafond)* | 185 mm | +14,8 % / +10,4 % | +14,8 % / +12,5 % | +31,7 % / +26,6 % | 54 px (+8) / +29,8 % |

**Le chiffre demandé, au plafond du code (`open_spread = 0,50`) : +8,5 % de diamètre vu de dessus,
+7,7 % en vue de jeu.** En diamètre équivalent : **+12,2 % / +10,2 %**. En masse allumée : **+21 %**.

La barre des 10 % est donc **franchie sur l'aire et sur le diamètre équivalent, manquée de 1,5 point
sur le diamètre maximal**. Il faut `open_spread ≈ 0,53` (160 mm, au-dessus du plafond actuel) pour
atteindre +10 % de diamètre maximal vu de dessus.

---

## 5. Question 4 — la planche, et le verdict à 46 pixels

`docs/forge/output/BRIEF-0042-planche-ecart-radial.png` — 4 états × 3 rangées, **cadrage identique
partout**, cercle cyan = enveloppe de l'état fermé :

- rangée 1, **vue de dessus** orthogonale au plan de jeu ;
- rangée 2, **vue de jeu** (20° de la verticale, distance et fov de `graybox.tscn`) ;
- rangée 3, **à 46 px** — la taille réelle en jeu — agrandie ×4 au plus proche, avec la vignette 1:1
  en coin pour juger sans interpolation.

**Ce que je vois, honnêtement, sur la rangée 46 px :**

1. **Fermée → ouverte 45° (écart 0)** : **le contour est le même**, au pixel près (46 px dans les
   deux cas, −0,2 % de pixels allumés). Ce qui change est interne : les tranches claires des plaques
   apparaissent, le disque paraît légèrement plus contrasté. **La plainte est confirmée, et chiffrée :
   0 pixel de différence d'enveloppe.**
2. **`open_spread = 0,33` (100 mm)** : les six plaques se détachent en lobes distincts séparés par
   des coutures sombres ; l'objet paraît un peu plus dense et plus rond. Mais **+1 px de largeur**.
   Côte à côte on voit la différence ; isolément, on ne dirait pas « elle grossit ». **Insuffisant.**
3. **`open_spread = 0,50` (150 mm)** : **ça se lit.** 46 → **50 px**, +21,6 % de pixels allumés, et
   surtout la silhouette **change de nature** : une rondelle pleine devient une couronne de six
   lobes autour d'un cœur dégagé, avec du noir franc entre les pièces. Sur la vue de dessus, les
   plaques **débordent visiblement** du cercle cyan de référence. C'est le premier état dont je dirais,
   sans connaître la réponse, que l'objet a grossi.
4. Au-delà (0,53 / 0,61, rendus mais hors planche), le gain continue mais les fentes atteignent
   62 à 76 mm — **2,5 à 3 px de noir** à la taille du jeu — et la mine commence à lire comme un objet
   **qui se disloque** plutôt qu'un objet qui s'ouvre. Je ne les recommande pas.

**Réglage recommandé : `open_spread = 0,50`** — c'est-à-dire exactement le plafond `MAX_SPREAD` déjà
présent dans le code. Il n'y a aucune raison mécanique de descendre en dessous, et la lecture à 46 px
ne devient franche qu'à partir de ~0,45.

---

## 6. Limites connues

1. **Aucun bloom, aucun post-process.** Cycles rend sans bloom ; le jeu, si. Le bloom **élargit** les
   sources claires (il devrait aider la lecture de croissance) mais **comble aussi les fentes
   sombres** entre plaques — c'est-à-dire précisément ce qui fait lire l'ouverture à `open_spread`
   0,50. Les deux effets jouent en sens contraire et je ne peux pas les départager depuis la forge :
   **à vérifier sur Windows** (`pratique-revue-asset.md`). C'est la seule réserve sérieuse de ce
   compte-rendu.
2. **L'enveloppe est relevée par seuil de luminance sur le rendu.** Le ventre anthracite d'une plaque
   sur fond `#070A12` est presque au niveau du fond : le seuil (+0,008 de luminance) tranche là où
   l'œil hésite. Les mesures d'aire ont ±1 % d'incertitude de ce fait ; les diamètres, moins (ils
   sont portés par des arêtes claires).
3. **Rendu en studio, pas en jeu.** Éclairage à trois points de `render-hull.py`, pas les lumières de
   `graybox.tscn`. La *géométrie* de caméra est celle du jeu ; l'*éclairage* ne l'est pas.
4. **Un seul angle d'ouverture testé (45°).** À 56° les plaques rentrent encore un peu plus
   (r ≈ 0,46 m), donc le coulissement nécessaire serait légèrement supérieur. Non mesuré : le brief
   fixe 45°.
5. **La marge est mesurée sur la pose finale, pas sur la trajectoire.** Comme la marge croît de façon
   monotone avec l'écart *et* avec l'angle (§2 et rapport d'origine §3), toute interpolation entre
   fermé et ouvert reste dans le domaine sûr — y compris un *overshoot* d'easing, tant qu'il ne
   dépasse pas 52° d'angle. C'est la rotation qui reste le facteur limitant, pas le coulissement.

---

## 7. Suggestions (à la session, pas des décisions de la forge)

1. **Prendre `open_spread = 0,50`**, et écrire dans `choir_mine.tres` d'où vient le chiffre. Le
   plafond `MAX_SPREAD` devient alors la valeur nominale : ajouter un mot dans `enemy_pose.gd`
   disant qu'ici le plafond **n'est pas une sécurité mécanique** (il n'y en a pas) mais une limite de
   lecture, sans quoi quelqu'un le relèvera un jour en croyant gagner de la marge mesurée.
2. **Trancher l'ambiguïté du rayon (§3)** : `|_rest|` (0,30091 m) ou rayon XZ (0,262 m). Un
   commentaire faux sur une donnée réglée à la main est exactement le genre d'erreur qui survit à
   trois reforges.
3. **Le vrai levier est ailleurs, si +10 % de diamètre est un impératif** : l'enveloppe appartient à
   la couronne. Faire coulisser **aussi les 11 modules de la couronne** (ils sont aujourd'hui soudés
   au corps, donc ce serait une reforge de coque, pas un réglage) ou, plus économique, rentrer la
   couronne à l'intérieur de la ligne des plaques pour que ce soient **les plaques qui portent le
   maître-couple**. C'est un brief de coque, pas un réglage de Resource — je ne l'ai pas fait.
4. **Vérifier `hitbox_radius`** : à `open_spread` 0,50, le rayon visuel passe de 0,575 à 0,627 m
   (+9 %) pendant le télégraphe. Le hitbox, lui, ne bouge pas. Les 5 cm de pointe de plaque
   deviennent donc traversables — ce qui va dans le sens de la spec (§5.3, hitbox généreux **côté
   joueur**), mais qui se voit si un projectile passe visiblement à travers une plaque.
5. **Capitaliser le piège de perspective (§4.2)** dans `.claude/resources/` : *mesurer une enveloppe
   sur un rendu cadré serré surestime toute croissance portée par la hauteur*. Ici, facteur 7. Ça
   vaut pour la coquille du Leviathan et pour toute future pièce mobile.

---

## 8. Périmètre respecté

Écrits : ce fichier, `docs/forge/output/BRIEF-0042-planche-ecart-radial.png`, et **une ligne**
ajoutée en `>>` à `assets/licenses/ASSET_PROVENANCE.csv`. Rien d'autre.
`tools/blender/build_choir_mine.py`, `assets/imported/models/ships/choir_mine.glb`, `scenes/`,
`scripts/`, `resources/`, les tests et les briefs sont **inchangés** — les scripts de mesure et de
rendu vivent dans le bac à sable de session et ne sont pas versionnés (ils réutilisent
`tools/render-hull.py` en lecture, sans le modifier).
