# Niveau 2 — la Citadelle de Défense : un verrou de level design à mi-parcours

| | |
|---|---|
| **Date** | **2026-09-03** |
| **Auteur** | session Claude, sur le brief d'implémentation et la planche de l'opérateur |
| **Périmètre** | une séquence de 30 à 45 s au milieu du Long Cortège : une fortification transversale qui **ferme physiquement la route**, s'ouvre en sabotant deux relais puis un noyau, et rend le passage praticable |
| **État** | ✅ **LOT 0 clos, LOTS 1 à 4 livrés** (2026-09-04) — la boucle se joue de bout en bout, en boîtes grises. Reste le seul LOT 5 (la respiration), et **une partie jouée à la main** dont dépend tout le reste. Des deux textures livrées le 2026-09-04, `TEX-0015` (bouclier) est **acceptée** après rattrapage de tuilage et `TEX-0016` (ambre) **refusée** : ses diodes font 0,8 px à l'écran pour 3 à 5 exigés |
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

## C1 — ⛔ Le budget vertical est de **1,30 m**, le brief en demande **2,50** — ✅ **TRANCHÉ**

C'est le point qui décide de la silhouette, et il tombe avant tout le reste.
**Résolu le 2026-09-04 par la voie (b), la hauteur par le creux — voir le LOT 0 pour les cotes.**

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

# Les demandes de texture — livrées par l'opérateur le 2026-09-04

**Une acceptée, une refusée, et les deux verdicts sont chiffrés.** Aucune n'est nécessaire avant
le LOT 3 : le refus ne bloque rien.

L'opérateur les produit pendant que le code avance (`ADR-0028` : la texture est la voie de
l'opérateur). Elles **ne bloquent ni le LOT 1 ni le LOT 2** — la boucle et la silhouette se
jouent en gris.

| Demande | Ce qu'elle sert | Requise pour | État |
|---|---|---|---|
| [`TEX-0015`](../forge/textures/TEX-0015-citadelle-bouclier-energie.json) — bouclier | le panneau d'énergie central, et la peau du noyau à une échelle plus serrée | **LOT 3** | ✅ acceptée après rattrapage |
| [`TEX-0016`](../forge/textures/TEX-0016-cortege-signaletique-ambre.json) — signalétique ambre | les diodes de balisage `#FFA92B` d'`ADR-0043` | **LOT 3** | ⛔ refusée, à régénérer |

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


## ✅ `TEX-0015` — le bouclier : **ACCEPTÉE après rattrapage de tuilage**

Artistiquement juste, et ça se mesure : maille hexagonale à deux échelles (lattice de lignes
vives + grain cellulaire fin dans les alvéoles, ce que `main_elements` demandait mot pour mot),
teinte **310–320°** — magenta/rose —, **zéro cyan, zéro corail**, aucun vignettage (écart
coin/centre 0,018), aucun texte ni pictogramme, **59 %** de l'aire au-dessus de la mi-valeur pour
une cible de 40–60.

⚠️ **Mais le tuilage livré était REFUSÉ** : écart **11,5 % en X et 11,2 % en Y** pour un seuil de
4 % (règle 4 du contrat). Et **aucun recadrage ne le sauvait** — la meilleure tuile carrée
possible, cherchée sur toutes les tailles de 900 à 1254 px et **tous** les décalages, plafonnait à
5,0 % : le générateur n'a pas produit une image périodique, il a produit une belle image.

**Rattrapée par fondu miroir de 48 px puis rééchantillonnage en 1024** → **0,1 % sur les deux
axes**. Et la planche 2×2 a été **regardée** (`ADR-0006`) : la maille hexagonale absorbe le fondu,
aucune bande miroir visible. C'est exactement le cas que `derive-maps --fix-tiling` décrit —
« il sauve une image presque bonne ».

⚠️ **Et elle ne reçoit AUCUNE carte dérivée.** La demande listait
`citadel_shield_nrm/rough/ao` : c'était une erreur d'écriture, corrigée dans le JSON. `output_usage`
vaut `albedo_and_emission`, pas `source_for_normal` — dériver une normale d'une carte de **couleur**
donne des gradients faux **qui ont l'air corrects**, le défaut même que la règle 2 existe pour
empêcher ; et un champ translucide émissif n'a aucun relief à ombrer. Même traitement que
`cortege_emissive`.

Déposée en **`assets/source/textures/cortege/citadel_shield_1024.png`** — et **là seulement**.
⚠️ `assets/imported/` ne porte « rien qui ne soit chargé » (`assets/README.md`) : la copie runtime
y entrera au LOT 3, avec le matériau `AA_Shield_Field` qui la lit. Y déposer une carte que rien
n'ouvre ferait de ce dossier une réserve, et c'est exactement la frontière que cette règle tient.
Sa dernière recette est en jeu, écran chargé, tirs ennemis présents.

⚠️ **Conséquence à ne pas perdre** : le placeholder du LOT 1 est un bouclier **bleu**
(`#4DB8FF`) ; `TEX-0015` le rend **magenta**. Au LOT 3, bouclier et noyau seront donc de la même
famille de teinte, et c'est la **structure** qui devra les séparer — c'est ce que la demande
argumente, mais ça ne s'est encore vu sur aucune capture.

## ⛔ `TEX-0016` — la signalétique ambre : **REFUSÉE, et pas sur ce qu'on craignait**

Tout ce que la demande redoutait est tenu, et largement : tuilage **OK** (1,8 % / 1,5 %),
anthracite dominant, aucun cabochon coupé par un bord, aucun vignettage (écart 0,002), aucun
texte. La clause 2 d'`ADR-0043` plafonne l'ambre à **3 %** de l'aire : l'image en emploie
**0,031 %**, soit **cent fois moins que le budget**.

⚠️ **Et c'est là qu'elle échoue.** Les 18 taches ambre mesurent **9 px de large en médiane** sur
1254, soit **3,6 cm au monde** à 5 m/tuile — quand la demande veut 12 à 20 cm. À 23 px/m, un
cabochon fait **0,8 px à l'écran** pour les **3 à 5 px** exigés : sous-pixel, donc il scintille ou
il disparaît au filtrage. Et **aucune échelle UV ne rattrape ça** : il faudrait une tuile de
**16,7 m** pour amener la diode à 12 cm, ce qui donnerait des plaques de bordé de 6,6 m — plus
large que le pont intérieur (4,6 m) et que le pont médian (2,95 m).

**Ce qu'il faut demander à la régénération, en une phrase** : *les mêmes plaques, les mêmes
groupes, mais des cabochons trois fois plus gros* — le budget de 3 % laisse de quoi les grossir
**dix fois** avant de le toucher. La contrainte qui a bridé le générateur n'était pas la bonne :
c'est la borne **basse** de lisibilité qui décide ici, pas le plafond d'aire.

Non déposée : un asset qui ne peut pas se lire n'entre pas dans le dépôt.

# Les lots — et l'ordre est imposé par le brief

> **« Ne pas passer du temps sur les greebles ou les effets tant que la boucle complète n'est pas
> jouable de bout en bout. »** C'est la consigne que l'opérateur a demandé de garder, et elle est la
> règle de production de ce plan. Chaque lot ci-dessous se termine par quelque chose de **jouable**.

