---
titre: Ennemis et vagues — rôles, priorité, composition
type: reference
statut: actif
maj: 2026-08-27
---

# Ennemis et vagues

Un bestiaire ne se juge pas au nombre de silhouettes, et une vague n'est pas une liste d'ennemis :
c'est une **composition**, avec un rythme et une intention.

| Loi | Force | Énoncé |
|---|---|---|
| `LOI-ENN-01` | **LOI** | Un bestiaire se juge à sa couverture des rôles, pas à son nombre d'unités |
| `LOI-ENN-02` | **LOI** | La priorité de cible se lit d'un coup d'œil, ou elle n'existe pas |
| `LOI-ENN-03` | CONTRAINTE | Le popcorn n'a que le minimum de points de vie nécessaire à sa fonction |
| `LOI-ENN-04` | **LOI** | On doit pouvoir toucher un ennemi collé au vaisseau |
| `LOI-ENN-05` | **LOI** | Approcher doit rester payant |
| `LOI-ENN-06` | RÉFÉRENCE | Le motif Toaplan : 5 à 7 couloirs, en alternance de côtés opposés |
| `LOI-ENN-07` | INTENTION | Zigzag plutôt qu'empilement vertical |
| `LOI-ENN-08` | INTENTION | Le chevauchement des vagues est un risque-récompense complet |
| `LOI-ENN-09` | **LOI** | Une vague emploie tout l'écran |
| `LOI-ENN-10` | RÉFÉRENCE | Le comportement d'une unité peut suivre la performance du joueur |
| `LOI-ENN-11` | **LOI** | Combiner vaut mieux qu'ajouter |

---

### `LOI-ENN-01` · Un bestiaire se juge à sa couverture des rôles — **[LOI]**

Les ennemis se rangent par **fonction**, jamais par apparence :

| Rôle | Ce qu'il fait au joueur |
|---|---|
| **Pression** | tir soutenu qui force le mouvement permanent |
| **Interdiction de zone** | ferme une portion de l'écran |
| **Défi direct** | l'élite, au pattern dense, qu'on affronte pour elle-même |

Dix silhouettes qui remplissent le même rôle font un bestiaire pauvre ; trois qui couvrent les trois
rôles font un bestiaire complet.

### `LOI-ENN-02` · La priorité de cible se lit d'un coup d'œil, ou elle n'existe pas — **[LOI]**

Ce qui désigne une unité comme prioritaire : **beaucoup de PV** (elle bloque les tirs derrière
elle), **un pattern dense**, **un cône large**, **une cadence élevée**.

Le joueur doit pouvoir désigner sa cible **sans réfléchir**. Une priorité qui demande une analyse
n'est pas une priorité : c'est une punition différée.

### `LOI-ENN-03` · Le popcorn n'a que le minimum de PV nécessaire à sa fonction — [CONTRAINTE]

Une unité de remplissage qui survit à une salve cesse d'être du remplissage : elle devient un
obstacle, et fausse le rythme prévu pour la vague.

### `LOI-ENN-04` · On doit pouvoir toucher un ennemi collé au vaisseau — **[LOI]**

Une unité qu'on ne peut plus atteindre **parce qu'on est trop près** est une punition sans lecture.
Elle enseigne au joueur une règle fausse : « ne pas s'approcher », alors que le problème est
géométrique.

### `LOI-ENN-05` · Approcher doit rester payant — **[LOI]**

> « Une approche sûre ne doit pas être plus dangereuse que d'ignorer l'ennemi. »

Le risque pris doit avoir une contrepartie. Certains jeux vont jusqu'au **bullet sealing** :
l'ennemi faible devient passif quand le joueur est tout près.

### `LOI-ENN-06` · Le motif Toaplan — [RÉFÉRENCE]

Diviser l'écran en **5 à 7 couloirs**, faire apparaître les unités en **alternance de côtés
opposés**. Le joueur est forcé de traverser, et un rythme naît de la traversée elle-même.

C'est un patron éprouvé, pas une obligation — mais un jeu qui pose ses ennemis en coordonnées
absolues plutôt qu'en couloirs se prive d'un outil de composition entier.

### `LOI-ENN-07` · Zigzag plutôt qu'empilement vertical — [INTENTION]

Une colonne d'ennemis fait **attendre** ; un zigzag fait **bouger**. À nombre d'unités égal, la
disposition décide de ce que le joueur fait de son temps.

### `LOI-ENN-08` · Le chevauchement des vagues est un risque-récompense complet — [INTENTION]

Tuer vite dégage l'écran **avant** l'arrivée de la vague suivante ; échouer fait se superposer deux
vagues et rend la récupération difficile.

C'est la même donnée de conception qui **récompense** et qui **punit** — la forme la plus économique
de tension qu'un shoot vertical puisse produire.

### `LOI-ENN-09` · Une vague emploie tout l'écran — **[LOI]**

Une action confinée à une zone gâche le terrain, et transforme le reste de l'écran en décor.

### `LOI-ENN-10` · Le comportement peut suivre la performance — [RÉFÉRENCE]

Un même ennemi peut avoir trois régimes selon la vitesse à laquelle on le tue : abattu tout de
suite il ne tire presque pas ; à la normale il joue son pattern ; laissé en vie il **s'écarte** ou
passe à un pattern moins agressif.

C'est un filet de sécurité contre l'accumulation. ⚠️ Il ajoute un axe de comportement à chaque
unité : à ne pas ouvrir sans raison observée en jeu.

### `LOI-ENN-11` · Combiner vaut mieux qu'ajouter — **[LOI]**

Une zone tenue par **un seul type** d'unité n'est jamais intéressante, quel qu'en soit le nombre.
C'est le **mélange** qui crée le défi — et il coûte moins cher qu'une unité de plus.

## Sources

- [Boghog's bullet hell shmup 101](https://shmups.wiki/library/Boghog%27s_bullet_hell_shmup_101) — Shmups Wiki : rôles, priorité de cible, popcorn, sealing, couloirs, chevauchement.
- [Designing smart, meaningful SHMUPs](https://www.gamedeveloper.com/design/designing-smart-meaningful-shmups) — Game Developer : le motif Toaplan, l'usage de tout l'écran.
- [Balancing the sh#& out of our shmup](https://www.gamedeveloper.com/design/balancing-the-sh-out-of-our-shmup) — Game Developer : « combiner vaut mieux qu'ajouter », retour d'expérience vécu.
