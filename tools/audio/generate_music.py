#!/usr/bin/env python3
"""Génère les neuf pistes de musique adaptative d'Aegis Ascendant.

Implémente `docs/forge/output/adaptive_music_structure.md` : tempos, centres tonaux et
couches actives y sont normatifs. Synthèse additive pure (aucun sample, aucune banque
externe), déterministe — un RNG par état, jamais de RNG global partagé.

Chaque piste est **bouclée par construction** : on rend une queue au-delà de la dernière
mesure, puis on la replie sur le début. La résonance qui déborde de la boucle retombe donc
sur elle-même au lieu d'être tranchée (structure §« ne coupe pas une résonance longue »).

Sortie : assets/source/audio/music/<état>.wav (gitignoré, ~50 Mo).
Encodage OGG et mastering : tools/audio/build_audio.py.

Usage : python3 tools/audio/generate_music.py
"""

from __future__ import annotations

import struct
import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44_100
OUTPUT = Path("assets/source/audio/music")

## Cellule signature : intervalles +5, -2, +4 demi-tons (structure §Socle commun).
MOTIF = (0, 5, 3, 7)

## Durée visée par piste ; le nombre de mesures est ajusté pour tomber juste.
TARGET_SECONDS = 32.0
## Queue repliée sur le début pour souder la boucle.
TAIL_SECONDS = 2.0

SCALES = {
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "major_add6": (0, 2, 4, 5, 7, 9, 11),
    "sus": (0, 2, 5, 7, 9, 12, 14),
}

## Fréquences des centres tonaux (Hz).
ROOTS = {"D3": 146.83, "Eb3": 155.56, "A2": 110.00}

## Les neuf états, tels que la forge les a spécifiés. `layers` pondère chaque voix : c'est
## la traduction directe de la colonne « couches actives ».
STATES = {
    "launch": dict(
        bpm=92, beats=4, root="D3", scale="dorian", chords=(0, 3, 0, 6), seed=1,
        layers=dict(drone=0.9, pad=0.8, bass=0.3, arp=0.22, lead=0.0,
                    choir=0.0, brass=0.0, kick=0.25, snare=0.0, hat=0.0)),
    "skirmish": dict(
        bpm=116, beats=4, root="D3", scale="dorian", chords=(0, 6, 3, 0), seed=2,
        layers=dict(drone=0.35, pad=0.5, bass=0.8, arp=0.7, lead=0.0,
                    choir=0.0, brass=0.0, kick=0.7, snare=0.5, hat=0.45)),
    "fleet_battle": dict(
        bpm=132, beats=4, root="D3", scale="minor", chords=(0, 5, 3, 6), seed=3,
        layers=dict(drone=0.25, pad=0.4, bass=0.9, arp=0.6, lead=0.0,
                    choir=0.0, brass=0.75, kick=1.0, snare=0.8, hat=0.6)),
    "docking": dict(
        bpm=84, beats=6, root="A2", scale="sus", chords=(0, 3, 4, 3), seed=4,
        layers=dict(drone=0.5, pad=0.9, bass=0.4, arp=0.5, lead=0.0,
                    choir=0.0, brass=0.0, kick=0.22, snare=0.0, hat=0.0)),
    "fortress_awakening": dict(
        bpm=108, beats=4, root="D3", scale="dorian", chords=(0, 4, 6, 3), seed=5,
        layers=dict(drone=0.6, pad=0.5, bass=0.7, arp=0.0, lead=0.0,
                    choir=0.9, brass=0.0, kick=0.45, snare=0.0, hat=0.0)),
    "boss_phase_1": dict(
        bpm=136, beats=4, root="D3", scale="phrygian", chords=(0, 1, 0, 6), seed=6,
        layers=dict(drone=0.3, pad=0.3, bass=0.95, arp=0.8, lead=0.0,
                    choir=0.0, brass=0.45, kick=1.0, snare=0.9, hat=0.5)),
    "boss_phase_2": dict(
        bpm=148, beats=4, root="Eb3", scale="minor", chords=(0, 6, 5, 1), seed=7,
        layers=dict(drone=0.3, pad=0.6, bass=1.0, arp=0.9, lead=0.0,
                    choir=0.0, brass=0.5, kick=1.0, snare=1.0, hat=0.7)),
    "final_charge": dict(
        bpm=156, beats=4, root="D3", scale="minor", chords=(0, 5, 6, 3), seed=8,
        layers=dict(drone=0.25, pad=0.6, bass=1.0, arp=0.9, lead=0.7,
                    choir=0.5, brass=0.9, kick=1.0, snare=1.0, hat=0.8)),
    "victory": dict(
        bpm=96, beats=4, root="D3", scale="major_add6", chords=(0, 4, 5, 3), seed=9,
        layers=dict(drone=0.4, pad=0.9, bass=0.6, arp=0.3, lead=1.0,
                    choir=0.6, brass=0.8, kick=0.4, snare=0.3, hat=0.25)),
}


