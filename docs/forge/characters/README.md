# Personnages — le contrat d'expression de besoin

Ce dossier tient les **demandes de planche de personnage**, une par fichier, au format JSON
normalisé. Même étagement que [`../textures/`](../textures/README.md), et pour la même raison :
séparer les **contraintes techniques** de la **description visuelle**, sinon on écrit des prompts
qui se contredisent.

> **Institué par [`ADR-0035`](../../decisions/ADR-0035-la-voix-du-jeu-a-un-visage.md).** Le dépôt
> n'avait jamais produit d'humain : ni section de charte, ni gabarit, ni contrat de livraison. Une
> planche livrée sans référentiel dérive d'une image à l'autre — le défaut que la charte interdit
> déjà pour les silhouettes de vaisseaux.

## ⛔ La règle qui commande tout : UNE FIGURE D'UN TENANT, et seules les pièces qui bougent SEULES sont à part

> **Révisée le 2026-08-28, après trois mises en jeu.** La version d'origine disait « en calques,
> jamais aplati », pour un squelette 2D qui déformerait chaque pièce. Mesuré : un générateur
> d'images réussit une **figure entière** et échoue sur des **morceaux** — les bras de CHR-0001
> ont une manche 2,3× trop large pour l'épaule tout en étant trop courts (aucune échelle ne
> satisfait les deux), `tete` porte déjà sa frange que `meches_avant` repeint par-dessus (le
> « faux raccord » vu en jeu), et les trois calques de cheveux ne racontent pas la même coiffure.
> Pendant ce temps la planche d'identité, plate, est parfaitement cohérente.

Et le jeu n'a plus besoin de morceaux : la respiration et le balancement sont une **translation
de toute la figure**, quantifiée au pixel (`lyra_portrait.gd`) — la seule animation qui ne
scintille pas sous le post-process rétro. Ne se demandent à part que les pièces qui bougent
**indépendamment** de la figure : les hologrammes (dérive, rotation), et — si l'outil sait
retoucher par masque, jamais par régénération — la bouche et les paupières.

Les six concepts d'origine restent plats et font foi sur **l'apparence** ; c'est désormais aussi
la forme de la livraison, sans les hologrammes ni le mobilier d'interface.

## Les cinq règles de validation

| # | Règle | Pourquoi |
|---|---|---|
| 1 | **Un fichier PNG par calque**, et les pièces d'un même GROUPE co-enregistrées (voir ci-dessous) | Les pièces d'un groupe s'empilent sans recalage. Entre groupes, c'est le jeu qui place — parce qu'un générateur d'images ne sait pas faire autrement |
| 2 | **Aucun fond, aucun décor, aucun élément d'interface** | Les maquettes portent nébuleuse, cadres et jauges. Le runtime n'en veut RIEN : le fond est la scène 3D du jeu, le cadre est dessiné par le HUD |
| 3 | `transparent_background` se demande par **découpe sur fond uni**, jamais par « fond transparent » | Même piège que les textures (règle 3 du contrat texture) : on reçoit un **damier peint** dans une image opaque. Fond `pure_black` ou `pure_magenta`, puis `tools/bg-key-alpha.py` |
| 4 | Les pièces **se recouvrent** aux articulations | Une découpe au ras de l'épaule fait apparaître un trou dès que le bras bouge de trois degrés. On demande 20 à 40 px de chevauchement sous la pièce voisine |
| 5 | La **palette de faction** fait foi, et le cyan `#3FD9E8` reste réservé à l'holo | Lyra porte la livrée Helios (charte §3 bis). Le cyan sur elle ne doit apparaître que sur ses **hologrammes** et ses liserés — jamais en aplat, sinon il vole sa lisibilité au tir allié |

## ⛔ Ce qu'un générateur d'images NE PEUT PAS faire : dessiner la pièce d'un puzzle

**Livraison CHR-0001 du 2026-08-28, mesurée.** Dix calques, tous en 1024×1536 comme exigé — et
inassemblables : une tête aux deux tiers de la hauteur du corps (`tete` 907 px pour `buste`
1460), des bras à leur propre échelle. Chaque pièce est dessinée **pour remplir sa toile** ; le
générateur ne sait pas qu'il dessine un morceau. Un contrôle de dimensions la faisait passer pour
conforme : un test qui mesure la toile ne mesure pas le cadrage.

Un placement en jeu (`CharacterRig`) a ensuite absorbé les échelles — pas les proportions ni les
raccords, qui ne se règlent pas. D'où la révision ci-dessus : **on ne découpe plus la figure.**

Le découpage qui reste :

```
figure               Lyra entière, sans hologrammes — respire et balance d'un bloc
holo_bracelet        poignet gauche, dérive lente et boucle
holo_sphere          main droite, rotation continue
figure_bouche_ouverte, figure_yeux_fermes   OPTIONNELLES : `figure` retouchée par masque
```

⚠️ **Une variante est une substitution, pas un nouveau dessin.** Trois livraisons d'expressions
(CHR-0002, CHR-0003) ont été régénérées au lieu d'être retouchées — 38 %, puis 23 % de pixels
changés au lieu des 3 % d'une bouche — et n'ont jamais servi. `tools/characters/check_delivery.py`
refuse au-delà de 12 %. Si l'outil ne sait pas retoucher, livrer `figure` seule.

## Où ça se dépose

| Quoi | Où | Chargé par le moteur |
|---|---|---|
| Les maquettes de référence | `assets/reference/concepts/` | non (`.gdignore`) |
| Les calques du runtime | `assets/imported/ui/characters/<nom>/` | **oui** |

Chaque calque livré prend sa ligne dans `assets/licenses/ASSET_PROVENANCE.csv`.

## Nommage

`CHR-NNNN-<personnage>-<cadrage>.json` — le cadrage est `pied` (pied-en-cap) ou `buste`.

## Les demandes

| Fichier | Sujet | Statut |
|---|---|---|
| [`CHR-0004-lyra-figure.json`](CHR-0004-lyra-figure.json) | Lyra pied-en-cap **d'un seul tenant**, sans hologrammes | **à commander — remplace CHR-0001 et CHR-0003** |
| [`CHR-0001-lyra-pied.json`](CHR-0001-lyra-pied.json) | Lyra pied-en-cap en dix calques | livrée le 28/08 — **remplacée** : morceaux inassemblables (voir plus haut). Seuls `holo_sphere` et `holo_bracelet` sont conservés |
| [`CHR-0002-lyra-buste.json`](CHR-0002-lyra-buste.json) | Lyra en buste, pour le HUD et le briefing | livrée le 28/08 — **base utilisable, expressions REFUSÉES** (régénérées au lieu d'être retouchées). En attente : le HUD tourne sur le recadrage de CHR-0001 |
| [`CHR-0003-lyra-expressions.json`](CHR-0003-lyra-expressions.json) | Les **trois** calques d'expression qui manquent (`tete_bouche_mi`, `tete_yeux_mi`, `tete_yeux_fermes`) — par RETOUCHE de `tete.png` | **remplacée par les variantes optionnelles de CHR-0004** |
