# Thème principal — spécification exécutable (`main_theme`)

- **Brief** : `docs/forge/briefs/BRIEF-0021-main-theme.md`
- **Statut** : spec normative, prête à coder. Aucun audio livré ici.
- **Cible d'implémentation** : `tools/audio/generate_main_theme.py` (session principale),
  sortie `assets/source/audio/music/main_theme.wav` → masterisé/encodé par
  `tools/audio/build_audio.py` (inchangé).
- **Socle** : `docs/forge/output/adaptive_music_structure.md` (cellule signature, ré mineur modal).

Ce document se lit comme une partition d'ingénieur : chaque nombre est destiné à être recopié
tel quel. Tout ce qui n'est pas chiffré ici est une liberté explicite laissée à l'implémenteur ;
tout le reste est normatif.

---

## 0. Propriété intellectuelle — cadre

- **Aucune œuvre, aucun artiste, aucun titre n'est cité ni pris pour modèle** dans cette spec.
  Les directions données au commanditaire (« hybride orchestral », « socle techno ») sont des
  **conventions de genre** — ostinato, nappe, braam, kick 4/4, riser, drop — au même titre que
  « accord parfait » ou « contretemps ». Elles ne sont l'objet d'aucun droit.
- **Le seul matériau mélodique du morceau est la cellule signature d'Aegis Ascendant**
  (intervalles `+5, −2, +4` demi-tons). Toute hauteur mélodique de la partition en dérive :
  énoncé direct, rétrograde, augmentation, doublure d'octave. Rien d'autre.
- **La grille d'accords est dérivée de la cellule** (§3.3), et non empruntée : chaque accord est
  choisi pour la couleur qu'il donne à la note de cellule qu'il porte. Aucune progression
  entendue ailleurs n'a servi de gabarit.
- Les percussions, le kick, le sub et le riser sont décrits **par leur synthèse** (§5), jamais
  par comparaison. Aucun sample, aucune banque, aucune imitation d'un timbre signé.

---

## 1. Constantes globales

| Paramètre | Valeur | Remarque |
|---|---|---|
| `SAMPLE_RATE` | `44_100` | identique au reste du pipeline |
| Tempo | **140 BPM**, 4/4 | |
| Tonalité | **ré mineur naturel** (`D`, `E`, `F`, `G`, `A`, `B♭`, `C`) | cohérent `fleet_battle` / `final_charge` |
| Longueur | **48 mesures** = **82,286 s** | dans la fenêtre 60–90 s du brief |
| `MOTIF` | `(0, +5, +3, +7)` demi-tons | offsets cumulés de `+5, −2, +4` — identique à `generate_music.py` |
| `SEED` | `0xAE6140` | « AE » + 140 BPM ; RNG propre au morceau |
| `TAIL_SECONDS` | `3.0` (132 300 échantillons) | ≥ RT60 du hall (2,90 s) — cf. §7 |

### 1.1 Grille d'échantillons — exacte, sans dérive

À 140 BPM et 44 100 Hz, **tout tombe sur un entier** :

| Unité | Échantillons | Secondes |
|---|---:|---:|
| Noire (temps) | **18 900** | 0,428571 |
| Croche | **9 450** | 0,214286 |
| Double-croche | **4 725** | 0,107143 |
| Mesure (4 temps) | **75 600** | 1,714286 |
| **Boucle (48 mesures)** | **3 628 800** | **82,2857** |
| Rendu total (boucle + queue) | 3 761 100 | 85,2857 |

Seule la **triple-croche vaut 2 362,5 échantillons** : elle n'apparaît que dans les roulements
(§5.12) ; calculer chaque position **en absolu depuis le début de la mesure** puis
`int(round(...))` — jamais par accumulation, pour éviter toute dérive.

C'est la première condition d'une boucle sans couture : **la boucle est exacte à l'échantillon
près, il n'y a rien à rogner**.

### 1.2 Bornes de sections (échantillon absolu)

| Section | Mesures | Début | Fin | Durée |
|---|---|---:|---:|---:|
| Intro | 1–8 | 0 | 604 800 | 13,714 s |
| Montée (*rise*) | 9–16 | 604 800 | 1 209 600 | 13,714 s |
| Drop | 17–32 | 1 209 600 | 2 419 200 | 27,429 s |
| Breakdown | 33–40 | 2 419 200 | 3 024 000 | 13,714 s |
| Reprise | 41–48 | 3 024 000 | 3 628 800 | 13,714 s |

Mesure `n` (1-indexée) → échantillon `(n - 1) * 75_600`.

### 1.3 Fréquences (Hz) — table de vérité

| Note | Oct. 1 | Oct. 2 | Oct. 3 | Oct. 4 | Oct. 5 |
|---|---:|---:|---:|---:|---:|
| **D** | 36,708 | 73,416 | 146,832 | 293,665 | 587,330 |
| E | — | 82,407 | 164,814 | 329,628 | 659,255 |
| **F** | — | 87,307 | 174,614 | 349,228 | 698,456 |
| **G** | — | 97,999 | 195,998 | 391,995 | 783,991 |
| **A** | 55,000 | 110,000 | 220,000 | 440,000 | 880,000 |
| B♭ | — | 116,541 | 233,082 | 466,164 | 932,328 |
| C | — | 130,813 | 261,626 | 523,251 | 1046,502 |

Les quatre notes en gras sont la cellule (§3.1).

---

## 2. Les 17 voix

Identifiants `snake_case` à reprendre dans le code. Chaque générateur de voix renvoie un signal
**normalisé à un pic de 1,0 pour une note ou un coup isolé** ; les gains du §6 sont donc des
gains de bus, directement comparables.

| Voix | Rôle | Nature |
|---|---|---|
| `drone` | fondation, présente presque partout | **périodique** (§7.2) |
| `pad` | lit d'accords tenus (cordes/nappe) | événement |
| `ostinato` | cordes, cellule en croches | événement |
| `braam` | cuivres graves, gestes de bascule | événement |
| `brass_cell` | cuivres énonçant la cellule | événement |
| `choir` | chœur synthétique, voyelles, **aucune parole** | événement |
| `clarion` | doublure aiguë de la cellule (reprise) | événement |
| `sub` | basse sinusoïdale tenue, sidechainée | événement |
| `bass_grit` | basse saw en croches (grain techno) | événement |
| `kick` | pouls 4/4 | événement |
| `taiko_low` / `taiko_mid` | percussions orchestrales | événement |
| `snare` | contretemps + roulements | événement |
| `hat` | doubles-croches | événement |
| `riser` | bruit filtré montant | événement |
| `impact` | point de bascule | événement |
| `reverse_riser` | scelle la boucle (mes. 48) | événement |

