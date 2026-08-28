---
titre: HISTORY — index chronologique des sujets abordés
type: index
statut: actif
maj: 2026-08-28
---

# Historique des sujets

Une ligne par **session utile** — pas un journal de commits, git le fait déjà. Ce qu'on cherche ici :
« a-t-on déjà creusé ce sujet, et qu'en est-il sorti ? »

Les lignes antérieures au 2026-08-23 sont **reconstituées** à partir des dates portées par les ADR
et par `docs/BACKLOG.md` : elles sont datées de façon fiable, mais ne racontent que ce qui a été
acté, pas ce qui a été exploré.

| Date | Sujet | Ce qui en est sorti | Traces |
|---|---|---|---|
| 2026-07-11 | Fondations : moteur, environnement, commandes, délégation créative, quarantaine IP | 5 ADR d'un coup ; le cadre de travail du projet | [ADR-0001 à 0005](../decisions/) |
| 2026-07-12 | Fond spatial, audio, chaîne 3D Blender | Nébuleuse procédurale (les SVG picturaux sont écartés), banque de cues + musique adaptative, pipeline `.glb` déterministe | [ADR-0006](../decisions/ADR-0006-fond-spatial-procedural.md), [0007](../decisions/ADR-0007-pipeline-audio.md), [0008](../decisions/ADR-0008-pipeline-3d-blender.md) |
| 2026-07-19 | **Un seul vaisseau** : la transformation en forteresse est supprimée | Nouvel arc `FIGHTER_WAVES → MINI_BOSS → FINAL_BOSS → DOCKING → VICTORY` ; référence d'inspiration réinstaurée | [ADR-0010](../decisions/ADR-0010-un-seul-vaisseau-docking-final.md), [ADR-0009](../decisions/ADR-0009-reference-ip-reinstauree.md), [DAF/arc-de-jeu.md](DAF/arc-de-jeu.md) |
| 2026-07-20 → 21 | Détail des coques, textures, écrans, silhouette du Specter-9 | Budgets de coque, textures déverrouillées, langage d'interface unifié, exception IP unique et actée | [ADR-0011 à 0014](../decisions/) |
| 2026-07-22 | Bestiaire, et la luminosité qui manquait | Le post-traitement rétro **pivotait son contraste à 0,5 sur une image entièrement sombre** : il n'était qu'un assombrisseur. +25,8 % mesurés sur la coque du joueur | [ADR-0015](../decisions/ADR-0015-bestiaire-catalogue-de-coques.md), [ADR-0016](../decisions/ADR-0016-luminosite-le-contraste-pivotait-a-0-5.md) |
| 2026-07-23 → 24 | Le Pale Leviathan : conception, silhouette, câblage, puis **coupe au playtest** | Boss à 4 phases sur conditions matérielles ; combat ramené de ~3 min à ~67 s ; lisibilité HUD + coquille qui tourne | [ADR-0017](../decisions/ADR-0017-plume-d-echappement.md), [ADR-0018](../decisions/ADR-0018-le-boss-final-se-demonte.md), [ADR-0019](../decisions/ADR-0019-le-leviathan-coupe-au-playtest.md) |
| 2026-08-23 | Reprise après un mois : revue d'état, fuites de test, mise en place de la KB | Dépôt à jour et vert (279 tests) ; **789 objets fuités** attribués à un seul fichier de test et supprimés ; backlog recalé ; création de `docs/KB/` et du skill `/cloture` | [REGLES/normes.md](REGLES/normes.md), `.claude/resources/pratique-verifier-par-test.md`, [MOTEUR.md](MOTEUR.md) |
| 2026-08-25 | Première **partie jouée** du boss en cycles, et la jauge qui bouclait | Équilibrage d'`ADR-0021` **acquis** ; mais le HUD recevait `structure_ratio()` (la cible courante, qui se remplit à chaque bascule) au lieu de `fight_ratio()` — six remplissages lus comme une boucle. La mesure juste existait et n'allait qu'à la **musique** | [ADR-0023](../decisions/ADR-0023-la-jauge-du-boss-montre-le-combat.md), [plan 2026-08-25](../plans/2026-08-25-boss-pale-leviathan.md), `tests/unit/test_leviathan_hud_relay.gd` |
| 2026-08-25 | Le flux du boss, dimensionné avec la cadence de l'armure | Playtest à puissance MAX : six plongées au lieu de trois. Une seule hypothèse de dps servait une cible large (les plaques) et une petite cible mobile (le flux) ; l'invariant se comparait à elle-même et validait à 99 % de son plafond | [ADR-0024](../decisions/ADR-0024-le-flux-a-sa-propre-cadence-de-reference.md) |
| 2026-08-25 | On entre VRAIMENT dans le noyau, et trois cycles deviennent une construction | La plongée était une sphère de 7 m retournée autour du boss : le chasseur n'allait nulle part. Zone dédiée + iris à volets (2 briefs de forge). Puis : aucun `flux_health` ne pouvait donner trois cycles (600 à 1200 PV placés par plongée selon la partie) — on plafonne le passage | [ADR-0025](../decisions/ADR-0025-on-entre-dans-le-noyau.md), [ADR-0026](../decisions/ADR-0026-trois-cycles-par-construction.md), `BRIEF-0082`, `BRIEF-0083` |
| 2026-08-25 | Le rangement documentaire : plans, briefs et backlog jamais fermés | Constat de l'opérateur, mesuré : **32 briefs livrés sur 37 portaient un statut faux**, deux documents morts dans `docs/`, et le backlog contenait **deux copies divergentes** de ses sections P0-P4. Un état tenu à la main rouille : `audit-docs.sh` le **dérive** du dépôt. Chantier du boss clos et archivé, plan du bestiaire repris (une seule session désormais), `/cloture` corrigé — son périmètre annonçait un chemin et un remote faux | [REGLES/consignes.md](REGLES/consignes.md), [MOTEUR.md](MOTEUR.md), `scripts/audit-docs.sh` |
| 2026-08-25 | **Une phase entre les deux boss** : le champ d'astéroïdes | Deux manques comblés d'un coup — trois unités du bestiaire (Choir Mine, Null Maw, Leech Drone) livrées et jouées **nulle part**, et deux boss dos à dos sans respiration. Revient sur le découpage d'`ADR-0010`, qui avait *supprimé* une phase. Second `WaveSpawner` **endormi** plutôt que de toucher la classe qui marche ; `FORTRESS_AWAKENING` réemployé — un lit musical rendu, payé, et **orphelin** depuis six semaines sans que rien ne le signale | [ADR-0027](../decisions/ADR-0027-une-phase-entre-les-deux-boss.md), [plan inter-boss](../plans/2026-08-25-phase-inter-boss-survol-de-lune.md), `tests/unit/test_asteroid_field_wave.gd` |
| 2026-08-25 | Le décor de la phase inter-boss bascule : on survole une lune | Le fond CÈDE LA PLACE au lieu de s'additionner — décision de budget autant que de mise en scène, et l'échange est gagnant (−0,200 ms/image). Trois défauts trouvés **en regardant** (lune rose qui noyait le chasseur, cratères qui flottaient au limbe, rocher qui frôlait le vaisseau), un quatrième trouvé **par le test** avant tout rendu : le ciel du survol aurait masqué ses propres rochers, en silence | [ADR-0027](../decisions/ADR-0027-une-phase-entre-les-deux-boss.md), `scripts/vfx/moon_flyby.gd`, `tests/unit/test_moon_flyby.gd`, [howto-mesurer-la-perf](../../.claude/resources/howto-mesurer-la-perf.md) |
| 2026-08-25 | Le ciel qu'on ne montre pas mais qu'on paie, et les impacts sur la lune | Le survol réglait `nebula_strength` à 0,12 en croyant éteindre la nébuleuse : le shader calcule ses cinq champs de bruit **inconditionnellement** et ne fait que multiplier le résultat — **un uniforme à 0,12 n'économise rien**. Un vrai chemin (`deep_sky`) fait tomber la phase de 0,738 à **0,323 ms**, un tiers du fond habituel. Puis les impacts, en VFX scripté hors `VFXManager` (question d'échelle : la lune fait 60 unités de rayon). ⚠️ Un tir isolé du témoin avait donné 1,535 ms au lieu de 0,945 : **une mesure unique ne vaut rien sans sa dispersion** | [ADR-0027](../decisions/ADR-0027-une-phase-entre-les-deux-boss.md), `shaders/space_background.gdshader`, `scripts/vfx/moon_flyby.gd` |
| 2026-08-25 | Une **bible de référence du genre**, constituée depuis le web | Six pages qui confrontent ce que le shoot'em up a établi à l'état RÉEL de notre code. Trois constats : les **boss sont la partie la mieux tenue** — et chacun de leurs points l'a été après un playtest, jamais du premier coup ; le **score est le plus grand écart** (nous avons un compteur, le genre y voit un système), mais rien ne dit que nous le voulions ; et le genre nomme deux garde-fous anti-spirale de la mort que nous n'avons **jamais vérifiés** | [`docs/design/bible/`](../design/bible/README.md) |
| 2026-08-25 | Le porteur de bouclier, de la coque au champ visible | Son comportement etait code et teste depuis deux jours, mais l'unite n'avait **ni Resource, ni scene, ni coque** : c'est `BRIEF-0046`, jamais execute, qui bloquait le lot 4 — pas l'equilibrage. Coque forgee, integree, deux exemplaires dans la vague (le premier ENSEIGNE le mecanisme seul, le second le fait payer). ⚠️ Puis le vrai manque : la **portee ne se voyait pas**, donc on subissait la bulle au lieu de jouer contre. C'est un ANNEAU et non un dome — trois essais de volume ont tous rendu un aplat, condamnes par leur SURFACE (bloom + `lift` de 1,25 du post-traitement) et non par leur reglage | [ADR-0027](../decisions/ADR-0027-une-phase-entre-les-deux-boss.md), `BRIEF-0046`, `tests/unit/test_enemy_shield.gd`, [howto-verifier-un-rendu](../../.claude/resources/howto-verifier-un-rendu.md) |

