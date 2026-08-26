# BRIEF-0085 — Le décor de survol : lune à cratères et champ d'astéroïdes

- **Statut** : ✅ **PRÊT À ENGAGER** — la garde GPU est levée, mesure faite le 2026-08-26 (voir §Contexte)
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-25

## Objectif

Remplacer la **doublure procédurale** du survol de lune (phase 2, `ADR-0027`) par un décor forgé :
une **calotte de lune à cratères** et **trois astéroïdes** qu'on survole, en `.glb`.

⚠️ **TU LIVRES LA GÉOMÉTRIE ET SES UV, PAS LA MATIÈRE.** Le grain de la surface arrive par une
**texture fournie par l'opérateur** (voir §Le partage du travail). Ton `.glb` doit être **prêt à la
recevoir**, ce qui change complètement ce qu'on attend de tes UV — lis cette section avant de
modéliser quoi que ce soit.

## La cible artistique — regarde-la

**`assets/reference/concepts/moon_flyby_scene_sheet.png`**, fournie par l'opérateur le 2026-08-25.
Regarde-la avec Read avant de commencer : c'est **la** cible de ce chantier.

Ce qu'elle dit, et que le mécanisme livré confirme déjà :

- **Le cadrage est le bon.** Chasseur en bas, calotte occupant les deux tiers inférieurs, courbure
  d'horizon nette contre le noir, astéroïdes en haut. C'est la géométrie que le lot 2 a posée — tu
  n'as pas à la réinventer, seulement à l'habiller.
- **Les cratères sont NOMBREUX et de tailles très variées** : de la piqûre au bassin qui occupe un
  sixième du cadre, avec des bords francs et, sur les plus grands, un relief central et des terrasses.
  La doublure en a huit, tous de taille voisine — c'est le premier écart à combler.
- **La surface n'est jamais lisse** : grain partout, rochers épars, débris au pied des reliefs. C'est
  ce que la texture apportera.
- **Les impacts** ont une gerbe **conique et lumineuse**, et le bolide laisse une **traînée**. ⚠️ Ils
  ne sont PAS dans ton périmètre (ils sont codés), mais la planche montre où le code devra encore
  progresser — n'essaie pas de les modéliser.
- Un **astre lointain** en haut à gauche. Hors périmètre lui aussi : le fond a déjà ses repères.

⚠️ **Et ce qu'elle NE dit pas.** C'est un artwork, pas un écran de jeu : rien n'y bouge, aucun HUD ne
la recouvre, et le chasseur y est presque perdu sur la surface. Le jeu, lui, doit rester lisible —
voir la contrainte de palette.

## Le partage du travail — trois mains, pas deux

Ce chantier a une entrée que les briefs précédents n'avaient pas, et c'est le point le plus
important de celui-ci :

| Qui | Quoi |
|---|---|
| **L'opérateur** | **génère les textures** (ChatGPT / imagegen) et les dépose dans `assets/source/`. C'est lui qui tient le grain, l'albédo et le relief fin de la surface |
| **La forge** (toi) | la **géométrie** — silhouette du limbe, cratères qui portent une ombre, rochers — et surtout des **UV faites pour recevoir cette texture** |
| **Le concepteur** | détoure, importe, câble le matériau, mesure et intègre |

### Ce que ça change pour tes UV

⚠️ **`ak.box_project_uv()` ne suffit plus ici.** Il convient à une coque qu'on regarde de loin sans
carte de détail ; il donne des îlots arbitraires, avec coutures et échelles inégales. Une carte de
surface plaquée dessus **s'étirera visiblement** sur les flancs des cratères — et personne ne le
verra avant le rendu final.

Ce qu'on attend :

- La calotte porte un dépliage **continu et à densité de texels homogène** sur la zone vue. Un
  déroulé **cylindrique ou polaire** convient : la caméra ne voit qu'une calotte, pas une sphère.
- **Donne la densité de texels mesurée** (texels par unité monde) et **où sont les coutures** — elles
  doivent tomber hors du champ, c'est-à-dire derrière l'horizon ou sous la lune.
- Livre une **planche de contrôle du dépliage** (damier UV appliqué sur la calotte, rendu à la
  perspective du jeu). C'est la seule façon de constater un étirement avant qu'il coûte une texture
  régénérée.
