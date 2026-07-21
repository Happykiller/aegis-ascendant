# BRIEF-0033 — Specter-9 : fuselage et pièces mobiles

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-21

## Objectif

Le Specter-9 lit comme une **plaque delta plate**. Lui donner du **volume et de la structure
verticale**, et sortir de sa coque les **pièces destinées à bouger** (volets, tuyères).

Ce n'est pas une refonte d'identité : delta à ailes basses, verrière axiale, deux réacteurs. Les
dimensions de gameplay ne changent pas. Ce qui change, c'est **l'épaisseur, la superposition des
volumes et la présence verticale**.

## Contexte

| Mesure | Specter-9 actuel | Planche visée |
|---|---|---|
| Rapport longueur / envergure | **1,41** | 1,36 — *déjà bon, ne pas y toucher* |
| **Hauteur / longueur** | **21 %** | **28 %** ← l'écart réel |
| Structure verticale | **aucune** | dérives, rails de bout d'aile |
| Nacelles moteur | noyées dans l'aile | volumes distincts, lisibles |
| Nez | court, dans le prolongement de l'aile | long, effilé, verrière en retrait |

Le rapport de proportions est donc déjà juste : **le problème est le profil**, pas le plan. Vue de
dessus la coque est correcte ; vue de trois quarts — c'est-à-dire sur l'écran d'accueil, en gros
plan — elle n'a aucune épaisseur.

**Lire d'abord** : `ADR-0013` (textures), `ADR-0011` (budgets), `ADR-0008` (pipeline), puis
`docs/forge/CHARTE_CREATIVE.md`.

## ⚠️ Référence de design et limite IP — lire en entier

**Référence** : `assets/reference/inspiration/reference_specter_9_design_sheet.png`. **Lis-la avec
`Read`.** Elle est riche : vues orthogonales, profil, réacteurs, verrière, et une rangée
« ANIMATIONS CLÉS » qui spécifie exactement les états à servir.

Cette planche est dans **`inspiration/`**, pas dans `concepts/` : elle est **d'origine tierce et
sensible côté IP**. Elle porte la mention « VF-class » et une silhouette de chasseur transformable
sous licence. ADR-0009 l'autorise comme **cible d'intention** (projet personnel, risque assumé) et
la DA §13 la classe explicitement « *silhouette à réinterpréter* ».

**Ce qu'on prend** : l'épaisseur et la superposition du profil, les nacelles comme volumes propres,
le nez long à verrière en retrait, la présence verticale, la densité de panneautage, le vocabulaire
d'animation.

**Ce qu'on ne prend PAS** — ce sont les trois traits qui font reconnaître la licence :

1. **Les deux dérives inclinées en V** à l'arrière. Remplacer la présence verticale par des **rails
   verticaux de bout d'aile** (la planche en montre en vue de face) plus une **arête dorsale basse**.
2. La **livrée tricolore** blanc / bleu / **rouge vif** en bandes. La palette du kit reste seule
   maîtresse : blanc cassé, bleu profond, or, rouge **de sécurité uniquement**, en marquages.
3. Le **badge numéroté** sur la dérive. Aucun chiffre, aucun texte.

Un doute se tranche du côté de l'original, pas de la ressemblance.

## Contraintes

- **Dimensions X/Z : INCHANGÉES**, **1,75 × 2,46 m à ±3 %**. Contrat de gameplay — hitbox,
  télégraphes et lisibilité en dépendent.
- **Hauteur Y : c'est LA marge.** De 0,52 m à **0,62-0,68 m** (25-28 % de la longueur). Cela dépasse
  la fourchette indicative d'ADR-0008 (15-25 %) : **autorisé ici**, et à consigner dans le rapport.
  ⚠️ **Contrepartie à vérifier** : la caméra de jeu regarde à 20° de la verticale. Une coque plus
  épaisse peut y lire comme un pâté au lieu d'un chasseur. **Juge la vue « game » de
  `render-hull.py` avant de conclure** — si l'épaisseur nuit à la lecture de dessus, redescends et
  dis-le.
- **Budget : 60 000 triangles** (ADR-0011). Actuel : 29 716. Plafond, pas objectif.
- Palette inchangée, 7 matériaux, `MATERIAL_ORDER` intact.
- **UV** : `ak.box_project_uv()` reste appelé (l. 1290), l'échelle actuelle est validée au rendu.
- **Déterminisme** : passer par **`./scripts/build-hull.sh --check specter_9`**, qui force `-t 1`.
  Sans ce drapeau les tangentes divergent d'une exécution à l'autre — voir
  `.claude/resources/howto-determinisme-des-coques.md`.

