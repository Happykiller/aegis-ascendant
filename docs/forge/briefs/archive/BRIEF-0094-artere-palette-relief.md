# BRIEF-0094 — L'artère, la palette, le relief

> **Trois lots dans un seul brief, et c'est délibéré** : ils touchent tous la peau du bordé.
> Trois reforges séparées coûteraient trois fois le même temps de maillage et risqueraient de se
> contredire. Ils sont **classés par priorité** — si tu dois t'arrêter, arrête-toi par la fin.

- **Plan** : [`2026-08-29-niveau-2-refonte-geometrie.md`](../../../plans/2026-08-29-niveau-2-refonte-geometrie.md), lots 3 à 5
- **Planche de consignes** : `assets/reference/concepts/BRIEF-0091-planche-consignes.png` —
  section 3 « EXEMPLE IN-GAME » et section 4 « PALETTE & LISIBILITÉ »
- **Modifie** : `assets/imported/models/backgrounds/long_cortege.glb`
- **Crée** : `assets/imported/models/backgrounds/spine_kit.glb`

## Texture

⛔ **Aucune demande `TEX-NNNN`.** Ce brief redistribue des matériaux existants et remodèle de la
géométrie ; il n'introduit aucune surface qui appellerait une carte neuve. `TEX-0010` à
`TEX-0014` sont livrées et intégrées. ⚠️ **Mais il sert directement `TEX-0013`** : sa consigne
— « au moins la moitié de l'aire sombre, le halo est le travail du moteur » — était respectée
par l'image et **trahie par la géométrie**, qui offrait une bande pleine à peindre. Géométrie,
UV et slots seulement (`ADR-0028`).

## ⚠️ La règle de production — inchangée, et elle prime

> **Identifiable par la seule SILHOUETTE, au plus 6–8 primitives principales. Les émissifs ne
> servent qu'à renforcer une fonction déjà lisible en géométrie.**

Et le test qui tranche : **en noir et blanc, émissifs coupés, les trois structures se
distinguent.** Le hangar creuse, la tourelle dépasse — les deux sont acquis. **Le nœud d'épine
doit maintenant s'y ajouter sans ressembler à ni l'un ni l'autre.**

---

# PRIORITÉ 1 — L'artère devient une tranchée

> « L'artère centrale est beaucoup trop proche d'un laser géant. Elle attire davantage l'œil que
> certaines menaces. » — l'opérateur

## Ce qui est demandé

```
   coque                                   coque
██████████╲                             ╱██████████
           │  ▌   ▌   ▌   ▌  │
           │  ▌   ▌   ▌   ▌  │   ← canal ENFONCÉ, ~2,00 m de large
██████████╱                             ╲██████████
```

- **Un canal creusé dans la peau**, pas une bande posée dessus. ~**2,00 m** de large.
- Un **rebord mécanique sombre** de part et d'autre, qui l'encadre et le fait lire comme une
  tranchée technique.
- **3 ou 4 bandes lumineuses de 10 à 25 cm**, parallèles, dans le fond du canal — jamais sur
  toute sa largeur.
- ⚠️ **Des interruptions.** Une bande continue sur 500 m est une frontière de terrain, pas une
  conduite. Coupe-les par des travées sombres, régulièrement mais sans métronome.
- ⛔ **Plus aucun centre blanc continu.**

## Le nœud d'épine devient une pièce de kit

Il est **destructible** : il doit donc s'éteindre quand il tombe, et une pièce cuite dans le
tronçon ne s'éteint pas sans éteindre les quatre autres. Même raison que pour les tourelles et
les hangars.

- **Retirer** `build_spine_bulb()` de la coque.
- Livrer `spine_kit.glb`. **Une pièce = un nœud racine nommé**, modélisée dans son repère,
  **origine au point d'assemblage**, exactement comme `bay_kit.glb` et `turret_kit.glb` — c'est
  cette table qui a permis d'assembler les deux précédents **sans une seule itération**, et c'est
  pourquoi les noms sont figés ici et non laissés au choix :

| Nœud | Ce que c'est | Repère |
|---|---|---|
| `spine_cradle` | le berceau qui l'ancre au fond du canal, plus large que le cœur | origine au centre, sur le fond du canal |
| `spine_core` | le cœur — la partie qui meurt, et donc la seule qui porte l'émissif | origine à sa base, posée sur le berceau |
| `spine_brace` | une entretoise ; le moteur en pose deux ou quatre, en miroir | origine au pied, côté berceau |

⚠️ **Le moteur éteint et détruit `spine_core` seul** — berceau et entretoises restent en place, un
nœud abattu laissant une carcasse. Aucun émissif hors du cœur, sans quoi la mort du nœud ne se
verra pas.
- **Taille** : 0,7 à 1,0 × la largeur du joueur (1,76 m) → viser **1,50 m**.
- ⚠️ **Il ne doit ressembler ni à une tourelle ni à un hangar en noir et blanc.** C'est la
  troisième silhouette du niveau, et la seule dont la récompense arrive quarante secondes plus
  tard : elle doit se reconnaître au premier coup d'œil.
