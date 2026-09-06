# Specter-9 D — la source d'une coque étrangère

Régime **`ADR-0048`** : ce modèle n'a pas été produit par le projet, sa source est son `.blend`,
et c'est lui qui fait foi. Livré le 2026-09-06 par un agent tiers, depuis
`~/aegis-ascendant_gpt_models/spectre9-d/v1/`.

| | |
|---|---|
| Livrable intégré | `assets/imported/models/ships/specter_9_d.glb` |
| Scène d'ajustement | `scenes/player/hulls/specter_9_d.tscn` (échelle, lacet, points d'accroche) |
| Planche cible | `assets/reference/concepts/specter_9_d_concept_sheet_2026-09-06.png` |
| Blender de création | **5.2.1 LTS** — notre version épinglée |

## Ce que l'audit a établi, et il compte plus que le README d'origine

### Le générateur se rejoue, mais ne reproduit rien au bit près

`scripts/build.py` part d'une scène vide (`manifest.json` : « *created from scratch for the
supplied Spectre 9-D sheet; no earlier model is an input* »). Rejoué trois fois sur notre Blender
épinglé, `-t 1`, il rend à chaque fois :

    413 nœuds · 406 maillages · 49 116 triangles · bbox 8,8992 × 3,2378 × 12,5229 · mêmes noms

**Et jamais le même sha256** — ni entre eux, ni avec le fichier livré. Mesuré plus finement :
**deux exports du MÊME `.blend`** donnent déjà deux sha256 différents. La divergence est donc dans
`export_asset.py`, pas dans le générateur.

⚠️ **Conséquence : l'invariant d'`ADR-0008` ne s'applique pas ici**, et il ne faut pas prétendre
le contraire. Le modèle est **rejouable** (on obtient la même géométrie) mais pas **reproductible**
(on n'obtient pas le même fichier). C'est un troisième cas, entre le générateur déterministe de la
tourelle lourde et le simple diff de la coque C : *un vrai générateur dont la sortie n'est pas
byte-stable*. Le `.blend` reste donc la référence, et une modification se fait dessus.

### Ce que la livraison ne portait pas

- **Sept points d'accroche sur neuf.** Elle n'a que `MARKER | exhaust L/R`. Les sept autres sont
  mesurés sur les pièces réelles du maillage et posés dans la scène d'ajustement — voir ses
  commentaires. C'est le défaut qui a coûté une partie entière sur la coque C.
- **Aucune tangente** (`POSITION`, `NORMAL`, `TEXCOORD_0` seulement) alors que quatre matériaux
  portent une `normalTexture`. Godot les génère à l'import ; à surveiller si le relief paraît plat.
- **Aucun LOD, aucune collision.** La hitbox vient des Resources de gameplay (`ADR-0034`), donc ce
  n'est pas bloquant ; les 406 maillages, eux, sont 406 instances par vaisseau.

### Ce qui est conforme sans négociation

| Cote | Modèle | × 0,19501 | Contrat `ADR-0008` | Écart |
|---|---|---|---|---|
| Longueur | 12,615 m | **2,4600** | 2,46 | 0 % |
| Envergure | 8,899 m | **1,7354** | 1,75 | **−0,84 %** |
| Hauteur | 3,540 m | **0,6903** | ≤ 0,72 | sous plafond |

Palette : blanc cassé, bleu profond, or, rouge — c'est la palette **Helios Vanguard** de la charte,
que la planche reprend d'elle-même. Aucune retouche n'a été nécessaire.

## Les cartes de surface ont été RÉÉCRITES par le projet (2026-09-06)

L'opérateur, après l'avoir vue en jeu : « *je trouve le D très bien mais il lui manque les
textures pour être aussi beau que le B* ». Mesuré, il avait raison sur le fond et le remède
n'était pas celui qu'on croit.

**Les six cartes livrées étaient des aplats.** L'albédo modulait de ±2,3 %, la rugosité de ±5 %,
et la normale de **±2 sur 255** — branchée de surcroît à une force de 0,22. Trois à dix fois sous
le seuil auquel un détail existe dans ce jeu.

**Et la réponse n'était pas plus de texels.** Densité UV mesurée sur le maillage : **0,831
tuile/m**, soit une tuile pour 1,20 m de modèle — 0,235 m en jeu, c'est-à-dire **11 pixels à
l'écran** à 45,8 px/m. Un damier fin y serait sous-pixel quelle que soit la résolution. La
résolution reste donc à **512**, où elle est déjà sur-échantillonnée quarante fois.

Ce qui a changé, c'est le **contenu** : une tôle par tuile, sa rainure de joint sur le bord (donc
raccord automatique), un liseré clair en dedans, une rangée de rivets, un grain brossé. La hauteur
porte tout ; la normale s'en **dérive** (`ADR-0013`).

| | avant | après |
|---|---|---|
| amplitude de l'albédo | 12 niveaux | **73** |
| amplitude de la normale | 4 niveaux | **245** |
| force de la normale | 0,22 | **0,85** |
| largeur de la rainure | 1 % de la tuile (0,11 px) | **4,2 % (0,46 px en jeu, 2 px au bestiaire)** |

⚠️ **Ce qu'une feuille tuilée ne donnera JAMAIS**, et la comparaison au bestiaire le montre :
l'usure PLACÉE et les décalcomanies. La `specter_9_b` porte un atlas peint de 2048 où les traînées
de crasse et les marquages sont posés là où la coque les veut ; une tuile qui se répète ne peut
que régulariser. La D lit désormais comme un appareil **neuf et propre**, la B comme un appareil
**usé**. **C'est fait depuis `BRIEF-0102`** : les 406 pièces sont dépliées dans un atlas unique de 2048²,
cuit et câblé (`resources/player/hull_detail_specter_9_d.tres`). La feuille tuilée décrite plus
haut ne sert plus ; ses six cartes ont été retirées du `.glb`. Densité obtenue : **78,1 texels/m**
sur la peau — 5,4 fois plus grossier que la feuille qu'il remplace, et c'est le prix de
l'ADRESSABILITÉ. Reste à **peindre** dessus : coulures, matricule 09, insignes.

⚠️ **La géométrie n'a pas bougé** : 413 nœuds, 406 maillages, 49 116 triangles, identiques au
fichier livré. Seules les cartes changent.

## Reconstruire

```sh
blender-aegis -b -noaudio -t 1 --python scripts/build.py          # écrase le .blend
blender-aegis -b -noaudio -t 1 --python scripts/export_asset.py   # écrit exports/spectre9_d.glb
blender-aegis -b -noaudio -t 1 --python scripts/verify.py
```

⚠️ **`build.py` REMPLACE le `.blend`.** Toute retouche faite à la main dans Blender est perdue au
prochain build. C'est aussi ce qui explique que le fichier livré ne soit pas celui que le script
rend : il a pu être retouché après coup, et on ne peut pas le prouver dans un sens ou dans l'autre.

Le dossier `reports/` est celui de l'auteur, conservé tel quel : `verification.json` (241 images
comparées après réimport, erreur max 4,8e-07), `portability.json` (import Godot 4.7.2), et
l'inventaire sha256. Ses chiffres décrivent **son** fichier, pas un rejeu.
