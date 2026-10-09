"""Soundtrack for the cinematic version: "Volatile Reaction" (Kevin MacLeod, CC BY 4.0)
+ whooshes / impacts placed on the transitions of index.html (155 BPM grid).
Usage: python3 audio_v2.py music.mp3 out.wav
"""
import subprocess, sys, wave
import numpy as np

SR = 44100
DUR = 145.0
N = int(SR * DUR)
music_path, out = sys.argv[1], sys.argv[2]
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', music_path, '-t', str(DUR), '-ac', '2', '-ar', str(SR),
                      '-f', 's16le', '-'], capture_output=True, check=True).stdout
m = np.frombuffer(raw, '<i2').reshape(-1, 2) / 32768.0
mix = np.zeros((N, 2))
mix[:len(m)] = m[:N] * 0.8
rng = np.random.default_rng(3)

BEAT = 60 / 155; BAR = 4 * BEAT; PH = 0.38
B = lambda n: PH + n * BAR


def add(sig, t, gain=1.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if j > i:
        mix[i:j] += sig[:j - i, None] * gain


def whoosh(d, rise=True):
    n = int(d * SR); x = rng.standard_normal(n); tt = np.linspace(0, 1, n)
    cut = np.interp(tt, [0, .75, 1], [250, 5000, 900]) if rise else np.interp(tt, [0, 1], [4000, 300])
    y = np.empty(n); acc = 0.0
    for k in range(n):
        a = np.exp(-2 * np.pi * cut[k] / SR); acc = (1 - a) * x[k] + a * acc; y[k] = acc
    e = (tt ** 2.2) * np.exp(-((tt - .78) / .2) ** 2) + (tt > .78) * np.exp(-(tt - .78) * 14)
    y *= e
    return y / np.abs(y).max()


def impact(d=1.8):
    n = int(d * SR); tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (38 + 80 * np.exp(-tt * 14)) * tt) * np.exp(-tt * 3)
    crack = rng.standard_normal(n) * np.exp(-tt * 35) * .6
    return (boom + crack) / 1.4


def riser(d):
    n = int(d * SR); tt = np.linspace(0, 1, n)
    f = 200 + 1400 * tt ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * .4 + rng.standard_normal(n) * .25 * tt
    return s * tt ** 2


W = {}
for kind, t in [('clouds', B(6)), ('push', B(13)), ('flare', B(19)), ('zoom', B(30)), ('push', B(38)),
                ('clouds', B(48)), ('flare', B(62)), ('push', B(70)), ('clouds', B(80))]:
    if kind == 'clouds':
        add(whoosh(2.0), t - 1.55, .55); add(impact(1.2), t, .25)
    elif kind == 'push':
        add(whoosh(.9), t - .7, .4)
    elif kind == 'flare':
        add(whoosh(1.0), t - .78, .45); add(impact(1.5), t, .45)
    elif kind == 'zoom':
        add(riser(1.4), t - 1.4, .35); add(whoosh(1.2), t - .95, .5); add(impact(1.6), t, .55)
add(impact(), B(38) + 6.9, .5)            # Guinness medal stamp
add(whoosh(.8), B(58.5) - .62, .45)       # slam "PRIMERA MUJER"
add(impact(2.2), B(58.5), .8)
for k in (B(25),):                         # whip to Orizaba
    add(whoosh(.6), k - .47, .4)

t = np.arange(N) / SR
fade = np.interp(t, [0, .02, DUR - 3, DUR], [0, 1, 1, 0])
# duck the music under the spoken conclusion (last screen)
fade *= np.interp(t, [0, B(80) + .8, B(80) + 2.5, DUR], [1, 1, .5, .5])
mix *= fade[:, None]
mix = np.tanh(mix * 1.05)
mix /= np.abs(mix).max() / 0.95
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('ok')
