# BRIEF-0096 — le kit de la Citadelle de Défense

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-04

## Objectif

Produire **`citadel_kit.glb`** : les sept pièces du verrou de mi-parcours du Long Cortège, que le
moteur assemble à la station `s = 240` du tronçon 3. C'est le **LOT 2** du plan
[`2026-09-03-citadelle-de-defense-midpoint.md`](../../plans/2026-09-03-citadelle-de-defense-midpoint.md) :
**la silhouette**.

## Contexte

Le verrou existe, il se joue, il a été **joué à la main le 2026-09-04** — en **boîtes grises**.
Toute la boucle est acquise : le survol freine et s'arrête, deux relais tombent dans n'importe
quel ordre, un noyau protégé devient touchable, un mur solide se retire, la route se rouvre. Et
la règle « gauche + droite → centre » s'est lue **sans un mot de HUD**, en boîtes.

Ce qui manque est la **forme**. Ce brief la demande, et rien d'autre.

⚠️ **POURQUOI UN KIT ET NON LA COQUE, ET C'EST LA QUATRIÈME FOIS QUE CETTE RAISON SE VÉRIFIE.**
Les hangars (`BRIEF-0091`), les affûts (`BRIEF-0093`) puis les nœuds d'épine (`BRIEF-0094`) ont
tous quitté `build_long_cortege.py` pour la même raison mécanique : **une pièce cuite dans le
tronçon ne meurt pas sans emporter ses voisines**, les cinq tronçons partageant un maillage et un
jeu de matériaux. Ici deux relais et un noyau sont **destructibles**, et la porte **s'ouvre** au
LOT 4. Ils ne peuvent pas être dans la coque.

⚠️ **ET LE PLAFOND DE CONSTRUCTION LE CONFIRME PAR UN CHIFFRE.** `BUILD_CEILING_Y = -3,20` borne
la coque, et `_assert_build_ceiling` a déjà **refusé la passerelle à −3,15**. Les cotes du verrou,
tranchées au LOT 0, montent à **−3,00** (décor) et **−2,40** (destructible) : ce sont les deux
plafonds d'`ADR-0041`, qui s'appliquent aux pièces de kit et non au maillage de coque. Le kit rend
donc les 20 cm que la coque interdirait.

## Contraintes

**IP.** Aucun nom, silhouette ou élément identifiable de Macross, Robotech ou d'une autre licence
(spec §0.2). L'exception du Specter-9 (`ADR-0014`) **ne s'étend pas ici**.

**Palette.** Faction **Unisson** (`ak.FACTION_NULL_CHOIR`). Les sept slots de `ak.MATERIAL_ORDER`
et **eux seuls** : ne pas déclarer de huitième matériau. Répartition demandée, dans l'esprit du
80/15/5 du niveau :

| Slot | Emploi ici |
|---|---|
| `AA_Hull` | la masse — porte, bastions, couronnes. **Le gros de l'aire** |
| `AA_Greeble` | les creux, la denture, la machinerie, les conduits |
| `AA_Trim` | **au plus 3 % de l'aire** — arêtes de lecture seulement |
| `AA_Emissive_Engine` | **relais et noyau UNIQUEMENT.** Voir la règle dure ci-dessous |
| `AA_Glass` | le panneau de bouclier, et lui seul |

⚠️ **RÈGLE DURE, ET C'EST CELLE DU NŒUD D'ÉPINE : AUCUN ÉMISSIF HORS DES PIÈCES QUI MEURENT.**
Le moteur détruit `citadel_relay` et `citadel_core` **séparément**. S'il y avait de l'émissif sur
la porte, les bastions ou les couronnes, la mort d'un relais ne se **verrait pas** — et c'est
exactement le défaut que `BRIEF-0094` a corrigé sur les cinq bulbes de l'épine.

**Techniques.** Godot 4.7. Script `tools/blender/build_citadel_kit.py`, lancé par
`./scripts/build-hull.sh citadel_kit`. Le script **EST** la source (`ADR-0008`) : aucun `.blend`
versionné, aucun aléa, et `./scripts/build-hull.sh --check citadel_kit` doit dire
**« déterminisme OK »**. Prendre `build_spine_kit.py` pour modèle — c'est le plus récent et le
plus proche.

**Budget : 3 000 triangles pour le kit entier.** Mesuré sur les trois kits existants —
`turret_kit` 2 240 tris (instancié **38 fois**), `bay_kit` 1 140 (**7 fois**), `spine_kit` 280
(**5 fois**). La citadelle est instanciée **une seule fois** par partie : elle peut donc être la
pièce la plus riche du vaisseau. La coque est à 47 254 tris sur 90 000, et le verrou coûte
aujourd'hui **≈ 0,2 ms** par image en boîtes sur la Quadro T1000 — il y a de la marge, et ce
budget la borne quand même.

