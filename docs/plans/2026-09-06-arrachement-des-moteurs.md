# Plan — L'arrachement des moteurs (phase finale du niveau 2)

> **Boucle cible** : ARRIVÉE → FLAMMES → ANCRAGES → INSTABILITÉ → ARRACHEMENT → MOTEUR EN
> DÉRIVE → TROIS BERCEAUX VIDES → SILENCE.

- **Statut** : rédigé le 2026-09-06, aucun lot entamé
- **Spec de référence** : « SPEC — Phase finale *Arrachement des moteurs* » (opérateur,
  2026-09-06), à verser dans `docs/` au LOT 0
- **Planche maîtresse** : `phase_final_niveau2_vaiseau_monde.png`

---

## Contexte

### Ce que le jeu fait aujourd'hui

Le niveau 2 **n'a pas de fin jouée**. `CortegeFlyby` émet `survey_finished` quand les
500 m ont défilé ; `CortegeRoot._on_survey_finished()` bascule directement en `VICTORY`,
lance `survey_end` et programme le rapport de mission. Il n'existe ni poupe, ni moteur, ni
état terminal — la traversée s'arrête, c'est tout.

Tout le lot se greffe donc à **un seul point de couture** : ce que `survey_finished`
déclenche. C'est une bonne nouvelle pour le risque, et une mauvaise pour la narration
(voir la décision D3).

### Ce qu'on a en main

| Ressource | État | Ce qu'elle vaut |
|---|---|---|
| La spec ci-dessus | complète, 22 sections | source de vérité de la phase |
| `phase_final_niveau2_vaiseau_monde.png` | planche maîtresse | cadrage, silhouette, storyboard en 3 temps, répliques |
| `groupe-moteur-principal` v2 | **livré** (`.glb` + `.blend` + scripts) | 3 clips, géométrie approuvée |
| `berceau-moteur` v1 | **livré** (`.glb` + `.blend` + scripts) | 4 clips, contrat de mariage écrit |
| `asset3_ancrage_destructible.png` | planche cotée | **la cible du gameplay** — pas encore modelée |
| `asset4_bras_encrage.png` | planche | bras d'ancrage |
| `asset5` conduite énergétique, `asset6` flexibles, `asset7` pylône | planches | habillage de poupe |
| `asset8` ×4 (tour thermique, bride moteur, conduit magenta, cryogénie) | planches | habillage |
| `asset9` ×4 (déflecteur, collier, refroidissement, anneau de maintenance) | planches | habillage |
| `asset10` moteur | planche | variante / détail |

**Dix-sept planches, deux binaires.** Le plan est construit pour que les quinze pièces
manquantes n'empêchent **rien** : la phase doit être jouable de bout en bout en boîtes
grises avant qu'un seul asset final n'entre.

### L'audit des deux binaires livrés — mesuré, pas supposé

```
groupe_moteur_principal.glb   70,4 Mo   1 300 maillages   276 816 triangles
                              9 matériaux   11 images embarquées   3 clips
                              bbox  9,10 × 5,49 × 11,93 m

berceau_moteur.glb            64,9 Mo     968 maillages   157 104 triangles
                              8 matériaux   11 images embarquées   4 clips
                              bbox 11,19 × 4,64 × 14,00 m
```

À comparer avec ce que le dépôt embarque déjà : **`long_cortege.glb` — les 500 m de coque,
5 tronçons, 30 marqueurs — fait 49 458 triangles.**

> ⚠️ **Trois groupes moteur + trois berceaux = 1 301 760 triangles, soit vingt-six fois tout
> le niveau 2 actuel, et 400 Mo de binaires.** Ce n'est pas un détail d'optimisation : c'est
> le fait dominant de ce chantier. Aucun lot ne pose ces `.glb` tels quels.

Trois autres écarts au contrat du dépôt, tous silencieux s'ils ne sont pas traités :

1. **Les matériaux ne portent pas les noms du kit** — `01 | Anthracite blinde`,
   `06 | Energie magenta`, `07 | Coeur plasma`… au lieu de `AA_Hull` / `AA_Emissive_Engine`.
   `CortegeSkin` reconnaît son émissif **par son nom** : tel quel, rien ne serait habillé et
   surtout **rien ne pourrait s'éteindre**. Précédent applicable : `foreign_materials` de
   `hull_detail.gd`, ajouté pour la Spectre-9 D.
