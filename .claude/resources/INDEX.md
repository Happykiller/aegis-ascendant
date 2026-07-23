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
  solliciter l'opérateur. ⚠️ Effacer `capture.png` **avant** chaque lancement et exiger la ligne
  `saved` (sinon on juge un PNG périmé) ; les flags de jeu passent **après `++`** ; et
  `--capture-after` compte des **images**, pas des secondes.
- [Mesurer le coût d'un effet](howto-mesurer-la-perf.md) — le **FPS d'un lancement automatisé est
  inexploitable** (Windows bride la présentation). Utiliser le **temps GPU par image**, et isoler un
  effet en comparant avec/sans. ⚠️ Un chiffre n'a de sens **qu'avec sa machine** : le même build rend
  0,84 ms sur RTX 4080 et 12,0 ms sur Quadro T1000 — ×14 à code identique.
- [Garder les coques 3D déterministes](howto-determinisme-des-coques.md) — l'invariant « deux
  exécutions, un `.glb` byte-identique » (ADR-0008) **était faux** depuis qu'ADR-0011 exporte les
  tangentes : mikktspace somme dans un ordre dépendant du **nombre de threads**. Passer par
  `./scripts/build-hull.sh` (force `-t 1`). ⚠️ Trois fausses pistes coûteuses écartées au passage —
  le Specter-9 a **plus** d'UV dégénérées que la citadelle et reste pourtant stable.
- [Intégrer un asset image généré par ChatGPT](howto-assets-image-genere.md) — ChatGPT **peint le
  damier** au lieu d'une vraie transparence (RGB opaque). Exiger un **fond noir pur** pour les objets
  lumineux ; reconstruire l'alpha avec `tools/bg-key-alpha.py` (ne pas refaire le keying à la main).

## Bonnes pratiques — apprises à nos dépens

- [Regarder un asset avant de l'intégrer](pratique-revue-asset.md) — un livrable de la forge n'est
  pas un asset validé tant qu'il n'a pas été **rendu et regardé**. Coût de l'oubli : ADR-0006.
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
  trois pièges qui ne produisent **ni erreur, ni test rouge, ni ligne au journal**, et ne se
  diagnostiquent qu'en capture : le **billboard jette l'échelle** du nœud (`billboard_keep_scale`),
  `GPUParticles3D.emitting` retombe à faux dès la salve **émise** (pas éteinte), et une géométrie
  déformée au vertex garde l'**AABB** de son maillage au repos. Coût du premier : trois captures vides.
- [Poser le détail en fraction, jamais en coordonnée absolue](pratique-detail-en-fraction-de-corde.md)
  — deux reforges de plan, deux fois le même dégât : les bandeaux posés à des abscisses absolues se
  retrouvent **hors de la coque** quand la silhouette bouge, et rien ne le signale. ⚠️ Cas vicieux :
  un marquage à cheval sur une charnière a fait tomber le dégagement d'un volet de 18,5° à **2,8°** —
  sous la valeur du jeu, donc un volet qui traverse la coque. **Le contrat a validé sans un mot** :
  la bbox au repos était parfaite, et un défaut d'animation ne se voit pas sur une pose fixe.
- [Juger une image en la MESURANT, pas à l'œil](pratique-juger-une-image-en-la-mesurant.md) —
  dès qu'il s'agit de luminosité, de contraste **ou d'échelle de motif**, « c'est mieux » n'est pas
  un résultat. Mesurer la luminance **sur le sujet**, sur le **fond**, et le **rapport des deux** —
  c'est ce dernier qui dit si la lisibilité en jeu a survécu. ⚠️ Coût de l'oubli : un correctif
  d'éclairage jugé bon à l'œil ne valait que **+5,7 %**, et la vraie cause (un contraste pivoté à
  0,5 sur une image entièrement sombre, ADR-0016) serait passée inaperçue. ⚠️ **Tout indicateur
  maison passe d'abord sur un témoin connu** : une mesure de calibre a rendu *1 cm* sur des écailles
  d'*1 m*, et ce chiffre partait dans un compte-rendu — une mesure fausse est plus dangereuse
  qu'aucune mesure, elle porte l'autorité du chiffre. ⚠️ Et une mesure que son propre correctif rend
  vide ne prouve rien : après `--fix-tiling`, le tuilage vaut 0,0 % **par construction**.
- [Vérifier par test, pas par capture chanceuse](pratique-verifier-par-test.md) — si l'événement à
  observer est probabiliste, la capture d'écran est le mauvais outil.
- [Un seul écrivain dans le dépôt](pratique-ecrivain-unique.md) — deux agents qui écrivent en
  parallèle produisent des commits mélangés et une porte rouge sans coupable. ⚠️ L'autre écrivain
  peut être un **outil tiers sous un autre compte** (Codex/GitKraken sous `faro`) : droits `.git` et
  fichier fantôme `NUL` — ce n'est pas ton code.

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
| `python3 tools/bg-key-alpha.py --mode …` | réécrire à la main le détourage d'un PNG ChatGPT (fausse transparence → alpha) |
| `python3 tools/derive-maps.py <hauteur>` | demander une **normal map** à un générateur (gradients faux, relief éclairé à l'envers) ; mesure aussi la **couture** de tuilage, qu'un « seamless » demandé ne garantit pas |
| `./scripts/build-hull.sh [--check\|--all] <coque>` | régénérer une coque **sans** `-t 1` — le `.glb` sera valide et pourtant non reproductible ; `--check` mesure le déterminisme, que le contrat d'`export_hull()` ne vérifie pas |
| `blender45 -b -P tools/render-hull.py -- <glb>` | intégrer une coque 3D **sans l'avoir regardée** (planche 4 vues, dont l'angle réel de la caméra de jeu) |
| sous-agent `godot-verifier` | ~50 lignes de bruit de build/deploy dans le contexte, pour 3 faits |
