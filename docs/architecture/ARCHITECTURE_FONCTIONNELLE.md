# Architecture fonctionnelle — Aegis Ascendant

> Ce que le jeu fait, du point de vue de l'expérience joueur, et où chaque fonction vit dans
> le code. État réel au 2026-07-11. Complète `ARCHITECTURE_TECHNIQUE.md`.

## 1. Pitch & promesse

Vertical shooter « space opera militaire rétrofuturiste » **original** (aucun emprunt de licence).
Le joueur incarne un pilote de la coalition **Helios Vanguard** aux commandes du chasseur
**Specter-9**, traverse une bataille orbitale, monte en puissance, apponte sur la forteresse
**Aegis Citadel**, en prend les commandes et détruit le vaisseau-amiral ennemi **The Pale
Leviathan** (faction **The Null Choir**). Montée en puissance :
`chasseur isolé → appareil surarmé → pilote décisif → commandant d'une forteresse`.

Cible : **démo courte et spectaculaire** (« qui claque »), difficulté volontairement **facile**.

## 2. Boucle de jeu complète (l'arc)

L'ensemble se déroule sans coupure, piloté par le director (machine à phases) :

| # | Phase (interne) | Ce que vit le joueur |
|---|---|---|
| 0 | Écran titre | « AEGIS ASCENDANT », contrôles, **Entrée** pour lancer |
| 1 | `FIGHTER_WAVES` | Pilote le Specter-9, tire, détruit une vague de **Needle Scouts**, ramasse des bonus |
| 2 | `MINI_BOSS` | Affronte le mini-boss **Choir Harvester** (barre de vie, patterns de tir) |
| 3 | `DOCKING` | L'**Aegis Citadel** descend ; le chasseur est guidé (autopilote) dans la baie d'appontage |
| 4 | `COMMAND_TRANSFER` | Bannière « COMMAND TRANSFER », le HUD bascule en mode forteresse |
| 5 | `FORTRESS_BOSS` | Pilote la **forteresse** (déplacement latéral + batteries) contre **The Pale Leviathan** (4 phases) |
| 6 | Finale | **Helios Lance** : explosions en cascade + secousse |
| 7 | `VICTORY` | Écran de victoire : score, rang (S/A/B/C), **Entrée** pour rejouer |

## 3. Contrôles

| Action | Touche | Où |
|---|---|---|
| Déplacement | **← →** (et ↑ ↓ / WASD) | `InputBootstrap`, `PlayerFighterController`, contrôle forteresse dans le director |
| Tir principal | **Espace** | idem |
| Valider (titre / rejouer) | **Entrée** | `boot_screen.gd`, `victory_screen.gd` |

> Manette, remapping, focus/précision, Overdrive, missiles, arme secondaire : **prévus par la
> spec mais pas encore implémentés** (voir `BACKLOG.md`).

## 4. Systèmes fonctionnels

### 4.1 Montée en puissance (Pulse Array, niveaux 1→5)
Les **Power Cores** ramassés augmentent le niveau de tir : la géométrie du tir change (tir jumeau
→ cadence accrue → tirs latéraux → axe central renforcé → éventail complet). *Où :* `PlayerStats`,
`_fire_pattern()` dans `PlayerFighterController`.

### 4.2 Bouclier & survie
100 unités de bouclier, invulnérabilité brève après impact, régénération après un délai calme,
3 vies visuelles, **continues illimités** (respawn tolérant). *Où :* `PlayerShield`, `PlayerFighterController`.

### 4.3 Bonus (pickups)
- **Power Core** (or) → niveau de tir +1
- **Shield Cell** (cyan) → restaure le bouclier
- **Score Prism** (vert) → +500 points

Flottement, rotation, **attraction magnétique** à courte portée, collecte au contact. Drops
**semi-déterministes** à la mort des ennemis avec garantie de Power Core. *Où :* `Pickup`,
`PickupManager`. Sprites = SVG originaux de la forge.

### 4.4 Ennemis
- **Needle Scout** : descente + oscillation, tir frontal lent (implémenté).
- **Choir Harvester** (mini-boss) et **Pale Leviathan** (boss final) : corps sprite, PV, patterns
  RADIAL / AIMED / FAN, phases. *Où :* `EnemyController`, `BossController`.

