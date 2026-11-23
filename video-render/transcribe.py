"""Trascrizione con tempi (faster-whisper, CPU) per tagliare le scene sulla canzone."""
import json, sys, urllib.request
from faster_whisper import WhisperModel
jobs = json.loads(sys.argv[1])  # {"en": url, "it": url}
m = WhisperModel("small", device="cpu", compute_type="int8")
out = {}
for lang, url in jobs.items():
    p = f"{lang}.wav"; urllib.request.urlretrieve(url, p)
    segs, _ = m.transcribe(p, language=lang, word_timestamps=True, vad_filter=False)
    out[lang] = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
    print(lang, len(out[lang]))
json.dump(out, open("transcript.json", "w"), ensure_ascii=False, indent=1)
