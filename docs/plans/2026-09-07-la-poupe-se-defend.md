# La poupe se défend — mettre du challenge sur la phase finale du niveau 2

- **Date** : 2026-09-07
- **Demande** : *« Il va falloir qu'on mette du challenge. Aujourd'hui, il n'y a rien, on tire
  sur les trucs. Donc place des grosses tours, des petites tours, des tourelles, des moyennes
  tourelles aussi. On peut placer des vagues d'ennemis aussi, de plusieurs types. »*
- **État de départ** : commit `47d7bce`, 962 tests verts, GPU 2,6 ms/image (RTX 4080).

---

## 0. La tension à nommer d'abord

`cortege_root.gd:466` tient les deux nuées en laisse dès que la poupe est montée, et cite la
spec §19 : *« je réduirais énormément les ennemis, pas de respawn »*. Ce plan **relâche cette
laisse** sur demande explicite de l'opérateur (2026-09-07). Ce qui reste de la spec §19 :

- **pas de respawn** — une tourelle abattue reste abattue, une salve consommée ne revient pas ;
- **les moteurs restent les protagonistes** — rien ne doit masquer un verrou, ni occuper la
  ligne de tir qui y mène ;
- **le silence de la spec §17 est intouchable** (décision de l'opérateur) : quand la propulsion
  meurt, plus rien n'entre. Les coques en vol finissent leur trajectoire, c'est tout.

Un ADR actera l'écart en fin de chantier (LOT 4).

## 0.1 Les quatre décisions prises (2026-09-07)

| # | Question | Décision |
|---|---|---|
| D1 | Le rythme | **Escalade sur les arrachements** — la poupe est déjà gardée à l'arrivée, et chaque moteur perdu la durcit. Trois paliers. |
| D2 | Le placement | **Les deux, par calibre** — les légères gardent les berceaux, les moyennes tiennent les flancs, les lourdes le massif arrière. |
| D3 | Les vagues | **Salves aux moments clés** — ouverture des verrous, chaque moteur perdu, exposition du central. |
| D4 | Le silence final | **Intouchable.** |

---

## 1. Ce que la géométrie permet, mesuré

### 1.1 Les deux seules zones libres

`BRIEF-0106-report.md` §1 : les trois emprises de berceau **se recouvrent** et n'en forment
qu'une seule.

```
   |x| <= 15,78   et   |z| <= 8,00      ->  interdit au-dessus du pont (-11,85)
```

Il ne reste donc que **les flancs** (`|x| >= 16,20`) et **le massif arrière** (`z <= -8,60`)…
plus deux bandes que le rapport ne compte pas parce qu'elles sont **au niveau du pont** et non
au-dessus : la dalle du bassin déborde les berceaux de 1,9 m à l'avant et à l'arrière.

| Zone | Cotes | Ce qu'elle porte |
|---|---|---|
| Bande avant du bassin | `z ∈ [6,1 ; 7,95]`, `y = −11,85` | les légères qui gardent les berceaux |
| Bande arrière du bassin | `z ∈ [−8,20 ; −6,1]`, `y = −11,85` | idem, côté fuite |
| Étagère de rive B1 | `|x| ∈ [16,60 ; 17,00]`, `y = −6,60` | — trop étroite (0,40 m) |
| Étagère de rive B2 | `|x| ∈ [17,60 ; 18,40]`, `y = −5,60` | les moyennes |
| Étagère de rive B3 | `|x| ∈ [18,60 ; 19,80]`, `y = −4,60` | les moyennes (bord de portée, § 1.3) |
| Plateau du massif | `z <= −8,60`, `y = −8,40` | les lourdes, à côté des tours d'échange |

Les quatre **pylônes de rive** occupent déjà `z ∈ [−2,15 ; 1,35]` et `[−7,75 ; −4,25]` sur les
étagères : ce sont les « grosses tours » de la demande, et elles sont **déjà là**. Ce chantier
leur donne des voisines armées, il ne les remplace pas.

### 1.2 ⚠️ Le piège de projection, et il a déjà coûté deux défauts

Une pièce posée sur la coque a sa **hitbox projetée** par `GameplayPlane.aim_point_of()` :

```
   t = -14 / (y_monde - 14)          plan_x = t * monde_x
                                     plan_y = -(5 + (monde_z - 5) * t)
```

**`t` dépend de la HAUTEUR de la pièce.** Plus une tourelle est haute sur la coque, plus sa
hitbox s'écarte du centre de l'écran — une lourde perchée sur un pylône à `y = −3,30` voit sa
hitbox partir à `plan_x = 0,81 × monde_x`, contre `0,54` pour la même pièce posée sur le pont.

Or **le réglage de la poupe (`CortegeSternTuning`) raisonne en monde 1:1** — `hold_plane_y`,
`anchor_reach()`, `anchor_rows()` traitent `world.xz` comme `plane.xy`. C'est conservateur pour
les ancrages (leur hitbox réelle est *plus* près du centre que le réglage ne le croit), mais
c'est un piège pour tout ce qu'on posera plus haut.

⚠️ **Aucune cote de placement ne sera écrite « à vue ».** Chaque emplacement passe par un
helper qui projette, et un invariant refuse toute pièce dont la hitbox sort de
`GameplayPlane.BOUNDS` ou de sa propre fenêtre de tir. C'est la troisième fois que ce défaut se
présente (`pratique-le-plan-de-vol-n-est-pas-le-cadre`) ; cette fois il est gardé par un test.

### 1.3 Les fenêtres de tir, qui décident du calibre autorisé

`turret_fire_span_of()` : légère **14** (demi 7), moyenne **20** (demi 10), lourde **26**
(demi 13). Et `target_span = 26` (demi 13) décide de ce qui est **touchable**.

| Emplacement | `plan_y` calculé | Calibres possibles |
|---|---|---|
| Bande avant du bassin (`z_local` +7,0) | **−2,6** | tous |
| Bande arrière du bassin (`z_local` −7,0) | **+5,0** | tous |
| Étagère B2 (`z_local` +2,0) | **+1,8** | tous |
| Plateau du massif (`z_local` −10,0) | **+8,4** | moyenne, lourde |

⚠️ **Une légère sur le massif arrière ne tirerait jamais** — elle serait visible, tournerait
vers le joueur, et resterait muette. Défaut exactement symétrique de « elle est visible,
pourtant je ne la touche pas ».

---

## 2. Les lots

### LOT 1 — La garnison

Une table de placement typée, montée par `CortegeStern`, trois calibres, chaque pièce enfant de
la poupe (donc solidaire du vaisseau, comme les ancrages).

- `CortegeSternGarrison` : la table + le montage + le `tick` groupé (les pièces n'ont pas de
  `_process` à elles, même règle que `CortegeHardpoints`).
- Réglages dans `CortegeSternTuning` : nombre par calibre, réserve, score.
- **Invariants** : rien dans l'emprise des berceaux ; hitbox dans `BOUNDS` ; `plan_y` dans la
  fenêtre de tir du calibre ; aucune pièce sur la ligne de tir d'un verrou.
- **Recette** : capture à la caméra du jeu, `--hide-solids` **et** `--show-solids` (la seconde
  prouve que les hitboxes tombent où l'on croit).

### LOT 2 — L'escalade

Trois paliers, déclenchés par les arrachements — c'est le vaisseau qui réagit à ce qu'on lui
prend, pas un minuteur.

| Palier | Déclencheur | Ce qui change |
|---|---|---|
| 0 | arrivée | la garnison de base tire |
| 1 | premier moteur arraché | la réserve s'éveille ; cadence +25 % |
| 2 | second moteur arraché | cadence +50 % ; les moyennes passent en tir soutenu |
| 3 | central exposé | **la contre-attaque** : tout ce qui reste tire sans répit |

- Lyra commente le palier 3 (la réplique `engine_transfer` existe déjà — la doubler serait du
  bruit ; on la laisse et on ajoute **un** signal sonore).
- **Recette** : bissection par drapeau `--stern-tier=N` pour entrer directement dans un palier.

### LOT 3 — Les salves

`resources/encounters/wave_cortege_stern.tres` — un jeu de vagues **événementiel**, pas
chronométré : `WaveSpawner` sait déjà naître hors cadre depuis le correctif du 2026-09-06.

| Salve | Déclencheur | Composition |
|---|---|---|
| A | ouverture des verrous | éclaireurs + arcs — apprendre la phase sous pression légère |
| B | premier moteur perdu | sangsues + porteur : il faut arrêter de tirer sur les verrous |
| C | second moteur perdu | pillards + mines |
| D | central exposé | gueules + intercepteurs — le pic |

⚠️ **Aucune salve après la coupure de propulsion** (D4). Le `hold()` des deux nuées du corridor
reste en place : les salves de poupe sont un troisième spawner, à elles.

### LOT 3 bis — Le chevauchement, et les plates-formes volantes *(fait)*

Retour de l'opérateur sur capture : « on a beaucoup de chevauchement ; tu pourrais mettre des
canons sur la fin du corps du vaisseau, ok sur au bout du mur, et pour la profondeur on pourrait
faire des plates-formes volantes ».

- Les six légères alignées sur la lèvre du bassin tombent à deux : leurs hitboxes projetées
  étaient jointives alors que les cotes étaient disjointes de 3,4 m.
- **Des canons sur la fin du corps du vaisseau** : la dernière tourelle du corridor est à
  `s = 478,8`, les vingt derniers mètres n'avaient rien. Une moyenne et une légère par bord, à
  `z_local` 12,5 et 13,0 — la seule menace du niveau qui tire vers le HAUT de l'écran.
- **Des plates-formes volantes** : elles résolvent ce qui bloquait le lot. La carène n'a aucune
  surface plane de plus de 1,40 m hors du massif arrière, si bien que toute moyenne posée sur un
  gradin flottait à moitié. Une dalle qui flotte vraiment donne une assise franche à n'importe
  quelle hauteur. Elles restent hors de l'emprise des berceaux.
- Deux invariants neufs : **écart projeté** et **écart dans le monde** entre toutes les paires.

⚠️ Reste ouvert pour la forge : la carène n'a **pas de plates-formes d'armement** à l'avant.
Un brief pourrait lui en donner ; les plates-formes volantes rendent ce travail facultatif.

### LOT 4 — L'équilibrage, la revue, la doc

- Jouer, mesurer (temps GPU, pas FPS), capturer les quatre paliers.
- ADR : l'écart assumé à la spec §19, avec ce qu'on en garde.
- Ghost : ce que la projection de hitbox a appris.
- `docs/KB/` : la page de la phase finale.

---

## 3. Ce qui est hors périmètre

- **Le corridor** : ses dix-sept tourelles et sept ponts ne changent pas.
- **Les verrous, les moteurs, l'arrachement** : la mécanique est validée, on ne la retouche pas.
- **Le silence final** et l'aveu de Lyra.
- **Une nouvelle coque d'ennemi** : le bestiaire en compte treize, ça suffit.
