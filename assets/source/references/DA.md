# Direction artistique — Aegis Ascendant

## 1. Rôle du document

Ce document fixe les invariants visuels d’**Aegis Ascendant** afin de produire à la demande de
nouvelles unités, structures, interfaces, illustrations et effets cohérents avec l’existant.

Il ne constitue pas un catalogue fermé. Toute extension est permise si elle respecte, dans cet
ordre :

1. la lisibilité immédiate du gameplay ;
2. la fonction et la faction de l’élément ;
3. les silhouettes, palettes et matières définies ici ;
4. le ton et la mise en scène du jeu ;
5. l’originalité de la création.

En cas de conflit, la lisibilité prime toujours sur la richesse des détails et le spectacle.

## 2. Vision artistique

**Aegis Ascendant** est un space opera militaire rétrofuturiste, traité comme un shooter vertical
2.5D moderne. Son identité repose sur la confrontation entre un appareil rapide et lisible et des
architectures de guerre démesurées.

Le rendu doit évoquer :

- une guerre orbitale dense mais compréhensible en un regard ;
- une technologie militaire massive, fonctionnelle et entretenue ;
- une montée en puissance du chasseur isolé vers le contrôle d’une forteresse ;
- un héroïsme franc, spectaculaire, sans cynisme ni photoréalisme ;
- une animation mécanique rétrofuturiste transposée dans un langage visuel original.

Formule directrice :

> Un petit chasseur lumineux remonte une guerre verticale froide et monumentale, traversée par des
> torrents d’énergie bleue et des ruptures explosives orange.

## 3. Piliers fondamentaux

### 3.1 Lisibilité prioritaire

Le joueur, les projectiles dangereux, les pickups et les objectifs doivent être identifiables en
moins de 200 ms. Ils sont prioritaires sur le décor, les alliés secondaires, les explosions et le
HUD non critique.

La couleur seule ne suffit jamais. Chaque catégorie de gameplay doit combiner au moins trois
signaux parmi :

- silhouette ;
- taille ;
- luminance ;
- couleur ;
- contour ou halo ;
- mouvement ;
- rythme de pulsation ;
- icône ;
- son.

### 3.2 Échelle monumentale

Le joueur reste une ancre visuelle petite et précise face à des croiseurs, ponts, batteries et
forteresses qui peuvent dépasser le cadre. La différence d’échelle doit être racontée par :

- des lumières de service répétées ;
- des modules mécaniques de taille connue ;
- plusieurs niveaux de détail ;
- des appareils secondaires minuscules ;
- des occultations et entrées/sorties hors cadre ;
- une parallaxe profonde avec planète, flotte et débris.

### 3.3 Technologie fonctionnelle

Les formes ne sont pas décoratives au hasard. Une baie permet d’accoster, une batterie pivote, un
nœud de bouclier protège, un réacteur propulse et un conduit transporte de l’énergie. Les détails
doivent révéler cette fonction.

Répartition indicative des surfaces :

- 60 % de grandes masses calmes qui portent la silhouette ;
- 30 % de panneaux, articulations et détails fonctionnels ;
- 10 % d’accents lumineux, marquages ou zones interactives.

### 3.4 Verticalité héroïque

La composition principale suit l’axe bas-vers-haut : joueur dans le tiers inférieur, destination,
menace ou structure majeure au-dessus. Les lignes de propulsion, les tirs et les volumes du décor
renforcent cette ascension.

### 3.5 Contraste thermique

Le monde est construit sur un fond froid et sombre. Le cyan et le bleu expriment le contrôle,
l’alliance et la propulsion. Le corail, le magenta et l’orange expriment la menace, l’instabilité,
les impacts et la destruction. Les explosions chaudes sont brèves ; elles ne doivent jamais
effacer durablement les menaces.

## 4. Style de rendu

Le gameplay utilise une **3D stylisée lisible en vue du dessus**, enrichie de textures et de VFX
qui évoquent un pixel art HD sans imposer une pixellisation littérale à tous les éléments.

Caractéristiques attendues :

- volumes nets et silhouettes franches ;
- détails mécaniques regroupés plutôt que distribués uniformément ;
- matériaux mats ou satinés, avec arêtes plus lumineuses ;
- émissifs localisés et contrôlés ;
- ombres profondes sans perdre les contours utiles ;
- explosions texturées, débris sombres et noyaux lumineux brefs ;
- bloom contenu, jamais utilisé pour compenser une silhouette faible.

Les écrans promotionnels et illustrations peuvent adopter un rendu plus cinématique, atmosphérique
et détaillé. Ils conservent les mêmes silhouettes, palettes, matières et rapports d’échelle. Ce
traitement cinématique ne constitue pas une cible de fidélité pour le rendu en jeu.

## 5. Langage des factions

### 5.1 Helios Vanguard

Valeurs : discipline, protection, précision, puissance maîtrisée.

