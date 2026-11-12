"""See which words ritual.wav could have kept, and how long the file is."""

import wave
from pathlib import Path

from enochaeon.roots import load_roots
from enochaeon.translate import MiniLM, match_phrase

wav = Path("ritual.wav")
with wave.open(str(wav)) as handle:
    seconds = handle.getnframes() / handle.getframerate()
print(f"duration {seconds:.2f}s")

roots = load_roots()
scorer = MiniLM()
phrase = "Speak justice into the fire."
result = match_phrase(phrase, roots, scorer)
print("matched", result.matched)
print("left out", result.left_out)
print("call", result.call_text)

for word in ("speak", "justice", "into", "the", "fire", "harmony"):
    ranked = []
    for root in roots:
        for gloss in root.glosses:
            ranked.append((scorer.similarity(word, gloss), gloss, root.spelling))
    ranked.sort(reverse=True)
    top = ranked[:5]
    print(word)
    for score, gloss, spelling in top:
        print(f"  {score:.3f} {gloss} -> {spelling}")
