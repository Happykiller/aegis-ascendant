# Plan — Élargir le bestiaire d'ennemis

| | |
|---|---|
| **Date** | **2026-08-23** |
| **Auteur** | session `aegis-ascendant-f0` (bestiaire) |
| **Périmètre** | familles d'ennemis, coques de vaisseaux, socle de comportement |
| **État** | **à appliquer** — lots 0 à 3 livrés, lots 3b à 6 à faire |
| **Supersède** | `docs/BACKLOG.md` sur le périmètre ci-dessous. Le backlog reste l'**inventaire** ; en cas de désaccord avec ce plan, **c'est le plan qui gagne** (règle inscrite en tête du backlog le 2026-08-23). |
| **Ne couvre pas** | le boss final et ses coques — session `aegis-ascendant-47`, voir son propre plan daté du jour. |

> **Pourquoi ce fichier est daté.** Le dépôt accumule des documents de planification
> sans date, et on ne sait plus lequel fait foi. Convention retenue le 2026-08-23,
> commune aux deux sessions : `docs/plans/AAAA-MM-JJ-<sujet>.md`, en-tête portant
> date / auteur / périmètre / état, et une ligne disant ce que le plan supersède.
> **Un plan sans ces quatre champs est à considérer comme périmé.**
>
> Et la date seule ne suffisait pas : elle dit lequel est **le plus récent**, pas
> lequel **s'applique**. D'où la règle d'arbitrage posée en tête de `docs/BACKLOG.md`
> le même jour — **entre le backlog et un plan plus récent, le plan gagne.**

---

## 1. État à la clôture du 2026-08-23

- **Porte verte** : `./scripts/check.sh` → **388 méthodes, 1567 assertions, 0 échec, 0 erreur de parse**.
- **Arbre de travail propre**, aucun fichier non suivi.
- **`main` est à 39 commits d'avance sur `origin`**, les deux sessions confondues.
  **Aucun push n'a été fait** : c'est une décision de l'opérateur, jamais prise.
