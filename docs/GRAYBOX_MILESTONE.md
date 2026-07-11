# Jalon graybox — statut (2026-07-11)

Fin de la « première séquence de travail » (spec §37) : Phase 0 complète + début de graybox
jouable. Vérifié headless (WSL) et sur build Windows natif (RTX 4080).

## Livré et vérifié

| Domaine | État |
|---|---|
| Dépôt, hygiène git, Git LFS (spec §24.8) | ✅ |
| Godot 4.7 + export templates (bootstrap idempotent, SHA512) | ✅ |
| Projet Godot, autoloads GameState/SceneRouter, scène Boot | ✅ |
| Scripts bash canoniques (`bootstrap/check/export-win/deploy-win`) | ✅ |
| Test runner headless + 32 tests (plan, pool, collision, health, wave, transitions) | ✅ vert |
| Export Windows x64 + lancement natif vérifié | ✅ |
| Plan logique 2D, chasseur arcade pilotable (accel < 250 ms, bank visuel ≠ hitbox) | ✅ |
| BulletManager data-oriented (600 max, grille spatiale, MultiMesh, 2 équipes) | ✅ |
| Needle Scout (composition, HealthComponent, destruction, score) | ✅ |
| WaveSpawner data-driven (10 scouts préinstanciés, `wave_cleared`) | ✅ |
| Passe créative forge intégrée (concepts, SVG, SFX) via LFS + provenance | ✅ |

## Performance (voir `docs/balance/graybox_baseline.md`)

- Bench headless BulletManager : `step()` moyen **0,321 ms** à 600 projectiles (budget 2,0 ms).
- Build Windows : 60 FPS constants (verrouillés V-Sync), Vulkan Forward+ RTX 4080.

## Limitations connues / différé volontaire (revue de code)

Points relevés par la review multi-agents, différés avec justification (aucun n'affecte le
jalon) :

- **Joueur non vulnérable** : le chasseur n'est pas encore enregistré comme `BulletTarget` —
  les tirs ennemis le traversent. Normal : le système bouclier/invulnérabilité/respawn
  (spec §8.3) est une tâche de l'itération suivante. **Priorité n°1 du prochain incrément.**
- **Swept collision absente** (spec §21.2) : la collision est ponctuelle. Aux vitesses graybox
  (balle joueur 0,4 u/frame < portée 0,57 u) aucun tunneling ne se produit ; à implémenter
  avant d'introduire des projectiles rapides.
- **Rendu MultiMesh par `set_instance_transform`** (600 appels/frame) : correct et dans le
  budget (6× de marge) ; un passage à `MultiMesh.buffer` en bloc est l'optimisation naturelle
  si le profil Windows le justifie plus tard.
- **Bench headless** ne mesure pas le chemin de rendu (impossible sans GPU en WSL) ; ce chemin
  est couvert par le relevé FPS sur build Windows.
- Constantes de présentation (`MUZZLE_OFFSET`, lissage du roulis) en dur : acceptables comme
  constantes nommées ; migreront vers des Resources si elles deviennent des paramètres d'équilibrage.

## Suivi créatif (voir `docs/forge/REVIEW_NOTES.md`)

- 7 planches de référence IP-contaminées quarantinées hors dépôt (ADR-0005).
- BRIEF-0019 (frégates) : prompt livré, planche raster à générer.
- Notes de modélisation : épaules Aegis Citadel, noyau Pale Leviathan à décentrer.
- Arbitrage couleur des explosions (chaud vs froid) à trancher en Phase 1.

## Prochaine itération (hors périmètre de ce jalon)

Vulnérabilité joueur + bouclier + invulnérabilité (spec §8.3), bonus/pickups et progression de
puissance (spec §10), HUD chasseur, puis montée vers la vertical slice (spec Phase 2).
