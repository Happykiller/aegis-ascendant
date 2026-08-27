---
titre: Level design — l'espace, les repères, et la reprise après la mort
type: reference
statut: actif
maj: 2026-08-27
---

# Level design

[`03-niveau-et-rythme.md`](03-niveau-et-rythme.md) traite le **temps** d'un niveau : ouvrir,
développer, intensifier, souffler. Celle-ci traite son **espace** — la taille du terrain, les
repères qu'on y pose, la manière dont on l'écrit, et ce qui se passe quand le joueur y meurt.

## Ce que le genre dit

### Le rapport vaisseau/écran est un choix de conception, pas un choix d'art

> Un **petit** personnage sur un **grand** écran accueille un jeu **rapide** et beaucoup d'éléments
> simultanés ; un personnage qui **remplit** une large part de l'écran autorise moins de sprites et
> laisse **moins de temps pour anticiper** les attaques.

C'est le paramètre qui commande tout le reste : densité possible, vitesse des projectiles, marge
d'esquive, taille des télégraphes.

### Un niveau révèle, puis combine

> Un bon *stage design* est censé **révéler toutes les mécaniques** disponibles au joueur, puis le
> mettre au défi de les **assembler** dans des situations variées, à mesure que le jeu durcit.

Et le mouvement des ennemis fait partie de la conception du niveau, pas de celle de l'ennemi : la
créativité des trajectoires est citée comme le premier levier de variété d'une étape.

### Le décor sert la mémorisation

> La clé pour gagner à un shmup est la **mémorisation** ; créer un fond **mémorisable** aide à
> orienter le joueur sur l'endroit **exact** où il se trouve dans le niveau.

Le décor n'est donc pas une toile de fond : c'est une **barre de progression implicite**. Un fond
qui se répète sans repère prive le joueur de la seule réponse à « où en suis-je ? ».

### Le niveau fait bouger, ou il ne sert à rien

> « La conception de chaque niveau est structurée pour vous **donner envie de zigzaguer partout**. »

Corollaire cité dans la même source : les ennemis **hors champ** sont une faute. « Si les ennemis ne
sont pas visibles par le joueur, comment le joueur pourrait-il seulement avoir une chance ? »

Et lorsque deux patterns se superposent : « des patterns simultanés distincts doivent avoir des
balles **d'apparence différente** » — sinon le joueur ne peut pas les séparer sous pression.

### Écrire un niveau : une file d'actions, pas des minuteurs

L'approche recommandée est une **file** d'actions — `SpawnEnemy(type, x, y)`, `Wait(frames)` — qui
permet de **remanier les formations** en les déplaçant dans la liste. C'est la même exigence que la
spec §11.3 (« des données de timeline, non une succession de délais dispersés dans le code »).

### La reprise après la mort : deux écoles, dont une redoutée

| | **Checkpoint** | **Reprise sur place** |
|---|---|---|
| Comportement | on renaît à un point fixe, **puissance remise à zéro**, bombes rechargées | on renaît là où l'on est tombé |
| Réputation | « associé à une difficulté brutale » — le *Gradius syndrome* | permissif |
| Risque | boucle de mort : trop faible pour repasser le passage qui vient de tuer | perte d'enjeu |

## Chez nous — état au 2026-08-27

### Le terrain fait 28 × 16 unités, le vaisseau 0,5

`GameplayPlane.BOUNDS` est un rectangle de **28 × 16 unités** (`scripts/gameplay/gameplay_plane.gd:12`).
La hitbox du joueur a un rayon de **0,25** — soit un diamètre de 0,5, **1,8 % de la largeur** du
terrain.

Nous sommes donc franchement dans le cas « petit vaisseau, grand écran » : beaucoup d'éléments
simultanés, projectiles lents et lisibles, temps d'anticipation long. C'est exactement ce que
demandent la spec §11.2 (« davantage de projectiles lents et lisibles ») et le pilier B — mais
c'est une **conséquence géométrique**, pas une règle écrite quelque part. ⚠️ Quiconque toucherait à
`BOUNDS` changerait la difficulté du jeu entier sans toucher à une seule valeur d'équilibrage.

### Les vagues sont déjà une file d'actions

`WaveData` / `WaveEntry` (`resources/data/`) sont littéralement la structure recommandée :
`time_offset`, `enemy_scene`, `spawn_plane_position`, `count`, `spacing`. Les entrées se
remanient en les déplaçant dans le `.tres`, sans toucher au code. La vague d'ouverture
(`resources/encounters/wave_graybox_01.tres`) compte une trentaine d'entrées, échelonnées de 0,3 s à
la fin de la phase.

⚠️ Ce n'est pas encore l'`EncounterDirector` de la spec §11.3 : la file sait **poser des ennemis**,
pas attendre une condition, synchroniser la musique, lancer une transmission ni poser un checkpoint.
Le director réel est le `graybox_root.gd`, en dur (`docs/KB/DAF/arc-de-jeu.md`).

