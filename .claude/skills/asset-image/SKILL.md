---
name: asset-image
description: Rédige des prompts d'images autosuffisants pour Aegis Ascendant (textures, planches, décors) et dit exactement comment nommer le livrable, où le déposer, quoi lancer ensuite et quelle ligne de provenance ajouter. Déclencher avec /asset-image.
trigger: /asset-image
---

# /asset-image — le prompt, le nom, le chemin, la suite

Ce skill existe parce que l'opérateur génère les images **hors du dépôt**, dans une autre fenêtre.
Un prompt qui suppose du contexte est donc un prompt raté : il faut que le bloc rendu se colle tel
quel, et qu'au retour on sache sans réfléchir où poser le fichier et quoi lancer.

Il existe aussi parce que le projet a **déjà payé** les mêmes pièges de génération : le damier peint
à la place de la transparence (BRIEF-0028), la fausse normal map, la couture invisible en preview et
évidente en jeu.

**Verrous levés (ADR-0013)** : plus aucun interdit sur les textures — jeux dédiés à une unité,
relief, couleur, décalques. Ce qui suit n'est pas de la réglementation, c'est ce qui marche.

---

## 1. Les trois choses qu'un générateur ne sait PAS faire

Ne jamais les demander. Les contourner.

| Ce qu'on serait tenté de demander | Ce qui arrive | Ce qu'on demande à la place |
|---|---|---|
| « une normal map » | une image violette **qui y ressemble**, aux gradients faux → relief éclairé à l'envers, et ça *a l'air* correct | une **hauteur en niveaux de gris** (clair = saillant). `tools/derive-maps.py` en dérive normale, rugosité, AO |
| « fond transparent, PNG alpha » | un **damier peint** dans une image RGB opaque | un **fond noir pur** (objet lumineux) ou **uni très clair** (objet opaque), puis `tools/bg-key-alpha.py` |
| « seamless, sans couture » | souvent une couture quand même, invisible sur l'image seule | on demande le seamless **et** on le **mesure** : `derive-maps.py --check-tiling` |
| « en 2048 × 2048 » | un **1024 agrandi** : du détail inventé par l'interpolation, jamais du détail en plus | son **format natif** : `1024×1024`, `1536×1024` ou `1024×1536`, et on ne redimensionne pas |

Corollaire : **une texture PBR se génère en une seule carte** (la hauteur), pas en quatre. Demander
quatre cartes « cohérentes entre elles » à un générateur donne quatre images qui ne le sont pas.

---

## 2. Écrire le prompt

Règles tirées des prompts qui ont fonctionné (`docs/forge/output/*_generation_prompt.md`) :

- **Les couleurs en mots, jamais en hexadécimal.** « blanc cassé », « bleu profond », « cyan
  électrique » — un code hexa est ignoré ou mal interprété.
- **Dire le cadrage, pas seulement le sujet.** Pour une texture : « vue orthogonale de dessus,
  éclairage neutre et plat, aucune ombre portée, aucune perspective, aucun vignettage ». Sans ça on
  reçoit une jolie photo d'un panneau, inutilisable en tuile.
- **Un bloc « Éviter absolument »**, explicite et long. C'est lui qui porte le résultat.
  Toujours y mettre : texte, lettres, chiffres, logo, filigrane, signature, nom de marque ou
  d'artiste. Pour une texture, y ajouter : perspective, ombre portée, vignettage, bords assombris,
  cadre, objet isolé au centre.
- **Demander le format natif du générateur**, jamais une taille inventée. Les formats sont
  `1024×1024`, `1536×1024` et `1024×1536` — rien d'autre. **Preuve dans le dépôt** : toutes les
  images réellement livrées par cette route sont en `1254×1254` (`citadel_*_height.png`,
  `planet_hero.png`, les six textures du Leviathan) ou `1536×1024` (`nebula_monument_*.png`). Les
  seuls fichiers en 2048 (`assets/source/textures/hull/*_seamless_2048.png`) viennent d'avant ce
  pipeline. ⚠️ **Et ça n'a aucune importance** : le rendu final passe par le post-process rétro à
  **960×540**. Une tuile de 1024 sur 5,5 m donne 186 px/m, bien plus que ce que l'écran montre —
  viser 2048 coûte du poids pour un détail que le filtre efface. *Coût de l'oubli : dix blocs de
  prompt à reprendre, relevés par l'opérateur (23/07/2026).*
- **Dire l'échelle réelle.** « chaque dalle mesure environ 1,5 mètre » cadre la densité mieux que
  n'importe quel adjectif. Une feuille calée sur un chasseur de 2 m lit comme du bruit sur une
  forteresse de 20 m — c'est le défaut n°1.