> Découper par année (`HISTORY/README.md` + `HISTORY/2026.md`) au-delà de ~200 lignes.

## 2026-08-26 — la phase 2 devient regardable, et cinq mécaniques cessent d'être muettes

Journée de rendu et de lisibilité, à haute densité de corrections.

**Ce qui a été livré** : le raccord entre les phases (un voile, plus de clignotement) et la
respiration avant le boss final — le seul ❌ que la bible de design portait. Le décor de survol
forgé remplace sa doublure, habillé de textures livrées par l'opérateur. L'impact du bolide est
refait cinq fois avant de trouver sa forme : une roche peinte, un sillage filamenté, un nuage de
particules. Et un dépôt public de releases, avec un livrable Windows **en un seul fichier**.

**Ce que ça a coûté, et qui est désormais écrit** :

- [howto-verifier-un-rendu](../../.claude/resources/howto-verifier-un-rendu.md) — **mesurer la
  distance de l'OBJET, pas du décor derrière lui** (96,5 unités contre 38,1 : 7,9 px contre 20).
  Cinq itérations, plus un brief de forge entier bâti sur le chiffre faux. Et **juger à 1:1** :
  une capture réduite pardonne exactement le défaut cherché.
- [DAF/signaux](DAF/signaux.md) — **la loi des signaux**, tirée de cinq mécaniques prises en défaut
  le même jour : un effet qui ne se montre pas se lit comme un défaut, et un signal **mal lu** est
  pire qu'un signal absent.
