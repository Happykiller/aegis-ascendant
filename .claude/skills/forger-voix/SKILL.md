# /forger-voix — donner une voix à un personnage

Ce skill sert **la production des répliques enregistrées** d'Aegis Ascendant : il synthétise une
demande `docs/forge/voice/VOX-NNNN-*.json`, la met à l'écoute de l'opérateur, et ne dépose dans le
dépôt que ce qu'il a validé **à l'oreille**.

Il existe parce que l'opérateur l'a demandé (« on en aura souvent besoin ») et parce que la
procédure est **déterministe** — donc elle s'encode, elle ne se raconte pas.

## Pourquoi un skill et pas un sous-agent

Les quatre questions de [`process-etendre-le-ghost`](../../resources/process-etendre-le-ghost.md) :
récurrente **oui**, bruyante **oui**, écriture verrouillable **oui** — mais **rend-elle un verdict
en une ligne ? NON.** Le verdict, ici, **s'entend**. Aucun sous-agent ne peut dire si une voix est
belle ; l'opérateur doit être dans la boucle. Le tableau tranche : sortie = *interagit avec
l'opérateur* → **skill**.

## La commande

```bash
python3 tools/voice/forge_voice.py <demande.json> --preview            # écouter
python3 tools/voice/forge_voice.py <demande.json> --deposer            # intégrer
```

Tout est dans le script. Ne pas refaire à la main l'installation, le téléchargement, le filtrage
ni la normalisation : c'est exactement ce que `/capitalize` interdit.

| Ce qu'il fait | Ce que ça évite |
|---|---|
| Installe piper et télécharge la voix **une fois**, hors du dépôt (`~/.local/share/aegis-voice`) | 60 à 80 Mo par modèle versionnés en LFS pour un outil qui ne part pas dans le jeu |
| Lit le texte **dans la demande JSON**, jamais retapé | trois copies d'une phrase = trois occasions de faire enregistrer autre chose que ce qui s'affiche. La demande tient elle-même son texte du `.tres`, et un test le garde |
| Dépose du **BRUT**, et ne filtre que pour l'écoute | ⚠️ la chaîne comms est **dans le jeu** (bus `Voice`). Une voix déjà filtrée passerait deux fois : bande étroite sur bande étroite, inintelligible — et le filtre ne serait plus réglable |
| Produit `_brut` **et** `_comms` en préversion | juger la voix brute, c'est juger autre chose que le jeu |
| Rogne les silences sous 100 ms, normalise à −3 dBFS | une demi-seconde de blanc en tête décale la bouche du portrait de tout ça |
| Rend les lignes de provenance prêtes à coller | un asset sans licence enregistrée est interdit (spec §0.2) |

## Protocole

### 1. La demande d'abord, la voix ensuite

Pas de `VOX-NNNN` ? On ne synthétise rien. Le gabarit et les quatre règles sont dans
[`docs/forge/voice/README.md`](../../../docs/forge/voice/README.md). Une demande dérive du `.tres`
que le jeu affiche — jamais l'inverse.

### 2. Préversion, et on s'arrête

```bash
python3 tools/voice/forge_voice.py docs/forge/voice/VOX-0001-lyra-accueil.json --preview
```

Les fichiers atterrissent sur le Bureau. **Rendre la main à l'opérateur** : il écoute les `_comms`.
Ne rien affirmer sur le rendu — une voix ne se juge pas au journal.

### 3. Ce qui se règle quand ça ne plaît pas

| Levier | Effet |
|---|---|
| `--voix` | `fr_FR-siwis-medium` (féminine, claire), `fr_FR-upmc-medium` (2 locuteurs, `--locuteur 0` jessica / `1` pierre), `fr_FR-tom-medium` (masculine) |
| `--cadence` | `length_scale` de piper. **> 1 ralentit** — et le débit fait autant que le timbre pour une voix posée. 1,15 par défaut ; 1,30 est nettement plus lent |

⚠️ **La ponctuation du `.tres` porte la prosodie.** Une réplique qui sonne plate se répare souvent
dans le TEXTE (une virgule, un point à la place d'une virgule) plutôt que dans un réglage. Le texte
change dans le `.tres` ; la demande et les gardes suivent.

### 4. Déposer, puis raccorder

```bash
python3 tools/voice/forge_voice.py docs/forge/voice/VOX-0001-lyra-accueil.json --deposer
```

Puis, et le script le rappelle : coller les lignes de provenance, et **reporter chaque `cue` dans
le champ `voice_cue`** de la réplique correspondante (`resources/dialogue/*.tres`). Sans ce
report, le jeu reste muet — et rien ne le signale.

Enfin `./scripts/check.sh`, puis `/jouer` : la voix ne se valide qu'entendue **en jeu**, après le
filtre, sous la musique.

## Ce qu'il ne faut PAS conclure

- **Un fichier produit n'est pas une voix validée.** Le seul test est l'écoute, par l'opérateur,
  de la version `_comms`.
- **La qualité plafonne à celle du modèle.** Piper est net et gratuit, il tourne hors ligne et
  aucune donnée ne sort de la machine. Il n'égale pas une synthèse commerciale expressive : si
  l'opérateur veut mieux, c'est un autre moteur — et alors une clé d'API et une ligne de licence
  à qualifier.
