# BRIEF-0043 — Null Maw, coque 3D : compte-rendu

*Livré le 2026-08-23 par `asset-forge`. `null_maw.glb` sha256
`f5f2f42051d97586f085e26341748ae20a4c15e5b28b2b9fdb26a41b20b8127f` (437 556 o).*

## 1. Livrables

| Fichier | Quoi |
|---|---|
| `tools/blender/build_null_maw.py` | script de construction, déterministe, auto-validant |
| `assets/imported/models/ships/null_maw.glb` | le mesh (LFS) |
| `docs/forge/output/BRIEF-0043-planche-quatre-vues.png` | recette 4 vues au repos (ADR-0006) |
| `docs/forge/output/BRIEF-0043-corolle-ouverte.png` | 6 poses : repos, 45°, fond de course 57,5° |
| `docs/forge/output/BRIEF-0043-silhouette-comparee.png` | **le test qui décide** : aplats noirs Null Maw / Choir Mine |
| `docs/forge/output/BRIEF-0043-report.md` | ce document |

## 2. Le chiffre que la session principale attend

**Seuil « puits franchement visible » : 42,5°.** C'est l'angle à partir duquel le disque
central dégagé (vu de dessus, mesuré par lancer de rayons verticaux sur une grille polaire de
2 304 points) atteint le rayon le plus étroit du percement, **0,160 m** : à partir de là la
ligne de visée traverse la coque de part en part, on voit le fond de l'espace au travers.
En dessous, l'œil voit un creux ; au-dessus, il voit un trou. La planche de poses le montre
sans argumenter : au repos le plan témoin bleu placé derrière la coque reste masqué, à 45° il
apparaît en plein centre.

Valeur recommandée pour `open_angle_deg` : **45°** — 2,5° au-delà du seuil (la mesure est
échantillonnée tous les 2,5°), 89,1 % de la bouche dégagée, et **12,5° de marge mécanique**
sous le dernier angle intégralement dégagé (57,5°).

| ouverture | bouche dégagée | disque central libre | empreinte hors-tout | traversant |
|---|---|---|---|---|
| 0° (repos) | 76,7 % | r = 0,127 m | 1,580 m | non |
| 20° | 79,3 % | r = 0,137 m | 1,623 m (maximum) | non |
| 40° | 87,2 % | r = 0,155 m | 1,538 m | non |
| **42,5°** | 88,1 % | **r = 0,165 m** | 1,518 m | **oui** |
| 45° | 89,1 % | r = 0,165 m | 1,497 m | oui |
| 55° | 92,9 % | r = 0,184 m | 1,396 m | oui |

⚠️ **L'empreinte n'est pas monotone** : la corolle s'élargit jusqu'à 15° (1,625 m) puis se
resserre — les bras basculent vers le bas, leur projection raccourcit. Si une hitbox suit
l'ouverture, elle doit suivre cette courbe et pas une interpolation linéaire.

## 3. Débattement mécanique, pétale par pétale

Mesuré sur le **maillage livré** (BVH, distance triangle-triangle dans les deux sens),
par pas de 2,5°, contre la coque **et** l'anneau **et** les deux voisins.

| Pièce | bras | dernier angle intégralement dégagé | 1re interpénétration | butée | marge coque au pire | marge voisin au pire |
|---|---|---|---|---|---|---|
| `Petal_01` | 519 mm | **57,5°** | 60,0° | coque + anneau | 5,4 mm | 59,9 mm |
| `Petal_02` | 470 mm | **60,0°** | 62,5° | coque + anneau | 4,4 mm | 55,1 mm |
| `Petal_03` | 536 mm | **57,5°** | 60,0° | coque + anneau | 5,4 mm | 55,1 mm |
| `Petal_04` | 469 mm | **57,5°** | 60,0° | coque + anneau | 5,3 mm | 47,9 mm |
| `Petal_05` | 262 mm | **60,0°** | 62,5° | coque + anneau | 4,8 mm | 55,1 mm |

- **Valeur sûre pour le gameplay : 50°.** 7,5° sous la butée la plus basse une fois ramenées
  les cinq pièces au pire cas (57,5°, cf. ci-dessous). Au-delà de 55° la corolle plonge sous le
  collier et la lecture de « fleur » cède à une lecture d'insecte : la butée mécanique n'est pas
  une cible esthétique.
- Ce qui butte est toujours **la face supérieure de l'anneau d'accrétion**, jamais un voisin :
  les pétales ne se touchent à aucun angle (marge minimale 47,9 mm, atteinte au repos).
