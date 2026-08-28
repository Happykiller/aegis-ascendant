# La Chambre du Réacteur doit devenir un LIEU — plan daté du 2026-08-27 (soir)

- **Auteur** : session principale, après le playtest de bout en bout de l'opérateur
- **Périmètre** : phase du noyau du boss final (plongée) — géométrie, bornes de jeu, cadrage
- **Ne supersède rien** ; il ferme un point laissé ouvert par
  [`2026-08-27-les-corps-ne-se-chevauchent-pas.md`](2026-08-27-les-corps-ne-se-chevauchent-pas.md)
  (« le couloir n'est pas un lieu — à trancher »).
- **État** : **clos le 2026-08-28** — cinq lots livrés, plongée jouée jusqu'à l'appontage. ⚠️ La cause racine n'était dans aucun lot : le décor tournait à l'envers de sa collision (voir `pratique-dessiner-avant-de-raisonner.md`). Reste ouvert, au backlog : remettre ou non un second mur

> ⛔ **AVERTISSEMENT DU 2026-08-28 — le chiffre qui fonde ce plan était faux.**
> Tout le dimensionnement ci-dessous part d'un chasseur de **4,22 × 1,76**. Le corps réel fait
> **2,46 × 1,76** : `PlaneCollider.capsule_blocks()` ajoute le rayon aux DEUX bouts du segment, et
> la demi-longueur du `.glb` avait été versée telle quelle dans `body_half_length`. Le chasseur
> était donc décrit **71 % trop long** dans l'axe (voir
> [`ADR-0034`](../decisions/ADR-0034-un-mur-arrete-un-tir.md)).
>
> **Le raisonnement d'époque est laissé intact** — c'est un document daté, et le réécrire
> falsifierait le compte rendu. Mais aucune de ses conclusions chiffrées ne doit être reprise telle
> quelle : l'agrandissement de la chambre tient (elle est jouable, `tools/dive_bench.gd` est vert),
> il a simplement été décidé contre un corps qui n'existait pas. En particulier, la conclusion
> « le couloir n'est pas un lieu » **mérite d'être rejouée** avec les bonnes dimensions.

## Le constat, mesuré

> « La physique ne marche pas du tout. Je n'arrivais pas à me déplacer en évitant les murs qui
> bougent. À un moment donné j'ai été expulsé, impossible de revenir sur la gauche, c'est comme si
> tout le cercle était un mur pour moi. Je ne suis pas arrivé à faire des dégâts sur le réacteur. »
> — l'opérateur, playtest du 2026-08-27

Rien n'est cassé dans la collision. C'est la **géométrie** qui ne tient pas :

| Grandeur | Valeur livrée |
|---|---|
| Couloir libre entre les deux murs (face à face) | **2,60 u** |
| Encombrement du chasseur **dans l'axe** (au-dessus / en dessous du noyau) | **4,22 u** |
| Encombrement du chasseur **sur les flancs** | 1,76 u |
| Course de vol sous le mur extérieur (face à −4,50, bord à −8,00) | **1,39 u** |
| Vitesse relative des deux murs | 43 °/s |

Le chasseur **ne peut pas** être dans le couloir au-dessus ou sous le réacteur : il y manque
1,62 u, quelle que soit l'adresse du joueur. Il y entre par les flancs avec 0,42 u de jeu de
chaque côté — et les murs tournent, donc un bord d'ouverture le rattrape et le pousse. « Tout le
cercle est un mur » est la description exacte de ce que ces chiffres produisent.

**La cause racine** : la chambre a été dimensionnée quand le chasseur était modélisé par un
**disque de 0,85**. Depuis la loi des corps, il est une **capsule de 4,22 × 1,76**. Le
commentaire de `pale_leviathan_tuning.tres` annonce encore « il reste 1,45 u » — un chiffre
calculé avec l'ancien corps. La même erreur disque/capsule que celle qui laissait son nez
traverser les murs, mais côté **décor** cette fois.

⚠️ **Correction d'une mesure annoncée trop tôt** : le premier chiffrage de cette session donnait
0,19 u de course sous le mur, en oubliant `PLANE_OFFSET` (la chambre est remontée de 1,2). La
valeur juste est **1,39 u** — étroit, mais pas impossible. C'est le couloir qui est impossible,
pas le poste de tir.

## Le convoyeur — mesuré, et ce n'est PAS un bug du collider