## LOT 0 — ✅ **CLOS** (2026-09-04) : la voie (b), et la cote est un chiffre

T1, T2 et T3 étaient tranchées ; `ADR-0043` actait l'ambre. Restait **C1**, la cote verticale.

**Tranché : la voie (b) — la hauteur se prend par le CREUX.** Une **douve de 1,55 m** est creusée
sous l'emprise de la citadelle. Ce n'est pas une profondeur neuve : c'est **exactement `PIT_DEPTH`**,
celle des quatre fosses du lot B3, déjà bâtie, déjà assertionnée sur cette coque. En inventer une
seconde aurait donné deux creux de profondeurs différentes sans qu'aucune raison ne les sépare.

Ce que la douve achète, en cotes :

| Pièce | Assise | Sommet | Hauteur bâtie | **Hauteur lue** depuis le fond de douve |
|---|---|---|---|---|
| Porte | −5,10 | **−3,00** (plafond décor) | 2,10 m | **2,85 m** |
| Bastion | −5,10 | −3,60 | 1,50 m | 2,25 m |
| Couronne | −3,60 | **−3,00** | 0,60 m | **2,85 m** |
| Relais | −4,30 (pont intérieur) | **−2,40** (plafond gameplay) | 1,90 m | 3,45 m |
| Noyau | −4,58 (fond de l'artère) | **−2,40** | 2,18 m | 3,73 m |

**Le brief demandait 1,5 à 2,5 m ; la lecture en donne 2,85.** On dépasse la demande sans toucher
`ADR-0041`, ce qu'aucune des deux autres issues ne permettait — (a) rabotait la silhouette, (c)
demandait d'amender un ADR et de démontrer que rien n'est masqué.

⚠️ **Et la hiérarchie tient dans une seule règle** : le seul volume autorisé à culminer à −2,40 est
celui qu'on peut **tirer**. Le noyau est donc le point le plus haut de la citadelle, 60 cm au-dessus
de la porte et des couronnes. C'est ce qui le désigne comme le centre **sans un mot de HUD**, et
`test_the_destructible_pieces_stay_under_the_gameplay_ceiling` le garde.

### ⚠️ Deux contraintes découvertes en posant les cotes, et qui appartiennent au LOT 2

1. **La fenêtre libre est sur une RAMPE, pas sur un plateau.** `TAPER` vaut 1,000 à `s = 236` et
   monte à 1,230 à `s = 258` — le grand élargissement du tronçon 3 commence *dans* l'emprise. La
   coque s'évase donc de +2 % à l'avant du verrou à +9 % à l'arrière. Le plan ne l'avait pas vu :
   il n'avait compté que les marqueurs et les fosses. **C'est assumé** — un verrou qui s'évase se
   lit comme un contrefort — mais le LOT 2 doit suivre `_side_scale(s, side)` comme tout le reste
   du fichier, et ne surtout pas poser des `x` absolus.
2. **La barrière déborde la coque, et il faudra la porter.** La coque fait 28 m ; le plan de vol,
   parallaxe appliquée, en couvre davantage. Une barrière arrêtée au bordé laisserait le joueur
   **contourner le verrou par le vide** — la séquence deviendrait facultative. La porte couvre donc
   **tout le plan** (|x| = 17,2 en monde, ±14,17 projeté). ⚠️ **Dû au LOT 2/3 : la partie qui
   déborde doit recevoir un PORTEUR VISIBLE** (portique, rideau de bouclier). Un mur invisible est
   la même injustice qu'une tourelle qu'on croit pouvoir raser et qui traverse.

## LOT 1 — La boucle, en cubes gris — ✅ **LIVRÉ (2026-09-04)**

**Aucune géométrie définitive, aucun effet.** Des boîtes grises aux bonnes places, et la machine à
états du §16 :

- `CitadelState` explicite — `APPROACH / LOCKED / ONE_RELAY / SHIELD_DOWN / CORE_DEAD / OPENING / CLEARED` ;
- deux relais destructibles **dans n'importe quel ordre**, un noyau invulnérable tant qu'ils vivent ;
- le passage bloqué par une `PlaneShape`, **retirée à `CLEARED`** ;
- `scroll_speed` piloté par l'état.

### Ce qui est livré

| | |
|---|---|
| `scripts/gameplay/cortege_citadel.gd` | la boucle, les sept états, la pose, le freinage, la forme solide |
| `scripts/gameplay/citadel_part.gd` | une pièce destructible **qui sait refuser** — le noyau rend les tirs sans perdre un point |
| `resources/data/cortege_tuning.gd` | dix réglages et **quatre invariants** (9 à 12) |
| `scripts/vfx/cortege_flyby.gd` | `travelled()` — voir « ce qui a coûté » |
| `tests/unit/test_cortege_citadel.gd` | 35 méthodes |

**La pose, mesurée :** face avant à `s = 240,0`, emprise `239,6 → 246,0`. Garde de la fosse de
`s = 228` finie à 236,2 (**3,4 m** de marge) ; socle de `Turret_07` commencé à 255,25 (**9,25 m**).
Le verrou s'immobilise à `travelled ≈ 256,1`, mur à `y = +4,0`, **arène de 12 unités**.
Relais à `(±5,0 ; 4,9)`, noyau à `(0 ; 6,5)`, quatre tourelles légères entre `y = 4,2` et `5,7` —
toutes dans le plan de vol **et** dans leur propre fenêtre de 14 unités.

**Le budget, tenu :** freinage 4,2 s (mesuré **5,0 s** en jeu — l'invariant estime avec la vitesse
de défilement, la vraie est celle du plan, 18 % plus lente : l'estimation est **optimiste**, donc
sûre pour un plafond), combat 22,8 s, ouverture 2,2 s, reprise 3,0 s → **32 s**, dans la fourchette
30–45 du brief.

### ⚠️ Cinq choses que le code a refusées, et ce qu'elles ont appris

1. **`global_position` ne répond QUE dans l'arbre de scène.** Hors de lui, le moteur rend
   l'identité et écrit une ligne au journal que personne ne lit dans une suite de 844 tests. La
   citadelle lisait sa position et celle de la caméra ainsi : **tous ses tests de pose passaient au
   vert sur une projection dégénérée**. Elle reçoit désormais `travelled` et l'œil — d'où
   `CortegeFlyby.travelled()`. C'est la même leçon que `CortegeSpineNode` avait déjà écrite ; elle
   a été repayée.
2. **Le banc lisait un œil à (0, 0, 0), et `aim_point_of` a un cas dégénéré documenté pour ça** :
   caméra dans le plan, le calcul « marche » et rend la position de la caméra — toutes les cibles au
   même endroit, sans erreur. Le test lit maintenant la caméra **de la scène du niveau**, en
   composant les transformations à la main, et **refuse un œil à moins d'une unité du plan**.
3. **Une tourelle légère ne tient pas sur la couronne.** À −3,00 son affût culmine à −2,15 et
   franchit le plafond du gameplay. Elle siège donc sur le pont du bastion à −3,60 (sommet −2,75,
   35 cm de marge), et **la couronne est bâtie ailleurs que sous les tourelles** — le même arbitrage
   que `build_long_cortege.py` fait déjà entre bastions et socles d'affût.
4. **Un relais abattu pendant le freinage figeait le mur deux unités trop haut.** Les relais
   deviennent tirables à l'instant précis où le freinage commence : quitter `APPROACH` faisait
   tomber la vitesse à zéro d'un coup, sur une porte que le joueur ne pouvait plus atteindre. Le
   mur va désormais jusqu'à sa station **quoi qu'il arrive aux relais** — c'est la géométrie qui
   dit quand il est en place, pas l'état du combat. Atteignable dès la première partie.
5. **`--cortege-from=4` gelait le survol pour toujours.** Un départ en aval pose le mur *derrière*
   le joueur : sa hauteur de plan est négative, donc la condition d'arrêt est vraie, et le verrou
   s'armait sur une porte qu'on ne peut plus ni voir ni tirer. Aucune erreur, aucun journal. Le
   verrou répute désormais la route franchie. Un outil de vérification qui gèle le jeu est pire que
   pas d'outil.

### ⚠️ Ce que la relecture a trouvé, et qui est corrigé (2026-09-04)

`godot-reviewer` a rendu **huit défauts, zéro bloquant**. Aucun n'aurait produit d'erreur ; six
n'auraient pas été vus en jouant. Tous sont fermés, chacun avec son garde.

| # | Le défaut | Ce qu'il coûtait |
|---|---|---|
| **1** | `level_duration()` ne comptait **que le défilement** | Le niveau se joue en 240 s et l'invariant en affirmait 208. Pire : la borne haute de l'invariant 9 autorisait un verrou qui rompait la promesse en restant **vert partout**. `level_duration()` compte désormais `citadel_sequence_time()`, `scroll_duration()` porte le défilement seul, et **`target_duration` passe de 210 à 240** — la promesse a changé parce que le contenu a changé |
| **2** | L'état `LOCKED` était **sautable**, précisément sur le chemin documenté comme normal | Un relais abattu pendant le freinage faisait passer `ONE_RELAY` avant que le mur soit en place : `LOCKED` n'était jamais traversé, la ligne horodatée « VERROU » ne s'imprimait pas — et le critère « sous 45 s » ne repose sur rien d'autre. Le mur annonce maintenant son arrivée par **son propre signal `wall_locked`**, quoi que fasse le combat. Mon test gravait le saut au lieu de le voir : il l'exige désormais |
| **3** | Les quatre tourelles du verrou **échappaient au nœud d'épine** | Le nœud du tronçon 2 éteint le tronçon 3, celui du verrou : les 21 batteries de coque faiblissaient, annoncées au bandeau, et les **seules** tourelles qui canardent le joueur pendant qu'il est immobile gardaient toute leur vigueur. C'est le trou de récompense exactement là où il se sent |
| **4** | L'inscription au gestionnaire de balles était **asymétrique** | Une pièce qui quittait le plan puis y rentrait restait éteinte **à vie** : cible inscrite, tir qui la traverse, **verrou inouvrable** — sans une ligne au journal. Et une pièce vivante hors plan restait inscrite deux minutes. Va-et-vient symétrique + passe monotone, comme la tourelle et le nœud |
| **5** | L'œil manquant devenait **(0, 0, 0) en silence** | C'est le cas dégénéré documenté d'`aim_point_of` : toutes les pièces se touchent ailleurs qu'où on les voit. Le banc le refusait, le runtime l'acceptait. `push_error` désormais |
| **6** | `reserve()` appelée à **chaque image physique** | Son contrat dit « une fois, au montage », et `size() + 1` faisait dépendre la capacité de l'**ordre** des fournisseurs. Retirée : `PlaneShapes._push()` dimensionne lui-même |
| **7** | La porte restait **dessinée** après `CLEARED` | Le fichier se prémunissait du mur invisible et livrait l'injustice miroir : 34 m de volume qui disent « fermé » pendant que le joueur les traverse. Escamotée — ce n'est pas l'ouverture du lot 4, c'est la version qui ne mente pas en attendant |
| **8** | `piece_world()` suppose le tronçon à `y = 0` — **vrai du `.glb`, faux de la doublure** | La doublure pose ses tronçons à −8 et ne porte aucun marqueur : le verrou y aurait dessiné ses boîtes huit mètres sous la dalle pendant que le mur solide arrêtait le joueur à sa hauteur nominale. **Un mur invisible qui bloque.** La citadelle ne se monte plus sans coque livrée — même règle que les trente marqueurs |

### Mesuré en jeu, sur Windows (`godot-verifier`, 4 lancements)

| | |
|---|---|
| **Verdict visuel** | **vert** — le verrou se voit sans ambiguïté, il s'immobilise, le mur couvre toute la largeur |
| **Coût GPU** | **3,90 ms/image** pendant le verrou, sur **Quadro T1000** (pas la RTX 4080) — 23 % du budget 60 Hz. La citadelle seule : **≈ 0,2 ms**, à peine au-dessus du bruit de mesure (0,16 ms), et c'est un **majorant** (la trame de référence porte trois chasseurs que celle du verrou n'a pas) |
| **Anomalies** | aucune — zéro `ERROR`, zéro `SCRIPT ERROR` sur les quatre lancements |

