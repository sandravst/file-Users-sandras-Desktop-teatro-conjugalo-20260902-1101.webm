#!/usr/bin/env python3
"""Assemble "The Origin of the Alebrijes" (approx. 5 min, 1080p) from the
narration clips, illustrations and music in assets/.

    python3 build.py            # writes alebrijes_origin.mp4 + .srt

Inputs
  assets/audio/<scene>.mp3   narration, one clip per scene (see SCENES)
  assets/img/<name>.png      16:9 illustrations
  assets/music.mp3           instrumental bed (ducked under narration)
"""
import json
import math
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
A = ROOT / "assets"
B = ROOT / "build"
B.mkdir(exist_ok=True)
W, H, FPS = 1920, 1080, 30
XF = 0.6          # crossfade between segments (s)
LEAD, TAIL = 0.5, 0.7   # silence before / after each narration clip

F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
F_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"

MAGENTA, TURQ, ORANGE, LIME, COBALT, YELLOW = (
    (230, 0, 126), (0, 178, 169), (255, 140, 0), (124, 200, 40), (40, 80, 200), (255, 214, 10))
PALETTE = [MAGENTA, TURQ, ORANGE, COBALT, LIME]
INK = (30, 20, 50)

SCRIPT = {s["id"]: s for s in json.load(open(ROOT / "scenes.json"))}

# (scene id, [images], move per image, fact sticker)
SCENES = [
    ("01_hook", ["01_hook"], ["in"], None),
    ("02_what", ["02_what"], ["lr"], "ALEBRIJE = real animals, mixed up!"),
    ("03_pedro", ["03_pedro"], ["in"], "Cartonero = paper & cardboard artist"),
    ("04_sick", ["04_sick"], ["out"], None),
    ("05_dream", ["05_dream_a", "05_dream_b"], ["rl", "in"], None),
    ("06_wake", ["06_wake"], ["lr"], "FUN FACT: \"alebrije\" was a brand-new word!"),
    ("07_fans", ["07_fans"], ["in"], None),
    ("08_oaxaca", ["08_oaxaca"], ["rl"], "Oaxaca = a state in southern Mexico"),
    ("09_wood", ["09_wood_a", "09_wood_b"], ["in", "lr"], "Copal: a soft, fragrant wood"),
    ("10_parade", ["10_parade"], ["out"], "Giant alebrije parade: every year since 2007"),
    ("11_coco", ["11_coco"], ["in"], "Movie idea, not ancient legend"),
]


def font(path, size):
    return ImageFont.truetype(path, size)


def dur(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(out)


def run(cmd):
    print(" ".join(str(c) for c in cmd)[:240], "...")
    subprocess.run([str(c) for c in cmd], check=True)


def rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)


def shadow_text(draw, xy, text, fnt, fill, offset=4, shadow=(0, 0, 0, 160), anchor="la"):
    x, y = xy
    draw.text((x + offset, y + offset), text, font=fnt, fill=shadow, anchor=anchor)
    draw.text((x, y), text, font=fnt, fill=fill, anchor=anchor)


