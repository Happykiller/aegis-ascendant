# BRIEF-0088 — La grande bible de l'univers d'Aegis Ascendant

- **Statut** : livré
  conformité faite : périmètre respecté (rien hors `docs/lore/`), bandeaux d'en-tête présents,
  aucune ligne de provenance requise, deux réflexes IP corrects (un candidat de nom écarté pour
  proximité avec une faction existante, une lune renommée pour un morphème de fantasy connue).
  ⚠️ **Intégration en attente d'une décision de l'opérateur** : le nom de la faction
  (`NULL_CHOIR.md` §1, sept candidats). Les écarts à trancher sont dans `EXPLOITATION.md` §8.
  ⚠️ Ce brief annonçait **douze** répliques enregistrées ; il y en a **quatorze** — `VOX-0003` en
  a ajouté trois entre la rédaction et l'exécution. Erreur du brief, relevée par la forge.
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-28

## Objectif

Écrire **l'histoire complète du monde** d'Aegis Ascendant — d'où vient l'humanité de ce jeu, qui
sont ses factions, d'où sort le Null Choir et pourquoi il attaque, qui sont les gens qui peuplent
cette guerre — et la livrer sous une forme **exploitable écran par écran**, pour que chaque
réplique, chaque briefing et chaque texte du jeu puisse s'y raccrocher au lieu d'être inventé sur
place.

Ce brief **supersede et absorbe `BRIEF-0087`** (la bible actuelle, `docs/lore/BIBLE.md`, 232
lignes). Celle-ci était volontairement minimale : elle reliait l'existant sans rien inventer.
L'opérateur demande maintenant **l'inverse** — « je veux la totale ».

## Contexte

Le jeu a un monde riche **par accident** : des noms de vaisseaux, des unités avec des
comportements, une navigatrice avec un visage et une voix. Mais rien ne dit **pourquoi**. Le
joueur traverse six phases sans savoir ce qu'il défend, contre qui, ni ce qui a déclenché la
guerre. Lyra parle beaucoup et ne raconte rien.

Demande de l'opérateur, dans ses mots : *« créer une histoire complète, cohérente de bout en bout,
qui va être utilisée à travers le jeu à différents moments : pour l'intro, pour chaque écran de
pause, pour expliquer quelle phase à quoi elle sert, pour les lignes de dialogue in game. »* Il
cite en modèle de **structure** l'invasion des Yuuzhan Vong de Star Wars — une civilisation venue
du dehors, avec sa propre logique, sa langue et ses figures — sans demander de la copier.

### ⚠️ AMENDEMENT DU 2026-08-28 — l'échelle est une CAMPAGNE, pas un niveau

Demande de l'opérateur, postérieure à la rédaction de ce brief et qui **prime sur tout ce qui
suit** : *« Le lore que tu es en train de créer doit s'étendre beaucoup plus largement en termes
d'histoire que le simple acte un ou niveau un qu'on fait actuellement. Il va falloir qu'on puisse
dérouler dix, douze niveaux différents. »*

Ce que ça change, et ce n'est pas un détail de dimensionnement :

- **Le niveau qui existe aujourd'hui devient le NIVEAU 1** d'une campagne de dix à douze. Ses six
  phases (`FIGHTER_WAVES → MINI_BOSS → ASTEROID_FIELD → FINAL_BOSS → DOCKING → VICTORY`) ne sont
  plus l'histoire : elles en sont l'**ouverture**.
- **Le Pale Leviathan cesse d'être l'aboutissement.** Il reste le boss du niveau 1, mais il ne peut
  plus être « l'organe avancé de l'assimilation » au sens d'un point culminant — c'est un boss
  d'étape, et le lore doit dire ce qu'il y a **au-dessus de lui**, et ce que sa chute déclenche
  chez l'ennemi.
- **La révélation se ré-étage sur toute la campagne.** L'arbitrage n° 1 ci-dessous (patrouille de
  routine, découverte progressive) valait pour un niveau ; il vaut désormais pour douze. ⚠️
  **Conséquence directe : le niveau 1 doit révéler BEAUCOUP MOINS qu'écrit plus bas.** Si le
  joueur comprend l'invasion au premier boss, il ne reste rien pour les onze suivants. Le niveau 1
  pose une anomalie et une inquiétude, pas une explication.
- **L'Aegis Citadel** — dont le noyau est la cible annoncée de l'ennemi — devient un enjeu de fin
  de campagne, pas une menace hors champ indéfinie.
