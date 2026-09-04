# Bonne pratique — quand deux sources décrivent la même position, teste leur COMPOSITION

## La règle

Dès qu'une position finale résulte de **deux sources** — un nœud qui se place *et* une géométrie
qui porte déjà son décalage, un réglage *et* une table livrée, une constante GDScript *et* une
constante Python — **aucun test par source ne suffit**. Chacune peut être juste séparément
pendant que leur composition est fausse.

Le test doit refaire **la chaîne entière, exactement comme le moteur**, et la comparer à ce que
le résultat doit être. Pas la moitié, pas les deux moitiés : la composition.

## Cas vécu (04/09/2026) — deux relais à des dizaines de mètres, sous 850 tests verts

La forge cuit le **X de coque dans la géométrie** : le relais de la Citadelle est modelé à
`x` 5,40 → 7,00, et le miroir se fait par un **yaw de π**, pas par un signe. Le nœud de la pièce,
lui, se plaçait *aussi* à ±6,20, parce que c'est de là que se déduit sa hitbox.

Les deux écarts s'additionnaient :

- **tribord** partait à `x ≈ 11,60` — au large du bastion, au-dessus du vide ;
- **bâbord**, faute de yaw, revenait se poser **sur l'axe**, derrière le noyau.

⚠️ **Aucune moitié prise séparément n'était fausse.** La position du nœud était juste. La boîte du
maillage était juste. Le centrage en Z était juste — et il avait **son propre test**, écrit
*précisément* pour attraper les défauts de miroir. Il passait. Il gardait **une** moitié.

Le build était vert, 850 tests étaient verts, et **seule la capture l'a vu** (`ADR-0006`) : en
cherchant les deux relais sur l'image, il n'y en avait qu'un.

## Ce qui l'a fermé

Un test qui compose `transform` du nœud × `transform` de la forme × boîte du maillage, et qui
exige que le résultat tombe sur l'emprise **mesurée par la forge** — des deux bords :

```gdscript
var chaine := part.transform * shape.transform
for i in 8:
    var monde := chaine * coin_de_la_boite(i)
    lo = minf(lo, monde.x); hi = maxf(hi, monde.x)
assert_almost_eq(lo, attendu_lo, 0.05, "…")
```

Voir `tests/unit/test_cortege_citadel.gd :: test_the_two_relays_land_where_the_kit_says`.

## Les trois formes qu'a prise ce défaut sur ce projet

| Où | Les deux sources | Ce que ça donnait |
|---|---|---|
| Relais de la Citadelle | nœud à ±6,20 **+** X cuit dans le `.glb` | deux pièces à des dizaines de mètres de leur place |
| Batteries légères | `ds` du moteur **+** `z` décroissant de la coque | chaque batterie en miroir de son hôte (`cortege_hardpoints.gd`) |
| Assise du bastion | `BASTION_BASE_Y` en GDScript **+** `MOAT_FLOOR_Y` en Python **+** le `.glb` | pièce flottante ou enterrée, sans erreur |

Le troisième cas montre la variante la plus vicieuse : **trois fichiers écrivent la même cote et
aucun ne peut lire les deux autres.** Le harnais Blender ne lit pas le GDScript, le moteur ne
relit pas le Python. Le seul élément commun est **le binaire** — donc c'est lui que le test doit
interroger (`test_the_bastion_sits_exactly_on_the_trench_the_hull_digs`).

## Comment le repérer avant qu'il ne coûte

Trois questions, à poser dès qu'on pose une pièce :

1. **Qui d'autre décrit cette position ?** Si la réponse n'est pas « personne », il faut un test
   de composition.
2. **Le test que j'écris interroge-t-il le résultat, ou un ingrédient ?** Un test sur un
   ingrédient passe au vert pendant que le plat est raté.
3. **Existe-t-il un artefact commun aux deux sources ?** S'il y en a un — un `.glb`, une Resource
   livrée — c'est lui qu'il faut lire, pas les deux constantes.

## Ce que ça n'excuse pas

Un test de composition **ne remplace pas la capture**. Ici c'est la capture qui a trouvé le
défaut, et le test n'est venu qu'après, pour qu'il ne revienne pas. L'ordre est toujours le
même : on regarde, puis on grave.
