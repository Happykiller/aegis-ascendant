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

`EngineTrail` **survit**, réduit, dans son seul rôle honnête : les braises laissées **dans le monde**
par une coque qui se déplace. La plume, rigide, ne peut pas dire ça — sans les braises, une embardée
latérale ne laisse plus aucune trace de vitesse.

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

## Ce que les captures ont corrigé — à ne pas refaire

Quatre réglages « raisonnables » ont été mesurés faux en capture, dans cet ordre :

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
- **Quad billboard peint au fragment** — le moins cher, mais c'est un décalque : le bestiaire, qui
  fait tourner la coque, montrerait un plan.
