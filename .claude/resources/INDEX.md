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
  effet en comparant avec/sans.

## Bonnes pratiques — apprises à nos dépens

- [Regarder un asset avant de l'intégrer](pratique-revue-asset.md) — un livrable de la forge n'est
  pas un asset validé tant qu'il n'a pas été **rendu et regardé**. Coût de l'oubli : ADR-0006.
- [Vérifier par test, pas par capture chanceuse](pratique-verifier-par-test.md) — si l'événement à
  observer est probabiliste, la capture d'écran est le mauvais outil.
- [Un seul écrivain dans le dépôt](pratique-ecrivain-unique.md) — deux agents qui écrivent en
  parallèle produisent des commits mélangés et une porte de qualité rouge sans coupable.

## Process — étendre le ghost

- [Sous-agent ou skill ?](process-etendre-le-ghost.md) — le critère de décision, hérité du cluster
  FitDesk, et les contraintes techniques (placement, pas de hot-reload).
- **`/capitalize`** (`.claude/skills/capitalize/`) — verser les leçons d'une session dans le ghost :
  quel réceptacle pour quelle leçon, écrire la règle **avec son coût**, indexer, corriger ce qui est
  faux. ⚠️ Une procédure déterministe s'**encode dans un script**, pas en prose.

## Outillage encodé — ne pas réinventer ces procédures

Elles ont été refaites à la main, et ratées. Elles sont dans le dépôt : les appeler, pas les récrire.

| Commande | Ce qu'elle évite |
|---|---|
| `./scripts/play-arc.sh [s]` | l'arc en temps réel, horodaté, **avec reprise de main garantie** (la démo boucle sans fin) |
| `./scripts/check.sh` | la porte de qualité — import + parse + tests |
| `python3 tools/preview-svg.py <svg…>` | intégrer un asset de la forge **sans l'avoir regardé** (ADR-0006) |
| sous-agent `godot-verifier` | ~50 lignes de bruit de build/deploy dans le contexte, pour 3 faits |
