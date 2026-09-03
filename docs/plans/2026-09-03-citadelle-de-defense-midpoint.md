# Niveau 2 — la Citadelle de Défense : un verrou de level design à mi-parcours

| | |
|---|---|
| **Date** | **2026-09-03** |
| **Auteur** | session Claude, sur le brief d'implémentation et la planche de l'opérateur |
| **Périmètre** | une séquence de 30 à 45 s au milieu du Long Cortège : une fortification transversale qui **ferme physiquement la route**, s'ouvre en sabotant deux relais puis un noyau, et rend le passage praticable |
| **État** | **à appliquer** — rien n'est engagé côté code. ✅ **Les trois arbitrages sont tranchés** (2026-09-03) ; reste la seule cote verticale (C1), au LOT 0. Les deux demandes de texture sont écrites et partent en parallèle |
| **Supersède** | rien. Il **complète** `2026-08-29-niveau-2-execution.md` (le niveau de bout en bout) et vit sous les contraintes de `2026-08-29-niveau-2-refonte-geometrie.md`, dont il reprend le test d'acceptation |
| **Source** | brief d'implémentation « MIDPOINT CITADELLE DE DÉFENSE » (opérateur, 2026-09-03) + planche `assets/reference/concepts/citadelle_de_defense_midpoint.png` |

## Ce que la séquence doit être, en une phrase

> « Ce gigantesque vaisseau m'a fermé la route ; j'ai saboté son verrou défensif pour continuer. »

**Ce n'est pas un boss** — et c'est la contrainte qui prime sur toutes les autres. Pas de barre de
vie, pas d'objet à gros PV, pas de rideau de projectiles. Une boucle :

```
APPROACH → FORTRESS_LOCKED → (RELAY_LEFT | RELAY_RIGHT, dans n'importe quel ordre)
         → SHIELD_DISABLED → CORE_DESTROYED → OPENING → CLEARED
```

---

# ⚠️ Ce qui existe déjà, et qu'il ne faut PAS repayer

Le brief demande cinq choses que le dépôt porte **déjà**. Les redécouvrir coûterait une session.

| Le brief demande | Ce qui est en dépôt |
|---|---|
| §8 « introduire une variante de petite tourelle » | ✅ **livrée le 2026-09-03** — `CortegeTuning.TurretScale.LIGHT`, 21 pièces en 7 batteries, `cortege_light_shot.tres`, sa table `BATTERIES`, ses 12 tests. **Rien à créer** : la citadelle en pose 4 à 6, c'est tout |
| §12 « ralentir puis arrêter le scrolling » | ✅ **un seul float** — `CortegeFlyby.scroll_speed` (2,4), lu en `_travelled += scroll_speed * delta`. Aucune refonte, un `Tween` suffit |
| §11 « collision bloquante, puis suppression fiable » | ✅ **`PlaneCollider` + `PlaneShapes`** — écrit pour la chambre du réacteur, il fait sortir un corps coincé **par le chemin le plus court**. C'est exactement le système qui a corrigé « je fonce tout droit et mon vaisseau est bloqué » |
| §15 « quatre états visuels lisibles » | ✅ **`SolidsOverlay`** (`--show-solids`) montre ce qui arrête un corps ET ce qu'une balle touche. C'est lui qui prouvera que la collision disparaît vraiment |
| planche : bandeau « TRAVERSÉE 02/05 » | ✅ **déjà en jeu** — `fighter_hud.gd` porte `_survey_panel`, `_survey_track`, `_survey_fill`, `_survey_label`, et `CortegeFlyby.progress()` l'alimente |

