# ADR-0021 — Le Pale Leviathan devient cyclique, et on entre dans son noyau

- **Date** : 2026-08-23
- **Statut** : accepté (décision du propriétaire, après playtest)
- **Amende / supersede** : `ADR-0018` (quatre phases, « rien ne repousse »), `ADR-0020`
  (deux phases linéaires), spec §7 et §12.

## Contexte

`ADR-0020`, pris le matin même, avait ramené le combat de quatre phases à deux et corrigé
une jauge qui mentait. Le playtest qui a suivi a été gagné — l'arc complet a été bouclé pour
la première fois — et le verdict fut malgré tout sans appel :

> « C'est extrêmement lancinant. Le boss va de gauche à droite et fait des vagues de
> bullets, on a les quatre plaques qui tournent autour, qu'on arrose sans vraiment trop
> faire gaffe en attendant qu'elles disparaissent. Les espèces de tentacules, antennes —
> je ne vois pas à quoi elles servent, je ne comprends pas. Et après, quand toutes les
> plaques sont détruites, je comprends difficilement, puisque c'est moi le concepteur,
> qu'il faut aller dans le noyau pour tirer. En fait, on ne voit pas, on ne comprend pas. »

Trois griefs, trois natures différentes :

1. **Du temps sans décision.** Une seule plaque était vulnérable (correctif d'ADR-0020),
   mais elle l'était en permanence : on arrose le boss, ça touche ce qui est exposé, et il
   n'y a rien à lire ni à choisir. Vingt-deux secondes de ce régime.
2. **Des pièces sans rôle.** Épines et nœuds ne servaient plus à rien depuis ADR-0020, sinon
   à tomber. Un objet qui bouge sans qu'on sache pourquoi n'est pas du décor, c'est du bruit.
3. **Une cible qu'il fallait deviner.** Le cœur était exposé « en permanence » — mais comme
   une hitbox invisible au centre d'un boss vu de loin. Le concepteur lui-même ne savait pas
   qu'il fallait tirer là.

Le propriétaire a proposé les trois remèdes, et ils sont retenus tels quels : que les épines
**tirent des lasers** et tombent une par plaque brisée ; qu'on **entre dans le noyau** avec
un zoom, comme à l'appontage, pour y arroser un flux d'énergie central pendant un temps
court avant d'être éjecté ; et que le combat **enchaîne ces deux temps en cycles**, avec
beaucoup moins de points de vie sur les plaques.

## Décision

**Trois cycles, deux temps par cycle, ~40 s.**

```
CYCLE 1   4 plaques, 4 tourelles-épines   ~8 s   →   plongée ~7,4 s
CYCLE 2   3 plaques, 3 tourelles          ~6 s   →   plongée ~7,4 s
CYCLE 3   2 plaques, 2 tourelles          ~4 s   →   plongée finale → mort
```

- **Les plaques tombent vite** : 1270 → **460 PV**. Une plaque cède toutes les ~2 s, et la
  première salve d'armure passe de ~22 s à ~8 s. C'est la réponse directe au « lancinant ».
- **Une seule plaque encaisse à la fois**, celle qui brille (acquis d'ADR-0020, conservé).
- **Les épines sont des tourelles laser télégraphiées** (`Beam`, la même grammaire que le
  canon du Harvester : télégraphe fin, faisceau, récupération). **Chaque plaque brisée en
  éteint une.** Casser une plaque retire une menace qu'on peut nommer.
- **On entre dans le noyau** : la coquille s'écarte, le chasseur est aspiré vers l'ouverture
  en autopilote, la caméra glisse jusqu'à ce que le noyau remplisse le cadre, et le **flux
  d'énergie** occupe le centre de l'écran. ~5 s de tir, puis éjection.
- **L'armure revient, amoindrie.** Une plaque et une tourelle de moins à chaque cycle. Le
  boss ne se répare pas : il se répare **de plus en plus mal**, et ça se lit sur sa silhouette.
- **L'aspiration survit comme pression**, plus comme phase : elle accompagne l'entrée, elle
  ne prend jamais les commandes.
- Le boss **s'immobilise** pendant la plongée (`drive_toward` à vitesse nulle) : un noyau qui
  dérive pendant que le chasseur est dedans emporterait le joueur hors du cadre.

### « Rien ne repousse » est abandonné

C'était le pilier d'`ADR-0018`, ce qui distinguait le Leviathan du Harvester (un verrou qui
se rouvre). Il tombe : l'armure revient. Ce que la nouvelle structure garde du pilier, c'est
**l'irréversibilité de la dégradation** — une plaque de moins à chaque tour, jamais une de
plus. Le boss ne revient jamais à son état initial.

### Le boss n'avance pas sur un compteur

Trois cycles, c'est ce qu'il faut **si le joueur tire correctement** : le flux vaut 5300 PV,
soit 1767 par plongée, contre 1785 atteignables en 5 s à 0,85 d'occupation. Serré exprès. Si
le joueur rate ses passages, le flux survit et un cycle de plus s'ouvre, au plancher de deux
plaques. Un boss qui mourrait au troisième cycle quoi qu'il arrive avancerait sur un
compteur, pas sur ce que le joueur a fait.

## Les invariants qui gardent tout ça

`LeviathanTuning.validate()` refuse désormais :

- un **arc plus étroit que l'écart entre plaques**, à *chaque* cycle. Quatre plaques sont
  espacées de 90°, trois de 120°, deux de 180° : un arc fixe marche au premier cycle et
  laisse, dès le deuxième, des instants où aucune plaque n'est atteignable. D'où
  `effective_arc_deg()`, qui élargit l'arc à mesure que le boss s'affaiblit ;
- une **durée totale** hors de 40 ± 10 s. Le garde-fou qui a manqué deux fois ;
- un **déséquilibre entre les deux temps** (chacun doit porter 25 à 75 % du combat) ;
- un **flux mal dimensionné** : trop mou, le boss meurt au premier plongeon et les cycles ne
  servent à rien ; trop dur, le joueur repart pour un tour de plus sans comprendre pourquoi ;
- un **télégraphe de laser plus court que la moitié du tir** — un avertissement qui se lit
  comme un clignotement n'en est pas un.

## Trois pièges rencontrés en chemin, et consignés

- **Un `Beam` enfant du module subit la transformation du boss deux fois.** `Beam.aim()` pose
  le faisceau en coordonnées monde ; Godot remonte l'arbre jusqu'au premier ancêtre `Node3D`.
  Symptôme : aucun laser à l'écran, aucune erreur nulle part. Correctif : `top_level = true`.
  ⚠️ `HarvesterCombat` attache ses faisceaux exactement de la même façon — **à vérifier**.
- **Une sphère intérieure en `CULL_DISABLED` referme le cadre.** Avec les faces retournées,
  seules les faces internes doivent être rendues, sinon la coque de la sphère masque tout :
  vu en capture, un disque plein écran, plus de boss, plus de joueur.
- **Le chasseur disparaît dans la coque.** À hauteur nulle il est géométriquement *dans* le
  boss. D'où `plane_lift`, purement visuel : `plane_position` ne bouge pas, donc ni les
  collisions ni les tirs ne changent.

## Ce qui reste à juger, et par qui

Le ressenti de durée, la lisibilité des cycles et l'alignement du halo ne se jugent **pas** à
la capture. C'est la leçon d'ADR-0019 et d'ADR-0020, et elle vaut une troisième fois.
