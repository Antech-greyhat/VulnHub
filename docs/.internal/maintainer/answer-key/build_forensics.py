#!/usr/bin/env python3
"""Build the Mfano forensics evidence pack (answer-key tool: never commit to main).

Standard library only, fully deterministic: running it twice gives
byte-identical files. Usage: python build_forensics.py <output_dir>
"""
import io
import math
import random
import struct
import sys
import wave
import zipfile
import zlib
from pathlib import Path

FLAGS = {
    "F-01": "MFANO{m3t4d4t4_t3lls_th3_st0ry}",
    "F-02": "MFANO{b1nw4lk_c4rv3d_th3_z1p}",
    "F-03": "MFANO{l34st_s1gn1f1c4nt_s3cr3ts}",
    "F-04": "MFANO{0n3_fr4m3_t00_f4st}",
    "F-05": "MFANO{m0rs3_c0d3_n3v3r_d13s}",
    "F-06": "MFANO{l00k_4t_th3_sp3ctr0gr4m}",
    "F-07": "MFANO{fr4m3_by_fr4m3_cctv}",
}

# ---------------------------------------------------------------- 5x7 font
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "10001", "11001", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "{": ["00011", "00100", "00100", "01000", "00100", "00100", "00011"],
    "}": ["11000", "00100", "00100", "00010", "00100", "00100", "11000"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "/": ["00001", "00001", "00010", "00100", "01000", "10000", "10000"],
    " ": ["00000"] * 7,
}


def text_mask(text, scale=1):
    """Return (width, height, set_of_lit_(x,y)) for text in the 5x7 font."""
    text = text.upper()
    lit = set()
    for i, ch in enumerate(text):
        glyph = FONT[ch]
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    for sy in range(scale):
                        for sx in range(scale):
                            lit.add(((i * 6 + gx) * scale + sx, gy * scale + sy))
    return len(text) * 6 * scale - scale, 7 * scale, lit


def draw_text(img, text, x0, y0, colour, scale=1):
    _, _, lit = text_mask(text, scale)
    h = len(img)
    w = len(img[0])
    for x, y in lit:
        if 0 <= x0 + x < w and 0 <= y0 + y < h:
            img[y0 + y][x0 + x] = colour


def rect(img, x0, y0, x1, y1, colour):
    for y in range(max(0, y0), min(len(img), y1)):
        row = img[y]
        for x in range(max(0, x0), min(len(row), x1)):
            row[x] = colour


# ---------------------------------------------------------------- PNG
def png_chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def png_bytes(img, text_chunks=()):
    """img: rows of (r,g,b) tuples -> 8-bit RGB PNG bytes."""
    h, w = len(img), len(img[0])
    raw = bytearray()
    for row in img:
        raw.append(0)
        for r, g, b in row:
            raw += bytes((r, g, b))
    out = b"\x89PNG\r\n\x1a\n"
    out += png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    for key, value in text_chunks:
        out += png_chunk(b"tEXt", key.encode("latin-1") + b"\x00" + value.encode("latin-1"))
    out += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += png_chunk(b"IEND", b"")
    return out


def canvas(w, h, colour):
    return [[colour] * w for _ in range(h)]


def noisy_photo(w, h, seed):
    """A soft gradient 'photo' with noise, so LSB changes are invisible."""
    rnd = random.Random(seed)
    img = []
    for y in range(h):
        row = []
        for x in range(w):
            r = int(70 + 110 * x / w + rnd.randint(-12, 12))
            g = int(120 + 60 * math.sin(y / 17.0) + rnd.randint(-12, 12))
            b = int(150 + 80 * y / h + rnd.randint(-12, 12))
            row.append(tuple(max(0, min(255, v)) for v in (r, g, b)))
        img.append(row)
    return img


def build_f01(out):
    img = canvas(320, 160, (233, 225, 200))
    rect(img, 0, 0, 320, 28, (20, 90, 50))
    draw_text(img, "MFANO HIGH SCHOOL", 60, 7, (255, 255, 255), 2)
    draw_text(img, "NOTICE TO ALL FORM 4 STUDENTS", 74, 50, (30, 30, 30))
    draw_text(img, "MOCK EXAMS START MONDAY 08:00", 74, 70, (30, 30, 30))
    draw_text(img, "NO PHONES IN THE EXAM ROOM", 82, 90, (150, 20, 20))
    draw_text(img, "- THE PRINCIPAL", 180, 130, (30, 30, 30))
    chunks = [
        ("Title", "Form 4 mock exam notice"),
        ("Author", "deputy.principal@mfano.school"),
        ("Software", "MfanoNoticeMaker 1.2"),
        ("Comment", "Draft approved. Ref: " + FLAGS["F-01"]),
    ]
    (out / "01_noticeboard.png").write_bytes(png_bytes(img, chunks))


