"""Soundtrack v3: the user's song (130 BPM, ~54 s) re-edited on its bar grid to fill the 145 s video.
- intro stretched so the beat drop lands on the 0:30 flare (start of "Sus inicios")
- body looped so a second drop lands on "PRIMERA MUJER DE LA HISTORIA" (~1:31)
- soft intro again under the spoken conclusion
+ the same whooshes / impacts as audio_v2 on the video transitions.
Usage: python3 audio_v3.py song.wav out.wav
"""
import subprocess, sys, wave
import numpy as np

SR = 44100
DUR = 145.0
N = int(SR * DUR)
src, out = sys.argv[1], sys.argv[2]
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', src, '-ac', '2', '-ar', str(SR), '-f', 's16le', '-'],
                     capture_output=True, check=True).stdout
song = np.frombuffer(raw, '<i2').reshape(-1, 2) / 32768.0
song = song / np.abs(song[:int(54 * SR)]).max() * 0.8

BAR_S = 4 * 60 / 130.02          # song bar length
D = 16.31                          # first downbeat of the drop in the song
END = D + 19 * BAR_S               # end of the usable body (before the song's outro)
SHIFT = 0.74                       # start offset so both drops sit on their visual hits

# (song_start, song_end) segments played back to back
segs = [(0.0, D),                   # intro
        (D - 7 * BAR_S, D),                      # 7 more intro bars -> drop at ~0:30
        (D, END),                                # body (19 bars)
        (D, D + 14 * BAR_S),                     # 14 bars -> next drop at ~1:31
        (D, END),                                # body again
        (D - 8 * BAR_S, D + 3 * BAR_S)]         # soft intro under the conclusion (+2 bars into the beat, faded)
music = np.zeros((N, 2))
pos = int(SHIFT * SR)
xf = int(0.03 * SR)
for a, b in segs:
    seg = song[int(a * SR):int(b * SR)].copy()
    seg[:xf] *= np.linspace(0, 1, xf)[:, None]
    seg[-xf:] *= np.linspace(1, 0, xf)[:, None]
    if a == D: print('drop at %.2f s' % (pos / SR))
    j = min(N, pos + len(seg))
    music[pos:j] += seg[:j - pos]
    pos += len(seg) - xf
    if pos >= N:
        break

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
