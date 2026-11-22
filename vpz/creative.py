"""Ventipunto Zero - caroselli inverno 1080x1350 da foto reali del sito (solo testo sovrapposto)."""
import json, os, re, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1080, 1350
RUST = (176, 84, 44); CREAM = (243, 234, 220)
os.makedirs("out", exist_ok=True)

def gfont(fam, name):
    if os.path.exists(name): return name
    try:
        css = urllib.request.urlopen(urllib.request.Request(
            f"https://fonts.googleapis.com/css2?family={fam}", headers={"User-Agent": "curl/8"})).read().decode()
        urllib.request.urlretrieve(re.search(r"url\((https://[^)]+)\)", css).group(1), name)
        return name
    except Exception as e:
        print("font fallback", e); return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SERIF = gfont("Playfair+Display:wght@600", "serif.ttf")
SANS = gfont("Montserrat:wght@600", "sans.ttf")
F = lambda p, s: ImageFont.truetype(p, s)

def load(url):
    p = "src_" + re.sub(r"\W", "", url)[-30:] + ".jpg"
    if not os.path.exists(p):
        urllib.request.urlretrieve(url + "/v1/fit/w_2200,h_2200/x.jpg", p)
    return Image.open(p).convert("RGB")

def cover(im, fy=0.5):
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l = (im.width - W) // 2; t = int((im.height - H) * fy)
    return im.crop((l, t, l + W, t + H))

def wrap(d, text, f, maxw):
    out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split():
            t = (line + " " + w).strip()
            if d.textbbox((0, 0), t, font=f)[2] <= maxw: line = t
            else: out.append(line); line = w
        out.append(line)
    return out

def slide(s, out, idx, tot):
    im = cover(load(s["img"]), s.get("fy", 0.5))
    # dark gradient at bottom
    g = Image.new("L", (1, H))
    for y in range(H):
        k = min(1, max(0, (y - H * 0.30) / (H * 0.45))); g.putpixel((0, y), int(240 * k ** 1.1))
    shade = Image.new("RGB", (W, H), (14, 10, 8))
    im = Image.composite(shade, im, g.resize((W, H)))
    d = ImageDraw.Draw(im)
    d.text((60, 56), "VENTIPUNTO ZERO", font=F(SANS, 30), fill=CREAM)
    if tot > 1 and not s.get("single"): d.text((W - 60, 56), f"{idx}/{tot}", font=F(SANS, 28), fill=CREAM, anchor="ra")
    y = H - 80
    lines = []
    if s.get("cta"):
        f = F(SANS, 34); tw = d.textbbox((0, 0), s["cta"], font=f)[2]
        d.rounded_rectangle((60, y - 84, 60 + tw + 64, y), 42, fill=RUST)
        d.text((92, y - 42), s["cta"], font=f, fill="white", anchor="lm"); y -= 120
    if s.get("body"):
        f = F(SANS, 34)
        for ln in reversed(wrap(d, s["body"], f, W - 120)):
            y -= 48; d.text((60, y), ln, font=f, fill=CREAM)
        y -= 24
    f = F(SERIF, s.get("size", 84))
    for ln in reversed(wrap(d, s["title"], f, W - 120)):
        y -= int(f.size * 1.12); d.text((60, y), ln, font=f, fill="white")
    if s.get("kicker"):
        y -= 56; d.text((60, y), s["kicker"].upper(), font=F(SANS, 30), fill=(236, 170, 120))
    im.save(out, quality=92)

cfg = json.load(open("creative.json"))
for name, slides in cfg.items():
    for i, s in enumerate(slides, 1):
        slide(s, f"out/{name}-{i}.jpg", i, len(slides))
# overview sheet
names = sorted(os.listdir("out")); n = len(names); C = 5; R = (n + C - 1) // C
sheet = Image.new("RGB", (C * 360, R * 450), "white")
for i, nm in enumerate(names):
    t = Image.open("out/" + nm); t.thumbnail((360, 450)); sheet.paste(t, ((i % C) * 360, (i // C) * 450))
sheet.save("out/_overview.jpg", quality=85)
