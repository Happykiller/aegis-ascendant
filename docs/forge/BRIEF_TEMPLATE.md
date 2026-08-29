# BRIEF-NNNN — <titre court de la mission>

- **Statut** : brouillon | assigné | livré | intégré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : AAAA-MM-JJ

## Objectif

Ce que la mission doit produire, en une ou deux phrases.

## Contexte

Pourquoi ce livrable est nécessaire, où il sera utilisé dans le jeu, références aux sections
utiles de la charte (`docs/forge/CHARTE_CREATIVE.md`) ou de la spec.

## Contraintes

- IP : rappel des interdits applicables (toujours).
- Palette / DA : couleurs et règles de silhouette applicables.
- Techniques : formats, tailles, budgets (poly/texture/duration), compatibilité Godot 4.7.

## Texture (ADR-0028 — OBLIGATOIRE, deux issues, jamais de silence)

⚠️ **Cette section ne peut pas être omise.** Un brief sans elle est incomplet, au même titre qu'un
livrable sans chemin. C'est ici qu'on décide si l'asset a une matière — et ce moment n'existait pas
avant `ADR-0028`.

Trancher, explicitement :

- **soit** l'asset dépend d'une ou plusieurs demandes de texture — les **nommer** :
  `docs/forge/textures/TEX-NNNN-<slug>.json` (contrat : `docs/forge/textures/README.md`) ;
- **soit** il n'en faut aucune — **écrire pourquoi**. « PBR par facteurs, pièce vue de loin et
  jamais en gros plan » est une réponse valable ; le silence n'en est pas une.

**Dans les deux cas**, dire quel dépliage la géométrie doit porter :

| Usage | Dépliage attendu |
|---|---|
| Pièce vue de loin, sans carte de détail | `ak.box_project_uv()`, en donnant les tuiles/m |
| Surface qui portera une carte de détail | dépliage **continu**, densité de texels **homogène**, coutures **hors champ** — et une planche de contrôle au damier UV |

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `chemin/exact/du/fichier` | ce que c'est |

## Provenance

Ligne(s) à ajouter dans `assets/licenses/ASSET_PROVENANCE.csv` pour chaque asset livré.

## Critères d'acceptation

- [ ] Critère vérifiable 1
- [ ] Critère vérifiable 2
- [ ] **UV présentes et `TEXCOORD_0` COMPTÉ dans le `.glb`** — compté, jamais supposé (`ADR-0028`).
      ⚠️ Trois coques du dépôt sont sorties sans UV et le défaut est **totalement silencieux** :
      ni erreur d'import, ni test rouge. Une coque sans UV est inhabitable sans reforge
- [ ] Densité de texels **mesurée** et emplacement des coutures donnés au rapport, si le brief
      demande un dépliage continu

## Hors périmètre

Ce que la mission ne doit PAS faire (éviter la dérive).

---

## ⚠️ Si le brief demande un KIT : figer les noms dans le brief

Un kit est assemblé par le **moteur**, qui va chercher chaque pièce **par son nom exact**. Le
brief doit donc porter une table, et pas une intention :

| Nœud | Ce que c'est | Repère |
|---|---|---|
| `<nom_exact>` | … | origine au point d'assemblage |

Trois kits ont été livrés ainsi (`bay_kit`, `turret_kit`, `spine_kit`) et **les trois se sont
assemblés sans une seule itération** — la forge rendant en plus la table des emprises mesurées,
qui dit au moteur où poser chaque pièce.

Laisser le choix des noms à la forge ne fait pas gagner de temps : ça déplace la même décision
d'un cran, et elle revient sous forme de code d'assemblage à réécrire. Un renommage ultérieur
casse le niveau **en silence** — le moteur ne trouve rien et ne dit rien.
