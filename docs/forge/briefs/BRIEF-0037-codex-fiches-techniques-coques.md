# BRIEF-0037 — Fiches techniques des cinq coques, pour le bestiaire

- **Statut** : intégré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-22

## Objectif

Produire les **données de fiche technique** (désignation, classe, constructeur, masse, équipage,
statut, notice) des cinq coques du jeu, pour alimenter l'écran **Bestiaire** ajouté au menu d'accueil.

Livrable unique : **un fichier markdown de données**, pas d'asset binaire, pas de code.

## Contexte

Le menu d'accueil reçoit une entrée « LE BESTIAIRE » : un écran qui présente **une coque à la fois**,
en 3D, plein cadre, animée et manipulable (rotation, zoom), avec ses caractéristiques affichées en
langage HUD — registre « fiche de dossier technique militaire », dans l'esprit des holo-fiches de
Star Citizen.

L'écran dispose déjà des données **mesurables ou déjà canoniques**, et elles ne sont PAS de ton
ressort :

- **dimensions** — calculées à l'exécution depuis la boîte englobante du `.glb` ;
- **points de structure, vitesse, cadence de tir, score, rayon de touche** — lus dans les Resources
  de gameplay existantes (`resources/enemies/*.tres`, `resources/player/specter9_stats.tres`, et les
  valeurs exportées des scènes de boss).

Il manque tout ce qui relève de la **fiction** : c'est l'objet de ce brief.

