# Fiches techniques des coques - données du Bestiaire

- **Brief** : `docs/forge/briefs/BRIEF-0037-codex-fiches-techniques-coques.md`
- **Type** : document de données (aucun asset chargé par le moteur)
- **Usage** : alimenter l'écran Bestiaire en champs de fiction. Les dimensions, points de
  structure, vitesses, cadences, scores et rayons de touche **ne figurent pas ici** : ils sont
  mesurés à l'exécution ou lus dans les Resources de gameplay.

Contrainte typographique (ADR-0012) : les champs `designation`, `classe`, `constructeur` et
`statut` sont en **ASCII pur, sans accent** (affichage tout en capitales en Press Start 2P).
Seule la `notice` est en casse normale et porte des minuscules accentuées. Aucune puce, aucun
tiret cadratin ni aucune flèche typographique dans les valeurs : seuls `-` et `>` sont admis,
apostrophes droites uniquement.

---

## Specter-9

| Champ | Valeur |
|---|---|
| `designation` | `HV-09` |
| `classe` | `MICROCHASSEUR MONOPLACE D'ASSAUT` |
| `constructeur` | `ARSENAL ORBITAL TALVERN` |
| `masse_t` | `1.42` |
| `equipage` | `1` |
| `statut` | `EN SERVICE ACTIF` |
| `notice` | Coque monoplace en décubitus ventral, dimensionnée au strict volume du pilote et de sa capsule. Les ailes à flèche variable et les volets de bord de fuite achètent un virage sec au prix d'une stabilité nulle sans assistance. Blindage minimal assumé: la survie tient au bouclier et au pilotage. |

## Needle Scout

| Champ | Valeur |
|---|---|
| `designation` | `NX-021` |
| `classe` | `VECTEUR D'ESSAIM POLYVALENT` |
| `constructeur` | `INCONNU - PRODUCTION SERIE` |
| `masse_t` | `0.19` |
| `equipage` | `0` |
| `statut` | `HOSTILE - EN NOMBRE` |
| `notice` | Contact le plus fréquent du théâtre, et le seul dont la production semble industrialisée: les épaves recueillies ne montrent aucune variation de coque. Le même fuseau couvre plusieurs profils de vol, qui ne se lisent qu'une fois l'engagement commencé. Aucune cavité habitable relevée. |

## Crescent Interceptor

| Champ | Valeur |
|---|---|
| `designation` | `NX-034` |
| `classe` | `LAME D'INTERCEPTION RAPIDE` |
| `constructeur` | `INCONNU - VARIANTE SERIE` |
| `masse_t` | `0.16` |
| `equipage` | `0` |
| `statut` | `MENACE CONFIRMEE` |
| `notice` | Lame aplatie, presque sans épaisseur de face: la coque sort du champ visuel dès qu'elle se met sur la tranche. Elle entre en crochet, repasse, et ne tient jamais un cap plus de deux secondes. La vitesse est payée par une structure qui cède au premier impact franc. |

## Choir Harvester

| Champ | Valeur |
|---|---|
| `designation` | `NX-208` |
| `classe` | `PLATEFORME DE COLLECTE ARMEE` |
| `constructeur` | `INCONNU - ASSEMBLAGE UNIQUE` |
| `masse_t` | `12.4` |
| `equipage` | `0` |
| `statut` | `MENACE MAJEURE` |
| `notice` | Assemblage isolé, jamais observé deux fois à l'identique: cinq pétales et trois bras articulés refermés sur un noyau. Les bras travaillent en séquence et découvrent le noyau entre deux passes, assez longtemps pour être exploité. Aucune pièce ne paraît usinée. |

## The Pale Leviathan

| Champ | Valeur |
|---|---|
| `designation` | `NX-001` |
| `classe` | `NOYAU DE COMMANDEMENT MOBILE` |
| `constructeur` | `INCONNU - CROISSANCE XENO` |
| `masse_t` | `44.6` |
| `equipage` | `0` |
| `statut` | `PRIORITE ABSOLUE` |
| `notice` | Première structure cataloguée du Null Choir, et la seule de cette masse à ce jour. Anneau incomplet dont le noyau reste exposé; la coque se réorganise en cours d'engagement et change quatre fois de comportement. Tout contact est traité en priorité absolue, sans exception. |

---

## Cohérence

Raisonnement d'échelle (non affiché en jeu, pour la review) :

- La masse est dérivée du **volume de boîte englobante** mesuré (envergure x tirant x longueur),
  affecté d'un taux de remplissage et d'une densité de matière.
- Les **petites coques sont denses** : 0,5 à 0,7 t/m3 de boîte (Specter-9 1,42 t pour 2,80 m3 ;
  Needle Scout 0,19 t pour 0,28 m3 ; Crescent Interceptor 0,16 t pour 0,30 m3). Un fuseau ou une
  lame remplissent bien leur boîte, et le peu de volume disponible est occupé par de la machine.
- Les **grandes coques sont creuses** : 0,29 à 0,30 t/m3 de boîte (Choir Harvester 12,4 t pour
  43,2 m3 ; Pale Leviathan 44,6 t pour 146,7 m3). Bras articulés, pétales ouverts et anneau
  incomplet laissent l'essentiel de la boîte vide ; la densité chute, la masse absolue grimpe
  quand même d'un facteur 65 entre le plus petit et le plus gros.
- Le Specter-9 de 2,46 m est traité comme un **microchasseur** : le pilote est allongé, la coque
  est dimensionnée sur lui, et la masse (1,42 t, l'ordre de grandeur d'une petite automobile)
  reste celle d'un engin habité blindé au minimum. Les trois vies du joueur ne sont donc pas
  trois pilotes mais trois cellules disponibles au hangar.
- La matière du Null Choir est prise plus légère que l'alliage allié (env. 1,1 contre 1,7 t/m3 de
  matière pleine), ce qui laisse au Specter-9 une masse supérieure à toutes les coques ennemies
  de sa taille.
