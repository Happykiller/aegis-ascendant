#!/usr/bin/env python3
"""Masterise les sources audio et écrit ce que le moteur importe réellement.

    assets/source/audio/sfx/*.wav    -> assets/imported/audio/sfx/*.wav    (WAV, importé en QOA)
    assets/source/audio/music/*.wav  -> assets/imported/audio/music/*.ogg  (Vorbis, via ffmpeg)

`source/` est le rendu brut du synthé ; `imported/` est la version masterisée — c'est
ce qui justifie que les deux existent (voir ADR-0007). Traitement (spec §18.5) :
DC retiré, fondu de sortie anti-clic, et une assertion qui échoue plutôt que de livrer
un fichier qui clippe.

La normalisation, elle, DIFFÈRE selon la nature du signal — et c'est le point :
    SFX     -> normalisation en CRÊTE (-1 dBFS) : des transitoires courtes ont besoin
               de leur marge dynamique.
    Musique -> normalisation en LOUDNESS (RMS) + arrondi des crêtes : normalisée au
               pic, une musique dynamique est perçue ~9 dB sous les SFX et disparaît
               sous le tir du joueur.

Idempotent : relancer le script sur les mêmes sources laisse `git status` propre.
Usage : python3 tools/audio/build_audio.py
"""

from __future__ import annotations

import math
import struct
import subprocess
import sys
import wave
from pathlib import Path

SFX_SOURCE = Path("assets/source/audio/sfx")
SFX_OUTPUT = Path("assets/imported/audio/sfx")
MUSIC_SOURCE = Path("assets/source/audio/music")
MUSIC_OUTPUT = Path("assets/imported/audio/music")

## -1 dBFS : on garde un cheveu de marge sous le plein échelle, le limiteur du bus
## Master fait le reste.
TARGET_PEAK = 10.0 ** (-1.0 / 20.0)
FADE_OUT_SECONDS = 0.005

## La musique est normalisée en LOUDNESS (RMS), les SFX en CRÊTE. Les traiter à
## l'identique était le bug : une musique dynamique normalisée au pic reste perçue très
## faible. Mesuré le 12/07/2026 sur les pistes livrées — même crête, loudness opposée :
##
##     musique  : crête -1 dBFS, RMS -17 dBFS   (facteur de crête 16 dB)
##     SFX tir  : crête -1 dBFS, RMS  -8 dBFS   (dense, écrasé vers le haut)
##
## Résultat en jeu : la musique disparaissait sous le tir du joueur, curseur à fond — et
## aucun réglage ne pouvait la rattraper, les curseurs plafonnant à 0 dB.
##
## -16 dBFS : réglé à l'oreille par l'opérateur (12/07/2026). -14 portait bien mais passait
## devant l'action ; -16 laisse la partition sous les SFX sans la faire disparaître.
TARGET_RMS = 10.0 ** (-16.0 / 20.0)

## Remonter le RMS de ~3 dB ferait écrêter une musique dont la crête est déjà à -1 dBFS.
## Au-dessus du genou, les crêtes sont donc ARRONDIES (tanh) au lieu d'être tranchées :
## la sortie tend vers TARGET_PEAK sans jamais l'atteindre, donc sans clipping.
LIMITER_KNEE = 0.55
## Qualité Vorbis : ~5 Mo pour les neuf pistes, transparent sur du synthé.
VORBIS_QUALITY = "4"

## Ces cues sont bouclés en jeu : un fondu de sortie y créerait le trou que la
## construction du signal évite précisément.
NO_FADE = {"engine_loop"}


def read_wav(path: Path) -> tuple[list[float], int, int]:
    with wave.open(str(path), "rb") as source:
        if source.getsampwidth() != 2:
            raise SystemExit("%s: seul le PCM 16 bits est géré" % path)
        channels = source.getnchannels()
        rate = source.getframerate()
        raw = source.readframes(source.getnframes())
    count = len(raw) // 2
    samples = struct.unpack("<%dh" % count, raw)
    return [value / 32768.0 for value in samples], channels, rate


