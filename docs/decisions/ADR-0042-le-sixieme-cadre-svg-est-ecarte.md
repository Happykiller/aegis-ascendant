# ADR-0042 — Le sixième cadre SVG est écarté, comme les cinq autres

- **Statut** : accepté
- **Date** : 2026-09-03
- **Étend** : `ADR-0012` (« Les écrans se construisent en langage d'interface, pas en cadres SVG
  plein écran ») au seul fichier de la famille qu'il n'avait pas nommé.
- **Contexte spec** : §19 (interfaces), DA §10 (interface et communication)

## Contexte

`BRIEF-0017` a livré **six** SVG plein écran dans `assets/source/ui/screens/`. `ADR-0012` en a
écarté **cinq**, qu'il nomme un par un : `pause_frame.svg`, `victory_frame.svg`,
`results_frame.svg`, `mission_failed_frame.svg`, `main_menu_frame.svg`.

**`title_backdrop.svg` n'y figure pas.** Ce n'est pas une exception motivée : c'est le seul du lot
dont le nom ne finit pas par `_frame`, et il est passé entre les mailles d'une énumération. Depuis,
le backlog le porte comme un reste à faire (« le `title_backdrop.svg` et les emblèmes de faction ne
sont pas utilisés ») — une ligne à moitié fausse, puisque les emblèmes, eux, servent **trois**
écrans. L'audit du 2026-09-03 a séparé les deux moitiés ; celle-ci demande une décision.

## Ce que le fichier contient, et pourquoi ça tranche

Il fait 626 octets et tient en sept `path` sur un `viewBox` de 1920 × 1080 :

| Élément | Ce que c'est |
|---|---|
| `M0 0h1920v1080H0Z` en `#070A12` | un **fond opaque plein écran** |
| losange `#1C2B5E`, `opacity=".72"` | exactement la **« boîte bleue opaque »** du tableau des symptômes d'`ADR-0012` |
| losange interne `#070A12`, filet or `#E4B54A` | un cadre figé, sans état ni focus |
| croix cyan, équerres, filet bas | du mobilier peint, aux coordonnées d'un écran de 1920 × 1080 |

C'est le même objet que ses cinq frères, avec les mêmes défauts, et `ADR-0012` les a déjà énoncés :
un cadre matriciel plein écran **ne connaît ni la résolution, ni le focus, ni les états, ni le
thème**.

⚠️ **Et il entrerait en concurrence avec ce qui existe.** L'accueil ne manque pas d'un fond : il
porte un `SpaceBackdrop` — du décor **animé**, en 3D, partagé avec le jeu. Poser par-dessus un
aplat `#070A12` à pleine page ne l'habillerait pas, il l'**effacerait**. `ADR-0012` l'écrit déjà
pour les autres écrans : « le fond derrière un écran est du décor animé ou un champ de bataille
figé — on ne sait pas ce qu'il y aura à cet endroit ».

## Décision

**`title_backdrop.svg` est écarté**, au même titre et pour les mêmes raisons que les cinq cadres
d'`ADR-0012`. Il reste en `assets/source/` — c'est un livrable de forge valide, avec sa provenance —
et n'est **jamais importé**. L'identité de l'accueil vient du thème `aegis_theme.tres`, de son
mobilier ancré et du `SpaceBackdrop`, pas d'une image.

**La ligne du backlog est close par cette décision** : il n'y a plus d'asset qui dort, il y a un
asset écarté, et c'est écrit.

## Un défaut d'application corrigé au passage

`ADR-0012` annonçait que « la ligne source porte la mention *superseded* » dans
`ASSET_PROVENANCE.csv`. **Elle n'y a jamais été portée** : les six lignes `screen_*` y sont
identiques à leur premier jour, et rien n'y distingue un livrable en service d'un livrable écarté.
Un registre de provenance qui ne dit pas ce qui est en service ne sert qu'à moitié — c'est le même
défaut que le backlog vient de payer six semaines durant.

Les **six** lignes portent donc désormais leur état, y compris les cinq que la décision d'origine
visait.

## Ce que cette décision ne fait pas

- Elle **ne touche pas aux emblèmes** : `helios_vanguard_emblem.svg` est importé et sert `boot.tscn`,
  `mission_report.tscn` et `pause_screen.tscn`. Il n'a jamais été concerné.
- Elle **ne supprime rien** de `assets/source/`. Un livrable de forge écarté reste consultable :
  c'est ce qui permet de vérifier, deux ans plus tard, qu'il a été jugé et non oublié.
- Elle **ne rouvre pas** `ADR-0012`, dont la doctrine est confirmée telle quelle.
