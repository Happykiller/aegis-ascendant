# BRIEF-0034 — rapport de forge : Specter-9, passe de PLAN

- **Brief** : `docs/forge/briefs/BRIEF-0034-specter-9-plan-fuselage-porteur.md`
- **ADR de portée** : `docs/decisions/ADR-0014-silhouette-du-specter-9.md`
- **Exécuté par** : asset-forge — 2026-07-21
- **Build** : `./scripts/build-hull.sh --check specter_9` — **déterminisme OK**,
  sha256 `620aa13f12a189f73064901cdefa906a8ae99a17e75f751c7ad83d58b42efee3`
- **Porte de qualité** : `./scripts/check.sh` — **ALL GREEN** (115 tests, 729 assertions,
  0 échec), y compris les 6 tests de `ship_flight.gd`.

---

## 1. Livrables

| Fichier | État |
|---|---|
| `tools/blender/build_specter_9.py` | retravaillé (plan, nacelles, dérives, tuyère d'axe, mesure de débattement) |
| `assets/imported/models/ships/specter_9.glb` | régénéré — 45 828 tris, bbox 1,7471 × 0,6676 × 2,4600 m |
| `docs/forge/output/BRIEF-0034-report.md` | ce document |
| `docs/forge/output/BRIEF-0034-comparaison-vue-de-dessus.png` | **hors table de livrables**, ajouté : la planche de comparaison exigée au §Critères. Un rapport en markdown ne peut pas la « contenir » autrement. |

Provenance : ligne `specter_9_hull` de `assets/licenses/ASSET_PROVENANCE.csv` **remplacée**
(convention établie : une coque reforgée ne duplique pas sa ligne), plus une ligne
`brief_0034_comparaison_dessus` pour la planche.

`aegis_kit.py` et le code Godot n'ont **pas** été touchés.

---

## 2. La planche de comparaison — ce qui manquait au brief précédent

**`docs/forge/output/BRIEF-0034-comparaison-vue-de-dessus.png`** — trois vues de dessus à la
même hauteur : la planche de référence, le Specter-9 livré, le Specter-9 d'avant.

Le regard suffit, mais voici la même chose en chiffres. Demi-envergure rapportée à la
demi-envergure maximale, à huit stations exprimées en fraction de la longueur depuis le nez :

| fraction de longueur | 0,20 | 0,30 | 0,40 | 0,50 | 0,60 | 0,70 | 0,80 | 0,85 |
|---|---|---|---|---|---|---|---|---|
| **planche** (mesuré sur le masque de l'image) | 0,10 | 0,24 | 0,39 | 0,54 | 0,68 | 0,83 | 0,97 | 1,00 |
| **livré (BRIEF-0034)** | 0,15 | 0,29 | **0,43** | **0,57** | **0,71** | **0,85** | **0,99** | 0,41 |
| avant (BRIEF-0033) | 0,18 | 0,26 | 0,40 | 0,62 | 0,83 | 1,00 | 0,99 | 0,27 |

Sur les six stations centrales, l'écart à la planche passe de 0,17 (pire cas, à 0,60) à **0,04**.
Le rendu et le tableau disent la même chose, ce qui est la seule raison de faire les deux.

Autres mesures de plan :

| | planche | avant | livré |
|---|---|---|---|
| Flèche du bord d'attaque (depuis l'axe) | 24,4° | 38,3° | **26,5°** |
| Station du bout d'aile | ~82 % | 67 % | **81 %** |
| Aire du plan (coque, hors nacelles) | — | 1,812 m² | **1,678 m²** |
| Part de l'aile **hors** groupe fuselage+nacelles | ~30 % *(ADR-0014)* | 30 % | **18 %** |

### Les deux écarts qui restent, et pourquoi

1. **À 85 % de la longueur, la planche est encore à pleine envergure (1,00) ; le modèle est à
   0,41.** Sur la planche, les bouts d'aile descendent jusqu'au niveau des tuyères. Ici la coque
   s'arrête à y = 0,860 et le bord de fuite s'effondre en 10 cm. La raison n'est pas esthétique :
   le bout d'aile se trouve déjà derrière la charnière de volet, donc **sur une pièce mobile**.
   Le reculer encore reviendrait à faire porter la moitié arrière de l'aile par le volet — soit
   une aile extérieure entièrement mobile, ce qui n'est pas ce que le brief demande et ce que
   `ShipFlight` sait animer proprement.
2. **La densité graphique de la planche n'est pas atteinte** et ne le sera pas sans texture :
   la planche est une illustration, la coque est un maillage à 7 matériaux par facteurs. Écart
   assumé et hors périmètre (« ne pas générer de texture »).

---

## 3. Ce qui a été fait, par ordre de rendement

1. **`PLANFORM` refait.** Bord d'attaque droit de 26,5° depuis l'axe (planche : 24,4°),
   bout d'aile à 81 % de la longueur, bord de fuite quasi transversal derrière. **Le geste
   décisif n'est pas la flèche mais le placement longitudinal** : l'ancienne version atteignait
   sa largeur maximale 0,34 m trop tôt et était donc systématiquement plus large que la planche
   dans toute la moitié avant. L'envergure n'a pas bougé d'un millimètre.
2. **Un fuselage qui a des flancs.** `FUSELAGE` **rétrécit** (0,232 → 0,176 de demi-largeur,
   soit 0,352 m = 20 % de l'envergure, dans la fourchette du brief) mais le plan d'aile part
   désormais de **0,34 fois l'épine au lieu de 0,65** (`WING_ROOT_FRAC`). Résultat : une marche
   de **94 mm** franchie sur 4 % de la corde, c'est-à-dire un flanc à ~75° et non un congé.
   Rétrécir pour paraître plus porteur n'est pas un paradoxe : ce n'est pas la largeur qui fait
   lire un fuselage, c'est l'ombre à son pied.
3. **Un caniveau, pas une jointure** (`GUTTER_DEPTH` = 30 mm). L'épaule de nacelle en recouvre
   la moitié externe ; ce qui reste à l'œil est une fente sombre de ~32 mm sur 1,8 m de long,
   entre le fuselage et chaque nacelle. C'est la « rainure visible » demandée.
4. **Nacelles écartées et allongées.** Axes 0,268 → **0,352**, rayons × 0,915 (le carénage refermait
   sinon le caniveau par le haut), et surtout une **épaule** (`SHOULDER`) qui prolonge chaque
   fuseau vers l'avant jusqu'à y = −0,26. Nacelle + épaule = **1,49 m, soit 60,6 % de la
   longueur** — le brief en demandait 60 à 75 %. Sans cette pièce, fuseau + carénage n'en
   couvraient que 38 % et la ligne « nacelles longues » du brief était fausse.
5. **Deux dérives inclinées** (ADR-0014), 30 cm d'envergure, **34° vers l'extérieur**, sur le dos
   des nacelles, bord d'attaque en flèche, coiffe rouge, flanc externe bleu profond. Elles
   projettent 168 mm en vue de dessus — c'est cette projection qui les rend utiles dans un shmup
   vertical, une dérive droite n'y montrerait que sa tranche.
6. **Les rails verticaux de bout d'aile disparaissent**, remplacés par une **lisse basse**
   (moitié de la hauteur). Ils n'existaient que parce que BRIEF-0033 s'interdisait les dérives ;
   à hauteur égale, une dérive au centre de la silhouette rapporte plus qu'un rail au bout d'une
   lame. La lisse subsiste pour que la lame ne lise pas comme un tranchant, et porte le feu de
   bout d'aile.
7. **Une tuyère d'axe** en bout de poutre dorsale (lèvre à y = 1,185, donc sans effet sur la
   longueur). C'est elle qui fait lire le fuselage comme porteur *jusqu'à la poupe* : sans elle,
   l'arête dorsale s'arrêtait dans le vide et le regard concluait « bande posée », exactement le
   défaut qu'ADR-0014 pointe.
8. **Nez d'aiguille.** 0,136 → **0,068** de demi-envergure à y = −0,86. Conséquences en chaîne
   traitées : quille avant amincie (0,058 → 0,044, elle débordait latéralement d'une coque
   devenue plus fine qu'elle) et tubes de canon resserrés (0,080 → 0,042).

---

## 4. Le plafond de débattement des volets — remesuré

> **18,5°** (contre 13° avant). `ShipFlight.FLAP_DEG` est à 11,0 : **la marge passe de 2° à 7,5°**.

**Aucun changement n'est requis côté code.** Si le concepteur veut un braquage plus expressif,
il peut monter jusqu'à ~16° en gardant la marge de sécurité que le commentaire de
`scripts/fx/ship_flight.gd:16-18` décrit ; ce n'est pas nécessaire, c'est possible.

La mesure n'est plus faite à la main. `_flap_travel_limit()` la refait **à chaque build**, sur
le maillage livré, et l'imprime :

```
volets : plafond de debattement mesure 18.5 deg
```

Le volet tourne autour d'un axe parallèle à X passant par son pivot ; un sommet `(y, z)` va en
`y' = y_p + (y−y_p)·cos t − (z−z_p)·sin t` et mord la cloison dès que `y' < FLAP_HINGE_Y`.
La fonction résout l'angle pour **chaque sommet**, dans les deux sens, et retient le plus petit.

Pourquoi mesurer plutôt que calculer : la valeur dépend de la forme du volet, donc de la corde
de l'aile à son emplanture, donc du planform. **Elle change dès qu'on touche à la silhouette.**

Cette instrumentation a immédiatement payé. Un marquage doré de bord de fuite, hérité de
BRIEF-0033 et posé à y = 0,700, s'est retrouvé **à cheval sur la nouvelle charnière** (0,760)
quand le volet a migré sur les lames. Il devenait le point le plus contraignant de la pièce et
faisait tomber le plafond à **2,8°** — sous les 11° auxquels `ShipFlight` est réglé, donc un
volet qui traverse la coque en jeu. Rien dans le contrat du kit n'aurait attrapé ça, et le
défaut ne se voit pas au repos. Le marquage est reculé à y = 0,795.

Le gain de 13 → 18,5° vient de la géométrie, pas d'un desserrage : la charnière est passée de
y = 0,610 à **0,760**, sur une portion de lame nettement plus mince, et le point du volet le plus
éloigné de l'axe de charnière est passé de 54 à 43 mm.

Les trois autres paramètres du volet n'ont pas changé de nature : jeu de charnière 13 mm,
emplanture à |x| = 0,530 (28 mm de garde sur le bord externe de la nacelle, à 0,502 — au-delà,
le volet traverserait le fuseau dès la première image), pivots `Flap_L/R` posés sur
l'articulation.

---

## 5. Verdict de lisibilité en vue de jeu — franchement

**Le risque annoncé par le brief ne s'est pas matérialisé. Aucun arbitrage n'est nécessaire.**

Le raisonnement du brief était juste dans son principe et faux dans son ampleur : un fuselage
porteur lit effectivement plus étroit qu'un delta, mais ici la perte est de **7 % d'aire de plan**
(1,812 → 1,678 m²) à **envergure et longueur strictement identiques**. La silhouette ne devient
pas une flèche maigre ; elle devient une flèche **articulée**.

Ce que montre la vue « game » de `render-hull.py` (20° de la verticale), réduite à 150, 80 et
48 px de haut — soit largement en dessous des ~1,2 m à l'écran de la DA :

- **La forme générale tient**, et c'est la même que pour l'ancienne : une pointe de flèche
  blanche. Le nez plus long rend l'apex plus net, ce qui aide plutôt.
- **Le vaisseau gagne trois marqueurs qu'il n'avait pas** : les **trois** couronnes dorées de
  tuyère au lieu de deux, les deux coiffes **rouges** de dérive, et l'axe sombre du fuselage qui
  court désormais sur toute la longueur. À 48 px, ce sont ces trois signes qui identifient
  l'appareil, pas son contour.
- **Le seul recul honnête** : à la plus petite taille, l'arrière du vaisseau est maintenant
  découpé en trois masses (nacelle, fuselage, nacelle) au lieu d'une, et les caniveaux
  introduisent deux lignes sombres dans une zone auparavant pleine. C'est un contour très
  légèrement moins « bloc ». Cela se paie en netteté de bord et se récupère largement en
  identité. Si l'intégration en jeu contredisait ce jugement, le levier le moins destructeur est
  d'**élargir l'épaule de nacelle** (`SHOULDER`, +2 cm de demi-largeur) : elle referme les
  caniveaux vus de loin sans toucher au plan.

Je n'ai donc **pas** élargi les lames ni écarté davantage les nacelles. Le faire aurait rendu
au delta ce que le brief venait de lui retirer, pour corriger un problème que le rendu ne montre
pas.

Réserve de méthode : ce jugement porte sur des rendus Cycles hors moteur. Le verdict définitif
appartient à un lancement Windows natif avec la caméra réelle et le fond de jeu — c'est du
ressort de la session principale (ADR-0006 est satisfait au sens « rendu et regardé », pas au
sens « vu en jeu »).

---

## 6. Mesures relevées sur le `.glb` livré

```
triangles  : 45 828        (budget 60 000 — ADR-0011 ; 42 520 avant)
sommets    : 52 132
bbox       : 1,7471 x 0,6676 x 2,4600 m   (Godot X, Y, Z)
centre     : (-0,0000, -0,0112, +0,0000)
matériaux  : Emissive=1538  Glass=140  Greeble=11098  Hull=27387
             Marking_Red=174  Panel=2649  Trim=2842      (7/7, MATERIAL_ORDER intact)
```

- **X = 1,7471** contre 1,75 imposé : **−0,17 %**, très en deçà des ±3 % du brief. L'écart vient
  du chanfrein de 2,2 mm appliqué au bout d'aile, qui appartient au volet et non à la coque.
- **Z = 2,4600** exactement (fixé par la lèvre des pétales, y = 1,230).
- **Y = 0,6676** = 27,1 % de la longueur, dans la fourchette 0,62-0,72 du brief. Les dérives
  n'ont **pas** poussé le plafond : leur sommet est à z = +0,319, la verrière à +0,314 — les deux
  culminent au même endroit, ce qui était l'objectif (ADR-0011 : ce qu'on ajoute au-dessus se paie
  en vue de dessus).
- Le budget de triangles est consommé à 76 %.

**4 pièces mobiles**, nœuds glTF séparés, origine sur l'articulation (repère Godot) :

| Pièce | Origine | Nature |
|---|---|---|
| `Flap_L` / `Flap_R` | (∓0,6700, −0,0240, +0,7730) | volets de bord de fuite, migrés sur les lames ; **rotation** autour de X |
| `Nozzle_L` / `Nozzle_R` | (∓0,3520, −0,0620, +1,0480) | couronnes de 12 pétales fermées au repos ; **mise à l'échelle** radiale |

**10 points d'attache**, mêmes rôles :

| | X | Y | Z |
|---|---|---|---|
| `Muzzle_L` / `Muzzle_R` | ∓0,042 | −0,068 | −1,070 |
| `Muzzle_C` | 0 | −0,068 | −1,070 |
| `Muzzle_Wing_L/R` | ∓0,500 | −0,018 | +0,007 |
| `Muzzle_Tip_L/R` | **∓0,800** | −0,018 | +0,607 |
| `Engine_L/R` | ∓0,352 | −0,044 | **+1,234** |
| `Cockpit` | 0 | +0,215 | −0,380 |

- `Muzzle_Tip_L/R` **reste à |x| = 0,800** comme l'exige le brief. Sa *dérivation* change :
  il est pris à la station de bord d'attaque où la demi-envergure vaut 0,800, et non plus au coin
  de largeur maximale. Ce coin est désormais derrière la charnière de volet ; l'ancienne
  dérivation aurait posé le point de tir sur une pièce mobile.
- `Engine_L/R` restent **4 mm derrière** la lèvre des pétales (1,230), conformément au brief.
- `Muzzle_L/R` se resserrent de 0,080 à 0,042 : les tubes du canon ventral ont suivi le nez qui a
  maigri de moitié. Flash, tube et balle restent alignés (une seule constante, `BARREL_X`, pilote
  les trois).

**Conformité aux exclusions d'ADR-0014** : aucune bande de livrée, aucun chiffre, aucun texte,
aucun insigne. `AA_Marking_Red` représente **174 triangles sur 45 828 (0,4 %)** — trois marques
de bord d'attaque, une platine ventrale, un bandeau de baie technique et les deux coiffes de
dérive. C'est un marquage restreint au sens de la charte §3, pas une livrée.

---

## 7. Ce qui est conservé de BRIEF-0033 — vérifié, non régressé

- **Profil superposé** : quille ventrale, écopes de nacelle, plan d'aile, corps de fuselage,
  arête dorsale, verrière. Les six couches sont intactes (vue « profil » du rendu).
- **Densité de panneautage** : 19 rainures transversales (autant qu'avant, redistribuées sur la
  nouvelle trame de stations) + 2 rainures longitudinales + panneaux bleus à deux niveaux.
- **Nacelles en volumes propres** : renforcé, pas conservé — elles sont plus écartées, plus
  longues et séparées du fuselage par un caniveau.
- **Verrière, cadre, montants, baie technique dorsale, greebles de pont** : conservés, repositionnés.
- **UV** : projection en boîte à 4,0 tuiles/m, inchangée ; `TEXCOORD_0` + `TANGENT` sur les
  5 maillages ; aucune texture embarquée.

⚠️ **Un piège rencontré, à consigner** : la moitié des détails de BRIEF-0033 était posée à des
**abscisses absolues** (`x = 0,470`, `x = 0,740`…). Le bord d'attaque ayant reculé de 12°, quatre
bandeaux sur sept se sont retrouvés **hors de la coque**, dans le vide, et deux sous l'épaule de
nacelle. Les bandeaux cyan sont désormais placés en **fraction de corde** (`_chord_x()`), ce qui
les rend insensibles à la prochaine passe de silhouette. Les greebles restent en absolu (leur
placement est un choix de composition, pas une règle) mais chaque valeur a été revérifiée contre
le nouveau planform.

---

## 8. Limites connues

1. **Le bout d'aile appartient au volet.** Conséquence : si le nœud `Flap_L/R` était masqué côté
   Godot, le vaisseau perdrait 4 cm d'envergure par côté (−5 %). Aucun risque en animation —
   une rotation autour d'un axe parallèle à X laisse |x| strictement invariant, la largeur ne peut
   pas changer — mais c'est à savoir avant d'écrire un LOD ou un état de dégâts qui retirerait la
   pièce.
2. **L'aile extérieure reste graphiquement pauvre** comparée à la planche : un liseré bleu au
   bord d'attaque, un chevron, quelques greebles. À l'échelle du jeu c'est suffisant ; en gros
   plan d'accueil, c'est la zone la plus nue de la coque.
3. **La comparaison à la planche est faite sur un masque de luminance**, pas sur un tracé
   vectoriel. Les valeurs du tableau §2 sont précises à ~±0,02 de demi-envergure ; elles suffisent
   à trancher un écart de 0,17, pas à départager 0,02.
4. **Le ventre reste riche pour ce qu'on en voit** (remarque de BRIEF-0033, toujours valable) :
   quille, écopes et cadres coûtent de la géométrie qu'une caméra à 20° ne verra jamais. C'est le
   premier endroit où couper si le budget devenait contraignant.
5. **Aucune mesure de perf.** Le passage de 42 520 à 45 828 triangles (+7,8 %) est présumé sous le
   bruit ; c'est une présomption, pas un relevé.
6. **Le nez d'aiguille rend le canon ventral proéminent.** Les deux tubes dépassent d'environ
   18 mm de part et d'autre d'une coque qui n'en fait plus que 39 à leur station. Lu comme un
   canon sous-nasal, ce qui est cohérent ; s'il déplaisait, il faudrait rentrer les tubes dans la
   quille et perdre leur lecture.

---

## 9. Ce qui a manqué au kit — signalé, non corrigé

`aegis_kit.py` n'a pas été modifié. Les trois manques de BRIEF-0033 tiennent toujours ; je ne les
répète pas. **Le troisième est confirmé par une preuve, et deux s'y ajoutent :**

1. **Confirmation, avec dégâts constatés — `moving_part()` ne sait toujours pas vérifier le
   dégagement.** BRIEF-0033 le signalait comme une gêne théorique. Ici, c'est un **défaut réel qui
   est passé** : un décor de 2 cm posé à cheval sur la charnière a fait chuter le plafond de
   débattement de 18,5° à 2,8° — soit un volet qui traverse la coque à chaque virage, sous les 11°
   auxquels le jeu est réglé. Le contrat du kit a validé cette version sans un mot, la bbox au
   repos étant parfaite. `_flap_travel_limit()` (≈ 25 lignes, dans `build_specter_9.py`) l'a
   attrapé au build suivant. **C'est un `MovingPart(axis=, limit_deg=)` balayé par `export_hull()`
   qui manque**, et l'implémentation existe désormais, prête à remonter.
2. **Aucune primitive de lame inclinée.** J'ai écrit `_fin()` localement : loft de sections
   rectangulaires le long d'un axe incliné, épaissies perpendiculairement au plan de la lame. Ce
   n'est pas propre au Specter-9 — c'est le vocabulaire de toute dérive, aileron, pale ou nageoire,
   et la Citadel comme le Leviathan en ont. Même histoire que `_beam` au brief précédent : trois
   scripts réimplémenteront la même chose avant que ça ne remonte.
3. **`_dome()` évalue son assise au seul axe de la pièce.** Un pod posé sur un pont courbe a donc
   une base plate et s'enfonce légèrement sur ses bords. Invisible ici (l'aile est presque plane
   là où sont les épaules), mais c'est une limite qui mordra sur une coque plus bombée. Un
   `base_z(x, y)` au lieu de `base_z(y)` suffirait.