> « C'est comme si je glissais sur la droite, où j'étais poussé sur la droite, impossible d'aller
> sur la gauche de la salle. J'arrive à avancer, à reculer un petit peu, mais mon vaisseau part
> sur la droite, je suis expulsé avec comme un mur invisible qui me pousse. » — l'opérateur,
> second playtest du même soir

Reproduit **sans aucune commande de joueur**, en headless, avec la géométrie livrée : un chasseur
posé immobile dans la chambre, les anneaux tournant pendant les 9 s de plongée.

| Départ | Arrivée | Contact |
|---|---|---|
| (0, −6,91) — l'entrée de plongée | inchangé | 0 / 540 images |
| (0, −4,80) — un pas vers le noyau | **(6,59 ; +1,03)** | 215 / 540 |
| (0, −2,70) — dans le couloir | (0,73 ; **+8,00**, le plafond) | 409 / 540 |

Le mur extérieur tourne à +26 °/s ; en bas du cercle, sa tangente pointe vers **+x**. Le corps ne
pouvant pas tenir dans le couloir, il est en contact les trois quarts du temps : chaque image le
dégage, l'image suivante le rattrape, et la somme de ces dégagements est un **transport le long de
l'arc**. « Un mur invisible qui pousse à droite » est la description exacte du phénomène.

⚠️ **CETTE CONCLUSION ÉTAIT FAUSSE, ET ELLE A COÛTÉ UN LOT ENTIER.** Elle disait « il n'y a rien à
corriger dans [`PlaneCollider`] » — le convoyeur ne serait qu'un manque de place. L'arène a donc été
agrandie… et l'opérateur a rapporté **le même symptôme, une troisième fois**.

Le défaut du raisonnement est dans le banc, pas dans le jeu : il posait le chasseur **immobile** au
milieu du couloir, là où aucun bord d'arc ne vient le chercher. Un joueur, lui, **pousse** vers le
noyau et rencontre les bords de flanc. Rejoué avec une commande — le vrai geste —, la dérive est de
**9,2 unités**, avec 279 images de contact sur 540, couloir élargi ou non.

La cause est bien dans le dégagement : sortir « par le bout de l'arc » est un déplacement
**tangentiel**, et rejoué à chaque image contre un mur en rotation, il devient un convoyeur.
`PlaneCollider.EDGE_EXIT_COST` le pénalise d'un facteur 2 : la sortie par le bout reste possible
quand elle est franchement la plus courte — c'est elle qui libère un corps coincé près d'une
ouverture — mais elle cesse de gagner sur une sortie radiale à peine plus longue.

**La leçon, plus large que ce bug** : un banc qui ne reproduit pas le geste du joueur ne prouve
rien, et deux bancs d'affilée peuvent se tromper de la même façon. Quand la mesure et l'opérateur se
contredisent, c'est l'opérateur qui a raison — il faut instrumenter le JEU (`--dive-probe`), pas
raffiner le banc.

L'élargissement reste juste et nécessaire (le couloir de 2,60 ne pouvait pas loger 4,22), mais il
n'était pas suffisant. Balayage du rayon du mur extérieur, même protocole :

| Rayon | Couloir libre | Dans le couloir |
|---|---|---|
| 5,45 (livré) | 2,60 | +11,0, éjecté — 409/540 en contact |
| 7,00 | 4,15 | +11,8, éjecté — 399/540 |
| **7,50** | **4,65** | **immobile — 0/540** |
| 8,05 | 5,20 | immobile — 0/540 |

Le seuil tombe **exactement** là où le couloir dépasse l'encombrement axial du chasseur (4,22).
7,50 est le minimum strict ; le plan retient **8,05**, parce qu'un joueur bouge, contrairement à
cette simulation. Le poste de tir sous le mur, lui, ne dérive dans aucune configuration.

## La décision (opérateur, 2026-08-27)

**Agrandir l'arène** — et non rétrécir les anneaux ni renoncer au couloir. La chambre est un lieu
distinct : elle a le droit d'avoir ses propres limites, plus larges que celles du plan de vol
habituel. `dive_time` **reste à 9 s** : on rerèglera sur du vécu une fois la phase jouable.

## Dimensionnement cible

En partant des deux contraintes qui ne bougent pas — l'enveloppe du flux (2,10) et l'encombrement
du chasseur (4,22 × 1,76) :

