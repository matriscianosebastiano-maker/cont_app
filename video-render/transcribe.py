"""Trascrizione con tempi (faster-whisper, CPU) per tagliare le scene sulla canzone."""
import json, subprocess, sys, urllib.request
import numpy as np
from faster_whisper import WhisperModel
jobs = json.loads(sys.argv[1])  # {"en": url, "it": url}
m = WhisperModel("small", device="cpu", compute_type="int8")
out = {}
for lang, url in jobs.items():
    p = f"{lang}.wav"; urllib.request.urlretrieve(url, p)
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", p, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.float32)
    segs, _ = m.transcribe(audio, language=lang, word_timestamps=True, vad_filter=False)
    out[lang] = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
    print(lang, len(out[lang]))
json.dump(out, open("transcript.json", "w"), ensure_ascii=False, indent=1)