- Le marqueur `Spine_NN` garde son nom et son X/Z ; son **Y devient le plan d'assise** dans le
  canal, comme les `Turret_NN` l'ont fait.

---

# PRIORITÉ 2 — La palette

> « Les gros rectangles violets posés partout sabotent la hiérarchie. Je réduirais d'environ 60
> à 70 % le nombre de surfaces violettes actuelles. »

| Part visée | Rôle |
|---|---|
| **80 %** | gris / anthracite — la structure |
| **15 %** | grège moyen — l'appareillage |
| **5 %** | magenta / violet — l'émissif **et rien d'autre** |

⚠️ **Une greffe doit se distinguer par sa HAUTEUR, son ORIENTATION et sa SILHOUETTE**, pas par
sa couleur. Aujourd'hui les grandes formes violettes se lisent comme des decals arbitraires : ce
sont des aplats, pas des volumes. Réduire le violet **et** relever ces masses est la même
correction, pas deux.

⚠️ **Ton écart mesuré sur le grège est ACCEPTÉ et documenté** — la palette de l'Unisson n'a rien
entre `AA_Hull` et `AA_Trim`, et tu as eu raison de refuser de forcer `AA_Trim` à 15 % (un
matériau clair sur une arête continue occupe plus de pixels qu'une pièce entière, `BRIEF-0089`).
**Si un grège moyen manque vraiment, propose un huitième slot** plutôt que de tordre les deux
qui existent — le précédent d'`AA_Hull_Ambry` est là.

---

# PRIORITÉ 3 — Le relief, et les zones calmes

> « Il y a actuellement du détail presque partout. Le bordé spécifiait explicitement de grandes
> plages de tôle nue, précisément pour que le vaisseau lise comme un ouvrage gigantesque. »

## La stratification

| Niveau | Usage |
|---|---|
| Z0 | la peau |
| Z + 0,2 | plaques, greffes |
| Z + 0,6 | nervures, coamings, machinerie |
| Z + 1,2 à + 2,0 | tourelles, hangars (le kit s'en charge) |

## Le rythme — et c'est du GAMEPLAY

> **15–20 m calmes → une installation → zone calme → un hangar → calme → un groupe de
> tourelles.** Pas `élément → élément → élément`.

⚠️ Quand un gros équipement entre dans le cadre, le joueur doit le **remarquer**. Sur un fond
chargé en permanence, il ne remarque rien. **Les zones calmes sont un livrable, pas un manque** —
à mesurer et à rendre : quelle est la plus longue plage nue, et quelle part de la longueur est
calme ?

Ajouter quelques **nervures et masses en Z + 0,5 AUTOUR des installations** pour les ancrer.
Rien ailleurs.

---

# Ce que ce brief ne touche pas

- **Les kits de hangar et de tourelle** : acceptés, livrés, câblés. N'y touche pas.
- **Les marqueurs** : noms, X, Z inchangés. Seul le Y des `Spine_NN` bouge.
- **`Turret_02` (s = 76), `Turret_05` (s = 173)**, `_marker_clashes()` et sa réciproque,
  `ACCEPTED_PAD_BAY_PROXIMITY` : arbitrages livrés, ne pas les rejouer.

# Ce qui a été arbitré depuis ton dernier rapport

⚠️ **Le plafond des pièces de gameplay est relevé à −2,40**, et le décor inerte reste à −3,00.
Ta mesure était juste — 1,70 m ne tenait pas sous −3,00 à dix emplacements sur dix-sept — et
c'est la lecture de la règle qui change, pas la règle : elle protège du décor qui masquerait le
combat *sans jamais pouvoir être touché*. Une tourelle se tire dessus, et à −2,40 elle reste
2,40 unités sous le plan de vol. **Le cliquet `CEILING_OVERSHOOT_MAX` peut donc être remplacé
par la vraie borne.** Un test moteur la tient désormais.

# Vérification

- `./scripts/build-hull.sh --check long_cortege` et `--check spine_kit` déterministes,
  `./scripts/check.sh` vert.
- UV comptées dans le binaire, **table des emprises** du kit d'épine.
- **Aires par matériau en pourcentage**, et la **part de longueur calme**.
- ⚠️ **Une planche regardée** (`ADR-0006`) : les **trois** structures dans le même cadre, en
  noir et blanc, émissifs coupés — c'est le test d'acceptation, et il porte maintenant sur trois
  silhouettes et non deux. Plus une vue de l'artère de près, et une vue longue montrant le
  rythme calme / installation / calme.