- Les rochers peuvent rester en projection cubique : ils sont petits et passent vite.

### Ce que la géométrie garde, malgré la texture

Une carte ne remplace pas un relief là où il compte :

- **Le limbe** — la silhouette qui se découpe sur le noir. Aucune texture ne la dessine.
- **Les grands cratères** — leur bord doit **porter une ombre réelle**. C'est la leçon de la
  doublure : à cette distance aucune ombre portée directionnelle ne les dessinera
  (`directional_shadow_max_distance` vaut 40, la lune est bien au-delà), donc si le relief n'est ni
  géométrique ni peint, il n'existe pas.
- Les **petits** cratères et le grain : à la texture, sans hésiter.

**Dis dans le rapport où tu as placé la frontière**, et pourquoi. C'est le vrai sujet technique de ce
brief.

## Texture (ADR-0028)

**L'asset dépend de deux demandes de texture**, toutes deux à commander :

| Demande | Ce qu'elle habille |
|---|---|
| [`TEX-0001-moon-regolith-height.json`](../textures/TEX-0001-moon-regolith-height.json) | le grain et les petits cratères de `Moon_Cap` |
| [`TEX-0002-asteroid-rock-height.json`](../textures/TEX-0002-asteroid-rock-height.json) | la roche des trois `Asteroid_*`, matériau **partagé** |

Deux conditionnelles existent — `TEX-0003` (ejectas clairs) et `TEX-0004` — et **ne se commandent
pas sur plan** : `derive-maps.py --mul` dérive déjà l'assombrissement des creux depuis la hauteur.
Elles n'ajoutent que ce qui est *plus clair* que la surface, et seule une capture regardée peut dire
si ça manque.

**Dépliage attendu**, et c'est le sujet technique de ce brief (détaillé plus bas) :

| Pièce | Dépliage |
|---|---|
| `Moon_Cap` | **continu, densité de texels homogène**, coutures hors champ + planche de contrôle au damier UV |
| `Asteroid_01..03` | projection en boîte, **même échelle monde sur les trois** — une tuile calée sur le petit rocher se lit comme du gravier sur le gros |

⚠️ Ce brief est antérieur à `ADR-0028` : cette section a été **ajoutée après coup**, le 2026-08-26,
pour le mettre en conformité. Le partage en trois mains qu'il avait inventé est précisément ce que
l'ADR institue.

## Contexte

La phase 2 — le champ d'astéroïdes, entre les deux boss — a **son propre décor** : pendant qu'elle
dure, le fond spatial cède la place à un survol de lune. Demande de l'opérateur, mot pour mot :

> « Intégrer des objets 3D dans le fond qui sont en mouvement, genre des astéroïdes qu'on
> survolerait, vraiment énormes, pour montrer la grandeur de l'espace. Sur toute cette phase entre
> les boss, on survolerait même une lune, avec ses cratères. Une belle scène. »

Le mécanisme est **livré et jouable** (`scripts/vfx/moon_flyby.gd`) : bascule du décor, dérive avec
parallaxe, impacts de bolides. Ce qui tient lieu de décor aujourd'hui est une **doublure** — une
sphère grise à pastilles et trois ellipsoïdes — et le journal l'annonce à chaque montage. C'est elle
que tu remplaces, **sans toucher au mécanisme**.

### ✅ La garde est LEVÉE — mesuré sur Quadro T1000 le 2026-08-26

Ce brief est resté au brouillon parce que son budget avait été mesuré **sur RTX 4080** (0,323 ms
contre 0,945 pour le fond habituel), alors que le poste qui **contraint** est la **Quadro T1000**.
La mesure a été refaite là-bas, dans la phase, à temps de jeu identique (8 s après l'entrée dans le
champ, à 60 Hz — pas en `--novsync`, qui ferait atteindre la même image à des temps de jeu
différents et donc avec des scènes différentes). **Trois tirs alternés par configuration**, comme
l'impose `.claude/resources/howto-mesurer-la-perf.md` sur une machine dont le bruit atteint ~1,9 ms.

