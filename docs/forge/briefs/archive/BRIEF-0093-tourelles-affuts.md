# BRIEF-0093 — Les tourelles deviennent des affûts

- **Plan** : [`2026-08-29-niveau-2-refonte-geometrie.md`](../../../plans/2026-08-29-niveau-2-refonte-geometrie.md), lot 2
- **Planche de consignes** : `assets/reference/concepts/BRIEF-0091-planche-consignes.png` — **la
  regarder avant de lire la suite**, section 1 « TOURELLE DE DÉFENSE »
- **Modifie** : `assets/imported/models/backgrounds/long_cortege.glb` — retrait des socles cuits
- **Crée** : `assets/imported/models/backgrounds/turret_kit.glb`
- **Précédent direct** : `BRIEF-0091`, dont la méthode (kit assemblé par le moteur) a fonctionné

## Texture

⛔ **Aucune demande de texture.** Le kit réemploie les slots existants de la coque
(`AA_Greeble`, `AA_Hull`, `AA_Trim`, `AA_Emissive_Engine`), aux mêmes matériaux et à la même
densité de dépliage. Les cartes `TEX-0010` à `TEX-0014` sont livrées et intégrées ; aucune
n'est à refaire pour ce lot. Géométrie, UV et slots seulement (`ADR-0028`).

## Pourquoi

> « Les tourelles ressemblent à des jetons circulaires. On distingue un anneau et une boule
> lumineuse, mais pratiquement pas de canon, pas de mécanisme de rotation, pas de blindage, pas
> de connexion physique à la coque. » — l'opérateur

## ⚠️ La règle de production — elle prime sur tout le reste

> **La structure doit être identifiable par sa seule SILHOUETTE, avec au plus 6–8 primitives
> principales. Les émissifs ne servent qu'à renforcer une fonction déjà lisible en géométrie.**

Test d'acceptation : **en noir et blanc, tous émissifs coupés, on distingue immédiatement une
tourelle d'un hangar.** `BRIEF-0091` l'a fait passer côté hangar — un cadre creux contre un
disque plein. Ce brief doit le faire passer côté tourelle : **un canon, pas un jeton.**

## La composition — cinq volumes, dans cet ordre

```
[socle large ancré] → [couronne de rotation] → [bloc blindé] ⇒ ══ deux canons ══
```

| # | Pièce | Rôle |
|---|---|---|
| 1 | `turret_pad` | socle ancré à la coque, très aplati, légèrement enfoncé |
| 2 | `turret_ring` | couronne de rotation — **c'est elle qui tourne**, pas la tourelle entière |
| 3 | `turret_body` | bloc canon blindé, **rectangulaire trapu — surtout pas une sphère** |
| 4 | `turret_barrel` | **un** tube ; le moteur en pose deux, parallèles |
| 5 | `turret_service_box` | coffret technique |
| 6 | `turret_pipe` | conduites |

## Les cotes

| | Valeur | Source |
|---|---|---|
| Diamètre du socle | **3,40 m** | planche 3,0–4,0 ; ratio 1,5–2 × le joueur (1,76 m) |
| Hauteur totale | **1,70 m** | planche 1,5–2,0 |
| Longueur de canon | **2,90 m** | planche 2,5–3,5 |
| Largeur des deux canons | **1,20 m** | planche 1,0–1,4 |
| Diamètre de la couronne | 60–70 % du socle → **2,25 m** | planche |
| Hauteur de la couronne | **0,35 m** | planche |
| Œil énergétique | **≤ 25 %** de la tourelle | planche — règle dure |

⚠️ **LES CANONS SONT EXAGÉRÉS DE 30 À 50 %, ET C'EST DÉLIBÉRÉ.** Un canon physiquement juste
mais fin disparaît après le post-traitement : à 23 px/m de détail utile, un tube de 12 cm fait
trois pixels. Ce n'est pas une erreur d'échelle, c'est une règle de lisibilité. Les tubes doivent
**dépasser largement du socle** — longueur visible 1,5 à 2 fois son rayon.

## ⚠️ Où dépenser le budget, et où ne pas le dépenser

