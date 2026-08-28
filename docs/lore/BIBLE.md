---
titre: Bible narrative — le pilote, le Null Choir, le fil de la mission
type: lore
statut: actif
maj: 2026-08-28
---

# Bible narrative d'Aegis Ascendant

Ce document relie ce qui existait déjà séparément — factions, coques, palette
(`docs/forge/CHARTE_CREATIVE.md` §2), arc de jeu (`docs/KB/DAF/arc-de-jeu.md`), voix de Lyra
(`docs/forge/voice/VOX-0001`, `VOX-0002`) — en un fil narratif unique. C'est une **matière de
référence**, pas un script : le concepteur y puise pour écrire les répliques qui manquent encore,
il n'y trouve aucune ligne prête à enregistrer.

Rien ici ne renomme, ne redouble ni ne contredit un élément déjà canon. Le seul ajout est celui
explicitement demandé : le nom et l'indicatif du pilote.

## 1. Le pilote

**Wren Adaire**, indicatif **Halyard**.

Un *halyard* est le cordage qui hisse une voile ou un pavillon — un mot de tradition navale,
raccord discret avec l'image déjà en place autour de la Vanguard (Aurora **Spear**, la citadelle
qui **tient la ligne**, l'Arsenal Orbital Talvern qui construit ses coques comme un chantier
naval). Ce n'est ni un titre héroïque ni un jeu de mots sur le Specter-9 : un indicatif de plus
parmi d'autres pilotes de la Vanguard, qui n'a pas besoin d'être remarquable pour exister.

Adaire a grandi sur un avant-poste colonial qui a cessé d'émettre après une incursion du Null
Choir. Engagé·e dans la Vanguard, formé·e en accéléré, iel prend aujourd'hui les commandes d'un
Specter-9 sorti de l'Arsenal Orbital Talvern — et c'est la première sortie où Lyra Vantella le/la
guide, ce qui recadre les quatre répliques d'accueil (`VOX-0001`) : « Bienvenue, Pilote » n'est
pas une formule générique, c'est littéralement une présentation.

⚠️ **Ce nom et cet indicatif sont pour la fiction — codex, journal de bord, écran de résultats —
jamais pour la bouche de Lyra.** La direction de `VOX-0001`/`VOX-0002` est explicite : « elle dit
*Pilote*, jamais un prénom ». Aucune réplique future ne doit lui faire prononcer « Adaire » ni
« Halyard ». Pas de visage à l'écran non plus : le pilote reste vu de l'extérieur, par ce qu'il
fait et ce qu'on lui dit — cf. `ADR-0035`, où Lyra est « le seul personnage du canon ».

## 2. Le Null Choir — ce qu'il veut

Le Null Choir n'a pas de chef et pas de visage : c'est une intelligence collective biomécanique
(charte §2), et une bible qui lui donnerait un porte-parole nommé trahirait ça. Ce qu'on peut lui
donner, c'est une **faim**, et elle est déjà écrite ailleurs dans le dépôt sans avoir été formulée
comme telle : la spec dit du Pale Leviathan qu'il « cherche à absorber le noyau de l'Aegis
Citadel » (§3.3). Ce n'est pas une conquête de territoire — c'est une conquête de **structure**.

Le Choir ne s'intéresse pas aux colonies pour leurs habitants : il s'intéresse à ce qu'elles ont
organisé — réacteurs, forges, grilles d'énergie, tout ce qui tient une forme cohérente dans le
vide. Assimiler, pour lui, c'est faire entrer une structure ordonnée dans son propre chant plutôt
que la détruire au hasard. C'est un motif qui explique, sans un mot de plus, pourquoi il choisit
systématiquement pour cibles des cœurs, des noyaux, des réacteurs — Choir Harvester, Pale
Leviathan, l'objectif final annoncé sur l'Aegis Citadel — et jamais une simple destruction de
masse. Une colonie tombée n'est pas un massacre raconté : c'est une ressource absorbée, au ton
sobre qu'exige le reste du jeu.