def build_f02(out):
    img = noisy_photo(240, 160, 202)
    rect(img, 20, 110, 220, 150, (40, 40, 40))
    draw_text(img, "STAFF PHOTO 2026", 72, 126, (240, 240, 240))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        info = zipfile.ZipInfo("leaked/kcse_mock_chemistry_p1.txt", date_time=(2026, 3, 14, 2, 13, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(
            info,
            "MFANO HIGH SCHOOL - FORM 4 MOCK CHEMISTRY PAPER 1 (CONFIDENTIAL)\n"
            "Q1. State two properties of noble gases. (2 marks)\n"
            "...\n"
            "Whoever hid this paper inside a photo left their mark:\n"
            + FLAGS["F-02"] + "\n",
        )
    (out / "02_staff_photo.png").write_bytes(png_bytes(img) + buf.getvalue())


def build_f03(out):
    img = noisy_photo(256, 192, 303)
    rect(img, 0, 160, 256, 192, (25, 25, 60))
    draw_text(img, "PRIZE GIVING DAY", 80, 172, (250, 210, 60))
    # Message: flag + NUL, bits MSB-first, spread over R,G,B LSBs row by row.
    message = FLAGS["F-03"].encode() + b"\x00"
    bits = [(byte >> (7 - i)) & 1 for byte in message for i in range(8)]
    k = 0
    for y in range(len(img)):
        for x in range(len(img[0])):
            if k >= len(bits):
                break
            px = list(img[y][x])
            for c in range(3):
                if k < len(bits):
                    px[c] = (px[c] & 0xFE) | bits[k]
                    k += 1
            img[y][x] = tuple(px)
    (out / "03_prize_giving.png").write_bytes(png_bytes(img, [("Comment", "Congratulations to all winners!")]))


# ---------------------------------------------------------------- GIF
def lzw_encode(indices, min_code_size):
    clear = 1 << min_code_size
    eoi = clear + 1
    out_bits = 0
    nbits = 0
    out = bytearray()

    def emit(code, size):
        nonlocal out_bits, nbits
        out_bits |= code << nbits
        nbits += size
        while nbits >= 8:
            out.append(out_bits & 0xFF)
            out_bits >>= 8
            nbits -= 8

    def reset():
        return {(i,): i for i in range(clear)}, eoi + 1, min_code_size + 1

    table, next_code, size = reset()
    emit(clear, size)
    current = ()
    for idx in indices:
        candidate = current + (idx,)
        if candidate in table:
            current = candidate
            continue
        emit(table[current], size)
        if next_code < 4096:
            table[candidate] = next_code
            next_code += 1
            if next_code - 1 == (1 << size) and size < 12:
                size += 1
        else:
            emit(clear, size)
            table, next_code, size = reset()
        current = (idx,)
    if current:
        emit(table[current], size)
    emit(eoi, size)
    if nbits:
        out.append(out_bits & 0xFF)
    return bytes(out)


def gif_bytes(frames, palette, delays, comment=None):
    """frames: list of rows of palette indices (all same size)."""
    h, w = len(frames[0]), len(frames[0][0])
    pal = list(palette) + [(0, 0, 0)] * (256 - len(palette))
    out = bytearray(b"GIF89a")
    out += struct.pack("<HHBBB", w, h, 0xF7, 0, 0)  # global table, 256 colours
    for r, g, b in pal:
        out += bytes((r, g, b))
    out += b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00"  # loop forever
    if comment:
        data = comment.encode("latin-1")
        out += b"\x21\xfe"
        for i in range(0, len(data), 255):
            part = data[i:i + 255]
            out += bytes((len(part),)) + part
        out += b"\x00"
    for frame, delay in zip(frames, delays):
        out += b"\x21\xf9\x04\x04" + struct.pack("<H", delay) + b"\x00\x00"
        out += b"\x2c" + struct.pack("<HHHHB", 0, 0, w, h, 0)
        out += b"\x08"
        data = lzw_encode([i for row in frame for i in row], 8)
        for i in range(0, len(data), 255):
            part = data[i:i + 255]
            out += bytes((len(part),)) + part
        out += b"\x00"
    out += b"\x3b"
    return bytes(out)


def build_f04(out):
    palette = [(245, 240, 225), (40, 40, 40), (200, 160, 30), (150, 20, 20), (20, 90, 50), (255, 255, 255)]
    w, h = 200, 80
    frames, delays = [], []
    for i in range(24):
        img = canvas(w, h, 0)
        rect(img, 0, 0, w, 14, 4)
        draw_text(img, "MFANO SCHOOL BELL", 50, 4, 5)
        # A swinging bell: body shifts left/right.
        swing = int(round(10 * math.sin(i * math.pi / 6)))
        cx = 100 + swing
        for y in range(24, 56):
            half = 6 + (y - 24) // 2
            rect(img, cx - half, y, cx + half, y + 1, 2)
        rect(img, cx - 3, 56, cx + 3, 62, 1)  # clapper
        draw_text(img, "RING" if i % 6 < 3 else "    ", 12, 36, 3)
        draw_text(img, "RING" if i % 6 < 3 else "    ", 165, 36, 3)
        frames.append(img)
        delays.append(12)
    secret = canvas(w, h, 0)
    rect(secret, 0, 0, w, 14, 4)
    draw_text(secret, "MFANO SCHOOL BELL", 50, 4, 5)
    draw_text(secret, FLAGS["F-04"], 22, 38, 3)
    frames.insert(17, secret)
    delays.insert(17, 1)  # 10 ms: too fast for the eye
    (out / "04_school_bell.gif").write_bytes(
        gif_bytes(frames, palette, delays, comment="Bell animation for the school website. Nothing to see here.")
    )


# ---------------------------------------------------------------- WAV
MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....",
    "I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.",
    "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
}


def write_wav(path, samples, rate):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"".join(struct.pack("<h", max(-32767, min(32767, int(s)))) for s in samples))