| Configuration | Relevés (ms/image) | Plage |
|---|---|---|
| Survol **avec** ses textures | 5,660 / 5,935 / 5,280 | **5,28 – 5,94** |
| Survol **sans** texture (`--no-surface-maps`) | 5,804 / 6,122 / 4,882 | **4,88 – 6,12** |
| Fond spatial habituel (`--no-flyby`) | 12,588 / 13,527 / 14,241 | **12,59 – 14,24** |

**Ce que ça autorise.** Le survol coûte **moins de la moitié** du fond qu'il remplace. Même dans
l'hypothèse la plus défavorable (fond au plus bas, survol au plus haut), l'économie est de
**6,6 ms par image**, soit 40 % du budget 60 Hz. Les budgets ci-dessous ne se resserrent donc pas :
ils supposaient que la phase garde « au moins la moitié de la marge libérée », elle la garde
**entière**. Tu peux les tenir sans inquiétude, et un dépassement raisonnable se discute.

⚠️ **Les textures, elles, ne coûtent rien de mesurable** : les deux premières séries se recouvrent
entièrement, et la version texturée est même plus rapide deux fois sur trois. Ce n'est pas « elles
sont gratuites », c'est « leur coût est sous le plancher de bruit de cette machine ». N'en conclus
pas qu'on peut en empiler.

⚠️ **La série du fond monte régulièrement** (12,59 → 13,53 → 14,24) : c'est la dérive thermique d'un
châssis Max-Q, décrite dans le howto. Sa vraie valeur est plutôt vers le bas de la plage — ce qui
rend l'écart encore plus net, pas moins.

## La géométrie du lieu — relevée, à respecter

Le lot 2 a **posé le repère**, et `tests/unit/test_moon_flyby.gd` en tient les bornes. Tu t'y
substitues, tu ne le redéfinis pas.

| Élément | Valeur | Pourquoi elle n'est pas négociable |
|---|---|---|
| Plafond du décor | **Y = −3** | Le plan de jeu est en Y = 0. Un volume qui monte au-dessus masque le combat sans jamais pouvoir être touché |
| Ciel du survol | Y = −45 | Il n'est pas de ton ressort (c'est un shader), mais **tout ton décor vit au-dessus de lui**, sinon il est masqué en silence |
| Centre de la lune | (0, −78, 34), rayon **60** | Le sommet affleure à −18 : sous le plan de jeu, au-dessus du ciel |
| Astéroïdes | entre Y = −13 et −34 | Leur **hauteur est bornée par leur rayon** : un bloc de rayon r posé à y doit tenir sous −3, transformations comprises |
| Caméra | (0, 14, 5), plongée ~20°, FOV 62° | C'est d'**au-dessus** qu'on regarde. Le détail va sur les faces supérieures |

⚠️ **Ce que tu livres n'est PAS une planète entière.** Le joueur n'en voit qu'une **calotte** qui
occupe le bas du cadre, avec sa courbure d'horizon. Modéliser la sphère complète, c'est payer 100 %
d'une géométrie dont on montre moins d'un quart.

## Contraintes

- **IP** : design original. Aucun élément identifiable d'une licence existante.
- **Palette** : le décor **recule pour que le jeu avance**, et c'est la contrainte qui prime sur la
  ressemblance à la planche. Première capture de la doublure : à 0,30 d'albédo la lune rendait rose
  pâle et **le chasseur blanc s'y perdait** — trois lumières chaudes plus le `warmth`/`saturation`
  du post-traitement réchauffent tout gris neutre. Pars de **0,10 à 0,13 d'albédo, teinte froide**,
  et mesure sur le RENDU, jamais sur la valeur d'entrée.
  ⚠️ La planche de référence montre une lune bien plus **claire** : elle y est éclairée en rasant,
  avec un contraste local très fort, et rien ne doit y rester lisible. Si tu veux monter l'albédo
  moyen, il faut que le **contraste local** monte avec — le critère qui tranche n'est pas un chiffre
  mais une capture : **le chasseur et les mines se lisent-ils encore par-dessus ?**