### Les repères existent, et ils sont même outillés

`BackdropLandmark` (`scripts/vfx/backdrop_landmark.gd`) fait dériver planètes et nébuleuses derrière
le plan de jeu, avec une bande de bouclage qui les tient **hors du couloir de combat central** — la
règle de lisibilité du fond est appliquée dans le code. Le survol de lune (`MoonFlyby`, `ADR-0027`)
donne à la phase du champ d'astéroïdes **son propre décor**, ce qui est précisément le rôle de
repère décrit par le genre : on sait qu'on a changé de section parce que le ciel a changé.

⚠️ Mais ils **dérivent et bouclent** : ils disent « on est dans cette phase », pas « on en est aux
deux tiers ». La progression fine reste invisible — même constat que [`08-boucle-de-jeu.md`](08-boucle-de-jeu.md).

### Il n'y a aucun checkpoint — et c'est une troisième école

La spec §5.3 demande « des checkpoints avant l'appontage et avant le boss ». **Le mot n'apparaît
dans aucun script.** Le jeu fait autre chose : `_respawn()` remet le joueur à `(0, −5)` après
1,2 s, avec 2,0 s d'invulnérabilité, **sans perdre de puissance**, et les continues sont illimités
(spec §8.4).

C'est une reprise **sur place, sans coût**, qui évite par construction le *Gradius syndrome* — et
qui supprime aussi l'enjeu de la mort. Ce n'est ni l'une ni l'autre des deux écoles du genre :
c'est le pilier A poussé jusqu'au bout.

### Les autres points, vérifiés

| Point du genre | État réel |
|---|---|
| Ennemis hors champ | ✅ les vagues apparaissent à `y = 9,5`, au-dessus du bord haut du terrain (`y_max = 8`) : les coques **entrent** dans le champ, elles n'y surgissent pas |
| Faire zigzaguer | ✅ tenu par construction — trajectoires `WEAVE`, `ARC_CROSS`, `SERPENTINE`, `SPIRAL`, `STRAFE_RUN`… neuf courbes distinctes |
| Balles distinctes pour patterns simultanés | ⚠️ **non vérifié** : nos `ProjectileData` diffèrent par unité, mais rien ne garantit que **deux patterns simultanés** emploient des projectiles d'apparence différente. Le champ d'astéroïdes superpose trois unités — c'est là que ça se joue |
| Révéler puis combiner | ✅ c'est explicitement le principe du champ d'astéroïdes : trois unités qui **se superposent** au lieu de se succéder |

## L'écart, et ce qu'on en fait

**Tenu.** Le format de données des vagues, l'entrée visible des ennemis, la variété des
trajectoires, les repères de fond hors du couloir central. Ce sont quatre choses que le genre
signale comme fautives quand elles manquent, et aucune ne manque.

**Assumé, mais à écrire quelque part.** Le rapport 0,5 / 28 unités est un **paramètre d'équilibrage
majeur déguisé en constante technique**. Cette page est désormais l'endroit où c'est dit ; si
`BOUNDS` bouge un jour, c'est un ADR, pas un ajustement.

**Écart franc avec la spec, à trancher.** Les checkpoints de §5.3 n'existent pas et **rien ne les
réclame** : la reprise sur place fait le travail, mieux et plus simplement. Le plus honnête est
probablement de **retirer la ligne de la spec** plutôt que d'implémenter un mécanisme dont le jeu
n'a pas besoin — mais la spec est source de vérité et la bible ne la modifie pas.

**Vérification gratuite, à faire en jouant** : dans le champ d'astéroïdes, les projectiles des trois
unités simultanées se distinguent-ils les uns des autres ? C'est une question de dix secondes de
jeu et c'est la seule ligne « non vérifiée » de cette page.

## Sources

- [What does "stage design" mean to you?](https://shmups.system11.org/viewtopic.php?f=1&t=58682) — shmups.system11.org : révéler puis combiner, la créativité des trajectoires. ⚠️ Forum consulté via résumé de recherche (403 aux robots) — à relire à la main si le sujet est repris.
- [Pixelblog 31 — Shmup Design Part 1](https://www.slynyrd.com/blog/2020/12/14/pixelblog-31-shmup-sprite-design) — SLYNYRD : le rapport vaisseau/écran, les repères de fond et la mémorisation.
- [The Anatomy of a Shmup](http://shmuptheory.blogspot.com/2010/02/anatomy-of-shmup.html) — SHMUPtheory : le zigzag, les ennemis hors champ, les balles d'apparence distincte pour des patterns simultanés.
- [Shmup Level Design/Scripting](https://gamedev.net/forums/topic/661568-shmup-level-designscripting-i39m-so-lost/5184798/) — GameDev.net : la file d'actions `SpawnEnemy` / `Wait`.
- [Help:Glossary](https://shmups.wiki/library/Help:Glossary) — Shmups Wiki : checkpoint, *Gradius syndrome*.
