---
titre: Consignes de l'opérateur — nées d'une correction
type: regle
statut: actif
maj: 2026-08-28
---

# Consignes

Ce que l'opérateur a corrigé chez Claude. Chaque ligne a coûté quelque chose : elle reste écrite
tant que personne ne la lève.

## Sur la conduite du travail

- **Demander une texture doit être un RÉFLEXE, pas une option.** L'opérateur a dû le dire :
  « si tu as besoin de texture pour les murs demande, rappelle-toi que cela doit être un
  réflexe » (2026-08-27). Un volume neuf qui rend un aplat de couleur n'est pas fini — il lui
  manque sa matière, et la voie est écrite (`ADR-0028`, brief de forge + `docs/forge/textures/`).
  Ne pas attendre qu'on la réclame. Le coût de l'oubli : deux playtests passés à juger « un halo
  de couleur » qu'une carte de 1024 px a réglé en une passe.
- **Signaler ce qui n'est PAS tenu quand une règle est posée.** Une loi appliquée à un seul
  endroit se lit comme une loi appliquée partout. Sur la collision, le plan a nommé lot par lot
  ce qui restait ouvert (coques de boss, vaisseaux entre eux, décor) — et l'opérateur a pu les
  demander dans l'ordre au lieu de les découvrir en jouant.

- **Ne pas tirer les leviers de réglage d'office.** Après un playtest, les correctifs évidents se
  font ; les leviers de rythme restants (`shell_orbit_period`, `plate_arc_deg`) attendent le verdict
  de l'opérateur. Source : `docs/BACKLOG.md`, section « Reste à confirmer ».
- **Le playtest manuel appartient à l'opérateur.** Aucune mesure automatique n'avait vu que le boss
  final était « beaucoup beaucoup trop long » ; c'est une partie jouée qui l'a dit (ADR-0019).
- **Un point de reprise faux coûte plus qu'un point de reprise absent** : il envoie la session
  suivante dans le mur sans qu'elle le questionne. D'où l'obligation de recaler `docs/BACKLOG.md`
  quand ses chiffres ne correspondent plus au réel.

- **Ce qui est clos doit descendre aux archives.** Verdict du 2026-08-25 : « j'ai un souci avec
  tous ces plans, roadmaps, fichiers qu'on crée et qu'on archive jamais, ou marque comme done ».
  Mesuré dans la foulée : **32 briefs livrés sur 37 portaient encore « assigné »**, deux
  documents de pilotage étaient morts depuis cinq et six semaines dans `docs/`, et le backlog
  contenait **deux copies divergentes** de ses sections P0-P4 — celle qu'on lisait en premier
  était la périmée. Un état tenu à la main rouille : `./scripts/audit-docs.sh` le **dérive** du
  dépôt et range (`--fix`), et `/cloture` l'appelle. ⚠️ **Avant d'archiver un plan, verser ce
  qu'il laisse ouvert dans `docs/BACKLOG.md`** — un plan qu'on archive ne doit rien emporter.
- **Un calibrage mesure une situation, pas une intention.** `ADR-0024` avait dimensionné le flux
  du boss contre la plongée d'alors ; `ADR-0025` a rendu la cible facile à toucher, et le
  calibrage est devenu faux **en silence** — aucun test rouge, invariant toujours vert. C'est le
  playtest suivant qui a payé (le boss est tombé en 2 cycles au lieu de 3). Quand la situation
  change sous un réglage, le réglage est à refaire — et si aucun nombre ne peut tenir, c'est la
  **règle** qu'il faut changer (`ADR-0026` : plafonner, pour que trois cycles soient vrais par
  construction et non par calibrage).

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

## Débogage et diagnostic (2026-08-28)

- **En développement, les zones de collision, les cibles et les écrans de tir sont TOUJOURS
  affichés** ; en release ils sont éteints par défaut mais restent activables dans Options →
  Débogage, chacun avec sa phrase explicative (but pédagogique). « C'est un outil extrêmement
  précieux. » — né d'une soirée où quatre diagnostics ont manqué un décalage de 90° visible en
  une capture.
- **Quand un symptôme survit à des correctifs, isoler** : retirer l'élément suspect et voir si
  le symptôme part avec lui (« la méthode de la sphère indienne »), puis **rebâtir un élément à
  la fois**. Ne pas empiler un cinquième correctif sur les quatre premiers.
- **Un enregistrement de partie vaut plus qu'un banc** : quand l'opérateur dit « ça ne marche
  toujours pas », enregistrer sa commande et sa position (`--dive-trace`) avant de re-raisonner.
