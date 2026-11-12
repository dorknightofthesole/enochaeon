"""Does Piper run the espeak-ng it carries when this project speaks?

Piper has a copy of espeak-ng inside it. Piper uses it to turn written text
into phonemes. This project gives Piper phonemes, inside [[ ]], so that step
should have nothing to do. This trial counts what the step is handed while one
Call word and one cipher letter sound are spoken the way the project speaks them.

    PYTHONPATH=src python3 tools/trials/piper-espeak-use.py

The count is written to scratch/piper-espeak-use.txt.
"""

from __future__ import annotations

from pathlib import Path

import piper
from piper import phonemize_espeak

from enochaeon import piper_voice
from enochaeon.alphabet import Alphabet
from enochaeon.cipher_voice import Speaker
from enochaeon.config import load_call_voice, load_cipher_voice
from enochaeon.enochian import parse
from enochaeon.roots import load_readings

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "scratch" / "piper-espeak-use.txt"


def main() -> None:
    handed: list[str] = []
    real = phonemize_espeak.EspeakPhonemizer.phonemize

    def counted(self, voice, text, *args, **kwargs):
        handed.append(text)
        return real(self, voice, text, *args, **kwargs)

    phonemize_espeak.EspeakPhonemizer.phonemize = counted
    lines: list[str] = []

    calls = load_call_voice(ROOT / "enochaeon.json")
    readings = load_readings(calls.piper_ipa or calls.ipa, ROOT / "calls")
    spelling = sorted(readings)[0]
    sent = piper_voice._word_ipa(parse(spelling)[0], readings, calls)
    speaker = piper.PiperVoice.load(ROOT / calls.piper_voice)
    audio = piper_voice._speak(speaker, piper.SynthesisConfig, sent, calls.length_scale)
    lines.append(f"Call word {spelling}: sent [[{sent}]], {audio.size} samples, espeak handed {handed!r}")

    handed.clear()
    alphabet = Alphabet.load()
    cipher = Speaker(load_cipher_voice(ROOT / "enochaeon.json"), alphabet)
    atom = next(iter(alphabet.atoms.values()))
    audio = cipher.sound(atom, "phone")
    lines.append(f"cipher letter {atom.id}: {audio.size} samples, espeak handed {handed!r}")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