def build_f05(out):
    rate, freq, unit = 8000, 700, 0.08  # 15 WPM-ish
    inner = FLAGS["F-05"][len("MFANO{"):-1]
    words = inner.upper().split("_")
    samples = []

    def tone(units):
        n = int(rate * unit * units)
        ramp = int(rate * 0.004)
        for i in range(n):
            env = min(1.0, i / ramp, (n - i) / ramp)
            samples.append(14000 * env * math.sin(2 * math.pi * freq * i / rate))

    def gap(units):
        samples.extend([0.0] * int(rate * unit * units))

    gap(10)
    for wi, word in enumerate(words):
        for li, letter in enumerate(word):
            for si, sym in enumerate(MORSE[letter]):
                tone(1 if sym == "." else 3)
                if si < len(MORSE[letter]) - 1:
                    gap(1)
            if li < len(word) - 1:
                gap(3)
        if wi < len(words) - 1:
            gap(7)
    gap(10)
    rnd = random.Random(505)
    samples = [s + rnd.gauss(0, 600) for s in samples]  # radio hiss
    write_wav(out / "05_radio_call.wav", samples, rate)


def build_f06(out):
    rate = 22050
    w, h, lit = text_mask(FLAGS["F-06"], 2)
    col_seconds = 0.035
    f_low, f_high = 3000.0, 9000.0
    # Each pixel row is a band of several close tones so letters look solid.
    sub = 5
    tones = h * sub
    all_freqs = [f_high - (f_high - f_low) * t / (tones - 1) for t in range(tones)]
    freqs = [all_freqs[r * sub:(r + 1) * sub] for r in range(h)]
    col_len = int(rate * col_seconds)
    rnd = random.Random(606)
    phases = [[rnd.random() * 2 * math.pi for _ in range(sub)] for _ in range(h)]
    lead = int(rate * 1.0)
    total = lead * 2 + col_len * w
    samples = [0.0] * total
    # Background: a dull "assembly hall" hum and murmur so it sounds like a bad recording.
    for i in range(total):
        t = i / rate
        samples[i] = 2500 * math.sin(2 * math.pi * 110 * t) + 1500 * math.sin(2 * math.pi * 220 * t) + rnd.gauss(0, 900)
    by_col = {}
    for x, y in lit:
        by_col.setdefault(x, []).append(y)
    for x, ys in by_col.items():
        start = lead + x * col_len
        for y in ys:
            for f, ph in zip(freqs[y], phases[y]):
                step = 2 * math.pi * f / rate
                for i in range(col_len):
                    n = start + i
                    samples[n] += 700 * math.sin(step * n + ph)
    peak = max(abs(s) for s in samples)
    scale = 30000 / peak
    write_wav(out / "06_assembly_recording.wav", [s * scale for s in samples], rate)


# ---------------------------------------------------------------- AVI
def riff_chunk(fourcc, data):
    pad = b"\x00" if len(data) % 2 else b""
    return fourcc + struct.pack("<I", len(data)) + data + pad


