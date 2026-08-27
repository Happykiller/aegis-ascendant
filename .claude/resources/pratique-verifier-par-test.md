# Bonne pratique — vérifier par test, pas par capture chanceuse

## La règle

Si l'événement à observer est **probabiliste**, la capture d'écran est le mauvais outil. Écrire le
test qui le force.

## Cas vécu (12/07/2026) — l'impact des tirs

Après avoir câblé la gerbe d'impact, j'ai voulu la prouver par capture. En mode `--demo` le vaisseau
balaie latéralement pendant que les ennemis dérivent : les tirs se croisent sans se toucher.
**Quatre captures à des images différentes, zéro impact visible.** Je pêchais une image chanceuse.

Le test déterministe, lui, a pris deux minutes et prouve exactement la propriété :

```gdscript
func test_hit_reports_impact_position_and_victim() -> void:
    bm.target_hit.connect(_on_target_hit)
    bm.register_target(_make_target(Team.PLAYER, Vector2(2.0, -3.0), 0.4))
    bm.spawn_bullet(Team.ENEMY, Vector2(2.0, -3.2), Vector2.ZERO, 0.1, 10.0, 5.0)
    bm.step(1.0 / 60.0)
    assert_eq(_impacts.size(), 1, "impact reported once")
```

## Cas vécu — le boss qui mourait deux fois

Bug rapporté par l'opérateur au bout de **trois parties enchaînées** : il fallait que deux
projectiles atteignent le boss **sur la même image**. Injouable à reproduire à la demande.

Le test le force en une ligne : quatre balles simultanées sur une cible qui meurt à la première →
`assert_eq(_lethal_hits, 1)`. La capture n'aurait **jamais** attrapé ça.

## Un test qui construit un Node le fuit — `track()` (23/08/2026)

Les tests tournent en mode `--script` : **il n'y a pas d'arbre de scène**. Une unité `RefCounted`
meurt avec le cas de test ; un **`Node` construit à la main n'a aucun parent pour le récupérer** et
survit jusqu'à la fin du process. Godot ne rapporte la pile qu'à la sortie :

```
WARNING: 789 ObjectDB instances were leaked at exit
```