2. **Onze images embarquées par pièce** (atlas 2048² pour trois familles de métal, 1024²
   pour l'énergie). Le Long Cortège est en PBR par facteurs, **zéro image**, et son harnais
   échoue le build si une texture apparaît.
3. **Mille trois cents nœuds nommés en clair avec suffixes `.001`**. Le moteur adresse ses
   marqueurs par leur nom ; il faut un contrat de noms, pas un inventaire.

### Le contrat de mariage, déjà écrit par l'auteur du berceau

C'est le meilleur cadeau de la livraison, et il faut le relire sur le binaire avant de s'y
fier (`pratique-la-cote-vient-de-l-asset`) :

- unités métriques, **+Z haut**, axe longitudinal **Y**, sortie du moteur vers **+Y** ;
- le moteur se pose **sans rotation, à (0 ; 1 ; 3,7) m** dans le repère Blender du berceau ;
- les quatre semelles magnétiques portent à **Z = 0,89 m** ;
- **42 repères nommés, 20 mécanismes animés** ; prises de puissance, ancrages, ruptures VFX
  et appuis inférieurs ont **quatre repères distincts chacun** ;
- le `.glb` est en **Y-up** (conversion glTF standard) : le décalage de montage doit être
  converti côté moteur ;
- clips à 30 im/s ; la pose finale de `Liberation` **est** le début de `Berceau_vide`.

### Les cotes qui contraignent tout — mesurées ce jour

| Cote | Valeur | D'où elle vient |
|---|---|---|
| Cadre visible, vertical | plan `y` de **−7,72 à +12,28** | `GameplayPlane.visible_frame()`, caméra réelle |
| Cadre visible, latéral | **\|x\| ≤ 20,37** à 16:9 | idem |
| Où le joueur peut aller | **\|x\| ≤ 14**, `y` ∈ [−8, +8] | `GameplayPlane.BOUNDS` |
| Largeur d'un groupe livré | **11,195 m** (berceau) | bbox du `.glb` |
| Trois groupes côte à côte | **33,6 m** | 3 × 11,195 |
| Un ancrage | **2,4 × 1,4 × 1,2 m** | planche `asset3` |
| La Spectre-9 | **2,46 m** de long | `ADR-0008` |
| Densité écran | **45,8 px/m** | `ADR-0045` |

Deux lectures immédiates :

- **Un ancrage fait exactement une longueur de chasseur**, soit ~110 px à l'écran. La
  consigne « pas de weakpoint de 10 pixels » (spec §7) est tenue par la planche telle quelle.
- **Trois groupes font 33,6 m de large pour un joueur qui n'en couvre que 28.** Les ancrages
  extérieurs des moteurs latéraux tomberaient **hors de portée**. C'est la décision D2.

---

## LOT 0 — Les décisions, avant une ligne de code

Aucune n'est un détail d'implémentation : chacune change ce qu'on construit.

### D1 — ⚠️ Le lore dit aujourd'hui le contraire de cette phase

`docs/lore/NULL_CHOIR.md:447` :

> « Il ne peut pas être détruit dans le niveau 2 — il continue sa route, et c'est ce qui doit
> rester de lui. »

Et `cortege_root.gd:385` le répète en tête de la fin de niveau. La spec, elle, demande
d'arrêter le vaisseau avant qu'il n'atteigne des zones sensibles.

**Les deux se réconcilient, mais il faut l'écrire** : arracher ses moteurs ne le détruit pas,
ça l'**échoue**. Il ne coule pas, il ne se rend pas, il ne meurt pas — il dérive. C'est
peut-être un meilleur lore que l'ancien, et c'est exactement pour ça qu'il faut un ADR : le
dépôt ne peut pas porter les deux phrases en même temps.

→ **ADR-0049 — *Le Cortège n'est pas coulé, il est échoué*.** Amende `NULL_CHOIR.md`, la fin
de `cortege_root.gd`, et verse la spec dans `docs/`.

### D2 — La poupe est plus large que le joueur ne peut aller

Trois groupes livrés font 33,6 m ; `BOUNDS` en fait 28. Trois issues, à trancher **sur
capture**, pas sur avis :

| Option | Ce qu'elle coûte |
|---|---|
| **a. Resserrer les groupes** (chevauchement des berceaux, ~9,3 m d'entraxe) | change la silhouette de la planche ; le plus simple, aucun code |
| **b. Réduire l'échelle** des deux assets à ~0,83 | l'ancrage tombe à 2,0 m, encore lisible ; touche le mariage moteur/berceau |
| **c. Élargir `BOUNDS` pour cette phase** | `GameplayPlane.use_bounds()` existe (précédent : la chambre du réacteur) — **mais `MAX_BOUNDS` plafonne à 28 de large, et c'est lui qui dimensionne la grille de collision des balles.** Le plus cher |

**Recommandation : (a), et (b) en secours.** Le concept montre les trois moteurs jointifs ;
l'espace entre eux n'est pas un livrable.

### D3 — Où passe l'aveu de Lyra

`survey_end` — « l'instant où Lyra avoue avoir lu le dossier du pilote » — est décrit dans
`VOX-0005` comme **la réplique qui commande toutes les autres** du niveau. Elle se joue
aujourd'hui à la fin du survol, c'est-à-dire exactement là où cette phase s'insère.

Trois places possibles : avant la poupe (l'aveu clôt la traversée, les moteurs sont un
épilogue), après le troisième moteur (l'aveu clôt le niveau), ou pendant le silence du §17.

**Recommandation : après**, dans les 5 à 8 s de respiration. Le silence du §17 est écrit
pour ça — mais c'est une décision d'auteur, pas une déduction.

### D4 — La texture entre-t-elle au niveau 2 ?

Les deux assets arrivent avec 11 images chacun ; le Long Cortège est à zéro par harnais.
`ADR-0047` autorise un atlas cuit à **remplacer** la palette. Décider : on garde les atlas
livrés (et on lève le harnais pour les kits de poupe), ou on repasse les pièces en PBR par
facteurs comme le reste du niveau.

**Recommandation : PBR par facteurs pour le LOT 1 à 4** (les boîtes grises n'en ont pas
besoin), **et arbitrage au LOT 6, sur capture comparée.** C'est gratuit de reporter, et ça
évite de payer 400 Mo de LFS avant d'avoir vu la différence à 45,8 px/m.

### D5 — Le plafond de vol

Un moteur livré fait **5,49 m de haut**. Posé sur le pont médian (`y = −4,99`), il crève le
plan de vol de **0,50 m** — le défaut exact qu'`ADR-0034` et le harnais des tourelles
interdisent. La poupe n'est pas le corridor : soit ses ponts descendent, soit les moteurs
sont couchés, soit ils sont mis à l'échelle. **À mesurer au LOT 1**, sur le binaire.

---

## LOT 1 — La phase existe, en boîtes grises, et elle se termine

**Objectif : la boucle complète jouable, testable et finie, sans un seul asset final.**
Trois cubes pour les moteurs, trois plaques pour les berceaux, six cubes pour les ancrages.

C'est la leçon de la cellule témoin : un lot qui commence par les assets se retrouve avec de
beaux objets et pas de jeu.

1. `scripts/gameplay/cortege_stern.gd` — la phase, montée par `CortegeRoot` sur
   `survey_finished` au lieu de la victoire immédiate.
2. `resources/data/cortege_stern_tuning.gd` — Resource typée avec `validate()`
   (spec §31) : PV d'ancrage, durées d'état, fenêtres, directions de dérive.
   **Aucun nombre de gameplay en dur.**
3. La machine à états par moteur : `ACTIVE → DAMAGED_1 → DAMAGED_2 → DETACHING → DETACHED`,
   fonction pure et testable sans arbre.
4. La fin : troisième moteur détaché → respiration → rapport de mission.
5. Les quatre répliques de Lyra (spec §18) — texte, `VOX-0006`, `.ogg`, `hold` mesuré.
   ⚠️ Le lot est indivisible (leçon `pratique-retourner-une-regle-retourne-la-narration`).

**Recette** : `check.sh` vert ; la phase se traverse en `--goto-level=long_cortege
--cortege-from=5` ; un drapeau `--goto-stern` pour ne pas payer 4 minutes de défilement à
chaque essai ; le journal raconte les cinq états.

## LOT 2 — Les ancrages : la seule cible

1. `CortegeAnchor` — pièce destructible, hitbox **depuis la Resource, jamais depuis le
   mesh** (`ADR-0034`), fenêtre de ciblage = `target_span` comme tout le reste du niveau
   (acquis de ce jour).
2. Trois ancrages par moteur latéral, trois ou quatre au central (spec §7).
3. ⚠️ **Le moteur ne prend AUCUN dégât** — c'est un critère d'acceptation, donc un test :
   tirer sur le corps moteur ne doit rien produire.
4. Les verrous centraux ne s'exposent qu'après les deux latéraux (planche maîtresse,
   spec §14).
5. Retour de destruction : explosion, étincelles, socket VFX de la planche `asset3`.

**Recette** : un test par transition d'état ; une capture par état (`INTACT`, `ENDOMMAGÉ`,
`OUVERT`) — les trois de la planche.

## LOT 3 — L'arrachement

La récompense. **Trajectoire déterministe, jamais de physique** (spec §11).

1. Séquence chronométrée du §9 (T+0 / 0,2 / 0,5 / 0,8 / 1,2 / 1,5–4 s).
2. Trois directions distinctes (§10) : haut-gauche, haut-droite, et le central plus haut
   avec rotation.
3. **Le berceau reste, vide, et c'est la preuve** (§21, critère 7).
4. Garde dure : le moteur détaché **ne peut pas toucher le joueur** ni rester coincé —
   testable sur la trajectoire, sans rendu.

**Recette** : capture à T+0,5 / T+1,2 / T+3 s pour chacun des trois ; le test de trajectoire
échantillonne le trajet et vérifie qu'il ne croise jamais `BOUNDS`.

## LOT 4 — Les flammes, et la poussée comme gameplay

Le lot où il faut **surinvestir** (spec §20) : « mieux vaut un moteur simple avec une
excellente propulsion animée qu'un moteur ultra détaillé avec une flamme médiocre ».

1. La flamme en couches (§5) : cœur étroit, corps magenta, filaments, particules,
   turbulence. Jamais constante : longueur ±10–15 %, largeur ±5–10 %.
2. La flamme **suit l'état du moteur** — irrégulière en `DAMAGED_1`, intermittente en
   `DAMAGED_2`, instable pendant la dérive.
3. La zone de danger (§6) et son **préavis de 300–500 ms** : montée de luminosité, son,
   poussée. Pas de bullet hell — du mouvement.
4. Le pattern du central (§15) : NORMAL → CHARGE → GROSSE POUSSÉE → EXTINCTION 1 s.

⚠️ **Coût GPU mesuré à chaque étape**, trois relevés de chaque côté : trois flammes en
couches sur un plan de jeu déjà chargé, c'est le poste qui peut faire dérailler le budget.

## LOT 5 — L'intégration des deux assets livrés

Suit `howto-integrer-un-modele-tiers.md` et `ADR-0048` (un modèle tiers entre avec sa
source).

1. **Audit** : cotes relues sur le binaire, contrat de mariage vérifié, clips joués.
2. **Réduction** : cible à fixer par mesure, ordre de grandeur **15 à 25 k triangles par
   groupe** (le Long Cortège entier en fait 49 458). Ce qui disparaît en premier est ce qui
   ne se voit pas à 45,8 px/m.
3. **Contrat de matériaux** : `AA_*`, et surtout `AA_Emissive_Engine` sur ce qui doit
   s'éteindre — sans quoi l'extinction ne prend pas, et **rien ne le dira**.
4. **Contrat de noms** : marqueurs d'ancrage, sockets VFX, prises de puissance.
5. **Clips** : `Fonctionnement` / `Endommage` / `Detachement` côté moteur,
   `Intact` / `Sous_contrainte` / `Liberation` / `Berceau_vide` côté berceau — câblés sur la
   machine à états du LOT 1. ⚠️ Un glTF **n'exécute pas les drivers Blender** : vérifier que
   les clés sont cuites.

**Recette** : `./scripts/build-hull.sh --check` déterministe ; rendu **et regardé** à la
caméra du jeu (`ADR-0006`), alimenté **et** détaché ; coût GPU avant/après réduction.

## LOT 6 — La poupe elle-même

La silhouette doit **casser** avec le corridor (spec §2) : bien plus large, plus massive,
relief vertical marqué. C'est le lot qui décide de D2 et D5, sur capture.

Brief de forge, alimenté par les planches `asset5` à `asset9` déjà fournies (conduites,
flexibles, pylône, tour thermique, bride, cryogénie, déflecteur, collier, refroidissement,
anneau de maintenance).

## LOT 7 — Ce qui manque encore

À briefer dans cet ordre de valeur :

1. **L'ancrage destructible** (`asset3`) — c'est la cible du jeu, elle passe avant tout le
   reste. Trois états, pièces mobiles, socket VFX ; la planche est déjà cotée et dit
   « game-ready ».
2. **Le bras d'ancrage** (`asset4`).
3. **La conduite énergétique** (`asset5`, `asset8`) — elle doit rompre.
4. Le reste de l'habillage, au fil de l'eau.

⚠️ **Un lot livré par l'agent tiers ne remplace un lot de la forge que s'il est mesuré
meilleur** — même critère que pour les deux binaires ci-dessus.

## LOT 8 — Le silence

Cinq à huit secondes de respiration (§17), **aucune vague**. Trois berceaux vides, quelques
arcs, presque plus de magenta, pas de flamme. Le blackout partiel de la poupe (§16).

C'est le lot le plus court et celui qui décide si toute la séquence porte : le contraste
avant/après est le livrable.

---

## Vérification de bout en bout

```bash
./scripts/check.sh                                    # à chaque commit
./scripts/build-hull.sh --check <piece>               # déterminisme après tout changement de kit
./scripts/play.sh -- --goto-level=long_cortege --goto-stern   # drapeau à créer au LOT 1
python3 tools/inspect-capture.py /mnt/c/tmp/aegis-ascendant/capture.png --at X,Y --size 700x420
```

⚠️ Pièges déjà payés, et qui coûteront encore ici : `deploy-win.sh` **ne ré-exporte pas** ;
un `grep` dans le tuyau avale une porte rouge ; le FPS d'un lancement automatisé ne mesure
rien (temps GPU par image) ; effacer `capture.png` **avant** chaque lancement ; un journal
vert ne valide **aucune** géométrie.

## Risques nommés

- **Le budget triangles** est le risque n°1, et il est chiffré : ×26 le niveau actuel si on
  pose les binaires tels quels. Le LOT 5 doit passer avant toute décision de contenu.
- **Le poids LFS** : 400 Mo pour six pièces, contre un dépôt qui compte aujourd'hui ses
  mégaoctets.
- **La lisibilité des ancrages** : ils font une longueur de chasseur, mais sur une poupe
  chargée de greebles, un ancrage peut disparaître dans le décor. Le garde-fou est le
  critère §21 : une capture doit suffire à dire *les attaches sont destructibles*.
- **Le plafond de vol** (D5) : 0,50 m de dépassement mesuré, sur une pièce qu'on ne peut pas
  simplement enfoncer sans casser le mariage moteur/berceau.
- **La fin actuelle est aussi la fracture Lyra/pilote** (D3) : déplacer l'aveu sans le
  décider, c'est perdre le seul moment d'acte I qui coûte quelque chose.
- **Deux moitiés qui ne valent rien séparées** : l'arrachement sans la flamme est un cube
  qui glisse ; la flamme sans l'arrachement est un fond d'écran. LOT 3 et LOT 4 se jugent
  ensemble.

## Hors périmètre

Refonte du corridor (tronçons 1 à 5), de la citadelle, du niveau 1 ; nouveaux ennemis (la
spec §19 en demande **moins**, pas plus) ; toute simulation physique ; le rattrapage des
coques déjà livrées.
