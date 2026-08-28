# Voix — le contrat d'expression de besoin

Ce dossier tient les **demandes de répliques enregistrées**, une par fichier, au format JSON
normalisé. Même étagement que [`../textures/`](../textures/README.md) et
[`../characters/`](../characters/README.md) : les **contraintes techniques** d'un côté, la
**direction d'acteur** de l'autre.

> **Institué par [`ADR-0035`](../../decisions/ADR-0035-la-voix-du-jeu-a-un-visage.md).** Lyra
> Vantella a une vraie voix, produite par la voie de l'opérateur. Le dépôt n'avait aucun gabarit
> pour en demander une.

## Ce que le jeu fait déjà de la voix

Trois choses sont **branchées et testées**, avant même qu'un seul fichier existe :

1. le bus **`Voice`** porte sa chaîne « comms » — passe-haut 300 Hz, passe-bas 3400 Hz,
   distorsion 0,18, compresseur. C'est elle qui la fait sortir de la **radio du vaisseau** et non
   d'un studio ;
2. la bouche du portrait suit le **crête-mètre du bus**, pas un drapeau : si la voix joue, elle
   parle dessus ; si elle se tait, la frappe du texte en tient lieu ;
3. le volume de la voix est **déjà réglable** dans Options (`SettingsData.BUSES`).

Conséquence : livrer les fichiers suffit. Il n'y a rien à recâbler.

## Les quatre règles

| # | Règle | Pourquoi |
|---|---|---|
| 1 | **Un fichier par réplique**, jamais une piste continue | Le jeu les déclenche à des instants qu'il ne connaît pas d'avance (l'accueil boucle, le HUD parle sur une transition de phase). Une piste unique obligerait à chercher des points de montage |
| 2 | Format **`.ogg` Vorbis, mono, 48 kHz** | Mono parce que la chaîne comms est mono par nature, et parce qu'une voix stéréo se décale du portrait qui, lui, est à une place fixe de l'écran |
| 3 | **Aucun traitement à la source** : ni réverbération, ni filtre radio, ni compression forte | ⚠️ Le filtre est DANS le jeu. Une voix déjà filtrée passerait deux fois — bande étroite sur bande étroite, elle devient inintelligible. Et le réglage du filtre ne serait plus modifiable |
| 4 | **Silence de tête et de queue < 100 ms**, crête à −3 dBFS | Le jeu déclenche la réplique au moment où la bulle s'ouvre : une demi-seconde de blanc en tête décale la bouche du portrait de tout ça |

## La direction

Elle se décrit dans le JSON, séparément du texte. Ce qui est **immuable pour Lyra** :

- **navigatrice, pas hôtesse.** Elle informe et elle engage ; elle ne vend rien et ne s'excuse pas ;
- **calme par défaut**, y compris quand elle annonce un danger — c'est son calme qui rend l'alerte
  crédible quand elle le perd ;
- elle s'adresse au joueur par **« Pilote »**, jamais par un prénom ;
- **débit posé** : le texte s'écrit à 45 caractères/seconde à l'écran, la voix ne doit pas courir
  devant.

## Où ça se dépose

`assets/imported/audio/voice/lyra/<cue>.ogg`, une ligne de provenance par fichier dans
`assets/licenses/ASSET_PROVENANCE.csv`, et le nom du `cue` reporté dans le champ `voice_cue` de la
réplique correspondante (`resources/dialogue/*.tres`).

## Nommage

`VOX-NNNN-<personnage>-<contexte>.json`

## Les demandes

| Fichier | Sujet | Statut |
|---|---|---|
| [`VOX-0001-lyra-accueil.json`](VOX-0001-lyra-accueil.json) | les quatre répliques de l'écran-titre | ✅ livrée en synthèse locale (`piper fr_FR-siwis-medium`), en jeu — à remplacer si le timbre ne convient pas |
| [`VOX-0002-lyra-secteurs.json`](VOX-0002-lyra-secteurs.json) | les **sept** annonces de secteur et de phase, en jeu | **à commander** |
