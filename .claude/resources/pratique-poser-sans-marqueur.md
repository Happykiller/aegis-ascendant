# Poser une pièce là où la coque n'a pas prévu de repère

**Origine** : 2026-09-08, les douze conduites de l'artère du niveau 2. Toutes les pièces de coque
du jeu — dix-sept tourelles, sept ponts, cinq nœuds — sont **enfants d'un marqueur** que le `.glb`
livre. L'artère n'en a aucun. Il a fallu poser par **station**, et trois choses ont coûté.

## 1. La convention de station se LIT dans le binaire

`Turret_17` est à la station 478,8 et sa translation vaut `z = −78,8` : un marqueur porte
`−(s − 100 × tronçon)`. La déduire d'un raisonnement aurait posé douze pièces à cent mètres de
leur place, **sans une erreur**.

⚠️ Et le tronçon se lit sur la **hiérarchie** (`Section_03` → index 2), pas sur le `z`.

## 2. ⚠️ Comparer des `z` LOCAUX entre tronçons différents est faux, et ça passe pour un bug de pose

`Turret_07` est à `s = 258` (tronçon 3, `z = −58`). Une conduite à `s = 58` est au tronçon 1, avec
exactement le même `z = −58`. Un test de dégagement écrit sur les `z` a rendu **six assertions
rouges sur des pièces distantes de deux cents mètres** — et la table était juste.

**La station se recompose** (`index × 100 + |z|`), elle ne se lit pas.

## 3. ⚠️ Un nœud de glTF n'a pas de propriété `position`

Lire `SceneState.get_node_property_value(i, "position")` sur une coque importée rend **zéro
marqueur** : un nœud de glTF porte un `transform`. Trois tests de placement sont passés **verts et
vides**, et seul le harnais du dépôt (« aucune assertion exécutée ») l'a dit.

**Instancier et parcourir l'arbre**, plutôt que lire l'état packé — c'est deux lignes de plus et
ça ne ment pas.

## 4. Et la cote qu'on ne peut pas lire, on la DÉCLARE

L'assise des conduites (`y = −4,30`) est la seule cote du lot qui ne vienne pas de l'asset :
l'artère n'a pas de marqueur, donc rien à échantillonner. Deux réflexes :

- **le dire dans le code**, à l'endroit exact de la constante — pas dans un rapport que personne
  ne relira ;
- **la faire garder par ce qui, lui, est lu** : un test compare cette constante au `y` des
  marqueurs voisins, qui sont échantillonnés sur la peau. Si la coque se reforge et que le pont
  bouge, le banc le dit au lieu de laisser douze pièces flotter.

⚠️ La vraie sortie reste un brief de forge pour douze repères `CTRL | Conduite NN`. Tant qu'il
n'existe pas, **la constante est une dette, et elle doit se lire comme telle**.

Cousin direct : [pratique-poser-une-piece-sur-une-coque](pratique-poser-une-piece-sur-une-coque.md),
qui traite de ce qui se passe une fois la pièce posée — projection, chevauchement, occultation.
