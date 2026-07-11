# PROJECT AEGIS ASCENDANT
## Cahier des charges complet — Vertical shooter 2.5D/3D sous Windows, piloté par Claude Code

**Version :** 1.0  
**Statut :** Spécification de référence obligatoire  
**Cible :** Prototype jouable spectaculaire, exporté en `.exe` Windows  
**Moteur retenu :** Godot Engine 4.6, renderer Forward+, projet GDScript typé  
**Plateforme principale :** Windows 10/11 x64, GPU NVIDIA  
**Configuration de développement de référence :** PC Windows équipé d’une NVIDIA RTX 4080  
**Durée de jeu cible :** 12 à 15 minutes  
**Format :** un niveau complet, rejouable, avec séquences de vol, appontage et contrôle d’une forteresse  
**Langue du projet :** code, noms de fichiers et identifiants en anglais ; documentation fonctionnelle en français  
**Nom de travail du jeu :** `Aegis Ascendant`

---

# 0. CONTRAT D’EXÉCUTION POUR L’AGENT CLAUDE CODE

Ce document constitue la source de vérité du projet.

L’agent doit :

1. Lire intégralement ce document avant toute modification.
2. Ne jamais inventer une API Godot, une option de ligne de commande, un type, une propriété ou une méthode.
3. Vérifier toute API incertaine dans la documentation officielle Godot 4.6 avant de l’utiliser.
4. Travailler par incréments jouables, compilables et testables.
5. Ne pas créer de dépendance tierce non documentée.
6. Ne pas introduire d’asset dont la licence n’est pas enregistrée.
7. Ne jamais casser le lancement du projet ou l’export Windows.
8. Préférer les fichiers texte versionnables aux ressources binaires opaques.
9. Éviter les architectures surdimensionnées.
10. Produire un résultat impressionnant visuellement sans sacrifier la lisibilité du gameplay.
11. Maintenir une cadence fluide ; les effets visuels ne doivent jamais rendre les projectiles dangereux illisibles.
12. Ne jamais reprendre directement des éléments protégés de l’univers Macross.
13. Demander une décision humaine uniquement lorsqu’un arbitrage artistique ou juridique ne peut pas être déduit de ce document.
14. À chaque étape, exécuter les contrôles prévus dans `scripts/check.ps1`.
15. Ne déclarer une tâche terminée que lorsque ses critères d’acceptation sont vérifiés.

## 0.1 Ordre des priorités

En cas de conflit, appliquer cet ordre :

1. Projet lançable.
2. Gameplay réactif et lisible.
3. Stabilité et absence de régression.
4. Performance.
5. Respect du périmètre.
6. Qualité visuelle.
7. Richesse fonctionnelle.
8. Effets secondaires et polish.

## 0.2 Interdictions

L’agent ne doit pas :

- utiliser les noms `Macross`, `SDF-1`, `Valkyrie`, `Zentradi`, `Robotech` ou des noms dérivés dans le jeu ;
- reproduire une silhouette, un logo, une interface, une musique, une scène ou un personnage identifiable de ces licences ;
- intégrer un modèle, une texture, un son ou une musique trouvés sur Internet sans licence explicite ;
- ajouter un système multijoueur ;
- ajouter un monde ouvert ;
- ajouter un inventaire complexe ;
- ajouter une boutique, des microtransactions ou un backend ;
- transformer le prototype en framework générique ;
- mettre en place une dépendance native avant d’avoir démontré que GDScript ne suffit pas ;
- contourner un test en le désactivant ;
- cacher une erreur d’import, de compilation ou d’export ;
- utiliser un asset temporaire non signalé comme tel.

---

# 1. VISION PRODUIT

## 1.1 Intention

Créer une démonstration jouable de vertical shooter moderne dans un univers de space opera militaire rétrofuturiste.

Le joueur commence aux commandes d’un chasseur spatial léger. Il traverse une bataille orbitale, augmente progressivement sa puissance de feu, protège une citadelle mobile et atteint sa baie d’appontage. Après un appontage jouable, il transfère son système de combat au cœur tactique de la citadelle et prend le contrôle de ses batteries principales pour affronter le vaisseau-amiral ennemi.

Le jeu doit donner l’impression d’une montée en puissance continue :

`chasseur isolé → appareil surarmé → pilote décisif → commandant d’une forteresse de guerre`

## 1.2 Promesse émotionnelle

Le joueur doit ressentir :

- une prise en main immédiate ;
- une grande puissance sans difficulté punitive ;
- une montée dramatique régulière ;
- des effets spectaculaires lisibles ;
- un sentiment d’échelle croissant ;
- une transition mémorable entre le chasseur et la forteresse ;
- une conclusion héroïque de niveau “boss final de série animée”.

## 1.3 Objectif de démonstration

Le prototype doit pouvoir être montré à un professionnel du jeu vidéo pour démontrer :

- la capacité d’un agent de code à construire un jeu cohérent ;
- la combinaison de génération procédurale, assets assistés par IA et intégration humaine ;
- une architecture propre et testable ;
- une direction artistique homogène ;
- un rendu nerveux et qualitatif ;
- un export Windows autonome.

## 1.4 Piliers du projet

### Pilier A — Puissance accessible

Le joueur doit être puissant rapidement. La difficulté provient de la densité, du spectacle et du positionnement, pas d’une punition excessive.

### Pilier B — Lisibilité parfaite

Le joueur, les bonus, les projectiles dangereux et les objectifs doivent être identifiables en moins de 200 ms.

### Pilier C — Échelle évolutive

Le décor et le gameplay passent progressivement de petits chasseurs à des croiseurs, puis à deux structures colossales.

### Pilier D — Transformation de la boucle de jeu

Le passage dans la forteresse doit modifier réellement la façon de jouer, et ne pas être une simple cinématique.

### Pilier E — Originalité juridique

L’œuvre peut évoquer le space opera militaire japonais des années 1980, mais doit posséder ses propres noms, silhouettes, factions, couleurs, sons et narration.

---

# 2. DÉCISION TECHNIQUE PRINCIPALE

## 2.1 Moteur retenu

Utiliser **Godot Engine 4.6**, renderer **Forward+**, avec un projet principalement écrit en **GDScript typé**.

## 2.2 Justification

Godot est retenu pour ce prototype car :

- les scènes et ressources peuvent être largement conservées sous forme textuelle ;
- l’agent peut modifier le code et une grande partie de la structure sans dépendre d’assets binaires complexes ;
- l’export Windows est direct ;
- le renderer Forward+ prend en charge les API modernes ;
- le moteur gère les particules GPU 2D et 3D ;
- le moteur accepte les scènes 3D au format glTF ;
- FSR 2.2, TAA, MSAA, VRS, post-traitements et shaders sont disponibles ;
- un vertical shooter ne nécessite pas les systèmes lourds d’un moteur AAA ;
- le coût d’itération est inférieur à celui d’un projet Unreal piloté majoritairement par agent.

## 2.3 Pourquoi Unreal Engine n’est pas retenu pour la première version

Unreal Engine offre un plafond visuel supérieur pour certaines productions, mais introduit ici :

- davantage d’assets binaires ;
- une dépendance forte à l’éditeur ;
- une automatisation plus fragile pour les Blueprints ;
- des temps de compilation et de packaging plus élevés ;
- une complexité disproportionnée pour un niveau unique de vertical shooter.

Unreal ne pourra être réévalué qu’après un prototype Godot terminé et uniquement si une limitation visuelle démontrée empêche d’atteindre la cible.

## 2.4 Langage

Utiliser :

- GDScript typé pour le gameplay, les outils, les tests et les scripts d’éditeur ;
- shaders Godot pour les effets GPU ;
- Python uniquement pour les outils externes, la génération Blender ou le traitement d’assets ;
- PowerShell pour les scripts Windows ;
- C++/GDExtension uniquement après profilage prouvant un goulot d’étranglement impossible à corriger proprement en GDScript.

## 2.5 Stratégie de rendu

Le jeu est un **vertical shooter 2.5D en environnement 3D** :

- chasseur, ennemis majeurs, forteresse et boss en modèles 3D ;
- projectiles simples sous forme de meshes instanciés ou sprites 3D ;
- effets complexes sous forme de particules GPU ;
- arrière-plans 3D à profondeur réelle ;
- HUD en 2D ;
- caméra perspective faiblement inclinée ;
- gameplay contraint sur un plan logique 2D projeté dans la scène 3D.

---

# 3. CADRE JURIDIQUE ET CRÉATIF

## 3.1 Référence autorisée

Référence générale autorisée :

> space opera militaire rétrofuturiste, animation japonaise des années 1980, forteresse spatiale, chasseurs rapides, batailles de flottes, technologies énergétiques et climax héroïque.

