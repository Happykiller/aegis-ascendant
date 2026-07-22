---
name: jouer
description: Lance Aegis Ascendant sur Windows pour un test à la main, en garantissant qu'on joue le code courant et non le build précédent. Sait ouvrir directement une scène, tourne en arrière-plan pour ne pas bloquer la session, et rend la chronologie de la partie à partir du journal. Déclencher avec /jouer.
trigger: /jouer
---

# /jouer — mettre le jeu entre les mains de l'opérateur

Ce skill sert **le test réel** : l'opérateur veut jouer, regarder, sentir. Il ne sert ni à
mesurer une perf (→ `godot-verifier`), ni à juger un rendu tout seul (→
[howto-verifier-un-rendu](../../resources/howto-verifier-un-rendu.md)), ni à relever une
chronologie d'équilibrage (→ sous-agent `balance-prober`).

## La commande

```bash
./scripts/play.sh [--release|--rebuild] [-- <drapeaux de jeu>]
```

Tout ce qui suit est **déjà dans le script**. Ne le refais pas à la main : c'est exactement ce
que `/capitalize` interdit — une procédure déterministe s'encode, elle ne se raconte pas.

| Ce qu'il fait | Ce que ça évite |
|---|---|
| Compare les sources au `.pck` et **n'exporte que si nécessaire** | `deploy-win.sh` **n'exporte pas**. Modifier un script puis le lancer fait jouer le build **précédent**, sans un mot — et l'on conclut sur du code qui n'est pas le sien |
| Pose le séparateur **`++`** tout seul | sans lui, les drapeaux de jeu sont avalés par Godot et **silencieusement ignorés** : la scène demandée ne s'ouvre pas, et rien ne le signale |
| Filtre la péremption **par extension** | éditer un `.sh` ou un `.md` ne déclenche pas un export complet — un faux positif de plus et l'on prend l'habitude de forcer, ce qui rouvre le trou |
| Nomme le fichier qui a périmé le build | « ton build est périmé » sans dire par quoi se lit comme un faux positif |
| **Étouffe la porte de qualité** dans `build/play-export.log`, résumé en 3 lignes | ses ~180 lignes contiennent des `[GameState] BOOT -> CODEX` émis par les **tests** : mêlées au journal, elles se lisent comme le parcours du joueur, et l'on rendrait une chronologie qu'il n'a **pas jouée**. En cas d'échec, le journal complet est rendu |

## Protocole

### 1. Lancer EN ARRIÈRE-PLAN — jamais au premier plan

`play.sh` ne rend la main **qu'à la fermeture du jeu**. Au premier plan, l'appel serait tué par
le délai d'expiration de l'outil au bout de deux minutes : la fenêtre se fermerait au nez de
l'opérateur, en pleine partie.

Lancer avec `run_in_background`, puis lire le fichier de sortie après quelques secondes pour
confirmer que le jeu est bien monté (`[TitleMenu] ready`, `[Level] ready`, ou l'écran visé).

### 2. Dire ce qui a été lancé, et sur quel build

Deux faits utiles à l'opérateur, tirés de la sortie :

- **le build est-il neuf ?** — `[play] build à jour` ou `[play] build périmé (… ) : export debug` ;
- **quelle machine** — la ligne Vulkan donne le GPU. ⚠️ Sur ce poste c'est une **Quadro T1000**,
  pas la RTX 4080 : à build identique le temps GPU par image est **×14**. Ne jamais lire 12 ms
  comme une régression.

### 3. Pendant la partie, ne rien affirmer

Le jeu tourne, on ne voit rien. Ne pas prédire ce que l'opérateur observe, ne pas déduire de
l'absence de nouvelles que « tout va bien ». Rappeler les touches si l'écran visé est récent.

### 4. À la fermeture, rendre la CHRONOLOGIE, pas le journal

La notification de fin arrive toute seule. Lire la sortie et en tirer un récit court :
transitions d'état, phases traversées, cues audio, erreurs. C'est ce que l'opérateur ne peut pas
lire lui-même — il jouait.

Ce qu'un journal propre raconte :

| Ligne | Ce qu'elle dit |
|---|---|
| `[GameState] X -> Y` | le chemin réellement parcouru dans l'arc |
| `[SceneRouter] -> …` | les scènes montées |
| `[WaveSpawner] pool ready: N` | le pooling a eu lieu **une fois** — une seconde occurrence en cours de vague serait une réallocation |
| `[Audio] music A -> B` | les fondus ; **pas** de nouvelle ligne au changement de scène = la musique a bien traversé sans trou |
| `game exited with code 0` | sortie propre |

Signaler ce qui **manque** autant que ce qui est là : pas de `SCRIPT ERROR`, pas d'assert.

## Drapeaux de jeu

Ils vont **après `--`**. Le `++` est ajouté par le script.

| Drapeau | Effet |
|---|---|
| `--goto-graybox` | saute l'accueil, droit au combat |
| `--goto-codex` | ouvre le bestiaire |
| `--codex-entry=N` | ouvre une fiche précise du bestiaire (0 = Specter-9) |
| `--pause-demo` | ouvre le menu de pause à l'entrée du niveau |
| `--victory-demo` | saute au rapport de mission, score semé |
| `--demo` | pilote automatique + tir continu |
| `--novsync` | débride la présentation |
| `--no-backdrop` / `--no-glow` | bissection de perf (voir `godot-verifier`) |

⚠️ **Ne pas passer `--demo` pour un test à la main** : le pilote automatique prend les commandes
et la démo **boucle sans fin**. C'est l'outil de `balance-prober`, pas celui d'un joueur.

## Ce qu'il ne faut PAS conclure

- **Le FPS d'un lancement automatisé ne mesure rien** — Windows bride la présentation. Le chiffre
  qui vaut est le **temps GPU par image**, et toujours avec sa machine
  ([howto-mesurer-la-perf](../../resources/howto-mesurer-la-perf.md)).
- **Une partie sans erreur ne valide pas un rendu.** Si l'enjeu est visuel, il faut une capture
  regardée (ADR-0006), pas un journal vert.
- **Une session courte ne dit pas qu'un écran déplaît.** Demander, ne pas interpréter.

## Cas particuliers

- **`--release`** quand la question est « à quoi ça ressemble vraiment » : le build debug embarque
  le wrapper console et ses vérifications.
- **`--rebuild`** après un changement que le filtre d'extensions ne voit pas : un réglage d'import,
  un `export_presets.cfg` retouché à la main, un doute.
- **L'exe reste verrouillé** si une partie précédente n'est pas morte. `deploy-win.sh` attend la
  libération du handle et le dit ; s'il échoue après 10 s, un processus est bloqué et il faut le
  tuer à la main.