- [ADR-0028](../decisions/ADR-0028-la-texture-est-une-etape.md) — la texture devient une **étape**
  du process, avec son contrat d'expression de besoin. Et sa règle jumelle, née le même jour :
  **une surface se texture, un VOLUME se peuple**.
- [pratique-godot-ce-qui-ne-compile-pas](../../.claude/resources/pratique-godot-ce-qui-ne-compile-pas.md)
  — deux fautes qui **compilent** : un nom de propriété faux (`check.sh` reste vert, la fonction
  s'interrompt au milieu, le symptôme ressemble à un comportement plausible) et une **lambda qui
  capture par valeur**.
- [pratique-ecrivain-unique](../../.claude/resources/pratique-ecrivain-unique.md) — **récidive** :
  le second écrivain n'est pas seulement l'autre agent, c'est **le sous-agent qu'on vient de
  lancer**.

## 2026-08-27 — la bible de design passe de six à treize pages

Recherche web à la demande de l'opérateur, pour **aller plus loin** que les six pages du 2026-08-25 :
piliers, boucle de jeu, règles et systèmes, expérience joueur, patterns, level design, lexique. Même
coupe qu'avant — *ce que le métier dit* / *l'état réel du code* / *l'écart* — et les états « chez
nous » sont **vérifiés fichier par fichier**, jamais supposés.

**Ce que l'audit a trouvé, et qui n'était documenté nulle part** :

- **Le pilier D de la spec §1.4 est orphelin** depuis `ADR-0010` (2026-07-19) : il décrit le passage
  au pilotage de la forteresse, supprimé après usage. Un pilier qui nomme une **fonctionnalité**
  meurt avec elle — c'est pour ça que le métier les veut formulés en **ressenti**.
  → [`bible/07`](../design/bible/07-piliers-et-intention.md)
- **`FAN` et `AIMED` ne sont employés par aucune unité de vague.** `fire` vaut `SINGLE` par défaut et
  **aucun `.tres` d'ennemi ne le surcharge**, sauf trois `NONE` et un `RADIAL`. Les neuf Needle
  Scout tirent tous une balle droite : le seul schéma qui punit l'immobilité en vague est écrit,
  testé, et jamais joué. Deux lignes de `.tres` le mettraient en jeu.
  → [`bible/11`](../design/bible/11-patterns-de-tir.md)
- **Le jeu n'a que des boucles de rétroaction positives**, et **aucune ressource ne se dépense** :
  pas d'économie, donc aucune décision d'arbitrage dans la micro-boucle. Overdrive (§9.4), arme
  secondaire (§9.3) et focus (§7.1) sont dans le pire des états — *prévus, absents et silencieux*.
  → [`bible/09`](../design/bible/09-regles-et-systemes.md)
- **`shake_multiplier` est codé mais injoignable** : la spec §7.3 exige une secousse désactivable, le
  code sait le faire (`CameraDirector`), le menu d'options n'expose que 4 volumes et la
  pixelisation. Manque **une ligne d'UI**. Idem manette (§7.2) et remappage (§7.1) : `InputBootstrap`
  n'enregistre **aucun événement joypad**. → [`bible/10`](../design/bible/10-experience-joueur.md)
- Deux constats mineurs mais vérifiés : la **cadence de récompense est déterministe** (un bonus tous
  les 4 ennemis, un Power Core tous les 16 (12 avant le playtest du soir) — donc indexée sur le **nombre d'ennemis**, pas sur le
  temps), et la **parité de l'éventail visé du boss change toute seule** à chaque phase
  (`3 + phase` : impair, pair, impair), ce qui rend la phase 1 plus permissive que la phase 0 pour
  ce pattern.

**Rien n'a été décidé** : la bible n'est pas un cahier des charges, et les quatre constats
ci-dessus attendent l'opérateur. Ils sont rappelés en tête de
[`bible/README`](../design/bible/README.md).

### Puis la bible change de nature : d'un état des lieux à un corpus de lois

Un rapport d'audit externe est remis le même jour ([`docs/design/AUDIT-2026-08-27-bible-supreme.md`](../design/AUDIT-2026-08-27-bible-supreme.md),
importé et **vérifié affirmation par affirmation** — aucune erreur factuelle). Il recommande une
« Bible suprême » qui deviendrait le **contrat produit** d'Aegis, au-dessus de la spec et des ADR.