### 2.1 RNG — table d'offsets figée

`rng(voix) = np.random.default_rng(SEED + offset)`. **Un flux par voix**, jamais un RNG global
séquentiel : c'est exactement l'écueil signalé par ADR-0007 §3 (ajouter une voix décalerait le
bruit de toutes les suivantes). Avec cette table, une voix ajoutée plus tard ne change **aucun**
échantillon des voix existantes.

| Voix | offset | | Voix | offset |
|---|---:|---|---|---:|
| `braam` | 1 | | `ostinato` (désaccords) | 9 |
| `choir` | 2 | | `pad` (désaccords) | 10 |
| `taiko_low` / `taiko_mid` | 3 | | `kick` (clic) | 11 |
| `snare` | 4 | | `ir_hall_l` | 12 |
| `hat` | 5 | | `ir_hall_r` | 13 |
| `riser` | 6 | | `ir_plate_l` | 14 |
| `impact` | 7 | | `ir_plate_r` | 15 |
| `reverse_riser` | 8 | | `clarion` | 16 |
| | | | `bass_grit` | 17 |

---

## 3. Matériau

### 3.1 La cellule signature

Intervalles `+5, −2, +4` demi-tons → offsets `(0, +5, +3, +7)`. **En ré mineur : D – G – F – A.**
Les quatre notes sont diatoniques ; la cellule contient la quarte juste (D→G), le pas descendant
(G→F) et le saut vers la quinte (F→A). C'est ce que le joueur doit reconnaître.

- **Rétrograde** : `A – F – G – D` (intervalles `−4, +2, −5`) — également diatonique. **Seule
  variante autorisée** avec l'octaviation et l'augmentation.
- **Renversement interdit** : il produit un si naturel, hors du mode. Ne pas l'implémenter.

### 3.2 Échelle d'augmentation — l'argument central du morceau

La même cellule est énoncée à quatre échelles de temps. C'est ce qui fait qu'un joueur qui a
entendu le titre reconnaîtra le motif dégradé dans `boss_phase_1` ou `final_charge`.

| Voix | Durée par note | Facteur | Section |
|---|---|---:|---|
| `ostinato` | croche | ×1 | montée, drop, reprise |
| `brass_cell` / `clarion` (variante) | blanche | ×4 | fin de drop, reprise |
| `brass_cell` | ronde (1 mesure) | ×8 | drop, reprise |
| `choir` | 2 mesures | ×16 | **breakdown — la forme la plus large** |

### 3.3 Grille d'accords — dérivée de la cellule

Degrés de l'échelle indexés `0..6` = `D, E, F, G, A, B♭, C` ; triades diatoniques
(`0` = Dm, `2` = F, `3` = Gm, `5` = B♭, `6` = C).

Le cycle de quatre mesures du drop **harmonise la cellule** : chaque mesure porte une note de
cellule, l'accord est choisi pour la couleur qu'il lui donne.

| Mes. du cycle | Note de cellule | Accord | Fonction de la note dans l'accord |
|---|---|---|---|
| 1 | **D** | `0` — Dm | fondamentale |
| 2 | **G** | `5` — B♭ | sixte → B♭6 |
| 3 | **F** | `2` — F | fondamentale |
| 4 | **A** | `3` — Gm | neuvième → Gm(add9), tension qui relance |

Grille complète, une entrée par mesure :

| Mesures | Degrés | Lecture |
|---|---|---|
| 1–6 | `0 0 0 0 0 0` | pédale de i |
| 7–8 | `5 5` | VI |
| 9–16 | `0 0 5 5 2 2 6 6` | i – VI – III – VII (2 mes. chacun) ; le VII des mes. 15–16 tire vers le drop |
| 17–28 | `0 5 2 3` × 3 | cycle harmonisant la cellule |
| 29–32 | `0 5 6 6` | sortie de drop : le VII s'installe |
| 33–40 | `0 0 0 0 5 5 6 6` | breakdown |
| 41–46 | `0 5 2 3 0 5` | reprise, cycle du drop |
| **47–48** | `6 6` | **VII tenu → cadence sur la boucle** (§7.4) |

Deux couleurs assumées, à ne pas « corriger » :
- **Mes. 35–36** : la cellule du chœur pose un **G sur Dm** → Dm(add11) suspendu. C'est la
  respiration du breakdown, pas une faute.
- **Mes. 30** : `A` sur B♭ → B♭maj7 fugitif (blanche de passage).

---

## 4. Primitives de synthèse

Toutes implémentables en **numpy pur**, sans dépendance nouvelle. Les trois premières existent
déjà dans `generate_music.py` (`saw`, `sine`, `envelope`) ; les autres sont à ajouter dans le
nouveau script.

### 4.1 `saw_lp(f0, t, harmonics, fc, order=2, q=0.0)` — saw à filtre passe-bas balayable

Le cœur du morceau. Somme additive **harmonique par harmonique** (comme le `saw()` existant :
une passe de longueur N par harmonique, jamais de matrice `k × t` — 48 harmoniques × 7
oscillateurs × 150 k échantillons reste sous la seconde ; une matrice coûterait 400 Mo).

```
out = 0
for k in 1..harmonics:
    fk = f0 * k
    if fk >= SAMPLE_RATE/2: break
    g = 1.0 / sqrt(1.0 + (fk / fc)**(2*order))          # Butterworth |H| — fc peut être un tableau (balayage)
    g *= 1.0 + q * exp(-0.5 * ((fk - fc) / (0.30*fc))**2)  # bosse de résonance
    out += sin(2*pi*fk*t) * g / k
out *= 2/pi
```

`fc` est **soit un scalaire, soit un tableau de longueur N** : c'est ce qui donne « l'ouverture
progressive du filtre » sans écrire un IIR. `order=2` → 12 dB/oct. `q` entre 0 et 1,2.

### 4.2 `noise_band(rng, n, fc_curve, bw_ratio)` — bruit filtré balayable (STFT)

Pour le riser, l'impact, les cymbales. Filtrage par blocs, entièrement vectorisable :

