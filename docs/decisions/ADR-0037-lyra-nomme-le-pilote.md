# ADR-0037 — Lyra nomme le pilote, et le nom qu'elle choisit dit où l'on en est

- **Statut** : accepté
- **Date** : 2026-08-28
- **Contexte** : demande de l'opérateur — « elle me désigne comme "Pilote". On a créé une
  histoire, faut qu'elle utilise mon nom, qu'il y ait une relation entre eux »
- **Amende** : `docs/lore/README.md` (règle n° 1), `docs/lore/EXPLOITATION.md` §0 (« canon, sans
  exception »), `docs/forge/CHARTE_CREATIVE.md` §2 (clause d'usage du nom du pilote),
  `docs/forge/voice/README.md` (contrat de direction), et **`ADR-0035`** dont le contrat de voix
  posait l'adresse invariable

## Contexte

`ADR-0036` a donné au jeu une bible narrative, et au pilote un nom : **Wren Adaire**, indicatif
**Halyard**, né sur Ambry — un avant-poste que le Registre a *radié* plutôt que déclaré perdu.

Ce nom n'a jamais été prononcé. Cinq documents interdisaient à Lyra de l'employer, dont trois le
posaient comme canon non discutable. La règle avait une raison : l'anonymat institutionnel. Un
pilote qu'on n'appelle que « Pilote » est un pilote interchangeable, et c'est le sujet du jeu.

L'opérateur la lève. Non pas contre cette raison, mais parce qu'elle **coûte plus qu'elle ne
rapporte** : après vingt minutes de jeu, une navigatrice qui ne vous a jamais nommé n'est pas
sobre, elle est distante — et le lien qu'`ADR-0035` voulait créer en lui donnant un visage,
l'adresse le défaisait à chaque réplique.

⚠️ **Ce que la règle protégeait vraiment survit intact.** Ce que Lyra tait n'est pas le nom : c'est
qu'elle a lu le dossier et sait qu'Ambry est radié (`docs/lore/PERSONNAGES.md`). Ce silence-là est
la clé de leur relation, et il ne dépend pas du vocatif.

## La décision

Lyra nomme le pilote, **et le nom qu'elle emploie change avec le moment**. Trois registres, définis
par leur DÉCLENCHEUR et jamais par leur texte — un ADR qui citerait les répliques se périmerait à
la première retouche.

| Registre | Déclencheur | Ce qu'il dit |
|---|---|---|
| **Halyard** | Partout ailleurs — accueil compris | L'indicatif, ce qu'on emploie en radio. C'est le terme **non marqué** : le fond contre lequel les deux autres se détachent |
| **Wren** | Clé `docking`, **une seule fois dans tout le jeu** | Elle laisse tomber le protocole à l'instant où il rentre vivant de ce qui n'aurait pas dû être là |
| **Adaire** | Clé `mission_failed` | Le nom du **dossier**, pas celui de la personne, pendant qu'elle porte l'entrée au Registre |

**« Halyard » doit être le défaut, y compris au premier mot du jeu.** Si l'accueil dit « Bienvenue,
Pilote », le joueur installe *Pilote* comme norme, « Halyard » devient une variante, et « Wren »
arrive en troisième registre au lieu de deuxième : la rupture ne se sent plus. C'est aussi le
dernier « Pilote » qui subsisterait, donc il se lirait comme un oubli.

### La règle d'unicité est opposable

« Wren » ne se dit **qu'une fois dans toute la campagne**, à l'appontage du niveau 1. Toute
réplique future des niveaux 2 à 12 qui voudrait l'employer **amende cet ADR**. Sans cette clause,
la deuxième occurrence arrivera par accident dans six mois, et la première cessera rétroactivement
de vouloir dire quelque chose.

### Ce que ça renverse, explicitement

`VOX-0004` (l'écran de défaite) portait l'argument inverse : « ne rien changer à sa façon
habituelle de le dire — c'est l'identité de l'adresse qui fait le vertige, pas une inflexion. »

Il n'est pas écarté, il est **retourné**. Il supposait que le vertige vienne de la **constance** :
elle parle exactement comme d'habitude à quelqu'un qui n'est plus là. La décision pose qu'il vient
de la **rupture** — « Adaire » au rapport *montre* le passage de l'homme au dossier au lieu de le
postuler. Et une rupture n'existe que sur fond de norme : c'est précisément pourquoi « Halyard »
doit être partout ailleurs.

### `asteroid_field` change aussi, et ça se dit

Son texte portait la mention « validé mot pour mot par l'opérateur » depuis une maquette. Il est
modifié — le seul vocatif, le reste octet pour octet. Raison : c'est la **première adresse en
mission**, et l'épargner ferait lire toute la gradation comme un renommage manqué. Un texte validé
ne se modifie pas en silence ; c'est ici qu'on le note.

## Le coût, accepté

**8 répliques sur 15 sont re-synthétisées** : les deux de l'accueil, et six des sept en jeu.

⚠️ **La chaîne de voix n'est pas reproductible, et on l'a découvert en la calibrant.** Un témoin —
une réplique au texte inchangé, synthétisée avec les nouvelles — a rendu **4,99 s au lieu de
4,49 s** : la cadence employée aux sessions précédentes n'était pas celle par défaut du script, et
n'était **tracée nulle part**. Pire, deux synthèses du même texte aux mêmes paramètres rendent
4,33 s et 4,52 s : **piper n'est pas déterministe**.

Conséquence de méthode, valable pour toute voix future : on ne vise pas une durée, on **dépose,
puis on mesure, puis on règle le `hold`**. Et la cadence s'inscrit désormais dans
`assets/licenses/ASSET_PROVENANCE.csv`, avec l'outil.

## Conséquences

- La règle « Lyra dit Pilote » disparaît des cinq documents qui la portaient ; elle y est
  **remplacée** par les trois registres, pas supprimée — `docs/lore/README.md` annonce « les deux
  règles qui ne se discutent pas », et un compte qui ment est pire qu'une règle périmée.
- Le tableau d'audit de `docs/lore/EXPLOITATION.md` §6, qui déclarait cinq de ces répliques
  « à conserver », est recalé.
- Le mot « pilote » reste partout où il est un **nom commun** (« le pilote garde ses commandes »,
  fiches de codex, commentaires). Ce qui change est l'**adresse**, pas le vocabulaire.
