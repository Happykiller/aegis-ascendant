---
titre: Consignes de l'opérateur — nées d'une correction
type: regle
statut: actif
maj: 2026-08-23
---

# Consignes

Ce que l'opérateur a corrigé chez Claude. Chaque ligne a coûté quelque chose : elle reste écrite
tant que personne ne la lève.

## Sur la conduite du travail

- **Ne pas tirer les leviers de réglage d'office.** Après un playtest, les correctifs évidents se
  font ; les leviers de rythme restants (`shell_orbit_period`, `plate_arc_deg`) attendent le verdict
  de l'opérateur. Source : `docs/BACKLOG.md`, section « Reste à confirmer ».
- **Le playtest manuel appartient à l'opérateur.** Aucune mesure automatique n'avait vu que le boss
  final était « beaucoup beaucoup trop long » ; c'est une partie jouée qui l'a dit (ADR-0019).
- **Un point de reprise faux coûte plus qu'un point de reprise absent** : il envoie la session
  suivante dans le mur sans qu'elle le questionne. D'où l'obligation de recaler `docs/BACKLOG.md`
  quand ses chiffres ne correspondent plus au réel.

## Sur l'outillage

- **`/jouer` nu démarre normalement**, à l'écran-titre, l'arc depuis le début. Les drapeaux
  (`--goto-graybox`, `--skip-to-final`…) ne s'ajoutent **que** si l'opérateur les demande
  explicitement. Un `/jouer` nu était parti droit au boss ; ce n'était pas ce qui était voulu.
- **Ne jamais passer `--demo` à `/jouer`** : le pilote automatique prend les commandes.
- **Une procédure déterministe s'encode dans un script**, pas en prose. `play-arc.sh` et le
  correctif de `deploy-win.sh` sont nés de quatre procédures réécrites à la main, et ratées trois
  fois. Si tu peux l'écrire en bash, ne l'écris pas en français.

## Sur la langue

Le projet et l'opérateur travaillent **en français** : documentation, commentaires et réponses.
Les identifiants de code et les termes techniques gardent leur forme d'origine.

> **À COMPLÉTER.** Les préférences non dérivables du dépôt (relation, habitudes, contraintes
> d'hôte) vivent dans la mémoire auto-rappelée, aujourd'hui **vide** pour ce projet — voir la
> question ouverte de [`../MOTEUR.md`](../MOTEUR.md) sur les trois mémoires restées à l'ancien
> chemin `-home-admin-sandbox-macross`.