## 3.2 Éléments obligatoirement originaux

Créer des éléments originaux pour :

- le titre ;
- les factions ;
- les uniformes ;
- les insignes ;
- les silhouettes des appareils ;
- la forteresse ;
- le boss ;
- les armes ;
- la musique ;
- les voix ;
- le scénario ;
- les dialogues ;
- les interfaces ;
- la palette visuelle.

## 3.3 Factions proposées

### Coalition humaine : Helios Vanguard

Organisation de défense interplanétaire chargée de protéger les colonies orbitales.

### Forteresse : Aegis Citadel

Citadelle mobile en forme de prisme axial, dotée de deux bras-batteries et d’un noyau énergétique central.

### Ennemi : The Null Choir

Intelligence collective biomécanique utilisant des vaisseaux sombres, segmentés et asymétriques.

### Vaisseau-amiral ennemi : The Pale Leviathan

Structure organo-mécanique qui cherche à absorber le noyau de l’Aegis Citadel.

## 3.4 Règle d’originalité visuelle

Les silhouettes doivent être reconnaissables uniquement comme appartenant au genre du space opera, jamais comme la copie d’une licence précise.

Les générations d’images et de modèles doivent utiliser des prompts décrivant :

- les fonctions ;
- les matériaux ;
- les proportions ;
- l’époque graphique générale ;
- l’ambiance ;

et ne doivent pas citer le nom d’une licence ou d’un artiste vivant.

---

# 4. PÉRIMÈTRE DU PROTOTYPE

## 4.1 Inclus

Le prototype comprend :

- écran titre ;
- menu principal minimal ;
- options graphiques ;
- options audio ;
- support clavier et manette ;
- tutoriel contextuel intégré ;
- un niveau complet ;
- un chasseur jouable ;
- trois armes principales ou variantes ;
- missiles secondaires ;
- jauge d’Overdrive ;
- bonus et progression de puissance ;
- plusieurs familles d’ennemis ;
- mini-boss ;
- appontage jouable ;
- passage au contrôle de la forteresse ;
- boss final multi-phase ;
- écran de victoire ;
- score ;
- statistiques de fin ;
- reprise depuis checkpoints ;
- export Windows x64 ;
- logs ;
- tests fonctionnels automatisés ;
- outils simples de debug et de profilage.

## 4.2 Exclus

Ne pas développer :

- campagne complète ;
- plusieurs niveaux ;
- multijoueur ;
- coopération ;
- sauvegarde complexe ;
- arbre de compétences ;
- personnalisation profonde ;
- dialogues ramifiés ;
- cinématiques pré-rendues longues ;
- doublage complet ;
- support console ;
- support mobile ;
- support VR ;
- génération de niveau procédurale ;
- éditeur de niveau destiné au public.

---

# 5. EXPÉRIENCE DE JEU CIBLE

## 5.1 Durée

Durée totale cible : **12 à 15 minutes** lors d’une première partie.

Durée cible par segment :

| Segment | Durée |
|---|---:|
| Introduction et lancement | 30 à 45 s |
| Approche de la bataille | 2 min |
| Percée dans la flotte | 3 min |
| Défense de l’Aegis Citadel | 2 min |
| Couloir d’appontage | 1 à 2 min |
| Prise de contrôle | 30 à 45 s |
| Boss final | 3 à 4 min |
| Conclusion | 30 s |

## 5.2 Courbe d’intensité

L’intensité doit suivre cette progression :

1. prise en main calme ;
2. première vague simple ;
3. apparition des bonus ;
4. arrivée d’ennemis plus gros ;
5. mini-boss ;
6. bataille à grande échelle ;
7. accalmie courte ;
8. appontage technique mais tolérant ;
9. révélation de la forteresse ;
10. boss final ;
11. super-attaque conclusive.

## 5.3 Difficulté

La difficulté par défaut doit être **nerveuse mais accessible**.

Principes :

- aucun ennemi ordinaire ne doit tuer en un coup ;
- un choc retire une portion de bouclier ;
- invulnérabilité temporaire après impact ;
- hitbox du joueur plus petite que le modèle ;
- bonus attirés magnétiquement à courte distance ;
- projectiles dangereux très contrastés ;
- vitesse des projectiles modérée ;
- motifs lisibles et annoncés ;
- checkpoints avant l’appontage et avant le boss ;
- continues illimités pour la démo ;
- le joueur conserve au moins un niveau de puissance après une destruction.

---

# 6. DÉROULEMENT DU NIVEAU

## 6.1 Segment 1 — Launch Vector

### Objectif

Décoller du porte-chasseur `Aurora Spear` et rejoindre la bataille.

### Mise en scène

- baie de lancement intérieure ;
- catapulte ;
- portes qui s’ouvrent sur une planète et une flotte ;
- transition automatique vers la caméra de gameplay.

### Gameplay

- mouvement ;
- tir principal ;
- premiers drones lents ;
- aucun projectile ennemi pendant les dix premières secondes ;
- tutorial prompts discrets.

### Critères

- le joueur doit comprendre le déplacement et le tir sans lire un écran de texte ;
- première sensation de vitesse ;
- aucun risque de mort.

## 6.2 Segment 2 — Broken Formation

### Objectif

Traverser les lignes de drones du Null Choir.

### Ennemis

- scouts ;
- intercepteurs ;
- mines orbitales ;
- premières tourelles de frégate.

### Nouveaux systèmes

- bonus de puissance ;
- missiles ;
- bonus de bouclier ;
- multiplicateur de score.

### Événement visuel

Une frégate alliée traverse l’arrière-plan puis est attaquée. Le joueur détruit les unités qui l’encerclent.

## 6.3 Segment 3 — The Frigate Wall

### Objectif

Ouvrir un passage à travers une formation de trois frégates.

### Gameplay

- ennemis plus résistants ;
- tourelles ciblables ;
- points faibles lumineux ;
- projectiles en éventail ;
- missiles télégraphiés ;
- première utilisation recommandée de l’Overdrive.

### Mini-boss

`Choir Harvester`

- trois bras ;
- noyau central protégé ;
- alternance de balayages et d’invocations ;
- durée cible : 60 à 90 secondes.

## 6.4 Segment 4 — Citadel Under Siege

### Objectif

Défendre les batteries externes de l’Aegis Citadel.

### Mise en scène

La forteresse entre progressivement dans le champ, d’abord en arrière-plan, puis sous la zone de jeu.

### Gameplay

- trois objectifs défensifs ;
- ennemis qui attaquent la forteresse ;
- le joueur peut détruire les missiles avant impact ;
- soutien de chasseurs alliés ;
- larges explosions en profondeur sans masquer le plan de jeu.

### Condition de réussite

Au moins une batterie doit survivre. En mode standard, une batterie ne peut pas être détruite avant une durée minimale garantissant une chance de réaction.

## 6.5 Segment 5 — Docking Run

### Objectif

Entrer dans la baie d’appontage.

### Transition

La caméra passe d’une vue verticale élevée à une perspective plus basse et plus rapprochée.

### Gameplay

- trajectoire guidée ;
- portes et structures à éviter ;
- tir toujours disponible ;
- drones poursuivant le joueur ;
- freinage automatique à l’approche finale ;
- zones d’assistance invisibles qui corrigent légèrement la trajectoire ;
- collision non létale : perte de bouclier et recentrage.

### Moment clé

Le chasseur s’arrime à un rail mobile. Le joueur conserve le contrôle jusqu’à l’accrochage.

## 6.6 Segment 6 — Command Transfer

### Objectif

Transférer l’interface du chasseur au noyau de la forteresse.

### Forme

Séquence interactive de 30 à 45 secondes :

- alignement de trois signatures énergétiques ;
- maintien d’une touche ;
- activation successive des batteries ;
- aucun échec définitif ;
- la vitesse de réussite influence seulement un bonus de score.

### Transition

Le HUD du chasseur se transforme progressivement en interface tactique de forteresse.

## 6.7 Segment 7 — The Pale Leviathan

### Objectif

Détruire le vaisseau-amiral ennemi à l’aide de la forteresse.

Décrit en détail dans la section Boss final.

---

# 7. CONTRÔLES

## 7.1 Clavier

| Action | Touche par défaut |
|---|---|
| Déplacement | WASD ou flèches |
| Tir principal | Espace |
| Arme secondaire | Ctrl gauche |
| Overdrive | Maj gauche |
| Changement de configuration de tir | E |
| Focus / précision | Alt gauche |
| Pause | Échap |
| Validation UI | Entrée / Espace |
| Retour UI | Échap |

Les touches doivent être remappables.

## 7.2 Manette

Disposition Xbox de référence :

| Action | Contrôle |
|---|---|
| Déplacement | Stick gauche |
| Tir principal | A ou RT |
| Arme secondaire | X ou RB |
| Overdrive | Y ou LB |
| Changement de configuration | B |
| Focus | LT |
| Pause | Menu |

