# BRIEF-0090 — Ambry : un matériau qui lui soit propre

> **Avenant à [`BRIEF-0089`](BRIEF-0089-long-cortege-coque.md).** La géométrie livrée est bonne et
> ne doit pas bouger. Ce brief ne demande qu'une chose, et elle vient de la forge elle-même :
> le rapport `BRIEF-0089-report.md` signale, en point n° 2 à trancher, qu'Ambry partage les sept
> matériaux du bordé et propose de reforger si on le demande. **On le demande.**

## Pourquoi — ce que ça change pour le jeu

Ambry est la **révélation du niveau 2**. Un avant-poste humain de quatre-vingts personnes, soudé
sur le bordé d'un vaisseau de six kilomètres huit, et le joueur apprend au même instant qu'il a
été **radié** du Registre — pas déclaré perdu. Tout le niveau existe pour cet instant : les cinq
briefings de pause y mènent, la dernière réplique de Lyra le nomme, et le rapport de mission
tombe sept secondes et demie plus tard pour lui laisser la place.

Or, sous la palette de l'Unisson, **`AA_Hull` *est* l'anthracite** : Ambry sort donc de la même
matière que ce qui l'a emporté. Le contraste ne repose que sur `AA_Trim`, soit **2,29 % de
l'aire**. Ce n'est pas assez pour qu'une greffe humaine se lise comme « de chez nous », et surtout
ça interdit de lui demander une texture qui lui soit propre — ce que la suite du plan prévoit.

## Ce qui est demandé

1. **Un huitième slot, `AA_Hull_Ambry`**, employé **uniquement** par la géométrie d'Ambry.
   Teinte : le **gris-ivoire froid des coques Helios Vanguard**, pas l'anthracite. `AA_Trim`,
   `AA_Glass` et l'émissif peuvent rester partagés si c'est plus propre — le dire dans le rapport.
2. Si `aegis_kit` refuse deux factions dans une palette : **déclarer le slot localement** dans
   `build_long_cortege.py`, à la manière dont `build_moon_flyby.py` refait son export sans passer
   par `ak.export_hull()`. ⚠️ **Le dire explicitement au rapport** plutôt que de contourner le kit
   en silence — c'est le genre d'écart qui ne se retrouve plus six mois après.
3. **L'échelle UV d'Ambry reste la sienne** — 0,700 tuiles/m, soit 1,43 m/tuile. C'est elle qui
   justifie le slot séparé : une texture calée sur les 5 m/tuile du bordé y lirait quatre fois
   trop grosse.
4. **Rien d'autre ne change.** Mêmes ~39 434 triangles, mêmes **30 marqueurs aux mêmes positions**
   (`Turret_01..17`, `Bay_01..07`, `Spine_01..05`, `Ambry`), même plafond à **−3,200**, mêmes
   jonctions à 0,00000 m, mêmes 27/27 primitives avec `TEXCOORD_0`. Si un chiffre bouge, dire
   lequel et pourquoi.

## Contraintes reconduites

- ⛔ **Aucune texture** (`ADR-0028`) : géométrie, UV et slots seulement. Les images viennent de
  l'opérateur ; le concepteur écrit les `TEX-NNNN` en parallèle.
- **`100 × densité ∈ ℤ`** — la règle trouvée par la forge au brief précédent, et qui explique
  `HULL_TILES_PER_SECTION = 20`. Pour Ambry, 0,700 donne 70 : entier, donc bon.
- **Déterminisme** : `./scripts/build-hull.sh --check long_cortege` doit dire *déterminisme OK*,
  0 octet divergent. `./scripts/check.sh` **ALL GREEN**.

## ⚠️ Le piège que ce brief hérite du précédent

Le rapport `BRIEF-0089` a relevé, en le mesurant, que **sur 500 m un matériau clair posé sur une
arête continue occupe plus de pixels qu'une pièce entière** — `AA_Trim` faisait moins de 6 % de
l'aire et lisait comme une piste d'aéroport. Ambry fait 60 m sur 6 800. Si son ivoire déborde sur
la coque de l'Unisson, **il volera la lecture à tout le reste du niveau**, et l'on aura payé une
reforge pour rendre le niveau moins lisible.

**À rendre : l'aire du nouveau slot, en pourcentage**, comme le rapport l'a fait pour `AA_Trim`.

## Vérification (ADR-0006)

Une **planche regardée**, et une exigence de cadrage qui n'est pas négociable : **Ambry et un
tronçon de bordé sur la MÊME vignette**. Le contraste est tout l'objet de la demande ; deux
vignettes séparées ne permettent pas d'en juger, et une planche qui ne le montre pas ne prouve
rien.

Mettre à jour `BRIEF-0089-report.md` et la ligne de provenance existante plutôt que d'en créer de
nouvelles : c'est le même asset.
