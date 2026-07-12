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

## Ne jamais faire

- `git add -A` quand l'arbre contient du travail dont on n'est pas l'auteur.
- « Réparer » le test rouge d'un autre agent : c'est son chantier en cours, pas un bug.
- Diagnostiquer un crash sur un seul lancement raté quand un autre agent déploie en parallèle.