Point positif : `build-hull.sh --check` a rendu deux exécutions byte-identiques du premier coup,
sur un maillage entièrement refait. Le `-t 1` fait exactement ce que son en-tête promet.

---

## 10. Suggestions au concepteur

1. **`ShipFlight.FLAP_DEG` peut monter.** 11° sur un plafond de 18,5° laisse 7,5° de marge. Un
   braquage à 14-15° serait nettement plus lisible en virage tout en gardant plus de marge
   qu'aujourd'hui. Décision de game feel, pas de forge — je ne l'ai pas prise.
2. **Remonter `_flap_travel_limit()` dans `aegis_kit.py`** (§9.1). C'est le meilleur retour sur
   investissement disponible : le code est écrit, testé, et il vient d'attraper un défaut qui
   serait parti en jeu.
3. **Écrire dans `.claude/resources/` la règle qui a coûté ce brief** : *ne jamais placer un
   détail à une abscisse absolue sur une surface dont la silhouette peut bouger* (§7). C'est la
   deuxième fois que le planform bouge et la deuxième fois que des détails partent dans le vide.
4. **La conclusion de méthode d'ADR-0014 est outillée, pas encore automatisée.** La planche
   côte-à-côte a été fabriquée à la main pour ce rapport. Un `tools/compare-to-reference.py`
   (recadrer, mettre à la même hauteur, juxtaposer) rendrait la vérification systématique au lieu
   de dépendre de qui y pense — c'est exactement le raisonnement qui a produit `build-hull.sh`.
