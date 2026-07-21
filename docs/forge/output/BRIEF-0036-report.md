# BRIEF-0036 — Rapport : l'aile sort d'une emplanture fixe

- **Agent** : asset-forge (Claude)
- **Date** : 2026-07-21
- **Brief** : `docs/forge/briefs/BRIEF-0036-specter-9-emplanture-fixe.md`
- **Lu au préalable** : `docs/forge/CHARTE_CREATIVE.md`,
  `docs/decisions/ADR-0014-silhouette-du-specter-9.md`,
  `.claude/resources/pratique-detail-en-fraction-de-corde.md`

---

## 1. Réponse aux trois demandes explicites

| Demande | Réponse |
|---|---|
| **Rendu aux deux extrêmes** | `BRIEF-0036-aplat-noir-deux-fleches.png`, `BRIEF-0036-jonction-aile-coque.png` et `BRIEF-0036-planche-deux-fleches.png` montrent chacun la pose **déployée** et la pose à **26°**. |
| **Jeu résiduel en flèche maximale** | **Il n'y a pas de jeu en plan** : le panneau et l'emplanture se **recouvrent** de **26,3 mm** à 26° (14,0 mm au déployé). Le seul jeu est **vertical**, sous la lèvre : **4,4 mm**. |
| **L'emplanture réduit-elle la plage de flèche ?** | **Non.** La flèche admissible reste **32,25°** pour 26° appliqués par `ShipFlight` — inchangée par rapport à BRIEF-0035. La butée est toujours la peau de nacelle à y = +0,478 ; l'emplanture est **au-dessus** du plan d'aile, elle n'entre donc pas dans le calcul. **Aucune adaptation de code n'est nécessaire.** |

---

## 2. Le critère n°1 — l'aplat noir, aux deux flèches

`docs/forge/output/BRIEF-0036-aplat-noir-deux-fleches.png` — trois panneaux, rendu
orthographique Cycles, émission noir pur, fond blanc, transformation d'affichage `Standard`.

| Panneau | Contenu |
|---|---|
| gauche | **AVANT** — le `.glb` de BRIEF-0035, restauré depuis l'objet Git LFS `f1f21f07…` |
| centre | **APRÈS** — ailes **déployées** (pose de repos, celle que le `.glb` contient) |
| droite | **APRÈS** — mêmes ailes à **26° de flèche** |

**Ce que l'image prouve, dans l'ordre du brief :**

1. **Plus de trou à la racine, à aucune des deux flèches.** Sur le panneau de gauche, un coin de
   fond blanc s'enfonce entre le fuseau et la lame et le bras de pivot y traverse le vide. Au
   centre et à droite, la lame prolonge une masse continue : le blanc ne pénètre plus nulle part
   entre la nacelle et l'aile.
2. **Les échancrures fuselage/nacelle de BRIEF-0035 sont intactes.** Les deux fentes verticales
   qui séparent la poutre centrale des deux fuseaux — l'une ouverte par l'avant, l'autre par
   l'arrière — sont présentes sur les trois panneaux, identiques. Le contour reste **non convexe**.
   Mesures remesurées à chaque build, inchangées au millimètre près :

   | Station | fente 1 (fuselage ↔ nacelle) | BRIEF-0035 | BRIEF-0036 |
   |---|---|---|---|
   | y = −0,360 | nez de nacelle | 106 mm | **106 mm** |
   | y = −0,100 | avant du caisson | 65 mm | **65 mm** |
   | y = +0,560 | arrière du caisson | 53 mm | **53 mm** |
   | y = +0,960 | poupe | 86 mm | **86 mm** |

   L'emplanture ne pouvait pas les toucher : son bord interne est dérivé du cercle de nacelle et
   reste toujours **à l'intérieur** du fuseau (x ≈ 0,235 à 0,249), alors que la fente 1 vit entre
   x = 0,130 et 0,190.

3. **En flèche maximale, l'appareil redevient une flèche compacte.** La largeur passe de 1,752 m à
   1,431 m et le contour se referme en pointe.

