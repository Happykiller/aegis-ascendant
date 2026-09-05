# Chantier — la forge remise à plat, et le Specter-9 v4 pour l'éprouver

- **Ouvert le** : 2026-09-05
- **Décisions** : `ADR-0045` (le rendu sort du filtre), `ADR-0046` (une coque naît animée),
  `ADR-0047` (l'atlas cuit par la forge, à écrire), `ADR-0048` (la livrée, à écrire)
- **Planche cible** : `assets/reference/concepts/specter_9_concept_sheet_2026-09-05.png`

## Pourquoi ce chantier

L'opérateur, 2026-09-05 : le jeu « fait jeu de débutant », « une représentation de jouets basiques
pour enfants ». Puis, après avoir vu la troisième coque : « peut-être que le problème ne vient pas
du modèle, mais de **notre forge et de notre méthodologie** ».

C'est le bon diagnostic, et la mesure le confirme : le rendu studio de la forge était propre, c'est
la chaîne de sortie qui le détruisait (`ADR-0045`), et le gréement d'animation se refaisait à la
main à chaque coque (`ADR-0046`).

## Le verdict de l'opérateur sur les trois coques existantes

À traiter comme des **anti-cibles** du v4 — ce sont des jugements de produit, pas des impressions
passagères :

| Coque | Verdict | Ce qu'il faut en tirer |
|---|---|---|
| `specter_9` (v1, BRIEF-0021/0033/0035/0036) | « **on dirait une baleine**, le vaisseau avec son gros ventre dessous » | le volume ventral est trop plein. La table `BELLY` de `build_specter_9.py` porte ce défaut |
| `specter_9_b` (v2) | « elle est **jolie, mais trop plate, trop simpliste** » | modèle tiers, monobloc, un seul matériau, aucune pièce mobile. Jolie de loin, vide de près |
| `specter_9_c` Talvern (v3, BRIEF-0098) | « un **essai avec Fable** pour voir s'il pouvait générer mieux » | l'essai a servi : il a prouvé que le modèle n'était pas le facteur limitant |

⚠️ **Le v4 ne repart d'AUCUNE des trois.** Consigne explicite : « on part sur une quatrième version
toute neuve en repartant de zéro ». C'est l'inverse exact de `BRIEF-0098` l.33 (« Repars de ses
cotes, pas de zéro »), et c'est cette ligne-là qui avait produit les écarts à la planche nommés
dans `BRIEF-0098-report.md` §9.1.

## La mesure qui autorise à suivre la planche

Facteur d'échelle : **2,46 / 12,6 = 0,19524 m par mètre-planche**.

| Cote | Planche | × 0,19524 | Contrat | Écart |
|---|---|---|---|---|
| Longueur | 12,6 m | 2,4600 m | 2,46 | 0 % |
| Largeur | 8,9 m | **1,7376 m** | 1,75 | **−0,71 %** (tolérance ±3 %) |
| Hauteur | 3,4 m | **0,6638 m** | ≤ 0,72 | sous plafond |

**La silhouette de la planche tient dans le contrat de gameplay sans le toucher.** Il n'existe donc
aucun argument technique pour s'en écarter — c'était le dernier prétexte.

## ⛔ La v3 est annulée (2026-09-05)

L'opérateur, après avoir vu la coque peinte en jeu : « *c'est très moche. Autant sur la forme
que sur les textures* […] *c'est un échec* ». `specter_9_c` est retirée du dépôt ; le jeu
revient à deux coques. Voir `ADR-0044`, annulé en tête.

Le verdict porte sur **la forme ET la matière**. Il tranche donc aussi une question que ce
plan laissait ouverte : le micro-contraste que l'atlas devait apporter ne s'est pas mesuré
(σ 7×7 inchangée face à l'état d'avant atlas), et l'œil confirme la mesure. **L'atlas seul ne
suffit pas à faire un beau vaisseau** — il rend la livrée possible, il ne dessine pas la coque.

## Ce qui a été mesuré, et ce que ça a coûté

| Lot | Résultat |
|---|---|
| **Retrait du filtre** | ✅ **Gain majeur.** Niveaux distincts par canal ×5 à ×7, luminance de coque +7,2 % (bestiaire) et +14 % (combat), écrêtage 3,6 % → 0,1 %, GPU bestiaire −68 % sur la borne basse. Lisibilité des tirs : empreinte chromatique +11 % (cyan) et +24 % (corail) — aucune régression. |
| **Atlas peint** | ⚠️ **Mécanisme acquis, résultat refusé.** La chaîne fonctionne de bout en bout et deux vrais défauts ont été trouvés et corrigés (espace de couleur linéaire→sRGB, rainure comptée deux fois). Mais la variance locale n'a jamais monté, et l'opérateur a refusé le rendu. L'outillage survit, la coque non. |
| **Réflexions d'environnement** | ❌ **Négatif, écarté.** Deux passes, effet monotone dans les deux sens : le ciel aplatit la coque (variance −0,76 %) sans produire une seule haute lumière (p99 immobile sur trois builds). Un dégradé procédural lisse ne fabrique pas de modelé. Détail dans `ADR-0045`. |

**La leçon d'ordonnancement** : les deux lots les moins chers ont donné l'un tout, l'autre rien. Le
« plastique » ne venait pas de l'éclairage — il vient de ce qu'il n'y a **rien à voir** sur la
surface : pas de ligne de panneau peinte, pas d'usure, pas de livrée. C'est le lot d'atlas qui
porte le sujet, et il n'est plus contournable.

## Ordre des lots

Le v4 est le **test** de la nouvelle forge, pas son point de départ. Le construire avant les
outils, ce serait produire une quatrième déception avec la méthode qui a produit les trois
premières.

1. **Rendu** — `ADR-0045` : retrait du filtre, luminosité migrée, `[rendering]` rempli, lumière et
   matière (réflexions d'environnement, occlusion, spéculaire).
2. **Gréement** — `ADR-0046` : vocabulaire de nœuds, points d'attache parentés, plafonds mesurés et
   **exportés** (fin des constantes recopiées dans `ship_flight.gd`), plume dérivée de la gorge.
3. **Matière** — `ADR-0047` : dépliage en atlas packé, cuisson déterministe d'albédo/normal/ORM.
4. **Livrée** — `ADR-0048` : bandes, filets, matricule « 09 ».
5. **Le v4** — `BRIEF-0099`, cotes mesurées sur la planche, critère d'acceptation qui **rejette**
   un écart de silhouette au lieu de le documenter.

## Ligne de base, relevée avant tout changement (2026-09-05)

- `./scripts/check.sh` **vert** : 883 méthodes, 6 771 assertions, 0 échec.
- Empreinte témoin : `md5sum build/windows/AegisAscendant.pck` = `c1c0db91429834c7183c4b771dbad4c9`.
  **Elle doit différer** après chaque lot, sinon on mesure l'ancien binaire.
- Captures 1:1 : `/mnt/c/tmp/aegis-ascendant/baseline-codex-talvern-run{1,2,3}.png` et
  `baseline-combat-graybox-run{1,2,3}.png`.
- Temps GPU par image, 60 Hz, trois tirs :
  - bestiaire **2,407 / 3,030 / 3,591 ms**
  - combat **2,435 / 2,985 / 3,935 ms**

⚠️ **Dispersion de ~1,5 ms, soit la moitié de la valeur basse.** Les deux écrans se recouvrent
entièrement : à ce niveau de bruit, un écart inférieur à ~1,5 ms n'est pas décidable sur trois
tirs. Comparer sur la **borne basse** de chaque série, ou tirer davantage.

⚠️ Et le fait qui autorise tout le reste : **le jeu consomme 2,4 à 3,9 ms sur un budget de
16,7 ms**. Il reste les trois quarts de l'image. L'antialiasing, les réflexions et l'occlusion ont
la place ; ce n'est pas la performance qui bornait la qualité.
