---
titre: Score et rang — les objectifs en conflit, et la difficulté qui s'adapte
type: reference
statut: actif
maj: 2026-08-25
---

# Score et rang

## Ce que le genre dit

### Un bon système de score fait faire ce qu'on ne ferait pas

> Un bon système « récompense le joueur qui comprend le jeu plus profondément et emploie des
> stratégies qu'il n'emploierait pas s'il cherchait *seulement* à finir ».

Sa structure de base : **des objectifs en conflit**. Survivre d'un côté, prendre des risques pour des
points de l'autre — et des ressources finies qui obligent à choisir. Sans conflit, il n'y a pas de
décision, donc pas de jeu dans le jeu.

### Chaînage

Le **chain** est une suite d'ennemis abattus sans interruption, qui fait monter un multiplicateur.
Il est **dépendant du temps** : au-delà d'un certain intervalle entre deux morts, la chaîne casse.

### Linéaire ou exponentiel — deux philosophies

| | Linéaire | Exponentiel |
|---|---|---|
| Erreur isolée | peu ou pas punie | casse la chaîne, remet à zéro |
| Ce qu'il reflète | l'adresse **globale** | des pics de risque |
| Récupération | possible par l'excellence ensuite | non |

### Agressif ou défensif

- **Défensif** — « le jeu vous attaque » : un minuteur force à continuer (école *DoDonPachi*).
- **Agressif** — « vous attaquez le jeu » : le bonus se gagne activement, sans pression.

### Le rang : la difficulté qui suit le joueur

L'exemple canonique est *Battle Garegga*. Le jeu suit en continu **combien d'objets sont ramassés,
à quel point le vaisseau est monté en puissance, et même combien de coups sont tirés**, et durcit le
jeu en conséquence. **Mourir est le principal moyen de faire redescendre la difficulté** — et
d'autant plus qu'on a peu de vies en réserve.

Quatre leçons de conception, indépendamment du jeu :

1. **Rétroaction continue**, sans paliers visibles — l'évolution doit être imperceptible.
2. **Plusieurs vecteurs** alimentent un seul paramètre.
3. **La mort remet du mou** — le système ne peut pas s'emballer.
4. Le joueur doit pouvoir **agir** dessus, même sans le comprendre.

⚠️ **Prudence sur les chiffres.** La page de référence expose une variable interne **inversée** (un
« rank » élevé y correspond à une difficulté plus faible) et l'affiche en pourcentage retourné. La
lecture fonctionnelle — tirer et se renforcer durcit, mourir adoucit — est celle des sources
secondaires. Ne pas recopier de formule d'ici sans la revérifier à la source.

## Chez nous — état au 2026-08-25

| Point | État réel |
|---|---|
| Score | ✅ Existe, et rien de plus : `GameState.add_score()`. Chaque ennemi vaut son `score_value` (90 pour la Choir Mine, 140 la Null Maw, 160 la Leech Drone), le mini-boss 5 000, le boss final 20 000, un ramassage 500 |
| Objectifs en conflit | ❌ **Aucun.** Le score est une conséquence mécanique du fait de jouer : rien ne se gagne en prenant un risque, rien ne se perd en jouant prudemment |
| Chaînage | ❌ Inexistant |
| Multiplicateur | ❌ Inexistant |
| Rang / difficulté dynamique | ❌ Inexistant. La difficulté est **entièrement scriptée** : la timeline d'une `WaveData`, et les cycles du boss |
| Rang affiché | ✅ Le rapport de mission attribue un rang (un « rang C » est mentionné dans le code du drapeau de démonstration) |

## L'écart, et ce qu'on en fait

C'est **le plus grand écart de toute la bible** : le genre considère le score comme un système de
jeu à part entière, nous en avons un compteur.

⚠️ **Et ce n'est pas forcément un défaut.** Un système de score profond sert une pratique de
répétition — le 1CC, le classement, la rejouabilité. Rien dans la spec ne dit qu'Aegis Ascendant vise
cela, et le P0 du backlog parle d'une **démo irréprochable de 2-3 minutes**, pas d'un jeu à scoring.
Ajouter un chaînage à un arc qu'on traverse une fois, c'est ajouter de la complexité à personne.

**La question appartient à l'opérateur**, et elle se pose en une phrase : *veut-on que l'arc se
rejoue pour le score, ou se traverse une fois ?* Les deux réponses sont défendables, et elles
commandent des chantiers très différents.

Si la réponse est « on rejoue », la marche la plus courte n'est **pas** le rang — c'est le
**conflit d'objectifs**, qui ne demande aucun système nouveau : il suffit qu'une chose désirable
coûte quelque chose. Le rang, lui, est un mécanisme puissant mais qui se règle en aveugle et se
mesure mal ; le projet a déjà appris ce que coûte un calibrage qui devient faux en silence
(`ADR-0024`, `ADR-0026`).