**L'opérateur tranche autrement, et c'est la décision structurante du jour** :

> « la bible doit pouvoir être suivie par n'importe quel jeu de shoot vertical comme le nôtre, c'est
> un document de référence, une table de lois et règles **universelle** pour faire un bon jeu de
> shoot vertical » — et « c'est pas un plan d'implémentation ».

D'où une bible **réécrite en corpus de lois** : 88 lois identifiées (`LOI-PAT-03`) et graduées en
quatre forces — **LOI** (48, respect exact), **CONTRAINTE** (15, fourchette), **INTENTION** (17,
résultat imposé, moyens libres), **RÉFÉRENCE** (8, jamais une obligation). Le dossier ne contient
plus **aucune** valeur, aucun nom de fichier, aucun jeu : il se copie tel quel vers un autre projet.

Tout le spécifique Aegis — les anciennes sections « chez nous » et « l'écart » — part dans
[`docs/design/CONFORMITE-AEGIS.md`](../design/CONFORMITE-AEGIS.md), qui cite les lois par
identifiant et distingue **écartée** (choix assumé) d'**absente** (dette). Cinq écarts y appellent
une décision, et trois gestes n'attendent rien.

⚠️ **Trois lois ne viennent d'aucune source publique du genre** : `LOI-EXP-09` (le contrat
SEE/UNDERSTAND/FEEL/ANTICIPATE/DECIDE, et sa ligne « à ne jamais produire »), `LOI-EXP-12`
(vérification ≠ validation) et le vocabulaire des quatre forces — ils viennent du rapport d'audit.
Et `LOI-EXP-08` est une **loi de terrain** : elle est née des cinq mécaniques muettes du 2026-08-26,
pas d'une lecture.