---

## 3. Le principe mécanique, transposé

### 3.1 Ce qui a été supprimé

Le « bras de pivot au-dessus d'un trou » était en réalité **deux pièces** :

- la **chape de charnière**, un tenon qui sortait de la peau du fuseau (x = 0,368 → 0,377) pour
  aller chercher l'aile ;
- la **ferrure de charnière**, sur l'aile, qui débordait de 26 mm en deçà de la corde de racine
  pour venir s'y emboîter.

**Les deux sont supprimées.** Il ne reste, posé sur le dos de l'emplanture au droit du pivot,
qu'un carter (`AA_Greeble` + platine `AA_Trim`) qui dit *où* est l'articulation sans la montrer.

Remarque utile pour la suite : une **boîte alignée sur les axes ne peut pas** tenir dans un
recouvrement défini en polaire — ses quatre coins ont quatre rayons et quatre angles différents,
et le coin avant-externe sort toujours. C'est mesuré, pas supposé : c'est pour cela que la ferrure
a été retirée plutôt que rétrécie.

### 3.2 Ce qui a été ajouté — `_glove()`, dans le maillage principal

Un karman en flèche, **solidaire de la coque**, un par côté :

| Grandeur | Valeur |
|---|---|
| Naissance (pointe avant, noyée dans le fuseau) | y = −0,260 |
| Émergence hors de la peau de nacelle | y ≈ −0,12 |
| Flèche du bord d'attaque | **56,8°** (contre 29,5° pour le bord d'attaque de la lame déployée) |
| Point le plus large | x = **0,648** à y = +0,437 (74 % de la demi-envergure) |
| Rentrée dans le fuseau | y = +0,606, en avant du pied de dérive (y = 0,600 → 1,012) |
| Longueur totale | 0,866 m, soit **35 % de la longueur du vaisseau** |
| Sous-face | plafonnée à z = 0,048, **calée 6 mm sous la couronne de nacelle** vers l'avant |

Le bord interne n'est pas une constante : il est **dérivé du cercle de nacelle** à la cote du
plancher, station par station. Une abscisse écrite en dur serait ressortie du fuseau vers l'avant,
là où celui-ci maigrit — et aurait ouvert une couture longitudinale exactement là où le brief
demande qu'il n'y en ait aucune.

### 3.3 La frontière externe : pourquoi la couverture se **démontre**

C'est le cœur de la solution, et c'est ce qui la distingue d'un réglage à l'œil.

La frontière externe de l'emplanture est définie **en polaire autour du pivot d'aile**, comme le
`min` de deux courbes :

```
rho(psi) = min(  (p0 + 14 mm) / cos(psi - alpha),      corde de racine décalée PERPENDICULAIREMENT
                 |coin arrière| + 18 mm            )   arc de LOGEMENT centré sur le pivot
```

Replier l'aile de θ **ajoute θ à l'angle polaire** de chaque point de la racine et **conserve son
rayon**. Il suffit donc que `rho(psi) ≥ rayon_de_racine(min(psi, 60°))` pour que la racine soit
couverte à **toute** flèche — ce que les deux courbes vérifient par construction : la première
parce qu'elle est en dehors de la corde, la seconde parce qu'elle est en dehors du cercle décrit
par le coin arrière (qui balaie de 60° à 86°, l'arc va jusqu'à 91°).

C'est une propriété de la géométrie, pas le résultat d'un essai. Elle est quand même **remesurée
sur le maillage livré** à chaque build, aux deux extrêmes (§4) : la démonstration porte sur le
plan, le maillage a une épaisseur et des chanfreins.

**Une correction en cours de route, trouvée par la mesure.** La première version décalait la corde
de racine **radialement** de 18 mm. Recouvrement annoncé : 18 mm. Recouvrement réel mesuré à
l'horizontale vers l'arrière de la corde : **0,9 mm** — parce qu'à cet endroit le rayon est presque
parallèle à la corde elle-même. Sous le chanfrein de 3,5 mm, donc nul. L'offset **perpendiculaire**
vaut la même chose partout ; c'est celui qui est livré.

