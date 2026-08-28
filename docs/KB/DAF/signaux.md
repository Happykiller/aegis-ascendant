---
titre: La loi des signaux — un effet qui ne se montre pas n'existe pas
type: reference
statut: actif
maj: 2026-08-28
---

# La loi des signaux

Ce que le jeu **fait** et ce que le joueur **voit** sont deux choses distinctes, et la seconde est
la seule qui compte. Cette page existe parce que le projet a payé la différence **cinq fois en une
journée**, sur cinq mécaniques différentes.

## Les deux lois

### 1. Un effet qui change l'état du jeu sans le montrer se lit comme un DÉFAUT

Pas comme une menace, pas comme une subtilité : comme un bug, ou comme des commandes qui répondent
mal. Le joueur n'a aucune raison de supposer une mécanique invisible — il accuse le jeu.

### 2. ⚠️ Un signal MAL LU est pire qu'un signal absent

Un signe absent laisse le joueur ignorant. Un signe mal compris lui enseigne une **règle fausse**,
et il jouera contre elle. C'est la loi la plus dure des deux, et la plus facile à enfreindre en
croyant bien faire.

## Ce que ça a coûté, le 2026-08-26

| Mécanique | Ce qu'elle faisait | Ce que le joueur voyait |
|---|---|---|
| **Leech Drone** — freinage −35 % et drain 6 PV/s | rien du tout : `trigger_radius` à 0,9 pour une unité plus lente que le joueur, elle n'atteignait jamais l'état actif | « elles viennent se mettre autour de moi **sans rien faire** ? » |
| **Freinage** du joueur | `add_drag()` et rien d'autre | des commandes molles, donc un défaut du jeu |
| **Champ du porteur** | rend les ennemis voisins invulnérables ; **aucun effet sur le joueur** | « je ne comprends pas ce que cela fait » |
| **Puits gravitique** | aspire le chasseur, `pull_radius` sans **aucun** rendu | ses commandes lui échappent sans raison |
| **Sursis de la mine** | monte de 0,6 à 0,9 de régime, coque fermée | « l'activation est **trop subtile** » |

Et le cas de la loi n°2, le plus instructif : un lien plein tracé du porteur vers les unités qu'il
protège a été lu comme « **un lien se crée et on est ralenti** ». Le signe avait réussi à tracer une
ligne et échoué à dire ce qu'elle signifie — il enseignait l'inverse de la règle.

## Ce qui a corrigé chaque cas

- **Le signal se pose sur celui qui SUBIT.** Le freinage se lit sur les tuyères du joueur, pas sur
  la sangsue qui est ailleurs à l'écran.
- **Le SENS du signal porte la mécanique.** Les points d'un lien remontent du protégé *vers* le
  porteur (« c'est lui qui les tient ») ; ceux du tracteur vont du joueur *vers* le puits (« tu es
  tiré là-dedans »). Inversés, ils diraient exactement le contraire.
- **Un compte à rebours se lit à sa CADENCE**, pas à son intensité. Le halètement ordinaire des
  coques descend à 1,47 s par battement au plus affolé : sur un sursis d'une seconde, le joueur
  n'en voit pas un entier. Une cadence propre a dû être posée (2,5 → 9 Hz, en accélérant).
- **Un mouvement dit ce qu'une valeur ne dit pas.** La coque de la mine qui se *rabat* montre le
  pardon ; la même règle sans animation claquait d'une image à l'autre et se lisait comme un
  clignotement de bug.

## Le cas extrême, le 2026-08-28 : l'entité qui n'existe pas

Les cas de 2026-08-26 étaient des mécaniques **visibles mais illisibles**. Les missiles du Pale
Leviathan sont un cran plus loin : **l'objet lui-même n'avait aucune image**. Trois par salve,
toutes les 6 s, 40 PV, **22 de bouclier au contact** — et `grep` sur tout le dépôt ne sortait que le
fichier qui les crée. Rien ne les dessinait.

