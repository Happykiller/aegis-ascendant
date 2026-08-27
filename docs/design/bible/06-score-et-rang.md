---
titre: Score et rang — les objectifs en conflit, et la difficulté qui s'adapte
type: reference
statut: actif
maj: 2026-08-27
---

# Score et rang

Un compteur de points n'est pas un système de score. La différence tient en un mot : **le conflit**.

| Loi | Force | Énoncé |
|---|---|---|
| `LOI-SCO-01` | **LOI** | Un bon système de score fait faire ce qu'on ne ferait pas |
| `LOI-SCO-02` | **LOI** | Sans objectifs en conflit, il n'y a pas de décision |
| `LOI-SCO-03` | RÉFÉRENCE | Le chaînage est dépendant du temps |
| `LOI-SCO-04` | CONTRAINTE | Linéaire ou exponentiel : choisir, et assumer ce que ça punit |
| `LOI-SCO-05` | RÉFÉRENCE | Agressif ou défensif : qui attaque qui |
| `LOI-SCO-06` | CONTRAINTE | Le rang obéit à quatre règles, ou il devient un bug perçu |

---

### `LOI-SCO-01` · Un bon système de score fait faire ce qu'on ne ferait pas — **[LOI]**

> Un bon système « récompense le joueur qui comprend le jeu **plus profondément** et emploie des
> stratégies qu'il n'emploierait pas s'il cherchait *seulement* à finir ».

Un score qui monte tout seul en jouant normalement ne récompense rien : il **mesure**.

### `LOI-SCO-02` · Sans objectifs en conflit, il n'y a pas de décision — **[LOI]**

La structure de base : survivre d'un côté, prendre des risques pour des points de l'autre, et des
ressources finies qui obligent à choisir. **Sans conflit, pas de décision — donc pas de jeu dans le
jeu.**

C'est la marche la plus courte vers un scoring qui existe : il suffit qu'une chose désirable
**coûte** quelque chose.

### `LOI-SCO-03` · Le chaînage est dépendant du temps — [RÉFÉRENCE]

Le **chain** est une suite d'ennemis abattus sans interruption, qui fait monter un multiplicateur.
Au-delà d'un certain intervalle entre deux morts, la chaîne casse — c'est ce délai, et non le
multiplicateur, qui dicte la façon de jouer.

### `LOI-SCO-04` · Linéaire ou exponentiel : choisir, et assumer ce que ça punit — [CONTRAINTE]

| | Linéaire | Exponentiel |
|---|---|---|
| Erreur isolée | peu ou pas punie | casse la chaîne, remet à zéro |
| Ce qu'il reflète | l'adresse **globale** | des **pics** de risque |
| Récupération | possible par l'excellence ensuite | non |

### `LOI-SCO-05` · Agressif ou défensif : qui attaque qui — [RÉFÉRENCE]

- **Défensif** — « le jeu vous attaque » : un minuteur force à continuer.
- **Agressif** — « vous attaquez le jeu » : le bonus se gagne activement, sans pression.

### `LOI-SCO-06` · Le rang obéit à quatre règles — [CONTRAINTE]

Le **rang** est une difficulté qui suit la performance du joueur, en continu. Quatre règles le
séparent d'un système qui se lit comme un bug :

1. **Rétroaction continue**, sans paliers visibles — l'évolution doit être imperceptible.
2. **Plusieurs vecteurs** alimentent un seul paramètre (objets ramassés, puissance atteinte, coups
   tirés…).
3. **La mort remet du mou** — le système ne peut pas s'emballer.
4. Le joueur doit pouvoir **agir** dessus, même sans le comprendre.

⚠️ La quatrième est la plus violée. Une difficulté qui monte sans que rien ne le dise, et sur
laquelle le joueur ne peut rien, ne se lit pas comme un adversaire : elle se lit comme un défaut.

⚠️ **Prudence sur les chiffres publiés.** La documentation de référence du rang expose une variable
interne **inversée** (une valeur élevée y correspond à une difficulté plus faible). Ne recopier
aucune formule sans la revérifier à la source.

## Sources

- [Boghog's bullet hell shmup 101](https://shmups.wiki/library/Boghog%27s_bullet_hell_shmup_101) — Shmups Wiki : objectifs en conflit, chaînage, linéaire/exponentiel, agressif/défensif.
- [Battle Garegga / Advanced Rank](https://shmups.wiki/library/Battle_Garegga/Advanced_Rank) — Shmups Wiki : le rang décortiqué, et la variable inversée.
