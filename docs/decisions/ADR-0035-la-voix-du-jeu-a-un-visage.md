# ADR-0035 — La voix du jeu a un visage, et ce visage est une illustration déformée

- **Statut** : accepté — ⚠️ **amendé par [`ADR-0036`](ADR-0036-l-ennemi-s-appelle-l-unisson.md)**
  (2026-08-28) : « Lyra est le seul personnage du canon » devient « le seul personnage
  **INCARNÉ** ». Huit personnes sont désormais nommées dans `docs/lore/PERSONNAGES.md` ; la
  décision tient sur le fond — Lyra reste la seule à avoir un visage à l'écran, et le pilote reste
  vu de l'extérieur.
- **Date** : 2026-08-28
- **Contexte** : demande de l'opérateur — « incarner nos discussions, les infos données »
- **Amende** : la charte créative, qui n'avait **aucune section personnage** ; `ADR-0028` (la
  texture est une étape), dont la voie s'étend ici aux planches de personnage

## Contexte

Le jeu parle déjà au joueur : bannières de phase (« DANS LE NOYAU », « CHAMP D'ASTÉROÏDES »), lignes
de journal, jauges. Tout cela est du **mobilier**. L'opérateur veut que ça vienne de quelqu'un :

> « L'idée d'incarner nos discussions, infos données […] un pour l'accueil qui vient nous parler,
> dire bonjour, et un in game pour nous donner des infos : "vous entrez dans le champ d'astéroïdes,
> débusquez les ennemis", "nos infos nous disent que dans le noyau il faut se concentrer sur le
> réacteur principal". »

Six concepts fournis nomment et dessinent le personnage : **Lyra Vantella**, navigatrice // IA guide
d'Helios Vanguard. Ils sont archivés dans `assets/reference/concepts/`.

## La question tranchée

La demande disait « **deux modèles 3D** qui bougent, animés ». Prise au mot, elle ouvre un pipeline
que le dépôt n'a pas :

- les quinze scripts `tools/blender/build_*.py` font du **hard-surface** — coques, anneaux, tourelles ;
- `ak.export_hull()` **refuse tout matériau hors des palettes de faction**, ce qui exclut par
  construction une peau, des cheveux, un tissu ;
- rien dans le dépôt ne sculpte, ne rétopologise, ne dépiaute, ne rigge ni ne skinne.

Et surtout : **les cinq maquettes qui ont plu montrent une illustration 2D dans un cadre.** Les
refaire en 3D, c'est s'éloigner de ce qui a été validé, pas s'en rapprocher.

L'opérateur a précisé « je veux le meilleur, peu importe le temps et l'investissement ». C'est
justement ce qui tranche : sur un personnage **cadré** comme celui-ci, le meilleur résultat n'est pas
le plus 3D. La référence du métier pour exactement ce cas — un portrait animé, framé, qui parle —
est la **déformation squelettique d'une illustration**. Un personnage 3D amateur passé sous le
retro-post (lift 1,25, scanlines) rendrait moins bien qu'une belle planche déformée.

## Décision

**1. Lyra est une illustration, déformée par un squelette 2D.** `Polygon2D` maillés + `Skeleton2D`,
nativement dans Godot — aucune dépendance externe. Elle respire, ses cheveux balancent, sa tête
tourne, elle cligne, et sa bouche suit l'amplitude de sa propre voix.

**2. Elle se livre EN CALQUES.** C'est la contrainte qui découle de la première, et elle est
bloquante : une image plate ne se déforme pas. Contrat et gabarit :
[`docs/forge/characters/`](../forge/characters/README.md). La charte créative gagne une section
« Personnages » qui fixe ce qui est immuable d'une planche à l'autre.

**3. Un seul module pour trois écrans.** `LyraPortrait` est monté par l'accueil, par le HUD et par
le briefing. Le personnage ne doit pas exister en trois copies qui dérivent — c'est la même leçon que
« la collision et l'image lisent la même donnée ».

**4. Deux régimes portés par le CADRE**, pas seulement par le visage : cyan au calme, rouge en
alerte. À la taille du portrait en jeu, une expression seule ne se lit pas
(`docs/KB/DAF/signaux.md`, loi n°2 : un signal mal lu est pire qu'un signal absent).

**5. Elle a une vraie voix**, produite par la voie de l'opérateur comme les textures, et passée en
jeu par un filtre « comms » — c'est le filtre qui la fait sortir de la radio du vaisseau plutôt que
d'un studio.

## Ce qu'on n'a PAS décidé

- **Le portrait en jeu va en bas à DROITE**, pas en bas à gauche comme sur les maquettes. Les quatre
  panneaux du HUD occupent haut-gauche, haut-droite, bas-gauche et haut-centre : le bas-droite est le
  **seul coin libre**. Relevé par l'opérateur, vérifié dans `fighter_hud.gd`.
- **« Continuer », profil pilote, XP, rang et réseaux sociaux** figurent sur la maquette de l'accueil
  et **ne sont pas repris** : ils reposent sur trois systèmes qui n'existent pas (sauvegarde,
  progression, comptes). Les afficher ferait de l'accueil une façade — et une façade promet ce
  qu'elle ne tient pas, ce que la loi des signaux interdit.
- **La 3D n'est pas fermée pour toujours.** Si Lyra doit un jour exister dans l'espace 3D de
  l'accueil — tourner autour d'elle, la voir marcher — la question se rouvre. Elle ne se pose pas
  pour un personnage qui parle depuis un cadre.

## Conséquences

- Le chantier se fait **pas à pas** : l'accueil, puis le portrait en jeu, puis le briefing/pause.
- La production des calques est **la dépendance bloquante** : tant qu'elle n'est pas livrée,
  l'intégration tourne sur une doublure, comme `CoreInterior` sait le faire pour son décor.
- Le canon gagne son **premier personnage**. Toute planche future de Lyra se juge contre
  `lyra_vantella_character_sheet.png`, jamais contre la précédente.

## Révision du 2026-08-28 — plus de squelette, une figure d'un tenant

Le point 1 (« déformée par un squelette 2D ») n'a pas survécu à la livraison. Les pièces
générées séparément n'ont ni les mêmes proportions ni la même coiffure (`docs/forge/characters/README.md`,
« dessiner la pièce d'un puzzle »), et la seule animation qui ne scintille pas sous le post-process
rétro s'est révélée être une **translation de toute la figure quantifiée au pixel** — qui n'a besoin
d'aucune découpe. Lyra est donc **une illustration d'un seul tenant**, plus ses hologrammes en
calques séparés, plus, si la retouche par masque est possible, une bouche et des paupières.
Demande : `CHR-0004`. Ce qui tient toujours : illustration plutôt que 3D, la charte §3 bis, la voix.
