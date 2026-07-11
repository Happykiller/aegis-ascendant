#!/usr/bin/env python3
"""Génère les SFX de prototype originaux d'Aegis Ascendant."""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44_100
PEAK = 0.88
OUTPUT = Path("assets/source/audio/sfx")


def envelope(t: float, duration: float, attack: float = 0.01, release: float = 0.25) -> float:
    rise = min(1.0, t / max(attack, 1e-6))
    fall = min(1.0, (duration - t) / max(release, 1e-6))
    return max(0.0, rise * fall)


def sine(phase: float) -> float:
    return math.sin(math.tau * phase)


def write_wav(name: str, duration: float, sampler) -> None:
    count = int(duration * SAMPLE_RATE)
    values = [sampler(i / SAMPLE_RATE, duration) for i in range(count)]
    mean = sum(values) / max(1, len(values))
    values = [value - mean for value in values]
    maximum = max(abs(value) for value in values) or 1.0
    scale = PEAK / maximum
    pcm = b"".join(struct.pack("<h", round(value * scale * 32767)) for value in values)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUTPUT / name), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(SAMPLE_RATE)
        target.writeframes(pcm)


def swept_tone(start: float, end: float, t: float, duration: float) -> float:
    rate = start + (end - start) * (t / duration)
    return sine(rate * t)


def main() -> None:
    rng = random.Random(0xAE615)

    write_wav("player_pulse.wav", 0.18, lambda t, d:
              envelope(t, d, 0.004, 0.09) *
              (0.75 * swept_tone(980, 540, t, d) + 0.25 * sine(1_960 * t)))

    write_wav("enemy_pulse.wav", 0.27, lambda t, d:
              envelope(t, d, 0.008, 0.16) *
              (0.65 * swept_tone(410, 120, t, d) + 0.35 * sine(67 * t) * sine(730 * t)))

    write_wav("hull_impact.wav", 0.24, lambda t, d:
              envelope(t, d, 0.001, 0.2) *
              (0.58 * rng.uniform(-1, 1) + 0.42 * sine((190 - 100 * t / d) * t)))

    write_wav("shield_impact.wav", 0.38, lambda t, d:
              envelope(t, d, 0.003, 0.3) *
              (0.55 * sine((1_180 + 420 * t / d) * t) +
               0.30 * sine((1_760 - 310 * t / d) * t) + 0.15 * rng.uniform(-1, 1)))

    write_wav("small_explosion.wav", 0.64, lambda t, d:
              envelope(t, d, 0.001, 0.58) *
              (0.68 * rng.uniform(-1, 1) * (1 - 0.55 * t / d) +
               0.32 * sine((105 - 55 * t / d) * t)))

    write_wav("pickup_collect.wav", 0.42, lambda t, d:
              envelope(t, d, 0.006, 0.12) *
              (0.45 * sine((520 + 820 * t / d) * t) +
               0.35 * sine((780 + 1_140 * t / d) * t) + 0.20 * sine(2_080 * t)))

    write_wav("danger_alarm.wav", 0.82, lambda t, d:
              envelope(t, d, 0.008, 0.08) *
              sine((310 if int(t * 8) % 2 == 0 else 470) * t) *
              (0.75 + 0.25 * sine(9 * t)))

    write_wav("docking_lock.wav", 0.72, lambda t, d:
              envelope(t, d, 0.002, 0.3) *
              (0.42 * rng.uniform(-1, 1) * max(0.0, 1 - t * 5) +
               0.38 * sine((145 + 90 * t / d) * t) + 0.20 * sine(690 * t)))

    write_wav("rail_battery.wav", 0.96, lambda t, d:
              envelope(t, d, 0.018, 0.62) *
              (0.48 * swept_tone(90, 42, t, d) +
               0.30 * swept_tone(680, 180, t, d) + 0.22 * rng.uniform(-1, 1)))

    write_wav("helios_lance.wav", 1.82, lambda t, d:
              envelope(t, d, 0.16, 0.46) *
              (0.36 * sine((160 + 720 * min(1, t / 0.9)) * t) +
               0.28 * sine((320 + 1_080 * min(1, t / 0.9)) * t) +
               0.20 * sine(74 * t) + 0.16 * rng.uniform(-1, 1) * min(1, t / 0.7)))


if __name__ == "__main__":
    main()
