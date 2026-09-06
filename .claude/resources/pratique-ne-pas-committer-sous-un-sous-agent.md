# Ne jamais `git add -A` pendant qu'un sous-agent écrit

**Payé le 2026-09-06.** La forge exécutait `BRIEF-0104` en arrière-plan — elle régénérait
`long_cortege.glb` et modifiait `build_long_cortege.py`. Pendant ce temps, la session principale
a corrigé des répliques de dialogue et committé avec `git add -A`.

Résultat : le commit `ec4b770`, intitulé *« le jeu disait encore le tronçon d'après — voix
comprises »*, contient aussi **le `.glb` régénéré et les 35 lignes de la table `SPINES`**. Son
message n'en dit pas un mot. Rien n'est perdu, le contenu est bon — mais l'historique ment sur
qui a fait quoi, et le lot de forge n'a plus de commit à lui.

## La règle

**Un sous-agent qui tourne est un second auteur dans l'arbre de travail.** Tant qu'il n'a pas
rendu la main :

- pas de `git add -A`, pas de `git add .`, pas de `git commit -a` ;
- **nommer les fichiers** qu'on committe, un par un — c'est de toute façon la bonne discipline
  pour un commit « petit, un objectif » ;
- et si le doute subsiste, `git status --short` **avant** l'ajout : un fichier qu'on n'a pas
  touché soi-même dans cette conversation n'a rien à faire dans le commit.

## ⚠️ Et ça vaut aussi dans l'autre sens

Le corollaire déjà payé (2026-09-05) : `git checkout --` pour « revenir à l'état d'avant » efface
les modifications non committées **de tout le monde**, y compris celles qu'on venait d'écrire
soi-même trois messages plus haut.

## Ce qui reste à faire quand c'est arrivé

L'historique ne se réécrit pas pour ça. On le **dit** : le commit suivant nomme ce que le
précédent a emporté en silence, et pourquoi. Un historique inexact qu'on sait inexact vaut
infiniment mieux qu'un historique inexact qu'on croit exact.

## Voir aussi

- [Étendre le ghost](process-etendre-le-ghost.md) — quand déléguer à `asset-forge`.
- [Intégrer un modèle tiers](howto-integrer-un-modele-tiers.md)
