---
titre: Arborescence — le rôle de chaque dossier de premier niveau
type: dat
statut: actif
maj: 2026-08-23
---

# Arborescence

| Dossier | Rôle | À savoir |
|---|---|---|
| `scripts/` | Tout le GDScript, rangé par domaine (`core/`, `gameplay/`, `player/`, `enemies/`, `bosses/`, `projectiles/`, `fx/`, `vfx/`, `ui/`, `audio/`, `pickups/`, `fortress/`, `debug/`) | Les **scripts shell** du projet (`check.sh`, `play.sh`, `export-win.sh`…) vivent dans ce même dossier, à sa racine, aux côtés des sous-dossiers de GDScript |
| `resources/` | Les **Resources typées** de gameplay (`data/`, `enemies/`, `bosses/`, `weapons/`, `player/`, `audio/`, `codex/`, `encounters/`, `ui/`, `vfx/`, `graphics/`) | Aucun paramètre de gameplay en dur dans le code : il vit ici, et chaque Resource expose `validate()` |
| `scenes/` | Les scènes `.tscn` | |
| `shaders/` | Les `.gdshader` (post-traitement rétro, atmosphère de planète, fond) | |
| `tests/` | Runner maison + `tests/unit/` + `tests/perf/` | Les tests n'ont **pas d'arbre de scène** : ils instancient leurs unités à la main |
| `tools/` | Outils Python et Blender de la chaîne d'assets | Ne pas réinventer une de ces procédures : cf. le tableau « Outillage encodé » de [`.claude/resources/INDEX.md`](../../../.claude/resources/INDEX.md) |
| `scripts-win/` | `run.ps1`, le lanceur côté Windows | Fichier en CRLF par `.gitattributes` |
| `assets/` | Trois compartiments étanches : `imported/` (le runtime), `source/` (ce qui **fabrique** du runtime), `reference/` (ce qu'on **regarde**) | La frontière `concepts/` vs `inspiration/` rend possible une purge IP — voir `assets/README.md` et ADR-0009 |
| `docs/` | Spec, ADR, design, forge, balance, architecture, backlog — et cette KB | |
| `build/` | Sortie d'export Windows | **Gitignoré**, comme `.godot/` |

## Le piège d'arborescence propre à ce projet

`assets/source/` contient des livrables de forge qui **dorment** : plusieurs ont été explicitement
écartés par un ADR. Leur présence sur le disque n'est pas un feu vert d'intégration.
`assets/source/README.md` dit, fichier par fichier, ce qui alimente le jeu et ce qui dort.