Les glyphes affichés doivent s’adapter au dernier périphérique utilisé.

## 7.3 Sensations

- accélération courte ;
- décélération courte ;
- vitesse maximale atteinte en moins de 250 ms ;
- inertie visible mais faible ;
- inclinaison visuelle du chasseur sans modifier la hitbox ;
- réponse immédiate au tir ;
- vibration manette optionnelle ;
- petite secousse de caméra sur tirs lourds ;
- secousse réduite ou désactivable.

---

# 8. SYSTÈME DU JOUEUR

## 8.1 Statistiques de base

Valeurs initiales à équilibrer, stockées dans des ressources de données :

- bouclier maximal ;
- vitesse ;
- accélération ;
- cadence ;
- puissance ;
- vitesse des projectiles ;
- délai d’invulnérabilité ;
- capacité d’Overdrive ;
- force d’attraction des bonus.

Aucune valeur majeure ne doit être codée en dur dans la logique.

## 8.2 Hitbox

- représentation debug activable ;
- hitbox centrale plus petite que le modèle ;
- collision avec projectiles ennemis sur le plan logique ;
- collision environnementale séparée ;
- collision de ram avec ennemis non létale en difficulté standard.

## 8.3 Bouclier

- 100 unités au départ ;
- impacts ordinaires : 10 à 25 unités ;
- régénération lente après plusieurs secondes sans impact ;
- bonus de bouclier : récupération immédiate ;
- effet visuel sphérique bref à l’impact ;
- alerte sonore sous 25 % ;
- pas d’écran rouge permanent.

## 8.4 Vies et continues

Pour le prototype :

- trois vies visuelles ;
- continues illimités ;
- reprise au dernier checkpoint ;
- le score de session conserve une pénalité ;
- le joueur ne recommence jamais plus de deux minutes de contenu.

---

# 9. ARMEMENT DU CHASSEUR

## 9.1 Tir principal — Pulse Array

Arme automatique de base.

### Niveaux de puissance

| Niveau | Effet |
|---:|---|
| 1 | double tir frontal |
| 2 | cadence accrue |
| 3 | deux tirs latéraux faibles |
| 4 | trois axes renforcés |
| 5 | faisceau central intermittent et tirs latéraux complets |

Chaque niveau doit modifier :

- la géométrie du tir ;
- le son ;
- les effets lumineux ;
- la sensation d’impact ;
- le HUD.

Le nombre d’objets de projectile doit rester maîtrisé grâce au système de pooling et au Bullet Manager.

## 9.2 Configurations de tir

Le bouton de configuration alterne entre :

### Spread Mode

- large couverture ;
- dégâts unitaires modérés ;
- adapté aux vagues.

### Lance Mode

- tir concentré ;
- dégâts élevés ;
- moins large ;
- adapté aux cibles lourdes.

### Orbit Mode

Débloqué temporairement par bonus :

- deux drones orbitaux ;
- tirs auxiliaires ;
- durée limitée ou perte progressive d’énergie.

Le changement doit être instantané avec un cooldown très court empêchant le spam audio.

## 9.3 Missiles secondaires

- verrouillage doux automatique ;
- nombre limité de salves ;
- recharge par bonus ;
- priorité aux ennemis lourds ;
- trajectoires visuelles courbes ;
- fumée GPU ;
- dégâts de zone faibles ;
- aucune interruption du tir principal.

## 9.4 Overdrive

### Activation

Une jauge se remplit par :

- destruction d’ennemis ;
- collecte de bonus ;
- esquive proche ;
- protection d’un objectif.

### Effets

Pendant 5 à 8 secondes :

- cadence augmentée ;
- puissance augmentée ;
- vitesse légèrement augmentée ;
- bouclier partiel ;
- attraction des bonus renforcée ;
- musique enrichie ;
- colorimétrie subtilement modifiée.

### Contraintes

- ne pas saturer l’écran ;
- ne pas empêcher de distinguer les tirs ennemis ;
- aucun flash blanc prolongé.

---

# 10. BONUS ET PROGRESSION DE PUISSANCE

## 10.1 Types de bonus

| Bonus | Fonction | Couleur |
|---|---|---|
| Power Core | augmente le niveau de tir | jaune-or |
| Shield Cell | restaure le bouclier | cyan |
| Missile Rack | recharge les missiles | orange |
| Orbit Drone | ajoute un drone temporaire | violet |
| Overdrive Shard | remplit la jauge | magenta |
| Score Prism | augmente le score | vert |
| Rescue Beacon | restaure une vie ou donne un gros bouclier | blanc |

Les couleurs ne doivent jamais être les seules informations. Chaque bonus possède aussi :

- une forme ;
- une icône ;
- un son ;
- un effet de halo distinct.

## 10.2 Comportement

- léger flottement ;
- rotation ;
- attraction magnétique à courte portée ;
- disparition après délai annoncé ;
- pas de disparition pendant une cinématique ;
- collecte possible même lors d’un appontage assisté.

## 10.3 Règles de progression

- le joueur doit atteindre au minimum le niveau 3 avant le mini-boss ;
- le niveau 5 doit être accessible avant la défense de la forteresse ;
- les drops sont semi-déterministes ;
- le système garantit un bonus utile après une période sans amélioration ;
- un joueur en difficulté reçoit davantage de boucliers ;
- le jeu ne doit pas annoncer explicitement l’assistance dynamique.

---

# 11. ENNEMIS

## 11.1 Familles

### Needle Scout

- faible ;
- trajectoire simple ;
- tir frontal lent ;
- utilisé en formation.

### Crescent Interceptor

- mouvement latéral ;
- tire en petits arcs ;
- fuit après une passe.

### Choir Mine

- stationnaire ;
- pulse radial annoncé ;
- peut être détruite avant déclenchement.

### Leech Drone

- cherche à s’attacher au joueur ;
- ralentit temporairement ;
- fragile.

### Frigate Turret

- ancrée sur une frégate ;
- balayage ;
- point faible.

### Null Bomber

- lent ;
- largue des mines ;
- explosion spectaculaire.

### Shield Carrier

- protège les unités proches ;
- priorité tactique ;
- bouclier clairement visible.

## 11.2 Principes de patterns

- peu de projectiles très rapides ;
- davantage de projectiles lents et lisibles ;
- alternance entre zones sûres larges et corridors ;
- télégraphie de 300 à 800 ms selon l’attaque ;
- aucun motif ne doit être impossible à lire sur fond lumineux ;
- projectiles dangereux dotés d’un contour ou halo constant ;
- projectiles décoratifs visuellement différents.

## 11.3 Spawning

Le niveau doit être orchestré par des données de timeline et non par une succession de délais dispersés dans le code.

Créer un système de `EncounterDirector` capable de :

- déclencher une vague à une position de progression ;
- attendre une condition ;
- synchroniser musique, caméra et ennemis ;
- lancer une transmission ;
- poser un checkpoint ;
- déclencher un mini-boss ;
- gérer une variation de difficulté.

---

# 12. BOSS FINAL — THE PALE LEVIATHAN

## 12.1 Intention

Le boss doit être la démonstration majeure du projet. Il oppose deux structures colossales sans perdre la lisibilité d’un shooter.

Le joueur contrôle les systèmes de l’Aegis Citadel depuis une interface tactique.

## 12.2 Changement de commandes

Pendant la phase forteresse :

- déplacement limité de la forteresse sur un axe ou dans une zone restreinte ;
- curseur tactique ou réticule piloté avec le stick ;
- batterie principale automatique ou maintenue ;
- sélection de sous-systèmes ;
- défense ponctuelle ;
- super-arme chargée.

Le changement doit rester proche des commandes précédentes :

- déplacement ;
- tir ;
- secondaire ;
- Overdrive devenu `Citadel Burst`.

## 12.3 Arsenal de la forteresse

### Point Defense Grid

- tir automatique sur petits ennemis ;
- améliorable temporairement ;
- donne une sensation de bataille massive.

### Twin Rail Batteries

- tir principal ;
- trajectoire visible ;
- forte sensation de recul ;
- alternance gauche/droite.

### Aegis Shield

- arme secondaire ;
- protection orientable ou temporaire ;
- absorbe les salves lourdes.

### Helios Lance

- super-arme finale ;
- nécessite trois étapes de charge ;
- ne doit pas être utilisable avant la dernière phase.

## 12.4 Phase 1 — Armor Choir

Objectifs :

- détruire quatre plaques d’armure ;
- repousser des vagues de drones ;
- protéger les batteries alliées.

Attaques :

- éventails lents ;
- lasers annoncés ;
- missiles ciblables.

Durée : 60 à 75 secondes.