def write_wav(path: Path, samples: list[float], channels: int, rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = b"".join(struct.pack("<h", int(round(value * 32767.0))) for value in samples)
    with wave.open(str(path), "wb") as target:
        target.setnchannels(channels)
        target.setsampwidth(2)
        target.setframerate(rate)
        target.writeframes(pcm)


def soft_limit(value: float) -> float:
    """Arrondit une crête au-dessus du genou au lieu de la trancher (waveshaper tanh)."""
    magnitude = abs(value)
    if magnitude <= LIMITER_KNEE:
        return value
    over = (magnitude - LIMITER_KNEE) / (1.0 - LIMITER_KNEE)
    shaped = LIMITER_KNEE + (TARGET_PEAK - LIMITER_KNEE) * math.tanh(over)
    return shaped if value >= 0.0 else -shaped


def master(samples: list[float], channels: int, rate: int, fade: bool,
           loudness: bool = False) -> list[float]:
    mean = sum(samples) / max(1, len(samples))
    samples = [value - mean for value in samples]
    peak = max((abs(value) for value in samples), default=0.0)
    if peak <= 0.0:
        raise SystemExit("signal muet")
    if loudness:
        # Viser une loudness, pas une crête — puis arrondir ce qui dépasse.
        rms = math.sqrt(sum(value * value for value in samples) / len(samples))
        if rms <= 0.0:
            raise SystemExit("signal muet")
        gain = TARGET_RMS / rms
        samples = [soft_limit(value * gain) for value in samples]
    else:
        samples = [value * (TARGET_PEAK / peak) for value in samples]
    if fade:
        fade_frames = min(int(FADE_OUT_SECONDS * rate), len(samples) // channels)
        for frame in range(fade_frames):
            gain = frame / fade_frames
            index = len(samples) - (fade_frames - frame) * channels
            for channel in range(channels):
                samples[index + channel] *= gain
    final_peak = max(abs(value) for value in samples)
    if final_peak >= 1.0:
        raise SystemExit("clipping: crête %.4f >= 1.0" % final_peak)
    return samples


def build_sfx() -> int:
    built = 0
    for source in sorted(SFX_SOURCE.glob("*.wav")):
        samples, channels, rate = read_wav(source)
        fade = source.stem not in NO_FADE
        write_wav(SFX_OUTPUT / source.name, master(samples, channels, rate, fade), channels, rate)
        built += 1
    return built


def build_music() -> int:
    if not MUSIC_SOURCE.is_dir():
        return 0
    built = 0
    for source in sorted(MUSIC_SOURCE.glob("*.wav")):
        # La musique est masterisée en WAV puis encodée : ffmpeg ne fait que l'encodage,
        # pour que le mastering reste sous notre contrôle et reproductible.
        samples, channels, rate = read_wav(source)
        staged = MUSIC_OUTPUT / (source.stem + ".staged.wav")
        write_wav(staged, master(samples, channels, rate, fade=False, loudness=True),
                  channels, rate)
        target = MUSIC_OUTPUT / (source.stem + ".ogg")
        # -bitexact : sans lui, ffmpeg tire un numéro de série de flux Ogg au hasard et
        # chaque encodage produit un fichier différent — le build ne serait pas reproductible.
        result = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(staged),
             "-c:a", "libvorbis", "-q:a", VORBIS_QUALITY, "-bitexact", str(target)],
            check=False,
        )
        staged.unlink()
        if result.returncode != 0:
            raise SystemExit("ffmpeg a échoué sur %s" % source.name)
        built += 1
    return built


def main() -> None:
    if not SFX_SOURCE.is_dir():
        raise SystemExit("sources introuvables: %s (lancer depuis la racine du dépôt)" % SFX_SOURCE)
    sfx = build_sfx()
    music = build_music()
    print("[audio] %d SFX -> %s" % (sfx, SFX_OUTPUT))
    print("[audio] %d piste(s) -> %s" % (music, MUSIC_OUTPUT))


if __name__ == "__main__":
    main()
