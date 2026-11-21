"""Render Kids Song Club videos: scenes + song -> 1080p H.264 MP4 (Ken Burns, crossfades, fades)."""
import json, os, subprocess, sys, urllib.request

FPS, XF, W, H = 30, 0.6, 1920, 1080
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def run(cmd):
    print(" ".join(cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True)

def fetch(url, path):
    if not os.path.exists(path):
        urllib.request.urlretrieve(url, path)
    return path

def render(lang, cfg, scenes, out_dir, work):
    cuts, end = cfg["cuts"], cfg["end"]
    audio = cfg["audio"] if not cfg["audio"].startswith("http") else fetch(cfg["audio"], f"{work}/{lang}.wav")
    clips = []
    for i, (start, sid) in enumerate(cuts):
        stop = cuts[i + 1][0] if i + 1 < len(cuts) else end
        dur = stop - start + (XF if i + 1 < len(cuts) else 0)
        n = max(2, round(dur * FPS))
        z = f"1+0.08*on/{n}" if i % 2 == 0 else f"1.08-0.08*on/{n}"
        clip = f"{work}/{lang}_{i:02d}.mp4"
        run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", scenes[sid],
             "-vf", f"scale={W*2}:{H*2},zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},format=yuv420p",
             "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", clip])
        clips.append((clip, dur))
    # chain crossfades
    inputs, filt, prev, offset = [], [], "[0:v]", 0.0
    for c, _ in clips:
        inputs += ["-i", c]
    for i in range(1, len(clips)):
        offset += clips[i - 1][1] - XF
        lbl = f"[v{i}]"
        filt.append(f"{prev}[{i}:v]xfade=transition=fade:duration={XF}:offset={offset:.3f}{lbl}")
        prev = lbl
    wm = (f"drawtext=fontfile={FONT}:text='Kids Song Club':fontsize=34:fontcolor=white:"
          f"box=1:boxcolor=black@0.35:boxborderw=14:x=w-tw-48:y=h-th-44")
    filt.append(f"{prev}{wm},fade=t=in:st=0:d=1,fade=t=out:st={end-2.5}:d=2.5,format=yuv420p[vout]")
    a = len(clips)
    filt.append(f"[{a}:a]atrim=0:{end},afade=t=out:st={end-2.5}:d=2.5,aresample=48000[aout]")
    out = f"{out_dir}/colors-song-{lang}.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-i", audio, "-filter_complex", ";".join(filt),
         "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(end), out])
    print("OK", out, flush=True)

def main():
    cfg = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "timeline.json"))
    langs = sys.argv[2].split(",") if len(sys.argv) > 2 else list(cfg["videos"])
    work, out_dir = "work", "out"
    os.makedirs(work, exist_ok=True); os.makedirs(out_dir, exist_ok=True)
    scenes = {k: fetch(v, f"{work}/{k}.jpg") if v.startswith("http") else v for k, v in cfg["scenes"].items()}
    for lang in langs:
        render(lang, cfg["videos"][lang], scenes, out_dir, work)

if __name__ == "__main__":
    main()
