# -*- coding: utf-8 -*-
"""Check QC renders: report the model's pixel bbox with noise tolerance.

A row/column counts as content only if it has >= MIN_HITS non-background pixels,
which ignores EEVEE render noise at frame borders.

Usage:
  python3 tools/qc_frame_check.py [dir]
"""
import os
import struct
import sys
import zlib

MIN_HITS = 3
BG = 163
TOL = 12


def read_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    idat = b""
    w = h = None
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", chunk[:10])
        elif typ == b"IDAT":
            idat += chunk
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    stride = w * ch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, out


def content_mask(w, h, ch, px):
    cols = [0] * w
    rows = [0] * h
    for y in range(h):
        row = y * w * ch
        for x in range(w):
            i = row + x * ch
            if abs(px[i] - BG) > TOL or abs(px[i + 1] - BG) > TOL or abs(px[i + 2] - BG) > TOL:
                cols[x] += 1
                rows[y] += 1
    return cols, rows


def main():
    qc = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "qc")
    for f in sorted(os.listdir(qc)):
        if not f.endswith(".png"):
            continue
        w, h, ch, px = read_png(os.path.join(qc, f))
        cols, rows = content_mask(w, h, ch, px)
        xs = [x for x, c in enumerate(cols) if c >= MIN_HITS]
        ys = [y for y, c in enumerate(rows) if c >= MIN_HITS]
        if not xs or not ys:
            print(f"{f}: EMPTY?")
            continue
        minx, maxx = xs[0], xs[-1]
        miny, maxy = ys[0], ys[-1]
        touch = []
        if miny <= 1:
            touch.append("TOP")
        if maxy >= h - 2:
            touch.append("BOTTOM")
        if minx <= 1:
            touch.append("LEFT")
        if maxx >= w - 2:
            touch.append("RIGHT")
        fill = round((maxy - miny) / h * 100)
        print(f"{f}: y=({miny},{maxy}) x=({minx},{maxx}) fillH={fill}% touch={touch or 'none'}")


if __name__ == "__main__":
    main()
