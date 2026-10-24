"""Generate self-hosted banner / avatar / favicon assets for the blog.

Run:  python tools/gen-assets.py
Outputs are written into source/img/.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source" / "img"
OUT.mkdir(parents=True, exist_ok=True)


def gradient(w: int, h: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> np.ndarray:
    t = np.linspace(0.0, 1.0, h)[:, None]
    top_a = np.array(top, dtype=np.float64)
    bottom_a = np.array(bottom, dtype=np.float64)
    rows = top_a + (bottom_a - top_a) * t  # (h, 3)
    return np.repeat(rows[:, None, :], w, axis=1)  # (h, w, 3)


def add_blob(
    canvas: np.ndarray,
    cx: float,
    cy: float,
    radius: float,
    color: tuple[int, int, int],
    strength: float,
) -> None:
    """Add a soft radial glow, composited additively."""
    h, w, _ = canvas.shape
    ys, xs = np.mgrid[0:h, 0:w]
    dist2 = (xs - cx) ** 2 + (ys - cy) ** 2
    falloff = np.exp(-dist2 / (2.0 * radius**2)) * strength
    tint = np.array(color, dtype=np.float64)
    # additive glow that fades toward the edges
    canvas[:] = canvas + falloff[:, :, None] * tint


def build_banner() -> Path:
    w, h = 1920, 1080
    canvas = gradient(w, h, (11, 16, 38), (42, 27, 77))

    add_blob(canvas, w * 0.18, h * 0.22, 520, (34, 211, 238), 0.42)
    add_blob(canvas, w * 0.82, h * 0.30, 620, (139, 92, 246), 0.50)
    add_blob(canvas, w * 0.55, h * 0.92, 700, (244, 114, 182), 0.30)
    add_blob(canvas, w * 0.05, h * 0.95, 480, (56, 189, 248), 0.22)

    # vignette keeps the edges calm behind the navigation bar
    hh, ww, _ = canvas.shape
    ys, xs = np.mgrid[0:hh, 0:ww]
    nx = (xs - ww / 2) / (ww / 2)
    ny = (ys - hh / 2) / (hh / 2)
    vignette = 1.0 - 0.35 * np.clip(nx**2 + ny**2, 0, 1.6) ** 1.1
    canvas *= vignette[:, :, None]

    # gentle dithering avoids visible banding on 8-bit gradients
    canvas += np.random.default_rng(7).normal(0, 1.6, canvas.shape)

    img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), "RGB")
    img = img.filter(ImageFilter.GaussianBlur(4))

    path = OUT / "banner.png"
    img.save(path, optimize=True)
    return path


def build_avatar() -> Path:
    size = 512
    canvas = gradient(size, size, (79, 70, 229), (14, 165, 233))
    add_blob(canvas, size * 0.22, size * 0.18, 200, (255, 255, 255), 0.28)
    add_blob(canvas, size * 0.85, size * 0.88, 220, (236, 72, 153), 0.35)
    canvas += np.random.default_rng(3).normal(0, 1.2, canvas.shape)

    img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)

    draw = ImageDraw.Draw(img)
    font = _load_font(int(size * 0.52))
    text = "T"
    box = draw.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    draw.text(
        ((size - tw) / 2 - box[0], (size - th) / 2 - box[1] - size * 0.02),
        text,
        font=font,
        fill=(255, 255, 255, 235),
    )

    img.putalpha(mask)

    path = OUT / "avatar.png"
    img.save(path, optimize=True)
    return path


def build_og() -> Path:
    """1200x630 social preview card with the site name."""
    w, h = 1200, 630
    canvas = gradient(w, h, (11, 16, 38), (42, 27, 77))
    add_blob(canvas, w * 0.15, h * 0.2, 340, (34, 211, 238), 0.40)
    add_blob(canvas, w * 0.85, h * 0.3, 400, (139, 92, 246), 0.48)
    add_blob(canvas, w * 0.5, h * 1.0, 420, (244, 114, 182), 0.26)
    canvas += np.random.default_rng(11).normal(0, 1.4, canvas.shape)

    img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), "RGB")
    img = img.filter(ImageFilter.GaussianBlur(3))
    draw = ImageDraw.Draw(img)

    title_font = _load_font(96)
    sub_font = _load_font(40)

    title = "Tatalvpai"
    box = draw.textbbox((0, 0), title, font=title_font)
    draw.text(
        ((w - (box[2] - box[0])) / 2 - box[0], h / 2 - 96),
        title,
        font=title_font,
        fill=(255, 255, 255),
    )

    sub = "记录技术与生活"
    box = draw.textbbox((0, 0), sub, font=sub_font)
    draw.text(
        ((w - (box[2] - box[0])) / 2 - box[0], h / 2 + 40),
        sub,
        font=sub_font,
        fill=(226, 232, 240),
    )

    path = OUT / "og.png"
    img.save(path, optimize=True)
    return path


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#4f46e5"/>
      <stop offset="1" stop-color="#0ea5e9"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="14" fill="url(#g)"/>
  <text x="32" y="46" font-family="Segoe UI, Arial, sans-serif" font-size="40"
        font-weight="700" fill="#ffffff" text-anchor="middle">T</text>
</svg>
"""


def main() -> None:
    for builder in (build_banner, build_avatar, build_og):
        path = builder()
        print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.1f} KiB")

    favicon = OUT / "favicon.svg"
    favicon.write_text(FAVICON, encoding="utf-8")
    print(f"{favicon.relative_to(ROOT)}  {favicon.stat().st_size / 1024:.1f} KiB")


if __name__ == "__main__":
    main()
