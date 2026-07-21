# BRIEF-0020 — Extraction des sprites héros depuis les planches de concept

> ⚠️ **CADUC — ne pas rejouer.** Les sprites livrés par ce brief ont été **supersédés par
> l'ADR-0008** (passage aux coques 3D glTF) : plus aucune scène ne les chargeait. Ils ont été
> purgés de `assets/imported/sprites/` le 2026-07-21, avec leurs lignes de provenance. Les chemins
> cités plus bas ne pointent donc plus sur rien — le brief est conservé comme trace de ce qui a été
> produit et pourquoi ça n'a pas tenu, pas comme instruction.

- **Statut** : caduc (livré, puis supersédé par ADR-0008)
- **Ancien statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-11

## Objectif

Extraire, depuis les planches de concept originales (`assets/reference/concepts/*.png`), des **sprites
PNG à fond transparent** utilisables directement en `Sprite3D` dans le jeu : le vaisseau du
joueur et les grandes structures/boss. C'est l'élément qui fera « l'art IA dans le jeu ».

## Contexte

Le jeu est un vertical shooter vu de dessus/léger angle. Les planches de concept contiennent,
parmi plusieurs vues, une **vue principale exploitable** par asset (vue de dessus pour le
chasseur, vue de face/principale pour les structures). Le fond des planches est un bleu nuit
uniforme quadrillé. Il faut isoler proprement le sujet principal.

## Livrables (chemins exacts, PNG RGBA à fond transparent)

| Fichier | Source | Vue à extraire | Orientation cible |
|---|---|---|---|
| `assets/imported/sprites/ships/specter_9.png` | `concepts/specter_9_concept_sheet.png` | grande vue de dessus (héros) | nez vers le HAUT |
| `assets/imported/sprites/structures/aegis_citadel.png` | `concepts/aegis_citadel_concept_sheet.png` | grande vue de face principale | baie d'appontage vers le BAS |
| `assets/imported/sprites/bosses/pale_leviathan.png` | `concepts/pale_leviathan_concept_sheet.png` | grande vue principale | menace vers le BAS |
| `assets/imported/sprites/bosses/choir_harvester.png` | `concepts/choir_harvester_concept_sheet.png` | vue principale (3 bras) | vers le BAS |
| `assets/imported/sprites/ships/needle_scout.png` | `concepts/null_choir_enemy_families_sheet.png` | 1re famille (Needle Scout), vue nette | nez vers le BAS |

## Méthode recommandée

- Outil : Python + Pillow (`pip install --user Pillow` si absent) ou ImageMagick si dispo.
- Détourage : color-key du fond bleu nuit avec **flood-fill depuis les 4 bords** (préserver les
  zones sombres INTERNES du sujet), tolérance ajustée, puis léger feathering de l'alpha (1-2 px)
  pour éviter les franges. Retirer le quadrillage/annotations autour du sujet.
- Recadrage serré sur le sujet (bounding box de l'alpha non nul), marge ~4 %.
- Rotation si nécessaire pour respecter l'orientation cible.
- Taille finale : côté max ~1024 px, PNG-32.
- **Vérifier** : alpha propre (pas de halo bleu résiduel), sujet centré, pas de bout de panneau voisin.

## Provenance

Une ligne par sprite dans `assets/licenses/ASSET_PROVENANCE.csv` :
`asset_type=sprite`, `source_tool=asset-forge (extraction from concept)`,
`modified_by=asset-forge`, `prompt_file=docs/forge/briefs/BRIEF-0020-hero-sprites-extraction.md`,
`notes` = planche source + vue extraite. (Append shell, ne pas réécrire le CSV.)

## Critères d'acceptation

- [ ] 5 PNG RGBA livrés aux chemins exacts, fond 100 % transparent (alpha 0 hors sujet)
- [ ] Aucun résidu de fond bleu / quadrillage / texte de planche autour du sujet
- [ ] Orientations respectées (joueur nez en haut ; ennemis/structures vers le bas)
- [ ] Provenance renseignée pour chaque sprite
- [ ] Compte-rendu : méthode, tolérances, limites par sprite

## Hors périmètre

Pas de retouche stylistique, pas de recoloration, pas de modèles 3D — extraction/détourage
seulement. Ne pas toucher au code ni aux scènes. Les planches `reference_*` quarantinées ne
doivent JAMAIS être utilisées.
