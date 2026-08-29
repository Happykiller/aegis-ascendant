# BRIEF-0087 — La bible narrative d'Aegis Ascendant

- **Statut** : **intégré** (2026-08-28). La bible est livrée (`docs/lore/BIBLE.md`), et ce qu'elle
  demandait est fait : les **trois moments muets** qu'elle avait identifiés (§3.0, §3.5, §3.6) ont
  leurs répliques — `VOX-0003`, jouées en `mission_start` / `docking` / `mission_complete`. Le nom
  du pilote est passé au canon de `docs/forge/CHARTE_CREATIVE.md`.
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-28

## Objectif

Écrire **la bible narrative** du jeu : un document unique dont le concepteur pourra piocher, pour
toute la suite du projet, le nom du pilote, la caractérisation de l'ennemi, et le déroulé
narratif de la mission — pour écrire ensuite les dialogues qui en découlent.

## Contexte

La spec (§3.2) prévoit explicitement « le scénario » et « les dialogues » parmi les éléments
originaux à créer — et ni l'un ni l'autre n'a jamais été écrit. Le jeu a un **canon mécanique et
visuel** riche (factions, coques, palettes — `docs/forge/CHARTE_CREATIVE.md` §2), un **arc de jeu**
précis (`docs/KB/DAF/arc-de-jeu.md`), et un **personnage qui parle déjà** (Lyra Vantella,
`ADR-0035`, ses répliques dans `resources/dialogue/`) — mais aucun **fil narratif** qui relie tout
ça. Le joueur traverse six phases sans jamais savoir qui il est, ni ce que l'ennemi veut.

Ce document devient la source à laquelle le concepteur puisera pour écrire de nouvelles répliques
de Lyra, à chaque endroit du jeu qui en manque encore.

### Ce qui est DÉJÀ CANON et ne se réécrit pas (lire avant d'écrire une ligne)

| Élément | Ce qui est fixé |
|---|---|
| `docs/forge/CHARTE_CREATIVE.md` §2 | La table des noms officiels : Helios Vanguard, Specter-9, Aurora Spear, Aegis Citadel, The Null Choir, The Pale Leviathan, Choir Harvester, Arsenal Orbital Talvern, Lyra Vantella. **Aucun de ces noms ne se réattribue à autre chose.** |
| Bestiaire (`resources/enemies/*.tres`) | Les unités du Null Choir sont DÉJÀ nommées : Needle Scout, Leech Drone, Choir Mine, Null Maw, Shield Carrier, Crescent Interceptor. **Ne pas en inventer d'autres** — la bible les intègre à sa description du Null Choir, elle ne les remplace pas. |
| `docs/forge/voice/VOX-0001-lyra-accueil.json`, `VOX-0002-lyra-secteurs.json` | Onze répliques de Lyra, déjà écrites, déjà en production. **Ne pas les réécrire.** La direction y dit explicitement : « elle dit *Pilote*, jamais un prénom » — le pilote garde donc un **nom pour la fiction** (codex, carnet de bord), jamais un prénom que Lyra prononcerait à voix haute. |
| `ADR-0021` | Le combat du Pale Leviathan : trois cycles armure/noyau. Ce que la bible en dit doit rester compatible. |
| Le Null Choir | « intelligence collective biomécanique » (charte §2) — **pas un chef, pas un individu**. Une bible qui lui invente un porte-parole nommé contredirait le canon ; elle peut lui donner une VOIX ou une NATURE (ce que le Choir communique, comment, pourquoi) sans lui donner un visage.

## Ce que le document doit contenir

### 1. Le pilote

