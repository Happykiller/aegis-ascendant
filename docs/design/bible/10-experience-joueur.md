---
titre: Expérience joueur — sensation, flow, apprentissage, signaux, accessibilité
type: reference
statut: actif
maj: 2026-08-27
---

# Expérience joueur

Ce que le joueur **ressent**, par opposition à ce que le jeu **contient**. C'est le domaine le plus
large du corpus, et le seul dont les manquements ne se voient jamais dans un test automatisé.

| Loi | Force | Énoncé |
|---|---|---|
| `LOI-EXP-01` | **LOI** | Trois choses doivent s'aligner : réponse, retour lisible, finition |
| `LOI-EXP-02` | **LOI** | On ne « juice » pas un jeu qui répond mal |
| `LOI-EXP-03` | CONTRAINTE | Le *hit stop* fait atterrir la conséquence — 60 à 80 ms |
| `LOI-EXP-04` | INTENTION | Le jeu accepte l'intention du joueur, pas la précision de son doigt |
| `LOI-EXP-05` | **LOI** | Ni ennui, ni angoisse |
| `LOI-EXP-06` | **LOI** | Après un gain de puissance vient une baisse de difficulté |
| `LOI-EXP-07` | INTENTION | On apprend en jouant : de l'espace, une erreur peu coûteuse, puis l'évaluation |
| `LOI-EXP-08` | **LOI** | Un effet invisible se lit comme un défaut ; un signal mal lu est pire qu'un signal absent |
| `LOI-EXP-09` | **LOI** | Une mécanique n'est pas spécifiée tant que l'expérience qu'elle produit ne l'est pas |
| `LOI-EXP-10` | **LOI** | Aucune information essentielle n'est portée par une couleur seule |
| `LOI-EXP-11` | CONTRAINTE | Le socle d'accessibilité est un plancher, pas une option |
| `LOI-EXP-12` | **LOI** | Un système qui fonctionne n'est pas validé : il l'est quand l'expérience est là |

---

### `LOI-EXP-01` · Trois choses doivent s'aligner — **[LOI]**

> Un jeu est agréable quand trois choses s'alignent : **les commandes répondent à l'instant** où
> l'on appuie, **chaque action produit un retour que le joueur peut lire**, et une **couche de
> finition** transforme chaque interaction en quelque chose de satisfaisant.

Les deux premières forment le *game feel* ; la troisième est la *juice* —
« l'esthétique **non fonctionnelle** : elle **ne change pas les règles**, elle change
**l'expérience** ».

### `LOI-EXP-02` · On ne « juice » pas un jeu qui répond mal — **[LOI]**

La finition **amplifie** la sensation existante, y compris quand elle est mauvaise. L'ordre de
travail n'est pas négociable : réponse, puis lisibilité du retour, puis finition.

### `LOI-EXP-03` · Le *hit stop* fait atterrir la conséquence — [CONTRAINTE]

| Technique | Effet | Repère |
|---|---|---|
| **Hit stop** | fige tout, brièvement, à l'impact | **60 à 80 ms** sur une frappe décisive |
| **Screen shake** | traduit la violence sans l'infliger | une trentaine de trucs cumulables |
| **Squash & stretch, anticipation, follow-through** | emprunts aux douze principes de l'animation | — |

### `LOI-EXP-04` · Le jeu accepte l'intention, pas la précision du doigt — [INTENTION]

L'**input buffering** mémorise une commande envoyée trop tôt ; le **coyote time** tolère une
commande envoyée trop tard (5 à 10 images). Les deux disent la même chose, et c'est l'idée la plus
transposable du *game feel* : **on interprète ce que le joueur voulait faire**.

### `LOI-EXP-05` · Ni ennui, ni angoisse — **[LOI]**

Le canal de flow oppose deux échecs symétriques : les défis montent **trop lentement** par rapport
aux compétences → **ennui** ; ils montent **plus vite** que la compétence ne s'acquiert →
**angoisse**. Les deux mènent au même mot, « le pire qu'un concepteur puisse entendre » :
frustration.

### `LOI-EXP-06` · Après un gain de puissance vient une baisse de difficulté — **[LOI]**

La difficulté oscille en **dent de scie**, et l'ordre est contre-intuitif :

> Ne jamais donner une nouvelle capacité sans l'enseigner, ni sans laisser s'y habituer. On donne
> une capacité, **puis on baisse volontairement la difficulté**. Une fois le joueur à l'aise, on
> remonte — pour redescendre plus tard.

Autrement dit : le gain de puissance ouvre une **phase de fantasme de puissance**, pas un pic. Et
l'oscillation est **fractale** — à l'intérieur d'une séquence comme entre deux sections.

### `LOI-EXP-07` · On apprend en jouant — [INTENTION]

Trois principes, tirés des premières minutes de jeux qui n'expliquent rien :

1. **Commencer par de l'espace** — de la place pour apprendre à se déplacer avant toute complexité.
2. **Un environnement d'apprentissage sûr** — la première erreur doit être **peu coûteuse**.
3. **Évaluer juste après** — la situation d'apprentissage sûre est suivie de sa jumelle, celle-là
   réelle.

