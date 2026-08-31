from pathlib import Path

import numpy as np
from PIL import Image

OUT_DIR = Path(__file__).resolve().parent
W, H = 5120, 2880
ASPECT = W / H

LEVELS = 30
INDEX_EVERY = 5
LINE_PX = 2.6
INDEX_PX = 5.2


def hex_to_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i : i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255.0


SELECTION = hex_to_rgb("#264f78")
ACCENT = hex_to_rgb("#1f6feb")
ACCENT_HOVER = hex_to_rgb("#388bfd")
TYPE = hex_to_rgb("#4ec9b0")
VARIABLE = hex_to_rgb("#9cdcfe")
CONSTANT = hex_to_rgb("#4fc1ff")
FUNCTION = hex_to_rgb("#dcdcaa")
KEYWORD = hex_to_rgb("#c586c0")

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
u = xx / W
v = yy / H
del xx, yy


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


RAMP = [
    (0.00, SELECTION),
    (0.20, ACCENT),
    (0.40, ACCENT_HOVER),
    (0.58, TYPE),
    (0.74, CONSTANT),
    (0.88, VARIABLE),
    (1.00, FUNCTION),
]


def ramp(t):
    ps = np.array([p for p, _ in RAMP], dtype=np.float64)
    cols = np.array([srgb_to_lin(c) for _, c in RAMP], dtype=np.float64)
    flat = t.ravel()
    out = np.empty((flat.size, 3), dtype=np.float32)
    for k in range(3):
        out[:, k] = np.interp(flat, ps, cols[:, k]).astype(np.float32)
    return out.reshape(t.shape + (3,))


def bump(cx, cy, rx, ry):
    return np.exp(-((((u - cx) / rx) ** 2 + ((v - cy) / ry) ** 2))).astype(np.float32)


def terrain(phase, relief):
    h = np.zeros((H, W), dtype=np.float32)
    for cx, cy, rx, ry, amp in relief:
        h += np.float32(amp) * bump(cx, cy, rx, ry)
    h += 0.26 * np.sin(2 * np.pi * (u * 0.80 + v * 0.52 + phase)).astype(np.float32)
    h += 0.125 * np.sin(2 * np.pi * (u * 1.35 - v * 1.05 + phase * 1.4 + 0.3)).astype(np.float32)
    h += 0.050 * np.sin(2 * np.pi * (u * 2.40 + v * 2.00 + phase * 0.7 + 0.8)).astype(np.float32)
    h += 0.018 * np.sin(2 * np.pi * (u * 4.10 - v * 3.50 + phase * 1.9 + 0.5)).astype(np.float32)

    gy, gx = np.gradient(h)
    sl = np.sqrt(gx * gx + gy * gy)
    del gx, gy
    sl = np.clip(sl / max(sl.max(), 1e-9) * 3.2, 0, 1).astype(np.float32)
    fine = (
        0.020 * np.sin(2 * np.pi * (u * 6.5 - v * 5.1 + phase * 2.3))
        + 0.011 * np.sin(2 * np.pi * (u * 10.3 + v * 8.7 + phase * 1.1 + 0.4))
        + 0.006 * np.sin(2 * np.pi * (u * 17.1 - v * 14.3 + phase * 3.1 + 0.9))
    ).astype(np.float32)
    return h + fine * sl


def notch_calm():
    return np.exp(-((((u - 0.5) / 0.36) ** 2 + (v / 0.26) ** 2) ** 1.4)).astype(np.float32)


def notch_pool():
    d = np.sqrt(((u - 0.5) / 0.165) ** 2 + (v / 0.068) ** 2)
    m = np.clip((2.6 - d) / 1.6, 0, 1)
    return (m * m * (3 - 2 * m)).astype(np.float32)


def render(name, phase, relief):
    h = terrain(phase, relief)
    h -= h.min()
    h /= max(h.max(), 1e-6)

    elev = h.copy()
    h = h * (1.0 - notch_calm())

    f = h * np.float32(LEVELS) + np.float32(0.5)
    gy, gx = np.gradient(f)
    grad = np.sqrt(gx * gx + gy * gy)
    del gx, gy
    np.maximum(grad, np.float32(1e-6), out=grad)

    dist = np.abs(f - np.round(f)) / grad
    idx = np.abs(np.round(f)) % INDEX_EVERY < 0.5
    del f, grad

    half = np.where(idx, np.float32(INDEX_PX), np.float32(LINE_PX)) * 0.5
    t = np.clip((half + 0.8 - dist) / 1.6, 0, 1)
    line = (t * t * (3 - 2 * t)).astype(np.float32)
    line *= np.where(idx, np.float32(1.0), np.float32(0.62))
    del t, half, idx

    haze = np.clip(1.0 - dist / 26.0, 0, 1)
    haze = (haze * haze).astype(np.float32)
    del dist

    col = ramp(elev)

    img = line[..., None] * col * np.float32(0.95)
    img += haze[..., None] * col * np.float32(0.040)
    del line, haze

    img += (elev**2)[..., None] * col * np.float32(0.030)
    del col

    r2 = ((u - 0.5) * 2) ** 2 * 0.85 + ((v - 0.5) * 2) ** 2 * 1.05
    vig = np.clip(1.0 - 0.42 * np.clip(r2 - 0.35, 0, None) ** 1.15, 0, 1).astype(np.float32)
    img *= vig[..., None]
    del r2, vig

    pool = notch_pool()
    img *= (1.0 - pool)[..., None]

    img = 1.0 - np.exp(-img)
    out = lin_to_srgb(np.clip(img, 0, 1)).astype(np.float32)
    del img

    rng = np.random.default_rng(11)
    dither = ((rng.random((H, W, 3), dtype=np.float32) + rng.random((H, W, 3), dtype=np.float32) - 1.0) / 255.0)
    lit = np.clip(out.max(axis=2, keepdims=True) * 30.0, 0, 1)
    out = np.clip(out + dither * lit * (1.0 - pool)[..., None], 0, 1)

    arr = (out * 255.0 + 0.5).astype(np.uint8)
    path = OUT_DIR / name
    Image.fromarray(arr).save(path, optimize=True)
    print("wrote", path)


render(
    "comfydark-horizon.png",
    phase=0.06,
    relief=[
        (0.72, 0.66, 0.30, 0.34, 1.25),
        (0.30, 0.78, 0.26, 0.26, 0.70),
        (0.14, 0.34, 0.24, 0.30, -0.85),
        (0.92, 0.22, 0.22, 0.26, -0.55),
    ],
)
render(
    "comfydark-corner.png",
    phase=0.52,
    relief=[
        (0.20, 0.74, 0.30, 0.30, 1.35),
        (0.86, 0.86, 0.26, 0.24, 0.65),
        (0.62, 0.30, 0.40, 0.36, -0.95),
        (0.98, 0.10, 0.24, 0.22, -0.45),
    ],
)
