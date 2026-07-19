# Index des références visuelles

**Statut : références visuelles légitimes du projet (ADR-0009).** Ces planches sont la **cible
d'inspiration** du rendu d'Aegis Ascendant — composition, densité, chaleur, profondeur, codes
couleur. Ce sont des **références**, pas des assets de production : `assets/source/` est `.gdignore`é,
elles ne sont jamais importées par Godot.

Jadis quarantinées hors dépôt (ADR-0005), elles ont été réinstaurées ici et versionnées par
**ADR-0009** (projet **personnel, non commercial, non distribué** ; risque IP assumé par le
propriétaire).

## Note de propriété intellectuelle

Certaines planches comportent des noms/codes visuels de licences existantes (« Macross »,
« Raiden », « Valkyrie », « Zentradi »). Elles servent d'**inspiration** ; la **production reste
originale** : on transpose l'intention (ambiance, mise en scène, palettes), on ne décalque pas une
silhouette sous licence ni un logo/texte de marque. Si le projet devait un jour être distribué, cette
posture serait à revoir (voir ADR-0009).

## Fichiers

### `reference_fortress_battle_scene.png`

Planche d'ambiance montrant une bataille spatiale en vue verticale autour d'une forteresse.

Éléments observés :

- une forteresse alliée massive occupant la partie supérieure de l'image ;
- un chasseur joueur central vu du dessus ;
- plusieurs chasseurs alliés secondaires ;
- des batteries, tourelles et modules mécaniques sur la forteresse ;
- des projectiles alliés bleus et des projectiles ennemis orange ;
- des missiles avec traînées de fumée ;
- des explosions et dégâts localisés sur la coque ;
- une planète, un champ d'étoiles et des débris en arrière-plan ;
- une lecture verticale avec forte différence d'échelle entre le joueur et la forteresse.

Usages génériques possibles : étude de hiérarchie d'échelle, densité d'une bataille, séparation
chromatique des équipes et mise en scène du segment de défense de l'Aegis Citadel.

### `reference_faction_design_sheet.png`

Planche de désignation regroupant des concepts de factions, des vues orthographiques et quatre
pickups.

Éléments observés :

- Specter-9 : chasseur joueur, vue principale et deux configurations de tir ;
- Aegis Citadel : forteresse alliée, vues frontale, latérale et arrière ;
- Pale Leviathan : vaisseau-amiral biomécanique ennemi et vues orthographiques ;
- Choir Harvester : mini-boss à trois bras autour d'un noyau central ;
- Needle Scout : petit drone ennemi ;
- Crescent Interceptor : intercepteur ennemi en croissant ;
- Choir Mine : mine sphérique à noyau lumineux ;
- Shield Carrier : unité de soutien avec champ de protection ;
- Power Core : pickup en losange doré ;
- Shield Cell : pickup hexagonal cyan ;
- Missile Rack : pickup en chevrons orange ;
- Overdrive Shard : pickup cristallin magenta ;
- palettes alliée blanc/bleu/cyan et ennemie anthracite/magenta ;
- encadrés techniques et emblèmes décoratifs non canoniques.

Usages génériques possibles : inventaire des unités, besoins de vues orthographiques et
différenciation fonctionnelle par silhouette. Les silhouettes représentées ne sont pas
validées et devront être redessinées à partir des contraintes de la charte.

### `reference_asset_overview_board.png`

Tableau d'inventaire couvrant la majorité des familles d'assets prévues pour le prototype.

Éléments observés :

- ennemis : Needle Scout, Crescent Interceptor, Leech Drone, Null Bomber, Shield Carrier,
  Frigate Turret, drones poursuivants, Choir Mine, missile ennemi et essaim d'abordage ;
- armement allié : cinq niveaux de Pulse Array, Spread Mode, Lance Mode, Orbit Mode, drone
  orbital, missile secondaire, Overdrive et Point Defense Grid ;
- pickups : Power Core, Shield Cell, Missile Rack, Orbit Drone, Overdrive Shard, Score Prism et
  Rescue Beacon ;
- VFX : impacts de coque et de bouclier, trois tailles d'explosion, débris, traînée de missile,
  télégraphe d'attaque et étincelles ;
