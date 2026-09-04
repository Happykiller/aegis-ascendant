# Niveau 2 — la Citadelle de Défense : un verrou de level design à mi-parcours

| | |
|---|---|
| **Date** | **2026-09-03** |
| **Auteur** | session Claude, sur le brief d'implémentation et la planche de l'opérateur |
| **Périmètre** | une séquence de 30 à 45 s au milieu du Long Cortège : une fortification transversale qui **ferme physiquement la route**, s'ouvre en sabotant deux relais puis un noyau, et rend le passage praticable |
| **État** | ✅ **LOT 0 clos et LOT 1 livré** (2026-09-04) — la boucle se joue de bout en bout, en boîtes grises. Reste le LOT 2 (silhouette), 3 (les quatre états), 4 (l'ouverture), 5 (la respiration), et **une partie jouée à la main** dont dépend tout le reste. Des deux textures livrées le 2026-09-04, `TEX-0015` (bouclier) est **acceptée** après rattrapage de tuilage et `TEX-0016` (ambre) **refusée** : ses diodes font 0,8 px à l'écran pour 3 à 5 exigés |
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