## Les cotes — RELEVÉES, jamais à réinventer

Toutes en repère de coque (Y = hauteur, `s` = station depuis la proue, `x` = latéral).
Elles viennent du profil de `build_long_cortege.py` et du LOT 0 du plan.

| Plan | Y |
|---|---|
| plafond du GAMEPLAY (`ADR-0041`) — **ce qui se détruit** | **−2,40** |
| plafond du DÉCOR INERTE (`ADR-0041`) | **−3,00** |
| pont du bastion (assise des tourelles de garde) | −3,60 |
| rebord du canal de l'artère | −4,02 |
| pont intérieur (`x` 2,20 à 6,80) | −4,30 |
| fond du canal de l'artère (`x` ≤ 0,88) | −4,58 |
| pont médian (`x` 7,35 à 10,30) | −4,94 à −4,99 |
| fond de la **tranchée de bastion** (creusée par le concepteur, hors de ce brief) | **−6,50** |
| assise de la porte, enterrée | **−6,60** |

⚠️ **L'ASSISE DE LA PORTE PLONGE DANS LA COQUE, ELLE NE SE POSE PAS DESSUS.** Le bordé n'est pas
plat : quatre plans différents sous une seule pièce de 34 m, plus la tranchée. Une porte assise
sur la cote la plus haute **flotterait** partout ailleurs — au-dessus du vide, en silence, et
personne ne le verrait avant une capture. C'est le défaut que la contremarche de chine a déjà fait
payer aux batteries légères.

## La table du kit — les noms sont FIGÉS

Le moteur va chercher chaque pièce **par son nom exact** (`CortegeCitadel`). Un renommage casse le
niveau **en silence** : rien n'est trouvé, rien n'est dit.

| Nœud | Ce que c'est | Origine | Emprise demandée |
|---|---|---|---|
| `citadel_gate` | **la porte** : la poutre transversale qui ferme la route | centre, à son assise | `x` ±17,20 · `s` ±0,60 · Y 0 → **+3,60** |
| `citadel_pylon` | **le porteur d'extrémité** — voir « le porte-à-faux » | pied, côté tribord | `x` 15,60 à 17,20 · `s` ±0,90 · Y 0 → +3,60 |
| `citadel_bastion` | **la masse**, sur le pont médian | pied, côté tribord | `x` 6,90 à 11,40 · `s` −0,40 à +6,00 · Y 0 → **+2,90** |
| `citadel_crown` | **la couronne** qui fait la silhouette | pied, côté tribord | `x` 7,40 à 10,00 · `s` +1,60 à +5,40 · Y 0 → +0,60 |
| `citadel_relay` | **le relais**, destructible | pied, côté tribord | `x` ±0,80 autour de 6,20 · Y 0 → **+1,90** |
| `citadel_conduit` | **le conduit** relais → noyau | pied, côté tribord | de `x` 5,40 à `x` 1,20 · Y 0 → +0,35 |
| `citadel_core` | **le noyau**, destructible, le point le plus haut | pied, sur l'axe | rayon ≤ 1,30 · Y 0 → **+2,18** |
| `citadel_shield` | **le panneau de bouclier** | centre du panneau | `x` ±1,80 · `s` ±0,12 · Y −1,50 → +1,50 |

⚠️ **UNE SEULE PIÈCE PAR CÔTÉ, LE MOTEUR MIROITE.** `citadel_pylon`, `citadel_bastion`,
`citadel_crown`, `citadel_relay` et `citadel_conduit` sont modelés **tribord** ; le moteur les
retourne par un yaw de π, comme `spine_brace`. Ne pas livrer de version bâbord.

⚠️ **CHAQUE ORIGINE EST À SON POINT D'ASSEMBLAGE, ET Y = 0 EST SON ASSISE** (sauf le bouclier,
centré, qui est un panneau). C'est ce qui permet au moteur de poser une pièce à la cote de son
plan sans arithmétique — et donc de ne pas pouvoir la désynchroniser.

## Les quatre silhouettes — C'EST LE CRITÈRE D'ACCEPTATION, PAS UNE INTENTION

> « En noir et blanc, émissifs coupés, on identifie **bastion ≠ relais ≠ noyau ≠ passage** sans
> hésitation. » — consigne 19 du redesign, et test d'acceptation du plan.

Trois familles occupent déjà l'espace des formes sur cette coque, et une quatrième ne peut pas se
poser sur leurs axes sans tomber du côté de l'une d'elles :

| Existant | Signature |
|---|---|
| hangar | négatif, horizontal, **rectangulaire** — un cadre vide |
| affût | positif, horizontal, **trapu** — un tambour et deux tubes |
| nœud d'épine | positif, **vertical, effilé**, avec des **diagonales** |

