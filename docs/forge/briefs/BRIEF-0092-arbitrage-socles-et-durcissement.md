# BRIEF-0092 — L'arbitrage des socles, et deux durcissements

> **Avenant à [`BRIEF-0091`](BRIEF-0091-hangars-cavites-reelles.md)**, dont la livraison est
> acceptée : le test noir et blanc passe, le puits est un vrai creux, le chasseur y est posé sur
> les rails. Ce brief ne traite que ce que la forge a eu raison de ne **pas** trancher.

## Texture

⛔ **Aucune demande de texture, et voici pourquoi.** Ce brief ne produit ni surface neuve ni
matériau neuf : il déplace deux marqueurs et durcit deux harnais. Les cartes du niveau 2
(`TEX-0010` à `TEX-0014`) sont livrées, intégrées et inchangées. Géométrie, UV et slots
seulement (`ADR-0028`).

*(Cette section manquait aux briefs 0090 et 0091 — la forge l'a signalé deux fois, elle avait
raison les deux fois.)*

## 1. L'arbitrage — deux marqueurs bougent, en `s` seulement

La forge a mesuré que `Turret_02` a **son centre dans l'ouverture de `Bay_01`**, et que
`Turret_05` mord 0,70 m dans `Bay_03`. Elle a eu raison de ne pas décider : c'est une ligne de
la table `TURRETS`, donc une décision de conception.

| Marqueur | `s` avant | `s` après | Dégagement obtenu | Dégagement requis |
|---|---|---|---|---|
| `Turret_02` | 84 | **76** | 10,0 avec `Bay_01` (s = 86) | 4,25 + 2,30 = **6,55** |
| `Turret_05` | 176 | **173** | 9,0 avec `Bay_03` (s = 182) | 4,25 + 2,55 = **6,80** |

⚠️ **Vérifier que `Turret_02` à s = 76 ne vient pas mordre `Turret_01` (s = 68)** : 8,0 entre
eux, deux socles de 2,30 se touchent à 4,60 — c'est large, mais ça se mesure.

### `Turret_14` reste où il est

Le verdict de la forge est le bon : il effleure le coaming de `Bay_07` sur 0,25 m, et **deux
installations qui se touchent est une lecture crédible**, pas un défaut. Le déclarer comme une
proximité **ACCEPTÉE**, avec la raison écrite sur place — sinon le prochain qui lira la table y
verra un oubli et « corrigera » quelque chose qui va bien.

⚠️ **Le nombre, les noms et l'ordre des 30 marqueurs ne changent pas.** Seuls deux `s` bougent.
Le moteur les résout par nom à chaque image : un déplacement est sûr, c'est un renommage ou une
disparition qui casserait le niveau **en silence**.

## 2. Le garde mutuel `TURRETS` / `BAYS`

Sur le modèle de `JOINT_CLEARANCE`. Deux marqueurs posés à la main à 2 m l'un de l'autre
n'auraient jamais dû passer — et c'est précisément le genre de faute qui ne se voit qu'une fois
la géométrie ouverte, six semaines plus tard.

## 3. ⚠️ « Trianguler tout avant le dépliage » remonte dans `aegis_kit`

**Ce n'est pas une optimisation, c'est une correction.** Un quad gauche fausse `box_project_uv`
**en silence**, et la mesure le prouve : densité minimale à **0,078** pour une borne théorique de
**0,116** — un étirement que la projection en boîte ne *peut pas* produire, donc un défaut de
méthode et non un cas limite.

⚠️ **Tout asset déjà livré par le kit a pu en souffrir sans que rien ne le dise.** À rendre : la
liste des assets existants concernés, mesurée et non supposée. Je déciderai s'il faut les
reforger.

## Ce qui n'est PAS demandé

- Le slot `AA_Hull_Bay` : **pas maintenant**. Il se justifiera le jour où l'intérieur du puits
  recevra sa propre carte ; l'ouvrir avant serait un slot qui ne sert à rien.
- Aucune retouche du kit ni de la cavité : ils sont acceptés tels quels.

## Vérification

- `./scripts/build-hull.sh --check long_cortege` déterministe, `./scripts/check.sh` vert.
- UV comptées dans le binaire, aires par matériau inchangées (les deux socles se déplacent, ils
  ne changent pas de taille).
- ⚠️ **Pas de planche complète.** Une seule **vue de dessus des tronçons 1 et 2** suffit à
  prouver que les deux socles déplacés ne mordent plus. C'est tout ce que ce lot ajoute, et une
  planche de six vignettes pour deux marqueurs serait du temps dépensé pour rien.