Le budget est **large** : `ADR-0011` accorde 120 000 triangles à la classe « structure », la
coque en consomme 40 446, et les sept hangars 2 772. **Le kit de tourelle dispose de 55 000
triangles** — soit ~3 200 par tourelle assemblée, dix fois ce qu'a coûté un hangar.

Mais un budget large ne veut pas dire du détail fin, et c'est le piège de ce lot :

| ✅ Dépenser ici — ça se voit | ⛔ Pas ici — ça disparaît |
|---|---|
| **Chanfreins sur les grandes arêtes** : ils accrochent la lumière clé à n'importe quelle résolution | Rivets, vis, petits reliefs sous 9 cm |
| **Profondeur réelle** : couronne enfoncée dans le socle, canons logés dans un masque | Grilles fines, textures géométriques |
| **Silhouette** : ce qui dépasse, ce qui creuse | Détail intérieur qu'on ne voit jamais du dessus |
| **Révolutions à 16–24 segments** sur le socle et la couronne | 64 segments : le contour est identique à 23 px/m |
| **Variété entre les dix-sept exemplaires** | Uniformité soignée |

## ⚠️ La variété est un livrable, pas un bonus

Dix-sept tourelles identiques se liront comme dix-sept fois la même. Le kit doit permettre au
moteur d'en varier au moins **trois familles** sans reforge, par assemblage seul :

- **socle** — présence ou non d'une jupe d'ancrage supplémentaire ;
- **appareillage** — 0, 1 ou 2 coffrets, 0 ou 1 groupe de conduites, à des angles différents ;
- **canons** — longueur au choix parmi deux, écartement variable.

Chaque pièce est donc un **nœud racine nommé**, modélisée dans son repère, **origine au point
d'assemblage**, comme `bay_kit.glb`. Rends la table des emprises mesurées : c'est elle qui dit au
moteur où poser chaque pièce, et c'est ce qui a permis d'assembler le hangar sans une itération.

⚠️ **`turret_ring` et tout ce qui est monté dessus doivent tourner autour de l'axe Y**, en un
bloc. Le moteur pivote la couronne à 42 °/s ; si l'origine de la couronne n'est pas sur son axe
de rotation, la tourelle balaiera en décrivant un cercle au lieu de pivoter sur place.

## Le retrait des socles cuits

`build_turret_pad()` cuit aujourd'hui dix-sept socles dans la coque. Le kit les remplace : **les
retirer**, comme `BRIEF-0091` a retiré les coamings.

⚠️ **Les marqueurs `Turret_NN` restent à leurs noms et à leurs positions** — sauf les deux que
`BRIEF-0092` déplace, s'il a déjà été livré. Le moteur monte les pièces dessus par leur nom
exact ; un renommage casse le niveau **en silence**.

⚠️ Et le **Y du marqueur** doit devenir le point d'assise du socle sur la peau, comme le Y des
`Bay_NN` est devenu la bouche.

## La palette — 80 / 15 / 5

| Part | Rôle |
|---|---|
| **80 %** | gris / anthracite — socle, couronne, bloc, canons |
| **15 %** | grège moyen — coffrets, conduites, radiateur |
| **5 %** | magenta — **l'œil, et rien d'autre** |

⚠️ L'aire par matériau se **mesure** et se rend en pourcentage. `BRIEF-0091` a rendu 84 / 10 / 6
avec un écart assumé et expliqué sur l'appareillage — la palette de l'Unisson n'a pas de grège
moyen entre `AA_Hull` et `AA_Trim`. Si le même écart se reproduit ici, **le dire plutôt que de
forcer `AA_Trim` à 15 %** : `BRIEF-0089` a mesuré qu'un matériau clair sur une arête continue
occupe plus de pixels qu'une pièce entière.

# Vérification

- `./scripts/build-hull.sh --check long_cortege` déterministe, `./scripts/check.sh` vert.
- UV comptées dans le binaire, aires par matériau en pourcentage, table des emprises.
- ⚠️ **Une planche regardée** (`ADR-0006`), avec le même cadrage non négociable que
  `BRIEF-0091` : **une tourelle et un hangar sur la MÊME vignette, en noir et blanc, émissifs
  coupés.** C'est le test d'acceptation. Ajouter une vue de trois-quarts d'une tourelle seule,
  et une vue montrant **trois exemplaires différents côte à côte** — c'est le seul moyen de
  juger la variété.
