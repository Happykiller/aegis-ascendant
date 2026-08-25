---
titre: Bestiaire d'ennemis — plan repris après la fin du régime à deux sessions
date: 2026-08-25
auteur: session Claude (poste happykiller) — reprise du plan de la session `aegis-ascendant-f0`
perimetre: familles d'ennemis, coques, comportements, composition des vagues
etat: à appliquer
supersede: docs/plans/2026-08-23-bestiaire-ennemis.md (intégralement)
---

# Bestiaire d'ennemis — plan repris

> **Ce document fait foi au 2026-08-25.** Il reprend le plan du 23/08 rédigé par l'autre
> session, en le recalant sur l'état **vérifié** du dépôt. Il ne remplace ni la spec ni les
> ADR, qui priment.

## 1. Ce qui a changé depuis le 23 août, et qui change le plan

### ⚠️ Il n'y a plus qu'une session sur ce poste

Le plan du 23/08 consacrait toute une section à des **accords entre deux sessions**. Ce régime
est **terminé**. Ce qui en découle :

| Accord du 23/08 | Statut |
|---|---|
| Plages de numéros de brief (0040-0079 bestiaire, 0080-0099 boss) | **caduc** — prendre le prochain numéro libre |
| « Un seul écrivain » sur `ASSET_PROVENANCE.csv` | **caduc** en tant que contrainte ; reste vrai de fait |
| « Un seul écrivain sur Windows », s'annoncer avant `play.sh` | **caduc** |
| `aegis_kit.py` **gelé** jusqu'à la correction d'`inset_panel()` | **levé** — la correction est faite (voir ci-dessous) |
| Jamais de `git commit -a`, `add .`, `--amend`, `rebase`, `reset --hard` | **reste une bonne pratique**, plus une nécessité |

⚠️ **Ce qui reste vrai malgré tout** : `--amend` cible `HEAD`, pas « mon dernier commit ». Sur
un dépôt poussé, il réécrit une histoire publique. La prudence garde sa valeur.

### Le kit est réparé, et toutes les coques ont été régénérées

`ADR-0008` demandait « le détail par la géométrie » et `ak.inset_panel()` **ne creusait rien
depuis le premier jour** : `bmesh.ops.inset_region` lisait des normales de face nulles sur un
maillage frais. Corrigé le 2026-08-25 (`BRIEF-0084`, kit en **1.1.0**), **dix coques
régénérées**, silhouettes inchangées (bbox et pivot à 0,00000 m), contrats de noms identiques.

**Conséquence directe pour ce périmètre** : `choir_mine`, `null_maw`, `leech_drone` et
`crescent_interceptor` ont de **nouveaux sha256**, déjà recalés dans
`assets/licenses/ASSET_PROVENANCE.csv`. `choir_mine` a vu son garde-fou de script relevé de
6 000 à 7 000 triangles (mesurée à 6 232 une fois ses panneaux réellement creusés).

### La ligne « quatre coques sans UV » du plan précédent est périmée

Vérifié le 2026-08-25 sur les `.glb` livrés :

| Coque | UV | |
|---|---|---|
| `choir_mine` | **33/33** | ✅ réglé par sa reforge |
| `null_maw` | **36/36** | ✅ réglé par sa reforge |
| `leech_drone` | **22/22** | ✅ |
| `crescent_interceptor` | **0/7** | ❌ **toujours ouvert** |
| `needle_scout` | **0/7** | ❌ **toujours ouvert** |
| `choir_harvester` | **0/61** | ❌ le mini-boss, toujours ouvert |

## 2. Ce qui est livré et jouable

Le socle d'`ADR-0022` — quatre axes de variété, tous *append-only*, tous d'indice 0 =
comportement d'avant, donc les familles historiques sont inchangées **par construction** :
`Path` (+`DRIFT`), `Motion {PATH, HOMING}`, `Fire {SINGLE, NONE, FAN, AIMED, RADIAL}`,
`Effect {NONE, GRAVITY_WELL, LEECH, SHIELD_AURA}`, plus `EnemyReaction` / `EnemyPose` /
`EnemyVitals`.

| Unité | Verbe de jeu | Resource | Scène | Coque | Codex |
|---|---|---|---|---|---|
| **Choir Mine** | un obstacle qu'on peut **dépenser** | ✅ | ✅ | ✅ | ✅ |
| **Null Maw** | une **zone interdite** : aspire, ne blesse jamais | ✅ | ✅ | ✅ | ✅ |
| **Leech Drone** | un **parasite** : poursuit, s'accroche, vole 60 % de la poussée | ✅ | ✅ | ✅ | ✅ |
| **Shield Carrier** | la **cible prioritaire** : rend les autres invulnérables | ❌ | ❌ | ❌ | ❌ |

Banc d'essai : `./scripts/play.sh -- --goto-lab=<mine|maw|leech|carrier>`.

## 3. Ce qui reste, dans l'ordre

### 3.1 — Poser les unités dans l'arc *(le plus rentable, et il demande une décision)*

⚠️ **Les trois unités livrées n'apparaissent dans AUCUNE vague**, vérifié : l'arc n'a qu'une
vague, `resources/encounters/wave_graybox_01.tres`, qui n'emploie que des Needle Scout et le
Crescent Interceptor. Le bestiaire est jouable **au banc d'essai seulement**.