- Aucun sous-agent en vol (la forge du Shield Carrier a été arrêtée avant d'écrire).

## 2. Ce qui est livré et jouable

### Le socle (ADR-0022)

Le bestiaire n'avait qu'un axe de variété — la courbe. Il en a **quatre**, tous
*append-only*, tous d'indice 0 = comportement d'avant, donc **les neuf familles
historiques sont inchangées par construction** :

| Axe | Bibliothèque | Répond à |
|---|---|---|
| `Path` (+ `DRIFT`) | `EnemyPath` | où va la coque — fonction **pure** de l'âge |
| `Motion { PATH, HOMING }` | `EnemyHoming` | qui pilote la position : la courbe, ou la poursuite |
| `Fire { SINGLE, NONE, FAN, AIMED, RADIAL }` | `EnemyFire` | la géométrie de la salve |
| `Effect { NONE, GRAVITY_WELL, LEECH, SHIELD_AURA }` | `EnemyController` | ce qui n'est pas une balle |
| `EnemyReaction` / `EnemyPose` / `EnemyVitals` | — | menace de proximité, pièces articulées, signes vitaux |

### Les quatre unités

| Unité | Verbe de jeu | Coque | Codex |
|---|---|---|---|
| **Choir Mine** | un obstacle qu'on peut **dépenser** (usage unique) | ✅ `choir_mine.glb` | ✅ |
| **Null Maw** | une **zone interdite** : aspire, ne blesse jamais, se réarme | ✅ `null_maw.glb` | ✅ |
| **Leech Drone** | un **parasite** : poursuit, s'accroche, vole 60 % de la poussée | ✅ `leech_drone.glb` | ✅ |
| **Shield Carrier** | la **cible prioritaire** : rend les autres invulnérables | ❌ **coque manquante** | ❌ |

⚠️ **Les quatre sont réglables au banc d'essai et visibles au bestiaire, mais
n'apparaissent dans AUCUNE vague de l'arc.** C'est délibéré : les poser dans
`wave_graybox_01.tres` change le rythme et la difficulté, et ce jugement appartient
à l'opérateur (`docs/KB/REGLES/consignes.md`).

Banc d'essai : `./scripts/play.sh -- --goto-lab=<mine|maw|leech|carrier>`
(`--no-backdrop` pour juger une silhouette, sans lui pour juger une couleur).

---

## 3. Ce qui reste, dans l'ordre

### 3b. Finir le Shield Carrier — *prêt à lancer, rien ne le bloque*

Le comportement est **écrit, testé et vérifié** ; il ne manque que la coque.

1. Relancer la forge sur `docs/forge/briefs/BRIEF-0046-shield-carrier-hull.md`
   (brief complet et commité, rejouable tel quel).
2. Vérifier le livrable **avant de le croire** : UV sur 100 % des primitives,
   budget ≤ 8 000 triangles, `Muzzle_C` + `Engine_C`, `Cradle_01..03`.
3. Intégrer : `resources/enemies/shield_carrier.tres`,
   `scenes/enemies/shield_carrier.tscn`, fiche codex + `ROSTER`, gardes dans
   `tests/unit/test_enemy_hulls.gd`, montage `SHIPPED` du banc.
4. **Générer le dôme de protection par le code** depuis `aura_radius` — il doit
   montrer la portée réelle. Non fait, et non sculpté à dessein.

### 4. Les deux familles restantes de la spec §11.1

- **Null Bomber** — lent, encaisse, **pond des mines** derrière lui. Demande un
  sous-pool de mines réservé dans le spawner (**aucun `instantiate()` en jeu**, spec §26.1).
- **Frigate Turret** — ancrée, ne bouge pas, mais **vise** (`Fire.AIMED`), point faible dorsal.
  ⚠️ **Piège connu et déjà payé par l'autre session** : un `Beam` enfant d'un `Node3D`
  subit **deux fois** la transformation et devient invisible, sans erreur ni test rouge.
  Poser `top_level = true` dès la première ligne.

### 5. Correction du kit Blender — *bloquée, et l'ordre est convenu*

`ak.inset_panel()` est un **no-op sur un maillage fraîchement bâti** : `inset_region`
lit une normale de face qui vaut zéro tant que `normal_update()` n'a pas été appelé.
Bordures d'aire **0,000000 m²** mesurées contre **0,000714** avec. Il ne reste que le
changement de matériau : **un panneau qui se voit sans exister**. Rien ne le signale —
ni le compte de triangles, ni le contrat d'export, ni le rendu.

Coques concernées : `choir_mine`, `null_maw`, `specter_9`, et **les deux coques de
boss** (`build_pale_leviathan.py` : 10 appels, 0 `normal_update`).

**Ordre acté entre les deux sessions, à ne pas court-circuiter :**

1. la reforge d'épines du boss (BRIEF-0080) est livrée **et intégrée** ;
2. correction dans `aegis_kit.inset_panel()` — **pas** dans chaque script, sinon le
   prochain l'oubliera comme les précédents ;
3. régénération de **toutes** les coques ;
4. re-revue des silhouettes.

⚠️ **Conséquence à anticiper** : la régénération change tous les `sha256`, donc les
lignes de `assets/licenses/ASSET_PROVENANCE.csv` **et** les compte-rendus de brief qui
les citent. CSV partagé → un seul écrivain, probablement un seul commit.

### 6. Intégration à l'arc — *demande une décision de l'opérateur*

Poser les unités dans une séquence « champ de mines » entre la vague de chasseurs et
le mini-boss. C'est le **P0 du backlog** (« ajouter 1-2 vagues pour 2-3 min de jeu »),
mais ça touche `scripts/gameplay/graybox_root.gd` — fichier de l'autre session — et
surtout **ça change le rythme**, ce qui est un jugement de joueur.

---

## 4. Décisions qui attendent l'opérateur

1. **Pousser `main` ?** 39 commits d'avance, jamais poussés.
2. **Intégrer les unités à l'arc**, et avec quelle intensité ?
3. **Le marquage vert de la Choir Mine** forme une plaque pleine sur le flanc.
   Mesuré à 0,2 % de l'aire vue **par la caméra de jeu**, qui regarde de dessus — mais
   le bestiaire présente la coque de trois quarts et montre un flanc que le jeu ne montre
   jamais. Les deux mesures sont exactes, elles ne répondent pas à la même question.
   Une ligne à changer dans `build_choir_mine.py` si ça gêne.
4. **`AudioManager` n'arrête pas ses flux à la sortie** : 2 × le nombre de sons en
   lecture fuit à chaque fermeture (4/2 à l'écran-titre, 14/7 en combat). Bénin, mais
   c'est du bruit permanent au journal — celui qui noiera la prochaine vraie fuite.
   ⚠️ Se mesure **uniquement en headless avec `--quit-after`** : sans arrêt déterministe,
   le compte n'est pas reproductible.

---

## 5. Accords entre sessions — à ne pas casser

- **Plages de numéros de brief** : **0040–0079 = bestiaire**, **0080–0099 = boss**.
  Aucune annonce nécessaire. Trois collisions en une journée ont montré qu'annoncer
  avant d'écrire ne suffit pas : les annonces se croisent en vol.
- **Un seul écrivain sur Windows** (`C:\tmp` et le processus ne sont pas cloisonnés) :
  prévenir avant tout `play.sh` / `deploy-win.sh` / capture.
- **Jamais de `git commit -a`, `add .`, `--amend`, `rebase`, `reset --hard`** tant que
  deux sessions écrivent. ⚠️ `--amend` cible `HEAD`, **pas « mon dernier commit »** : sur
  un arbre partagé, `HEAD` appartient à celui qui a committé en dernier. Un pathspec
  n'en protège pas — c'est ce que la commande **vise** qui est le problème.
- **Le kit `tools/blender/lib/aegis_kit.py` est gelé** jusqu'au point 5 ci-dessus.

---

## 6. Ce que la journée a appris, et qui vaut pour la suite

Cinq fois, une garde verte a affirmé quelque chose de faux. Aucune de ces erreurs
n'était de la négligence — c'est ce qui les rendait indétectables en solo.

- **Un test dit qu'une valeur a changé, jamais que le joueur le voit.** Le télégraphe
  des mines montait l'énergie d'un émissif **déjà saturé** : opération nulle.
- **Une garde sur la mauvaise propriété est pire que pas de garde** — elle ne peut pas
  échouer, et elle rassure. Celle sur les tangentes était vide : Godot les régénère à
  l'import. Ce sont les **UV** qui ne s'inventent pas.
- **Un test de géométrie ne remplace pas un test d'existence.** Cinq tests de mise en
  page sont restés verts pendant que le bandeau du codex avait entièrement disparu.
- **Un différentiel ne vaut que si le témoin ne diffère que par la variable mesurée.**
  Comparer à une *autre* unité au lieu de la *même* sans le réglage a failli faire
  renoncer à un réglage qui marchait — et le chiffre faux allait dans le sens qui
  **avait l'air le plus rigoureux**.
- **On vérifie ce qui revient d'une délégation, pas ce qu'on a envoyé.** Un livrable
  irréprochable ressemble à une preuve que la commande était bonne.

Corollaire outillé : **`--no-backdrop` pour juger une silhouette, le fond réel pour
juger une couleur — deux captures, jamais la même.**