**Ce qui a été refusé du rapport, et pourquoi** : le renversement de la hiérarchie de vérité (la
Bible n'est pas le contrat produit d'Aegis, donc `SPEC → ADR → KB` reste en place) ; l'appareil de
traçabilité `REQ ↔ VAL ↔ preuve` (hors nature d'un document de lois) ; la correction du `README.md`
— « le README est un document pour les opérateurs, la KB porte déjà ce qu'il faut ».

### Le soir : un playtest, et le mouvement cesse d'être sur rails

Partie complète jouée à la main (rang S, sortie propre). Les cinq changements de la journée
passent sans remarque ; quatre retours en sortent, tous vérifiables dans le code.

**Trois sont livrés le soir même** :

- **La plongée sortait au minuteur.** Une fois le quota de dégâts atteint, le code disait
  lui-même « les tirs portent, ils ne comptent plus » — et la sortie attendait `dive_time = 5 s`
  fixes, jauge gelée. ⚠️ `ADR-0026` demandait pourtant **l'inverse** en toutes lettres (« mieux
  jouer raccourcit chaque plongée ») : ce n'était pas un réglage, c'était **une décision déjà
  prise et jamais appliquée**. Le minuteur reste la sortie de qui n'atteint pas le quota.
- **La puissance montait trop vite.** Mesure : 107 unités dans la vague, un Power Core tous les
  12 kills, donc **niveau 5 au 48ᵉ — 45 % de la vague**. Et 8 Cores distribués quand 4 suffisent :
  la moitié tombait sur un joueur plein et **ne produisait rien**. Passé à un Core tous les 16.
  `KILLS_PER_POWER` devient public : c'est LE nombre d'équilibrage de la montée en puissance.
- **Tout était sur rails** — [`ADR-0029`](../decisions/ADR-0029-la-derive-organique.md). Les
  trajectoires sont des fonctions **pures** sans graine : une nuée volait en miroir. Les figures
  de boss sont **harmoniques**, donc elles bouclaient exactement. Une **graine par instance** sur
  des **périodes non harmoniques** casse les deux, sans rien coûter aux trois garanties de
  pureté d'`ADR-0022`. ⚠️ Le remède **existait déjà dans le dépôt** — `title_stage.gd` fait
  dériver sa caméra sur 11,0 / 7,3 / 17,0 s « sinon l'œil repère la boucle » — et n'avait jamais
  été transposé au bestiaire.