- bruit blanc `rng.normal(0, 1, n)` ;
- STFT : blocs de **2048**, saut **1024**, fenêtre de Hann (somme des fenêtres = constante) ;
- pour chaque bloc `b`, `fc = fc_curve[b*1024]` ; masque appliqué au spectre :
  passe-bande gaussien `M(f) = exp(-0.5 * ((f - fc) / (bw_ratio * fc))**2)` (`bw_ratio ≈ 0,8`
  pour un riser large, `0,35` pour un balayage résonant) ; ou **passe-bas** Butterworth
  `M(f) = 1/sqrt(1 + (f/fc)**4)` là où c'est indiqué ;
- `irfft`, recomposition par *overlap-add*.

### 4.3 `sweep(f_start, f_end, n, curve="exp")` — sinus à fréquence balayée

`f(t) = f_start * (f_end/f_start)**(t/T)` (exp) ou `f_start + (f_end-f_start)*t/T` (lin), puis
`sin(2*pi*cumsum(f)/SAMPLE_RATE)`. C'est la technique déjà utilisée par le kick de
`generate_music.py` — phase continue garantie.

### 4.4 `env_exp(n, attack_ms, decay_s)` — enveloppe percussive

Identique à `envelope()` existante : montée linéaire sur `attack`, décroissance
`exp(-t/decay)`. Pour les voix tenues, on ajoute `env_ar(n, attack_ms, hold_s, release_s)` :
montée linéaire, plateau, descente `exp(-t/release)` bornée à zéro sur les 15 derniers ms.

### 4.5 `formant_voice(f0, t, vowel_a, vowel_b, morph)` — chœur

Synthèse additive à enveloppe de formants (voyelle, **aucune parole**, aucun sample) :

```
a_k = (1/k**0.7) * sum_i( A_i * exp(-((k*f0 - F_i)**2) / (2*B_i**2)) )   pour k = 1..48, k*f0 < 16 kHz
```

Formants interpolés linéairement entre `vowel_a` et `vowel_b` selon `morph ∈ [0,1]` :

| Voyelle | F1 (A, B) | F2 (A, B) | F3 (A, B) | F4 (A, B) |
|---|---|---|---|---|
| `/u/` (sombre) | 320 Hz (1,00 ; 80) | 800 Hz (0,35 ; 90) | 2400 Hz (0,08 ; 140) | 3200 Hz (0,04 ; 180) |
| `/a/` (ouverte) | 760 Hz (1,00 ; 100) | 1200 Hz (0,55 ; 120) | 2600 Hz (0,30 ; 160) | 3400 Hz (0,15 ; 200) |

Vibrato par voix : `f0 * (1 + 0.006 * sin(2*pi*5.2*t + phi))`, `phi` tiré du RNG `choir`.
Souffle : `noise_band(rng_choir, n, fc=4000, bw=0.6)` × l'enveloppe d'amplitude × **0,03**.

### 4.6 `convolve_ir(sig, ir)` — réverbération

`irfft(rfft(sig, L) * rfft(ir, L))`, `L = len(sig) + len(ir) - 1`, puis troncature à `len(sig)`.

| IR | Longueur | Décroissance | Pré-délai | Teinte | RT60 |
|---|---:|---|---:|---|---:|
| `hall` | 2,60 s | `exp(-t/0.42)` | 28 ms | `1/(1+(f/4200)**2)` | **2,90 s** |
| `plate` | 0,90 s | `exp(-t/0.16)` | 8 ms | `1/(1+(f/7000)**2)` | 1,10 s |

IR = bruit blanc × décroissance, **un flux RNG distinct par canal** (L et R décorrélés → largeur
stéréo réelle), teinte appliquée dans le domaine spectral, puis normalisation en énergie
(`ir /= sqrt(sum(ir**2))`). La queue de 3,0 s (§1) est choisie **≥ RT60 du hall** : ce qui est
perdu au-delà est à −62 dB.

### 4.7 Saturation

- **Kick / taiko / impact** : `x -> tanh(drive * x) / tanh(drive)`, `drive` donné par voix.
- **Bus master** : `y = tanh(x)` (pente unitaire en 0, colle les crêtes). Voir §6.3.

---

## 5. Recettes de timbre

Chaque timbre est une recette complète. Aucune n'est une comparaison ; toutes sont des nombres.

### 5.1 `drone`

| Composante | Fréquence | Gain |
|---|---|---|
| Sinus grave | D1 = 36,708 Hz | 0,50 |
| Sinus | D2 = 73,416 Hz | 0,35 |
| Sinus battant | D2 × 1,004 = 73,710 Hz | 0,25 |

- LFO d'amplitude sur les deux D2 : `1 + 0.15 * sin(2*pi*f_lfo*t)`, `f_lfo ≈ 0,08 Hz`.
- **Toutes ces fréquences (et le LFO) sont recalées sur la grille de boucle** — voir §7.2. Sans
  ça, la boucle claque.
- Aucun envoi de réverbe (voix périodique, §7.2). Mono, réparti L/R à parts égales.

### 5.2 `braam` — cuivres graves

Le geste, pas juste le son : gonflement + ouverture spectrale + retombée.

- **7 oscillateurs** `saw_lp` par note, désaccordés en cents :
  `[-14, -9, -4, 0, +4, +9, +14]` (+ un aléa `rng_braam.uniform(-3, +3)` cents par oscillateur,
  figé une fois pour toutes) → `f = f0 * 2**(cents/1200)`.
- Notes : **triade grave** D2 (73,4), A2 (110,0), D3 (146,8) ; en mesure 31–32 et 47–48,
  A2 + A3 seuls (pédale de dominante).
- `harmonics = 48`, `order = 2`.
- **Balayage de filtre (le braam)** : `fc(t)` = 300 Hz → 2 200 Hz sur les 260 premiers ms
  (courbe `1 - exp(-t/0.09)`), puis retombée exponentielle vers 900 Hz avec τ = 0,7 s.
  `q = 0.35`.
- **Enveloppe** : attaque **220 ms** (linéaire), plateau 400 ms, relâche `exp(-t/0.90)` ;
  longueur totale **2 mesures = 3,43 s**.