### `LOI-EXP-08` · Un effet invisible se lit comme un défaut — **[LOI]**

Deux propositions indissociables :

- **Un effet qui ne se montre pas se lit comme un défaut.** Le joueur n'a pas accès à l'état interne
  du jeu : ce qui n'est pas signalé n'existe pas, et ce qui n'existe pas mais se ressent est un bug.
- **Un signal mal compris est pire qu'un signal absent**, parce qu'il enseigne une **règle fausse**
  — et le joueur jouera cette règle fausse jusqu'à ce qu'elle le tue.

### `LOI-EXP-09` · Une mécanique n'est pas spécifiée tant que l'expérience ne l'est pas — **[LOI]**

Toute mécanique porte **deux contrats**. Le contrat système
(`objectif / entrées / sorties / états / transitions / valeurs / interactions / exceptions`) ne
suffit jamais. Il lui faut son contrat joueur :

| Dimension | Ce qu'il faut écrire |
|---|---|
| **SEE** | ce que le joueur doit **percevoir** |
| **UNDERSTAND** | la règle qu'il doit en **déduire** |
| **FEEL** | ce qu'il doit **ressentir** |
| **ANTICIPATE** | ce qu'il doit pouvoir **prévoir** |
| **DECIDE** | la **décision** que la mécanique doit provoquer |
| **À ne jamais produire** | les lectures fausses à exclure explicitement |

⚠️ **La dernière ligne est celle qui rapporte le plus.** Écrire « le joueur ne doit surtout pas
comprendre *je suis ralenti* » attrape, avant l'implémentation, la classe de défaut que les autres
lignes laissent passer.

### `LOI-EXP-10` · Aucune information essentielle n'est portée par une couleur seule — **[LOI]**

Prolonge [`LOI-LIS-01`](01-lisibilite.md) hors du champ visuel : tout signal critique doit être
**redondant** sur au moins deux canaux — forme, mouvement, son, position, texte. Ce n'est pas
seulement une règle d'accessibilité : c'est ce qui sauve la lecture quand l'écran est saturé.

### `LOI-EXP-11` · Le socle d'accessibilité est un plancher — [CONTRAINTE]

Quatre manques reviennent plus que tous les autres : **remappage**, **taille de texte**,
**daltonisme**, **sous-titres**. Le plancher, pour un jeu d'action rapide :

- **remappage** des commandes et **sensibilité** ajustable ;
- aucune information essentielle par la couleur seule ;
- police lisible par défaut, **fort contraste** texte/fond ;
- pas d'images clignotantes ni de motifs répétitifs (photosensibilité) ;
- **secousse d'écran réductible ou désactivable** ;
- un **choix de difficulté**.

### `LOI-EXP-12` · Un système qui fonctionne n'est pas validé — **[LOI]**

Deux disciplines distinctes, et confondre les deux est la faute la plus coûteuse du domaine :

| | **Vérification** | **Validation** |
|---|---|---|
| Question | « le système fait-il ce qui est spécifié ? » | « le joueur vit-il ce qui est visé ? » |
| Exemple | « la mine attend-elle réellement 1 s ? » | « le joueur comprend-il qu'il a un sursis ? » |
| Méthodes | test, analyse, inspection, démonstration | **playtest**, observation |

Un test unitaire prouve parfaitement la première colonne et est **totalement incapable** de prouver
la seconde. Une porte de qualité verte n'a jamais démontré qu'un jeu était lisible.

## Sources

- [How to Make Your Game Feel Good](https://egmatic.com/blog/how-to-make-your-game-feel-good) — les trois choses qui s'alignent, hit stop 60–80 ms, coyote time, input buffering.
- [The Art of Screenshake](https://www.youtube.com/watch?v=AJdEqssNZ-U) — Jan Willem Nijman (Vlambeer), INDIGO Classes 2013. ⚠️ Conférence vidéo, non transcrite.
- [Game Design Theory Applied: The Flow Channel](https://www.gamedeveloper.com/design/game-design-theory-applied-the-flow-channel) — ennui/angoisse, l'oscillation, son caractère fractal.
- [Video Game Level Design and Difficulty](https://stepico.com/blog/video-game-level-design-and-difficulty-how-to-challenge-players-without-losing-them/) — « tense and release », l'ordre capacité → baisse de difficulté.
- [Why Super Mario Bros is still a fantastic lesson in game design](https://www.creativebloq.com/3d/video-game-design/why-super-mario-bros-is-still-a-fantastic-lesson-in-game-design) — l'apprentissage sans tutoriel, l'erreur peu coûteuse suivie de sa jumelle réelle.
- [Game Accessibility Guidelines — Basic](https://gameaccessibilityguidelines.com/basic/) — le plancher : remappage, sensibilité, couleur, contraste, clignotement, difficulté.
- Vérification / validation : distinction empruntée aux pratiques d'ingénierie (V&V), et la méthode `PLAYTEST` comme extension propre au jeu.