- **Les personnages ont un arc**, pas seulement une fiche. Qui change entre le niveau 1 et le
  niveau 12, et à cause de quoi ? Qui ne survit pas ? Lyra elle-même est concernée : ce qu'elle
  est vraiment est le genre de révélation qui se garde pour le dernier tiers.

Livrable supplémentaire correspondant : **`docs/lore/CAMPAGNE.md`** (voir la table des livrables).
La longueur cible passe à **900 à 1300 lignes** au total.

⚠️ **Ce que ça ne change PAS** : le jeu ne contient qu'un seul niveau jouable aujourd'hui, et ce
brief n'en commande aucun autre. La campagne est une **charpente narrative** qui dit où l'on va —
elle ne promet aucune mécanique et ne décrit aucun contenu à produire. Chaque niveau se résume en
quelques lignes : son lieu, son enjeu, ce qu'il révèle, son adversaire. Pas de découpage en phases,
pas de composition de vagues, pas de boss spécifié : ce serait du design, et ce n'en est pas la
commande.

### Les trois arbitrages déjà rendus par l'opérateur

Ils ne sont pas à rediscuter ; ils cadrent tout le reste.

1. **L'ouverture est une patrouille de routine, et le titre ne fait que teaser.** *« On peut
   remanier tout, teaser seulement dans le titre, GO pour une grande aventure. »* Le joueur ne
   sait pas, en commençant, qu'il entre dans une invasion. Il part vérifier une anomalie. La
   première vague est une surprise, le Choir Harvester une confirmation, le Pale Leviathan une
   révélation. ⚠️ **Conséquence directe** : les quatre répliques de l'écran-titre, qui annoncent
   aujourd'hui « Le Null Choir avance sur les colonies », **doivent être réécrites** — voir la
   section « Ce qui coûte cher à changer ».
2. **L'origine du Null Choir est libre, et large.** *« Le plus large possible, on peut imaginer
   les chefs, la langue, tout — libre à toi l'imagination, surprends-moi. »* Le canon actuel dit
   « pas de chef, pas de visage » : **cette contrainte est levée par l'opérateur**. Le Choir peut
   avoir une structure, des figures, une langue, une histoire d'avant l'humanité.
3. **Casting complet, Lyra seule à l'écran.** On peuple le monde de vrais personnages — noms,
   personnalités, passés, rapports entre eux — mais **aucun n'a de portrait** : l'`ADR-0035` tient
   sur ce point. Ils vivent dans le lore, dans les briefings, et dans la bouche de Lyra.

## Ce qui est DÉJÀ CANON — intangible

Ces noms sont dans le code, les Resources, les assets livrés et les voix **déjà enregistrées**. Ils
ne se renomment pas. Le lore doit les **expliquer**, pas les remplacer.

| Élément | Ce qu'il est aujourd'hui |
|---|---|
| **Helios Vanguard** | La coalition humaine ; défense interplanétaire des colonies |
| **Arsenal Orbital Talvern** | Le chantier Helios qui construit le Specter-9 |
| **Specter-9** | Le chasseur du joueur, léger, triangulaire |
| **Aurora Spear** | Le porte-chasseur, présent dans ce niveau (lancement + appontage) |
| **Aegis Citadel** | La forteresse mobile dont le noyau est l'objectif final du Choir ; **jamais visitée** dans cette mission (`ADR-0010`) |
| **The Null Choir** | L'ennemi : intelligence collective biomécanique qui **absorbe des structures** |
| **The Pale Leviathan** | Son vaisseau-amiral ; anneau incomplet, noyau visible, blindage qui se répare **de plus en plus mal** à chaque cycle (`ADR-0021`) |
| **Choir Harvester** | Le mini-boss ; trois bras, noyau protégé qui s'ouvre par séquence |
| **Le bestiaire** | Needle Scout, Crescent Interceptor, Leech Drone, Choir Mine, Null Maw, Shield Carrier, Frigate Turret — chacun a une fiche codex et un comportement codé |
| **Lyra Vantella** | Navigatrice // IA guide ; **seul personnage avec un visage à l'écran** (`ADR-0035`) |
| **Wren Adaire**, indicatif **Halyard** | Le pilote. ⚠️ **Jamais prononcé par Lyra**, qui dit « Pilote » |
| **Canal 09** | Le canal de comms sécurisé entre Lyra et le pilote |
| **« Tenir la ligne »** | L'engagement de la Vanguard à rester entre le Choir et les colonies |

