#!/usr/bin/env python3
"""Generate the Pinkas Android launcher icon using only Python's standard library."""
from pathlib import Path
import struct
import sys
import zlib

NAVY = (23, 30, 42, 255)       # #171E2A
PAPER = (243, 240, 230, 255)   # #F3F0E6
LIME = (215, 243, 106, 255)    # #D7F36A
BLUE = (105, 120, 233, 255)    # #6978E9
SCALE = 3


class Canvas:
    def __init__(self, size, background=(0, 0, 0, 0)):
        self.size = size
        self.pixels = bytearray(background * (size * size))

    def put(self, x, y, color):
        if 0 <= x < self.size and 0 <= y < self.size:
            i = (y * self.size + x) * 4
            self.pixels[i:i + 4] = bytes(color)

    def polygon(self, points, color):
        s = self.size
        pts = [(int(x * s), int(y * s)) for x, y in points]
        min_x = max(0, min(x for x, _ in pts))
        max_x = min(s - 1, max(x for x, _ in pts))
        min_y = max(0, min(y for _, y in pts))
        max_y = min(s - 1, max(y for _, y in pts))
        for y in range(min_y, max_y + 1):
            py = y + 0.5
            for x in range(min_x, max_x + 1):
                px = x + 0.5
                inside = False
                j = len(pts) - 1
                for i, (xi, yi) in enumerate(pts):
                    xj, yj = pts[j]
                    if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / ((yj - yi) or 1e-9) + xi):
                        inside = not inside
                    j = i
                if inside:
                    self.put(x, y, color)

    def line(self, a, b, width, color):
        s = self.size
        ax, ay = a[0] * s, a[1] * s
        bx, by = b[0] * s, b[1] * s
        radius = width * s / 2.0
        min_x = max(0, int(min(ax, bx) - radius - 1))
        max_x = min(s - 1, int(max(ax, bx) + radius + 1))
        min_y = max(0, int(min(ay, by) - radius - 1))
        max_y = min(s - 1, int(max(ay, by) + radius + 1))
        dx, dy = bx - ax, by - ay
        denom = dx * dx + dy * dy
        for y in range(min_y, max_y + 1):
            py = y + 0.5
            for x in range(min_x, max_x + 1):
                px = x + 0.5
                t = 0 if denom == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / denom))
                qx, qy = ax + t * dx, ay + t * dy
                if (px - qx) ** 2 + (py - qy) ** 2 <= radius * radius:
                    self.put(x, y, color)

    def downsample(self, out_size):
        src = self.size
        factor = src // out_size
        out = bytearray(out_size * out_size * 4)
        samples = factor * factor
        for oy in range(out_size):
            for ox in range(out_size):
                sums = [0, 0, 0, 0]
                for sy in range(oy * factor, (oy + 1) * factor):
                    start = (sy * src + ox * factor) * 4
                    for sx in range(factor):
                        p = start + sx * 4
                        for c in range(4):
                            sums[c] += self.pixels[p + c]
                q = (oy * out_size + ox) * 4
                out[q:q + 4] = bytes(int(v / samples + 0.5) for v in sums)
        return out


def make_icon(size, background):
    c = Canvas(size * SCALE, background)
    # A paper page with a folded lime corner and tidy ledger lines.
    c.polygon([(0.27, 0.17), (0.59, 0.17), (0.73, 0.31),
               (0.73, 0.80), (0.27, 0.80)], PAPER)
    c.polygon([(0.59, 0.17), (0.59, 0.31), (0.73, 0.31)], LIME)
    c.line((0.59, 0.17), (0.59, 0.31), 0.012, NAVY)
    c.line((0.36, 0.39), (0.60, 0.39), 0.016, BLUE)
    c.line((0.36, 0.46), (0.60, 0.46), 0.016, BLUE)
    c.line((0.36, 0.53), (0.50, 0.53), 0.016, BLUE)
    # A clear lime checkmark, the key identifying element of the selected icon.
    c.line((0.36, 0.62), (0.46, 0.70), 0.045, LIME)
    c.line((0.46, 0.70), (0.64, 0.51), 0.045, LIME)
    return c.downsample(size)


def write_png(path, size, rgba):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = bytearray()
    stride = size * 4
    for y in range(size):
        raw.append(0)  # PNG filter: none
        raw.extend(rgba[y * stride:(y + 1) * stride])
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    path.write_bytes(png)


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "android/app/src/main/res")
    densities = [("mdpi", 48, 108), ("hdpi", 72, 162), ("xhdpi", 96, 216),
                 ("xxhdpi", 144, 324), ("xxxhdpi", 192, 432)]
    for density, legacy_size, foreground_size in densities:
        folder = root / ("mipmap-" + density)
        legacy = make_icon(legacy_size, NAVY)
        foreground = make_icon(foreground_size, (0, 0, 0, 0))
        write_png(folder / "ic_launcher.png", legacy_size, legacy)
        write_png(folder / "ic_launcher_round.png", legacy_size, legacy)
        write_png(folder / "ic_launcher_foreground.png", foreground_size, foreground)

    (root / "values").mkdir(parents=True, exist_ok=True)
    (root / "values" / "pinkas_launcher_colors.xml").write_text(
        '<resources><color name="pinkas_launcher_background">#171E2A</color></resources>\n',
        encoding="utf-8")
    (root / "mipmap-anydpi-v26").mkdir(parents=True, exist_ok=True)
    adaptive = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/pinkas_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
'''
    (root / "mipmap-anydpi-v26" / "ic_launcher.xml").write_text(adaptive, encoding="utf-8")
    (root / "mipmap-anydpi-v26" / "ic_launcher_round.xml").write_text(adaptive, encoding="utf-8")
    print("Generated Pinkas launcher icons in", root)


if __name__ == "__main__":
    main()
