---
titre: Les quatre couches — où va ce que j'écris
type: dat
statut: actif
maj: 2026-08-29
---

# Les quatre couches

**Décidé par [`ADR-0039`](../../decisions/ADR-0039-le-jeu-a-quatre-couches.md), le 2026-08-29.**
Avant cette date, la troisième n'existait pas : le runtime commun vivait dans le script du
niveau 1, et le niveau 2 s'est joué sans voix, sans explosions d'ennemi, sans écrasement et sans
zones de debug. Quatre défauts, **aucun message d'erreur**.

## La question qui range tout

> **Est-ce que le niveau 3 en aura besoin sans rien y changer ?**
> Si oui → runtime. Sinon → level design.

## Les couches

| Couche | Où | Ce qu'on y met |
|---|---|---|
| **Données** | `resources/data/*.gd` + `resources/**/*.tres` | Ce qu'est une chose. `EnemyData` porte 38 caractéristiques : tir, cadence, projectile, poids, hitbox, surface de contact, trajectoire, effet. **Une caractéristique nouvelle va ici, pas dans un script.** |
| **Moteur** | `scripts/gameplay/`, `scripts/projectiles/`, `scripts/enemies/`, `scripts/core/` | Comment ça marche. Modules purs, testables seuls : `BulletManager`, `GameplayPlane`, `PlaneCollider`, `MassRules`, `HealthComponent`, `EnemyPath/Fire/Homing`, `WaveSpawner`. |
| **Runtime** | `combat_runtime.gd`, `level_root.gd`, `boss_stage.gd` | Les LOIS d'une partie : mourir, toucher, percuter, annoncer, parler. Le montage d'un niveau. La mise en scène d'un boss. |
| **Level design** | `graybox_root.gd`, `cortege_root.gd`, Resources de contenu | Ce qui n'est vrai que d'ICI : quelles vagues, quels boss, quel décor, quel enchaînement, quelles répliques. |

## Les trois pièges que cette structure supprime

⚠️ **Un effet oublié ne ressemble pas à un bug.** Un ennemi qui meurt sans exploser, sans bruit
et sans bonus se joue très bien — il a juste l'air pauvre. Aucun test ne le voit. C'est pour ça
que ces effets sont des LOIS et non des lignes à recopier.

⚠️ **Brancher source par source finit toujours par en oublier une.** Le runtime adopte les
unités **par le groupe `enemies`**, jamais spawner par spawner. Le niveau 1 en a deux, le
niveau 2 en a huit.

⚠️ **`setup_level()` s'appelle explicitement.** Ce n'est pas `_ready()` : un `super._ready()`
oublié ne se voit pas à la lecture, une ligne manquante si.

## Ce qui reste à faire

L'**arc** d'un niveau est encore du code — `graybox_root.gd` enchaîne ses six phases à la main.
Le transformer en donnée (`EncounterDirector` piloté par une Resource) est l'étape suivante,
au backlog. Elle est possible sans rien casser depuis `ADR-0039`.

## La garde

`scripts/lint-regles.sh` refuse un script racine de niveau qui ne convoque pas `CombatRuntime`.
Le message dit exactement ce qui manquerait : *« ses ennemis n'exploseront pas, ne feront pas de
bruit, ne laisseront pas de bonus, et sa navigatrice sera muette »*.
