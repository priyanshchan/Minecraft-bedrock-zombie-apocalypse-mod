#!/usr/bin/env python3
"""Synthesises every sound effect of the add-on (numpy -> wav -> ogg via ffmpeg).

Nothing is sampled: each sound is built from noise, oscillators and filters below, so the
output is original and re-running gives the same files.
Usage:  python3 tools/gen/audio.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

from defs import LOUD_SOUNDS, NS, RP, SOUNDS

SR = 32000


def t_(dur):
    return np.arange(int(SR * dur)) / SR


def noise(n, seed):
    return np.random.default_rng(seed).uniform(-1.0, 1.0, n)


def filt(x, lo=None, hi=None, order=2):
    """Zero-phase band filter in the frequency domain."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    gain = np.ones_like(f)
    if hi:
        gain /= np.sqrt(1 + (f / hi) ** (2 * order))
    if lo:
        with np.errstate(divide="ignore"):
            gain /= np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    return np.fft.irfft(spec * gain, len(x))


def decay(n, seconds):
    return np.exp(-np.arange(n) / SR / seconds)


def swell(n, attack, release):
    t = np.arange(n) / SR
    total = n / SR
    return np.clip(t / max(attack, 1e-4), 0, 1) * np.clip((total - t) / max(release, 1e-4), 0, 1)


def osc(freq, n, kind="sine"):
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    phase = np.cumsum(f) / SR
    if kind == "saw":
        return 2 * (phase % 1.0) - 1
    if kind == "square":
        return np.sign(np.sin(2 * np.pi * phase))
    return np.sin(2 * np.pi * phase)


def place(out, x, at):
    i = int(at * SR)
    end = min(len(out), i + len(x))
    out[i:end] += x[: end - i]
    return out


def echo(x, delays=((0.11, 0.35), (0.23, 0.2), (0.41, 0.1))):
    out = x.copy()
    for d, g in delays:
        i = int(d * SR)
        if i < len(x):
            out[i:] += x[: len(x) - i] * g
    return out


def pad(x, seconds):
    return np.concatenate([x, np.zeros(int(seconds * SR))])


def norm(x, peak=0.8):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


# ---------------------------------------------------------------- weapons

