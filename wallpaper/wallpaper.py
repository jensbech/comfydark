from pathlib import Path

import numpy as np
from PIL import Image

OUT_DIR = Path(__file__).resolve().parent
W, H = 5120, 2880


def hex_to_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i : i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


BG = hex_to_rgb("#0d1117")
BG_DEEP = hex_to_rgb("#0a0e14")
EDGE = hex_to_rgb("#010409")
ACCENT = hex_to_rgb("#1f6feb")
ACCENT_HOVER = hex_to_rgb("#388bfd")
SELECTION = hex_to_rgb("#264f78")
CYAN = hex_to_rgb("#4ec9b0")

yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
u = xx / W
v = yy / H


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def ribbon(path_v, sigma, color, strength, taper=None):
    fall = np.exp(-(((v - path_v) / sigma) ** 2))
    if taper is not None:
        fall = fall * taper
    return fall[..., None] * srgb_to_lin(color)[None, None, :] * strength


def notch_pool():
    d = np.sqrt(((u - 0.5) / 0.16) ** 2 + (v / 0.06) ** 2)
    m = np.clip((2.6 - d) / (2.6 - 1.0), 0, 1)
    return m * m * (3 - 2 * m)


def render(name, phase):
    t = np.clip(0.2 * u + 0.8 * v, 0, 1)
    base = srgb_to_lin(BG_DEEP)[None, None, :] * (1 - t[..., None]) + srgb_to_lin(BG)[None, None, :] * t[..., None]
    img = base * 0.62

    dip = np.exp(-(((u - 0.46) / 0.27) ** 2))
    wave = np.sin(2 * np.pi * (u * 1.15 + phase))

    c1 = 0.015 + 0.31 * dip + 0.025 * wave
    sides = np.clip((np.abs(u - 0.5) - 0.14) / 0.24, 0, 1)
    sides = sides * sides * (3 - 2 * sides)
    taper1 = 1.0 + 1.0 * sides
    img = img + ribbon(c1 + 0.02, 0.19, ACCENT, 0.016, taper1)
    img = img + ribbon(c1, 0.085, ACCENT, 0.030, taper1)
    img = img + ribbon(c1 + 0.035, 0.030, ACCENT_HOVER, 0.016, taper1)

    c2 = 0.52 + 0.11 * np.sin(2 * np.pi * (u * 0.7 + phase + 0.35))
    sig2 = 0.13 * (1 + 0.25 * np.sin(2 * np.pi * (u * 0.9 + phase + 0.6)))
    img = img + ribbon(c2, sig2, SELECTION, 0.070)
    img = img + ribbon(c2 - 0.055, 0.035, ACCENT_HOVER, 0.012)

    c3 = 0.88 + 0.07 * np.sin(2 * np.pi * (u * 0.55 + phase + 0.7))
    taper3 = 0.55 + 0.45 * np.sin(2 * np.pi * (u * 0.5 + phase + 0.2))
    img = img + ribbon(c3, 0.24, ACCENT, 0.020, taper3)
    img = img + ribbon(c3, 0.12, ACCENT, 0.058, taper3)
    img = img + ribbon(c3 - 0.05, 0.030, ACCENT_HOVER, 0.018, taper3)

    taper4 = np.exp(-(((u - (0.18 + 0.5 * phase)) / 0.30) ** 2))
    img = img + ribbon(c1 - 0.045, 0.018, CYAN, 0.016, taper4)

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
