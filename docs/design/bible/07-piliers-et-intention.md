---
titre: Piliers et intention — ce qui arbitre
type: reference
statut: actif
maj: 2026-08-27
---

# Piliers et intention

Un pilier n'est pas un slogan : c'est un **arbitre**. Sa seule fonction utile est de trancher, à la
place de l'auteur, entre deux idées également séduisantes.

| Loi | Force | Énoncé |
|---|---|---|
| `LOI-PIL-01` | CONTRAINTE | Trois à cinq piliers, jamais plus |
| `LOI-PIL-02` | **LOI** | Un pilier tient en une phrase, en langage actif |
| `LOI-PIL-03` | **LOI** | Un pilier nomme un ressenti, pas une fonctionnalité |
| `LOI-PIL-04` | **LOI** | Toute idée passe le test du filtre : bien, neutre, ou mauvais |
| `LOI-PIL-05` | INTENTION | Les piliers servent à couper, pas à ajouter |
| `LOI-PIL-06` | **LOI** | Un pilier sans implémentation est signalé, jamais laissé en place |

---

### `LOI-PIL-01` · Trois à cinq piliers, jamais plus — [CONTRAINTE]

Les piliers sont « **3 à 5 éléments/émotions** que le jeu cherche à explorer et à faire ressentir ».
Le raisonnement est un aveu de budget, pas une convention esthétique : au-delà, « vous ne pourrez
pas livrer tous ces éléments à un haut niveau de qualité ».

### `LOI-PIL-02` · Un pilier tient en une phrase, en langage actif — **[LOI]**

- « Chaque énoncé doit être court — **pas plus d'une phrase**. »
- « Utiliser un **langage actif** » : *ce jeu est…*, *nous ferons…*

Un pilier qui demande un paragraphe n'arbitrera jamais rien en réunion, ni en session de travail.

### `LOI-PIL-03` · Un pilier nomme un ressenti, pas une fonctionnalité — **[LOI]**

Se concentrer sur « **ce que les joueurs vont ressentir**, plutôt que sur les choses qu'ils vont
faire ».

> *« Fais-moi me sentir puissant, et fais-moi dire : c'était énorme ! »* — et non *« système de
> combat à trois armes »*.

⚠️ **C'est le critère qui sépare un pilier d'une ligne de périmètre.** Une fonctionnalité nommée
dans un pilier **meurt avec la fonctionnalité** ; une émotion survit à son implémentation.

### `LOI-PIL-04` · Toute idée passe le test du filtre — **[LOI]**

Une question, posée à chaque idée : « ce changement **rapproche-t-il** le jeu de ses piliers
(*bien*), ne les affecte-t-il **pas vraiment** (*neutre*), ou joue-t-il **contre** eux (*mauvais*) ? »

Une idée brillante mais neutre **perd** contre une idée moyenne qui sert un pilier.

### `LOI-PIL-05` · Les piliers servent à couper, pas à ajouter — [INTENTION]

« Cette mécanique sert-elle nos piliers ? Si non, elle devrait probablement **disparaître**. » Un
corpus de piliers qui n'a jamais fait supprimer quoi que ce soit n'a pas encore servi.

### `LOI-PIL-06` · Un pilier sans implémentation est signalé, jamais laissé en place — **[LOI]**

Quand une décision supprime ce qu'un pilier décrivait, le pilier devient une phrase qui **n'arbitre
plus rien** — et il continue pourtant d'être lu comme une loi. Trois issues, et une seule est
interdite : le laisser tel quel.

1. **Le réécrire** autour de ce qui a repris sa fonction.
2. **Le retirer**, et assumer un pilier de moins.
3. **Lui redonner une implémentation.**

## Sources

- [Design Pillars – The Core of Your Game](https://www.gamedeveloper.com/design/design-pillars-the-core-of-your-game) — Game Developer : trois à cinq, le filtre, couper plutôt qu'ajouter.
- [How pillars and triangles can focus your game design](https://www.raspberrypi.com/news/how-pillars-and-triangles-can-focus-your-game-design/) — Raspberry Pi Foundation : la phrase unique, le langage actif, le ressenti avant les actes, le test bien/neutre/mauvais.