Les quatre pièces du verrou prennent donc quatre axes neufs, et chacune doit se lire **par sa
géométrie seule** :

1. **La porte — la LONGUEUR.** Rien d'autre sur ce vaisseau ne traverse le cadre. Une poutre de
   34 m, mince, qui coupe l'écran d'un bord à l'autre : c'est la seule chose du niveau dont on ne
   voit pas les deux bouts en même temps. ⚠️ Elle doit porter une **denture** en son centre — deux
   séries de dents qui s'engrènent sur `x` ±2,40 — parce que c'est **par là qu'elle s'ouvrira**
   (LOT 4) et qu'une porte qui ne montre pas sa jointure ne se lit pas comme une porte.
2. **Le bastion — la MASSE ÉTAGÉE.** Le seul volume à deux niveaux du vaisseau : le corps à
   +2,90, la couronne à +3,50 depuis la même assise. Large, chanfreiné, sans rien de vertical ni
   d'oblique. ⚠️ **Il est plus large que haut**, et c'est ce qui l'empêche de se lire comme un
   affût géant.
3. **Le relais — le BRANCHEMENT.** Court, épais, avec un **collier** à mi-hauteur et un
   **conduit** qui en sort au ras du pont et court **vers le centre**. Le conduit est la pièce la
   plus importante du brief : c'est lui qui dit « ceci alimente cela » **en géométrie**, donc sans
   émissif, donc au test noir et blanc. ⚠️ Ni tube long, ni diagonale : le nœud d'épine les a.
4. **Le noyau — la RÉVOLUTION.** Le seul volume à symétrie de rotation de la citadelle, sur
   l'axe, et **le point le plus haut du verrou** (+2,18 depuis le fond du canal, soit 60 cm
   au-dessus des couronnes). Tout le reste du verrou est orthogonal : un tambour facetté y est
   immédiatement autre chose. ⚠️ Il monte à −2,40 **parce qu'il se tire dessus** — le seul volume
   autorisé à culminer est celui qu'on peut détruire, et c'est ce qui le désigne comme le centre
   sans un mot de HUD.

## ⚠️ Le porte-à-faux — un défaut mesuré à corriger, pas une liberté

Vu en capture le 2026-09-04, et c'est le seul reproche visuel du LOT 1 : **les deux tiers
extérieurs de la poutre surplombent le vide**, étoiles visibles dessous.

Ce n'est pas rattrapable en la raccourcissant. La porte **doit** couvrir tout le plan de vol,
sinon le joueur **contourne le verrou** et la séquence devient facultative. Les chiffres :

- la coque fait **28 m** bord à bord (±14,00) ;
- le cadre de la caméra de jeu, au plan du pont, fait **41,60 m** de large — mesuré au build ;
- la porte fait **34,40 m** (±17,20), soit 82,7 % du cadre visible et **la totalité du plan de
  vol** après projection.

Il reste donc **3,60 m** de porte en l'air de chaque côté. `citadel_pylon` existe pour ça : un
**portique** qui descend du bout de la poutre et vient s'appuyer sur la lisse d'épaule
(`x` ≈ 13,88, Y ≈ −7,65). ⚠️ **Un mur invisible est la même injustice qu'une tourelle qu'on croit
pouvoir raser et qui traverse** — le porteur doit rendre le surplomb *voulu*.

## Texture (`ADR-0028`)

**Une seule demande, et elle est déjà livrée.**

- **`docs/forge/textures/TEX-0015-citadelle-bouclier-energie.json`** — le panneau de bouclier, et
  la peau du noyau à une échelle UV plus serrée. **Livrée et acceptée** le 2026-09-04 (après
  rattrapage de tuilage), déposée en `assets/source/textures/cortege/citadel_shield_1024.png`.
  ⚠️ **Elle n'est PAS câblée par ce brief** : le matériau `AA_Shield_Field` et sa mise en œuvre
  appartiennent au **LOT 3**. Ici, le panneau porte `AA_Glass`.
- **`TEX-0016`** (signalétique ambre) est **refusée et à régénérer** : ne pas compter dessus, et
  ne pas poser d'ambre dans ce kit.

**Aucune autre demande n'est nécessaire, et voici pourquoi** : le blindage, les panneaux greffés
et la machinerie de la citadelle sont servis par `TEX-0010`, `TEX-0011` et `TEX-0012`, **déjà
livrées et intégrées** sur la coque. Et la consigne 19 exige que la citadelle soit identifiable
**par sa géométrie même sans émissif** : si elle avait besoin d'une carte pour se distinguer du
bordé, c'est la silhouette de ce brief qui aurait échoué.

