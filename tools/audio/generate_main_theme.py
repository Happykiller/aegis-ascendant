#!/usr/bin/env python3
"""Génère le thème principal d'Aegis Ascendant (écran titre).

Implémente `docs/forge/output/main_theme_spec.md` : tempos, grille d'accords, recettes de
timbre, table de gains et mécanisme de bouclage y sont normatifs. Chaque nombre de ce script
vient de la spec ; les §N cités en commentaire renvoient à ses sections.

Hybride orchestral sur socle techno, 140 BPM, ré mineur, 48 mesures (82,286 s), bouclé.
Synthèse additive/soustractive pure — aucun sample, aucune banque, aucune dépendance nouvelle.

Le morceau ne rentre pas dans le gabarit `STATES` de `generate_music.py` (moteur à couches
uniformes) : il exige de l'automation par section. D'où ce script séparé (spec §10).

Sortie : assets/source/audio/music/main_theme.wav (gitignoré).
Mastering et encodage OGG : tools/audio/build_audio.py (inchangé).

Usage : python3 tools/audio/generate_main_theme.py
"""

from __future__ import annotations

import hashlib
import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44_100
OUTPUT = Path("assets/source/audio/music/main_theme.wav")

# --- Grille temporelle (spec §1.1) : à 140 BPM / 44,1 kHz, tout tombe sur un entier. -------
SIXTEENTH = 4_725
BEAT = 18_900
BAR = 75_600
BARS = 48
LOOP = BARS * BAR                  # 3 628 800 échantillons pile
TAIL = 132_300                     # 3,0 s ≥ RT60 du hall (2,90 s)
TOTAL = LOOP + TAIL
LOOP_SECONDS = LOOP / SAMPLE_RATE  # 82,285714…

SEED = 0xAE6140

## Un flux de RNG par voix (spec §2.1). Une voix ajoutée plus tard ne décale le bruit
## d'aucune autre — c'est l'écueil signalé par ADR-0007 §3, évité par construction.
RNG_OFFSET = {
    "braam": 1, "choir": 2, "taiko": 3, "snare": 4, "hat": 5, "riser": 6,
    "impact": 7, "reverse_riser": 8, "ostinato": 9, "pad": 10, "kick": 11,
    "ir_hall_l": 12, "ir_hall_r": 13, "ir_plate_l": 14, "ir_plate_r": 15,
    "clarion": 16, "bass_grit": 17,
}

## Ré mineur naturel : D, E, F, G, A, B♭, C (spec §1).
SCALE = (0, 2, 3, 5, 7, 8, 10)
## Cellule signature : intervalles +5, −2, +4 → offsets cumulés. En ré mineur : D, G, F, A.
MOTIF = (0, 5, 3, 7)
D1 = 36.708

## Grille d'accords, une entrée par mesure (spec §3.3). Degrés : 0=Dm 2=F 3=Gm 5=B♭ 6=C.
CHORDS = (
    [0] * 6 + [5] * 2                       # 1–8    intro : pédale de i, puis VI
    + [0, 0, 5, 5, 2, 2, 6, 6]              # 9–16   montée : i VI III VII
    + [0, 5, 2, 3] * 3                      # 17–28  drop : le cycle harmonise la cellule
    + [0, 5, 6, 6]                          # 29–32  sortie de drop
    + [0, 0, 0, 0, 5, 5, 6, 6]              # 33–40  breakdown
    + [0, 5, 2, 3, 0, 5]                    # 41–46  reprise
    + [6, 6]                                # 47–48  VII tenu → cadence sur la boucle
)
assert len(CHORDS) == BARS

SECTIONS = (("intro", 1, 8), ("rise", 9, 16), ("drop", 17, 32),
            ("breakdown", 33, 40), ("reprise", 41, 48))

## Table de gains (spec §6.1). Le crescendo vient de l'ajout de voix et de l'ouverture du
## filtre, jamais d'un gain global : c'est ce qui fait qu'un drop « ouvre » au lieu de monter.
GAIN = {
    "drone":         dict(intro=0.55, rise=0.40, drop=0.22, breakdown=0.30, reprise=0.20),
    "pad":           dict(intro=0.00, rise=0.28, drop=0.30, breakdown=0.18, reprise=0.34),
    "ostinato":      dict(intro=0.00, rise=0.30, drop=0.42, breakdown=0.00, reprise=0.46),
    "braam":         dict(intro=0.30, rise=0.35, drop=0.55, breakdown=0.25, reprise=0.55),
    "brass_cell":    dict(intro=0.00, rise=0.00, drop=0.60, breakdown=0.00, reprise=0.65),
    "choir":         dict(intro=0.00, rise=0.14, drop=0.26, breakdown=0.62, reprise=0.40),
    "clarion":       dict(intro=0.00, rise=0.00, drop=0.00, breakdown=0.00, reprise=0.30),
    "sub":           dict(intro=0.10, rise=0.30, drop=0.62, breakdown=0.18, reprise=0.62),
    "bass_grit":     dict(intro=0.00, rise=0.20, drop=0.32, breakdown=0.00, reprise=0.32),
    "kick":          dict(intro=0.28, rise=0.45, drop=0.85, breakdown=0.35, reprise=0.85),
    "taiko_low":     dict(intro=0.00, rise=0.42, drop=0.62, breakdown=0.00, reprise=0.66),
    "taiko_mid":     dict(intro=0.00, rise=0.30, drop=0.48, breakdown=0.00, reprise=0.52),
    "snare":         dict(intro=0.00, rise=0.35, drop=0.30, breakdown=0.25, reprise=0.32),
    "hat":           dict(intro=0.00, rise=0.22, drop=0.34, breakdown=0.00, reprise=0.34),
    "riser":         dict(intro=0.25, rise=0.50, drop=0.00, breakdown=0.35, reprise=0.00),
    "impact":        dict(intro=0.75, rise=0.00, drop=0.90, breakdown=0.00, reprise=0.80),
    "reverse_riser": dict(intro=0.00, rise=0.00, drop=0.00, breakdown=0.00, reprise=0.45),
}

## Fader de bus master. Les gains du §6.1 sont des rapports entre voix, et chaque voix sort
## normalisée à 1,0 par note (§2) : leur somme dépasse forcément le plein échelle. Un facteur
## unique, appliqué avant le `tanh`, ramène la crête sous la limite de l'assertion §9-3 **sans
## toucher à un seul équilibre** — c'est le fader, pas le drive (que la spec interdit de monter).
## Il règle aussi la dynamique : moins on entre fort dans le `tanh`, moins il colle, plus la
## piste respire — et c'est exactement ce que la fenêtre de RMS du §6.5 cherche à préserver.
MASTER_TRIM = 0.40

