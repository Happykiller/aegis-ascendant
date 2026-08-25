# BRIEF-0082 — L'intérieur du noyau du Pale Leviathan : passerelle et réacteur

- **Statut** : livré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-25

## Objectif

Modéliser **l'intérieur du noyau ouvert** du Pale Leviathan en `.glb` PBR : une **arène vue du
dessus**, bordée de parois, traversée d'une **passerelle**, avec un **réacteur au centre** — la
cible unique de la phase. C'est un décor **autonome**, pas une pièce de la coque du boss.

## Contexte

Le boss final se joue en trois cycles (`ADR-0021`) : briser l'armure, puis **plonger dans le
noyau**. Verdict de l'opérateur au playtest du 2026-08-25, sur la plongée :

> « Ce n'est pas jouable. Visuellement c'est moche, on n'a pas la sensation que le noyau s'ouvre et
> qu'on rentre dedans — plus qu'il change, et qu'on perd de vue le vaisseau qui est dans la sphère.
> Ce n'est pas ce que j'entendais par rentrer dedans. »

Ce qu'il y a aujourd'hui, et qu'il faut remplacer : une `SphereMesh` de 7 m **retournée**,
construite au vol par le code autour du boss. Le chasseur ne va nulle part ; on dessine une bulle
autour de tout et la caméra glisse. D'où la sensation, exacte, que « ça change » au lieu qu'on entre.

**La décision prise** : l'intérieur devient une **zone dédiée**. On zoome à fond dans l'ouverture,
le chasseur s'y rend, et l'on découvre un vrai lieu — vu du dessus, comme tout le jeu.

⚠️ **Le mécanisme d'ouverture de la gueule N'EST PAS dans ton périmètre** (ce sera `BRIEF-0083`, sur
la coque du boss). Toi, tu livres **le lieu qu'on découvre une fois entré**.

### Le piège précis que ce brief doit éviter

Le document de conception `BOSS_PALE_LEVIATHAN.md` §6 décrivait déjà un puits intérieur, et la coque
livre les pièces qui portent ses noms : `Ring_01..05`, `Tunnel_End`, `Maw_Center`, `Heart`. **Elles
existent par le nom, jamais à l'échelle** — mesuré dans le `.glb` :

| Pièce livrée | Dimensions réelles |
|---|---|
| `Ring_01` → `Ring_05` | **0,33 m** → **0,24 m** de large, 0,14 m de haut |
| `Heart` | **0,63 × 0,31 × 0,56 m** |
| Chasseur `Specter-9` (référence) | **1,29 × 0,65 × 2,41 m** |

Les « cinq anneaux qu'on franchit » sont trois fois plus petits que le vaisseau censé les traverser.
Le contrat de noms avait été respecté, l'échelle jamais vérifiée, et **rien ne l'a signalé** — ni le
compte de triangles, ni le contrat d'export, ni le rendu. **C'est l'erreur à ne pas refaire :
mesure ton livrable contre le chasseur, pas contre lui-même.**

**Lire d'abord** : `docs/forge/CHARTE_CREATIVE.md`, `docs/decisions/ADR-0008-pipeline-3d-blender.md`,
`docs/decisions/ADR-0011-detail-des-coques-budgets-et-textures.md`,
`docs/decisions/ADR-0021-le-leviathan-en-cycles.md`, puis
`tools/blender/lib/aegis_kit.py` — **kit réutilisé SANS modification** (il est gelé, cf. plan daté).
Modèle de script le mieux instrumenté : `tools/blender/build_leech_drone.py`.

## Contraintes

### Échelle — la contrainte n°1

Le plan de jeu fait **28 × 16 m** (`GameplayPlane.BOUNDS` : X de −14 à +14, Z de −8 à +8). L'arène
intérieure doit **remplir ce cadre**, réacteur au centre du monde.

- Enveloppe visée : **30,0 × 18,0 m** au sol (X × Z), un peu plus large que les bornes pour que les
  parois débordent du cadre et qu'on n'en voie jamais la fin.
- Hauteur totale ≤ **4,0 m** (Y). Le jeu se lit du dessus : tout ce qui monte cache le vaisseau.
- **Le couloir jouable doit rester libre** : aucune géométrie au-dessus de Y = 0,9 m dans le disque
  de rayon 11 m centré sur l'origine, hormis le réacteur. Le chasseur vole à Y ≈ 0.

### Ce qu'il faut modéliser

1. **Le réacteur central** (`Reactor`) — la cible. Massif, lisible d'un coup d'œil comme *la chose à
   tirer* : **3,5 à 4,5 m de diamètre**, posé au centre, émissif en son cœur. Il doit se distinguer
   du décor par la **forme et la valeur**, pas seulement par la couleur (le joueur arrive dans un
   rideau de balles).