> Autres familles de la spec (Crescent Interceptor, Choir Mine, Leech Drone, Null Bomber,
> Shield Carrier, Frigate Turret) : **non implémentées**.

### 4.5 Appontage & prise de commande
La Citadelle glisse dans le champ (sens d'échelle), le chasseur est **guidé automatiquement**
dans la baie (assistance, non létal), puis « rangé » ; le HUD se transforme. *Où :* director
(`_start_docking`, `_on_citadel_arrived`, `_on_player_docked`, `_start_command_transfer`),
`AegisCitadel`, `PlayerFighterController.begin_autopilot/stow`.

### 4.6 Phase forteresse
Le joueur déplace la forteresse sur l'axe X et tire les **Twin Rail Batteries**. La forteresse a
une **intégrité** (jauge) ; à 0 elle est réinitialisée (pas d'échec dur). Le boss final enchaîne
**4 phases**. *Où :* director (`_start_fortress_boss`, `_physics_process`, `_fire_battery`,
`_on_fortress_hit`).

### 4.7 Finale & victoire
**Helios Lance** : cascade d'explosions lourdes + forte secousse, puis écran de victoire avec
**rang** calculé sur le score (S ≥ 40k, A ≥ 25k, B ≥ 12k, sinon C) et rejouabilité. *Où :*
`_fire_helios_lance`, `_start_victory`, `VictoryScreen`.

### 4.8 Score
+100 par Needle Scout, +500 par Score Prism, +5000 mini-boss, +20000 boss final. Affiché au HUD
et au résumé. *Où :* `GameState.add_score`, director. *(Multiplicateur, combos, précision,
batteries sauvées : non implémentés.)*

### 4.9 Feedback (« game feel »)
Screen shake sur impacts/morts/tirs lourds, glow/bloom, explosions GPU, traînée moteur, muzzle
flash, SFX sur les événements clés (explosion, pickup, impact, appontage, batterie, Helios Lance).

## 5. Direction artistique (réalisée)

- **Sprites issus des concepts IA de la forge** : Specter-9 (joueur), Aegis Citadel (forteresse),
  Pale Leviathan (boss), Choir Harvester (mini-boss).
- Palette : allié cyan/blanc/or, ennemi magenta/corail, fond spatial sombre. Projectiles
  contrastés par équipe. Fond nébuleuse procédural.
- Provenance de tous les assets dans `assets/licenses/ASSET_PROVENANCE.csv`.
- **Interdits IP respectés** : aucun élément de licence existante ; 7 planches de référence
  contaminées ont été mises en quarantaine hors dépôt (ADR-0005).

## 6. Univers (canon)

| Élément | Nom |
|---|---|
| Coalition alliée | **Helios Vanguard** |
| Chasseur joueur | **Specter-9** |
| Porte-chasseur | **Aurora Spear** *(concept produit, non intégré)* |
| Forteresse | **Aegis Citadel** |
| Ennemi | **The Null Choir** |
| Mini-boss | **Choir Harvester** |
| Vaisseau-amiral | **The Pale Leviathan** |

## 7. Difficulté & accessibilité (état)

- Difficulté **unique**, facile/tolérante (bouclier généreux, continues illimités, boss abordable).
- **Non implémentés** : modes Story/Vanguard/Ace, difficulté adaptative, options d'accessibilité
  (remapping, réduction shake/flash, contraste, sous-titres, volumes séparés), tutoriel contextuel,
  menu d'options.

## 8. Écart au cahier des charges (résumé fonctionnel)

Livré : boucle complète chasseur→forteresse→boss, montée en puissance, bonus, mini-boss, appontage,
boss multi-phase, victoire, score, VFX, sprites IA, SFX.
Non livré (voir `BACKLOG.md`) : missiles, Overdrive, drones orbitaux, configs de tir (Spread/Lance/
Orbit), autres familles d'ennemis, objectifs de défense de batteries, musique, options/accessibilité,
manette, checkpoints formels, statistiques de fin détaillées.
