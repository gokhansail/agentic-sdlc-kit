"""Draw the plugin icon: a 1024 x 1024 PNG with a lead circle linked to three agent circles.

Teal background, white shapes, anti-aliased by distance-based coverage. Needs no packages.
Usage: python tools/make_icon.py <out.png>
"""
import math
import struct
import sys
import zlib

N = 1024
BG = (0x0F, 0x6E, 0x56)
LEAD = (512, 300, 120)
AGENTS = [(232, 740, 85), (512, 740, 85), (792, 740, 85)]
LINE_HALF_WIDTH = 14


def _put(cov: bytearray, x: int, y: int, d: float) -> None:
    c = 0.5 - d
    if c <= 0:
        return
    v = 255 if c >= 1 else int(c * 255 + 0.5)
    i = y * N + x
    if v > cov[i]:
        cov[i] = v


def _circle(cov: bytearray, cx: float, cy: float, r: float) -> None:
    for y in range(max(0, int(cy - r - 2)), min(N, int(cy + r + 3))):
        for x in range(max(0, int(cx - r - 2)), min(N, int(cx + r + 3))):
            _put(cov, x, y, math.hypot(x + 0.5 - cx, y + 0.5 - cy) - r)


def _line(cov: bytearray, x0: float, y0: float, x1: float, y1: float, hw: float) -> None:
    dx, dy = x1 - x0, y1 - y0
    ll = dx * dx + dy * dy
    for y in range(max(0, int(min(y0, y1) - hw - 2)), min(N, int(max(y0, y1) + hw + 3))):
        for x in range(max(0, int(min(x0, x1) - hw - 2)), min(N, int(max(x0, x1) + hw + 3))):
            px, py = x + 0.5 - x0, y + 0.5 - y0
            t = max(0.0, min(1.0, (px * dx + py * dy) / ll))
            _put(cov, x, y, math.hypot(px - t * dx, py - t * dy) - hw)


def _chunk(tag: bytes, data: bytes) -> bytes:
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def render() -> bytes:
    cov = bytearray(N * N)
    for ax, ay, ar in AGENTS:
        _line(cov, LEAD[0], LEAD[1], ax, ay, LINE_HALF_WIDTH)
    _circle(cov, *LEAD)
    for a in AGENTS:
        _circle(cov, *a)
    rows = bytearray()
    for y in range(N):
        rows.append(0)
        for x in range(N):
            c = cov[y * N + x] / 255.0
            rows += bytes(int(b + (255 - b) * c + 0.5) for b in BG)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", struct.pack(">IIBBBBB", N, N, 8, 2, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(bytes(rows), 9))
            + _chunk(b"IEND", b""))


def main(argv: list) -> int:
    if len(argv) != 2:
        print("usage: python tools/make_icon.py <out.png>", file=sys.stderr)
        return 2
    data = render()
    with open(argv[1], "wb") as f:
        f.write(data)
    print(f"{argv[1]}: {len(data)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