- ⚠️ **Ni cyan ni corail, nulle part.** Le cyan est réservé au tir allié, le corail (#FF5A3D) au tir
  ennemi (règles de lisibilité de `space_background.gdshader`). Un élément de décor dans l'une de ces
  deux teintes se lit comme une menace ou comme une aide, et il n'est ni l'un ni l'autre. Cette règle
  a déjà coûté une itération sur le bolide d'impact.
- **Aucun émissif** sur la lune ni sur les rochers. Rien dans ce décor n'est allumé : la seule chose
  chaude de la phase est l'impact, et il doit rester seul à l'être.
- **Techniques** : Blender 4.5 LTS, headless, déterministe. Kit `tools/blender/lib/aegis_kit.py`
  réutilisé **sans modification** (il est en 1.1.0 depuis le 2026-08-25). Modèle le mieux
  instrumenté : `tools/blender/build_leech_drone.py`.
- ⚠️ **UV OBLIGATOIRES** (`ak.box_project_uv()`), n-gons triangulés avant export, et **compte
  `TEXCOORD_0` dans le `.glb` produit** — ne le suppose pas. Trois coques du dépôt sont sorties sans
  UV et le défaut est **totalement silencieux**.

### Budgets — confirmés par la mesure du 2026-08-26

| Pièce | Triangles | Raison |
|---|---|---|
| `Moon_Cap` — la calotte | **≤ 12 000** | Elle occupe le tiers bas du cadre en permanence. Le relief se joue par la **silhouette du limbe** et par les cratères, pas par la densité du maillage |
| `Asteroid_01..03` | **≤ 2 500 chacun** | Le plus gros traverse le cadre entier ; les deux autres sont plus loin |

⚠️ **Le « vraiment énorme » ne s'achète pas en triangles.** Il se joue par la **parallaxe et le
cadrage** — un bloc proche qui traverse lentement dit mieux l'échelle que dix cailloux. Le mécanisme
livré s'en charge déjà : la vitesse de dérive se **déduit** de la hauteur de chaque rocher.

## Les cratères — le sujet technique du brief

C'est le seul endroit où le rapport détail/coût se joue vraiment.

- Une sphère très subdivisée est hors budget ; une **carte de hauteur sur une géométrie modeste** ne
  l'est pas. Choisis, et **dis pourquoi dans le rapport**.
- ⚠️ **Un cratère doit se lire comme un CREUX, pas comme une pastille posée.** La doublure a fait
  exactement cette faute : des palets de 0,6 d'épaisseur posés à `R − 0,2` dépassaient de la surface,
  et au limbe — là où la lune tourne — ils se **détachaient franchement de la silhouette**. On voyait
  un objet sur la lune, l'exact contraire d'un creux.
- À cette distance **aucune ombre portée ne dessinera le relief** (`directional_shadow_max_distance`
  vaut 40 et la lune est bien au-delà). Un creux se lit donc par le **noir qu'il fait** et par le
  **bord** qu'il découpe. Prévois-le : un cratère purement géométrique, sans contraste d'albédo,
  risque d'être invisible.
- Tailles : la doublure a montré qu'un cratère de rayon **9 sur une lune de 60** lisait comme une
  flaque. Reste dans **1,5 à 5**, et varie-les.

## La rotation, et ce qu'elle impose

La lune **tourne autour de X** à 0,022 rad/s : sa surface défile vers le bas de l'écran, dans le sens
où le joueur avance, et parcourt ~63° pendant la phase. Deux conséquences :

- Le relief doit rester crédible **sur tout ce parcours**, pas seulement à la pose de départ. Un
  détail concentré sur une seule face sortira du cadre au bout de vingt secondes.
- Le **limbe** est la partie la plus regardée : c'est là que la silhouette se découpe sur le noir.

## Les impacts — ce que le décor doit leur offrir

Trois bolides percutent la lune à 11 s, 26 s et 40 s, **en (x, z) monde** : (−6, 10), (12, 2),
(−14, −2). La hauteur est déduite de la sphère par le code, jamais écrite à la main.

Tu ne fournis **aucun effet** — flash, gerbe et bolide sont du code. Mais **prévois trois zones de
surface dégagées** à ces endroits : un choc au milieu d'un massif de cratères ne se lirait pas.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_moon_flyby.py` | script de construction, rejouable, déterministe |
| `assets/imported/models/backgrounds/moon_flyby.glb` | le décor exporté (LFS) |
| `docs/forge/output/BRIEF-0085-report.md` | compte-rendu : mesures réelles, budgets tenus, choix de relief et sa justification |
| `docs/forge/output/BRIEF-0085-planche-survol.png` | **rendu à la perspective du jeu**, pas au cadrage de `render-hull.py` |
| `docs/forge/output/BRIEF-0085-planche-uv.png` | **contrôle du dépliage** : damier UV sur la calotte, même perspective. Sans elle, un étirement ne se découvre qu'après la texture |

## Contrat de noms — lu par le code

`MoonFlyby._collect_bodies()` relève les pièces **par leur nom**. Un nom manquant dégrade en
silence : la lune ne tournera pas, ou un rocher restera planté.

| Nœud | Ce que c'est |
|---|---|
| `Moon` | le **pivot** de la calotte, à l'origine du décor. C'est LUI que le code fait tourner |
| `Asteroid_01`, `Asteroid_02`, `Asteroid_03` | les rochers, **enfants directs de la racine** — le code ne les cherche pas plus profond |

⚠️ **Un contrat de noms respecté n'est pas une preuve que l'asset fait ce qu'il dit.** `ADR-0025` l'a
payé : la coque du boss livrait des « anneaux qu'on franchit » de 30 cm pour un chasseur de 2,46 m,
noms parfaitement conformes. **Donne les dimensions réelles mesurées**, et rends une vue avec un
repère d'échelle.

## Provenance

Une ligne par asset dans `assets/licenses/ASSET_PROVENANCE.csv`, **en append shell (`>>`)**, jamais
par réécriture. `asset_type=model3d`, `source_tool=asset-forge (Blender 4.5.11, script)`,
`license=proprietary-internal`, `prompt_file=docs/forge/briefs/BRIEF-0085-survol-de-lune-decor.md`.

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_moon_flyby.py` régénère le `.glb` sans erreur
- [ ] **Rien ne monte au-dessus de Y = −3**, transformations comprises — mesuré, pas supposé
- [ ] La calotte a son sommet à **−18 ± 1** et son centre implicite en (0, −78, 34)
- [ ] Budgets tenus : calotte ≤ 12 000 triangles, chaque rocher ≤ 2 500 — chiffres réels au rapport
- [ ] **`TEXCOORD_0` sur 100 % des primitives**, compté dans le `.glb`
- [ ] Dépliage de la calotte **continu, densité de texels homogène**, coutures **hors champ** —
      densité mesurée et emplacement des coutures donnés au rapport
- [ ] Planche de **damier UV** rendue et regardée : aucun étirement visible sur les flancs de cratères
- [ ] La frontière géométrie / texture est **explicitée et justifiée** dans le rapport
- [ ] Contrat de noms : `Moon` (pivot), `Asteroid_01..03` en enfants directs
- [ ] Albédo rendu **entre 0,10 et 0,13**, teinte froide — mesuré sur le rendu
- [ ] **Aucun émissif**, aucun cyan, aucun corail
- [ ] Les cratères se lisent comme des **creux** au limbe, pas comme des pastilles posées
- [ ] **Tailles très variées**, de la piqûre au grand bassin — la planche de référence en est le juge
- [ ] Vérifié en capture : **le chasseur et les mines restent lisibles** par-dessus la surface
- [ ] Trois zones dégagées aux points d'impact (−6, 10), (12, 2), (−14, −2)
- [ ] `./scripts/build-hull.sh --check moon_flyby` : deux exécutions, `.glb` byte-identique
- [ ] **Rendu et regardé** (ADR-0006), à la perspective du jeu, avec repère d'échelle
- [ ] Provenance renseignée

## Hors périmètre

Pas de `.tscn`, `.tres`, code ni tests — l'intégration appartient au concepteur. **Pas d'effets
d'impact** : bolide, flash et gerbe sont du code. **Pas de ciel** : c'est un shader. Pas de LOD, pas
de `.blend` versionné. Et **aucune modification du kit**.

⚠️ **PAS DE TEXTURES.** Ni peintes, ni générées, ni procédurales cuites dans le `.glb`. La matière de
la surface vient de l'opérateur, par une carte qu'il génère et dépose. Ce que tu livres, ce sont la
géométrie, les UV qui l'accueillent, et la **preuve** que ces UV la porteront sans l'étirer. Un
matériau provisoire pour tes propres rendus est bienvenu — mais il ne part pas dans le `.glb`
autrement qu'en couleur unie.