### 3.4 Pourquoi la lame passe **sous** l'emplanture

Ce n'est pas un choix esthétique, c'est le seul agencement possible : la corde de racine **balaie un
secteur entier** entre 0° et 26°. Une pièce fixe coplanaire qui couvrirait la position déployée
serait traversée dès le premier degré de flèche ; une pièce qui ne couvrirait que la position
repliée laisserait un trou au déployé. Les appareils réels règlent cela par un carénage supérieur
sous lequel le panneau coulisse ; c'est ce qui est fait ici.

Conséquence directe : **le chiffre qui dit si la mécanique tient n'est pas un jeu en plan** (il est
nul par construction, les deux corps se recouvrent) **mais un jeu vertical**.

---

## 4. Mesures — toutes remesurées à chaque build, toutes bloquantes

Sortie de `./scripts/build-hull.sh --check specter_9` :

```
volets     : plafond de debattement mesure 21.1 deg
ailes      : fleche admissible mesuree 32.25 deg (cible 26)
             premiere butee : peau de nacelle a y = +0.478 (x = 0.3790, peau 0.3672)
emplanture : jeu vertical minimal 4.4 mm
             fleche 0 deg, (x = 0.5128, y = +0.2025, z = +0.0420) sous plancher 0.0463
racine a  0.0 deg de fleche (y +0.034 -> +0.428) : pire ecart  -14.0 mm  [RECOUVREMENT]
racine a 26.0 deg de fleche (y +0.046 -> +0.489) : pire ecart  -26.3 mm  [RECOUVREMENT]
```

### 4.1 Recouvrement de racine — le chiffre demandé

`_print_root_coverage()` balaie 121 stations sur la **fenêtre de racine** (de l'emplanture du bord
d'attaque au coin arrière, aux positions correspondant à la flèche testée) et compare, à chaque
station, le bord externe de l'emplanture au point le plus interne de la lame :

| Flèche | Fenêtre de racine | Pire écart | Lecture |
|---|---|---|---|
| **0°** (déployé) | y = +0,034 → +0,428 | **−14,0 mm** | recouvrement — aucune fente |
| **26°** (maxi) | y = +0,046 → +0,489 | **−26,3 mm** | recouvrement — aucune fente |

Un écart **négatif** est un recouvrement. Le pire cas est donc encore 14 mm de matière fixe
par-dessus la racine, à la flèche la moins favorable.

⚠️ Cette mesure porte sur la **racine**, c'est-à-dire la coupe d'emplanture de la lame. En arrière
du coin arrière de racine, ce qui borde l'aile est son **bord de fuite** : l'espace qui s'y ouvre
est le derrière de l'aile, il a toujours existé et le brief ne demande pas de le boucher. La
première version de la mesure confondait les deux et criait au trou de 338 mm là où il n'y a que du
ciel — corrigé.

### 4.2 Jeu résiduel vertical

`_glove_clearance()` prend **tous les sommets** de l'aile et du volet du maillage livré, applique
au volet son braquage (−21,1° à +21,1°, cinq positions) **puis** à l'ensemble la flèche (0 à 26°
par pas de 1°), et pour chaque sommet qui tombe sous l'emplanture en vue de dessus mesure
`plancher − z`.

- **Jeu minimal : 4,4 mm**, au point le plus épais du profil de racine (x = 0,513, y = +0,203,
  z = +0,042), sous un plancher à 0,046.
- Le build **échoue** en deçà de 3 mm.

4,4 mm sur une envergure de 1,752 m représente **0,25 %** de la largeur : à 96 px, moins d'un
quart de pixel. Invisible en jeu, et c'est exactement la fente de joint d'un carénage réel.

### 4.3 Ce défaut n'aurait pas été trouvé autrement — et il en a révélé un autre

