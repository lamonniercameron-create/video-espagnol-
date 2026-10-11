"""Soundtrack v4: the full song ("Caliente", Inna), played in ONE continuous take from the very first
second of the video to the end - no edit, no loop. The record-label logo at the start of the
source clip is skipped (song starts at 3.1 s in the file).
+ the same whooshes / impacts on the video transitions, music lowered under the spoken conclusion.
Usage: python3 audio_v4.py song_clip.mp4 out.wav
"""
import subprocess, sys, wave
import numpy as np

SR = 44100
DUR = 145.0
N = int(SR * DUR)
SONG_START = 3.1          # end of the label logo in the source clip
src, out = sys.argv[1], sys.argv[2]
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', str(SONG_START), '-i', src, '-t', str(DUR), '-vn',
                      '-ac', '2', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True).stdout
song = np.frombuffer(raw, '<i2').reshape(-1, 2) / 32768.0
music = np.zeros((N, 2))
music[:min(N, len(song))] = song[:N]
fi = int(0.15 * SR)
music[:fi] *= np.linspace(0, 1, fi)[:, None]
music /= np.abs(music).max() / 0.8
mix = music * 0.85
rng = np.random.default_rng(3)
BEAT = 60 / 155; BAR = 4 * BEAT; PH = 0.38
B = lambda n: PH + n * BAR


def add(sig, t, gain=1.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if j > i:
        mix[i:j] += sig[:j - i, None] * gain


def whoosh(d):
    n = int(d * SR); x = rng.standard_normal(n); tt = np.linspace(0, 1, n)
    cut = np.interp(tt, [0, .75, 1], [250, 5000, 900])
    y = np.empty(n); acc = 0.0
    for k in range(n):
        a = np.exp(-2 * np.pi * cut[k] / SR); acc = (1 - a) * x[k] + a * acc; y[k] = acc
    y *= (tt ** 2.2) * np.exp(-((tt - .78) / .2) ** 2) + (tt > .78) * np.exp(-(tt - .78) * 14)
    return y / np.abs(y).max()


def impact(d=1.8):
    n = int(d * SR); tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (38 + 80 * np.exp(-tt * 14)) * tt) * np.exp(-tt * 3)
    return (boom + rng.standard_normal(n) * np.exp(-tt * 35) * .6) / 1.4


for kind, t in [('clouds', B(6)), ('push', B(13)), ('flare', B(19)), ('zoom', B(30)), ('push', B(38)),
                ('clouds', B(48)), ('flare', B(62)), ('push', B(70)), ('clouds', B(80))]:
    if kind == 'clouds':
        add(whoosh(2.0), t - 1.55, .4); add(impact(1.2), t, .18)
    elif kind == 'push':
        add(whoosh(.9), t - .7, .3)
    elif kind == 'flare':
        add(whoosh(1.0), t - .78, .35); add(impact(1.5), t, .3)
    elif kind == 'zoom':
        add(whoosh(1.2), t - .95, .4); add(impact(1.6), t, .4)
add(impact(), B(38) + 6.9, .4)
add(whoosh(.8), B(58.5) - .62, .35)
add(impact(2.2), B(58.5), .6)

t = np.arange(N) / SR
fade = np.interp(t, [0, .02, DUR - 3, DUR], [0, 1, 1, 0])
fade *= np.interp(t, [0, B(80) + .8, B(80) + 2.5, DUR], [1, 1, .6, .6])
mix *= fade[:, None]
mix = np.tanh(mix * 1.05)
mix /= np.abs(mix).max() / 0.95
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('ok')
