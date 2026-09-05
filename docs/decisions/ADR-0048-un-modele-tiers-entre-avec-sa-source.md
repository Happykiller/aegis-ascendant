# ADR-0048 — Un modèle tiers entre avec sa SOURCE, et on écrit sa transformation

- **Date** : 2026-09-05
- **Statut** : accepté (décision du propriétaire du projet : « *on doit reprendre la main
  sur ce modèle* »)
- **Déroge à** : `ADR-0008` — « le script Python EST la source de l'asset. Aucun `.blend`
  n'est versionné » — **pour les modèles tiers uniquement**
- **Précédent** : `specter_9_b`, entré en 2026-08 sans source ni possibilité de le modifier

## Contexte

Le projet a désormais deux coques qu'il n'a pas produites. La première, `specter_9_b`,
est entrée comme un `.glb` seul : belle, jouable, et **définitivement figée** — aucune
retouche n'a jamais été possible, ni de sa livrée, ni de sa géométrie.

La seconde, `specter_9_v3`, est arrivée avec plus : un `.blend`, un script, un README, une
vérification. De quoi croire le pipeline complet. **Il ne l'est pas**, et l'opérateur l'a
vu avant moi :

> « les modèles qui nous ont été partagés ne sont pas complets. Les scripts que tu as,
> c'est juste des scripts d'évolution d'une version à une autre. Ce n'est pas le script
> qui génère l'intégralité du modèle. C'est un peu comme les sources, et le Blender ou le
> glTF, c'est le livrable. »

C'est exactement ce que le fichier montre. `build_spectre9_v3.py` ouvre un
`spectre9_v2.blend` **absent du dépôt**, efface les animations, **supprime** une liste de
pièces, et les reconstruit. **241 lignes pour 525 objets** : c'est un *diff*, pas une
origine. La chaîne v1 → v2 → v3 n'existe qu'en partie, et son premier maillon manque.

## La question posée, et pourquoi elle se referme

> « Est-il indispensable de faire une rétro-ingénierie pour reconstituer le générateur, ou
> est-ce impossible ? »

**Ni l'un ni l'autre — c'est le mauvais problème.** Le `.blend` est déjà l'état complet :
525 objets, 10 matériaux, 44 pilotes, 4 images. Tout ce qu'une chaîne de scripts aurait
produit y est **matérialisé**. Reconstituer le générateur ne servirait qu'à re-dériver ce
qu'on tient déjà, au prix de rétro-concevoir 525 objets — et le résultat ne serait pas une
reconstruction, mais un vaisseau **nouveau** qui lui ressemble.

Ce dont on a besoin n'est pas de *régénérer* mais de *modifier*. Et cela, le `.blend` le
permet : il s'ouvre sous notre Blender épinglé, ses pilotes se lisent et s'écrivent, ses
matériaux sont nommés.

## Décision

**Un modèle tiers entre dans le dépôt avec sa source, et le projet écrit les
transformations qu'il lui applique.**

```
.blend        la SOURCE            assets/source/models/<coque>/   (versionnée, LFS)
.glb          le LIVRABLE          assets/imported/models/ships/
nos scripts   la TRANSFORMATION    tools/blender/adapt_<coque>.py
```

### 1. La source est versionnée — et c'est la dérogation

`ADR-0008` interdit de versionner un `.blend`, pour une raison qui reste **entièrement
valable pour les coques du kit** : leur source est leur script, et garder un binaire à
côté créerait deux vérités. Un modèle tiers n'a pas ce choix : **sa source EST son
`.blend`**. Refuser de le versionner, c'est décider qu'on ne le modifiera jamais — ce qui
est précisément l'impasse de `specter_9_b`.

**La dérogation est bornée** : elle vaut pour un modèle que le projet n'a pas produit.
Les coques du kit ne changent pas de régime.

### 2. Ce qui accompagne la source

Le script de l'auteur (même incomplet — il documente ses intentions), son README, sa
vérification, et **toute dépendance qu'on a pu retrouver**. Pour `specter_9_v3`, le
`geometry.py` que son script importe manquait de son dossier : il a été récupéré depuis
celui d'un autre modèle du même auteur, et il fournit exactement les neuf fonctions
importées.

### 3. La transformation est à nous, et elle est un script

Pas une retouche à la main dans Blender. Un fichier dans `tools/blender/`, relisible,
rejouable, qui ouvre la source, applique le changement, cuit les pilotes en images clés et
exporte. **C'est la méthode de l'auteur, continuée** — lui aussi transformait plutôt que
de générer.

⚠️ **Un glTF n'exécute pas les pilotes de Blender.** Sans la cuisson en images clés, le
`.glb` sortirait avec une animation vide et la coque serait figée en jeu, sans erreur.

### 4. Ce que ce régime ne permettra jamais

Un changement **paramétrique** de la coque entière — « refais-la 10 % plus large ». Cela
demanderait le générateur, qu'on n'a pas et qu'on ne cherchera pas à reconstituer. Les
transformations possibles sont **discrètes** : un axe, une couleur, une pièce ajoutée ou
retirée.

## Ce qui ne change pas

- **Le `.glb` reste exactement ce que l'export produit** ; échelle, orientation et points
  d'accroche vivent dans une **scène d'ajustement** (`scenes/player/hulls/`), jamais dans
  le fichier livré. Convention posée par `specter_9_b`, conservée.
- **La hitbox vient des Resources de gameplay** (`ADR-0034`), jamais du maillage.
- **Le contrat de dimensions** d'`ADR-0008` s'applique après mise à l'échelle : la
  `specter_9_v3` tient à −0,95 % de l'envergure admise, sans dérogation.
- **Les sept matériaux `AA_*`** restent imposés aux coques **du kit**. Un modèle tiers
  porte les siens ; `HullDetail` ne les touche pas, faute de les reconnaître.

## Conséquences

- `assets/source/models/` est un dossier neuf, `.gdignore`é comme tout `assets/source/` —
  ce qui évite au passage que Godot tente d'importer un `.blend` et réclame un chemin
  Blender qu'il n'a pas en headless.
- Le poids LFS augmente d'un `.blend` par modèle tiers (14 Mo pour celui-ci).
- ⚠️ **Un couplage caché a été trouvé sur le premier usage**, et il faut s'y attendre sur
  les suivants : parmi les 44 pilotes de ce modèle, deux font balayer les ailes et deux
  autres les **contre-braquent** pour garder les canons vers l'avant. Modifier les
  premiers sans les seconds aurait produit des canons de travers, sans une erreur ni une
  ligne de journal. **Un modèle livré sans documentation cache ses dépendances internes :
  les lister avant de toucher quoi que ce soit fait partie de la transformation.**
