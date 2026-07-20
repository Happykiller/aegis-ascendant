# ADR-0011 — Détail des coques : budgets relevés et textures de détail répétables

- **Statut** : accepté
- **Date** : 2026-07-20
- **Amende** : ADR-0008 (budgets de triangles, interdiction de textures)
- **Contexte spec** : §24.2 (modèles 3D), §24.4 (textures)

## Contexte

Les coques livrées sous ADR-0008 sont conformes à leur contrat et **font « trop jouet »** : surfaces
lisses et molles, aucune ligne de panneau, arêtes uniformément adoucies. Le constat n'est pas une
impression, il se mesure sur les scripts et les rapports de forge :

| Symptôme | Mesure |
|---|---|
| Coque principale du Specter-9 à peine subdivisée | 32 stations × 15 abscisses ≈ **1 860 triangles** pour tout le fuselage |
| Panneaux bleus « peints » plutôt que découpés | **496 triangles** de `AA_Panel` sur tout le vaisseau |
| Vaisseau trop plat | **0,41 m** de haut pour 0,60 autorisés (BRIEF-0021-report §8.3 : « *la planche montre un vaisseau plus épais* ») |
| Presque aucun greeble sur un héros | **~12 boîtes** au total |
| Aegis Citadel : silhouette sous-échantillonnée | les trois masses coûtent **~200 quads** ; le budget part en révolutions à 8-12 segments |
| Charte non honorée | « surfaces segmentées » exigée, **112 triangles** de `AA_Panel` sur toute la forteresse |

Deux causes structurelles, et aucune n'est un défaut d'exécution de la forge :

1. **Les budgets de triangles sont le vrai frein.** `build_specter_9.py:782-786` documente qu'un
   biseau à 2 segments coûtait **5 000 triangles** — soit 97 % de la marge du héros — et a donc été
   abandonné. La marge affichée (34 %) est illusoire : elle est consommée par le premier réglage de
   qualité qu'on tente.
2. **Le détail purement géométrique plafonne.** Le kit n'a aucune primitive de rainure fine :
   `inset_panel` opère sur des faces entières, donc une ligne de panneau qui traverse une face est
   inexprimable. C'est la cause directe de l'aspect « aplat », signalée dès BRIEF-0021-report §8.6.

Par ailleurs le contexte de rendu a changé : le Specter-9 est désormais affiché **en gros plan sur
l'écran d'accueil** (diorama 3D), et plus seulement vu de loin, presque au zénith, en combat.

## Décision

### 1. Budgets de triangles relevés

| Classe | ADR-0008 | ADR-0011 |
|---|---|---|
| Héros (Specter-9) | 15 000 | **60 000** |
| Ennemi léger | 3 000 | **12 000** |
| Boss | 25 000 | **90 000** |
| Structure | 30 000 | **120 000** |

**Justification mesurée, pas confortable.** Sur le poste courant (Quadro T1000, budget 16,7 ms à
60 Hz), le temps GPU est dominé par le **remplissage écran** — fond procédural, glow, post-process —
et non par la géométrie : l'écran d'accueil rend à **8,3 ms** avec la citadelle (21 k triangles) plus
quatre chasseurs, quand le combat rend à **11,4-13,3 ms** avec 107 ennemis et jusqu'à 600
projectiles. La scène la plus chargée en géométrie est la moins chère. Multiplier la géométrie des
coques par quatre reste sous le bruit de mesure de cette machine (~1,9 ms de dispersion).

Ces plafonds restent des **garde-fous**, pas des objectifs : dépenser 60 000 triangles sur un
chasseur qui n'en a pas besoin reste une faute. La règle « le budget se justifie au rendu, pas au
chiffre » ne change pas.

⚠️ Le plafond de **hauteur** de l'Aegis Citadel passe de 5,00 m à **5,60 m** : à 4,88 m mesurés, il
ne restait aucune marge pour une antenne ou une nervure (BRIEF-0025-report §5). Les autres
dimensions X/Z **restent inchangées et normatives** (voir « ce qui ne change pas »).

### 2. Textures de détail répétables, en niveaux de gris

ADR-0008 interdisait les textures tout en laissant explicitement la porte ouverte : « *le bake de
textures reste possible plus tard, par unité, si un plan rapproché (menu, cinématique) l'exige* ».
L'écran d'accueil **est** ce plan rapproché.

On autorise donc, **pour toutes les coques** :

- des **feuilles de détail répétables (seamless) en NIVEAUX DE GRIS**, multipliées sur les couleurs
  de palette — lignes de panneau, greebles, usure ;
- un **dépliage UV par projection**, simple, non peint à la main ;
- l'export des **UV et des tangentes** dans le `.glb`.

**Ce que ce choix préserve.** Les feuilles étant en niveaux de gris et multipliées, la palette
normative reste exacte : aucune teinte n'est introduite par la texture. Les **sept noms de matériaux**
d'ADR-0008 restent imposés — les scènes Godot s'y raccrochent. Et une même feuille sert les six
coques, donc le coût LFS est payé une fois, pas par unité.

**Ce qui reste interdit** : les textures peintes à la main par vaisseau (atlas UV dédié), qui
demanderaient un pipeline d'authoring que ce projet n'a pas, et les textures porteuses de couleur,
qui contourneraient la palette.

### 3. Retrait de la dette « torse + épaules » de l'Aegis Citadel

`docs/forge/REVIEW_NOTES.md` demandait d'« abaisser/écarter les bras pour casser cette lecture
humanoïde ». Le propriétaire du projet arbitre en faveur de la **fidélité à la planche de concept**,
laquelle présente elle-même cette lecture. La dette est donc **retirée**, pas contournée.

Motif : laisser coexister une consigne (« aussi proche de la planche que possible ») et son contraire
(« casser la lecture de la planche ») produirait des arbitrages incohérents d'une session à l'autre.
Deux règles opposées dans le dépôt valent moins que zéro règle.

## Ce qui ne change pas

- **Dimensions X/Z imposées, tolérance ±3 %.** C'est le contrat de gameplay : hitbox, télégraphes et
  lisibilité en dépendent. ADR-0008 §dimensions reste normatif.
- **Les sept matériaux** et leur ordre (`MATERIAL_ORDER`), la palette, les noms de points d'attache.
- **Le script Python EST la source** ; aucun `.blend` versionné.
- **Déterminisme** : aucun aléa non seedé, deux exécutions byte-identiques, auto-validation par
  `export_hull()` qui refuse de publier hors contrat.
- **La règle de BRIEF-0026** : si une surface n'est pas visible depuis la caméra de jeu (20° de la
  verticale), ce qu'on y met n'existe pas. Relever les budgets ne dispense pas de placer le détail
  là où il se voit.

## Conséquences

- `aegis_kit.py` doit exporter les UV et les tangentes (`export_texcoords`, `export_tangents`), et
  offrir un dépliage par projection. Sans cela la décision 2 est inopérante.
- Les contrats des scripts de coque existants doivent être relus : un `tri_budget` relevé sans
  retravailler la géométrie ne change rien au rendu.
- Le coût GPU est à **re-mesurer** après chaque reforge, aux deux endroits où les coques
  apparaissent : l'écran d'accueil (gros plan) et le combat. La méthode ne change pas
  (`.claude/resources/howto-mesurer-la-perf.md`) : plusieurs relevés, retenir la plage, jamais le FPS.
- Si un jour le projet vise un GPU plus faible que le Quadro T1000, ces budgets sont le premier
  levier de dégradation — et ils redeviendront contraignants.
