# Index des ressources du Ghost — Aegis Ascendant

> Le **ghost**, c'est tout ce qui relève du fonctionnement de Claude sur ce projet : `CLAUDE.md`,
> `.claude/` (agents, resources, settings), et la mémoire auto-rappelée.
>
> Ce répertoire capitalise **comment travailler** sur Aegis Ascendant : process, workflows, bonnes
> pratiques, howtos. Il est **chargé à la demande** — jamais recopié dans `CLAUDE.md`, qui reste
> lean (un `CLAUDE.md` se charge en entier à chaque session et brûle du contexte même pour une
> tâche triviale).

## Où écrire quoi

| Nature du savoir | Destination |
|---|---|
| Comment *travailler* avec Claude sur ce projet (outillage, boucle de vérif, méthode) | **`.claude/resources/`** ← ici |
| Le *produit* : décisions, spec, backlog, architecture du jeu | `docs/` (in-repo, ship avec le projet) |
| Préférences opérateur, relation, faits d'hôte non dérivables du repo | Mémoire auto (`~/.claude/projects/…/memory/`) |
| Règles courtes, permanentes, à charger systématiquement | `CLAUDE.md` (lean — un pointeur, pas le détail) |

Règle : **tout nouvel apprentissage de session s'ajoute ici avec sa ligne dans cet index.**
Si une entrée dépasse l'utile, la scinder plutôt que gonfler le fichier.

---

## Howtos — outillage vérifié

- [Vérifier un rendu visuel depuis WSL](howto-verifier-un-rendu.md) — capture PNG autonome, sans
  solliciter l'opérateur. ⚠️ **Deux captures, jamais une** : la **silhouette** (et d'où part un
  effet) se juge sur fond NOIR (`--no-backdrop`), la **couleur** sur le fond RÉEL. Coût de la
  confusion, le même jour dans les deux sens : des lasers de boss qui partaient du vide, invisibles
  sur la nébuleuse ; et un signal de mine parfait sur fond noir, noyé en jeu. ⚠️ Sur fond lumineux,
  mesurer la **teinte**, pas la luminance — un pic à 255 ne dit pas « lumineux », il dit « écrêté ». ⚠️ Effacer `capture.png` **avant** chaque lancement et exiger la ligne
  `saved` (sinon on juge un PNG périmé) ; les flags de jeu passent **après `++`** ; et
  `--capture-after` compte des **images**, pas des secondes. ⚠️ **Un `--skip-to-*` seul ne quitte pas l'écran-titre** : il est lu par le NIVEAU, qui n'est pas chargé — il faut `--goto-graybox` devant. Symptôme : `[TitleStage] ready` sans `[Level] ready`, sortie en `code 0`, un lancement complet pour rien. ⚠️ **Ce qui doit rester discret doit être FIN, pas transparent** : le bloom et le `lift` du post-traitement ravivent toute grande surface teintée, même à 11 % d'opacité.
