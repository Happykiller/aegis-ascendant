---
titre: Piliers et intention — ce qui arbitre, et le pilier devenu orphelin
type: reference
statut: actif
maj: 2026-08-27
---

# Piliers et intention

Un pilier n'est pas un slogan : c'est un **arbitre**. Sa seule fonction utile est de trancher, à
la place de l'opérateur, entre deux idées également séduisantes.

## Ce que le métier dit

### Trois à cinq, pas plus

Les piliers sont « **3 à 5 éléments/émotions** que le jeu cherche à explorer et à faire ressentir ».
Au-delà, le raisonnement est explicite : on ne pourra pas « livrer tous ces éléments à un haut
niveau de qualité ». Le nombre n'est pas une convention esthétique — c'est un aveu de budget.

### Une phrase, en langage actif, sur le **ressenti**

La formulation recommandée tient en trois règles :

- « Chaque énoncé doit être court — **pas plus d'une phrase**. »
- « Utiliser un **langage actif** » (« ce jeu est… », « nous ferons… »).
- Et surtout : se concentrer sur « **ce que les joueurs vont ressentir**, plutôt que sur les choses
  qu'ils vont faire ».

D'où des piliers qui ressemblent à *« Fais-moi me sentir puissant, et fais-moi dire : c'était
énorme ! »* plutôt qu'à *« système de combat à trois armes »*.

⚠️ **C'est le critère qui sépare un pilier d'une ligne de périmètre.** Une fonctionnalité nommée
dans un pilier meurt avec la fonctionnalité ; une émotion survit à son implémentation.

### Le test du filtre

L'usage quotidien est une question posée à chaque idée : « ce changement rapproche-t-il le jeu de
ses piliers (**bien**), ne les affecte-t-il pas vraiment (**neutre**), ou joue-t-il contre eux
(**mauvais**) ? » Une idée brillante mais neutre **perd** contre une idée moyenne qui sert un pilier.

Corollaire rarement dit : les piliers servent à **couper**, pas à ajouter. « Cette
mécanique sert-elle nos piliers ? Si non, elle devrait probablement disparaître. »

## Chez nous — état au 2026-08-27

La spec §1.4 pose **cinq piliers**, nommés A à E. Audit, en regardant le code et les ADR :

| Pilier | Énoncé (spec §1.4) | État réel |
|---|---|---|
| **A** — Puissance accessible | puissant vite ; la difficulté vient de la densité et du positionnement, pas de la punition | **tenu, et au-delà** — voir ci-dessous |
| **B** — Lisibilité parfaite | joueur, bonus, projectiles, objectifs identifiables en < 200 ms | **tenu en partie** — c'est le sujet entier de [`01-lisibilite.md`](01-lisibilite.md) |
| **C** — Échelle évolutive | des chasseurs aux structures colossales | **tenu** — Needle Scout → Choir Harvester → Pale Leviathan, plus la citadelle |
| **D** — Transformation de la boucle | « le passage dans la forteresse doit **modifier réellement la façon de jouer** » | ⚠️ **sans implémentation** — voir ci-dessous |
| **E** — Originalité juridique | noms, silhouettes, couleurs, sons propres | **tenu**, avec l'exception unique et actée du Specter-9 (`ADR-0014`) |

### Le pilier A est tenu plus généreusement que la spec ne l'exige

La spec §5.3 demande que « le joueur conserve **au moins un niveau de puissance** après une
destruction ». Le code n'en retire **aucun** : `_destroy()`
(`scripts/player/player_fighter_controller.gd:263`) décrémente les vies, rien d'autre — `_power_level`
n'est touché nulle part ailleurs que par `add_power()`. S'y ajoutent 2,0 s d'invulnérabilité au
respawn, 1,2 s de pause avant, un bouclier qui se régénère et des continues illimités.

Ce n'est pas un bug : c'est le pilier A appliqué à la lettre. Mais c'est une **décision de fait,
non écrite**, et la spec dit autre chose — voir [`05-puissance-mort-recuperation.md`](05-puissance-mort-recuperation.md).

### Le pilier D n'a plus d'objet

Il décrit le transfert de commande vers la citadelle : on quitte le chasseur, on pilote la
forteresse, la boucle change de nature. **`ADR-0010` (2026-07-19) a supprimé cette phase** — un seul
vaisseau du début à la fin, parce que le changement de véhicule cassait le flow et la lisibilité
de l'arme du joueur.

Le pilier est donc resté dans la spec **huit jours de plus que son implémentation**, et personne ne
l'a rouvert depuis. C'est exactement ce qu'un pilier ne doit pas être : une phrase qui n'arbitre
plus rien.

Ce qui, dans le jeu actuel, **remplit encore la fonction** que le pilier D visait — rompre la boucle,
changer la nature de l'acte — c'est l'**entrée dans le noyau** du Pale Leviathan (`ADR-0025`) :
coquille écartée, aspiration, autopilote, caméra qui plonge, tir plein cadre, éjection. La boucle
est bien suspendue et remplacée, une trentaine de secondes, trois fois.

## L'écart, et ce qu'on en fait

**Tenu.** A, C, E. B est un chantier permanent, pas un écart.

**Assumé.** Les cinq énoncés de la spec nomment des **fonctionnalités**, pas des émotions — sauf le
A, qui est le seul écrit comme un ressenti (« le joueur doit être puissant rapidement »). C'est
contraire à la recommandation du métier, et c'est probablement pour ça que le D a pu mourir sans
qu'on s'en aperçoive : quand un pilier nomme une fonctionnalité, il disparaît avec elle.

> **À COMPLÉTER — décision de l'opérateur.** Le pilier D est orphelin. Trois issues, et cette page
> n'en choisit aucune :
>
> 1. **Le réécrire autour de ce qui l'a remplacé** — quelque chose comme « une fois par acte, le jeu
>    doit cesser d'être le même jeu » ; l'entrée dans le noyau devient alors son implémentation, et
>    le pilier redevient un arbitre pour les prochaines phases.
> 2. **Le retirer** et assumer quatre piliers — le métier dit trois à cinq, quatre est confortable.
> 3. **Lui redonner une implémentation** — mais `ADR-0010` a tranché après usage, et le rouvrir
>    demanderait un nouvel ADR contre une décision prise pour de bonnes raisons.

**Piste ouverte, non décidée.** La spec §1.2 (« promesse émotionnelle ») contient **déjà** sept
énoncés au bon format — « une prise en main immédiate », « une grande puissance sans difficulté
punitive », « un sentiment d'échelle croissant ». Les piliers §1.4 et la promesse §1.2 se
recouvrent largement sans jamais se citer. Les fusionner en **quatre phrases de ressenti** rendrait
le filtre utilisable en session. ⚠️ Cela touche la spec, qui reste source de vérité : la bible ne
la réécrit pas.

## Sources

- [Design Pillars – The Core of Your Game](https://www.gamedeveloper.com/design/design-pillars-the-core-of-your-game) — Game Developer : trois à cinq, le filtre, les exemples.
- [How pillars and triangles can focus your game design](https://www.raspberrypi.com/news/how-pillars-and-triangles-can-focus-your-game-design/) — Raspberry Pi Foundation : la phrase unique, le langage actif, le ressenti avant les actes, le test bien/neutre/mauvais.
