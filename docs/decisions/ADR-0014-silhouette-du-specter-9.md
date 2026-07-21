# ADR-0014 — Le Specter-9 reprend le plan de sa planche de référence

- **Statut** : accepté
- **Date** : 2026-07-21
- **Amende** : ADR-0009 (« les assets produits restent originaux »), spec §0.2 via `CLAUDE.md`
- **Portée** : **le Specter-9 uniquement**. Aucune autre coque n'est concernée.

## Contexte

La reforge BRIEF-0033 a échoué à rapprocher le chasseur de
`assets/reference/inspiration/reference_specter_9_design_sheet.png`, et le motif était une **erreur
de diagnostic du concepteur**, pas d'exécution :

> « Le rapport de proportions est donc déjà juste : le problème est le profil, pas le plan. »
> — BRIEF-0033, §Contexte

Ce raisonnement s'appuyait sur le rapport de la **boîte englobante** (1,41 contre 1,36). Cette
statistique est vide : elle mesure la boîte, jamais la répartition des masses dedans. Comparaison
faite ensuite, vue de dessus contre vue de dessus :

| | Planche | Specter-9 (BRIEF-0033) |
|---|---|---|
| Masse dominante | **fuselage central + deux nacelles** | **l'aile** |
| Part visuelle de l'aile | ~30 % | ~70 % |
| Fuselage | volume porteur sur toute la longueur | bande fine posée sur le delta |
| Dérives | deux, inclinées | aucune |

Le brief demandait explicitement de **conserver le delta**. Aucun travail de profil ne pouvait donc
corriger l'écart.

## Décision

**Le Specter-9 adopte le plan de la planche, dérives inclinées comprises.** Décision du propriétaire
du projet, prise en connaissance de ce qui suit.

Ce que cela change par rapport à ADR-0009 : cet ADR autorisait les planches tierces comme **cible
d'inspiration** tout en exigeant que « *les assets produits restent originaux* ». Pour cette coque,
cette seconde clause **ne s'applique plus** : c'est l'architecture — fuselage porteur, nacelles
flanquantes, ailes en lames, doubles dérives — qui est reprise, et c'est elle qui rend l'appareil
identifiable.

La ligne de `CLAUDE.md` « aucun nom/silhouette/élément identifiable » reste vraie pour **tout le
reste du jeu**. Elle cesse de l'être pour cette unité.

## Ce qui reste hors de portée

Repris : le **plan** et les **dérives**. Ne le sont pas :

- la **livrée tricolore** en bandes rouges — la palette du kit reste seule maîtresse ;
- le **badge numéroté** et tout texte ou marquage lisible ;
- tout **nom**, logo, insigne ou désignation de la licence.

Ce n'est pas une demi-mesure de prudence : la palette et les marquages sont ce qui raccroche le
chasseur au reste de la flotte Helios. Un appareil tricolore au milieu d'une flotte ivoire et bleue
serait un corps étranger dans le jeu, indépendamment de toute question de droits.

## Conséquence à ne pas perdre de vue

**Si le projet devait un jour être distribué**, cette coque est le premier élément à refaire. ADR-0009
prévoyait déjà de purger `assets/reference/inspiration/` de l'arbre et de l'historique dans ce cas ;
il faut y ajouter **`build_specter_9.py` et le `.glb` qu'il produit**, qui ne sont plus une
transposition mais une reprise.

Le projet est aujourd'hui **personnel, non commercial, non distribué**, et le propriétaire assume ce
risque — c'est la même posture qu'ADR-0009, portée un cran plus loin.

## Conséquence de méthode

Ne plus jamais conclure sur une **répartition de formes** à partir d'un rapport de boîte englobante.
Deux silhouettes sans rapport peuvent partager la même boîte : c'est exactement ce qui s'est produit
ici, et ça a coûté une reforge complète. La vérification qui manquait tenait en une image :
**mettre la planche et le rendu côte à côte, à la même hauteur**, avant d'écrire le brief.
