# Baseline de performance — jalon graybox (2026-07-11)

Mesures de référence à l'issue de la séquence §37 (Phase 0 + début graybox).
À re-mesurer à chaque évolution significative du BulletManager ou de la scène.

## Bench headless BulletManager (WSL, CPU)

Commande : `godot4 --headless --path . --script res://tests/perf/bench_bullets.gd`

Charge : pool plein constant (150 projectiles alliés + 450 ennemis = budget max spec §21.3)
+ 20 cibles enregistrées, 3600 steps simulés (60 s à 60 Hz).

| Métrique | Valeur | Budget (spec §25.3) |
|---|---|---|
| step() moyen | **0,321 ms** | < 2,0 ms |
| step() max | 0,931 ms | — |

Verdict : **~6× de marge** sous le budget gameplay CPU au plafond de projectiles.

## Build Windows (RTX 4080, fenêtre 1920×1080, build debug)

Commande : `./scripts/deploy-win.sh -- --print-fps --quit-after 2500 ++ --goto-graybox`

- **60 FPS constants, 16,66 ms/frame** — verrouillés par la V-Sync (aucun pic observé
  sur ~40 s de scène graybox avec vague et projectiles).
- Renderer effectif : `Vulkan 1.4.325 - Forward+` sur RTX 4080.

Limites de cette mesure :

- La V-Sync masque la marge réelle du GPU : la cible 120 FPS (spec §25.2) sera vérifiée
  avec un mode fenêtré sans V-Sync ou un moniteur haute fréquence lors du profilage Phase 1.
- Build **debug** (template debug + wrapper console) : le build release sera plus rapide.
- D3D12 (spec §25.1 : à tester en priorité) non encore comparé à Vulkan — à faire en Phase 1.
