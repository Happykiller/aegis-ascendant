# Le plan de VOL n'est pas le plan VISIBLE — et la confusion a coûté quatre défauts en un jour

**2026-09-06.** Quatre défauts distincts, rapportés ou trouvés le même jour, tous produits par la
même erreur : avoir pris `GameplayPlane.BOUNDS` pour ce que l'écran montre.

| Ce que c'est | Valeur | Ce que ça décide |
|---|---|---|
| `GameplayPlane.BOUNDS` | `y` de **−8 à +8**, `x` de **−14 à +14** | où le CHASSEUR a le droit d'aller |
| Le cadre de la caméra | `y` de **−7,72 à +12,28**, `\|x\| ≤ 20,37** (16:9) | ce que le JOUEUR voit |

**Il reste donc 4,28 unités visibles au-dessus de l'arène** — plus d'un cinquième de la hauteur
d'écran — et une marge latérale de 6,4. C'est le couloir d'entrée. Il existait depuis toujours ;
personne ne s'en servait, parce que personne ne l'avait mesuré.

## Les quatre défauts

1. **Des tourelles visibles et intouchables.** « J'essaye de tirer dessus, elle est visible,
   pourtant je ne la touche pas » (opérateur, capture à l'appui). Chaque famille de pièce avait sa
   fenêtre de tir, choisie sur sa **taille apparente** : ±7 pour une batterie légère, ±10 pour une
   tourelle standard. Soit **5,3 unités — 26 % de la hauteur d'écran** — où la pièce se voit, vise
   ostensiblement le joueur (une tourelle se tourne vers lui sur le DOUBLE de sa portée de tir) et
   n'encaisse rien.
2. **Des ennemis qui éclosent en plein cadre.** Les **cent quinze** points de naissance du jeu
   étaient dans le cadre : 108 à `y = +9,5` pour un bord haut à +12,28, et sept passes de
   mitraillage à `|x| = 16` pour un bord latéral à 20,37.
3. **Les balles du joueur s'éteignaient à l'écran.** Coupe à `y = 13,0`, soit **0,72 unité**
   au-dessus du bord du cadre. Défaut nommé par l'opérateur dès le 2026-08-27 — « mes tirs ne vont
   pas jusqu'au bout de l'écran » — et corrigé à l'époque en se calant sur la ligne d'apparition
   des ennemis, qui ne mesurait le haut de l'écran que **tant que les coques naissaient dedans**.
4. **Des ancrages de poupe posés hors de portée** (même jour, LOT 1) : à `y` de plan 9,6 quand le
   joueur ne monte qu'à 8, sur la SEULE cible de la phase. Trouvé en capture, pas en test.

## ⚠️ Et naître hors cadre était IMPOSSIBLE — les deux moitiés vont ensemble

Le couperet de despawn d'`EnemyController` tombait à `y = +11` (`BOUNDS.end.y + ESCAPE_MARGIN`),
c'est-à-dire **sous le bord haut de l'écran**. Une coque posée hors cadre mourait à sa première
trame, **sans une erreur ni une ligne de journal**. Aucun auteur de vague ne pouvait faire mieux.

C'est la forme la plus vicieuse de ce défaut : une règle de sortie qui interdit une règle d'entrée.
Chercher l'un sans l'autre donne un correctif qui s'annule tout seul.

Corollaire : **un seul `DESPAWN_MARGIN` ne peut pas garder trois bords.** Le bas est une SORTIE
(marge serrée, on recycle vite) ; le haut et les côtés sont des ENTRÉES (marge large, on laisse
entrer). Trois questions différentes, trois constantes.

## Ce qu'il faut faire

**La question « est-ce que ça se voit ? » a une réponse mesurée depuis ce jour :**

```gdscript
GameplayPlane.visible_frame(camera_transform, fov_deg)  # -> Rect2 du plan visible
```

Elle prend la caméra en paramètre, exprès. **Un nombre recopié dans un commentaire meurt au
premier déplacement de caméra, en silence.** Les gardes de ce dépôt relisent donc la caméra dans
la scène (`cortege.tscn`, `graybox.tscn` — elles sont identiques) plutôt que de citer 12,28.

Trois gardes existent et doivent le rester :

- `test_the_target_window_covers_what_the_camera_shows` — aucune fenêtre de tir sous le cadre ;
- `test_no_enemy_is_born_inside_the_frame` + `test_the_despawn_box_lets_an_offscreen_birth_live` ;
- `test_a_bolt_outlives_the_screen_and_reaches_what_appears_on_it`.

## Deux pièges de méthode, payés le même jour

- **Une règle calée sur un proxy meurt quand le proxy bouge.** La coupe des balles se calait sur la
  ligne d'apparition des ennemis. Le jour où celle-ci est sortie du cadre, la règle est devenue
  absurde (elle exigeait une coupe à 17,5 pour un défaut qui se juge à 12,28). Caler sur la CHOSE,
  pas sur ce qui lui ressemblait.
- **Un témoin recalé peut devenir vert ET VIDE.** `test_a_bullet_born_above_the_cull_line...`
  posait sa bouche à `y = 14,5` — les plaques du Léviathan — et affirmait qu'elle était hors de la
  coupe. En remontant la coupe à 15,5, cette première assertion est devenue fausse : le test
  passait toujours, mais ne testait plus rien. Le point d'essai se **calcule** depuis la constante
  courante, il ne se recopie pas.

## ⚠️ Et le cadre borne aussi le DÉCOR — deuxième famille, 2026-09-08

Tout ce qui précède parle de la **couche de vol** : où le chasseur va, où les ennemis naissent, où
les balles meurent. Le décor posé sur une coque obéit à la même caméra et **personne ne l'avait
écrit**. Coût : deux allers-retours de forge, `BRIEF-0109` et `BRIEF-0112`.

Une pièce de décor a **trois** enveloppes, pas deux, et seules les deux premières étaient
documentées :

| Enveloppe | Ce qu'elle dit | Où elle est écrite |
|---|---|---|
| `BUILD_CEILING_Y = −3,20` | la pièce ne traverse pas la couche de vol | briefs de forge |
| le plan de vol (`\|x\| ≤ 14`) | au-delà, le chasseur n'ira jamais | `BOUNDS` |
| **le cadre** | **quelqu'un la regarde-t-il ?** | ⚠️ nulle part, jusqu'à ce jour |

### La contrainte est contre-intuitive : plus une pièce est HAUTE, plus elle sort TÔT

C'est ce qui a piégé deux lots de suite. Le `BRIEF-0112` a raisonné juste : le plan de vol
s'arrête à `|x| = 14`, donc au-delà une pièce peut monter sans que le joueur la traverse. Il a
appelé ça « le vrai gain » et il avait tort — les tours posées là avaient leur **sommet à
−142 px**, au-dessus du bord de l'image.

L'étagère de rive est 3,80 m plus haut que le plateau du massif ; sa fenêtre visible est donc
**4,7 m plus courte**. La hauteur d'assise que la règle gagne, le cadre la reprend.

```
   assise −8,40 (plateau du massif)   pièce visible jusqu'à z ≥ −10,38
   assise −4,60 (étagère de rive)     pièce visible jusqu'à z ≥  −5,69