- décors : dock de chasseurs, couloir d'appontage, structure intérieure, tourelle défensive,
  générateur d'énergie, conduit, pont de commandement, ascenseur magnétique, panneau de
  contrôle et hangar ;
- transition joueur : Specter-9, approche, arrimage et prise de contrôle ;
- HUD chasseur : score, multiplicateur, bouclier, puissance, missiles, Overdrive, objectif,
  boss et danger ;
- HUD forteresse : bouclier, Point Defense, batteries, Helios Lance et état des systèmes ;
- musique : neuf états adaptatifs, de Launch à Victory ;
- SFX : tir allié, impact, missile, explosion, bouclier, pickup, alerte, appontage, batterie
  lourde et Helios Lance ;
- écrans : titre, menu principal, résumé de fin et victoire.

Usages génériques possibles : base de découpage des futurs briefs et contrôle de couverture de
l'inventaire. Cette planche contient des mentions explicites à des licences existantes et ne
constitue donc pas une référence artistique autorisée.

### `reference_ships_docking_and_fortress_systems.png`

Planche d'inventaire consacrée aux grands vaisseaux, à la séquence d'appontage, aux systèmes
de l'Aegis Citadel et aux décors spatiaux.

Éléments observés :

- Aurora Spear : porte-chasseur avec pont de commandement, hangars internes, baies de
  lancement, catapultes, rails d'arrimage et propulseurs principaux ;
- frégate alliée : appareil d'escorte humanoïde vu du dessus ;
- deux frégates ennemies : variantes organo-mécaniques aux palettes verte et anthracite ;
- batterie externe de l'Aegis Citadel : canon lourd quadruple, silos à missiles et nœud de
  bouclier ;
- séquence d'appontage : baie de lancement, catapulte, rail d'arrimage, tunnel d'approche et
  mécanisme d'accrochage ;
- accessoires d'appontage : portes, balises lumineuses, section de tunnel et mécanismes
  articulés ;
- Helios Lance : états de charge, canon prêt et tir du faisceau principal ;
- Twin Rail Batteries : batterie double à projectiles énergétiques ;
- Aegis Shield : dôme de protection autour d'un module de forteresse ;
- activation coordonnée de plusieurs batteries ;
- section de pont de l'Aegis Citadel avec Point Defense Grid, nœuds de bouclier, batteries
  lourdes, silos à missiles, Helios Lance et tourelles anti-aériennes ;
- planète et flotte alliée en arrière-plan ;
- décors spatiaux : épave, débris métalliques, cargo flottant, station relais et champ
  d'étoiles.

Usages génériques possibles : décomposition fonctionnelle de l'Aurora Spear, liste des modules
nécessaires à l'appontage, inventaire des systèmes défensifs de la Citadel et catégories de
décors d'arrière-plan. Les noms de classes non canoniques visibles sur la planche doivent être
ignorés. Les silhouettes et la composition devront être entièrement recréées.

### `reference_specter_9_design_sheet.png`

Fiche de conception détaillée du Specter-9 présentant sa géométrie, ses systèmes et ses états.

Éléments observés :

- vues de dessus, dessous, face, arrière et profil droit ;
- dimensions, masse, vitesse et équipage proposés à titre indicatif ;
- palette blanc cassé, bleu profond, rouge de sécurité, gris, or et cyan lumineux ;
- cockpit monoplace et interface intérieure ;
- points d'emport : Pulse Array, missiles, drones orbitaux, armements auxiliaires et pont
  d'appontage ;
- inclinaisons gauche, neutre et droite ;
- état Overdrive avec propulsion, cadence et bouclier renforcés ;
- grappins, rail magnétique et amortisseurs du système d'appontage ;
- propulseurs principaux et tuyères auxiliaires ;
- détails des armes intégrées ;
- états de dégâts intact, 25 %, 50 % et 75 % ;
- comparaison d'échelle avec une frégate et l'Aurora Spear ;
- poses d'animation : attente, accélération, inclinaison, tirs, Overdrive, freinage et appontage ;
- marquage d'escadron et proposition d'insigne Helios Vanguard.

