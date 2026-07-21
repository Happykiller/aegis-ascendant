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
- [Intégrer un asset image généré par ChatGPT](howto-assets-image-genere.md) — ChatGPT **peint le
  damier** au lieu d'une vraie transparence (RGB opaque). Exiger un **fond noir pur** pour les objets
  lumineux ; reconstruire l'alpha avec `tools/bg-key-alpha.py` (ne pas refaire le keying à la main).

## Bonnes pratiques — apprises à nos dépens

- [Regarder un asset avant de l'intégrer](pratique-revue-asset.md) — un livrable de la forge n'est
  pas un asset validé tant qu'il n'a pas été **rendu et regardé**. Coût de l'oubli : ADR-0006.
  ⚠️ Le rendu **studio flatte**, le **post-process rétro (960×540 + scanlines) écrase le détail
  fin** : juger en jeu, mettre le détail dans la géométrie, pas dans une texture fine.
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
- **`/asset-image`** (`.claude/skills/asset-image/`) — rendre un prompt d'image **autosuffisant** :
  le texte à coller, le nom du fichier, son chemin de dépôt, la commande suivante et la ligne de
  provenance. L'opérateur génère hors du dépôt : un prompt qui suppose du contexte est un prompt
  raté. ⚠️ Ne jamais demander une **normal map** ni une **transparence** à un générateur — il rend
  une image *qui y ressemble*, et le défaut a l'air correct.

## Outillage encodé — ne pas réinventer ces procédures

Elles ont été refaites à la main, et ratées. Elles sont dans le dépôt : les appeler, pas les récrire.

| Commande | Ce qu'elle évite |
|---|---|
| `./scripts/play-arc.sh [s]` | l'arc en temps réel, horodaté, **avec reprise de main garantie** (la démo boucle sans fin) |
| `./scripts/check.sh` | la porte de qualité — import + parse + tests ; **détecte un LFS non tiré** (sinon Godot importe les pointeurs comme des textures et l'erreur ment) |
| `./scripts/deploy-win.sh` | le déploiement Windows ; **résout `powershell.exe` par chemin absolu** si le PATH interop de WSL ne l'expose pas |
| `python3 tools/preview-svg.py <svg…>` | intégrer un asset de la forge **sans l'avoir regardé** (ADR-0006) |
| `python3 tools/bg-key-alpha.py --mode …` | réécrire à la main le détourage d'un PNG ChatGPT (fausse transparence → alpha) |
| `python3 tools/derive-maps.py <hauteur>` | demander une **normal map** à un générateur (gradients faux, relief éclairé à l'envers) ; mesure aussi la **couture** de tuilage, qu'un « seamless » demandé ne garantit pas |
| `blender45 -b -P tools/render-hull.py -- <glb>` | intégrer une coque 3D **sans l'avoir regardée** (planche 4 vues, dont l'angle réel de la caméra de jeu) |
| sous-agent `godot-verifier` | ~50 lignes de bruit de build/deploy dans le contexte, pour 3 faits |
