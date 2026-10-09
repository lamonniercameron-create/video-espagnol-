"""Generates soft transparent cloud sprites (PNG) used for the fly-through transitions."""
import numpy as np
from PIL import Image
import sys, os
out = sys.argv[1] if len(sys.argv) > 1 else 'assets/clouds'
os.makedirs(out, exist_ok=True)
N = 768
def fbm(seed, oct=6):
    rng = np.random.default_rng(seed)
    acc = np.zeros((N, N)); amp = 1.0; tot = 0
    for o in range(oct):
        res = 4 * 2 ** o
        g = rng.random((res + 1, res + 1))
        img = np.array(Image.fromarray((g * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC), float) / 255
        acc += img * amp; tot += amp; amp *= 0.55
    return acc / tot
yy, xx = np.mgrid[0:N, 0:N] / N - 0.5
for k in range(8):
    rng = np.random.default_rng(100 + k)
    # blob made of several gaussian puffs
    shape = np.zeros((N, N))
    for _ in range(7):
        cx, cy = rng.normal(0, .12, 2); r = rng.uniform(.12, .22)
        shape = np.maximum(shape, np.exp(-((xx - cx) ** 2 + (yy - cy * .6) ** 2) / (2 * r * r)))
    n = fbm(k)
    a = np.clip((shape * (0.55 + 0.9 * n) - 0.35) * 1.8, 0, 1) ** 1.3
    shade = np.clip(0.78 + 0.35 * (n - 0.5) - 0.25 * (yy + 0.1), 0.55, 1.0)
    warm = np.array([255, 244, 236]) if k % 2 else np.array([248, 250, 255])
    rgb = (shade[..., None] * warm).astype(np.uint8)
    Image.fromarray(np.dstack([rgb, (a * 255).astype(np.uint8)]), 'RGBA').save(f'{out}/c{k}.png')
print('ok')