Le vocabulaire des unités porte déjà cette idée sans qu'il ait fallu l'inventer : tout ce qui
appartient au Choir se nomme d'après le **Chant** — la manière dont l'essaim se coordonne sans
commandement central, par résonance plutôt que par ordre. Chaque unité déjà nommée dans le
bestiaire (`resources/enemies/*.tres`) y tient un rôle précis, lisible dans sa propre fiche de
comportement :

| Unité (déjà canon) | Ce qu'elle EST dans le Chant |
|---|---|
| **Needle Scout** | La voix la plus nombreuse et la plus interchangeable : coques identiques, production industrialisée (fiche codex). Le Chant sonde une ligne avant de s'y engager. |
| **Crescent Interceptor** | Une réponse réflexe, rapide et jetable — elle frappe, repart, ne tient jamais un cap. Le Chant corrige, il ne raisonne pas. |
| **Leech Drone** | Une pulsion isolée qui poursuit sans relâche et se consume en mordant. Le Chant, quand il perd le contact, ne renonce pas — il s'accroche. |
| **Choir Mine** | Une note plantée à l'avance, qui n'existe que pour un endroit précis et ne répond que si on la dérange. Le Chant a une mémoire du terrain, pas seulement des cibles. |
| **Null Maw** | Une faim sans dents : elle ne blesse pas, elle retire la liberté de manœuvrer. C'est l'image la plus directe de ce que veut le Choir — pas tuer, *inclure*. |
| **Shield Carrier** | La preuve que rien n'agit seul ici : elle ne menace jamais par elle-même, elle rend invulnérable ce qui l'entoure. Abattre une unité isolée ne veut rien dire tant que sa protectrice vit. |
| **Choir Harvester** (mini-boss) | Un prototype de la faim à plus grande échelle : un assemblage qui ne ressemble à aucun autre (codex), envoyé consolider ce qu'un secteur contient avant l'arrivée du corps principal. |

**Le Pale Leviathan** n'est ni un général ni un individu — c'est l'endroit où le Chant se fait le
plus dense, l'organe avancé de l'assimilation elle-même. Son noyau visible n'est pas un point
faible accidentel : c'est la partie du Choir la plus proche d'une mémoire, la trace de tout ce
qu'il a déjà absorbé pour prendre sa forme actuelle. C'est pour ça que son blindage **se répare de
plus en plus mal à chaque cycle** (`ADR-0021`) — narrativement, ce n'est pas une carapace qui
s'use : c'est une mémoire qui perd sa cohérence à mesure qu'on lui arrache ce qu'elle avait
intégré. Le Leviathan ne veut donc pas *vaincre* le pilote : il veut *atteindre* le noyau
énergétique de l'Aegis Citadel, exactement comme il a déjà atteint d'autres cœurs avant lui. Le
combat que joue le pilote est ce qui l'en empêche, pas une fin en soi pour le Choir.

## 3. Le déroulé narratif de la mission

Arc fixé (`docs/KB/DAF/arc-de-jeu.md`) : `FIGHTER_WAVES → MINI_BOSS → ASTEROID_FIELD →
FINAL_BOSS → DOCKING → VICTORY`. Pour chaque étape : l'enjeu narratif, le point de vue du pilote,
celui de Lyra, et une matière pour ses répliques — pas un script.

### 0. Avant la première vague — ⚠️ AUCUNE RÉPLIQUE AUJOURD'HUI, PRIORITAIRE

