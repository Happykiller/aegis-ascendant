# Pratique — ce qui ne compile pas en Godot 4.7, et ce que l'erreur n'en dit pas

Deux pièges relevés le 2026-08-25, dans la même session. Ils ont coûté un cycle de porte de
qualité chacun — peu, mais **le premier ne se diagnostique pas** : le moteur n'imprime ni ligne,
ni cause.

## `return` au milieu de `fragment()` — l'erreur muette

```glsl
void fragment() {
    if (deep_sky) {
        ALBEDO = ...;
        return;            // ❌ ERROR: Shader compilation failed.
    }
    ...
}
```

Le seul retour du moteur est **`ERROR: Shader compilation failed.`** — pas de numéro de ligne, pas
de motif, rien à quoi se raccrocher. `check.sh` dit « import produced errors » et s'arrête là.

**La forme qui passe** : un `if / else`, avec une seule écriture de `ALBEDO` en sortie.

```glsl
void fragment() {
    vec3 col;
    if (deep_sky) { col = ...; } else { col = ...; }
    ALBEDO = col;
}
```

⚠️ **Bénéfice inattendu de la contrainte** : en factorisant ce qui suivait le `return` — ici le
calme central et l'écriture d'`ALBEDO` — les deux chemins ont cessé de pouvoir diverger. La
restructuration a produit un meilleur shader que le raccourci.

## `const` et tableaux compactés — l'appel de constructeur n'est pas constant

```gdscript
const TIMES := PackedFloat32Array([11.0, 26.0, 40.0])
# ❌ Parse Error: Assigned value for constant "TIMES" isn't a constant expression.
```

L'appel `PackedFloat32Array(...)` est une **construction à l'exécution**, quel que soit son
contenu. La forme constante passe par l'**annotation de type** et un littéral :

```gdscript
const TIMES: PackedFloat32Array = [11.0, 26.0, 40.0]              # ✅
const SPOTS: PackedVector2Array = [Vector2(-6.0, 10.0), ...]      # ✅ — Vector2(...) EST constant
```

À retenir : les constructeurs de types **built-in par valeur** (`Vector2`, `Color`, `Rect2`…) sont
des expressions constantes ; les **tableaux compactés** ne se construisent pas, ils se **convertissent**
depuis un littéral, et c'est l'annotation qui déclenche la conversion.

Le dépôt en avait déjà un exemple sous les yeux — `const _LEVIATHAN_PLATE_LABELS: PackedStringArray
= ["P 1", …]` dans `graybox_root.gd`. Lire une forme qui marche avant d'en inventer une coûte moins
cher que le cycle de parse.


## Deux fautes qui COMPILENT et se voient seulement en jeu (26/08/2026)

Ce fichier collectionnait ce qui ne compile pas. Ces deux-là compilent très bien, passent la
porte de qualité, et cassent à l'exécution — ce qui est pire.

### Un nom de propriété faux n'échoue qu'à l'EXÉCUTION

`_health.maximum` sur un `HealthComponent` qui expose `max_health`. GDScript ne le vérifie
pas à la compilation : `check.sh` reste **vert**, et l'erreur ne sort que si le chemin est
exécuté.

⚠️ **Et le symptôme ne ressemble pas à une erreur.** L'accès invalide interrompt la fonction
au milieu — donc la moitié du travail est faite et l'autre pas. Vécu : une sangsue censée
détoner survivait, passait en épuisée, puis se réarmait et repartait. L'opérateur a rapporté
« les sangsues n'explosent pas, elles repartent » : un comportement plausible, entièrement
faux, et introuvable sans le journal.

**La parade** : un test qui exerce le chemin, même trivial. Le plus bête suffit —
`assert_true("max_health" in objet)` aurait économisé une partie entière.

### ⚠️ Une lambda capture par VALEUR

```gdscript
var vu := false
signal_quelconque.connect(func() -> void: vu = true)   # ❌ modifie une COPIE
assert_true(vu)                                        # échoue sur du code CORRECT
```

Le test affirme alors que rien ne s'est passé, sur un mécanisme qui fonctionne — et l'on
part corriger le code au lieu du test. Passer par un conteneur :

```gdscript
var vu := [false]
signal_quelconque.connect(func() -> void: vu[0] = true)   # ✅
```