⚠️ **La graine est déterministe, et c'est le point discutable de l'ADR** : varier les unités
entre elles, pas la vague d'une partie à l'autre. Un vrai hasard rendrait le jeu inapprenable, et
la mémorisation est un pilier du genre.

## 2026-08-27 (soir) — la collision devient un moteur, et une loi

Le fil part d'un playtest — « j'arrive à traverser les murs » — et remonte jusqu'à une règle de
projet : **les corps ne se chevauchent pas** ([`REGLES/lois.md`](REGLES/lois.md)). Quatre lots :
la chambre du réacteur, les coques de boss, les vaisseaux entre eux, le décor
([`ADR-0032`](../decisions/ADR-0032-un-module-de-collision-de-plan.md), plan
`docs/plans/2026-08-27-les-corps-ne-se-chevauchent-pas.md`).

Ce que la session a coûté, et qu'il ne faut pas repayer :

- **Corriger après coup, c'est un ressort.** Laisser entrer puis repousser fait entrer *pour de
  bon*, et le saut rejoué contre la commande du joueur se sent comme un aimant. Pire : abandonner
  sa commande dès qu'il TOUCHE un mur lui retire le contrôle **77 % du temps** dans cette phase.
  On glisse d'abord, on ne corrige que ce qui dépasse.
- **Un vaisseau n'est pas un disque.** Décrit par sa demi-envergure, le Specter-9 laissait son nez
  dépasser de 0,38 et traverser. Et **mesurer un `.glb` sans parcourir sa hiérarchie** donne 1,30
  au lieu de 1,752 — deuxième fois, après le 25/08.
- **Trois seuils inventés** dans des gardes vertes (35 % de couverture, 6 s de plongée, 260
  bousculades) ont chacun caché un défaut. Un seuil se lit dans la donnée qui décide.
- **Le couloir entre les deux murs n'est pas un lieu** : le chasseur est toujours aligné, donc
  radialement c'est sa longueur (2,46) qui devrait tenir dans 0,84 de libre. Le labyrinthe est un
  décor, pas un terrain.
- **`total_duration()` mesurait le pire cas** et servait de cible depuis toujours. La durée qui
  décide du rythme est celle d'un joueur de référence, qui sort dès son quota rempli.

Et une correction de l'opérateur qui vaut consigne : **demander une texture doit être un réflexe**
([`REGLES/consignes.md`](REGLES/consignes.md)).
- **2026-08-28** — Chambre du réacteur : après quatre diagnostics chiffrés, l'overlay des
  collisions montre le décor tournant **à l'envers** de sa collision (maillage en miroir + pivot
  négatif). Réécriture de la résolution des contacts (surfaces avec vitesse,
  `move_capsule`), noyau qui se faisait écran à sa propre cible, corps du boss caché mais
  touchable, un seul mur reconstruit, section Options → Débogage. Leçon :
  `.claude/resources/pratique-dessiner-avant-de-raisonner.md`.