- silhouettes symétriques, axiales et orientées vers l’avant ;
- formes triangulaires, prismatiques ou en bouclier ;
- coques modulaires, entretenues et clairement assemblées ;
- grandes plaques blanc cassé séparées par des panneaux bleu profond ;
- propulsion et systèmes actifs cyan ;
- or réservé au commandement, aux insignes et aux fonctions exceptionnelles ;
- rouge de sécurité utilisé avec parcimonie pour les avertissements et marquages techniques.

Palette canonique :

| Fonction | Couleur |
|---|---|
| Coque principale | `#EDEAE3` |
| Panneaux | `#1C2B5E` |
| Énergie, moteurs, HUD | `#3FD9E8` |
| Commandement, insignes | `#E4B54A` |
| Sécurité | `#C93A31` |

### 5.2 The Null Choir

Valeurs : prédation collective, corruption, croissance biomécanique, intention étrangère.

- silhouettes segmentées et asymétriques ;
- carapaces, pointes, cavités et espaces négatifs ;
- articulation moins rationnelle que celle des unités Helios ;
- noyaux visibles semblables à des organes, jamais à de simples cockpits ;
- fissures lumineuses irrégulières ;
- répétition organique imparfaite plutôt que modularité industrielle.

Palette canonique :

| Fonction | Couleur |
|---|---|
| Coque | `#24252B` |
| Segments profonds | `#452663` |
| Carapace secondaire | `#DDDCD2` |
| Noyaux, armes | `#D93D9C` |
| Corruption rare | `#7C9E52` |

Une nouvelle unité Null Choir ne doit pas être seulement un chasseur Helios assombri. Sa silhouette
doit rester identifiable en aplat noir et présenter au minimum une rupture asymétrique majeure.

## 6. Contraste et hiérarchie de visibilité

Le fond spatial de référence est `#070A12`. Il doit rester le plancher de luminance. Les nébuleuses,
planètes, coques et fumées ne doivent pas remonter globalement ce plancher au point de réduire la
séparation des éléments actifs.

Hiérarchie de saillance, de la plus forte à la plus discrète :

1. projectiles ennemis et télégraphes létaux ;
2. joueur ;
3. objectifs immédiats et pickups ;
4. projectiles alliés ;
5. ennemis ;
6. alliés et systèmes secondaires ;
7. décor interactif ;
8. décor d’ambiance et particules non fonctionnelles.

Règles obligatoires :

- un projectile ennemi possède toujours un cœur clair et un halo contrasté ;
- le cœur ennemi utilise `#FFE9D2`, le halo danger `#FF5A3D` ;
- les tirs alliés principaux utilisent le cyan `#3FD9E8` ;
- un flash d’impact reste inférieur à 120 ms lorsqu’il approche la luminance d’un danger ;
- les fumées restent sombres ou désaturées ;
- le bloom ne doit pas fusionner plusieurs projectiles en une masse illisible ;
- un effet non interactif ne doit jamais présenter durablement la même forme, taille, couleur et
  luminance qu’un danger ;
- les contours utiles doivent survivre sur les zones les plus claires et les plus sombres du niveau ;
- la distinction allié/ennemi et bonus/danger doit rester valide en vision périphérique et en
  simulation de déficience colorimétrique ;
- aucun texte essentiel ne doit reposer sur une image chargée sans fond ou contour de séparation.

Avant validation, observer l’asset dans une capture réelle de gameplay :

1. en taille de jeu normale, jamais seulement en gros plan ;
2. sur fond spatial sombre ;
3. devant une coque claire ;
4. au milieu de tirs et d’une explosion ;
5. en niveaux de gris ;
6. avec simulation de deutéranopie au minimum ;
7. pendant le mouvement, avec le post-traitement final actif.

Si un élément échoue, corriger d’abord sa silhouette, sa valeur ou son contour avant d’augmenter sa
saturation et son bloom.

## 7. VFX et langage du mouvement

### Alliés

- tirs fins, propres, directionnels ;
- cyan, bleu et or ;
- géométrie stable et cadence régulière ;
- propulsion en faisceau resserré ;
- boucliers hexagonaux ou prismatiques.

### Ennemis

- projectiles compacts avec cœur et couronne ;
- corail, magenta et orange ;
- pulsations, trajectoires courbes ou rythmes irréguliers ;
- télégraphes circulaires ou organiques clairement séparés des tirs actifs.

### Explosions et destruction

- noyau blanc-jaune très bref ;
- expansion orange chaude ;
- fragments sombres donnant l’échelle ;
- fumée désaturée qui se dissipe rapidement dans la zone de jeu ;
- dégâts localisés et progressifs sur les grandes coques.

Le spectacle vient de la succession et de la chorégraphie des effets, pas de leur présence maximale
et permanente.

## 8. Pickups et objets interactifs

Chaque pickup combine une couleur, une silhouette et une icône distinctes :

| Pickup | Couleur | Forme dominante |
|---|---|---|
| Power Core | jaune-or | losange |
| Shield Cell | cyan | hexagone |
| Missile Rack | orange | chevron |
| Orbit Drone | violet | anneau |
| Overdrive Shard | magenta | éclat |
| Score Prism | vert | prisme |
| Rescue Beacon | blanc | étoile |

