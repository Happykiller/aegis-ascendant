---
titre: Rapport « Bible suprême » — vérification, tri, et ce qu'il faut décider
date: 2026-08-27
auteur: session Claude (poste happykiller), sur remise d'un rapport externe par l'opérateur
perimetre: gouvernance documentaire (SPEC / ADR / KB / bible de design), pas de code
etat: rapport IMPORTÉ, VÉRIFIÉ et TRIÉ ; les trois décisions sont PRISES (voir §6) et appliquées
supersede: rien. Complète docs/design/bible/ (étendue le même jour)
---

# Le rapport « Bible suprême », et ce qu'on en fait

> **Le rapport est dans le dépôt** :
> [`docs/design/AUDIT-2026-08-27-bible-supreme.md`](../design/AUDIT-2026-08-27-bible-supreme.md),
> texte intégral, statut **PROPOSÉ**, **sans autorité**.
>
> Ce plan est la seule chose à lire pour décider : il dit ce qui est **vrai**, ce qui est **déjà
> fait**, ce qui est **nouveau**, ce qui est **discutable**, et les **trois questions** qui
> attendent l'opérateur.

## Contexte

L'opérateur a commandé un audit externe du projet, remis le 2026-08-27, avec une recommandation
centrale : créer `docs/BIBLE_AEGIS_ASCENDANT.md`, **document canonique unique**, et **renverser la
hiérarchie de vérité** — la Bible deviendrait l'état courant, l'ADR ne dirait plus que le *pourquoi*.

Le rapport a été produit par lecture du dépôt à la révision `f64f6cf`, soit **avant** l'extension de
la bible de design du même jour (6 → 13 pages). Les deux travaux sont donc **indépendants**, et
c'est ce qui rend leur recoupement intéressant.

## 1. Vérification — ses affirmations factuelles sont exactes

Contrôlées une par une dans le dépôt, le 2026-08-27 :

| Affirmation du rapport | Verdict | Preuve |
|---|---|---|
| Le `README.md` décrit **encore** l'arc avec forteresse jouable, contre `ADR-0010` | ✅ **confirmé** | `README.md:5`, `:37`, `:43` — « prise de contrôle de la forteresse » |
| `ARCHITECTURE_TECHNIQUE.md` s'annonce à l'état du **2026-07-11** | ✅ confirmé | ligne 3 du fichier |
| Godot 4.7-stable, Forward+, GDScript typé, viewport 1920×1080 | ✅ confirmé | `project.godot:29-30` |
| Quatre autoloads : `GameState`, `SceneRouter`, `SettingsManager`, `AudioManager` | ✅ confirmé | `project.godot:14-21` |
| Budget projectiles **600**, sous-budgets **150 / 450** | ✅ confirmé | `bullet_manager.gd:17-18` |
| Bus `Master/Music/SFX/Voice`, limiteur **−0,5 dB**, compresseur sur SFX | ✅ confirmé | `resources/audio/default_bus_layout.tres` |
| États musicaux calqués sur les six phases | ✅ confirmé | `music_context.gd:8` |
| Le scoring est « essentiellement un compteur » | ✅ confirmé | et déjà écrit dans [`bible/06`](../design/bible/06-score-et-rang.md) |

**Aucune erreur factuelle trouvée.** C'est à souligner : le rapport peut être discuté sur ses
recommandations, pas sur son constat.

## 2. Convergence — il retrouve, seul, ce que la bible a trouvé le même jour

Quatre points identiques, établis par deux chemins indépendants :

⚠️ Les renvois ci-dessous pointent le **rapport de conformité** : les pages de la bible sont
devenues universelles le jour même, et ne parlent plus d'Aegis (voir §6).

| Constat | Rapport | [`CONFORMITE-AEGIS.md`](../design/CONFORMITE-AEGIS.md) |
|---|---|---|
| Un pilier de la spec §1.4 décrit encore la forteresse supprimée | « un pilier historique concerne encore la transformation en forteresse supprimée » | section `PIL` — pilier D orphelin depuis `ADR-0010`, et `LOI-PIL-06` violée |
| Le score n'est pas un système | « pas de chain, pas de multiplicateur, pas de conflit risque/récompense » | section `SCO` — six lois sur six absentes |
| Manette à revalider | « le README de release documente surtout le clavier : **à revalider** » | section `EXP` — **aucun événement joypad** n'est enregistré |
| Budgets perf « objectif » ≠ « mesuré » | `TARGET / MEASURED / MINIMUM / REFERENCE` | `.claude/resources/howto-mesurer-la-perf.md` |

