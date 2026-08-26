---
titre: La loi des signaux — un effet qui ne se montre pas n'existe pas
type: reference
statut: actif
maj: 2026-08-26
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

## La contrepartie : ne pas promettre ce qu'on ne tient pas

La bible pose que **rien ne doit ressembler à un obstacle s'il n'en est pas un**
([Niveau et rythme](../../design/bible/03-niveau-et-rythme.md)). La règle vaut aussi pour les
éléments de gameplay, et pas seulement pour le décor : un grand cercle lumineux dans lequel le
joueur vole **promet une conséquence**. S'il n'en délivre aucune, il ment — même quand la mécanique
sous-jacente est correcte.

## Le réflexe à garder

Devant toute mécanique qui modifie l'état du jeu, se poser **deux** questions et non une :

1. *Le joueur peut-il voir que ça se produit ?*
2. *Peut-il en déduire la bonne règle ?*

La seconde est celle qu'on oublie. Un signal qui répond « oui » à la première et « non » à la
seconde est un piège qu'on a soi-même posé.

## Voir aussi

- [Lisibilité](../../design/bible/01-lisibilite.md) — le contrat de lecture, dont la télégraphie
- [Boss](../../design/bible/04-boss.md) — « tirer dessus sans rien produire à l'écran se lit comme
  un défaut, pas comme une armure » : la même loi, découverte sur le Choir Harvester et non
  généralisée avant cette page
