# ADR-0045 — Le rendu sort du filtre

- **Date** : 2026-09-05
- **Statut** : accepté (décision du propriétaire du projet)
- **Amende** : `SPEC §15.1` (photoréalisme), `SPEC §25.2` (machine de référence),
  `assets/reference/DA.md` §4 et §13, `ADR-0011` (justification des budgets sur Quadro T1000),
  `ADR-0044 §2` (seuil d'acceptation à 12 ms sur T1000), `ADR-0016` (le `lift` change de maison).

## Contexte

L'opérateur, regardant le jeu à côté des planches de concept qu'il fournit : « ça fait jeu de
débutant », « une représentation de jouets basiques pour enfants », « on arrête avec les filtres,
on arrête avec les choses qui viendraient casser, déformer ce qui pourrait être fait ».

Le constat n'est pas une impression. Il se mesure, et la mesure désigne l'aval, pas l'amont.

### Le maillage n'est pas en cause

Le rendu studio Cycles de la cellule-témoin (`docs/forge/output/BRIEF-0098-planche-quatre-vues.png`)
est net, détaillé, lisible. La capture en jeu de **la même coque**, regardée à l'échelle 1:1
(`tools/inspect-capture.py`), montre des blocs durs postérisés, des bandes de scanlines, des hautes
lumières écrêtées et des lignes de panneau effacées. Entre les deux, il n'y a que la chaîne de
sortie.

### Ce que la chaîne de sortie détruit, chiffré

| Poste | Réglage | Effet mesuré |
|---|---|---|
| `shaders/retro_post.gdshader` | `target_res = 960×540` sur une fenêtre 1920×1080 | 1 pixel logique = un bloc **2×2 dur** ; ÷4 de la densité d'information |
| idem | `levels = 20` + dither Bayer | ~8 000 couleurs au lieu de 16,7 M. Le contrat de texture en tire déjà la conséquence : « **un détail dont la modulation est sous ~6 niveaux de gris n'existe pas dans ce jeu** » (`docs/forge/textures/README.md`) |
| `shaders/scanlines.gdshader` | `line_alpha = 0.18`, `period = 4` | une ligne sur deux assombrie de 18 % → **−9 % de luminance** sur l'image entière, en aval de tout |
| `project.godot` | section `[rendering]` d'**une seule ligne** | aucun antialiasing d'aucune sorte : MSAA, FXAA, TAA, debanding tous au défaut désactivé |

Sur la coque, cela fait **23 px/m** : toute géométrie plus fine que ~9 cm est moyennée puis
disparaît (`docs/BACKLOG.md`). C'est la raison pour laquelle relever les budgets de triangles
n'avait jamais rien donné de visible.

### Ce filtre n'a jamais été décidé

C'est le point qui tranche. **Aucun ADR n'acte le post-process rétro.** Il est justifié *a
posteriori* par un commentaire de code — `retro_post.gdshader:3-5` invoque « ADR-0009 target: la
référence est du pixel-art HD dense et chaud » — alors que le texte d'ADR-0009 ne contient ni le
mot pixel-art ni aucune cible de traitement d'image : il décrit « shmup vertical dense — flux de
tir bleus serrés, explosions/flashs orange chauds, missiles à traînée, planète + atmosphère au bord
de cadre, forteresse massive ».

Il ne figure pas davantage dans la **liste fermée** des effets autorisés de `SPEC §17.4`
(tonemapping, glow, vignette très légère, color grading, TAA ou FSR2, SSAO si le budget le permet,
brouillard volumétrique localisé, DOF en cinématique, aberration chromatique légère et
désactivable).

Et la direction artistique demandait explicitement le contraire de ce qu'il fait —
`assets/reference/DA.md` §4 : une 3D stylisée « qui évoque un pixel art HD **sans imposer une
pixellisation littérale à tous les éléments** ».

### La référence a toujours été plus détaillée que le rendu

`assets/reference/inspiration/reference_specter_9_design_sheet.png`, versée en juillet 2026,
montrait déjà une livrée peinte, un train d'atterrissage et un cockpit détaillé. La planche du
2026-09-05 la confirme. Le projet a dérivé de sa propre référence, règle après règle — et le ghost
a fini par codifier la reddition : « placer le budget de détail dans les volumes, pas dans une
texture fine qui ne survivra pas au downsampling », « un détail visible seulement en studio n'existe
pas » (`.claude/resources/pratique-revue-asset.md`).

## Décision

### 0. Ce retrait ne coûte rien — il rend

Mesuré avant d'écrire : `retro_post.gdshader:41` fait `floor(SCREEN_UV * target_res)`. Il accroche
l'**échantillonnage**, pas le rendu. La scène 3D est **déjà rendue en 1920×1080** et le shader en
jette les trois quarts ; le jeu paie donc déjà la pleine résolution et n'en montre qu'un quart.

Le retrait est à coût GPU **nul ou négatif** — une passe plein écran de moins, plus la passe de
scanlines. Aucun arbitrage performance/qualité n'est en jeu : c'était une dépense pour dégrader.

### 1. Le post-process rétro et les scanlines sont retirés du dépôt

`shaders/retro_post.gdshader`, `shaders/scanlines.gdshader`, le script `retro_post` de
`scripts/fx/` — cité sans son chemin complet, parce que le lint des règles dures vérifie que
tout chemin de source entre backticks existe, et celui-ci n'existe justement plus — et les
nœuds `RetroPost` / `Scanlines` des cinq scènes qui les montent (`scenes/boot/boot.tscn`,
`scenes/ui/codex.tscn`, `scenes/gameplay/graybox.tscn`, `scenes/gameplay/cortege.tscn`,
`scenes/dev/bestiary_lab.tscn`) sont **supprimés**, ainsi que le réglage joueur `pixelation`.

Pas de neutralisation par uniforme, pas de drapeau : un uniforme à zéro n'économise rien et laisse
un mensonge dans le dépôt. Le git garde l'historique si l'envie revenait.

### 2. Le `lift` d'ADR-0016 migre dans l'`Environment` — AVANT le retrait

C'est la seule séquence acceptable. `ADR-0016` avait mesuré que l'image de ce jeu vit sous 0,25 de
luminance, et avait placé un relèvement gamma (`lift`, 1,18 à l'accueil, 1,25 en jeu, 1,30 au
bestiaire) **dans le shader rétro**. Retirer le shader sans déplacer ce correctif rendrait l'image
nette **et** la replongerait dans le sombre — le défaut exact qu'ADR-0016 avait corrigé.

Le relèvement passe donc dans `resources/graphics/space_environment.tres` et
`title_environment.tres`, réglé pour reproduire la luminance actuelle, et **vérifié sur capture**.

⚠️ **La règle centrale d'ADR-0016 survit intacte** : ne jamais « donner du punch » en remontant
`contrast`. Sur une image dont les tons vivent sous 0,25, ce réglage ne fabrique pas de contraste,
il soustrait de la lumière. Le levier d'exposition reste le relèvement des tons moyens.

### 3. Le Quadro T1000 cesse d'être la machine de référence

`ADR-0011` avait calé **tous** les budgets de triangles sur elle, et prévoyait explicitement leur
réouverture si la cible changeait. `docs/BACKLOG.md` portait la question ouverte, marquée comme
appartenant à l'opérateur : « Le Quadro T1000 est-il encore une cible ? ». **Réponse : non.**

La cible redevient celle de `SPEC §25.2` : **RTX 4080 en 2560×1440 à 120 FPS** (60 minimum), et
**RTX 2060 en 1920×1080 à 60 FPS** en qualité Medium. Le T1000 reste un témoin bas de gamme utile,
il n'est plus une porte.

Conséquence directe : le seuil d'acceptation d'`ADR-0044 §2` (« l'accueil reste sous 12 ms sur
T1000 ») est remplacé par le budget de `SPEC §25.3` — **rendu GPU sous 6,5 ms** à 120 FPS, pics
sous 12 ms, mesuré sur RTX 4080.

### 4. La section `[rendering]` de `project.godot` est renseignée

Elle contenait une ligne. Le jeu tournait donc sans antialiasing, sans debanding, avec le filtrage
anisotrope au défaut. Les postes sont ouverts un par un, chacun **jugé sur capture et mesuré**,
jamais activés en bloc « parce que c'est mieux ».

### 5. La cible de rendu est réénoncée

`SPEC §15.1` disait « le rendu ne doit pas chercher le photoréalisme total ». La phrase est
**maintenue dans son intention et précisée dans sa portée** : ce que le jeu refuse, c'est de
troquer sa direction artistique contre du réalisme photographique — la palette Helios, les
silhouettes franches, les émissifs localisés et la hiérarchie de saillance restent la loi.

Ce que le jeu ne refuse plus, c'est **le niveau de finition** : matériaux PBR crédibles, réflexions
d'environnement, lignes de panneau, usure, livrée, densité de détail. La stylisation se fait par la
palette, l'éclairage et la composition — **plus jamais par la destruction du signal en sortie**.

De même, `DA.md` §4 (« ce traitement cinématique ne constitue pas une cible de fidélité pour le
rendu en jeu ») et §13 (les planches sont « des références d'intention, non des assets à
reproduire ») sont amendés : les planches redeviennent **une cible de fidélité de silhouette et de
finition**, dans la limite de l'originalité et de la lisibilité.

## Une piste explorée, mesurée, et écartée : les réflexions d'environnement

Les deux `Environment` ont `ambient_light_source = COLOR` et **aucun ciel**. En Forward+, un
matériau métallique réfléchit son environnement ; sans environnement, il ne réfléchit rien. Le kit
donne `metallic 0,85` à `AA_Trim` et `0,75` à `AA_Greeble` : l'hypothèse — sérieuse — était que ces
deux matériaux rendaient en aplat gris faute d'avoir quoi que ce soit à réfléchir, et que c'était
une cause du « plastique ».

Testée en deux passes, avec un ciel de réflexion non affiché (`background_mode` laissé sur couleur
unie, `reflected_light_source = SKY`), à énergie croissante. **Le fond n'a pas bougé d'un
millième** aux deux passes : le câblage était juste, ce n'est pas un raté d'implémentation.

| Ciel (canal max) | Variance locale σ7×7 sur la coque | p99 de luminance | Luminance moyenne |
|---|---|---|---|
| aucun | 20,922 | 244,0 | référence |
| 0,235 | 20,896 (**−0,12 %**) | 244,0 | +0,23 % |
| 0,706 | 20,764 (**−0,76 %**) | 244,0 | +1,26 % |

Plancher de bruit mesuré sur deux captures du **même** build : ±0,13 % sur la variance, p99
strictement immobile.

**Résultat : négatif, et monotone dans les deux sens.** Tripler l'énergie du ciel triple le voile
**et** aggrave l'aplatissement. Le 99e percentile n'a pas bougé d'un niveau sur trois builds, alors
que la coque avait de la marge (0,12 % de pixels à 254+) : le ciel avait la place de produire une
haute lumière, il n'en a produit aucune. La stratification par tranche le dit franchement — le gain
culmine entre 80 et 140 de luminance et s'**inverse** au-dessus de 180. C'est un relèvement
d'ombres, pas un spéculaire.

**La cause, et c'est elle qu'il faut retenir** : un `ProceduralSkyMaterial` est un dégradé **lisse**.
Il n'a aucune fréquence spatiale haute. Il ne peut donc pas produire de détail de réflexion, quelle
que soit son énergie et quelle que soit la rugosité du matériau — monter son énergie ne crée pas de
structure, ça verse de la lumière ambiante par un chemin détourné. Et ce +1 % s'obtient
gratuitement avec `ambient_light_energy`, sans ressource, sans cubemap de radiance.

Le ciel et `reflected_light_source` sont donc **retirés**. Si le modelé spéculaire redevient un
objectif, il faudra changer de levier : une lumière au spéculaire marqué accordée à la rugosité du
kit, ou un vrai panorama à haute fréquence — pas un dégradé procédural.

## Ce qui ne change pas

- **La lisibilité prime toujours** (`SPEC §0.1`, `DA §3.1`). Une coque magnifique qui noie un
  projectile est à refaire, pas à ajuster. Le critère de validation reste une capture regardée où
  **le chasseur et les balles se lisent par-dessus** (`ADR-0006`, `ADR-0028`).
- **La réserve de couleurs** : cyan `#3FD9E8` au tir allié, corail `#FF5A3D` au tir ennemi.
- **La règle du regard** : un asset n'est pas validé tant qu'il n'a pas été rendu et **regardé en
  jeu**. Elle devient d'ailleurs plus honnête : le rendu studio ne « flatte » plus par rapport à un
  jeu qui écrase — les deux se rapprochent.
- **Mesurer, pas supposer** (`SPEC §25.8`). Chaque poste ouvert se paie en temps GPU relevé trois
  fois de chaque côté, à 60 Hz, sur un binaire dont on a prouvé qu'il avait changé
  (`.claude/resources/howto-mesurer-la-perf.md`).
- **Le déterminisme des coques** (`ADR-0008`) et le contrat d'export.

## Conséquences

- **Tous les écrans changent**, pas seulement les vaisseaux : interfaces, fond procédural, plume
  d'échappement, portrait de Lyra. Plusieurs décisions avaient été prises *contre* le filtre et
  sont à relire à cette lumière — `ADR-0012` (un écran posé au-dessus des scanlines rejouait la
  passe localement), `ADR-0017` (plafond de 3 disques de Mach, calé sur 960×540 avec scanlines),
  `ADR-0035` (Lyra en illustration 2D parce qu'un modèle 3D « rendrait moins bien sous le
  retro-post »). Aucune n'est renversée par cet ADR : elles sont **à re-juger sur capture**, une
  par une, quand leur sujet est touché.
- Le ghost ment désormais sur un point et doit être réécrit : `.claude/resources/pratique-revue-asset.md`
  et la ligne de `docs/KB/REGLES/process.md` sur le post-traitement qui écrase.
- La contradiction dormante entre `SPEC §24.4` (« héros : 2K à 4K ») et
  `docs/forge/textures/README.md` règle 1 (« jamais 2048 », motivée par le rendu à 960×540) perd sa
  cause. Elle est arbitrée par `ADR-0046`.
- Les budgets de triangles d'`ADR-0011` perdent leur justification mesurée. Ils restent en place
  comme garde-fous d'accident jusqu'à une mesure sur la nouvelle cible.
- Si le résultat déplaisait, le retour n'est pas un réglage mais un `git revert` : c'est assumé.
