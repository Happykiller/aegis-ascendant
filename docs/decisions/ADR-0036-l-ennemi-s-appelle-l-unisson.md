# ADR-0036 — L'ennemi s'appelle l'Unisson, et le jeu ouvre sur une patrouille de routine

- **Statut** : accepté
- **Date** : 2026-08-28
- **Contexte** : demande de l'opérateur — « je veux du lore, la totale », puis « je n'aime pas du
  tout le nom Null Choir », puis « il va falloir qu'on puisse dérouler dix, douze niveaux »
- **Amende** : la **spec §3.3** (« Ennemi : The Null Choir »), la **charte créative §2** (table du
  canon), et **`ADR-0035`** dont la formule « seul personnage du canon » devient « seul personnage
  **incarné** »
- **Supersede** : `BRIEF-0087` et l'ancienne `docs/lore/BIBLE.md`, bible minimale qui reliait
  l'existant sans rien inventer

## Contexte

Le jeu avait un monde **par accident** : des noms de vaisseaux, des unités aux comportements
travaillés, une navigatrice avec un visage et une voix. Mais rien ne disait **pourquoi**. Le joueur
traversait six phases sans savoir ce qu'il défendait, contre qui, ni ce qui avait déclenché la
guerre. Lyra parlait beaucoup et ne racontait rien.

Trois demandes successives de l'opérateur ont cadré le chantier, et chacune a changé l'échelle de
la précédente :

1. **« La totale »** — planète d'origine, factions, origine de l'invasion, personnages, histoire de
   chaque vaisseau ennemi, et un lore *exploitable* écran par écran ;
2. **« Je n'aime pas du tout le nom Null Choir »** — le nom de la faction, jusque-là intangible,
   redevient ouvert ;
3. **« Dix, douze niveaux »** — le lore ne couvre plus un niveau mais une **campagne**.

## Les décisions

### 1. L'ennemi s'appelle **The Unison** / l'Unisson

« Null Choir » avait été posé **avant qu'il y ait un lore à nommer** : une étiquette de genre, pas
une conclusion. Deux défauts sont apparus une fois l'origine écrite. « Choir » tire vers le
**religieux** — un chœur loue — alors que cet ennemi n'a ni foi, ni culte, ni sacrifice : le mot
promettait l'envahisseur mystique venu du dehors, c'est-à-dire exactement le cliché que le brief
interdisait. Et « Null » ne disait rien de lui, seulement de nos instruments.

**Unison** vient d'un relevé : des sources innombrables tenant exactement la même note, sans
décalage ni hiérarchie. Il gagne sur le critère qui compte pour une campagne — **il retourne au
niveau 12** : mot d'analyste presque neutre à l'ouverture, il devient une menace rétroactive quand
on comprend que « prendre à l'unisson » veut dire *faire tenir la même note pour toujours*. Il garde
le fil musical du canon en coupant le fil religieux.

Deux unités suivent, parce qu'elles portaient le morphème de faction : **Choir Mine → Anchor
Mine**, **Choir Harvester → Graft Harvester**. **Null Maw ne bouge pas**, et en sort renforcé :
« Null » n'était pas un morceau du nom de la faction, c'est un mot du **journal d'avaries** — un
relevé qui ne rend rien s'écrit *nul*. Or le Null Maw est précisément l'unité qui saisit un chasseur
et n'en tire rien.

⚠️ **Les identifiants techniques ne changent pas.** `choir_mine.tres`, `choir_harvester.tscn`,
`null_maw.glb`, les clés de dialogue, les `voice_cue`, les préfixes de pièces : le joueur ne les
voit jamais, et les renommer coûterait des `.uid`, des imports et des tests pour zéro gain. La
distinction **nom affiché ≠ identifiant** est la règle, pas une négligence.

### 2. Le jeu ouvre sur une patrouille de routine

L'écran-titre annonçait « Le Null Choir avance sur les colonies. La Vanguard tient la ligne — et
vous en êtes » : la guerre y était connue, nommée, déclarée, et le joueur enrôlé avant d'avoir
décollé. Le niveau 1 devient l'**ouverture** d'une campagne de douze : une vérification de
calibrage sur un relais dont l'horloge avance de 40 ms.

