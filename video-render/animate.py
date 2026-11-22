"""Puppet animation for Kids Song Club scenes.

For each scene image: cut out the characters (rembg), inpaint the background,
then render the characters bouncing / swaying / squashing to the song's beat.
Output: one MP4 clip per scene, same length as requested.
"""
import math
import subprocess

import cv2
import numpy as np
from PIL import Image

W, H, FPS = 1920, 1080, 30
_SESSION = None


def _session():
    global _SESSION
    if _SESSION is None:
        from rembg import new_session
        _SESSION = new_session("isnet-general-use")
    return _SESSION


_CACHE = {}


def split_scene(path, min_area_ratio=0.02):
    """Return (background image, list of (rgba sprite, x, y))."""
    if path in _CACHE:
        return _CACHE[path]
    from rembg import remove
    img = Image.open(path).convert("RGB").resize((W, H))
    cut = remove(img, session=_session())  # RGBA
    alpha = np.array(cut)[:, :, 3]
    mask = (alpha > 40).astype(np.uint8)
    # separate characters: connected components of a slightly eroded mask
    eroded = cv2.erode(mask, np.ones((9, 9), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(eroded, 8)
    sprites = []
    full = np.array(cut)
    big = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > min_area_ratio * W * H]
    big.sort(key=lambda i: stats[i, cv2.CC_STAT_LEFT])
    used = np.zeros_like(mask)
    for i in big:
        comp = cv2.dilate((labels == i).astype(np.uint8), np.ones((13, 13), np.uint8)) & mask
        used |= comp
        x, y, w, h = cv2.boundingRect(comp)
        rgba = full[y:y + h, x:x + w].copy()
        rgba[:, :, 3] = (rgba[:, :, 3] * comp[y:y + h, x:x + w]).astype(np.uint8)
        sprites.append((Image.fromarray(rgba, "RGBA"), x, y))
    # background: remove only the animated characters, fill by inpainting
    hole = cv2.dilate(used, np.ones((25, 25), np.uint8)) * 255
    bg = cv2.inpaint(np.array(img), hole, 12, cv2.INPAINT_TELEA)
    _CACHE[path] = (Image.fromarray(bg), sprites)
    return _CACHE[path]


def render_clip(path, duration, out, bpm=110, zoom_in=True):
    bg, sprites = split_scene(path)
    frames = max(2, round(duration * FPS))
    beat = 60.0 / bpm
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(frames):
        t = f / FPS
        k = f / (frames - 1)
        z = 1 + 0.05 * (k if zoom_in else 1 - k)
        canvas = bg.copy()
        for j, (spr, x, y) in enumerate(sprites):
            ph = (t / beat + j * 0.33) % 1.0
            hop = abs(math.sin(math.pi * ph))           # 0..1 per beat
            lift = 28 * hop                              # px up
            squash = 1 + 0.06 * (1 - hop) ** 3           # squash when landing
            sw, sh = spr.size
            nw, nh = int(sw * squash), int(sh / squash)
            s = spr.resize((nw, nh), Image.BICUBIC)
            ang = 4 * math.sin(2 * math.pi * (t / (2 * beat)) + j)
            s = s.rotate(ang, resample=Image.BICUBIC, expand=True)
            cx = x + sw / 2
            by = y + sh                                  # feet line
            px = int(cx - s.size[0] / 2)
            py = int(by - lift - s.size[1] + (s.size[1] - nh) / 2)
            canvas.alpha_composite(s, (px, py)) if canvas.mode == "RGBA" else canvas.paste(s, (px, py), s)
        if z != 1:
            cw, ch = int(W / z), int(H / z)
            l, tp = (W - cw) // 2, (H - ch) // 2
            canvas = canvas.crop((l, tp, l + cw, tp + ch)).resize((W, H), Image.BILINEAR)
        proc.stdin.write(canvas.tobytes())
    proc.stdin.close()
    proc.wait()
    return out