```

### La recette, et elle ne se calibre pas

```gdscript
GameplayPlane.screen_y_of(camera, fov_deg, point_monde, hauteur_px)   # 0 = haut de l'écran
```

Il reste à savoir **où la pièce se trouve quand on la regarde**. Pour la poupe du niveau 2, c'est
exact et non empirique : le survol s'arrête à `LEAD_IN + station − hold`, le décor porte
`parcouru − LEAD_IN`, la poupe est posée à `−station` dessus. **Les trois termes se simplifient :
la poupe au repos est à `z = −hold_plane_y`.** J'ai d'abord calibré ce nombre sur des pixels lus à
la main (−7,42, 43 px d'erreur) avant de m'apercevoir qu'il se dérivait (−6,47).

⚠️ **Un `Transform3D` de `.tscn` se sérialise par LIGNES**, pas par colonnes. L'autre lecture
donne une caméra qui regarde le ciel — et elle ne lève aucune erreur, elle rend juste « hors
champ » pour tout. Deux d'entre nous s'y sont fait prendre le même jour.

### Le chiffre qui condamne le rendu studio « à la caméra du jeu »

Même paire de rendus avant/après, deux cadrages, mesurée sur les pixels :

- au cadrage que la forge utilisait pour se relire : **22 050 pixels** changent ;
- au cadrage réel du jeu : **110**, c'est-à-dire du bruit d'échantillonnage.

Les deux tours occupaient un quart de la planche de contrôle et **zéro pixel** dans la partie. Une
planche studio ne porte pas la STATION de la pièce ; elle montre donc ce que le jeu ne montrera
pas. `ADR-0006` dit « rendu et regardé » — il faut lire « regardé **là où le joueur regarde** ».

### La sortie n'est pas toujours de déplacer

Quatre voies ont été explorées pour rattraper les deux tours, et **trois se sont fermées par la
mesure** : la coque ne descend pas assez bas au bord (il aurait fallu creuser un puits de 3,6 m),
les places libres du plateau *sont* les canaux d'échappement, et avancer la rive coûtait une
plate-forme de tourelle — un canon échangé contre du décor. La réponse retenue a été **deux
pièces au lieu de quatre**. Deux pièces qu'on voit valent mieux que quatre dont la moitié est
au-dessus du cadre.

## Voir aussi

- [Une cote se lit sur l'asset livré](pratique-la-cote-vient-de-l-asset.md)
- [Juger une image en la mesurant](pratique-juger-une-image-en-la-mesurant.md)