# --------------------------------------------------------------- overlays
def overlay_chip(name, title, color, fact=None):
    """Transparent PNG with the scene title chip (bottom-left) and an optional
    fact sticker (top-right)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if title:
        f = font(F_BLACK, 56)
        tw = d.textlength(title, font=f)
        x0, y0 = 70, H - 170
        rounded(d, (x0 + 8, y0 + 8, x0 + tw + 76, y0 + 100), 22, (0, 0, 0, 110))
        rounded(d, (x0, y0, x0 + tw + 68, y0 + 92), 22, color + (240,))
        d.text((x0 + 34, y0 + 46), title, font=f, fill="white", anchor="lm")
    if fact:
        sticker = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sticker)
        f = font(F_BOLD, 40)
        tw = sd.textlength(fact, font=f)
        rounded(sd, (16, 26, tw + 76, 126), 18, (0, 0, 0, 90))
        rounded(sd, (10, 20, tw + 70, 120), 18, YELLOW + (250,))
        sd.text((40, 70), fact, font=f, fill=INK, anchor="lm")
        sticker = sticker.crop((0, 0, int(tw) + 100, 160)).rotate(2.5, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(sticker, (W - sticker.width - 50, 40))
    p = B / f"ov_{name}.png"
    img.save(p)
    return p


def overlay_title(name, top, big, sub):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # soft dark vignette on the left for legibility
    grad = Image.new("L", (W, H))
    gd = ImageDraw.Draw(grad)
    for x in range(W):
        gd.line([(x, 0), (x, H)], fill=int(max(0, 170 * (1 - x / (W * 0.62)))))
    img.paste((10, 5, 30, 255), mask=grad)
    d = ImageDraw.Draw(img)
    x = 110
    shadow_text(d, (x, 300), top, font(F_BOLD, 64), (255, 255, 255, 255))
    fb = font(F_BLACK, 190)
    cx = x
    for i, ch in enumerate(big):
        c = PALETTE[i % len(PALETTE)] if ch != " " else (0, 0, 0)
        shadow_text(d, (cx, 380), ch, fb, c + (255,), offset=8)
        cx += d.textlength(ch, font=fb) + 4
    shadow_text(d, (x + 4, 620), sub, font(F_SEMI, 50), (255, 235, 180, 255))
    p = B / f"ov_{name}.png"
    img.save(p)
    return p


def card_background(src):
    bg = Image.open(A / "img" / f"{src}.png").convert("RGB").resize((W, H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(18))
    return Image.blend(bg, Image.new("RGB", (W, H), (20, 10, 45)), 0.62).convert("RGBA")


def quiz_card(name, header, lines, bg_src, header_color, marks=None):
    img = card_background(bg_src)
    d = ImageDraw.Draw(img)
    fh = font(F_BLACK, 110)
    shadow_text(d, (W // 2, 170), header, fh, header_color + (255,), offset=7, anchor="mm")
    fq = font(F_BOLD, 54)
    y = 330
    for i, line in enumerate(lines):
        c = PALETTE[i % 3 + 0]
        d.ellipse((150, y - 8, 250, y + 92), fill=c)
        d.text((200, y + 42), marks[i] if marks else str(i + 1), font=font(F_BLACK, 60), fill="white", anchor="mm")
        rounded(d, (280, y - 8, W - 150, y + 92), 26, (255, 255, 255, 235))
        d.text((320, y + 42), line, font=fq, fill=INK, anchor="lm")
        y += 170
    p = B / f"card_{name}.png"
    img.convert("RGB").save(p)
    return p


def countdown_cards(bg_src, n=5):
    paths = []
    for k in range(n, 0, -1):
        img = card_background(bg_src)
        d = ImageDraw.Draw(img)
        shadow_text(d, (W // 2, 230), "PAUSE & THINK!", font(F_BLACK, 120), YELLOW + (255,), offset=7, anchor="mm")
        r = 230
        c = PALETTE[k % len(PALETTE)]
        d.ellipse((W // 2 - r, 600 - r, W // 2 + r, 600 + r), fill=c)
        d.text((W // 2, 600), str(k), font=font(F_BLACK, 300), fill="white", anchor="mm")
        p = B / f"card_count_{k}.png"
        img.convert("RGB").save(p)
        paths.append(p)
    return paths


def end_card():
    img = card_background("00_title")
    d = ImageDraw.Draw(img)
    shadow_text(d, (W // 2, 170), "YOUR TURN!", font(F_BLACK, 140), YELLOW + (255,), offset=8, anchor="mm")
    shadow_text(d, (W // 2, 300), "Design your own alebrije", font(F_BOLD, 64), (255, 255, 255, 255), anchor="mm")
    steps = [("1", "Pick 2 or 3 animals", MAGENTA), ("2", "Mix their best parts", TURQ),
             ("3", "Add bold colors & patterns", ORANGE), ("4", "Give it a name!", COBALT)]
    y = 400
    for num, text, c in steps:
        d.ellipse((520, y, 610, y + 90), fill=c)
        d.text((565, y + 45), num, font=font(F_BLACK, 56), fill="white", anchor="mm")
        d.text((650, y + 45), text, font=font(F_BOLD, 58), fill="white", anchor="lm")
        y += 120
    d.text((W // 2, H - 60),
           "Illustrations are artistic recreations, not historical photos. Narration, art and music made with AI.",
           font=font(F_SEMI, 28), fill=(220, 220, 235), anchor="mm")
    p = B / "card_end.png"
    img.convert("RGB").save(p)
    return p


# --------------------------------------------------------------- segments
MOVES = {
    "in": ("1.0+0.12*on/{N}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "out": ("1.12-0.12*on/{N}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "lr": ("1.12", "(iw-iw/zoom)*on/{N}", "ih/2-(ih/zoom/2)"),
    "rl": ("1.12", "(iw-iw/zoom)*(1-on/{N})", "ih/2-(ih/zoom/2)"),
    "still": ("1.0", "0", "0"),
}


def render_segment(name, image, seconds, move="in", overlay=None, ov_in=0.5):
    out = B / f"seg_{name}.mp4"
    n = int(round(seconds * FPS))
    z, x, y = (s.format(N=max(n - 1, 1)) for s in MOVES[move])
    vf = (f"[0:v]scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
          f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={FPS},setsar=1[bg]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", FPS, "-t", f"{seconds:.3f}", "-i", image]
    if overlay:
        cmd += ["-loop", "1", "-framerate", FPS, "-t", f"{seconds:.3f}", "-i", overlay]
        vf += (f";[1:v]format=rgba,fade=in:st={ov_in}:d=0.6:alpha=1,"
               f"fade=out:st={max(seconds - 1.3, ov_in + 0.7):.3f}:d=0.6:alpha=1[ov];[bg][ov]overlay=0:0[v]")
    else:
        vf += ";[bg]null[v]"
    cmd += ["-filter_complex", vf, "-map", "[v]", "-frames:v", n, "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p", "-r", FPS, out]
    run(cmd)
    return out, n / FPS


def caption_chunks(text):
    text = re.sub(r"\[[^\]]*\]\s*", "", text).strip()
    parts = re.split(r"(?<=[.!?:])\s+", text)
    chunks = []
    for p in parts:
        words = p.split()
        while len(words) > 14:            # keep captions to ~2 short lines
            chunks.append(" ".join(words[:12]))
            words = words[12:]
        if words:
            chunks.append(" ".join(words))
    return chunks


def srt_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"


def main():
    segs = []      # (path, duration)
    narr = []      # (audio path, start time)
    captions = []  # (start, end, text)
    t = 0.0

    def add(seg, seconds, audio=None, text=None):
        nonlocal t
        start = t if not segs else t - XF
        segs.append((seg, seconds))
        if audio:
            a0 = start + LEAD
            narr.append((audio, a0))
            if text:
                chunks = caption_chunks(text)
                total = sum(len(c) for c in chunks)
                ad = dur(audio)
                c0 = a0
                for c in chunks:
                    c1 = c0 + ad * len(c) / total
                    captions.append((c0, c1, c))
                    c0 = c1
        t = start + seconds

    # title
    seg, d = render_segment("00_title", A / "img/00_title.png", 6.5, "out",
                            overlay_title("title", "THE ORIGIN OF THE", "ALEBRIJES",
                                          "How one dream changed Mexican art"), ov_in=0.4)
    add(seg, d)

    for i, (sid, imgs, moves, fact) in enumerate(SCENES):
        audio = A / "audio" / f"{sid}.mp3"
        total = dur(audio) + LEAD + TAIL
        title = SCRIPT[sid]["title"]
        ov = overlay_chip(sid, title, PALETTE[i % len(PALETTE)], fact) if (title or fact) else None
        if len(imgs) == 1:
            seg, d = render_segment(sid, A / "img" / f"{imgs[0]}.png", total, moves[0], ov)
            add(seg, d, audio, SCRIPT[sid]["narration"])
        else:
            first = total * 0.5 + XF / 2
            seg, d = render_segment(sid + "_a", A / "img" / f"{imgs[0]}.png", first, moves[0], ov)
            add(seg, d, audio, SCRIPT[sid]["narration"])
            seg, d = render_segment(sid + "_b", A / "img" / f"{imgs[1]}.png", total - first + XF, moves[1])
            add(seg, d)

    # quiz
    qa = A / "audio/12_quiz.mp3"
    qcard = quiz_card("quiz", "QUICK QUIZ!", [
        "Who created the first alebrijes?",
        "What happened in 1936 that inspired them?",
        "In Oaxaca, what wood are alebrijes carved from?"], "02_what", YELLOW)
    seg, d = render_segment("12_quiz", qcard, dur(qa) + LEAD + 0.4, "still")
    quiz_text = re.sub(r"\.\.\. Ready\?.*$", "", SCRIPT["12_quiz"]["narration"]).strip()
    add(seg, d, qa, quiz_text)
    for k, p in zip(range(5, 0, -1), countdown_cards("02_what")):
        seg, d = render_segment(f"12_count_{k}", p, 1.0 + (XF if k != 5 else XF), "still")
        add(seg, d)
    aa = A / "audio/12b_answers.mp3"
    acard = quiz_card("answers", "ANSWERS", ["Pedro Linares", "A fever dream", "Copal wood"],
                      "09_wood_b", LIME, marks=["✓"] * 3)
    seg, d = render_segment("12_answers", acard, dur(aa) + LEAD + 1.4, "still")
    add(seg, d, aa, "Ready? The answers are: Pedro Linares, a fever dream, and copal wood!")

    # challenge + end card
    ca = A / "audio/13_challenge.mp3"
    ov = overlay_chip("13_challenge", SCRIPT["13_challenge"]["title"], MAGENTA)
    seg, d = render_segment("13_challenge", A / "img/13_challenge.png", dur(ca) + LEAD + TAIL + 0.3, "in", ov)
    add(seg, d, ca, SCRIPT["13_challenge"]["narration"])
    seg, d = render_segment("14_end", end_card(), 8.0, "still")
    add(seg, d)
    total = t

    # ---- video: crossfade chain
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for p, _ in segs:
        cmd += ["-i", p]
    fc, prev, acc = [], "[0:v]", segs[0][1]
    for k in range(1, len(segs)):
        off = acc - XF
        lab = f"[x{k}]"
        fc.append(f"{prev}[{k}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}{lab}")
        prev, acc = lab, off + segs[k][1]
    fc.append(f"{prev}fade=in:st=0:d=0.8,fade=out:st={total - 1.5:.3f}:d=1.5[vout]")
    video = B / "video_only.mp4"
    cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-c:v", "libx264", "-preset", "medium",
            "-crf", "19", "-pix_fmt", "yuv420p", "-r", FPS, video]
    run(cmd)

    # ---- audio: narration on the timeline, music ducked underneath
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for p, _ in narr:
        cmd += ["-i", p]
    cmd += ["-stream_loop", "-1", "-i", A / "music.mp3"]
    mi = len(narr)
    fc = []
    for k, (_, st) in enumerate(narr):
        ms = int(st * 1000)
        fc.append(f"[{k}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms}[n{k}]")
    fc.append("".join(f"[n{k}]" for k in range(len(narr))) +
              f"amix=inputs={len(narr)}:normalize=0,apad,atrim=0:{total:.3f}[narr]")
    fc.append("[narr]asplit[nk][nm]")
    fc.append(f"[{mi}:a]aresample=44100,aformat=channel_layouts=stereo,atrim=0:{total:.3f},volume=0.30,"
              f"afade=in:st=0:d=1.5,afade=out:st={total - 4:.3f}:d=4[mus]")
    fc.append("[mus][nk]sidechaincompress=threshold=0.015:ratio=9:attack=30:release=600[duck]")
    fc.append("[nm][duck]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
    audio = B / "audio_mix.m4a"
    cmd += ["-filter_complex", ";".join(fc), "-map", "[aout]", "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", audio]
    run(cmd)

    # ---- captions + mux
    srt = ROOT / "alebrijes_origin.srt"
    with open(srt, "w") as f:
        for n, (c0, c1, txt) in enumerate(captions, 1):
            f.write(f"{n}\n{srt_time(c0)} --> {srt_time(c1)}\n{txt}\n\n")
    out = ROOT / "alebrijes_origin.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", audio, "-i", srt,
         "-map", "0:v", "-map", "1:a", "-map", "2:s", "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text",
         "-metadata:s:s:0", "language=eng", "-metadata", "title=The Origin of the Alebrijes",
         "-movflags", "+faststart", out])
    print(f"done: {out}  ({total:.1f}s = {int(total // 60)}:{int(total % 60):02d})")


if __name__ == "__main__":
    main()