Ce chiffre **ne désigne jamais son coupable** — il tombe après le dernier test, tous fichiers
confondus. Pour l'attribuer : exécuter **un fichier de test par process** et lire le compte de
chacun. Ici la totalité venait d'un seul (`test_leviathan_combat.gd`, un `LeviathanCombat extends
Node` par méthode) pendant que le backlog l'annonçait à « 8, tweens/timers non libérés » — le
diagnostic hérité était faux **et** cent fois trop petit.

La parade est dans le socle : `tests/test_case.gd` expose `track()`, et le runner appelle
`free_tracked()` après chaque méthode.

```gdscript
var combat := track(CombatScript.new()) as LeviathanCombat
```

Ne pas tracker un nœud qu'un parent tracké possède déjà — `add_child()` suffit, le parent le libère.

**Pourquoi s'en soucier alors que le test passe** : ce bruit est inoffensif *en soi*, mais il occupe
la place où s'afficherait une **vraie** fuite runtime. Une sortie de check propre est un instrument ;
une sortie qui crie déjà 789 objets n'en est plus un.

## Le partage

| Ce qu'on veut savoir | Bon outil |
|---|---|
| « À quoi ça ressemble ? » (couleur, échelle, composition, lisibilité) | **Capture** — cf. [howto-verifier-un-rendu](howto-verifier-un-rendu.md) |
| « Est-ce que ça arrive, et une seule fois ? » (logique, signal, race, cas limite) | **Test** |
| « Combien ça coûte ? » | **Mesure GPU** — cf. [howto-mesurer-la-perf](howto-mesurer-la-perf.md) |

Une capture répond à « à quoi ça ressemble », **jamais** à « est-ce que c'est correct ».

## ⛔ Ne JAMAIS défaire une mutation avec `git checkout <fichier>`

**Deux fois dans la même session, le 2026-08-27.** La seconde a effacé toute une
implémentation non commitée — variables, méthode extraite, réinitialisation — en une commande
tapée par réflexe après un test de mutation réussi.

Le piège est que le geste a l'air sûr : on vient d'écrire *une* ligne de mutation, on veut la
retirer, et `git checkout` est la façon évidente. Sauf qu'il ne retire pas la mutation, il
**ramène le fichier à HEAD** — donc il emporte aussi tout ce qu'on venait d'écrire et qui n'est
pas encore commité, c'est-à-dire précisément le code que la mutation servait à éprouver.

Le remède, en deux lignes :

```bash
cp fichier.gd "$SCRATCH/fichier.gd.avant"   # AVANT de muter
# ... muter, lancer les tests, lire le rouge ...
cp "$SCRATCH/fichier.gd.avant" fichier.gd   # rendre exactement l'etat d'avant
```

Ou muter par substitution réversible (`sed` dans un sens, puis dans l'autre) — jamais par un
appel à git. **Règle** : aucune commande git qui écrit dans l'arbre de travail pendant qu'il
porte du travail non commité, sauf `git add`/`git commit`.

Corollaire : **commiter avant de muter** est la vraie protection. Un test de mutation se fait
sur du travail déjà sauvé ; le rouge attendu ne prouve rien de plus s'il est obtenu sur du code
qu'on risque de perdre.

## Une garde qui RECOPIE le code ne teste rien (27/08/2026)

La garde de la répulsion entre ennemis rejouait à la main les quatre lignes du pas d'image —
retirer l'écart, avancer, le réappliquer — au lieu d'appeler ce pas. Elle était verte, et elle
serait **restée verte** le jour où le contrôleur aurait oublié de réappliquer l'écart : elle
testait sa propre copie.

Le nœud du problème est réel : le contrôleur est un `Node`, et son `_physics_process` n'est pas
appelable en headless. La tentation est alors de reproduire ce qu'il fait.

**Le remède** : extraire le pas dans une méthode publique (`step_position(delta)`) et faire
appeler **celle-là** par le test *et* par `_physics_process`. Une méthode publique de plus vaut
mieux qu'une garde qui ment.

**Le témoin qui tranche** : muter le code et vérifier que la garde rougit. Ici, retirer la
réapplication de l'écart — la garde d'origine passait, la garde rebranchée échoue avec
« l'écart a survécu au recalcul (0.00 u) ».

## ⛔ Un seuil INVENTÉ dans une garde est une panne qui dort (27/08/2026)

Trois fois dans la même session, et à chaque fois le même mécanisme : une garde verte qui tenait
un chiffre que personne n'avait dérivé de quoi que ce soit.

| Garde | Le chiffre inventé | Ce que ça a coûté |
|---|---|---|
| couverture du blindage | « < 35 % » | l'équilibrage calculait avec 45 % — huit à douze plongées au lieu de trois, aucun test rouge |
| durée de la plongée | « ≤ 6 s » | interdisait de relever un **plafond** que le joueur de référence n'atteint jamais |
| bousculades au contact | « < 260 sur 600 » | mesurait un taux là où le fait qui compte est « le blindage finit-il par laisser passer ? » |

Une borne inventée ne protège de rien : elle **fige un chiffre plausible** et donne à la suite
l'autorité d'une mesure. Pire, elle rend vert un désaccord entre deux valeurs qui décrivent le
même fait.

**La règle** : une garde numérique doit lire son seuil **dans la donnée qui décide** — la Resource
que le jeu emploie, la dimension mesurée sur le modèle, la cible déclarée. `assert ratio ≈
tuning.ring_occupancy` vaut mille fois `assert ratio < 0.35`, parce qu'elle rougit aussi quand
c'est l'estimation qui a tort.

Et quand aucune donnée ne porte le seuil, c'est souvent qu'on mesure la mauvaise chose : la
question « combien d'images bousculées ? » n'avait pas de bonne réponse ; « le joueur garde-t-il
le contrôle en longeant ? » en avait une, et binaire.

## Mesurer un `.glb` : parcourir la hiérarchie, ou se tromper (27/08/2026, 2ᵉ fois)

Lire les `min`/`max` des accesseurs `POSITION` donne les bornes **en espace local de chaque
maillage**. Une pièce portée par un nœud décalé — un canon de bout d'aile, un bras — en sort.

Le Specter-9 mesure ainsi **1,30** de large au lieu de **1,752**. Le chiffre faux est parti dans
un brief de forge le 25/08, et il est revenu le 27/08 : j'allais « corriger » une constante de
test qui avait raison depuis le début.

**Le contrôle gratuit** : comparer au chiffre déjà écrit quelque part (constante de test, doc de
Resource). Deux mesures qui divergent d'un facteur ~1,35 signent un oubli de transformation, pas
une erreur de l'autre.

Il faut composer `translation`/`rotation`/`scale` (ou `matrix`) de chaque nœud en descendant, et
transformer **les huit coins** de la boîte locale — pas seulement `min` et `max`, qui ne sont plus
les extrêmes après rotation.
