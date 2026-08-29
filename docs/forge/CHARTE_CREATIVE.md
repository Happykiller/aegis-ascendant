# Charte créative — Aegis Ascendant

Bible de référence pour toute production créative (agent `asset-forge` et humains).
Extraite de la spec (§3, §10, §15, §24) ; en cas de conflit, la spec prime.
Les valeurs hex marquées *(normatif)* sont obligatoires ; les autres sont des repères.

## 1. Univers et ton

Space opera **militaire rétrofuturiste**, esthétique inspirée de l'animation japonaise des
années 1980 **en général** (jamais d'une œuvre précise) : silhouettes mécaniques fortes,
lignes tendues, accents lumineux, héroïsme lisible. Pas de photoréalisme : rendu stylisé,
cohérent, spectaculaire.

## 2. Canon (noms officiels — ne pas en créer d'autres sans brief)

| Élément | Nom | Nature |
|---|---|---|
| Coalition humaine | **Helios Vanguard** | défense interplanétaire des colonies |
| Chasseur du joueur | **Specter-9** | chasseur spatial léger triangulaire |
| Porte-chasseur | **Aurora Spear** | vaisseau de lancement du joueur |
| Forteresse mobile | **Aegis Citadel** | prisme axial, deux bras-batteries, noyau énergétique |
| Ennemi | **The Unison** — *l'Unisson* | Un système d'entretien qui a survécu à ses commanditaires : il cherche de la structure cohérente et l'archive. ⚠️ **Remplace « The Null Choir »**, rejeté par l'opérateur le 2026-08-28 (`docs/lore/NULL_CHOIR.md` §1). Les identifiants de fichiers gardent leur nom : le joueur ne les voit pas |
| Vaisseau-amiral ennemi | **The Pale Leviathan** | organo-mécanique, anneau incomplet, noyau visible. **Boss d'étape**, pas l'aboutissement de la campagne |
| Convoi (niveau 2) | **The Long Cortège** | 6,8 km, survolé de la proue à la poupe. Il **emporte** des structures entières, greffées sur son bordé — il ne livre pas bataille et **ne peut pas être détruit**. ⚠️ Ni « vaisseau-amiral » ni « flagship » : notre ennemi n'est pas une marine (`docs/lore/NULL_CHOIR.md`) |
| Mini-boss | **Graft Harvester** | trois bras, noyau central protégé. ⚠️ ex-« Choir Harvester » : il prélève et il greffe |
| Mine du champ | **Anchor Mine** | ⚠️ ex-« Choir Mine » : elle ancre et elle interdit une zone |
| Constructeur du Specter-9 | **Arsenal Orbital Talvern** | chantier Helios ; s'affiche dans le bestiaire (BRIEF-0037) |
| Navigatrice du joueur | **Lyra Vantella** | Instance de navigation d'Helios Vanguard ; **le seul personnage INCARNÉ** — le seul à avoir un visage à l'écran (ADR-0035, amendé). Sept autres personnes sont nommées dans `docs/lore/PERSONNAGES.md` ; aucune n'a de portrait |
| Monde d'origine | **Orvane** | La planète qu'on a quittée — évacuée, pas détruite. Le système d'arrivée est **Helios** ; ne pas confondre avec la coalition **Helios Vanguard** qui en tire son nom |
| Pilote (le joueur) | **Wren Adaire**, indicatif **Halyard** | ⚠️ **Lyra l'appelle par son indicatif, « Halyard »** (`ADR-0037`). Deux exceptions dans tout le jeu : « Wren » à l'appontage, « Adaire » à l'écran de défaite. Aucun visage à l'écran |

## 3. Palettes

### Helios Vanguard (allié)
- Blanc cassé `#EDEAE3` — coques
- Bleu profond `#1C2B5E` — panneaux
- Cyan `#3FD9E8` — lignes lumineuses, moteurs, HUD
- Or `#E4B54A` — accents, insignes
- Rouge sécurité `#C93A31` — marquages restreints

### The Null Choir (ennemi)
- Anthracite `#24252B` — coques
- Violet sombre `#452663` — segments
- Ivoire froid `#DDDCD2` — carapaces
- Magenta `#D93D9C` — lumières, armes
- Vert maladif `#7C9E52` — usage très limité

### Projectiles (lisibilité avant tout — spec Pilier B)
- Alliés : cyan / bleu / or
- Ennemis : rouge corail / magenta / orange — **toujours cœur lumineux + halo contrasté**
- Les valeurs hex normatives de gameplay (émissifs, fond, contrastes) sont définies par
  `docs/forge/output/graybox_palette.md` *(normatif, livrable BRIEF-0002)*.

### Bonus (couleur + forme + icône + son distincts — jamais la couleur seule)
| Bonus | Couleur | Forme repère |
|---|---|---|
| Power Core | jaune-or | losange |
| Shield Cell | cyan | hexagone |
| Missile Rack | orange | chevron |
| Orbit Drone | violet | anneau |
| Overdrive Shard | magenta | éclat |
| Score Prism | vert | prisme |
| Rescue Beacon | blanc | étoile |

## 3 bis. Personnages

⚠️ **CETTE SECTION N'EXISTAIT PAS, ET LE DÉPÔT N'AVAIT JAMAIS PRODUIT D'HUMAIN.** La charte ne
décrivait que des factions, des coques et des palettes. Toute production d'un personnage sans ce
référentiel repart d'une feuille blanche à chaque planche, et la silhouette dérive d'une image à
l'autre — le défaut que la section « silhouettes » interdit déjà pour les vaisseaux.

### Lyra Vantella — navigatrice // IA guide

Elle **incarne la voix du jeu** : ce que les bannières et le journal disaient en texte, elle le dit
en personne — à l'accueil, en jeu, au briefing. Un seul personnage, trois cadrages.

**Ce qui est immuable d'une planche à l'autre** (fait foi :
`assets/reference/concepts/lyra_vantella_character_sheet.png`) :

| Trait | Valeur |
|---|---|
| Livrée | Combinaison **bleu profond `#1C2B5E`** + panneaux **blanc cassé `#EDEAE3`**, liserés **or `#E4B54A`** |
| Cheveux | Orange cuivré, longs, **queue haute** tenue par une pince cyan |
| Tête | Casque-micro à branche droite, oreillette cyan |
| Accessoires | **Bracelet holographique cyan `#3FD9E8`** au poignet gauche, sphère de navigation holo en main droite |
| Ceinture | Boucle à gemme cyan, étui de cuisse à gauche |
| Bottes | Blanches, talon, liseré cyan |

Elle porte donc **la palette Helios sans exception** : c'est ce qui la rattache à la faction sans
qu'aucun logo n'ait à le dire.

### Deux régimes, et ils se lisent à la couleur du cadre

| Régime | Cadre | Expression | Quand |
|---|---|---|---|
| **Calme** | Cyan `#3FD9E8` | sourire, posture ouverte | accueil, information, progression |
| **Alerte** | Rouge sécurité `#C93A31` | urgence, bouche ouverte | danger immédiat, point faible ouvert |

⚠️ C'est le **cadre** qui porte le régime, pas seulement le visage : à la taille où le portrait
s'affiche en jeu, une expression seule ne se lit pas. Deux signaux valent mieux qu'un
(cf. `docs/KB/DAF/signaux.md`, loi n°2).

### ⛔ Un personnage se livre D'UN SEUL TENANT — seules les pièces qui bougent seules sont à part

> Règle **retournée le 2026-08-28**. Elle disait « en calques, jamais aplati », pour un squelette
> 2D. Mesuré sur la livraison : un générateur d'images réussit une figure entière et échoue sur
> des morceaux — bras aux mauvaises proportions, frange peinte deux fois, trois coiffures. Et le
> jeu anime par translation de toute la figure, qui n'a besoin d'aucune découpe (`ADR-0035`,
> révision).

```
figure                          entière, sans hologrammes, sur fond magenta
holo_bracelet · holo_sphere     ils dérivent et tournent seuls
figure_bouche_* · figure_yeux_* OPTIONNELS, par retouche de masque — jamais régénérés
```

PNG sur fond uni (magenta), découpé par `tools/bg-key-alpha.py --mode chroma`. Le contrat complet
et son gabarit JSON : [`docs/forge/characters/README.md`](characters/README.md).

## 4. Règles de silhouettes (spec §15.3–15.5)

- **Specter-9** : triangulaire, deux propulseurs, ailes courtes, nez central, cockpit visible
  original, aucune transformation humanoïde, pièces mobiles limitées (aérofreins/armes).
- **Aegis Citadel** : lisible à très grande distance, noyau prismatique central, deux
  bras-batteries, grande baie d'appontage, surfaces segmentées, lumières d'échelle.
- **Null Choir** : sombre, segmenté, **asymétrique**, biomécanique ; fissures lumineuses.
- Test d'originalité : une silhouette doit évoquer *le genre*, jamais une œuvre identifiable.
  En cas de doute, s'éloigner davantage.

## 5. Interdits absolus (spec §0.2, §3)

> **Assoupli par ADR-0009** (projet personnel non commercial) : les références de
> `assets/reference/inspiration/` (voir leur `REFERENCE_INDEX.md`) peuvent servir d'inspiration au rendu ;
> la production reste originale (on transpose l'intention, on ne décalque pas). Voir l'ADR.

- Aucun nom/design dérivé de : Macross, SDF-1, Valkyrie, Zentradi, Robotech, ou toute licence.
- Prompts de génération : décrire fonctions, matériaux, proportions, époque graphique,
  ambiance — **jamais** de nom de licence ni d'artiste vivant.
- Aucun asset téléchargé sans licence explicite enregistrée. Aucun asset temporaire non signalé.

## 6. Formats et conventions de livraison

- Fichiers : anglais, `snake_case`. Textes in-game : anglais. Docs : français.
- Vecteurs : **SVG** propre (pas de metadata d'éditeur), viewBox carré pour icônes,
  lisible de 16 à 256 px.
- Images : PNG alpha propre, sans franges ; sources conservées dans `assets/source/`.
- 3D : glTF 2.0 (`.glb` en livraison), 1 unité = 1 m, +Z avant Godot, pivots posés, LOD si brief.
- Audio : WAV source dans `assets/source/audio/`, OGG en livraison, pas de clipping.
- **Provenance obligatoire** : une ligne par asset livré dans
  `assets/licenses/ASSET_PROVENANCE.csv` (voir en-tête du fichier).
- **UV obligatoires** (`ADR-0028`) : tout maillage livré porte des UV, et `TEXCOORD_0` est
  **compté** dans le `.glb` — jamais supposé. Un asset sans UV n'est pas « sans texture pour
  l'instant » : il est **définitivement inhabitable** sans reforge, et le défaut est totalement
  silencieux (aucune erreur d'import, aucun test rouge).

### Textures — la voie de l'opérateur (`ADR-0028`)

La texture est une **étape du process**, plus une simple permission. `ADR-0013` avait levé les
interdits sans instituer d'étape ; `ADR-0028` la pose.

**Le partage est en trois mains, et la forge n'en tient qu'une :**

| Qui | Quoi |
|---|---|
| L'opérateur | **génère les images**, hors du dépôt, et les dépose dans `assets/source/` |
| La forge | la **géométrie et les UV qui accueillent la texture** — jamais la texture elle-même |
| Le concepteur | rédige la demande `TEX-NNNN`, dérive les cartes, câble le matériau, mesure, intègre |

⚠️ **La forge ne livre donc AUCUNE texture** : ni peinte, ni générée, ni procédurale cuite dans le
`.glb`. Un matériau provisoire pour ses propres rendus est bienvenu, mais il ne part pas dans le
`.glb` autrement qu'en couleur unie.

Une demande de texture est un **fichier JSON normalisé**, une par fichier :
`docs/forge/textures/TEX-NNNN-<slug>.json`. Le contrat — schéma, six règles de validation, échelle
monde déclarée `measured` ou `decided` — est dans
[`docs/forge/textures/README.md`](textures/README.md). Le skill `/asset-image` en est l'étage de
transformation en prompt.

⚠️ **La réserve de couleurs s'applique aux textures comme au reste** : le cyan `#3FD9E8` appartient
au tir allié, le corail `#FF5A3D` au tir ennemi (§3). Une texture qui les emploie vole leur
lisibilité aux projectiles. Et le critère qui valide une texture n'est jamais la beauté de la
surface : c'est une capture regardée, où **le chasseur et les balles se lisent encore par-dessus**
(`ADR-0006`).

## 7. Échelles indicatives (graybox)

- Specter-9 : ~1,2 unité de large. Needle Scout : ~0,9. Frégate : 8–12.
  Aegis Citadel : 60+. Pale Leviathan : 80+.
- Plan de jeu logique : rectangle 24 × 14 unités (X latéral, « haut écran » = -Z monde).
