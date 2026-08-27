# ADR-0030 — La fenêtre de vulnérabilité vit DANS la plongée

- **Date** : 2026-08-27
- **Statut** : accepté (décision de l'opérateur, sur spécification « Reactor Chamber »)
- **Complète** : `ADR-0025` (l'arène dédiée) et `ADR-0026` (le plafond par plongée), qui
  sortent tous deux **intacts**.
- **Ne touche pas** : la structure en trois cycles, le contrat de pooling, la durée cible de
  l'arc (spec §5.1).

## Contexte

Playtest du 2026-08-27, puis spécification et planche de l'opérateur :

> « Le joueur entre dans le noyau puis se retrouve face à une cible quasiment fixe. »
>
> « **Le décor crée le gameplay.** On évite donc de remplir simplement l'écran avec
> davantage d'ennemis. »

La session avait mesuré le même défaut le matin : la cible n'était pas seulement fixe, elle
était **invisible** — son halo se posait sur le cœur du boss, resté **dehors**.

La spec propose une boucle `PRESSION → POSITIONNEMENT → OUVERTURE → FENÊTRE → FERMETURE` de
8 à 12 s, avec un réacteur qui aurait **sa propre santé** (100 → 70 → 35 %).

## La décision

**La fenêtre de vulnérabilité vit DANS la plongée. Le réacteur n'a pas de santé propre.**

Deux lectures étaient possibles, et l'opérateur a tranché pour la première :

| | (a) **retenue** — la fenêtre dans la plongée | (b) écartée — le noyau devient une phase |
|---|---|---|
| Structure | la plongée dure le temps d'une boucle de puzzle | le noyau a ses trois paliers de santé |
| Durée ajoutée | **+18 s** sur l'arc | +2 à 3 min |
| `ADR-0026` | **intact** | abrogé |

⚠️ **Pourquoi (b) a été écartée.** `ADR-0026` existe parce que trois playtests avaient donné
trois comptes de cycles différents (3 à 6) pour le même réglage : le plafond d'un tiers par
plongée rend les trois cycles vrais **par construction et non par calibrage**. Donner au
réacteur sa propre santé aurait rouvert exactement ce problème, contre un gain de structure
que le puzzle apporte déjà.

## Ce qui en découle

### La plongée passe de 5 s à 11 s, et le chiffre n'est pas un goût

Le quota d'une plongée est de **800** dégâts, pour **884** atteignables en 5 s — dix pour cent
de marge. Un blindage ouvert **45 %** du temps ferait tomber les atteignables à **398** : *le
combat ne pourrait plus finir en trois cycles*.

Onze secondes rétablissent la marge, et c'est aussi la durée d'une boucle complète du puzzle
(8-12 s dans la spec).

⚠️ **C'est la sortie de SECOURS, pas la durée réelle.** Depuis le playtest, le quota rempli
éjecte immédiatement : un joueur qui trouve ses corridors sort bien avant.

### La part d'ouverture entre dans l'invariant de portée

`ring_occupancy` est **nommée et validée** : sans elle, on aurait armé le réacteur d'un
blindage tout en continuant de calculer les dégâts atteignables comme s'il n'y en avait pas.
C'est le calibrage silencieux qu'`ADR-0024` a coûté au projet.

**0,45 est une ESTIMATION**, et elle est écrite comme telle. Un joueur immobile n'aurait que
~13 % (le produit des deux couvertures d'anneaux). À mesurer en jouant.

### Le joueur n'attend jamais

Réglage livré : deux anneaux en **sens contraires**, 3 ouvertures de 46° à +26 °/s et
2 ouvertures de 62° à −17 °/s. **Simulé avant d'être écrit**, sur deux minutes : un corridor
existe **100 % du temps** quelque part sur le cercle, verrou le plus long **0,00 s**.

⚠️ C'est le point de conception le plus important de cette phase. Une phase où l'on **patiente**
devant un blindage fermé serait le défaut qu'on corrigeait, en pire. La difficulté est d'**aller**
au corridor, pas d'attendre qu'il s'ouvre.

⚠️ Et c'est **`ADR-0029` à l'envers** : là, il fallait des périodes qui ne retombent **jamais**
en rythme, pour que l'œil ne repère pas la boucle. Ici il faut qu'elles se croisent **souvent**.
Deux problèmes opposés, deux réglages opposés, deux gardes opposées.

### Une seule source pour l'image et pour la règle

Les arcs du décor se déduisent des **mêmes `ReactorRing`** que la mécanique, et tournent sur la
**même horloge** (`combat_age()`). Deux sources auraient fini par diverger — et le joueur aurait
tiré dans un blindage plein en croyant viser un trou, ce qui est le seul défaut que cette phase
ne peut pas se permettre.

## Conséquences

**Acquis.** La cible fixe devient un puzzle de positionnement, pour **0 ms de GPU mesurable**
(6,45 ms/image sur Quadro T1000, contre 7,1 à 12,6 relevés sur la même arène avant le chantier).

**Coûts assumés.** +18 s sur l'arc. Une estimation (`ring_occupancy`) qui reste à mesurer.

**Ce qui reste ouvert, et qu'il faut dire.**

- ⚠️ **Les tirs traversent visuellement un blindage fermé.** Le verrou est logique
  (`BulletTarget.enabled`), pas physique. Le projet a déjà nommé ce défaut sur le Harvester —
  « tirer dessus sans rien produire à l'écran se lit comme un défaut, pas comme une armure » —
  et y a répondu par une gerbe de déviation. Il faut la même chose ici.
- ⚠️ **Les anneaux se lisent comme de la peinture au sol** : posés sous le plan de jeu pour ne
  pas masquer les balles, ils passent sous les nervures du décor livré. Une hauteur à reprendre.
- Les lots 2 à 5 du plan (lasers balayants, nodes, rails, décor animé) restent entiers.
