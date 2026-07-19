# ADR-0005 — Quarantaine des planches de référence IP-contaminées

- **Date** : 2026-07-11
- **Statut** : **superseded par [ADR-0009](ADR-0009-reference-ip-reinstauree.md)** (2026-07-19) —
  décision du propriétaire pour ce projet personnel non commercial : les planches sont sorties de
  quarantaine, versionnées dans `assets/source/references/` et réinstaurées comme référence visuelle.
  Le texte ci-dessous reste l'archive de la décision d'origine.

## Contexte

La première grande passe de l'atelier `asset-forge` (session Codex + imagegen) a produit,
en plus des livrables originaux, **7 planches de « référence » raster** générées via ChatGPT :
`assets/source/concepts/reference_*.png`. L'index qui les accompagnait
(`REFERENCE_INDEX.md`) documente honnêtement qu'elles **contiennent des marques déposées
visibles** — « Macross », « Valkyrie », « Zentradi », « Raiden », « VF-class » — et des
silhouettes non originales (livrée évoquant le VF-1). L'atelier les avait délibérément
exclues de la provenance et marquées « non livrables ».

Ces fichiers violent les interdictions de la spec §0.2 et §3 (aucun élément identifiable
d'une licence ; aucun asset reproduisant une marque). Même non importés dans le jeu, les
laisser dans l'arbre versionné les ferait entrer de façon permanente dans l'historique git/LFS.

## Décision

- Les 7 `reference_*.png` et leur `REFERENCE_INDEX.md` sont déplacés dans `/_ip_quarantine/`
  à la racine, **répertoire gitignoré** — conservés en local pour consultation, jamais versionnés.
- Les **8 planches de concept structurées** (specter_9, aegis_citadel, pale_leviathan,
  aurora_spear, choir_harvester, null_choir_enemy_families, docking_environments,
  radio_characters) sont des **créations originales** (aucun texte de licence, silhouettes
  divergentes), provenancées, et **conservées** comme sources de production.

## Conséquences

- Aucune marque tierce n'entre dans l'historique du dépôt.
- Toute production future repart de la charte (`docs/forge/CHARTE_CREATIVE.md`) et du canon,
  jamais de ces références.
- Règle générale actée : l'atelier ne doit plus déposer d'images générées portant un nom de
  licence, même à titre de « référence interne » — à défaut, elles sont quarantinées à la revue.
- Rappel opérationnel : ne jamais `git add -f` sous `/_ip_quarantine/`.
