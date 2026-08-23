# ADR-0022 — Un ennemi peut connaître le joueur, mais pas n'importe lequel

- **Date** : 2026-08-23
- **Statut** : accepté
- **Complète** : `ADR-0015` (le bestiaire catalogue des coques, pas des ennemis), spec §11.
- **Ne touche pas** : `ADR-0008` (pipeline 3D), le contrat de pooling (spec §26.1), qui sortent
  tous deux renforcés.

## Contexte

Le bestiaire livré comptait **neuf profils pour deux coques**, et un seul axe de variété : la
courbe. `EnemyPath` est une bibliothèque de fonctions **pures** `(âge, point de spawn) → position`,
et cette pureté n'est pas un détail d'implémentation — c'est ce qui rend vrais trois invariants du
projet :

- **le pooling est sûr** : une instance réactivée repart de son spawn sans traîner l'état de la
  précédente, puisque sa position ne dépend que de son âge ;
- **la forme ne dépend pas du pas de temps** : rien ne s'accumule ;
- **tout se teste en headless**, sans arbre de scène ni joueur — `tests/unit/test_enemy_path.gd`
  porte quatre contrats génériques qu'une trajectoire neuve hérite gratuitement.

Le tir, lui, n'avait aucun axe du tout : `EnemyController._update_fire()` savait tirer **une** balle
**droit vers le bas** depuis `Muzzle_C`, et rien d'autre. Les trois motifs du `BossController`
(`RADIAL`, `AIMED_SPREAD`, `FAN`) existaient mais **inline**, inaccessibles aux unités de vague.

L'opérateur demande de la variété de comportement, et son exemple est précis :

> « on pourrait imaginer que les mines sont assez linéaires dans leur déplacement — en fait c'est
> nous qui avançons — et quand on s'approche il y a des mines qui réagissent, et si on s'approche
> trop elles explosent ; d'autres qui feraient un pouvoir d'attraction avec la génération d'un
> micro trou noir quand on s'approche trop »

Aucune de ces deux unités n'est exprimable dans le modèle existant. Toutes deux ont besoin de la
**distance au joueur**, que le contrat de pureté interdit par construction. Cinq des sept familles
de la spec §11.1 sont dans le même cas : la sangsue poursuit, le porteur de bouclier protège ses
voisins, la tourelle vise.

## Décision

**Les ennemis peuvent connaître le joueur — et la frontière de pureté est déplacée, pas supprimée.**

### 1. Trois axes orthogonaux dans `EnemyData`, tous append-only

| Axe | Enum | Bibliothèque | Répond à |
|---|---|---|---|
| Trajectoire | `Path` *(existant)* | `EnemyPath` | où va la coque |
| Tir | `Fire { SINGLE, NONE, FAN, AIMED, RADIAL }` | `EnemyFire` | où part le coup |
| Effet non-projectile | `Effect { NONE, GRAVITY_WELL }` | `EnemyController` | ce qu'elle fait qui n'est pas une balle |

**L'indice 0 de chaque enum reproduit le comportement d'avant** (`SINGLE`, `NONE`). Les neuf `.tres`
livrés ne portent pas ces champs, héritent donc de l'indice 0, et sont strictement inchangés — la
non-régression n'est pas une intention, c'est une propriété de la sérialisation.

⚠️ **Toute valeur s'APPEND en fin de liste.** Les `.tres` sérialisent l'indice numérique : une
insertion au milieu réaffecterait silencieusement le comportement de toutes les unités existantes.

### 2. La ligne exacte : ce qui reste pur, ce qui voit

**`EnemyPath` ne reçoit jamais la position du joueur.** Pas d'exception, pas de surcharge, pas de
paramètre optionnel. Les quatre contrats testés restent vrais pour toute trajectoire, présente ou
future — y compris `DRIFT`, ajoutée ici, dont la signature est une **absence** : elle ne manœuvre
pas, c'est le joueur qui avance.

**Ce qui voit le joueur est cantonné à trois endroits nommés**, tous dans `EnemyController` :
`_update_reaction()`, la visée d'`EnemyFire.AIMED`, et `_pull_player()`. Le joueur est **injecté**
par `WaveSpawner` (`@export var player_path`), reste **facultatif**, et vaut `null` dans tous les
tests — auquel cas la distance est l'infini et aucune menace ne se déclenche.

**La menace de proximité est elle-même pure** : `EnemyReaction` est une machine à états sans nœud
ni état interne — `next_state(état, temps dans l'état, distance, données)`. Le contrôleur détient
l'état, la bibliothèque dit ce qui vient après. Un comportement qui dépend du joueur redevient donc
testable en headless, le test jouant le rôle du joueur qui s'approche.