- **2026-08-28 (soir)** — *Ce que l'overlay a montré en une partie*, puis une revue de tout le
  dépôt. Trois observations de l'opérateur, trois défauts de modèle ([`ADR-0034`](../decisions/ADR-0034-un-mur-arrete-un-tir.md)) :
  - **Une capsule n'est pas une boîte.** `capsule_blocks()` ajoute le rayon aux DEUX bouts :
    l'étendue vaut `half_length + radius`. La demi-longueur du `.glb` (1,23) versée dans
    `body_half_length` donnait un chasseur de **4,22 dans l'axe pour une coque de 2,46** — et le
    garde de `validate()` refusait précisément la valeur juste (0,35). `PlayerStats.body_reach()`
    porte désormais l'étendue.
  - **Les balles n'étaient testées contre aucune géométrie.** Le blindage du Léviathan était une
    fausse cible de rayon 0,95 posée sur la ligne joueur→noyau : elle attrapait un disque de mur et
    ratait par construction les flux latéraux des canons d'aile. `BulletManager.screens` fait du
    mur un vrai écran. Coût mesuré 1,55 ms/image, ramené à **0,23 ms** par une phase large
    (disque englobant + **trou central**).
  - **Une attaque invisible n'est pas difficile, elle est fausse.** Les missiles du boss n'avaient
    aucun visuel — et mouraient de toute façon à l'image de leur création, le boss tirant depuis
    `y = 11,9` quand le plan s'arrête à 8,0. **On ne retire pas ce qui n'est jamais entré.**
  - Conséquence d'équilibrage : le noyau était calibré contre un joueur qui place ses dégâts, et ce
    joueur n'existait pas. `flux_health` 1600 → 2000 (57 % → 71 % de la bande autorisée).

  Et deux leçons de méthode :
  - **Un test vert peut être mort** — GDScript abandonne la méthode sur un `SCRIPT ERROR` et le
    harnais annonce `[PASS]`. Deux gardes de `test_hud_layout` n'avaient jamais rien gardé.
    `.claude/resources/pratique-un-test-vert-peut-etre-mort.md`.
  - **Un modèle headless peut être structurellement faux sans erreur** : monté sans coque, il
    annonçait 100 % de projectiles perdus là où le jeu instrumenté en comptait **zéro**.
  - **Un témoin A/B se prouve** : deux mesures identiques venaient du même binaire — `export-win.sh`
    passe par `check.sh`, le témoin cassait la porte, et `deploy-win.sh` a rejoué l'exe précédent
    sans un mot. `md5sum build/windows/*.pck` avant de conclure.

  Et la capitalisation elle-même a trouvé de la doc **devenue fausse**, ce que rien ne pouvait
  voir : `MOTEUR.md` pointait encore la fonction `_trace_dive` dans le niveau six heures après
  son déménagement, le backlog portait le chasseur de 4,22, et la loi des corps citait
  la mesure de `.glb` **sans parcours de hiérarchie** — celle-là même contre laquelle elle met en
  garde. D'où `scripts/lint-regles.sh` : les règles dures de `CLAUDE.md` **appliquées** (étape 2/3
  de `check.sh`), pointeurs de doc morts compris, et `godot-reviewer` branché dessus au lieu de les
  redériver en prose.
- **2026-08-28 (nuit)** — *La voix du jeu prend un visage.* Six concepts fournis par l'opérateur
  nomment le personnage : **Lyra Vantella**, navigatrice // IA guide. [`ADR-0035`](../decisions/ADR-0035-la-voix-du-jeu-a-un-visage.md)
  tranche la question posée — « deux modèles 3D animés » — au profit d'une **illustration déformée
  par squelette 2D** : les maquettes validées SONT en 2D, le dépôt n'a aucun pipeline organique, et
  le retro-post écraserait le détail d'un personnage 3D. Trois écrans livrés en trois pas :
  - **l'accueil** — menu en colonne de gauche avec ses sous-titres, bulle de dialogue paginée qui
    s'écrit et **boucle**, oscillogramme repris de `CommsTrace` (celui de la pause, pas un second
    qui dériverait) ;
  - **le HUD** — portrait **en bas à droite** et non à gauche comme la maquette : c'est le seul
    coin libre des cinq panneaux, relevé par l'opérateur et vérifié dans le code. Elle **double**
    la bannière au lieu de la remplacer ;
  - **la pause** — Lyra et les **objectifs de mission** à gauche, menu à droite, et le centre
    laissé au jeu figé. Le jeu ne rappelait son objectif **nulle part** : les bannières durent
    1,6 s, au moment où le joueur esquive.

  Trois manques de référentiel comblés au passage : la charte créative n'avait **aucune section
  personnage**, et il n'existait de gabarit ni pour commander une planche (`docs/forge/characters/`)
  ni pour commander une voix (`docs/forge/voice/`). Le bus `Voice` existait sans sa chaîne comms.

  Et une règle réaffirmée trois fois dans la même soirée : **on nomme, on ne compte pas.** Répliques
  de combat, briefings de secteur — tous cherchés par clé, jamais par rang, parce qu'un rang dans
  une liste qu'on réordonne n'est pas une identité (la leçon des missiles du Léviathan, le matin
  même).