⚠️ **Deux choses vues à la capture, et regardées** (`ADR-0006`) :

1. **Le porte-à-faux est réel.** Le cœur du verrou est franchement planté — bastions, relais,
   noyau, tourelles s'appuient sur la coque — mais **les deux tiers extérieurs de la poutre
   surplombent le vide**, étoiles visibles dessous. C'est la conséquence directe de « fermer tout
   le plan », et c'est ce que le LOT 2 doit porter. Fonctionnellement juste, mais ça se lit comme
   une poutre en l'air.
2. **Les quatre tourelles sont peu lisibles** : gris sombre sur plinthe gris-brun, très petites,
   à la limite du repérable sans zoom. Relais, noyau et bouclier claquent ; elles, non. À traiter
   au LOT 2 (silhouette) plutôt qu'à coup de teinte.

### ⚠️ La partie de l'opérateur, 2026-09-04 — et elle a refusé le dimensionnement

Première partie jouée à la main sur le verrou. Le journal **horodaté** (ajouté au LOT 1) a servi
immédiatement :

| | | |
|---|---|---|
| +0,0 s | route fermée droit devant — freinage | |
| +5,0 s | **VERROU** — survol à l'arrêt | freinage **5,0 s** |
| +16,0 s | premier relais tombé | **11,0 s** |
| +37,5 s | second relais tombé | **21,5 s** — le double du premier |
| +52,9 s | noyau détruit | **15,4 s** |
| +55,1 s | route praticable | |

Zéro `SCRIPT ERROR`, zéro `ERROR`. Pools alloués **une seule fois** (14 + 209), musique 0→1→2→3
sans trou, **sept coques écrasées** pendant la séquence : les ponts d'envol produisent bien
pendant l'arrêt.

**Ce que l'opérateur a répondu, et qui décide du remède** : « **j'ai compris tout de suite** » —
donc aucune de ces 47,9 s n'est passée à chercher quoi tirer. Et l'arène de 12 unités : « **juste,
ça va** » — `citadel_wall_plane_y` ne bouge pas.