## Ce qui est LIBRE — et attendu

C'est le cœur de la commande. Rien de tout cela n'existe aujourd'hui.

### Le monde d'où l'on vient

- **La planète d'origine** : un nom, et ce qu'elle est. L'humanité de ce jeu vient-elle encore de
  la Terre, ou d'un monde qui l'a remplacée ? Depuis combien de temps ?
- **Le système, ou les systèmes** : où se joue cette guerre. Les colonies dont parle Lyra — quelles
  sont-elles, combien, et qu'est-ce qui les tient ensemble ?
- **Une chronologie** : cinq à dix dates qui mènent d'un point de départ à cette mission-ci.
  Assez pour situer, pas une encyclopédie.

### Les factions

Helios Vanguard existe. Ce qu'il lui manque : **contre qui d'autre** elle s'est construite, **qui
la finance**, **qui n'est pas d'accord avec elle**. Une guerre à une seule faction humaine est une
guerre sans politique — et sans politique, un briefing ne peut rien dire d'intéressant. Attendu :
deux à quatre entités humaines aux intérêts distincts, dont l'Arsenal Orbital Talvern, déjà canon,
peut être une.

### Le Null Choir

C'est là que l'opérateur attend d'être surpris. Attendu :

- **Son origine** — d'où il vient, depuis quand, et par quel chemin il est arrivé jusqu'ici ;
- **Pourquoi il attaque**, et pourquoi **des structures** plutôt que des gens : ce point est déjà
  à moitié écrit dans le dépôt (spec §3.3 : le Leviathan « cherche à absorber le noyau de l'Aegis
  Citadel »), il demande une cause, pas une reformulation ;
- **Sa langue** — comment il se coordonne, ce que « le Chant » est vraiment, et ce qu'un humain en
  perçoit. Peut-il être traduit ? Mal traduit ? C'est une matière de dialogue considérable ;
- **Ses figures** : la contrainte « pas de chef » est levée. S'il a une structure, il faut dire
  laquelle, et où le Pale Leviathan s'y situe ;
- **L'histoire de chaque vaisseau ennemi** : les sept unités du bestiaire et les deux boss ne sont
  pas des silhouettes, ce sont des **rôles dans le Chant**. La bible actuelle (§2) en a esquissé
  la lecture — la reprendre, l'approfondir, et donner à chacune ce que l'opérateur demande : d'où
  elle sort, à quoi elle servait avant d'être une arme, pourquoi elle a cette forme-là.

### Les personnages

Un vrai casting, **avec noms, personnalités, passés et rapports entre eux**. Au minimum :

- **Lyra Vantella**, approfondie : ce qu'elle est réellement (une IA ? une personne derrière une
  interface ? autre chose ?), pourquoi elle a un visage, ce qui la lie à ce pilote-ci. Elle porte
  99 % du texte du jeu : c'est le personnage qui mérite le plus de matière ;
