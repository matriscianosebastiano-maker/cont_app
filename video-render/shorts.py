"""Kids Song Club - Shorts verticali 1080x1920 dai video gia' montati (ritornello)."""
import json, os, re, subprocess, urllib.request
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920
os.makedirs("shorts", exist_ok=True)

def font():
    p = "lilita.ttf"
    if not os.path.exists(p):
        try:
            css = urllib.request.urlopen(urllib.request.Request(
                "https://fonts.googleapis.com/css2?family=Lilita+One", headers={"User-Agent": "curl/8"})).read().decode()
            urllib.request.urlretrieve(re.search(r"url\((https://[^)]+)\)", css).group(1), p)
        except Exception as e:
            print("font fallback", e); return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    return p
FONT = font()
COLS = ["#FF4D4D", "#FFB000", "#FFE14D", "#3DDC84", "#33B5FF", "#9B6BFF", "#FF6EC7"]

def overlay(title, sub, out):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    size = 130
    while True:
        f = ImageFont.truetype(FONT, size)
        if d.textbbox((0, 0), title, font=f)[2] <= W - 80 or size < 60: break
        size -= 6
    tw = d.textbbox((0, 0), title, font=f)[2]; x = (W - tw) // 2; y = 230; i = 0
    for ch in title:
        if ch != " ":
            d.text((x, y), ch, font=f, fill=COLS[i % len(COLS)], stroke_width=10, stroke_fill="white"); i += 1
        x += d.textlength(ch, font=f)
    f2 = ImageFont.truetype(FONT, 64)
    sw = d.textbbox((0, 0), sub, font=f2)[2]
    d.rounded_rectangle(((W - sw) // 2 - 40, 1500, (W + sw) // 2 + 40, 1600), 50, fill="#FFD23F")
    d.text((W // 2, 1550), sub, font=f2, fill="#2B2D42", anchor="mm")
    f3 = ImageFont.truetype(FONT, 46)
    d.text((W // 2, 1700), "Kids Song Club", font=f3, fill="white", anchor="mm", stroke_width=4, stroke_fill="#2B2D42")
    im.save(out)

for s in json.load(open("shorts.json")):
    src = f"src_{s['src'].split('/')[-1]}"
    if not os.path.exists(src): urllib.request.urlretrieve(s["src"], src)
    ov = f"ov_{s['name']}.png"; overlay(s["title"], s["sub"], ov)
    st, du = s["start"], s["dur"]
    fc = ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:2,eq=brightness=-0.12[bg];"
          "[0:v]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2+40[v];[v][1:v]overlay=0:0,"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={du-0.6}:d=0.6[vo];"
          f"[0:a]afade=t=in:st=0:d=0.3,afade=t=out:st={du-1}:d=1[ao]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(st), "-t", str(du), "-i", src, "-i", ov,
                    "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", f"shorts/{s['name']}.mp4"], check=True)
    print("ok", s["name"])
