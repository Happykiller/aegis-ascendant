# BRIEF-0084 — Réparer `inset_panel()`, régénérer toutes les coques : compte-rendu

*Mesuré le 2026-08-25, Blender 4.5.11 LTS, `blender45 -t 1 -b`. **Verdict : LIVRÉ**, avec **un défaut
sur deux requalifié** (§2), **un troisième défaut découvert en corrigeant** (§3), **un garde-fou de
script relevé et chiffré** (§6) et **un critère d'acceptation non tenu, de cause pré-existante**
(§9.1).*

| Critère du brief | | Mesure |
|---|---|---|
| Les deux défauts reproduits et mesurés par moi | ✅ | §1 et §2, cas minimal de 16 quads |
| Correctif dans `aegis_kit.py`, idempotent | ✅ | `core_interior.glb` et `leech_drone.glb` **byte-identiques** |
| Toutes les coques régénérées | ✅ | 12/12 |
| Aucune au-dessus de son plafond ADR-0011 | ✅ | la plus chargée : `pale_leviathan` à 78 % de son contrat, 35 % du plafond de classe |
| Diff du contrat de noms vide, coque par coque | ✅ | 12/12 diffs vides, §5 |
| UV sur 100 % des primitives, partout | ❌ | 9 coques sur 12 ; `needle_scout`, `crescent_interceptor`, `choir_harvester` n'ont **jamais** eu d'UV — §9.1 |
| Déterminisme, trois exécutions | ✅ | 12/12, §7 |
| Planche avant/après regardée | ✅ | §8 — relief visible, **aucune silhouette ne bouge**, bbox identiques au 1/10 de mm |
| `core_interior` non régénéré à la hausse | ✅ | 19 414 triangles, sha256 **inchangé** |
| `./scripts/check.sh` | ✅ | *ALL GREEN* — 413 tests, 1 891 assertions, 0 échec (les 10 `.glb` modifiés se réimportent) |

---

## 1. Défaut 1 — la normale nulle : **CONFIRMÉ**, et il ne creusait rien du tout

Cas minimal, reproduit avant toute correction : 16 quads de 1 m **contigus**, bâtis par
`bm.faces.new()` comme le fait tout le kit, passés tels quels à `ak.inset_panel(…, thickness=0,10,
depth=−0,05)`.

| | normales laissées telles quelles (kit du dépôt) | après `normal_update()` |
|---|---|---|
| normale des faces à l'appel | `(0.0, 0.0, 0.0)` | `(0.0, 0.0, 1.0)` |
| **aire totale du liseré rendu** | **0,000000 m²** | **1,744132 m²** |
| creux réellement obtenu (min z) | **0,000000 m** | **−0,050000 m** |
| triangles avant → après `ak.cleanup()` | 64 → **32** | 64 → **64** |

La dernière ligne est le cœur du défaut : l'opérateur crée bien 16 faces de bordure, mais **d'aire
nulle** — ses sommets sont confondus avec ceux d'origine. `ak.cleanup()` (`remove_doubles`, 1e-5) les
ressoude à l'export, et il ne reste que l'affectation de matériau. **Un panneau qui se voit et qui
n'existe pas** : la description de la session bestiaire est exacte, y compris l'ordre de grandeur.

Ce que le dépôt subissait, mesuré appel par appel en instrumentant `ak.inset_panel` sur les 12
scripts (aucune modification, simple espion) :

| Script | appels | faces passées | **faces à normale NULLE à l'appel** |
|---|---|---|---|
| `build_specter_9.py` | 62 | 798 | **166** |
| `build_null_maw.py` | 10 | 250 | **75** |
| `build_pale_leviathan.py` | 276 | 444 | **72** |
| `build_choir_mine.py` | 23 | 115 | **67** |
| `build_crescent_interceptor.py` | 25 | 66 | **24** |
| `build_choir_harvester.py` | 33 | 254 | **21** |
| `build_aegis_citadel.py` | 730 | 2 026 | **12** |
| `build_needle_scout.py` | 5 | 30 | **6** |
| `build_citadel_turret.py` | 20 | 20 | **1** |
| `build_citadel_beacon.py` | 4 | 4 | **1** |
| `build_leech_drone.py` | 31 | 31 | 0 (le script met à jour) |
| `build_core_interior.py` | 45 | 543 | 0 (le script met à jour) |

⚠️ **Le tableau du brief compte les appels ; celui-ci compte les faces effectivement perdues.** Les
deux ne coïncident pas : la plupart des appels d'une coque tombent *après* qu'un premier
`inset_region` a validé les normales de son voisinage, et ceux-là fonctionnaient. Ce ne sont donc pas
« 15 insets morts sur le Specter-9 » mais **166 faces sur 798** — un cinquième du détail promis, et
toujours le premier de chaque zone, c'est-à-dire le plus visible.