## 12.5 Phase 2 — Gravitic Maw

Le boss ouvre son noyau.

Gameplay :

- aspiration légère ;
- débris traversant l’écran ;
- zones de gravité ;
- utilisation du bouclier ;
- tirs concentrés sur trois nœuds.

Durée : 60 secondes.

## 12.6 Phase 3 — Boarding Swarm

Le boss lance des unités d’abordage.

Gameplay :

- point defense ;
- priorités multiples ;
- destruction de transports ;
- jauge d’intégrité de la forteresse ;
- soutien du chasseur du joueur visible dans la baie ou via drones relais.

Durée : 45 à 60 secondes.

## 12.7 Phase 4 — Helios Lance

Séquence finale :

1. détruire deux conduits exposés ;
2. tenir pendant la charge ;
3. aligner le réticule ;
4. déclencher le tir ;
5. conserver un court contrôle pendant la cinématique interactive ;
6. destruction du boss.

L’attaque finale doit être spectaculaire mais durer moins de 15 secondes.

## 12.8 Échec

En cas de destruction de la forteresse :

- reprise au début de la phase en cours ;
- courte animation de réinitialisation ;
- aucune cinématique longue à revoir.

---

# 13. DIFFICULTÉ ADAPTATIVE ET ACCESSIBILITÉ

## 13.1 Modes

### Story

- projectiles plus lents ;
- dégâts réduits ;
- assistance d’appontage forte ;
- régénération accrue ;
- plus de bonus.

### Vanguard — défaut

- expérience cible ;
- nerveuse mais tolérante.

### Ace

- patterns plus denses ;
- dégâts plus élevés ;
- assistance réduite ;
- score majoré.

## 13.2 Ajustements dynamiques autorisés

En Story et Vanguard :

- chance de bonus de bouclier ;
- vitesse de certains projectiles ;
- délai entre salves ;
- quantité de missiles secondaires ;
- assistance de trajectoire ;
- durée d’invulnérabilité.

Ne jamais modifier brutalement ces paramètres pendant une attaque en cours.

## 13.3 Options d’accessibilité

- remappage complet ;
- taille du HUD ;
- réduction des secousses ;
- réduction des flashs ;
- désactivation de l’aberration chromatique ;
- intensité du bloom ;
- mode contraste renforcé ;
- couleurs alternatives des projectiles ;
- sous-titres ;
- volume séparé musique, SFX et voix ;
- pause à tout moment hors cinématique finale très courte ;
- maintien ou bascule pour le tir continu ;
- assistance d’appontage réglable.

---

# 14. SCORE ET REJOUABILITÉ

## 14.1 Score

Le score récompense :

- destruction ;
- enchaînement ;
- protection d’alliés ;
- collecte de prismes ;
- esquive proche ;
- efficacité contre les boss ;
- survie des batteries ;
- vitesse du transfert de commande.

## 14.2 Multiplicateur

- augmente sans recevoir de dégâts ;
- baisse partiellement à l’impact ;
- ne retombe pas systématiquement à zéro ;
- plafonné ;
- affichage discret.

## 14.3 Résumé de fin

Afficher :

- score total ;
- rang ;
- précision ;
- ennemis détruits ;
- dégâts reçus ;
- batteries sauvées ;
- bonus collectés ;
- temps ;
- meilleur combo ;
- difficulté ;
- invitation à rejouer.

---

# 15. DIRECTION ARTISTIQUE

## 15.1 Style

Style cible :

- space opera militaire ;
- rétrofuturisme ;
- silhouettes mécaniques fortes ;
- matériaux PBR ;
- cel shading léger ou éclairage stylisé ;
- accents lumineux ;
- palette contrôlée ;
- détails de surface ;
- vastes arrière-plans spatiaux ;
- explosions volumétriques stylisées.

Le rendu ne doit pas chercher le photoréalisme total. L’objectif est un rendu cohérent, maîtrisé et spectaculaire.

## 15.2 Palette

### Helios Vanguard

- blanc cassé ;
- bleu profond ;
- cyan ;
- or ;
- touches rouges de sécurité.

### Null Choir

- anthracite ;
- violet sombre ;
- ivoire froid ;
- magenta ;
- vert maladif limité.

### Projectiles

- alliés : cyan, bleu, or ;
- ennemis : rouge corail, magenta, orange ;
- bonus : couleurs normalisées définies plus haut.

## 15.3 Chasseur du joueur — Specter-9

Contraintes :

- silhouette triangulaire ;
- deux propulseurs principaux ;
- ailes courtes ;
- nez central ;
- cockpit visible mais non inspiré d’un modèle existant ;
- panneaux blancs et bleu sombre ;
- lignes lumineuses cyan ;
- pièces mobiles uniquement pour les aérofreins et armes ;
- aucune transformation humanoïde.

## 15.4 Aegis Citadel

Contraintes :

- silhouette lisible à très grande distance ;
- noyau central prismatique ;
- deux bras-batteries ;
- grande baie d’appontage ;
- surfaces segmentées ;
- lumières d’échelle ;
- éléments animés ;
- zones de dégâts ;
- aucune silhouette proche d’une forteresse existante de licence connue.

## 15.5 The Pale Leviathan

Contraintes :

- asymétrique ;
- mélange de métal et de formes organiques ;
- grand anneau incomplet ;
- noyau visible ;
- appendices articulés ;
- surfaces sombres ;
- fissures lumineuses ;
- phases de transformation limitées aux ouvertures mécaniques.

---

# 16. CAMÉRA ET MISE EN SCÈNE

## 16.1 Caméra de gameplay

- perspective ;
- faible angle ;
- champ de vision stable ;
- position contrôlée par rails et zones ;
- pas de caméra libre ;
- anticipation légère du déplacement ;
- zoom contextuel lent ;
- caméra jamais attachée directement aux vibrations du modèle.

## 16.2 Plan de gameplay

Le joueur se déplace dans un rectangle logique 2D.

Le système doit :

- convertir l’entrée en coordonnées du plan ;
- contraindre la position ;
- séparer position logique et inclinaison visuelle ;
- préserver la cohérence des collisions ;
- permettre à la caméra de se déplacer indépendamment.

## 16.3 Screen shake

Utiliser un système centralisé avec :

- amplitude ;
- fréquence ;
- durée ;
- catégorie ;
- multiplicateur d’accessibilité ;
- cumul plafonné.

Les secousses décoratives ne doivent jamais perturber l’esquive.

## 16.4 Cinématiques

Toutes les cinématiques sont réalisées dans le moteur.

Durée maximale sans interaction :

- introduction : 15 secondes ;
- arrivée de la forteresse : 8 secondes ;
- appontage final : 8 secondes ;
- transformation du HUD : 10 secondes ;
- destruction finale : 15 secondes.

Prévoir skip après une première visualisation, sauf transitions techniques très courtes.

---

# 17. EFFETS VISUELS

## 17.1 Principes

- effets basés sur particules GPU ;
- utilisation de trails ;
- bloom maîtrisé ;
- matériaux emissifs ;
- distorsion limitée ;
- decals ou marques temporaires ;
- débris instanciés ;
- transparences limitées ;
- aucun effet plein écran prolongé.

## 17.2 Explosions

Trois catégories :

1. petite explosion de drone ;
2. explosion moyenne d’appareil ;
3. explosion lourde de structure.

Chaque catégorie possède :

- flash bref ;
- volume principal ;
- étincelles ;
- débris ;
- onde de choc ;
- son ;
- lumière temporaire.

La lumière temporaire doit être limitée pour éviter un coût GPU excessif.

## 17.3 Projectiles

Chaque projectile doit avoir :

- cœur lumineux ;
- halo ;
- trail ;
- couleur d’équipe ;
- taille cohérente avec sa hitbox ;
- LOD ou simplification selon distance.

## 17.4 Post-traitement

Prévoir des profils :

- Gameplay ;
- Overdrive ;
- Docking ;
- Fortress ;
- Victory.

Effets autorisés :

- tonemapping ;
- glow ;
- vignette très légère ;
- color grading ;
- TAA ou FSR2 ;
- SSAO si le budget le permet ;
- brouillard volumétrique localisé ;
- profondeur de champ uniquement pour les cinématiques ;
- aberration chromatique très légère et désactivable.

---

# 18. AUDIO

## 18.1 Direction musicale

Musique originale :

- synthétiseurs analogiques ;
- percussions orchestrales ;
- lignes de basse électroniques ;
- montée héroïque ;
- motifs musicaux originaux ;
- aucune imitation d’un thème existant.

## 18.2 États musicaux

- launch ;
- skirmish ;
- fleet battle ;
- docking ;
- fortress awakening ;
- boss phase 1 ;
- boss phase 2 ;
- final charge ;
- victory.

