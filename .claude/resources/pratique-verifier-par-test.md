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
