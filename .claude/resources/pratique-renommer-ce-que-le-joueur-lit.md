# Pratique — renommer ce que le joueur lit, sans toucher au reste

Un nom de fiction change plus souvent qu'on ne croit : l'opérateur a rejeté **« Null Choir »** le
2026-08-28, après huit mois d'usage, une fois qu'il existait un lore pour le juger. Le renommage a
coûté **une heure**, alors qu'il en aurait coûté dix s'il avait été mené comme un `sed` global.

Deux règles en sortent, et une seule des deux est évidente.

## 1. Nom affiché ≠ identifiant technique

Le joueur ne lit **jamais** un nom de fichier. Séparer les deux dès le premier grep :

| Catégorie | Exemples | Faut-il changer ? |
|---|---|---|
| **Nom affiché** | `display_name`, `title` et `description` d'un briefing, `notice` d'une fiche codex, texte d'une réplique | **Oui** — c'est ce qui est à l'écran |
| **Identifiant** | `choir_mine.tres`, `choir_harvester.tscn`, `null_maw.glb`, clés de dialogue, `voice_cue`, préfixes de pièces animées, valeurs d'énumération | **Non** — invisible, et le renommer coûte des `.uid`, des réimports et des tests pour zéro gain |
| **Documentation** | la majorité du volume | Au fil de l'eau, **sauf** la charte créative et la spec, qui sont normatives : elles passent **avant** tout autre emploi du nouveau nom, sinon deux sources de vérité se contredisent |

Mesuré sur ce renommage : 89 occurrences du nom affiché, dont **71 en documentation**, 5 dans le
code, 5 dans les Resources. Le travail réel tenait dans une dizaine de fichiers.

## 2. ⚠️ Un renommage se vérifie DANS LES DEUX LANGUES

C'est le piège, et il est passé à travers un inventaire pourtant écrit exprès.

Le dépôt mélange l'anglais (noms canon, identifiants) et le français (notices, briefings,
répliques). Deux fiches de codex disaient **« Choeur Nul »** — la traduction française, écrite par
une session qui avait bien fait son travail. `grep "Null Choir"` ne les voyait pas.

```bash
# ⚠️ DEUX MOTIFS SÉPARÉS, jamais une classe de caractères
grep -rn "Null Choir" . ; grep -rn "Choeur Nul" . ; grep -rn "Chœur Nul" .
```

**Chercher la traduction avant de conclure**, y compris ses variantes de graphie. Un renommage
« terminé à 90 % » laisse justement les occurrences que personne ne relira.

⚠️ **Et la ligature `œ` est un piège dans le piège.** Ce grep-ci, écrit le 2026-08-28 pour ne plus
se faire avoir, s'est fait avoir : il cherchait `Choeur` en deux lettres, et **43 occurrences de
`Chœur` avec la ligature** lui ont échappé — dont trois dans du code vivant, relevées le lendemain.

Pire, la parade qui vient naturellement ne marche pas : `Ch[œo]eur` est une **classe d'octets**,
pas de caractères. « œ » est multi-octets en UTF-8, donc la classe est silencieusement fausse et
le grep rend zéro résultat en ayant l'air de fonctionner. Écrire **deux motifs séparés**, ou
`grep -P`. Même famille : `æ`, `’` contre `'`, `—` contre `-`, `É` composé contre précomposé.

## 3. Le nom se choisit sur ce qu'il devient, pas sur ce qu'il évoque

« Null Choir » avait été posé **avant qu'il existe un lore à nommer** : une étiquette de genre.
Une fois l'origine écrite, ses deux défauts sont apparus d'un coup — « Choir » tirait vers le
religieux alors que cet ennemi n'a ni foi ni culte, et « Null » ne disait rien de lui.

Le critère qui a tranché entre sept candidats : **est-ce que le nom veut dire autre chose au
dernier niveau qu'au premier ?** Un nom qui change de sens sans changer de lettre est ce qu'une
campagne demande. C'est ce qui a désigné « l'Unisson », et c'est reproductible pour n'importe quel
nom propre du projet.

→ Décision et inventaire complet : [`ADR-0036`](../../docs/decisions/ADR-0036-l-ennemi-s-appelle-l-unisson.md)