- **Le gris n'est pas un dogme, c'est le contrat d'entrée de `derive-maps.py`.** Une hauteur et un
  masque sont des champs scalaires, et l'outil **avertit** si l'image reçue est colorée — c'est le
  symptôme d'un générateur qui a rendu *une jolie image* au lieu de la carte demandée. Mais
  **ADR-0013 §3 autorise la couleur quand elle est motivée** (cristal, décalques, croûte émissive),
  et le projet ne s'en est longtemps jamais servi. Demander de la couleur là où elle sert, du gris
  partout ailleurs — et le **vérifier** : échantillonner les teintes livrées et refuser toute dérive
  hors palette (le cyan et le corail sont réservés au gameplay, DA §6).
- **IP** : création originale. Ne jamais citer une licence, un artiste vivant, un titre existant
  (ADR-0009). On transpose une intention, on ne décalque pas.
- **Palette** : `assets/reference/DA.md` §5 fait foi. Le cyan allié et le corail ennemi sont
  **réservés au gameplay** — un décor ou une texture qui les emploie vole leur lisibilité aux
  projectiles (DA §6).

---

## 3. Où va le livrable

La carte complète est dans `assets/README.md`. Une seule question tranche : **est-ce que ça finit
dans le jeu ?**

| Nature | Chemin |
|---|---|
| Image brute rendue par le générateur | `assets/source/<famille>/…` — **toujours**, même si elle sert telle quelle |
| Fichier réellement chargé par le moteur | `assets/imported/<famille>/…` |
| Planche qu'on regarde et qui n'entre jamais dans le jeu | `assets/reference/concepts/` (nos planches) ou `assets/reference/inspiration/` (tierces) |

**La source se garde toujours**, même quand la dérivée est seule utilisée : c'est elle qui permet de
régénérer autrement sans repasser par le générateur.

### Nommage

- Source : `<sujet>_<rôle>_<taille>.png` → `citadel_panels_height_2048.png`
- Dérivées (produites par l'outil, jamais générées) : `<sujet>_<rôle>_nrm.png`, `_rough.png`,
  `_ao.png`, `_mul.png`
- Minuscules, `snake_case`, pas d'accent, pas d'espace.

---

## 4. Le format de sortie — un bloc par image

Chaque image demandée produit **exactement** ce bloc. Rien à aller chercher ailleurs.

```
### <n>/<total> — <nom_du_fichier_sans_extension>

PROMPT — à coller tel quel :
────────────────────────────────────────────────────────────
<le prompt complet, en français, sujet + cadrage + échelle
 réelle + palette en mots, puis « Éviter absolument : … »>
────────────────────────────────────────────────────────────

FORMAT      : PNG, 1024 x 1024 (carre natif du generateur), niveaux de gris
DÉPOSER     : assets/source/textures/citadel/citadel_panels_height_2048.png
ENSUITE     : python3 tools/derive-maps.py \
                assets/source/textures/citadel/citadel_panels_height_2048.png \
                --out assets/imported/textures/citadel --mul \
                --preview /tmp/citadel_panels.png
VÉRIFIER    : la ligne « tuilage » doit dire OK ; ouvrir la preview
              (le quart haut-gauche montre 2x2 tuiles — la couture s'y voit)
PROVENANCE  : <ligne CSV prête à coller dans assets/licenses/ASSET_PROVENANCE.csv>
```

La ligne de provenance suit l'en-tête du CSV
(`asset_id,file_path,asset_type,source_tool,source_url,author,license,generated_date,prompt_file,modified_by,notes`).
Pour une image générée : `source_tool` = l'outil réel, `author` = `tiers (genere IA)`,
`license` = `proprietary-internal`. Une ligne pour la **source**, une pour chaque **dérivée**
réellement versionnée.

---

## 5. Après le retour de l'opérateur

1. **Regarder.** Un asset non rendu et non regardé n'est pas validé (ADR-0006). La preview de
   `derive-maps.py` d'abord, puis **en jeu** : le rendu studio flatte, et le post-process rétro
   (960×540 + scanlines) écrase le détail fin.
2. **Mesurer le tuilage**, ne pas le supposer. `--fix-tiling` est un rattrapage qui duplique
   visiblement le motif sur la bande — il sauve une image presque bonne, pas une image mal pensée.
3. **Provenance** : la ligne est ajoutée avant l'intégration, pas après (spec §24.7).
4. **Coût** : une texture n'est pas gratuite. Temps GPU par image avant/après, jamais le FPS
   (`.claude/resources/howto-mesurer-la-perf.md`).
5. Si l'image ne convient pas, **corriger le prompt, pas l'image** — et redonner le bloc complet.
   Un prompt rafistolé de mémoire à la troisième itération est un prompt perdu.
