# BRIEF-0034 — Specter-9 : changer le PLAN, pas le profil

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-21

## Objectif

**Abandonner le delta.** Redistribuer les masses du chasseur pour qu'il lise comme la planche :
**fuselage central porteur** sur toute la longueur, **deux nacelles longues qui le flanquent**, et
des ailes réduites à des **lames fines en flèche**. Plus **deux dérives inclinées** à l'arrière.

Le travail de BRIEF-0033 sur le profil, les nacelles, le panneautage et les pièces mobiles est
**acquis et conservé**. Ce qui change, c'est le **plan** — la vue de dessus.

## Contexte — pourquoi ce brief existe

BRIEF-0033 a demandé explicitement de *conserver le delta* et affirmait que « le problème est le
profil, pas le plan ». **C'était faux, et c'est une erreur du concepteur, pas de la forge.** Le
raisonnement s'appuyait sur le rapport de la boîte englobante (1,41 contre 1,36 sur la planche) —
une statistique vide : elle mesure la boîte, pas la répartition des masses dedans.

Comparaison faite ensuite, vue de dessus contre vue de dessus :

| | Planche | Modèle actuel |
|---|---|---|
| Masse dominante | **fuselage + deux nacelles** | **l'aile** |
| Part visuelle de l'aile | ~30 % | ~70 % |
| Fuselage | volume porteur, pleine longueur | bande fine posée sur le delta |
| Dérives | **deux, inclinées vers l'extérieur** | aucune |

**Lis `ADR-0014` avant tout** : il acte cette décision et sa portée exacte.

## Ce qui est repris de la planche — et ce qui ne l'est pas

**Référence** : `assets/reference/inspiration/reference_specter_9_design_sheet.png`, vues
« VUE DESSUS », « VUE DESSOUS », « VUE FACE » et « VUE PROFIL DROIT ». **Lis-la avec `Read`.**

**Repris (ADR-0014)** : le **plan** et les **deux dérives inclinées**. Le brief précédent les
excluait ; cette exclusion est levée.

**Toujours exclu** :
- la **livrée tricolore** à bandes rouges — la palette du kit reste seule maîtresse (blanc cassé,
  bleu profond, or, rouge de sécurité en marquages seulement). Un appareil tricolore serait un corps
  étranger au milieu d'une flotte ivoire et bleue, indépendamment de toute autre considération ;
- tout **texte, chiffre, badge numéroté, logo, insigne**.

## Le plan demandé, concrètement

Vu de dessus, en partant de l'axe :

1. **Fuselage central** — un volume porteur qui court du nez à la poupe, large d'environ **0,32 à
   0,40 m** (18-23 % de l'envergure). Il porte la verrière, en avant du tiers médian. C'est LA pièce
   qui manque aujourd'hui : le fuselage actuel est une bande décorative sur un delta.
2. **Deux nacelles longues** flanquant le fuselage, séparées de lui par une rainure visible, courant
   sur **60 à 75 % de la longueur**, se terminant par les tuyères existantes.
3. **Ailes en lames** — **l'envergure ne change pas** (les marqueurs `Muzzle_Tip_L/R` restent à
   |x| = 0,80), mais la **corde s'effondre** : des lames fines en flèche accrochées au flanc des
   nacelles, pas un aplat triangulaire qui remplit tout l'arrière. C'est le geste central du brief.
4. **Deux dérives inclinées** vers l'extérieur, en arrière, sur le dessus des nacelles.
5. **Nez long et pointu**, nettement en avant de l'emplanture d'aile.

## Contraintes

- **Dimensions X/Z : INCHANGÉES**, **1,75 × 2,46 m à ±3 %**. Le plan change **à l'intérieur** de la
  boîte. C'est précisément le point : deux silhouettes sans rapport partagent la même boîte.
- **Hauteur Y** : **0,62-0,72 m**. Les dérives montent, mais restent **étroites** — ADR-0011 :
  ce qu'on ajoute au-dessus se paie en vue de dessus, ce qu'on ajoute en dessous est gratuit.
- ⚠️ **LE RISQUE DE CE BRIEF, à vérifier et à me dire franchement.** Un appareil à fuselage porteur
  lit **plus étroit** de dessus qu'un delta. Or la caméra de jeu regarde à 20° de la verticale et la
  DA §6 exige que le joueur soit identifiable en moins de 200 ms. **Juge la vue « game » de
  `render-hull.py`** : si la silhouette devient une flèche maigre difficile à suivre, dis-le et
  propose l'arbitrage (lames plus larges ? nacelles plus écartées ?). Je préfère un compromis assumé
  à une fidélité qui casse la lisibilité.
- **Budget : 60 000 triangles.** Actuel : 42 520.
- Palette inchangée, 7 matériaux, `MATERIAL_ORDER` intact. UV conservées.
- **Déterminisme** : passer par `./scripts/build-hull.sh --check specter_9`.

## Ce qui est conservé de BRIEF-0033 — ne pas régresser

- Les **4 pièces mobiles** `Flap_L/R`, `Nozzle_L/R`, nœuds séparés, origine sur l'articulation.
  Les volets migrent sur les nouvelles lames : **redonne-moi leur plafond de débattement mesuré**,
  `ShipFlight` est réglé à 11° sur un plafond de 13° et devra peut-être changer.
- Les **10 points d'attache** existants, aux mêmes rôles. `Engine_L/R` doivent rester **derrière**
  les pétales.
- La **densité de panneautage**, le **profil superposé**, les **nacelles en volumes propres**.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_specter_9.py` | script retravaillé |
| `assets/imported/models/ships/specter_9.glb` | coque + 4 pièces mobiles (LFS) |
| `docs/forge/output/BRIEF-0034-report.md` | mesures, rendu, **plafond de débattement des volets**, verdict de lisibilité en vue de jeu |

## Critères d'acceptation

- [ ] `./scripts/build-hull.sh --check specter_9` : déterminisme OK
- [ ] Bbox X/Z inchangée à ±3 % ; hauteur 0,62-0,72 m ; ≤ 60 000 triangles
- [ ] **Vue de dessus** : le fuselage et les nacelles dominent, l'aile ne remplit plus l'arrière
- [ ] Deux dérives inclinées présentes
- [ ] Aucune bande rouge de livrée, aucun chiffre, aucun texte
- [ ] 4 pièces mobiles et 10 points d'attache conservés
- [ ] **Rendu et regardé** (ADR-0006), avec une **planche de comparaison côte à côte** contre la vue
      de dessus de la planche, à la même hauteur. C'est la vérification qui manquait au brief
      précédent et qui lui a coûté sa reforge — je la veux dans le rapport.

## Hors périmètre

Ne pas toucher au code gameplay, aux `.tscn`, aux `.gd`, aux tests, ni aux autres coques.
Ne pas modifier `aegis_kit.py` — signaler les manques dans le rapport (les trois du BRIEF-0033 sont
notés, inutile de les répéter). Ne pas générer de texture. Pas de `.blend` versionné.
