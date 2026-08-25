---
titre: HISTORY — index chronologique des sujets abordés
type: index
statut: actif
maj: 2026-08-25
---

# Historique des sujets

Une ligne par **session utile** — pas un journal de commits, git le fait déjà. Ce qu'on cherche ici :
« a-t-on déjà creusé ce sujet, et qu'en est-il sorti ? »

Les lignes antérieures au 2026-08-23 sont **reconstituées** à partir des dates portées par les ADR
et par `docs/BACKLOG.md` : elles sont datées de façon fiable, mais ne racontent que ce qui a été
acté, pas ce qui a été exploré.

| Date | Sujet | Ce qui en est sorti | Traces |
|---|---|---|---|
| 2026-07-11 | Fondations : moteur, environnement, commandes, délégation créative, quarantaine IP | 5 ADR d'un coup ; le cadre de travail du projet | [ADR-0001 à 0005](../decisions/) |
| 2026-07-12 | Fond spatial, audio, chaîne 3D Blender | Nébuleuse procédurale (les SVG picturaux sont écartés), banque de cues + musique adaptative, pipeline `.glb` déterministe | [ADR-0006](../decisions/ADR-0006-fond-spatial-procedural.md), [0007](../decisions/ADR-0007-pipeline-audio.md), [0008](../decisions/ADR-0008-pipeline-3d-blender.md) |
| 2026-07-19 | **Un seul vaisseau** : la transformation en forteresse est supprimée | Nouvel arc `FIGHTER_WAVES → MINI_BOSS → FINAL_BOSS → DOCKING → VICTORY` ; référence d'inspiration réinstaurée | [ADR-0010](../decisions/ADR-0010-un-seul-vaisseau-docking-final.md), [ADR-0009](../decisions/ADR-0009-reference-ip-reinstauree.md), [DAF/arc-de-jeu.md](DAF/arc-de-jeu.md) |
| 2026-07-20 → 21 | Détail des coques, textures, écrans, silhouette du Specter-9 | Budgets de coque, textures déverrouillées, langage d'interface unifié, exception IP unique et actée | [ADR-0011 à 0014](../decisions/) |
| 2026-07-22 | Bestiaire, et la luminosité qui manquait | Le post-traitement rétro **pivotait son contraste à 0,5 sur une image entièrement sombre** : il n'était qu'un assombrisseur. +25,8 % mesurés sur la coque du joueur | [ADR-0015](../decisions/ADR-0015-bestiaire-catalogue-de-coques.md), [ADR-0016](../decisions/ADR-0016-luminosite-le-contraste-pivotait-a-0-5.md) |
| 2026-07-23 → 24 | Le Pale Leviathan : conception, silhouette, câblage, puis **coupe au playtest** | Boss à 4 phases sur conditions matérielles ; combat ramené de ~3 min à ~67 s ; lisibilité HUD + coquille qui tourne | [ADR-0017](../decisions/ADR-0017-plume-d-echappement.md), [ADR-0018](../decisions/ADR-0018-le-boss-final-se-demonte.md), [ADR-0019](../decisions/ADR-0019-le-leviathan-coupe-au-playtest.md) |
| 2026-08-23 | Reprise après un mois : revue d'état, fuites de test, mise en place de la KB | Dépôt à jour et vert (279 tests) ; **789 objets fuités** attribués à un seul fichier de test et supprimés ; backlog recalé ; création de `docs/KB/` et du skill `/cloture` | [REGLES/normes.md](REGLES/normes.md), `.claude/resources/pratique-verifier-par-test.md`, [MOTEUR.md](MOTEUR.md) |
| 2026-08-25 | Première **partie jouée** du boss en cycles, et la jauge qui bouclait | Équilibrage d'`ADR-0021` **acquis** ; mais le HUD recevait `structure_ratio()` (la cible courante, qui se remplit à chaque bascule) au lieu de `fight_ratio()` — six remplissages lus comme une boucle. La mesure juste existait et n'allait qu'à la **musique** | [ADR-0023](../decisions/ADR-0023-la-jauge-du-boss-montre-le-combat.md), [plan 2026-08-25](../plans/2026-08-25-boss-pale-leviathan.md), `tests/unit/test_leviathan_hud_relay.gd` |
| 2026-08-25 | Le flux du boss, dimensionné avec la cadence de l'armure | Playtest à puissance MAX : six plongées au lieu de trois. Une seule hypothèse de dps servait une cible large (les plaques) et une petite cible mobile (le flux) ; l'invariant se comparait à elle-même et validait à 99 % de son plafond | [ADR-0024](../decisions/ADR-0024-le-flux-a-sa-propre-cadence-de-reference.md) |
| 2026-08-25 | On entre VRAIMENT dans le noyau, et trois cycles deviennent une construction | La plongée était une sphère de 7 m retournée autour du boss : le chasseur n'allait nulle part. Zone dédiée + iris à volets (2 briefs de forge). Puis : aucun `flux_health` ne pouvait donner trois cycles (600 à 1200 PV placés par plongée selon la partie) — on plafonne le passage | [ADR-0025](../decisions/ADR-0025-on-entre-dans-le-noyau.md), [ADR-0026](../decisions/ADR-0026-trois-cycles-par-construction.md), `BRIEF-0082`, `BRIEF-0083` |
| 2026-08-25 | Le rangement documentaire : plans, briefs et backlog jamais fermés | Constat de l'opérateur, mesuré : **32 briefs livrés sur 37 portaient un statut faux**, deux documents morts dans `docs/`, et le backlog contenait **deux copies divergentes** de ses sections P0-P4. Un état tenu à la main rouille : `audit-docs.sh` le **dérive** du dépôt. Chantier du boss clos et archivé, plan du bestiaire repris (une seule session désormais), `/cloture` corrigé — son périmètre annonçait un chemin et un remote faux | [REGLES/consignes.md](REGLES/consignes.md), [MOTEUR.md](MOTEUR.md), `scripts/audit-docs.sh` |
| 2026-08-25 | **Une phase entre les deux boss** : le champ d'astéroïdes | Deux manques comblés d'un coup — trois unités du bestiaire (Choir Mine, Null Maw, Leech Drone) livrées et jouées **nulle part**, et deux boss dos à dos sans respiration. Revient sur le découpage d'`ADR-0010`, qui avait *supprimé* une phase. Second `WaveSpawner` **endormi** plutôt que de toucher la classe qui marche ; `FORTRESS_AWAKENING` réemployé — un lit musical rendu, payé, et **orphelin** depuis six semaines sans que rien ne le signale | [ADR-0027](../decisions/ADR-0027-une-phase-entre-les-deux-boss.md), [plan inter-boss](../plans/2026-08-25-phase-inter-boss-survol-de-lune.md), `tests/unit/test_asteroid_field_wave.gd` |

> Découper par année (`HISTORY/README.md` + `HISTORY/2026.md`) au-delà de ~200 lignes.