def note_hz(root: float, scale: tuple[int, ...], degree: int, octave: int = 0) -> float:
    """Degré (peut dépasser l'octave) -> fréquence."""
    span = len(scale)
    semitones = scale[degree % span] + 12 * (degree // span + octave)
    return root * 2.0 ** (semitones / 12.0)


def saw(freq: float, t: np.ndarray, harmonics: int) -> np.ndarray:
    """Dent de scie à bande limitée : `harmonics` tient lieu de fréquence de coupure."""
    out = np.zeros_like(t)
    for k in range(1, harmonics + 1):
        if freq * k >= SAMPLE_RATE / 2:
            break
        out += np.sin(2 * np.pi * freq * k * t) / k
    return out * (2.0 / np.pi)


def sine(freq: float, t: np.ndarray, phase: float = 0.0) -> np.ndarray:
    return np.sin(2 * np.pi * freq * t + phase)


def envelope(length: int, attack: float, decay: float) -> np.ndarray:
    """Enveloppe percussive : attaque linéaire, décroissance exponentielle."""
    t = np.arange(length) / SAMPLE_RATE
    rise = np.clip(t / max(attack, 1e-6), 0.0, 1.0)
    return rise * np.exp(-t / max(decay, 1e-6))


def add(buffer: np.ndarray, start: int, chunk: np.ndarray, gain: float) -> None:
    """Somme `chunk` dans `buffer` à partir de `start`, en tronquant proprement."""
    if gain <= 0.0 or start >= len(buffer):
        return
    end = min(start + len(chunk), len(buffer))
    buffer[start:end] += chunk[: end - start] * gain


def render(name: str, spec: dict) -> np.ndarray:
    rng = np.random.default_rng(spec["seed"])
    root = ROOTS[spec["root"]]
    scale = SCALES[spec["scale"]]
    beats_per_bar = spec["beats"]
    beat = 60.0 / spec["bpm"]
    bar = beat * beats_per_bar

    bars = max(4, int(round(TARGET_SECONDS / bar / 4)) * 4)
    loop_samples = int(round(bars * bar * SAMPLE_RATE))
    tail = int(TAIL_SECONDS * SAMPLE_RATE)
    left = np.zeros(loop_samples + tail)
    right = np.zeros(loop_samples + tail)
    layers = spec["layers"]

    def at(bar_index: float) -> int:
        return int(round(bar_index * bar * SAMPLE_RATE))

    # --- Nappes tenues : drone, pad, chœur -----------------------------------
    hold = np.arange(int(bar * 4 * SAMPLE_RATE) + tail) / SAMPLE_RATE
    fade = np.clip(hold / 0.6, 0, 1) * np.clip((hold[-1] - hold) / 1.2, 0, 1)

    drone = (sine(note_hz(root, scale, 0, -1), hold) * 0.6
             + sine(note_hz(root, scale, 0, -2), hold) * 0.4)
    # Battement lent entre deux voix légèrement désaccordées : la nappe respire.
    drone += sine(note_hz(root, scale, 0, -1) * 1.003, hold) * 0.3
    for block in range(bars // 4):
        add(left, at(block * 4), drone * fade, layers["drone"] * 0.5)
        add(right, at(block * 4), drone * fade, layers["drone"] * 0.5)

    for index, degree in enumerate(spec["chords"] * (bars // 4 // len(spec["chords"]) or 1)):
        if index * 4 >= bars:
            break
        start = at(index * 4)
        triad = (degree, degree + 2, degree + 4)
        pad = np.zeros_like(hold)
        for voice, tone in enumerate(triad):
            freq = note_hz(root, scale, tone)
            # Deux saws désaccordées par voix : le battement fait la largeur du pad.
            pad += saw(freq * 0.997, hold, 8) * (0.5 - 0.08 * voice)
            pad += saw(freq * 1.003, hold, 8) * (0.5 - 0.08 * voice)
        pad *= fade
        add(left, start, pad, layers["pad"] * 0.14)
        add(right, start, np.roll(pad, 220), layers["pad"] * 0.14)  # ~5 ms : image stéréo

        if layers["choir"] > 0.0:
            choir = np.zeros_like(hold)
            vibrato = sine(4.6, hold) * 0.004
            for tone in triad:
                freq = note_hz(root, scale, tone, 1)
                choir += np.sin(2 * np.pi * freq * hold * (1.0 + vibrato)) * 0.5
                choir += np.sin(2 * np.pi * freq * 1.008 * hold) * 0.3
            choir *= fade
            add(left, start, choir, layers["choir"] * 0.10)
            add(right, start, choir, layers["choir"] * 0.10)

    # --- Basse : la fondamentale de l'accord, une note par temps -------------
    if layers["bass"] > 0.0:
        note = envelope(int(beat * 0.9 * SAMPLE_RATE), 0.006, beat * 0.35)
        for bar_index in range(bars):
            degree = spec["chords"][(bar_index // 4) % len(spec["chords"])]
            freq = note_hz(root, scale, degree, -1)
            for step in range(beats_per_bar):
                t = np.arange(len(note)) / SAMPLE_RATE
                voice = saw(freq, t, 6) * 0.7 + sine(freq, t) * 0.5
                start = at(bar_index) + int(step * beat * SAMPLE_RATE)
                add(left, start, voice * note, layers["bass"] * 0.30)
                add(right, start, voice * note, layers["bass"] * 0.30)

    # --- Arpège / ostinato : la cellule signature, en croches ---------------
    if layers["arp"] > 0.0:
        step_seconds = beat / 2.0
        note = envelope(int(step_seconds * 0.95 * SAMPLE_RATE), 0.004, step_seconds * 0.5)
        t = np.arange(len(note)) / SAMPLE_RATE
        steps = int(bars * beats_per_bar * 2)
        for step in range(steps):
            degree = spec["chords"][(step // (beats_per_bar * 8)) % len(spec["chords"])]
            semitone = MOTIF[step % len(MOTIF)]
            freq = note_hz(root, scale, degree, 1) * 2.0 ** (semitone / 12.0)
            voice = (saw(freq, t, 5) * 0.6 + sine(freq * 2, t) * 0.25) * note
            start = int(step * step_seconds * SAMPLE_RATE)
            # L'arpège alterne d'une oreille à l'autre : c'est la « séquence stéréo ».
            pan = 0.65 if step % 2 == 0 else 0.35
            add(left, start, voice, layers["arp"] * 0.13 * pan)
            add(right, start, voice, layers["arp"] * 0.13 * (1.0 - pan))

    # --- Cuivres synthétiques : stabs sur le premier temps de chaque mesure --
    if layers["brass"] > 0.0:
        note = envelope(int(beat * 1.6 * SAMPLE_RATE), 0.05, beat * 0.8)
        t = np.arange(len(note)) / SAMPLE_RATE
        for bar_index in range(0, bars, 2):
            degree = spec["chords"][(bar_index // 4) % len(spec["chords"])]
            voice = np.zeros_like(t)
            for tone in (degree, degree + 2, degree + 4):
                freq = note_hz(root, scale, tone)
                voice += saw(freq, t, 12) * 0.4 + saw(freq * 1.005, t, 12) * 0.3
            add(left, at(bar_index), voice * note, layers["brass"] * 0.10)
            add(right, at(bar_index), voice * note, layers["brass"] * 0.10)

    # --- Lead : la cellule signature, élargie, en blanches -------------------
    if layers["lead"] > 0.0:
        note = envelope(int(beat * 1.8 * SAMPLE_RATE), 0.03, beat * 0.9)
        t = np.arange(len(note)) / SAMPLE_RATE
        for index in range(bars // 2):
            semitone = MOTIF[index % len(MOTIF)]
            degree = spec["chords"][(index // 2) % len(spec["chords"])]
            freq = note_hz(root, scale, degree, 1) * 2.0 ** (semitone / 12.0)
            voice = (sine(freq, t) * 0.6 + saw(freq, t, 6) * 0.3 + sine(freq * 2, t) * 0.2) * note
            add(left, at(index * 2), voice, layers["lead"] * 0.16)
            add(right, at(index * 2), voice, layers["lead"] * 0.16)

    # --- Percussions --------------------------------------------------------
    if layers["kick"] > 0.0:
        length = int(0.30 * SAMPLE_RATE)
        t = np.arange(length) / SAMPLE_RATE
        sweep = 120.0 * np.exp(-t / 0.045) + 45.0
        kick = np.sin(2 * np.pi * np.cumsum(sweep) / SAMPLE_RATE) * envelope(length, 0.002, 0.09)
        for bar_index in range(bars):
            for step in (0, beats_per_bar // 2):
                start = at(bar_index) + int(step * beat * SAMPLE_RATE)
                add(left, start, kick, layers["kick"] * 0.55)
                add(right, start, kick, layers["kick"] * 0.55)

    if layers["snare"] > 0.0:
        length = int(0.22 * SAMPLE_RATE)
        noise = rng.normal(0.0, 1.0, length)
        body = sine(190.0, np.arange(length) / SAMPLE_RATE) * 0.35
        snare = (noise * 0.8 + body) * envelope(length, 0.001, 0.075)
        for bar_index in range(bars):
            for step in range(1, beats_per_bar, 2):
                start = at(bar_index) + int(step * beat * SAMPLE_RATE)
                add(left, start, snare, layers["snare"] * 0.30)
                add(right, start, snare, layers["snare"] * 0.30)

    if layers["hat"] > 0.0:
        length = int(0.06 * SAMPLE_RATE)
        # Différence première = passe-haut du pauvre : il ne reste que le grain.
        hat = np.diff(rng.normal(0.0, 1.0, length + 1)) * envelope(length, 0.001, 0.018)
        for step in range(int(bars * beats_per_bar * 2)):
            start = int(step * (beat / 2.0) * SAMPLE_RATE)
            gain = layers["hat"] * (0.16 if step % 2 else 0.24)
            add(left, start, hat, gain)
            add(right, start, hat, gain)

    # --- Soudure de la boucle : la queue retombe sur le début ---------------
    left[:tail] += left[loop_samples:loop_samples + tail]
    right[:tail] += right[loop_samples:loop_samples + tail]
    stereo = np.stack([left[:loop_samples], right[:loop_samples]], axis=1)

    peak = float(np.max(np.abs(stereo)))
    if peak <= 0.0:
        raise SystemExit("%s: piste muette" % name)
    return stereo / peak * 0.89


def write_wav(path: Path, stereo: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(np.round(stereo * 32767.0), -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as target:
        target.setnchannels(2)
        target.setsampwidth(2)
        target.setframerate(SAMPLE_RATE)
        target.writeframes(pcm.tobytes())


def main() -> None:
    for name, spec in STATES.items():
        stereo = render(name, spec)
        write_wav(OUTPUT / ("%s.wav" % name), stereo)
        seconds = len(stereo) / SAMPLE_RATE
        print("[music] %-20s %3d BPM  %5.1f s" % (name, spec["bpm"], seconds))


if __name__ == "__main__":
    main()
