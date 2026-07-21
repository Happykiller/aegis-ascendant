# BRIEF-0035 — Specter-9 : casser le monobloc, ailes à flèche variable

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-21

## Objectif

Deux choses, la première étant de loin la plus importante :

1. **Le vaisseau doit cesser d'être une surface continue.** La planche est un **assemblage de
   volumes séparés par du vide** — un fuselage, deux nacelles, deux ailes, avec de l'air entre eux.
   Le nôtre est un triangle d'un seul tenant sur lequel on a dessiné des lignes.
2. **Ailes à flèche variable** : elles se referment à l'accélération, s'ouvrent au freinage.

## Contexte — le diagnostic, à la troisième tentative

BRIEF-0033 a corrigé le profil. BRIEF-0034 a corrigé la répartition des masses. Les deux ont
amélioré la coque **sans jamais toucher au vrai défaut**, que le propriétaire a fini par nommer :

> « on a un triangle monobloc, alors que l'artwork reprend le principe du fuselage, et des ailes »

Regarde la planche avec `Read` — vues « VUE DESSUS » et « VUE DESSOUS ». Ce qu'il faut y voir n'est
pas un dessin, c'est une **topologie** :

- le fuselage central est un corps **fermé sur lui-même**, avec ses propres flancs ;
- chaque nacelle est un corps fermé, **séparée du fuselage par une fente visible de part en part** ;
- chaque aile est une **lame distincte**, greffée au flanc externe de la nacelle, avec une
  **échancrure** entre son bord d'attaque et la nacelle ;
- on voit **le fond de l'image** entre ces corps, à plusieurs endroits.

## Le critère d'acceptation — un test de silhouette, pas une opinion

Rends la coque **en aplat noir sur fond blanc**, vue de dessus. Sur cette image :

- on doit **voir du blanc pénétrer entre les volumes** — au minimum deux échancrures franches par
  côté (fuselage/nacelle, et nacelle/bord d'attaque d'aile) ;
- la silhouette ne doit plus être un polygone convexe.

Aujourd'hui cet aplat est un triangle plein. **Mets cette image dans le rapport**, avant/après. Si
elle ne montre pas ces trouées, le brief n'est pas rempli — quel que soit le reste.

C'est délibérément un critère **binaire et mesurable** : deux briefs ont échoué parce que je
décrivais une intention (« plus fuselé », « redistribuer les masses ») au lieu d'un test.

## Ailes à flèche variable

Le kit sait désormais imbriquer les pièces mobiles (`ak.moving_part(..., parent="…")`, cf.
`tools/blender/test_moving_parts.py`). Structure demandée :

| Pièce | Parent | Pivot | Mouvement (côté Godot) |
|---|---|---|---|
| `Wing_L` / `Wing_R` | — | emplanture, au flanc de la nacelle | rotation autour de l'axe **vertical** : flèche |
| `Flap_L` / `Flap_R` | **`Wing_L` / `Wing_R`** | bord de fuite de l'aile | battement, comme aujourd'hui |
| `Nozzle_L` / `Nozzle_R` | — | col de tuyère | ouverture par mise à l'échelle |

- **Position de repos = ailes DÉPLOYÉES** (flèche minimale). C'est l'état neutre, celui que le `.glb`
  montre et que le contrat mesure.
- **Débattement visé : 20 à 30° de flèche supplémentaire.** Donne-moi la valeur que la géométrie
  supporte réellement, **mesurée** comme tu l'as fait pour les volets — et **remesurée à chaque
  build**. L'aile ne doit ni entrer dans la nacelle, ni sortir de la boîte englobante en position
  repliée.
- ⚠️ **La bbox est mesurée au REPOS.** Une aile qui dépasse une fois repliée passera le contrat sans
  un mot — c'est exactement le piège qui a fait tomber le dégagement d'un volet à 2,8° au brief
  précédent. Vérifie les deux poses et dis-le.

## Contraintes

- **Dimensions X/Z : 1,75 × 2,46 m à ±3 %**, ailes **déployées**. Inchangé.
- **Hauteur Y** : 0,62-0,72 m.
- **Budget : 60 000 triangles.** Actuel : 45 828. Séparer des volumes coûte des faces (chaque corps
  se ferme) : c'est un usage légitime de la marge.
- ⚠️ **Lisibilité en vue de jeu.** Des trouées dans la silhouette peuvent la rendre plus difficile à
  suivre à 48 px. Juge la vue « game » et dis-moi franchement. La DA §6 exige que le joueur soit
  identifiable en moins de 200 ms — si les échancrures cassent la lecture, propose l'arbitrage.
- Palette, 7 matériaux, UV, points d'attache : inchangés. Livrée tricolore et marquages chiffrés
  toujours exclus (`ADR-0014`).
- **Détails en FRACTION de la géométrie porteuse**, jamais en coordonnée absolue :
  `.claude/resources/pratique-detail-en-fraction-de-corde.md`. Le plan bouge encore une fois ; c'est
  la troisième, et les deux précédentes ont envoyé des bandeaux dans le vide.
- **Déterminisme** : `./scripts/build-hull.sh --check specter_9`.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_specter_9.py` | script retravaillé |
| `assets/imported/models/ships/specter_9.glb` | coque + 6 pièces mobiles (LFS) |
| `docs/forge/output/BRIEF-0035-report.md` | mesures, **aplats noirs avant/après**, débattement de flèche mesuré, verdict de lisibilité |

## Critères d'acceptation

- [ ] **L'aplat noir vu de dessus montre des trouées** — au moins deux par côté. **Le critère n°1.**
- [ ] `Wing_L/R` sont des pièces mobiles ; `Flap_L/R` sont leurs **enfants**
- [ ] Débattement de flèche mesuré et remesuré à chaque build, ailes déployées au repos
- [ ] Bbox X/Z inchangée à ±3 % **au repos**, et vérifiée **aussi en position repliée**
- [ ] `./scripts/build-hull.sh --check specter_9` : déterminisme OK
- [ ] ≤ 60 000 triangles ; UV et tangentes présentes ; 10 points d'attache conservés
- [ ] Aucune bande rouge de livrée, aucun chiffre

## Hors périmètre

Ne pas toucher au code Godot ni à `aegis_kit.py` (il vient d'être étendu pour ce brief : parentage
des pièces + bbox en position monde). Signaler les manques dans le rapport. Pas de texture, pas de
`.blend`.