## Pièces mobiles — le kit sait le faire depuis aujourd'hui

`ak.moving_part(nom, bmesh, pivot)` + `ak.export_hull(..., parts=[...])` exportent des **nœuds glTF
séparés**, chacun avec son origine sur son point d'articulation. Exemple complet et vérifié :
`tools/blender/test_moving_parts.py`.

⚠️ **Le pivot est toute la primitive.** Une pièce dont l'origine reste à zéro décrit un arc de cercle
autour du nez au lieu de pivoter sur sa charnière — et ça ne se voit qu'une fois animée.

Pièces demandées :

| Nom | Rôle | Pivot |
|---|---|---|
| `Flap_L` / `Flap_R` | volet de bord de fuite, un par aile | la **ligne de charnière**, au bord de fuite de l'aile |
| `Nozzle_L` / `Nozzle_R` | couronne de pétales de tuyère, qui s'ouvre | le **centre du col** de la tuyère |

- Les volets battent autour de leur axe **transversal** (X d'auteur) : ±12° suffisent, prévois le
  dégagement pour qu'ils ne traversent pas l'aile.
- Les pétales de tuyère seront **mis à l'échelle** à l'accélération, pas tournés : modèle-les au
  repos **fermés**, et laisse assez de longueur pour que l'ouverture se lise.
- Au repos, chaque pièce doit être **exactement à sa place** : c'est le `.glb` non animé qui fait foi
  pour le rendu de contrôle.
- `Engine_L` / `Engine_R` (points d'attache des traînées) **restent** et doivent tomber **derrière**
  les pétales, sinon la plume sort du milieu de la tuyère.

## Travail demandé, par ordre de rendement décroissant

1. **Épaissir et superposer le profil.** C'est le seul levier qui change la lecture de volume :
   arête dorsale du nez à la poupe, ventre distinct de l'extrados, nacelles qui saillent sous l'aile.
2. **Nacelles moteur en volumes propres**, avec col, pétales et anneaux — la planche leur consacre un
   encart entier.
3. **Nez plus long et effilé**, verrière en retrait et **encadrée en relief** (pas un ovale posé à plat).
4. **Présence verticale** : rails de bout d'aile + arête dorsale basse (voir la limite IP ci-dessus).
5. **Pièces mobiles** (tableau ci-dessus).
6. **Densité de panneautage** : la planche montre des dizaines de panneaux. Double `inset_panel`
   emboîté, technique déjà prouvée dans `build_crescent_interceptor.py:597-598`.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_specter_9.py` | script retravaillé |
| `assets/imported/models/ships/specter_9.glb` | coque + 4 pièces mobiles (LFS) |
| `docs/forge/output/BRIEF-0033-report.md` | mesures réelles, ce que le rendu montre, limites |

## Critères d'acceptation

- [ ] `./scripts/build-hull.sh --check specter_9` : **déterminisme OK**
- [ ] Bbox X/Z inchangée à ±3 % (1,75 × 2,46) ; hauteur **0,62-0,68 m**
- [ ] ≤ 60 000 triangles ; `TEXCOORD_0` et `TANGENT` présents
- [ ] Les 10 points d'attache existants **conservés** aux mêmes rôles
- [ ] `Flap_L/R` et `Nozzle_L/R` sont des **nœuds séparés**, origine sur leur articulation
- [ ] **Rendu et regardé** (ADR-0006) : `blender45 -b -P tools/render-hull.py -- <glb>`.
      Critère : sur la vue « profil » on doit voir un appareil **superposé**, pas une plaque ;
      sur la vue « game », la silhouette doit rester **lisible de dessus**.
- [ ] Aucun des trois traits sous licence (dérives en V, livrée tricolore, badge numéroté)
- [ ] Provenance : la ligne `specter_9_hull` **réécrite**, pas dupliquée

## Hors périmètre

Ne pas toucher au code gameplay, aux `.tscn`, aux `.gd`, aux tests, ni aux autres coques.
**Ne pas modifier `aegis_kit.py`** — il vient d'être étendu pour ce brief ; s'il manque encore
quelque chose, le **signaler dans le rapport**. Ne pas écrire l'animation : elle est faite côté
Godot. Ne pas générer de texture. Pas de `.blend` versionné.