Les transitions doivent être musicales, pas de simples coupures.

## 18.3 SFX

Familles :

- tirs ;
- impacts ;
- boucliers ;
- moteurs ;
- missiles ;
- explosions ;
- bonus ;
- UI ;
- alarmes ;
- appontage ;
- batteries lourdes ;
- super-arme.

## 18.4 Voix

Voix radio courtes, optionnelles :

- commandante ;
- opérateur tactique ;
- IA de bord.

Limiter à une dizaine de répliques. Toujours fournir les sous-titres.

## 18.5 Pipeline audio

Formats de travail possibles :

- WAV source ;
- OGG pour livraison ;
- normalisation ;
- bus séparés ;
- compression légère ;
- limiteur master ;
- aucun clipping.

---

# 19. UI ET UX

## 19.1 HUD chasseur

Afficher :

- bouclier ;
- niveau de puissance ;
- missiles ;
- Overdrive ;
- score ;
- multiplicateur ;
- objectif courant ;
- indicateur de boss ;
- indicateur de danger hors écran.

## 19.2 HUD forteresse

Afficher :

- intégrité ;
- batteries ;
- bouclier ;
- charge Helios Lance ;
- sous-systèmes ;
- boss ;
- objectifs.

Le passage du HUD chasseur au HUD forteresse doit être animé.

## 19.3 Style

- lignes fines ;
- panneaux translucides ;
- cyan et or pour l’allié ;
- typographie lisible ;
- inspiration cockpit futuriste originale ;
- marges suffisantes ;
- compatibilité 16:9 ;
- prise en charge 1080p, 1440p et 4K.

## 19.4 Menus

Menu principal :

- Play ;
- Options ;
- Credits ;
- Quit.

Options :

- Display ;
- Graphics ;
- Audio ;
- Controls ;
- Accessibility.

---

# 20. ARCHITECTURE LOGICIELLE

## 20.1 Principes

- composition plutôt qu’héritage profond ;
- signaux pour les événements ;
- ressources de données pour les paramètres ;
- autoloads limités ;
- dépendances explicites ;
- scènes petites ;
- logique testable ;
- aucune référence circulaire ;
- aucune recherche répétée par chemin de scène dans les boucles critiques ;
- aucune allocation massive par frame.

## 20.2 Autoloads autorisés

Maximum recommandé :

- `GameState`
- `AudioManager`
- `SceneRouter`
- `SettingsManager`
- `Telemetry`
- `DebugTools`

Ne pas créer un singleton par fonctionnalité.

## 20.3 Composants principaux

### GameFlowController

Gère :

- menu ;
- lancement ;
- pause ;
- checkpoint ;
- victoire ;
- défaite ;
- changement de mode.

### EncounterDirector

Gère la timeline du niveau.

### PlayerFighterController

Gère l’entrée, le mouvement et l’état du chasseur.

### WeaponController

Gère les armes et configurations.

### BulletManager

Gère les projectiles à haute densité.

### EnemyController

Base de composition pour ennemis.

### BossController

Machine à états du boss.

### FortressController

Contrôle de la forteresse.

### CameraDirector

Rails, transitions, shakes et zooms.

### VFXManager

Pools d’effets visuels.

### AudioManager

Musique adaptative et SFX.

### DifficultyDirector

Paramètres de difficulté et assistance discrète.

### PickupManager

Drops, garantie de progression et attraction.

## 20.4 Machine à états globale

États minimum :

- BOOT
- MAIN_MENU
- LOADING
- FIGHTER_INTRO
- FIGHTER_COMBAT
- CITADEL_DEFENSE
- DOCKING
- COMMAND_TRANSFER
- FORTRESS_COMBAT
- BOSS_FINAL
- VICTORY
- GAME_OVER
- PAUSED

Les transitions doivent être centralisées et journalisées.

---

# 21. SYSTÈME DE PROJECTILES

## 21.1 Problème

Un shooter peut contenir plusieurs centaines de projectiles. Des centaines de `Area3D` individuelles peuvent devenir coûteuses.

## 21.2 Solution cible

Implémenter un `BulletManager` data-oriented :

- tableau de positions logiques ;
- tableau de vitesses ;
- tableau de rayons ;
- tableau d’équipes ;
- tableau de durées de vie ;
- tableau de dégâts ;
- tableau de styles ;
- pool d’indices libres ;
- rendu par `MultiMeshInstance3D` ou groupes de MultiMesh ;
- collision sur le plan logique 2D ;
- grille spatiale simple pour réduire les comparaisons ;
- swept collision pour projectiles rapides ;
- aucune allocation par projectile pendant le gameplay.

## 21.3 Limites

Budgets initiaux :

- 600 projectiles actifs ;
- 150 projectiles alliés ;
- 450 projectiles ennemis ;
- 100 effets d’impact concurrents ;
- 80 ennemis mineurs visibles ;
- 20 unités lourdes ;
- 1 boss.

Ces valeurs sont des plafonds, pas des objectifs visuels permanents.

## 21.4 Lisibilité

Le rendu des projectiles doit être séparé par équipe et priorité. Les projectiles dangereux passent avant certains effets décoratifs.

---

# 22. DONNÉES ET RESSOURCES

## 22.1 Données pilotées

Créer des ressources personnalisées pour :

- `WeaponData`
- `ProjectileData`
- `EnemyData`
- `PickupData`
- `EncounterData`
- `BossPhaseData`
- `DifficultyProfile`
- `AudioCueData`
- `VFXProfile`
- `GraphicsPreset`

## 22.2 Règles

- les ressources contiennent des données, pas une logique métier lourde ;
- aucune duplication silencieuse ;
- valeurs documentées ;
- unités explicites ;
- valeurs de défaut sûres ;
- validation au chargement ;
- message d’erreur clair pour toute donnée invalide.

---

# 23. STRUCTURE DU DÉPÔT

```text
aegis-ascendant/
├─ CLAUDE.md
├─ README.md
├─ LICENSES.md
├─ project.godot
├─ export_presets.cfg
├─ .gitignore
├─ .gitattributes
├─ .mcp.json
├─ .claude/
│  ├─ settings.json
│  ├─ agents/
│  │  ├─ gameplay-architect.md
│  │  ├─ godot-reviewer.md
│  │  ├─ performance-auditor.md
│  │  ├─ asset-integrator.md
│  │  └─ qa-agent.md
│  └─ skills/
│     ├─ implement-feature/
│     │  └─ SKILL.md
│     ├─ run-quality-gate/
│     │  └─ SKILL.md
│     └─ create-encounter/
│        └─ SKILL.md
├─ assets/
│  ├─ source/
│  │  ├─ blender/
│  │  ├─ textures/
│  │  ├─ audio/
│  │  └─ concepts/
│  ├─ imported/
│  │  ├─ models/
│  │  ├─ textures/
│  │  ├─ sprites/
│  │  ├─ vfx/
│  │  ├─ audio/
│  │  └─ fonts/
│  └─ licenses/
├─ scenes/
│  ├─ boot/
│  ├─ menus/
│  ├─ gameplay/
│  ├─ player/
│  ├─ enemies/
│  ├─ bosses/
│  ├─ fortress/
│  ├─ projectiles/
│  ├─ pickups/
│  ├─ vfx/
│  ├─ ui/
│  └─ debug/
├─ scripts/
│  ├─ core/
│  ├─ gameplay/
│  ├─ player/
│  ├─ enemies/
│  ├─ bosses/
│  ├─ fortress/
│  ├─ projectiles/
│  ├─ pickups/
│  ├─ ui/
│  ├─ tools/
│  └─ debug/
├─ resources/
│  ├─ weapons/
│  ├─ enemies/
│  ├─ encounters/
│  ├─ difficulty/
│  ├─ vfx/
│  └─ graphics/
├─ shaders/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ scenes/
│  └─ test_runner.gd
├─ tools/
│  ├─ blender/
│  ├─ texture/
│  └─ validation/
├─ scripts-win/
│  ├─ bootstrap.ps1
│  ├─ run.ps1
│  ├─ check.ps1
│  ├─ import-assets.ps1
│  ├─ build-debug.ps1
│  ├─ build-release.ps1
│  └─ profile.ps1
├─ docs/
│  ├─ architecture/
│  ├─ art/
│  ├─ balance/
│  ├─ decisions/
│  └─ captures/
└─ build/
```

---

# 24. PIPELINE D’ASSETS

## 24.1 Principe général

Les assets passent par quatre états :

1. concept ;
2. source ;
3. asset nettoyé ;
4. asset importé dans Godot.

Aucun asset généré par IA ne doit être intégré directement sans contrôle.

## 24.2 Modèles 3D

Pipeline recommandé :

