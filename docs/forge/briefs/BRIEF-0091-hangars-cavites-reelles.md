# BRIEF-0091 — Les ponts d'envol deviennent de vraies cavités

> **Deux livrables indissociables**, et c'est pourquoi ils sont dans un seul brief : la coque
> doit **perdre** ses coamings de baie et **gagner** ses ouvertures, et le kit doit s'y loger au
> millimètre. Les séparer garantirait qu'ils ne s'emboîtent pas.

- **Plan** : [`2026-08-29-niveau-2-refonte-geometrie.md`](../../plans/2026-08-29-niveau-2-refonte-geometrie.md), lot 1
- **Planche de consignes** : `assets/reference/concepts/BRIEF-0091-planche-consignes.png` — **la
  regarder avant de lire la suite**, section 2 « PONT D'ENVOL (HANGAR) »
- **Modifie** : `assets/imported/models/backgrounds/long_cortege.glb` (livré par `BRIEF-0089`)
- **Crée** : `assets/imported/models/backgrounds/bay_kit.glb`

## Pourquoi — et ce n'est pas une question de qualité

> « Les ponts d'envol ressemblent à de gros boutons hexagonaux magenta. On ne comprend pas qu'un
> appareil peut physiquement sortir de là. » — l'opérateur, en jouant

Le défaut n'est pas dans la texture, il est dans la **géométrie qui ne porte pas la fonction**.
Un pont d'envol produit des ennemis en continu tant qu'on ne l'abat pas ; c'est la mécanique la
plus coûteuse du niveau à faire taire. Si le joueur ne comprend pas que la structure **produit**,
le choix de la détruire ne se relie à rien.

## ⚠️ La règle de production — elle prime sur tout le reste

> **La structure doit être identifiable par sa seule SILHOUETTE, avec au plus 6–8 primitives
> principales. Les émissifs ne servent qu'à renforcer une fonction déjà lisible en géométrie.**

Test d'acceptation, littéral : **en noir et blanc, tous émissifs coupés, on doit distinguer
immédiatement un hangar d'une tourelle.** Aujourd'hui ce test échoue.

⛔ **Ne pas « améliorer la qualité 3D ».** À 23 px/m de détail utile après le post-traitement
rétro, tout détail sous ~9 cm disparaît. Du détail ajouté est du budget dépensé pour du bruit.

---

# Partie A — La coque perd ses coamings et gagne ses ouvertures

## ⚠️ Le changement de méthode, et sa raison chiffrée

`build_bay()` écrit aujourd'hui, et la raison était bonne :

> « Une VRAIE cavité demanderait de trouer la peau (booléen, donc non déterministe, et une peau
> non manifold). Ici la baie est un coaming POSÉ sur le bordé. […] un puits de 0,78 m borde de
> parois sombres se lit exactement comme une baie creusée. »

Ce compromis tenait tant qu'on visait 0,78 m. **La planche demande 1,5 à 2,5 m**, et il n'y a que
**1,1 m** entre la peau (−4,30) et le plafond du plan de jeu (−3,20) :

```
  −3,20  ┄┄┄ plafond du plan de jeu — RIEN ne monte au-dessus
  −4,30  ▀▀▀ la peau du bordé, à l'emprise des baies
                     ↕  1,8 m de cavité — n'existe qu'ICI, sous la peau
  −6,10  ▄▄▄ fond du puits
  −12,60     le bas de la coque : il y a la place
```

**La profondeur demandée n'existe qu'en descendant SOUS la peau.**

## Ce qui est demandé

1. **Retirer** les sept coamings et sols émissifs produits par `build_bay()`.
2. **Ouvrir** la peau à leur emprise : une ouverture par marqueur `Bay_NN`, **6,00 m de large ×
   8,50 m de long**, l'axe long dans le sens du survol (Z).
3. ⚠️ **Générer la peau AVEC ses ouvertures — pas de booléen.** On n'émet simplement pas les
   faces de l'emprise et on raccorde proprement le bord. Le déterminisme est une exigence dure
   (`build-hull.sh --check`, 0 octet divergent), et un booléen ne le tient pas.
4. Les marqueurs `Bay_NN` restent **à leur nom et à leur position**, mais leur `Y` passe **au
   niveau de la peau** (la bouche), pas au fond : c'est là que le jeu pose ses portes.

## ⚠️ Ce qu'il ne faut PAS toucher

- Les **socles de tourelle** (`build_turret_pad`) : ils partiront au `BRIEF-0092`, avec le kit
  qui les remplace. Les retirer maintenant laisserait dix-sept tourelles flottant sur du plat.
- Les **bulbes d'épine** (`build_spine_bulb`) : ils partiront au `BRIEF-0093`.
- **Les 30 marqueurs**, leurs noms et leurs X/Z. Le moteur monte les pièces dessus par leur nom
  exact ; un renommage casse le niveau **en silence**.