Deux exemples nommés, tous deux entièrement inertes jusqu'à aujourd'hui :

- `build_aegis_citadel.py:1192-1195` — le plancher de la baie d'appontage. Le commentaire du script
  décrit *« une gorge, pas une dalle »*, et prévient même qu'il a fallu retourner la boucle pour que
  l'inset creuse au lieu de soulever. La face avait une normale nulle : **rien n'a jamais été
  creusé**. La rampe se rendait comme un aplat bleu. Vignette `aegis_citadel` de la planche zoom.
- `build_specter_9.py:1283` — le puits de verrière, 160 faces, *« bordure dorée, cuve sombre »*.
  Inerte : la cuve n'était que du matériau anthracite peint à plat.

## 2. Défaut 2 — la région : **le comportement est confirmé, sa qualification de défaut ne l'est pas**

Le comportement est réel et je le mesure sur le même cas minimal :

| 16 quads contigus, un seul appel | faces de liseré | aire de liseré | îlots de liseré | triangles |
|---|---|---|---|---|
| `inset_region` sur la liste entière | 16 (le pourtour de la grille) | 1,744132 m² | **1** | 64 |
| une plaque par face (lots sans arête commune, 2 lots) | **64** | **6,439875 m²** | 16 | **160** |

**3,7 × plus de liseré, 2,5 × plus de triangles.** BRIEF-0082 a raison sur toute la ligne, et son
correctif (découper en lots sans arête commune) est le bon.

**Mais la généralisation ne tient pas, et c'est le résultat le plus important de ce brief.** J'ai
compté, pour chaque appel du dépôt, le nombre d'îlots connexes parmi les faces passées : c'est
exactement le nombre de liserés que l'opérateur produira.

| Script | faces | îlots | ce que le code dit vouloir |
|---|---|---|---|
| `build_aegis_citadel.py:474` | 1 282 | 509 | *« chaque plaque est un `inset_panel` appliqué à une poignée de bandes consécutives (1 à 3) »* |
| `build_choir_harvester.py:674` | 120 | 6 | *« plaques de carapace : couronne (6 secteurs) »* — 20 cellules par plaque |
| `build_null_maw.py:500` | 250 | 10 | *« trois plaques violettes ENFONCÉES sur le dessus, séparées par des joints »* — 25 cellules par plaque |
| `build_specter_9.py:1283` | 160 | 1 | *« puits de verrière : bordure dorée, cuve sombre »* |
| `build_specter_9.py:1289` | 48 | 1 | *« sillon dorsal creusé, du nez à la verrière »* |
| `build_pale_leviathan.py:1087` | 64 | 8 | plaque = 2 bandes × 4 colonnes |
| `build_core_interior.py:350` | 543 | **543** | 240 plaques de pont — **le seul appelant qui veut une plaque par face** |

Dans **onze scripts sur douze**, la sémantique de région est exactement celle que le code demande, en
toutes lettres, dans son commentaire. Basculer `inset_panel()` en « une plaque par face » par défaut
n'aurait corrigé personne : cela aurait **redessiné** la carapace du Harvester (6 plaques → 120), les
pétales du Null Maw (10 → 250), les 509 plaques de la citadelle (→ 1 282), et transformé le puits de
verrière du Specter-9 en gaufrier de 160 alvéoles. Le brief interdit précisément cela (« ce chantier
répare un outil, il ne redessine rien »).

**Conclusion : le défaut 2 n'est pas un défaut du kit, c'est une sémantique qui n'était ni nommée ni
sélectionnable** — et qui était donc un piège pour qui voulait l'autre geste. C'est ce que le
correctif règle : les deux gestes existent, portent deux noms, et le mauvais ne peut plus être obtenu
par inadvertance (§4).

**Conséquence chiffrée directe : le +57 % redouté par le brief n'a jamais lieu.** La coque la plus
touchée prend +10,7 % (`choir_mine`), le héros +1,2 %, la citadelle +0,3 %. Le budget n'est le
risque n°2 que si l'on force la sémantique per-face partout ; §6 donne les vrais chiffres.

## 3. Défaut 3, découvert **en corrigeant**, et il aurait été livré sans le test

Première version du correctif : mettre à jour les normales **face par face**
(`BMFace.normal_update()` sur les seules faces passées) plutôt que globalement — moins cher, aucun
effet de bord. Un test de non-régression sur le cas minimal a rendu *« idempotent : False »* :

