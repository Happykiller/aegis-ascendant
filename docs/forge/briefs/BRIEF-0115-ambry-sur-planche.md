# BRIEF-0115 — Ambry, sur planche cette fois

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-13
- **Planche** : `assets/reference/concepts/ambry_concept_sheet_2026-09.png` ⚠️ **à ouvrir en premier**
- **Spécification écrite** : `docs/forge/concepts/AMBRY-ce-qu-on-doit-voir.md`
- **Suite de** : `BRIEF-0114` (livré — le relief est venu, la LECTURE n'est pas venue)

## Pourquoi ce lot existe

Le `BRIEF-0114` a triplé la géométrie d'Ambry et doublé son contraste local. **Et l'opérateur ne
reconnaît toujours pas ce qu'il regarde** : « je comprends toujours pas visuel ce que c'est, c'est
moche, pas de forme ». Troisième signalement en neuf jours.

⚠️ **CE N'EST PAS VOTRE FAUTE, ET C'EST IMPORTANT DE LE DIRE.** Tout ce que vous avez jamais reçu
sur Ambry tient en **une ligne** du `BRIEF-0089` : *« antenne, serre, modules d'habitation »*. Vous
avez livré exactement ces trois mots. Ce qui manquait était le brief, pas le travail.

**Il existe maintenant**, et il est de deux pièces : une planche de concept, et une spécification
écrite. C'est la première fois qu'Ambry est décrite.

## Ce qu'Ambry est — en une phrase, parce que tout en découle

**C'est l'avant-poste où le JOUEUR a grandi**, quatre-vingts personnes, tu depuis 379, **radié** du
Registre plutôt que déclaré perdu — et retrouvé soudé sur le flanc de la chose qui l'a emporté.
Debout. Intact. **Éclairé.**

> ⚠️ **Le mot est INSOUTENABLE, pas SPECTACULAIRE. Ce qui doit serrer la gorge, c'est que tout va
> bien.** La serre pousse, les fenêtres sont allumées, l'antenne est debout. Une ruine ne dirait
> rien de plus qu'une ruine.

Lisez `AMBRY-ce-qu-on-doit-voir.md` en entier avant de dessiner. Il porte l'enjeu, les quatre
lieux, et les sources du lore.

## La planche est le contrat

Elle porte six vues, et **chacune répond à une question que vous vous poseriez** :

| Vue | Ce qu'elle tranche |
|---|---|
| **Vue gameplay 70°** | l'insertion sur le flanc, et la lecture réelle en jeu |
| **Silhouette de dessus** | les proportions, 27 × 5,7 m, et le contour qui doit se reconnaître |
| **Élévation de flanc** | les quatre zones dans l'ordre, et la hauteur |
| **Détail A — Greffe** | couture **sale**, métal coulé, deux colliers, **roche arrachée sous la dalle** |
| **Détail B — Serre** | verrière/bâche sur arceaux, **ça pousse encore**, unique vert vivant |
| **Détail C — Re-plombé** | module **de travers de 2 à 3°**, passerelle décalée, main courante absurde |

### ⚠️ Le panneau « À ÉVITER » de la planche EST la grille d'acceptation

Quatre défauts y sont nommés, et ce sont exactement les quatre de la version en jeu :

1. **boîtes identiques** ;
2. **ailettes vertes** (la serre lit comme un radiateur) ;
3. **tout d'équerre** ;
4. **aucune vie lisible**.

> **« AMBRY ≠ INSTALLATION STANDARD — un lieu humain, pas un asset générique. »**

## ⚠️ Le re-plombé : le jeu contredit aujourd'hui son propre lore

La bible le glose en toutes lettres, an 301 :

> « On le retrouve **intact et re-plombé** : rien de détruit, rien de volé, **tout rebâti
> légèrement de travers**. »

Et `NULL_CHOIR.md` : « la jonction entre la coque d'origine et ce qui a poussé dessus **n'est
jamais propre** ».

**Re-plombé ne veut pas dire redressé.** L'Unisson se dégrade par recopie — c'est le fait central
de la campagne. Or le générateur a lu « remis d'aplomb » et a tout aligné sur deux axes au
millimètre : Ambry est aujourd'hui **la seule chose parfaitement orthogonale** d'un vaisseau fait
de facettes inclinées, et sa couture est nette. C'est l'inverse exact de ce qu'elle doit être.

**Détail C de la planche donne la valeur : 2 à 3 degrés.** Assez pour qu'on le voie, trop peu pour
qu'on croie à une erreur d'assemblage. Le malaise doit demander **une seconde**, pas zéro.

## ⚠️ LA SEULE CHOSE QUE LA PLANCHE NE PEUT PAS AVOIR : LA HAUTEUR

C'est la conversion que vous seuls pouvez faire, et c'est le cœur du lot.

| | |
|---|---|
| Assise du radeau | `y = −4,48` |
| Plafond de construction | **`−3,20`** — le plan de vol du chasseur passe juste au-dessus |
| **Ciel disponible** | **1,28 m**, sur 27 m de long |

Ambry est à `x 7,90..13,60`, donc **DANS le plan de vol** (`|x| ≤ 14`). La règle B des flancs ne
s'applique pas : **rien ne peut monter**.

**Donc la lecture vient du PLAN, et elle y vient très bien** — le corridor rend à **45,8 px/m** :

| Objet | Taille monde | À l'écran |
|---|---:|---:|
| Ambry entière | 27,0 m | **1 237 px** |
| sa largeur | 5,7 m | 261 px |
| une porte | 0,60 m | **27 px** |
| un montant de garde-corps | 0,20 m | **9 px** |
| un détail de 3 cm | 0,03 m | 1,4 px — ne le payez pas |

> **Une porte fait 27 pixels. Un garde-corps se voit.** Ce qui dit « des gens vivaient là » est
> donc parfaitement à portée — mais **en plan**, jamais en élévation.

Deux conséquences directes :

- **le mât est le seul accent vertical**, et il a déjà le droit d'aller à −3,22. Faites-en la
  silhouette : c'est la seule chose qui dépasse ;
- **la roche arrachée du Détail A doit DÉBORDER**, pas pendre sous la dalle. À 70° de plongée, rien
  sous un radeau de 5,5 m n'est visible — c'est votre propre mesure du `BRIEF-0113`, et c'est ce
  qui a fait rater les douze béquilles au premier tirage.

## Les fenêtres allumées — un slot neuf, et il est décidé

**C'est l'élément le plus important de toute la pièce**, et il n'existe pas aujourd'hui.

⚠️ **PAS `AA_Emissive_Engine`.** L'interdit de magenta sur Ambry tient : le magenta appartient à
l'Unisson. Mais l'interdit porte sur **cette couleur-là**, pas sur la lumière. Déclarez un
**neuvième slot local**, `AA_Window_Ambry`, en **ambre chaud** — même procédé que le huitième au
`BRIEF-0090`, déclaré localement dans `build_long_cortege.py`, sans toucher au kit.

⚠️ **ET CE SLOT SÉPARÉ A UNE CONSÉQUENCE DE JEU QUE JE VEUX** : `CortegeSkin.emissives_of()` ne
ramasse que `AA_Emissive_Engine`, donc **le blackout de fin n'éteindra pas Ambry**. Quand les trois
moteurs sont arrachés et que le vaisseau meurt, ses veines magenta s'éteignent sur 85 conduits —
et **les fenêtres d'Ambry restent allumées**. Les gens n'étaient pas alimentés par ce qui les a
pris. Je ne câble rien : il suffit que le slot soit distinct.

## Ce qui ne change pas

- **La valeur claire** — ivoire `#EDEAE3` des coques Helios Vanguard contre l'anthracite
  `#24252B`. Décision de l'opérateur du 2026-09-13, l'amortissement a été proposé et écarté.
- **L'état INTACT.** Ni ruine, ni trou, ni feu.
- **Le vert de la serre est la seule couleur**, et c'est un vert **vivant** — pas les ailettes
  plates d'aujourd'hui.
- **Les deux colliers de greffe et le pas d'appontage gardent l'anthracite** : ils appartiennent au
  vaisseau, pas à l'avant-poste. Le pas est **vide**, et c'est de là que le pilote est parti.
- ⚠️ **Le bord avant reste à `s = 446,5 ± 1`.** Le code y déclenche la réplique de Lyra à l'instant
  où Ambry entre dans le cadre ; le déplacer décale la révélation. Gardé par
  `test_the_front_edge_of_ambry_is_read_from_the_hull`.

⚠️ **AUCUN BUDGET DE TRIANGLES.** Décision de l'opérateur, toujours en vigueur : « je ne veux pas
entendre parler de budget et de restriction, je veux un jeu beau ». Ambry est à 3 364 triangles
après le `BRIEF-0114` ; le corridor rend à 1,5–5,1 ms sur les 16,67 d'une image à 60 Hz.
**Rapportez les comptes, ne les contraignez pas.**

## Texture (ADR-0028) / Animation (ADR-0046 §6)

**Aucune image.** PBR par facteurs et slots, comme tout le Long Cortège. Les quatre cartes
`ambry_hull_*` existent et fonctionnent ; `CortegeSkin` posera le reste.

⚠️ **Le nouveau slot `AA_Window_Ambry` n'a pas besoin de carte** : c'est un émissif par facteur.

⚠️ **ET SIGNALEZ CE QUE VOUS DÉPLIEZ.** Le `BRIEF-0114` a laissé un défaut ouvert (backlog du
2026-09-13) : `box_project_uv(ambry, 0,700)` déplie **tout l'objet** à la densité d'Ambry, mais le
code choisit l'échelle par nom de matériau et seul `AA_Hull_Ambry` reçoit la sienne — 1 652
triangles sur 3 364 reçoivent donc les cartes du bordé 3,5× trop fines. **Si votre géométrie neuve
aggrave ce partage, dites-le et proposez** : un slot par famille, ou une densité annoncée par
slot. C'est moi qui corrigerai côté code, mais je dois savoir ce que vous livrez.

**Géométrie figée.** Ambry n'a pas d'animation.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_long_cortege.py` | `build_ambry()` sur la planche, + le slot `AA_Window_Ambry` |
| `assets/imported/models/backgrounds/long_cortege.glb` | le corridor |
| `docs/forge/output/BRIEF-0115-report.md` | triangles par slot, hauteur consommée, angles de travers, densités de dépliage par slot |
| `docs/forge/output/BRIEF-0115-planche.png` | avant/après **au cadrage du jeu**, plus une vue de dessus à comparer à la silhouette de la planche |

## Critères d'acceptation

- [ ] ⚠️ **LES QUATRE « À ÉVITER » DE LA PLANCHE SONT LEVÉS**, un par un, et le rapport le dit :
      plus de boîtes identiques, plus d'ailettes vertes, plus de tout-d'équerre, **de la vie
      lisible**.
- [ ] **Les quatre zones se reconnaissent** sur la capture en jeu : greffe, habitation, serre,
      antenne. Pas « il y a de la matière » — « on voit un lieu, et il a des parties ».
- [ ] **Les fenêtres sont allumées**, sur leur propre slot, et **ne sont pas `AA_Emissive_Engine`**.
- [ ] **Le re-plombé se voit** : au moins un module à 2–3° et une passerelle décalée, mesurés en
      degrés dans le rapport.
- [ ] **La couture de greffe n'est pas propre**, et la roche arrachée **déborde** — visible depuis
      la caméra du jeu, pas seulement en élévation.
- [ ] **Rien au-dessus de `−3,20`**, mesuré sur le binaire.
- [ ] **Le bord avant reste à `s = 446,5 ± 1`** et `./scripts/check.sh` est vert.
- [ ] **La silhouette de dessus se compare à celle de la planche** dans le rapport.
- [ ] **Déterminisme** : trois exécutions, zéro octet divergent.
- [ ] **Rendu et REGARDÉ à la caméra du jeu** (`ADR-0006`), avant/après au même cadrage.

⚠️ **Le test final, en une question** : un joueur qui voit l'image une seconde et demie doit
pouvoir dire *« des gens vivaient là »* — puis, une seconde plus tard, *« et ce n'est pas eux qui
l'ont remonté »*.

## Hors périmètre

- **Le code de jeu.** La révélation de Lyra est déjà recalée (`b2cd87d`) ; le blackout se réglera
  tout seul si le slot est distinct.
- **La valeur, l'interdit de magenta, l'état intact** : décidés.
- **Le complexe industriel du tronçon 5**, la poupe, le reste du bordé.