1. concept art ;
2. blockout Blender ;
3. génération assistée éventuelle ;
4. retopologie ;
5. UV ;
6. textures PBR ;
7. optimisation ;
8. pivots et échelle ;
9. export glTF 2.0 ;
10. import Godot ;
11. création de scène héritée ;
12. collisions séparées ;
13. test de performance.

## 24.3 Blender

Blender constitue l’outil principal de préparation.

L’agent peut produire des scripts Python Blender pour :

- générer un blockout ;
- appliquer des matériaux ;
- créer des variations ;
- placer des points d’attache ;
- nommer les meshes ;
- exporter en glTF ;
- créer des LOD simples.

Les scripts doivent être versionnés.

## 24.4 Textures

Formats et tailles :

- héros : 2K à 4K ;
- ennemis lourds : 2K ;
- petits ennemis : 1K à 2K ;
- atlas quand pertinent ;
- compression contrôlée ;
- normal maps ;
- roughness ;
- metallic ;
- emissive ;
- AO si utile.

Les textures 4K sont réservées aux objets réellement proches de la caméra.

## 24.5 Sprites détaillés

Les sprites sont utilisés pour :

- projectiles ;
- impacts ;
- halos ;
- explosions ;
- éléments HUD ;
- illustrations de menu ;
- portraits radio.

Exigences :

- PNG ou format importable adapté ;
- alpha propre ;
- fond transparent ;
- pas de franges ;
- cohérence de perspective ;
- atlas versionné ;
- fichier source conservé ;
- licence enregistrée.

## 24.6 Outils IA possibles

Catégories possibles, sans dépendance obligatoire à un fournisseur :

- génération d’images pour concepts ;
- génération de textures ;
- génération de modèles 3D ;
- génération de voix temporaires ;
- génération de bruitages ;
- génération musicale ;
- assistance Blender ;
- upscale et nettoyage.

Pour chaque outil :

- enregistrer le fournisseur ;
- enregistrer la date ;
- enregistrer le prompt ;
- enregistrer le compte ou type de licence ;
- vérifier les droits d’usage ;
- conserver le fichier original ;
- documenter les retouches humaines.

## 24.7 Fichier de provenance

Créer `assets/licenses/ASSET_PROVENANCE.csv` avec :

```csv
asset_id,file_path,asset_type,source_tool,source_url,author,license,generated_date,prompt_file,modified_by,notes
```

Aucune ligne vide pour un asset livré.

## 24.8 Git LFS

Utiliser Git LFS pour les gros binaires :

- `.blend`
- `.glb`
- `.gltf` si volumineux
- `.png` volumineux
- `.wav`
- `.ogg`
- captures vidéo
- exports de build si temporairement versionnés

Ne pas versionner le cache Godot.

---

# 25. RENDU ET GPU NVIDIA

## 25.1 Renderer

- Forward+ obligatoire pour la cible principale ;
- Direct3D 12 à tester en priorité sous Windows ;
- Vulkan conservé comme option de compatibilité ;
- aucun choix de driver ne doit être considéré valide sans test sur la machine cible.

## 25.2 Cible de performance

### Machine de développement RTX 4080

- 2560 × 1440 ;
- 120 FPS cible ;
- 60 FPS minimum absolu ;
- frametime sans pics perceptibles ;
- qualité High par défaut.

### Machine de référence secondaire

Objectif à valider :

- Windows 10/11 ;
- GPU de classe RTX 2060 ou équivalent ;
- 1920 × 1080 ;
- 60 FPS ;
- qualité Medium.

Ces valeurs sont des objectifs produit, pas des garanties matérielles.

## 25.3 Budgets

À 120 FPS :

- frame totale : 8,33 ms ;
- gameplay CPU : idéalement < 2,0 ms ;
- physique/collisions : idéalement < 1,5 ms ;
- rendu GPU : idéalement < 6,5 ms ;
- pics exceptionnels : < 12 ms.

À 60 FPS :

- frame totale : 16,67 ms ;
- aucun pic récurrent > 25 ms.

## 25.4 Réglages graphiques

### Low

- particules réduites ;
- ombres réduites ;
- effets volumétriques désactivés ;
- résolution interne réduite ;
- FSR2 Performance ou équivalent validé ;
- SSAO désactivé.

### Medium

- particules moyennes ;
- ombres moyennes ;
- volumétrie limitée ;
- FSR2 Quality ou TAA ;
- bloom modéré.

### High

- particules élevées ;
- ombres élevées ;
- volumétrie ;
- FSR2 Quality ou rendu natif ;
- effets complets.

### Ultra

- réservé à la RTX 4080 de démonstration ;
- résolution native ou supérieure selon test ;
- particules maximales ;
- ombres maximales raisonnables ;
- effets cinématiques ;
- aucune option ne doit réduire la lisibilité.

## 25.5 FSR2 et antialiasing

Prévoir une option parmi :

- TAA natif ;
- FSR2 natif pour antialiasing ;
- FSR2 Quality ;
- FSR2 Balanced ;
- FXAA en fallback.

Le choix par défaut doit être établi par comparaison réelle d’image et de performance.

## 25.6 Variable Rate Shading

Le VRS peut être proposé sur les GPU compatibles.

Règles :

- désactivable ;
- jamais appliqué au HUD ;
- ne doit pas dégrader les projectiles ;
- validation visuelle obligatoire ;
- mesure avant/après obligatoire.

## 25.7 Shader stutter

- précharger les effets critiques ;
- déclencher une scène de warm-up au chargement ;
- tester les compilations de pipelines ;
- éviter la création d’un nouveau shader au milieu du boss ;
- enregistrer les pics de frame ;
- produire une capture de profilage.

## 25.8 Profilage

Utiliser :

- profiler Godot ;
- moniteurs de performance ;
- logs de frametime ;
- NVIDIA Nsight Graphics si nécessaire ;
- captures avant/après optimisation.

Aucune optimisation ne doit être réalisée uniquement sur intuition.

---

# 26. PERFORMANCE DU GAMEPLAY

## 26.1 Pooling obligatoire

Pooler :

- projectiles ;
- ennemis fréquents ;
- impacts ;
- explosions ;
- pickups ;
- débris ;
- labels de dégâts si utilisés.

## 26.2 Allocation

Interdire dans les boucles critiques :

- création répétée de tableaux ;
- concaténation importante de chaînes ;
- chargement de ressources ;
- instanciation massive ;
- parsing JSON ;
- appels de recherche de nœud répétés.

## 26.3 Décor

Utiliser :

- frustum culling ;
- LOD ;
- visibility ranges ;
- MultiMesh ;
- occlusion culling uniquement lorsqu’il apporte un gain dans les sections internes ;
- réduction des lumières dynamiques ;
- matériaux partagés ;
- atlas.

## 26.4 Physique

- gameplay sur plan logique ;
- collisions custom pour projectiles ;
- physique Godot réservée aux acteurs principaux et obstacles ;
- éviter les corps rigides pour les débris purement visuels ;
- débris GPU si possible.

---

# 27. EXPORT WINDOWS

## 27.1 Livrable

Créer :

```text
build/windows/AegisAscendant.exe
build/windows/AegisAscendant.pck
build/windows/README.txt
build/windows/LICENSES.txt
```

L’intégration du PCK dans l’exécutable peut être utilisée après validation.

## 27.2 Exigences

- Windows x64 ;
- icône originale ;
- nom propre dans la fenêtre ;
- mode plein écran sans bordure par défaut ;
- option fenêtrée ;
- aucune console visible en release ;
- logs dans un répertoire utilisateur ;
- build reproductible ;
- numéro de version ;
- crédits ;
- licences.

## 27.3 Scripts PowerShell

### `bootstrap.ps1`

- vérifie Godot ;
- vérifie les export templates ;
- vérifie Git LFS ;
- initialise les dossiers ;
- lance l’import initial ;
- affiche les erreurs clairement.

### `run.ps1`

- lance le projet ;
- transmet les options debug ;
- retourne le code de sortie.

### `check.ps1`

- vérifie format et fichiers ;
- lance l’import headless ;
- lance les tests ;
- détecte erreurs et warnings critiques ;
- valide les assets ;
- vérifie la provenance ;
- retourne un code non nul en cas d’échec.

### `build-release.ps1`

- nettoie le dossier de build ;
- exécute `check.ps1` ;
- exporte Windows release ;
- vérifie la présence des fichiers ;
- génère un manifeste ;
- calcule les hash ;
- refuse de continuer si une étape échoue.

Toute option Godot utilisée dans ces scripts doit être confirmée dans la documentation officielle de la version installée.

---

# 28. TESTS

## 28.1 Stratégie

Éviter de dépendre immédiatement d’un framework tiers. Créer un runner Godot headless interne simple.

Le runner doit :