- **Gonflement de hauteur** : `f *= 1 + 0.004 * (1 - exp(-t/0.15))` (≈ +7 cents montants).
- **Stéréo** : oscillateur `i` panoramiqué linéairement de 0,15 (G) à 0,85 (D).
- Envoi `hall` : **0,40**.
- *Variante « braam lointain » (intro)* : mêmes oscillateurs, `fc` fixe **500 Hz**, `q = 0`,
  attaque 400 ms, gain 0,30, envoi `hall` **0,60**.

### 5.3 `brass_cell` — cuivres énonçant la cellule

- **5 oscillateurs** `saw_lp` désaccordés `[-10, -5, 0, +5, +10]` cents, **par note de la
  cellule**, empilée en **trois octaves** : `f0` (D3–A3), `f0/2` (D2–A2, gain 0,55),
  `f0*2` (D4–A4, gain 0,30).
- `harmonics = 40`, `fc = 2600 Hz` fixe, `q = 0.25`, `order = 2`.
- **Enveloppe** : attaque **60 ms**, plateau = 80 % de la durée de note, relâche
  `exp(-t/0.45)`. Ronde → note de 4 temps (1,714 s) ; blanche → 2 temps (0,857 s).
- Léger vibrato lent après 400 ms : `1 + 0.003 * sin(2*pi*4.2*(t-0.4))` (nul avant).
- Envoi `hall` : **0,22**. Stéréo : doublé, L désaccordé −6 cents / R +6 cents.

Fréquences de la cellule pour cette voix : **D3 146,83 · G3 196,00 · F3 174,61 · A3 220,00**
(+ octaves).

### 5.4 `ostinato` — cordes, cellule en croches

- **3 oscillateurs** `saw_lp` par note, désaccords tirés une fois du RNG `ostinato` dans
  `[-9, +9]` cents ; **double-piste vraie** : un jeu de désaccords pour la voie **gauche**, un
  second jeu indépendant pour la **droite** (pas de délai Haas — reste mono-compatible).
- Doublure à l'octave supérieure (`f*2`, gain **0,35**), activée **à partir de la mesure 25**.
- `harmonics = 16`, `order = 2`. `fc` : voir l'automation §6.2.
- **Enveloppe** (détaché) : attaque **12 ms**, longueur 0,9 × croche (8 505 éch.), décroissance
  `exp(-t/0.11)`.
- **Bruit d'archet** : à chaque attaque, `np.diff(rng.normal(0,1,220))` × `exp(-t/0.008)`,
  gain **0,06** — c'est ce qui donne le mordant, sans lui les cordes sonnent comme un orgue.
- **Registre fixe, harmonie mobile** : la cellule reste en D4–A4
  (**D4 293,66 · G4 392,00 · F4 349,23 · A4 440,00**) pendant que les accords bougent dessous.
  C'est l'harmonie statique du genre, et c'est diatonique sur les cinq accords de la grille.
- **Rythme** : croches, 8 notes par mesure → la cellule **deux fois par mesure**.
  Mesures impaires : cellule **directe** ; mesures paires : **rétrograde** (A F G D).