| grille 16 quads, `depth = −0,05` | `bm.normal_update()` global | `face.normal_update()` ciblé |
|---|---|---|
| les 16 sommets de la bordure | z = −0,050 | z = −0,050 |
| **les 9 sommets INTÉRIEURS de la région** | **z = −0,050** | **z = 0,000** ❌ |

`inset_region` déplace les sommets intérieurs d'une région le long de leur **normale de sommet**, que
seul `bm.normal_update()` calcule : une mise à jour ciblée laisse le fond du panneau **voilé** au
lieu d'être plat, avec la même topologie, le même compte de triangles et le même contrat vert. Le
défaut est aussi silencieux que les deux précédents. Le kit fait donc l'appel global, et le docstring
consigne la mesure.

Coût mesuré du global : `aegis_citadel` fait **730 appels** sur un maillage de 60 k triangles et se
construit toujours en **4 s** (2 s de modélisation). Le calcul n'a jamais été le problème.

Ce défaut est la raison pour laquelle les chiffres de ce rapport ne sont pas ceux de ma première
passe : `choir_mine` 6 376 → **6 232**, `null_maw` 6 990 → **6 830**, `specter_9` 35 464 → **35 412**
(un fond plat produit moins d'arêtes vives à biseauter que le même fond voilé).

## 4. Le correctif retenu — dans le kit, et il oblige à choisir

`tools/blender/lib/aegis_kit.py`, version passée de `1.0.0` à `1.1.0`. Trois changements, aucun
autre :

1. **`inset_panel()` appelle `bm.normal_update()` avant l'opérateur.** Juste par défaut, sans que
   personne ait à le savoir. Idempotent : un script qui l'appelle déjà obtient exactement la même
   géométrie qu'avant — **vérifié à l'octet** (§5, `core_interior` et `leech_drone` sont
   byte-identiques).
2. **`inset_panel(..., per_face=True)`** découpe la liste en lots sans arête commune et insette lot
   par lot (l'algorithme de BRIEF-0082, glouton et déterministe, `_edge_disjoint_lots()`).
   Propriété qui compte : une liste **déjà** sans arête commune rend **un seul lot égal à
   l'entrée, dans le même ordre** — donc les deux chemins donnent le même `.glb` à l'octet près
   quand ils sont équivalents. Vérifié.
3. **`inset_panels()`** (pluriel), alias lisible de `per_face=True`. Le pluriel est là pour qu'il
   faille **choisir** : deux gestes, deux noms, et le docstring dit lequel se trompe en silence.

Le docstring porte désormais les trois pièges avec leurs mesures — c'est le seul endroit où le
prochain auteur les lira au moment où ça compte, c'est-à-dire quand il tape `ak.inset_`.

Ce que je n'ai **pas** fait, volontairement : convertir un seul appel existant en `per_face=True`.
Le seul appelant qui veut ce geste, `build_core_interior.py`, le fait déjà dans sa fonction `_inset()`
locale ; le remplacer par `ak.inset_panels()` donnerait le même fichier (même algorithme, même
ordre) mais changerait un fichier que le brief demande de laisser tranquille. **Suggestion §10.1.**

## 5. Coque par coque — triangles, contrat de noms, UV, sha256

Contrat de noms comparé sur le `.glb` livré, pas sur le script : nom, **parent**, et **position monde
composée** de chaque nœud (maillage et point d'attache), triés. Les comptes de triangles et de
sommets sont exclus de la comparaison — ce sont eux qui doivent bouger. **Les 12 diffs sont vides.**

| coque | tris avant → après | Δ | plafond (source) | occupation | maillages / attaches comparés | diff noms | UV | bbox |
|---|---|---|---|---|---|---|---|---|
| `specter_9` | 35 008 → **35 412** | +404 (+1,2 %) | 60 000 (ADR-0011 héros) | 59 % | 7 / 10 | **vide** | 29/29 | identique |
| `aegis_citadel` | 62 712 → **62 884** | +172 (+0,3 %) | 120 000 (ADR-0011 structure) | 52 % | 1 / 17 | **vide** | 7/7 | identique |
| `pale_leviathan` | 30 122 → **31 236** | +1 114 (+3,7 %) | 40 000 (ADR-0018 ; classe : 90 000) | 78 % | 35 / 14 | **vide** | 170/170 | identique |
| `choir_harvester` | 18 666 → **18 748** | +82 (+0,4 %) | 25 000 (script ; classe : 90 000) | 75 % | 16 / 6 | **vide** | **0/61** ⚠️ | identique |
| `core_interior` | 19 414 → **19 414** | **0** | 22 000 (BRIEF-0082) | 88 % | 12 / 2 | **vide** | 49/49 | identique |
| `null_maw` | 6 630 → **6 830** | +200 (+3,0 %) | 7 000 (script ; classe : 12 000) | **98 %** | 7 / 1 | **vide** | 36/36 | identique |
| `choir_mine` | 5 632 → **6 232** | +600 (+10,7 %) | **7 000** (script **relevé**, §6) | 89 % | 7 / 1 | **vide** | 33/33 | identique |
| `leech_drone` | 3 888 → **3 888** | **0** | 4 000 (script ; classe : 12 000) | 97 % | 4 / 2 | **vide** | 22/22 | identique |
| `crescent_interceptor` | 2 665 → **2 911** | +246 (+9,2 %) | 3 000 (script ; classe : 12 000) | **97 %** | 1 / 4 | **vide** | **0/7** ⚠️ | identique |
| `citadel_turret` | 2 596 → **2 616** | +20 (+0,8 %) | 3 000 (script) | 87 % | 1 / 4 | **vide** | 7/7 | identique |
| `citadel_beacon` | 1 852 → **1 884** | +32 (+1,7 %) | 2 000 (script) | 94 % | 1 / 4 | **vide** | 7/7 | identique |
| `needle_scout` | 1 612 → **1 716** | +104 (+6,5 %) | 3 000 (script) | 57 % | 1 / 2 | **vide** | **0/7** ⚠️ | identique |

**Bounding box et pivot : identiques au 1/10 de millimètre sur les 12 coques** (relevés composés
nœud par nœud sur le `.glb`) — c'est la preuve chiffrée qu'aucune silhouette ne bouge : un inset à
`depth < 0` ne fait que creuser sous la peau existante.

`core_interior` et `leech_drone` sont **byte-identiques** au dépôt (`95d6876f…`, `f812c5d1…`) : ce
sont les deux scripts qui appelaient déjà `bm.normal_update()`, et c'est la preuve d'idempotence
demandée par le brief.

| coque | sha256 du `.glb` livré | octets |
|---|---|---|
| `specter_9` | `14aba06deb8ebcfbcd2337791d62368d5b7c6217a2558a6b8866dc8cf9f7a9ed` | 2 325 476 |
| `aegis_citadel` | `d6d4aed65756e72b301499cfa0491dce9f3b3c1d5e7427f933a44bb04309e83b` | 4 540 568 |
| `pale_leviathan` | `dcf723474f21f59308bb5bd66b9d60e701fa284983349060db27bce787b99c86` | 2 517 960 |
| `choir_harvester` | `93cb5288df4b6ead09516d43ad680b6c55ac7a0305385051ae8a195076abb515` | 805 440 |
| `core_interior` | `95d6876f8cccf1dc5e76b467731e525af54d2fbdc4ec4f2058703412359be7a8` | 1 231 112 *(inchangé)* |
| `null_maw` | `accb596fa048e49996b7fdb9d8636bffc1dd9bdc469008912971ea9cf2b35bd7` | 444 484 |
| `choir_mine` | `eac2f025c84bd61662a582cc18e7947cf2304ac84bf3441ab95e3c0a6f6a4d4d` | 422 528 |
| `leech_drone` | `f812c5d12c166a3d149ef0a129184e560cfccf01751907e4909dbb537e1af754` | 330 804 *(inchangé)* |
| `crescent_interceptor` | `32a3f00369488ce93592d8bb9a0ebff862e38d90d4de856dcbcf9df91da51b80` | 74 332 |
| `citadel_turret` | `0e15a984289b5ea359044e2cd84cbe897876e5f579288c6bfedd682afd417f0e` | 182 336 |
| `citadel_beacon` | `756cb44429009b72d943313a633086a0614b8935c065bc96c5faf0aa29089385` | 152 648 |
| `needle_scout` | `678f78830bc362bbdf6a17039dba66cfa65ff796addd95808c7c73afebf9be72` | 52 052 |

### Répartition des matériaux (en triangles, écarts ≥ 0,3 point)

Le liseré créé par l'inset conserve le matériau de la face d'origine (le plus souvent `AA_Hull`) :
la part de coque monte donc mécaniquement, celle du fond enfoncé baisse d'autant. **En aire, l'écart
est bien plus faible** — un liseré de 6 à 40 mm couvre peu.

| coque | ce qui bouge |
|---|---|
| `choir_mine` | Greeble 50,4 → 47,8, Hull 13,0 → 17,4, Emissive 17,3 → 15,7, Panel 8,6 → 6,5, Trim 6,7 → 8,4 |
| `crescent_interceptor` | Hull 52,5 → 56,5, Greeble 25,1 → 23,1, Emissive 8,0 → 7,3 |
| `null_maw` | Hull 12,9 → 17,0, Greeble 35,0 → 34,0, Panel 13,7 → 11,8, Trim 26,1 → 25,3, Emissive 10,0 → 9,7 |
| `needle_scout` | Hull 41,3 → 44,2, Emissive 21,0 → 19,8 |
| `pale_leviathan` | Hull 31,9 → 32,7, Trim 21,5 → 22,6, Panel 17,4 → 16,4, **Emissive 8,5 → 8,2** |
| `specter_9` (Trim 7,9 → 8,4), `citadel_turret`, `citadel_beacon` | ≤ 0,6 point |
| `aegis_citadel`, `choir_harvester` | rien ne bouge de plus de 0,3 point |

À noter : la part émissive du Pale Leviathan, connue comme au-dessus de sa cible (8,5 % pour 8 %),
**descend** à 8,2 %. Aucun matériau requis ne disparaît (le contrat l'aurait refusé).

## 6. Budgets — un seul dépassement, et je n'ai rien retiré

**Aucune coque n'approche son plafond de classe ADR-0011.** Le seul mur rencontré est un garde-fou
que les scripts se posent à eux-mêmes, bien en dessous :

> `build_choir_mine.py` : `tri_budget = 6_000`, commenté *« moitié du plafond ennemi léger
> d'ADR-0011 »*. La mine mesure **6 232** triangles une fois ses panneaux réellement creusés.
> `export_hull()` a refusé d'écrire le `.glb` — le garde-fou a fonctionné.

Conformément au brief (« ne la mutile pas »), **je n'ai retiré aucun détail**. J'ai relevé le
garde-fou de **6 000 à 7 000**, avec sa justification écrite dans le script : le plafond normatif de
la classe est **12 000** (ADR-0011), 7 000 en représente 58 %, et la mine reste sous garde-fou avec
768 triangles de marge. C'est le **seul** script de coque modifié par ce brief, et la seule ligne de
code qui y change.

⚠️ **Trois coques sont désormais à moins de 5 % de leur garde-fou de script** : `null_maw` 6 830 /
7 000 (98 %), `crescent_interceptor` 2 911 / 3 000 (97 %), `leech_drone` 3 888 / 4 000 (97 %). Aucune
n'est à plus de 57 % du plafond ADR-0011 de sa classe. **Le prochain détail ajouté à l'une d'elles
butera sur un chiffre qui n'a pas de justification mesurée**, pas sur une contrainte de rendu — c'est
la suggestion §10.2.

## 7. Déterminisme — trois exécutions, 12 coques

`blender45 -t 1 -b` (le `-t 1` d'ADR-0003/`build-hull.sh` : sans lui les tangentes divergent).
Protocole : sha256 du fichier livré, puis deux reconstructions complètes, sha256 après chacune.

**12 coques sur 12 : trois sha256 identiques.** Les valeurs sont celles du tableau §5. Temps de
reconstruction complets : de 1 s (`citadel_beacon`) à 19 s (`pale_leviathan`), 4 s pour
`aegis_citadel` — l'appel global à `normal_update()` ne coûte rien de mesurable.

## 8. Les planches — ce qu'elles montrent, et la mesure qui va avec

| Fichier | Contenu |
|---|---|
| `docs/forge/output/BRIEF-0084-revue-avant-apres.png` | 2048 × 3252 — **12 coques, avant et après**, vue d'ensemble |
| `docs/forge/output/BRIEF-0084-revue-zoom-avant-apres.png` | 2048 × 3252 — mêmes 24 vues, **recadrées 1:1** là où la différence est la plus dense |

Les deux planches : **caméra de jeu** (20° de la verticale, fov 62°, la base réelle de
`graybox.tscn` que reprend `tools/render-hull.py`), **fond noir** (`#070A12`, le fond de l'espace du
jeu), Cycles CPU 48 échantillons, 1024². Chaque vignette est étiquetée `nom AVANT|APRES n tris` ;
cadre rouge = avant, cadre cyan = après. **Le cadrage est calculé sur l'AVANT et réimposé à
l'APRÈS** : les deux images d'une paire sont strictement superposables.

⚠️ **La seconde planche n'est pas un confort, c'est la leçon de BRIEF-0082** (« il a fallu recadrer
un coin de la planche pour s'en apercevoir »). À taille de planche, une coque plaquée et une coque
lisse se ressemblent. La fenêtre de recadrage n'est pas choisie à l'œil : c'est la fenêtre 512 × 512
qui **maximise le nombre de pixels changés**, trouvée par image intégrale sur la différence.

Mesure de la différence, sur le masque du sujet (fond exclu), seuil 2/255 en luminance :

| coque | pixels changés | delta moyen | ce qu'on voit dans la vignette recadrée |
|---|---|---|---|
| `choir_mine` | 5,58 % | 0,0061 | chaque plaque dorsale gagne un fond enfoncé et un joint clair — la « carapace segmentée » que le script décrivait sans la produire |
| `crescent_interceptor` | 4,83 % | 0,0049 | le grand aplat violet devient un panneau enfoncé dans un cadre anthracite biseauté |
| `pale_leviathan` | 3,85 % | 0,0038 | les plaques de coque prennent une épaisseur : bord éclairé, fond décalé |
| `null_maw` | 1,26 % | 0,0014 | les joints des pétales deviennent des rainures réelles |
| `specter_9` | 0,82 % | 0,0015 | le puits de verrière existe : liseré or, cuve creusée |
| `choir_harvester` | 0,69 % | 0,0004 | liserés de carapace |
| `aegis_citadel` | 0,59 % | 0,0011 | **la baie d'appontage** : l'aplat bleu devient une gorge entre deux margelles |
| `needle_scout` | 0,51 % | 0,0004 | rainures de nez |
| `citadel_beacon` | 0,35 % | 0,0004 | capot |
| `citadel_turret` | 0,15 % | 0,0004 | jonc du dôme |
| `core_interior` | **0,00 %** | **0,0000** | fichier identique — la vignette prouve l'idempotence |
| `leech_drone` | **0,00 %** | **0,0000** | idem |

Les deux lignes à 0,00 % valident aussi la chaîne de mesure : deux rendus Cycles du même fichier ne
produisent **aucun** pixel de bruit, donc tout ce qui est mesuré ailleurs est de la géométrie.

**Silhouettes : aucune ne change**, ni à l'œil sur la planche d'ensemble, ni à la mesure (bounding
box et pivot identiques au 1/10 de mm, §5).

## 9. Réserves

### 9.1 ⚠️ Critère « UV sur 100 % des primitives » : NON TENU, et la cause est antérieure

Trois coques n'ont **aucune** UV ni tangente dans le `.glb` — ni avant ce brief, ni après :

| coque | primitives avec `TEXCOORD_0` | cause |
|---|---|---|
| `choir_harvester` | **0 / 61** | `build_choir_harvester.py` n'appelle jamais `ak.box_project_uv()` |
| `crescent_interceptor` | **0 / 7** | idem |
| `needle_scout` | **0 / 7** | idem |

Ce n'est pas une régression : `export_hull()` exporte les texcoords, mais un maillage sans calque UV
n'en a aucune à exporter. Les neuf autres coques sont à 100 %.

**Ça n'est pas anodin en jeu** : `codex_screen.gd:231` et `enemy_vitals` appliquent `HullDetail` à
toute coque non-forteresse ; sans UV, la feuille de détail (albédo × normale × rugosité × AO) est
échantillonnée en un seul texel — le relief peint n'apparaît pas et la teinte est multipliée par une
constante arbitraire.

**Correctif connu, une ligne par script**, à poser juste avant l'export, comme les neuf autres :
`ak.box_project_uv(obj, TEXELS_PER_METER)` avec 4,0 pour les deux chasseurs (valeur du Specter-9 et
de la mine, coques de 1 à 2 m) et ~0,55 pour le Harvester (7 m ; valeur du décor de noyau).
**Je ne l'ai pas appliqué** : cela change le rendu en jeu de trois coques que ce brief n'a pas
mandaté de retoucher, et le choix du tuilage est une décision de rendu, pas une réparation d'outil.
À arbitrer — §10.3.

### 9.2 Le CSV de provenance était déjà légèrement décalé

Avant toute intervention de ma part, deux lignes ne correspondaient plus au fichier du dépôt :
`aegis_citadel` annonçait 86 388 sommets (mesuré : 86 412) et `choir_harvester` 27 256 (mesuré :
27 286). Les triangles, eux, étaient justes partout. Les valeurs du §10 sont **mesurées sur les
fichiers livrés**, définition « somme des accesseurs POSITION de toutes les primitives » — celle qui
reproduit exactement le chiffre du Specter-9 déjà au CSV.

### 9.3 Ce que je n'ai pas vérifié

- **Aucune coque n'a été vue en jeu** (ADR-0006 : rendu Cycles à l'angle de la caméra de jeu, pas
  Godot). `./scripts/check.sh` est vert, donc les 10 `.glb` modifiés se réimportent sans erreur, mais
  la confirmation visuelle en jeu reste à faire à l'intégration.
- **Les pièces mobiles n'ont pas été rejouées.** Les harnais de dégagement de
  `build_pale_leviathan.py` (marges volet/coquille, orbite × course) tournent à chaque build et n'ont
  pas échoué — c'est le seul contrôle de collision qui ait été exercé. Les insets creusent **vers
  l'intérieur** de la matière, donc ils ne peuvent qu'augmenter les marges, mais je ne l'ai pas
  mesuré pièce à pièce.
- **`tools/blender/test_moving_parts.py`** n'a pas été lancé (hors périmètre du brief, non demandé).

## 10. Suggestions

1. **Remplacer le `_inset()` local de `build_core_interior.py` par `ak.inset_panels()`.** Même
   algorithme, même ordre, donc **même `.glb` à l'octet** — je l'ai vérifié sur le cas minimal. C'est
   la seule copie locale du geste qui reste dans le dépôt, et la laisser là garantit qu'elle
   divergera. À faire dans un commit séparé, avec vérification de sha256.
2. **Trois garde-fous de script à 97-98 % n'ont aucune justification mesurée** (`null_maw` 7 000,
   `crescent_interceptor` 3 000, `leech_drone` 4 000, contre 12 000 au plafond de classe). Le
   prochain brief qui touche à ces coques les percutera. Soit on les relève à la moitié du plafond de
   classe (6 000), soit on écrit dans chaque script *pourquoi* ce chiffre-là — la deuxième option est
   la doctrine du dépôt.
3. **Les trois coques sans UV (§9.1)** méritent un micro-brief : une ligne par script, un rendu de
   contrôle en jeu, et l'ADR-0011 est enfin tenu partout.
4. **`inset_panel` ne devrait plus jamais être appelé sans que l'auteur ait vu son docstring.** Si
   l'on veut aller plus loin que ce brief, la version « impossible à se tromper » consisterait à
   rendre le choix **obligatoire** dès que la liste contient deux faces adjacentes (paramètre sans
   défaut, `ContractError` sinon). C'est une modification de 20 sites d'appel : elle mérite sa
   propre décision, pas une décision de forge.

---

## 11. Lignes de provenance à recaler — **le CSV n'a PAS été touché**

Consigne respectée : `assets/licenses/ASSET_PROVENANCE.csv` est **inchangé** (un seul écrivain).

Les lignes concernées font 700 à 7 700 caractères de `notes` ; les recopier entières ici serait à la
fois illisible et un excellent moyen d'y introduire une faute. Voici donc, ligne par ligne, **les
substitutions exactes à opérer** — toutes les valeurs sont mesurées sur le fichier livré.

Pour **les dix coques régénérées**, dans les trois colonnes suivantes :

- `generated_date` → **2026-08-25**
- `modified_by` → **asset-forge (Claude)**
- `prompt_file` → **inchangé** (il documente la conception de la coque ; ce brief ne la conçoit pas)

Dans `notes`, les substitutions numériques :

| ligne CSV | asset_id | remplacer | par |
|---|---|---|---|
| 93 | `specter_9_hull` | `35008 triangles` · `43039 sommets` · `sha256 fe6658b0b0b2ae07a37b970cda6632377b958b9e8a148a357a9b13d5dd3e404f (2306012 o)` | `35412 triangles` · `43394 sommets` · `sha256 14aba06deb8ebcfbcd2337791d62368d5b7c6217a2558a6b8866dc8cf9f7a9ed (2325476 o)` |
| 94 | `needle_scout_hull` | `1612 triangles` · `1409 sommets` | `1716 triangles` · `1471 sommets` |
| 95 | `aegis_citadel_hull` | `62712 triangles` · `86388 sommets` | `62884 triangles` · `86528 sommets` |
| 96 | `citadel_turret` | `2596 triangles` · `3266 sommets` | `2616 triangles` · `3293 sommets` |
| 97 | `citadel_beacon` | `1852 triangles` · `2722 sommets` | `1884 triangles` · `2767 sommets` |
| 98 | `choir_harvester_hull` | `18666 triangles` · `27256 sommets` · `803816 o` · `sha256 a3d88d00d207392653c9984e38bb051575e992bf8d9dc51c706c10010e6394c8` | `18748 triangles` · `27333 sommets` · `805440 o` · `sha256 93cb5288df4b6ead09516d43ad680b6c55ac7a0305385051ae8a195076abb515` |
| 99 | `pale_leviathan_hull` | `30122 triangles` et `44403 sommets` (**les mentions de 27 710 / 27 756 sont l'historique BRIEF-0041/0083 : les laisser**) · `sha256 8c8112a8723a118dfe47de0d2ccf13f83eac6a66d0b32c73bb1122841190bad2` | `31236 triangles` · `45318 sommets` · `sha256 dcf723474f21f59308bb5bd66b9d60e701fa284983349060db27bce787b99c86` |
| 120 | `crescent_interceptor_hull` | `2665 triangles` · `1955 sommets` · `sha256 2b908fd2e8c6ae88ed09ade77f5c0be7c330667d209ed62e57a0800d82e2edc9` | `2911 triangles` · `2092 sommets` · `sha256 32a3f00369488ce93592d8bb9a0ebff862e38d90d4de856dcbcf9df91da51b80` |
| 169 | `choir_mine_hull` | `5632 triangles (budget 6000)` · `6706 sommets` · `sha256 b60d5e378f4efdbca419b31c47fffbaafd097dcd716b59901256644ad5f55e6a` | `6232 triangles (budget 7000)` · `7371 sommets` · `sha256 eac2f025c84bd61662a582cc18e7947cf2304ac84bf3441ab95e3c0a6f6a4d4d` |
| 172 | `null_maw_hull` | `6630 triangles` · `7554 sommets` · `sha256 f5f2f42051d97586f085e26341748ae20a4c15e5b28b2b9fdb26a41b20b8127f` | `6830 triangles` · `7722 sommets` · `sha256 accb596fa048e49996b7fdb9d8636bffc1dd9bdc469008912971ea9cf2b35bd7` |
| 177 | `leech_drone_hull` | *(rien)* | **fichier byte-identique — ne rien changer** |
| 183 | `core_interior` | *(rien)* | **fichier byte-identique — ne rien changer** |

Et, pour les **dix lignes régénérées**, la phrase à **ajouter** en fin de `notes` (texte ASCII, sans
virgule non protégée — le champ est déjà entre guillemets) :

> `REGENEREE PAR BRIEF-0084 (correctif de ak.inset_panel dans le kit ; aucune retouche de forme). Le kit passe en 1.1.0 : inset_panel() met desormais a jour les normales (bm.normal_update()) avant bmesh.ops.inset_region, qui lisait des normales nulles sur un maillage frais et ne creusait donc RIEN — seul le materiau changeait. Les panneaux enfonces de cette coque existent en geometrie pour la premiere fois. Silhouette inchangee : bounding box et pivot identiques au 1/10 de mm, contrat de noms (nœuds, parents, positions monde) diff VIDE, aucune piece renommee ni reparentee. Trois executions byte-identiques (blender45 -t 1 -b). Rendu et regarde a l angle de la camera de jeu sur fond noir : docs/forge/output/BRIEF-0084-revue-avant-apres.png et BRIEF-0084-revue-zoom-avant-apres.png. Mesures et methode : docs/forge/output/BRIEF-0084-report.md.`

Pour `choir_mine_hull`, ajouter en plus :

> `Garde-fou de triangles du script releve de 6 000 a 7 000 (BRIEF-0084) : la mine passe a 6 232 triangles une fois ses panneaux reellement creusés ; le plafond normatif de la classe ennemi leger reste 12 000 (ADR-0011). Aucun detail n a ete retire pour rentrer dans l ancien chiffre.`

Pour `leech_drone_hull` et `core_interior`, si l'on veut tracer la vérification (facultatif, aucune
valeur ne change) :

> `Verifie sous BRIEF-0084 : reconstruite avec le kit 1.1.0, le .glb est BYTE-IDENTIQUE (sha256 inchange). C est la preuve d idempotence du correctif — ce script appelait deja bm.normal_update() de son cote.`

---

## 12. Fichiers touchés

| Fichier | État |
|---|---|
| `tools/blender/lib/aegis_kit.py` | **modifié** — `inset_panel()` corrigé, `inset_panels()` et `_edge_disjoint_lots()` ajoutés, `VERSION` 1.0.0 → 1.1.0 |
| `tools/blender/build_choir_mine.py` | **modifié** — une ligne : `tri_budget` 6 000 → 7 000, avec sa justification (§6) |
| `assets/imported/models/**/*.glb` (10 fichiers) | **régénérés** |
| `assets/imported/models/bosses/core_interior.glb`, `ships/leech_drone.glb` | **reconstruits, byte-identiques** (git ne les voit pas modifiés) |
| `docs/forge/output/BRIEF-0084-revue-avant-apres.png` | **livrée** |
| `docs/forge/output/BRIEF-0084-revue-zoom-avant-apres.png` | **livrée** |
| `docs/forge/output/BRIEF-0084-report.md` | ce rapport |
| `assets/licenses/ASSET_PROVENANCE.csv` | **non touché** (§11) |
| les 10 autres `tools/blender/build_*.py` | **non touchés** |
| `scripts/`, `scenes/`, `resources/`, `tests/`, `project.godot` | **non touchés** |

Reconstruction :

```bash
./scripts/build-hull.sh --all                 # les 12 coques
./scripts/build-hull.sh --check specter_9     # determinisme d'une coque
```
