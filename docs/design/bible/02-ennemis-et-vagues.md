---
titre: Ennemis et vagues — rôles, priorité, composition
type: reference
statut: actif
maj: 2026-08-25
---

# Ennemis et vagues

## Ce que le genre dit

### Trois rôles, pas une liste d'unités

Boghog range les ennemis par **fonction**, non par apparence :

| Rôle | Ce qu'il fait au joueur |
|---|---|
| **Pression** | tir soutenu qui force le mouvement permanent |
| **Interdiction de zone** | ferme une portion de l'écran |
| **Défi direct** | l'élite, au pattern dense, qu'on affronte pour lui-même |

Un bestiaire se juge donc à la **couverture de ces rôles**, pas au nombre de silhouettes.

### La priorité de cible se lit, ou ne sert à rien

Ce qui fait qu'une unité doit être tuée en premier : **beaucoup de PV** (elle bloque les tirs
derrière elle), **un pattern dense**, **un cône large**, **une cadence élevée**. Le joueur doit
pouvoir désigner sa cible **d'un coup d'œil** — sinon le mécanisme de priorité n'existe pas.

### Le popcorn ne mérite pas de PV

> Le popcorn n'a que le **minimum de PV** nécessaire à sa fonction.

Et une règle anti-frustration explicite : **on doit pouvoir toucher un ennemi assis dessus.** Une
unité qu'on ne peut plus atteindre parce qu'on est trop près est une punition sans lecture.

### Approcher doit rester payant

> « Une approche sûre ne doit pas être plus dangereuse que d'ignorer l'ennemi. »

Certains jeux vont jusqu'au **bullet sealing** : l'ennemi faible devient passif quand le joueur est
tout près.

### Composer une vague : couloirs et chevauchement

- **Le motif Toaplan** : diviser l'écran en **5 à 7 couloirs**, faire apparaître les unités en
  **alternance de côtés opposés** — le joueur est forcé de traverser, et un rythme naît.
- **Le zigzag plutôt que l'empilement vertical** : une colonne fait attendre, un zigzag fait bouger.
- **Le chevauchement des vagues** est un système de risque-récompense complet : tuer vite dégage
  l'écran **avant** la vague suivante ; échouer fait se superposer deux vagues et rend la
  récupération difficile. C'est la même donnée de conception qui récompense et qui punit.
- **Utiliser tout l'écran** : une action confinée à une zone gâche le terrain.

### Le comportement peut suivre la performance

Un même ennemi peut avoir trois régimes selon la vitesse à laquelle on le tue : tué tout de suite
il ne tire presque pas ; à la normale il joue son pattern ; laissé en vie il **s'écarte** ou passe
à un pattern moins agressif — un filet de sécurité qui évite l'accumulation.

### Combiner vaut mieux qu'ajouter

Le retour d'expérience de *1993 Space Machine* est net : une zone tenue par **un seul type**
d'ennemi n'était jamais intéressante — c'est le **mélange** qui a créé le défi.

## Chez nous — état au 2026-08-25

**Le bestiaire couvre les trois rôles**, et c'est récent :

| Rôle | Nos unités |
|---|---|
| Pression | les neuf familles de Needle Scout (`EnemyPath`), le Crescent Interceptor |
| Interdiction de zone | **Null Maw** — `Effect.GRAVITY_WELL`, elle ne blesse pas, elle mange l'esquive ; **Choir Mine** posée en barrage |
| Défi direct | **Leech Drone** — le seul poursuivant (`Motion.HOMING`) ; les deux boss |

Et un quatrième rôle que le genre nomme peu : **le Shield Carrier** (`Effect.SHIELD_AURA`), qui ne
menace rien et rend les autres invulnérables — de la priorité de cible **pure**. ⚠️ Son comportement
est codé et testé, mais l'unité n'a ni Resource ni coque : elle n'est **jouable nulle part**.

| Point | État réel |
|---|---|
| Priorité de cible | ⚠️ **Conçue, pas encore jouée.** Le Shield Carrier est exactement le mécanisme décrit par le genre, et son brief (`BRIEF-0046`) exige qu'on comprenne « en une seconde » que c'est elle qu'il faut abattre. Non vérifiable tant qu'elle n'est pas en jeu |
| PV du popcorn | ✅ Tenu. Choir Mine 12 PV, Leech Drone 10 — elles tombent d'une salve |
| Toucher de près | ⚠️ Non vérifié. Les canons du chasseur sont frontaux ; une unité collée au nez est-elle atteignable ? Jamais mesuré |
| Approche payante | ✅ **Tenu, et réglé.** `pull_speed_max` de la Null Maw est plafonné à 7,0 contre 14,0 de vitesse joueur, et `GravityWell.leaves_room()` l'**impose** — « une aspiration à laquelle on ne peut rien opposer n'est plus un danger, c'est une cinématique » |
| Couloirs | ⚠️ **Absent comme outil.** Nos vagues posent des `spawn_plane_position` en unités monde, pas en couloirs. Le champ d'astéroïdes emploie quatre colonnes échelonnées — c'est du Toaplan sans le nommer |
| Chevauchement | ✅ Employé dans la vague 1 (les nuées se recouvrent) et dans le champ (les sangsues arrivent pendant que les puits descendent) |
| Régimes selon performance | ❌ **Inexistant.** Nos unités ont un comportement unique. `chase_time` de la sangsue est le seul filet : passé 8 s elle cesse de virer et sort |
| Mélange | ✅ C'est le principe explicite du champ d'astéroïdes : trois unités qui **se superposent** au lieu de se succéder |

## L'écart, et ce qu'on en fait

**Le plus rentable est déjà identifié et en cours** : mettre le Shield Carrier en jeu. C'est le rôle
que le genre décrit comme structurant et dont nous n'avons aucune expérience de terrain.

**Deux vérifications gratuites**, à faire en jouant :

- Peut-on toucher un ennemi collé au nez ? Si non, c'est une frustration sans lecture, et le genre
  la nomme.
- Nos salves groupées se lisent-elles comme des groupes ? (voir [Lisibilité](01-lisibilite.md))

**Une piste ouverte, non engagée** : les **régimes selon performance**. Elle est séduisante — elle
supprime l'accumulation quand le joueur peine — mais elle ajoute un axe à `EnemyData`, qui en a déjà
quatre (`Path`, `Motion`, `Fire`, `Effect`, ADR-0022). À ne pas ouvrir sans raison jouée.
