# ADR-0032 — Un module de collision de plan, et le noyau devient un corps

- **Statut** : accepté
- **Date** : 2026-08-27
- **Contexte** : playtests du 2026-08-27 (soir), Chambre du Réacteur
- **Amende** : `ADR-0031` (qui a posé la ligne de tir sans poser de moteur)

## Contexte

Le blindage du boss final a reçu une collision « au fil de l'eau » : d'abord un halo sans corps,
puis `ReactorRings.blocks()`, puis `blocks_body()` pour l'envergure, puis `push_out()` pour
dégager, puis `first_hit_along()` pour la ligne de tir. Cinq fonctions écrites une par une, pour
**une seule forme** — le secteur d'anneau — au fur et à mesure des plaintes.

Trois plaintes du même playtest, qui n'en faisaient qu'une :

- « le vaisseau rentre en partie dans les murs » ;
- « le bord des murs est franchissable, et les tirs aussi peuvent passer » ;
- « je fonce tout droit et à l'apparition de la phase interne mon vaisseau est **bloqué**, il
  avance pas ».

Puis une quatrième, qui a tranché : « le réacteur central ne devrait pas être franchissable, on
doit se doter d'un moteur physique complet et crédible et facilement utilisable ».

## Le défaut

La détection était juste. C'est le **dégagement** qui ne l'était pas : il ne connaissait qu'une
direction, la radiale. Un corps pris dans un mur était donc poussé vers l'intérieur ou vers
l'extérieur — **jamais par le bout de l'arc**, c'est-à-dire par l'ouverture, même quand elle était
à un demi-mètre de côté.

Combiné à un point d'apparition écrit en dur (`Vector2(0, -5)`, une constante posée **avant** que
les murs n'existent, et qui tombait en plein dedans), ça donnait : le chasseur naît dans le
blindage, se fait repousser vers l'intérieur, et se retrouve enfermé dans un couloir de 0,9 unité
dont il ne peut plus sortir. Il fonce tout droit ; il n'avance pas.

Et le noyau, lui, n'était pas un obstacle du tout : la collision ne savait traiter que des murs.

## Décision

**1. Un module dédié, [`PlaneCollider`] + [`PlaneShapes`]**, dans `scripts/gameplay/`. Trois
formes — disque, secteur d'anneau, capsule —, une entrée `resolve(formes, position, rayon)`, une
autre `first_hit(formes, de, vers, rayon)`. Pur et statique : aucune scène, aucun autoload, aucun
nœud, donc testable à la main comme l'exige la règle du projet.

**2. Un corps coincé sort par le chemin le plus court**, et pour un secteur d'anneau ça fait
**quatre** sorties possibles : la face interne, la face externe, et **les deux bouts de l'arc**.
Ce sont les deux dernières qui manquaient, et qui enfermaient. Le coût d'une sortie par le bout se
mesure en **longueur d'arc** (rayon × angle), jamais en angle : sinon un mur lointain paraîtrait
plus proche par le bout qu'un mur voisin par la face.

**3. Zéro allocation.** Les murs tournent et le noyau dérive : les formes sont refaites à chaque
image. `PlaneShapes` les range à plat dans des tableaux `Packed*` dimensionnés **une fois** ;
`clear()` remet un compteur à zéro et ne libère rien (spec §26.1, gardé par
`test_refilling_the_shapes_never_grows_the_arrays`).

**4. Le noyau est un corps.** Il entre dans le jeu de formes comme un disque de
`flux_hitbox_radius`, au même titre qu'un mur — c'est tout l'intérêt d'avoir un module plutôt
qu'un cas particulier par obstacle. ⚠️ Il est **exclu du test de ligne de tir** : il est là pour
arrêter le chasseur, et l'y laisser ferait de la cible son propre écran.

**5. Le point d'entrée se déduit des anneaux** (`LeviathanTuning.dive_entry_local()`) au lieu de
s'écrire en dur. Changer un rayon déplace l'entrée avec lui, et
`test_the_dive_entry_is_never_inside_a_wall` refuse la combinaison qui enfermerait.

**6. `ReactorRings` ne fait plus de collision.** Ses cinq fonctions ont été **retirées**, pas
laissées à dormir : plus personne ne les appelait, seuls leurs propres tests les maintenaient en
vie. Deux implémentations de la même chose finissent toujours par diverger. Il ne garde que la
**convention** — où sont les ouvertures, dans quel sens ça tourne — et `fill_shapes()` la traduit.

## Ce que la géométrie a coûté

Rendre le noyau solide a fait apparaître qu'**il l'englobait déjà**. `flux_hitbox_radius` vaut
1,80 **en rayon**, plus 0,90 de dérive : le flux occupait jusqu'à 2,70 unités, quand la face
interne du mur intérieur était à 1,70. Ce n'était pas un mur autour du flux, c'était de la
décoration **posée dessus** — visible sur toutes les captures depuis le début, deux arcs violets à
cheval sur la sphère, et aucun test ne le regardait.

L'arène ne pouvait pas absorber ça : 8 unités sous le noyau doivent contenir l'enveloppe du flux,
le couloir de 1,5 largeur de chasseur demandé au playtest, le mur, l'envergure de part et d'autre,
et de quoi voler. **Décision de l'opérateur** : garder les deux murs et réduire la dérive du flux
(0,90 → 0,30). Les anneaux passent à 5,45 et 2,35, épaisseur 0,5 ; il reste 1,45 unité pour
manœuvrer, et le couloir de 2,60 est conservé.

## Conséquences

- `ring_occupancy` passe de 0,45 **estimé** à 0,31 **mesuré sur la géométrie livrée, le long de
  la vraie ligne de tir, avec le rayon du tir**. `flux_health` suit : 780 → 540.
  ⚠️ Les 44 % d'`ADR-0031` étaient encore faux d'un facteur et demi : ils comptaient un tir sans
  épaisseur. C'est la **troisième** version de cette mesure ; la garde refait désormais exactement
  ce que le combat fait.
- La jauge du boss ne lit plus que le flux (voir `ADR-0023`, amendé) : elle ne descend plus en
  phase externe.
- Le module est disponible pour tout le reste du jeu — c'est ce que « facilement utilisable »
  demandait.

## Alternatives écartées

- **La physique native de Godot** (`CharacterBody3D`, `move_and_slide`) — écartée par l'opérateur
  et par la spec : le jeu raisonne en `plane_position` 2D, il aurait fallu faire vivre deux
  sources de vérité pour une seule position, et les unités ne se testeraient plus sans scène.
- **Garder `push_out` en lui ajoutant un cas** — c'est ce qui a produit les cinq fonctions.
