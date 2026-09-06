# Howto — décider quoi faire d'un modèle 3D qui nous est poussé

## Pourquoi cette page

L'opérateur dépose des modèles dans `resources/gpt_models/`. Ils arrivent tous avec le même
habillage — un `.blend`, un `.glb`, des scripts Python, un README, une `verification.json`, des
rendus — et **ce même habillage recouvre deux régimes opposés**. Se tromper de régime coûte soit
une rétro-ingénierie inutile, soit un copier-coller qui importe des régressions.

Il existe **une commande** qui tranche, et elle prend deux minutes.

## Le test qui tranche : rejouer le générateur

```bash
SB=<scratchpad>/rejeu
mkdir -p $SB && cp resources/gpt_models/<modele>/*.py resources/gpt_models/<modele>/reference.png \
                  resources/gpt_models/<modele>/textures -r $SB/ 2>/dev/null
cd $SB && blender-aegis -t 1 -b -noaudio --python build_<modele>.py
sha256sum $SB/<modele>.glb resources/gpt_models/<modele>/<modele>.glb
```

⚠️ **`-t 1` est obligatoire**, comme partout ici : c'est lui qui rend la sortie reproductible.
Ne copier que les sources — si le `.glb` livré est présent dans le bac à sable, on ne saura pas
si le script l'a écrit ou si on le relit.

**Regarder d'abord la première ligne du script** :

| Ce qu'on lit en tête | Régime | Ce que ça veut dire |
|---|---|---|
| `bpy.ops.wm.read_factory_settings(use_empty=True)` | **générateur** | il construit tout depuis rien |
| `bpy.ops.wm.open_mainfile(...)` | **diff** | il TRANSFORME un `.blend` antérieur |

## Les deux régimes, et ce qu'on fait de chacun

### Régime générateur — porter la RECETTE

Mesuré le 2026-09-05 sur `tourelle-lourde_v1` : 386 lignes, parties d'une scène vide, et le
rejeu rend **le même sha256 au bit près** (`86fbaf62…`), cartes PBR cuites comprises, sur notre
Blender 5.2.1 épinglé.

C'est **exactement notre régime** (`ADR-0008` : le script est la source). On peut donc lire ses
recettes et les ré-exprimer avec notre kit, notre palette, nos cotes — sans reprendre un seul
fichier. C'est ce qu'a fait `BRIEF-0100`.

⚠️ **Porter ≠ copier.** Ce qui se porte, ce sont des procédés : « le socle est fait de 24 modules
et non d'un disque », « toute plaque est posée sur un retrait sombre et bordée d'un liseré clair ».
Ce qui ne se porte pas : les cotes (elles sont bornées par NOTRE coque), la palette (elle
appartient à une faction), et le motif `for obj in set(...)` — l'ordre d'un `set` Python n'est pas
garanti d'une exécution à l'autre, et il casserait le déterminisme.

### Régime diff — versionner la SOURCE (`ADR-0048`)

Mesuré le même jour sur `spectre9_v3` : 241 lignes pour 525 objets, et le fichier qu'il ouvre
(`spectre9_v2.blend`) **n'est pas dans la livraison**. La chaîne est incomplète et son premier
maillon manque.

Ici la rétro-ingénierie est **le mauvais problème** : le `.blend` contient déjà l'état complet.
On versionne la source, on écrit notre transformation dans `tools/blender/adapt_<coque>.py`, et on
accepte de ne jamais pouvoir faire de changement paramétrique.

## Ce que le rejeu ne dit pas, et qu'il faut mesurer à part