#### ⚠️ L'hypothèse était optimiste d'un facteur 2,4 — le même qu'`ADR-0024`, au même chiffre

3 800 PV tombés en **47,9 s** de combat quand `citadel_fight_time()` en promettait 22,8. Soit
**79 dps effectifs** sur les 420 de référence : l'occupation réelle du verrou est de **0,19**, pas
les **0,45** déclarés.

Et le fichier savait : il écrit, deux lignes au-dessus du réglage, que se dimensionner sur
l'occupation de la coque ouverte « reviendrait à se donner raison ». Puis il choisissait 0,45
**sans mesurer** — c'est-à-dire qu'il se donnait raison quand même. L'invariant se comparait à
lui-même, exactement comme le flux du Léviathan.

#### Ce que la mesure a changé

| | Avant | Après |
|---|---|---|
| `occupancy_citadel` | 0,45 (au jugé) | **0,19** (mesuré) |
| `citadel_relay_health` | 1200 | **800** |
| `citadel_core_health` | 1900 | **1100** |
| *durée du verrou* | 29 s promis / **55,1 s joués** | **41,1 s** |
| *durée du niveau* | 240 s | **252 s** |

⚠️ **Et un nombre inventé a été retiré.** L'invariant 9 bornait le temps de tir à « 30 s » — un
chiffre qui ne venait de nulle part, et qui **refusait le bon réglage** dès que l'occupation est
devenue honnête. Ce que le brief spécifie, lui, est la durée de la **séquence** : 30 à 45 s. Le
combat n'a donc plus qu'un **plancher** (un verrou qui tombe en quatre secondes n'est pas un
verrou) et son plafond se **déduit** du budget, freinage et ouverture retirés.

⚠️ **Le freinage mentait de 20 %, et le chronomètre l'a dit.** L'estimation employait la vitesse
de **défilement** là où le mur descend à la vitesse du **plan** : la caméra projette, et les deux
diffèrent de 18 %. Prédit 4,17 s, corrigé 5,06 s, **chronométré 5,0**. La première écriture
assumait l'écart en le déclarant « optimiste, donc sûr » — c'était vrai, et c'était quand même une
seconde d'erreur sur un budget de quarante-cinq. `PLANE_SPEED_RATIO` porte désormais le nombre, et
`test_the_projection_factor_still_matches_the_camera_of_the_level` le **mesure** contre la caméra
de la scène : une caméra reculée sans toucher ce réglage échoue.

#### Trois choses que cette partie apprend et qui ne sont pas des réglages

1. ✅ **La règle se lit SANS HUD, et déjà en boîtes grises.** « Gauche + droite → centre » a été
   compris sans un mot. C'est le critère d'acceptation du **LOT 3**, à moitié acquis avant que le
   LOT 3 n'existe — la symétrie de `T1` a fait ce qu'elle promettait.
2. ⚠️ **Le second relais a coûté le DOUBLE du premier** (21,5 s contre 11,0). Ce n'est pas de
   l'apprentissage — l'apprentissage rendrait le second plus rapide. C'est la traversée de l'arène
   sous le feu qui coûte, et c'est **là** que vit la difficulté de la séquence. À regarder au
   LOT 3 avant d'y toucher.
