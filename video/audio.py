"""Synthesises the soundtrack (soft music bed + sound effects synced to the animation).
Usage: python3 audio.py soundtrack.wav
Times below mirror the timeline in index.html.
"""
import sys, wave
import numpy as np

SR = 44100
DUR = 132.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
mix = np.zeros((N, 2))


def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    j = min(N, i + len(sig))
    if j <= i:
        return
    s = sig[: j - i] * gain
    mix[i:j, 0] += s * (1 - pan) * 0.5 * 2 ** 0.5
    mix[i:j, 1] += s * (1 + pan) * 0.5 * 2 ** 0.5


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for k in range(len(x)):
        acc = (1 - a) * x[k] + a * acc
        y[k] = acc
    return y


def lp_fast(x, cutoff):
    # FFT brick-ish lowpass with soft knee (fast for long signals)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---------------- music ----------------
BPM = 96
beat = 60 / BPM
bar = 4 * beat
# A minor: Am - F - C - G (MIDI roots)
prog = [(57, [0, 3, 7]), (53, [0, 4, 7]), (60, [0, 4, 7]), (55, [0, 4, 7])]

t = np.arange(N) / SR
pad = np.zeros(N)
nbars = int(DUR / bar) + 1
for b in range(nbars):
    root, iv = prog[b % 4]
    s, e = b * bar, min(DUR, (b + 1) * bar + 0.3)
    i0, i1 = int(s * SR), int(e * SR)
    tt = t[i0:i1] - s
    chunk = np.zeros(i1 - i0)
    for k in iv + [12]:
        f = note(root + k)
        for det in (-0.12, 0.12):
            ph = 2 * np.pi * f * (1 + det / 100) * tt
            chunk += (2 * ((ph / (2 * np.pi)) % 1) - 1) * 0.5 + np.sin(ph)
    chunk += np.sin(2 * np.pi * note(root - 12) * tt) * 1.5  # bass
    chunk *= env(len(chunk), 0.25, 0.35)
    pad[i0:i1] += chunk
pad = lp_fast(pad, 900)
pad /= np.abs(pad).max()

# arpeggio plucks (enter at 21 s)
arp = np.zeros(N)
step = beat / 2
for k in range(int(DUR / step)):
    ts = k * step
    if ts < 21 or ts > 128:
        continue
    root, iv = prog[int(ts / bar) % 4]
    pat = [0, 1, 2, 1, 3, 2, 1, 2]
    m = root + 12 + (iv + [12])[pat[k % 8]]
    n = int(0.45 * SR)
    tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * note(m) * tt) + 0.3 * np.sin(4 * np.pi * note(m) * tt)) * np.exp(-tt * 9)
    i = int(ts * SR)
    arp[i:i + n] += s[: max(0, min(n, N - i))]
arp /= np.abs(arp).max()

# drums: soft kick + hat from 31 s, build 75-90, full after drop
drums = np.zeros(N)
kick_n = int(0.35 * SR)
kt = np.arange(kick_n) / SR
kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 9)
hat_n = int(0.06 * SR)
hat = rng.standard_normal(hat_n) * np.exp(-np.arange(hat_n) / SR * 70)
hat = hat - lowpass(hat, 6000)
for k in range(int(DUR / beat)):
    ts = k * beat
    if 31 <= ts < 125:
        if 88.5 <= ts < 90.5:  # breath before the slam
            continue
        add(kick, ts, 0.9 if ts >= 90.5 else 0.6)
        add(hat, ts + beat / 2, 0.18)
# build: snare roll 84 -> 88.5
sn_n = int(0.15 * SR)
sn = rng.standard_normal(sn_n) * np.exp(-np.arange(sn_n) / SR * 25)
ts, gap = 84.0, 0.4
while ts < 88.4:
    add(sn, ts, 0.15 + 0.35 * (ts - 84) / 4.4)
    ts += gap
    gap = max(0.06, gap * 0.86)

# music automation
vol = np.interp(t, [0, 2, 20, 21, 88.5, 90.5, 97, 109, 125, 129, 132],
                   [0, .55, .55, .7, .8, .9, .7, .75, .75, .5, 0])
music = (pad * 0.55 + arp * 0.28 * (t >= 21)) * vol
mix[:, 0] += music
mix[:, 1] += music
mix[:, 0] += drums
mix[:, 1] += drums