S'ajoutent, réutilisables sans modification : `CortegeTurret` (destruction, épave, familles, `serial`),
`CortegeBay` (hangar, séquence de décollage en quatre temps), `CortegeSpineNode` (le précédent d'un
objectif qui **change l'état du niveau**), le kit de tourelle paramétrique, Lyra
(`lyra_cortege.tres`, `dialogue_box.gd`) et la palette 80/15/5.

---

# Les contraintes dures — aucune n'est une opinion

## C1 — ⛔ Le budget vertical est de **1,30 m**, le brief en demande **2,50**

C'est le point qui décide de la silhouette, et il tombe avant tout le reste.

```
  -2,40   plafond du GAMEPLAY  (ADR-0041 — une tourelle se tire dessus)
  -3,00   plafond du DECOR INERTE
  -3,20   plafond de CONSTRUCTION (BUILD_CEILING_Y)
  -4,30   le pont
```

| Le brief (§3) | Disponible | Verdict |
|---|---|---|
| plateformes « +0,5 à +1 m » | 1,30 m de décor | ✅ tient |
| bastions « +1,5 à +2,5 m » | **1,30 m** (décor) / **1,90 m** (gameplay) | ⛔ **impossible en l'état** |

⚠️ **Et le plafond n'est pas décoratif** : il protège ce qui masquerait le combat sans jamais
pouvoir être touché. `_assert_build_ceiling` a déjà refusé une passerelle à −3,15.

**Trois issues, à trancher au lot 0** : (a) réécrire les cotes du brief dans le budget réel — un
bastion de 1,80 m *paraît* haut quand tout le reste fait 1,10 m ; (b) obtenir de la hauteur par le
**creux** plutôt que par la masse, comme les fosses du lot B3 : une citadelle qui *descend* dans la
coque lit aussi bien qu'une qui monte ; (c) amender `ADR-0041` pour cette séquence seule — le plus
cher, et il faudrait démontrer que rien n'est masqué.

## C2 — La mi-parcours n'offre que **18 m** de coque libre

Relevé sur les tables, à s = 200–300 (le milieu du survol est s = 250) :

| | s | ce que c'est |
|---|---|---|
| `Turret_06` | 216,6 | socle, tronçon 3 → rayon 2,75 |
| `Bay_04` | 224,6 | **ouverture** dans la peau |
| fosse | 228,0 | 12 m de long, garde 2,20 |
| **fenêtre libre** | **≈ 236 → 254** | **18 m** |
| `Turret_07` | 258,0 | socle |
| `Spine_03` | 260,2 | nœud d'épine |
| `Turret_08` | 263,0 | socle |

⚠️ **Et cette fenêtre est une respiration VOULUE** : `cortege_hardpoints.gd` l'écrit — « RIEN AU
DÉBUT DU TRONÇON 3 (s 214 à 246) : c'est la respiration, et elle est voulue ». Y poser une
fortification la consomme. Ce n'est pas un interdit, c'est un arbitrage à énoncer.

Élargir au-delà de 18 m **déplace des marqueurs**, et un marqueur déplacé rejoue son Y et les
fenêtres de relâche du `BRIEF-0092` — c'est un chantier, pas un réglage (le lot B4 l'a payé).

## C3 — Un mur transversal doit franchir la **contremarche de chine**

Le pont a deux paliers : intérieur (|x| 2,20 à 6,80, à −4,30) et médian (7,35 à 10,30, à −4,99),
séparés par 60 cm. Une citadelle « transversale » traverse les deux **et l'artère centrale**. Toute
pièce posée sans tenir compte du palier flotte de 69 cm au-dessus du vide, en silence — le défaut
que `test_cortege_light_turrets.gd` garde déjà pour les batteries.

## C4 — Les cinq tronçons sont des objets **séparés**

Une pièce à cheval sur z = −200 ou z = −300 serait coupée en deux maillages, sans qu'aucune erreur
ne le dise (leçon de la passerelle, lot C3). La citadelle doit **tenir dans un seul tronçon** —
avec la fenêtre de C2, c'est le tronçon 3.

## C5 — 40 s de séquence valent **96 m de coque** à vitesse normale

Le survol fait 500 m en 208 s (`scroll_speed` = 2,4 m/s). Une séquence de 40 s consommerait **un
cinquième du vaisseau**, ce que C2 rend impossible. **Le ralentissement n'est donc pas un effet de
mise en scène : c'est ce qui rend la séquence géométriquement possible.** À budget : arrêt complet
pendant la phase de combat, reprise progressive après `OPENING`.