- charger les tests ;
- exécuter les assertions ;
- afficher un résumé ;
- retourner un code d’échec ;
- fonctionner en CI locale.

## 28.2 Tests unitaires

Minimum :

- progression de puissance ;
- calcul de dégâts ;
- bouclier ;
- invulnérabilité ;
- drops garantis ;
- difficulté ;
- score ;
- transitions de state machine ;
- calcul de collision projectile ;
- pool d’objets ;
- sauvegarde des réglages.

## 28.3 Tests d’intégration

Minimum :

- lancement niveau ;
- spawn vague ;
- mort ennemi ;
- collecte bonus ;
- checkpoint ;
- appontage ;
- transition forteresse ;
- passage phase boss ;
- victoire ;
- export sans erreur.

## 28.4 Test de stabilité

Créer un mode soak test :

- IA du joueur ou invulnérabilité ;
- niveau bouclé ;
- durée 30 minutes ;
- collecte des FPS ;
- collecte mémoire ;
- nombre d’objets ;
- détection de croissance mémoire ;
- logs.

## 28.5 Tests visuels

Captures automatiques ou semi-automatiques pour :

- HUD 1080p ;
- HUD 1440p ;
- HUD 4K ;
- Story ;
- Vanguard ;
- mode contraste ;
- docking ;
- boss ;
- explosion lourde ;
- Overdrive.

## 28.6 Quality Gate

Une branche n’est livrable que si :

- le projet s’importe ;
- aucun parse error ;
- tests verts ;
- lancement manuel réussi ;
- export Windows réussi ;
- aucun asset sans provenance ;
- FPS mesurés ;
- pas de warning critique ;
- documentation mise à jour.

---

# 29. TÉLÉMÉTRIE LOCALE ET DEBUG

## 29.1 Aucun service externe

Le prototype n’envoie aucune donnée sur Internet.

## 29.2 Données locales

Possibilité d’enregistrer localement :

- FPS ;
- frametime ;
- nombre de projectiles ;
- nombre d’ennemis ;
- mémoire ;
- durée du niveau ;
- morts ;
- dégâts ;
- pickups ;
- phase atteinte.

## 29.3 Overlay debug

Activation par touche ou argument :

- FPS ;
- CPU ;
- GPU si disponible ;
- bullets ;
- enemies ;
- pools ;
- state ;
- encounter ;
- player hitbox ;
- collision grid ;
- checkpoint ;
- difficulté dynamique.

Overlay absent en release par défaut.

---

# 30. CLAUDE CODE — ORGANISATION DU TRAVAIL

## 30.1 CLAUDE.md

Créer un `CLAUDE.md` concis contenant :

- moteur et version ;
- commandes ;
- structure ;
- règles de code ;
- interdictions ;
- critères de fin ;
- liens vers ce cahier des charges ;
- conventions Godot ;
- règles d’asset ;
- workflow Git.

Le document ne doit pas recopier intégralement ce cahier des charges. Il doit pointer vers lui.

## 30.2 Sous-agents

### gameplay-architect

Mission :

- gameplay ;
- état ;
- équilibre ;
- architecture fonctionnelle.

Ne modifie pas les assets visuels lourds.

### godot-reviewer

Mission :

- vérifier les API ;
- détecter les mauvaises pratiques Godot ;
- relire les scènes et scripts ;
- vérifier les signaux et ressources.

### performance-auditor

Mission :

- analyser frametime ;
- allocations ;
- pools ;
- bullets ;
- rendu ;
- proposer des optimisations mesurées.

### asset-integrator

Mission :

- import ;
- noms ;
- échelle ;
- matériaux ;
- provenance ;
- LOD ;
- collisions.

### qa-agent

Mission :

- tests ;
- critères d’acceptation ;
- reproduction de bugs ;
- non-régression ;
- build.

## 30.3 Hooks

Configurer avec prudence :

- après édition GDScript : lancer un contrôle léger ;
- avant commande destructive : bloquer ;
- après modification d’asset : valider la provenance ;
- avant arrêt d’une tâche : vérifier le Quality Gate associé.

Les hooks doivent être rapides. Les tests longs sont lancés explicitement.

## 30.4 MCP

MCP est optionnel.

Autorisé pour :

- GitHub ;
- gestion de tâches ;
- documentation interne ;
- suivi des décisions.

Ne pas ajouter un MCP uniquement pour contourner une commande locale simple.

## 30.5 Context management

- utiliser un sous-agent pour les recherches volumineuses ;
- faire un résumé des décisions dans `docs/decisions/`;
- ne pas laisser une décision importante uniquement dans la conversation ;
- utiliser `/clear` entre tâches non liées ;
- lancer `/plan` avant les changements multi-fichiers ;
- faire relire les changements critiques par un sous-agent différent.

## 30.6 Discipline de commit

Commits :

- petits ;
- cohérents ;
- testés ;
- message impératif ;
- un objectif principal.

Exemples :

```text
feat: add pooled projectile manager
feat: implement fighter power progression
fix: preserve checkpoint state after docking
perf: batch enemy projectile rendering
test: cover boss phase transitions
docs: record Direct3D 12 renderer decision
```

---

# 31. CONVENTIONS DE CODE

## 31.1 GDScript

- typage obligatoire pour les APIs publiques et les variables importantes ;
- `class_name` uniquement pour les types réellement partagés ;
- une responsabilité principale par script ;
- fonctions courtes ;
- noms explicites ;
- pas d’abréviations opaques ;
- commentaires sur le pourquoi ;
- signaux nommés au passé ou comme événements explicites ;
- constantes en `UPPER_SNAKE_CASE` ;
- fichiers en `snake_case.gd` ;
- classes en `PascalCase`.

## 31.2 Gestion d’erreur

- `assert` pour invariants de développement ;
- erreurs explicites pour données invalides ;
- fallback sûr en release ;
- jamais de catch silencieux ;
- logs avec catégorie.

## 31.3 Dépendances

- injecter les références importantes ;
- éviter `get_node("/root/...")` partout ;
- autoloads limités ;
- ressources préchargées lorsque pertinent ;
- pas de chemin fragile répété.

## 31.4 Documentation

Chaque système majeur possède :

- but ;
- responsabilités ;
- dépendances ;
- diagramme simple ;
- données ;
- tests ;
- limites ;
- points d’extension.

---

# 32. ROADMAP

## Phase 0 — Bootstrap

Livrables :

- dépôt ;
- Godot 4.6 ;
- projet vide ;
- scripts PowerShell ;
- export Windows minimal ;
- CLAUDE.md ;
- structure de dossiers ;
- test runner ;
- scène boot.

Critère : un `.exe` affiche un écran de test.

## Phase 1 — Graybox jouable

Livrables :

- chasseur simple ;
- mouvement ;
- tir ;
- ennemis ;
- projectiles ;
- collision ;
- score ;
- caméra ;
- un segment de 60 secondes.

Critère : boucle de jeu agréable avec primitives.

## Phase 2 — Vertical slice

Livrables :

- trois minutes ;
- assets intermédiaires ;
- bonus ;
- niveau de puissance ;
- mini-boss ;
- HUD ;
- musique ;
- VFX ;
- profilage.

Critère : qualité suffisante pour valider le moteur et la direction artistique.

## Phase 3 — Niveau complet

Livrables :

- tous les segments ;
- appontage ;
- forteresse ;
- boss ;
- checkpoints ;
- difficulté ;
- victoire.

Critère : partie complète du début à la fin.

## Phase 4 — Art pass

Livrables :

- modèles définitifs ;
- textures ;
- VFX ;
- arrière-plans ;
- animation ;
- UI ;
- audio.

Critère : cohérence artistique.

## Phase 5 — Polish

Livrables :

- feedback ;
- haptique ;
- caméra ;
- accessibilité ;
- tutoriel ;
- scoring ;
- équilibrage.

Critère : démonstration agréable dès la première partie.

## Phase 6 — Optimisation et release

Livrables :

- presets ;
- profiling ;
- correction des spikes ;
- build final ;
- licences ;
- README ;
- captures ;
- package.

Critère : export Windows stable et reproductible.

---

# 33. BACKLOG PRIORISÉ

## P0 — Obligatoire

- bootstrap Godot ;
- build Windows ;
- player movement ;
- tir ;
- Bullet Manager ;
- collisions ;
- enemies ;
- pickups ;
- power progression ;
- HUD ;
- Encounter Director ;
- checkpoints ;
- docking ;
- fortress mode ;
- boss ;
- pause ;
- options ;
- tests ;
- provenance assets ;
- profilage ;
- build release.

## P1 — Très important

- Overdrive ;
- missiles ;
- drones orbitaux ;
- musique adaptative ;
- voix radio ;
- graphismes presets ;
- VRS ;
- FSR2 ;
- contraste ;
- vibration ;
- scoring avancé ;
- replay rapide.

