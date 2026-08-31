from pathlib import Path

import numpy as np
from PIL import Image

OUT_DIR = Path(__file__).resolve().parent
W, H = 5120, 2880


def hex_to_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i : i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


BG = hex_to_rgb("#161b22")
BG_DEEP = hex_to_rgb("#0d1117")
EDGE = hex_to_rgb("#0d1117") * 0.35
ACCENT = hex_to_rgb("#1f6feb")
ACCENT_HOVER = hex_to_rgb("#388bfd")
SELECTION = hex_to_rgb("#264f78")
TYPE = hex_to_rgb("#4ec9b0")
VARIABLE = hex_to_rgb("#9cdcfe")
CONSTANT = hex_to_rgb("#4fc1ff")
FUNCTION = hex_to_rgb("#dcdcaa")
KEYWORD = hex_to_rgb("#c586c0")

yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
u = xx / W
v = yy / H


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def ribbon(vv, path_v, sigma, color, strength, taper=None, sharp=2):
    fall = np.exp(-(np.abs((vv - path_v) / sigma) ** sharp))
    if taper is not None:
        fall = fall * taper
    return fall[..., None] * srgb_to_lin(color)[None, None, :] * strength


def notch_pool():
    d = np.sqrt(((u - 0.5) / 0.165) ** 2 + (v / 0.068) ** 2)
    m = np.clip((2.6 - d) / (2.6 - 1.0), 0, 1)
    return m * m * (3 - 2 * m)


def render(name, phase):
    t = np.clip(0.2 * u + 0.8 * v, 0, 1)
    base = srgb_to_lin(BG_DEEP)[None, None, :] * (1 - t[..., None]) + srgb_to_lin(BG)[None, None, :] * t[..., None]
    img = base * 0.55

    dip = np.exp(-(((u - 0.46) / 0.30) ** 2))
    sides = np.clip((np.abs(u - 0.5) - 0.14) / 0.24, 0, 1)
    sides = sides * sides * (3 - 2 * sides)

    c1 = 0.045 + 0.27 * dip + 0.072 * np.sin(2 * np.pi * (u * 0.50 + phase))
    taper1 = 1.0 + 0.85 * sides
    img = img + ribbon(v, c1 + 0.02, 0.062, ACCENT, 0.050, taper1, sharp=4)
    img = img + ribbon(v, c1, 0.030, ACCENT, 0.155, taper1, sharp=5)
    img = img + ribbon(v, c1 + 0.035, 0.007, VARIABLE, 0.072, taper1, sharp=4)
    img = img + ribbon(v, c1 - 0.042, 0.006, TYPE, 0.050, taper1, sharp=4)

    c2 = 0.45 + 0.140 * np.sin(2 * np.pi * (u * 0.46 + phase + 0.30))
    sig2 = 0.048 * (1 + 0.18 * np.sin(2 * np.pi * (u * 0.5 + phase + 0.6)))
    img = img + ribbon(v, c2, sig2, SELECTION, 0.310, sharp=5)
    img = img + ribbon(v, c2 - 0.055, 0.009, CONSTANT, 0.070, sharp=4)

    c4 = 0.70 + 0.120 * np.sin(2 * np.pi * (u * 0.44 + phase + 0.55))
    taper4 = 0.78 + 0.22 * np.sin(2 * np.pi * (u * 0.42 + phase + 0.85))
    img = img + ribbon(v, c4, 0.052, SELECTION, 0.195, taper4, sharp=5)
    img = img + ribbon(v, c4, 0.027, ACCENT, 0.140, taper4, sharp=5)
    img = img + ribbon(v, c4 + 0.022, 0.007, TYPE, 0.052, taper4, sharp=4)
    img = img + ribbon(v, c4 - 0.034, 0.005, FUNCTION, 0.040, taper4, sharp=4)

    c3 = 0.93 + 0.105 * np.sin(2 * np.pi * (u * 0.40 + phase + 0.88))
    taper3 = 0.76 + 0.24 * np.sin(2 * np.pi * (u * 0.45 + phase + 0.2))
    img = img + ribbon(v, c3, 0.076, ACCENT, 0.062, taper3, sharp=4)
    img = img + ribbon(v, c3, 0.040, ACCENT, 0.270, taper3, sharp=5)
    img = img + ribbon(v, c3 - 0.05, 0.009, ACCENT_HOVER, 0.125, taper3, sharp=4)
    img = img + ribbon(v, c3 - 0.072, 0.005, KEYWORD, 0.034, taper3, sharp=4)

    s1 = 0.28 + 0.26 * np.sin(2 * np.pi * (u * 0.34 + phase + 0.18))
    img = img + ribbon(v, s1, 0.006, TYPE, 0.046, 0.55 + 0.45 * u, sharp=4)
    s2 = 0.55 + 0.26 * np.sin(2 * np.pi * (u * 0.34 + phase + 0.24))
    img = img + ribbon(v, s2, 0.005, CONSTANT, 0.038, 0.95 - 0.40 * u, sharp=4)
    s3 = 0.80 + 0.26 * np.sin(2 * np.pi * (u * 0.34 + phase + 0.30))
    img = img + ribbon(v, s3, 0.005, VARIABLE, 0.032, 0.60 + 0.40 * u, sharp=4)

    cx_d = (u - 0.5) * 2.0
    cy_d = (v - 0.5) * 2.0
    r2 = cx_d**2 * 0.9 + cy_d**2 * 1.1
    top_relief = np.clip(1 - v / 0.30, 0, 1) * np.clip((np.abs(u - 0.5) - 0.14) / 0.24, 0, 1)
    vig_k = 0.34 * (1 - 0.75 * top_relief)
    vig = 1.0 - vig_k * np.clip(r2 - 0.30, 0, None) ** 1.2
    edge_mix = np.clip((r2 - 0.60) * 0.5, 0, 0.40) * (1 - 0.85 * top_relief)
    img = img * vig[..., None]
    img = img * (1 - edge_mix[..., None]) + srgb_to_lin(EDGE)[None, None, :] * edge_mix[..., None]

    pool = notch_pool()
    img = img * (1 - pool[..., None])

    out = lin_to_srgb(np.clip(img, 0, 1))

    rng = np.random.default_rng(7)
    dither = (rng.random((H, W, 3)) + rng.random((H, W, 3)) - 1.0) / 255.0
    grain = rng.normal(0.0, 0.55 / 255.0, (H, W, 1))
    out = np.clip(out + (dither + grain) * (1 - pool[..., None]), 0, 1)

    arr = (out * 255.0 + 0.5).astype(np.uint8)
    path = OUT_DIR / name
    Image.fromarray(arr).save(path, optimize=True)
    print("wrote", path)


render("comfydark-horizon.png", phase=0.06)
render("comfydark-corner.png", phase=0.52)