- **Wren Adaire / Halyard**, approfondi·e à partir des deux phrases existantes (un avant-poste
  colonial qui a cessé d'émettre après une incursion du Choir) ;
- **Le commandement de l'Aurora Spear** — qui envoie le pilote, et avec quelles arrière-pensées ;
- **Quelqu'un de l'Arsenal Orbital Talvern** — celui ou celle qui a construit ce chasseur ;
- **Un ou deux autres pilotes** — une escadre où le joueur n'est pas seul rend la solitude du
  cockpit lisible.

Pour chacun : ce qu'il veut, ce qu'il cache, et **une phrase que lui seul pourrait dire**.

## La contrainte qui compte le plus : ÇA DOIT S'INJECTER

Un lore qui ne se branche nulle part est un document mort. L'opérateur est explicite : *« On va
pouvoir l'injecter un peu de partout. »* Le livrable doit donc porter, en plus du récit, une
**page d'exploitation** qui dit, pour chaque endroit du jeu, ce que le lore y met :

| Endroit | Ce qui s'y trouve aujourd'hui | Ce que le lore doit y apporter |
|---|---|---|
| **Écran-titre** (`lyra_title.tres`, 4 répliques en boucle) | « Le Null Choir avance sur les colonies » — la guerre y est déjà connue | Un **teaser**, pas une déclaration. Lyra accueille un pilote pour une patrouille, mentionne une anomalie, et n'annonce aucune invasion |
| **Briefing de pause, une page par phase** (`sector_briefings.tres`) | Un titre, deux lignes, trois objectifs | **Pourquoi cette phase existe** dans l'histoire, en plus de ce qu'il faut y faire. C'est le seul écran où le joueur a le temps de lire |
| **Répliques en jeu** (`lyra_ingame.tres`, 10 répliques) | Des annonces d'état (« champ détecté », « réacteur exposé ») | De quoi les **remplacer ou les doubler** par des phrases qui portent l'histoire en même temps que l'information |
| **Rapport de mission**, victoire ET **défaite** | « VICTOIRE » / « DEFAITE » et un score | ⚠️ **La défaite est aujourd'hui muette** : aucune réplique, aucun texte. Que se passe-t-il, dans la fiction, quand le pilote échoue ? |
| **Codex / bestiaire** | Une fiche par coque, dimensions et chiffres | L'histoire de chaque unité, telle que demandée plus haut |

⚠️ **Cette page d'exploitation est un livrable à part entière**, pas une annexe. C'est elle qui
sera lue en premier à chaque fois qu'on écrira une réplique.

## Ce qui coûte cher à changer — le dire, ne pas le faire

Douze répliques sont **déjà enregistrées en voix** (`assets/imported/audio/voice/lyra/`,
demandes `VOX-0001`, `VOX-0002`, `VOX-0003`). Changer leur texte oblige à **re-synthétiser** la
voix et à refaire valider l'écoute par l'opérateur. Ce n'est pas interdit — l'opérateur a
explicitement autorisé le remaniement — mais ça se **chiffre**.

Attendu : une section du livrable qui liste, réplique par réplique, **lesquelles le nouveau lore
oblige à réécrire**, laquelle peut rester telle quelle, et pourquoi. Ne PAS écrire les nouveaux
textes ici : c'est le travail d'une demande `VOX-NNNN` séparée, que le concepteur pilotera.

De la même façon, deux décisions actées seront à amender, et il faut le **signaler** sans y
toucher :

- **`ADR-0035`** pose que Lyra est « le seul personnage du canon » — le casting l'élargit ;
- **`docs/lore/BIBLE.md` §2** pose que le Choir « n'a pas de chef et pas de visage » — l'opérateur
  lève cette contrainte.

Lister ces écarts dans une section « ce que ce lore oblige à rouvrir ». Le concepteur écrira les
ADR.

## Contraintes

- **IP** : aucun nom, silhouette, race, planète, terme ou élément identifiable de Macross,
  Robotech, Star Wars, Warhammer 40 000, Mass Effect, Halo, ou de toute autre licence. Les
  Yuuzhan Vong sont cités par l'opérateur comme **modèle de structure narrative** (une civilisation
  venue du dehors, avec sa logique propre) — **jamais comme matière à recopier**. Un lecteur qui
  connaît Star Wars ne doit reconnaître **aucun** élément.
- **Ton** : celui déjà établi par Lyra (`VOX-0002`, champ `direction`) — sobre, militaire, jamais
  grandiloquent. Une invasion racontée à hauteur de cockpit. ⚠️ « Grande aventure » veut dire
  **ample**, pas **emphatique** : le jeu se joue en une session, et son personnage principal est
  quelqu'un qui garde son calme.
- **Cohérence mécanique** : tout ce que le lore affirme doit être **compatible avec ce que le jeu
  fait déjà**. Le Leviathan a trois cycles et son armure se répare de plus en plus mal ; le
  Harvester ouvre et referme son noyau ; le Null Maw retire la manœuvre sans blesser. Le lore
  explique ces comportements, il ne les contredit pas.
- **Longueur** : c'est la commande la plus ample du dépôt, mais la densité prime. Viser
  **600 à 900 lignes au total**, réparties sur les fichiers ci-dessous. Un fichier qu'on ne
  relit jamais ne sert à rien.

## Texture (ADR-0028)

**Sans objet** — ce livrable est entièrement documentaire (Markdown). Aucun asset graphique,
aucun modèle 3D, aucune demande `TEX-NNNN` n'en dépend. Les planches et coques qui existent déjà
ne sont pas modifiées par ce brief : il en donne l'histoire, pas la forme.

## Livrables (chemins exacts)

