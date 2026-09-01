import math
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

OUT_DIR = Path(__file__).resolve().parent
CACHE = OUT_DIR / ".demcache"
W, H = 5120, 2880

ZOOM = 13
CENTER_LON, CENTER_LAT = 10.705, 59.888
SRC_W, SRC_H = 3716, 2090
TILE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"

INTERVAL = 65.0
INDEX_EVERY = 5
LINE_PX = 2.4
INDEX_PX = 4.8
COAST_PX = 7.5
COAST_GAIN = 0.72
ELEV_TOP = 380.0


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

RAMP = [
    (0.00, SELECTION),
    (0.16, ACCENT),
    (0.36, ACCENT_HOVER),
    (0.56, TYPE),
    (0.74, CONSTANT),
    (0.88, VARIABLE),
    (1.00, FUNCTION),
]


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def ramp(t):
    ps = np.array([p for p, _ in RAMP], dtype=np.float64)
    cols = np.array([srgb_to_lin(c) for _, c in RAMP], dtype=np.float64)
    flat = t.ravel()
    out = np.empty((flat.size, 3), dtype=np.float32)
    for k in range(3):
        out[:, k] = np.interp(flat, ps, cols[:, k]).astype(np.float32)
    return out.reshape(t.shape + (3,))


def lonlat_to_px(lon, lat, z):
    n = 256 * 2**z
    s = math.sin(math.radians(lat))
    return (lon + 180.0) / 360.0 * n, (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n


def fetch_dem():
    CACHE.mkdir(exist_ok=True)
    cx, cy = lonlat_to_px(CENTER_LON, CENTER_LAT, ZOOM)
    x0, y0 = cx - SRC_W / 2, cy - SRC_H / 2
    tx0, ty0 = int(x0 // 256), int(y0 // 256)
    tx1, ty1 = int((x0 + SRC_W) // 256), int((y0 + SRC_H) // 256)

    jobs = [(x, y) for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]

    def grab(t):
        x, y = t
        dst = CACHE / f"{ZOOM}_{x}_{y}.png"
        if dst.exists() and dst.stat().st_size > 500:
            return
        urllib.request.urlretrieve(TILE_URL.format(z=ZOOM, x=x, y=y), dst)

    with ThreadPoolExecutor(12) as ex:
        list(ex.map(grab, jobs))

    mos = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), dtype=np.float32)
    for i, x in enumerate(range(tx0, tx1 + 1)):
        for j, y in enumerate(range(ty0, ty1 + 1)):
            a = np.asarray(Image.open(CACHE / f"{ZOOM}_{x}_{y}.png").convert("RGB")).astype(np.float32)
            mos[j * 256 : (j + 1) * 256, i * 256 : (i + 1) * 256] = (
                a[:, :, 0] * 256.0 + a[:, :, 1] + a[:, :, 2] / 256.0
            ) - 32768.0
    ox, oy = int(round(x0 - tx0 * 256)), int(round(y0 - ty0 * 256))
    return mos[oy : oy + SRC_H, ox : ox + SRC_W].copy()


def box_blur(a, r, passes=1):
    out = a
    for _ in range(passes):
        p = np.pad(out, ((r, r), (0, 0)), mode="edge")
        c = np.cumsum(p, axis=0)
        out = (c[2 * r :] - c[: -2 * r]) / (2 * r)
        p = np.pad(out, ((0, 0), (r, r)), mode="edge")
        c = np.cumsum(p, axis=1)
        out = (c[:, 2 * r :] - c[:, : -2 * r]) / (2 * r)
    return out.astype(np.float32)


def curvature_smooth(m, r, iters):
    out = m
    for _ in range(iters):
        out = box_blur(out, r, 1)
        out = (out > 0.5).astype(np.float32)
    return box_blur(out, max(r // 2, 2), 2)


def crisp_lines(field, half, gate_floor):
    gy, gx = np.gradient(field)
    grad = np.sqrt(gx * gx + gy * gy)
    del gx, gy
    dist = np.abs(field - np.round(field)) / np.maximum(grad, 1e-7)
    gate = np.clip(grad / gate_floor, 0, 1)
    t = np.clip((half + 0.8 - dist) / 1.6, 0, 1)
    return (t * t * (3 - 2 * t) * gate).astype(np.float32), dist


def render(name):
    dem = fetch_dem()
    dem = np.asarray(Image.fromarray(dem).resize((W, H), Image.BICUBIC), dtype=np.float32)

    water = (box_blur(dem, 2, 1) < 0.6).astype(np.float32)
    wsm = curvature_smooth(water, 4, 3)

    land = np.maximum(box_blur(dem, 19, 3), 0.0)
    elev = np.clip(land / ELEV_TOP, 0, 1).astype(np.float32)

    f = land / np.float32(INTERVAL)
    lev = np.round(f)
    is_index = (np.abs(lev) % INDEX_EVERY) < 0.5
    half = np.where(is_index, np.float32(INDEX_PX), np.float32(LINE_PX)) * 0.5
    line, dist = crisp_lines(f, half, np.float32(0.0035))
    line *= np.where(is_index, np.float32(1.0), np.float32(0.60))
    line *= 1.0 - np.clip(wsm * 2.0, 0, 1)
    del f, lev, is_index, half

    haze = np.clip(1.0 - dist / 22.0, 0, 1)
    haze = (haze * haze).astype(np.float32) * (1.0 - np.clip(wsm * 2.0, 0, 1))
    del dist

    coast, _ = crisp_lines(wsm - 0.5, np.float32(COAST_PX * 0.5), np.float32(0.0002))

    col = ramp(elev)
    img = line[..., None] * col * np.float32(0.95)
    img += haze[..., None] * col * np.float32(0.045)
    img += (elev**2)[..., None] * col * np.float32(0.035)
    del line, haze, col

    img += coast[..., None] * srgb_to_lin(VARIABLE)[None, None, :].astype(np.float32) * np.float32(COAST_GAIN)
    img += (wsm * 0.045)[..., None] * srgb_to_lin(SELECTION)[None, None, :].astype(np.float32)
    del coast, wsm

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx / W, yy / H
    del xx, yy

    top = np.clip(v / 0.19, 0, 1)
    img *= (top * top * (3 - 2 * top))[..., None]

    r2 = ((u - 0.5) * 2) ** 2 * 0.85 + ((v - 0.5) * 2) ** 2 * 1.05
    img *= np.clip(1.0 - 0.42 * np.clip(r2 - 0.35, 0, None) ** 1.15, 0, 1)[..., None]
    del r2

    d = np.sqrt(((u - 0.5) / 0.185) ** 2 + (v / 0.080) ** 2)
    m = np.clip((2.6 - d) / 1.6, 0, 1)
    pool = (m * m * (3 - 2 * m)).astype(np.float32)
    img *= (1.0 - pool)[..., None]
    del u, v, d, m

    img = 1.0 - np.exp(-img)
    out = lin_to_srgb(np.clip(img, 0, 1)).astype(np.float32)
    del img

    rng = np.random.default_rng(11)
    dither = (rng.random((H, W, 3), dtype=np.float32) + rng.random((H, W, 3), dtype=np.float32) - 1.0) / 255.0
    lit = np.clip(out.max(axis=2, keepdims=True) * 30.0, 0, 1)
    out = np.clip(out + dither * lit * (1.0 - pool)[..., None], 0, 1)

    Image.fromarray((out * 255.0 + 0.5).astype(np.uint8)).save(OUT_DIR / name, optimize=True)
    print("wrote", OUT_DIR / name)


if __name__ == "__main__":
    render("comfydark-oslo.png")