- Le **plafond −3,200** et les jonctions à 0,00000 m.
- Le dépliage à **0,200 tuile/m** (`100 × densité ∈ ℤ`).

---

# Partie B — Le kit de hangar, 7 pièces

Livré dans `bay_kit.glb`, **une pièce = un nœud racine nommé**, modélisée dans son propre repère,
**origine au point d'assemblage**. Le moteur les instancie et les compose : c'est lui qui fait
sept hangars différents à partir d'un seul kit, par rotation, largeur et présence des blocs.

| Nœud | Ce que c'est | Repère |
|---|---|---|
| `bay_frame_left` | montant gauche du coaming | origine au bord gauche de l'ouverture, à hauteur de peau |
| `bay_frame_right` | montant droit — **miroir**, pas une copie | idem, bord droit |
| `bay_frame_top` | traverse avant (côté proue) | origine au milieu du bord avant |
| `bay_inner_wall` | paroi interne du puits, en anneau fermé | origine au centre de l'ouverture, à hauteur de peau |
| `bay_floor` | le fond | origine au centre, à −1,80 m sous la peau |
| `bay_launch_rail` | **un** rail ; le moteur en pose deux | origine au fond, à l'arrière du puits |
| `bay_service_block` | bloc de servitude — optionnel, pour varier | origine à sa base |

## Les cotes

| | Valeur |
|---|---|
| Ouverture | **6,00 × 8,50 m** |
| Profondeur (peau → fond) | **1,80 m** |
| Hauteur de coaming au-dessus de la peau | **0,60 m** |
| Retrait des parois internes | l'anneau interne rentre de **0,7 m** par rapport à l'ouverture |
| Rail | **0,35 m** de large, courant du fond vers la sortie |

## ⚠️ Les quatre règles visuelles de la planche, et ce qu'elles interdisent

1. **Toujours un trou, jamais un bouton.** La lecture immédiate doit être « il y a un creux ici ».
2. **L'intérieur est PLUS SOMBRE que l'extérieur.** C'est ce qui fait la profondeur, bien plus
   que la géométrie : un intérieur clair remonte à la surface et le trou redevient un bouton.
3. **Bandes lumineuses seulement EN PARTIE.** L'émissif vit sur des bandes internes — au pied des
   parois, le long des rails — **jamais sur toute la surface du fond**. C'est déjà la consigne de
   `TEX-0013` (« au moins la moitié de l'aire sombre »), et c'est elle qui a été trahie par un
   fond magenta plein.
4. **L'appareil est visible avant le décollage.** Le kit doit lui laisser la place : le puits est
   creusé pour qu'un chasseur d'environ 1,8 × 2,5 m y tienne **posé sur les rails**, visible du
   dessus.

## ⚠️ Le piège de la cavité ouverte

La coque est une **coque creuse**. Une fois la peau trouée, on voit **à travers** — l'intérieur du
vaisseau, puis sa face opposée. `bay_inner_wall` et `bay_floor` doivent donc **fermer le puits**
vu de la caméra de jeu (plongée à ~70°, jamais à la verticale). Un puits qui laisse voir le vide
intérieur est pire que pas de puits : il se lit comme un trou dans le modèle.

## La palette

| Part visée sur le kit | Rôle |
|---|---|
| **80 %** | gris / anthracite — le coaming, les parois, le fond |
| **15 %** | grège moyen — les rails, les blocs de servitude |
| **5 %** | magenta / violet — **les bandes internes, et rien d'autre** |

⚠️ **L'aire par matériau se MESURE et se rend au rapport**, comme tu l'as fait pour `AA_Trim`
(2,29 %). Ce n'est pas une intention, c'est un chiffre.

# Vérification

- `./scripts/build-hull.sh --check long_cortege` → *déterminisme OK*, 0 octet divergent.
- `./scripts/check.sh` **ALL GREEN**.
- **UV comptées dans le binaire** : 100 % des primitives avec `TEXCOORD_0`, kit compris.
- **Budget** : la coque est à 39 434 tri sur 90 000. Le kit de hangar dispose de **20 000 tri**
  au plus — sept instances, donc ~2 800 par hangar assemblé. C'est confortable pour huit
  primitives ; si tu en demandes plus, dis pourquoi.
- **Aires par matériau** rendues en pourcentage.
- ⚠️ **Une planche regardée** (`ADR-0006`), avec une exigence de cadrage non négociable : **un
  hangar et une tourelle actuelle sur la MÊME vignette, en noir et blanc, émissifs coupés.**
  C'est le test d'acceptation ; une planche qui ne le montre pas ne prouve rien.
- ⛔ **Aucune texture** (`ADR-0028`) : géométrie, UV et slots de matériau seulement.