# ---------------- sound effects ----------------
def whoosh(d=0.9, up=True):
    n = int(d * SR)
    x = rng.standard_normal(n)
    tt = np.linspace(0, 1, n)
    cut = np.interp(tt, [0, .6, 1], [300, 4000, 800]) if up else np.interp(tt, [0, 1], [3000, 300])
    # time-varying lowpass
    y = np.empty(n)
    acc = 0.0
    for k in range(n):
        a = np.exp(-2 * np.pi * cut[k] / SR)
        acc = (1 - a) * x[k] + a * acc
        y[k] = acc
    e = np.sin(np.pi * tt) ** 2
    return y * e / (np.abs(y * e).max() + 1e-9)


def impact(d=1.4):
    n = int(d * SR)
    tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (40 + 70 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 3.5)
    crack = rng.standard_normal(n) * np.exp(-tt * 30) * 0.5
    return (boom + crack) / 1.3


def click(f=2200, d=0.05):
    n = int(d * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * f * tt) * np.exp(-tt * 120)


def pop(f=660):
    n = int(0.25 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * f * (1 + 0.8 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 14)


def chime(m=81):
    n = int(1.8 * SR)
    tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * note(m) * h * tt) / h for h in (1, 2.01, 3.0))
    return s * np.exp(-tt * 2.5) * 0.5


W = whoosh(0.9)
# car pass in the intro
car_n = int(2.6 * SR)
ct = np.arange(car_n) / SR
engine = np.sin(2 * np.pi * (70 + 25 * ct) * ct + 3 * np.sin(2 * np.pi * 9 * ct)) * 0.6
engine = engine * np.sin(np.pi * ct / 2.6) ** 2
for c, pan in ((engine, 0),):
    i = int(0.95 * SR)
    pans = np.linspace(-0.9, 0.9, car_n)
    mix[i:i + car_n, 0] += c * (1 - pans) * 0.25
    mix[i:i + car_n, 1] += c * (1 + pans) * 0.25
add(whoosh(1.6), 1.6, 0.35)

for T in (10, 21, 31, 47, 60, 75, 97, 109, 125):
    add(W, T - 0.55, 0.55, pan=0.3 if T % 2 else -0.3)
add(chime(88), 59.9, 0.35)          # flash
add(pop(520), 6.0, 0.35)            # badge
for i in range(4):
    add(pop(600 + 60 * i), 11.6 + i * 1.6, 0.22)   # doc rows
for i in range(4):
    add(click(1800), 22.4 + i * 1.5, 0.25)          # id rows
for k, ts in enumerate((32.6, 35.2, 37.8, 40.8)):  # milestones
    add(pop(500 + 80 * k), ts, 0.3)
add(chime(84), 41.0, 0.3)           # Orizaba flag
for k in range(1, 26):              # Everest counter ticks (follow the ease-out count)
    add(click(2600), 47.8 + 3.2 * (1 - (1 - k / 25) ** (1 / 3)), 0.1)
add(impact(1.0), 51.0, 0.35)
add(pop(700), 51.2, 0.3)            # flag
for i in range(3):
    add(pop(450 + 70 * i), 60.8 + i * 1.6, 0.3)
add(impact(), 67.25, 0.6)           # Guinness stamp
add(chime(86), 67.3, 0.3)
for i in range(14):
    add(click(2000 + 60 * i), 75.5 + i * (6.7 / 14), 0.22)
for i in range(7):
    add(pop(520 + 40 * i), 84.8 + i * 0.55, 0.22)
add(whoosh(1.2), 89.4, 0.5)
add(impact(1.8), 90.45, 0.95)       # PRIMERA MUJER slam
add(chime(81), 91.8, 0.35)
add(chime(88), 92.0, 0.2)
for i in range(21):                 # typewriter
    add(click(1400 + (i % 3) * 200, 0.04), 98.2 + i * (3.2 / 21), 0.18)
for i in range(3):
    add(whoosh(0.6), 110.0 + i * 2.6, 0.3)
add(impact(1.0), 119.4, 0.4)
add(chime(81), 125.3, 0.4)
add(chime(76), 125.6, 0.3)

# ---------------- master ----------------
fade = np.interp(t, [0, 0.05, DUR - 1.5, DUR], [0, 1, 1, 0])
mix *= fade[:, None]
mix = np.tanh(mix * 1.1)
mix /= np.abs(mix).max() / 0.6

with wave.open(sys.argv[1] if len(sys.argv) > 1 else 'soundtrack.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('ok')