C'est aussi le **P0 du backlog** (« une seule vague de ~10 Needle Scouts puis mini-boss ;
ajouter 1-2 vagues et une 2ᵉ famille pour 2-3 min de jeu »). Les deux se traitent d'un coup :
une séquence « champ de mines » entre les chasseurs et le mini-boss.

**Ça change le rythme et la difficulté, donc c'est un jugement de joueur** — ça appartient à
l'opérateur (`docs/KB/REGLES/consignes.md`). Le code, lui, est prêt.

### 3.2 — Finir le Shield Carrier *(prêt à lancer, rien ne le bloque)*

Le comportement est **écrit, testé et vérifié** ; seule la coque manque.

1. Relancer la forge sur `docs/forge/briefs/BRIEF-0046-shield-carrier-hull.md` — brief complet,
   commité, **rejouable tel quel**. Il est resté parmi les briefs vivants : l'audit l'a
   correctement laissé là, n'ayant ni sortie ni ligne de provenance.
2. **Vérifier le livrable avant de le croire** : UV sur 100 % des primitives, ≤ 8 000 tris,
   `Muzzle_C` + `Engine_C`, `Cradle_01..03`, et **mesuré contre le chasseur**
   (⚠️ le Specter-9 fait **1,752 × 0,647 × 2,460 m** — pas 1,29, qui est l'agrégat des bornes
   en espace local, sans les transformations de nœuds).
3. Intégrer : `.tres`, `.tscn`, fiche codex + `ROSTER`, gardes dans `test_enemy_hulls.gd`,
   montage `SHIPPED` du banc.
4. **Générer le dôme par le code** depuis `aura_radius` — il doit montrer la portée réelle.

### 3.3 — Les deux familles restantes de la spec §11.1

- **Null Bomber** — lent, encaisse, **pond des mines** derrière lui. Demande un sous-pool de
  mines réservé dans le spawner (**aucun `instantiate()` en jeu**, spec §26.1).
- **Frigate Turret** — ancrée, ne bouge pas, mais **vise** (`Fire.AIMED`), point faible dorsal.
  ⚠️ **Piège déjà payé deux fois** : un `Beam` enfant d'un `Node3D` subit **deux fois** la
  transformation et devient invisible, sans erreur ni test rouge. Poser `top_level = true` dès
  la première ligne. (`leviathan_combat.gd` est le seul endroit du dépôt où ce drapeau
  apparaît — et `HarvesterCombat` n'a jamais été vérifié, cf. backlog P0 bis.)

### 3.4 — Les UV manquantes de deux unités de ce périmètre

`crescent_interceptor` **0/7** et `needle_scout` **0/7** : leurs scripts n'appellent jamais
`ak.box_project_uv()`. Ce n'est pas cosmétique — `codex_screen.gd` leur applique
`HullDetail.apply()`, qui échantillonne alors la feuille de détail **en un seul texel**.
Correctif : une ligne par script (~4,0 tuiles/m pour deux chasseurs), mais **ça change leur
rendu en jeu** — donc à montrer avant/après.

### 3.5 — Différés, avec leur raison

- **Le marquage vert de la Choir Mine** forme une plaque pleine sur le flanc : 0,2 % de l'aire
  vue **par la caméra de jeu**, qui regarde de dessus — mais le bestiaire présente la coque de
  trois quarts et montre un flanc que le jeu ne montre jamais. Les deux mesures sont exactes,
  elles ne répondent pas à la même question. Une ligne dans `build_choir_mine.py` si ça gêne.
- **`AudioManager` n'arrête pas ses flux à la sortie** — passé en P0 bis du backlog, il
  déborde de ce périmètre.

## 4. Ce que ce chantier a appris, et qui vaut toujours

Reprises du plan du 23/08 parce qu'elles ont coûté cher, et confirmées depuis :

- **Un test dit qu'une valeur a changé, jamais que le joueur le voit.** Le télégraphe des mines
  montait l'énergie d'un émissif **déjà saturé** : opération nulle.
- **Une garde sur la mauvaise propriété est pire que pas de garde** — elle ne peut pas échouer,
  et elle rassure. Celle sur les tangentes était vide : Godot les régénère à l'import. Ce sont
  les **UV** qui ne s'inventent pas.
- **Un test de géométrie ne remplace pas un test d'existence.** Cinq tests de mise en page sont
  restés verts pendant que le bandeau du codex avait entièrement disparu.
- **Un différentiel ne vaut que si le témoin ne diffère que par la variable mesurée.**
- **On vérifie ce qui revient d'une délégation, pas ce qu'on a envoyé.**

Ajoutées le 2026-08-25, du même genre :

- **Un calibrage mesure une situation, pas une intention.** Changer la situation l'invalide en
  silence : aucun test ne rougit, l'invariant reste vert, et c'est le playtest suivant qui paie.
- **Un contrat de noms respecté n'est pas une preuve d'échelle.** La coque du boss livrait
  `Ring_01..05` et `Tunnel_End`, corrects de nom, mesurés à 24-33 cm pour un chasseur de 241.
  Toute planche de recette doit porter **une vue avec le chasseur posé à l'échelle**.
- **Un état tenu à la main rouille.** Le champ `Statut` des briefs a été maintenu 5 fois sur
  37. `./scripts/audit-docs.sh` dérive désormais l'état du dépôt.
