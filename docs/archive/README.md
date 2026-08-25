# Archive documentaire

Ce dossier contient les documents de pilotage **clos**. Ils ne sont pas supprimés — ils
racontent comment le projet a été conduit — mais ils ne pilotent plus rien.

> **Règle** : ce qui vit est dans `docs/`, `docs/plans/` et `docs/forge/briefs/`. Ce qui est
> clos descend ici. On **déplace**, on ne se contente pas de changer un champ : un statut tenu
> à la main rouille (mesuré le 2026-08-25 — 32 briefs livrés sur 37 portaient encore
> « assigné »). `./scripts/audit-docs.sh` dérive l'état du dépôt et range tout seul.

| Document | Clos le | Pourquoi |
|---|---|---|
| `TASKS_HORIZONTAL.md` | 2026-08-25 | Tableau de tâches H1-H9 pour un agent externe. **Plus rien de vivant** : H5 livré (Crescent Interceptor), H7 traité (`ADR-0016`), H8 traité (commit « open up the combat arena »), H9 traité (`ADR-0022`), H4 redéfini par `ADR-0012`. H1, H2, H3 et H6 étaient déjà repris dans `docs/BACKLOG.md`, qui les porte désormais sans renvoi. |
| `GRAYBOX_MILESTONE.md` | 2026-08-25 | Se déclarait lui-même « ARCHIVÉ » depuis le 2026-07-11 — il n'était qu'une pierre tombale pointant vers `docs/architecture/` et le backlog. Il vivait juste au mauvais endroit. |
