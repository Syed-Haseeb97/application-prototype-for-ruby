"""Generate assets/ruby.ico and assets/ruby.png (plasma-orb style) with Pillow.

Run:  python packaging/make_icon.py
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SIZE = 512
OUT = Path(__file__).resolve().parent.parent / "assets"


def render(size: int = SIZE) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx = cy = size / 2
    radius = size * 0.38
    glow = Image.new("RGBA", (size, size), (139, 92, 246, 0))
    ImageDraw.Draw(glow).ellipse(
        (cx - radius * 1.2, cy - radius * 1.2, cx + radius * 1.2, cy + radius * 1.2),
        fill=(139, 92, 246, 120),
    )
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(size * 0.06)))

    orb = Image.new("RGBA", (size, size), (91, 33, 182, 0))
    px = orb.load()
    inner, outer = (196, 181, 253), (91, 33, 182)
    hx, hy = cx - radius * 0.35, cy - radius * 0.4  # highlight centre
    for y in range(size):
        for x in range(size):
            if math.hypot(x - cx, y - cy) <= radius:
                t = min(1.0, math.hypot(x - hx, y - hy) / (radius * 1.55))
                px[x, y] = tuple(int(inner[i] + (outer[i] - inner[i]) * t) for i in range(3)) + (255,)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    orb.putalpha(mask)
    img.alpha_composite(orb)

    shine = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    ImageDraw.Draw(shine).ellipse(
        (cx - radius * 0.62, cy - radius * 0.72, cx - radius * 0.12, cy - radius * 0.38),
        fill=(255, 255, 255, 150),
    )
    img.alpha_composite(shine.filter(ImageFilter.GaussianBlur(size * 0.012)))
    return img


def main() -> None:
    OUT.mkdir(exist_ok=True)
    img = render()
    img.save(OUT / "ruby.png")
    img.save(OUT / "ruby.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote", OUT / "ruby.ico", OUT / "ruby.png")


if __name__ == "__main__":
    main()
