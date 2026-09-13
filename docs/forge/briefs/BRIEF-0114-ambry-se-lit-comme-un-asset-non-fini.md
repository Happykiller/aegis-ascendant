# BRIEF-0114 — Ambry se lit comme un asset non fini : la faire exister comme une construction

- **Statut** : livré et intégré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-13

## Le verdict, et il est de l'opérateur, deux fois

> « Il y a un truc à droite sans texture blanc, je ne sais pas ce que c'est » (en jouant, 2026-09-05)

> « Dans le dernier tronçon on a toujours cette zone claire, non texturée, non travaillée, qui ne
> s'intègre pas du tout au design » (en jouant, 2026-09-13, deux captures à l'appui)

Ambry est la **destination du niveau** et sa révélation : quatre-vingts personnes, debout, greffées
sur le bordé de celui qui les a emportées. L'homme qui l'a commandée la prend pour un bloc oublié.
Quelle que soit l'intention, **c'est un échec de l'exécution**, et il est mesurable.

## ⚠️ CE QUI EST DÉCIDÉ ET NE CHANGE PAS

L'opérateur a tranché le 2026-09-13 : **on garde la valeur claire.** L'ivoire `#EDEAE3` des coques
Helios Vanguard contre l'anthracite `#24252B` de l'Unisson est ce qui dit « ce n'est pas le même
camp qui a construit ça », et l'amortir a été explicitement écarté.

Restent intouchables, avec eux : le **vert maladif `#7C9E52`** de la serre (seul emploi de cette
couleur sur les 500 m), l'**orthogonalité** contre les facettes inclinées — le « re-plombé » —,
l'**absence de magenta**, et le fait qu'Ambry soit **INTACTE** : modules alignés, passerelle
continue, serre entière, antenne debout. Une ruine ne dirait rien de plus qu'une ruine.

## La mesure — « non travaillée » est littéralement exact

Comptée dans le binaire livré, sur l'emprise `x 6,90..14,10`, `s 443,5..476,5` :

| Slot | Triangles |
|---|---:|
| `AA_Greeble` | 573 |
| `AA_Hull` | 159 |
| **`AA_Hull_Ambry`** (les faces ivoire, celles qu'on voit) | **126** |
| `AA_Marking_Red` (la serre) | 86 |
| `AA_Glass` | 72 |
| `AA_Panel` | 8 |
| **TOTAL** | **1 024** |

**1 024 triangles pour 27 × 5,7 m**, soit 154 m² — **6,7 triangles par m²**. Les faces ivoire, qui
sont tout ce que l'œil retient, en font **126 sur 27 mètres** : *4,7 triangles par mètre linéaire*.

Le point de comparaison est dans le même tronçon, à cinq mètres de là : le complexe industriel du
`BRIEF-0111` fait **1 756 triangles** sur ~98 m², soit **18 par m²** — **2,7 fois plus dense**. Et
c'est la pièce que l'opérateur a validée sans réserve.

### Et ce n'est PAS un défaut de texture

J'ai vérifié en instanciant la coque et en passant `CortegeSkin.apply()` : les quatre cartes
`ambry_hull_{mul,nrm,rough,ao}.png` sont bien posées, `uv1_scale = 1,0`, normale comprise. Mesuré
sur la capture du joueur :

| | Ambry | bordé juste à côté |
|---|---:|---:|
| Luminance moyenne | **165** | 41 |
| Contraste local (détail, fenêtres de 16 px) | **17,4** | 6,7 |

Elle porte **plus** de détail de surface que la tôle voisine. Ce qui manque n'est pas la peau,
c'est le **relief** : quatre fois plus claire que tout le reste et presque plate, l'œil ne lit plus
une structure — il lit une découpe blanche.

⚠️ **L'entrée de backlog qui disait « plate, faute de toute texture au niveau 2 » est PÉRIMÉE.**
Les textures sont arrivées depuis. Ne repartez pas de ce diagnostic.

## ⚠️ LA CONTRAINTE QUI DÉCIDE DE TOUT : IL N'Y A PLUS DE CIEL

Le radeau est à `y = −4,48`, le plafond de construction à **`−3,20`**, et la boîte actuelle monte
déjà à **−3,53**. Il reste **0,33 m**, et l'antenne en consomme presque tout (elle s'arrête à
−3,22, soit 2 cm sous le plafond).

Ambry est à `x 7,90..13,60`, donc **DANS le plan de vol** (`|x| ≤ 14`) : la règle B des flancs de
poupe ne s'applique pas ici. **Vous ne pouvez pas monter.**

> **C'est le plan qui paie, et c'est mesuré** (`BRIEF-0110`) : sur cette caméra, une hauteur ne
> rend que **34 %** de sa longueur à l'écran quand un plan en rend **94 %**. Ambry offre 154 m² de
> plan à 94 % de rendement, et 0,33 m de hauteur. Travaillez le plan.

Et Ambry est **immense à l'écran** : 27 m à 45,8 px/m font plus de **1 200 px** de large. C'est un
des plus gros objets du niveau ; chaque mètre carré y vaut 2 100 pixels.

## Ce qu'il faut faire

**Donner à Ambry le relief d'une construction humaine, à plat, sans monter.** Vous choisissez
comment ; ce que la mesure rend évident :

1. **Les faces ivoire sont le sujet, et elles sont nues.** 126 triangles sur 27 m : pas une
   nervure, pas un joint de panneau franc, pas un décrochement. Une tôle de 27 m sans une
   interruption ne peut pas se lire autrement que comme une plaque.
