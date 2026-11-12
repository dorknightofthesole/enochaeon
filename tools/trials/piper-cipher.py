"""Speak the cipher with John and decipher it. The shipped path stayed on espeak.

This trial was run against the cipher as espeak spoke it, one breath for each word. The cipher is now
spoken by John one letter at a time, and this script does not run against it.
The espeak voice it compares against has been taken out of the project.

The decoder still uses the espeak calibration. Word gaps stay at the cipher
length, so a word break is a word break. John only replaces the voice.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from enochaeon.alphabet import Alphabet
from enochaeon.audio import Gaps, normalize, silence, trim_silence, write_wav
from enochaeon.config import load_call_voice
from enochaeon.decode import decode_file, require_calibration
from enochaeon.piper_voice import _IPA, _speak
from enochaeon import piper_voice

# Affricates and the two fricatives the cipher uses and the Call map does not.
_IPA.update({"dZ": "dʒ", "tS": "tʃ", "S": "ʃ", "T": "θ"})
piper_voice._ORDERED = sorted(_IPA, key=len, reverse=True)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "example" / "pangram.txt"
ESPEAK_WAV = ROOT / "example" / "pangram.wav"
OUT_WAV = ROOT / "scratch" / "piper-cipher-pangram.wav"
OUT_TXT = ROOT / "scratch" / "piper-cipher.txt"


def main() -> None:
    voice = load_call_voice()
    from piper import PiperVoice, SynthesisConfig

    speaker = PiperVoice.load(voice.piper_voice)
    alphabet = Alphabet.load()
    text = SOURCE.read_text(encoding="utf-8")
    gaps = Gaps()
    lines = [
        f"voice {voice.piper_voice}",
        f"length_scale {voice.length_scale}",
        f"gaps syllable {gaps.syllable_ms} word {gaps.word_ms} nl {gaps.nl_ms}",
        "",
    ]
    pieces = []
    for item in alphabet.atom_ids(text):
        if isinstance(item, str):
            pieces.append(silence(gaps.nl_ms if item == "\n" else gaps.word_ms))
            continue
        phonemes = alphabet.pronounce_atoms(tuple(alphabet.atoms[atom_id] for atom_id in item))
        ipa = piper_voice.ipa_of(phonemes)
        lines.append(f"{phonemes}  ->  {ipa}")
        audio = _speak(speaker, SynthesisConfig, ipa, voice.length_scale)
        pieces.append(normalize(trim_silence(audio)))
    write_wav(OUT_WAV, __import__("numpy").concatenate(pieces), comment=gaps.comment())
    labels = require_calibration(alphabet)
    espeak_text, espeak_unknown = decode_file(ESPEAK_WAV, alphabet, labels)
    john_text, john_unknown = decode_file(OUT_WAV, alphabet, labels)
    lines.extend(
        [
            "",
            f"source:  {text.strip()}",
            f"espeak:  {espeak_text.strip()}  unknown={espeak_unknown}",
            f"john:    {john_text.strip()}  unknown={john_unknown}",
        ]
    )
    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