- **`Petal_02` et `Petal_05` gagnent 2,5°** parce que, dans l'orientation modélisée, ils
  débordent d'une brèche de l'anneau. Comme `Ring` tourne, **retenir 57,5° pour les cinq** :
  c'est le pire cas sur toute rotation de l'anneau. Les cinq azimuts de pétale tombent bien
  au-dessus d'un arc plein dans l'orientation livrée, donc le tableau ci-dessus est déjà le
  pire cas pour `Petal_01/03/04`.
- Le rayon d'exclusion de charnière (`HINGE_SKIP = 55 mm`) **n'est pas un réglage à vue** :
  toute la ferrure de charnière (les deux joues et leurs bossages d'axe) tient à moins de
  58 mm du pivot, et une rotation autour du pivot conserve la distance au pivot. Ce qui est
  écarté de la mesure est exactement ce qui ne peut, par construction, rencontrer rien d'autre.

### Pivots et axes, en repère Godot

Angle > 0 = ouverture (bras vers le bas, langue vers le haut). `Basis(axe, angle)` suffit.

| Nœud | pivot (X, Y, Z) | axe de rotation |
|---|---|---|
| `Petal_01` | (−0,2550, +0,1150, +0,1030) | (+0,3746, 0, +0,9272) |
| `Petal_02` | (+0,0287, +0,1150, +0,2735) | (+0,9945, 0, −0,1045) |
| `Petal_03` | (+0,2492, +0,1150, +0,1162) | (+0,4226, 0, −0,9063) |
| `Petal_04` | (+0,0240, +0,1150, −0,2740) | (−0,9962, 0, −0,0872) |
| `Petal_05` | (−0,2137, +0,1150, −0,1731) | (−0,6293, 0, +0,7771) |
| `Ring` | (0, 0, 0) | (0, 1, 0) — rotation pure sur l'axe |

L'axe se recalcule côté jeu sans table : `axe = UP × normalize(pivot.x, 0, pivot.z)`.
`Ring` est la seule pièce dont l'origine reste à zéro, et c'est correct — le piège documenté
par `aegis_kit.moving_part` (une pièce qui décrit un arc autour du centre de l'objet) est ici
le comportement voulu.

## 4. Contrat et mesures

| Critère | Exigé | Mesuré | |
|---|---|---|---|
| Largeur X | 1,45 m ±3 % | **1,4537 m** (+0,26 %) | ✅ |
| Longueur Z | 1,45 m ±3 % | **1,4499 m** (−0,01 %) | ✅ |
| Hauteur Y | 0,35 à 0,45 m | **0,4235 m** | ✅ |
| Centrage du pivot | ±20 mm | (−0,00003, +0,0618, +0,0001) | ✅ |
| Triangles | ≤ 7 000 | **6 630** (marge 5,3 %) | ✅ |
| Sommets | — | 7 554 | |
| UV + tangentes | 36 primitives | **36 TANGENT, 36 TEXCOORD_0** | ✅ |
| Déterminisme | 2 exports identiques | `build-hull.sh --check null_maw` → OK | ✅ |
| `Muzzle_C` | au centre | (0, 0, 0), sur l'axe, dans le puits | ✅ |
| `Engine_C` | **absent** | absent | ✅ |
| Kit partagé | non modifié | `aegis_kit.py` intact | ✅ |

⚠️ **La bounding box axiale n'est pas l'encombrement réel.** Les cinq pointes visent 22°, 96°,
155°, 265° et 321° — aucune n'est alignée sur un axe. La bbox du contrat vaut donc 1,4537 m,
mais le **diamètre circonscrit au repos vaut 1,580 m**. C'est le chiffre à utiliser pour un
rayon de hitbox ou un test de chevauchement en vague, pas 1,45.

### Répartition des matériaux, en aire réelle (lue sur le `.glb` livré)

| Matériau | aire | part | rôle |
|---|---|---|---|
| `AA_Greeble` | 1,31 m² | 47,2 % | dessous des pétales, gorge du puits, joues de charnière — jamais vu d'en haut |
| `AA_Panel` | 0,66 m² | 23,8 % | plaques violettes enfoncées des pétales, anneau de plaques du collier |
| `AA_Hull` | 0,32 m² | 11,7 % | joints entre plaques |
| `AA_Trim` | 0,25 m² | 9,1 % | couronne ivoire de la bouche, crochets, quilles, tranches |
| `AA_Emissive_Engine` | 0,11 m² | **4,1 %** | haut de gorge, liserés de lèvre, fissures, dents de l'anneau |
| `AA_Glass` | 0,11 m² | 3,9 % | membrane sombre du fond du puits |
| `AA_Marking_Red` (vert maladif) | 0,005 m² | 0,2 % | trois évents |

L'émissif est à **4,1 %**, très en deçà des ~10 % au-delà desquels un accent devient une
livrée. Il est entièrement sur des surfaces **supérieures** ou tourné vers la caméra.

## 5. Le test qui décide — Null Maw contre Choir Mine

`choir_mine.glb` **existe** : la comparaison est faite sur les deux vrais `.glb`, pas sur une
reconstruction. Méthode ADR-0014 : rendu orthographique vu de dessus, canal alpha en
film-transparent (un percement traversant ressort donc blanc, sans interprétation), **même
échelle métrique de 320 px/m**, puis réduction à 40 px et 20 px.

| | Null Maw (repos) | Choir Mine |
|---|---|---|
| Largeur mesurée sur l'aplat | 1,456 m | 1,150 m |
| Couverture de l'aplat | 26,7 % | 34,2 % |
| **Rayon minimal de matière depuis l'axe** | **124 mm** | **2 mm** |

**Verdict : oui, on les distingue — aux trois tailles, et sur trois signaux indépendants.**

1. **Le centre.** La mine a de la matière jusqu'à 2 mm de son axe : c'est un disque plein.
   Le Null Maw n'en a aucune dans un rayon de 124 mm au repos, 160 mm à 45°. À 20 px, le trou
   blanc tient encore sur 2-3 pixels au cœur de la forme. C'est le signal qui survit à la
   réduction, parce qu'il est topologique et pas décoratif.
2. **Le contour.** Cinq lobes longs et inégaux, à écarts irréguliers (56° à 110°) contre une
   couronne régulière et fine. À 40 px, l'un est une croix ébréchée, l'autre une pastille.
3. **La taille.** 1,45 m contre 1,15 m, +27 %.

Réserve honnête : la Choir Mine livrée n'est pas le cercle lisse que décrivait le tableau du
brief — sa couronne de modules lui donne un bord crénelé régulier. La distinction ne repose
donc pas sur « rond contre dentelé » mais sur **régulier et fin contre inégal et long**, ce qui
tient aussi bien, et sur le trou central, qui tranche seul.

## 6. Choix créatifs et leur justification

- **Le puits est un percement réel et traversant**, pas une cavité peinte : le collier est un
  tore. C'est ce qui rend le centre lisible en aplat, et c'est aussi ce qui interdit à un futur
  réglage d'y remettre un noyau lumineux par inadvertance — il n'y a pas de surface pour ça.
- **Le magenta borde le vide** (haut de gorge + liserés de lèvre des langues) et s'éteint dès
  le tiers supérieur de la gorge, qui passe en anthracite puis en membrane sombre. Vu de
  dessus : un anneau de lumière autour d'un puits qui s'assombrit en descendant.
- **Onze crochets ivoire** penchés au-dessus de la lèvre, pour cinq pétales : les deux rythmes
  ne coïncident jamais, la bouche ne peut pas retomber sur la symétrie de la corolle. C'est
  aussi ce qui nomme l'objet — une gueule.
- **L'anneau d'accrétion est brisé** (trois arcs inégaux, une dent lumineuse sur quatre) et
  **flotte** à 30 mm du collier. Un anneau lisse et jointif ne se voit pas tourner ; celui-ci
  si. Le vide qui le sépare de la coque dit « machine à gravité », pas « carter ».
- **Vocabulaire de famille tenu** : anneaux de plaques concentriques sur le collier, plaques
  violettes enfoncées (le violet couvre 24 % de l'aire, comme sur le Needle Scout, contre 12 %
  d'anthracite qui ne fait plus que les joints), carapace ivoire, vert maladif à 0,2 %.
  Les **fissures magenta rayonnantes** de la planche sont là — mais elles ne rayonnent plus
  d'un cœur, elles rayonnent d'un vide et s'arrêtent net sur la lèvre.
- **Charnière en fourche** (deux joues hors de la largeur du pétale) au lieu d'un axe plein
  traversant : le premier jet interpénétrait la plaque dès la pose de repos et le débattement
  mesuré tombait à 0°. Le contrat d'export ne s'en apercevait pas — c'est exactement le défaut
  que le brief annonçait.

## 7. Limites connues et réserves

1. **Le puits est déjà ouvert à 77 % au repos.** Il n'était pas possible de le fermer davantage
   sans contredire le critère qui décide : une corolle close redonne un disque plein vu de
   dessus, donc une mine. L'ouverture ne *révèle* donc pas le puits, elle le **rend
   traversant** — d'où le seuil à 42,5°, qui est un fait géométrique et non un jugement.
2. **L'empreinte diminue au-delà de 15°.** L'objet ne « grandit » pas en s'ouvrant au-delà de
   cet angle ; il s'épanouit vers le bas. Si le gameplay veut une menace qui grandit, jouer sur
   le télégraphe (VFX, anneau qui accélère) plutôt que sur l'angle.
3. **La vérification d'orientation du kit est inopérante ici.** Le seul point d'attache,
   `Muzzle_C`, est à l'origine : le témoin asymétrique sur lequel `export_hull()` s'appuie vaut
   (0,0,0) → (0,0,0) et ne prouve rien. Pour un objet radial sans avant ni arrière c'est sans
   conséquence de gameplay, mais il ne faut pas croire l'orientation « vérifiée ».
4. **Marge de triangles mince** : 6 630 sur 7 000 (5,3 %). Le plafond « ennemi léger » d'ADR-0011
   est à 12 000 ; c'est le brief qui fixe 7 000. Tout ajout de détail devra passer par un
   relèvement explicite, pas par un rognage silencieux ailleurs.
5. **Marge mécanique de 5 mm** entre le bras et l'anneau à fond de course. C'est étroit pour un
   objet qui pourrait un jour être secoué par un shader de déformation ou une animation
   élastique. Si ce cas se présente, descendre `RING_SECTION` de 10 mm rend 4° environ.
6. **Le script de pose et de silhouette n'est pas versionné** (scratchpad de session), comme
   pour BRIEF-0040. Les trois planches sont reproductibles à partir du `.glb` seul, mais leur
   recette exacte n'est pas dans le dépôt. Si ces planches doivent être régénérées à chaque
   reforge, c'est un `tools/render-poses.py` à cadrer dans un brief séparé.

## 8. Défaut corrigé en cours de brief — tangentes absentes

Signalé par la session principale, mesuré, corrigé, revérifié : le `.glb` sortait **sans aucune
tangente ni UV** (0/36). Deux omissions de ma part, pas une : ni `_triangulate_ngons()` ni
`ak.box_project_uv()` n'étaient appelés. La première est indispensable parce que l'exporteur
glTF abandonne le calcul mikktspace dès qu'une face dépasse quatre sommets — il l'annonce dans
le flot de sortie, puis exporte quand même, sans l'attribut. Aucune erreur, aucun test rouge.
Ce script produit des dizaines de n-gons (chaque `cap_ring`).

Après correction, vérifié en comptant les attributs dans le chunk JSON du `.glb` :
**36 primitives, 36 `TANGENT`, 36 `TEXCOORD_0`**, et **6 630 triangles inchangés** (une n-gon de
n sommets vaut n−2 triangles, ici comme dans l'exporteur). Densité de dépliage
`TEXELS_PER_METER = 4.0`, la même que la Choir Mine et le Specter-9 : deux unités de la même
famille doivent porter la même feuille de détail à la même échelle. Déterminisme revérifié
après coup (`--check` → OK, sha `f5f2f420…`).

`needle_scout.glb` et `crescent_interceptor.glb` sont, eux, toujours dans ce cas dans le dépôt —
hors périmètre de ce brief, mais la dette existe et se corrige de la même façon.

## 9. Suggestions (hors périmètre, à arbitrer)

- **Kit** : `_triangulate_ngons()` est copié-collé à l'identique dans six scripts de coque, et
  son oubli est silencieux et coûteux. Sa place est dans `aegis_kit.py`, mieux encore : dans
  `export_hull()`, qui pourrait **refuser** d'exporter un maillage sans `TANGENT` comme il
  refuse déjà une bbox hors contrat. Le contrat couvre la géométrie mais pas les attributs de
  sommet — c'est le seul trou par lequel ce défaut passe.
- **Gameplay** : l'anneau brisé donne une lecture gratuite de l'état de charge — vitesse de
  rotation proportionnelle au réarmement. Rien à modéliser, tout est déjà dans le `.glb`.
