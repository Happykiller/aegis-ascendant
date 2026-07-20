# Bonne pratique — un seul écrivain dans le dépôt

## La règle

Deux agents qui écrivent en parallèle dans le même arbre produisent des **commits mélangés** et une
**porte de qualité rouge sans coupable identifiable**. Avant d'ouvrir une seconde session
d'écriture sur `macross`, s'assurer que la première est terminée — ou lui donner un **worktree
séparé** (`isolation: "worktree"`).

## Cas vécu (12/07/2026)

Le dépôt était **propre au démarrage** de la session. Pendant que je travaillais sur les impacts, un
sous-système audio complet est apparu dans l'arbre (banque de cues typée, throttle, bus, 11 WAV, 12
tests) — écrit par un autre processus, qui faisait aussi des `git add`.

Trois symptômes, aucun évident :

1. **Un compte de tests qui saute** — 43 → 57 sans que j'aie ajouté 14 tests. C'est ce qui a mis la
   puce à l'oreille.
2. **Des fichiers partagés mixtes** — `graybox_root.gd`, `enemy_controller.gd` et
   `player_fighter_controller.gd` contenaient *leur* travail **et** le mien. Un `git add -A` aurait
   produit un commit qui s'attribue le code d'autrui.
3. **Une porte de qualité rouge sans mon code en cause** — leur refonte à mi-chemin cassait leur
   propre test (`pickup_collect` retiré de la banque, encore exigé par le test).

## Le réflexe qui a sauvé la mise

Avant tout commit, quand `git status` montre des fichiers qu'on n'a pas touchés :

```bash
git status --short              # ⚠️ sans | head : la troncature masque l'ampleur
git log --oneline -5
for c in <mes commits>; do git show --stat --format="" $c | grep -i <domaine-suspect>; done
```

Puis **séparer** : sauvegarder ses propres versions, reconstruire des versions « travail d'autrui
seul » en retirant ses hunks, committer le travail d'autrui **d'abord et tel quel**, puis reposer le
sien par-dessus. Deux commits, chacun sa paternité.

Et **sauvegarder son propre travail en patch** tant qu'on ne peut pas committer :

```bash
git diff HEAD -- <mes fichiers> > /tmp/…/mon-correctif.patch   # réapplicable par git apply
```

## Le piège suivant : `C:\tmp` n'est pas cloisonné par les worktrees

Un worktree isole le **dépôt**, pas les **ressources externes**. `deploy-win.sh` fait deux choses
globales, partagées par tous les agents :

1. il **tue tous les processus `AegisAscendant`** avant de copier ;
2. il écrase `/mnt/c/tmp/aegis-ascendant/`.

Donc un agent qui déploie **tue le jeu d'un autre**. Symptômes observés le 12/07/2026, et leur
vraie cause :

| Symptôme | Ce qu'on croit | Ce que c'est |
|---|---|---|
| `game exited with code 255` juste après le boot | le jeu crashe | un autre agent a déployé et l'a tué |
| `cp: Permission denied` sur `AegisAscendant.exe` | droits WSL cassés | le processus de l'autre agent verrouille l'exe |

**Avant de conclure au crash**, relancer une fois : si l'arc se déroule et sort en **code 0**, il n'y
avait pas de bug. Et avant de déployer quand un autre worktree est actif, le dire à l'opérateur —
on va couper sa fenêtre de jeu.

## L'autre écrivain n'est pas forcément un agent Claude (20/07/2026)

Le second écrivain peut être un **outil tiers sous un autre compte Unix**. Sur ce poste, un agent
**Codex** et **GitKraken** tournent sous l'utilisateur **`faro`** (le dépôt est partagé). Ils ne
font pas de `git add` concurrents comme un autre Claude : ils bloquent par les **droits** et par des
**fichiers fantômes**. Quatre blocages distincts, tous vécus dans la même session, tous d'aspect
« bug de mon travail » alors qu'aucun ne l'était :