def riff_list(kind, payload):
    return b"LIST" + struct.pack("<I", len(payload) + 4) + kind + payload


def avi_bytes(frames, palette, fps, info):
    """Uncompressed 8-bit palettised AVI (BI_RGB). frames: rows of indices."""
    h, w = len(frames[0]), len(frames[0][0])
    stride = (w + 3) & ~3
    frame_size = stride * h
    pal = list(palette) + [(0, 0, 0)] * (256 - len(palette))
    usec = int(1_000_000 / fps)
    avih = struct.pack(
        "<IIIIIIIIII4I", usec, frame_size * fps, 0, 0x10, len(frames), 0, 1, frame_size, w, h, 0, 0, 0, 0
    )
    strh = b"vids" + b"DIB " + struct.pack(
        "<IHHIIIIIIIIhhhh", 0, 0, 0, 0, 1, fps, 0, len(frames), frame_size, 0xFFFFFFFF, 0, 0, 0, w, h
    )
    bih = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 8, 0, frame_size, 2835, 2835, 256, 256)
    bih += b"".join(bytes((b, g, r, 0)) for r, g, b in pal)
    hdrl = riff_list(b"hdrl", riff_chunk(b"avih", avih) + riff_list(b"strl", riff_chunk(b"strh", strh) + riff_chunk(b"strf", bih)))
    info_payload = b"".join(riff_chunk(k, v.encode("latin-1") + b"\x00") for k, v in info)
    info_list = riff_list(b"INFO", info_payload)
    movi_payload = bytearray()
    index = bytearray()
    for frame in frames:
        data = bytearray()
        for row in reversed(frame):  # bottom-up DIB
            data += bytes(row) + b"\x00" * (stride - w)
        offset = len(movi_payload) + 4  # relative to the 'movi' fourcc
        movi_payload += riff_chunk(b"00db", bytes(data))
        index += b"00db" + struct.pack("<III", 0x10, offset, len(data))
    movi = riff_list(b"movi", bytes(movi_payload))
    body = b"AVI " + hdrl + info_list + movi + riff_chunk(b"idx1", bytes(index))
    return b"RIFF" + struct.pack("<I", len(body)) + body


def build_f07(out):
    palette = [
        (18, 18, 18), (70, 70, 70), (110, 110, 105), (150, 150, 140), (200, 200, 190),
        (235, 235, 235), (40, 120, 60), (180, 30, 30), (230, 230, 120), (60, 60, 90),
    ]
    w, h, fps, count, secret_at = 192, 112, 10, 60, 41
    frames = []
    for i in range(count):
        img = canvas(w, h, 2)
        rect(img, 0, 70, w, h, 1)  # floor
        for x in range(0, w, 24):  # floor tiles
            rect(img, x, 70, x + 1, h, 0)
        rect(img, 120, 22, 180, 58, 5)  # whiteboard on the wall
        rect(img, 120, 22, 180, 23, 3)
        rect(img, 20, 20, 48, 70, 9)  # classroom door
        # Person walking left to right.
        px = -20 + i * 4
        rect(img, px + 4, 30, px + 12, 38, 8)  # head
        rect(img, px + 2, 38, px + 14, 60, 6)  # uniform
        leg = 2 if (i // 2) % 2 else 0
        rect(img, px + 3 + leg, 60, px + 7 + leg, 74, 0)
        rect(img, px + 9 - leg, 60, px + 13 - leg, 74, 0)
        rect(img, 0, 0, w, 10, 0)
        secs = i // fps
        draw_text(img, f"CAM-02 2026-03-14 02:13:{secs:02d}", 2, 2, 5)
        draw_text(img, "REC", 170, 100, 7)
        if i == secret_at:
            rect(img, 4, 78, 188, 96, 5)
            draw_text(img, FLAGS["F-07"], 8, 84, 7)
        frames.append(img)
    info = [
        (b"INAM", "Corridor B CCTV export"),
        (b"ICMT", "Exported for the discipline office. Review every frame."),
        (b"ISFT", "MfanoCCTV 0.9"),
    ]
    (out / "07_corridor_cctv.avi").write_bytes(avi_bytes(frames, palette, fps, info))


def main(argv):
    out = Path(argv[1] if len(argv) > 1 else "forensics/evidence")
    out.mkdir(parents=True, exist_ok=True)
    for build in (build_f01, build_f02, build_f03, build_f04, build_f05, build_f06, build_f07):
        build(out)
    for path in sorted(out.iterdir()):
        print(f"{path.name:28} {path.stat().st_size:>9} bytes")


if __name__ == "__main__":
    main(sys.argv)
