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

## Le partage

| Ce qu'on veut savoir | Bon outil |
|---|---|
| « À quoi ça ressemble ? » (couleur, échelle, composition, lisibilité) | **Capture** — cf. [howto-verifier-un-rendu](howto-verifier-un-rendu.md) |
| « Est-ce que ça arrive, et une seule fois ? » (logique, signal, race, cas limite) | **Test** |
| « Combien ça coûte ? » | **Mesure GPU** — cf. [howto-mesurer-la-perf](howto-mesurer-la-perf.md) |

Une capture répond à « à quoi ça ressemble », **jamais** à « est-ce que c'est correct ».