## C6 — Le noyau est **invulnérable**, pas « très résistant »

`enemy_controller` porte `_shield_grace` — une invulnérabilité **temporaire**, par durée. Ce n'est
pas un bouclier de zone conditionné par deux relais. Le bouclier central est donc **à créer**, et sa
règle est booléenne : tant que les deux relais vivent, aucun point de vie ne bouge, et l'impact se
voit **sur le bouclier**. Un noyau à 99 % de PV qui descend lentement raconterait un boss.

---

# Les tensions — ✅ **TRANCHÉES par l'opérateur le 2026-09-03**

## T1 — La symétrie est **autorisée**

> « pas grave dans le cadre d'un boss ou event pour la symétrie »

La planche fait foi : **deux bastions en miroir, deux relais aux mêmes places, bouclier centré.**
L'interdit du §14 du brief visait la coque courante, où la symétrie fabrique le couloir que toute la
refonte du 2026-08-29 a combattu. **Un événement n'est pas la coque** : il est vu une fois, il doit
se lire en une seconde, et c'est précisément la symétrie qui fait comprendre « GAUCHE + DROITE →
CENTRE » sans un mot de HUD (§4).

⚠️ **Ce que ça n'autorise pas** : le §7 reste vrai *dans le détail* — orientation des tourelles,
nombre de petites pièces, découpe des volumes secondaires. La **fonction** est en miroir, la
**finition** ne l'est pas. Un miroir au pixel près relèverait du copier-coller, pas de la
composition.

## T2 — L'ambre entre dans la palette — ✅ **`ADR-0043`**

> « je trouve que les lumières orange vont bien dans le décor telles des LED de signalement dans un
> env technologie, on pourrait même l'étendre au reste du long parcours »

Acté, et la teinte est **mesurée, pas choisie à l'œil** : `#FFA92B`, à **26,7° du corail `#FF5A3D`**
qui est le tir ennemi. Un « orange » posé au jugé atterrit à 10-20° du corail et lui volerait sa
lisibilité — la règle qui a déjà coûté une itération sur le bolide d'impact (`ADR-0027`).