Ils partagent une matière cristalline ou énergétique et un halo contrôlé. Leur animation de collecte
converge vers le joueur sans reproduire la forme ni le rythme d’un projectile ennemi.

## 9. Environnements et profondeur

Les environnements combinent six familles de profondeur : étoiles lointaines, nébuleuses, planète
ou atmosphère, flotte distante, structures intermédiaires, débris et effets proches.

Toutes ne doivent pas être également visibles. Les couches éloignées ont :

- moins de contraste ;
- moins de saturation ;
- des mouvements plus lents ;
- des détails plus larges et plus calmes.

Les structures proches portent davantage de contraste local, mais leurs lumières restent sous la
saillance des objets de gameplay. Une planète sert de repère de profondeur et de composition, jamais
de fond uniformément clair derrière toute la zone jouable.

## 10. Interface et communication

L’interface est militaire, compacte et périphérique : fond bleu-noir, filets cyan, texte clair,
angles coupés et géométrie prismatique inspirée de l’Aegis Citadel.

- le centre de l’écran reste libre ;
- les états critiques utilisent couleur, icône et animation ;
- l’orange et le rouge sont réservés aux alertes ou valeurs dégradées ;
- les informations persistantes restent moins lumineuses que les dangers ;
- les portraits radio ne masquent jamais la trajectoire du joueur ;
- la typographie est condensée, technique et lisible, sans reproduire une identité existante.

Les portraits doivent employer un seul traitement cohérent pour toute la production : illustration
2D stylisée ou rendu 3D stylisé. Le mélange de styles au sein d’une même famille est interdit.

## 11. Étendre la direction artistique

Toute création nouvelle doit hériter d’une famille existante, puis introduire une variation motivée
par sa fonction.

Méthode :

1. définir la fonction de gameplay et la priorité visuelle ;
2. choisir faction et famille de formes ;
3. dessiner une silhouette lisible avant les détails ;
4. appliquer la palette canonique et une seule couleur d’accent fonctionnelle ;
5. définir matière, échelle, mouvement et signature lumineuse ;
6. vérifier que l’élément ne se confond avec aucune catégorie existante ;
7. tester le contraste dans une scène de gameplay chargée ;
8. produire des vues ou états utiles à l’intégration, pas uniquement une illustration de présentation.

Une extension réussie paraît appartenir immédiatement à l’univers tout en ajoutant une fonction ou
une silhouette absente. Elle ne doit pas créer une troisième grammaire visuelle sans décision
explicite sur une nouvelle faction ou un nouveau contexte.

## 12. Gabarit de brief ou de génération

Utiliser ce bloc pour demander un nouvel élément :

```text
Élément :
Fonction en jeu :
Faction :
Priorité visuelle : critique / active / secondaire / décorative
Échelle par rapport au Specter-9 :
Silhouette dominante :
Formes héritées de la faction :
Variation fonctionnelle originale :
Palette canonique :
Couleur d’accent et justification :
Matériaux :
Sources lumineuses :
Mouvement ou animation :
États nécessaires : intact / actif / chargé / endommagé / détruit / autre
Contexte d’utilisation : gameplay / HUD / menu / illustration
Distance et taille minimales de lecture :
Éléments avec lesquels il ne doit pas être confondu :
Contraintes de contraste :
Livrables et vues demandées :
```

Un prompt de génération décrit uniquement la fonction, les volumes, les matériaux, la composition,
l’époque graphique et l’ambiance. Il ne cite ni licence existante ni artiste vivant.

## 13. Références et autorité

Les planches de `assets/source/references/` sont des références d’intention, non des assets à
reproduire. Leur autorité est la suivante :

1. `reference_fortress_battle_scene.png` : composition, échelle et intensité du gameplay ;
2. `reference_gameplay_vfx_environment_board.png` : lisibilité, VFX et couverture fonctionnelle ;
3. `reference_faction_design_sheet.png` : opposition des factions ;
4. `reference_ships_docking_and_fortress_systems.png` : architecture fonctionnelle ;
5. `reference_specter_9_design_sheet.png` : besoins du chasseur, silhouette à réinterpréter ;
6. `reference_ui_characters_and_branding_board.png` : inventaire des interfaces ;
7. `reference_asset_overview_board.png` : catalogue de production uniquement ;
8. `ref_home.png` : cible émotionnelle et promotionnelle, non cible directe du gameplay.

Les noms, logos, textes, personnages, interfaces et silhouettes associés à des licences tierces ne
sont jamais reproduits. La création transpose les intentions de composition, de chaleur, de
profondeur et de densité dans les formes originales d’Aegis Ascendant.

## 14. Critères de validation

Un élément est conforme à la DA lorsque :

- sa fonction est comprise sans texte ;
- sa faction est identifiable par sa silhouette avant sa couleur ;
- il reste lisible à sa taille réelle en jeu ;
- son contraste respecte la hiérarchie de saillance ;
- il ne masque pas un projectile dangereux ni le joueur ;
- ses détails renforcent sa fonction ;
- il étend une famille existante sans la contredire ;
- son rendu a été observé dans une capture de gameplay ;
- il demeure original et sa provenance est enregistrée avant intégration.