Chaque fichier porte le bandeau d'en-tête des pages de lore (`titre`, `type: lore`, `statut:
actif`, `maj: 2026-08-28`).

| Fichier | Description |
|---|---|
| `docs/lore/README.md` | L'index : ce que contient chaque page, et par laquelle commencer selon ce qu'on écrit |
| `docs/lore/BIBLE.md` | **Réécrit** : le grand récit — le monde, la chronologie, la guerre, et ce que cette mission-ci y représente. C'est la page qu'on lit en entier une fois |
| `docs/lore/FACTIONS.md` | Helios Vanguard, l'Arsenal Orbital Talvern, et les autres entités humaines : ce qu'elles veulent, ce qui les oppose |
| `docs/lore/NULL_CHOIR.md` | L'ennemi : origine, mobile, langue, structure, figures — et l'histoire de chacune de ses neuf unités (7 du bestiaire + 2 boss) |
| `docs/lore/PERSONNAGES.md` | Le casting : Lyra, Wren Adaire, le commandement, l'Arsenal, l'escadre. Pour chacun : ce qu'il veut, ce qu'il cache, une phrase que lui seul dirait |
| `docs/lore/CAMPAGNE.md` | **La charpente des dix à douze niveaux** (amendement du 2026-08-28) : pour chacun, son lieu, son enjeu, ce qu'il révèle de l'ennemi, son adversaire, et ce qui change chez les personnages. Quelques lignes par niveau — une charpente, pas un design |
| `docs/lore/EXPLOITATION.md` | **La page d'usage** : par écran et par phase, ce que le lore y injecte. Plus la liste des répliques enregistrées à réécrire, et la liste des décisions à rouvrir |

## Provenance

Documents texte originaux, sans matière première tierce : **aucune ligne de provenance requise**
(pas d'image, pas d'audio, pas de modèle). ⚠️ En revanche, si une source externe a inspiré une
structure, le dire dans le rapport de livraison — pas dans le lore lui-même.

## Critères d'acceptation

- [ ] **Aucun élément de la table « déjà canon » n'est renommé ni contredit** — chacun est
      expliqué par le nouveau lore.
- [ ] La planète d'origine est **nommée**, les factions sont **nommées**, l'origine du Null Choir
      est **expliquée** — les trois demandes littérales de l'opérateur.
- [ ] Chacune des **neuf unités ennemies** (7 du bestiaire + Choir Harvester + Pale Leviathan) a
      son histoire, et cette histoire est **compatible avec son comportement codé**.
- [ ] Le casting comporte au moins **cinq personnages** nommés, chacun avec ce qu'il veut, ce
      qu'il cache, et une phrase qui n'appartient qu'à lui.
- [ ] **`EXPLOITATION.md` couvre les six phases + l'écran-titre + les deux issues du rapport**,
      défaite comprise — c'est le trou narratif le plus visible aujourd'hui.
- [ ] **`CAMPAGNE.md` tient dix à douze niveaux**, chacun avec son lieu, son enjeu, sa révélation
      et son adversaire — et le niveau 1 est bien celui que le jeu contient déjà.
- [ ] **La révélation est étagée sur la campagne, pas consommée au niveau 1.** Vérifiable ainsi :
      ce que le joueur ignore encore à la fin du niveau 1 doit être énumérable, et non vide.
- [ ] Le **Pale Leviathan est repositionné** comme boss d'étape : le lore dit ce qu'il y a au-dessus
      de lui, et ce que sa chute déclenche.
- [ ] La liste des **répliques enregistrées à réécrire** est donnée, avec le coût (re-synthèse).
- [ ] La liste des **décisions à rouvrir** (`ADR-0035`, le « pas de chef ») est donnée, sans que
      le brief y touche.
- [ ] **Zéro élément reconnaissable d'une licence tierce**, Yuuzhan Vong compris.
- [ ] Le ton reste celui de Lyra : sobre, à hauteur de cockpit, jamais épique pour l'être.

## Hors périmètre

- **N'écrit AUCUN fichier de jeu** : pas de `.tres`, pas de `.gd`, pas de `VOX-NNNN.json`, pas de
  modification de `resources/dialogue/`. Le lore est une matière ; le concepteur l'injecte.
- **N'écrit AUCUN ADR** : les décisions à rouvrir sont *signalées*, pas prises.
- **Ne réécrit pas les répliques existantes** : elle les *liste* comme à réécrire, avec la raison.
- **N'invente pas de mécanique de jeu.** Si une idée narrative appellerait une mécanique qui
  n'existe pas, la noter comme piste dans le rapport de livraison — jamais l'affirmer dans le lore
  comme si le jeu la portait.
- **Ne touche pas à `docs/design/bible/`** : c'est la bible du *genre* (référence shoot'em up),
  sans rapport avec la bible narrative malgré le nom.
