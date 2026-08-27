---
titre: Lexique du genre — le vocabulaire, et ce qu'on en a
type: reference
statut: actif
maj: 2026-08-27
---

# Lexique du genre

Le shoot'em up a un vocabulaire **précis**, et l'ignorer coûte des tours de piste : deux personnes
qui disent « pattern » ou « rang » sans parler de la même chose ne s'en aperçoivent qu'au moment
d'intégrer.

Ces définitions viennent du glossaire de la Shmups Wiki. La **troisième colonne** dit si le concept
existe chez nous — c'est ce qui fait de cette page une **carte de couverture** plutôt qu'une
traduction.

## Esquive et mouvement

| Terme | Définition | Chez nous |
|---|---|---|
| **Micro-esquive** | enfiler précisément de petits interstices, par mouvements délicats | ✅ le mode d'esquive par défaut du jeu |
| **Macro-esquive** | lire tout l'écran pour trouver les grandes ouvertures, par grands déplacements | ⚠️ seulement face aux couronnes de la Choir Mine |
| **Streaming** | éviter des balles **visées** en bougeant le moins possible, pour concentrer le tir en un flux et libérer l'écran | ❌ sans objet : **aucune unité de vague ne tire visé** (voir [`11`](11-patterns-de-tir.md)) |
| **Restream** | ouvrir un trou dans ce flux : changement de direction sec, pause, retour | ❌ idem |
| **Point-blank** | coller un ennemi pour concentrer la puissance de feu, au risque de la collision | ⚠️ possible, **jamais mesuré** — le genre en fait un levier de score, pas nous |
| **Sealing** | entrer dans l'angle mort d'un ennemi pour l'empêcher de tirer | ❌ |
| **Safespot** | position où l'on est totalement à l'abri, par oubli ou par bug — « peut rendre une rencontre triviale » | ⚠️ jamais cherché. `RADIAL_PHASE = 0,5` en supprime une famille par construction |

## Ennemis et rencontres

| Terme | Définition | Chez nous |
|---|---|---|
| **Popcorn** / *zako* | ennemis faibles et nombreux, tués en quelques tirs | ✅ Choir Mine (12 PV), Leech Drone (10 PV) |
| **Mid-boss** | affrontement majeur au milieu d'une étape | ✅ le Choir Harvester, phase `MINI_BOSS` |
| **TLB** (*True Last Boss*) | boss caché, conditionné à une performance (sans mort, sans bombe, score seuil) | ❌ |
| **Loop** / *round* | reprise du jeu complet, plus dur, score conservé | ❌ — et hors périmètre (arc unique de 12–15 min) |

## Score

| Terme | Définition | Chez nous |
|---|---|---|
| **Chain / combo** | technique répétée qui augmente les points obtenus | ❌ |
| **Milking** | maximiser les points d'un ennemi (souvent un boss) en le **gardant en vie** | ❌ — et impossible : rien ne rapporte tant que la cible vit |
| **Tick points** | petit bonus constant quand un tir **touche** sans tuer | ❌ |
| **Graze** | frôler une balle sans la toucher, pour du score, des objets ou un ralentissement des balles | ❌ |
| **Bullet cancel** | condition qui **efface les balles à l'écran**, souvent avec du score ou des objets à la clé | ⚠️ **le mécanisme existe, sans le score** : `clear_team(ENEMY)` vide l'écran à la mort du joueur (`graybox_root.gd:961`), en garde-fou anti-mort-en-chaîne |
| **Rank** | difficulté qui suit la performance du joueur | ❌ — voir [`06`](06-score-et-rang.md) |
| **No-miss** | finir sans perdre une seule vie ; donne souvent un bonus | ❌ non détecté, non récompensé |
| **1CC** / *1-ALL* | finir tout le jeu sur un seul crédit | ❌ sans objet : continues illimités (spec §8.4) |

## Survie et puissance

| Terme | Définition | Chez nous |
|---|---|---|
| **Hitbox** | zone de collision réelle, souvent bien plus petite que le sprite | ✅ rayon **0,25**, « délibérément plus petite que le modèle visuel » (spec §8.2) |
| **Focus** | mode lent/précis, qui révèle ou réduit la hitbox | ❌ prévu spec §7.1, **non écrit** |
| **Bombe** | arme d'urgence à usage limité, **grosse dégâts + invulnérabilité**, jouable en panique comme en offensive | ❌ ; l'Overdrive (§9.4) qui en tiendrait lieu n'existe pas |
| **Autobomb** | bombe déclenchée automatiquement à la place d'une mort | ❌ |
| **Invulnérabilité** (*i-frames*) | fenêtre d'invincibilité après un coup ou une renaissance, pour « éviter les morts en chaîne » | ✅ **1,2 s** après impact, **2,0 s** à la renaissance |
| **Checkpoint** | point de reprise fixe, puissance remise à zéro — « associé à une difficulté brutale » (*Gradius syndrome*) | ❌ assumé : reprise sur place, sans perte de puissance (voir [`12`](12-level-design.md)) |

## Patterns

| Terme | Définition | Chez nous |
|---|---|---|
| **Danmaku** | « grand nombre de balles, souvent en motifs complexes » | ⚠️ à l'échelle du boss seulement |
| **Anneau** (*ring*) | balles simultanées à écart angulaire constant | ✅ `RADIAL` |
| **Éventail** (*spread*) | balles en arc ; **impair piège, pair contraint** | ✅ `FAN` (aveugle) et `AIMED` (visé) — écrits, **non employés en vague** |
| **Mur** (*wall*) | formation infranchissable, à contourner | ⚠️ de fait, jamais nommé comme outil |
| **Pile** (*stack*) | même angle, **vitesses différentes** | ❌ absent de la bibliothèque |

## Comment s'en servir

- **En brief de forge** : ces mots sont sans ambiguïté, un brief qui les emploie n'a pas besoin de
  les expliquer.
- **En review** : un « ✅ » de ce tableau est une chose à ne pas casser ; un « ❌ » n'est **pas** une
  tâche — plusieurs sont des choix (voir les pages [`06`](06-score-et-rang.md),
  [`09`](09-regles-et-systemes.md), [`12`](12-level-design.md)).
- ⚠️ **Ne pas confondre `rank` (difficulté dynamique) et le rang affiché** en fin de partie
  (`MissionReport`, seuils 12 000 / 25 000 / 40 000). Le second est une note, le premier un système
  vivant. Nous n'avons que le second.

## Sources

- [Help:Glossary](https://shmups.wiki/library/Help:Glossary) — Shmups Wiki : la totalité des définitions de cette page.
- [Shmups 101: A Beginner's Guide to 2D Shooters](https://racketboy.com/retro/shmups-101-a-beginners-guide-to-2d-shooters) — Racketboy : vue d'ensemble et usages du vocabulaire.