### 3. Deux contrats de gameplay, inscrits dans le code et dans les tests

**Le télégraphe ne ment jamais.** `WINDUP → ACTIVE` est irréversible : une fois engagée, l'unité
part, même si le joueur s'enfuit à l'autre bout du champ. Un télégraphe annulable en reculant
apprend au joueur à ignorer les télégraphes, et c'est toute la lisibilité du jeu (spec §11.2, §5.3)
qui s'écroule avec. `validate()` impose la fenêtre de la spec : **300 à 800 ms**.

**Se vider ne rapporte rien.** Une unité à usage unique (`rearm_time = 0`) quitte le champ sans
émettre `destroyed` : ni score, ni explosion de mise à mort. Abattre une mine à distance paie ;
la laisser se déclencher ne paie pas. Si les deux payaient, il n'y aurait plus de décision à prendre
— et la prudence, qui est la seule contre-mesure d'un champ de mines, ne serait plus récompensée.

### 4. `add_pull()` s'ajoute là où `apply_pull()` affectait

Le boss est seul : une affectation lui suffisait. Un champ de mines, non — deux puits ouverts
doivent **additionner** leurs contributions, faute de quoi le dernier appelé gagne et le joueur
traverse tranquillement un nid qui devrait l'écraser. `apply_pull()` est laissée intacte pour le
boss ; `add_pull()` est ajoutée à côté, consommée par la même remise à zéro.

L'invariant `GravityWell.leaves_room()` est **repris tel quel** et vérifié dans `validate()` : une
aspiration à laquelle le chasseur ne peut rien opposer n'est plus un danger, c'est une cinématique.
Sur une mine c'est pire que sur le boss — le joueur a **choisi** de s'approcher, il doit pouvoir
choisir de repartir.

### 5. Les coques respirent

`EnemyVitals` donne un régime à l'émissif : respiration à ±10 % au repos, montée en énergie et
accélération du battement avec la menace. Le matériau est **dupliqué par instance** — `AA_Emissive_Engine`
porte le même nom sur toutes les coques du jeu, le muter en place ferait battre le chasseur du
joueur au rythme d'une mine (même piège, même parade que `CitadelLife` et `HullDetail`). Le déphasage
d'une instance à l'autre suit un pas irrationnel plutôt qu'un tirage aléatoire : deux coques voisines
sont toujours déphasées, et la scène reste reproductible d'un lancement à l'autre.

## Conséquences

- Les cinq familles restantes de la spec §11.1 deviennent exprimables **sans nouveau script
  d'ennemi** : `EnemyController` reste la base de composition unique, et « ajouter un ennemi » reste
  « écrire une Resource ».
- Une unité peut désormais menacer **sans projectile** : `validate()` n'exige un `ProjectileData`
  que si elle tire.
- Un troisième axe de déplacement (`Motion { PATH, HOMING }`, pour la sangsue) est **réservé mais
  pas écrit** : il arrivera avec son premier utilisateur, pas avant. Une poursuite ne peut pas être
  une fonction pure de l'âge ; elle sera testée en lui injectant une suite scriptée de positions
  joueur, ce qui la laisse déterministe en headless.
- Coût de vérification : 37 tests neufs, dont les gardes de `validate()` **mises en échec avant
  d'être validées** — une règle qu'on n'a jamais vue refuser une donnée ne prouve rien.
- Une unité réactive ne tire plus à l'horloge. `fire_interval` reste lu par les unités ordinaires
  et ignoré par les autres : ce n'est pas une donnée morte, c'est une donnée hors sujet.

## Alternatives écartées

**Passer la position du joueur à `EnemyPath`.** La solution la plus courte, et la plus chère : elle
invalide d'un coup les quatre contrats génériques de `test_enemy_path.gd`, rend le pooling incorrect
(une instance réactivée hériterait d'une trajectoire dépendant d'un historique) et rend la forme
dépendante du pas de temps. On aurait payé ça pour deux familles sur sept.

**Un script par famille d'ennemi.** C'est de l'héritage là où le projet impose la composition
(spec §31), et cela multiplie par sept la surface où un bug de pooling peut se loger — précisément
ce que `_set_active()` centralise aujourd'hui.

**Écrire d'abord l'`EncounterDirector` data-driven** (backlog P1). Plus gros chantier, et il ne
répond pas à la question : un director orchestre *quand* des ennemis arrivent, pas *ce qu'ils font*.
La variété demandée est un problème d'unités, pas de timeline.

**Un enum `Reaction { NONE, PROXIMITY }`.** Un axe de plus pour dire ce que `trigger_radius > 0` dit
déjà. Écarté au titre de l'obligation §0 n°9 : éviter les architectures surdimensionnées.
