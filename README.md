# Aegis Ascendant

Prototype jouable de **vertical shooter 2.5D/3D** — space opera militaire rétrofuturiste original.
Un niveau complet (12–15 min) : chasseur léger → bataille orbitale → appontage → contrôle d'une
forteresse de guerre → boss final multi-phase.

- **Moteur** : Godot 4.7-stable, renderer Forward+, GDScript typé
- **Cible** : Windows 10/11 x64 (`build/windows/AegisAscendant.exe`)
- **Cahier des charges** : [`docs/SPEC_AEGIS_ASCENDANT.md`](docs/SPEC_AEGIS_ASCENDANT.md)
- **Décisions d'architecture** : [`docs/decisions/`](docs/decisions/)

## Démarrage rapide (WSL2)

```bash
./scripts/bootstrap.sh     # installe Godot 4.7 + export templates (vérification SHA512)
./scripts/check.sh         # import headless + tests
./scripts/export-win.sh    # export Windows (debug par défaut)
./scripts/deploy-win.sh    # copie vers C:\tmp\aegis-ascendant et lance le jeu sous Windows
```

Le développement et les contrôles tournent **headless dans WSL** ; le rendu réel s'exécute
**nativement sous Windows** (voir `docs/decisions/ADR-0002`).

## État du projet

- [x] Phase 0 — Bootstrap (dépôt, projet Godot, scripts, tests, export Windows)
- [ ] Phase 1 — Graybox jouable *(en cours : chasseur, tir, ennemis, vague)*
- [ ] Phase 2 — Vertical slice
- [ ] Phase 3 — Niveau complet
- [ ] Phase 4 — Art pass
- [ ] Phase 5 — Polish
- [ ] Phase 6 — Optimisation et release

## Univers (créations originales)

| Élément | Nom |
|---|---|
| Coalition humaine | **Helios Vanguard** |
| Chasseur du joueur | **Specter-9** |
| Forteresse mobile | **Aegis Citadel** |
| Ennemi | **The Null Choir** |
| Vaisseau-amiral ennemi | **The Pale Leviathan** |

Toutes les créations (noms, silhouettes, sons, musiques) sont originales — voir `LICENSES.md`
et `assets/licenses/ASSET_PROVENANCE.csv`.