**Dépliage attendu** : `ak.box_project_uv()`, **0,200 tuile/m** — la densité du bordé du Cortège,
pour qu'un raccord verrou/coque ne montre pas deux échelles de détail. ⚠️ **`TEXCOORD_0` doit être
COMPTÉ dans le `.glb` livré, jamais supposé** : trois coques du dépôt sont sorties sans UV, et le
défaut est totalement silencieux — ni erreur d'import, ni test rouge.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_citadel_kit.py` | le script, qui EST la source (`ADR-0008`) |
| `assets/imported/models/backgrounds/citadel_kit.glb` | les sept pièces, aux noms figés |
| `docs/forge/output/BRIEF-0096-report.md` | le rapport : cotes MESURÉES pièce par pièce, triangles, densité de texels, sha256, et la table des emprises pour le moteur |
| `docs/forge/output/BRIEF-0096-planche-citadelle.png` | la planche de recette — voir les critères |

## Provenance

```
citadel_kit,assets/imported/models/backgrounds/citadel_kit.glb,glb_mesh,Blender 4.5 (script),,asset-forge (Claude),proprietary-internal,2026-09-04,docs/forge/briefs/BRIEF-0096-citadelle-kit.md,,"Kit de la Citadelle de Defense (niveau 2, verrou de mi-parcours) : porte, portique, bastion, couronne, relais, conduit, noyau, panneau de bouclier. Assemble par CortegeCitadel a la station s = 240 du troncon 3. LOT 2 du plan docs/plans/2026-09-03-citadelle-de-defense-midpoint.md."
```

## Critères d'acceptation

- [ ] **Les huit nœuds portent EXACTEMENT les noms de la table.** Le moteur les résout par nom ;
      une lettre de travers ne monte rien et ne dit rien
- [ ] **Le test noir et blanc, émissifs coupés** : bastion ≠ relais ≠ noyau ≠ passage, sans
      hésitation. **C'est le critère qui décide**, et la planche doit le montrer
- [ ] **Aucun émissif hors de `citadel_relay` et `citadel_core`** — vérifié par matériau, pas à
      l'œil : le moteur les détruit séparément
- [ ] **Aucune pièce ne dépasse sa cote de plafond** : décor inerte ≤ −3,00 une fois posé,
      destructible ≤ −2,40. À vérifier **en composant l'assise du plan avec la hauteur mesurée**
- [ ] **≤ 3 000 triangles** pour le kit entier, compté dans le `.glb`
- [ ] **`AA_Trim` ≤ 3 % de l'aire**, mesuré
- [ ] **UV présentes et `TEXCOORD_0` COMPTÉ dans le `.glb`** — compté, jamais supposé
      (`ADR-0028`). ⚠️ Trois coques du dépôt sont sorties sans UV et le défaut est **totalement
      silencieux** : ni erreur d'import, ni test rouge
- [ ] **Densité de texels mesurée** et donnée au rapport (cible 0,200 tuile/m)
- [ ] **`./scripts/build-hull.sh --check citadel_kit` dit « déterminisme OK »**
- [ ] **Aucune normale retournée.** Une pièce retournée **disparaît** en jeu (culling arrière) et
      aucune bbox, aucun compte de triangles, aucune mesure d'UV ne le voit. Les trois kits
      existants calculent le bobinage (`_face_facing`) plutôt que de l'écrire
- [ ] Le rapport donne, pour chaque pièce, son **emprise mesurée** (x, y, s) : c'est elle qui dira
      au moteur où poser, et elle a fait que les trois kits précédents se sont assemblés **sans
      une seule itération**

## Hors périmètre

- **La tranchée de bastion dans la coque.** Elle se creuse dans `build_long_cortege.py`, par le
  concepteur, comme les quatre fosses du lot B3 — le pont médian (`x` 7,35 et 10,30) est **déjà**
  fait de deux points du profil, donc elle ne coûte aucun point neuf. Ce brief la prend comme
  acquise : fond à **−6,50**.
- **Le câblage moteur.** `CortegeCitadel` remplace ses boîtes par le kit ; c'est du code.
- **`AA_Shield_Field` et `TEX-0015`.** LOT 3.
- **Les quatre états visuels** (stable, instable, surcharge, éteint) : LOT 3, et ils sont pilotés
  par le moteur sur une seule carte.
- **L'ouverture animée.** LOT 4. Ce brief ne livre que la **denture** qui la rendra possible.
- **Toute lisibilité obtenue par la couleur.** Si la silhouette a besoin d'une teinte pour se
  lire, elle a échoué — c'est la consigne 19, et c'est le critère d'acceptation.
- **Les tourelles de garde.** Elles existent : `turret_kit` en échelle légère, posées par le
  moteur sur le pont du bastion à −3,60. Ne pas en modeler.