2. **Creuser plutôt que dresser.** Sans ciel, ce qui reste est le négatif : rainures, sas en
   retrait, caniveaux, marches, ombres portées par 20 à 30 cm de décrochement. À 70° de plongée,
   un creux se lit aussi bien qu'une bosse — et lui n'a pas de plafond.
3. **Découper les quatre zones.** La docstring du générateur dit qu'elles se suivent dans l'axe du
   survol — greffe, habitation, serre, antenne — et qu'on les découvre dans cet ordre. **À l'écran
   elles ne se distinguent pas.** Le joueur voit une plaque là où il devrait voir quatre lieux.
4. **Les douze béquilles de longueurs différentes** — le « re-plombé », la meilleure idée de la
   pièce d'après son propre compte-rendu — **ne se voient pas** sur les deux captures. Si elles
   sont sous le radeau, à 70° de plongée personne ne les verra jamais (leçon du `BRIEF-0110` §3 :
   une caméra qui plonge à 70° ne voit jamais un dessous). **Faites-les déborder.**

⚠️ **AUCUN BUDGET DE TRIANGLES.** Décision de l'opérateur du 2026-09-08, toujours en vigueur :
« je ne veux pas entendre parler de budget et de restriction, je veux un jeu beau ». Le corridor
rend à 1,5–5,1 ms sur les 16,67 d'une image à 60 Hz. **Rapportez les comptes, ne les contraignez
pas.** Le voisin immédiat en a 1 756 pour une surface deux fois plus petite.

⚠️ **CE QUI RESTE VRAI ET N'EST PAS UN BUDGET** : à 45,8 px/m un détail de 3 cm fait 1,4 pixel.
Ne le payez pas parce que personne ne le verra — pas parce qu'il coûte.

## Texture (ADR-0028) / Animation (ADR-0046 §6)

**Aucune image nouvelle.** Les quatre cartes `ambry_hull_*` existent, sont posées et fonctionnent :
le manque est du relief, pas de la peau. Si la géométrie nouvelle a besoin d'un slot, réutilisez
les huit déjà déclarés — `AA_Hull_Ambry` pour ce qui appartient à l'avant-poste, `AA_Hull`
anthracite pour ce qui appartient au vaisseau (les deux colliers de greffe et le pas d'appontage
gardent volontairement l'anthracite : c'est leur valeur SOMBRE qui fait lire le pas).

⚠️ **Aucune face `AA_Emissive_Engine` sur Ambry**, comme aujourd'hui : l'absence de magenta est ce
qui dit qu'elle n'est pas de ce vaisseau.

**Géométrie figée.** Ambry n'a pas d'animation et n'en prend pas.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_long_cortege.py` | `build_ambry()` retravaillée |
| `assets/imported/models/backgrounds/long_cortege.glb` | le corridor |
| `docs/forge/output/BRIEF-0114-report.md` | triangles par slot, relief obtenu, hauteur consommée |
| `docs/forge/output/BRIEF-0114-planche.png` | avant/après **au cadrage du jeu**, Ambry en place |

## Critères d'acceptation

- [ ] **Rien au-dessus de `−3,20`**, mesuré sur le binaire. La marge actuelle est de 0,33 m.
- [ ] **Les quatre zones se distinguent à l'œil** sur la capture : greffe, habitation, serre,
      antenne. C'est le critère principal — pas « il y a plus de matière », mais « on voit un
      lieu, et il a des parties ».
- [ ] **Les béquilles se voient depuis la caméra du jeu**, ou elles sont retirées et le rapport
      le dit. Une idée qu'on ne voit pas n'est pas une idée livrée.
- [ ] **Le contraste local d'Ambry est mesuré avant/après**, au même cadrage, dans les mêmes
      fenêtres de 16 px (référence : 17,4 aujourd'hui, contre 6,7 pour le bordé voisin).
- [ ] **La valeur claire est conservée** : la luminance moyenne d'Ambry ne descend pas sous
      130 (elle est à 165). C'est une décision de l'opérateur, pas une préférence.
- [ ] ⚠️ **LE CADRE** : Ambry est dans le plan de vol, donc **règle A** uniquement. Rien ne doit
      sortir par le haut de l'image — projection de `GameplayPlane.screen_y_of()`, et le banc
      `test_the_front_edge_of_ambry_is_read_from_the_hull` doit rester vert : **le bord avant
      reste à `s = 446,5 ± 1`**, sinon la révélation de Lyra se déclenche au mauvais instant.
- [ ] **Les harnais du corridor restent verts** — tourelles, ponts, nœuds, les douze repères de
      conduite, les cinq du complexe, l'emprise de garde d'Ambry.
- [ ] **Déterminisme** : trois exécutions, zéro octet divergent.
- [ ] **Les comptes sont RAPPORTÉS, jamais contraints.**
- [ ] **Rendu et REGARDÉ à la caméra du jeu** (`ADR-0006`), avant/après au même cadrage.

## Hors périmètre

- **Le code de jeu.** La révélation de Lyra est déjà recalée : elle part quand Ambry entre dans le
  cadre (commit `b2cd87d`), et non plus 51 m trop tôt.
- **La valeur, la couleur, l'absence de magenta, l'état INTACT** : décidés, voir plus haut.
- **Le complexe industriel du tronçon 5**, la poupe, le reste du bordé.