Un constat trouvé deux fois par deux méthodes différentes n'est plus une opinion.

## 3. Ce que le rapport apporte de NEUF

Sept idées qui n'existent nulle part dans le projet, classées par rapport coût/rendement :

| # | Apport | Coût | Pourquoi ça vaut le coup |
|---|---|---|---|
| **A** | **Double étiquetage** : force normative (`FIXED / CONSTRAINT / INTENTION / REFERENCE / TO_DECIDE`) **×** état de preuve (`VERIFIED / INFERRED / PROPOSED / OBSOLETE`) | **faible** | Répond aux deux questions qu'un agent se pose : « dois-je obéir ? » et « est-ce encore vrai ? ». La seconde dimension **aurait empêché** la dérive du README et du pilier D |
| **B** | `UNSPECIFIED` **est une information valide** | nul | « Infiniment préférable à une décision inventée par un agent ». C'est déjà l'esprit de la KB (« À COMPLÉTER — décision de l'opérateur »), jamais formalisé |
| **C** | `value_type: NORMATIVE / RUNTIME_SOURCE / TO_DECIDE` | faible | Interdit de recopier dans un document une valeur dont le `.tres` fait foi. Le projet a **déjà** payé ce bug de duplication (`ADR-0024`, `ADR-0026`) |
| **D** | Contrat joueur **SEE / UNDERSTAND / FEEL / ANTICIPATE / DECIDE** par mécanique | moyen | **Généralise la loi des signaux** de [`KB/DAF/signaux.md`](../KB/DAF/signaux.md) — qui est née de cinq mécaniques muettes le même jour — et ajoute la ligne la plus utile : *« à ne jamais produire »* |
| **E** | Hiérarchie audio `CRITICAL / TACTICAL / FEEDBACK / SPECTACLE / AMBIENCE`, et la règle **« le mixage suit la priorité gameplay, pas la taille physique de l'événement »** | moyen | Rien n'existe là-dessus. Et le jeu a précisément un cas : le survol de lune et ses impacts d'astéroïdes, en pleine phase jouée |
| **F** | Distinction **vérification / validation** (V&V), méthodes `TEST / ANALYSIS / INSPECTION / DEMONSTRATION / PLAYTEST`, traçabilité `REQ ↔ VAL ↔ preuve` | **élevé** | Nomme exactement le trou du projet : « plusieurs défauts d'expérience existaient **malgré une porte de qualité verte** » |
| **G** | Contrôle de **dérive documentaire** dans `check.sh` | moyen | Le seul mécanisme du lot qui **empêche** la dette au lieu de la constater |

## 4. Ce qu'il faut discuter, et ne pas prendre tel quel

- **Il propose de renverser la hiérarchie de vérité.** « Une ADR acceptée devrait désormais
  obligatoirement modifier la Bible dans le même changement », l'ADR ne gardant que le *pourquoi*.
  C'est cohérent, et c'est **un changement de gouvernance**, pas une amélioration documentaire : il
  réécrit `CLAUDE.md`, la Definition of Done et le rituel `/cloture`. À ne pas faire à moitié.

- **Il se trompe sur ce qu'est la bible de design.** Il lit sa prudence (« elle n'est pas la source
  de vérité du produit ») comme un défaut — « précisément l'inverse de ce dont la Bible suprême a
  besoin ». Ce sont **deux objets différents**, et la décision de l'opérateur (§6) tranche dans le
  sens inverse du rapport : la bible n'est **pas** le contrat produit d'Aegis, c'est un corpus de
  lois **universelles**. Sa prudence n'était pas un défaut, c'était sa nature — désormais assumée
  jusqu'au bout, puisque tout le spécifique projet en est sorti.

- **Le volume du P0 est hors de proportion avec l'état du projet.** Quatre items « effort élevé »
  (catalogue `MEC-*` complet, SEE/UNDERSTAND/… sur chaque mécanique critique, matrice
  `REQ ↔ VAL ↔ preuve`, rebaseline complète SPEC+ADR+KB+README). Le P0 réel du backlog est
  « **rendre la démo irréprochable** » sur 2-3 minutes de jeu. Tout adopter gèlerait le jeu au
  profit de sa documentation — pour un **prototype de démonstration** (spec §1.3), c'est l'inverse
  de l'objectif.

