"""Write scratch/piper-call.wav from calls/01.txt using the Calls config.

Phoneme length and the voice path come from that config. The Call wavs in
calls/ are not touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from enochaeon.audio import Gaps, write_wav
from enochaeon.config import load_call_voice
from enochaeon.enochian import render

SOURCE = ROOT / "calls" / "01.txt"
WAV = ROOT / "scratch" / "piper-call.wav"


def main() -> None:
    voice = load_call_voice(ROOT / "enochaeon.json")
    print(f"length_scale {voice.length_scale}")
    print(f"piper_voice {voice.piper_voice}")
    audio = render(SOURCE.read_text(encoding="utf-8"), voice=voice)
    write_wav(WAV, audio, comment=Gaps().comment())
    print(WAV)


if __name__ == "__main__":
    main()