- **Si ça tient dans notre coque.** L'emprise, la hauteur sous le plafond de vol, les dégagements
  — voir [la cote vient de l'asset](pratique-la-cote-vient-de-l-asset.md). Le modèle de tourelle
  poussé faisait 3,62 m de rayon là où la coque en accepte 2,60 : il **débordait dans le vide**.
- **Si ça se lit dans notre moteur.** Un rendu Cycles ne prouve rien de la chaîne de sortie. Monter
  le modèle en jeu derrière un drapeau (`--turret-proto`) et capturer **au même instant du survol,
  à la même caméra**, coûte deux lancements et tranche la question.
- **Ce que ça coûte.** Quatre relevés GPU du même jour (1,037 / 1,209 puis 1,800 / 0,765 ms) sont
  dominés par la dispersion : ils n'établissent **aucun** surcoût et n'en excluent aucun. Un
  chiffre isolé ne mesure rien ici — voir [mesurer la perf](howto-mesurer-la-perf.md).

## L'ordre qui a marché

1. Archiver la planche fournie (`assets/reference/concepts/`) + sa ligne de provenance.
2. Rejouer le script → **quel régime ?**
3. Monter le modèle en jeu derrière un drapeau, capturer contre l'existant, **regarder**.
4. Écrire le brief à partir de ce que la capture a montré, pas de ce que le rendu studio promettait.
5. Retirer le drapeau et le `.glb` de banc d'essai — ils gonflent l'export tant qu'ils traînent.

## ⚠️ L'audit de poids passe AVANT tout le reste (2026-09-06)

Quatre livraisons d'un agent tiers sont arrivées le même jour pour la poupe du niveau 2. Mesuré sur
les binaires, en quatre lignes de Python (chunk JSON du `.glb`) :

| pièce | poids | triangles | images | clips |
|---|---|---|---|---|
| groupe moteur | 70,4 Mo | **276 816** | 11 | 3 |
| berceau | 64,9 Mo | **157 104** | 11 | 4 |
| ancrage destructible | 59,4 Mo | **54 640** | 11 | 5 |
| bras d'ancrage | 60,1 Mo | **66 332** | 11 | 6 |
| *pour mémoire* `long_cortege.glb` — les 500 m, 5 tronçons, 30 marqueurs | — | **49 458** | 0 | — |

Aux quantités que la phase demande (3 moteurs, 3 berceaux, 10 ancrages, ~20 bras) : **≈ 3,17
millions de triangles et ~1 Go**, soit **soixante-quatre fois tout le niveau**.

**La géométrie et les cotes étaient justes** — l'ancrage fait exactement les 2,40 × 1,40 × 1,20 de
sa planche, le berceau porte même son contrat de mariage écrit au millimètre. Ce n'est donc pas une
livraison ratée : c'est une livraison **à un autre budget**, et l'ordre de travail en dépend
entièrement.

**Ce qu'il faut mesurer avant de se réjouir, dans cet ordre :**

1. **triangles et poids**, comparés à ce que le dépôt embarque déjà — un rapport, pas un chiffre ;
2. **noms de matériaux** : `01 | Anthracite blinde`, `06 | Energie magenta`… au lieu de `AA_*`.
   `CortegeSkin` reconnaît son émissif **par son nom** — tel quel, rien n'est habillé et surtout
   **rien ne peut s'éteindre**, sans qu'aucune erreur ne le dise ;
3. **images embarquées** : onze par pièce, sur un niveau dont le harnais échoue le build si une
   texture apparaît ;
4. **noms de nœuds** : 1 300 nœuds en clair avec suffixes `.001`. Le moteur adresse ses marqueurs
   par leur nom ; il faut un contrat, pas un inventaire ;
5. **clips**, qui sont souvent le vrai cadeau — `Ouverture` et `Fermeture` séparés valent mieux
   qu'un changement de couleur, et `ADR-0046` rappelle qu'un glTF **n'exécute pas les drivers**.

⚠️ **Et l'échelle ne se déduit pas d'un rendu.** Trois berceaux livrés côte à côte font 33,6 m
quand le joueur n'en couvre que 28 : leurs ancrages extérieurs seraient hors de portée. Les
« coller » ne suffisait pas — **jointifs, ils font déjà 33,6**. Seule une réduction d'échelle
passait, et c'est une contrainte de GAMEPLAY qu'aucune revue d'asset ne voit.