## P2 — Optionnel

- photo mode ;
- classement local ;
- mode boss rush ;
- seconde configuration de chasseur ;
- crédits interactifs ;
- écran attract mode.

Aucun P2 ne doit commencer avant validation de tous les P0.

---

# 34. CRITÈRES D’ACCEPTATION GLOBAUX

Le projet est terminé lorsque :

1. Le jeu se lance depuis un `.exe` Windows propre.
2. Une partie complète est jouable.
3. Le joueur commence en chasseur.
4. Le joueur collecte des bonus.
5. La puissance de feu change visuellement et fonctionnellement.
6. Le joueur atteint la forteresse.
7. L’appontage est jouable.
8. Le joueur prend le contrôle de la forteresse.
9. Le boss final comporte au moins quatre phases.
10. Le jeu est nerveux sans être punitif.
11. Le jeu est jouable au clavier et à la manette.
12. Les options graphiques fonctionnent.
13. Les options d’accessibilité principales fonctionnent.
14. Le build cible tient 120 FPS à 1440p sur la RTX 4080 dans les scènes ordinaires et reste au-dessus de 60 FPS dans les pics, après validation réelle.
15. Le build secondaire vise 60 FPS à 1080p en Medium.
16. Aucun asset livré n’est sans provenance.
17. Aucun élément protégé de Macross n’est reproduit.
18. Les tests automatisés passent.
19. Les logs ne contiennent pas d’erreur critique.
20. Le build est reproductible par `build-release.ps1`.

---

# 35. DEFINITION OF DONE D’UNE FONCTIONNALITÉ

Une fonctionnalité est terminée si :

- le besoin est compris ;
- une tâche ou note existe ;
- le code est typé ;
- les données ne sont pas codées en dur sans justification ;
- les erreurs sont gérées ;
- les tests sont ajoutés ;
- les tests passent ;
- le projet se lance ;
- le comportement est testé au clavier ;
- le comportement est testé à la manette si pertinent ;
- les performances sont vérifiées si la fonctionnalité est critique ;
- la documentation est mise à jour ;
- les assets ont une provenance ;
- aucune régression n’est détectée ;
- le commit est propre.

---

# 36. RISQUES ET MITIGATIONS

## Risque 1 — Ambition visuelle excessive

Mitigation :

- vertical slice précoce ;
- priorité à la cohérence ;
- un seul niveau ;
- assets héros limités ;
- presets ;
- budgets.

## Risque 2 — Assets IA incohérents

Mitigation :

- bible artistique ;
- prompts versionnés ;
- retouches Blender ;
- palettes fixes ;
- validation humaine ;
- modèle de référence par faction.

## Risque 3 — Mauvaise lisibilité

Mitigation :

- couleurs normalisées ;
- contours ;
- réduction du bloom ;
- VFX séparés ;
- tests de capture ;
- mode contraste.

## Risque 4 — Performance projectiles

Mitigation :

- Bullet Manager ;
- MultiMesh ;
- pool ;
- collision custom ;
- profilage ;
- plafond.

## Risque 5 — Appontage frustrant

Mitigation :

- assistance ;
- correction invisible ;
- collisions non létales ;
- checkpoint ;
- vitesse contrôlée.

## Risque 6 — Transition chasseur/forteresse confuse

Mitigation :

- commandes similaires ;
- HUD morphing ;
- tutoriel contextuel ;
- phase d’apprentissage sans danger ;
- objectifs explicites.

## Risque 7 — Hallucination d’API par l’agent

Mitigation :

- documentation officielle obligatoire ;
- reviewer ;
- scripts de contrôle ;
- aucun code non exécuté déclaré terminé ;
- preuve de build.

## Risque 8 — Propriété intellectuelle

Mitigation :

- noms originaux ;
- silhouettes originales ;
- prompts sans licence ;
- revue IP ;
- provenance ;
- aucun asset récupéré sans droit.

## Risque 9 — Shader stutter

Mitigation :

- warm-up ;
- préchargement ;
- capture frametime ;
- limitation des variantes ;
- test sur build exporté.

---

# 37. PREMIÈRE SÉQUENCE DE TRAVAIL POUR CLAUDE CODE

Exécuter dans cet ordre :

1. Créer le dépôt et la structure.
2. Créer `CLAUDE.md`.
3. Créer `README.md`.
4. Créer `LICENSES.md`.
5. Créer le projet Godot 4.6.
6. Créer la scène Boot.
7. Créer les scripts PowerShell.
8. Vérifier l’import headless.
9. Vérifier l’export Windows.
10. Créer le test runner.
11. Créer un test minimal.
12. Créer une scène graybox.
13. Créer le plan de gameplay.
14. Créer le contrôleur du chasseur.
15. Créer un projectile unique.
16. Créer le Bullet Manager.
17. Créer une cible ennemie.
18. Créer dégâts et destruction.
19. Créer une vague.
20. Profiler.
21. Committer.
22. Seulement ensuite ajouter bonus et progression.

Ne pas commencer les assets définitifs avant la validation de la vertical slice.

---

# 38. PROMPT INITIAL RECOMMANDÉ POUR CLAUDE CODE

```text
Tu travailles sur PROJECT AEGIS ASCENDANT.

Lis intégralement :
- docs/SPEC_AEGIS_ASCENDANT.md
- CLAUDE.md
- README.md

Tu dois respecter strictement le cahier des charges.

Avant de coder :
1. inspecte le dépôt ;
2. vérifie la version de Godot réellement installée ;
3. vérifie les commandes disponibles ;
4. produis un plan de la phase 0 ;
5. identifie les risques ;
6. ne suppose aucune API ;
7. consulte la documentation officielle Godot 4.6 pour toute option incertaine.

Implémente uniquement la phase 0 :
- structure ;
- projet Godot ;
- scène Boot ;
- scripts Windows ;
- test runner minimal ;
- export Windows de test.

Critères :
- pas d’asset externe ;
- code typé ;
- scripts PowerShell robustes ;
- erreurs explicites ;
- import headless valide ;
- tests valides ;
- export `.exe` valide ;
- documentation mise à jour.

À la fin :
- exécute tous les contrôles ;
- donne les commandes exécutées ;
- liste les fichiers créés ;
- liste les limites restantes ;
- ne déclare pas le travail terminé si l’export n’a pas été vérifié.
```

---

# 39. RÉFÉRENCES TECHNIQUES À CONSULTER

L’agent doit privilégier les documents officiels correspondant à la version installée.

## Godot

- Documentation Godot 4.6  
  https://docs.godotengine.org/en/4.6/

- System requirements  
  https://docs.godotengine.org/en/4.6/about/system_requirements.html

- Renderers  
  https://docs.godotengine.org/en/4.6/tutorials/rendering/renderers.html

- GPU particles  
  https://docs.godotengine.org/en/4.6/tutorials/3d/particles/creating_a_3d_particle_system.html

- Import de scènes 3D et glTF  
  https://docs.godotengine.org/en/4.6/tutorials/assets_pipeline/importing_3d_scenes/available_formats.html

- Antialiasing et FSR2  
  https://docs.godotengine.org/en/4.6/tutorials/3d/3d_antialiasing.html

- Variable Rate Shading  
  https://docs.godotengine.org/en/4.6/tutorials/3d/variable_rate_shading.html

- Optimisation GPU  
  https://docs.godotengine.org/en/4.6/tutorials/performance/gpu_optimization.html

- Optimisation 3D  
  https://docs.godotengine.org/en/4.6/tutorials/performance/optimizing_3d_performance.html

- Réduction du stutter de compilation  
  https://docs.godotengine.org/en/4.6/tutorials/performance/pipeline_compilations.html

- Command line  
  https://docs.godotengine.org/en/4.6/tutorials/editor/command_line_tutorial.html

## Claude Code

- Overview  
  https://code.claude.com/docs/en/overview

- Best practices  
  https://code.claude.com/docs/en/best-practices

- CLAUDE.md et mémoire projet  
  https://code.claude.com/docs/en/memory

- Sous-agents  
  https://code.claude.com/docs/en/sub-agents

- Hooks  
  https://code.claude.com/docs/en/hooks

- MCP  
  https://code.claude.com/docs/en/mcp

- Settings  
  https://code.claude.com/docs/en/settings

---

# 40. DÉCISION FINALE

La réussite du projet ne dépend pas du nombre de fonctionnalités.

Elle dépend de cinq éléments :

1. un mouvement immédiatement agréable ;
2. une montée de puissance visible ;
3. une bataille parfaitement lisible ;
4. une transition chasseur-forteresse mémorable ;
5. un boss final spectaculaire et fluide.

Tout travail ne renforçant pas directement l’un de ces cinq éléments doit être considéré comme secondaire.