3. ⚠️ **Deux chemins restent non joués** : le **second ordre de relais** (tribord d'abord), et
   l'**affaiblissement par le nœud d'épine** du tronçon 2 — aucune ligne `nœud d'épine abattu`
   dans cette partie, donc les quatre tourelles du verrou n'ont jamais été vues diminuées.

### Ce que le lot laisse ouvert, et qui n'est pas un oubli

- ⚠️ **Le pilote automatique reste bloqué au verrou.** `--demo` tire droit devant : il n'abat pas
  les relais, donc le survol ne repart jamais. **`balance-prober` ne peut plus rendre une
  chronologie d'arc complète du niveau 2** — exactement le pendant du blocage de l'iris du Choir
  Harvester, déjà au backlog. Ce n'est pas un défaut du verrou, c'est le prix d'un verrou.
- **Les unités ne sont pas versées dans les solides du niveau 2.** `CombatRuntime.fill_solids()`
  rendrait solides les coques trop lourdes à écraser ; le niveau 1 le fait, le niveau 2 ne l'a
  jamais fait. L'ajouter changerait la collision de tout le survol — au backlog, à juger en jouant.
- **La teinte magenta des relais et du noyau est une béquille de lot 1.** Le LOT 2 doit les rendre
  identifiables **sans émissif**, et c'est le test d'acceptation.

### Ce qui prouve le lot

Vérifié en headless (`--goto-level=long_cortege --cortege-from=3 --demo`) : le verrou s'arme, freine
en **5,0 s**, s'immobilise, et le journal est **horodaté**. 847 tests verts, dont 35 sur ce lot.

✅ **Et il a été joué** — voir « La partie de l'opérateur » ci-dessus : la boucle se joue de bout
en bout, la règle se lit sans HUD, et le dimensionnement a été refusé par le chronomètre puis
recalé. Restent le **second ordre de relais** et le chemin du **nœud d'épine**.

⚠️ **Ce qui restait dû avant cette partie, et qui n'appartenait qu'à l'opérateur** (`ADR-0006`, `ADR-0019`) : une partie
jouée à la main, **dans les deux ordres de relais**, où le chasseur franchit le passage sans
téléportation — et une partie où l'animation d'ouverture est volontairement coupée doit rester
jouable (§11). La route ne dépend jamais d'un visuel : `test_the_route_opens_only_after_the_opening_has_run`
le garde, mais seul un humain dit si l'arène de 12 unités se **joue**.

## LOT 2 — La silhouette — ✅ **LIVRÉ (2026-09-04)**

La géométrie **dans un kit**, pas dans `build_long_cortege.py` — voir « le kit et non la coque »
ci-dessous. Volumes simples, extrusions, modules répétés. **Ce qui prouve le lot** : le test noir
et blanc, émissifs coupés — on identifie bastion ≠ relais ≠ noyau ≠ passage **sans couleur**
(§19 : « identifiable par sa géométrie même sans emissif »).

### ⚠️ Le kit et non la coque, et c'est la QUATRIÈME fois que cette raison se vérifie

Le plan écrivait « la géométrie dans `build_long_cortege.py` ». C'est faux, pour deux raisons dont
une est un chiffre :

1. **Mécanique.** Deux relais et un noyau sont **destructibles**, et la porte **s'ouvre** au
   LOT 4. Une pièce cuite dans le tronçon ne meurt pas sans emporter ses voisines — les cinq
   tronçons partagent un maillage et un jeu de matériaux. C'est mot pour mot la raison qui a sorti
   les hangars (`BRIEF-0091`), les affûts (`BRIEF-0093`) puis les nœuds d'épine (`BRIEF-0094`).
2. **Le plafond de construction.** `BUILD_CEILING_Y = −3,20` borne la coque, et
   `_assert_build_ceiling` a déjà **refusé la passerelle à −3,15**. Les cotes du LOT 0 montent à
   −3,00 et −2,40 : ce sont les deux plafonds d'`ADR-0041`, qui valent pour les pièces de kit et
   **non** pour le maillage de coque. Le kit rend les 20 cm que la coque interdirait.

### Ce qui est livré

`BRIEF-0096` → `citadel_kit.glb` : **huit pièces, 1 304 triangles** pour un budget de 3 000,
déterministe, UV et tangentes sur 8/8. Vérifié indépendamment du rapport de forge :
`AA_Emissive_Engine` est sur `citadel_relay` et `citadel_core` **et sur aucune autre pièce**,
`AA_Trim` à 0,7 % de l'aire, huit nœuds à la racine sans transformation ni enfant.

Comparaison qui a servi à fixer le budget : `turret_kit` 2 240 tris **instancié 38 fois**,
`bay_kit` 1 140 (**7 fois**), `spine_kit` 280 (**5 fois**). La citadelle est instanciée **une
seule fois** : elle peut être la pièce la plus riche du vaisseau.

### Les quatre signatures, et pourquoi aucun autre axe n'était libre

Trois familles occupaient déjà l'espace des formes sur cette coque — le hangar **creuse**
(négatif, horizontal, rectangulaire), l'affût **dépasse** (positif, horizontal, trapu), le nœud
d'épine est **vertical, effilé, oblique**. Une quatrième famille ne peut pas se poser sur leurs
axes sans tomber du côté de l'une d'elles. D'où :

| Pièce | Signature | Mesuré |
|---|---|---|
| la porte | **la LONGUEUR** — rien d'autre ne traverse le cadre | 34,40 m pour 1,20 d'épaisseur, **28,7 : 1**, denture de 4,80 m au centre |
| le bastion | **la MASSE ÉTAGÉE** — le seul volume à deux niveaux | 4,50 large pour 2,90 haut, plus une couronne. Refusé par harnais s'il s'inverse |
| le relais | **le BRANCHEMENT** — un fût, un collier, un caisson vers l'axe | rapport 1,19, collier débordant de 0,18 |
| le noyau | **la RÉVOLUTION** — le seul tambour, et le point le plus haut | constance de rayon 1,0000 contre 1,2939 pour le relais |

⚠️ **Le conduit est la pièce la plus importante du lot**, et ce n'est pas le plus gros volume :
c'est lui qui dit « ceci alimente cela » **en géométrie**, donc sans émissif, donc au test noir et
blanc. Le couple relais/noyau est **le plus serré des quatre**, et il a fallu une correction
*après avoir regardé* : le capot du relais portait `AA_Trim` comme celui du noyau, et les deux se
présentaient alors comme « un volume sombre coiffé d'une tache claire ». Capot passé en sombre.

### ⚠️ La forge a corrigé deux de mes chiffres, et elle avait raison

- **Le portique va à `x` 13,58 et non 15,60.** Le tableau du brief et sa propre page
  « porte-à-faux » se contredisaient : la lisse d'épaule (13,88) est **en dedans** de l'emprise
  que j'avais donnée. Arrêté à 15,60, le portique **flotte** — le défaut qu'il existe pour
  corriger. Morsure mesurée contre le profil réel, taper compris : 0,19 à 0,56 m.
- **Le conduit culmine à +0,62 et non +0,35.** La peau monte de 0,28 m entre le pied du relais et
  le rebord de l'artère : un caisson de 0,35 m y serait enterré aux quatre cinquièmes, là
  précisément où il doit se lire.

### ⚠️ Un défaut latent trouvé en chemin, qui touche les TROIS kits précédents

L'importateur glTF pose `rotation_mode = 'QUATERNION'` : `obj.rotation_euler` y est rangé mais
**jamais lu**, sans un mot. `build_spine_kit._place()`, `build_turret_kit._place()` et
`build_bay_kit._import()` écrivent la même ligne — **l'azimut des affûts et le miroir des
entretoises d'épine n'ont donc jamais été rendus dans leurs planches de recette**. Trois recettes
ont été validées sur des images incomplètes. Le jeu, lui, n'est pas touché : il construit ses
propres nœuds Godot. Corrigé dans `build_citadel_kit.py`, au backlog pour les trois autres.

### La couronne a chassé une tourelle, et c'est une bonne chose

`citadel_crown` occupe `s +1,60 → +5,40` sur le pont du bastion, où siégeaient mes deux tourelles
de garde. Le socle léger fait **1,04 m de rayon** : les deux ne peuvent pas tenir en avant d'elle
(il faudrait `s ≤ 0,56`) et le bastion est trop court pour en loger une derrière. La seconde
descend donc sur le **pont intérieur**, à `x ±4,60 · s +3,30`, **0,42 m derrière le conduit** —
posée devant, son socle se serait couché sur le caisson. Deux ponts au lieu d'un empilement, ce
qui vaut mieux en composition, et `test_a_guard_turret_seated_on_the_bastion...` vérifie désormais
**les deux assises** : n'en garder qu'une laisserait l'autre franchir le plafond en silence.

### ⚠️ Vérifié en jeu — et la capture a trouvé ce que 850 tests verts ne voyaient pas

| | |
|---|---|
| **Verdict visuel** | **vert** après un correctif. Le verrou lit beaucoup mieux qu'en boîtes : la poutre traverse tout le cadre avec sa denture au centre, les bastions nervurés sont la pièce la plus lisible du kit, le noyau et son bouclier tiennent l'axe, et les deux tourelles hautes se détachent sur le noir de l'ouverture |
| **Coût GPU** | **3,79 ms/image** sur Quadro T1000 (22,7 % du budget 60 Hz) contre **3,90 ms** en boîtes grises. Les 1 304 triangles du kit sont **gratuits**, sous le bruit de mesure |
| **Anomalies** | aucune — zéro `ERROR`, zéro `pièce de kit manquante` |

#### ⛔ Les deux relais étaient à des dizaines de mètres de leur place

En cherchant les deux relais sur la capture je n'en ai trouvé **qu'un**, au bord droit du cadre,
posé au-dessus du vide.

La forge cuit le **X de coque dans la géométrie** — le relais est modelé à `x` 5,40 → 7,00 — et le
miroir se fait par un **yaw de π**, pas par un signe. Or le nœud de la pièce se plaçait *lui aussi*
à ±6,20, parce que c'est de là que se déduit sa hitbox. Les deux écarts s'additionnaient :

- tribord partait à `x ≈ 11,60` — au large du bastion, en l'air ;
- bâbord, faute de yaw, revenait se poser **sur l'axe**, derrière le noyau.

⚠️ **ET AUCUNE MOITIÉ PRISE SÉPARÉMENT N'ÉTAIT FAUSSE.** La position du nœud était juste, la boîte
du maillage était juste, le centrage en Z était juste — c'est leur **composition** qui ne l'était
pas. Trois tests gardaient le kit, dont un sur le centrage en Z **écrit précisément pour attraper
les défauts de miroir**, et il passait : il gardait *une* moitié.
`test_the_two_relays_land_where_the_kit_says` refait désormais la chaîne complète — nœud × forme ×
boîte — exactement comme le moteur, et vérifie que chaque relais atterrit sur l'emprise mesurée
par la forge. Corrigé et **re-vérifié en capture** : les deux boîtes de lampe tombent à **1 pixel**
du miroir exact l'une de l'autre.

C'est très exactement ce que `ADR-0006` existe pour dire.

#### Trois réserves, laissées aux lots suivants

1. **La denture se lit comme un créneau de rempart, pas comme un joint de battants.** Elle est
   posée sur le dessus de la poutre, dents vers le haut, **sans mâchoire en vis-à-vis** : l'œil y
   voit un peigne. Il manque le vantail — pas de tableau, pas de ligne de refend, pas deux
   moitiés. Le LOT 4 l'ouvrira, mais **la lecture manque déjà**.
2. **Le portique a des jambes, et elles sont dans le noir.** Deux piliers descendent bien dans la
   tranchée centrale, mais dans un noir quasi pur : la poutre paraît flotter quand même, et ses
   deux bouts dépassent la silhouette de la coque d'environ 250 px de chaque côté.
3. ~~**Le pied des bastions n'a plus d'embase**~~ — ✅ **corrigé le 2026-09-04 par la tranchée**,
   que l'opérateur a tranchée contre le collier. Voir « La tranchée est creusée » plus bas.

### ✅ La tranchée est creusée (2026-09-04), et c'est l'opérateur qui a tranché

Deux tranchées **latérales**, une par bastion : pont médian, `x` 7,35 → 10,30, fond à **−6,50**,
`s` 239,2 → 246,4 — 40 cm de jeu à chaque bout, sans quoi la jupe toucherait les parois et le
creux disparaîtrait.

| | |
|---|---|
| **Triangles** | **+272** sur toute la coque (47 254 → 47 526). Section 3 à **52,9 %** de son budget |
| **Points de profil** | **zéro** — `7,35` et `10,30` sont déjà les points 9 et 10 de `PROFILE_BASE` |
| **Déterminisme** | OK (`9f4e0715`) |
| **Coque calme** | 52,2 % → **50,8 %** |
| **Coût GPU** | 3,93 ms/image sur Quadro T1000, **23,5 %** du budget |

⚠️ **LES 50,8 % SONT LA MARGE LA PLUS MINCE QUE CE VAISSEAU AIT EUE.** Le lot C1 de
l'enrichissement a *refusé* trois bastions parce qu'ils ramenaient le calme **sous les 50,3 %**
d'où le lot B4 était parti. La tranchée coûte 1,4 point et nous laisse **0,5 point** au-dessus de
ce plancher. Toute dépense de bordé future doit être pesée contre ce chiffre.

Et une partie de cette dépense est un **gain de justesse** : le compte de calme **voit désormais
le verrou**. Les pièces de la citadelle sont un kit, donc invisibles au fichier de coque — mais la
tranchée qui l'assied (239,2 → 246,4) recouvre son emprise (239,6 → 246,0). La compter, c'est le
compter. Sans ça, le chiffre surestimait de six mètres le bordé le plus chargé du vaisseau, ce
qui est exactement le défaut que le commentaire de cette fonction décrit.

#### Un mécanisme, pas deux

Six endroits du fichier interrogent les creux — la peau qui saute ses cellules, les modules qui
les évitent, les stations qui pavent leur emprise, le tracé, et deux harnais. Les six passent
désormais par un seul générateur `_hollows()` : **un creux sans son saut de peau est un plancher
sous une peau intacte**, invisible et définitif. Les quatre fosses restent byte-identiques.

La différence entre les deux familles est écrite dans le code : une **fosse** se creuse *sous la
peau* (profondeur relative, le fond suit le bord) ; une **tranchée** porte un *fond absolu*, parce
que le moteur y assied une pièce de kit à une cote écrite. Faire dériver le fond ferait flotter le
bastion sans un mot.

#### ⚠️ Trois fichiers écrivent la même cote, et aucun ne peut lire les deux autres

`CortegeCitadel.BASTION_BASE_Y` dit où le moteur **pose**. `MOAT_FLOOR_Y` dit où la coque
**creuse**. Entre les deux il y a un `.glb` qui seul fait foi. Le harnais Blender ne lit pas le
GDScript ; le moteur ne relit pas le Python. Si les deux nombres divergent, le bastion flotte ou
s'enterre — sans erreur, sans test rouge, et sans que la capture le montre franchement puisque la
jupe est arrondie.

`test_the_bastion_sits_exactly_on_the_trench_the_hull_digs` ferme la boucle par le **seul élément
commun** : il scanne les sommets de `Section_03` dans l'emprise de la tranchée et exige que leur
point le plus bas soit exactement l'assise du bastion. Plus `_assert_moats_are_hollow()`, qui
refuse une tranchée creusant moins de 1,40 m si la peau bougeait.

#### Ce que la capture montre

Le défaut est **corrigé**. Profil de luminance au travers du bord aval du socle gauche :
`68 → 42` (gorge) `→ 79 · 80 · 91 · 104` (chanfrein éclairé) `→ 42` (ombre de contact) `→ 68`
(pont) — contraste adjacent 2,5:1. C'est la lecture qu'on attend d'un socle, et la jupe se lit
maintenant en silhouette sur toute la hauteur du bastion.

⚠️ **Mais le socle TRIBORD est moins crédible que le bâbord**, et ce n'est pas la géométrie : la
lumière-clé vient du haut-gauche, donc le bord droit ne reçoit **aucun rasant**. Son chanfrein ne
se détache presque plus du pont (68 contre 56) et seule l'ombre de contact (38) porte la lecture.
Ça tient, mais par l'ombre seule. ⚠️ Et le constat vaut pour **tout ce qui est à tribord sur les
500 m** du vaisseau, pas seulement ici : c'est la conséquence d'une seule directionnelle.

**La bande non tranchée passe.** Le bastion va de 6,90 à 11,40 et la tranchée de 7,35 à 10,30 :
les 1,10 m au large se lisent comme un **tablier d'appui** à faible contraste, les 45 cm en dedans
sont noyés dans la fente d'ombre de l'axe. **Aucun artefact de bord** — ni raie d'ombre à la
limite `x = 10,30`, ni extrémité de tranchée ouverte : la silhouette du socle se referme sur
elle-même.

## LOT 3 — Les quatre états se voient — ✅ **LIVRÉ (2026-09-04)**

Conduits magenta relais → noyau, extinction d'un conduit, instabilité, surcharge, feux résiduels.
C'est le lot qui rend la règle compréhensible **sans HUD** (§5). **Ce qui prouve le lot** : une
capture par état, et un joueur qui n'a pas lu le plan sait quoi tirer.

### Ce que chaque état donne à voir

| État | Ce qui change à l'écran |
|---|---|
| verrou intact | **deux** conduits alimentent le noyau, bouclier à pleine énergie, noyau qui bat lentement |
| un relais tombé | **son** conduit s'éteint, et le bouclier perd **la moitié** de son énergie |
| bouclier à terre | le panneau disparaît, le noyau bat vite et fort — « maintenant, ça compte » |
| noyau mort | surcharge, puis feux résiduels pendant l'ouverture |

⚠️ **Le bouclier qui faiblit est le seul des quatre à rendre la CAUSE visible**, et il ne coûte
qu'une division. Couper un relais ne fait pas seulement disparaître un relais : ça affaiblit
visiblement ce qu'il alimentait. Sans lui, le joueur voit deux morts sans conséquence, puis un
bouclier qui tombe d'un coup — et il n'apprend le lien qu'après.

### Deux réutilisations plutôt que deux inventions

**Les conduits sont des `FlowLink`**, l'outil écrit pour le porteur de bouclier — et son en-tête
dit exactement pourquoi : « pas de trait grossier comme ça […] plutôt un effet de particule »
(opérateur, en jouant). Un trait plein est du carton : il ne dit ni sens, ni mouvement, ni
intensité. Et surtout il s'était fait **lire à l'envers** — « on me ralentit » là où le lien
disait « c'est lui qui les tient ». Ici les points partent du **relais** vers le **noyau** :
*ceci alimente cela*, donc *coupe les deux côtés d'abord*.

⚠️ **Le sens ne se vérifie qu'en jouant** : une capture ne montre pas un mouvement. C'est la seule
chose de ce lot qui reste due, et elle est due à l'opérateur.

**Les feux résiduels sont des explosions du banc commun**, poolées, avec un tirage **semé** : un
aléa libre rendrait deux captures incomparables — la leçon des arcs du nœud d'épine.

### ⚠️ Trois réglages posés au jugé, tous les trois corrigés en regardant

1. **Les conduits lisaient comme des lampions.** À 0,75 de large, les points faisaient 20 à 27 px
   — quatre à six fois le seuil que je craignais. Le problème était l'**inverse** de celui que
   j'anticipais, et sa cause était ailleurs : `FlowLink.DOTS_PER_UNIT` est réglée sur les liens du
   porteur, qui font des dizaines de mètres. Un conduit en fait 6,4 → **trois points**. Deux
   lumières, pas une circulation. Corrigé sur les deux axes — largeur **0,55**, densité **1,4/m**
   → cinq billes nettes séparées par un vide visible. `FlowLink.aim()` a gagné un paramètre de
   densité **au défaut inchangé**, pour ne pas dérégler par la bande deux signes déjà validés.
2. **Le panneau cramait.** Émission blanche à 1,35 plus le `glow` : une dalle blanche lisse.
   Ramenée à **0,75**, la dalle est passée de blanche à **rose**.
3. **Et les trois sont désormais bornés des DEUX côtés**, ce qu'ils n'étaient pas : largeur 0,55
   est juste (à 25 % du pic la bille couvre 51 px pour un pas de 30) ; densité 1,4 est le
   **plafond** et non le milieu — à 1,6 le pas tomberait à 26 px, égal à la largeur de bille, et
   on retrouverait le trait plein ; énergie 0,75 ne doit pas descendre, le rouge est encore
   écrêté sur 48 % et baisser ternirait sans rien révéler.

### ⛔ La maille du bouclier ne se voit pas — et ce n'est ni la carte, ni l'UV, ni les mipmaps

C'est le résultat le plus utile du lot, parce qu'il dépasse la citadelle.

`TEX-0015` est câblée, et la chaîne est **juste à 1 % près** : pas de maille mesuré à **28,4 px**
à l'écran pour 28,6 prédits, échelle UV vérifiée jusque dans les texels de la carte. Un défaut
d'import a bien été trouvé et corrigé au passage — `mipmaps/generate=false`, le défaut de Godot,
qui écrasait 1 106 texels dans 152 px sans filtrage : **plancher de bruit du spectre divisé par
deux** une fois activées. Mais elles ont **nettoyé** le crénelage, pas révélé le motif.

La cause est **en aval**, et elle est chiffrée :

| Maillon | Mesuré |
|---|---|
| `retro_post` accroche l'image à `target_res` | **960 × 540** — le panneau de 152 px n'en fait plus que 76 |
| `levels = 20.0` postérise | pas de **12,75 niveaux** ; le panneau ne contient QUE 204 / 217 / 229 / 242 / 255 |
| la maille module de | **0,83 niveau** — un quinzième d'une marche |
| le canal rouge | saturé sur **52 %** du panneau, **deux valeurs en tout** |

⚠️ **Un détail dont la modulation est sous ~6 niveaux de gris n'existe pas dans ce jeu.** Le
tramage de Bayer le porte encore *statistiquement* — c'est pourquoi il se **mesure** au spectre —
mais l'œil ne le voit pas, et aucun réglage n'y change rien. La leçon est remontée au **contrat de
texture** (`docs/forge/textures/README.md`) : `readability_requirements` doit raisonner en
**contraste**, pas seulement en pixels. « 9 à 18 px par maille » était vrai et **insuffisant** — la
maille en faisait 29 et ne se voyait pas.

La carte est **conservée** : elle donne sa teinte et son grain au panneau, les mipmaps sont un gain
net, et l'échelle redeviendra utile le jour où l'ouverture du LOT 4 élargira le panneau.

### Un drapeau de vérification, parce que le critère l'exigeait

`--citadel-state=<0..3>` amène le verrou à l'état voulu **au moment où il s'immobilise**, et il
tire **pour de vrai**, par `hit_callback`. Un raccourci qui poserait les drapeaux à la main
capturerait un état que le jeu ne produit pas — un bouclier éteint sans que son relais soit mort,
un noyau vulnérable sans passer par `SHIELD_DOWN`. Sans lui, « une capture par état » était
inatteignable : le pilote automatique tire droit devant, il n'abat pas un relais. Même esprit que
`--leviathan-phase=2`, dont l'absence avait coûté trois lancements.

### Ce que les captures ont dit, et ce qui reste

**L'asymétrie de l'état 1 saute aux yeux** sans comparer deux images : l'anneau du relais bâbord
s'éteint (luminance 104 → 39, pic 255 → 76) et son conduit disparaît, tandis que tribord garde le
sien. **La séparation par la structure tient** : le panneau lit comme un volume plat devant une
coupole ronde, et les tirs ennemis ne posent aucun problème — ils sont **orange**, pas magenta.

⚠️ **L'affaiblissement du panneau ne se lit pas seul** : 203 → 188 de luminance, essentiellement
une perte de vert. Il confirme le signal porté par l'anneau, il ne le porte pas. Pour qu'une
moitié d'énergie perdue se lise par elle-même, il faudrait le dire en **géométrie** — demi-hauteur,
moitié de maille manquante — et non en intensité. À juger si le besoin s'en fait sentir en jouant.

**Coût GPU** : **3,92 ms/image** sur Quadro T1000, 23 % du budget. Tripler la densité des billes
n'a rien coûté de mesurable. ⚠️ Et une leçon de méthode confirmée trois fois : **le premier
lancement après un déploiement lit 0,2 à 0,8 ms trop haut** — cache de shaders froid. Prendre une
médiane, jamais un tir.

## LOT 4 — L'ouverture (solution C) — ✅ **LIVRÉ (2026-09-04)**

Explosion du noyau, puis mécanismes latéraux qui écartent la voie. **Ce qui prouve le lot** : la
collision disparaît à l'`SolidsOverlay`, et la largeur de passage est **mesurée**, pas estimée.

### Le mécanisme — deux vantaux qui se rétractent dans deux logements

`citadel_gate`, la poutre d'un seul tenant, est **remplacée** par `citadel_leaf` (miroité) et
`citadel_housing` (`BRIEF-0097`). La chaîne de cotes devait tenir **trois choses en même temps**,
et c'est elle qui a décidé du mécanisme :

| | fermé | ouvert |
|---|---|---|
| vantail | `x` 0 → 12,90 | `x` **4,25 → 17,15** |
| recouvrement vantail/logement | **+0,20 m** — aucun jour | +4,45 |
| marge sous le bout de la poutre (17,20) | +4,30 | **+0,05** |
| passe | nulle | **8,50 m** de coque, soit **7,00 unités de plan** |

⚠️ **Toute variante qui fait GLISSER les vantaux vers l'extérieur allonge le porte-à-faux** que le
LOT 2 venait de corriger. La rétraction dans un fourreau est la seule forme qui garde le bout
extérieur à `x = 17,20` — donc qui continue de couvrir tout le plan de vol, décision du LOT 1 —
tout en dégageant un centre mesurable.

⚠️ **Et le sommet du logement est la cote qui pouvait tout casser en silence.** Un fourreau est
plus grand que ce qu'il reçoit ; s'il gagnait sa garde par le haut depuis la même assise, il
franchirait le plafond du décor inerte. Il part donc de **−6,90** pour culminer à **−3,00
exactement**, comme le vantail.

**La passe fait quatre fois la largeur du chasseur, et c'est mesuré** : son corps réel fait
**1,76 unité** en travers (`body_radius = 0,88`, `ADR-0034`). La chambre du réacteur a payé
l'inverse — « c'est comme si tout le cercle était un mur pour moi ».

### ⚠️ La forge a REFUSÉ une de mes cotes, avec une démonstration

Une denture qui se **recouvre vraiment** est arithmétiquement impossible sous ces cotes, et elle
l'a prouvé au lieu de l'appliquer en silence. Soit `a(s)` l'abscisse la plus interne de la matière
tribord dans la bande `s` : le miroir par yaw de π fait qu'à bâbord la matière occupe `x ≤ −a(−s)`,
donc « aucun jour » ⟺ `a(s) + a(−s) ≤ 0`. Avec une saillie `p`, cela force **`a ≤ −p/2`** — le
vantail devrait franchir l'axe de la moitié de sa saillie, donc manger la passe et sortir de
l'emprise déclarée. Une saillie lisible demandait `p ≥ 0,50` : passe à 8,00 et emprise fausse de
25 cm.

Elle a **tenu les cotes** et fait le joint **à tenon et mortaise** : face de butée pleine à
`x = 0`, la dent d'un vantail ferme la mortaise de l'autre. Son argument, et il tient : à 20° de
la verticale, **un tenon qui entre et un tenon qui s'arrête devant donnent la même image** — ce
qui se lit est l'alternance et son changement de phase en franchissant l'axe.

**Trois dents par vantail, et le compte impair est IMPOSÉ par le miroir** : le yaw envoie la bande
`k` sur `5 − k`, donc {0, 2, 4} → {5, 3, 1}, complémentaire exact. Un compte pair mettrait une
dent en face d'une dent. Et une **gorge de refend** de 0,14 m au milieu, ajoutée **après le
premier tirage** où la mâchoire se lisait comme un seul bloc clair — `ADR-0006` a encore payé.

### Vérifié indépendamment : les six pièces conservées sont intactes

Le compte de triangles et la boîte englobante ne prouvent rien — on déplace un sommet sans changer
ni l'un ni l'autre. J'ai donc récupéré l'ancien binaire depuis LFS et haché, **nœud par nœud, les
octets de chaque accesseur** (positions, normales, UV, tangentes, indices) plus le nom de matériau
de chaque primitive. Les six sont **byte-identiques**. Kit à **1 348 triangles** (+44) pour un
plafond de 2 300.

### La collision disparaît, et c'est mesuré à l'overlay

| | plages de l'overlay |
|---|---|
| fermé | **une seule** plage continue, colonnes 125 → 1795 — les deux capsules se touchent, aucun jour |
| mi-course | **deux** plages, 107 → 902 et 1019 → 1814 : **795 px chacune** contre ≈835 fermées, et un trou central de **117 px** symétrique |
| ouvert | **0 pixel d'overlay sur l'image entière** — aucune capsule résiduelle, ni au centre ni ailleurs |

Les capsules sont donc **raccourcies** (−40 px) *et* reculées (−18 px) : ce n'est pas une simple
translation. La passe s'élargit réellement pendant l'ouverture, et
`test_the_passage_widens_while_the_leaves_retract` garde qu'elle ne se referme jamais en cours de
route.

⚠️ **À `CLEARED`, plus rien — alors que les vantaux sont toujours là**, et c'est délibéré. Un
vantail resté solide pendant que la coque reprend son défilement **pousserait** un joueur resté au
large, sur toute la largeur du plan : c'est exactement le défaut pour lequel `PlaneCollider` a été
écrit — « je fonce tout droit et mon vaisseau est bloqué » — et on ne va pas le recréer pour la
rigueur d'une barrière qu'on vient d'ouvrir.

**Coût GPU** : **3,93 ms** médiane sur quatre tirs à l'état 0, contre 3,92 avant — **dérive
nulle**. Porte ouverte : 3,68 ms, un peu moins.

### ⚠️ La réserve du LOT 2 est levée — mais l'ouverture, elle, ne se lit pas encore

**La porte fermée se lit comme une porte.** Au zoom sur le joint : deux mâchoires en vis-à-vis,
trois bandes claires par vantail **décalées verticalement** l'une par rapport à l'autre, et une
ligne verticale sombre franche au centre exact. L'œil voit deux moitiés et sait où ça s'ouvrira.
⚠️ *Cette lecture-là a été vérifiée au zoom par le vérificateur, pas par moi à pleine image : à
distance de jeu la denture n'est qu'un petit motif rayé, et c'est sa **position** — au centre du
couloir — qui porte l'information.*

⛔ **Et l'ouverture ne se lit pas, pour une raison de TON et non de géométrie.** Regardé à pleine
image : la poutre paraît continue. Les vantaux rétractés, la poutre fixe et la coque vue **à
travers** la passe partagent le même gris ; le seul endroit où l'ouverture se voit est là où la
**tranchée sombre de l'artère** apparaît au travers. Le seul autre indice à vitesse de jeu est le
départ du bloc denté vers la droite.

⚠️ **Et le vantail bâbord n'est JAMAIS lisible** — ni à mi-course, ni ouvert : son bout intérieur
se lit comme une tranche plate, alors que la collision prouve qu'il a bougé symétriquement. C'est
le même défaut que les socles de bastion : **une seule directionnelle venant du haut-gauche**, donc
aucun rasant à tribord — et ici c'est bâbord qui perd, parce que c'est la face opposée qui compte.

**Ce qui manquerait est un SEUIL**, et il a déjà un nom : `TEX-0016`, la signalétique ambre
refusée, demande « quelques doubles points marquant **un seuil** ». Un marquage au sol dans la
passe dirait « voici par où » là où la valeur ne le dit pas. La carte est à régénérer — elle a
maintenant un emploi précis qui l'attend.

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
