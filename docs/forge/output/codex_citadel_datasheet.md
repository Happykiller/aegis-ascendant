# Fiche technique de l'Aegis Citadel - données du Bestiaire

- **Brief** : `docs/forge/briefs/BRIEF-0038-codex-fiche-aegis-citadel.md`
- **Type** : document de données (aucun asset chargé par le moteur)
- **Usage** : sixième entrée du Bestiaire, en complément de
  `docs/forge/output/codex_hull_datasheets.md` (BRIEF-0037). Les dimensions, le nombre de
  triangles, de tourelles, de balises, de batteries lourdes et de baies **ne figurent pas ici** :
  ils sont mesurés sur la coque à l'exécution. Cette coque n'ayant ni points de structure, ni
  vitesse, ni cadence de tir, aucune de ces trois lignes n'est proposée.

Contrainte typographique (ADR-0012) : les champs `designation`, `classe`, `constructeur` et
`statut` sont en **ASCII pur, sans accent** (affichage tout en capitales en Press Start 2P).
Seule la `notice` est en casse normale et porte des minuscules accentuées. Aucune puce, aucun
tiret cadratin ni aucune flèche typographique dans les valeurs : seuls `-` et `>` sont admis,
apostrophes droites uniquement.

---

## Aegis Citadel

| Champ | Valeur |
|---|---|
| `designation` | `HV-01` |
| `classe` | `CORVETTE-FORTERESSE PILOTABLE` |
| `constructeur` | `ARSENAL ORBITAL TALVERN` |
| `masse_t` | `690.8` |
| `equipage` | `18` |
| `statut` | `EN SERVICE - UNIQUE` |
| `notice` | Prisme axial habité, plus proche de la corvette que de la station: elle rejoint sa position de combat par ses propres moyens. Sa baie ventrale recueille le chasseur en vol; la passerelle bascule alors sur le pilote entrant, qui prend la coque en main. Les servants restent aux batteries pendant toute la phase. |

---

## Cohérence

Raisonnement d'échelle (non affiché en jeu, pour la review) :

- Même modèle qu'en BRIEF-0037 : masse = boîte englobante x taux de remplissage x densité de
  matière. La boîte mesurée fait 19,63 x 5,30 x 16,60 = **1 727 m3**, soit 11,8 fois celle du
  Pale Leviathan (146,7 m3) : la citadelle reste la plus grosse coque du catalogue, et de loin.
- Sa densité est prise à **0,40 t/m3 de boîte**, au-dessus des 0,30 t/m3 des deux grandes coques
  ennemies : là où le Harvester ouvre ses pétales et où le Leviathan laisse son anneau incomplet,
  le prisme axial remplit sa boîte de blindage, de machines et de soutes. D'où 690,8 t, soit
  15,5 fois le Leviathan pour 11,8 fois son volume - l'écart vient de la matière, pas du gabarit.
- La progression du catalogue reste monotone et lisible : 0,16 t (Crescent) < 0,19 t (Needle) <
  1,42 t (Specter-9) < 12,4 t (Harvester) < 44,6 t (Leviathan) < 690,8 t (Aegis Citadel).
- `equipage` = 18 : à 8 % de volume pressurisé sur la boîte, on obtient environ 140 m3 habitables,
  soit près de 8 m3 par personne - le standard d'un bâtiment militaire tenu en quarts. Cela couvre
  une passerelle, les servants des deux batteries lourdes, le pont d'appontage et la conduite du
  noyau, les six tourelles et les trois balises étant asservies. Le pilote du Specter-9 arrive en
  dix-neuvième et prend la main : il embarque, il ne remplace personne.