2. **La passerelle** (`Catwalk_01..04`) — quatre travées qui rejoignent le réacteur depuis les
   parois, à ~90°. Elles donnent l'échelle et le sens de lecture ; elles ne bloquent pas le vol.
   Épaisseur ≤ 0,5 m, elles se lisent comme un plancher, pas comme un mur.
3. **Les parois** (`Rim_01..06`) — la bordure du noyau ouvert, en segments. Elles ferment le cadre.
   Hauteur 2,5 à 4,0 m, inclinées vers l'intérieur : on doit sentir qu'on est **dans** une cavité.
4. **Le sol** (`Floor`) — un fond sombre, structuré (nervures, plaques), qui ne mange pas la lisibilité.

### Points d'ancrage (contrat de noms — le code s'y accroche)

| Nom | Rôle |
|---|---|
| `Reactor_Core` | point exact que le code prend pour centre de hitbox du réacteur |
| `Entry_Point` | où le chasseur apparaît en arrivant, bord bas de l'arène |

### IP, palette, DA

- **IP** : aucun nom, silhouette ou élément identifiable de Macross, Robotech ou d'une autre licence.
  L'exception `ADR-0014` porte sur le **Specter-9 uniquement** et ne s'étend pas ici.
- **Palette** : celle du Pale Leviathan — blancs osseux, magenta `d93d9c`, violets profonds
  désaturés. ⚠️ **Le décor doit RECULER pour que la cible avance.** L'erreur déjà payée sur ce boss
  (mesurée, consignée) : la chambre était rouge-violet saturé (R−G 41,9) **et** le flux aussi (31,5)
  — dix points d'écart, donc aucun contraste entre ce qu'il faut tirer et le lieu où l'on se trouve.
  Vise **au moins 25 points d'écart R−G** entre `Reactor` et l'ensemble sol + parois.
- Matériaux `AA_Hull`, `AA_Emissive_Engine`, `AA_Greeble` (cf. ADR-0011).

### Techniques

- Godot 4.7, `.glb` PBR, export **déterministe** (même entrée → même sha256).
- Budget : **≤ 22 000 triangles** pour l'ensemble.
- ⚠️ **UV OBLIGATOIRES sur 100 % des primitives.** Quatre coques du dépôt sont intexturables faute
  de `_triangulate_ngons()` + `box_project_uv()` : le dépliage ne s'invente pas, et aucun importateur
  ne le devine. Vérifie-le **à l'export**, pas au rendu.
- ⚠️ `ak.inset_panel()` est un **no-op sur un maillage fraîchement bâti** : `inset_region` lit une
  normale de face nulle tant que `normal_update()` n'a pas été appelé. Si tu t'en sers, appelle
  `normal_update()` **avant**, dans ton script — **pas** dans le kit, qui est gelé.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_core_interior.py` | script de génération, déterministe, autonome |
| `assets/imported/models/bosses/core_interior.glb` | le décor exporté |
| `docs/forge/output/BRIEF-0082-planche-quatre-vues.png` | planche de recette (dessus, 3/4, coupe, dessus avec le chasseur à l'échelle) |
| `docs/forge/output/BRIEF-0082-report.md` | mesures, sha256, écarts, choix assumés |

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv` pour `core_interior.glb` : origine
« production interne asset-forge », brief `BRIEF-0082`, licence projet, sha256 mesuré.

## Critères d'acceptation

- [ ] Enveloppe au sol entre **28 × 16 m** et **32 × 20 m**, hauteur totale ≤ 4,0 m — **mesurées**.
- [ ] **Aucune géométrie au-dessus de Y = 0,9 m** dans le disque de rayon 11 m, réacteur excepté.
- [ ] `Reactor` entre 3,5 et 4,5 m de diamètre.
- [ ] Points d'ancrage `Reactor_Core` et `Entry_Point` présents et correctement placés.
- [ ] Contrat de noms complet : `Reactor`, `Catwalk_01..04`, `Rim_01..06`, `Floor`.
- [ ] **UV sur 100 % des primitives**, vérifié à l'export et rapporté.
- [ ] ≤ 22 000 triangles.
- [ ] Export déterministe, sha256 rapporté.
- [ ] Écart **R−G ≥ 25 points** entre le réacteur et le sol/parois, **mesuré sur la planche**.
- [ ] La planche comporte **une vue de dessus avec le Specter-9 posé à l'échelle** — c'est la vue qui
      prouve que l'erreur des anneaux à 30 cm n'a pas été refaite.

## Hors périmètre

- **Le mécanisme d'ouverture de la gueule** (volets coulissants) : ce sera `BRIEF-0083`, sur
  `build_pale_leviathan.py`. Ne touche pas à la coque du boss.
- **Ne modifie pas `tools/blender/lib/aegis_kit.py`** — il est gelé par accord entre sessions.
- Aucune animation : le décor est statique, le code anime ce qui bouge.
- Aucune logique de gameplay, aucune hitbox : le code les pose depuis les points d'ancrage.
