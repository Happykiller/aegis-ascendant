# BRIEF-0083 — L'iris à volets coulissants du Pale Leviathan

- **Statut** : livré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-25
- **Va avec** : `BRIEF-0082` (l'intérieur qu'on découvre une fois l'iris ouvert)

## Objectif

Remplacer la lèvre monobloc `Maw_Lip` de la coque du Pale Leviathan par un **iris de six volets
coulissants** (`Shutter_01..06`), chacun pivoté pour **reculer et glisser latéralement** — ouvrant
au centre un passage franc vers le noyau.

## Contexte

Verdict de l'opérateur au playtest du 2026-08-25 :

> « On n'a pas la sensation que le noyau s'ouvre et qu'on rentre dedans, plus qu'il change. Comme le
> premier boss quand le noyau est exposé, il s'ouvre comme une fleur — ici on imagine un mécanisme
> similaire, le noyau doit s'ouvrir. Faisons en sorte d'avoir une animation dédiée, différente du
> premier. »

Ce qui se passe aujourd'hui, et qui explique le mot « change » : `Shell_Ring` se **translate en Z**
et **grossit de 18 %**. Il n'y a aucun mécanisme, aucune pièce qui s'écarte. La coque porte bien une
`Maw_Lip` (3,05 × 0,51 × 0,97 m) — mais elle est **monobloc** et **n'est référencée nulle part dans
le code du jeu**.

### La contrainte de distinction, et elle est ferme

Le **Choir Harvester** s'ouvre déjà avec `Petal_01..N` sur un iris : des pétales qui **pivotent vers
l'extérieur**, comme une fleur. Les deux boss ne doivent jamais se confondre.

**Décision prise** : l'iris du Leviathan est **mécanique, pas organique**. Les volets ne pivotent pas
vers l'extérieur — ils **reculent dans l'épaisseur de la coque puis coulissent latéralement**, comme
un diaphragme. C'est le geste **opposé** à celui du Harvester.

**Lire d'abord** : `docs/forge/CHARTE_CREATIVE.md`, `ADR-0008`, `ADR-0011`, `ADR-0021`, puis
`tools/blender/build_pale_leviathan.py` et le rapport `docs/forge/output/BRIEF-0081-report.md`.

## Contraintes

- **Six volets** `Shutter_01..06`, répartis à 60°, autour de l'axe du noyau.
- Chacun est une **pièce mobile** (`ak.moving_part`) avec un **pivot posé au bon endroit** : le
  glissement se fait dans le plan de la lèvre, vers l'extérieur radial. Le code anime, pas toi —
  mais un pivot mal placé rend l'animation impossible, et rien ne le signalera.
- ⚠️ **Un repère n'est pas une convention, c'est une mesure** (leçon de `BRIEF-0045`, qui a été
  annulé pour avoir relevé des angles dans le repère du fichier en les présentant comme ceux du jeu).
  `BossController` applique `FACING_PLAYER = (0, π, 0)`. **Rapporte les positions de pivot dans les
  DEUX repères**, en disant lequel est lequel.
- **Ouverture au repos = fermée** : les six volets jointifs doivent redonner la silhouette actuelle
  de `Maw_Lip`. Un joueur qui n'a pas encore brisé l'armure ne doit voir aucune différence.
- **Ouverture à fond** : un passage libre d'au moins **3,0 m de diamètre** au centre — le chasseur
  fait 1,29 m de large et doit y entrer sans que ça ait l'air serré.
- Budget : le delta de triangles sur la coque entière reste **≤ +2 500**.
- ⚠️ **UV sur 100 % des primitives neuves.**
- ⚠️ `ak.inset_panel()` est un no-op sans `normal_update()` préalable. `build_pale_leviathan.py` en
  fait **10 appels, aucun suivi de `normal_update()`** : ses panneaux n'existent pas. **Ne corrige
  pas ça ici** (le kit est gelé, un chantier séparé est convenu) — mais n'en ajoute pas de nouveaux.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_pale_leviathan.py` | modifié : `Maw_Lip` → six `Shutter_NN` |
| `assets/imported/models/bosses/pale_leviathan.glb` | régénéré |
| `docs/forge/output/BRIEF-0083-planche-quatre-vues.png` | planche : fermé, mi-ouvert, ouvert, et une vue de dessus ouvert avec le chasseur à l'échelle |
| `docs/forge/output/BRIEF-0083-report.md` | mesures, pivots dans les deux repères, sha256, delta de triangles |

## Provenance

⚠️ La régénération **change le sha256** de `pale_leviathan.glb` : recale sa ligne dans
`assets/licenses/ASSET_PROVENANCE.csv`. Le CSV est partagé entre sessions — **un seul écrivain**.

## Critères d'acceptation

- [ ] Six `Shutter_01..06`, pièces mobiles, pivots mesurés et rapportés **dans les deux repères**.
- [ ] **Fermés, la silhouette est celle d'aujourd'hui** — comparaison à l'appui sur la planche.
- [ ] Ouverts, passage central libre **≥ 3,0 m** de diamètre — mesuré.
- [ ] Le geste est **un recul + un glissement**, jamais un pivot vers l'extérieur : distinct du
      Choir Harvester au premier coup d'œil.
- [ ] Contrat de noms du reste de la coque **intact** (30 maillages, parentage exact) — la régression
      ici casserait le combat entier.
- [ ] UV sur 100 % des primitives, delta ≤ +2 500 triangles, export déterministe, sha256 rapporté.

## Hors périmètre

- **Le décor intérieur** : c'est `BRIEF-0082`.
- **L'animation** : tu livres des pièces mobiles et des pivots ; le code les anime.
- **Ne modifie pas `aegis_kit.py`**, ni les `Ring_01..05`, ni `Heart`, ni les plaques, ni les épines.