- ⚠️ **Les références Sonic sont des guides de licence tiers.** Le rapport les cite comme exemples
  de **format**, ce qui est légitime. Mais `ADR-0005` / `ADR-0009` encadrent strictement les
  références IP dans ce dépôt : rien de ces documents n'entre dans `assets/`, et l'inspiration
  visuelle reste régie par la spec §0.2. Le rapport le dit lui-même — la leçon à retenir n'est
  « **pas de faire uniquement un style guide** ».

## 5. Le seul item actionnable — et sa réponse

- **`README.md` contredit `ADR-0010`.** Il annonce encore « prise de contrôle de la forteresse » et
  un arc qui n'existe plus depuis le 2026-07-19.

  ❌ **Non corrigé, sur décision de l'opérateur** (§6) : « le README est un document pour les
  opérateurs [...] on a sûrement dans la KB ce qu'il faut. » L'arc réel vit dans
  [`KB/DAF/arc-de-jeu.md`](../KB/DAF/arc-de-jeu.md), et c'est lui qui fait foi.

⚠️ Les deux documents `docs/architecture/*.md` sont dans le même cas, **mais la question est déjà
ouverte** dans [`KB/DAF/arc-de-jeu.md`](../KB/DAF/arc-de-jeu.md) avec trois options (corriger /
archiver daté / laisser). Ne pas trancher ici ce qui attend là-bas.

## 6. Les trois décisions — prises le 2026-08-27

### DEC-1 — La Bible n'est pas le contrat produit d'Aegis : c'est un corpus universel

L'opérateur écarte la proposition centrale du rapport, et en pose une autre :

> « La bible doit pouvoir être suivie par **n'importe quel jeu de shoot vertical** comme le nôtre.
> C'est un document de référence, une table de **lois et règles universelle** pour faire un bon jeu
> de shoot vertical. » — et « **c'est pas un plan d'implémentation**, c'est une table de vérité,
> règle, lois, convention à suivre ».

Conséquences appliquées :

- `docs/design/bible/` est réécrite en **corpus de 88 lois**, identifiées (`LOI-PAT-03`) et graduées.
  Elle ne contient **aucune** valeur, aucun nom de fichier, aucun jeu : elle se copie telle quelle.
- **La hiérarchie de vérité ne bouge pas.** `SPEC → ADR → KB` reste en place, `CLAUDE.md` est
  inchangé. Une loi de genre qui contredit une décision de projet **perd**.
- Tout le spécifique Aegis part dans
  [`docs/design/CONFORMITE-AEGIS.md`](../design/CONFORMITE-AEGIS.md).

### DEC-2 — Périmètre : les lois, pas l'appareil de traçabilité

Sans Bible-contrat, les catalogues `MEC-*` et la matrice `REQ ↔ VAL ↔ preuve` **n'ont plus d'objet**
dans ce document : ils décriraient une implémentation, ce que la Bible refuse d'être par définition.

Deux de leurs idées sont **conservées, converties en lois** : le contrat joueur
(`LOI-EXP-09`) et la distinction vérification/validation (`LOI-EXP-12`).

### DEC-3 — Les forces normatives : adoptées, et c'est le meilleur apport du rapport

Quatre forces, sur chaque loi : **LOI** (48), **CONTRAINTE** (15), **INTENTION** (17),
**RÉFÉRENCE** (8).

⚠️ L'**état de preuve** (`VERIFIED / INFERRED / PROPOSED / OBSOLETE`) n'entre **pas** dans la
Bible : il porte sur un build, donc sur un projet. Il devient la colonne « état » du rapport de
conformité — *tenue / partielle / **écartée** / **absente** / non vérifiée* — où la distinction qui
compte est celle qu'ajoute ce projet : **écartée** (choix assumé) n'est pas **absente** (dette).

### Et le `README.md` ?

**Non corrigé, sur décision de l'opérateur** : « le README est un document pour les opérateurs, je
ne suis pas convaincu qu'il soit judicieux d'aborder le contenu, on a sûrement dans la KB ce qu'il
faut. » La KB porte l'arc réel ([`KB/DAF/arc-de-jeu.md`](../KB/DAF/arc-de-jeu.md)), et c'est elle
qui fait foi.

## Ce qui reste ouvert

Les cinq écarts de [`CONFORMITE-AEGIS.md`](../design/CONFORMITE-AEGIS.md) — pilier D orphelin,
score à trancher, Overdrive/secondaire/focus, manette, checkpoints de la spec §5.3 — et les trois
gestes gratuits qui n'attendent aucune décision.

Rien de tout cela n'est engagé par ce plan.
