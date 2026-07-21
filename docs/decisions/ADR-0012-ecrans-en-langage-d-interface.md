# ADR-0012 — Les écrans se construisent en langage d'interface, pas en cadres SVG plein écran

- **Statut** : accepté
- **Date** : 2026-07-21
- **Amende** : tâche **H4 « Écrans »** de `docs/TASKS_HORIZONTAL.md`, entrée « Écrans & HUD » du backlog
- **Contexte spec** : §19 (interfaces), DA §10 (interface et communication)

## Contexte

BRIEF-0017 a livré une famille de **cadres SVG plein écran** — un par écran (`pause_frame.svg`,
`victory_frame.svg`, `results_frame.svg`, `mission_failed_frame.svg`, `main_menu_frame.svg`). La
tâche H4 prévoyait de les copier dans `assets/imported/` et de les afficher en `TextureRect`
pleine page. C'est ce qui avait été fait pour la pause.

Le résultat, rendu et regardé (ADR-0006), ne tient pas :

| Symptôme | Cause |
|---|---|
| Une boîte bleue opaque masque tout le champ de bataille | le SVG peint un fond `#1C2B5E` à 72 % sur 840 × 848 px |
| Deux rectangles or non identifiables flottent en haut | la « marque centrale double » du cadre, illisible hors de son contexte de planche |
| Texte en police Godot par défaut, boutons gris | le cadre est une image : il n'apporte **ni thème, ni typographie, ni états de focus** |
| Aucune parenté avec l'écran d'accueil | l'accueil ne contient **aucun** cadre SVG — il est bâti en `Panel` + `Label` + `Theme` |

Le fond du problème est structurel : un cadre matriciel plein écran est **figé**. Il ne connaît ni
la résolution, ni le focus, ni les états, ni le thème. Or l'écran d'accueil — le seul écran
réellement abouti du projet — a démontré l'inverse : son identité vient d'un filet de 2 px, du
thème `aegis_theme.tres` (Press Start 2P, cyan `#29E6FF`, or `#E4B54A`, angles vifs) et d'un
**mobilier récurrent** placé aux mêmes ancres : identité en haut à gauche, oscillogramme COMMS en
bas à gauche, devise en bas à droite, rappel de touches en bas au centre.

## Décision

**Les écrans du jeu sont construits en langage d'interface (thème + Control), pas en cadres SVG
plein écran.** Le vocabulaire de référence est celui de `scenes/boot/boot.tscn`.

1. Le mobilier de l'accueil est **reconduit aux mêmes ancres** sur chaque écran. C'est la
   répétition des places, pas la répétition d'une image, qui fait qu'un jeu se lit d'une seule main.
2. Chaque écran **décline** ce mobilier plutôt que de le recopier : l'écran de pause garde le bloc
   COMMS de l'accueil mais le passe en régime *tenu* — pastille ambre, trace aplatie
   (`scripts/ui/comms_trace.gd`, deux modes, un seul appareil). L'état se raconte par
   l'instrument, pas par un deuxième libellé.
3. Un écran qui se superpose au gameplay **efface le HUD** le temps de son affichage : les coins
   que réclame le mobilier sont ceux du HUD, et deux blocs de texte superposés ne se lisent ni l'un
   ni l'autre. Le raccord passe par un **signal** émis par l'écran et câblé par le niveau — l'écran
   ne connaît pas le HUD.
4. Un écran posé au-dessus des scanlines globales (layer > 5) **rejoue la passe localement**, sinon
   il est le seul élément à échapper au grain CRT et lit comme une capture collée sur le jeu.

Les cadres SVG livrés restent en `assets/source/` : ce sont des livrables de forge valides, avec
leur provenance. Ils ne sont simplement plus **importés**. `assets/imported/ui/screens/pause_frame.svg`
est supprimé et sa ligne de provenance retirée ; la ligne source porte la mention *superseded*.

## Conséquences

- La tâche H4 change de nature : elle ne consiste plus à importer des cadres, mais à décliner le
  mobilier de l'accueil sur les écrans restants — **victoire, résultats, échec de mission**, qui
  souffrent aujourd'hui exactement du même défaut que la pause.
- `scenes/ui/victory_screen.tscn` reste sur l'ancien modèle (cadre SVG + police par défaut) et
  constitue la dette identifiée par cet ADR.
- L'emblème `helios_vanguard_emblem.svg` gagne un second point d'usage : il est le pivot visuel du
  bloc d'identité, sur l'accueil comme sur la pause.
- Le seuil de validation ne change pas : un écran n'est pas fini tant qu'il n'a pas été **rendu et
  regardé** en jeu, post-traitement rétro actif (ADR-0006).