| Symptôme | Ce qu'on croit | Ce que c'est | Correctif (opérateur, sudo) |
|---|---|---|---|
| `git … : impossible d'accéder à '.git/config'` | dépôt corrompu | GitKraken a `chown`é `.git/config` vers `faro` | `sudo chown happykiller:happykiller .git/config` |
| `droits insuffisants pour ajouter un objet à .git/objects` | index cassé | des shards `.git/objects/xx` appartiennent à `faro` ; l'échec est **aléatoire** selon le hash du blob | `sudo chown -R happykiller:happykiller .git` |
| `check.sh` rouge : `ERROR: Cannot go into subdir 'NUL'` | assets corrompus | un script Codex redirige vers `NUL` (convention Windows) ; sous WSL ça **crée un vrai répertoire** que Godot refuse de scanner | `sudo rm -rf NUL` (il **revient** tant que Codex tourne) |
| remote `git@github-happykiller/…` sans `:` ni propriétaire | clé SSH cassée | l'URL avait été réécrite invalide | `git remote set-url origin git@…:Owner/repo.git` |

**Le fichier `NUL` est le piège le plus coûteux** : il réapparaît à chaque exécution d'un script
Codex, donc le supprimer ne suffit pas — il faut **tarir la source** (fermer Codex, ou corriger sa
redirection `> NUL` en `> /dev/null`). Diagnostic : `stat -c '%y %U' NUL` montre l'horodatage et le
propriétaire `faro`.

**Réflexes** :

- Quand un échec git/porte est un problème de **droits ou de fichier fantôme**, ne pas chercher le
  bug dans son propre code : vérifier `find .git -user faro | wc -l` et la présence de `NUL`.
- **Prouver que l'échec n'est pas le sien** avant d'accuser son travail :
  `godot4 --headless --import 2>&1 | grep ERROR | grep -v NUL` — si c'est vide, seul `NUL` bloque.
- **Voir le rendu malgré une porte rouge irréductible** : exporter depuis une **copie** du dépôt
  dans le scratch, sans le fichier fantôme.
  `tar -c --exclude=NUL --exclude=.git --exclude=.godot --exclude=build … | tar -x -C <scratch>`,
  puis `godot4 --path <scratch> --import` et `--export-debug`. Ne touche ni au dépôt ni au fantôme.
- **Un `.git` partiellement possédé par `faro` casse les commits de façon intermittente** : un
  `chown -R .git` d'un coup vaut mieux que fichier par fichier.
- Le correctif durable n'est pas à moi : **manipuler ce dépôt sous un seul compte** (git en CLI sous
  `happykiller`, ou GitKraken sous `happykiller`). Le signaler à l'opérateur plutôt que de rejouer
  le blocage à chaque commit.

## Ne jamais faire

- `git add -A` quand l'arbre contient du travail dont on n'est pas l'auteur.
- « Réparer » le test rouge d'un autre agent : c'est son chantier en cours, pas un bug.
- Diagnostiquer un crash sur un seul lancement raté quand un autre agent déploie en parallèle.

## Toujours un `timeout` sur une commande qui lance le jeu

Le jeu en `--demo` **ne s'arrête jamais** : il rejoue l'arc en boucle. Un `deploy-win.sh` lancé sans
`timeout` **bloque la session indéfiniment** — l'opérateur doit interrompre à la main (vécu le
12/07/2026, y compris via un sous-agent, qui a hérité du blocage).

```bash
timeout 240 ./scripts/deploy-win.sh -- ++ --novsync --goto-graybox --demo > /tmp/arc.log 2>&1
echo "exit=$?"   # 124 = timeout atteint : NORMAL, c'est la garantie qu'on garde la main
```

Deux pièges de plomberie qui font perdre la sortie :

- **Ne pas mettre `timeout … | grep …` en pipe** : le tampon avale les lignes et on ne voit rien.
  **Rediriger vers un fichier**, puis lire le fichier.
- Pour horodater les jalons, piloter le processus **depuis Python** (`subprocess.Popen`, lecture
  ligne à ligne, `deadline` explicite, `p.kill()` en `finally`) : c'est le seul montage qui donne à
  la fois les temps et la certitude de rendre la main.

Et si un lancement précédent a été interrompu, **l'exe reste verrouillé** (`cp: Permission denied`) :
tuer le processus et laisser Windows relâcher le handle avant de redéployer.
