# BRIEF-0104 — compte-rendu : les cinq nœuds siègent en tête de leur tronçon

- **Brief** : `docs/forge/briefs/BRIEF-0104-les-noeuds-remontent-en-tete-de-troncon.md`
- **Date** : 2026-09-06 — `asset-forge`
- **Livrables** :
  - `tools/blender/build_long_cortege.py` (la table `SPINES` + le commentaire qui la tient,
    et une planche d'acceptation `--nodes`)
  - `assets/imported/models/backgrounds/long_cortege.glb` (coque régénérée)
  - `docs/forge/output/BRIEF-0104-planche-noeuds.png` (rendu d'acceptation, 6 vues)
  - ce fichier
- **Empreinte du binaire** :
  `sha256 6682f923afe1fe5f328ee49cdeff066726ad91cd54ff2d3d1e3302bb35224c71`
  — 2 737 480 octets, **49 458 triangles** (55,0 % du budget), **27/27 primitives avec
  `TEXCOORD_0`** (50 251 sommets porteurs d'UV), 27/27 avec `TANGENT`, **0 image embarquée**.
- **Aucun `.gd`, `.tscn` ni `.tres` n'a été touché.** Ce lot ne livre que de la géométrie.

---

## 1. Le diff du contrat de noms : **QUE les cinq `Spine_NN`**

C'est le critère qui prime, il passe donc en premier. Les trente Empties du `.glb` livré ont
été comparés à ceux du `.glb` d'avant le lot (objet LFS `af9418fd…`, le binaire du commit
`df4f6eb`), nom par nom, parent par parent, composante par composante :

```
marqueurs avant : 30    après : 30
marqueurs déplacés : 5 — Spine_01, Spine_02, Spine_03, Spine_04, Spine_05
écart MAXIMAL sur les 25 autres : 0,000000 mm
```

Zéro, pas « sous le dixième de millimètre » : les dix-sept `Turret_NN`, les sept `Bay_NN` et
`Ambry` sont **bit pour bit** aux mêmes coordonnées, chacun toujours enfant du même tronçon.
Les branches de `BRIEF-0103`, qui s'enracinent à la station de leur tourelle, ne se
redessinent donc pas non plus.

| Marqueur | z monde avant | z monde après | s avant | s après | Y avant | Y après |
|---|---|---|---|---|---|---|
| `Spine_01` | −54,1000 | **−46,0000** | 54,1 | **46,0** | −4,7534 | **−4,9075** |
| `Spine_02` | −151,8000 | **−103,0000** | 151,8 | **103,0** | −4,5800 | −4,5800 |
| `Spine_03` | −260,2000 | **−203,0000** | 260,2 | **203,0** | −4,5800 | −4,5800 |
| `Spine_04` | −338,5000 | **−305,0000** | 338,5 | **305,0** | −4,5800 | −4,5800 |
| `Spine_05` | −458,8000 | **−406,0000** | 458,8 | **406,0** | −4,5800 | −4,5800 |

Les cinq restent sur l'axe (x = 0,0000 exactement). Le Y de `Spine_01` descend de 15,4 cm
parce que `spine_seat_y()` le **recalcule** : le fond du canal monte dans le fuseau de proue,
et le marqueur porte l'assise, il ne la choisit pas.

---

## 2. Les cinq stations, mesurées sur les gardes du module

Mesures faites en appelant `spine_seat_y()`, `_scales()`, `_surface_y()` et
`_canal_lane()` du module — pas recopiées du brief. Les deux gardes sont celles de
`_audit()` :

- **fond plat disponible** = `CANAL_FLOOR_HALF × _scales(s).x − 0,04`, il faut ≥ `SPINE_FOOTPRINT_HX` = **0,66** ;
- **tranchée** = `_surface_y(s, CANAL_RIM_X × échelle) − assise`, il faut ≥ **0,35**.

| Marqueur | s | +/début | assise Y | fond plat dispo | marge | tranchée | marge |
|---|---|---|---|---|---|---|---|
| `Spine_01` | **46,0** | +46,0 | −4,9075 | 0,6907 | **+0,0307** | 0,4086 | **+0,0586** |
| `Spine_02` | **103,0** | +3,0 | −4,5800 | 0,7064 | +0,0464 | 0,5300 | +0,1800 |
| `Spine_03` | **203,0** | +3,0 | −4,5800 | 0,7060 | +0,0460 | 0,5300 | +0,1800 |
| `Spine_04` | **305,0** | +5,0 | −4,5800 | 0,7727 | +0,1127 | 0,5300 | +0,1800 |
| `Spine_05` | **406,0** | +6,0 | −4,5800 | 0,8400 | +0,1800 | 0,5300 | +0,1800 |

Les chiffres du brief sont confirmés à l'arrondi près sur les dix valeurs.

### La borne basse de `Spine_01` : **44,018** et non 44,1

Par dichotomie sur la garde elle-même (et non sur une valeur mémorisée), le berceau de
1,32 m cesse de tenir dans le fond plat **en dessous de s = 44,018**. `Spine_01` à 46,0
laisse donc **31 mm**, la plus mince des cinq marges — et à 44,0 la marge est déjà
négative (−0,0003 m). Le brief annonçait 44,1 ; l'écart de 8 cm ne change aucune décision,
mais c'est 44,02 qui est la vraie frontière.

### Où l'artère s'allume vraiment, mesuré par `_canal_lane()`

| voie | |x| | s d'allumage |
|---|---|---|
| interne | 0,14 → 0,32 | **27,277** |
| externe | 0,48 → 0,60 | **41,119** |

Le brief écrit « la voie interne à 28, l'externe à 42 » : mesuré, c'est 27,28 et 41,12.
⚠️ **Et cela nuance sa conclusion** — voir la réserve n° 1, §7.

---

## 3. Les deux fosses qui tiennent `Spine_04` et `Spine_05`, nommées

`_assert_pits_are_clear()` interdit une station de nœud quand l'emprise d'une fosse, garde
(`PIT_KEEPOUT` = 2,20 m) et tablier (`APRON_SPINE` = 3,80 m) compris, **atteint l'axe**.
Les quatre fosses de `PITS` l'atteignent toutes ; les deux qui contraignent ce lot sont :

| Fosse | bord | emprise en x, garde comprise | intervalle de `s` INTERDIT à un nœud |
|---|---|---|---|
| **s = 292** | **bâbord** | −9,00 → **0,00** (x_hi vaut exactement 0) | **280,0 → 304,0** ⇒ `Spine_04` ne peut pas descendre sous 304,1 |
| **s = 393** | **tribord** | **0,00** → +9,00 | **381,0 → 405,0** ⇒ `Spine_05` ne peut pas descendre sous 405,1 |

(les deux autres, s = 136 et s = 228 tribord, interdisent 124,0–148,0 et 216,0–240,0 : elles
ne gênent aucune des cinq stations retenues.)

**La garde a été vérifiée en la faisant tomber**, pas en la lisant :

```
(46.0, 103.0, 203.0, 303.0, 406.0) -> REFUSE :
  - la fosse a s = 292 emporte l'assise de Spine_04 (s = 303)
(46.0, 103.0, 203.0, 305.0, 405.0) -> REFUSE :
  - la fosse a s = 393 emporte l'assise de Spine_05 (s = 405)
(46.0, 103.0, 203.0, 305.0, 406.0) -> PASSE
```

Aucune fosse n'a été déplacée. Si l'une d'elles bouge un jour, c'est ce tableau qui dit ce
qui tenait 305,0 et 406,0.

---

## 4. Ce qui a bougé par ricochet — et les chiffres à imprimer

### Plages nues et part calme

| | avant (stations 54/152/260/338/459) | après (46/103/203/305/406) |
|---|---|---|
| emprises des 30 marqueurs, fusionnées | 206,8 m | **233,2 m** |
| longueur laissée libre | 293,2 m (**58,6 %**) | **266,8 m (53,4 %)** |
| plages nues | 15, dont **12** de 12 m ou plus | **18, dont 11** de 12 m ou plus |
| **bordé nu mesuré sur la géométrie posée** | 253,8 m (**50,8 %**) | **227,4 m (45,5 %)** |
| plus longue plage | 50,3 m | 42,2 m |

⚠️ **Les deux lignes en gras ne mesurent pas la même chose, et le brief mélange les deux.**
Les 53,4 % / 58,6 % qu'il annonce sont le **plafond théorique** (266,8 et 293,2 m sur 500),
c'est-à-dire ce que les emprises de marqueur laissent libre. La **part calme réelle**, celle
que le build imprime en énumérant la géométrie posée, vaut **45,5 %** après contre 50,8 %
avant. Le mouvement est le même (−5,3 points contre −5,2 annoncés) ; c'est l'étiquette qui
diffère. Le témoin « avant » a été produit en rejouant le build hors du dépôt avec l'ancienne
table, avec l'indicateur d'**aujourd'hui** — comparer au chiffre d'un ancien rapport aurait
comparé deux indicateurs.

**Le cliquet des 8 plages est vert** : `_audit()` compte 11 plages nues de ≥ 12 m, il en
exige 8. Le rythme tient.

### L'artère gagne 139 m allumés

| | avant | après |
|---|---|---|
| longueur cumulée allumée | 1 092 m (55 %) | **1 231 m (62 %)** |
| travées sombres | 19 | **21** |
| triangles | 48 678 (54,1 %) | **49 458 (55,0 %)** |

Les conduits ne se posent que dans l'emprise d'une installation : déplacer les nœuds a
déplacé leurs tabliers, et le vocabulaire modulaire a suivi. C'est le comportement attendu,
et il va dans le bon sens — il y a **plus** d'artère à éteindre.

### Ce que le nœud alimente est bien DEVANT le joueur

Mesuré sur le binaire livré, en isolant les triangles `AA_Emissive_Engine` du fond du canal
(|x| < 0,70) tronçon par tronçon :

| Tronçon | artère allumée | allumée **en amont** du nœud | premier segment |
|---|---|---|---|
| 1 | 59,9 m | **10,5 m** (s 27,5 → 38,0) | s 27,5 |
| 2 | 93,0 m | **0,0 m** | s 105,5 |
| 3 | 92,5 m | **0,0 m** | s 206,0 |
| 4 | 86,1 m | **0,0 m** | s 311,1 |
| 5 | 88,9 m | **0,0 m** | s 409,6 |

**Sur quatre tronçons sur cinq, la totalité de ce que le nœud alimente est devant le joueur
au moment où il le rencontre.** Le tronçon 1 fait exception de 10,5 m — voir la réserve n° 1.

### Le kit d'épine suit, ses gardes passent

`spine_kit.glb` est modelé sur le plan Y = 0 du marqueur : il n'a pas à être régénéré. Ses
deux gardes propres, évaluées aux nouvelles stations :

| Marqueur | dénivelé sous l'emprise | marge de jupe (`CRADLE_BURIED` − 0,08) | sommet du nœud | plafond décor |
|---|---|---|---|---|
| `Spine_01` | 0,0788 | **+0,1012** | −3,407 | −3,00 |
| `Spine_02..05` | 0,0000 | +0,1800 | −3,080 | −3,00 |

`Spine_01` gagne au passage 15 cm de dégagement sous le plafond (−3,407 contre −3,253).

---

## 5. Déterminisme, UV, textures

- **`./scripts/build-hull.sh --check long_cortege` : zéro octet divergent.** Le `.glb` a été
  produit **six** fois au total, toujours avec `-t 1` (une fois seul, deux fois par
  `--check` — qui compare lui-même les deux —, trois fois par les rendus de planche, chaque
  rendu rejouant le build). Le sha256 a été relevé après **quatre** d'entre elles :
  `6682f923…` à chaque fois.
- **UV comptées, jamais supposées** : 27 primitives sur 27 portent `TEXCOORD_0`, 50 251
  sommets, 27/27 portent `TANGENT`.
- **Zéro image, zéro texture** dans le `.glb` : `images: 0, textures: 0, samplers: 0`,
  8 matériaux en couleur unie. Conforme au `## Texture` du brief (**aucune** : rien de neuf
  n'est modelé) et à `ADR-0028`.
- Dépliage inchangé — **projection en boîte**, cible 0,200 tuile/m (5,00 m/tuile) :
  mesuré 0,141 à 0,200, moyenne **0,197 t/m**, anisotropie max **1,42** sur les cinq
  tronçons ; Ambry à 0,699 t/m (cible 0,700), anisotropie 1,15. Aucune couture n'a été
  déplacée : aucune surface n'a été redépliée.
- **`## Animation`** : figée, comme le brief le déclare. Aucun pilote, aucune image clé,
  aucune animation dans le `.glb`.
- `./scripts/check.sh` : **ALL GREEN** — 914 tests, 7 031 assertions, 0 échec.

---

## 6. Rendu et REGARDÉ à la caméra du jeu (`ADR-0006`)

`docs/forge/output/BRIEF-0104-planche-noeuds.png` — 1920 × 6480, **six vues à 1920 × 1080**,
c'est-à-dire à la résolution du jeu, à la caméra du jeu (0, 14, 5) / FOV 62°, avec le
Specter-9 réel à l'échelle et les pièces **réelles** de `spine_kit.glb` et `turret_kit.glb`
montées sur les marqueurs. Nouveau mode `--nodes` du script de coque.

**Le cadre ne montre que 26,2 m de pont** (mesuré en intersectant les deux rayons de bord
avec le plan du pont) : c'est toute la raison d'être de cette planche — 26 m sur 500, c'est
ce qui sépare une mécanique lisible d'une mécanique invisible.

| Vue | chasseur | cadre (s) | nœud | hauteur d'écran du nœud |
|---|---|---|---|---|
| tronçon 2 | **exactement sur la frontière s = 100** | 94,8 → 121,0 | `Spine_02` à 103,0 | 41 % |
| tronçon 4 | **exactement sur la frontière s = 300** | 294,8 → 321,0 | `Spine_04` à 305,0 | 49 % |
| tronçon 1 | s = 36 | 30,8 → 57,0 | `Spine_01` à 46,0 | 67 % |

**Ce qu'on voit** : à l'instant même où le chasseur franchit la frontière, le nœud est déjà
dans le cadre, à un peu moins de la moitié de la hauteur d'écran, juste devant le nez de
l'appareil — et toute l'artère qu'il alimente monte devant lui jusqu'au haut du cadre. C'est
la demande de l'opérateur, littéralement.

**Chaque vue est livrée dans les deux états.** L'extinction reproduit le moteur exactement :
matériau **dupliqué par maillage** puis `AA_Emissive_Engine` du **seul tronçon du nœud** posé
à 0,06 (`CortegeSkin.EMISSIVE_DEAD`) contre 0,45 (`EMISSIVE_ENERGY`), et **cœur retiré** du
kit (`cortege_spine_node._take_damage()` : le berceau reste, la carcasse sombre est la preuve
qu'on est passé par là).

Mesure de luminance sur les **pixels de veine** (masque magenta de la vue alimentée), de part
et d'autre de la frontière :

| Vue | veine du tronçon du nœud (au-dessus) | tronçon précédent (au-dessous) |
|---|---|---|
| tronçon 2 | 0,5379 → 0,4932 (**−8,3 %**), 15,6 % des pixels perdent > 20 % | 0,5702 → 0,5703 (**+0,0 %**) |
| tronçon 4 | 0,5873 → 0,5098 (**−13,2 %**), 28,8 % des pixels perdent > 20 % | 0,5923 → 0,5923 (**−0,0 %**) |
| tronçon 1 | 0,6016 → 0,4738 (**−21,2 %**), 33,4 % des pixels perdent > 20 % | 0,5753 → 0,5468 (−5,0 %) |

Le tronçon précédent est **strictement** inchangé (0,0 %) : l'extinction s'arrête à la
frontière, et c'est ce contraste — couloir mort devant, couloir vif derrière — qui dit au
joueur ce que son tir vient de faire. (Le −5,0 % de la troisième ligne n'est pas une fuite :
sous le chasseur, à s < 36, on est **encore dans le tronçon 1**, donc dans la section
éteinte.)

---

## 7. Réserves et limites connues

1. ⚠️ **Le tronçon 1 a bien quelque chose d'allumé en amont de son nœud — 10,5 m.** Le brief
   écrit « le tronçon 1 n'a rien d'allumé en amont à éteindre » ; mesuré sur le binaire, la
   **voie interne** du canal s'allume dès s = 27,3 et un tronçon de conduit est réellement
   posé de **s = 27,5 à 38,0**, soit 8,0 m avant le nœud. Le raisonnement du brief vaut pour
   la voie **externe** (41,1), pas pour l'artère entière. Conséquence pratique : nulle — ces
   10,5 m appartiennent à `Section_01`, donc ils s'éteignent avec le reste quand `Spine_01`
   tombe ; simplement, ils s'éteignent **derrière** le joueur. Et `Spine_01` ne peut pas
   remonter les chercher : 44,02 est un mur (§2). Le seul levier serait de retarder
   l'allumage de la voie interne — décision de conception, hors périmètre.
2. ⚠️ **L'écart alimenté / éteint reste modeste en rendu Cycles** (−8 à −21 % de luminance
   sur la veine) : c'est la réserve déjà remontée par `BRIEF-0103`. Le moteur ne change que
   l'**émission**, alors que le terme diffus de l'albédo domine sous la clé directionnelle,
   et `cortege_emissive` sert d'albédo dans les deux états. Le bloom du jeu, absent de la
   planche, portera l'essentiel de l'écart. Le levier, s'il en faut un, est dans
   `CortegeSkin` (assombrir aussi l'albédo, comme `PANEL_DAMP` le fait pour `AA_Panel`), pas
   dans la géométrie.
3. **Le nœud siège dans une portion sombre du canal, et c'est voulu — mais grossier.**
   `_spine_gap()` écarte **tout un tronçon de conduit** dès qu'il chevauche un nœud à ±2 m ;
   comme un tronçon fait plusieurs mètres, la coupure autour d'un nœud peut atteindre une
   dizaine de mètres (visible sur la vue du tronçon 1 : rien d'allumé entre s ≈ 38 et 48,4
   hormis le cœur du nœud). La lecture « le nœud est **sur** la conduite » est tenue ; une
   coupure plus courte demanderait de **tailler** le tronçon au lieu de le jeter — une
   évolution de `build_conduits()`, hors périmètre de ce lot.
4. **Le mode `--nodes` ajouté au script dépasse la lettre du brief**, qui n'y demandait que
   la table `SPINES` et son commentaire. Il a été ajouté pour que la planche d'acceptation
   soit **rejouable** (comme `--plate` et `--branches` avant elle) plutôt que produite par un
   script jetable. Il ne pose aucune géométrie et n'entre pas dans le `.glb` : les quatre
   builds successifs rendent le même sha256.
5. ⚠️ **Un commit de la session principale a emporté du travail en cours de la forge.**
   `ec4b770` (17:54:49) contient déjà le `.glb` régénéré et les 35 lignes de la table
   `SPINES` — écrits pendant que le lot tournait. Rien n'est perdu et le contenu committé est
   le bon, mais c'est exactement le défaut « un seul écrivain dans le dépôt » : la forge n'a
   rien committé, ni ici ni ailleurs. Restent non committés : le mode `--nodes`, la planche,
   ce rapport et la ligne de provenance.

---

## 8. Provenance

La ligne **existante** `long_cortege_hull` d'`assets/licenses/ASSET_PROVENANCE.csv` a été
mise à jour (pas dupliquée) : `modified_by` gagne `BRIEF-0104, 2026-09-06`, les notes portent
les nouvelles stations, les marges, les deux fosses, la mesure des plages nues et le nouveau
sha256. `source_tool` passe de `Blender 4.5.11` à **`Blender 5.2.1`**, qui est la version qui
a réellement produit ce binaire (le dépôt a migré au commit `2202ae6`) — le champ était
devenu faux.

Deux lignes **neuves** ont été ajoutées pour les deux autres fichiers livrés :
`brief_0104_planche_noeuds` (la planche, `render`) et `brief_0104_report` (ce fichier, `doc`),
sur le modèle des lignes `brief_0102_*`. La planche est prise par Git LFS
(`git check-attr filter` → `lfs`), comme l'exige la spec §24.8.