*Narrativement* : le sas s'ouvre, le Specter-9 quitte l'Aurora Spear. C'est le moment où « le Null
Choir avance sur les colonies » (déjà dit à l'accueil, `VOX-0001`) cesse d'être une phrase de
briefing et devient un secteur précis, devant soi.

- **Le pilote** : première sortie réelle sous la garde de cette navigatrice précise — l'accueil
  n'était pas une formalité, c'était une présentation qui engage maintenant.
- **Lyra** : elle bascule du registre « accueil » (regardée) au registre « secteur » (entendue
  par-dessus le combat, `VOX-0002`) — c'est la **première fois** que sa voix doit porter sans
  qu'on la regarde.
- **Matière pour Lyra** : confirmer le verrouillage télémétrique et nommer ce qui va suivre sans
  grandiloquence — la même sobriété que « Liaison de navigation établie » à l'accueil, mais
  tournée vers l'instant présent plutôt que vers la présentation. Elle peut aussi ancrer l'enjeu
  personnel du pilote sans jamais le nommer : rappeler que la Vanguard tient la ligne, pas encore
  que *ce* secteur est celui d'où le pilote vient — ça, ce sera pour un texte plus tardif, si le
  concepteur choisit de l'écrire.

### 1. FIGHTER_WAVES — la patrouille avancée (répliques existantes : `waves_cleared`)

*Narrativement* : les Needle Scout et Crescent Interceptor sondent la ligne — la voix la plus
nombreuse et la plus jetable du Chant, envoyée en éclaireur avant tout ce qui vient ensuite
(cf. §2). Ce n'est pas encore une bataille décisive, c'est un test de la ligne elle-même.

- **Le pilote** : premier contact réel, où l'instinct fait tout — enchaîner, encaisser, apprendre
  la cadence de son propre appareil sous tir.
- **Lyra** : elle observe une ligne qui tient, pour l'instant — c'est le moment où elle construit
  sa confiance dans ce nouveau pilote autant que l'inverse.
- **Ce qui existe déjà** (`resources/dialogue/lyra_ingame.tres`, clé `waves_cleared`) : « Secteur
  dégagé, Pilote. Quelque chose de plus gros arrive. » La bible n'y ajoute qu'un contexte : ce
  « quelque chose de plus gros » n'est pas une menace anonyme — c'est la première fois que le
  pilote rencontre une unité qui ne se comporte *pas* comme de l'essaim (cf. §2, Choir Harvester).

### 2. MINI_BOSS — le Choir Harvester (répliques existantes : `boss_approach`)

*Narrativement* : la première rencontre avec une unité du Chant qui ne fonctionne pas par nombre
mais par patience — elle referme et rouvre son noyau en séquence, elle *travaille* plutôt qu'elle
n'attaque en masse. C'est un aperçu réduit de ce qu'implique « absorber » avant d'en affronter la
pleine échelle.

- **Le pilote** : bascule d'un réflexe de tir permanent vers une lecture de rythme — il faut
  attendre une ouverture plutôt que soutenir un flot continu.
- **Lyra** : elle passe en registre ALERTE pour la première fois du niveau (`VOX-0002`, `mood:
  ALERTE`) — le calme qu'elle garde d'habitude devient le repère qui rend cette alerte crédible.
- **Ce qui existe déjà** : « Signature massive droit devant. C'est lui. Tenez la ligne. » Le
  « lui » est un accord grammatical avec l'appareil qu'elle désigne (le Harvester), pas une
  personnification du Choir — cohérent avec §2 : elle nomme une menace, jamais une personne. La
  bible y ajoute que « tenez la ligne » fait écho, mot pour mot, à la ligne déjà posée à l'accueil
  (« La Vanguard tient la ligne — et vous en êtes ») : ce n'est plus une déclaration de guerre
  abstraite, c'est un ordre concret donné à ce pilote précis.

### 3. ASTEROID_FIELD — le champ (répliques existantes : `asteroid_field`)

*Narrativement* : la traversée qui sépare les deux affrontements majeurs, semée de Choir Mine,
Null Maw et Leech Drone — les trois unités « plantées » du Chant (§2), celles qui n'avancent pas
mais attendent. Le champ lui-même peut se lire comme la trace d'un engagement plus ancien : des
débris parmi lesquels le Chant a déjà laissé ses sentinelles, plutôt qu'un terrain neutre.
⚠️ Idée narrative, pas mécanique : rien n'exige que ce soit dit à voix haute pour fonctionner.

- **Le pilote** : rupture de rythme voulue — après l'urgence des vagues et du mini-boss, une
  phase de patience et de précision, où l'erreur vient de l'impatience plus que de la puissance de
  feu adverse.
- **Lyra** : elle retrouve son registre calme (`VOX-0002`, `mood: CALME`) — elle a une solution
  avant même que le danger soit nommé, ce qui la définit depuis l'accueil (« navigatrice, pas
  hôtesse : elle informe et elle engage »).
