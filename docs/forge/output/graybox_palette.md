# Palette colorimétrique normative — Graybox

- **Statut** : normatif (référence citée par la charte créative §3)
- **Brief** : `docs/forge/briefs/BRIEF-0002-graybox-palette.md`
- **Produit par** : asset-forge
- **Date** : 2026-07-11
- **Portée** : phase graybox (primitives Godot + `StandardMaterial3D` émissifs). Les couleurs de
  bonus/pickups sont hors périmètre (brief dédié à venir).

## 1. Palette normative

Toutes les valeurs sont en **hex sRGB**. « Énergie » = valeur suggérée pour
`emission_energy_multiplier` (échelle 0–4). « Contraste » = ratio WCAG 2.1 de la couleur émissive
(ou de l'albedo si non émissif) contre le fond `#070A12`.

| Élément | Hex albedo | Hex émissif | Énergie (0–4) | Rôle | Contraste vs fond |
|---|---|---|---|---|---|
| Fond spatial | `#070A12` | — | 0.0 | plancher de luminance de la scène | — (référence) |
| Sol / repères de bounds | `#1C2B5E` | `#3FD9E8` | 0.3 | cadre de jeu discret, non distrayant | 11.59:1 (émissif, atténué par l'énergie 0.3) |
| Chasseur joueur (Specter-9) | `#EDEAE3` | `#3FD9E8` | 1.2 | ancre visuelle alliée, toujours localisable | albedo 16.47:1 / émissif 11.59:1 |
| Needle Scout (ennemi) | `#24252B` | `#D93D9C` | 1.0 | menace lisible mais moins saillante que ses tirs | émissif 4.80:1 (albedo 1.30:1, voulu sombre) |
| Projectile allié | `#3FD9E8` | `#3FD9E8` | 2.0 | feedback de tir, ne masque jamais le danger | 11.59:1 |
| Projectile ennemi — cœur | `#FFE9D2` | `#FFE9D2` | 4.0 | **élément le plus saillant de l'écran** | **16.81:1** |
| Projectile ennemi — halo | `#FF5A3D` | `#FF5A3D` | 2.5 | signature « danger » persistante (corail) | 6.39:1 |
| Flash d'impact | `#000000` | `#D9E6F2` | 3.0 | ponctuation brève (< 120 ms), blanc froid | 15.60:1 |
| Texte HUD provisoire | `#EDEAE3` (accents `#3FD9E8`) | — | — (UI, `Label`) | lecture instantanée du score/état | 16.47:1 (AAA ; accents 11.59:1) |

### Transposition `StandardMaterial3D`

- `albedo_color` = hex albedo ; `emission_enabled = true` ; `emission` = hex émissif ;
  `emission_energy_multiplier` = énergie.
- Projectile ennemi = **deux sphères** : cœur (rayon r, énergie 4.0) + halo (rayon ~1.8 r,
  matériau transparent additif, énergie 2.5). Si le budget graybox impose une seule sphère,
  utiliser le matériau **halo** (`#FF5A3D`, énergie 3.0) — jamais le cœur seul (confusion
  possible avec le flash d'impact, voir §5).
- Fond : `Environment.background_color = #070A12`, sans brouillard clair ni glow global qui
  remonterait le plancher de luminance.

## 2. Hiérarchie de saillance (Pilier B — identification < 200 ms)

Chaque catégorie occupe un étage distinct d'énergie émissive **et** de luminance, du plus
discret au plus criant :

| Étage | Élément | Énergie | Luminance relative WCAG |
|---|---|---|---|
| 0 | Fond spatial | 0.0 | 0.003 |
| 1 | Repères de bounds | 0.3 | 0.565 (× énergie 0.3) |
| 2 | Needle Scout | 1.0 | 0.205 |
| 3 | Joueur | 1.2 | 0.565 |
| 4 | Projectile allié | 2.0 | 0.565 |
| 5 | Halo projectile ennemi | 2.5 | 0.289 |
| 6 | Flash d'impact | 3.0 | 0.778 |
| 7 | **Cœur projectile ennemi** | **4.0** | **0.842** |

Le cœur du projectile ennemi cumule la luminance la plus haute **et** l'énergie émissive
maximale : c'est mathématiquement l'élément le plus lumineux de la scène, conformément à la
spec §11.2 (« projectiles dangereux dotés d'un contour ou halo constant ») et §21.4.

## 3. Discrimination allié / ennemi (y compris en périphérie)

Trois canaux redondants, jamais la teinte seule :

1. **Teinte** : axe froid (cyan `#3FD9E8`) vs axe chaud (corail `#FF5A3D` + blanc chaud `#FFE9D2`).
2. **Luminance** : cœur ennemi 0.842 vs allié 0.565 (ratio 1.45:1) ; en énergie rendue,
   l'écart est doublé (4.0 vs 2.0).
3. **Structure** : seul le projectile ennemi porte un halo (cœur + couronne), lisible même
   flou en périphérie de vision où la discrimination chromatique chute.

## 4. Vérification daltonisme

- **Méthode** : simulation de **deutéranopie sévérité 1.0** (matrice de Machado, Oliveira &
  Fernandes 2009, appliquée en RGB linéaire, aller-retour gamma sRGB 2.4), puis recalcul des
  ratios de contraste WCAG 2.1 sur les couleurs simulées. Script : calcul `python3`
  (luminance relative WCAG : 0.2126 R + 0.7152 G + 0.0722 B en linéaire).

| Élément | Hex réel | Hex simulé (deutan) | Contraste vs fond (deutan) |
|---|---|---|---|
| Projectile ennemi — cœur | `#FFE9D2` | `#F6EED2` | 17.04:1 |
| Projectile ennemi — halo | `#FF5A3D` | `#B2A037` | 7.52:1 |
| Projectile allié | `#3FD9E8` | `#B0BFE9` | 10.81:1 |
| Flash d'impact | `#D9E6F2` | `#DEE3F2` | 15.43:1 |
| Joueur (émissif) | `#3FD9E8` | `#B0BFE9` | 10.81:1 |
| Needle Scout (émissif) | `#D93D9C` | `#818798` | 5.51:1 |
| Texte HUD | `#EDEAE3` | `#EDEBE3` | 16.58:1 |

- **Verdict : PASS.** Sous deutéranopie, l'opposition allié/ennemi bascule sur l'axe
  bleu–jaune (préservé chez les deutans) : allié → bleu pervenche `#B0BFE9`, halo ennemi →
  or-olive `#B2A037` ; la hiérarchie de luminance est intégralement conservée (cœur ennemi
  0.854 > flash 0.769 > allié 0.524 > halo ennemi 0.349 > scout 0.243 > fond 0.003) et le
  cœur ennemi reste l'élément le plus contrasté de l'écran (17.04:1). Le canal structurel
  (halo) est indépendant de la couleur. La protanopie n'a pas été vérifiée (le brief exige
  la deutéranopie au minimum) ; le corail `#FF5A3D` perdra davantage de luminance chez les
  protans — voir §5.

## 5. Justifications et notes

- **Fond `#070A12`** : noir bleuté (et non `#000000`) pour garder une profondeur « espace »
  sans écraser le tone mapping ; luminance 0.003, soit 6× plus sombre que l'élément actif le
  plus faible. Tout élément actif contraste à ≥ 4.8:1.
- **Repères de bounds** : albedo bleu profond charte `#1C2B5E` + filet cyan à énergie 0.3 —
  visibles pour cadrer l'espace de jeu (24 × 14 unités), assez ternes pour ne jamais
  concurrencer un projectile.
- **Joueur** : coque blanc cassé charte + lignes cyan charte, l'entité alliée la plus
  lumineuse hors projectiles ; le blanc `#EDEAE3` le distingue du Needle Scout anthracite
  même à silhouette égale (prismes graybox).
- **Needle Scout** : coque anthracite charte, feux **magenta** `#D93D9C` (canal « corps
  ennemis ») distincts du canal « tirs ennemis » (corail/blanc chaud) — on sait en < 200 ms
  si l'objet rose/chaud est une source (magenta, énergie 1) ou un danger direct (corail,
  énergie 2.5–4).
- **Projectile ennemi cœur + halo** : applique littéralement la règle charte §3 « toujours
  cœur lumineux + halo contrasté ». Le blanc chaud du cœur maximise la luminance ; le corail
  du halo porte l'identité « danger » et la persistance rétinienne en périphérie.
- **Flash d'impact blanc *froid* `#D9E6F2`** : contraste chromatique délibéré avec le cœur
  ennemi blanc *chaud* `#FFE9D2`. Leur écart de luminance est faible (1.08:1) : la
  distinction repose sur (a) l'axe chaud/froid — préservé sous deutéranopie (`#F6EED2` vs
  `#DEE3F2`), (b) la durée (flash < 120 ms vs projectile persistant), (c) le halo corail
  absent du flash. C'est la raison pour laquelle un projectile ennemi mono-sphère doit
  utiliser le matériau halo, pas le cœur.
- **Texte HUD** : blanc cassé charte sur fond spatial = 16.47:1 (WCAG AAA, seuil 7:1
  largement dépassé) ; accents cyan 11.59:1.

### Limites connues

- Les ratios WCAG sont calculés sur les hex sRGB **avant** tone mapping/glow Godot ; l'énergie
  émissive et le `Environment` (ACES/AgX, glow) moduleront la luminance perçue. La hiérarchie
  d'énergie (§2) est conçue pour que l'ordre de saillance survive au tone mapping, mais une
  vérification par capture d'écran en Phase 1 reste nécessaire.
- Contraste cœur ennemi / explosions : les VFX d'explosion n'existent pas encore ; la garantie
  actuelle est chromatique (chaud vs froid) et structurelle (halo). Le brief des VFX
  d'explosion devra imposer une dominante **froide ou désaturée** aux fumées/flashs pour
  préserver la saillance du corail.
- Protanopie et tritanopie non simulées (hors exigence minimale du brief).

### Suggestions

- Réserver l'**or charte `#E4B54A`** aux futurs projectiles alliés secondaires (missiles) :
  il reste dans le canal allié tout en étant discriminable du cyan.
- Vérifier en Phase 1 que le glow ne fusionne pas cœur et halo ennemis en une tache uniforme ;
  au besoin, baisser l'énergie du halo à 2.0.
