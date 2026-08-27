# ADR-0029 — La dérive organique : une graine par instance, sur des périodes non harmoniques

- **Date** : 2026-08-27
- **Statut** : accepté (décision de l'opérateur après playtest)
- **Complète** : `ADR-0022` (les ennemis peuvent connaître le joueur) sur son **contrat de
  pureté** — qu'il ne remet pas en cause, et dont il conserve les trois garanties.
- **Ne touche pas** : le pooling (spec §26.1), la règle de variété d'`enemy_path.gd`, le
  budget d'allocation.

## Contexte

Playtest du 2026-08-27, arc complet joué à la main. Verdict de l'opérateur, mot pour mot :

> « J'aimerais que tous les ennemis aient des mouvements aléatoires non linéaires, même s'ils
> doivent respecter un pattern. **Ça fait figé, fête foraine, nul.** »
>
> « D'ailleurs le boss aussi a ce défaut. »

**Le constat se vérifie dans le code, et il est structurel.**

`EnemyPath` est une bibliothèque de fonctions **pures** : `(données, âge, spawn) → position`.
Aucun aléa, aucune graine. Deux unités du même type nées au même endroit décrivent donc
**exactement** la même courbe, en même temps — une nuée de quatre coques espacées de 0,7 s
ondule à l'unisson, décalée d'un pas constant. C'est une formation de parade, pas un vol.

`BossMovement` a le même défaut par un autre chemin : ses quatre figures sont **harmoniques**
(`w`, `w × 2`, `w × 0,5`), donc elles **bouclent exactement**. À la troisième répétition, l'œil
a la figure entière et le boss cesse d'être un adversaire pour redevenir un mobile.

⚠️ **Cette pureté n'est pas un accident, et on ne veut pas la perdre.** `ADR-0022` la défend
explicitement ; elle achète trois choses :

- **le pooling est sûr** — une instance réactivée repart de son spawn sans traîner l'état de la
  précédente, puisque sa position ne dépend que de son âge ;
- **la forme ne dépend pas du pas de temps** — rien ne s'accumule ;
- **tout se teste en headless**, sans arbre de scène ni joueur.

## Décision

**Une graine par instance, ajoutée en DÉCALAGE sur des périodes non harmoniques.**

```
position_at(données, âge, spawn)  →  position_at(données, âge, spawn, graine)
```

Le module `OrganicDrift` rend un **décalage**, jamais une position. Il reste donc une fonction
pure de `(âge, graine, amplitude)`, et les trois garanties tiennent :

| Garantie d'`ADR-0022` | Comment elle survit |
|---|---|
| Pooling sûr | la graine est **réassignée à chaque activation** — une coque réutilisée ne rejoue pas le mouvement de la précédente |
| Indépendance au pas de temps | le décalage est une fonction de l'âge : rien ne s'accumule |
| Testable en headless | une graine fixe rend un chemin déterministe ; `NO_DRIFT` rend la courbe **nue**, et c'est sous cette forme que les tests jugent sa signature |

### Deux périodes, et elles ne doivent jamais tomber en rythme

**2,9 s et 4,7 s** — rapport 1,62. Leur somme ne se répète pas avant plus de deux minutes,
très au-delà de la vie d'une unité (~6 s pour traverser le champ).

⚠️ **Le remède existait déjà dans ce dépôt, et n'avait jamais été transposé.**
`title_stage.gd` fait dériver la caméra de l'accueil sur des périodes « volontairement non
harmoniques (11,0 / 7,3 / 17,0 s) », avec ce commentaire :

> « la scène ne doit jamais se retrouver deux fois dans la même pose, sinon **l'œil repère la
> boucle** et l'accueil redevient un décor. »

C'est le reproche de l'opérateur, mot pour mot, résolu ailleurs deux mois plus tôt.

### La graine est DÉTERMINISTE, et c'est le point le plus discutable

L'opérateur a demandé des mouvements « aléatoires ». Nous posons une graine **dérivée du rang
d'apparition** (suite du nombre d'or modulo 1) : les unités varient **entre elles**, mais une
vague rejouée est identique.

**Pourquoi** : la mémorisation est un pilier du genre — « la clé pour gagner à un shmup est la
mémorisation » (`LOI-LVL-03`), et « des patterns, pas du chaos » (`LOI-BOS-04`). Une graine
tirée au sort rendrait chaque partie différente, donc **inapprenable** : on troquerait un défaut
de rendu contre un défaut de conception. L'opérateur a d'ailleurs posé lui-même la limite —
« même s'ils doivent respecter un pattern ».

Le nombre d'or n'est pas décoratif : c'est une suite à **faible discordance**, donc deux
ennemis **successifs** d'une même nuée reçoivent les phases les plus éloignées possible. C'est
exactement le cas qui se voyait.

### Une amplitude par trajectoire, pour ne pas effacer les signatures

Le risque symétrique d'un bruit ajouté à tout le monde : que les trajectoires cessent de se
distinguer. Chacune reçoit donc sa part :

| Trajectoire | Part | Pourquoi |
|---|---:|---|
| `DRIFT` | 0,3 | « elle ne manœuvre pas » — juste assez pour ne plus être tracée à la règle |
| `SERPENTINE` | 0,5 | ses cassures nettes **sont** sa lecture ; trop de dérive les arrondirait |
| `DIVE` | 0,5 | l'accélération est l'information |
| `HOVER_STRAFE` | 0,6 | elle tient sa ligne pour viser (tir `AIMED`) : elle respire, elle ne se déplace pas |
| les autres | 1,0 | — |

Amplitude de référence : **0,55 u** pour une unité, **1,1 u** pour un boss (une coque de onze
mètres qui bougerait d'une demi-unité ne bougerait pas).

### La rampe de 0,6 s existe pour une raison dure

À l'âge zéro, le décalage vaut **exactement zéro**. Une unité doit apparaître **à son point de
spawn** : c'est le contrat que `test_enemy_path.gd` garde depuis toujours, et c'est lui qui rend
le pooling observable. Une dérive à pleine amplitude dès la première image téléporterait chaque
réapparition d'un demi-mètre — sans erreur, sans test rouge, et invisible autrement qu'en jouant.

## Conséquences

**Acquis.** Une nuée cesse de voler en miroir ; une figure de boss cesse de boucler ; et rien de
tout cela ne coûte une allocation, un nœud, ou une once de déterminisme.

**Ce qu'on accepte.** Une vague rejouée est identique à elle-même. C'est un choix, pas une
limite technique : `OrganicDrift.seed_for()` est le seul endroit à changer si l'on veut un jour
du vrai hasard — et il faudra alors mesurer ce qu'on perd en apprenabilité.

**Ce qui est gardé par des tests.** Sept, et ils protègent les **deux** risques opposés : que la
dérive ne serve à rien (deux voisins volent encore en miroir, les périodes retombent en rythme,
le mouvement se répète dans une vie d'unité) et qu'elle serve **trop** (deux trajectoires
deviennent confondables, celle qui ne manœuvre pas se met à manœuvrer, une unité n'apparaît plus
sur son spawn). Le seuil de non-répétition est **mesuré** — pire cas 0,41 u au décalage 0,4 s —
et le décalage testé est **borné par la durée de vie** : une quasi-répétition à treize secondes
d'écart existe dans tout signal quasi périodique et n'intéresse aucun joueur.

**Ce qui reste à faire.** Le jugement en mouvement. Une capture montre une nuée **décalée** au
lieu d'une formation de parade ; elle ne dit pas si ça se sent manette en main.