## Écart assumé à la table du §6.1, et c'est la spec elle-même qui le prescrit : rendue telle
## quelle, la piste sort à un RMS de 0,190 — au-dessus de la fenêtre [0,14 ; 0,18] du §6.5, donc
## trop écrasée pour laisser leur réserve aux SFX de menu. Le remède imposé par le §6.5 est de
## baisser les **percussions**, jamais de monter le drive. Ce facteur est ce remède, rendu
## visible plutôt que fondu dans la table.
PERCUSSION_TRIM = 0.85
PERCUSSIVE = ("kick", "taiko_low", "taiko_mid", "snare", "hat")
for _voice in PERCUSSIVE:
    for _section in GAIN[_voice]:
        GAIN[_voice][_section] *= PERCUSSION_TRIM

## Profondeur de sidechain par voix (spec §6.4). C'est le seul emprunt à la production techno :
## une enveloppe de gain, aucun matériau.
SIDECHAIN = {"sub": 0.72, "bass_grit": 0.50, "pad": 0.35, "choir": 0.30, "drone": 0.25}

## Envois de réverbe (spec §5).
HALL_SEND = {"braam": 0.40, "brass_cell": 0.22, "pad": 0.25, "choir": 0.55,
             "taiko_low": 0.18, "taiko_mid": 0.18, "impact": 0.60, "reverse_riser": 0.50}
PLATE_SEND = {"ostinato": 0.14, "clarion": 0.30, "snare": 0.25, "hat": 0.05, "riser": 0.20}

## Formants du chœur (spec §4.5) : (F, A, B) par formant. Aucune parole, une voyelle.
VOWEL_U = ((320.0, 1.00, 80.0), (800.0, 0.35, 90.0), (2400.0, 0.08, 140.0), (3200.0, 0.04, 180.0))
VOWEL_A = ((760.0, 1.00, 100.0), (1200.0, 0.55, 120.0), (2600.0, 0.30, 160.0), (3400.0, 0.15, 200.0))


def rng(voice: str) -> np.random.Generator:
    return np.random.default_rng(SEED + RNG_OFFSET[voice])


def bar_start(bar: int) -> int:
    """Mesure 1-indexée -> échantillon absolu."""
    return (bar - 1) * BAR


def at(bar: int, sixteenth: float) -> int:
    """Position en doubles-croches depuis le début de la mesure, calculée en absolu :
    jamais par accumulation, sinon les triples-croches font dériver la grille (spec §1.1)."""
    return bar_start(bar) + int(round(sixteenth * SIXTEENTH))


def section_of(bar: int) -> str:
    for name, first, last in SECTIONS:
        if first <= bar <= last:
            return name
    raise ValueError("mesure hors morceau: %d" % bar)