- **Ce qui existe déjà** : « Champ d'astéroïdes détecté. Restez mobile, Pilote. Je vais vous
  ouvrir une route sûre. » La bible n'y ajoute qu'un fond : ce que le pilote traverse n'est pas un
  simple obstacle géologique, c'est un secteur déjà visité par le Chant.

### 4. FINAL_BOSS — le Pale Leviathan (répliques existantes : `dive_entered`, `core_exposed`, `core_shielded`, `armour_reformed`)

*Narrativement* : l'affrontement direct avec l'organe avancé de l'assimilation (§2). Ce que le
pilote défend ici dépasse sa propre survie : c'est le noyau énergétique de l'Aegis Citadel, hors
champ, jamais montré, que le Leviathan cherche à atteindre. Le combat entier est ce qui l'arrête
avant qu'il ne l'atteigne — pas une joute personnelle.

- **Le pilote** : l'enjeu cesse d'être local — ce n'est plus « survivre à cette vague » mais
  « empêcher que ça continue plus loin ».
- **Lyra** : c'est la seule phase du niveau où elle passe deux fois en registre ALERTE
  (`dive_entered`, `core_exposed`) — et `core_exposed` reste, par direction explicite, « la seule
  réplique où elle hausse le ton » de tout le niveau. Le contraste avec son calme par défaut est ce
  qui rend chacune de ces deux alertes lisible, jamais la puissance de la voix seule.
- **Ce qui existe déjà** couvre les quatre temps du combat cyclique (`ADR-0021`) : l'entrée dans le
  noyau, l'ouverture du réacteur, sa fermeture, la reformation du blindage. La bible y ajoute un
  fil : chaque « blindage repousse, mais plus mal qu'avant » est la trace, à l'écran, d'une
  mémoire du Choir qui s'effiloche cycle après cycle (§2) — ce n'est pas juste une jauge qui
  baisse, c'est la preuve que ce qu'il a absorbé lui échappe.

### 5. DOCKING — le retour (⚠️ AUCUNE RÉPLIQUE AUJOURD'HUI, PRIORITAIRE)

