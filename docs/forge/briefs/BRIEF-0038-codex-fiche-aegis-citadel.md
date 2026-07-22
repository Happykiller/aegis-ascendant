# BRIEF-0038 — Fiche technique de l'Aegis Citadel, pour le bestiaire

- **Statut** : intégré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-22

## Objectif

Produire la **fiche technique** (désignation, classe, constructeur, masse, équipage, statut,
notice) de l'**Aegis Citadel**, sixième entrée du bestiaire.

Livrable unique : **un fichier markdown de données**, pas d'asset binaire, pas de code.

## Contexte

BRIEF-0037 a livré les cinq premières fiches du bestiaire
(`docs/forge/output/codex_hull_datasheets.md`) — **lis-le d'abord** : ta fiche doit s'y raccorder
en ton, en échelle et en vocabulaire. L'opérateur réclame maintenant le **vaisseau mère** :
c'est la seule coque majeure du jeu qui manquait au catalogue.

Elle est d'une **autre nature** que les cinq premières, et c'est le cœur de ce brief.

L'Aegis Citadel n'est pas un objet de combat au sens du code : elle n'a **ni points de structure,
ni vitesse, ni cadence de tir** dans les Resources de gameplay — elle n'est pas destructible, elle
apparaît pour la séquence d'appontage puis devient le corps piloté du joueur (spec §6.5, §12). Sa
fiche n'affichera donc pas les mêmes lignes que celle d'un chasseur : à la place des trois jauges
de combat, l'écran compte ses **équipements** directement sur la coque (tourelles, balises,
batteries lourdes).

Ce que l'écran mesure ou compte tout seul, et qui n'est **pas de ton ressort** :

| Donnée | Valeur mesurée |
|---|---|
| Envergure | 19,63 m |
| Tirant | 5,30 m |
| Longueur | 16,60 m |
| Triangles | 62 712 |
| Tourelles | 6 (marqueurs `Turret_01..06`) |
| Balises | 3 (marqueurs `Beacon_01..03`) |
| Batteries lourdes | 2 (marqueurs `Muzzle_Battery_L/R`) |
| Baie d'appontage | 1 (marqueur `Dock_Entry`) |

Charte applicable : `docs/forge/CHARTE_CREATIVE.md` §1 (ton), §2 (canon — **Aegis Citadel** et
**Arsenal Orbital Talvern** y figurent déjà, ne pas les renommer), §3 (palette Helios).

## Ce que la coque raconte déjà, et qu'il faut respecter

Elle est décrite au canon comme **prisme axial, deux bras-batteries, noyau énergétique**. Le code
en dit plus, et ce sont des faits, pas des suggestions :

- elle **se déplace** (elle glisse vers une position de combat) — ce n'est pas une station fixe ;
- elle porte une **baie d'appontage** où le chasseur du joueur se pose ;
- ses six tourelles et ses trois balises sont des **pièces mobiles animées**, et ses émissifs
  « respirent » lentement (`scripts/fx/citadel_life.gd`) ;
- **le joueur la pilote** dans la phase forteresse : c'est un poste de commandement habité, pas
  un drone.

## Contraintes

- **IP** — interdits habituels de `CLAUDE.md` : aucun nom ni élément identifiable d'une licence
  existante.
- **Échelle** — 19,63 m d'envergure. C'est une **corvette**, pas un cuirassé de plusieurs
  kilomètres. Comme pour le Specter-9 dans BRIEF-0037, traite l'échelle de front dans la classe et
  la notice plutôt que de la démentir par un chiffre. La masse doit rester cohérente avec le modèle
  de BRIEF-0037 (grandes coques creuses : ~0,3 t/m³ de boîte englobante ; la citadelle est un
  prisme plein, donc plutôt plus dense qu'un Leviathan).
- **Registre** — allié, donc **dossier interne Helios**, comme le Specter-9 : constructeur nommé,
  ton sec et factuel, et un **équipage non nul** (c'est un bâtiment habité, à la différence de
  toutes les coques du Null Choir).
- **Statut** — la progression des cinq premières fiches va de `EN SERVICE ACTIF` (allié) à
  `PRIORITE ABSOLUE` (menace maximale). Le statut de la citadelle appartient au registre allié.

### Contraintes typographiques — impératives (ADR-0012)

Identiques à BRIEF-0037, et vérifiées par un test automatique
(`tests/unit/test_codex_entries.gd::test_uppercase_fields_are_pure_ascii`) : une seule lettre
accentuée dans un champ court fait **échouer `check.sh`**.

- Champs courts (`designation`, `classe`, `constructeur`, `statut`) : **ASCII pur, sans accent**.
- `notice` : casse normale, minuscules accentuées bienvenues, pas de capitale accentuée.
- Aucun caractère `●`, `■`, `→`, `—`. Apostrophes droites uniquement.
- Longueurs : `classe` ≤ 34, `constructeur` ≤ 28, `statut` ≤ 22, `notice` ≤ 320 caractères.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `docs/forge/output/codex_citadel_datasheet.md` | la fiche, **même gabarit de tableau** que `codex_hull_datasheets.md` |

Les sept champs, nommés exactement comme dans BRIEF-0037 : `designation`, `classe`,
`constructeur`, `masse_t`, `equipage`, `statut`, `notice`.

Ajoute une courte section **« Cohérence »** (3 à 5 lignes) : comment ta masse se place face aux
cinq autres, et pourquoi l'équipage retenu est plausible pour ce volume.

## Provenance

Document de données, pas un asset chargé par le moteur : **pas de ligne dans
`assets/licenses/ASSET_PROVENANCE.csv`**.

## Critères d'acceptation

- [ ] Les sept champs sont présents et nommés exactement comme dans BRIEF-0037.
- [ ] Aucun caractère non-ASCII dans les quatre champs courts.
- [ ] `equipage` > 0, et la notice justifie implicitement ce chiffre.
- [ ] La masse se place de façon cohérente face aux cinq masses de BRIEF-0037 (0,16 t à 44,6 t).
- [ ] La notice mentionne ce qui distingue vraiment cette coque : elle se déplace, elle apponte,
      et le joueur finit par la piloter.
- [ ] Le nom canonique **Aegis Citadel** est repris tel quel.

## Hors périmètre

- **Ne pas** toucher au code, aux scènes ni aux `.tres`.
- **Ne pas** proposer de points de structure, de vitesse, de cadence de tir ni de nombre de
  tourelles : l'écran les compte sur la coque, et une valeur concurrente dans un document créerait
  une deuxième source de vérité.
- **Ne pas** réécrire les cinq fiches de BRIEF-0037.
- **Ne pas** produire d'image ni de prompt de génération.
