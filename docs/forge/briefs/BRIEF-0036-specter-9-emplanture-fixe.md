# BRIEF-0036 — Specter-9 : l'aile sort d'une emplanture, elle n'est pas boulonnée à côté

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-21

## Objectif

**Intégrer les ailes mobiles à la coque, à la manière d'un F-14.** Aujourd'hui elles pendent à côté
du vaisseau, reliées par un bras de pivot visible au-dessus d'une fente. Il leur faut une
**emplanture fixe** — un karman large et en flèche, solidaire de la coque — d'où le panneau mobile
**sort**, et contre laquelle il vient se plaquer en flèche maximale.

## Contexte — ce qui a marché et ce que j'ai sur-corrigé

BRIEF-0035 a réussi son objectif : la silhouette n'est plus un triangle plein, elle montre des
échancrures franches entre fuselage et nacelles. **Ces échancrures-là restent** : elles ne sont pas
en cause.

Ce qui ne va pas, c'est **la jonction aile/coque**. J'avais demandé « de la séparation » et « du vide
entre les volumes » sans distinguer les jonctions : le résultat est une aile suspendue à un bras,
au-dessus d'un trou. Vu en jeu, elle ne fait pas partie de l'appareil.

Le propriétaire l'a formulé ainsi : *« les ailes ne font pas intégré au vaisseau, style F-14 »*.

## Le principe mécanique à transposer

Sur un appareil à géométrie variable réel :

1. Une **emplanture fixe** large et en flèche (le *glove*) prolonge le fuselage vers l'extérieur et
   vers l'avant. Elle **fait partie de la coque**, elle ne bouge jamais.
2. Le **pivot est enfoui dedans**, pas exposé. On ne voit ni axe, ni bras.
3. Le **panneau mobile** sort du bord de fuite de cette emplanture. Sa racine reste **toujours
   couverte** par elle, quelle que soit la flèche.
4. **En flèche maximale**, le panneau vient se ranger **contre** l'emplanture, presque au contact :
   l'appareil redevient une flèche compacte, sans trou.

## Travail demandé

1. **Créer l'emplanture fixe**, gauche et droite, **dans le maillage principal** (pas une pièce
   mobile). Large, en flèche prononcée, elle relie le flanc de nacelle au bord d'attaque de l'aile
   et se fond dans la coque sans rupture.
2. **Enfouir le pivot** dedans. Supprimer le bras de liaison visible et toute fente à la racine.
3. **Recaler le panneau mobile** : sa racine doit rester couverte par l'emplanture sur toute la
   plage de flèche. Vérifier aux **deux extrêmes** (déployé et flèche maximale), pas seulement au
   repos — c'est le piège habituel de la bbox.
4. **En flèche maximale**, le panneau doit venir **au contact ou presque** de l'emplanture. Donne le
   jeu résiduel mesuré.

## Ce qui ne doit PAS régresser

- **Les échancrures fuselage/nacelle** de BRIEF-0035, avant et arrière. Elles sont acquises.
  L'aplat noir doit continuer de montrer un contour **non convexe** — remets l'image dans le rapport.
- Les 6 pièces mobiles, leur imbrication (`Flap_*` enfants de `Wing_*`), les 10 points d'attache.
- Le **plafond de flèche remesuré à chaque build**, avec échec du build en dessous de la cible.
  `ShipFlight` applique **26°** : si l'emplanture réduit la plage sous cette valeur, **dis-le
  clairement**, c'est le code qui s'adaptera.
- Dimensions X/Z 1,75 × 2,46 m à ±3 % **ailes déployées**, hauteur 0,62-0,72 m, ≤ 60 000 triangles.
- Palette, UV, tangentes, déterminisme (`./scripts/build-hull.sh --check specter_9`).
- Détails en **fraction** de la géométrie porteuse (`.claude/resources/pratique-detail-en-fraction-de-corde.md`).
  Le plan bouge une quatrième fois.

## Le point de lisibilité, à traiter cette fois

BRIEF-0035 signalait qu'à 48 px les ailes perdent en cohésion (fente de 1,6 px) et proposait trois
arbitrages, dont un feu cyan d'emplanture. **L'emplanture fixe devrait résoudre le problème à la
source** — la lame n'est plus isolée, elle prolonge une masse solidaire de la coque. Vérifie-le sur
la vue « game » et dis si le feu d'emplanture reste utile ou devient superflu.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_specter_9.py` | script retravaillé |
| `assets/imported/models/ships/specter_9.glb` | coque + 6 pièces mobiles (LFS) |
| `docs/forge/output/BRIEF-0036-report.md` | mesures, aplat noir, **rendu aux deux extrêmes de flèche**, jeu résiduel, verdict de lisibilité |

## Critères d'acceptation

- [ ] **Aucun bras de pivot ni fente visible à la racine d'aile**, sur toute la plage de flèche
- [ ] La racine du panneau mobile est **couverte par l'emplanture** au déployé ET au replié
- [ ] En flèche maximale, le panneau se range **contre** l'emplanture (jeu résiduel donné)
- [ ] L'aplat noir montre toujours les échancrures **fuselage/nacelle** (contour non convexe)
- [ ] Plafond de flèche mesuré et remesuré à chaque build ; si < 26°, le dire
- [ ] Bbox, budget, matériaux, UV, points d'attache, déterminisme : conformes
- [ ] **Rendu aux deux extrêmes** dans le rapport — c'est une pièce mobile, une pose fixe ne prouve rien

## Hors périmètre

Ne pas toucher au code Godot ni à `aegis_kit.py`. Pas de texture, pas de `.blend`. Ne pas revenir sur
la séparation fuselage/nacelles.