La première exécution de `_glove_clearance()` a **échoué** : −2,0 mm à 4° de flèche. La lame
traversait l'emplanture. Enquête : `bridge_rings` oriente les faces de l'aile **vers l'intérieur**
de la lame (l'ordre du quad est corde × envergure, leur produit vectoriel pointe vers le bas sur
l'extrados). Or `inset_panel` enfonce **le long de la normale**. Avec `depth = −0,004` puis
`−0,005`, les rainures et les aplats bleus de l'aile sortaient donc **en relief de 9 mm** au lieu
d'être creusés — contre l'intention écrite dans le script, et 4 mm au-dessus du point le plus haut
du profil.

`ak.cleanup()` recalcule bien les normales, mais **après** : trop tard pour les insets. Le script
les recalcule désormais **avant le plaquage**, sur l'aile comme sur l'emplanture. Sur l'emplanture
le défaut aurait été pire encore : le côté tribord est bâti en miroir, donc la rainure aurait été
creusée à bâbord et en relief à tribord — une dissymétrie qu'aucune mesure du contrat ne voit.

C'est signalé ici parce que **cela modifie l'aspect de l'aile** au-delà du strict périmètre du
brief : ses panneaux bleus et ses deux rainures longitudinales sont maintenant enfoncés. C'est ce
que le script disait faire depuis BRIEF-0035 ; ce n'est pas ce qu'il faisait.

### 4.4 Contrat du `.glb` livré

| Grandeur | Valeur | Contrat |
|---|---|---|
| Largeur X | **1,7520 m** | 1,75 ± 3 % ✔ (écart 0,11 %) |
| Longueur Z | **2,4600 m** | 2,46 ± 3 % ✔ |
| Hauteur Y | **0,6465 m** | 0,62 – 0,72 ✔ (26,3 % de la longueur) |
| Triangles | **35 008** | ≤ 60 000 ✔ (58 % du budget ; 31 840 avant, +3 168 pour les deux emplantures) |
| Sommets | 43 039 | — |
| Pivot | X −0,0000 / Z +0,0000 | ± 0,02 ✔ |
| Matériaux | 7 / 7 | ✔ |
| UV + tangentes | présentes sur **les 7 maillages**, 4,0 tuiles/m | ✔ |
| Points d'attache | 10 / 10, **positions inchangées** depuis BRIEF-0035 | ✔ |
| Pièces mobiles | 6, `Flap_L/R` **enfants** de `Wing_L/R` (vérifié sur le graphe glTF) | ✔ |
| Taille | 2 306 012 o | — |
| Déterminisme | `./scripts/build-hull.sh --check specter_9` → **OK**, sha256 `fe6658b0…` | ✔ |
| Livrée tricolore / chiffres | aucun (ADR-0014) | ✔ |
| `./scripts/check.sh` | **ALL GREEN** (118 tests, 734 assertions) | ✔ |

Les 10 points d'attache ne bougent pas d'un millimètre : l'emplanture n'a touché ni au plan de
l'aile, ni aux nacelles, ni au fuselage.

---

## 5. Lisibilité en vue de jeu — le feu d'emplanture devient superflu

`docs/forge/output/BRIEF-0036-lisibilite-vue-de-jeu.png` : vue « game » (70° au-dessus du plan, la
caméra réelle de `graybox.tscn`), **même cadrage monde pour les trois colonnes** — colonne 1
BRIEF-0035, colonne 2 BRIEF-0036 déployé, colonne 3 BRIEF-0036 à 26°. Lignes : 48, 64 et 96 px de
large.

BRIEF-0035 relevait qu'à 48 px « les ailes perdent en cohésion : séparées du corps par 58 mm, soit
1,6 px sur fond sombre, elles lisent comme deux éclats détachés », et proposait trois arbitrages
dont un **feu cyan d'emplanture**.

**Verdict, en regardant l'image :**

- **À 48 px, la lame n'est plus une pièce détachée.** Colonne 1, on voit deux pâles virgules
  flottant de part et d'autre du corps. Colonne 2, on voit **une aile** : elle part du fuselage,
  s'élargit, et se termine en pointe. Le regard ne cherche plus le lien, il n'y a plus de lien à
  chercher.
- **La colonne 3 (repliée) est encore plus solide** : la silhouette devient une pointe de flèche
  unique.
- **Le feu cyan d'emplanture devient superflu.** Il devait rattacher optiquement deux masses
  séparées ; il n'y a plus deux masses. L'ajouter maintenant reviendrait à souligner une jonction
  qui n'a plus besoin d'être expliquée — et à dépenser de l'émissif là où le vaisseau en a déjà
  huit sources. **Recommandation : ne pas le poser.**
- Les deux autres arbitrages proposés par BRIEF-0035 (resserrer la fente, élargir la lame) sont
  **sans objet** : ils coûtaient tous deux de la flèche admissible, et le problème qu'ils visaient
  n'existe plus.

Le brief avait raison sur ce point : **l'emplanture fixe résout le problème à la source.**

---

## 6. Décisions de forme et leurs raisons

- **L'emplanture s'élargit vers l'arrière**, jusqu'à x = 0,648 à y = +0,437. Ce n'est pas un choix
  de style : c'est la forme exacte du vide qu'elle remplit. La corde de racine de la lame est très
  râteau (62,9° par rapport à l'axe transversal), donc la matière fixe qui doit se trouver en deçà
  d'elle est un triangle dont la pointe est en avant. C'est le plan des emplantures d'appareils à
  géométrie variable dont le pivot est très en dehors.
- **Section en coin, plancher plat.** Le galbe est entièrement sur le dessus (30 % d'épaisseur au
  bord interne, 100 % à 42 % de la largeur, 34 % à la lèvre externe) ; la sous-face est **plate**.
  Une sous-face galbée aurait un point bas quelque part, et ce point bas serait le seul chiffre qui
  compte pour le jeu de la lame.
- **La lèvre externe reste épaisse** (34 % de l'épaisseur locale, soit 10 mm). Un bord effilé aurait
  lu comme une découpe de papier là où il faut lire une pièce sous laquelle on rentre.
- **Le détail de l'emplanture est posé en fraction de sa largeur locale**
  (`.claude/resources/pratique-detail-en-fraction-de-corde.md`) : sa largeur varie de 40 à 400 mm
  d'une station à l'autre, une abscisse absolue ne désignerait pas la même surface deux fois.
  Rainure longitudinale sur la bande `v = 0,18…0,42`, aplat bleu sur `v = 0,42…0,72` entre
  y = −0,020 et +0,420, lèvre dorée en avant du pivot et sombre en arrière (là où elle borde le
  logement).

---

## 7. Limites connues

1. **La sous-face de l'emplanture est visible depuis le dessous.** Entre x ≈ 0,32 (où elle sort du
   fuseau) et son bord externe, elle surplombe du vide : c'est une casquette, pas un caisson fermé.
   Invisible depuis la caméra de jeu (20° de la verticale) et depuis l'écran d'accueil, vérifié au
   rendu à 78° ; visible dans une vue de ventre. La fermer demanderait une peau ventrale reliant
   l'emplanture à la nacelle, ce qui **rejoindrait le fuseau à l'aile par le dessous** et
   supprimerait une partie de la lecture « lame séparée » acquise en BRIEF-0035. Laissée ouverte
   volontairement — à trancher par le concepteur si une vue ventrale est prévue.
2. **L'ouverture derrière le bord de fuite de l'aile n'est pas bouchée**, à aucune flèche. Ce n'est
   pas la racine : c'est l'arrière de l'aile, il existait avant ce brief et le boucher ferait
   réapparaître le delta plein que BRIEF-0035 a supprimé.
3. **`Muzzle_Wing_*` et `Muzzle_Tip_*` restent figés à la pose déployée.** `ak.attach_point()` ne
   sait créer qu'un `Empty` à la racine — le kit n'expose aucun parentage pour les points d'attache.
   Limite déjà signalée par BRIEF-0035, inchangée, hors périmètre (interdiction de toucher à
   `aegis_kit.py`).
4. **L'aspect de l'aile change** (§4.3) : ses panneaux bleus et ses rainures sont désormais creusés
   et non plus en relief. Correction d'un défaut, mais **c'est un changement visible** — à valider à
   la revue.
5. **Observation faite en dimensionnant l'emplanture, hors périmètre** : le carénage dorsal de
   nacelle (`FAIRING`, 9 sections) est **entièrement contenu à l'intérieur du fuseau** — sa
   demi-largeur et sa hauteur maximales (0,0956) sont inférieures au rayon local (0,098) à toutes
   ses stations. Il ne produit aucune surface visible et `nacelle_half_width()` ne le retient jamais.
   Environ 250 triangles inutiles, et le pied de dérive s'appuie en fait sur le fuseau. À nettoyer
   lors d'une prochaine passe si le budget devient serré.
6. **Pas de `.blend`, pas de texture, aucun fichier de `scenes/`, `scripts/`, `resources/` touché** —
   conforme au brief.

---

## 8. Livrables

| Fichier | Rôle |
|---|---|
| `tools/blender/build_specter_9.py` | script retravaillé (source de l'asset, ADR-0008) |
| `assets/imported/models/ships/specter_9.glb` | coque + 6 pièces mobiles (Git LFS) |
| `docs/forge/output/BRIEF-0036-report.md` | ce rapport |
| `docs/forge/output/BRIEF-0036-aplat-noir-deux-fleches.png` | **le critère n°1** : avant / déployé / 26° |
| `docs/forge/output/BRIEF-0036-jonction-aile-coque.png` | gros plan de la jonction, aux deux extrêmes |
| `docs/forge/output/BRIEF-0036-planche-deux-fleches.png` | planches 4 vues, déployé et 26° |
| `docs/forge/output/BRIEF-0036-lisibilite-vue-de-jeu.png` | vue « game » à 48 / 64 / 96 px, trois états |

Provenance mise à jour dans `assets/licenses/ASSET_PROVENANCE.csv` : la ligne `specter_9_hull` est
**remplacée**, non dupliquée ; quatre lignes de rendu ajoutées.

---

## 9. Critères d'acceptation

- [x] **Aucun bras de pivot ni fente visible à la racine d'aile**, sur toute la plage de flèche —
      chape et ferrure supprimées, pivot enfoui, recouvrement mesuré négatif aux deux extrêmes.
- [x] **La racine du panneau est couverte par l'emplanture au déployé ET au replié** —
      −14,0 mm à 0°, −26,3 mm à 26°, mesuré à chaque build.
- [x] **En flèche maximale le panneau se range contre l'emplanture** — recouvrement en plan de
      26,3 mm, **jeu résiduel vertical de 4,4 mm**, mesuré sommet par sommet, flèche × braquage.
- [x] **L'aplat noir montre toujours les échancrures fuselage/nacelle** — contour non convexe,
      quatre mesures identiques à BRIEF-0035.
- [x] **Plafond de flèche mesuré et remesuré à chaque build** — 32,25° pour 26 visés ; **il ne
      passe pas sous 26°**, l'emplanture ne réduit pas la plage.
- [x] **Bbox, budget, matériaux, UV, points d'attache, déterminisme** — conformes ; `check.sh` vert.
- [x] **Rendu aux deux extrêmes** — dans trois des quatre planches livrées.


---

## Arbitrage du concepteur — sous-face de l'emplanture

La sous-face reste une **casquette ouverte**, elle ne sera pas fermée en caisson.

Motif : elle est invisible depuis la caméra de jeu (vérifié au rendu jusqu'à 78°), et la fermer
relierait le fuseau à l'aile **par le dessous**, annulant une part de la séparation acquise au
BRIEF-0035. La règle d'ADR-0011 tranche : *ce qui n'est pas visible depuis la caméra de jeu n'existe
pas* — mais ce qui casserait une silhouette acquise, si.

À rouvrir seulement si une vue de ventre apparaît un jour (cinématique, écran de sélection).
