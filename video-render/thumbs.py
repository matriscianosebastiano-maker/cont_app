"""Kids Song Club thumbnails: scene image + big outlined title + badge. 1280x720 JPG."""
import json, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/fredokaone/FredokaOne-Regular.ttf"

def font(size):
    if not os.path.exists("fredoka.ttf"):
        urllib.request.urlretrieve(FONT_URL, "fredoka.ttf")
    return ImageFont.truetype("fredoka.ttf", size)

def fit(draw, text, maxw, start):
    s = start
    while s > 40:
        f = font(s)
        if draw.textbbox((0, 0), text, font=f, stroke_width=s // 9)[2] <= maxw:
            return f
        s -= 6
    return font(s)

def make(item, out):
    src = "tmp_" + os.path.basename(item["image"])
    if not os.path.exists(src):
        urllib.request.urlretrieve(item["image"], src)
    im = Image.open(src).convert("RGB").resize((1280, 720))
    d = ImageDraw.Draw(im)
    # soft dark band at top for readability
    band = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    ImageDraw.Draw(band).rectangle([0, 0, 1280, 250], fill=(0, 0, 0, 90))
    im = Image.alpha_composite(im.convert("RGBA"), band.filter(ImageFilter.GaussianBlur(30))).convert("RGB")
    d = ImageDraw.Draw(im)
    f = fit(d, item["title"], 1180, 170)
    sw = max(8, f.size // 9)
    w = d.textbbox((0, 0), item["title"], font=f, stroke_width=sw)[2]
    x = (1280 - w) // 2
    # rainbow letters
    cols = item.get("colors", ["#FF3B3B", "#FF9F1C", "#FFE14D", "#3DDC84", "#3BA7FF", "#B36BFF", "#FF6FB5"])
    cx = x
    for i, ch in enumerate(item["title"]):
        d.text((cx, 30), ch, font=f, fill=cols[i % len(cols)], stroke_width=sw, stroke_fill="white")
        cx += d.textlength(ch, font=f)
    # badge bottom-left
    if item.get("badge"):
        bf = font(54)
        bw = d.textlength(item["badge"], font=bf)
        d.rounded_rectangle([30, 610, 30 + bw + 50, 690], radius=40, fill="#FFE14D", outline="white", width=6)
        d.text((55, 618), item["badge"], font=bf, fill="#2B2B2B")
    im.save(out, quality=92)

if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    os.makedirs("out", exist_ok=True)
    for name, item in cfg.items():
        make(item, f"out/thumb-{name}.jpg")
        print("ok", name)
