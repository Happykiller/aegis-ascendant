---
titre: Normes de code, de nommage et de test
type: regle
statut: actif
maj: 2026-08-23
---

# Normes

Source : `docs/SPEC_AEGIS_ASCENDANT.md` §31, rappelée dans `CLAUDE.md`.

## Code

- **GDScript typé partout.** Pas d'exception de confort.
- **Composition > héritage** ; les événements passent par des **signaux**.
- Les **paramètres de gameplay** vivent dans des Resources typées (`resources/data/*.gd`), jamais en
  dur dans le code. Chaque Resource expose `validate()`.
- **Zéro allocation dans les boucles critiques** : tableaux Packed préalloués, pooling obligatoire.

## Nommage

| Objet | Forme |
|---|---|
| Fichiers | `snake_case.gd` |
| Classes | `PascalCase` |
| Constantes | `UPPER_SNAKE_CASE` |

## Versionnement

- **Committer les `*.uid`** générés par Godot ; `.godot/` et `build/` sont gitignorés.
- Binaires (`*.png`, `*.wav`, `*.ogg`, `*.glb`, `*.blend`) → **Git LFS** (spec §24.8).
- Le dépôt est **local** ; son remote est `github-perso` (`Happykiller/aegis-ascendant`).

## Tests

- Runner maison, pas de framework tiers (spec §28.1). Les assertions **accumulent** les échecs au
  lieu d'interrompre le run.
- **Les tests n'ont pas d'arbre de scène** (mode `--script`, autoloads absents) : chaque unité
  s'instancie à la main.
- ⚠️ Un test qui construit un **`Node`** doit le confier à `track()` : sans parent pour le récupérer,
  il survit jusqu'à la fin du process. Godot n'en rend compte qu'à la sortie, en un total qui ne
  désigne jamais son coupable. Coût de l'oubli : **789 objets fuités** dans la sortie du check, un
  diagnostic hérité faux pendant des semaines, et l'instrument rendu aveugle à une vraie fuite.
  → `.claude/resources/pratique-verifier-par-test.md`.
