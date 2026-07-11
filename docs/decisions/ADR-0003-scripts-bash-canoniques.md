# ADR-0003 — Scripts canoniques en bash, PowerShell réduit au lancement Windows

- **Date** : 2026-07-11
- **Statut** : accepté

## Contexte

La spec (§23, §27.3) prévoit un dossier `scripts-win/` de scripts PowerShell (bootstrap, run,
check, build) en supposant un développement sous Windows. Or le développement se fait dans WSL
(ADR-0002) avec un Godot **Linux** : des `.ps1` pilotant un binaire Linux depuis Windows n'ont
pas de sens.

## Décision

- Les scripts canoniques (CI locale) sont en **bash** dans `scripts/` : `bootstrap.sh`,
  `check.sh`, `export-win.sh`, `deploy-win.sh` (tous `set -euo pipefail`).
- `scripts-win/` ne contient que ce qui s'exécute réellement côté Windows : `run.ps1`
  (lancement du build exporté, préférence au wrapper console en debug).
- Le contrat de la spec §0 (« exécuter les contrôles prévus dans scripts/check.ps1 ») est rempli
  par `scripts/check.sh`, à contenu équivalent.

## Conséquences

- Une CI Windows future réintroduirait les `.ps1` complets de la spec ; le découpage actuel les
  rend faciles à ajouter (mêmes étapes, même Godot CLI).
- `.gitattributes` force LF pour `*.sh` et CRLF pour `*.ps1`.