⚠️ **Ce n'est pas un premier contact absolu**, et c'est délibéré : « la Vanguard tient la ligne »
est **déjà enregistré en voix** et suppose une menace connue. L'arbitrage retenu — l'ennemi est
connu depuis quarante-cinq ans comme un phénomène de frontière lointaine — coûte **une seule
re-synthèse** au lieu de plusieurs, et déplace la découverte du niveau 1 de « des aliens existent »
vers **« ils sont derrière nous »**. Une seule mauvaise nouvelle, ce qui préserve les onze niveaux
suivants.

### 3. Le casting s'élargit, l'écran non

`ADR-0035` posait que Lyra est « le seul personnage du canon ». Huit personnes sont désormais
nommées (`docs/lore/PERSONNAGES.md`). La décision tient sur le fond et change de mot : Lyra reste
le seul personnage **incarné**, le seul à avoir un visage à l'écran. Aucun des sept autres n'a de
portrait, et le pilote reste vu de l'extérieur.

De même, l'ancienne bible posait que l'ennemi « n'a pas de chef et pas de visage ». L'opérateur a
levé la contrainte ; **son intention est tenue quand même** : les Voix de l'Unisson *pèsent*, elles
n'ordonnent pas. Il n'y a ni général, ni porte-parole, et l'ennemi ne parle jamais.

### 4. La défaite cesse d'être muette

C'était le seul dénouement du jeu sans un mot : on perdait, un écran rouge se levait, et la
navigatrice qui venait de parler pendant toute la mission se taisait. Elle **rapporte** désormais
(`mission_failed`, `VOX-0004`) — froidement, parce que c'est sa fonction et qu'il n'y a plus
personne pour l'entendre.

Et le rapport porte une ligne de relevé qui n'explique rien et dit tout : l'anomalie qui a motivé la
sortie valait **+40 ms**. Gagnée, elle est *remise à l'heure*. Perdue, elle affiche **0 ms** — elle
ne dérive plus, parce qu'elle s'est mise à l'heure de quelque chose d'autre.

## Ce que ça coûte, mesuré

| Poste | Volume | Coût réel |
|---|---|---|
| Nom affiché de la faction | 89 occurrences, dont 71 en documentation | Édition de texte |
| **Voix enregistrée** | **1 seule** la prononçait (`lyra_title_3`) | **1 re-synthèse**, et elle était déjà à refaire pour le cadrage |
| Identifiants techniques | fichiers, scènes, modèles, clés | **Zéro** — ils ne changent pas |

⚠️ **Deux occurrences avaient échappé à l'inventaire** : `leech_drone.tres` et
`shield_carrier.tres` disaient « Choeur Nul », la traduction française. Un renommage se vérifie par
`grep` sur les deux langues, pas sur le nom anglais seul.

## Conséquences

- `docs/lore/` porte sept pages (1 649 lignes) dont **`EXPLOITATION.md`**, la page d'usage : écran
  par écran, ce que le lore y met et **ce qu'on n'a pas le droit d'y dire encore**. C'est elle qu'on
  relit avant d'écrire une réplique, pas la bible.
- Chaque écran a désormais un **plafond de révélation** écrit dans son propre fichier. Le niveau 1
  est une ouverture : ce qui est dit trop tôt ne pourra plus l'être au niveau 8.
- Deux gardes neufs tiennent une erreur que rien ne signalait : une réplique ne peut plus quitter
  l'écran pendant qu'on l'entend encore, ni sur le HUD (`hold + fondu`) ni dans la bulle de
  l'accueil (`frappe + hold`, arithmétique différente).

## Ce qui reste ouvert

- **La fin de la campagne** — trois issues écrites, aucune tranchée (`docs/lore/CAMPAGNE.md` §5).
- **Frigate Turret et Null Bomber** — au canon de la spec §11, sans Resource ni coque. Leur
  histoire est écrite ; leur existence en jeu ne l'est pas. À produire ou à retirer du canon.
- **`Camp.NULL_CHOIR`** — l'identifiant d'énumération garde son nom, par application de la règle
  ci-dessus. Il est le seul endroit du **code** où le nom rejeté survit ; le renommer est sans
  risque (les `.tres` sérialisent l'entier) mais sans gain visible.