Charte applicable : `docs/forge/CHARTE_CREATIVE.md` §1 (ton), §2 (canon — les noms officiels
existent déjà, **ne pas en inventer d'autres**), §3 (palettes, pour le registre de langage).

## Les cinq coques, avec leurs faits établis

L'échelle du projet est **1 unité monde = 1 mètre**. Les dimensions ci-dessous sont **mesurées** sur
les `.glb` livrés (longueur = axe de vol, largeur = envergure, hauteur = tirant). Elles sont **non
négociables** : la masse et l'équipage que tu proposes doivent être **plausibles pour ces
volumes-là**. Un chasseur de 2,46 m n'est pas un intercepteur habité de série ; c'est au lore de
rendre cette échelle cohérente, pas aux chiffres de la démentir.

| Coque | Camp | Envergure | Tirant | Longueur | Triangles | Faits de gameplay |
|---|---|---|---|---|---|---|
| **Specter-9** | Helios Vanguard | 1,75 m | 0,65 m | 2,46 m | 35 008 | chasseur du joueur ; bouclier 100 ; 3 vies ; ailes à flèche variable, volets de bord de fuite, tuyères à pétales ; 7 points de tir |
| **Needle Scout** | The Null Choir | 0,65 m | 0,23 m | 1,90 m | 1 612 | 8 profils de vol distincts (20 PV de base) ; l'ennemi le plus commun |
| **Crescent Interceptor** | The Null Choir | 1,10 m | 0,17 m | 1,60 m | 2 665 | 18 PV, le plus rapide (4,0 u/s), trajectoire en crochet |
| **Choir Harvester** | The Null Choir | 4,54 m | 1,36 m | 7,00 m | 16 156 | mini-boss, 420 PV, cinq pétales et trois bras articulés autour d'un noyau |
| **The Pale Leviathan** | The Null Choir | 7,00 m | 2,39 m | 8,77 m | 16 838 | vaisseau-amiral, 950 PV, 4 phases, anneau incomplet et noyau exposé |

## Contraintes

- **IP** — interdits habituels de `CLAUDE.md` §« Interdictions clés » : aucun nom, aucune référence
  identifiable de Macross, Robotech ou d'une autre licence. Les constructeurs, chantiers et
  désignations que tu inventes doivent être **originaux**.
- **Canon** — les sept noms de la charte §2 sont fixés. Tu peux inventer des **constructeurs** et
  des **matricules**, pas renommer une coque.
- **Ton** — dossier technique militaire : sec, factuel, un peu froid. Côté Null Choir, le registre
  bascule vers l'observation xéno : on ne connaît pas leur constructeur, on classe ce qu'on observe.
  Pas d'emphase héroïque dans une fiche technique — l'héroïsme est ailleurs dans le jeu.

### Contraintes typographiques — impératives (ADR-0012)

L'écran est rendu en **Press Start 2P**, dont les **capitales accentuées sont dessinées en hauteur
de bas-de-casse** : un `É` dans un mot tout en capitales y troue le mot.

- Les champs courts (`designation`, `classe`, `constructeur`, `statut`) s'affichent **tout en
  capitales** : les écrire en **ASCII pur, sans aucun accent** (`DESIGNE`, pas `DÉSIGNÉ`).
- La `notice` s'affiche en casse normale : les **minuscules accentuées sont autorisées et
  souhaitées** (français correct). Éviter seulement une capitale accentuée en début de phrase.
- Aucun caractère `●`, `■`, `→`, `—` : la police ne les a pas. Utiliser `-` et `>`.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `docs/forge/output/codex_hull_datasheets.md` | les cinq fiches, sous forme d'**un tableau markdown par coque**, champs nommés exactement comme ci-dessous |

Pour **chacune** des cinq coques, exactement ces champs :

| Champ | Format | Exemple de forme attendue |
|---|---|---|
| `designation` | ASCII majuscules, court | matricule de coque, ex. forme `HV-09` |
| `classe` | ASCII majuscules, ≤ 34 caractères | le rôle tactique, ex. forme `CHASSEUR LEGER D'INTERCEPTION` |
| `constructeur` | ASCII majuscules, ≤ 28 caractères | chantier ou origine ; côté Null Choir, une classification d'observation |
| `masse_t` | nombre décimal, en tonnes | cohérent avec le volume mesuré |
| `equipage` | entier ≥ 0 | 0 est une réponse valable et intéressante |
| `statut` | ASCII majuscules, ≤ 22 caractères | ex. forme `EN SERVICE`, `MENACE CONFIRMEE` |
| `notice` | 2 à 3 phrases, casse normale, ≤ 320 caractères | ce que le dossier dit de la coque : ce qu'elle fait, ce qui la trahit au combat |

Ajoute en fin de fichier une courte section **« Cohérence »** expliquant en 3 à 5 lignes le
raisonnement d'échelle qui rend les masses plausibles. Elle ne sera pas affichée en jeu ; elle sert
la review.

## Provenance

Le livrable est un document de données, pas un asset chargé par le moteur : **pas de ligne dans
`assets/licenses/ASSET_PROVENANCE.csv`**. Il vit dans `docs/forge/output/`, comme
`graybox_palette.md` et `main_theme_spec.md`.

## Critères d'acceptation

- [ ] Les cinq coques sont traitées, avec les sept champs, nommés exactement comme au tableau.
- [ ] Aucun champ court ne contient de caractère non-ASCII (vérifiable : `grep -P '[^\x00-\x7F]'`
      ne doit rien remonter sur les lignes de champs courts).
- [ ] Les masses sont cohérentes entre elles et avec les volumes mesurés (un Leviathan de 8,77 m
      ne pèse pas le même ordre de grandeur qu'un Needle Scout de 1,90 m).
- [ ] Aucun nom, terme ou désignation renvoyant à une licence existante.
- [ ] Les noms canoniques de la charte §2 sont repris tels quels, sans variante.
- [ ] Les notices distinguent nettement le registre allié (dossier interne) du registre ennemi
      (observation xéno).

## Hors périmètre

- **Ne pas** toucher au code, aux scènes, aux `.tres` ni aux Resources de gameplay.
- **Ne pas** proposer de dimensions, de PV, de vitesse, de score ou de rayon de touche : ces
  valeurs existent, elles sont mesurées ou lues à l'exécution, et une valeur concurrente dans un
  document créerait une deuxième source de vérité.
- **Ne pas** produire d'image, de planche ni de prompt de génération.
- **Ne pas** écrire de lore d'univers au-delà des sept champs (pas de récit de campagne, pas de
  chronologie).