Trois clauses de l'ADR gouvernent tout usage : écart de teinte ≥ 25° du corail ; **ponctuelle,
jamais surfacique** (au plus 3 % de l'aire) ; et elle **ne signale jamais une cible** — le magenta
dit « fonction, donc à détruire », l'ambre dit « repère technique ». L'extension au reste du Cortège
est validée **dans son principe**, à faire après que la citadelle l'ait montrée en jeu.

## T3 — La citadelle **se décale** vers la proue

> « oki décale »

Elle ne voisine plus `Spine_03` (s = 260,2). **Centre retenu : s ≈ 240**, dans la fenêtre libre de
C2 (236 → 254), ce qui laisse **20 m** entre le bord aval de la citadelle et le nœud d'épine — assez
pour que la respiration du §18 sépare les deux verrous au lieu de les faire se chevaucher.

⚠️ **Conséquence à ne pas perdre** : à s ≈ 240 la citadelle mange la respiration voulue « s 214 à
246 ». C'est assumé — un verrou EST une rupture de rythme — mais la respiration doit alors être
**rendue après**, ce que le LOT 5 porte déjà.

---

# Les demandes de texture — à générer **en parallèle** des lots

L'opérateur les produit pendant que le code avance (`ADR-0028` : la texture est la voie de
l'opérateur). Elles sont écrites, validées contre les six règles du contrat, et **ne bloquent ni le
LOT 1 ni le LOT 2** — la boucle et la silhouette se jouent en gris.

| Demande | Ce qu'elle sert | Requise pour |
|---|---|---|
| [`TEX-0015`](../forge/textures/TEX-0015-citadelle-bouclier-energie.json) — bouclier | le panneau d'énergie central, et la peau du noyau à une échelle plus serrée | **LOT 3** |
| [`TEX-0016`](../forge/textures/TEX-0016-cortege-signaletique-ambre.json) — signalétique ambre | les diodes de balisage `#FFA92B` d'`ADR-0043` | **LOT 3** |

⚠️ **DEUX, ET PAS SIX — c'est délibéré.** Le blindage de la citadelle, ses panneaux greffés et sa
machinerie sont servis par `TEX-0010`, `TEX-0011` et `TEX-0012`, déjà livrées et intégrées. Le brief
§1 demande de réutiliser au maximum, et §19 exige que la citadelle soit **identifiable par sa
géométrie même sans emissif** : si elle a besoin d'une texture pour se distinguer du bordé, c'est la
géométrie du LOT 2 qui a échoué, pas la carte qui manque.

**Pourquoi `TEX-0015` ne peut pas être `TEX-0013`** : l'artère est bâtie sur la règle inverse — « au
moins la moitié de l'aire SOMBRE », « pas d'aplat lumineux plein cadre » — parce qu'elle est un
conduit étroit. Un bouclier est une surface **tenue**. Réutiliser l'artère donnerait un mur de
canaux : un décor, pas une barrière.

**Et le noyau n'a pas sa carte** : il porte `TEX-0015` à une échelle UV plus serrée. Ses trois états
(protégé, surchargé, éteint) sont pilotés **par le moteur** — une carte par état ferait quatre
choses à maintenir et trois à oublier.

# Les lots — et l'ordre est imposé par le brief

> **« Ne pas passer du temps sur les greebles ou les effets tant que la boucle complète n'est pas
> jouable de bout en bout. »** C'est la consigne que l'opérateur a demandé de garder, et elle est la
> règle de production de ce plan. Chaque lot ci-dessous se termine par quelque chose de **jouable**.

## LOT 0 — ✅ **presque clos** : il ne reste que la cote verticale

T1, T2 et T3 sont **tranchées** (voir ci-dessus), et `ADR-0043` acte l'ambre. Reste **C1**, la seule
question à laquelle l'opérateur ne peut pas répondre sans un chiffre : les bastions demandés à
« +1,5 à +2,5 m » ne disposent que de **1,30 m** (décor) ou **1,90 m** (gameplay).

**Livrable** : la hauteur des bastions posée en chiffre, et la voie retenue parmi les trois de C1.
⚠️ **Ma recommandation : la voie (b), obtenir la hauteur par le CREUX.** Le lot B3 l'a déjà démontré
sur cette coque — quatre fosses de 1,55 m ont donné du relief là où le plafond interdisait de
monter, pour 384 triangles. Une citadelle dont la porte s'enfonce dans le pont lit **plus** fermée
qu'une qui dépasse de 1,30 m, et elle ne coûte aucun amendement d'`ADR-0041`.

## LOT 1 — La boucle, en cubes gris

**Aucune géométrie définitive, aucun effet.** Des boîtes grises aux bonnes places, et la machine à
états du §16 :

- `CitadelState` explicite — `APPROACH / LOCKED / ONE_RELAY / SHIELD_DOWN / CORE_DEAD / OPENING / CLEARED` ;
- deux relais destructibles **dans n'importe quel ordre**, un noyau invulnérable tant qu'ils vivent ;
- le passage bloqué par une `PlaneShape`, **retirée à `CLEARED`** ;
- `scroll_speed` piloté par l'état.

**Ce qui prouve le lot** : une partie se joue de bout en bout, dans les deux ordres de relais, et le
chasseur franchit le passage sans téléportation. ⚠️ **Et une partie où l'animation d'ouverture est
volontairement coupée doit rester jouable** (§11) — la route ne dépend jamais d'un visuel.

## LOT 2 — La silhouette

La géométrie dans `build_long_cortege.py` : bastions, porte, noyau, aux cotes du lot 0. Volumes
simples, extrusions, modules répétés — le kit avant le mesh dédié. **Ce qui prouve le lot** : le
test noir et blanc, émissifs coupés — on identifie bastion ≠ relais ≠ noyau ≠ passage **sans
couleur** (§19 : « identifiable par sa géométrie même sans emissif »).

## LOT 3 — Les quatre états se voient

Conduits magenta relais → bouclier, extinction d'un conduit, instabilité, surcharge, feux résiduels.
C'est le lot qui rend la règle compréhensible **sans HUD** (§5). **Ce qui prouve le lot** : une
capture par état, et un joueur qui n'a pas lu le plan sait quoi tirer.

## LOT 4 — L'ouverture (solution C)

Explosion du noyau, puis mécanismes latéraux qui écartent la voie. **Ce qui prouve le lot** : la
collision disparaît à l'`SolidsOverlay`, et la largeur de passage est mesurée, pas estimée.

## LOT 5 — La respiration, et la seconde moitié

§18 : quelques secondes sans grosse tourelle, citadelle visible derrière, retour progressif de la
musique. ⚠️ **La « seconde moitié plus machinique » du §18 n'est PAS dans ce plan** — c'est le
LOT 6 (décoration) de la refonte, déjà au backlog. Les deux se rejoindront ; les mélanger ferait
un chantier qu'on ne saurait plus finir.

---

# Test d'acceptation

Il reprend celui de `2026-08-29-niveau-2-refonte-geometrie.md` et lui ajoute la boucle :

1. **Noir et blanc, émissifs coupés** : bastion ≠ relais ≠ noyau ≠ passage, sans hésitation.
2. **Les deux ordres de relais** donnent la même ouverture.
3. **Le noyau ne perd pas un point de vie** tant qu'un relais vit, et l'impact se voit sur le bouclier.
4. **La collision tombe** : vérifié à `--show-solids`, largeur de passage **mesurée**.
5. **Animation coupée = route quand même praticable.**
6. **Les deux plafonds tiennent** (décor < −3,00, gameplay < −2,40), tests moteur verts.
7. **Sous 45 s** en partie normale, chronométré — ⚠️ le journal du survol **n'est pas horodaté**
   (dette connue au backlog) : soit on l'horodate d'abord, soit on chronomètre à la capture vidéo.
8. **Aucun marqueur des 30 n'a disparu ni changé de nom**, `build-hull.sh --check` déterministe.
9. **Budget triangles** : la coque est à 48 678 / 90 000 — la citadelle dispose de ~41 000, ventilé au rapport.
10. Et la règle qui prime : **une partie jouée** (`ADR-0006`).

---

# Ce que ce plan ne fait pas

- **Il ne crée pas de petite tourelle** : elle existe (lot A du 2026-09-03).
- **Il ne touche pas au boss ni à l'arc** : la citadelle est un verrou de niveau, pas une phase.
- **Il n'ajoute aucune barre de vie ni objectif au HUD** : la planche montre deux encarts
  explicatifs — ce sont des **légendes de planche**, pas du HUD. §4 : « ne pas afficher
  immédiatement dix objectifs différents ».
- **Il ne refait pas la coque** : découpage, scrolling, matériaux, UV, systèmes de tourelles et de
  baies sont conservés.
- **Il ne traite pas la direction artistique de la seconde moitié** (§18) — voir LOT 5.

# Ordre et dépendances

```
LOT 0  trancher            ← peut réécrire la silhouette du brief
  ↓
LOT 1  la boucle en cubes  ← JOUABLE de bout en bout, sans un seul effet
  ↓
LOT 2  la silhouette       ← dépend des cotes du lot 0
  ↓
LOT 3  les quatre états    ┐
LOT 4  l'ouverture         ┘ ← composent sur la géométrie du lot 2
  ↓
LOT 5  la respiration
```

⚠️ **Le lot 1 avant le lot 2 n'est pas un confort, c'est la consigne de l'opérateur** : une
citadelle magnifique dont le verrou ne s'ouvre pas est un échec complet, une boîte grise qui s'ouvre
correctement est un succès à habiller.