*Narrativement* : la cascade d'explosions qui suit la chute du Leviathan retombe, l'Aurora Spear
récupère le chasseur en autopilote (`resources/dialogue/sector_briefings.tres`, brief `DOCKING` :
« L'Aurora Spear vous récupère »). C'est une descente de tension, pas une nouvelle péripétie —
le seul moment du niveau où rien ne demande d'action au pilote.

- **Le pilote** : la bascule du combat au silence — plus de commandes à tenir, juste l'attente que
  l'appontage se termine, avec tout ce que ça laisse remonter.
- **Lyra** : premier moment du niveau où son rôle n'est plus de prévenir ou d'ordonner mais
  d'accompagner — un registre qu'elle n'a jamais eu l'occasion de montrer avant cet instant.
- **Matière pour Lyra** : confirmer que l'autopilote a la main (rassurer sans infantiliser),
  situer sobrement ce qui vient d'être empêché — pas « vous avez sauvé la colonie » en grande
  pompe, plutôt un constat factuel dans le même registre que « Liaison de navigation établie » :
  quelque chose qui n'a pas eu lieu parce que le pilote l'en a empêché. Elle peut aussi, pour la
  première fois, laisser passer une trace personnelle très courte — un aparté, pas une déclaration
  — cohérente avec « elle informe et elle engage », jamais avec de l'emphase.

### 6. VICTORY — l'écran de résultats (⚠️ AUCUNE RÉPLIQUE AUJOURD'HUI, PRIORITAIRE)

*Narrativement* : le rapport de mission (`MissionReport`), formel, hors du cockpit — le seul
endroit du jeu qui ressemble à un débriefing plutôt qu'à une transmission en direct.

- **Le pilote** : sort du rôle qu'il vient de tenir ; c'est un compte-rendu qu'on lit, pas un
  moment qu'on vit.
- **Lyra** : dernière apparition du niveau — l'occasion de refermer ce qu'elle a ouvert à
  l'accueil sans le répéter mot pour mot.
- **Matière pour Lyra** : un ton de clôture professionnelle, pas triomphal — le Null Choir n'est
  pas vaincu dans l'absolu, seule cette avant-garde l'a été (cohérent avec §2 : le Choir est une
  faim continue, pas un adversaire qu'on épuise en une sortie). Elle peut reconnaître la
  performance du pilote sans lyrisme, et laisser entendre que la ligne tient *parce que* ce pilote
  a tenu, sans promettre une suite qui n'existe pas encore dans le jeu.

## 4. Lexique narratif

| Terme | Ce qu'il désigne dans la fiction |
|---|---|
| **La ligne** | Pas une frontière tracée : l'engagement de la Vanguard à rester entre le Null Choir et les colonies. « Tenir la ligne » se dit d'un secteur comme d'un pilote — c'est la même promesse à deux échelles. |
| **Canal 09** | Le canal de comms sécurisé sur lequel Lyra s'adresse au pilote (`VOX-0001`, « Comms sécurisées, canal 09»). Un détail technique volontairement laissé sans emphase — le genre de précision qu'une vraie navigatrice donnerait en passant. |
| **Le Chant** | La façon dont le Null Choir se coordonne : par résonance collective, sans commandement central (cf. §2). N'est jamais prononcé par Lyra ni affiché en jeu — c'est un mot d'analyse pour le concepteur, pas un terme du monde diégétique. |
| **Absorber / assimiler** | Le vocabulaire du Choir face à une structure organisée (réacteur, noyau, grille d'énergie) — jamais de destruction gratuite. Sert à décrire son comportement sans en faire un adversaire théâtral. |
| **Aurora Spear** vs **Aegis Citadel** | Deux vaisseaux distincts, à ne pas confondre dans une réplique : l'Aurora Spear est le porte-chasseur, présent dans ce niveau (lancement, docking) ; l'Aegis Citadel est la forteresse dont le noyau est l'enjeu final du Choir, jamais visitée dans cette mission — elle reste une menace hors champ, pas un décor jouable (`ADR-0010`). |
| **Secteur** | L'unité de découpage narratif du niveau — chaque phase de l'arc correspond à un secteur annoncé par Lyra ou par le briefing de pause, jamais à un lieu nommé de façon définitive. |

## Limites et choix assumés

- Le pilote reste **délibérément sous-défini au-delà de son nom, de son indicatif et de deux
  phrases de passé** : le brief l'exige (« vu de l'extérieur, jamais un visage à l'écran »), et
  c'est aussi ce qui laisse au concepteur la marge d'écrire n'importe quelle réplique de Lyra sans
  se heurter à un détail biographique déjà fixé ici.
- Le lexique n'introduit qu'un seul terme réellement nouveau (« le Chant ») ; tout le reste
  reformule ou relie du canon existant plutôt que d'en ajouter.
- Les idées de répliques pour DOCKING et VICTORY restent volontairement générales : la tonalité
  exacte (longueur, niveau d'émotion) dépend de décisions de mise en scène (musique, timing HUD)
  qui ne sont pas du ressort de cette bible.
