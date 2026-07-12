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


def arpeggio(root: float, steps: tuple[float, ...], t: float, duration: float) -> float:
    """Une note par palier ; chaque note est un demi-ton de `steps` au-dessus de `root`."""
    step = min(int(t / duration * len(steps)), len(steps) - 1)
    freq = root * (2.0 ** (steps[step] / 12.0))
    # Chaque note repart de zéro : sinon les paliers claquent.
    local = t - step * duration / len(steps)
    return sine(freq * local) * envelope(local, duration / len(steps), 0.004, 0.05)


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

    # (pickup_collect a été retiré : remplacé par pickup_power/shield/score, un son par
    # bonus. Son échantillonneur n'appelait pas le rng, sa suppression ne décale donc
    # aucun des sons suivants — voir ADR-0007.)

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

    # --- v2 : les cues que le graybox déclenchait avec un son emprunté ---------
    # Les nouveaux cues sont ajoutés APRÈS les dix premiers : le rng est partagé et
    # séquentiel, insérer au milieu décalerait le bruit de tous les sons existants.

    # Trois calibres d'explosion, pour que la mort d'un chasseur, celle d'un mini-boss
    # et celle du Léviathan ne soient plus le même échantillon monté en volume.
    write_wav("medium_explosion.wav", 0.92, lambda t, d:
              envelope(t, d, 0.001, 0.82) *
              (0.62 * rng.uniform(-1, 1) * (1 - 0.6 * t / d) +
               0.26 * sine((78 - 42 * t / d) * t) + 0.12 * sine((150 - 90 * t / d) * t)))

    write_wav("heavy_explosion.wav", 1.45, lambda t, d:
              envelope(t, d, 0.002, 1.25) *
              (0.50 * rng.uniform(-1, 1) * (1 - 0.7 * t / d) +
               0.30 * sine((52 - 28 * t / d) * t) +
               0.20 * sine((31 - 12 * t / d) * t)))

    # Un bonus doit s'entendre, pas seulement se voir : couleur + forme + son distincts
    # (CHARTE_CREATIVE §5 — jamais la couleur seule).
    write_wav("pickup_power.wav", 0.46, lambda t, d:      # triade ascendante, énergique
              0.9 * arpeggio(523.25, (0, 7, 12), t, d) + 0.1 * sine(1_046 * t) * envelope(t, d, 0.01, 0.2))

    write_wav("pickup_shield.wav", 0.52, lambda t, d:     # cluster cristallin, protecteur
              envelope(t, d, 0.006, 0.4) *
              (0.40 * sine(880 * t) + 0.30 * sine(1_320 * t) +
               0.20 * sine(1_760 * t) + 0.10 * sine(2_640 * t)))

    write_wav("pickup_score.wav", 0.34, lambda t, d:      # arpège bref et brillant
              arpeggio(783.99, (0, 4, 7, 12), t, d))

    # UI : discrète, jamais dans le chemin des alarmes.
    write_wav("ui_select.wav", 0.08, lambda t, d:
              envelope(t, d, 0.002, 0.05) * sine(1_320 * t))

    write_wav("ui_confirm.wav", 0.26, lambda t, d:
              0.85 * arpeggio(659.26, (0, 7), t, d) + 0.15 * sine(1_318 * t) * envelope(t, d, 0.01, 0.12))

    write_wav("ui_banner.wav", 0.55, lambda t, d:         # gonflement doux sous la bannière
              envelope(t, d, 0.14, 0.34) *
              (0.55 * sine((196 + 66 * t / d) * t) + 0.30 * sine((294 + 98 * t / d) * t) +
               0.15 * sine(588 * t)))

    write_wav("player_death.wav", 1.15, lambda t, d:      # souffle + descente : on a perdu la coque
              envelope(t, d, 0.002, 0.95) *
              (0.55 * rng.uniform(-1, 1) * (1 - 0.55 * t / d) +
               0.30 * swept_tone(420, 60, t, d) + 0.15 * sine((96 - 54 * t / d) * t)))

    write_wav("boss_phase_shift.wav", 1.05, lambda t, d:  # impact sec puis montée de tension
              envelope(t, d, 0.001, 0.7) *
              (0.42 * rng.uniform(-1, 1) * max(0.0, 1 - t * 9) +
               0.34 * swept_tone(110, 330, t, d) + 0.24 * sine(55 * t)))

    # Boucle moteur : bouclée par construction. Toutes les partielles sont des
    # multiples entiers de 1/durée, donc l'onde vaut exactement zéro aux deux bouts
    # et se raccorde sans clic — pas d'enveloppe, pas de bruit apériodique.
    loop_seconds = 2.0
    base = 1.0 / loop_seconds
    partials = [(k, rng.uniform(0.0, 1.0)) for k in (37, 74, 111, 148, 222, 296)]
    write_wav("engine_loop.wav", loop_seconds, lambda t, d: sum(
        (1.0 / (i + 1)) * sine(k * base * t + phase) for i, (k, phase) in enumerate(partials)))


if __name__ == "__main__":
    main()
