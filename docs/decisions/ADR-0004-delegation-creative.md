# ADR-0004 — Délégation créative par sous-agent et briefs versionnés

- **Date** : 2026-07-11
- **Statut** : accepté (décision utilisateur)

## Contexte

Le projet mêle deux natures de travail : (a) conception/architecture/code, exigeant la vision
d'ensemble et la continuité du contexte ; (b) production créative ou répétitive (assets, palettes,
scripts Blender, lore, SFX, prompts de génération), volumineuse et parallélisable. L'utilisateur
veut que la session principale reste « le grand concepteur » et que (b) soit systématiquement
délégué à un agent au contexte séparé, piloté par des instructions écrites réutilisables.

## Décision

- Un sous-agent dédié **`asset-forge`** est défini dans `.claude/agents/asset-forge.md`
  (spec §30.2, famille asset-integrator). Contexte isolé, périmètre restreint aux livrables
  créatifs — il ne touche jamais `scenes/`, `scripts/` (hors `tools/`), `project.godot`, ni les tests.
- Ses instructions vivent dans des fichiers versionnés :
  - `docs/forge/CHARTE_CREATIVE.md` — bible créative permanente (palettes, silhouettes, interdits IP, formats) ;
  - `docs/forge/BRIEF_TEMPLATE.md` — gabarit de mission ;
  - `docs/forge/briefs/BRIEF-NNNN-<slug>.md` — une mission = un brief.
- Boucle : le concepteur rédige le brief → invoque `asset-forge` → l'agent livre + remplit
  `assets/licenses/ASSET_PROVENANCE.csv` → le concepteur review (charte, IP, formats) → intègre → commit.

## Conséquences

- Le savoir-faire créatif s'accumule dans des fichiers relisibles et rejouables, pas dans des
  conversations éphémères ; un brief peut être ré-exécuté ou raffiné.
- La revue IP (spec §0.2/§3) a un point de contrôle unique : la review du concepteur.
- La montée en charge (Blender, textures, musique…) n'exige que de nouveaux briefs, pas de
  nouveau dispositif.
