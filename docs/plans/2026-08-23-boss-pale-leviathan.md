---
titre: Pale Leviathan — ce qui reste à faire
date: 2026-08-23
auteur: session Claude « boss » (aegis-ascendant-47)
perimetre: scripts/bosses/, graybox_root.gd, resources/data/leviathan_tuning.gd, tools/blender/build_pale_leviathan.py, docs/forge/briefs/BRIEF-008x
etat: à appliquer
supersede: rien — premier plan daté de ce chantier
---

# Pale Leviathan — ce qui reste à faire

> **Ce document fait foi au 2026-08-23.** Il ne remplace ni la spec ni les ADR (qui priment) : il
> dit **ce qui reste**, dans l'ordre où le prendre. Le combat a été refondu deux fois ce jour-là —
> `ADR-0020` (quatre phases → deux) puis `ADR-0021` (trois cycles armure/noyau). Ces deux ADR
> décrivent l'état actuel ; ce plan décrit la suite.

## État à la clôture de la session

Porte verte, tout commité, rien à moitié intégré. Le combat tourne en **trois cycles** :
`BRISER L'ARMURE` (4 puis 3 puis 2 plaques) → `PLONGER DANS LE NOYAU`, ~40 s au total.

Ce qui a été livré et **vérifié en capture** ce jour-là :

- les plaques tombent selon leur tangente réelle (`fall_axis` n'était jamais calculé : les quatre
  basculaient autour du même axe) et ne rétrécissent plus ;
- les épines sont des **tourelles laser** télégraphiées, et chaque plaque brisée en éteint une ;
- le laser part de `Muzzle_Spike_NN`, la bouche que la coque livre — elle existait depuis le premier
  brief et n'avait jamais été câblée ;
- **dans le noyau, on voit enfin quoi tirer** : le flux est passé de la teinte du décor au blanc
  chaud (luminance 95,7 → 138,5), la chambre a reculé (R−G 41,9 → 13,8).

## Ce qui reste, dans l'ordre

### 1. ⚠️ Rejouer le combat — c'est le seul point bloquant

**Rien de ce qui précède n'a été joué.** Les captures disent que la mécanique est là et lisible à
l'arrêt ; elles ne disent pas si le combat est agréable. Trois questions à trancher en jouant :

- les cycles se lisent-ils ? (une plaque toutes les ~2 s, une tourelle qui s'éteint avec elle,
  bannière `ARMURE REFORMEE — N PLAQUES`)
- la plongée fait-elle son effet, et sait-on quoi faire une fois dedans ?
- est-ce encore « lancinant » ?

Leviers prêts si l'armure traîne : `shell_orbit_period` 9 → 7, `plate_health` 460 → 380. Le
garde-fou de durée (`validate()`) refusera d'aller trop loin.

### 2. Rejouer `BRIEF-0080` — le brief est écrit, commité, prêt

`docs/forge/briefs/BRIEF-0080-leviathan-epines-vers-l-avant-bis.md`. La forge avait été lancée puis
**arrêtée à la clôture** ; elle n'avait rien écrit, l'arbre est propre.

Objet : retourner **`Spike_01` et `Spike_02`** pour que les quatre épines pointent vers le joueur.
État mesuré aujourd'hui, en jeu : `Spike_01` +68,7° et `Spike_02` +109,0° (arrière), `Spike_03`
−120,7° et `Spike_04` −68,5° (vers le joueur). **2 sur 4.**

⚠️ **Lire l'avertissement en tête du brief avant de le relancer.** `BRIEF-0045` a demandé l'inverse
et a été annulé : les angles avaient été relevés dans le repère du **fichier** et présentés comme
ceux du **jeu**, alors que `BossController` applique `FACING_PLAYER = (0, π, 0)` — soit 180° de
différence. Le rapport de 0045 (`docs/forge/output/BRIEF-0045-report.md`) reste utile : son travail
était juste, seule la cible était fausse, et ses constats se transposent en miroir.

**Une fois livré**, une ligne à changer dans `_aim_spine()` : le faisceau prolongera l'axe de
l'épine au lieu de viser le joueur. C'est le grief d'origine du playtest, réglé à ce moment-là
seulement.

### 3. Dettes ouvertes, aucune urgente

- **`ak.inset_panel()` ne creuse rien** sans `normal_update()` : `build_pale_leviathan.py` fait
  10 appels, `build_choir_harvester.py` 7, aucun ne l'appelle. Le relief de dix panneaux du boss
  final n'existe pas. **Correctif dans le kit**, pas dans les scripts — mais il régénère tous les
  `.glb` du dépôt. Ordre convenu entre les deux sessions : **0080 intégré → correction du kit →
  régénération → re-revue des silhouettes**, puis recalage des sha256 dans `ASSET_PROVENANCE.csv`.
- **`choir_harvester.glb` est sans UV** (0/61) : le mini-boss est intexturable. Cause : ni
  `_triangulate_ngons()` ni `box_project_uv()` dans son script.
- **`HarvesterCombat` attache ses `Beam` comme le Leviathan le faisait** — enfants d'un `Node` sous
  le `BossController`, donc doublement transformés. Corrigé chez le Leviathan (`top_level = true`),
  **non vérifié chez le mini-boss**.
- **Les flux audio ne sont pas arrêtés à la sortie** : le compte de fuites vaut 2 × le nombre de
  sons en lecture. Bénin, mais c'est le bruit qui noiera la prochaine vraie fuite.
- **Fuite propre à la plongée** : non — vérifié, c'était la même cause audio.

## Ce que ce chantier a appris, et où c'est écrit

Les leçons de méthode de la journée sont dans `.claude/resources/` (indexées par `INDEX.md`), pas
ici. Les plus coûteuses :

- une silhouette se juge sur **fond noir**, une couleur sur le **fond réel** — deux captures ;
- un **différentiel** ne vaut que si le témoin ne diffère que par la variable mesurée ;
- **un repère n'est pas une convention, c'est une mesure** (la leçon de `BRIEF-0045`) ;
- on vérifie le **livrable** d'une délégation, rarement la **commande** qu'on lui a donnée.
