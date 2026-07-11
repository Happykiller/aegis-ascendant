# Composition des couches de parallaxe spatiale

- **Brief** : `docs/forge/briefs/BRIEF-0015-space-parallax-backgrounds.md`
- **Format source** : SVG panoramique 2048 × 1024

| Ordre | Couche | Facteur de déplacement suggéré | Opacité de départ |
|---:|---|---:|---:|
| 1 | Distant stars | 0,05 | 1,00 |
| 2 | Nebula | 0,10 | 0,70 |
| 3 | Planet | 0,16 | 0,85 |
| 4 | Distant fleet | 0,24 | 0,75 |
| 5 | Mid cruisers | 0,42 | 0,90 |
| 6 | Foreground debris | 0,72 | 0,85 |

## Règles de composition

- Conserver le tiers central moins dense que les bords.
- Ne pas augmenter les étoiles cyan au point de les confondre avec les tirs alliés.
- Désaturer davantage la planète pendant les séquences chargées en VFX.
- Masquer temporairement les croiseurs si leur silhouette passe sous un boss ou un objectif.
- Les débris ne doivent jamais employer le corail réservé aux projectiles ennemis.
- Les facteurs indiquent un rapport relatif, à adapter à la caméra et au cadrage final.
