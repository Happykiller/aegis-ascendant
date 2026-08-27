# ADR-0031 — On ne vise pas en pivotant : le blindage rythme le tir, il ne le porte pas

- **Statut** : accepté
- **Date** : 2026-08-27
- **Contexte** : Chambre du Réacteur, lot 3 — playtests des 2026-08-27 (soir)
- **Remplace/amende** : le postulat de conception du blindage rotatif (plan
  `docs/plans/2026-08-27-reactor-chamber.md`, lot 1)

## Contexte

Le boss final enferme son noyau derrière **deux anneaux blindés contrarotatifs**, percés
d'ouvertures. L'intention écrite était : « leur corridor commun se déplace vite, et le joueur doit
**aller le chercher** au lieu de camper sous le noyau ».

Toute la vérification était bâtie sur cette phrase. La garde de référence mesurait qu'« un corridor
existe **quelque part sur le cercle** 100 % du temps, verrou le plus long 0,00 s » ; une seconde
bornait la couverture à moins de 35 % pour que le blindage reste un blindage. Les deux étaient
vertes. L'équilibrage, lui, dimensionnait le flux avec `ring_occupancy = 0,45`, valeur **annoncée
comme une estimation** et justifiée par : « un joueur immobile n'aurait que ~13 % ; un joueur qui
suit l'ouverture a bien davantage ».

Au playtest, le combat n'a pas été difficile : il a été **interminable**. Douze plongées à puissance
maximale, là où l'ossature en prévoit trois. Rien n'était rouge.

## Le défaut

**Le chasseur tire droit vers le haut.** Il ne possède pas d'azimut — seulement une position. Le
seul angle sous lequel il peut atteindre le noyau est **par le bas**, toujours le même. Se déplacer
latéralement ne lui donne aucun autre angle : ça ne fait que le désaligner.

« Aller chercher le corridor » **n'existe pas** dans un shoot vertical. Le joueur ne pouvait
qu'**attendre** que l'ouverture passe devant lui — et l'ouverture, au bas du cercle, n'était
dégagée que 46/120 × 62/180 = **13 %** du temps. Exactement le chiffre du « joueur immobile » que
l'estimation écartait comme le mauvais cas.

Deux fautes se sont couvertes l'une l'autre :

1. **On mesurait au mauvais endroit.** « Un corridor existe quelque part » est vrai en permanence et
   ne dit rien sur ce que le joueur peut faire. La bonne mesure est la fraction de temps où **la
   ligne de tir réelle** est dégagée.
2. **Deux chiffres sur le même fait ne se parlaient pas.** La borne du test (« < 35 % ») était
   inventée, et l'estimation d'équilibrage (0,45) n'était confrontée à aucune géométrie. La panne
   exacte qu'`ADR-0024` avait déjà coûtée au projet.

## Décision

**1. Le blindage rythme le tir ; il ne demande plus de se placer.** L'intention « aller chercher le
corridor » est **abandonnée** : elle est irréalisable dans le genre. Un obstacle qui coupe la ligne
de tir par intermittence reste légitime — il donne une cadence, et une cadence se lit et
s'anticipe.

**2. Les ouvertures sont élargies pour que la promesse écrite soit tenue** : `46° -> 80°` (anneau
extérieur, 3 ouvertures) et `62° -> 120°` (anneau intérieur, 2 ouvertures). À azimut fixe, un
anneau est ouvert `aperture/step` du temps et les deux tournent à des vitesses incommensurables :
80/120 × 120/180 = **44 %**, soit les 45 % dont l'équilibrage déduit déjà la santé du flux.

**3. `ring_occupancy` cesse d'être une estimation.** Elle devient la **valeur de référence**, et
`test_the_shield_opens_as_often_as_the_balance_assumes` compare la couverture **simulée sur la
géométrie livrée** à cette valeur, à ±6 points. Changer les ouvertures sans corriger l'estimation —
ou l'inverse — rougit désormais.

**4. La porte se teste sur la ligne, pas sur l'azimut.** `ReactorRings.first_hit_along()` /
`line_blocked()` évaluent le segment **joueur -> flux** ; `blocks_body()` ajoute la demi-envergure
angulaire du corps (`asin(body / distance)`) pour qu'une aile ne traverse pas un bord que le centre
franchit.

## Conséquences

- Le combat retrouve son ossature de trois cycles ; `flux_health` n'a **pas** été retouché, la
  correction porte sur la géométrie qui rendait l'estimation fausse.
- La leçon est promue en loi de genre : [`LOI-SYS-07`](../design/bible/09-regles-et-systemes.md)
  — *le joueur vise en se déplaçant, jamais en pivotant*. Elle est universelle, pas propre à ce
  boss : elle interdit toute porte filtrée sur l'azimut du joueur.
- Les verrous orbitaux restent désactivés (décision du playtest précédent) ; le mécanisme reste
  codé et testé pour ses deux autres rôles.

## Alternatives écartées

- **Baisser `flux_health`** — rattraper des points de vie aurait masqué une géométrie fausse, et
  laissé la mécanique demander au joueur une chose impossible. C'est le calibrage silencieux
  d'`ADR-0024`, une deuxième fois.
- **Ralentir les anneaux** — ne change pas la fraction de temps dégagée, seulement sa granularité :
  des attentes plus longues et moins nombreuses. Le défaut est un rapport, pas une vitesse.
- **Donner une visée libre au chasseur** — hors du genre, et hors spec.
