---
titre: Patterns de tir — la taxonomie du danmaku
type: reference
statut: actif
maj: 2026-08-27
---

# Patterns de tir

[Lisibilité](01-lisibilite.md) dit **comment un pattern se lit**. Ce domaine dit **de quoi il est
fait** : les familles géométriques, leurs paramètres, et ce que chacune impose au joueur.

| Loi | Force | Énoncé |
|---|---|---|
| `LOI-PAT-01` | **LOI** | Le nombre de balles n'est pas le sujet |
| `LOI-PAT-02` | RÉFÉRENCE | Cinq familles : anneau, éventail, mur, pile, flux |
| `LOI-PAT-03` | **LOI** | La parité d'un éventail décide de son sens |
| `LOI-PAT-04` | CONTRAINTE | Trois semences d'angle, et jamais uniquement du fixe |
| `LOI-PAT-05` | INTENTION | Composer plutôt qu'agrandir |
| `LOI-PAT-06` | **LOI** | Un pattern désigne son mode d'esquive |
| `LOI-PAT-07` | CONTRAINTE | Deux schémas doivent différer par leur forme, pas par leurs constantes |

---

### `LOI-PAT-01` · Le nombre de balles n'est pas le sujet — **[LOI]**

> « La première chose à noter, c'est que le facteur qui différencie n'est **pas** le nombre de
> balles. On peut en avoir beaucoup, mais si elles ne sont pas employées avec **intention**, ce
> n'est pas vraiment du bullet hell. »

### `LOI-PAT-02` · Cinq familles — [RÉFÉRENCE]

| Famille | Construction | Ce qu'elle impose au joueur |
|---|---|---|
| **Anneau** (*ring*) | ≥ 3 balles tirées **au même instant**, écart angulaire commun = 360°/n | seule la **distance** protège ; aucune direction n'est sûre |
| **Éventail** (*spread*, *n-way*) | balles dans un **arc**, écart angulaire commun | ferme un secteur ; on le contourne |
| **Mur** (*wall*) | « toute formation à travers laquelle le joueur **ne peut pas passer** » | **macro-esquive** : contourner, jamais traverser |
| **Pile** (*stack*) | plusieurs balles **au même angle**, avec un **décalage de vitesse** | « de longs murs parfaits pour le *streaming*, et des lignes qui autorisent la micro-esquive » |
| **Flux** (*stream*) | anneaux ou chaînes de balles **visées**, tirés à la suite | on s'éloigne latéralement pour **concentrer** le flux et libérer l'écran |

### `LOI-PAT-03` · La parité d'un éventail décide de son sens — **[LOI]**

C'est la loi la plus opérationnelle du domaine :

> Un nombre **impair** de balles **piège** le joueur ; un nombre **pair** fait que **toutes les
> balles de l'éventail l'évitent**.

Pour un éventail **visé** :

- **impair** → une balle part **exactement sur la ligne de visée**. Rester immobile tue : le pattern
  **punit l'inaction**.
- **pair** → l'axe de visée est **vide**. Le joueur est « piégé dans un secteur angulaire **sans
  être touché** » : le pattern **contraint la position**.

⚠️ Les deux sont valides, mais ce sont **deux intentions opposées** — et elles se décident par un
nombre. Un compte de balles qui varie avec la phase, la difficulté ou le niveau de puissance
**change le sens du pattern à chaque changement de parité**, sans que personne ne l'ait voulu.

### `LOI-PAT-04` · Trois semences d'angle, et jamais uniquement du fixe — [CONTRAINTE]

| Semence | Effet |
|---|---|
| **fixe** | motifs prévisibles, lisibles, apprenables — mais « laisse des **angles morts** » où le joueur peut se poster |
| **aléatoire** | couverture ; produit des patterns « désordonnés, particulièrement durs à esquiver » |
| **visée** | interaction directe avec la position du joueur |

Le conseil est net : **ne pas n'employer que des semences fixes** si le pattern est fait pour être
esquivé — sinon un point sûr existe quelque part, et il sera trouvé.

### `LOI-PAT-05` · Composer plutôt qu'agrandir — [INTENTION]

Une **pile d'anneaux** (mêmes anneaux, vitesses différentes) donne de la profondeur gratuitement :
« les balles rapides d'un groupe **plus tardif** peuvent dépasser les balles lentes d'un groupe
**antérieur**, ce qui produit un chevauchement du motif et une complexité supérieure » — sans une
seule balle de plus.

Une **pile d'éventails** a la propriété inverse, et elle est défensive : elle a « des **bords
nets** » et laisse « des ouvertures entre les piles, plus loin du point de tir, ce qui permet de
s'échapper ».

Règle de composition qui les recouvre toutes : **régularité, plus une légère fluctuation**. Une
couronne sur deux décalée d'un demi-intervalle interdit de rester immobile, sans ajouter un
projectile.

### `LOI-PAT-06` · Un pattern désigne son mode d'esquive — **[LOI]**

| Mode | Ce que le joueur fait |
|---|---|
| **micro-esquive** | enfiler précisément de petits interstices, par mouvements délicats |
| **macro-esquive** | lire **tout l'écran** pour trouver les grandes ouvertures, par grands déplacements |
| **streaming** | éviter des balles visées en bougeant **le moins possible** |
| **restream** | ouvrir un trou dans ce flux : changement de direction sec, pause, retour |

Un mur qu'on croit micro-esquivable tue ; un nuage qu'on macro-esquive fait perdre l'écran. Le
pattern doit **dire** lequel il attend — par sa forme, avant d'être compris.

### `LOI-PAT-07` · Deux schémas diffèrent par leur forme, pas par leurs constantes — [CONTRAINTE]

Un éventail de trois balles n'est pas un éventail de cinq : c'est **le même geste**, et le joueur le
voit. Une bibliothèque de patterns dont deux entrées ne se distinguent que par un réglage n'a
qu'une entrée.

Le test : deux schémas sont distincts si l'on peut nommer, en une phrase, ce que l'un fait au joueur
et que l'autre ne fait pas. *« L'un est aveugle, l'autre voit »* est une distinction ; *« l'un est
plus large »* n'en est pas une.

## Sources

- [Sparen's Danmaku Design Studio — Guide A3](https://sparen.github.io/ph3tutorials/ddsga3.html) — anneaux, éventails et leur parité, murs, piles, piles d'anneaux et d'éventails, chevauchement.
- [Sparen's Danmaku Design Studio — Guide A2](https://sparen.github.io/ph3tutorials/ddsga2.html) — l'intention avant le nombre, les trois semences d'angle, les angles morts du fixe.
- [Help:Glossary](https://shmups.wiki/library/Help:Glossary) — Shmups Wiki : micro/macro-esquive, streaming, restream.