- [Mesurer le coût d'un effet](howto-mesurer-la-perf.md) — le **FPS d'un lancement automatisé est
  inexploitable** (Windows bride la présentation). Utiliser le **temps GPU par image**, et isoler un
  effet en comparant avec/sans. ⚠️ Un chiffre n'a de sens **qu'avec sa machine** : le même build rend
  0,84 ms sur RTX 4080 et 12,0 ms sur Quadro T1000 — ×14 à code identique. ⚠️ **`deploy-win.sh` ne
  ré-exporte pas** : sans `export-win.sh` d'abord, on mesure le binaire de la fois d'avant, sans
  la moindre erreur — et c'est le journal, pas le chiffre, qui le dit. ⚠️ **Trois tirs de chaque
  côté** : un témoin a donné 1,535 ms une fois pour 0,945 trois fois. ⚠️ **Un uniforme à zéro
  n'économise rien** — pour éteindre une dépense de shader il faut un branchement, pas un facteur.
  ⚠️ **`--novsync` fausse un différentiel dès que la scène est vivante** : à cadence libre chaque
  configuration atteint l'image N à un **temps de jeu différent**, donc avec moins d'ennemis à
  l'écran — et le biais gonfle l'écart dans le sens qu'on veut voir. Mesurer à **60 Hz** quand on
  compare des configurations.
- [Garder les coques 3D déterministes](howto-determinisme-des-coques.md) — l'invariant « deux
  exécutions, un `.glb` byte-identique » (ADR-0008) **était faux** depuis qu'ADR-0011 exporte les
  tangentes : mikktspace somme dans un ordre dépendant du **nombre de threads**. Passer par
  `./scripts/build-hull.sh` (force `-t 1`). ⚠️ Trois fausses pistes coûteuses écartées au passage —
  le Specter-9 a **plus** d'UV dégénérées que la citadelle et reste pourtant stable.
- [Intégrer un asset image généré par ChatGPT](howto-assets-image-genere.md) — ChatGPT **peint le
  damier** au lieu d'une vraie transparence (RGB opaque). Exiger un **fond noir pur** pour les objets
  lumineux ; reconstruire l'alpha avec `tools/bg-key-alpha.py` (ne pas refaire le keying à la main).
  ⚠️ Et **un brief de forge doit dire que la texture viendra d'ailleurs** : trois mains, pas deux —
  sinon la forge modélise en géométrie ce que l'opérateur allait peindre, et ses UV n'accueillent
  rien.
  ⚠️ Et **trois pièges muets** quand la texture se pose sur un maillage bâti par code — mipmaps
  absents (défaut d'import de Godot, `detect_3d` ne rattrape rien sans éditeur), tangentes absentes
  (`ArrayMesh` à la main), échelle trop fine. Même symptôme, du **grain**, aucune erreur. Les régler
  **dans cet ordre** : recaler l'échelle en premier donne un faux progrès qui masque les deux vrais
  défauts.

## Bonnes pratiques — apprises à nos dépens

- [Ce qui ne compile pas en Godot 4.7](pratique-godot-ce-qui-ne-compile-pas.md) — deux pièges d'API,
  dont un **muet** : un `return` au milieu de `fragment()` ne rend que « Shader compilation failed »,
  sans ligne ni cause. Et `const X := PackedFloat32Array([...])` n'est pas une expression constante —
  c'est `const X: PackedFloat32Array = [...]` qu'il faut écrire.
  ⚠️ **Et deux fautes qui COMPILENT** (26/08/2026), donc pires : un **nom de propriété faux**
  n'échoue qu'à l'exécution — `check.sh` reste vert, la fonction s'interrompt AU MILIEU, et
  le symptôme ressemble à un comportement plausible (une unité censée exploser « repart ») ;
  et une **lambda capture par VALEUR**, si bien qu'un test affirme que rien ne s'est passé
  sur du code parfaitement correct.

- [Regarder un asset avant de l'intégrer](pratique-revue-asset.md) — un livrable de la forge n'est
  pas un asset validé tant qu'il n'a pas été **rendu et regardé**. Coût de l'oubli : ADR-0006.
  ⚠️ **Un correctif de brief ne se propage pas aux autres livrables du même brief** : deux coques,
  même forge, même session, une corrigée et pas l'autre (UV 33/33 contre 0/36). Auditer CHAQUE
  fichier, sur la mesure et pas sur le rapport. ⚠️ Et **mesurer la bonne propriété** : le comptage
  de `TANGENT` dans le `.glb` ne prouve rien, Godot les **fabrique à l'import**
  (`ensure_tangents`) ; ce sont les **UV** qui ne s'inventent pas et ferment la porte au texturage.
  Une garde écrite sur la mauvaise propriété ne peut pas échouer — pire qu'aucune garde.
  ⚠️ **Un contrat d'export valide pendant que la silhouette dérive** : `export_hull()` mesure bbox,
  triangles, matériaux, pivot et attaches — **aucune de ces cinq mesures ne parle de la forme**. Une
  coque du boss final a tout passé et ne ressemblait pas à ses planches (un brief correctif entier).
  Exiger un verdict **côte à côte, panneau par panneau**, et objectiver par la **répartition des
  matériaux** : un émissif au-delà de ~10 % de la coque n'est plus un accent, c'est une livrée.
  ⚠️ Le rendu **studio flatte**, le **post-process rétro (960×540 + scanlines) écrase le détail
  fin** : juger en jeu, mettre le détail dans la géométrie, pas dans une texture fine. ⚠️ Et juger
  **sur la vue qui montre l'axe réglé** : le bestiaire présente les coques de trois quarts avant,
  la plume y part en enfilade — une itération de réglage perdue sur une image incapable de répondre.
- [Les géométries Godot qui disparaissent sans une erreur](pratique-geometries-invisibles.md) —
  **six** pièges qui ne produisent **ni erreur, ni test rouge, ni ligne au journal**, et ne se
  diagnostiquent qu'en capture. ⚠️ Les deux derniers datent du 23/08/2026 : un nœud posé en
  coordonnées **monde** subit quand même la transformation de son premier ancêtre `Node3D` (Godot
  traverse les `Node` intermédiaires) — d'où **aucun laser à l'écran** alors que le tir fonctionnait,
  parade `top_level` ; et une paroi vue de l'intérieur en `CULL_DISABLED` **referme le cadre**, un
  disque plein écran à la place de la scène. Les trois premiers : le **billboard jette l'échelle**
  du nœud (`billboard_keep_scale`), `GPUParticles3D.emitting` retombe à faux dès la salve **émise**
  (pas éteinte), et une géométrie
  déformée au vertex garde l'**AABB** de son maillage au repos. Coût du premier : trois captures vides. ⚠️ Le sixième (26/08/2026) est en 2D : un **`CanvasLayer` sans ligne `layer` vit à 1**, et le `layer = 5` qu'on lit dans `graybox.tscn` est celui des **scanlines**, pas du HUD. Un `grep layer` ne peut pas montrer une ligne qui n'existe pas — reconstituer l'empilement, implicites compris, et le verrouiller par un test.
- [Poser le détail en fraction, jamais en coordonnée absolue](pratique-detail-en-fraction-de-corde.md)
  — deux reforges de plan, deux fois le même dégât : les bandeaux posés à des abscisses absolues se
  retrouvent **hors de la coque** quand la silhouette bouge, et rien ne le signale. ⚠️ Cas vicieux :
  un marquage à cheval sur une charnière a fait tomber le dégagement d'un volet de 18,5° à **2,8°** —
  sous la valeur du jeu, donc un volet qui traverse la coque. **Le contrat a validé sans un mot** :
  la bbox au repos était parfaite, et un défaut d'animation ne se voit pas sur une pose fixe.
- [Juger une image en la MESURANT, pas à l'œil](pratique-juger-une-image-en-la-mesurant.md) —
  ⚠️ **Un différentiel ne vaut que si le témoin ne diffère QUE par la variable mesurée** : deux
  objets « comparables » ne sont pas un témoin, le témoin c'est **la même chose sans le réglage**
  (`--no-glow`, `--no-backdrop` servent à ça). Vécu : un verdict « aucune croissance » rendu sur
  deux unités à des profondeurs différentes, dont une allumée — le vrai différentiel dit +17,2 %.
  Le chiffre faux allait dans le sens qui faisait **renoncer**, donc dans celui qui avait l'air
  rigoureux.
  dès qu'il s'agit de luminosité, de contraste **ou d'échelle de motif**, « c'est mieux » n'est pas
  un résultat. Mesurer la luminance **sur le sujet**, sur le **fond**, et le **rapport des deux** —
  c'est ce dernier qui dit si la lisibilité en jeu a survécu. ⚠️ Coût de l'oubli : un correctif
  d'éclairage jugé bon à l'œil ne valait que **+5,7 %**, et la vraie cause (un contraste pivoté à
  0,5 sur une image entièrement sombre, ADR-0016) serait passée inaperçue. ⚠️ **Tout indicateur
  maison passe d'abord sur un témoin connu** : une mesure de calibre a rendu *1 cm* sur des écailles
  d'*1 m*, et ce chiffre partait dans un compte-rendu — une mesure fausse est plus dangereuse
  qu'aucune mesure, elle porte l'autorité du chiffre. ⚠️ Et une mesure que son propre correctif rend
  vide ne prouve rien : après `--fix-tiling`, le tuilage vaut 0,0 % **par construction**. ⚠️ **Un seuil absolu peut être aveugle à la nature de l'image** : `--check-tiling` compare deux colonnes d'UN pixel, donc sur une texture à grain fin il mesure la variance du grain et crie à la couture. Le témoin gratuit : l'écart entre deux colonnes **adjacentes à l'intérieur**. Vécu sur quatre textures, le verdict s'inverse **dans les deux sens**.
- [Dessiner avant de raisonner](pratique-dessiner-avant-de-raisonner.md) — quand le joueur et la
  mesure se contredisent, **c'est le joueur qui a raison** : instrumenter le JEU, pas raffiner le
  banc. ⚠️ **Quatre diagnostics chiffrés** ont précédé une superposition des formes de collision
  sur l'image qui a tout montré en **une capture** (le décor de la chambre tournait à l'envers de
  sa collision). `SolidsOverlay` est allumé par défaut en dev : ne jamais diagnostiquer une
  collision sans lui. ⚠️ Un banc qui **recopie** la boucle ment — `tools/dive_bench.gd` pilote le
  vrai `_slide_to()`. ⚠️ `check.sh | grep && git commit` prend le code de retour de **grep** : un
  commit est passé rouge.
- [Vérifier par test, pas par capture chanceuse](pratique-verifier-par-test.md) — si l'événement à
  observer est probabiliste, la capture d'écran est le mauvais outil. ⚠️ **Un test qui construit un
  `Node` le fuit** (mode `--script` : pas d'arbre, donc pas de parent pour le récupérer) — passer par
  `track()`. Le compte de Godot ne désigne pas son coupable : l'attribuer en exécutant **un fichier
  de test par process**. Un backlog annonçait 8 fuites « tweens/timers », il y en avait **789**,
  toutes dans un seul fichier.
  ⛔ **Jamais `git checkout <fichier>` pour défaire une mutation** : il ramène à HEAD et
  emporte tout le travail non commité du fichier — deux fois en une session le 2026-08-27,
  la seconde a coûté une implémentation entière. Copier le fichier avant, ou commiter avant
  de muter.
  ⛔ **Un seuil inventé dans une garde est une panne qui dort** : trois fois en une session
  (35 % de couverture, 6 s de plongée, 260 bousculades) — une borne plausible fige un chiffre
  et rend vert un désaccord. Lire le seuil dans **la donnée qui décide**.
  ⛔ **Une garde qui RECOPIE le pas d'image ne teste rien** : extraire le pas et l'appeler.
  ⛔ **Mesurer un `.glb` sans parcourir la hiérarchie** donne 1,30 au lieu de 1,752 sur le
  Specter-9 — deux fois la même erreur, 25/08 puis 27/08.
- [Un seul écrivain dans le dépôt](pratique-ecrivain-unique.md) — deux agents qui écrivent en
  parallèle produisent des commits mélangés et une porte rouge sans coupable. ⚠️ L'autre écrivain
  peut être un **outil tiers sous un autre compte** (Codex/GitKraken sous `faro`) : droits `.git` et
  fichier fantôme `NUL` — ce n'est pas ton code. ⚠️ **Aucune réécriture d'historique à deux**
  (`--amend`, `rebase`, `reset --hard`) : `--amend` vise `HEAD`, donc le commit de l'AUTRE s'il a
  committé en dernier, et un pathspec n'y change rien. Vécu : un commit détruit, sauvé par hasard
  parce qu'un `reset --soft` laisse le contenu dans l'index.
  ⚠️ **RÉCIDIVE (26/08/2026), et elle déplace la règle** : le second écrivain n'est pas seulement
  l'autre agent sous un autre compte — c'est aussi **le sous-agent qu'on vient soi-même de lancer**.
  Un `git add -A` pendant qu'`asset-forge` travaillait a emporté 677 lignes de son script en cours
  dans un commit de VFX. On ne se pense pas comme deux, et c'est là que ça casse.

## Process — étendre le ghost

- [Sous-agent ou skill ?](process-etendre-le-ghost.md) — le critère de décision, hérité du cluster
  FitDesk, et les contraintes techniques (placement, pas de hot-reload).
- **`/capitalize`** (`.claude/skills/capitalize/`) — verser les leçons d'une session dans le ghost :
  quel réceptacle pour quelle leçon, écrire la règle **avec son coût**, indexer, corriger ce qui est
  faux. ⚠️ Une procédure déterministe s'**encode dans un script**, pas en prose.
- **`/jouer`** (`.claude/skills/jouer/`) — mettre le jeu entre les mains de l'opérateur pour un
  test réel : lancement **en arrière-plan** (au premier plan, le délai d'expiration fermerait la
  fenêtre en pleine partie), et **chronologie rendue à la fermeture** — l'opérateur jouait, il n'a
  pas lu le journal. ⚠️ Ne jamais y passer `--demo` : le pilote automatique prend les commandes.
- **`/asset-image`** (`.claude/skills/asset-image/`) — rendre un prompt d'image **autosuffisant** :
  le texte à coller, le nom du fichier, son chemin de dépôt, la commande suivante et la ligne de
  provenance. L'opérateur génère hors du dépôt : un prompt qui suppose du contexte est un prompt
  raté. ⚠️ Ne jamais demander une **normal map** ni une **transparence** à un générateur — il rend
  une image *qui y ressemble*, et le défaut a l'air correct. ⚠️ **Ni une taille qu'il ne sait pas
  rendre** : les formats sont `1024×1024`, `1536×1024`, `1024×1536` — demander 2048 rend un 1024
  agrandi, et le post-process rétro à 960×540 rend la question sans objet.

## Outillage encodé — ne pas réinventer ces procédures

Elles ont été refaites à la main, et ratées. Elles sont dans le dépôt : les appeler, pas les récrire.

| Commande | Ce qu'elle évite |
|---|---|
| `./scripts/play-arc.sh [s]` | l'arc en temps réel, horodaté, **avec reprise de main garantie** (la démo boucle sans fin) |
| `./scripts/play.sh [-- flags]` | jouer le **build précédent** sans le savoir — `deploy-win.sh` n'exporte pas ; pose aussi le `++` tout seul |
| `./scripts/check.sh` | la porte de qualité — import + parse + tests ; **détecte un LFS non tiré** (sinon Godot importe les pointeurs comme des textures et l'erreur ment). ⚠️ **Toujours lui, jamais `test_runner.gd` seul** : le runner nu ne fait pas l'import, donc tout `class_name` neuf rend `Identifier not declared` — une itération perdue à chercher une faute qui n'existe pas |
| `./scripts/deploy-win.sh` | le déploiement Windows ; **résout `powershell.exe` par chemin absolu** si le PATH interop de WSL ne l'expose pas |
| `python3 tools/preview-svg.py <svg…>` | intégrer un asset de la forge **sans l'avoir regardé** (ADR-0006) |
| `python3 tools/inspect-capture.py <png> [--at X,Y] [--zoom N]` | **juger une capture RÉDUITE** — la réduction pardonne exactement le défaut cherché (contour dur, facette, couture, saturation). Il découpe à **1:1**, agrandit au plus proche voisin, et **ne sait pas redimensionner**. Coût de l'oubli : un effet déclaré bon deux fois sur des images incapables de le montrer |
| `./scripts/release.sh [--publish\|vX.Y.Z]` | livrer un ZIP là où **un exe unique** suffit, et publier un export **partiel** — Godot rend 0 dessus, et un exe trop léger se lance sur un écran vide. Le script vérifie le PRODUIT (taille, absence de `.pck` à côté), pas le code de retour. ⚠️ **La version ne se saisit plus : elle se lit** dans `project.godot` (`config/version`), la seule que Godot grave dans l'exe et que les écrans affichent. Un tag qui ne lui correspond pas est refusé, un tag déjà publié aussi — pour monter de version, on édite `project.godot`, pas la ligne de commande |
| `python3 tools/bg-key-alpha.py --mode …` | réécrire à la main le détourage d'un PNG ChatGPT (fausse transparence → alpha) |
| `python3 tools/derive-maps.py <hauteur>` | demander une **normal map** à un générateur (gradients faux, relief éclairé à l'envers) ; mesure aussi la **couture** de tuilage, qu'un « seamless » demandé ne garantit pas |
| `./scripts/build-hull.sh [--check\|--all] <coque>` | régénérer une coque **sans** `-t 1` — le `.glb` sera valide et pourtant non reproductible ; `--check` mesure le déterminisme, que le contrat d'`export_hull()` ne vérifie pas. ⚠️ **`--check` ne contrôle QUE LE PREMIER `.glb` d'un script** (`grep … | head -1`) : un script qui en produit deux laisse le second sans garde, en silence (relevé 26/08/2026 sur `build_impact_debris.py`). ⚠️ Et **`ak.export_hull()` refuse tout matériau hors `MATERIAL_ORDER`** — donc hors palettes de faction : une pièce neutre (roche, décor) ne peut pas passer par le contrat du kit sans se voir imposer une couleur qui ne lui appartient pas |
| `blender45 -b -P tools/render-hull.py -- <glb>` | intégrer une coque 3D **sans l'avoir regardée** (planche 4 vues, dont l'angle réel de la caméra de jeu) |
| sous-agent `godot-verifier` | ~50 lignes de bruit de build/deploy dans le contexte, pour 3 faits |