- Envoi `plate` : **0,14**. Pas de sidechain (c'est lui, la pulsation mélodique).

### 5.5 `pad` — lit d'accords

- Triade de l'accord courant (degrés `d`, `d+2`, `d+4`) en octave 3, **2 saws par voix**
  désaccordées ±5 cents (RNG `pad`), `harmonics = 12`.
- `fc` : automation §6.2 (suit l'ostinato). `q = 0.2`.
- Enveloppe par bloc d'accord : attaque **350 ms**, plateau, relâche **1,2 s** (elle déborde sur
  l'accord suivant : c'est voulu, ça soude la grille).
- Stéréo : voix `i` panoramiquée à `0.25 + 0.25*i`. Envoi `hall` **0,25**. Sidechain 0,35.

### 5.6 `choir` — chœur synthétique abstrait

- **3 voix par note d'accord**, chacune `formant_voice` (§4.5), désaccords ±(6 à 12) cents tirés
  du RNG `choir`, phases de vibrato indépendantes → ensemble choral sans sample.
- **Registre soprano** : notes d'accord en octave 4–5 (293–880 Hz) ; **doublure grave** une
  octave en dessous à **0,35** (le « pupitre d'hommes »).
- **La voix supérieure trace la cellule** : dans le breakdown, une note de cellule **toutes les
  deux mesures** (D → G → F → A, mes. 33-34 / 35-36 / 37-38 / 39-40) = augmentation ×16, la
  forme la plus large du morceau.
- **Morphing de voyelle** : `morph` interpolé **0 → 1** (`/u/` → `/a/`) sur les 8 mesures du
  breakdown ; fixe à `0.75` ailleurs. Le chœur s'ouvre sans changer de niveau.
- Enveloppe : attaque **400 ms** / relâche **1,4 s** (breakdown) ; attaque **90 ms** /
  relâche 0,8 s (reprise).
- Panoramique des trois voix : 0,20 / 0,50 / 0,80. Envoi `hall` : **0,55**, porté à **0,85**
  dans le breakdown. Sidechain 0,30 (là où il y a un kick).

### 5.7 `clarion` — doublure aiguë (reprise seulement)

- 2 × `saw_lp` désaccordées ±10 cents + un sinus à `2*f0` (gain 0,25).
- `harmonics = 20`, `fc = 5000 Hz`, `q = 0.4`.
- Registre **D5–A5** (587–880 Hz). Attaque 40 ms, relâche `exp(-t/0.6)`.
- Vibrato 5,5 Hz, profondeur 0,5 %, retardé de 250 ms.
- Stéréo large : deux rendus indépendants (désaccords différents) pan 0,30 / 0,70.
- Envoi `plate` : **0,30**.

### 5.8 `sub` — basse tenue

- **Sinus pur** sur la fondamentale de l'accord, **octave 2** (D2 73,42 · B♭2 116,54 ·
  F2 87,31 · G2 98,00 · C3 130,81) + un sinus une octave **en dessous** à **0,25**.
- Legato : une note par bloc d'accord, attaque 8 ms, relâche 30 ms (anti-clic aux changements).
- **Aucune mélodie** : fondamentales uniquement. Le rythme du sub, c'est le sidechain (§6.4).
- Mono, centre. Aucun envoi de réverbe (règle d'hygiène : les graves restent secs et mono).

### 5.9 `bass_grit` — basse saw (grain techno)

- 3 × `saw_lp` désaccordées `[-7, 0, +7]` cents sur la fondamentale de l'accord, **octave 2–3**.
- `harmonics = 10`, `fc = 700 Hz`, `q = 0.5`, `order = 2` → une basse trapue, sans aigu.
- Enveloppe : attaque **5 ms**, `exp(-t/0.10)`, longueur 0,9 × croche.
- **Rythme** : croches (positions 0, 2, 4, 6, 8, 10, 12, 14 en doubles-croches).
- Saturation `tanh(2.2 x)/tanh(2.2)`. Mono centre. Sidechain 0,50.

### 5.10 `kick`

| Composante | Recette |
|---|---|
| Corps | `sweep` : `f(t) = 48 + 130 * exp(-t/0.018)` Hz, via `cumsum` (phase continue) |
| Enveloppe corps | attaque **1,5 ms**, `exp(-t/0.11)`, longueur **0,32 s** |
| Clic | `np.diff(rng_kick.normal(0,1,120))` × `exp(-t/0.003)`, gain **0,25** |
| Saturation | `tanh(3.2 x)/tanh(3.2)` puis renormalisation à 1,0 |

- **Drop / reprise** : doubles-croches **0, 4, 8, 12** (4/4 plein).
  Dernière mesure de chaque phrase de 8 (`(mes-1) % 8 == 7`) : ajout d'un kick en **15** à 0,70.
- **Montée** : mêmes positions, gain 0,45 ; **clic désactivé jusqu'à la mesure 12**.
- **Intro** : positions **0 et 8** seulement (demi-temps), **corps seul** (clic à 0, saturation à
  0), `decay` 0,06 s → un battement mat. C'est le « kick filtré passe-bas » du brief : sur un
  kick sinusoïdal, la sourdine vient de la suppression du transitoire, pas d'un filtre.
- **Breakdown** : absent des mesures 33–38 ; revient mesures **39–40** sur les temps 1 et 3,
  corps seul, gain 0,35 (un cœur qui repart).
- Mono centre, aucun envoi de réverbe.

### 5.11 `taiko_low` / `taiko_mid`

| Composante | `taiko_low` | `taiko_mid` |
|---|---|---|
| Corps (sweep) | `62 + 40*exp(-t/0.05)` Hz | `96 + 55*exp(-t/0.045)` Hz |
| Partiel inharmonique | ×1,58 du corps, gain 0,32 | ×1,58, gain 0,35 |
| Peau (bruit) | `np.diff(noise)` × `exp(-t/0.030)`, gain 0,18 | idem, gain 0,22 |
| Enveloppe | attaque 2 ms, `exp(-t/0.28)`, 0,55 s | attaque 2 ms, `exp(-t/0.20)`, 0,42 s |
| Saturation | `tanh(2.0 x)/tanh(2.0)` | idem |
| Stéréo | centre | pan 0,62 |

Le partiel à ×1,58 (non entier) est ce qui fait la membrane plutôt que la note.

**Rythme** (positions en doubles-croches, 0–15), deux motifs alternés :

| | `taiko_low` | `taiko_mid` |
|---|---|---|
| Motif A (mesures impaires) | 0, 6, 10 | 4, 12, 14 |
| Motif B (mesures paires) | 0, 3, 6, 10 | 4, 12 |

**Fill** de fin de phrase (toutes les 4 mesures, dernière mesure) : `taiko_mid` sur
10, 11, 12, 13, 14, 15 avec un gain linéaire 0,50 → 1,00.
Envoi `hall` : **0,18**. Jitter de gain ±5 % (RNG `taiko`) — c'est ce qui évite la machine.

### 5.12 `snare` — caisse claire orchestrale

- Bruit `rng_snare.normal(0,1,n)` × 0,80 + sinus 190 Hz × 0,35, enveloppe attaque 1 ms,
  `exp(-t/0.075)`, longueur 0,22 s. Timbre (grésil) : `np.diff` du bruit, gain 0,20.
- **Contretemps** (drop/reprise) : doubles-croches **4** et **12**, gain de bus 0,30, précédés
  d'un **flam** 40 ms avant à ×0,35.
- **Roulements** :
  - mesure 15 : croches (0, 2, …, 14), gain 0,40 → 0,60 ;
  - mesure 16 : doubles-croches sur les temps 1–2, **triples-croches** sur les temps 3–4,
    gain 0,60 → **1,00**, coupe nette 60 ms avant la mesure 17 ;
  - mesure 40 : mêmes règles, gain plafonné à 0,80.
- Envoi `plate` : **0,25**. Pan 0,45.

### 5.13 `hat`

- Fermé : `np.diff(np.diff(rng_hat.normal(0,1,n+2)))` (double dérivée = passe-haut raide) ×
  `exp(-t/0.022)`, longueur 60 ms.
- Ouvert : simple `np.diff`, `exp(-t/0.16)`, longueur 0,22 s.
- **Rythme** : les **16 doubles-croches**. Gains :
  `0.30` si `pos % 4 == 0` ; `0.75` si `pos % 2 == 1` ; `0.50` sinon.
  Jitter ±8 % (RNG `hat`).
- Hat ouvert : position **14**, gain 0,50, une mesure sur deux.
- Pan alterné 0,45 / 0,55 par double-croche. Envoi `plate` : 0,05.

### 5.14 `riser` — bruit filtré montant

Deux couches superposées, sur **2 mesures** (3,43 s) :

1. **Bruit balayé** : `noise_band` (§4.2), `fc` **exponentiel 300 Hz → 9 000 Hz**,
   `bw_ratio = 0.8`. Amplitude `(t/T)**2` (0 → 1).
2. **Sinus balayé** : `sweep` exponentiel **220 Hz → 880 Hz** (A5), gain 0,20. Il atterrit sur
   la **dominante A**, que le drop résout sur D. Le riser est donc **harmonique**, pas décoratif.

**Coupe** : le riser s'arrête **60 ms (2 646 éch.) avant** le premier temps de la section
suivante, avec un fondu linéaire de 30 ms. Le trou est intentionnel : c'est ce qui fait exister
l'impact.

Occurrences : mesures **15–16** (gain 0,50), mesure **40** (1 mesure seulement, gain 0,35).
Envoi `plate` : 0,20.

### 5.15 `impact` — point de bascule

Trois composantes sommées puis `tanh(1.8 x)/tanh(1.8)` :

| Composante | Recette | Gain |
|---|---|---|
| Boum sub | `sweep` linéaire **90 Hz → 38 Hz** sur 0,60 s, env. attaque 2 ms `exp(-t/0.35)` | 1,00 |
| Corps | `noise_band` passe-bas `fc = 1800 Hz`, env. attaque 1 ms `exp(-t/0.55)`, 1,6 s | 0,55 |
| Éclat | `np.diff(np.diff(bruit))` × `exp(-t/0.60)`, 1,6 s | 0,22 |

Longueur totale **2,0 s**. Mono centre (le boum), l'éclat élargi ±0,25 de pan. Envoi `hall` :
**0,60**. Occurrences : **mesure 1** (0,75), **mesure 17** (0,90), **mesure 41** (0,80).

### 5.16 `reverse_riser` — sceau de boucle (mesure 48)

- `noise_band`, `fc` **exponentiel 200 Hz → 6 000 Hz**, `bw_ratio = 0.6`, amplitude `(t/T)**1.7`,
  longueur **1 mesure (1,714 s)** — puis **inversion temporelle ? non** : il est déjà construit
  montant, on le laisse tel quel. (L'effet « reverse » vient de l'enveloppe qui gonfle, pas d'un
  retournement de buffer.)
- Il **culmine 20 ms avant la fin de la boucle**, puis **fondu linéaire de 20 ms à zéro**, se
  terminant exactement à l'échantillon 3 628 799.
- Envoi `hall` : **0,50**. Sa queue de réverbe déborde de la boucle → elle est **repliée** (§7.3)
  et retombe pile sur l'impact de la mesure 1. C'est ce qui rend la couture inaudible.
- Gain de bus : 0,45. Stéréo : deux rendus décorrélés (RNG L / RNG R).

---

## 6. Mixage

### 6.1 Table de gains (linéaires, pré-master)

Chaque voix est normalisée à un pic de 1,0 par note isolée (§2), donc ces gains sont des gains
de bus directement comparables. `—` = voix absente.

| Voix | Intro | Montée | Drop | Breakdown | Reprise |
|---|---:|---:|---:|---:|---:|
| `drone` | 0,55 | 0,40 | 0,22 | 0,30 | 0,20 |
| `pad` | — | 0,28 | 0,30 | 0,18 | 0,34 |
| `ostinato` | — | 0,30 | 0,42 | — | 0,46 |
| `braam` | 0,30 *(lointain)* | 0,35 | 0,55 | 0,25 *(mes. 40)* | 0,55 |
| `brass_cell` | — | — | 0,60 | — | 0,65 |
| `choir` | — | 0,14 | 0,26 | **0,62** | 0,40 |
| `clarion` | — | — | — | — | 0,30 |
| `sub` | 0,10 | 0,30 | 0,62 | 0,18 *(mes. 39–40)* | 0,62 |
| `bass_grit` | — | 0,20 | 0,32 | — | 0,32 |
| `kick` | 0,28 | 0,45 | 0,85 | 0,35 *(mes. 39–40)* | 0,85 |
| `taiko_low` | — | 0,42 | 0,62 | — | 0,66 |
| `taiko_mid` | — | 0,30 | 0,48 | — | 0,52 |
| `snare` | — | 0,35 *(roulement)* | 0,30 | 0,25 *(mes. 40)* | 0,32 |
| `hat` | — | 0,22 | 0,34 | — | 0,34 |
| `riser` | — | 0,50 *(mes. 15–16)* | — | 0,35 *(mes. 40)* | — |
| `impact` | 0,75 *(mes. 1)* | — | 0,90 *(mes. 17)* | — | 0,80 *(mes. 41)* |
| `reverse_riser` | — | — | — | — | 0,45 *(mes. 48)* |

Le crescendo de section n'est **pas** un gain global : il est produit par l'**ajout de voix** et
par l'**ouverture du filtre** (§6.2). C'est ce qui fait qu'un drop « ouvre » au lieu de « monter
le volume ».

### 6.2 Automation de filtre (`fc` de `saw_lp`)

S'applique à `ostinato`, `pad`, `bass_grit`.

| Section | `fc` | `q` |
|---|---|---|
| Intro | (voix absentes ; `braam` lointain à 500 Hz fixe) | 0 |
| **Montée (mes. 9→16)** | **exponentielle 220 Hz → 6 000 Hz** : `fc(u) = 220 * (6000/220)**u`, `u` = progression 0→1 sur les 8 mesures | **0,4 → 1,1** (linéaire) |
| Drop | 7 500 Hz fixe | 0,30 |
| Breakdown | `pad` seul, 1 200 Hz fixe | 0,20 |
| Reprise | 9 000 Hz fixe | 0,25 |

(`bass_grit` garde son `fc = 700 Hz` propre : il n'est pas concerné par le balayage, sinon la
basse disparaît pendant la montée.)

### 6.3 Chaîne master (ordre strict)

1. Somme des voix **sèches** (bus `dry`).
2. Somme des envois → bus `hall` et `plate`, **une seule convolution par bus** (§4.6).
3. `mix = dry + hall + plate`.
4. **Repli de la queue** (§7.3) → buffer de longueur exactement 3 628 800.
5. **Passe-haut Butterworth 2ᵉ ordre à 30 Hz**, appliqué par `rfft`/`irfft` **sur le buffer de
   boucle** : `H(f) = 1/sqrt(1 + (30/f)**4)`, `H(0) = 0`. Le filtrage circulaire par FFT est ici
   un **avantage** : il préserve exactement la périodicité de la boucle. Il retire l'énergie
   inaudible qui mangeait de la marge et que Vorbis coderait pour rien.
6. **Colle** : `y = tanh(x)` (pente 1 en zéro, écrête doucement au-delà).
7. Normalisation de crête à **0,89** (identique aux neuf pistes adaptatives).
8. Écriture PCM 16 bits stéréo → `assets/source/audio/music/main_theme.wav`.

`build_audio.py` fait ensuite le reste (DC, −1 dBFS, **pas de fondu de sortie** sur la musique :
`master(..., fade=False)`, déjà le cas — ne rien changer).

### 6.4 Sidechain (le « pouls »)

Tableau de gain construit une fois à partir de la grille de kicks :

```
p(t) = 1 - depth * exp(-dt / 0.10)     # dt = temps écoulé depuis le dernier kick
```

| Voix | `depth` |
|---|---:|
| `sub` | **0,72** |
| `bass_grit` | 0,50 |
| `pad` | 0,35 |
| `choir` | 0,30 |
| `drone` | 0,25 |
| `ostinato`, cuivres, percussions | 0 |

Actif dans **montée, drop, reprise** ; inactif dans l'intro et le breakdown (mes. 33–38).
C'est le seul « traitement de production » emprunté au genre techno — un enveloppement de gain,
aucun matériau.

### 6.5 Niveau de livraison — marge pour les SFX de menu

Le WAV est normalisé comme les autres pistes ; la marge doit donc venir de la lecture :

- **RMS intégré cible du mix : 0,14 à 0,18** (≈ −17 à −15 dBFS). À vérifier par assertion (§9) :
  si le RMS dépasse 0,20, la piste est trop écrasée — **baisser les gains percussifs**, ne pas
  augmenter le drive du `tanh`.
- **Recommandation d'intégration** (hors périmètre de ce livrable) : `AudioStreamPlayer` du titre
  sur le bus `Music` à **`volume_db = -7.0`**, fondu d'entrée 1,2 s, fondu de sortie 0,4 s sur
  Entrée. Les cues de menu conservent ainsi leur réserve.

### 6.6 Stéréo — règles

- **Graves mono** : `kick`, `sub`, boum de l'`impact` strictement au centre.
- **Aucune inversion de polarité** nulle part : le mix doit rester compatible mono.
- La largeur vient de **sources décorrélées** (désaccords indépendants L/R, IR de réverbe L/R
  décorrélées), jamais d'un délai de type Haas sur une voix rythmique.

---

## 7. Bouclage sans couture — le mécanisme, point par point

Quatre garanties indépendantes. Les quatre sont nécessaires.

### 7.1 Grille exacte

48 mesures = **3 628 800 échantillons pile** (§1.1). Aucun arrondi, aucun rognage, aucun
crossfade. La boucle n'est pas « recollée », elle est **juste**.

### 7.2 Deux buffers : périodique et événementiel

C'est le piège principal de l'implémentation.

- **`body`** — longueur **3 628 800** : uniquement les voix **continues et périodiques**, à ce
  jour la seule voix `drone`. **Fréquences recalées sur la grille de boucle** :

  ```
  f_loop = round(f * LOOP_SECONDS) / LOOP_SECONDS      # LOOP_SECONDS = 82.285714…
  ```

  Résolution : 1 / 82,2857 = **0,01215 Hz** (≈ 0,6 cent à 36 Hz — inaudible). Valeurs de
  contrôle : D1 36,708 → **36,7135 Hz** (3021 cycles) ; D2 73,416 → **73,4149 Hz** (6041) ;
  battement 73,710 → **73,7188 Hz** (6066) ; LFO 0,08 → **0,08507 Hz** (7 cycles).
  Le battement lui-même (0,304 Hz) boucle alors exactement, par construction.
  **Le `drone` ne reçoit aucune réverbe** (une convolution détruirait sa périodicité) et
  **n'est pas rendu dans la queue**.

- **`ring`** — longueur **3 628 800 + 132 300** : toutes les autres voix, plus les deux bus de
  réverbe. Elles ont le droit de sonner au-delà de la fin.

### 7.3 Repli de la queue

Après convolution des réverbes, **sur `ring` uniquement** :

```
ring[:TAIL] += ring[LOOP : LOOP + TAIL]
ring = ring[:LOOP]
mix  = body + ring
```

La résonance qui déborde retombe donc **sur elle-même** — technique déjà en place dans
`generate_music.py`. Conséquence directe : `mix[0]` vaut exactement ce que le signal aurait valu
à l'instant `LOOP` s'il avait continué. **La continuité à la couture est vraie par construction,
pas approchée.**

Appliquer le repli **avant** le passe-haut et la normalisation (§6.3), jamais après.

### 7.4 La couture est un événement musical

Cacher une couture est fragile. On la **met en scène** :

1. Mesures 47–48 : l'harmonie tient le **VII (C)**, les cuivres tiennent **A** (dominante).
2. Mesure 48 : les percussions s'éclaircissent après le temps 2, le `reverse_riser` gonfle et
   s'éteint en 20 ms **pile à l'échantillon 3 628 799**.
3. Échantillon 0 : **impact** + retour du **i (Dm)** + `drone`.

La couture est donc une **cadence VII → i doublée d'une résolution A → D**, ponctuée par un
impact dont le transitoire masquerait de toute façon n'importe quel micro-défaut. À la première
lecture (démarrage depuis le silence), l'impact de la mesure 1 fait aussi une ouverture franche.

### 7.5 Côté moteur

Le WAV est encodé en OGG Vorbis par `build_audio.py` (`-q:a 4`, `-bitexact`). Activer sur le
`AudioStreamOggVorbis` importé : **`loop = true`, `loop_offset = 0`**. Ne **pas** ajouter de
fondu ni de crossfade côté Godot : ils réintroduiraient le trou qu'on vient d'éliminer.

---

## 8. Plan mesure par mesure

| Mes. | Section | Accord | Cellule | Événements |
|---:|---|---|---|---|
| 1 | Intro | Dm | — | **impact** (couture) ; `drone` ; `sub` 0,10 |
| 2 | Intro | Dm | — | |
| 3 | Intro | Dm | — | **braam lointain** (LP 500 Hz) ; `kick` corps (temps 1 et 3) |
| 4 | Intro | Dm | — | |
| 5–6 | Intro | Dm | — | |
| 7 | Intro | B♭ | — | **braam lointain** #2 |
| 8 | Intro | B♭ | — | temps 4 : bref balayage de bruit (`noise_band`, 300→2000 Hz, 0,4 s) |
| 9 | Montée | Dm | ×1 | entrée `ostinato` (fc 220 Hz), `taiko`, `hat`, `bass_grit` |
| 10 | Montée | Dm | ×1 | |
| 11–12 | Montée | B♭ | ×1 | `kick` : clic activé à partir de la mes. 12 |
| 13–14 | Montée | F | ×1 | `choir` 0,14 entre ; le filtre continue de s'ouvrir |
| 15 | Montée | C | ×1 | **riser** démarre ; roulement de `snare` en croches |
| 16 | Montée | C | ×1 | riser au sommet ; roulement 16ᵉ → 32ᵉ ; **coupe 60 ms avant la mes. 17** |
| **17** | **Drop** | **Dm** | **D** (ronde) | **impact** ; `kick` plein ; `sub` ; `braam` ; `brass_cell` |
| 18 | Drop | B♭ | **G** | |
| 19 | Drop | F | **F** | |
| 20 | Drop | Gm | **A** | |
| 21 | Drop | Dm | D | `braam` relancé |
| 22–24 | Drop | B♭ / F / Gm | G / F / A | |
| 25 | Drop | Dm | D | `braam` ; **octave supérieure de l'`ostinato` activée** |
| 26–28 | Drop | B♭ / F / Gm | G / F / A | |
| 29 | Drop | Dm | **D, G** (blanches) | `braam` ; la cellule accélère (×4) |
| 30 | Drop | B♭ | **F, A** (blanches) | |
| 31 | Drop | C | **A** tenu | `braam` A2+A3 (pédale de dominante) |
| 32 | Drop | C | A tenu | percussions coupées au temps 3 ; gonflement de bruit vers le breakdown |
| 33–34 | Breakdown | Dm | **D** (chœur, ×16) | **chœur seul**, `hall` 0,85, aucun pouls ; voyelle `/u/` |
| 35–36 | Breakdown | Dm | **G** | Dm(add11) — suspension assumée |
| 37–38 | Breakdown | B♭ | **F** | morphing de voyelle en cours |
| 39 | Breakdown | C | **A** | `kick` corps (temps 1 et 3), `sub` 0,18 — le pouls repart |
| 40 | Breakdown | C | A | voyelle `/a/` atteinte ; `riser` + roulement ; `braam` gonfle ; **coupe 60 ms** |
| **41** | **Reprise** | **Dm** | **D** (ronde) | **impact** ; **tutti** |
| 42–44 | Reprise | B♭ / F / Gm | G / F / A | |
| 45 | Reprise | Dm | **D, G** (blanches) | entrée `clarion` (cellule à l'octave supérieure) |
| 46 | Reprise | B♭ | **F, A** (blanches) | |
| 47 | Reprise | **C** | **A** tenu | cuivres + chœur + clarion tiennent A ; `ostinato` en rétrograde, ×0,6 |
| 48 | Reprise | **C** | A tenu | percussions s'éclaircissent après le temps 2 ; **`reverse_riser`** ; fin exacte |

---

## 9. Assertions d'implémentation (à coder dans le générateur)

Ces vérifications transforment la spec en test. Elles doivent toutes passer.

| # | Assertion | Valeur attendue |
|---|---|---|
| 1 | Longueur de la boucle | **exactement 3 628 800** frames |
| 2 | Aucun `NaN` / `inf` dans le mix | — |
| 3 | Crête **avant** `tanh` | `< 1,6` (sinon revoir §6.1, pas le drive) |
| 4 | Crête après normalisation | `0,89 ± 0,001` |
| 5 | RMS intégré | **∈ [0,14 ; 0,18]** (§6.5) |
| 6 | Continuité de couture | `abs(x[0] - x[-1]) < 0,08` par canal (contrôle de fumée ; la vraie garantie est §7.3) |
| 7 | Déterminisme | deux exécutions → **SHA-256 identique** du WAV |
| 8 | Fréquences périodiques recalées | `f * 82.285714` entier à `1e-6` près pour toute voix du buffer `body` |

Temps de rendu attendu : **1 à 3 minutes** (les braams et le chœur dominent). Travailler en
`float32` pour les accumulations harmoniques, `float64` pour la somme master.

---

## 10. Limites connues et arbitrages

- **La spec dépasse le gabarit des neuf pistes adaptatives.** `generate_music.py` est un moteur à
  couches uniformes ; ce morceau demande de l'**automation par section** (filtre, gains, motifs).
  Il faut donc un script **séparé** (`generate_main_theme.py`), comme le brief le prévoit — ne pas
  chercher à faire rentrer le thème dans `STATES`. Les primitives §4.1–4.7 peuvent en revanche
  être partagées plus tard par une petite factorisation (`tools/audio/synth.py`) : c'est une
  suggestion, pas une exigence.
- **Le chœur à formants est le poste le plus coûteux** (3 voix × 3–4 notes × 48 harmoniques). Si
  le rendu devient pénible, réduire `harmonics` à 32 (perte : un peu de brillance dans la voyelle
  `/a/`) avant de toucher au nombre de voix — c'est le désaccord entre voix qui fait le chœur.
- **Vorbis à `-q:a 4` est lossy** : un transitoire peut se salir de quelques ms à la couture. Le
  dispositif du §7.4 (impact sur la couture) rend cela inaudible. Si un clic apparaît malgré tout,
  **vérifier `loop`/`loop_offset` sur la ressource importée avant de soupçonner le signal**.
- **La marge de niveau vis-à-vis des SFX de menu ne peut pas être livrée dans le fichier** : le
  master normalise à −1 dBFS. Elle est donc portée par le `volume_db` du lecteur (§6.5). C'est la
  seule exigence du brief que ce livrable ne peut pas satisfaire seul ; elle est explicitement
  transmise à l'intégration.
- **Suspension mes. 35–36** (G sur Dm) : c'est une décision, pas une erreur. Si elle déplaît en
  écoute, la correction minimale est de passer l'accord des mesures 35–36 au degré `3` (Gm) —
  jamais de changer la note de la cellule.
- La distinction `pad` / `ostinato` (deux voix de cordes) est ce qui empêche l'ensemble de sonner
  comme un seul synthé large. Ne pas les fusionner pour économiser du code.

---

## 11. Conformité au brief

| Critère | Où |
|---|---|
| Cellule `+5, −2, +4` énoncée et **seul** matériau mélodique | §0, §3.1, §3.2, §3.3, §8 |
| Chaque timbre décrit par une recette numpy implémentable | §4, §5 |
| Chaque section : durée en mesures, grille d'accords, voix actives | §1.2, §3.3, §6.1, §8 |
| Bouclage sans couture explicité | §7 (grille exacte, deux buffers, repli, cadence) |
| Aucune œuvre / artiste / titre cité comme modèle | §0 — aucun nom nulle part dans ce document |
| Tempo, tonalité, durée 60–90 s, structure en 5 sections | §1, §1.2 |
| Synthèse pure, déterministe, aucune dépendance nouvelle | §2.1, §4, §9 (assertion 7) |
| Crête sous −1 dBFS, pas de clipping, marge de niveau | §6.3, §6.5, §9 |