def note_hz(degree: int, octave: int) -> float:
    """Degré d'échelle (peut dépasser l'octave) et octave (celle de D) -> fréquence."""
    span = len(SCALE)
    semitones = SCALE[degree % span] + 12 * (degree // span)
    return D1 * 2.0 ** (octave - 1) * 2.0 ** (semitones / 12.0)


def cell_hz(index: int, octave: int) -> float:
    """Note `index` de la cellule signature, dans l'octave donnée."""
    return D1 * 2.0 ** (octave - 1) * 2.0 ** (MOTIF[index % 4] / 12.0)


def triad(degree: int, octave: int) -> tuple[float, float, float]:
    return tuple(note_hz(degree + step, octave) for step in (0, 2, 4))


# --- Primitives de synthèse (spec §4) ------------------------------------------------------

def _time(n: int) -> np.ndarray:
    return np.arange(n, dtype=np.float64) / SAMPLE_RATE


def saw_lp(f0: float, n: int, harmonics: int, fc, order: int = 2, q: float = 0.0,
           pitch: np.ndarray | None = None) -> np.ndarray:
    """Dent de scie additive à passe-bas Butterworth balayable (spec §4.1).

    `fc` est un scalaire ou un tableau de longueur n : c'est ce qui donne l'ouverture
    progressive du filtre sans écrire un IIR. `pitch` module la fréquence (gonflement,
    vibrato) ; la phase passe alors par un cumsum, donc reste continue.

    Somme harmonique par harmonique — jamais de matrice k×t : 48 harmoniques × 150 k
    échantillons en matrice coûteraient des centaines de Mo pour rien.
    """
    if pitch is None:
        phase = 2.0 * np.pi * f0 * _time(n)
        f_max = f0
    else:
        phase = 2.0 * np.pi * np.cumsum(f0 * pitch) / SAMPLE_RATE
        f_max = f0 * float(np.max(pitch))
    out = np.zeros(n)
    for k in range(1, harmonics + 1):
        if f_max * k >= SAMPLE_RATE / 2:
            break
        f_k = f0 * k if pitch is None else f0 * k * pitch
        gain = 1.0 / np.sqrt(1.0 + (f_k / fc) ** (2 * order))
        if q > 0.0:
            gain = gain * (1.0 + q * np.exp(-0.5 * ((f_k - fc) / (0.30 * fc)) ** 2))
        out += np.sin(k * phase) * gain / k
    return out * (2.0 / np.pi)


def noise_band(generator: np.random.Generator, n: int, fc, bw_ratio: float = 0.8,
               lowpass: bool = False) -> np.ndarray:
    """Bruit filtré à coupure balayable, par STFT (spec §4.2).

    Blocs de 2048, saut 1024, fenêtre de Hann périodique : à ce saut la somme des fenêtres
    est constante, donc l'overlap-add ne module pas l'amplitude.
    """
    block, hop = 2048, 1024
    noise = generator.normal(0.0, 1.0, n + block)
    window = 0.5 - 0.5 * np.cos(2.0 * np.pi * np.arange(block) / block)
    freqs = np.fft.rfftfreq(block, 1.0 / SAMPLE_RATE)
    out = np.zeros(n + block)
    fc_array = np.full(n, float(fc)) if np.isscalar(fc) else np.asarray(fc)
    for start in range(0, n, hop):
        spectrum = np.fft.rfft(noise[start:start + block] * window)
        cutoff = float(fc_array[min(start, n - 1)])
        if lowpass:
            mask = 1.0 / np.sqrt(1.0 + (freqs / cutoff) ** 4)
        else:
            mask = np.exp(-0.5 * ((freqs - cutoff) / (bw_ratio * cutoff)) ** 2)
        out[start:start + block] += np.fft.irfft(spectrum * mask, block)
    return out[:n]


def sweep(f_start: float, f_end: float, n: int, curve: str = "exp") -> np.ndarray:
    """Sinus à fréquence balayée, phase continue par cumsum (spec §4.3)."""
    t = _time(n)
    span = max(t[-1], 1e-9)
    if curve == "exp":
        freq = f_start * (f_end / f_start) ** (t / span)
    else:
        freq = f_start + (f_end - f_start) * (t / span)
    return np.sin(2.0 * np.pi * np.cumsum(freq) / SAMPLE_RATE)


def env_exp(n: int, attack: float, decay: float) -> np.ndarray:
    """Enveloppe percussive : attaque linéaire, décroissance exponentielle (spec §4.4)."""
    t = _time(n)
    return np.clip(t / max(attack, 1e-6), 0.0, 1.0) * np.exp(-t / max(decay, 1e-6))


def env_ahr(n: int, attack: float, hold: float, release: float) -> np.ndarray:
    """Enveloppe tenue. Les 15 derniers ms sont ramenés à zéro : sans ça, une note coupée
    en plein régime claque (spec §4.4)."""
    env = np.ones(n)
    rise = min(int(attack * SAMPLE_RATE), n)
    if rise > 0:
        env[:rise] = np.linspace(0.0, 1.0, rise)
    start = min(rise + int(hold * SAMPLE_RATE), n)
    if start < n:
        env[start:] = np.exp(-_time(n - start) / max(release, 1e-6))
    tail = min(int(0.015 * SAMPLE_RATE), n)
    env[n - tail:] *= np.linspace(1.0, 0.0, tail)
    return env


def formant_voice(f0: float, n: int, morph: float, vib_phase: float) -> np.ndarray:
    """Chœur : synthèse additive à enveloppe de formants (spec §4.5).

    Une voyelle interpolée entre /u/ et /a/, jamais une parole, jamais un sample. Les
    amplitudes harmoniques sont sculptées par quatre formants ; c'est ce qui distingue une
    voix d'une nappe de saws.
    """
    t = _time(n)
    vibrato = 1.0 + 0.006 * np.sin(2.0 * np.pi * 5.2 * t + vib_phase)
    phase = 2.0 * np.pi * np.cumsum(f0 * vibrato) / SAMPLE_RATE
    out = np.zeros(n)
    for k in range(1, 49):
        f_k = f0 * k
        if f_k >= 16_000.0 or f_k >= SAMPLE_RATE / 2:
            break
        amp = 0.0
        for (f_u, a_u, b_u), (f_a, a_a, b_a) in zip(VOWEL_U, VOWEL_A):
            centre = f_u + (f_a - f_u) * morph
            level = a_u + (a_a - a_u) * morph
            width = b_u + (b_a - b_u) * morph
            amp += level * np.exp(-((f_k - centre) ** 2) / (2.0 * width ** 2))
        out += (amp / k ** 0.7) * np.sin(k * phase)
    return out


def saturate(signal: np.ndarray, drive: float) -> np.ndarray:
    return np.tanh(drive * signal) / np.tanh(drive)


def normalize(signal: np.ndarray) -> np.ndarray:
    """Chaque timbre sort à un pic de 1,0 pour une note isolée : les gains du §6.1 sont donc
    des gains de bus directement comparables (spec §2)."""
    peak = float(np.max(np.abs(signal)))
    return signal / peak if peak > 0.0 else signal


def make_ir(name: str, seconds: float, decay: float, predelay: float, tint: float,
            channel: str) -> np.ndarray:
    """IR de réverbe : bruit décroissant, teinté dans le domaine spectral, normalisé en
    énergie. Un flux RNG par canal — c'est la décorrélation L/R qui fait la largeur, pas un
    délai (spec §4.6, §6.6)."""
    n = int(seconds * SAMPLE_RATE)
    noise = rng("ir_%s_%s" % (name, channel)).normal(0.0, 1.0, n)
    ir = noise * np.exp(-_time(n) / decay)
    freqs = np.fft.rfftfreq(n, 1.0 / SAMPLE_RATE)
    ir = np.fft.irfft(np.fft.rfft(ir) / (1.0 + (freqs / tint) ** 2), n)
    ir = np.concatenate([np.zeros(int(predelay * SAMPLE_RATE)), ir])
    return ir / np.sqrt(float(np.sum(ir ** 2)))


def convolve_ir(signal: np.ndarray, ir: np.ndarray) -> np.ndarray:
    length = len(signal) + len(ir) - 1
    wet = np.fft.irfft(np.fft.rfft(signal, length) * np.fft.rfft(ir, length), length)
    return wet[:len(signal)]


# --- Grilles rythmiques --------------------------------------------------------------------

def kick_events() -> list[tuple[int, float, str]]:
    """(échantillon, gain relatif, variante). La grille du kick est aussi celle du sidechain."""
    events: list[tuple[int, float, str]] = []
    for bar in range(1, BARS + 1):
        section = section_of(bar)
        if section == "intro":
            # Le « kick filtré » du brief : sur un kick sinusoïdal, la sourdine vient de la
            # suppression du transitoire, pas d'un filtre (spec §5.10).
            if bar >= 3:
                events += [(at(bar, s), 1.0, "muted") for s in (0, 8)]
        elif section == "rise":
            variant = "full" if bar >= 12 else "noclick"
            events += [(at(bar, s), 1.0, variant) for s in (0, 4, 8, 12)]
        elif section in ("drop", "reprise"):
            # Mesures 32 et 48 : les percussions s'éclaircissent après le temps 2 (spec §8).
            steps = (0, 4) if bar in (32, 48) else (0, 4, 8, 12)
            events += [(at(bar, s), 1.0, "full") for s in steps]
            if (bar - 1) % 8 == 7 and bar not in (32, 48):
                events.append((at(bar, 15), 0.70, "full"))
        elif section == "breakdown" and bar >= 39:
            events += [(at(bar, s), 1.0, "muted") for s in (0, 8)]
    return events


def sidechain_curve(onsets: list[int]) -> np.ndarray:
    """`u(t) = exp(-dt / 0.10)`, dt = temps depuis le dernier kick, **avec bouclage** : le
    dernier kick de la mesure 48 duque le début de la mesure 1. Sans ce repli, la boucle
    aurait un pouls manquant à la couture — et le drone, qui est sidechainé, cesserait d'être
    périodique (spec §6.4, §7.2)."""
    grid = np.array(sorted(set(onsets)), dtype=np.int64)
    index = np.searchsorted(grid, np.arange(LOOP), side="right") - 1
    last = np.where(index >= 0, grid[index], grid[-1] - LOOP)
    dt = (np.arange(LOOP) - last) / SAMPLE_RATE
    pulse = np.exp(-dt / 0.10)
    # Inactif dans l'intro et dans les mesures 33–38 : le breakdown n'a pas de pouls.
    pulse[:bar_start(9)] = 0.0
    pulse[bar_start(33):bar_start(39)] = 0.0
    return pulse


def filter_at(bar: int, start: int, n: int) -> tuple[np.ndarray | float, float]:
    """Automation du filtre pour `ostinato`, `pad` (spec §6.2). L'ouverture du filtre est ce
    qui fait la montée — pas le volume."""
    section = section_of(bar)
    if section == "rise":
        u = np.clip((np.arange(start, start + n) - bar_start(9)) / (8.0 * BAR), 0.0, 1.0)
        fc = 220.0 * (6000.0 / 220.0) ** u
        q = 0.4 + 0.7 * float(u[0])
        return fc, q
    if section == "drop":
        return 7500.0, 0.30
    if section == "breakdown":
        return 1200.0, 0.20
    if section == "reprise":
        return 9000.0, 0.25
    return 2000.0, 0.0


def chord_blocks(first: int, last: int) -> list[tuple[int, int, int]]:
    """Suites maximales de mesures portant le même accord -> (mesure de début, mesures, degré)."""
    blocks: list[tuple[int, int, int]] = []
    bar = first
    while bar <= last:
        degree = CHORDS[bar - 1]
        span = 1
        while bar + span <= last and CHORDS[bar + span - 1] == degree:
            span += 1
        blocks.append((bar, span, degree))
        bar += span
    return blocks


# --- Mixage --------------------------------------------------------------------------------

class Mix:
    """Deux buffers, et c'est le cœur du bouclage (spec §7.2).

    `body` (longueur LOOP) ne reçoit que les voix continues et périodiques — aujourd'hui le
    seul `drone`, dont les fréquences sont recalées sur la grille de boucle. Replier une queue
    sur une voix périodique la **doublerait** dans les premières secondes : c'est le piège.

    `ring` (LOOP + TAIL) reçoit tout le reste et a le droit de sonner au-delà de la fin ; sa
    queue est repliée sur le début, et retombe donc sur elle-même.
    """

    def __init__(self) -> None:
        self.body = np.zeros((LOOP, 2))
        self.dry = np.zeros((TOTAL, 2))
        self.hall = np.zeros((TOTAL, 2))
        self.plate = np.zeros((TOTAL, 2))

    def add_voice(self, name: str, buffer: np.ndarray, pulse: np.ndarray,
                  periodic: bool = False) -> None:
        depth = SIDECHAIN.get(name, 0.0)
        if depth > 0.0:
            gain = 1.0 - depth * pulse
            buffer[:LOOP] *= gain[:, None]
            if not periodic:
                # La queue prolonge la fin de la boucle : elle subit le pouls de la mesure 1,
                # sinon le repli ferait rentrer un signal non ducké sous le premier kick.
                buffer[LOOP:] *= gain[:TAIL, None]
        if periodic:
            self.body += buffer[:LOOP]
            return
        self.dry += buffer
        hall = HALL_SEND.get(name, 0.0)
        if hall > 0.0:
            self.hall += buffer * hall
        plate = PLATE_SEND.get(name, 0.0)
        if plate > 0.0:
            self.plate += buffer * plate


def place(buffer: np.ndarray, start: int, chunk: np.ndarray, gain: float,
          pan: float = 0.5) -> None:
    """Somme `chunk` (mono) dans `buffer` (stéréo) à `start`, panoramiqué à puissance
    constante. Aucune inversion de polarité nulle part : le mix doit rester mono-compatible
    (spec §6.6)."""
    if gain <= 0.0 or start >= len(buffer):
        return
    end = min(start + len(chunk), len(buffer))
    piece = chunk[: end - start] * gain
    buffer[start:end, 0] += piece * np.sqrt(1.0 - pan)
    buffer[start:end, 1] += piece * np.sqrt(pan)


# --- Voix (spec §5) ------------------------------------------------------------------------

def render_drone() -> np.ndarray:
    """Fondation. Ses fréquences sont **recalées sur la grille de boucle** : une fréquence qui
    ne boucle pas un nombre entier de fois fait claquer la couture (spec §5.1, §7.2)."""
    def snap(freq: float) -> float:
        return round(freq * LOOP_SECONDS) / LOOP_SECONDS

    t = _time(LOOP)
    lfo = 1.0 + 0.15 * np.sin(2.0 * np.pi * snap(0.08) * t)
    signal = (np.sin(2.0 * np.pi * snap(D1) * t) * 0.50
              + np.sin(2.0 * np.pi * snap(D1 * 2) * t) * 0.35 * lfo
              + np.sin(2.0 * np.pi * snap(D1 * 2 * 1.004) * t) * 0.25 * lfo)
    signal = normalize(signal)

    # Le gain de section ne peut pas être un escalier : un saut de 0,55 à 0,40 s'entend comme
    # une bosse. Une rampe d'une mesure de part et d'autre de chaque frontière suffit.
    gain = np.zeros(LOOP)
    for name, first, last in SECTIONS:
        gain[bar_start(first):min(bar_start(last + 1), LOOP)] = GAIN["drone"][name]
    ramp = BAR
    for _, first, _ in SECTIONS[1:]:
        edge = bar_start(first)
        lo, hi = edge - ramp // 2, edge + ramp // 2
        gain[lo:hi] = np.linspace(gain[lo], gain[hi], hi - lo)

    buffer = np.zeros((LOOP, 2))
    buffer[:, 0] = signal * gain * np.sqrt(0.5)
    buffer[:, 1] = signal * gain * np.sqrt(0.5)
    return buffer


def _braam_note(f0: float, n: int, generator: np.random.Generator,
                distant: bool) -> list[tuple[np.ndarray, float]]:
    """Sept saws désaccordées : le braam est un geste (gonflement + ouverture spectrale +
    retombée), pas un accord tenu (spec §5.2)."""
    cents = np.array([-14, -9, -4, 0, 4, 9, 14], dtype=float)
    cents = cents + generator.uniform(-3.0, 3.0, len(cents))
    t = _time(n)
    if distant:
        fc: np.ndarray | float = 500.0
        q = 0.0
        env = env_ahr(n, 0.400, 0.400, 0.90)
    else:
        opening = 300.0 + 1900.0 * (1.0 - np.exp(-t / 0.09))
        settle = 900.0 + (2200.0 - 900.0) * np.exp(-np.maximum(t - 0.26, 0.0) / 0.7)
        fc = np.where(t < 0.26, opening, settle)
        q = 0.35
        env = env_ahr(n, 0.220, 0.400, 0.90)
    # Gonflement de hauteur : ≈ +7 cents montants, ce qui donne au geste sa poussée.
    pitch = 1.0 + 0.004 * (1.0 - np.exp(-t / 0.15))
    voices: list[tuple[np.ndarray, float]] = []
    for index, cent in enumerate(cents):
        freq = f0 * 2.0 ** (cent / 1200.0)
        voice = saw_lp(freq, n, 48, fc, order=2, q=q, pitch=pitch) * env
        pan = 0.15 + 0.70 * index / (len(cents) - 1)
        voices.append((voice, pan))
    return voices


def render_braam() -> np.ndarray:
    buffer = np.zeros((TOTAL, 2))
    generator = rng("braam")
    length = 2 * BAR
    # Occurrences : gestes de bascule. La pédale de dominante (A2+A3) prépare les deux
    # cadences — celle du breakdown et celle de la boucle (spec §5.2, §8).
    events = [(3, "distant"), (7, "distant"), (9, "open"),
              (17, "open"), (21, "open"), (25, "open"), (29, "open"), (31, "pedal"),
              (40, "open"), (41, "open"), (45, "open"), (47, "pedal")]
    # Sept saws × 48 harmoniques × 151 k échantillons : rendre chaque note à chaque occurrence
    # coûterait des minutes pour un signal identique. Les douze braams ne couvrent que huit
    # notes distinctes.
    cache: dict[tuple[float, bool], list[tuple[np.ndarray, float]]] = {}
    for bar, kind in events:
        notes = [110.0, 220.0] if kind == "pedal" else [73.416, 110.0, 146.832]
        gain = GAIN["braam"][section_of(bar)]
        for freq in notes:
            key = (freq, kind == "distant")
            if key not in cache:
                cache[key] = [(normalize(voice), pan)
                              for voice, pan in _braam_note(freq, length, generator, key[1])]
            for voice, pan in cache[key]:
                place(buffer, bar_start(bar), voice, gain / len(notes), pan)
    return buffer


def render_brass_cell() -> np.ndarray:
    """Les cuivres énoncent la cellule. C'est la voix que le joueur doit reconnaître quand le
    motif ressurgit, dégradé, dans boss_phase_1 ou final_charge (spec §3.2, §5.3)."""
    buffer = np.zeros((TOTAL, 2))
    # (mesure, position en doubles-croches, index de cellule, durée en temps)
    events: list[tuple[int, int, int, float]] = []
    for offset, bar in enumerate(range(17, 29)):          # drop : la cellule à la ronde (×8)
        events.append((bar, 0, offset % 4, 4.0))
    events += [(29, 0, 0, 2.0), (29, 8, 1, 2.0),          # la cellule accélère (×4)
               (30, 0, 2, 2.0), (30, 8, 3, 2.0),
               (31, 0, 3, 4.0), (32, 0, 3, 4.0)]          # A tenu : pédale de dominante
    for offset, bar in enumerate(range(41, 45)):          # reprise
        events.append((bar, 0, offset % 4, 4.0))
    events += [(45, 0, 0, 2.0), (45, 8, 1, 2.0),
               (46, 0, 2, 2.0), (46, 8, 3, 2.0),
               (47, 0, 3, 4.0), (48, 0, 3, 4.0)]

    cents = (-10.0, -5.0, 0.0, 5.0, 10.0)
    cache: dict[tuple[int, int, float, float], np.ndarray] = {}
    for bar, step, cell, beats in events:
        n = int(beats * BEAT)
        gain = GAIN["brass_cell"][section_of(bar)]
        for octave, weight in ((0, 1.00), (-1, 0.55), (1, 0.30)):
            for side, detune in ((0.0, -6.0), (1.0, 6.0)):
                key = (cell, octave, side, beats)
                if key not in cache:
                    t = _time(n)
                    # Vibrato lent, nul avant 400 ms : un cuivre qui vibre dès l'attaque sonne
                    # comme un synthé.
                    vibrato = 1.0 + 0.003 * np.sin(2.0 * np.pi * 4.2 * np.maximum(t - 0.4, 0.0))
                    env = env_ahr(n, 0.060, 0.80 * n / SAMPLE_RATE, 0.45)
                    f0 = cell_hz(cell, 3 + octave)
                    voice = np.zeros(n)
                    for cent in cents:
                        freq = f0 * 2.0 ** ((cent + detune) / 1200.0)
                        voice += saw_lp(freq, n, 40, 2600.0, order=2, q=0.25, pitch=vibrato)
                    cache[key] = normalize(voice * env)
                place(buffer, at(bar, step), cache[key],
                      gain * weight * 0.5, pan=0.5 + (side - 0.5) * 0.7)
    return buffer


def render_ostinato() -> np.ndarray:
    """Cordes, la cellule en croches : registre fixe, harmonie mobile. C'est l'harmonie statique
    du genre — et la cellule reste diatonique sur les cinq accords de la grille (spec §5.4)."""
    buffer = np.zeros((TOTAL, 2))
    generator = rng("ostinato")
    detune = {side: generator.uniform(-9.0, 9.0, 3) for side in (0, 1)}
    n = int(0.9 * (BEAT // 2))
    env = env_exp(n, 0.012, 0.11)
    bow_len = 220
    bow = np.zeros(n)
    bow[:bow_len - 1] = np.diff(generator.normal(0.0, 1.0, bow_len)) * np.exp(
        -_time(bow_len - 1) / 0.008)

    for bar in range(1, BARS + 1):
        section = section_of(bar)
        gain = GAIN["ostinato"][section]
        if gain <= 0.0:
            continue
        # Mesures impaires : cellule directe ; paires : rétrograde. Les mesures 47–48 tiennent
        # le rétrograde et s'effacent : c'est la cadence qui scelle la boucle (spec §8).
        retrograde = (bar % 2 == 0) or bar in (47, 48)
        level = gain * (0.6 if bar in (47, 48) else 1.0)
        for step in range(8):
            cell = (3 - (step % 4)) if retrograde else (step % 4)
            start = at(bar, step * 2)
            fc, q = filter_at(bar, start, n)
            for side in (0, 1):
                voice = np.zeros(n)
                for cent in detune[side]:
                    freq = cell_hz(cell, 4) * 2.0 ** (cent / 1200.0)
                    voice += saw_lp(freq, n, 16, fc, order=2, q=q)
                    if bar >= 25:   # doublure à l'octave, à partir du deuxième tiers du drop
                        voice += saw_lp(freq * 2.0, n, 16, fc, order=2, q=q) * 0.35
                voice = normalize(voice) * env + bow * 0.06
                place(buffer, start, voice, level * 0.5, pan=0.15 + 0.70 * side)
    return buffer


def render_pad() -> np.ndarray:
    """Lit d'accords. La relâche déborde sur l'accord suivant : c'est voulu, ça soude la grille
    (spec §5.5). Ne pas le fusionner avec l'ostinato — deux voix de cordes, pas un synthé."""
    buffer = np.zeros((TOTAL, 2))
    generator = rng("pad")
    for bar, span, degree in chord_blocks(1, BARS):
        gain = GAIN["pad"][section_of(bar)]
        if gain <= 0.0:
            continue
        n = span * BAR
        start = bar_start(bar)
        fc, q = filter_at(bar, start, n)
        env = env_ahr(n, 0.350, max(n / SAMPLE_RATE - 1.2, 0.1), 1.2)
        for index, freq in enumerate(triad(degree, 3)):
            voice = np.zeros(n)
            for cent in generator.uniform(-5.0, 5.0, 2):
                voice += saw_lp(freq * 2.0 ** (cent / 1200.0), n, 12, fc, order=2, q=max(q, 0.2))
            place(buffer, start, normalize(voice) * env, gain / 3.0, pan=0.25 + 0.25 * index)
    return buffer


def render_choir() -> np.ndarray:
    """Chœur synthétique abstrait — voyelles, aucune parole. Dans le breakdown, la voix
    supérieure trace la cellule à raison d'une note toutes les deux mesures : augmentation ×16,
    la forme la plus large du morceau (spec §3.2, §5.6)."""
    buffer = np.zeros((TOTAL, 2))
    generator = rng("choir")
    # Hors breakdown le chœur suit les blocs d'accords ; dans le breakdown il suit la cellule,
    # qui avance toutes les deux mesures — le bloc de Dm en couvre quatre à lui seul, il ne peut
    # donc pas servir de grille ici.
    blocks = [(bar, span, degree) for bar, span, degree in chord_blocks(1, BARS)
              if section_of(bar) != "breakdown"]
    blocks += [(bar, 2, CHORDS[bar - 1]) for bar in (33, 35, 37, 39)]

    for bar, span, degree in sorted(blocks):
        section = section_of(bar)
        gain = GAIN["choir"][section]
        if gain <= 0.0:
            continue
        n = span * BAR
        start = bar_start(bar)
        breakdown = section == "breakdown"
        attack, release = (0.400, 1.4) if breakdown else (0.090, 0.8)
        env = env_ahr(n, attack, max(n / SAMPLE_RATE - release, 0.1), release)
        notes = list(triad(degree, 4))
        if breakdown:
            # La voix supérieure trace la cellule, une note toutes les deux mesures : D (33–34),
            # G (35–36), F (37–38), A (39–40) — augmentation ×16, la forme la plus large du
            # morceau. Le G sur Dm des mesures 35–36 est un Dm(add11) assumé (spec §3.3).
            notes[-1] = cell_hz((bar - 33) // 2, 5)
            morph = np.clip((bar - 33) / 7.0, 0.0, 1.0)
        else:
            morph = 0.75
        for index, freq in enumerate(notes):
            for octave, weight in ((0, 1.0), (-1, 0.35)):
                voice = np.zeros(n)
                for _ in range(3):
                    cent = generator.uniform(6.0, 12.0) * generator.choice([-1.0, 1.0])
                    voice += formant_voice(freq * (2.0 ** octave) * 2.0 ** (cent / 1200.0),
                                           n, morph, generator.uniform(0.0, 2.0 * np.pi))
                breath = noise_band(generator, n, 4000.0, bw_ratio=0.6) * 0.03
                place(buffer, start, (normalize(voice) + breath) * env,
                      gain * weight / 3.0, pan=0.20 + 0.30 * index)
    return buffer


def render_clarion() -> np.ndarray:
    """Doublure aiguë de la cellule, réservée à la reprise : ce que le morceau garde en réserve
    jusqu'à la dernière section (spec §5.7)."""
    buffer = np.zeros((TOTAL, 2))
    generator = rng("clarion")
    events = [(45, 0, 0, 2.0), (45, 8, 1, 2.0), (46, 0, 2, 2.0), (46, 8, 3, 2.0),
              (47, 0, 3, 4.0), (48, 0, 3, 4.0)]
    for bar, step, cell, beats in events:
        n = int(beats * BEAT)
        t = _time(n)
        vibrato = 1.0 + 0.005 * np.sin(2.0 * np.pi * 5.5 * np.maximum(t - 0.25, 0.0))
        env = env_ahr(n, 0.040, 0.55 * n / SAMPLE_RATE, 0.6)
        f0 = cell_hz(cell, 5)
        for side, pan in ((0, 0.30), (1, 0.70)):
            voice = np.zeros(n)
            for cent in generator.uniform(-10.0, 10.0, 2):
                voice += saw_lp(f0 * 2.0 ** (cent / 1200.0), n, 20, 5000.0,
                                order=2, q=0.4, pitch=vibrato)
            voice += np.sin(2.0 * np.pi * 2.0 * f0 * t) * 0.25
            place(buffer, at(bar, step), normalize(voice) * env,
                  GAIN["clarion"][section_of(bar)] * 0.5, pan=pan)
    return buffer


def render_sub() -> np.ndarray:
    """Basse sinusoïdale tenue. Aucune mélodie : des fondamentales. Le rythme du sub, c'est le
    sidechain (spec §5.8). Mono, sec — les graves restent au centre."""
    buffer = np.zeros((TOTAL, 2))
    for bar, span, degree in chord_blocks(1, BARS):
        gain = GAIN["sub"][section_of(bar)]
        # Dans le breakdown, le sub ne revient qu'avec le pouls, mesures 39–40.
        if section_of(bar) == "breakdown" and bar < 39:
            continue
        if gain <= 0.0:
            continue
        n = span * BAR
        t = _time(n)
        root = note_hz(degree, 2)
        env = env_ahr(n, 0.008, max(n / SAMPLE_RATE - 0.03, 0.01), 0.03)
        voice = (np.sin(2.0 * np.pi * root * t)
                 + np.sin(2.0 * np.pi * root * 0.5 * t) * 0.25)
        place(buffer, bar_start(bar), normalize(voice) * env, gain)
    return buffer


def render_bass_grit() -> np.ndarray:
    """La basse saw en croches : le grain techno sous l'orchestre (spec §5.9)."""
    buffer = np.zeros((TOTAL, 2))
    n = int(0.9 * (BEAT // 2))
    env = env_exp(n, 0.005, 0.10)
    for bar in range(1, BARS + 1):
        gain = GAIN["bass_grit"][section_of(bar)]
        if gain <= 0.0:
            continue
        root = note_hz(CHORDS[bar - 1], 2)
        voice = np.zeros(n)
        for cent in (-7.0, 0.0, 7.0):
            # fc propre à la basse : la soustraire au balayage de la montée la ferait
            # disparaître au moment précis où elle doit tenir le bas (spec §6.2).
            voice += saw_lp(root * 2.0 ** (cent / 1200.0), n, 10, 700.0, order=2, q=0.5)
        voice = saturate(normalize(voice) * env, 2.2)
        for step in range(8):
            place(buffer, at(bar, step * 2), voice, gain)
    return buffer


def render_kick(events: list[tuple[int, float, str]]) -> np.ndarray:
    buffer = np.zeros((TOTAL, 2))
    generator = rng("kick")
    click_source = np.diff(generator.normal(0.0, 1.0, 120)) * np.exp(-_time(119) / 0.003)

    def body(decay: float, click: float, drive: float) -> np.ndarray:
        n = int(0.32 * SAMPLE_RATE)
        t = _time(n)
        freq = 48.0 + 130.0 * np.exp(-t / 0.018)
        voice = np.sin(2.0 * np.pi * np.cumsum(freq) / SAMPLE_RATE) * env_exp(n, 0.0015, decay)
        if click > 0.0:
            voice[:len(click_source)] += click_source * click
        if drive > 0.0:
            voice = saturate(voice, drive)
        return normalize(voice)

    variants = {
        "full": body(0.11, 0.25, 3.2),
        "noclick": body(0.11, 0.0, 3.2),
        # Intro : corps seul, décroissance courte. Un battement mat, pas un kick de club.
        "muted": body(0.06, 0.0, 0.0),
    }
    for start, gain, variant in events:
        bar = start // BAR + 1
        place(buffer, start, variants[variant], GAIN["kick"][section_of(bar)] * gain)
    return buffer


def render_taiko() -> tuple[np.ndarray, np.ndarray]:
    """Le partiel inharmonique à ×1,58 est ce qui fait la membrane plutôt que la note
    (spec §5.11). Le jitter de gain est ce qui évite la machine."""
    generator = rng("taiko")

    def drum(f_base: float, f_drop: float, tau: float, partial: float, skin: float,
             decay: float, length: float) -> np.ndarray:
        n = int(length * SAMPLE_RATE)
        t = _time(n)
        freq = f_base + f_drop * np.exp(-t / tau)
        phase = 2.0 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        voice = np.sin(phase) + np.sin(phase * 1.58) * partial
        noise = np.zeros(n)
        noise[:-1] = np.diff(generator.normal(0.0, 1.0, n)) * np.exp(-t[:-1] / 0.030)
        voice = (voice + noise * skin) * env_exp(n, 0.002, decay)
        return normalize(saturate(voice, 2.0))

    low = drum(62.0, 40.0, 0.05, 0.32, 0.18, 0.28, 0.55)
    mid = drum(96.0, 55.0, 0.045, 0.35, 0.22, 0.20, 0.42)
    buf_low = np.zeros((TOTAL, 2))
    buf_mid = np.zeros((TOTAL, 2))
    for bar in range(1, BARS + 1):
        gain_low = GAIN["taiko_low"][section_of(bar)]
        gain_mid = GAIN["taiko_mid"][section_of(bar)]
        if gain_low <= 0.0 and gain_mid <= 0.0:
            continue
        if bar % 2 == 1:
            steps_low, steps_mid = (0, 6, 10), (4, 12, 14)
        else:
            steps_low, steps_mid = (0, 3, 6, 10), (4, 12)
        for step in steps_low:
            jitter = 1.0 + generator.uniform(-0.05, 0.05)
            place(buf_low, at(bar, step), low, gain_low * jitter)
        for step in steps_mid:
            jitter = 1.0 + generator.uniform(-0.05, 0.05)
            place(buf_mid, at(bar, step), mid, gain_mid * jitter, pan=0.62)
        if bar % 4 == 0:  # fill de fin de phrase
            for index, step in enumerate((10, 11, 12, 13, 14, 15)):
                ramp = 0.50 + 0.50 * index / 5.0
                place(buf_mid, at(bar, step), mid, gain_mid * ramp, pan=0.62)
    return buf_low, buf_mid


def render_snare() -> np.ndarray:
    buffer = np.zeros((TOTAL, 2))
    generator = rng("snare")
    n = int(0.22 * SAMPLE_RATE)
    t = _time(n)
    noise = generator.normal(0.0, 1.0, n)
    rattle = np.zeros(n)
    rattle[:-1] = np.diff(noise)
    hit = normalize((noise * 0.80 + np.sin(2.0 * np.pi * 190.0 * t) * 0.35 + rattle * 0.20)
                    * env_exp(n, 0.001, 0.075))
    flam = int(0.040 * SAMPLE_RATE)

    for bar in range(1, BARS + 1):
        section = section_of(bar)
        gain = GAIN["snare"][section]
        if gain <= 0.0:
            continue
        if section in ("drop", "reprise") and bar not in (32, 48):
            for step in (4, 12):                     # contretemps, précédé d'un flam
                place(buffer, at(bar, step) - flam, hit, gain * 0.35, pan=0.45)
                place(buffer, at(bar, step), hit, gain, pan=0.45)
        elif bar == 15:                              # roulement : croches
            for index, step in enumerate(range(0, 16, 2)):
                place(buffer, at(bar, step), hit, gain * (0.40 + 0.20 * index / 7.0), pan=0.45)
        elif bar in (16, 40):                        # roulement : 16ᵉ puis 32ᵉ, coupe nette
            ceiling = 1.00 if bar == 16 else 0.80
            steps = [s * 1.0 for s in range(8)] + [s * 0.5 for s in range(16, 32)]
            for index, step in enumerate(steps):
                level = 0.60 + (ceiling - 0.60) * index / (len(steps) - 1)
                start = at(bar, step)
                if start >= bar_start(bar + 1) - int(0.060 * SAMPLE_RATE):
                    break
                place(buffer, start, hit, gain * level, pan=0.45)
    return buffer


def render_hat() -> np.ndarray:
    buffer = np.zeros((TOTAL, 2))
    generator = rng("hat")
    n = int(0.060 * SAMPLE_RATE)
    raw = generator.normal(0.0, 1.0, n + 2)
    closed = normalize(np.diff(np.diff(raw)) * np.exp(-_time(n) / 0.022))
    n_open = int(0.22 * SAMPLE_RATE)
    raw_open = generator.normal(0.0, 1.0, n_open + 1)
    opened = normalize(np.diff(raw_open) * np.exp(-_time(n_open) / 0.16))

    for bar in range(1, BARS + 1):
        gain = GAIN["hat"][section_of(bar)]
        if gain <= 0.0:
            continue
        for step in range(16):
            if bar in (32, 48) and step >= 8:
                continue
            if step % 4 == 0:
                level = 0.30
            elif step % 2 == 1:
                level = 0.75
            else:
                level = 0.50
            level *= 1.0 + generator.uniform(-0.08, 0.08)
            pan = 0.45 if step % 2 == 0 else 0.55
            place(buffer, at(bar, step), closed, gain * level, pan=pan)
        if bar % 2 == 0 and bar not in (32, 48):
            place(buffer, at(bar, 14), opened, gain * 0.50, pan=0.55)
    return buffer


def render_riser() -> np.ndarray:
    """Le riser atterrit sur la dominante A, que le drop résout sur D : il est **harmonique**,
    pas décoratif. Et il se coupe 60 ms avant le temps — le trou est ce qui fait exister
    l'impact (spec §5.14)."""
    buffer = np.zeros((TOTAL, 2))
    generator = rng("riser")
    cut = int(0.060 * SAMPLE_RATE)
    fade = int(0.030 * SAMPLE_RATE)

    for bar, bars, level in ((15, 2, GAIN["riser"]["rise"]), (40, 1, GAIN["riser"]["breakdown"])):
        n = bars * BAR - cut
        t = _time(n)
        curve = 300.0 * (9000.0 / 300.0) ** (t / t[-1])
        voice = noise_band(generator, n, curve, bw_ratio=0.8) * (t / t[-1]) ** 2
        # Le sinus balayé atterrit sur A5 : la dominante, que le drop résout sur D.
        voice = normalize(voice) + sweep(220.0, 880.0, n) * (t / t[-1]) ** 2 * 0.20
        voice[-fade:] *= np.linspace(1.0, 0.0, fade)
        place(buffer, bar_start(bar), normalize(voice), level)

    # Mesure 8, temps 4 : bref balayage qui annonce la montée (spec §8).
    n = int(0.4 * SAMPLE_RATE)
    t = _time(n)
    curve = 300.0 * (2000.0 / 300.0) ** (t / t[-1])
    swell = normalize(noise_band(generator, n, curve, bw_ratio=0.8) * (t / t[-1]) ** 2)
    place(buffer, at(8, 12), swell, GAIN["riser"]["intro"])
    return buffer


def render_impact() -> np.ndarray:
    """Le point de bascule. Son transitoire masque n'importe quel micro-défaut à la couture —
    c'est la quatrième garantie du bouclage (spec §5.15, §7.4)."""
    buffer = np.zeros((TOTAL, 2))
    generator = rng("impact")
    n = int(2.0 * SAMPLE_RATE)
    boom = sweep(90.0, 38.0, int(0.60 * SAMPLE_RATE), curve="lin")
    boom = boom * env_exp(len(boom), 0.002, 0.35)
    body = noise_band(generator, n, 1800.0, lowpass=True) * env_exp(n, 0.001, 0.55)
    raw = generator.normal(0.0, 1.0, n + 2)
    shine = np.diff(np.diff(raw)) * env_exp(n, 0.001, 0.60)

    centre = np.zeros(n)
    centre[:len(boom)] += normalize(boom)
    centre += normalize(body) * 0.55
    centre = saturate(centre, 1.8)
    shine = normalize(shine) * 0.22

    for bar in (1, 17, 41):
        gain = GAIN["impact"][section_of(bar)]
        place(buffer, bar_start(bar), normalize(centre), gain)
        place(buffer, bar_start(bar), shine, gain, pan=0.25)
        place(buffer, bar_start(bar), shine, gain, pan=0.75)
    return buffer


def render_reverse_riser() -> np.ndarray:
    """Le sceau de la boucle. Il culmine 20 ms avant la fin, s'éteint exactement à l'échantillon
    3 628 799, et sa queue de réverbe — repliée — retombe pile sur l'impact de la mesure 1.
    L'effet « reverse » vient de l'enveloppe qui gonfle, pas d'un retournement de buffer
    (spec §5.16, §7.4)."""
    buffer = np.zeros((TOTAL, 2))
    n = BAR
    t = _time(n)
    curve = 200.0 * (6000.0 / 200.0) ** (t / t[-1])
    fade = int(0.020 * SAMPLE_RATE)
    for channel, pan in ((0, 0.2), (1, 0.8)):
        # Deux rendus décorrélés. Une graine dérivée (et non `SEED + offset + channel`) : la
        # somme retomberait sur l'offset d'une autre voix, et les deux partageraient son bruit.
        generator = np.random.default_rng([SEED + RNG_OFFSET["reverse_riser"], channel])
        voice = noise_band(generator, n, curve, bw_ratio=0.6) * (t / t[-1]) ** 1.7
        voice = normalize(voice)
        voice[-fade:] *= np.linspace(1.0, 0.0, fade)
        place(buffer, bar_start(48), voice, GAIN["reverse_riser"]["reprise"], pan=pan)
    return buffer


# --- Master (spec §6.3) --------------------------------------------------------------------

def highpass_loop(mix: np.ndarray, cutoff: float = 30.0) -> np.ndarray:
    """Passe-haut appliqué par FFT **sur le buffer de boucle**. Le filtrage circulaire, qui est
    d'ordinaire un défaut, est ici exactement ce qu'on veut : il préserve la périodicité de la
    boucle. Il retire l'énergie inaudible qui mangeait de la marge et que Vorbis coderait pour
    rien (spec §6.3, étape 5)."""
    n = len(mix)
    freqs = np.fft.rfftfreq(n, 1.0 / SAMPLE_RATE)
    response = np.zeros_like(freqs)
    response[1:] = 1.0 / np.sqrt(1.0 + (cutoff / freqs[1:]) ** 4)
    out = np.zeros_like(mix)
    for channel in range(2):
        out[:, channel] = np.fft.irfft(np.fft.rfft(mix[:, channel]) * response, n)
    return out


def main() -> None:
    print("[theme] rendu des voix (1 à 3 min attendues)…")
    mix = Mix()
    kicks = kick_events()
    pulse = sidechain_curve([start for start, _, _ in kicks])

    mix.add_voice("drone", render_drone(), pulse, periodic=True)
    print("[theme]   drone")
    for name, buffer in (
        ("pad", render_pad()),
        ("ostinato", render_ostinato()),
        ("braam", render_braam()),
        ("brass_cell", render_brass_cell()),
        ("choir", render_choir()),
        ("clarion", render_clarion()),
        ("sub", render_sub()),
        ("bass_grit", render_bass_grit()),
        ("kick", render_kick(kicks)),
        ("snare", render_snare()),
        ("hat", render_hat()),
        ("riser", render_riser()),
        ("impact", render_impact()),
        ("reverse_riser", render_reverse_riser()),
    ):
        mix.add_voice(name, buffer, pulse)
        print("[theme]   %s" % name)
    taiko_low, taiko_mid = render_taiko()
    mix.add_voice("taiko_low", taiko_low, pulse)
    mix.add_voice("taiko_mid", taiko_mid, pulse)
    print("[theme]   taiko")

    print("[theme] réverbes…")
    ring = mix.dry.copy()
    for name, seconds, decay, predelay, tint, send in (
        ("hall", 2.60, 0.42, 0.028, 4200.0, mix.hall),
        ("plate", 0.90, 0.16, 0.008, 7000.0, mix.plate),
    ):
        for channel, side in ((0, "l"), (1, "r")):
            ir = make_ir(name, seconds, decay, predelay, tint, side)
            ring[:, channel] += convolve_ir(send[:, channel], ir)

    # Repli de la queue (spec §7.3). La résonance qui déborde retombe sur elle-même : mix[0]
    # vaut exactement ce que le signal aurait valu à l'instant LOOP s'il avait continué. La
    # continuité à la couture est vraie par construction, pas approchée.
    ring[:TAIL] += ring[LOOP:LOOP + TAIL]
    stereo = (mix.body + ring[:LOOP]) * MASTER_TRIM

    assert stereo.shape == (LOOP, 2), "longueur de boucle: %s" % (stereo.shape,)
    assert np.all(np.isfinite(stereo)), "le mix contient des NaN ou des inf"
    peak = float(np.max(np.abs(stereo)))
    print("[theme] crête pré-tanh %.3f" % peak)
    assert peak < 1.6, "crête pré-tanh %.3f >= 1.6 : revoir les gains du §6.1, pas le drive" % peak

    stereo = highpass_loop(stereo)
    stereo = np.tanh(stereo)
    stereo = stereo / float(np.max(np.abs(stereo))) * 0.89

    rms = float(np.sqrt(np.mean(stereo ** 2)))
    seam = float(np.max(np.abs(stereo[0] - stereo[-1])))
    print("[theme] RMS %.3f   couture %.4f" % (rms, seam))
    assert 0.14 <= rms <= 0.18, "RMS %.3f hors de [0,14 ; 0,18] : baisser les percussions" % rms
    assert seam < 0.08, "discontinuité à la couture: %.4f" % seam

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(np.round(stereo * 32767.0), -32768, 32767).astype("<i2")
    with wave.open(str(OUTPUT), "wb") as target:
        target.setnchannels(2)
        target.setsampwidth(2)
        target.setframerate(SAMPLE_RATE)
        target.writeframes(pcm.tobytes())

    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print("[theme] %s  %.3f s  sha256 %s" % (OUTPUT, LOOP / SAMPLE_RATE, digest[:16]))


if __name__ == "__main__":
    main()