> « Les missiles existent mais j'ai eu l'impression qu'ils font rien à part me courir après » —
> l'opérateur, après les avoir découverts **par l'overlay de collision**, seule chose à l'écran qui
> en portait la trace : deux petits cercles qu'il ne comprenait pas.

Trois enseignements qui n'étaient pas dans la page :

- **Une attaque invisible n'est pas difficile, elle est FAUSSE.** Elle retire au joueur la seule
  chose que ce projectile existe pour lui apprendre — qu'il peut *répondre* à un tir au lieu de
  l'esquiver. Ce n'est pas un défaut de lisibilité, c'est une mécanique qui n'est pas jouable.
- **Une FIN est un signal, au même titre qu'un début.** Les deux issues du missile étaient muettes,
  chacune pour sa propre raison : `consume()` d'un côté, et de l'autre la valeur de retour
  d'`apply_damage()` — qui ne vaut vrai **que sur l'image où le projectile tombe**, précisément pour
  que l'appelant joue l'explosion une fois — **jetée**. Le joueur pouvait déjà les abattre ; rien ne
  le lui disait, donc il ne l'a jamais appris.
- **Et les deux fins ne se lisent pas pareil.** Sur le chasseur : explosion moyenne, secousse, son
  de coque — un coup reçu. Abattu en vol : explosion plus petite, pas de secousse, son léger — une
  récompense. Les jouer identiques dirait au joueur que réussir et échouer se valent.

⚠️ **Le réflexe qui aurait attrapé ça** n'est pas dans les deux questions ci-dessous : c'est de
demander, pour toute entité qui inflige des dégâts, *qu'est-ce qui la DESSINE ?* — et de répondre
par un fichier, pas par une intention. Voir [`ADR-0034`](../../decisions/ADR-0034-un-mur-arrete-un-tir.md).

## La contrepartie : ne pas promettre ce qu'on ne tient pas

La bible pose que **rien ne doit ressembler à un obstacle s'il n'en est pas un**
([`LOI-RYT-07`](../../design/bible/03-niveau-et-rythme.md)). La règle vaut aussi pour les
éléments de gameplay, et pas seulement pour le décor : un grand cercle lumineux dans lequel le
joueur vole **promet une conséquence**. S'il n'en délivre aucune, il ment — même quand la mécanique
sous-jacente est correcte.

## Le réflexe à garder

Devant toute mécanique qui modifie l'état du jeu, se poser **deux** questions et non une :

1. *Le joueur peut-il voir que ça se produit ?*
2. *Peut-il en déduire la bonne règle ?*

La seconde est celle qu'on oublie. Un signal qui répond « oui » à la première et « non » à la
seconde est un piège qu'on a soi-même posé.

⚠️ **Depuis le 2026-08-27, il existe une troisième question, et c'est la plus rentable** :
*quelle lecture fausse ne doit-il surtout PAS faire ?* C'est la ligne « à ne jamais produire » du
contrat joueur ([`LOI-EXP-09`](../../design/bible/10-experience-joueur.md)) — celle qui aurait
attrapé le lien du Shield Carrier lu comme « je suis ralenti », **avant** de l'implémenter.

## Voir aussi

- [`LOI-EXP-08`](../../design/bible/10-experience-joueur.md) — **cette page est devenue une loi du
  corpus** : « un effet invisible se lit comme un défaut ; un signal mal lu est pire qu'un signal
  absent ». C'est la seule loi de la bible née du terrain et non d'une lecture
- [Lisibilité](../../design/bible/01-lisibilite.md) — le contrat de lecture, dont la télégraphie
  ([`LOI-LIS-04`](../../design/bible/01-lisibilite.md))
- [`CONFORMITE-AEGIS.md`](../../design/CONFORMITE-AEGIS.md), section `BOS` — « tirer dessus sans
  rien produire à l'écran se lit comme un défaut, pas comme une armure » : la même loi, découverte
  sur le Choir Harvester et non généralisée avant cette page