| | Cible | D'où elle vient |
|---|---|---|
| Couloir libre | **5,2 u** | 4,22 + 1,0 de marge de pilotage |
| Face externe du mur intérieur | 2,60 (inchangé) | l'enveloppe du flux le fixe |
| Mur extérieur : rayon / face externe | **8,05 / 8,30** | 2,60 + 5,2 = 7,80 de face interne |
| Course de vol sous le mur | **3,6 u** | 2,11 (demi-corps) + 1,5 de jeu |
| Borne basse du plan pendant la plongée | **−10,7** | 1,2 − 8,30 − 3,61 |
| Bornes de la chambre | **≈ ±11 en y** (22 u de haut) | symétrie |

## Ce que la livraison a appris

- **L'entrée de plongée commande la profondeur du plan**, pas le poste de tir. Elle se déduit
  du rayon du mur (`dive_entry_local()`), donc elle descend avec lui : −9,51, et il lui faut le
  corps entier dessous. C'est elle qui a fixé le bas à −12, pas les −10,2 du calcul initial.
- **L'équilibrage n'a PAS bougé**, contrairement à ce que ce plan annonçait. L'occupation
  mesurée passe de 0,31 à 0,334 — dans la tolérance de la garde — et le flux reste à 57 % du
  plaçable. `flux_health` reste à 840. ⚠️ Ne pas « corriger » `ring_occupancy` à 0,334 pour
  autant : ça remonterait le plaçable à 531 et ferait tomber le ratio sous les 55 % exigés.
- **Le décor ne suivait pas, et sa garde ne le voyait pas** : elle comparait la salle à
  l'arène ouverte. À `DECOR_SCALE` = 1,26 la bordure basse tombait à −8,19, soit près de
  quatre unités de vol à travers le mur de la salle. Portée à 1,81, mesurée sur les bornes de
  la chambre.
- **Sept gardes sont tombées** au changement de géométrie, et c'est le vrai travail du lot :
  elles encodaient l'ancien monde. La plus instructive exigeait « une largeur et demie de
  chasseur » (2,64) là où il fallait sa LONGUEUR (4,22) — elle était verte sur un couloir de
  2,60. Une garde qui mesure la mauvaise dimension certifie le défaut.

## Lots

1. ✅ **Des bornes de jeu par phase.** `GameplayPlane.BOUNDS` est une constante unique lue par le
   joueur, les ennemis, les balles et les bonus. Elle devient une valeur **courante**, dont le
   défaut est exactement celle d'aujourd'hui. Garde : hors plongée, les bornes sont identiques
   au chiffre près — cette étape ne doit rien changer au reste du jeu.
2. ✅ **La chambre pose les siennes.** Bornes élargies à l'entrée de plongée, restaurées à la
   sortie (y compris sur une sortie par mort ou par quota). `DECOR_SCALE` suit, pour que les
   bordures restent au-delà des limites — la garde `test_no_decor_wall_reaches_into_the_play_area`
   fait déjà ce calcul et doit rester verte.
3. ✅ **La caméra cadre la chambre.** Elle revient aujourd'hui au cadrage normal une fois dedans
   (`_dive_camera(false)` → `restore_rest`) : il lui faut un repos propre à la phase, calculé
   depuis les nouvelles bornes et le champ de vision, pas une fraction inventée.
4. ✅ **Le blindage devient un terrain.** Mur extérieur porté à 8,05 — valeur **mesurée** (voir le
   balayage ci-dessus), pas déduite. Garde à écrire : un chasseur immobile dans le couloir y est
   encore neuf secondes plus tard. Elle est ROUGE aujourd'hui, et c'est ce qui en fait une garde. ⚠️ **Ça change l'équilibrage** :
   `ring_occupancy` (0,31) a été MESURÉ sur la géométrie actuelle, le long de la vraie ligne de
   tir. Il faut refaire la mesure, puis reprendre `flux_health` — qu'on vient de porter à 840.
5. ⏳ **Vérification.** La plongée jouée par l'opérateur, et deux captures : le chasseur DANS le
   couloir, et le poste de tir sous le mur.

## Ce qu'il ne faut pas faire au passage

- **Ne pas agrandir `BOUNDS` globalement.** Le cadrage des trois autres phases en dépend, et la
  caméra à 62° remplit déjà 85-90 % du plan visible.
- **Ne pas toucher au mur intérieur.** Sa face est à 2,10, l'enveloppe du flux aussi : il n'a plus
  un millimètre à céder sans se poser sur la cible — le défaut corrigé hier.
- **Ne pas rerégler `flux_health` avant le lot 4.** Deux réglages en vol sur la même valeur, et
  plus personne ne sait lequel répondait à quoi.