Usages génériques possibles : cahier des besoins pour un futur brief de modèle 3D, liste des
animations et points d'emport, états de dégâts et contraintes d'appontage. Les dimensions
contredisent l'échelle graybox de la charte et ne sont pas normatives. La mention « VF-class »,
la silhouette et l'insigne représentés doivent être écartés ou entièrement redessinés.

### `reference_ui_characters_and_branding_board.png`

Planche regroupant personnages de communication, interfaces, écrans, projectiles, identité
visuelle, parallaxe et familles sonores.

Éléments observés :

- portraits et expressions d'une commandante, d'un opérateur tactique et d'une IA de bord ;
- combinaisons de vol et casques ;
- HUD chasseur, HUD forteresse et transition entre les deux modes ;
- écrans titre, menu, options, pause, échec, victoire et résumé de niveau ;
- prompts de tutoriel, icônes d'armes et glyphes de contrôles ;
- télégraphes, projectiles et impacts de cinq familles ennemies ;
- cinq états de dégâts de l'Aegis Citadel ;
- sept couches d'arrière-plan spatial destinées à la parallaxe ;
- familles de SFX représentées par des formes d'onde ;
- logos, emblèmes, marquages de coque, typographie et icône d'application proposés.

Usages génériques possibles : inventaire des écrans et états UI, liste d'expressions pour les
communications radio, organisation de la parallaxe et couverture audio. Cette planche cite
explicitement des licences existantes : aucun portrait, logo, symbole, marquage, caractère
typographique, écran ou agencement ne doit être reproduit.

### `reference_gameplay_vfx_environment_board.png`

Planche de synthèse consacrée aux pickups, VFX, environnements, HUD, audio et identité.

Éléments observés :

- les sept pickups canoniques avec variantes et effet de collecte ;
- HUD chasseur et forteresse ;
- tirs alliés et ennemis, impacts de coque et de bouclier ;
- télégraphe d'attaque, trois tailles d'explosion, débris et étincelles ;
- onde de choc, traînée et fumée de missile, point faible et dégâts de la Citadel ;
- collecte, Overdrive, activation des batteries, charge et tir de la Helios Lance ;
- profils visuels Gameplay, Overdrive, Docking, Fortress et Victory ;
- neuf états de musique adaptative et dix familles de SFX ;
- trois intervenants radio avec formes d'onde ;
- écrans titre, menu, options, tutoriel, pause, échec, victoire et résumé ;
- extérieurs de la Citadel, couloirs, baie, catapulte, rail et portes d'appontage ;
- six couches de parallaxe et palettes des deux factions ;
- propositions de logo, emblèmes, marquages, patch, icône et glyphes de contrôles.

Usages génériques possibles : matrice de couverture globale pour découper les briefs pickups,
VFX, UI, audio et environnements. Les fonctions, catégories et palettes canoniques sont
exploitables ; tous les rendus, personnages, logos et agencements restent à recréer.

## Correspondance avec le canon

| Famille | Éléments canoniques exploitables pour les briefs | Statut des visuels montrés |
|---|---|---|
| Alliés | Specter-9, Aegis Citadel, armements Helios Vanguard | Intentions seulement, silhouettes à refaire |
| Null Choir | Pale Leviathan, Choir Harvester et sept familles ennemies | Intentions seulement, silhouettes à refaire |
| Pickups | Sept types définis par la charte | Fonctions et codes forme/couleur exploitables |
| VFX | Projectiles, impacts, explosions, télégraphes et débris | Catégories exploitables, rendu à recréer |
| Décors | Lancement, appontage, Citadel et bataille spatiale | Besoins fonctionnels exploitables |
| UI et audio | HUD, écrans, états musicaux et familles de SFX | Inventaire exploitable, design à recréer |

## Provenance et usage

- Origine apparente : images générées avec ChatGPT et ajoutées manuellement au dépôt le
  11 juillet 2026.
- Prompt source : non fourni.
- Auteur et droits de diffusion : à confirmer par le propriétaire du dépôt.
- Statut : références internes non validées, non destinées à la livraison.

Ces fichiers ne sont volontairement pas enregistrés comme assets livrés dans
`assets/licenses/ASSET_PROVENANCE.csv`. Leur provenance devra être complétée avant tout usage
autre que l'analyse interne.