def gunshot(seed, body_hz, crack_decay, boom_decay, tail, lowpass):
    n = int(SR * (0.25 + tail))
    crack = filt(noise(n, seed), 400, lowpass) * decay(n, crack_decay)
    boom = osc(body_hz * (1 + 2 * decay(n, 0.01)), n) * decay(n, boom_decay) * 0.9
    rumble = filt(noise(n, seed + 1), 30, 400) * decay(n, tail / 2.5) * 0.6
    x = crack + boom + rumble
    x[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return echo(np.tanh(x * 2.2), ((0.09, 0.3), (0.21, 0.18), (0.38, 0.1), (0.6, 0.05)))


def s_pistol():
    return gunshot(1, 150, 0.025, 0.05, 0.45, 7500)


def s_smg():
    return gunshot(11, 170, 0.02, 0.035, 0.3, 8000)


def s_assault_rifle():
    return gunshot(12, 120, 0.03, 0.06, 0.6, 7000)


def s_lmg():
    return gunshot(13, 100, 0.035, 0.08, 0.7, 6000)


def s_shotgun():
    shot = gunshot(2, 80, 0.06, 0.12, 0.7, 4000)
    out = pad(shot, 0.4)
    place(out, s_click(4, 2200) * 0.6, 0.62)
    place(out, filt(noise(int(0.08 * SR), 5), 800, 3000) * decay(int(0.08 * SR), 0.02) * 0.5, 0.66)
    place(out, s_click(6, 1800) * 0.7, 0.78)
    return out


def s_sniper():
    return gunshot(3, 95, 0.03, 0.1, 1.4, 8500)


def s_click(seed=7, ping=3200):
    n = int(0.06 * SR)
    tick = filt(noise(n, seed), 2000, None) * decay(n, 0.003)
    ring = osc(ping, n) * decay(n, 0.012) * 0.4
    return tick + ring


def s_dry_fire():
    return s_click(8, 2800)


def s_reload():
    out = np.zeros(int(0.95 * SR))
    place(out, s_click(9, 2600), 0.0)
    slide = filt(noise(int(0.14 * SR), 10), 1500, 5000) * swell(int(0.14 * SR), 0.02, 0.05) * 0.4
    place(out, slide, 0.12)
    clunk = osc(220, int(0.1 * SR)) * decay(int(0.1 * SR), 0.02) * 0.6
    place(out, clunk, 0.42)
    place(out, s_click(11, 1900), 0.42)
    place(out, s_click(12, 2400), 0.72)
    place(out, slide * 0.8, 0.75)
    place(out, s_click(13, 3000), 0.88)
    return out


def boom(seed, seconds, low, crack_hi):
    n = int(SR * seconds)
    body = filt(noise(n, seed), 20, low) * decay(n, seconds / 4) * 1.6
    thump = osc(45 * (1 + 3 * decay(n, 0.03)), n) * decay(n, 0.25)
    crack = filt(noise(n, seed + 1), 500, crack_hi) * decay(n, 0.05) * 0.8
    debris = filt(noise(n, seed + 2), 1500, 6000) * decay(n, seconds / 3) * 0.15 * (np.random.default_rng(seed).random(n) < 0.05)
    x = np.tanh((body + thump + crack + debris) * 2.4)
    x[: int(0.003 * SR)] *= np.linspace(0, 1, int(0.003 * SR))
    return echo(x, ((0.18, 0.3), (0.4, 0.18), (0.75, 0.1)))


def s_explosion():
    return boom(20, 2.4, 300, 4000)


def s_tank_fire():
    out = boom(21, 2.0, 220, 3000)
    place(out, s_click(22, 900) * 0.8, 1.2)
    place(out, osc(180, int(0.2 * SR)) * decay(int(0.2 * SR), 0.05) * 0.5, 1.25)
    return out


def s_rocket_launch():
    n = int(SR * 1.6)
    t = np.arange(n) / SR
    whoosh = filt(noise(n, 23), 300, 2500) * swell(n, 0.02, 1.2) * (1 - 0.5 * t / 1.6)
    thump = osc(70, n) * decay(n, 0.08) * 1.2
    return np.tanh((whoosh * 1.4 + thump) * 1.5)


def s_grenade_pin():
    out = np.zeros(int(0.5 * SR))
    place(out, osc(4200, int(0.2 * SR)) * decay(int(0.2 * SR), 0.05) * 0.5, 0.0)
    place(out, s_click(24, 3600), 0.0)
    place(out, s_click(25, 2000) * 0.8, 0.25)
    return out


def tone(freq, seconds, kind="sine", bright=0.3):
    n = int(SR * seconds)
    x = osc(freq, n, kind) * (1 - bright) + osc(freq * 2, n) * bright
    return x * decay(n, seconds / 2.5) * swell(n, 0.005, 0.05)


def s_hitmarker():
    n = int(0.08 * SR)
    return (osc(1900, n) * 0.6 + filt(noise(n, 30), 3000, None) * 0.4) * decay(n, 0.015)


def s_kill():
    out = np.zeros(int(0.45 * SR))
    place(out, tone(1320, 0.18), 0.0)
    place(out, tone(1760, 0.3), 0.09)
    return out


def jingle(notes, step=0.12, kind="square"):
    out = np.zeros(int(SR * (step * len(notes) + 0.6)))
    for i, f in enumerate(notes):
        place(out, filt(tone(f, 0.45, kind, 0.2), None, 3500), i * step)
    return out


def s_capture():
    return jingle([523, 659, 784, 1046])


def s_capture_lost():
    return jingle([784, 622, 523, 392], 0.14)


def s_alarm():
    n = int(SR * 3.5)
    t = np.arange(n) / SR
    freq = 520 + 380 * (0.5 - 0.5 * np.cos(2 * np.pi * t / 1.75))
    x = osc(freq, n) + 0.35 * osc(freq * 2, n) + 0.15 * osc(freq * 3.01, n)
    return x * swell(n, 0.2, 0.6)


def s_battle_start():
    n = int(SR * 3.5)
    x = osc(110, n, "saw") + 0.7 * osc(165, n, "saw") + 0.4 * osc(220.5, n, "saw")
    x = filt(x, 60, 1400)
    return echo(np.tanh(x * 1.3) * swell(n, 0.4, 1.4), ((0.3, 0.3), (0.7, 0.15)))


def brass(freq, seconds):
    n = int(SR * seconds)
    x = osc(freq, n, "saw") + 0.5 * osc(freq * 1.005, n, "saw")
    return filt(x, 80, 2200) * swell(n, 0.04, seconds * 0.4)


def s_victory():
    out = np.zeros(int(SR * 2.6))
    for i, (f, d) in enumerate(((392, 0.2), (523, 0.2), (659, 0.2), (784, 1.3))):
        place(out, brass(f, d + 0.3), i * 0.2)
        if i == 3:
            place(out, brass(523, 1.6) * 0.6, 0.6)
            place(out, brass(659, 1.6) * 0.5, 0.6)
    return echo(out, ((0.25, 0.25),))


def s_defeat():
    out = np.zeros(int(SR * 2.8))
    for i, f in enumerate((392, 370, 349, 262)):
        place(out, brass(f, 0.9 if i < 3 else 1.6), i * 0.45)
    return echo(out, ((0.3, 0.25),))


def s_radio():
    n = int(SR * 1.4)
    t = np.arange(n) / SR
    static = filt(noise(n, 40), 500, 4500) * (0.6 + 0.4 * (filt(noise(n, 41), None, 12) > 0))
    beeps = osc(1000, n) * ((t > 0.5) & (t < 0.62) | (t > 0.75) & (t < 0.87)) * 0.5
    return (static * 0.7 + beeps) * swell(n, 0.03, 0.2)


def s_heal():
    out = np.zeros(int(SR * 1.0))
    for i, f in enumerate((880, 1109, 1319, 1760)):
        place(out, tone(f, 0.5, "sine", 0.1) * 0.5, i * 0.07)
    return out


def s_resupply():
    out = np.zeros(int(SR * 0.9))
    rng = np.random.default_rng(50)
    for i in range(7):
        m = int(rng.uniform(0.03, 0.08) * SR)
        part = filt(noise(m, 51 + i), rng.uniform(400, 1500), rng.uniform(2500, 6000)) * decay(m, 0.02)
        place(out, part * rng.uniform(0.4, 1.0), rng.uniform(0, 0.5))
    place(out, s_click(60, 1500), 0.6)
    place(out, s_click(61, 2100), 0.7)
    return out


def s_repair():
    out = np.zeros(int(SR * 0.8))
    for i in range(5):
        place(out, s_click(70 + i, 1200 + 300 * (i % 2)) * 0.9, i * 0.13)
    hiss = filt(noise(int(0.6 * SR), 79), 2500, 8000) * swell(int(0.6 * SR), 0.05, 0.2) * 0.25
    place(out, hiss, 0.1)
    return out


def s_click_ui():
    return s_click(90, 2400)


def s_engine():
    n = int(SR * 0.6)
    t = np.arange(n) / SR
    x = osc(48 * (1 + 0.05 * np.sin(2 * np.pi * 9 * t)), n, "saw") * (0.7 + 0.3 * osc(14, n))
    x = filt(x + 0.2 * noise(n, 95), 30, 500)
    return x * swell(n, 0.08, 0.15)


BUILDERS = {
    "pistol": s_pistol, "smg": s_smg, "assault_rifle": s_assault_rifle, "lmg": s_lmg, "shotgun": s_shotgun,
    "sniper": s_sniper, "rocket_launch": s_rocket_launch, "explosion": s_explosion, "tank_fire": s_tank_fire,
    "dry_fire": s_dry_fire, "reload": s_reload, "grenade_pin": s_grenade_pin, "hitmarker": s_hitmarker,
    "kill": s_kill, "capture": s_capture, "capture_lost": s_capture_lost, "alarm": s_alarm,
    "battle_start": s_battle_start, "victory": s_victory, "defeat": s_defeat, "radio": s_radio, "heal": s_heal,
    "resupply": s_resupply, "repair": s_repair, "click": s_click_ui, "engine": s_engine,
}

CATEGORY = {"explosion": "weather", "tank_fire": "hostile", "alarm": "ambient", "battle_start": "ambient",
            "engine": "neutral"}
RANGE = {"sniper": 160.0, "explosion": 160.0, "tank_fire": 160.0, "lmg": 112.0, "assault_rifle": 112.0,
         "shotgun": 96.0, "pistol": 80.0, "smg": 80.0, "rocket_launch": 112.0, "alarm": 160.0,
         "battle_start": 200.0, "engine": 24.0}
VOLUME = {"alarm": 0.6, "click": 0.6, "hitmarker": 0.8, "engine": 0.5, "victory": 0.9, "defeat": 0.9}


def write_wav(path, x):
    data = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def main():
    assert set(BUILDERS) == set(SOUNDS), set(BUILDERS) ^ set(SOUNDS)
    out = RP / "sounds" / NS
    out.mkdir(parents=True, exist_ok=True)
    have_ffmpeg = shutil.which("ffmpeg") is not None
    defs = {}
    with tempfile.TemporaryDirectory() as tmp:
        for name in SOUNDS:
            dst = out / f"{name}.ogg"
            if have_ffmpeg:
                x = norm(BUILDERS[name](), 0.9 if name in LOUD_SOUNDS else 0.75)
                wav = Path(tmp) / f"{name}.wav"
                write_wav(wav, x)
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis",
                                "-q:a", "4", str(dst)], check=True)
            elif not dst.exists():
                raise RuntimeError("ffmpeg is required to encode the sounds")
            defs[f"{NS}.{name}"] = {
                "category": CATEGORY.get(name, "player"),
                "min_distance": 1.0,
                "max_distance": RANGE.get(name, 32.0),
                "sounds": [{"name": f"sounds/{NS}/{name}", "volume": VOLUME.get(name, 1.0), "load_on_low_memory": True}],
            }
    (RP / "sounds" / "sound_definitions.json").write_text(
        json.dumps({"format_version": "1.20.20", "sound_definitions": defs}, indent=2) + "\n", encoding="utf-8")
    print(f"audio: {len(defs)} sounds")


if __name__ == "__main__":
    main()
