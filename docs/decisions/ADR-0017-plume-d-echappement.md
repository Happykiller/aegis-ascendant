# ADR-0017 — La plume d'échappement est une géométrie, pas des particules

- **Statut** : accepté
- **Date** : 2026-07-23
- **Portée** : rendu des réacteurs (joueur, ennemis, écran d'accueil, bestiaire)

## Contexte

Tout ce qui poussait dans le jeu émettait la même chose : `EngineTrail.make()` semait des quads
billboard additifs en espace monde, texturés par `FlameStreak`. Rendu à 960×540 sous le post rétro,
ça lit comme **un chapelet de petits nuages** qui tombe derrière la coque. Le moteur n'était pas un
moteur, c'était une traînée de fumée.

L'objectif demandé est nommément la **plume d'échappement** — le cône de gaz éjecté par la tuyère —
et ses **disques de Mach** : les nœuds lumineux successifs que les ondes de choc dessinent dans le
jet. On veut de surcroît que la **forme et la couleur racontent le mouvement** (accélération,
ralentissement), le vaisseau du joueur n'ayant aujourd'hui pour tout retour de pilotage que son
inclinaison.

## Décision

**La plume est un maillage solidaire de la coque, peint par un shader**
(`shaders/engine_plume.gdshader` + `scripts/fx/engine_plume.gd`), et non un système de particules.

Les particules ne sont pas écartées par goût : **les disques de Mach sont des ondes stationnaires**.
Elles restent fixes par rapport à la tuyère pendant que le gaz les traverse. Des particules qui
s'éloignent de l'émetteur ne peuvent pas les tenir en place — aucun réglage de `ParticleProcessMaterial`
ne produira ce motif, jamais. C'est un fait de cinématique, pas un arbitrage de rendu.

Le maillage est un `CylinderMesh` **unitaire** (rayons 1, hauteur 1, capuchons coupés) : tout le
profil — longueur, évasement, train de chocs — est calculé dans le vertex shader. Deux plumes de même
subdivision partagent donc le même maillage, quels que soient leur camp, leur taille et leur régime.

**Les particules disparaissent entièrement** — `EngineTrail` et `FlameStreak` sont supprimés du dépôt.
Elles ont d'abord été conservées, réduites, comme braises résiduelles : la plume étant rigide, on
craignait qu'une embardée latérale ne laisse plus aucune trace de vitesse. À l'écran, ces braises
lisent comme des **débris qui tombent du vaisseau**, pas comme un sillage. Le moteur se raconte dans
la plume, et nulle part ailleurs.

## Conséquences

- Les réglages vivent dans une Resource typée `PlumeTuning` (`resources/vfx/plume_*.tres`), une par
  camp. L'écart `length_idle` → `length_full` **est** la lisibilité de l'accélération : `validate()`
  refuse une plume qui ne grandit pas, et une réponse symétrique (une tuyère ne se coupe pas net).
- La commande (`EnginePlume.throttle_from`) mélange **l'intention** (la commande du pilote, qui
  précède la vitesse) et **la vitesse acquise** (qui entretient le jet quand le manche est relâché).
  L'une sans l'autre rate soit le geste, soit le vol plané — c'est vérifié par test.
- Les **disques de Mach n'apparaissent qu'au-dessus de `shock_threshold`** : ils ne sont pas un
  ornement permanent, ils sont la preuve visible que le moteur est ouvert en grand.
- **Plafond de 3 disques**, imposé par `validate()`. À 960×540 avec scanlines, la plume du joueur
  mesure ~45 px de long : au-delà de 3 cellules le motif devient une bouillie grise.
- Drapeau de bissection **`--no-plumes`**, sur le modèle de `--no-backdrop` / `--no-glow`.

## La forme : une plume s'effile, elle ne s'ouvre pas

C'est le défaut de forme qui a survécu le plus longtemps, parce qu'il vient d'une intuition juste
appliquée trop loin : *« le gaz se détend en sortant de la tuyère, donc ça s'ouvre »*. C'est vrai
sur les premiers pourcents de la course, et faux ensuite — le jet se dilue et **se referme en
pointe**. Un profil d'évasement **monotone**, quel que soit l'exposant, rend un **cône ouvert à bout
franc**, la forme la plus éloignée d'une plume.

Le profil retenu est donc un produit de deux termes : un **ventre** qui s'ouvre très tôt (8 % de la
course) et très peu (`belly_flare` ≈ 1,25), puis un **effilement** `pow(1 - t, 0.5)` qui reprend tout
et termine sur un point. Le nom du réglage dit lequel des deux il pilote : `belly_flare`, pas
`tail_flare` — sur une valeur seule, les deux sont indiscernables.

Corollaire indissociable : **c'est la géométrie qui termine la plume, pas l'alpha.** Une extinction
d'alpha trop raide éteint le jet avant que le maillage ne se referme, et l'on retrouve un bout franc
alors même que le profil est correct. L'exposant d'extinction reste donc faible (0,4).

## Ce que les captures ont corrigé — à ne pas refaire

Quatre autres réglages « raisonnables » ont été mesurés faux en capture, dans cet ordre :

1. **Extinction de l'alpha à `t = 0.55`** : elle tuait la moitié aval du cône, c'est-à-dire
   exactement la moitié qui s'évase. La plume rendait **deux barres parallèles**, et l'évasement
   était calculé pour rien.
2. **Enveloppe pondérée `0.3 + 0.7·rim`** : rendue `cull_disabled` et additive, la silhouette
   additionne ses deux parois rasantes. Le bord devenait un cerceau lumineux — **une bulle de savon**.
3. **Évasement concave (`pow(t, 0.7)`)** : le cône ballonne dès la sortie de tuyère. Il faut un
   profil **convexe** (`pow(t, 1.4)`) : serré sur sa première moitié, ouvert en queue.
4. **Train de chocs sinusoïdal** : le sinus arrondit les raccords et rend **un chapelet de perles**
   — précisément l'effet « petits nuages » qu'on remplaçait. La cellule est **triangulaire** : ce
   sont les flancs droits et les angles vifs qui font lire un diamant. Et le choc **pince** sans
   jamais gonfler au-delà de l'enveloppe, sinon le premier bulbe se colle à la coque.

Corollaire de méthode : le **bestiaire est un mauvais juge de la longueur** d'une plume (la coque y
est vue de trois quarts avant, jet quasiment en enfilade). L'écran d'accueil, lui, la montre de
profil et en gros plan — c'est là qu'il faut juger la forme.

## Coût

Mesuré avec et sans (`--no-plumes`), vague pleine à l'écran, sur **Quadro T1000** : **sous le
plancher de bruit** de la mesure (±0,7 ms sur ~12 ms/image — les tirs « sans plumes » sont même
ressortis plus lents deux fois sur deux). Le levier si cela changeait un jour est `rings` du `.tres`
Null Choir, pas le shader.

## Alternatives écartées

- **Restyler les particules** — impossible par construction (voir plus haut).
- **Garder des braises résiduelles derrière la plume** — essayé, puis retiré : à l'écran ce sont des
  débris qui tombent, pas un sillage.
- **Quad billboard peint au fragment** — le moins cher, mais c'est un décalque : le bestiaire, qui
  fait tourner la coque, montrerait un plan.