Un nom, un indicatif (callsign) dans la tradition d'Helios Vanguard, une ou deux phrases de passé
qui expliquent pourquoi cette personne pilote un Specter-9 — sans en faire une cinématique : c'est
un joueur inconnu vu de l'extérieur, jamais un visage à l'écran (aucun asset n'est demandé ici).

### 2. Le Null Choir — ce qu'il VEUT

Pas juste « l'ennemi » : pourquoi il avance sur les colonies (charte : « Le Null Choir avance sur
les colonies »), ce qu'une « intelligence collective biomécanique » désire, comment ses unités
déjà nommées (Needle Scout, Leech Drone, Choir Mine, Null Maw, Shield Carrier, Crescent
Interceptor) s'articulent dans cette nature — et ce que le Pale Leviathan EST pour le Choir
(son cœur ? son messager ? sa mémoire ?).

### 3. Le déroulé narratif de la mission

L'arc de jeu est fixé (`docs/KB/DAF/arc-de-jeu.md`) : **FIGHTER_WAVES → MINI_BOSS → ASTEROID_FIELD
→ FINAL_BOSS (plongée, cycles armure/noyau) → DOCKING → VICTORY**. Pour CHAQUE étape, écrire :

- ce qui s'y joue narrativement (pas mécaniquement — la mécanique est déjà écrite ailleurs) ;
- l'enjeu vu par le pilote, l'enjeu vu par Lyra ;
- une ou deux idées de ce que Lyra pourrait dire à cet instant précis (le concepteur écrira les
  répliques définitives lui-même — ceci n'est qu'une matière, pas un script final).

Trois moments n'ont AUCUNE réplique aujourd'hui et sont la priorité de cette section : le tout
début de la mission (avant la première vague), l'arrivée à l'appontage (DOCKING), et la victoire.
Les cinq autres moments ont déjà leurs répliques (VOX-0002) — la bible leur donne un CONTEXTE, ne
les remplace pas.

### 4. Lexique narratif

Les quelques termes propres à cette fiction (ce que « la ligne » signifie pour Helios Vanguard, ce
qu'est le « canal 09 » déjà mentionné en jeu, etc.) — bref, pas un glossaire exhaustif.

## Contraintes

- **IP** : aucun nom, personnage, faction ou trame identifiable d'une œuvre existante
  (Macross, Robotech, Gundam, ou toute autre licence). Aucune référence à une licence ou à un
  artiste vivant.
- **Ton** : celui déjà établi par Lyra (`docs/forge/voice/VOX-0002-lyra-secteurs.json`, champ
  `direction`) — sobre, militaire, jamais grandiloquent. Le jeu est un prototype solo, pas une
  épopée : la bible doit rester à l'échelle de six phases jouées en une session.
- **Longueur** : un document dense vaut mieux qu'un document long. Viser 150-250 lignes.

## Texture (ADR-0028)

Sans objet — ce livrable est un document texte, aucun asset graphique ou modèle 3D n'est demandé.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `docs/lore/BIBLE.md` | Le document décrit ci-dessus, en Markdown, avec un bandeau d'en-tête (`titre`, `type: lore`, `statut: actif`, `maj: 2026-08-28`) comme les pages de `docs/design/bible/`. |

## Provenance

Un document texte original, sans matière première tierce : aucune ligne de provenance requise
(pas d'image, pas d'audio, pas de modèle).

## Critères d'acceptation

- [ ] Ne contredit aucun élément de la table « déjà canon » ci-dessus.
- [ ] N'invente aucun nom d'unité, de coque ou de personnage qui n'existe pas déjà — sauf le nom
      et l'indicatif du pilote, seul élément explicitement demandé comme nouveau.
- [ ] Couvre les six phases de l'arc, avec un traitement particulier des trois moments sans
      réplique (début de mission, appontage, victoire).
- [ ] Reste un document de RÉFÉRENCE — pas un script de dialogue final : pas de guillemets de
      réplique "prêtes à enregistrer", des idées et des intentions.

## Hors périmètre

- N'écrit AUCUN fichier `.tres`, `.gd`, `.json` de demande de voix (VOX-NNNN) : le concepteur
  s'en charge après lecture de la bible.
- Ne modifie ni la charte créative, ni le canon existant, ni aucun asset déjà livré.
- Ne propose aucun visuel, aucune musique, aucun asset : uniquement le texte demandé.
